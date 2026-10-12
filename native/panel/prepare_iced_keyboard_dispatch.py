#!/usr/bin/env python3
"""Exact active-focus prerequisite plus explicit single-event Iced message boundary."""
import argparse,difflib,gzip,hashlib,importlib.util,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
PIN='b5cc19e351b82eed999097ced1ff267d27bf8e7a'
STATE='cosmic-panel-bin/src/iced/state.rs'
MODULE='cosmic-panel-bin/src/iced/iced_keyboard_dispatch.rs'
FIXTURE_SHA='27a86422819fe5a03b8179b794590035493da55ac70e4a71c58c7d6c34bf988c'

def prerequisite():
    spec=importlib.util.spec_from_file_location('focusmatch_prerequisite',HERE/'prepare_client_focus_match.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def originals():
    data=(HERE/'pinned-iced-state.json.gz').read_bytes()
    if hashlib.sha256(data).hexdigest()!=FIXTURE_SHA:raise ValueError('Changed exact original Iced State fixture.')
    files=json.loads(gzip.decompress(data))
    if set(files)!={STATE} or hashlib.sha256(files[STATE].encode()).hexdigest()!='199b3a9aa395a28fbc24f8007b9e472ccb0d9a591abda887d154689b5f9ec39a':raise ValueError('Changed original Iced State bytes.')
    return files

def expected_inputs():
    prior=prerequisite();return {**prior.transform(prior.expected_inputs()),**originals()}

def transform(files):
    if files!=expected_inputs():raise ValueError('Changed exact active-focus/State postimages; fresh tree required.')
    changed=dict(files)
    changed[STATE]+='\n#[path = "iced_keyboard_dispatch.rs"]\nmod keyboard_dispatch;\n'
    changed[MODULE]=(HERE/'iced_keyboard_dispatch.rs').read_text(encoding='utf-8')
    return changed

def prepare(source,output,apply=False):
    source=Path(source);output=Path(output)
    if source.is_symlink() or any(p.is_symlink() for p in source.parents):raise ValueError('Symlink source forbidden.')
    source=source.resolve()
    if any(p in ('usr','opt','.cargo','.cache') for p in source.parts):raise ValueError('Use isolated source, not installed files/caches.')
    if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=PIN:raise ValueError('Exact original panel HEAD required.')
    prior=prerequisite();original={**prior.prerequisite().prerequisite().prerequisite().prerequisite().originals(),**originals()}
    expected=expected_inputs();files={}
    for name,text in expected.items():
        path=source/name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.resolve().is_relative_to(source):raise ValueError('Symlink/escaped keyboard-dispatch source forbidden.')
        if name in original and subprocess.check_output(['git','-C',str(source),'show','HEAD:'+name])!=original[name].encode():raise ValueError('Original keyboard-dispatch Git blob differs.')
        if path.read_bytes()!=text.encode():raise ValueError('Changed exact keyboard-dispatch input; preserve tree.')
        files[name]=text
    path=source/MODULE
    if path.exists() or path.is_symlink() or any(p.is_symlink() for p in path.parents):raise ValueError('Existing/symlink keyboard-dispatch module refused; fresh tree required.')
    changed=transform(files)
    patch=''.join(''.join(difflib.unified_diff(expected.get(n,'').splitlines(True),t.splitlines(True),fromfile='a/'+n if n in expected else '/dev/null',tofile='b/'+n)) for n,t in changed.items())
    with output.open('x',encoding='utf-8',newline='\n') as stream:stream.write(patch)
    subprocess.run(['git','-C',str(source),'apply','--check',str(output.resolve())],check=True)
    if apply:
        subprocess.run(['git','-C',str(source),'apply',str(output.resolve())],check=True)
        if any((source/n).read_bytes()!=t.encode() for n,t in changed.items()):raise ValueError('Native keyboard-dispatch postimage mismatch.')
    return changed

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source',type=Path);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--apply',action='store_true');args=parser.parse_args();prepare(args.source,args.output,args.apply)
