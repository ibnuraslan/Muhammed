"""Five MPFB rigs re-used from finished films, re-dressed for B11.
Worker  (victim, 2009)  <- BellyFat ShopperA : shirt -> neon yellow-green, jeans
Manager (store manager) <- RingBullet Owner  : dark suit
Detective               <- GoatOwner OffA    : shirt -> royal blue
ConA (contractor, logo) <- WaterTubes Hero   : top -> orange, jeans -> charcoal, hard hat, DA KRAS FILMS on the back
ConB (contractor)       <- DrunkTrain Worker : orange overalls, tee -> orange, hard hat
blender -b --python 01_chars.py"""
import bpy, sys, math, os, bmesh
from mathutils import Vector, Matrix
exec(open(os.path.dirname(os.path.abspath(__file__)) + "/common.py").read())
exec(open(PIPE + "/hand_poses.py").read())
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
SRC = [("BellyFat_v010", "ShopperA", "Worker"), ("RingBullet_v008", "Owner", "Manager"), ("GoatOwner_v009", "OffA", "Detective"),
       ("WaterTubes_v006", "Hero", "ConA"), ("DrunkTrain_v007", "Worker", "ConB")]
RIGS = {}
for f, src, new in SRC:
    p = REPO + "/" + f + "/" + f + "_60fps.blend"
    with bpy.data.libraries.load(p, link=False) as (fd, td):
        td.objects = [n for n in fd.objects if n == src or n.startswith(src + ".")]
    rig = None
    for o in td.objects:
        if o is None: continue
        bpy.context.scene.collection.objects.link(o)
        if o.type == 'ARMATURE' and o.name.split(".")[0] == src and rig is None: rig = o
    rig.name = new
    for o in [rig] + list(rig.children):
        if o.animation_data: o.animation_data_clear()
        o.hide_render = False; o.hide_viewport = False
        if o is not rig: o.name = new + "." + o.name.split(".", 1)[1]
    rig.constraints.clear(); rig.parent = None; rig.matrix_world = Matrix.Identity(4)
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    for o in rig.children:
        if o.type == 'MESH': o.data = o.data.copy()          # own mesh data (recolour masks)
    RIGS[new] = rig
    print("RIG", new, [c.name for c in rig.children], all(b in rig.pose.bones for b in ("IK_hand.L", "IK_foot.R", "Pole_elbow.L")))

def child(rig, key): return next(o for o in rig.children if key in o.name)
def dominant_bone(ob, v):
    rig = ob.parent; bn = {b.name for b in rig.data.bones}
    best = (None, 0)
    for g in v.groups:
        n = ob.vertex_groups[g.group].name
        if n in bn and g.weight > best[1]: best = (n, g.weight)
    return best[0] or ""
LOWER = ("pelvis", "upperleg", "lowerleg", "foot", "toe", "root")
def islands(ob):
    """vertex index -> island id (linked geometry); prints per-island stats"""
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
    isl = [-1] * len(bm.verts); k = 0
    for v0 in bm.verts:
        if isl[v0.index] >= 0: continue
        st = [v0]; isl[v0.index] = k
        while st:
            v = st.pop()
            for e in v.link_edges:
                w = e.other_vert(v)
                if isl[w.index] < 0: isl[w.index] = k; st.append(w)
        k += 1
    bm.free()
    for i in range(k):
        vs = [ob.data.vertices[j] for j in range(len(isl)) if isl[j] == i]
        arm = sum(1 for v in vs if dominant_bone(ob, v).startswith(("upperarm", "lowerarm", "clavicle", "shoulder")))
        print("ISL", ob.name, i, len(vs), "zmean", round(sum(v.co.z for v in vs) / len(vs), 2), "arm", arm)
    return isl
def make_mask(ob, fn, name="RecolMask"):
    """per-vertex 0/1 colour attribute: 1 where fn(dominant bone, vertex) is true"""
    a = ob.data.color_attributes.get(name) or ob.data.color_attributes.new(name, 'FLOAT_COLOR', 'POINT')
    n = 0
    for v in ob.data.vertices:
        m = 1.0 if fn(dominant_bone(ob, v), v) else 0.0; n += m
        a.data[v.index].color = (m, m, m, 1)
    return n
def recolour(ob, tint, name="RecolMask", keep=0.0):
    """base colour -> tint * shading(luminance of the original texture) where the mask is 1"""
    for m in ob.data.materials:
        m2 = m.copy(); ob.data.materials[list(ob.data.materials).index(m)] = m2
        nt = m2.node_tree
        P = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
        lk = next((l for l in nt.links if l.to_socket == P.inputs["Base Color"]), None)
        if lk is None: continue
        src = lk.from_socket
        at = nt.nodes.new("ShaderNodeVertexColor"); at.layer_name = name
        bw = nt.nodes.new("ShaderNodeRGBToBW"); nt.links.new(src, bw.inputs[0])
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.0; mr.inputs[2].default_value = 0.6
        mr.inputs[3].default_value = 0.55; mr.inputs[4].default_value = 1.05; nt.links.new(bw.outputs[0], mr.inputs[0])
        tn = nt.nodes.new("ShaderNodeMix"); tn.data_type = 'RGBA'; tn.blend_type = 'MULTIPLY'; tn.inputs[0].default_value = 1.0
        tn.inputs[6].default_value = (*tint, 1); nt.links.new(mr.outputs[0], tn.inputs[7])
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'
        nt.links.new(at.outputs["Color"], mx.inputs[0]); nt.links.new(src, mx.inputs[6]); nt.links.new(tn.outputs[2], mx.inputs[7])
        nt.links.new(mx.outputs[2], P.inputs["Base Color"])
        m2.name = ob.name + "_recol"

W = RIGS["Worker"]; sh = child(W, "casualsuit03")
I = islands(sh); up_i = {i for i in set(I) if sum(sh.data.vertices[j].co.z for j in range(len(I)) if I[j] == i) / I.count(i) > 1.15}
print("MASK Worker shirt", make_mask(sh, lambda b, v: I[v.index] in up_i))
recolour(sh, (0.62, 0.86, 0.06))
D = RIGS["Detective"]; sh = child(D, "casualsuit01")
print("MASK Detective shirt", make_mask(sh, lambda b, v: not b.startswith(LOWER) and v.co.z > 0.93))
recolour(sh, (0.10, 0.25, 0.85))
A = RIGS["ConA"]; top = child(A, "casualsuit02")
print("MASK ConA all", make_mask(top, lambda b, v: True))
# top orange / jeans charcoal: two masks
up = top.data.color_attributes.new("UpMask", 'FLOAT_COLOR', 'POINT')
I = islands(top); up_i = {i for i in set(I) if sum(top.data.vertices[j].co.z for j in range(len(I)) if I[j] == i) / I.count(i) > 1.15}
for v in top.data.vertices:
    m = 1.0 if I[v.index] in up_i else 0.0; up.data[v.index].color = (m, m, m, 1)
lo = top.data.color_attributes["RecolMask"]
for v in top.data.vertices:
    m = 1.0 - up.data[v.index].color[0]; lo.data[v.index].color = (m, m, m, 1)
recolour(top, (0.16, 0.17, 0.19), "RecolMask")          # jeans -> charcoal work trousers
recolour(top, (1.0, 0.36, 0.03), "UpMask")              # top -> safety orange
B = RIGS["ConB"]; ov = child(B, "worksuit01")
I = islands(ov); tee_i = {i for i in set(I) if sum(1 for j in range(len(I)) if I[j] == i and dominant_bone(ov, ov.data.vertices[j]).startswith(("upperarm", "lowerarm"))) > 200}
print("MASK ConB tee", make_mask(ov, lambda b, v: I[v.index] in tee_i))
recolour(ov, (1.0, 0.40, 0.05))

# ---- hard hats (Sketchfab CC-BY, Kristiyan Marinov): Child Of the head bone, rim at the forehead
def import_glb(path, name):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]; meshes = [o for o in new if o.type == 'MESH']
    for o in meshes:
        M = o.matrix_world.copy(); o.parent = None; o.matrix_world = M
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in new:
        if o != ob and o.name in bpy.data.objects: bpy.data.objects.remove(o, do_unlink=True)
    ob.name = name; return ob
hat_src = import_glb(MODELS + "/hardhat.glb", "HardHatSrc")
_vs = [v.co for v in hat_src.data.vertices]; _zm = sum(v.z for v in _vs) / len(_vs); _z0 = min(v.z for v in _vs); _z1 = max(v.z for v in _vs)
if False:                          # model is already dome-up
    hat_src.data.transform(Matrix.Rotation(math.pi, 4, 'Y')); print("HAT flipped")
_vs = [v.co for v in hat_src.data.vertices]; _z0 = min(v.z for v in _vs); _z1 = max(v.z for v in _vs)
_low = [v for v in _vs if v.z < _z0 + 0.25 * (_z1 - _z0)]; _hi = [v for v in _vs if v.z > _z0 + 0.6 * (_z1 - _z0)]
_ly = sum(v.y for v in _low) / len(_low); _hy = sum(v.y for v in _hi) / len(_hi); _lx = sum(v.x for v in _low) / len(_low); _hx = sum(v.x for v in _hi) / len(_hi)
print("HAT brim offset", round(_lx - _hx, 3), round(_ly - _hy, 3))
if abs(_lx - _hx) > abs(_ly - _hy):
    hat_src.data.transform(Matrix.Rotation(-math.pi / 2 if _lx > _hx else math.pi / 2, 4, 'Z'))
    _ly = 0.0
_vs = [v.co for v in hat_src.data.vertices]; _low = [v for v in _vs if v.z < _z0 + 0.25 * (_z1 - _z0)]; _hi = [v for v in _vs if v.z > _z0 + 0.6 * (_z1 - _z0)]
if sum(v.y for v in _low) / len(_low) > sum(v.y for v in _hi) / len(_hi):
    hat_src.data.transform(Matrix.Rotation(math.pi, 4, 'Z')); print("HAT turned brim to -Y")
hat_src.data.update()
bb = [v.co.copy() for v in hat_src.data.vertices]; mn = Vector([min(p[i] for p in bb) for i in range(3)]); mx_ = Vector([max(p[i] for p in bb) for i in range(3)])
print("HAT dims", tuple(round(x, 3) for x in (mx_ - mn)))
hm = bpy.data.materials.new("HardHat_Yellow"); hm.use_nodes = True
Pn = hm.node_tree.nodes["Principled BSDF"]; Pn.inputs["Base Color"].default_value = (1.0, 0.72, 0.02, 1); Pn.inputs["Roughness"].default_value = 0.38
hat_src.data.materials.clear(); hat_src.data.materials.append(hm)
for nm in ("ConA", "ConB"):
    rig = RIGS[nm]; body = child(rig, ".body")
    hb = rig.data.bones["head"]
    hv = [v.co for v in body.data.vertices if dominant_bone(body, v) in ("head",) ]
    top_z = hb.tail_local.z; xs = [v.x for v in hv]; ys = [v.y for v in hv]
    cx = hb.head_local.x; cy = hb.head_local.y - 0.005; wid = max(xs) - min(xs); dep = max(ys) - min(ys)
    hat = hat_src.copy(); hat.data = hat_src.data.copy(); bpy.context.scene.collection.objects.link(hat); hat.name = nm + "_HardHat"
    # model: find which axis is the brim front; assume +Z up after import; scale crown width to head width * 1.25
    d = mx_ - mn; s = (wid * 1.20) / min(d.x, d.y)
    hat.scale = (s, s, s)
    # hat bottom sits 9 cm below the head top
    hat.location = Vector((cx, cy + 0.005, top_z - 0.065)) - Vector(((mn.x + mx_.x) / 2, (mn.y + mx_.y) / 2, mn.z)) * s
    print("HAT", nm, "head w", round(wid, 3), "dep", round(dep, 3), "top", round(top_z, 3), "scale", round(s, 3))
    bpy.context.view_layer.update(); Mw = hat.matrix_world.copy()
    hat.parent = rig; hat.parent_type = 'BONE'; hat.parent_bone = "head"
    pbh = rig.pose.bones["head"]
    P = rig.matrix_world @ pbh.matrix @ Matrix.Translation((0, pbh.bone.length, 0))
    hat.matrix_parent_inverse = P.inverted(); hat.matrix_basis = Mw; bpy.context.view_layer.update()
    print("HAT world z", round(hat.matrix_world.translation.z, 3))
bpy.data.objects.remove(hat_src, do_unlink=True)
# hair under the hard hats: hidden (the hat covers the crown; short sides read as cropped hair)
# ---- Detective fringe: lift fringe verts that hang over the eyes (both eyes must read)
hair = child(D, "short03"); body = child(D, ".body")
eye_z = D.data.bones["eye.L"].head_local.z; fy = min(v.co.y for v in body.data.vertices if v.co.z > eye_z - 0.02)
n = 0
for v in hair.data.vertices:
    if v.co.z < eye_z + 0.055 and v.co.y < fy + 0.07:
        dz = (eye_z + 0.055) - v.co.z; v.co.z += dz; v.co.y -= 0.004; n += 1
print("FRINGE lifted", n)

# ---- DA KRAS FILMS logo on ConA's back (white on orange), shrink-wrapped + skinned
logo = bpy.data.images.load(REPO + "/assets/brand/DaKrasFilms_logo_white.png"); logo.name = "DaKrasFilms_logo_white"
w = 0.30; h = w * 414 / 967
zc = A.data.bones["upperarm01.L"].head_local.z - 0.17
bpy.ops.mesh.primitive_grid_add(x_subdivisions=34, y_subdivisions=16, size=1)
dec = bpy.context.active_object; dec.name = "ConA_BackLogo"
dec.scale = (w, h, 1); dec.rotation_euler = (math.radians(90), 0, math.radians(180)); dec.location = (0, 0.5, zc)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
sw = dec.modifiers.new("sw", 'SHRINKWRAP'); sw.target = top; sw.wrap_method = 'PROJECT'
sw.use_project_y = True; sw.use_negative_direction = True; sw.use_positive_direction = True; sw.offset = 0.004
bpy.context.view_layer.objects.active = dec; bpy.ops.object.modifier_apply(modifier="sw")
dt = dec.modifiers.new("dt", 'DATA_TRANSFER'); dt.object = top; dt.use_vert_data = True
dt.data_types_verts = {'VGROUP_WEIGHTS'}; dt.vert_mapping = 'POLYINTERP_NEAREST'
bpy.ops.object.datalayout_transfer(modifier="dt"); bpy.ops.object.modifier_apply(modifier="dt")
dec.parent = A; am = dec.modifiers.new("Armature", 'ARMATURE'); am.object = A
dm = bpy.data.materials.new("BackLogo"); dm.use_nodes = True; nt = dm.node_tree; nt.nodes.clear()
o = nt.nodes.new("ShaderNodeOutputMaterial"); t = nt.nodes.new("ShaderNodeTexImage"); t.image = logo; t.extension = 'CLIP'
pr = nt.nodes.new("ShaderNodeBsdfPrincipled"); pr.inputs["Roughness"].default_value = 0.7
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mxs = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(t.outputs["Color"], pr.inputs["Base Color"]); nt.links.new(t.outputs["Alpha"], mxs.inputs[0])
nt.links.new(tr.outputs[0], mxs.inputs[1]); nt.links.new(pr.outputs[0], mxs.inputs[2]); nt.links.new(mxs.outputs[0], o.inputs[0])
dec.data.materials.append(dm)
print("LOGO back y", round(max(v.co.y for v in dec.data.vertices), 3), "z", round(zc, 3))

# ---- eye fix, hand limits, open elbows
EYE_SRC = open(V + "/scripts/eye_fix.py").read().replace('g = bpy.data.node_groups["EnhancedEye"]; nt = g', 'g = _G; nt = g')
for _G in [g for g in bpy.data.node_groups if g.name.startswith("EnhancedEye")]:
    if "CorneaTransparentMix" in _G.nodes: print("EYEFIX already", _G.name); continue
    _NO_SAVE = True; exec(EYE_SRC); print("EYEFIX", _G.name)
for i, rig in enumerate(RIGS.values()):
    add_hand_limits(rig)
    for s in "LR":
        lo_ = rig.pose.bones["lowerarm01." + s]; lo_.use_ik_limit_x = True; lo_.ik_min_x = math.radians(-40); lo_.ik_max_x = math.radians(145)
    rig.location = (i * 1.0, 0, 0)
for g in bpy.data.node_groups: 
    if "Eye" in g.name: print("NG", g.name, g.users)
bpy.ops.wm.save_as_mainfile(filepath=BUILD + "/chars.blend")
