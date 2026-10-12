import importlib.util,hashlib,tempfile,subprocess,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('input_ledger',HERE/'prepare_keyboard_input.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class InputTests(unittest.TestCase):
    def test_fixture_checksum_and_mpl_headers_retained(self):
        self.assertEqual(hashlib.sha256((HERE/'pinned-keyboard-input-sources.json.gz').read_bytes()).hexdigest(),module.FIXTURE_SHA)
        original=module.originals();changed=module.transform(module.expected_inputs())
        name=module.PREFIX+'client/handlers/seat.rs'
        self.assertTrue(original[name].startswith('// SPDX-License-Identifier: MPL-2.0'))
        self.assertTrue(changed[name].startswith('// SPDX-License-Identifier: MPL-2.0'))
        self.assertEqual(len(module.originals()),3)

    def test_actual_client_seat_initialization_and_lifecycle_seams(self):
        changed=module.transform(module.expected_inputs());p=module.PREFIX
        self.assertIn('InputLedger<WlSeat>',changed[p+'client/state.rs'])
        seat=changed[p+'client/handlers/seat.rs'];self.assertEqual(seat.count('InputLedger::new(seat.clone())'),2)
        self.assertEqual(seat.count('sp.client.key_input.invalidate();'),2)
        keyboard=changed[module.KEYBOARD]
        self.assertIn('seat.client.key_input.enter(_raw);',keyboard)
        self.assertIn('seat.client.key_input.press(event.raw_code, serial, event.time)',keyboard)
        self.assertIn('seat.client.key_input.release(event.raw_code)',keyboard)
        self.assertEqual(keyboard.count('seat.client.key_input.invalidate();'),2)

    def test_forwarding_serial_and_repeat_contracts_byte_unchanged(self):
        before=module.expected_inputs()[module.KEYBOARD];after=module.transform(module.expected_inputs())[module.KEYBOARD]
        for name,next_name in [('repeat_key','release_key'),('update_repeat_info','update_keymap'),('update_modifiers',None)]:
            start=before.index('    fn '+name+'(');end=before.index('    fn '+next_name+'(',start) if next_name else len(before)
            self.assertIn(before[start:end],after)
        self.assertEqual(after.count('SERIAL_COUNTER.next_serial()'),before.count('SERIAL_COUNTER.next_serial()'))
        self.assertEqual(after.count('event.raw_code.saturating_add(8)'),2)
        self.assertIn('*last_key_pressed = (serial, event.time);',after)
        # No new Iced key event, popup message, server serial or invented shortcut.
        for forbidden in ('KeyboardEvent::KeyPressed','TogglePopup','get_serial_of_last_seat_event','ctrl ='):
            self.assertEqual(after.count(forbidden),before.count(forbidden))

    def test_missing_focus_prerequisite_drift_and_repeat_refused(self):
        with self.assertRaises(ValueError):module.transform(module.originals())
        changed=module.expected_inputs();changed[module.KEYBOARD]+='\n'
        with self.assertRaises(ValueError):module.transform(changed)
        with self.assertRaises(ValueError):module.transform(module.transform(module.expected_inputs()))

    def test_real_git_patch_application_and_lock_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'source';root.mkdir()
            for n,t in module.originals().items():p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.encode())
            (root/'Cargo.lock').write_bytes(b'original fixture lock\n')
            for args in (['init','-q'],['-c','core.autocrlf=false','add','.'],['-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','original']):subprocess.run(['git','-C',str(root),*args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            (root/module.KEYBOARD).write_bytes(module.expected_inputs()[module.KEYBOARD].encode())
            call=subprocess.check_output
            def output(args,**kwargs):
                if args[-2:]==['rev-parse','HEAD']:return module.PIN+'\n' if kwargs.get('text') else (module.PIN+'\n').encode()
                return call(args,**kwargs)
            # Only the tiny fixture HEAD identity is mocked; patch application is real.
            with patch.object(module.subprocess,'check_output',side_effect=output),patch.dict('os.environ',{'GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'core.autocrlf','GIT_CONFIG_VALUE_0':'false'}):
                changed=module.prepare(root,Path(tmp)/'input.patch',True)
                for n,t in changed.items():self.assertEqual((root/n).read_bytes(),t.encode())
                self.assertEqual((root/'Cargo.lock').read_bytes(),b'original fixture lock\n')
                with self.assertRaises(ValueError):module.prepare(root,Path(tmp)/'again.patch',True)
