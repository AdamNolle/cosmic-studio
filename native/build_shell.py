#!/usr/bin/env python3
"""Rebuild a pinned COSMIC shell client with native display typography."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tomllib

PACKAGE = Path(__file__).resolve().parents[1]
SOURCES = {
    'cosmic-panel': ('b5cc19e351b82eed999097ced1ff267d27bf8e7a', '23f5d63fed2a370f3c2f54b90ec8f0896fe82105', 'panel/panel-glass.patch'),
    'cosmic-launcher': ('cc3d42bcc8fbcb67e6312f2766394e18b4d937d5', '8cb86195ec576064ac8e59e9200315714d17dc55', 'typography/cosmic-launcher-dark-shell.patch'),
    'cosmic-app-library': ('0a3996de82c264095ade047661f7a3088f99013e', '8cb86195ec576064ac8e59e9200315714d17dc55', 'typography/cosmic-app-library-dark-shell.patch'),
    'cosmic-workspaces': ('28e257daa86643aee4166f192fb3e000ac3f7605', '8cb10bf6e24b86a7d2a9cf8c662d3e0154db1b21', 'typography/cosmic-workspaces-dark-shell.patch'),
}
SOURCE_REPOSITORIES = {
    'cosmic-workspaces': 'https://github.com/pop-os/cosmic-workspaces-epoch.git',
}


def run(args, cwd=None):
    subprocess.run([str(arg) for arg in args], cwd=cwd, check=True)


def checkout(folder, repository, revision):
    if not folder.exists():
        run(['git', 'clone', '--no-checkout', repository, folder])
        run(['git', 'checkout', '--detach', revision], folder)
        run(['git', 'submodule', 'update', '--init', '--recursive'], folder)
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=folder, text=True).strip()
    if actual != revision:
        raise RuntimeError(f'Unexpected source revision in {folder}: {actual}')
    return actual


def prepared_inputs(component):
    revision, library_revision, patch_relative = SOURCES[component]
    patch = PACKAGE / 'native' / patch_relative
    generator = PACKAGE / 'native/typography/patch_libcosmic.py'
    return {
        'schema_version': 3,
        'source_commit': revision,
        'library_commit': library_revision,
        'source_patch_sha256': hashlib.sha256(patch.read_bytes()).hexdigest(),
        'typography_generator_sha256': hashlib.sha256(generator.read_bytes()).hexdigest(),
        'font_embedding_generator_sha256': hashlib.sha256(
            (PACKAGE / 'native/typography/embed_fonts.py').read_bytes()).hexdigest(),
        'font_manifest_sha256': hashlib.sha256((PACKAGE / 'fonts/manifest.json').read_bytes()).hexdigest(),
        'display_role_generator_sha256': hashlib.sha256(
            (PACKAGE / 'native/typography/prepare_display_roles.py').read_bytes()).hexdigest(),
        'display_role_profiles_sha256': hashlib.sha256(
            (PACKAGE / 'native/typography/display-role-profiles.json').read_bytes()).hexdigest(),
        'popup_generator_sha256': popup_inputs_digest(),
    }


def popup_inputs_digest():
    directory = PACKAGE / 'native/popups'
    digest = hashlib.sha256()
    paths = sorted(p for p in directory.iterdir() if p.suffix in ('.py', '.rs', '.json'))
    for path in paths:
        digest.update(path.name.encode() + b'\0' + path.read_bytes() + b'\0')
    return digest.hexdigest()


def library_inputs(expected):
    return {key: value for key, value in expected.items()
            if key not in ('source_commit', 'source_patch_sha256')}


def validate_prepared(marker, expected):
    try:
        actual = json.loads(marker.read_text())
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeError(f'Unverified prepared inputs in {marker}; use a fresh --work directory. '
                           'The existing source tree was left unchanged.') from error
    if actual != expected:
        raise RuntimeError(f'Stale prepared inputs in {marker}; use a fresh --work directory. '
                           'The existing source tree was left unchanged.')


def library_overrides(library):
    entries = []
    for path in library.rglob('Cargo.toml'):
        try:
            name = tomllib.loads(path.read_text()).get('package', {}).get('name', '')
        except tomllib.TOMLDecodeError:
            continue
        if name == 'libcosmic' or name.startswith('iced') or name in ('cosmic-config', 'cosmic-config-derive', 'cosmic-theme'):
            entries.append((name, path.parent.relative_to(library)))
    return '\n[patch."https://github.com/pop-os/libcosmic"]\n' + ''.join(
        f'{name} = {{ path = "../{library.name}/{relative}" }}\n' for name, relative in sorted(entries))


def build(component, work, jobs):
    revision, library_revision, patch_relative = SOURCES[component]
    work.mkdir(parents=True, exist_ok=True)
    source = work / component
    library = work / ('libcosmic-' + library_revision[:7])
    marker = source / '.studio-prepared'
    library_marker = library / '.studio-typography-prepared'
    expected = prepared_inputs(component)
    library_expected = library_inputs(expected)
    # Reject stale or legacy preparations before touching either source tree.
    if marker.exists():
        validate_prepared(marker, expected)
        validate_prepared(library_marker, library_expected)
    elif library_marker.exists():
        validate_prepared(library_marker, library_expected)
    checkout(source, SOURCE_REPOSITORIES.get(component,
             f'https://github.com/pop-os/{component}.git'), revision)
    checkout(library, 'https://github.com/pop-os/libcosmic.git', library_revision)
    display_prepared = 'pub fn display()' in (library / 'src/font.rs').read_text()
    if display_prepared:
        validate_prepared(library_marker, library_expected)
    elif library_marker.exists() or marker.exists():
        raise RuntimeError(f'Prepared native typography is missing in {library}; '
                           'use a fresh --work directory. The existing source tree was left unchanged.')
    if not marker.exists():
        patch = PACKAGE / 'native' / patch_relative
        run(['git', 'apply', '--check', patch], source)
        run(['git', 'apply', patch], source)
        if not display_prepared:
            spec = importlib.util.spec_from_file_location('typography', PACKAGE / 'native/typography/patch_libcosmic.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            typography = work / ('typography-' + library_revision[:7] + '.patch')
            typography.write_text(module.patch_for(library))
            run(['git', 'apply', '--check', typography], library)
            run(['git', 'apply', typography], library)
            embed_spec = importlib.util.spec_from_file_location('embed_fonts', PACKAGE / 'native/typography/embed_fonts.py')
            embed = importlib.util.module_from_spec(embed_spec)
            embed_spec.loader.exec_module(embed)
            if library_revision in embed.PINS:
                run(['python3', PACKAGE / 'native/typography/embed_fonts.py', library,
                     '--output', work / ('embedded-fonts-' + library_revision[:7] + '.patch'), '--apply'])
            # Semantic menu headings use the already-prepared display font.
            # This file is outside the strict popup source fingerprints.
            run(['python3', PACKAGE / 'native/typography/prepare_display_roles.py', library,
                 '--profile', 'native-' + library_revision[:8],
                 '--output', work / ('display-roles-' + library_revision[:7] + '.patch'), '--apply'])
            run(['python3', PACKAGE / 'native/popups/prepare.py', library,
                 '--revision', library_revision, '--output', work / ('popup-' + library_revision[:7] + '.patch'), '--apply'])
            library_marker.write_text(json.dumps(library_expected, indent=2) + '\n')
        if component != 'cosmic-panel':
            run(['python3', PACKAGE / 'native/typography/prepare_display_roles.py', source,
                 '--profile', component,
                 '--output', work / ('display-roles-' + component + '.patch'), '--apply'])
        cargo = source / 'Cargo.toml'
        if tomllib.loads(cargo.read_text()).get('patch', {}).get('https://github.com/pop-os/libcosmic'):
            raise RuntimeError('Source already contains a libcosmic override; inspect it before building.')
        cargo.write_text(cargo.read_text() + library_overrides(library))
        marker.write_text(json.dumps(expected, indent=2) + '\n')
    # Resolve only the local crate substitutions; existing transitive pins stay
    # in the upstream lockfile. The subsequent release build requires that lock.
    run(['cargo', '+stable', 'check', '-j', jobs], source)
    run(['cargo', '+stable', 'build', '--release', '--locked', '-j', jobs], source)
    binary = source / 'target/release' / component
    print(f'Built native candidate: {binary}')
    print('Inspect it before installing with native/install.py. The running session is unchanged.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('component', choices=SOURCES)
    parser.add_argument('--work', type=Path, default=PACKAGE / 'work/native-builds')
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.jobs <= 24:
        parser.error('--jobs must be between 1 and 24.')
    build(args.component, args.work.resolve(), args.jobs)
