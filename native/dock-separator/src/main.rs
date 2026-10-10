// SPDX-License-Identifier: MIT

use cosmic::{Application, Element, Theme, app, iced, widget};
use iced::{Length, Limits};
use std::sync::LazyLock;

static AUTOSIZE_ID: LazyLock<widget::Id> =
    LazyLock::new(|| widget::Id::new("cosmic-studio-dock-separator"));

struct Separator {
    core: app::Core,
}

#[derive(Debug, Clone)]
enum Message {}

#[derive(Clone, Copy, Debug, PartialEq)]
struct Geometry {
    width: f32,
    height: f32,
    line_width: f32,
    line_height: f32,
}

impl Geometry {
    fn new(horizontal_dock: bool, cross_axis: f32) -> Self {
        let cross_axis = if cross_axis.is_finite() {
            cross_axis.max(1.0)
        } else {
            56.0
        };
        let major_axis = if cross_axis >= 64.0 { 24.0 } else { 20.0 };
        let line = (cross_axis - 16.0).max(0.0).min(cross_axis * 0.5).min(36.0);
        if horizontal_dock {
            Self {
                width: major_axis,
                height: cross_axis,
                line_width: 1.0,
                line_height: line,
            }
        } else {
            Self {
                width: cross_axis,
                height: major_axis,
                line_width: line,
                line_height: 1.0,
            }
        }
    }
}

fn content<'a, M: 'a, R: iced::advanced::Renderer + 'a>(
    geometry: Geometry,
) -> iced::Element<'a, M, Theme, R> {
    let line = widget::container(
        widget::Space::new()
            .width(Length::Fixed(geometry.line_width))
            .height(Length::Fixed(geometry.line_height)),
    )
    .class(cosmic::theme::Container::custom(|theme| {
        let mut neutral: iced::Color = theme.cosmic().on_bg_color().into();
        neutral.a = 0.28;
        widget::container::Style {
            background: Some(neutral.into()),
            snap: true,
            ..Default::default()
        }
    }));
    widget::container(line)
        .center_x(Length::Fixed(geometry.width))
        .center_y(Length::Fixed(geometry.height))
        .into()
}

impl Application for Separator {
    type Message = Message;
    type Executor = cosmic::SingleThreadExecutor;
    type Flags = ();
    const APP_ID: &'static str = "local-dock-divider-applet";

    fn init(mut core: app::Core, _flags: ()) -> (Self, app::Task<Message>) {
        // This static line uses the dock's backdrop and never requests another
        // blur capture or rounded-surface pass of its own.
        core.set_auto_blur(Default::default());
        core.set_auto_corner_radius(Default::default());
        (Self { core }, cosmic::Task::none())
    }

    fn core(&self) -> &app::Core {
        &self.core
    }

    fn core_mut(&mut self) -> &mut app::Core {
        &mut self.core
    }

    fn style(&self) -> Option<iced::theme::Style> {
        Some(cosmic::applet::style())
    }

    fn update(&mut self, message: Message) -> app::Task<Message> {
        match message {}
    }

    fn view(&self) -> Element<'_, Message> {
        let context = &self.core.applet;
        let horizontal = context.is_horizontal();
        let suggested = context.suggested_size(false);
        let (_, minor_padding) = context.suggested_padding(false);
        let native_cross = if horizontal { suggested.1 } else { suggested.0 } + 2 * minor_padding;
        let cross = context
            .suggested_bounds
            .map(|bounds| {
                if horizontal {
                    bounds.height
                } else {
                    bounds.width
                }
            })
            .filter(|dimension| dimension.is_finite() && *dimension > 0.0)
            .unwrap_or(f32::from(native_cross));
        let geometry = Geometry::new(horizontal, cross);

        // A direct native autosize root avoids the ordinary icon button's
        // 64px minimum slot while retaining Wayland's size negotiation.
        widget::autosize::autosize(content(geometry), AUTOSIZE_ID.clone())
            .limits(Limits::NONE.width(geometry.width).height(geometry.height))
            .into()
    }
}

fn main() -> iced::Result {
    cosmic::applet::run::<Separator>(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use iced::advanced::{layout, widget::Tree};

    #[test]
    fn native_layout_keeps_the_separator_narrow_and_centers_the_rule() {
        for horizontal in [true, false] {
            let geometry = Geometry::new(horizontal, 56.0);
            let mut element: iced::Element<'_, (), Theme, ()> = content(geometry);
            let mut tree = Tree::new(element.as_widget());
            let node = element
                .as_widget_mut()
                .layout(&mut tree, &(), &layout::Limits::NONE);
            let slot = node.size();
            let rule = node.children()[0].bounds();
            let (major, cross) = if horizontal {
                (slot.width, slot.height)
            } else {
                (slot.height, slot.width)
            };
            assert_eq!((major, cross), (20.0, 56.0));
            assert_eq!(
                (rule.center_x(), rule.center_y()),
                (slot.width / 2.0, slot.height / 2.0)
            );
            assert_eq!(rule.width.min(rule.height), 1.0);
            assert_eq!(rule.width.max(rule.height), 28.0);
        }
    }

    #[test]
    fn geometry_transposes_at_large_sizes_and_fits_tiny_configures() {
        let wide = Geometry::new(true, 80.0);
        let tall = Geometry::new(false, 80.0);
        assert_eq!((wide.width, wide.height), (24.0, 80.0));
        assert_eq!((tall.width, tall.height), (80.0, 24.0));
        assert_eq!(
            (wide.line_width, wide.line_height),
            (tall.line_height, tall.line_width)
        );
        for cross in [1.0, 8.0, 16.0, 32.0, 56.0, 64.0, 80.0] {
            let geometry = Geometry::new(true, cross);
            assert!(geometry.line_height <= geometry.height);
            assert!(geometry.line_height <= 36.0);
            assert_eq!(geometry.line_width, 1.0);
        }
        assert_eq!(Geometry::new(true, f32::NAN), Geometry::new(true, 56.0));
    }
}
