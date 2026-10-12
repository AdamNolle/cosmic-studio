"""Source/XML checks only: not rendered optics, native recoloring or runtime proof."""

import contextlib
import importlib.util
import io
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET


SOURCE = Path(__file__).resolve().parents[1] / "utilities" / "symbols.py"
SPEC = importlib.util.spec_from_file_location("utility_symbols_candidates", SOURCE)
symbols = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(symbols)
NS = "{http://www.w3.org/2000/svg}"
EXPECTED_STATES = {
    "studio-utility-stats": ("normal", "unavailable"),
    "studio-utility-brightness": ("low", "medium", "high", "unavailable"),
    "studio-utility-overflow": ("hidden", "revealed"),
}


def drawing(name, state, size):
    return ET.fromstring(symbols.svg(name, state=state, size=size)).find(NS + "g")


class UtilitySymbols(unittest.TestCase):
    def test_supported_names_states_sizes_and_self_contained_xml(self):
        self.assertEqual(dict(symbols.STATES), EXPECTED_STATES)
        self.assertEqual(symbols.SIZES, (16, 20, 24, 32))
        allowed_tags = {"svg", "title", "g", "rect", "circle", "line", "polyline"}
        allowed_attributes = {
            "width", "height", "viewBox", "role", "aria-labelledby", "id",
            "fill", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin",
            "x", "y", "rx", "cx", "cy", "r", "x1", "y1", "x2", "y2", "points",
        }
        count = 0
        for name, states in EXPECTED_STATES.items():
            for state in states:
                for size in symbols.SIZES:
                    with self.subTest(name=name, state=state, size=size):
                        content = symbols.svg(name, state=state, size=size)
                        self.assertEqual(content, symbols.svg(name, state=state, size=size))
                        root = ET.fromstring(content)
                        self.assertEqual(root.tag, NS + "svg")
                        self.assertEqual(root.get("viewBox"), f"0 0 {size} {size}")
                        self.assertEqual(root.get("width"), str(size))
                        self.assertEqual(root.get("height"), str(size))
                        self.assertTrue(root.find(NS + "title").text)
                        self.assertEqual(root.get("aria-labelledby"), "title")
                        for node in root.iter():
                            self.assertIn(node.tag.removeprefix(NS), allowed_tags)
                            self.assertLessEqual(set(node.attrib), allowed_attributes)
                            for key, value in node.attrib.items():
                                self.assertNotIn("url(", value)
                                self.assertNotIn("data:", value)
                                if key in ("fill", "stroke"):
                                    self.assertIn(value, ("none", "currentColor"))
                        self.assertNotIn("<!", content)
                        count += 1
        self.assertEqual(count, 32)

    def test_invalid_names_states_and_sizes_are_rejected_without_io(self):
        cases = [
            (name, "normal", 16) for name in ("stats", "display-brightness", "../stats", "", None, [])
        ] + [
            ("studio-utility-stats", state, 16) for state in ("paused", "low", "NORMAL", None, [])
        ] + [
            ("studio-utility-stats", "normal", size) for size in (0, 18, 48, 16.0, True, "16", None, [])
        ] + [
            ("studio-utility-brightness", "normal", 16),
            ("studio-utility-overflow", "unavailable", 16),
        ]
        with patch.object(Path, "open", side_effect=AssertionError("unexpected I/O")):
            for name, state, size in cases:
                with self.subTest(name=name, state=state, size=size), self.assertRaises(ValueError):
                    symbols.svg(name, state=state, size=size)

    def test_all_states_have_distinct_geometry_not_only_titles(self):
        for name, states in EXPECTED_STATES.items():
            for size in symbols.SIZES:
                geometries = [ET.tostring(drawing(name, state, size)) for state in states]
                self.assertEqual(len(set(geometries)), len(states), (name, size))

    def test_statistics_unavailable_replaces_bars_with_dash(self):
        for size in symbols.SIZES:
            normal = drawing("studio-utility-stats", "normal", size)
            unavailable = drawing("studio-utility-stats", "unavailable", size)
            self.assertEqual(len(normal.findall(NS + "rect")), 3)
            self.assertEqual(len(unavailable.findall(NS + "rect")), 0)
            self.assertEqual(ET.tostring(normal[0]), ET.tostring(unavailable[0]))
            self.assertEqual(len(unavailable), 2)
            dash = unavailable[1]
            self.assertEqual(dash.tag, NS + "line")
            self.assertEqual(dash.get("y1"), dash.get("y2"))
            self.assertLess(float(dash.get("x1")), float(dash.get("x2")))

    def test_brightness_two_displays_and_shape_based_levels(self):
        for size in symbols.SIZES:
            groups = {state: drawing("studio-utility-brightness", state, size)
                      for state in EXPECTED_STATES["studio-utility-brightness"]}
            for group in groups.values():
                screens = group.findall(NS + "rect")
                self.assertEqual(len(screens), 2)
                self.assertEqual(screens[0].get("width"), screens[1].get("width"))
                self.assertLess(float(screens[0].get("x")) + float(screens[0].get("width")),
                                float(screens[1].get("x")))
            monitor_count = 4 if size == 16 else 6
            monitors = [ET.tostring(n) for n in list(groups["low"])[:monitor_count]]
            for group in groups.values():
                self.assertEqual([ET.tostring(n) for n in list(group)[:monitor_count]], monitors)
            low = groups["low"].find(NS + "circle")
            medium = groups["medium"].find(NS + "circle")
            self.assertEqual(low.get("fill"), "none")
            self.assertEqual(medium.get("fill"), "currentColor")
            self.assertEqual(medium.get("stroke"), "none")
            self.assertEqual(ET.tostring(medium), ET.tostring(groups["high"].find(NS + "circle")))
            self.assertEqual(len(groups["high"]), len(groups["medium"]) + 4)
            self.assertIsNone(groups["unavailable"].find(NS + "circle"))
            self.assertEqual(groups["unavailable"][-1].tag, NS + "line")

    def test_overflow_changes_only_chevron_direction(self):
        for size in symbols.SIZES:
            hidden = drawing("studio-utility-overflow", "hidden", size)
            revealed = drawing("studio-utility-overflow", "revealed", size)
            self.assertEqual([ET.tostring(n) for n in list(hidden)[:-1]],
                             [ET.tostring(n) for n in list(revealed)[:-1]])
            for group, direction in ((hidden, 1), (revealed, -1)):
                self.assertEqual(len(group.findall(NS + "rect")), 2)
                points = [tuple(map(float, pair.split(","))) for pair in group[-1].get("points").split()]
                self.assertEqual(points[0][0], points[2][0])
                self.assertGreater(direction * (points[1][0] - points[0][0]), 0)

    def test_authored_small_size_geometry_is_not_blind_scaling(self):
        # Independent 16/20/24/32 widths; normalized values are not a shared master.
        widths = []
        for size, expected in ((16, 2), (20, 3), (24, 3), (32, 5)):
            bar = drawing("studio-utility-stats", "normal", size).find(NS + "rect")
            self.assertEqual(float(bar.get("width")), expected)
            widths.append(expected / size)
        # 16 and 24 happen to share a ratio; the family is not one scaled master.
        self.assertEqual(len(set(widths)), 3)
        # Feet are actually removed at 16, not shrunk from larger artwork.
        small = drawing("studio-utility-brightness", "low", 16)
        self.assertEqual(len(small.findall(NS + "line")), 2)
        for size in (20, 24, 32):
            large = drawing("studio-utility-brightness", "low", size)
            self.assertEqual(len(large.findall(NS + "line")), 4)
        chevron_widths = []
        for size in symbols.SIZES:
            points = drawing("studio-utility-overflow", "hidden", size)[-1].get("points")
            xs = [float(pair.split(",")[0]) for pair in points.split()]
            chevron_widths.append((max(xs) - min(xs)) / size)
        self.assertGreater(len(set(chevron_widths)), 1)

    def test_finite_coordinates_and_conservative_stroked_bounds(self):
        for name, states in EXPECTED_STATES.items():
            for state in states:
                for size in symbols.SIZES:
                    group = drawing(name, state, size)
                    for node in group:
                        tag = node.tag.removeprefix(NS)
                        margin = 0 if node.get("stroke") == "none" else float(group.get("stroke-width")) / 2
                        if tag == "rect":
                            x, y, w, h = (float(node.get(a)) for a in ("x", "y", "width", "height"))
                            self.assertGreater(min(w, h), 0)
                            self.assertLessEqual(float(node.get("rx")), min(w, h) / 2)
                            xs, ys = [x, x+w], [y, y+h]
                        elif tag == "circle":
                            x, y, r = (float(node.get(a)) for a in ("cx", "cy", "r"))
                            self.assertGreater(r, 0)
                            xs, ys = [x-r, x+r], [y-r, y+r]
                        elif tag == "line":
                            xs = [float(node.get(a)) for a in ("x1", "x2")]
                            ys = [float(node.get(a)) for a in ("y1", "y2")]
                        else:
                            points = [tuple(map(float, pair.split(","))) for pair in node.get("points").split()]
                            xs, ys = zip(*points)
                        for values in (xs, ys):
                            self.assertTrue(all(math.isfinite(v) for v in values))
                            self.assertGreaterEqual(min(values)-margin, 0, (name, state, size))
                            self.assertLessEqual(max(values)+margin, size, (name, state, size))

    def test_import_has_no_writes_output_or_cli_execution(self):
        code = compile(SOURCE.read_text(encoding="utf-8"), str(SOURCE), "exec")
        namespace = {"__file__": str(SOURCE), "__name__": "pure_import_probe"}
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured), \
                patch("builtins.open", side_effect=AssertionError("import opened a file")), \
                patch.object(Path, "open", side_effect=AssertionError("import opened a path")), \
                patch.object(Path, "mkdir", side_effect=AssertionError("import created a directory")), \
                patch.object(symbols.argparse.ArgumentParser, "parse_args", side_effect=AssertionError("import ran CLI")):
            exec(code, namespace)
        self.assertEqual(captured.getvalue(), "")
        self.assertTrue(callable(namespace["svg"]))

    def test_export_exclusive_flat_candidate_files_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            with patch.object(symbols, "_CANDIDATE_ROOT", root):
                paths = symbols.export_candidates()
                self.assertEqual(len(paths), 32)
                output = root / "studio-utility-symbols.candidates"
                self.assertEqual(set(root.iterdir()), {output})
                self.assertEqual(set(output.iterdir()), set(paths))
                before = {path: path.read_bytes() for path in paths}
                for path in paths:
                    self.assertEqual(path.parent, output)
                    self.assertTrue(path.name.endswith("-candidate.svg"))
                    ET.fromstring(before[path])
                with self.assertRaises(FileExistsError):
                    symbols.export_candidates()
                self.assertEqual(before, {path: path.read_bytes() for path in paths})

    def test_export_rejects_missing_root_without_creating_parents(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory).resolve() / "missing"
            with patch.object(symbols, "_CANDIDATE_ROOT", missing), self.assertRaises(ValueError):
                symbols.export_candidates()
            self.assertFalse(missing.exists())

    def test_export_rejects_symlinked_ancestry_and_output_before_writes(self):
        # Mock redirection detection: Windows test hosts may not permit symlink creation.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            output = root / "studio-utility-symbols.candidates"
            for redirected in (root, root.parent, output):
                with self.subTest(redirected=redirected), \
                        patch.object(symbols, "_CANDIDATE_ROOT", root), \
                        patch.object(Path, "is_symlink", autospec=True, side_effect=lambda p: p == redirected), \
                        self.assertRaises(ValueError):
                    symbols.export_candidates()
                self.assertEqual(list(root.iterdir()), [])
            if hasattr(Path, "is_junction"):
                with patch.object(symbols, "_CANDIDATE_ROOT", root), \
                        patch.object(Path, "is_junction", autospec=True, side_effect=lambda p: p == output), \
                        self.assertRaises(ValueError):
                    symbols.export_candidates()
                self.assertEqual(list(root.iterdir()), [])

    def test_export_rejects_resolved_escape_before_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            output = root / "studio-utility-symbols.candidates"
            resolve = Path.resolve
            with patch.object(symbols, "_CANDIDATE_ROOT", root), \
                    patch.object(Path, "resolve", autospec=True,
                                 side_effect=lambda p: root.parent / "escaped" if p == output else resolve(p)), \
                    self.assertRaises(ValueError):
                symbols.export_candidates()
            self.assertEqual(list(root.iterdir()), [])

    def test_each_candidate_file_uses_exclusive_create_even_after_directory_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            original_open = Path.open
            intercepted = []

            def collide(path, mode="r", **kwargs):
                intercepted.append(path)
                self.assertEqual(mode, "x")
                with original_open(path, "wb") as stream:
                    stream.write(b"existing candidate")
                return original_open(path, mode, **kwargs)

            with patch.object(symbols, "_CANDIDATE_ROOT", root), \
                    patch.object(Path, "open", autospec=True, side_effect=collide), \
                    self.assertRaises(FileExistsError):
                symbols.export_candidates()
            self.assertEqual(len(intercepted), 1)
            self.assertEqual(intercepted[0].read_bytes(), b"existing candidate")

    def test_cli_requires_explicit_export_and_has_no_path_or_install_option(self):
        captured = io.StringIO()
        with patch.object(symbols, "export_candidates") as export, \
                contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            self.assertEqual(symbols.main([]), 0)
            with self.assertRaises(SystemExit) as help_exit:
                symbols.main(["--help"])
            self.assertEqual(help_exit.exception.code, 0)
            for option in ("--install", "--output", "--force"):
                with self.assertRaises(SystemExit) as error:
                    symbols.main([option])
                self.assertEqual(error.exception.code, 2)
            export.assert_not_called()
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(symbols, "_CANDIDATE_ROOT", Path(directory).resolve()), \
                contextlib.redirect_stdout(captured):
            self.assertEqual(symbols.main(["--export-candidates"]), 0)
        self.assertIn("32 inactive SVG candidates", captured.getvalue())


if __name__ == "__main__":
    unittest.main()
