"""Preserve installed application marks; only the surrounding presentation changes.

No portfolio assets are imported. Local distribution artwork remains attributed
and is excluded from the public source checkout by default. Inkscape handles the
SVG composition and export; bitmap marks retain their original pixels.
"""
from pathlib import Path
import base64,hashlib,json,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
BRANDS={
 'Brave':('brave-browser','https://brave.com/branding/'),
 'Obsidian':('obsidian','https://obsidian.md/'),
 'Zed':('dev.zed.Zed','https://zed.dev/'),
 'Inkscape':('org.inkscape.Inkscape','https://inkscape.org/'),
 'Blender':('blender','https://www.blender.org/about/logo/'),
 'GIMP':('gimp','https://www.gimp.org/'),
 'Music':('spotify-client','https://developer.spotify.com/documentation/design'),
 'Mail':('thunderbird','https://www.thunderbird.net/'),
 'Steam':('steam','https://store.steampowered.com/'),
 'Discord':('discord','https://discord.com/branding'),
 'Firefox':('firefox','https://mozilla.design/'),
 'Darktable':('darktable','https://www.darktable.org/'),
 'Slicer':('PrusaSlicer','https://www.prusa3d.com/'),
}

def find_mark(name):
 roots=[Path('/usr/share/icons/hicolor'),Path('/var/lib/flatpak/exports/share/icons/hicolor'),Path.home()/'.local/share/icons/hicolor',Path('/usr/share/pixmaps')]
 paths=[p for root in roots for p in root.rglob('*') if p.stem==name and p.suffix in ('.svg','.png') and 'symbolic' not in str(p)]
 def rank(p):
  if p.suffix=='.svg':return 10000
  try:return int(next(x.split('x')[0] for x in p.parts if 'x' in x and x[0].isdigit()))
  except (ValueError,StopIteration):return 512
 return max(paths,key=rank) if paths else None

def artwork(name):
 if name not in BRANDS:return None
 icon,url=BRANDS[name];path=find_mark(icon)
 if path is None:return None
 source=path.read_bytes()
 if path.suffix=='.svg':
  root=ET.fromstring(source)
  if 'viewBox' not in root.attrib:root.set('viewBox',f"0 0 {root.get('width','128').replace('px','')} {root.get('height','128').replace('px','')}")
  root.set('x','22');root.set('y','20');root.set('width','84');root.set('height','84')
  root.set('preserveAspectRatio','xMidYMid meet')
  # Prefix all ids and local references before embedding in a shared document.
  for element in root.iter():
   for key,value in list(element.attrib.items()):
    if key=='id':element.set(key,'brand-'+name.lower()+'-'+value)
    elif 'url(#' in value:element.set(key,value.replace('url(#','url(#brand-'+name.lower()+'-'))
    elif key.endswith('href') and value.startswith('#'):element.set(key,'#brand-'+name.lower()+'-'+value[1:])
  body=ET.tostring(root,encoding='unicode')
 else:body='<image xmlns:xlink="http://www.w3.org/1999/xlink" x="22" y="20" width="84" height="84" preserveAspectRatio="xMidYMid meet" xlink:href="data:image/png;base64,'+base64.b64encode(source).decode()+'"/>'
 return body,{'application':name,'reference':url,'source':'installed hicolor/pixmap '+path.name,'sha256':hashlib.sha256(source).hexdigest(),'modification':'Original identifying mark preserved; presentation composed in a Studio material tile.','redistribution':'Generated local assets excluded from source repository; consult the application artwork license before redistribution.'}
