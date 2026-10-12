import importlib.util,tempfile,subprocess,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('client_delivery',HERE/'prepare_client_keyboard_delivery.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class ClientKeyboardDeliveryTests(unittest.TestCase):
    def test_only_actual_callback_state_and_new_module_change(self):
        before=module.expected_inputs();after=module.transform(before)
        for name,text in before.items():
            if name not in (module.STATE,module.SEAT,module.KEYBOARD):self.assertEqual(after[name],text)
        self.assertEqual(after[module.KEYBOARD].count('client_keyboard_delivery::capture('),3)
        self.assertNotIn('let _ = seat.client.key_input.press(',after[module.KEYBOARD])
        self.assertNotIn('let _ = seat.client.key_input.release(',after[module.KEYBOARD])
        self.assertEqual(after[module.SEAT].count('key_delivery: None,'),2)
        self.assertEqual(after[module.KEYBOARD].count('key_delivery = None;'),4)
        for line in before[module.KEYBOARD].splitlines():
            if any(word in line for word in ('kbd.input','KeyCode::new','KeyState::','SERIAL_COUNTER.next_serial','FilterResult::Forward','last_key_pressed =')):self.assertIn(line,after[module.KEYBOARD])
        self.assertIn('// SPDX-License-Identifier: MPL-2.0',after[module.SEAT])

    def test_release_pairing_precedes_retirement_and_no_widget_grant(self):
        text=(HERE/'client_keyboard_delivery.rs').read_text(encoding='utf-8').split('#[cfg(test)]')[0]
        release=text.split('Kind::Release => {',1)[1].split('},',1)[0]
        self.assertLess(release.index('input.held_press('),release.index('input.release('))
        self.assertIn('self.frame.kind() == Kind::Press && context.is_current',text)
        for forbidden in ('last_pointer_press','toggle_overflow_popup','iced_key_event(', 'update_keyboard(', 'current_focus(', 'is_grabbed(', 'unsafe ', 'insert_idle(', 'SERIAL_COUNTER'):
            self.assertNotIn(forbidden,text)
        self.assertEqual((HERE/'client_keyboard_delivery.rs').read_text(encoding='utf-8').count('#[test]'),8)

    def test_prior_drift_and_repeat_refused(self):
        with self.assertRaises(ValueError):module.transform(module.prerequisite().expected_inputs())
        before=module.expected_inputs();before[module.KEYBOARD]+='\n'
        with self.assertRaises(ValueError):module.transform(before)
        with self.assertRaises(ValueError):module.transform(module.transform(module.expected_inputs()))

    def test_redacted_immutable_delivery_and_panel_only_fingerprints(self):
        text=(HERE/'client_keyboard_delivery.rs').read_text(encoding='utf-8')
        self.assertIn('    frame: Frame<O>,',text);self.assertIn('    press: Option<ClientPress<O>>,',text)
        self.assertIn('fn press(&self) -> Option<&ClientPress<O>>',text)
        self.assertIn('f.debug_struct("Delivery").finish_non_exhaustive()',text)
        builder=(HERE.parent/'build_shell.py').read_text(encoding='utf-8')
        for token in ('client_keyboard_delivery_generator_sha256','client_keyboard_delivery_module_sha256'):
            self.assertEqual(builder.count("'"+token+"'"),2)
        self.assertIn("work / 'client-keyboard-delivery.patch'",builder)

    def test_real_git_apply_preserves_lock_and_refuses_existing_module(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'source';root.mkdir();prior=module.prerequisite().prerequisite()
            original={**prior.load('prepare_keyboard_focus').originals(),**prior.load('prepare_keyboard_input').originals(),**prior.prerequisite().originals()}
            for n,t in original.items():p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.encode())
            (root/'Cargo.lock').write_bytes(b'original lock fixture\n')
            for args in (['init','-q'],['-c','core.autocrlf=false','add','.'],['-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','original']):subprocess.run(['git','-C',str(root),*args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            for n,t in module.expected_inputs().items():p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.encode())
            call=subprocess.check_output
            def output(args,**kwargs):
                if args[-2:]==['rev-parse','HEAD']:return module.PIN+'\n' if kwargs.get('text') else (module.PIN+'\n').encode()
                return call(args,**kwargs)
            with patch.object(module.subprocess,'check_output',side_effect=output),patch.dict('os.environ',{'GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'core.autocrlf','GIT_CONFIG_VALUE_0':'false'}):
                changed=module.prepare(root,Path(tmp)/'delivery.patch',True)
                for n,t in changed.items():self.assertEqual((root/n).read_bytes(),t.encode())
                self.assertEqual((root/'Cargo.lock').read_bytes(),b'original lock fixture\n')
                with self.assertRaises(ValueError):module.prepare(root,Path(tmp)/'repeat.patch',True)
