import importlib.util,tempfile,subprocess,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('context',HERE/'prepare_keyboard_context.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class ContextTests(unittest.TestCase):
    def test_actual_client_payload_types_and_seat_lifecycle_seams(self):
        changed=module.transform(module.expected_inputs());p=module.PREFIX
        state=changed[p+'client/state.rs']
        for name in ('KeyEvent','Modifiers','RawModifiers'):self.assertIn('sctk::seat::keyboard::'+name,state)
        seat=changed[p+'client/handlers/seat.rs'];self.assertEqual(seat.count('EventContext::new(seat.clone())'),2)
        self.assertEqual(seat.count('sp.client.key_events.invalidate();'),2)
        keyboard=changed[module.KEYBOARD]
        self.assertEqual(keyboard.count('seat.client.key_events.invalidate();'),2)
        self.assertIn('seat.client.key_events.enter();',keyboard)
        self.assertIn('key_events.set_modifiers(serial, modifiers, raw_modifiers, group)',keyboard)
        self.assertEqual(keyboard.count('key_events.capture('),3)

    def test_original_forwarding_and_modifier_operations_stay_exact(self):
        before=module.expected_inputs()[module.KEYBOARD];after=module.transform(module.expected_inputs())[module.KEYBOARD]
        for name,next_name in [('press_key','repeat_key'),('release_key','update_repeat_info')]:
            start=before.index('    fn '+name+'(');end=before.index('    fn '+next_name+'(',start)
            original=before[start:end];self.assertIn(original[original.index('kbd.input'):],after)
        start=before.index('        let mut state = ModifiersState::default();')
        self.assertTrue(after.endswith(before[start:]))
        self.assertEqual(after.count('SERIAL_COUNTER.next_serial()'),before.count('SERIAL_COUNTER.next_serial()'))
        for name in ('get_keyboard_with_repeat','KeyboardEvent::KeyPressed','TogglePopup','utf8 =','unsafe {'):
            self.assertEqual(after.count(name),before.count(name))

    def test_repeat_observation_does_not_arm_forward_or_reconstruct(self):
        after=module.transform(module.expected_inputs())[module.KEYBOARD]
        block=after[after.index('    fn repeat_key('):after.index('    fn release_key(')]
        self.assertIn('kbd == _keyboard',block);self.assertIn('Kind::Repeat',block);self.assertIn('_serial, _event,',block)
        for name in ('key_input.press','kbd.input','KeyState::Pressed','next_serial','set_modifiers','utf8'):
            self.assertNotIn(name,block)

    def test_missing_previous_postimage_or_module_drift_is_refused(self):
        with self.assertRaises(ValueError):module.transform(module.prerequisite().expected_inputs())
        files=module.expected_inputs();files[module.prerequisite().MODULE]+='\n'
        with self.assertRaises(ValueError):module.transform(files)
        with self.assertRaises(ValueError):module.transform(module.transform(module.expected_inputs()))

    def test_real_git_application_and_lock_bytes_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'source';root.mkdir()
            for n,t in module.prerequisite().originals().items():p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.encode())
            (root/'Cargo.lock').write_bytes(b'original lock fixture\n')
            for args in (['init','-q'],['-c','core.autocrlf=false','add','.'],['-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','original']):subprocess.run(['git','-C',str(root),*args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            for n,t in module.expected_inputs().items():(root/n).write_bytes(t.encode())
            call=subprocess.check_output
            def output(args,**kwargs):
                if args[-2:]==['rev-parse','HEAD']:return module.PIN+'\n' if kwargs.get('text') else (module.PIN+'\n').encode()
                return call(args,**kwargs)
            with patch.object(module.subprocess,'check_output',side_effect=output),patch.dict('os.environ',{'GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'core.autocrlf','GIT_CONFIG_VALUE_0':'false'}):
                changed=module.prepare(root,Path(tmp)/'context.patch',True)
                for n,t in changed.items():self.assertEqual((root/n).read_bytes(),t.encode())
                self.assertEqual((root/'Cargo.lock').read_bytes(),b'original lock fixture\n')
                with self.assertRaises(ValueError):module.prepare(root,Path(tmp)/'repeat.patch',True)
