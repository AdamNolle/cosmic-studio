#!/usr/bin/env python3
"""Build exact-pinned remaining OS clients; never install or launch candidates."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tomllib

# Running this script supplies its own directory on sys.path.
from prepare_components import COMPONENTS
from build_core_apps import clone

HERE = Path(__file__).resolve().parent
SOURCES = {name: (revision, library) for revision, (name, library) in COMPONENTS.items()}
WINDOW_APPS = {'cosmic-store', 'cosmic-monitor', 'cosmic-player', 'cosmic-viewer'}
DEFAULTS = ['cosmic-applets', 'cosmic-notifications', 'cosmic-osd',
            'cosmic-store', 'cosmic-monitor', 'cosmic-player', 'cosmic-viewer', 'cosmic-osk']


def is_native_source(source):
    return source.split('#')[0].split('?')[0].removesuffix('/').removesuffix('.git') == 'git+https://github.com/pop-os/libcosmic'


def native_packages(lock):
    return {(p['name'], p['version']) for p in tomllib.loads(lock)['package']
            if is_native_source(p.get('source', ''))}


def foreign_dependencies(lock, substitutions=()):
    """Only the original libcosmic packages may change from Git to local paths."""
    return {(p['name'], p['version'], p.get('source', ''), p.get('checksum', ''))
            for p in tomllib.loads(lock)['package']
            if not is_native_source(p.get('source', ''))
            and not ((p['name'], p['version']) in substitutions and not p.get('source'))}


def library_profiles(components):
    profiles = {}
    for component in components:
        library = SOURCES[component][1]
        profiles[library] = profiles.get(library, False) or component in WINDOW_APPS
    return profiles


def preflight(work, components):
    # Fail before any network fetch or source mutation if a selected tree exists.
    if len(components) != len(set(components)):
        raise ValueError('Select each component only once.')
    paths = [work / component for component in components]
    paths += [work / ('libcosmic-' + revision[:8]) for revision in library_profiles(components)]
    for path in paths:
        if path.exists() or path.is_symlink():
            raise FileExistsError(f'Use a fresh --work directory; refusing existing source: {path}')


def run(*args, cwd=None, env=None):
    subprocess.run([str(a) for a in args], cwd=cwd, env=env, check=True)


def build(work, components, jobs, toolchain):
    if not 1 <= jobs <= 24:
        raise ValueError('Jobs must be between 1 and 24.')
    preflight(work, components)
    work.mkdir(parents=True, exist_ok=True)
    libraries = {}
    env = os.environ.copy()
    env['CARGO_TARGET_DIR'] = str(work / 'target')
    python = sys.executable
    for revision, window_glass in library_profiles(components).items():
        library = work / ('libcosmic-' + revision[:8])
        clone('https://github.com/pop-os/libcosmic.git', revision, library)
        display = work / ('typography-' + revision[:8] + '.patch')
        run(python, HERE / 'patch_libcosmic.py', library, '--output', display)
        run('git', 'apply', '--check', display, cwd=library)
        run('git', 'apply', display, cwd=library)
        run(python, HERE / 'embed_fonts.py', library,
            '--output', work / ('embedded-fonts-' + revision[:8] + '.patch'), '--apply')
        run(python, HERE / 'prepare_display_roles.py', library, '--profile', 'native-' + revision[:8],
            '--output', work / ('display-roles-' + revision[:8] + '.patch'), '--apply')
        flags = ['--window-glass'] if window_glass else []
        run(python, HERE.parent / 'popups/prepare.py', library, '--revision', revision,
            '--output', work / ('materials-' + revision[:8] + '.patch'), '--apply', *flags)
        run(python, HERE.parent / 'dock-icons/prepare_tooltip.py', library, '--apply')
        if window_glass:
            run(python, HERE.parent / 'window-controls/prepare.py', library)
        run('git', 'diff', '--check', cwd=library)
        libraries[revision] = library
    built = []
    for component in components:
        revision, library_revision = SOURCES[component]
        application = work / component
        clone(f'https://github.com/pop-os/{component}.git', revision, application)
        old_lock = (application / 'Cargo.lock').read_bytes()
        substitutions = native_packages(old_lock.decode())
        expected = foreign_dependencies(old_lock.decode(), substitutions)
        run(python, HERE / 'prepare_components.py', application, '--library', libraries[library_revision],
            '--output', work / (component + '-native.patch'), '--apply')
        if component == 'cosmic-applets':
            run(python, HERE / 'prepare_display_roles.py', application, '--profile', 'cosmic-applets-calendar',
                '--output', work / 'calendar-display-role.patch', '--apply')
            run(python, HERE.parent / 'dock-icons/prepare.py', '--source', application, '--apply')
        # Resolve local substitutions once. Do not accept registry or foreign Git drift.
        result = subprocess.run(['cargo', '+' + toolchain, 'metadata', '--format-version', '1'],
                                cwd=application, env=env, stdout=subprocess.PIPE, check=True)
        (work / (component + '-metadata.json')).write_bytes(result.stdout)
        if foreign_dependencies((application / 'Cargo.lock').read_text(), substitutions) != expected:
            (application / 'Cargo.lock').write_bytes(old_lock)
            raise RuntimeError(f'Unexpected foreign dependency changes in {component}; original lock restored.')
        binaries = [component] + (['cosmic-panel-button'] if component == 'cosmic-applets' else [])
        selections = [argument for binary in binaries for argument in ('--bin', binary)]
        run('cargo', '+' + toolchain, 'check', '--locked', *selections, '-j', jobs, cwd=application, env=env)
        run('cargo', '+' + toolchain, 'build', '--release', '--locked', *selections, '-j', jobs,
            cwd=application, env=env)
        run('git', 'diff', '--check', cwd=application)
        if foreign_dependencies((application / 'Cargo.lock').read_text(), substitutions) != expected:
            raise RuntimeError(f'Foreign dependency graph changed after locked build: {component}')
        for binary in binaries:
            candidate = work / 'target/release' / binary
            with candidate.open('rb') as stream:
                if stream.read(4) != b'\x7fELF':
                    raise RuntimeError(f'Expected native ELF candidate: {candidate}')
            destination = work / 'artifacts' / binary
            destination.parent.mkdir(exist_ok=True)
            shutil.copy2(candidate, destination)
            report = {'schema': 1, 'component': component, 'binary': binary,
                      'source_commit': revision, 'library_commit': library_revision,
                      'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
                      'lock_sha256': hashlib.sha256((application / 'Cargo.lock').read_bytes()).hexdigest(),
                      'foreign_dependency_graph_unchanged': True, 'installed': False,
                      'runtime_validated': False, 'candidate': str(destination)}
            (destination.parent / (binary + '.json')).write_text(json.dumps(report, indent=2) + '\n')
            built.append(report)
        if component == 'cosmic-applets':
            run(python, HERE.parent / 'dock-icons/prepare.py', '--source', application,
                '--record-binary', work / 'artifacts/cosmic-applets',
                '--output', work / 'artifacts/compact-dock-build.json')
    print(json.dumps({'candidates': built, 'installed': False}, indent=2))
    return built


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--components', nargs='+', choices=sorted(SOURCES), default=DEFAULTS)
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--toolchain', default='stable')
    args = parser.parse_args()
    if platform.system() != 'Linux':
        parser.error('Build native ELF candidates inside the Linux guest.')
    if not 1 <= args.jobs <= 24:
        parser.error('--jobs must be between 1 and 24.')
    build(args.work.resolve(), args.components, args.jobs, args.toolchain)
