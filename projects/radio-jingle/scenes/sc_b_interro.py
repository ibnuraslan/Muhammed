"""CH3 (chat B): a 1981 police interrogation room and the station corridor outside it (generic, no crest).
Pale green gloss paint, one hard lamp over the table, a barred high window with grey daylight, cigarette smoke.
The man questioned is unnamed (an acquaintance in the story); he is never shown doing anything but talking.
  question (A, day):   slow push from the corner: two detectives across from a man, a reel recorder turning, smoke curling
  size     (B, day):   the man holds his hands apart to show a size; a detective writes it down (medium)
  retract  (A, night): reverse angle: he shakes his head and pushes the typed statement back across the table
  leave    (B, night): the door opens; he walks out down the dim corridor
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from common import world_flat, ease
from human import reach, fingers_curl
import ph
import b_common as B
import b_props as P

EXPOSURE = 0.3
DUR = {"question": 5.5, "size": 5.0, "retract": 5.0, "leave": 6.0}
VARIANT_FOR = {"question": "day", "size": "day", "retract": "night", "leave": "night"}
TOP = 0.8
TABLE = Vector((0.0, 0.3, 0))


def person81(role, name, fallback):
    """1981 figures from chat A's kit when available (consistent clothes), else our own."""
    try:
        import rj
        return rj.person(role, name)
    except Exception as e:
        print("[interro] rj.person unavailable:", e)
        return B.person(name, *fallback)


def build(variant=None):
    variant = variant or "day"
    c = {"variant": variant}
    rng = np.random.default_rng(3)
    world_flat((0.008, 0.01, 0.013), 1.0)
    paint = pbr("GreenGloss", (0.32, 0.4, 0.34), 0.35, **{'Coat Weight': 0.2})
    upper = B.plaster("Cream", (0.62, 0.6, 0.52), dirt=0.2)
    floor = B.tex_mat("Lino", "old_linoleum_flooring_01", scale=0.7, tint=(0.7, 0.66, 0.6))
    box("Floor", (0, 0, -0.01), (4.4, 4.0, 0.02), floor)
    for nm, loc, size in (("WallB", (0, 2.0, 1.4), (4.4, 0.1, 2.8)), ("WallL", (-2.2, 0, 1.4), (0.1, 4.0, 2.8))):
        box(nm + "lo", (loc[0], loc[1], 0.75), (size[0], size[1], 1.5), paint)
        box(nm + "hi", (loc[0], loc[1], 2.15), (size[0], size[1], 1.3), upper)
    # right wall with the door (open in "leave"), front wall
    box("WallR_a", (2.2, -1.25, 1.4), (0.1, 1.5, 2.8), upper); box("WallR_b", (2.2, 1.3, 1.4), (0.1, 1.4, 2.8), upper)
    box("WallR_top", (2.2, 0.05, 2.45), (0.1, 1.1, 0.7), upper)
    box("WallF", (0, -2.0, 1.4), (4.4, 0.1, 2.8), upper)
    box("Ceil", (0, 0, 2.82), (4.4, 4.0, 0.04), B.plaster("CeilI", (0.5, 0.5, 0.46)))
    door_m = pbr("DoorBrown", (0.18, 0.11, 0.06), 0.45)
    door = box("Door", (0, 0.45, 1.05), (0.04, 0.9, 2.1), door_m, bevel=0.005)
    knob = cyl("Knob", (-0.04, 0.8, 1.0), 0.025, 0.06, pbr("Brass", (0.6, 0.45, 0.2), 0.3, 1.0), verts=16, rot=(0, math.radians(90), 0))
    hinge = bpy.data.objects.new("DoorHinge", None); bpy.context.collection.objects.link(hinge); hinge.location = (2.2, -0.5, 0)
    door.parent = hinge; knob.parent = hinge
    c["door"] = hinge
    # high barred window in the back wall
    box("WinHole", (1.0, 2.0, 2.2), (1.0, 0.12, 0.6), emissive("Grey", (0.7, 0.75, 0.8), 1.4 if variant == "day" else 0.08))
    for k in range(5):
        box("Bar", (0.6 + k * 0.2, 1.93, 2.2), (0.02, 0.02, 0.6), pbr("BarSteel", (0.1, 0.1, 0.1), 0.4, 0.8))
    # corridor outside the door (x 2.2..6)
    box("CorFloor", (4.2, 0, -0.01), (4.0, 2.2, 0.02), floor)
    box("CorWallN", (4.2, 1.1, 1.4), (4.0, 0.1, 2.8), paint); box("CorWallS", (4.2, -1.1, 1.4), (4.0, 0.1, 2.8), paint)
    box("CorCeil", (4.2, 0, 2.82), (4.0, 2.2, 0.04), B.plaster("CorC", (0.45, 0.45, 0.42)))
    box("CorEnd", (6.2, 0, 1.4), (0.1, 2.2, 2.8), upper)
    for x in (3.5, 5.3):
        box("CorTube", (x, 0, 2.78), (1.2, 0.12, 0.04), emissive("Tube", (0.85, 0.95, 0.9), 2.0 if variant == "night" else 0.5))
        l = area_light((x, 0, 2.7), (0, 0, 0), 1.0, 25 if variant == "night" else 8, (0.8, 0.95, 0.88)); l.visible_camera = False
    # ------------------------------------------------------------------ table, chairs, recorder, ashtray
    ph.model("wooden_table_02", loc=tuple(TABLE), rot_z=0)
    for (x, y, fz) in ((-0.3, -0.35, 0.0), (0.35, -0.35, 0.0), (0.0, 0.98, math.pi)):
        ph.model("dining_chair_02", loc=(x, y - 0.0, 0), rot_z=fz + math.pi)
    rec = P.reel_recorder("PoliceRec", (-0.32, 0.38, TOP), rot_z=0.15, spin=0.3, scale=0.9)
    c["rec"] = rec
    ash = cyl("Ashtray", (0.38, 0.22, TOP + 0.012), 0.06, 0.025, glass("AshGlass", (0.8, 0.85, 0.8), 0.1), verts=24)
    cig = cyl("Cig", (0.4, 0.24, TOP + 0.03), 0.004, 0.06, pbr("CigPaper", (0.9, 0.88, 0.82), 0.7), verts=8, rot=(0, math.radians(80), 0.4))
    c["smoke"] = B.smoke((0.42, 0.25, TOP + 0.04), density=0.5, size=(0.3, 0.3, 1.2))
    paper = B.paper_mat("Typed", (0.88, 0.87, 0.82), seed=2)
    c["statement"] = B.sheet("Statement", (0.05, 0.25, TOP + 0.003), (0.21, 0.297), paper, rot=(0, 0, 0.1))
    c["pad"] = B.sheet("Notepad", (0.32, -0.02, TOP + 0.003), (0.15, 0.21), paper, rot=(0, 0, -0.2))
    pen = cyl("Pen", (0, 0, 0), 0.004, 0.14, pbr("PenBlk", (0.02, 0.02, 0.02), 0.3), verts=8)
    c["pen"] = pen
    # the lamp: one hard key from above
    ph.model("hanging_industrial_lamp", loc=(0.0, 0.3, 2.8), rot_z=0)
    B.key_spot((0.0, 0.3, 1.38), (0.0, 0.3, 0.0), 500 if variant == "day" else 600, 80, (1.0, 0.8, 0.56), soft=0.05, blend=0.3, name="TableLamp")
    if variant == "day":
        B.key_spot((1.0, 2.3, 2.2), (-0.4, -0.6, 0.6), 160, 30, (0.7, 0.8, 0.95), soft=0.3, name="WinLight")
    B.fill((-1.8, -1.6, 2.0), (0, 0.3, 1.0), 40, 1.5, (0.4, 0.55, 0.75))
    B.room_haze((1.8, 0, 1.4), (8.4, 4.0, 2.8), density=0.01, color=(0.92, 0.92, 0.9))
    # ------------------------------------------------------------------ people
    d1 = B.person("Det1", 1.0, 46, "male_casualsuit05", "short02", hue=0.08, sat=0.35, val=0.45, hair_val=0.5)
    d2 = person81("detective", "Det2", (1.0, 38, "male_elegantsuit01", "short04")) if False else B.person("Det2", 1.0, 36, "male_elegantsuit01", "short04", hue=0.08, sat=0.25, val=0.35, hair_val=0.3)
    man = B.person("Questioned", 1.0, 33, "male_casualsuit03", "short01", hue=0.55, sat=0.3, val=0.5, hair_val=0.6)
    B.seat(d1, (-0.3, -0.42, 0), math.pi, lean=10)      # face +Y, across the table
    B.seat(d2, (0.35, -0.42, 0), math.pi, lean=14)
    B.seat(man, (0.0, 1.05, 0), 0.0, lean=8)            # faces -Y
    c["d1"], c["d2"], c["man"] = d1, d2, man
    c["rest"] = {k: B.capture(c[k]) for k in ("d1", "d2", "man")}
    if variant == "night":
        P0 = c["rest"]["man"]
        B.stand(man, (3.0, 0.0, 0), math.pi / 2); c["walkpose"] = B.capture(man)   # for the corridor walk
        B.apply_pose(man, P0)
        coat = box("Coat", (0, 0, 0), (0.06, 0.32, 0.55), fabric("CoatFab", (0.12, 0.1, 0.08), 0.9, 0.3, 300), bevel=0.02)
        coat.location = (0, 0, -30); c["coat"] = coat
    return c


def hands_on_table(h, sec, ph_=0.0, spread=0.16, fwd_d=0.4, lift=0.0):
    fwd = B.fwd_of(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
    sh = h.bone_head("spine01")
    base = Vector((sh.x, sh.y, TOP + 0.05 + lift)) + fwd * fwd_d
    for sd, sg in (("L", -1), ("R", 1)):
        reach(h, sd, base + side * (spread * sg) + Vector((0, 0, 0.004 * math.sin(sec + ph_))), Vector((sg * side.x, sg * side.y, -0.8)), fwd + Vector((0, 0, -0.3)))
    fingers_curl(h, 30, thumb=10)


def write_hand(c, h, sec):
    fwd = B.fwd_of(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
    pad = c["pad"].location
    tip = pad + Vector((0.03 * math.sin(sec * 5.0), -0.03 + 0.01 * math.sin(sec * 1.3), 0.01))
    reach(h, "R", tip + Vector((0.04, -0.05, 0.06)), Vector((0.6, -0.4, -0.6)), fwd + Vector((0, 0, -0.7)))
    reach(h, "L", pad + Vector((-0.2, -0.06, 0.05)), Vector((-0.6, -0.4, -0.6)), fwd + Vector((0, 0, -0.5)))
    fingers_curl(h, 40, thumb=25)
    pen = c["pen"]; w = h.bone_tail("wrist.R")
    pen.location = (w + tip) * 0.5 + Vector((0, 0, 0.02)); d = (tip - w)
    pen.rotation_mode = 'QUATERNION'; pen.rotation_quaternion = d.to_track_quat('Z', 'Y')
    h.rot("head", (1, 0, 0), 18)


def anim(c, t, move):
    sec = t * DUR[move]
    for k in ("d1", "d2", "man"):
        B.apply_pose(c[k], c["rest"][k])
    d1, d2, man = c["d1"], c["d2"], c["man"]
    c["door"].rotation_euler = (0, 0, 0)
    if move in ("question", "size"):
        hands_on_table(d1, sec, 0.0, fwd_d=0.42)
        d1.rot("head", (0, 0, 1), 4 * math.sin(sec * 0.4))
        if move == "size":
            write_hand(c, d2, sec)
            # the man shows a size with his hands apart, at chest height, then lowers them a little
            fwd = B.fwd_of(man); side = fwd.cross(Vector((0, 0, 1))).normalized()
            open_ = 0.18 + 0.2 * ease(min(1.0, max(0.0, (sec - 0.6) / 1.2)))
            chest = man.bone_head("neck01") + fwd * 0.38 + Vector((0, 0, -0.3 - 0.04 * ease(max(0.0, (sec - 3.6) / 1.0))))
            for sd, sg in (("L", -1), ("R", 1)):
                reach(man, sd, chest + side * (open_ * sg), Vector((sg * side.x, sg * side.y, -0.6)), Vector((0, 0, 1)) - side * 0.6 * sg)
            fingers_curl(man, 12, thumb=5)
            man.rot("head", (0, 0, 1), 5 * math.sin(sec * 0.9))
        else:
            hands_on_table(d2, sec, 1.0, fwd_d=0.4)
            hands_on_table(man, sec, 2.0, fwd_d=0.36, spread=0.12)
            man.rot("head", (1, 0, 0), 8 + 3 * math.sin(sec * 0.8))
    elif move == "retract":
        hands_on_table(d1, sec, 0.0, fwd_d=0.42); hands_on_table(d2, sec, 1.0, fwd_d=0.4)
        d1.rot("head", (1, 0, 0), 6)
        u = ease(min(1.0, max(0.0, (sec - 1.6) / 1.4)))
        st = c["statement"]; st.location = Vector((0.03, 0.6, TOP + 0.003)).lerp(Vector((0.05, 0.12, TOP + 0.003)), u)
        fwd = B.fwd_of(man); side = fwd.cross(Vector((0, 0, 1))).normalized()
        reach(man, "R", st.location + Vector((0.05, 0.12, 0.05)), Vector((0.6, 0.3, -0.7)), fwd + Vector((0, 0, -0.6)))
        reach(man, "L", man.bone_head("spine01") + fwd * 0.35 + side * -0.14 + Vector((0, 0, TOP - man.bone_head("spine01").z + 0.05)), Vector((-0.6, 0.3, -0.7)), fwd + Vector((0, 0, -0.4)))
        fingers_curl(man, 20, thumb=10)
        man.rot("head", (0, 0, 1), 15 * math.sin(sec * 3.4) * (1 if sec < 1.6 or sec > 3.3 else 0.3))
    elif move == "leave":
        B.hide_person(d1); B.hide_person(d2)
        c["door"].rotation_euler = (0, 0, math.radians(-95) * ease(min(1.0, sec / 1.2)))
        u = ease(min(1.0, max(0.0, (sec - 0.6) / (DUR["leave"] - 0.6))))
        B.walk_to(man, (2.55, 0.0, 0), (5.6, 0.05, 0), u, 4.2 * u, stride=22, swing=6)
        fwd = B.fwd_of(man)
        man.rot("head", (1, 0, 0), 10)
    bpy.context.view_layer.update()


def cam(a, b, tgt, lens):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(tgt), lens)


MOVES = {
    "question": dict(kind="anim", dof=2.8, cam=cam((-1.9, -1.75, 1.85), (-1.55, -1.35, 1.7), (0.05, 0.4, 1.0), 30),
                     anim=lambda c, t: anim(c, t, "question"), focus=lambda c, t: c["man"].bone_head("head")),
    "size": dict(kind="anim", dof=2.4, cam=cam((1.65, -1.2, 1.45), (1.45, -0.95, 1.4), (0.0, 0.7, 1.1), 40),
                 anim=lambda c, t: anim(c, t, "size"), focus=lambda c, t: c["man"].bone_head("spine02")),
    "retract": dict(kind="anim", dof=2.8, cam=cam((-1.5, 1.75, 1.75), (-1.3, 1.5, 1.68), (0.2, -0.2, 0.95), 32),
                    anim=lambda c, t: anim(c, t, "retract"), focus=lambda c, t: c["statement"].location),
    "leave": dict(kind="anim", dof=4.0, cam=cam((0.5, -0.15, 1.6), (0.95, -0.05, 1.6), (5.0, 0.05, 1.2), 30),
                  anim=lambda c, t: anim(c, t, "leave"), focus=lambda c, t: c["man"].bone_head("spine03")),
}
