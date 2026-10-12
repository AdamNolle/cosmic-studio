"""Read-only VM installation safety checks; never invoke distinst."""
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('studio_install_guard', Path(__file__).with_name('install_guest.py'))
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
driver_spec = importlib.util.spec_from_file_location('studio_install_driver', Path(__file__).with_name('run_install.py'))
driver = importlib.util.module_from_spec(driver_spec)
driver_spec.loader.exec_module(driver)


class DiskGuards(unittest.TestCase):
    def disk(self):
        return {'path': '/dev/sda', 'type': 'disk', 'model': 'VBOX HARDDISK',
                'serial': 'VB-test-only', 'size': 160 * guard.GIB, 'ro': False}

    def test_only_exact_whole_empty_virtual_disk_is_accepted(self):
        guard.validate_disk(self.disk(), '/dev/sda', 'VB-test-only', 160 * guard.GIB)

    def test_wrong_disk_partition_size_serial_model_and_readonly_are_refused(self):
        variants = {'path': '/dev/sdb', 'type': 'part', 'model': 'Physical disk',
                    'serial': 'another-vm', 'size': 159 * guard.GIB, 'ro': True,
                    'children': [{'path': '/dev/sda1', 'type': 'part'}]}
        for key, value in variants.items():
            disk = self.disk()
            disk[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                guard.validate_disk(disk, '/dev/sda', 'VB-test-only', 160 * guard.GIB)

    def test_missing_identification_and_unapproved_sizes_are_refused(self):
        for serial, size in [('', 160 * guard.GIB), ('VB-test-only', 1),
                             ('VB-test-only', 513 * guard.GIB)]:
            with self.subTest(serial=serial, size=size), self.assertRaises(ValueError):
                guard.validate_disk(self.disk(), '/dev/sda', serial, size)


class DriverGuards(unittest.TestCase):
    def test_installer_logs_remove_secrets_and_credential_related_lines(self):
        secret = 'ExampleOnlyFakeSecret12345'
        self.assertNotIn(secret, driver.clean_log('\x1b[32mvalue=' + secret + '\x1b[0m\n', secret))
        self.assertEqual(driver.clean_log('password = transformed-sensitive-data\n', secret),
                         '[credential-related installer log redacted]\n')
        self.assertEqual(driver.clean_log('safe progress\n', secret), 'safe progress\n')

    def test_mocked_install_uses_lf_binary_stdin_not_password_arguments(self):
        secret = 'ExampleOnlyFakeSecret12345'
        class Input(io.BytesIO):
            def close(self):
                self.sent = self.getvalue()
                super().close()
        class Process:
            stdin = Input()
            stdout = iter([b'EMPTY_VM_DISK_AND_LIVE_ISO_VALIDATED\n', b'DISTINST_INSTALL_SUCCEEDED\n'])
            def wait(self):
                return 0
        process = Process()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'ssh-live.conf').write_text('test fixture; never used by a real SSH process')
            argv = ['run_install.py', '--root', str(root), '--expected-serial', 'VB-test-only',
                    '--expected-bytes', str(160 * guard.GIB), '--iso-root', '/cdrom/test', '--install']
            with patch.object(driver.platform, 'system', return_value='Windows'), \
                 patch.dict(os.environ, {'SystemRoot': 'C:/Windows'}), \
                 patch.object(driver.sys, 'argv', argv), \
                 patch.object(driver, 'credential', return_value=secret), \
                 patch.object(driver, 'private_acl'), \
                 patch.object(driver.subprocess, 'run') as preflight, \
                 patch.object(driver.subprocess, 'Popen', return_value=process) as popen, \
                 patch('builtins.print'):
                self.assertEqual(driver.main(), 0)
            self.assertEqual(process.stdin.sent, secret.encode('ascii') + b'\n')
            self.assertNotIn(b'\r', process.stdin.sent)
            self.assertNotIn(secret, ' '.join(popen.call_args.args[0]))
            self.assertNotIn('--password', ' '.join(popen.call_args.args[0]))
            self.assertNotIn(' --install', preflight.call_args.args[0][-1])
            self.assertIn(' --install', popen.call_args.args[0][-1])
            report = json.loads(next(root.glob('distinst-*.json')).read_text())
            self.assertTrue(report['install_command_succeeded'])
            self.assertFalse(report['first_boot_validated'])
            self.assertFalse(report['desktop_validated'])


if __name__ == '__main__':
    unittest.main()
