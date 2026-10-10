#!/usr/bin/env python3
"""Read-only unchanged-Flatpak checks for a separately authorized staged ELF.

Without --instance this validates only the captured permissions/runtime/ref and
launcher substitution. It never stages files, installs SDKs, changes permissions,
launches an app, restarts an instance or writes a desktop launcher.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess


def output(args):
    return subprocess.check_output(args, text=True)


def validate_baseline(app):
    identifier = app['flatpak_id']
    current = {
        'effective_permissions': output(['flatpak', 'info', '--show-permissions', identifier]),
        'runtime': output(['flatpak', 'info', '--show-runtime', identifier]).strip(),
        'ostree_commit': output(['flatpak', 'info', '--show-commit', identifier]).strip(),
    }
    for key, value in current.items():
        if value != app[key]:
            raise ValueError('Installed '+identifier+' differs from baseline: '+key)
    reference = output(['flatpak', 'info', '--show-ref', identifier]).strip()
    if reference != f"app/{identifier}/{app['arch']}/{app['branch']}":
        raise ValueError('Installed branch/architecture differs from baseline.')
    before, after = app['original_launch_argv'], app['proposed_launch_argv']
    differences = [(x, y) for x, y in zip(before, after) if x != y]
    if len(before) != len(after) or differences != [('--command='+app['command'], '--command='+app['sandbox_command_path'])]:
        raise ValueError('Candidate launcher changes something besides the command path.')
    if Path(app['host_stage_path']) != Path(app['sandbox_command_path']):
        raise ValueError('Candidate must use the existing identical app-private cache mount.')
    expected = Path.home()/'.var/app'/identifier/'cache/cosmic-studio'/app['command']
    if Path(app['host_stage_path']) != expected:
        raise ValueError('Unexpected candidate staging path; no additional filesystem grants allowed.')
    return current


def check_candidate(app, instance):
    path = Path(app['host_stage_path'])
    if not path.is_file():
        raise ValueError('A separately authorized compiled ELF must already be staged at the exact app-private path.')
    with path.open('rb') as file:
        if file.read(4) != b'\x7fELF':
            raise ValueError('Staged candidate must be a compiled ELF.')
    rows = output(['flatpak', 'ps', '--columns=instance,application']).splitlines()
    if not any(row.split() == [instance, app['flatpak_id']] for row in rows):
        raise ValueError('Instance does not belong to the unchanged existing app ID.')
    command = ['flatpak', 'enter', instance, '/usr/bin/ldd', '-r', app['sandbox_command_path']]
    result = subprocess.run(command, capture_output=True, text=True)
    combined = result.stdout+result.stderr
    if result.returncode or re.search(r'not found|undefined symbol|version .+ not found', combined):
        raise ValueError('Candidate does not resolve in the unchanged runtime:\n'+combined)
    return {'command': command, 'ldd_r': combined, 'runtime_symbols_resolved': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('--app-id', required=True)
    parser.add_argument('--instance', help='Existing instance of the same unchanged app; enables staged candidate ldd -r')
    args = parser.parse_args()
    document = json.loads(args.baseline.read_text())
    matches = [a for a in document['applets'] if a['flatpak_id'] == args.app_id]
    if len(matches) != 1:
        raise ValueError('Choose exactly one captured installed app ID.')
    app = matches[0]
    report = {'flatpak_id': args.app_id, 'baseline': validate_baseline(app), 'permission_changes': False, 'app_launched': False}
    if args.instance:
        report['candidate'] = check_candidate(app, args.instance)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
