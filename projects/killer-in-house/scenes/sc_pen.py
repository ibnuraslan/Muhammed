"""CH3: the state penitentiary at Cañon City. Tall stone walls and a gate tower under dry foothills and mountains.
  gate  (A): a prison van drives through the gate in the stone wall; mountains beyond; slow pan.
  wall  (B): two guards walk the wall-top; slow pan across the yard and the mountains.
  cell  (C): the thin man sits on a cot in a narrow stone cell; the camera pulls slowly back through the bars.
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from common import grid_mesh
import house as H
from house import reset_pose
from human import pose_sit

DUR = {"gate": 5.0, "wall": 5.0, "cell": 6.0}
VARIANT_FOR = {k: k for k in DUR}


def mountains():
    n = 200; rng = np.random.default_rng(7)
    xs = np.linspace(-1, 1, n)
    X, Y = np.meshgrid(xs, xs)
    h = np.zeros_like(X)
    for k in range(6):
        f = 2 ** k; ph_ = rng.uniform(0, 6.28, 2)
        h += (0.5 ** k) * np.sin(X * 3 * f + ph_[0]) * np.cos(Y * 2.3 * f + ph_[1])
    ridge = np.clip((Y + 0.2) * 1.4, 0, 1)
    h = (h * 0.5 + 0.6) * ridge
    o = grid_mesh("Mountains", h.astype(np.float32), 2400, 1200, 420, origin=(0, 900, -20))
    o.data.materials.append(H.ph.texture("rock_face", 0.004, name="MtnRock", tint=(0.85, 0.75, 0.62)))
    return o


def stone():
    return H.ph.texture("stone_wall", 0.45, name="PenStone", tint=(0.92, 0.84, 0.72))


def build(variant=None):
    c = {}
    if variant == "cell":
        world_flat((0.5, 0.6, 0.75), 1.2)
        bpy.context.scene.view_settings.exposure = 0.6
        st = stone()
        box("CFloor", (0, 0, -0.02), (3, 6, 0.04), H.mat("conc"))
        for x in (-1.1, 1.1):
            box("CWall", (x, 0, 1.5), (0.4, 6, 3.0), st)
        H.wall_x("CBack", -1.3, 1.3, 2.3, 0, 3.0, 0.4, st, [(-0.2, 0.2, 2.15, 2.45)]); box("CCeil", (0, 0, 3.0), (2.6, 6, 0.2), st)
        box("CDoorWall", (0, -3.0, 1.5), (2.6, 0.3, 3.0), st)
        for k in range(3):
            box("CWinBar", (-0.12 + k * 0.12, 2.07, 2.3), (0.02, 0.02, 0.32), H.mat("iron"))
        sl = bpy.data.lights.new("Shaft", 'AREA'); sl.size = 0.4; sl.energy = 120; sl.color = (0.9, 0.95, 1.0)
        so = bpy.data.objects.new("Shaft", sl); bpy.context.collection.objects.link(so); so.location = (0, 2.0, 2.3); so.rotation_euler = (math.radians(-60), 0, 0)
        c["haze"] = haze((0, 0, 1.5), (1.8, 6, 3.0), density=0.04, color=(0.9, 0.92, 1.0), anis=0.6)
        for k in range(12):
            box("Bar", (-0.9 + k * 0.165, -1.2, 1.2), (0.025, 0.025, 2.4), H.mat("iron"))
        box("BarTop", (0, -1.2, 2.4), (2.0, 0.06, 0.08), H.mat("iron")); box("BarMid", (0, -1.2, 1.2), (2.0, 0.04, 0.05), H.mat("iron"))
        box("Cot", (-0.55, 0.9, 0.38), (0.7, 1.9, 0.08), H.mat("iron")); box("CotMat", (-0.55, 0.9, 0.46), (0.66, 1.85, 0.08), fabric("CotBlanket", (0.35, 0.33, 0.28), 0.95, 0.3, 300), bevel=0.02)
        for sy in (-1, 1):
            box("CotLeg", (-0.55, 0.9 + sy * 0.9, 0.19), (0.66, 0.04, 0.38), H.mat("iron"))
        H.point((0, -2.5, 2.6), 20, (1.0, 0.8, 0.55), 0.2)
        c["man"] = H.person("Thin", "thin_court")
        return c
    world_sky(sun_elev_deg=26, sun_rot_deg=120, strength=0.55, tint=(1.0, 0.96, 0.9))
    sun(26, -30, energy=3.2, color=(1.0, 0.9, 0.75), angle_deg=1.2)
    bpy.context.scene.view_settings.exposure = -0.5
    mountains()
    box("Ground", (0, 0, -0.05), (400, 400, 0.1), H.ph.texture("dry_ground_rocks", 0.2, name="DryGround"))
    box("Road", (0, -30, -0.02), (7, 60, 0.05), H.mat("asphalt"))
    st = stone()
    H.wall_x("PenWall", -60, 60, 0, 0, 8, 1.4, st, [(-3.0, 3.0, 0, 5.0)])
    box("Parapet", (0, 0, 8.3), (120, 1.6, 0.6), st)
    for x in (-6.0, 6.0):
        box("Tower", (x, 0, 6.0), (4.0, 4.0, 12), st)
        box("TowerCap", (x, 0, 12.3), (4.6, 4.6, 0.6), st)
        box("TowerWin", (x, -2.02, 10.0), (1.2, 0.05, 1.0), pbr("TWin", (0.02, 0.02, 0.03), 0.1))
    c["gate"] = box("Gate", (0, -0.2, 2.5), (5.8, 0.15, 5.0), H.mat("iron"))
    for k in range(10):
        box("GateBar", (-2.6 + k * 0.58, -0.35, 2.5), (0.06, 0.06, 5.0), H.mat("iron"))
    box("Yard", (0, 30, 0.0), (120, 60, 0.02), H.mat("pave"))
    for k in range(3):
        box("CellBlock", (-20 + k * 20, 35, 7), (14, 10, 14), st)
    if variant == "gate":
        c["van"] = H.vehicle("PVan", (0.1, 0.11, 0.1))
    else:
        c["guards"] = [H.person("Guard%d" % k, "officer") for k in range(2)]
    return c


def anim_gate(c, t):
    sec = t * DUR["gate"]
    up = ease(min(1.0, sec / 2.0))
    c["gate"].location.z = 2.5 + 4.6 * up
    for o in bpy.data.objects:
        if o.name.startswith("GateBar"):
            o.location.z = 2.5 + 4.6 * up
    H.drive(c["van"], (0, -28, 0), (0, 12, 0), ease(t) * 0.85, heading=math.radians(90))


def anim_wall(c, t):
    for k, h in enumerate(c["guards"]):
        H.walk_to(h, (-22 + 3 * k, 0.0, 8.6), (-10 + 3 * k, 0.0, 8.6), t * 0.6, swing=10, stride=1.0)


def anim_cell(c, t):
    sec = t * DUR["cell"]
    h = c["man"]; reset_pose(h); pose_sit(h, lean=26)
    h.arm.rotation_euler = (0, 0, math.radians(-90)); h.arm.location = (-0.55, 0.7, 0); bpy.context.view_layer.update(); H.ground_to(h, 0.0)
    H.rotl(h, "head", (1, 0, 0), 20 + 2 * math.sin(0.6 * sec))


MOVES = {
    "gate": dict(kind="anim", dof=None, far=500, anim=anim_gate,
                 cam=lambda c, t: (Vector((14, -32, 1.8)).lerp(Vector((10, -30, 2.0)), ease(t)), Vector((0, 0, 4.5)).lerp(Vector((0, 4, 5.5)), ease(t)), 28)),
    "wall": dict(kind="anim", dof=None, far=500, anim=anim_wall,
                 cam=lambda c, t: (Vector((-30, -18, 10.0)).lerp(Vector((-24, -20, 10.5)), ease(t)), Vector((-16, 0, 9.0)).lerp(Vector((-4, 40, 14)), ease(t)), 30)),
    "cell": dict(kind="anim", dof=None, far=20, anim=anim_cell,
                 cam=lambda c, t: (Vector((0.15, -0.9, 1.45)).lerp(Vector((0.15, -2.6, 1.55)), ease(t)), Vector((-0.4, 0.8, 1.0)), 30)),
}
