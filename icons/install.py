#!/usr/bin/env python3
"""Transactional icon-theme install with conflict-aware exact-file recovery."""
from pathlib import Path
import argparse,base64,datetime,hashlib,json,os,re,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parent
CONFIG=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))
DATA=Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))
DEST=DATA/'icons/Studio Objects'
STATE=DATA/'cosmic-studio/icon-backups'
NATIVE=CONFIG/'cosmic/com.system76.CosmicTk/v1/icon_theme'
NAME='Studio Objects'
def run(*args):return subprocess.check_output(args,text=True).strip()
def record(path):
 if path.is_symlink():return {'link':os.readlink(path)}
 if not path.exists():return None
 return {'bytes':base64.b64encode(path.read_bytes()).decode(),'mode':path.stat().st_mode&0o777}
def atomic(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 stage=CONFIG if path==NATIVE else path.parent
 fd,tmp=tempfile.mkstemp(prefix='.studio-icons-',dir=stage)
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.chmod(tmp,0o644);os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def ini(text,section,key,value):
 lines=text.splitlines(keepends=True)
 if lines and not lines[-1].endswith('\n'):lines[-1]+='\n'
 result=[];inside=False;seen=False;found=False
 for line in lines:
  m=re.match(r'^\s*\[([^]]+)\]',line)
  if m:
   if inside and not seen:result.append(f'{key}={value}\n');seen=True
   inside=m.group(1)==section;found|=inside
  if inside and re.match(r'^\s*'+re.escape(key)+r'\s*=',line):
   if not seen:result.append(f'{key}={value}\n');seen=True
  else:result.append(line)
 if inside and not seen:result.append(f'{key}={value}\n')
 if not found:
  if result and not result[-1].endswith('\n'):result[-1]+='\n'
  result.extend([f'\n[{section}]\n',f'{key}={value}\n'])
 return ''.join(result)

def desktop_icon(text,value):
 """Change only Icon in Desktop Entry; preserve Exec, actions and all formatting."""
 lines=text.splitlines(keepends=True);result=[];inside=False;seen=False;found=False
 for line in lines:
  header=re.match(r'^\s*\[([^]]+)\]',line)
  if header:
   if inside and not seen:result.append(f'Icon={value}\n');seen=True
   inside=header.group(1)=='Desktop Entry';found|=inside
  if inside and re.match(r'^\s*Icon\s*=',line):
   newline='\r\n' if line.endswith('\r\n') else '\n'
   if not seen:result.append(f'Icon={value}'+newline);seen=True
  else:result.append(line)
 if inside and not seen:
  if result and not result[-1].endswith('\n'):result[-1]+='\n'
  result.append(f'Icon={value}\n')
 if not found:raise RuntimeError('No Desktop Entry section in launcher')
 return ''.join(result)

def launcher_changes():
 manifest=ROOT/'launcher-overrides.local.json'
 if not manifest.exists():return {}
 overrides=json.loads(manifest.read_text());out={}
 # Desktop-ID priority follows the local XDG launcher directories. Overrides
 # belong in the user's applications directory; system files remain untouched.
 from inventory import launcher_roots
 roots=launcher_roots(DATA)
 for name,icon in overrides.items():
  if Path(name).name!=name or not name.endswith('.desktop'):raise RuntimeError('Unsafe desktop ID')
  selected=next((r/name for r in reversed(roots) if (r/name).is_file()),None)
  if selected is None:continue
  out[DATA/'applications'/name]=desktop_icon(selected.read_bytes().decode('utf-8'),icon).encode('utf-8')
 return out

def changes():
 out={DEST/p.relative_to(ROOT/'Studio Objects'):p.read_bytes() for p in (ROOT/'Studio Objects').rglob('*') if p.is_file()}
 out.update(launcher_changes())
 out[NATIVE]=b'"Studio Objects"\n'
 for toolkit in ('gtk-3.0','gtk-4.0'):
  p=CONFIG/toolkit/'settings.ini';out[p]=ini(p.read_text() if p.exists() else '', 'Settings','gtk-icon-theme-name',NAME).encode()
 for toolkit in ('qt5ct','qt6ct'):
  p=CONFIG/toolkit/(toolkit+'.conf')
  if p.exists():out[p]=ini(p.read_text(),'Appearance','icon_theme',NAME).encode()
 return out

def restore(manifest,force=False):
 m=json.loads(manifest.read_text())
 for name,after in m.get('after',{}).items():
  if record(Path(name))!=after and not force:raise RuntimeError('A managed icon file was edited; restore refused: '+name)
 if m.get('gsettings_after') and not force and run('gsettings','get','org.gnome.desktop.interface','icon-theme')!=m['gsettings_after']:
  raise RuntimeError('Icon preference was changed after installation; restore refused.')
 for name,before in m['before'].items():
  p=Path(name)
  if p.is_symlink():p.unlink()
  if before is None:p.unlink(missing_ok=True)
  elif 'link' in before:p.unlink(missing_ok=True);p.parent.mkdir(parents=True,exist_ok=True);p.symlink_to(before['link'])
  else:atomic(p,base64.b64decode(before['bytes']));p.chmod(before['mode'])
 run('gsettings','set','org.gnome.desktop.interface','icon-theme',m['gsettings'])
 m['status']='restored';manifest.write_text(json.dumps(m,indent=2)+'\n')
 print('Restored previous icon files and theme preference.')

def apply():
 update=changes();pending={p:b for p,b in update.items() if not p.is_file() or p.is_symlink() or p.read_bytes()!=b}
 prior=run('gsettings','get','org.gnome.desktop.interface','icon-theme')
 if not pending and prior==repr(NAME):print('Already installed; no changes.');return
 STATE.mkdir(parents=True,exist_ok=True,mode=0o700)
 stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f');manifest=STATE/(stamp+'.json')
 m={'status':'applying','before':{str(p):record(p) for p in pending},'gsettings':prior,'after':{}}
 manifest.write_text(json.dumps(m,indent=2)+'\n');manifest.chmod(0o600)
 try:
  for p,data in pending.items():atomic(p,data)
  run('gsettings','set','org.gnome.desktop.interface','icon-theme',NAME)
  m['after']={str(p):record(p) for p in pending};m['status']='applied';m['gsettings_after']=repr(NAME);manifest.write_text(json.dumps(m,indent=2)+'\n')
  (STATE/'latest').write_text(str(manifest))
 except Exception:
  restore(manifest,force=True);raise
 print('Installed Studio Objects. Recovery manifest: '+str(manifest))
 print('Cursor settings unchanged. Existing app windows may require a relaunch to refresh cached icons.')

def verify():
 expected=changes();bad=[str(p) for p,b in expected.items() if not p.is_file() or p.read_bytes()!=b]
 if bad:raise RuntimeError('Icon installation differs: '+', '.join(bad[:8]))
 if run('gsettings','get','org.gnome.desktop.interface','icon-theme')!=repr(NAME):raise RuntimeError('GTK preference differs')
 print('Verified theme files and native/GTK/Qt icon preferences. Visual coverage remains a separate check.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['preview','apply','verify','restore']);p.add_argument('--backup',type=Path);p.add_argument('--force',action='store_true');a=p.parse_args()
 if a.command=='preview':print('Preview: '+str(ROOT/'preview.png'));print('Files to manage:',len(changes()));print('Current icon theme:',run('gsettings','get','org.gnome.desktop.interface','icon-theme'))
 elif a.command=='apply':apply()
 elif a.command=='verify':verify()
 else:restore(a.backup or Path((STATE/'latest').read_text()),a.force)
