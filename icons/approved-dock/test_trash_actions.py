import unittest
from unittest.mock import patch
from types import SimpleNamespace
from trash_actions import empty_trash, launcher_actions


class TrashActionTests(unittest.TestCase):
    def test_cancel_and_close_never_delete(self):
        for code in [1,5]:
            with patch('trash_actions.item_count',return_value=3), patch('trash_actions.subprocess.run',return_value=SimpleNamespace(returncode=code)) as run, patch('trash_actions.update') as update:
                self.assertFalse(empty_trash())
                self.assertEqual(run.call_count,1)
                self.assertEqual(run.call_args.args[0][0],'zenity')
                update.assert_not_called()

    def test_confirm_then_empty_and_refresh(self):
        with patch('trash_actions.item_count',return_value=3), patch('trash_actions.subprocess.run',return_value=SimpleNamespace(returncode=0)) as run, patch('trash_actions.update') as update:
            self.assertTrue(empty_trash())
            self.assertEqual(run.call_args_list[1].args[0],['gio','trash','--empty'])
            update.assert_called_once_with()

    def test_failed_empty_does_not_report_empty_state(self):
        with patch('trash_actions.item_count',return_value=3), patch('trash_actions.subprocess.run',side_effect=[SimpleNamespace(returncode=0),SimpleNamespace(returncode=1,stderr='Read-only volume'),SimpleNamespace(returncode=0)]) as run, patch('trash_actions.update') as update:
            self.assertFalse(empty_trash())
            update.assert_not_called()
            self.assertIn('--error',run.call_args.args[0])

    def test_launcher_preserves_existing_actions_and_exec(self):
        source='[Desktop Entry]\nExec=cosmic-files --trash\nActions=Inspect;\n\n[Desktop Action Inspect]\nName=Inspect\nExec=inspector\n'
        actual=launcher_actions(source,'/tmp/helper.py')
        self.assertIn('Actions=Inspect;StudioEmptyTrash;',actual)
        self.assertIn('Exec=cosmic-files --trash',actual)
        self.assertIn('[Desktop Action Inspect]\nName=Inspect\nExec=inspector',actual)
        self.assertEqual(launcher_actions(actual,'/tmp/helper.py'),actual)


if __name__=='__main__':unittest.main()
