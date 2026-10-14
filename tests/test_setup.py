"""Appearance assets and recovery tests. Never access the running desktop."""
import base64
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('studio_setup',ROOT/'setup.py')
setup=importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)

def contrast(a,b):
    def lum(s):
        rgb=[int(s[i:i+2],16)/255 for i in (1,3,5)]
        rgb=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in rgb]
        return sum(x*w for x,w in zip(rgb,[.2126,.7152,.0722]))
    lo,hi=sorted([lum(a),lum(b)])
    return (hi+.05)/(lo+.05)

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
    def tearDown(self): self.temp.cleanup()
    def fixture(self):
        file=self.root/'setting'; file.write_text('original')
        file.chmod(0o640)
        target=self.root/'target';target.write_text('target')
        link=self.root/'link';link.symlink_to(target)
        new=self.root/'new'
        before=setup.snapshot([file,link,new])
        setup.atomic(file,'applied')
        link.unlink();link.write_text('replaced link')
        new.write_text('created')
        after=setup.snapshot([file,link,new])
        manifest={'schema':setup.SCHEMA_VERSION,'status':'applied',
                  'roots':[str(file),str(link),str(new)],'before':before,
                  'changed':[str(file),str(link),str(new)],'gsettings':{},
                  'after_hashes':{k:hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest() for k,v in after.items()}}
        backup=self.root/'backup';backup.mkdir()
        setup.save_manifest(backup,manifest)
        return file,link,new,before,backup
    def test_restore_exact_contents_permissions_symlink_and_absent_file(self):
        file,link,new,before,backup=self.fixture()
        with patch.object(setup.time,'sleep'):
            setup.restore(backup)
        self.assertEqual(setup.record(file),before[str(file)])
        self.assertEqual(setup.record(link),before[str(link)])
        self.assertFalse(new.exists())
    def test_restore_protects_changes_made_after_apply(self):
        file,link,new,before,backup=self.fixture()
        file.write_text('user edit')
        with self.assertRaisesRegex(RuntimeError,'changed since apply'):
            setup.restore(backup)
        self.assertEqual(file.read_text(),'user edit')
        self.assertTrue(new.exists())
        with patch.object(setup.time,'sleep'):
            setup.restore(backup,force=True)
        self.assertEqual(file.read_text(),'original')
    def test_interrupted_apply_recomputes_changed_files(self):
        file,link,new,before,backup=self.fixture()
        manifest=json.loads((backup/'manifest.json').read_text())
        manifest.update(status='applying',changed=[],after_hashes={})
        setup.save_manifest(backup,manifest)
        with patch.object(setup.time,'sleep'):
            setup.restore(backup)
        self.assertEqual(file.read_text(),'original')
        self.assertTrue(link.is_symlink())
        self.assertFalse(new.exists())
    def test_qt_stylesheet_reapplication_preserves_other_preferences(self):
        text='[Appearance]\ncustom_palette=true\n\n[Interface]\nstylesheets=/existing/style.qss\nmenus_have_icons=false\n\n[Fonts]\ngeneral=test\n'
        first=setup.ini_stylesheet(text,Path('/new/glass.qss'))
        self.assertEqual(first,setup.ini_stylesheet(first,Path('/new/glass.qss')))
        for value in ['custom_palette=true','/existing/style.qss','menus_have_icons=false','general=test']:
            self.assertIn(value,first)

class AssetTests(unittest.TestCase):
    def test_zed_light_syntax_is_readable(self):
        theme=json.loads((ROOT/'studio-light-zed.json').read_text())['themes'][0]
        self.assertEqual(theme['appearance'],'light')
        for name,attrs in theme['style']['syntax'].items():
            if attrs.get('color'):
                self.assertGreaterEqual(contrast(attrs['color'],'#FFFFFF'),4.5,name)
    def test_light_text_focus_and_chrome_contrast(self):
        light,dark=setup.TOKENS['palette']['light'],setup.TOKENS['palette']['dark']
        pairs=[(light['ink'],light['paper']),(light['ink2'],light['paper']),(light['accent'],light['paper']),
               ('#FFFFFF',light['accent']),(light['ink'],light['fill']),(light['ink'],light['paper2']),
               (dark['ink'],dark['paper']),(dark['ink2'],dark['paper']),(dark['accent'],dark['paper']),
               (dark['ink'],dark['paper3'])]
        for palette in (light,dark):
            pairs += [(palette[role],palette['paper']) for role in ['success','warning','destructive']]
        for fg,bg in pairs:
            self.assertGreaterEqual(contrast(fg,bg),4.5,(fg,bg))
    def test_ghostty_palette_is_readable_on_light_background(self):
        import re
        text=(ROOT/'Studio Light.ghostty').read_text()
        colors=re.findall(r'^palette = \d+=(#[0-9A-Fa-f]{6})$',text,re.M)
        self.assertEqual(len(colors),16)
        for color in colors: self.assertGreaterEqual(contrast(color,'#F5F5F7'),4.5,color)
    def test_approved_dark_ghostty_palette_and_monospace_survive(self):
        import re
        text=(ROOT/'Studio Dark.ghostty').read_text()
        colors=re.findall(r'^palette = \d+=(#[0-9A-Fa-f]{6})$',text,re.M)
        self.assertEqual(len(colors),16)
        for color in colors: self.assertGreaterEqual(contrast(color,'#101214'),4.5,color)
        appearance=(ROOT/'appearance.ghostty').read_text()
        for value in ['theme = Studio Dark','background-opacity = 1','font-family = iA Writer Mono S']:
            self.assertIn(value,appearance)
    def test_fonts_have_pinned_license_and_original_file_checksums(self):
        files=setup.font_assets()
        self.assertEqual(len([p for p,_ in files if p.suffix=='.ttf']),10)
        for family in ['archivo','instrumentserif']:
            self.assertIn('SIL OPEN FONT LICENSE',(ROOT/'fonts'/family/'OFL.txt').read_text())

class TypographyTests(unittest.TestCase):
    def test_caffeine_private_font_is_conditional_on_an_installed_flatpak(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);data=root/'data'
            stale=root/'.var/app'/setup.CAFFEINE_FLATPAK_ID/'config'
            stale.mkdir(parents=True)
            with patch.object(setup,'DATA',data),patch.object(setup.Path,'home',return_value=root):
                self.assertEqual(setup.private_flatpak_font_roots(),[])
                (data/'flatpak/app'/setup.CAFFEINE_FLATPAK_ID).mkdir(parents=True)
                target=stale/'cosmic/com.system76.CosmicTk/v1/interface_font'
                self.assertEqual(setup.private_flatpak_font_roots(),[target])
                self.assertFalse(target.exists())

    def test_caffeine_font_apply_backup_absence_and_later_edit_protection(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);config=root/'config';data=root/'data';cosmic=config/'cosmic'
            (data/'flatpak/app'/setup.CAFFEINE_FLATPAK_ID).mkdir(parents=True)
            target=root/'.var/app'/setup.CAFFEINE_FLATPAK_ID/'config/cosmic/com.system76.CosmicTk/v1/interface_font'
            unrelated=target.parent/'monospace_font';unrelated.parent.mkdir(parents=True)
            unrelated.write_text('personal monospace')
            def run(args,**kwargs):
                if args[0]=='fc-match': return SimpleNamespace(returncode=0,stdout=args[-1],stderr='')
                if args[0]=='gsettings' and args[1]=='get': return SimpleNamespace(returncode=0,stdout="'Old 11'\n",stderr='')
                return SimpleNamespace(returncode=0,stdout='',stderr='')
            with patch.multiple(setup,CONFIG=config,DATA=data,COSMIC=cosmic),patch.object(setup.Path,'home',return_value=root),patch.object(setup,'run',side_effect=run),patch.object(setup.time,'sleep'):
                roots=setup.typography_roots();before=setup.snapshot(roots)
                self.assertIn(target,roots)
                self.assertNotIn(str(target),before)
                setup.apply_typography()
                self.assertEqual(target.read_text(),setup.INTERFACE_FONT)
                check=next(c for c in setup.verify_typography() if c['check']=='Caffeine sandbox Archivo interface font')
                self.assertEqual(check['status'],'PASS')
                after=setup.snapshot(roots)
                changed=sorted(k for k in before.keys()|after.keys() if before.get(k)!=after.get(k))
                backup=root/'backup';backup.mkdir()
                setup.save_manifest(backup,{'schema':setup.SCHEMA_VERSION,'status':'applied','roots':[str(p) for p in roots],
                                           'before':before,'changed':changed,'gsettings':{},
                                           'after_hashes':{k:hashlib.sha256(json.dumps(after.get(k),sort_keys=True).encode()).hexdigest() for k in changed}})
                target.write_text('later personal font')
                with self.assertRaisesRegex(RuntimeError,'changed since apply'):
                    setup.restore(backup)
                self.assertEqual(target.read_text(),'later personal font')
                setup.restore(backup,force=True)
                self.assertFalse(target.exists())
                self.assertEqual(unrelated.read_text(),'personal monospace')

    def test_typography_rejects_extra_cli_argument_before_apply(self):
        with patch.object(setup.sys,'argv',['setup.py','typography','preview']),patch.object(setup,'apply_typography_only') as apply:
            with self.assertRaises(SystemExit) as error: setup.main()
            self.assertEqual(error.exception.code,2)
            apply.assert_not_called()
    def test_ini_updates_preserve_scaling_and_unrelated_controls(self):
        text='; personal settings\n[Fonts]\ngeneral=Instrument Sans,12.5,-1,5,50,0,0,0,0,0\nfixed=iA Writer Mono S,11\n[Interface]\nmenus_have_icons=false\n'
        updated=setup.ini_value(text,'Fonts','general',setup.qt_font_value(text,'11'))
        self.assertIn('general=Archivo,12.5,-1,5,50,0,0,0,0,0',updated)
        self.assertIn('fixed=iA Writer Mono S,11',updated)
        self.assertIn('menus_have_icons=false',updated)
        self.assertEqual(updated,setup.ini_value(updated,'Fonts','general',setup.qt_font_value(updated,'11')))
        self.assertEqual(setup.font_size("'Instrument Sans 12.5'"),'12.5')
    def test_typography_install_restores_originals_and_retains_toolkit_preferences(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);config=root/'config';data=root/'data';cosmic=config/'cosmic'
            gtk=config/'gtk-4.0';gtk.mkdir(parents=True)
            (gtk/'settings.ini').write_text('[Settings]\ngtk-font-name=Old 12.5\ngtk-cursor-theme-size=32\ngtk-icon-theme-name=Studio Dock\n')
            tk=cosmic/'com.system76.CosmicTk/v1';tk.mkdir(parents=True)
            (tk/'icon_theme').write_text('"Studio Dock"')
            (tk/'monospace_font').write_text('(family: "iA Writer Mono S", weight: Normal)')
            icon_before=setup.record(tk/'icon_theme');mono_before=setup.record(tk/'monospace_font')
            (gtk/'gtk.css').write_text('/* personal stylesheet */\nlabel { color: red; }\n')
            frames=config/'studio-light/window-frames.css';frames.parent.mkdir();frames.write_bytes((ROOT/'window-frames.css').read_bytes())
            (frames.parent/'typography-gtk.css').write_bytes((ROOT/'typography-gtk.css').read_bytes())
            palette=gtk/'cosmic';palette.mkdir()
            for mode in ['light','dark']: (palette/f'{mode}.css').write_text('@define-color window_bg_color #fff;\n')
            qt=config/'qt6ct';qt.mkdir()
            (qt/'qt6ct.conf').write_text('[Fonts]\ngeneral=Old,12.5,-1,5,50,0,0,0,0,0\nfixed=iA Writer Mono S,11\n[Interface]\nstylesheets=/personal.qss\n')
            zed=config/'zed';zed.mkdir()
            (zed/'settings.json').write_text('{"theme":"Studio Light","ui_font_size":14.5,"terminal":{"font_family":"iA Writer Mono S"}}')
            def run(args,**kwargs):
                if args[0]=='fc-match': return SimpleNamespace(returncode=0,stdout=args[-1],stderr='')
                if args[0]=='gsettings' and args[1]=='get': return SimpleNamespace(returncode=0,stdout="'Old 12.5'\n",stderr='')
                if args[0]=='gsettings' and args[1]=='set':
                    # Model a native sync discarding managed imports after a font update.
                    for path in palette.glob('*.css'):
                        path.write_text(re.sub(r'/\* BEGIN STUDIO WINDOW FRAMES \*/.*?/\* END STUDIO WINDOW FRAMES \*/', '',path.read_text(),flags=re.S))
                return SimpleNamespace(returncode=0,stdout='',stderr='')
            with patch.multiple(setup,CONFIG=config,DATA=data,COSMIC=cosmic),patch.object(setup,'run',side_effect=run),patch.object(setup.time,'sleep'):
                setup.apply_window_frame_imports()
                roots=setup.typography_roots();before=setup.snapshot(roots)
                setup.apply_typography();first=setup.snapshot(roots)
                setup.apply_typography();after=setup.snapshot(roots)
                self.assertEqual(first,after)
                self.assertIn('gtk-font-name=Archivo 12.5',(gtk/'settings.ini').read_text())
                self.assertIn('gtk-cursor-theme-size=32',(gtk/'settings.ini').read_text())
                self.assertIn('gtk-icon-theme-name=Studio Dock',(gtk/'settings.ini').read_text())
                self.assertEqual(setup.record(tk/'icon_theme'),icon_before)
                self.assertEqual(setup.record(tk/'monospace_font'),mono_before)
                self.assertIn('/personal.qss',(qt/'qt6ct.conf').read_text())
                self.assertEqual(json.loads((zed/'settings.json').read_text())['ui_font_size'],14.5)
                self.assertEqual(json.loads((zed/'settings.json').read_text())['terminal']['font_family'],'iA Writer Mono S')
                for path in palette.glob('*.css'):
                    self.assertIn(path,roots)
                    self.assertEqual(path.read_text().count('BEGIN STUDIO WINDOW FRAMES'),1)
                    self.assertEqual(path.read_text().count('BEGIN STUDIO TYPOGRAPHY'),1)
                    self.assertIn(str(config/'studio-light/typography-gtk.css'),path.read_text())
                changed=sorted(k for k in before.keys()|after.keys() if before.get(k)!=after.get(k))
                backup=root/'backup';backup.mkdir()
                setup.save_manifest(backup,{'schema':setup.SCHEMA_VERSION,'status':'applied','roots':[str(p) for p in roots],
                                          'before':before,'changed':changed,'gsettings':{},
                                          'after_hashes':{k:hashlib.sha256(json.dumps(after.get(k),sort_keys=True).encode()).hexdigest() for k in changed}})
                setup.restore(backup)
                self.assertEqual(setup.snapshot(roots),before)
    def test_corrupt_font_asset_fails_before_any_install(self):
        with tempfile.TemporaryDirectory() as directory:
            package=Path(directory)
            (package/'fonts').mkdir()
            (package/'fonts/bad.ttf').write_bytes(b'changed')
            (package/'fonts/manifest.json').write_text(json.dumps({'families':{'Archivo':[{'file':'bad.ttf','sha256':'bad'}]}}))
            with patch.object(setup,'PACKAGE',package),patch.object(setup,'atomic') as atomic:
                with self.assertRaisesRegex(RuntimeError,'checksum mismatch'): setup.apply_typography()
                atomic.assert_not_called()
    def test_unsafe_font_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            package=Path(directory);(package/'fonts').mkdir()
            (package/'fonts/manifest.json').write_text(json.dumps({'families':{'Archivo':[{'file':'../escape.ttf','sha256':'bad'}]}}))
            with patch.object(setup,'PACKAGE',package):
                with self.assertRaisesRegex(RuntimeError,'Unsafe'): setup.font_assets()

class ShellTests(unittest.TestCase):
    def test_native_backdrop_level_verification_rejects_disabled_builder(self):
        with tempfile.TemporaryDirectory() as directory:
            cosmic=Path(directory)
            for group,settings in [('Dock',setup.DOCK),('Panel',setup.PANEL)]:
                root=cosmic/f'com.system76.CosmicPanel.{group}/v1';root.mkdir(parents=True)
                for key,value in settings.items(): (root/key).write_text(value)
            for mode in ['Light','Dark']:
                for suffix in ['','.Builder']:
                    root=cosmic/f'com.system76.CosmicTheme.{mode}{suffix}/v2';root.mkdir(parents=True)
                    for key,value in {'frosted':setup.SHELL_FROSTED,'frosted_panel':'true','frosted_applets':'true','frosted_system_interface':'true','frosted_windows':'false','alpha_map':'(medium: 0.90,)'}.items():
                        (root/key).write_text(value)
                    (root/'corner_radii').write_text('('+''.join(f'radius_{k}: ({v:.1f}, {v:.1f}, {v:.1f}, {v:.1f}),' for k,v in setup.CORNER_RADII.items())+')')
            with patch.object(setup,'COSMIC',cosmic):
                self.assertFalse(any(check['status']=='FAIL' for check in setup.verify_shell()))
                (cosmic/'com.system76.CosmicTheme.Dark.Builder/v2/frosted').write_text('None')
                failed=[check for check in setup.verify_shell() if check['status']=='FAIL']
                self.assertEqual([check['check'] for check in failed],['Dark.Builder lowest nonzero native backdrop level'])

    def test_native_sync_keeps_custom_toolkit_styles_and_exact_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);config=root/'config';cosmic=config/'cosmic';data=root/'data';package=root/'package'
            package.mkdir();backups=package/'backups'
            favorites=cosmic/'com.system76.CosmicAppList/v1/favorites';favorites.parent.mkdir(parents=True);favorites.write_text('["brave", "ghostty"]')
            font=cosmic/'com.system76.CosmicTk/v1/interface_font';font.parent.mkdir(parents=True);font.write_text(setup.INTERFACE_FONT)
            gtk=config/'gtk-4.0';gtk.mkdir()
            (gtk/'gtk.css').write_text('/* GENERATED BY COSMIC */\n@define-color window_bg_color #fff;\n/* custom */\n@import url("/personal.css");\n')
            frames=config/'studio-light/window-frames.css';frames.parent.mkdir();frames.write_bytes((ROOT/'window-frames.css').read_bytes())
            (frames.parent/'typography-gtk.css').write_bytes((ROOT/'typography-gtk.css').read_bytes())
            palette=gtk/'cosmic';palette.mkdir()
            for mode in ['light','dark']: (palette/f'{mode}.css').write_text('@define-color window_bg_color #fff;\n')
            qt=config/'qt6ct';qt.mkdir()
            (qt/'qt6ct.conf').write_text('[Interface]\nstylesheets=/personal.qss, /typography.qss\n[Fonts]\ngeneral=Archivo,12.5,-1,5,50,0,0,0,0,0\n')
            def run(args,**kwargs):
                self.assertNotIn(args[0],['blender','pgrep'])
                if args[0]=='cosmic-settings':
                    (gtk/'gtk.css').write_text('/* GENERATED BY COSMIC */\n@define-color window_bg_color #eee;\n')
                    for path in palette.glob('*.css'): path.write_text('@define-color window_bg_color #eee;\n')
                    (qt/'qt6ct.conf').write_text('[Appearance]\ncustom_palette=true\n')
                    return SimpleNamespace(returncode=0,stdout='Successfully imported',stderr='')
                return SimpleNamespace(returncode=0,stdout="'original'\n",stderr='')
            with patch.multiple(setup,CONFIG=config,COSMIC=cosmic,DATA=data,PACKAGE=package,BACKUPS=backups),patch.object(setup,'prepare'),patch.object(setup,'preflight') as preflight,patch.object(setup,'run',side_effect=run),patch.object(setup.time,'sleep'),patch.object(setup,'verify_shell',return_value=[{'status':'PASS'}]):
                setup.apply_window_frame_imports()
                roots=setup.shell_roots();before=setup.snapshot(roots)
                setup.apply_shell()
                preflight.assert_called_once_with(include_apps=False)
                self.assertIn('@define-color window_bg_color #eee;',(gtk/'gtk.css').read_text())
                self.assertEqual((gtk/'gtk.css').read_text().count('/personal.css'),1)
                self.assertIn('stylesheets=/personal.qss, /typography.qss',(qt/'qt6ct.conf').read_text())
                self.assertIn('general=Archivo,12.5,-1,5,50,0,0,0,0,0',(qt/'qt6ct.conf').read_text())
                self.assertEqual(font.read_text(),setup.INTERFACE_FONT)
                for path in palette.glob('*.css'):
                    self.assertEqual(path.read_text().count('BEGIN STUDIO WINDOW FRAMES'),1)
                    self.assertEqual(path.read_text().count('BEGIN STUDIO TYPOGRAPHY'),1)
                backup=Path((package/'latest-shell-backup.txt').read_text().strip())
                manifest=json.loads((backup/'manifest.json').read_text())
                self.assertEqual(manifest['profile'],'shell')
                setup.restore(backup)
                self.assertEqual(setup.snapshot(roots),before)

class WindowFrameTests(unittest.TestCase):
    def test_shared_native_palette_links_preserve_settings_and_restore_exactly(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);config=root/'config';cosmic=config/'cosmic';package=root/'package'
            package.mkdir();backups=package/'backups';data=root/'data'
            (package/'window-frames.css').write_bytes((ROOT/'window-frames.css').read_bytes())
            palette=config/'gtk-4.0/cosmic';palette.mkdir(parents=True)
            light=palette/'light.css';dark=palette/'dark.css'
            light.write_text('@define-color window_bg_color #fff;\n/* custom */\n@import url("/typography.css");\n')
            light.chmod(0o640);dark.write_text('@define-color window_bg_color #000;\n')
            for toolkit in ['gtk-3.0','gtk-4.0']:
                gtk=config/toolkit;gtk.mkdir(exist_ok=True)
                (gtk/'gtk.css').symlink_to(light)
                (gtk/'settings.ini').write_text('[Settings]\ngtk-font-name=Archivo 12.5\ngtk-icon-theme-name=Studio Glass\n')
            dock=cosmic/'com.system76.CosmicPanel.Dock/v1';dock.mkdir(parents=True)
            (dock/'border_width').write_text('1.0')
            icons=data/'icons';icons.mkdir(parents=True);(icons/'conflux.svg').write_text('original Conflux')
            with patch.multiple(setup,CONFIG=config,COSMIC=cosmic,DATA=data,PACKAGE=package,BACKUPS=backups),patch.object(setup,'run',side_effect=AssertionError('Frame action must not invoke external tools')),patch.object(setup.time,'sleep'):
                roots=setup.window_frame_roots();before=setup.snapshot(roots)
                setup.apply_window_frames_only()
                backup=Path((package/'latest-window-frames-backup.txt').read_text().strip())
                manifest=json.loads((backup/'manifest.json').read_text())
                self.assertEqual(manifest['profile'],'window_frames')
                self.assertEqual(set(manifest['changed']),{str(light),str(dark),str(config/'studio-light/window-frames.css')})
                self.assertTrue(all(check['status']!='FAIL' for check in setup.verify_window_frames(backup)))
                for path in [light,dark]: self.assertEqual(path.read_text().count('BEGIN STUDIO WINDOW FRAMES'),1)
                self.assertIn('@import url("/typography.css");',light.read_text())
                self.assertEqual((dock/'border_width').read_text(),'1.0')
                self.assertEqual((icons/'conflux.svg').read_text(),'original Conflux')
                setup.apply_window_frames_only()
                second=Path((package/'latest-window-frames-backup.txt').read_text().strip())
                self.assertEqual(json.loads((second/'manifest.json').read_text())['changed'],[])
                setup.restore(backup)
                self.assertEqual(setup.snapshot(roots),before)
                self.assertTrue((config/'gtk-3.0/gtk.css').is_symlink())
                self.assertEqual(light.stat().st_mode & 0o777,0o640)

    def test_verification_failure_rolls_back_only_outer_frame_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);config=root/'config';package=root/'package';package.mkdir()
            (package/'window-frames.css').write_bytes((ROOT/'window-frames.css').read_bytes())
            gtk=config/'gtk-3.0';gtk.mkdir(parents=True);(gtk/'gtk.css').write_text('original CSS')
            with patch.multiple(setup,CONFIG=config,COSMIC=config/'cosmic',PACKAGE=package,BACKUPS=package/'backups'),patch.object(setup,'verify_window_frames',return_value=[{'status':'FAIL'}]),patch.object(setup.time,'sleep'):
                roots=setup.window_frame_roots();before=setup.snapshot(roots)
                with self.assertRaisesRegex(RuntimeError,'Outer-frame verification failed'):
                    setup.apply_window_frames_only()
                self.assertEqual(setup.snapshot(roots),before)

if __name__=='__main__': unittest.main()


class DesignTests(unittest.TestCase):
    """The imported desktop design, as committed native themes and assets."""
    def test_committed_native_themes_match_design_palette(self):
        for mode in ['Light','Dark']:
            text=(ROOT/f'studio-{mode.lower()}.ron').read_text()
            for field,color in setup.theme_colors(mode).items():
                self.assertIn(f'    {field}: Some("{color}FF"),',text,(mode,field))
    def test_shell_geometry_follows_design(self):
        self.assertEqual(setup.DOCK['border_radius'],str(setup.TOKENS['dock']['radius']))
        self.assertEqual(setup.PANEL['border_radius'],str(setup.TOKENS['menu_bar']['radius']))
        self.assertEqual(setup.PANEL['margin'],str(setup.TOKENS['menu_bar']['margin']))
        self.assertEqual(setup.DOCK['margin'],str(setup.TOKENS['dock']['margin']))
    def test_dock_indicator_is_monochrome_and_tooltip_compact(self):
        patch=(ROOT/'native/dock-icons/compact-icons.patch').read_text()
        added='\n'.join(l for l in patch.splitlines() if l.startswith('+'))
        self.assertIn('Color::WHITE',added); self.assertIn('Color::BLACK',added)
        self.assertNotIn('accent_color()',added)
        self.assertIn('-                        Some(Background::Color(theme.cosmic().accent_color().into()))',patch)
        bars=setup.TOKENS['dock']['indicator']
        self.assertIn(f"Some([{bars['running']:.1f}, {bars['multiple']:.1f}, {bars['focused']:.1f}])",added)
        tooltip=(ROOT/'native/dock-icons/prepare_tooltip.py').read_text()
        self.assertIn(f".size({setup.TOKENS['tooltip']['size']})",tooltip)
        self.assertIn('Wrapping::None',tooltip)
    def test_rocker_assets_cover_every_role_shape_and_state(self):
        art=ROOT/'icons/window-controls/svg'
        tokens=json.loads((ROOT/'icons/window-controls/tokens.json').read_text())
        for state in tokens['states']:
            for role in tokens['colors']:
                for shape in tokens['shapes']:
                    svg=(art/state/f'{role}-{shape}.svg').read_text()
                    self.assertIn('width="22" height="24"',svg)
                    self.assertEqual('stroke-linecap' in svg,state in tokens['glyph']['visible'],(state,role,shape))
                    self.assertEqual('<rect y="5" width="1"' in svg,shape in ('middle','right'),(role,shape))
        for role,color in setup.TOKENS['window_controls']['colors'].items():
            self.assertEqual(tokens['colors'][role].upper(),color)
    def test_toolkit_rocker_styles_reference_existing_art(self):
        art=ROOT/'icons/window-controls/svg'
        for name in ['gtk.css','obsidian.css']:
            text=(ROOT/'native/window-controls'/name).read_text()
            for path in re.findall(r'assets/([a-z]+/[a-z-]+\.svg)',text):
                self.assertTrue((art/path).is_file(),(name,path))
        gtk=(ROOT/'native/window-controls/gtk.css').read_text()
        for selector in [':only-child',':first-child',':last-child','windowcontrols { border-spacing: 0; }']:
            self.assertIn(selector,gtk)
