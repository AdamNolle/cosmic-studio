#!/usr/bin/env python3
"""Compact applet tooltips in an isolated, already-prepared libcosmic checkout.

Dock and panel hover names become a small 12 px Archivo Medium label on a
rounded neutral plate instead of 14 px body text. Positioning, delay and the
popup surface path stay native.
"""
from pathlib import Path
import argparse, hashlib, json, subprocess

FILE = 'src/applet/mod.rs'
BEFORE = '''                    layer_container(crate::widget::text(tooltip.clone()))
                        .layer(crate::cosmic_theme::Layer::Background)
                        .padding(4.),'''
AFTER = '''                    // Studio: compact single-line name, never display-sized.
                    crate::widget::container(
                        crate::widget::text(tooltip.clone())
                            .size(12)
                            .font(crate::font::Font {
                                weight: iced::font::Weight::Medium,
                                ..crate::font::default()
                            })
                            .wrapping(iced::widget::text::Wrapping::None),
                    )
                    .padding([4, 8])
                    .class(crate::theme::Container::custom(|theme| {
                        let cosmic = theme.cosmic();
                        let background = cosmic.background(theme.transparent);
                        iced_widget::container::Style {
                            text_color: Some(background.on.into()),
                            background: Some(Color::from(background.base).into()),
                            border: iced::Border {
                                radius: cosmic.corner_radii.radius_s.into(),
                                ..Default::default()
                            },
                            ..Default::default()
                        }
                    })),'''


def apply(library, write=False):
    path = library/FILE
    text = path.read_text()
    if AFTER in text:
        raise RuntimeError('Compact tooltips already prepared; use a fresh source copy.')
    if text.count(BEFORE) != 1:
        raise RuntimeError('Applet tooltip source does not match the reviewed implementation.')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=library, text=True).strip()
    before = hashlib.sha256(text.encode()).hexdigest()
    if write:
        path.write_text(text.replace(BEFORE, AFTER, 1))
    return {'library': str(library), 'revision': revision, 'file': FILE, 'before': before, 'applied': write}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('library', type=Path)
    parser.add_argument('--apply', action='store_true', help='write the change; otherwise only check it applies')
    args = parser.parse_args()
    print(json.dumps(apply(args.library.resolve(), args.apply), indent=2))
