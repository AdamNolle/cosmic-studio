"""Portable orchestration refusals only; these tests do not build applets."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('thirdparty_vm_builder', Path(__file__).with_name('build_thirdparty.py'))
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class ThirdPartyGuards(unittest.TestCase):
    def test_root_and_non_linux_refused(self):
        for system, uid in (('Linux', 0), ('Windows', 1000)):
            with self.subTest(system=system, uid=uid), \
                 patch.object(builder.platform, 'system', return_value=system), \
                 patch.object(builder.os, 'geteuid', return_value=uid, create=True), \
                 patch.object(builder.subprocess, 'run') as run:
                with self.assertRaises(ValueError):
                    builder.preflight()
                run.assert_not_called()

    def test_caller_build_library_overrides_refused(self):
        for key in ('RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS', 'CARGO_PROFILE_RELEASE_LTO',
                    'CARGO_TARGET_DIR', 'LD_LIBRARY_PATH', 'PKG_CONFIG_PATH', 'RUSTUP_TOOLCHAIN'):
            with self.subTest(key=key), \
                 patch.object(builder.platform, 'system', return_value='Linux'), \
                 patch.object(builder.os, 'geteuid', return_value=1000, create=True), \
                 patch.dict(builder.os.environ, {key:'unapproved-fixture'}, clear=True):
                with self.assertRaises(ValueError):
                    builder.preflight()

    def test_explicit_selection_preserves_default_and_build_routes(self):
        self.assertEqual(builder.selected_profiles(None), tuple(builder.REPOSITORIES))
        self.assertEqual(builder.selected_profiles(['brightness']), ('brightness',))
        self.assertEqual(builder.profile_options(('brightness',)), ['--profile', 'brightness'])
        for invalid in ([], ['brightness', 'brightness'], ['unreviewed']):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                builder.selected_profiles(invalid)

    def test_four_reviewed_profiles_have_exact_repository_routes(self):
        spec = importlib.util.spec_from_file_location('thirdparty_original_pins', builder.ROOT/'native/thirdparty/prepare_build.py')
        pins = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pins)
        self.assertEqual(set(builder.REPOSITORIES), set(pins.PROFILES))
        for app_pin, library_pin in pins.PROFILES.values():
            self.assertEqual(len(app_pin),40)
            self.assertEqual(len(library_pin),40)
        self.assertTrue(all(url.startswith('https://github.com/') and url.endswith('.git')
                            for url in builder.REPOSITORIES.values()))


if __name__ == '__main__':
    unittest.main()
