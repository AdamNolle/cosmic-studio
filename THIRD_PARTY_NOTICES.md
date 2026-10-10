# Third-party notices

## COSMIC source changes

Native theme data derives from the installed COSMIC configuration. The native panel, compositor and greeter patches are modifications of [System76 COSMIC](https://github.com/pop-os), pinned at recorded installed revisions. Their GPL-3.0 source licenses continue to apply. The compositor shader and native probes carry GPL-3.0-only headers. [libcosmic](https://github.com/pop-os/libcosmic) typography changes retain its MPL-2.0 license; applicable Iced and other dependency notices remain with those source trees.

Compiled native candidates are built locally, with the exact source/patch matrix kept alongside the build scripts. The repository does not vendor a replacement operating system or strip upstream license files.

## Fonts

Archivo comes from [Omnibus-Type Archivo](https://github.com/Omnibus-Type/Archivo); Instrument Serif comes from [Google Fonts](https://github.com/google/fonts/tree/main/ofl/instrumentserif). Both are distributed under the SIL Open Font License 1.1. Each family includes its upstream OFL.txt; fonts/manifest.json records source URLs, revisions and file hashes. Original family names and notices are preserved.

## Application artwork

The glass housings, Blender material/lighting setup and original utility metaphors are authored for this theme. Recognizable application marks are sourced from the user's installed applications or recorded upstream brand artwork. They remain subject to their original copyrights, trademarks and recorded licenses; the setup's MIT license does not relicense them. Machine-specific icon provenance records capture the source, hash, declared license and changes for each identity. Installed proprietary marks and editable packed scenes are local production assets excluded from Git.

The [Parakeet app-icon studies](https://parakeet.co/app-icons/) are a visual material reference. Their icon assets are not copied into this theme.

## Existing Zed theme

The Zed Studio Light theme derives from the One Light theme distributed in [zed-industries/zed](https://github.com/zed-industries/zed/tree/main/assets/themes/one). Its original license is included in licenses/zed-one-LICENSE.txt.

## Design references

The [Liquid Glass for GNOME project](https://github.com/ryohsuke1231/liquid-glass), [Apple materials guidance](https://developer.apple.com/design/human-interface-guidelines/materials), and the user's [design-ui skill](https://github.com/AdamNolle/my-skills) informed the design. No GNOME extension, Apple assets or shader code from those projects is distributed here. COSMIC's existing blur path is extended with an original native material pass.


## Approved macOS dock assets

The active `icons/approved-dock/` set includes official macOS artwork for Brave, Ghostty, Spotify, Obsidian, Zed, and darktable, plus the approved ChatGPT mark adaptation. These assets and marks retain their original ownership and licenses; the repository MIT license does not relicense them. Exact upstream URLs are recorded in `icons/approved-dock/sources/original-provenance.json`. This selected asset directory is separate from the older, locally excluded Studio Objects studies.

The clear-glass Trash vessel and crumpled paper geometry are original Blender work; the blue Files icon preserves the prior COSMIC folder silhouette. [Sam Asante’s liquid-glass reference](https://glass.samasante.com/) informed transparency and edge highlights. No code or image assets from that site were copied.
