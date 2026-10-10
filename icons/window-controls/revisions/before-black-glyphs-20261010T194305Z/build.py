#!/usr/bin/env python3
"""Build precise, editable Studio window controls using Inkscape."""
from pathlib import Path
import base64, json, subprocess
ROOT=Path(__file__).resolve().parent
SHAPE='M9 2H23C28 2 30 4 30 9V23C30 28 28 30 23 30H9C4 30 2 28 2 23V9C2 4 4 2 9 2Z'
COLORS={'minimize':('#4bd77e','#21b75a','#123d27'),'maximize':('#ffd24b','#f5b51f','#5b3f09'),'restore':('#ffd24b','#f5b51f','#5b3f09'),'close':('#ff6860','#eb3f3a','#fffafa')}
GLYPHS={'minimize':'<path d="M10.5 18.5H21.5"/>','maximize':'<rect x="10.5" y="10.5" width="11" height="11" rx="1"/>','restore':'<path d="M14 10.5H21.5V18M10.5 14H18V21.5H10.5Z"/>','close':'<path d="M11 11L21 21M21 11L11 21"/>'}
def icon(name,state):
    top,bottom,ink=COLORS[name]
    if state=='inactive':top,bottom,ink='#dce1e7','#c6cdd6','#6d7988'
    overlay={'normal':'','hover':'<path d="'+SHAPE+'" fill="white" opacity=".14"/>','pressed':'<path d="'+SHAPE+'" fill="black" opacity=".13"/>','inactive':''}[state]
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><defs><linearGradient id="surface" x2="0" y2="1"><stop stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient></defs><path d="{SHAPE}" fill="url(#surface)" stroke="{ink}" stroke-opacity=".15" stroke-width=".7"/>{overlay}<g fill="none" stroke="{ink}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{GLYPHS[name]}</g></svg>'
for state in ['normal','hover','pressed','inactive']:
    d=ROOT/'svg'/state;d.mkdir(parents=True,exist_ok=True)
    for name in COLORS:
        p=d/(name+'.svg');p.write_text(icon(name,state))
        for size in [24,28,32,48,56,64,96,128,256]:
            out=ROOT/'png'/str(size)/state;out.mkdir(parents=True,exist_ok=True)
            subprocess.run(['inkscape',str(p),'--export-width='+str(size),'--export-filename='+str(out/(name+'.png'))],check=True,capture_output=True)
def pic(name,state,x,y,size):
    return icon(name,state).replace('width="32" height="32"',f'x="{x}" y="{y}" width="{size}" height="{size}"').replace('surface',f'surface-{name}-{state}-{x}-{y}')
parts=['<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1440" height="1000"><rect width="1440" height="1000" fill="#eef1f5"/>']
def text(x,y,s,size=24,color='#354255'):
    return f'<text x="{x}" y="{y}" font-family="DejaVu Sans" font-size="{size}" fill="{color}">{s}</text>'
parts += [text(84,90,'Studio window controls',38),text(84,133,'Green minimize · Yellow maximize · Red close',20,'#718092')]
for i,name in enumerate(['minimize','maximize','close']):
    parts.extend([pic(name,'normal',140+i*440,190,280),text(178+i*440,518,name.capitalize(),25)])
for row,(bg,fg) in enumerate([('#fdfefe','#435065'),('#202a37','#edf2f8')]):
    y=586+row*124
    parts.append(f'<rect x="84" y="{y}" width="1272" height="88" rx="16" fill="{bg}"/>')
    parts.append(text(116,y+53,'COSMIC Studio',22,fg))
    for i,name in enumerate(['minimize','maximize','close']):parts.append(pic(name,'normal',1214+i*38,y+28,32))
parts.append(text(84,900,'32 px controls · 28 px visible shape · hover, pressed, inactive and restore states included',18,'#718092'))
parts.append('</svg>')
(ROOT/'preview.svg').write_text(''.join(parts))
subprocess.run(['inkscape',str(ROOT/'preview.svg'),'--export-filename='+str(ROOT/'preview.png')],check=True,capture_output=True)
(ROOT/'tokens.json').write_text(json.dumps({'order':['minimize','maximize','close'],'canvas':32,'visible_shape':28,'gap':6,'stroke':1.8,'colors':COLORS,'states':['normal','hover','pressed','inactive']},indent=2)+'\n')
print('Built all control states and retina exports.')
