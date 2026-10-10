    /// An owned palette for an old managed native popup. Main windows keep
    /// their original palette. No corner, accent or high-contrast changes.
    #[must_use]
    pub fn with_popup_material(&self, alpha: f32) -> Self {
        let mut material = self.clone();
        if self.is_high_contrast {
            return material;
        }
        let alpha = alpha.clamp(0.0, 1.0);
        let control_alpha = alpha.max(0.98);
        for container in [&mut material.background,
                          &mut material.primary,
                          &mut material.secondary] {
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
        material.text_button.on = material.background.on;
        material.text_button.on_disabled = material.background.component.on_disabled;
        material
    }
