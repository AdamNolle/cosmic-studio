// Copyright 2026 COSMIC Studio contributors
// SPDX-License-Identifier: MPL-2.0

use super::{CosmicTheme, Theme, ThemeType};
use std::sync::{Arc, LazyLock, Mutex};

struct CachedMaterial {
    source_key: usize,
    // Keep source Arcs alive so an address cannot be reused for another palette.
    _source: ThemeType,
    material: Arc<CosmicTheme>,
}

static CACHE: LazyLock<Mutex<Vec<CachedMaterial>>> = LazyLock::new(|| Mutex::new(Vec::new()));

pub(crate) fn is_material(theme: &Theme) -> bool {
    let key = theme.cosmic() as *const CosmicTheme as usize;
    CACHE.lock().unwrap_or_else(|e| e.into_inner()).iter().any(|entry| {
        Arc::as_ptr(&entry.material) as usize == key
    })
}

/// Only managed XDG popup IDs enter this function. Old Theme has no global
/// transparency field: palette ownership and the clear style stay per-popup.
pub(crate) fn for_popup(mut theme: Theme, supported: bool) -> Theme {
    if !crate::popup_policy::enabled() || !supported || theme.cosmic().is_high_contrast {
        return theme;
    }
    let source_key = theme.cosmic() as *const CosmicTheme as usize;
    let mut cache = CACHE.lock().unwrap_or_else(|e| e.into_inner());
    let material = if let Some(entry) = cache.iter().find(|entry| entry.source_key == source_key) {
        Arc::clone(&entry.material)
    } else {
        let material = Arc::new(theme.cosmic().with_popup_material(0.95));
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
