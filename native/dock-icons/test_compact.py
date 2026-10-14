import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('studio_compact_install', HERE/'install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)
spec = importlib.util.spec_from_file_location('studio_compact_prepare', HERE/'prepare.py')
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)
spec = importlib.util.spec_from_file_location('studio_compact_tooltip', HERE/'prepare_tooltip.py')
tooltip = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tooltip)


class CompactCandidateTests(unittest.TestCase):
    def test_shared_dispatcher_requires_reviewed_features_matching_owned_install(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'bin').mkdir()
            artifact = root/'bin/cosmic-applets'
            alias = root/'bin/cosmic-app-list'
            artifact.write_bytes(b'\x7fELF COSMIC_STUDIO_COMPACT_DOCK COSMIC_STUDIO_POPUP_GLASS')
            artifact.chmod(0o755)
            alias.symlink_to('cosmic-applets')
            report = root/'native-backups/123/manifest.json'
            report.parent.mkdir(parents=True)
            state = {'status': 'applied', 'versions': {'cosmic-app-list': 'pinned'},
                     'after': {str(p): installer.native.fingerprint(p) for p in (alias, artifact)}}
            report.write_text(json.dumps(state))
            with patch.object(installer.native, 'DATA', root):
                self.assertEqual(installer.owned_native_candidate('pinned'), alias)
                self.assertIsNone(installer.owned_native_candidate('upgrade'))
                artifact.write_bytes(b'\x7fELF COSMIC_STUDIO_COMPACT_DOCK')
                self.assertIsNone(installer.owned_native_candidate('pinned'))
                artifact.write_bytes(b'\x7fELF COSMIC_STUDIO_COMPACT_DOCK COSMIC_STUDIO_POPUP_GLASS changed')
                self.assertIsNone(installer.owned_native_candidate('pinned'))
                artifact.write_bytes(b'\x7fELF COSMIC_STUDIO_COMPACT_DOCK COSMIC_STUDIO_POPUP_GLASS')
                state['status'] = 'restored'
                report.write_text(json.dumps(state))
                self.assertIsNone(installer.owned_native_candidate('pinned'))

    def test_preparation_rejects_source_edits_after_reviewed_postimage(self):
        profile = json.loads((HERE/'profile.json').read_text())
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root/profile['file']
            path.parent.mkdir(parents=True)
            path.write_text('unreviewed source mutation')
            with patch.object(subprocess, 'check_output', return_value=profile['revision']+'\n'):
                with self.assertRaisesRegex(RuntimeError, 'differs from both'):
                    prepare.prepare(root, apply=True)
            self.assertEqual(path.read_text(), 'unreviewed source mutation')


class CompactTooltipTests(unittest.TestCase):
    def library(self, folder, text):
        import subprocess
        root = Path(folder)
        (root/'src/applet').mkdir(parents=True)
        (root/tooltip.FILE).write_text(text)
        for args in (['init', '-q'], ['add', '.'], ['-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'pin']):
            subprocess.run(['git', *args], cwd=root, check=True)
        return root

    def test_reviewed_source_is_rewritten_once_and_never_twice(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self.library(folder, 'before\n' + tooltip.BEFORE + '\nafter\n')
            self.assertFalse(tooltip.apply(root)['applied'])
            self.assertIn(tooltip.BEFORE, (root/tooltip.FILE).read_text())
            self.assertTrue(tooltip.apply(root, write=True)['applied'])
            text = (root/tooltip.FILE).read_text()
            self.assertIn('.size(12)', text)
            self.assertNotIn(tooltip.BEFORE, text)
            with self.assertRaisesRegex(RuntimeError, 'already prepared'):
                tooltip.apply(root, write=True)

    def test_unreviewed_tooltip_source_is_refused_without_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self.library(folder, 'changed upstream tooltip\n')
            with self.assertRaisesRegex(RuntimeError, 'reviewed implementation'):
                tooltip.apply(root, write=True)
            self.assertEqual((root/tooltip.FILE).read_text(), 'changed upstream tooltip\n')


if __name__ == '__main__':
    unittest.main()
