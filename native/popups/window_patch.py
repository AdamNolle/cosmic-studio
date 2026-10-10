"""Optional, version-pinned native system-window additions to the popup patch.

The popup-only patch stays independent. This profile is supported solely by
inspected native GUI toolkit implementations, not arbitrary clients.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUPPORTED = ('08a09e3dfa1f729d52585fcedd6e731130235363',
             'd77e99fb1555e2728297677de61e23ada4d9d09b',
             '23f5d63fed2a370f3c2f54b90ec8f0896fe82105',
             '03c8f93b294ad239ea935f6dd3c14a15acde8d0d',
             '9cc82abd9ca5601bb0341edd12a9acbc97e77801',
             'eaa7a5a24c4359ebeaab507855388942e8984d5d')


def once(text, before, after):
    if text.count(before) != 1:
        raise ValueError('Pinned window source shape changed: ' + before[:90])
    return text.replace(before, after, 1)


def extend(changed, revision):
    if revision not in SUPPORTED:
        raise ValueError('Window glass supports only the inspected native GUI libraries.')
    changed = dict(changed)
    changed['src/lib.rs'] += '\nmod window_policy;\n'
    changed['src/window_policy.rs'] = (HERE / 'window_policy.rs').read_text()

    core = changed['src/core.rs']
    core = once(core, '    pub fn frosted(&self, theme: &cosmic_theme::Theme) -> bool {',
        '''    pub fn frosted(&self, theme: &cosmic_theme::Theme) -> bool {
        if crate::window_policy::enabled() && matches!(self.app_type, AppType::Window)
            && self.main_window_id().is_some()
        {
            return self.studio_window_glass_automatic(theme);
        }''')
    core = once(core, '        let theme = theme.cosmic();\n        match surface_id_wrapper {',
        '''        if crate::window_policy::enabled()
            && matches!(self.app_type, AppType::Window)
            && (matches!(surface_id_wrapper, Some(SurfaceIdWrapper::Window(_)))
                || (surface_id_wrapper.is_none() && self.main_window_id().is_some()))
        {
            return self.studio_window_glass_automatic(theme.cosmic());
        }
        let theme = theme.cosmic();
        match surface_id_wrapper {''')
    core = once(core, '    pub fn set_auto_corner_radius(&mut self, auto_corner_radius: BitFlags<Auto>) {',
        '''    fn studio_window_glass_automatic(&self, theme: &cosmic_theme::Theme) -> bool {
        crate::window_policy::automatic(
            self.auto_blur.contains(Auto::Window),
            theme.is_high_contrast,
            self.window.sharp_corners || self.window.is_maximized,
            theme.frosted_maximized_apps,
        )
    }

    pub fn set_auto_corner_radius(&mut self, auto_corner_radius: BitFlags<Auto>) {''')
    changed['src/core.rs'] = core

    app = changed['src/app/cosmic.rs']
    app = once(app, '        if let Some(style) = self.app.style() {',
        '''        if crate::theme::popup_material::is_window_theme(theme) && !theme.transparent
        {
            // Respect this surface's opaque fallback, not stale global state
            // during a maximize/tile transition or a protocol/accessibility gate.
            return crate::style::iced::application::style(theme);
        }
        if let Some(style) = self.app.style() {''')
    # Native geometry events retain corner synchronization and refresh only
    # the opted-in Window's exact blur request. No popup/layer gets this policy.
    app = once(app, '                    return Task::batch([corner_radius(id, cur_rad).discard()]);',
        '''                    let mut commands = vec![corner_radius(id, cur_rad).discard()];
                    if crate::window_policy::enabled()
                        && matches!(self.app.core().app_type(), crate::core::AppType::Window)
                    {
                        let explicit = self.surface_views.get(&id).and_then(|s| s.2(&self.app).blur);
                        let enabled = crate::popup_policy::resolve_blur(
                            self.blur_enabled,
                            self.app.core().blur(&theme, Some(SurfaceIdWrapper::Window(id))),
                            explicit,
                        );
                        commands.push(Self::studio_surface_blur(SurfaceIdWrapper::Window(id), enabled));
                    }
                    return Task::batch(commands);''')
    app = once(app, '''    pub fn theme(&self) -> Theme {
        crate::theme::active()
    }''', '''    pub fn theme(&self) -> Theme {
        let theme = crate::theme::active();
        if crate::window_policy::enabled()
            && matches!(self.app.core().app_type(), crate::core::AppType::Window)
            && self.app.core().main_window_id().is_some()
        {
            return crate::theme::popup_material::for_window(
                theme.clone(),
                self.blur_enabled && self.app.core().frosted(theme.cosmic()),
            );
        }
        theme
    }''')
    # Insert the Window branch after the separate Popup branch so popup opacity
    # and explicit settings are independent from the parent window material.
    app = once(app, '''            return crate::theme::popup_material::for_popup(theme, blur);
        }
        theme
    }''', '''            return crate::theme::popup_material::for_popup(theme, blur);
        }
        #[cfg(all(feature = "wayland", target_os = "linux"))]
        if crate::window_policy::enabled()
            && matches!(self.app.core().app_type(), crate::core::AppType::Window)
        {
            // Only actual XDG Window IDs enter this profile. Desktop layers,
            // input-method roots and unknown IDs keep their native clear style.
            let window_surface = crate::window_policy::is_window_surface(
                self.surface_views.get(&id).map(|s| matches!(s.1, SurfaceIdWrapper::Window(_))),
                self.app.core().main_window_id() == Some(id),
            );
            if !window_surface {
                return theme;
            }
            let explicit = self.surface_views.get(&id).and_then(|s| s.2(&self.app).blur);
            let blur = crate::popup_policy::resolve_blur(
                self.blur_enabled,
                self.app.core().blur(&theme, Some(SurfaceIdWrapper::Window(id))),
                explicit,
            );
            let geometry_allowed = crate::window_policy::automatic(
                true, theme.cosmic().is_high_contrast,
                self.app.core().window.sharp_corners || self.app.core().window.is_maximized,
                theme.cosmic().frosted_maximized_apps,
            );
            return crate::theme::popup_material::for_window(theme, blur && geometry_allowed);
        }
        theme
    }''')
    changed['src/app/cosmic.rs'] = app
    # Send a disable request as well when high contrast or native maximized
    # policy turns an opted-in main window opaque after it was already blurred.
    import re
    app, count = re.subn(r'if (?P<core>core|self\.app\.core\(\))\.blur\(&(?P<theme>theme|cosmic_theme|t), None\) \{',
        lambda m: f'if {m["core"]}.blur(&{m["theme"]}, None) || (crate::window_policy::enabled() && matches!({m["core"]}.app_type(), crate::core::AppType::Window)) {{', app)
    # Four guarded paths and one already unconditional SystemThemeChange path.
    if count != 4:
        raise ValueError(f'Expected four guarded native main-window refresh paths, found {count}.')
    start = app.index('Action::DesktopSettings(crate::theme::portal::Desktop::ColorScheme(s))')
    end = app.index('Action::DesktopSettings(crate::theme::portal::Desktop::Accent(c))', start)
    portal = app[start:end]
    portal = once(portal, 'let mut cosmic_theme = THEME.lock().unwrap();',
        '''let mut cosmic_theme = THEME.lock().unwrap();
                        if crate::window_policy::enabled()
                            && matches!(core.app_type(), crate::core::AppType::Window)
                        {
                            cosmic_theme.transparent = self.blur_enabled && core.frosted(new_theme.cosmic());
                        }''')
    app = app[:start] + portal + app[end:]
    changed['src/app/cosmic.rs'] = app

    material = changed['src/theme/popup_material.rs']
    material = once(material, 'struct CachedMaterial {',
        '''#[derive(Clone, Copy, PartialEq, Eq)]
enum MaterialKind { Popup, Window }

struct CachedMaterial {
    kind: MaterialKind,
    transparent: bool,''')
    material = material.replace('// At most two palettes (normally dark and light).',
        '// At most four palettes (light/dark for popup/window).')
    material = once(material, '''pub(crate) fn for_popup(mut theme: Theme, blur: bool) -> Theme {
    if !crate::popup_policy::enabled() {
        return theme;
    }
    if theme.cosmic().is_high_contrast {''',
        '''pub(crate) fn for_popup(mut theme: Theme, blur: bool) -> Theme {
    if !crate::popup_policy::enabled() {
        if crate::window_policy::enabled() {
            theme.transparent = false;
        }
        return theme;
    }
    for_material(theme, blur, MaterialKind::Popup)
}

pub(crate) fn for_window(theme: Theme, blur: bool) -> Theme {
    if !crate::window_policy::enabled() {
        return theme;
    }
    for_material(theme, blur, MaterialKind::Window)
}

fn for_material(mut theme: Theme, blur: bool, kind: MaterialKind) -> Theme {
    if theme.cosmic().is_high_contrast {''')
    material = once(material, '''    if theme.cosmic().is_high_contrast {
        // Accessibility palettes use their original opaque containers. Do not
        // tint, recolor or cache a translucent derivative of that palette.
        theme.transparent = false;
        return theme;
    }
    theme.transparent = blur;
    if !blur {
        return theme;
    }''', '''    let blur = blur && !theme.cosmic().is_high_contrast;
    theme.transparent = blur;
    if !blur && kind == MaterialKind::Popup {
        return theme;
    }
    // An actual Window's opaque fallback owns an exact palette clone. Its Arc
    // marks the clear style without mistaking an original desktop/layer theme.
    // The bounded cache avoids cloning during ordinary redraws.''')
    material = once(material, '/// Called only for tracked XDG Popup surfaces by Cosmic::theme(id).',
        '''pub(crate) fn is_window_theme(theme: &Theme) -> bool {
    let key = theme.cosmic() as *const CosmicTheme as usize;
    CACHE.lock().unwrap_or_else(|e| e.into_inner()).iter().any(|entry| {
        entry.kind == MaterialKind::Window && Arc::as_ptr(&entry.material) as usize == key
    })
}

/// Called only for tracked XDG Popup surfaces by Cosmic::theme(id).''')
    material = once(material, 'cache.iter().find(|entry| entry.source_key == source_key)',
        'cache.iter().find(|entry| entry.source_key == source_key && entry.kind == kind && entry.transparent == blur)')
    material = once(material, 'let material = Arc::new(theme.cosmic().with_popup_material(TINT_ALPHA));',
        '''let material = Arc::new(if !blur {
            theme.cosmic().clone()
        } else { match kind {
            MaterialKind::Popup => theme.cosmic().with_popup_material(TINT_ALPHA),
            MaterialKind::Window => theme.cosmic().with_window_material(),
        }});''')
    material = once(material, 'if cache.len() == 2 {', 'if cache.len() == 4 {')
    material = once(material, 'cache.push(CachedMaterial {\n            source_key,',
        'cache.push(CachedMaterial {\n            kind,\n            transparent: blur,\n            source_key,')
    changed['src/theme/popup_material.rs'] = material

    changed['cosmic-theme/src/model/theme.rs'] = once(
        changed['cosmic-theme/src/model/theme.rs'], 'impl Theme {',
        'impl Theme {\n' + (HERE / 'window_method.rs').read_text())
    return changed
