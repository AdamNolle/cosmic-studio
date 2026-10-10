#!/usr/bin/env python3
"""Prepare exact installed native OS clients for a private font build."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tomllib

from embed_fonts import require_isolated

COMPONENTS = {
    '82e7cd814addb0641959b634227fe550374e195b': ('cosmic-applets', '03c8f93b294ad239ea935f6dd3c14a15acde8d0d'),
    'aa4dac2702506395ab76da1f6755e03b2ccb0db8': ('cosmic-notifications', 'd921602cde8248c070b493ce43b0edd388e19b9a'),
    '3faadf56bdaea4b088ea8dc5e808b167cec86de3': ('cosmic-osd', 'd921602cde8248c070b493ce43b0edd388e19b9a'),
    'c6e57a18a8abaf4ae6b5755576982839f8e53900': ('cosmic-store', '23f5d63fed2a370f3c2f54b90ec8f0896fe82105'),
    'fdcc323f533137430fa5609a6986daebda2d5741': ('cosmic-monitor', '03c8f93b294ad239ea935f6dd3c14a15acde8d0d'),
    '66b3f34335a500ce5dc93880d06f7ae94905872f': ('cosmic-player', '9cc82abd9ca5601bb0341edd12a9acbc97e77801'),
    'd820ab36b84d0fe97b9e1fb96683b9597f03ac83': ('cosmic-viewer', 'eaa7a5a24c4359ebeaab507855388942e8984d5d'),
    '38e962576f1893e6452d4c273c41149c432191b2': ('cosmic-osk', '87ab8179e1bd9880239c340855ae8862034bd0e8'),
    '9b5a9490e60966ebf0565267ce0e9fca368dfbd1': ('cosmic-initial-setup', '8cb10bf6e24b86a7d2a9cf8c662d3e0154db1b21'),
}

def revision(path):
    return subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()

def changes_for(source, library):
    pin = revision(source)
    if pin not in COMPONENTS:
        raise RuntimeError('Exact installed native component revision is required.')
    name, library_pin = COMPONENTS[pin]
    if revision(library) != library_pin:
        raise RuntimeError('Component native library revision does not match its original lockfile.')
    lock = tomllib.loads((source/'Cargo.lock').read_text())
    native = [package for package in lock['package'] if package['name']=='libcosmic']
    if len(native)!=1 or not native[0].get('source','').endswith('#'+library_pin):
        raise RuntimeError('Use the unmodified upstream pinned Cargo.lock for preparation.')
    font = (library/'src/font.rs').read_text()
    if 'pub fn display() -> Font' not in font or 'Font::from(crate::config::interface_font())' not in font:
        raise RuntimeError('Native semantic display helper must preserve configured UI font selection.')
    if not (library/'res/studio-fonts/manifest.json').is_file():
        raise RuntimeError('Apply the reviewed authentic font embedding patch first.')
    package=Path(__file__).resolve().parents[2]
    expected=json.loads((package/'fonts/manifest.json').read_text())
    embedded=json.loads((library/'res/studio-fonts/manifest.json').read_text())
    if embedded!=expected: raise RuntimeError('Embedded font provenance differs from the reviewed manifest.')
    for entries in expected['families'].values():
        for entry in entries:
            data=(library/'res/studio-fonts'/entry['file']).read_bytes()
            if hashlib.sha256(data).hexdigest()!=entry['sha256']:
                raise RuntimeError('Embedded authentic font bytes differ: '+entry['file'])
    packages = {}
    for cargo in library.rglob('Cargo.toml'):
        if '/target/' in str(cargo) or '/examples/' in str(cargo):
            continue
        metadata = tomllib.loads(cargo.read_text())
        if 'package' in metadata:
            packages[metadata['package']['name']] = cargo.parent
    if not {'libcosmic','iced'} <= packages.keys():
        raise RuntimeError('Native library submodules are incomplete.')
    cargo = (source/'Cargo.toml').read_text()
    override=tomllib.loads(cargo).get('patch',{}).get('https://github.com/pop-os/libcosmic')
    base=cargo
    if override is not None:
        # This exact OSD commit includes an upstream development-only relative
        # override. Replace that reviewed section, never append a duplicate.
        if name!='cosmic-osd' or override not in [{}, {'libcosmic':{'path':'../libcosmic'}}]:
            raise RuntimeError('Source already has an unreviewed native library override.')
        base,count=re.subn(r"(?ms)^\[patch\.'https://github.com/pop-os/libcosmic'\]\n.*?(?=^\[|\Z)",'',cargo)
        if count!=1: raise RuntimeError('Unrecognized upstream OSD development override.')
    patched = base+'\n[patch."https://github.com/pop-os/libcosmic"]\n'
    patched += ''.join(f'{package} = {{ path = {json.dumps(str(path))} }}\n' for package,path in sorted(packages.items()))
    changes = {'Cargo.toml':(cargo,patched)}
    if name=='cosmic-notifications':
        app = (source/'src/app.rs').read_text()
        before = '''text::body(
                                                n.summary.lines().next().unwrap_or_default()
                                            )
                                            .width(Length::Fill),'''
        after = before.replace('.width(Length::Fill),', '.font(cosmic::font::display())\n                                            .size(18)\n                                            .width(Length::Fill),')
        if app.count(before)!=1:
            raise RuntimeError('Notification semantic summary source differs from reviewed shape.')
        changes['src/app.rs'] = (app,app.replace(before,after))
    return name, changes

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    source=require_isolated(args.source);library=require_isolated(args.library)
    name,changes=changes_for(source,library)
    patch=''.join(''.join(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),
                                            fromfile='a/'+file,tofile='b/'+file))
                  for file,(before,after) in changes.items())
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(patch)
    if args.apply:
        for file,(_,after) in changes.items(): (source/file).write_text(after)
    print(('Applied' if args.apply else 'Prepared')+' private native component typography: '+name)

if __name__=='__main__': main()
