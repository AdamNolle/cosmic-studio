#!/usr/bin/env python3
"""Original layered SVG artwork. Inkscape is the sole raster/export renderer."""
from pathlib import Path
import json, subprocess, argparse, html, math
from symbols import build as build_symbols
from brands import artwork
ROOT=Path(__file__).resolve().parent
THEME=ROOT/'Studio Objects'
NS='http://www.w3.org/2000/svg'
INK='http://www.inkscape.org/namespaces/inkscape'
# Every glyph is original geometric artwork in a 128-unit drawing space.
GLYPHS={
'ghost': '<path d="M39 92V59c0-36 50-36 50 0v33l-12-9-13 10-13-10Z"/><path d="m48 52 9 7-9 7m17-1h13" fill="none" stroke="#163552" stroke-width="3.5" stroke-linejoin="round"/>',
'folder': '<path d="M28 43q0-6 6-6h22l8 8h30q6 0 6 6v40H28Z" fill="#8cc4ff"/><path d="M26 56h77l-7 35H31Z"/><path d="M34 60h60" stroke="white" stroke-opacity=".6" stroke-width="2"/>',
'brave': '<path d="m64 29 22 7 9 14-7 31-24 19-24-19-7-31 9-14Z"/><path d="m49 49 15-9 15 9-5 20-10 12-10-12Z" fill="#b2461e"/><path d="m43 49 12 4-7 8m37-12-12 4 7 8M58 65l6 3 6-3-6 13Z" fill="#ffdf9b"/>',
'crystal': '<path d="m63 26 28 20 8 35-33 22-33-28 8-31Z" fill="#a78cfa"/><path d="m63 26 7 42-29-24Z" fill="#eee2ff"/><path d="m63 26 28 20-21 22Z" fill="#c5adff"/><path d="m70 68 29 13-33 22Z" fill="#6651b3"/><path d="m33 75 37-7-4 35Z" fill="#9272e1"/><path d="m70 68 21-22 8 35Z" fill="#8163d3"/>',
'chat': '<path d="M29 38h70v47H60L42 99V85H29Z"/><path d="M44 52h40M44 62h30M44 72h36" fill="none" stroke="#287b76" stroke-width="4" stroke-linecap="round"/>',
'zed': '<path d="M39 37h53v12L54 80h38v13H35V81l39-31H39Z"/><path d="m43 34 12-7h45v45l-8 10V37Z" fill="#8eb8f6"/>',
'code': '<path d="m48 43-23 22 23 22m32-44 23 22-23 22M73 34 56 96" fill="none" stroke="url(#material)" stroke-width="9" stroke-linejoin="round"/>',
'pen': '<path d="m34 91 8-24 42-40 17 18-43 40Z"/><path d="m34 91 8-24 16 18Z" fill="#e8d5b7"/><path d="m34 91 3-11 7 7Z" fill="#273241"/><path d="m46 66 40-38 4 5-40 38Z" fill="white" opacity=".6"/>',
'settings': '<path d="M55 28h18l3 12 11 6 12-3 9 16-9 9v12l-11 9-10-4-8 14H54l-6-13-13 2-10-16 9-10-1-13 13-7Z"/><circle cx="65" cy="64" r="19" fill="#273c55"/><circle cx="65" cy="64" r="11" fill="#80adce"/><path d="M62 55a10 10 0 0 1 11 6" fill="none" stroke="#d5efff" stroke-width="2"/>',
'play': '<circle cx="64" cy="64" r="35"/><circle cx="64" cy="64" r="29" fill="#123c69"/><path d="m55 46 27 18-27 18Z" fill="#d9f3ff"/>',
'camera': '<path d="m43 42 7-11h28l7 11h17v49H26V42Z"/><circle cx="64" cy="65" r="24" fill="#26364c"/><circle cx="64" cy="65" r="17" fill="#164968"/><circle cx="64" cy="65" r="11" fill="#3989b0"/><circle cx="58" cy="58" r="5" fill="#b4f3ff" opacity=".85"/><path d="M33 49h8" stroke="white" stroke-width="3"/>',
'image': '<path d="M27 33h74v64H27Z"/><path d="M33 39h62v51H33Z" fill="#164b75"/><circle cx="78" cy="51" r="8" fill="#ffe7a1"/><path d="m33 84 20-26 17 19 11-14 14 21v6H33Z" fill="#85cfb6"/>',
'store': '<path d="m35 44-5 54h68l-5-54Z"/><path d="M48 50V37a16 16 0 0 1 32 0v13" fill="none" stroke="#c8eaff" stroke-width="5"/><path d="m52 71 9 9 18-20" fill="none" stroke="#32648f" stroke-width="5"/>',
'monitor': '<path d="M24 32h80v54H24Z"/><path d="M30 38h68v42H30Z" fill="#142d40"/><path d="m33 63 13 0 8-17 11 28 9-20 8 9h13" fill="none" stroke="#90f2c5" stroke-width="3"/><path d="M58 86h12v11H47v5h34v-5H70"/>',
'cone': '<path d="m55 27 18 0 22 67H33Z"/><path d="m47 51 34 0 4 12H43Zm-8 25h50l4 12H35Z" fill="#fff3d8"/><path d="M27 94h74v10H27Z"/>',
'ink': '<path d="m64 25 34 54-34 23-34-23Z"/><path d="m64 38 15 26-15 24-15-24Z" fill="#152b41"/><path d="M64 48v32" stroke="#d6ebff" stroke-width="2"/><circle cx="64" cy="64" r="4" fill="#d6ebff"/>',
'music': '<path d="M52 83V38l43-10v45" fill="none" stroke="url(#material)" stroke-width="9"/><path d="m52 43 43-10v11L52 54Z"/><ellipse cx="42" cy="86" rx="15" ry="10" transform="rotate(-18 42 86)"/><ellipse cx="84" cy="77" rx="15" ry="10" transform="rotate(-18 84 77)"/>',
'mail': '<path d="M26 40h76v53H26Z"/><path d="m28 43 36 28 36-28" fill="#cee6ff" stroke="#659dcd" stroke-width="2"/><path d="m28 91 25-24m47 24L75 67" fill="none" stroke="#659dcd" stroke-width="2"/>',
'disk': '<path d="M31 27h66v75H31Z"/><circle cx="64" cy="59" r="25" fill="#b4c2d3"/><circle cx="64" cy="59" r="18" fill="#e2edf7"/><circle cx="64" cy="59" r="7" fill="#2d405b"/><path d="m86 91-18-28 6-4 19 27Z" fill="#607d9e"/><circle cx="39" cy="94" r="2" fill="#32485e"/>',
'document': '<path d="M38 25h36l20 21v57H38Z"/><path d="M74 25v22h20" fill="#9ebcdc"/><path d="M48 60h36M48 70h36M48 80h27M48 90h31" fill="none" stroke="#496e9d" stroke-width="3"/>',
'chart': '<path d="M30 94h68" fill="none" stroke="url(#material)" stroke-width="4"/><path d="M34 66h14v24H34Zm23-20h14v44H57Zm23-17h14v61H80Z"/>',
'cube': '<path d="m64 27 35 20v40l-35 20-35-20V47Z" fill="#79aefe"/><path d="m64 27 35 20-35 20-35-20Z" fill="#d4e9ff"/><path d="m64 67 35-20v40l-35 20Z" fill="#3976c7"/><path d="M64 67v40" stroke="#aad3ff" stroke-width="1"/>',
'palette': '<path d="M64 29c-47-1-51 65-9 71 9 1 14-5 10-13-3-7 4-14 13-11 26 9 26-46-14-47Z"/><circle cx="48" cy="47" r="6" fill="#e27271"/><circle cx="71" cy="43" r="6" fill="#f5be65"/><circle cx="84" cy="59" r="6" fill="#70bba9"/><circle cx="38" cy="66" r="6" fill="#6d9edb"/>',
'network': '<path d="M64 41v39M36 85V67h56v18" fill="none" stroke="url(#material)" stroke-width="5"/><path d="M50 26h28v24H50ZM22 80h28v23H22Zm56 0h28v23H78Z"/>',
'key': '<circle cx="49" cy="51" r="21"/><circle cx="49" cy="51" r="10" fill="#233e63"/><path d="m61 66 31 31 8-8-8-8 5-5-9-9-5 5-13-14Z"/>',
'archive': '<path d="M33 26h62v76H33Z"/><path d="M59 26h11v57H59Z" fill="#9d764b"/><path d="M59 28h6v7h5v7h-5v7h5v7h-5v7h5v7h-5" fill="none" stroke="#f0dbb5" stroke-width="3"/><rect x="57" y="78" width="16" height="15" rx="3" fill="#604d3f"/><rect x="61" y="81" width="8" height="7" fill="#d8ba88"/>',
'game': '<path d="M43 44h42c12 0 24 40 14 47-8 5-18-11-23-13H52c-5 2-15 18-23 13-10-7 2-47 14-47Z"/><path d="M46 54v22m-11-11h22" fill="none" stroke="#344c74" stroke-width="6"/><circle cx="83" cy="58" r="4" fill="#779bcf"/><circle cx="92" cy="69" r="4" fill="#b080cd"/>',
'printer': '<path d="M42 28h44v26H42Z" fill="#e9f2fc"/><path d="M27 49h74v39H27Z"/><path d="M39 73h50v30H39Z" fill="#e9f2fc"/><path d="M47 84h34m-34 8h25" stroke="#7996b6" stroke-width="2"/><circle cx="89" cy="59" r="3" fill="#8bf0b8"/>',
'scan': '<path d="m29 39 66-12 7 15-69 14Z" fill="#c1d6e9"/><path d="M28 58h72v39H28Z"/><path d="M35 64h57v20H35Z" fill="#23496a"/><path d="M39 74h49" stroke="#80dbef" stroke-width="2"/><circle cx="88" cy="90" r="2" fill="#72e6a4"/>',
'font': '<path d="m64 29 30 69H80l-6-16H51l-6 16H31l27-69Zm-9 42h15L62 49Z"/>',
'chip': '<path d="M41 41h46v46H41Z"/><path d="M50 50h28v28H50Z" fill="#2e5370"/><path d="M49 26v15m15-15v15m15-15v15M49 87v15m15-15v15m15-15v15M26 49h15M26 64h15M26 79h15m46-30h15M87 64h15M87 79h15" fill="none" stroke="url(#material)" stroke-width="5"/>',
'help': '<circle cx="64" cy="64" r="36"/><path d="M50 49c0-18 31-17 29 1-1 10-15 10-15 23" fill="none" stroke="#345d8b" stroke-width="7"/><circle cx="64" cy="87" r="4" fill="#345d8b"/>',
'globe': '<circle cx="64" cy="64" r="35"/><ellipse cx="64" cy="64" rx="17" ry="35" fill="none" stroke="#346e9d" stroke-width="3"/><path d="M29 64h70M36 45h56M36 83h56" fill="none" stroke="#346e9d" stroke-width="3"/>',
'sync': '<path d="M36 60a29 29 0 0 1 50-17l9 8M92 68a29 29 0 0 1-50 17l-9-8" fill="none" stroke="url(#material)" stroke-width="8"/><path d="M97 30v24H73ZM31 98V74h24Z"/>',
'volume': '<path d="M28 53h17l23-21v64L45 75H28Z"/><path d="M79 48q16 16 0 32m10-43q27 27 0 54" fill="none" stroke="url(#material)" stroke-width="5"/>',
'sun': '<circle cx="64" cy="64" r="21"/><path d="M64 24v10m0 60v10M24 64h10m60 0h10M36 36l7 7m42 42 7 7M36 92l7-7m42-42 7-7" fill="none" stroke="url(#material)" stroke-width="5"/>',
'keyboard': '<path d="M23 43h82v48H23Z"/><path d="M32 53h7m7 0h7m7 0h7m7 0h7m7 0h7M32 65h7m7 0h7m7 0h7m7 0h7m7 0h7M45 79h37" fill="none" stroke="#476381" stroke-width="5"/>',
'film': '<path d="M28 29h72v72H28Z"/><path d="M43 36h42v23H43Zm0 32h42v25H43Z" fill="#355077"/><path d="M34 36v7m0 10v7m0 10v7m0 10v7M94 36v7m0 10v7m0 10v7m0 10v7" stroke="#385476" stroke-width="4"/>',
'fire': '<path d="M68 23c8 28 28 28 28 49 0 43-69 39-65-2 1-13 11-19 18-32 0 14 4 18 9 19-5-16 2-27 10-34Z"/><path d="M66 58c0 13 13 20 13 29 0 17-29 17-29 0 0-10 8-18 16-29Z" fill="#fff3c5"/>',
'leaf': '<path d="M97 28C46 21 22 46 35 81c24 35 66 10 62-53Z"/><path d="M33 101 84 42M52 79l-7-24m22 7 16 3" fill="none" stroke="#347561" stroke-width="3"/>',
'blender': '<path d="m28 38 30 10-22-21 8-5 36 29c36 10 25 47-6 49-29 2-43-22-27-40l-24 5-4-9 33-7Z"/><ellipse cx="73" cy="73" rx="21" ry="17" fill="#ebf6ff"/><ellipse cx="73" cy="73" rx="14" ry="11" fill="#448ed0"/>',
'brush': '<path d="m50 73 33-46 14 10-36 43Z"/><path d="M50 71c-16-5-17 17-24 22 20 9 38-3 34-15Z" fill="#d7b9dc"/><path d="m51 71 9 7 7-9-9-7Z" fill="#c9d4df"/>',
'antenna': '<path d="M64 59v42M47 101h34M48 43a23 23 0 0 0 0 33m32-33a23 23 0 0 1 0 33M36 29a43 43 0 0 0 0 61m56-61a43 43 0 0 1 0 61" fill="none" stroke="url(#material)" stroke-width="5"/><circle cx="64" cy="58" r="7"/>',
'cup': '<path d="M34 38h52v39c0 26-52 26-52 0Z"/><path d="M86 46h6c24 0 15 31-6 27" fill="none" stroke="url(#material)" stroke-width="7"/><path d="M28 103h65" stroke="url(#material)" stroke-width="4"/>',
}
# name, glyph, shell top, shell base, object light, object base, icon lookup names
SPECS=[
('Ghostty','ghost','#246e9b','#112a43','#f8fbfa','#a9d0dd',['com.mitchellh.ghostty','ghostty']),
('Files','folder','#1b69b4','#143556','#d8efff','#60a4e9',['com.system76.CosmicFiles','system-file-manager','folder']),
('Brave','brave','#c75920','#61260f','#ffdc91','#ef9840',['brave-browser']),
('Obsidian','crystal','#47346c','#191226','#e8d6ff','#8663d4',['obsidian','md.obsidian.Obsidian']),
('ChatGPT','chat','#226c65','#12332f','#e5fff7','#80cbb7',['chatgpt','Chatgpt','codex']),
('Zed','zed','#244369','#0d192b','#eff5ff','#bacdea',['dev.zed.Zed','zed']),
('Settings','settings','#506477','#1f2c3b','#f2f6fa','#8ba6bd',['com.system76.CosmicSettings','preferences-system','preferences-desktop-theme']),
('Player','play','#20599b','#102b50','#e4f6ff','#6fb7f1',['com.system76.CosmicPlayer']),
('Screenshot','camera','#4d426f','#211a36','#ebdef8','#9a87c0',['com.system76.CosmicScreenshot','org.flameshot.Flameshot']),
('Viewer','image','#367967','#173d33','#e5f6ef','#a6d3bf',['com.system76.CosmicViewer','org.gnome.eog']),
('Store','store','#286bc0','#173057','#e5f4ff','#95bcea',['com.system76.CosmicStore','repoman']),
('Monitor','monitor','#356a64','#163530','#d4f3e9','#76b6aa',['com.system76.CosmicMonitor','io.github.kai_j_g.HardwareMonitor']),
('Terminal','code','#3b566f','#152637','#daeefe','#8eb2d0',['com.system76.CosmicTerm','mini.xterm','utilities-terminal']),
('Editor','pen','#375ba8','#182749','#d7eaff','#76a8e9',['com.system76.CosmicEdit','gvim']),
('VLC','cone','#ab4d1c','#4c230e','#ffe8b2','#ef9745',['vlc']),
('Inkscape','ink','#4c5a6e','#18212e','#eff6ff','#8fa8c5',['org.inkscape.Inkscape','inkscape']),
('Blender','blender','#8f4c21','#39220e','#ffd795','#e9974c',['blender']),
('GIMP','brush','#5d4967','#271e30','#fae1dd','#c78db2',['gimp']),
('Music','music','#386248','#142c20','#d8f8cc','#8bc393',['spotify-client','audio-x-generic']),
('Mail','mail','#356bbb','#172e56','#e8f4ff','#8fbceb',['thunderbird','internet-mail']),
('Disks','disk','#4e6174','#1e2b3b','#e8f0f8','#97aec6',['org.gnome.DiskUtility','drive-harddisk']),
('Usage','chart','#3f7267','#172e2b','#d7ffe8','#81c4ae',['org.gnome.baobab','org.gnome.PowerStats']),
('Document','document','#5c6b80','#253145','#f9fbff','#d1e1f3',['org.gnome.Evince','text-x-generic','libreoffice-startcenter']),
('Writer','pen','#285da6','#112947','#e2f0ff','#8cb6e6',['libreoffice-writer']),
('Calc','chart','#317253','#143224','#e0f6de','#90c999',['libreoffice-calc']),
('Impress','image','#a9542d','#442519','#fff0d7','#dca57b',['libreoffice-impress']),
('Draw','palette','#9a6833','#422a13','#fff0c9','#e1bd87',['libreoffice-draw']),
('Math','font','#73507d','#301f39','#f4e1fa','#bd9dca',['libreoffice-math']),
('Network','network','#396786','#183346','#dceffe','#8cb9d6',['preferences-system-network']),
('Keys','key','#8a6b32','#382b14','#fff0bc','#dabb6d',['org.gnome.seahorse.Application']),
('Archive','archive','#81613e','#38291b','#f5dec1','#c9a375',['org.gnome.FileRoller','application-x-archive']),
('Steam','game','#3b526f','#182333','#edf5ff','#a3b8d4',['steam','applications-games']),
('Discord','game','#5752a1','#242148','#f0ecff','#aaa4e8',['discord']),
('Printer','printer','#536272','#212b36','#f1f5fa','#a4b6ca',['printer']),
('Scanner','scan','#3d727b','#18343a','#dff3f6','#89bcc5',['org.gnome.SimpleScan']),
('Fonts','font','#6b546f','#2b2131','#f4e7f2','#b89fc0',['org.gnome.font-viewer','accessories-character-map']),
('Firmware','chip','#5f713e','#28321a','#e9f3cc','#b0c689',['firmware-manager','system76-driver','nvidia-settings']),
('Help','help','#4071a6','#1a314a','#e8f4ff','#9cbedf',['org.gnome.Yelp','dialog-information']),
('Language','globe','#3e7682','#19383e','#d9f4f8','#8cc0cb',['preferences-desktop-locale']),
('Syncthing','sync','#41777c','#19383c','#e6ffff','#8dc6cc',['syncthing','net.blip.Blip']),
('Audio','volume','#6c5c87','#2d253c','#eee5fa','#b9a3d6',['multimedia-volume-control']),
('Keyboard','keyboard','#59677a','#222d3c','#f2f5fa','#a7b8d1',['ibus-setup','input-keyboard']),
('Video','film','#485a83','#1e2942','#e2ebff','#97aed8',['kdenlive','fr.handbrake.ghb']),
('Firefox','fire','#a1522e','#43221b','#ffeab4','#f2a669',['firefox']),
('Darktable','camera','#594e43','#27221c','#f5ece0','#bca891',['darktable','display-im6.q16']),
('Antigravity','antenna','#4c609a','#1d2643','#e6edff','#93a9e0',['antigravity']),
('Slicer','cube','#94603b','#3d291c','#ffe7d1','#d9a27e',['PrusaSlicer','PrusaSlicer-gcodeviewer']),
('Popsicle','chip','#366c86','#172f3e','#e3f5ff','#91bed5',['com.system76.Popsicle']),
('Solaar','sun','#997635','#3b2e17','#fff4bf','#dfc477',['solaar']),
]

def svg(spec):
 name,glyph,top,base,light,dark,aliases=spec
 brand=artwork(name)
 body=brand[0] if brand else GLYPHS[glyph]
 shadow='' if brand else GLYPHS[glyph]
 return f'''<svg xmlns="{NS}" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="128" height="128" viewBox="0 0 128 128">
<title>Studio Objects — {html.escape(name)}</title><desc>Original layered vector icon. Lighting from upper left.</desc>
<defs><linearGradient id="shell" x1=".2" y1="0" x2=".8" y2="1" gradientUnits="objectBoundingBox"><stop stop-color="{top}"/><stop offset="1" stop-color="{base}"/></linearGradient>
<linearGradient id="material" x1=".15" y1="0" x2=".8" y2="1"><stop stop-color="{light}"/><stop offset=".45" stop-color="{light}"/><stop offset="1" stop-color="{dark}"/></linearGradient>
<linearGradient id="rim" x2=".5" y2="1"><stop stop-color="white" stop-opacity=".5"/><stop offset=".5" stop-color="white" stop-opacity=".06"/><stop offset="1" stop-color="black" stop-opacity=".32"/></linearGradient></defs>
<g inkscape:groupmode="layer" inkscape:label="01 · material tile" id="tile"><rect x="6" y="8" width="116" height="116" rx="25" fill="#03070d" opacity=".24"/><rect x="6" y="5" width="116" height="116" rx="25" fill="url(#shell)"/><rect x="6.5" y="5.5" width="115" height="115" rx="24.5" fill="none" stroke="url(#rim)"/><path d="M32 7h64" stroke="white" stroke-opacity=".23" stroke-width="1"/></g>
<g inkscape:groupmode="layer" inkscape:label="02 · cast shadow" id="shadow" transform="translate(0 3)" opacity=".24" fill="#020811">{shadow}</g>
<g inkscape:groupmode="layer" inkscape:label="03 · sculpted object" id="object" fill="url(#material)">{body}</g>
</svg>'''

def main():
 p=argparse.ArgumentParser();p.add_argument('--render',action='store_true');args=p.parse_args()
 masters=ROOT/'masters';masters.mkdir(exist_ok=True)
 out=THEME/'scalable/apps';out.mkdir(parents=True,exist_ok=True)
 mapping={}
 brand_notes=[]
 for spec in SPECS:
  brand=artwork(spec[0])
  if brand:brand_notes.append(brand[1])
  content=svg(spec);master=masters/(spec[0].lower()+'.svg');master.write_text(content)
  for alias in spec[-1]:
   (out/(alias+'.svg')).write_text(content);mapping[alias]={'master':str(master.relative_to(ROOT)),'category':'application','status':'custom'}
 mapping.update(build_symbols(ROOT))
 dirs=['scalable/apps','scalable/actions']
 if args.render:
  for size in (16,24,32,48,64,128,256):
   d=THEME/f'{size}x{size}/apps';d.mkdir(parents=True,exist_ok=True);dirs.append(f'{size}x{size}/apps')
   for spec in SPECS:
    dst=d/(spec[-1][0]+'.png')
    subprocess.run(['inkscape',str(masters/(spec[0].lower()+'.svg')),'--export-width='+str(size),'--export-height='+str(size),'--export-filename='+str(dst)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for alias in spec[-1][1:]:
     (d/(alias+'.png')).write_bytes(dst.read_bytes())
 index='[Icon Theme]\nName=Studio Objects\nComment=Original layered vector icons for COSMIC Studio\nInherits=Conflux,Cosmic,hicolor\nDirectories='+','.join(dirs)+'\n'
 for d in dirs:
  scalable=d.startswith('scalable');size=128 if scalable else int(d.split('x')[0]);index+=f'\n[{d}]\nSize={size}\nContext={'Actions' if d.endswith('actions') else 'Applications'}\nType='+('Scalable\nMinSize=16\nMaxSize=512\n' if scalable else 'Fixed\n')
 (THEME/'index.theme').write_text(index)
 (ROOT/'brand-sources.local.json').write_text(json.dumps(brand_notes,indent=2)+'\n')
 (ROOT/'coverage.json').write_text(json.dumps({'custom_masters':len(SPECS),'custom_names':len(mapping),'icons':mapping,'complete':False,'inherited_fallbacks':'Conflux,Cosmic,hicolor','cursor':'unchanged'},indent=2)+'\n')
 # Vector contact sheet with dark and light surface comparison.
 chunks=[];W=1056;H=180+math.ceil(len(SPECS)/8)*144
 chunks.append(f'<svg xmlns="{NS}" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="#f5f5f7"/><text x="32" y="44" font-family="Instrument Sans,sans-serif" font-size="27" fill="#202024">Studio Objects</text><text x="32" y="73" font-family="Instrument Sans,sans-serif" font-size="14" fill="#56616e">Original vector materials · Inkscape render · application artwork review</text>')
 for i,spec in enumerate(SPECS):
  x=24+(i%8)*128;y=106+(i//8)*144
  # Inline each icon in its own nested SVG; unique paint ids avoid sheet collisions.
  art=svg(spec).replace('id="','id="i'+str(i)+'-').replace('url(#','url(#i'+str(i)+'-').replace('href="#','href="#i'+str(i)+'-')
  chunks.append(f'<g transform="translate({x} {y}) scale(.75)">{art}</g><text x="{x+48}" y="{y+116}" text-anchor="middle" font-family="Instrument Sans,sans-serif" font-size="12" fill="#364153">{html.escape(spec[0])}</text>')
 chunks.append('</svg>');sheet=ROOT/'preview.svg';sheet.write_text(''.join(chunks))
 subprocess.run(['inkscape',str(sheet),'--export-filename='+str(ROOT/'preview.png')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 print(f'{len(SPECS)} editable masters, {len(mapping)} theme lookup names; preview rendered by Inkscape.')
if __name__=='__main__':main()
