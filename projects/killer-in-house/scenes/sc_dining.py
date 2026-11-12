"""CH1: the neighbours' dining room, autumn 1941 evening. Warm lamp over a set table, wallpaper, a wall clock.
  dinner      (4A): the family at dinner; Philip is passed a dish; camera tracks along the table.
  plate       (4B): at the door, the neighbour hands Philip a plate wrapped in a cloth as he buttons his coat.
  empty_chair (5A): his place set, his chair empty; the family glance at the clock; slow push.
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import house as H
from house import reset_pose
import ph
from human import pose_sit, reach, fingers_curl

DUR = {"dinner": 5.0, "plate": 4.5, "empty_chair": 5.0}
VARIANT_FOR = {"dinner": "dinner", "plate": "plate", "empty_chair": "empty"}
SEATS = [(-0.75, -0.95, math.pi), (0.75, -0.95, math.pi), (-0.75, 0.95, 0.0), (0.75, 0.95, 0.0), (-1.55, 0.0, math.pi / 2)]


def seat_off(x, y):
    return Vector((-0.2 if not y else 0.0, math.copysign(0.25, y) if y else 0.0, 0.0))


def build(variant=None):
    c = {"variant": variant}
    world_flat((0.01, 0.015, 0.03), 1.0)
    bpy.context.scene.view_settings.exposure = 1.1
    paper = H.mat("paper"); fl = H.mat("floor"); tr = H.mat("trim")
    box("Floor", (0, 0, -0.02), (7, 6, 0.04), fl)
    box("Ceil", (0, 0, 2.75), (7, 6, 0.1), H.mat("plaster"))
    H.wall_x("WallN", -3.5, 3.5, 3.0, 0, 2.7, 0.15, paper, [(-1.0, 0.2, 0.9, 2.2)])
    p, g = H.window_unit('x', -0.4, 1.2, 3.0, 0.9, 2.2)
    H.wall_x("WallS", -3.5, 3.5, -3.0, 0, 2.7, 0.15, paper, [(1.6, 2.5, 0.0, 2.1)])
    H.wall_y("WallW", -3, 3, -3.5, 0, 2.7, 0.15, paper)
    H.wall_y("WallE", -3, 3, 3.5, 0, 2.7, 0.15, paper)
    box("Wainscot", (-3.42, 0, 0.45), (0.02, 6, 0.9), H.mat("oak"))
    box("Wainscot", (0, 2.92, 0.45), (7, 0.02, 0.9), H.mat("oak"))
    c["door"] = H.hinge_door("DDoor", (1.62, -3.0, 0.0), 0.86, 2.08, 0.04, H.mat("door"))
    t, _ = ph.model("dining_table", loc=(0, 0, 0), scale=0.85)
    for (x, y, rz) in SEATS:
        o = seat_off(x, y); ph.model("dining_chair_02", loc=(x + o.x, y + o.y, 0), rot_z=rz)
    ph.model("vintage_cabinet_01", loc=(3.25, 0.0, 0), rot_z=math.radians(90), scale=0.75)
    ph.model("Chandelier_01", loc=(0, 0, 2.7), scale=0.8) if False else None
    shade = join([cyl("LampShade", (0, 0, 2.0), 0.35, 0.22, pbr("Shade", (0.85, 0.66, 0.4), 0.8, 0.0, **{'Emission Color': (1.0, 0.7, 0.4, 1), 'Emission Strength': 1.5}), 32),
                  cyl("LampCord", (0, 0, 2.4), 0.005, 0.7, H.mat("black"), 8)], "Lamp")
    c["lamp"] = H.point((0, 0, 1.85), 120, (1.0, 0.68, 0.38), 0.1)
    H.point((2.0, -2.0, 2.0), 15, (1.0, 0.7, 0.42), 0.2)
    wc, ms = ph.model("wall_clock", loc=(-3.38, 0.0, 1.95), rot_z=math.radians(90)); c["clock"] = ms
    # dishes on the table
    plate = H.mat("enamel")
    c["plates"] = []
    for (x, y, rz) in SEATS:
        px, py = x * 0.75, y * 0.6 if y else 0
        if not y:
            px = -1.0
        c["plates"].append(cyl("Plate", (px, py, 0.765), 0.12, 0.015, plate, 32))
    c["dish"] = cyl("Dish", (0.0, 0.0, 0.78), 0.16, 0.06, pbr("Dish", (0.8, 0.78, 0.7), 0.25), 32)
    cyl("Roast", (0.0, 0.0, 0.83), 0.1, 0.06, pbr("Roast", (0.28, 0.12, 0.05), 0.6), 24)
    for k in range(3):
        cyl("Glass", (-0.3 + 0.3 * k, 0.15, 0.82), 0.035, 0.11, H.mat("glass"), 16)
    # the family
    cast = {"m": "neighbour_m", "w": "neighbour_w", "p": "philip"}
    if variant == "empty":
        cast = {"m": "neighbour_m", "w": "neighbour_w"}
    if variant == "plate":
        cast = {"w": "neighbour_w", "p": "philip"}
    c["cast"] = {k: H.person(v.capitalize() + k, v) for k, v in cast.items()}
    c["wrapped"] = box("WrappedPlate", (0, 0, -20), (0.3, 0.3, 0.07), fabric("Cloth", (0.82, 0.8, 0.72), 0.9, 0.4, 500), bevel=0.04)
    import look                   # neighbours' dining room at dusk: lamplit, keep the practicals, darker walls
    look.night_interior()
    return c


def seat(h, idx):
    x, y, rz = SEATS[idx]
    reset_pose(h); pose_sit(h, lean=8)
    off = seat_off(x, y)
    h.arm.rotation_euler = (0, 0, rz); h.arm.location = Vector((x, y, 0)) + off; bpy.context.view_layer.update(); H.ground_to(h, 0.0)


def tick(c, sec):
    for o in c["clock"]:
        if "second" in o.name:
            o.rotation_euler.y = -sec * math.radians(6)


def anim_dinner(c, t):
    sec = t * DUR["dinner"]; tick(c, sec)
    m, w, p = c["cast"]["m"], c["cast"]["w"], c["cast"]["p"]
    seat(m, 4); seat(w, 2); seat(p, 1)
    u = ease(min(1.0, max(0.0, (sec - 0.8) / 2.0)))
    dish = Vector((0.0, 0.0, 0.78)).lerp(Vector((0.45, -0.45, 0.85)), u)
    c["dish"].location = dish
    reach(w, "R", dish + Vector((-0.12, 0.05, 0.03)), Vector((0, 0, -1)), Vector((0, -1, 0)))
    if u > 0.6:
        reach(p, "L", dish + Vector((0.1, -0.08, 0.03)), Vector((0, 0, -1)), Vector((0, 1, 0)))
    H.look(m, 20 * math.sin(0.6 * sec), 10); H.look(p, -10, 14); H.look(w, 8, 10)
    fingers_curl(m, 30)


def anim_plate(c, t):
    sec = t * DUR["plate"]; tick(c, sec)
    w, p = c["cast"]["w"], c["cast"]["p"]
    c["door"].rotation_euler = (0, 0, math.radians(-70))
    H.stand_at(w, (1.6, -1.6, 0), math.radians(160))
    H.stand_at(p, (2.1, -2.4, 0), math.radians(-20))
    u = ease(min(1.0, max(0.0, (sec - 0.6) / 1.8)))
    pl = w.bone_head("spine05") + Vector((0.15, -0.35, -0.2))
    pl = pl.lerp(p.bone_head("spine05") + Vector((-0.1, 0.35, -0.25)), u)
    c["wrapped"].location = pl
    reach(w, "R", pl + Vector((-0.12, 0, 0.0)), Vector((0, 0, -1)), Vector((0, -1, 0))); reach(w, "L", pl + Vector((0.12, 0, 0.0)), Vector((0, 0, -1)), Vector((0, -1, 0)))
    if u > 0.5:
        reach(p, "R", pl + Vector((0.1, 0.0, -0.03)), Vector((0, 0, -1)), Vector((0, 1, 0))); reach(p, "L", pl + Vector((-0.12, 0, -0.03)), Vector((0, 0, -1)), Vector((0, 1, 0)))
    H.look(p, 0, 12); H.look(w, 0, 10)


def anim_empty(c, t):
    sec = t * DUR["empty_chair"]; tick(c, sec)
    m, w = c["cast"]["m"], c["cast"]["w"]
    seat(m, 4); seat(w, 2)
    g = ease(min(1.0, max(0.0, (sec - 1.5) / 1.0)))
    H.look(m, -45 * g, -5 * g); H.look(w, -60 * g, 0)


MOVES = {
    "dinner": dict(kind="anim", dof=None, far=20, anim=anim_dinner,
                   cam=lambda c, t: (Vector((2.6, -2.4, 1.55)).lerp(Vector((2.6, 0.4, 1.55)), ease(t)), Vector((0.0, -0.4, 0.9)).lerp(Vector((-0.2, 0.3, 0.9)), ease(t)), 30)),
    "plate": dict(kind="anim", dof=None, far=20, anim=anim_plate,
                  cam=lambda c, t: (Vector((-1.4, 0.4, 1.6)).lerp(Vector((-1.0, 0.1, 1.6)), ease(t)), Vector((1.9, -2.1, 1.1)), 28)),
    "empty_chair": dict(kind="anim", dof=None, far=20, anim=anim_empty,
                        cam=lambda c, t: (Vector((1.4, -2.6, 1.3)).lerp(Vector((1.0, -1.9, 1.2)), ease(t)), Vector((0.75, -1.1, 0.7)), 32)),
}
