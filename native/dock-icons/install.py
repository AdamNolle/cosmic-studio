#!/usr/bin/env python3
"""Apply the compact dock applet with exact backups and a package-version fallback."""
import argparse
import datetime
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('native_install', ROOT/'native/install.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)
sys.path.insert(0, str(ROOT/'icons/approved-dock'))
import install as icons

STATE = native.DATA/'compact-dock'
BINARY = STATE/'cosmic-app-list'
WRAPPER = Path.home()/'.local/bin/cosmic-app-list'
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', Path.home()/'.config'))/'cosmic/com.system76.CosmicPanel.Dock/v1'
SETTINGS = {'size': 'M', 'padding': '0', 'spacing': '4'}


def owned_native_candidate(version):
    """Prefer the reviewed multicall artifact installed by native/install.py."""
    alias = native.DATA/'bin/cosmic-app-list'
    artifact = native.DATA/'bin/cosmic-applets'
    if not alias.is_symlink() or os.readlink(alias) != 'cosmic-applets':
        return None
    if not artifact.is_file() or not os.access(artifact, os.X_OK):
        return None
    content = artifact.read_bytes()
    # Both exact process-start gates are retained in the linked native ELF.
    # Its source/patch provenance is separately recorded by prepare.py.
    if content[:4] != b'\x7fELF' or any(flag not in content for flag in (
            b'COSMIC_STUDIO_COMPACT_DOCK', b'COSMIC_STUDIO_POPUP_GLASS')):
        return None
    current = {str(p): native.fingerprint(p) for p in (alias, artifact)}
    for report in sorted((native.DATA/'native-backups').glob('*/manifest.json'), reverse=True):
        try:
            state = json.loads(report.read_text())
        except (OSError, ValueError):
            continue
        if (state.get('status') == 'applied'
                and state.get('versions', {}).get('cosmic-app-list') == version
                and all(state.get('after', {}).get(name) == entry for name, entry in current.items())):
            return alias
    return None


def reload():
    icons.reload_dock_plugins()
    deadline = time.monotonic()+15
    while time.monotonic()<deadline:
        running = icons.dock_applets()
        if running:
            return running
        time.sleep(.25)
    raise RuntimeError('Dock applets did not return after the configuration reload.')


def restore(path):
    state = json.loads(path.read_text())
    for name, expected in state['after'].items():
        if native.fingerprint(Path(name)) != expected:
            raise RuntimeError('A managed file changed after installation: '+name)
    for name, entry in state['before'].items():
        native.restore_entry(Path(name), entry)
    reload()
    state['status'] = 'restored'
    native.atomic(path, json.dumps(state, indent=2), 0o600)
    print('Restored the previous dock applet and sizing.')


def apply(source):
    version = subprocess.check_output(['dpkg-query','-W','-f=${Version}','cosmic-applets'],text=True)
    if '82e7cd8' not in version:
        raise RuntimeError('Rebuild the compact applet against the installed package revision.')
    content = source.read_bytes()
    if content[:4] != b'\x7fELF':
        raise RuntimeError('Expected a compiled ELF applet.')
    shared = owned_native_candidate(version)
    target = shared or BINARY
    wrapper = ('#!/bin/sh\n'
               'studio_version=$(dpkg-query -W -f=\'${Version}\' cosmic-applets 2>/dev/null)\n'
               'if [ "$studio_version" = '+shlex.quote(version)+' ]; then\n'
               '    export COSMIC_STUDIO_COMPACT_DOCK=1\n'
               '    export COSMIC_STUDIO_POPUP_GLASS=1\n'
               '    exec '+shlex.quote(str(target))+' "$@"\n'
               'fi\nexec /usr/bin/cosmic-app-list "$@"\n')
    updates = {WRAPPER: (wrapper,0o755)}
    if shared is None:
        updates[BINARY] = (content,0o755)
    updates.update({CONFIG/name: (value,0o644) for name,value in SETTINGS.items()})
    before_outputs = set(icons.dock_applets().values())
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = STATE/'backups'/(stamp+'.json')
    state = {'status':'applying','package_version':version,
             'candidate': str(target), 'shared_native': shared is not None,
             'before': {str(p):native.saved(p) for p in updates},'after':{}}
    native.atomic(backup,json.dumps(state,indent=2),0o600)
    try:
        for path,(data,mode) in updates.items():
            native.atomic(path,data,mode)
        running = reload()
        deadline = time.monotonic()+15
        while set(running.values()) != before_outputs and time.monotonic()<deadline:
            time.sleep(.25)
            running = icons.dock_applets()
        if set(running.values()) != before_outputs:
            raise RuntimeError('The dock has not returned on every original display.')
        for pid in running:
            if Path('/proc',str(pid),'exe').resolve() != target.resolve():
                raise RuntimeError('The dock is not using the compact applet.')
        state.update(status='applied',after={str(p):native.fingerprint(p) for p in updates},
                     dock_applets=running,icon_size=60,button_size=[66,72],trash_button_size=[60,72],icon_spacing=7)
        native.atomic(backup,json.dumps(state,indent=2),0o600)
        native.atomic(STATE/'latest',str(backup)+'\n',0o600)
    except BaseException:
        for name,entry in state['before'].items():
            native.restore_entry(Path(name),entry)
        reload()
        state['status']='rolled_back'
        native.atomic(backup,json.dumps(state,indent=2),0o600)
        raise
    print('Compact 60px dock icons loaded on '+', '.join(sorted(running.values()))+'.')
    print('Backup: '+str(backup))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['install','restore'])
    parser.add_argument('--binary',type=Path)
    parser.add_argument('--backup',type=Path)
    args=parser.parse_args()
    if args.action=='install':
        if not args.binary: parser.error('--binary is required for install')
        apply(args.binary)
    else:
        restore(args.backup or Path((STATE/'latest').read_text().strip()))
