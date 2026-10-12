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


def backend_test_command(manifest, jobs):
    # A dependency package can be selected for testing, but Cargo forbids
    # enabling its features from the application workspace. Retain the app's
    # original unified feature graph; verify the actual test artifact below.
    return ['cargo', 'test', '--locked', '--manifest-path', str(manifest),
            '-p', 'iced_winit', '--lib', '--no-run', '--message-format=json',
            '-j', str(jobs)]


def backend_test_artifact(metadata, messages, library, target):
    packages = [p for p in metadata['packages'] if p['name'] == 'iced_winit']
    if len(packages) != 1:
        raise ValueError('Expected one exact native backend package.')
    package = packages[0]
    if Path(package['manifest_path']).resolve() != (library/'iced/winit/Cargo.toml').resolve():
        raise ValueError('Backend package is not the reviewed local Iced source.')
    nodes = [n for n in metadata['resolve']['nodes'] if n['id'] == package['id']]
    if len(nodes) != 1 or 'wayland' not in nodes[0]['features']:
        raise ValueError('Original backend metadata must include Wayland.')
    matches = [m for m in messages if m.get('reason') == 'compiler-artifact'
               and m.get('package_id') == package['id']
               and m.get('executable') and m.get('profile', {}).get('test')
               and m.get('target', {}).get('name') == 'iced_winit']
    if len(matches) != 1:
        raise ValueError('Expected one compiled native backend test artifact.')
    artifact = matches[0]
    if (set(artifact['features']) != set(nodes[0]['features'])
            or Path(artifact['target']['src_path']).resolve() != (library/'iced/winit/src/lib.rs').resolve()):
        raise ValueError('Backend test source/features differ from the original application graph.')
    binary = Path(artifact['executable']).resolve()
    if not binary.is_relative_to(target.resolve()) or not binary.is_file():
        raise ValueError('Backend test executable must be in the owned target directory.')
    with binary.open('rb') as stream:
        if stream.read(4) != b'\x7fELF':
            raise ValueError('Backend test executable is not a native ELF.')
    return artifact


def application_test_command(manifest, package, jobs):
    return ['cargo', 'test', '--locked', '--manifest-path', str(manifest),
            '--bin', package, '--no-run', '--message-format=json', '-j', str(jobs)]


def application_test_artifact(metadata, messages, app, target):
    packages = [p for p in metadata['packages']
                if Path(p['manifest_path']).resolve() == (app/'Cargo.toml').resolve()]
    if len(packages) != 1 or packages[0].get('source') is not None:
        raise ValueError('Expected the exact local application package.')
    package = packages[0]
    nodes = [n for n in metadata['resolve']['nodes'] if n['id'] == package['id']]
    matches = [m for m in messages if m.get('reason') == 'compiler-artifact'
               and m.get('package_id') == package['id'] and m.get('executable')
               and m.get('profile', {}).get('test')
               and m.get('target', {}).get('name') == package['name']
               and m.get('target', {}).get('kind') == ['bin']]
    if len(nodes) != 1 or len(matches) != 1:
        raise ValueError('Expected one original-feature compiled application test artifact.')
    artifact = matches[0]
    if (set(artifact['features']) != set(nodes[0]['features'])
            or Path(artifact['target']['src_path']).resolve() != (app/'src/main.rs').resolve()):
        raise ValueError('Application test source/features differ from original metadata.')
    binary = Path(artifact['executable'])
    if (binary.is_symlink() or not binary.resolve().is_relative_to(target.resolve())
            or not binary.is_file() or binary.read_bytes()[:4] != b'\x7fELF'):
        raise ValueError('Application test must be an owned native target ELF.')
    return artifact


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
    backend = None
    application_tests = None
    if profile in ('brightness', 'sysinfo'):
        package = tomllib.loads((app/'Cargo.toml').read_text())['package']['name']
        messages_path = output/'app-test-artifacts.jsonl'
        command('app-test-build', application_test_command(manifest, package, jobs), messages_path)
        prepare.prepare(app, library, profile)
        messages = [json.loads(line) for line in messages_path.read_text().splitlines() if line.strip()]
        artifact = application_test_artifact(json.loads((output/'metadata.json').read_text()),
                                             messages, app, target)
        frozen_test = output/(profile+'-app-tests')
        shutil.copy2(artifact['executable'], frozen_test)
        command('app-tests', [str(frozen_test.resolve()), '--test-threads=1'])
        application_tests = {'package_id': artifact['package_id'], 'features': artifact['features'],
                             'source': artifact['target']['src_path'], 'executable': str(frozen_test.resolve()),
                             'binary_sha256': prepare.digest(frozen_test),
                             'feature_graph': 'identical to original resolved application metadata',
                             'scope': 'Full application test compilation; production module/original app tests, not sensors/DDC/desktop runtime'}
        (output/'app-tests.json').write_text(json.dumps(application_tests, indent=2)+'\n')
        prepare.prepare(app, library, profile)
    if profile == 'caffeine':
        messages_path = output/'backend-test-artifacts.jsonl'
        command('backend-test-build', backend_test_command(manifest, jobs), messages_path)
        prepare.prepare(app, library, profile)
        messages = [json.loads(line) for line in messages_path.read_text().splitlines() if line.strip()]
        backend = backend_test_artifact(json.loads((output/'metadata.json').read_text()),
                                        messages, library, target)
        binary = Path(backend['executable'])
        frozen_test = output/'iced-winit-tests'
        shutil.copy2(binary, frozen_test)
        command('backend-tests', [str(frozen_test.resolve()), '--test-threads=1'])
        backend = {'package_id': backend['package_id'], 'features': backend['features'],
                   'source': backend['target']['src_path'], 'executable': str(frozen_test.resolve()),
                   'binary_sha256': prepare.digest(frozen_test),
                   'feature_graph': 'identical to original resolved application metadata'}
        (output/'backend-tests.json').write_text(json.dumps(backend, indent=2)+'\n')
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
              'seconds': time.time()-started, 'phases': phases, 'backend_tests': backend,
              'application_tests': application_tests,
              'runtime_gate': 'pending', 'deployed': False}
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
