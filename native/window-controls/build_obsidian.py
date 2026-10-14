#!/usr/bin/env python3
"""Generate a titlebar-only Obsidian snippet using the reviewed control artwork."""
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
ART = HERE.parents[1] / 'icons/window-controls/svg'
SELECTOR = '.titlebar-button:is(.mod-minimize,.mod-maximize,.mod-close)'
parts = ['/* Studio window controls: preserve Obsidian native button actions. */',
         SELECTOR + ''' {
  width: 22px; height: 24px; min-width: 22px;
  align-self: center; margin: 0; padding: 0;
  border: 0; border-radius: 4px;
  background-color: transparent !important;
  background-size: 22px 24px;
  background-position: center; background-repeat: no-repeat;
}''', SELECTOR + ' svg { visibility: hidden; }',
         SELECTOR + ':focus-visible { outline: 1px solid var(--interactive-accent); }']
for role in ['minimize', 'maximize', 'close', 'restore']:
    button = 'maximize' if role == 'restore' else role
    body = 'body.is-maximized' if role == 'restore' else 'body'
    for state, condition, suffix in [('normal', '', ''), ('inactive', ':not(.is-focused)', ''),
                                     ('hover', '', ':hover'), ('pressed', '', ':active')]:
        # Obsidian always shows all three, so each role keeps its rocker position.
        svg = (ART/state/(role+'.svg')).read_text()
        parts.append(body + condition + ' .titlebar-button.mod-' + button + suffix
                     + ' { background-image: url("data:image/svg+xml,' + quote(svg, safe='') + '") !important; }')
(HERE/'obsidian.css').write_text('\n\n'.join(parts)+'\n')
print('Generated Obsidian titlebar snippet.')
