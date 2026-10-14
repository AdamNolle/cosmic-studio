#!/usr/bin/env python3
"""Add Studio controls to an isolated, already-prepared libcosmic checkout."""
from pathlib import Path
import argparse, shutil, hashlib, json, subprocess, tempfile, os

ROOT=Path(__file__).resolve().parents[2]
ROLES=['minimize','maximize','restore','close']
SHAPES=['solo','left','middle','right']

def replace_once(text,old,new):
    if text.count(old)!=1:
        raise RuntimeError('Native source does not match expected control implementation: '+old[:90])
    return text.replace(old,new,1)

SUPPORTED = {
 '08a09e3dfa1f729d52585fcedd6e731130235363', 'd77e99fb1555e2728297677de61e23ada4d9d09b',
 'd922ac380134c00208d2acf93947d44fb217eec5', '23f5d63fed2a370f3c2f54b90ec8f0896fe82105',
 '03c8f93b294ad239ea935f6dd3c14a15acde8d0d', '9cc82abd9ca5601bb0341edd12a9acbc97e77801',
 'eaa7a5a24c4359ebeaab507855388942e8984d5d',
}

def apply(library, revision=None):
    revision = revision or subprocess.check_output(['git','rev-parse','HEAD'],cwd=library,text=True).strip()
    if revision not in SUPPORTED:
        raise RuntimeError('Unsupported libcosmic revision: '+revision)
    assets = library/'src/widget/window_controls_assets'
    if assets.exists():
        raise RuntimeError('Window controls already prepared; use a fresh source copy')
    widget=library/'src/widget/button/widget.rs'
    header=library/'src/widget/header_bar.rs'
    before={str(p.relative_to(library)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [widget,header]}
    text=widget.read_text()
    text=replace_once(text,'    force_enabled: bool,','    force_enabled: bool,\n    studio_control: Option<([svg::Handle; 4], bool)>,')
    assert text.count('            force_enabled: false,')==2
    text=text.replace('            force_enabled: false,','            force_enabled: false,\n            studio_control: None,')
    marker='    /// Sets the [`Id`] of the [`Button`].'
    method='''    /// Paint exact vector titlebar artwork through the existing button event path.
    pub fn studio_window_control(mut self, handles: [svg::Handle; 4], focused: bool) -> Self {
        self.studio_control = Some((handles, focused));
        self
    }

'''
    text=replace_once(text,marker,method+marker)
    marker='        let mut styling = if !is_enabled {'
    painting='''        if let Some((handles, window_focused)) = self.studio_control.as_ref()
            .filter(|_| !theme.cosmic().is_high_contrast) {
            use iced_core::svg::Renderer as _;
            let index = if !is_enabled { 3 }
                else if is_mouse_over && state.is_pressed { 2 }
                else if is_mouse_over { 1 }
                else if !window_focused { 3 }
                else { 0 };
            renderer.draw_svg(svg::Svg::new(handles[index].clone()), bounds, *viewport);
            if state.is_focused {
                // Ring the visible 14 px rocker segment, not the taller pointer target.
                let segment = Rectangle {
                    y: bounds.y + (bounds.height - 14.0) / 2.0,
                    height: 14.0,
                    ..bounds
                };
                renderer.fill_quad(Quad {
                    bounds: segment,
                    border: Border {
                        color: theme.cosmic().accent_color().into(),
                        width: 1.0,
                        radius: 4.0.into(),
                    },
                    ..Default::default()
                }, Color::TRANSPARENT);
            }
            return;
        }

'''
    text=replace_once(text,marker,painting+marker)
    widget_text = text
    text=header.read_text()
    start=text.index('        macro_rules! icon {',text.index('    fn window_controls('))
    end=text.index('            .spacing(spacing)\n            .align_y(iced::Alignment::Center)\n            .into()\n    }',start)
    rows=[]
    for name in ROLES:
        for shape in SHAPES:
            rows.append('            ['+', '.join(f'include_bytes!("window_controls_assets/{state}/{name}-{shape}.svg").as_slice()' for state in ['normal','hover','pressed','inactive'])+'],')
    replacement='''        // One rocker: each segment's corners follow its position among the visible controls.
        const ART: [[&[u8]; 4]; 16] = [
'''+ '\n'.join(rows)+'''
        ];
        static HANDLES: std::sync::OnceLock<Vec<[iced_core::svg::Handle; 4]>> = std::sync::OnceLock::new();
        let handles = HANDLES.get_or_init(|| ART.iter().map(|states|
            states.map(iced_core::svg::Handle::from_memory)).collect());
        let present = [self.on_minimize.is_some(), self.on_maximize.is_some(), self.on_close.is_some()];
        let count = present.iter().filter(|shown| **shown).count();
        let mut shapes = [0usize; 3];
        let mut position = 0;
        for (slot, shown) in present.iter().enumerate() {
            if *shown {
                // 0 solo, 1 left, 2 middle, 3 right
                shapes[slot] = if count == 1 { 0 } else if position == 0 { 1 }
                    else if position + 1 == count { 3 } else { 2 };
                position += 1;
            }
        }
        macro_rules! icon {
            ($name:expr, $size:expr, $on_press:expr, $shape:expr) => {{
                let role = match $name {
                    "window-minimize-symbolic" => 0,
                    "window-maximize-symbolic" => 1,
                    "window-restore-symbolic" => 2,
                    "window-close-symbolic" => 3,
                    _ => unreachable!(),
                };
                widget::button::custom(
                    widget::icon::from_name($name).size($size).prefer_svg(true).icon()
                )
                    .width(22).height(24).padding(0)
                    .class(theme::Button::HeaderBar)
                    .selected(self.focused)
                    .studio_window_control(handles[role * 4 + $shape].clone(), self.focused)
                    .on_press($on_press)
            }};
        }

        widget::row::with_capacity(3)
            .push_maybe(
                self.on_minimize
                    .take()
                    .map(|m| icon!("window-minimize-symbolic", 16, m, shapes[0])),
            )
            .push_maybe(self.on_maximize.take().map(|m| {
                if self.maximized {
                    icon!("window-restore-symbolic", 16, m, shapes[1])
                } else {
                    icon!("window-maximize-symbolic", 16, m, shapes[1])
                }
            }))
            .push_maybe(
                self.on_close
                    .take()
                    .map(|m| icon!("window-close-symbolic", 16, m, shapes[2])),
            )
'''
    text=text[:start]+replacement+text[end:]
    # Segments join edge to edge; keep layout changes confined to the window-control group.
    start=text.index('    fn window_controls(')
    text=text[:start]+text[start:].replace('.spacing(spacing)','.spacing(0)',1)
    text=text.replace('fn window_controls(&mut self, spacing: u16)','fn window_controls(&mut self, _spacing: u16)',1)
    # Validate both source transformations and stage assets before any source write.
    originals = {p:p.read_bytes() for p in [widget,header]}
    with tempfile.TemporaryDirectory(prefix='.studio-controls-',dir=library) as temporary:
        staged = Path(temporary)/'assets'
        shutil.copytree(ROOT/'icons/window-controls/svg',staged)
        try:
            widget.write_text(widget_text)
            header.write_text(text)
            os.replace(staged,assets)
        except BaseException:
            for path,data in originals.items():path.write_bytes(data)
            raise
    return {'library':str(library),'revision':revision,'before':before,'assets':len(ROLES)*len(SHAPES)*4}


def apply_compositor(compositor):
    path = compositor / 'src/shell/element/window.rs'
    text = path.read_text()
    before = '.focused(win.window.is_activated(false))'
    after = '.focused(win.activated.load(Ordering::SeqCst))'
    if after not in text:
        text=replace_once(text,before,after)
    if '.maximized(win.window.is_maximized(false))' not in text:
        text=replace_once(text,after,after+'\n            .maximized(win.window.is_maximized(false))')
    before='''            SpaceElement::set_activate(&self.0, activated);
            self.0.force_redraw();
            self.0.with_program(|p| {
                p.activated.store(activated, Ordering::SeqCst);
                SpaceElement::set_activate(&p.window, activated);
            });'''
    after='''            self.0.with_program(|p| {
                p.activated.store(activated, Ordering::SeqCst);
                SpaceElement::set_activate(&p.window, activated);
            });
            SpaceElement::set_activate(&self.0, activated);
            self.0.force_redraw();'''
    if after not in text:
        text=replace_once(text,before,after)
    path.write_text(text)
    return {'compositor': str(compositor), 'restore_state': True, 'focus_before_view_update': True}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('library',type=Path)
    parser.add_argument('--compositor', action='store_true')
    parser.add_argument('--revision')
    args=parser.parse_args()
    print(json.dumps(apply_compositor(args.library) if args.compositor else apply(args.library,args.revision),indent=2))
