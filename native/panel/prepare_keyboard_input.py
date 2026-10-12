#!/usr/bin/env python3
"""Exact native ClientSeat ledger prerequisite, not key conversion/activation."""
import argparse,difflib,gzip,hashlib,json,subprocess,importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
PIN='b5cc19e351b82eed999097ced1ff267d27bf8e7a'
FIXTURE_SHA='2854ab8b15cb8434a050a55a5e75f7393173d4729256efb6aa356f285d94ee57'
PREFIX='cosmic-panel-bin/src/xdg_shell_wrapper/'
MODULE=PREFIX+'client/keyboard_input_state.rs'
KEYBOARD=PREFIX+'client/handlers/keyboard.rs'

def originals():
    raw=(HERE/'pinned-keyboard-input-sources.json.gz').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA:raise ValueError('Original input fixture checksum differs.')
    return json.loads(gzip.decompress(raw))

def expected_inputs():
    files=originals()
    spec=importlib.util.spec_from_file_location('prerequisite_focus',HERE/'prepare_keyboard_focus.py')
    focus=importlib.util.module_from_spec(spec);spec.loader.exec_module(focus)
    files[KEYBOARD]=focus.transform(focus.originals())[KEYBOARD]
    return files

def once(text,old,new):
    if text.count(old)!=1:raise ValueError('Changed exact client input seam.')
    return text.replace(old,new,1)

def callback(text,name,next_name,statement):
    start=text.index('    fn '+name+'(');end=text.index('    fn '+next_name+'(',start)
    block=text[start:end]
    block=once(block,'            .iter()','            .iter_mut()')
    block=once(block,'.map(|seat| (seat.name.as_str(), seat.server.seat.get_keyboard()))',
        '.map(|seat| {\n                '+statement+'\n                (seat.name.as_str(), seat.server.seat.get_keyboard())\n            })')
    return text[:start]+block+text[end:]

def transform(files):
    if files!=expected_inputs():raise ValueError('Changed client input prerequisite; use fresh tree.')
    out=dict(files);state=PREFIX+'client/state.rs';seat=PREFIX+'client/handlers/seat.rs'
    out[state]=once(out[state],'#[derive(Debug)]\npub(crate) struct ClientSeat {',
        '#[path = "keyboard_input_state.rs"]\npub(crate) mod keyboard_input_state;\n\n#[derive(Debug)]\npub(crate) struct ClientSeat {')
    out[state]=once(out[state],'    pub(crate) last_key_press: (u32, u32),',
        '    pub(crate) last_key_press: (u32, u32),\n    pub(crate) key_input: keyboard_input_state::InputLedger<WlSeat>,')
    old='                    _seat: seat.clone(),'
    if out[seat].count(old)!=2:raise ValueError('Changed original ClientSeat constructors.')
    out[seat]=out[seat].replace(old,old+'\n                    key_input: crate::xdg_shell_wrapper::client_state::keyboard_input_state::InputLedger::new(seat.clone()),')
    out[seat]=once(out[seat],'                        sp.client.kbd.replace(kbd);','                        sp.client.key_input.invalidate();\n                        sp.client.kbd.replace(kbd);')
    out[seat]=once(out[seat],'                sp.server.seat.remove_keyboard();','                sp.client.key_input.invalidate();\n                sp.server.seat.remove_keyboard();')
    text=out[KEYBOARD]
    for name,next_name,statement in [('enter','leave','seat.client.key_input.enter(_raw);'),('leave','press_key','seat.client.key_input.invalidate();'),('release_key','update_repeat_info','let _ = seat.client.key_input.release(event.raw_code);'),('update_keymap','update_modifiers','seat.client.key_input.invalidate();')]:text=callback(text,name,next_name,statement)
    text=once(text,'            .map(|seat| {\n                (\n                    seat.name.as_str(),',
        '            .map(|seat| {\n                let _ = seat.client.key_input.press(event.raw_code, serial, event.time);\n                (\n                    seat.name.as_str(),')
    out[KEYBOARD]=text;out[MODULE]=(HERE/'keyboard_input_state.rs').read_text(encoding='utf-8')
    return out

def prepare(source,output,apply=False):
    source=Path(source);output=Path(output)
    if source.is_symlink() or any(p.is_symlink() for p in source.parents):raise ValueError('Symlink source forbidden.')
    source=source.resolve()
    if any(p in ('usr','opt','.cache','.cargo') for p in source.parts):raise ValueError('Use isolated source, not installed files/caches.')
    if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=PIN:raise ValueError('Exact original panel HEAD required.')
    original=originals();expected=expected_inputs();files={}
    for name,text in expected.items():
        path=source/name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.resolve().is_relative_to(source):raise ValueError('Symlink/escaped client input source forbidden.')
        if subprocess.check_output(['git','-C',str(source),'show','HEAD:'+name])!=original[name].encode() or path.read_bytes()!=text.encode():raise ValueError('Changed original/prerequisite input bytes; preserve tree.')
        files[name]=text
    path=source/MODULE
    if path.exists() or path.is_symlink() or any(p.is_symlink() for p in path.parents):raise ValueError('Existing/symlink input module refused; fresh tree required.')
    changed=transform(files)
    patch=''.join(''.join(difflib.unified_diff(expected.get(n,'').splitlines(True),t.splitlines(True),fromfile='a/'+n if n in expected else '/dev/null',tofile='b/'+n)) for n,t in changed.items())
    with output.open('x',encoding='utf-8',newline='\n') as stream:stream.write(patch)
    subprocess.run(['git','-C',str(source),'apply','--check',str(output.resolve())],check=True)
    if apply:
        subprocess.run(['git','-C',str(source),'apply',str(output.resolve())],check=True)
        if any((source/n).read_bytes()!=t.encode() for n,t in changed.items()):raise ValueError('Native client input postimage mismatch.')
    return changed

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source',type=Path);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--apply',action='store_true');args=parser.parse_args();prepare(args.source,args.output,args.apply)
