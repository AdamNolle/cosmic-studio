#!/usr/bin/env python3
"""Install verified native candidates for the next session; restore exact files."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import tempfile
import time

DATA = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))) / 'cosmic-studio'
BIN = Path.home() / '.local/bin'
REVISIONS = {'cosmic-panel': 'b5cc19e', 'cosmic-comp': '0fbd457',
             'cosmic-launcher': 'cc3d42b', 'cosmic-app-library': '0a3996d',
             'cosmic-workspaces': '28e257d', 'cosmic-greeter': 'bfb2745',
             'cosmic-files': 'd1f0af7', 'cosmic-edit': 'bfc98bf',
    'cosmic-term': '9129277', 'cosmic-settings': '7421ff0',
    'cosmic-store': 'c6e57a1', 'cosmic-monitor': 'fdcc323',
    'cosmic-player': '66b3f34', 'cosmic-viewer': 'd820ab3'}
WINDOW_COMPONENTS = frozenset(('cosmic-files', 'cosmic-settings', 'cosmic-store',
                               'cosmic-monitor', 'cosmic-player', 'cosmic-viewer'))

# Keep each argv[0] basename: the native applet ELF is a multicall executable.
APPLET_NAMES = ('cosmic-app-list', 'cosmic-panel-button') + tuple(
    'cosmic-applet-' + name for name in
    ('a11y', 'audio', 'battery', 'bluetooth', 'minimize', 'network', 'notifications',
     'osk', 'power', 'status-area', 'tiling', 'time', 'workspaces', 'input-sources'))
MULTICALL_NAMES = tuple(name for name in APPLET_NAMES if name != 'cosmic-panel-button')
PACKAGE_NAMES = {name: 'cosmic-applets' for name in APPLET_NAMES}
PACKAGE_NAMES['cosmic-studio-dock-separator'] = 'cosmic-applets'
REVISIONS.update({name: '82e7cd8' for name in PACKAGE_NAMES})
REVISIONS.update({'cosmic-notifications': 'aa4dac2', 'cosmic-osd': '3faadf5'})
PACKAGE_NAMES['cosmic-files-applet'] = 'cosmic-files'
REVISIONS['cosmic-files-applet'] = 'd1f0af7'


def fingerprint(path):
    if path.is_symlink():
        return {'kind': 'symlink', 'target': os.readlink(path)}
    if path.is_file():
        return {'kind': 'file', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'mode': stat.S_IMODE(path.stat().st_mode)}
    if path.exists():
        raise RuntimeError(f'Expected a file: {path}')
    return None


def saved(path):
    entry = fingerprint(path)
    if entry and entry['kind'] == 'file':
        entry['data'] = base64.b64encode(path.read_bytes()).decode()
    return entry


def atomic(path, data, mode=0o700):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.studio-native-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data if isinstance(data, bytes) else data.encode())
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def restore_entry(path, entry):
    if entry is None:
        path.unlink(missing_ok=True)
    elif entry['kind'] == 'symlink':
        path.unlink(missing_ok=True)
        path.symlink_to(entry['target'])
    else:
        atomic(path, base64.b64decode(entry['data']), entry['mode'])


def wrapper_for(component, target, version, system_binary=None):
    """Use this candidate only while the installed package version still matches."""
    system_binary = system_binary or Path('/usr/bin') / component
    variable = {'cosmic-panel': 'COSMIC_STUDIO_GLASS',
                'cosmic-comp': 'COSMIC_STUDIO_LIQUID_GLASS'}.get(component)
    script = '#!/bin/sh\n# COSMIC Studio native candidate; restore with native/install.py.\n'
    script += 'unset COSMIC_STUDIO_WINDOW_GLASS\n'
    script += ('studio_package_version=$(dpkg-query -W -f=\'${Version}\' '
               + shlex.quote(PACKAGE_NAMES.get(component, component)) + ' 2>/dev/null) || studio_package_version=\'\'\n')
    script += (f'if [ -x {shlex.quote(str(target))} ] && '
               f'[ "$studio_package_version" = {shlex.quote(version)} ]; then\n')
    if variable:
        script += f'    export {variable}=1\n'
    if component != 'cosmic-comp':
        script += '    export COSMIC_STUDIO_POPUP_GLASS=1\n'
    if component == 'cosmic-app-list':
        script += '    export COSMIC_STUDIO_COMPACT_DOCK=1\n'
    if component in WINDOW_COMPONENTS:
        script += '    export COSMIC_STUDIO_WINDOW_GLASS=1\n'
    script += f'    exec {shlex.quote(str(target))} "$@"\nfi\n'
    if component == 'cosmic-studio-dock-separator' and system_binary == Path('/usr/bin') / component:
        script += 'exec /usr/bin/cosmic-panel-button local-dock-divider "$@"\n'
    else:
        script += f'exec {shlex.quote(str(system_binary))} "$@"\n'
    return script


def install(candidates):
    if os.geteuid() == 0:
        raise RuntimeError('Run as the desktop user.')
    prepared = []
    artifacts = {}
    for component, source in candidates.items():
        source = source.resolve()
        with source.open('rb') as stream:
            if stream.read(4) != b'\x7fELF':
                raise RuntimeError(f'Candidate is not an ELF executable: {source}')
        if not os.access(source, os.X_OK):
            raise RuntimeError(f'Candidate is not executable: {source}')
        version = subprocess.check_output(
            ['dpkg-query', '-W', '-f=${Version}', PACKAGE_NAMES.get(component, component)], text=True).strip()
        if REVISIONS[component] not in version:
            raise RuntimeError(f'{component} changed ({version}); rebuild against the installed revision.')
        target = DATA / 'bin' / component
        artifact = DATA / 'bin/cosmic-applets' if component in MULTICALL_NAMES else target
        data = source.read_bytes()
        if artifact in artifacts and artifacts[artifact] != data:
            raise RuntimeError(f'Conflicting multicall candidates for {artifact}')
        artifacts[artifact] = data
        wrapper = BIN / component
        script = wrapper_for(component, target, version)
        prepared.append((component, source, target, wrapper, script, version))
    directory = DATA / 'native-backups' / f'{time.time_ns()}'
    directory.mkdir(parents=True, mode=0o700)
    manifest = {'schema': 1, 'before': {}, 'after': {}, 'versions': {}, 'status': 'applying'}
    for artifact in artifacts:
        manifest['before'][str(artifact)] = saved(artifact)
    for component, source, target, wrapper, script, version in prepared:
        for path in (target, wrapper):
            manifest['before'][str(path)] = saved(path)
        manifest['versions'][component] = version
    report = directory / 'manifest.json'
    atomic(report, json.dumps(manifest, indent=2), 0o600)
    try:
        for artifact, data in artifacts.items():
            atomic(artifact, data, 0o755)
        for component, source, target, wrapper, script, version in prepared:
            if component in MULTICALL_NAMES:
                # Share one executable inode and its read-only mapped pages.
                # Invoking this alias still supplies its basename in argv[0].
                fd, temporary = tempfile.mkstemp(prefix='.studio-native-', dir=target.parent)
                os.close(fd)
                os.unlink(temporary)
                try:
                    os.symlink('cosmic-applets', temporary)
                    os.replace(temporary, target)
                finally:
                    Path(temporary).unlink(missing_ok=True)
            atomic(wrapper, script, 0o755)
        manifest['after'] = {p: fingerprint(Path(p)) for p in manifest['before']}
        manifest['status'] = 'applied'
        atomic(report, json.dumps(manifest, indent=2), 0o600)
    except BaseException:
        for path, entry in manifest['before'].items():
            restore_entry(Path(path), entry)
        manifest['status'] = 'rolled-back'
        atomic(report, json.dumps(manifest, indent=2), 0o600)
        raise
    atomic(DATA / 'latest-native-backup', str(report), 0o600)
    return report


def restore(report, force=False):
    manifest = json.loads(report.read_text())
    if manifest['status'] != 'applied':
        raise RuntimeError('This installation is not active.')
    changed = [p for p, entry in manifest['after'].items() if fingerprint(Path(p)) != entry]
    if changed and not force:
        raise RuntimeError('Later changes are protected: ' + ', '.join(changed))
    for path, entry in manifest['before'].items():
        restore_entry(Path(path), entry)
    manifest['status'] = 'restored'
    atomic(report, json.dumps(manifest, indent=2), 0o600)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'restore'])
    parser.add_argument('--panel-binary', type=Path)
    parser.add_argument('--compositor-binary', type=Path)
    parser.add_argument('--launcher-binary', type=Path)
    parser.add_argument('--library-binary', type=Path)
    parser.add_argument('--workspaces-binary', type=Path)
    parser.add_argument('--greeter-binary', type=Path)
    parser.add_argument('--files-binary', type=Path)
    parser.add_argument('--desktop-binary', type=Path)
    parser.add_argument('--editor-binary', type=Path)
    parser.add_argument('--terminal-binary', type=Path)
    parser.add_argument('--settings-binary', type=Path)
    parser.add_argument('--store-binary', type=Path)
    parser.add_argument('--monitor-binary', type=Path)
    parser.add_argument('--player-binary', type=Path)
    parser.add_argument('--viewer-binary', type=Path)
    parser.add_argument('--applets-binary', type=Path)
    parser.add_argument('--panel-button-binary', type=Path)
    parser.add_argument('--notifications-binary', type=Path)
    parser.add_argument('--osd-binary', type=Path)
    parser.add_argument('--separator-binary', type=Path)
    parser.add_argument('--backup', type=Path)
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    if args.action == 'install':
        candidates = {name: path for name, path in
                      [('cosmic-panel', args.panel_binary), ('cosmic-comp', args.compositor_binary),
                       ('cosmic-launcher', args.launcher_binary), ('cosmic-app-library', args.library_binary),
                       ('cosmic-workspaces', args.workspaces_binary), ('cosmic-greeter', args.greeter_binary),
                       ('cosmic-files', args.files_binary), ('cosmic-edit', args.editor_binary),
                       ('cosmic-term', args.terminal_binary), ('cosmic-settings', args.settings_binary),
                       ('cosmic-store', args.store_binary), ('cosmic-monitor', args.monitor_binary),
                       ('cosmic-player', args.player_binary), ('cosmic-viewer', args.viewer_binary)] if path}
        if args.applets_binary:
            candidates.update({name: args.applets_binary for name in MULTICALL_NAMES})
        for name, path in [('cosmic-panel-button', args.panel_button_binary),
                           ('cosmic-files-applet', args.desktop_binary),
                           ('cosmic-notifications', args.notifications_binary), ('cosmic-osd', args.osd_binary),
                           ('cosmic-studio-dock-separator', args.separator_binary)]:
            if path:
                candidates[name] = path
        if not candidates:
            parser.error('Provide at least one compiled candidate.')
        report = install(candidates)
        print(f'Native candidates installed. Backup: {report}')
        print('The compositor activates at the next login. This command does not stop the running session.')
    else:
        report = args.backup or Path((DATA / 'latest-native-backup').read_text())
        restore(report, args.force)
        print(f'Exact native files restored from {report}; running processes are unchanged.')


if __name__ == '__main__':
    main()
