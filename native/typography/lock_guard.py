"""Strict original dependency graph guard for Git-to-local native toolkit overrides."""
import subprocess
import tomllib


def is_native_source(source):
    return source.split('#')[0].split('?')[0].removesuffix('/').removesuffix('.git') == 'git+https://github.com/pop-os/libcosmic'


def native_packages(lock):
    return {(p['name'], p['version']) for p in tomllib.loads(lock)['package']
            if is_native_source(p.get('source', ''))}


def foreign_dependencies(lock, substitutions=()):
    return {(p['name'], p['version'], p.get('source', ''), p.get('checksum', ''))
            for p in tomllib.loads(lock)['package']
            if not is_native_source(p.get('source', ''))
            and not ((p['name'], p['version']) in substitutions and not p.get('source'))}


def validate(application, original):
    old = original.decode('utf-8')
    substitutions = native_packages(old)
    if foreign_dependencies((application / 'Cargo.lock').read_text(), substitutions) != foreign_dependencies(old, substitutions):
        (application / 'Cargo.lock').write_bytes(original)
        raise RuntimeError('Foreign registry/checksum/Git dependency drift; original lock restored.')


def resolve(application, original, toolchain='stable', env=None):
    """Allow only recorded native Git packages to become equal-version local paths."""
    try:
        result = subprocess.run(['cargo', '+' + toolchain, 'metadata', '--format-version', '1'],
                                cwd=application, env=env, stdout=subprocess.PIPE, check=True)
        (application / '.studio-cargo-metadata.json').write_bytes(result.stdout)
        validate(application, original)
    except BaseException:
        (application / 'Cargo.lock').write_bytes(original)
        raise
