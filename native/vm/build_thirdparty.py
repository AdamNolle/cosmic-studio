#!/usr/bin/env python3
"""Prepare/build the four reviewed applets in fresh isolated sources; never deploy.

No Flatpak installation, permission override or candidate launch is performed.
Host ELF compilation does not satisfy the separately required unchanged-runtime gate.
"""
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

ROOT = Path(__file__).resolve().parents[2]
REPOSITORIES = {
    'caffeine': 'https://github.com/codevardhan/caffeine-applet.git',
    'brightness': 'https://github.com/cosmic-utils/cosmic-ext-applet-external-monitor-brightness.git',
    'sysinfo': 'https://github.com/cosmic-utils/cosmic-ext-applet-sysinfo.git',
    'status-hub': 'https://github.com/marcelogomes90/cosmic-ext-applet-status-hub.git',
}


def selected_profiles(requested):
    profiles = tuple(REPOSITORIES) if requested is None else tuple(requested)
    if not profiles or len(set(profiles)) != len(profiles) or any(p not in REPOSITORIES for p in profiles):
        raise ValueError('Select distinct reviewed applet profiles only.')
    return profiles


def profile_options(profiles):
    return [argument for profile in profiles for argument in ('--profile', profile)]


def preflight():
    if platform.system() != 'Linux' or os.geteuid() == 0:
        raise ValueError('Run as the normal Linux development user, never root.')
    if any(k.startswith(('CARGO_PROFILE_', 'CARGO_TARGET_', 'RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS'))
           or k in ('RUSTUP_TOOLCHAIN', 'LD_LIBRARY_PATH', 'LIBRARY_PATH', 'PKG_CONFIG_PATH')
           for k in os.environ):
        raise ValueError('Unset caller compiler/profile/library overrides before preparing/building.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs', type=int, default=1)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--profile', choices=REPOSITORIES, action='append',
                        help='Prepare/build only explicit reviewed profiles; default retains all four.')
    args = parser.parse_args()
    profiles = selected_profiles(args.profile)
    preflight()
    if not 1 <= args.jobs <= 3:
        parser.error('Use 1–3 bounded jobs.')
    spec = importlib.util.spec_from_file_location('thirdparty_pins', ROOT/'native/thirdparty/prepare_build.py')
    pins = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pins)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    work = ROOT/'work/thirdparty-builds'/stamp
    work.mkdir(parents=True, exist_ok=False)
    sources, patches = work/'sources', work/'patches'
    sources.mkdir()
    patches.mkdir()
    manifest = work/'studio-source-manifest.json'
    shutil.copy2(ROOT/'studio-source-manifest.json', manifest)
    shutil.copy2(Path(__file__), work/'executed-builder.py')
    report = {'schema': 1, 'status': 'running', 'start_utc': stamp, 'uid': os.geteuid(),
              'cwd': str(ROOT), 'kernel': platform.release(), 'cpus': os.cpu_count(),
              'PATH': os.environ.get('PATH'), 'jobs': args.jobs, 'commands': [],
              'pins': pins.PROFILES, 'repositories': REPOSITORIES, 'selected_profiles': profiles,
              'source_manifest_sha256': pins.digest(manifest), 'sources': str(sources),
              'installed': False, 'runtime_validated': False, 'sandbox_permissions_changed': False}
    def save():
        (work/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    save()
    print('THIRDPARTY_REPORT='+str(work/'report.json'), flush=True)
    with (work/'build.log').open('x') as log:
        def run(command, cwd=ROOT):
            command = [str(a) for a in command]
            item = {'command': command, 'cwd': str(cwd), 'start_utc': datetime.now(timezone.utc).isoformat()}
            report['commands'].append(item)
            save()
            print(json.dumps(item), file=log, flush=True)
            result = subprocess.run(command, cwd=cwd, stdout=log, stderr=subprocess.STDOUT)
            item.update(returncode=result.returncode, end_utc=datetime.now(timezone.utc).isoformat())
            save()
            if result.returncode:
                raise subprocess.CalledProcessError(result.returncode, command)
        def clone(repository, revision, folder):
            if folder.exists():
                raise FileExistsError('Refusing existing source: '+str(folder))
            run(['git', 'clone', '--no-checkout', repository, folder])
            run(['git', 'fetch', 'origin', revision], folder)
            run(['git', 'checkout', '--detach', revision], folder)
            actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=folder, text=True).strip()
            if actual != revision:
                raise ValueError('Exact source revision mismatch.')
            run(['git', 'submodule', 'update', '--init', '--recursive'], folder)
            status = subprocess.check_output(['git', 'submodule', 'status', '--recursive'], cwd=folder, text=True)
            if any(line[:1] in ('-', '+', 'U') for line in status.splitlines()):
                raise ValueError('Unverified pinned submodule.')
            (work/(folder.name+'.submodules.txt')).write_text(status)
        try:
            run(['rustc', '--version'])
            run(['cargo', '--version'])
            for profile in profiles:
                app_pin, lib_pin = pins.PROFILES[profile]
                print('Preparing '+profile, flush=True)
                app, lib = sources/('app-'+profile+'-native'), sources/('library-'+profile+'-native')
                clone(REPOSITORIES[profile], app_pin, app)
                clone('https://github.com/pop-os/libcosmic.git', lib_pin, lib)
                lock = subprocess.check_output(['git', 'show', 'HEAD:Cargo.lock'], cwd=app)
                (work/(profile+'-upstream-Cargo.lock')).write_bytes(lock)
                run([sys.executable, 'native/typography/patch_libcosmic.py', lib, '--output', patches/(profile+'-typography.patch')])
                run(['git', 'apply', '--check', patches/(profile+'-typography.patch')], lib)
                run(['git', 'apply', patches/(profile+'-typography.patch')], lib)
                run([sys.executable, 'native/typography/embed_fonts.py', lib, '--output', patches/(profile+'-fonts.patch'), '--apply'])
                run([sys.executable, 'native/typography/prepare_display_roles.py', lib, '--profile', 'native-'+lib_pin[:8], '--output', patches/(profile+'-roles.patch'), '--apply'])
                if profile == 'caffeine':
                    run([sys.executable, 'native/thirdparty/prepare_caffeine_blur.py', lib/'iced', '--apply'])
                    material = 'native/popups/legacy/caffeine.py'
                    options = []
                else:
                    material = 'native/popups/prepare.py'
                    options = ['--revision', lib_pin]
                run([sys.executable, material, lib, *options, '--output', patches/(profile+'-materials.patch'), '--apply'])
                if profile in ('brightness', 'sysinfo'):
                    run([sys.executable, 'native/thirdparty/prepare_routes.py', app, '--profile', profile, '--output', patches/(profile+'-routes.patch'), '--apply'])
                if profile == 'brightness':
                    run([sys.executable, 'native/thirdparty/prepare_brightness_batch.py', app,
                         '--output', patches/'brightness-batch.patch', '--apply'])
                if profile == 'sysinfo':
                    run([sys.executable, 'native/thirdparty/prepare_sysinfo_rates.py', app,
                         '--output', patches/'sysinfo-rates.patch', '--apply'])
                run([sys.executable, 'native/thirdparty/prepare_build.py', '--app', app, '--library', lib, '--profile', profile])
                run(['git', 'diff', '--check'], app)
                run(['git', 'diff', '--check'], lib)
                report.setdefault('prepared', []).append(profile)
                save()
            if not args.prepare_only:
                run([sys.executable, 'native/thirdparty/build.py', '--sources', sources, '--target', work/'target', '--artifacts', work/'artifacts', '--jobs', args.jobs, *profile_options(profiles)])
            report.update(status='prepared' if args.prepare_only else 'built', returncode=0)
        except Exception as error:
            report.update(status='failed', returncode=getattr(error, 'returncode', 1), error=str(error))
        finally:
            report['end_utc'] = datetime.now(timezone.utc).isoformat()
            save()
    print('THIRDPARTY_EXIT='+str(report['returncode']), flush=True)
    return report['returncode']


if __name__ == '__main__':
    sys.exit(main())
