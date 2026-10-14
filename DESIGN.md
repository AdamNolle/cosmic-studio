# Design direction

Archivo is the interface and reading face. Instrument Serif belongs in native titles, section headings, display labels and menu-root headings. Inputs, commands, shortcuts, code and documents retain their appropriate faces and metrics.

The desktop follows the imported [COSMIC Studio Desktop](design/README.md) design: warm paper, ink rules and one accent. The panel and dock share one refractive glass. Windows are single paper sheets with menus in the title bar. Labels stay opaque in both modes, ordinary controls stay neutral, and blue is used only for selection, links and focus. [design/desktop-tokens.json](design/desktop-tokens.json) is the single source for palette and shell geometry; setup and tests read it. Popup surrounds have 0.95 backing and controls 0.98; primary content plates remain opaque.

Window controls are one rocker: green minimize, yellow maximize/restore and red close as joined 22 × 14 px segments with 4 px outer corners and 1 px dividers. Glyphs appear only on hover and press. Inactive windows show a neutral rocker until hovered. A window that offers only some controls still draws a complete switch from the segments it has.

The dock has 8 logical px outer corners, a 3 px inset and no black outline. Hover names are a compact 12 px Archivo Medium tooltip, never a display-sized caption. Running indicators are 2 px bars in plain white on dark glass or black on light: 10 px for one window, 16 px for several, 22 px for the focused application. No per-application colours appear under icons. Windows have approximately 6–8 px corners; popovers 8 px and menus 5 px. The menu bar is 32 px tall with 6 px corners and an 8 px margin, then snaps flush and square for visible maximized or fullscreen windows on its output. Minimized windows must not trigger this. Preserve approved compact spacing and all pins.

Use the approved Studio Dock overlay: 71 application designs cover 75 inventoried launchers. Files keeps its blue folder silhouette; Trash uses the approved frosted vessel with empty/full states. Conflux supplies inherited symbols. Rejected studies stay inactive.

The GPU material uses a bounded analytic screen-space lens with Fresnel highlights, dispersion and static grain. Text/icons sit above it. Reuse native Wayland regions, scale transforms, damage tracking and cached textures. Avoid animation timers and CPU backdrop readback. High-contrast mode retains native opaque materials and symbolic controls.

Selected system windows opt into restrained glass. Content colors remain appropriate for editors, terminals, images, video and documents. Spotify server decorations use its near-black palette through an exact identity policy. Application-drawn titlebars require toolkit or application support.

Keep every installation reversible. Validate candidates in owned isolated sessions before main-session activation. Never restart the running compositor or locker to apply styling. Report settings, prepared sources, builds, visible evidence and pending checks separately.
