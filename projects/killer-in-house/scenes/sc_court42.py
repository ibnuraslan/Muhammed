"""CH3: Denver courtroom, 1942. Dark oak panelling, a raised bench, the witness chair beside it, a jury box of
twelve, tall windows with warm afternoon light.
  prosecutor (A): the prosecutor in a double-breasted suit addresses the jury box; slow track.
  stand      (B): the thin defendant in the witness chair, speaking; the judge above him; slow push.
  jury_in    (C): the jury files back in; the foreman stands with a slip of paper.
  gavel      (D): slow push on the defendant at the defence table as the gavel comes down behind, out of focus.
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

DUR = {"prosecutor": 5.0, "stand": 5.0, "jury_in": 5.0, "gavel": 5.0}
VARIANT_FOR = {k: k for k in DUR}
JURY = [(x, y) for y in (1.2, 2.1) for x in (-5.2, -4.6, -4.0, -3.4, -2.8, -2.2)]


def build(variant=None):
    c = {"variant": variant}
    world_sky(sun_elev_deg=24, sun_rot_deg=100, strength=0.4, tint=(1.0, 0.95, 0.88))
    sun(24, 30, energy=2.6, color=(1.0, 0.86, 0.66), angle_deg=1.2)
    bpy.context.scene.view_settings.exposure = -0.1
    oak = H.mat("oak"); dark = wood("CDark", (0.06, 0.035, 0.02), (0.14, 0.08, 0.04), scale=(0.3, 6, 6), rough=0.35, coat=0.4)
    pl = pbr("CPlaster", (0.62, 0.58, 0.5), 0.85)
    box("Floor", (0, 2, -0.02), (14, 18, 0.04), H.mat("floor"))
    box("WallBack", (0, 9.5, 3.5), (14, 0.2, 7), dark)
    box("WallL", (-7, 2, 3.5), (0.2, 18, 7), pl); box("PanelL", (-6.88, 2, 1.1), (0.04, 18, 2.2), dark)
    box("Ceil", (0, 2, 7), (14, 18, 0.2), pbr("CCeil", (0.6, 0.57, 0.52), 0.85))
    H.wall_y("WinWall", -7, 11, 7, 0, 7, 0.25, pl, [(y - 0.7, y + 0.7, 1.4, 5.6) for y in (-3, 0.5, 4, 7.5)])
    for y in (-3, 0.5, 4, 7.5):
        H.window_unit('y', y, 1.4, 7.0, 1.4, 5.6)
    c["haze"] = haze((0, 2, 3.5), (13.6, 18, 7), density=0.008, color=(1.0, 0.95, 0.85), anis=0.6)
    for x in (-3, 0, 3):
        H.point((x, 3, 6.2), 60, (1.0, 0.85, 0.65), 0.3)
    box("Bench", (0, 7.6, 0.95), (4.4, 1.2, 1.9), dark, bevel=0.02); box("BenchTop", (0, 7.6, 1.92), (4.6, 1.3, 0.05), oak)
    box("Dais", (0, 8.0, 0.25), (5.5, 2.4, 0.5), oak)
    box("JudgeChair", (0, 8.5, 1.6), (0.8, 0.6, 1.9), pbr("Leather", (0.05, 0.03, 0.02), 0.45), bevel=0.06)
    box("WitnessBox", (3.2, 6.8, 0.55), (1.4, 1.3, 1.1), dark, bevel=0.02)
    box("WitnessRail", (3.2, 6.15, 1.12), (1.4, 0.06, 0.06), oak)
    box("JuryBox", (-3.7, 1.65, 0.45), (4.4, 2.3, 0.9), dark, bevel=0.02)
    box("JuryRail", (-3.7, 0.45, 0.95), (4.4, 0.08, 0.08), oak)
    box("JuryStep", (-3.7, 2.1, 0.12), (4.4, 1.0, 0.24), oak)
    for (x, y) in JURY:
        ph.model("dining_chair_02", loc=(x, y, 0.24 if y > 2 else 0), rot_z=math.radians(-90))
    for x in (-1.6, 1.8):
        box("Counsel", (x, 3.0, 0.76), (2.2, 0.9, 0.05), oak)
        for sx in (-1, 1):
            box("CLeg", (x + sx * 1.0, 3.0, 0.38), (0.06, 0.8, 0.74), dark)
    box("Bar", (0, 0.0, 0.5), (8, 0.1, 1.0), dark)
    for k in range(4):
        for x in (-2.6, 2.6):
            box("Pew", (x, -1.2 - k * 1.2, 0.45), (4.2, 0.45, 0.9), oak, bevel=0.03)
    c["gavel"] = join([cyl("GavelHead", (0, 0, 0), 0.035, 0.12, dark, 24, rot=(0, math.radians(90), 0)),
                       cyl("GavelHandle", (0, -0.13, 0), 0.012, 0.25, dark, 12, rot=(math.radians(90), 0, 0))], "Gavel")
    c["slip"] = box("Slip", (0, 0, -20), (0.1, 0.004, 0.14), pbr("SlipPaper", (0.9, 0.88, 0.82), 0.8))
    # cast per variant
    kinds = {"prosecutor": {"pr": "detective2", "j1": "neighbour_m", "j2": "neighbour_w", "j3": "captain", "j4": "friend", "j5": "son", "j6": "neighbour_m"},
             "stand": {"def": "thin_court", "judge": "captain"},
             "jury_in": {"j1": "neighbour_m", "j2": "neighbour_w", "j3": "captain", "j4": "friend", "j5": "son"},
             "gavel": {"def": "thin_court", "judge": "captain", "law": "detective2"}}[variant]
    c["cast"] = {k: H.person(v.capitalize() + k, v) for k, v in kinds.items()}
    return c


def seat(h, loc, rz, lean=8, floor=0.0):
    reset_pose(h); pose_sit(h, lean=lean)
    h.arm.rotation_euler = (0, 0, rz); h.arm.location = loc; bpy.context.view_layer.update(); H.ground_to(h, floor)


def judge(c, sec):
    j = c["cast"]["judge"]; seat(j, Vector((0, 8.5, 0.5)), 0.0, 12, floor=0.5)
    H.look(j, 0, 15)


def anim_prosecutor(c, t):
    sec = t * DUR["prosecutor"]
    for k, key in enumerate(("j1", "j2", "j3", "j4", "j5", "j6")):
        x, y = JURY[k + 6 if k % 2 else k]
        seat(c["cast"][key], Vector((x, y, 0)), math.radians(-90), 6, floor=0.24 if y > 2 else 0.0)
        H.look(c["cast"][key], 10, 0)
    pr = c["cast"]["pr"]
    H.walk_to(pr, (-0.6, 0.6, 0), (-0.9, 0.9, 0), 0.5 + 0.3 * math.sin(0.5 * sec), swing=4, face=math.radians(90))
    reach(pr, "R", pr.bone_head("head") + Vector((-0.45, 0.15 * math.sin(1.4 * sec), -0.25)), Vector((0, -1, -1)), Vector((-1, 0, 0.2)))


def anim_stand(c, t):
    sec = t * DUR["stand"]; judge(c, sec)
    d = c["cast"]["def"]; seat(d, Vector((3.2, 6.9, 0.25)), math.radians(180), 10, floor=0.25)
    H.look(d, 10 * math.sin(0.8 * sec), 8)
    reach(d, "R", Vector((3.0, 6.25, 1.1)), Vector((0, 0, -1)), Vector((0, -1, 0)))


def anim_jury(c, t):
    sec = t * DUR["jury_in"]
    keys = ("j1", "j2", "j3", "j4", "j5")
    for k, key in enumerate(keys):
        h = c["cast"][key]; x, y = JURY[k]
        u = min(1.0, max(0.0, (sec - 0.5 * k) / 2.2))
        if u < 1.0:
            H.walk_to(h, (-6.4, y - 0.2, 0), (x, y - 0.2, 0), u, swing=8, stride=0.8)
        else:
            if key == "j1" and sec > 3.3:
                H.stand_at(h, (x, y - 0.2, 0), math.radians(-90))
                c["slip"].location = h.bone_tail("wrist.R") + Vector((0.12, -0.05, 0.1))
                reach(h, "R", h.bone_head("head") + Vector((0.3, -0.1, -0.35)), Vector((0, 0, -1)), Vector((1, 0, 0.3)))
            else:
                seat(h, Vector((x, y, 0)), math.radians(-90), 6)


def anim_gavel(c, t):
    sec = t * DUR["gavel"]; judge(c, sec)
    d = c["cast"]["def"]; seat(d, Vector((1.6, 2.4, 0)), 0.0, 10)
    H.rotl(d, "head", (1, 0, 0), 18)
    l = c["cast"]["law"]; seat(l, Vector((2.4, 2.4, 0)), 0.0, 10)
    hit = 1.0 - max(0.0, math.sin(math.pi * min(1.0, max(0.0, (sec - 2.0) / 0.6))))
    gz = 1.98 + 0.25 * (1 - hit) if sec < 2.6 else 1.98
    c["gavel"].location = (0.4, 7.2, gz)
    reach(c["cast"]["judge"], "R", Vector((0.4, 7.35, gz + 0.02)), Vector((0, 0, -1)), Vector((0, -1, 0)))


MOVES = {
    "prosecutor": dict(kind="anim", dof=None, far=30, anim=anim_prosecutor,
                       cam=lambda c, t: (Vector((1.6, -0.6, 1.6)).lerp(Vector((1.2, 0.2, 1.6)), ease(t)), Vector((-2.4, 1.4, 1.2)), 28)),
    "stand": dict(kind="anim", dof=None, far=30, anim=anim_stand,
                  cam=lambda c, t: (Vector((1.0, 2.0, 1.5)).lerp(Vector((1.6, 3.2, 1.55)), ease(t)), Vector((2.0, 7.2, 1.7)), 30)),
    "jury_in": dict(kind="anim", dof=None, far=30, anim=anim_jury,
                    cam=lambda c, t: (Vector((-0.4, -0.4, 1.5)).lerp(Vector((-0.6, 0.0, 1.5)), ease(t)), Vector((-4.0, 1.7, 1.1)), 28)),
    "gavel": dict(kind="anim", dof=2.0, far=30, anim=anim_gavel,
                  cam=lambda c, t: (Vector((1.6, 0.4, 1.3)).lerp(Vector((1.6, 1.1, 1.3)), ease(t)), Vector((1.4, 4.0, 1.4)), 45),
                  focus=lambda c, t: Vector((1.6, 2.4, 1.2))),
}
