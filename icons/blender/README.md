# Blender scenes

The current family is `studio-glass-family.blend`: a separate editable scene for
each app, with packed identifying artwork, physical biconvex glass geometry,
pigmented backing, beveled relief, studio lights, and a near-frontal camera.
The new build script is `glass_family.py`; use the preparation/export commands
in [the icon README](../README.md). See [GLASS-CONTRACT.md](GLASS-CONTRACT.md)
for the current design and review decisions. The desktop loads offline PNGs.

The following documents the earlier three material studies. It is source
history rather than the active icon-build path.

## Initial studies

Open `studio-material-studies.blend` in Blender. It contains separate Ghostty,
Darktable and Brave scenes with editable geometry, materials, lights and cameras.

Rebuild with Blender 5.2.2:

```sh
blender -b --python-exit-code 1 --python build.py
```

The accepted technical render pass uses Cycles with CPU denoising in Blender
5.2.2. The previous 4.0 distribution build lacked OpenImageDenoise; its noisy
initial images were rejected. Eevee was used for intermediate material checks.
The script currently loads the installed legacy SVG importer from
`/usr/share/blender/scripts/addons/io_curve_svg` for Brave's exact curves. This
local dependency still needs a portable replacement before general release.
The earlier desktop icon draft was rolled back; these images remain studies.

Brave's original vector source comes from
[brave/leo](https://github.com/brave/leo/blob/main/icons/brave-icon-release-color.svg).
The identifying artwork remains Brave's; the local study adds a material and
lighting treatment. This source and generated brand studies are excluded from
the public-source checkout pending a distribution-license review.

See DESIGN-STUDY.md for the observed design principles and review criteria.
