# Imported desktop design

`reference/COSMIC Studio Desktop.dc.html` is the claude.ai/design prototype this repository implements, imported on 2026-10-14. It is a browser mock-up of the shell, kept for reference; it loads assets from the design project and is not installed anywhere.

[`desktop-tokens.json`](desktop-tokens.json) translates it into values the native layers consume:

| Design element | Native implementation |
| --- | --- |
| Paper/ink palette, one blue accent | `setup.py prepare` writes `studio-light.ron` / `studio-dark.ron`; `glass-gtk.css` and `glass-qt.qss` restyle toolkit chrome |
| Menu bar: 8 px margin, 6 px corners | `PANEL` settings in `setup.py` |
| Dock: 8 px corners, 8 px margin | `DOCK` settings in `setup.py` |
| Dock indicators | `native/dock-icons/compact-icons.patch`: monochrome 2 px bars, width marks focus |
| Dock and panel hover names | `native/dock-icons/prepare_tooltip.py`: compact 12 px applet tooltips |
| Window-control rocker | `icons/window-controls/build.py`, `native/window-controls/` (libcosmic, compositor decorations, GTK 3/4, Obsidian) |

Two parts of the prototype are deliberately not reproduced: the large italic serif caption above a hovered dock icon, and the coloured glow pools and bars under running applications. Hover names stay small and indicators stay black or white.

Parts of the prototype that describe behaviour rather than appearance — the workspace peek, the pinned CPU/memory popovers, the quick-settings tiles and the launcher — map onto existing COSMIC applets (workspaces, Sysinfo, quick settings, launcher). Their native refinements are tracked in [to-do.md](../to-do.md).

`tests/test_setup.py` (`DesignTests`) checks that the committed themes, shell settings, dock patch and rocker assets match the tokens.
