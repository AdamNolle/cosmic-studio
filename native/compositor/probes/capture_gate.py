#!/usr/bin/env python3
"""Reject successful protocol captures that do not demonstrate rendered fixtures."""
from pathlib import Path
import re


def validate(image, compositor_log):
    raw = Path(image).read_bytes()
    match = re.match(rb'P6\s+(\d+)\s+(\d+)\s+255\s', raw)
    if not match:
        raise ValueError('Expected native RGB P6 capture.')
    width, height = map(int, match.groups())
    if not 1 <= width <= 8192 or not 1 <= height <= 8192:
        raise ValueError('Capture dimensions outside fixture bounds.')
    pixels = raw[match.end():]
    if len(pixels) != width * height * 3:
        raise ValueError('Truncated or malformed native capture payload.')
    # The synthetic checker/gradient background has many colors. A successful
    # ext-image-copy roundtrip with a blank compositor framebuffer is not enough.
    colors = set()
    for offset in range(0, len(pixels), 3):
        colors.add(pixels[offset:offset + 3])
        if len(colors) >= 16:
            break
    if len(colors) < 16:
        raise ValueError('Blank/near-uniform capture: rendered fixture not demonstrated.')
    log = Path(compositor_log).read_text(errors='replace')
    for marker in ('Failed to render frame.', 'The context has been lost',
                   'Failed to submit buffer for display'):
        if marker in log:
            raise ValueError('Candidate frame rendering failed: '+marker)
    return {'width': width, 'height': height, 'fixture_color_diversity_at_least': 16,
            'frame_render_failure_markers': False,
            'scope': 'Synthetic frame visibility only; not optical quality, real panel/apps, input or performance.'}
