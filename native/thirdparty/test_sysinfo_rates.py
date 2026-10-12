import gzip,hashlib,importlib.util,json,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).parent
spec=importlib.util.spec_from_file_location('sysinfo_rates',ROOT/'prepare_sysinfo_rates.py');rates=importlib.util.module_from_spec(spec);spec.loader.exec_module(rates)
original=json.loads(gzip.decompress((ROOT/'pinned-sysinfo-sources.json.gz').read_bytes()))

class SysinfoRateGuards(unittest.TestCase):
    def test_original_blobs_and_license_retained(self):
        for name,text in original.items():self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),rates.ORIGINAL[name])
        self.assertIn('GNU GENERAL PUBLIC LICENSE',(ROOT/'pinned-sysinfo.LICENSE').read_text())

    def test_only_existing_delta_rates_are_normalized(self):
        after=rates.transform(original);data=after['src/data/mod.rs']
        self.assertIn('megabytes_per_second(read, elapsed)',data)
        self.assertIn('megabytes_per_second(down, elapsed)',data)
        self.assertIn('checked_add(disk.usage().read_bytes)',data)
        self.assertIn('checked_add(iface.transmitted())',data)
        self.assertIn('self.network_rate_window.reset()',data)
        self.assertIn('self.disks.rate_window.reset()',data)
        self.assertIn('MB/s',after['src/config.rs'])
        self.assertIn('const CONFIG_VERSION: u64 = 1;',after['src/config.rs'])
        # Existing GPU implementation is untouched, including the deferred unbounded output.
        before=original['src/data/mod.rs'].split('pub(crate) struct Gpu {')[1].split('/// The data coming')[0]
        actual=data.split('pub(crate) struct Gpu {')[1].split('/// The data coming')[0]
        self.assertEqual(actual,before)
        self.assertNotIn('total_read_bytes',data)
        self.assertNotIn('total_received()',data)
        self.assertTrue(all(line.rstrip()==line for text in after.values() for line in text.splitlines()))

    def test_drift_or_repeat_refused(self):
        changed=dict(original);changed['src/main.rs']+='\n'
        for files in (changed,{k:v for k,v in rates.transform(original).items() if k in original}):
            with self.assertRaisesRegex(ValueError,'Changed original'):rates.transform(files)

    def test_working_copy_line_endings_are_not_normalized_into_acceptance(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'app';root.mkdir()
            for name,text in original.items():
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(text.encode())
            subprocess.run(['git','init','-q',str(root)],check=True)
            subprocess.run(['git','-C',str(root),'-c','core.autocrlf=false','add','.'],check=True)
            subprocess.run(['git','-C',str(root),'-c','user.name=Fixture','-c','user.email=fixture@invalid','commit','-qm','fixture'],check=True)
            file=root/'src/data/mod.rs';file.write_bytes(file.read_bytes().replace(b'\n',b'\r\n'))
            real=subprocess.check_output
            def revision(command,**kwargs):return rates.PIN+'\n' if command[-2:]==['rev-parse','HEAD'] else real(command,**kwargs)
            with patch.object(rates.subprocess,'check_output',side_effect=revision):
                with self.assertRaisesRegex(ValueError,'input bytes'):rates.prepare(root,Path(folder)/'forbidden.patch',True)
                self.assertFalse((Path(folder)/'forbidden.patch').exists())

    def test_real_patch_and_lock_preservation(self):
        # Authentic source bytes/real Git apply; the fixture revision response alone is mocked.
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'app';root.mkdir()
            for name,text in original.items():
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(text.encode())
            lock=root/'Cargo.lock';lock.write_bytes(b'exact lock fixture\n')
            subprocess.run(['git','init','-q',str(root)],check=True)
            subprocess.run(['git','-C',str(root),'-c','core.autocrlf=false','add','.'],check=True)
            subprocess.run(['git','-C',str(root),'-c','user.name=Fixture','-c','user.email=fixture@invalid','commit','-qm','fixture'],check=True)
            real=subprocess.check_output
            def revision(command,**kwargs):return rates.PIN+'\n' if command[-2:]==['rev-parse','HEAD'] else real(command,**kwargs)
            with patch.object(rates.subprocess,'check_output',side_effect=revision):
                after=rates.prepare(root,Path(folder)/'rates.patch',True)
                for name,text in after.items():self.assertEqual((root/name).read_bytes(),text.encode())
                self.assertEqual(lock.read_bytes(),b'exact lock fixture\n')
                with self.assertRaisesRegex(ValueError,'Existing rate'):rates.prepare(root,Path(folder)/'repeat.patch',True)

if __name__=='__main__':unittest.main()
