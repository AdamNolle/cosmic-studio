// SPDX-License-Identifier: GPL-3.0-only
//! Focus ownership only. No key conversion, activation, popup serial or hiding.
use std::collections::BTreeSet;

#[derive(Default)]
pub(super) struct FocusSeats(BTreeSet<String>);

impl FocusSeats {
    /// Focus the cached widget only on the first admitted native seat.
    pub(super) fn enter(&mut self, seat: &str) -> bool {
        let was_empty = self.0.is_empty();
        self.0.insert(seat.to_owned()) && was_empty
    }

    /// Unfocus only when the final actual owner leaves. Unknown leave is inert.
    pub(super) fn leave(&mut self, seat: &str) -> bool {
        self.0.remove(seat) && self.0.is_empty()
    }
}

#[cfg(test)]
mod tests {
    use super::FocusSeats;
    #[test]
    fn first_owner_focuses_and_last_owner_unfocuses() {
        let mut seats = FocusSeats::default();
        assert!(seats.enter("seat0"));
        assert!(seats.leave("seat0"));
    }
    #[test]
    fn second_owner_does_not_duplicate_focus_or_clear_first() {
        let mut seats = FocusSeats::default();
        assert!(seats.enter("seat0"));
        assert!(!seats.enter("seat1"));
        assert!(!seats.leave("seat0"));
        assert!(seats.leave("seat1"));
    }
    #[test]
    fn duplicate_enter_is_not_a_second_owner() {
        let mut seats = FocusSeats::default();
        assert!(seats.enter("seat0"));
        assert!(!seats.enter("seat0"));
        assert!(seats.leave("seat0"));
        assert!(!seats.leave("seat0"));
    }
    #[test]
    fn unknown_leave_and_new_clone_state_do_not_inherit_focus() {
        let mut seats = FocusSeats::default();
        assert!(!seats.leave("seat0"));
        assert!(seats.enter("seat0"));
        let mut fresh = FocusSeats::default();
        assert!(!fresh.leave("seat0"));
        assert!(fresh.enter("seat0"));
    }
    #[test]
    fn distinct_names_are_not_normalized() {
        let mut seats = FocusSeats::default();
        assert!(seats.enter("Seat0"));
        assert!(!seats.enter("seat0"));
        assert!(!seats.leave("Seat0"));
        assert!(seats.leave("seat0"));
    }
}
