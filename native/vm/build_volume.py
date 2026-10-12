"""Read-only identity guard for an explicitly approved NEW build-only VM disk.

Not a formatter. Never reuses the installer OS-disk guard or accepts signatures.
Invoke before any private authenticated format command and revalidate immediately.
"""
import re
PRIMARY_SERIAL='VB5fcfe660-4751c2d2'
PRIMARY_BYTES=171798691840
BUILD_BYTES=137438953472


def select_empty_build_disk(layout, serial, root_source):
    if not re.fullmatch(r'VB[0-9a-f]{8}-[0-9a-f]{8}',serial) or serial==PRIMARY_SERIAL:
        raise ValueError('Explicit distinct VirtualBox build-disk serial required.')
    disks=layout.get('blockdevices',[])
    primary=[d for d in disks if d.get('path')=='/dev/sda']
    if (root_source!='/dev/sda2' or len(primary)!=1 or primary[0].get('serial')!=PRIMARY_SERIAL
            or primary[0].get('size')!=PRIMARY_BYTES or primary[0].get('type')!='disk'
            or not any(c.get('path')=='/dev/sda2' and '/' in (c.get('mountpoints') or []) for c in primary[0].get('children',[]))):
        raise ValueError('Original owned OS disk/root identity required; never resize or format it.')
    matches=[d for d in disks if d.get('serial')==serial]
    if len(matches)!=1:raise ValueError('Unique explicitly identified new build disk required.')
    disk=matches[0]
    if (not re.fullmatch(r'/dev/sd[b-z]',disk.get('path','')) or disk.get('type')!='disk'
            or disk.get('size')!=BUILD_BYTES or disk.get('model','').strip()!='VBOX HARDDISK'
            or disk.get('ro') not in (False,0) or disk.get('children')
            or disk.get('fstype') or disk.get('uuid') or any(disk.get('mountpoints') or [])):
        raise ValueError('Build disk must be the exact128GiB writable empty whole VirtualBox disk.')
    return disk['path']
