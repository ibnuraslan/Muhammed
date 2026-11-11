"""Fit the CC-BY 'Male Body Muscular System' model inside Lad and skin it to his rig (exec'd at the end of 02_build_scene.py).
Scale to his height, swing its arms about the shoulders into his A-pose, then copy the body's bone weights (Data Transfer, nearest face)."""
import bpy, math
from mathutils import Vector, Matrix
body = bpy.data.objects["Lad.body"]; rig = bpy.data.objects["Lad"]
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(GLB, "muscles.glb"))
objs = [o for o in bpy.data.objects if o not in before]
bpy.ops.object.select_all(action='DESELECT')
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
for o in objs:
    if o.type != 'MESH': bpy.data.objects.remove(o, do_unlink=True)
ms = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in ms: o.select_set(True)
bpy.context.view_layer.objects.active = ms[0]
bpy.ops.object.make_single_user(object=True, obdata=True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
if len(ms) > 1: bpy.ops.object.join()
mus = bpy.context.view_layer.objects.active; mus.name = "XrayMuscles"
me = mus.data
# decimate to keep the file small
dm = mus.modifiers.new("dec", 'DECIMATE'); dm.ratio = 0.45
bpy.ops.object.modifier_apply(modifier="dec")
me = mus.data
V = [v.co.copy() for v in me.vertices]
mn = Vector([min(v[i] for v in V) for i in range(3)]); mx = Vector([max(v[i] for v in V) for i in range(3)])
B = rig.data.bones
head_top = B["head"].tail_local.z + 0.02
s = (head_top - 0.0) / (mx.z - mn.z) * 0.985
ctr = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
bodyc_y = sum(B[n].head_local.y for n in ("spine03", "spine02")) / 2
T = Matrix.Translation((0, bodyc_y - 0.02, 0.0)) @ Matrix.Scale(s, 4) @ Matrix.Translation(-ctr)
me.transform(T)
# arm swing: compare fingertip angle about the shoulder
for side, sx in (("L", 1), ("R", -1)):
    sh = B["upperarm01." + side].head_local
    tip = B["finger3-3." + side].tail_local
    vs = [v for v in me.vertices if v.co.x * sx > sh.x * sx + 0.02 and v.co.z < sh.z + 0.05]
    far = max(vs, key=lambda v: v.co.x * sx - 0.3 * v.co.z)
    a_m = math.atan2(sx * (far.co.x - sh.x), sh.z - far.co.z)
    a_l = math.atan2(sx * (tip.x - sh.x), sh.z - tip.z)
    d = a_l - a_m
    print("ARM", side, round(math.degrees(a_m), 1), round(math.degrees(a_l), 1))
    R = Matrix.Rotation(-sx * d, 3, 'Y')   # rotate about the shoulder (y axis)
    for v in me.vertices:
        rel = (v.co.x - sh.x) * sx
        if rel <= -0.03: continue
        w = min(1.0, (rel + 0.03) / 0.1)
        if v.co.z > sh.z + 0.12: w *= max(0.0, 1 - (v.co.z - sh.z - 0.12) / 0.06)
        p = sh + R @ (v.co - sh)
        v.co = v.co.lerp(p, w)
me.update()
# skin: copy bone weights from the body
for vg in body.vertex_groups:
    if vg.name in B and B[vg.name].use_deform: mus.vertex_groups.new(name=vg.name)
dt = mus.modifiers.new("wt", 'DATA_TRANSFER'); dt.object = body; dt.use_vert_data = True
dt.data_types_verts = {'VGROUP_WEIGHTS'}; dt.vert_mapping = 'POLYINTERP_NEAREST'
dt.layers_vgroup_select_src = 'ALL'; dt.layers_vgroup_select_dst = 'NAME'
rig.data.pose_position = 'REST'; bpy.context.view_layer.update()
bpy.context.view_layer.objects.active = mus
bpy.ops.object.datalayout_transfer(modifier="wt")
bpy.ops.object.modifier_apply(modifier="wt")
rig.data.pose_position = 'POSE'
mus.parent = rig
am = mus.modifiers.new("Armature", 'ARMATURE'); am.object = rig
for poly in me.polygons: poly.use_smooth = True
link(mus, "People")
print("MUSCLES fitted", len(me.vertices), "verts, scale", round(s, 4))
