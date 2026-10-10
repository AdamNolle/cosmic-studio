    /// Clone this palette for a native popup without changing opaque containers,
    /// selection colors, fonts, or user corner radii. Active text stays opaque.
    #[must_use]
    pub fn with_popup_material(&self, alpha: f32) -> Self {
        let mut material = self.clone();
        if self.is_high_contrast {
            return material;
        }
        let alpha = alpha.clamp(0.0, 1.0);
        let control_alpha = alpha.max(0.98);
        for container in [&mut material.transparent_background,
                          &mut material.transparent_primary,
                          &mut material.transparent_secondary] {
            container.base.alpha = alpha;
            container.on.alpha = 1.0;
            container.component.base.alpha = control_alpha;
            container.component.on.alpha = 1.0;
            container.component.selected_text.alpha = 1.0;
            for state in [&mut container.component.hover, &mut container.component.pressed] {
                if state.alpha <= 0.001 {
                    *state = container.component.base;
                } else {
                    state.alpha = state.alpha.max(control_alpha);
                }
            }
            container.divider.alpha = container.divider.alpha.min(0.24);
            container.component.divider.alpha = container.component.divider.alpha.min(0.24);
        }
        // Ordinary text controls use neutral labels. Links, suggested actions,
        // focus and selected-state accents retain their native semantic colors.
        material.text_button.on = material.transparent_background.on;
        material.text_button.on_disabled = material.transparent_background.component.on_disabled;
        material
    }
