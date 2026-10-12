#!/usr/bin/env python3
"""Exact prior client-keymap postimages plus explicit complete Iced conversion."""
import argparse,difflib,gzip,hashlib,importlib.util,json,re,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
PIN='b5cc19e351b82eed999097ced1ff267d27bf8e7a'
PREFIX='cosmic-panel-bin/src/xdg_shell_wrapper/'
MODULE=PREFIX+'client/client_iced_event.rs'
TABLE=PREFIX+'client/client_key_tables.rs'
FIXTURE_SHA='38dae7286b61a3b5cc3be0f85b48730051a0921d9db1786584da748ae46449e1'

def prerequisite():
    spec=importlib.util.spec_from_file_location('keymap_prerequisite',HERE/'prepare_client_keymap.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def expected_inputs():
    prior=prerequisite();return prior.transform(prior.expected_inputs())

def table_source():
    raw=(HERE/'pinned-iced-keymap-sources.json.gz').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA:raise ValueError('Original Iced keymap fixture checksum differs.')
    fixture=json.loads(gzip.decompress(raw));keymap=fixture['iced/winit/src/platform_specific/wayland/keymap.rs']
    if (HERE/'pinned-iced-keymap.LICENSE').read_bytes()!=fixture['iced/LICENSE'].encode():raise ValueError('Original Iced keymap license differs.')
    physical=keymap[keymap.index('pub fn scancode_to_physicalkey('):keymap.index('pub fn physicalkey_to_scancode(')]
    physical=physical.replace('pub fn','pub(crate) fn').replace('PhysicalKey','Physical').replace('NativeKeyCode','NativeCode').replace('KeyCode::','Code::').replace('Code::MetaLeft','Code::SuperLeft').replace('Code::MetaRight','Code::SuperRight')
    named=keymap[keymap.index('pub fn keysym_to_key('):keymap.index('pub fn key_to_keysym(')]
    named=named.replace('pub fn','pub(crate) fn').replace('    use xkbcommon_dl::keysyms;\n','')
    def constant(match):
        stem=match.group(1);stem=stem.removeprefix('_') if stem.startswith('_3270') else stem
        return 'keysyms::KEY_'+stem.replace('XF86_','XF86').replace('SUN_','Sun')
    named=''.join(line if line.lstrip().startswith('//') else re.sub(r'(?:xkeysym::key|keysyms)::(\w+)',constant,line) for line in named.splitlines(True))
    return '// SPDX-License-Identifier: MIT\n// Adapted from exact Iced 87e1787f Wayland keymap (commented upstream cases retained).\n// Borrowed from winit in original source. See pinned-iced-keymap.LICENSE / NOTICE.\nuse cosmic::iced::keyboard::{Key, Location, key::{Named, Code, Physical, NativeCode}};\nuse smithay::input::keyboard::xkb::keysyms;\n\n'+physical+named.rstrip()+'\n'

def once(text,old,new):
    if text.count(old)!=1:raise ValueError('Changed exact native Iced conversion seam.')
    return text.replace(old,new,1)

def transform(files):
    if files!=expected_inputs():raise ValueError('Changed exact client-keymap postimages; fresh tree required.')
    tables=table_source()
    if (HERE/'client_key_tables.rs').read_bytes()!=tables.encode():raise ValueError('Changed original adapted Iced key tables.')
    changed=dict(files);state=PREFIX+'client/state.rs'
    changed[state]=once(changed[state],'pub(crate) mod client_keymap;',
        'pub(crate) mod client_keymap;\n#[path = "client_key_tables.rs"]\npub(crate) mod client_key_tables;\n#[path = "client_iced_event.rs"]\npub(crate) mod client_iced_event;')
    changed[state]=once(changed[state],'impl ClientSeat {\n',
        'impl ClientSeat {\n    // Explicit metadata conversion; caller must separately validate live routing/grabs.\n    pub(crate) fn iced_key_event(&self, frame: &client_iced_event::Frame<WlSeat>)\n        -> Result<client_iced_event::Converted<WlSeat>, client_keymap::LookupError> {\n        client_iced_event::convert(&self.keymap_source, &self.key_events, frame)\n    }\n')
    changed[TABLE]=tables;changed[MODULE]=(HERE/'client_iced_event.rs').read_text(encoding='utf-8');return changed

def prepare(source,output,apply=False):
    source=Path(source);output=Path(output)
    if source.is_symlink() or any(p.is_symlink() for p in source.parents):raise ValueError('Symlink source forbidden.')
    source=source.resolve()
    if any(p in ('usr','opt','.cargo','.cache') for p in source.parts):raise ValueError('Use isolated source, not installed files/caches.')
    if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=PIN:raise ValueError('Exact original panel HEAD required.')
    prior=prerequisite();original=prior.prerequisite().prerequisite().originals();expected=expected_inputs();files={}
    for name,text in expected.items():
        path=source/name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.resolve().is_relative_to(source):raise ValueError('Symlink/escaped native conversion source forbidden.')
        if name in original and subprocess.check_output(['git','-C',str(source),'show','HEAD:'+name])!=original[name].encode():raise ValueError('Original native conversion Git blob differs.')
        if path.read_bytes()!=text.encode():raise ValueError('Changed exact keymap input; preserve tree.')
        files[name]=text
    for name in (MODULE,TABLE):
        path=source/name
        if path.exists() or path.is_symlink() or any(p.is_symlink() for p in path.parents):raise ValueError('Existing/symlink conversion module refused; use fresh tree.')
    changed=transform(files)
    patch=''.join(''.join(difflib.unified_diff(expected.get(n,'').splitlines(True),t.splitlines(True),fromfile='a/'+n if n in expected else '/dev/null',tofile='b/'+n)) for n,t in changed.items())
    with output.open('x',encoding='utf-8',newline='\n') as stream:stream.write(patch)
    subprocess.run(['git','-C',str(source),'apply','--check',str(output.resolve())],check=True)
    if apply:
        subprocess.run(['git','-C',str(source),'apply',str(output.resolve())],check=True)
        if any((source/n).read_bytes()!=t.encode() for n,t in changed.items()):raise ValueError('Native Iced conversion postimage mismatch.')
    return changed

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source',type=Path);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--apply',action='store_true');args=parser.parse_args();prepare(args.source,args.output,args.apply)
