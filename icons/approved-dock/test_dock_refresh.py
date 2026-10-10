import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from install import dock_applets, normalize_favorites, reload_dock_plugins


class DockRefreshTests(unittest.TestCase):
    def test_configuration_restored_even_when_refresh_is_interrupted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'plugins_center'
            original = b'Some(["com.system76.CosmicAppList", "com.system76.CosmicAppletMinimize",])'
            path.write_bytes(original)
            def interrupted(_):
                self.assertNotIn(b'CosmicAppList', path.read_bytes())
                self.assertIn(b'CosmicAppletMinimize', path.read_bytes())
                raise KeyboardInterrupt()
            with patch('install.time.sleep', side_effect=interrupted):
                with self.assertRaises(KeyboardInterrupt):
                    reload_dock_plugins(path)
            self.assertEqual(path.read_bytes(), original)

    def test_canonical_ids_preserve_order_and_other_apps(self):
        original='["brave-browser", "Chatgpt", "darktable", "local-trash"]'
        self.assertEqual(normalize_favorites(original),
                         '["brave-browser", "chatgpt", "org.darktable.darktable", "local-trash"]')
        self.assertEqual(normalize_favorites(normalize_favorites(original)), normalize_favorites(original))

    def test_selects_only_supervised_dock_app_lists(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for pid, name in [('1','cosmic-panel'),('2','other-parent')]:
                p=root/pid;p.mkdir();(p/'exe').symlink_to('/usr/bin/'+name)
            cases=[('10','cosmic-app-list','Dock','1'),
                   ('11','cosmic-app-list','Panel','1'),
                   ('12','cosmic-app-list','Dock','2'),
                   ('13','cosmic-files','Dock','1')]
            for pid,command,surface,parent in cases:
                p=root/pid;p.mkdir()
                (p/'cmdline').write_bytes((command+'\0').encode())
                (p/'environ').write_text('COSMIC_PANEL_NAME='+surface+'\0COSMIC_PANEL_OUTPUT=DP-6\0')
                (p/'status').write_text('Name: '+command+'\nPPid:\t'+parent+'\n')
            self.assertEqual(dock_applets(root),{10:'DP-6'})


if __name__=='__main__':unittest.main()
