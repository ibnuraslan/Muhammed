"""A TV NEWSROOM, March 1985 (generic: no network names or logos). A studio corner with an anchor desk, two pedestal
cameras, a lighting grid of fresnels, a slatted backdrop; behind glass, the newsroom: desks, typewriters, a wire teletype.

Ch4 7A  roll     the cameras roll on the anchor desk: a pedestal camera glides in, its tally lamp on
Ch4 7B  wire     in the newsroom a wire teletype chatters out copy; a writer tears it off
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph
import twp
import machines as MC
import typewriter as T

EXPOSURE = 0.0
DUR = {"roll": 5.0, "wire": 4.5}
ANCHOR = Vector((0.0, 2.0, 0.0))


def studio_camera(name):
    body = pbr("CamBody", (0.32, 0.33, 0.34), 0.4, 0.4); dark = pbr("CamDark", (0.03, 0.03, 0.035), 0.4)
    r = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(r)
    parts = [box("CamHousing", (0, 0, 1.45), (0.36, 0.7, 0.42), body, bevel=0.03), box("Viewfinder", (0, -0.42, 1.62), (0.3, 0.22, 0.22), dark, bevel=0.02),
             cyl("Lens", (0, 0.5, 1.42), 0.11, 0.35, dark, verts=24, rot=(math.radians(90), 0, 0)),
             cyl("LensHood", (0, 0.7, 1.42), 0.14, 0.08, dark, verts=24, rot=(math.radians(90), 0, 0)),
             box("PanBar", (0.22, -0.6, 1.3), (0.03, 0.6, 0.03), pbr("Chrome", (0.8, 0.8, 0.8), 0.2, 1.0), rot=(math.radians(-20), 0, 0)),
             cyl("Column", (0, 0, 0.75), 0.09, 1.2, pbr("PedChrome", (0.7, 0.7, 0.72), 0.2, 1.0), verts=20),
             cyl("Base", (0, 0, 0.12), 0.45, 0.16, body, verts=6), cyl("Ring", (0, 0, 0.95), 0.32, 0.03, pbr("PedChrome2", (0.7, 0.7, 0.72), 0.2, 1.0), verts=32)]
    for k in range(3):
        a = k * 2.094
        parts.append(cyl("Caster", (0.4 * math.cos(a), 0.4 * math.sin(a), 0.05), 0.05, 0.04, dark, verts=12, rot=(math.radians(90), 0, a)))
    tally = pbr("Tally", (0.4, 0.02, 0.02), 0.3, 0.0, **{'Emission Color': (1, 0.05, 0.03, 1), 'Emission Strength': 0.0})
    parts.append(cyl("TallyLamp", (0, 0.2, 1.7), 0.025, 0.03, tally, verts=12))
    for o in parts:
        o.parent = r
    return r, tally


def build(variant=None):
    c = {}
    rng = np.random.default_rng(85)
    world_flat((0.02, 0.022, 0.026), 1.0)
    box("Floor", (0, 0, -0.01), (16, 14, 0.02), ph.texture("concrete_floor_painted", scale=0.4, name="StudioFloor", tint=(0.45, 0.47, 0.48)))
    wall = ph.texture("painted_plaster_wall", scale=0.5, name="NewsWall", tint=(0.55, 0.58, 0.6))
    box("BackWall", (0, 3.6, 2.5), (16, 0.1, 5), wall); box("SideWall", (-8, 0, 2.5), (0.1, 14, 5), wall)
    # backdrop: dark blue slatted panels with a soft gradient light wash (generic, no graphics)
    slat_m = pbr("Slat", (0.06, 0.09, 0.16), 0.45, 0.3)
    for k in range(24):
        box("BackSlat", (-2.9 + k * 0.25, 3.3, 1.9), (0.18, 0.08, 3.4), slat_m)
    wash = area_light((0, 2.6, 4.2), (math.radians(30), 0, 0), 5.0, 120, (0.35, 0.5, 1.0)); point_at(wash, (0, 3.3, 1.2)); wash.visible_camera = False
    # anchor desk (curved front), chair, papers
    desk_m = ph.texture("dark_wood", scale=0.8, name="AnchorDesk")
    box("DeskTop", (ANCHOR.x, ANCHOR.y - 0.1, 0.79), (2.6, 0.8, 0.04), pbr("DeskTopGrey", (0.3, 0.3, 0.31), 0.35))
    box("DeskFront", (ANCHOR.x, ANCHOR.y - 0.48, 0.39), (2.6, 0.06, 0.78), desk_m)
    ph.model("modern_arm_chair_01", loc=(ANCHOR.x, ANCHOR.y + 0.5, 0), rot_z=math.pi, scale=0.95)
    ph.model("office_notepads", loc=(ANCHOR.x + 0.4, ANCHOR.y - 0.2, 0.81), scale=0.35)
    MC.terminal("DeskMonitor", (ANCHOR.x - 0.9, ANCHOR.y + 0.05, 0.81), math.pi * 0.95)
    # lighting grid of fresnels (scanned lamp housings) with real spots
    for k in range(5):
        for j in range(2):
            x = -2.4 + k * 1.2; y = -0.5 + j * 1.6
            ph.model("hanging_industrial_lamp", loc=(x, y, 4.6), scale=0.6)
            sp = bpy.data.lights.new("Fresnel", 'SPOT'); sp.energy = 1600; sp.spot_size = math.radians(40); sp.spot_blend = 0.5; sp.color = (1.0, 0.9, 0.78)
            so = bpy.data.objects.new("Fresnel", sp); bpy.context.collection.objects.link(so); so.location = (x, y, 4.0); point_at(so, (ANCHOR.x, ANCHOR.y, 1.0))
    box("Grid", (0, 0.3, 4.75), (6, 2.2, 0.05), pbr("GridPipe", (0.1, 0.1, 0.1), 0.4, 0.8))
    cams = []
    for k, x in enumerate((-1.3, 1.6)):
        r, tally = studio_camera(f"StudioCam{k}"); r.location = (x, -2.6, 0); r.rotation_euler = (0, 0, math.radians(-12 if x < 0 else 14))
        cams.append(r)
    c["cams"] = cams; c["tally"] = tally
    d = bpy.data.materials["Tally"].node_tree.nodes["Principled BSDF"].inputs['Emission Strength'].driver_add("default_value").driver
    d.type = 'SCRIPTED'; d.expression = "20 * (1 if frame > 24 else 0)"
    for k in range(6):
        cyl("Cable", (-2 + k * 0.7, -3.5 + k * 0.1, 0.01), 0.02, 3.0, pbr("CableBlack", (0.02, 0.02, 0.02), 0.6), verts=8, rot=(math.radians(90), 0, 0.3 * k))
    # the newsroom behind glass (to the right, x > 4): desks with typewriters, the wire teletype, monitors
    box("GlassWall", (4.0, 0, 1.4), (0.03, 7, 2.8), glass("NewsGlass", (0.9, 0.93, 0.95)))
    box("GlassFrame", (4.0, 0, 2.85), (0.06, 7, 0.1), pbr("Frame", (0.15, 0.15, 0.16), 0.4, 0.6))
    for k in range(3):
        for j in range(2):
            x, y = 5.4 + j * 1.8, -2.0 + k * 1.8
            ph.model("metal_office_desk", loc=(x, y, 0), rot_z=math.pi / 2, scale=0.7)
            T.make(f"NTW{k}{j}", loc=(x - 0.05, y, 0.553), rot_z=math.pi / 2, mechanism=False, glyphs=False, legends=False, text=" ",
                   color=[(0.32, 0.28, 0.22), (0.11, 0.15, 0.2)][(k + j) % 2])
            twp.model_fit("SchoolChair_01", (x + 0.55, y, 0), rot_z=math.pi / 2, height=0.92)
    tty, p = MC.teletype("WireTTY", (5.6, 2.6, 0), math.radians(200)); c["wire"] = p; c["wire_root"] = tty
    for k in range(3):
        MC.terminal(f"NewsMon{k}", (7.6, -2.4 + k * 1.2, 1.0), -math.pi / 2)
        box("MonShelf", (7.7, -2.4 + k * 1.2, 0.98), (0.6, 0.6, 0.04), pbr("Shelf", (0.3, 0.3, 0.3), 0.5))
    for x in (5.4, 7.0):
        for y in (-1.5, 1.5):
            ph.model("mounted_fluorescent_lights", loc=(x, y, 2.9), rot_z=math.pi / 2)
            l = area_light((x, y, 2.82), (0, 0, 0), 0.9, 30, (0.9, 0.96, 1.0)); l.visible_camera = False
    box("NewsCeil", (6.0, 0, 2.95), (4, 7, 0.05), ph.texture("ceiling_interior", scale=0.5, name="NewsCeil"))
    # people: the anchor (unnamed, from behind / side), a camera operator, a writer at the wire
    P = {}
    P["anchor"] = twp.person("Anchor", 1.0, 50, "male_elegantsuit01", "short02", hv=0.55, cval=0.5, hue=0.6, sat=0.2)
    P["op"] = twp.person("CamOp", 1.0, 30, "male_casualsuit02", "short03", hv=0.25, cval=0.55, hue=0.1, sat=0.2)
    P["writer"] = twp.person("Writer", 0.0, 34, "female_elegantsuit01", "long01", hv=0.3, cval=0.6, hue=0.55, sat=0.25)
    c["P"] = P
    animate(c, 0.0, "roll")
    return c


def animate(c, sec, shot):
    from human import reach, fingers_curl
    P = c["P"]
    twp.seat(P["anchor"], (ANCHOR.x, ANCHOR.y + 0.32, 0), 0.0, lean=6)
    reach(P["anchor"], "R", Vector((ANCHOR.x + 0.25, ANCHOR.y - 0.25, 0.86)), Vector((0.6, 0.3, -0.7)), Vector((0, -1, -0.2)))
    reach(P["anchor"], "L", Vector((ANCHOR.x - 0.25, ANCHOR.y - 0.25, 0.86)), Vector((-0.6, 0.3, -0.7)), Vector((0, -1, -0.2)))
    P["anchor"].rot("head", (0, 0, 1), 4 * math.sin(sec * 1.1))
    cam0 = c["cams"][0]
    cam0.location = (-1.3 + 0.4 * ease(min(1.0, sec / 4.0)), -2.6 + 0.5 * ease(min(1.0, sec / 4.0)), 0)
    op = P["op"]
    twp.stand(op, (cam0.location.x + 0.05, cam0.location.y - 0.85, 0), math.radians(-5))
    reach(op, "R", Vector(cam0.location) + Vector((0.22, -0.88, 1.3)), Vector((0.5, -0.4, -0.7)), Vector((0, 1, 0)))
    op.rot("head", (1, 0, 0), 6)
    MC.run_teletype(c["wire"], sec, rate=9.0)
    w = P["writer"]
    twp.hide(twp.person_objs(w), shot == "wire")            # the wire teletype chattering on its own in the empty newsroom
    tty = c["wire_root"]
    front = tty.matrix_world @ Vector((0, -0.62, 0))
    twp.stand(w, (front.x, front.y, 0), tty.rotation_euler.z + math.pi)          # facing the machine
    tear = ease(min(1.0, max(0.0, (sec - 2.6) / 0.8))) if shot == "wire" else 0.0
    pp = tty.matrix_world @ Vector((0.0, -0.05, 1.18 + 0.1 * tear))
    for sd, dx in (("L", -0.12), ("R", 0.12)):
        reach(w, sd, pp + tty.matrix_world.to_3x3() @ Vector((dx, -0.12, 0)), Vector((dx * 4, -0.3, -0.9)), tty.matrix_world.to_3x3() @ Vector((0, 1, 0.3)))
    fingers_curl(w, 40, thumb=20); w.rot("head", (1, 0, 0), 10)
    bpy.context.view_layer.update()


def anim(shot):
    return lambda c, t: animate(c, t * DUR[shot], shot)


def cam_roll(c, t):
    e = ease(t)
    return (Vector((-2.6, -1.6, 1.75)).lerp(Vector((-2.3, -1.3, 1.7)), e), Vector((0.0, 1.6, 1.1)), 30)


def cam_wire(c, t):
    e = ease(t); tty = c["wire_root"]
    at = tty.matrix_world @ Vector((0.0, 0.1, 1.2))
    return (at + Vector((-1.3, -0.9, 0.35)).lerp(Vector((-1.05, -0.7, 0.3)), e), at, 32)


MOVES = {
    "roll": dict(kind="anim", dof=3.5, cam=cam_roll, focus=lambda c, t: Vector(c["cams"][0].location) + Vector((0, 0, 1.4)), anim=anim("roll")),
    "wire": dict(kind="anim", dof=2.2, cam=cam_wire, focus=lambda c, t: c["wire_root"].matrix_world @ Vector((0, 0.1, 1.2)), anim=anim("wire")),
}
