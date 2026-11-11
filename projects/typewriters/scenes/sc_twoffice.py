"""EMBASSY TYPING ROOM, Moscow 1984 (dramatization). Steel desks, typewriters, venetian blinds, fluorescent panels.
Variants: day (people at work) / night (empty, one desk lamp on the typewriter).

Intro 3A  typing     a secretary types; the ball whirls (3/4 front-left, slow push)
Intro 3B  notice     a clerk pins an "equipment upgrade" notice; a colleague stops to read it
Intro 8A  night_push push in on the lone typewriter under the desk lamp
Intro 8B  night_type no hands in frame: the ball types one short line, then stops
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph, paper_tex
import typewriter as T
import twp

EXPOSURE = -0.4
DUR = {"typing": 4.5, "notice": 5.0, "night_push": 4.5, "night_type": 5.0}
VARIANT_FOR = {"night_push": "night", "night_type": "night"}
DESK_Z = 0.79
DESK_A = Vector((0.9, 0.4, 0.0))
TEXT_A = "The copier on the fourth floor will be replaced\nthis week. Please clear all papers from the"
TEXT_N = "Moscow, May 1984."


def notice_image(path):
    import skia
    W_, H_ = 850, 1100
    s = skia.Surface(W_, H_); c = s.getCanvas(); c.clear(skia.Color4f(0.92, 0.91, 0.87, 1))
    p = skia.Paint(AntiAlias=True); p.setColor4f(skia.Color4f(0.08, 0.08, 0.09, 1))
    f = skia.Font(skia.Typeface.MakeFromFile(T.MONO_B), 46); f2 = skia.Font(skia.Typeface.MakeFromFile(T.MONO_B), 26)
    c.drawString("NOTICE TO ALL STAFF", 150, 160, f, p)
    c.drawString("EQUIPMENT UPGRADE", 190, 230, f, p)
    p.setColor4f(skia.Color4f(0.3, 0.3, 0.32, 1))
    rng = np.random.default_rng(4); y = 330
    for k in range(14):
        c.drawRect(skia.Rect.MakeXYWH(90, y, rng.uniform(450, 670), 9), p); y += 34
        if k % 5 == 4:
            y += 26
    s.makeImageSnapshot().save(path, skia.kPNG)
    return path


def build(variant=None):
    c = {"variant": variant}
    night = variant == "night"
    rng = np.random.default_rng(5)
    if night:
        world_flat((0.004, 0.006, 0.011), 1.0)
    else:
        world_sky(sun_elev_deg=34, sun_rot_deg=70, strength=0.45, tint=(0.88, 0.92, 1.0))
    # ---------------------------------------------------------------- room shell: x -4..4, y -3..3, h 3.0
    box("Floor", (0, 0, -0.01), (8, 6, 0.02), ph.texture("old_linoleum_flooring_01", scale=0.5, tint=(0.55, 0.6, 0.62)))
    wall = pbr("WallPaint", (0.52, 0.53, 0.5), 0.85)
    box("WallBack", (0, 3.05, 1.5), (8, 0.1, 3.0), wall); box("WallFront", (0, -3.05, 1.5), (8, 0.1, 3.0), wall)
    box("WallL", (-4.05, 0, 1.5), (0.1, 6, 3.0), wall)
    box("Ceiling", (0, 0, 3.02), (8, 6, 0.04), pbr("CeilTile", (0.66, 0.66, 0.64), 0.9))
    box("Skirting", (0, 2.995, 0.05), (8, 0.01, 0.1), pbr("Skirt", (0.12, 0.1, 0.08), 0.5))
    # +X wall: three tall windows with blinds, a brick building across the street
    for z, h in ((0.45, 0.9), (2.8, 0.4)):
        box("WallR", (4.05, 0, z), (0.1, 6, h), wall)
    for y in (-3.0, -1.0, 1.0, 3.0):
        box("WinPier", (4.05, y, 1.65), (0.1, 0.6, 1.5), wall)
    frame = pbr("WinFrame", (0.36, 0.34, 0.3), 0.5)
    for yc in (-2.0, 0.0, 2.0):
        box("Sash", (4.02, yc, 1.65), (0.04, 1.4, 0.04), frame)
        box("SashV", (4.02, yc, 1.65), (0.04, 0.04, 1.5), frame)
        box("Glass", (4.04, yc, 1.65), (0.01, 1.4, 1.5), glass("WinGlass", (0.9, 0.93, 0.95)))
    slat = pbr("Blind", (0.72, 0.71, 0.66), 0.5)
    for yc in (-2.0, 0.0, 2.0):
        twp.venetian(3.95, yc, 1.3 if not night else 0.95, 2.38, 1.36, "y", slat, tilt=-55)
    brick = ph.texture("brick_wall_02", scale=0.4)
    box("Across", (22, 0, 8), (0.5, 60, 24), brick)
    for k in range(5):
        for j in range(4):
            box("AcrossWin", (21.7, -12 + k * 6, 2.5 + j * 3.4), (0.05, 1.4, 1.8), pbr("AcrossGlass", (0.03, 0.035, 0.04), 0.15, 0.4))
    if not night:
        sn = bpy.data.lights.new("Sun", 'SUN'); sn.energy = 2.6; sn.angle = math.radians(1.5); sn.color = (1.0, 0.94, 0.86)
        so = bpy.data.objects.new("Sun", sn); bpy.context.collection.objects.link(so); so.rotation_euler = (math.radians(58), math.radians(-35), math.radians(-90))
        pt = bpy.data.lights.new("Portal", 'AREA'); pt.shape = 'RECTANGLE'; pt.size = 6.0; pt.size_y = 1.5; pt.cycles.is_portal = True
        po = bpy.data.objects.new("Portal", pt); bpy.context.collection.objects.link(po); po.location = (3.98, 0, 1.65); po.rotation_euler = (0, math.radians(-90), 0)
    else:
        mn = area_light((3.8, 0.5, 1.8), (0, 0, 0), 2.5, 18, (0.45, 0.55, 0.85)); point_at(mn, (0, 0.4, 0.5)); mn.visible_camera = False
    for x in (-2.2, 0.6, 3.0):
        for y in (-1.5, 1.2):
            ph.model("mounted_fluorescent_lights", loc=(x, y, 3.0), rot_z=math.radians(90))
            if not night:
                l = area_light((x, y, 2.92), (0, 0, 0), 0.9, 38, (0.9, 0.96, 1.0)); l.visible_camera = False
    # ---------------------------------------------------------------- desks with typewriters (typists sit at +Y, face -Y)
    c["tws"] = []
    desks = [(DESK_A, True), (Vector((-1.5, 0.4, 0)), True), (Vector((0.9, -1.9, 0)), True), (Vector((-1.5, -1.9, 0)), False)]
    paper = paper_tex.make_all()
    pages = [bpy.data.materials.new(f"Pg{k}") for k in range(3)]
    for k, m in enumerate(pages):
        m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(paper["pages"][k]); L.new(t.outputs[0], N["Principled BSDF"].inputs['Base Color'])
    for k, (p, has_tw) in enumerate(desks):
        ph.model("metal_office_desk", loc=(p.x, p.y, 0), rot_z=math.pi)
        if has_tw:
            tw = T.make(f"TW{k}", loc=(p.x - 0.15, p.y + 0.21, DESK_Z), rot_z=math.pi,
                        text=TEXT_N if (night and k == 0) else (TEXT_A if k == 0 else "Please clear all papers from the"),
                        color=(0.11, 0.15, 0.2) if k != 1 else (0.32, 0.28, 0.22), mechanism=(k == 0), glyphs=(k == 0), legends=(k == 0), seed=k)
            c["tws"].append(tw)
        ph.model("office_notepads", loc=(p.x + 0.55, p.y - 0.05, DESK_Z), rot_z=rng.uniform(-0.3, 0.3), scale=0.45)
        for j in range(3):
            bpy.ops.mesh.primitive_plane_add(size=1, location=(p.x + 0.5 + rng.uniform(-0.1, 0.1), p.y + rng.uniform(-0.2, 0.15), DESK_Z + 0.012 + j * 0.0005),
                                             rotation=(0, 0, rng.uniform(-0.4, 0.4)))
            o = bpy.context.active_object; o.scale = (0.21, 0.28, 1); o.data.materials.append(pages[(k + j) % 3])
        r, ms = twp.model_fit("painted_wooden_chair_01", (p.x - 0.15, p.y + 0.75, 0), rot_z=math.pi + rng.uniform(-0.15, 0.15), height=0.92)
    c["tw"] = c["tws"][0]
    ph.model("stationery_supplies", loc=(DESK_A.x + 0.35, DESK_A.y + 0.25, DESK_Z), rot_z=0.3)
    # desk lamp (on at night)
    lamp_r, lamp_ms = ph.model("desk_lamp_arm_01", loc=(DESK_A.x + 0.5, DESK_A.y + 0.25, DESK_Z), rot_z=math.radians(200))
    twp.tint_model(lamp_ms, (0.16, 0.2, 0.17), keep=0.1)
    if night:
        sp = bpy.data.lights.new("Lamp", 'SPOT'); sp.energy = 22; sp.spot_size = math.radians(85); sp.spot_blend = 0.6
        sp.color = (1.0, 0.74, 0.48); sp.shadow_soft_size = 0.04
        lo = bpy.data.objects.new("Lamp", sp); bpy.context.collection.objects.link(lo)
        lo.location = (DESK_A.x + 0.32, DESK_A.y + 0.05, DESK_Z + 0.5); point_at(lo, (DESK_A.x - 0.15, DESK_A.y + 0.05, DESK_Z + 0.05))
        bl = bpy.data.lights.new("Bounce", 'AREA'); bl.energy = 1.2; bl.size = 1.0; bl.color = (1.0, 0.8, 0.6)
        bo = bpy.data.objects.new("Bounce", bl); bpy.context.collection.objects.link(bo); bo.location = (DESK_A.x - 0.2, DESK_A.y - 0.6, DESK_Z + 0.4)
        point_at(bo, (DESK_A.x - 0.15, DESK_A.y, DESK_Z)); bo.visible_camera = False
    # ---------------------------------------------------------------- back wall: filing cabinets, clock; left wall: notice board
    import sc_invest
    steel = pbr("CabSteel", (0.3, 0.32, 0.3), 0.42, 0.55, **{'Coat Weight': 0.15}); hm = pbr("Chrome", (0.8, 0.8, 0.8), 0.2, 1.0)
    sc_invest.CAB_Y = 2.3
    for x in (-3.4, -2.92, -2.44, 1.9, 2.38, 2.86):
        sc_invest.filing_cabinet(x, steel, hm)
    ph.model("wall_clock", loc=(-0.4, 2.99, 2.25), rot_z=math.pi)
    ph.model("potted_plant_01", loc=(3.5, 2.5, 0))
    cork = pbr("Cork", (0.4, 0.29, 0.18), 0.9)
    box("CorkBoard", (-3.985, -0.6, 1.55), (0.03, 1.6, 1.0), cork)
    box("CorkFrame", (-3.99, -0.6, 1.55), (0.02, 1.66, 1.06), pbr("CorkFrame", (0.15, 0.1, 0.06), 0.5))
    for k in range(5):
        y, z = -1.2 + k * 0.32 + rng.uniform(-0.04, 0.04), 1.7 + rng.uniform(-0.2, 0.15)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(-3.965, y, z), rotation=(math.radians(90), rng.uniform(-0.05, 0.05), math.radians(90)))
        o = bpy.context.active_object; o.scale = (0.2, 0.26, 1); o.data.materials.append(pages[k % 3])
    import os
    nm = bpy.data.materials.new("Notice"); nm.use_nodes = True
    t = nm.node_tree.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(notice_image(os.path.join(T.GEN, "notice.png")))
    nm.node_tree.links.new(t.outputs[0], nm.node_tree.nodes["Principled BSDF"].inputs['Base Color'])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-3.6, 0.1, 1.3), rotation=(math.radians(90), 0, math.radians(90)))
    notice = bpy.context.active_object; notice.name = "NoticeSheet"; notice.scale = (0.21, 0.28, 1); notice.data.materials.append(nm)
    c["notice"] = notice
    # ---------------------------------------------------------------- people (day only)
    c["people"] = {}
    if not night:
        sec = twp.person("Secretary", 0.0, 33, "female_elegantsuit01", "bob02", hv=0.22, cval=0.35, hue=0.55, sat=0.25)
        twp.seat(sec, (DESK_A.x - 0.15, DESK_A.y + 0.66, 0), 0.0, lean=12)
        c["people"]["sec"] = sec
        sec2 = twp.person("Secretary2", 0.0, 45, "female_casualsuit01", "ponytail01", hv=0.4, cval=0.4)
        twp.seat(sec2, (-1.65, 1.06, 0), 0.0, lean=12)
        c["people"]["sec2"] = sec2
        clerk = twp.person("Clerk", 1.0, 40, "male_casualsuit03", "short02", hv=0.25, cval=0.25, hue=0.6, sat=0.15)
        c["people"]["clerk"] = clerk
        reader = twp.person("Reader", 1.0, 52, "male_elegantsuit01", "short04", hv=0.6, cval=0.2)
        c["people"]["reader"] = reader
    animate(c, 0.0)
    return c


# ============================================================================ animation
def animate(c, sec, shot=None):
    night = c["variant"] == "night"
    if night:
        T.type_at(c["tw"], sec, start=1.2 if shot == "night_type" else 99.0, cps=5.5)
    else:
        for k, tw in enumerate(c["tws"]):
            T.type_at(tw, sec + k * 1.3, start=0.0, cps=7.0 if k == 0 else 6.0)
        P = c["people"]
        twp.type_pose(P["sec"], c["tws"][0], sec)
        twp.type_pose(P["sec2"], c["tws"][1], sec + 0.8)
        # the clerk walks to the board with the notice, pins it; the reader walks in and stops beside him
        cl = P["clerk"]; nt = c["notice"]
        moving = twp.walk(cl, (-2.2, 1.6), (-3.55, -0.2), sec, speed=1.0)
        if moving:
            hand = cl.bone_head("lowerarm02.R") + twp.forward(cl) * 0.1
            nt.location = hand + Vector((0, 0, -0.05)); nt.rotation_euler = (math.radians(90), 0, math.radians(90))
        else:
            from human import reach, fingers_curl
            twp.face(cl, -math.pi / 2)                       # faces -X, the board
            k = ease(min(1.0, max(0.0, (sec - 2.1) / 0.9)))
            start = Vector((-3.7, -0.15, 1.35)); tgt = Vector((-3.966, -0.25, 1.62))
            nt.location = start.lerp(tgt, k)
            reach(cl, "R", nt.location + Vector((0.07, 0.07, 0.06)), Vector((0.3, -0.6, -0.7)), Vector((-1, 0, 0.2)))
            reach(cl, "L", nt.location + Vector((0.07, -0.07, 0.06)) if sec > 2.6 else cl.bone_head("upperarm01.L") + Vector((0.05, 0.1, -0.55)),
                  Vector((0.3, 0.7, -0.6)), Vector((-1, 0, 0.0)))
            fingers_curl(cl, 25, thumb=15)
        rd = P["reader"]
        if sec < 1.2:
            twp.walk(rd, (-1.0, -2.5), (-3.2, -1.3), 0.0)
        else:
            m = twp.walk(rd, (-1.0, -2.5), (-3.2, -1.25), sec - 1.2, speed=1.1)
            if not m:
                twp.face(rd, -math.pi / 2 - 0.35)
    bpy.context.view_layer.update()


def anim(shot):
    return lambda c, t: animate(c, t * DUR[shot], shot)


def _tw(c, p):
    return T.world(c["tw"], p)


def cam_typing(c, t):
    e = ease(t)
    hd = c["people"]["sec"].bone_head("head")
    tgt = _tw(c, (0.0, -0.05, 0.14)).lerp(hd, 0.4)
    a = _tw(c, (0.95, 0.05, 0.3)); b = _tw(c, (0.8, 0.02, 0.28))
    return (a.lerp(b, e), tgt, 38)


def cam_notice(c, t):
    e = ease(t)
    return (Vector((-0.6, 0.9, 1.65)).lerp(Vector((-0.85, 0.75, 1.62)), e), Vector((-3.7, -0.6, 1.4)), 30)


def cam_night_push(c, t):
    e = ease(t)
    tgt = _tw(c, (0.0, -0.02, 0.1))
    a = _tw(c, (0.55, -1.6, 0.55)); b = _tw(c, (0.3, -0.95, 0.38))
    return (a.lerp(b, e), tgt, 40)


def cam_night_type(c, t):
    e = ease(t)
    car = c["tw"]["carrier"].location.x
    tgt = _tw(c, (-0.02 + 0.04 * e, 0.02, 0.125))
    a = _tw(c, (0.16, -0.38, 0.36)); b = _tw(c, (0.12, -0.33, 0.33))
    return (a.lerp(b, e), tgt, 50)


MOVES = {
    "typing": dict(kind="anim", dof=2.6, cam=cam_typing, focus=lambda c, t: _tw(c, (0.0, 0.03, 0.13)), anim=anim("typing")),
    "notice": dict(kind="anim", dof=3.2, cam=cam_notice, focus=lambda c, t: c["notice"].location, anim=anim("notice")),
    "night_push": dict(kind="anim", dof=2.0, cam=cam_night_push, focus=lambda c, t: _tw(c, (0, 0, 0.12)), anim=anim("night_push")),
    "night_type": dict(kind="anim", dof=2.0, cam=cam_night_type, focus=lambda c, t: T.strike_point(c["tw"]), anim=anim("night_type")),
}
