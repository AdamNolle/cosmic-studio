// SPDX-License-Identifier: GPL-3.0-only
// Overflow-local fail-closed isolation, not keyboard activation/authority.
// Never pass a keyboard event to the SDK button's shared pointer state.
use cosmic::iced::core::{self, Clipboard, Event, Layout, Length, Rectangle, Shell, Size,
    Vector, Widget, layout, mouse, overlay, renderer, widget::{Id, Operation, Tree, tree}};

pub(super) fn isolate<'a, M: 'a>(content: cosmic::Element<'a, M>) -> cosmic::Element<'a, M> {
    cosmic::Element::new(Isolated(content))
}
struct Isolated<'a, M>(cosmic::Element<'a, M>);
impl<M> Widget<M, cosmic::Theme, cosmic::Renderer> for Isolated<'_, M> {
    fn size(&self) -> Size<Length> { self.0.as_widget().size() }
    fn size_hint(&self) -> Size<Length> { self.0.as_widget().size_hint() }
    fn tag(&self) -> tree::Tag { self.0.as_widget().tag() }
    fn state(&self) -> tree::State { self.0.as_widget().state() }
    fn children(&self) -> Vec<Tree> { self.0.as_widget().children() }
    fn diff(&mut self, tree: &mut Tree) { self.0.as_widget_mut().diff(tree); }
    fn layout(&mut self, tree: &mut Tree, renderer: &cosmic::Renderer,
        limits: &layout::Limits) -> layout::Node {
        self.0.as_widget_mut().layout(tree, renderer, limits)
    }
    fn operate(&mut self, tree: &mut Tree, layout: Layout<'_>, renderer: &cosmic::Renderer,
        operation: &mut dyn Operation) {
        self.0.as_widget_mut().operate(tree, layout, renderer, operation);
    }
    fn update(&mut self, tree: &mut Tree, event: &Event, layout: Layout<'_>, cursor: mouse::Cursor,
        renderer: &cosmic::Renderer, clipboard: &mut dyn Clipboard, shell: &mut Shell<'_, M>,
        viewport: &Rectangle) {
        // Refuse BEFORE content/SDK handling. No state mutation, publish, synthetic
        // pointer event, focus reset, ordinary Program update or task scheduling.
        // Enter/Space (including repeats/releases), Escape/Tab/modifiers are inert
        // here until a separate live client-keyboard dispatcher is established.
        if matches!(event, Event::Keyboard(_)) { return; }
        self.0.as_widget_mut().update(tree, event, layout, cursor, renderer, clipboard, shell, viewport);
    }
    fn draw(&self, tree: &Tree, renderer: &mut cosmic::Renderer, theme: &cosmic::Theme,
        style: &renderer::Style, layout: Layout<'_>, cursor: mouse::Cursor, viewport: &Rectangle) {
        self.0.as_widget().draw(tree, renderer, theme, style, layout, cursor, viewport);
    }
    fn mouse_interaction(&self, tree: &Tree, layout: Layout<'_>, cursor: mouse::Cursor,
        viewport: &Rectangle, renderer: &cosmic::Renderer) -> mouse::Interaction {
        self.0.as_widget().mouse_interaction(tree, layout, cursor, viewport, renderer)
    }
    fn overlay<'a>(&'a mut self, tree: &'a mut Tree, layout: Layout<'a>, renderer: &cosmic::Renderer,
        viewport: &Rectangle, translation: Vector) -> Option<overlay::Element<'a, M, cosmic::Theme, cosmic::Renderer>> {
        self.0.as_widget_mut().overlay(tree, layout, renderer, viewport, translation)
    }
    fn id(&self) -> Option<Id> { self.0.as_widget().id() }
    fn set_id(&mut self, id: Id) { self.0.as_widget_mut().set_id(id); }
    fn drag_destinations(&self, tree: &Tree, layout: Layout<'_>, renderer: &cosmic::Renderer,
        rectangles: &mut core::clipboard::DndDestinationRectangles) {
        self.0.as_widget().drag_destinations(tree, layout, renderer, rectangles);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use super::super::{OverflowButton, Message};
    use crate::iced::Program;
    use cosmic::iced::{Font, Pixels, Point, keyboard::{self, Key, Location, Modifiers, key::Named}};
    use std::{borrow::Cow, sync::{Arc, atomic::AtomicBool}};

    struct Probe { program: OverflowButton, tree: Tree, node: layout::Node, renderer: cosmic::Renderer }
    impl Probe {
        fn new(focused: bool) -> Self {
            let program = OverflowButton::new(Id::unique(), smithay::utils::Point::from((0,0)),
                20, cosmic::iced::Padding::from(0), Arc::new(AtomicBool::new(false)),
                Cow::Borrowed("view-more-symbolic"), 1);
            let renderer = cosmic::Renderer::new(Font::default(), Pixels(16.0));
            let (tree, node) = {
                let mut element = program.view();
                let mut tree = Tree::new(element.as_widget());
                let node = element.as_widget_mut().layout(&mut tree, &renderer,
                    &layout::Limits::new(Size::ZERO, Size::new(80.0,80.0)));
                if focused { element.as_widget_mut().operate(&mut tree, Layout::new(&node), &renderer,
                    &mut core::widget::operation::focusable::focus::<()>(program.id.clone())); }
                (tree, node)
            };
            Self { program, tree, node, renderer }
        }
        fn event(&mut self, event: Event) -> Vec<Message> {
            // Actual OverflowButton::view, reconstructed like ordinary cached UI.
            let mut element = self.program.view();
            self.tree.diff(element.as_widget_mut());
            let mut messages = Vec::new();
            element.as_widget_mut().update(&mut self.tree, &event, Layout::new(&self.node),
                mouse::Cursor::Available(Point::new(5.0,5.0)), &self.renderer,
                &mut core::clipboard::Null, &mut Shell::new(&mut messages),
                &Rectangle::with_size(Size::new(80.0,80.0)));
            messages
        }
        fn unfocus(&mut self) {
            self.program.view().as_widget_mut().operate(&mut self.tree, Layout::new(&self.node),
                &self.renderer, &mut core::widget::operation::focusable::unfocus::<()>());
        }
    }
    fn press(key: Key, repeat: bool) -> Event {
        Event::Keyboard(keyboard::Event::KeyPressed { key: key.clone(), modified_key: key,
            physical_key: keyboard::key::Physical::Unidentified(keyboard::key::NativeCode::Unidentified),
            location: Location::Standard, modifiers: Modifiers::empty(), text: None, repeat })
    }
    fn release(key: Key) -> Event {
        Event::Keyboard(keyboard::Event::KeyReleased { key: key.clone(), modified_key: key,
            physical_key: keyboard::key::Physical::Unidentified(keyboard::key::NativeCode::Unidentified),
            location: Location::Standard, modifiers: Modifiers::empty() })
    }
    fn enter() -> Key { Key::Named(Named::Enter) }
    fn space() -> Key { Key::Character(" ".into()) }
    fn down() -> Event { Event::Mouse(mouse::Event::ButtonPressed(mouse::Button::Left)) }
    fn up() -> Event { Event::Mouse(mouse::Event::ButtonReleased(mouse::Button::Left)) }
    fn toggle(messages: Vec<Message>) { assert!(matches!(messages.as_slice(), [Message::TogglePopup])); }
    #[test] fn overflow_view_keyboard_never_arms_pointer() {
        let mut p=Probe::new(true);
        for key in [enter(),space(),Key::Named(Named::Escape),Key::Named(Named::Tab)] {
            assert!(p.event(press(key.clone(),false)).is_empty());
            assert!(p.event(press(key.clone(),true)).is_empty());
            assert!(p.event(release(key)).is_empty());
        }
        assert!(p.event(up()).is_empty());
    }
    #[test] fn overflow_view_unfocused_keyboard_is_inert() {
        let mut p=Probe::new(false);assert!(p.event(press(enter(),false)).is_empty());
        assert!(p.event(up()).is_empty());
    }
    #[test] fn overflow_view_real_pointer_click_survives() {
        let mut p=Probe::new(true);assert!(p.event(down()).is_empty());toggle(p.event(up()));
        assert!(p.event(up()).is_empty());
    }
    #[test] fn overflow_view_pointer_down_enter_repeat_release_survives() {
        let mut p=Probe::new(true);assert!(p.event(down()).is_empty());
        for event in [press(enter(),false),press(enter(),true),release(enter())] { assert!(p.event(event).is_empty()); }
        toggle(p.event(up()));assert!(p.event(up()).is_empty());
    }
    #[test] fn overflow_view_pointer_down_space_unfocus_release_survives() {
        let mut p=Probe::new(true);assert!(p.event(down()).is_empty());
        assert!(p.event(press(space(),false)).is_empty());p.unfocus();
        assert!(p.event(release(space())).is_empty());toggle(p.event(up()));
    }
    #[test] fn overflow_view_keyboard_then_unfocus_no_pointer_down_no_output() {
        let mut p=Probe::new(true);assert!(p.event(press(enter(),false)).is_empty());p.unfocus();
        assert!(p.event(release(enter())).is_empty());assert!(p.event(up()).is_empty());
    }
    #[test] fn overflow_view_real_cursor_leave_still_cancels_pointer() {
        let mut p=Probe::new(true);assert!(p.event(down()).is_empty());
        assert!(p.event(press(enter(),false)).is_empty());
        assert!(p.event(Event::Mouse(mouse::Event::CursorLeft)).is_empty());assert!(p.event(up()).is_empty());
    }
    #[test] fn overflow_view_focus_id_and_pointer_interaction_delegated() {
        let p=Probe::new(true);let element=p.program.view();assert_eq!(element.as_widget().id(),Some(p.program.id.clone()));
        assert_eq!(element.as_widget().mouse_interaction(&p.tree,Layout::new(&p.node),
            mouse::Cursor::Available(Point::new(5.0,5.0)), &Rectangle::with_size(Size::new(80.0,80.0)),
            &p.renderer),mouse::Interaction::Pointer);
    }
}
