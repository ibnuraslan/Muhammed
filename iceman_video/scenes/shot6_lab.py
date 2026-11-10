"""Shot 6 - The mummy on the perforated steel table in the cold lab."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from mathutils import Vector
from common import *
from human import lay_down, evaluated_bounds, settle, bake_pose, flatten_contact
from mummy import build_mummy

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
OUT = arg('--out', '/tmp/shot6'); FRAMES = arg('--frames', 1); STEP = arg('--step', 1)
s = reset(samples=arg('--samples', 48), exposure=-0.3)
s.cycles.max_bounces = 8

TABLE_Z = 0.88
# ---------------------------------------------------------------- table
def steel(name, perforated=False, aniso=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    p.inputs['Metallic'].default_value = 1.0
    p.inputs['Base Color'].default_value = (0.55, 0.57, 0.6, 1)
    p.inputs['Anisotropic'].default_value = aniso
    # brushed streaks + smudges
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (1, 300, 1)
    L.new(tc.outputs['Object'], mp.inputs['Vector'])
    br = N.new("ShaderNodeTexNoise"); br.inputs['Scale'].default_value = 4; br.inputs['Detail'].default_value = 6
    L.new(mp.outputs[0], br.inputs['Vector'])
    sm = N.new("ShaderNodeTexNoise"); sm.inputs['Scale'].default_value = 3; sm.inputs['Detail'].default_value = 5
    L.new(tc.outputs['Object'], sm.inputs['Vector'])
    rr = N.new("ShaderNodeMath"); rr.operation = 'MULTIPLY_ADD'; rr.inputs[1].default_value = 0.25
    L.new(sm.outputs['Fac'], rr.inputs[0]); rr.inputs[2].default_value = 0.30
    rr2 = N.new("ShaderNodeMath"); rr2.operation = 'MULTIPLY_ADD'; rr2.inputs[1].default_value = 0.12
    L.new(br.outputs['Fac'], rr2.inputs[0]); L.new(rr.outputs[0], rr2.inputs[2])
    L.new(rr2.outputs[0], p.inputs['Roughness'])
    if perforated:
        # grid of round holes (alpha cut-out), 18 mm holes on a 45 mm pitch
        sc = N.new("ShaderNodeVectorMath"); sc.operation = 'SCALE'; sc.inputs['Scale'].default_value = 1 / 0.045
        L.new(tc.outputs['Object'], sc.inputs[0])
        fr = N.new("ShaderNodeVectorMath"); fr.operation = 'FRACTION'; L.new(sc.outputs[0], fr.inputs[0])
        sub = N.new("ShaderNodeVectorMath"); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = (0.5, 0.5, 0)
        L.new(fr.outputs[0], sub.inputs[0])
        sep = N.new("ShaderNodeSeparateXYZ"); L.new(sub.outputs[0], sep.inputs[0])
        cxy = N.new("ShaderNodeCombineXYZ"); L.new(sep.outputs[0], cxy.inputs[0]); L.new(sep.outputs[1], cxy.inputs[1])
        ln = N.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; L.new(cxy.outputs[0], ln.inputs[0])
        hole = N.new("ShaderNodeMath"); hole.operation = 'GREATER_THAN'; hole.inputs[1].default_value = 0.2
        L.new(ln.outputs['Value'], hole.inputs[0])
        L.new(hole.outputs[0], p.inputs['Alpha'])
    return m

bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.75, TABLE_Z - 0.01))
top = bpy.context.active_object; top.scale = (0.78, 2.3, 0.012)
bpy.ops.object.transform_apply(scale=True)
bev = top.modifiers.new("b", 'BEVEL'); bev.width = 0.004; bev.segments = 2
top.data.materials.append(steel("Perf", perforated=True))
plain = steel("Steel", aniso=0.4)
for sx in (-1, 1):  # side rails
    bpy.ops.mesh.primitive_cube_add(size=1, location=(sx * 0.4, 0.75, TABLE_Z + 0.01))
    r = bpy.context.active_object; r.scale = (0.03, 2.32, 0.05); r.data.materials.append(plain)
    bv = r.modifiers.new("b", 'BEVEL'); bv.width = 0.006; bv.segments = 3
for sy in (-1, 1):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.75 + sy * 1.15, TABLE_Z + 0.01))
    r = bpy.context.active_object; r.scale = (0.83, 0.03, 0.05); r.data.materials.append(plain)
# drip tray under the perforations + pedestal
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.75, TABLE_Z - 0.09))
tray = bpy.context.active_object; tray.scale = (0.74, 2.2, 0.02); tray.data.materials.append(steel("Tray", aniso=0.2))
for y in (0.0, 1.5):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=TABLE_Z - 0.1, location=(0, y, (TABLE_Z - 0.1) / 2))
    bpy.context.active_object.data.materials.append(plain)

# ---------------------------------------------------------------- room
def flat(name, col, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    return m
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
floor = bpy.context.active_object
fm = flat("Floor", (0.05, 0.055, 0.06), 0.25)
nt = fm.node_tree; bt = nt.nodes.new("ShaderNodeTexBrick"); bt.inputs['Scale'].default_value = 1.6
bt.inputs['Color1'].default_value = (0.05, 0.055, 0.06, 1); bt.inputs['Color2'].default_value = (0.04, 0.045, 0.05, 1)
bt.inputs['Mortar'].default_value = (0.02, 0.022, 0.025, 1); bt.inputs['Mortar Size'].default_value = 0.004
nt.links.new(bt.outputs['Color'], nt.nodes["Principled BSDF"].inputs['Base Color'])
floor.data.materials.append(fm)
wall = flat("Wall", (0.06, 0.07, 0.08), 0.8)
bpy.ops.mesh.primitive_plane_add(size=1, location=(-2.6, 1.0, 1.6), rotation=(0, math.radians(90), 0))
w1 = bpy.context.active_object; w1.scale = (3.2, 12, 1); w1.data.materials.append(wall)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 4.2, 1.6), rotation=(math.radians(90), 0, 0))
w2 = bpy.context.active_object; w2.scale = (12, 3.2, 1); w2.data.materials.append(wall)
# steel cabinets along the back wall with cold strip lights
cab = steel("Cab", aniso=0.3)
for k in range(5):
    x = -2.0 + k * 0.92
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 3.9, 1.0))
    c = bpy.context.active_object; c.scale = (0.88, 0.5, 2.0); c.data.materials.append(cab)
    bv = c.modifiers.new("b", 'BEVEL'); bv.width = 0.01; bv.segments = 2
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x + 0.3, 3.63, 1.05))
    hd = bpy.context.active_object; hd.scale = (0.02, 0.03, 0.35); hd.data.materials.append(plain)
strip = bpy.data.materials.new("Strip"); strip.use_nodes = True
sp = strip.node_tree.nodes["Principled BSDF"]; sp.inputs['Emission Color'].default_value = (0.55, 0.8, 1.0, 1); sp.inputs['Emission Strength'].default_value = 6
bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.2, 3.62, 2.05)); st = bpy.context.active_object; st.scale = (4.6, 0.02, 0.025); st.data.materials.append(strip)

# ---------------------------------------------------------------- the mummy
h = build_mummy()
lay_down(h, face_up=True, z=0.0)
h.arm.location = (0.09, 0.18, 0)
settle(h, TABLE_Z - 0.012)
bake_pose(h)
flatten_contact(h.body, TABLE_Z + 0.001, band=0.11, squash=0.18)

# ---------------------------------------------------------------- lights
world_flat((0.006, 0.010, 0.018), 1.0)
panel = area_light((0, 0.85, 2.35), (0, 0, 0), 1.0, 160, (0.80, 0.90, 1.0)); panel.data.shape = 'RECTANGLE'
panel.data.size = 0.7; panel.data.size_y = 1.6
rim = area_light((-1.6, 2.6, 1.5), (0, 0, 0), 0.8, 40, (0.45, 0.7, 1.0)); point_at(rim, (0, 1.0, TABLE_Z))
kick = area_light((1.8, -0.6, 1.2), (0, 0, 0), 1.2, 12, (0.6, 0.75, 1.0)); point_at(kick, (0, 0.6, TABLE_Z))

cam = camera((0, 0, 0), (0, 0, 0), lens=40, dof_dist=1.5, fstop=2.8)
head = h.bone_head("head")
feet = (h.bone_tail("foot.L") + h.bone_tail("foot.R")) / 2
print("head", head, "feet", feet)

def frame(i, t):
    e = ease(t)
    look = Vector(lerp(tuple(feet.lerp(head, 0.35)), tuple(feet.lerp(head, 0.8)), e)); look.z = TABLE_Z + 0.08
    cam.location = Vector(lerp((1.2, -0.5, 1.62), (1.0, 0.5, 1.5), e))
    point_at(cam, tuple(look))
    cam.data.dof.focus_distance = (cam.location - look).length

render_frames(OUT, frame, FRAMES, STEP)
