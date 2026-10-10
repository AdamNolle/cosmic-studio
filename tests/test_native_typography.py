"""Strict native typography preparation; never launch a desktop component."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('studio_embed', ROOT/'native/typography/embed_fonts.py')
embed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(embed)

class NativeTypographyTests(unittest.TestCase):
    def test_authentic_faces_and_licenses_are_required(self):
        files = embed.assets()
        self.assertEqual(len([file for file in files if file.suffix == '.ttf']), 10)
        self.assertIn(Path('archivo/OFL.txt'), files)
        self.assertIn(Path('instrumentserif/OFL.txt'), files)

    def test_installed_and_cargo_cache_sources_are_rejected(self):
        for path in ['/usr/src/libcosmic', '/opt/libcosmic', '/tmp/.cargo/git/checkouts/libcosmic']:
            with self.assertRaisesRegex(RuntimeError, 'isolated'):
                embed.require_isolated(Path(path))

    def test_reviewed_legacy_preload_guards_duplicate_faces(self):
        before = '''fn preload_fonts() {
    let mut font_system = iced::advanced::graphics::text::font_system()
        .write()
        .unwrap();

    EMBEDDED_FONTS
        .iter()
        .for_each(move |font| font_system.load_font(Cow::Borrowed(font)));
}'''
        after = embed.legacy_once(before)
        self.assertIn('static PRELOAD: std::sync::Once', after)
        self.assertEqual(after.count('font_system.load_font(Cow::Borrowed(font))'), 1)
        with self.assertRaisesRegex(RuntimeError, 'differs'):
            embed.legacy_once(before.replace('.write()', '.read()'))
        test = embed.legacy_font_test()
        self.assertIn('fonts.write().unwrap().raw().db().faces().count()', test)
        self.assertIn('fonts.raw().db().faces().any', test)
        self.assertIn('fontdb::Source::Binary', test)

    def test_preparation_keeps_native_fallbacks_and_configured_family(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source/'src/app').mkdir(parents=True)
            (source/'src/config').mkdir()
            (source/'iced').mkdir()
            (source/'iced/graphics/src').mkdir(parents=True)
            (source/'iced/graphics/src/text.rs').write_text('reviewed native font-system fixture')
            app = '''const EMBEDDED_FONTS: &[&[u8]] = &[
    include_bytes!("../../res/open-sans/OpenSans-Regular.ttf"),
    include_bytes!("../../res/noto/NotoSansMono-Regular.ttf"),
];
fn preload_fonts() {
    font_system.load_font(Cow::Borrowed(font));
}
'''
            config = 'const SANS_FAMILY_DEFAULT: &str = "Open Sans";\n'
            paths = {'src/app/mod.rs': app, 'src/config/mod.rs': config}
            for name, text in paths.items():
                (source/name).write_text(text)
            hashes = {name: hashlib.sha256(text.encode()).hexdigest() for name, text in paths.items()}
            revision='03c8f93b294ad239ea935f6dd3c14a15acde8d0d';iced=embed.PINS[revision]
            native_hash=hashlib.sha256((source/'iced/graphics/src/text.rs').read_bytes()).hexdigest()
            with patch.object(embed, 'PREIMAGES', hashes), patch.object(embed,'FONT_SYSTEM_SHA256',native_hash), patch.object(embed.subprocess, 'check_output', side_effect=[revision, iced]):
                _, changes = embed.changes_for(source, embed.assets())
            self.assertIn('OpenSans-Regular.ttf', changes['src/app/mod.rs'][1])
            self.assertIn('NotoSansMono-Regular.ttf', changes['src/app/mod.rs'][1])
            self.assertEqual(changes['src/app/mod.rs'][1].count('include_bytes!("../../res/studio-fonts/'), 10)
            self.assertIn('font_system.load_font(Cow::Borrowed(font));', changes['src/app/mod.rs'][1])
            self.assertIn('fontdb::Source::Binary', changes['src/app/mod.rs'][1])
            self.assertEqual(changes['src/config/mod.rs'][1], 'const SANS_FAMILY_DEFAULT: &str = "Archivo";\n')
            self.assertEqual((source/'src/app/mod.rs').read_text(), app)
            (source/'src/app/mod.rs').write_text(app+'// unexpected patch\n')
            with patch.object(embed, 'PREIMAGES', hashes), patch.object(embed,'FONT_SYSTEM_SHA256',native_hash), patch.object(embed.subprocess, 'check_output', side_effect=[revision, iced]), self.assertRaisesRegex(RuntimeError, 'preimage'):
                embed.changes_for(source, embed.assets())

if __name__ == '__main__':
    unittest.main()
