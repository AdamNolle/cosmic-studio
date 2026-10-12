#!/usr/bin/env python3
"""Build authentic source-matched stock Debian packages. Never install packages.

Original application/toolkit code, locks, features and Debian recipes are retained.
Only the publication changelog records the actual full source SHA/local build.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[2]
PINS = {
    'cosmic-comp': '0fbd4574ef4caf74769a617d205fd1fc909ac9b1',
    'cosmic-panel': 'b5cc19e351b82eed999097ced1ff267d27bf8e7a',
}


def publication(original, component, revision):
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('Require the full authentic source SHA.')
    match = re.match(r'([^ ]+) \(([^)]+)\) ', original)
    if not match or match[1] != component:
        raise ValueError('Original package changelog does not match selected source.')
    version = match[2] + '+studio.stock.git' + revision
    date = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')
    stanza = (f'{component} ({version}) noble; urgency=medium\n\n'
              f'  * Local unmodified stock build from upstream commit {revision}.\n'
              '    No Studio source patches or changed dependency pins/features.\n\n'
              f' -- COSMIC Studio VM Builder <studio@localhost>  {date}\n\n')
    return version, stanza + original


def verify_pristine(source):
    # Tracked source changes, including native toolkit submodule changes, fail.
    names = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD'], cwd=source, text=True).splitlines()
    if set(names) - {'debian/changelog'}:
        raise RuntimeError('Stock tracked source changed: ' + ', '.join(names))
    subprocess.run(['git', 'submodule', 'foreach', '--recursive',
                    'git diff --exit-code HEAD && test -z "$(git status --porcelain --untracked-files=no)"'],
                   cwd=source, check=True)


def verify_lock(source, original):
    if (source / 'Cargo.lock').read_bytes() != original:
        raise RuntimeError('Original stock Cargo.lock changed; refusing to publish.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--component', required=True, choices=PINS)
    parser.add_argument('--jobs', type=int, default=1)
    args = parser.parse_args()
    if platform.system() != 'Linux' or os.geteuid() == 0:
        parser.error('Run as the normal Linux development user, never root.')
    if not 1 <= args.jobs <= 8:
        parser.error('Jobs must be between 1 and 8.')
    revision = PINS[args.component]
    env = os.environ.copy()
    for name in env:
        if name.startswith(('CARGO_PROFILE_', 'RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS')) or name in (
                'CARGO_TARGET_DIR', 'RUSTUP_TOOLCHAIN'):
            parser.error('Unexpected caller build override: ' + name)
    env.update(CARGO_BUILD_JOBS=str(args.jobs), VENDOR='1', SOURCE_GIT_HASH=revision, GIT_HASH=revision)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    work = ROOT / 'work/stock-builds' / (args.component + '-' + stamp)
    work.mkdir(parents=True)
    source = work / args.component
    manifest = work / 'studio-source-manifest.json'
    manifest.write_bytes((ROOT / 'studio-source-manifest.json').read_bytes())
    report = {'schema': 1, 'component': args.component, 'source_commit': revision,
              'repository': 'https://github.com/pop-os/' + args.component + '.git',
              'status': 'running', 'start_utc': stamp, 'uid': os.geteuid(),
              'cwd': str(ROOT), 'source': str(source), 'commands': [],
              'input_manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
              'input_manifest': str(manifest), 'installed': False, 'runtime_validated': False,
              'stock_code_unmodified': False, 'original_lock_unchanged': False,
              'environment': {'kernel': platform.release(), 'cpus': os.cpu_count(),
                              'PATH': os.environ.get('PATH', ''), 'CARGO_BUILD_JOBS': str(args.jobs)}}
    destination = work / 'report.json'
    def save():
        destination.write_text(json.dumps(report, indent=2) + '\n')
    save()
    print(f'STOCK_REPORT={destination}', flush=True)
    with (work / 'build.log').open('x') as log:
        def run(*command, cwd=source, capture=False):
            report['commands'].append({'argv': list(command), 'cwd': str(cwd)})
            save()
            result = subprocess.run(command, cwd=cwd, env=env, check=True,
                                    stdout=subprocess.PIPE if capture else log, stderr=log)
            return result.stdout if capture else None
        try:
            run('git', 'clone', '--no-checkout', report['repository'], str(source), cwd=work)
            run('git', 'fetch', 'origin', revision)
            run('git', 'checkout', '--detach', revision)
            run('git', 'submodule', 'update', '--init', '--recursive')
            actual = run('git', 'rev-parse', 'HEAD', capture=True).decode().strip()
            if actual != revision:
                raise RuntimeError('Authentic checkout did not match the approved full SHA.')
            verify_pristine(source)
            original_lock = (source / 'Cargo.lock').read_bytes()
            (work / 'upstream-Cargo.lock').write_bytes(original_lock)
            report['original_lock_sha256'] = hashlib.sha256(original_lock).hexdigest()
            for name in ('cargo', 'rustc'):
                report['environment'][name] = run(name, '--version', capture=True).decode().strip()
            # Respect the source's own rust-toolchain file; capture actual selection.
            if (source / 'rust-toolchain.toml').exists():
                report['rust_toolchain_file'] = (source / 'rust-toolchain.toml').read_text()
            run('dpkg-checkbuilddeps')
            changelog = source / 'debian/changelog'
            old = changelog.read_text()
            (work / 'upstream-changelog').write_bytes(changelog.read_bytes())
            version, text = publication(old, args.component, revision)
            changelog.write_text(text)
            report['package_version'] = version
            # Pre-vendor strictly, so the original clean hook cannot resolve unlocked.
            config = run('cargo', 'vendor', '--locked', '--sync', 'Cargo.toml', capture=True)
            (source / '.cargo').mkdir(exist_ok=True)
            (source / '.cargo/config.toml').write_bytes(config)
            verify_lock(source, original_lock)
            verify_pristine(source)
            with tarfile.open(source / 'vendor.tar', 'w') as archive:
                archive.add(source / 'vendor', arcname='vendor')
            run('dpkg-buildpackage', '-b', '-nc', '-us', '-uc', '-j' + str(args.jobs))
            verify_lock(source, original_lock)
            verify_pristine(source)
            packages = []
            for package in sorted(work.glob('*.deb')):
                fields = run('dpkg-deb', '-f', str(package), 'Package', 'Version', 'Architecture', capture=True).decode()
                (work / (package.name + '.control.txt')).write_text(fields)
                run('dpkg-deb', '--contents', str(package))
                packages.append({'path': str(package), 'sha256': hashlib.sha256(package.read_bytes()).hexdigest(),
                                 'control': fields})
            if not any('Package: ' + args.component + '\n' in p['control'] and
                       'Version: ' + version + '\n' in p['control'] for p in packages):
                raise RuntimeError('Expected genuine source-derived binary package was not produced.')
            report.update(status='built', returncode=0, packages=packages,
                          stock_code_unmodified=True, original_lock_unchanged=True)
        except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
            report.update(status='failed', returncode=1, error=str(error))
        report['end_utc'] = datetime.now(timezone.utc).isoformat()
        save()
    print('STOCK_EXIT=' + str(report['returncode']), flush=True)
    return report['returncode']


if __name__ == '__main__':
    sys.exit(main())
