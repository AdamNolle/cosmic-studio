#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Connect actual client callbacks to the inert overflow wrapper outside Smithay locks."""
import argparse
import difflib
import importlib.util
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
PIN = 'b5cc19e351b82eed999097ced1ff267d27bf8e7a'
KEYBOARD = 'cosmic-panel-bin/src/xdg_shell_wrapper/client/handlers/keyboard.rs'
WRAPPER = 'cosmic-panel-bin/src/iced/mod.rs'
MODULE = 'cosmic-panel-bin/src/iced/client_overflow_route.rs'


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prerequisite():
    return load('prepare_overflow_preflight')


def expected_inputs():
    prior = prerequisite()
    return prior.transform(prior.expected_inputs())


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Changed exact synchronous callback route seam.')
    return text.replace(old, new, 1)


def transform(files):
    if files != expected_inputs():
        raise ValueError('Changed exact preflight/delivery/isolation inputs; fresh tree required.')
    changed = dict(files)
    changed[WRAPPER] = once(files[WRAPPER], 'mod iced_keyboard_route;',
                           'mod iced_keyboard_route;\npub(crate) mod client_overflow_route;')
    text = files[KEYBOARD]
    # Original server input/filter expressions remain exact. Only after they
    # return may the new caller query keyboard state and lock the wrapper.
    text = once(text, '''        );
    }

    fn repeat_key(''', '''        );
        self.route_overflow_keyboard(keyboard);
    }

    fn repeat_key(''')
    text = once(text, '''        }
    }

    fn release_key(''', '''        }
        self.route_overflow_keyboard(_keyboard);
    }

    fn release_key(''')
    text = once(text, '''        );
    }

    fn update_repeat_info(''', '''        );
        self.route_overflow_keyboard(keyboard);
    }

    fn update_repeat_info(''')
    changed[KEYBOARD] = text
    changed[MODULE] = (HERE / 'client_overflow_route.rs').read_text(encoding='utf-8')
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
    originals[prior.SOURCE] = prior.original()
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
