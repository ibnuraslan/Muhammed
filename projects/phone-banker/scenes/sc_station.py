"""RAILWAY PLATFORM, Moscow, night rain (dramatization; a generic suburban-line platform, not a likeness).
  handover : under a sodium lamp on the wet platform, beside a waiting train, a small parcel changes hands (Ch2 6A)
  platform : one of them stands alone as the train pulls out (Ch2 6B)
The train is a placeholder electric train (lit interiors behind real glass) until the shared vehicle kit's elektrichka lands."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph
from pbkit import joinm, masonry_facade, precip_curtains, ph_instances
from pbpeople import person, stand, walk_at, nod, look, hand_to, hide, fwd
from sc_street import wet_asphalt

EXPOSURE = 1.0
BOUNCES = 6
DUR = {"handover": 6.0, "platform": 6.5}
VARIANT_FOR = {"handover": None, "platform": None}
TRACK_Y = -4.6
rng = np.random.default_rng(41)


def train_car(name, x, y, front=False):
    """A green suburban electric-train car: rounded body, red band, real glass windows with a lit interior
    (seat rows, a warm ceiling light) visible through them."""
    green = pbr("TrainGreen", (0.12, 0.26, 0.16), 0.4, 0.25, **{'Coat Weight': 0.5, 'Coat Roughness': 0.15})
    red = pbr("TrainRed", (0.45, 0.06, 0.04), 0.4, 0.2, **{'Coat Weight': 0.5})
    gl = glass("TrainGlass", (0.85, 0.9, 0.88), 0.03)
    L_, W_, H_ = 19.5, 3.4, 3.3
    parts = [box("TLower", (0, 0, 1.05), (L_, W_, 1.1), green, bevel=0.12),
             box("TBand", (0, 0, 1.0), (L_ + 0.01, W_ + 0.01, 0.16), red),
             box("TUpper", (0, 0, 3.05), (L_, W_, 1.0), green, bevel=0.25),
             box("TRoof", (0, 0, 3.6), (L_ - 0.3, W_ - 0.4, 0.2), pbr("TRoofGrey", (0.3, 0.3, 0.3), 0.6), bevel=0.15),
             box("TFloor", (0, 0, 1.62), (L_ - 0.2, W_ - 0.2, 0.05), pbr("TFloorM", (0.25, 0.22, 0.18), 0.8))]
    for k in range(9):                                          # window piers between the glass
        for sy in (-1, 1):
            parts.append(box("TPier", (-L_ / 2 + 0.6 + k * 2.3, sy * (W_ / 2 - 0.03), 2.05), (0.5, 0.06, 0.9), green))
    for sy in (-1, 1):
        parts.append(box("TDoor", (-L_ / 2 + 1.2, sy * (W_ / 2 + 0.005), 1.9), (1.3, 0.02, 2.1), pbr("DoorGrey", (0.35, 0.37, 0.35), 0.5)))
    seat = pbr("SeatWood", (0.42, 0.25, 0.12), 0.5)
    for k in range(14):                                         # bench seats inside
        for sy in (-1, 1):
            parts.append(box("TSeat", (-L_ / 2 + 2.5 + k * 1.15, sy * 1.05, 1.95), (0.5, 0.95, 0.12), seat))
            parts.append(box("TBack", (-L_ / 2 + 2.25 + k * 1.15, sy * 1.05, 2.3), (0.08, 0.95, 0.6), seat))
    body = joinm(parts, name)
    for sy in (-1, 1):
        g = box("TGlass", (0, sy * (W_ / 2 - 0.02), 2.05), (L_ - 0.4, 0.01, 0.9), gl); g.parent = body
    for k in range(4):                                          # warm ceiling lights inside
        l = bpy.data.lights.new("TrainInt", 'AREA'); l.energy = 40; l.size = 1.2; l.color = (1.0, 0.86, 0.62)
        o = bpy.data.objects.new("TrainInt", l); bpy.context.collection.objects.link(o); o.parent = body; o.location = (-7.5 + k * 5.0, 0, 3.0)
    if front:
        cab = joinm([box("Cab", (L_ / 2 + 0.6, 0, 2.1), (1.4, W_, 2.9), red, bevel=0.5),
                     box("CabWin", (L_ / 2 + 1.25, 0, 2.6), (0.05, 2.6, 0.8), gl)], name + "Cab")
        cab.parent = body
        for sy in (-0.9, 0.9):
            h = cyl("Headlamp", (L_ / 2 + 1.31, sy, 1.4), 0.12, 0.04, emissive("TrainHead", (1.0, 0.92, 0.8), 8), verts=20, rot=(0, math.radians(90), 0)); h.parent = body
    body.location = (x, y, 0.15)
    return body


def build(variant=None):
    c = {}
    world_flat((0.012, 0.016, 0.03), 1.0)
    asph = wet_asphalt("PlatformWet")
    box("Platform", (0, 0, 0.55), (110, 6, 1.1), asph)
    box("PlatformEdge", (0, -2.92, 1.11), (110, 0.25, 0.02), pbr("EdgeYellow", (0.55, 0.45, 0.1), 0.6))
    box("Trackbed", (0, TRACK_Y - 1, -0.05), (110, 8, 0.1), ph.texture("gravel_floor", scale=0.5))
    for sy in (TRACK_Y - 0.75, TRACK_Y + 0.75):
        box("Rail", (0, sy, 0.12), (110, 0.08, 0.14), pbr("RailSteel", (0.5, 0.5, 0.52), 0.2, 1.0))
    for k in range(70):
        box("Sleeper", (-55 + k * 1.6, TRACK_Y, 0.05), (0.25, 2.6, 0.1), pbr("Sleeper", (0.12, 0.1, 0.08), 0.8))
    # sodium lamps on posts along the platform; a short canopy over the stairs
    for k in range(8):
        x = -28 + k * 9.0
        cyl("LampPost", (x, 1.6, 3.3), 0.07, 4.4, pbr("PostDark", (0.08, 0.1, 0.09), 0.5, 0.6), verts=12)
        box("LampArm", (x, 1.1, 5.45), (0.1, 1.1, 0.08), pbr("PostDark2", (0.08, 0.1, 0.09), 0.5, 0.6))
        box("LampHead", (x, 0.55, 5.4), (0.35, 0.25, 0.12), pbr("LampHousing", (0.1, 0.1, 0.1), 0.5))
        l = bpy.data.lights.new("Sodium", 'SPOT'); l.energy = 650; l.spot_size = math.radians(100); l.spot_blend = 0.7; l.color = (1.0, 0.62, 0.28)
        o = bpy.data.objects.new("Sodium", l); bpy.context.collection.objects.link(o); o.location = (x, 0.55, 5.3); point_at(o, (x, 0.0, 1.1))
    box("Canopy", (22, 1.2, 4.2), (14, 3.5, 0.2), pbr("CanopyRoof", (0.15, 0.17, 0.16), 0.6))
    for x in (16, 28):
        cyl("CanopyCol", (x, 2.4, 2.65), 0.1, 3.1, pbr("ColGreen", (0.12, 0.22, 0.16), 0.5, 0.4), verts=16)
    ph_instances("painted_wooden_bench", [((x, 2.2, 1.1), math.pi, 1.0) for x in (5.5, 18.0)])
    box("FarBuildings", (0, -40, 9), (160, 2, 18), masonry_facade("FarB", (0.4, 0.4, 0.38), 3.2, 2.6, 1.2, 1.5, 0.22, lit_strength=0.8))
    c["train"] = [train_car(f"Car{k}", -6 + k * 20.2, TRACK_Y, front=(k == 0)) for k in range(4)]
    c["rain"] = precip_curtains("rain", x_range=(-30, 30), ys=(-7, -3, 0.5, 3.5), top=10)
    c["a"] = person("Courier", 1.0, 45, "male_casualsuit05", "short02", hv=0.3, col=(0.22, 0.2, 0.17))
    c["b"] = person("Buyer", 1.0, 38, "male_elegantsuit01", "short01", hv=0.15, col=(0.28, 0.3, 0.33))
    c["parcel"] = joinm([box("Parcel", (0, 0, 0), (0.2, 0.13, 0.08), pbr("ParcelPaper", (0.5, 0.38, 0.24), 0.85), bevel=0.005),
                         box("String", (0, 0, 0.0), (0.205, 0.006, 0.083), pbr("StringM", (0.75, 0.7, 0.6), 0.8))], "Parcel")
    animate(c, 0.0, "handover")
    return c


def animate(c, sec, move):
    a, b = c["a"], c["b"]
    Z = 1.1
    if move == "handover":
        for k, car in enumerate(c["train"]):
            car.location.x = -6 + k * 20.2
        stand(a, (-0.4, -0.6, Z), math.radians(90))                       # face each other along the platform
        stand(b, (0.4, -0.6, Z), math.radians(-90))
        k = ease(min(1.0, max(0.0, (sec - 1.2) / 2.2)))
        mid = Vector((0.0, -0.62, Z + 1.0))
        pa = a.bone_head("spine03") + fwd(a) * 0.28 + Vector((0, 0, -0.25))
        pb = b.bone_head("spine03") + fwd(b) * 0.25 + Vector((0, 0, -0.2))
        p = pa.lerp(mid, min(1.0, k * 1.6)) if k < 0.62 else mid.lerp(pb, (k - 0.62) / 0.38)
        c["parcel"].location = p; c["parcel"].rotation_euler = (0, 0, 0.3)
        if k < 0.8:
            hand_to(a, "R", p + Vector((-0.06, 0.03, 0.03)), curl=50)
        if k > 0.45:
            hand_to(b, "L", p + Vector((0.06, 0.03, 0.03)), curl=50)
        look(a, b.bone_head("head")); look(b, a.bone_head("head")); nod(a, "head", 8); nod(b, "head", 10)
        a.rot("head", (0, 0, 1), -25 * max(0.0, math.sin(min(1.0, max(0.0, (sec - 4.2) / 1.6)) * math.pi)))      # a glance along the platform
    else:
        hide(b, True); c["parcel"].hide_render = True
        for k, car in enumerate(c["train"]):
            car.location.x = -6 + k * 20.2 + (0.0 if sec < 0.8 else 0.55 * (sec - 0.8) ** 1.7)
        stand(a, (-2.0, -1.2, Z), 0.0)                                    # facing the train (-Y)
        nod(a, "head", 6); look(a, Vector((14.0, TRACK_Y, 2.0)), 0.5 * min(1.0, sec / 4.0))
    bpy.context.view_layer.update()


def _push(a, b, ta, tb, lens):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(ta).lerp(Vector(tb), ease(t)), lens)


MOVES = {
    "handover": dict(kind="anim", dof=2.8, far=40.0, anim=lambda c, t: animate(c, t * DUR["handover"], "handover"),
                     cam=_push((-2.6, 2.3, 2.55), (-2.2, 2.0, 2.5), (0.0, -0.6, 2.05), (0.0, -0.7, 2.0), 35),
                     focus=lambda c, t: Vector((0.0, -0.6, 2.1))),
    "platform": dict(kind="anim", dof=4.0, far=60.0, anim=lambda c, t: animate(c, t * DUR["platform"], "platform"),
                     cam=_push((-9.0, 2.2, 2.9), (-8.0, 2.0, 2.85), (-2.0, -2.5, 2.4), (-1.6, -2.7, 2.4), 30),
                     focus=lambda c, t: Vector((-2.0, -1.2, 2.5))),
}


_build_set = build


def build(variant=None):
    c = _build_set(variant)
    from pbkit import finish_scene
    finish_scene()
    return c
