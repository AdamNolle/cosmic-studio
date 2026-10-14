#!/usr/bin/env python3
"""Generate matching GTK 3/4 titlebutton CSS from the reviewed rocker SVG assets."""
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASE=['button.titlebutton', 'windowcontrols button']
properties='''min-width: 22px;
  min-height: 24px;
  padding: 0;
  margin: 0;
  border: 0;
  border-radius: 4px;
  box-shadow: none;
  background-color: transparent;
  background-size: 22px 24px;
  background-position: center;
  background-repeat: no-repeat;
  transition: none;
  color: #000000;'''
# Segment corners follow position, so a close-only or reversed layout still reads as one switch.
POSITIONS=[('middle',''),('left',':first-child'),('right',':last-child'),('solo',':only-child')]
STATES=[('normal',''),('inactive',':backdrop'),('hover',':hover'),('pressed',':active'),('inactive',':disabled')]
parts=['/* Studio titlebar rocker. Artwork includes glyphs; preserve native actions. */',
       ',\n'.join(BASE)+' {\n  '+properties+'\n}',
       ',\n'.join(s+' image' for s in BASE)+' { opacity: 0; color: transparent; -gtk-icon-shadow: none; }',
       '/* GTK 4 lays controls out with CSS spacing; GTK 3 keeps a 6 px box gap. */\nwindowcontrols { border-spacing: 0; }',
       'button.titlebutton + button.titlebutton { margin-left: -6px; }']
def rules(role,art,prefix=''):
    for state,suffix in STATES:
        for shape,position in POSITIONS:
            selectors=[prefix+s+'.'+role+position+suffix for s in BASE]
            parts.append(',\n'.join(selectors)+' { background-image: url("assets/'+state+'/'+art+'-'+shape+'.svg"); }')
for role in ['minimize','maximize','close']: rules(role,role)
rules('maximize','restore','window.maximized ')
parts.append(',\n'.join(s+':focus' for s in BASE)+' { outline: 1px solid @theme_selected_bg_color; outline-offset: -1px; }')
(ROOT/'gtk.css').write_text('\n\n'.join(parts)+'\n')
print('Generated GTK titlebar styles.')
