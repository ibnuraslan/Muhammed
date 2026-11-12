"""COURT: a Paris criminal tribunal, February 2015 (dramatization, generic room, no emblem). Oak panelling, a raised
bench for three judges in black robes, the prosecutor's desk raised on the left, a glass dock on the right,
defence benches in front of it, public benches, tall windows with grey winter light.
  aisle     (ch4 1A, title): slow push down the aisle as people take their seats
  dock      (ch4 1B): a defendant stands in the glass dock, seen in profile, as the clerk reads
  prosecutor(ch4 3A): the prosecutor stands and speaks toward the bench, seen across the room
  file      (ch4 3B): a lawyer passes a file along the defence bench while the defendants watch (wide)
  ashamed   (ch4 4A): slow push on a man standing alone in the dock, head bowed
  reverse   (ch4 4B): from behind the dock: the public benches, faces turned toward him
  judges    (ch4 5A): the judges file in to the bench as the room rises
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import dd
from dd import person, place, face_to, walk_to, arms_relaxed, zero, ground
from human import pose_sit, pose_walk, reach, fingers_curl

EXPOSURE = -0.3
DUR = {k: 9.0 for k in ("aisle", "dock", "prosecutor", "file", "ashamed", "reverse", "judges")}
VARIANT_FOR = {k: k for k in DUR}
BENCH_Y = 17.0
DOCK = (4.6, 6.6, 9.0, 13.5)      # x0, x1, y0, y1 of the glass dock


def room():
    oak = dd.tex_mat("oak_veneer_01", 1.2, tint=(0.85, 0.75, 0.62), name="CourtOak", sat=0.8, coat=0.25)
    dark = dd.tex_mat("walnut_veneer", 1.2, tint=(0.7, 0.62, 0.55), name="CourtDark", sat=0.8, coat=0.3)
    panel = dd.tex_mat("wooden_panels", 0.5, tint=(0.8, 0.7, 0.58), name="CourtPanel", sat=0.8)
    plaster = pbr("CourtPlaster", (0.68, 0.66, 0.6), 0.85)
    B = dd.Builder("Courtroom")
    B.box((0, 10, -0.05), (14, 22, 0.1), dd.tex_mat("herringbone_parquet", 0.5, tint=(0.75, 0.68, 0.6), name="Parquet", sat=0.7))
    B.box((0, 20.6, 4), (14, 0.2, 8), panel).box((-7.1, 10, 4), (0.2, 22, 8), plaster).box((0, -0.6, 4), (14, 0.2, 8), plaster)
    B.box((0, 10, 8.1), (14, 22, 0.2), pbr("CourtCeil", (0.72, 0.7, 0.66), 0.85))
    B.box((-7.0, 10, 1.1), (0.1, 22, 2.2), panel)                     # wainscot
    for y in np.arange(0.5, 20, 1.6):
        B.box((-6.95, y, 1.1), (0.03, 0.05, 2.2), dark)
    for k in range(6):                                               # right wall: tall windows
        B.box((7.1, -0.2 + k * 3.6, 4), (0.2, 1.2, 8), plaster)
    B.box((7.1, 10, 0.9), (0.2, 22, 1.8), oak).box((7.1, 10, 7.4), (0.2, 22, 1.2), plaster)
    # bench on a dais, the clerk's desk, the prosecutor's raised desk
    B.box((0, BENCH_Y + 1.0, 0.25), (9, 3.0, 0.5), oak)
    B.box((0, BENCH_Y, 1.05), (7.5, 0.9, 1.1), dark).box((0, BENCH_Y, 1.62), (7.7, 1.0, 0.05), oak)
    for x in (-1.6, 0, 1.6):
        B.box((x, BENCH_Y + 0.9, 1.35), (0.7, 0.6, 1.7), pbr("JudgeLeather", (0.16, 0.035, 0.03), 0.4, 0.0, **{"Coat Weight": 0.3}))
    B.box((-2.8, BENCH_Y - 2.0, 0.55), (2.6, 0.8, 1.1), dark)          # clerk
    B.box((-5.3, 13.5, 0.2), (2.4, 3.0, 0.4), oak).box((-4.6, 13.5, 0.95), (0.8, 2.6, 1.1), dark)   # prosecutor
    # the glass dock: oak base, glass walls
    x0, x1, y0, y1 = DOCK
    B.box(((x0 + x1) / 2, (y0 + y1) / 2, 0.15), (x1 - x0, y1 - y0, 0.3), oak)
    B.box((x0, (y0 + y1) / 2, 0.75), (0.1, y1 - y0, 0.9), dark)
    B.box(((x0 + x1) / 2, (y0 + y1) / 2, 0.45), (1.6, y1 - y0 - 0.4, 0.45), oak)   # their bench
    # defence benches (tables) in front of the dock, facing the bench (+Y)
    for k in range(2):
        B.box((2.4, 9.5 + k * 2.2, 0.74), (3.2, 0.8, 0.05), oak).box((2.4, 9.85 + k * 2.2, 0.4), (3.2, 0.06, 0.75), dark)
        B.box((2.4, 8.9 + k * 2.2, 0.45), (3.2, 0.45, 0.06), dark)
    # the bar and the public benches (facing +Y)
    B.box((0, 7.0, 0.5), (14, 0.12, 1.0), dark)
    for k in range(5):
        for x in (-3.6, 3.4):
            B.box((x, 5.6 - k * 1.25, 0.45), (5.4, 0.45, 0.06), oak).box((x, 5.85 - k * 1.25, 0.75), (5.4, 0.06, 0.6), oak)
    room_o = B.done()
    gl = glass("DockGlass", (0.94, 0.97, 0.97), 0.02)
    for (loc, size) in (((x0 + 0.02, (y0 + y1) / 2, 1.85), (0.02, y1 - y0, 1.3)), (((x0 + x1) / 2, y0, 1.25), (x1 - x0, 0.02, 1.9)),
                        (((x0 + x1) / 2, y1, 1.25), (x1 - x0, 0.02, 1.9))):
        box("DockGlass", loc, size, gl)
    for k in range(6):
        box("Win", (7.15, 1.6 + k * 3.6, 4.1), (0.02, 2.4, 4.6), glass("CourtGlass", (0.9, 0.93, 0.95), 0.02))
    pt = bpy.data.lights.new("Portal", 'AREA'); pt.shape = 'RECTANGLE'; pt.size = 22; pt.size_y = 4.6; pt.cycles.is_portal = True
    po = bpy.data.objects.new("Portal", pt); bpy.context.collection.objects.link(po); po.location = (7.3, 10, 4.1); po.rotation_euler = (0, math.radians(-90), 0)
    for x in (-3, 0, 3):
        for y in (4, 10, 16):
            l = area_light((x, y, 7.9), (0, 0, 0), 1.5, 90, (1.0, 0.9, 0.78)); l.visible_camera = False
    # dressing: brass pendant lamps, curtains half-drawn on the tall windows, microphones on the bench and desks,
    # stacked case files, leather chairs for counsel, a wall clock, two framed paintings (generic landscapes)
    for x in (-3.5, 0.0, 3.5):
        for y in (4.0, 11.0, 17.0):
            dd.model_h("Chandelier_02", (x, y, 6.4), 1.1)
            pl = bpy.data.lights.new("Pendant", 'POINT'); pl.energy = 120; pl.color = (1.0, 0.78, 0.5); pl.shadow_soft_size = 0.4
            po = bpy.data.objects.new("Pendant", pl); bpy.context.collection.objects.link(po); po.location = (x, y, 6.6)
    curtain = fabric("Curtain", (0.32, 0.06, 0.06), 0.9, 0.6, 300)
    for k in range(6):
        for sy in (-1, 1):
            box("Curtain", (7.0, 1.6 + k * 3.6 + sy * 0.85, 4.1), (0.06, 0.75, 4.8), curtain)
    mic_m = pbr("MicM", (0.03, 0.03, 0.03), 0.4, 0.6)
    for x in (-1.6, 0.0, 1.6):
        cyl("Mic", (x, BENCH_Y - 0.25, 1.82), 0.006, 0.3, mic_m, verts=8, rot=(math.radians(-25), 0, 0))
        cyl("MicHead", (x, BENCH_Y - 0.33, 1.95), 0.014, 0.04, mic_m, verts=10, rot=(math.radians(-25), 0, 0))
    for x in (1.2, 2.4, 3.6):
        cyl("Mic", (x, 9.3, 0.9), 0.006, 0.3, mic_m, verts=8, rot=(math.radians(-25), 0, 0))
    for k in range(6):
        box("CaseFiles", (-2.6 + 0.02 * k, BENCH_Y - 2.0, 1.12 + 0.03 * k), (0.3, 0.38, 0.028),
            pbr("CF", ((0.55, 0.42, 0.25), (0.82, 0.8, 0.74))[k % 2], 0.8), rot=(0, 0, 0.08 * k))
    for k in range(4):
        dd.model_h("dining_chair_02", (1.3 + k * 1.0, 8.85, 0), 0.95, rot_z=0.0)
    dd.model_h("wall_clock", (0, 20.45, 6.2), 0.5, rot_z=math.pi)
    for x in (-5.0, 5.0):
        dd.model_h("fancy_picture_frame_01", (x, 20.45, 3.0), 1.4, rot_z=math.pi)
    # papers on the bench
    for k in range(4):
        box("Paper", (-2.0 + k * 1.3, BENCH_Y - 0.1, 1.655), (0.21, 0.3, 0.003), pbr("Paper", (0.85, 0.84, 0.8), 0.8), rot=(0, 0, 0.1 * k))
    return room_o


def robed(name, gender, years, hair):
    return person(name, gender, years, "male_elegantsuit01" if gender > 0.5 else "female_elegantsuit01", hair, cval=0.04, hv=0.3, sat=0.0)


def seated(h, loc, face, lean=8, seat_z=0.48):
    zero(h); from human import reset_pose
    reset_pose(h); pose_sit(h, lean=lean)
    for sd, sg in (("L", 1), ("R", -1)):          # hands resting on the thighs
        knee = h.bone_tail(f"upperleg02.{sd}"); hip = h.bone_head(f"upperleg01.{sd}")
        reach(h, sd, hip.lerp(knee, 0.65) + Vector((0, 0, 0.08)), Vector((sg * 0.6, 0.3, -0.5)))
    h.arm.rotation_euler = (0, 0, face); h.arm.location = Vector(loc); bpy.context.view_layer.update()
    # sit the pelvis on the seat
    hip = (h.bone_head("upperleg01.L") + h.bone_head("upperleg01.R")) / 2
    h.arm.location.z += seat_z + 0.06 - hip.z; bpy.context.view_layer.update()


def standing(h, loc, face, z=0.0):
    zero(h); pose_walk(h, 0.0, stride=0.0, arm_swing=0.0)
    place(h, loc, face, z); arms_relaxed(h)


PUBLIC_HAIR = ["short02", "bob01", "short04", "ponytail01", "short01", "long01", "short03", "bob02"]


def public(c, n, rng, rows=(0, 1, 2), turned=0.0):
    out = []
    for k in range(n):
        g = 1.0 if k % 2 == 0 else 0.0
        cl = ("male_casualsuit05", "male_casualsuit01", "male_elegantsuit01", "male_casualsuit03")[k % 4] if g > 0.5 else "female_elegantsuit01"
        h = person(f"Pub{k}", g, int(rng.integers(25, 65)), cl, PUBLIC_HAIR[k % 8], cval=float(rng.uniform(0.1, 0.35)), hv=float(rng.uniform(0.15, 0.6)))
        row = rows[k % len(rows)]; side = -3.6 if (k // len(rows)) % 2 == 0 else 3.4
        x = side - 1.8 + ((k * 1.7) % 3.6)
        seated(h, (x, 5.35 - row * 1.25, 0), math.pi + turned)
        h.seat = (x, 5.35 - row * 1.25)
        out.append(h)
    return out


def build(variant=None):
    c = {}
    v = variant or "aisle"
    world_sky(sun_elev_deg=14, sun_rot_deg=270, strength=0.35, tint=(0.85, 0.9, 1.0))
    sun(14, 270, energy=0.3, color=(0.9, 0.93, 1.0), angle_deg=8)
    room()
    rng = np.random.default_rng(23)
    x0, x1, y0, y1 = DOCK
    dock_mid = Vector(((x0 + x1) / 2, (y0 + y1) / 2, 0.3))
    if v in ("aisle", "judges", "reverse"):
        c["public"] = public(c, 10 if v != "reverse" else 12, rng, turned=(math.radians(-55) if v == "reverse" else 0.0))
    if v == "aisle":
        c["walkers"] = [person("Late0", 0.0, 34, "female_elegantsuit01", "bob02", cval=0.25),
                        person("Late1", 1.0, 58, "male_elegantsuit01", "short02", cval=0.15, hv=0.7)]
    if v in ("dock", "ashamed", "file", "reverse"):
        c["accused"] = []
        n = 1 if v == "ashamed" else 4
        for k in range(n):
            h = person(f"Acc{k}", 1.0, 35 + 5 * k, ("male_casualsuit05", "male_casualsuit01", "male_casualsuit03")[k % 3],
                       ("short02", "short04", "short01", "short03")[k % 4], cval=0.2)
            c["accused"].append(h)
        if v in ("dock", "ashamed"):
            standing(c["accused"][0], (x0 + 0.55, (y0 + y1) / 2, 0.3), math.radians(-90), z=0.3)    # facing -X (toward the room)
            if v == "ashamed":
                c["accused"][0].rot("neck01", (0, 1, 0), 0)
            for k, h in enumerate(c["accused"][1:]):
                seated(h, (x0 + 1.3, y0 + 0.7 + k * 1.3, 0.3), math.radians(-90), seat_z=0.67)
        else:
            for k, h in enumerate(c["accused"]):
                seated(h, (x0 + 1.3, y0 + 0.6 + k * 1.1, 0.3), math.radians(-90), seat_z=0.67)
    if v == "dock":
        clerk = robed("Clerk", 0.0, 44, "bob01"); standing(clerk, (-2.8, BENCH_Y - 1.4, 0), math.pi)
        c["clerk"] = clerk
        c["sheet"] = box("ClerkSheet", (0, 0, 0), (0.21, 0.003, 0.3), pbr("Paper2", (0.88, 0.87, 0.83), 0.8))
    if v in ("prosecutor", "judges", "dock", "file"):
        c["judges"] = [robed(f"Judge{k}", (1.0, 0.0, 1.0)[k], (58, 52, 47)[k], ("short02", "bob02", "short04")[k]) for k in range(3)]
        if v != "judges":
            for k, h in enumerate(c["judges"]):
                seated(h, ((-1.6, 0, 1.6)[k], BENCH_Y + 0.75, 0.5), 0.0, seat_z=1.02)
    if v in ("prosecutor", "file"):
        pr = robed("Prosecutor", 0.0, 50, "bob01"); c["prosecutor"] = pr
        standing(pr, (-5.4, 13.4, 0.4), math.radians(-120), z=0.4)
    if v == "file":
        c["lawyers"] = []
        for k in range(3):
            lw = robed(f"Lawyer{k}", (1.0, 0.0, 1.0)[k], (40, 36, 55)[k], ("short01", "ponytail01", "short03")[k])
            seated(lw, (1.3 + k * 1.1, 8.95, 0), math.pi, seat_z=0.48)
            c["lawyers"].append(lw)
        c["folder"] = box("Folder", (0, 0, 0), (0.24, 0.32, 0.02), pbr("FolderM", (0.55, 0.42, 0.25), 0.7))
    return c


# ============================================================================ animation
def anim_aisle(c, t):
    sec = t * DUR["aisle"]
    for k, h in enumerate(c["walkers"]):
        walk_to(h, Vector((0.2 - 0.5 * k, 0.5 - 1.2 * k, 0)), Vector((0.2 - 0.5 * k, 6.5, 0)), sec, speed=0.9)
        if h.arm.location.y > 4.0:
            h.arm.location.x = 0.2 - 0.5 * k


def anim_dock(c, t):
    sec = t * DUR["dock"]
    cl = c["clerk"]; M = cl.arm.matrix_world.to_3x3()
    chest = cl.bone_head("spine01") + Vector((0, 0, 0.35)) + M @ Vector((0, -0.32, 0))
    reach(cl, "L", chest + M @ Vector((0.1, 0, -0.05)), M @ Vector((1, 0.3, -0.6)))
    reach(cl, "R", chest + M @ Vector((-0.1, 0, -0.05)), M @ Vector((-1, 0.3, -0.6)))
    sh = c["sheet"]; sh.location = chest + Vector((0, 0, 0.02 * math.sin(sec * 0.7))); sh.rotation_euler = (math.radians(-30), 0, cl.arm.rotation_euler.z)
    cl.rot("head", (1, 0, 0), 12)


def anim_prosecutor(c, t):
    sec = t * DUR["prosecutor"]
    pr = c["prosecutor"]; standing(pr, (-5.4, 13.4, 0.4), math.radians(-120), z=0.4)
    M = pr.arm.matrix_world.to_3x3(); sh = pr.bone_head("upperarm01.R")
    g = 0.5 + 0.5 * math.sin(sec * 1.1)
    reach(pr, "R", sh + M @ Vector((-0.15, -0.45 - 0.1 * g, -0.15 + 0.2 * g)), M @ Vector((-0.6, 0.2, -0.7)))
    pr.rot("head", (0, 0, 1), 6 * math.sin(sec * 0.6))


def anim_file(c, t):
    sec = t * DUR["file"]
    anim_prosecutor(c, t)
    u = ease(min(1.0, max(0.0, (sec - 2.0) / 3.0)))
    a = Vector((1.3, 9.45, 0.775)); b = Vector((3.5, 9.45, 0.775))
    f = c["folder"]; f.location = a.lerp(b, u) + Vector((0, 0, 0.06 * math.sin(math.pi * u)))
    lw0, lw2 = c["lawyers"][0], c["lawyers"][2]
    if u < 0.5:
        reach(lw0, "L", f.location + Vector((0, -0.1, 0.05)), Vector((0.5, -0.3, -0.6)))
    else:
        reach(lw2, "R", f.location + Vector((0, -0.1, 0.05)), Vector((-0.5, -0.3, -0.6)))


def anim_ashamed(c, t):
    h = c["accused"][0]; x0, x1, y0, y1 = DOCK
    standing(h, (x0 + 0.55, (y0 + y1) / 2, 0.3), math.radians(-90), z=0.3)
    h.rot("neck01", (0, 1, 0), 12 + 3 * t); h.rot("head", (0, 1, 0), 14 + 4 * t)     # bowed toward -X (forward)


def anim_judges(c, t):
    sec = t * DUR["judges"]
    for k, h in enumerate(c["judges"]):
        x = (-1.6, 0, 1.6)[k]
        a = Vector((-4.2, BENCH_Y + 1.3, 0.5)); b = Vector((x, BENCH_Y + 1.3, 0.5))
        walk_to(h, a, b, max(0.0, sec - 1.2 * k), speed=0.8)
        h.arm.rotation_euler.z = math.radians(90) if h.arm.location.x < x - 0.05 else 0.0
        ground(h, 0.5)
    # the public rises as they enter (a staggered stand-up)
    for k, h in enumerate(c["public"]):
        u = ease(min(1.0, max(0.0, (sec - 0.6 - 0.15 * k) / 1.2)))
        if u > 0.5:
            standing(h, (h.seat[0], h.seat[1] - 0.15, 0), math.pi)
        else:
            seated(h, (h.seat[0], h.seat[1], 0), math.pi)


def anim_reverse(c, t):
    for k, h in enumerate(c["public"]):
        h.rot("head", (0, 0, 1), 3 * math.sin(t * 3 + k))


# ============================================================================ cameras
MOVES = {
    "aisle": dict(kind="anim", dof=None, anim=anim_aisle, title=("Chapter Four", "The Night Before", 24, 4.5 * 24),
                  cam=lambda c, t: (Vector((0.4, -0.2, 1.7)).lerp(Vector((0.3, 3.0, 1.75)), ease(t)), Vector((0.0, 18.0, 2.0)), 28)),
    "dock": dict(kind="anim", dof=4.0, anim=anim_dock,
                 cam=lambda c, t: (Vector((5.6, 17.5, 1.9)).lerp(Vector((5.2, 17.2, 1.85)), ease(t)), Vector((5.0, 11.0, 1.55)), 40),
                 focus=lambda c, t: Vector((5.15, 11.25, 1.9))),
    "prosecutor": dict(kind="anim", dof=4.0, anim=anim_prosecutor,
                       cam=lambda c, t: (Vector((-1.6, 10.2, 1.75)).lerp(Vector((-2.0, 10.6, 1.72)), ease(t)), Vector((-5.4, 13.4, 1.75)), 45),
                       focus=lambda c, t: Vector((-5.4, 13.4, 1.9))),
    "file": dict(kind="anim", dof=5.6, anim=anim_file,
                 cam=lambda c, t: (Vector((-1.6, 13.5, 2.6)).lerp(Vector((-1.2, 13.8, 2.55)), ease(t)), Vector((3.2, 9.6, 0.9)), 30),
                 focus=lambda c, t: Vector((2.4, 9.4, 1.0))),
    "ashamed": dict(kind="anim", dof=2.8, anim=anim_ashamed,
                    cam=lambda c, t: (Vector((1.4, 10.0, 1.75)).lerp(Vector((2.4, 10.5, 1.78)), ease(t)), Vector((5.15, 11.25, 1.7)), 45),
                    focus=lambda c, t: Vector((5.15, 11.25, 1.8))),
    "reverse": dict(kind="anim", dof=4.0, anim=anim_reverse,
                    cam=lambda c, t: (Vector((6.3, 12.6, 2.1)).lerp(Vector((6.3, 12.0, 2.05)), ease(t)), Vector((-1.5, 3.5, 1.0)), 28),
                    focus=lambda c, t: Vector((-1.5, 4.0, 1.0))),
    "judges": dict(kind="anim", dof=5.6, anim=anim_judges,
                   cam=lambda c, t: (Vector((-0.8, 6.2, 1.7)).lerp(Vector((-0.4, 7.4, 1.75)), ease(t)), Vector((0.0, BENCH_Y + 1.0, 1.8)), 30),
                   focus=lambda c, t: Vector((0.0, BENCH_Y + 1.0, 1.6))),
}
