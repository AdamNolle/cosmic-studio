// SPDX-License-Identifier: GPL-3.0-only
// Recovery-only candidate: dismiss the originating seat's existing native leaf
// overflow on a fresh Escape press. NOT opening, popup-grab or focus authority.
use crate::xdg_shell_wrapper::{shared_state::GlobalState,
    client_state::{FocusStatus, client_focus_match, client_keyboard_delivery::Delivery,
        client_iced_event::{Context, convert}, client_keymap::ClientKeymap,
        keyboard_event_context::Kind, keyboard_input_state::InputLedger}};
use cosmic::iced::keyboard::{Event, Key, key::Named};
use sctk::reexports::client::{Proxy, protocol::wl_keyboard::WlKeyboard};
use sctk::shell::WaylandSurface;

fn eligible_escape<O: Clone + PartialEq>(
    delivery: &Delivery<O>, input: &InputLedger<O>, context: &Context<O>, map: &ClientKeymap,
) -> bool {
    if !delivery.current_fresh_press(input, context)
        || delivery.frame().event().keysym.raw() != 0xff1b { return false; }
    let Some(modifiers) = delivery.frame().modifiers() else { return false; };
    let raw = modifiers.raw();
    // Conservative known-zero policy, not a guessed raw server-mask setter.
    // Nonzero/unknown modifiers (including lock masks) remain refused here.
    if raw.depressed != 0 || raw.latched != 0 || raw.locked != 0
        || modifiers.named().num_lock { return false; }
    let Ok(event) = convert(map, context, delivery.frame()) else { return false; };
    matches!(event.iced(), Event::KeyPressed { key: Key::Named(Named::Escape),
        modified_key: Key::Named(Named::Escape), modifiers, repeat: false, .. }
        if modifiers.is_empty())
}

// Exact recorded client-surface subtree, not a PID/name/persistent identity.
// Used by the actual PanelSpace::close_popup before existing destruction.
pub(crate) fn descendant_surfaces<S: Clone + PartialEq>(root: S,
    edges: impl IntoIterator<Item = (S, S)>) -> Vec<S> {
    let edges = edges.into_iter().collect::<Vec<_>>();
    let mut closing = vec![root];
    loop {
        let previous_len = closing.len();
        for (parent, child) in &edges {
            if closing.contains(parent) && !closing.contains(child) { closing.push(child.clone()); }
        }
        if closing.len() == previous_len { return closing; }
    }
}

// Actual selected native teardown batch, children before parents. Equality is
// the original client proxy identity. Duplicate selection is idempotent; late
// Done finds no native object. Cycle fallback terminates, not protocol validity.
pub(crate) fn teardown_order<S: Clone + PartialEq>(selected: impl IntoIterator<Item = S>,
    edges: impl IntoIterator<Item = (S, S)>) -> Vec<S> {
    let edges = edges.into_iter().collect::<Vec<_>>();
    let mut pending = Vec::new();
    for surface in selected { if !pending.contains(&surface) { pending.push(surface); } }
    let mut ordered = Vec::new();
    while !pending.is_empty() {
        let index = pending.iter().position(|candidate|
            !edges.iter().any(|(parent, child)| parent == candidate && child != parent
                && pending.contains(child))).unwrap_or(pending.len() - 1);
        ordered.push(pending.remove(index));
    }
    ordered
}

// Keep the actual native owners, not merely raw protocol proxies, alive until
// their child-first step. The synchronous callback may release only that owner.
pub(crate) fn ordered_teardown<S: Clone + PartialEq, T>(mut batch: Vec<(S, T)>,
    edges: impl IntoIterator<Item = (S, S)>, mut destroy: impl FnMut(T)) {
    let ordered = teardown_order(batch.iter().map(|(surface, _)| surface.clone()), edges);
    for surface in ordered {
        // Even duplicate retained handles release at this step, never after
        // an ancestor. The actual native caller creates unique popup surfaces.
        while let Some(index) = batch.iter().position(|(candidate, _)| candidate == &surface) {
            let (_, owner) = batch.remove(index);
            destroy(owner);
        }
    }
}

impl GlobalState {
    pub(crate) fn dismiss_overflow_keyboard(&mut self, keyboard: &WlKeyboard) -> bool {
        // Only called by the existing route AFTER original Smithay input.
        // No element mutex, SDK event processing, Program update or idle task.
        if !keyboard.is_alive() { return false; }
        let mut seats = self.server_state.seats.iter().enumerate().filter(|(_, seat)|
            seat.client.kbd.as_ref() == Some(keyboard));
        let Some((seat_index, seat)) = seats.next() else { return false; };
        if seats.next().is_some() || !seat.client._seat.is_alive() { return false; }
        let Some(delivery) = seat.client.key_delivery.as_ref() else { return false; };
        if delivery.frame().origin() != &seat.client._seat { return false; }
        let Some(kbd) = seat.server.seat.get_keyboard() else { return false; };
        // A proxied client/leaf/grab keeps its own keyboard handling. These
        // queries are outside Smithay filter/target callbacks and all UI locks.
        if kbd.is_grabbed() || kbd.current_focus().is_some() { return false; }
        let focused = self.client_state.focused_surface.borrow();
        let Some(index) = client_focus_match::active_index(&focused, &seat.name,
            |status| matches!(status, FocusStatus::Focused)) else { return false; };
        let surface = &focused[index].0;
        if !surface.is_alive() { return false; }
        let mut panels = self.space.space_list.iter().enumerate().filter(|(_, panel)|
            panel.popups.is_empty()
            && panel.overflow_popup.as_ref().is_some_and(|(popup, _)|
                popup.grab && popup.c_popup.wl_surface() == surface)
            && panel.overflow_keyboard_owner.as_ref().is_some_and(|(owned_popup, owner)|
                owned_popup == surface && owner == &seat.client._seat && owner.is_alive()));
        let Some((panel_index, panel)) = panels.next() else { return false; };
        if panels.next().is_some() { return false; }
        if !eligible_escape(delivery, &seat.client.key_input,
            &seat.client.key_events, &seat.client.keymap_source) { return false; }
        let Some(press) = delivery.press().cloned() else { return false; };
        // Force-hide ignores its ID parameter; retain an existing native ID,
        // without requiring a surviving anchor/parent or inventing a grab.
        let id = panel.center_overflow_button_id.clone();
        let original_seat = seat.client._seat.clone();
        drop(focused);
        // No event-loop yield/callback/deferred envelope. All refusals precede
        // consume and effects; consume is lifetime bookkeeping, not admission.
        if !self.server_state.seats[seat_index].client.key_input.consume(&press) { return false; }
        let panel = &mut self.space.space_list[panel_index];
        let result = panel.toggle_overflow_popup(id, &self.client_state.compositor_state,
            self.client_state.fractional_scaling_manager.as_ref(),
            self.client_state.viewporter_state.as_ref(), &self.client_state.queue_handle,
            &mut self.client_state.xdg_shell_state, (press.serial, original_seat), true);
        // No synthesized server focus, enter, release or popup grab. Destruction
        // uses the existing protocol; real restoration is a separate runtime gate.
        panel.is_dirty = true;
        panel.needs_layout = true;
        if let Err(error) = result { tracing::warn!("Overflow keyboard dismissal refused: {error}"); }
        true
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::xdg_shell_wrapper::client_state::client_keyboard_delivery::capture;
    use sctk::seat::keyboard::{KeyEvent, Modifiers, RawModifiers};
    use smithay::input::keyboard::xkb;
    fn setup() -> (InputLedger<&'static str>, Context<&'static str>, ClientKeymap) {
        let mut input=InputLedger::new("seat"); input.enter(&[]);
        let mut context=Context::new("seat"); context.enter();
        context.set_modifiers(0, Modifiers::default(), RawModifiers::default(), 0);
        let mut map=ClientKeymap::default(); map.replace(r#"xkb_keymap {
            xkb_keycodes { minimum=8; maximum=255; <ESC>=9; <ENTER>=36; };
            xkb_types { type "ONE" { modifiers=none; map[None]=Level1; }; };
            xkb_compatibility { };
            xkb_symbols { key <ESC> { type="ONE", [ Escape ] }; key <ENTER> { type="ONE", [ Return ] }; };
        };"#.into()); (input, context, map)
    }
    fn key(raw: u32, symbol: u32) -> KeyEvent {
        KeyEvent { raw_code: raw, time: 0, keysym: xkb::Keysym::new(symbol), utf8: Some("é🦀".into()) }
    }
    #[test]
    fn current_original_escape_is_consume_once_not_a_grab() {
        let (mut i,mut c,m)=setup(); let d=capture(&mut i,&mut c,Kind::Press,0,key(1,0xff1b)).unwrap();
        assert!(eligible_escape(&d,&i,&c,&m)); let p=d.press().unwrap();
        assert_eq!((p.serial,p.time),(0,0)); assert!(i.consume(p)); assert!(!i.consume(p));
        assert!(i.is_current(p)); assert_eq!(d.frame().event().utf8.as_deref(),Some("é🦀"));
    }
    #[test]
    fn repeat_and_release_never_consume_a_fresh_action() {
        let (mut i,mut c,m)=setup(); let _=capture(&mut i,&mut c,Kind::Press,7,key(1,0xff1b));
        for kind in [Kind::Repeat,Kind::Release] {
            let d=capture(&mut i,&mut c,kind,9,key(1,0xff1b)).unwrap(); assert!(!eligible_escape(&d,&i,&c,&m));
        }
    }
    #[test]
    fn entry_held_and_duplicate_down_are_not_action_presses() {
        let (mut i,mut c,m)=setup(); i.enter(&[1]);
        let d=capture(&mut i,&mut c,Kind::Press,0,key(1,0xff1b)).unwrap(); assert!(!eligible_escape(&d,&i,&c,&m));
        let _=capture(&mut i,&mut c,Kind::Release,0,key(1,0xff1b));
        let _=capture(&mut i,&mut c,Kind::Press,0,key(1,0xff1b));
        let d=capture(&mut i,&mut c,Kind::Press,0,key(1,0xff1b)).unwrap(); assert!(!eligible_escape(&d,&i,&c,&m));
    }
    #[test]
    fn reused_client_values_do_not_revive_a_consumed_press() {
        let (mut i,mut c,m)=setup(); let old=capture(&mut i,&mut c,Kind::Press,0,key(1,0xff1b)).unwrap();
        assert!(i.consume(old.press().unwrap())); let _=capture(&mut i,&mut c,Kind::Release,0,key(1,0xff1b));
        let fresh=capture(&mut i,&mut c,Kind::Press,0,key(1,0xff1b)).unwrap();
        assert!(!i.consume(old.press().unwrap())); assert!(eligible_escape(&fresh,&i,&c,&m)); assert!(i.consume(fresh.press().unwrap()));
    }
    #[test]
    fn stale_frame_or_modifier_change_refuses_before_consumption() {
        let (mut i,mut c,m)=setup(); let d=capture(&mut i,&mut c,Kind::Press,0,key(1,0xff1b)).unwrap();
        c.set_modifiers(0,Modifiers::default(),RawModifiers::default(),0);
        assert!(!eligible_escape(&d,&i,&c,&m)); assert!(i.is_current(d.press().unwrap()));
    }
    #[test]
    fn unknown_or_nonzero_modifiers_and_non_escape_are_refused() {
        let (mut i,mut c,m)=setup(); c.enter();
        let d=capture(&mut i,&mut c,Kind::Press,0,key(1,0xff1b)).unwrap(); assert!(!eligible_escape(&d,&i,&c,&m));
        let (mut i,mut c,m)=setup(); c.set_modifiers(0,Modifiers::default(),RawModifiers{locked:1,..RawModifiers::default()},0);
        let d=capture(&mut i,&mut c,Kind::Press,0,key(1,0xff1b)).unwrap(); assert!(!eligible_escape(&d,&i,&c,&m));
        let (mut i,mut c,m)=setup(); let d=capture(&mut i,&mut c,Kind::Press,0,key(28,0xff0d)).unwrap(); assert!(!eligible_escape(&d,&i,&c,&m));
    }
    #[test]
    fn separate_or_recreated_seat_cannot_consume_another_witness() {
        let (mut i,mut c,m)=setup(); let d=capture(&mut i,&mut c,Kind::Press,0,key(1,0xff1b)).unwrap();
        let (mut other,other_context,_)=setup(); assert!(!other.consume(d.press().unwrap()));
        assert!(!eligible_escape(&d,&other,&other_context,&m)); assert!(i.consume(d.press().unwrap()));
    }
    #[test]
    fn actual_teardown_closure_preserves_unrelated_roots_and_terminates_cycles() {
        let closing=descendant_surfaces("root",[("child","leaf"),("other","unrelated"),
            ("root","child"),("leaf","child"),("root","child"),("leaf","root")]);
        assert_eq!(closing,vec!["root","child","leaf"]);
        assert_eq!(descendant_surfaces("unknown",[("other","unrelated")]),vec!["unknown"]);
        assert_eq!(descendant_surfaces("root",Vec::<(&str,&str)>::new()),vec!["root"]);
        for root in ["ordinary-root", "overflow-root"] {
            assert_eq!(descendant_surfaces(root,[("child","grandchild"),(root,"child"),
                ("unrelated-root","unrelated-child")]),vec![root,"child","grandchild"]);
        }
    }
    #[test]
    fn actual_selected_teardown_is_child_first_and_idempotent() {
        for root in ["ordinary-root", "overflow-root"] {
            let edges=[("child","grandchild"),(root,"child"),("other","unrelated")];
            let selected=descendant_surfaces(root,edges);
            assert_eq!(teardown_order(selected.into_iter().chain([root]),edges),
                vec!["grandchild","child",root]);
            assert_eq!(teardown_order(Vec::<&str>::new(),edges),Vec::<&str>::new());
        }
        assert_eq!(teardown_order(["root","child","root"],[("root","child"),("child","root")]),
            vec!["child","root"]);
    }
    #[test]
    fn actual_ordered_batch_keeps_native_owners_until_their_drop_step() {
        use std::{cell::RefCell, collections::BTreeSet, rc::Rc};
        struct Owner { id: u32, live: Rc<RefCell<BTreeSet<u32>>>, trace: Rc<RefCell<Vec<u32>>> }
        impl Drop for Owner {
            fn drop(&mut self) {
                assert!(self.live.borrow_mut().remove(&self.id));
                self.trace.borrow_mut().push(self.id);
            }
        }
        let live=Rc::new(RefCell::new(BTreeSet::from([1,2,3,99])));
        let trace=Rc::new(RefCell::new(Vec::new()));
        let make=|id| Owner {id, live:live.clone(), trace:trace.clone()};
        let unrelated=make(99);
        let batch=vec![(1,make(1)),(2,make(2)),(3,make(3))];
        ordered_teardown(batch,[(1,2),(2,3)],|owner| {
            // Equivalent to native notification/focus cleanup: NO prior owner
            // drop, ancestors and unrelated native owners still retained.
            assert!(live.borrow().contains(&1));
            assert!(live.borrow().contains(&99));
            assert_eq!(live.borrow().len(),4-trace.borrow().len());
            if owner.id==3 { assert!(trace.borrow().is_empty()); }
            drop(owner);
        });
        assert_eq!(*trace.borrow(),vec![3,2,1]);
        assert_eq!(*live.borrow(),BTreeSet::from([99]));
        ordered_teardown(Vec::<(u32,Owner)>::new(),[(1,2)],|_| panic!("late batch must be empty"));
        drop(unrelated);
        assert_eq!(*trace.borrow(),vec![3,2,1,99]);
    }
    #[test]
    fn focus_invalidation_clears_consumption_without_resurrection() {
        let (mut i,mut c,m)=setup(); let d=capture(&mut i,&mut c,Kind::Press,0,key(1,0xff1b)).unwrap();
        assert!(i.consume(d.press().unwrap())); i.invalidate(); c.invalidate(); i.enter(&[]); c.enter();
        c.set_modifiers(0,Modifiers::default(),RawModifiers::default(),0);
        let fresh=capture(&mut i,&mut c,Kind::Press,0,key(1,0xff1b)).unwrap(); assert!(!i.consume(d.press().unwrap()));
        assert!(eligible_escape(&fresh,&i,&c,&m)); assert!(i.consume(fresh.press().unwrap()));
    }
}
