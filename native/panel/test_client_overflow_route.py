# SPDX-License-Identifier: GPL-3.0-only
import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('client_overflow', HERE / 'prepare_client_overflow_route.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ClientOverflowRouteTests(unittest.TestCase):
    def test_actual_callbacks_route_only_after_original_server_input(self):
        before = module.expected_inputs(); after = module.transform(before)
        callbacks = after[module.KEYBOARD]
        self.assertEqual(callbacks.count('self.route_overflow_keyboard('), 3)
        self.assertEqual(callbacks.replace('        self.route_overflow_keyboard(keyboard);\n', '')
                         .replace('        self.route_overflow_keyboard(_keyboard);\n', ''), before[module.KEYBOARD])
        for start, end in [('fn press_key(', 'fn repeat_key('), ('fn release_key(', 'fn update_repeat_info(')]:
            text = callbacks.split(start)[1].split(end)[0]
            self.assertGreater(text.index('self.route_overflow_keyboard('), text.index('FilterResult::Forward'))
        self.assertIn('self.route_overflow_keyboard(_keyboard);', callbacks.split('fn repeat_key(')[1].split('fn release_key(')[0])

    def test_live_snapshot_before_mutex_and_no_keyboard_authority(self):
        text = module.transform(module.expected_inputs())[module.MODULE]
        caller = text.split('impl GlobalState {')[1].split('#[cfg(test)]')[0]
        for guard in ('keyboard.is_alive()', 'seats.next().is_some()', 'key_events.is_current(',
                      'kbd.is_grabbed()', 'kbd.current_focus()', 'client_focus_match::active_index(',
                      'panel.popups.is_empty()', 'panel.overflow_popup.is_none()',
                      'element_location(element).is_none()', 'element.geometry()', 'iced_key_event(delivery.frame())'):
            self.assertLess(caller.index(guard), caller.index('deliver_inert(button,'))
        validator = caller.split('deliver_inert(button,')[1]
        for forbidden in ('current_focus()', 'is_grabbed()', 'geometry()', 'with_program(', 'keyboard_enter('):
            self.assertNotIn(forbidden, validator)
        production = text.split('#[cfg(test)]')[0]
        for forbidden in ('last_pointer_press', 'toggle_overflow_popup', 'insert_idle', 'SERIAL_COUNTER', '.press()', 'unsafe'):
            self.assertNotIn(forbidden, production)
        self.assertIn('Task::none()).is_ok()', production)

    def test_exact_prior_postimages_isolation_and_drift_refusal(self):
        before = module.expected_inputs(); after = module.transform(before)
        for name in before:
            if name not in (module.KEYBOARD, module.WRAPPER):
                self.assertEqual(before[name], after[name])
        self.assertIn('if matches!(event, Event::Keyboard(_)) { return; }',
                      after['cosmic-panel-bin/src/iced/elements/overflow_keyboard_isolation.rs'])
        for name in (module.KEYBOARD, module.WRAPPER):
            wrong = module.expected_inputs(); wrong[name] += '\n'
            with self.assertRaises(ValueError): module.transform(wrong)
        with self.assertRaises(ValueError): module.transform(after)

    def test_panel_only_fingerprints_and_build_order(self):
        builder = (HERE.parent / 'build_shell.py').read_text(encoding='utf-8')
        for token in ('client_overflow_route_generator_sha256', 'client_overflow_route_module_sha256'):
            self.assertEqual(builder.count("'" + token + "'"), 2)
        self.assertLess(builder.index("work / 'overflow-preflight.patch'"), builder.index("work / 'client-overflow-route.patch'"))
        self.assertEqual((HERE / 'client_overflow_route.rs').read_text().count('#[test]'), 5)

    def test_real_git_apply_original_blobs_lock_and_exclusive_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'source'; root.mkdir()
            originals = {**module.load('prepare_keyboard_focus').originals(), **module.load('prepare_keyboard_input').originals()}
            prior = module.prerequisite(); originals[prior.SOURCE] = prior.original()
            for name, text in originals.items():
                p = root / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(text.encode())
            (root / 'Cargo.lock').write_bytes(b'original fixture lock\n')
            for args in (['init', '-q'], ['-c', 'core.autocrlf=false', 'add', '.'],
                         ['-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'original']):
                subprocess.run(['git', '-C', str(root), *args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for name, text in module.expected_inputs().items():
                p=root/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(text.encode())
            actual = subprocess.check_output
            def output(args, **kwargs):
                if args[-2:] == ['rev-parse', 'HEAD']: return module.PIN + '\n'
                return actual(args, **kwargs)
            with patch.object(module.subprocess, 'check_output', side_effect=output), patch.dict(os.environ, {
                'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'core.autocrlf', 'GIT_CONFIG_VALUE_0': 'false'}):
                out=Path(tmp)/'route.patch'; expected=module.prepare(root,out,True)
                for name, text in expected.items(): self.assertEqual((root/name).read_bytes(),text.encode())
                self.assertEqual((root/'Cargo.lock').read_bytes(), b'original fixture lock\n')
                with self.assertRaises(ValueError): module.prepare(root,Path(tmp)/'repeat.patch',True)
                (root/module.MODULE).unlink()
                for name, text in module.expected_inputs().items(): (root/name).write_bytes(text.encode())
                with self.assertRaises(FileExistsError): module.prepare(root,out,True)
                (root/module.KEYBOARD).write_bytes(module.expected_inputs()[module.KEYBOARD].replace('\n','\r\n').encode())
                with self.assertRaises(ValueError): module.prepare(root,Path(tmp)/'crlf.patch',True)
