#!/usr/bin/env python3
"""Reversible, version-matched COSMIC and application appearance setup.

Only appearance settings are changed. No motion or third-party app patches.
"""
import argparse
import base64
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import uuid

PACKAGE = Path(__file__).resolve().parent
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config')))
COSMIC = CONFIG/'cosmic'
DATA = Path(os.environ.get('XDG_DATA_HOME', str(Path.home()/'.local/share')))
BACKUPS = PACKAGE/'backups'
SCHEMA_VERSION = 1
GSETTINGS = [('org.gnome.desktop.interface','color-scheme'),
             ('org.gnome.desktop.interface','gtk-theme'),
             ('org.gnome.desktop.interface','font-name'),
             ('org.gnome.desktop.interface','document-font-name')]
FONT_GSETTINGS = GSETTINGS[2:]
INTERFACE_FONT = '(family: "Archivo", weight: Normal, stretch: Normal, style: Normal)'
CAFFEINE_FLATPAK_ID = 'com.github.codevardhan.caffeine-applet'
SHELL_FROSTED = 'ExtremelyLow'
CORNER_RADII = {'0': 0.0, 'xs': 2.0, 's': 4.0, 'm': 6.0, 'l': 8.0, 'xl': 10.0}
DOCK = {'background':'Dark','border_radius':'6','border_width':'0','size':'M','padding':'0','spacing':'4','anchor_gap':'true',
        'margin':'8','opacity':'0.86','autohide':'Always','keep_style_on_maximize':'true'}
PANEL = {'background':'Dark','border_radius':'6','border_width':'0','opacity':'0.92','margin':'8','anchor_gap':'true','expand_to_edges':'true','autohide':'Never','keep_style_on_maximize':'false'}

def run(args, timeout=30, check=True):
    env=os.environ.copy()
    env.update(LANG='en_US.UTF-8',LC_ALL='en_US.UTF-8')
    result=subprocess.run([str(a) for a in args],capture_output=True,text=True,timeout=timeout,env=env)
    if check and result.returncode:
        raise RuntimeError(f'{args[0]} failed ({result.returncode}): '+(result.stderr or result.stdout)[-1600:])
    return result

def atomic(path, data, mode=None):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    if mode is None:
        mode=stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    fd,name=tempfile.mkstemp(prefix='.studio-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(data if isinstance(data,bytes) else data.encode())
            f.flush(); os.fsync(f.fileno())
        os.chmod(name,mode)
        os.replace(name,path)
    finally:
        if os.path.exists(name): os.unlink(name)

def appearance_roots():
    roots=[COSMIC/f'com.system76.CosmicTheme.{s}' for s in
           ['Dark','Light','Dark.Builder','Light.Builder','Mode']]
    for group,settings in [('Dock',DOCK),('Panel',PANEL)]:
        roots.extend(COSMIC/f'com.system76.CosmicPanel.{group}/v1'/key for key in settings)
    roots += [CONFIG/'gtk-3.0',CONFIG/'gtk-4.0',CONFIG/'qt5ct',CONFIG/'qt6ct',
              CONFIG/'kdeglobals',DATA/'color-schemes/CosmicLight.colors',DATA/'color-schemes/CosmicDark.colors',
              CONFIG/'ghostty/config.ghostty', CONFIG/'ghostty/appearance.ghostty',CONFIG/'ghostty/themes/Studio Light',
              CONFIG/'ghostty/themes/Studio Dark',
              CONFIG/'zed/settings.json',CONFIG/'zed/themes/studio-light.json',CONFIG/'GIMP/2.10/gimprc',
              CONFIG/'studio-light/glass-gtk.css',CONFIG/'studio-light/glass-qt.qss',
              CONFIG/'studio-light/ghostty-dark.css']
    roots += typography_roots()
    if shutil.which('blender'):
        text=run(['blender','--version']).stdout
        m=re.search(r'Blender (\d+\.\d+)',text)
        if m: roots.append(CONFIG/f'blender/{m.group(1)}/config/userpref.blend')
    return roots

def font_assets():
    """Check pinned originals before they enter the desktop's font cache."""
    manifest=json.loads((PACKAGE/'fonts/manifest.json').read_text())
    files=[]
    for family,entries in manifest['families'].items():
        for entry in entries:
            name=Path(entry['file'])
            if name.is_absolute() or '..' in name.parts:
                raise RuntimeError('Unsafe font asset path.')
            source=PACKAGE/'fonts'/name
            if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest()!=entry['sha256']:
                raise RuntimeError('Font asset checksum mismatch: '+str(name))
            files.append((source,DATA/'fonts/cosmic-studio'/name))
    return files

def private_flatpak_font_roots():
    """Caffeine cannot read host CosmicTk; keep its sandbox permissions intact."""
    installed = any((base/CAFFEINE_FLATPAK_ID).is_dir() for base in
                    [DATA/'flatpak/app',Path('/var/lib/flatpak/app')])
    if not installed:
        return []
    return [Path.home()/'.var/app'/CAFFEINE_FLATPAK_ID/'config/cosmic/com.system76.CosmicTk/v1/interface_font']

def typography_roots():
    roots=[COSMIC/'com.system76.CosmicTk/v1/interface_font',DATA/'fonts/cosmic-studio',
           CONFIG/'fontconfig/conf.d/60-cosmic-studio-fonts.conf',
           CONFIG/'gtk-3.0/settings.ini',CONFIG/'gtk-4.0/settings.ini',
           CONFIG/'qt5ct/qt5ct.conf',CONFIG/'qt6ct/qt6ct.conf',CONFIG/'kdeglobals',
           CONFIG/'zed/settings.json',CONFIG/'studio-light/typography-gtk.css',
           CONFIG/'studio-light/typography-qt.qss']
    # COSMIC owns these symlinks. Snapshot targets as well as links before appending CSS.
    for toolkit in ['gtk-3.0','gtk-4.0']:
        path=CONFIG/toolkit/'gtk.css'
        roots += [path,path.resolve()]
    roots += window_frame_targets()
    roots += private_flatpak_font_roots()
    return roots

def ini_value(text,section,key,value):
    """Replace one toolkit key; keep comments, unrelated keys and section ordering."""
    marker=re.search(r'^\['+re.escape(section)+r'\][ \t]*$',text,flags=re.M)
    if not marker: return text.rstrip()+'\n\n['+section+']\n'+key+'='+value+'\n'
    start=marker.end()
    match=re.search(r'^\[',text[start:],flags=re.M)
    end=start+match.start() if match else len(text)
    body=text[start:end]
    pattern=re.compile(r'^'+re.escape(key)+r'=[^\n]*$',flags=re.M)
    if pattern.search(body): body=pattern.sub(lambda _:key+'='+value,body)
    else: body='\n'+key+'='+value+'\n'+body.lstrip('\n')
    return text[:start]+body+text[end:]

def font_size(value,fallback='11'):
    match=re.search(r'(\d+(?:\.\d+)?)\s*[\'\"]?$',value)
    return match.group(1) if match else fallback

def qt_font_value(text,size):
    match=re.search(r'^general=([^\n]*)$',text,flags=re.M)
    if match and ',' in match.group(1):
        fields=match.group(1).split(','); fields[0]='Archivo'
        return ','.join(fields)
    return f'Archivo,{size},-1,5,50,0,0,0,0,0'

def append_css_import(path,asset,marker):
    target=path.resolve()
    old=target.read_text() if target.is_file() else ''
    old=re.sub(r'\n?/\* BEGIN '+marker+r' \*/.*?/\* END '+marker+r' \*/\n?', '',old,flags=re.S)
    suffix='\n/* BEGIN '+marker+' */\n@import url("'+str(asset)+'");\n/* END '+marker+' */\n'
    atomic(target,old.rstrip('\n')+suffix)

def window_frame_targets():
    """Follow existing COSMIC-owned links and cover both native palettes."""
    targets={(CONFIG/toolkit/'gtk.css').resolve() for toolkit in ['gtk-3.0','gtk-4.0']}
    for toolkit in ['gtk-3.0','gtk-4.0']:
        for mode in ['light','dark']:
            path=CONFIG/toolkit/'cosmic'/f'{mode}.css'
            if path.is_file(): targets.add(path.resolve())
    return sorted(targets)

def window_frame_roots():
    return [CONFIG/'studio-light/window-frames.css',
            CONFIG/'gtk-3.0/gtk.css',CONFIG/'gtk-4.0/gtk.css',*window_frame_targets()]

def apply_window_frame_imports():
    asset=CONFIG/'studio-light/window-frames.css'
    for path in window_frame_targets(): append_css_import(path,asset,'STUDIO WINDOW FRAMES')

def apply_typography_imports():
    asset=CONFIG/'studio-light/typography-gtk.css'
    for path in window_frame_targets(): append_css_import(path,asset,'STUDIO TYPOGRAPHY')

def verify_window_frames(directory=None):
    checks=[]
    def add(name,condition,details=''):
        checks.append({'check':name,'status':'PASS' if condition else 'FAIL','details':details})
    source=PACKAGE/'window-frames.css';asset=CONFIG/'studio-light/window-frames.css'
    add('Outer-frame stylesheet matches reviewed source',asset.is_file() and source.read_bytes()==asset.read_bytes(),str(asset))
    for path in window_frame_targets():
        text=path.read_text() if path.is_file() else ''
        add('GTK frame import '+str(path),text.count('/* BEGIN STUDIO WINDOW FRAMES */')==1 and str(asset) in text)
    if directory:
        manifest=json.loads((directory/'manifest.json').read_text())
        for name,original in manifest.get('preserved',{}).items():
            add('Independent setting preserved '+name,record(Path(name))==original)
    checks.append({'check':'Existing application frame refresh','status':'PENDING',
                   'details':'GTK/Chromium may cache decoration assets until a theme refresh or their next launch. No applications were closed or restarted.'})
    return checks

def apply_window_frames_only():
    """Remove application frame strokes independently of shell and app presets."""
    if os.geteuid()==0: raise RuntimeError('Run as the desktop user, not root.')
    source=PACKAGE/'window-frames.css'
    if not source.is_file(): raise RuntimeError('Missing reviewed outer-frame stylesheet.')
    roots=window_frame_roots()
    preserved=[COSMIC/'com.system76.CosmicTk/v1/interface_font',
               COSMIC/'com.system76.CosmicAppList/v1/favorites',
               COSMIC/'com.system76.CosmicTheme.Mode/v1/is_dark',
               CONFIG/'gtk-3.0/settings.ini',CONFIG/'gtk-4.0/settings.ini',
               CONFIG/'qt5ct/qt5ct.conf',CONFIG/'qt6ct/qt6ct.conf',
               CONFIG/'ghostty/appearance.ghostty',CONFIG/'zed/settings.json']
    for group,settings in [('Dock',DOCK),('Panel',PANEL)]:
        preserved.extend(COSMIC/f'com.system76.CosmicPanel.{group}/v1'/key for key in settings)
    BACKUPS.mkdir(exist_ok=True,mode=0o700)
    directory=BACKUPS/(datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-frames-'+uuid.uuid4().hex[:6])
    directory.mkdir(mode=0o700)
    manifest={'schema':SCHEMA_VERSION,'profile':'window_frames','status':'applying',
              'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'roots':[str(p) for p in roots],'before':snapshot(roots),'changed':[],
              'gsettings':{},'preserved':{str(path):record(path) for path in preserved}}
    save_manifest(directory,manifest)
    try:
        atomic(CONFIG/'studio-light/window-frames.css',source.read_bytes(),0o644)
        apply_window_frame_imports()
        after=snapshot(roots)
        manifest['changed']=sorted(k for k in manifest['before'].keys()|after.keys() if manifest['before'].get(k)!=after.get(k))
        manifest['after_hashes']={k:hashlib.sha256(json.dumps(after.get(k),sort_keys=True).encode()).hexdigest() for k in manifest['changed']}
        manifest['status']='applied';save_manifest(directory,manifest)
        checks=verify_window_frames(directory)
        atomic(PACKAGE/'window-frames-verification.json',json.dumps(checks,indent=2)+'\n')
        if any(c['status']=='FAIL' for c in checks): raise RuntimeError('Outer-frame verification failed.')
        atomic(PACKAGE/'latest-window-frames-backup.txt',str(directory)+'\n')
        print('Applied outer-frame styling. Backup: '+str(directory))
        print('Restore: python3 '+str(PACKAGE/'setup.py')+' restore '+str(directory))
    except Exception:
        manifest['status']='applying';save_manifest(directory,manifest)
        restore(directory,force=True)
        raise

def apply_typography():
    if (DATA/'fonts/cosmic-studio').is_symlink():
        raise RuntimeError('Managed font directory is a symlink; refusing an incomplete backup.')
    if not shutil.which('fc-cache') or not shutil.which('fc-match'):
        raise RuntimeError('Fontconfig fc-cache and fc-match are required.')
    for source,target in font_assets(): atomic(target,source.read_bytes(),0o644)
    atomic(CONFIG/'fontconfig/conf.d/60-cosmic-studio-fonts.conf',
           (PACKAGE/'fonts/fontconfig.conf').read_bytes(),0o644)
    run(['fc-cache','-f',DATA/'fonts/cosmic-studio'],timeout=60)
    for family in ['Archivo','Instrument Serif']:
        matched=run(['fc-match','-f','%{family}',family]).stdout
        if family not in matched.split(','):
            raise RuntimeError('Fontconfig did not load '+family+': '+matched)
    atomic(COSMIC/'com.system76.CosmicTk/v1/interface_font',INTERFACE_FONT)
    for path in private_flatpak_font_roots():
        atomic(path,INTERFACE_FONT)
    current=run(['gsettings','get','org.gnome.desktop.interface','font-name']).stdout.strip()
    size=font_size(current)
    run(['gsettings','set','org.gnome.desktop.interface','font-name','Archivo '+size])
    doc=run(['gsettings','get','org.gnome.desktop.interface','document-font-name']).stdout.strip()
    run(['gsettings','set','org.gnome.desktop.interface','document-font-name','Archivo '+font_size(doc)])
    for toolkit in ['gtk-3.0','gtk-4.0']:
        path=CONFIG/toolkit/'settings.ini'
        old=path.read_text() if path.is_file() else ''
        existing=re.search(r'^gtk-font-name=([^\n]*)$',old,flags=re.M)
        gtk_size=font_size(existing.group(1)) if existing else size
        atomic(path,ini_value(old,'Settings','gtk-font-name','Archivo '+gtk_size))
    for toolkit in ['qt5ct','qt6ct']:
        path=CONFIG/toolkit/f'{toolkit}.conf'
        old=path.read_text() if path.is_file() else ''
        atomic(path,ini_value(old,'Fonts','general',qt_font_value(old,size)))
    path=CONFIG/'kdeglobals'
    old=path.read_text() if path.is_file() else ''
    old_font=re.search(r'^font=([^\n]*)$',old,flags=re.M)
    value=old_font.group(1).split(',') if old_font else [f'Archivo,{size},-1,5,50,0,0,0,0,0']
    if old_font: value[0]='Archivo'
    atomic(path,ini_value(old,'General','font',','.join(value)))
    path=CONFIG/'zed/settings.json'
    settings=json.loads(path.read_text()) if path.is_file() else {}
    settings['ui_font_family']='Archivo'
    atomic(path,json.dumps(settings,indent=2)+'\n')
    for name in ['typography-gtk.css','typography-qt.qss']:
        atomic(CONFIG/'studio-light'/name,(PACKAGE/name).read_bytes(),0o644)
    # Cover inactive native palettes too: GTK changes the owned link on a mode
    # switch, so decorating only today's target loses semantic display fonts.
    apply_typography_imports()
    for toolkit in ['qt5ct','qt6ct']:
        path=CONFIG/toolkit/f'{toolkit}.conf'
        atomic(path,ini_stylesheet(path.read_text(),CONFIG/'studio-light/typography-qt.qss'))
    if (CONFIG/'studio-light/window-frames.css').is_file(): apply_window_frame_imports()

def apply_typography_only():
    """Install fonts and roles using the same conflict-aware recovery as full setup."""
    if os.geteuid()==0: raise RuntimeError('Run as the desktop user, not root.')
    font_assets()
    if (DATA/'fonts/cosmic-studio').is_symlink():
        raise RuntimeError('Managed font directory is a symlink; refusing an incomplete backup.')
    path=CONFIG/'zed/settings.json'
    if path.is_file(): json.loads(path.read_text())
    BACKUPS.mkdir(exist_ok=True,mode=0o700)
    directory=BACKUPS/(datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-fonts-'+uuid.uuid4().hex[:6])
    directory.mkdir(mode=0o700)
    roots=typography_roots()
    manifest={'schema':SCHEMA_VERSION,'profile':'typography','status':'applying',
              'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'roots':[str(p) for p in roots],'before':snapshot(roots),'changed':[],
              'gsettings':{s+'/'+k:run(['gsettings','get',s,k]).stdout.strip() for s,k in FONT_GSETTINGS},
              'preserved':{str(path):record(path) for path in [
                  COSMIC/'com.system76.CosmicTk/v1/icon_theme',
                  COSMIC/'com.system76.CosmicTk/v1/monospace_font',
                  COSMIC/'com.system76.CosmicAppList/v1/favorites']}}
    save_manifest(directory,manifest)
    try:
        apply_typography()
        after=snapshot(roots)
        manifest['changed']=sorted(k for k in manifest['before'].keys()|after.keys()
                                  if manifest['before'].get(k)!=after.get(k))
        manifest['after_hashes']={k:hashlib.sha256(json.dumps(after.get(k),sort_keys=True).encode()).hexdigest()
                                  for k in manifest['changed']}
        manifest['status']='applied';save_manifest(directory,manifest)
        checks=verify_typography(directory)
        atomic(PACKAGE/'typography-verification.json',json.dumps(checks,indent=2)+'\n')
        if any(c['status']=='FAIL' for c in checks):
            raise RuntimeError('Typography verification failed.')
        atomic(PACKAGE/'latest-typography-backup.txt',str(directory)+'\n')
        print('Applied typography. Backup: '+str(directory))
        print('Restore: python3 '+str(PACKAGE/'setup.py')+' restore '+str(directory))
    except Exception:
        manifest['status']='applying';save_manifest(directory,manifest)
        restore(directory,force=True)
        raise

def record(path):
    if path.is_symlink(): return {'kind':'symlink','target':os.readlink(path)}
    if not path.is_file(): return None
    return {'kind':'file','data':base64.b64encode(path.read_bytes()).decode(),
            'mode':stat.S_IMODE(path.stat().st_mode)}

def snapshot(roots):
    out={}
    for root in roots:
        if root.is_symlink() or root.is_file(): out[str(root)]=record(root)
        elif root.is_dir():
            for path in root.rglob('*'):
                if path.is_file() or path.is_symlink(): out[str(path)]=record(path)
    return out

def preflight(include_apps=True):
    if os.geteuid()==0: raise RuntimeError('Run as the desktop user, not root.')
    for command in ['cosmic-settings','gsettings']:
        if not shutil.which(command): raise RuntimeError(f'Missing command: {command}')
    for mode in ['Light','Dark']:
        if not (COSMIC/f'com.system76.CosmicTheme.{mode}.Builder/v2').is_dir():
            raise RuntimeError('This package requires the COSMIC theme v2 installation used to prepare it.')
    # The prepared native themes preserve installation-specific spacing and palette fields.
    if not (PACKAGE/'installation.json').is_file():
        raise RuntimeError('Run "python3 setup.py prepare" to match these themes to this installation first.')
    prepared=json.loads((PACKAGE/'installation.json').read_text())
    current=run(['dpkg-query','-W','-f=${Version}','cosmic-settings']).stdout.strip()
    if current!=prepared['cosmic_settings_version']:
        raise RuntimeError('COSMIC Settings changed since this package was prepared. Regenerate themes before applying.')
    if not include_apps:
        for filename in ['studio-dark.ron','studio-light.ron']:
            if not (PACKAGE/filename).is_file(): raise RuntimeError('Missing asset: '+filename)
        return
    font_assets()
    for filename in ['studio-dark.ron','studio-light.ron','Studio Dark.ghostty',
                     'appearance.ghostty','studio-light-zed.json','studio-light-obsidian.css','glass-gtk.css','glass-qt.qss',
                     'typography-gtk.css','typography-qt.qss','ghostty-dark.css']:
        if not (PACKAGE/filename).is_file(): raise RuntimeError('Missing asset: '+filename)
    zed=CONFIG/'zed/settings.json'
    if zed.exists():
        try: json.loads(zed.read_text())
        except json.JSONDecodeError:
            raise RuntimeError('Zed settings contain comments or invalid JSON; refusing to replace them automatically.')
    # Do not overwrite binary preferences currently owned by a running Blender.
    if run(['pgrep','-x','blender'],check=False).returncode==0:
        raise RuntimeError('Close Blender before applying its appearance preset; unsaved work is preserved.')

def save_manifest(directory, manifest):
    atomic(directory/'manifest.json',json.dumps(manifest,indent=2)+'\n',0o600)

def prepare():
    """Generate native RON from the local schema, without changing the desktop."""
    for mode in ['Light','Dark']:
        root=COSMIC/f'com.system76.CosmicTheme.{mode}.Builder/v2'
        if not root.is_dir(): raise RuntimeError('COSMIC v2 theme configuration is required.')
        values={p.name:p.read_text().strip() for p in root.iterdir() if p.is_file()}
        light=mode=='Light'
        colors={'bg_color':'#F5F5F7' if light else '#000000',
                'primary_container_bg':'#FFFFFF' if light else '#030405',
                'secondary_container_bg':'#ECECEF' if light else '#0D1117',
                'text_tint':'#202024' if light else '#F0F1F2',
                'accent':'#2868C7' if light else '#659BEE',
                'success':'#247747' if light else '#5FD08A',
                'warning':'#805A00' if light else '#E9C46A',
                'destructive':'#B72F28' if light else '#EF766E'}
        for k,v in colors.items(): values[k]=f'Some("{v}FF")'
        values['corner_radii']='('+''.join(f'radius_{k}: ({v:.1f}, {v:.1f}, {v:.1f}, {v:.1f}),' for k,v in CORNER_RADII.items())+')'
        values.update(frosted=SHELL_FROSTED,frosted_panel='true',frosted_applets='true',
                      frosted_system_interface='true',frosted_windows='false',frosted_maximized_apps='false')
        if not light: values['alpha_map']=re.sub(r'(\bmedium:\s*)[0-9.]+',r'\g<1>0.90',values['alpha_map'])
        atomic(PACKAGE/f'studio-{mode.lower()}.ron','(\n'+''.join(f'    {k}: {v},\n' for k,v in sorted(values.items()))+')\n')
    version=run(['dpkg-query','-W','-f=${Version}','cosmic-settings']).stdout.strip()
    atomic(PACKAGE/'installation.json',json.dumps({'cosmic_settings_version':version,'theme_schema':2},indent=2)+'\n')
    print('Prepared themes for COSMIC Settings '+version+'. No desktop settings changed.')

def shell_roots():
    roots=[COSMIC/f'com.system76.CosmicTheme.{s}' for s in
           ['Dark','Light','Dark.Builder','Light.Builder','Mode']]
    for group,settings in [('Dock',DOCK),('Panel',PANEL)]:
        roots.extend(COSMIC/f'com.system76.CosmicPanel.{group}/v1'/key for key in settings)
    roots += [CONFIG/'gtk-3.0',CONFIG/'gtk-4.0',CONFIG/'qt5ct',CONFIG/'qt6ct',CONFIG/'kdeglobals',
              DATA/'color-schemes/CosmicLight.colors',DATA/'color-schemes/CosmicDark.colors',
              COSMIC/'com.system76.CosmicTk/v1/interface_font']
    roots += [(CONFIG/toolkit/'gtk.css').resolve() for toolkit in ['gtk-3.0','gtk-4.0']]
    return roots

def custom_gtk_css(text):
    """Keep custom CSS while allowing COSMIC's generated palette to refresh."""
    return re.sub(r'^@define-color\s+[^;]*;[ \t]*\n?', '',text,flags=re.M).replace('/* GENERATED BY COSMIC */','').strip()

def apply_shell():
    """Apply native shell material without applying application presets."""
    prepare()
    preflight(include_apps=False)
    roots=shell_roots()
    BACKUPS.mkdir(exist_ok=True,mode=0o700)
    directory=BACKUPS/(datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-shell-'+uuid.uuid4().hex[:6])
    directory.mkdir(mode=0o700)
    manifest={'schema':SCHEMA_VERSION,'profile':'shell','status':'applying',
              'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'roots':[str(p) for p in roots],'before':snapshot(roots),'changed':[],
              'gsettings':{s+'/'+k:run(['gsettings','get',s,k]).stdout.strip() for s,k in GSETTINGS},
              'favorites_before':(COSMIC/'com.system76.CosmicAppList/v1/favorites').read_text()}
    save_manifest(directory,manifest)
    custom={toolkit:custom_gtk_css((CONFIG/toolkit/'gtk.css').read_text())
            for toolkit in ['gtk-3.0','gtk-4.0'] if (CONFIG/toolkit/'gtk.css').is_file()}
    qt_styles={}
    qt_fonts={}
    for toolkit in ['qt5ct','qt6ct']:
        path=CONFIG/toolkit/f'{toolkit}.conf'
        text=path.read_text() if path.is_file() else ''
        match=re.search(r'^stylesheets=([^\n]*)$',text,flags=re.M)
        if match: qt_styles[toolkit]=match.group(1)
        match=re.search(r'^general=([^\n]*)$',text,flags=re.M)
        if match: qt_fonts[toolkit]=match.group(1)
    try:
        for mode in ['dark','light']:
            result=run(['cosmic-settings','appearance','import',PACKAGE/f'studio-{mode}.ron'])
            if 'Successfully imported' not in result.stdout:
                raise RuntimeError('Native theme importer did not confirm import: '+result.stdout[-800:])
        for group,settings in [('Dock',DOCK),('Panel',PANEL)]:
            for key,value in settings.items(): atomic(COSMIC/f'com.system76.CosmicPanel.{group}/v1'/key,value)
        time.sleep(2)
        # Keep prior custom toolkit rules and type roles after the native sync.
        written=set()
        for toolkit,extra in custom.items():
            path=(CONFIG/toolkit/'gtk.css').resolve()
            if path in written: continue
            written.add(path)
            text=path.read_text() if path.is_file() else ''
            current=custom_gtk_css(text)
            if extra and extra not in current: atomic(path,text.rstrip()+'\n'+extra+'\n')
        for toolkit in ['qt5ct','qt6ct']:
            path=CONFIG/toolkit/f'{toolkit}.conf'
            text=path.read_text() if path.is_file() else ''
            if toolkit in qt_styles: text=ini_value(text,'Interface','stylesheets',qt_styles[toolkit])
            if toolkit in qt_fonts: text=ini_value(text,'Fonts','general',qt_fonts[toolkit])
            if path.is_file() or toolkit in qt_styles or toolkit in qt_fonts: atomic(path,text)
        if (CONFIG/'studio-light/typography-gtk.css').is_file(): apply_typography_imports()
        if (CONFIG/'studio-light/window-frames.css').is_file(): apply_window_frame_imports()
        after=snapshot(roots)
        manifest['changed']=sorted(k for k in manifest['before'].keys()|after.keys() if manifest['before'].get(k)!=after.get(k))
        manifest['after_hashes']={k:hashlib.sha256(json.dumps(after.get(k),sort_keys=True).encode()).hexdigest() for k in manifest['changed']}
        manifest['status']='applied';save_manifest(directory,manifest)
        checks=verify_shell(directory)
        atomic(PACKAGE/'shell-verification.json',json.dumps(checks,indent=2)+'\n')
        if any(c['status']=='FAIL' for c in checks): raise RuntimeError('Native shell verification failed.')
        atomic(PACKAGE/'latest-shell-backup.txt',str(directory)+'\n')
        print('Applied native shell material. Backup: '+str(directory))
        print('Restore: python3 '+str(PACKAGE/'setup.py')+' restore '+str(directory))
    except Exception:
        manifest['status']='applying';save_manifest(directory,manifest)
        restore(directory,force=True)
        raise

def verify_shell(directory=None):
    checks=[]
    def add(name,condition,details=''):
        checks.append({'check':name,'status':'PASS' if condition else 'FAIL','details':details})
    def read(path): return path.read_text().strip() if path.is_file() else ''
    for group,settings in [('Dock',DOCK),('Panel',PANEL)]:
        for key,value in settings.items(): add(group+' '+key,read(COSMIC/f'com.system76.CosmicPanel.{group}/v1'/key)==value,value)
    for mode in ['Light','Dark']:
        for suffix in ['','.Builder']:
            base=COSMIC/f'com.system76.CosmicTheme.{mode}{suffix}/v2'
            radii=read(base/'corner_radii')
            add(mode+suffix+' subtle corner radii',all(re.search(rf'\bradius_{k}:\s*\(\s*{v:.1f}\s*,\s*{v:.1f}\s*,\s*{v:.1f}\s*,\s*{v:.1f}\s*,?\s*\)',radii) for k,v in CORNER_RADII.items()))
            add(mode+suffix+' native shell frosting',all(read(base/key)=='true' for key in ['frosted_panel','frosted_applets','frosted_system_interface']))
            add(mode+suffix+' lowest nonzero native backdrop level',read(base/'frosted')==SHELL_FROSTED,SHELL_FROSTED)
            add(mode+suffix+' opaque app content',read(base/'frosted_windows')=='false')
    add('Dark medium glass tint',bool(re.search(r'\bmedium:\s*0\.9(?:0)?\s*,',read(COSMIC/'com.system76.CosmicTheme.Dark/v2/alpha_map'))),'0.90')
    if directory:
        manifest=json.loads((directory/'manifest.json').read_text())
        add('Pinned app order preserved',read(COSMIC/'com.system76.CosmicAppList/v1/favorites')==manifest['favorites_before'].strip())
        original=manifest['before'].get(str(COSMIC/'com.system76.CosmicTk/v1/interface_font'))
        add('Native UI typography preserved',record(COSMIC/'com.system76.CosmicTk/v1/interface_font')==original)
    checks.append({'check':'Rendered glass and interaction','status':'PENDING',
                   'details':'Configuration checks do not prove rendering. Inspect the patched native panel over light/dark patterned backgrounds and both display scales.'})
    return checks

def ini_stylesheet(text,path):
    """Add one stylesheet while preserving all other Qt settings and their formatting."""
    marker=re.search(r'^\[Interface\]\s*$',text,flags=re.M)
    if not marker: return text.rstrip()+'\n\n[Interface]\nstylesheets='+str(path)+'\n'
    start=marker.end()
    end_match=re.search(r'^\[',text[start:],flags=re.M)
    end=start+end_match.start() if end_match else len(text)
    section=text[start:end]
    old=re.search(r'^stylesheets=(.*)$',section,flags=re.M)
    if old:
        val=old.group(1).strip()
        if str(path) in val: return text
        val=(val+', ' if val and val!='@Invalid()' else '')+str(path)
        section=section[:old.start()]+f'stylesheets={val}'+section[old.end():]
    else: section='\nstylesheets='+str(path)+'\n'+section.lstrip('\n')
    return text[:start]+section+text[end:]

def apply_blender():
    if not shutil.which('blender'): return 'not installed'
    # Blender exposes a supported headless preset API. This changes only theme preferences.
    code='''import bpy, os
roots=bpy.utils.script_paths(subdir="presets")
preset=next((os.path.join(p,"interface_theme","Blender_Light.xml") for p in roots
             if os.path.isfile(os.path.join(p,"interface_theme","Blender_Light.xml"))),None)
if preset is None: raise RuntimeError("Installed Blender Light preset not found")
bpy.ops.script.execute_preset(filepath=preset, menu_idname="USERPREF_MT_interface_theme_presets")
bpy.ops.wm.save_userpref()
print("STUDIO_LIGHT_PRESET_APPLIED")
'''
    result=run(['blender','--background','--python-expr',code],timeout=90)
    if 'STUDIO_LIGHT_PRESET_APPLIED' not in result.stdout:
        raise RuntimeError('Blender did not confirm saving the light theme.')
    return 'Blender Light saved; next launch uses this preset'

def apply():
    preflight()
    BACKUPS.mkdir(exist_ok=True,mode=0o700)
    directory=BACKUPS/(datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6])
    directory.mkdir(mode=0o700)
    roots=appearance_roots()
    manifest={'schema':SCHEMA_VERSION,'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'roots':[str(p) for p in roots],'before':snapshot(roots),'changed':[],
              'gsettings':{s+'/'+k:run(['gsettings','get',s,k]).stdout.strip() for s,k in GSETTINGS},
              'favorites_before':(COSMIC/'com.system76.CosmicAppList/v1/favorites').read_text(),
              'status':'applying'}
    save_manifest(directory,manifest)
    try:
        for mode in ['dark','light']:
            result=run(['cosmic-settings','appearance','import',PACKAGE/f'studio-{mode}.ron'])
            if 'Successfully imported' not in result.stdout:
                raise RuntimeError('Native theme importer did not confirm import: '+result.stdout[-800:])
        for group,settings in [('Dock',DOCK),('Panel',PANEL)]:
            for key,value in settings.items():
                atomic(COSMIC/f'com.system76.CosmicPanel.{group}/v1'/key,value)
        run(['gsettings','set','org.gnome.desktop.interface','color-scheme','prefer-light'])
        if Path('/usr/share/themes/adw-gtk3').is_dir():
            run(['gsettings','set','org.gnome.desktop.interface','gtk-theme','adw-gtk3'])
        apply_typography()
        atomic(CONFIG/'ghostty/themes/Studio Dark',(PACKAGE/'Studio Dark.ghostty').read_bytes())
        atomic(CONFIG/'studio-light/ghostty-dark.css',(PACKAGE/'ghostty-dark.css').read_bytes(),0o644)
        ghostty_appearance=(PACKAGE/'appearance.ghostty').read_text().replace('@STUDIO_GTK_CSS@',str(CONFIG/'studio-light/ghostty-dark.css'))
        atomic(CONFIG/'ghostty/appearance.ghostty',ghostty_appearance)
        ghostty=CONFIG/'ghostty/config.ghostty'
        old=ghostty.read_text() if ghostty.exists() else ''
        old=re.sub(r'\n?# BEGIN STUDIO LIGHT\n.*?# END STUDIO LIGHT\n?', '', old, flags=re.S)
        addition='\n# BEGIN STUDIO LIGHT\nconfig-file = '+str(CONFIG/'ghostty/appearance.ghostty')+'\n# END STUDIO LIGHT\n'
        atomic(ghostty,old.rstrip('\n')+addition)
        if shutil.which('ghostty'): run(['ghostty','+validate-config'])
        atomic(CONFIG/'zed/themes/studio-light.json',(PACKAGE/'studio-light-zed.json').read_bytes())
        path=CONFIG/'zed/settings.json'
        settings=json.loads(path.read_text()) if path.exists() else {}
        settings['theme']='Studio Light'
        settings['ui_font_family']='Archivo'
        atomic(path,json.dumps(settings,indent=2)+'\n')
        path=CONFIG/'GIMP/2.10/gimprc'
        old=path.read_text() if path.exists() else ''
        old=re.sub(r'^\s*\(theme\s+"[^"\n]*"\)\s*$', '', old,flags=re.M)
        atomic(path,old.rstrip()+'\n(theme "Light")\n')
        manifest['blender']=apply_blender()
        time.sleep(2) # Allow COSMIC's existing GTK/Qt synchronizer to write its palettes.
        atomic(CONFIG/'studio-light/glass-gtk.css',(PACKAGE/'glass-gtk.css').read_bytes())
        atomic(CONFIG/'studio-light/glass-qt.qss',(PACKAGE/'glass-qt.qss').read_bytes())
        # Keep COSMIC's generated color variables and its existing GTK stylesheet symlinks.
        gtk_targets={(CONFIG/v/'gtk.css').resolve() for v in ['gtk-3.0','gtk-4.0']}
        for target in gtk_targets:
            if target.is_file():
                old=target.read_text()
                old=re.sub(r'\n?/\* BEGIN STUDIO GLASS \*/.*?/\* END STUDIO GLASS \*/\n?', '',old,flags=re.S)
                suffix='\n/* BEGIN STUDIO GLASS */\n@import url("'+str(CONFIG/'studio-light/glass-gtk.css')+'");\n/* END STUDIO GLASS */\n'
                atomic(target,old.rstrip('\n')+suffix)
        for toolkit in ['qt5ct','qt6ct']:
            path=CONFIG/toolkit/f'{toolkit}.conf'
            if path.is_file():
                atomic(path,ini_stylesheet(path.read_text(),CONFIG/'studio-light/glass-qt.qss'))
        if (CONFIG/'studio-light/typography-gtk.css').is_file(): apply_typography_imports()
        if (CONFIG/'studio-light/window-frames.css').is_file(): apply_window_frame_imports()
        after=snapshot(roots)
        manifest['changed']=sorted(k for k in manifest['before'].keys()|after.keys()
                                   if manifest['before'].get(k)!=after.get(k))
        manifest['after_hashes']={k:hashlib.sha256(json.dumps(after.get(k),sort_keys=True).encode()).hexdigest()
                                  for k in manifest['changed']}
        manifest['status']='applied'
        save_manifest(directory,manifest)
        atomic(PACKAGE/'latest-backup.txt',str(directory)+'\n')
        if not (PACKAGE/'original-backup.txt').exists(): atomic(PACKAGE/'original-backup.txt',str(directory)+'\n')
        checks=verify(directory)
        failures=[c for c in checks if c['status']=='FAIL']
        if failures: raise RuntimeError('Verification failed: '+', '.join(c['check'] for c in failures))
        print('Applied. Backup: '+str(directory))
        print('Run: python3 '+str(PACKAGE/'setup.py')+' restore')
    except Exception:
        after=snapshot(roots)
        manifest['changed']=sorted(k for k in manifest['before'].keys()|after.keys()
                                  if manifest['before'].get(k)!=after.get(k))
        manifest['status']='failed'
        save_manifest(directory,manifest)
        print('Application failed; restoring affected appearance settings.',file=sys.stderr)
        restore(directory,force=True)
        raise

def select_backup(value=None):
    if value in ['original','latest']:
        value=(PACKAGE/f'{value}-backup.txt').read_text().strip()
    path=Path(value) if value else Path((PACKAGE/'latest-backup.txt').read_text().strip())
    path=path.resolve()
    if not path.is_relative_to(BACKUPS.resolve()):
        raise RuntimeError('Backup must be inside this package backups directory.')
    return path

def restore(directory, force=False):
    manifest=json.loads((directory/'manifest.json').read_text())
    if manifest['schema']!=SCHEMA_VERSION: raise RuntimeError('Unsupported backup schema.')
    if manifest['status']=='applying':
        after=snapshot([Path(r) for r in manifest['roots']])
        manifest['changed']=sorted(k for k in manifest['before'].keys()|after.keys()
                                  if manifest['before'].get(k)!=after.get(k))
    # Refuse to discard appearance edits made since apply unless explicitly requested.
    conflicts=[]
    for name,digest in manifest.get('after_hashes',{}).items():
        current=hashlib.sha256(json.dumps(record(Path(name)),sort_keys=True).encode()).hexdigest()
        if current!=digest: conflicts.append(name)
    if conflicts and not force:
        raise RuntimeError('Appearance files changed since apply. Review before restore; use --force to restore the backup.\n'+'\n'.join(conflicts))
    for name in manifest['changed']:
        path=Path(name); original=manifest['before'].get(name)
        if original is None:
            if path.is_file() or path.is_symlink(): path.unlink()
        elif original['kind']=='symlink':
            if path.is_file() or path.is_symlink(): path.unlink()
            path.parent.mkdir(parents=True,exist_ok=True)
            path.symlink_to(original['target'])
        else: atomic(path,base64.b64decode(original['data']),original['mode'])
    for setting,value in manifest['gsettings'].items():
        schema,key=setting.split('/',1)
        run(['gsettings','set',schema,key,value])
    time.sleep(1)
    # Watchers can regenerate toolkit files after the mode changes: restore exact originals last.
    for name in manifest['changed']:
        original=manifest['before'].get(name); path=Path(name)
        if original and original['kind']=='file': atomic(path,base64.b64decode(original['data']),original['mode'])
        elif original is None and (path.is_file() or path.is_symlink()): path.unlink()
    mismatches=[n for n in manifest['changed'] if record(Path(n))!=manifest['before'].get(n)]
    if mismatches: raise RuntimeError('Restore could not reproduce original files: '+', '.join(mismatches))
    if any('/fonts/cosmic-studio' in r or '/fontconfig/conf.d/60-cosmic-studio' in r for r in manifest['roots']):
        run(['fc-cache','-f'],timeout=60)
    manifest['status']='restored'
    save_manifest(directory,manifest)
    print('Restored '+str(len(manifest['changed']))+' appearance files. Reload/restart affected applications.')

def verify(directory=None):
    if directory and json.loads((directory/'manifest.json').read_text()).get('profile')=='window_frames':
        checks=verify_window_frames(directory)
        for c in checks: print(c['status']+': '+c['check']+' — '+c['details'])
        atomic(PACKAGE/'window-frames-verification.json',json.dumps(checks,indent=2)+'\n')
        return checks
    if directory and json.loads((directory/'manifest.json').read_text()).get('profile')=='shell':
        checks=verify_shell(directory)
        for c in checks: print(c['status']+': '+c['check']+' — '+c['details'])
        atomic(PACKAGE/'shell-verification.json',json.dumps(checks,indent=2)+'\n')
        return checks
    if directory and json.loads((directory/'manifest.json').read_text()).get('profile')=='typography':
        checks=verify_typography(directory)
        for c in checks: print(c['status']+': '+c['check']+' — '+c['details'])
        atomic(PACKAGE/'typography-verification.json',json.dumps(checks,indent=2)+'\n')
        return checks
    checks=[]
    def add(name,condition,details=''):
        checks.append({'check':name,'status':'PASS' if condition else 'FAIL','details':details})
    def read(path): return path.read_text().strip() if path.is_file() else ''
    add('Persistent COSMIC light mode',read(COSMIC/'com.system76.CosmicTheme.Mode/v1/is_dark')=='false')
    add('GTK light preference',run(['gsettings','get','org.gnome.desktop.interface','color-scheme']).stdout.strip()=="'prefer-light'")
    for mode in ['Light','Dark']:
        for suffix in ['','.Builder']:
            base=COSMIC/f'com.system76.CosmicTheme.{mode}{suffix}/v2'
            radii=read(base/'corner_radii')
            numbers=re.findall(r'(?<![\w])\d+\.\d+',radii)
            add(f'{mode}{suffix} subtle corner radii',len(numbers)==24 and numbers==[f'{v:.1f}' for v in CORNER_RADII.values() for _ in range(4)])
            add(f'{mode}{suffix} opaque application windows',read(base/'frosted_windows')=='false')
            add(f'{mode}{suffix} shell frosting',all(read(base/k)=='true' for k in ['frosted_panel','frosted_applets','frosted_system_interface']))
            add(f'{mode}{suffix} lowest nonzero native backdrop level',read(base/'frosted')==SHELL_FROSTED,SHELL_FROSTED)
    for group,settings in [('Dock',DOCK),('Panel',PANEL)]:
        for key,value in settings.items():
            add(group+' '+key,read(COSMIC/f'com.system76.CosmicPanel.{group}/v1'/key)==value)
    zed=CONFIG/'zed/settings.json'
    add('Zed custom light theme',zed.exists() and json.loads(zed.read_text()).get('theme')=='Studio Light')
    expected=read(PACKAGE/'appearance.ghostty').replace('@STUDIO_GTK_CSS@',str(CONFIG/'studio-light/ghostty-dark.css'))
    add('Ghostty approved opaque dark theme and iA Writer Mono S',read(CONFIG/'ghostty/appearance.ghostty')==expected)
    if shutil.which('ghostty'):
        result=run(['ghostty','+validate-config'],check=False)
        add('Ghostty config parser',result.returncode==0,(result.stderr+result.stdout).strip()[:300])
    add('GIMP Light preset','(theme "Light")' in read(CONFIG/'GIMP/2.10/gimprc'))
    # Toolkit configuration is generated by COSMIC, not replaced by this installer.
    for toolkit in ['qt5ct','qt6ct']:
        path=CONFIG/toolkit/f'{toolkit}.conf'
        add(toolkit+' follows light palette','CosmicLight.conf' in read(path))
        add(toolkit+' glass chrome stylesheet',str(CONFIG/'studio-light/glass-qt.qss') in read(path))
    add('GTK glass chrome stylesheet',all('BEGIN STUDIO GLASS' in read(CONFIG/v/'gtk.css') for v in ['gtk-3.0','gtk-4.0']))
    for mode,expected in [('Light','#F5F5F7FF'),('Dark','#000000FF')]:
        add(mode+' background color',expected in read(COSMIC/f'com.system76.CosmicTheme.{mode}/v2/background'))
    for mode,expected in [('Light','#2868C7FF'),('Dark','#659BEEFF')]:
        add(mode+' blue accent',expected in read(COSMIC/f'com.system76.CosmicTheme.{mode}/v2/accent'))
    add('Dark glass tint','medium: 0.90' in read(COSMIC/'com.system76.CosmicTheme.Dark/v2/alpha_map'))
    portal=run(['gdbus','call','--session','--dest','org.freedesktop.portal.Desktop',
                '--object-path','/org/freedesktop/portal/desktop','--method',
                'org.freedesktop.portal.Settings.Read','org.freedesktop.appearance','color-scheme'],check=False)
    add('Portal light preference',portal.returncode==0 and 'uint32 2' in portal.stdout,portal.stdout.strip())
    if directory:
        manifest=json.loads((directory/'manifest.json').read_text())
        current=read(COSMIC/'com.system76.CosmicAppList/v1/favorites')
        add('Pinned app order preserved',current==manifest['favorites_before'].strip())
        add('Backup contains originals',all(k in manifest['before'] or record(Path(k)) is not None for k in manifest['changed']))
    checks.extend([
        {'check':'Brave','status':'PENDING','details':'Existing light preference retained; system preference applied. Browser settings UI is unavailable to automation.'},
        {'check':'ChatGPT/Codex','status':'PENDING','details':'System light preference applied; check app Appearance if it has an independent override.'},
        {'check':'VLC','status':'PENDING','details':'Qt light integration configured; confirm dialogs on next launch.'},
        {'check':'Obsidian','status':'PREPARED','details':'Light CSS snippet delivered for later; vaults untouched.'},
        {'check':'Launcher','status':'THEMED','details':'Native 600px keyboard launcher inherits square geometry, blue focus, and system frosting. Raycast-specific layout changes require a native source build; no user layout settings exist in this version.'},
        {'check':'Visual and sign-in checks','status':'PENDING','details':'Native desktop screenshots are unavailable here. Check actual windows, maximization, displays, and persistence after next sign-in.'}])
    checks.extend(verify_typography())
    for c in checks: print(c['status']+': '+c['check']+((' — '+c['details']) if c['details'] else ''))
    atomic(PACKAGE/'verification.json',json.dumps(checks,indent=2)+'\n')
    return checks

def verify_typography(directory=None):
    checks=[]
    def add(name,condition,details=''):
        checks.append({'check':name,'status':'PASS' if condition else 'FAIL','details':details})
    for family in ['Archivo','Instrument Serif']:
        result=run(['fc-match','-f','%{family}|%{style}|%{file}',family],check=False)
        actual=result.stdout.split('|')[0]
        add(family+' font resolution',result.returncode==0 and family in actual.split(','),result.stdout.strip())
    files=font_assets()
    add('Pinned font files and OFL licenses',all(target.is_file() and source.read_bytes()==target.read_bytes()
                                              for source,target in files),str(len(files))+' checked assets')
    path=COSMIC/'com.system76.CosmicTk/v1/interface_font'
    add('Native COSMIC Archivo interface font',path.is_file() and path.read_text().strip()==INTERFACE_FONT,str(path))
    for path in private_flatpak_font_roots():
        add('Caffeine sandbox Archivo interface font',
            path.is_file() and path.read_text().strip()==INTERFACE_FONT,str(path))
    for schema,key in FONT_GSETTINGS:
        result=run(['gsettings','get',schema,key],check=False)
        add('GTK '+key,result.returncode==0 and result.stdout.strip().startswith("'Archivo "),result.stdout.strip())
    for toolkit in ['gtk-3.0','gtk-4.0']:
        path=CONFIG/toolkit/'settings.ini'
        css=CONFIG/toolkit/'gtk.css'
        add(toolkit+' Archivo UI setting',path.is_file() and bool(re.search(r'^gtk-font-name=Archivo \d',path.read_text(),re.M)),str(path))
        add(toolkit+' semantic heading CSS',css.is_file() and 'BEGIN STUDIO TYPOGRAPHY' in css.read_text(),str(css))
    for toolkit in ['qt5ct','qt6ct']:
        path=CONFIG/toolkit/f'{toolkit}.conf'
        text=path.read_text() if path.is_file() else ''
        add(toolkit+' Archivo UI setting',bool(re.search(r'^general=Archivo,',text,re.M)),str(path))
        add(toolkit+' heading stylesheet',str(CONFIG/'studio-light/typography-qt.qss') in text,str(path))
    for path in window_frame_targets():
        add('GTK palette semantic heading CSS '+str(path),path.is_file() and
            path.read_text().count('/* BEGIN STUDIO TYPOGRAPHY */')==1 and
            str(CONFIG/'studio-light/typography-gtk.css') in path.read_text(),str(path))
    path=CONFIG/'zed/settings.json'
    add('Zed Archivo interface',path.is_file() and json.loads(path.read_text()).get('ui_font_family')=='Archivo',str(path))
    path=COSMIC/'com.system76.CosmicTk/v1/icon_theme'
    if path.is_file():
        try: current_icon_theme=json.loads(path.read_text())
        except (json.JSONDecodeError,UnicodeError): current_icon_theme=None
        add('Current native icon theme is independent of typography',
            isinstance(current_icon_theme,str) and bool(current_icon_theme),str(current_icon_theme))
    if directory:
        manifest=json.loads((directory/'manifest.json').read_text())
        for name,original in manifest.get('preserved',{}).items():
            add('Independent setting preserved '+name,record(Path(name))==original)
    checks.append({'check':'COSMIC separate heading family','status':'PREPARED',
                   'details':'Installed COSMIC Tk v1 has no heading_font setting. Build the reviewed libcosmic typography patch to activate Instrument Serif native title helpers. Existing processes may retain their cached font collection until next launch.'})
    return checks

def preview():
    preflight()
    print('Ready: COSMIC v2 themes, light app defaults, dark frosted panel/dock, zero-radius native geometry.')
    print('Applications: custom Ghostty/Zed light themes, native GIMP/Blender light presets, GTK/Qt integration.')
    print('Typography: authentic Archivo UI faces and Instrument Serif headings; existing point sizes and code fonts retained.')
    print('Unchanged: pinned apps, app controls, wallpaper, monitors, content, motion.')
    print('Obsidian snippet prepared only. Backups and restore are included. No settings changed by preview.')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['prepare','preview','apply','shell','typography','frames','verify','restore'])
    parser.add_argument('backup',nargs='?')
    parser.add_argument('--force',action='store_true',help='Restore even if appearance files were edited after apply.')
    args=parser.parse_args()
    if args.backup and args.command not in ['verify','restore']:
        parser.error('Only verify and restore accept a backup path; '+args.command+' accepts no second argument.')
    if args.command=='prepare': prepare()
    elif args.command=='preview': preview()
    elif args.command=='apply': apply()
    elif args.command=='typography': apply_typography_only()
    elif args.command=='shell': apply_shell()
    elif args.command=='frames': apply_window_frames_only()
    elif args.command=='restore': restore(select_backup(args.backup),args.force)
    else:
        directory=select_backup(args.backup) if args.backup or (PACKAGE/'latest-backup.txt').exists() else None
        if any(c['status']=='FAIL' for c in verify(directory)): sys.exit(1)

if __name__=='__main__':
    try: main()
    except Exception as error:
        print('ERROR: '+str(error),file=sys.stderr)
        sys.exit(1)
