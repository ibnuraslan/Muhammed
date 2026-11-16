"""TenDimes characters: MPFB2 rigs re-used from our delivered packages, re-dressed.
blender -b --factory-startup --python 01_chars.py
Singer  = EscapeArtist Judge (elegant suit -> light-grey 1960s suit, white shirt, navy tie) + grey fedora (CC-BY model, Child Of head)
Son     = EscapeArtist Boy (casual suit, red tee + jeans)
Kidnap  = EscapeArtist Guard2 (dark charcoal jacket, bare head so the face reads)
Daughter= DrunkTrain WitA (elegant female suit -> black mourning dress)"""
import sys, os, math
import bpy, bmesh
from mathutils import Vector, Matrix
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "common.py")).read())
exec(open(PIPE + "/hand_poses.py").read())
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
EA = REPO + "/EscapeArtist_v010/EscapeArtist_v010_60fps.blend"
DT = REPO + "/DrunkTrain_v007/DrunkTrain_v007_60fps.blend"
SRC = [(EA, "Judge", "Singer"), (REPO + "/DonationBin_v009/DonationBin_v009_60fps.blend", "Shover", "Son"), (EA, "Guard2", "Kidnapper"), (DT, "WitA", "Daughter")]
RIGS = {}
for path, src, new in SRC:
    with bpy.data.libraries.load(path, link=False) as (df, dt):
        dt.objects = [n for n in df.objects if n == src or n.startswith(src + ".")]
    objs = [o for o in dt.objects if o is not None]
    rig = next(o for o in objs if o.type == 'ARMATURE' and o.name.split(".")[0] == src)
    kids = [o for o in objs if o.parent == rig and o.type == 'MESH']
    for o in [rig] + kids:
        sc.collection.objects.link(o); o.animation_data_clear()
        if o.type == 'MESH' and o.data.shape_keys: o.data.shape_keys.animation_data_clear()
        o.hide_render = o.hide_viewport = False
        o.constraints.clear() if o.type == 'MESH' else None
    for o in objs:
        if o not in kids and o is not rig: bpy.data.objects.remove(o, do_unlink=True)
    rig.name = new; rig.data.name = new
    for k in kids:
        k.name = new + "." + k.name.split(".", 1)[1]; k.data.name = k.name
    rig.location = (0, 0, 0); rig.rotation_euler = (0, 0, 0); rig.scale = (1, 1, 1)
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
    RIGS[new] = rig
    print("CHAR", new, "from", src, [k.name for k in kids])
bpy.ops.outliner.orphans_purge(do_recursive=True)

for r in RIGS.values():
    for k in r.children:
        if k.type != 'MESH': continue
        for sl in k.material_slots:
            if sl.material: sl.link = 'OBJECT' if sl.link == 'OBJECT' else sl.link; sl.material = sl.material.copy()

def MATS(o): return [sl.material for sl in o.material_slots if sl.material]

def principled(m):
    return next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)

def tint(m, mode, rgb, rough=None):
    """recolour a clothes texture: 'lum' = keep the texture's light/dark pattern but map it onto rgb (grey suit keeps white shirt);
    'flat' = plain colour"""
    nt = m.node_tree; P = principled(m)
    src = P.inputs['Base Color'].links[0].from_socket if P.inputs['Base Color'].links else None
    for l in list(P.inputs['Base Color'].links): nt.links.remove(l)
    if mode == 'flat' or src is None:
        P.inputs['Base Color'].default_value = (*rgb, 1)
    else:
        rgbbw = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(src, rgbbw.inputs[0])
        ramp = nt.nodes.new('ShaderNodeValToRGB'); nt.links.new(rgbbw.outputs[0], ramp.inputs[0])
        ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (*rgb, 1)
        ramp.color_ramp.elements[1].position = 1.0; ramp.color_ramp.elements[1].color = (*[min(1, c * 1.6) for c in rgb], 1)
        nt.links.new(ramp.outputs[0], P.inputs['Base Color'])
        m["ramp_node"] = ramp.name
    if rough is not None:
        for l in list(P.inputs['Roughness'].links): nt.links.remove(l)
        P.inputs['Roughness'].default_value = rough
    return P

def child(r, key): return next(k for k in r.children if key in k.name)

# ---- the singer's suit: elegantsuit01 texture = dark jacket + light shirt; map luminance so the jacket turns light grey
suit = child(RIGS["Singer"], "elegantsuit01")
for m in MATS(suit):
    nt = m.node_tree; P = principled(m)
    src = P.inputs['Base Color'].links[0].from_socket if P.inputs['Base Color'].links else None
    for l in list(P.inputs['Base Color'].links): nt.links.remove(l)
    bw = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(src, bw.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); nt.links.new(bw.outputs[0], ramp.inputs[0])
    e = ramp.color_ramp.elements
    e[0].position = 0.0; e[0].color = (0.13, 0.14, 0.16, 1)     # darkest folds of the jacket
    e[1].position = 0.30; e[1].color = (0.27, 0.29, 0.32, 1)    # jacket: light cool grey
    e3 = ramp.color_ramp.elements.new(0.55); e3.color = (0.85, 0.86, 0.88, 1)  # shirt: white
    nt.links.new(ramp.outputs[0], P.inputs['Base Color'])
    P.inputs['Roughness'].default_value = 0.6
    for l in list(P.inputs['Roughness'].links): nt.links.remove(l)
    m["suit_ramp"] = ramp.name
for m in MATS(child(RIGS["Singer"], "shoes")): tint(m, 'flat', (0.03, 0.025, 0.02), 0.35)

# ---- son: red tee + blue jeans (casualsuit03 diffuse is tee+jeans in one texture: tint by UV-free luminance would mix both,
# so leave the donor's own colours unless they are skin-like)
son_suit = child(RIGS["Son"], "casualsuit")
print("SON suit mats", [m.name for m in son_suit.data.materials])
# ---- kidnapper: charcoal jacket
for m in MATS(child(RIGS["Kidnapper"], "casualsuit")): tint(m, 'lum', (0.018, 0.02, 0.026), 0.6)
# ---- daughter: black dress
for m in MATS(child(RIGS["Daughter"], "elegantsuit")): tint(m, 'lum', (0.006, 0.006, 0.008), 0.6)
for m in MATS(child(RIGS["Daughter"], "shoes")): tint(m, 'flat', (0.02, 0.02, 0.02), 0.3)

# ---- daughter: dark-brown bob, fringe cleared off the eyes (delete hair verts in front of the eye line, below the brow)
hair = child(RIGS["Daughter"], "bob02")
for m in MATS(hair):
    hs = next(n for n in m.node_tree.nodes if n.type == 'HUE_SAT'); hs.inputs['Value'].default_value = 0.12; hs.inputs['Saturation'].default_value = 1.6
B = RIGS["Daughter"].data.bones; ez = B["eye.L"].head_local.z; ey = B["eye.L"].head_local.y
bm = bmesh.new(); bm.from_mesh(hair.data)
dl = [v for v in bm.verts if v.co.y < ey + 0.012 and v.co.z < ez + 0.045 and abs(v.co.x) < 0.075]
print("FRINGE delete", len(dl)); bmesh.ops.delete(bm, geom=dl, context='VERTS'); bm.to_mesh(hair.data); bm.free()

# ---- eye fix + elbow limits + hand limits
g = bpy.data.node_groups.get("EnhancedEye")
if g and not any(nd.name.startswith("CorneaTransparentMix") for nd in g.nodes):
    _NO_SAVE = True; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "eye_fix.py")).read())
for n, r in RIGS.items():
    eye = child(r, "high-poly")
    print("EYEMAT", n, [m.name for m in eye.data.materials])
    add_hand_limits(r)
    for s in "LR":
        lo = r.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(145)

# ---- fedora (CC-BY "Fedora Hat" by alexnoiseless), light grey with a black band, Child Of the head bone
def parent_to_bone(o, r, bone):
    Mw = o.matrix_world.copy(); o.parent = r; o.parent_type = 'BONE'; o.parent_bone = bone
    bpy.context.view_layer.update(); o.matrix_world = Mw

def head_metrics(r):
    body = child(r, ".body"); gi = body.vertex_groups["head"].index
    pts = [v.co.copy() for v in body.data.vertices if any(gg.group == gi and gg.weight > 0.5 for gg in v.groups)]
    xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
    return Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, 0)), max(xs) - min(xs), max(ys) - min(ys), max(zs)

before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=ASSETS + "/fedora.glb")
new = [o for o in bpy.data.objects if o not in before]
new_names = [o.name for o in new]
meshes = [o for o in new if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
for o in meshes:   # bake parent transforms in
    Mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = Mw
if len(meshes) > 1: bpy.ops.object.join()
hat = bpy.context.view_layer.objects.active; hat.name = "Singer.fedora"
for nm in new_names:
    o = bpy.data.objects.get(nm)
    if o is not None and o != hat: bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
# normalise: centre the crown base at origin; brim width ~ 0.36 m
vs = [v.co for v in hat.data.vertices]
mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs))); mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
print("HAT raw dims", mx - mn)
c, wx, wy, top = head_metrics(RIGS["Singer"])
sz = mx - mn
s = 0.355 / max(sz.x, sz.y)
for v in hat.data.vertices: v.co = (v.co - Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))) * s
# crown inner width must fit the head: estimate crown width at 40% height
vs = [v.co for v in hat.data.vertices]; H = max(v.z for v in vs)
band = [v for v in vs if 0.25 * H < v.z < 0.45 * H]
cw = max(v.x for v in band) - min(v.x for v in band) if band else 0.2
k = (wx * 1.06) / cw
print("HAT crown w", cw, "head w", wx, "scale fix", k)
for v in hat.data.vertices: v.co *= k
hat.location = (c.x, c.y + 0.005, top - 0.075)
hat.rotation_euler = (math.radians(-4), 0, 0)
mh = bpy.data.materials.new("M_Fedora"); mh.use_nodes = True; Ph = mh.node_tree.nodes["Principled BSDF"]
Ph.inputs['Base Color'].default_value = (0.36, 0.38, 0.41, 1); Ph.inputs['Roughness'].default_value = 0.8
mb = bpy.data.materials.new("M_FedoraBand"); mb.use_nodes = True; Pb = mb.node_tree.nodes["Principled BSDF"]
Pb.inputs['Base Color'].default_value = (0.02, 0.02, 0.025, 1); Pb.inputs['Roughness'].default_value = 0.5
hat.data.materials.clear(); hat.data.materials.append(mh); hat.data.materials.append(mb)
bpy.context.view_layer.update()
hz = [v.co.z for v in hat.data.vertices]; H = max(hz)
for p in hat.data.polygons:
    zc = sum(hat.data.vertices[i].co.z for i in p.vertices) / len(p.vertices)
    rr = max(math.hypot(hat.data.vertices[i].co.x, hat.data.vertices[i].co.y) for i in p.vertices)
    p.material_index = 1 if 0.10 * H < zc < 0.32 * H and abs(p.normal.z) < 0.7 and rr < 0.14 else 0
    p.use_smooth = True
parent_to_bone(hat, RIGS["Singer"], "head")
# singer's hair hidden under the hat would poke through the crown: hide hair (the hat covers the head in every shot)
for k in RIGS["Singer"].children:
    if k.type == 'MESH' and "short0" in k.name: k.hide_render = True; k.hide_viewport = True; print("HIDE hair", k.name)

# ---- breast pocket with a navy pocket-square edge on the singer's jacket (the dimes' pocket, used in every pocket shot)
body = child(RIGS["Singer"], ".body"); A = RIGS["Singer"].data.bones
chest_z = A["upperarm01.L"].head_local.z - 0.15
bpy.ops.mesh.primitive_cube_add(size=1)
ps = bpy.context.active_object; ps.name = "Singer.pocketsquare"; ps.scale = (0.075, 0.006, 0.012)
bpy.ops.object.transform_apply(scale=True)
ps.location = (A["upperarm01.L"].head_local.x - 0.07, 0, chest_z)
# put it on the jacket surface: ray from the front
dg = bpy.context.evaluated_depsgraph_get(); se = suit.evaluated_get(dg)
ok, loc, nrm, _ = se.ray_cast(Vector((ps.location.x, -1.0, chest_z)), Vector((0, 1, 0)))
print("POCKET ray", ok, loc)
if ok: ps.location = loc + Vector((0, -0.004, 0))
mp = bpy.data.materials.new("M_PocketSquare"); mp.use_nodes = True; Pp = mp.node_tree.nodes["Principled BSDF"]
Pp.inputs['Base Color'].default_value = (0.10, 0.18, 0.45, 1); Pp.inputs['Roughness'].default_value = 0.6
ps.data.materials.append(mp)
bev = ps.modifiers.new("bev", 'BEVEL'); bev.width = 0.003; bev.segments = 2
# tilt to the chest slope
ps.rotation_euler = (math.radians(-8), 0, math.radians(-6))
parent_to_bone(ps, RIGS["Singer"], "spine01" if "spine01" in A else "spine02")

for n, r in RIGS.items():
    print("RIG", n, tuple(round(d, 2) for d in r.dimensions), "head z", round(r.data.bones["head"].head_local.z, 3))
bpy.ops.wm.save_as_mainfile(filepath=BUILD + "/chars.blend")
print("CHARS_OK")
