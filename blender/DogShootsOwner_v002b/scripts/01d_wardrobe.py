"""DogShootsOwner v002b wardrobe (director: no one-colour 'onesie' suits).
blender -b lib3.blend --python 01d_wardrobe.py -- lib4.blend

Owner: the collared button shirt + jeans + belt mesh (MakeHuman male_casualsuit01, CC0) refitted from MedA's body to
       the Owner's body (same MPFB topology: barycentric position on the nearest body triangle + normal offset),
       recoloured as a red/brown flannel plaid shirt over blue denim with the dark leather belt.
       His old jumper/trousers mesh (male_casualsuit02) is removed and the body's delete mask follows the new suit.
MedA:  same mesh he already wears, recoloured as an EMS shirt (royal blue) over dark charcoal work trousers + belt.
The shirt and the jeans sit in separate UV islands of the suit texture: the jeans/belt column is u 0.36-0.725.
"""
import bpy, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT = sys.argv[sys.argv.index("--") + 1]
OB = bpy.data.objects
own, med = OB["Owner"], OB["MedA"]


def rest_mesh(o, rig):
    """world-space rest-pose vertex positions of o (armature at rest, masks/subsurf off)."""
    keep = []
    for m in o.modifiers:
        if m.type in ('MASK', 'SUBSURF'):
            keep.append((m, m.show_viewport)); m.show_viewport = False
    pp = rig.data.pose_position; rig.data.pose_position = 'REST'
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    e = o.evaluated_get(dg); me = e.to_mesh()
    vs = [e.matrix_world @ v.co for v in me.vertices]
    tris = [tuple(t.vertices) for t in me.loop_triangles] if me.loop_triangles else None
    if tris is None:
        me.calc_loop_triangles(); tris = [tuple(t.vertices) for t in me.loop_triangles]
    e.to_mesh_clear()
    rig.data.pose_position = pp
    for m, s in keep: m.show_viewport = s
    return vs, tris


# ---------------------------------------------------------------- 1. refit MedA's suit onto the Owner
src_body, dst_body = OB["MedA.body"], OB["Owner.body"]
src_cloth = OB["MedA.male_casualsuit01"]
sb, tris = rest_mesh(src_body, med)
db, _ = rest_mesh(dst_body, own)
sc_, _ = rest_mesh(src_cloth, med)
assert len(sb) == len(db), (len(sb), len(db))
bvh = BVHTree.FromPolygons(sb, tris)


def tri_frame(P, t):
    a, b, c = (P[i] for i in t)
    n = (b - a).cross(c - a)
    return a, b, c, (n.normalized() if n.length > 1e-12 else Vector((0, 0, 1)))


new_co = []
for p in sc_:
    loc, nrm, ti, d = bvh.find_nearest(p)
    t = tris[ti]
    a, b, c, n = tri_frame(sb, t)
    # barycentric of the closest point
    v0, v1, v2 = b - a, c - a, loc - a
    d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
    den = d00 * d11 - d01 * d01 or 1e-12
    wv = (d11 * d20 - d01 * d21) / den; ww = (d00 * d21 - d01 * d20) / den; wu = 1 - wv - ww
    off = (p - loc).dot(n)
    A, Bv, C, N = tri_frame(db, t)
    new_co.append(A * wu + Bv * wv + C * ww + N * off)

cl = src_cloth.copy(); cl.data = src_cloth.data.copy(); cl.name = "Owner.male_casualsuit01"
for c in src_cloth.users_collection: c.objects.link(cl)
cl.parent = own; cl.matrix_parent_inverse = own.matrix_world.inverted()
cl.matrix_world = own.matrix_world.copy()
inv = cl.matrix_world.inverted()
for v, co in zip(cl.data.vertices, new_co): v.co = inv @ co
for m in cl.modifiers:
    if m.type == 'ARMATURE': m.object = own
# same smoothing as his other meshes
if not any(m.type == 'SUBSURF' for m in cl.modifiers):
    ss = cl.modifiers.new("Subdivision", 'SUBSURF'); ss.levels = 1; ss.render_levels = 1
print("WARD refit", cl.name, len(cl.data.vertices))

# body delete mask: copy MedA's 'Delete.male_casualsuit01' weights by index onto the Owner body
gsrc = src_body.vertex_groups["Delete.male_casualsuit01"]
gdst = dst_body.vertex_groups.get("Delete.male_casualsuit01") or dst_body.vertex_groups.new(name="Delete.male_casualsuit01")
idx = gsrc.index; keep_idx = []
for v in src_body.data.vertices:
    for g in v.groups:
        if g.group == idx and g.weight > 0.5: keep_idx.append(v.index)
gdst.add(keep_idx, 1.0, 'REPLACE')
for m in dst_body.modifiers:
    if m.type == 'MASK' and m.vertex_group == "Delete.male_casualsuit02":
        m.vertex_group = "Delete.male_casualsuit01"
old = OB["Owner.male_casualsuit02"]
bpy.data.objects.remove(old, do_unlink=True)
print("WARD mask verts", len(keep_idx))


# ---------------------------------------------------------------- 2. materials
def diffuse_tex(m):
    for n in m.node_tree.nodes:
        if n.type == 'TEX_IMAGE' and n.image and 'diffuse' in n.image.name.lower(): return n.image
    return next((n.image for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image), None)


def outfit_material(name, img, shirt_fn, pants_rgb, belt_rgb=(0.05, 0.035, 0.025)):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N, L = nt.nodes, nt.links
    P = N["Principled BSDF"]; P.inputs["Roughness"].default_value = 0.75
    uv = N.new("ShaderNodeTexCoord")
    tx = N.new("ShaderNodeTexImage"); tx.image = img; L.new(uv.outputs["UV"], tx.inputs["Vector"])
    lum = N.new("ShaderNodeRGBToBW"); L.new(tx.outputs["Color"], lum.inputs["Color"])
    # shade = fabric detail (folds, seams, buttons) around 1.0
    sh = N.new("ShaderNodeMapRange"); sh.inputs["From Min"].default_value = 0.05; sh.inputs["From Max"].default_value = 0.45
    sh.inputs["To Min"].default_value = 0.45; sh.inputs["To Max"].default_value = 1.25; L.new(lum.outputs[0], sh.inputs["Value"])
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(uv.outputs["UV"], sep.inputs[0])
    # jeans column mask
    g1 = N.new("ShaderNodeMath"); g1.operation = 'GREATER_THAN'; g1.inputs[1].default_value = 0.36; L.new(sep.outputs[0], g1.inputs[0])
    g2 = N.new("ShaderNodeMath"); g2.operation = 'LESS_THAN'; g2.inputs[1].default_value = 0.725; L.new(sep.outputs[0], g2.inputs[0])
    jm = N.new("ShaderNodeMath"); jm.operation = 'MULTIPLY'; L.new(g1.outputs[0], jm.inputs[0]); L.new(g2.outputs[0], jm.inputs[1])
    shirt = shirt_fn(N, L, sep)
    pants = N.new("ShaderNodeRGB"); pants.outputs[0].default_value = (*pants_rgb, 1)
    # the belt is the darkest band of the jeans texture: keep it leather-dark
    at = N.new("ShaderNodeAttribute"); at.attribute_name = "belt"
    blt = N.new("ShaderNodeMath"); blt.operation = 'GREATER_THAN'; blt.inputs[1].default_value = 0.5; L.new(at.outputs["Fac"], blt.inputs[0])
    pb = N.new("ShaderNodeMix"); pb.data_type = 'RGBA'; L.new(blt.outputs[0], pb.inputs["Factor"])
    L.new(pants.outputs[0], pb.inputs["A"]); pb.inputs["B"].default_value = (*belt_rgb, 1)
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(jm.outputs[0], mx.inputs["Factor"])
    L.new(shirt, mx.inputs["A"]); L.new(pb.outputs["Result"], mx.inputs["B"])
    mul = N.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs["Factor"].default_value = 1.0
    L.new(mx.outputs["Result"], mul.inputs["A"])
    shc = N.new("ShaderNodeCombineColor"); [L.new(sh.outputs[0], shc.inputs[i]) for i in range(3)]
    L.new(shc.outputs[0], mul.inputs["B"])
    L.new(mul.outputs["Result"], P.inputs["Base Color"])
    return m


def flannel(N, L, sep):
    """red/brown plaid: two crossing stripe sets on the shirt's UVs"""
    def stripes(axis_out, freq, width):
        mm = N.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = freq; L.new(axis_out, mm.inputs[0])
        fr = N.new("ShaderNodeMath"); fr.operation = 'FRACT'; L.new(mm.outputs[0], fr.inputs[0])
        lt = N.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = width; L.new(fr.outputs[0], lt.inputs[0])
        return lt.outputs[0]
    su, sv = stripes(sep.outputs[0], 30.0, 0.32), stripes(sep.outputs[1], 30.0, 0.32)
    tu, tv = stripes(sep.outputs[0], 30.0, 0.06), stripes(sep.outputs[1], 30.0, 0.06)
    base = N.new("ShaderNodeRGB"); base.outputs[0].default_value = (0.42, 0.06, 0.045, 1)       # brick red
    dark = N.new("ShaderNodeRGB"); dark.outputs[0].default_value = (0.10, 0.035, 0.03, 1)       # dark band
    thin = N.new("ShaderNodeRGB"); thin.outputs[0].default_value = (0.55, 0.42, 0.20, 1)       # mustard thread
    a = N.new("ShaderNodeMath"); a.operation = 'MAXIMUM'; L.new(su, a.inputs[0]); L.new(sv, a.inputs[1])
    m1 = N.new("ShaderNodeMix"); m1.data_type = 'RGBA'; L.new(a.outputs[0], m1.inputs["Factor"])
    L.new(base.outputs[0], m1.inputs["A"]); L.new(dark.outputs[0], m1.inputs["B"])
    both = N.new("ShaderNodeMath"); both.operation = 'MULTIPLY'; L.new(su, both.inputs[0]); L.new(sv, both.inputs[1])
    m2 = N.new("ShaderNodeMix"); m2.data_type = 'RGBA'; m2.inputs["Factor"].default_value = 0.0
    L.new(both.outputs[0], m2.inputs["Factor"]); L.new(m1.outputs["Result"], m2.inputs["A"])
    m2.inputs["B"].default_value = (0.06, 0.02, 0.02, 1)
    t = N.new("ShaderNodeMath"); t.operation = 'MAXIMUM'; L.new(tu, t.inputs[0]); L.new(tv, t.inputs[1])
    m3 = N.new("ShaderNodeMix"); m3.data_type = 'RGBA'; L.new(t.outputs[0], m3.inputs["Factor"])
    L.new(m2.outputs["Result"], m3.inputs["A"]); L.new(thin.outputs[0], m3.inputs["B"])
    return m3.outputs["Result"]


def solid(rgb):
    def f(N, L, sep):
        c = N.new("ShaderNodeRGB"); c.outputs[0].default_value = (*rgb, 1); return c.outputs[0]
    return f


def add_belt(o, rest_world):
    """per-vertex 'belt' = 1 on the top 4 cm of the jeans (rest pose); the jeans are the u 0.36-0.725 UV column"""
    me = o.data; uvl = me.uv_layers.active.data
    jeans = set()
    for poly in me.polygons:
        us = [uvl[li].uv.x for li in poly.loop_indices]
        if all(0.36 < u < 0.725 for u in us): jeans.update(poly.vertices)
    cx = sum(rest_world[i].x for i in jeans) / len(jeans)
    shirt = [i for i in range(len(me.vertices)) if i not in jeans and abs(rest_world[i].x - cx) < 0.17]
    ztop = min(rest_world[i].z for i in shirt)          # the shirt hem: the belt shows just below it
    att = me.attributes.get("belt") or me.attributes.new("belt", 'FLOAT', 'POINT')
    n = 0
    for v in me.vertices:
        z = rest_world[v.index].z
        b = 1.0 if (v.index in jeans and ztop - 0.045 < z < ztop + 0.02) else 0.0
        att.data[v.index].value = b; n += b > 0
    print("WARD belt", o.name, "jeans", len(jeans), "belt", n, "ztop", round(ztop, 3))
add_belt(cl, new_co); add_belt(src_cloth, sc_)

img = diffuse_tex(src_cloth.data.materials[0])
if img.packed_file is None:
    try: img.pack()
    except Exception: pass
m_own = outfit_material("Owner_flannel_jeans", img, flannel, (0.10, 0.17, 0.32))
m_med = outfit_material("MedA_EMS", img, solid((0.09, 0.20, 0.50)), (0.035, 0.04, 0.045))
cl.data.materials.clear(); cl.data.materials.append(m_own)
src_cloth.data.materials.clear(); src_cloth.data.materials.append(m_med)
print("WARD materials", m_own.name, m_med.name, img.name)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("WARD SAVED", OUT)
