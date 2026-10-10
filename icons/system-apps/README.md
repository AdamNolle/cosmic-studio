# Studio application icons

71 designs cover the 75 visible application launchers installed when this set was made. Established app marks are retained inside the approved continuous squircle silhouette. The previously approved dock artwork is preserved; Files and Trash keep their requested transparent silhouettes.

Editable compositions are in `sources/svg`, original brand assets are in `sources/original`, and PNGs are exported at 16, 24, 32, 48, 64, 96, 128, 256, 512 and 1024 pixels. Vector sources remain resolution independent; embedded raster marks retain their original source detail. `manifest.json` records source paths, hashes and resolutions. Brand artwork retains its original ownership and license.

The ImageMagick entry uses its bundled Wizard artwork, documented in [ImageMagick's built-in images](https://imagemagick.org/script/formats.php/), replacing the incomplete installed launcher image.

Preview the collection in `gallery-1.png` through `gallery-3.png`. Only application icons are redesigned; inherited file-type, toolbar and status symbols remain available.

## Installation

The active overlay is built into `../approved-dock/theme`. Run from the repository root:

```sh
python3 icons/approved-dock/install.py apply
python3 icons/approved-dock/install.py verify
```

The installer records a reversible backup before changing icons or launcher files. Five launchers originally used absolute icon paths; their user-local overrides preserve launch commands and actions, change the icon name, and normalize NVIDIA's legacy `Terminal=No` spelling to the equivalent `Terminal=false`.

`launcher-map.json` records coverage and `launcher-overrides.json` declares those overrides. Originals under system application directories are untouched. Application updates that introduce new launchers or icon names may need new mappings.

The native Trash menu and compact dock geometry are maintained separately in `../../native/dock-icons`.
