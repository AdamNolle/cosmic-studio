#!/usr/bin/env python3
"""Generate/apply popup material changes to one isolated, pinned libcosmic source.

Never installs binaries, changes preferences or edits a Cargo cache. Existing
font edits in unrelated files are left intact. Exact input fingerprints prevent
partial application to a changed upstream implementation.
"""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from window_patch import extend as window_changes
from header_policy import neutral_header
CHECKED = ('src/lib.rs', 'src/core.rs', 'src/app/cosmic.rs', 'src/theme/mod.rs',
           'cosmic-theme/src/model/theme.rs', 'src/theme/style/iced.rs', 'Cargo.toml')


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError('Pinned source shape changed: ' + before[:90])
    return text.replace(before, after, 1)


def profile_for(source, revision):
    profiles = json.loads((HERE / 'compatibility.json').read_text())['profiles']
    matches = [entry for entry in profiles if entry['revision'].startswith(revision)]
    if len(matches) != 1:
        raise ValueError('Specify one supported full revision or unique prefix.')
    profile = matches[0]
    if (source / '.git').exists():
        actual = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
        if actual != profile['revision']:
            raise ValueError('Source HEAD differs from the declared pinned revision.')
    for name, expected in profile['sha256'].items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'Changed pinned input: {name}; no files were modified.')
    return profile


def transform_app(text, expected_loops=5):
    theme_before = '''    pub fn theme(&self, _id: window::Id) -> Theme {
        crate::theme::active()
    }'''
    theme_after = '''    pub fn theme(&self, id: window::Id) -> Theme {
        let theme = crate::theme::active();
        #[cfg(all(feature = "wayland", target_os = "linux"))]
        if let Some((_, surface @ SurfaceIdWrapper::Popup(_), settings, _)) = self.surface_views.get(&id) {
            let blur = crate::popup_policy::resolve_blur(
                self.blur_enabled,
                self.app.core().blur(&theme, Some(*surface)),
                settings(&self.app).blur,
            );
            return crate::theme::popup_material::for_popup(theme, blur);
        }
        theme
    }'''
    text = replace_once(text, theme_before, theme_after)

    text = replace_once(text, '    pub fn style(&self, theme: &Theme) -> theme::Style {',
        '''    pub fn style(&self, theme: &Theme) -> theme::Style {
        // Popup clear color must not inherit an opaque maximized main window.
        if crate::theme::popup_material::is_material(theme) {
            return theme::Style {
                background_color: iced_core::Color::TRANSPARENT,
                icon_color: theme.cosmic().on_bg_color().into(),
                text_color: theme.cosmic().on_bg_color().into(),
            };
        }''')

    # Five independent refresh paths: explicit theme, system palette, system
    # mode, portal dark preference and protocol-capability notification.
    pattern = re.compile(
        r'if (?P<core>core|self\.app\.core\(\))\.blur\(&(?P<theme>theme|cosmic_theme|t), Some\(wrapper\.1\)\)'
        r'\s*&& overriden\.blur\.unwrap_or\(true\)\s*\{\s*cmds\.push\(blur\(\*id\)\);\s*\}'
        r'\s*else if overriden\.blur\.is_some_and\(\|b\| !b\)\s*\{\s*'
        r'cmds\.push\(iced::window::disable_blur\(\*id\)\);\s*\}'
    )
    def refresh(match):
        indent = ' ' * (match.start() - text.rfind('\n', 0, match.start()) - 1)
        lines = ['let surface_blur = crate::popup_policy::resolve_blur(',
                 '    self.blur_enabled,',
                 f'    {match["core"]}.blur(&{match["theme"]}, Some(wrapper.1)),',
                 '    overriden.blur,',
                 ');',
                 'cmds.push(Self::studio_surface_blur(wrapper.1, surface_blur));']
        return lines[0] + ''.join('\n' + indent + line for line in lines[1:])
    text, count = pattern.subn(refresh, text)
    if count != expected_loops:
        raise ValueError(f'Expected {expected_loops} refresh paths, found {count}.')

    opened_before = '                    let blur_cmd = if self.app.core().blur(&theme, wrapper)'
    opened_after = '''                    let blur_cmd = if let Some(surface) = wrapper.filter(|s| matches!(s, SurfaceIdWrapper::Popup(_))) {
                        let explicit = self.surface_views.get(&id).and_then(|s| s.2(&self.app).blur);
                        let enabled = crate::popup_policy::resolve_blur(
                            self.blur_enabled,
                            self.app.core().blur(&theme, Some(surface)),
                            explicit,
                        );
                        Self::studio_surface_blur(surface, enabled)
                    } else if self.app.core().blur(&theme, wrapper)'''
    text = replace_once(text, opened_before, opened_after)

    start = text.index('        if let Some(blur) = live_settings.blur {', text.index('pub fn apply_live_settings('))
    end_match = re.search(r'\n        #\[cfg[^\n]+\]\n        if let Some\(corners\)', text[start:])
    if not end_match:
        raise ValueError('Unrecognized native live-settings blur/corner boundary.')
    end = start + end_match.start()
    text = text[:start] + '''        let automatic = self.app.core().blur(&t, Some(id_wrapper));
        let enabled = crate::popup_policy::resolve_blur(self.blur_enabled, automatic, live_settings.blur);
        if automatic || live_settings.blur.is_some() {
            cmds.push(Self::studio_surface_blur(id_wrapper, enabled));
        }
''' + text[end:]

    helper = '''    /// The same native request path for surface creation and all refreshes.
    /// Window actions and Wayland popup/layer actions use different dispatchers.
    fn studio_surface_blur(id_wrapper: SurfaceIdWrapper, enabled: bool) -> Task<crate::Action<App::Message>> {
        let id = id_wrapper.inner();
        if matches!(id_wrapper, SurfaceIdWrapper::Window(_)) {
            if enabled { window::enable_blur(id) } else { window::disable_blur(id) }
        } else {
            #[cfg(all(feature = "wayland", target_os = "linux"))]
            {
                iced_winit::commands::blur::blur(
                    id,
                    enabled.then(|| vec![iced::Rectangle::new(iced::Point::ORIGIN, iced::Size::INFINITE)]),
                ).discard()
            }
            #[cfg(not(all(feature = "wayland", target_os = "linux")))]
            {
                if enabled { window::enable_blur(id) } else { window::disable_blur(id) }
            }
        }
    }

'''
    text = replace_once(text, '    #[cfg(feature = "surface-message")]\n    /// Apply live setting overrides for a surface',
                        helper + '    #[cfg(feature = "surface-message")]\n    /// Apply live setting overrides for a surface')
    return text


def changes_for(source, revision, window_glass=False):
    profile = profile_for(source, revision)
    if (source / 'src/popup_policy.rs').exists() or (source / 'src/theme/popup_material.rs').exists():
        raise ValueError('Popup material is already prepared; use a fresh isolated source.')
    original = {name: (source / name).read_text() for name in CHECKED if name != 'Cargo.toml'}
    changed = dict(original)
    changed['src/lib.rs'] = replace_once(original['src/lib.rs'], 'pub mod theme;', 'pub mod theme;\nmod popup_policy;')
    changed['src/theme/mod.rs'] = replace_once(original['src/theme/mod.rs'], 'pub mod style;', 'pub mod style;\npub(crate) mod popup_material;')
    changed['cosmic-theme/src/model/theme.rs'] = replace_once(
        original['cosmic-theme/src/model/theme.rs'], 'impl Theme {',
        'impl Theme {\n' + (HERE / 'theme_method.rs').read_text())
    core = original['src/core.rs']
    anchor = '        use iced_winit::SurfaceIdWrapper;\n        let theme = theme.cosmic();'
    guard = '''        use iced_winit::SurfaceIdWrapper;
        // Popup opt-in is independent of whole-window frosting. The client
        // still confirms protocol support before making this material clear.
        if matches!(surface_id_wrapper, Some(SurfaceIdWrapper::Popup(_)))
            && crate::popup_policy::enabled()
        {
            return self.auto_blur.contains(Auto::Popup) && !theme.cosmic().is_high_contrast;
        }
        let theme = theme.cosmic();'''
    changed['src/core.rs'] = replace_once(core, anchor, guard)
    changed['src/app/cosmic.rs'] = transform_app(original['src/app/cosmic.rs'], profile['refresh_paths'])
    changed['src/popup_policy.rs'] = (HERE / 'policy.rs').read_text()
    changed['src/theme/popup_material.rs'] = (HERE / 'material.rs').read_text()
    changed['src/theme/style/iced.rs'] = neutral_header(original['src/theme/style/iced.rs'])
    if window_glass:
        window_manifest = json.loads((HERE / 'window_compatibility.json').read_text())
        if profile['revision'] not in window_manifest:
            raise ValueError('Window glass supports only the inspected native GUI libraries.')
        name = 'src/theme/style/iced.rs'
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != window_manifest[profile['revision']]:
            raise ValueError('Changed pinned window style input: ' + name)
        changed = window_changes(changed, profile['revision'])
    return original, changed, profile


def require_isolated(source):
    if source.is_relative_to('/usr') or source.is_relative_to('/opt') or ('.cargo' in source.parts and 'checkouts' in source.parts):
        raise ValueError('Use an isolated source copy; installed files and Cargo checkouts are read-only.')


def prepare(source, revision, output, apply=False, window_glass=False):
    source = source.resolve()
    require_isolated(source)
    if output.resolve().suffix != '.patch':
        raise ValueError('Use a .patch output file; source/config files cannot be overwritten.')
    original, changed, profile = changes_for(source, revision, window_glass)
    patch = ''.join(''.join(difflib.unified_diff(
        original.get(name, '').splitlines(keepends=True), text.splitlines(keepends=True),
        fromfile='a/' + name if name in original else '/dev/null', tofile='b/' + name))
        for name, text in changed.items())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(patch)
    # git apply works on isolated copies without a .git directory as well.
    subprocess.run(['git', 'apply', '--check', str(output.resolve())], cwd=source, check=True)
    if apply:
        subprocess.run(['git', 'apply', str(output.resolve())], cwd=source, check=True)
    return {'revision': profile['revision'], 'applied': apply, 'window_glass': window_glass, 'patch': str(output.resolve()),
            'changed_files': list(changed), 'input_sha256': profile['sha256']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--window-glass', action='store_true', help='Optional pinned native GUI window profile')
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.revision, args.output, args.apply, args.window_glass), indent=2))


if __name__ == '__main__':
    main()
