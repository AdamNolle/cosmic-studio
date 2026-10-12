#!/usr/bin/env python3
"""Guarded original client keymap text capture; explicit local XKB lookup only."""
import argparse,importlib.util,difflib,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
PIN='b5cc19e351b82eed999097ced1ff267d27bf8e7a'
PREFIX='cosmic-panel-bin/src/xdg_shell_wrapper/'
MODULE=PREFIX+'client/client_keymap.rs'

def prerequisite():
    spec=importlib.util.spec_from_file_location('context_prerequisite',HERE/'prepare_keyboard_context.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def expected_inputs():
    prior=prerequisite();return prior.transform(prior.expected_inputs())

def once(text,old,new):
    if text.count(old)!=1:raise ValueError('Changed exact native client-keymap seam.')
    return text.replace(old,new,1)

def transform(files):
    if files!=expected_inputs():raise ValueError('Changed original event-context postimages; fresh tree required.')
    changed=dict(files);state=PREFIX+'client/state.rs';seat=PREFIX+'client/handlers/seat.rs';keyboard=PREFIX+'client/handlers/keyboard.rs'
    changed[state]=once(changed[state],'pub(crate) mod keyboard_event_context;',
        'pub(crate) mod keyboard_event_context;\n#[path = "client_keymap.rs"]\npub(crate) mod client_keymap;')
    changed[state]=once(changed[state],'    pub(crate) key_events: keyboard_event_context::EventContext<',
        '    pub(crate) keymap_source: client_keymap::ClientKeymap,\n    pub(crate) key_events: keyboard_event_context::EventContext<')
    old='                    key_events: crate::xdg_shell_wrapper::client_state::keyboard_event_context::EventContext::new(seat.clone()),'
    if changed[seat].count(old)!=2:raise ValueError('Changed ClientSeat constructors.')
    changed[seat]=changed[seat].replace(old,old+'\n                    keymap_source: Default::default(),')
    old='sp.client.key_events.invalidate();'
    if changed[seat].count(old)!=2:raise ValueError('Changed native capability/replacement seam.')
    changed[seat]='\n'.join(line+'\n'+line[:len(line)-len(line.lstrip())]+'sp.client.keymap_source.clear();' if line.strip()==old else line for line in changed[seat].split('\n'))
    text=changed[keyboard];start=text.index('    fn update_keymap(');end=text.index('    fn update_modifiers(',start)
    block=text[start:end]
    block=once(block,'seat.client.key_events.invalidate();',
        'seat.client.key_events.invalidate();\n                seat.client.keymap_source.replace(keymap.as_string());')
    changed[keyboard]=text[:start]+block+text[end:]
    changed[MODULE]=(HERE/'client_keymap.rs').read_text(encoding='utf-8');return changed

def prepare(source,output,apply=False):
    source=Path(source);output=Path(output)
    if source.is_symlink() or any(p.is_symlink() for p in source.parents):raise ValueError('Symlink source forbidden.')
    source=source.resolve()
    if any(p in ('usr','opt','.cargo','.cache') for p in source.parts):raise ValueError('Use isolated source, not installed files/caches.')
    if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=PIN:raise ValueError('Exact original panel HEAD required.')
    original=prerequisite().prerequisite().originals();expected=expected_inputs();files={}
    for name,text in expected.items():
        path=source/name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.resolve().is_relative_to(source):raise ValueError('Symlink/escaped native keymap source forbidden.')
        if name in original and subprocess.check_output(['git','-C',str(source),'show','HEAD:'+name])!=original[name].encode():raise ValueError('Original native keymap Git blob differs.')
        if path.read_bytes()!=text.encode():raise ValueError('Changed exact event context input; preserve tree.')
        files[name]=text
    path=source/MODULE
    if path.exists() or path.is_symlink() or any(p.is_symlink() for p in path.parents):raise ValueError('Existing/symlink keymap module refused; use fresh tree.')
    changed=transform(files)
    patch=''.join(''.join(difflib.unified_diff(expected.get(n,'').splitlines(True),t.splitlines(True),fromfile='a/'+n if n in expected else '/dev/null',tofile='b/'+n)) for n,t in changed.items())
    with output.open('x',encoding='utf-8',newline='\n') as stream:stream.write(patch)
    subprocess.run(['git','-C',str(source),'apply','--check',str(output.resolve())],check=True)
    if apply:
        subprocess.run(['git','-C',str(source),'apply',str(output.resolve())],check=True)
        if any((source/n).read_bytes()!=t.encode() for n,t in changed.items()):raise ValueError('Native client keymap postimage mismatch.')
    return changed

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source',type=Path);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--apply',action='store_true');args=parser.parse_args();prepare(args.source,args.output,args.apply)
