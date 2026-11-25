"""ShoeBomber v011 shared helpers (base copied from SurgeonBrandsLivers v015 lib.py) (exec'd by 01_build.py / 02_animate.py).
Materials, MPFB humans, R1 one-piece garments (body copy, bisected, offset, solidify), hide-under masks, eye fix,
simple modelling helpers. Patterns follow the client-approved EarInArm v015 / MonkeyHead v015 builds."""
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

def rest_relax(g, body, offset, iters, hem_z=None, collar_above=None, flatten_chest=None):
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
    if flatten_chest is not None:
        z0, z1 = flatten_chest
        band = [i for i in range(n) if z0 < co[i].z < z1 and abs(co[i].x) < 0.15 and co[i].y < 0]
        if band:
            ymin = min(co[i].y for i in band)
            plane = ymin + 0.035
            for i in band:
                w = min(1.0, (co[i].z - z0) / 0.04, (z1 - co[i].z) / 0.04, (0.15 - abs(co[i].x)) / 0.04)
                if co[i].y < plane: co[i].y = co[i].y + (plane - co[i].y) * max(0.0, w)
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
        n = len(loop)
        for it in range(6):
            new = [(loop[i - 1].co + loop[i].co * 2 + loop[(i + 1) % n].co) / 4 for i in range(n)]
            for v, c in zip(loop, new): v.co = c
        bm.normal_update()
        rings = []
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

def garment(rig, body, name, region, cuts, offset, material, thick=0.003, folds=0.0, fold_scale=0.07, subd=True, relax=0, hem_z=None, flatten_chest=None):
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
        rest_relax(g, body, offset, relax, hem_z=hem_z, collar_above=(hem_z if hem_z is not None else None), flatten_chest=flatten_chest)
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
             neck_tilt=-0.35, hide=True, top_only=False, bot_off_leg=None, vneck=0.0, relax=50, flat=False):
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
    top, cov_t = garment(rig, body, prefix + ".top", top_region, cuts_top, top_off, top_m, folds=top_folds, fold_scale=0.12, relax=relax * 2, hem_z=hip - 0.02, flatten_chest=((bl(rig, "spine03").z + 0.02, neck.z - 0.07) if flat else None))
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

def hide_by_proximity(body, garment, name, dist=0.022, rings=3):
    """body skin under a garment that has no MakeHuman delete group: masked (rest pose, eroded so hems keep skin)"""
    from mathutils.bvhtree import BVHTree
    gv = [v.co.copy() for v in garment.data.vertices]
    bvh = BVHTree.FromPolygons(gv, [tuple(p.vertices) for p in garment.data.polygons])
    gm_inv = garment.matrix_world.inverted() @ body.matrix_world
    cov = set()
    for v in body.data.vertices:
        loc, nrm, _, d = bvh.find_nearest(gm_inv @ v.co)
        if loc is not None and d < dist: cov.add(v.index)
    me = body.data; nb = {i: set() for i in range(len(me.vertices))}
    for e in me.edges:
        a_, b_ = e.vertices; nb[a_].add(b_); nb[b_].add(a_)
    for _ in range(rings):
        cov = {i for i in cov if all(n in cov for n in nb[i])}
    vg = body.vertex_groups.new(name=name); vg.add(list(cov), 1.0, 'REPLACE')
    mk = body.modifiers.new(name, 'MASK'); mk.vertex_group = name; mk.invert_vertex_group = True
    while body.modifiers.find(name) > body.modifiers.find("Armature") + 1:
        i = body.modifiers.find(name); body.modifiers.move(i, i - 1)
    return mk


# ===== animation helpers (from LegoInNose v013 lib_v013.py)
O = bpy.data.objects
def upd(): bpy.context.view_layer.update()
def fs(f): sc.frame_set(int(f))
def W(rig, bone): return rig.matrix_world @ rig.pose.bones[bone].matrix
def Wh(rig, bone): return rig.matrix_world @ rig.pose.bones[bone].head
def Wt(rig, bone): return rig.matrix_world @ rig.pose.bones[bone].tail

def set_interp(obj_or_data, kind='CONSTANT', path_contains=None):
    ad = obj_or_data.animation_data
    if not ad or not ad.action: return
    for fc in iter_fcurves(ad.action):
        if path_contains and path_contains not in fc.data_path: continue
        for kp in fc.keyframe_points: kp.interpolation = kind

def frame_from(y_dir, z_hint, origin):
    y = Vector(y_dir).normalized(); z = Vector(z_hint); z = (z - y * z.dot(y)).normalized(); x = y.cross(z)
    M = Matrix((x, y, z)).transposed().to_4x4(); M.translation = Vector(origin); return M

def dom_bones(body, rig):
    names = {b.name for b in rig.data.bones}; i2n = {g.index: g.name for g in body.vertex_groups if g.name in names}
    out = {}
    for v in body.data.vertices:
        best = (0, None)
        for g in v.groups:
            n = i2n.get(g.group)
            if n and g.weight > best[0]: best = (g.weight, n)
        out[v.index] = best[1]
    return out

def eval_points(obj, filt=None):
    saved = []
    for m in obj.modifiers:
        if m.type in ('MASK', 'SUBSURF'): saved.append((m, m.show_viewport)); m.show_viewport = False
    upd(); dg = bpy.context.evaluated_depsgraph_get(); e = obj.evaluated_get(dg); me = e.to_mesh()
    pts = [(v.index, obj.matrix_world @ v.co, (obj.matrix_world.to_3x3() @ v.normal).normalized()) for v in me.vertices
           if filt is None or filt(v.index)]
    e.to_mesh_clear()
    for m, sv in saved: m.show_viewport = sv
    upd()
    return pts

def world_bvh(obj):
    upd(); dg = bpy.context.evaluated_depsgraph_get(); e = obj.evaluated_get(dg); me = e.to_mesh()
    Mw = obj.matrix_world
    b = BVHTree.FromPolygons([Mw @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons]); e.to_mesh_clear(); return b

def ray_down(objs, x, y, z0=3.0):
    best = None
    for o in objs:
        b = world_bvh(o); hit = b.ray_cast(Vector((x, y, z0)), Vector((0, 0, -1)), 10.0)
        if hit[0] is not None and (best is None or hit[0].z > best): best = hit[0].z
    return best

def smoothstep(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

# ------------------------------------------------------------------ FK helpers (from EarInArm v015)
def aim_bone(rig, name, direction, f=1):
    upd(); pb = rig.pose.bones[name]; cur = pb.matrix.copy()
    y = cur.col[1].to_3d().normalized(); q = y.rotation_difference(Vector(direction).normalized())
    R = q.to_matrix() @ cur.to_3x3().normalized()
    M = R.to_4x4(); M.translation = cur.translation; pb.matrix = M; upd()
    pb.keyframe_insert("rotation_quaternion", frame=f, group=name)

# ------------------------------------------------------------------ props owned by hands / heads (Child Of switching, R4)
def key_basis(obj, f, M):
    loc, q, s = M.decompose(); obj.rotation_mode = 'QUATERNION'
    if obj.rotation_quaternion.dot(q) < 0: q = -q
    obj.location = loc; obj.rotation_quaternion = q; obj.scale = s
    for k in ("location", "rotation_quaternion", "scale"): obj.keyframe_insert(k, frame=f)
    ad = obj.animation_data
    if ad and ad.action:
        for fc in iter_fcurves(ad.action):
            for kp in fc.keyframe_points:
                if abs(kp.co.x - f) < 0.5 and not fc.data_path.startswith("constraints"): kp.interpolation = 'LINEAR'


def bone_world(target, sub):
    return target.matrix_world @ target.pose.bones[sub].matrix if sub else target.matrix_world.copy()

OWN = {}
def owner_switch(obj, f, target=None, sub=None, log=print):
    """from frame f the prop is owned by `target`(.sub) via Child Of, or by nobody (static); world kept continuous"""
    fs(f - 1); Wprev = obj.matrix_world.copy()
    obj.rotation_mode = 'QUATERNION'
    for k_ in ("location", "rotation_quaternion", "scale"): obj.keyframe_insert(k_, frame=f - 1)
    for c in obj.constraints:
        if c.type != 'CHILD_OF': continue
        c.keyframe_insert("influence", frame=f - 1); c.influence = 0.0; c.keyframe_insert("influence", frame=f)
    if target is None:
        key_basis(obj, f, Wprev)
        set_interp(obj, 'LINEAR')
    else:
        c = obj.constraints.new('CHILD_OF'); c.name = "own_%d" % f; c.target = target
        if sub: c.subtarget = sub
        c.influence = 0.0; c.keyframe_insert("influence", frame=0); c.keyframe_insert("influence", frame=f - 1)
        c.influence = 1.0; c.keyframe_insert("influence", frame=f)
        fs(f)
        c.inverse_matrix = bone_world(target, sub).inverted() @ Wprev
        key_basis(obj, f, Matrix.Identity(4))
    set_interp(obj, 'LINEAR')
    fs(f); log("owner", obj.name, f, target.name if target else None, sub, "jump_mm", round((obj.matrix_world.translation - Wprev.translation).length * 1000, 2))
    OWN.setdefault(obj.name, []).append((f, target.name if target else None, sub))

def active_child(obj):
    for c in obj.constraints:
        if c.type == 'CHILD_OF' and c.influence > 0.5: return c
    return None

def key_world_while_owned(obj, f, Mworld):
    """key the basis so the prop sits at world matrix Mworld at frame f under its active owner"""
    fs(f); c = active_child(obj)
    if c is None: key_basis(obj, f, Mworld); return
    P = bone_world(c.target, c.subtarget) @ c.inverse_matrix
    key_basis(obj, f, P.inverted() @ Mworld)

def vis(obj, f, show):
    obj.hide_render = not show; obj.hide_viewport = not show
    obj.keyframe_insert("hide_render", frame=f); obj.keyframe_insert("hide_viewport", frame=f)
    set_interp(obj, 'CONSTANT', "hide")

def quat_continuity(obj):
    if not obj.animation_data or not obj.animation_data.action: return 0
    groups = {}
    for fc in iter_fcurves(obj.animation_data.action):
        if fc.data_path.endswith("rotation_quaternion"): groups.setdefault(fc.data_path, {})[fc.array_index] = fc
    nfix = 0
    for dp, ch in groups.items():
        if len(ch) != 4: continue
        frames = sorted({kp.co.x for kp in ch[0].keyframe_points})
        idx = [{round(kp.co.x, 3): kp for kp in ch[i].keyframe_points} for i in range(4)]
        prev = None
        for fr in frames:
            kps = [idx[i].get(round(fr, 3)) for i in range(4)]
            if any(k is None for k in kps): continue
            q = Quaternion([k.co.y for k in kps])
            if prev is not None and prev.dot(q) < 0:
                for k in kps:
                    k.co.y = -k.co.y; k.handle_left.y = -k.handle_left.y; k.handle_right.y = -k.handle_right.y
                q = -q; nfix += 1
            prev = q
        for c in ch.values(): c.update()
    return nfix

# ===== ShoeBomber v011: solid bodies under real garments
def solid_under(body, garments, name="under_cloth", dist=0.03, depth=0.013, rings=3):
    """Client lesson: bodies stay SOLID under clothes (no deleted skin, nothing hollow at the openings).
    Skin covered by a garment is kept and only pulled in by `depth` along its normal (weighted, fading to 0
    at the garment edges), so it never pokes through the cloth but fills every sleeve, collar and crotch."""
    from mathutils.bvhtree import BVHTree
    w = {}
    for g in garments:
        gv = [v.co.copy() for v in g.data.vertices]
        bvh = BVHTree.FromPolygons(gv, [tuple(p.vertices) for p in g.data.polygons])
        gm_inv = g.matrix_world.inverted() @ body.matrix_world
        for v in body.data.vertices:
            loc, nrm, _, d = bvh.find_nearest(gm_inv @ v.co)
            if loc is not None and d < dist: w[v.index] = 1.0
    me = body.data; nb = {i: set() for i in range(len(me.vertices))}
    for e in me.edges:
        a_, b_ = e.vertices; nb[a_].add(b_); nb[b_].add(a_)
    core = set(w)
    layers = []
    for _ in range(rings):
        core = {i for i in core if all(n in core for n in nb[i])}; layers.append(core)
    vg = body.vertex_groups.get(name) or body.vertex_groups.new(name=name)
    for i in w: vg.add([i], 0.35, 'REPLACE')
    for k, L in enumerate(layers):
        vg.add(list(L), 0.35 + 0.65 * (k + 1) / rings, 'REPLACE')
    d = body.modifiers.new(name, 'DISPLACE'); d.vertex_group = name; d.strength = -depth; d.mid_level = 0.0; d.direction = 'NORMAL'
    while body.modifiers.find(name) > body.modifiers.find("Armature") + 1:
        i = body.modifiers.find(name); body.modifiers.move(i, i - 1)
    return d

def socks(rig, body, col, prefix):
    """skin-tight socks are correct for socks: the foot region copy, slightly offset"""
    m = fabric("M_Sock" + prefix, col, scale=500, bump=0.2)
    ank = bl(rig, "foot.L").z + 0.11
    def reg(co, bn, ank=ank): return in_region(bn, ("foot", "toe", "lowerleg")) and co.z <= ank
    sk, cov = garment(rig, body, rig.name + ".socks", reg, [((0, 0, ank), (0, 0, 1))], 0.0025, m, thick=0.0015, folds=0.0)
    return sk

def flatten_chest(rig, body, keep=0.0):
    """male chest pushed back to the sternum plane BEFORE dressing (05/06 lesson)"""
    me = body.data
    gi = {body.vertex_groups[n].index for n in ("breast.L", "breast.R") if n in body.vertex_groups}
    mids = [v for v in me.vertices if abs(v.co.x) < 0.012 and 1.12 < v.co.z < 1.42 and v.co.y < 0.0 and v.normal.y < -0.5]
    def ster(z):
        near = sorted(mids, key=lambda v: abs(v.co.z - z))[:4]
        return sum(v.co.y for v in near) / max(1, len(near))
    for v in me.vertices:
        wv = max([g.weight for g in v.groups if g.group in gi] or [0.0])
        if wv <= 0.02 or v.co.y > 0.02: continue
        lim = ster(v.co.z) + 0.10 * v.co.x * v.co.x / 0.04 * 0.25
        if v.co.y < lim:
            u = min(1.0, wv * 2.5); v.co.y = v.co.y + (lim + (v.co.y - lim) * keep - v.co.y) * u
    me.update()

def flatten_crotch(rig, body):
    """crotch front smoothed to a plain curve before dressing (no bulge, no shape under the trousers)"""
    me = body.data; hip = bl(rig, "pelvis.L").z
    L = bl(rig, "upperleg01.L"); zc = L.z - 0.10
    pts = [v for v in me.vertices if abs(v.co.x) < 0.075 and zc - 0.09 < v.co.z < hip and v.co.y < 0.02]
    for v in pts:
        # plane through the lower belly, leaning back with depth
        ref = [u.co.y for u in me.vertices if 0.07 < abs(u.co.x) < 0.10 and abs(u.co.z - v.co.z) < 0.01 and u.co.y < 0.02]
        if not ref: continue
        lim = min(ref) + 0.004
        if v.co.y < lim: v.co.y = lim
    me.update()

# ===== glTF import (from PrisonKeyCake v011 lib_build.py)
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
