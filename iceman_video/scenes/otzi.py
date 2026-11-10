"""Ötzi alive: a weathered 45-year-old Copper Age man with strand-based hair and beard, a striped
goat-hide coat, hide leggings and shoes, and a bearskin cap - all generated from code on top of
the MakeHuman body."""
import math
import numpy as np
import bpy, bmesh
from mathutils import Vector
from human import Human, MH

RNG = np.random.default_rng(1991)


# ----------------------------------------------------------------------------- strand hair
def _face_samples(verts, faces, n, rng):
    """Area-weighted random points (and normals) on a set of quads/tris."""
    a, b, c, d = (verts[faces[:, i]] for i in range(4))
    tris = np.concatenate([np.stack([a, b, c], 1), np.stack([a, c, d], 1)])
    area = np.linalg.norm(np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]), axis=1) * 0.5
    keep = area > 1e-10; tris = tris[keep]; area = area[keep]
    idx = rng.choice(len(tris), n, p=area / area.sum())
    u = rng.random(n); v = rng.random(n); flip = u + v > 1; u[flip] = 1 - u[flip]; v[flip] = 1 - v[flip]
    t = tris[idx]
    p = t[:, 0] + (t[:, 1] - t[:, 0]) * u[:, None] + (t[:, 2] - t[:, 0]) * v[:, None]
    nrm = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    return p, nrm


def grow_strands(roots, normals, length, segs, gravity, lift, rng, collide=None, curl=0.12, wave=0.0,
                 clump=0.6, n_guides=250, jitter=0.25):
    """Simple procedural grooming: guide strands bend from the surface normal toward gravity; children
    follow the nearest guide (clumping), with per-strand waviness and noise. Returns (N, segs+1, 3)."""
    N = len(roots)
    gi = rng.choice(N, min(n_guides, N), replace=False)

    def make(r, nrm, L, rnd):
        pts = np.zeros((len(r), segs + 1, 3)); pts[:, 0] = r
        d = nrm * lift + rnd * jitter
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        step = (L / segs)[:, None]
        for k in range(segs):
            d = d + gravity[None, :] * (0.35 + 0.3 * k / segs) + rng.normal(0, curl, d.shape)
            d /= np.linalg.norm(d, axis=1, keepdims=True)
            pts[:, k + 1] = pts[:, k] + d * step
            if collide is not None:
                pts[:, k + 1] = collide(pts[:, k + 1])
        return pts

    L = length * rng.uniform(0.75, 1.15, N)
    guides = make(roots[gi], normals[gi], L[gi], rng.normal(0, 1, (len(gi), 3)))
    own = make(roots, normals, L, rng.normal(0, 1, (N, 3)))
    # clumping: blend each strand toward its nearest guide's shape (translated to its root)
    from scipy.spatial import cKDTree
    _, near = cKDTree(roots[gi]).query(roots)
    g = guides[near] - guides[near][:, :1] + roots[:, None]
    t = np.linspace(0, 1, segs + 1)[None, :, None]
    pts = own * (1 - clump * t) + g * (clump * t)
    if wave:
        ph = rng.uniform(0, 6.28, N)[:, None]
        side = np.cross(pts[:, -1] - pts[:, 0], [0, 0, 1]); side /= np.maximum(np.linalg.norm(side, axis=1, keepdims=True), 1e-6)
        pts += side[:, None] * (np.sin(t[..., 0] * 9 + ph) * wave * t[..., 0])[..., None]
    if collide is not None:
        for k in range(1, segs + 1):
            pts[:, k] = collide(pts[:, k])
    return pts


def curves_object(name, pts, r_root, r_tip, mat):
    N, P, _ = pts.shape
    c = bpy.data.hair_curves.new(name)
    c.add_curves([P] * N)
    c.attributes['position'].data.foreach_set('vector', pts.astype(np.float32).ravel())
    rad = c.attributes.new('radius', 'FLOAT', 'POINT')
    rr = np.linspace(r_root, r_tip, P)[None, :].repeat(N, 0)
    rad.data.foreach_set('value', rr.astype(np.float32).ravel())
    o = bpy.data.objects.new(name, c); bpy.context.collection.objects.link(o)
    c.materials.append(mat)
    return o


def hair_material(name, melanin=0.85, redness=0.45, rough=0.35, grey=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    h = N.new("ShaderNodeBsdfHairPrincipled"); h.parametrization = 'MELANIN'
    h.inputs['Melanin'].default_value = melanin; h.inputs['Melanin Redness'].default_value = redness
    h.inputs['Roughness'].default_value = rough; h.inputs['Radial Roughness'].default_value = 0.4
    h.inputs['Random Color'].default_value = 0.15; h.inputs['Random Roughness'].default_value = 0.2
    h.inputs['Coat'].default_value = 0.08
    if grey:
        h.inputs['Tint'].default_value = (1, 1, 1, 1)
    L.new(h.outputs[0], out.inputs['Surface'])
    return m


def ellipsoid_collider(center, radii, margin):
    c = np.asarray(center); r = np.asarray(radii) + margin

    def f(p):
        q = (p - c) / r
        d = np.linalg.norm(q, axis=1)
        inside = d < 1.0
        q[inside] /= d[inside, None]
        return np.where(inside[:, None], c + q * r, p)
    return f


# ----------------------------------------------------------------------------- garments cut from the body
def garment(h, name, region_mask_v, offset, mat, lumps=0.006, solid=0.003, subsurf=1):
    """Duplicate the rigged body, keep faces in the region, push out along normals (before the armature)."""
    o = h.body.copy(); o.data = h.body.data.copy(); o.name = f"{h.name}_{name}"
    bpy.context.collection.objects.link(o)
    o.data.materials.clear(); o.data.materials.append(mat)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    kill = [f for f in bm.faces if not all(region_mask_v[v.index] for v in f.verts)]
    bmesh.ops.delete(bm, geom=kill, context='FACES_ONLY')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(o.data); bm.free()
    for m in list(o.modifiers):
        if m.type != 'ARMATURE':
            o.modifiers.remove(m)
    d = o.modifiers.new("Offset", 'DISPLACE'); d.strength = offset; d.mid_level = 0.0; d.direction = 'NORMAL'
    tex = bpy.data.textures.new(name + "_lump", 'CLOUDS'); tex.noise_scale = 0.09
    d2 = o.modifiers.new("Lumps", 'DISPLACE'); d2.texture = tex; d2.strength = lumps; d2.texture_coords = 'LOCAL'
    while o.modifiers[0].type == 'ARMATURE':
        bpy.ops.object.select_all(action='DESELECT')
        o.modifiers.move(0, len(o.modifiers) - 1)
    s = o.modifiers.new("Solid", 'SOLIDIFY'); s.thickness = solid; s.offset = -1
    if subsurf:
        ss = o.modifiers.new("Sub", 'SUBSURF'); ss.levels = subsurf; ss.render_levels = subsurf
    h.parts.append(o)
    return o


def hide_material(name, stripes=True, light=(0.13, 0.085, 0.05), dark=(0.028, 0.02, 0.014), fur=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Object'], sep.inputs[0])
    at = N.new("ShaderNodeMath"); at.operation = 'ARCTAN2'; L.new(sep.outputs['X'], at.inputs[0]); L.new(sep.outputs['Y'], at.inputs[1])
    wn = N.new("ShaderNodeTexNoise"); wn.inputs['Scale'].default_value = 5; wn.inputs['Detail'].default_value = 4
    L.new(tc.outputs['Object'], wn.inputs['Vector'])
    ph = N.new("ShaderNodeMath"); ph.operation = 'MULTIPLY_ADD'; ph.inputs[1].default_value = 7.0
    L.new(at.outputs[0], ph.inputs[0]); L.new(wn.outputs['Fac'], ph.inputs[2])
    sn = N.new("ShaderNodeMath"); sn.operation = 'SINE'; L.new(ph.outputs[0], sn.inputs[0])
    st = N.new("ShaderNodeMapRange"); st.inputs['From Min'].default_value = -0.15; st.inputs['From Max'].default_value = 0.15
    L.new(sn.outputs[0], st.inputs['Value'])
    col = N.new("ShaderNodeMix"); col.data_type = 'RGBA'
    if stripes:
        L.new(st.outputs[0], col.inputs['Factor'])
    else:
        col.inputs['Factor'].default_value = 0.35
    col.inputs[6].default_value = (*dark, 1); col.inputs[7].default_value = (*light, 1)
    # dirt / wear
    dn = N.new("ShaderNodeTexNoise"); dn.inputs['Scale'].default_value = 14; dn.inputs['Detail'].default_value = 8
    L.new(tc.outputs['Object'], dn.inputs['Vector'])
    dm = N.new("ShaderNodeMix"); dm.data_type = 'RGBA'; dm.blend_type = 'MULTIPLY'; dm.inputs['Factor'].default_value = 0.6
    L.new(col.outputs[2], dm.inputs[6]); L.new(dn.outputs['Color'], dm.inputs[7])
    L.new(dm.outputs[2], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.85
    p.inputs['Sheen Weight'].default_value = fur; p.inputs['Sheen Roughness'].default_value = 0.6
    # leather creases + hair-on texture
    wr = N.new("ShaderNodeTexWave"); wr.inputs['Scale'].default_value = 28; wr.inputs['Distortion'].default_value = 24
    wr.inputs['Detail'].default_value = 6; L.new(tc.outputs['Object'], wr.inputs['Vector'])
    fz = N.new("ShaderNodeTexNoise"); fz.inputs['Scale'].default_value = 700; fz.inputs['Detail'].default_value = 2
    L.new(tc.outputs['Object'], fz.inputs['Vector'])
    hm = N.new("ShaderNodeMath"); hm.operation = 'MULTIPLY_ADD'; hm.inputs[1].default_value = 0.5
    L.new(fz.outputs['Fac'], hm.inputs[0]); L.new(wr.outputs['Fac'], hm.inputs[2])
    bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.45; bp.inputs['Distance'].default_value = 0.002
    L.new(hm.outputs[0], bp.inputs['Height']); L.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m


# ----------------------------------------------------------------------------- the character
def build_otzi(name="Otzi", hair_density=1.0, coat_fur=True):
    h = Human(name, gender=1.0, years=45, muscle=0.62, weight=0.42, height=0.3,
              skin="middleage_lightskinned_male_diffuse.png", skin_tint=(0.80, 0.62, 0.50),
              eyebrows="eyebrow010", eyelashes="eyelashes02",
              extra={"targets/head/head-age-incr": 0.5, "targets/cheek/l-cheek-bones-incr": 0.4,
                     "targets/cheek/r-cheek-bones-incr": 0.4, "targets/nose/nose-hump-incr": 0.4,
                     "targets/chin/chin-prominent-incr": 0.3})
    # weathered skin: more roughness variation, stronger pores
    pb = h.skin_mat.node_tree.nodes["Principled BSDF"]
    pb.inputs['Subsurface Weight'].default_value = 0.3
    bmp = h.skin_mat.node_tree.nodes[h.skin_mat["bump_node"]]; bmp.inputs['Strength'].default_value = 0.4
    for o in h.parts:
        if o.name.endswith("brows"):
            for m in o.data.materials:
                mix = [n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeMix"][0]
                mix.inputs[7].default_value = (0.08, 0.05, 0.035, 1)

    V = np.array([v.co[:] for v in h.body.data.vertices])        # rest-pose positions (Blender space)
    F = np.array([list(p.vertices) + ([p.vertices[-1]] if len(p.vertices) == 3 else []) for p in h.body.data.polygons])
    bones = h.rig.bones
    def wsum(names):
        idx = [bones.index(b) for b in names if b in bones]
        return h.W[:, idx].sum(1)
    w_head = wsum(["head"] + [b for b in bones if any(k in b for k in ("jaw", "eye", "lid", "brow", "cheek", "nose", "lip", "ear", "temporalis", "oris", "levator", "risorius", "tongue", "special"))])
    eye_c = (np.array(h.eyes[0].matrix_world.to_translation()) + np.array(h.eyes[1].matrix_world.to_translation())) / 2
    head_c = eye_c + np.array([0, 0.035, 0.005])
    d = V - head_c; dn = d / np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)
    is_head = w_head > 0.55
    # scalp: top and back of the head, not the face, not the ears
    scalp = is_head & ((dn[:, 2] > 0.22) | ((dn[:, 1] > 0.25) & (dn[:, 2] > -0.55))) & ~((np.abs(dn[:, 0]) > 0.82) & (dn[:, 2] < 0.3))
    scalp &= ~((dn[:, 1] < -0.55) & (dn[:, 2] < 0.62))
    # beard: jaw, chin, cheeks below the cheekbones, upper lip; avoid the lips themselves
    mouth_c = eye_c + np.array([0, -0.025, -0.075])
    dm_ = np.linalg.norm((V - mouth_c) * np.array([1.0, 1.6, 2.2]), axis=1)
    beard = is_head & (V[:, 2] < eye_c[2] - 0.035) & (dn[:, 1] < 0.35) & (dm_ > 0.028)
    beard |= (w_head > 0.2) & (V[:, 2] < eye_c[2] - 0.11) & (V[:, 2] > eye_c[2] - 0.2) & (V[:, 1] < head_c[1] + 0.02)  # under the jaw
    head_rad = (0.082, 0.098, 0.115)
    col_head = ellipsoid_collider(head_c, head_rad, 0.006)

    def faces_of(mask):
        return F[mask[F].all(1)]

    # head hair: shoulder length, dark brown, slightly wavy
    # roots at the sides and back, below the cap line; the face stays clear (hair combed back and down)
    hair_roots = scalp & (dn[:, 2] < 0.48) & (dn[:, 1] > -0.18)
    n_hair = int(22000 * hair_density)
    r, nr = _face_samples(V, faces_of(hair_roots), n_hair, RNG)
    nr = nr * 0.5 + np.array([0, 0.45, -0.25])
    hp = grow_strands(r, nr, 0.25, 16, np.array([0, 0.30, -1.0]), 0.6, RNG,
                      collide=ellipsoid_collider(head_c, (0.088, 0.11, 0.12), 0.008), curl=0.07, wave=0.008, clump=0.72)
    hair = curves_object(name + "_hair", hp, 0.00005, 0.00002, hair_material(name + "_hairmat", 0.88, 0.5, 0.32))
    # beard + moustache
    n_b = int(16000 * hair_density)
    r, nr = _face_samples(V, faces_of(beard), n_b, RNG)
    bpz = grow_strands(r, nr, 0.075, 9, np.array([0, -0.15, -1.0]), 0.75, RNG, collide=ellipsoid_collider(head_c, head_rad, 0.003),
                       curl=0.16, wave=0.004, clump=0.5, n_guides=400)
    beard_o = curves_object(name + "_beard", bpz, 0.00006, 0.00002, hair_material(name + "_beardmat", 0.85, 0.55, 0.38))
    for o in (hair, beard_o):
        mw = o.matrix_world.copy(); o.parent = h.arm; o.parent_type = 'BONE'; o.parent_bone = "head"
        bpy.context.view_layer.update(); o.matrix_world = mw
        h.parts.append(o)

    # garments
    torso_b = ["spine01", "spine02", "spine03", "spine04", "spine05", "clavicle.L", "clavicle.R", "shoulder01.L", "shoulder01.R",
               "upperarm01.L", "upperarm01.R", "upperarm02.L", "upperarm02.R", "lowerarm01.L", "lowerarm01.R", "root",
               "pelvis.L", "pelvis.R", "breast.L", "breast.R", "neck01"]
    coat_v = (wsum(torso_b) > 0.5) | ((wsum(["upperleg01.L", "upperleg01.R"]) > 0.5) & (V[:, 2] > 0.62))
    coat_v &= ~(wsum(["head", "neck02", "neck03"]) > 0.3)
    coat = garment(h, "coat", coat_v, 0.024, hide_material(name + "_hide", True), lumps=0.016)
    legs_v = wsum(["upperleg01.L", "upperleg01.R", "upperleg02.L", "upperleg02.R", "lowerleg01.L", "lowerleg01.R",
                   "lowerleg02.L", "lowerleg02.R"]) > 0.5
    garment(h, "leggings", legs_v, 0.007, hide_material(name + "_legs", False, (0.22, 0.15, 0.09), (0.09, 0.06, 0.04), 0.3), lumps=0.004)
    feet_v = wsum([b for b in bones if b.startswith("foot") or b.startswith("toe")]) > 0.45
    garment(h, "shoes", feet_v, 0.012, hide_material(name + "_shoe", False, (0.12, 0.08, 0.05), (0.05, 0.035, 0.02), 0.1), lumps=0.006)
    # bearskin cap: top of the scalp, pushed out, with short dense fur
    cap_v = scalp & (dn[:, 2] > 0.30)
    cap = garment(h, "cap", cap_v, 0.022, hide_material(name + "_capm", False, (0.06, 0.04, 0.03), (0.03, 0.02, 0.015), 0.8), lumps=0.004)
    r, nr = _face_samples(V, faces_of(cap_v), int(14000 * hair_density), RNG)
    r = r + nr * 0.024
    fur = grow_strands(r, nr, 0.035, 6, np.array([0, 0.3, -1.0]), 0.9, RNG, curl=0.2, clump=0.4, n_guides=300)
    fo = curves_object(name + "_capfur", fur, 0.00012, 0.00004, hair_material(name + "_furm", 0.95, 0.4, 0.5))
    mw = fo.matrix_world.copy(); fo.parent = h.arm; fo.parent_type = 'BONE'; fo.parent_bone = "head"
    bpy.context.view_layer.update(); fo.matrix_world = mw; h.parts.append(fo)
    # fur cape over the shoulders and upper back (hair-on hide)
    sh_z = V[(wsum(["clavicle.L", "clavicle.R"]) > 0.5)][:, 2].mean()
    cape_v = coat_v & (V[:, 2] > sh_z - 0.20) & ~(wsum(["lowerarm01.L", "lowerarm01.R"]) > 0.3)
    cape_v &= (V[:, 1] > np.median(V[coat_v, 1]) - 0.02) | (V[:, 2] > sh_z + 0.02)   # shoulders and back, not the chest
    r, nr = _face_samples(V, faces_of(cape_v), int(30000 * hair_density), RNG)
    r = r + nr * 0.026
    cf = grow_strands(r, nr, 0.06, 6, np.array([0, 0.05, -1.0]), 0.5, RNG, curl=0.18, clump=0.55, n_guides=500)
    cape = curves_object(name + "_cape", cf, 0.00016, 0.00005, hair_material(name + "_capem", 0.7, 0.6, 0.5))
    # the fur is grown in rest pose: bind it to the torso so it follows the posed body
    mw = cape.matrix_world.copy(); cape.parent = h.arm; cape.parent_type = 'BONE'; cape.parent_bone = "spine02"
    bpy.context.view_layer.update(); cape.matrix_world = mw; h.parts.append(cape)
    h.hair_objs = [hair, beard_o, fo, cape]
    # covered skin is hidden (no poke-through)
    hide_v = coat_v | legs_v | feet_v
    bm = bmesh.new(); bm.from_mesh(h.body.data); bm.verts.ensure_lookup_table()
    inner = [f for f in bm.faces if all(hide_v[v.index] for v in f.verts) and
             sum(1 for v in f.verts if not coat_v[v.index] or V[v.index, 2] < 0.62) >= 0]
    # keep a margin of skin under garment edges: only remove faces whose neighbours are all covered too
    bmesh.ops.delete(bm, geom=[f for f in inner if all(all(hide_v[v.index] for v in nf.verts) for e in f.edges for nf in e.link_faces)], context='FACES_ONLY')
    bm.to_mesh(h.body.data); bm.free()
    return h
