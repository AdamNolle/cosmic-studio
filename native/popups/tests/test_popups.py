import gzip
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('popup_prepare', HERE / 'prepare.py')
prepare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare)


def snapshots():
    return json.loads(gzip.decompress((HERE / 'tests/pinned-inputs.json.gz').read_bytes()))


def source_copy(root, files):
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


class PinnedGeneratorTests(unittest.TestCase):
    def test_all_pinned_variants_apply_and_keep_font_work(self):
        for revision, files in snapshots().items():
            with self.subTest(revision=revision), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                source_copy(root, files)
                font = root / 'src/font.rs'
                font.write_text('Existing Archivo and Instrument Serif work\n')
                report = prepare.prepare(root, revision, root / 'popup.patch', apply=True)
                self.assertTrue(report['applied'])
                self.assertEqual(font.read_text(), 'Existing Archivo and Instrument Serif work\n')
                self.assertEqual((root / 'Cargo.toml').read_text(), files['Cargo.toml'])
                app = (root / 'src/app/cosmic.rs').read_text()
                self.assertEqual(app.count('let surface_blur = crate::popup_policy::resolve_blur('), 5)
                self.assertIn('surface @ SurfaceIdWrapper::Popup(_)', app)
                self.assertIn('Self::studio_surface_blur(surface, enabled)', app)
                # Popup refreshes use the same Wayland request dispatcher as
                # creation, rather than a main-window enable/disable action.
                self.assertIn('cmds.push(Self::studio_surface_blur(wrapper.1, surface_blur))', app)
                self.assertNotIn('&& overriden.blur.unwrap_or(true)', app)
                self.assertIn('new_blur = self.blur_enabled', app)
                self.assertIn('!theme.cosmic().is_high_contrast', (root / 'src/core.rs').read_text())
                self.assertEqual((root / 'src/theme/popup_material.rs').read_text(), (HERE / 'material.rs').read_text())
                from header_policy import neutral_header
                self.assertEqual((root / 'src/theme/style/iced.rs').read_text(), neutral_header(files['src/theme/style/iced.rs']))

    def test_header_style_fingerprint_rejects_unknown_chrome_before_any_write(self):
        for revision, files in snapshots().items():
            with self.subTest(revision=revision), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                source_copy(root, files)
                path = root / 'src/theme/style/iced.rs'
                path.write_text(path.read_text() + '// unreviewed future header style\n')
                with self.assertRaisesRegex(ValueError, 'Changed pinned input'):
                    prepare.prepare(root, revision, root / 'popup.patch', apply=True)
                self.assertFalse((root / 'popup.patch').exists())
                self.assertFalse((root / 'src/popup_policy.rs').exists())

    def test_changed_input_rejects_before_any_output_or_source_mutation(self):
        revision, files = next(iter(snapshots().items()))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source_copy(root, files)
            (root / 'src/core.rs').write_text(files['src/core.rs'] + '// unrelated later edit\n')
            before = {name: (root / name).read_bytes() for name in files}
            with self.assertRaisesRegex(ValueError, 'Changed pinned input'):
                prepare.prepare(root, revision, root / 'popup.patch', apply=True)
            self.assertFalse((root / 'popup.patch').exists())
            self.assertFalse((root / 'src/popup_policy.rs').exists())
            self.assertEqual(before, {name: (root / name).read_bytes() for name in files})

    def test_window_profile_is_narrow_and_does_not_change_popup_only_generation(self):
        for revision, files in snapshots().items():
            with self.subTest(revision=revision), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                source_copy(root, files)
                _, popup, _ = prepare.changes_for(root, revision)
                self.assertNotIn('src/window_policy.rs', popup)
                self.assertEqual(popup['src/theme/popup_material.rs'], (HERE / 'material.rs').read_text())
                if revision.startswith(('08a09e3', 'd77e99f', '23f5d63', '03c8f93', '9cc82ab', 'eaa7a5a')):
                    report = prepare.prepare(root, revision, root / 'window.patch', apply=True, window_glass=True)
                    self.assertTrue(report['window_glass'])
                    app = (root / 'src/app/cosmic.rs').read_text()
                    self.assertIn('SurfaceIdWrapper::Window(id)', app)
                    self.assertIn('let geometry_allowed = crate::window_policy::automatic(', app)
                    self.assertIn('for_window(theme, blur && geometry_allowed)', app)
                    self.assertIn('return crate::style::iced::application::style(theme);', app)
                    self.assertIn('let window_surface = crate::window_policy::is_window_surface(', app)
                    self.assertIn('if !window_surface {\n                return theme;', app)
                    self.assertIn('neutral_header_icon(', (root / 'src/theme/style/iced.rs').read_text())
                    self.assertIn('entry.kind == kind', (root / 'src/theme/popup_material.rs').read_text())
                    self.assertIn('if cache.len() == 4', (root / 'src/theme/popup_material.rs').read_text())
                    self.assertEqual((root / 'Cargo.toml').read_text(), files['Cargo.toml'])
                else:
                    with self.assertRaisesRegex(ValueError, 'only the inspected native GUI'):
                        prepare.prepare(root, revision, root / 'window.patch', apply=True, window_glass=True)
                    self.assertFalse((root / 'window.patch').exists())
                    self.assertEqual((root / 'src/core.rs').read_text(), files['src/core.rs'])

    def test_unknown_revision_and_cargo_cache_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaisesRegex(ValueError, 'supported'):
                prepare.profile_for(root, '0000000')
            with self.assertRaisesRegex(ValueError, 'Cargo checkouts'):
                prepare.require_isolated(root / '.cargo/git/checkouts/source')

    def test_repeat_apply_refuses_changed_inputs(self):
        revision, files = next(iter(snapshots().items()))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source_copy(root, files)
            prepare.prepare(root, revision, root / 'popup.patch', apply=True)
            first = (root / 'src/app/cosmic.rs').read_bytes()
            with self.assertRaises(ValueError):
                prepare.prepare(root, revision, root / 'popup.patch', apply=True)
            self.assertEqual(first, (root / 'src/app/cosmic.rs').read_bytes())

    def test_output_cannot_overwrite_a_source_or_configuration_file(self):
        revision, files = next(iter(snapshots().items()))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source_copy(root, files)
            output = root / 'misleading.patch'
            output.symlink_to(root / 'src/lib.rs')
            with self.assertRaisesRegex(ValueError, '.patch output'):
                prepare.prepare(root, revision, output, apply=True)
            self.assertEqual((root / 'src/lib.rs').read_text(), files['src/lib.rs'])


RUST_MATERIAL_TESTS = r'''
mod popup_policy { include!("POLICY_PATH"); }
mod theme {
    use std::sync::Arc;
    #[derive(Clone, Copy, Debug, PartialEq)] pub struct Color { pub alpha: f32, pub tone: u8 }
    #[derive(Clone, Debug, PartialEq)] pub struct Component { pub base: Color, pub divider: Color, pub on: Color, pub on_disabled: Color, pub selected_text: Color, pub hover: Color, pub pressed: Color }
    #[derive(Clone, Debug, PartialEq)] pub struct Container { pub base: Color, pub component: Component, pub divider: Color, pub on: Color }
    #[derive(Clone, Debug, PartialEq)] pub struct CosmicTheme {
        pub transparent_background: Container, pub transparent_primary: Container,
        pub transparent_secondary: Container, pub square_radius: u32, pub text_alpha: f32,
        pub is_high_contrast: bool, pub opaque_base_alpha: f32, pub text_button: Component, pub accent_button: Component, pub is_dark: bool,
    }
    impl CosmicTheme { METHOD_BODY }
    #[derive(Clone, Debug, PartialEq)] pub enum ThemeType { Custom(Arc<CosmicTheme>), System { theme: Arc<CosmicTheme>, prefer_dark: Option<bool> } }
    #[derive(Clone, Debug, PartialEq)] pub struct Theme { pub theme_type: ThemeType, pub transparent: bool }
    impl Theme { pub fn cosmic(&self) -> &CosmicTheme { match &self.theme_type { ThemeType::Custom(t) | ThemeType::System { theme:t, .. } => t } } }
    pub mod popup_material { include!("MATERIAL_PATH"); }
}
#[cfg(test)] mod material_tests {
    use super::theme::*;
    use super::theme::popup_material::{for_popup,is_material};
    use std::sync::Arc;
    fn original() -> Theme {
        let component=Component { base:Color {alpha:0.7,tone:4}, divider:Color {alpha:1.0,tone:0}, on:Color {alpha:0.9,tone:9},on_disabled:Color {alpha:0.65,tone:9},selected_text:Color {alpha:1.0,tone:5},hover:Color {alpha:0.85,tone:6},pressed:Color {alpha:0.0,tone:0} };
        let container=Container { base:Color {alpha:0.9,tone:2}, component:component.clone(), divider:Color {alpha:1.0,tone:0},on:Color {alpha:0.8,tone:9} };
        let cosmic=CosmicTheme {transparent_background:container.clone(),transparent_primary:container.clone(),transparent_secondary:container,square_radius:0,text_alpha:1.0,is_high_contrast:false,opaque_base_alpha:1.0,text_button:component.clone(),accent_button:component,is_dark:true};
        Theme { theme_type:ThemeType::System { theme:Arc::new(cosmic),prefer_dark:Some(true)},transparent:false }
    }
    #[test] fn material_preserves_square_corners_text_and_original_main_palette() {
        let main=original();let before=main.clone();let popup=for_popup(main.clone(),true);
        assert_eq!(main,before);assert!(!main.transparent);assert!(popup.transparent);
        assert_eq!(popup.cosmic().square_radius,0);assert_eq!(popup.cosmic().text_alpha,1.0);
        assert_eq!(popup.cosmic().transparent_background.base.alpha,0.95);
        assert_eq!(popup.cosmic().transparent_background.divider.alpha,0.24);
        assert_eq!(main.cosmic().transparent_background.base.alpha,0.9);
        assert!(matches!(popup.theme_type,ThemeType::System {prefer_dark:Some(true),..}));
        assert!(is_material(&popup));assert!(!is_material(&main));
    }
    #[test] fn missing_protocol_and_explicit_disable_keep_opaque_original() {
        let source=original();let fallback=for_popup(source.clone(),false);
        assert_eq!(source,fallback);assert!(!fallback.transparent);assert!(!is_material(&fallback));
    }
    #[test] fn light_and_dark_keep_neutral_control_backings_and_semantic_accents() {
        for is_dark in [false,true] {
            let mut source=original();
            if let ThemeType::System {theme,..}=&mut source.theme_type { Arc::make_mut(theme).is_dark=is_dark; }
            let before=source.clone();let popup=for_popup(source.clone(),true);
            let material=popup.cosmic();
            for container in [&material.transparent_background,&material.transparent_primary,&material.transparent_secondary] {
                assert_eq!(container.base.alpha,0.95);
                assert_eq!(container.component.base.alpha,0.98);
                assert_eq!(container.on.alpha,1.0);assert_eq!(container.component.on.alpha,1.0);
                assert_eq!(container.component.hover.alpha,0.98);
                assert_eq!(container.component.hover.tone,6);
                assert_eq!(container.component.pressed,container.component.base);
                assert_eq!(container.component.selected_text.tone,5);
            }
            assert_eq!(material.text_button.on,material.transparent_background.on);
            assert_eq!(material.text_button.on_disabled,source.cosmic().transparent_background.component.on_disabled);
            assert_eq!(material.accent_button,source.cosmic().accent_button);
            assert_eq!(source,before);
        }
    }
    #[test] fn repeated_redraw_reuses_palette_arc() {
        let source=original();let first=for_popup(source.clone(),true);let second=for_popup(source,true);
        assert!(std::ptr::eq(first.cosmic(),second.cosmic()));
    }
    #[test] fn high_contrast_keeps_full_opacity_and_the_exact_original_palette() {
        let mut source=original();
        if let ThemeType::System {theme,..} = &mut source.theme_type {
            Arc::make_mut(theme).is_high_contrast=true;
        }
        source.transparent=true;
        let popup=for_popup(source.clone(),true);
        assert!(!popup.transparent);assert!(!is_material(&popup));
        assert_eq!(popup.cosmic().opaque_base_alpha,1.0);
        assert!(std::ptr::eq(source.cosmic(),popup.cosmic()));
        assert_eq!(source.cosmic(),popup.cosmic());
        assert_eq!(popup.cosmic().text_alpha,1.0);
        assert_eq!(popup.cosmic().square_radius,0);
    }
}
'''


@unittest.skipUnless(shutil.which('rustc'), 'Rust compiler required for native material policy tests')
class NativePolicyTests(unittest.TestCase):
    def test_native_policy_and_material_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'tests.rs'
            source.write_text(RUST_MATERIAL_TESTS.replace('POLICY_PATH', str(HERE / 'policy.rs'))
                              .replace('MATERIAL_PATH', str(HERE / 'material.rs'))
                              .replace('METHOD_BODY', (HERE / 'theme_method.rs').read_text()))
            binary = root / 'tests'
            subprocess.run(['rustc', '--edition=2024', '--test', str(source), '-o', str(binary)], check=True, capture_output=True)
            env = os.environ.copy()
            env['COSMIC_STUDIO_POPUP_GLASS'] = '1'
            result = subprocess.run([str(binary), '--test-threads=1'], env=env, text=True, capture_output=True, check=True)
            self.assertIn('10 passed', result.stdout)

    def test_actual_optional_window_policy_and_material_profiles(self):
        revision = next(r for r in snapshots() if r.startswith('08a09e3'))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source_copy(root, snapshots()[revision])
            _, changed, _ = prepare.changes_for(root, revision, window_glass=True)
            material = root / 'generated_material.rs'
            material.write_text(changed['src/theme/popup_material.rs'])
            source = root / 'tests.rs'
            text = RUST_MATERIAL_TESTS.replace('POLICY_PATH', str(HERE / 'policy.rs')) \
                .replace('MATERIAL_PATH', str(material)) \
                .replace('METHOD_BODY', (HERE / 'theme_method.rs').read_text() + (HERE / 'window_method.rs').read_text())
            text = 'mod window_policy { include!("' + str(HERE / 'window_policy.rs') + '"); }\n' + text
            text += r'''
#[cfg(test)] mod window_material_tests {
    use super::theme::*;
    use super::theme::popup_material::{for_popup,for_window};
    use std::sync::Arc;
    #[test] fn window_and_popup_cache_profiles_do_not_alias() {
        let source=super::material_tests::original();
        let popup=for_popup(source.clone(),true);let window=for_window(source.clone(),true);
        assert!(window.transparent);assert!(!std::ptr::eq(popup.cosmic(),window.cosmic()));
        assert_eq!(popup.cosmic().transparent_background.base.alpha,0.95);
        assert_eq!(window.cosmic().transparent_background.base.alpha,0.95);
        assert_eq!(window.cosmic().transparent_primary.base.alpha,1.00);
        assert_eq!(window.cosmic().transparent_secondary.base.alpha,1.00);
        assert_eq!(window.cosmic().transparent_background.component.base.alpha,1.00);
        assert_eq!(window.cosmic().transparent_background.on.alpha,1.0);
        assert_eq!(window.cosmic().accent_button,source.cosmic().accent_button);
        assert!(!source.transparent);assert_eq!(source.cosmic().opaque_base_alpha,1.0);
        let repeated=for_window(source,true);assert!(std::ptr::eq(window.cosmic(),repeated.cosmic()));
    }
    #[test] fn window_protocol_and_high_contrast_fallback_keep_original_palette() {
        let mut source=super::material_tests::original();
        let absent=for_window(source.clone(),false);assert_eq!(absent,source);
        if let ThemeType::System {theme,..}=&mut source.theme_type {Arc::make_mut(theme).is_high_contrast=true;}
        source.transparent=true;
        let window=for_window(source.clone(),true);assert!(!window.transparent);
        assert!(!std::ptr::eq(window.cosmic(),source.cosmic()));
        assert_eq!(window.cosmic(),source.cosmic());
    }
    #[test] fn actual_window_identity_does_not_mark_source_layers_or_popup_fallbacks() {
        let source=super::material_tests::original();
        let window=for_window(source.clone(),false);
        assert!(super::theme::popup_material::is_window_theme(&window));
        assert!(!super::theme::popup_material::is_material(&window));
        assert!(!super::theme::popup_material::is_window_theme(&source));
        let popup=for_popup(source.clone(),false);
        assert!(!super::theme::popup_material::is_window_theme(&popup));
        assert_eq!(source.cosmic(),window.cosmic());
        assert_eq!(source.cosmic(),popup.cosmic());
        assert!(!super::window_policy::is_window_surface(Some(false),true));
        assert!(!super::window_policy::is_window_surface(None,false));
        assert!(super::window_policy::is_window_surface(Some(true),false));
        assert!(super::window_policy::is_window_surface(None,true));
    }
    #[test] fn material_flags_are_independent_in_actual_helpers() {
        let popup_on=super::popup_policy::enabled();
        let window_on=super::window_policy::enabled();
        let mut source=super::material_tests::original();
        // Global native theme can be transparent because the parent window
        // opted in. A disabled popup profile must still stay opaque.
        source.transparent=window_on;
        let popup=for_popup(source.clone(),true);
        assert_eq!(popup.transparent,popup_on);
        source.transparent=false;
        let window=for_window(source,true);
        assert_eq!(window.transparent,window_on);
    }
}
'''
            text = text.replace('    fn original() -> Theme {', '    pub(crate) fn original() -> Theme {')
            source.write_text(text)
            binary = root / 'window-tests'
            subprocess.run(['rustc', '--edition=2024', '--test', str(source), '-o', str(binary)],
                           check=True, capture_output=True)
            env = os.environ.copy()
            env.update(COSMIC_STUDIO_POPUP_GLASS='1', COSMIC_STUDIO_WINDOW_GLASS='1')
            result = subprocess.run([str(binary), '--test-threads=1'], env=env,
                                    text=True, capture_output=True, check=True)
            self.assertIn('16 passed', result.stdout)
            for popup_flag, window_flag in [('0', '1'), ('1', '0'), ('0', '0'), ('1', '1')]:
                env.update(COSMIC_STUDIO_POPUP_GLASS=popup_flag, COSMIC_STUDIO_WINDOW_GLASS=window_flag)
                result = subprocess.run([str(binary), 'material_flags_are_independent_in_actual_helpers', '--test-threads=1'],
                                        env=env, text=True, capture_output=True, check=True)
                self.assertIn('1 passed', result.stdout)

    def test_window_opt_in_is_exact_and_cached_independently(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = Path(folder) / 'window-policy-tests'
            subprocess.run(['rustc', '--edition=2024', '--test', str(HERE / 'window_policy.rs'),
                            '-o', str(binary)], check=True, capture_output=True)
            for value in ['1', '0', 'true', None]:
                env = os.environ.copy()
                env['COSMIC_STUDIO_POPUP_GLASS'] = '1'  # Does not enable window glass.
                env.pop('COSMIC_STUDIO_WINDOW_GLASS', None)
                if value is not None:
                    env['COSMIC_STUDIO_WINDOW_GLASS'] = value
                result = subprocess.run([str(binary), '--test-threads=1'], env=env,
                                        text=True, capture_output=True, check=True)
                self.assertIn('2 passed', result.stdout)

    def test_opt_in_is_exact_and_cached_for_each_initial_environment(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = Path(folder) / 'policy-tests'
            subprocess.run(['rustc', '--edition=2024', '--test', str(HERE / 'policy.rs'),
                            '-o', str(binary)], check=True, capture_output=True)
            for value in ['1', '0', 'true', None]:
                with self.subTest(value=value):
                    env = os.environ.copy()
                    env.pop('COSMIC_STUDIO_POPUP_GLASS', None)
                    if value is not None:
                        env['COSMIC_STUDIO_POPUP_GLASS'] = value
                    result = subprocess.run([str(binary), '--test-threads=1'], env=env,
                                            text=True, capture_output=True, check=True)
                    self.assertIn('5 passed', result.stdout)


if __name__ == '__main__':
    unittest.main()
