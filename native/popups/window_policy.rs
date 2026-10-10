// Copyright 2026 COSMIC Studio contributors
// SPDX-License-Identifier: MPL-2.0

use std::sync::LazyLock;

// This is independent from popup opt-in. Only the Files and Settings launch
// wrappers export it; document, editor and terminal clients remain unchanged.
static ENABLED: LazyLock<bool> = LazyLock::new(|| {
    std::env::var("COSMIC_STUDIO_WINDOW_GLASS").as_deref() == Ok("1")
});

pub(crate) fn enabled() -> bool {
    *ENABLED
}

/// An explicit tracked surface type takes priority over reserved/main IDs.
/// Untracked IDs must be the actual main window; other windows use native
/// AppWindow/get_window tracking, so raw unknown IDs remain conservative.
pub(crate) const fn is_window_surface(tracked_window: Option<bool>, main: bool) -> bool {
    match tracked_window {
        Some(window) => window,
        None => main,
    }
}

pub(crate) const fn automatic(
    auto_window: bool,
    high_contrast: bool,
    maximized_or_tiled: bool,
    frosted_maximized_apps: bool,
) -> bool {
    auto_window && !high_contrast && (!maximized_or_tiled || frosted_maximized_apps)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn native_maximized_policy_and_accessibility_take_priority() {
        assert!(automatic(true, false, false, false));
        assert!(!automatic(false, false, false, false));
        assert!(!automatic(true, true, false, true));
        assert!(!automatic(true, false, true, false));
        assert!(automatic(true, false, true, true));
    }

    #[test]
    fn exact_opt_in_is_cached_independently() {
        let expected = std::env::var("COSMIC_STUDIO_WINDOW_GLASS").as_deref() == Ok("1");
        assert_eq!(enabled(), expected);
        // This test runs in a serial test process with no other environment
        // writers. Changing the process environment does not alter the policy.
        unsafe { std::env::set_var("COSMIC_STUDIO_WINDOW_GLASS", if expected { "0" } else { "1" }) };
        assert_eq!(enabled(), expected);
    }
}
