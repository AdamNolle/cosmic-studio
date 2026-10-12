// SPDX-License-Identifier: GPL-3.0-only
// Same-seat active callback focus selection; not keyboard popup authorization.

pub(crate) fn active_index<T, S>(
    rows: &[(T, String, S)],
    seat: &str,
    mut active: impl FnMut(&S) -> bool,
) -> Option<usize> {
    let mut matching = rows.iter().enumerate().filter_map(|(i, (_, name, status))| {
        (name == seat && active(status)).then_some(i)
    });
    let index = matching.next()?;
    // Never pick the first of ambiguous same-seat active rows.
    matching.next().is_none().then_some(index)
}

pub(crate) fn leave_index<T: PartialEq, S>(
    rows: &[(T, String, S)],
    seat: &str,
    surface: &T,
    active: impl FnMut(&S) -> bool,
) -> Option<usize> {
    let index = active_index(rows, seat, active)?;
    (&rows[index].0 == surface).then_some(index)
}

#[cfg(test)]
mod tests {
    use super::*;
    fn row(surface: u32, seat: &str, active: bool) -> (u32, String, bool) {
        (surface, seat.into(), active)
    }

    #[test]
    fn shared_surface_leave_selects_only_originating_seat() {
        let rows = vec![row(10, "first", true), row(10, "second", true)];
        assert_eq!(leave_index(&rows, "second", &10, |s| *s), Some(1));
        assert_eq!(leave_index(&rows, "absent", &10, |s| *s), None);
    }
    #[test]
    fn stale_leave_does_not_select_new_active_surface() {
        let rows = vec![row(10, "seat", false), row(11, "seat", true)];
        assert_eq!(leave_index(&rows, "seat", &10, |s| *s), None);
        assert_eq!(leave_index(&rows, "seat", &11, |s| *s), Some(1));
    }
    #[test]
    fn last_focused_history_is_not_active_press_focus() {
        let rows = vec![row(10, "seat", false)];
        assert_eq!(active_index(&rows, "seat", |s| *s), None);
        assert_eq!(leave_index(&rows, "seat", &10, |s| *s), None);
    }
    #[test]
    fn ambiguous_active_rows_refuse_even_matching_surface() {
        for other in [10, 11] {
            let rows = vec![row(10, "seat", true), row(other, "seat", true)];
            assert_eq!(active_index(&rows, "seat", |s| *s), None);
            assert_eq!(leave_index(&rows, "seat", &10, |s| *s), None);
        }
    }
    #[test]
    fn exact_seat_names_and_other_inactive_rows_remain_distinct() {
        let rows = vec![row(10, "Seat", true), row(11, "seat", true), row(12, "seat", false)];
        assert_eq!(active_index(&rows, "Seat", |s| *s), Some(0));
        assert_eq!(active_index(&rows, "seat", |s| *s), Some(1));
        assert_eq!(active_index(&rows, "SEAT", |s| *s), None);
    }
    #[test]
    fn empty_unknown_surface_and_repeated_leave_are_inert() {
        let mut rows = vec![row(10, "seat", true)];
        assert_eq!(leave_index(&rows, "seat", &99, |s| *s), None);
        let index = leave_index(&rows, "seat", &10, |s| *s).unwrap();
        rows[index].2 = false;
        assert_eq!(leave_index(&rows, "seat", &10, |s| *s), None);
        assert_eq!(active_index::<u32, bool>(&[], "seat", |s| *s), None);
    }
}
