#!/usr/bin/env python3
"""Verify isolated greeter appearance edits against its exact upstream source.

This checker does not launch a greeter, call PAM, or acquire a session lock.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

PACKAGE=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('greeter_prepare',Path(__file__).with_name('prepare.py'))
prepare=importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)

def git_text(source,name):
    return subprocess.check_output(['git','-C',str(source),'show',prepare.PIN+':'+name],text=True)

def verify(source):
    revision=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
    if revision!=prepare.PIN: raise RuntimeError('Source revision does not match the installed greeter.')
    with tempfile.TemporaryDirectory(prefix='studio-greeter-source-') as directory:
        baseline=Path(directory);(baseline/'src').mkdir()
        for name in ['lib.rs','main.rs','time.rs','greeter.rs','locker.rs']:
            (baseline/'src'/name).write_text(git_text(source,'src/'+name))
        for name,(_,expected) in prepare.changes_for(baseline).items():
            if (source/'src'/name).read_text()!=expected:
                raise RuntimeError('Source has edits beyond the reviewed appearance hooks: '+name)
    for target,asset in [('studio.rs','studio.rs'),('studio_preview.rs','preview.rs')]:
        if (source/'src'/target).read_bytes()!=(PACKAGE/'native/greeter'/asset).read_bytes():
            raise RuntimeError('Native helper does not match the packaged source: '+target)
    protected={}
    for name in ['src/common.rs','src/wayland/mod.rs']:
        original=git_text(source,name);actual=(source/name).read_text()
        if original!=actual: raise RuntimeError('Protected source was changed: '+name)
        protected[name]=hashlib.sha256(actual.encode()).hexdigest()
    return {'status':'PASS','revision':revision,
            'appearance_source':'matches exact reviewed transformations',
            'protected_source_sha256':protected,
            'scope':'Static verification; actual authentication/lock/login states require separate review'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    args=parser.parse_args()
    print(json.dumps(verify(args.source.resolve()),indent=2))

if __name__=='__main__': main()
