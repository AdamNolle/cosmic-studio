#!/usr/bin/env python3
"""Build the local Studio Glass family from editable geometry and installed marks.

Run with a Python containing Pillow. Blender renders offline; the desktop only
loads optimized PNGs. Third-party artwork and machine inventory stay local.
"""
from pathlib import Path
import argparse, base64, configparser, gzip, hashlib, html, json, math, re, struct, subprocess, sys
from urllib.request import urlopen
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from build import SPECS, GLYPHS
from symbols import build as build_symbols
from brands import find_mark

THEME = ROOT / 'Studio Objects'
ART = ROOT / 'blender' / 'sources'
RENDERS = ROOT / 'blender' / 'glass-renders'
SIZES = (16, 20, 24, 32, 36, 40, 48, 64, 72, 96, 128, 192, 256, 512)
NS = 'http://www.w3.org/2000/svg'

# Metaphors are app-specific. Vendor marks retain their original silhouettes.
# The shared identity is the optical size, glass construction, and lighting.
EXTRA = [
 ('Trash', 'trash', '#90c6db', '#365c70', '#f4fbff', '#a1c5d4', ['user-trash', 'user-trash-full']),
 ('Kdenlive', 'film', '#5ba3c0', '#234d69', '#e5f4ff', '#85bad7', ['org.kde.kdenlive','kdenlive']),
 ('HandBrake', 'film', '#68b85c', '#2a583d', '#edffc9', '#83b77a', ['fr.handbrake.ghb']),
 ('ImageMagick', 'camera', '#88a3d9', '#314367', '#f4e4bc', '#9db4db', ['display-im6.q16']),
 ('Vim', 'pen', '#66ba69', '#214a37', '#e6ffe4', '#8dbb8e', ['gvim']),
 ('NVIDIA Settings', 'chip', '#86be45', '#254528', '#e6ffd4', '#9dbb7a', ['nvidia-settings']),
 ('Nsight Eclipse', 'chip', '#a18adb', '#3c325f', '#e9e1ff', '#9f8ccc', ['studio-nsight-eclipse']),
 ('Nsight Compute', 'chip', '#80b96c', '#284d39', '#ecffdc', '#9aba84', ['studio-nsight-compute']),
 ('Nsight Systems', 'monitor', '#71bdab', '#274c47', '#e7fff4', '#a4cbbf', ['studio-nsight-systems']),
 ('NVIDIA Visual Profiler', 'chart', '#94b767', '#3c4b25', '#f4ffd9', '#b6cb89', ['studio-nvidia-profiler']),
 ('Flameshot','camera','#de665b','#652c35','#fff0d9','#e39c86',['org.flameshot.Flameshot']),
 ('Image Viewer','image','#78b28b','#315a47','#f5ffdd','#a8cfb3',['org.gnome.eog']),
 ('Repoman','store','#bb96dd','#593a70','#f7e9ff','#c4a6dc',['repoman']),
 ('Hardware Monitor','monitor','#8e9fcf','#374064','#e9ecff','#a5acd4',['io.github.kai_j_g.HardwareMonitor']),
 ('XTerm','code','#b19969','#493e24','#fff5ce','#d4ba81',['mini.xterm']),
 ('Power Statistics','power','#94b55f','#3e5027','#eeffcc','#c6d58e',['org.gnome.PowerStats']),
 ('LibreOffice','document','#b8c9d1','#4d646f','#fbfeff','#b8c6d3',['libreoffice-startcenter']),
 ('Character Map','characters','#bc9fb7','#5b3f5a','#fff0fd','#d6b4ce',['accessories-character-map']),
 ('System76 Driver','chip','#839cac','#374b5b','#f1fcff','#b3c4d3',['system76-driver']),
 ('TeXInfo','information','#8cb8d6','#3b5876','#f4fbff','#b3d5eb',['dialog-information']),
 ('Looking Glass','monitor','#64bdd2','#234b60','#e5faff','#91cbdd',['looking-glass']),
]
BRAND_LOOKUPS = {
 'Brave': ('brave-browser', 'https://brave.com/branding/'),
 'Obsidian': ('obsidian', 'https://obsidian.md/'),
 'Zed': ('zed', 'https://zed.dev/brand'),
 'GIMP': ('org.gimp.GIMP', 'https://www.gimp.org/'),
 'Inkscape': ('org.inkscape.Inkscape', 'https://inkscape.org/'),
 'Blender': ('blender', 'https://www.blender.org/about/logo/'),
 'Music': ('spotify-client', 'https://developer.spotify.com/documentation/design'),
 'Mail': ('thunderbird', 'https://www.thunderbird.net/'),
 'Steam': ('steam', 'https://store.steampowered.com/'),
 'Discord': ('discord', 'https://discord.com/branding'),
 'Firefox': ('firefox', 'https://mozilla.design/'),
 'Darktable': ('darktable', 'https://www.darktable.org/'),
 'Slicer': ('PrusaSlicer', 'https://www.prusa3d.com/'),
 'Kdenlive': ('org.kde.kdenlive', 'https://kdenlive.org/'),
 'HandBrake': ('fr.handbrake.ghb', 'https://handbrake.fr/'),
 'Blip': ('net.blip.Blip', 'https://blip.net/'),
 'Vim': ('gvim', 'https://www.vim.org/'),
 'ImageMagick': ('display-im6.q16', 'https://imagemagick.org/'),
 'Writer': ('libreoffice-writer', 'https://www.libreoffice.org/'),
 'Calc': ('libreoffice-calc', 'https://www.libreoffice.org/'),
 'Impress': ('libreoffice-impress', 'https://www.libreoffice.org/'),
 'Draw': ('libreoffice-draw', 'https://www.libreoffice.org/'),
 'Math': ('libreoffice-math', 'https://www.libreoffice.org/'),
 'Syncthing': ('syncthing', 'https://syncthing.net/'),
 'Solaar': ('solaar', 'https://pwr-solaar.github.io/Solaar/'),
 'Flameshot': ('org.flameshot.Flameshot', 'https://flameshot.org/'),
 'Image Viewer': ('org.gnome.eog', 'https://apps.gnome.org/Loupe/'),
 'Hardware Monitor': ('io.github.kai_j_g.HardwareMonitor','https://github.com/kai-jg/hardware-monitor'),
 'LibreOffice': ('libreoffice-startcenter','https://www.libreoffice.org/'),
 'Looking Glass': ('looking-glass','https://looking-glass.io/'),
 'Antigravity': ('antigravity','https://antigravity.google/'),
 'Nsight Compute': ('studio-nsight-compute','https://developer.nvidia.com/nsight-compute'),
 'Nsight Systems': ('studio-nsight-systems','https://developer.nvidia.com/nsight-systems'),
 'NVIDIA Settings': ('nvidia-settings','https://www.nvidia.com/'),
}
OVERRIDES = {
 'blender.desktop': 'blender',
 'nsight.desktop': 'studio-nsight-eclipse',
 'nvvp.desktop': 'studio-nvidia-profiler',
 'nsight-compute-2025.3.1.desktop': 'studio-nsight-compute',
 'nsight-compute-2026.1.1.desktop': 'studio-nsight-compute',
 'nsys-ui-2025.3.2.desktop': 'studio-nsight-systems',
 'nsys-ui-2025.6.3.desktop': 'studio-nsight-systems',
}
GLYPHS['trash'] = '<path d="M39 42h50l-5 58H44Z"/><path d="M33 35h62M52 34v-8h24v8M54 53v35M74 53v35" fill="none" stroke="#dcefff" stroke-width="5" stroke-linecap="round"/>'
GLYPHS['power'] = '<path d="M43 32h42v67H43Z"/><path d="m67 41-17 27h14l-3 23 19-30H66Z" fill="#4d7129"/><path d="M54 25h20v7H54Z"/>'
GLYPHS['characters'] = '<rect x="28" y="28" width="72" height="72" rx="8"/><path d="M64 30v68M30 64h68" stroke="#755369" stroke-width="3"/><path d="m38 54 8-18 8 18m-13-5h10M74 49h13m-9-7h10M39 76h13m-13 9h13m23-11 12 14m0-14L75 88" stroke="#755369" fill="none" stroke-width="3" stroke-linecap="round"/>'
GLYPHS['information'] = '<circle cx="64" cy="64" r="35"/><circle cx="64" cy="43" r="5" fill="#38577a"/><path d="M60 56h8v32h-8Z" fill="#38577a"/>'

def slug(name):
 return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

def family():
 specs = []
 separate = {'fr.handbrake.ghb', 'display-im6.q16', 'gvim', 'nvidia-settings', 'kdenlive', 'net.blip.Blip',
  'org.flameshot.Flameshot','org.gnome.eog','repoman','io.github.kai_j_g.HardwareMonitor','mini.xterm',
  'org.gnome.PowerStats','libreoffice-startcenter','accessories-character-map','system76-driver','dialog-information'}
 for s in SPECS:
  s = list(s); s[-1] = [x for x in s[-1] if x not in separate]
  if s[0] == 'GIMP': s[-1].append('org.gimp.GIMP')
  if s[0] == 'Darktable': s[-1].append('org.darktable.Darktable')
  if s[0] == 'ChatGPT': s[2:6] = ['#e0edea','#b2c8c2','#202e2a','#13221d']
  if s[0] == 'Zed': s[2:6] = ['#506475','#17232c','#e6eef7','#8292a2']
  if s[0] == 'Brave': s[2:6] = ['#ff8455','#bd351c','#fff5e8','#e2bda5']
  if s[0] == 'Ghostty': s[2:6] = ['#438bbb','#173b68','#f5fcff','#acd6ee']
  if s[-1]: specs.append(tuple(s))
 specs.extend(EXTRA)
 specs.append(('Blip','sync','#54aec6','#25515e','#effcff','#9cd6e2',['net.blip.Blip']))
 return specs

def locate_mark(name):
 direct = {
  'Brave': ART/'brave-official.svg',
  'Zed': ART/'zed-official.svg',
  'Antigravity': ART/'antigravity-vendor.png',
  'Nsight Compute': Path('/opt/nvidia/nsight-compute/2026.1.1/host/linux-desktop-glibc_2_11_3-x64/ncu-ui.png'),
  'Nsight Systems': Path('/opt/nvidia/nsight-systems/2025.6.3/host-linux-x64/nsys-ui.png'),
  'NVIDIA Settings': Path('/usr/share/pixmaps/nvidia-settings.png'),
 }
 if name in direct and direct[name].exists(): return direct[name]
 if name not in BRAND_LOOKUPS: return None
 icon = BRAND_LOOKUPS[name][0]
 roots = [Path.home()/'.local/share/flatpak/exports/share/icons/hicolor', Path('/usr/local/share/icons/hicolor'), Path('/usr/share/icons/hicolor'), Path('/usr/share/pixmaps')]
 candidates = [p for root in roots for p in root.rglob('*') if p.stem == icon and p.suffix in ('.svg','.svgz','.png')]
 def rank(p):
  if p.suffix in ('.svg','.svgz'): return 10000
  try: return int(next(x.split('x')[0] for x in p.parts if 'x' in x and x[0].isdigit()))
  except (StopIteration, ValueError): return 512
 return max(candidates, key=rank) if candidates else find_mark(icon)

def source_svg(path):
 data = gzip.decompress(path.read_bytes()) if path.suffix=='.svgz' else path.read_bytes()
 root = ET.fromstring(data)
 if 'viewBox' not in root.attrib: root.set('viewBox',f"0 0 {root.get('width','128').replace('px','')} {root.get('height','128').replace('px','')}")
 root.set('width','512'); root.set('height','512')
 return ET.tostring(root, encoding='unicode')

def mark_svg(spec):
 name,glyph,top,base,light,dark,aliases = spec
 # Blossom is the installed Conflux vector, preserving exact interlocking paths.
 if name == 'ChatGPT':
  path = Path.home()/'.local/share/icons/Conflux/apps/scalable/Chatgpt.svg'
  if path.exists():
   source=ET.parse(path).getroot(); p=next(e for e in source if e.tag.endswith('path'))
   return '<svg xmlns="'+NS+'" width="512" height="512" viewBox="8 8 48 48"><path d="'+p.get('d')+'" fill="#23312e"/></svg>',path
 # Zed's original mark is isolated from its supplied textured tile, with alpha.
 source=locate_mark(name)
 if source and source.suffix in ('.svg','.svgz'):
  svg=source_svg(source)
  if name=='Brave':
   mark=ET.fromstring(svg)
   for element in mark.iter():
    if element.tag.endswith('path'):
     element.set('fill','#fff5e8' if element.get('fill','').startswith('url(') else '#d94a27')
   svg=ET.tostring(mark,encoding='unicode')
  if name=='Zed':
   mark=ET.fromstring(svg)
   for element in mark.iter():
    if element.tag.endswith('path'):element.set('fill','#ffffff')
   svg=ET.tostring(mark,encoding='unicode')
  return svg,source
 if source:
  im=Image.open(source).convert('RGBA')
  if name == 'Antigravity':
   # Extract the ribbon from the vendor's supplied white tile, retaining colors.
   pixels=im.load()
   for y in range(im.height):
    for x in range(im.width):
     r,g,b,alpha=pixels[x,y]
     if min(r,g,b)>246: pixels[x,y]=(r,g,b,0)
  if name == 'Obsidian':
   # Vendor crystal is supplied on a neutral dark tile. Separate the colored
   # crystal from that background so it becomes its own glass-family object.
   pixels=im.load()
   for y in range(im.height):
    for x in range(im.width):
     r,g,b,alpha=pixels[x,y]
     if max(r,g,b)-min(r,g,b)<18:pixels[x,y]=(r,g,b,0)
  if name == 'Zed':
   # Vendor asset has a white/gray mark on a black tile. Preserve its geometry;
   # threshold alpha separates mark from the supplied tile, not new drawing.
   rgba=im.load()
   for y in range(im.height):
    for x in range(im.width):
     r,g,b,a=rgba[x,y]; v=max(r,g,b); alpha=int(max(0,min(1,(v-100)/80))*a)
     rgba[x,y]=(236,244,250,alpha)
   box=im.getbbox(); im=im.crop(box)
  im.thumbnail((512,512),Image.Resampling.LANCZOS)
  buf=ART/(slug(name)+'-bitmap.png'); im.save(buf)
  enc=base64.b64encode(buf.read_bytes()).decode()
  return '<svg xmlns="'+NS+'" xmlns:xlink="http://www.w3.org/1999/xlink" width="512" height="512" viewBox="0 0 512 512"><image width="512" height="512" preserveAspectRatio="xMidYMid meet" xlink:href="data:image/png;base64,'+enc+'"/></svg>',source
 body=GLYPHS[glyph].replace('url(#material)',light)
 return '<svg xmlns="'+NS+'" width="512" height="512" viewBox="20 20 88 88"><g fill="'+light+'">'+body+'</g></svg>',None

def prepare():
 ART.mkdir(parents=True,exist_ok=True); RENDERS.mkdir(parents=True,exist_ok=True)
 # Source preparation is explicit and offline at desktop runtime. Known vendor
 # vectors are fetched once, not during icon lookup or app startup.
 for name,url in {'brave-official.svg':'https://raw.githubusercontent.com/brave/leo/main/icons/brave-icon-release-color.svg','zed-official.svg':'https://raw.githubusercontent.com/zed-industries/zed/main/assets/images/zed_logo.svg'}.items():
  target=ART/name
  if not target.exists():
   try:
    content=urlopen(url,timeout=20).read();ET.fromstring(content);target.write_bytes(content)
   except Exception as error:print(f'Vendor vector unavailable ({name}): {type(error).__name__}; installed mark/original metaphor fallback.')
 antigravity=Path.home()/'.local/opt/Antigravity-x64/resources/app.asar'
 if antigravity.exists() and not (ART/'antigravity-vendor.png').exists():
  with antigravity.open('rb') as source:
   sizes=struct.unpack('<4I',source.read(16))
   if sizes[3]>4_000_000:raise RuntimeError('Unexpected Antigravity ASAR header size')
   entries=json.loads(source.read(sizes[3]));entry=entries.get('files',{}).get('icon.png')
   if entry:
    source.seek(8+sizes[1]+int(entry['offset']));(ART/'antigravity-vendor.png').write_bytes(source.read(entry['size']))
 manifest=[]; provenance=[]
 for spec in family():
  name,glyph,top,base,light,dark,aliases=spec; sid=slug(name)
  svg,source=mark_svg(spec); path=ART/(sid+'.svg'); path.write_text(svg)
  png=ART/(sid+'.png')
  subprocess.run(['inkscape',str(path),'--export-background-opacity=0','--export-width=512','--export-height=512','--export-filename='+str(png)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  im=Image.open(png).convert('RGBA'); box=im.getbbox()
  if box:
   im=im.crop(box); scale=480/max(im.size); im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
   canvas=Image.new('RGBA',(512,512)); canvas.alpha_composite(im,((512-im.width)//2,(512-im.height)//2)); canvas.save(png)
  shape='circle' if name in {'Settings','Darktable','Music','Usage','Solaar','Help','Language'} else 'squircle'
  manifest.append({'name':name,'id':sid,'aliases':aliases,'top':top,'base':base,'mark_color':light,'shape':shape,'mark':str(png),'render':str(RENDERS/(sid+'.png'))})
  provenance.append({'application':name,'creator':('Conflux contributors / OpenAI identifying mark' if name=='ChatGPT' else ('Application vendor / installed distribution' if source else 'COSMIC Studio original geometric metaphor')),'source':str(source) if source else str(ROOT/'build.py'),'reference':BRAND_LOOKUPS.get(name,('', 'https://openai.com/brand/' if name=='ChatGPT' else ''))[1], 'original_url':({'Brave':'https://raw.githubusercontent.com/brave/leo/main/icons/brave-icon-release-color.svg','Zed':'https://raw.githubusercontent.com/zed-industries/zed/main/assets/images/zed_logo.svg','Antigravity':'Installed Antigravity resources/app.asar /icon.png'}.get(name, str(source) if source else None)), 'sha256':hashlib.sha256(source.read_bytes()).hexdigest() if source else None,'license':('Conflux GPL-3.0; OpenAI retains Blossom trademark rights.' if name=='ChatGPT' else ('Installed or vendor-published artwork retained for personal local app identification; original rights and trademarks retained. Public redistribution license has not been established for every source.' if source else 'Project license')),'edits':'Identifying silhouette retained. Shallow sculpted relief, original glass housing, authored lighting, optical sizing. Brave: porcelain/coral material interpretation. Zed: official white mark. Obsidian and Antigravity: vendor tile separated from mark.','redistribution':'Third-party derived artwork excluded from source repository.'})
 (ART/'family.local.json').write_text(json.dumps(manifest,indent=2)+'\n')
 (ROOT/'brand-sources.local.json').write_text(json.dumps(provenance,indent=2)+'\n')
 (ROOT/'launcher-overrides.local.json').write_text(json.dumps(OVERRIDES,indent=2)+'\n')
 print(f'Prepared {len(manifest)} app identities; source attribution retained locally.')

def svg_embed(name,path):
 data=base64.b64encode(path.read_bytes()).decode()
 return f'<svg xmlns="{NS}" xmlns:xlink="http://www.w3.org/1999/xlink" width="512" height="512" viewBox="0 0 512 512"><title>Studio Glass — {html.escape(name)}</title><desc>Offline Blender render. Editable geometry in studio-glass-family.blend; exact mark source alongside the scene.</desc><image width="512" height="512" xlink:href="data:image/png;base64,{data}"/></svg>'

def export():
 manifest=json.loads((ART/'family.local.json').read_text()); mapping={}; masters=ROOT/'masters'; masters.mkdir(exist_ok=True)
 dirs=['scalable/apps','scalable/actions']+[f'{n}x{n}/apps' for n in SIZES]
 for d in dirs: (THEME/d).mkdir(parents=True,exist_ok=True)
 # Drop obsolete aliases so theme does not contain unreported old artwork.
 for d in [THEME/'scalable/apps']+[THEME/f'{n}x{n}/apps' for n in SIZES]:
  for path in d.glob('*'): path.unlink()
 for row in manifest:
  path=Path(row['render'])
  if not path.exists(): raise RuntimeError('Render missing: '+row['name'])
  im=Image.open(path).convert('RGBA');optimized=masters/(row['id']+'.png');im.convert('RGBa').resize((512,512),Image.Resampling.LANCZOS).convert('RGBA').save(optimized,optimize=True)
  art=svg_embed(row['name'],optimized); master=masters/(row['id']+'.svg'); master.write_text(art)
  for name in row['aliases']:
   (THEME/'scalable/apps'/(name+'.svg')).write_text(art)
   mapping[name]={'master':str(master.relative_to(ROOT)),'category':'application','status':'custom','identity':row['name'],'source_scene':'blender/studio-glass-family.blend','material':'offline Blender glass'}
  for size in SIZES:
   # Resample premultiplied alpha: transparent RGB never leaks dark fringes.
   out=im.convert('RGBa').resize((size,size),Image.Resampling.LANCZOS).convert('RGBA')
   canonical=THEME/f'{size}x{size}/apps'/(row['aliases'][0]+'.png');out.save(canonical,optimize=True)
   for name in row['aliases'][1:]: (canonical.parent/(name+'.png')).write_bytes(canonical.read_bytes())
 mapping.update(build_symbols(ROOT))
 index='[Icon Theme]\nName=Studio Objects\nComment=Studio Glass — original offline Blender material icons\nInherits=Conflux,Cosmic,hicolor\nDirectories='+','.join(dirs)+'\n'
 for d in dirs:
  scalable=d.startswith('scalable'); size=512 if scalable and d.endswith('apps') else (16 if scalable else int(d.split('x')[0]))
  index+=f'\n[{d}]\nSize={size}\nContext='+('Actions' if d.endswith('actions') else 'Applications')+'\nType='+('Scalable\nMinSize=16\nMaxSize=1024\n' if scalable else 'Fixed\n')
 (THEME/'index.theme').write_text(index)
 coverage={'custom_masters':len(manifest),'custom_names':len(mapping),'icons':mapping,'complete':False,'scope':'All visible installed desktop launchers; embedded application/web/document imagery excluded.','inherited_fallbacks':'Conflux,Cosmic,hicolor','cursor':'unchanged','raster_sizes':SIZES,'renderer':'Blender Cycles offline, premultiplied-alpha PNG exports'}
 (ROOT/'coverage.json').write_text(json.dumps(coverage,indent=2)+'\n')
 sheet(manifest)
 print(f'Exported {len(manifest)} identities / {len(mapping)} lookup names at {len(SIZES)} physical sizes.')

def font(size):
 for path in ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf']:
  if Path(path).exists(): return ImageFont.truetype(path,size)
 return ImageFont.load_default()

def sheet(manifest):
 cols=8; cell=154; heading=112; h=heading+math.ceil(len(manifest)/cols)*188
 page=Image.new('RGB',(cols*cell,h),'#f1f4f6'); d=ImageDraw.Draw(page)
 d.text((28,23),'Studio Glass',fill='#18272f',font=font(28));d.text((28,67),'Original glass housings · faithful app identities · Blender material scenes',fill='#52636d',font=font(14))
 for i,row in enumerate(manifest):
  x=(i%cols)*cell; y=heading+(i//cols)*188; im=Image.open(row['render']).convert('RGBA')
  d.rounded_rectangle((x+8,y+8,x+cell-8,y+147),radius=15,fill='#23323d')
  preview=im.convert('RGBa').resize((110,110),Image.Resampling.LANCZOS).convert('RGBA');page.paste(preview,(x+22,y+14),preview)
  page.paste(im.convert('RGBa').resize((32,32),Image.Resampling.LANCZOS).convert('RGBA'),(x+17,y+110),im.convert('RGBa').resize((32,32),Image.Resampling.LANCZOS).convert('RGBA'))
  tiny=im.convert('RGBa').resize((24,24),Image.Resampling.LANCZOS).convert('RGBA');page.paste(tiny,(x+54,y+116),tiny)
  d.text((x+12,y+155),row['name'][:22],font=font(12),fill='#253945')
 page.save(ROOT/'preview.png',optimize=True)
 # Exact pixel dock assets shown on pale and dark surfaces at 100/150/200%.
 chosen=[r for r in manifest if r['name'] in ['Ghostty','Files','Brave','ChatGPT','Zed','Settings','Darktable','GIMP','Inkscape','Blender','Music','Trash']]
 sizes=(32,48,64); review=Image.new('RGB',(1100,480),'#f0f4f6');dr=ImageDraw.Draw(review)
 for mode,bg in enumerate(('#f0f4f6','#16242f')):
  top=mode*240;dr.rectangle((0,top,1100,top+240),fill=bg)
  for j,n in enumerate(sizes):
   yy=top+j*78;dr.text((12,yy+24),f'{n}px',fill='#80929e',font=font(13))
   for i,row in enumerate(chosen):
    icon=Image.open(THEME/f'{n}x{n}/apps'/(row['aliases'][0]+'.png'));review.paste(icon,(82+i*82,yy+(72-n)//2),icon)
 review.save(ROOT/'dock-review.png',optimize=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','export']);args=parser.parse_args()
 {'prepare':prepare,'export':export}[args.command]()
