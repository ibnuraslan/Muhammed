"""Thumbnail sets for the $25M Drain v3 ideas.
  velvet: a jeweller's display, the same brilliant on a velvet cushion under show lights (left half of the split)
  grate:  looking down through a street drain grate at night; a flashlight finds the diamond in the black water below"""
import math
import bpy, bmesh
from mathutils import Vector
from kit import pbr, box
import ph
import sc_tdrain as D

EXPOSURE = 0.0
BOUNCES = 16


def _black_world():
    w = bpy.context.scene.world or bpy.data.worlds.new("W"); bpy.context.scene.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]; bg.inputs['Color'].default_value = (0, 0, 0, 1); bg.inputs['Strength'].default_value = 0.0


def _rounded(name, loc, size, mat, bevel):
    o = box(name, loc, size, mat, bevel=bevel); o.modifiers["bevel"].segments = 6
    s = o.modifiers.new("sub", 'SUBSURF'); s.levels = 2; s.render_levels = 3
    bpy.ops.object.shade_smooth(); return o


def velvet():
    _black_world(); c = {}
    vel = ph.texture("velour_velvet", scale=6, tint=(0.018, 0.02, 0.04))
    p = vel.node_tree.nodes["Principled BSDF"]; p.inputs['Sheen Weight'].default_value = 0.45; p.inputs['Sheen Roughness'].default_value = 0.35
    p.inputs['Sheen Tint'].default_value = (0.35, 0.38, 0.5, 1)
    # plinth, cushion on it, a curved backdrop
    blk = pbr("BlackLacquer", (0.008, 0.008, 0.01), 0.3); bp_ = blk.node_tree.nodes["Principled BSDF"]
    bp_.inputs['Coat Weight'].default_value = 1.0; bp_.inputs['Coat Roughness'].default_value = 0.04
    _rounded("Plinth", (0, 0, 0.09), (0.5, 0.42, 0.18), blk, 0.006)
    cu = _rounded("Cushion", (0, 0, 0.18 + 0.03), (0.26, 0.24, 0.07), vel, 0.03)
    back = pbr("Backdrop", (0.02, 0.025, 0.06), 0.6)
    # an old brick wall behind the display, dark, picked out by the light from above
    bw = ph.texture("red_brick_03", scale=2.6, tint=(0.42, 0.38, 0.38))
    bwn = [n for n in bw.node_tree.nodes if n.type == 'NORMAL_MAP']
    if bwn: bwn[0].inputs['Strength'].default_value = 2.0
    next(n for n in bw.node_tree.nodes if n.type == 'MAPPING').inputs['Rotation'].default_value = (0, 0, math.pi / 2)   # courses horizontal
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 1.4, 0.8), rotation=(math.pi / 2, 0, 0)); b = bpy.context.active_object
    b.scale = (6, 3, 1); b.data.materials.append(bw)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.5, 0.0)); f = bpy.context.active_object; f.scale = (6, 4, 1); f.data.materials.append(back)
    top = Vector((0, 0, 0.18 + 0.065))
    d = D.diamond("Diamond", 0.055); d.location = top + Vector((0, 0, 0.055 * 0.86 - 0.012)); d.rotation_euler = (math.radians(-10), math.radians(4), 0.2)
    c["diamond"] = d; c["back"] = b
    return c


def _rusty_iron(name):
    m = pbr(name, (0.03, 0.025, 0.022), 0.55, 0.6)
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); n = N.new("ShaderNodeTexNoise"); n.inputs['Scale'].default_value = 30; n.inputs['Detail'].default_value = 10
    L.new(tc.outputs['Object'], n.inputs['Vector'])
    r = N.new("ShaderNodeValToRGB"); e = r.color_ramp.elements
    e[0].position = 0.5; e[0].color = (0.018, 0.016, 0.015, 1); e[1].position = 0.75; e[1].color = (0.09, 0.035, 0.015, 1)
    L.new(n.outputs['Fac'], r.inputs[0]); L.new(r.outputs[0], p.inputs['Base Color'])
    mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.45; mr.inputs['From Max'].default_value = 0.7
    mr.inputs['To Min'].default_value = 0.7; mr.inputs['To Max'].default_value = 0.0
    L.new(n.outputs['Fac'], mr.inputs['Value']); L.new(mr.outputs['Result'], p.inputs['Metallic'])
    p.inputs['Coat Weight'].default_value = 0.6; p.inputs['Coat Roughness'].default_value = 0.1      # rain-wet
    return m


GW, GL = 0.70, 0.46          # the opening in the road (x, y)
DEPTH = 0.75


def grate():
    _black_world(); c = {}
    road = ph.texture("asphalt_02", scale=1.4, tint=(0.16, 0.16, 0.17))
    p = road.node_tree.nodes["Principled BSDF"]; p.inputs['Coat Weight'].default_value = 0.85; p.inputs['Coat Roughness'].default_value = 0.06
    # the road around the opening: four slabs
    for nm, (x0, x1, y0, y1) in {"RoadL": (-3, -GW / 2, -3, 3), "RoadR": (GW / 2, 3, -3, 3),
                                 "RoadF": (-GW / 2, GW / 2, -3, -GL / 2), "RoadB": (-GW / 2, GW / 2, GL / 2, 3)}.items():
        box(nm, ((x0 + x1) / 2, (y0 + y1) / 2, -0.05), (x1 - x0, y1 - y0, 0.1), road)
    iron = _rusty_iron("Iron")
    fw = 0.045                                        # cast frame
    box("FrameF", (0, -GL / 2 - fw / 2 + 0.01, 0.001), (GW + 2 * fw, fw, 0.03), iron, bevel=0.004)
    box("FrameB", (0, GL / 2 + fw / 2 - 0.01, 0.001), (GW + 2 * fw, fw, 0.03), iron, bevel=0.004)
    box("FrameL", (-GW / 2 - fw / 2 + 0.01, 0, 0.001), (fw, GL, 0.03), iron, bevel=0.004)
    box("FrameR", (GW / 2 + fw / 2 - 0.01, 0, 0.001), (fw, GL, 0.03), iron, bevel=0.004)
    n = 11; pitch = GW / n
    for k in range(n - 1):                            # bars run away from the camera, so we look down between them
        box(f"Bar{k}", (-GW / 2 + pitch * (k + 1), 0, -0.012), (0.022, GL, 0.05), iron, bevel=0.003)
    box("Cross", (0, 0, -0.03), (GW, 0.02, 0.03), iron, bevel=0.003)
    # the shaft: old brick walls down to black water, rubble in it
    wall = ph.texture("brick_wall_02", scale=2.2, tint=(0.3, 0.26, 0.23))
    pw = wall.node_tree.nodes["Principled BSDF"]; pw.inputs['Coat Weight'].default_value = 0.7; pw.inputs['Coat Roughness'].default_value = 0.12
    sw, sl = GW + 0.5, GL + 0.9
    for nm, loc, size in (("WallL", (-sw / 2, 0.2, -DEPTH / 2 - 0.03), (0.05, sl, DEPTH)), ("WallR", (sw / 2, 0.2, -DEPTH / 2 - 0.03), (0.05, sl, DEPTH)),
                          ("WallB", (0, 0.2 + sl / 2, -DEPTH / 2 - 0.03), (sw, 0.05, DEPTH)), ("WallF", (0, 0.2 - sl / 2, -DEPTH / 2 - 0.03), (sw, 0.05, DEPTH))):
        box(nm, loc, size, wall)
    box("Ceiling", (0, 0.2, -0.1), (sw, sl, 0.02), pbr("Under", (0.01, 0.01, 0.01), 0.9)).hide_render = True
    water = pbr("Water", (0.003, 0.004, 0.004), 0.04); water.node_tree.nodes["Principled BSDF"].inputs['Coat Weight'].default_value = 1.0
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.2, -DEPTH)); wa = bpy.context.active_object; wa.scale = (sw, sl, 1); wa.data.materials.append(water)
    mats = [D.real_brick_mat(f"Brick{k}", (0.5 + 0.06 * k, 0.36 + 0.03 * k, 0.33), k) for k in range(3)]
    D.brick("R0", (0.02, 0.06, -DEPTH + 0.02), (0.15, 0, 0.3), mats[0])
    D.brick("R1", (-0.2, 0.2, -DEPTH + 0.01), (0, 0.4, 1.2), mats[1])
    D.brick("R2", (0.22, 0.3, -DEPTH + 0.015), (0.3, 0, -0.5), mats[2])
    top = Vector((0.02, 0.06, -DEPTH + 0.02 + 0.04))
    d = D.diamond("Diamond", 0.09); d.location = top + Vector((0, 0, 0.09 * 0.86 - 0.012)); d.rotation_euler = (math.radians(-28), math.radians(8), 0.3)
    c["diamond"] = d
    rats = []
    for loc, rz, s in (((-0.3, 0.42, -DEPTH), -0.6, 1.8), ((0.33, -0.05, -DEPTH), 2.4, 1.7)):
        try:
            rats.append(ph.model("street_rat", loc=loc, rot_z=rz, scale=s))
        except Exception as e:
            print("rat failed", e)
    c["rats"] = rats
    return c


def build(variant=None):
    return velvet() if variant == "velvet" else grate()


MOVES = {}
