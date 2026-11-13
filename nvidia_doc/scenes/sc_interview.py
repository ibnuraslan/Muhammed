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

EXPOSURE = 0.0
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
    # wall clock with a turning second hand (frame driver -> plays in any render)
    box("ClockFace", (1.4, 2.54, 2.3), (0.001, 0.26, 0.26), emissive("ClockFace", (0.95, 0.95, 0.93), 0.6), rot=(0, math.radians(90), 0))
    hand = box("SecondHand", (1.39, 2.54, 2.3), (0.004, 0.012, 0.2), pbr("Hand", (0.05, 0.05, 0.05), 0.4))
    hand.location = (1.39, 2.54, 2.3)
    drv = hand.driver_add("rotation_euler", 0).driver         # spin around the face normal (X axis here)
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
                           title=("CHAPTER 5", "THE PASSPORT AND THE PAPER TRAIL", 18, 120),
                           cam=lambda c, t: (Vector((1.65, -2.15, 1.35)).lerp(Vector((1.35, -1.75, 1.28)), ease(t)),
                                             Vector((0.0, -0.05, TH + 0.05)), 40),
                           focus=lambda c, t: c["passport"].location),
    "question": dict(kind="anim", dof=2.2, far=12.0, anim=anim_take,
                     cam=lambda c, t: (Vector((1.5, -1.75, 1.2)).lerp(Vector((1.35, -1.5, 1.16)), ease(t)),
                                       Vector((0.0, 0.05, TH + 0.04)), 50),
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
