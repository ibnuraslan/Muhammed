"""Recolour and dress: Mom pink blouse + plum trousers + near-black bob; Kid green tee; police olive caps; eye fix on every rig.
blender -b work/chars.blend --python 02_dress.py -- work/dressed.blend"""
import bpy, bmesh, sys, math
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]
HERE = "/home/user/Muhammed/blender/FakeDrainRescue_v001/"
NONBONE = ("HelperGeometry", "JointCubes", "Left", "Right", "Mid", "body")
def mat(name, rgb, rough=0.6, sheen=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; P = m.node_tree.nodes.get("Principled BSDF")
    P.inputs["Base Color"].default_value = (*rgb, 1); P.inputs["Roughness"].default_value = rough
    if sheen: P.inputs["Sheen Weight"].default_value = sheen
    return m
def dominant_bone(v, names):
    best = None; bw = 0
    for g in v.groups:
        n = names.get(g.group, "")
        if n in NONBONE or n.startswith(("helper", "joint")): continue
        if g.weight > bw: bw = g.weight; best = n
    return best
TOP = ("spine", "clavicle", "shoulder", "breast", "pectoral", "upperarm", "lowerarm", "neck")
def split_suit(ob, top_mat, leg_mat, zcut):
    """faces dominated by upper-body bones above zcut -> top_mat, the rest -> leg_mat (solid colours, no texture)"""
    names = {g.index: g.name for g in ob.vertex_groups}
    ob.data.materials.clear(); ob.data.materials.append(leg_mat); ob.data.materials.append(top_mat)
    vt = [bool((lambda b: b and b.startswith(TOP))(dominant_bone(v, names))) and v.co.z > zcut for v in ob.data.vertices]
    n = 0
    for p in ob.data.polygons:
        p.material_index = 1 if sum(vt[i] for i in p.vertices) * 2 > len(p.vertices) else 0; n += p.material_index
    print("SPLIT", ob.name, n, "top faces of", len(ob.data.polygons))
def tint_group(ob, rgb):
    for m in ob.data.materials:
        trees = [m.node_tree] + [n.node_tree for n in m.node_tree.nodes if n.type == 'GROUP']
        for nt in trees:
            for nd in list(nt.nodes):
                if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
                    for lk in list(nd.outputs['Color'].links):
                        if lk.to_node.name.startswith("SkinTint"): continue
                        mx = nt.nodes.new('ShaderNodeMix'); mx.name = "SkinTint"; mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                        mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (*rgb, 1)
                        nt.links.new(nd.outputs['Color'], mx.inputs['A']); nt.links.new(mx.outputs['Result'], lk.to_socket)
                    print("TINT", ob.name, nd.image.name)
def eval_pts(ob):
    dg = bpy.context.evaluated_depsgraph_get(); e = ob.evaluated_get(dg)
    return [ob.matrix_world @ v.co for v in e.to_mesh().vertices]
def attach(o, rig, bone):
    R = bpy.data.objects[rig]; pb = R.pose.bones[bone]
    c = o.constraints.new('CHILD_OF'); c.target = R; c.subtarget = bone
    c.inverse_matrix = (R.matrix_world @ pb.matrix).inverted()

POS = {}
for o in bpy.data.objects:
    if o.type == 'ARMATURE': POS[o.name] = o.location.copy(); o.location = (0, 0, 0)
bpy.context.view_layer.update()

# ---- Mom: pink blouse, plum trousers, near-black short hair
suit = bpy.data.objects["Mom.female_casualsuit01"]
zc = bpy.data.objects["Mom"].data.bones["upperleg01.L"].head_local.z + 0.06
split_suit(suit, mat("Mom_PinkBlouse", (0.92, 0.36, 0.78), 0.55, sheen=0.3), mat("Mom_PlumTrousers", (0.42, 0.12, 0.42), 0.6, sheen=0.2), zc)
tint_group(bpy.data.objects["Mom.bob02"], (0.18, 0.13, 0.11))
sh = bpy.data.objects["Mom.shoes02"]; sh.data.materials.clear(); sh.data.materials.append(mat("Mom_Shoes", (0.12, 0.08, 0.1), 0.4))
# fringe parted off the eyes: hair vertices in front of the eyes are lifted to a line above the brows
R_ = bpy.data.objects["Mom"]; hb = bpy.data.objects["Mom.bob02"]
eL = R_.data.bones["eye.L"].head_local; eR = R_.data.bones["eye.R"].head_local
ez = (eL.z + eR.z) / 2; ey = (eL.y + eR.y) / 2; ex = abs(eL.x)
line = ez + 0.035; nfix = 0
co_sets = [hb.data.vertices] + ([k.data for k in hb.data.shape_keys.key_blocks] if hb.data.shape_keys else [])
for cs in co_sets:
    for v in cs:
        c = v.co
        if c.y < ey + 0.02 and abs(c.x) < ex + 0.05 and line - 0.12 < c.z < line:
            w = min(1.0, max(0.0, (ex + 0.05 - abs(c.x)) / 0.02))
            c.z = c.z + (line - c.z) * w; nfix += 1
print("FRINGE lifted", nfix, "eye z", round(ez, 3))
# ---- Kid: green tee, jeans kept
ks = bpy.data.objects["Kid.male_casualsuit04"]
zc = bpy.data.objects["Kid"].data.bones["upperleg01.L"].head_local.z + 0.03
names = {g.index: g.name for g in ks.vertex_groups}
ks.data.materials.append(mat("Kid_GreenTee", (0.35, 0.85, 0.12), 0.55, sheen=0.3)); mi = len(ks.data.materials) - 1
vt = [bool((lambda b: b and b.startswith(TOP))(dominant_bone(v, names))) and v.co.z > zc for v in ks.data.vertices]
for p in ks.data.polygons:
    if sum(vt[i] for i in p.vertices) * 2 > len(p.vertices): p.material_index = mi
# ---- police caps (olive crown + black peak), Child Of the head bone
def cap(rig, col):
    body = bpy.data.objects[rig + ".body"]
    top = max(eval_pts(body), key=lambda c: c.z)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0)
    c = bpy.context.object; c.name = rig + "_Cap"
    bm = bmesh.new(); bm.from_mesh(c.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.05], context='VERTS')
    for v in bm.verts:   # flat-topped police crown, a bit wider at the top
        if v.co.z > 0.55: v.co.z = 0.55 + (v.co.z - 0.55) * 0.2
        v.co.x *= 1.0 + 0.12 * max(0, v.co.z); v.co.y *= 1.0 + 0.12 * max(0, v.co.z)
    bm.to_mesh(c.data); bm.free()
    c.scale = (0.108, 0.122, 0.11); c.location = (top.x, top.y + 0.006, top.z - 0.085)
    c.modifiers.new("t", 'SOLIDIFY').thickness = 0.06
    c.data.materials.append(mat("CapOlive", (0.22, 0.24, 0.12), 0.55))
    for p in c.data.polygons: p.use_smooth = True
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=8, radius=1.0)
    b = bpy.context.object; b.name = rig + "_CapPeak"
    b.scale = (0.085, 0.065, 0.012); b.location = (top.x, top.y - 0.10, top.z - 0.075); b.rotation_euler = (math.radians(-14), 0, 0)
    b.data.materials.append(mat("CapPeak", (0.03, 0.03, 0.03), 0.3))
    band = bpy.data.objects.new(rig + "_CapBand", None)
    bpy.context.view_layer.update()
    for o in (c, b): attach(o, rig, "head")
for r in ("CopA", "CopB"): cap(r, None)
# ---- eye fix on every EnhancedEye group (idempotent)
for ng in list(bpy.data.node_groups):
    if ng.name.startswith("EnhancedEye") and "CorneaTransparentMix" not in ng.nodes:
        src = open(HERE + "scripts/eye_fix.py").read().replace('bpy.data.node_groups["EnhancedEye"]', 'bpy.data.node_groups["%s"]' % ng.name)
        exec(src, {"bpy": bpy, "sys": sys, "_NO_SAVE": True})
        print("EYEFIX", ng.name)
    elif ng.name.startswith("EnhancedEye"): print("EYEFIX already", ng.name)
for n, p in POS.items(): bpy.data.objects[n].location = p
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
