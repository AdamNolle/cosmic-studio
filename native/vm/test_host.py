"""Portable Windows-side source packaging and byte-integrity checks."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('studio_snapshot', HERE / 'snapshot.py')
snapshot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)


class HostChecks(unittest.TestCase):
    def test_pinned_font_bytes_are_not_rewritten_by_windows_checkout(self):
        manifest = json.loads((ROOT / 'fonts/manifest.json').read_text())
        for entries in manifest['families'].values():
            for entry in entries:
                with self.subTest(file=entry['file']):
                    data = (ROOT / 'fonts' / entry['file']).read_bytes()
                    self.assertEqual(len(data), entry['bytes'])
                    self.assertEqual(hashlib.sha256(data).hexdigest(), entry['sha256'])

    def test_source_paths_reject_private_data_and_path_escape(self):
        for name in ['../private', '/etc/passwd', 'C:/secret', 'work/report.json',
                     '.git/config', 'backups/manifest.json', '.ralph/state.json',
                     'image.iso', 'disk.vdi', 'private.key', 'nested\\escape',
                     'WORK/report.json', '.ssh/config', 'guest-account.json',
                     'nested/Guest-Account.json', 'development_ed25519', 'id_ed25519', 'machine.vbox']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                snapshot.safe_name(name)

    def repository(self, parent):
        root = parent / 'repo'
        root.mkdir()
        def git(*args):
            subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)
        git('init')
        git('config', 'core.autocrlf', 'false')
        git('config', 'user.name', 'Snapshot Test')
        git('config', 'user.email', 'snapshot-test@example.invalid')
        (root / 'source.py').write_bytes(b'original\n')
        git('add', 'source.py')
        git('commit', '-m', 'fixture')
        return root

    def test_archive_contains_current_source_and_explicit_files_not_private_untracked(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            root = self.repository(parent)
            (root / 'source.py').write_bytes(b'changed\n')
            (root / 'new.py').write_bytes(b'new\n')
            (root / 'credential.txt').write_bytes(b'never export')
            output = parent / 'source.tar.gz'
            result = snapshot.export(root, output, ['new.py'])
            self.assertEqual(result['files'], 2)
            with tarfile.open(output) as archive:
                self.assertEqual(set(archive.getnames()), {'source.py', 'new.py', 'studio-source-manifest.json'})
                self.assertEqual(archive.extractfile('source.py').read(), b'changed\n')
                manifest = json.load(archive.extractfile('studio-source-manifest.json'))
                self.assertEqual(manifest['files']['source.py'], hashlib.sha256(b'changed\n').hexdigest())
            other = parent / 'other.tar.gz'
            snapshot.export(root, other, ['new.py'])
            self.assertEqual(output.read_bytes(), other.read_bytes())
            with self.assertRaises(FileExistsError):
                snapshot.export(root, output)

    def test_missing_source_and_repository_output_fail_before_archive_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            root = self.repository(parent)
            with self.assertRaises(ValueError):
                snapshot.export(root, root / 'source.tar.gz')
            (root / 'source.py').unlink()
            output = parent / 'source.tar.gz'
            with self.assertRaises(ValueError):
                snapshot.export(root, output)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
