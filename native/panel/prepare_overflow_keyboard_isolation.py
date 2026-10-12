#!/usr/bin/env python3
"""Exact reviewed wrapper prerequisite plus overflow-local fail-closed widget isolation."""
import argparse,difflib,importlib.util,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
PIN='b5cc19e351b82eed999097ced1ff267d27bf8e7a'
VIEW='cosmic-panel-bin/src/iced/elements/overflow_button.rs'
MODULE='cosmic-panel-bin/src/iced/elements/overflow_keyboard_isolation.rs'

def prerequisite():
    spec=importlib.util.spec_from_file_location('overflow_prior',HERE/'prepare_iced_keyboard_route.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def expected_inputs():
    prior=prerequisite();return prior.transform(prior.expected_inputs())

def transform(files):
    if files!=expected_inputs():raise ValueError('Changed exact wrapper route inputs; fresh tree required.')
    changed=dict(files);text=files[VIEW]
    old='''    fn view(&self) -> crate::iced::Element<'_, Self::Message> {
        Element::from('''
    new='''    fn view(&self) -> crate::iced::Element<'_, Self::Message> {
        keyboard_isolation::isolate(Element::from('''
    if text.count(old)!=1 or not text.endswith('        )\n    }\n}\n'):raise ValueError('Changed exact overflow view seam.')
    text=text.replace(old,new,1)
    text=text.removesuffix('        )\n    }\n}\n')+'        ))\n    }\n}\n'
    changed[VIEW]=text+'\n#[path = "overflow_keyboard_isolation.rs"]\nmod keyboard_isolation;\n'
    changed[MODULE]=(HERE/'overflow_keyboard_isolation.rs').read_text(encoding='utf-8')
    return changed

def prepare(source,output,apply=False):
    source=Path(source);output=Path(output)
    if source.is_symlink() or any(p.is_symlink() for p in source.parents):raise ValueError('Symlink source forbidden.')
    source=source.resolve()
    if any(p in ('usr','opt','.cargo','.cache') for p in source.parts):raise ValueError('Use isolated sources, not installed files/caches.')
    if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=PIN:raise ValueError('Exact original panel HEAD required.')
    prior=prerequisite()
    original={**prior.load('prepare_keyboard_focus').originals(),**prior.load('prepare_keyboard_input').originals(),**prior.prerequisite().originals()}
    expected=expected_inputs();files={}
    for name,text in expected.items():
        path=source/name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.resolve().is_relative_to(source):raise ValueError('Symlink/escaped isolation source forbidden.')
        if name in original and subprocess.check_output(['git','-C',str(source),'show','HEAD:'+name])!=original[name].encode():raise ValueError('Original isolation Git blob differs.')
        if path.read_bytes()!=text.encode():raise ValueError('Changed exact isolation input; preserve tree.')
        files[name]=text
    path=source/MODULE
    if path.exists() or path.is_symlink() or any(p.is_symlink() for p in path.parents):raise ValueError('Existing/symlink isolation module refused; fresh tree required.')
    changed=transform(files)
    patch=''.join(''.join(difflib.unified_diff(expected.get(n,'').splitlines(True),t.splitlines(True),fromfile='a/'+n if n in expected else '/dev/null',tofile='b/'+n)) for n,t in changed.items())
    with output.open('x',encoding='utf-8',newline='\n') as stream:stream.write(patch)
    subprocess.run(['git','-C',str(source),'apply','--check',str(output.resolve())],check=True)
    if apply:
        subprocess.run(['git','-C',str(source),'apply',str(output.resolve())],check=True)
        if any((source/n).read_bytes()!=t.encode() for n,t in changed.items()):raise ValueError('Isolation postimage mismatch.')
    return changed

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source',type=Path);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--apply',action='store_true');args=parser.parse_args();prepare(args.source,args.output,args.apply)
