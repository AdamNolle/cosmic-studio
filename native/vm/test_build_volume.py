import copy,unittest
from build_volume import select_empty_build_disk,PRIMARY_SERIAL,PRIMARY_BYTES,BUILD_BYTES
SERIAL='VBb58f2faf-407eedd1'
def layout():
 return {'blockdevices':[{'path':'/dev/sda','serial':PRIMARY_SERIAL,'size':PRIMARY_BYTES,'type':'disk','children':[{'path':'/dev/sda2','mountpoints':['/']}]},{'path':'/dev/sdb','serial':SERIAL,'size':BUILD_BYTES,'type':'disk','model':'VBOX HARDDISK','ro':False,'fstype':None,'uuid':None,'mountpoints':[None]}]}
class BuildVolumeGuard(unittest.TestCase):
 def test_only_exact_new_disk_selected(self):self.assertEqual(select_empty_build_disk(layout(),SERIAL,'/dev/sda2'),'/dev/sdb')
 def test_os_disk_root_or_ambiguous_identity_refused(self):
  for change in ('serial','size','root','duplicate','primary-request'):
   data=layout();serial=SERIAL;root='/dev/sda2'
   if change=='serial':data['blockdevices'][0]['serial']='different'
   if change=='size':data['blockdevices'][0]['size']+=1
   if change=='root':root='/dev/sdb'
   if change=='duplicate':data['blockdevices'].append(copy.deepcopy(data['blockdevices'][1]))
   if change=='primary-request':serial=PRIMARY_SERIAL
   with self.subTest(change=change),self.assertRaises(ValueError):select_empty_build_disk(data,serial,root)
 def test_partition_signature_mount_readonly_or_wrong_device_refused(self):
  for key,value in [('children',[{'path':'/dev/sdb1'}]),('fstype','ext4'),('uuid','existing'),('mountpoints',['/mnt/old']),('ro',True),('size',BUILD_BYTES-1),('path','/dev/sda'),('model','other'),('type','crypt')]:
   data=layout();data['blockdevices'][1][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):select_empty_build_disk(data,SERIAL,'/dev/sda2')
if __name__=='__main__':unittest.main()
