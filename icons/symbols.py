"""Pixel-aligned original control glyphs. Semantic aliases never guess by substring."""
from pathlib import Path
import json
P='<path d="{}"/>'
GLYPHS={
'close':P.format('m5 5 14 14M19 5 5 19'),
'minus':P.format('M5 12h14'),
'plus':P.format('M5 12h14M12 5v14'),
'check':P.format('m4 12 5 5L20 6'),
'menu':P.format('M4 6h16M4 12h16M4 18h16'),
'more':'<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',
'left':P.format('m15 5-7 7 7 7'),
'right':P.format('m9 5 7 7-7 7'),
'up':P.format('m5 15 7-7 7 7'),
'down':P.format('m5 9 7 7 7-7'),
'search':'<circle cx="10" cy="10" r="6"/>'+P.format('m15 15 6 6'),
'folder':P.format('M3 6h7l2 3h9v11H3ZM3 6V4h7l2 2'),
'home':P.format('m2 11 10-8 10 8M5 9v12h5v-7h4v7h5V9'),
'trash':P.format('M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7m4-7v7'),
'document':P.format('M5 2h9l5 5v15H5ZM14 2v6h5M8 12h8m-8 4h6'),
'copy':P.format('M8 8h13v13H8ZM4 16H2V2h14v2'),
'cut':'<circle cx="6" cy="17" r="4"/><circle cx="18" cy="17" r="4"/>'+P.format('m8 14 12-12M16 14 4 2'),
'paste':P.format('M8 5H4v16h16V5h-4M8 3h8v5H8Z'),
'save':P.format('M3 3h15l3 3v15H3ZM7 3v6h9V3M7 21v-8h10v8'),
'undo':P.format('M3 11h10a6 6 0 0 1 0 12M3 11l5-5M3 11l5 5'),
'redo':P.format('M21 11H11a6 6 0 0 0 0 12M21 11l-5-5M21 11l-5 5'),
'refresh':P.format('M3 10a9 9 0 0 1 16-4l2 3M21 9V3m0 6h-6M21 14A9 9 0 0 1 5 18l-2-3M3 15v6m0-6h6'),
'power':P.format('M12 2v10M6 5a9 9 0 1 0 12 0'),
'lock':'<rect x="5" y="10" width="14" height="12" rx="2"/>'+P.format('M8 10V6a4 4 0 0 1 8 0v4M12 15v3'),
'unlock':'<rect x="5" y="10" width="14" height="12" rx="2"/>'+P.format('M8 10V6a4 4 0 0 1 8 0M12 15v3'),
'brightness':'<circle cx="12" cy="12" r="4"/>'+P.format('M12 1v3m0 16v3M1 12h3m16 0h3M4 4l2 2m12 12 2 2M4 20l2-2M18 6l2-2'),
'bluetooth':P.format('m6 5 13 12-7 5V2l7 5L6 19'),
'wifi':P.format('M2 7a16 16 0 0 1 20 0M5 11a11 11 0 0 1 14 0M8 15a6 6 0 0 1 8 0')+'<circle cx="12" cy="20" r="1"/>',
'volume':P.format('M2 9h4l6-5v16l-6-5H2ZM16 8a6 6 0 0 1 0 8M19 4a11 11 0 0 1 0 16'),
'muted':P.format('M2 9h4l6-5v16l-6-5H2ZM16 8l6 8M22 8l-6 8'),
'microphone':'<rect x="9" y="2" width="6" height="13" rx="3"/>'+P.format('M5 10v2a7 7 0 0 0 14 0v-2M12 19v4M8 23h8'),
'headphones':P.format('M3 14V11a9 9 0 0 1 18 0v3M3 12h4v9H3Zm14 0h4v9h-4Z'),
'play':P.format('m7 3 14 9-14 9Z'),
'pause':P.format('M6 3h3v18H6Zm9 0h3v18h-3Z'),
'stop':P.format('M4 4h16v16H4Z'),
'next':P.format('m3 3 13 9-13 9ZM20 3v18'),
'previous':P.format('m21 3-13 9 13 9ZM4 3v18'),
'record':'<circle cx="12" cy="12" r="8"/>',
'apps':P.format('M3 3h6v6H3Zm12 0h6v6h-6ZM3 15h6v6H3Zm12 0h6v6h-6Z'),
'workspaces':P.format('M2 3h14v13H2ZM20 7h2v15H7v-2'),
'fullscreen':P.format('M2 9V2h7M15 2h7v7M22 15v7h-7M9 22H2v-7'),
'restore':P.format('M3 8h13v13H3ZM8 4V2h14v14h-2'),
'monitor':P.format('M2 3h20v14H2ZM12 17v5M7 22h10'),
'keyboard':P.format('M2 5h20v15H2ZM5 9h1m3 0h1m3 0h1m3 0h1M5 13h1m3 0h1m3 0h1m3 0h1M7 17h10'),
'network':P.format('M9 2h6v6H9ZM2 16h6v6H2Zm14 0h6v6h-6ZM12 8v4M5 16v-4h14v4'),
'info':'<circle cx="12" cy="12" r="10"/>'+P.format('M12 11v7')+'<circle cx="12" cy="7" r=".6"/>',
'warning':P.format('m12 2 11 20H1ZM12 9v6')+'<circle cx="12" cy="18" r=".6"/>',
'error':'<circle cx="12" cy="12" r="10"/>'+P.format('m8 8 8 8M16 8l-8 8'),
'help':'<circle cx="12" cy="12" r="10"/>'+P.format('M8 8c0-5 9-5 8 0-1 3-4 2-4 6')+'<circle cx="12" cy="18" r=".6"/>',
'download':P.format('M12 2v13m-5-5 5 5 5-5M3 17v5h18v-5'),
'upload':P.format('M12 16V3m-5 5 5-5 5 5M3 17v5h18v-5'),
'eject':P.format('m12 3 10 12H2ZM3 20h18'),
'link':P.format('m9 15 6-6M7 17l-1 1a4 4 0 0 1-6-6l6-6a4 4 0 0 1 6 0M17 7l1-1a4 4 0 0 1 6 6l-6 6a4 4 0 0 1-6 0'),
'pin':P.format('m7 2 10 0-1 8 4 5H4l4-5ZM12 15v8'),
'eye':'<path d="M1 12q11-16 22 0-11 16-22 0Z"/><circle cx="12" cy="12" r="3"/>',
'clock':'<circle cx="12" cy="12" r="10"/>'+P.format('M12 5v8h5'),
'calendar':P.format('M3 5h18v17H3ZM7 2v6M17 2v6M3 11h18M7 15h3m4 0h3m-10 4h3'),
'user':'<circle cx="12" cy="7" r="5"/>'+P.format('M3 22v-3c0-8 18-8 18 0v3Z'),
'printer':P.format('M6 8V2h12v6M6 17H2V8h20v9h-4M6 14h12v8H6Z'),
'settings':'<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2"/>'+P.format('M12 1v4m0 14v4M1 12h4m14 0h4M4 4l3 3m10 10 3 3M4 20l3-3M17 7l3-3'),
'location':'<path d="M12 23C-3 8 6 1 12 1s15 7 0 22Z"/><circle cx="12" cy="9" r="3"/>',
}
ALIASES={
'close':['window-close','edit-clear','close-menu'], 'minus':['window-minimize','list-remove','zoom-out'], 'plus':['list-add','zoom-in','value-increase'], 'check':['object-select','emblem-ok','checkbox-checked'],
'menu':['application-menu','open-menu','view-more'], 'more':['view-more-horizontal'],
'left':['go-previous','pan-start','go-back'], 'right':['go-next','pan-end','go-forward'], 'up':['go-up','pan-up'], 'down':['go-down','pan-down'],
'search':['edit-find','system-search','search'], 'folder':['folder','document-open'], 'home':['user-home','go-home'], 'trash':['user-trash','edit-delete'], 'document':['document-new','text-x-generic'],
'copy':['edit-copy'], 'cut':['edit-cut'], 'paste':['edit-paste'], 'save':['document-save','document-save-as'], 'undo':['edit-undo'], 'redo':['edit-redo'], 'refresh':['view-refresh','reload','document-revert'],
'power':['system-shutdown','system-power-off'], 'lock':['system-lock-screen','changes-prevent'], 'unlock':['changes-allow'],
'brightness':['display-brightness','brightness','weather-clear'], 'bluetooth':['bluetooth','bluetooth-active'], 'wifi':['network-wireless','network-wireless-signal-excellent'],
'volume':['audio-volume-high','multimedia-volume-control'], 'muted':['audio-volume-muted'], 'microphone':['audio-input-microphone','microphone-sensitivity-high'], 'headphones':['audio-headphones'],
'play':['media-playback-start'], 'pause':['media-playback-pause'], 'stop':['media-playback-stop'], 'next':['media-skip-forward'], 'previous':['media-skip-backward'], 'record':['media-record'],
'apps':['view-app-grid','view-grid','applications-other','com.system76.CosmicAppLibrary'], 'workspaces':['view-paged','preferences-desktop-workspaces','com.system76.CosmicWorkspaces'],
'fullscreen':['view-fullscreen','window-maximize'], 'restore':['view-restore','window-restore'], 'monitor':['video-display','preferences-desktop-display'], 'keyboard':['input-keyboard'], 'network':['network-wired','network-transmit-receive'],
'info':['dialog-information'], 'warning':['dialog-warning'], 'error':['dialog-error','process-stop'], 'help':['help-about','help-browser','dialog-question'],
'download':['folder-download','folder-downloads'], 'upload':['document-send'], 'eject':['media-eject'], 'link':['insert-link','emblem-symbolic-link'], 'pin':['view-pin'], 'eye':['view-reveal'],
'clock':['appointment-soon','document-open-recent'], 'calendar':['x-office-calendar','date'], 'user':['avatar-default','system-users'], 'printer':['document-print','printer'], 'settings':['preferences-system','emblem-system'], 'location':['mark-location'],
}

def build(root):
 root=Path(root);directory=root/'Studio Objects/scalable/actions';directory.mkdir(parents=True,exist_ok=True)
 mapping={}
 for key,names in ALIASES.items():
  content=f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><title>{key}</title><g fill="none" stroke="#2e3436" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{GLYPHS[key]}</g></svg>'
  for name in names:
   alias=name+'-symbolic';(directory/(alias+'.svg')).write_text(content);mapping[alias]={'master':'symbols.py:'+key,'category':'symbolic','status':'custom'}
 # Battery fill levels carry actual semantic state, not a single generic icon.
 for level in range(0,101,10):
  for charging in (False,True):
   inner=f'<rect x="2" y="6" width="18" height="12" rx="2" fill="none" stroke="#2e3436" stroke-width="2"/><path d="M22 10v4" stroke="#2e3436" stroke-width="2"/>'
   if level:inner+=f'<rect x="4" y="8" width="{14*level/100:g}" height="8" fill="#2e3436"/>'
   if charging:inner+='<path d="m12 5-5 8h4l-1 6 6-9h-4l2-5Z" fill="#2e3436" stroke="#fff" stroke-width=".6"/>'
   alias=f'battery-level-{level}'+('-charging' if charging else '')+'-symbolic'
   (directory/(alias+'.svg')).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><title>{alias}</title>{inner}</svg>')
   mapping[alias]={'master':'symbols.py:battery','category':'symbolic','status':'custom'}
 return mapping
