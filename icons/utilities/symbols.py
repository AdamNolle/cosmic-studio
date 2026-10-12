"""Original, inactive utility-symbol candidates; standard-library authoring only.

These are not deployed aliases or live readings. Import and svg() do no I/O.
The only writer, export_candidates(), exclusively creates a flat candidate bundle
beside this source, never a theme or installation. Native recoloring, accessibility
wiring and real-size optical review remain separate validation gates.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from types import MappingProxyType
import xml.etree.ElementTree as ET


SIZES = (16, 20, 24, 32)
STATES = MappingProxyType({
    "studio-utility-stats": ("normal", "unavailable"),
    "studio-utility-brightness": ("low", "medium", "high", "unavailable"),
    "studio-utility-overflow": ("hidden", "revealed"),
})
_CANDIDATE_ROOT = Path(__file__).absolute().parent
_CANDIDATE_DIRECTORY = "studio-utility-symbols.candidates"

# Per-size coordinates, not a scaled master. Small screens omit wide feet;
# bars, gaps, corner radii and chevrons have independently authored metrics.
_STROKE = {16: 1, 20: 1.5, 24: 1.5, 32: 2}
_STATS = {
    16: (2, 2, 14, (3, 7, 11), 2, (9, 5, 7), 14, .5, (5, 10, 11)),
    20: (2.5, 2.5, 17.5, (3, 8, 13), 3, (11, 6, 8), 17, .75, (6, 12, 14)),
    24: (3, 3, 21, (4, 10, 16), 3, (13, 7, 10), 21, 1, (7, 14, 17)),
    32: (4, 4, 28, (5, 13, 21), 5, (18, 9, 13), 28, 1, (9, 19, 23)),
}
# screens: two x positions, y, width, height; sun: cx, cy, radius,
# ray start/end radius; stand: bottom y, half foot width (zero omits feet).
_BRIGHTNESS = {
    16: ((1.5, 9.5), 7.5, 5, 5, (8, 3.5, 1.25, 2.5, 3), 14.5, 0),
    20: ((2, 12), 9, 6, 6, (10, 4.5, 1.5, 2.5, 3.5), 17, 2),
    24: ((2, 14), 11, 8, 7, (12, 5, 2, 3, 4), 21, 2.5),
    32: ((3, 19), 15, 10, 9, (16, 6, 2.5, 4, 5), 28, 3),
}
_OVERFLOW = {
    16: (2, 14, 3, (2, 6), 7, 2, 3, 9.5, 6, 13, (11, 14, 8, 12)),
    20: (2.5, 17.5, 4, (3, 8), 9, 3, 4, 12.5, 8, 16, (15, 18, 10, 14)),
    24: (3, 21, 5, (3, 9), 11, 3, 5, 14.5, 9, 20, (17, 21, 12, 18)),
    32: (4, 28, 6, (4, 12), 14, 4, 6, 19, 12, 27, (23, 28, 16, 24)),
}


def _node(parent: ET.Element, tag: str, **attributes: object) -> ET.Element:
    return ET.SubElement(parent, tag, {
        key.replace("_", "-"): f"{value:g}" if isinstance(value, (int, float)) else str(value)
        for key, value in attributes.items()
    })


def _line(parent: ET.Element, x1: float, y1: float, x2: float, y2: float,
          **attributes: object) -> None:
    _node(parent, "line", x1=x1, y1=y1, x2=x2, y2=y2, **attributes)


def _stats(parent: ET.Element, size: int, state: str) -> None:
    left, rail_y, right, xs, width, tops, bottom, radius, dash = _STATS[size]
    _line(parent, left, rail_y, right, rail_y)
    if state == "unavailable":
        x1, y, x2 = dash
        _line(parent, x1, y, x2, y)
    else:
        for x, top in zip(xs, tops):
            _node(parent, "rect", x=x, y=top, width=width, height=bottom-top,
                  rx=radius, fill="currentColor", stroke="none")


def _brightness(parent: ET.Element, size: int, state: str) -> None:
    xs, y, width, height, sun, stand_bottom, foot = _BRIGHTNESS[size]
    for x in xs:
        _node(parent, "rect", x=x, y=y, width=width, height=height, rx=.5 if size == 16 else 1)
        center = x + width / 2
        _line(parent, center, y+height, center, stand_bottom)
        if foot:
            _line(parent, center-foot, stand_bottom, center+foot, stand_bottom)
    cx, cy, radius, ray_start, ray_end = sun
    if state == "unavailable":
        _line(parent, cx-ray_start, cy, cx+ray_start, cy)
        return
    # Hollow / solid / solid with cardinal rays: no hue or opacity coding.
    # These qualitative candidates do not imply percentages or linked displays.
    _node(parent, "circle", cx=cx, cy=cy, r=radius,
          fill="none" if state == "low" else "currentColor",
          stroke="currentColor" if state == "low" else "none")
    if state == "high":
        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            _line(parent, cx+dx*ray_start, cy+dy*ray_start,
                  cx+dx*ray_end, cy+dy*ray_end, stroke_linecap="butt")


def _overflow(parent: ET.Element, size: int, state: str) -> None:
    left, right, rail_y, xs, y, width, height, divider, top, bottom, chevron = _OVERFLOW[size]
    _line(parent, left, rail_y, right, rail_y)
    for x in xs:
        _node(parent, "rect", x=x, y=y, width=width, height=height,
              rx=.5, fill="currentColor", stroke="none")
    _line(parent, divider, top, divider, bottom)
    x1, x2, y1, y2 = chevron
    start, tip = (x1, x2) if state == "hidden" else (x2, x1)
    _node(parent, "polyline", points=f"{start:g},{y1:g} {tip:g},{(y1+y2)/2:g} {start:g},{y2:g}")


def svg(name: str, *, state: str, size: int) -> str:
    """Return one self-contained, currentColor SVG for an exact candidate key.

    Only SIZES and the corresponding STATES are supported; there is deliberately
    no default state, alias lookup, external art, scaling transform or runtime API.
    """
    if not isinstance(name, str) or name not in STATES:
        raise ValueError(f"Unsupported utility candidate: {name!r}")
    if not isinstance(state, str) or state not in STATES[name]:
        raise ValueError(f"Unsupported state for {name}: {state!r}")
    if type(size) is not int or size not in SIZES:
        raise ValueError(f"Unsupported logical size: {size!r}")
    title = {
        "studio-utility-stats": f"Statistics {state}",
        "studio-utility-brightness": f"Multi-monitor brightness {state}",
        "studio-utility-overflow": "Show hidden items" if state == "hidden" else "Hide extra items",
    }[name]
    root = ET.Element("svg", {
        "xmlns": "http://www.w3.org/2000/svg", "width": str(size), "height": str(size),
        "viewBox": f"0 0 {size} {size}", "role": "img", "aria-labelledby": "title",
    })
    _node(root, "title", id="title").text = title
    group = _node(root, "g", fill="none", stroke="currentColor", stroke_width=_STROKE[size],
                  stroke_linecap="round", stroke_linejoin="round")
    {"studio-utility-stats": _stats, "studio-utility-brightness": _brightness,
     "studio-utility-overflow": _overflow}[name](group, size, state)
    return ET.tostring(root, encoding="unicode", short_empty_elements=True) + "\n"


def export_candidates() -> tuple[Path, ...]:
    """Exclusively create this source directory's fixed *.candidates bundle.

    No caller-selected path, parent creation, overwrite, cleanup or installation.
    Symlinked/redirected ancestry is rejected before writing. The owned source
    directory must not be concurrently redirected during export. On I/O failure,
    a partial candidate directory is left intact and the exception propagates.
    """
    root = _CANDIDATE_ROOT
    for ancestor in (root, *root.parents):
        if ancestor.is_symlink() or (hasattr(ancestor, "is_junction") and ancestor.is_junction()):
            raise ValueError("Candidate source ancestry must not be redirected")
    if not root.is_dir() or root.resolve() != root:
        raise ValueError("Candidate source root must be an existing canonical directory")
    output = root / _CANDIDATE_DIRECTORY
    if output.is_symlink() or (hasattr(output, "is_junction") and output.is_junction()):
        raise ValueError("Candidate output must not be redirected")
    if output.resolve().parent != root:
        raise ValueError("Candidate output must be a direct child of its source directory")
    # Prepare all bytes before creating anything; only explicit export reaches I/O.
    contents = [
        (output / f"{name}-{state}-{size}-candidate.svg", svg(name, state=state, size=size))
        for name, states in STATES.items() for state in states for size in SIZES
    ]
    output.mkdir(exist_ok=False)
    for path, content in contents:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
    return tuple(path for path, _ in contents)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-candidates", action="store_true",
                        help="exclusively create icons/utilities/studio-utility-symbols.candidates; never install")
    args = parser.parse_args(argv)
    if not args.export_candidates:
        parser.print_help()
        return 0
    paths = export_candidates()
    print(f"Created {len(paths)} inactive SVG candidates in {paths[0].parent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
