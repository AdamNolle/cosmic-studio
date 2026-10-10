#!/usr/bin/env python3
"""User-invoked Trash actions; permanent removal requires an explicit confirmation."""
from pathlib import Path
import argparse
import re
import subprocess
from trash_state import item_count, update


def launcher_actions(text, helper):
    action = 'StudioEmptyTrash'
    lines = text.splitlines()
    inside = False
    found = False
    result = []
    for line in lines:
        if line.startswith('['):
            if inside and not found:
                result.append('Actions='+action+';')
                found = True
            inside = line.strip() == '[Desktop Entry]'
        if inside and line.startswith('Actions='):
            names = [x for x in line.split('=',1)[1].split(';') if x]
            if action not in names:
                names.append(action)
            line = 'Actions='+';'.join(names)+';'
            found = True
        result.append(line)
    if inside and not found:
        result.append('Actions='+action+';')
    text='\n'.join(result)+'\n'
    section = ('[Desktop Action '+action+']\nName=Empty Trash Can\n'
               'Exec=/usr/bin/python3 "'+str(helper)+'" empty\n')
    pattern=r'(?ms)^\[Desktop Action '+action+r'\]\n.*?(?=^\[|\Z)'
    if re.search(pattern,text):
        text=re.sub(pattern,lambda _:section+'\n',text)
    else:
        text+='\n'+section
    return text.rstrip()+'\n'


def empty_trash():
    count=item_count()
    if not count:
        subprocess.run(['zenity','--info','--title=Trash','--text=Trash is already empty.'],check=False)
        return False
    confirmation=subprocess.run([
        'zenity','--question','--title=Empty Trash','--icon=user-trash-full',
        '--text=Permanently delete all items in Trash? This cannot be undone.',
        '--ok-label=Empty Trash','--cancel-label=Cancel','--default-cancel','--width=420',
    ],check=False)
    if confirmation.returncode != 0:
        return False
    result=subprocess.run(['gio','trash','--empty'],capture_output=True,text=True,check=False)
    if result.returncode:
        subprocess.run(['zenity','--error','--title=Could not empty Trash',
                        '--no-markup','--text='+result.stderr.strip()[:1500]],check=False)
        return False
    update()
    return True


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['empty'])
    parser.parse_args()
    empty_trash()
