"""Portable Viewer resume refusal tests only; no native compilation evidence."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('viewer_resume_guard', Path(__file__).with_name('resume_viewer.py'))
resume = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resume)


class ResumeGuards(unittest.TestCase):
    def refused(self, uid, extra_env):
        with patch.object(resume.platform, 'system', return_value='Linux'), \
             patch.object(resume.os, 'geteuid', return_value=uid, create=True), \
             patch.dict(resume.os.environ, extra_env, clear=True), \
             patch.object(resume.subprocess, 'run') as run, \
             patch.object(Path, 'mkdir') as mkdir, \
             patch.object(sys, 'argv', ['resume_viewer.py', '--project', '/owned', '--build-dir', '/owned/work/native-builds/media-fixture']), \
             patch.object(sys, 'stderr'):
            with self.assertRaises(SystemExit):
                resume.main()
            run.assert_not_called()
            mkdir.assert_not_called()

    def test_root_refused_before_file_network_or_build_mutation(self):
        self.refused(0, {})

    def test_compiler_and_profile_override_refused(self):
        for variable in ('RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS', 'CARGO_PROFILE_RELEASE_LTO'):
            with self.subTest(variable=variable):
                self.refused(1000, {variable: 'unapproved-fixture'})


if __name__ == '__main__':
    unittest.main()
