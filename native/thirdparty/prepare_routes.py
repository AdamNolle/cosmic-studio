#!/usr/bin/env python3
"""Port exact third-party applet popup constructors in an isolated source.

The existing view, positioner, input behavior and application identity remain
authoritative. This only registers the popup with libcosmic's native lifecycle.
No binaries, Flatpak permissions or installed files are changed.
"""
import argparse
import difflib
import hashlib
from pathlib import Path
import subprocess

PROFILES = {
    'brightness': {
        'revision': '3e6486ff11dba8cdb729420c27b4ce2c519f8443',
        'file': 'src/app.rs',
        'sha256': 'a88bdb088798ba15030681948c1ec2c6b1dc085a737a062b9ef54ac93f4ac30b',
        'constructors': 2,
    },
    'sysinfo': {
        'revision': 'f66e0c7b133bf4249d23ab7483693cedca46ad19',
        'file': 'src/applet.rs',
        'sha256': 'c88e09ae6795179dfbb9b6f93630ec062b8fca1cff22671c97b1bbec588ea65b',
        'constructors': 1,
    },
}

MANAGED_POPUP = '''cosmic::surface::surface_task(cosmic::surface::action::app_popup::<Self>(
                    |_| cosmic::surface::action::LiveSettings::default(),
                    move |_| popup_settings.clone(),
                    None,
                ))'''


def changes_for(source, name):
    source = source.resolve()
    forbidden = [Path('/usr'), Path.home()/'.cargo', Path.home()/'.var', Path.home()/'.local']
    if any(source.is_relative_to(path) for path in forbidden):
        raise ValueError('Use an isolated source; installed files and Cargo caches are forbidden.')
    profile = PROFILES[name]
    revision = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != profile['revision']:
        raise ValueError('Source HEAD differs from the installed exact revision.')
    file = source / profile['file']
    before = file.read_text()
    if hashlib.sha256(before.encode()).hexdigest() != profile['sha256']:
        raise ValueError('Changed pinned constructor input; prepare a fresh isolated source.')
    if name == 'brightness':
        old = 'get_popup(popup_settings)'
        if before.count(old) != profile['constructors']:
            raise ValueError('Unrecognized popup constructor count.')
        after = before.replace(old, MANAGED_POPUP)
        import_before = 'use cosmic::iced::platform_specific::shell::commands::popup::{destroy_popup, get_popup};'
        if after.count(import_before) != 1:
            raise ValueError('Unrecognized popup command import.')
        after = after.replace(import_before,
            'use cosmic::iced::platform_specific::shell::commands::popup::destroy_popup;')
    else:
        old = '''cosmic::iced::platform_specific::shell::commands::popup::get_popup(
                    popup_settings,
                )'''
        if before.count(old) != profile['constructors']:
            raise ValueError('Unrecognized popup constructor count.')
        after = before.replace(old, MANAGED_POPUP)
    return file, before, after


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--profile', choices=PROFILES, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    file, before, after = changes_for(args.source, args.profile)
    name = str(file.relative_to(args.source.resolve()))
    patch = ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                      fromfile='a/'+name, tofile='b/'+name))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(patch)
    if args.apply:
        file.write_text(after)
    print(('Applied' if args.apply else 'Prepared')+' pinned native popup routes: '+args.profile)


if __name__ == '__main__':
    main()
