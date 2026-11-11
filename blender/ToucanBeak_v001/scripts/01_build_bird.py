"""Hero keel-billed toucan: body from Lary's CC-BY Toucan (re-coloured to keel-billed, feather hair layer),
beak = MooreLab's CC-BY specimen scan of a real Ramphastos sulfuratus beak. Custom armature.
Bird faces +Y, feet (perch grip) at the origin, metres.
blender -b --factory-startup -P 01_build_bird.py -- <out.blend>"""
import bpy, bmesh, sys, os, math, numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(HERE, "assets")
out = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)

def imp(name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(A, name + ".glb"))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o.type != 'MESH': bpy.data.objects.remove(o)
    for o in meshes:
        bpy.context.view_layer.objects.active = o; o.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True); o.select_set(False)
    return meshes

def verts(o): return np.array([v.co[:] for v in o.data.vertices])

# ---------------- body (Lary) ----------------
body = imp("toucan_b")[0]; body.name = "Toucan_body"
S = 0.02
V = verts(body)
# feet: light-coloured verts low on the body (not throat)
img = [n for n in body.data.materials[0].node_tree.nodes if n.type == 'TEX_IMAGE'][0].image
px = np.array(img.pixels[:]).reshape(img.size[1], img.size[0], 4)
uv = np.zeros((len(V), 2)); ul = body.data.uv_layers.active.data
for l in body.data.loops: uv[l.vertex_index] = ul[l.index].uv
col = px[(uv[:, 1].clip(0, .999) * img.size[1]).astype(int), (uv[:, 0].clip(0, .999) * img.size[0]).astype(int), :3]
bright = col.mean(1) > 0.45
feet = bright & (V[:, 2] < 4) & (V[:, 2] > -3) & (V[:, 1] > -8)
print("FEET verts", feet.sum(), V[feet].min(0).round(2), V[feet].max(0).round(2))
fc = V[feet].mean(0); fz = V[feet][:, 2].min()
# delete the low-poly beak (we put the scanned one on)
bm = bmesh.new(); bm.from_mesh(body.data)
kill = [v for v in bm.verts if v.co.y > -1.55 and v.co.z > 9.0]
bmesh.ops.delete(bm, geom=kill, context='VERTS')
bm.to_mesh(body.data); bm.free()
# origin at feet grip, scale to metres
grip = Vector((0, fc[1], fz + 0.35))
body.data.transform(Matrix.Translation(-grip)); body.data.transform(Matrix.Scale(S, 4))
LB_base = (Vector((0, -1.75, 12.45)) - grip) * S       # beak base centre (Lary)
LB_tip = (Vector((0, 5.07, 9.6)) - grip) * S
# Lary's shell is open with oval holes: keep its legs/feet as-is, rebuild the body as a closed voxel skin (holes closed)
bpy.context.view_layer.objects.active = body; body.select_set(True)
mod = body.modifiers.new("sub", 'SUBSURF'); mod.levels = 1; bpy.ops.object.modifier_apply(modifier="sub")
legs_o = body.copy(); legs_o.data = body.data.copy(); bpy.context.scene.collection.objects.link(legs_o)
bm = bmesh.new(); bm.from_mesh(legs_o.data)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > 0.045 or v.co.y < -0.075], context='VERTS'); bm.to_mesh(legs_o.data); bm.free()
mod = body.modifiers.new("sub2", 'SUBSURF'); mod.levels = 2; bpy.ops.object.modifier_apply(modifier="sub2")
gn = bpy.data.node_groups.new("closeskin", 'GeometryNodeTree')
gn.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
gn.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
gi = gn.nodes.new("NodeGroupInput"); go = gn.nodes.new("NodeGroupOutput")
m2p = gn.nodes.new("GeometryNodeMeshToPoints"); p2v = gn.nodes.new("GeometryNodePointsToVolume"); v2m = gn.nodes.new("GeometryNodeVolumeToMesh")
p2v.inputs["Radius"].default_value = 0.0125
try:
    p2v.resolution_mode = 'VOXEL_SIZE'
except Exception: pass
for k in ("Voxel Size",):
    if k in p2v.inputs: p2v.inputs[k].default_value = 0.0022
v2m.inputs["Threshold"].default_value = 0.5 if "Threshold" in v2m.inputs else 0
gn.links.new(gi.outputs[0], m2p.inputs[0]); gn.links.new(m2p.outputs[0], p2v.inputs[0]); gn.links.new(p2v.outputs[0], v2m.inputs[0]); gn.links.new(v2m.outputs[0], go.inputs[0])
mod = body.modifiers.new("skin", 'NODES'); mod.node_group = gn; bpy.ops.object.modifier_apply(modifier="skin")
mod = body.modifiers.new("sm", 'SMOOTH'); mod.factor = 1.0; mod.iterations = 20; bpy.ops.object.modifier_apply(modifier="sm")
bm = bmesh.new(); bm.from_mesh(body.data)   # remove the blobby voxel feet; real legs come back from legs_o
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < 0.03 and v.co.y > -0.075], context='VERTS'); bm.to_mesh(body.data); bm.free()
body.select_set(True); legs_o.select_set(True); bpy.context.view_layer.objects.active = body; bpy.ops.object.join()
bpy.ops.object.shade_smooth(); body.select_set(False)
print("BODY polys", len(body.data.polygons))
VB = verts(body); eyes = []
em = bpy.data.materials.new("Toucan_eye"); em.use_nodes = True; eb = em.node_tree.nodes["Principled BSDF"]
eb.inputs["Base Color"].default_value = (0.02, 0.025, 0.02, 1); eb.inputs["Roughness"].default_value = 0.03; eb.inputs["Coat Weight"].default_value = 1.0
sk = bpy.data.materials.new("Toucan_eyeskin"); sk.use_nodes = True; sb = sk.node_tree.nodes["Principled BSDF"]
sb.inputs["Base Color"].default_value = (0.25, 0.55, 0.15, 1); sb.inputs["Roughness"].default_value = 0.5
eyc_y = LB_base.y - 0.016; eyc_z = LB_base.z + 0.012
for sx in (1, -1):
    sel = (np.abs(VB[:, 1] - eyc_y) < 0.006) & (np.abs(VB[:, 2] - eyc_z) < 0.006) & (VB[:, 0] * sx > 0)
    xs = VB[sel][:, 0] * sx; xo = xs.max() if len(xs) else 0.025
    for nm, r, mat, inset in (("eyeskin", 0.0075, sk, 0.0035), ("eye", 0.0048, em, 0.0015)):
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=r); me = bpy.data.meshes.new(nm); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new("Toucan_%s.%s" % (nm, "L" if sx > 0 else "R"), me); bpy.context.scene.collection.objects.link(o)
        o.location = (sx * (xo - inset), eyc_y, eyc_z); o.scale = (0.55, 1, 1) if nm == "eyeskin" else (0.8, 1, 1)
        me.materials.append(mat); [setattr(f_, "use_smooth", True) for f_ in me.polygons]; eyes.append(o)
# keel-billed colouring (procedural by body position, Lary's stylised texture is not used):
# black body, lemon-yellow bib, red undertail coverts, blue-grey legs; feather-scale bump + sheen
m = bpy.data.materials.new("Toucan_feathers"); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
body.data.materials.clear(); body.data.materials.append(m)
bsdf = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
def node_math(op, a, b):
    n = N.new("ShaderNodeMath"); n.operation = op
    for k, x in enumerate((a, b)):
        if isinstance(x, (int, float)): n.inputs[k].default_value = x
        else: L.new(x, n.inputs[k])
    return n.outputs[0]
def smooth(x, a, b):
    n = N.new("ShaderNodeMapRange"); n.interpolation_type = 'SMOOTHSTEP'; L.new(x, n.inputs[0]); n.inputs[1].default_value = a; n.inputs[2].default_value = b
    return n.outputs[0]
X, Y, Z = sep.outputs["X"], sep.outputs["Y"], sep.outputs["Z"]
# bib: front of the breast/throat
yf = node_math('SUBTRACT', Y, node_math('MULTIPLY', node_math('SUBTRACT', 0.27, Z), 0.22))
bib = node_math('MULTIPLY', smooth(yf, -0.012, -0.002), node_math('MULTIPLY', smooth(Z, 0.135, 0.165), node_math('SUBTRACT', 1.0, smooth(Z, 0.262, 0.272))))
red = node_math('MULTIPLY', smooth(Y, -0.03, -0.06), node_math('MULTIPLY', smooth(Z, -0.035, -0.015), node_math('SUBTRACT', 1.0, smooth(Z, 0.02, 0.045))))
leg = node_math('MULTIPLY', node_math('SUBTRACT', 1.0, smooth(Z, 0.03, 0.04)), smooth(Y, -0.08, -0.06))
def mixc(fac, a, b):
    n = N.new("ShaderNodeMix"); n.data_type = 'RGBA'; L.new(fac, n.inputs["Factor"])
    for k, x in ((6, a), (7, b)):
        if isinstance(x, tuple): n.inputs[k].default_value = x
        else: L.new(x, n.inputs[k])
    return n.outputs[2]
noise = N.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 300; noise.inputs["Detail"].default_value = 6
L.new(tc.outputs["Object"], noise.inputs["Vector"])
blk = mixc(noise.outputs["Fac"], (0.012, 0.012, 0.014, 1), (0.035, 0.03, 0.028, 1))
c1 = mixc(bib, blk, (0.95, 0.76, 0.04, 1))
c1 = mixc(red, c1, (0.6, 0.03, 0.02, 1))
c1 = mixc(leg, c1, (0.32, 0.42, 0.62, 1))
L.new(c1, bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.5
bsdf.inputs["Sheen Weight"].default_value = 0.35; bsdf.inputs["Sheen Tint"].default_value = (0.3, 0.3, 0.33, 1); bsdf.inputs["Sheen Roughness"].default_value = 0.35
vor = N.new("ShaderNodeTexVoronoi"); vor.feature = 'DISTANCE_TO_EDGE'; vor.inputs["Scale"].default_value = 260
mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1.4, 0.6, 1.0); L.new(tc.outputs["Object"], mp.inputs[0]); L.new(mp.outputs[0], vor.inputs["Vector"])
h_ = node_math('MULTIPLY_ADD', node_math('MINIMUM', vor.outputs["Distance"], 0.08), 4.0)
hh_ = N.new("ShaderNodeMath"); hh_.operation = 'ADD'; L.new(h_, hh_.inputs[0]); L.new(noise.outputs["Fac"], hh_.inputs[1])
wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 900; wv.inputs["Distortion"].default_value = 6; wv.inputs["Detail"].default_value = 3
L.new(tc.outputs["Object"], wv.inputs["Vector"])
h2 = N.new("ShaderNodeMath"); h2.operation = 'MULTIPLY_ADD'; L.new(wv.outputs["Fac"], h2.inputs[0]); h2.inputs[1].default_value = 0.25; L.new(hh_.outputs[0], h2.inputs[2]); hh_ = h2
bmp = N.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.55; bmp.inputs["Distance"].default_value = 0.003
L.new(hh_.outputs[0], bmp.inputs["Height"]); L.new(bmp.outputs["Normal"], bsdf.inputs["Normal"])

# ---------------- beak (MooreLab scan) ----------------
scan = imp("toucan_scan")
for o in scan[1:]: bpy.data.objects.remove(o)
scan = scan[0]; scan.name = "Toucan_beak"
SV = verts(scan); c = SV.mean(0); ax = np.array([-1.0, 0.02, -0.06]); ax /= np.linalg.norm(ax)
p = (SV - c) @ ax
CUT = 0.098
bm = bmesh.new(); bm.from_mesh(scan.data)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if (Vector(v.co) - Vector(c)).dot(Vector(ax)) < CUT], context='VERTS')
bm.to_mesh(scan.data); bm.free()
SV = verts(scan); p = (SV - c) @ ax
base = SV[p < CUT + 0.008].mean(0); tip = SV[p.argmax()]
print("SCAN beak len", np.linalg.norm(tip - base))
# frame of scan beak: x' = axis, z' = up(+z)
def frame(b, t, up):
    x = Vector(t) - Vector(b); x.normalize(); z = Vector(up) - Vector(up).dot(x) * x; z.normalize(); y = z.cross(x)
    return Matrix((x, y, z)).transposed()
Fs = frame(base, tip, (0, 0, 1)); Fl = frame(LB_base, LB_tip, (0, 0, 1))
k = (LB_tip - LB_base).length / np.linalg.norm(tip - base) * 0.96
T = Matrix.Translation(LB_base) @ (Fl @ Fs.inverted()).to_4x4() @ Matrix.Scale(k, 4) @ Matrix.Translation(-Vector(base))
scan.data.transform(T)
bpy.context.view_layer.objects.active = scan; scan.select_set(True); bpy.ops.object.shade_smooth(); scan.select_set(False)
bm_ = scan.data.materials[0]; bb = [n for n in bm_.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
bb.inputs["Roughness"].default_value = 0.28; bb.inputs["Coat Weight"].default_value = 0.35
# brighten/saturate the scanned colours a little (museum specimens fade)
bt = [n for n in bm_.node_tree.nodes if n.type == 'TEX_IMAGE'][0]
hsv = bm_.node_tree.nodes.new("ShaderNodeHueSaturation"); hsv.inputs["Saturation"].default_value = 1.35; hsv.inputs["Value"].default_value = 1.25
bm_.node_tree.links.new(bt.outputs["Color"], hsv.inputs["Color"])
sp = bm_.node_tree.nodes.new("ShaderNodeSeparateColor"); sp.mode = 'HSV'; bm_.node_tree.links.new(bt.outputs["Color"], sp.inputs[0])
gm = bm_.node_tree.nodes.new("ShaderNodeMapRange"); bm_.node_tree.links.new(sp.outputs[1], gm.inputs[0]); gm.inputs[1].default_value = 0.35; gm.inputs[2].default_value = 0.15
gr = bm_.node_tree.nodes.new("ShaderNodeMix"); gr.data_type = 'RGBA'; gr.blend_type = 'MULTIPLY'
bm_.node_tree.links.new(gm.outputs[0], gr.inputs[0]); bm_.node_tree.links.new(hsv.outputs["Color"], gr.inputs[6]); gr.inputs[7].default_value = (0.5, 1.0, 0.25, 1)
bm_.node_tree.links.new(gr.outputs[2], bb.inputs["Base Color"])

# beak axis helper data (stored on object for later scripts)
for o in (scan,):
    o["base"] = list(LB_base); o["tip"] = list(LB_tip)
# split beak into upper / lower mandible by the commissure line (straight line base-mid -> tip, slightly below centre)
bv = verts(scan); fx = (Vector(LB_tip) - Vector(LB_base)).normalized()
def along(v): return (Vector(v) - LB_base).dot(fx)
Lb = (LB_tip - LB_base).length
upZ = Fl.col[2]
def h(v): return (Vector(v) - LB_base).dot(Vector(upZ))
# commissure: lower ~40 % of the height at each station
st = np.array([along(v) for v in bv]); hh = np.array([h(v) for v in bv])
bins = np.linspace(st.min(), st.max(), 30); comm = []
for a0, a1 in zip(bins[:-1], bins[1:]):
    s = (st >= a0) & (st < a1)
    comm.append(hh[s].min() + 0.38 * np.ptp(hh[s]) if s.sum() > 5 else (comm[-1] if comm else 0))
comm = np.array(comm)
def comm_at(a): return np.interp(a, (bins[:-1] + bins[1:]) / 2, comm)
lower = scan.copy(); lower.data = scan.data.copy(); lower.name = "Toucan_beak_lower"; bpy.context.scene.collection.objects.link(lower)
for o, keep_upper in ((scan, True), (lower, False)):
    bm = bmesh.new(); bm.from_mesh(o.data)
    rm = [v for v in bm.verts if (h(v.co) > comm_at(along(v.co))) != keep_upper]
    bmesh.ops.delete(bm, geom=rm, context='VERTS'); bm.to_mesh(o.data); bm.free()
scan.name = "Toucan_beak_upper"
# broken upper beak: keep proximal 42 %, jagged boolean cut
up_broken = scan.copy(); up_broken.data = scan.data.copy(); up_broken.name = "Toucan_beak_upper_broken"
bpy.context.scene.collection.objects.link(up_broken)
cutter = bpy.data.objects.new("cutter", bpy.data.meshes.new("cutter")); bpy.context.scene.collection.objects.link(cutter)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=10, use_grid_fill=True); bm.to_mesh(cutter.data); bm.free()
cutter.scale = (Lb, Lb * 0.6, Lb * 0.6)
cutter.matrix_world = Matrix.Translation(LB_base + fx * (Lb * 0.42 + Lb * 0.5)) @ Fl.to_4x4() @ Matrix.Diagonal((Lb, Lb * 0.6, Lb * 0.6, 1))
dsp = cutter.modifiers.new("d", 'DISPLACE'); tx = bpy.data.textures.new("jag", 'VORONOI'); tx.noise_scale = 0.012; dsp.texture = tx; dsp.strength = 0.012
bpy.context.view_layer.objects.active = cutter; bpy.ops.object.modifier_apply(modifier="d")
tip_piece = scan.copy(); tip_piece.data = scan.data.copy(); tip_piece.name = "Beak_tip_piece"; bpy.context.scene.collection.objects.link(tip_piece)
for o, op in ((up_broken, 'DIFFERENCE'), (tip_piece, 'INTERSECT')):
    b = o.modifiers.new("cut", 'BOOLEAN'); b.object = cutter; b.operation = op; b.solver = 'EXACT'
    bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier="cut")
# fracture surface material (keratin interior: pale, fibrous)
fm = bpy.data.materials.new("Keratin_fracture"); fm.use_nodes = True
fb = fm.node_tree.nodes["Principled BSDF"]; fb.inputs["Base Color"].default_value = (0.78, 0.66, 0.42, 1); fb.inputs["Roughness"].default_value = 0.7
fn = fm.node_tree.nodes.new("ShaderNodeTexNoise"); fn.inputs["Scale"].default_value = 400; fn.inputs["Detail"].default_value = 8
fbp = fm.node_tree.nodes.new("ShaderNodeBump"); fbp.inputs["Distance"].default_value = 0.0006
fm.node_tree.links.new(fn.outputs["Fac"], fbp.inputs["Height"]); fm.node_tree.links.new(fbp.outputs["Normal"], fb.inputs["Normal"])
for o in (up_broken, tip_piece):
    o.data.materials.append(fm)
    for poly in o.data.polygons:
        if poly.material_index != 0: pass
    # faces created by the cutter got cutter's (no) material -> index beyond; set faces near cut plane to fracture mat
    cut_a = Lb * 0.42
    for poly in o.data.polygons:
        a = along(poly.center)
        if abs(a - cut_a) < Lb * 0.035 and abs(Vector(poly.normal).dot(fx)) > 0.5: poly.material_index = 1
# shards: intersect the tip piece with small blobs -> textured chunks
shards = []
rng = np.random.default_rng(7)
tv = verts(tip_piece)
for i in range(9):
    cpos = Vector(tv[rng.integers(len(tv))])
    bl = bpy.data.objects.new("blob", bpy.data.meshes.new("blob")); bpy.context.scene.collection.objects.link(bl)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=Lb * rng.uniform(0.06, 0.12)); bm.to_mesh(bl.data); bm.free()
    for v in bl.data.vertices: v.co *= rng.uniform(0.6, 1.4)
    bl.location = cpos
    sh = tip_piece.copy(); sh.data = tip_piece.data.copy(); sh.name = "Beak_shard_%d" % i; bpy.context.scene.collection.objects.link(sh)
    b = sh.modifiers.new("i", 'BOOLEAN'); b.object = bl; b.operation = 'INTERSECT'; b.solver = 'EXACT'
    bpy.context.view_layer.objects.active = sh; bpy.ops.object.modifier_apply(modifier="i")
    bpy.data.objects.remove(bl)
    if len(sh.data.vertices) < 8: bpy.data.objects.remove(sh); continue
    for poly in sh.data.polygons:
        if poly.material_index == 0 and rng.random() < 0: pass
    shards.append(sh)
bpy.data.objects.remove(cutter)
# recentre shards / tip piece origins
for o in shards + [tip_piece]:
    bpy.context.view_layer.objects.active = o
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS'); o.select_set(False)
print("SHARDS", len(shards))

# ---------------- armature ----------------
arm = bpy.data.armatures.new("ToucanRig"); rig = bpy.data.objects.new("ToucanRig", arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
E = arm.edit_bones
def B(n, h, t, par=None):
    b = E.new(n); b.head = Vector(h); b.tail = Vector(t)
    if par: b.parent = E[par]; b.use_connect = False
    return b
Vb = verts(body)
B("root", (0, 0, 0), (0, 0, 0.03))
B("body", (0, -0.02, 0.02), (0, 0.02, 0.12), "root")
B("chest", (0, 0.02, 0.12), (0, 0.03, 0.19), "body")
B("neck", (0, 0.03, 0.19), (0, 0.0, 0.22), "chest")
hb = B("head", (0, 0.0, 0.22), (LB_base.x, LB_base.y, LB_base.z), "neck")
B("tail", (0, -0.07, 0.03), (0, -0.2, -0.08), "body")
B("wing.L", (0.04, -0.01, 0.17), (0.05, -0.15, 0.03), "chest")
B("wing.R", (-0.04, -0.01, 0.17), (-0.05, -0.15, 0.03), "chest")
B("jaw", (LB_base.x, LB_base.y, LB_base.z - 0.012), (LB_tip.x, LB_tip.y, LB_tip.z), "head")
bpy.ops.object.mode_set(mode='OBJECT')
print("BODY bounds", Vb.min(0).round(3), Vb.max(0).round(3), "beak", LB_base, LB_tip)
# weights by nearest-bone-segment distance, smooth falloff
def segd(P, a, b):
    ab = b - a; t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1); return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)
names = ["body", "chest", "neck", "head", "tail", "wing.L", "wing.R"]
W = []
for n in names:
    b = arm.bones[n]; W.append(segd(Vb, np.array(b.head_local), np.array(b.tail_local)))
W = np.array(W)
W = np.exp(-(W / 0.025) ** 2) + 1e-6
# wings only on the outer side
W[5] *= (Vb[:, 0] > 0.025); W[6] *= (Vb[:, 0] < -0.025)
W /= W.sum(0)
for i, n in enumerate(names):
    g = body.vertex_groups.new(name=n)
    for vi in np.nonzero(W[i] > 0.01)[0]: g.add([int(vi)], float(W[i, vi]), 'REPLACE')
# feet / legs stay with root (planted)
g = body.vertex_groups.new(name="root")
legs = (Vb[:, 2] < 0.035) & (Vb[:, 1] > -0.07)
gb = body.vertex_groups["body"]
for vi in np.nonzero(legs)[0]:
    for n in names: body.vertex_groups[n].remove([int(vi)])
    g.add([int(vi)], 1.0, 'REPLACE')
body.parent = rig; body.modifiers.new("arm", 'ARMATURE').object = rig
bpy.context.view_layer.update()
for o, bn in [(scan, "head"), (up_broken, "head"), (lower, "jaw")] + [(e_, "head") for e_ in eyes]:
    mw = o.matrix_world.copy(); o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = bn
    o.matrix_parent_inverse = Matrix(); bpy.context.view_layer.update(); o.matrix_world = mw
up_broken.hide_render = True; up_broken.hide_viewport = True

# feather layer: short, dense, clumped hair-strand feathers (same procedural plumage material), lying back along the body
ps = body.modifiers.new("feathers", 'PARTICLE_SYSTEM').particle_system
st_ = ps.settings; st_.type = 'HAIR'; st_.count = 14000; st_.use_advanced_hair = True
st_.normal_factor = 0.0035; st_.object_align_factor = (0, -0.0065, -0.0035); st_.factor_random = 0.0008
st_.hair_step = 4; st_.display_step = 3; st_.render_step = 3
st_.child_type = 'INTERPOLATED'; st_.child_percent = 4; st_.rendered_child_count = 6; st_.clump_factor = 0.75; st_.clump_shape = -0.3
st_.child_length = 0.9; st_.child_length_threshold = 0.3; st_.roughness_1 = 0.0006; st_.roughness_endpoint = 0.0004
st_.root_radius = 0.6; st_.tip_radius = 0.15; st_.radius_scale = 0.0012; st_.shape = -0.4
st_.material_slot = body.data.materials[0].name
st_.kink = 'NO'
fd = body.vertex_groups.new(name="feather_density")
VB2 = verts(body)
for vi in range(len(VB2)):
    if not (VB2[vi, 2] < 0.035 and VB2[vi, 1] > -0.075): fd.add([vi], 1.0, 'REPLACE')
ps.vertex_group_density = "feather_density"
# comb: hairs lie back (toward -y / down the body)  -> use hair dynamics-free combing via particle edit is not scriptable; use
# 'Object align'-free approach: tangent phase via Grow direction is normal; bend with child 'Bend'/'Clump' + parting below
st_.child_parting_factor = 0.0
for o in [body, scan, lower, up_broken, tip_piece] + shards:
    o["toucan"] = True
bpy.ops.wm.save_as_mainfile(filepath=out)
print("BIRD_DONE", out)
