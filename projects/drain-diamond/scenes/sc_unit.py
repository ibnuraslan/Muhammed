"""UNIT: the Paris armed-robbery squad office, 2009. Metal desks, files, a corkboard of blank / blurred prints (no
faces, no names), rain on tall windows over grey zinc roofs.
  pin  (ch3 1A, title): push into the office as a detective pins a print to the corkboard (medium-wide)
  read (ch3 1B): a second detective reads a file at her desk under a lamp, rain streaking the window behind
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import dd
from dd import officer, place, face_to, arms_relaxed, zero, ground
from human import reach, pose_walk, pose_sit, reset_pose, fingers_curl
from sc_invest import office_chair
from sc_boutique import haussmann

EXPOSURE = -0.8
DUR = {"pin": 9.0, "read": 9.0, "listen": 9.0}


def blank_print(name, loc, size, seed):
    """A blurred print: soft tonal blobs only (nothing identifiable), on white card."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = '4D'
    nz.inputs['W'].default_value = seed * 1.7; nz.inputs['Scale'].default_value = 2.5; nz.inputs['Detail'].default_value = 1
    L.new(tc.outputs['UV'], nz.inputs['Vector'])
    ramp = N.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (0.18, 0.18, 0.2, 1); ramp.color_ramp.elements[1].color = (0.75, 0.74, 0.7, 1)
    L.new(nz.outputs['Fac'], ramp.inputs['Fac']); L.new(ramp.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.4
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=(math.radians(90), 0, 0))
    o = bpy.context.active_object; o.name = name; o.scale = (size[0], size[1], 1); o.data.materials.append(m)
    return o


def build(variant=None):
    c = {}
    world_sky(sun_elev_deg=15, sun_rot_deg=200, strength=0.5, tint=(0.75, 0.82, 0.95))
    B = dd.Builder("Office")
    floor = dd.tex_mat("laminate_floor_02", 0.6, tint=(0.6, 0.58, 0.55), name="OffFloor", sat=0.5)
    wall = dd.tex_mat("painted_plaster_wall", 0.6, tint=(0.82, 0.82, 0.78), name="OffWall", sat=0.4)
    B.box((0, 4, -0.05), (10, 9, 0.1), floor).box((0, 4, 3.05), (10, 9, 0.1), pbr("OffCeil", (0.8, 0.8, 0.78), 0.9))
    B.box((-5.05, 4, 1.5), (0.1, 9, 3.0), wall).box((0, 8.55, 1.5), (10, 0.1, 3.0), wall)
    # window wall on the right (x = 5): tall windows over the roofs, rain on the glass
    for k in range(3):
        B.box((5.05, 0.6 + k * 3.0, 1.5), (0.1, 0.8, 3.0), wall)
    B.box((5.05, 4, 0.45), (0.1, 9, 0.9), wall).box((5.05, 4, 2.85), (0.1, 9, 0.3), wall)
    B.done()
    for k in range(3):
        box("Win", (5.05, 2.1 + k * 3.0, 1.75), (0.02, 2.2, 1.9), rain_glass("OffRain", 60, 0.55))
    pt = bpy.data.lights.new("Portal", 'AREA'); pt.shape = 'RECTANGLE'; pt.size = 9; pt.size_y = 2.0; pt.cycles.is_portal = True
    po = bpy.data.objects.new("Portal", pt); bpy.context.collection.objects.link(po); po.location = (5.2, 4, 1.75); po.rotation_euler = (0, math.radians(-90), 0)
    haussmann(-20, 20, seed=60, rot_z=math.radians(90), origin=(22, 4, -14), lit_frac=0.3)
    # desks, chairs, lamps, binders, a filing cabinet row, the corkboard
    fab = fabric("ChairFab", (0.05, 0.05, 0.06), 0.9, 0.3, 400); met = pbr("ChairMetal", (0.25, 0.25, 0.27), 0.35, 0.9)
    for k, (x, y, rz) in enumerate(((-2.5, 2.2, 0), (0.5, 2.2, 0), (-2.5, 5.0, math.pi), (0.5, 5.0, math.pi), (3.3, 3.6, -math.pi / 2))):
        dd.model_h("metal_office_desk", (x, y, 0), 0.76, rot_z=rz)
        if k < 4:
            office_chair((x, y - 0.75 if rz == 0 else y + 0.75, 0), rz, fab, met)
        else:
            office_chair((x + 0.8, y, 0), math.pi / 2, fab, met)      # the reader's chair, between desk and window
        dd.model_h("binder_notebook", (x - 0.4, y, 0.76), 0.05, rot_z=0.3 * k)
        if k % 2 == 0:
            dd.model_h("desk_lamp_arm_01", (x + 0.5, y + 0.1, 0.76), 0.45, rot_z=2.5)
        for j in range(3):
            box("Folder", (x + 0.1, y - 0.05 + 0.02 * j, 0.77 + 0.012 * j), (0.25, 0.33, 0.01), pbr("FolderM", ((0.55, 0.42, 0.25), (0.2, 0.3, 0.5), (0.6, 0.15, 0.1))[j], 0.7), rot=(0, 0, 0.1 * j))
    for k in range(4):
        dd.model_h("drawer_cabinet", (-4.7, 6.2 + k * 0.55, 0), 1.3, rot_z=math.radians(90))
    dd.model_h("potted_plant_01", (4.5, 7.8, 0), 1.0)
    # 2009 office dressing: venetian blinds (light bars on the floor), CRT monitors, desk phones, piled files, coffee cups,
    # a coat stand, a generic map of the region (shapes only, no text)
    slat = pbr("Slat", (0.85, 0.84, 0.8), 0.45, 0.2)
    for k in range(3):
        yc = 2.1 + k * 3.0
        for j in range(22):
            box("Blind", (4.98, yc, 0.85 + j * 0.085), (0.012, 2.2, 0.05), slat, rot=(0, math.radians(-20), 0))
    sn = sun(18, 0, energy=1.4, color=(1.0, 0.9, 0.78), angle_deg=1.0)
    sn.rotation_euler = (math.radians(72), 0, math.radians(90 + 20))       # low sun through the blinds onto the floor
    plastic = pbr("Beige", (0.62, 0.6, 0.55), 0.5)
    for k, (x, y, rz) in enumerate(((-2.5, 2.2, 0), (0.5, 2.2, 0), (-2.5, 5.0, math.pi), (0.5, 5.0, math.pi))):
        dd.model_h("television_02", (x - 0.1, y + (0.15 if rz == 0 else -0.15), 0.76), 0.36, rot_z=rz)
        ph_ = Vector((x + 0.45, y + (0.1 if rz == 0 else -0.1), 0.76))
        box("Phone", ph_ + Vector((0, 0, 0.03)), (0.18, 0.2, 0.06), plastic, bevel=0.01)
        box("Handset", ph_ + Vector((0, 0, 0.075)), (0.05, 0.2, 0.035), plastic, bevel=0.012)
        for j in range(5):
            box("FilePile", (x - 0.65, y + 0.1 * (j % 2), 0.77 + 0.025 * j), (0.25, 0.33, 0.022),
                pbr("Pile", ((0.55, 0.42, 0.25), (0.75, 0.73, 0.68), (0.2, 0.3, 0.5))[j % 3], 0.8), rot=(0, 0, 0.12 * (j - 2)))
        cyl("Mug", (x + 0.25, y - 0.15 if rz == 0 else y + 0.15, 0.815), 0.04, 0.1, pbr("MugM", ((0.85, 0.85, 0.82), (0.15, 0.2, 0.4))[k % 2], 0.3), verts=16)
    cyl("CoatStand", (-4.5, 0.6, 0.9), 0.025, 1.8, pbr("StandW", (0.25, 0.16, 0.1), 0.4), verts=12)
    for k in range(4):
        a_ = k * math.pi / 2
        box("CoatHook", (-4.5 + 0.1 * math.cos(a_), 0.6 + 0.1 * math.sin(a_), 1.72), (0.14, 0.02, 0.02), pbr("StandW", (0.25, 0.16, 0.1), 0.4), rot=(0, 0, a_))
    box("Coat", (-4.4, 0.6, 1.3), (0.12, 0.45, 0.8), fabric("CoatF", (0.3, 0.27, 0.22), 0.9, 0.4, 300), bevel=0.05)
    # the map: soft-coloured region shapes in a frame, no text
    mm = bpy.data.materials.new("Map"); mm.use_nodes = True
    N = mm.node_tree.nodes; L = mm.node_tree.links; p_ = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexVoronoi"); vo.inputs['Scale'].default_value = 6
    L.new(tc.outputs['UV'], vo.inputs['Vector'])
    ramp = N.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (0.85, 0.82, 0.7, 1); ramp.color_ramp.elements[1].color = (0.6, 0.72, 0.55, 1)
    sep = N.new("ShaderNodeSeparateColor"); L.new(vo.outputs['Color'], sep.inputs[0]); L.new(sep.outputs[0], ramp.inputs['Fac'])
    L.new(ramp.outputs['Color'], p_.inputs['Base Color']); p_.inputs['Roughness'].default_value = 0.5
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-4.97, 4.0, 1.7), rotation=(math.radians(90), 0, math.radians(-90)))
    mp = bpy.context.active_object; mp.scale = (1.6, 1.1, 1); mp.data.materials.append(mm)
    box("MapFrame", (-5.0, 4.0, 1.7), (0.02, 1.68, 1.18), pbr("MapFrameM", (0.1, 0.1, 0.1), 0.5))
    cork = dd.tex_mat("concrete_floor_02", 1.0, tint=(0.62, 0.45, 0.28), name="Cork", sat=0.9)
    box("Corkboard", (-1.0, 8.47, 1.65), (3.0, 0.03, 1.4), cork)
    box("CorkFrame", (-1.0, 8.49, 1.65), (3.1, 0.02, 1.5), pbr("CorkFrameM", (0.35, 0.25, 0.15), 0.5))
    rng = np.random.default_rng(4)
    for k in range(9):
        blank_print(f"Print{k}", (-2.2 + (k % 5) * 0.55 + rng.uniform(-0.05, 0.05), 8.44, 1.35 + (k // 5) * 0.55 + rng.uniform(-0.04, 0.04)), (0.2, 0.26), k)
    c["new_print"] = blank_print("PrintNew", (0, 0, -20), (0.2, 0.26), 99)
    for k in range(6):                       # red string between some prints
        box("String", (-1.6 + k * 0.4, 8.43, 1.6 + 0.12 * math.sin(k)), (0.4, 0.003, 0.004), pbr("StringR", (0.6, 0.05, 0.04), 0.6), rot=(0, 0.2 * math.cos(k), 0))
    for x in (-2.5, 1.0, 3.5):
        box("Fluo", (x, 4, 2.97), (0.3, 1.3, 0.05), emissive("FluoE", (0.92, 0.96, 1.0), 4))
        a = bpy.data.lights.new("FluoL", 'AREA'); a.shape = 'RECTANGLE'; a.size = 0.3; a.size_y = 1.3; a.energy = 90; a.color = (0.92, 0.96, 1.0)
        o = bpy.data.objects.new("FluoL", a); bpy.context.collection.objects.link(o); o.location = (x, 4, 2.9)
    c["pinner"] = officer("Pinner", 47, seed=3, band=False)
    reader = officer("Reader", 38, seed=0, gender=0.0, band=False); c["reader"] = reader
    # the reader seated at the desk by the window, facing -X toward the room... reading a file
    zero(reader); reset_pose(reader); pose_sit(reader, lean=14)
    for sd, sg in (("L", 1), ("R", -1)):
        reach(reader, sd, Vector((-0.12 * sg, -0.42, 0.72)), Vector((sg * 0.6, 0.2, -0.6)))
    place(reader, (3.3 + 0.8, 3.6, 0), math.radians(-90))      # facing -X: the room, the desk in front of her
    hip = (reader.bone_head("upperleg01.L") + reader.bone_head("upperleg01.R")) / 2
    reader.arm.location.z += 0.52 - hip.z; bpy.context.view_layer.update()
    c["file"] = box("OpenFile", (3.55, 3.5, 0.775), (0.33, 0.45, 0.01), pbr("FilePaper", (0.88, 0.87, 0.82), 0.7))
    l = bpy.data.lights.new("DeskLampL", 'SPOT'); l.energy = 40; l.spot_size = math.radians(70); l.color = (1.0, 0.85, 0.6)
    lo = bpy.data.objects.new("DeskLampL", l); bpy.context.collection.objects.link(lo); lo.location = (3.3, 3.2, 1.2); point_at(lo, (3.3, 3.6, 0.77))
    # the listening post on the reader's desk: a reel-to-reel deck (two spools, tape across the heads, two VU meters)
    rec = Vector((3.2, 3.95, 0.76))
    body = pbr("DeckBody", (0.05, 0.05, 0.055), 0.4, 0.3)
    plate = brushed_metal("DeckPlate", (0.7, 0.7, 0.72))
    box("Deck", rec + Vector((0, 0, 0.07)), (0.36, 0.46, 0.14), body, bevel=0.01)
    box("DeckPlate", rec + Vector((0.02, 0, 0.142)), (0.3, 0.44, 0.004), plate)
    box("HeadBlock", rec + Vector((-0.1, 0, 0.155)), (0.05, 0.08, 0.025), body)
    c["spools"] = []
    reel_m = pbr("Reel", (0.75, 0.75, 0.78), 0.25, 1.0)
    tape_m = pbr("TapeM", (0.14, 0.08, 0.04), 0.45)
    for k in range(2):
        cpos = rec + Vector((0.05, -0.12 + 0.24 * k, 0.15))
        R = dd.Builder(f"Reel{k}")
        R.cyl((0, 0, 0.002), 0.095, 0.003, reel_m, verts=32).cyl((0, 0, 0.012), 0.095, 0.003, reel_m, verts=32)
        R.cyl((0, 0, 0.007), 0.05 + 0.02 * k, 0.008, tape_m, verts=32)            # the wound tape
        for q in range(3):
            a_ = q * 2 * math.pi / 3
            R.cyl((0.055 * math.cos(a_), 0.055 * math.sin(a_), 0.0135), 0.022, 0.002, pbr("ReelHole", (0.02, 0.02, 0.02), 0.6), verts=12)
        sp = R.done(cpos); c["spools"].append(sp)
    box("TapeRun", rec + Vector((-0.07, 0, 0.162)), (0.004, 0.3, 0.006), tape_m)
    for k in range(2):                                     # VU meters with a needle each
        vp = rec + Vector((-0.181, -0.08 + 0.16 * k, 0.08))
        box(f"VU{k}", vp, (0.004, 0.11, 0.06), emissive(f"VUE{k}", (1.0, 0.8, 0.45), 3.0))
        nd = box(f"Needle{k}", vp + Vector((-0.004, 0, -0.022)), (0.002, 0.003, 0.045), pbr("NeedleM", (0.05, 0.05, 0.05), 0.5))
        c.setdefault("needles", []).append(nd)
    hp = pbr("Headphones", (0.04, 0.04, 0.045), 0.5)
    H = dd.Builder("HeadPhones")                     # a padded band over the crown and two big ear cups
    for q in range(13):
        a_ = math.pi * q / 12
        H.box((0.095 * math.cos(a_), 0, 0.1 * math.sin(a_)), (0.03, 0.035, 0.03), hp, rot=(0, -a_ + math.pi / 2, 0))
    for sx in (-1, 1):
        H.cyl((sx * 0.1, 0, -0.01), 0.045, 0.035, hp, verts=24, rot=(0, math.radians(90), 0))
        H.cyl((sx * 0.08, 0, -0.01), 0.04, 0.012, pbr("EarPad", (0.12, 0.12, 0.13), 0.8), verts=24, rot=(0, math.radians(90), 0))
    c["headband"] = H.done((0, 0, -20))
    return c


def anim_listen(c, t):
    sec = t * DUR["listen"]
    for k, sp in enumerate(c["spools"]):
        sp.rotation_euler = (0, 0, -sec * (2.2 if k else 1.6))
    for k, nd in enumerate(c.get("needles", [])):
        nd.rotation_euler = (math.radians(35 * (0.4 + 0.3 * math.sin(sec * 7.0 + k) + 0.2 * math.sin(sec * 13.0 + 2 * k))), 0, 0)
    r = c["reader"]
    r.rot("head", (0, 1, 0), 3 * math.sin(sec * 0.4))
    hd = r.bone_head("head"); M = r.arm.matrix_world.to_3x3()
    c["headband"].location = hd + Vector((0, 0, 0.07)); c["headband"].rotation_euler = (0, 0, r.arm.rotation_euler.z)


def anim_pin(c, t):
    sec = t * DUR["pin"]
    h = c["pinner"]; zero(h); pose_walk(h, 0.0, stride=0.0, arm_swing=0.0)
    sp = Vector((-0.9, 7.85, 0)); place(h, sp, math.pi)          # facing the board (+Y)
    M = h.arm.matrix_world.to_3x3()
    u = ease(min(1.0, max(0.0, (sec - 1.5) / 2.0)))
    tgt = Vector((-0.6, 8.43, 1.95))
    hand = (h.bone_head("upperarm01.R") + Vector((0.1, 0.3, -0.35))).lerp(tgt + Vector((0, -0.03, 0)), u)
    reach(h, "R", hand, Vector((-0.5, -0.4, -0.6)))
    arms_relaxed_one_left(h)
    p = c["new_print"]; p.location = hand + Vector((0, 0.02, 0.05)) if u < 1 else tgt + Vector((0, 0.005, 0))
    p.rotation_euler = (math.radians(90), 0, 0)


def arms_relaxed_one_left(h):
    from sc_boutique import arms_relaxed_one
    arms_relaxed_one(h, "L")


def anim_read(c, t):
    sec = t * DUR["read"]
    r = c["reader"]; r.rot("head", (0, 1, 0), 3 * math.sin(sec * 0.4))
    f = c["file"]; f.rotation_euler = (0, 0, 0.03 * math.sin(sec * 0.3))


MOVES = {
    "listen": dict(kind="anim", dof=2.0, anim=anim_listen,
                   cam=lambda c, t: (Vector((2.3, 4.9, 1.45)).lerp(Vector((2.55, 4.7, 1.42)), ease(t)), Vector((3.8, 3.7, 1.05)), 32),
                   focus=lambda c, t: Vector((3.6, 3.8, 1.0))),
    "pin": dict(kind="anim", dof=None, anim=anim_pin, title=("Chapter Three", "A Little Cement", 24, 4.5 * 24),
                cam=lambda c, t: (Vector((2.6, 0.2, 2.1)).lerp(Vector((1.8, 2.4, 2.0)), ease(t)), Vector((-1.0, 8.4, 1.5)), 26)),
    "read": dict(kind="anim", dof=2.8, anim=anim_read,
                 cam=lambda c, t: (Vector((2.2, 2.0, 1.6)).lerp(Vector((2.45, 2.25, 1.55)), ease(t)), Vector((3.9, 3.6, 1.0)), 32),
                 focus=lambda c, t: Vector((4.0, 3.6, 1.2))),
}
