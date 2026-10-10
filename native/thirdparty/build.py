#!/usr/bin/env python3
"""Compile reviewed applets without upgrading their original dependency graph."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import tomllib

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('studio_thirdparty_prepare', HERE/'prepare_build.py')
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


def run(profile, sources, target, artifacts, deps, jobs):
    app = sources/('app-'+profile+'-native')
    library = sources/('library-'+profile+'-native')
    prepare.prepare(app, library, profile)
    output = artifacts/profile
    output.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.pop('LD_LIBRARY_PATH', None)
    env['PATH'] = str(Path.home()/'.cargo/bin')+os.pathsep+env.get('PATH', '')
    env['CARGO_TARGET_DIR'] = str(target.resolve())
    if deps:
        lib = deps/'usr/lib/x86_64-linux-gnu'
        env['PKG_CONFIG_PATH'] = os.pathsep.join(str(p) for p in
            (lib/'pkgconfig', deps/'usr/share/pkgconfig', Path('/usr/lib/x86_64-linux-gnu/pkgconfig')))
        env['LIBRARY_PATH'] = str(lib)
    # Native source substitutions require one lock normalization before the
    # first locked command. Every original foreign package remains authoritative.
    old_lock = (app/'Cargo.lock').read_bytes()
    started = time.time()
    phases = []
    def command(name, arguments, stdout_path=None):
        print(profile+': '+name, flush=True)
        log = output/(name+'.log')
        with log.open('wb') as stream:
            if stdout_path:
                with stdout_path.open('wb') as stdout:
                    result = subprocess.run(arguments, cwd=app, env=env, stdout=stdout, stderr=stream)
            else:
                result = subprocess.run(arguments, cwd=app, env=env, stdout=stream, stderr=subprocess.STDOUT)
        phases.append({'name': name, 'returncode': result.returncode, 'log': str(log.resolve())})
        if result.returncode:
            raise RuntimeError(profile+' '+name+' failed; inspect '+str(log))
    try:
        command('metadata', ['cargo', 'metadata', '--format-version', '1', '--manifest-path', str(app/'Cargo.toml')],
                output/'metadata.json')
        prepare.prepare(app, library, profile)
    except BaseException:
        (app/'Cargo.lock').write_bytes(old_lock)
        raise
    manifest = str(app/'Cargo.toml')
    command('check', ['cargo', 'check', '--locked', '--manifest-path', manifest, '-j', str(jobs)])
    prepare.prepare(app, library, profile)
    if profile == 'caffeine':
        command('backend-tests', ['cargo', 'test', '--locked', '--manifest-path', manifest,
                                 '-p', 'iced_winit', '--lib', '--no-default-features',
                                 '--features', 'iced_winit/wayland', '-j', str(jobs)])
        prepare.prepare(app, library, profile)
    command('release', ['cargo', 'build', '--locked', '--release', '--manifest-path', manifest, '-j', str(jobs)])
    marker = prepare.prepare(app, library, profile)
    package = tomllib.loads((app/'Cargo.toml').read_text())['package']['name']
    candidate = target/'release'/package
    if not candidate.is_file() or candidate.read_bytes()[:4] != b'\x7fELF':
        raise RuntimeError('Expected linked native applet candidate: '+str(candidate))
    immutable = output/package
    shutil.copy2(candidate, immutable)
    report = {'schema': 1, 'profile': profile, 'source': str(app.resolve()), 'library': str(library.resolve()),
              'candidate': str(immutable.resolve()), 'binary_sha256': prepare.digest(immutable),
              'prepared_marker_sha256': prepare.digest(marker), 'lock_sha256': prepare.digest(app/'Cargo.lock'),
              'foreign_dependency_graph': 'identical to exact original lock; native Git-to-path substitutions only',
              'seconds': time.time()-started, 'phases': phases, 'runtime_gate': 'pending', 'deployed': False}
    (output/'build.json').write_text(json.dumps(report, indent=2)+'\n')
    print(profile+': compiled '+str(immutable)+' SHA256 '+report['binary_sha256'], flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, required=True)
    parser.add_argument('--target', type=Path, required=True)
    parser.add_argument('--artifacts', type=Path, required=True)
    parser.add_argument('--deps', type=Path)
    parser.add_argument('--jobs', type=int, default=3)
    parser.add_argument('--profile', choices=prepare.PROFILES, action='append')
    args = parser.parse_args()
    if not 1 <= args.jobs <= 3:
        parser.error('Use 1–3 independent jobs while the native shell queue is active.')
    for profile in args.profile or ('caffeine', 'brightness', 'sysinfo', 'status-hub'):
        run(profile, args.sources.resolve(), args.target.resolve(), args.artifacts.resolve(), args.deps, args.jobs)
