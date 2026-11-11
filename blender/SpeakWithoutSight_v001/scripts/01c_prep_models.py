"""Normalise the CC-BY anatomy and prop models (hand skeleton, larynx, footstool, open book) into models.blend.
blender -b --factory-startup --python 01c_prep_models.py -- <glb_dir> <out.blend>
Hand skeleton: origin at the wrist, +Y wrist->middle fingertip, +X towards the thumb, unit length (scaled at use).
Larynx: origin at the thyroid cartilage, +Z up the neck, -Y towards the front (Adam's apple), 11 cm tall overall."""
import sys, os, math
import bpy, bmesh
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]; GD, OUT = a[0], a[1]
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
def imp(name):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=os.path.join(GD, name + ".glb"))
    new = [o for o in bpy.data.objects if o not in before]
    ms = [o for o in new if o.type == 'MESH']
    for o in ms:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o.type != 'MESH': bpy.data.objects.remove(o)
    for o in ms:
        o.data = o.data.copy() if o.data.users > 1 else o.data
        o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
    return ms
def join(ms, name):
    for o in bpy.data.objects: o.select_set(False)
    for o in ms: o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]
    if len(ms) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active; ob.name = name; ob.data.name = name; return ob
def wet_mat(name, rgb, sss=0.4, coat=0.5, rough=0.35, noise=600.0, bump=0.15):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Subsurface Weight"].default_value = sss; p.inputs["Subsurface Radius"].default_value = (0.4, 0.2, 0.12); p.inputs["Subsurface Scale"].default_value = 0.004
    p.inputs["Coat Weight"].default_value = coat; p.inputs["Coat Roughness"].default_value = 0.15
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = noise; nz.inputs["Detail"].default_value = 8
    vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = noise * 0.3
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = 'ADD'; nt.links.new(nz.outputs["Fac"], mx.inputs[0]); nt.links.new(vo.outputs["Distance"], mx.inputs[1])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
    nt.links.new(mx.outputs[0], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    # subtle mottling in the colour
    cr = nt.nodes.new("ShaderNodeMix"); cr.data_type = 'RGBA'; cr.inputs["A"].default_value = (*[c * 0.82 for c in rgb], 1); cr.inputs["B"].default_value = (*rgb, 1)
    nt.links.new(nz.outputs["Fac"], cr.inputs["Factor"]); nt.links.new(cr.outputs["Result"], p.inputs["Base Color"])
    return m
def decimate(ob, ratio):
    d = ob.modifiers.new("D", 'DECIMATE'); d.ratio = ratio
    bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier="D")

# ---------------- hand skeleton
hs = join(imp("HandSkeleton"), "Model_HandSkeleton")
V = [v.co.copy() for v in hs.data.vertices]
c = sum(V, Vector()) / len(V)
# principal (long) axis = largest bbox extent
mn = Vector([min(v[i] for v in V) for i in range(3)]); mx_ = Vector([max(v[i] for v in V) for i in range(3)])
ax = max(range(3), key=lambda i: mx_[i] - mn[i])
def width_at(t):
    lo = mn[ax] + (mx_[ax] - mn[ax]) * t; band = [v for v in V if abs(v[ax] - lo) < (mx_[ax] - mn[ax]) * 0.06]
    if not band: return 0
    o2 = [i for i in range(3) if i != ax]
    return max(max(v[o2[0]] for v in band) - min(v[o2[0]] for v in band), max(v[o2[1]] for v in band) - min(v[o2[1]] for v in band))
wrist_low = width_at(0.06) < width_at(0.94)       # fingers spread wider than the wrist
sgn = 1 if wrist_low else -1
along = [v[ax] * sgn for v in V]; a0, a1 = min(along), max(along)
wrist_pts = [v for v, s in zip(V, along) if s < a0 + (a1 - a0) * 0.05]; wrist = sum(wrist_pts, Vector()) / len(wrist_pts)
tip = max(V, key=lambda v: v[ax] * sgn)
mid = [v for v, s in zip(V, along) if a0 + (a1 - a0) * 0.3 < s < a0 + (a1 - a0) * 0.75]
axis_v = (tip - wrist).normalized()
def lat(v): d = v - wrist; return d - axis_v * d.dot(axis_v)
thumb = max(mid, key=lambda v: lat(v).length)
Y = axis_v; X = lat(thumb).normalized(); Z = X.cross(Y)
R = Matrix((X, Y, Z))            # rows: maps model -> canonical (x thumb, y fingers, z palm-ish)
L = (tip - wrist).length
hs.data.transform(Matrix.Scale(1 / L, 4) @ R.to_4x4() @ Matrix.Translation(-wrist))
print("HAND len", L, "wrist_low", wrist_low)
hs.data.materials.clear(); hs.data.materials.append(wet_mat("M_HandBone", (0.88, 0.84, 0.74), sss=0.35, coat=0.25, rough=0.4, noise=900, bump=0.08))
for p in hs.data.polygons: p.use_smooth = True

# ---------------- larynx
lx_parts = imp("Larynx")
cart = wet_mat("M_Cartilage", (0.86, 0.84, 0.78), sss=0.5, coat=0.6, rough=0.3, noise=4000, bump=0.1)
lig = wet_mat("M_Ligament", (0.72, 0.42, 0.36), sss=0.6, coat=0.7, rough=0.3, noise=3000, bump=0.12)
bonem = wet_mat("M_HyoidBone", (0.86, 0.8, 0.68), sss=0.3, coat=0.3, rough=0.45, noise=3500, bump=0.1)
muc = wet_mat("M_Mucosa", (0.78, 0.38, 0.36), sss=0.7, coat=0.8, rough=0.25, noise=3000, bump=0.1)
thy = None
for o in lx_parts:
    n = o.name.lower()
    mat = lig if ("ligament" in n or "membrane" in n or "muscle" in n) else (bonem if "hyoid" in n else (muc if ("fold" in n or "vocal" in n or "mucos" in n) else cart))
    o.data.materials.clear(); o.data.materials.append(mat)
    if "thyroid" in n and "ligament" not in n and "membrane" not in n: thy = o
print("LARYNX parts", [o.name for o in lx_parts])
lx = join(lx_parts, "Model_Larynx")
for o_ in bpy.data.objects: o_.select_set(False)
lx.select_set(True); bpy.context.view_layer.objects.active = lx
bm_ = bmesh.new(); bm_.from_mesh(lx.data); bmesh.ops.remove_doubles(bm_, verts=bm_.verts, dist=lx.dimensions.length * 1e-5); bm_.to_mesh(lx.data); bm_.free()
print("LARYNX welded", len(lx.data.vertices))
dmod = lx.modifiers.new("D", 'DECIMATE'); dmod.ratio = 40000 / len(lx.data.vertices); dmod.use_collapse_triangulate = True
dg_ = bpy.context.evaluated_depsgraph_get(); newm = bpy.data.meshes.new_from_object(lx.evaluated_get(dg_))
lx.modifiers.remove(dmod); oldm = lx.data; lx.data = newm; bpy.data.meshes.remove(oldm); print("LARYNX decimated", len(newm.vertices))
P = [v.co for v in lx.data.vertices]
lmn = Vector([min(v[i] for v in P) for i in range(3)]); lmx = Vector([max(v[i] for v in P) for i in range(3)])
H = lmx.z - lmn.z
center = (lmn + lmx) / 2
# front = side where the thyroid cartilage sticks out most (Adam's apple)
thy_c = None
if thy:
    pass
s = 0.11 / H
lx.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation(-Vector((center.x, center.y, lmn.z + H * 0.72))))
# front detection after scaling: the hemisphere (+/-Y) with the farther-reaching vertices near the top third
P = [v.co for v in lx.data.vertices]; top = [v for v in P if v.z > -0.01]
fr = max(top, key=lambda v: abs(v.y)); front_sign = -1 if fr.y < 0 else 1
if front_sign > 0: lx.data.transform(Matrix.Rotation(math.pi, 4, 'Z'))
print("LARYNX H", H, "scale", s, "front_sign", front_sign)
for p in lx.data.polygons: p.use_smooth = True
# ---------------- footstool and open book
fs = join(imp("Footstool"), "Model_Footstool")
for p in fs.data.polygons: p.use_smooth = True
bk = join(imp("OpenBook"), "Model_OpenBook")
P = [v.co for v in bk.data.vertices]; bmn = Vector([min(v[i] for v in P) for i in range(3)]); bmx = Vector([max(v[i] for v in P) for i in range(3)])
bk.data.transform(Matrix.Scale(0.30 / max(bmx.x - bmn.x, bmx.y - bmn.y), 4) @ Matrix.Translation(-(bmn + bmx) / 2))
for o in (hs, lx, fs, bk): o.location = (0, 0, 0)
for o in list(bpy.data.objects):
    if o not in (hs, lx, fs, bk): bpy.data.objects.remove(o)
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("MODELS_OK", [(o.name, len(o.data.vertices), tuple(round(d, 3) for d in o.dimensions)) for o in (hs, lx, fs, bk)])
