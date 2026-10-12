import importlib.util,tempfile,subprocess,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('iced_dispatch',HERE/'prepare_iced_keyboard_dispatch.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class IcedKeyboardDispatchTests(unittest.TestCase):
    def test_ordinary_state_and_all_previous_callbacks_stay_exact(self):
        before=module.expected_inputs();after=module.transform(before)
        for n,t in before.items():
            if n!=module.STATE:self.assertEqual(after[n],t)
        self.assertTrue(after[module.STATE].startswith(before[module.STATE]))
        self.assertEqual(after[module.STATE][len(before[module.STATE]):], '\n#[path = "iced_keyboard_dispatch.rs"]\nmod keyboard_dispatch;\n')

    def test_busy_and_invalid_entry_refuse_before_cache_or_widgets(self):
        text=module.transform(module.expected_inputs())[module.MODULE]
        self.assertLess(text.index('if !self.is_queue_empty()'),text.index('if !validate(context)'))
        self.assertLess(text.index('if !validate(context)'),text.index('self.cache.take()'))
        self.assertIn('Event::Keyboard(context.iced().clone())',text)
        self.assertIn('std::slice::from_ref(&event)',text)
        self.assertNotIn('queued_events.clear',text);self.assertNotIn('messages.append',text)

    def test_message_validation_and_explicit_dispatch_never_use_plain_or_pointer_authority(self):
        text=module.transform(module.expected_inputs())[module.MODULE];production=text[:text.index('#[cfg(test)]')]
        self.assertIn('for message in messages',production)
        self.assertIn('if validate(context) { tasks.push(dispatch(&mut self.program, message, context)); }',production)
        for forbidden in ('self.program.update(', 'last_pointer_press', 'current_focus(', 'is_grabbed(', 'unsafe ', 'SERIAL_COUNTER'):
            self.assertNotIn(forbidden,production)

    def test_changed_previous_and_repeat_inputs_refused(self):
        with self.assertRaises(ValueError):module.transform(module.prerequisite().expected_inputs())
        files=module.expected_inputs();files[module.STATE]+='\n'
        with self.assertRaises(ValueError):module.transform(files)
        with self.assertRaises(ValueError):module.transform(module.transform(module.expected_inputs()))

    def test_real_git_apply_lock_and_repeat_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'source';root.mkdir();prior=module.prerequisite()
            original={**prior.prerequisite().prerequisite().prerequisite().prerequisite().originals(),**module.originals()}
            for n,t in original.items():p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.encode())
            (root/'Cargo.lock').write_bytes(b'original lock fixture\n')
            for args in (['init','-q'],['-c','core.autocrlf=false','add','.'],['-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','original']):subprocess.run(['git','-C',str(root),*args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            for n,t in module.expected_inputs().items():p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.encode())
            call=subprocess.check_output
            def output(args,**kwargs):
                if args[-2:]==['rev-parse','HEAD']:return module.PIN+'\n' if kwargs.get('text') else (module.PIN+'\n').encode()
                return call(args,**kwargs)
            with patch.object(module.subprocess,'check_output',side_effect=output),patch.dict('os.environ',{'GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'core.autocrlf','GIT_CONFIG_VALUE_0':'false'}):
                changed=module.prepare(root,Path(tmp)/'keyboard-dispatch.patch',True)
                for n,t in changed.items():self.assertEqual((root/n).read_bytes(),t.encode())
                self.assertEqual((root/'Cargo.lock').read_bytes(),b'original lock fixture\n')
                with self.assertRaises(ValueError):module.prepare(root,Path(tmp)/'repeat.patch',True)
