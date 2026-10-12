#!/usr/bin/env python3
"""Exact client event-context prerequisite; no XKB/Iced/popup conversion."""
import argparse,difflib,importlib.util,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
PIN='b5cc19e351b82eed999097ced1ff267d27bf8e7a'
PREFIX='cosmic-panel-bin/src/xdg_shell_wrapper/'
MODULE=PREFIX+'client/keyboard_event_context.rs'
KEYBOARD=PREFIX+'client/handlers/keyboard.rs'

def prerequisite():
    spec=importlib.util.spec_from_file_location('input_prerequisite',HERE/'prepare_keyboard_input.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def expected_inputs():
    module=prerequisite()
    return module.transform(module.expected_inputs())

def once(text,old,new):
    if text.count(old)!=1:raise ValueError('Changed exact client event-context seam.')
    return text.replace(old,new,1)

def transform(files):
    if files!=expected_inputs():raise ValueError('Changed input-ledger prerequisite; use fresh tree.')
    changed=dict(files);state=PREFIX+'client/state.rs';seat=PREFIX+'client/handlers/seat.rs'
    changed[state]=once(changed[state],'pub(crate) mod keyboard_input_state;',
        'pub(crate) mod keyboard_input_state;\n#[path = "keyboard_event_context.rs"]\npub(crate) mod keyboard_event_context;')
    changed[state]=once(changed[state],'    pub(crate) key_input: keyboard_input_state::InputLedger<WlSeat>,',
        '    pub(crate) key_input: keyboard_input_state::InputLedger<WlSeat>,\n    pub(crate) key_events: keyboard_event_context::EventContext<\n        WlSeat,\n        sctk::seat::keyboard::KeyEvent,\n        sctk::seat::keyboard::Modifiers,\n        sctk::seat::keyboard::RawModifiers,\n    >,')
    old='                    key_input: crate::xdg_shell_wrapper::client_state::keyboard_input_state::InputLedger::new(seat.clone()),'
    if changed[seat].count(old)!=2:raise ValueError('Changed actual ClientSeat constructors.')
    changed[seat]=changed[seat].replace(old,old+'\n                    key_events: crate::xdg_shell_wrapper::client_state::keyboard_event_context::EventContext::new(seat.clone()),')
    old='sp.client.key_input.invalidate();'
    if changed[seat].count(old)!=2:raise ValueError('Changed actual keyboard capability/replacement invalidation.')
    changed[seat]='\n'.join(line+'\n'+line[:len(line)-len(line.lstrip())]+'sp.client.key_events.invalidate();' if line.strip()==old else line for line in changed[seat].split('\n'))
    text=changed[KEYBOARD]
    text=once(text,'seat.client.key_input.enter(_raw);','seat.client.key_input.enter(_raw);\n                seat.client.key_events.enter();')
    old='seat.client.key_input.invalidate();'
    if text.count(old)!=2:raise ValueError('Changed actual focus/keymap invalidation.')
    text=text.replace(old,old+'\n                seat.client.key_events.invalidate();')
    text=once(text,'let _ = seat.client.key_input.press(event.raw_code, serial, event.time);',
        'let _ = seat.client.key_input.press(event.raw_code, serial, event.time);\n                let _ = seat.client.key_events.capture(\n                    crate::xdg_shell_wrapper::client_state::keyboard_event_context::Kind::Press,\n                    serial, event.clone(),\n                );')
    text=once(text,'let _ = seat.client.key_input.release(event.raw_code);',
        'let _ = seat.client.key_input.release(event.raw_code);\n                let _ = seat.client.key_events.capture(\n                    crate::xdg_shell_wrapper::client_state::keyboard_event_context::Kind::Release,\n                    _serial, event.clone(),\n                );')
    start=text.index('    fn repeat_key(');end=text.index('    fn release_key(',start)
    block=text[start:end]
    block=once(block,'        // TODO',
        '        // Observe only an actual upstream callback; do not arm or forward\n        // another server key-down or invent text/repeat timing.\n        if let Some(seat) = self.server_state.seats.iter_mut().find(|seat| {\n            seat.client.kbd.as_ref().map(|kbd| kbd == _keyboard).unwrap_or(false)\n        }) {\n            let _ = seat.client.key_events.capture(\n                crate::xdg_shell_wrapper::client_state::keyboard_event_context::Kind::Repeat,\n                _serial, _event,\n            );\n        }')
    text=text[:start]+block+text[end:]
    start=text.index('    fn update_modifiers(');block=text[start:]
    block=once(block,'        _serial: u32,','        serial: u32,')
    block=once(block,'        _: RawModifiers,\n        _: u32,','        raw_modifiers: RawModifiers,\n        group: u32,')
    block=once(block,'            .iter()','            .iter_mut()')
    block=once(block,'.and_then(|seat| seat.server.seat.get_keyboard())',
        '.and_then(|seat| {\n                seat.client.key_events.set_modifiers(serial, modifiers, raw_modifiers, group);\n                seat.server.seat.get_keyboard()\n            })')
    text=text[:start]+block;changed[KEYBOARD]=text
    changed[MODULE]=(HERE/'keyboard_event_context.rs').read_text(encoding='utf-8')
    return changed

def prepare(source,output,apply=False):
    source=Path(source);output=Path(output)
    if source.is_symlink() or any(p.is_symlink() for p in source.parents):raise ValueError('Symlink source forbidden.')
    source=source.resolve()
    if any(p in ('usr','opt','.cargo','.cache') for p in source.parts):raise ValueError('Use isolated source, not installed files/caches.')
    if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=PIN:raise ValueError('Exact original panel HEAD required.')
    original=prerequisite().originals();expected=expected_inputs();files={}
    for name,text in expected.items():
        path=source/name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.resolve().is_relative_to(source):raise ValueError('Symlink/escaped event-context source forbidden.')
        if name in original and subprocess.check_output(['git','-C',str(source),'show','HEAD:'+name])!=original[name].encode():raise ValueError('Original event-context Git blob differs.')
        if path.read_bytes()!=text.encode():raise ValueError('Changed exact input prerequisite bytes; preserve tree.')
        files[name]=text
    path=source/MODULE
    if path.exists() or path.is_symlink() or any(p.is_symlink() for p in path.parents):raise ValueError('Existing/symlink context module refused; fresh tree required.')
    changed=transform(files)
    patch=''.join(''.join(difflib.unified_diff(expected.get(n,'').splitlines(True),t.splitlines(True),fromfile='a/'+n if n in expected else '/dev/null',tofile='b/'+n)) for n,t in changed.items())
    with output.open('x',encoding='utf-8',newline='\n') as stream:stream.write(patch)
    subprocess.run(['git','-C',str(source),'apply','--check',str(output.resolve())],check=True)
    if apply:
        subprocess.run(['git','-C',str(source),'apply',str(output.resolve())],check=True)
        if any((source/n).read_bytes()!=t.encode() for n,t in changed.items()):raise ValueError('Native event-context postimage mismatch.')
    return changed

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source',type=Path);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--apply',action='store_true');args=parser.parse_args();prepare(args.source,args.output,args.apply)
