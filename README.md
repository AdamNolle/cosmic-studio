# COSMIC Studio

A native COSMIC appearance project implementing the [COSMIC Studio Desktop design](design/README.md): warm paper and ink with one blue accent, Archivo interface text, Instrument Serif headings, readable glass, subtle corners, and the approved Studio Dock application icons.

This is a source checkpoint. See [CHECKPOINT.md](CHECKPOINT.md) for installed changes, validated candidates and remaining work. Native binaries and private recovery data stay local.

## Appearance

| Surface | Current source direction |
| --- | --- |
| Interface text | Archivo, preserving native sizes and weights |
| Titles and headings | Instrument Serif through semantic font roles |
| Code and terminal content | Existing monospace preferences; dark Ghostty palette |
| Palette | Paper and ink in light and dark themes; blue only for selection, links and focus |
| Menu bar | Glass, 6 px corners and 8 px margin; flush square geometry for visible maximized/fullscreen windows |
| Dock | Glass, 8 px outer corners, 3 px inset, no black outline; white/black 2 px running bars whose width marks focus |
| Dock layout | Approved 60 px icons in 66 × 72 px cells, minimal padding and 4 px spacing |
| Menus and tooltips | Readable glass surround, denser controls and opaque labels; compact 12 px hover names |
| Application content | Native content colors; six selected system apps can opt into quiet window glass |
| Window buttons | One rocker: green minimize, yellow maximize/restore and red close segments, glyphs on hover |
| Application icons | Studio Dock covers 75 inventoried launchers with 71 designs; Conflux supplies remaining symbols |

Latest source configuration: panel opacity 0.92 and dock opacity 0.86, multiplied by native gradient backing factors 0.96 and 0.82. Popup surrounds use 0.95 backing, controls 0.98, and primary window content remains opaque. These are material parameters, not measured final pixel opacity. All final configurations and rebuilt binaries have not been activated together on the main desktop.

## Install and restore

Run as the desktop user without sudo. Read the checkpoint and component documentation before installing candidates.

```sh
python3 setup.py typography
python3 setup.py shell
python3 setup.py frames
python3 icons/approved-dock/install.py apply
python3 icons/approved-dock/install.py verify
```

These actions preserve unrelated preferences and create reversible backups. Typography installs pinned OFL fonts and toolkit settings. Shell imports native themes and panel settings while preserving GTK/Qt chrome. Frames removes outer GTK strokes while retaining keyboard focus and shadows. The broader original `setup.py apply` also applies application presets; read its instructions first.

```sh
python3 setup.py verify
python3 setup.py restore backups/TIMESTAMP-ID
python3 icons/approved-dock/install.py restore
```

Recovery preserves bytes, permissions, symlinks and previously absent files, and protects later edits. Restore layers in reverse installation order. Machine-specific backups and reports are excluded from Git.

Approved assets, Blender scenes, SVGs and exports are in [approved-dock](icons/approved-dock/README.md), [system-apps](icons/system-apps/README.md) and [window-controls](icons/window-controls/README.md). Older Studio Objects studies are inactive. The Trash watcher changes launcher artwork only.

## Windows development VM

Use the [isolated Pop!_OS VM tooling](native/vm/README.md) to edit this repo on Windows and build/test inside Linux. It verifies the official ISO, preserves existing VMs, exports explicit source inputs and retains source/recovery reports. Native runtime and hardware validation remain separate completion gates.

## Native Rust integration

Typography and materials require changes to statically linked libcosmic and COSMIC clients. Builders pin revisions and retain native Iced shaping, glyph caches, Wayland input and scaling. Preparation refuses unsupported sources. Builders create candidates without installing or stopping the desktop.

```sh
python3 native/build_shell.py --help
python3 native/typography/build_core_apps.py --help
python3 native/compositor/build.py --help
python3 native/thirdparty/build.py --help
python3 native/greeter/prepare.py --help
```

Component documentation records dependencies, source pins and installation commands. The installer validates ELF candidates and installed package revisions, then creates rollback manifests.

```sh
python3 native/install.py install --panel-binary /absolute/path/to/cosmic-panel
python3 native/install.py restore --backup /absolute/path/to/native-manifest.json
```

It never stops the compositor, restarts the locker or closes user windows. A compositor wrapper takes effect on a later login. A user-local locker candidate does not deploy the system greeter. Window buttons have their own [checkpoint](native/window-controls/CHECKPOINT.md).

## Glass and Wayland

The opt-in compositor material (`COSMIC_STUDIO_LIQUID_GLASS=1`) uses GPU screen-space refraction, Fresnel highlights, static grain and bounded dispersion over COSMIC's native backdrop blur. It has four texture samples, no animation clock and no CPU screenshot loop. It reuses native regions, damage handling and cached targets. Text/icons retain ordinary rendering. Shader failure retains native frosting.

Profiles cover Panel, Dock, tracked menus/tooltips and six opt-in native windows. Terminal, editor, document, video and image content retain their own rendering. The effect is an analytic lens over a captured backdrop, rather than hardware ray tracing of a 3D desktop scene.

`native/wayland_audit.py` checks backend evidence, scales, Qt plugins and Flatpak sockets. Existing Electron/Ozone flags, launcher actions and supported X11 fallbacks are preserved. Prepared Flatpak candidates require no added permissions.

## Verification

```sh
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s native/tests -v
python3 -m unittest discover -s native/popups/tests -v
python3 -m unittest discover -s icons/tests -v
python3 -m compileall -q setup.py native icons
```

Checks cover recovery, source guards, contrast, exports and launcher actions. Selected native builds, font database checks and isolated Wayland fixtures passed. GPU timings measure the final shader only, excluding blur and total frame cost. Mixed-scale interaction, adaptive menu-bar geometry, final dock rendering and login persistence remain validation tasks.

## Design and licenses

The user's [design skill](https://github.com/AdamNolle/my-skills), [Archivo](https://www.beautifulwebtype.com/archivo/), [Instrument Serif](https://www.beautifulwebtype.com/instrument-serif/), [liquid-glass references](https://github.com/ryohsuke1231/liquid-glass) and [Parakeet studies](https://parakeet.co/app-icons/) informed the work. Setup code is MIT; patches retain upstream licenses, fonts are OFL, and third-party marks retain their ownership. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and provenance records.
