"""v012 OR rebuild (client rejection, Nov 21: items 2-6, 19). Runs on the v011 package (VO timing, frames 1-1644).
blender -b v011.blend --python 20_v012_or.py -- <out.blend>

- The patient's whole body lies on the table (no head-only mask). A drape is fitted over her body by ray casting
  (shape of the body reads under the sheet) with a window over the upper abdomen.
- Open abdomen: the skin inside an ellipse is cut out in her skin material (driven by the empty CavityCut), and a
  tissue-lined cavity sits underneath. The branded liver (the old studio liver, its burn animation and sparks) is
  moved, as one group, into that cavity: front surface up, right lobe on her right side.
- Cavity is open for the branding (1-276) and for the second surgery (1000-1260); closed (sutured incision) between."""
import sys, os, math
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
V = lambda *a: Vector(a)

def fcurves(idb):
    ad = getattr(idb, "animation_data", None)
    if not ad or not ad.action: return []
    return [fc for L in ad.action.layers for st in L.strips for cb in st.channelbags for fc in cb.fcurves]
def key_hide(ob, spans, total=(0, 1700)):
    """visible only inside spans [(a,b),...]; constant keys"""
    for fc in fcurves(ob):
        if fc.data_path in ("hide_render", "hide_viewport"):
            k = fc.keyframe_points
            for i in reversed(range(len(k))): k.remove(k[i], fast=True)
    pts = {0: True}
    for a, b in spans: pts[a] = False; pts[b + 1] = True
    for f in sorted(pts):
        ob.hide_render = pts[f]; ob.keyframe_insert("hide_render", frame=f)
    for fc in fcurves(ob):
        if fc.data_path == "hide_render":
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'

OR_OPEN1 = (0, 362)            # branding (S1, S2) and the closing beat (276-360)
OR_OPEN2 = (1000, 1262)        # second surgery (reveal + eyes)
OR_TABLE = [(0, 600), (1000, 1262)]   # patient on the table

# ---------------------------------------------------------------- patient: whole body
pb_ = bpy.data.objects["Patient.body"]
for fc in list(fcurves(pb_)):
    if 'head_only' in fc.data_path:
        for i in reversed(range(len(fc.keyframe_points))): fc.keyframe_points.remove(fc.keyframe_points[i], fast=True)
m = pb_.modifiers["head_only"]; m.show_render = m.show_viewport = False
for n in ("Drape", "AbdomenSkin", "Incision"):
    key_hide(bpy.data.objects[n], [])
for o in bpy.data.objects:
    if o.name.startswith("Suture"): key_hide(o, [])

# she rested ~2 cm into the table pad: lifted 2.5 cm while she is on the table
PRo = bpy.data.objects["Patient"]
for f, dz in ((0, 0.025), (601, 0.0), (1000, 0.025), (1263, 0.0)):
    PRo.delta_location = (0, 0, dz); PRo.keyframe_insert("delta_location", frame=f)
for fc in fcurves(PRo):
    if fc.data_path == "delta_location":
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
_vp = {mm.name: mm.show_viewport for mm in pb_.modifiers}
for mm in pb_.modifiers:
    if mm.name.startswith("Delete."): mm.show_viewport = False
sc.frame_set(70); bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
def bvh_of(o):
    ev = o.evaluated_get(dg); me = ev.to_mesh(); mw = o.matrix_world
    t = BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons]); ev.to_mesh_clear(); return t
BODY = bvh_of(pb_)
def body_top(x, y):
    hit = BODY.ray_cast(V(x, y, 2.0), V(0, 0, -1), 2.0)
    return hit[0].z if hit[0] is not None else None

for mm in pb_.modifiers: mm.show_viewport = _vp[mm.name]
# liver site: patient's right upper abdomen (her right = -y), below the ribs
PR = bpy.data.objects["Patient"]
sp1 = PR.matrix_world @ PR.pose.bones["spine01"].head; sp3 = PR.matrix_world @ PR.pose.bones["spine03"].head
CX = sp3.x + 0.045; CY = -0.055
SKZ = body_top(CX, CY)
print("CAVITY site", round(CX, 3), CY, "skin z", SKZ)
CA, CB = 0.11, 0.075          # opening half-sizes: along y (across the body), along x (along the body)

# ---------------------------------------------------------------- fitted drape
PAD = 0.952
xs = np.arange(-0.69, 1.16, 0.01); ys = np.arange(-0.64, 0.6401, 0.01)
H = np.zeros((len(xs), len(ys)))
for i, x in enumerate(xs):
    for j, y in enumerate(ys):
        z = PAD + 0.006
        if abs(y) <= 0.27 and x <= 1.05:
            bt = body_top(x, y)
            if bt is not None: z = max(z, bt + 0.013)          # v014: lower, the body shape reads
        H[i, j] = z
H0 = H.copy()
for it in range(25):                       # sheet bridges the hollows (between arms and torso, between the legs)
    P = np.pad(H, 1, mode='edge')
    avg = (P[:-2, 1:-1] + P[2:, 1:-1] + P[1:-1, :-2] + P[1:-1, 2:]) / 4
    H = np.maximum(H0, avg - 0.0012)
for i, x in enumerate(xs):                 # hang over the table edges
    for j, y in enumerate(ys):
        d = max(abs(y) - 0.27, x - 1.05, 0)
        if d > 0:
            H[i, j] = min(H[i, j], PAD + 0.006) - min(0.32, d * d * 18 + d * 2.2)
rng = np.random.default_rng(3)
H += 0.0025 * np.sin(xs[:, None] * 37 + ys[None, :] * 11) * np.cos(ys[None, :] * 23)
WX, WY = CB + 0.028, CA + 0.032            # window half-sizes
bm = bmesh.new(); vv = {}
for i, x in enumerate(xs):
    for j, y in enumerate(ys):
        vv[i, j] = bm.verts.new((x, y, H[i, j]))
for i in range(len(xs) - 1):
    for j in range(len(ys) - 1):
        cx_, cy_ = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
        if CX - CB - 0.012 < cx_ < CX + WX and CY - WY - 0.07 < cy_ < CY + WY: continue   # v014: open toward his side
        bm.faces.new((vv[i, j], vv[i + 1, j], vv[i + 1, j + 1], vv[i, j + 1]))
for v in [v for v in bm.verts if not v.link_faces]: bm.verts.remove(v)
me = bpy.data.meshes.new("DrapeFit"); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
dr = bpy.data.objects.new("DrapeFit", me); bpy.data.collections["OR_Set"].objects.link(dr)
me.materials.append(bpy.data.materials["Drape"])
s_ = dr.modifiers.new("t", 'SOLIDIFY'); s_.thickness = 0.004; s_.offset = 1.0
key_hide(dr, OR_TABLE)

# ---------------------------------------------------------------- skin cut (material) + cavity
cut = bpy.data.objects.new("CavityCut", None); bpy.data.collections["OR_Set"].objects.link(cut)
cut.empty_display_size = 0.1
def key_cut(f, open_):
    cut.location = V(CX, CY, SKZ) if open_ else V(CX, CY, SKZ + 50.0)
    cut.keyframe_insert("location", frame=f)
for f, o_ in ((0, True), (OR_OPEN1[1] + 1, False), (OR_OPEN2[0], True), (OR_OPEN2[1] + 1, False)): key_cut(f, o_)
for fc in fcurves(cut):
    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
def add_cut(mat):
    nt = mat.node_tree; N, L = nt.nodes, nt.links
    out = [n for n in N if n.type == 'OUTPUT_MATERIAL' and n.is_active_output][0]
    src = out.inputs['Surface'].links[0].from_socket
    tc = N.new("ShaderNodeTexCoord"); tc.object = cut
    sx = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sx.inputs[0])
    def math_(op, a, b=None):
        n = N.new("ShaderNodeMath"); n.operation = op
        for k, v in enumerate((a, b)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[k].default_value = v
            else: L.new(v, n.inputs[k])
        return n.outputs[0]
    ex = math_('POWER', math_('DIVIDE', sx.outputs[0], CB), 2.0)
    ey = math_('POWER', math_('DIVIDE', sx.outputs[1], CA), 2.0)
    inside = math_('LESS_THAN', math_('ADD', ex, ey), 1.0)
    zin = math_('LESS_THAN', math_('ABSOLUTE', sx.outputs[2]), 0.09)
    fac = math_('MULTIPLY', inside, zin)
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(fac, mx.inputs[0]); L.new(src, mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs['Surface'])
for mt in set(pb_.data.materials): add_cut(mt)

def tissue_mat(name, rgb, rough=0.35, sss=0.3):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgb + (1,); b.inputs["Roughness"].default_value = rough
    b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Radius"].default_value = (0.02, 0.006, 0.004)
    b.inputs["Coat Weight"].default_value = 0.35; b.inputs["Coat Roughness"].default_value = 0.15
    nz = m.node_tree.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 180
    bp = m.node_tree.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.15
    m.node_tree.links.new(nz.outputs["Fac"], bp.inputs["Height"]); m.node_tree.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m
M_WALL = tissue_mat("CavityWall", (0.55, 0.16, 0.14))
M_EDGE = tissue_mat("CavityEdge", (0.78, 0.42, 0.38), 0.45, 0.5)
M_FAT = tissue_mat("CavityFat", (0.85, 0.66, 0.35), 0.4, 0.4)
# bowl: ellipse at the skin, curving down 8 cm; rim lip (cut skin edge, a thin yellow fat layer under it)
NA, NR = 64, 14; bm = bmesh.new(); ring = []
for r in range(NR + 1):
    t = r / NR; row = []
    for a in range(NA):
        th = 2 * math.pi * a / NA
        if t < 0.12:            # lip: from 4 mm outside the cut, rolling over and down
            u = t / 0.12; k = 1.03 - 0.03 * u; dz = 0.002 * math.sin(math.pi * u) - 0.012 * u
        else:
            u = (t - 0.12) / 0.88; k = 1.0 - 0.55 * u ** 1.6; dz = -0.012 - 0.075 * math.sin(u * math.pi / 2)
        row.append(bm.verts.new((CX + CB * k * math.cos(th), CY + CA * k * math.sin(th), 0)))
        row[-1].co.z = dz
    ring.append(row)
for r in range(NR):
    for a in range(NA):
        f_ = bm.faces.new((ring[r][a], ring[r][(a + 1) % NA], ring[r + 1][(a + 1) % NA], ring[r + 1][a]))
        f_.material_index = 0 if r < 1 else (1 if r < 3 else 2)
bm.faces.new(ring[-1][::-1]).material_index = 2
me = bpy.data.meshes.new("Cavity"); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
# rest the rim on the skin surface: each vertex's z follows the body top at its xy
for v in me.vertices:
    st = body_top(v.co.x, v.co.y) or SKZ
    v.co.z = st + v.co.z
cav = bpy.data.objects.new("Cavity", me); bpy.data.collections["OR_Set"].objects.link(cav)
for mm in (M_EDGE, M_FAT, M_WALL): me.materials.append(mm)
key_hide(cav, [OR_OPEN1, OR_OPEN2])

# ---------------------------------------------------------------- v013: the wound is seen closing (276-318) before the stitches
cpiv = bpy.data.objects.new("CavityClose", None); bpy.data.collections["OR_Set"].objects.link(cpiv)
cpiv.location = V(CX, CY, SKZ); bpy.context.view_layer.update()
mw_ = cav.matrix_world.copy(); cav.parent = cpiv; cav.matrix_parent_inverse = cpiv.matrix_world.inverted(); cav.matrix_world = mw_
for f, sx in ((0, 1.0), (280, 1.0), (360, 0.03)):
    cpiv.scale = (sx, 1, 1); cpiv.keyframe_insert("scale", frame=f)
    cut.scale = (max(sx, 0.001), 1, 1); cut.keyframe_insert("scale", frame=f)
for f, sx in ((OR_OPEN2[0], 1.0),):
    cpiv.scale = (sx, 1, 1); cpiv.keyframe_insert("scale", frame=f); cut.scale = (sx, 1, 1); cut.keyframe_insert("scale", frame=f)
# retractor blades hooked over the long sides
M_STEEL = bpy.data.materials.new("Retractor"); M_STEEL.use_nodes = True
bs = M_STEEL.node_tree.nodes["Principled BSDF"]; bs.inputs["Metallic"].default_value = 1; bs.inputs["Roughness"].default_value = 0.25
bs.inputs["Base Color"].default_value = (0.8, 0.82, 0.85, 1)
for sgn in (-1, 1):
    pts = [V(0, 0, -0.05), V(0, 0, -0.005), V(0, 0.012, 0.01), V(0, 0.05, 0.012), V(0, 0.16, -0.04)]
    cu = bpy.data.curves.new("Retractor", 'CURVE'); cu.dimensions = '3D'; cu.extrude = 0.022; cu.bevel_depth = 0.0
    spl = cu.splines.new('POLY'); spl.points.add(len(pts) - 1)
    for p_, c_ in zip(spl.points, pts): p_.co = (c_.x, c_.y, c_.z, 1)
    ob = bpy.data.objects.new("Retractor", cu); bpy.data.collections["OR_Set"].objects.link(ob); cu.materials.append(M_STEEL)
    yy = CY + sgn * (CA * 0.985)
    ob.location = V(CX - 0.01, yy, body_top(CX, yy) or SKZ)
    ob.rotation_euler = (0, 0, 0 if sgn > 0 else math.pi)
    ob.rotation_euler.y = math.radians(90); ob.rotation_euler.x = 0
    ob.matrix_world = Matrix.Translation(ob.location) @ Matrix.Rotation(0 if sgn > 0 else math.pi, 4, 'Z') @ Matrix.Rotation(math.radians(90), 4, 'Y') @ Matrix.Rotation(math.radians(90), 4, 'Z')
    key_hide(ob, [])          # v012: read as tall grey plates on screen; the open cavity reads without them

# ---------------------------------------------------------------- liver group moved into the cavity
sc.frame_set(200)
LV = bpy.data.objects["Liver"]
for fc in list(fcurves(LV)):
    for i in reversed(range(len(fc.keyframe_points))): fc.keyframe_points.remove(fc.keyframe_points[i], fast=True)
LV.location = LV.location; LV.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()
pts = [LV.matrix_world @ Vector(b) for b in LV.bound_box]; c0 = sum(pts, Vector()) / 8
E = bpy.data.objects.new("LiverRig", None); bpy.data.collections["OR_Set"].objects.link(E); E.location = c0
bpy.context.view_layer.update()
E0i = E.matrix_world.inverted()
studio_move = [LV, bpy.data.objects["ArgonPen_Studio"]] + [o for o in bpy.data.objects if o.name.startswith(("Spark_", "Smoke_"))]
for o in studio_move:
    o.parent = E; o.matrix_parent_inverse = E0i.copy()
SCL = 0.74
R = Matrix(((0, 0, -1), (1, 0, 0), (0, -1, 0)))     # studio x -> world +y, studio -y (front) -> +z, studio z -> -x
front_half = (max(p.y for p in pts) - min(p.y for p in pts)) / 2 * SCL
LIVER_C = V(CX + 0.005, CY, SKZ - 0.026 - front_half)
E.matrix_world = Matrix.Translation(LIVER_C) @ (R * SCL).to_4x4() if False else Matrix.Translation(LIVER_C) @ R.to_4x4() @ Matrix.Scale(SCL, 4)
E.keyframe_insert("location", frame=1); E.keyframe_insert("rotation_euler", frame=1); E.keyframe_insert("scale", frame=1)
key_hide(LV, [OR_OPEN1, OR_OPEN2])
for o in LV.children: key_hide(o, [OR_OPEN1, OR_OPEN2])
# studio set gone
for n in ("StudioDome", "StudioMembrane", "Studio_Key", "Studio_Rim", "Studio_Fill", "RevealSpot"):
    o = bpy.data.objects.get(n)
    if o: key_hide(o, [])
for o in bpy.data.objects:
    if o.name.startswith(("Smoke_", "Spark_")): key_hide(o, [])           # v013: no floating sparks
for n in ("EtherDrape", "EtherBar", "EtherPost", "EtherPost.001"):        # v013: no screen hiding her head
    o = bpy.data.objects.get(n)
    if o: key_hide(o, [])
for o in bpy.data.objects["ArgonPen_Studio"].children_recursive:        # v013: dark pen, so the glove reads as one hand
    if o.type == 'MESH' and not o.name.endswith("Tip"):
        m = bpy.data.materials.new("PenDark"); m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.05, 0.06, 0.08, 1); b.inputs["Roughness"].default_value = 0.35
        o.data.materials.clear(); o.data.materials.append(m)
GH = bpy.data.objects["GloveHands"]
for o in [GH] + list(GH.children_recursive): key_hide(o, [])
# the old OR pen (replaced by the one pen that brands)
for o in [bpy.data.objects["ArgonPen_OR"]] + list(bpy.data.objects["ArgonPen_OR"].children_recursive): key_hide(o, [])
# a soft key light over the wound (OR lamps are high; the cavity would be dark)
ld = bpy.data.lights.new("WoundLight", 'AREA'); ld.energy = 25; ld.size = 0.35; ld.color = (1.0, 0.97, 0.92)
wl = bpy.data.objects.new("WoundLight", ld); bpy.data.collections["OR_Set"].objects.link(wl)
wl.location = V(CX + 0.25, CY - 0.1, SKZ + 0.75); wl.rotation_euler = (V(CX, CY, SKZ) - wl.location).to_track_quat('-Z', 'Y').to_euler()
key_hide(wl, [OR_OPEN1, OR_OPEN2])

# ---------------------------------------------------------------- Surgeon 1's own hand holds the pen (no glove-only hands)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v12lib as VL
pen = bpy.data.objects["ArgonPen_Studio"]
TIP = {}
for f in range(1, 281):
    sc.frame_set(f); TIP[f] = pen.matrix_world.translation.copy() + V(0, 0, 0.009)   # 9 mm stand-off: the argon beam
gap = VL.hold_path("Surgeon1", "R", pen, 1, 280, lambda f: TIP[f], 60, head_clear=0.22)
print("PEN hold gap cm", round(gap * 100, 2))
for o in [pen] + list(pen.children_recursive): VL.key_hide(o, [] if o.name.endswith('Cable') else [(0, 280)])
# argon beam: blue plasma cone from the tip to the liver, on while burning (BurnProgress 141-282)
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=12, radius1=0.0007, radius2=0.0028, depth=0.010)
bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, -0.005))
me = bpy.data.meshes.new("ArgonBeam"); bm.to_mesh(me); bm.free()
bmat = bpy.data.materials.new("ArgonBeam"); bmat.use_nodes = True; nt = bmat.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
em = nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (0.45, 0.6, 1.0, 1); em.inputs[1].default_value = 40
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader"); mx.inputs[0].default_value = 0.65
lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.4
nt.links.new(lw.outputs["Facing"], mx.inputs[0]); nt.links.new(em.outputs[0], mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0].inputs[0])
me.materials.append(bmat)
beam = bpy.data.objects.new("ArgonBeam", me); bpy.data.collections["OR_Set"].objects.link(beam)
beam.parent = pen; beam.matrix_parent_inverse = Matrix.Identity(4); beam.location = (0, 0, 0)
VL.key_hide(beam, [(141, 278)])
import json
json.dump({"CX": CX, "CY": CY, "SKZ": SKZ, "CA": CA, "CB": CB, "LIVER_C": list(LIVER_C), "SCL": SCL},
          open(os.path.join(os.path.dirname(OUT), "or_site.json"), "w"))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("OR_DONE", OUT)
