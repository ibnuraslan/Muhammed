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

# procedural fedora (classic shape): tapered crown with a centre crease and front pinches, plain dark band, snap brim
c, wx, wy, top = head_metrics(RIGS["Singer"])
rx, ry = wx / 2 * 1.16, wy / 2 * 1.12
CH = 0.135; NU = 64; NV = 14
bm = bmesh.new(); rings = []
for k in range(NV + 1):
    h = CH * k / NV; ring = []
    for i in range(NU):
        a = 2 * math.pi * i / NU; x = math.cos(a) * rx; y = math.sin(a) * ry
        sc_ = 1.0 - 0.17 * (h / CH)
        x *= sc_; y *= sc_
        u = h / CH
        if u > 0.45 and y < 0:                                  # front pinches
            x *= 1.0 - 0.20 * ((u - 0.45) / 0.55) * (-y / ry) ** 1.5
        z = h
        if k == NV: z = h
        ring.append(bm.verts.new((x, y, z)))
    rings.append(ring)
for k in range(NV):
    for i in range(NU):
        bm.faces.new((rings[k][i], rings[k][(i + 1) % NU], rings[k + 1][(i + 1) % NU], rings[k + 1][i]))
# top with a centre crease (dent along the front-back line)
ctr_top = bm.verts.new((0, 0, CH - 0.030))
inner = []
for i in range(NU):
    v = rings[NV][i]; x, y = v.co.x, v.co.y
    p = bm.verts.new((x * 0.55, y * 0.75, CH - 0.004 - 0.026 * math.exp(-(x / (0.35 * rx)) ** 2)))
    inner.append(p)
for i in range(NU):
    bm.faces.new((rings[NV][i], rings[NV][(i + 1) % NU], inner[(i + 1) % NU], inner[i]))
    bm.faces.new((inner[i], inner[(i + 1) % NU], ctr_top))
# brim: flat ring outward, sides curl up, front snaps down slightly
BR = 0.050; brim_o = []
for i in range(NU):
    a = 2 * math.pi * i / NU; ca, sa = math.cos(a), math.sin(a)
    x = ca * (rx + BR); y = sa * (ry + BR * 1.1)
    z = 0.012 * ca * ca - (0.010 * (-sa) if sa < 0 else 0.0) + 0.006 * (sa if sa > 0 else 0)
    brim_o.append(bm.verts.new((x, y, z)))
for i in range(NU):
    bm.faces.new((rings[0][(i + 1) % NU], rings[0][i], brim_o[i], brim_o[(i + 1) % NU]))
me = bpy.data.meshes.new("Singer.fedora"); bm.to_mesh(me); bm.free()
hat = bpy.data.objects.new("Singer.fedora", me); sc.collection.objects.link(hat)
for p_ in me.polygons: p_.use_smooth = True
mh = bpy.data.materials.new("M_Fedora"); mh.use_nodes = True; Ph = mh.node_tree.nodes["Principled BSDF"]
Ph.inputs['Base Color'].default_value = (0.30, 0.32, 0.35, 1); Ph.inputs['Roughness'].default_value = 0.8
mb = bpy.data.materials.new("M_FedoraBand"); mb.use_nodes = True; Pb = mb.node_tree.nodes["Principled BSDF"]
Pb.inputs['Base Color'].default_value = (0.015, 0.015, 0.02, 1); Pb.inputs['Roughness'].default_value = 0.5
me.materials.append(mh); me.materials.append(mb)
for p_ in me.polygons:
    zc = sum(me.vertices[i].co.z for i in p_.vertices) / len(p_.vertices)
    rr = max(math.hypot(me.vertices[i].co.x / rx, me.vertices[i].co.y / ry) for i in p_.vertices)
    p_.material_index = 1 if 0.004 < zc < 0.032 and rr < 1.01 else 0
sol = hat.modifiers.new("sol", 'SOLIDIFY'); sol.thickness = 0.005; sol.offset = 1.0
EZ = RIGS["Singer"].data.bones["eye.L"].head_local.z
print("HATFIT top", top, "eye", EZ)
hat.location = (c.x, c.y + 0.012, EZ + 0.028)
hat.rotation_euler = (math.radians(-14), 0, 0)   # Phase-2 note: tipped back further for S16             # tipped back: the brim clears the eyes
bpy.context.view_layer.update()
parent_to_bone(hat, RIGS["Singer"], "head")
# singer's hair hidden under the hat would poke through the crown: hide hair (the hat covers the head in every shot)
for k in RIGS["Singer"].children:
    pass  # hair kept (shows at the temples under the hat)
# trim the hair cards around the right ear (the payphone handset sits there; long card edges crossed the earpiece)
hair = child(RIGS["Singer"], "short01"); body_ = child(RIGS["Singer"], ".body")
B_ = RIGS["Singer"].data.bones; ez_ = B_["eye.R"].head_local.z
gi_ = body_.vertex_groups["head"].index
earR = min((v.co for v in body_.data.vertices if abs(v.co.z - (ez_ - 0.02)) < 0.02 and v.co.x < 0 and any(g.group == gi_ and g.weight > 0.5 for g in v.groups)), key=lambda p: p.x)
bm_ = bmesh.new(); bm_.from_mesh(hair.data)
dl_ = [v for v in bm_.verts if (v.co - earR).length < 0.075 and v.co.x < earR.x + 0.04]
print("EARTRIM", len(dl_)); bmesh.ops.delete(bm_, geom=dl_, context='VERTS'); bm_.to_mesh(hair.data); bm_.free()

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
