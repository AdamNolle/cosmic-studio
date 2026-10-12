#!/usr/bin/env python3
"""Retain an actual native build's command, environment, output and exit status. No deployment."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--component', choices=['compositor', 'panel', 'core', 'os-clients', 'media', 'launcher', 'app-library', 'workspaces'], required=True)
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    if platform.system() != 'Linux' or os.geteuid() == 0:
        parser.error('Run as the normal development user inside Linux, not root.')
    if not 1 <= args.jobs <= 24:
        parser.error('Jobs must be between 1 and 24.')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    work = ROOT / 'work/native-builds' / (args.component + '-' + stamp)
    work.mkdir(parents=True)
    commands = {
        'compositor': [sys.executable, 'native/compositor/build.py'],
        'panel': [sys.executable, 'native/build_shell.py', 'cosmic-panel'],
        'launcher': [sys.executable, 'native/build_shell.py', 'cosmic-launcher'],
        'app-library': [sys.executable, 'native/build_shell.py', 'cosmic-app-library'],
        'workspaces': [sys.executable, 'native/build_shell.py', 'cosmic-workspaces'],
        'core': [sys.executable, 'native/typography/build_core_apps.py'],
        'os-clients': [sys.executable, 'native/typography/build_os_clients.py',
                       '--components', 'cosmic-applets', 'cosmic-notifications', 'cosmic-osd',
                       'cosmic-store', 'cosmic-monitor', 'cosmic-osk'],
        'media': [sys.executable, 'native/typography/build_os_clients.py',
                  '--components', 'cosmic-player', 'cosmic-viewer'],
    }
    command = commands[args.component] + ['--work', str(work / 'sources'), '--jobs', str(args.jobs)]
    def version(*command):
        return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).strip()
    manifest = work / 'studio-source-manifest.json'
    manifest.write_bytes((ROOT / 'studio-source-manifest.json').read_bytes())
    report = {'schema': 1, 'component': args.component, 'command': command, 'cwd': str(ROOT),
              'start_utc': stamp, 'status': 'running', 'uid': os.geteuid(),
              'environment': {'kernel': platform.release(), 'machine': platform.machine(),
                              'cpus': os.cpu_count(), 'python': sys.version,
                              'rustc': version('rustc', '+stable', '--version'),
                              'cargo': version('cargo', '+stable', '--version'),
                              'PATH': os.environ.get('PATH', ''),
                              'cargo_overrides': {k: v for k, v in os.environ.items()
                                if k.startswith(('CARGO_PROFILE_', 'RUSTFLAGS'))}},
              'source_manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
              'source_manifest': str(manifest), 'log': str(work / 'build.log'),
              'installed': False, 'runtime_validated': False}
    destination = work / 'report.json'
    def save():
        destination.write_text(json.dumps(report, indent=2) + '\n')
    save()
    print(f'BUILD_REPORT={destination}', flush=True)
    with (work / 'build.log').open('x') as stream:
        result = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
    report.update(returncode=result.returncode, status='built' if result.returncode == 0 else 'failed',
                  end_utc=datetime.now(timezone.utc).isoformat())
    save()
    print(f'BUILD_EXIT={result.returncode}', flush=True)
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
