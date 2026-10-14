# Studio window controls

The design's rocker: one switch with green minimize, yellow maximize/restore and red close.

- Joined 22 × 14 px segments with 4 px outer corners, a half-pixel outer edge, a top highlight and 1 px dividers.
- Each segment sits in a 22 × 24 px canvas, so the pointer target stays 24 px tall.
- Glyphs are hidden until hover and press. Inactive windows show a neutral rocker until hovered.
- Every role is drawn in four shapes (solo, left, middle, right), so a window with only some controls still shows a complete switch. `<role>.svg` is the usual full-rocker position.
- Normal, hover, pressed and inactive states; PNG exports at 1×–4×.

`preview.png` shows every state, the restore, close-only and no-maximize layouts, and active and inactive titlebars on paper and graphite. `tokens.json` records geometry and colours. Run `python3 build.py`; PNG exports use Inkscape or `rsvg-convert` when either is installed. The previous circular-squircle set is kept in `revisions/before-rocker-20261014/`.

The artwork is integrated through `native/window-controls/`: native COSMIC headerbars, compositor decorations, GTK 3/4 titlebars and an Obsidian titlebar snippet. Native installation takes effect when applications next launch and when the desktop session next starts.
