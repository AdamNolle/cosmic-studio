# Window controls checkpoint — 2026-10-10

The approved artwork and implementation are saved in the redesign repository. All work and private builds in this chat have stopped.

Installed: GTK 3/4 styles and titlebutton layout, Zed server-decoration preference, and Obsidian titlebar snippet. These have exact recovery snapshots and preserve existing appearance settings.

Built but not installed: the latest composed compositor, Files, Settings, Text Editor, Terminal, Store, and System Monitor. All preserve the latest shared fonts/materials and the approved colored controls. The compositor's normal and maximized decorations were rendered in an isolated desktop; active focus and the restore symbol are correct.

Pending: Player needs libunwind/libdw development metadata. Viewer was interrupted during the final application stage at the requested stopping point. A complete native rollout and next-login verification remain outstanding. Existing user windows, desktop compositor, and lock screen were not restarted.

Repository files: native/window-controls/{prepare.py,build_gtk.py,gtk.css,build_obsidian.py,obsidian.css,install_gtk.py,README.md,validation/}; hooks in native/compositor/build.py and native/typography/build_core_apps.py; updated icons/window-controls/README.md. Earlier approved icons and dock assets remain unchanged.

Build sources and logs remain in this chat's work/window-controls-native directory. validation/checkpoint.json records exact successful candidate hashes. No native binary is included in the repository.

Toolkit snapshots, in installation order: ~/.local/share/cosmic-studio/window-controls/backups/1791662611180348191/manifest.json and .../1791662898389896766/manifest.json. For complete rollback use install_gtk.py restore --backup PATH in reverse order. No native installation snapshot was created during this button integration.
