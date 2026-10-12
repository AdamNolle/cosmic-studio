#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Refuse invalid native overflow opening targets before existing popup effects."""
import argparse
import difflib
import gzip
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
PIN = 'b5cc19e351b82eed999097ced1ff267d27bf8e7a'
SOURCE = 'cosmic-panel-bin/src/space/overflow.rs'
FIXTURE_SHA = 'c91d3b972279a17120f4f541f81aacb2e8ebab47fdea0d605e7a2e23955120d2'
SOURCE_SHA = '46729d2b07e57002deb80dab2040e694b3027e97d31817fcf7d8f7f1f09278c1'


def original():
    data = (HERE / 'pinned-overflow-preflight.json.gz').read_bytes()
    if hashlib.sha256(data).hexdigest() != FIXTURE_SHA:
        raise ValueError('Changed licensed overflow fixture.')
    files = json.loads(gzip.decompress(data))
    if set(files) != {SOURCE} or hashlib.sha256(files[SOURCE].encode()).hexdigest() != SOURCE_SHA:
        raise ValueError('Changed original overflow source.')
    return files[SOURCE]


def prerequisite():
    spec = importlib.util.spec_from_file_location('preflight_prior', HERE / 'prepare_client_keyboard_delivery.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expected_inputs():
    prior = prerequisite()
    return {**prior.transform(prior.expected_inputs()), SOURCE: original()}


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Changed exact overflow opening seam.')
    return text.replace(old, new, 1)


def transform(files):
    if files != expected_inputs():
        raise ValueError('Changed exact delivery/original overflow inputs; fresh tree required.')
    changed = dict(files)
    text = files[SOURCE]
    text = once(text, '''        let has_popup = self.overflow_popup.is_some();
        self.close_popups(|_| false);

        if force_hide || has_popup {
''', '''        let has_popup = self.overflow_popup.is_some();

        // Recovery/dismissal does not require a still-mapped opening anchor.
        if force_hide || has_popup {
            self.close_popups(|_| false);
''')
    block = '''        let (Some((element, section)), Some(popup_element)) =
            self.overflow_elements_for_id(&element_id)
        else {
            bail!("No element found with id: {:?}", element_id);
        };
'''
    text = once(text, block, '')
    text = once(text, '''        if let Some(cosmic_workspaces) = &self.shared.cosmic_workspaces {
''', '''        // Opening preflight is read-only. Refusal must not dismiss unrelated
        // popups, hide Workspaces or allocate a protocol surface. These checks
        // are NOT keyboard admission, serial validity or popup-grab authority.
''' + block + '''        let Some(loc) = self.space.element_location(&element) else {
            bail!("Overflow anchor is not mapped");
        };
        let Some(parent) = self.layer.as_ref().map(|layer| layer.wl_surface().clone())
            .filter(|parent| parent.is_alive())
        else {
            bail!("Overflow parent layer is unavailable");
        };
        let bbox = element.geometry();
        let popup_bbox = popup_element.geometry();

        // No callback/yield occurs between this snapshot and existing effects.
        // close_popups does not replace the layer or unmap the anchor. Later
        // protocol/allocation failures are still NOT transactional rollback.
        self.close_popups(|_| false);
        if let Some(cosmic_workspaces) = &self.shared.cosmic_workspaces {
''')
    text = once(text, '        let loc = self.space.element_location(&element).unwrap_or_default();\n        let bbox = element.geometry();\n', '')
    text = once(text, '        let popup_bbox = popup_element.geometry();\n\n        positioner.set_anchor_rect', '\n        positioner.set_anchor_rect')
    text = once(text, '                parent: self.layer.as_ref().unwrap().wl_surface().clone(),', '                parent,')
    changed[SOURCE] = text
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
    expected = expected_inputs()
    for name, text in expected.items():
        path = source / name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.resolve().is_relative_to(source):
            raise ValueError('Symlink/escaped overflow input forbidden.')
        if path.read_bytes() != text.encode():
            raise ValueError('Changed exact preflight input; preserve tree.')
    if subprocess.check_output(['git', '-C', str(source), 'show', 'HEAD:' + SOURCE]) != original().encode():
        raise ValueError('Original overflow Git blob differs.')
    changed = transform(expected)
    patch = ''.join(difflib.unified_diff(expected[SOURCE].splitlines(True), changed[SOURCE].splitlines(True),
                                       fromfile='a/' + SOURCE, tofile='b/' + SOURCE))
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(patch)
    subprocess.run(['git', '-C', str(source), 'apply', '--check', str(output.resolve())], check=True)
    if apply:
        subprocess.run(['git', '-C', str(source), 'apply', str(output.resolve())], check=True)
        if any((source / name).read_bytes() != text.encode() for name, text in changed.items()):
            raise ValueError('Overflow preflight postimage mismatch.')
    return changed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    prepare(args.source, args.output, args.apply)
