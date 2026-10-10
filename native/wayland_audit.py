#!/usr/bin/env python3
"""Read-only evidence for this workstation's native rendering configuration."""
import argparse
import configparser
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess


LIVE_COMPONENTS = frozenset({
    'cosmic-session', 'cosmic-comp', 'cosmic-panel', 'cosmic-launcher',
    'cosmic-app-library', 'cosmic-workspaces', 'cosmic-greeter',
    'cosmic-files', 'cosmic-edit', 'cosmic-term', 'cosmic-settings',
    'ChatGPT', 'chatgpt', 'brave', 'brave-browser', 'ghostty', 'zed',
    'zed-editor', 'Xwayland',
})


def run(args):
    try:
        result = subprocess.run(args, text=True, capture_output=True, timeout=15)
        return {'ok': result.returncode == 0, 'output': result.stdout.strip(),
                'error': result.stderr.strip()[:600] if result.returncode else ''}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'ok': False, 'output': '', 'error': str(error)}


def launchers():
    data = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share')))
    directories = os.environ.get('XDG_DATA_DIRS', '/usr/local/share:/usr/share').split(':')
    roots = [Path(directory) / 'applications' for directory in reversed(directories) if directory]
    roots += [Path('/var/lib/flatpak/exports/share/applications'),
              data / 'flatpak/exports/share/applications', data / 'applications']
    entries = {}
    for root in roots:
        for path in root.glob('*.desktop'):
            parser = configparser.ConfigParser(interpolation=None, strict=False)
            try:
                parser.read(path)
                section = parser['Desktop Entry']
            except (configparser.Error, KeyError, UnicodeError):
                continue
            if section.get('Hidden') == 'true' or section.get('NoDisplay') == 'true':
                entries.pop(path.name, None)
                continue
            if section.get('Type', 'Application') != 'Application':
                continue
            command = section.get('Exec', '')
            try:
                executable = section.get('TryExec') or shlex.split(command)[0]
                available = bool(shutil.which(executable))
            except (ValueError, IndexError):
                available = False
            if '--ozone-platform=wayland' in command:
                backend = 'native Wayland requested by launcher'
            elif path.name.startswith('com.system76.') or 'cosmic-' in command:
                backend = 'COSMIC native client; live rendering still needs inspection'
            elif section.get('X-Flatpak'):
                backend = 'Flatpak: verify Wayland socket and runtime below'
            else:
                backend = 'toolkit default; do not infer rendering correctness from the launcher'
            entries[path.name] = {'id': path.name, 'name': section.get('Name', path.stem),
                                  'backend_evidence': backend, 'executable_available': available,
                                  'source': str(path)}
    return sorted(entries.values(), key=lambda row: row['name'].casefold())


def live_components(proc_root=Path('/proc')):
    rows = []
    for entry in proc_root.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            executable = os.readlink(entry / 'exe')
            deleted = executable.endswith(' (deleted)')
            deployed_path = executable.removesuffix(' (deleted)')
            name = Path(deployed_path).name
            if name not in LIVE_COMPONENTS:
                continue
            args = (entry / 'cmdline').read_bytes().split(b'\0')
            if any(arg.startswith(b'--type=') for arg in args):
                continue
            environment_error = ''
            try:
                env = dict(part.split(b'=', 1) for part in (entry / 'environ').read_bytes().split(b'\0') if b'=' in part)
            except OSError as error:
                env = {}
                environment_error = str(error)
            keys = [b'WAYLAND_DISPLAY', b'XDG_SESSION_TYPE', b'GDK_BACKEND', b'QT_QPA_PLATFORM',
                    b'COSMIC_STUDIO_GLASS', b'COSMIC_STUDIO_LIQUID_GLASS']
            rows.append({'pid': int(entry.name), 'process': name,
                         'comm': (entry / 'comm').read_text().strip(),
                         'exe': deployed_path, 'deployed_path': deployed_path,
                         'exe_deleted': deleted,
                         'wayland_requested': b'--ozone-platform=wayland' in args,
                         'environment_error': environment_error,
                         'environment': {key.decode(): env[key].decode(errors='replace') for key in keys if key in env}})
        except (OSError, ValueError):
            continue
    return sorted(rows, key=lambda row: row['pid'])


def audit():
    displays = run(['cosmic-randr', 'list'])
    displays['output'] = re.sub(r'\x1b\[[0-9;]*m', '', displays['output'])
    flatpaks = {}
    listing = run(['flatpak', 'list', '--app', '--columns=application'])
    if listing['ok']:
        for app in listing['output'].splitlines():
            permissions = run(['flatpak', 'info', app, '--show-permissions'])
            flatpaks[app] = {'permissions_available': permissions['ok'],
                             'wayland_socket': bool(re.search(r'^sockets=.*\bwayland;', permissions['output'], re.M)),
                             'fallback_x11': 'fallback-x11;' in permissions['output'],
                             'error': permissions['error']}
    qt = {version: bool(list(Path(f'/usr/lib/x86_64-linux-gnu/qt{version}/plugins/platforms').glob('libqwayland*')))
          for version in (5, 6)}
    x11 = run(['xlsclients', '-l'])
    return {'session': os.environ.get('XDG_SESSION_TYPE'), 'display_configuration': displays,
            'native_components': live_components(), 'qt_wayland_plugins': qt,
            'flatpak_wayland': flatpaks, 'launchers': launchers(),
            'x11_clients': x11,
            'font_resolution': {face: run(['fc-match', '-f', '%{family} | %{style}\n', face])
                                for face in ('Archivo', 'Instrument Serif', 'iA Writer Mono S')},
            'limits': ['Backend settings and protocol availability do not prove that every application renders correctly.',
                       'xlsclients lists X11 clients that expose WM_COMMAND, not every possible Xwayland surface.',
                       'Unlaunched applications, popup behavior, fractional scaling and color-managed content need actual visual checks.',
                       'Toolkit fallback is retained for applications without native Wayland support.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(f"Audited {len(report['launchers'])} launchers; report: {args.output}")
    print(f"Session: {report['session']}; Qt Wayland plugins: {report['qt_wayland_plugins']}")
    print('Pending: actual application states and login persistence.')
