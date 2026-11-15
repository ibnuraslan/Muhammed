"""CH5 2A v2 (c5_04, 155 f): the interview room of sc_interview2 (same room, table, props, lamp, 'lift' lighting),
now with the officer in the far chair. Seen over his right shoulder: he leans in, reaches across the steel table,
lays his fingers on the passport, slides it toward himself (away from the empty near chair), lifts his hand off and
withdraws it to rest on the table. His left forearm rests on the table edge throughout.
Character and suit setup reused from sc_binder_ots (W6's c4_08 v2): matte wool suit, shirt cuffs, hair material.
Nothing moves by itself: the passport moves only while his fingers are on it."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from common import area_light, ease
from human import reset_pose, _world_verts, reach, aim_bone, SIDE
import sc_interview2 as I2
from sc_interview2 import TH
from sc_binder_ots import investigator, shirt_cuff, _bump, _palm, orient_hand, _reset_fingers, _dir, hand_verts

EXPOSURE = 0.0
VARIANT_FOR = {"slide": "lift"}
FRAMES = 155
P_TOP = TH + 0.024 + 0.006               # top face of the passport
T_TOP = TH + 0.0175                      # top face of the table
Y0, Y1 = -0.02, 0.30                     # passport travel (toward him); ends where c5_07/c5_09 have it (y = 0.3)
PX = -0.04                               # passport x (a little toward his right hand)
SEAT_Y = 0.80                            # his spine03 over this y (the far chair, pulled in to the table)
LEAN = 10                                # forward lean of the seated torso (degrees, distributed over the spine)
SEAT_H = 0.52                            # his hips (pelvis head) above the floor: an ordinary chair


def build(variant=None):
    c = I2.build(variant)
    pp = c["passport"]; pp.location = (PX, Y0, TH + 0.024)
    far = bpy.data.objects.get("FarChair")
    if far is not None:                                   # rebuilt below at his hip height (same chair, same style)
        bpy.data.objects.remove(far, do_unlink=True)
    h = investigator(); h.arm.name = "Officer"
    reset_pose(h); pose_chair(h)                          # default orientation faces -Y: toward the table and the empty chair
    sp = h.bone_head("spine03")
    h.arm.location = (0.0 - sp.x, SEAT_Y - sp.y, 0); bpy.context.view_layer.update()
    hp = h.bone_head("pelvis") if "pelvis" in h.arm.pose.bones else h.bone_head("spine05")
    h.arm.location.z += SEAT_H - hp.z; bpy.context.view_layer.update()
    feet = min(h.bone_tail(f"foot.{sd}").z for sd in ("L", "R"))
    print(f"[ots] hips {SEAT_H:.3f}, lowest foot joint {feet:.3f}", flush=True)
    c["h"] = h
    cotton = I2.pbr("ShirtCotton", (0.78, 0.78, 0.76), 0.75); _bump(cotton, 700, 0.15, 0.0003)
    for sd in ("R", "L"):
        shirt_cuff(h, sd, cotton)
    hip = h.bone_head("pelvis") if "pelvis" in h.arm.pose.bones else h.bone_head("spine05")
    c["hip"] = hip.copy()
    seat = pbr("Seat", (0.09, 0.095, 0.1), 0.45); steel = pbr("Steel", (0.35, 0.36, 0.38), 0.35, 0.9)
    sz = hip.z - 0.10                                      # seat pan top just under his hips
    sy = hip.y + 0.04
    parts = [box("FarPan", (0, sy, sz - 0.025), (0.44, 0.44, 0.05), seat, bevel=0.01),
             box("FarBack", (0, sy + 0.21, sz + 0.255), (0.42, 0.03, 0.42), seat, bevel=0.01)]
    for sx in (-0.19, 0.19):
        for dy in (-0.19, 0.19):
            parts.append(cyl("FarLeg", (sx, sy + dy, (sz - 0.05) / 2), 0.012, sz - 0.05, steel, verts=10))
        parts.append(cyl("FarPost", (sx, sy + 0.2, sz + 0.135), 0.012, 0.32, steel, verts=10))
    join(parts, "FarChair")
    # a soft kick on his hair and shoulder from behind (as in sc_binder_ots), not seen by the camera
    rim = area_light((-0.6, 1.9, 2.0), (0, 0, 0), 0.8, 6, (1.0, 0.88, 0.75)); point_at(rim, (0.0, 0.7, 1.15))
    rim.visible_camera = False; rim.visible_glossy = False
    c["focus"] = Vector((PX, (Y0 + Y1) / 2, P_TOP))
    return c


def pose_chair(h):
    """Seated upright on a chair: thighs level and forward (-Y), shins down to the floor, torso leaning in a little."""
    for sd, sg in SIDE.items():
        for b in ("upperleg01", "upperleg02"):
            h.aim(f"{b}.{sd}", (0.10 * sg, -1, -0.04))
        for b in ("lowerleg01", "lowerleg02"):
            h.aim(f"{b}.{sd}", (0.02 * sg, -0.04, -1))
        h.aim(f"foot.{sd}", (0.08 * sg, -1, -0.25))
    for b, a in (("spine05", 4), ("spine04", 5), ("spine03", 5), ("spine02", 4), ("spine01", 3)):
        h.rot(b, (1, 0, 0), LEAN * a / 21)
    for sd, sg in SIDE.items():                        # arms held out to the sides while the shirt cuffs are measured
        for b in ("upperarm01", "upperarm02", "lowerarm01", "lowerarm02"):   # (hanging by the thighs, the trousers
            h.aim(f"{b}.{sd}", (sg, -0.25, -0.35))                         # would be read as sleeve); the per-frame
                                                                           # solve places the arms
    bpy.context.view_layer.update()


# ------------------------------------------------------------------ right hand: fingertips on the passport
RH_F = Vector((0.12, -1.0, -0.30)).normalized()        # wrist -> knuckles: forward (toward -Y), slightly inward, down
RH_N = Vector((0.0, 0.0, -1.0))                         # palm down
# cumulative flexion of each phalanx (index..little): a relaxed, slightly arched hand, pads of index/middle/ring down
RH_SEGS = {"finger2": (14, 30, 38), "finger3": (14, 30, 38), "finger4": (18, 36, 44), "finger5": (24, 46, 56)}


def pose_right_hand(h, lift):
    _reset_fingers(h, "R")
    f, k, n = _palm(h, "R")
    for fg, segs in RH_SEGS.items():
        for j, deg in enumerate(segs, 1):
            aim_bone(h.arm, f"{fg}-{j}.R", _dir(f, k, n, deg - 12 * lift, 0.0))
    aim_bone(h.arm, "finger1-2.R", (f * 0.6 + k * 0.7 + n * 0.25).normalized())   # thumb relaxed alongside
    aim_bone(h.arm, "finger1-3.R", (f * 0.8 + k * 0.5 + n * 0.2).normalized())


def tips(h, sd="R"):
    """World points just under the pads of index, middle and ring finger."""
    return [h.bone_tail(f"finger{g}-3.{sd}") for g in (2, 3, 4)]


def place_right(h, tgt, lift, iters=4):
    """Wrist solved so the middle of the fingertip pads lands on tgt (x, y on the passport, z = surface + lift)."""
    wt = tgt - RH_F * 0.15 + Vector((0, 0, 0.04))
    for _ in range(iters):
        reach(h, "R", wt, Vector((-0.8, 0.3, -0.5)))       # elbow out and down to his right side
        orient_hand(h, RH_F, RH_N, "R")
        pose_right_hand(h, lift)
        tp = tips(h); m = sum(tp, Vector()) / 3
        err = Vector((tgt.x - m.x, tgt.y - m.y, 0.0))
        wt = wt + err
    # seat the pads on the surface: lowest skin vertex near the fingertips at surface + lift
    w = hand_verts(h, "R")
    return wt, w


def contact_z(h, sd, xy_box):
    """Lowest skin/clothes z of the hand inside an xy box (x0, x1, y0, y1)."""
    w = hand_verts(h, sd)
    x0, x1, y0, y1 = xy_box
    sel = (w[:, 0] > x0) & (w[:, 0] < x1) & (w[:, 1] > y0) & (w[:, 1] < y1)
    return float(w[sel][:, 2].min()) if sel.any() else None, float(w[:, 2].min())


def timeline(t):
    """Phases: 0-.10 rest | .10-.32 reach | .32-.38 settle | .38-.78 slide | .78-.84 lift | .84-1 withdraw."""
    rest = Vector((-0.10, 0.30, T_TOP))                      # resting point on the table near him (fingertips)
    p0 = Vector((PX, Y0 - 0.022, P_TOP)); p1 = Vector((PX, Y1 - 0.022, P_TOP))
    if t < 0.10:
        return rest, 0.004, Y0, 0.0
    if t < 0.32:
        e = ease((t - 0.10) / 0.22)
        a = rest.lerp(p0, e); a.z = (rest.z + (p0.z - rest.z) * e)
        return a, 0.004 + 0.035 * math.sin(math.pi * e), Y0, 0.0
    if t < 0.38:
        return p0, 0.004 * (1 - ease((t - 0.32) / 0.06)), Y0, 0.0
    if t < 0.78:
        e = ease((t - 0.38) / 0.40)
        return p0.lerp(p1, e), 0.0, Y0 + (Y1 - Y0) * e, 0.0
    if t < 0.84:
        e = ease((t - 0.78) / 0.06)
        return p1, 0.012 * e, Y1, e
    e = ease((t - 0.84) / 0.16)
    back = rest + Vector((0.03, 0.0, 0.0))
    a = p1.lerp(back, e); a.z = p1.z + (back.z - p1.z) * e
    return a, 0.012 * (1 - e) + 0.004 + 0.02 * math.sin(math.pi * e), Y1, 1 - e


def anim(c, t):
    h = c["h"]
    tgt, lift, py, open_ = timeline(t)
    c["passport"].location = (PX, py, TH + 0.024)
    reach_amt = max(0.0, min(1.0, (0.30 - tgt.y) / 0.32))       # how far forward his hand is
    h.rot("spine02", (1, 0, 0), 4 * reach_amt); h.rot("spine01", (1, 0, 0), 3 * reach_amt)
    h.rot("neck01", (1, 0, 0), 4); h.rot("head", (1, 0, 0), 10 + 4 * reach_amt)
    h.rot("head", (0, 0, 1), 3)
    surf = P_TOP if (abs(tgt.x - PX) < 0.07 and abs(tgt.y - py) < 0.065) else T_TOP
    dz = c.get("rh_dz", 0.0)
    for _ in range(3):
        g = Vector((tgt.x, tgt.y, surf + lift + 0.0006 + dz))
        place_right(h, g, open_)
        lo, _ = contact_z(h, "R", (tgt.x - 0.06, tgt.x + 0.06, tgt.y - 0.05, tgt.y + 0.05))
        if lo is None:
            break
        dz += (surf + lift + 0.0006) - lo
    c["rh_dz"] = dz
    lo, allmin = contact_z(h, "R", (tgt.x - 0.06, tgt.x + 0.06, tgt.y - 0.05, tgt.y + 0.05))
    c["rh_gap"] = None if lo is None else lo - surf
    c["rh_min"] = allmin
    pose_left(h, c)
    bpy.context.view_layer.update()


LH_F = Vector((-0.55, -0.83, -0.05)).normalized()          # left forearm across the table edge, hand toward his midline
LH_N = Vector((0.05, 0.0, -1.0))
LH_SEGS = ((10, 22, 30), (12, 26, 34), (14, 30, 38), (16, 34, 42))


def pose_left(h, c):
    dz = c.get("lh_dz", 0.02)
    for _ in range(3):
        lw = Vector((0.22, 0.33, T_TOP + 0.03 + dz))
        reach(h, "L", lw, Vector((0.9, 0.2, -0.6)))
        orient_hand(h, LH_F, LH_N, "L")
        _reset_fingers(h, "L")
        f, k, n = _palm(h, "L")
        for fg, segs in zip(("finger2", "finger3", "finger4", "finger5"), LH_SEGS):
            for j, deg in enumerate(segs, 1):
                aim_bone(h.arm, f"{fg}-{j}.L", _dir(f, k, n, deg, 0.0))
        aim_bone(h.arm, "finger1-2.L", (f * 0.7 + k * 0.6 - n * 0.05).normalized())
        aim_bone(h.arm, "finger1-3.L", (f * 0.85 + k * 0.4 - n * 0.05).normalized())
        bpy.context.view_layer.update()
        w = hand_verts(h, "L")
        sel = w[:, 1] < 0.42                                 # over the table top only
        lo = float(w[sel][:, 2].min()) if sel.any() else T_TOP
        dz += (T_TOP + 0.0012) - lo
    c["lh_dz"] = dz


def cam(c, t):
    e = ease(t)
    loc = Vector((-0.98, 1.22, 1.78)).lerp(Vector((-0.92, 1.14, 1.73)), e)     # over his right shoulder, slow push
    tgt = Vector((PX + 0.03, 0.13, TH + 0.03))
    return loc, tgt, 44


MOVES = {"slide": dict(kind="anim", dof=2.8, far=12.0, anim=anim, cam=cam, focus=lambda c, t: c["passport"].location)}
