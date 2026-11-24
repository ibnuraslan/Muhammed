"""LegoInNose v013 stage A: three sets, three characters (one model each), props, look. Built from scratch.
blender -b --python 01_build.py -- <dl_dir> <out.blend>
Sets are separate islands (the camera moves between them only inside the x-ray void):
  LIVING ROOM at the origin: the boy sits ON the rug facing -Y; Mom sits ON the sofa at his right (-X), facing +X.
  BEDROOM at x=+8: the man lies propped up ON the mattress, head at the headboard (+Y), facing -Y.
  BATHROOM at x=+16: the man stands IN the tub, facing -Y, behind an opaque curtain (framed shoulders-up)."""
import bpy, bmesh, sys, math, random, json
from mathutils import Vector, Matrix
from bl_ext.user_default.mpfb.services.humanservice import HumanService

a = sys.argv[sys.argv.index("--") + 1:]
DL, OUT = a[0], a[1]
R_ = math.radians
random.seed(3)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
sc = bpy.context.scene
sc.render.fps = 60
sc.frame_start, sc.frame_end = 1, 2036
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
BED_X, BATH_X = 8.0, 16.0

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
    if coat: p.inputs["Coat Weight"].default_value = coat
    if sheen: p.inputs["Sheen Weight"].default_value = sheen
    if emit:
        p.inputs["Emission Color"].default_value = (*emit[0], 1)
        p.inputs["Emission Strength"].default_value = emit[1]
    return m

def fabric(name, col, scale=900.0, bump=0.25):
    m = mat(name, col, rough=0.8, sheen=0.15)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave")
    wv.inputs["Scale"].default_value = scale; wv.inputs["Distortion"].default_value = 2.0
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.0005
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"]); nt.links.new(wv.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m

def stripes(name, c1, c2, scale=40.0):
    m = fabric(name, c1, scale=700)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'
    wv.inputs["Scale"].default_value = scale; wv.bands_direction = 'Z'
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = 'CONSTANT'
    cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].position = 0.55; cr.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"]); nt.links.new(wv.outputs["Fac"], cr.inputs["Fac"])
    nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
    return m

# ------------------------------------------------------------------ characters
_EYE = json.load(open("/root/.config/blender/5.2/extensions/user_default/mpfb/data/settings/eye_settings.default.json"))
def human(name, gender, age, race, hair, skin, eyebrow, height=0.5, muscle=0.5, weight=0.5, prop=0.6):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": gender, "age": age, "muscle": muscle, "weight": weight, "proportions": prop,
                         "height": height, "cupsize": 0.5, "firmness": 0.5, "race": race}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = eyebrow
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair
    info["clothes"] = []
    es = dict(_EYE); es["IrisMajorColor"] = [0.30, 0.17, 0.07, 1.0]; es["IrisMinorColor"] = [0.12, 0.07, 0.03, 1.0]
    info["eyes_material_settings"] = es
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = 1
    HumanService.deserialize_from_dict(info, st)
    rig = bpy.data.objects[name]
    body = [c for c in rig.children if c.type == 'MESH' and c.name.endswith(".body")][0]
    return rig, body

def bake_keys(body):
    bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); bpy.context.view_layer.objects.active = body
    if body.data.shape_keys:
        bpy.ops.object.shape_key_remove(all=True, apply_mix=True)

def bone_names(rig): return {b.name for b in rig.data.bones}
def dom_bone(vgroups_iter, idx2name):
    best = (0.0, None)
    for gi, w in vgroups_iter:
        n = idx2name.get(gi)
        if n and w > best[0]: best = (w, n)
    return best[1]
def in_region(bn, prefixes): return bn is not None and any(bn.startswith(p) for p in prefixes)
ARM = ("upperarm", "lowerarm", "wrist", "finger", "metacarpal")
HANDS = ("wrist", "finger", "metacarpal")
HEADB = ("head", "jaw", "neck", "eye", "orbic", "oris", "levator", "risor", "temporal", "tongue")
def plane_side(co, p0, n): return (Vector(co) - Vector(p0)).dot(Vector(n))

def garment(rig, body, name, region, cuts, offset, material, thick=0.003, folds=0.0):
    """R1: one joined garment = duplicate of the body, bisected along clean cut planes, region-filtered,
    pushed out along the normals after the Armature, solidified, smoothed, subdivided."""
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
    if g.data.shape_keys: g.shape_key_clear()
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
    covered = set()
    for v in body.data.vertices:
        bn = dom_bone(((gg.group, gg.weight) for gg in v.groups), idx2name)
        if region(v.co, bn): covered.add(v.index)
    return g, covered

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
    return mk

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
                    for lk in out_links: nt.links.new(mx.outputs["Shader"], lk.to_socket)

RACE = {"asian": 0.05, "caucasian": 0.85, "african": 0.10}
BOY, BB = human("Boy", 1.0, 0.115, RACE, "short02/short02.mhclo", "young_caucasian_male/young_caucasian_male.mhmat",
                "eyebrow001/eyebrow001.mhclo", height=0.6, weight=0.45)
MOM, MB = human("Mom", 0.0, 0.56, {"asian": 0.1, "caucasian": 0.8, "african": 0.1}, "ponytail01/ponytail01.mhclo",
                "young_caucasian_female/young_caucasian_female.mhmat", "eyebrow010/eyebrow010.mhclo", height=0.5, weight=0.45)
MAN, NB = human("Man", 1.0, 0.56, RACE, "short02/short02.mhclo", "young_caucasian_male2/young_caucasian_male2.mhmat",
                "eyebrow001/eyebrow001.mhclo", height=0.55, weight=0.5)
for r, b in ((BOY, BB), (MOM, MB), (MAN, NB)):
    bake_keys(b); eye_fix(r)
# the MPFB EnhancedEye group: refractive cornea -> transmission 0 + Transparent mix (LESSONS 3, black-hole eyes)
g = bpy.data.node_groups.get("EnhancedEye")
if g:
    p = g.nodes["Principled BSDF"]; ti = p.inputs["Transmission Weight"]
    if ti.is_linked:
        src = ti.links[0].from_socket; g.links.remove(ti.links[0]); ti.default_value = 0.0
        outs = list(p.outputs["BSDF"].links)
        tr = g.nodes.new("ShaderNodeBsdfTransparent"); mx = g.nodes.new("ShaderNodeMixShader")
        mm = g.nodes.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = 0.92
        g.links.new(src, mm.inputs[0]); g.links.new(mm.outputs[0], mx.inputs["Fac"])
        g.links.new(p.outputs["BSDF"], mx.inputs[1]); g.links.new(tr.outputs["BSDF"], mx.inputs[2])
        for lk in outs: g.links.new(mx.outputs["Shader"], lk.to_socket)
        print("EYEFIX group done")
for rig, col in ((BOY, (0.42, 0.28, 0.17)), (MAN, (0.42, 0.28, 0.17)), (MOM, (0.30, 0.18, 0.11))):
    for c in rig.children:
        if c.type == 'MESH' and any(k in c.name.lower() for k in ("short", "bob", "pony", "eyebrow")):
            for m in c.data.materials: tint(m, col)
for b in (BB, MB, NB):
    for m in b.data.materials: tint(m, (1.0, 0.86, 0.76))

def bl(rig, n): return rig.data.bones[n].head_local.copy()

def wardrobe(rig, body, top_m, bot_m, hem_drop, top_off, bot_off, top_folds, bot_folds, prefix, collar=0.03):
    hip = bl(rig, "pelvis.L").z; neck = bl(rig, "neck01")
    cuts_top = [((0, 0, hip - hem_drop), (0, 0, -1)), ((0, neck.y, neck.z - collar), (0, -0.35, 1))]
    arm_cut = {}
    for s in "LR":
        el = bl(rig, "lowerarm01." + s); wr = bl(rig, "wrist." + s)
        dvec = (wr - el).normalized(); p0 = wr - dvec * 0.015
        arm_cut[s] = (p0, dvec); cuts_top.append((p0, dvec))
    def top_region(co, bn):
        if bn is None or in_region(bn, HEADB + ("lowerleg", "foot", "toe") + HANDS): return False
        if plane_side(co, *cuts_top[0]) > 1e-5 or plane_side(co, *cuts_top[1]) > 1e-5: return False
        if in_region(bn, ARM) or in_region(bn, ("shoulder", "clavicle")):
            s = "L" if co.x > 0 else "R"
            if plane_side(co, *arm_cut[s]) > 1e-5: return False
        return True
    top, cov_t = garment(rig, body, prefix + ".top", top_region, cuts_top, top_off, top_m, folds=top_folds)
    ank = {s: bl(rig, "foot." + s).z + 0.06 for s in "LR"}
    cuts_bot = [((0, 0, hip + 0.07), (0, 0, 1)), ((0, 0, ank["L"]), (0, 0, -1))]
    def bot_region(co, bn):
        if bn is None: return ank["L"] < co.z < hip + 0.07 and abs(co.x) < 0.12
        if in_region(bn, HEADB + ARM + ("spine03", "spine04", "spine05", "clavicle", "shoulder", "breast", "foot", "toe")): return False
        if plane_side(co, *cuts_bot[0]) > 1e-5 or plane_side(co, *cuts_bot[1]) > 1e-5: return False
        return True
    bot, cov_b = garment(rig, body, prefix + ".trousers", bot_region, cuts_bot, bot_off, bot_m, folds=bot_folds)
    mk = hide_under(body, cov_t | cov_b)
    return top, bot, mk

boy_tee = stripes("M_BoyTop", (0.10, 0.36, 0.62), (0.92, 0.92, 0.88), scale=30.0)
boy_trs = fabric("M_BoyTrousers", (0.16, 0.22, 0.30), scale=600)
wardrobe(BOY, BB, boy_tee, boy_trs, -0.025, 0.010, 0.006, 0.004, 0.003, "Boy")
mom_top = fabric("M_MomTop", (0.20, 0.50, 0.42))
mom_trs = fabric("M_MomTrousers", (0.10, 0.12, 0.20), scale=600)
wardrobe(MOM, MB, mom_top, mom_trs, 0.0, 0.012, 0.007, 0.005, 0.004, "Mom")
pj_top = fabric("M_PJTop", (0.36, 0.48, 0.70))
pj_bot = fabric("M_PJTrousers", (0.20, 0.25, 0.42), scale=600)
sock_m = fabric("M_Socks", (0.85, 0.85, 0.82), scale=500)
for rig, body, col in ((BOY, BB, (0.90, 0.88, 0.80)), (MOM, MB, (0.25, 0.25, 0.30))):
    sm_ = fabric("M_Socks" + rig.name, col, scale=500)
    ank = bl(rig, "foot.L").z + 0.07
    def sock_region(co, bn, ank=ank):
        return in_region(bn, ("foot", "toe", "lowerleg")) and co.z <= ank
    for s_ in "LR":
        pass
    sk, cov = garment(rig, body, rig.name + ".socks", sock_region, [((0, 0, ank), (0, 0, 1))], 0.003, sm_, thick=0.002)
    hide_under(body, cov, name="hide_socks", rings=2)
MT, MBT, MMASK = wardrobe(MAN, NB, pj_top, pj_bot, 0.0, 0.012, 0.008, 0.005, 0.004, "Man")

# ------------------------------------------------------------------ set helpers
def box(name, size, loc, material, bevel=0.01, segs=3, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = segs; b.limit_method = 'ANGLE'
    o.data.materials.append(material)
    for p in o.data.polygons: p.use_smooth = True
    return o

def cyl(name, r, h, loc, material, rot=(0, 0, 0), verts=32, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.active_object; o.name = name; o.data.materials.append(material)
    if bevel:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = 3; b.limit_method = 'ANGLE'
    bpy.ops.object.shade_smooth()
    return o

def imp(path, name, target_dim=None, axis=None, keep=None):
    """import a glb, join meshes, origin at the bottom centre, uniform scale so its `axis` extent = target_dim"""
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
    if len(meshes) > 1: bpy.ops.object.join()
    o = bpy.context.active_object; o.name = name
    if o.data.shape_keys: o.shape_key_clear()
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bb = [v.co.copy() for v in o.data.vertices]; mn = Vector([min(v[i] for v in bb) for i in range(3)]); mx = Vector([max(v[i] for v in bb) for i in range(3)])
    o.data.transform(Matrix.Translation(-Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))))
    if target_dim:
        d = (mx - mn); s = target_dim / (d[axis] if axis is not None else max(d))
        o.data.transform(Matrix.Scale(s, 4))
    o.location = (0, 0, 0); o.rotation_mode = 'XYZ'; o.rotation_euler = (0, 0, 0)
    for p in o.data.polygons: p.use_smooth = True
    return o

def soften(o, sat=1.1, rough_min=0.4):
    for m in o.data.materials:
        if not m or not m.use_nodes: continue
        for n in m.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                if not n.inputs["Roughness"].is_linked: n.inputs["Roughness"].default_value = max(rough_min, n.inputs["Roughness"].default_value)
            if n.type == 'NORMAL_MAP': n.inputs["Strength"].default_value = 0.35
            if n.type == 'BUMP': n.inputs["Strength"].default_value = 0.3

wall_m = mat("M_WallLR", (0.86, 0.80, 0.70), rough=0.75)
wall_b = mat("M_WallBed", (0.55, 0.66, 0.78), rough=0.75)
floor_m = mat("M_Wood", (0.52, 0.34, 0.20), rough=0.45, coat=0.25)
nt = floor_m.node_tree; p = nt.nodes["Principled BSDF"]
br = nt.nodes.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 2.0; br.offset = 0.5
br.inputs["Color1"].default_value = (0.55, 0.36, 0.21, 1); br.inputs["Color2"].default_value = (0.46, 0.29, 0.17, 1)
br.inputs["Mortar"].default_value = (0.30, 0.19, 0.11, 1); br.inputs["Mortar Size"].default_value = 0.003
br.inputs["Brick Width"].default_value = 1.6; br.inputs["Row Height"].default_value = 0.16
nt.links.new(br.outputs["Color"], p.inputs["Base Color"])
white_m = mat("M_Trim", (0.95, 0.94, 0.92), rough=0.4)
sky_m = mat("M_WindowSky", (0.5, 0.8, 1.0), emit=((0.55, 0.82, 1.0), 2.5))
nt = sky_m.node_tree; p = nt.nodes["Principled BSDF"]
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); ramp = nt.nodes.new("ShaderNodeValToRGB")
nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
ramp.color_ramp.elements[0].color = (0.91, 0.97, 1.0, 1); ramp.color_ramp.elements[1].color = (0.31, 0.76, 0.97, 1)
nt.links.new(ramp.outputs["Color"], p.inputs["Emission Color"]); nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])

def window(x, y, z, w, h, along='X', tag=""):
    if along == 'X':
        box("WinSky" + tag, (w, 0.02, h), (x, y + 0.03, z), sky_m, bevel=0)
        for (sx, sz, lx, lz) in ((0.06, h + 0.12, x - w / 2 - 0.03, z), (0.06, h + 0.12, x + w / 2 + 0.03, z), (w + 0.12, 0.06, x, z + h / 2 + 0.03),
                                 (w + 0.12, 0.08, x, z - h / 2 - 0.04), (0.04, h, x, z)):
            box("WinFrame" + tag, (sx, 0.07, sz), (lx, y, lz), white_m, bevel=0.006)
    else:
        box("WinSky" + tag, (0.02, w, h), (x + 0.03, y, z), sky_m, bevel=0)
        for (sy, sz, ly, lz) in ((0.06, h + 0.12, y - w / 2 - 0.03, z), (0.06, h + 0.12, y + w / 2 + 0.03, z), (w + 0.12, 0.06, y, z + h / 2 + 0.03),
                                 (w + 0.12, 0.08, y, z - h / 2 - 0.04), (0.04, h, y, z)):
            box("WinFrame" + tag, (0.07, sy, sz), (x, ly, lz), white_m, bevel=0.006)

def frame_art(name, loc, size, col, rot_z=0.0):
    f = box(name + "Frame", (size[0], 0.03, size[1]), loc, white_m, bevel=0.006, rot=(0, 0, rot_z))
    pm = mat("M_" + name, col, rough=0.6)
    nt = pm.node_tree; pp = nt.nodes["Principled BSDF"]; wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 1.4
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*col, 1); cr.color_ramp.elements[1].color = (0.97, 0.95, 0.90, 1)
    nt.links.new(wv.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], pp.inputs["Base Color"])
    off = Matrix.Rotation(rot_z, 3, 'Z') @ Vector((0, -0.017, 0))
    box(name, (size[0] - 0.08, 0.01, size[1] - 0.08), Vector(loc) + off, pm, bevel=0, rot=(0, 0, rot_z))

# ------------------------------------------------------------------ LIVING ROOM (origin)
box("LR_Floor", (7, 7, 0.02), (0, 0, -0.01), floor_m, bevel=0)
box("LR_WallBack", (7, 0.1, 2.8), (0, 2.0, 1.4), wall_m, bevel=0)
box("LR_WallLeft", (0.1, 7, 2.8), (-2.0, 0, 1.4), wall_m, bevel=0)
box("LR_Skirt", (7, 0.03, 0.10), (0, 1.94, 0.05), white_m, bevel=0.004)
box("LR_SkirtL", (0.03, 7, 0.10), (-1.94, 0, 0.05), white_m, bevel=0.004)
window(0.6, 1.94, 1.45, 1.3, 1.1, 'X', "LR")
frame_art("LR_Art1", (-0.9, 1.93, 1.55), (0.55, 0.70), (0.95, 0.62, 0.30))
frame_art("LR_Art2", (-1.93, -0.3, 1.55), (0.70, 0.50), (0.36, 0.62, 0.75), rot_z=R_(90))
rug_m = mat("M_Rug", (0.70, 0.32, 0.30), rough=0.9, sheen=0.4)
nt = rug_m.node_tree; p = nt.nodes["Principled BSDF"]
tc = nt.nodes.new("ShaderNodeTexCoord"); ch = nt.nodes.new("ShaderNodeTexChecker"); ch.inputs["Scale"].default_value = 7.0
ch.inputs["Color1"].default_value = (0.62, 0.56, 0.48, 1); ch.inputs["Color2"].default_value = (0.70, 0.64, 0.56, 1)
nt.links.new(tc.outputs["Object"], ch.inputs["Vector"]); nt.links.new(ch.outputs["Color"], p.inputs["Base Color"])
box("LR_Rug", (2.4, 2.0, 0.012), (-0.1, 0.0, 0.006), rug_m, bevel=0.004)
SOFA = imp(DL + "/sofa.glb", "Sofa", 1.95, axis=0); soften(SOFA)
SOFA.rotation_euler = (0, 0, R_(90))
for m_ in SOFA.data.materials:
    if m_ and m_.use_nodes:
        pp = m_.node_tree.nodes.get("Principled BSDF")
        if pp:
            for l_ in list(pp.inputs["Base Color"].links): m_.node_tree.links.remove(l_)
            pp.inputs["Base Color"].default_value = (0.20, 0.33, 0.45, 1) if m_.name.startswith(("Fabric", "material")) else (0.30, 0.44, 0.56, 1)
            for n_ in m_.node_tree.nodes:
                if n_.type == 'NORMAL_MAP': n_.inputs["Strength"].default_value = 0.3
SOFA.location = (-1.45, 0.25, 0.0)
side_m = mat("M_SideTable", (0.40, 0.26, 0.16), rough=0.4, coat=0.3)
box("LR_SideTop", (0.42, 0.42, 0.03), (-1.5, -1.05, 0.55), side_m, bevel=0.01)
for dx in (-0.17, 0.17):
    for dy in (-0.17, 0.17):
        cyl("LR_SideLeg", 0.015, 0.54, (-1.5 + dx, -1.05 + dy, 0.27), side_m)
plant_m = mat("M_Pot", (0.85, 0.82, 0.76), rough=0.4); leaf_m = mat("M_Leaf", (0.15, 0.45, 0.18), rough=0.5)
cyl("LR_Pot", 0.16, 0.34, (1.6, 1.6, 0.17), plant_m, bevel=0.01)
for i in range(9):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(1.6 + random.uniform(-0.12, 0.12), 1.6 + random.uniform(-0.12, 0.12), 0.55 + random.uniform(0, 0.4)))
    lf = bpy.context.active_object; lf.name = "LR_Leaf"; lf.scale = (0.25, 1.0, 0.08); lf.rotation_euler = (random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6), random.uniform(0, 6))
    lf.data.materials.append(leaf_m); bpy.ops.object.shade_smooth()
shelf_m = mat("M_Shelf", (0.93, 0.92, 0.88), rough=0.4)
box("LR_Shelf", (1.2, 0.35, 0.9), (1.6, 0.4, 0.45), shelf_m, bevel=0.01, rot=(0, 0, R_(90)))
for i, c in enumerate(((0.8, 0.3, 0.2), (0.2, 0.4, 0.7), (0.3, 0.6, 0.3), (0.85, 0.7, 0.2), (0.5, 0.3, 0.6))):
    box("LR_Book", (0.04, 0.2, 0.26), (1.55, -0.05 + i * 0.05, 1.03), mat("M_Book%d" % i, c, rough=0.5), bevel=0.003)

# ------------------------------------------------------------------ LEGO-type bricks (generic, no logo)
def plastic(name, col):
    return mat(name, col, rough=0.22, coat=0.6)
P = 0.008; H_ = 0.0096
def brick(name, nx, ny, material, stud=True):
    bm = bmesh.new()
    w, d = nx * P - 0.0002, ny * P - 0.0002
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * w, v.co.y * d, (v.co.z + 0.5) * H_))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    b = o.modifiers.new("bev", 'BEVEL'); b.width = 0.0004; b.segments = 2
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.modifier_apply(modifier="bev")
    parts = [o]
    if stud:
        for i in range(nx):
            for j in range(ny):
                bpy.ops.mesh.primitive_cylinder_add(radius=0.0024, depth=0.0018, vertices=24,
                                                    location=((i - (nx - 1) / 2) * P, (j - (ny - 1) / 2) * P, H_ + 0.0009))
                s = bpy.context.active_object
                bv = s.modifiers.new("bev", 'BEVEL'); bv.width = 0.0003; bv.segments = 2
                bpy.ops.object.modifier_apply(modifier="bev"); parts.append(s)
    bpy.ops.object.select_all(action='DESELECT')
    for p_ in parts: p_.select_set(True)
    bpy.context.view_layer.objects.active = o; bpy.ops.object.join()
    o.data.materials.append(material)
    for p_ in o.data.polygons: p_.use_smooth = True
    return o

RED = brick("BrickRed", 1, 1, mat("M_BrickRed", (0.85, 0.02, 0.01), rough=0.22, coat=0.6, emit=((1.0, 0.06, 0.03), 1.0)))          # the hero: one model all film
YEL = brick("BrickYellow", 2, 1, mat("M_BrickYellow", (1.0, 0.72, 0.0), rough=0.22, coat=0.6, emit=((1.0, 0.75, 0.05), 0.4)))    # the larger one Mom removes
for o_ in (RED, YEL):
    try:
        bpy.context.view_layer.objects.active = o_; bpy.ops.object.shade_auto_smooth(angle=R_(35))
    except Exception: pass
cols = {"blue": (0.04, 0.22, 0.75), "green": (0.05, 0.50, 0.15), "white": (0.92, 0.92, 0.90), "orange": (0.95, 0.35, 0.03),
        "lime": (0.55, 0.75, 0.10), "azure": (0.15, 0.60, 0.90)}
PM = {k: plastic("M_Brick_" + k, v) for k, v in cols.items()}
# a toy tub (rounded plastic box) and loose bricks lying flat ON the rug, a small built house (stud-aligned, flush)
tub_m = mat("M_Tub", (0.15, 0.55, 0.85), rough=0.3, coat=0.4)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts: v.co = Vector((v.co.x * 0.34, v.co.y * 0.24, (v.co.z + 0.5) * 0.14))
top = [f for f in bm.faces if f.normal.z > 0.9]; bmesh.ops.delete(bm, geom=top, context='FACES_ONLY')
me = bpy.data.meshes.new("ToyTub"); bm.to_mesh(me); bm.free()
TUB = bpy.data.objects.new("ToyTub", me); bpy.context.collection.objects.link(TUB); me.materials.append(tub_m)
so = TUB.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.006; so.offset = -1
bv = TUB.modifiers.new("bev", 'BEVEL'); bv.width = 0.012; bv.segments = 4; bv.limit_method = 'ANGLE'
for p_ in me.polygons: p_.use_smooth = True
TUB.location = (0.23, 0.35, 0.012); TUB.rotation_euler = (0, 0, R_(18))
SCATTER = []
names = list(cols)
k = 0
def place(nx, ny, cname, loc, yaw, base_z):
    global k
    b = brick("Scatter%02d" % k, nx, ny, PM[cname]); k += 1
    b.location = (loc[0], loc[1], base_z); b.rotation_euler = (0, 0, yaw); SCATTER.append(b); return b
RUG_Z = 0.012
rng = random.Random(5)
spots = [(x - 0.19, y + 0.23) for x, y in [(0.20, -0.30), (0.30, -0.22), (0.12, -0.42), (0.36, -0.40), (0.05, -0.47), (0.45, -0.30),
         (0.26, -0.52), (0.52, -0.18), (0.40, -0.55), (0.55, -0.45)]]
spots = [q for q in spots if min(math.hypot(q[0] - hx_, q[1] - hy_) for hx_, hy_ in ((0.02, -0.01), (0.06, -0.06))) > 0.07]
for i, (x, y) in enumerate(spots):
    nx, ny = rng.choice([(2, 2), (2, 4), (1, 2), (2, 3), (1, 4)])
    place(nx, ny, names[i % len(names)], (x, y), rng.uniform(0, math.pi), RUG_Z)
# a little house: 3 courses, stud-aligned and flush (each course exactly one brick height up)
hx, hy, hyaw = 0.45, 0.18, R_(-20)
Rh = Matrix.Rotation(hyaw, 3, 'Z')
for c in range(3):
    for (ox, oy, nx, ny) in ((0, 0, 4, 1), (0, 0.040, 4, 1), (-0.012, 0.020, 1, 4), (0.012, 0.020, 1, 4)):
        sh = 0.008 if c % 2 else 0.0
        off = Rh @ Vector((ox + (sh if ny == 1 else 0), oy, 0))
        place(nx, ny, ["white", "azure", "white"][c], (hx + off.x, hy + off.y), hyaw + (0 if ny == 1 else 0), RUG_Z + c * H_)
# bricks inside the tub, flat on its floor
for i in range(6):
    place(2, 2 if i % 2 else 4, names[(i + 2) % len(names)], (0.23 + rng.uniform(-0.15, 0.15), 0.35 + rng.uniform(-0.08, 0.08)), rng.uniform(0, 3), 0.012 + 0.006 + (i // 3) * H_)
for b in SCATTER: b.parent = None

# hero bricks lie on the rug at the start (flat, studs up)
RED.location = (0.02, -0.01, RUG_Z); RED.rotation_euler = (0, 0, R_(25))
YEL.location = (0.06, -0.06, RUG_Z); YEL.rotation_euler = (0, 0, R_(-35))

# tweezers on the side table; Mom's book on the sofa
TWZ = imp(DL + "/tweezers.glb", "Tweezers", 0.11)
bb = [v.co.copy() for v in TWZ.data.vertices]; ext = [max(v[i] for v in bb) - min(v[i] for v in bb) for i in range(3)]
ax = max(range(3), key=lambda i: ext[i])
if ax == 2: TWZ.data.transform(Matrix.Rotation(R_(-90), 4, 'X'))
elif ax == 0: TWZ.data.transform(Matrix.Rotation(R_(90), 4, 'Z'))
bb = [v.co.copy() for v in TWZ.data.vertices]; mn = Vector([min(v[i] for v in bb) for i in range(3)]); mx = Vector([max(v[i] for v in bb) for i in range(3)])
TWZ.data.transform(Matrix.Translation(-Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, (mn.z + mx.z) / 2))))
# tip at +Y: the narrow end
vs = [v.co for v in TWZ.data.vertices]; y0, y1 = min(v.y for v in vs), max(v.y for v in vs)
wd = lambda lo, hi: max([abs(v.x) for v in vs if lo <= v.y <= hi] or [0])
if wd(y1 - 0.01, y1) > wd(y0, y0 + 0.01): TWZ.data.transform(Matrix.Rotation(R_(180), 4, 'Z'))
for m_ in TWZ.data.materials:
    if m_ and m_.use_nodes:
        pp = m_.node_tree.nodes.get("Principled BSDF")
        if pp: pp.inputs["Metallic"].default_value = 1.0; pp.inputs["Roughness"].default_value = 0.25
print("TWEEZERS dims", [round(max(v.co[i] for v in TWZ.data.vertices)-min(v.co[i] for v in TWZ.data.vertices),4) for i in range(3)])
book_m = mat("M_BookCover", (0.85, 0.40, 0.25), rough=0.5); page_m = mat("M_Pages", (0.95, 0.93, 0.86), rough=0.8)
BOOK = box("Book", (0.17, 0.24, 0.022), (0, 0, 0), book_m, bevel=0.003)
pg = box("BookPages", (0.165, 0.23, 0.018), (0.004, 0, 0), page_m, bevel=0.001)
bpy.ops.object.select_all(action='DESELECT'); pg.select_set(True); BOOK.select_set(True); bpy.context.view_layer.objects.active = BOOK; bpy.ops.object.join()
BOOK.data.transform(Matrix.Translation((0, 0, 0.011)))

# ------------------------------------------------------------------ BEDROOM (x = +8)
def at(x, y, z): return (BED_X + x, y, z)
box("BR_Floor", (6, 6, 0.02), at(0, 0, -0.01), floor_m, bevel=0)
box("BR_WallBack", (6, 0.1, 2.8), at(0, 1.6, 1.4), wall_b, bevel=0)
box("BR_WallLeft", (0.1, 6, 2.8), at(-1.7, 0, 1.4), wall_b, bevel=0)
box("BR_Skirt", (6, 0.03, 0.10), at(0, 1.54, 0.05), white_m, bevel=0.004)
window(BED_X - 1.64, -0.5, 1.5, 1.0, 1.1, 'Y', "BR")
frame_art("BR_Art", at(0.9, 1.54, 1.55), (0.6, 0.45), (0.45, 0.55, 0.85))
BED = imp(DL + "/bed.glb", "Bed", 2.05, axis=1); soften(BED)
BED.location = at(0, 0.5, 0); BED.rotation_euler = (0, 0, R_(180))   # pillows toward +Y (the headboard wall)      # headboard toward +Y (checked/rotated in stage B against the mattress ray test)
NSTAND = imp(DL + "/nightstand.glb", "Nightstand", 0.75, axis=2); soften(NSTAND)
NSTAND.location = at(-0.85, 1.3, 0)
box("BR_Rug", (1.4, 0.9, 0.01), at(0.0, -0.95, 0.005), mat("M_RugB", (0.85, 0.78, 0.62), rough=0.9, sheen=0.4), bevel=0.003)
# inhaler (blue actuator + steel canister + cap off), procedural, mouthpiece at local -Y, canister up +Z
inh_m = mat("M_Inhaler", (0.15, 0.40, 0.85), rough=0.3, coat=0.3); can_m = mat("M_Canister", (0.78, 0.80, 0.83), rough=0.25, metal=1.0)
body_ = box("Inhaler", (0.026, 0.022, 0.066), (0, 0, 0.033), inh_m, bevel=0.008, segs=4)
mp = box("InhMouth", (0.024, 0.026, 0.018), (0, -0.020, 0.010), inh_m, bevel=0.006, segs=4)
cn = cyl("InhCan", 0.0105, 0.05, (0, 0, 0.078), can_m, bevel=0.002)
for o_ in (body_, mp):
    bpy.context.view_layer.objects.active = o_; bpy.ops.object.modifier_apply(modifier="bev")
bpy.ops.object.select_all(action='DESELECT')
for o_ in (mp, cn, body_): o_.select_set(True)
bpy.context.view_layer.objects.active = body_; bpy.ops.object.join(); INH = body_
INH.location = at(-0.85, 1.25, 0.80)
tis_m = mat("M_Tissue", (0.97, 0.97, 0.98), rough=0.9, sheen=0.3)
box("TissueBox", (0.12, 0.22, 0.09), at(-0.92, 1.12, 0.0), mat("M_TissueBox", (0.40, 0.70, 0.75), rough=0.5), bevel=0.006)

# ------------------------------------------------------------------ BATHROOM (x = +16)
tile_m = mat("M_Tile", (0.48, 0.68, 0.74), rough=0.2, coat=0.5)
nt = tile_m.node_tree; p = nt.nodes["Principled BSDF"]
br = nt.nodes.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 6.0; br.offset = 0.0
br.inputs["Color1"].default_value = (0.48, 0.68, 0.74, 1); br.inputs["Color2"].default_value = (0.44, 0.64, 0.70, 1)
br.inputs["Mortar"].default_value = (0.95, 0.97, 0.97, 1); br.inputs["Mortar Size"].default_value = 0.01
br.inputs["Brick Width"].default_value = 1.0; br.inputs["Row Height"].default_value = 1.0
nt.links.new(br.outputs["Color"], p.inputs["Base Color"])
box("BA_Floor", (5, 5, 0.02), (BATH_X, 0, -0.01), tile_m, bevel=0)
box("BA_WallBack", (5, 0.1, 2.8), (BATH_X, 0.95, 1.4), tile_m, bevel=0)
box("BA_WallLeft", (0.1, 5, 2.8), (BATH_X - 1.0, 0, 1.4), tile_m, bevel=0)
box("BA_WallRight", (0.1, 5, 2.8), (BATH_X + 1.0, 0, 1.4), tile_m, bevel=0)
# tub (hollow rounded acrylic), tiled pony wall at chest height in front (no nudity read: he is framed over it), shower head, rail
acr = mat("M_Acrylic", (0.90, 0.92, 0.93), rough=0.18, coat=0.6)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts: v.co = Vector((v.co.x * 1.65, v.co.y * 0.80, (v.co.z + 0.5) * 0.52))
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.9], context='FACES_ONLY')
me = bpy.data.meshes.new("Tub"); bm.to_mesh(me); bm.free()
TUBO = bpy.data.objects.new("BA_Tub", me); bpy.context.collection.objects.link(TUBO); me.materials.append(acr)
s_ = TUBO.modifiers.new("solid", 'SOLIDIFY'); s_.thickness = 0.05; s_.offset = -1
b_ = TUBO.modifiers.new("bev", 'BEVEL'); b_.width = 0.02; b_.segments = 4; b_.limit_method = 'ANGLE'
for p_ in me.polygons: p_.use_smooth = True
TUBO.location = (BATH_X, 0.50, 0.0)
box("BA_TubFloor", (1.55, 0.70, 0.06), (BATH_X, 0.50, 0.03), acr, bevel=0.01)
tile2 = mat("M_TileAccent", (0.18, 0.50, 0.58), rough=0.25, coat=0.4)
nt = tile2.node_tree; p = nt.nodes["Principled BSDF"]
br = nt.nodes.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 9.0; br.offset = 0.5
br.inputs["Color1"].default_value = (0.18, 0.50, 0.58, 1); br.inputs["Color2"].default_value = (0.15, 0.45, 0.53, 1)
br.inputs["Mortar"].default_value = (0.92, 0.95, 0.95, 1); br.inputs["Mortar Size"].default_value = 0.012
nt.links.new(br.outputs["Color"], p.inputs["Base Color"])
PONY = box("BA_PonyWall", (1.70, 0.10, 1.04), (BATH_X, 0.07, 0.52 + 0.52), tile2, bevel=0.012)
box("BA_PonyCap", (1.74, 0.14, 0.03), (BATH_X, 0.07, 1.56), white_m, bevel=0.008)
chrome = mat("M_Chrome", (0.90, 0.91, 0.93), rough=0.08, metal=1.0)
cyl("BA_ShowerArm", 0.012, 0.30, (BATH_X - 0.40, 0.80, 2.10), chrome, rot=(R_(70), 0, 0))
SHH = cyl("BA_ShowerHead", 0.085, 0.03, (BATH_X - 0.40, 0.66, 2.05), chrome, rot=(R_(-25), 0, 0), bevel=0.008)
cyl("BA_Rail", 0.01, 1.7, (BATH_X, 0.10, 2.15), chrome, rot=(0, R_(90), 0))
for dx, h in ((-0.35, 1.25), (0.35, 1.25)):
    cyl("BA_Tap", 0.02, 0.10, (BATH_X + dx * 0.3, 0.88, 0.75), chrome, rot=(R_(90), 0, 0))
# shower curtain gathered at the right end (opaque, folded)
cur_m = stripes("M_Curtain", (0.95, 0.95, 0.96), (0.30, 0.62, 0.72), scale=6.0)
bpy.ops.mesh.primitive_plane_add(size=1, location=(BATH_X + 0.72, 0.30, 1.45))
CUR = bpy.context.active_object; CUR.name = "BA_Curtain"; CUR.scale = (0.32, 1, 1.38); CUR.rotation_euler = (R_(90), 0, 0)
bpy.ops.object.transform_apply(scale=True, rotation=True)
sb = CUR.modifiers.new("sub", 'SUBSURF'); sb.levels = 3; sb.render_levels = 3; sb.subdivision_type = 'SIMPLE'
wtex = bpy.data.textures.new("CurtainWave", 'WOOD'); wtex.wood_type = 'BANDNOISE' if False else 'BANDS'; wtex.noise_basis_2 = 'SIN'
dp = CUR.modifiers.new("folds", 'DISPLACE'); dp.texture = wtex; dp.strength = 0.05; dp.direction = 'Y'; dp.texture_coords = 'LOCAL'
so = CUR.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.003
CUR.data.materials.append(cur_m)
for p_ in CUR.data.polygons: p_.use_smooth = True
box("BA_Mirror", (0.6, 0.02, 0.8), (BATH_X + 1.3, 0.95, 1.5), white_m, bevel=0.01)
box("BA_TowelBar", (0.6, 0.03, 0.03), (BATH_X - 0.95 + 0.04, -0.6, 1.2), chrome, bevel=0.005, rot=(0, 0, R_(90)))
TOW = box("BA_Towel", (0.04, 0.45, 0.6), (BATH_X - 0.92, -0.6, 0.92), fabric("M_Towel", (0.95, 0.55, 0.35), scale=300, bump=0.6), bevel=0.02, segs=4)

# ------------------------------------------------------------------ x-ray anatomy: a skull (fitted in stage B) + the void backdrop
SKULL = imp(DL + "/skull.glb", "Skull")
bone_m = mat("M_SkullBone", (0.94, 0.89, 0.76), rough=0.4, coat=0.2)
SKULL.data.materials.clear(); SKULL.data.materials.append(bone_m)
for p_ in SKULL.data.polygons: p_.material_index = 0
print("SKULL dims", tuple(round(d, 3) for d in SKULL.dimensions))

# ------------------------------------------------------------------ look: AgX Punchy, bright, clean
sc.view_settings.view_transform = 'AgX'
sc.view_settings.exposure = 0.0
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: pass
sc.render.engine = 'CYCLES'
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 8; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3; sc.cycles.transmission_bounces = 8
sc.cycles.transparent_max_bounces = 32; sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
sc.render.use_motion_blur = False
w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.75, 0.82, 0.90, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.25

def area(name, loc, power, size, col, target):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = power; ld.size = size; ld.color = col; ld.shape = 'DISK'
    o = bpy.data.objects.new(name, ld); bpy.context.collection.objects.link(o); o.location = loc
    d = Vector(target) - o.location; o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return o
# living room: warm key from the window side, cool fill, rim
area("LR_Key", (1.2, -1.6, 2.3), 220, 1.6, (1.0, 0.92, 0.82), (-0.3, 0.1, 0.6))
area("LR_Fill", (-1.0, -2.2, 1.4), 70, 2.0, (0.85, 0.92, 1.0), (-0.3, 0.1, 0.6))
area("LR_Rim", (0.3, 1.7, 2.2), 120, 1.0, (1.0, 0.95, 0.88), (-0.3, 0.1, 0.7))
area("LR_Win", (0.6, 1.8, 1.5), 90, 1.2, (0.80, 0.90, 1.0), (0.0, 0.0, 0.5))
# bedroom: warm lamp-side key, cool window fill, rim
area("BR_Key", (BED_X - 0.9, -0.6, 1.9), 150, 1.0, (1.0, 0.85, 0.65), (BED_X, 0.9, 0.8))
area("BR_Fill", (BED_X + 1.2, -1.8, 1.6), 70, 2.0, (0.80, 0.88, 1.0), (BED_X, 0.9, 0.8))
area("BR_Rim", (BED_X + 0.6, 1.4, 2.2), 70, 1.0, (0.95, 0.95, 1.0), (BED_X, 0.9, 0.9))
lp = bpy.data.lights.new("BR_LampBulb", 'POINT'); lp.energy = 25; lp.color = (1.0, 0.75, 0.45); lp.shadow_soft_size = 0.08
lo = bpy.data.objects.new("BR_LampBulb", lp); bpy.context.collection.objects.link(lo); lo.location = (BED_X - 0.85, 1.3, 0.95)
# bathroom: soft top light, front fill, warm rim
area("BA_Top", (BATH_X, 0.0, 2.6), 38, 1.4, (1.0, 0.97, 0.94), (BATH_X, 0.2, 1.2))
area("BA_Fill", (BATH_X - 0.6, -1.8, 1.6), 32, 1.8, (0.88, 0.94, 1.0), (BATH_X, 0.2, 1.4))
area("BA_Rim", (BATH_X + 0.8, 0.8, 2.2), 40, 0.8, (1.0, 0.90, 0.78), (BATH_X, 0.2, 1.5))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("BUILD_OK", OUT)
for r in (BOY, MOM, MAN):
    print("BONES", r.name, {n: tuple(round(x, 3) for x in r.data.bones[n].head_local) for n in ("root", "head", "eye.L", "foot.L", "wrist.L")})
print("BED dims", tuple(round(d, 3) for d in BED.dimensions), "SOFA", tuple(round(d, 3) for d in SOFA.dimensions))
