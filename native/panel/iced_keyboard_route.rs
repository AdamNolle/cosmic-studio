// SPDX-License-Identifier: GPL-3.0-only
// Actual IcedElement wrapper route. Caller admission remains mandatory.
use super::*;
use crate::xdg_shell_wrapper::client_state::client_iced_event::Converted;
use std::sync::mpsc::TryRecvError;

// A readiness probe must not discard None, reorder Some, or attribute task
// output to a keyboard event. Ordinary update consumes the same staged item.
pub(super) struct TaskInbox<M> {
    receiver: Receiver<Option<M>>,
    staged: Option<Option<M>>,
}
impl<M> fmt::Debug for TaskInbox<M> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("TaskInbox").field("pending", &self.staged.is_some()).finish_non_exhaustive()
    }
}
impl<M> From<Receiver<Option<M>>> for TaskInbox<M> {
    fn from(receiver: Receiver<Option<M>>) -> Self { Self { receiver, staged: None } }
}
impl<M> TaskInbox<M> {
    fn has_pending(&mut self) -> bool {
        if self.staged.is_none() {
            self.staged = self.receiver.try_recv().ok();
        }
        self.staged.is_some()
    }
    pub(super) fn try_recv(&mut self) -> Result<Option<M>, TryRecvError> {
        match self.staged.take() { Some(output) => Ok(output), None => self.receiver.try_recv() }
    }
}

#[derive(Debug, PartialEq, Eq)]
pub(crate) enum WrapperKeyboardError { Busy, InvalidContext }

impl<P: Program + Send + 'static> IcedElement<P> {
    // This MUST be called outside Smithay's filter/target keyboard callbacks.
    // The mandatory validator supplies live originating WlKeyboard/WlSeat,
    // admitted target/focus/modifier/order/press/grab checks; this API does not.
    // No default Program::update, pointer serial or implicit deferred authority.
    // Validator/dispatcher run under this element's mutex: do not re-enter the
    // element or synchronously change focus through a callback that locks it.
    pub(crate) fn update_keyboard<O>(
        &self,
        context: &Converted<O>,
        validate: impl FnMut(&Converted<O>) -> bool,
        mut dispatch: impl FnMut(&mut P, P::Message, &Converted<O>) -> Task<P::Message>,
    ) -> Result<(iced::event::Status, usize), WrapperKeyboardError> {
        let mut guard = self.0.lock().unwrap();
        let internal = &mut *guard;
        if !internal.state.is_queue_empty() || internal.rx.has_pending() {
            return Err(WrapperKeyboardError::Busy);
        }
        // No ordinary update/flush: cached widget processing is one event only.
        let cursor = internal.cursor_pos
            .map(|p| IcedPoint::new(p.x as f32, p.y as f32))
            .map(Cursor::Available).unwrap_or(Cursor::Unavailable);
        let result = internal.state.update_keyboard(
            context, ID.clone(), IcedSize::new(internal.size.w as f32, internal.size.h as f32),
            cursor, &mut internal.renderer, &internal.theme,
            &Style { scale_factor: 1.0, icon_color: internal.theme.cosmic().on_bg_color().into(),
                text_color: internal.theme.cosmic().on_bg_color().into() },
            &mut NullClipboard, validate,
            |program, message, original| dispatch(&mut program.0, message, original),
        ).map_err(|error| match error {
            state::keyboard_dispatch::KeyboardDispatchError::Busy => WrapperKeyboardError::Busy,
            state::keyboard_dispatch::KeyboardDispatchError::InvalidContext => WrapperKeyboardError::InvalidContext,
        })?;
        let (status, task, rejected) = result;
        // Returned tasks have no keyboard provenance. Preserve original executor
        // behavior: eventual output is ordinary untrusted work via this inbox.
        if let Some(stream) = into_stream(task) {
            let _ = internal.scheduler.schedule(stream.into_future().map(|f| match f.0 {
                Some(Action::Output(message)) => Some(message), _ => None,
            }));
        }
        if internal.request_redraws {
            internal.pending_update = Some(Instant::now());
            let panel_id = internal.panel_id;
            internal.handle.insert_idle(move |state| state.space.iced_request_redraw(panel_id));
        }
        Ok((status, rejected))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use cosmic::iced::core::{widget::{Widget, Tree}, layout, Layout, Rectangle as IcedRectangle,
        Shell, mouse, renderer, Clipboard};
    use crate::xdg_shell_wrapper::client_state::{client_iced_event::{self, Context},
        client_keymap::ClientKeymap, keyboard_event_context::Kind};
    use sctk::seat::keyboard::{KeyEvent, Modifiers, RawModifiers};
    use smithay::input::keyboard::xkb;
    use std::{cell::Cell, rc::Rc};

    struct Emitter;
    impl Widget<u8, cosmic::Theme, cosmic::Renderer> for Emitter {
        fn size(&self) -> IcedSize<Length> { IcedSize::new(Length::Fixed(20.0), Length::Fixed(20.0)) }
        fn layout(&mut self, _: &mut Tree, _: &cosmic::Renderer, _: &layout::Limits) -> layout::Node {
            layout::Node::new(IcedSize::new(20.0,20.0))
        }
        fn update(&mut self, _: &mut Tree, event: &Event, _: Layout<'_>, _: mouse::Cursor,
            _: &cosmic::Renderer, _: &mut dyn Clipboard, shell: &mut Shell<'_,u8>, _: &IcedRectangle) {
            if matches!(event,Event::Keyboard(_)) { shell.publish(1);shell.publish(2);shell.capture_event(); }
        }
        fn draw(&self, _: &Tree, _: &mut cosmic::Renderer, _: &cosmic::Theme, _: &renderer::Style,
            _: Layout<'_>, _: mouse::Cursor, _: &IcedRectangle) {}
    }
    #[derive(Default)]
    struct TestProgram { ordinary: Vec<u8>, attributed: Vec<(u8,&'static str,u32,Kind,Option<String>)> }
    impl Program for TestProgram {
        type Message=u8;
        fn update(&mut self,message:u8,_:&LoopHandle<'static,GlobalState>)->Task<u8> {
            self.ordinary.push(message);Task::none()
        }
        fn view(&self)->Element<'_,u8> { Element::new(Emitter) }
    }
    fn setup()->(IcedElement<TestProgram>,calloop::EventLoop<'static,GlobalState>) {
        let event_loop=calloop::EventLoop::try_new().unwrap();
        let element=IcedElement::new(TestProgram::default(),Size::from((40,40)),event_loop.handle(),
            cosmic::Theme::default(),0,false);
        (element,event_loop)
    }
    fn context(kind:Kind,text:Option<&str>,origin:&'static str)->Converted<&'static str> {
        let mut map=ClientKeymap::default();map.replace(r#"xkb_keymap {
            xkb_keycodes { minimum = 8; maximum = 255; <TEST> = 38; <CTRL> = 37; };
            xkb_types { type "ONE" { modifiers = none; map[None] = Level1; }; };
            xkb_compatibility { };
            xkb_symbols { key <TEST> { type="ONE", [ a ] }; key <CTRL> { [ Control_L ] };
                modifier_map Control { <CTRL> }; };
        };"#.into());
        let mut ctx=Context::new(origin);ctx.enter();ctx.set_modifiers(0,Modifiers::default(),RawModifiers::default(),0);
        let frame=ctx.capture(kind,u32::MAX,KeyEvent { time:0,raw_code:30,
            keysym:xkb::Keysym::new(xkb::keysyms::KEY_a),utf8:text.map(Into::into) }).unwrap();
        client_iced_event::convert(&map,&ctx,&frame).unwrap()
    }
    fn dispatch(p:&mut TestProgram,m:u8,c:&Converted<&'static str>)->Task<u8> {
        let f=c.original();p.attributed.push((m,*f.origin(),f.serial(),f.kind(),f.event().utf8.clone()));Task::none()
    }
    #[test]
    fn inbox_probe_retains_none_and_all_output_order() {
        let (tx,rx)=std::sync::mpsc::channel();let mut inbox:TaskInbox<u8>=rx.into();
        tx.send(None).unwrap();tx.send(Some(7)).unwrap();tx.send(Some(8)).unwrap();
        assert!(inbox.has_pending());assert!(inbox.has_pending());assert_eq!(inbox.try_recv(),Ok(None));
        assert!(inbox.has_pending());
        assert_eq!(format!("{:?}",inbox),"TaskInbox { pending: true, .. }");
        assert_eq!(inbox.try_recv(),Ok(Some(7)));
        assert_eq!(inbox.try_recv(),Ok(Some(8)));assert!(!inbox.has_pending());
        drop(tx);assert!(!inbox.has_pending());assert_eq!(inbox.try_recv(),Err(TryRecvError::Disconnected));
    }
    #[test]
    fn real_wrapper_busy_task_does_not_validate_flush_or_attribute() {
        for output in [None,Some(7)] {
            let (element,_loop)=setup();let (tx,rx)=std::sync::mpsc::channel();
            element.0.lock().unwrap().rx=rx.into();tx.send(output).unwrap();
            let c=context(Kind::Press,None,"seat");
            for _ in 0..2 { assert_eq!(element.update_keyboard(&c, |_|panic!("busy validated"),dispatch),Err(WrapperKeyboardError::Busy)); }
            element.with_program(|p| {assert!(p.ordinary.is_empty());assert!(p.attributed.is_empty());});
            // Same ordinary update consumes the staged item, not a keyboard route.
            element.force_update();element.with_program(|p|assert_eq!(p.ordinary,output.into_iter().collect::<Vec<_>>()));
            assert!(element.0.lock().unwrap().state.is_queue_empty());
        }
    }
    #[test]
    fn real_wrapper_busy_state_preserves_receiver_and_queued_pointer_work() {
        let (element,_loop)=setup();let (tx,rx)=std::sync::mpsc::channel();
        { let mut i=element.0.lock().unwrap();i.rx=rx.into();i.state.queue_event(Event::Mouse(MouseEvent::CursorLeft)); }
        tx.send(Some(7)).unwrap();let c=context(Kind::Press,None,"seat");
        assert_eq!(element.update_keyboard(&c, |_|panic!("busy validated"),dispatch),Err(WrapperKeyboardError::Busy));
        let mut i=element.0.lock().unwrap();assert!(i.rx.staged.is_none());assert!(!i.state.is_queue_empty());
        assert_eq!(i.rx.try_recv(),Ok(Some(7)));
    }
    #[test]
    fn real_wrapper_explicit_outputs_revalidate_original_envelope() {
        let (element,_loop)=setup();let c=context(Kind::Press,Some("é🦀"),"Seat0");
        let live=Rc::new(Cell::new(true));let check=live.clone();let retire=live.clone();
        let (status,rejected)=element.update_keyboard(&c,move |_|check.get(),move |p,m,c| {
            let task=dispatch(p,m,c);retire.set(false);task
        }).unwrap();assert_eq!(status,iced::event::Status::Captured);assert_eq!(rejected,1);
        element.with_program(|p| { assert!(p.ordinary.is_empty());assert_eq!(p.attributed,
            vec![(1,"Seat0",u32::MAX,Kind::Press,Some("é🦀".into()))]); });
    }
    #[test]
    fn real_wrapper_invalid_context_and_release_repeat_remain_distinct() {
        let (element,_loop)=setup();let c=context(Kind::Press,None,"seat0");
        assert_eq!(element.update_keyboard(&c, |_|false,dispatch),Err(WrapperKeyboardError::InvalidContext));
        element.with_program(|p|assert!(p.attributed.is_empty()));
        for kind in [Kind::Release,Kind::Repeat] { for text in [None,Some("")] {
            let c=context(kind,text,"seat0");element.update_keyboard(&c, |_|true,dispatch).unwrap();
        } }
        element.with_program(|p| {assert!(p.ordinary.is_empty());assert_eq!(p.attributed.len(),8);
            for (index,kind) in [Kind::Release,Kind::Repeat].into_iter().enumerate() {
                assert_eq!(p.attributed[index*4].3,kind);assert_eq!(p.attributed[index*4].4,None);
                assert_eq!(p.attributed[index*4+2].4,Some(String::new()));
            }
        });
    }
    #[test]
    fn later_task_output_is_ordinary_and_blocks_next_keyboard_route() {
        let (element,_loop)=setup();let c=context(Kind::Press,None,"seat0");
        element.update_keyboard(&c, |_|true,dispatch).unwrap();
        let (tx,rx)=std::sync::mpsc::channel();element.0.lock().unwrap().rx=rx.into();
        // Models executor delivery, not live event-loop/Wayland scheduling.
        tx.send(Some(9)).unwrap();
        assert_eq!(element.update_keyboard(&c, |_|panic!("task output validated"),dispatch),Err(WrapperKeyboardError::Busy));
        element.force_update();element.with_program(|p|{assert_eq!(p.ordinary,vec![9]);assert_eq!(p.attributed.len(),2);});
    }
}
