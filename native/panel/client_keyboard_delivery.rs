// SPDX-License-Identifier: GPL-3.0-only
// Original callback/press pairing only. NOT routing, activation or popup authority.
use super::{client_iced_event::{Context, Frame},
    keyboard_event_context::Kind, keyboard_input_state::{ClientPress, InputLedger}};
use sctk::seat::keyboard::KeyEvent;
use std::fmt;

#[derive(Clone)]
pub(crate) struct Delivery<O> {
    frame: Frame<O>,
    press: Option<ClientPress<O>>,
}
impl<O> Delivery<O> {
    pub(crate) fn frame(&self) -> &Frame<O> { &self.frame }
    // For release, this is a RETIRED witness, never a held grant. For repeat it
    // is the original press, not the repeat callback's serial/time/text.
    pub(crate) fn press(&self) -> Option<&ClientPress<O>> { self.press.as_ref() }
}
impl<O> fmt::Debug for Delivery<O> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("Delivery").finish_non_exhaustive()
    }
}
impl<O: Clone + PartialEq> Delivery<O> {
    // Necessary freshness only; even true does not validate a keyboard, target,
    // admission, queue order or popup grant. Call outside Smithay callbacks.
    pub(crate) fn current_fresh_press(&self, input: &InputLedger<O>, context: &Context<O>) -> bool {
        self.frame.kind() == Kind::Press && context.is_current(&self.frame)
            && self.press.as_ref().is_some_and(|press| input.is_current(press))
    }
}

// Invoked by the original client callback BEFORE ordinary server forwarding.
// Capture release witness before retiring; preserve the original release frame.
// Duplicate down/entry-held/unknown events have no fresh press witness.
pub(crate) fn capture<O: Clone + PartialEq>(
    input: &mut InputLedger<O>, context: &mut Context<O>,
    kind: Kind, serial: u32, event: KeyEvent,
) -> Option<Delivery<O>> {
    let press = match kind {
        Kind::Press => input.press(event.raw_code, serial, event.time),
        Kind::Repeat => input.held_press(event.raw_code).cloned(),
        Kind::Release => {
            let press = input.held_press(event.raw_code).cloned();
            let _ = input.release(event.raw_code);
            press
        },
    };
    // Refuse mismatched independently-created ledger/context origins. Do not
    // relabel a press witness with the latest event's seat.
    let frame = context.capture(kind, serial, event)?;
    let press = press.filter(|press| &press.origin == frame.origin());
    Some(Delivery { frame, press })
}

#[cfg(test)]
mod tests {
    use super::*;
    use sctk::seat::keyboard::{Modifiers, RawModifiers};
    use smithay::input::keyboard::xkb;
    fn setup(origin: &'static str) -> (InputLedger<&'static str>, Context<&'static str>) {
        let mut input = InputLedger::new(origin); input.enter(&[]);
        let mut context = Context::new(origin); context.enter();
        context.set_modifiers(0, Modifiers::default(), RawModifiers::default(), 0);
        (input, context)
    }
    fn event(raw: u32, time: u32, text: Option<&str>) -> KeyEvent {
        KeyEvent { raw_code: raw, time, keysym: xkb::Keysym::new(0xff0d), utf8: text.map(Into::into) }
    }
    #[test]
    fn fresh_press_pairs_original_frame_and_private_lifetime() {
        let (mut i, mut c) = setup("Seat0");
        let d = capture(&mut i, &mut c, Kind::Press, 0, event(28, u32::MAX, Some("é🦀"))).unwrap();
        assert!(d.current_fresh_press(&i, &c));
        let p = d.press().unwrap(); assert_eq!((p.origin,p.raw_code,p.serial,p.time),("Seat0",28,0,u32::MAX));
        assert_eq!(d.frame().event().utf8.as_deref(),Some("é🦀"));
        assert_eq!(d.frame().modifiers().unwrap().serial(),0);
    }
    #[test]
    fn repeat_retains_original_press_but_never_fresh_activation() {
        let (mut i, mut c) = setup("seat");
        let first = capture(&mut i,&mut c,Kind::Press,7,event(28,8,None)).unwrap();
        let repeat = capture(&mut i,&mut c,Kind::Repeat,9,event(28,10,Some(""))).unwrap();
        assert_eq!((repeat.press().unwrap().serial, repeat.press().unwrap().time),(7,8));
        assert_eq!((repeat.frame().serial(), repeat.frame().event().time),(9,10));
        assert_eq!(repeat.frame().event().utf8.as_deref(),Some(""));
        assert!(i.is_current(repeat.press().unwrap()));
        assert!(!repeat.current_fresh_press(&i,&c)); assert!(!first.current_fresh_press(&i,&c));
    }
    #[test]
    fn release_captures_retired_press_before_clear_and_preserves_release() {
        let (mut i, mut c) = setup("seat");
        let down = capture(&mut i,&mut c,Kind::Press,7,event(28,8,None)).unwrap();
        let up = capture(&mut i,&mut c,Kind::Release,11,event(28,12,Some("opaque-release"))).unwrap();
        assert_eq!((up.press().unwrap().serial,up.press().unwrap().time),(7,8));
        assert_eq!((up.frame().serial(),up.frame().event().time),(11,12));
        assert_eq!(up.frame().event().utf8.as_deref(),Some("opaque-release"));
        assert!(c.is_current(up.frame())); assert!(!i.is_current(up.press().unwrap()));
        assert!(!up.current_fresh_press(&i,&c)); assert!(!down.current_fresh_press(&i,&c));
    }
    #[test]
    fn duplicate_down_does_not_relabel_original_press() {
        let (mut i,mut c) = setup("seat");
        let old = capture(&mut i,&mut c,Kind::Press,7,event(28,8,None)).unwrap();
        let duplicate = capture(&mut i,&mut c,Kind::Press,99,event(28,100,None)).unwrap();
        assert!(duplicate.press().is_none()); assert!(!duplicate.current_fresh_press(&i,&c));
        assert!(!old.current_fresh_press(&i,&c)); assert!(i.is_current(old.press().unwrap()));
    }
    #[test]
    fn entry_held_unknown_release_and_repeat_never_mint_press() {
        let (mut i,mut c) = setup("seat"); i.enter(&[28]);
        for (kind,raw) in [(Kind::Press,28),(Kind::Repeat,28),(Kind::Release,28),(Kind::Release,57),(Kind::Repeat,57)] {
            let d = capture(&mut i,&mut c,kind,1,event(raw,2,None)).unwrap();
            assert!(d.press().is_none()); assert!(!d.current_fresh_press(&i,&c));
        }
        assert!(capture(&mut i,&mut c,Kind::Press,3,event(28,4,None)).unwrap().current_fresh_press(&i,&c));
    }
    #[test]
    fn reused_values_recreated_seat_focus_and_modifiers_cannot_revive_delivery() {
        let (mut i,mut c) = setup("seat");
        let old = capture(&mut i,&mut c,Kind::Press,7,event(28,8,None)).unwrap();
        let _ = capture(&mut i,&mut c,Kind::Release,7,event(28,8,None));
        let fresh = capture(&mut i,&mut c,Kind::Press,7,event(28,8,None)).unwrap();
        assert!(!old.current_fresh_press(&i,&c)); assert!(fresh.current_fresh_press(&i,&c));
        c.set_modifiers(0,Modifiers::default(),RawModifiers::default(),0);
        assert!(!fresh.current_fresh_press(&i,&c));
        i.invalidate(); c.invalidate(); i.enter(&[]); c.enter();
        assert!(!fresh.current_fresh_press(&i,&c));
        let (other_i,other_c) = setup("seat"); assert!(!fresh.current_fresh_press(&other_i,&other_c));
    }
    #[test]
    fn wrong_origin_and_raw_key_cannot_borrow_another_press() {
        let (mut i,mut c) = setup("seat");
        let first = capture(&mut i,&mut c,Kind::Press,7,event(28,8,None)).unwrap();
        let other_raw = capture(&mut i,&mut c,Kind::Repeat,7,event(57,8,None)).unwrap();
        assert!(other_raw.press().is_none()); assert!(i.is_current(first.press().unwrap()));
        let (_,mut wrong_context) = setup("Seat");
        let wrong = capture(&mut i,&mut wrong_context,Kind::Repeat,7,event(28,8,None)).unwrap();
        assert!(wrong.press().is_none()); assert!(!wrong.current_fresh_press(&i,&wrong_context));
    }
    #[test]
    fn invalid_context_refuses_delivery_and_debug_redacts_all_payloads() {
        let (mut i,mut c) = setup("private-seat");
        let d = capture(&mut i,&mut c,Kind::Press,789012,event(123456,345678,Some("private-text"))).unwrap();
        assert_eq!(format!("{d:?}"),"Delivery { .. }");
        c.invalidate(); assert!(!d.current_fresh_press(&i,&c));
        assert!(capture(&mut i,&mut c,Kind::Release,0,event(123456,0,None)).is_none());
        assert!(!i.is_current(d.press().unwrap()));
    }
}
