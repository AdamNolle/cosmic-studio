#!/usr/bin/env python3
"""Exact overflow isolation prerequisite plus native callback/press pairing."""
import argparse,difflib,importlib.util,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
PIN='b5cc19e351b82eed999097ced1ff267d27bf8e7a'
PREFIX='cosmic-panel-bin/src/xdg_shell_wrapper/'
MODULE=PREFIX+'client/client_keyboard_delivery.rs'
STATE=PREFIX+'client/state.rs'
KEYBOARD=PREFIX+'client/handlers/keyboard.rs'
SEAT=PREFIX+'client/handlers/seat.rs'

def prerequisite():
    spec=importlib.util.spec_from_file_location('delivery_prior',HERE/'prepare_overflow_keyboard_isolation.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def expected_inputs():
    prior=prerequisite();return prior.transform(prior.expected_inputs())

def once(text,old,new):
    if text.count(old)!=1:raise ValueError('Changed exact callback delivery seam.')
    return text.replace(old,new,1)

def transform(files):
    if files!=expected_inputs():raise ValueError('Changed exact isolation inputs; fresh tree required.')
    changed=dict(files)
    changed[STATE]=once(files[STATE],'#[derive(Debug)]\npub(crate) struct ClientSeat {',
        '#[path = "client_keyboard_delivery.rs"]\npub(crate) mod client_keyboard_delivery;\n\n#[derive(Debug)]\npub(crate) struct ClientSeat {')
    changed[STATE]=once(changed[STATE],'    pub(crate) keymap_source: client_keymap::ClientKeymap,',
        '    pub(crate) keymap_source: client_keymap::ClientKeymap,\n    pub(crate) key_delivery: Option<client_keyboard_delivery::Delivery<WlSeat>>,')
    text=files[SEAT];old='                    _seat: seat.clone(),'
    if text.count(old)!=2:raise ValueError('Changed exact delivery constructors.')
    text=text.replace(old,old+'\n                    key_delivery: None,')
    old='sp.client.key_events.invalidate();'
    if text.count(old)!=2:raise ValueError('Changed exact delivery capability invalidation.')
    text=text.replace(old,old+'\n                        sp.client.key_delivery = None;')
    changed[SEAT]=text
    text=files[KEYBOARD]
    text=once(text,'                seat.client.key_events.enter();','                seat.client.key_events.enter();\n                seat.client.key_delivery = None;')
    old='seat.client.key_events.invalidate();'
    if text.count(old)!=2:raise ValueError('Changed exact delivery focus/keymap invalidation.')
    text=text.replace(old,old+'\n                seat.client.key_delivery = None;')
    for kind,serial,event in [('Press','serial','event.clone()'),('Release','_serial','event.clone()'),('Repeat','_serial','_event')]:
        indent='                ' if kind!='Repeat' else '            '
        old=indent+'let _ = seat.client.key_events.capture(\n'+indent+'    crate::xdg_shell_wrapper::client_state::keyboard_event_context::Kind::'+kind+',\n'+indent+'    '+serial+', '+event+',\n'+indent+');'
        new=indent+'seat.client.key_delivery = crate::xdg_shell_wrapper::client_state::client_keyboard_delivery::capture(\n'+indent+'    &mut seat.client.key_input, &mut seat.client.key_events,\n'+indent+'    crate::xdg_shell_wrapper::client_state::keyboard_event_context::Kind::'+kind+',\n'+indent+'    '+serial+', '+event+',\n'+indent+');'
        text=once(text,old,new)
    text=once(text,'                let _ = seat.client.key_input.press(event.raw_code, serial, event.time);\n','')
    text=once(text,'                let _ = seat.client.key_input.release(event.raw_code);\n','')
    text=once(text,'                seat.client.key_events.set_modifiers(serial, modifiers, raw_modifiers, group);',
        '                seat.client.key_events.set_modifiers(serial, modifiers, raw_modifiers, group);\n                seat.client.key_delivery = None;')
    changed[KEYBOARD]=text
    changed[MODULE]=(HERE/'client_keyboard_delivery.rs').read_text(encoding='utf-8')
    return changed

def prepare(source,output,apply=False):
    source=Path(source);output=Path(output)
    if source.is_symlink() or any(p.is_symlink() for p in source.parents):raise ValueError('Symlink source forbidden.')
    source=source.resolve()
    if any(p in ('usr','opt','.cargo','.cache') for p in source.parts):raise ValueError('Use isolated sources, not installed files/caches.')
    if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=PIN:raise ValueError('Exact original panel HEAD required.')
    prior=prerequisite().prerequisite()
    original={**prior.load('prepare_keyboard_focus').originals(),**prior.load('prepare_keyboard_input').originals(),**prior.prerequisite().originals()}
    expected=expected_inputs();files={}
    for name,text in expected.items():
        path=source/name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.resolve().is_relative_to(source):raise ValueError('Symlink/escaped delivery source forbidden.')
        if name in original and subprocess.check_output(['git','-C',str(source),'show','HEAD:'+name])!=original[name].encode():raise ValueError('Original delivery Git blob differs.')
        if path.read_bytes()!=text.encode():raise ValueError('Changed exact delivery input; preserve tree.')
        files[name]=text
    path=source/MODULE
    if path.exists() or path.is_symlink() or any(p.is_symlink() for p in path.parents):raise ValueError('Existing/symlink delivery module refused; fresh tree required.')
    changed=transform(files)
    patch=''.join(''.join(difflib.unified_diff(expected.get(n,'').splitlines(True),t.splitlines(True),fromfile='a/'+n if n in expected else '/dev/null',tofile='b/'+n)) for n,t in changed.items())
    with output.open('x',encoding='utf-8',newline='\n') as stream:stream.write(patch)
    subprocess.run(['git','-C',str(source),'apply','--check',str(output.resolve())],check=True)
    if apply:
        subprocess.run(['git','-C',str(source),'apply',str(output.resolve())],check=True)
        if any((source/n).read_bytes()!=t.encode() for n,t in changed.items()):raise ValueError('Delivery postimage mismatch.')
    return changed

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source',type=Path);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--apply',action='store_true');args=parser.parse_args();prepare(args.source,args.output,args.apply)
