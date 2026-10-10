#!/usr/bin/env python3
"""Give the pinned compositor the canonical native font preload API.

No installed or Cargo-cache files are touched. Native font loading remains in
the same global FontSystem, with one byte array and an explicit Once guard.
The public SDK path works for custom renderers without the winit app module.
"""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
import subprocess

from embed_fonts import assets, require_isolated, FONT_SYSTEM_SHA256, PINS

LIBRARY_PIN = 'd922ac380134c00208d2acf93947d44fb217eec5'
COMPOSITOR_PIN = '0fbd4574ef4caf74769a617d205fd1fc909ac9b1'
PREIMAGES = {
    'src/app/mod.rs': '37e0d20114437e42942602cb1a8fa8ac1e94bf41de087457f0c6d07ee6230408',
    'src/font.rs': 'cb789f6ffb712988ca7f351e9320d37c4075a74a0f0e125b966e7cd79135e586',
}
RENDERER_PREIMAGE = '64a5d562422805c64f44babc26d5d10e2fdf3641163c0a75b26a885fbbd2f879'
NATIVE_TEST = '''
#[cfg(test)]
mod studio_native_font_tests {
    use cosmic::iced::advanced::graphics::text::{cosmic_text::fontdb, font_system};

    #[test]
    fn custom_renderer_fonts_are_authentic_and_loaded_once() {
        cosmic::font::preload();
        let fonts = font_system();
        let count_before = fonts.read().unwrap().db().faces().count();
        cosmic::font::preload();
        let fonts = fonts.read().unwrap();
        assert_eq!(count_before, fonts.db().faces().count());
        for (family, weight, italic) in [
            ("Archivo", 400, false), ("Archivo", 400, true),
            ("Archivo", 500, false), ("Archivo", 500, true),
            ("Archivo", 600, false), ("Archivo", 600, true),
            ("Archivo", 700, false), ("Archivo", 700, true),
            ("Instrument Serif", 400, false), ("Instrument Serif", 400, true),
        ] {
            assert!(fonts.db().faces().any(|face| {
                face.families.iter().any(|(name, _)| name == family)
                    && face.weight.0 == weight
                    && (face.style == fontdb::Style::Italic) == italic
                    && matches!(face.source, fontdb::Source::Binary(_))
            }), "Missing native custom-renderer face: {family} {weight} italic={italic}");
        }
    }
}
'''


def revision(path):
    return subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()


def checked(path, expected):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise RuntimeError('Unreviewed native font/renderer preimage: ' + str(path))
    return data.decode()


def changes_for(library, compositor):
    if revision(library) != LIBRARY_PIN or revision(compositor) != COMPOSITOR_PIN:
        raise RuntimeError('Exact installed compositor and native SDK revisions are required.')
    if revision(library / 'iced') != PINS[LIBRARY_PIN]:
        raise RuntimeError('Exact native Iced submodule revision is required.')
    checked(library / 'iced/graphics/src/text.rs', FONT_SYSTEM_SHA256)
    # The embedding generator already checked complete font provenance. Check
    # the copied assets again before exposing a renderer API to those bytes.
    package = Path(__file__).resolve().parents[2]
    manifest = json.loads((package / 'fonts/manifest.json').read_text())
    if json.loads((library / 'res/studio-fonts/manifest.json').read_text()) != manifest:
        raise RuntimeError('Native embedded font manifest differs.')
    for asset in assets():
        if (package / 'fonts' / asset).read_bytes() != (library / 'res/studio-fonts' / asset).read_bytes():
            raise RuntimeError('Native embedded font asset differs: ' + str(asset))
    originals = {name: checked(library / name, digest) for name, digest in PREIMAGES.items()}
    app = originals['src/app/mod.rs']
    pattern = re.compile(r'const EMBEDDED_FONTS: &\[&\[u8\]\] = &\[\n.*?\n\];\n\n#\[cold\]\nfn preload_fonts\(\) \{\n.*?\n\}', re.S)
    matches = list(pattern.finditer(app))
    if len(matches) != 1:
        raise RuntimeError('Native canonical preload source differs.')
    original_preload = matches[0].group(0)
    array, _ = original_preload.split('\n\n#[cold]\nfn preload_fonts()', 1)
    array = array.replace('include_bytes!("../../res/', 'include_bytes!("../res/')
    if array.count('include_bytes!("../res/studio-fonts/') != 10:
        raise RuntimeError('Canonical preload must contain ten authentic faces.')
    sdk = '''
/// Load the canonical native faces before creating a custom text renderer.
/// Repeated renderer/app construction does no further loading or font scan.
#[cold]
pub fn preload() {
    static PRELOAD: std::sync::Once = std::sync::Once::new();
    PRELOAD.call_once(|| {
        let mut font_system = iced::advanced::graphics::text::font_system()
            .write()
            .unwrap();
        EMBEDDED_FONTS.iter().for_each(|font| {
            font_system.load_font(std::borrow::Cow::Borrowed(font));
        });
    });
}
'''
    app = app[:matches[0].start()] + '#[cold]\nfn preload_fonts() {\n    crate::font::preload();\n}' + app[matches[0].end():]
    font = originals['src/font.rs'].rstrip() + '\n\n' + array + '\n' + sdk
    source = compositor / 'src/utils/iced/mod.rs'
    renderer = checked(source, RENDERER_PREIMAGE)
    before = '        let mut renderer = cosmic::Renderer::new(cosmic::font::default(), Pixels(16.0));'
    if renderer.count(before) != 2:
        raise RuntimeError('Both reviewed custom renderer constructors are required.')
    renderer = renderer.replace(before, '        cosmic::font::preload();\n' + before)
    renderer += NATIVE_TEST
    return {'src/app/mod.rs': (originals['src/app/mod.rs'], app),
            'src/font.rs': (originals['src/font.rs'], font)}, {
            'src/utils/iced/mod.rs': (source.read_text(), renderer)}


def diff(changes):
    return ''.join(''.join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                               fromfile='a/' + name, tofile='b/' + name))
                   for name, (before, after) in changes.items())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('library', type=Path)
    parser.add_argument('--compositor', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    library = require_isolated(args.library)
    compositor = require_isolated(args.compositor)
    library_changes, comp_changes = changes_for(library, compositor)
    args.output.mkdir(parents=True, exist_ok=True)
    for name, changes in [('sdk-preload.patch', library_changes), ('compositor-preload.patch', comp_changes)]:
        (args.output / name).write_text(diff(changes))
    if args.apply:
        for root, changes in [(library, library_changes), (compositor, comp_changes)]:
            for name, (_, after) in changes.items():
                (root / name).write_text(after)
    print(('Applied' if args.apply else 'Prepared') + ' canonical native SDK/custom-renderer font preload')


if __name__ == '__main__':
    main()
