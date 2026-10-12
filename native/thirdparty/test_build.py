import importlib.util
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('studio_thirdparty_build', Path(__file__).with_name('build.py'))
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class LockedBuildGateTests(unittest.TestCase):
    def test_rejected_alias_resolution_restores_lock_before_any_compilation(self):
        for metadata_status in (0, 1):
            with self.subTest(metadata_status=metadata_status), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                app = root/'sources/app-caffeine-native'
                app.mkdir(parents=True)
                lock = app/'Cargo.lock'
                lock.write_bytes(b'exact original lock')
                calls = []
                def metadata(arguments, **kwargs):
                    calls.append(arguments)
                    lock.write_bytes(b'rejected dependency resolution')
                    return SimpleNamespace(returncode=metadata_status)
                checks = [app/'.studio-thirdparty-prepared.json', ValueError('foreign dependency graph changed')]
                with patch.object(build.prepare, 'prepare', side_effect=checks), \
                        patch.object(subprocess, 'run', side_effect=metadata):
                    with self.assertRaises((ValueError, RuntimeError)):
                        build.run('caffeine', root/'sources', root/'target', root/'artifacts', None, 1)
                self.assertEqual(lock.read_bytes(), b'exact original lock')
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0][1], 'metadata')
                self.assertFalse((root/'artifacts/caffeine/build.json').exists())


class ApplicationTestRoutingGuards(unittest.TestCase):
    def test_locked_binary_route_keeps_original_features(self):
        command = build.application_test_command(Path('app/Cargo.toml'), 'brightness', 2)
        self.assertEqual(command, ['cargo', 'test', '--locked', '--manifest-path',
                                  str(Path('app/Cargo.toml')), '--bin', 'brightness',
                                  '--no-run', '--message-format=json', '-j', '2'])
        self.assertNotIn('--features', command)
        self.assertNotIn('--no-default-features', command)

    def test_exact_application_artifact_required(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder);app = root/'app';target = root/'target';target.mkdir()
            binary = target/'tests';binary.write_bytes(b'\x7fELFmock-source-only')
            metadata = {'packages': [{'id':'local-app', 'name':'brightness', 'source':None,
                                     'manifest_path':str(app/'Cargo.toml')}],
                        'resolve': {'nodes':[{'id':'local-app','features':['original']}]}}
            artifact = {'reason':'compiler-artifact','package_id':'local-app','executable':str(binary),
                        'profile':{'test':True},'features':['original'],
                        'target':{'name':'brightness','kind':['bin'],'src_path':str(app/'src/main.rs')}}
            self.assertEqual(build.application_test_artifact(metadata,[artifact],app,target),artifact)
            for field, wrong in [('features',[]),('package_id','foreign'),
                                  ('target',dict(artifact['target'],src_path=str(root/'foreign.rs'))),
                                  ('target',dict(artifact['target'],kind=['lib'])),
                                  ('executable',str(root/'escaped'))]:
                bad = deepcopy(artifact);bad[field] = wrong
                with self.subTest(field=field), self.assertRaises(ValueError):
                    build.application_test_artifact(metadata,[bad],app,target)
            with self.assertRaises(ValueError):
                build.application_test_artifact(metadata,[artifact,artifact],app,target)
            foreign = deepcopy(metadata);foreign['packages'][0]['source']='git+foreign'
            with self.assertRaises(ValueError):
                build.application_test_artifact(foreign,[artifact],app,target)
            binary.write_bytes(b'not ELF')
            with self.assertRaises(ValueError):
                build.application_test_artifact(metadata,[artifact],app,target)


class BackendTestRoutingGuards(unittest.TestCase):
    def test_locked_dependency_selection_does_not_suppress_original_features(self):
        command = build.backend_test_command(Path('application/Cargo.toml'), 2)
        self.assertEqual(command, ['cargo', 'test', '--locked', '--manifest-path',
                                  str(Path('application/Cargo.toml')), '-p', 'iced_winit',
                                  '--lib', '--no-run', '--message-format=json', '-j', '2'])
        self.assertNotIn('--features', command)
        self.assertNotIn('--no-default-features', command)

    def test_artifact_requires_exact_native_source_and_full_original_features(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            library, target = root/'library', root/'target'
            target.mkdir()
            binary = target/'backend-tests'
            binary.write_bytes(b'\x7fELFmock-source-only')
            package_id = 'pinned-local-backend'
            metadata = {'packages': [{'name': 'iced_winit', 'id': package_id,
                                     'manifest_path': str(library/'iced/winit/Cargo.toml')}],
                        'resolve': {'nodes': [{'id': package_id,
                                              'features': ['default', 'x11', 'wayland', 'multi-window']}]}}
            artifact = {'reason': 'compiler-artifact', 'package_id': package_id,
                        'executable': str(binary), 'profile': {'test': True},
                        'features': ['wayland', 'default', 'multi-window', 'x11'],
                        'target': {'name': 'iced_winit', 'src_path': str(library/'iced/winit/src/lib.rs')}}
            self.assertEqual(build.backend_test_artifact(metadata, [artifact], library, target), artifact)
            for field, wrong in [('features', ['default', 'x11']),
                                 ('features', artifact['features']+['unexpected']),
                                 ('target', {'name': 'iced_winit', 'src_path': str(root/'foreign/lib.rs')}),
                                 ('executable', str(root/'foreign-tests')),
                                 ('package_id', 'foreign')]:
                changed = deepcopy(artifact)
                changed[field] = wrong
                with self.subTest(field=field, wrong=wrong), self.assertRaises(ValueError):
                    build.backend_test_artifact(metadata, [changed], library, target)
            with self.assertRaises(ValueError):
                build.backend_test_artifact(metadata, [artifact, artifact], library, target)
            foreign = deepcopy(metadata)
            foreign['packages'][0]['manifest_path'] = str(root/'foreign/Cargo.toml')
            with self.assertRaisesRegex(ValueError, 'reviewed local'):
                build.backend_test_artifact(foreign, [artifact], library, target)
            binary.write_bytes(b'not ELF')
            with self.assertRaisesRegex(ValueError, 'native ELF'):
                build.backend_test_artifact(metadata, [artifact], library, target)


class NativeHelperIdentityGuards(unittest.TestCase):
    # Byte-exact reviewed upstream manifest; filesystem/Git below are mocks,
    # not an actual source checkout or Cargo compilation.
    MANIFEST = b'''[package]
name = "build_helpers"
version.workspace = true
authors.workspace = true
edition.workspace = true
license.workspace = true
repository.workspace = true
homepage.workspace = true
categories.workspace = true
keywords.workspace = true
rust-version.workspace = true

[dependencies]
cfg_aliases = { version = "0.2.1" }

[lints]
workspace = true
'''

    def fixture(self, root):
        library = root/'library'
        for name, package in [('Cargo.toml', 'libcosmic'), ('iced/winit/Cargo.toml', 'iced_winit')]:
            path = library/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('[package]\nname = "'+package+'"\nversion = "0.14.0"\n')
        manifest = library/'iced/build_helpers/Cargo.toml'
        manifest.parent.mkdir()
        manifest.write_bytes(self.MANIFEST)
        return library, manifest

    def test_only_exact_original_helper_from_reviewed_submodule_is_native(self):
        guard = build.prepare
        self.assertEqual(hashlib.sha256(self.MANIFEST).hexdigest(), guard.NATIVE_HELPER_MANIFEST_SHA256)
        for revision, iced in guard.NATIVE_HELPER_SUBMODULES.items():
            with self.subTest(revision=revision), tempfile.TemporaryDirectory() as folder:
                library, manifest = self.fixture(Path(folder))
                def git(root, *args):
                    return revision if root == library and args == ('rev-parse', 'HEAD') else iced
                with patch.object(guard, 'git', side_effect=git), patch.object(subprocess, 'check_output', return_value=self.MANIFEST):
                    entries = guard.crate_entries(library)
                self.assertEqual(entries['build_helpers'], manifest.parent)

    def test_wrong_path_manifest_or_library_submodule_is_refused(self):
        guard = build.prepare
        revision, iced = next(iter(guard.NATIVE_HELPER_SUBMODULES.items()))
        with tempfile.TemporaryDirectory() as folder:
            library, manifest = self.fixture(Path(folder))
            def git(root, *args):
                return revision if root == library and args == ('rev-parse', 'HEAD') else iced
            with patch.object(guard, 'git', side_effect=git), patch.object(subprocess, 'check_output', return_value=self.MANIFEST):
                wrong = library/'foreign/Cargo.toml'
                wrong.parent.mkdir()
                wrong.write_bytes(self.MANIFEST)
                with self.assertRaisesRegex(ValueError, 'reviewed SDK path'):
                    guard.verify_native_helper(library, wrong)
                manifest.write_bytes(self.MANIFEST+b'# changed\n')
                with self.assertRaisesRegex(ValueError, 'original bytes'):
                    guard.verify_native_helper(library, manifest)
                manifest.write_bytes(self.MANIFEST)
                with patch.object(subprocess, 'check_output', return_value=self.MANIFEST+b'# unreviewed\n'):
                    with self.assertRaisesRegex(ValueError, 'original bytes'):
                        guard.verify_native_helper(library, manifest)
            for root, args, changed in [(library, ('rev-parse', 'HEAD'), '0'*40),
                                        (library, ('rev-parse', 'HEAD:iced'), '0'*40),
                                        (library/'iced', ('rev-parse', 'HEAD'), '0'*40)]:
                def wrong_git(path, *actual_args):
                    return changed if (path, actual_args) == (root, args) else git(path, *actual_args)
                with patch.object(guard, 'git', side_effect=wrong_git), self.assertRaisesRegex(ValueError, 'pins'):
                    guard.verify_native_helper(library, manifest)

    def test_helper_alias_never_allows_foreign_source_checksum_or_version_drift(self):
        guard = build.prepare
        revision = guard.PROFILES['brightness'][1]
        def lock(version='0.14.0', source=None, checksum='original'):
            return ('[[package]]\nname="build_helpers"\nversion="'+version+'"\n'
                    + ('source="'+source+'"\n' if source else '')
                    + '[[package]]\nname="foreign"\nversion="1.0.0"\n'
                    + 'source="registry+https://github.com/rust-lang/crates.io-index"\nchecksum="'+checksum+'"\n')
        trusted = 'git+https://github.com/pop-os/libcosmic#'+revision
        expected = guard.lock_packages(lock(source=trusted), {'build_helpers'}, revision)
        self.assertEqual(expected, guard.lock_packages(lock(), {'build_helpers'}, revision))
        for source in ['git+https://evil.invalid/libcosmic#'+revision,
                       'git+https://github.com/pop-os/libcosmic-lookalike#'+revision,
                       'git+https://github.com/pop-os/libcosmic//#'+revision,
                       'registry+https://github.com/rust-lang/crates.io-index',
                       'git+https://github.com/pop-os/libcosmic#'+'0'*40]:
            with self.subTest(source=source), self.assertRaises(ValueError):
                guard.lock_packages(lock(source=source), {'build_helpers'}, revision)
        self.assertNotEqual(expected, guard.lock_packages(lock(version='0.14.1'), {'build_helpers'}, revision))
        self.assertNotEqual(expected, guard.lock_packages(lock(checksum='changed'), {'build_helpers'}, revision))


class BackportSourceGuards(unittest.TestCase):
    def test_real_git_lifecycle_postimage_and_acknowledged_discards(self):
        directory = Path(__file__).resolve().parent
        name = 'winit/src/platform_specific/wayland/handlers/blur_lifecycle.rs'
        legacy = json.loads((directory.parent/'popups/legacy/compatibility.json').read_text())
        with tempfile.TemporaryDirectory() as folder:
            args = ['git', '-c', 'core.autocrlf=false', 'apply', '--include='+name,
                    str(directory/'caffeine-blur.patch')]
            subprocess.run(args[:4]+['--check']+args[4:], cwd=folder, check=True, capture_output=True)
            subprocess.run(args, cwd=folder, check=True, capture_output=True)
            source = Path(folder)/name
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),
                             legacy['native_backport_sha256']['iced/'+name])
            text = source.read_text()
            self.assertEqual(text.count('_ = self.desired.'), 3)
            self.assertEqual(text.count('_ = self.applied.remove(&id);'), 1)
            self.assertIn('_ = state.reconcile(1, true, true);', text)
            self.assertNotIn('#[allow(', text)

    def test_real_git_patch_on_exact_original_popup_state(self):
        directory = Path(__file__).resolve().parent
        profile = json.loads((directory/'caffeine-blur-profile.json').read_text())
        legacy = json.loads((directory.parent/'popups/legacy/compatibility.json').read_text())
        name = 'winit/src/platform_specific/wayland/event_loop/state.rs'
        original = gzip.decompress((directory/'pinned-caffeine-state.rs.gz').read_bytes())
        self.assertEqual(hashlib.sha256(original).hexdigest(), profile['sha256'][name])
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder)/name
            source.parent.mkdir(parents=True)
            source.write_bytes(original)
            # Command-local LF preservation; never change host Git policy or accept CRLF hashes.
            args = ['git', '-c', 'core.autocrlf=false', 'apply', '--include='+name, str(directory/'caffeine-blur.patch')]
            subprocess.run(args[:4]+['--check']+args[4:], cwd=folder, check=True, capture_output=True)
            subprocess.run(args, cwd=folder, check=True, capture_output=True)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),
                             legacy['native_backport_sha256']['iced/'+name])

    def test_correction_owns_parent_before_mutable_reconciliation(self):
        text = Path(__file__).with_name('caffeine-blur.patch').read_text()
        owned = text.index('+        let toplevel = toplevel.clone();')
        reconcile = text.index('+        self.reconcile_popup_blur(settings.id);')
        returned = text.index('+            toplevel,')
        self.assertLess(owned, reconcile)
        self.assertLess(reconcile, returned)
        self.assertEqual(text.count('+        let toplevel = toplevel.clone();'), 1)
        self.assertIn('-            toplevel.clone(),', text)

    def test_patch_hash_and_original_pins_preimage_remain_authoritative(self):
        directory = Path(__file__).parent
        profile = json.loads((directory/'caffeine-blur-profile.json').read_text())
        self.assertEqual(hashlib.sha256((directory/'caffeine-blur.patch').read_bytes()).hexdigest(),
                         profile['patch_sha256'])
        self.assertEqual(profile['iced'], '7bb364e01d6cd6c07703416828006ab497a082e6')
        self.assertEqual(profile['library'], '76c1897d4d9a637c8aa4016483bf05fec5f10ebd')
        self.assertEqual(profile['sha256']['winit/src/platform_specific/wayland/event_loop/state.rs'],
                         '7b1cd04b4b54ec7197b18646429b53be449ff748f60fca695ae87f81d7968436')
        legacy = json.loads((directory.parent/'popups/legacy/compatibility.json').read_text())
        self.assertEqual(legacy['native_backport_sha256']['iced/winit/src/platform_specific/wayland/event_loop/state.rs'],
                         '6153e6d5f0a3d7e190b8c636f773021ba9b86d2bfb1424c32f7783b487206142')


if __name__ == '__main__':
    unittest.main()
