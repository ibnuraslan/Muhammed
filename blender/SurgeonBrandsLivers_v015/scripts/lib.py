"""SurgeonBrandsLivers v015 shared helpers (exec'd by 01_build.py / 02_animate.py).
Materials, MPFB humans, R1 one-piece garments (body copy, bisected, offset, solidify), hide-under masks, eye fix,
simple modelling helpers. Patterns follow the client-approved EarInArm v015 / MonkeyHead v015 builds."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

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
def human(name, gender, age, race, hair, skin, eyebrow, height=0.5, muscle=0.5, weight=0.5, prop=0.6, shoes="shoes03/shoes03.mhclo"):
    from bl_ext.user_default.mpfb.services.humanservice import HumanService
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    info["phenotype"] = {"gender": gender, "age": age, "muscle": muscle, "weight": weight, "proportions": prop,
                         "height": height, "cupsize": 0.5, "firmness": 0.5, "race": race}
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = eyebrow
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair
    info["clothes"] = [shoes] if shoes else []
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

def plane_side(co, p0, n):
    return (Vector(co) - Vector(p0)).dot(Vector(n))

def rest_relax(g, body, offset, iters, hem_z=None, collar_above=None):
    """cloth drape in the rest pose: push out by `offset`, relax interior vertices (hems pinned) so the cloth bridges
    hollows instead of hugging anatomy, and keep at least 0.7*offset from the skin (BVH push-out)."""
    from mathutils.bvhtree import BVHTree
    bvh = BVHTree.FromPolygons([v.co.copy() for v in body.data.vertices], [tuple(p.vertices) for p in body.data.polygons])
    bm = bmesh.new(); bm.from_mesh(g.data); bm.verts.ensure_lookup_table(); bm.normal_update()
    vs = bm.verts; n = len(vs)
    nbr = [[e.other_vert(v).index for e in v.link_edges] for v in vs]
    pin = [v.is_boundary for v in vs]
    # rings from the hem: the cloth closes in to ~4 mm at every hem/collar/cuff and eases out over 4 rings
    ring = [99] * n; front = [i for i in range(n) if pin[i] and (hem_z is None or vs[i].co.z > hem_z)]
    for i in front: ring[i] = 0
    for r_ in range(1, 6):
        nxt = []
        for i in front:
            for j in nbr[i]:
                if ring[j] > r_: ring[j] = r_; nxt.append(j)
        front = nxt
    offv = [offset * max(0.28, min(1.0, ring[i] / 5.0)) for i in range(n)]
    co = [v.co + v.normal * offv[v.index] for v in vs]
    def push():
        for i in range(n):
            loc, nrm, _, d = bvh.find_nearest(co[i])
            if loc is None: continue
            mn = offv[i] * 0.45
            if (co[i] - loc).dot(nrm) < mn: co[i] = loc + nrm * mn
    for it in range(iters):
        new = co[:]
        for i in range(n):
            if pin[i] or not nbr[i]: continue
            avg = Vector((0, 0, 0))
            for j in nbr[i]: avg += co[j]
            avg /= len(nbr[i])
            new[i] = co[i].lerp(avg, 0.6)
        co = new
        if it % 4 == 3: push()
    push()
    for i, v in enumerate(vs): v.co = co[i]
    if collar_above is not None:
        add_rolled_edges(bm, collar_above)
    bm.to_mesh(g.data); bm.free()

def add_rolled_edges(bm, z_above, rad=0.0045, seg=6):
    """a rolled/ribbed edge (small tube) along every boundary loop above z_above: clean collars and cuffs; the tube
    copies the skin weights of the edge vertex so it deforms with the garment"""
    dl = bm.verts.layers.deform.active
    bm.verts.ensure_lookup_table(); bm.normal_update()
    bedges = [e for e in bm.edges if e.is_boundary]
    adj = {}
    for e in bedges:
        a_, b_ = e.verts; adj.setdefault(a_, []).append(b_); adj.setdefault(b_, []).append(a_)
    seen = set(); loops = []
    for v0 in list(adj):
        if v0 in seen: continue
        loop = [v0]; seen.add(v0); prev = None; cur = v0
        while True:
            nx = [w for w in adj[cur] if w is not prev and w not in seen]
            if not nx: break
            prev, cur = cur, nx[0]; loop.append(cur); seen.add(cur)
        if len(loop) > 8: loops.append(loop)
    for loop in loops:
        if sum(v.co.z for v in loop) / len(loop) < z_above: continue
        n = len(loop); rings = []
        for i, v in enumerate(loop):
            t = (loop[(i + 1) % n].co - loop[i - 1].co).normalized()
            nr = v.normal.copy(); nr = (nr - t * nr.dot(t)).normalized()
            b = t.cross(nr)
            ring = []
            for k in range(seg):
                a_ = 2 * math.pi * k / seg
                nv = bm.verts.new(v.co + (nr * math.cos(a_) + b * math.sin(a_)) * rad + nr * rad * 0.4)
                if dl is not None:
                    for gi, w in v[dl].items(): nv[dl][gi] = w
                ring.append(nv)
            rings.append(ring)
        for i in range(n):
            r0, r1 = rings[i], rings[(i + 1) % n]
            for k in range(seg):
                try: bm.faces.new((r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]))
                except ValueError: pass

def garment(rig, body, name, region, cuts, offset, material, thick=0.003, folds=0.0, fold_scale=0.07, subd=True, relax=0, hem_z=None):
    """R1: one joined garment = duplicate of the body, bisected along clean cut planes, region-filtered,
    pushed out along the normals after the Armature, solidified, smoothed, subdivided."""
    g = body.copy(); g.data = body.data.copy(); g.name = name; g.data.name = name
    sc.collection.objects.link(g); g.parent = rig; g.matrix_world = body.matrix_world.copy()
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
    for mod in list(g.modifiers):
        if mod.type != 'ARMATURE': g.modifiers.remove(mod)
    if g.data.shape_keys:
        g.shape_key_clear()
    g.data.materials.clear(); g.data.materials.append(material)
    for p in g.data.polygons: p.use_smooth = True
    if relax:
        rest_relax(g, body, offset, relax, hem_z=hem_z, collar_above=(hem_z if hem_z is not None else None))
        offset_rt = 0.0
    else:
        offset_rt = offset
    at = g.data.attributes.new("rest_co", 'FLOAT_VECTOR', 'POINT')
    for i, v in enumerate(g.data.vertices): at.data[i].vector = v.co
    d = g.modifiers.new("offset", 'DISPLACE'); d.strength = offset_rt; d.mid_level = 0.0; d.direction = 'NORMAL'
    if folds > 0:
        tex = bpy.data.textures.new(name + "_folds", 'CLOUDS'); tex.noise_scale = fold_scale; tex.noise_depth = 1
        d2 = g.modifiers.new("folds", 'DISPLACE'); d2.texture = tex; d2.strength = folds; d2.mid_level = 0.35; d2.direction = 'NORMAL'
        d2.texture_coords = 'LOCAL'
    sm = g.modifiers.new("smooth", 'CORRECTIVE_SMOOTH'); sm.factor = 0.5; sm.iterations = 3; sm.smooth_type = 'LENGTH_WEIGHTED'
    so = g.modifiers.new("solid", 'SOLIDIFY'); so.thickness = thick; so.offset = -1.0
    if subd:
        sd = g.modifiers.new("subd", 'SUBSURF'); sd.levels = 1; sd.render_levels = 2
    covered = set()
    for v in body.data.vertices:
        bn = dom_bone(((gg.group, gg.weight) for gg in v.groups), idx2name)
        if region(v.co, bn):
            covered.add(v.index)
    return g, covered

def hide_under(body, covered, name="hide_under", rings=3):
    """mask the body skin that sits under a garment (eroded so no gap shows at the hems)"""
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
                    for lk in out_links:
                        nt.links.new(mx.outputs["Shader"], lk.to_socket)

def bl(rig, n): return rig.data.bones[n].head_local.copy()

def part(rig, key):
    for c in rig.children:
        if c.type == 'MESH' and key in c.name: return c
    return None

def wardrobe(rig, body, top_m, bot_m, sleeve, hem_drop, top_off, bot_off, top_folds, bot_folds, prefix, neck_drop=0.012,
             neck_tilt=-0.35, hide=True, top_only=False, bot_off_leg=None, vneck=0.0, relax=50):
    """top (long or short sleeves) + trousers, each ONE joined mesh (R1). Returns (top, trousers, covered_set)."""
    hip = bl(rig, "pelvis.L").z; neck = bl(rig, "neck01")
    cuts_top = [((0, 0, hip - hem_drop), (0, 0, -1)), ((0, neck.y, neck.z - neck_drop), (0, neck_tilt, 1))]
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
        if bn is None or in_region(bn, tuple(h for h in HEADB if h != "neck") + ("lowerleg", "foot", "toe") + HANDS): return False
        if in_region(bn, ("neck",)) and plane_side(co, *cuts_top[1]) > -0.004: return False
        if plane_side(co, *cuts_top[0]) > 1e-5 or plane_side(co, *cuts_top[1]) > 1e-5: return False
        if vneck and co.y < neck.y - 0.02 and abs(co.x) < (co.z - (neck.z - vneck)) * 0.75: return False
        if in_region(bn, ARM) or in_region(bn, ("shoulder", "clavicle")):
            s = "L" if co.x > 0 else "R"
            if plane_side(co, *arm_cut[s]) > 1e-5: return False
        return True
    top, cov_t = garment(rig, body, prefix + ".top", top_region, cuts_top, top_off, top_m, folds=top_folds, fold_scale=0.12, relax=relax * 2, hem_z=hip - 0.02)
    if top_only:
        if hide: hide_under(body, cov_t, name="hide_" + prefix)
        return top, None, cov_t
    ank = {s: bl(rig, "foot." + s).z + 0.075 for s in "LR"}
    cuts_bot = [((0, 0, hip + 0.035), (0, 0, 1)), ((0, 0, ank["L"]), (0, 0, -1))]
    def bot_region(co, bn):
        if bn is None:
            return ank["L"] < co.z < hip + 0.035 and abs(co.x) < 0.12
        if in_region(bn, HEADB + ARM + ("clavicle", "shoulder", "foot", "toe")): return False
        if plane_side(co, *cuts_bot[0]) > 1e-5 or plane_side(co, *cuts_bot[1]) > 1e-5: return False
        if abs(co.x) < 0.08 and co.z > ank["L"] + 0.25: return True      # crotch / fly: always cloth
        if in_region(bn, ("spine03", "spine04", "spine05", "breast")): return False
        return True
    bot, cov_b = garment(rig, body, prefix + ".trousers", bot_region, cuts_bot, bot_off, bot_m, folds=bot_folds, fold_scale=0.12, relax=relax)
    if hide: hide_under(body, cov_t | cov_b, name="hide_" + prefix)
    return top, bot, cov_t | cov_b

def gloves(rig, body, glove_m, reach=0.06):
    idx2 = {vg.index: vg.name for vg in body.vertex_groups if vg.name in bone_names(rig)}
    body.data.materials.append(glove_m); gi = len(body.data.materials) - 1
    for p in body.data.polygons:
        bns = [dom_bone(((g.group, g.weight) for g in body.data.vertices[v].groups), idx2) for v in p.vertices]
        if all(in_region(b, HANDS + ("lowerarm02",)) for b in bns):
            c = p.center; s = "L" if c.x > 0 else "R"
            el = bl(rig, "lowerarm01." + s); wr = bl(rig, "wrist." + s); dvec = (wr - el).normalized()
            if (c - wr).dot(dvec) > -reach: p.material_index = gi
    return gi

def to_head_only(g):
    for vg in list(g.vertex_groups): g.vertex_groups.remove(vg)
    vh = g.vertex_groups.new(name="head"); vh.add(list(range(len(g.data.vertices))), 1.0, 'REPLACE')

def cap_and_mask(rig, body, prefix, cap_m, mask_m=None, cap_off=0.016, cap_folds=0.008, cap_front=0.034):
    """soft cloth scrub cap (band, folds, bound to the head bone) + optional face mask. Returns (cap, mask, cap plane)."""
    eye_z = bl(rig, "eye.L").z
    nose = max(body.data.vertices, key=lambda v: -v.co.y if abs(v.co.x) < 0.006 and eye_z - 0.07 < v.co.z < eye_z else -9).co.copy()
    MASK = None
    if mask_m is not None:
        def mask_region(co, bn):
            return in_region(bn, ("head", "jaw", "oris", "levator", "risor", "neck03")) and abs(co.x) <= 0.07201 and co.y <= nose.y + 0.07501 and nose.z - 0.10001 <= co.z <= eye_z - 0.02199
        mask_cuts = [((0, 0, nose.z - 0.10), (0, 0, -1)), ((0, 0, eye_z - 0.022), (0, 0, 1)), ((0.072, 0, 0), (1, 0, 0)), ((-0.072, 0, 0), (-1, 0, 0)), ((0, nose.y + 0.075, 0), (0, 1, 0))]
        MASK, _ = garment(rig, body, prefix + ".mask", mask_region, mask_cuts, 0.008, mask_m, thick=0.002, folds=0.0, relax=12)
        to_head_only(MASK)
    cap_p0 = Vector((0, -0.10, eye_z + cap_front)); cap_n = Vector((0, 0.095, 0.2)).normalized()
    def cap_region(co, bn):
        return in_region(bn, ("head", "neck03", "temporal")) and plane_side(co, cap_p0, cap_n) >= -1e-5
    CAP, _ = garment(rig, body, prefix + ".cap", cap_region, [(cap_p0, -cap_n)], cap_off, cap_m, thick=0.002, folds=cap_folds)
    to_head_only(CAP)
    bm = bmesh.new(); bm.from_mesh(CAP.data); bm.verts.ensure_lookup_table()
    bnd = {v.index for v in bm.verts if v.is_boundary}
    ring = set(bnd)
    for v in bm.verts:
        if v.index in bnd:
            for e in v.link_edges: ring.add(e.other_vert(v).index)
    bm.free()
    vb = CAP.vertex_groups.new(name="band"); vb.add(list(ring), 1.0, 'REPLACE')
    bd = CAP.modifiers.new("band", 'DISPLACE'); bd.strength = -(cap_off - 0.006); bd.mid_level = 0.0; bd.direction = 'NORMAL'; bd.vertex_group = "band"
    CAP.modifiers.move(CAP.modifiers.find("band"), CAP.modifiers.find("smooth"))
    CAP.modifiers["folds"].vertex_group = "band"; CAP.modifiers["folds"].invert_vertex_group = True
    return CAP, MASK, (cap_p0, cap_n), nose

def trim_hair(hair, rig_world_inv, p0, n, margin=0.010):
    """delete hair cards above the cap plane so no hair pokes through the cap; the hairline below stays visible"""
    bm = bmesh.new(); bm.from_mesh(hair.data)
    kill = [v for v in bm.verts if plane_side(v.co, p0, n) > -margin]
    bmesh.ops.delete(bm, geom=kill, context='VERTS'); bm.to_mesh(hair.data); bm.free()

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

def suit_material(name, rig, jacket, shirt, tie):
    """jacket / white shirt V / tie mixed in the shader by the garment's REST coordinates (smooth edges that move with the cloth)"""
    neck = bl(rig, "neck01"); st = bl(rig, "spine03")
    z0 = st.z + 0.02; z1 = neck.z; ycut = neck.y - 0.03
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    def bsdf(col, rough, sheen=0.1):
        p = N.new("ShaderNodeBsdfPrincipled"); p.inputs["Base Color"].default_value = (*col, 1); p.inputs["Roughness"].default_value = rough
        p.inputs["Sheen Weight"].default_value = sheen; return p
    pj, ps, pt = bsdf(jacket, 0.6, 0.2), bsdf(shirt, 0.55), bsdf(tie, 0.4)
    at = N.new("ShaderNodeAttribute"); at.attribute_name = "rest_co"
    sp = N.new("ShaderNodeSeparateXYZ"); L.new(at.outputs["Vector"], sp.inputs[0])
    def math(op, a, b=None, clamp=False):
        n = N.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: L.new(v, n.inputs[i])
        return n.outputs[0]
    X, Y, Z = sp.outputs[0], sp.outputs[1], sp.outputs[2]
    t = math('MULTIPLY', math('SUBTRACT', Z, z0), 1.0 / max(0.01, z1 - z0), clamp=True)
    half = math('ADD', math('MULTIPLY', math('POWER', t, 1.2), 0.075), 0.014)
    ax = math('ABSOLUTE', X)
    front = math('LESS_THAN', Y, ycut); above = math('GREATER_THAN', Z, z0)
    shirt = math('MULTIPLY', math('MULTIPLY', math('LESS_THAN', ax, half), front), above)
    tie = math('MULTIPLY', math('MULTIPLY', math('LESS_THAN', ax, 0.011), shirt), math('LESS_THAN', Z, z1 - 0.025))
    # lapels: a darker satin band along the V; two buttons below it
    lap = math('MULTIPLY', math('MULTIPLY', math('LESS_THAN', ax, math('ADD', half, 0.032)), front), math('GREATER_THAN', Z, z0 - 0.02))
    pl = bsdf(tuple(c * 0.55 for c in jacket), 0.35, 0.4)
    def btn(zc):
        dx = math('POWER', X, 2.0); dz = math('POWER', math('SUBTRACT', Z, zc), 2.0)
        return math('MULTIPLY', math('LESS_THAN', math('ADD', dx, dz), 0.009 ** 2), front)
    bt = math('MAXIMUM', btn(z0 - 0.06), btn(z0 - 0.15))
    pb_ = bsdf((0.02, 0.02, 0.02), 0.3)
    m0 = N.new("ShaderNodeMixShader"); L.new(lap, m0.inputs[0]); L.new(pj.outputs[0], m0.inputs[1]); L.new(pl.outputs[0], m0.inputs[2])
    m0b = N.new("ShaderNodeMixShader"); L.new(bt, m0b.inputs[0]); L.new(m0.outputs[0], m0b.inputs[1]); L.new(pb_.outputs[0], m0b.inputs[2])
    m1 = N.new("ShaderNodeMixShader"); L.new(shirt, m1.inputs[0]); L.new(m0b.outputs[0], m1.inputs[1]); L.new(ps.outputs[0], m1.inputs[2])
    m2 = N.new("ShaderNodeMixShader"); L.new(tie, m2.inputs[0]); L.new(m1.outputs[0], m2.inputs[1]); L.new(pt.outputs[0], m2.inputs[2])
    L.new(m2.outputs[0], out.inputs["Surface"])
    return m
