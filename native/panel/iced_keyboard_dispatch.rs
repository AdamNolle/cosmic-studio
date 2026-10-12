// SPDX-License-Identifier: GPL-3.0-only
// Explicit single-event widget/message boundary, not native callback admission.
use super::{State, Program, build_user_interface};
use crate::xdg_shell_wrapper::client_state::client_iced_event::Converted;
use cosmic::iced::core::{id, event, Event, Size, mouse, renderer, Clipboard};
use cosmic::iced::runtime::{Task, user_interface};

#[derive(Debug, PartialEq, Eq)]
pub(crate) enum KeyboardDispatchError { Busy, InvalidContext }

impl<P: Program + 'static> State<P> {
    // No implicit Program::update fallback. Caller must independently validate
    // live client keyboard/seat/focus/target/modifiers/order/press/grab, outside
    // Smithay keyboard locks, then supply a keyboard-only message dispatcher.
    // Neither conversion nor this method grants popup authority. Task outputs
    // do NOT inherit this context and must remain untrusted ordinary messages.
    pub(crate) fn update_keyboard<O>(
        &mut self,
        context: &Converted<O>,
        id: id::Id,
        bounds: Size,
        cursor: mouse::Cursor,
        renderer: &mut cosmic::Renderer,
        theme: &cosmic::Theme,
        style: &renderer::Style,
        clipboard: &mut dyn Clipboard,
        mut validate: impl FnMut(&Converted<O>) -> bool,
        mut dispatch: impl FnMut(&mut P, P::Message, &Converted<O>) -> Task<P::Message>,
    ) -> Result<(event::Status, Task<P::Message>, usize), KeyboardDispatchError> {
        // Never flush/relabel preexisting pointer/window/task/keyboard work.
        // Refusal leaves the cache and queues untouched, with no widget calls.
        if !self.is_queue_empty() { return Err(KeyboardDispatchError::Busy); }
        if !validate(context) { return Err(KeyboardDispatchError::InvalidContext); }
        let mut ui = build_user_interface(id.clone(), &mut self.program,
            self.cache.take().unwrap(), renderer, bounds);
        let mut messages = Vec::new();
        // Event and provenance cannot be independently supplied/mismatched.
        let event = Event::Keyboard(context.iced().clone());
        let (state, statuses) = ui.update(std::slice::from_ref(&event), cursor,
            renderer, clipboard, &mut messages);
        let status = statuses.into_iter().next().unwrap_or(event::Status::Ignored);
        let cache = ui.into_cache();
        let mut rejected = 0;
        let mut tasks = Vec::new();
        for message in messages {
            // Recheck each output, not only conversion/initial event. A previous
            // dispatch may retire focus. No transactional rollback is claimed.
            if validate(context) { tasks.push(dispatch(&mut self.program, message, context)); }
            else { rejected += 1; }
        }
        if let user_interface::State::Updated { mouse_interaction, .. } = state {
            self.mouse_interaction = mouse_interaction;
        }
        let mut ui = build_user_interface(id, &mut self.program, cache, renderer, bounds);
        ui.draw(renderer, theme, style, cursor);
        self.cache = Some(ui.into_cache());
        Ok((status, Task::batch(tasks), rejected))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use cosmic::iced::{Font, Pixels, Length};
    use cosmic::iced::core::{widget::{Widget, Tree}, layout, Layout, Rectangle, Shell};
    use crate::xdg_shell_wrapper::client_state::{client_iced_event::{self, Context},
        client_keymap::ClientKeymap, keyboard_event_context::Kind};
    use sctk::seat::keyboard::{KeyEvent, Modifiers, RawModifiers};
    use smithay::input::keyboard::xkb;
    use std::{cell::Cell, rc::Rc};

    // Real Iced Widget/UI/cache/renderer path; synthetic events, not WlSeat input.
    struct Emitter;
    impl Widget<u8, cosmic::Theme, cosmic::Renderer> for Emitter {
        fn size(&self) -> Size<Length> { Size::new(Length::Fixed(20.0), Length::Fixed(20.0)) }
        fn layout(&mut self, _: &mut Tree, _: &cosmic::Renderer, _: &layout::Limits) -> layout::Node {
            layout::Node::new(Size::new(20.0, 20.0))
        }
        fn update(&mut self, _: &mut Tree, event: &Event, _: Layout<'_>, _: mouse::Cursor,
            _: &cosmic::Renderer, _: &mut dyn Clipboard, shell: &mut Shell<'_, u8>, _: &Rectangle) {
            if matches!(event, Event::Keyboard(_)) {
                shell.publish(1);shell.publish(2);shell.capture_event();
            }
        }
        fn draw(&self, _: &Tree, _: &mut cosmic::Renderer, _: &cosmic::Theme,
            _: &renderer::Style, _: Layout<'_>, _: mouse::Cursor, _: &Rectangle) {}
    }
    struct TestProgram { ordinary: Vec<u8>, attributed: Vec<(u8, &'static str, u32, u32, Kind, Option<String>)> }
    impl Program for TestProgram {
        type Message = u8;
        fn update(&mut self, message: u8) -> Task<u8> { self.ordinary.push(message);Task::none() }
        fn view(&self) -> cosmic::iced::Element<'_, u8, cosmic::Theme, cosmic::Renderer> {
            cosmic::iced::Element::new(Emitter)
        }
    }
    fn converted(kind: Kind, text: Option<&str>, seat: &'static str) -> client_iced_event::Converted<&'static str> {
        let mut map = ClientKeymap::default();
        map.replace(r#"xkb_keymap {
            xkb_keycodes { minimum = 8; maximum = 255; <TEST> = 38; <CTRL> = 37; };
            xkb_types { type "ONE" { modifiers = none; map[None] = Level1; }; };
            xkb_compatibility { };
            xkb_symbols { key <TEST> { type="ONE", [ a ] }; key <CTRL> { [ Control_L ] };
                modifier_map Control { <CTRL> }; };
        };"#.into());
        let mut ctx = Context::new(seat);ctx.enter();
        ctx.set_modifiers(0, Modifiers::default(), RawModifiers::default(), 0);
        let frame = ctx.capture(kind, u32::MAX, KeyEvent { time: 0, raw_code: 30,
            keysym: xkb::Keysym::new(xkb::keysyms::KEY_a), utf8: text.map(Into::into) }).unwrap();
        client_iced_event::convert(&map, &ctx, &frame).unwrap()
    }
    fn setup() -> (State<TestProgram>, cosmic::Renderer) {
        let mut renderer = cosmic::Renderer::new(Font::default(), Pixels(16.0));
        let state = State::new(id::Id::new("test"), TestProgram { ordinary: Vec::new(), attributed: Vec::new() },
            Size::new(40.0,40.0), &mut renderer);
        (state, renderer)
    }
    fn dispatch(program: &mut TestProgram, message: u8, context: &Converted<&'static str>) -> Task<u8> {
        let frame = context.original();
        program.attributed.push((message, *frame.origin(), frame.serial(), frame.event().time,
            frame.kind(), frame.event().utf8.clone()));Task::done(9)
    }
    fn run(state: &mut State<TestProgram>, renderer: &mut cosmic::Renderer, context: &Converted<&'static str>,
        validate: impl FnMut(&Converted<&'static str>) -> bool,
        dispatcher: impl FnMut(&mut TestProgram, u8, &Converted<&'static str>) -> Task<u8>)
        -> Result<(event::Status, Task<u8>, usize), KeyboardDispatchError> {
        state.update_keyboard(context, id::Id::new("test"), Size::new(40.0,40.0), mouse::Cursor::Unavailable,
            renderer, &cosmic::Theme::default(), &renderer::Style { scale_factor: 1.0, icon_color: cosmic::iced::Color::WHITE, text_color: cosmic::iced::Color::WHITE },
            &mut cosmic::iced::core::clipboard::Null, validate, dispatcher)
    }
    #[test]
    fn each_real_widget_message_retains_same_original_envelope_without_plain_update() {
        let (mut state, mut renderer) = setup();let ctx = converted(Kind::Press, Some("é🦀"), "Seat0");
        let (status, _, rejected) = run(&mut state, &mut renderer, &ctx, |_| true, dispatch).unwrap();
        assert_eq!(status,event::Status::Captured);assert_eq!(rejected,0);
        assert_eq!(state.program.attributed, vec![(1,"Seat0",u32::MAX,0,Kind::Press,Some("é🦀".into())),
            (2,"Seat0",u32::MAX,0,Kind::Press,Some("é🦀".into()))]);
        assert!(state.program.ordinary.is_empty());assert!(state.is_queue_empty());assert!(state.cache.is_some());
    }
    #[test]
    fn queued_pointer_window_and_task_work_refuses_without_relabel_or_flush() {
        for event in [None, Some(Event::Mouse(mouse::Event::CursorLeft)), Some(Event::Window(cosmic::iced::window::Event::Focused))] {
            let (mut state,mut renderer)=setup();let ctx=converted(Kind::Press,None,"seat");
            if let Some(event)=event { state.queue_event(event); } else { state.queue_message(7); }
            let before_events=state.queued_events.clone();let before_messages=state.queued_messages.clone();
            let result=run(&mut state,&mut renderer,&ctx, |_| panic!("busy path validated"),dispatch);
            assert!(matches!(result,Err(KeyboardDispatchError::Busy)));
            assert_eq!(state.queued_events,before_events);assert_eq!(state.queued_messages,before_messages);
            assert!(state.cache.is_some());assert!(state.program.attributed.is_empty());assert!(state.program.ordinary.is_empty());
        }
    }
    #[test]
    fn invalid_entry_does_not_touch_widgets_queues_or_program() {
        let (mut state,mut renderer)=setup();let ctx=converted(Kind::Press,None,"seat");
        assert!(matches!(run(&mut state,&mut renderer,&ctx, |_| false,dispatch),Err(KeyboardDispatchError::InvalidContext)));
        assert!(state.cache.is_some());assert!(state.is_queue_empty());assert!(state.program.attributed.is_empty());
    }
    #[test]
    fn each_output_revalidates_and_retired_second_message_is_not_dispatched() {
        let (mut state,mut renderer)=setup();let ctx=converted(Kind::Press,None,"seat");
        let live=Rc::new(Cell::new(true));let check=live.clone();let retire=live.clone();
        let (_,_,rejected)=run(&mut state,&mut renderer,&ctx, move |_|check.get(), move |p,m,c| {
            let task=dispatch(p,m,c);retire.set(false);task
        }).unwrap();
        assert_eq!(rejected,1);assert_eq!(state.program.attributed.len(),1);assert_eq!(state.program.attributed[0].0,1);
        assert!(state.program.ordinary.is_empty());
    }
    #[test]
    fn release_repeat_and_none_empty_text_are_original_not_new_presses() {
        for kind in [Kind::Release,Kind::Repeat] { for text in [None,Some("")] {
            let (mut state,mut renderer)=setup();let ctx=converted(kind,text,"seat");
            let _=run(&mut state,&mut renderer,&ctx, |_|true,dispatch).unwrap();
            assert_eq!(state.program.attributed[0].4,kind);assert_eq!(state.program.attributed[0].5.as_deref(),text);
        } }
    }
    #[test]
    fn successive_events_keep_distinct_origins_and_tasks_do_not_enter_attributed_queue() {
        let (mut state,mut renderer)=setup();
        for seat in ["Seat0","seat0"] { let ctx=converted(Kind::Press,None,seat);
            let _=run(&mut state,&mut renderer,&ctx, |_|true,dispatch).unwrap(); }
        assert_eq!(state.program.attributed.iter().map(|row|row.1).collect::<Vec<_>>(),vec!["Seat0","Seat0","seat0","seat0"]);
        assert!(state.queued_messages.is_empty());assert!(state.program.ordinary.is_empty());
        // Simulate ordinary scheduling of a returned task output: no inherited origin.
        state.queue_message(9);assert_eq!(state.queued_messages,vec![9]);
    }
}
