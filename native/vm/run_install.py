#!/usr/bin/env python3
"""Windows driver for a guarded distinst run; credentials stay outside source and argv.

First copy install_guest.py to the verified live guest's home. This driver always
runs its read-only preflight again. Formatting additionally requires --install.
"""
import argparse
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import secrets
import shlex
import string
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')


def private_acl(path):
    system = Path(os.environ['SystemRoot']) / 'System32'
    who = subprocess.check_output([str(system / 'whoami.exe'), '/user', '/fo', 'csv', '/nh'], text=True)
    sid = next(csv.reader(who.strip().splitlines()))[1]
    subprocess.run([str(system / 'icacls.exe'), str(path), '/inheritance:r', '/grant:r',
                    '*' + sid + ':(F)', '/grant:r', '*S-1-5-18:(F)'],
                   check=True, stdout=subprocess.DEVNULL)


def credential(root, username):
    path = root / 'guest-account.json'
    if path.exists():
        data = json.loads(path.read_text())
        if data.get('username') != username:
            raise ValueError('Existing credential belongs to a different guest account; refusing overwrite.')
    else:
        alphabet = string.ascii_letters + string.digits
        data = {'username': username, 'password': ''.join(secrets.choice(alphabet) for _ in range(24)),
                'purpose': 'Dedicated local COSMIC Studio development VM account'}
        with path.open('x', encoding='utf-8') as stream:
            json.dump(data, stream, indent=2)
            stream.write('\n')
    private_acl(path)
    password = data['password']
    if not isinstance(password, str) or len(password) < 20 or not password.isascii() or not password.isalnum():
        raise ValueError('Expected a generated high-entropy alphanumeric development password.')
    return password


def clean_log(line, password):
    line = ANSI.sub('', line).replace(password, '[REDACTED]')
    if 'password' in line.lower() or 'passwd' in line.lower():
        return '[credential-related installer log redacted]\n'
    return line


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True, help='Private VM artifacts directory outside source')
    parser.add_argument('--expected-serial', required=True)
    parser.add_argument('--expected-bytes', type=int, required=True)
    parser.add_argument('--iso-root', required=True)
    parser.add_argument('--username', default='studio')
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    if platform.system() != 'Windows':
        parser.error('Use this host driver on Windows.')
    root = args.root.resolve()
    if root.is_relative_to(ROOT):
        parser.error('Credentials and installer logs must remain outside the repository.')
    config = root / 'ssh-live.conf'
    if not config.is_file():
        parser.error('Create a dedicated SSH configuration with a console-verified host key first.')
    ssh = str(Path(os.environ['SystemRoot']) / 'System32/OpenSSH/ssh.exe')
    base = [ssh, '-F', str(config), 'cosmic-studio-live']
    guest = ['sudo', '-n', 'python3', 'install_guest.py', '--device', '/dev/sda',
             '--expected-serial', args.expected_serial, '--expected-bytes', str(args.expected_bytes),
             '--iso-root', args.iso_root, '--username', args.username]
    subprocess.run([*base, shlex.join(guest)], stdin=subprocess.DEVNULL, check=True)
    if not args.install:
        return 0
    password = credential(root, args.username)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    log = root / ('distinst-' + stamp + '.log')
    success_marker = False
    print('Starting explicitly approved empty-VM-disk installation. Password is sent only via private stdin.', flush=True)
    with log.open('x', encoding='utf-8') as stream:
        private_acl(log)
        process = subprocess.Popen([*base, shlex.join([*guest, '--install'])], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # Binary stdin preserves LF on Windows. CRLF would become part of the
        # password because distinst removes exactly one trailing character.
        process.stdin.write(password.encode('ascii') + b'\n')
        process.stdin.close()
        for count, raw_line in enumerate(process.stdout, 1):
            line = clean_log(raw_line.decode('utf-8', errors='replace'), password)
            stream.write(line)
            stream.flush()
            success_marker |= line.strip() == 'DISTINST_INSTALL_SUCCEEDED'
            if any(word in line.lower() for word in ('stage', 'error', 'failed', 'succeeded', 'validated')):
                print(line.strip(), flush=True)
            elif count % 100 == 0:
                print(f'Guest installer: {count} log lines retained.', flush=True)
        result = process.wait()
    passed = result == 0 and success_marker
    report = {'phase': 'distinst-only', 'returncode': result, 'install_command_succeeded': passed,
              'first_boot_validated': False, 'desktop_validated': False, 'log': log.name}
    (root / ('distinst-' + stamp + '.json')).write_text(json.dumps(report, indent=2) + '\n')
    print(f'Installer log (credential-redacted): {log}', flush=True)
    print('DISTINST_RUN_SUCCEEDED_BOOT_PENDING' if passed else 'DISTINST_RUN_FAILED_INSPECT_LOG', flush=True)
    return 0 if passed else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
