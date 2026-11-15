"""Humpback whale: import the CC-BY model (K9239), cut the mouth along the mouth line, rig it (root, head, jaw, spine,
tail, fluke, flippers), give it a pink inner mouth shell, baleen plates and a clean slate-grey/white look.
blender -b --factory-startup -P 02_whale.py -- whale_hp.glb out.blend"""
import bpy, bmesh, sys, math
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]; SRC, OUT = a[0], a[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
sc = bpy.context.scene

# ---- flatten hierarchy, join the barnacles into the body ---------------------------------------------------------
meshes = [o for o in sc.objects if o.type == 'MESH']
for o in meshes:
    M = o.matrix_world.copy(); o.parent = None; o.matrix_world = M
for o in list(sc.objects):
    if o.type != 'MESH': bpy.data.objects.remove(o)
body = next(o for o in meshes if o.name.startswith("body"))
eyes = [o for o in meshes if "eye" in o.name]
barn = [o for o in meshes if "hujitubo" in o.name]
for o in meshes: o.select_set(False)
bpy.context.view_layer.objects.active = body
for o in barn: bpy.data.objects.remove(o)
for o in eyes + [body]:
    bpy.context.view_layer.objects.active = o; o.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
body.name = "Whale_body"; body.data.name = "Whale_body"
for i, e in enumerate(eyes): e.name = "Whale_eye_" + "LR"[i]

# ---- mouth line (side view, measured from ortho renders) ----------------------------------------------------------
ML = [(-8.30, 1.28), (-7.5, 1.33), (-6.5, 1.42), (-6.0, 1.47), (-5.6, 1.33), (-5.2, 1.00), (-4.85, 0.70), (-4.70, 0.55)]
def mouth_z(x):
    if x <= ML[0][0]: return ML[0][1]
    for (x0, z0), (x1, z1) in zip(ML, ML[1:]):
        if x <= x1: return z0 + (z1 - z0) * (x - x0) / (x1 - x0)
    return ML[-1][1]
CORNER_X = -5.35
me = body.data
bm = bmesh.new(); bm.from_mesh(me)
nb0 = sum(1 for e in bm.edges if e.is_boundary)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.002)
print("BOUNDARY before/after merge", nb0, sum(1 for e in bm.edges if e.is_boundary))
bm.faces.ensure_lookup_table()
lower = set()
for f in bm.faces:
    c = f.calc_center_median()
    if c.x < CORNER_X + 0.6 and c.z < mouth_z(c.x): lower.add(f.index)
def _front(f): return f.calc_center_median().x < CORNER_X
cut = [e for e in bm.edges if len(e.link_faces) == 2 and ((e.link_faces[0].index in lower) != (e.link_faces[1].index in lower))
       and _front(e.link_faces[0]) and _front(e.link_faces[1])]
for v in set(v for e in cut for v in e.verts):
    v.co.z = mouth_z(v.co.x)
upper_lip = [v.co.copy() for e in cut for v in e.verts]
bmesh.ops.split_edges(bm, edges=cut)
bm.faces.ensure_lookup_table()
low_verts = set(v.index for f in bm.faces if f.index in lower for v in f.verts)
bm.to_mesh(me); bm.free()
print("SPLIT edges", len(cut), "lower faces", len(lower), "lip pts", len(upper_lip))

# ---- armature --------------------------------------------------------------------------------------------------------
xs = [v.co.x for v in me.vertices]
fl = [v.co for v in me.vertices if abs(v.co.y) > 1.6 and v.co.z < 0.0 and -5.5 < v.co.x < 0.5]
fl_root = {}
for s, sg in (("L", 1), ("R", -1)):
    pts = [p for p in fl if p.y * sg > 0]
    inner = sorted(pts, key=lambda p: abs(p.y))[:max(1, len(pts) // 12)]
    outer = sorted(pts, key=lambda p: -abs(p.y))[:max(1, len(pts) // 12)]
    fl_root[s] = (sum(inner, Vector()) / len(inner), sum(outer, Vector()) / len(outer))
    print("FLIPPER", s, fl_root[s])
arm = bpy.data.armatures.new("WhaleRig"); rig = bpy.data.objects.new("WhaleRig", arm); sc.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones
def bone(n, h, t, p=None):
    b = eb.new(n); b.head, b.tail = Vector(h), Vector(t); b.roll = 0
    if p: b.parent = eb[p]
    return b
bone("root", (-1.5, 0, 0.2), (-0.5, 0, 0.2))
bone("head", (-3.0, 0, 0.4), (-8.0, 0, 0.9), "root")
bone("jaw", (-5.15, 0, 0.95), (-8.1, 0, 0.75), "head")
bone("sp1", (-1.5, 0, 0.2), (2.5, 0, 0.2), "root")
bone("sp2", (2.5, 0, 0.2), (5.5, 0, 0.1), "sp1")
bone("tail", (5.5, 0, 0.1), (7.3, 0, 0.05), "sp2")
bone("fluke", (7.3, 0, 0.05), (8.2, 0, 0.0), "tail")
for s in "LR":
    bone("flip." + s, fl_root[s][0], fl_root[s][1], "root")
bpy.ops.object.mode_set(mode='OBJECT')

# ---- weights ---------------------------------------------------------------------------------------------------------
CP = [("head", -5.6), ("root", -2.2), ("sp1", 0.8), ("sp2", 4.0), ("tail", 6.4), ("fluke", 7.8)]
groups = {n: body.vertex_groups.new(name=n) for n in ["root", "head", "jaw", "sp1", "sp2", "tail", "fluke", "flip.L", "flip.R"]}
def sstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0))); return t * t * (3 - 2 * t)
flipset = {}
for s, sg in (("L", 1), ("R", -1)):
    r0, r1 = fl_root[s]
    for v in me.vertices:
        p = v.co
        if p.y * sg > 0 and p.z < 0.2 and -5.8 < p.x < 0.8:
            d = (p - r0).dot((r1 - r0).normalized())
            if abs(p.y) > abs(r0.y) - 0.1 and d > -0.2:
                flipset[v.index] = (s, sstep(-0.2, 0.6, d))
for v in me.vertices:
    x = v.co.x; w = {}
    if x <= CP[0][1]: w[CP[0][0]] = 1.0
    elif x >= CP[-1][1]: w[CP[-1][0]] = 1.0
    else:
        for (n0, x0), (n1, x1) in zip(CP, CP[1:]):
            if x0 <= x <= x1:
                t = sstep(x0, x1, x); w[n0] = 1 - t; w[n1] = t; break
    if v.index in low_verts:
        j = sstep(CORNER_X + 0.35, CORNER_X - 0.45, x)
        w = {k: val * (1 - j) for k, val in w.items()}; w["jaw"] = j
    elif x < -2.6 and v.co.z < 0.2 and x > CORNER_X - 0.1:      # throat behind the corner follows the jaw a little
        j = 0.5 * sstep(-2.6, CORNER_X, x) * sstep(0.2, -0.8, v.co.z)
        w = {k: val * (1 - j) for k, val in w.items()}; w["jaw"] = j
    if v.index in flipset:
        s, k = flipset[v.index]
        w = {kk: val * (1 - k) for kk, val in w.items()}; w["flip." + s] = k
    for n, val in w.items():
        if val > 1e-4: groups[n].add([v.index], val, 'REPLACE')
md = body.modifiers.new("Armature", 'ARMATURE'); md.object = rig
body.parent = rig
for e in eyes:
    e.parent = rig; ev = e.vertex_groups.new(name="head"); ev.add(list(range(len(e.data.vertices))), 1.0, 'REPLACE')
    em = e.modifiers.new("Armature", 'ARMATURE'); em.object = rig

# ---- materials: clean slate-grey back, white belly, pink inner mouth ------------------------------------------------
mat = body.data.materials[0]; nt = mat.node_tree; N = nt.nodes; L = nt.links
P = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
base_link = next((l for l in nt.links if l.to_socket == P.inputs['Base Color']), None)
tex = base_link.from_node if base_link else None
# procedural colouring (robust): dark slate back, white throat/belly by object-space normal, texture adds mottling
tc = N.new('ShaderNodeTexCoord'); sxyz = N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Normal'], sxyz.inputs[0])
mr = N.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -0.15; mr.inputs['From Max'].default_value = -0.55
L.new(sxyz.outputs['Z'], mr.inputs[0])
mixc = N.new('ShaderNodeMix'); mixc.data_type = 'RGBA'; mixc.inputs['A'].default_value = (0.045, 0.06, 0.08, 1); mixc.inputs['B'].default_value = (0.80, 0.83, 0.86, 1)
if tex:
    lum = N.new('ShaderNodeRGBToBW'); L.new(tex.outputs['Color'], lum.inputs[0])
    mott = N.new('ShaderNodeMapRange'); mott.inputs['From Min'].default_value = 0.0; mott.inputs['From Max'].default_value = 0.12
    mott.inputs['To Min'].default_value = -0.25; mott.inputs['To Max'].default_value = 0.35; L.new(lum.outputs[0], mott.inputs[0])
    add = N.new('ShaderNodeMath'); add.operation = 'ADD'; add.use_clamp = True; L.new(mr.outputs[0], add.inputs[0]); L.new(mott.outputs[0], add.inputs[1])
    L.new(add.outputs[0], mixc.inputs['Factor'])
else:
    L.new(mr.outputs[0], mixc.inputs['Factor'])
for l in list(nt.links):
    if l.to_socket == P.inputs['Base Color']: nt.links.remove(l)
L.new(mixc.outputs['Result'], P.inputs['Base Color'])
P.inputs['Roughness'].default_value = 0.42
for l in list(nt.links):
    if l.to_socket == P.inputs['Roughness'] or l.to_socket == P.inputs['Metallic']: nt.links.remove(l)
P.inputs['Metallic'].default_value = 0.0
for n in N:
    if n.type == 'NORMAL_MAP': n.inputs['Strength'].default_value = 0.35
pink = bpy.data.materials.new("Whale_mouth"); pink.use_nodes = True
pp = pink.node_tree.nodes["Principled BSDF"]; pp.inputs['Base Color'].default_value = (0.85, 0.36, 0.42, 1)
pp.inputs['Roughness'].default_value = 0.38; pp.inputs['Subsurface Weight'].default_value = 0.0
pp.inputs['Coat Weight'].default_value = 0.4
lip = bpy.data.materials.new("Whale_lip"); lip.use_nodes = True
lip.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.2, 0.22, 0.26, 1)
lip.node_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = 0.5
body.data.materials.append(pink); body.data.materials.append(lip)
sol = body.modifiers.new("MouthShell", 'SOLIDIFY'); sol.thickness = 0.12; sol.offset = -1
sol.material_offset = 1; sol.material_offset_rim = 2; sol.use_rim = True
bpy.context.view_layer.objects.active = body
while body.modifiers[0].name != "MouthShell": bpy.ops.object.modifier_move_up(modifier="MouthShell")
for e in eyes:
    m = e.data.materials[0]; pe = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for l in list(m.node_tree.links):
        if l.to_socket == pe.inputs['Base Color']: m.node_tree.links.remove(l)
    pe.inputs['Base Color'].default_value = (0.03, 0.03, 0.035, 1); pe.inputs['Roughness'].default_value = 0.15

# ---- baleen plates along the upper lip, hanging inside the mouth -----------------------------------------------------
bal_mat = bpy.data.materials.new("Baleen"); bal_mat.use_nodes = True
bp = bal_mat.node_tree.nodes["Principled BSDF"]; bp.inputs['Base Color'].default_value = (0.045, 0.042, 0.04, 1)   # dark baleen plates, not tooth-white
bp.inputs['Roughness'].default_value = 0.55
pts = sorted([p for p in upper_lip if p.x < CORNER_X - 0.25], key=lambda p: p.x)
bm = bmesh.new(); placed = []
for p in pts:
    if p.x > -5.0 or abs(p.y) < 0.15: continue
    if any((p - q).length < 0.045 for q in placed): continue
    placed.append(p)
    inward = Vector((0, -math.copysign(1, p.y), 0)) if abs(p.y) > 0.05 else Vector((0, 0, 0))
    top = p + inward * 0.10 + Vector((0, 0, 0.12)); h = 0.45 + 0.25 * sstep(-8.0, -5.6, p.x)
    w = 0.30; t = 0.012
    d = inward * w
    vs = [bm.verts.new(top + Vector((dx, 0, 0)) + dd + Vector((0, 0, dz)))
          for dx, dd, dz in [(-t, Vector(), 0), (t, Vector(), 0), (t, d, 0), (-t, d, 0),
                             (-t, Vector(), -h), (t, Vector(), -h), (t, d * 0.4, -h * 0.85), (-t, d * 0.4, -h * 0.85)]]
    for f in [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]:
        bm.faces.new([vs[i] for i in f])
bal = bpy.data.meshes.new("Baleen"); bm.to_mesh(bal); bm.free()
bo = bpy.data.objects.new("Whale_baleen", bal); sc.collection.objects.link(bo); bal.materials.append(bal_mat)
vg = bo.vertex_groups.new(name="head"); vg.add(list(range(len(bal.vertices))), 1.0, 'REPLACE')
bo.parent = rig; m2 = bo.modifiers.new("Armature", 'ARMATURE'); m2.object = rig
print("BALEEN plates", len(placed))
rig["whale"] = 1
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("WHALE_DONE", OUT)
