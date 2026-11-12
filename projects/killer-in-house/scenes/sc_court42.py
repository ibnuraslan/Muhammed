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
    # winter afternoon: soft cool window light, warm pendant fill; plain (non-noisy) panelling, no moire
    world_sky(sun_elev_deg=18, sun_rot_deg=100, strength=0.5, tint=(0.88, 0.93, 1.0))
    sun(18, 20, energy=1.8, color=(0.92, 0.95, 1.0), angle_deg=3.0)
    bpy.context.scene.view_settings.exposure = 0.35
    oak = wood("COak", (0.17, 0.1, 0.05), (0.26, 0.15, 0.08), scale=(0.04, 0.8, 0.8), rough=0.45, coat=0.2)      # grain enlarged ~8x
    dark = wood("CDark", (0.06, 0.035, 0.02), (0.11, 0.065, 0.035), scale=(0.04, 0.8, 0.8), rough=0.42, coat=0.25)
    pl = pbr("CPlaster", (0.66, 0.63, 0.56), 0.9)
    box("Floor", (0, 2, -0.02), (14, 18, 0.04), fabric("CourtCarpet", (0.2, 0.08, 0.06), 0.95, 0.2, 500))
    box("WallBack", (0, 9.5, 3.5), (14, 0.2, 7), dark)
    box("WallL", (-7, 2, 3.5), (0.2, 18, 7), pl); box("PanelL", (-6.88, 2, 1.1), (0.04, 18, 2.2), dark)
    box("Ceil", (0, 2, 7), (14, 18, 0.2), pbr("CCeil", (0.6, 0.57, 0.52), 0.85))
    H.wall_y("WinWall", -7, 11, 7, 0, 7, 0.25, pl, [(y - 0.7, y + 0.7, 1.4, 5.6) for y in (-3, 0.5, 4, 7.5)])
    for y in (-3, 0.5, 4, 7.5):
        H.window_unit('y', y, 1.4, 7.0, 1.4, 5.6)
    sc_ = bpy.context.scene; sc_.cycles.sample_clamp_indirect = 3.0; sc_.cycles.use_denoising = True   # no speckle on panelling
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
    # US flag on a pole beside the bench (generated image, as the shared courtroom set)
    import os, sys
    gen = os.path.join("/home/user/Muhammed/nvidia_doc/assets", "generated"); fimg = os.path.join(gen, "us_flag.png")
    if not os.path.exists(fimg):
        import sc_capitol; sc_capitol.flag_image(fimg)
    fm = bpy.data.materials.new("Flag"); fm.use_nodes = True
    N = fm.node_tree.nodes; L = fm.node_tree.links; tx = N.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(fimg)
    tc = N.new("ShaderNodeTexCoord"); L.new(tc.outputs['UV'], tx.inputs['Vector']); L.new(tx.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
    gold = pbr("PoleGold", (0.7, 0.52, 0.22), 0.3, 1.0)
    cyl("FlagPole", (-2.9, 8.6, 1.6), 0.03, 3.2, gold, 12)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=30, y_subdivisions=20, size=1, location=(-2.5, 8.6, 2.65), rotation=(math.radians(90), 0, 0))
    f = bpy.context.active_object; f.scale = (0.8, 1.2, 1); f.data.materials.append(fm)
    wv = f.modifiers.new("wave", 'WAVE'); wv.height = 0.04; wv.width = 0.4; wv.speed = 0.0
    c["gavel"] = join([cyl("GavelHead", (0, 0, 0), 0.035, 0.12, dark, 24, rot=(0, math.radians(90), 0)),
                       cyl("GavelHandle", (0, -0.13, 0), 0.012, 0.25, dark, 12, rot=(math.radians(90), 0, 0))], "Gavel")
    c["slip"] = box("Slip", (0, 0, -20), (0.1, 0.004, 0.14), pbr("SlipPaper", (0.9, 0.88, 0.82), 0.8))
    # cast per variant
    jk = ["neighbour_m", "captain", "son", "detective2", "neighbour_m", "captain", "son", "neighbour_m", "detective2", "captain", "son", "neighbour_m"]
    jury = {"j%d" % (k + 1): jk[k] for k in range(12)}
    gallery = {"g%d" % (k + 1): ("detective", "detective2", "officer", "son")[k % 4] for k in range(8)}
    kinds = {"prosecutor": dict(pr="detective2", judge="judge", **jury, **gallery),
             "stand": {"def": "thin_court", "judge": "judge"},
             "jury_in": dict(judge="judge", **jury),
             "gavel": {"def": "thin_court", "judge": "judge", "law": "detective2"}}[variant]
    c["cast"] = {k: H.person(v.capitalize() + k, v) for k, v in kinds.items()}
    return c


def seat(h, loc, rz, lean=8, floor=0.0):
    reset_pose(h); pose_sit(h, lean=lean)
    h.arm.rotation_euler = (0, 0, rz); h.arm.location = loc; bpy.context.view_layer.update(); H.ground_to(h, floor)


def judge(c, sec):
    j = c["cast"]["judge"]; seat(j, Vector((0, 8.5, 0.5)), 0.0, 12, floor=0.5)
    H.look(j, 0, 15)


GALLERY = [(x, -1.2 - k * 1.2) for k in range(2) for x in (-3.8, -2.0, 1.9, 3.6)]


def anim_prosecutor(c, t):
    sec = t * DUR["prosecutor"]; judge(c, sec)
    for k in range(12):
        x, y = JURY[k]; key = "j%d" % (k + 1)
        seat(c["cast"][key], Vector((x, y, 0)), math.radians(-90), 6, floor=0.24 if y > 2 else 0.0)
        H.look(c["cast"][key], 10, 0)
    for k, (x, y) in enumerate(GALLERY):
        seat(c["cast"]["g%d" % (k + 1)], Vector((x, y + 0.05, 0)), math.pi, 4)
    pr = c["cast"]["pr"]
    H.walk_to(pr, (-0.6, 0.6, 0), (-0.9, 0.9, 0), 0.5 + 0.3 * math.sin(0.5 * sec), swing=4, face=math.radians(90))
    reach(pr, "R", pr.bone_head("head") + Vector((-0.45, 0.15 * math.sin(1.4 * sec), -0.25)), Vector((0, -1, -1)), Vector((-1, 0, 0.2)))


def anim_stand(c, t):
    sec = t * DUR["stand"]; judge(c, sec)
    if "key" not in c:
        c["key"] = area_light((1.6, 6.6, 2.2), (0, 0, 0), 0.8, 120, (1.0, 0.95, 0.88)); point_at(c["key"], (3.2, 6.9, 1.3)); c["key"].visible_camera = False
    d = c["cast"]["def"]; seat(d, Vector((3.2, 6.9, 0.25)), 0.0, 10, floor=0.25)          # faces the court
    H.look(d, 10 * math.sin(0.8 * sec), 8)
    reach(d, "R", Vector((3.05, 6.55, 0.95)), Vector((0, 0, -1)), Vector((0, -1, 0)))


def anim_jury(c, t):
    sec = t * DUR["jury_in"]; judge(c, sec)
    keys = tuple("j%d" % (k + 1) for k in range(12))
    for k, key in enumerate(keys):
        h = c["cast"][key]; x, y = JURY[k]
        u = min(1.0, max(0.0, (sec + 2.6 - 0.35 * k) / 2.2))
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
    d = c["cast"]["def"]; H.stand_at(d, (1.6, 2.2, 0), math.pi)                   # standing for the verdict
    H.rotl(d, "head", (1, 0, 0), 14)
    l = c["cast"]["law"]; seat(l, Vector((2.4, 2.4, 0)), math.pi, 10)
    hit = 1.0 - max(0.0, math.sin(math.pi * min(1.0, max(0.0, (sec - 2.0) / 0.6))))
    gz = 1.98 + 0.25 * (1 - hit) if sec < 2.6 else 1.98
    c["gavel"].location = (0.4, 7.2, gz)
    reach(c["cast"]["judge"], "R", Vector((0.4, 7.35, gz + 0.02)), Vector((0, 0, -1)), Vector((0, -1, 0)))


MOVES = {
    "prosecutor": dict(kind="anim", dof=None, far=30, anim=anim_prosecutor,
                       cam=lambda c, t: (Vector((5.6, -5.2, 2.5)).lerp(Vector((5.2, -4.6, 2.45)), ease(t)), Vector((-2.2, 2.2, 1.0)), 24)),
    "stand": dict(kind="anim", dof=None, far=30, anim=anim_stand,
                  cam=lambda c, t: (Vector((1.2, 5.9, 1.45)).lerp(Vector((1.5, 6.0, 1.45)), ease(t)), Vector((3.2, 6.95, 1.3)), 40)),
    "jury_in": dict(kind="anim", dof=None, far=30, anim=anim_jury,
                    cam=lambda c, t: (Vector((-0.4, -0.4, 1.5)).lerp(Vector((-0.6, 0.0, 1.5)), ease(t)), Vector((-4.0, 1.7, 1.1)), 28)),
    "gavel": dict(kind="anim", dof=4.0, far=30, anim=anim_gavel,
                  cam=lambda c, t: (Vector((3.4, 1.2, 1.6)).lerp(Vector((3.1, 1.45, 1.6)), ease(t)), Vector((1.1, 3.6, 1.6)), 34),
                  focus=lambda c, t: Vector((1.6, 2.2, 1.6))),
}
