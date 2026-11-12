"""CH4/CH5 (chat B): Michael's study / music room, 2008-2013 (the brother, now a music teacher in his forties;
unnamed figure, no likeness). Desk stacked with case binders under a lamp, an upright piano on the side wall,
a window with grey overcast light (day) or blue night.
  read     (A, day):   slow push as he reads at the desk among binders, turning a page
  lookup   (B, day):   he stops and looks back toward the piano in the dark; slow push past the piano
  replay   (A, night): headphones on, he replays the tape on a laptop; the waveform loops; slow push
  objection(B, night): he types his objections; a printer feeds pages into the lamplight
  notes    (A, music): he plays a few notes on the piano and stops; the room goes still; slow push
  window   (B, music_night): night; he sits on the piano bench facing the dark window; the camera creeps in
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

EXPOSURE = 0.2
DUR = {"read": 5.5, "lookup": 5.0, "replay": 5.5, "objection": 5.0, "notes": 6.0, "window": 6.5}
VARIANT_FOR = {"read": "day", "lookup": "day", "replay": "night", "objection": "night", "notes": "music", "window": "music_night"}
DESK = Vector((1.2, 1.78, 0))
TOP = 0.8
PIANO_X = -1.9


def binder(name, loc, rot_z, col, upright=False):
    m = pbr(name + "Cov", col, 0.55)
    lab = pbr("SpineLabel", (0.9, 0.9, 0.86), 0.7)
    if upright:
        b = box(name, (0, 0, 0.16), (0.07, 0.29, 0.32), m, bevel=0.004)
        l = box(name + "L", (-0.036, 0, 0.2), (0.002, 0.05, 0.12), lab)
    else:
        b = box(name, (0, 0, 0.03), (0.31, 0.29, 0.06), m, bevel=0.004)
        l = box(name + "L", (-0.156, 0, 0.035), (0.002, 0.06, 0.04), lab)
    o = join([b, l], name); o.location = loc; o.rotation_euler = (0, 0, rot_z)
    return o


def build(variant=None):
    variant = variant or "day"
    night = variant in ("night", "music_night")
    c = {"variant": variant}
    rng = np.random.default_rng(45)
    world_flat((0.006, 0.008, 0.012), 1.0)
    floor = B.tex_mat("Parquet", "herringbone_parquet", scale=0.5, tint=(0.75, 0.62, 0.5))
    box("Floor", (0, 0, -0.01), (5.2, 4.6, 0.02), floor)
    wall = B.plaster("WallM", (0.55, 0.53, 0.48), dirt=0.1)
    box("WallB", (0, 2.3, 1.35), (5.2, 0.1, 2.7), wall); box("WallL", (-2.6, 0, 1.35), (0.1, 4.6, 2.7), wall)
    box("WallF", (0, -2.3, 1.35), (5.2, 0.1, 2.7), wall); box("Ceil", (0, 0, 2.72), (5.2, 4.6, 0.04), B.plaster("CeilM", (0.5, 0.5, 0.48)))
    # right wall with a tall window
    box("WallR_a", (2.6, -1.4, 1.35), (0.1, 1.8, 2.7), wall); box("WallR_b", (2.6, 1.95, 1.35), (0.1, 0.7, 2.7), wall)
    box("WallR_lo", (2.6, 0.25, 0.4), (0.1, 1.9, 0.8), wall); box("WallR_hi", (2.6, 0.25, 2.5), (0.1, 1.9, 0.4), wall)
    fr = pbr("Frame", (0.85, 0.85, 0.83), 0.5)
    box("WinMull", (2.6, 0.25, 1.55), (0.06, 0.05, 1.5), fr); box("WinTrans", (2.6, 0.25, 1.55), (0.06, 1.9, 0.05), fr)
    out_col, out_s = ((0.2, 0.3, 0.5), 0.2) if night else ((0.75, 0.8, 0.85), 0.45)
    sky = box("Outside", (4.5, 0.25, 1.5), (0.05, 6, 4), emissive("OutM", out_col, out_s)); sky.visible_shadow = False
    if night:
        B.key_spot((4.0, 0.0, 2.2), (-1.2, 0.45, 1.0), 700, 30, (0.45, 0.58, 0.95), soft=0.4, name="Moon")
    else:
        B.key_spot((4.2, -0.3, 2.0), (0.2, 0.8, 0.8), 1600, 30, (0.85, 0.9, 1.0), soft=0.6, name="WinDay")
    B.fill((-2.0, -1.8, 2.0), (0.5, 0.8, 1.0), 10 if night else 25, 1.5, (0.4, 0.5, 0.7))
    B.room_haze((0, 0, 1.35), (5.0, 4.4, 2.6), density=0.012, color=(0.9, 0.92, 0.95))
    # ------------------------------------------------------------------ desk, binders, lamp, laptop, printer
    ph.model("wooden_table_02", loc=tuple(DESK), rot_z=0)
    ph.model("dining_chair_02", loc=(DESK.x, DESK.y - 0.62, 0), rot_z=math.pi)
    cols = [(0.05, 0.07, 0.12), (0.16, 0.05, 0.04), (0.06, 0.06, 0.06), (0.07, 0.1, 0.07), (0.2, 0.17, 0.1)]
    for sx, n in ((-0.38, 6), (0.4, 5)):
        for k in range(n):
            binder(f"Bn{sx}{k}", (DESK.x + sx + rng.uniform(-0.02, 0.02), DESK.y + 0.12, TOP + k * 0.062), rng.uniform(-0.1, 0.1), cols[(k + n) % 5])
    for k in range(9):                                            # a row of binders on the floor along the wall
        binder(f"BnF{k}", (DESK.x - 1.0 + k * 0.08, 2.05, 0.0), 0.0, cols[k % 5], upright=True)
    for k in range(4):
        binder(f"BnF2{k}", (DESK.x + 0.75, 1.3, k * 0.072), 0.3 + rng.uniform(-0.1, 0.1), cols[k % 5])
    ph.model("desk_lamp_arm_01", loc=(DESK.x - 0.5, DESK.y + 0.2, TOP), rot_z=math.radians(-30))
    B.key_spot((DESK.x - 0.3, DESK.y + 0.05, TOP + 0.6), (DESK.x, DESK.y - 0.2, TOP), 160, 70, (1.0, 0.75, 0.5), soft=0.04, name="DeskLamp")
    paper = B.paper_mat("FilePage", (0.88, 0.87, 0.82))
    c["open"] = box("OpenBinder", (DESK.x, DESK.y - 0.12, TOP + 0.012), (0.46, 0.31, 0.022), pbr("OpenCov", (0.08, 0.12, 0.25), 0.55), bevel=0.003)
    c["page"] = B.sheet("FPage", (0, 0, -20), (0.21, 0.297), paper)
    B.sheet("FPageL", (DESK.x - 0.11, DESK.y - 0.12, TOP + 0.024), (0.21, 0.297), paper)
    B.sheet("FPageR", (DESK.x + 0.11, DESK.y - 0.12, TOP + 0.024), (0.21, 0.297), paper)
    if variant == "night":
        hide = [o for o in bpy.data.objects if o.name.startswith(("OpenBinder", "FPage"))]
        for o in hide:
            o.location.z -= 30
        lm = pbr("LapBody", (0.12, 0.12, 0.13), 0.35, 0.5)
        base = box("LapBase", (DESK.x + 0.0, DESK.y - 0.15, TOP + 0.012), (0.34, 0.24, 0.022), lm, bevel=0.004)
        wf = P.waveform_image(f"{B.GEN}/b_wave_laptop.png", segments=1, seed=33)
        lid = box("LapLid", (DESK.x, DESK.y - 0.02, TOP + 0.13), (0.34, 0.012, 0.22), lm, bevel=0.004, rot=(math.radians(-12), 0, 0))
        scr = B.sheet("LapScr", (DESK.x, DESK.y - 0.03, TOP + 0.13), (0.31, 0.19), P.screen_mat("LapWave", wf, 1.4, cursor_speed=0.2, cursor_start=0.1),
                      rot=(math.radians(90 - 12), 0, 0))
        # printer at the right of the desk feeding pages (frame driver: a sheet slides out every 2 s)
        pr = box("Printer", (DESK.x + 0.42, DESK.y + 0.05, TOP + 0.1), (0.4, 0.32, 0.2), pbr("PrinterGrey", (0.5, 0.5, 0.52), 0.4), bevel=0.01)
        c["sheets"] = []
        for k in range(3):
            sh = B.sheet(f"PrintSheet{k}", (0, 0, 0), (0.21, 0.297), paper)
            c["sheets"].append(sh)
        B.practical((DESK.x + 0.0, DESK.y - 0.25, TOP + 0.25), 3, (0.6, 0.85, 0.7), 0.15, "ScreenGlow")
    # ------------------------------------------------------------------ the piano
    try:
        import rj
        pn = rj.upright_piano("MPiano")
        c["piano"] = pn
        root = pn["root"]; root.location = (PIANO_X, 0.4, 0); root.rotation_euler = (0, 0, math.pi / 2)
        if pn.get("bench") is not None:
            pn["bench"].location = (PIANO_X + 0.55, 0.4, 0) if pn["bench"].parent is None else pn["bench"].location
        keys_z = pn.get("keys_z", 0.74)
    except Exception as e:
        print("[michael] rj piano unavailable:", e)
        pw = pbr("PianoBlack", (0.015, 0.013, 0.012), 0.15, **{'Coat Weight': 0.8})
        box("PianoCase", (PIANO_X - 0.3, 0.4, 0.62), (0.6, 1.48, 1.25), pw, bevel=0.012)
        box("PianoKeybed", (PIANO_X + 0.13, 0.4, 0.7), (0.32, 1.42, 0.06), pw)
        box("PianoKeys", (PIANO_X + 0.15, 0.4, 0.735), (0.15, 1.36, 0.02), pbr("Ivory", (0.85, 0.82, 0.74), 0.3))
        box("PianoBench", (PIANO_X + 0.6, 0.4, 0.25), (0.35, 0.8, 0.5), pw, bevel=0.01)
        keys_z = 0.745
    c["keys_z"] = keys_z
    ph.model("wooden_bookshelf_worn", loc=(-2.25, -1.4, 0), rot_z=math.radians(90))
    for k in range(2):
        ph.model("book_encyclopedia_set_01", loc=(-2.2, -1.65 + k * 0.55, 1.02 + 0.0 * k), rot_z=math.radians(90))
    ph.model("potted_plant_01", loc=(2.2, 1.5, 0), rot_z=1.0)
    # ------------------------------------------------------------------ Michael (forties, navy jumper)
    h = B.michael("Michael", 47)
    if variant in ("music", "music_night"):
        if variant == "music":
            B.seat(h, (PIANO_X + 0.62, 0.42, 0), -math.pi / 2, lean=8)         # faces -X, the keys
        else:
            B.seat(h, (PIANO_X + 0.62, 0.42, 0), math.pi / 2 + 0.25, lean=14)  # turned on the bench toward the window
    else:
        B.seat(h, (DESK.x, DESK.y - 0.68, 0), math.pi, lean=12)
    c["m"] = h
    if variant == "night":
        c["phones"] = P.headphones(h)
        # lamp bounce off the wall onto his face and greying hair (continuity: he must read grey at night too)
        B.key_spot((DESK.x - 0.9, DESK.y + 0.6, 1.9), (DESK.x, DESK.y - 0.68, 1.25), 170, 60, (1.0, 0.8, 0.6), soft=0.5, name="HairBounce")
        B.key_spot((DESK.x + 1.3, DESK.y - 0.2, 2.0), (DESK.x, DESK.y - 0.68, 1.3), 110, 50, (1.0, 0.82, 0.62), soft=0.6, name="HairBounceR")
    if variant == "day":                                      # soft room-side fill so his greying hair reads against the window
        B.key_spot((DESK.x - 1.8, DESK.y - 0.9, 2.1), (DESK.x, DESK.y - 0.68, 1.3), 120, 50, (0.95, 0.92, 0.88), soft=0.6, name="HairFill")
    c["rest"] = B.capture(h)
    B.finish_interior(lift=0.4 if variant in ("day", "music") else 0.0)   # day must read (hub luminance rule)
    return c


def turn_page(c, h, sec, at=1.4):
    base = c["open"].location + Vector((0, 0, 0.014))
    u = ease(min(1.0, max(0.0, (sec - at) / 1.2)))
    pg = c["page"]
    pg.rotation_mode = 'XYZ'; pg.rotation_euler = (0, -math.pi * u, 0)
    pg.location = base + Vector((0.11 * math.cos(math.pi * u), 0, 0.11 * math.sin(math.pi * u) + 0.012))
    tip = base + Vector((0.2 * math.cos(math.pi * u), -0.1, 0.05 + 0.1 * math.sin(math.pi * u)))
    fwd = B.fwd_of(h)
    reach(h, "R", tip, Vector((0.6, -0.4, -0.6)), fwd + Vector((0, 0, -0.6)))
    reach(h, "L", base + Vector((-0.2, -0.12, 0.05)), Vector((-0.6, -0.4, -0.6)), fwd + Vector((0, 0, -0.6)))
    B.curl(h, 25, thumb=10)


def type_hands(h, sec, kb):
    fwd = B.fwd_of(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
    for sd, sg in (("L", -1), ("R", 1)):
        tap = 0.006 * max(0.0, math.sin(sec * 18 + (0 if sd == "L" else 1.9)))
        reach(h, sd, kb + side * (0.08 * sg) - fwd * 0.04 + Vector((0, 0, 0.05 - tap)), Vector((sg * side.x, sg * side.y, -0.7)), fwd + Vector((0, 0, -0.4)))
    B.curl(h, 35, thumb=10)


def anim(c, t, move):
    sec = t * DUR[move]
    h = c["m"]; B.apply_pose(h, c["rest"])
    for o in c.get("phones", []):
        o.hide_render = (move == "objection")                 # typing: headphones off, his grey hair visible
    if move == "read":
        turn_page(c, h, sec); B.nod(h, 20)
    elif move == "lookup":
        turn_page(c, h, 0.0, at=99)
        u = ease(min(1.0, max(0.0, (sec - 1.0) / 1.6)))
        B.nod(h, 20 * (1 - u)); h.rot("neck01", (0, 0, 1), 30 * u); h.rot("head", (0, 0, 1), 25 * u)
        h.rot("spine03", (0, 0, 1), 10 * u)
    elif move in ("replay", "objection"):
        kb = Vector((DESK.x, DESK.y - 0.2, TOP + 0.03))
        if move == "replay":
            fwd = B.fwd_of(h)
            reach(h, "R", kb + Vector((0.12, -0.02, 0.04)), Vector((0.6, -0.4, -0.6)), fwd + Vector((0, 0, -0.5)))
            reach(h, "L", kb + Vector((-0.18, -0.08, 0.04)), Vector((-0.6, -0.4, -0.6)), fwd + Vector((0, 0, -0.5)))
            B.curl(h, 30); B.nod(h, 10 + 4 * math.sin(sec * 0.6))
        else:
            type_hands(h, sec, kb); B.nod(h, 12)
        for k, sh in enumerate(c.get("sheets", [])):
            ph_ = ((sec + k * 2.0) % 6.0) / 2.0                        # each sheet: 2 s feeding out, then rests
            u = min(1.0, ph_)
            p0 = Vector((DESK.x + 0.42, DESK.y + 0.02, TOP + 0.19)); p1 = Vector((DESK.x + 0.42, DESK.y - 0.28, TOP + 0.12))
            sh.location = p0.lerp(p1, u) + Vector((0, 0, 0.002 * k)); sh.rotation_euler = (math.radians(-14 * (1 - u)), 0, 0)
    elif move == "notes":
        fwd = B.fwd_of(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
        kz = c["keys_z"] + 0.04
        play = 1.0 if sec < 2.4 else 0.0
        keys = Vector((PIANO_X - 0.05, 0.42, kz))
        for sd, sg in (("L", -1), ("R", 1)):
            press = 0.012 * max(0.0, math.sin(sec * 7 + sg)) * play
            lift = 0.0 if play else 0.06 * ease(min(1.0, (sec - 2.4) / 0.8))
            reach(h, sd, keys + side * (0.18 * sg + 0.02 * math.sin(sec * 1.5) * play) + Vector((0, 0, -press + lift)), Vector((sg * side.x, sg * side.y, -0.7)), fwd + Vector((0, 0, -0.5)))
        B.curl(h, 25, thumb=10)
        B.nod(h, 12 + (8 * ease(min(1.0, max(0.0, (sec - 2.6) / 1.5)))))
    elif move == "window":
        fwd = B.fwd_of(h); side = fwd.cross(Vector((0, 0, 1))).normalized()
        knee = h.bone_tail("upperleg02.L")
        for sd, sg in (("L", -1), ("R", 1)):
            k = h.bone_tail(f"upperleg02.{sd}")
            reach(h, sd, k + Vector((0, 0, 0.05)) + fwd * 0.05, Vector((sg * side.x, sg * side.y, -0.6)), fwd + Vector((0, 0, -0.7)))
        B.curl(h, 30)
        B.nod(h, 6 + 2 * math.sin(sec * 0.3))
    bpy.context.view_layer.update()


def cam(a, b, tgt, lens):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(tgt), lens)


MOVES = {
    "read": dict(kind="anim", dof=2.4, cam=cam((2.35, -0.45, 1.55), (2.15, -0.05, 1.48), (1.1, 1.5, 1.0), 32),
                 anim=lambda c, t: anim(c, t, "read"), focus=lambda c, t: c["m"].bone_head("head")),
    "lookup": dict(kind="anim", dof=2.4, cam=cam((-1.45, 0.95, 1.3), (-1.2, 0.95, 1.28), (1.2, 1.15, 1.15), 40),
                   anim=lambda c, t: anim(c, t, "lookup"), focus=lambda c, t: c["m"].bone_head("head")),
    "replay": dict(kind="anim", dof=2.4, cam=cam((2.3, 0.3, 1.45), (2.15, 0.6, 1.4), (1.1, 1.3, 1.15), 35),
                   anim=lambda c, t: anim(c, t, "replay"), focus=lambda c, t: c["m"].bone_head("head")),
    "objection": dict(kind="anim", dof=2.8, cam=cam((0.05, 0.35, 1.5), (0.3, 0.55, 1.46), (1.45, 1.65, 0.98), 32),
                      anim=lambda c, t: anim(c, t, "objection"), focus=lambda c, t: Vector((DESK.x + 0.42, DESK.y - 0.2, TOP + 0.1))),
    "notes": dict(kind="anim", dof=2.8, cam=cam((0.6, -1.4, 1.45), (0.2, -0.9, 1.4), (PIANO_X, 0.4, 1.0), 35),
                  anim=lambda c, t: anim(c, t, "notes"), focus=lambda c, t: c["m"].bone_head("head")),
    "window": dict(kind="anim", dof=2.8, cam=cam((-0.3, -1.5, 1.4), (-0.45, -1.1, 1.36), (-0.9, 0.7, 1.0), 35),
                   anim=lambda c, t: anim(c, t, "window"), focus=lambda c, t: c["m"].bone_head("head")),
}
