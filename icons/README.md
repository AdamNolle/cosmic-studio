# Studio Glass app icons

## Active approved dock set

The selected icons now live in [`approved-dock/`](approved-dock/README.md). Use `python3 icons/approved-dock/install.py apply` and `verify` from the repository root for that set. It provides the approved macOS artwork, blue Files icon, and Blender glass Trash with automatic empty/full states. The Studio Objects generator and installer documented below are older inactive studies.

### Audit the selected approved theme

`python3 icons/inventory.py --local-report icons/inventory.local.json` audits
actual exact-case files under `approved-dock/theme` (Studio Dock), not membership
in the older `coverage.json`. It respects XDG launcher priority, recursive
freedesktop desktop IDs and hidden overrides. Declared inherited lookups and
absolute paths are reported separately, never counted as authored coverage.
`env`-wrapped launchers without `TryExec` remain unassessed. An existing report
is never overwritten. This is a filesystem/source audit: theme installation,
application startup, embedded resources and optical quality remain unverified.

The additional CPU/RAM/GPU/disk, multi-monitor brightness and hidden-bar icon
families requested in iteration21 now have parent-reviewed original
[geometry specifications and state/size SVG candidates](utilities/README.md)
with27 passing source tests. Real editable Blender exports, family/glass optics,
active-theme aliases, visual review and native runtime evidence remain open.
No new utility artwork is installed merely by fixing this audit.


The new family uses editable Blender geometry, physical cast-glass volumes,
app-specific colors, beveled identifying objects, and authored lighting. The
theme keeps the established `Studio Objects` lookup name. The previous vector
draft and three initial material studies remain as source history; the new
build entry point is `glass_family.py`.

The art direction takes material and optical-sizing lessons from
[Parakeet's app-icon gallery](https://parakeet.co/app-icons/), following the
user's design skill. None of Parakeet's icons or screenshots are shipped.
Vendor silhouettes remain recognizable, with faithful installed marks or
vendor-published vectors. Original utility metaphors have distinct palettes
and construction. Blender scenes contain packed artwork, materials, cameras,
lighting, and editable geometry.

The source is local by design. `brand-sources.local.json` records each creator,
source, hash, edit, and license scope; generated vendor artwork, machine
inventory, packed scenes, and exports are excluded from the public checkout.
The ChatGPT identifying vector comes from the installed Conflux theme under
GPL-3.0. Brave and Zed use vendor-published vectors. Local app-artwork licenses
have not been established for public redistribution of every source.

## Build and inspect

Asset-build dependencies: Python 3.12 with Pillow, Inkscape, and Blender 5.2.
There is no Python, Blender, shader, or image-generation process at desktop
runtime; native COSMIC and GTK/Qt load ordinary freedesktop icons.

```sh
python3 icons/glass_family.py prepare
blender -b --python-exit-code 1 --python icons/blender/glass_family.py -- --samples 64 --resolution 768
python3 icons/glass_family.py export
python3 icons/inventory.py --local-report icons/inventory.local.json
python3 -m unittest discover -s icons/tests -v
```

`icons/preview.png` shows the complete family and actual 24/32px versions;
`icons/dock-review.png` shows 32/48/64 physical pixels on dark and pale surfaces.
Fixed PNG exports include 16, 20, 24, 32, 36, 40, 48, 64, 72, 96, 128, 192,
256, and 512px, covering common logical dock sizes at 100%, 150%, and 200%.
They use premultiplied-alpha resampling to avoid dark transparent-pixel fringes.
SVG lookups embed an optimized 512px image and contain no external references;
the editable 3D source is `blender/studio-glass-family.blend`.

Simple toolbar and status glyphs stay separate in `symbols.py`. Their semantic
states (muted, battery levels, window controls) remain crisp, recolorable SVGs.
Inherited fallbacks remain for document types and system names outside the
authored family. Embedded application images, thumbnails, and web favicons
use their own assets and are outside icon-theme lookup.

## Reversible local installation

```sh
python3 icons/install.py preview
python3 icons/install.py apply
python3 icons/install.py verify
python3 icons/install.py restore
```

The installer uses standard COSMIC/GTK/Qt icon preferences. App launchers that
use an absolute icon path receive a local desktop-ID override; only the main
`Icon` key changes. Exec commands, Wayland flags, desktop actions, and all other
text are preserved. System launchers are never edited. The private recovery
manifest lives in `~/.local/share/cosmic-studio/icon-backups/`, preserving exact
previous bytes, symlinks, and permissions. Restore refuses to overwrite later
user edits unless `--force` is explicitly supplied.

No shell restart or app shutdown is performed. Existing windows may retain a
cached icon until the app or shell normally refreshes it. `inventory.py` follows
the session's XDG launcher priority, includes `/usr/local/share/applications`,
and reports stale launchers and each missing lookup individually. Executable
availability is checked; app startup success is a separate check.
