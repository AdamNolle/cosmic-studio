#!/usr/bin/env python3
"""Exact Iced prerequisite plus same-seat active leave/press-history repair."""
import argparse,difflib,importlib.util,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
PIN='b5cc19e351b82eed999097ced1ff267d27bf8e7a'
PREFIX='cosmic-panel-bin/src/xdg_shell_wrapper/'
MODULE=PREFIX+'client/client_focus_match.rs'
KEYBOARD=PREFIX+'client/handlers/keyboard.rs'

def prerequisite():
    spec=importlib.util.spec_from_file_location('iced_prerequisite',HERE/'prepare_client_iced.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def expected_inputs():
    prior=prerequisite();return prior.transform(prior.expected_inputs())

def once(text,old,new):
    if text.count(old)!=1:raise ValueError('Changed exact native active-focus seam.')
    return text.replace(old,new,1)

def transform(files):
    if files!=expected_inputs():raise ValueError('Changed exact Iced postimages; fresh tree required.')
    changed=dict(files);state=PREFIX+'client/state.rs'
    changed[state]=once(changed[state],'pub(crate) mod client_iced_event;',
        'pub(crate) mod client_iced_event;\n#[path = "client_focus_match.rs"]\npub(crate) mod client_focus_match;')
    text=changed[KEYBOARD]
    text=once(text,'use crate::xdg_shell_wrapper::client_state::FocusStatus;',
        'use crate::xdg_shell_wrapper::client_state::{FocusStatus, client_focus_match};')
    start=text.index('    fn leave(');end=text.index('    fn press_key(',start);block=text[start:end]
    block=once(block,'            .seats\n            .iter_mut()','            .seats\n            .iter()')
    block=once(block,'                seat.client.key_input.invalidate();\n                seat.client.key_events.invalidate();\n','')
    block=once(block,'''            if let Some(i) = c_focused_surface.iter().position(|f| &f.0 == surface) {
                c_focused_surface[i].2 = FocusStatus::LastFocused(Instant::now());
                true
            } else {
                false
            }''','''            let Some(i) = client_focus_match::leave_index(
                &c_focused_surface, &name, surface,
                |status| matches!(status, FocusStatus::Focused),
            ) else {
                // A stale/wrong-seat/ambiguous leave cannot retire live focus.
                return;
            };
            c_focused_surface[i].2 = FocusStatus::LastFocused(Instant::now());
            true''')
    block=once(block,'        let s_surface = self',
        '''        // Retire only after the actual originating keyboard/active surface match.
        if let Some(seat) = self.server_state.seats.iter_mut().find(|seat| {
            seat.client.kbd.as_ref().map(|k| k == keyboard).unwrap_or(false)
        }) {
            seat.client.key_input.invalidate();
            seat.client.key_events.invalidate();
        }

        let s_surface = self''')
    text=text[:start]+block+text[end:]
    text=once(text,'''            c_focused_surface
                .iter()
                .find_map(|f| if f.1 == seat_name { Some(f.0.clone()) } else { None })''',
        '''            client_focus_match::active_index(
                &c_focused_surface, &seat_name,
                |status| matches!(status, FocusStatus::Focused),
            ).map(|i| c_focused_surface[i].0.clone())''')
    changed[KEYBOARD]=text;changed[MODULE]=(HERE/'client_focus_match.rs').read_text(encoding='utf-8');return changed

def prepare(source,output,apply=False):
    source=Path(source);output=Path(output)
    if source.is_symlink() or any(p.is_symlink() for p in source.parents):raise ValueError('Symlink source forbidden.')
    source=source.resolve()
    if any(p in ('usr','opt','.cargo','.cache') for p in source.parts):raise ValueError('Use isolated source, not installed files/caches.')
    if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=PIN:raise ValueError('Exact original panel HEAD required.')
    prior=prerequisite();original=prior.prerequisite().prerequisite().prerequisite().originals();expected=expected_inputs();files={}
    for name,text in expected.items():
        path=source/name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.resolve().is_relative_to(source):raise ValueError('Symlink/escaped active-focus source forbidden.')
        if name in original and subprocess.check_output(['git','-C',str(source),'show','HEAD:'+name])!=original[name].encode():raise ValueError('Original active-focus Git blob differs.')
        if path.read_bytes()!=text.encode():raise ValueError('Changed exact Iced input; preserve tree.')
        files[name]=text
    path=source/MODULE
    if path.exists() or path.is_symlink() or any(p.is_symlink() for p in path.parents):raise ValueError('Existing/symlink active-focus module refused; fresh tree required.')
    changed=transform(files)
    patch=''.join(''.join(difflib.unified_diff(expected.get(n,'').splitlines(True),t.splitlines(True),fromfile='a/'+n if n in expected else '/dev/null',tofile='b/'+n)) for n,t in changed.items())
    with output.open('x',encoding='utf-8',newline='\n') as stream:stream.write(patch)
    subprocess.run(['git','-C',str(source),'apply','--check',str(output.resolve())],check=True)
    if apply:
        subprocess.run(['git','-C',str(source),'apply',str(output.resolve())],check=True)
        if any((source/n).read_bytes()!=t.encode() for n,t in changed.items()):raise ValueError('Native active-focus postimage mismatch.')
    return changed

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source',type=Path);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--apply',action='store_true');args=parser.parse_args();prepare(args.source,args.output,args.apply)
