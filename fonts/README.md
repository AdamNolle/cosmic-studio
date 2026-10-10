# Pinned font sources

Archivo is supplied as the author's original static Regular, Italic, Medium,
Medium Italic, SemiBold, SemiBold Italic, Bold and Bold Italic TTF files.
Instrument Serif uses the original Regular and Italic TTF files from Google
Fonts. Each family includes its complete SIL Open Font License 1.1 notice.

The exact upstream Git revision, download URL, byte count and SHA-256 checksum
of every asset are in `manifest.json`. The installer checks the entire manifest
before installing any file. It copies originals into the user's private
`~/.local/share/fonts/cosmic-studio` directory, preserves existing files in a
reversible backup, and refreshes Fontconfig through its native cache tool.

Archivo's static faces avoid differences in variable-font default-instance
matching between desktop text engines. Instrument Serif has no bold face;
display titles use its real 400-weight face rather than synthetic bold.
Font lookup and glyph shaping continue through COSMIC's native Rust libraries
and the application's native toolkit. No web font request or runtime font
conversion is involved.

Sources:

- [Archivo by Omnibus-Type](https://github.com/Omnibus-Type/Archivo)
- [Instrument Serif in Google Fonts](https://github.com/google/fonts/tree/main/ofl/instrumentserif)
- [Requested Archivo reference](https://www.beautifulwebtype.com/archivo/)
- [Requested Instrument Serif reference](https://www.beautifulwebtype.com/instrument-serif/)
