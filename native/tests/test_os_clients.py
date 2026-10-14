"""Portable guards for remaining native OS-client builds; no network or candidate installation."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1] / 'typography'
spec = importlib.util.spec_from_file_location('studio_os_builds', HERE / 'build_os_clients.py')
builder = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(HERE))
try:
    spec.loader.exec_module(builder)
finally:
    sys.path.pop(0)


LOCK = '''version = 3
[[package]]
name = "libcosmic"
version = "0.1.0"
source = "git+https://github.com/pop-os/libcosmic.git?rev=abc#abc"
[[package]]
name = "foreign"
version = "1.2.3"
source = "registry+https://github.com/rust-lang/crates.io-index"
checksum = "original"
[[package]]
name = "foreign-git"
version = "0.2.0"
source = "git+https://example.invalid/foreign#original"
'''


class OSClientBuildTests(unittest.TestCase):
    def test_every_pin_has_existing_reviewed_embedding_and_display_profiles(self):
        from embed_fonts import PINS
        roles = json.loads((HERE / 'display-role-profiles.json').read_text())['profiles']
        self.assertEqual(len(builder.SOURCES), 9)
        for name, (_, revision) in builder.SOURCES.items():
            with self.subTest(component=name):
                self.assertIn(revision, PINS)
                self.assertEqual(roles['native-' + revision[:8]]['revision'], revision)
        self.assertNotIn('cosmic-initial-setup', builder.DEFAULTS)
        self.assertIn('cosmic-player', builder.DEFAULTS)
        self.assertIn('cosmic-viewer', builder.DEFAULTS)

    def test_shared_library_gets_window_profile_only_when_a_window_app_is_selected(self):
        revision = builder.SOURCES['cosmic-applets'][1]
        self.assertFalse(builder.library_profiles(['cosmic-applets'])[revision])
        for components in [['cosmic-applets', 'cosmic-monitor'], ['cosmic-monitor', 'cosmic-applets']]:
            self.assertEqual(builder.library_profiles(components), {revision: True})
        self.assertFalse(next(iter(builder.library_profiles(['cosmic-notifications']).values())))

    def test_existing_sources_and_duplicate_components_fail_before_any_clone(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            (work / 'cosmic-player').mkdir()
            with patch.object(builder, 'clone') as clone:
                with self.assertRaises(FileExistsError):
                    builder.build(work, ['cosmic-player'], 2, 'stable')
                clone.assert_not_called()
            with self.assertRaises(ValueError):
                builder.preflight(work, ['cosmic-osd', 'cosmic-osd'])
            with patch.object(builder, 'clone') as clone:
                with self.assertRaises(ValueError):
                    builder.build(work, ['cosmic-osd'], 0, 'stable')
                clone.assert_not_called()

    def test_existing_library_fails_before_source_preparation(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            revision = builder.SOURCES['cosmic-osd'][1]
            (work / ('libcosmic-' + revision[:8])).mkdir()
            with self.assertRaises(FileExistsError):
                builder.preflight(work, ['cosmic-osd'])

    def test_mocked_build_retains_multicall_binaries_and_marks_runtime_unvalidated(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            calls = []
            def clone(url, revision, target):
                target.mkdir()
                if target.name == 'cosmic-applets':
                    (target / 'Cargo.lock').write_text(LOCK, newline='\n')
            def run(*args, **kwargs):
                calls.append(tuple(str(a) for a in args))
                if args[:2] == ('cargo', '+stable') and 'build' in args:
                    target = work / 'target/release'
                    target.mkdir(parents=True)
                    for binary in ['cosmic-applets', 'cosmic-panel-button']:
                        (target / binary).write_bytes(b'\x7fELFowned-test-fixture')
            def metadata(*args, **kwargs):
                (kwargs['cwd'] / 'Cargo.lock').write_text(LOCK.replace(
                    'source = "git+https://github.com/pop-os/libcosmic.git?rev=abc#abc"\n', ''), newline='\n')
                return type('Result', (), {'stdout': b'{"packages":[]}\n'})()
            with patch.object(builder, 'clone', side_effect=clone), \
                 patch.object(builder, 'run', side_effect=run), \
                 patch.object(builder.subprocess, 'run', side_effect=metadata), \
                 patch('builtins.print'):
                reports = builder.build(work, ['cosmic-applets'], 2, 'stable')
            self.assertEqual({report['binary'] for report in reports}, {'cosmic-applets', 'cosmic-panel-button'})
            self.assertTrue(all(not report['installed'] and not report['runtime_validated'] for report in reports))
            release = next(call for call in calls if call[:3] == ('cargo', '+stable', 'build'))
            self.assertIn('--locked', release)
            self.assertIn('cosmic-panel-button', release)
            self.assertTrue(any('cosmic-applets-calendar' in call for call in calls))
            compact = [call for call in calls if Path(call[1]) == HERE.parent / 'dock-icons/prepare.py']
            self.assertEqual(len(compact), 2)
            self.assertIn('--apply', compact[0])
            self.assertLess(calls.index(compact[0]), calls.index(release))
            self.assertIn('--record-binary', compact[1])
            self.assertIn(str(work / 'artifacts/cosmic-applets'), compact[1])
            self.assertIn(str(work / 'artifacts/compact-dock-build.json'), compact[1])
            self.assertGreater(calls.index(compact[1]), calls.index(release))
            self.assertFalse(any('window-controls/prepare.py' in ' '.join(call) for call in calls))
            tooltip = [call for call in calls if Path(call[1]) == HERE.parent / 'dock-icons/prepare_tooltip.py']
            self.assertTrue(tooltip and all('--apply' in call for call in tooltip))
            self.assertLess(calls.index(tooltip[-1]), calls.index(release))

    def test_mocked_metadata_drift_restores_lock_before_any_build(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            def clone(url, revision, target):
                target.mkdir()
                if target.name == 'cosmic-osd':
                    (target / 'Cargo.lock').write_bytes(LOCK.encode())
            def metadata(*args, **kwargs):
                (kwargs['cwd'] / 'Cargo.lock').write_text(LOCK.replace('version = "1.2.3"', 'version = "9.0.0"'), newline='\n')
                return type('Result', (), {'stdout': b'{}'})()
            with patch.object(builder, 'clone', side_effect=clone), \
                 patch.object(builder, 'run') as run, \
                 patch.object(builder.subprocess, 'run', side_effect=metadata):
                with self.assertRaisesRegex(RuntimeError, 'original lock restored'):
                    builder.build(work, ['cosmic-osd'], 2, 'stable')
                self.assertFalse(any(str(call.args[0]) == 'cargo' for call in run.call_args_list))
            self.assertEqual((work / 'cosmic-osd/Cargo.lock').read_bytes(), LOCK.encode())
            self.assertFalse((work / 'artifacts').exists())

    def test_only_original_native_git_to_path_substitution_is_permitted(self):
        native = builder.native_packages(LOCK)
        expected = builder.foreign_dependencies(LOCK, native)
        normalized = LOCK.replace('source = "git+https://github.com/pop-os/libcosmic.git?rev=abc#abc"\n', '')
        self.assertEqual(builder.foreign_dependencies(normalized, native), expected)
        for changed in [normalized.replace('checksum = "original"', 'checksum = "changed"'),
                        normalized.replace('version = "1.2.3"', 'version = "1.2.4"'),
                        normalized.replace('foreign#original', 'foreign#changed'),
                        normalized.replace('version = "0.1.0"', 'version = "0.9.0"')]:
            self.assertNotEqual(builder.foreign_dependencies(changed, native), expected)
        for spelling in ('libcosmic/', 'libcosmic.git/'):
            original = LOCK.replace('libcosmic.git?', spelling + '?')
            self.assertEqual(builder.native_packages(original), native)
            self.assertEqual(builder.foreign_dependencies(original, native), expected)
        misleading = LOCK.replace('libcosmic.git?', 'libcosmic-malware.git?')
        self.assertEqual(builder.native_packages(misleading), set())
        self.assertNotEqual(builder.foreign_dependencies(misleading, native), expected)


if __name__ == '__main__':
    unittest.main()
