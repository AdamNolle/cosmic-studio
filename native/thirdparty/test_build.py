import importlib.util
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('studio_thirdparty_build', Path(__file__).with_name('build.py'))
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class LockedBuildGateTests(unittest.TestCase):
    def test_rejected_alias_resolution_restores_lock_before_any_compilation(self):
        for metadata_status in (0, 1):
            with self.subTest(metadata_status=metadata_status), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                app = root/'sources/app-caffeine-native'
                app.mkdir(parents=True)
                lock = app/'Cargo.lock'
                lock.write_bytes(b'exact original lock')
                calls = []
                def metadata(arguments, **kwargs):
                    calls.append(arguments)
                    lock.write_bytes(b'rejected dependency resolution')
                    return SimpleNamespace(returncode=metadata_status)
                checks = [app/'.studio-thirdparty-prepared.json', ValueError('foreign dependency graph changed')]
                with patch.object(build.prepare, 'prepare', side_effect=checks), \
                        patch.object(subprocess, 'run', side_effect=metadata):
                    with self.assertRaises((ValueError, RuntimeError)):
                        build.run('caffeine', root/'sources', root/'target', root/'artifacts', None, 1)
                self.assertEqual(lock.read_bytes(), b'exact original lock')
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0][1], 'metadata')
                self.assertFalse((root/'artifacts/caffeine/build.json').exists())


if __name__ == '__main__':
    unittest.main()
