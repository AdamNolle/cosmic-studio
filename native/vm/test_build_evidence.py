"""Mocked build-report guards only; these tests do not compile native candidates."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('studio_build_evidence', Path(__file__).with_name('build_native.py'))
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class BuildEvidenceTests(unittest.TestCase):
    def test_mocked_failures_preserve_original_inputs_and_exact_commands(self):
        for component, jobs in [('core', 4), ('media', 2), ('os-clients', 1),
                                ('launcher', 2), ('app-library', 2), ('workspaces', 2)]:
            with self.subTest(component=component), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                original = b'{"owned-test-fixture": true}\n'
                (root / 'studio-source-manifest.json').write_bytes(original)
                def failed(command, **kwargs):
                    # Source refresh must not alter the immutable build inputs.
                    (root / 'studio-source-manifest.json').write_bytes(b'changed fixture')
                    return subprocess.CompletedProcess(command, 1)
                with patch.object(builder, 'ROOT', root), \
                     patch.object(builder.platform, 'system', return_value='Linux'), \
                     patch.object(builder.os, 'geteuid', return_value=1000, create=True), \
                     patch.object(builder.subprocess, 'check_output', return_value='owned-version-fixture'), \
                     patch.object(builder.subprocess, 'run', side_effect=failed), \
                     patch.object(sys, 'argv', ['build_native.py', '--component', component, '--jobs', str(jobs)]), \
                     patch('builtins.print'):
                    self.assertEqual(builder.main(), 1)
                reports = list((root / 'work/native-builds').glob('*/report.json'))
                self.assertEqual(len(reports), 1)
                report = json.loads(reports[0].read_text())
                self.assertEqual(Path(report['source_manifest']).read_bytes(), original)
                self.assertEqual(report['source_manifest_sha256'], hashlib.sha256(original).hexdigest())
                self.assertEqual(report['status'], 'failed')
                self.assertFalse(report['installed'])
                self.assertFalse(report['runtime_validated'])
                self.assertEqual(report['command'][-2:], ['--jobs', str(jobs)])
                if component == 'media':
                    self.assertEqual(report['command'][2:5], ['--components', 'cosmic-player', 'cosmic-viewer'])
                if component in ('launcher', 'app-library', 'workspaces'):
                    self.assertEqual(report['command'][1:3], ['native/build_shell.py', 'cosmic-' + component])
                if component == 'os-clients':
                    self.assertEqual(report['command'][2:9], ['--components', 'cosmic-applets',
                        'cosmic-notifications', 'cosmic-osd', 'cosmic-store', 'cosmic-monitor', 'cosmic-osk'])
                self.assertTrue(Path(report['log']).is_file())

    def test_root_refused_before_any_build_or_network(self):
        with patch.object(builder.platform, 'system', return_value='Linux'), \
             patch.object(builder.os, 'geteuid', return_value=0, create=True), \
             patch.object(builder.subprocess, 'run') as run, \
             patch.object(builder.subprocess, 'check_output') as output, \
             patch.object(sys, 'argv', ['build_native.py', '--component', 'core']), \
             patch.object(sys, 'stderr'):
            with self.assertRaises(SystemExit):
                builder.main()
            run.assert_not_called()
            output.assert_not_called()


if __name__ == '__main__':
    unittest.main()
