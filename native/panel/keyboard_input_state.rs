// SPDX-License-Identifier: GPL-3.0-only
// COSMIC Studio candidate prerequisite, 2026-10-11.
// Original client raw/serial/time namespaces only; no Iced events or popup grants.
use std::{collections::BTreeMap, fmt, sync::Arc};

#[derive(Clone)]
pub(crate) struct ClientPress<O> {
    pub(crate) origin: O,
    pub(crate) raw_code: u32,
    pub(crate) serial: u32,
    pub(crate) time: u32,
    focus: Arc<()>,
    // Distinct from focus: a release ends this exact press even if raw/serial/time
    // are later reused within the same focus lifetime.
    press: Arc<()>,
}

impl<O> fmt::Debug for ClientPress<O> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("ClientPress").finish_non_exhaustive()
    }
}

pub(crate) struct InputLedger<O> {
    origin: O,
    focus: Option<Arc<()>>,
    // None is a key held on entry: no original press serial exists in this focus.
    held: BTreeMap<u32, Option<ClientPress<O>>>,
}

impl<O> fmt::Debug for InputLedger<O> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("InputLedger")
            .field("focused", &self.focus.is_some())
            .field("held_count", &self.held.len())
            .finish_non_exhaustive()
    }
}

impl<O: Clone + PartialEq> InputLedger<O> {
    pub(crate) fn new(origin: O) -> Self {
        Self { origin, focus: None, held: BTreeMap::new() }
    }

    pub(crate) fn enter(&mut self, raw: &[u32]) {
        // Allocation identity prevents stale focus reuse without serial/time
        // arithmetic or epoch wrap. Outstanding snapshots keep the old token alive.
        self.focus = Some(Arc::new(()));
        self.held = raw.iter().map(|&key| (key, None)).collect();
    }

    pub(crate) fn invalidate(&mut self) {
        self.focus = None;
        self.held.clear();
    }

    pub(crate) fn press(&mut self, raw_code: u32, serial: u32, time: u32) -> Option<ClientPress<O>> {
        let focus = self.focus.as_ref()?;
        if self.held.contains_key(&raw_code) {
            // A duplicate down/repeat cannot replace the original press authority.
            return None;
        }
        let press = ClientPress { origin: self.origin.clone(), raw_code, serial, time, focus: focus.clone(), press: Arc::new(()) };
        let _ = self.held.insert(raw_code, Some(press.clone()));
        Some(press)
    }

    pub(crate) fn release(&mut self, raw_code: u32) -> bool {
        self.held.remove(&raw_code).is_some()
    }

    // Necessary provenance/lifetime check only; NOT popup-grab authorization.
    // Later activation must additionally validate native seat/keyboard/surface,
    // modifiers, the exact client serial, popup-root/grab and event/message order.
    pub(crate) fn is_current(&self, press: &ClientPress<O>) -> bool {
        self.origin == press.origin
            && self.focus.as_ref().is_some_and(|focus| Arc::ptr_eq(focus, &press.focus))
            && self.held.get(&press.raw_code).and_then(Option::as_ref).is_some_and(|held| {
                Arc::ptr_eq(&held.press, &press.press)
                    && held.serial == press.serial && held.time == press.time
            })
    }
}

#[cfg(test)]
mod tests {
    use super::InputLedger;
    #[test]
    fn held_on_enter_never_arms_until_release_and_new_press() {
        let mut input = InputLedger::new("client-seat");input.enter(&[28, 28, 57]);
        assert!(input.press(28, 9, 10).is_none());assert!(input.release(28));
        let press = input.press(28, 11, 12).unwrap();assert!(input.is_current(&press));
        assert_eq!((press.origin, press.raw_code, press.serial, press.time), ("client-seat", 28, 11, 12));
        assert!(input.press(57, 13, 14).is_none());
    }
    #[test]
    fn duplicate_down_does_not_refresh_original_client_authority() {
        let mut input = InputLedger::new("seat");input.enter(&[]);
        let press = input.press(30, 1, 2).unwrap();assert!(input.press(30, 999, 1000).is_none());
        assert!(input.is_current(&press));assert_eq!((press.serial, press.time), (1, 2));
    }
    #[test]
    fn leave_reenter_and_reused_serial_cannot_resurrect_old_focus() {
        let mut input = InputLedger::new("seat");input.enter(&[]);
        let old = input.press(28, 1, 2).unwrap();input.invalidate();assert!(!input.is_current(&old));
        input.enter(&[]);let new = input.press(28, 1, 2).unwrap();
        assert!(!input.is_current(&old));assert!(input.is_current(&new));
    }
    #[test]
    fn separate_seats_and_recreated_ledger_do_not_share_lifetime() {
        let mut a = InputLedger::new("Seat0");let mut b = InputLedger::new("seat0");
        a.enter(&[]);b.enter(&[]);let press = a.press(28, 5, 6).unwrap();
        let _ = b.press(28, 5, 6);assert!(!b.is_current(&press));
        let mut replacement = InputLedger::new("Seat0");replacement.enter(&[]);
        let _ = replacement.press(28, 5, 6);assert!(!replacement.is_current(&press));
    }
    #[test]
    fn release_unknown_and_other_raw_key_do_not_clear_survivor() {
        let mut input = InputLedger::new("seat");input.enter(&[]);let press = input.press(28, 3, 4).unwrap();
        assert!(!input.release(29));assert!(input.is_current(&press));
        assert!(input.release(28));assert!(!input.is_current(&press));assert!(!input.release(28));
    }
    #[test]
    fn released_press_cannot_resurrect_when_serial_and_time_are_reused() {
        let mut input = InputLedger::new("client-seat");input.enter(&[]);
        let old = input.press(28, 7, 8).unwrap();assert!(input.release(28));
        assert!(!input.is_current(&old));
        let fresh = input.press(28, 7, 8).unwrap();assert!(input.is_current(&fresh));
        assert!(!input.is_current(&old));
    }
    #[test]
    fn unfocused_keymap_or_capability_invalidation_is_fail_closed() {
        let mut input = InputLedger::new("seat");assert!(input.press(28, 1, 2).is_none());
        input.enter(&[]);let press = input.press(28, 1, 2).unwrap();input.invalidate();
        assert!(!input.is_current(&press));assert!(input.press(28, 3, 4).is_none());
    }
    #[test]
    fn client_values_are_not_normalized_or_replaced_with_server_serials() {
        let mut input = InputLedger::new(41);input.enter(&[]);
        let press = input.press(u32::MAX, 0, u32::MAX).unwrap();
        assert_eq!((press.origin, press.raw_code, press.serial, press.time),(41,u32::MAX,0,u32::MAX));
        assert!(input.is_current(&press));
    }
    #[test]
    fn debug_does_not_log_key_values_or_client_identity() {
        let mut input = InputLedger::new("private-client-identity");input.enter(&[]);
        let press = input.press(123456, 789012, 345678).unwrap();
        for text in [format!("{input:?}"),format!("{press:?}")] {
            for forbidden in ["private-client-identity","123456","789012","345678"] { assert!(!text.contains(forbidden)); }
        }
    }
}
