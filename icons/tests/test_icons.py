import importlib.util,sys,unittest,tempfile,json,xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import install

class Icons(unittest.TestCase):
 @unittest.skipUnless((ROOT/'Studio Objects/index.theme').is_file(), 'Local Blender export is not present')
 def test_every_custom_lookup_resolves_to_self_contained_svg(self):
  coverage=json.loads((ROOT/'coverage.json').read_text())
  for name,row in coverage['icons'].items():
   paths=list((ROOT/'Studio Objects/scalable').rglob(name+'.svg'));self.assertEqual(len(paths),1,name)
   tree=ET.parse(paths[0]);ids={x.get('id') for x in tree.iter() if x.get('id')}
   self.assertTrue(tree.getroot().get('viewBox'))
   for node in tree.iter():
    for key,value in node.attrib.items():
     if key.endswith('href'):
      self.assertTrue(value.startswith(('#','data:')),name+': external dependency '+value)
      if value.startswith('#'):self.assertIn(value[1:],ids,name)
 @unittest.skipUnless((ROOT/'Studio Objects/index.theme').is_file(), 'Local Blender export is not present')
 def test_theme_declares_each_icon_directory(self):
  import configparser
  c=configparser.ConfigParser();c.read(ROOT/'Studio Objects/index.theme')
  dirs=c['Icon Theme']['Directories'].split(',')
  for path in (ROOT/'Studio Objects').rglob('*.svg'):
   self.assertIn(str(path.parent.relative_to(ROOT/'Studio Objects')),dirs)
  self.assertNotIn('cursors',dirs)
 def test_ini_preserves_other_preferences_and_sections(self):
  old='[Settings]\n# personal font\ngtk-font-name=Example 11\ngtk-cursor-theme-name=breeze_cursors\n[Other]\ngtk-icon-theme-name=keep\n'
  new=install.ini(old,'Settings','gtk-icon-theme-name','Studio Objects')
  self.assertIn('# personal font\ngtk-font-name=Example 11\ngtk-cursor-theme-name=breeze_cursors\n',new)
  self.assertIn('[Other]\ngtk-icon-theme-name=keep\n',new)
  self.assertEqual(install.ini(new,'Settings','gtk-icon-theme-name','Studio Objects'),new)
 def test_ini_missing_final_newline(self):
  out=install.ini('[Settings]\npersonal=true','Settings','gtk-icon-theme-name','Studio Objects')
  self.assertIn('personal=true\ngtk-icon-theme-name=',out)
 def test_launcher_override_preserves_wayland_exec_and_actions(self):
  old='[Desktop Entry]\nName=Renderer\nExec=/opt/application --ozone-platform=wayland --enable-features=WaylandWindowDecorations %U\nIcon=/opt/application/icon.png\nStartupWMClass=Application\nActions=New;\n\n[Desktop Action New]\nExec=/opt/application --new\nIcon=action-specific\n'
  changed=install.desktop_icon(old,'studio-app')
  self.assertEqual(changed,old.replace('Icon=/opt/application/icon.png','Icon=studio-app'))
  self.assertEqual(install.desktop_icon(changed,'studio-app'),changed)
 def test_launcher_override_rejects_wrong_section(self):
  with self.assertRaises(RuntimeError):install.desktop_icon('[Desktop Action New]\nIcon=keep\n','studio-app')
 def test_launcher_override_preserves_crlf(self):
  source='[Desktop Entry]\r\nExec=app %U\r\nIcon=/old.png\r\n'
  self.assertEqual(install.desktop_icon(source,'studio-app'),source.replace('/old.png','studio-app'))
 def test_restore_retains_bytes_modes_and_absence(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);old=root/'old';new=root/'created';old.write_bytes(b'original\x00bytes');old.chmod(0o640)
   before={str(old):install.record(old),str(new):None};old.write_text('theme');new.write_text('added')
   manifest=root/'backup.json';manifest.write_text(json.dumps({'before':before,'after':{str(old):install.record(old),str(new):install.record(new)},'gsettings':"'Old theme'"}))
   with patch.object(install,'run',return_value="'Studio Objects'"):install.restore(manifest)
   self.assertEqual(old.read_bytes(),b'original\x00bytes');self.assertEqual(old.stat().st_mode&0o777,0o640);self.assertFalse(new.exists())
 def test_restore_rejects_later_user_edits_before_any_write(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);one=root/'one';two=root/'two';one.write_text('new');two.write_text('new')
   before={str(one):None,str(two):None};after={str(one):install.record(one),str(two):install.record(two)}
   two.write_text('personal edit');m=root/'backup.json';m.write_text(json.dumps({'before':before,'after':after,'gsettings':"'Conflux'"}))
   with self.assertRaises(RuntimeError):install.restore(m)
   self.assertEqual(one.read_text(),'new');self.assertEqual(two.read_text(),'personal edit')
 @unittest.skipUnless((ROOT/'Studio Objects/index.theme').is_file(), 'Local Blender export is not present')
 def test_symbolic_states_are_not_generic_aliases(self):
  d=ROOT/'Studio Objects/scalable/actions'
  self.assertNotEqual((d/'audio-volume-muted-symbolic.svg').read_bytes(),(d/'audio-volume-high-symbolic.svg').read_bytes())
  self.assertNotEqual((d/'battery-level-10-symbolic.svg').read_bytes(),(d/'battery-level-90-symbolic.svg').read_bytes())
  self.assertNotEqual((d/'window-close-symbolic.svg').read_bytes(),(d/'window-minimize-symbolic.svg').read_bytes())
if __name__=='__main__':unittest.main()
