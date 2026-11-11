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

EXPOSURE = 0.0
DUR = {"pin": 9.0, "read": 9.0}


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
        office_chair((x, y - 0.75 if rz == 0 else y + 0.75, 0), rz, fab, met)
        dd.model_h("binder_notebook", (x - 0.4, y, 0.76), 0.05, rot_z=0.3 * k)
        if k % 2 == 0:
            dd.model_h("desk_lamp_arm_01", (x + 0.5, y + 0.1, 0.76), 0.45, rot_z=2.5)
        for j in range(3):
            box("Folder", (x + 0.1, y - 0.05 + 0.02 * j, 0.77 + 0.012 * j), (0.25, 0.33, 0.01), pbr("FolderM", ((0.55, 0.42, 0.25), (0.2, 0.3, 0.5), (0.6, 0.15, 0.1))[j], 0.7), rot=(0, 0, 0.1 * j))
    for k in range(4):
        dd.model_h("drawer_cabinet", (-4.7, 6.2 + k * 0.55, 0), 1.3, rot_z=math.radians(90))
    dd.model_h("potted_plant_01", (4.5, 7.8, 0), 1.0)
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
    place(reader, (3.3 + 0.75, 3.6, 0), math.radians(90))
    hip = (reader.bone_head("upperleg01.L") + reader.bone_head("upperleg01.R")) / 2
    reader.arm.location.z += 0.52 - hip.z; bpy.context.view_layer.update()
    c["file"] = box("OpenFile", (3.35, 3.6, 0.775), (0.33, 0.45, 0.01), pbr("FilePaper", (0.88, 0.87, 0.82), 0.7))
    l = bpy.data.lights.new("DeskLampL", 'SPOT'); l.energy = 40; l.spot_size = math.radians(70); l.color = (1.0, 0.85, 0.6)
    lo = bpy.data.objects.new("DeskLampL", l); bpy.context.collection.objects.link(lo); lo.location = (3.3, 3.2, 1.2); point_at(lo, (3.3, 3.6, 0.77))
    return c


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
    "pin": dict(kind="anim", dof=None, anim=anim_pin, title=("Chapter Three", "A Little Cement", 24, 4.5 * 24),
                cam=lambda c, t: (Vector((2.6, 0.2, 2.1)).lerp(Vector((1.8, 2.4, 2.0)), ease(t)), Vector((-1.0, 8.4, 1.5)), 26)),
    "read": dict(kind="anim", dof=2.8, anim=anim_read,
                 cam=lambda c, t: (Vector((1.3, 6.0, 1.75)).lerp(Vector((1.6, 5.7, 1.7)), ease(t)), Vector((4.0, 3.6, 1.0)), 30),
                 focus=lambda c, t: Vector((4.0, 3.6, 1.2))),
}
