# Application frame outlines

`python3 setup.py frames` applies only `window-frames.css` through GTK's existing
user stylesheet links and the existing light/dark COSMIC palette files. It does
not change the application theme, fonts, icon files/theme, pinned apps, terminal
settings, compositor settings or dock/panel frame. On this machine both GTK
stylesheet links resolve to the same native light palette; links stay intact.

GTK3's installed adw-gtk3 stylesheet draws `decoration` with a blurred shadow
plus a separate `0 0 0 1px` shadow stroke. Its inactive state has the same extra
stroke. The override removes border/outline and that hard stroke, retaining one
restrained soft shadow. Maximized, fullscreen and tiled windows have no shadow.
It keeps native radii, content backgrounds, padding, resize/input regions and
all control/menu/header separator styles.

Chromium's [native GTK window frame provider](https://github.com/chromium/chromium/blob/154.0.8037.98/ui/gtk/window_frame_provider_gtk.cc)
creates `window.background.csd` / `window.background.solid-csd` contexts. GTK3
adds a `decoration` node; GTK4 renders the decoration on the window itself. The
provider renders GTK backgrounds/frames, then caches the assets for each scale.
These outer-node selectors cover that path without selectors for input widgets
or website contents. Browsers using a separate custom frame/theme may have an
independent frame path.

The native COSMIC client audit found zero-width borders on libcosmic's
`Container::WindowBackground` and `HeaderBar`. The compositor active hint was
already disabled. This action does not add a native override.

Each application saves a focused backup and exact changed-file hashes. Restore
protects edits made after application:

```sh
python3 setup.py frames
python3 setup.py verify /path/to/printed/frames-backup
python3 setup.py restore /path/to/printed/frames-backup
```

The setup suite checks shared links, light/dark coverage, idempotence, preservation
of independent settings/icons, rollback on failure, and exact file/mode recovery.
The native GTK3 Cairo check changed decoration pixels while focused-entry pixels
remained identical. GTK3 and GTK4 native parsers reported no CSS errors. This is
rendering/source evidence, not proof that an existing browser's cached frame
has refreshed. No user applications were closed or restarted.

A fresh Brave `154.1.96.61` / Chromium `154.0.8037.98` window was also rendered
on a separate private headless Weston desktop. The disposable profile selected
GTK3; its sole tab was a local blank file. Runtime mappings confirmed the native
GTK3 library, and the exact Chromium version's provider has the selectors above.
Visual review found no black outer stroke, with a restrained soft shadow and
internal controls/separator retained. Both owned fixture process groups were
stopped afterward. Existing user browser windows, profiles, preferences and
cached frame refresh were untouched.

GTK/Chromium may refresh decoration assets only with a theme update or a new
process. If COSMIC regenerates a palette file while editing themes, run `frames`
again; Studio's `shell` and full `apply` actions reappend an already installed
frame import after native synchronization. Typography also reapplies installed
frame imports to both palettes after font updates, including their targets in
its recovery snapshot. The shell uses the native `ExtremelyLow` frosting level
on both mode/builders to keep the backdrop active with minimal diffusion.
There is no polling service or
additional application runtime.
