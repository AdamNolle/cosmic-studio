import importlib.util,tempfile,subprocess,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('clienticed',HERE/'prepare_client_iced.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class ClientIcedTests(unittest.TestCase):
    def test_tables_exact_original_adaptation_and_license(self):
        self.assertEqual(module.table_source(),(HERE/'client_key_tables.rs').read_text(encoding='utf-8'))
        self.assertIn('Code::SuperLeft',module.table_source())
        self.assertNotIn('use winit::',module.table_source())
        with patch.object(module,'FIXTURE_SHA','0'*64):
            with self.assertRaisesRegex(ValueError,'checksum'):module.table_source()

    def test_native_explicit_client_callable_and_unchanged_callbacks(self):
        before=module.expected_inputs();changed=module.transform(before)
        self.assertIn('pub(crate) fn iced_key_event(&self',changed[module.PREFIX+'client/state.rs'])
        self.assertIn('client_iced_event::convert(&self.keymap_source, &self.key_events, frame)',changed[module.PREFIX+'client/state.rs'])
        for name,text in before.items():
            if name!=module.PREFIX+'client/state.rs':self.assertEqual(changed[name],text)
        self.assertNotIn('iced_key_event(',changed[module.PREFIX+'client/handlers/keyboard.rs'])

    def test_complete_fields_original_text_repeat_and_private_envelope(self):
        text=(HERE/'client_iced_event.rs').read_text(encoding='utf-8')
        for seam in ('map.lookup(context, frame)?','logical(symbols.base())','logical(symbols.control_cleared())',
            'frame.event().raw_code','keysym_location(symbols.all().raw())','frame.kind() == Kind::Repeat',
            'frame.event().utf8.as_deref().map(Into::into)','original: frame.clone()','Kind::Release => keyboard::Event::KeyReleased'):
            self.assertIn(seam,text)
        for forbidden in ('unsafe {','unsafe impl','new_from_names','update_key(','key_get_utf8','SERIAL_COUNTER','last_pointer_press','key_input.press','utf8.pop('):self.assertNotIn(forbidden,text)

    def test_previous_or_changed_postimage_and_repeat_transform_refused(self):
        with self.assertRaises(ValueError):module.transform(module.prerequisite().expected_inputs())
        files=module.expected_inputs();files[module.prerequisite().MODULE]+='\n'
        with self.assertRaises(ValueError):module.transform(files)
        with self.assertRaises(ValueError):module.transform(module.transform(module.expected_inputs()))

    def test_real_git_apply_unchanged_lock_and_repeat_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'source';root.mkdir();prior=module.prerequisite();original=prior.prerequisite().prerequisite().originals()
            for n,t in original.items():p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.encode())
            (root/'Cargo.lock').write_bytes(b'original lock fixture\n')
            for args in (['init','-q'],['-c','core.autocrlf=false','add','.'],['-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','original']):subprocess.run(['git','-C',str(root),*args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            for n,t in module.expected_inputs().items():(root/n).write_bytes(t.encode())
            call=subprocess.check_output
            def output(args,**kwargs):
                if args[-2:]==['rev-parse','HEAD']:return module.PIN+'\n' if kwargs.get('text') else (module.PIN+'\n').encode()
                return call(args,**kwargs)
            with patch.object(module.subprocess,'check_output',side_effect=output),patch.dict('os.environ',{'GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'core.autocrlf','GIT_CONFIG_VALUE_0':'false'}):
                changed=module.prepare(root,Path(tmp)/'iced.patch',True)
                for n,t in changed.items():self.assertEqual((root/n).read_bytes(),t.encode())
                self.assertEqual((root/'Cargo.lock').read_bytes(),b'original lock fixture\n')
                with self.assertRaises(ValueError):module.prepare(root,Path(tmp)/'repeat.patch',True)
