import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('native_install', Path(__file__).parents[1] / 'install.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


class WrapperTests(unittest.TestCase):
    def test_app_list_keeps_compact_geometry_and_native_popup_flags(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            query = root / 'dpkg-query'
            query.write_text('#!/bin/sh\nprintf "%s" "$STUDIO_TEST_PACKAGE_VERSION"\n')
            query.chmod(0o755)
            candidate = root / 'cosmic-app-list'
            candidate.write_text('#!/bin/sh\nprintf "%s:%s:%s:%s" "${0##*/}" '
                                 '"${COSMIC_STUDIO_COMPACT_DOCK:-0}" '
                                 '"${COSMIC_STUDIO_POPUP_GLASS:-0}" "$1"\n')
            candidate.chmod(0o755)
            distro = root / 'distro'
            distro.write_text('#!/bin/sh\nprintf "distro:%s:%s:%s" '
                              '"${COSMIC_STUDIO_COMPACT_DOCK:-0}" '
                              '"${COSMIC_STUDIO_POPUP_GLASS:-0}" "$1"\n')
            distro.chmod(0o755)
            wrapper = root / 'wrapper'
            wrapper.write_text(native.wrapper_for('cosmic-app-list', candidate, 'pinned', distro))
            wrapper.chmod(0o755)
            env = os.environ.copy()
            for name in ('COSMIC_STUDIO_COMPACT_DOCK', 'COSMIC_STUDIO_POPUP_GLASS'):
                env.pop(name, None)
            env.update(PATH=str(root) + os.pathsep + env['PATH'], STUDIO_TEST_PACKAGE_VERSION='pinned')
            self.assertEqual(subprocess.check_output([str(wrapper), 'with spaces'], env=env, text=True),
                             'cosmic-app-list:1:1:with spaces')
            env['STUDIO_TEST_PACKAGE_VERSION'] = 'new-package'
            self.assertEqual(subprocess.check_output([str(wrapper), 'with spaces'], env=env, text=True),
                             'distro:0:0:with spaces')

    def test_candidate_windows_enable_glass_without_changing_editor_content(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            query = root / 'dpkg-query'
            query.write_text('#!/bin/sh\nprintf pinned\n')
            query.chmod(0o755)
            candidate = root / 'candidate'
            candidate.write_text('#!/bin/sh\nprintf "%s:%s" "${COSMIC_STUDIO_WINDOW_GLASS:-0}" "${COSMIC_STUDIO_POPUP_GLASS:-0}"\n')
            candidate.chmod(0o755)
            env = os.environ.copy()
            env['COSMIC_STUDIO_WINDOW_GLASS'] = '1'
            env.pop('COSMIC_STUDIO_POPUP_GLASS', None)
            env['PATH'] = str(root) + os.pathsep + env['PATH']
            for component, expected in [('cosmic-files', '1:1'), ('cosmic-settings', '1:1'),
                                        ('cosmic-store', '1:1'), ('cosmic-monitor', '1:1'),
                                        ('cosmic-player', '1:1'), ('cosmic-viewer', '1:1'),
                                        ('cosmic-edit', '0:1'), ('cosmic-term', '0:1')]:
                with self.subTest(component=component):
                    wrapper = root / 'wrapper'
                    wrapper.write_text(native.wrapper_for(component, candidate, 'pinned'))
                    wrapper.chmod(0o755)
                    self.assertEqual(subprocess.check_output([str(wrapper)], env=env, text=True), expected)

    def test_multicall_alias_checks_owning_package_and_keeps_argv_zero(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            candidate = root / 'cosmic-applet-time'
            candidate.write_text('#!/bin/sh\nprintf "%s:%s" "${0##*/}" "$1"\n')
            candidate.chmod(0o755)
            query = root / 'dpkg-query'
            query.write_text('#!/bin/sh\n[ "$3" = cosmic-applets ] || exit 9\nprintf pinned\n')
            query.chmod(0o755)
            wrapper = root / 'wrapper'
            wrapper.write_text(native.wrapper_for('cosmic-applet-time', candidate, 'pinned'))
            wrapper.chmod(0o755)
            env = os.environ.copy()
            env['PATH'] = str(root) + ':' + env['PATH']
            result = subprocess.check_output([str(wrapper), 'with spaces'], env=env, text=True)
            self.assertEqual(result, 'cosmic-applet-time:with spaces')

    def test_package_upgrade_uses_distro_binary_and_preserves_arguments(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            files = {
                'dpkg-query': '#!/bin/sh\nprintf "%s" "$STUDIO_TEST_PACKAGE_VERSION"\n',
                'candidate': '#!/bin/sh\nprintf "candidate:%s:%s\\n" "$COSMIC_STUDIO_GLASS" "$1"\n',
                'distro': '#!/bin/sh\nprintf "distro:%s\\n" "$1"\n',
            }
            for name, text in files.items():
                (root / name).write_text(text)
                (root / name).chmod(0o755)
            wrapper = root / 'wrapper'
            wrapper.write_text(native.wrapper_for('cosmic-panel', root / 'candidate',
                                                  'pinned-version', root / 'distro'))
            wrapper.chmod(0o755)
            env = os.environ.copy()
            env.pop('COSMIC_STUDIO_GLASS', None)
            env['PATH'] = str(root) + ':' + env['PATH']
            env['STUDIO_TEST_PACKAGE_VERSION'] = 'pinned-version'
            result = subprocess.check_output([str(wrapper), 'argument with spaces'], env=env, text=True)
            self.assertEqual(result, 'candidate:1:argument with spaces\n')
            env['STUDIO_TEST_PACKAGE_VERSION'] = 'upgraded-version'
            result = subprocess.check_output([str(wrapper), 'argument with spaces'], env=env, text=True)
            self.assertEqual(result, 'distro:argument with spaces\n')
            env['STUDIO_TEST_PACKAGE_VERSION'] = 'pinned-version'
            (root / 'candidate').unlink()
            result = subprocess.check_output([str(wrapper), 'argument with spaces'], env=env, text=True)
            self.assertEqual(result, 'distro:argument with spaces\n')


class RestoreTests(unittest.TestCase):
    def test_multicall_install_shares_one_inode_and_restores_all_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'source'
            source.write_bytes(b'\x7fELFtest candidate')
            source.chmod(0o755)
            with patch.object(native, 'DATA', root/'data'), patch.object(native, 'BIN', root/'bin'), \
                 patch.object(native.os, 'geteuid', return_value=1000), \
                 patch.object(native.subprocess, 'check_output', return_value='1~82e7cd8'):
                report = native.install({'cosmic-app-list': source, 'cosmic-applet-time': source})
                canonical = root/'data/bin/cosmic-applets'
                for name in ['cosmic-app-list', 'cosmic-applet-time']:
                    alias = root/'data/bin'/name
                    self.assertTrue(alias.is_symlink())
                    self.assertEqual(alias.stat().st_ino, canonical.stat().st_ino)
                native.restore(report)
                self.assertFalse(canonical.exists())
                self.assertFalse((root/'data/bin/cosmic-app-list').is_symlink())
                self.assertFalse((root/'bin/cosmic-applet-time').exists())

    def test_absence_permissions_and_symlink_are_restored(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'candidate'
            native.restore_entry(path, None)
            self.assertFalse(path.exists())
            native.atomic(path, b'original', 0o751)
            original = native.saved(path)
            native.atomic(path, b'new', 0o755)
            native.restore_entry(path, original)
            self.assertEqual(path.read_bytes(), b'original')
            self.assertEqual(path.stat().st_mode & 0o777, 0o751)
            path.unlink()
            path.symlink_to('absent-target')
            original = native.saved(path)
            native.atomic(path, b'replacement')
            native.restore_entry(path, original)
            self.assertTrue(path.is_symlink())
            self.assertEqual(path.readlink(), Path('absent-target'))

    def test_restore_protects_later_user_edit(self):
        import json
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'candidate'
            native.atomic(path, b'installed', 0o755)
            report = Path(folder) / 'manifest.json'
            report.write_text(json.dumps({'status': 'applied', 'before': {str(path): None},
                                         'after': {str(path): native.fingerprint(path)}}))
            native.atomic(path, b'edited')
            with self.assertRaisesRegex(RuntimeError, 'Later changes'):
                native.restore(report)
            self.assertEqual(path.read_bytes(), b'edited')


if __name__ == '__main__':
    unittest.main()
