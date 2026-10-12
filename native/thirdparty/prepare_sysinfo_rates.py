#!/usr/bin/env python3
"""Exact Sysinfo delta-rate normalization; no new providers/permissions/lock changes."""
import argparse
import difflib
import hashlib
from pathlib import Path
import subprocess

PIN='f66e0c7b133bf4249d23ab7483693cedca46ad19'
ORIGINAL={'src/data/mod.rs':'6beb11a8c5d257479baf903fcfaea45582ddc4bf1609e1171d87f32052cc3712',
          'src/main.rs':'48e47e8f403409b3c4a775a5c3b4c79196ef9b8e258bb855e468dbfc3c3efc43',
          'src/config.rs':'37994da076f21ec167c7198413870d5c60635d1ec00bbcdc20c5686d4d58d9c3'}
MODULE=Path(__file__).with_name('sysinfo_sample_rates.rs')


def replace_once(text,before,after):
    if text.count(before)!=1:raise ValueError('Changed exact Sysinfo rate seam.')
    return text.replace(before,after,1)


def transform(files):
    if set(files)!=set(ORIGINAL) or any(hashlib.sha256(files[name].encode()).hexdigest()!=digest for name,digest in ORIGINAL.items()):
        raise ValueError('Changed original Sysinfo input; preserve it and prepare a fresh tree.')
    data=replace_once(files['src/data/mod.rs'],'use crate::{\n    config::SysInfoConfig,',
                      'use crate::{\n    sample_rates::{RateWindow, megabytes_per_second},\n    config::SysInfoConfig,')
    data=replace_once(data,'    disks: sysinfo::Disks,','    disks: sysinfo::Disks,\n    rate_window: RateWindow,')
    data=replace_once(data,'            disks: sysinfo::Disks::new_with_refreshed_list(),',
                      '            disks: sysinfo::Disks::new_with_refreshed_list(),\n            rate_window: RateWindow::default(),')
    data=replace_once(data,'        let (mut read, mut write) = (0u64, 0u64);',
                      '        let (mut read, mut write) = (Some(0u64), Some(0u64));')
    data=replace_once(data,'''            read += disk.usage().read_bytes;
            write += disk.usage().written_bytes;''',
                      '''            read = read.and_then(|bytes| bytes.checked_add(disk.usage().read_bytes));
            write = write.and_then(|bytes| bytes.checked_add(disk.usage().written_bytes));''')
    data=replace_once(data,'''        self.read = Some(read as f64 / 1_000_000.0);
        self.write = Some(write as f64 / 1_000_000.0);''',
                      '''        let elapsed = self.rate_window.elapsed(Instant::now(), seen.into_iter().map(|name| name.to_os_string()));
        self.read = megabytes_per_second(read, elapsed);
        self.write = megabytes_per_second(write, elapsed);''')
    data=replace_once(data,'    last_interface_scan: Instant,','    last_interface_scan: Instant,\n    network_rate_window: RateWindow,')
    data=replace_once(data,'            last_interface_scan: Instant::now(),',
                      '            last_interface_scan: Instant::now(),\n            network_rate_window: RateWindow::default(),')
    data=replace_once(data,'            let (mut up, mut down) = (0u64, 0u64);',
                      '            let (mut up, mut down) = (Some(0u64), Some(0u64));\n            let mut seen = HashSet::new();')
    data=replace_once(data,'''                    up += iface.transmitted();
                    down += iface.received();''',
                      '''                    let _ = seen.insert(name.as_str());
                    up = up.and_then(|bytes| bytes.checked_add(iface.transmitted()));
                    down = down.and_then(|bytes| bytes.checked_add(iface.received()));''')
    data=replace_once(data,'''            self.download_speed = needs_download.then(|| down as f64 / 1_000_000.0);
            self.upload_speed = needs_upload.then(|| up as f64 / 1_000_000.0);''',
                      '''            let elapsed = self.network_rate_window.elapsed(Instant::now(), seen.into_iter().map(std::ffi::OsString::from));
            self.download_speed = needs_download.then(|| megabytes_per_second(down, elapsed)).flatten();
            self.upload_speed = needs_upload.then(|| megabytes_per_second(up, elapsed)).flatten();''')
    data=replace_once(data,'            self.download_speed = None;\n            self.upload_speed = None;',
                      '            self.network_rate_window.reset();\n            self.download_speed = None;\n            self.upload_speed = None;')
    data=replace_once(data,'''            self.disks.refresh_disks();
        }

        // NPU''',
                      '''            self.disks.refresh_disks();
        } else {
            self.disks.rate_window.reset();
            self.disks.read = None;
            self.disks.write = None;
        }

        // NPU''')
    main=replace_once(files['src/main.rs'],'mod data;','mod data;\nmod sample_rates;')
    config=replace_once(files['src/config.rs'],'↓{dl_speed}M/s ↑{ul_speed}M/s','↓{dl_speed}MB/s ↑{ul_speed}MB/s')
    return {'src/data/mod.rs':data,'src/main.rs':main,'src/config.rs':config,
            'src/sample_rates.rs':MODULE.read_text(encoding='utf-8')}


def prepare(source,output,apply=False):
    if source.is_symlink():raise ValueError('Symlink source forbidden.')
    source=source.resolve()
    if any(source.is_relative_to(p) for p in (Path('/usr'),Path.home()/'.cargo',Path.home()/'.local',Path.home()/'.var')):
        raise ValueError('Use only isolated source, not installed files/caches.')
    if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=PIN:raise ValueError('Exact Sysinfo HEAD required.')
    if (source/'src/sample_rates.rs').exists() or (source/'src/sample_rates.rs').is_symlink():raise ValueError('Existing rate module refused; prepare a fresh tree.')
    files={}
    for name,digest in ORIGINAL.items():
        path=source/name
        if any(p.is_symlink() for p in (path, *path.parents) if p==source or source in p.parents) or not path.resolve().is_relative_to(source):
            raise ValueError('Symlink/escaped rate source forbidden.')
        blob=subprocess.check_output(['git','-C',str(source),'show','HEAD:'+name])
        if hashlib.sha256(blob).hexdigest()!=digest:raise ValueError('Original Sysinfo Git blob differs.')
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Changed original Sysinfo input bytes; preserve this tree.')
        files[name]=raw.decode('utf-8')
    after=transform(files)
    patch=''.join(''.join(difflib.unified_diff(files.get(name,'').splitlines(True),text.splitlines(True),fromfile='a/'+name if name in files else '/dev/null',tofile='b/'+name)) for name,text in after.items())
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8',newline='\n') as stream:stream.write(patch)
    command=['git','-C',str(source),'-c','core.autocrlf=false','apply']
    subprocess.run(command+['--check',str(output.resolve())],check=True)
    if apply:
        subprocess.run(command+[str(output.resolve())],check=True)
        for name,text in after.items():
            if (source/name).read_bytes()!=text.encode():raise ValueError('Sysinfo rate postimage mismatch.')
    return after


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source',type=Path);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    prepare(args.source,args.output,args.apply)
    print('Prepared exact elapsed-time delta rates; full app/hardware/runtime gates remain open.')
