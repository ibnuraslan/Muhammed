"""Cast for B04, appended from our WW1Assassination_v007 package (MPFB characters with IK controls, hand limits and
the eye fix already applied; MakeHuman's asset server was down on Nov 15) plus the horse rig from the same film.
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

# ---------------------------------------------------------------- gunman (olive frock suit, moustache)
G, _ = char("Gunman", "Gunman", skip=())
tint(G, "elegantsuit", (0.95, 0.82, 0.45))
arch = None
if False:
  arch = append(["Archduke", "Moustache"] + ["Archduke.body"])
  for o in arch: CC.objects.link(o)
  bpy.context.view_layer.update()
  A = arch[0]; must = arch[1]
  A.animation_data_clear()
  for pb in A.pose.bones: pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
  bpy.context.view_layer.update()
  hA = A.matrix_world @ A.pose.bones["head"].matrix; hG = G.matrix_world @ G.pose.bones["head"].matrix
  rel = hA.inverted() @ must.matrix_world
  must.parent = None; must.matrix_world = hG @ rel
  must.name = "Gunman_Moustache"
  for o in arch[:1] + arch[2:]: bpy.data.objects.remove(o, do_unlink=True)
  bone_parent(must, G, "head")
G.location = (0, 0, 0)

# ---------------------------------------------------------------- president (black suit, top hat); only seen from behind
P, _ = char("NerveA", "President")
tint(P, "elegantsuit", (0.035, 0.035, 0.04))
P.location = (3, 0, 0); bpy.context.view_layer.update()
hat = glb_asset("tophat", CC, target_size=0.33, axis=0)
hat.scale = (1, 1, 1.35)   # stovepipe proportion
bpy.context.view_layer.update()
top = head_top(P)
hat.location = (top.x, top.y + 0.005, top.z - 0.075)
hat.name = "President_TopHat"
bpy.context.view_layer.update()
bone_parent(hat, P, "head")

# ---------------------------------------------------------------- stage actors (background, comedy scene)
AA, _ = char("Duchess", "ActorA", extras=["WideHat"])
tint(AA, "elegantsuit", (0.2, 0.8, 0.75))
wh = bpy.data.objects.get("WideHat")
if wh:
    wh.name = "ActorA_Hat"
AA.location = (6, 0, 0)
AB, _ = char("Bomber", "ActorB")
tint(AB, "elegantsuit", (1.3, 1.25, 1.1))
AB.location = (7, 0, 0)

# ---------------------------------------------------------------- soldiers (navy)
for i in range(3):
    S_, objs = char("Officer", "Soldier%d" % (i + 1), extras=["OfficerCap"])
    tint(S_, "elegantsuit", (0.06, 0.09, 0.26))
    cap = objs[-1]; cap.name = "Soldier%d_Cap" % (i + 1)
    for j, m in enumerate(cap.data.materials):
        m = m.copy(); cap.data.materials[j] = m
        bs = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bs: bs.inputs['Base Color'].default_value = (0.05, 0.07, 0.2, 1)
    S_.location = (9 + i, 0, 0)

# ---------------------------------------------------------------- horse
hs = append(["Horse_rig", "Horse_body"])
for o in hs:
    CC.objects.link(o); o.animation_data_clear(); o.hide_render = False; o.hide_viewport = False
hs[0].name = "Horse"; hs[1].name = "Horse_body"
for pb in hs[0].pose.bones: pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
hs[0].location = (14, 0, 0)
hb = hs[1]; hb.data.transform(Matrix.Diagonal((0.84, 1.0, 1.0, 1.0)))   # 16% narrower barrel so a rider's legs stay outside the body

for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        print("CHAR", o.name, [c.name for c in o.children], tuple(round(d, 2) for d in o.dimensions))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("CHARS_DONE")
