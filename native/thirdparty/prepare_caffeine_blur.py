#!/usr/bin/env python3
"""Apply the reviewed native popup blur backport to the exact old Iced source.

This preparation tool changes only an isolated source tree. It performs no
build, Flatpak installation, permission override, staging, or app launch.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

DIRECTORY = Path(__file__).resolve().parent


def validate(source):
    source = source.resolve()
    forbidden = (Path('/usr'), Path.home()/'.cargo', Path.home()/'.var', Path.home()/'.local')
    if any(source.is_relative_to(path) for path in forbidden):
        raise ValueError('Use an isolated Iced source; installed files and Cargo caches are forbidden.')
    profile = json.loads((DIRECTORY/'caffeine-blur-profile.json').read_text())
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    if revision != profile['iced']:
        raise ValueError('Iced HEAD differs from the exact installed submodule revision.')
    patch = DIRECTORY/'caffeine-blur.patch'
    if hashlib.sha256(patch.read_bytes()).hexdigest() != profile['patch_sha256']:
        raise ValueError('Reviewed blur patch hash differs; regenerate the strict profile deliberately.')
    for name, expected in profile['sha256'].items():
        file = source/name
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != expected:
            raise ValueError('Changed pinned blur input: '+name)
    for name in profile['new_files']:
        if (source/name).exists():
            raise ValueError('Blur output already exists; use a fresh isolated source: '+name)
    subprocess.run(['git', 'apply', '--check', str(patch)], cwd=source, check=True)
    return source, patch, profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Exact isolated Iced submodule directory')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    source, patch, profile = validate(args.source)
    if args.apply:
        subprocess.run(['git', 'apply', str(patch)], cwd=source, check=True)
    print(('Applied' if args.apply else 'Validated')+' popup-only native blur at '+profile['iced'])


if __name__ == '__main__':
    main()
