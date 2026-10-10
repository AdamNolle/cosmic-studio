import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import trash_state


class TrashStateTests(unittest.TestCase):
    def test_only_main_icon_changes(self):
        text='[Desktop Entry]\nName=Trash\nExec=cosmic-files --trash\nIcon=user-trash\n\n[Desktop Action Other]\nIcon=other-icon\nExec=example\n'
        revised=trash_state.icon_line(text,'user-trash-full')
        self.assertEqual(revised,text.replace('Icon=user-trash\n','Icon=user-trash-full\n'))

    def test_insert_icon_before_actions(self):
        text='[Desktop Entry]\nName=Trash\n[Desktop Action Other]\nIcon=other\n'
        revised=trash_state.icon_line(text,'user-trash')
        self.assertIn('Name=Trash\nIcon=user-trash\n[Desktop Action Other]',revised)
        self.assertTrue(revised.endswith('Icon=other\n'))

    def test_empty_full_and_empty_without_touching_trash(self):
        with tempfile.TemporaryDirectory() as directory:
            launcher=Path(directory)/'local-trash.desktop'
            launcher.write_text('[Desktop Entry]\nExec=cosmic-files --trash\nIcon=user-trash\n')
            launcher.chmod(0o640)
            for count,expected in [(6,'user-trash-full'),(0,'user-trash'),(1,'user-trash-full')]:
                with patch.object(trash_state,'item_count',return_value=count):
                    self.assertEqual(trash_state.update(launcher),expected)
                self.assertIn('Icon='+expected+'\n',launcher.read_text())
                self.assertEqual(launcher.stat().st_mode & 0o777,0o640)

    def test_unavailable_trash_keeps_existing_icon(self):
        with tempfile.TemporaryDirectory() as directory:
            launcher=Path(directory)/'local-trash.desktop'
            launcher.write_text('[Desktop Entry]\nIcon=user-trash-full\n')
            before=launcher.read_bytes()
            with patch.object(trash_state,'item_count',side_effect=RuntimeError('unavailable')):
                with self.assertRaises(RuntimeError):trash_state.update(launcher)
            self.assertEqual(launcher.read_bytes(),before)


if __name__=='__main__':unittest.main()
