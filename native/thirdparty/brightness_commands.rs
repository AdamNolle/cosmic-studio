// SPDX-License-Identifier: GPL-3.0-only
// Original Studio command batching for the exact reviewed Brightness application.
// One group action is one watch-channel value: all its monitor writes survive.
// This does NOT make the upstream watch channel a FIFO across distinct actions.
pub type DisplayId = String;
pub type ScreenBrightness = u16;

#[derive(Debug, Clone)]
pub enum EventToSub {
    Refresh,
    Set(DisplayId, ScreenBrightness),
    SetBatch(Vec<(DisplayId, ScreenBrightness)>),
}

impl EventToSub {
    pub fn into_writes(self) -> Option<Vec<(DisplayId, ScreenBrightness)>> {
        match self {
            Self::Refresh => None,
            Self::Set(id, value) => Some(vec![(id, value)]),
            Self::SetBatch(writes) => Some(writes),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn group_action_preserves_each_monitor_without_receiver_scheduling() {
        let writes = vec![("display-a".into(), 30), ("display-b".into(), 70), ("display-c".into(), 95)];
        assert_eq!(EventToSub::SetBatch(writes.clone()).into_writes(), Some(writes));
    }

    #[test]
    fn single_monitor_command_keeps_original_identity_and_value() {
        assert_eq!(EventToSub::Set("display-b".into(), 42).into_writes(), Some(vec![("display-b".into(), 42)]));
    }

    #[test]
    fn refresh_remains_distinct_from_an_empty_write_batch() {
        assert!(EventToSub::Refresh.into_writes().is_none());
        assert_eq!(EventToSub::SetBatch(vec![]).into_writes(), Some(vec![]));
    }

    #[test]
    fn bounds_are_not_replaced_with_an_invented_brightness() {
        assert_eq!(EventToSub::SetBatch(vec![("low".into(), 0), ("high".into(), 100)]).into_writes(),
                   Some(vec![("low".into(), 0), ("high".into(), 100)]));
    }

    #[test]
    fn original_order_is_preserved_without_monitor_name_normalization() {
        let writes = vec![("DP-2".into(), 15), ("dp-2".into(), 85)];
        assert_eq!(EventToSub::SetBatch(writes.clone()).into_writes(), Some(writes));
    }
}
