"""CH2: Denver police station interview room, 1942. A single hanging lamp over a scarred table; a typewriter.
  interview (A): the captain studies the thin man while a detective types.
  photo     (B): the captain holds an old file photo up beside the man's face, then lowers it.
  talk      (C): the man talks quietly, head down, as the captain leans in.
"""
import math
import bpy
from mathutils import Vector
from kit import *
import house as H
from house import reset_pose
import ph
from human import pose_sit, reach, fingers_curl

DUR = {"interview": 5.0, "photo": 4.5, "talk": 5.0}
VARIANT_FOR = {k: k for k in DUR}


def build(variant=None):
    c = {}
    world_flat((0.005, 0.006, 0.008), 1.0)
    bpy.context.scene.view_settings.exposure = 0.9
    wall = pbr("StationGreen", (0.28, 0.33, 0.28), 0.8); low = pbr("StationDado", (0.16, 0.18, 0.15), 0.6)
    box("Floor", (0, 0, -0.02), (6, 6, 0.04), H.mat("lino"))
    for (x, y, sx, sy) in ((0, 3, 6, 0.2), (0, -3, 6, 0.2), (3, 0, 0.2, 6), (-3, 0, 0.2, 6)):
        box("Wall", (x, y, 1.5), (sx, sy, 3.0), wall)
    box("Dado", (0, 2.88, 0.55), (6, 0.04, 1.1), low); box("Dado", (-2.88, 0, 0.55), (0.04, 6, 1.1), low)
    box("Ceil", (0, 0, 3.0), (6, 6, 0.1), pbr("StCeil", (0.5, 0.5, 0.48), 0.8))
    box("Table", (0, 0, 0.74), (1.6, 0.9, 0.05), H.mat("oak"))
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("TLeg", (sx * 0.72, sy * 0.38, 0.36), (0.06, 0.06, 0.72), H.mat("oak"))
    shade = cyl("Shade", (0, 0, 2.1), 0.28, 0.12, pbr("ShadeMetal", (0.12, 0.14, 0.12), 0.4, 0.8), 32)
    cyl("Cord", (0, 0, 2.55), 0.006, 0.9, H.mat("black"), 8)
    c["lamp"] = H.point((0, 0, 1.98), 90, (1.0, 0.82, 0.6), 0.06)
    c["haze"] = haze((0, 0, 1.5), (5.8, 5.8, 3.0), density=0.012, color=(0.9, 0.9, 0.85), anis=0.5)
    # typewriter on a side desk
    box("Desk", (2.0, 1.6, 0.74), (1.1, 0.6, 0.05), H.mat("oak")); box("DeskBody", (2.0, 1.6, 0.37), (1.1, 0.6, 0.72), H.mat("oak"))
    c["typer"] = join([box("TW", (0, 0, 0.08), (0.42, 0.34, 0.14), H.mat("black"), bevel=0.02), cyl("Platen", (0, 0.12, 0.17), 0.03, 0.44, H.mat("black"), 16, rot=(0, math.radians(90), 0)),
                       box("Paper", (0, 0.15, 0.27), (0.22, 0.01, 0.2), pbr("Paper", (0.9, 0.88, 0.82), 0.8))], "Typewriter")
    c["typer"].location = (2.0, 1.6, 0.77)
    H.point((2.0, 1.4, 1.6), 8, (1.0, 0.8, 0.6), 0.2)
    c["file"] = box("FilePhoto", (0, 0, -20), (0.13, 0.005, 0.18), pbr("Photo", (0.55, 0.53, 0.5), 0.4))
    ph.model("dining_chair_02", loc=(0, -0.75, 0), rot_z=math.pi)
    ph.model("dining_chair_02", loc=(0, 0.75, 0), rot_z=0.0)
    ph.model("dining_chair_02", loc=(2.0, 2.2, 0), rot_z=0.0)
    c["thin"] = H.person("Thin", "thin"); c["cap"] = H.person("Captain", "captain")
    if variant == "interview":
        c["typist"] = H.person("Typist", "detective2")
    return c


def seat(h, loc, rz, lean=8):
    reset_pose(h); pose_sit(h, lean=lean)
    h.arm.rotation_euler = (0, 0, rz); h.arm.location = loc; bpy.context.view_layer.update(); H.ground_to(h, 0.0)


def anim_common(c, sec, lean_in=0.0):
    seat(c["thin"], Vector((0, -0.75, 0)), math.pi, lean=24)
    H.rotl(c["thin"], "head", (1, 0, 0), 28)
    seat(c["cap"], Vector((0, 0.75, 0)), 0.0, lean=10 + 20 * lean_in)
    for sd in ("L", "R"):
        reach(c["thin"], sd, Vector((0.12 * (1 if sd == "L" else -1), -0.3, 0.8)), Vector((0, 0, -1)), Vector((0, 1, 0)))


def anim_interview(c, t):
    sec = t * DUR["interview"]
    anim_common(c, sec)
    reach(c["cap"], "R", Vector((-0.2, 0.3, 0.79)), Vector((0, 0, -1)), Vector((0, -1, 0)))
    H.look(c["cap"], 4 * math.sin(sec), 8)
    ty = c["typist"]; seat(ty, Vector((2.0, 2.2, 0)), 0.0, lean=14)
    for sd, ph_ in (("L", 0.0), ("R", 1.7)):
        tap = 0.025 * max(0.0, math.sin(2 * math.pi * 3.2 * sec + ph_))
        reach(ty, sd, Vector((2.0 + (0.1 if sd == "L" else -0.1), 1.62, 0.9 - tap)), Vector((0, 0, -1)), Vector((0, -1, -0.5)))
    H.look(ty, 0, 20)


def anim_photo(c, t):
    sec = t * DUR["photo"]
    anim_common(c, sec)
    up = ease(min(1.0, sec / 1.2)) * (1 - ease(min(1.0, max(0.0, (sec - 3.0) / 1.0))))
    hd = c["thin"].bone_head("head")
    p = Vector((0.15, 0.2, 0.8)).lerp(hd + Vector((0.28, 0.12, 0.0)), up)
    c["file"].location = p; c["file"].rotation_euler = (0, 0, 0)
    reach(c["cap"], "R", p + Vector((0.0, 0.05, -0.08)), Vector((0, 0, -1)), Vector((0, -1, 0.5)))
    H.look(c["cap"], 0, 6)


def anim_talk(c, t):
    sec = t * DUR["talk"]
    lean = ease(min(1.0, sec / 3.0))
    anim_common(c, sec, lean)
    H.rotl(c["thin"], "jaw", (1, 0, 0), 4 * max(0.0, math.sin(9 * sec))) if "jaw" in c["thin"].arm.pose.bones else None
    reach(c["cap"], "R", Vector((-0.2, 0.25, 0.79)), Vector((0, 0, -1)), Vector((0, -1, 0)))
    reach(c["cap"], "L", Vector((0.2, 0.25, 0.79)), Vector((0, 0, -1)), Vector((0, -1, 0)))
    H.look(c["cap"], 0, 14)


MOVES = {
    "interview": dict(kind="anim", dof=None, far=20, anim=anim_interview,
                      cam=lambda c, t: (Vector((-2.2, -1.6, 1.6)).lerp(Vector((-1.9, -1.2, 1.55)), ease(t)), Vector((0.4, 0.5, 1.0)), 28)),
    "photo": dict(kind="anim", dof=2.8, far=20, anim=anim_photo,
                  cam=lambda c, t: (Vector((-2.4, 2.2, 1.6)).lerp(Vector((-2.1, 1.9, 1.55)), ease(t)), Vector((0.05, -0.4, 1.1)), 30),
                  focus=lambda c, t: Vector((0.1, -0.7, 1.2))),
    "talk": dict(kind="anim", dof=2.8, far=20, anim=anim_talk,
                 cam=lambda c, t: (Vector((1.8, -1.4, 1.35)).lerp(Vector((1.5, -1.1, 1.3)), ease(t)), Vector((0.0, -0.4, 1.05)), 38),
                 focus=lambda c, t: Vector((0.0, -0.75, 1.15))),
}
