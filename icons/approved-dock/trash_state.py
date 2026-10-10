#!/usr/bin/env python3
"""Keep the COSMIC Trash launcher in sync without touching any trashed files."""
from pathlib import Path
import os
import re
import subprocess
import tempfile


def icon_line(text, name):
    """Edit only Desktop Entry/Icon, retaining launcher actions and formatting."""
    lines = text.splitlines(keepends=True)
    inside = False
    found = False
    end = None
    result = []
    for line in lines:
        if line.strip().startswith('['):
            if inside and not found:
                result.append('Icon=' + name + '\n')
                found = True
            inside = line.strip() == '[Desktop Entry]'
        if inside and re.match(r'^Icon\s*=', line):
            line = 'Icon=' + name + ('\n' if line.endswith('\n') else '')
            found = True
        result.append(line)
    if inside and not found:
        if result and not result[-1].endswith('\n'):
            result[-1] += '\n'
        result.append('Icon=' + name + '\n')
    return ''.join(result)


def item_count():
    result = subprocess.run(['gio', 'info', 'trash:///', '-a', 'trash::item-count'],
                            text=True, capture_output=True, timeout=10)
    match = re.search(r'trash::item-count:\s*(\d+)', result.stdout)
    if result.returncode or not match:
        raise RuntimeError('Trash count unavailable; retaining the current icon.')
    return int(match.group(1))


def desired_icon(count):
    return 'user-trash-full' if count else 'user-trash'


def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def update(path=None):
    if path is None:
        data = Path(os.environ.get('XDG_DATA_HOME', Path.home()/'.local/share'))
        path = data/'applications/local-trash.desktop'
    path = Path(path)
    if not path.is_file():
        raise RuntimeError('Trash launcher is missing; no launcher was created.')
    count = item_count()
    before = path.read_text()
    after = icon_line(before, desired_icon(count))
    if after != before:
        atomic_write(path, after.encode())
    return desired_icon(count)


if __name__ == '__main__':
    try:
        print(update())
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        print(error)
