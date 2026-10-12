#!/usr/bin/env python3
"""Exact-source grouped brightness batching; no dependencies or permission changes.

Apply only after the original managed-popup route in a fresh isolated app tree.
The original watch channel still coalesces DISTINCT actions; this is not a FIFO.
"""
import argparse
import difflib
import hashlib
from pathlib import Path
import subprocess

PIN = '3e6486ff11dba8cdb729420c27b4ce2c519f8443'
ORIGINAL = {'src/app.rs': 'a88bdb088798ba15030681948c1ec2c6b1dc085a737a062b9ef54ac93f4ac30b',
            'src/monitor.rs': '4481cb35c980d769b9d32ed351d49366cefad879d5d92b30ef0d9f28c5250988',
            'src/main.rs': '1a128075ef9bb1230a192746ef2a4ce220fefe921c762efbb99c293b257b3c1f'}
ROUTED_APP = '0ee178476b4dd9d738339801927ffc4baab21a5222d0858ec433ab220b8a2e37'
COMMANDS = Path(__file__).with_name('brightness_commands.rs')


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError('Unrecognized exact brightness batch seam.')
    return text.replace(before, after, 1)


def transform(files):
    expected = dict(ORIGINAL, **{'src/app.rs': ROUTED_APP})
    if set(files) != set(expected) or any(hashlib.sha256(files[name].encode()).hexdigest() != digest
                                        for name, digest in expected.items()):
        raise ValueError('Changed brightness input; preserve it and prepare a fresh exact source.')
    app = replace_once(files['src/app.rs'], 'vec.push(EventToSub::Set(id.clone(), b));',
                       'vec.push((id.clone(), b));')
    app = replace_once(app, '''                for e in vec {
                    self.send(e);
                }''', '''                // One watch-channel value preserves every monitor in this action.
                // An empty original group sent nothing; do not displace a refresh.
                if !vec.is_empty() {
                    self.send(EventToSub::SetBatch(vec));
                }''')
    monitor = replace_once(files['src/monitor.rs'], '''pub type DisplayId = String;
pub type ScreenBrightness = u16;''',
                           'pub use crate::commands::{DisplayId, EventToSub, ScreenBrightness};')
    monitor = replace_once(monitor, '''#[derive(Debug, Clone)]
pub enum EventToSub {
    Refresh,
    Set(DisplayId, ScreenBrightness),
}

''', '')
    start = monitor.index('                            EventToSub::Set(id, value) => {\n')
    end_marker = '                                tokio::time::sleep(Duration::from_millis(50)).await;\n                            }'
    end = monitor.index(end_marker, start) + len(end_marker)
    old = monitor[start:end]
    lines = old.splitlines(True)
    body = ''.join('    '+line if line.strip() else line for line in lines[1:-1])
    # The last split line is the original arm close; keep all original DDC operations.
    new = ('                            command => {\n'
           '                                for (id, value) in command.into_writes().expect("write command") {\n'
           + body + '                                }\n                            }')
    monitor = replace_once(monitor, old, new)
    main = replace_once(files['src/main.rs'], 'mod monitor;', 'mod commands;\nmod monitor;')
    return {'src/app.rs': app, 'src/monitor.rs': monitor, 'src/main.rs': main,
            'src/commands.rs': COMMANDS.read_text(encoding='utf-8')}


def prepare(source, output, apply=False):
    if source.is_symlink():
        raise ValueError('Symlink source forbidden.')
    source = source.resolve()
    if any(source.is_relative_to(p) for p in (Path('/usr'), Path.home()/'.cargo', Path.home()/'.local', Path.home()/'.var')):
        raise ValueError('Only an isolated source is allowed.')
    if subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip() != PIN:
        raise ValueError('Original Brightness HEAD required.')
    files = {}
    for name, digest in ORIGINAL.items():
        path = source/name
        if path.is_symlink() or not path.resolve().is_relative_to(source):
            raise ValueError('Symlink/escaped batch source forbidden.')
        original = subprocess.check_output(['git', '-C', str(source), 'show', 'HEAD:'+name])
        if hashlib.sha256(original).hexdigest() != digest:
            raise ValueError('Original brightness Git blob differs.')
        files[name] = path.read_text(encoding='utf-8')
    added = source/'src/commands.rs'
    if added.exists() or added.is_symlink():
        raise ValueError('Existing command source forbidden; prepare a fresh tree.')
    after = transform(files)
    patch = ''.join(''.join(difflib.unified_diff(files.get(name, '').splitlines(True), text.splitlines(True),
                          fromfile='a/'+name if name in files else '/dev/null', tofile='b/'+name))
                    for name, text in after.items())
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(patch)
    # Disable autocrlf only for this exact patch command, never host policy/checksums.
    command = ['git', '-C', str(source), '-c', 'core.autocrlf=false', 'apply']
    subprocess.run(command+['--check', str(output.resolve())], check=True)
    if apply:
        subprocess.run(command+[str(output.resolve())], check=True)
        for name, text in after.items():
            if (source/name).read_bytes() != text.encode():
                raise ValueError('Brightness batch postimage mismatch.')
    return after


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    prepare(args.source, args.output, args.apply)
    print('Prepared exact grouped brightness batch; no FIFO/hardware/runtime certification.')
