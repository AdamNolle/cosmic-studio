#!/usr/bin/env python3
"""Test real pinned cosmic-theme palette contrast without opening a UI."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Prepared isolated libcosmic with window profile')
    parser.add_argument('--target-dir', type=Path, required=True)
    parser.add_argument('--lockfile', type=Path, required=True, help='Existing locked native application dependency graph')
    parser.add_argument('--legacy-caffeine', action='store_true', help='Exact separately prepared old Caffeine palette API')
    args = parser.parse_args()
    dependency = args.source.resolve() / 'cosmic-theme'
    required_method = 'with_popup_material' if args.legacy_caffeine else 'with_window_material'
    if not (dependency / 'Cargo.toml').is_file() or required_method not in (dependency / 'src/model/theme.rs').read_text():
        raise ValueError('Use the prepared native window-profile source.')
    if args.legacy_caffeine:
        expected = (HERE / 'legacy/theme_method.rs').read_text()
        if expected not in (dependency / 'src/model/theme.rs').read_text():
            raise ValueError('Use the exact reviewed legacy Caffeine material source.')
    with tempfile.TemporaryDirectory(prefix='studio-native-palette-') as folder:
        root = Path(folder)
        (root / 'src').mkdir()
        (root / 'Cargo.toml').write_text(
            '[package]\nname="studio-native-palette-review"\nversion="0.1.0"\nedition="2024"\n'
            '[dependencies]\ncosmic-theme={path=' + json.dumps(str(dependency)) + '}\n')
        test_source = HERE / ('legacy/native_palette.rs' if args.legacy_caffeine else 'tests/native_palette.rs')
        (root / 'src/lib.rs').write_text(test_source.read_text())
        shutil.copyfile(args.lockfile.resolve(), root / 'Cargo.lock')
        subprocess.run(['cargo', 'test', '--offline', '--manifest-path', str(root / 'Cargo.toml'),
                        '--target-dir', str(args.target_dir.resolve()), '-j', '4', '--', '--nocapture', '--test-threads=1'], check=True)


if __name__ == '__main__':
    main()
