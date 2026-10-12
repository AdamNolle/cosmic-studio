import importlib.util,hashlib,json,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('focus',HERE/'prepare_keyboard_focus.py');focus=importlib.util.module_from_spec(spec);spec.loader.exec_module(focus)

class FocusTests(unittest.TestCase):
    def test_original_and_license_retained(self):
        self.assertEqual(hashlib.sha256((HERE/'pinned-keyboard-focus-sources.json.gz').read_bytes()).hexdigest(),focus.FIXTURE_SHA)
        self.assertIn('GNU General Public License',(HERE/'pinned-keyboard-focus.LICENSE').read_text(encoding='utf-8'))
        self.assertEqual(len(focus.originals()),6)

    def test_typed_target_bridge_keeps_proxy_and_grab_rules(self):
        original=focus.originals();changed=focus.transform(original);p=focus.PREFIX
        self.assertIn(') -> Option<SpaceTarget>;',changed[p+'xdg_shell_wrapper/space/space.rs'])
        self.assertIn('kbd.set_focus(self, s, SERIAL_COUNTER.next_serial())',changed[p+'xdg_shell_wrapper/client/handlers/keyboard.rs'])
        self.assertIn('Some(s_surface.into())',changed[p+'xdg_shell_wrapper/client/handlers/keyboard.rs'])
        self.assertIn('drop(p_ret);',changed[p+'space_container/wrapper_space.rs'])
        for marker in ('fn keyboard_leave(', 'fn pointer_leave('):
            a=original[p+'space/wrapper_space.rs'];b=changed[p+'space/wrapper_space.rs'];start=a.index(marker);end=a.index('\n    fn ',start+8)
            self.assertIn(a[start:end],b)
        self.assertIn('|| !self.popups.is_empty()',changed[p+'space/wrapper_space.rs'])
        self.assertIn('geometry.size.w <= 0',changed[p+'space/wrapper_space.rs'])
        self.assertIn('candidate == target',changed[p+'space/wrapper_space.rs'])

    def test_cached_operation_and_explicit_widget_id_not_task(self):
        changed=focus.transform(focus.originals());p=focus.PREFIX
        self.assertIn('self.state.operate(',changed[p+'iced/mod.rs'])
        self.assertIn('fn keyboard_focus_id(&self) -> Option<Id>',changed[p+'iced/mod.rs'])
        self.assertIn('.id(self.id.clone())',changed[p+'iced/elements/overflow_button.rs'])
        self.assertIn('fn keyboard_focus_id(&self) -> Option<id::Id>',changed[p+'iced/elements/overflow_button.rs'])
        self.assertEqual(changed[p+'iced/mod.rs'].count('keyboard_focus_seats::FocusSeats::default()'),2)
        # Original key conversion, repeat behavior and popup serial have NOT been
        # rewritten/pretended safe in this prerequisite-only candidate.
        self.assertIn('_time: InputTime,\n    ) {\n        // TODO convert keys',changed[p+'iced/mod.rs'])
        self.assertIn('seat.client.last_pointer_press.0',changed[p+'iced/elements/overflow_button.rs'])

    def test_drift_or_repeat_refused(self):
        original=focus.originals();drift=dict(original);name=next(iter(drift));drift[name]+='\n'
        with self.assertRaises(ValueError):focus.transform(drift)
        with self.assertRaises(ValueError):focus.transform(focus.transform(original))

    def test_real_git_patch_and_lock_preservation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)/'source';root.mkdir()
            for name,text in focus.originals().items():
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(text.encode())
            (root/'Cargo.lock').write_bytes(b'unchanged fixture lock\n')
            for args in (['init','-q'],['-c','core.autocrlf=false','add','.'],['-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture']):subprocess.run(['git','-C',str(root),*args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            call=subprocess.check_output
            def output(args,**kwargs):
                if args[-2:]==['rev-parse','HEAD']:return focus.PIN+'\n' if kwargs.get('text') else (focus.PIN+'\n').encode()
                return call(args,**kwargs)
            # Fixture revision response alone is mocked, not real patch application.
            with patch.object(focus.subprocess,'check_output',side_effect=output):
                with patch.dict('os.environ',{'GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'core.autocrlf','GIT_CONFIG_VALUE_0':'false'}):
                    changed=focus.prepare(root,Path(temporary)/'focus.patch',True)
                self.assertEqual((root/'Cargo.lock').read_bytes(),b'unchanged fixture lock\n')
                for n,t in changed.items():self.assertEqual((root/n).read_bytes(),t.encode())
                with self.assertRaises(ValueError):focus.prepare(root,Path(temporary)/'again.patch',True)
