#!/usr/bin/env python3
"""Produce a reviewed native display-font patch; never edit Cargo caches.

Point at an isolated, pinned libcosmic source checkout. Apply the emitted patch
there before compiling clients. Existing installed binaries stay untouched.
"""
import argparse
import difflib
from pathlib import Path
import re

HELPER = '''
/// COSMIC Studio display face. A static font key uses the renderer's existing
/// shaped-text cache; ordinary UI, captions, code and symbols keep their roles.
#[inline]
pub fn display() -> Font {
    Font::with_name("Instrument Serif")
}
'''

def transform_text(text):
    for name in ['title1','title2','title3','title4','heading']:
        pattern=re.compile(r'(pub fn '+name+r"<'a>.*?\n}\n)",re.S)
        matches=list(pattern.finditer(text))
        if len(matches)!=1: raise ValueError('Unrecognized native text helper: '+name)
        before=matches[0].group(0)
        after,count=re.subn(r'\.font\(crate::font::(?:bold|semibold)\(\)\)',
                            '.font(crate::font::display())',before)
        if count!=1: raise ValueError('Unrecognized native font assignment: '+name)
        text=text[:matches[0].start()]+after+text[matches[0].end():]
    return text

def changes_for(source):
    files={}
    font=source/'src/font.rs'
    original=font.read_text()
    if 'pub fn display()' in original: raise ValueError('Native display helper is already present.')
    if 'pub use iced::Font;' not in original: raise ValueError('Unrecognized native Font export.')
    core=(source/'iced/core/src/font.rs').read_text()
    if 'pub const fn with_name' not in core: raise ValueError('Pinned iced Font::with_name support is required.')
    files['src/font.rs']=(original,original.rstrip()+'\n'+HELPER)
    text=source/'src/widget/text.rs'
    original=text.read_text()
    files['src/widget/text.rs']=(original,transform_text(original))
    return files

def patch_for(source):
    return ''.join(''.join(difflib.unified_diff(before.splitlines(keepends=True),
                                               after.splitlines(keepends=True),
                                               fromfile='a/'+name,tofile='b/'+name))
                   for name,(before,after) in changes_for(source).items())

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    output=patch_for(args.source.resolve())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(output)
    print('Prepared native display-font patch: '+str(args.output))

if __name__=='__main__': main()
