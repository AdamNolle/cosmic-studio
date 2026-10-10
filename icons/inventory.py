#!/usr/bin/env python3
"""Local coverage audit; does not copy private profiles or embedded app assets."""
from pathlib import Path
import argparse, configparser, json, os, shlex, shutil
ROOT=Path(__file__).resolve().parent

def launcher_roots(data):
 bases=os.environ.get('XDG_DATA_DIRS','/usr/local/share:/usr/share').split(':')
 roots=[Path(p)/'applications' for p in reversed(bases) if p]
 # Include flatpak exports when the session's XDG variable was not propagated.
 for root in [Path('/var/lib/flatpak/exports/share/applications'),data/'flatpak/exports/share/applications']:
  if root not in roots:roots.append(root)
 roots.append(data/'applications')
 return roots

def launches(entry):
 command=entry.get('TryExec') or entry.get('Exec','')
 try:parts=shlex.split(command)
 except ValueError:return False
 if not parts:return False
 executable=parts[0]
 return os.access(executable,os.X_OK) if executable.startswith('/') else shutil.which(executable) is not None

def collect():
 data=Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))
 roots=launcher_roots(data)
 apps={}
 for root in roots:
  for path in root.glob('*.desktop'):
   c=configparser.ConfigParser(interpolation=None,strict=False)
   try:c.read(path)
   except configparser.Error:continue
   if 'Desktop Entry' not in c:continue
   d=c['Desktop Entry']
   if d.get('Hidden','').casefold()=='true' or d.get('NoDisplay','').casefold()=='true':
    # A higher-priority hidden override suppresses its lower-priority launcher.
    apps.pop(path.name,None);continue
   if d.get('Type','Application')!='Application':continue
   apps[path.name]={'name':d.get('Name',path.stem),'icon':d.get('Icon',''),'desktop_id':path.name,'source':str(path),'launchable':launches(d)}
 covered=json.loads((ROOT/'coverage.json').read_text())['icons']
 theme_names=set()
 for root in [Path('/usr/share/icons/Cosmic'),data/'icons/Conflux']:
  for path in root.rglob('*'):
   if path.suffix in ('.svg','.png','.xpm'):theme_names.add(path.stem)
 rows=[]
 for entry in apps.values():
  row=dict(entry);row['status']='absolute-path override needed' if entry['icon'].startswith('/') else ('custom' if entry['icon'] in covered else 'inherited');rows.append(row)
 return {'applications':sorted(rows,key=lambda r:r['name'].casefold()),'missing':sorted((r for r in rows if r['launchable'] and r['status']!='custom'),key=lambda r:r['name'].casefold()),'stale_launchers':sorted((r for r in rows if not r['launchable']),key=lambda r:r['name'].casefold()),'summary':{'launchers':len(rows),'launchable_launchers':sum(r['launchable'] for r in rows),'custom_launchers':sum(r['status']=='custom' for r in rows),'custom_launchable_launchers':sum(r['status']=='custom' and r['launchable'] for r in rows),'absolute_path_launchers':sum(r['status'].startswith('absolute') for r in rows),'theme_names':len(theme_names),'custom_existing_theme_names':len(theme_names.intersection(covered)),'inherited_theme_names':len(theme_names.difference(covered))},'complete':False,'launchers_complete':all(r['status']=='custom' for r in rows if r['launchable']),'limits':['Theme names are not a census of embedded application resources.','Document thumbnails, web content and favicons retain their own imagery.','Fallback assets are not counted as custom artwork.','Launchability checks verify the launcher executable or TryExec, not app startup success.']}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--local-report',type=Path);a=p.parse_args();report=collect()
 if a.local_report:a.local_report.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report['summary'],indent=2))
