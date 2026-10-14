# Studio window controls

Draw the design's window-control rocker in desktop titlebars: green minimize, yellow maximize/restore and red close as joined segments, with glyphs on hover. The source SVGs are in `icons/window-controls/svg`. Every state shares a 22 × 24 px canvas with a 14 px visible segment.

## Native integration

`prepare.py LIBCOSMIC --revision REVISION` applies to the seven supported, pinned SDK sources after the existing typography and material patches. It validates both source transformations before writing, stages the artwork, and restores original source files if writing fails. Reapplying requires a fresh prepared source copy. It never modifies an upstream or another task's source tree implicitly.

The existing Button widget keeps its native event handling and action messages. A cached SVG handle table supplies exact artwork during painting; ordinary icons elsewhere are unaffected. The header bar works out each control's position from the actions the window offers, picks the solo, left, middle or right segment, and lays the group out with no spacing. The keyboard focus ring follows the visible segment. High-contrast themes retain native symbolic controls and theme colors. Keyboard focus retains an accent outline.

`prepare.py COSMIC_COMP --compositor` passes maximization state through to the restore symbol. It also updates activation before the decoration view rebuild, using the compositor's immediate activation state rather than a delayed client acknowledgement. This prevents active buttons from remaining gray.

The compositor and core-app build scripts invoke these hooks after existing styling. The installed binaries are guarded against package-version mismatches by `native/install.py`. A package upgrade falls back to the distribution binary until rebuilt.

## Other applications

`build_gtk.py` produces GTK 3/4 titlebutton CSS. Segment shape follows `:first-child`, `:last-child` and `:only-child`, so reversed or partial decoration layouts still join; GTK 4 spacing is removed with `border-spacing` and GTK 3's fixed 6 px box gap with a negative margin. `install_gtk.py install` adds an import to existing host palettes, preserves GTK symlinks, and installs app-private copies for installed GIMP, darktable, and HandBrake Flatpaks without changing sandbox permissions. It enables the three standard titlebuttons in GTK settings.

The installer also selects server decorations for Zed and enables the generated `obsidian.css` snippet in configured Obsidian vaults. That snippet targets only titlebar minimize, maximize/restore, and close buttons; it preserves other settings and button actions.

Chromium/Brave GTK navigation buttons consume the same artwork. Applications drawing proprietary titlebars without native decorations or a supported style interface may retain their own controls. Tab-close buttons, popup dismiss buttons, and stack-tab close buttons are not window titlebar controls and retain their ordinary symbols.

## Activation and recovery

No installer closes user applications, restarts the running compositor, or changes the lock screen. Reopen applications to activate their new native headerbars. Log out and back in when ready to activate compositor decorations across the session.

Native recovery snapshots are under `~/.local/share/cosmic-studio/native-backups/`; restore a specific manifest with `native/install.py restore --backup PATH`. Toolkit snapshots are under `~/.local/share/cosmic-studio/window-controls/backups/`; run `install_gtk.py restore --backup PATH` in reverse installation order. Both protect later edits by checking installed fingerprints before restoration.

Validation uses a private headless Weston instance and nested COSMIC compositor, with disposable settings and browser profiles. Screenshots cover native Files and Settings, GTK titlebars, Brave navigation buttons, and normal/maximized compositor decorations. They never require restarting the user's desktop or operating on user documents.
