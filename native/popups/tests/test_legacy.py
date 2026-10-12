import gzip
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from test_popups import RUST_MATERIAL_TESTS, source_copy

HERE = Path(__file__).resolve().parents[1]
LEGACY = HERE / 'legacy'
SPEC = importlib.util.spec_from_file_location('legacy_caffeine', LEGACY / 'caffeine.py')
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)


class LegacyAdapterTests(unittest.TestCase):
    def test_exact_old_source_applies_only_managed_popup_surface_material(self):
        files = json.loads(gzip.decompress((LEGACY / 'pinned-inputs.json.gz').read_bytes()))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source_copy(root, files)
            (root / 'src/font.rs').write_text('Existing native fonts\n')
            report = adapter.prepare(root, root / 'old-popup.patch', apply=True, require_backend=False)
            self.assertTrue(report['applied'])
            app = (root / 'src/app/cosmic.rs').read_text()
            self.assertIn('Some((_, SurfaceIdWrapper::Popup(_), _))', app)
            self.assertIn('iced_winit::commands::blur::available()', app)
            self.assertIn('Task::batch([blur, get_popup(settings)])', app)
            self.assertIn('studio_refresh_popup_blur()', app)
            self.assertIn('desired.then(|| vec![iced_core::Rectangle::new', app)
            self.assertIn('iced_core::Size::INFINITY', app)
            self.assertNotIn('iced_core::Size::INFINITE', app)
            api = json.loads((LEGACY/'compatibility.json').read_text())['native_api_sha256']
            self.assertEqual(api['iced/core/src/size.rs'],
                             '7ec056939a02804f65076ca3bf2b804ec033a5bd3a91dbcae76fca13614ad87d')
            self.assertIn('theme.cosmic().is_high_contrast', app)
            self.assertEqual((root / 'src/core.rs').read_text(), files['src/core.rs'])
            self.assertEqual((root / 'Cargo.toml').read_text(), files['Cargo.toml'])
            self.assertEqual((root / 'src/font.rs').read_text(), 'Existing native fonts\n')
            self.assertNotIn('.transparent', (root / 'src/theme/popup_material.rs').read_text())
            with self.assertRaisesRegex(ValueError, 'Changed legacy pinned input'):
                adapter.prepare(root, root / 'repeat.patch', apply=True, require_backend=False)

    def test_changed_source_and_absent_backport_reject_before_mutation(self):
        files = json.loads(gzip.decompress((LEGACY / 'pinned-inputs.json.gz').read_bytes()))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source_copy(root, files)
            with self.assertRaisesRegex(ValueError, 'backport'):
                adapter.prepare(root, root / 'missing.patch')
            self.assertFalse((root / 'missing.patch').exists())
            (root / 'src/app/cosmic.rs').write_text(files['src/app/cosmic.rs'] + '// changed\n')
            with self.assertRaisesRegex(ValueError, 'Changed legacy pinned input'):
                adapter.prepare(root, root / 'changed.patch', require_backend=False)
            self.assertFalse((root / 'changed.patch').exists())
            self.assertFalse((root / 'src/popup_policy.rs').exists())

    @unittest.skipUnless(shutil.which('rustc'), 'Rust required')
    def test_actual_legacy_material_preserves_opaque_source_and_native_semantics(self):
        text = RUST_MATERIAL_TESTS
        text = text.replace('transparent_background', 'background').replace('transparent_primary', 'primary').replace('transparent_secondary', 'secondary')
        text = text.replace('pub transparent: bool', 'pub unused_transparent: bool').replace('transparent:false', 'unused_transparent:false')
        # Old Theme has no transparency flag. Assert exact original Arc and
        # per-popup material ownership instead; unchanged high-contrast palette.
        text = text.replace('assert!(!main.transparent);assert!(popup.transparent);', 'assert!(!is_material(&main));assert!(is_material(&popup));')
        text = text.replace('assert!(!fallback.transparent);', 'assert!(!is_material(&fallback));')
        text = text.replace('source.transparent=true;', '')
        text = text.replace('assert!(!popup.transparent);', 'assert!(!is_material(&popup));')
        text = text.replace('POLICY_PATH', str(HERE / 'policy.rs')).replace('MATERIAL_PATH', str(LEGACY / 'material.rs')).replace('METHOD_BODY', (LEGACY / 'theme_method.rs').read_text())
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'legacy-tests.rs'
            source.write_text(text)
            binary = root / 'legacy-tests'
            result = subprocess.run(['rustc', '--edition=2024', '--test', str(source), '-o', str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            env = os.environ.copy()
            env['COSMIC_STUDIO_POPUP_GLASS'] = '1'
            result = subprocess.run([str(binary), '--test-threads=1'], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('10 passed', result.stdout)
