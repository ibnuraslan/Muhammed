"""CH5 (NEW): a plain police interview room (Singapore), house style. A laminate table, two chairs (the near one,
Alice's, left empty), a thin passport booklet and a document folder on the table, a wall clock whose second hand
turns, cool institutional light through a high window. No people: Alice is represented by the empty chair; the
passport moves on its own across the table (taken, then returned) so nothing needs a hand close-up.

  passport_slide : CH5 1A, establishing medium + CHAPTER 5 title, slow push; passport sits mid-table
  question       : CH5 2A, the passport slides away from the empty chair (police take it)
  warning        : CH5 4B, the empty near chair, slow push; passport held on the far side
  passport_back  : CH5 5A, the passport slides back toward the empty chair (returned)
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from common import area_light, world_flat

EXPOSURE = -0.8
TH = 0.75                      # table-top height
NEAR_Y, FAR_Y = -0.95, 0.95    # Alice's (empty) chair near camera; officer's chair far side


def _chair(name, y, facing):
    seat = pbr(name + "Seat", (0.07, 0.08, 0.09), 0.5)
    frame = pbr(name + "Frame", (0.05, 0.05, 0.055), 0.4, 0.8)
    parts = [box(name + "Pan", (0, y, 0.46), (0.44, 0.44, 0.07), seat, bevel=0.02),
             box(name + "Back", (0, y - facing * 0.2, 0.74), (0.44, 0.06, 0.5), seat, bevel=0.02)]
    for sx in (-0.18, 0.18):
        for sy in (-0.18, 0.18):
            parts.append(cyl(name + "Leg", (sx, y + sy, 0.23), 0.02, 0.46, frame))
    return join(parts, name)


def build(variant=None):
    c = {}
    world_flat((0.03, 0.035, 0.04), 1.0)
    # room shell
    floor = pbr("Vinyl", (0.30, 0.31, 0.32), 0.35, 0.0, **{'Coat Weight': 0.3})
    box("Floor", (0, 0, 0), (7, 7, 0.04), floor)
    wall = pbr("Wall", (0.40, 0.43, 0.43), 0.9)
    box("WallBack", (0, 2.6, 1.6), (7, 0.1, 3.2), wall)
    box("WallL", (-3.0, 0, 1.6), (0.1, 7, 3.2), wall)
    box("WallR", (3.0, 0, 1.6), (0.1, 7, 3.2), wall)
    box("Ceil", (0, 0, 3.2), (7, 7, 0.1), pbr("Ceil", (0.8, 0.82, 0.83), 0.9))
    # high window on the back wall with cool daylight behind it
    box("WinGlass", (-1.4, 2.54, 2.2), (1.6, 0.02, 1.1), glass("WinG", (0.9, 0.94, 0.98), 0.0))
    sky = emissive("SkyPanel", (0.55, 0.66, 0.80), 1.4)
    box("SkyPanel", (-1.4, 2.72, 2.2), (1.7, 0.02, 1.2), sky)
    area_light((-1.4, 1.6, 2.3), (math.radians(90), 0, 0), 2.2, 120, (0.8, 0.88, 1.0))
    # fluorescent ceiling
    for yy in (-1.2, 1.2):
        box("Panel", (0, yy, 3.12), (1.3, 0.5, 0.04), emissive("Fluoro", (1.0, 0.98, 0.94), 2.4))
        area_light((0, yy, 3.0), (0, 0, 0), 1.2, 110, (1.0, 0.97, 0.92))
    # table
    top = wood("TableTop", (0.14, 0.15, 0.16), (0.22, 0.23, 0.24), rough=0.3, coat=0.4)
    box("TableTop", (0, 0, TH), (1.7, 1.0, 0.05), top, bevel=0.01)
    leg = pbr("TableLeg", (0.06, 0.06, 0.07), 0.4, 0.8)
    for sx in (-0.75, 0.75):
        for sy in (-0.4, 0.4):
            box("TLeg", (sx, sy, TH / 2), (0.05, 0.05, TH), leg)
    c["near_chair"] = _chair("NearChair", NEAR_Y, +1)      # empty (Alice)
    c["far_chair"] = _chair("FarChair", FAR_Y, -1)
    # props: a passport booklet, a document folder, a water cup
    pass_mat = pbr("Passport", (0.17, 0.03, 0.04), 0.45)   # dark red booklet, no emblem
    passport = box("Passport", (0.0, -0.28, TH + 0.035), (0.125, 0.088, 0.012), pass_mat, bevel=0.004)
    c["passport"] = passport
    folder = box("Folder", (0.52, 0.12, TH + 0.03), (0.23, 0.31, 0.015), pbr("Folder", (0.5, 0.46, 0.36), 0.8), bevel=0.004, rot=(0, 0, 0.1))
    cup = cyl("Cup", (-0.55, 0.2, TH + 0.06), 0.035, 0.09, glass("Cup", (0.95, 0.97, 0.98), 0.0))
    # a desk recorder (black, red record light), a second file with a few loose sheets, a pen
    rec = pbr("Recorder", (0.03, 0.03, 0.035), 0.4)
    box("Recorder", (-0.25, 0.32, TH + 0.045), (0.16, 0.09, 0.04), rec, bevel=0.008, rot=(0, 0, -0.15))
    box("RecGrille", (-0.25, 0.32, TH + 0.066), (0.1, 0.05, 0.002), pbr("Grille", (0.12, 0.12, 0.13), 0.6), rot=(0, 0, -0.15))
    lm = bpy.data.materials.new("RecLED"); lm.use_nodes = True
    Nn = lm.node_tree.nodes; Ll = lm.node_tree.links; Nn.clear()
    o_ = Nn.new("ShaderNodeOutputMaterial"); em = Nn.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (1.0, 0.1, 0.05, 1)
    v = Nn.new("ShaderNodeValue"); dd = v.outputs[0].driver_add("default_value").driver; dd.type = 'SCRIPTED'
    dd.expression = "6 * (1 if (frame % 48) < 36 else 0.2)"
    Ll.new(v.outputs[0], em.inputs['Strength']); Ll.new(em.outputs[0], o_.inputs['Surface'])
    box("RecLED", (-0.19, 0.30, TH + 0.067), (0.012, 0.012, 0.004), lm)
    box("FileB", (0.45, 0.42, TH + 0.045), (0.24, 0.32, 0.02), pbr("FileB", (0.18, 0.24, 0.36), 0.7), bevel=0.004, rot=(0, 0, -0.25))
    for k in range(3):
        box("Sheet", (0.25 + 0.03 * k, -0.05 + 0.02 * k, TH + 0.027 + 0.001 * k), (0.21, 0.297, 0.001), pbr("Sheet", (0.9, 0.89, 0.86), 0.8), rot=(0, 0, 0.2 - 0.12 * k))
    cyl("Pen", (0.1, -0.2, TH + 0.03), 0.004, 0.14, pbr("Pen", (0.02, 0.02, 0.025), 0.3, 0.8), verts=12, rot=(math.radians(90), 0, 0.7))
    # blinds over the high window, a cork notice board, a wall-mounted camera
    for k in range(18):
        box("Blind", (-1.4, 2.5, 1.7 + k * 0.058), (1.7, 0.05, 0.006), pbr("BlindM", (0.7, 0.7, 0.68), 0.5), rot=(math.radians(50), 0, 0))
    box("NoticeBoard", (0.4, 2.54, 1.75), (0.9, 0.02, 0.6), pbr("Cork", (0.45, 0.33, 0.2), 0.9))
    for k, (dx, dz) in enumerate(((-0.25, 0.1), (0.05, -0.08), (0.25, 0.12))):
        box("Notice", (0.4 + dx, 2.525, 1.75 + dz), (0.18, 0.005, 0.24), pbr("NoticeP", (0.92, 0.91, 0.88), 0.8))
    box("WallCam", (2.85, 2.4, 2.9), (0.12, 0.2, 0.1), pbr("WallCam", (0.85, 0.85, 0.85), 0.4), bevel=0.02)
    # wall clock with a turning second hand (frame driver -> plays in any render)
    cyl("ClockRim", (1.25, 2.555, 2.15), 0.15, 0.03, pbr("ClockRim", (0.05, 0.05, 0.05), 0.4), verts=40, rot=(math.radians(90), 0, 0))
    box("ClockFace", (1.25, 2.535, 2.15), (0.27, 0.006, 0.27), emissive("ClockFace", (0.95, 0.95, 0.93), 0.6))
    hand = box("SecondHand", (1.25, 2.528, 2.15), (0.008, 0.004, 0.22), pbr("Hand", (0.05, 0.05, 0.05), 0.4))
    box("HourHand", (1.25, 2.529, 2.18), (0.012, 0.004, 0.08), pbr("Hand", (0.05, 0.05, 0.05), 0.4), rot=(0, math.radians(40), 0))
    hand.location = (1.25, 2.528, 2.15)
    drv = hand.driver_add("rotation_euler", 1).driver         # spin around the face normal (Y axis)
    drv.type = 'SCRIPTED'; drv.expression = "-frame * 0.10"
    hand.rotation_mode = 'XYZ'
    c["table_focus"] = Vector((0.0, -0.1, TH + 0.05))
    return c


def _slide(c, y_from, y_to, t):
    c["passport"].location = (0.0, y_from + (y_to - y_from) * ease(t), TH + 0.035)


def anim_hold(c, t):
    _slide(c, -0.28, -0.24, t)                               # a touch of drift so the frame is never fully static


def anim_take(c, t):
    _slide(c, -0.30, 0.34, t)                                # police take the passport across the table


def anim_back(c, t):
    _slide(c, 0.34, -0.26, t)                                # the passport slid back toward the empty chair


def anim_warn(c, t):
    c["passport"].location = (0.30, 0.34, TH + 0.035)        # held on the far side; near chair sits empty


MOVES = {
    # CH5 1A: establishing medium + CHAPTER 5 title (two-line card + scrim via bake.py).
    # DOF off so the camera-parented title plane stays crisp (as in the Ch1-3 title shots).
    "passport_slide": dict(kind="anim", far=12.0, anim=anim_hold,
                           title=("CHAPTER 5", "THE PASSPORT AND THE PAPER TRAIL", 18, 120, 0.75),     # stronger scrim: bright room
                           cam=lambda c, t: (Vector((1.85, -2.45, 1.45)).lerp(Vector((1.55, -2.05, 1.38)), ease(t)),
                                             Vector((-0.1, 0.4, 1.05)), 30),
                           focus=lambda c, t: c["passport"].location),
    "question": dict(kind="anim", dof=2.2, far=12.0, anim=anim_take,
                     cam=lambda c, t: (Vector((1.6, -1.85, 1.32)).lerp(Vector((1.42, -1.6, 1.27)), ease(t)),
                                       Vector((-0.05, 0.35, 0.98)), 38),
                     focus=lambda c, t: c["passport"].location),
    "warning": dict(kind="anim", dof=2.8, far=12.0, anim=anim_warn,
                    cam=lambda c, t: (Vector((1.55, -2.0, 1.3)).lerp(Vector((1.45, -1.7, 1.24)), ease(t)),
                                      Vector((0.0, NEAR_Y, TH + 0.02)), 44),
                    focus=lambda c, t: Vector((0.0, NEAR_Y + 0.1, 0.6))),
    "passport_back": dict(kind="anim", dof=2.2, far=12.0, anim=anim_back,
                          cam=lambda c, t: (Vector((1.45, -1.7, 1.18)).lerp(Vector((1.5, -1.9, 1.22)), ease(t)),
                                            Vector((0.0, -0.1, TH + 0.04)), 50),
                          focus=lambda c, t: c["passport"].location),
}
