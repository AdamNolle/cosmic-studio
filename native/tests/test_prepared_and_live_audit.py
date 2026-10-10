import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parents[1] / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shell = load('studio_build_shell', 'build_shell.py')
audit = load('studio_wayland_audit', 'wayland_audit.py')


class PreparedBuildTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.component = 'cosmic-panel'
        self.revision = 'a' * 40
        self.library_revision = 'b' * 40
        self.patch_relative = 'panel/panel-glass.patch'
        self.source_patch = self.root / 'native' / self.patch_relative
        self.generator = self.root / 'native/typography/patch_libcosmic.py'
        for path, text in ((self.source_patch, 'native panel patch\n'),
                           (self.generator, 'display font generator\n'),
                           (self.root/'native/typography/embed_fonts.py', 'font embedding generator\n'),
                           (self.root/'native/typography/prepare_display_roles.py', 'semantic font roles\n'),
                           (self.root/'native/typography/display-role-profiles.json', 'semantic source pins\n'),
                           (self.root/'fonts/manifest.json', 'font checksums\n'),
                           (self.root/'native/popups/policy.rs', 'popup policy\n')):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        self.work = self.root / 'work'
        self.source = self.work / self.component
        self.library = self.work / ('libcosmic-' + self.library_revision[:7])
        self.source.mkdir(parents=True)
        (self.library / 'src').mkdir(parents=True)
        (self.library / 'src/font.rs').write_text('pub fn display() {}\n')
        self.marker = self.source / '.studio-prepared'
        self.library_marker = self.library / '.studio-typography-prepared'
        self.sentinel = self.source / 'existing-candidate.rs'
        self.sentinel.write_text('preserve this existing candidate\n')
        self.package_patch = mock.patch.object(shell, 'PACKAGE', self.root)
        self.sources_patch = mock.patch.object(shell, 'SOURCES', {
            self.component: (self.revision, self.library_revision, self.patch_relative)})
        self.package_patch.start()
        self.sources_patch.start()
        self.addCleanup(self.package_patch.stop)
        self.addCleanup(self.sources_patch.stop)
        expected = shell.prepared_inputs(self.component)
        self.marker.write_text(json.dumps(expected))
        self.library_marker.write_text(json.dumps(shell.library_inputs(expected)))

    def assert_rejected_without_work(self, message='Stale prepared inputs'):
        before = self.marker.read_bytes()
        with mock.patch.object(shell, 'checkout') as checkout, mock.patch.object(shell, 'run') as run:
            with self.assertRaisesRegex(RuntimeError, message):
                shell.build(self.component, self.work, 4)
            checkout.assert_not_called()
            run.assert_not_called()
        self.assertEqual(self.marker.read_bytes(), before)
        self.assertEqual(self.sentinel.read_text(), 'preserve this existing candidate\n')

    def test_changed_applied_patch_is_rejected_before_checkout_or_cargo(self):
        self.source_patch.write_text('changed native panel patch\n')
        self.assert_rejected_without_work()

    def test_changed_typography_generator_is_rejected_before_checkout_or_cargo(self):
        self.generator.write_text('changed font generator\n')
        self.assert_rejected_without_work()

    def test_changed_popup_policy_is_rejected_before_checkout_or_cargo(self):
        (self.root/'native/popups/policy.rs').write_text('new popup policy\n')
        self.assert_rejected_without_work()

    def test_changed_semantic_font_roles_are_rejected_before_checkout_or_cargo(self):
        (self.root/'native/typography/prepare_display_roles.py').write_text('changed semantic roles\n')
        self.assert_rejected_without_work()

    def test_changed_semantic_font_profiles_are_rejected_before_checkout_or_cargo(self):
        (self.root/'native/typography/display-role-profiles.json').write_text('changed reviewed roles\n')
        self.assert_rejected_without_work()

    def test_changed_pinned_revisions_and_legacy_marker_are_rejected(self):
        for field in ('source_commit', 'library_commit'):
            with self.subTest(field=field):
                record = shell.prepared_inputs(self.component)
                record[field] = 'c' * 40
                self.marker.write_text(json.dumps(record))
                self.assert_rejected_without_work()
        self.marker.write_text(json.dumps({'source_commit': self.revision,
                                           'library_commit': self.library_revision}))
        self.assert_rejected_without_work()

    def test_corrupt_marker_is_rejected(self):
        self.marker.write_text('{')
        self.assert_rejected_without_work('Unverified prepared inputs')

    def test_matching_inputs_reuse_preparation_without_applying_patches(self):
        before = self.marker.read_bytes()
        with mock.patch.object(shell, 'checkout') as checkout, mock.patch.object(shell, 'run') as run:
            with contextlib.redirect_stdout(io.StringIO()):
                shell.build(self.component, self.work, 4)
            self.assertEqual(checkout.call_count, 2)
            commands = [call.args[0] for call in run.call_args_list]
            self.assertEqual([command[:3] for command in commands], [
                ['cargo', '+stable', 'check'], ['cargo', '+stable', 'build']])
        self.assertEqual(self.marker.read_bytes(), before)

    def test_new_client_cannot_inherit_stale_shared_typography(self):
        self.marker.unlink()
        self.generator.write_text('changed font generator\n')
        with mock.patch.object(shell, 'checkout') as checkout, mock.patch.object(shell, 'run') as run:
            with self.assertRaisesRegex(RuntimeError, 'Stale prepared inputs'):
                shell.build(self.component, self.work, 4)
            checkout.assert_not_called()
            run.assert_not_called()
        self.assertFalse(self.marker.exists())


class LiveAuditTests(unittest.TestCase):
    def process(self, proc, pid, executable, args=(), environment=True):
        entry = proc / str(pid)
        entry.mkdir()
        (entry / 'exe').symlink_to(executable)
        (entry / 'comm').write_text(Path(executable.removesuffix(' (deleted)')).name[:15] + '\n')
        (entry / 'cmdline').write_bytes(b'\0'.join([executable.encode(), *args]) + b'\0')
        if environment:
            (entry / 'environ').write_bytes(b'WAYLAND_DISPLAY=wayland-7\0PRIVATE_TOKEN=excluded\0')

    def test_all_native_clients_are_found_from_executable_despite_comm_truncation(self):
        components = ['cosmic-session', 'cosmic-comp', 'cosmic-panel', 'cosmic-launcher',
                      'cosmic-app-library', 'cosmic-workspaces', 'cosmic-greeter',
                      'cosmic-files', 'cosmic-edit', 'cosmic-term', 'cosmic-settings']
        with tempfile.TemporaryDirectory() as folder:
            proc = Path(folder)
            for pid, name in enumerate(components, 100):
                path = '/home/example/.local/share/cosmic-studio/bin/' + name
                self.process(proc, pid, path + (' (deleted)' if name == 'cosmic-app-library' else ''))
            rows = audit.live_components(proc)
        self.assertEqual([row['process'] for row in rows], components)
        library = next(row for row in rows if row['process'] == 'cosmic-app-library')
        self.assertEqual(library['comm'], 'cosmic-app-libr')
        self.assertTrue(library['exe_deleted'])
        self.assertEqual(library['deployed_path'],
                         '/home/example/.local/share/cosmic-studio/bin/cosmic-app-library')
        self.assertEqual(library['exe'], library['deployed_path'])
        self.assertEqual(library['environment'], {'WAYLAND_DISPLAY': 'wayland-7'})

    def test_helpers_are_excluded_but_unreadable_environment_does_not_hide_client(self):
        with tempfile.TemporaryDirectory() as folder:
            proc = Path(folder)
            self.process(proc, 200, '/usr/bin/cosmic-greeter', environment=False)
            self.process(proc, 201, '/opt/ChatGPT', args=(b'--type=renderer',))
            self.process(proc, 202, '/usr/bin/unrelated')
            rows = audit.live_components(proc)
        self.assertEqual([row['process'] for row in rows], ['cosmic-greeter'])
        self.assertEqual(rows[0]['environment'], {})
        self.assertTrue(rows[0]['environment_error'])


if __name__ == '__main__':
    unittest.main()
