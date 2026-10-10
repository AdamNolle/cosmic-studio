#!/usr/bin/env python3
"""Patch an isolated, exact greeter source checkout with reviewable appearance hooks."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

PACKAGE=Path(__file__).resolve().parents[2]
PIN='bfb2745176e3fd0824e008d3efb2b37bce5ae0db'
LIBRARY_PIN='87ab8179e1bd9880239c340855ae8862034bd0e8'

def replace(text,old,new,count=1):
    if text.count(old)!=count: raise RuntimeError('Pinned greeter source shape changed: '+old[:80])
    return text.replace(old,new)

def changes_for(source):
    originals={name:(source/'src'/name).read_text() for name in ['lib.rs','main.rs','time.rs','greeter.rs','locker.rs']}
    changed=dict(originals)
    changed['lib.rs']=replace(changed['lib.rs'],'pub mod locker;','pub mod locker;\npub mod studio;\npub mod studio_preview;')
    changed['main.rs']=replace(changed['main.rs'],'    // Enable jpeg-xl support for image-rs.',
        '    // Load display/UI faces before any surface or authentication flow starts.\n'
        '    cosmic_greeter::studio::load_fonts();\n\n    // Enable jpeg-xl support for image-rs.')
    changed['main.rs']=replace(changed['main.rs'],'            Some("--version") | Some("-v") => {',
        '            Some("--studio-preview") => {\n'
        '                cosmic_greeter::studio_preview::run()?;\n'
        '                return Ok(());\n'
        '            }\n'
        '            Some("--version") | Some("-v") => {')
    changed['time.rs']=replace(changed['time.rs'],'text(self.format_time(military_time))',
        'text(self.format_time(military_time))\n                        .font(cosmic::font::display())')
    for name in ['greeter.rs','locker.rs']:
        changed[name]=replace(changed[name],'let settings = Settings::default().no_main_window(true);',
            'let settings = Settings::default()\n'
            '        .default_font(cosmic::iced::Font::with_name("Archivo"))\n'
            '        .theme(crate::studio::'+('dark_theme()' if name=='greeter.rs' else 'theme_for(flags.user_data.theme_opt.as_ref())')+')\n'
            '        .no_main_window(true);')
    changed['greeter.rs']=replace(changed['greeter.rs'],'        tasks.push(common_task);',
        '        tasks.push(common_task);\n        tasks.push(cosmic::command::set_theme(crate::studio::dark_theme()));')
    changed['greeter.rs']=replace(changed['greeter.rs'],
        'tasks.push(cosmic::command::set_theme(cosmic::Theme::custom(Arc::new(\n                theme.clone(),\n            ))));',
        'tasks.push(cosmic::command::set_theme(crate::studio::theme_for(Some(theme))));')
    changed['greeter.rs']=replace(changed['greeter.rs'],'return cosmic::command::set_theme(new.clone());',
        'return cosmic::command::set_theme(crate::studio::select_theme(&new));')
    changed['greeter.rs']=replace(changed['greeter.rs'],'    let is_dark = builder.palette.is_dark();',
        '    if !enabled {\n        return Ok(crate::studio::dark_theme().cosmic().clone());\n    }\n'
        '    let is_dark = builder.palette.is_dark();')
    changed['locker.rs']=replace(changed['locker.rs'],'        let mut app = App {',
        '        let appearance = crate::studio::theme_for(flags.user_data.theme_opt.as_ref());\n\n        let mut app = App {')
    changed['locker.rs']=replace(changed['locker.rs'],'(app, Task::batch([task, common_task]))',
        '(app, Task::batch([task, common_task, cosmic::command::set_theme(appearance)]))')
    return {name:(originals[name],changed[name]) for name in originals}

def source_patch(changes,helper,preview):
    patch=''.join(''.join(difflib.unified_diff(a.splitlines(keepends=True),b.splitlines(keepends=True),
                                            fromfile='a/src/'+name,tofile='b/src/'+name)) for name,(a,b) in changes.items())
    patch+=''.join(difflib.unified_diff([],helper.splitlines(keepends=True),fromfile='/dev/null',tofile='b/src/studio.rs'))
    patch+=''.join(difflib.unified_diff([],preview.splitlines(keepends=True),fromfile='/dev/null',tofile='b/src/studio_preview.rs'))
    return patch

def require_isolated(path):
    parts=path.parts
    if path.is_relative_to('/usr') or path.is_relative_to('/opt') or '.cargo' in parts and 'checkouts' in parts:
        raise RuntimeError('Use an isolated source copy; installed files and Cargo checkouts are not editable: '+str(path))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--patch-output',type=Path,required=True)
    args=parser.parse_args()
    source=args.source.resolve();library=args.library.resolve()
    require_isolated(source);require_isolated(library)
    revision=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
    if revision!=PIN: raise RuntimeError('Exact installed greeter source revision is required: '+PIN)
    revision=subprocess.check_output(['git','-C',str(library),'rev-parse','HEAD'],text=True).strip()
    if revision!=LIBRARY_PIN: raise RuntimeError('Pinned greeter native library is required: '+LIBRARY_PIN)
    if (source/'src/studio.rs').exists(): raise RuntimeError('Source is already patched.')
    changes=changes_for(source)
    helper=(PACKAGE/'native/greeter/studio.rs').read_text()
    preview=(PACKAGE/'native/greeter/preview.rs').read_text()
    patch=source_patch(changes,helper,preview)
    font=library/'src/font.rs'
    original=font.read_text()
    if 'pub fn display() -> Font' not in original:
        raise RuntimeError('Apply the native display-font helper patch to the isolated library first.')
    # This isolated library belongs only to the greeter candidate. The greeter
    # account has no access to the desktop user's CosmicTk font configuration.
    ui=replace(original,'Font::from(crate::config::interface_font())','Font::with_name("Archivo")')
    library_patch=args.patch_output.with_name('libcosmic-greeter-ui-font.patch')
    ui_patch=''.join(difflib.unified_diff(original.splitlines(keepends=True),ui.splitlines(keepends=True),
                                       fromfile='a/src/font.rs',tofile='b/src/font.rs'))
    manifest=json.loads((PACKAGE/'fonts/manifest.json').read_text())
    for entries in manifest['families'].values():
        for entry in entries:
            name=Path(entry['file'])
            if name.is_absolute() or '..' in name.parts: raise RuntimeError('Unsafe font asset path.')
            data=(PACKAGE/'fonts'/name).read_bytes()
            if hashlib.sha256(data).hexdigest()!=entry['sha256']: raise RuntimeError('Font checksum mismatch: '+str(name))
    if (source/'fonts').exists(): raise RuntimeError('Isolated source already contains font assets.')
    # Patch all packages of this native library, not only libcosmic, to prevent
    # different iced versions and duplicated types in client code.
    import tomllib
    packages={}
    for cargo in library.rglob('Cargo.toml'):
        if '/target/' in str(cargo) or '/examples/' in str(cargo): continue
        metadata=tomllib.loads(cargo.read_text())
        if 'package' in metadata: packages[metadata['package']['name']]=cargo.parent
    if not {'libcosmic','iced'}<=packages.keys(): raise RuntimeError('Native library submodules are incomplete.')
    text=(source/'Cargo.toml').read_text()
    if 'https://github.com/pop-os/libcosmic' in tomllib.loads(text).get('patch',{}):
        raise RuntimeError('Source already contains a native library override.')
    text+='\n[patch."https://github.com/pop-os/libcosmic"]\n'
    text+=''.join(f'{name} = {{ path = {json.dumps(str(path))} }}\n' for name,path in sorted(packages.items()))
    # Validate every source shape, font checksum and submodule before any write.
    args.patch_output.parent.mkdir(parents=True,exist_ok=True);args.patch_output.write_text(patch)
    library_patch.write_text(ui_patch)
    for name,(_,changed) in changes.items(): (source/'src'/name).write_text(changed)
    (source/'src/studio.rs').write_text(helper)
    (source/'src/studio_preview.rs').write_text(preview)
    font.write_text(ui)
    shutil.copytree(PACKAGE/'fonts',source/'fonts')
    (source/'Cargo.toml').write_text(text)
    print('Prepared isolated greeter '+PIN+' with native library '+str(library))

if __name__=='__main__':
    try: main()
    except Exception as error:
        print('ERROR: '+str(error),file=sys.stderr);sys.exit(1)
