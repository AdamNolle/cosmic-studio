# Typography contract and implementation

The supported system and toolkit configuration selects Archivo for interface
text. Instrument Serif regular is the display face for supported semantic
headings. Both native GTK palettes retain the managed font stylesheet, including
when COSMIC regenerates its toolkit theme. Terminal, code, symbols and embedded
document fonts keep their own roles.

Native COSMIC clients initialize a font database at startup. The reviewed
embedding patch includes all ten authentic Archivo/Instrument Serif faces and
license records; actual native font-database tests check family, weight, style,
Binary-backed faces and repeated-preload deduplication. Fontconfig resolution
alone does not establish what an already-running client renders.

At this publication checkpoint, the existing font/toolkit configuration is
applied, and reviewed native candidates cover body fonts and the canonical title
helpers. The latest additional menu-heading and prominent shell-title roles are
applied to prepared sources, with clean replay and fingerprint checks, but await
their next native rebuild. The Calendar's selected-date role remains a prepared
patch. Existing applications and the active compositor are left running; source
preparation and a staged candidate are distinct from a verified live process.
The login/lock candidate embeds both families and has a safe isolated preview,
but is not installed over an active greeter.

Archivo remains the configurable native interface role; an explicit configured
family override wins. Instrument Serif is assigned to semantic titles rather
than tiny utility captions. See the [native component build instructions](native/typography/README.md)
for exact pins, build commands, runtime limits and applet dispatch requirements.

The desktop is a repeated working environment. Archivo carries controls,
navigation and reading text; Instrument Serif brings the user's editorial
character to supported titles. Tiny captions remain utility text, and code
retains its established monospace family. This applies the user's Design UI
skill through type roles and coherent material rather than changing familiar
navigation or content.

`python3 setup.py typography` applies only the reversible font installation and
supported toolkit roles. It prints its exact backup and restore command.
`python3 setup.py verify <backup-path>` checks that typography profile, and
`python3 setup.py restore <backup-path>` restores original bytes, permissions,
symlinks, GSettings values and absent files. Restoration rejects intervening
file edits unless explicitly forced. Full `setup.py apply` includes these same
fonts in its appearance backup.

| Surface | Font role | Implementation scope |
|---|---|---|
| COSMIC native controls | Archivo | Existing Tk v1 `interface_font` schema |
| Native titles and header bars | Instrument Serif | Canonical helper patch in reviewed candidates; additional menu/shell roles await rebuild |
| GTK controls | Archivo | GSettings plus GTK 3/4 `gtk-font-name` |
| GTK semantic titles | Instrument Serif regular | Supported title/header CSS classes |
| Qt controls | Archivo | Qt5ct/Qt6ct and KDE native font configuration |
| Qt group/dock titles | Instrument Serif regular | Supported Qt title subcontrols; client behavior needs inspection |
| Zed interface | Archivo | Supported `ui_font_family`; editor/terminal fonts retained |
| Ghostty terminal | iA Writer Mono S | Prior approved dark palette, padding and font retained |
| Ghostty header/menu chrome | Display title plus dark controls | Separate process-local GTK stylesheet; no palette bleed into light apps |
| Obsidian | Archivo plus Instrument Serif | Delivered snippet; enable in a vault to apply |
| Lock/login UI | Archivo plus Instrument Serif | Embedded-font candidate and isolated preview verified; active greeter unchanged |

Existing point sizes, fractional sizes, user text scaling, toolkit backend
selection, cursor settings and monospace choices are preserved. Fontconfig
prefers Archivo for `sans-serif` and `system-ui`; it does not replace arbitrary
serif, monospace, emoji or application-specific font families. No global
`GDK_BACKEND`, `QT_QPA_PLATFORM`, or antialiasing override is introduced. Wayland
display scaling and COSMIC's native shaping/cache remain in control.

Authentic fonts and license/checksum records are in `fonts/`. The native helper
patch is documented in `native/typography/README.md`. Stock COSMIC Tk v1 has no
separate heading-font preference; CSS cannot replace its native Rust widgets.
Rebuilt title helpers use a static `Font::with_name` key with existing sizes and
line heights. Applications with custom heading code or independent preferences
require their own supported integration.

Fontconfig resolution and exact assets are mechanically checked. Existing
processes may have loaded their font collection before installation and need
their next normal launch. A stored configuration or matched font file does not
establish the visual result: check actual long titles, fallback characters,
numbers, focus/disabled states and both display scales before claiming final
coverage. The login greeter runs under another account, so a user's font
directory cannot establish login coverage; its candidate must embed the
licensed fonts or use an authorized system font install.

The meaningful recovery, idempotence, checksum, point-size and prior-preference
tests are in `tests/test_setup.py`. The font changes add no background renderer,
live conversion, network font request or recurring task. Runtime performance
still needs measurement of the actual native client; no performance score is
inferred from the use of static assets.
