"""EarInArm v015 stage A: characters, wardrobe, set, props, look. Built from scratch.
blender -b --python 01_build.py -- <dl_dir> <out.blend>
Layout (metres, Z up, characters face -Y):
  patient seated at the origin, right arm (-X side) on an arm board, healed earless site on the RIGHT side of his head;
  surgeon stands behind the arm board at (-0.62, 0.32), facing the camera side; tray on a trolley at his front-right."""
import bpy, bmesh, sys, math, random
from mathutils import Vector, Matrix
from bl_ext.user_default.mpfb.services.humanservice import HumanService

a = sys.argv[sys.argv.index("--") + 1:]
DL, OUT = a[0], a[1]
R_ = math.radians
random.seed(7)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
sc.render.fps = 60
sc.frame_start, sc.frame_end = 1, 1572
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920

# ------------------------------------------------------------------ materials
def mat(name, col, rough=0.5, metal=0.0, sss=0.0, coat=0.0, sheen=0.0, emit=None, alpha=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*col, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if sss:
        p.inputs["Subsurface Weight"].default_value = sss
        p.inputs["Subsurface Radius"].default_value = (0.9, 0.35, 0.2)
        p.inputs["Subsurface Scale"].default_value = 0.004
    if coat:
        p.inputs["Coat Weight"].default_value = coat
    if sheen:
        p.inputs["Sheen Weight"].default_value = sheen
    if emit:
        p.inputs["Emission Color"].default_value = (*emit[0], 1)
        p.inputs["Emission Strength"].default_value = emit[1]
    return m

def fabric(name, col, scale=900.0, bump=0.25):
    """solid-colour cloth with a fine weave bump (clean animated look)"""
    m = mat(name, col, rough=0.8, sheen=0.1)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave")
    wv.inputs["Scale"].default_value = scale; wv.inputs["Distortion"].default_value = 2.0
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.0005
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"]); nt.links.new(wv.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m

# ------------------------------------------------------------------ characters
def human(name, gender, age, race, hair, skin, eyebrow, height=0.5, muscle=0.5, weight=0.5):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": gender, "age": age, "muscle": muscle, "weight": weight, "proportions": 0.6,
                         "height": height, "cupsize": 0.5, "firmness": 0.5, "race": race}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = eyebrow
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair
    info["clothes"] = ["shoes03/shoes03.mhclo"]
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 1
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]
    body = [c for c in rig.children if c.type == 'MESH' and c.name.endswith(".body")][0]
    return rig, body

def bake_keys(body):
    """apply the MPFB phenotype shape-key mix into the mesh (so later edits are absolute)"""
    bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); bpy.context.view_layer.objects.active = body
    if body.data.shape_keys:
        bpy.ops.object.shape_key_remove(all=True, apply_mix=True)

def bone_names(rig):
    return {b.name for b in rig.data.bones}

def dom_bone(vgroups_iter, idx2name):
    best = (0.0, None)
    for gi, w in vgroups_iter:
        n = idx2name.get(gi)
        if n and w > best[0]: best = (w, n)
    return best[1]

def in_region(bn, prefixes):
    return bn is not None and any(bn.startswith(p) for p in prefixes)

ARM = ("upperarm", "lowerarm", "wrist", "finger", "metacarpal")
HANDS = ("wrist", "finger", "metacarpal")
HEADB = ("head", "jaw", "neck", "eye", "orbic", "oris", "levator", "risor", "temporal", "tongue")
LEGB = ("upperleg", "lowerleg", "foot", "toe")

def plane_side(co, p0, n):
    return (Vector(co) - Vector(p0)).dot(Vector(n))

def garment(rig, body, name, region, cuts, offset, material, thick=0.003, folds=0.0):
    """R1: one joined garment = duplicate of the body, bisected along clean cut planes, region-filtered,
    pushed out along the normals after the Armature, solidified, smoothed, subdivided.
    region(co, bone) -> bool ; cuts = list of (p0, n) planes (bisected so every hem/cuff/collar is a straight line)."""
    g = body.copy(); g.data = body.data.copy(); g.name = name; g.data.name = name
    bpy.context.collection.objects.link(g); g.parent = rig; g.matrix_world = body.matrix_world.copy()
    idx2name = {vg.index: vg.name for vg in body.vertex_groups if vg.name in bone_names(rig)}
    hg = body.vertex_groups.get("HelperGeometry").index; jc = body.vertex_groups.get("JointCubes").index
    bm = bmesh.new(); bm.from_mesh(g.data)
    dl = bm.verts.layers.deform.active
    for p0, n in cuts:
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector(p0), plane_no=Vector(n).normalized(), dist=1e-5)
    kill = []
    for v in bm.verts:
        d = v[dl]
        if d.get(hg, 0) > 0.5 or d.get(jc, 0) > 0.5: kill.append(v); continue
        if not region(v.co, dom_bone(d.items(), idx2name)): kill.append(v)
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    # keep only the biggest connected piece (no stray islands)
    seen = set(); comps = []
    for v in bm.verts:
        if v in seen: continue
        st = [v]; comp = []; seen.add(v)
        while st:
            x = st.pop(); comp.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y not in seen: seen.add(y); st.append(y)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    for c in comps[1:]:
        if len(c) < 0.15 * len(comps[0]):
            bmesh.ops.delete(bm, geom=c, context='VERTS')
    bm.to_mesh(g.data); bm.free()
    for mod in list(g.modifiers):
        if mod.type != 'ARMATURE': g.modifiers.remove(mod)
    g.data.materials.clear(); g.data.materials.append(material)
    for p in g.data.polygons: p.use_smooth = True
    d = g.modifiers.new("offset", 'DISPLACE'); d.strength = offset; d.mid_level = 0.0; d.direction = 'NORMAL'
    if folds > 0:
        tex = bpy.data.textures.new(name + "_folds", 'CLOUDS'); tex.noise_scale = 0.07; tex.noise_depth = 1
        d2 = g.modifiers.new("folds", 'DISPLACE'); d2.texture = tex; d2.strength = folds; d2.mid_level = 0.35; d2.direction = 'NORMAL'
        d2.texture_coords = 'LOCAL'
    sm = g.modifiers.new("smooth", 'CORRECTIVE_SMOOTH'); sm.factor = 0.5; sm.iterations = 3; sm.smooth_type = 'LENGTH_WEIGHTED'
    so = g.modifiers.new("solid", 'SOLIDIFY'); so.thickness = thick; so.offset = -1.0
    sd = g.modifiers.new("subd", 'SUBSURF'); sd.levels = 1; sd.render_levels = 2
    # body vertices under this garment (same tests, applied to the body)
    covered = set()
    for v in body.data.vertices:
        bn = dom_bone(((gg.group, gg.weight) for gg in v.groups), idx2name)
        if region(v.co, bn):
            covered.add(v.index)
    return g, covered

def region_cut_applies(co, bn, p0, n):
    return True

def hide_under(body, covered, name="hide_under", rings=3):
    me = body.data
    nb = {i: set() for i in range(len(me.vertices))}
    for e in me.edges:
        a_, b_ = e.vertices; nb[a_].add(b_); nb[b_].add(a_)
    inner = set(covered)
    for _ in range(rings):
        inner = {i for i in inner if all(n in inner for n in nb[i])}
    vg = body.vertex_groups.get(name) or body.vertex_groups.new(name=name)
    vg.add(list(inner), 1.0, 'REPLACE')
    mk = body.modifiers.new(name, 'MASK'); mk.vertex_group = name; mk.invert_vertex_group = True
    while body.modifiers.find(name) > body.modifiers.find("Armature") + 1:
        i = body.modifiers.find(name); body.modifiers.move(i, i - 1)

def tint(m, mult):
    if not m or not m.use_nodes: return
    for nd in list(m.node_tree.nodes):
        if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
            for lk in list(nd.outputs['Color'].links):
                mx = m.node_tree.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                mx.inputs['Factor'].default_value = 1.0; mx.inputs['B'].default_value = (*mult, 1)
                m.node_tree.links.new(nd.outputs['Color'], mx.inputs['A']); m.node_tree.links.new(mx.outputs['Result'], lk.to_socket)

def eye_fix(rig):
    """black-hole eyes: refractive cornea -> transmission 0 mixed with Transparent (LESSONS 3)"""
    for c in rig.children:
        if c.type != 'MESH': continue
        for m in c.data.materials:
            if not m or not m.use_nodes: continue
            nt = m.node_tree
            for p in [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']:
                tw = p.inputs["Transmission Weight"].default_value
                if tw > 0.05 and not p.inputs["Transmission Weight"].is_linked:
                    p.inputs["Transmission Weight"].default_value = 0.0
                    out_links = list(p.outputs["BSDF"].links)
                    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader")
                    mx.inputs["Fac"].default_value = min(0.9, tw)
                    nt.links.new(p.outputs["BSDF"], mx.inputs[1]); nt.links.new(tr.outputs["BSDF"], mx.inputs[2])
                    for lk in out_links:
                        nt.links.new(mx.outputs["Shader"], lk.to_socket)

PAT, PB = human("Patient", 1.0, 0.5, {"asian": 0.05, "caucasian": 0.85, "african": 0.10}, "short02/short02.mhclo",
                "young_caucasian_male/young_caucasian_male.mhmat", "eyebrow001/eyebrow001.mhclo", height=0.5, weight=0.55)
DOC, DB = human("Surgeon", 1.0, 0.55, {"asian": 0.10, "caucasian": 0.15, "african": 0.75}, "short01/short01.mhclo",
                "middleage_african_male/middleage_african_male.mhmat", "eyebrow004/eyebrow004.mhclo", height=0.55, muscle=0.6)
for r, b in ((PAT, PB), (DOC, DB)):
    bake_keys(b); eye_fix(r)
for c in PAT.children:
    if c.type == 'MESH' and ("short02" in c.name or "eyebrow" in c.name):
        for m in c.data.materials: tint(m, (0.45, 0.30, 0.20))
for m in PB.data.materials: tint(m, (1.0, 0.93, 0.88))

def bl(rig, n): return rig.data.bones[n].head_local.copy()

def wardrobe(rig, body, top_m, bot_m, sleeve, hem_drop, top_off, bot_off, top_folds, bot_folds, prefix):
    hip = bl(rig, "pelvis.L").z; neck = bl(rig, "neck01")
    cuts_top = [((0, 0, hip - hem_drop), (0, 0, -1)), ((0, neck.y, neck.z - 0.03), (0, -0.35, 1))]
    arm_cut = {}
    for s in "LR":
        sh = bl(rig, "upperarm01." + s); el = bl(rig, "lowerarm01." + s); wr = bl(rig, "wrist." + s)
        if sleeve == "short":
            dvec = (el - sh).normalized(); p0 = sh + (el - sh) * 0.62
        else:
            dvec = (wr - el).normalized(); p0 = wr - dvec * 0.015
        arm_cut[s] = (p0, dvec)
        cuts_top.append((p0, dvec))
    def top_region(co, bn):
        if bn is None or in_region(bn, HEADB + ("lowerleg", "foot", "toe") + HANDS): return False
        if plane_side(co, *cuts_top[0]) > 1e-5 or plane_side(co, *cuts_top[1]) > 1e-5: return False
        if in_region(bn, ARM) or in_region(bn, ("shoulder", "clavicle")):
            s = "L" if co.x > 0 else "R"
            if plane_side(co, *arm_cut[s]) > 1e-5: return False
        return True
    top, cov_t = garment(rig, body, prefix + ".top", top_region, cuts_top, top_off, top_m, folds=top_folds)
    ank = {s: bl(rig, "foot." + s).z + 0.075 for s in "LR"}
    cuts_bot = [((0, 0, hip + 0.035), (0, 0, 1)), ((0, 0, ank["L"]), (0, 0, -1))]
    def bot_region(co, bn):
        if bn is None:
            return ank["L"] < co.z < hip + 0.035 and abs(co.x) < 0.12
        if in_region(bn, HEADB + ARM + ("spine03", "spine04", "spine05", "clavicle", "shoulder", "breast", "foot", "toe")): return False
        if plane_side(co, *cuts_bot[0]) > 1e-5 or plane_side(co, *cuts_bot[1]) > 1e-5: return False
        return True
    bot, cov_b = garment(rig, body, prefix + ".trousers", bot_region, cuts_bot, bot_off, bot_m, folds=bot_folds)
    hide_under(body, cov_t | cov_b)
    return top, bot

tee_m = fabric("M_PatientTee", (0.16, 0.30, 0.55))
trs_m = fabric("M_PatientTrousers", (0.09, 0.10, 0.13), scale=600)
wardrobe(PAT, PB, tee_m, trs_m, "short", 0.06, 0.010, 0.008, 0.005, 0.004, "Patient")
scr_top = fabric("M_ScrubTop", (0.16, 0.42, 0.55))
scr_bot = fabric("M_ScrubTrousers", (0.07, 0.17, 0.30), scale=700)
wardrobe(DOC, DB, scr_top, scr_bot, "long", 0.13, 0.020, 0.016, 0.012, 0.009, "Surgeon")

# gloves: the surgeon's hand skin becomes nitrile (real MPFB hands with posed fingers, no sausage gloves)
glove = mat("M_Glove", (0.30, 0.36, 0.78), rough=0.38, coat=0.25)
idx2 = {vg.index: vg.name for vg in DB.vertex_groups if vg.name in bone_names(DOC)}
DB.data.materials.append(glove); gi = len(DB.data.materials) - 1
wr_z = {s: bl(DOC, "wrist." + s) for s in "LR"}
for p in DB.data.polygons:
    bns = [dom_bone(((g.group, g.weight) for g in DB.data.vertices[v].groups), idx2) for v in p.vertices]
    if all(in_region(b, HANDS + ("lowerarm02",)) for b in bns):
        c = p.center; s = "L" if c.x > 0 else "R"
        el = bl(DOC, "lowerarm01." + s); wr = wr_z[s]; dvec = (wr - el).normalized()
        if (c - wr).dot(dvec) > -0.06: p.material_index = gi

# mask + bouffant cap (bound to the head bone only, LESSONS 2.5)
eye_z = bl(DOC, "eye.L").z
nose = max(DB.data.vertices, key=lambda v: -v.co.y if abs(v.co.x) < 0.006 and eye_z - 0.07 < v.co.z < eye_z else -9).co.copy()
mask_m = fabric("M_Mask", (0.55, 0.78, 0.92), scale=500, bump=0.4)
def mask_region(co, bn):
    return in_region(bn, ("head", "jaw", "oris", "levator", "risor", "neck03")) and abs(co.x) <= 0.07201 and co.y <= nose.y + 0.07501 and nose.z - 0.10001 <= co.z <= eye_z - 0.02199
mask_cuts = [((0, 0, nose.z - 0.10), (0, 0, -1)), ((0, 0, eye_z - 0.022), (0, 0, 1)), ((0.072, 0, 0), (1, 0, 0)), ((-0.072, 0, 0), (-1, 0, 0)), ((0, nose.y + 0.075, 0), (0, 1, 0))]
MASK, _ = garment(DOC, DB, "Surgeon.mask", mask_region, mask_cuts, 0.005, mask_m, thick=0.002, folds=0.0)
cap_m = fabric("M_Cap", (0.22, 0.50, 0.66), scale=400, bump=0.5)
cap_p0 = (0, -0.10, eye_z + 0.034); cap_n = Vector((0, 0.095, 0.2)).normalized()
def cap_region(co, bn):
    return in_region(bn, ("head", "neck03", "temporal")) and plane_side(co, cap_p0, cap_n) >= -1e-5
CAP, _ = garment(DOC, DB, "Surgeon.cap", cap_region, [(cap_p0, -cap_n)], 0.026, cap_m, thick=0.002, folds=0.016)
for g in (CAP, MASK):
    for vg in list(g.vertex_groups): g.vertex_groups.remove(vg)
    vh = g.vertex_groups.new(name="head"); vh.add(list(range(len(g.data.vertices))), 1.0, 'REPLACE')
bm = bmesh.new(); bm.from_mesh(CAP.data); bm.verts.ensure_lookup_table()
bnd = {v.index for v in bm.verts if v.is_boundary}
ring = set(bnd)
for v in bm.verts:
    if v.index in bnd:
        for e in v.link_edges: ring.add(e.other_vert(v).index)
bm.free()
vb = CAP.vertex_groups.new(name="band"); vb.add(list(ring), 1.0, 'REPLACE')
bd = CAP.modifiers.new("band", 'DISPLACE'); bd.strength = -0.020; bd.mid_level = 0.0; bd.direction = 'NORMAL'; bd.vertex_group = "band"
CAP.modifiers.move(CAP.modifiers.find("band"), CAP.modifiers.find("smooth"))
CAP.modifiers["folds"].vertex_group = "band"; CAP.modifiers["folds"].invert_vertex_group = True
for c in DOC.children:
    if c.type == 'MESH' and "short01" in c.name:
        c.hide_render = True; c.hide_viewport = True   # hair fully under the cap

# patient: healed earless site on the RIGHT (-X) side (story: the lost ear). Flatten the right ear onto the scalp.
eg = PB.vertex_groups.get("ears")
earR = [v for v in PB.data.vertices if any(g.group == eg.index and g.weight > 0.5 for g in v.groups) and v.co.x < 0]
cx = sum(v.co.x for v in earR) / len(earR); cy = sum(v.co.y for v in earR) / len(earR); cz = sum(v.co.z for v in earR) / len(earR)
ring_x = max(v.co.x for v in earR)
for v in earR:
    v.co.x = ring_x - 0.002 + (v.co.x - ring_x) * 0.03
    v.co.y = cy + (v.co.y - cy) * 0.45; v.co.z = cz + (v.co.z - cz) * 0.45
EAR_SITE_REST = Vector((ring_x, cy, cz))
attr = PB.data.color_attributes.new("scar", 'FLOAT_COLOR', 'POINT')
for v in PB.data.vertices:
    d = Vector((0, v.co.y - cy, (v.co.z - cz) * 0.8)).length
    t = max(0.0, 1.0 - d / 0.026) if v.co.x < -0.055 and abs(v.co.x - ring_x) < 0.03 else 0.0
    attr.data[v.index].color = (t, t, t, 1)
for m in PB.data.materials:
    if not m or not m.use_nodes: continue
    nt = m.node_tree; ps = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']
    if not ps or not ps[0].inputs["Base Color"].is_linked: continue
    p = ps[0]; src = p.inputs["Base Color"].links[0].from_socket
    ca = nt.nodes.new("ShaderNodeVertexColor"); ca.layer_name = "scar"
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MIX'
    mr = nt.nodes.new("ShaderNodeMath"); mr.operation = 'MULTIPLY'; mr.inputs[1].default_value = 0.6
    nt.links.new(ca.outputs["Color"], mr.inputs[0]); nt.links.new(mr.outputs[0], mx.inputs["Factor"])
    nt.links.new(src, mx.inputs["A"]); mx.inputs["B"].default_value = (0.80, 0.45, 0.42, 1)
    nt.links.new(mx.outputs["Result"], p.inputs["Base Color"])
for c in PAT.children:
    if c.type == 'MESH' and "short02" in c.name:
        hm = c.data; bmh = bmesh.new(); bmh.from_mesh(hm)
        kill = [v for v in bmh.verts if v.co.x < -0.05 and abs(v.co.z - cz) < 0.04 and abs(v.co.y - cy) < 0.045]
        bmesh.ops.delete(bmh, geom=kill, context='VERTS'); bmh.to_mesh(hm); bmh.free()
nose_tip = nose

# ------------------------------------------------------------------ the room
def box(name, size, loc, material, bevel=0.01, segs=3, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = segs; b.limit_method = 'ANGLE'
    o.data.materials.append(material)
    for p in o.data.polygons: p.use_smooth = True
    o.data.shade_auto_smooth if False else None
    return o

def cyl(name, r, h, loc, material, rot=(0, 0, 0), verts=32, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.active_object; o.name = name; o.data.materials.append(material)
    if bevel:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = 3; b.limit_method = 'ANGLE'
    bpy.ops.object.shade_smooth()
    return o

floor_m = mat("M_Floor", (0.40, 0.46, 0.47), rough=0.45, coat=0.2)
nt = floor_m.node_tree; p = nt.nodes["Principled BSDF"]
br = nt.nodes.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 1.6
br.inputs["Color1"].default_value = (0.42, 0.48, 0.49, 1); br.inputs["Color2"].default_value = (0.37, 0.43, 0.44, 1)
br.inputs["Mortar"].default_value = (0.42, 0.47, 0.47, 1); br.inputs["Mortar Size"].default_value = 0.004; br.offset = 0.0
br.inputs["Brick Width"].default_value = 0.5; br.inputs["Row Height"].default_value = 0.5
nt.links.new(br.outputs["Color"], p.inputs["Base Color"])
wall_m = mat("M_Wall", (0.74, 0.68, 0.58), rough=0.7)
wall2_m = mat("M_WallLow", (0.16, 0.42, 0.46), rough=0.55)
rail_m = mat("M_Rail", (0.92, 0.92, 0.90), rough=0.35)
steel = mat("M_Steel", (0.80, 0.82, 0.84), rough=0.22, metal=1.0)
vinyl = mat("M_Vinyl", (0.10, 0.36, 0.44), rough=0.42, coat=0.3)
frame_m = mat("M_Frame", (0.95, 0.95, 0.95), rough=0.4)
lamp_m = mat("M_Lamp", (0.95, 0.96, 0.98), rough=0.3)
emit_m = mat("M_LampGlow", (1, 1, 1), emit=((1.0, 0.97, 0.92), 6.0))

box("Floor", (8, 8, 0.02), (0, 0, -0.01), floor_m, bevel=0)
box("WallBack", (8, 0.1, 3.0), (0, 2.1, 1.5), wall_m, bevel=0)
box("WallLeft", (0.1, 8, 3.0), (-2.5, 0, 1.5), wall_m, bevel=0)
box("WallRight", (0.1, 8, 3.0), (2.4, 0, 1.5), wall_m, bevel=0)
box("DadoBack", (8, 0.02, 0.95), (0, 2.045, 0.475), wall2_m, bevel=0)
box("DadoLeft", (0.02, 8, 0.95), (-2.445, 0, 0.475), wall2_m, bevel=0)
box("RailBack", (8, 0.05, 0.06), (0, 2.03, 0.96), rail_m, bevel=0.008)
box("RailLeft", (0.05, 8, 0.06), (-2.43, 0, 0.96), rail_m, bevel=0.008)
box("Ceiling", (8, 8, 0.05), (0, 0, 3.0), wall_m, bevel=0)
# window on the left wall: bright sky gradient behind a white frame (STYLE: sky-blue)
sky_m = mat("M_WindowSky", (0.5, 0.8, 1.0), emit=((0.55, 0.82, 1.0), 2.2))
nt = sky_m.node_tree; p = nt.nodes["Principled BSDF"]
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); ramp = nt.nodes.new("ShaderNodeValToRGB")
nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
ramp.color_ramp.elements[0].color = (0.91, 0.97, 1.0, 1); ramp.color_ramp.elements[1].color = (0.31, 0.76, 0.97, 1)
nt.links.new(ramp.outputs["Color"], p.inputs["Emission Color"]); nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
box("WindowSky", (0.02, 1.4, 1.1), (-2.44, -0.6, 1.75), sky_m, bevel=0)
for (sy, sz, ly, lz) in ((0.06, 1.22, -1.33, 1.75), (0.06, 1.22, 0.13, 1.75), (1.52, 0.06, -0.6, 2.33), (1.52, 0.08, -0.6, 1.17), (0.04, 1.1, -0.6, 1.75)):
    box("WinFrame", (0.06, sy, sz), (-2.42, ly, lz), frame_m, bevel=0.006)
# framed abstract posters (no text)
for i, (x, col) in enumerate(((-0.9, (0.95, 0.62, 0.30)), (0.9, (0.36, 0.70, 0.55)))):
    box("PosterFrame", (0.62, 0.03, 0.82), (x, 2.035, 1.75), frame_m, bevel=0.006)
    pm = mat("M_Poster%d" % i, col, rough=0.6)
    nt = pm.node_tree; pp = nt.nodes["Principled BSDF"]; wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 1.2
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*col, 1); cr.color_ramp.elements[1].color = (0.97, 0.95, 0.90, 1)
    nt.links.new(wv.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], pp.inputs["Base Color"])
    box("Poster", (0.54, 0.01, 0.74), (x, 2.018, 1.75), pm, bevel=0)

# procedure chair: chrome base, vinyl seat/back/armrest; patient's right arm board
CH = {}
CH["seat"] = box("ChairSeat", (0.56, 0.52, 0.10), (0, 0.02, 0.47), vinyl, bevel=0.035, segs=4)
CH["back"] = box("ChairBack", (0.54, 0.10, 0.78), (0, 0.30, 0.92), vinyl, bevel=0.04, segs=4, rot=(R_(-12), 0, 0))
CH["armL"] = box("ChairArmL", (0.10, 0.46, 0.06), (0.33, 0.04, 0.66), vinyl, bevel=0.025, segs=4)
for x in (0.33,):
    cyl("ChairArmPost", 0.018, 0.18, (x, 0.10, 0.56), steel)
cyl("ChairColumn", 0.05, 0.36, (0, 0.04, 0.24), steel)
cyl("ChairBase", 0.30, 0.04, (0, 0.04, 0.03), steel, bevel=0.01)
# arm board (pose-fitted in stage B: it is moved under the forearm there)
CH["board"] = box("ArmBoard", (0.56, 0.14, 0.045), (-0.48, -0.06, 0.66), vinyl, bevel=0.02, segs=4)
cyl("ArmBoardPost", 0.02, 0.60, (-0.62, -0.06, 0.33), steel)
cyl("ArmBoardFoot", 0.16, 0.03, (-0.62, -0.06, 0.015), steel, bevel=0.008)
# instrument trolley (Mayo-style) at the surgeon's front-right
box("TrolleyTop", (0.44, 0.36, 0.025), (-1.02, -0.04, 0.86), steel, bevel=0.008)
box("TrolleyShelf", (0.40, 0.32, 0.02), (-1.02, -0.04, 0.30), steel, bevel=0.006)
for dx in (-0.19, 0.19):
    for dy in (-0.15, 0.15):
        cyl("TrolleyLeg", 0.012, 0.82, (-1.02 + dx, -0.04 + dy, 0.44), steel)
        cyl("TrolleyWheel", 0.03, 0.02, (-1.02 + dx, -0.04 + dy, 0.03), mat("M_Rubber", (0.08, 0.08, 0.09), rough=0.6), rot=(0, R_(90), 0))
drape = fabric("M_Drape", (0.20, 0.55, 0.58), scale=500)
box("TrolleyDrape", (0.42, 0.34, 0.004), (-1.02, -0.04, 0.875), drape, bevel=0.002)
# overhead surgical lamp (out of most frames, gives a motivated top light)
cyl("LampArm", 0.025, 1.1, (-0.6, 0.6, 2.45), lamp_m, rot=(R_(90), 0, R_(30)))
cyl("LampHead", 0.26, 0.10, (-0.35, 0.10, 2.25), lamp_m, bevel=0.02)
cyl("LampGlow", 0.22, 0.01, (-0.35, 0.10, 2.195), emit_m)
# wall cabinet + side cabinet
box("SideCounter", (1.3, 0.55, 0.9), (1.4, 1.75, 0.45), mat("M_Counter", (0.93, 0.93, 0.92), rough=0.35), bevel=0.01)
box("CounterTop", (1.34, 0.6, 0.04), (1.4, 1.74, 0.92), mat("M_CounterTop", (0.30, 0.34, 0.38), rough=0.3), bevel=0.006)

# ------------------------------------------------------------------ imported props
def imp(path, keep=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH' and (keep is None or keep(o))]
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o not in meshes: bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    for o in meshes: o.select_set(True)
    if len(meshes) > 1: bpy.ops.object.join()
    o = bpy.context.active_object
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return o

def recenter(o, origin):
    """set origin to `origin` (object-local) without moving the mesh"""
    o.data.transform(Matrix.Translation(-Vector(origin))); o.location = o.location + Vector(origin)

# cabinet
cab = imp(DL + "/cabinet/scene.gltf"); cab.name = "Cabinet"
cab.location = (-1.7, 1.78, 0.0)
# tray
tray = imp(DL + "/tray/scene.gltf"); tray.name = "Tray"
bb = [Vector(c) for c in tray.bound_box]; mn = Vector([min(v[i] for v in bb) for i in range(3)]); mx_ = Vector([max(v[i] for v in bb) for i in range(3)])
recenter(tray, ((mn.x + mx_.x) / 2, (mn.y + mx_.y) / 2, mn.z))
tray.location = (-1.02, -0.04, 0.877); tray.rotation_euler = (0, 0, R_(90))

def axis_prop(path, name, length, keep=None):
    o = imp(path, keep); o.name = name
    bb = [Vector(c) for c in o.bound_box]; mn = Vector([min(v[i] for v in bb) for i in range(3)]); mx_ = Vector([max(v[i] for v in bb) for i in range(3)])
    dims = mx_ - mn; ax = max(range(3), key=lambda i: dims[i])
    s = length / dims[ax]
    o.data.transform(Matrix.Translation(-(mn + mx_) / 2)); o.data.transform(Matrix.Scale(s, 4))
    # rotate so the long axis is local +Y
    if ax == 0: o.data.transform(Matrix.Rotation(R_(90), 4, 'Z'))
    if ax == 2: o.data.transform(Matrix.Rotation(R_(-90), 4, 'X'))
    o.location = (0, 0, 0)
    return o

def scalpel():
    """steel handle (ridged grip) + curved blade; long axis +Y, blade tip at +Y"""
    hm = mat("M_ScalpelHandle", (0.78, 0.80, 0.83), rough=0.3, metal=1.0)
    bmat = mat("M_Blade", (0.88, 0.90, 0.92), rough=0.12, metal=1.0)
    bpy.ops.mesh.primitive_cube_add(size=1); h = bpy.context.active_object; h.name = "Scalpel"
    h.scale = (0.009, 0.115, 0.0028); bpy.ops.object.transform_apply(scale=True)
    for v in h.data.vertices:
        if v.co.y < 0: v.co.x *= 0.8
    b = h.modifiers.new("bev", 'BEVEL'); b.width = 0.0012; b.segments = 3
    h.data.materials.append(hm)
    # blade: a flat, curved-edge profile
    import bmesh as _bm
    bm = _bm.new()
    prof = [(-0.0035, 0.0), (0.0035, 0.0), (0.0042, 0.012), (0.0030, 0.026), (0.0, 0.036), (-0.0030, 0.018)]
    vs = [bm.verts.new((x, y + 0.0575, 0.0)) for x, y in prof]
    f = bm.faces.new(vs); _bm.ops.solidify(bm, geom=[f], thickness=0.0005)
    me = bpy.data.meshes.new("Blade"); bm.to_mesh(me); bm.free()
    bo = bpy.data.objects.new("Blade", me); bpy.context.collection.objects.link(bo); me.materials.append(bmat)
    bpy.ops.object.select_all(action='DESELECT'); h.select_set(True); bo.select_set(True); bpy.context.view_layer.objects.active = h
    bpy.ops.object.modifier_apply(modifier="bev"); bpy.ops.object.join()
    h.data.transform(Matrix.Translation((0, -0.025, 0)))
    for p in h.data.polygons: p.use_smooth = False
    return h

FORC = axis_prop(DL + "/forceps/scene.gltf", "Forceps", 0.14)
NEED = axis_prop(DL + "/needleholder/scene.gltf", "NeedleHolder", 0.15)
for o in (FORC, NEED):
    for m in o.data.materials:
        if m and m.use_nodes:
            p = m.node_tree.nodes.get("Principled BSDF")
            if p:
                p.inputs["Metallic"].default_value = 1.0; p.inputs["Roughness"].default_value = 0.25
                if p.inputs["Base Color"].is_linked: pass
                else: p.inputs["Base Color"].default_value = (0.82, 0.84, 0.86, 1)
# tip ends: which end of local Y is narrower -> that is the tip (+Y after flip)
def orient_tip(o):
    vs = [v.co for v in o.data.vertices]
    ys = [v.y for v in vs]; y0, y1 = min(ys), max(ys); L = y1 - y0
    def width(lo, hi):
        sel = [v for v in vs if lo <= v.y <= hi]
        return (max(v.x for v in sel) - min(v.x for v in sel)) + (max(v.z for v in sel) - min(v.z for v in sel)) if sel else 0
    w_lo, w_hi = width(y0, y0 + 0.12 * L), width(y1 - 0.12 * L, y1)
    if w_hi > w_lo: o.data.transform(Matrix.Rotation(R_(180), 4, 'Z'))
    return w_lo, w_hi
SCAL = scalpel()
for o in (FORC, NEED):
    print("TIP", o.name, orient_tip(o), tuple(round(d, 3) for d in o.dimensions))
# needle + thread on the needle holder tip (small curved needle)
bpy.ops.curve.primitive_bezier_circle_add(radius=0.006)
ndl = bpy.context.active_object; ndl.name = "Needle"; ndl.data.bevel_depth = 0.0006; ndl.data.materials.append(steel)
bpy.ops.object.convert(target='MESH'); ndl = bpy.context.active_object
bm = bmesh.new(); bm.from_mesh(ndl.data); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -0.001], context='VERTS'); bm.to_mesh(ndl.data); bm.free()
ndl.location = (0, 0.075 + 0.004, 0); ndl.rotation_euler = (0, R_(90), 0); ndl.parent = NEED

# rib cage (x-ray anatomy) - placed inside the patient's chest in stage B
TH = imp(DL + "/thorax/scene.gltf"); TH.name = "RibCage"
bone_m = mat("M_Bone", (0.93, 0.88, 0.76), rough=0.4, coat=0.2)
cart_m = mat("M_RibCartilage", (0.86, 0.87, 0.84), rough=0.3, coat=0.3)
old_names = [sl.material.name if sl.material else "" for sl in TH.material_slots]
pidx = [p_.material_index for p_ in TH.data.polygons]
TH.data.materials.clear(); TH.data.materials.append(bone_m); TH.data.materials.append(cart_m)
for p_, mi in zip(TH.data.polygons, pidx):
    p_.material_index = 1 if old_names[mi].startswith("initialShading") else 0
for sl in TH.material_slots: sl.link = 'DATA'
TH.data.color_attributes and [TH.data.color_attributes.remove(a_) for a_ in list(TH.data.color_attributes)]
TH.data.transform(Matrix.Rotation(R_(-90), 4, 'Z'))
bpy.context.view_layer.objects.active = TH
try: bpy.ops.mesh.customdata_custom_splitnormals_clear()
except Exception as e_: print("splitnormals", e_)
bmt = bmesh.new(); bmt.from_mesh(TH.data); bmesh.ops.recalc_face_normals(bmt, faces=bmt.faces[:]); bmt.to_mesh(TH.data); bmt.free()
for p_ in TH.data.polygons: p_.use_smooth = True
bb = [Vector(c) for c in TH.bound_box]; mn = Vector([min(v[i] for v in bb) for i in range(3)]); mx_ = Vector([max(v[i] for v in bb) for i in range(3)])
TH.data.transform(Matrix.Translation(-Vector(((mn.x + mx_.x) / 2, (mn.y + mx_.y) / 2, mx_.z))))
TH.data.transform(Matrix.Scale(0.225 / (mx_.x - mn.x), 4))
TH.location = (0, 0, 0)

# the ear (one model for the whole story: rib cartilage block -> carved ear -> grows in the arm -> grafted)
EAR = imp(DL + "/ear/scene.gltf"); EAR.name = "Ear"
bb = [Vector(c) for c in EAR.bound_box]; mn = Vector([min(v[i] for v in bb) for i in range(3)]); mx_ = Vector([max(v[i] for v in bb) for i in range(3)])
EAR.data.transform(Matrix.Translation(-(mn + mx_) / 2)); EAR.data.transform(Matrix.Scale(0.062 / (mx_ - mn).z, 4))
EAR.location = (0, 0, 0)
ear_m = mat("M_Ear", (0.86, 0.87, 0.84), rough=0.35, coat=0.2)
EAR.data.materials.clear(); EAR.data.materials.append(ear_m)
for p in EAR.data.polygons: p.use_smooth = True
print("EARDIMS", tuple(round(d, 4) for d in EAR.dimensions))

# ------------------------------------------------------------------ look (STYLE_ANIMATED): AgX Punchy, bright, clean
sc.view_settings.view_transform = 'AgX'
sc.view_settings.exposure = -0.3
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: pass
sc.render.engine = 'CYCLES'
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 8; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3; sc.cycles.transmission_bounces = 8
sc.cycles.transparent_max_bounces = 16; sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
sc.render.use_motion_blur = False
w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.75, 0.80, 0.85, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.15

def area(name, loc, rot, power, size, col):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = power; ld.size = size; ld.color = col; ld.shape = 'DISK'
    o = bpy.data.objects.new(name, ld); bpy.context.collection.objects.link(o); o.location = loc
    o.rotation_euler = rot
    return o
def aim(o, target):
    d = Vector(target) - o.location; o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
k = area("Key", (-1.6, -2.0, 2.6), (0, 0, 0), 260, 1.6, (1.0, 0.93, 0.85)); aim(k, (-0.3, 0.0, 1.1))
f = area("Fill", (1.8, -1.6, 1.7), (0, 0, 0), 70, 2.2, (0.85, 0.92, 1.0)); aim(f, (-0.2, 0.0, 1.0))
r = area("Rim", (0.6, 1.6, 2.4), (0, 0, 0), 160, 1.2, (1.0, 0.96, 0.92)); aim(r, (-0.3, 0.0, 1.2))
t = area("Top", (-0.35, 0.10, 2.15), (0, 0, 0), 60, 0.5, (1.0, 0.98, 0.95)); aim(t, (-0.35, 0.10, 0.0))
sc["ear_site_rest"] = list(EAR_SITE_REST)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("BUILD_OK", OUT)
for n in ("head", "neck01", "upperarm01.R", "lowerarm01.R", "wrist.R", "upperleg01.L", "lowerleg01.L", "foot.L", "root", "spine03"):
    print("BONE", n, tuple(round(x, 3) for x in PAT.data.bones[n].head_local), tuple(round(x, 3) for x in DOC.data.bones[n].head_local))
print("EARSITE", tuple(round(x, 3) for x in EAR_SITE_REST), "nose", tuple(round(x, 3) for x in nose_tip))
