#!/usr/bin/env python3
"""Guard an official distinst install onto an explicitly identified EMPTY VirtualBox disk.

Read-only by default. --install requires root in the Pop!_OS live guest and a private
password pipe on stdin. Never pass account passwords on the command line.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import shlex
import stat
import subprocess
import sys

GIB = 1024 ** 3


def validate_disk(record, device, expected_serial, expected_bytes):
    if not expected_serial or not 32 * GIB <= expected_bytes <= 512 * GIB:
        raise ValueError('An explicit serial and supported expected disk size are required.')
    if record.get('path') != device or record.get('type') != 'disk':
        raise ValueError('Select the expected whole disk, not a partition or another device.')
    if str(record.get('model', '')).strip() != 'VBOX HARDDISK':
        raise ValueError('Target is not a VirtualBox hard disk.')
    if str(record.get('serial', '')).strip() != expected_serial:
        raise ValueError('Disk serial differs from the explicitly selected new VM disk.')
    if int(record.get('size', 0)) != expected_bytes or record.get('ro') not in (False, 0, '0'):
        raise ValueError('Disk size or write capability differs from the approved target.')
    if record.get('children'):
        raise ValueError('Refusing a disk that already has partitions or dependent devices.')


def output(*args):
    return subprocess.check_output(args, text=True).strip()


def check_context():
    if platform.system() != 'Linux' or os.geteuid() != 0:
        raise ValueError('Run with sudo inside the disposable Linux live guest, never on Windows.')
    if output('systemd-detect-virt') != 'oracle':
        raise ValueError('This installer is restricted to VirtualBox guests.')
    release = dict(line.split('=', 1) for line in Path('/etc/os-release').read_text().splitlines() if '=' in line)
    if release.get('ID', '').strip('"') != 'pop' or release.get('VERSION_ID', '').strip('"') != '24.04':
        raise ValueError('The supported Pop!_OS 24.04 live image is required.')
    if output('findmnt', '-n', '-o', 'FSTYPE', '--target', '/') not in ('overlay', 'aufs'):
        raise ValueError('Refusing to install from an existing installed OS; use the live ISO.')


def prepare(device, expected_serial, expected_bytes, iso_root, username):
    check_context()
    if not device.startswith('/dev/') or str(Path(device).resolve()) != device:
        raise ValueError('Supply the canonical /dev/ whole-disk path, not a symlink.')
    if not stat.S_ISBLK(Path(device).stat().st_mode):
        raise ValueError('Target must be an actual block device.')
    probe = json.loads(output('lsblk', '--bytes', '--json', '-o', 'PATH,SIZE,TYPE,MODEL,SERIAL,RO', device))
    records = probe.get('blockdevices', [])
    if len(records) != 1:
        raise ValueError('Expected exactly one selected target disk.')
    validate_disk(records[0], device, expected_serial, expected_bytes)
    if output('wipefs', '--no-act', '--noheadings', '--output', 'TYPE', device):
        raise ValueError('Refusing a disk with any existing filesystem/partition signature.')
    iso_root = iso_root.resolve()
    if not iso_root.is_relative_to('/cdrom') or iso_root == Path('/cdrom'):
        raise ValueError('Select the verified ISO casper directory under /cdrom.')
    if output('findmnt', '-n', '-o', 'FSTYPE', '--target', str(iso_root)) != 'iso9660':
        raise ValueError('Installation files must be on the attached read-only ISO.')
    squashfs = iso_root / 'filesystem.squashfs'
    remove = iso_root / 'filesystem.manifest-remove'
    if not squashfs.is_file() or not remove.is_file():
        raise ValueError('The official squashfs and package-removal manifest are required.')
    if not username.isascii() or not username.islower() or not username.replace('-', '').isalnum() or username in ('root', 'pop-os'):
        raise ValueError('Use a dedicated non-root development account name.')
    icons = [Path('/usr/share/pixmaps/faces/penguin.png'),
             Path('/usr/share/icons/gnome/256x256/status/avatar-default.png'),
             Path('/usr/share/icons/HighContrast/256x256/status/avatar-default.png')]
    icon = next((path for path in icons if path.is_file()), None)
    if icon is None:
        raise ValueError('A supported native PNG profile icon is absent; inspect the live image.')
    if not Path('/sys/firmware/efi').is_dir():
        raise ValueError('The VM must be booted in EFI mode.')
    # EFI ends at 1024 MB, plus root and 8192 MB swap (distinst M is decimal).
    # The verified ISO remains a recovery option.
    return ['distinst', '-s', str(squashfs), '-r', str(remove), '-h', 'cosmic-studio',
            '-k', 'us', '-l', 'en_US.UTF-8', '-b', device, '-t', device + ':gpt',
            '-n', device + ':primary:start:1024M:fat32:mount=/boot/efi:flags=esp',
            '-n', device + ':primary:1024M:-8192M:ext4:mount=/',
            '-n', device + ':primary:-8192M:end:swap', '--username', username,
            '--realname', 'COSMIC Studio Developer', '--profile_icon', str(icon), '--tz', 'Etc/UTC']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', required=True)
    parser.add_argument('--expected-serial', required=True)
    parser.add_argument('--expected-bytes', required=True, type=int)
    parser.add_argument('--iso-root', required=True, type=Path)
    parser.add_argument('--username', default='studio')
    parser.add_argument('--install', action='store_true', help='Explicitly permit formatting the validated empty disk')
    args = parser.parse_args()
    try:
        command = prepare(args.device, args.expected_serial, args.expected_bytes, args.iso_root, args.username)
        print('EMPTY_VM_DISK_AND_LIVE_ISO_VALIDATED', flush=True)
        print(shlex.join(command), flush=True)
        if args.install:
            if sys.stdin.isatty():
                raise ValueError('Supply the new account password over a private stdin pipe, not a terminal or argv.')
            subprocess.run(command, check=True)
            print('DISTINST_INSTALL_SUCCEEDED', flush=True)
        else:
            print('READ_ONLY_PREFLIGHT_PASSED: no partitioning, formatting or installation performed.', flush=True)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, str(error) + '\n')
