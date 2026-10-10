use cosmic_theme::{Container, Theme};

fn blend(container: &Container, backdrop: [f32; 3], control: bool) -> [f32; 3] {
    let bg = container.base;
    let base = [bg.color.red, bg.color.green, bg.color.blue];
    let mut rendered = std::array::from_fn(|i| base[i] * bg.alpha + backdrop[i] * (1.0 - bg.alpha));
    if control {
        let color = container.component.base;
        let rgb = [color.color.red, color.color.green, color.color.blue];
        rendered = std::array::from_fn(|i| rgb[i] * color.alpha + rendered[i] * (1.0 - color.alpha));
    }
    rendered
}

fn luminance(rgb: [f32; 3]) -> f32 {
    let linear = rgb.map(|v| if v <= 0.04045 { v / 12.92 } else { ((v + 0.055) / 1.055).powf(2.4) });
    linear[0] * 0.2126 + linear[1] * 0.7152 + linear[2] * 0.0722
}

fn contrast(foreground: [f32; 3], background: [f32; 3]) -> f32 {
    let fg = luminance(foreground);
    let bg = luminance(background);
    (fg.max(bg) + 0.05) / (fg.min(bg) + 0.05)
}

#[test]
fn real_light_dark_palettes_keep_opaque_text_readable_over_extreme_backdrops() {
    let backdrops = [[0.0; 3], [1.0; 3], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0], [0.0, 0.4, 1.0]];
    for source in [Theme::dark_default(), Theme::light_default()] {
        for (kind, material) in [("popup", source.with_popup_material(0.95)), ("window", source.with_window_material())] {
            let mut minimum = f32::MAX;
            for container in [material.background(true), material.primary(true), material.secondary(true)] {
                for control in [false, true] {
                    let text = if control { container.component.on } else { container.on };
                    assert_eq!(text.alpha, 1.0);
                    let foreground = [text.color.red, text.color.green, text.color.blue];
                    for backdrop in backdrops {
                        let value = contrast(foreground, blend(container, backdrop, control));
                        minimum = minimum.min(value);
                        assert!(value >= 4.5, "{kind}, dark={}, control={control}, backdrop={backdrop:?}: contrast={value}", source.is_dark);
                    }
                }
            }
            eprintln!("{kind}, dark={}: minimum contrast={minimum:.4}", source.is_dark);
        }
    }
}

#[test]
fn real_high_contrast_palettes_are_exact_original_opaque_fallbacks() {
    for source in [Theme::high_contrast_dark_default(), Theme::high_contrast_light_default()] {
        assert!(source.is_high_contrast);
        assert_eq!(source.with_popup_material(0.95), source);
        assert_eq!(source.with_window_material(), source);
        for container in [source.background(false), source.primary(false), source.secondary(false)] {
            assert_eq!(container.base.alpha, 1.0);
        }
    }
}

#[test]
fn real_palettes_keep_source_content_radii_and_semantic_states_exact() {
    for source in [Theme::dark_default(), Theme::light_default()] {
        let original = source.clone();
        for material in [source.with_popup_material(0.95), source.with_window_material()] {
            assert_eq!(material.background(false), source.background(false));
            assert_eq!(material.primary(false), source.primary(false));
            assert_eq!(material.secondary(false), source.secondary(false));
            assert_eq!(material.corner_radii, source.corner_radii);
            assert_eq!(material.accent_button, source.accent_button);
            assert_eq!(material.destructive_button, source.destructive_button);
            assert_eq!(material.icon_button, source.icon_button);
            assert_eq!(material.link_button, source.link_button);
            assert_eq!(material.text_button.selected_text, source.text_button.selected_text);
            assert_eq!(material.text_button.focus, source.text_button.focus);
            assert_eq!(material.text_button.on.color, source.background(true).on.color);
            assert_eq!(material.background(true).base.color, source.background(true).base.color);
        }
        assert_eq!(source, original);
    }
}
