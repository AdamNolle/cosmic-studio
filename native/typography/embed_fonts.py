#!/usr/bin/env python3
"""Embed reviewed fonts in an isolated pinned native libcosmic checkout.

Emit a reviewable diff and apply it only with --apply. Existing native font
loading, its static-byte deduplication, glyph fallback and configured family
overrides remain intact. Installed files and Cargo caches are forbidden.
"""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

PACKAGE = Path(__file__).resolve().parents[2]
PINS = {
    '23f5d63fed2a370f3c2f54b90ec8f0896fe82105': '87e1787fbb9b924576e6f6ea2ef2f45d0729e63d',
    '8cb86195ec576064ac8e59e9200315714d17dc55': '5fc4372d877ad2ca6eaab1c0ca5e424f238b9258',
    '8cb10bf6e24b86a7d2a9cf8c662d3e0154db1b21': 'b5b2b2fcc3e58be793624ba3a7dd45485813935a',
    'd922ac380134c00208d2acf93947d44fb217eec5': 'c781ff6199715f5650411c7ac625d4e1929bfdfb',
    '87ab8179e1bd9880239c340855ae8862034bd0e8': '5fc4372d877ad2ca6eaab1c0ca5e424f238b9258',
    '08a09e3dfa1f729d52585fcedd6e731130235363': '0968a10fc165984080799551124a96adf6be1fb8',
    'd77e99fb1555e2728297677de61e23ada4d9d09b': '87e1787fbb9b924576e6f6ea2ef2f45d0729e63d',
    '03c8f93b294ad239ea935f6dd3c14a15acde8d0d': '6f1b3a71704c4074fad03b3bd6a4203f69556c9e',
    'd921602cde8248c070b493ce43b0edd388e19b9a': '87e1787fbb9b924576e6f6ea2ef2f45d0729e63d',
    '9cc82abd9ca5601bb0341edd12a9acbc97e77801': '39d3c99d1315e9a3db76fa8b32aa91e439c38b32',
    'eaa7a5a24c4359ebeaab507855388942e8984d5d': '5e2b580791e994cb0132c94b32ba4b00bc9ced21',
    '76c1897d4d9a637c8aa4016483bf05fec5f10ebd': '7bb364e01d6cd6c07703416828006ab497a082e6',
    'dc1cf9f00cbe2902a52166492654bb9fee8a73d1': '7346cffd2e51e45fbe4dd31bdd42211b8ca0078e',
    '1f8d8786940cc6db59d412153c5a03f69a20375c': '7918b2826ec8ad4f9e0032f6a21286bac431e482',
    'a401af8b1c54a8abd393b8c5b7c8809402f83850': 'ffe1f1dbe3cbfd313f9b5fe8e36a4af462cae5d7',
}
PREIMAGES = {
    'src/app/mod.rs': '9cf1caf2d774e96e8682c69e5d6b1a612f71c344e738c75d90dee4500991f2ee',
    'src/config/mod.rs': '6a9a66b05e8dc62f337b88ade83102ed520d57fbc421141467f953efa8901cc2',
}
APP_PREIMAGES = {
    '8cb10bf6e24b86a7d2a9cf8c662d3e0154db1b21': '74acc2a2be9e8219252b51940605b4d150b6c891f16c5fa43c855e781309ffa3',
    'd922ac380134c00208d2acf93947d44fb217eec5': '8008abadb0dcb2cebcc43d886100a3f3bfdc6f33688b157a1e63bed56c99d13e',
    '9cc82abd9ca5601bb0341edd12a9acbc97e77801': '50bc446b69f9b11dc2a80fb0df8545df6a4732fa49793efef33087c9e69aae31',
    'dc1cf9f00cbe2902a52166492654bb9fee8a73d1': '50bc446b69f9b11dc2a80fb0df8545df6a4732fa49793efef33087c9e69aae31',
    '1f8d8786940cc6db59d412153c5a03f69a20375c': '50bc446b69f9b11dc2a80fb0df8545df6a4732fa49793efef33087c9e69aae31',
    '76c1897d4d9a637c8aa4016483bf05fec5f10ebd': '5f84a0468bf59c5d435cac4423adc1656a363f74ede5996e631bd637847ccd13',
}
FONT_SYSTEM_SHA256 = '3b7c2245e515f662f30e78c2b9bc52ba8fb3a285d32ca06bc87d6eea5b5dbd20'
LEGACY_REVISION = '76c1897d4d9a637c8aa4016483bf05fec5f10ebd'
LEGACY_FONT_SYSTEM_SHA256 = '0026e099d6451a8cf332a1fbcb575a8c20c7da32527757c272d84675527fe085'
LEGACY_CONFIG_SHA256 = '2fdf497ac66362929d1bdeddac1a4b71d6c1297f7060828d5c171000af7efc23'

FONT_TEST = '''
#[cfg(test)]
mod studio_embedded_font_tests {
    use crate::iced::advanced::graphics::text::cosmic_text::fontdb;
    #[test]
    fn authentic_faces_load_once_with_native_font_system() {
        super::preload_fonts();
        let fonts = crate::iced::advanced::graphics::text::font_system();
        let count_before = fonts.read().unwrap().db().faces().count();
        super::preload_fonts();
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
            }), "Missing native face: {family} {weight} italic={italic}");
        }
    }
}
'''

def digest(data):
    return hashlib.sha256(data).hexdigest()

def legacy_once(app):
    # This reviewed old renderer lacks static-byte pointer deduplication.
    # Its global FontSystem persists; guard the native preload once instead of
    # loading duplicate faces when another application startup path calls it.
    before = '''fn preload_fonts() {
    let mut font_system = iced::advanced::graphics::text::font_system()
        .write()
        .unwrap();

    EMBEDDED_FONTS
        .iter()
        .for_each(move |font| font_system.load_font(Cow::Borrowed(font)));
}'''
    after = '''fn preload_fonts() {
    static PRELOAD: std::sync::Once = std::sync::Once::new();
    PRELOAD.call_once(|| {
        let mut font_system = iced::advanced::graphics::text::font_system()
            .write()
            .unwrap();

        EMBEDDED_FONTS
            .iter()
            .for_each(move |font| font_system.load_font(Cow::Borrowed(font)));
    });
}'''
    if app.count(before) != 1:
        raise RuntimeError('Legacy native preload differs from the reviewed source.')
    return app.replace(before, after)

def legacy_font_test():
    test = FONT_TEST.replace('fonts.read().unwrap().db().faces().count()',
                             'fonts.write().unwrap().raw().db().faces().count()')
    test = test.replace('let fonts = fonts.read().unwrap();',
                        'let mut fonts = fonts.write().unwrap();')
    return test.replace('fonts.db()', 'fonts.raw().db()')

def require_isolated(source):
    source = source.resolve()
    if source.is_relative_to('/usr') or source.is_relative_to('/opt') or (
            '.cargo' in source.parts and ('checkouts' in source.parts or 'registry' in source.parts)):
        raise RuntimeError('Use an isolated source checkout, never installed files or Cargo caches.')
    return source

def assets():
    manifest = json.loads((PACKAGE/'fonts/manifest.json').read_text())
    files = []
    for entries in manifest['families'].values():
        for entry in entries:
            path = Path(entry['file'])
            if path.is_absolute() or '..' in path.parts:
                raise RuntimeError('Unsafe font asset path.')
            data = (PACKAGE/'fonts'/path).read_bytes()
            if digest(data) != entry['sha256']:
                raise RuntimeError('Font checksum mismatch: '+str(path))
            files.append(path)
    if len([path for path in files if path.suffix == '.ttf']) != 10:
        raise RuntimeError('Ten authentic faces are required.')
    for family in ['archivo', 'instrumentserif']:
        if Path(family+'/OFL.txt') not in files:
            raise RuntimeError('Complete font license is required.')
    return files

def changes_for(source, files):
    revision = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    if revision not in PINS:
        raise RuntimeError('Unreviewed libcosmic revision: '+revision)
    iced = subprocess.check_output(['git', '-C', str(source/'iced'), 'rev-parse', 'HEAD'], text=True).strip()
    if iced != PINS[revision]:
        raise RuntimeError('Pinned native Iced submodule is required.')
    native_loader=source/'iced/graphics/src/text.rs'
    loader_hash = LEGACY_FONT_SYSTEM_SHA256 if revision == LEGACY_REVISION else FONT_SYSTEM_SHA256
    if digest(native_loader.read_bytes())!=loader_hash:
        raise RuntimeError('Native font-system preload/dedup API differs from its reviewed source.')
    originals = {}
    preimages=dict(PREIMAGES)
    if revision in APP_PREIMAGES: preimages['src/app/mod.rs']=APP_PREIMAGES[revision]
    if revision == LEGACY_REVISION: preimages['src/config/mod.rs']=LEGACY_CONFIG_SHA256
    for name, expected in preimages.items():
        data = (source/name).read_bytes()
        if digest(data) != expected:
            raise RuntimeError('Native source differs from reviewed preimage: '+name)
        originals[name] = data.decode()
    app = originals['src/app/mod.rs']
    pattern = r'(const EMBEDDED_FONTS: &\[&\[u8\]\] = &\[\n)(.*?)(\n\];)'
    matches = list(re.finditer(pattern, app, re.S))
    if len(matches) != 1 or app.count('font_system.load_font(Cow::Borrowed(font))') != 1:
        raise RuntimeError('Unrecognized native preload path.')
    faces = ''.join('\n    include_bytes!("../../res/studio-fonts/'+str(path)+'"),' for path in files if path.suffix == '.ttf')
    match = matches[0]
    app = app[:match.start()] + match.group(1)+match.group(2)+faces+match.group(3)+app[match.end():]
    # Test native fontdb faces and deduplication without any app/session surface.
    if revision == LEGACY_REVISION:
        app = legacy_once(app)
        app += legacy_font_test()
    else:
        app += FONT_TEST
    config = originals['src/config/mod.rs']
    fallback = 'const SANS_FAMILY_DEFAULT: &str = "Open Sans";'
    if config.count(fallback) != 1:
        raise RuntimeError('Unrecognized native default font fallback.')
    config = config.replace(fallback, 'const SANS_FAMILY_DEFAULT: &str = "Archivo";')
    return revision, {'src/app/mod.rs': (originals['src/app/mod.rs'], app),
                      'src/config/mod.rs': (originals['src/config/mod.rs'], config)}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    source = require_isolated(args.source)
    files = assets()
    revision, changes = changes_for(source, files)
    destination = source/'res/studio-fonts'
    if destination.exists():
        raise RuntimeError('Embedding assets already exist; use a fresh pinned checkout.')
    patch = ''.join(''.join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                              fromfile='a/'+name, tofile='b/'+name))
                    for name, (before, after) in changes.items())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(patch)
    if args.apply:
        destination.mkdir()
        for path in files:
            target = destination/path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PACKAGE/'fonts'/path, target)
        shutil.copyfile(PACKAGE/'fonts/manifest.json', destination/'manifest.json')
        for name, (_, after) in changes.items():
            (source/name).write_text(after)
    print(('Applied' if args.apply else 'Prepared')+' reviewed native font embedding: '+revision)

if __name__ == '__main__':
    main()
