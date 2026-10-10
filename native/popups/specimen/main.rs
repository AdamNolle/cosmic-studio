// Copyright 2026 COSMIC Studio contributors
// SPDX-License-Identifier: MPL-2.0

//! Private-fixture specimen: an actual managed XDG popup, no CSS/SHM rendering.
use cosmic::app::{Core, Settings, Task};
use cosmic::cctk::sctk::reexports::protocols::xdg::shell::client::xdg_positioner::{Anchor, Gravity};
use cosmic::iced::{self, window, Length, Rectangle, Size, Subscription};
use cosmic::surface::action::{app_popup, LiveSettings};
use cosmic::widget::{self, button, column, container, row};
use cosmic::{Element, Theme};
use iced_runtime::platform_specific::wayland::popup::{SctkPopupSettings, SctkPositioner};
use std::sync::Arc;
use std::path::Path;

mod guard;

const APP_ID: &str = "org.cosmicstudio.PopupSpecimen";

#[derive(Clone, Debug)]
enum Message {
    Open,
    Noop,
    Surface(cosmic::surface::Action<Message>),
}

struct Specimen {
    core: Core,
    popup: Option<window::Id>,
    mode: String,
}

impl cosmic::Application for Specimen {
    type Executor = cosmic::SingleThreadExecutor;
    type Flags = String;
    type Message = Message;
    const APP_ID: &'static str = APP_ID;

    fn core(&self) -> &Core { &self.core }
    fn core_mut(&mut self) -> &mut Core { &mut self.core }

    fn init(core: Core, mode: String) -> (Self, Task<Message>) {
        let parent = core.main_window_id().unwrap_or(window::Id::RESERVED);
        let title = core.set_title(None, format!("Native popup specimen · {mode}"));
        // Resolves against the native window handle, so popup creation occurs
        // after its parent exists. Opened subscription is an idempotent backup.
        let ready = window::run_with_handle(parent, |_| Message::Open).map(cosmic::Action::App);
        (Self { core, popup: None, mode }, Task::batch([title, ready]))
    }

    fn subscription(&self) -> Subscription<Message> {
        iced::event::listen_with(|event, _, _| {
            matches!(event, iced::Event::Window(window::Event::Opened { .. })).then_some(Message::Open)
        })
    }

    fn update(&mut self, message: Message) -> Task<Message> {
        match message {
            Message::Open if self.popup.is_none() => {
                let action = app_popup::<Self>(
                    |_| LiveSettings { blur: Some(true), ..Default::default() },
                    |state| {
                        let id = window::Id::unique();
                        state.popup = Some(id);
                        SctkPopupSettings {
                            parent: state.core.main_window_id().unwrap_or(window::Id::RESERVED),
                            id,
                            positioner: SctkPositioner {
                                size: Some((376, 330)),
                                // Adjacent to the parent, so the real popup samples wallpaper
                                // rather than overlapping opaque fixture text.
                                anchor_rect: Rectangle { x: 359, y: 70, width: 1, height: 1 },
                                anchor: Anchor::BottomRight,
                                gravity: Gravity::BottomRight,
                                offset: (0, 0),
                                ..Default::default()
                            },
                            parent_size: None,
                            // Automatic fixture opening does not have an input
                            // serial. It exercises the native popup protocol.
                            grab: false,
                            close_with_children: true,
                            input_zone: None,
                        }
                    },
                    Some(Box::new(|state| state.popup_view().map(cosmic::Action::App))),
                );
                cosmic::task::message(cosmic::Action::Surface(action))
            }
            Message::Surface(action) => cosmic::task::message(cosmic::Action::Surface(action)),
            _ => Task::none(),
        }
    }

    fn view(&self) -> Element<'_, Message> {
        container(column::with_capacity(2)
            .push(widget::text::heading("Native popup material"))
            .push(widget::text::body("This parent uses the original opaque window palette."))
            .spacing(12))
            .padding(24)
            .width(Length::Fill)
            .height(Length::Fill)
            .class(cosmic::theme::Container::Background)
            .into()
    }
}

impl Specimen {
    fn popup_view(&self) -> Element<'_, Message> {
        let controls = row::with_capacity(3)
            .push(button::standard("Ordinary").on_press(Message::Noop))
            .push(button::icon(widget::icon::from_name("edit-copy-symbolic")).on_press(Message::Noop))
            .push(button::standard("Disabled"))
            .spacing(8);
        let primary = container(column::with_capacity(2)
            .push(widget::text::body("Primary container · opaque labels"))
            .push(controls)
            .spacing(12))
            .padding(12)
            .class(cosmic::theme::Container::Primary);
        let secondary = container(row::with_capacity(2)
            .push(widget::text::body("Secondary state"))
            .push(button::suggested("Selected").on_press(Message::Noop))
            .spacing(12))
            .padding(12)
            .class(cosmic::theme::Container::Secondary);
        container(column::with_capacity(5)
            .push(widget::text::heading(format!("Glass popup · {}", self.mode)))
            .push(widget::text::body("Archivo body · Instrument Serif title"))
            .push(primary)
            .push(secondary)
            .push(button::text("More options")
                .trailing_icon(widget::icon::from_name("go-next-symbolic"))
                .width(Length::Fill)
                .on_press(Message::Noop))
            .spacing(12))
            .padding(18)
            .width(Length::Fill)
            .height(Length::Fill)
            .class(cosmic::theme::Container::Background)
            .into()
    }
}

fn main() -> iced::Result {
    // Refuse accidental use in the user's session. The harness must supply all
    // private XDG paths, private bus and Wayland socket, plus this explicit flag.
    assert_eq!(std::env::var("STUDIO_PRIVATE_TEST").as_deref(), Ok("1"));
    for name in ["XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS", "WAYLAND_DISPLAY"] {
        assert!(std::env::var_os(name).is_some(), "private fixture requires {name}");
    }
    let user_id = unsafe { libc::geteuid() };
    // Obtain real account home from the OS; private HOME overrides cannot
    // accidentally make the guard treat the host's config as a fixture.
    let account = unsafe { libc::getpwuid(user_id) };
    assert!(!account.is_null(), "cannot determine real account home");
    let host_home = unsafe { std::ffi::CStr::from_ptr((*account).pw_dir) }.to_string_lossy().into_owned();
    guard::validate(
        Path::new(&std::env::var("XDG_RUNTIME_DIR").unwrap()),
        Path::new(&std::env::var("WAYLAND_DISPLAY").unwrap()),
        Path::new(&std::env::var("XDG_CONFIG_HOME").unwrap()),
        Path::new(&std::env::var("XDG_DATA_HOME").unwrap()),
        user_id, Path::new(&host_home),
    ).expect("unsafe native fixture environment");
    let mode = std::env::args().nth(1).unwrap_or_else(|| "dark".into());
    let source = match mode.as_str() {
        "dark" => cosmic::cosmic_theme::Theme::dark_default(),
        "light" => cosmic::cosmic_theme::Theme::light_default(),
        "contrast-dark" => cosmic::cosmic_theme::Theme::high_contrast_dark_default(),
        "contrast-light" => cosmic::cosmic_theme::Theme::high_contrast_light_default(),
        _ => panic!("theme must be dark, light, contrast-dark or contrast-light"),
    };
    // This fixture-owned palette matches the subtle native corner design. It
    // never writes config or changes toolkit/global/user preferences.
    let mut source = source;
    source.corner_radii = cosmic::cosmic_theme::CornerRadii {
        radius_0: [0.0; 4], radius_xs: [2.0; 4], radius_s: [4.0; 4],
        radius_m: [6.0; 4], radius_l: [8.0; 4], radius_xl: [10.0; 4],
    };
    let theme = Theme { theme_type: cosmic::theme::ThemeType::Custom(Arc::new(source)), ..Default::default() };
    cosmic::app::run::<Specimen>(Settings::default().size(Size::new(360.0, 280.0)).theme(theme), mode)
}

#[cfg(test)]
mod tests {
    use super::*;
    use cosmic::iced::widget::container::Catalog;

    #[test]
    fn native_header_icons_are_neutral_without_window_or_popup_identity() {
        let opted_in = std::env::var("COSMIC_STUDIO_POPUP_GLASS").as_deref() == Ok("1");
        // Original/opaque parent, derived Popup and derived Window palettes
        // share the same native class rule; private material-cache identity is
        // intentionally absent here. No actual window, renderer or bus opens.
        for source in [cosmic::cosmic_theme::Theme::dark_default(),
                       cosmic::cosmic_theme::Theme::light_default(),
                       cosmic::cosmic_theme::Theme::high_contrast_dark_default(),
                       cosmic::cosmic_theme::Theme::high_contrast_light_default()] {
            for palette in [source.clone(), source.with_popup_material(0.95), source.with_window_material()] {
                for transparent in [false, true] {
                    let theme = Theme {
                        theme_type: cosmic::theme::ThemeType::Custom(Arc::new(palette.clone())),
                        transparent,
                        ..Default::default()
                    };
                    let style = <Theme as Catalog>::style(&theme, &cosmic::theme::Container::HeaderBar {
                        focused: true, sharp_corners: false, transparent,
                    });
                    let expected: iced::Color = if opted_in && !palette.is_high_contrast {
                        palette.background(transparent).on.into()
                    } else {
                        palette.accent_text_color().into()
                    };
                    assert_eq!(style.icon_color, Some(expected));
                    assert_eq!(style.text_color, Some(palette.background(transparent).on.into()));
                    // Original semantic widget palettes remain byte-for-byte.
                    assert_eq!(palette.accent_button, source.accent_button);
                    assert_eq!(palette.destructive_button, source.destructive_button);
                    assert_eq!(palette.link_button, source.link_button);
                    assert_eq!(palette.icon_button, source.icon_button);
                }
            }
        }
    }
}
