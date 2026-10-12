// SPDX-License-Identifier: GPL-3.0-only
// Original Studio normalization of sysinfo's already-delta byte counts.
// This does not query hardware, subtract cumulative counters, or certify sensors.
use std::{collections::BTreeSet, ffi::OsString, time::{Duration, Instant}};

#[derive(Default)]
pub(crate) struct RateWindow {
    previous: Option<(Instant, BTreeSet<OsString>)>,
}

impl RateWindow {
    pub(crate) fn reset(&mut self) {
        self.previous = None;
    }

    pub(crate) fn elapsed(&mut self, now: Instant, identities: impl IntoIterator<Item=OsString>) -> Option<Duration> {
        let identities: BTreeSet<_> = identities.into_iter().collect();
        if identities.is_empty() {
            self.reset();
            return None;
        }
        let previous = self.previous.replace((now, identities.clone()))?;
        if previous.1 != identities {
            return None;
        }
        now.checked_duration_since(previous.0).filter(|elapsed| !elapsed.is_zero())
    }
}

pub(crate) fn megabytes_per_second(bytes: Option<u64>, elapsed: Option<Duration>) -> Option<f64> {
    let seconds = elapsed?.as_secs_f64();
    if seconds == 0.0 {
        return None;
    }
    Some(bytes? as f64 / 1_000_000.0 / seconds)
}

#[cfg(test)]
mod tests {
    use super::*;
    fn ids(names: &[&str]) -> Vec<OsString> { names.iter().map(OsString::from).collect() }

    #[test]
    fn first_sample_is_unknown_then_real_zero_is_zero() {
        let mut window = RateWindow::default();let now = Instant::now();
        assert_eq!(window.elapsed(now,ids(&["disk"])),None);
        let elapsed = window.elapsed(now+Duration::from_secs(1),ids(&["disk"]));
        assert_eq!(megabytes_per_second(Some(0),elapsed),Some(0.0));
    }

    #[test]
    fn delayed_and_fractional_windows_are_not_assumed_one_second() {
        assert_eq!(megabytes_per_second(Some(8_000_000),Some(Duration::from_secs(2))),Some(4.0));
        assert_eq!(megabytes_per_second(Some(8_000_000),Some(Duration::from_millis(500))),Some(16.0));
    }

    #[test]
    fn zero_time_overflow_and_missing_measurements_are_unknown() {
        assert_eq!(megabytes_per_second(Some(123),Some(Duration::ZERO)),None);
        assert_eq!(megabytes_per_second(None,Some(Duration::from_secs(1))),None);
        assert_eq!(megabytes_per_second(Some(123),None),None);
        assert!(megabytes_per_second(Some(u64::MAX),Some(Duration::from_nanos(1))).unwrap().is_finite());
    }

    #[test]
    fn identity_changes_rebaseline_without_case_normalization() {
        let mut window = RateWindow::default();let now = Instant::now();
        assert_eq!(window.elapsed(now,ids(&["A","b"])),None);
        assert!(window.elapsed(now+Duration::from_secs(1),ids(&["b","A"])).is_some());
        assert_eq!(window.elapsed(now+Duration::from_secs(2),ids(&["a","b"])),None);
    }

    #[test]
    fn pause_empty_devices_and_clock_regression_rebaseline() {
        let mut window = RateWindow::default();let now = Instant::now();
        assert_eq!(window.elapsed(now,ids(&["disk"])),None);window.reset();
        assert_eq!(window.elapsed(now+Duration::from_secs(1),ids(&["disk"])),None);
        assert_eq!(window.elapsed(now+Duration::from_secs(2),ids(&[])),None);
        assert_eq!(window.elapsed(now+Duration::from_secs(3),ids(&["disk"])),None);
        assert_eq!(window.elapsed(now+Duration::from_secs(2),ids(&["disk"])),None);
    }
}
