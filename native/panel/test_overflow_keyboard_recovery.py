# SPDX-License-Identifier: GPL-3.0-only
import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('overflow_recovery', HERE / 'prepare_overflow_keyboard_recovery.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class OverflowKeyboardRecoveryTests(unittest.TestCase):
    def test_actual_post_input_caller_recovers_without_internal_popup_target(self):
        before=module.expected_inputs(); after=module.transform(before)
        self.assertEqual(before[module.KEYBOARD],after[module.KEYBOARD])
        self.assertIn('if self.dismiss_overflow_keyboard(keyboard) { return; }',after[module.ROUTE])
        text=after[module.MODULE].split('#[cfg(test)]')[0]
        for guard in ('keyboard.is_alive()', 'seats.next().is_some()', 'kbd.is_grabbed()',
                      'kbd.current_focus().is_some()', 'client_focus_match::active_index(',
                      'panel.popups.is_empty()', 'overflow_keyboard_owner.as_ref()',
                      'owner == &seat.client._seat', 'panels.next().is_some()', 'eligible_escape('):
            self.assertLess(text.rindex(guard),text.index('.key_input.consume(&press)'))
        self.assertLess(text.index('.key_input.consume(&press)'),text.index('panel.toggle_overflow_popup('))
        for forbidden in ('insert_idle','last_pointer_press','SERIAL_COUNTER','update_keyboard(',
                          'with_program(', 'set_focus(', 'keyboard_enter(', 'element_location(', 'unsafe'):
            self.assertNotIn(forbidden,text)
        self.assertIn('(press.serial, original_seat), true)',text)
        self.assertIn('if modifiers.is_empty()',text)
        self.assertIn('raw.depressed != 0 || raw.latched != 0 || raw.locked != 0',text)

    def test_actual_creation_ownership_and_done_teardown(self):
        after=module.transform(module.expected_inputs())
        self.assertIn('Some((c_wl_surface, seat.1))',after[module.OVERFLOW])
        self.assertIn('overflow_keyboard_owner: None',after[module.PANEL])
        self.assertIn('self.overflow_keyboard_owner = None;',after[module.POPUP])
        close=after[module.CONTAINER].split('fn close_popup(')[1].split('fn configure_layer(')[0]
        self.assertIn('s.overflow_popup.as_ref().is_some_and(',close)
        close=after['cosmic-panel-bin/src/space/wrapper_space.rs'].split('fn close_popup(')[1].split('fn configure_layer(')[0]
        self.assertIn('overflow_keyboard_recovery::descendant_surfaces(',close)
        self.assertIn('(child.popup.parent.clone(), child.popup.c_popup.wl_surface().clone())',close)
        self.assertIn('self.close_popups(|p| !closing.contains(p.c_popup.wl_surface()))',close)
        # Actual generic Rust subtree helper is invoked here and has a native
        # reversed-order/duplicate/cycle/unrelated-root test, not a Done runtime test.
        self.assertIn('self.overflow_keyboard_owner = None;',after[module.PANEL])
        teardown=after[module.POPUP].split('pub(crate) fn close_popups(')[1].split('pub fn configure_panel_popup(')[0]
        self.assertIn('overflow_keyboard_recovery::ordered_teardown(batch, edges, |(popup, s_popup)|',teardown)
        self.assertIn('for p in self.popups.drain(..)',teardown)
        self.assertIn('to_destroy.push((p.popup, Some(p.s_surface)))',teardown)
        self.assertIn('to_destroy.push((popup, None))',teardown)
        self.assertLess(teardown.index('ordered_teardown(batch'),teardown.index('s_popup.send_popup_done()'))
        self.assertLess(teardown.index('s_popup.send_popup_done()'),teardown.index('drop(popup)'))
        for forbidden in ('retain_mut(','.xdg_popup().clone()', 'popup.destroy()', 'surface.destroy()',
                          'p.s_surface.send_popup_done();'):
            self.assertNotIn(forbidden,teardown)

    def test_exact_prior_isolation_forwarding_and_drift_refusal(self):
        before=module.expected_inputs(); after=module.transform(before)
        changed={module.ROUTE,module.WRAPPER,module.LEDGER,module.PANEL,module.POPUP,module.OVERFLOW,
                 module.CONTAINER,'cosmic-panel-bin/src/space/wrapper_space.rs'}
        for name in before:
            if name not in changed: self.assertEqual(before[name],after[name])
        self.assertIn('if matches!(event, Event::Keyboard(_)) { return; }',
                      after['cosmic-panel-bin/src/iced/elements/overflow_keyboard_isolation.rs'])
        for name in changed:
            wrong=dict(before); wrong[name]+='\n'
            with self.assertRaises(ValueError): module.transform(wrong)
        with self.assertRaises(ValueError): module.transform(after)
        ledger=after[module.LEDGER]
        self.assertIn('self.is_current(press) && self.consumed.insert(press.raw_code)',ledger)
        self.assertEqual(ledger.count('self.consumed.clear();'),2)
        self.assertIn('self.consumed.remove(&raw_code)',ledger)

    def test_panel_only_fingerprints_and_exact_build_order(self):
        builder=(HERE.parent/'build_shell.py').read_text(encoding='utf-8')
        for name in ('generator','module','fixture'):
            self.assertEqual(builder.count("'overflow_keyboard_recovery_"+name+"_sha256'"),2)
        self.assertLess(builder.index("work / 'client-overflow-route.patch'"),builder.index("work / 'overflow-keyboard-recovery.patch'"))
        self.assertEqual((HERE/'overflow_keyboard_recovery.rs').read_text().count('#[test]'),11)
        notice=(HERE/'pinned-overflow-recovery.NOTICE').read_text()
        self.assertIn(module.PIN,notice); self.assertIn('GPL-3.0-only',notice)
        self.assertEqual(len(module.fixture_originals()),2)

    def test_real_git_apply_original_blobs_lock_and_exclusive_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'source'; root.mkdir()
            originals={**module.load('prepare_keyboard_focus').originals(),
                       **module.load('prepare_keyboard_input').originals(),**module.fixture_originals()}
            overflow=module.load('prepare_overflow_preflight'); originals[overflow.SOURCE]=overflow.original()
            for name,text in originals.items():
                p=root/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(text.encode())
            (root/'Cargo.lock').write_bytes(b'original fixture lock\n')
            for args in (['init','-q'],['-c','core.autocrlf=false','add','.'],
                         ['-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','original']):
                subprocess.run(['git','-C',str(root),*args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            for name,text in module.expected_inputs().items():
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(text.encode())
            actual=subprocess.check_output
            def output(args,**kwargs):
                if args[-2:]==['rev-parse','HEAD']:return module.PIN+'\n'
                return actual(args,**kwargs)
            with patch.object(module.subprocess,'check_output',side_effect=output),patch.dict(os.environ,{
                'GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'core.autocrlf','GIT_CONFIG_VALUE_0':'false'}):
                out=Path(tmp)/'recovery.patch';expected=module.prepare(root,out,True)
                for name,text in expected.items():self.assertEqual((root/name).read_bytes(),text.encode())
                self.assertEqual((root/'Cargo.lock').read_bytes(),b'original fixture lock\n')
                with self.assertRaises(ValueError):module.prepare(root,Path(tmp)/'repeat.patch',True)
                (root/module.MODULE).unlink()
                for name,text in module.expected_inputs().items():(root/name).write_bytes(text.encode())
                with self.assertRaises(FileExistsError):module.prepare(root,out,True)
                (root/module.PANEL).write_bytes(module.expected_inputs()[module.PANEL].replace('\n','\r\n').encode())
                with self.assertRaises(ValueError):module.prepare(root,Path(tmp)/'crlf.patch',True)
