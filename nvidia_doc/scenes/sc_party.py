"""Trade-show party (illustration): lounge, cocktail table, two empty chairs side by side, colourful bokeh. No people."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *

EXPOSURE = 0.4


def lounge_chair(loc, rot, fab, leg):
    parts = [box("Seat", (0, 0, 0.42), (0.6, 0.58, 0.12), fab, bevel=0.04),
             box("Back", (0, 0.26, 0.72), (0.6, 0.1, 0.52), fab, bevel=0.05)]
    for dx in (-0.25, 0.25):
        for dy in (-0.23, 0.23):
            parts.append(cyl("Leg", (dx, dy, 0.18), 0.015, 0.36, leg, verts=12))
    c = join(parts, "Lounge"); c.location = loc; c.rotation_euler = (0, 0, rot)
    for p in c.data.polygons:
        p.use_smooth = True
    m = c.modifiers.new("sub", 'SUBSURF'); m.levels = 1; m.render_levels = 2
    return c


def glass_tumbler(loc, liquid=(0.6, 0.3, 0.08)):
    g = cyl("Glass", loc, 0.035, 0.11, glass("Tumbler", (0.96, 0.98, 0.99)), verts=32)
    sol = g.modifiers.new("solid", 'SOLIDIFY'); sol.thickness = 0.003
    l = cyl("Liquid", (loc[0], loc[1], loc[2] - 0.02), 0.031, 0.06, pbr("Drink", liquid, 0.02, 0.0, **{'Transmission Weight': 1.0, 'IOR': 1.36}), verts=32)
    return g


def build(variant=None):
    world_flat((0.01, 0.008, 0.016), 1.0)
    r = np.random.default_rng(14)
    floor = box("Floor", (0, 0, -0.01), (30, 30, 0.02), pbr("Floor", (0.02, 0.02, 0.025), 0.15, 0.0, **{'Coat Weight': 0.6}))
    velvet = fabric("Velvet", (0.06, 0.07, 0.11), 0.85, 0.9, 500)
    leg = brushed_metal("Brass", (0.8, 0.6, 0.32), (0.18, 0.3), 0.3)
    a = lounge_chair((-0.42, 0.0, 0), math.radians(12), velvet, leg)     # seats face the camera
    b = lounge_chair((0.42, 0.0, 0), math.radians(-12), velvet, leg)
    top = cyl("SideTable", (0.0, -0.75, 0.5), 0.3, 0.025, pbr("Marble", (0.75, 0.74, 0.72), 0.15, 0.0, **{'Coat Weight': 0.5}), verts=48)
    cyl("SideLeg", (0.0, -0.7, 0.25), 0.02, 0.5, leg, verts=16)
    glass_tumbler((-0.08, -0.72, 0.57)); glass_tumbler((0.1, -0.66, 0.57), (0.75, 0.55, 0.2))
    # the room: bar with backlit shelves, stage wash, string lights - all far and out of focus
    box("BackWall", (0, 9, 2.5), (24, 0.1, 5), pbr("BackWall", (0.015, 0.014, 0.02), 0.6))
    bar = emissive("BarGlow", (1.0, 0.7, 0.35), 0.6)
    box("BarShelf", (-3.5, 8.8, 1.6), (5, 0.1, 1.6), bar)
    cols = [(0.4, 0.2, 1.0), (0.2, 0.5, 1.0), (1.0, 0.35, 0.6), (1.0, 0.7, 0.3), (0.3, 0.9, 1.0)]
    mats = [emissive(f"Bokeh{k}", c, 25) for k, c in enumerate(cols)]
    proto = [None] * len(mats)
    for k, m in enumerate(mats):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.03, location=(0, 0, -20))
        proto[k] = bpy.context.active_object; proto[k].data.materials.append(m)
    for j in range(260):
        k = int(r.integers(0, len(mats)))
        instance(proto[k], (r.uniform(-9, 9), r.uniform(4, 8.7), r.uniform(0.6, 4.5)))
    for j in range(60):   # string lights in an arc
        x = -8 + j * 0.27
        instance(proto[3], (x, 6.5, 3.9 - 0.4 * math.sin(math.pi * j / 59)))
    for k, c in enumerate(cols[:3]):
        l = bpy.data.lights.new("Stage", 'SPOT'); l.energy = 2500; l.color = c; l.spot_size = math.radians(18); l.spot_blend = 0.4
        o = bpy.data.objects.new("Stage", l); bpy.context.collection.objects.link(o); o.location = (-4 + k * 4, 8, 5); point_at(o, (-2 + k * 2, 2, 0))
    key = area_light((-1.8, -1.6, 2.2), (0, 0, 0), 1.2, 45, (1.0, 0.82, 0.6)); point_at(key, (0, 0, 0.5))
    rim = area_light((1.5, 2.0, 1.8), (0, 0, 0), 1.0, 30, (0.5, 0.55, 1.0)); point_at(rim, (0, 0, 0.6))
    haze((0, 4, 2.5), (20, 10, 5), density=0.03, color=(0.9, 0.85, 1.0), anis=0.5)
    return dict(chairs=Vector((0, 0.05, 0.55)), table=Vector((0, -0.7, 0.58)))


MOVES = {
    "bokeh_drift": dict(kind="plate", dof=1.8, far=20.0, cam=lambda c, t: ((1.6, -2.6, 1.15), (0.0, 2.0, 1.0), 45), focus=lambda c, t: c["chairs"]),
    "rack_focus": dict(kind="plate", dof=1.4, far=20.0, cam=lambda c, t: ((0.55, -1.55, 0.78), c["table"], 60), focus=lambda c, t: c["table"]),
    "two_chairs": dict(kind="plate", dof=2.2, far=20.0, cam=lambda c, t: ((0.2, -2.4, 0.95), c["chairs"], 42), focus=lambda c, t: c["chairs"]),
}
