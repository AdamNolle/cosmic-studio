# SPDX-License-Identifier: GPL-3.0-only
import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('overflow_preflight', HERE / 'prepare_overflow_preflight.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class OverflowPreflightTests(unittest.TestCase):
    def test_original_defect_and_new_actual_effect_order(self):
        original = module.original()
        self.assertLess(original.index('self.close_popups('), original.index('self.overflow_elements_for_id('))
        self.assertLess(original.index('cosmic_workspaces.hide()'), original.index('self.overflow_elements_for_id('))
        self.assertLess(original.index('compositor_state.create_surface('), original.index('self.overflow_elements_for_id('))
        text = module.transform(module.expected_inputs())[module.SOURCE]
        opening = text.split('// Opening preflight is read-only.', 1)[1]
        first_effect = opening.index('self.close_popups(')
        for check in ('self.overflow_elements_for_id(', 'self.space.element_location(', 'parent.is_alive()',
                      'let bbox = element.geometry()', 'let popup_bbox = popup_element.geometry()'):
            self.assertLess(opening.index(check), first_effect)
        for effect in ('cosmic_workspaces.hide()', 'compositor_state.create_surface(', 'XdgPositioner::new('):
            self.assertGreater(opening.index(effect), first_effect)
        self.assertNotIn('unwrap_or_default()', opening)

    def test_recovery_does_not_require_missing_anchor_or_parent(self):
        text = module.transform(module.expected_inputs())[module.SOURCE]
        recovery = text.split('if force_hide || has_popup {', 1)[1].split('// Opening preflight', 1)[0]
        for token in ('self.close_popups(|_| false);', 'self.overflow_popup = None;', 'return Ok(());'):
            self.assertIn(token, recovery)
        self.assertNotIn('overflow_elements_for_id(', recovery)
        self.assertNotIn('is_alive()', recovery)

    def test_original_serial_geometry_and_protocol_tail_preserved(self):
        before = module.expected_inputs()
        after = module.transform(before)
        for name in before:
            if name != module.SOURCE:
                self.assertEqual(before[name], after[name])
        marker = '        positioner.set_anchor_rect'
        old_tail = before[module.SOURCE].split(marker, 1)[1]
        expected_tail = old_tail.replace('                parent: self.layer.as_ref().unwrap().wl_surface().clone(),', '                parent,', 1)
        self.assertEqual(after[module.SOURCE].split(marker, 1)[1], expected_tail)
        self.assertIn('c_popup.xdg_popup().grab(&seat.1, seat.0);', expected_tail)
        self.assertIn('popup_bbox.size.w.max(1)', expected_tail)
        self.assertIn('if matches!(event, Event::Keyboard(_)) { return; }', after[module.prerequisite().prerequisite().MODULE])

    def test_drift_reapply_and_raw_bytes_refused(self):
        for name in (module.SOURCE, module.prerequisite().KEYBOARD):
            files = module.expected_inputs()
            files[name] += '\n'
            with self.assertRaises(ValueError):
                module.transform(files)
        with self.assertRaises(ValueError):
            module.transform(module.transform(module.expected_inputs()))
        with patch.object(module, 'FIXTURE_SHA', '0' * 64):
            with self.assertRaises(ValueError):
                module.original()

    def test_panel_only_fingerprints(self):
        builder = (HERE.parent / 'build_shell.py').read_text(encoding='utf-8')
        for token in ('overflow_preflight_generator_sha256', 'overflow_preflight_fixture_sha256'):
            self.assertEqual(builder.count("'" + token + "'"), 2)
        self.assertIn("work / 'overflow-preflight.patch'", builder)
        self.assertLess(builder.index("work / 'client-keyboard-delivery.patch'"), builder.index("work / 'overflow-preflight.patch'"))

    def test_real_git_apply_lock_preservation_and_existing_patch_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'source'
            root.mkdir()
            p = root / module.SOURCE
            p.parent.mkdir(parents=True)
            p.write_bytes(module.original().encode())
            (root / 'Cargo.lock').write_bytes(b'original lock fixture\n')
            for args in (['init', '-q'], ['-c', 'core.autocrlf=false', 'add', '.'],
                         ['-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'original']):
                subprocess.run(['git', '-C', str(root), *args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for n, t in module.expected_inputs().items():
                p = root / n
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(t.encode())
            actual = subprocess.check_output
            def output(args, **kwargs):
                if args[-2:] == ['rev-parse', 'HEAD']:
                    return module.PIN + '\n'
                return actual(args, **kwargs)
            with patch.object(module.subprocess, 'check_output', side_effect=output), patch.dict(os.environ, {
                'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'core.autocrlf', 'GIT_CONFIG_VALUE_0': 'false'}):
                out = Path(tmp) / 'preflight.patch'
                expected = module.prepare(root, out, True)
                for n, t in expected.items():
                    self.assertEqual((root / n).read_bytes(), t.encode())
                self.assertEqual((root / 'Cargo.lock').read_bytes(), b'original lock fixture\n')
                with self.assertRaises(ValueError):
                    module.prepare(root, Path(tmp) / 'repeat.patch', True)
                # Exclusive output must refuse without applying anything.
                (root / module.SOURCE).write_bytes(module.original().encode())
                with self.assertRaises(FileExistsError):
                    module.prepare(root, out, True)
