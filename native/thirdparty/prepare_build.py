#!/usr/bin/env python3
"""Record exact prepared applet sources and local crate substitutions; never build.

Call after the strict font, popup and (for Caffeine) native blur source transforms.
Repeated preparation validates every recorded source/resource file and generator
hash. It refuses stale trees instead of quietly reusing a prior preparation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tomllib

PACKAGE = Path(__file__).resolve().parents[2]
PROFILES = {
    'caffeine': ('41edb7bc1dabfa7d0033484ca81db0ac64e32a5c', '76c1897d4d9a637c8aa4016483bf05fec5f10ebd'),
    'brightness': ('3e6486ff11dba8cdb729420c27b4ce2c519f8443', 'dc1cf9f00cbe2902a52166492654bb9fee8a73d1'),
    'sysinfo': ('f66e0c7b133bf4249d23ab7483693cedca46ad19', '1f8d8786940cc6db59d412153c5a03f69a20375c'),
    'status-hub': ('d09f89256c254310a660d84780bba9b8a75b23be', 'a401af8b1c54a8abd393b8c5b7c8809402f83850'),
}


def git(folder, *args):
    return subprocess.check_output(['git', *args], cwd=folder, text=True).strip()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(folder, exclude=()):
    files = {}
    roots = [folder]
    # All recursively pinned submodule files matter, including the native Iced
    # backport; the parent repository's dirty-submodule marker alone is not enough.
    for line in git(folder, 'submodule', 'status', '--recursive').splitlines():
        if line[:1] in ('-', '+', 'U'):
            raise ValueError('Unverified or changed pinned submodule: '+line)
        roots.append(folder/line.strip().split()[1])
    for root in roots:
        for name in git(root, 'ls-files', '--cached', '--others', '--exclude-standard').splitlines():
            file = root/name
            relative = str(file.relative_to(folder))
            if file.is_file() and not file.name.startswith('.studio-') and relative not in exclude:
                files[relative] = digest(file)
    return dict(sorted(files.items()))


def generator_inputs(profile):
    paths = [PACKAGE/'native/typography/embed_fonts.py',
             PACKAGE/'native/typography/patch_libcosmic.py', PACKAGE/'fonts/manifest.json']
    paths += [PACKAGE/'native/thirdparty/prepare_build.py']
    paths += [PACKAGE/'native/typography/prepare_display_roles.py']
    if profile in ('brightness', 'sysinfo'):
        paths += [PACKAGE/'native/thirdparty/prepare_routes.py']
    paths += [PACKAGE/'native/popups'/name for name in
              ('prepare.py', 'policy.rs', 'material.rs', 'theme_method.rs', 'window_patch.py')]
    if profile == 'caffeine':
        paths += [PACKAGE/'native/thirdparty'/name for name in
                  ('prepare_caffeine_blur.py', 'caffeine-blur.patch', 'caffeine-blur-profile.json')]
        paths += [PACKAGE/'native/popups/legacy'/name for name in
                  ('caffeine.py', 'compatibility.json', 'material.rs', 'theme_method.rs')]
    inputs = {str(p.relative_to(PACKAGE)): digest(p) for p in sorted(paths)}
    # Added unrelated profiles/specimen tests do not change this transformation.
    # Hash the selected registry entry; all consumed implementation files above
    # still have their full hashes recorded.
    registry = json.loads((PACKAGE/'native/popups/compatibility.json').read_text())
    entry = next(p for p in registry['profiles'] if p['revision'] == PROFILES[profile][1]) if profile != 'caffeine' else None
    if entry is not None:
        inputs['native/popups/compatibility.json#'+entry['revision']] = hashlib.sha256(
            json.dumps(entry, sort_keys=True).encode()).hexdigest()
    roles = json.loads((PACKAGE/'native/typography/display-role-profiles.json').read_text())
    role_key = 'native-'+PROFILES[profile][1][:8]
    inputs['native/typography/display-role-profiles.json#'+role_key] = hashlib.sha256(
        json.dumps(roles['profiles'][role_key], sort_keys=True).encode()).hexdigest()
    return inputs


def crate_entries(library):
    entries = {}
    for cargo in library.rglob('Cargo.toml'):
        if any(part in ('target', '.git') for part in cargo.relative_to(library).parts):
            continue
        try:
            name = tomllib.loads(cargo.read_text()).get('package', {}).get('name', '')
        except tomllib.TOMLDecodeError:
            continue
        if name == 'libcosmic' or name.startswith('iced') or name in ('cosmic-config', 'cosmic-config-derive', 'cosmic-theme'):
            if name in entries:
                raise ValueError('Ambiguous native crate name: '+name)
            entries[name] = cargo.parent
    if 'libcosmic' not in entries or 'iced_winit' not in entries:
        raise ValueError('Expected native toolkit crate roots are missing.')
    return entries


def lock_packages(text, native_crates, library_revision):
    """Permit only exact-revision Git-to-local substitutions, never version drift."""
    packages = []
    for package in tomllib.loads(text)['package']:
        item = {key: package[key] for key in ('name', 'version', 'source', 'checksum') if key in package}
        if package['name'] in native_crates:
            source = package.get('source')
            if source is not None and not (source.startswith('git+https://github.com/pop-os/libcosmic') and source.endswith('#'+library_revision)):
                raise ValueError('Unexpected source for native crate: '+package['name'])
            item.pop('source', None)
            item.pop('checksum', None)
        packages.append(item)
    return sorted(packages, key=lambda p: (p['name'], p['version'], p.get('source', '')))


def prepare(app, library, profile):
    app, library = app.resolve(), library.resolve()
    for source in (app, library):
        if any(source.is_relative_to(p) for p in (Path('/usr'), Path.home()/'.var', Path.home()/'.local', Path.home()/'.cargo')):
            raise ValueError('Use isolated app/library sources, never installed files or Cargo caches.')
    if app.parent != library.parent:
        raise ValueError('App and library must be sibling isolated sources for portable relative overrides.')
    app_revision, library_revision = PROFILES[profile]
    if git(app, 'rev-parse', 'HEAD') != app_revision or git(library, 'rev-parse', 'HEAD') != library_revision:
        raise ValueError('Exact installed source/library revisions are required.')
    marker = app/'.studio-thirdparty-prepared.json'
    cargo = app/'Cargo.toml'
    entries = crate_entries(library)
    original_lock_bytes = subprocess.check_output(['git', 'show', 'HEAD:Cargo.lock'], cwd=app)
    original_lock = original_lock_bytes.decode()
    expected_lock = lock_packages(original_lock, entries, library_revision)
    if lock_packages((app/'Cargo.lock').read_text(), entries, library_revision) != expected_lock:
        raise ValueError('App dependency versions/sources drifted from its exact upstream lock; refuse upgrades.')
    inputs = {'schema': 2, 'profile': profile, 'app_revision': app_revision,
              'library_revision': library_revision, 'generators': generator_inputs(profile),
              'library_files': inventory(library), 'app_files': inventory(app, exclude=('Cargo.lock',)),
              'original_app_lock_sha256': hashlib.sha256(original_lock_bytes).hexdigest(),
              'app_locked_packages': expected_lock,
              'crate_paths': {k: str(v.relative_to(library)) for k, v in sorted(entries.items())}}
    if marker.exists():
        if json.loads(marker.read_text()) != inputs:
            raise ValueError('Stale prepared source/generator fingerprints; preserve this tree and prepare a fresh isolated copy.')
        return marker
    if tomllib.loads(cargo.read_text()).get('patch', {}).get('https://github.com/pop-os/libcosmic'):
        raise ValueError('Existing app override without a valid prepared marker; inspect it before reuse.')
    if 'pub fn display()' not in (library/'src/font.rs').read_text() or 'res/studio-fonts/archivo/Archivo-Regular.ttf' not in (library/'src/app/mod.rs').read_text():
        raise ValueError('Native semantic/embedded typography preparation is missing.')
    overrides = '\n[patch."https://github.com/pop-os/libcosmic"]\n'
    overrides += ''.join(f'{name} = {{ path = "../{library.name}/{path.relative_to(library)}" }}\n'
                         for name, path in sorted(entries.items()))
    cargo.write_text(cargo.read_text()+overrides)
    inputs['app_files'] = inventory(app, exclude=('Cargo.lock',))
    marker.write_text(json.dumps(inputs, indent=2, sort_keys=True)+'\n')
    return marker


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', type=Path, required=True)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--profile', choices=PROFILES, required=True)
    args = parser.parse_args()
    print('Prepared exact native app source: '+str(prepare(args.app, args.library, args.profile)))


if __name__ == '__main__':
    main()
