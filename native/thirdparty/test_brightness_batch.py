"""Exact original source/patch guards; native command tests are a separate gate."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parent

def load(name):
    spec = importlib.util.spec_from_file_location('studio_'+name, ROOT/(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

batch = load('prepare_brightness_batch')
routes = load('prepare_routes')
original = json.loads(gzip.decompress((ROOT/'pinned-brightness-sources.json.gz').read_bytes()))

def routed():
    files = dict(original)
    files['src/app.rs'] = files['src/app.rs'].replace('get_popup(popup_settings)', routes.MANAGED_POPUP).replace(
        'use cosmic::iced::platform_specific::shell::commands::popup::{destroy_popup, get_popup};',
        'use cosmic::iced::platform_specific::shell::commands::popup::destroy_popup;')
    return files


class BrightnessBatchGuards(unittest.TestCase):
    def test_fixture_original_blobs_and_original_license_retained(self):
        self.assertEqual(set(original), set(batch.ORIGINAL))
        for name, text in original.items():
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), batch.ORIGINAL[name])
        self.assertEqual(hashlib.sha256((ROOT/'pinned-brightness.LICENSE').read_bytes()).hexdigest(),
                         '3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986')

    def test_all_group_targets_use_one_original_watch_value(self):
        after = batch.transform(routed())
        self.assertIn('if !vec.is_empty() {\n                    self.send(EventToSub::SetBatch(vec));', after['src/app.rs'])
        self.assertIn('vec.push((id.clone(), b));', after['src/app.rs'])
        self.assertNotIn('for e in vec', after['src/app.rs'])
        self.assertIn('watch::channel(EventToSub::Refresh)', after['src/monitor.rs'])
        self.assertIn('command.into_writes().expect("write command")', after['src/monitor.rs'])
        for unchanged in ('get_vcp_feature(BRIGHTNESS_CODE)', 'set_vcp_feature(BRIGHTNESS_CODE, value)',
                          'tokio::time::sleep(Duration::from_millis(50)).await', 'Arc::clone(displays.get_mut(&id).unwrap())'):
            self.assertEqual(after['src/monitor.rs'].count(unchanged), original['src/monitor.rs'].count(unchanged))
        self.assertIn('mod commands;\nmod monitor;', after['src/main.rs'])
        self.assertEqual(after['src/commands.rs'], batch.COMMANDS.read_text())
        self.assertIn('NOT make the upstream watch channel a FIFO', after['src/commands.rs'])

    def test_original_unrouted_drift_or_repeat_refused(self):
        for files in (original, dict(routed(), **{'src/monitor.rs':original['src/monitor.rs']+'\n'}),
                      {k:v for k,v in batch.transform(routed()).items() if k in original}):
            with self.subTest(files=list(files)), self.assertRaisesRegex(ValueError, 'Changed brightness'):
                batch.transform(files)

    def test_real_git_patch_is_exact_and_lock_unchanged(self):
        # Git application is real; only the expected revision response is a mock.
        # This tiny repository is not claimed to be authentic upstream provenance.
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)/'app';root.mkdir()
            for name, text in original.items():
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(text.encode())
            lock=root/'Cargo.lock';lock.write_bytes(b'exact original lock fixture\n')
            subprocess.run(['git','init','-q',str(root)],check=True)
            subprocess.run(['git','-C',str(root),'add','.'],check=True)
            subprocess.run(['git','-C',str(root),'-c','user.name=Fixture','-c','user.email=fixture@invalid','commit','-qm','fixture'],check=True)
            for name,text in routed().items():(root/name).write_bytes(text.encode())
            real = subprocess.check_output
            def revision(command, **kwargs):
                return batch.PIN+'\n' if command[-2:]==['rev-parse','HEAD'] else real(command,**kwargs)
            with patch.object(batch.subprocess,'check_output',side_effect=revision):
                after=batch.prepare(root,Path(folder)/'batch.patch',apply=True)
                for name,text in after.items():self.assertEqual((root/name).read_bytes(),text.encode())
                self.assertEqual(lock.read_bytes(),b'exact original lock fixture\n')
                with self.assertRaisesRegex(ValueError,'Existing command'):
                    batch.prepare(root,Path(folder)/'repeat.patch',apply=True)


if __name__ == '__main__':
    unittest.main()
