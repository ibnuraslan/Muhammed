"""The statue: an MPFB male body (copy of CrowdM3) posed on the cross, in white marble, with a loincloth cut from his
fitted trousers. Replaces the scanned corpus (its feet are crude stumps and the film opens on a macro of the feet).
blender -b sets.blend --python 03_statue.py -- <out.blend>"""
import sys, os, math
import bpy, bmesh
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
V = Vector
sc = bpy.context.scene
C1 = bpy.data.collections["S1_Courtyard"]
# drop the scan corpus
old = bpy.data.objects.get("S1_Statue")
if old: bpy.data.objects.remove(old, do_unlink=True)
SRC = bpy.data.objects["CrowdM3"]
rig = SRC.copy(); rig.data = SRC.data.copy(); rig.name = "S1_StatueRig"; rig.data.name = "S1_StatueRig"
rig.animation_data_clear(); C1.objects.link(rig)
for c in [c for c in bpy.data.objects if c.parent == SRC]:
    part = c.name.split(".", 1)[1]
    if part.startswith("shoes") or part in ("teeth_base", "tongue01", "eyelashes01"): continue
    d = c.copy(); d.data = c.data.copy(); d.name = "S1_Statue." + part; d.parent = rig; C1.objects.link(d)
    for m in list(d.modifiers):
        if m.type == 'MASK' and m.name.startswith('Delete.'): d.modifiers.remove(m)      # under-clothes delete groups (statue has no clothes); keep 'Hide helpers'
    for m in d.modifiers:
        if m.type == 'ARMATURE': m.object = rig
for cl in list(rig.users_collection):
    if cl != C1: cl.objects.unlink(rig)
for d in rig.children:
    for cl in list(d.users_collection):
        if cl != C1: cl.objects.unlink(d)
rig.location = (0, 0, 0)
R = make_human_ctrl(rig); H = Human(R)
B = R.BN
# ---- loincloth from the fitted casual suit: keep a band around the hips only
suit = next(c for c in rig.children if "casualsuit" in c.name)
hipz = B["upperleg01.L"].head_local.z; knee = B["lowerleg01.L"].head_local.z
zlo, zhi = hipz - 0.80 * (hipz - knee), hipz + 0.08
bm = bmesh.new(); bm.from_mesh(suit.data)
mwS = suit.matrix_world.copy()
print("SUITZ", zlo, zhi, min((mwS @ v.co).z for v in bm.verts), max((mwS @ v.co).z for v in bm.verts))
kill = [v for v in bm.verts if not (zlo <= (mwS @ v.co).z <= zhi)]
bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(suit.data); bm.free()
sol = suit.modifiers.new("thick", 'SOLIDIFY'); sol.thickness = 0.008; sol.offset = 1.0
suit.name = "S1_Statue.loincloth"
# ---- marble on everything; hair/brows keep their alpha
M = bpy.data.materials.get("M_StatueMarble")
if M is None:
    M = bpy.data.materials.new("M_StatueMarble"); M.use_nodes = True
    M.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.88, 0.87, 0.84, 1)
P0 = M.node_tree.nodes["Principled BSDF"]; P0.inputs['Roughness'].default_value = 0.38
def marble_alpha(src_mat):
    """copy of the marble material that keeps src_mat's alpha texture (hair / brow cards)"""
    m = M.copy(); m.name = "M_StatueMarbleCards"; m.blend_method = 'HASHED' if hasattr(m, "blend_method") else None
    tex = next((n for n in src_mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image and ("diffuse" in n.image.name.lower() or "alpha" in n.image.name.lower())), None)
    if tex:
        t2 = m.node_tree.nodes.new('ShaderNodeTexImage'); t2.image = tex.image
        uv = m.node_tree.nodes.new('ShaderNodeUVMap')
        m.node_tree.links.new(uv.outputs[0], t2.inputs[0])
        m.node_tree.links.new(t2.outputs['Alpha'], m.node_tree.nodes["Principled BSDF"].inputs['Alpha'])
    return m
for d in rig.children:
    if d.type != 'MESH': continue
    cards = any(k in d.name for k in ("short", "eyebrow", "long", "bob", "ponytail", "braid"))
    mats = [marble_alpha(m) if (cards and m) else M for m in d.data.materials]
    d.data.materials.clear()
    for m in mats: d.data.materials.append(m)
    d.visible_shadow = True
# ---- pose (static, keyed at frame 1): hands on the crossbar, feet pointing down, head bowed right
scale = 0.96
rig.scale = (scale,) * 3
def W(p):  # world target -> armature space
    return Matrix.Scale(1 / scale, 3) @ V(p)
FEET_TOP = 1.58      # ankle height (world)
ank = H.ankle["L"]
root_world_z = FEET_TOP + (H.root_head.z - ank.z) * scale - 0.03
ROOT = V((0.0, -0.30 - 0.17, root_world_z))
f = 1
H.key_root(f, W(ROOT), yaw=0.0, flex=2.0)
H.key_spine(f, flex=6.0, side=-3.0, head=(26.0, 14.0))
sh = B["upperarm01.L"].head_local
for s, sx in (("L", 1), ("R", -1)):
    hand = V((sx * 0.80, -0.30 - 0.06, ROOT.z + (sh.z - H.root_head.z) * scale + 0.30))
    d_ = V((sx * 0.9, 0.0, 0.42)).normalized(); n_ = V((0, -1, 0))
    pole = V((sx * 0.45, -0.30, hand.z - 0.55))
    H.key_hand(s, f, W(hand), d_, n_, W(pole))
    # feet: plantar-flexed ~55 deg, R foot over L
    fx = sx * 0.035
    fy = -0.30 - 0.14 - (0.03 if s == "R" else 0.0)
    a = H.ankle[s]
    Mf = Matrix.Translation(W(V((fx, fy, FEET_TOP + (0.0 if s == "L" else 0.03))))) @ Matrix.Rotation(R_(62), 4, 'X') @ \
         Matrix.Rotation(R_(-sx * 6), 4, 'Z') @ Matrix.Translation(-a) @ R.rest("IK_foot." + s)
    R.key_world("IK_foot." + s, f, Mf)
    pb = R.PB["Pole_knee." + s]; nm = "Pole_knee." + s
    pb.location = R.rest(nm).to_3x3().inverted() @ (W(V((fx, -1.2, FEET_TOP + 0.55))) - B[nm].head_local); pb.keyframe_insert("location", frame=f, group=nm)
exec(open(os.path.join(HERE, "..", "..", "pipeline", "hand_poses.py")).read())
add_hand_limits(rig)
apply_pose(rig, "L", "relaxed", f); apply_pose(rig, "R", "relaxed", f)
sc.frame_set(1); bpy.context.view_layer.update()
# toe tips (lowest body verts) for the drips
body = next(c for c in rig.children if c.name.endswith("body"))
dg = bpy.context.evaluated_depsgraph_get(); be = body.evaluated_get(dg); me = be.to_mesh()
allw = [body.matrix_world @ v.co for v in me.vertices]
pts = sorted(allw, key=lambda p: p.z)
be.to_mesh_clear()
# ---- draped loincloth (perizoma): an elliptical skirt fitted to the posed hips, with folds; replaces the shorts band
hipw = rig.matrix_world @ R.PB["upperleg01.L"].head
band = [p for p in allw if abs(p.z - (hipw.z - 0.04)) < 0.03]
cx = sum(p.x for p in band) / len(band); cy = sum(p.y for p in band) / len(band)
ex = max(abs(p.x - cx) for p in band); ey = max(abs(p.y - cy) for p in band)
lowb = [p for p in allw if abs(p.z - (hipw.z - 0.30)) < 0.03]
ex2 = max(abs(p.x - cx) for p in lowb); ey2 = max(abs(p.y - cy) for p in lowb)
ztop, zbot = hipw.z + 0.07, hipw.z - 0.32
bm = bmesh.new(); NA, NZ = 64, 14; rows = []
for j in range(NZ + 1):
    t = j / NZ; z = ztop + (zbot - ztop) * t
    ax = (ex + 0.018) * (1 - t) + (ex2 + 0.05) * t; ay = (ey + 0.022) * (1 - t) + (ey2 + 0.06) * t
    row = []
    for i in range(NA):
        a = 2 * math.pi * i / NA
        fold = 1.0 + (0.05 + 0.10 * t) * math.sin(7 * a + 0.6) * (0.4 + t)
        hem = 0.035 * math.sin(3 * a + 1.0) * (t ** 3)
        row.append(bm.verts.new((cx + ax * fold * math.cos(a), cy + ay * fold * math.sin(a), z + hem)))
    rows.append(row)
for j in range(NZ):
    for i in range(NA):
        bm.faces.new((rows[j][i], rows[j][(i + 1) % NA], rows[j + 1][(i + 1) % NA], rows[j + 1][i]))
# knot / tuck at the right hip
lme = bpy.data.meshes.new("Loincloth"); bm.to_mesh(lme); bm.free()
LC = bpy.data.objects.new("S1_Statue.perizoma", lme); C1.objects.link(LC)
for p_ in lme.polygons: p_.use_smooth = True
s_ = LC.modifiers.new("thick", 'SOLIDIFY'); s_.thickness = 0.01; s_.offset = 1.0
sd_ = LC.modifiers.new("sub", 'SUBSURF'); sd_.levels = 1; sd_.render_levels = 1
lme.materials.append(M)
old_lc = bpy.data.objects.get("S1_Statue.loincloth")
if old_lc: bpy.data.objects.remove(old_lc, do_unlink=True)
print("PERIZOMA", round(ex, 3), round(ey, 3), round(ex2, 3), round(ey2, 3))
sc["TOE"] = tuple(pts[0]); sc["FEET_Z"] = pts[0].z
hands = [rig.matrix_world @ R.PB["wrist." + s].head for s in "LR"]
print("STATUE toe", tuple(round(t, 3) for t in pts[0]), "hands", [tuple(round(t, 2) for t in h) for h in hands],
      "head", tuple(round(t, 2) for t in rig.matrix_world @ R.PB["head"].head))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("STATUE_OK")
