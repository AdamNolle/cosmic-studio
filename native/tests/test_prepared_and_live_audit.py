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
                           (self.root/'native/panel/prepare_keyboard_focus.py', 'focus generator\n'),
                           (self.root/'native/panel/keyboard_focus_seats.rs', 'focus ownership module\n'),
                           (self.root/'native/panel/prepare_keyboard_input.py', 'input generator\n'),
                           (self.root/'native/panel/keyboard_input_state.rs', 'input ledger module\n'),
                           (self.root/'native/panel/prepare_keyboard_context.py', 'context generator\n'),
                           (self.root/'native/panel/keyboard_event_context.rs', 'event context module\n'),
                           (self.root/'native/panel/prepare_client_keymap.py', 'keymap generator\n'),
                           (self.root/'native/panel/client_keymap.rs', 'keymap module\n'),
                           (self.root/'native/panel/prepare_client_iced.py', 'iced generator\n'),
                           (self.root/'native/panel/client_iced_event.rs', 'iced module\n'),
                           (self.root/'native/panel/client_key_tables.rs', 'iced tables\n'),
                           (self.root/'native/panel/pinned-iced-keymap-sources.json.gz', 'iced fixture\n'),
                           (self.root/'native/panel/pinned-iced-keymap.LICENSE', 'iced license\n'),
                           (self.root/'native/panel/prepare_client_focus_match.py', 'active focus generator\n'),
                           (self.root/'native/panel/client_focus_match.rs', 'active focus module\n'),
                           (self.root/'native/panel/prepare_iced_keyboard_dispatch.py', 'dispatch generator\n'),
                           (self.root/'native/panel/iced_keyboard_dispatch.rs', 'dispatch module\n'),
                           (self.root/'native/panel/pinned-iced-state.json.gz', 'dispatch fixture\n'),
                           (self.root/'native/panel/prepare_iced_keyboard_route.py', 'wrapper route generator\n'),
                           (self.root/'native/panel/iced_keyboard_route.rs', 'wrapper route module\n'),
                           (self.root/'native/panel/prepare_overflow_keyboard_isolation.py', 'overflow isolation generator\n'),
                           (self.root/'native/panel/overflow_keyboard_isolation.rs', 'overflow isolation module\n'),
                           (self.root/'native/panel/prepare_client_keyboard_delivery.py', 'client delivery generator\n'),
                           (self.root/'native/panel/client_keyboard_delivery.rs', 'client delivery module\n'),
                           (self.root/'native/panel/prepare_overflow_preflight.py', 'overflow preflight generator\n'),
                           (self.root/'native/panel/pinned-overflow-preflight.json.gz', 'overflow preflight fixture\n'),
                            (self.root/'native/panel/prepare_client_overflow_route.py', 'client overflow route generator\n'),
                            (self.root/'native/panel/client_overflow_route.rs', 'client overflow route module\n'),
                           (self.root/'native/typography/lock_guard.py', 'dependency guard\n'),
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

    def test_changed_focus_generator_is_rejected_before_checkout_or_cargo(self):
        (self.root/'native/panel/prepare_keyboard_focus.py').write_text('changed focus generator\n')
        self.assert_rejected_without_work()

    def test_changed_focus_module_is_rejected_before_checkout_or_cargo(self):
        (self.root/'native/panel/keyboard_focus_seats.rs').write_text('changed focus module\n')
        self.assert_rejected_without_work()

    def test_changed_input_generator_or_module_is_rejected_before_checkout_or_cargo(self):
        for name in ('prepare_keyboard_input.py', 'keyboard_input_state.rs'):
            with self.subTest(name=name):
                path=self.root/'native/panel'/name
                before=path.read_bytes()
                path.write_text('changed native input\n')
                self.assert_rejected_without_work()
                path.write_bytes(before)

    def test_changed_context_generator_or_module_is_rejected_before_checkout_or_cargo(self):
        for name in ('prepare_keyboard_context.py', 'keyboard_event_context.rs'):
            with self.subTest(name=name):
                path=self.root/'native/panel'/name
                before=path.read_bytes()
                path.write_text('changed native context\n')
                self.assert_rejected_without_work()
                path.write_bytes(before)

    def test_changed_client_keymap_generator_or_module_is_rejected_before_checkout_or_cargo(self):
        for name in ('prepare_client_keymap.py', 'client_keymap.rs'):
            with self.subTest(name=name):
                path=self.root/'native/panel'/name
                before=path.read_bytes()
                path.write_text('changed native keymap\n')
                self.assert_rejected_without_work()
                path.write_bytes(before)

    def test_changed_client_focus_match_inputs_are_rejected_before_checkout_or_cargo(self):
        for name in ('prepare_client_focus_match.py', 'client_focus_match.rs'):
            with self.subTest(name=name):
                path=self.root/'native/panel'/name
                before=path.read_bytes()
                path.write_text('changed native active focus\n')
                self.assert_rejected_without_work()
                path.write_bytes(before)

    def test_changed_keyboard_route_inputs_are_rejected_before_checkout_or_cargo(self):
        for name in ('prepare_iced_keyboard_route.py', 'iced_keyboard_route.rs',
                     'prepare_overflow_keyboard_isolation.py', 'overflow_keyboard_isolation.rs',
                     'prepare_client_keyboard_delivery.py', 'client_keyboard_delivery.rs',
                     'prepare_overflow_preflight.py', 'pinned-overflow-preflight.json.gz',
                     'prepare_client_overflow_route.py', 'client_overflow_route.rs'):
            with self.subTest(name=name):
                path=self.root/'native/panel'/name
                before=path.read_bytes()
                path.write_text('changed native wrapper route\n')
                self.assert_rejected_without_work()
                path.write_bytes(before)

    def test_changed_keyboard_dispatch_inputs_are_rejected_before_checkout_or_cargo(self):
        for name in ('prepare_iced_keyboard_dispatch.py', 'iced_keyboard_dispatch.rs', 'pinned-iced-state.json.gz'):
            with self.subTest(name=name):
                path=self.root/'native/panel'/name
                before=path.read_bytes()
                path.write_text('changed native message attribution\n')
                self.assert_rejected_without_work()
                path.write_bytes(before)

    def test_changed_client_iced_inputs_are_rejected_before_checkout_or_cargo(self):
        for name in ('prepare_client_iced.py', 'client_iced_event.rs', 'client_key_tables.rs',
                     'pinned-iced-keymap-sources.json.gz', 'pinned-iced-keymap.LICENSE'):
            with self.subTest(name=name):
                path=self.root/'native/panel'/name
                before=path.read_bytes()
                path.write_text('changed native conversion\n')
                self.assert_rejected_without_work()
                path.write_bytes(before)

    def test_changed_dependency_guard_is_rejected_before_checkout_or_cargo(self):
        (self.root/'native/typography/lock_guard.py').write_text('changed dependency guard\n')
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
        original = b'version = 3\npackage = []\n'
        with mock.patch.object(shell, 'checkout') as checkout, mock.patch.object(shell, 'run') as run, \
             mock.patch.object(shell.subprocess, 'check_output', return_value=original) as upstream, \
             mock.patch.object(shell.lock_guard, 'resolve') as resolve, \
             mock.patch.object(shell.lock_guard, 'validate') as validate:
            with contextlib.redirect_stdout(io.StringIO()):
                shell.build(self.component, self.work, 4)
            upstream.assert_called_once_with(['git', 'show', self.revision + ':Cargo.lock'], cwd=self.source)
            resolve.assert_called_once_with(self.source, original)
            validate.assert_called_once_with(self.source, original)
            self.assertEqual(checkout.call_count, 2)
            commands = [call.args[0] for call in run.call_args_list]
            self.assertEqual([command[:3] for command in commands], [
                ['cargo', '+stable', 'check'], ['cargo', '+stable', 'build']])
            self.assertTrue(all('--locked' in command for command in commands))
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
