#!/usr/bin/env python3
"""Generate matching GTK 3/4 titlebutton CSS from the reviewed SVG assets."""
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASE=['button.titlebutton', 'windowcontrols button']
properties='''min-width: 32px;
  min-height: 32px;
  padding: 0;
  margin: 0 3px;
  border: 0;
  border-radius: 8px;
  box-shadow: none;
  background-color: transparent;
  background-size: 32px 32px;
  background-position: center;
  background-repeat: no-repeat;
  transition: none;
  color: #000000;'''
parts=['/* Studio titlebar controls. Artwork includes the black glyph; preserve native actions. */',
       ',\n'.join(BASE)+' {\n  '+properties+'\n}',
       ',\n'.join(s+' image' for s in BASE)+' { opacity: 0; color: transparent; -gtk-icon-shadow: none; }']
for name in ['minimize','maximize','close']:
    for state,suffix in [('normal',''),('inactive',':backdrop'),('hover',':hover'),('pressed',':active'),('inactive',':disabled')]:
        selectors=[s+'.'+name+suffix for s in BASE]
        parts.append(',\n'.join(selectors)+' { background-image: url("assets/'+state+'/'+name+'.svg"); }')
for state,suffix in [('normal',''),('inactive',':backdrop'),('hover',':hover'),('pressed',':active'),('inactive',':disabled')]:
    selectors=['window.maximized '+s+'.maximize'+suffix for s in BASE]
    parts.append(',\n'.join(selectors)+' { background-image: url("assets/'+state+'/restore.svg"); }')
parts.append('button.titlebutton { margin: 0; }')
parts.append(',\n'.join(s+':focus' for s in BASE)+' { outline: 1px solid @theme_selected_bg_color; outline-offset: -1px; }')
(ROOT/'gtk.css').write_text('\n\n'.join(parts)+'\n')
print('Generated GTK titlebar styles.')
