// SPDX-License-Identifier: GPL-3.0-only
// Diagnostic only: call the actual compiled COSMIC SDK button widget.
// No client keyboard, serial, popup grant, event loop or desktop acceptance.
use cosmic::iced::{Event, Size, Point, Rectangle, mouse,
    keyboard::{self, key::Named, Key, Location, Modifiers},
    core::{Font, Pixels, Layout, Shell, widget::{Tree, operation::focusable}, layout, clipboard::Null}};

struct ButtonProbe {
    element: cosmic::Element<'static, u8>,
    tree: Tree,
    node: layout::Node,
    renderer: cosmic::Renderer,
}
impl ButtonProbe {
    fn new(focused: bool) -> Self {
        let id = cosmic::widget::Id::unique();
        let mut element: cosmic::Element<'static, u8> = cosmic::widget::button::custom(
            cosmic::iced::widget::Space::new().width(20).height(20),
        ).id(id.clone()).on_press(7).into();
        let mut tree = Tree::new(element.as_widget());
        let renderer = cosmic::Renderer::new(Font::default(), Pixels(16.0));
        let node = element.as_widget_mut().layout(&mut tree, &renderer,
            &layout::Limits::new(Size::ZERO, Size::new(80.0, 80.0)));
        if focused {
            element.as_widget_mut().operate(&mut tree, Layout::new(&node), &renderer,
                &mut focusable::focus::<()>(id));
        }
        Self { element, tree, node, renderer }
    }
    fn event(&mut self, event: Event) -> Vec<u8> {
        let mut messages = Vec::new();
        self.element.as_widget_mut().update(&mut self.tree, &event, Layout::new(&self.node),
            mouse::Cursor::Available(Point::new(5.0, 5.0)), &self.renderer,
            &mut Null, &mut Shell::new(&mut messages), &Rectangle::with_size(Size::new(80.0,80.0)));
        messages
    }
    fn unfocus(&mut self) {
        self.element.as_widget_mut().operate(&mut self.tree, Layout::new(&self.node),
            &self.renderer, &mut focusable::unfocus::<()>());
    }
}
fn press(key: Key, repeat: bool) -> Event {
    Event::Keyboard(keyboard::Event::KeyPressed {
        key: key.clone(), modified_key: key,
        physical_key: keyboard::key::Physical::Unidentified(keyboard::key::NativeCode::Unidentified),
        location: Location::Standard, modifiers: Modifiers::empty(), text: None, repeat,
    })
}
fn release(key: Key) -> Event {
    Event::Keyboard(keyboard::Event::KeyReleased {
        key: key.clone(), modified_key: key,
        physical_key: keyboard::key::Physical::Unidentified(keyboard::key::NativeCode::Unidentified),
        location: Location::Standard, modifiers: Modifiers::empty(),
    })
}
fn pointer_release() -> Event { Event::Mouse(mouse::Event::ButtonReleased(mouse::Button::Left)) }
fn enter() -> Key { Key::Named(Named::Enter) }
fn space() -> Key { Key::Character(" ".into()) }

#[test]
fn actual_button_requires_widget_focus_for_enter() {
    assert!(ButtonProbe::new(false).event(press(enter(),false)).is_empty());
    assert_eq!(ButtonProbe::new(true).event(press(enter(),false)),vec![7]);
}
#[test]
fn actual_button_repeat_enter_emits_another_activation() {
    let mut button=ButtonProbe::new(true);
    assert_eq!(button.event(press(enter(),false)),vec![7]);
    assert_eq!(button.event(press(enter(),true)),vec![7]);
}
#[test]
fn actual_button_space_does_not_activate() {
    let mut button=ButtonProbe::new(true);
    assert!(button.event(press(space(),false)).is_empty());
    assert!(button.event(release(space())).is_empty());
    assert!(button.event(pointer_release()).is_empty());
}
#[test]
fn actual_button_enter_release_leaves_later_pointer_activation() {
    let mut untouched=ButtonProbe::new(true);
    assert!(untouched.event(pointer_release()).is_empty());
    let mut button=ButtonProbe::new(true);
    assert_eq!(button.event(press(enter(),false)),vec![7]);
    assert!(button.event(release(enter())).is_empty());
    assert_eq!(button.event(pointer_release()),vec![7]);
    assert!(button.event(pointer_release()).is_empty());
}
#[test]
fn actual_button_unfocus_does_not_clear_keyboard_pressed_pointer_state() {
    let mut button=ButtonProbe::new(true);
    assert_eq!(button.event(press(enter(),false)),vec![7]);
    button.unfocus();
    assert_eq!(button.event(pointer_release()),vec![7]);
}
#[test]
fn actual_button_cursor_leave_clears_pressed_state_without_activation() {
    let mut button=ButtonProbe::new(true);
    assert_eq!(button.event(press(enter(),false)),vec![7]);
    assert!(button.event(Event::Mouse(mouse::Event::CursorLeft)).is_empty());
    assert!(button.event(pointer_release()).is_empty());
}
