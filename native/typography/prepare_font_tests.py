#!/usr/bin/env python3
"""Give the isolated native library its own pinned font-test workspace.

Cargo cannot test a dependency's private unit tests from an app workspace.
This prepares only private build manifests; native runtime source is unchanged.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tomllib
from embed_fonts import PINS, LEGACY_REVISION, require_isolated

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('library',type=Path)
    parser.add_argument('--client-lock',type=Path,required=True)
    args=parser.parse_args()
    library=require_isolated(args.library)
    revision=subprocess.check_output(['git','-C',str(library),'rev-parse','HEAD'],text=True).strip()
    if revision not in PINS: raise RuntimeError('Unreviewed native library revision.')
    if not (library/'res/studio-fonts/manifest.json').is_file(): raise RuntimeError('Embed authentic fonts first.')
    cargo=library/'Cargo.toml';original=cargo.read_text()
    override=tomllib.loads(original).get('patch',{}).get('https://github.com/pop-os/libcosmic')
    base=original
    if override is not None:
        # The pinned older library ships a single self-path patch already.
        # Expand only that exact reviewed upstream shape for its private tests.
        if revision != LEGACY_REVISION or override != {'libcosmic':{'path':'./'}}:
            raise RuntimeError('Private font-test workspace is already prepared or unreviewed.')
        base,count=re.subn(r'(?ms)^\[patch\."https://github.com/pop-os/libcosmic"\]\n.*?(?=^\[|\Z)','',original)
        if count != 1: raise RuntimeError('Unrecognized legacy self-path override.')
    if original.count('    "examples/*",')!=1: raise RuntimeError('Unreviewed native workspace shape.')
    packages={}
    for path in library.rglob('Cargo.toml'):
        if '/target/' in str(path) or '/examples/' in str(path): continue
        data=tomllib.loads(path.read_text())
        if 'package' in data: packages[data['package']['name']]=path.parent
    if not {'libcosmic','iced'}<=packages.keys(): raise RuntimeError('Incomplete native submodules.')
    # Preserve the client's pinned registry/Git versions. Unit-test-only dev
    # dependencies can be fetched without changing its application lockfile.
    lock=args.client_lock.read_bytes();tomllib.loads(lock.decode())
    text=base.replace('    "examples/*",\n','')
    text+='\n[patch."https://github.com/pop-os/libcosmic"]\n'
    text+=''.join(f'{name} = {{ path = {json.dumps(str(path))} }}\n' for name,path in sorted(packages.items()))
    cargo.write_text(text);(library/'Cargo.lock').write_bytes(lock)
    print('Prepared private native font-test workspace: '+str(library))

if __name__=='__main__': main()
