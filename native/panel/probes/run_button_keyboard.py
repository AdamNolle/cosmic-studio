#!/usr/bin/env python3
"""Diagnostic against the already compiled, reviewed iteration32 SDK; never build/install a desktop."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

PANEL = 'b5cc19e351b82eed999097ced1ff267d27bf8e7a'
SDK = '23f5d63fed2a370f3c2f54b90ec8f0896fe82105'
WIDGET_SHA = 'e1542a78f5739904dd5f3656c8cf46c94a2455f6985f101622ff6e6a77b0f2c0'
ROOT_NAME = 'cosmic-studio-panel-wrapper-reviewed-iteration32'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def contained(path, root):
    if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Escaped/symlink diagnostic input refused.')
    return path

def run(build_root, output):
    if os.getuid() != 1000:
        raise ValueError('Original non-root studio UID required.')
    for name in os.environ:
        if name in ('LD_PRELOAD', 'LD_LIBRARY_PATH', 'RUSTFLAGS', 'RUSTC_WRAPPER', 'CARGO_ENCODED_RUSTFLAGS',
                    'CARGO_TARGET_DIR', 'RUSTUP_TOOLCHAIN', 'RUSTC', 'CARGO_BUILD_RUSTC',
                    'CARGO_BUILD_RUSTFLAGS', 'CARGO_BUILD_RUSTC_WRAPPER') or name.startswith('CARGO_PROFILE_'):
            raise ValueError('Compiler/library/profile override refused: ' + name)
    build_root = Path(build_root)
    parent = Path('/mnt/cosmic-studio-builds/studio')
    contained(build_root, parent)
    if build_root.name != ROOT_NAME or build_root.parent != parent:
        raise ValueError('Only preserved reviewed iteration32 root accepted.')
    if not parent.parent.is_mount() or shutil.disk_usage('/').free <= 10 * 1024**3:
        raise ValueError('Mounted approved volume/root headroom required.')
    volume = json.loads((parent.parent/'build-volume-provenance.json').read_text())
    if (volume['filesystem_uuid'], volume['host_medium_uuid']) != ('8cc60e47-3725-44b2-a9a1-42294265f707', 'b58f2faf-94a5-4ca5-8108-5f01407eedd1'):
        raise ValueError('Changed approved volume identity.')
    active = subprocess.check_output(['ps', '-eo', 'comm'], text=True).splitlines()
    if any(p.strip() in ('cargo', 'rustc', 'rust-lld') for p in active):
        raise ValueError('Active compiler refused.')
    driver = build_root/'work/iteration-32-reviewed-driver'
    report32 = json.loads((driver/'report.json').read_text())
    if len(report32['phases']) != 8 or any(p['returncode'] for p in report32['phases']) or not report32['source_inputs_unchanged']:
        raise ValueError('Successful complete prior native driver required.')
    runs = list((build_root/'work/native-builds').glob('panel-*'))
    if len(runs) != 1:
        raise ValueError('Unique reviewed panel build required.')
    source = runs[0]/'sources/cosmic-panel'
    sdk = source.parent/'libcosmic-23f5d63'
    for root, pin in ((source, PANEL), (sdk, SDK)):
        if subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip() != pin:
            raise ValueError('Exact prior source HEAD required.')
    widget = sdk/'src/widget/button/widget.rs'
    if sha(widget) != WIDGET_SHA or subprocess.check_output(['git','-C',str(sdk),'show','HEAD:src/widget/button/widget.rs']) != widget.read_bytes():
        raise ValueError('Actual original SDK widget differs.')
    # Validate all prior app/SDK inventory files without touching the trees.
    inventory = json.loads((driver/'source-inputs-after.json').read_text())
    def validate_source_inputs():
        for name, digest in inventory.items():
            label, relative = name.split('/', 1)
            if label not in ('panel', 'sdk'):
                raise ValueError('Unknown prior source inventory namespace.')
            tree = source if label == 'panel' else sdk
            path = contained(tree/relative, tree)
            if sha(path) != digest:
                raise ValueError('Prior reviewed input drift: ' + name)
    validate_source_inputs()
    metadata = json.loads((driver/'panel-metadata.json').read_text())
    packages = [p for p in metadata['packages'] if Path(p['manifest_path']) == sdk/'Cargo.toml']
    if len(packages) != 1:
        raise ValueError('Exact local SDK metadata package required.')
    package = packages[0]
    features = next(n['features'] for n in metadata['resolve']['nodes'] if n['id'] == package['id'])
    artifacts = []
    for line in (driver/'panel-app-test-build.log').read_text().splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get('reason') == 'compiler-artifact' and row.get('package_id') == package['id'] and row['target']['kind'] == ['lib']:
            artifacts.append(row)
    if len(artifacts) != 1 or sorted(artifacts[0]['features']) != sorted(features):
        raise ValueError('Exact prior SDK compiler feature artifact required.')
    artifact = artifacts[0]
    rlibs = [Path(p) for p in artifact['filenames'] if p.endswith('.rlib')]
    if len(rlibs) != 1 or artifact['target']['name'] != 'cosmic':
        raise ValueError('Unique actual cosmic SDK rlib required.')
    rlib = contained(rlibs[0], source/'target/debug/deps')
    deps = rlib.parent
    def dependency_inventory():
        return {str(p): sha(contained(p, deps)) for p in sorted(deps.iterdir()) if p.is_file() and p.suffix in ('.rlib', '.rmeta', '.so')}
    before = dependency_inventory()
    output = Path(output)
    contained(output, parent)
    if output.parent != parent or output.exists():
        raise ValueError('Fresh direct child diagnostic directory required.')
    output.mkdir(mode=0o700)
    harness = Path(__file__).with_name('overflow_button_keyboard.rs')
    shutil.copy2(harness, output/harness.name)
    shutil.copy2(__file__, output/'executed-driver.py')
    (output/'dependency-inputs-before.json').write_text(json.dumps(before,indent=2)+'\n')
    report = {'scope':'Actual compiled SDK widget diagnostic; no native keyboard delivery or popup',
              'start':time.time(),'uid':os.getuid(),'cwd':str(output),'prior_build_root':str(build_root),
              'compiler':subprocess.check_output(['rustc','--version'],text=True).strip(),
              'sdk_compiler_artifact':artifact,'metadata_features':features,
              'input_sha256':{str(p):sha(p) for p in (widget, sdk/'src/widget/button/mod.rs',
                  driver/'report.json', driver/'panel-metadata.json', driver/'panel-app-test-build.log',
                  driver/'source-inputs-after.json', rlib, output/harness.name, output/'executed-driver.py')},
              'candidate_runtime_pass':False,'final_desktop_complete':False,
              'source_inputs_unchanged':False,'phases':[]}
    def save():
        (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    def command(name, argv):
        with (output/(name+'.log')).open('xb') as log:
            result = subprocess.run(argv,cwd=output,stdout=log,stderr=subprocess.STDOUT,timeout=120)
        report['phases'].append({'name':name,'command':argv,'returncode':result.returncode});save()
        return result.returncode
    save()
    executable = output/'button-keyboard-tests'
    result = command('compile',['rustc','--edition=2024','--test',str(output/harness.name),
        '--extern','cosmic='+str(rlib),'-L','dependency='+str(deps),'-o',str(executable)])
    if result == 0:
        report['elf_sha256'] = sha(executable)
        result = command('tests',[str(executable),'--test-threads=1'])
        command('file',['file',str(executable)])
        command('ldd',['ldd',str(executable)])
    after = dependency_inventory()
    (output/'dependency-inputs-after.json').write_text(json.dumps(after,indent=2)+'\n')
    report['dependencies_unchanged'] = before == after
    validate_source_inputs()
    report['source_inputs_unchanged'] = True
    report['end'] = time.time();save()
    if before != after:
        raise ValueError('Compiled dependency mutation detected.')
    return result

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-root',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    raise SystemExit(run(args.build_root,args.output))
