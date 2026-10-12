"""Source/specification checks only; no Blender, render or runtime evidence."""

import ast
from dataclasses import asdict
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch


SOURCE = Path(__file__).resolve().parents[1] / "utilities/geometry.py"
MODULE = importlib.util.spec_from_file_location("utility_geometry_under_test", SOURCE)
geometry = importlib.util.module_from_spec(MODULE)
sys.modules[MODULE.name] = geometry
MODULE.loader.exec_module(geometry)


def by_name(spec):
    return {primitive.name: primitive for primitive in spec.primitives}


def numeric_values(value):
    if isinstance(value, dict):
        for child in value.values():
            yield from numeric_values(child)
    elif isinstance(value, (tuple, list)):
        for child in value:
            yield from numeric_values(child)
    elif isinstance(value, (float, int)):
        yield value


class UtilityGeometryTests(unittest.TestCase):
    def test_exact_candidate_identity_and_state_allowlists(self):
        self.assertEqual(geometry.CANDIDATES, (
            "studio-utility-stats", "studio-utility-brightness", "studio-utility-overflow"))
        for bad in ("stats", "monitor-brightness", "view-more", "", "../trash"):
            with self.assertRaises(ValueError):
                geometry.utility_geometry(bad)
        for candidate in geometry.CANDIDATES:
            for bad in ("paused", "unavailable", "mixed", "linked", "empty", "EXPANDED"):
                with self.assertRaises(ValueError):
                    geometry.utility_geometry(candidate, state=bad)
        for candidate in geometry.CANDIDATES[:2]:
            for bad in ("collapsed", "expanded"):
                with self.assertRaises(ValueError):
                    geometry.utility_geometry(candidate, state=bad)
        default = geometry.utility_geometry("studio-utility-overflow")
        self.assertEqual(default, geometry.utility_geometry("studio-utility-overflow", state="collapsed"))

    def test_specs_are_finite_deterministic_serializable_and_owned(self):
        for candidate, state in [(c, "default") for c in geometry.CANDIDATES] + [
                ("studio-utility-overflow", "expanded")]:
            spec = geometry.utility_geometry(candidate, state=state)
            self.assertEqual(spec.candidate, candidate)
            self.assertEqual(spec, geometry.utility_geometry(candidate, state=state))
            json.dumps(asdict(spec), allow_nan=False)
            self.assertTrue(all(math.isfinite(v) for v in numeric_values(asdict(spec))))
            self.assertEqual(len(by_name(spec)), len(spec.primitives))
            materials = {m.name for m in spec.materials}
            for primitive in spec.primitives:
                self.assertIn(primitive.collection, geometry.COLLECTIONS[:3])
                self.assertIn(primitive.material, materials)
                if isinstance(primitive, geometry.RoundedPlate):
                    self.assertGreater(primitive.radius, 0)
                    self.assertLessEqual(primitive.radius, min(primitive.size) / 2)
                    points = geometry._plate_points(primitive)
                    self.assertEqual(len(points), 36)
                    self.assertEqual(len(set(points)), len(points))
                    for axis in (0, 1):
                        self.assertAlmostEqual(max(p[axis] for p in points),
                                               primitive.center[axis] + primitive.size[axis] / 2)
                        self.assertAlmostEqual(min(p[axis] for p in points),
                                               primitive.center[axis] - primitive.size[axis] / 2)
                else:
                    points = primitive.points
                margin = primitive.radius if isinstance(primitive, geometry.Stroke) else primitive.bevel
                self.assertTrue(all(abs(v) + margin <= 2.05 for p in points for v in p[:2]))
                if not isinstance(primitive, geometry.Stroke):
                    self.assertGreater(primitive.half_depth, 0)
                    self.assertGreater(primitive.bevel, 0)
                    if primitive.collection != "Backing":
                        z = primitive.center[2] if isinstance(primitive, geometry.RoundedPlate) else primitive.z
                        self.assertGreater(z - primitive.half_depth - primitive.bevel, 0.06)

    def test_backing_is_only_approved_clip_normalized_without_interior(self):
        spec = geometry.utility_geometry("studio-utility-stats")
        backing = by_name(spec)["family-backing"]
        self.assertEqual(backing.collection, "Backing")
        self.assertEqual(len(backing.points), 512)
        self.assertEqual(backing.points[0], (2.0, 0.0))
        for axis in (0, 1):
            self.assertEqual(min(p[axis] for p in backing.points), -2.0)
            self.assertEqual(max(p[axis] for p in backing.points), 2.0)
        self.assertAlmostEqual(backing.z + backing.half_depth + backing.bevel, 0.06)
        for candidate in geometry.CANDIDATES:
            with patch.object(Path, "read_text", side_effect=AssertionError("Unexpected file read")):
                bare = geometry.utility_geometry(candidate, include_backing=False)
            full = geometry.utility_geometry(candidate)
            self.assertEqual(bare.primitives, full.primitives[1:])

    def test_backing_parser_rejects_unapproved_syntax_and_ignores_interior(self):
        def svg(path, extra=""):
            return ('<svg xmlns="http://www.w3.org/2000/svg"><defs><clipPath id="studio_clip">'
                    f'<path d="{path}"/></clipPath></defs>{extra}</svg>')
        path = "M100,512L512,100L924,512Z"
        self.assertEqual(geometry._parse_backing(svg(path, '<path d="vendor interior ignored"/>')),
                         ((-2.0, 0.0), (0.0, 2.0), (2.0, 0.0)))
        for bad in ("", "M100,512Q512,100 924,512Z", "m100,512l512,100l924,512z",
                    "M100,512L512,100L924,512", "M99,512L512,100L924,512Z", "Mnan,512L512,100L924,512Z"):
            with self.assertRaises(ValueError):
                geometry._parse_backing(svg(bad))
        for bad in (svg(path).replace('id="studio_clip"', 'id="other"'),
                    svg(path).replace('<path d=', '<path transform="scale(2)" d='),
                    svg(path).replace('</clipPath>', '<path d="M1,2L3,4L5,6Z"/></clipPath>')):
            with self.assertRaises(ValueError):
                geometry._parse_backing(bad)

    def test_stats_has_instrument_rail_and_distinct_unequal_data_bars(self):
        objects = by_name(geometry.utility_geometry("studio-utility-stats", include_backing=False))
        self.assertEqual(set(objects), {"instrument-rail", "data-bar-1", "data-bar-2", "data-bar-3"})
        rail = objects["instrument-rail"]
        self.assertEqual(rail.center[:2], (0.0, 0.85))
        self.assertEqual(rail.size, (2.65, 0.18))
        for i, (x, h) in enumerate(zip((-0.78, 0.0, 0.78), (0.65, 1.55, 1.10)), 1):
            bar = objects[f"data-bar-{i}"]
            self.assertEqual(bar.size, (0.42, h))
            self.assertEqual(bar.center[0], x)
            self.assertAlmostEqual(bar.center[1] - h / 2, -1.0)
            self.assertEqual(bar.material, "graphite")
            self.assertLess(bar.center[1] + h / 2 + bar.bevel,
                            rail.center[1] - rail.size[1] / 2 - rail.bevel)

    def test_brightness_has_two_separate_screens_stands_and_shared_light_control(self):
        objects = by_name(geometry.utility_geometry("studio-utility-brightness", include_backing=False))
        self.assertEqual(len(objects), 13)
        for side, x in (("left", -0.78), ("right", 0.78)):
            body = objects[f"{side}-display-body"]
            screen = objects[f"{side}-display-screen"]
            self.assertEqual(body.center[:2], (x, -0.35))
            self.assertEqual(body.size, (1.28, 0.92))
            self.assertEqual(screen.center[:2], body.center[:2])
            self.assertTrue(all(a < b for a, b in zip(screen.size, body.size)))
            self.assertGreater(screen.center[2] - screen.half_depth - screen.bevel,
                               body.center[2] + body.half_depth + body.bevel)
            for part in ("stem", "foot"):
                self.assertEqual(objects[f"{side}-display-{part}"].center[0], x)
        left, right = objects["left-display-body"], objects["right-display-body"]
        self.assertGreater(right.center[0] - right.size[0] / 2 - right.bevel,
                           left.center[0] + left.size[0] / 2 + left.bevel)
        disc = objects["light-control-disc"]
        for x, y in disc.points:
            self.assertAlmostEqual(math.hypot(x, y - 0.87), 0.23)
        rays = [p for name, p in objects.items() if name.startswith("light-control-ray-")]
        self.assertEqual(len(rays), 4)
        for ray in rays:
            for point, radius in zip(ray.points, (0.38, 0.56)):
                self.assertAlmostEqual(math.hypot(point[0], point[1] - 0.87), radius)

    def test_overflow_shutter_reveals_only_third_block_and_chevron_reverses(self):
        collapsed = geometry.utility_geometry("studio-utility-overflow")
        expanded = geometry.utility_geometry("studio-utility-overflow", state="expanded")
        before, after = by_name(collapsed), by_name(expanded)
        self.assertEqual(set(before), set(after))
        self.assertEqual({name for name in before if before[name] != after[name]},
                         {"reveal-shutter", "reveal-chevron"})
        self.assertEqual(collapsed.camera, expanded.camera)
        self.assertEqual(collapsed.lights, expanded.lights)
        self.assertEqual(collapsed.materials, expanded.materials)
        block, shutter = before["status-block-3"], before["reveal-shutter"]
        for axis in (0, 1):
            self.assertGreater(shutter.center[axis] + shutter.size[axis] / 2,
                               block.center[axis] + block.size[axis] / 2 + block.bevel)
            self.assertLess(shutter.center[axis] - shutter.size[axis] / 2,
                            block.center[axis] - block.size[axis] / 2 - block.bevel)
        self.assertGreater(shutter.center[2] - shutter.half_depth - shutter.bevel,
                           block.center[2] + block.half_depth + block.bevel)
        second = before["status-block-2"]
        self.assertGreater(shutter.center[0] - shutter.size[0] / 2 - shutter.bevel,
                           second.center[0] + second.size[0] / 2 + second.bevel)
        moved = after["reveal-shutter"]
        self.assertGreater(moved.center[0] - moved.size[0] / 2 - moved.bevel,
                           block.center[0] + block.size[0] / 2 + block.bevel)
        self.assertGreater(before["reveal-chevron"].points[1][0], before["reveal-chevron"].points[0][0])
        self.assertLess(after["reveal-chevron"].points[1][0], after["reveal-chevron"].points[0][0])

    def test_materials_are_neutral_opaque_identity_with_restrained_coat(self):
        for candidate in geometry.CANDIDATES:
            spec = geometry.utility_geometry(candidate, include_backing=False)
            self.assertEqual({m.srgb for m in spec.materials}, {"#E9EFF6", "#30343A", "#F4F6F8"})
            for material in spec.materials:
                self.assertEqual(material.metallic, 0)
                self.assertEqual(material.transmission, 0)
                self.assertEqual(material.ior, 1.45)
                self.assertLessEqual(material.coat, 0.15)
                self.assertTrue(0.30 <= material.roughness <= 0.38)
        self.assertEqual(geometry.srgb_to_linear("#000000"), (0.0, 0.0, 0.0, 1.0))
        self.assertEqual(geometry.srgb_to_linear("#FFFFFF"), (1.0, 1.0, 1.0, 1.0))
        self.assertAlmostEqual(geometry.srgb_to_linear("#808080")[0], 0.2158605001)
        self.assertAlmostEqual(geometry.srgb_to_linear("#010101")[0], 1 / 255 / 12.92)
        for bad in ("white", "#ffff", "#ffffff00", "#gggggg"):
            with self.assertRaises(ValueError):
                geometry.srgb_to_linear(bad)

    def test_lighting_is_near_front_orthographic_and_key_dominant(self):
        spec = geometry.utility_geometry("studio-utility-stats", include_backing=False)
        self.assertEqual(spec.camera, geometry.CameraIntent((0.0, -0.25, 10.0), (0.0, 0.0, 0.0), 5.0))
        key, fill = spec.lights
        self.assertLess(key.location[0], 0)
        self.assertGreater(key.location[1], 0)
        self.assertGreater(fill.location[0], 0)
        self.assertGreater(key.energy, fill.energy)

    def test_fresh_import_performs_no_writes_or_blender_import(self):
        script = '''
import os
import sys

def audit(event, args):
    if event == "open":
        mode, flags = args[1:3]
        if (isinstance(mode, str) and any(c in mode for c in "wax+")) or flags & (os.O_CREAT | os.O_TRUNC | os.O_APPEND | os.O_WRONLY | os.O_RDWR):
            raise AssertionError("Import attempted a write")
    if event == "import" and args[0] in ("bpy", "mathutils"):
        raise AssertionError("Import attempted Blender access")
    if event.startswith(("subprocess.", "socket.")) or event in ("os.system", "os.remove", "os.mkdir", "os.rename"):
        raise AssertionError(event)
sys.addaudithook(audit)
import icons.utilities.geometry
assert "bpy" not in sys.modules
'''
        result = subprocess.run([sys.executable, "-B", "-c", script],
                                cwd=SOURCE.parents[2], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_adapter_source_avoids_global_context_operators_and_destructive_apis(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                self.assertNotIn(node.attr, {"ops", "context", "remove", "unlink", "save", "save_as_mainfile", "open_mainfile"})
            if isinstance(node, ast.ImportFrom):
                self.assertNotIn("build_glass", node.module or "")
            if isinstance(node, ast.Import):
                self.assertFalse(any("build_glass" in alias.name for alias in node.names))
        with patch.object(Path, "read_text", side_effect=AssertionError("Unexpected read")):
            with self.assertRaises(ValueError):
                geometry.create_utility_scene("trash")
            with self.assertRaises(ValueError):
                geometry.create_utility_scene("studio-utility-stats", state="expanded")

    def test_adapter_new_owned_data_only_using_a_fake_blender_api(self):
        # This checks adapter calls, NOT Blender compatibility or rendered optics.
        class Points(list):
            def __init__(self):
                super().__init__([SimpleNamespace(co=None)])

            def add(self, count):
                self.extend(SimpleNamespace(co=None) for _ in range(count))

        stores = {}
        registries = {}
        for kind in ("scenes", "collections", "materials", "objects", "curves", "cameras", "lights", "worlds"):
            stores[kind] = []

            def new(name, *args, kind=kind):
                data = MagicMock()
                used = {item.name for item in stores[kind]}
                data.name = name if name not in used else f"{name}.{len(used):03}"
                data.location = SimpleNamespace(z=0)
                if kind == "curves":
                    data.splines.new.return_value.points = Points()
                stores[kind].append(data)
                return data

            registries[kind] = SimpleNamespace(new=MagicMock(side_effect=new))
        fake_bpy = SimpleNamespace(data=SimpleNamespace(**registries))
        with patch.dict(sys.modules, {"bpy": fake_bpy, "mathutils": SimpleNamespace(Vector=MagicMock())}):
            scenes = [geometry.create_utility_scene("studio-utility-brightness", include_backing=False) for _ in range(2)]
        self.assertEqual(len(stores["scenes"]), 2)
        self.assertNotEqual(scenes[0].name, scenes[1].name)
        self.assertEqual(len(stores["collections"]), 8)
        self.assertEqual(len(stores["objects"]), 32)  # 13 shapes + camera + two lights per scene
        self.assertEqual(len(stores["curves"]), 26)
        for scene in scenes:
            scene.__setitem__.assert_any_call("utility_owner", scene.name)
            scene.__setitem__.assert_any_call("approval", "pending")
            self.assertEqual(scene.collection.children.link.call_count, 4)
        for kind, items in stores.items():
            if kind == "scenes":
                continue
            for data in items:
                owner = data.name.split("/")[0]
                self.assertIn(owner, {s.name for s in scenes})
                data.__setitem__.assert_any_call("utility_owner", owner)
        for curve in stores["curves"]:
            spline = curve.splines.new.return_value
            self.assertTrue(all(point.co is not None for point in spline.points))
            if "ray-" in curve.name:
                self.assertEqual(curve.dimensions, "3D")
                self.assertTrue(curve.use_fill_caps)
                self.assertFalse(spline.use_cyclic_u)
                self.assertEqual(len(spline.points), 2)
            else:
                self.assertEqual(curve.dimensions, "2D")
                self.assertEqual(curve.fill_mode, "BOTH")
                self.assertTrue(spline.use_cyclic_u)
                self.assertIn(curve.extrude, (0.015, 0.035))
        for camera in stores["cameras"]:
            self.assertEqual(camera.type, "ORTHO")
            self.assertEqual(camera.ortho_scale, 5.0)


if __name__ == "__main__":
    unittest.main()
