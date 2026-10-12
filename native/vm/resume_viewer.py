#!/usr/bin/env python3
"""Retained locked Viewer resume after a genuine prerequisite fix; no deployment."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(source):
    result = {}
    for directory, children, files in os.walk(source):
        children[:] = [name for name in children if name not in ('.git', 'target', '__pycache__')]
        for name in files:
            if name == '.git':
                continue
            path = Path(directory) / name
            if path.is_symlink():
                result[str(path.relative_to(source))] = 'symlink:' + os.readlink(path)
            else:
                result[str(path.relative_to(source))] = digest(path)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--build-dir', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=2)
    args = parser.parse_args()
    if platform.system() != 'Linux' or os.geteuid() == 0:
        parser.error('Run as the normal Linux development user, not root.')
    if not 1 <= args.jobs <= 24:
        parser.error('Jobs must be between 1 and 24.')
    overrides = {k: v for k, v in os.environ.items() if k.startswith(('CARGO_PROFILE_', 'RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS'))}
    if overrides:
        parser.error('Refusing caller compiler/profile overrides.')
    project, build = args.project.resolve(), args.build_dir.resolve()
    if build.parent != project / 'work/native-builds':
        parser.error('Select an original native-build directory inside this project.')
    prior = json.loads((build / 'report.json').read_text())
    if prior['component'] != 'media' or prior['status'] != 'failed':
        parser.error('Select a retained failed media run, not a running or completed pipeline.')
    spec = importlib.util.spec_from_file_location('viewer_lock_guard', project / 'native/typography/lock_guard.py')
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    sys.path.insert(0, str(project / 'native/typography'))
    from prepare_components import COMPONENTS
    revision, (_, library_revision) = next((r, data) for r, data in COMPONENTS.items() if data[0] == 'cosmic-viewer')
    source = build / 'sources/cosmic-viewer'
    library = build / ('sources/libcosmic-' + library_revision[:8])
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    out = project / 'work/native-resumes' / ('viewer-' + stamp)
    out.mkdir(parents=True)
    manifest = out / 'studio-source-manifest.json'
    manifest.write_bytes((build / 'studio-source-manifest.json').read_bytes())
    report = {'schema': 1, 'status': 'running', 'component': 'cosmic-viewer',
              'start_utc': stamp, 'source': str(source), 'library': str(library),
              'original_failed_report': str(build / 'report.json'),
              'original_failed_report_sha256': digest(build / 'report.json'),
              'source_manifest_sha256': digest(manifest), 'resumer_sha256': digest(Path(__file__)),
              'uid': os.geteuid(), 'kernel': platform.release(), 'jobs': args.jobs,
              'commands': [], 'installed': False, 'runtime_validated': False}
    env = os.environ.copy()
    env['CARGO_TARGET_DIR'] = str(build / 'sources/target')
    report['environment'] = {'PATH': env.get('PATH', ''), 'CARGO_TARGET_DIR': env['CARGO_TARGET_DIR'], 'overrides': overrides}
    destination = out / 'report.json'
    def save():
        destination.write_text(json.dumps(report, indent=2) + '\n')
    print('VIEWER_RESUME_REPORT=' + str(destination), flush=True)
    save()
    with (out / 'build.log').open('x') as log:
        def run(argv, cwd=source):
            report['commands'].append({'argv': [str(a) for a in argv], 'cwd': str(cwd)})
            save()
            result = subprocess.run(argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            log.write_bytes(result.stdout) if 'b' in log.mode else log.write(result.stdout.decode(errors='replace'))
            log.flush()
            result.check_returncode()
            return result.stdout
        try:
            for tree, pin in ((source, revision), (library, library_revision)):
                if run(['git', 'rev-parse', 'HEAD'], tree).decode().strip() != pin:
                    raise RuntimeError('Unexpected retained source/library revision.')
            original = run(['git', 'show', revision + ':Cargo.lock'])
            guard.validate(source, original)
            before = {'application': inventory(source), 'library': inventory(library)}
            (out / 'inputs-before.json').write_text(json.dumps(before, sort_keys=True, indent=2) + '\n')
            report['inputs_sha256'] = digest(out / 'inputs-before.json')
            report['rustc'] = run(['rustc', '+stable', '--version']).decode().strip()
            report['cargo'] = run(['cargo', '+stable', '--version']).decode().strip()
            run(['cargo', '+stable', 'build', '--release', '--locked', '--bin', 'cosmic-viewer', '-j', str(args.jobs)])
            guard.validate(source, original)
            after = {'application': inventory(source), 'library': inventory(library)}
            (out / 'inputs-after.json').write_text(json.dumps(after, sort_keys=True, indent=2) + '\n')
            if before != after:
                raise RuntimeError('Retained prepared input changed during locked resume.')
            candidate = build / 'sources/target/release/cosmic-viewer'
            with candidate.open('rb') as stream:
                if stream.read(4) != b'\x7fELF':
                    raise RuntimeError('Expected native ELF output.')
            frozen = out / 'cosmic-viewer'
            shutil.copy2(candidate, frozen)
            report['binary_sha256'] = digest(frozen)
            if digest(candidate) != report['binary_sha256']:
                raise RuntimeError('Frozen output differs from original.')
            run(['file', str(frozen)])
            libraries = run(['ldd', str(frozen)]).decode()
            if 'not found' in libraries:
                raise RuntimeError('Unresolved dynamic library.')
            report.update(status='built', returncode=0, prepared_inputs_unchanged=True,
                          foreign_dependency_graph_unchanged=True, candidate=str(frozen))
        except Exception as error:
            report.update(status='failed', returncode=1, error=str(error))
            log.write('\nRESUME_FAILED: ' + str(error) + '\n')
    report['end_utc'] = datetime.now(timezone.utc).isoformat()
    save()
    print('VIEWER_RESUME_EXIT=' + str(report['returncode']), flush=True)
    return report['returncode']


if __name__ == '__main__':
    sys.exit(main())
