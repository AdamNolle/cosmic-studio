# Studio window controls

A modern vector interpretation of the supplied Windows XP controls, using the Studio squircle shape and restrained shading:

- Green minimize, yellow maximize/restore, red close.
- Pure black symbols across all four button states.
- 32-pixel layout canvas with a 28-pixel visible button and 6-pixel inter-button gap.
- Normal, hover, pressed and inactive states.
- Editable SVGs plus PNG exports at 24, 28, 32, 48, 56, 64, 96, 128 and 256 pixels.

`preview.png` shows enlarged artwork and controls at native size on light and dark titlebars. `tokens.json` records dimensions and colors. Run `python3 build.py` with Inkscape installed to regenerate the set.

The approved artwork is integrated through `native/window-controls/`: native COSMIC headerbars, compositor decorations, GTK 3/4 titlebars, and an Obsidian titlebar snippet. Native installation activates when applications next launch and when the desktop session next starts.
