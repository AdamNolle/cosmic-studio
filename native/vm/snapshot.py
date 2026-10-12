#!/usr/bin/env python3
"""Export tracked build inputs plus explicitly named new files; never export caches or secrets."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN = {'.git', '.ralph', 'work', 'backups', '__pycache__', '.ssh'}
PRIVATE_NAMES = {'guest-account.json', 'development_ed25519', 'id_rsa', 'id_dsa', 'id_ecdsa', 'id_ed25519'}


def safe_name(name):
    path = PurePosixPath(name)
    if path.is_absolute() or not path.parts or any(p.casefold() in FORBIDDEN or p in ('.', '..') for p in path.parts):
        raise ValueError(f'Unsafe snapshot path: {name}')
    if ('\\' in name or ':' in name or path.name.casefold() in PRIVATE_NAMES
            or path.suffix.lower() in {'.iso', '.vdi', '.vhdx', '.vmdk', '.vbox', '.nvram', '.sav', '.pem', '.key'}):
        raise ValueError(f'Not a source input: {name}')
    return path.as_posix()


def inputs(root, include):
    entries = subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=root).split(b'\0')
    paths = {}
    for entry in entries:
        if not entry:
            continue
        meta, name = entry.split(b'\t', 1)
        mode, _, stage = meta.split()
        if stage != b'0':
            raise ValueError('Resolve Git conflicts before exporting build inputs.')
        if mode == b'160000':
            raise ValueError('Source submodules must be exported explicitly, not silently omitted.')
        paths[safe_name(name.decode('utf-8'))] = int(mode, 8)
    for name in include:
        paths.setdefault(safe_name(name), 0o100644)
    return paths


def export(root, output, include=()):
    root = root.resolve()
    paths = inputs(root, include)
    output = output.resolve()
    if output.is_relative_to(root):
        raise ValueError('Write snapshots outside the source repository.')
    if output.exists():
        raise FileExistsError(f'Refusing to overwrite snapshot: {output}')
    # Validate the entire input set before creating the archive.
    files = []
    for name, mode in sorted(paths.items()):
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError(f'Refusing symlink or escaped source input: {name}')
        if not path.is_file():
            raise ValueError(f'Missing tracked source input: {name}')
        files.append((name, mode, path.read_bytes()))
    manifest = {
        'schema': 1,
        'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
        'files': {name: hashlib.sha256(data).hexdigest() for name, _, data in files},
        'includes_working_tree_changes': True,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open('xb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode='w|', format=tarfile.PAX_FORMAT) as archive:
                for name, mode, data in files:
                    entry = tarfile.TarInfo(name)
                    entry.size = len(data)
                    entry.mode = mode & 0o777
                    archive.addfile(entry, io.BytesIO(data))
                data = (json.dumps(manifest, sort_keys=True, indent=2) + '\n').encode()
                entry = tarfile.TarInfo('studio-source-manifest.json')
                entry.size = len(data)
                entry.mode = 0o644
                archive.addfile(entry, io.BytesIO(data))
    except Exception:
        output.unlink(missing_ok=True)
        raise
    return {'files': len(files), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--include', action='append', default=[], help='Explicit new relative source path (repeatable)')
    args = parser.parse_args()
    print(json.dumps(export(ROOT, args.output, args.include), indent=2))
