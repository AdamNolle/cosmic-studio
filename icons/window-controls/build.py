#!/usr/bin/env python3
"""Build the Studio window-control rocker: three joined segments, glyphs on hover.

Each control is one segment of a single switch. Its corners depend on its
position among the visible controls, so every role is drawn in four shapes:
solo, left, middle and right. `<role>.svg` is the usual full-rocker position.
PNG exports and the preview use Inkscape when installed, otherwise rsvg-convert.
"""
from pathlib import Path
import json, shutil, subprocess, sys

ROOT = Path(__file__).resolve().parent
WIDTH, HEIGHT = 22, 24           # layout canvas; keeps a 24 px pointer target
SEGMENT, TOP, RADIUS = 14, 5, 4  # visible segment height, offset and outer corners
COLORS = {'minimize': '#2fc469', 'maximize': '#f8c22e', 'restore': '#f8c22e', 'close': '#f0514b'}
INACTIVE = ('#808080', 0.26)     # neutral over light paper and dark graphite alike
GLYPH = {'minimize': 0.6, 'maximize': 0.6, 'restore': 0.6, 'close': 0.65}
# 9 px glyphs from the design's studio-glyphs sprite, centred in the segment.
GLYPHS = {'minimize': '<path d="M2 4.5H7"/>',
          'maximize': '<rect x="2" y="2" width="5" height="5"/>',
          'restore': '<path d="M3.5 1.5H7.5V5.5M1.5 3.5H5.5V7.5H1.5Z"/>',
          'close': '<path d="M2 2L7 7M7 2L2 7"/>'}
SHAPES = {'solo': (True, True), 'left': (True, False), 'middle': (False, False), 'right': (False, True)}
DEFAULT = {'minimize': 'left', 'maximize': 'middle', 'restore': 'middle', 'close': 'right'}
STATES = ['normal', 'hover', 'pressed', 'inactive']
MENUS = {'File': 22, 'Edit': 23, 'View': 27, 'Go': 16, 'Window': 44, 'Help': 26}  # Archivo 12.5 px advances


def outline(left, right, inset=0.0):
    """Closed segment path; rounded only on the rocker's outer ends."""
    r, y0, y1, w = RADIUS - inset, TOP + inset, TOP + SEGMENT - inset, WIDTH
    x0, x1 = (inset if left else 0), (w - inset if right else w)
    d = f'M{x0 + r if left else x0} {y0}H{x1 - r if right else x1}'
    d += f'A{r} {r} 0 0 1 {x1} {y0 + r}V{y1 - r}A{r} {r} 0 0 1 {x1 - r} {y1}' if right else f'V{y1}'
    d += f'H{x0 + r if left else x0}'
    d += f'A{r} {r} 0 0 1 {x0} {y1 - r}V{y0 + r}A{r} {r} 0 0 1 {x0 + r} {y0}Z' if left else 'Z'
    return d


def ring(left, right):
    """Half-pixel outer edge; interior joints are left to the divider."""
    r, y0, y1, w, i = RADIUS, TOP, TOP + SEGMENT, WIDTH, 0.25
    xa, xb = (r if left else 0), (w - r if right else w)
    d = f'M{xa} {y0 + i}H{xb}M{xa} {y1 - i}H{xb}'
    if left:
        d += f'M{r} {y0 + i}A{r - i} {r - i} 0 0 0 {i} {y0 + r}V{y1 - r}A{r - i} {r - i} 0 0 0 {r} {y1 - i}'
    if right:
        d += f'M{w - r} {y0 + i}A{r - i} {r - i} 0 0 1 {w - i} {y0 + r}V{y1 - r}A{r - i} {r - i} 0 0 1 {w - r} {y1 - i}'
    return d


def icon(name, state, shape):
    left, right = SHAPES[shape]
    body = outline(left, right)
    fill = f'fill="{COLORS[name]}"' if state != 'inactive' else f'fill="{INACTIVE[0]}" fill-opacity="{INACTIVE[1]}"'
    parts = [f'<path d="{body}" {fill}/>']
    if state == 'pressed':
        parts.append(f'<path d="{body}" fill="#000" fill-opacity=".13"/>')
    if state != 'inactive':
        xa, xb = (RADIUS if left else 0), (WIDTH - RADIUS if right else WIDTH)
        parts.append(f'<path d="M{xa} {TOP + 0.75}H{xb}" stroke="#fff" stroke-opacity=".35" stroke-width=".5"/>')
    if not left:
        parts.append(f'<rect y="{TOP}" width="1" height="{SEGMENT}" fill="#000" fill-opacity=".18"/>')
    parts.append(f'<path d="{ring(left, right)}" fill="none" stroke="#000" stroke-opacity="{.35 if state != "inactive" else .22}" stroke-width=".5"/>')
    if state in ('hover', 'pressed'):
        opacity = min(GLYPH[name] + (.1 if state == 'pressed' else 0), 1)
        parts.append(f'<g transform="translate({(WIDTH - 9) / 2} {TOP + (SEGMENT - 9) / 2})" fill="none" stroke="#000" '
                     f'stroke-opacity="{opacity:g}" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round">{GLYPHS[name]}</g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
            f'viewBox="0 0 {WIDTH} {HEIGHT}">' + ''.join(parts) + '</svg>')


def rasterize(source, target, width=None):
    target.parent.mkdir(parents=True, exist_ok=True)
    if shutil.which('inkscape'):
        args = ['inkscape', str(source), '--export-filename=' + str(target)]
        if width: args.insert(2, f'--export-width={width}')
    elif shutil.which('rsvg-convert'):
        args = ['rsvg-convert', str(source), '-o', str(target)] + (['-w', str(width)] if width else [])
    else:
        return False
    subprocess.run(args, check=True, capture_output=True)
    return True


def build():
    shutil.rmtree(ROOT/'svg', ignore_errors=True)
    for state in STATES:
        for name in COLORS:
            for shape in SHAPES:
                path = ROOT/'svg'/state/f'{name}-{shape}.svg'
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(icon(name, state, shape))
            (ROOT/'svg'/state/f'{name}.svg').write_text(icon(name, state, DEFAULT[name]))
    (ROOT/'preview.svg').write_text(preview())
    (ROOT/'tokens.json').write_text(json.dumps({
        'order': ['minimize', 'maximize', 'close'], 'canvas': [WIDTH, HEIGHT], 'segment': [WIDTH, SEGMENT],
        'segment_top': TOP, 'outer_radius': RADIUS, 'gap': 0, 'divider': 'rgba(0,0,0,.18) 1px',
        'ring': 'rgba(0,0,0,.35) 0.5px', 'highlight': 'rgba(255,255,255,.35) 0.5px',
        'glyph': {'size': 9, 'stroke': 1.3, 'opacity': GLYPH, 'visible': ['hover', 'pressed']},
        'colors': COLORS, 'inactive': {'color': INACTIVE[0], 'opacity': INACTIVE[1]},
        'shapes': list(SHAPES), 'states': STATES}, indent=2) + '\n')
    exported = rasterize(ROOT/'preview.svg', ROOT/'preview.png')
    for size in [1, 2, 3, 4] if exported else []:
        for state in STATES:
            for name in COLORS:
                rasterize(ROOT/'svg'/state/f'{name}.svg', ROOT/'png'/f'{size}x'/state/f'{name}.png', WIDTH*size)
    print('Built rocker controls: 4 roles x 4 shapes x 4 states.'
          + ('' if exported else ' Install Inkscape or rsvg-convert for PNG exports.'), file=sys.stderr)


def preview():
    def text(x, y, s, size=24, color='#1f1f22', family='Archivo', style=''):
        return f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" fill="{color}"{style}>{s}</text>'

    def rocker(x, y, state, scale, roles=('minimize', 'maximize', 'close'), maximized=False):
        out = []
        for i, role in enumerate(roles):
            name = 'restore' if maximized and role == 'maximize' else role
            shape = 'solo' if len(roles) == 1 else 'left' if i == 0 else 'right' if i == len(roles) - 1 else 'middle'
            art = icon(name, state, shape).replace(f'width="{WIDTH}" height="{HEIGHT}"',
                                                  f'x="{x + i * WIDTH * scale}" y="{y}" width="{WIDTH * scale}" height="{HEIGHT * scale}"')
            out.append(art)
        return ''.join(out)

    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="1000"><rect width="1440" height="1000" fill="#e9e7e1"/>',
             text(84, 104, 'Window controls', 56, family='Instrument Serif'),
             text(86, 144, 'One rocker: green minimize, yellow maximize, red close. Glyphs appear on hover.', 19, '#5f5f63')]
    for i, state in enumerate(STATES):
        x = 84 + i * 336
        parts += [rocker(x, 184, state, 4), text(x + 2, 316, state.upper(), 13, '#5f5f63', style=' letter-spacing="2.2" font-weight="600"')]
    parts += [rocker(84, 360, 'normal', 4, maximized=True), text(86, 492, 'RESTORE', 13, '#5f5f63', style=' letter-spacing="2.2" font-weight="600"'),
              rocker(420, 360, 'normal', 4, ('close',)), text(422, 492, 'CLOSE ONLY', 13, '#5f5f63', style=' letter-spacing="2.2" font-weight="600"'),
              rocker(756, 360, 'hover', 4, ('minimize', 'close')), text(758, 492, 'NO MAXIMIZE', 13, '#5f5f63', style=' letter-spacing="2.2" font-weight="600"')]
    for row, (paper, ink, sub) in enumerate([('#e9e7e1', '#1f1f22', '#5f5f63'), ('#1b1c20', '#f3f3f5', '#9c9ca1')]):
        y = 560 + row * 150
        parts.append(f'<rect x="84" y="{y}" width="1272" height="110" rx="6" fill="{paper}" stroke="#000" stroke-opacity=".18"/>')
        parts.append(f'<rect x="84" y="{y + 37}" width="1272" height="1" fill="{ink}" fill-opacity=".22"/>')
        parts.append(text(640, y + 26, 'Documents', 18, ink, 'Instrument Serif'))
        parts += [text(104 + sum(w + 16 for w in list(MENUS.values())[:i]), y + 24, label, 12.5, sub) for i, label in enumerate(MENUS)]
        parts.append(rocker(1270, y + 7, 'normal' if row == 0 else 'inactive', 1))
        parts.append(text(104, y + 80, 'Active window' if row == 0 else 'Inactive window: neutral until hovered', 13, sub))
    parts.append(text(84, 920, f'{WIDTH} x {SEGMENT} px segments, {RADIUS} px outer corners, 1 px dividers, {HEIGHT} px pointer target', 16, '#5f5f63'))
    parts.append('</svg>')
    return ''.join(parts)


if __name__ == '__main__':
    build()
