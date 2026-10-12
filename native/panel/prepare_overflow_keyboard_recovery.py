#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Guard actual owned-leaf Escape recovery and native popup teardown outside locks."""
import argparse
import gzip
import hashlib
import json
import difflib
import importlib.util
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
PIN = 'b5cc19e351b82eed999097ced1ff267d27bf8e7a'
KEYBOARD = 'cosmic-panel-bin/src/xdg_shell_wrapper/client/handlers/keyboard.rs'
WRAPPER = 'cosmic-panel-bin/src/iced/mod.rs'
ROUTE = 'cosmic-panel-bin/src/iced/client_overflow_route.rs'
MODULE = 'cosmic-panel-bin/src/iced/overflow_keyboard_recovery.rs'
LEDGER = 'cosmic-panel-bin/src/xdg_shell_wrapper/client/keyboard_input_state.rs'
PANEL = 'cosmic-panel-bin/src/space/panel_space.rs'
POPUP = 'cosmic-panel-bin/src/space/popup.rs'
OVERFLOW = 'cosmic-panel-bin/src/space/overflow.rs'
CONTAINER = 'cosmic-panel-bin/src/space_container/wrapper_space.rs'
FIXTURE_SHA = 'f2dad6959fe1c52f718d9445971fbcedd98dc27d827f7a09a8f49fa2b6e5683e'


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prerequisite():
    return load('prepare_client_overflow_route')


def expected_inputs():
    prior = prerequisite()
    files = prior.transform(prior.expected_inputs())
    files.update(fixture_originals())
    return files


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Changed exact native keyboard recovery seam.')
    return text.replace(old, new, 1)


def fixture_originals():
    data = (HERE / 'pinned-overflow-recovery.json.gz').read_bytes()
    if hashlib.sha256(data).hexdigest() != FIXTURE_SHA:
        raise ValueError('Changed licensed original recovery fixture.')
    return json.loads(gzip.decompress(data).decode('utf-8'))


def transform(files):
    if files != expected_inputs():
        raise ValueError('Changed exact inert route/recovery inputs; fresh tree required.')
    changed = dict(files)
    changed[WRAPPER] = once(files[WRAPPER], 'pub(crate) mod client_overflow_route;',
        'pub(crate) mod client_overflow_route;\npub(crate) mod overflow_keyboard_recovery;')
    changed[ROUTE] = once(files[ROUTE],
        'pub(crate) fn route_overflow_keyboard(&self, keyboard: &WlKeyboard) {',
        'pub(crate) fn route_overflow_keyboard(&mut self, keyboard: &WlKeyboard) {\n'
        '        if self.dismiss_overflow_keyboard(keyboard) { return; }')
    text = files[LEDGER]
    text = once(text, 'collections::BTreeMap', 'collections::{BTreeMap, BTreeSet}')
    text = once(text, '    held: BTreeMap<u32, Option<ClientPress<O>>>,',
        '    held: BTreeMap<u32, Option<ClientPress<O>>>,\n'
        '    // One native action attempt per actual press lifetime; not a grab.\n'
        '    consumed: BTreeSet<u32>,')
    text = once(text, 'Self { origin, focus: None, held: BTreeMap::new() }',
        'Self { origin, focus: None, held: BTreeMap::new(), consumed: BTreeSet::new() }')
    text = once(text, '        self.held = raw.iter().map(|&key| (key, None)).collect();',
        '        self.held = raw.iter().map(|&key| (key, None)).collect();\n        self.consumed.clear();')
    text = once(text, '        self.held.clear();', '        self.held.clear();\n        self.consumed.clear();')
    text = once(text, '        self.held.remove(&raw_code).is_some()',
        '        let _ = self.consumed.remove(&raw_code);\n        self.held.remove(&raw_code).is_some()')
    text = once(text, '    // Necessary provenance/lifetime check only; NOT popup-grab authorization.',
        '    // Call only AFTER operation-specific live/frame/target validation.\n'
        '    // Consumption neither retires the held press nor authorizes a grab.\n'
        '    pub(crate) fn consume(&mut self, press: &ClientPress<O>) -> bool {\n'
        '        self.is_current(press) && self.consumed.insert(press.raw_code)\n'
        '    }\n\n'
        '    // Necessary provenance/lifetime check only; NOT popup-grab authorization.')
    changed[LEDGER] = text
    text = files[PANEL]
    text = once(text, '    pub overflow_popup: Option<(PanelPopup, OverflowSection)>,',
        '    pub overflow_popup: Option<(PanelPopup, OverflowSection)>,\n'
        '    // Exact ephemeral popup/creating client seat, never persistent identity.\n'
        '    pub(crate) overflow_keyboard_owner: Option<(\n'
        '        sctk::reexports::client::protocol::wl_surface::WlSurface,\n'
        '        sctk::reexports::client::protocol::wl_seat::WlSeat)>,')
    text = once(text, '            overflow_popup: None,',
        '            overflow_popup: None,\n            overflow_keyboard_owner: None,')
    text = once(text, '        self.overflow_popup = None;',
        '        self.overflow_popup = None;\n        self.overflow_keyboard_owner = None;')
    changed[PANEL] = text
    text = files[OVERFLOW]
    text = once(text, '            self.overflow_popup = None;',
        '            self.overflow_popup = None;\n            self.overflow_keyboard_owner = None;')
    text = once(text, '        Ok(())\n    }\n\n    fn overflow_elements_for_id(',
        '        self.overflow_keyboard_owner = Some((c_wl_surface, seat.1));\n'
        '        Ok(())\n    }\n\n    fn overflow_elements_for_id(')
    changed[OVERFLOW] = text
    begin = files[POPUP].index('    pub(crate) fn close_popups(')
    end = files[POPUP].index('\n    pub fn configure_panel_popup(', begin)
    changed[POPUP] = once(files[POPUP], files[POPUP][begin:end], '''    pub(crate) fn close_popups(&mut self, exclude: impl Fn(&PanelPopup) -> bool) {
        let edges = self.popups.iter().map(|child|
            (child.popup.parent.clone(), child.popup.c_popup.wl_surface().clone()))
            .collect::<Vec<_>>();
        // MOVE the whole native owner; raw proxies do not retain SCTK PopupInner.
        let mut to_destroy = Vec::with_capacity(self.popups.len());
        let mut retained = Vec::with_capacity(self.popups.len());
        for p in self.popups.drain(..) {
            if exclude(&p.popup) { retained.push(p); }
            else {
                tracing::info!("Closing popup: {:?}", p.popup.c_popup.wl_surface());
                to_destroy.push((p.popup, Some(p.s_surface)));
            }
        }
        self.popups = retained;
        if self.overflow_popup.as_ref().is_some_and(|(p, _)| !exclude(p)) {
            let (popup, _) = self.overflow_popup.take().unwrap();
            self.overflow_keyboard_owner = None;
            tracing::info!("Closing overflow popup: {:?}", popup.c_popup.wl_surface());
            to_destroy.push((popup, None));
        }
        let batch = to_destroy.into_iter().map(|(popup, embedded)|
            (popup.c_popup.wl_surface().clone(), (popup, embedded))).collect();
        crate::iced::overflow_keyboard_recovery::ordered_teardown(batch, edges, |(popup, s_popup)| {
            let surface = popup.c_popup.wl_surface().clone();
            self.shared.c_focused_surface.borrow_mut().retain(|s| s.0 != surface);
            self.shared.c_hovered_surface.borrow_mut().retain(|s| s.0 != surface);
            if let Some(s_popup) = s_popup {
                s_popup.send_popup_done();
                let s_surface = s_popup.wl_surface().clone();
                self.s_focused_surface
                    .retain(|s| !s.0.wl_surface().is_some_and(|s| s.as_ref() == &s_surface));
                self.s_hovered_surface
                    .retain(|s| !s.surface.wl_surface().is_some_and(|s| s.as_ref() == &s_surface));
            }
            // Original PanelPopup/SCTK RAII: EGL first, role then xdg/wl surface.
            // Do not manually destroy raw proxies and later destroy them again.
            drop(popup);
        });
    }
''')
    # Actual done routing must include native overflow, not just proxied popups.
    changed[CONTAINER] = once(files[CONTAINER],
        '.find(|s| s.popups.iter().any(|p| p.popup.c_popup.wl_surface() == popup.wl_surface()))',
        '.find(|s| s.popups.iter().any(|p| p.popup.c_popup.wl_surface() == popup.wl_surface())\n'
        '                || s.overflow_popup.as_ref().is_some_and(|(p, _)| p.c_popup.wl_surface() == popup.wl_surface()))')
    # close_popups takes an EXCLUSION predicate. Close the requested object,
    # not every unrelated object while retaining the done popup itself.
    source = 'cosmic-panel-bin/src/space/wrapper_space.rs'
    changed[source] = once(files[source],
        '        self.close_popups(|p| p.c_popup.wl_surface() == popup.wl_surface());',
        '        // Close the requested popup AND its recorded descendants.\n'
        '        // Never depend on remote done ordering or destroy unrelated roots.\n'
        '        let closing = crate::iced::overflow_keyboard_recovery::descendant_surfaces(\n'
        '            popup.wl_surface().clone(), self.popups.iter().map(|child|\n'
        '                (child.popup.parent.clone(), child.popup.c_popup.wl_surface().clone())));\n'
        '        self.close_popups(|p| !closing.contains(p.c_popup.wl_surface()));\n'
        '        self.is_dirty = true;\n        self.needs_layout = true;')
    changed[MODULE] = (HERE / 'overflow_keyboard_recovery.rs').read_text(encoding='utf-8')
    return changed


def prepare(source, output, apply=False):
    source, output = Path(source), Path(output)
    if source.is_symlink() or any(p.is_symlink() for p in source.parents):
        raise ValueError('Symlink source forbidden.')
    source = source.resolve()
    if any(p in ('usr', 'opt', '.cargo', '.cache') for p in source.parts):
        raise ValueError('Use isolated sources, not installed files/caches.')
    if subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip() != PIN:
        raise ValueError('Exact original panel HEAD required.')
    originals = {**load('prepare_keyboard_focus').originals(), **load('prepare_keyboard_input').originals()}
    prior = prerequisite()
    overflow = load('prepare_overflow_preflight')
    originals[overflow.SOURCE] = overflow.original()
    originals.update(fixture_originals())
    expected = expected_inputs()
    for name, text in expected.items():
        path = source / name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.resolve().is_relative_to(source):
            raise ValueError('Symlink/escaped callback route input forbidden.')
        if path.read_bytes() != text.encode():
            raise ValueError('Changed exact callback route input; preserve tree.')
        if name in originals and subprocess.check_output(['git', '-C', str(source), 'show', 'HEAD:' + name]) != originals[name].encode():
            raise ValueError('Original callback route Git blob differs.')
    path = source / MODULE
    if path.exists() or path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError('Existing/symlink route module refused; fresh tree required.')
    changed = transform(expected)
    patch = ''.join(''.join(difflib.unified_diff(expected.get(name, '').splitlines(True), text.splitlines(True),
        fromfile='a/' + name if name in expected else '/dev/null', tofile='b/' + name))
        for name, text in changed.items())
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(patch)
    subprocess.run(['git', '-C', str(source), 'apply', '--check', str(output.resolve())], check=True)
    if apply:
        subprocess.run(['git', '-C', str(source), 'apply', str(output.resolve())], check=True)
        if any((source / name).read_bytes() != text.encode() for name, text in changed.items()):
            raise ValueError('Callback route postimage mismatch.')
    return changed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    prepare(args.source, args.output, args.apply)
