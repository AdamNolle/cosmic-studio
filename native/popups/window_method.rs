    /// Readable material for opted-in native system windows. Opaque source
    /// containers and all semantic accent/error colors remain unchanged.
    #[must_use]
    pub fn with_window_material(&self) -> Self {
        if self.is_high_contrast {
            return self.clone();
        }
        let mut material = self.with_popup_material(0.95);
        material.transparent_primary.base.alpha = 1.00;
        material.transparent_secondary.base.alpha = 1.00;
        for container in [&mut material.transparent_background,
                          &mut material.transparent_primary,
                          &mut material.transparent_secondary] {
            container.component.base.alpha = 1.00;
            container.component.hover.alpha = container.component.hover.alpha.max(1.00);
            container.component.pressed.alpha = container.component.pressed.alpha.max(1.00);
        }
        material
    }

