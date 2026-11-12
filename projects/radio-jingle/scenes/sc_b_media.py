"""CH3/CH4/CH5 (chat B): three working rooms (generic: no show names, no crests, no readable text).
  studio81: a 1980s TV studio during a crime appeal (no real programme).
            appeal (A): a presenter at a plain desk under studio lights; a pedestal camera dollies past in the foreground
            phones (B): a row of desks: officers answer ringing phones and write tips on slips
  office07: a 2007 investigation office, rain on the window.
            pin    (A): a detective pins a file to the cork wall
            clock  (B): slow push past file boxes to a wall clock, its second hand ticking
  edit24:   a dark 2024 broadcast edit suite.
            scrub  (A): two journalists watch archive footage on monitors, scrubbing it
            paused (B): a reel-recorder image paused on screen; the camera drifts past their silhouettes
"""
import math, os
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from common import world_flat, ease
from human import reach, fingers_curl
import ph
import b_common as B
import b_props as P

EXPOSURE = 0.2
DUR = {"appeal": 5.5, "phones": 5.0, "pin": 5.0, "clock": 5.0, "scrub": 5.5, "paused": 5.5}
VARIANT_FOR = {"appeal": "studio81", "phones": "studio81", "pin": "office07", "clock": "office07", "scrub": "edit24", "paused": "edit24"}


def studio_camera(name, loc, rot_z):
    dark = pbr(name + "Body", (0.05, 0.05, 0.055), 0.4); grey = pbr(name + "Grey", (0.3, 0.3, 0.32), 0.4, 0.5)
    parts = [box("CamBody", (0, 0.1, 1.45), (0.32, 0.55, 0.38), grey, bevel=0.02),
             cyl("CamLens", (0, -0.3, 1.45), 0.11, 0.35, dark, verts=32, rot=(math.radians(90), 0, 0)),
             box("CamVF", (0, 0.42, 1.6), (0.24, 0.1, 0.18), dark, bevel=0.01),
             cyl("Column", (0, 0.05, 0.75), 0.06, 1.2, grey, verts=16),
             cyl("Base", (0, 0.05, 0.1), 0.45, 0.08, dark, verts=6),
             cyl("Ring", (0, 0.05, 1.05), 0.28, 0.02, grey, verts=32)]
    o = join(parts, name); o.location = loc; o.rotation_euler = (0, 0, rot_z)
    return o


def build(variant=None):
    variant = variant or "studio81"
    c = {"variant": variant}
    rng = np.random.default_rng(84)
    world_flat((0.004, 0.005, 0.007), 1.0)
    if variant == "studio81":
        box("Floor", (0, 0, -0.01), (16, 12, 0.02), pbr("StudioFloor", (0.08, 0.08, 0.085), 0.3, **{'Coat Weight': 0.3}))
        # the set: a curved blue backdrop with soft abstract panels (no text), a plain desk
        for k in range(9):
            a = math.radians(-40 + k * 10)
            box("Backdrop", (6.0 * math.sin(a), 4.5 + 6.0 * (1 - math.cos(a)) * 0.0 + 1.2 * (1 - math.cos(a)), 1.6), (1.1, 0.06, 3.2),
                pbr("BackBlue", (0.06, 0.12, 0.3) if k % 2 else (0.1, 0.16, 0.32), 0.6), rot=(0, 0, a))
        box("Desk", (0, 2.6, 0.4), (2.2, 0.7, 0.8), pbr("DeskGrey", (0.35, 0.36, 0.4), 0.4), bevel=0.02)
        box("DeskTop", (0, 2.6, 0.81), (2.3, 0.75, 0.03), pbr("DeskTopW", (0.6, 0.6, 0.62), 0.3))
        B.sheet("Notes", (0.15, 2.6, 0.83), (0.21, 0.297), B.paper_mat("PrNotes", (0.88, 0.87, 0.82)), rot=(0, 0, 0.1))
        pres = B.person("Presenter", 1.0, 50, "male_elegantsuit01", "short02", hue=0.6, sat=0.2, val=0.3, hair_val=0.8, hair_sat=0.2)
        B.seat(pres, (0, 3.15, 0), 0.0, lean=6)
        c["pres"] = pres
        c["studiocam"] = studio_camera("StudioCam", (-3.0, -1.5, 0), math.radians(-15))
        studio_camera("StudioCam2", (2.6, -1.8, 0), math.radians(25))
        # lighting grid: hard keys from the grid, a cold backlight on the set, a warm key on the presenter
        for x in (-3, 0, 3):
            box("GridBar", (x, 0.5, 4.5), (0.08, 10, 0.08), pbr("GridM", (0.1, 0.1, 0.1), 0.5, 0.6))
            cyl("Fresnel", (x, 1.2, 4.3), 0.15, 0.3, pbr("FresnelM", (0.05, 0.05, 0.05), 0.5), verts=16, rot=(math.radians(60), 0, 0))
        B.key_spot((1.6, 0.0, 4.2), (0, 3.1, 1.3), 1400, 25, (1.0, 0.86, 0.68), soft=0.15, name="PresKey")
        B.key_spot((0.0, 6.0, 4.0), (0, 3.2, 1.4), 900, 30, (0.6, 0.72, 1.0), soft=0.1, name="BackLight")
        # the phone desks (to the right of the set, under their own lamps)
        c["callers"] = []
        try:
            import rj
            have_rj = True
        except Exception:
            have_rj = False
        for k in range(4):
            x = 5.0 + k * 1.3; y = 1.5
            box("PDesk", (x, y, 0.37), (1.1, 0.6, 0.74), pbr("PDeskM", (0.3, 0.25, 0.2), 0.5))
            if have_rj:
                r, hs, dial = rj.rotary_phone(f"Ph{k}"); r.location = (x - 0.25, y + 0.05, 0.74); r.rotation_euler = (0, 0, 0.1)
            else:
                hs = box(f"Hs{k}", (x - 0.25, y + 0.05, 0.8), (0.2, 0.05, 0.05), pbr("HsM", (0.6, 0.5, 0.3), 0.4))
            B.sheet(f"Slip{k}", (x + 0.1, y - 0.05, 0.742), (0.1, 0.14), B.paper_mat("Slip", (0.9, 0.88, 0.7)), rot=(0, 0, 0.2))
            h = B.person(f"Caller{k}", 1.0 if k % 2 == 0 else 0.0, 30 + 7 * k, "male_casualsuit05" if k % 2 == 0 else "female_elegantsuit01",
                         ["short03", "bob01", "short01", "ponytail01"][k], hue=0.5 + 0.03 * k, sat=0.3, val=0.35, hair_val=0.3)
            B.seat(h, (x, y - 0.45, 0), math.pi, lean=12)
            c["callers"].append((h, hs))
            B.key_spot((x, y - 0.3, 2.4), (x, y, 0.75), 160, 50, (1.0, 0.75, 0.5), soft=0.1, name="PLamp")
        c["rest"] = {"pres": B.capture(pres), **{f"c{k}": B.capture(h) for k, (h, _) in enumerate(c["callers"])}}
        B.room_haze((2, 1, 2.5), (16, 12, 5), density=0.012)
    elif variant == "office07":
        box("Floor", (0, 0, -0.01), (7, 6, 0.02), B.tex_mat("OffFl", "grey_tiles", scale=0.5, tint=(0.5, 0.5, 0.5)))
        wall = B.plaster("OffWall", (0.55, 0.55, 0.52), dirt=0.1)
        box("WallB", (0, 3.0, 1.4), (7, 0.1, 2.8), wall); box("WallL", (-3.5, 0, 1.4), (0.1, 6, 2.8), wall)
        box("WallF", (0, -3.0, 1.4), (7, 0.1, 2.8), wall)
        box("WallR_lo", (3.5, 0, 0.45), (0.1, 6, 0.9), wall); box("WallR_hi", (3.5, 0, 2.55), (0.1, 6, 0.5), wall)
        box("WallR_a", (3.5, -2.2, 1.6), (0.1, 1.6, 1.4), wall); box("WallR_b", (3.5, 2.2, 1.6), (0.1, 1.6, 1.4), wall)
        box("RainPane", (3.5, 0.0, 1.6), (0.02, 2.8, 1.4), rain_glass("Rain", 60, 0.4))
        sky = box("Outside", (6.0, 0, 1.5), (0.05, 8, 4), emissive("RainSky", (0.55, 0.62, 0.7), 0.9)); sky.visible_shadow = False
        B.key_spot((5.0, 0.0, 2.2), (0.0, 1.5, 1.0), 3500, 50, (0.75, 0.85, 1.0), soft=0.8, name="WinKey")
        B.key_spot((1.5, 1.0, 2.7), (-0.3, 2.9, 1.4), 400, 40, (1.0, 0.78, 0.55), soft=0.3, name="DeskLampKey")
        box("Ceil", (0, 0, 2.82), (7, 6, 0.04), wall)
        cork = pbr("Cork", (0.42, 0.3, 0.19), 0.9)
        box("Cork", (-0.5, 2.94, 1.5), (3.0, 0.03, 1.3), cork)
        pm = [B.paper_mat(f"Pin{k}", (0.88, 0.87, 0.82)) for k in range(2)]
        for k in range(14):
            B.sheet("Pinned", (-1.8 + (k % 7) * 0.4 + rng.uniform(-0.05, 0.05), 2.92, 1.15 + (k // 7) * 0.55 + rng.uniform(-0.04, 0.04)), (0.21, 0.297), pm[k % 2],
                    rot=(math.radians(90), 0, rng.uniform(-0.05, 0.05)))
        c["newfile"] = box("NewFile", (0, 0, 0), (0.24, 0.02, 0.32), pbr("FileRed", (0.45, 0.08, 0.06), 0.7), bevel=0.003)
        ph.model("metal_office_desk", loc=(0.5, 0.0, 0), rot_z=0)
        for k in range(5):
            box("ArchBox", (2.6, -1.5 + k * 0.45, 0.17 + 0.0), (0.4, 0.38, 0.34), pbr("ArchBoxM", (0.55, 0.45, 0.3), 0.85), bevel=0.01)
            box("ArchBox", (2.6, -1.4 + k * 0.45, 0.51), (0.4, 0.38, 0.34), pbr("ArchBoxM", (0.55, 0.45, 0.3), 0.85), bevel=0.01)
        try:
            ph.model("wall_clock", loc=(2.2, 2.95, 2.1), rot_z=0)
        except Exception:
            pass
        hand = box("SecondHand", (0, 0, 0), (0.003, 0.002, 0.13), pbr("SecRed", (0.7, 0.05, 0.03), 0.4))
        hand.location = (2.2, 2.93, 2.1)
        d = hand.driver_add("rotation_euler", 1).driver; d.type = 'SCRIPTED'; d.expression = "floor(frame / 24) * 0.10472"
        c["hand"] = hand
        det = B.person("Detective07", 1.0, 48, "male_casualsuit05", "short02", hue=0.6, sat=0.2, val=0.32, hair_val=1.0, hair_sat=0.2)
        B.stand(det, (-0.3, 2.35, 0), math.pi)
        c["det"] = det; c["rest"] = {"det": B.capture(det)}
        B.practical((0.8, 0.2, 2.6), 80, (1.0, 0.8, 0.6), 0.3, "OffBulb")
        B.room_haze((0, 0, 1.4), (6.8, 5.8, 2.8), density=0.01)
    else:
        box("Floor", (0, 0, -0.01), (6, 5, 0.02), pbr("EditFloor", (0.05, 0.05, 0.055), 0.6))
        wall = pbr("EditWall", (0.06, 0.065, 0.07), 0.8)
        box("WallB", (0, 2.5, 1.4), (6, 0.1, 2.8), wall); box("WallL", (-3, 0, 1.4), (0.1, 5, 2.8), wall); box("WallR", (3, 0, 1.4), (0.1, 5, 2.8), wall)
        foot = os.path.join(B.GEN, "b_footage.png")
        if not os.path.exists(foot):
            P.waveform_image(foot, segments=1, seed=55)
        rec_img = os.path.join(B.GEN, "b_archive_recorder.png")
        img = rec_img if os.path.exists(rec_img) else foot
        box("EditDesk", (0, 1.6, 0.37), (2.6, 0.8, 0.74), pbr("EditDeskM", (0.08, 0.08, 0.09), 0.4))
        c["mons"] = []
        for k, (x, rz, im) in enumerate(((-0.75, 0.15, foot), (0.0, 0.0, img), (0.75, -0.15, foot))):
            r, s_ = P.lcd_monitor(f"EMon{k}", (x, 1.85, 0.74), rz, P.screen_mat(f"EScr{k}", im, 1.1, cursor=(k != 1), cursor_speed=0.15), w=0.6, h=0.36)
            c["mons"].append(s_)
        box("EKB", (0, 1.4, 0.75), (0.45, 0.15, 0.02), pbr("EKBm", (0.05, 0.05, 0.05), 0.4))
        cyl("Jog", (0.4, 1.4, 0.76), 0.05, 0.03, pbr("JogM", (0.2, 0.2, 0.22), 0.3, 0.8), verts=24)
        B.practical((0.0, 1.0, 1.1), 3, (0.6, 0.75, 1.0), 0.3, "ScreenSpill")
        B.key_spot((-2.0, 0.5, 2.5), (0, 1.0, 1.0), 60, 30, (1.0, 0.65, 0.4), soft=0.2, name="EditPractical")
        j1 = B.person("Journalist1", 0.0, 36, "female_elegantsuit01", "long01", hue=0.6, sat=0.2, val=0.3, hair_val=0.3)
        j2 = B.person("Journalist2", 1.0, 41, "male_casualsuit03", "short04", hue=0.6, sat=0.2, val=0.35, hair_val=0.3)
        B.seat(j1, (-0.35, 0.85, 0), math.pi, lean=8); B.seat(j2, (0.45, 0.8, 0), math.pi + 0.2, lean=12)
        c["j1"], c["j2"] = j1, j2
        c["rest"] = {"j1": B.capture(j1), "j2": B.capture(j2)}
        B.room_haze((0, 0, 1.4), (5.8, 4.8, 2.8), density=0.015)
    B.finish_interior(lift=0.0)
    return c


def anim(c, t, move):
    sec = t * DUR[move]
    v = c["variant"]
    if v == "studio81":
        B.apply_pose(c["pres"], c["rest"]["pres"])
        pres = c["pres"]; fwd = B.fwd_of(pres); side = fwd.cross(Vector((0, 0, 1))).normalized()
        for sd, sg in (("L", -1), ("R", 1)):
            reach(pres, sd, Vector((0.18 * sg, 2.5, 0.88)), Vector((sg * side.x, sg * side.y, -0.8)), fwd + Vector((0, 0, -0.4)))
        fingers_curl(pres, 25); pres.rot("head", (0, 0, 1), 4 * math.sin(sec * 0.6)); B.nod(pres, -2)
        c["studiocam"].location = Vector((-3.4 + 1.6 * ease(t), -1.6, 0))
        for k, (h, hs) in enumerate(c["callers"]):
            B.apply_pose(h, c["rest"][f"c{k}"])
            fwd = B.fwd_of(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
            pick = 0.4 + 0.9 * k
            if sec > pick and hasattr(hs, "matrix_parent_inverse"):
                # handset to the ear (simple: lift it to the head side), the other hand writes
                hd = h.bone_head("head"); ear = hd + side * 0.09 + Vector((0, 0, 0.0))
                if k % 2 == 0:
                    hs.matrix_parent_inverse.identity() if hs.parent is None else None
                reach(h, "L", ear - side * 0.02 + Vector((0, 0, -0.05)), Vector((0, 0, -1)), Vector((0, 0, 1)))
                if hs.parent is not None:
                    mw = hs.matrix_world.copy(); hs.parent = None; hs.matrix_world = mw
                hs.location = ear + Vector((0, 0, -0.02)); hs.rotation_euler = (math.radians(80), 0, math.atan2(fwd.y, fwd.x))
            slip = h.arm.location + fwd * 0.45 + side * 0.15
            reach(h, "R", Vector((slip.x, slip.y, 0.79)) + Vector((0.01 * math.sin(sec * 6 + k), 0, 0)), Vector((0.4, -0.5, -0.8)), fwd + Vector((0, 0, -0.6)))
            fingers_curl(h, 35); B.nod(h, 14)
    elif v == "office07":
        det = c["det"]; B.apply_pose(det, c["rest"]["det"])
        u = ease(min(1.0, max(0.0, (sec - 0.5) / 1.8)))
        f = c["newfile"]; f.location = Vector((0.2, 2.6, 1.25)).lerp(Vector((0.55, 2.91, 1.5)), u)
        reach(det, "R", f.location + Vector((0.08, -0.08, 0.05)), Vector((0.5, -0.6, -0.6)), Vector((0, 1, 0.3)))
        if sec > 2.6:
            reach(det, "R", Vector((0.55, 2.82, 1.62)), Vector((0.5, -0.6, -0.6)), Vector((0, 1, 0)))
        fingers_curl(det, 35); B.nod(det, -4)
    else:
        for k in ("j1", "j2"):
            B.apply_pose(c[k], c["rest"][k])
        j1, j2 = c["j1"], c["j2"]
        for h, ph_ in ((j1, 0.0), (j2, 1.0)):
            fwd = B.fwd_of(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
            for sd, sg in (("L", -1), ("R", 1)):
                k_ = h.bone_tail(f"upperleg02.{sd}")
                reach(h, sd, k_ + Vector((0, 0, 0.06)) + fwd * 0.08, Vector((sg * side.x, sg * side.y, -0.6)), fwd + Vector((0, 0, -0.7)))
            fingers_curl(h, 30)
        fwd = B.fwd_of(j2)
        reach(j2, "R", Vector((0.4, 1.38, 0.82)) + Vector((0.012 * math.sin(sec * 2.0), 0, 0)), Vector((0.5, -0.5, -0.8)), fwd + Vector((0, 0, -0.6)))
        j1.rot("head", (0, 0, 1), 6 * math.sin(sec * 0.4)); B.nod(j1, -3)
    bpy.context.view_layer.update()


def cam(a, b, tgt, lens):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(tgt), lens)


MOVES = {
    "appeal": dict(kind="anim", dof=4.0, cam=cam((2.2, -3.6, 1.7), (1.7, -3.2, 1.68), (0.0, 3.0, 1.25), 40),
                   anim=lambda c, t: anim(c, t, "appeal"), focus=lambda c, t: c["pres"].bone_head("head")),
    "phones": dict(kind="anim", dof=4.0, cam=cam((3.4, -1.6, 1.7), (3.8, -1.3, 1.65), (7.2, 1.3, 0.95), 30),
                   anim=lambda c, t: anim(c, t, "phones"), focus=lambda c, t: Vector((6.3, 1.1, 1.0))),
    "pin": dict(kind="anim", dof=3.2, cam=cam((1.9, -0.6, 1.65), (1.6, -0.2, 1.6), (-0.3, 2.9, 1.45), 30),
                anim=lambda c, t: anim(c, t, "pin"), focus=lambda c, t: Vector((0.3, 2.9, 1.5))),
    "clock": dict(kind="anim", dof=2.4, cam=cam((1.9, -1.9, 0.9), (2.0, 0.4, 1.6), (2.2, 2.93, 2.0), 35),
                  anim=lambda c, t: anim(c, t, "clock"), focus=lambda c, t: Vector((2.2, 2.93, 2.1))),
    "scrub": dict(kind="anim", dof=2.8, cam=cam((1.6, -1.2, 1.55), (1.3, -0.8, 1.5), (0.0, 1.85, 1.0), 32),
                  anim=lambda c, t: anim(c, t, "scrub"), focus=lambda c, t: c["j1"].bone_head("head")),
    "paused": dict(kind="anim", dof=2.4, cam=cam((0.25, -0.2, 1.38), (0.05, 0.1, 1.35), (0.0, 1.85, 1.06), 40),
                   anim=lambda c, t: anim(c, t, "paused"), focus=lambda c, t: Vector((0.0, 1.85, 0.95))),
}
