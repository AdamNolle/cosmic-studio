import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('rustc'), 'Rust required')
class PrivateSpecimenGuardTests(unittest.TestCase):
    def test_real_owned_socket_private_runtime_and_host_path_rejection(self):
        with tempfile.TemporaryDirectory(prefix='cs-panel-') as folder, tempfile.TemporaryDirectory() as outside:
            root = Path(folder)
            config, data, home = root / 'config', root / 'data', root / 'home'
            for p in [config, data, home / '.config', home / '.local/share']:
                p.mkdir(parents=True)
            channel = socket.socket(socket.AF_UNIX)
            channel.bind(str(root / 'wayland-private'))
            other = socket.socket(socket.AF_UNIX)
            other.bind(str(Path(outside) / 'wayland-other'))
            try:
                source = root / 'tests.rs'
                source.write_text('mod guard { include!("' + str(HERE / 'specimen/guard.rs') + '"); }\n' + r'''
#[test] fn accepts_owned_private_native_socket() {
    let root=std::path::Path::new("RUNTIME");
    assert!(guard::validate(root,std::path::Path::new("wayland-private"),&root.join("config"),&root.join("data"),USER,&root.join("home")).is_ok());
}
#[test] fn refuses_another_wayland_socket_and_another_owner() {
    let root=std::path::Path::new("RUNTIME");
    assert!(guard::validate(root,std::path::Path::new("OUTSIDE"),&root.join("config"),&root.join("data"),USER,&root.join("home")).is_err());
    assert!(guard::validate(root,std::path::Path::new("wayland-private"),&root.join("config"),&root.join("data"),USER+1,&root.join("home")).is_err());
}
#[test] fn refuses_real_host_configuration_and_shared_data() {
    let root=std::path::Path::new("RUNTIME");
    assert!(guard::validate(root,std::path::Path::new("wayland-private"),&root.join("home/.config"),&root.join("data"),USER,&root.join("home")).is_err());
    assert!(guard::validate(root,std::path::Path::new("wayland-private"),&root.join("config"),&root.join("home/.local/share"),USER,&root.join("home")).is_err());
    assert!(guard::validate(root,std::path::Path::new("wayland-private"),&root.join("config"),&root.join("config"),USER,&root.join("home")).is_err());
}
'''.replace('RUNTIME', str(root)).replace('OUTSIDE', str(Path(outside) / 'wayland-other')).replace('USER', str(os.geteuid())))
                binary = root / 'guard-tests'
                result = subprocess.run(['rustc', '--edition=2024', '--test', str(source), '-o', str(binary)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                result = subprocess.run([str(binary)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('3 passed', result.stdout)
                root.chmod(0o755)
                result = subprocess.run([str(binary), 'accepts_owned_private_native_socket'], capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
            finally:
                channel.close()
                other.close()
