"""BeethovenDeaf v011 shared helpers (exec by 01_build.py / 02_animate.py). Material/modelling/MPFB helpers follow the
client-approved rebuilds (EarInArm v015, MonkeyHead v015, LegoInNose v013) and SurgeonBrandsLivers v015 (real garments)."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler
from mathutils.bvhtree import BVHTree
R_ = math.radians
sc = bpy.context.scene
# ------------------------------------------------------------------ materials
def mat(name, col, rough=0.5, metal=0.0, sss=0.0, coat=0.0, sheen=0.0, emit=None, alpha=1.0, spec=None):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*col, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if spec is not None:
        p.inputs["Specular IOR Level"].default_value = spec
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
    if alpha < 1.0:
        p.inputs["Alpha"].default_value = alpha
    return m

def fabric(name, col, scale=900.0, bump=0.25, rough=0.8):
    """solid-colour cloth with a fine weave bump (clean animated look)"""
    m = mat(name, col, rough=rough, sheen=0.15)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); wv = nt.nodes.new("ShaderNodeTexWave")
    wv.inputs["Scale"].default_value = scale; wv.inputs["Distortion"].default_value = 2.0
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.0005
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"]); nt.links.new(wv.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m

def tiles(name, c1, c2, mortar, scale=4.0, w=0.5, h=0.5, rough=0.35, coat=0.2):
    m = mat(name, c1, rough=rough, coat=coat)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    br = nt.nodes.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = scale
    br.inputs["Color1"].default_value = (*c1, 1); br.inputs["Color2"].default_value = (*c2, 1)
    br.inputs["Mortar"].default_value = (*mortar, 1); br.inputs["Mortar Size"].default_value = 0.012; br.offset = 0.0
    br.inputs["Brick Width"].default_value = w; br.inputs["Row Height"].default_value = h
    nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], p.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25
    nt.links.new(br.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
    return m

def wood(name, c1, c2, scale=3.0, rough=0.4):
    m = mat(name, c1, rough=rough, coat=0.25)
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1, 12, 1)
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'RINGS'; wv.inputs["Scale"].default_value = scale; wv.inputs["Distortion"].default_value = 6
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], wv.inputs["Vector"])
    nt.links.new(wv.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
    return m

def gradient_emit(name, top, bottom, strength=2.0, axis="Z"):
    """a vertical sky/backdrop gradient (emission), used in windows"""
    m = mat(name, top, emit=(top, strength))
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs[axis], ramp.inputs["Fac"])
    ramp.color_ramp.elements[0].color = (*bottom, 1); ramp.color_ramp.elements[1].color = (*top, 1)
    nt.links.new(ramp.outputs["Color"], p.inputs["Emission Color"]); nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
    return m

def image_mat(name, path, emit=0.0, rough=0.5, alpha=True):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]; p.inputs["Roughness"].default_value = rough
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(path); tx.extension = 'CLIP'
    nt.links.new(tx.outputs["Color"], p.inputs["Base Color"])
    if alpha: nt.links.new(tx.outputs["Alpha"], p.inputs["Alpha"])
    if emit:
        nt.links.new(tx.outputs["Color"], p.inputs["Emission Color"]); p.inputs["Emission Strength"].default_value = emit
    return m

# ------------------------------------------------------------------ modelling helpers
def link(o, parent=None):
    if o.name not in sc.collection.objects and not o.users_collection:
        sc.collection.objects.link(o)
    if parent is not None:
        o.parent = parent
    return o

def box(name, size, loc, material, bevel=0.01, segs=3, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = segs; b.limit_method = 'ANGLE'
    o.data.materials.append(material)
    for p in o.data.polygons: p.use_smooth = True
    if parent is not None:
        mw = o.matrix_world.copy(); o.parent = parent; o.matrix_world = parent.matrix_world @ mw
    return o

def cyl(name, r, h, loc, material, rot=(0, 0, 0), verts=32, bevel=0.0, parent=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.active_object; o.name = name; o.data.materials.append(material)
    if bevel:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = 3; b.limit_method = 'ANGLE'
    bpy.ops.object.shade_smooth()
    if parent is not None:
        mw = o.matrix_world.copy(); o.parent = parent; o.matrix_world = parent.matrix_world @ mw
    return o

def sphere(name, r, loc, material, parent=None, segs=24):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=segs, ring_count=segs // 2)
    o = bpy.context.active_object; o.name = name; o.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    if parent is not None:
        mw = o.matrix_world.copy(); o.parent = parent; o.matrix_world = parent.matrix_world @ mw
    return o

def empty(name, loc=(0, 0, 0), rot=(0, 0, 0), parent=None, size=0.1):
    e = bpy.data.objects.new(name, None); sc.collection.objects.link(e)
    e.location = loc; e.rotation_euler = rot; e.empty_display_size = size
    if parent is not None: e.parent = parent
    return e

def curve_tube(name, pts, bevel, material, parent=None, res=6):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = bevel; cu.bevel_resolution = 3
    cu.resolution_u = res; cu.use_fill_caps = True
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = Vector(p); bp.handle_left_type = bp.handle_right_type = 'AUTO'
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o); cu.materials.append(material)
    if parent is not None: o.parent = parent
    return o

# ------------------------------------------------------------------ characters (MPFB2, CC0 MakeHuman assets)
def human(name, gender, age, race, hair, skin, eyebrow, height=0.5, muscle=0.5, weight=0.5, prop=0.6, shoes="shoes03/shoes03.mhclo", clothes=(), cup=0.5):
    from bl_ext.user_default.mpfb.services.humanservice import HumanService
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": gender, "age": age, "muscle": muscle, "weight": weight, "proportions": prop,
                         "height": height, "cupsize": cup, "firmness": 0.5, "race": race}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = eyebrow
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair
    info["clothes"] = list(clothes) + ([shoes] if shoes else [])
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

def bone_names(rig):
    return {b.name for b in rig.data.bones}

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

def bl(rig, n): return rig.data.bones[n].head_local.copy()

def part(rig, key):
    for c in rig.children:
        if c.type == 'MESH' and key in c.name: return c
    return None
def iter_fcurves(action):
    try:
        for fc in action.fcurves: yield fc
    except AttributeError:
        for layer in action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for fc in cb.fcurves: yield fc

def key_vis(objs, f, visible):
    """LESSONS 2.14: key hide_viewport together with hide_render (constant)"""
    for o in objs:
        o.hide_render = not visible; o.hide_viewport = not visible
        o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)

# ------------------------------------------------------------------ real garments (MakeHuman community CC0 clothes, fitted by MPFB)
def colorize(obj, rgb, gain=1.7):
    """keep the garment texture's folds/weave as value, recolour it to rgb (deep, saturated wardrobe colours)"""
    for m in obj.data.materials:
        if not m or not m.use_nodes: continue
        nt = m.node_tree
        for p in [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']:
            bc = p.inputs["Base Color"]
            if bc.is_linked:
                src = bc.links[0].from_socket
                bw = nt.nodes.new("ShaderNodeRGBToBW"); nt.links.new(src, bw.inputs[0])
                mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs["Factor"].default_value = 1.0
                nt.links.new(bw.outputs[0], mul.inputs["A"]); mul.inputs["B"].default_value = (*[min(1.0, c * gain) for c in rgb], 1)
                nt.links.new(mul.outputs["Result"], bc)
            else:
                bc.default_value = (*rgb, 1)
            p.inputs["Roughness"].default_value = max(0.6, p.inputs["Roughness"].default_value)

# ------------------------------------------------------------------ v011: SOLID bodies under real garments (client lesson: no hollow clothes)
def covered_by(body, garments, dist=0.03):
    """body verts (rest) that lie under any of the garments"""
    cov = set()
    for g in garments:
        bvh = BVHTree.FromPolygons([v.co.copy() for v in g.data.vertices], [tuple(p.vertices) for p in g.data.polygons])
        Mi = g.matrix_world.inverted() @ body.matrix_world
        for v in body.data.vertices:
            loc, nrm, _, d = bvh.find_nearest(Mi @ v.co)
            if loc is not None and d < dist: cov.add(v.index)
    return cov

def solid_inset(body, covered, inset=0.007, rings=4, name="SolidInset"):
    """the skin under clothes is NOT removed (no hollow garments): it is pulled inward along its normal by `inset`
    (full inside, fading to 0 over `rings` edge rings at the hems), so the garment always sits outside it while every
    opening (cuffs, collar, trouser legs) shows a solid body."""
    me = body.data; nb = {i: set() for i in range(len(me.vertices))}
    for e in me.edges:
        a_, b_ = e.vertices; nb[a_].add(b_); nb[b_].add(a_)
    w = {i: 1.0 for i in covered}
    layer = set(covered)
    for k in range(rings):
        edge = {i for i in layer if any(n not in layer for n in nb[i])}
        for i in edge: w[i] = min(w[i], (k + 0.5) / rings)
        layer = layer - edge
    vg = body.vertex_groups.get(name) or body.vertex_groups.new(name=name)
    for i, x in w.items(): vg.add([i], x, 'REPLACE')
    d = body.modifiers.new(name, 'DISPLACE'); d.vertex_group = name; d.mid_level = 0.0; d.strength = -inset; d.direction = 'NORMAL'
    while body.modifiers.find(name) > 0:
        i = body.modifiers.find(name); body.modifiers.move(i, i - 1)
    return d

def thicken(g, t=0.0035):
    """real cloth thickness at every hem/cuff/collar (no paper-thin edges)"""
    s = g.modifiers.new("Thick", 'SOLIDIFY'); s.thickness = t; s.offset = -1.0; s.use_rim = True; s.use_even_offset = False
    return s

def sat_boost(obj, sat=1.25, val=1.0, hue=0.5):
    for m in obj.data.materials:
        if not m or not m.use_nodes: continue
        nt = m.node_tree
        for p in [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']:
            bc = p.inputs["Base Color"]
            if not bc.is_linked: continue
            src = bc.links[0].from_socket
            hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = sat; hs.inputs["Value"].default_value = val
            hs.inputs["Hue"].default_value = hue
            nt.links.new(src, hs.inputs["Color"]); nt.links.new(hs.outputs["Color"], bc)

def eye_group_fix():
    """EnhancedEye cornea: refractive transmission -> transparent mix (LESSONS 3, Connect03 a44130b)"""
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
