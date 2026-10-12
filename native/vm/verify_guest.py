#!/usr/bin/env python3
"""Run isolated Linux source/recovery checks and retain rerunnable local reports.

This does not install candidates, launch apps, manipulate user windows or test GPU performance.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SUITES = [
    ('setup', 'tests', 'test*.py'),
    ('native', 'native/tests', 'test*.py'),
    ('popups', 'native/popups/tests', 'test*.py'),
    ('icons', 'icons/tests', 'test*.py'),
    ('approved-dock', 'icons/approved-dock', 'test*.py'),
    ('compact-dock', 'native/dock-icons', 'test*.py'),
    ('thirdparty-build', 'native/thirdparty', 'test*.py'),
    ('panel-focus', 'native/panel', 'test*.py'),
    ('vm-tooling', 'native/vm', 'test*.py'),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reports', type=Path, default=ROOT / 'work/vm-validation')
    args = parser.parse_args()
    if platform.system() != 'Linux':
        parser.error('Run full recovery checks inside Linux. Windows: unittest discover -s native/vm -p test*.py.')
    missing = [tool for tool in ('git', 'rustc', 'fc-cache', 'fc-match', 'sh') if not shutil.which(tool)]
    if missing:
        parser.error('Missing verification dependencies: ' + ', '.join(missing))
    reports = args.reports.resolve() / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    reports.mkdir(parents=True)
    summary = {'schema': 1, 'kind': 'source-and-recovery-only', 'python': platform.python_version(), 'suites': []}
    failed = False
    for name, directory, pattern in SUITES:
        command = [sys.executable, '-m', 'unittest', 'discover', '-s', directory, '-p', pattern, '-v']
        result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        log = reports / (name + '.log')
        log.write_text(result.stdout, encoding='utf-8')
        count = re.search(r'Ran (\d+) tests?', result.stdout)
        skipped = re.findall(r"\.\.\. skipped (.+)", result.stdout)
        passed = result.returncode == 0 and count is not None and int(count.group(1)) > 0
        failed |= not passed
        summary['suites'].append({'name': name, 'command': command, 'returncode': result.returncode,
                                  'tests': int(count.group(1)) if count else 0, 'skipped': skipped, 'passed': passed})
        print(f"{name}: {'PASS' if passed else 'FAIL'}; {count.group(1) if count else 0} tests; {len(skipped)} skips; {log}", flush=True)
    command = [sys.executable, '-m', 'compileall', '-q', 'setup.py', 'native', 'icons']
    result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    (reports / 'compileall.log').write_text(result.stdout, encoding='utf-8')
    summary['compileall'] = {'command': command, 'returncode': result.returncode}
    failed |= result.returncode != 0
    summary['passed'] = not failed
    summary['runtime_validated'] = False
    (reports / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(f'Source/recovery summary: {reports / "summary.json"}')
    print('Native compilation, visible desktop behavior, authentication and performance remain separate gates.')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
