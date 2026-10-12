#!/usr/bin/env python3
"""Read-only, filesystem-backed icon lookup audit; never certify app rendering."""
from pathlib import Path
import argparse
import configparser
import json
import os
import shlex
import shutil

ROOT = Path(__file__).resolve().parent
ACTIVE_THEME = ROOT/'approved-dock/theme'
EXTENSIONS = {'.svg', '.png', '.xpm'}


def launcher_roots(data):
    """Return low-to-high priority roots; declared XDG order wins over fallbacks."""
    bases = [Path(p) for p in os.environ.get('XDG_DATA_DIRS', '/usr/local/share:/usr/share').split(':') if p]
    fallbacks = [Path('/var/lib/flatpak/exports/share'), data/'flatpak/exports/share']
    priority = [data] + bases + [p for p in fallbacks if p not in bases and p != data]
    unique = list(dict.fromkeys(priority))
    return [base/'applications' for base in reversed(unique)]


def launches(entry):
    """Executable availability only. env wrappers without TryExec are unassessed."""
    command = entry.get('TryExec') or entry.get('Exec', '')
    try:
        parts = shlex.split(command)
    except ValueError:
        return False
    if not parts:
        return False
    executable = parts[0]
    if not entry.get('TryExec') and Path(executable).name == 'env':
        return None
    return os.access(executable, os.X_OK) if os.path.isabs(executable) else shutil.which(executable) is not None


def theme_assets(theme):
    """Enumerate exact case-sensitive lookup names in declared theme directories.

    Never use a historical manifest membership or Windows exists(name) lookup
    as authored-coverage proof. This checks file presence, not optical quality.
    """
    theme = Path(theme)
    parser = configparser.ConfigParser(interpolation=None)
    try:
        with (theme/'index.theme').open(encoding='utf-8') as stream:
            parser.read_file(stream)
        section = parser['Icon Theme']
    except (OSError, configparser.Error, KeyError) as error:
        return {'name': theme.name, 'path': str(theme), 'assets': {}, 'inherits': [], 'errors': [str(error)]}
    assets, errors = {}, []
    directories = section.get('Directories', '').split(',') + section.get('ScaledDirectories', '').split(',')
    for declared in dict.fromkeys(p.strip() for p in directories if p.strip()):
        relative = Path(declared)
        if relative.is_absolute() or '..' in relative.parts or relative == Path('.') or '\\' in declared:
            errors.append('Unsafe declared theme directory: '+declared)
            continue
        if declared not in parser:
            errors.append('Undeclared theme section: '+declared)
            continue
        for path in sorted((theme/relative).glob('*')):
            if path.suffix.lower() in EXTENSIONS and path.is_file():
                assets.setdefault(path.stem, []).append(path.relative_to(theme).as_posix())
    return {'name': section.get('Name', theme.name), 'path': str(theme), 'assets': assets,
            'inherits': [p.strip() for p in section.get('Inherits', '').split(',') if p.strip()], 'errors': errors}


def inherited_assets(theme, search_roots):
    """Resolve declared inheritance only, without guessing from installed names."""
    names, examined, unresolved = {}, set(), []
    queue = list(theme['inherits'])
    while queue:
        name = queue.pop(0)
        if name in examined:
            continue
        examined.add(name)
        if Path(name).name != name or name in ('.', '..') or '\\' in name:
            unresolved.append(name)
            continue
        # Enumerate directory names exactly even on case-insensitive hosts.
        candidates = [p for root in search_roots if Path(root).is_dir()
                      for p in Path(root).iterdir() if p.is_dir() and p.name == name]
        if not candidates:
            unresolved.append(name)
            continue
        # Themes can be split across XDG roots; earlier roots win individual files.
        for candidate in candidates:
            index = theme_assets(candidate)
            for key, files in index['assets'].items():
                names.setdefault(key, {'theme': name, 'theme_path': str(candidate), 'files': files})
            queue.extend(index['inherits'])
    return names, unresolved


def collect(*, roots=None, theme=ACTIVE_THEME, theme_roots=None):
    data = Path(os.environ.get('XDG_DATA_HOME', Path.home()/'.local/share'))
    roots = launcher_roots(data) if roots is None else list(map(Path, roots))
    theme_roots = ([data/'icons'] + [Path(p)/'icons' for p in
                    os.environ.get('XDG_DATA_DIRS', '/usr/local/share:/usr/share').split(':') if p]
                   if theme_roots is None else list(map(Path, theme_roots)))
    index = theme_assets(theme)
    inherited, absent_themes = inherited_assets(index, theme_roots)
    apps, errors = {}, list(index['errors'])
    for root in roots:
        local = {}
        for path in sorted(root.rglob('*.desktop')):
            desktop_id = '-'.join(path.relative_to(root).parts)
            if desktop_id in local:
                errors.append('Ambiguous desktop ID: '+desktop_id+' under '+str(root))
                local[desktop_id] = None
                continue
            local[desktop_id] = path
        for desktop_id, path in local.items():
            if path is None:
                apps.pop(desktop_id, None)
                continue
            parser = configparser.ConfigParser(interpolation=None, strict=False)
            try:
                with path.open(encoding='utf-8') as stream:
                    parser.read_file(stream)
            except (OSError, UnicodeError, configparser.Error) as error:
                errors.append(str(path)+': '+str(error))
                apps.pop(desktop_id, None)
                continue
            if 'Desktop Entry' not in parser:
                continue
            entry = parser['Desktop Entry']
            if entry.get('Hidden', '').casefold() == 'true' or entry.get('NoDisplay', '').casefold() == 'true':
                apps.pop(desktop_id, None)
                continue
            if entry.get('Type', 'Application') != 'Application':
                apps.pop(desktop_id, None)
                continue
            apps[desktop_id] = {'name': entry.get('Name', desktop_id), 'icon': entry.get('Icon', ''),
                                'desktop_id': desktop_id, 'source': str(path), 'launchable': launches(entry)}
    rows = []
    for entry in apps.values():
        row = dict(entry)
        icon = entry['icon']
        if os.path.isabs(icon):
            row.update(status='absolute-path override needed', authored_files=[],
                       absolute_asset_present=Path(icon).is_file())
        elif icon in index['assets']:
            row.update(status='custom', authored_files=index['assets'][icon])
        elif icon in inherited:
            row.update(status='inherited-resolved', inherited_asset=inherited[icon], authored_files=[])
        else:
            row.update(status='unresolved', authored_files=[])
        rows.append(row)
    sort = lambda items: sorted(items, key=lambda row: (row['name'].casefold(), row['desktop_id']))
    return {'schema': 2, 'scope': 'Observed launcher lookups against the selected theme tree, not installed-theme or runtime proof',
            'theme': index, 'missing_inherited_themes': absent_themes, 'inventory_errors': errors,
            'applications': sort(rows), 'missing': sort([r for r in rows if r['status'] != 'custom']),
            'stale_launchers': sort([r for r in rows if r['launchable'] is False]),
            'unassessed_launchers': sort([r for r in rows if r['launchable'] is None]),
            'summary': {'launchers': len(rows), 'launchable_launchers': sum(r['launchable'] is True for r in rows),
                        'custom_launchers': sum(r['status'] == 'custom' for r in rows),
                        'custom_launchable_launchers': sum(r['status'] == 'custom' and r['launchable'] is True for r in rows),
                        'absolute_path_launchers': sum(r['status'].startswith('absolute') for r in rows),
                        'unresolved_launchers': sum(r['status'] == 'unresolved' for r in rows),
                        'inherited_resolved_launchers': sum(r['status'] == 'inherited-resolved' for r in rows),
                        'unassessed_launchers': sum(r['launchable'] is None for r in rows),
                        'authored_lookup_names': len(index['assets'])},
            'complete': False, 'installed_theme_verified': False,
            'launchers_complete': bool(rows) and not errors and all(r['status'] == 'custom' for r in rows),
            'limits': ['Historical coverage.json belongs to the inactive Studio Objects study and is not used.',
                       'Authored lookup means an exact named file exists, not approved optics at every size.',
                       'Selected repository theme assets are not evidence of installation or toolkit selection.',
                       'Theme lookups are not a census of embedded resources, action icons, MIME icons or favicons.',
                       'Inherited and absolute assets are never counted as authored coverage.',
                       'Executable availability/TryExec does not demonstrate application startup.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local-report', type=Path)
    parser.add_argument('--theme', type=Path, default=ACTIVE_THEME)
    args = parser.parse_args()
    report = collect(theme=args.theme)
    if args.local_report:
        with args.local_report.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, indent=2)
            stream.write('\n')
    print(json.dumps(report['summary'], indent=2))
