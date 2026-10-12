#!/usr/bin/env python3
"""Exact original GPL panel focus bridge; not key conversion or manual hiding."""
import argparse,difflib,gzip,hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
PIN='b5cc19e351b82eed999097ced1ff267d27bf8e7a'
FIXTURE_SHA='48a0eb2b2c1b7c7870c0cfebe21576b6158814016950974cba391cd8fdf60bf7'
PREFIX='cosmic-panel-bin/src/'
MODULE=PREFIX+'iced/keyboard_focus_seats.rs'

def originals():
    raw=(HERE/'pinned-keyboard-focus-sources.json.gz').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA:raise ValueError('Original focus fixture checksum differs.')
    return json.loads(gzip.decompress(raw))

def once(text,old,new):
    if text.count(old)!=1:raise ValueError('Changed exact native focus seam.')
    return text.replace(old,new,1)

def transform(files):
    original=originals()
    if files!=original:raise ValueError('Changed original focus inputs; prepare a fresh tree.')
    out=dict(files)
    name=PREFIX+'xdg_shell_wrapper/space/space.rs'
    out[name]=once(out[name],'    /// optionally returns a focused server wl surface','    /// optionally returns the existing native keyboard focus target')
    out[name]=once(out[name],'    ) -> Option<s_WlSurface>;','    ) -> Option<SpaceTarget>;')
    name=PREFIX+'space_container/wrapper_space.rs'
    out[name]=once(out[name],'    ) -> Option<wl_surface::WlSurface> {\n        if let Some((popup_space_i, popup_space))', '    ) -> Option<SpaceTarget> {\n        if let Some((popup_space_i, popup_space))')
    # Preserve original popup-first routing/drop and all leave/grab rules. Our panel
    # entry refuses active popups/grabs; do not invent cross-popup restoration.
    name=PREFIX+'xdg_shell_wrapper/client/handlers/keyboard.rs'
    out[name]=once(out[name],'kbd.set_focus(self, s.map(|s| s.into()), SERIAL_COUNTER.next_serial());','kbd.set_focus(self, s, SERIAL_COUNTER.next_serial());')
    name=PREFIX+'space/wrapper_space.rs'
    out[name]=once(out[name],'''    fn keyboard_enter(&mut self, _: &str, _: c_wl_surface::WlSurface) -> Option<s_WlSurface> {
        None
    }''','''    fn keyboard_enter(
        &mut self,
        seat_name: &str,
        surface: c_wl_surface::WlSurface,
    ) -> Option<SpaceTarget> {
        // An admitted outer-layer enter is NOT a global keyboard entry action.
        // Do not take a parent focus while any child/grabbing popup owns it.
        if !self.layer.as_ref().is_some_and(|l| l.wl_surface() == &surface)
            || !self.popups.is_empty()
            || self.overflow_popup.is_some()
        {
            return None;
        }
        let mut mapped = self.space.elements().filter_map(|element| {
            let location = self.space.element_location(element)?;
            let geometry = element.geometry();
            if geometry.size.w <= 0 || geometry.size.h <= 0 {
                return None;
            }
            let target = SpaceTarget::try_from(element.clone()).ok()?;
            Some((location.x, location.y, target))
        }).collect::<Vec<_>>();
        mapped.sort_by_key(|(x, y, _)| (*x, *y));
        // Preserve the same-seat surviving mapped target; never resurrect an
        // unmapped client/PID/index. Otherwise choose a real overflow anchor.
        let target = self.s_focused_surface.iter()
            .find(|(_, name)| name == seat_name)
            .and_then(|(target, _)| mapped.iter()
                .find(|(_, _, candidate)| candidate == target)
                .map(|(_, _, target)| target.clone()))
            .or_else(|| mapped.into_iter().find_map(|(_, _, target)| {
                matches!(&target, SpaceTarget::OverflowButton(_)).then_some(target)
            }))?;
        self.s_focused_surface.retain(|(_, name)| name != seat_name);
        self.s_focused_surface.push((target.clone(), seat_name.to_owned()));
        Some(target)
    }''')
    name=PREFIX+'iced/elements/overflow_button.rs'
    out[name]=once(out[name],'    type Message = Message;\n\n    fn update(','''    type Message = Message;

    fn keyboard_focus_id(&self) -> Option<id::Id> {
        Some(self.id.clone())
    }

    fn update(''')
    out[name]=once(out[name],'            .selected(self.selected.load(Ordering::Relaxed))','            .id(self.id.clone())\n            .selected(self.selected.load(Ordering::Relaxed))')
    name=PREFIX+'iced/mod.rs'
    out[name]=once(out[name],'pub mod elements;','mod keyboard_focus_seats;\npub mod elements;')
    out[name]=once(out[name],'''pub trait Program {
    type Message: std::fmt::Debug + Send;''','''pub trait Program {
    type Message: std::fmt::Debug + Send;

    // Only programs with a verified native focusable widget opt in.
    fn keyboard_focus_id(&self) -> Option<Id> {
        None
    }''')
    out[name]=once(out[name],'    // iced\n    theme: Theme,','    keyboard_focus_seats: keyboard_focus_seats::FocusSeats,\n\n    // iced\n    theme: Theme,')
    # Fresh/deep clones never inherit active native seat ownership.
    out[name]=out[name].replace('            last_touch_frame: None,','            last_touch_frame: None,\n            keyboard_focus_seats: keyboard_focus_seats::FocusSeats::default(),')
    if out[name].count('keyboard_focus_seats: keyboard_focus_seats::FocusSeats::default()')!=2:raise ValueError('Changed native focus constructors.')
    out[name]=once(out[name],'''impl<P: Program + Send + 'static> IcedElementInternal<P> {
    fn update(''','''impl<P: Program + Send + 'static> IcedElementInternal<P> {
    fn set_keyboard_widget_focus(&mut self, focused: bool) {
        let Some(widget_id) = self.state.program().0.keyboard_focus_id() else {
            return;
        };
        use cosmic::iced::core::widget::{Operation, operation::focusable};
        let operation: Box<dyn Operation> = if focused {
            Box::new(focusable::focus::<()>(widget_id))
        } else {
            Box::new(focusable::unfocus::<()>())
        };
        // Apply directly to the actual cached native tree. Returning a Widget
        // Task here is insufficient: the original executor consumes Output only.
        self.state.operate(
            ID.clone(),
            &mut self.renderer,
            std::iter::once(operation),
            IcedSize::new(self.size.w as f32, self.size.h as f32),
        );
        self.state.queue_event(Event::Window(if focused {
            WindowEvent::Focused
        } else {
            WindowEvent::Unfocused
        }));
        if self.request_redraws {
            self.pending_update = Some(Instant::now());
            let panel_id = self.panel_id;
            self.handle.insert_idle(move |state| state.space.iced_request_redraw(panel_id));
        }
        let _ = self.update(true);
    }

    fn update(''')
    out[name]=once(out[name],'''        _seat: &Seat<GlobalState>,
        _data: &mut GlobalState,
        _keys: Vec<KeysymHandle<'_>>,
        _serial: Serial,
    ) {
        // TODO convert keys
    }

    fn leave(&self, _seat: &Seat<GlobalState>, _data: &mut GlobalState, _serial: Serial) {
        // TODO remove all held keys
    }''','''        seat: &Seat<GlobalState>,
        _data: &mut GlobalState,
        _keys: Vec<KeysymHandle<'_>>,
        _serial: Serial,
    ) {
        let mut internal = self.0.lock().unwrap();
        if internal.keyboard_focus_seats.enter(&seat.name()) {
            internal.set_keyboard_widget_focus(true);
        }
        // Held-key/event conversion and activation remain a separate gate.
        // Do not activate an Enter/Space already held on native focus entry.
    }

    fn leave(&self, seat: &Seat<GlobalState>, _data: &mut GlobalState, _serial: Serial) {
        let mut internal = self.0.lock().unwrap();
        if internal.keyboard_focus_seats.leave(&seat.name()) {
            internal.set_keyboard_widget_focus(false);
        }
        // No new key events or popup activation are synthesized here.
    }''')
    out[MODULE]=(HERE/'keyboard_focus_seats.rs').read_text(encoding='utf-8')
    return out

def prepare(source,output,apply=False):
    source=Path(source);output=Path(output)
    if source.is_symlink() or any(p.is_symlink() for p in source.parents):raise ValueError('Symlink source forbidden.')
    source=source.resolve()
    if any(p in ('usr','opt','.cache','.cargo') for p in source.parts):raise ValueError('Use isolated source, not installed files/caches.')
    if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=PIN:raise ValueError('Exact original panel HEAD required.')
    original=originals()
    files={}
    for name,text in original.items():
        path=source/name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.resolve().is_relative_to(source):raise ValueError('Symlink/escaped focus source forbidden.')
        expected=text.encode('utf-8')
        if subprocess.check_output(['git','-C',str(source),'show','HEAD:'+name])!=expected or path.read_bytes()!=expected:raise ValueError('Changed original focus bytes; preserve tree.')
        files[name]=text
    path=source/MODULE
    if path.exists() or path.is_symlink() or any(p.is_symlink() for p in path.parents):raise ValueError('Existing/symlink focus module refused; fresh tree required.')
    changed=transform(files)
    patch=''.join(''.join(difflib.unified_diff(original.get(n,'').splitlines(True),t.splitlines(True),fromfile='a/'+n if n in original else '/dev/null',tofile='b/'+n)) for n,t in changed.items())
    with output.open('x',encoding='utf-8',newline='\n') as stream:stream.write(patch)
    subprocess.run(['git','-C',str(source),'apply','--check',str(output.resolve())],check=True)
    if apply:
        subprocess.run(['git','-C',str(source),'apply',str(output.resolve())],check=True)
        if any((source/n).read_bytes()!=t.encode('utf-8') for n,t in changed.items()):raise ValueError('Native focus postimage mismatch.')
    return changed

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source',type=Path);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--apply',action='store_true');args=parser.parse_args();prepare(args.source,args.output,args.apply)
