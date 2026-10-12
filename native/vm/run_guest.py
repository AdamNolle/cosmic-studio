#!/usr/bin/env python3
"""Run owned-guest bootstrap or source checks with private stdin and retained logs.

Uses ssh-installed.conf with a previously console-verified key. No candidate
installation, desktop launch, password arguments or sudo policy changes.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shlex
import subprocess
import sys
from run_install import ROOT, clean_log, credential, private_acl


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path, help='Private VM artifact directory outside source')
    parser.add_argument('--phase', required=True, choices=('bootstrap', 'verify', 'clock', 'poweroff', 'inhibit', 'compositor', 'panel', 'core', 'media', 'media-deps', 'packaging-deps', 'stock-comp', 'stock-panel', 'os-clients', 'launcher', 'app-library', 'workspaces'))
    args = parser.parse_args()
    root = args.root.resolve()
    if platform.system() != 'Windows' or root.is_relative_to(ROOT):
        parser.error('Use the Windows host and an artifact directory outside source.')
    config = root / 'ssh-installed.conf'
    if not config.is_file():
        parser.error('Create installed-user SSH config with a console-verified host key first.')
    password = ''
    if args.phase in ('bootstrap', 'clock', 'poweroff', 'inhibit', 'media-deps', 'packaging-deps'):
        if not (root / 'guest-account.json').is_file():
            parser.error('Existing installed-account credential is required; never generate a replacement here.')
        password = credential(root, 'studio')
        if args.phase == 'clock':
            remote = shlex.join(['sudo', '-S', '-p', '', 'bash', 'cosmic-studio/native/vm/configure_clock.sh'])
        elif args.phase == 'poweroff':
            remote = shlex.join(['sudo', '-S', '-p', '', 'systemctl', '--ignore-inhibitors', 'poweroff'])
        elif args.phase == 'inhibit':
            remote = shlex.join(['sudo', '-S', '-p', '', 'systemd-run',
                '--unit=cosmic-studio-build-inhibit', '--property=Type=exec',
                'systemd-inhibit', '--what=sleep', '--mode=block', '--who=Studio-VM-build',
                '--why=owned-VM-native-builds', 'sleep', 'infinity'])
        elif args.phase == 'packaging-deps':
            remote = shlex.join(['sudo', '-S', '-p', '', 'env', 'DEBIAN_FRONTEND=noninteractive',
                'apt-get', 'install', '--no-install-recommends', '--no-upgrade', '--no-remove', '-y',
                'debhelper', 'just', 'cargo', 'rustc', 'rust-all', 'libclang-dev', 'ripgrep', 'dpkg-repack'])
        elif args.phase == 'media-deps':
            remote = shlex.join(['sudo', '-S', '-p', '', 'env', 'DEBIAN_FRONTEND=noninteractive',
                'apt-get', 'install', '--no-install-recommends', '--no-upgrade', '--no-remove', '-y',
                'nasm', 'zlib1g-dev', 'libnuma-dev'])
        else:
            remote = shlex.join(['bash', 'cosmic-studio/native/vm/bootstrap.sh', '--sudo-password-stdin'])
    elif args.phase == 'verify':
        remote = shlex.join(['bash', '-lc', 'source ~/.cargo/env && cd ~/cosmic-studio && python3 native/vm/verify_guest.py'])
    else:
        launch = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
        stock = args.phase.startswith('stock-')
        shell = args.phase in ('launcher', 'app-library', 'workspaces')
        directory = ('cosmic-studio-stock' if stock else
                     'cosmic-studio-shell' if shell else
                     'cosmic-studio-clients' if args.phase == 'os-clients' else 'cosmic-studio')
        entry = 'build_stock.py' if stock else 'build_native.py'
        component = 'cosmic-' + args.phase.removeprefix('stock-') if stock else args.phase
        jobs = 1 if stock or args.phase == 'os-clients' else (2 if shell or args.phase in ('panel', 'media') else 4)
        script = (f'source ~/.cargo/env && cd ~/{directory} && mkdir -p work/build-launch || exit 1; '
                  f'nohup python3 native/vm/{entry} --component {component} --jobs {jobs} '
                  f'>work/build-launch/{args.phase}-{launch}.log 2>&1 </dev/null & echo BUILD_PID=$!')
        remote = shlex.join(['bash', '-lc', script])
    ssh = str(Path(os.environ['SystemRoot']) / 'System32/OpenSSH/ssh.exe')
    command = [ssh, '-F', str(config), 'cosmic-studio', remote]
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    log = root / (args.phase + '-' + stamp + '.log')
    print(f'Running guest {args.phase}; private log: {log}', flush=True)
    with log.open('x', encoding='utf-8') as stream:
        private_acl(log)
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        if password:
            process.stdin.write(password.encode('ascii') + b'\n')
        process.stdin.close()
        for number, raw in enumerate(process.stdout, 1):
            line = raw.decode('utf-8', errors='replace')
            if password:
                line = clean_log(line, password)
            stream.write(line)
            stream.flush()
            if args.phase == 'verify' or any(word in line.lower() for word in
                    ('error', 'failed', 'not found', 'rustc ', 'cargo ', 'python ', 'dependencies installed', 'clock_candidate', 'build_pid')):
                print(line.strip(), flush=True)
            elif number % 150 == 0:
                print(f'{args.phase}: {number} log lines retained.', flush=True)
        result = process.wait()
    report = {'phase': args.phase, 'command': command, 'returncode': result,
              'log': log.name, 'native_build_validated': False, 'studio_runtime_validated': False}
    (root / (args.phase + '-' + stamp + '.json')).write_text(json.dumps(report, indent=2) + '\n')
    print(f'GUEST_{args.phase.upper()}_EXIT_{result}', flush=True)
    return result


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
