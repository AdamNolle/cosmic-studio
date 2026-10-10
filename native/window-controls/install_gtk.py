#!/usr/bin/env python3
"""Install toolkit titlebuttons and exact conflict-aware recovery snapshots."""
from pathlib import Path
import argparse, importlib.util, json, os, re, subprocess, time
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('native_install',ROOT/'native/install.py')
native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
STATE=native.DATA/'window-controls'
MARKER='/* Studio window controls */'

def button_layout(text):
    setting='gtk-decoration-layout=:minimize,maximize,close\n'
    match=re.search(r'(?m)^\[Settings\][^\n]*\n(?:[^\[].*(?:\n|$)|\n)*',text)
    if not match:
        return '[Settings]\n'+setting+'\n'+text
    section=match.group()
    if re.search(r'(?m)^gtk-decoration-layout\s*=',section):
        section=re.sub(r'(?m)^gtk-decoration-layout\s*=.*(?:\n|$)',setting,section)
    else:
        section=section.rstrip()+'\n'+setting
    return text[:match.start()]+section+text[match.end():]

def changes():
    updates={}
    config=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))
    roots=[config]
    # App-private styles keep the existing Flatpak sandbox permissions intact.
    ids=subprocess.check_output(['flatpak','list','--app','--columns=application'],text=True).splitlines()
    for app in ids:
        if app in {'org.gimp.GIMP','org.darktable.Darktable','fr.handbrake.ghb'}:
            roots.append(Path.home()/'.var/app'/app/'config')
    for base in roots:
        for toolkit in ['gtk-3.0','gtk-4.0']:
            path=(base/toolkit/'settings.ini').resolve()
            updates[path]=button_layout(path.read_text() if path.is_file() else '').encode()
        assets=base/'gtk-4.0/studio-window-controls'
        updates[assets/'style.css']=(ROOT/'native/window-controls/gtk.css').read_bytes()
        for p in (ROOT/'icons/window-controls/svg').glob('*/*.svg'):
            updates[assets/'assets'/p.relative_to(ROOT/'icons/window-controls/svg')]=p.read_bytes()
        palettes={base/'gtk-3.0/gtk.css',base/'gtk-4.0/gtk.css'}
        palettes.update((base/'gtk-4.0/cosmic').glob('*.css'))
        for entry in palettes:
            path=entry.resolve()
            text=path.read_text() if path.exists() else ''
            if MARKER not in text:
                updates[path]=(text.rstrip()+'\n\n'+MARKER+'\n@import url("'+(assets/'style.css').as_uri()+'");\n').encode()
    zed=config/'zed/settings.json'
    if zed.is_file():
        settings=json.loads(zed.read_text())
        settings['window_decorations']='server'
        updates[zed]=(json.dumps(settings,indent=2)+'\n').encode()
    obsidian=config/'obsidian/obsidian.json'
    if obsidian.is_file():
        for vault in json.loads(obsidian.read_text()).get('vaults',{}).values():
            directory=Path(vault['path'])/'.obsidian'
            if not directory.is_dir():
                continue
            appearance=directory/'appearance.json'
            settings=json.loads(appearance.read_text()) if appearance.is_file() else {}
            enabled=settings.setdefault('enabledCssSnippets',[])
            if 'studio-window-controls' not in enabled:
                enabled.append('studio-window-controls')
            updates[appearance]=(json.dumps(settings,indent=2)+'\n').encode()
            updates[directory/'snippets/studio-window-controls.css']=(ROOT/'native/window-controls/obsidian.css').read_bytes()
    return updates

def install():
    updates={p:data for p,data in changes().items() if not p.is_file() or p.read_bytes()!=data}
    if not updates:
        print('Toolkit window controls are already current.');return
    backup=STATE/'backups'/str(time.time_ns())/'manifest.json'
    record={'before':{str(p):native.saved(p) for p in updates},'status':'applying'}
    native.atomic(backup,json.dumps(record,indent=2),0o600)
    try:
        for path,data in updates.items():
            mode=(path.stat().st_mode & 0o777) if path.exists() else 0o644
            native.atomic(path,data,mode)
        record.update(status='applied',after={str(p):native.fingerprint(p) for p in updates})
        native.atomic(backup,json.dumps(record,indent=2),0o600)
        native.atomic(STATE/'latest-gtk-backup',str(backup)+'\n',0o600)
    except BaseException:
        for name,entry in record['before'].items():native.restore_entry(Path(name),entry)
        record['status']='rolled-back';native.atomic(backup,json.dumps(record,indent=2),0o600)
        raise
    print('Installed GTK window controls. Backup: '+str(backup))

def restore(backup):
    data=json.loads(backup.read_text())
    for name,expected in data['after'].items():
        if native.fingerprint(Path(name))!=expected:raise RuntimeError('Later edits preserved; restore stopped: '+name)
    for name,entry in data['before'].items():native.restore_entry(Path(name),entry)
    data['status']='restored';native.atomic(backup,json.dumps(data,indent=2),0o600)
    print('Restored previous GTK styles.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['install','restore'])
    parser.add_argument('--backup',type=Path)
    args=parser.parse_args()
    if args.action=='install':install()
    else:restore(args.backup or Path((STATE/'latest-gtk-backup').read_text().strip()))
