// Copyright 2026 COSMIC Studio contributors
// SPDX-License-Identifier: MPL-2.0

use super::{CosmicTheme, Theme, ThemeType};
use std::sync::{Arc, LazyLock, Mutex};

pub(crate) const TINT_ALPHA: f32 = 0.95;

struct CachedMaterial {
    source_key: usize,
    // Retain the original Arc so its address cannot be reused for a new theme.
    _source: ThemeType,
    material: Arc<CosmicTheme>,
}

// At most two palettes (normally dark and light). Theme refreshes replace the
// oldest entry; ordinary redraws only clone an Arc. No colors/radii are global.
static CACHE: LazyLock<Mutex<Vec<CachedMaterial>>> = LazyLock::new(|| Mutex::new(Vec::new()));

pub(crate) fn is_material(theme: &Theme) -> bool {
    if !theme.transparent {
        return false;
    }
    let key = theme.cosmic() as *const CosmicTheme as usize;
    CACHE.lock().unwrap_or_else(|e| e.into_inner()).iter().any(|entry| {
        Arc::as_ptr(&entry.material) as usize == key
    })
}

/// Called only for tracked XDG Popup surfaces by Cosmic::theme(id).
/// A failed/absent protocol uses the original opaque palette. Main windows,
/// layer surfaces, input-method popups and in-buffer overlays never enter here.
pub(crate) fn for_popup(mut theme: Theme, blur: bool) -> Theme {
    if !crate::popup_policy::enabled() {
        return theme;
    }
    if theme.cosmic().is_high_contrast {
        // Accessibility palettes use their original opaque containers. Do not
        // tint, recolor or cache a translucent derivative of that palette.
        theme.transparent = false;
        return theme;
    }
    theme.transparent = blur;
    if !blur {
        return theme;
    }

    let source_key = theme.cosmic() as *const CosmicTheme as usize;
    let mut cache = CACHE.lock().unwrap_or_else(|e| e.into_inner());
    let material = if let Some(entry) = cache.iter().find(|entry| entry.source_key == source_key) {
        Arc::clone(&entry.material)
    } else {
        let material = Arc::new(theme.cosmic().with_popup_material(TINT_ALPHA));
        if cache.len() == 2 {
            cache.remove(0);
        }
        cache.push(CachedMaterial {
            source_key,
            _source: theme.theme_type.clone(),
            material: Arc::clone(&material),
        });
        material
    };
    drop(cache);
    theme.theme_type = match theme.theme_type {
        ThemeType::System { prefer_dark, .. } => ThemeType::System { theme: material, prefer_dark },
        _ => ThemeType::Custom(material),
    };
    theme
}
