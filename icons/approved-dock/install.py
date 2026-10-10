#!/usr/bin/env python3
"""Install the approved dock overlay; retain all original artwork and a backup."""
from pathlib import Path
import argparse
import base64
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from trash_state import atomic_write, desired_icon, icon_line, item_count
from trash_actions import launcher_actions

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get('XDG_DATA_HOME', Path.home()/'.local/share'))
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', Path.home()/'.config'))
THEME = 'Studio Dock'
DEST = DATA/'icons'/THEME
NATIVE = CONFIG/'cosmic/com.system76.CosmicTk/v1/icon_theme'
LAUNCHER = DATA/'applications/local-trash.desktop'
HELPER = DATA/'cosmic-studio/approved-dock/trash_state.py'
ACTIONS_HELPER = DATA/'cosmic-studio/approved-dock/trash_actions.py'
STATE = DATA/'cosmic-studio/approved-dock-backups'
UNITS = ('cosmic-studio-trash-icon.path', 'cosmic-studio-trash-icon.timer')
FAVORITES = CONFIG/'cosmic/com.system76.CosmicAppList/v1/favorites'
DOCK_PLUGINS = CONFIG/'cosmic/com.system76.CosmicPanel.Dock/v1/plugins_center'


def normalize_favorites(text):
    """Use installed desktop IDs without changing the pinned apps or order."""
    return text.replace('"Chatgpt"', '"chatgpt"').replace(
        '"darktable"', '"org.darktable.darktable"')


def dock_applets(proc=Path('/proc')):
    """Select only the app-list children of a COSMIC panel on dock surfaces."""
    found = {}
    for entry in proc.glob('[0-9]*'):
        try:
            command = entry.joinpath('cmdline').read_bytes().split(b'\0')[0].decode()
            if Path(command).name != 'cosmic-app-list':
                continue
            env = dict(value.split('=', 1) for value in
                       entry.joinpath('environ').read_text().split('\0') if '=' in value)
            if env.get('COSMIC_PANEL_NAME') != 'Dock':
                continue
            parent = next(line.split()[1] for line in
                          entry.joinpath('status').read_text().splitlines() if line.startswith('PPid:'))
            if (proc/parent/'exe').resolve().name != 'cosmic-panel':
                continue
            found[int(entry.name)] = env.get('COSMIC_PANEL_OUTPUT', '')
        except (FileNotFoundError, PermissionError, ProcessLookupError, StopIteration, UnicodeError):
            continue
    return found


def reload_dock_plugins(path=DOCK_PLUGINS):
    """Recreate the app list through the panel's configuration watcher."""
    original = path.read_bytes()
    temporary = original.replace(b'"com.system76.CosmicAppList",', b'')
    if temporary == original:
        raise RuntimeError('The dock app-list configuration was not recognized.')
    try:
        atomic_write(path, temporary)
        time.sleep(2)
    finally:
        atomic_write(path, original)


def refresh_dock():
    """Reload dock applets without restarting the panel or open applications."""
    before = dock_applets()
    if not before:
        print('No running COSMIC dock applets; icons will load when the dock starts.')
        return
    expected = Counter(before.values())
    reload_dock_plugins()
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        after = dock_applets()
        if not (set(after) & set(before)) and Counter(after.values()) == expected:
            print('Reloaded dock icons on '+', '.join(sorted(expected))+'.')
            return {'before': before, 'after': after}
        time.sleep(.25)
    raise RuntimeError('The dock applets have not finished restarting; icon assets remain installed.')


def run(*args):
    return subprocess.check_output(args, text=True).strip()


def record(path):
    if path.is_symlink():
        return {'link': os.readlink(path)}
    if not path.exists():
        return None
    return {'bytes': base64.b64encode(path.read_bytes()).decode(),
            'mode': path.stat().st_mode & 0o777}


def unit_enabled(unit):
    result = subprocess.run(['systemctl', '--user', 'is-enabled', unit], capture_output=True, text=True)
    return result.stdout.strip() == 'enabled'


def updates():
    source = ROOT/'theme'
    if not (source/'index.theme').is_file():
        raise RuntimeError('Build or copy the approved theme assets first.')
    out = {DEST/p.relative_to(source): p.read_bytes() for p in source.rglob('*') if p.is_file()}
    out[NATIVE] = ('"' + THEME + '"\n').encode()
    if FAVORITES.is_file():
        text = FAVORITES.read_text()
        corrected = normalize_favorites(text)
        if text != corrected:
            out[FAVORITES] = corrected.encode()
    out[HELPER] = (ROOT/'trash_state.py').read_bytes()
    out[ACTIONS_HELPER] = (ROOT/'trash_actions.py').read_bytes()
    if not LAUNCHER.exists():
        raise RuntimeError('Expected the existing local-trash.desktop launcher.')
    launcher = launcher_actions(LAUNCHER.read_text(), ACTIONS_HELPER)
    out[LAUNCHER] = icon_line(launcher, desired_icon(item_count())).encode()
    # Preserve absolute-icon launchers in user-local overrides, changing only Icon.
    system_overrides = ROOT.parent/'system-apps/launcher-overrides.json'
    if system_overrides.is_file():
        for entry in json.loads(system_overrides.read_text()):
            destination = DATA/'applications'/entry['desktop_id']
            source = destination if destination.is_file() else Path(entry['source'])
            text = icon_line(source.read_text(), entry['icon'])
            # NVIDIA's launchers use legacy boolean spelling; preserve its meaning.
            text = re.sub(r'(?m)^Terminal=No$', 'Terminal=false', text)
            out[destination] = text.encode()
    unitdir = CONFIG/'systemd/user'
    command = f'/usr/bin/python3 "{HELPER}"'
    out[unitdir/'cosmic-studio-trash-icon.service'] = (
        '[Unit]\nDescription=Update the COSMIC Studio trash icon\n\n'
        '[Service]\nType=oneshot\nExecStart=' + command + '\n').encode()
    out[unitdir/'cosmic-studio-trash-icon.path'] = (
        '[Unit]\nDescription=Watch Trash changes for the dock icon\n\n[Path]\n'
        f'PathChanged={DATA}/Trash/files\nPathChanged={DATA}/Trash/info\n'
        'Unit=cosmic-studio-trash-icon.service\n\n[Install]\nWantedBy=default.target\n').encode()
    out[unitdir/'cosmic-studio-trash-icon.timer'] = (
        '[Unit]\nDescription=Refresh the dock Trash state for removable volumes\n\n[Timer]\n'
        'OnStartupSec=3s\nOnUnitActiveSec=30s\nAccuracySec=2s\n'
        'Unit=cosmic-studio-trash-icon.service\n\n[Install]\nWantedBy=timers.target\n').encode()
    return out


def restore(manifest, force=False):
    data = json.loads(manifest.read_text())
    if not force:
        for name, expected in data.get('after', {}).items():
            current = record(Path(name))
            if Path(name) == LAUNCHER and current and expected and 'bytes' in current:
                actual_text = icon_line(base64.b64decode(current['bytes']).decode(), 'STATE')
                saved_text = icon_line(base64.b64decode(expected['bytes']).decode(), 'STATE')
                if actual_text == saved_text:
                    continue
            if current != expected:
                raise RuntimeError('Managed file changed; restore stopped: ' + name)
        current_theme = run('gsettings','get','org.gnome.desktop.interface','icon-theme')
        if current_theme != repr(THEME):
            raise RuntimeError('Icon theme changed after installation; restore stopped.')
    subprocess.run(['systemctl','--user','disable','--now',*UNITS], check=False, capture_output=True)
    for name, before in data['before'].items():
        path = Path(name)
        if before is None:
            # These are only files created by this installer, never user originals.
            path.unlink(missing_ok=True)
        elif 'link' in before:
            path.unlink(missing_ok=True)
            path.symlink_to(before['link'])
        else:
            atomic_write(path, base64.b64decode(before['bytes']))
            path.chmod(before['mode'])
    run('gsettings','set','org.gnome.desktop.interface','icon-theme',data['gsettings_before'])
    run('systemctl','--user','daemon-reload')
    for unit, enabled in data['units_before'].items():
        if enabled:
            run('systemctl','--user','enable','--now',unit)
    data['status'] = 'restored'
    manifest.write_text(json.dumps(data,indent=2)+'\n')
    print('Restored the previous icon files and preferences.')


def apply():
    changes = updates()
    current_theme = run('gsettings','get','org.gnome.desktop.interface','icon-theme')
    pending = {p:content for p,content in changes.items()
               if p.is_symlink() or not p.is_file() or p.read_bytes()!=content}
    if not pending and current_theme == repr(THEME):
        verify()
        refresh_dock()
        return
    STATE.mkdir(parents=True,exist_ok=True,mode=0o700)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    manifest = STATE/(stamp+'.json')
    state = {'status':'applying','theme':THEME,
             'gsettings_before':current_theme,
             'units_before':{unit:unit_enabled(unit) for unit in UNITS},
             'before':{str(p):record(p) for p in pending},'after':{}}
    manifest.write_text(json.dumps(state,indent=2)+'\n');manifest.chmod(0o600)
    try:
        for path, content in pending.items():
            atomic_write(path,content)
        if shutil.which('gtk-update-icon-cache'):
            subprocess.run(['gtk-update-icon-cache','--force','--ignore-theme-index',str(DEST)],check=True,capture_output=True)
        run('gsettings','set','org.gnome.desktop.interface','icon-theme',THEME)
        run('systemctl','--user','daemon-reload')
        run('systemctl','--user','enable','--now',*UNITS)
        run('systemctl','--user','start','cosmic-studio-trash-icon.service')
        state['after'] = {str(p):record(p) for p in pending}
        state['status'] = 'applied'
        manifest.write_text(json.dumps(state,indent=2)+'\n')
        (STATE/'latest').write_text(str(manifest)+'\n')
        (ROOT/'installation.local.json').write_text(json.dumps({'theme':THEME,'backup':str(manifest),'status':'applied'},indent=2)+'\n')
    except Exception:
        restore(manifest,force=True)
        raise
    verify()
    refresh_dock()
    print('Backup: '+str(manifest))


def verify():
    expected = updates()
    mismatches = [str(path) for path,content in expected.items()
                  if not path.is_file() or path.read_bytes()!=content]
    if mismatches:
        raise RuntimeError('Installation differs: '+', '.join(mismatches[:5]))
    if run('gsettings','get','org.gnome.desktop.interface','icon-theme') != repr(THEME):
        raise RuntimeError('GTK icon theme differs.')
    for unit in UNITS:
        if run('systemctl','--user','is-active',unit)!='active':
            raise RuntimeError('Trash state watcher is inactive.')
    print('Verified Studio Dock, native/GTK preferences, and automatic Trash states.')


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['apply','verify','restore'])
    parser.add_argument('--backup',type=Path)
    parser.add_argument('--force',action='store_true')
    options=parser.parse_args()
    if options.command=='apply':apply()
    elif options.command=='verify':verify()
    else:restore(options.backup or Path((STATE/'latest').read_text().strip()), options.force)
