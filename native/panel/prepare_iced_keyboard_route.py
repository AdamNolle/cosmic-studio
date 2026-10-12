#!/usr/bin/env python3
"""Exact single-event State prerequisite plus real IcedElement wrapper route."""
import argparse,difflib,hashlib,importlib.util,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
PIN='b5cc19e351b82eed999097ced1ff267d27bf8e7a'
WRAPPER='cosmic-panel-bin/src/iced/mod.rs'
MODULE='cosmic-panel-bin/src/iced/iced_keyboard_route.rs'
STATE='cosmic-panel-bin/src/iced/state.rs'

def load(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def prerequisite():return load('prepare_iced_keyboard_dispatch')
def expected_inputs():
    prior=prerequisite();focus=load('prepare_keyboard_focus')
    return {**focus.transform(focus.originals()),**prior.transform(prior.expected_inputs())}
def once(text,old,new):
    if text.count(old)!=1:raise ValueError('Changed exact wrapper keyboard route seam.')
    return text.replace(old,new,1)
def transform(files):
    if files!=expected_inputs():raise ValueError('Changed exact single-event postimages; fresh tree required.')
    changed=dict(files);text=files[WRAPPER]
    text=once(text,'    rx: Receiver<Option<<P as Program>::Message>>,','    rx: iced_keyboard_route::TaskInbox<<P as Program>::Message>,')
    if text.count('            rx,')!=2:raise ValueError('Changed exact fresh wrapper receiver constructors.')
    text=text.replace('            rx,','            rx: rx.into(),')
    changed[WRAPPER]=text+'\nmod iced_keyboard_route;\n'
    changed[STATE]=once(files[STATE],'mod keyboard_dispatch;','pub(super) mod keyboard_dispatch;')
    changed[MODULE]=(HERE/'iced_keyboard_route.rs').read_text(encoding='utf-8')
    return changed

def prepare(source,output,apply=False):
    source=Path(source);output=Path(output)
    if source.is_symlink() or any(p.is_symlink() for p in source.parents):raise ValueError('Symlink source forbidden.')
    source=source.resolve()
    if any(p in ('usr','opt','.cargo','.cache') for p in source.parts):raise ValueError('Use isolated source, not installed files/caches.')
    if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=PIN:raise ValueError('Exact original panel HEAD required.')
    original={**load('prepare_keyboard_focus').originals(),**load('prepare_keyboard_input').originals(),**prerequisite().originals()}
    expected=expected_inputs();files={}
    for name,text in expected.items():
        path=source/name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.resolve().is_relative_to(source):raise ValueError('Symlink/escaped wrapper route source forbidden.')
        if name in original and subprocess.check_output(['git','-C',str(source),'show','HEAD:'+name])!=original[name].encode():raise ValueError('Original wrapper route Git blob differs.')
        if path.read_bytes()!=text.encode():raise ValueError('Changed exact wrapper route input; preserve tree.')
        files[name]=text
    path=source/MODULE
    if path.exists() or path.is_symlink() or any(p.is_symlink() for p in path.parents):raise ValueError('Existing/symlink wrapper route module refused; fresh tree required.')
    changed=transform(files)
    patch=''.join(''.join(difflib.unified_diff(expected.get(n,'').splitlines(True),t.splitlines(True),fromfile='a/'+n if n in expected else '/dev/null',tofile='b/'+n)) for n,t in changed.items())
    with output.open('x',encoding='utf-8',newline='\n') as stream:stream.write(patch)
    subprocess.run(['git','-C',str(source),'apply','--check',str(output.resolve())],check=True)
    if apply:
        subprocess.run(['git','-C',str(source),'apply',str(output.resolve())],check=True)
        if any((source/n).read_bytes()!=t.encode() for n,t in changed.items()):raise ValueError('Native wrapper route postimage mismatch.')
    return changed

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source',type=Path);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--apply',action='store_true');args=parser.parse_args();prepare(args.source,args.output,args.apply)
