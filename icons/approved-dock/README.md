# Approved dock icons

This is the selected macOS-based dock set with a blue Files icon and a clear-glass Trash icon. It supersedes the previous inactive icon studies for these dock apps only. Studio Dock inherits the existing Conflux theme for all other icons.

Trash has two matched states, `trash-empty.png` and `trash-full.png`. The full state contains original modeled crumpled paper. Both are rendered in Blender with transparent backgrounds. The blue Files icon uses a taller, near-square folder silhouette with continuous rounded corners, retaining its tab and transparent background. It is rendered from an editable SVG in Inkscape.

## Install and recovery

Run from this directory:

```sh
python3 install.py apply
python3 install.py verify
python3 install.py restore
```

The installer saves exact prior files and the previous icon-theme setting before changing anything. It never modifies or deletes trash contents. Recovery details are recorded in `installation.local.json`; backups live in the user's data directory.

The COSMIC Trash launcher automatically uses the full icon when GIO reports one or more trashed items. A user path unit responds to local Trash changes; a 30-second timer also catches changes on removable volumes. Only its Icon entry changes; launch commands and actions are preserved.

## Files

- `png/4096/`: true high-resolution vector or Blender masters. Glass masters retain 16-bit PNG channels.
- `png/32/` through `png/1024/`: transparent dock exports. Native raster app icons retain their genuine 1024px detail.
- `sources/blender/`: editable empty/full glass bin scenes with camera, materials, lights, and paper meshes.
- `sources/svg/files.svg`: editable blue folder.
- `theme/`: installable freedesktop overlay and all app-name aliases.
- `glass-and-blue-preview.png`, `complete-set-light.png`, and `complete-set-dark.png`: review images.

The glass study follows the restrained edge highlights and transparency in [Sam Asante's liquid-glass reference](https://glass.samasante.com/). These are static PNGs: their alpha reveals the desktop, while the paper refraction is rendered into the image. PNG icons cannot dynamically refract live wallpaper.

## Artwork credits

Brave, Ghostty, Spotify, Obsidian, Zed, and darktable use their official macOS artwork. ChatGPT retains its established mark in the approved adaptation. Native artwork and third-party marks remain the property of their respective owners; their inclusion is not a claim of original authorship or an MIT relicensing. Exact source URLs and revision details are recorded under `sources/`. New glass geometry, paper geometry, blue-folder finishing, and integration scripts are part of this redesign.


## Folder variants

`files-empty.png` and `files-full.png` share the same rounded blue body and slightly shorter tab. The full version has two paper sheets tucked behind the front panel. Both are available as editable SVGs and 32–4096px PNGs. `files.png` remains an alias of the empty version used by the Files dock launcher. The named theme icons are `studio-folder-empty` and `studio-folder-full`. These are artwork alternatives; no folder-content watcher is installed.


Applying the theme also reloads the COSMIC dock applets on all active displays through the panel configuration watcher. Legacy ChatGPT and darktable favorites are normalized to their installed desktop IDs, preserving the pinned applications and their order.
