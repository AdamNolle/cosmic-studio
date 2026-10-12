"""Source-only dependency guard tests; fixtures are not native compilation evidence."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('guard', Path(__file__).resolve().parents[1] / 'typography/lock_guard.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
LOCK = '''version = 3
[[package]]
name = "libcosmic"
version = "0.1.0"
source = "git+https://github.com/pop-os/libcosmic?rev=abc#abc"
[[package]]
name = "foreign"
version = "1.0.0"
source = "registry+https://github.com/rust-lang/crates.io-index"
checksum = "original"
[[package]]
name = "git-dep"
version = "0.2.0"
source = "git+https://example.invalid/dep#original"
'''
LOCAL = LOCK.replace('source = "git+https://github.com/pop-os/libcosmic?rev=abc#abc"\n', '')


class LockGuardTests(unittest.TestCase):
    def test_native_equal_version_path_is_only_allowed_substitution(self):
        substitutions = guard.native_packages(LOCK)
        expected = guard.foreign_dependencies(LOCK, substitutions)
        self.assertEqual(guard.foreign_dependencies(LOCAL, substitutions), expected)
        for drift in (LOCAL.replace('checksum = "original"', 'checksum = "other"'),
                      LOCAL.replace('version = "1.0.0"', 'version = "1.0.1"'),
                      LOCAL.replace('dep#original', 'dep#other'),
                      LOCAL.replace('version = "0.1.0"', 'version = "9.0.0"'),
                      LOCAL.replace('source = "registry+https://github.com/rust-lang/crates.io-index"\n', '')):
            self.assertNotEqual(guard.foreign_dependencies(drift, substitutions), expected)
        self.assertEqual(guard.native_packages(LOCK.replace('libcosmic?', 'libcosmic-malware?')), set())

    def test_exact_repository_trailing_slash_is_native_not_foreign_drift(self):
        for suffix in ('', '/', '.git', '.git/'):
            original = LOCK.replace('libcosmic?', 'libcosmic' + suffix + '?')
            self.assertEqual(guard.native_packages(original), {('libcosmic', '0.1.0')})
            self.assertEqual(guard.foreign_dependencies(original), guard.foreign_dependencies(LOCAL, guard.native_packages(original)))
        for url in ('git+https://github.com/pop-os/libcosmic-malware/',
                    'git+https://github.com/pop-os/libcosmic/other',
                    'git+https://github.com.evil.invalid/pop-os/libcosmic/',
                    'git+http://github.com/pop-os/libcosmic/',
                    'git+https://github.com/pop-os/libcosmic.git//'):
            self.assertFalse(guard.is_native_source(url + '#abc'))

    def test_drift_restores_byte_exact_original(self):
        with tempfile.TemporaryDirectory() as directory:
            application = Path(directory)
            original = LOCK.replace('\n', '\r\n').encode()
            (application / 'Cargo.lock').write_text(LOCAL.replace('checksum = "original"', 'checksum = "other"'))
            with self.assertRaisesRegex(RuntimeError, 'original lock restored'):
                guard.validate(application, original)
            self.assertEqual((application / 'Cargo.lock').read_bytes(), original)

    def test_metadata_is_resolution_only_and_evidence_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            application = Path(directory)
            (application / 'Cargo.lock').write_text(LOCAL)
            with patch.object(guard.subprocess, 'run', return_value=type('Result', (), {'stdout': b'{}'})()) as run:
                guard.resolve(application, LOCK.encode(), 'stable', {'OWNED': 'true'})
            self.assertEqual(run.call_args.args[0], ['cargo', '+stable', 'metadata', '--format-version', '1'])
            self.assertEqual((application / '.studio-cargo-metadata.json').read_bytes(), b'{}')
            self.assertEqual((application / 'Cargo.lock').read_text(), LOCAL)

    def test_metadata_failure_restores_original_without_build(self):
        with tempfile.TemporaryDirectory() as directory:
            application = Path(directory)
            (application / 'Cargo.lock').write_text(LOCAL)
            with patch.object(guard.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'cargo')):
                with self.assertRaises(subprocess.CalledProcessError):
                    guard.resolve(application, LOCK.encode())
            self.assertEqual((application / 'Cargo.lock').read_bytes(), LOCK.encode())


if __name__ == '__main__':
    unittest.main()
