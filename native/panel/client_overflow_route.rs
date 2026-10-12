// SPDX-License-Identifier: GPL-3.0-only
// Synchronous actual client callback delivery to the INERT overflow view.
// These checks are NOT an activation, popup-grab or deferred-work grant.
use crate::iced::elements::{CosmicMappedInternal, overflow_button::OverflowButtonElement,
    target::SpaceTarget};
use crate::xdg_shell_wrapper::{shared_state::GlobalState,
    client_state::{FocusStatus, client_focus_match, client_iced_event::Converted}};
use cosmic::Task;
use sctk::reexports::client::{Proxy, protocol::wl_keyboard::WlKeyboard};
use sctk::shell::WaylandSurface;
use smithay::desktop::space::SpaceElement;

// Exact overflow type, not arbitrary Programs. Never invoke ordinary Program
// update, return a task, use pointer history or retain authority for later work.
fn deliver_inert<O>(
    button: &OverflowButtonElement, event: &Converted<O>,
    validate: impl FnMut(&Converted<O>) -> bool,
) -> bool {
    button.update_keyboard(event, validate, |_, _, _| Task::none()).is_ok()
}

impl GlobalState {
    pub(crate) fn route_overflow_keyboard(&self, keyboard: &WlKeyboard) {
        // Called AFTER original kbd.input returns, never inside a Smithay
        // filter/target callback. Unknown/ambiguous/dead originating devices fail.
        if !keyboard.is_alive() { return; }
        let mut seats = self.server_state.seats.iter().filter(|seat|
            seat.client.kbd.as_ref() == Some(keyboard));
        let Some(seat) = seats.next() else { return; };
        if seats.next().is_some() || !seat.client._seat.is_alive() { return; }
        let Some(delivery) = seat.client.key_delivery.as_ref() else { return; };
        if delivery.frame().origin() != &seat.client._seat
            || !seat.client.key_events.is_current(delivery.frame()) { return; }
        let Some(kbd) = seat.server.seat.get_keyboard() else { return; };
        // All Smithay queries precede the element mutex. No recursive locking,
        // lock inversion or keyboard query in the validator/dispatcher below.
        if kbd.is_grabbed() { return; }
        let Some(target @ SpaceTarget::OverflowButton(_)) = kbd.current_focus() else { return; };
        let SpaceTarget::OverflowButton(button) = &target else { return; };
        let focused = self.client_state.focused_surface.borrow();
        let Some(index) = client_focus_match::active_index(&focused, &seat.name,
            |status| matches!(status, FocusStatus::Focused)) else { return; };
        let outer = &focused[index].0;
        if !outer.is_alive() { return; }
        // Recheck original same-seat outer layer and actual mapped target, not
        // stale last-focus history, pointer selection, IDs or a fresh enter.
        let mut panels = self.space.space_list.iter().filter(|panel|
            panel.layer.as_ref().is_some_and(|layer| layer.wl_surface() == outer
                && layer.wl_surface().is_alive())
            && panel.popups.is_empty() && panel.overflow_popup.is_none()
            && panel.s_focused_surface.iter().filter(|(_, name)| name == &seat.name).count() == 1
            && panel.s_focused_surface.iter().any(|(focus, name)| name == &seat.name && focus == &target));
        let Some(panel) = panels.next() else { return; };
        if panels.next().is_some() { return; }
        let mut mapped = panel.space.elements().filter(|element|
            matches!(element, CosmicMappedInternal::OverflowButton(candidate) if candidate == button));
        let Some(element) = mapped.next() else { return; };
        if mapped.next().is_some() || panel.space.element_location(element).is_none() { return; }
        // geometry() locks the element: it MUST be evaluated before wrapper lock.
        let geometry = element.geometry();
        if geometry.size.w <= 0 || geometry.size.h <= 0 { return; }
        let Ok(converted) = seat.client.iced_key_event(delivery.frame()) else { return; };
        // No event-loop yield/native callback between snapshot and inert UI.
        // &self remains immutable; the isolated view never handles keyboard in
        // SDK/content. Validator is pure original-frame freshness, not live
        // popup admission. It does not lock/re-enter this or any other element.
        let _ = deliver_inert(button, &converted, |original|
            original.original().origin() == &seat.client._seat
                && seat.client.key_events.is_current(original.original()));
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::iced::elements::overflow_button::{OverflowButton, Message};
    use crate::xdg_shell_wrapper::client_state::{client_iced_event::{self, Context},
        client_keymap::ClientKeymap, keyboard_event_context::Kind};
    use cosmic::iced::{Event, mouse, widget::Id};
    use sctk::seat::keyboard::{KeyEvent, Modifiers, RawModifiers};
    use smithay::input::keyboard::xkb;
    use std::{borrow::Cow, sync::{Arc, atomic::{AtomicBool, Ordering}}};

    fn setup() -> (OverflowButtonElement, calloop::EventLoop<'static, GlobalState>, Arc<AtomicBool>) {
        let event_loop = calloop::EventLoop::try_new().unwrap();
        let selected = Arc::new(AtomicBool::new(false));
        let program = OverflowButton::new(Id::unique(), (0,0).into(), 20,
            cosmic::iced::Padding::from(0), selected.clone(), Cow::Borrowed("view-more-symbolic"), 1);
        let element = crate::iced::IcedElement::new(program, (40,40), event_loop.handle(),
            cosmic::Theme::default(), 1, false);
        (element, event_loop, selected)
    }
    fn event(kind: Kind, space: bool, text: Option<&str>) -> Converted<&'static str> {
        let mut map = ClientKeymap::default();
        map.replace(r#"xkb_keymap {
            xkb_keycodes { minimum=8; maximum=255; <ENTER>=36; <SPACE>=65; <CTRL>=37; };
            xkb_types { type "ONE" { modifiers=none; map[None]=Level1; }; };
            xkb_compatibility { };
            xkb_symbols { key <ENTER> { type="ONE", [ Return ] }; key <SPACE> { type="ONE", [ space ] };
                key <CTRL> { [ Control_L ] }; modifier_map Control { <CTRL> }; };
        };"#.into());
        let mut context = Context::new("Seat0"); context.enter();
        context.set_modifiers(0, Modifiers::default(), RawModifiers::default(), 0);
        let frame = context.capture(kind, u32::MAX, KeyEvent { time: 0,
            raw_code: if space {57} else {28}, keysym: xkb::Keysym::new(if space {0x20} else {0xff0d}),
            utf8: text.map(Into::into) }).unwrap();
        client_iced_event::convert(&map, &context, &frame).unwrap()
    }
    #[test]
    fn actual_overflow_wrapper_preserves_original_press_repeat_release() {
        let (element, _loop, selected) = setup();
        for kind in [Kind::Press, Kind::Repeat, Kind::Release] {
            for space in [false,true] { for text in [None, Some(""), Some("é🦀")] {
                let original = event(kind, space, text); let mut calls=0;
                assert!(deliver_inert(&element, &original, |context| {
                    calls+=1; let f=context.original();
                    assert_eq!((*f.origin(),f.kind(),f.serial(),f.event().time),("Seat0",kind,u32::MAX,0));
                    assert_eq!(f.event().utf8.as_deref(),text); true
                }));
                assert_eq!(calls,1); assert!(!selected.load(Ordering::SeqCst));
                assert!(element.0.lock().unwrap().state.is_queue_empty());
            } }
        }
    }
    #[test]
    fn busy_pointer_work_refuses_before_original_validator() {
        let (element, _loop, _) = setup();
        element.0.lock().unwrap().state.queue_event(Event::Mouse(mouse::Event::CursorLeft));
        assert!(!deliver_inert(&element, &event(Kind::Press,false,None), |_| panic!("busy validated")));
        assert!(!element.0.lock().unwrap().state.is_queue_empty());
    }
    #[test]
    fn invalid_original_context_never_reaches_ui() {
        let (element, _loop, selected) = setup();
        assert!(!deliver_inert(&element, &event(Kind::Press,false,None), |_| false));
        assert!(element.0.lock().unwrap().state.is_queue_empty());
        assert!(!selected.load(Ordering::SeqCst));
        assert!(deliver_inert(&element, &event(Kind::Press,false,None), |_| true));
    }
    #[test]
    fn contextless_task_work_is_not_flushed_or_attributed() {
        let (element, _loop, _) = setup(); let (tx, rx)=std::sync::mpsc::channel();
        element.0.lock().unwrap().rx=rx.into(); tx.send(Some(Message::TogglePopup)).unwrap();
        assert!(!deliver_inert(&element, &event(Kind::Press,false,None), |_| panic!("task validated")));
        assert!(matches!(element.0.lock().unwrap().rx.try_recv(), Ok(Some(Message::TogglePopup))));
    }
    #[test]
    fn none_task_output_remains_pending_untrusted_work() {
        let (element, _loop, _) = setup(); let (tx, rx)=std::sync::mpsc::channel();
        element.0.lock().unwrap().rx=rx.into(); tx.send(None).unwrap();
        assert!(!deliver_inert(&element, &event(Kind::Repeat,true,Some("")), |_| panic!("none validated")));
        assert!(matches!(element.0.lock().unwrap().rx.try_recv(), Ok(None)));
    }
}
