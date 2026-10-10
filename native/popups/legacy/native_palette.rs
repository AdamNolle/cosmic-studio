use cosmic_theme::{Container, Theme};

fn blend(container: &Container, backdrop: [f32; 3], control: bool) -> [f32; 3] {
    let bg = container.base;
    let rgb = [bg.color.red, bg.color.green, bg.color.blue];
    let mut out = std::array::from_fn(|i| rgb[i] * bg.alpha + backdrop[i] * (1.0 - bg.alpha));
    if control {
        let color = container.component.base;
        let rgb = [color.color.red, color.color.green, color.color.blue];
        out = std::array::from_fn(|i| rgb[i] * color.alpha + out[i] * (1.0 - color.alpha));
    }
    out
}

fn luminance(rgb: [f32; 3]) -> f32 {
    let linear = rgb.map(|v| if v <= 0.04045 { v / 12.92 } else { ((v + 0.055) / 1.055).powf(2.4) });
    linear[0] * 0.2126 + linear[1] * 0.7152 + linear[2] * 0.0722
}

fn contrast(fg: [f32; 3], bg: [f32; 3]) -> f32 {
    let (a, b) = (luminance(fg), luminance(bg));
    (a.max(b) + 0.05) / (a.min(b) + 0.05)
}

#[test]
fn actual_old_popup_palettes_keep_text_readable_over_extreme_backdrops() {
    for source in [Theme::dark_default(), Theme::light_default()] {
        let material = source.with_popup_material(0.95);
        let mut minimum = f32::MAX;
        for container in [&material.background, &material.primary, &material.secondary] {
            for control in [false, true] {
                let text = if control { container.component.on } else { container.on };
                assert_eq!(text.alpha, 1.0);
                let fg = [text.color.red, text.color.green, text.color.blue];
                for bg in [[0.0; 3], [1.0; 3], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0], [0.0, 0.4, 1.0]] {
                    let value = contrast(fg, blend(container, bg, control));
                    minimum = minimum.min(value);
                    assert!(value >= 4.5, "legacy, dark={}, control={control}, bg={bg:?}, contrast={value}", source.is_dark);
                }
            }
        }
        eprintln!("legacy popup, dark={}: minimum contrast={minimum:.4}", source.is_dark);
    }
}

#[test]
fn actual_old_high_contrast_keeps_exact_original_opaque_palette() {
    for source in [Theme::high_contrast_dark_default(), Theme::high_contrast_light_default()] {
        assert!(source.is_high_contrast);
        assert_eq!(source.with_popup_material(0.95), source);
        for container in [&source.background, &source.primary, &source.secondary] {
            assert_eq!(container.base.alpha, 1.0);
        }
    }
}

#[test]
fn actual_old_source_radii_and_semantic_states_are_preserved() {
    for source in [Theme::dark_default(), Theme::light_default()] {
        let before = source.clone();
        let material = source.with_popup_material(0.95);
        assert_eq!(material.corner_radii, source.corner_radii);
        assert_eq!(material.accent_button, source.accent_button);
        assert_eq!(material.destructive_button, source.destructive_button);
        assert_eq!(material.icon_button, source.icon_button);
        assert_eq!(material.link_button, source.link_button);
        assert_eq!(material.text_button.selected_text, source.text_button.selected_text);
        assert_eq!(material.text_button.focus, source.text_button.focus);
        assert_eq!(material.text_button.on.color, source.background.on.color);
        assert_eq!(material.background.base.color, source.background.base.color);
        assert_eq!(source, before);
    }
}
