"""Cast for B12 IronRodHead, appended from our WW1Assassination_v007 package (MPFB characters with IK controls, hand limits and
the eye fix already applied; MakeHuman's asset server was down on Nov 15) .
blender -b --factory-startup --python 01_chars.py -- <out.blend>"""
import sys, os
import bpy
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "00_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 60; sc.render.resolution_x = 1080; sc.render.resolution_y = 1920
CC = coll("Cast")

def append(names):
    with bpy.data.libraries.load(WW1, link=False) as (src, dst):
        dst.objects = list(names)
    return dst.objects

def char(src, new, extras=(), skip=()):
    with bpy.data.libraries.load(WW1, link=False) as (s, d):
        kids = [n for n in s.objects if n.startswith(src + ".")]
    objs = append([src] + [k for k in kids if k.split(".", 1)[1] not in skip] + list(extras))
    rig = objs[0]
    for o in objs:
        CC.objects.link(o)
        o.animation_data_clear()
        if o.type == 'MESH' and o.data.shape_keys: o.data.shape_keys.animation_data_clear()
        o.hide_render = False; o.hide_viewport = False
        if o is not rig and o.name.startswith(src): o.name = new + o.name[len(src):].split(".001")[0]
    rig.name = new; rig.data.name = new
    rig.location = (0, 0, 0); rig.rotation_euler = (0, 0, 0)
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
    for s in "LR":   # open the elbow IK limit (MPFB rests at ~46 deg; min 0 kept arms in an A-pose)
        pb = rig.pose.bones["lowerarm01." + s]; pb.use_ik_limit_x = True; pb.ik_min_x = -0.75; pb.ik_max_x = 2.53
    for o in objs:   # drop other films' actions on the meshes (visibility keys etc.)
        if o.type == 'MESH':
            for m in o.modifiers:
                if m.type == 'ARMATURE': m.object = rig
    return rig, objs

def tint(rig, key, rgb):
    for ch in rig.children:
        if ch.type == 'MESH' and key in ch.name:
            for i, m in enumerate(ch.data.materials):
                m = m.copy(); ch.data.materials[i] = m
                nt = m.node_tree
                mx = next((n for n in nt.nodes if n.type == 'MIX' and n.blend_type == 'MULTIPLY'), None)
                if mx is None:
                    for nd in list(nt.nodes):
                        if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                            for lk in list(nd.outputs['Color'].links):
                                mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                                mx.inputs['Factor'].default_value = 1.0
                                nt.links.new(nd.outputs['Color'], mx.inputs['A']); nt.links.new(mx.outputs['Result'], lk.to_socket)
                            break
                if mx is not None:
                    mx.inputs['B'].default_value = (*rgb, 1)
                    hsv = next((n for n in nt.nodes if n.type == 'HUE_SAT'), None)
                    if hsv:   # WW1 chain Mix.001 -> Mix -> diffuseIntensity -> HSV overrode the tint; feed HSV directly
                        nt.links.new(mx.outputs['Result'], hsv.inputs['Color'])
                else:
                    bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); bs.inputs['Base Color'].default_value = (*rgb, 1)

def head_top(rig):
    body = next(c for c in rig.children if c.name.endswith(".body"))
    dg = bpy.context.evaluated_depsgraph_get(); e = body.evaluated_get(dg)
    vs = [body.matrix_world @ v.co for v in e.data.vertices]
    return max(vs, key=lambda v: v.z)

def bone_parent(o, rig, bone):
    mw = o.matrix_world.copy()
    o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = bone
    bpy.context.view_layer.update()
    o.matrix_world = mw


# ---------------------------------------------------------------- Gage: the railroad foreman (work shirt + trousers, worksuit tinted denim blue)
G, _ = char("Driver", "Gage")
tint(G, "worksuit", (0.42, 0.58, 0.95))
G.location = (0, 0, 0)
# co-workers (period suits: brown waistcoat suit + felt hat, olive work suit)
WB, _ = char("NerveB", "WorkerB")
tint(WB, "elegantsuit", (0.78, 0.52, 0.30))
WB.location = (3, 0, 0)
WC, _ = char("Officer", "WorkerC")
tint(WC, "elegantsuit", (0.50, 0.62, 0.36))
WC.location = (6, 0, 0)
# background workers for the wide shots (low-poly crowd rigs, hats, clearly clothed)
E1, _ = char("CrowdM1", "ExtraA"); tint(E1, "elegantsuit", (0.55, 0.55, 0.62)); E1.location = (9, 0, 0)
E2, _ = char("CrowdM3", "ExtraB"); tint(E2, "worksuit", (0.85, 0.45, 0.30)); E2.location = (12, 0, 0)
for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        print("CHAR", o.name, [c.name for c in o.children], tuple(round(d, 2) for d in o.dimensions))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("CHARS_DONE")
