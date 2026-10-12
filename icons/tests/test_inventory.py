"""Filesystem fixtures only: no app launches, theme installation or optical claim."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('studio_icon_inventory', ROOT/'inventory.py')
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


def theme(path, names=(), inherits=''):
    path.mkdir(parents=True)
    (path/'index.theme').write_text('[Icon Theme]\nName=Fixture\nDirectories=24x24/apps\nInherits='+inherits+'\n[24x24/apps]\nSize=24\nType=Fixed\n')
    folder = path/'24x24/apps'
    folder.mkdir(parents=True)
    for name in names:
        (folder/(name+'.svg')).write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    return path


def launcher(root, filename, icon, extra=''):
    path = root/filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('[Desktop Entry]\nType=Application\nName=Fixture\nExec=fixture %U\nIcon='+icon+'\n'+extra)
    return path


class ActiveInventory(unittest.TestCase):
    def test_actual_active_names_not_inactive_manifest_membership(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            active = theme(root/'theme', ['new-approved'])
            launcher(root/'apps', 'new.desktop', 'new-approved')
            launcher(root/'apps', 'old.desktop', 'folder')
            with patch.object(inventory, 'launches', return_value=True):
                report = inventory.collect(roots=[root/'apps'], theme=active, theme_roots=[])
            rows = {r['desktop_id']: r for r in report['applications']}
            self.assertEqual(rows['new.desktop']['status'], 'custom')
            self.assertEqual(rows['old.desktop']['status'], 'unresolved')
            self.assertEqual(report['summary']['custom_launchers'], 1)
            self.assertFalse(report['complete'])
            self.assertFalse(report['installed_theme_verified'])

    def test_case_is_exact_even_on_windows(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            active = theme(root/'theme', ['org.darktable.darktable'])
            launcher(root/'apps', 'app.desktop', 'org.darktable.Darktable')
            report = inventory.collect(roots=[root/'apps'], theme=active, theme_roots=[])
            self.assertEqual(report['applications'][0]['status'], 'unresolved')

    def test_inheritance_absolute_and_unresolved_are_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            active = theme(root/'active', inherits='Fallback,Missing')
            theme(root/'icons/Fallback', ['fallback'])
            asset = root/'absolute.svg'
            asset.write_text('<svg/>')
            for name, icon in [('fallback', 'fallback'), ('absolute', str(asset)), ('absent', 'absent')]:
                launcher(root/'apps', name+'.desktop', icon)
            report = inventory.collect(roots=[root/'apps'], theme=active, theme_roots=[root/'icons'])
            rows = {r['desktop_id']: r for r in report['applications']}
            self.assertEqual(rows['fallback.desktop']['status'], 'inherited-resolved')
            self.assertEqual(rows['absolute.desktop']['status'], 'absolute-path override needed')
            self.assertTrue(rows['absolute.desktop']['absolute_asset_present'])
            self.assertEqual(rows['absent.desktop']['status'], 'unresolved')
            self.assertEqual(report['missing_inherited_themes'], ['Missing'])
            self.assertEqual(report['summary']['custom_launchers'], 0)

    def test_xdg_priority_and_nested_hidden_override(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            active = theme(root/'theme', ['approved'])
            launcher(root/'system', 'nested/app.desktop', 'approved')
            launcher(root/'user', 'nested/app.desktop', 'approved', 'Hidden=true\n')
            launcher(root/'system', 'shown.desktop', 'absent')
            launcher(root/'user', 'shown.desktop', 'approved')
            report = inventory.collect(roots=[root/'system', root/'user'], theme=active, theme_roots=[])
            self.assertEqual([r['desktop_id'] for r in report['applications']], ['shown.desktop'])
            self.assertEqual(report['applications'][0]['source'], str(root/'user/shown.desktop'))
            # XDG uses POSIX colon lists; do not put Windows C: drives in this fixture.
            local, system = Path('/inventory-fixture-local'), Path('/inventory-fixture-system')
            with patch.dict(os.environ, {'XDG_DATA_DIRS': str(local)+':'+str(system)}):
                roots = inventory.launcher_roots(root/'user')
            self.assertGreater(roots.index(local/'applications'), roots.index(system/'applications'))
            self.assertEqual(roots[-1], root/'user/applications')

    def test_env_wrapper_without_tryexec_is_unassessed(self):
        self.assertIsNone(inventory.launches({'Exec': 'env EXAMPLE=1 missing-app %U'}))
        with patch.object(inventory.shutil, 'which', return_value=None):
            self.assertFalse(inventory.launches({'Exec': 'env EXAMPLE=1 missing-app', 'TryExec': 'missing-app'}))

    def test_missing_theme_and_empty_census_never_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = inventory.collect(roots=[], theme=root/'absent', theme_roots=[])
            self.assertFalse(report['launchers_complete'])
            self.assertFalse(report['complete'])
            self.assertTrue(report['inventory_errors'])

    def test_desktop_id_collision_blocks_completeness(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            active = theme(root/'theme', ['approved'])
            launcher(root/'apps', 'foo/bar.desktop', 'approved')
            launcher(root/'apps', 'foo-bar.desktop', 'approved')
            report = inventory.collect(roots=[root/'apps'], theme=active, theme_roots=[])
            self.assertTrue(report['inventory_errors'])
            self.assertFalse(report['launchers_complete'])

    def test_active_repo_inventory_does_not_normalize_case_or_invent_symbols(self):
        report = inventory.theme_assets(inventory.ACTIVE_THEME)
        self.assertEqual(report['name'], 'Studio Dock')
        self.assertFalse(report['errors'])
        self.assertIn('org.darktable.darktable', report['assets'])
        # The tracked theme has case-colliding aliases. Linux extraction can
        # contain both; Windows can expose only one. Audit actual names, not
        # either host's assumed spelling. The synthetic case test is separate.
        expected = {path.stem for path in inventory.ACTIVE_THEME.rglob('*')
                    if path.is_file() and path.suffix.lower() in {'.png', '.svg', '.xpm'}}
        self.assertEqual(set(report['assets']), expected)
        self.assertNotIn('audio-volume-muted-symbolic', report['assets'])


if __name__ == '__main__':
    unittest.main()
