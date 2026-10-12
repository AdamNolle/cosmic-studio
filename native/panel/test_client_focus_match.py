import importlib.util,tempfile,subprocess,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('clientfocusmatch',HERE/'prepare_client_focus_match.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class ClientFocusMatchTests(unittest.TestCase):
    def test_leave_matches_before_retiring_ledgers_or_server_focus(self):
        changed=module.transform(module.expected_inputs());text=changed[module.KEYBOARD]
        block=text[text.index('    fn leave('):text.index('    fn press_key(')]
        self.assertIn('&c_focused_surface, &name, surface,',block)
        self.assertIn('|status| matches!(status, FocusStatus::Focused)',block)
        self.assertLess(block.index('client_focus_match::leave_index('),block.index('seat.client.key_input.invalidate();'))
        self.assertLess(block.index('return;\n            };'),block.index('kbd.set_focus(self, None'))
        self.assertIn('self.space.keyboard_leave(&name, Some(surface.clone()));',block)

    def test_press_history_uses_unique_active_same_seat(self):
        changed=module.transform(module.expected_inputs());text=changed[module.KEYBOARD]
        block=text[text.index('    fn press_key('):text.index('    fn repeat_key(')]
        self.assertIn('client_focus_match::active_index(',block)
        self.assertIn('&c_focused_surface, &seat_name,',block)
        self.assertIn('|status| matches!(status, FocusStatus::Focused)',block)

    def test_ordinary_forwarding_and_other_callbacks_remain_exact(self):
        before=module.expected_inputs();changed=module.transform(before)
        for name,text in before.items():
            if name not in (module.KEYBOARD,module.PREFIX+'client/state.rs'):self.assertEqual(changed[name],text)
        a=before[module.KEYBOARD];b=changed[module.KEYBOARD]
        self.assertEqual(a[a.index('    fn repeat_key('):],b[b.index('    fn repeat_key('):])
        self.assertEqual(a[a.index('        let _ = kbd.input'):a.index('    fn repeat_key(')],b[b.index('        let _ = kbd.input'):b.index('    fn repeat_key(')])
        self.assertNotIn('iced_key_event(',b)
        self.assertNotIn('last_pointer_press',b)

    def test_changed_or_previous_postimages_refused(self):
        with self.assertRaises(ValueError):module.transform(module.prerequisite().expected_inputs())
        files=module.expected_inputs();files[module.KEYBOARD]+='\n'
        with self.assertRaises(ValueError):module.transform(files)
        with self.assertRaises(ValueError):module.transform(module.transform(module.expected_inputs()))

    def test_real_git_apply_lock_and_repeat_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'source';root.mkdir();prior=module.prerequisite();original=prior.prerequisite().prerequisite().prerequisite().originals()
            for n,t in original.items():p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.encode())
            (root/'Cargo.lock').write_bytes(b'original lock fixture\n')
            for args in (['init','-q'],['-c','core.autocrlf=false','add','.'],['-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','original']):subprocess.run(['git','-C',str(root),*args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            for n,t in module.expected_inputs().items():(root/n).write_bytes(t.encode())
            call=subprocess.check_output
            def output(args,**kwargs):
                if args[-2:]==['rev-parse','HEAD']:return module.PIN+'\n' if kwargs.get('text') else (module.PIN+'\n').encode()
                return call(args,**kwargs)
            with patch.object(module.subprocess,'check_output',side_effect=output),patch.dict('os.environ',{'GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'core.autocrlf','GIT_CONFIG_VALUE_0':'false'}):
                changed=module.prepare(root,Path(tmp)/'focus-match.patch',True)
                for n,t in changed.items():self.assertEqual((root/n).read_bytes(),t.encode())
                self.assertEqual((root/'Cargo.lock').read_bytes(),b'original lock fixture\n')
                with self.assertRaises(ValueError):module.prepare(root,Path(tmp)/'repeat.patch',True)
