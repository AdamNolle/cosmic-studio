#!/usr/bin/env python3
"""Copy the native popup specimen into isolated work; no build or UI launch."""
import argparse
import gzip
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import tomllib

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('popup_prepare', HERE.parent / 'prepare.py')
popup_prepare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(popup_prepare)
REVISION = '08a09e3dfa1f729d52585fcedd6e731130235363'


def prepare(output, sdk, lockfile):
    output, sdk, lockfile = output.resolve(), sdk.resolve(), lockfile.resolve()
    popup_prepare.require_isolated(output)
    popup_prepare.require_isolated(sdk)
    if output.exists():
        raise ValueError('Use a new isolated specimen directory.')
    # Compare exact generated material source with the reviewed pinned SDK,
    # while embedded fonts and semantic heading work stay separate.
    files = json.loads(gzip.decompress((HERE.parent / 'tests/pinned-inputs.json.gz').read_bytes()))[REVISION]
    with tempfile.TemporaryDirectory(prefix='studio-popup-specimen-source-') as folder:
        root = Path(folder)
        for name, text in files.items():
            p = root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        _, changed, _ = popup_prepare.changes_for(root, REVISION, window_glass=True)
    for name, text in changed.items():
        if (sdk / name).read_text() != text:
            raise ValueError('SDK differs from reviewed native material source: ' + name)
    package_paths = {}
    for p in sdk.rglob('Cargo.toml'):
        if any(part in {'target', '.git'} for part in p.relative_to(sdk).parts):
            continue
        item = tomllib.loads(p.read_text()).get('package', {})
        if item.get('name') in {'libcosmic', 'cosmic-theme', 'cosmic-config', 'cosmic-config-derive',
                                'build_helpers', 'cosmic-client-toolkit', 'dpi'} or item.get('name', '').startswith('iced'):
            package_paths[item['name']] = p.parent
    if len(package_paths) != 24:
        raise ValueError('Native package inventory differs from the reviewed 24-crate SDK.')
    manifest = '[package]\nname="cosmic-studio-popup-specimen"\nversion="0.1.0"\nedition="2024"\n'
    manifest += '[dependencies]\nlibcosmic={path=' + json.dumps(str(sdk)) + ',default-features=false,features=["wayland","winit","tokio","wgpu"]}\n'
    manifest += 'iced_runtime={path=' + json.dumps(str(sdk / 'iced/runtime')) + ',features=["wayland"]}\n'
    manifest += 'libc="0.2"\n'
    manifest += '[patch."https://github.com/pop-os/libcosmic"]\n'
    manifest += ''.join(name + '={path=' + json.dumps(str(path)) + '}\n' for name, path in sorted(package_paths.items()))
    output.mkdir(parents=True)
    (output / 'src').mkdir()
    (output / 'Cargo.toml').write_text(manifest)
    shutil.copyfile(HERE / 'main.rs', output / 'src/main.rs')
    shutil.copyfile(HERE / 'guard.rs', output / 'src/guard.rs')
    shutil.copyfile(lockfile, output / 'Cargo.lock')
    report = {'sdk': str(sdk), 'revision': REVISION, 'native_package_count': len(package_paths),
              'app_id': 'org.cosmicstudio.PopupSpecimen', 'built': False, 'launched': False,
              'lock_seed': str(lockfile), 'output': str(output)}
    (output / 'source-review.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('output', type=Path)
    p.add_argument('--sdk', type=Path, required=True)
    p.add_argument('--lockfile', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(prepare(a.output, a.sdk, a.lockfile), indent=2))
