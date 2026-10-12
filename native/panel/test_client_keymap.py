import importlib.util,tempfile,subprocess,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('clientmap',HERE/'prepare_client_keymap.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class ClientKeymapTests(unittest.TestCase):
    def test_actual_owned_client_keymap_and_capability_seams(self):
        changed=module.transform(module.expected_inputs());p=module.PREFIX
        self.assertIn('pub(crate) keymap_source: client_keymap::ClientKeymap,',changed[p+'client/state.rs'])
        seat=changed[p+'client/handlers/seat.rs'];self.assertEqual(seat.count('keymap_source: Default::default()'),2)
        self.assertEqual(seat.count('sp.client.keymap_source.clear();'),2)
        keyboard=changed[p+'client/handlers/keyboard.rs'];self.assertEqual(keyboard.count('keymap_source.replace(keymap.as_string())'),1)
        block=keyboard[keyboard.index('    fn update_keymap('):keyboard.index('    fn update_modifiers(')]
        self.assertLess(block.index('key_events.invalidate()'),block.index('keymap_source.replace'))
        self.assertIn('kbd.set_keymap_from_string(self, keymap.as_string())',block)

    def test_original_key_repeat_modifiers_admission_and_text_unchanged(self):
        before=module.expected_inputs();changed=module.transform(before);p=module.PREFIX
        keyboard=changed[p+'client/handlers/keyboard.rs'];old=before[p+'client/handlers/keyboard.rs']
        self.assertEqual(keyboard[:keyboard.index('    fn update_keymap(')],old[:old.index('    fn update_keymap(')])
        self.assertEqual(keyboard[keyboard.index('    fn update_modifiers('):],old[old.index('    fn update_modifiers('):])
        self.assertNotIn('keymap_source.lookup',keyboard)
        self.assertEqual(changed[p+'client/keyboard_input_state.rs'],before[p+'client/keyboard_input_state.rs'])
        self.assertEqual(changed[p+'client/keyboard_event_context.rs'],before[p+'client/keyboard_event_context.rs'])

    def test_native_public_api_only_no_borrowed_ffi_or_default_keyboard(self):
        text=(HERE/'client_keymap.rs').read_text(encoding='utf-8')
        self.assertIn('smithay::input::keyboard::xkb',text);self.assertIn('Keymap::new_from_string',text)
        self.assertIn('checked_add(8)',text);self.assertIn('raw.latched & !bit',text);self.assertIn('raw.locked & !bit',text)
        for name in ('unsafe {','unsafe impl','from_raw_ptr','new_from_names','update_key(','key_get_utf8','winit::','xkbcommon_dl'):
            self.assertNotIn(name,text)
        self.assertIn('LookupError::ResidualControl',text);self.assertIn('LookupError::EventMismatch',text)

    def test_old_missing_or_changed_postimages_are_refused(self):
        with self.assertRaises(ValueError):module.transform(module.prerequisite().expected_inputs())
        files=module.expected_inputs();files[module.prerequisite().MODULE]+='\n'
        with self.assertRaises(ValueError):module.transform(files)
        with self.assertRaises(ValueError):module.transform(module.transform(module.expected_inputs()))

    def test_real_git_apply_unchanged_lock_and_repeat_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'source';root.mkdir();original=module.prerequisite().prerequisite().originals()
            for n,t in original.items():p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.encode())
            (root/'Cargo.lock').write_bytes(b'original lock fixture\n')
            for args in (['init','-q'],['-c','core.autocrlf=false','add','.'],['-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','original']):subprocess.run(['git','-C',str(root),*args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            for n,t in module.expected_inputs().items():(root/n).write_bytes(t.encode())
            call=subprocess.check_output
            def output(args,**kwargs):
                if args[-2:]==['rev-parse','HEAD']:return module.PIN+'\n' if kwargs.get('text') else (module.PIN+'\n').encode()
                return call(args,**kwargs)
            with patch.object(module.subprocess,'check_output',side_effect=output),patch.dict('os.environ',{'GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'core.autocrlf','GIT_CONFIG_VALUE_0':'false'}):
                changed=module.prepare(root,Path(tmp)/'keymap.patch',True)
                for n,t in changed.items():self.assertEqual((root/n).read_bytes(),t.encode())
                self.assertEqual((root/'Cargo.lock').read_bytes(),b'original lock fixture\n')
                with self.assertRaises(ValueError):module.prepare(root,Path(tmp)/'repeat.patch',True)
