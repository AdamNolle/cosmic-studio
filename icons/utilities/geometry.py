"""Inactive, original utility artwork specifications; not deployed icon aliases.

XY is the four-unit icon plane, front is +Z. Unequal statistics bars are identity,
not readings; the two displays denote capability, not connected hardware. Only
artwork states are modeled here; live/accessibility and small symbolic states
belong to separate native controls. Materials and lighting are starting intent,
not optical approval. No files or Blender data are touched at module import.

The optional backing reads only the existing Studio family studio_clip contour;
no upstream identifying interior, image texture or vendor mark is copied. Existing
source attribution/licensing remains with that SVG, unchanged.
"""

from dataclasses import dataclass
from math import cos, isfinite, pi, sin
from pathlib import Path
import re
from typing import Union
import xml.etree.ElementTree as ET


CANDIDATES = (
    "studio-utility-stats",
    "studio-utility-brightness",
    "studio-utility-overflow",
)
COLLECTIONS = ("Backing", "Identity", "State", "Lights")
BACKING_SOURCE = "icons/system-apps/sources/svg/com.system76.CosmicMonitor.svg#studio_clip"

Point2 = tuple[float, float]
Point3 = tuple[float, float, float]


@dataclass(frozen=True)
class MaterialIntent:
    name: str
    srgb: str
    roughness: float
    coat: float = 0.12
    metallic: float = 0.0
    transmission: float = 0.0
    ior: float = 1.45


@dataclass(frozen=True)
class RoundedPlate:
    name: str
    collection: str
    material: str
    center: Point3
    size: Point2
    radius: float
    half_depth: float = 0.035
    bevel: float = 0.025


@dataclass(frozen=True)
class Relief:
    name: str
    collection: str
    material: str
    points: tuple[Point2, ...]
    z: float
    half_depth: float
    bevel: float


@dataclass(frozen=True)
class Stroke:
    name: str
    collection: str
    material: str
    points: tuple[Point3, ...]
    radius: float = 0.04


Primitive = Union[RoundedPlate, Relief, Stroke]


@dataclass(frozen=True)
class CameraIntent:
    location: Point3 = (0.0, -0.25, 10.0)
    target: Point3 = (0.0, 0.0, 0.0)
    orthographic_scale: float = 5.0


@dataclass(frozen=True)
class LightIntent:
    name: str
    location: Point3
    energy: float
    size: float
    target: Point3 = (0.0, 0.0, 0.0)


@dataclass(frozen=True)
class UtilityGeometry:
    candidate: str
    state: str
    primitives: tuple[Primitive, ...]
    materials: tuple[MaterialIntent, ...]
    camera: CameraIntent
    lights: tuple[LightIntent, ...]


def srgb_to_linear(hex_color: str) -> tuple[float, float, float, float]:
    """Convert literal sRGB colors before assigning Principled shader values."""
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", hex_color):
        raise ValueError("Expected #RRGGBB")
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
                 for c in channels) + (1.0,)


def _parse_backing(svg: str) -> tuple[Point2, ...]:
    """Accept only the approved explicit M/L/Z contour, never approximate syntax."""
    ns = {"s": "http://www.w3.org/2000/svg"}
    clips = ET.fromstring(svg).findall("./s:defs/s:clipPath[@id='studio_clip']", ns)
    if len(clips) != 1 or len(clips[0]) != 1:
        raise ValueError("Expected one studio_clip containing one path")
    path = clips[0][0]
    if path.tag != "{http://www.w3.org/2000/svg}path" or "transform" in path.attrib or "transform" in clips[0].attrib:
        raise ValueError("Unsupported backing transform or element")
    number = r"-?\d+(?:\.\d+)?"
    pair = rf"{number},{number}"
    data = path.get("d", "")
    if not re.fullmatch(rf"M{pair}(?:L{pair}){{2,}}Z", data):
        raise ValueError("Unsupported backing path syntax")
    points = tuple(((float(x) - 512) / 206, (512 - float(y)) / 206)
                   for x, y in re.findall(rf"[ML]({number}),({number})", data))
    if any(not isfinite(v) or abs(v) > 2 for point in points for v in point):
        raise ValueError("Backing outside the four-unit composition")
    return points


def _backing() -> Relief:
    source = Path(__file__).resolve().parents[1] / "system-apps/sources/svg/com.system76.CosmicMonitor.svg"
    return Relief("family-backing", "Backing", "backing", _parse_backing(source.read_text(encoding="utf-8")),
                  0.0, 0.04, 0.02)


def _rail() -> RoundedPlate:
    return RoundedPlate("instrument-rail", "Identity", "graphite", (0.0, 0.85, 0.18), (2.65, 0.18), 0.06)


def _stats() -> tuple[Primitive, ...]:
    return (_rail(),) + tuple(
        RoundedPlate(f"data-bar-{i}", "Identity", "graphite", (x, -1.0 + height / 2, 0.18),
                     (0.42, height), 0.07)
        for i, (x, height) in enumerate(zip((-0.78, 0.0, 0.78), (0.65, 1.55, 1.10)), 1)
    )


def _brightness() -> tuple[Primitive, ...]:
    objects: list[Primitive] = []
    for side, x in (("left", -0.78), ("right", 0.78)):
        objects.extend((
            RoundedPlate(f"{side}-display-body", "Identity", "graphite", (x, -0.35, 0.18), (1.28, 0.92), 0.12),
            RoundedPlate(f"{side}-display-screen", "Identity", "contrast", (x, -0.35, 0.28),
                         (1.02, 0.66), 0.065, 0.015, 0.025),
            RoundedPlate(f"{side}-display-stem", "Identity", "graphite", (x, -0.96, 0.18), (0.16, 0.30), 0.04),
            RoundedPlate(f"{side}-display-foot", "Identity", "graphite", (x, -1.14, 0.18), (0.65, 0.14), 0.04),
        ))
    disc = tuple((0.23 * cos(i * pi / 16), 0.87 + 0.23 * sin(i * pi / 16)) for i in range(32))
    objects.append(Relief("light-control-disc", "Identity", "graphite", disc, 0.18, 0.035, 0.025))
    for name, dx, dy in (("east", 1, 0), ("north", 0, 1), ("west", -1, 0), ("south", 0, -1)):
        objects.append(Stroke(f"light-control-ray-{name}", "Identity", "graphite",
                              tuple((dx * r, 0.87 + dy * r, 0.20) for r in (0.38, 0.56))))
    return tuple(objects)


def _overflow(expanded: bool) -> tuple[Primitive, ...]:
    blocks = tuple(RoundedPlate(f"status-block-{i}", "Identity", "graphite", (x, 0.0, 0.18),
                                (0.36, 0.44), 0.05)
                   for i, x in enumerate((-0.85, -0.10, 0.65), 1))
    # Opaque shutter covers only block three; the expanded position clears it.
    shutter = RoundedPlate("reveal-shutter", "State", "contrast", (1.35 if expanded else 0.66, 0.0, 0.36),
                           (0.64, 0.88), 0.07)
    tip, tail = (0.87, 1.17) if expanded else (1.17, 0.87)
    chevron = Stroke("reveal-chevron", "State", "graphite",
                     ((tail, -0.68, 0.20), (tip, -0.90, 0.20), (tail, -1.12, 0.20)))
    return (_rail(),) + blocks + (shutter, chevron)


def utility_geometry(candidate: str, *, state: str = "default", include_backing: bool = True) -> UtilityGeometry:
    """Return editable candidate specs. Only overflow has collapsed/expanded art.

    include_backing=False avoids even the explicit read of the family SVG.
    Unsupported identities/states fail before any file or Blender access.
    """
    if candidate not in CANDIDATES:
        raise ValueError(f"Unknown utility candidate: {candidate!r}")
    overflow = candidate == "studio-utility-overflow"
    if state not in (("default", "collapsed", "expanded") if overflow else ("default",)):
        raise ValueError(f"Unsupported artwork state: {state!r}")
    if overflow:
        state = "collapsed" if state == "default" else state
        primitives = _overflow(state == "expanded")
    else:
        primitives = _stats() if candidate == "studio-utility-stats" else _brightness()
    if include_backing:
        primitives = (_backing(),) + primitives
    return UtilityGeometry(candidate, state, primitives, (
        MaterialIntent("backing", "#E9EFF6", 0.34),
        MaterialIntent("graphite", "#30343A", 0.34),
        MaterialIntent("contrast", "#F4F6F8", 0.30),
    ), CameraIntent(), (
        LightIntent("upper-left-key", (-3.0, 4.0, 6.0), 450.0, 5.0),
        LightIntent("right-fill", (4.0, 1.0, 4.0), 120.0, 4.0),
    ))


def _plate_points(plate: RoundedPlate) -> tuple[Point2, ...]:
    x, y, _ = plate.center
    w, h = plate.size
    r = plate.radius
    points = []
    for cx, cy, angle in ((x + w / 2 - r, y + h / 2 - r, 0),
                          (x - w / 2 + r, y + h / 2 - r, pi / 2),
                          (x - w / 2 + r, y - h / 2 + r, pi),
                          (x + w / 2 - r, y - h / 2 + r, 3 * pi / 2)):
        points.extend((cx + r * cos(angle + i * pi / 16), cy + r * sin(angle + i * pi / 16))
                      for i in range(9))
    return tuple(points)


def create_utility_scene(candidate: str, *, state: str = "default", include_backing: bool = True):
    """Explicit, lazy Blender 4+ adapter; return a NEW owned, inactive scene.

    Uses data APIs only. Never switches the active scene, edits existing data,
    saves, renders, removes objects, or imports historical generators. Blender
    execution and optical/editability review require separate authorization.
    """
    spec = utility_geometry(candidate, state=state, include_backing=include_backing)
    import bpy
    from mathutils import Vector

    scene = bpy.data.scenes.new(f"candidate-{candidate}-{spec.state}")
    owner = scene.name
    scene["utility_candidate"] = candidate
    scene["artwork_state"] = spec.state
    scene["approval"] = "pending"

    def own(data):
        data["utility_owner"] = owner
        return data

    own(scene)
    collections = {}
    for name in COLLECTIONS:
        collection = own(bpy.data.collections.new(f"{owner}/{name}"))
        scene.collection.children.link(collection)
        collections[name] = collection

    materials = {}
    for intent in spec.materials:
        material = own(bpy.data.materials.new(f"{owner}/{intent.name}"))
        material.use_nodes = True
        shader = material.node_tree.nodes.get("Principled BSDF")
        for name, value in (("Base Color", srgb_to_linear(intent.srgb)), ("Metallic", intent.metallic),
                            ("Roughness", intent.roughness), ("Coat Weight", intent.coat),
                            ("Transmission Weight", intent.transmission), ("IOR", intent.ior)):
            shader.inputs[name].default_value = value
        materials[intent.name] = material

    def link(name, data, collection):
        obj = own(bpy.data.objects.new(f"{owner}/{name}", own(data)))
        collections[collection].objects.link(obj)
        return obj

    for primitive in spec.primitives:
        curve = own(bpy.data.curves.new(f"{owner}/{primitive.name}", "CURVE"))
        curve.resolution_u = 16
        curve.bevel_resolution = 3
        stroke = isinstance(primitive, Stroke)
        curve.dimensions = "3D" if stroke else "2D"
        if stroke:
            points = primitive.points
            curve.bevel_depth = primitive.radius
            curve.use_fill_caps = True
        else:
            xy = _plate_points(primitive) if isinstance(primitive, RoundedPlate) else primitive.points
            points = tuple((x, y, 0.0) for x, y in xy)
            curve.fill_mode = "BOTH"
            # Curve extrusion extends on BOTH sides of the local XY plane.
            curve.extrude = primitive.half_depth
            curve.bevel_depth = primitive.bevel
        spline = curve.splines.new("POLY")
        spline.points.add(len(points) - 1)
        for point, xyz in zip(spline.points, points):
            point.co = (*xyz, 1.0)
        spline.use_cyclic_u = not stroke
        curve.materials.append(materials[primitive.material])
        obj = link(primitive.name, curve, primitive.collection)
        if not stroke:
            obj.location.z = primitive.center[2] if isinstance(primitive, RoundedPlate) else primitive.z

    def aim(obj, location, target):
        obj.location = location
        obj.rotation_euler = (Vector(target) - Vector(location)).to_track_quat("-Z", "Y").to_euler()

    camera = bpy.data.cameras.new(f"{owner}/camera")
    camera.type = "ORTHO"
    camera.ortho_scale = spec.camera.orthographic_scale
    scene.camera = link("camera", camera, "Lights")
    aim(scene.camera, spec.camera.location, spec.camera.target)
    for intent in spec.lights:
        light = bpy.data.lights.new(f"{owner}/{intent.name}", "AREA")
        light.energy = intent.energy
        light.shape = "DISK"
        light.size = intent.size
        aim(link(intent.name, light, "Lights"), intent.location, intent.target)
    world = own(bpy.data.worlds.new(f"{owner}/world"))
    world.use_nodes = True
    world.node_tree.nodes.get("Background").inputs["Strength"].default_value = 0.25
    scene.world = world
    scene.render.film_transparent = True
    return scene
