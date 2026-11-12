"""RAILWAY STATION, Moscow, night rain (dramatization; a generic terminus, not a likeness).
  handover : two men meet under a lamp on the station square; a small parcel changes hands (Ch2 6A)
  platform : under the platform canopy one of them stands alone as a train pulls out (Ch2 6B)"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph
from pbkit import joinm, masonry_facade, precip_curtains, soviet_car, ph_instances
from pbpeople import person, stand, walk_at, nod, look, hand_to, hide, fwd
from sc_street import wet_asphalt

EXPOSURE = 0.9
BOUNCES = 6
DUR = {"handover": 6.0, "platform": 6.5}
VARIANT_FOR = {"handover": "square", "platform": "platform"}
rng = np.random.default_rng(41)


def arched_facade(x0, x1, y, h, col=(0.45, 0.55, 0.48)):
    """Station front: green stucco with white pilasters and tall lit arched windows (simple geometry, lit from inside)."""
    st = pbr("StationStucco", col, 0.75); white = pbr("StationWhite", (0.78, 0.78, 0.74), 0.6)
    lit = emissive("StationWindow", (1.0, 0.82, 0.55), 0.8)
    box("StationWall", ((x0 + x1) / 2, y + 0.5, h / 2), (x1 - x0, 1.0, h), st)
    n = int((x1 - x0) / 4.0)
    for k in range(n):
        x = x0 + 2.0 + k * 4.0
        box("Pilaster", (x - 2.0, y - 0.1, h / 2), (0.5, 0.25, h), white)
        box("ArchWin", (x, y - 0.01, 4.0), (2.0, 0.02, 4.2), lit)
        cyl("ArchTop", (x, y - 0.01, 6.1), 1.0, 0.02, lit, verts=24, rot=(math.radians(90), 0, 0))
        box("ArchFrame", (x, y - 0.03, 4.0), (0.08, 0.02, 4.2), white)
        box("ArchTransom", (x, y - 0.03, 5.0), (2.0, 0.02, 0.08), white)
    box("Cornice", ((x0 + x1) / 2, y - 0.15, h - 0.3), (x1 - x0, 0.4, 0.4), white)
    # a clock in the pediment
    r, clk = ph.model("wall_clock", loc=((x0 + x1) / 2, y - 0.2, h + 1.5), rot_z=0.0, scale=6.0)
    box("Pediment", ((x0 + x1) / 2, y + 0.3, h + 1.5), (8.0, 0.6, 3.0), st)


def train_car(name, x, y, lit=True):
    green = pbr("TrainGreen", (0.08, 0.2, 0.12), 0.45, 0.2, **{'Coat Weight': 0.4})
    win = emissive("TrainWin", (1.0, 0.85, 0.6), 0.45 if lit else 0.05)
    parts = [box("TCar", (0, 0, 2.2), (24.0, 3.1, 3.4), green, bevel=0.2), box("TRoof", (0, 0, 3.95), (23.8, 2.9, 0.2), pbr("TRoofM", (0.2, 0.2, 0.2), 0.6), bevel=0.1)]
    for k in range(10):
        for sy in (-1, 1):
            parts.append(box("TWin", (-10.0 + k * 2.2, sy * 1.552, 2.6), (1.2, 0.01, 0.8), win))
    for sx in (-8.5, 8.5):
        for sy in (-1, 1):
            parts.append(cyl("TBogie", (sx, sy * 0.75, 0.5), 0.45, 0.2, pbr("Bogie", (0.05, 0.05, 0.05), 0.6), verts=20, rot=(math.radians(90), 0, 0)))
    o = joinm(parts, name); o.location = (x, y, 0.0)
    return o


def build(variant=None):
    variant = variant or "square"
    c = {"variant": variant}
    world_flat((0.015, 0.02, 0.035), 1.0)
    asph = wet_asphalt("StationWet")
    if variant == "square":
        box("Square", (0, 0, -0.02), (80, 60, 0.04), asph)
        arched_facade(-20, 20, 14.0, 12.0)
        for x in (-6.0, 6.0):
            ph.model("street_lamp_01", loc=(x, 2.0, 0))
            l = bpy.data.lights.new("SqLamp", 'SPOT'); l.energy = 400; l.spot_size = math.radians(90); l.spot_blend = 0.6; l.color = (1.0, 0.72, 0.42)
            o = bpy.data.objects.new("SqLamp", l); bpy.context.collection.objects.link(o); o.location = (x, 2.0, 3.8); point_at(o, (x, 2.0, 0))
        for k, x in enumerate((-12.0, -7.5, 9.0)):
            car = soviet_car(f"Taxi{k}", ((0.62, 0.55, 0.38), (0.15, 0.16, 0.18), (0.4, 0.42, 0.45))[k], kind="volga" if k != 1 else "lada")
            car.location = (x, 7.5, 0); car.rotation_euler = (0, 0, math.radians(90))
        fill = area_light((0, 12, 6), (math.radians(-60), 0, 0), 12, 400, (1.0, 0.8, 0.55)); fill.visible_camera = False
        c["rain"] = precip_curtains("rain", x_range=(-15, 15), ys=(-4, 0, 4, 8))
        c["a"] = person("Courier", 1.0, 45, "male_casualsuit05", "short02", cval=0.12, hv=0.3, sat=0.2)
        c["b"] = person("Buyer", 1.0, 38, "male_elegantsuit01", "short01", cval=0.1, hv=0.15, sat=0.2)
        c["parcel"] = joinm([box("Parcel", (0, 0, 0), (0.2, 0.13, 0.08), pbr("ParcelPaper", (0.5, 0.38, 0.24), 0.85), bevel=0.005),
                             box("String", (0, 0, 0.0), (0.205, 0.006, 0.083), pbr("StringM", (0.75, 0.7, 0.6), 0.8))], "Parcel")
    else:
        box("Platform", (0, 0, 0.5), (90, 6, 1.0), pbr("PlatformConcrete", (0.3, 0.3, 0.3), 0.6, 0.0, **{'Coat Weight': 0.6}))
        box("PlatformEdge", (0, -2.95, 1.01), (90, 0.3, 0.02), pbr("EdgeWhite", (0.7, 0.7, 0.65), 0.6))
        box("Trackbed", (0, -6, -0.05), (90, 6, 0.1), asph)
        for sy in (-6.7, -5.3):
            box("Rail", (0, sy, 0.12), (90, 0.08, 0.14), pbr("RailSteel", (0.4, 0.4, 0.42), 0.25, 1.0))
        for k in range(12):                                                      # canopy on columns
            x = -30 + k * 5.5
            cyl("CanopyCol", (x, 0.5, 3.0), 0.12, 4.0, pbr("ColGreen", (0.1, 0.2, 0.15), 0.5, 0.5), verts=16)
            l = bpy.data.lights.new("PlatLamp", 'POINT'); l.energy = 90; l.color = (1.0, 0.78, 0.5)
            o = bpy.data.objects.new("PlatLamp", l); bpy.context.collection.objects.link(o); o.location = (x, 0.5, 4.5)
        box("Canopy", (0, 0.5, 5.1), (70, 7.5, 0.25), pbr("CanopyRoof", (0.12, 0.15, 0.13), 0.6))
        c["train"] = [train_car(f"Car{k}", -4 + k * 24.6, -6.0) for k in range(4)]
        c["rain"] = precip_curtains("rain", x_range=(-25, 25), ys=(-9, -5), top=10)
        box("FarBuildings", (0, -30, 8), (120, 2, 16), masonry_facade("FarB", (0.4, 0.4, 0.38), 3.2, 2.6, 1.2, 1.6, 0.25, lit_strength=1.2))
        c["a"] = person("Courier", 1.0, 45, "male_casualsuit05", "short02", cval=0.12, hv=0.3, sat=0.2)
    animate(c, 0.0, variant)
    return c


def animate(c, sec, move):
    if c["variant"] == "square":
        a, b = c["a"], c["b"]
        stand(a, (-0.45, 1.6, 0), math.radians(90))                 # faces +X
        stand(b, (0.45, 1.6, 0), math.radians(-90))                 # faces -X
        k = ease(min(1.0, max(0.0, (sec - 1.2) / 2.2)))
        mid = Vector((0.0, 1.55, 1.05))
        p = (a.bone_head("spine03") + fwd(a) * 0.3 + Vector((0, 0, -0.25))).lerp(mid, min(1.0, k * 1.6))
        if k > 0.62:
            p = mid.lerp(b.bone_head("spine03") + fwd(b) * 0.25 + Vector((0, 0, -0.2)), (k - 0.62) / 0.38)
        c["parcel"].location = p; c["parcel"].rotation_euler = (0, 0, 0.3)
        hand_to(a, "R", p + Vector((-0.05, 0.05, 0.04)) if k < 0.8 else a.bone_head("spine02") + fwd(a) * 0.15 + Vector((0, -0.1, -0.15)), curl=50)
        if k > 0.45:
            hand_to(b, "L", p + Vector((0.05, 0.05, 0.04)), curl=50)
        look(a, b.bone_head("head")); look(b, a.bone_head("head"))
        nod(a, "head", 8); nod(b, "head", 10)
        # one glances over his shoulder
        a.rot("head", (0, 0, 1), -25 * max(0.0, math.sin(min(1.0, max(0.0, (sec - 4.2) / 1.6)) * math.pi)))
    else:
        for k, car in enumerate(c["train"]):
            v = 0.0 if sec < 0.8 else 0.6 * (sec - 0.8) ** 1.6
            car.location.x = -4 + k * 24.6 + v
        a = c["a"]
        stand(a, (-2.0, -1.4, 1.0), 0.0)                             # on the platform, facing the train (-Y)
        nod(a, "head", 6); look(a, Vector((10.0, -6.0, 2.0)), 0.5 * min(1.0, sec / 4.0))
    bpy.context.view_layer.update()


def _push(a, b, ta, tb, lens):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(ta).lerp(Vector(tb), ease(t)), lens)


MOVES = {
    "handover": dict(kind="anim", dof=2.8, far=40.0, anim=lambda c, t: animate(c, t * DUR["handover"], "handover"),
                     cam=_push((-2.4, -2.6, 1.55), (-2.0, -2.2, 1.5), (0.0, 1.6, 1.25), (0.0, 1.6, 1.2), 35),
                     focus=lambda c, t: Vector((0.0, 1.6, 1.2))),
    "platform": dict(kind="anim", dof=4.0, far=60.0, anim=lambda c, t: animate(c, t * DUR["platform"], "platform"),
                     cam=_push((-9.0, 1.8, 2.4), (-8.0, 1.6, 2.35), (-2.0, -2.0, 1.8), (-1.6, -2.2, 1.8), 30),
                     focus=lambda c, t: Vector((-2.0, -1.4, 2.0))),
}
