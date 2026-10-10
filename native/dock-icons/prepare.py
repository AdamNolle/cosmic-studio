#!/usr/bin/env python3
"""Apply the exact reviewed dock geometry to its pinned native applet source."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def prepare(source, apply=False):
    profile = json.loads((HERE/'profile.json').read_text())
    patch = HERE/'compact-icons.patch'
    if sha256(patch.read_bytes()) != profile['patch_sha256']:
        raise RuntimeError('Compact dock patch changed; review a new profile before preparation.')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    if revision != profile['revision']:
        raise RuntimeError('Compact dock source revision is not the reviewed 82e7cd8 input.')
    path = source/profile['file']
    current = sha256(path.read_bytes())
    if current == profile['postimage']:
        return profile
    if current != profile['preimage']:
        raise RuntimeError('App list source differs from both reviewed compact preimage and postimage.')
    subprocess.run(['git', 'apply', '--check', str(patch)], cwd=source, check=True)
    if apply:
        subprocess.run(['git', 'apply', str(patch)], cwd=source, check=True)
        if sha256(path.read_bytes()) != profile['postimage']:
            raise RuntimeError('Compact dock source did not produce the reviewed postimage.')
    return profile


def record_binary(source, binary, output):
    profile = prepare(source)
    if sha256((source/profile['file']).read_bytes()) != profile['postimage']:
        raise RuntimeError('Prepare the reviewed compact source before recording a build.')
    content = binary.read_bytes()
    if content[:4] != b'\x7fELF' or any(flag not in content for flag in (
            b'COSMIC_STUDIO_COMPACT_DOCK', b'COSMIC_STUDIO_POPUP_GLASS')):
        raise RuntimeError('Candidate lacks the linked native compact/popup feature gates.')
    record = dict(profile, binary=str(binary.resolve()), binary_sha256=sha256(content),
                  source=str(source.resolve()), cargo_lock_sha256=sha256((source/'Cargo.lock').read_bytes()))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2)+'\n')
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--record-binary', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.record_binary:
        if not args.output:
            parser.error('--output is required with --record-binary')
        result = record_binary(args.source, args.record_binary, args.output)
    else:
        result = prepare(args.source, args.apply)
    print(json.dumps(result, indent=2))
