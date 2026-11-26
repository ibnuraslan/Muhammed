"""ElectricianPolice v011 stage 1: the two people, each ONE MPFB model with REAL loose garments.
blender -b --factory-startup? no: needs the MPFB extension ->  blender -b --python 01_people.py -- <out_people.blend>
  Ravi (the electrician): red polo shirt + navy cargo trousers + work shoes (MakeHuman community CC0 garments)
  Officer (traffic police / station officer): khaki polo + khaki wool trousers + black shoes, white peaked cap (ours, rigid)
Bodies stay SOLID: the skin is hidden only where a garment covers it (eroded masks, so every hem/cuff/collar shows skin
or cloth, never a hollow), garments get solidify thickness, the trousers' waistband under the shirt is masked."""
import bpy, bmesh, sys, os, math
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc.render.fps = 60

POLO = "namuhekam_male_polo_shirt/namuhekam_male_polo_shirt.mhclo"
CARGO = "cortu_cargo_pants/cortu_cargo_pants.mhclo"
WOOL = "toigo_wool_pants/toigo_wool_pants.mhclo"
RAVI, RB = human("Ravi", 1.0, 0.45, {"asian": 0.55, "caucasian": 0.30, "african": 0.15}, "short02/short02.mhclo",
                 "young_asian_male/young_asian_male.mhmat", "eyebrow004/eyebrow004.mhclo", height=0.55, muscle=0.45, weight=0.42,
                 shoes="shoes04/shoes04.mhclo", clothes=[POLO, WOOL])
OFF, OB = human("Officer", 1.0, 0.62, {"asian": 0.55, "caucasian": 0.20, "african": 0.25}, "short01/short01.mhclo",
                "middleage_asian_male/middleage_asian_male.mhmat", "eyebrow001/eyebrow001.mhclo", height=0.5, muscle=0.40, weight=0.62,
                shoes="shoes03/shoes03.mhclo", clothes=[POLO, WOOL])
OFF.location.x = 1.2
for r, b in ((RAVI, RB), (OFF, OB)):
    bake_keys(b); eye_fix(r)
# EnhancedEye cornea: refractive transmission -> transparent mix (LESSONS 3), every eye group
for g in [g for g in bpy.data.node_groups if g.name.startswith("EnhancedEye")]:
    P = next((n for n in g.nodes if n.type == "BSDF_PRINCIPLED"), None); OUTN = next((n for n in g.nodes if n.type == "GROUP_OUTPUT"), None)
    if P is None or OUTN is None or "CorneaTransparentMix" in g.nodes: continue
    tl = [l for l in g.links if l.to_node == P and l.to_socket.name == "Transmission Weight"]
    src = tl[0].from_socket if tl else None
    for l in tl: g.links.remove(l)
    P.inputs["Transmission Weight"].default_value = 0.0
    ols = [l for l in g.links if l.from_node == P and l.to_node == OUTN]
    if not ols: continue
    out_sock = ols[0].to_socket; g.links.remove(ols[0])
    tr = g.nodes.new("ShaderNodeBsdfTransparent"); mx = g.nodes.new("ShaderNodeMixShader"); mx.name = "CorneaTransparentMix"
    if src: g.links.new(src, mx.inputs[0])
    else: mx.inputs[0].default_value = 0.0
    g.links.new(P.outputs[0], mx.inputs[1]); g.links.new(tr.outputs[0], mx.inputs[2]); g.links.new(mx.outputs[0], out_sock)
# dark brown irises
for m in bpy.data.materials:
    if m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == 'GROUP' and n.node_tree and n.node_tree.name.startswith("EnhancedEye"):
                n.inputs["IrisMajorColor"].default_value = (0.20, 0.09, 0.03, 1); n.inputs["IrisMinorColor"].default_value = (0.08, 0.035, 0.01, 1)
# warm saturated skin, dark hair
for m in RB.data.materials: tint(m, (1.0, 0.90, 0.82))
for m in OB.data.materials: tint(m, (1.0, 0.90, 0.82))
for r in (RAVI, OFF):
    for c in r.children:
        if c.type == 'MESH' and any(k in c.name for k in ("short0", "eyebrow")):
            for m in c.data.materials: tint(m, (0.16, 0.11, 0.08))

def cl(rig, key, newname):
    o = part(rig, key); o.name = newname; return o
R_TOP = cl(RAVI, "polo", "Ravi.top"); R_TRS = cl(RAVI, "wool_pants", "Ravi.trousers")
O_TOP = cl(OFF, "polo", "Officer.top"); O_TRS = cl(OFF, "wool_pants", "Officer.trousers")
# each garment gets its own material copy (MPFB may share one per asset), then deep saturated colours
for o in (R_TOP, R_TRS, O_TOP, O_TRS):
    o.data.materials[0] = o.data.materials[0].copy()
colorize(R_TOP, (0.78, 0.04, 0.05)); colorize(R_TRS, (0.05, 0.10, 0.30))
colorize(O_TOP, (0.66, 0.50, 0.24)); colorize(O_TRS, (0.50, 0.37, 0.17))

def under_top(trs, top):
    zmin = min((top.matrix_world @ v.co).z for v in top.data.vertices)
    vg = trs.vertex_groups.new(name="under_top"); vg.add([v.index for v in trs.data.vertices if (trs.matrix_world @ v.co).z > zmin + 0.03], 1.0, 'REPLACE')
    mk = trs.modifiers.new("under_top", 'MASK'); mk.vertex_group = "under_top"; mk.invert_vertex_group = True
under_top(R_TRS, R_TOP); under_top(O_TRS, O_TOP)
for body, gar in ((RB, R_TOP), (RB, R_TRS), (OB, O_TOP), (OB, O_TRS)):
    hide_by_proximity(body, gar, "Hide." + gar.name, dist=0.02, rings=3)
    so = gar.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.0035; so.offset = 1.0; so.use_rim = True
    for p in gar.data.polygons: p.use_smooth = True
    print("GARMENT", gar.name, len(gar.data.vertices), [m.type for m in gar.modifiers])
print("BODYMODS", [(m.name, m.type) for m in RB.modifiers], [(m.name, m.type) for m in OB.modifiers])

# ---- rigid head gear (ours): the electrician's hard hat and the officer's peaked cap, both Child Of the head bone
def head_top(rig, body):
    hg = body.vertex_groups["HelperGeometry"].index; jc = body.vertex_groups["JointCubes"].index
    def helper(v): return any(g.group in (hg, jc) and g.weight > 0.5 for g in v.groups)
    vs = [v.co for v in body.data.vertices if v.co.z > bl(rig, "head").z + 0.05 and not helper(v)]
    top = max(v.z for v in vs); cx = 0.0
    band = [v for v in vs if v.z > top - 0.06]          # skull cap only (bbox centre, not the dense face mean)
    cy = (min(v.y for v in band) + max(v.y for v in band)) / 2
    return Vector((cx, cy, top))

def annulus(name, rin_x, rin_y, rout_x, rout_y, front=1.0, thick=0.006, seg=64, z=0.0):
    """a flat ring (hat brim / visor base): inner ellipse -> outer ellipse, the front (-y) half pushed out by `front`"""
    me = bpy.data.meshes.new(name); bm = bmesh.new(); inner = []; outer = []
    for k in range(seg):
        a = 2 * math.pi * k / seg; c, s_ = math.cos(a), math.sin(a)
        inner.append(bm.verts.new((rin_x * c, rin_y * s_, z)))
        fo = front if s_ < 0 else 1.0
        outer.append(bm.verts.new((rout_x * c, rout_y * s_ * (1 + (fo - 1) * abs(s_)), z)))
    for k in range(seg):
        bm.faces.new((inner[k], inner[(k + 1) % seg], outer[(k + 1) % seg], outer[k]))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    so = o.modifiers.new("s", 'SOLIDIFY'); so.thickness = thick; so.offset = 0.0
    bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.object.modifier_apply(modifier="s")
    return o

def hard_hat(rig, body):
    t = head_top(rig, body)
    yel = mat("M_HardHat", (1.0, 0.62, 0.0), rough=0.35, coat=0.4)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.125, segments=40, ring_count=20, location=(0, 0, 0))
    h = bpy.context.active_object; h.name = "Ravi.hardhat"
    bm = bmesh.new(); bm.from_mesh(h.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.002], context='VERTS')
    for v in bm.verts:
        v.co.x *= 0.84; v.co.y *= 1.0; v.co.z *= 1.0
    bm.to_mesh(h.data); bm.free()
    so = h.modifiers.new("s", 'SOLIDIFY'); so.thickness = 0.006
    # brim: a flat ring, longer at the front (-y)
    br = annulus("brim", 0.105 * 0.84, 0.105, 0.122 * 0.90, 0.122, front=1.30, thick=0.007)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.121, minor_radius=0.009, major_segments=64, minor_segments=10, location=(0, 0, 0), rotation=(0, math.pi / 2, 0))
    ridge = bpy.context.active_object      # the moulded centre rib, front to back ON the dome's outer surface
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    bm = bmesh.new(); bm.from_mesh(ridge.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < 0.03], context='VERTS'); bm.to_mesh(ridge.data); bm.free()
    for o in (h, br, ridge):
        o.data.materials.clear(); o.data.materials.append(yel)
    bpy.ops.object.select_all(action='DESELECT')
    for o in (h, br, ridge): o.select_set(True)
    bpy.context.view_layer.objects.active = h
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.join(); bpy.ops.object.shade_smooth()
    h.location = t + Vector((0, 0.004, -0.075)); h.rotation_euler = (math.radians(-6), 0, 0)
    return h

def peaked_cap(rig, body):
    t = head_top(rig, body)
    white = mat("M_CapTop", (0.92, 0.90, 0.84), rough=0.55); band = mat("M_CapBand", (0.05, 0.06, 0.12), rough=0.5)
    visor = mat("M_CapVisor", (0.02, 0.02, 0.02), rough=0.25, coat=0.6); gold = mat("M_CapBadge", (0.95, 0.70, 0.15), rough=0.25, metal=1.0)
    parts = []
    bpy.ops.mesh.primitive_cylinder_add(radius=0.098, depth=0.05, vertices=48, location=(0, 0, 0.025), end_fill_type='NOTHING'); b_ = bpy.context.active_object
    b_.scale = (0.90, 1.05, 1); b_.data.materials.append(band); parts.append(b_)
    so = b_.modifiers.new("s", 'SOLIDIFY'); so.thickness = 0.005; so.offset = 1.0
    bpy.context.view_layer.objects.active = b_; bpy.ops.object.modifier_apply(modifier="s")
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.13, segments=48, ring_count=16, location=(0, 0, 0.0)); c_ = bpy.context.active_object
    bm = bmesh.new(); bm.from_mesh(c_.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.001], context='VERTS'); bm.to_mesh(c_.data); bm.free()
    c_.location = (0, 0.004, 0.048); c_.scale = (0.80, 0.92, 0.36); c_.data.materials.append(white); parts.append(c_)
    so = c_.modifiers.new("s", 'SOLIDIFY'); so.thickness = 0.01
    bpy.context.view_layer.objects.active = c_; bpy.ops.object.modifier_apply(modifier="s")
    v_ = annulus("visor", 0.088, 0.103, 0.088, 0.103, front=1.55, thick=0.006)
    bm = bmesh.new(); bm.from_mesh(v_.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y > -0.035], context='VERTS'); bm.to_mesh(v_.data); bm.free()
    v_.location = (0, -0.014, 0.006); v_.rotation_euler = (math.radians(9), 0, 0); v_.data.materials.append(visor); parts.append(v_)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.016, depth=0.006, vertices=24, location=(0, -0.113, 0.03), rotation=(math.pi / 2, 0, 0)); g_ = bpy.context.active_object
    g_.data.materials.append(gold); parts.append(g_)
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active = b_
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.join(); b_.name = "Officer.cap"; bpy.ops.object.shade_smooth()
    b_.location = t + Vector((0, 0.008, -0.062)); b_.rotation_euler = (math.radians(-5), 0, 0)
    return b_

def fit_clear(gear, body, rig, lift_step=0.002, clear=0.004):
    """raise the gear until its inner surface clears the scalp by `clear` (rest pose, sampled on the head's skin)"""
    from mathutils.bvhtree import BVHTree
    bpy.context.view_layer.update(); z0 = gear.location.z
    for _ in range(60):
        me = gear.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
        bvh = BVHTree.FromPolygons([gear.matrix_world @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
        gear.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
        hz = bl(rig, "head").z
        hg = body.vertex_groups["HelperGeometry"].index
        bad = 0
        for v in body.data.vertices:
            if v.co.z < hz + 0.03 or any(g.group == hg and g.weight > 0.5 for g in v.groups): continue
            loc, n, i, d = bvh.find_nearest(body.matrix_world @ v.co)
            if loc is not None and d < clear: bad += 1
        if bad == 0: break
        gear.location.z += lift_step; bpy.context.view_layer.update()
    return bad, round((gear.location.z - z0) * 1000, 1)

HAT = hard_hat(RAVI, RB); CAP = peaked_cap(OFF, OB)
CAP.location.x += OFF.location.x
for gear, rig, body in ((HAT, RAVI, RB), (CAP, OFF, OB)):
    print("FIT", gear.name, fit_clear(gear, body, rig))
    M = gear.matrix_world.copy()
    c = gear.constraints.new('CHILD_OF'); c.target = rig; c.subtarget = "head"
    bpy.context.view_layer.update()
    c.inverse_matrix = (rig.matrix_world @ rig.pose.bones["head"].matrix).inverted()
# hair under the hats: trim cards that would poke through (keep the hairline)
for gear, rig, key in ((HAT, RAVI, "short02"), (CAP, OFF, "short01")):
    hr = part(rig, key)
    if rig is RAVI:      # Ravi is bare-headed on the bike and at the end: keep an untrimmed copy for those beats
        full = hr.copy(); full.data = hr.data.copy(); full.name = "Ravi.hair_full"; sc.collection.objects.link(full)
        hr.name = "Ravi.hair_hat"
    Mg = gear.matrix_world
    p0 = Mg @ Vector((0, 0, 0.004)); n = (Mg.to_3x3() @ Vector((0, 0, 1))).normalized()
    n0 = len(hr.data.vertices)
    trim_hair(hr, None, p0, n, margin=0.004)
    print("HAIR", hr.name, n0, "->", len(hr.data.vertices))
sc["RAVI"] = RAVI.name; sc["OFFICER"] = OFF.name
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("PEOPLE_OK", OUT)
