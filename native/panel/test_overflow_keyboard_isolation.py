import importlib.util,tempfile,subprocess,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('overflow_isolation',HERE/'prepare_overflow_keyboard_isolation.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class OverflowKeyboardIsolationTests(unittest.TestCase):
    def test_only_overflow_view_wrapper_and_new_module_change(self):
        before=module.expected_inputs();after=module.transform(before)
        for name,text in before.items():
            if name!=module.VIEW:self.assertEqual(after[name],text)
        restored=after[module.VIEW].removesuffix('\n#[path = "overflow_keyboard_isolation.rs"]\nmod keyboard_isolation;\n').replace('keyboard_isolation::isolate(Element::from(','Element::from(')
        restored=restored.removesuffix('        ))\n    }\n}\n')+'        )\n    }\n}\n'
        self.assertEqual(restored,before[module.VIEW])

    def test_keyboard_refused_before_sdk_without_synthetic_input(self):
        text=(HERE/'overflow_keyboard_isolation.rs').read_text(encoding='utf-8').split('#[cfg(test)]')[0]
        self.assertLess(text.index('if matches!(event, Event::Keyboard(_)) { return; }'),text.index('self.0.as_widget_mut().update('))
        for forbidden in ('publish(', 'capture_event(', 'last_pointer_press', 'CursorLeft', 'unsafe ', 'SERIAL_COUNTER', 'current_focus(', 'is_grabbed('):self.assertNotIn(forbidden,text)
        self.assertIn('shell, viewport);',text)

    def test_original_feature_widget_delegation_and_actual_view_tests(self):
        text=(HERE/'overflow_keyboard_isolation.rs').read_text(encoding='utf-8')
        for method in ('size','size_hint','tag','state','children','diff','layout','operate','draw','mouse_interaction','overlay','id','set_id','drag_destinations'):
            self.assertIn('fn '+method,text)
        self.assertIn('let mut element = self.program.view();',text)
        self.assertIn('self.tree.diff(element.as_widget_mut());',text)
        self.assertEqual(text.count('#[test]'),8)
        for sequence in ('pointer_down_enter_repeat_release','pointer_down_space_unfocus_release','real_cursor_leave','keyboard_then_unfocus'):
            self.assertIn(sequence,text)

    def test_prior_drift_and_repeat_refused(self):
        with self.assertRaises(ValueError):module.transform(module.prerequisite().expected_inputs())
        files=module.expected_inputs();files[module.VIEW]+='\n'
        with self.assertRaises(ValueError):module.transform(files)
        with self.assertRaises(ValueError):module.transform(module.transform(module.expected_inputs()))

    def test_real_git_apply_lock_and_repeat_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'source';root.mkdir();prior=module.prerequisite()
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
                changed=module.prepare(root,Path(tmp)/'isolation.patch',True)
                for n,t in changed.items():self.assertEqual((root/n).read_bytes(),t.encode())
                self.assertEqual((root/'Cargo.lock').read_bytes(),b'original lock fixture\n')
                with self.assertRaises(ValueError):module.prepare(root,Path(tmp)/'repeat.patch',True)
