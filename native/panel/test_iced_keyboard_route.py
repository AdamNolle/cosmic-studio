import importlib.util,tempfile,subprocess,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('iced_route',HERE/'prepare_iced_keyboard_route.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class IcedKeyboardRouteTests(unittest.TestCase):
    def test_only_receiver_constructors_child_visibility_and_new_module_change(self):
        before=module.expected_inputs();after=module.transform(before)
        for name,text in before.items():
            if name not in (module.WRAPPER,module.STATE):self.assertEqual(after[name],text)
        restored=after[module.WRAPPER].removesuffix('\nmod iced_keyboard_route;\n').replace('    rx: iced_keyboard_route::TaskInbox<<P as Program>::Message>,','    rx: Receiver<Option<<P as Program>::Message>>,').replace('            rx: rx.into(),','            rx,')
        self.assertEqual(restored,before[module.WRAPPER])
        self.assertEqual(after[module.STATE].replace('pub(super) mod keyboard_dispatch;','mod keyboard_dispatch;'),before[module.STATE])

    def test_actual_wrapper_refuses_state_and_receiver_before_validator_ui(self):
        text=module.transform(module.expected_inputs())[module.MODULE];production=text[:text.index('#[cfg(test)]')]
        self.assertLess(production.index('!internal.state.is_queue_empty() || internal.rx.has_pending()'),production.index('internal.state.update_keyboard('))
        self.assertIn('dispatch(&mut program.0, message, original)',production)
        for forbidden in ('internal.update(', 'queue_message(', 'queue_event(', 'last_pointer_press', 'current_focus(', 'is_grabbed(', 'unsafe ', 'SERIAL_COUNTER', 'program.update('):self.assertNotIn(forbidden,production)

    def test_probe_stages_none_and_does_not_drain_or_relabel_tasks(self):
        text=(HERE/'iced_keyboard_route.rs').read_text(encoding='utf-8')
        self.assertIn('staged: Option<Option<M>>',text)
        self.assertIn('self.staged = self.receiver.try_recv().ok()',text)
        self.assertIn('Some(output) => Ok(output)',text)
        self.assertIn('field("pending", &self.staged.is_some()).finish_non_exhaustive()',text)
        self.assertNotIn('#[derive(Debug)]\npub(super) struct TaskInbox',text)
        self.assertIn('Some(Action::Output(message)) => Some(message), _ => None',text)
        self.assertNotIn('while let',text[:text.index('#[cfg(test)]')])

    def test_prior_drift_and_repeat_refused(self):
        with self.assertRaises(ValueError):module.transform(module.prerequisite().expected_inputs())
        files=module.expected_inputs();files[module.WRAPPER]+='\n'
        with self.assertRaises(ValueError):module.transform(files)
        with self.assertRaises(ValueError):module.transform(module.transform(module.expected_inputs()))

    def test_real_git_apply_lock_and_repeat_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'source';root.mkdir()
            original={**module.load('prepare_keyboard_focus').originals(),**module.load('prepare_keyboard_input').originals(),**module.prerequisite().originals()}
            for n,t in original.items():p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.encode())
            (root/'Cargo.lock').write_bytes(b'original lock fixture\n')
            for args in (['init','-q'],['-c','core.autocrlf=false','add','.'],['-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','original']):subprocess.run(['git','-C',str(root),*args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            for n,t in module.expected_inputs().items():p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.encode())
            call=subprocess.check_output
            def output(args,**kwargs):
                if args[-2:]==['rev-parse','HEAD']:return module.PIN+'\n' if kwargs.get('text') else (module.PIN+'\n').encode()
                return call(args,**kwargs)
            with patch.object(module.subprocess,'check_output',side_effect=output),patch.dict('os.environ',{'GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'core.autocrlf','GIT_CONFIG_VALUE_0':'false'}):
                changed=module.prepare(root,Path(tmp)/'keyboard-route.patch',True)
                for n,t in changed.items():self.assertEqual((root/n).read_bytes(),t.encode())
                self.assertEqual((root/'Cargo.lock').read_bytes(),b'original lock fixture\n')
                with self.assertRaises(ValueError):module.prepare(root,Path(tmp)/'repeat.patch',True)
