// Copyright 2026 COSMIC Studio contributors
// SPDX-License-Identifier: MPL-2.0

use std::sync::LazyLock;

// Read once per process. Nothing consults the environment during a redraw.
static ENABLED: LazyLock<bool> = LazyLock::new(|| {
    std::env::var("COSMIC_STUDIO_POPUP_GLASS").as_deref() == Ok("1")
});

pub(crate) fn enabled() -> bool {
    *ENABLED
}

/// Neutral ordinary chrome is independent of window transparency. Preserve the
/// native high-contrast palette and all semantic widget states outside headers.
pub(crate) const fn neutral_header_icon(opted_in: bool, high_contrast: bool) -> bool {
    opted_in && !high_contrast
}

/// Explicit surface settings take priority, but unsupported effects never
/// activate translucent material. Both creation and refresh use this rule.
pub(crate) const fn resolve_blur(supported: bool, automatic: bool, explicit: Option<bool>) -> bool {
    supported && match explicit {
        Some(value) => value,
        None => automatic,
    }
}

#[cfg(test)]
mod tests {
    use super::{enabled, neutral_header_icon, resolve_blur};

    #[test]
    fn ordinary_header_icons_are_neutral_only_when_opted_in_and_accessible() {
        assert!(neutral_header_icon(true, false));
        assert!(!neutral_header_icon(false, false));
        assert!(!neutral_header_icon(true, true));
        assert!(!neutral_header_icon(false, true));
    }

    #[test]
    fn opt_in_is_exact_and_cached() {
        let expected = std::env::var("COSMIC_STUDIO_POPUP_GLASS").as_deref() == Ok("1");
        assert_eq!(enabled(), expected);
        // Run these unit tests serially. Other tests do not read the environment.
        unsafe { std::env::set_var("COSMIC_STUDIO_POPUP_GLASS", if expected { "0" } else { "1" }); }
        assert_eq!(enabled(), expected);
    }

    #[test]
    fn explicit_overrides_survive_automatic_policy_changes() {
        assert!(resolve_blur(true, false, Some(true)));
        assert!(resolve_blur(true, true, Some(true)));
        assert!(!resolve_blur(true, true, Some(false)));
        assert!(!resolve_blur(true, false, Some(false)));
    }

    #[test]
    fn unsupported_protocol_is_always_opaque() {
        for automatic in [false, true] {
            for explicit in [None, Some(false), Some(true)] {
                assert!(!resolve_blur(false, automatic, explicit));
            }
        }
    }

    #[test]
    fn automatic_policy_applies_without_override() {
        assert!(resolve_blur(true, true, None));
        assert!(!resolve_blur(true, false, None));
    }
}
