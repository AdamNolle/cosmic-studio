#!/usr/bin/env python3
"""Strict old-Caffeine popup adapter; requires the reviewed native Iced backport.

This separate adapter never relaxes the modern generator's compatibility rules.
It edits only libcosmic files, not Iced, dependencies, preferences or app sources.
"""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from prepare import replace_once, require_isolated
from header_policy import neutral_header

REVISION = '76c1897d4d9a637c8aa4016483bf05fec5f10ebd'
ICED_REVISION = '7bb364e01d6cd6c07703416828006ab497a082e6'


def transform_app(text):
    text = replace_once(text, '''    pub fn theme(&self, _id: window::Id) -> Theme {
        crate::theme::active()
    }''', '''    pub fn theme(&self, id: window::Id) -> Theme {
        let theme = crate::theme::active();
        #[cfg(all(feature = "wayland", target_os = "linux"))]
        if matches!(self.surface_views.get(&id), Some((_, SurfaceIdWrapper::Popup(_), _))) {
            return crate::theme::popup_material::for_popup(
                theme, iced_winit::commands::blur::available(),
            );
        }
        theme
    }''')
    text = replace_once(text, '    pub fn style(&self, theme: &Theme) -> iced_runtime::Appearance {',
        '''    pub fn style(&self, theme: &Theme) -> iced_runtime::Appearance {
        if crate::theme::popup_material::is_material(theme) {
            return iced_runtime::Appearance {
                background_color: iced_core::Color::TRANSPARENT,
                icon_color: theme.cosmic().on_bg_color().into(),
                text_color: theme.cosmic().on_bg_color().into(),
            };
        }''')
    # Existing lifecycle owns the tuple. The backport records the desired mask
    # before creation, then replays on creation/capability; no polling or timers.
    start = text.index('    pub fn get_popup(')
    end = text.index('    pub fn get_window(', start)
    chunk = text[start:end]
    chunk = replace_once(chunk, '        *self.opened_surfaces.entry(settings.id)',
        '        #[cfg(all(feature = "wayland", target_os = "linux"))]\n        let blur = Self::studio_popup_blur(settings.id, &crate::theme::active());\n        #[cfg(not(all(feature = "wayland", target_os = "linux")))]\n        let blur = Task::none();\n        *self.opened_surfaces.entry(settings.id)')
    chunk = replace_once(chunk, '        get_popup(settings)\n',
        '        Task::batch([blur, get_popup(settings)])\n')
    text = text[:start] + chunk + text[end:]
    text = replace_once(text, '''    ) -> iced::Task<crate::Action<T::Message>> {
        let message = match message {''', '''    ) -> iced::Task<crate::Action<T::Message>> {
        #[cfg(all(feature = "wayland", target_os = "linux"))]
        let refresh_popup = matches!(&message,
            crate::Action::Cosmic(Action::AppThemeChange(_)) |
            crate::Action::Cosmic(Action::SystemThemeChange(_, _)) |
            crate::Action::Cosmic(Action::SystemThemeModeChange(_, _)));
        #[cfg(all(feature = "wayland", target_os = "linux", feature = "xdg-portal"))]
        let refresh_popup = refresh_popup || matches!(&message,
            crate::Action::Cosmic(Action::DesktopSettings(crate::theme::portal::Desktop::ColorScheme(_))) |
            crate::Action::Cosmic(Action::DesktopSettings(crate::theme::portal::Desktop::Accent(_))) |
            crate::Action::Cosmic(Action::DesktopSettings(crate::theme::portal::Desktop::Contrast(_))));
        let message = match message {''')
    text = replace_once(text, '''        #[cfg(all(target_env = "gnu", not(target_os = "windows")))]
        crate::malloc::trim(0);

        message''', '''        #[cfg(all(target_env = "gnu", not(target_os = "windows")))]
        crate::malloc::trim(0);

        #[cfg(all(feature = "wayland", target_os = "linux"))]
        let message = if refresh_popup {
            Task::batch([message, self.studio_refresh_popup_blur()])
        } else {
            message
        };
        message''')
    helper = '''    #[cfg(all(feature = "wayland", target_os = "linux"))]
    fn studio_popup_blur(id: window::Id, theme: &Theme) -> Task<crate::Action<App::Message>> {
        let desired = crate::popup_policy::enabled() && !theme.cosmic().is_high_contrast;
        // Queue desired masks even before the capability announcement. The
        // native backend safely replays them; unavailable remains opaque.
        iced_winit::commands::blur::blur(
            id,
            desired.then(|| vec![iced_core::Rectangle::new(iced_core::Point::ORIGIN, iced_core::Size::INFINITY)]),
        ).discard()
    }

    #[cfg(all(feature = "wayland", target_os = "linux"))]
    fn studio_refresh_popup_blur(&self) -> Task<crate::Action<App::Message>> {
        let theme = crate::theme::active();
        Task::batch(self.surface_views.iter().filter_map(|(id, (_, surface, _))| {
            matches!(surface, SurfaceIdWrapper::Popup(_)).then(|| Self::studio_popup_blur(*id, &theme))
        }))
    }

'''
    # Both methods live in the App implementation; ordinary Window/Layer ids
    # never receive old-client requests or derived translucent palettes.
    text = replace_once(text, '    #[cfg(feature = "wayland")]\n    /// Create a subsurface\n    pub fn get_popup(',
                        helper + '    #[cfg(feature = "wayland")]\n    /// Create a subsurface\n    pub fn get_popup(')
    return text


def prepare(source, output, apply=False, require_backend=True):
    source = source.resolve()
    require_isolated(source)
    if output.resolve().suffix != '.patch':
        raise ValueError('Use a .patch output file.')
    manifest = json.loads((HERE / 'compatibility.json').read_text())
    if (source / '.git').exists():
        actual = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
        if actual != REVISION:
            raise ValueError('Only the exact inspected Caffeine libcosmic revision is supported.')
    for name, expected in manifest['sha256'].items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Changed legacy pinned input: ' + name)
    if require_backend:
        for name, expected in {**manifest['native_api_sha256'], **manifest['native_backport_sha256']}.items():
            backend = source / name
            if not backend.exists() or hashlib.sha256(backend.read_bytes()).hexdigest() != expected:
                raise ValueError('Reviewed native Iced blur backport must be prepared first: ' + name)
    names = ['src/lib.rs', 'src/theme/mod.rs', 'src/app/cosmic.rs', 'cosmic-theme/src/model/theme.rs', 'src/theme/style/iced.rs']
    original = {name: (source / name).read_text() for name in names}
    changed = dict(original)
    changed['src/lib.rs'] = replace_once(original['src/lib.rs'], 'pub mod theme;', 'pub mod theme;\nmod popup_policy;')
    changed['src/theme/mod.rs'] = replace_once(original['src/theme/mod.rs'], 'pub mod style;', 'pub mod style;\npub(crate) mod popup_material;')
    changed['src/app/cosmic.rs'] = transform_app(original['src/app/cosmic.rs'])
    changed['cosmic-theme/src/model/theme.rs'] = replace_once(original['cosmic-theme/src/model/theme.rs'],
        'impl Theme {', 'impl Theme {\n' + (HERE / 'theme_method.rs').read_text())
    changed['src/popup_policy.rs'] = (HERE.parent / 'policy.rs').read_text()
    changed['src/theme/popup_material.rs'] = (HERE / 'material.rs').read_text()
    changed['src/theme/style/iced.rs'] = neutral_header(original['src/theme/style/iced.rs'], legacy=True)
    patch = ''.join(''.join(difflib.unified_diff(
        original.get(name, '').splitlines(keepends=True), text.splitlines(keepends=True),
        fromfile='a/' + name if name in original else '/dev/null', tofile='b/' + name))
        for name, text in changed.items())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(patch)
    subprocess.run(['git', 'apply', '--check', str(output.resolve())], cwd=source, check=True)
    if apply:
        subprocess.run(['git', 'apply', str(output.resolve())], cwd=source, check=True)
    return {'revision': REVISION, 'iced_revision': ICED_REVISION, 'applied': apply,
            'patch': str(output.resolve()), 'changed_files': list(changed)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.output, args.apply), indent=2))
