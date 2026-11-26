# Shared build helpers (from BellyFat_v018 / PrisonKeyCake_v011, director-approved rebuilds).
import bpy, bmesh, math, json, random
from mathutils import Vector, Matrix
from bl_ext.user_default.mpfb.services.humanservice import HumanService
R_ = math.radians
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
def human(name, gender, age, race, hair, skin, eyebrow, height=0.5, muscle=0.5, weight=0.5, prop=0.6, clothes=()):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": gender, "age": age, "muscle": muscle, "weight": weight, "proportions": prop,
                         "height": height, "cupsize": 0.5, "firmness": 0.5, "race": race}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = eyebrow
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair
    info["clothes"] = list(clothes)
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

# the MPFB EnhancedEye group: refractive cornea -> transmission 0 + Transparent mix (LESSONS 3, black-hole eyes)
def eye_group_fix():
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

def bl(rig, n): return rig.data.bones[n].head_local.copy()
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
