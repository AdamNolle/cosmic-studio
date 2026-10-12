// SPDX-License-Identifier: GPL-3.0-only
// COSMIC Studio candidate, 2026-10-11. Original client event context only.
// No XKB reconstruction, Iced conversion, repeat generation or popup grants.
use std::{fmt, sync::Arc};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum Kind {
    Press,
    Release,
    Repeat,
}

#[derive(Clone)]
pub(crate) struct ModifierFrame<N, R> {
    serial: u32,
    named: N,
    raw: R,
    group: u32,
}

impl<N, R> ModifierFrame<N, R> {
    pub(crate) fn serial(&self) -> u32 { self.serial }
    pub(crate) fn named(&self) -> &N { &self.named }
    pub(crate) fn raw(&self) -> &R { &self.raw }
    pub(crate) fn group(&self) -> u32 { self.group }
}

// Fields are private: consumers can inspect/clone but not rewrite a captured
// serial, kind, text or modifier frame while retaining its lifetime witness.
#[derive(Clone)]
pub(crate) struct EventFrame<O, E, N, R> {
    origin: O,
    kind: Kind,
    serial: u32,
    event: E,
    modifiers: Option<ModifierFrame<N, R>>,
    focus: Arc<()>,
    identity: Arc<()>,
}

impl<O, E, N, R> EventFrame<O, E, N, R> {
    pub(crate) fn origin(&self) -> &O { &self.origin }
    pub(crate) fn kind(&self) -> Kind { self.kind }
    pub(crate) fn serial(&self) -> u32 { self.serial }
    pub(crate) fn event(&self) -> &E { &self.event }
    pub(crate) fn modifiers(&self) -> Option<&ModifierFrame<N, R>> { self.modifiers.as_ref() }
}

impl<O, E, N, R> fmt::Debug for EventFrame<O, E, N, R> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("EventFrame").field("kind", &self.kind).finish_non_exhaustive()
    }
}

pub(crate) struct EventContext<O, E, N, R> {
    origin: O,
    focus: Option<Arc<()>>,
    modifiers: Option<ModifierFrame<N, R>>,
    latest: Option<EventFrame<O, E, N, R>>,
}

impl<O, E, N, R> fmt::Debug for EventContext<O, E, N, R> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("EventContext")
            .field("focused", &self.focus.is_some())
            .field("has_modifier_frame", &self.modifiers.is_some())
            .field("has_event", &self.latest.is_some())
            .finish_non_exhaustive()
    }
}

impl<O: Clone + PartialEq, E: Clone, N: Clone, R: Clone> EventContext<O, E, N, R> {
    pub(crate) fn new(origin: O) -> Self {
        Self { origin, focus: None, modifiers: None, latest: None }
    }

    pub(crate) fn enter(&mut self) {
        self.invalidate();
        self.focus = Some(Arc::new(()));
    }

    pub(crate) fn invalidate(&mut self) {
        self.focus = None;
        self.modifiers = None;
        self.latest = None;
    }

    pub(crate) fn set_modifiers(&mut self, serial: u32, named: N, raw: R, group: u32) {
        if self.focus.is_some() {
            self.modifiers = Some(ModifierFrame { serial, named, raw, group });
            // A queued older event must not be treated as current authority
            // after modifier changes. Its immutable historical snapshot survives.
            self.latest = None;
        }
    }

    pub(crate) fn capture(&mut self, kind: Kind, serial: u32, event: E) -> Option<EventFrame<O, E, N, R>> {
        let focus = self.focus.as_ref()?;
        let frame = EventFrame {
            origin: self.origin.clone(), kind, serial, event,
            modifiers: self.modifiers.clone(), focus: focus.clone(),
            identity: Arc::new(()),
        };
        self.latest = Some(frame.clone());
        Some(frame)
    }

    pub(crate) fn latest(&self) -> Option<&EventFrame<O, E, N, R>> { self.latest.as_ref() }

    // Necessary current-context check only, NOT activation/pop-up authorization.
    // The input ledger's fresh client press, live native seat/keyboard/target and
    // popup/grab/queued event rules remain separate mandatory gates.
    pub(crate) fn is_current(&self, frame: &EventFrame<O, E, N, R>) -> bool {
        self.origin == frame.origin
            && self.focus.as_ref().is_some_and(|focus| Arc::ptr_eq(focus, &frame.focus))
            && self.latest.as_ref().is_some_and(|latest| Arc::ptr_eq(&latest.identity, &frame.identity))
    }
}

#[cfg(test)]
mod tests {
    use super::{EventContext, Kind};
    type Context = EventContext<&'static str, String, u32, [u32; 3]>;

    #[test]
    fn unfocused_events_and_modifiers_do_not_invent_defaults() {
        let mut context = Context::new("seat");
        context.set_modifiers(1, 2, [3, 4, 5], 6);
        assert!(context.capture(Kind::Press, 7, "é".into()).is_none());
        context.enter();
        let event = context.capture(Kind::Press, 8, "é".into()).unwrap();
        assert!(event.modifiers().is_none());
    }

    #[test]
    fn original_origin_kind_serial_and_composed_text_are_opaque() {
        let mut context = Context::new("Seat0");context.enter();
        let text = "é\u{301}日\0".to_string();
        let event = context.capture(Kind::Press, u32::MAX, text.clone()).unwrap();
        assert_eq!(*event.origin(), "Seat0");assert_eq!(event.kind(), Kind::Press);
        assert_eq!(event.serial(), u32::MAX);assert_eq!(event.event(), &text);
        assert!(context.is_current(&event));
    }

    #[test]
    fn modifier_snapshot_preserves_masks_layout_and_serial_without_mutation() {
        let mut context = Context::new("seat");context.enter();
        context.set_modifiers(0, 17, [u32::MAX, 0, 0x80000000], u32::MAX);
        let event = context.capture(Kind::Press, 8, "text".into()).unwrap();
        let modifiers = event.modifiers().unwrap();
        assert_eq!((modifiers.serial(), *modifiers.named(), *modifiers.raw(), modifiers.group()),
                   (0, 17, [u32::MAX, 0, 0x80000000], u32::MAX));
        context.set_modifiers(9, 0, [0; 3], 0);
        assert!(!context.is_current(&event));
        assert_eq!(*event.modifiers().unwrap().raw(), [u32::MAX, 0, 0x80000000]);
        let zero = context.capture(Kind::Release, 10, String::new()).unwrap();
        assert_eq!(*zero.modifiers().unwrap().raw(), [0; 3]);
    }

    #[test]
    fn duplicate_values_and_repeat_replace_latest_not_fifo_or_press_authority() {
        let mut context = Context::new("seat");context.enter();
        let first = context.capture(Kind::Press, 1, "x".into()).unwrap();
        let second = context.capture(Kind::Press, 1, "x".into()).unwrap();
        assert!(!context.is_current(&first));assert!(context.is_current(&second));
        let repeated = context.capture(Kind::Repeat, 1, "x".into()).unwrap();
        assert_eq!(repeated.kind(), Kind::Repeat);assert!(!context.is_current(&second));
        assert_eq!(context.latest().unwrap().kind(), Kind::Repeat);
    }

    #[test]
    fn release_record_keeps_original_payload_without_creating_text() {
        let mut context = Context::new("seat");context.enter();
        let event = context.capture(Kind::Release, 0, String::new()).unwrap();
        assert_eq!(event.kind(), Kind::Release);assert_eq!(event.event(), "");
        assert_eq!(event.serial(), 0);
    }

    #[test]
    fn focus_and_keymap_capability_invalidation_never_resurrect_old_events() {
        let mut context = Context::new("seat");context.enter();
        let old = context.capture(Kind::Press, 1, "x".into()).unwrap();
        context.invalidate();assert!(!context.is_current(&old));assert!(context.latest().is_none());
        context.enter();let fresh = context.capture(Kind::Press, 1, "x".into()).unwrap();
        assert!(!context.is_current(&old));assert!(context.is_current(&fresh));
        assert!(fresh.modifiers().is_none());
    }

    #[test]
    fn separate_and_recreated_seats_do_not_share_lifetime() {
        let mut a = Context::new("Seat0");let mut b = Context::new("seat0");
        a.enter();b.enter();let old = a.capture(Kind::Press, 1, "x".into()).unwrap();
        let _ = b.capture(Kind::Press, 1, "x".into());assert!(!b.is_current(&old));
        let mut replacement = Context::new("Seat0");replacement.enter();
        let _ = replacement.capture(Kind::Press, 1, "x".into());assert!(!replacement.is_current(&old));
    }

    #[test]
    fn debug_never_logs_text_serial_origin_masks_or_group() {
        let mut context = Context::new("private-seat");context.enter();
        context.set_modifiers(789012, 123456, [123456; 3], 123456);
        let event = context.capture(Kind::Press, 789012, "private-text".into()).unwrap();
        for text in [format!("{context:?}"), format!("{event:?}")] {
            for forbidden in ["private-seat", "private-text", "123456", "789012"] {
                assert!(!text.contains(forbidden));
            }
        }
    }
}
