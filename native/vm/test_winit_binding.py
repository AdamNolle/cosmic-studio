"""Source-only exact-Winit repair guards, not an EGL/runtime test."""
import gzip
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]/'compositor'
spec = importlib.util.spec_from_file_location('winit_binding', HERE/'prepare_winit_binding.py')
binding = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binding)


class WinitBindingGuards(unittest.TestCase):
    def original(self):
        return gzip.decompress((HERE/'pinned-winit.rs.gz').read_bytes())

    def test_exact_original_resizes_then_binds_age_and_submission(self):
        original = self.original()
        self.assertEqual(hashlib.sha256(original).hexdigest(), binding.INPUT_SHA256)
        updated = binding.transform(original).decode()
        body = updated[updated.index('pub fn render_output'):updated.index('pub fn all_outputs')]
        self.assertLess(body.index('Failed to prepare window buffer'), body.index('Self::make_window_current(&mut self.backend)?;'))
        self.assertLess(body.index('Self::make_window_current(&mut self.backend)?;'), body.index('let age ='))
        self.assertIn('std::mem::drop(fb);\n                // Offscreen work', body)
        self.assertIn('Self::make_window_current(&mut self.backend)?;\n                self.backend\n                    .submit(damage.map', body)
        self.assertEqual(body.count('Self::make_window_current(&mut self.backend)?;'), 2)
        self.assertIn('fn make_window_current(backend: &mut WinitGraphicsBackend<GlowRenderer>)', body)
        self.assertNotIn('fn make_window_current(&mut self)', body)
        self.assertIn('egl::MakeCurrent(**display, surface, surface, context.get_context_handle())', body)
        self.assertIn('egl::GetError()', body)
        for forbidden in ('CreateContext(', 'CreateWindowSurface(', 'DestroySurface(', 'sleep(', 'thread::spawn'):
            self.assertNotIn(forbidden, body)
        self.assertTrue(updated.startswith('// SPDX-License-Identifier: GPL-3.0-only'))
        self.assertEqual(hashlib.sha256((HERE/'pinned-winit.LICENSE').read_bytes()).hexdigest(),
                         '3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986')

    def test_drift_repeated_source_or_wrong_foreign_identity_refused(self):
        original = self.original()
        for data in (original+b'\n', binding.transform(original)):
            with self.assertRaises(ValueError):
                binding.transform(data)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder);src = root/binding.RELATIVE;src.parent.mkdir(parents=True);src.write_bytes(original)
            (root/'Cargo.lock').write_text('[[package]]\nname="smithay"\nversion="0.7.0"\nsource="git+https://evil.invalid/smithay#e3d461a"\n')
            with patch.object(binding.subprocess, 'check_output', side_effect=[binding.COMP, original]):
                with self.assertRaisesRegex(ValueError, 'Smithay identity'):
                    binding.prepare(root, root/'change.patch', True)
            self.assertEqual(src.read_bytes(), original)
            self.assertFalse((root/'change.patch').exists())

    def test_real_git_applies_patch_byte_exact_with_original_lock_unchanged(self):
        original = self.original()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder);src = root/binding.RELATIVE;src.parent.mkdir(parents=True);src.write_bytes(original)
            lock = ('[[package]]\nname="smithay"\nversion="0.7.0"\nsource="'+binding.SMITHAY_SOURCE+'"\n').encode()
            (root/'Cargo.lock').write_bytes(lock)
            subprocess.run(['git', 'init', '--quiet', str(root)], check=True)
            # No host policy changes: only these fixture Git commands use LF.
            subprocess.run(['git', '-c', 'core.autocrlf=false', 'add', '.'], cwd=root, check=True)
            subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                            'commit', '--quiet', '-m', 'fixture'], cwd=root, check=True)
            real = binding.subprocess.check_output
            def output(args, **kwargs):
                if args == ['git', 'rev-parse', 'HEAD']:
                    return binding.COMP
                return real(args, **kwargs)
            real_run = binding.subprocess.run
            def run(args, **kwargs):
                if args[:2] == ['git', 'apply']:
                    args = ['git', '-c', 'core.autocrlf=false', *args[1:]]
                return real_run(args, **kwargs)
            with patch.object(binding.subprocess, 'check_output', side_effect=output), \
                    patch.object(binding.subprocess, 'run', side_effect=run):
                report = binding.prepare(root, root/'change.patch', True)
            self.assertTrue(report['applied'])
            self.assertEqual(src.read_bytes(), binding.transform(original))
            self.assertEqual((root/'Cargo.lock').read_bytes(), lock)
            self.assertEqual(report['postimage_sha256'], hashlib.sha256(src.read_bytes()).hexdigest())


if __name__ == '__main__':
    unittest.main()
