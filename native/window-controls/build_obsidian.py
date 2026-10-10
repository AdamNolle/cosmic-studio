#!/usr/bin/env python3
"""Generate a titlebar-only Obsidian snippet using the reviewed control artwork."""
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
ART = HERE.parents[1] / 'icons/window-controls/svg'
SELECTOR = '.titlebar-button:is(.mod-minimize,.mod-maximize,.mod-close)'
parts = ['/* Studio window controls: preserve Obsidian native button actions. */',
         SELECTOR + ''' {
  width: 32px; height: 32px; min-width: 32px;
  align-self: center; margin: 0 3px; padding: 0;
  border: 0; border-radius: 8px;
  background-color: transparent !important;
  background-size: 32px 32px;
  background-position: center; background-repeat: no-repeat;
}''', SELECTOR + ' svg { visibility: hidden; }',
         SELECTOR + ':focus-visible { outline: 1px solid var(--interactive-accent); }']
for role in ['minimize', 'maximize', 'close', 'restore']:
    button = 'maximize' if role == 'restore' else role
    body = 'body.is-maximized' if role == 'restore' else 'body'
    for state, condition, suffix in [('normal', '', ''), ('inactive', ':not(.is-focused)', ''),
                                     ('hover', '', ':hover'), ('pressed', '', ':active')]:
        svg = (ART/state/(role+'.svg')).read_text()
        parts.append(body + condition + ' .titlebar-button.mod-' + button + suffix
                     + ' { background-image: url("data:image/svg+xml,' + quote(svg, safe='') + '") !important; }')
(HERE/'obsidian.css').write_text('\n\n'.join(parts)+'\n')
print('Generated Obsidian titlebar snippet.')
