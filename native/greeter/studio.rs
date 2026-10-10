// COSMIC Studio lock/login appearance. Authentication and session state stay
// in upstream greeter/locker code; this module selects only fonts and theme.
use std::borrow::Cow;
use std::sync::{Arc, Once};

pub fn load_fonts() {
    static LOAD: Once = Once::new();
    LOAD.call_once(|| {
        // Parse authentic licensed faces once through COSMIC's own text engine.
        let faces: &[&'static [u8]] = &[
            include_bytes!("../fonts/archivo/Archivo-Regular.ttf"),
            include_bytes!("../fonts/archivo/Archivo-Italic.ttf"),
            include_bytes!("../fonts/archivo/Archivo-Medium.ttf"),
            include_bytes!("../fonts/archivo/Archivo-MediumItalic.ttf"),
            include_bytes!("../fonts/archivo/Archivo-SemiBold.ttf"),
            include_bytes!("../fonts/archivo/Archivo-SemiBoldItalic.ttf"),
            include_bytes!("../fonts/archivo/Archivo-Bold.ttf"),
            include_bytes!("../fonts/archivo/Archivo-BoldItalic.ttf"),
            include_bytes!("../fonts/instrumentserif/InstrumentSerif-Regular.ttf"),
            include_bytes!("../fonts/instrumentserif/InstrumentSerif-Italic.ttf"),
        ];
        let mut fonts = cosmic::iced::advanced::graphics::text::font_system()
            .write()
            .expect("native font system poisoned");
        for face in faces {
            fonts.load_font(Cow::Borrowed(*face));
        }
    });
}

pub fn dark_theme() -> cosmic::Theme {
    cosmic::Theme::custom(Arc::new(cosmic::theme::system_dark().cosmic().clone()))
}

pub fn select_theme(theme: &cosmic::Theme) -> cosmic::Theme {
    if theme.cosmic().is_high_contrast {
        theme.clone()
    } else {
        dark_theme()
    }
}

pub fn theme_for(theme: Option<&cosmic::cosmic_theme::Theme>) -> cosmic::Theme {
    match theme {
        Some(theme) if theme.is_high_contrast => cosmic::Theme::custom(Arc::new(theme.clone())),
        _ => dark_theme(),
    }
}

#[cfg(test)]
mod studio_tests {
    use super::*;

    #[test]
    fn embedded_faces_are_available_once_without_fontconfig_or_a_display() {
        load_fonts();
        let fonts = cosmic::iced::advanced::graphics::text::font_system().read().unwrap();
        let before = fonts.db().faces().count();
        for family in ["Archivo", "Instrument Serif"] {
            assert!(fonts.db().faces().any(|face| face.families.iter().any(|(name, _)| name == family)));
        }
        drop(fonts);
        load_fonts();
        let fonts = cosmic::iced::advanced::graphics::text::font_system().read().unwrap();
        assert_eq!(before, fonts.db().faces().count());
    }

    #[test]
    fn dark_shell_appearance_does_not_change_global_user_preferences() {
        let before = cosmic::theme::active_type();
        assert!(dark_theme().cosmic().is_dark);
        assert_eq!(before, cosmic::theme::active_type());
        assert!(select_theme(&cosmic::theme::system_light()).cosmic().is_dark);
    }

    #[test]
    fn explicit_high_contrast_theme_survives_the_dark_default() {
        let mut theme = cosmic::theme::system_light().cosmic().clone();
        theme.is_high_contrast = true;
        let selected = theme_for(Some(&theme));
        assert!(selected.cosmic().is_high_contrast);
        assert!(!selected.cosmic().is_dark);
        assert!(select_theme(&selected).cosmic().is_high_contrast);
    }
}
