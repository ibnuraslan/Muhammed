"""Cladh Hallan in the Bronze Age (c. 1100 BC): three conjoined roundhouses on the machair, and an interior.

  village(smoke=True)        three thatched roundhouses (Sketchfab CC-BY reconstruction, nebulousflynn) set into the
                             sand at uist.HOUSES, roofs touching, doorways east, peat smoke seeping through the thatch
  interior(fire=1.0, door_sun=...)  inside the middle house: stone-revetted sunken wall, ring of posts, rafters and
                             thatch, a hearth fire, saddle quern, pots, baskets, sheepskins, a storage pit; returns dict
  Islander(...)              a Bronze Age man (wool tunic and cloak, long hair, beard) - only ever a silhouette / from behind
"""
import math, random
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
import uist as U
import dig as G
import ph, sf

ROUNDHOUSE = "0608ab8dcf3d4a9183c01e87eb1c4bcf"


def _mat(name, col, rough=0.8, emit=None, strength=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Roughness'].default_value = rough
    if emit:
        p.inputs['Emission Color'].default_value = (*emit, 1); p.inputs['Emission Strength'].default_value = strength
    return m


def smoke(base, height=14.0, drift=(0.45, 0.12), r0=0.35, grow=0.24, density=1.2, name="smoke"):
    """Peat smoke seeping from a thatched roof: a volumetric plume (world-space) that leans downwind, widens as it rises,
    breaks up into wisps and thins out. base = the smoke hole / roof apex."""
    bx, by, bz = base
    L_ = height; dx, dy = drift
    lo = Vector((bx - 2.5, by - 2.5 - 0.2 * L_, bz - 0.5)); hi = Vector((bx + dx * L_ + r0 + grow * L_ + 2, by + dy * L_ + r0 + grow * L_ + 2.5, bz + L_))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(lo + hi) / 2); o = bpy.context.active_object; o.name = name
    o.scale = hi - lo
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; Lk = m.node_tree.links; N.remove(N["Principled BSDF"])
    geo = N.new("ShaderNodeNewGeometry"); sp = N.new("ShaderNodeSeparateXYZ"); Lk.new(geo.outputs['Position'], sp.inputs[0])
    def math(op, a, b=None, v=None):
        n = N.new("ShaderNodeMath"); n.operation = op
        (Lk.new(a, n.inputs[0]) if not isinstance(a, (int, float)) else setattr(n.inputs[0], 'default_value', a))
        if b is not None:
            (Lk.new(b, n.inputs[1]) if not isinstance(b, (int, float)) else setattr(n.inputs[1], 'default_value', b))
        return n.outputs[0]
    dz = math('MAXIMUM', math('SUBTRACT', sp.outputs['Z'], bz), 0.0)
    ax = math('ADD', math('MULTIPLY', dz, dx), bx); ay = math('ADD', math('MULTIPLY', dz, dy), by)
    # wobble the axis with low-frequency noise (wind gusts)
    nzw = N.new("ShaderNodeTexNoise"); nzw.inputs['Scale'].default_value = 0.12; Lk.new(geo.outputs['Position'], nzw.inputs['Vector'])
    wob = math('MULTIPLY', math('SUBTRACT', nzw.outputs['Fac'], 0.5), math('MULTIPLY', dz, 0.35))
    ex = math('SUBTRACT', sp.outputs['X'], math('ADD', ax, wob)); ey = math('SUBTRACT', sp.outputs['Y'], ay)
    dist = math('SQRT', math('ADD', math('MULTIPLY', ex, ex), math('MULTIPLY', ey, ey)))
    rad = math('ADD', math('MULTIPLY', dz, grow), r0)
    q = math('DIVIDE', dist, rad)
    core = N.new("ShaderNodeMapRange"); core.interpolation_type = 'SMOOTHSTEP'
    core.inputs['From Min'].default_value = 1.0; core.inputs['From Max'].default_value = 0.15; Lk.new(q, core.inputs['Value'])
    fade = N.new("ShaderNodeMapRange"); fade.inputs['From Min'].default_value = L_; fade.inputs['From Max'].default_value = 0.0
    Lk.new(dz, fade.inputs['Value'])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 0.9; nz.inputs['Detail'].default_value = 7; nz.inputs['Roughness'].default_value = 0.6
    Lk.new(geo.outputs['Position'], nz.inputs['Vector'])
    wisp = N.new("ShaderNodeMapRange"); wisp.inputs['From Min'].default_value = 0.38; wisp.inputs['From Max'].default_value = 0.72
    Lk.new(nz.outputs['Fac'], wisp.inputs['Value'])
    # thinner as it spreads (mass conserved-ish)
    thin = math('DIVIDE', 1.0, math('ADD', math('MULTIPLY', dz, 0.35), 1.0))
    d = math('MULTIPLY', math('MULTIPLY', math('MULTIPLY', core.outputs[0], fade.outputs[0]), wisp.outputs[0]), thin)
    d = math('MULTIPLY', d, density)
    v = N.new("ShaderNodeVolumePrincipled"); v.inputs['Color'].default_value = (0.78, 0.76, 0.74, 1); v.inputs['Anisotropy'].default_value = 0.5
    Lk.new(d, v.inputs['Density']); Lk.new(v.outputs[0], N["Material Output"].inputs['Volume'])
    o.data.materials.append(m)
    return o


def _strip_ground(ms, centre=(0.13, 1.98), r_keep=4.6, z_cut=0.05):
    """The reconstruction scan carries its own patch of turf: delete scan faces low down outside the house."""
    for o in ms:
        if o.name.startswith("Object_2"):          # an untextured fill plane
            bpy.data.objects.remove(o); continue
        bm = bmesh.new(); bm.from_mesh(o.data)
        M = o.matrix_world
        kill = []
        for f in bm.faces:
            c = M @ f.calc_center_median()
            r = math.hypot(c.x - centre[0], c.y - centre[1])
            if (r > r_keep and c.z < z_cut + (r - r_keep) * 0.0) or (r > r_keep + 0.6) or c.z < 0.25:
                kill.append(f)
        bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(o.data); bm.free()


DOOR_ROT = 35.0
WALL_H = 0.95             # drystone wall base under the thatch           # rotation that turns the reconstruction's doorway to face east (+x)


def roof_weights(apex, r_eave, z_eave, n=14, seed=0, meshes=()):
    """Heather ropes draped over the thatch (each point dropped onto the roof by ray cast), weighted at the eave with a
    slung stone (Hebridean thatch)."""
    from mathutils.bvhtree import BVHTree
    rng = random.Random(seed)
    rope = _mat("heatherrope", (0.16, 0.12, 0.08), 0.9)
    dg = bpy.context.evaluated_depsgraph_get()
    trees = [BVHTree.FromObject(m, dg) for m in meshes]
    # BVHTree.FromObject is in object space: carry matrices
    mats = [m.matrix_world.copy() for m in meshes]
    def drop(x, y):
        best = None
        for t, M in zip(trees, mats):
            Mi = M.inverted()
            o = Mi @ Vector((x, y, apex.z + 3)); d = (Mi.to_3x3() @ Vector((0, 0, -1))).normalized()
            hit = t.ray_cast(o, d)
            if hit[0] is not None:
                w = M @ hit[0]; nw = (M.to_3x3() @ hit[1]).normalized()
                if best is None or w.z > best[0].z:
                    best = (w, nw)
        return best
    for k in range(n):
        a = 2 * math.pi * k / n + rng.uniform(-0.05, 0.05)
        pts = []
        for j in range(15):
            t = 0.08 + 0.92 * j / 14
            x = apex.x + r_eave * t * math.cos(a); y = apex.y + r_eave * t * math.sin(a)
            h = drop(x, y)
            if h is None:
                break
            pts.append(h[0] + h[1] * 0.03)
        if len(pts) < 4:
            continue
        e = pts[-1]
        pts.append(e + Vector((math.cos(a), math.sin(a), 0)) * 0.08 + Vector((0, 0, -0.4)))
        cu = bpy.data.curves.new("roofrope", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.014
        sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            sp.points[i].co = (*p, 1)
        o = bpy.data.objects.new("roofrope", cu); bpy.context.scene.collection.objects.link(o); cu.materials.append(rope)
        G.stone(tuple(pts[-1] + Vector((0, 0, -0.08))), (0.22, 0.16, 0.18), rot_z=a, seed=rng.randrange(10), flat=0.85)


def drystone_wall(hx, hy, r, z0, h=WALL_H if False else 0.95, seed=0, door=1.15):
    """Low drystone wall ring under the eaves, flat stones in courses, an opening facing east with two upright jambs."""
    rng = random.Random(seed)
    courses = int(h / 0.16)
    for c in range(courses):
        n = int(2 * math.pi * r / 0.42)
        for k in range(n):
            a = 2 * math.pi * (k + 0.5 * (c % 2)) / n
            if abs(((math.degrees(a) + 180) % 360) - 180) < math.degrees(door / 2 / r) + 4:
                continue
            sz = rng.uniform(0.34, 0.52)
            px, py = hx + (r + rng.uniform(-0.04, 0.04)) * math.cos(a), hy + (r + rng.uniform(-0.04, 0.04)) * math.sin(a)
            G.stone((px, py, z0 + 0.07 + c * 0.155), (sz, sz * rng.uniform(0.55, 0.8), sz * 0.36), rot_z=a + math.pi / 2 + rng.uniform(-0.2, 0.2),
                    seed=rng.randrange(10), tilt=(rng.uniform(-0.08, 0.08), rng.uniform(-0.08, 0.08)))
    for sgn in (-1, 1):
        a = sgn * door / 2 / r
        G.stone((hx + r * math.cos(a), hy + r * math.sin(a), z0 + h / 2), (0.28, 0.2, h * 0.55), rot_z=a, seed=3 + sgn, flat=0.95)
    G.stone((hx + r + 0.5, hy, z0 + 0.02), (0.6, door * 0.8, 0.07), seed=5, flat=0.3)      # threshold slab


def trodden(hx, hy, r, z0, seed=0):
    """Trampled ground: a ring of bare earth round the house and a worn path east from the door (alpha decals)."""
    mud = bpy.data.materials.get("trodden")
    if mud is None:
        mud = ph.texture("dense_sand", scale=0.8, name="trodden", tint=(1.5, 1.3, 1.0))
        nt = mud.node_tree; N = nt.nodes; Lk = nt.links; p = [n for n in N if n.type == 'BSDF_PRINCIPLED'][0]
        tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(tc.outputs['UV'], sep.inputs[0])
        nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 6; nz.inputs['Detail'].default_value = 6; Lk.new(tc.outputs['Object'], nz.inputs['Vector'])
        gx = N.new("ShaderNodeMath"); gx.operation = 'PINGPONG'; gx.inputs[1].default_value = 0.5
        Lk.new(sep.outputs['Y'], gx.inputs[0])
        e = N.new("ShaderNodeMapRange"); e.inputs['From Min'].default_value = 0.0; e.inputs['From Max'].default_value = 0.3; Lk.new(gx.outputs[0], e.inputs['Value'])
        a_ = N.new("ShaderNodeMath"); a_.operation = 'MULTIPLY'; Lk.new(e.outputs[0], a_.inputs[0])
        nb = N.new("ShaderNodeMapRange"); nb.inputs['From Min'].default_value = 0.35; nb.inputs['From Max'].default_value = 0.6; Lk.new(nz.outputs['Fac'], nb.inputs['Value'])
        Lk.new(nb.outputs[0], a_.inputs[1]); Lk.new(a_.outputs[0], p.inputs['Alpha'])
    # ring
    bm = bmesh.new(); segs = 64; ri, ro = r + 0.1, r + 1.4
    vi = []; vo = []
    for k in range(segs + 1):
        a = 2 * math.pi * k / segs
        for rr, lst in ((ri, vi), (ro, vo)):
            x, y = hx + rr * math.cos(a), hy + rr * math.sin(a)
            lst.append(bm.verts.new((x, y, float(U.surface(x, y)) + 0.025)))
    uvs = []
    for k in range(segs):
        f = bm.faces.new((vi[k], vi[k + 1], vo[k + 1], vo[k])); uvs.append((f, k))
    uv = bm.loops.layers.uv.new("UVMap")
    for f, k in uvs:
        for l in f.loops:
            l[uv].uv = (k / segs, 0.0 if l.vert in vi else 1.0)
    me = bpy.data.meshes.new("trodden"); bm.to_mesh(me); bm.free(); me.materials.append(mud)
    o = bpy.data.objects.new("trodden", me); bpy.context.scene.collection.objects.link(o)
    # worn path east from the door
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap"); L_ = 7.0; w = 0.7; n = 20
    rows = []
    for k in range(n + 1):
        t = k / n; x = hx + r + 0.4 + t * L_; y = hy + 0.6 * math.sin(t * 3 + seed)
        rows.append([bm.verts.new((x, y + sgn * w, float(U.surface(x, y + sgn * w)) + 0.03)) for sgn in (-1, 1)])
    for k in range(n):
        f = bm.faces.new((rows[k][0], rows[k + 1][0], rows[k + 1][1], rows[k][1]))
        for l in f.loops:
            l[uvl].uv = (k / n, 0.0 if l.vert in (rows[k][0], rows[k + 1][0]) else 1.0)
    me = bpy.data.meshes.new("path"); bm.to_mesh(me); bm.free(); me.materials.append(mud)
    o = bpy.data.objects.new("path", me); bpy.context.scene.collection.objects.link(o)


def village(smoke_on=True, scale=1.75):
    out = []
    for i, (hx, hy, r) in enumerate(U.HOUSES):
        z = float(U.surface(hx, hy))
        root, ms = sf.model(ROUNDHOUSE, loc=(0, 0, 0), rot_z=0)
        _strip_ground(ms)
        # recentre the house on its own footprint, then place it (rotated so the doorway faces east)
        for c in root.children:
            c.location -= Vector((0.13, 1.98, 0))
        s = scale * r / 4.5
        root.scale = (s, s, s); root.location = (hx, hy, z + WALL_H - 0.35); root.rotation_euler = (0, 0, math.radians(DOOR_ROT + 8 * i))
        out.append(root)
        bpy.context.view_layer.update()
        msw = [m_ for m_ in root.children_recursive if m_.type == 'MESH']
        def _wv(m_):
            co_ = np.empty(len(m_.data.vertices) * 3, np.float32); m_.data.vertices.foreach_get("co", co_)
            M_ = np.array(m_.matrix_world); return co_.reshape(-1, 3) @ M_[:3, :3].T + M_[:3, 3]
        Vw = np.concatenate([_wv(m_) for m_ in msw])
        zb = z + WALL_H
        eave = Vw[(Vw[:, 2] > zb + 0.3) & (Vw[:, 2] < zb + 1.2)]          # the thatch just above the wall top
        r_eave = float(np.percentile(np.hypot(eave[:, 0] - hx, eave[:, 1] - hy), 85)) * 0.97 if len(eave) else 4.0
        drystone_wall(hx, hy, r_eave, z, seed=i)
        trodden(hx, hy, r_eave, z, seed=i)
        bpy.context.view_layer.update()
        top = max((m_.matrix_world @ Vector(c)).z for m_ in root.children_recursive if m_.type == 'MESH' for c in m_.bound_box)
        ms_ = [m_ for m_ in root.children_recursive if m_.type == 'MESH']
        P = np.array([m_.matrix_world @ Vector(c) for m_ in ms_ for c in m_.bound_box])
        half = float((P[:, 0].max() - P[:, 0].min() + P[:, 1].max() - P[:, 1].min()) / 4)
        roof_weights(Vector((hx, hy, top)), half * 0.98, z + 0.75, n=14, seed=i, meshes=ms_)
        if smoke_on:
            smoke((hx, hy, top - 1.6), height=20.0, drift=(0.75, 0.18), r0=1.5, grow=0.5, density=3.2 + 0.5 * i, name=f"smoke{i}")
    if smoke_on:
        ground_mist((0, 0, float(U.surface(0, 0))))
    return out


def ground_mist(c, size=(160, 160, 3.0), density=0.035):
    """Dawn mist lying on the machair: a shallow noise-broken volume, thickest at the ground."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(c[0], c[1], c[2] + size[2] / 2 - 0.3)); o = bpy.context.active_object
    o.name = "groundmist"; o.scale = size
    m = bpy.data.materials.new("mist"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; N.remove(N["Principled BSDF"])
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Generated'], sep.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 6; nz.inputs['Detail'].default_value = 4
    L.new(tc.outputs['Generated'], nz.inputs['Vector'])
    fz = N.new("ShaderNodeMapRange"); fz.inputs['From Min'].default_value = 0.0; fz.inputs['From Max'].default_value = 1.0
    fz.inputs['To Min'].default_value = 1.0; fz.inputs['To Max'].default_value = 0.0; L.new(sep.outputs['Z'], fz.inputs['Value'])
    br = N.new("ShaderNodeMapRange"); br.inputs['From Min'].default_value = 0.4; br.inputs['From Max'].default_value = 0.7
    L.new(nz.outputs['Fac'], br.inputs['Value'])
    m1 = N.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; L.new(fz.outputs[0], m1.inputs[0]); L.new(br.outputs[0], m1.inputs[1])
    m2 = N.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'; m2.inputs[1].default_value = density; L.new(m1.outputs[0], m2.inputs[0])
    v = N.new("ShaderNodeVolumePrincipled"); v.inputs['Color'].default_value = (0.85, 0.82, 0.8, 1); v.inputs['Anisotropy'].default_value = 0.6
    L.new(m2.outputs[0], v.inputs['Density']); L.new(v.outputs[0], N["Material Output"].inputs['Volume'])
    o.data.materials.append(m); o.visible_shadow = False
    return o


# ----------------------------------------------------------------------------- interior
def _lathe(name, prof, mat, loc, segs=40):
    return G._lathe(name, prof, segs=segs, mat_name=None, loc=loc) if False else _lathe2(name, prof, mat, loc, segs)


def _lathe2(name, prof, mat, loc, segs=40):
    bm = bmesh.new(); rings = []
    for r, z in prof:
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * k / segs), r * math.sin(2 * math.pi * k / segs), z)) for k in range(segs)])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(segs):
            bm.faces.new((r0[k], r0[(k + 1) % segs], r1[(k + 1) % segs], r1[k]))
    bm.faces.new(rings[0][::-1])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); o.location = loc
    return o


def pot(x, y, z, h=0.32, r=0.16, seed=0):
    rng = random.Random(seed)
    clay = ph.texture("brown_mud_dry", scale=6, name=f"potclay{seed}", tint=(0.75, 0.55, 0.42))
    prof = [(r * 0.55, 0), (r * 0.8, h * 0.08), (r * 1.0, h * 0.45), (r * 0.92, h * 0.8), (r * 0.82, h * 0.92), (r * 0.86, h),
            (r * 0.8, h * 0.98), (r * 0.74, h * 0.9), (r * 0.86, h * 0.45), (r * 0.5, h * 0.06), (0.0, h * 0.06)]
    o = _lathe2("pot", prof, clay, (x, y, z))
    d = o.modifiers.new("lumpy", "DISPLACE"); t = bpy.data.textures.new("potlump", "CLOUDS"); t.noise_scale = 0.08
    d.texture = t; d.strength = 0.006
    o.rotation_euler = (rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04), rng.uniform(0, 6))
    return o


def saddle_quern(x, y, z, rot=0.0):
    """Saddle quern: a long slab with a dished, worn top, and the rubbing stone (muller) resting on it."""
    base = G.stone((x, y, z + 0.08), (0.55, 0.34, 0.16), rot_z=rot, seed=3, flat=0.5)
    mul = G.stone((x + 0.05 * math.cos(rot), y + 0.05 * math.sin(rot), z + 0.19), (0.24, 0.14, 0.08), rot_z=rot + 0.2, seed=7, flat=0.6)
    return base, mul


def interior(fire=1.0, door_sun=0.0, hx=0.3, hy=0.0, r=4.6, seed=5, moon=0.0):
    """Built at the middle house centre (hx, hy) on a flat floor z = 0 (its own set, not the excavation terrain)."""
    rng = random.Random(seed)
    out = {}
    floor = ph.texture("dirt_floor", scale=1.5, name="earthfloor", tint=(0.8, 0.7, 0.58))
    bpy.ops.mesh.primitive_circle_add(vertices=96, radius=r + 0.6, fill_type='NGON', location=(hx, hy, 0)); f = bpy.context.active_object
    f.name = "floor"; f.data.materials.append(floor)
    sub = f.modifiers.new("sub", "SUBSURF"); sub.subdivision_type = 'SIMPLE'; sub.levels = 4; sub.render_levels = 4
    d = f.modifiers.new("d", "DISPLACE"); t = bpy.data.textures.new("floorlump", "CLOUDS"); t.noise_scale = 0.4; d.texture = t; d.strength = 0.015
    # revetment wall: courses of stone round the sunken floor (0.9 m), doorway east
    for c in range(7):
        n = int(2 * math.pi * r / 0.36)
        for k in range(n):
            a = 2 * math.pi * k / n + (0.5 * (c % 2)) * 2 * math.pi / n
            if math.degrees(a) % 360 < 11 or math.degrees(a) % 360 > 349:
                continue
            s = rng.uniform(0.25, 0.6)
            a2 = a + rng.uniform(-0.03, 0.03)
            G.stone((hx + (r + 0.12 + rng.uniform(-0.04, 0.04)) * math.cos(a2), hy + (r + 0.12) * math.sin(a2), 0.06 + c * 0.13 + rng.uniform(-0.03, 0.03)),
                    (s, s * rng.uniform(0.5, 0.8), s * rng.uniform(0.3, 0.55)),
                    rot_z=a2 + math.pi / 2 + rng.uniform(-0.25, 0.25), seed=rng.randrange(10), tilt=(rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12)))
    # turf-and-earth wall core behind the stone facing (no gaps to the sky), open at the east door
    earth = ph.texture("brown_mud_02", scale=1.5, name="turfwall", tint=(0.45, 0.38, 0.3))
    bm = bmesh.new(); segs = 96; rr = r + 0.38; top = 1.35
    ring0 = []; ring1 = []
    for k in range(segs + 1):
        a = 2 * math.pi * k / segs
        ring0.append(bm.verts.new((hx + rr * math.cos(a), hy + rr * math.sin(a), -0.05)))
        ring1.append(bm.verts.new((hx + rr * math.cos(a), hy + rr * math.sin(a), top)))
    for k in range(segs):
        mid = math.degrees(2 * math.pi * (k + 0.5) / segs) % 360
        if mid < 11 or mid > 349:
            continue
        bm.faces.new((ring0[k], ring0[k + 1], ring1[k + 1], ring1[k]))
    me = bpy.data.meshes.new("earthwall"); bm.to_mesh(me); bm.free(); me.materials.append(earth)
    ew = bpy.data.objects.new("earthwall", me); bpy.context.scene.collection.objects.link(ew)
    # posts, ring beam, rafters to the apex, thatch cone (inside face)
    wood = ph.texture("bark_brown_02", scale=3.0, name="postbark", tint=(0.6, 0.5, 0.42))
    for k in range(9):
        a = 2 * math.pi * (k + 0.5) / 9
        px, py = hx + 3.2 * math.cos(a), hy + 3.2 * math.sin(a)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=2.6, location=(px, py, 1.3)); p = bpy.context.active_object
        p.rotation_euler = (rng.uniform(-0.02, 0.02), rng.uniform(-0.02, 0.02), 0); p.data.materials.append(wood); p.name = "post"
    apex = Vector((hx, hy, 6.2)); eave_z = 1.2
    for k in range(28):
        a = 2 * math.pi * k / 28
        b = Vector((hx + (r + 0.3) * math.cos(a), hy + (r + 0.3) * math.sin(a), eave_z))
        mid = (apex + b) / 2; L_ = (apex - b).length
        bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=L_, location=mid); rf = bpy.context.active_object
        rf.rotation_euler = (apex - b).to_track_quat('Z', 'Y').to_euler(); rf.data.materials.append(wood); rf.name = "rafter"
    thatch = ph.texture("thatch_roof_angled", scale=1.2, name="thatch", tint=(0.55, 0.45, 0.32))
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=r + 0.45, radius2=0.05, depth=apex.z - eave_z + 0.1,
                                    location=(hx, hy, (apex.z + eave_z) / 2 + 0.08), end_fill_type='NOTHING')
    roof = bpy.context.active_object; roof.name = "roof"; roof.data.materials.append(thatch)
    sol = roof.modifiers.new("th", "SOLIDIFY"); sol.thickness = 0.25
    # door: a gap in the roof/wall east, light from outside
    bpy.ops.mesh.primitive_cube_add(size=1, location=(hx + r + 0.3, hy, 0.9)); cut = bpy.context.active_object
    cut.scale = (1.4, 1.2, 1.8); cut.display_type = 'WIRE'; cut.hide_render = True; cut.name = "doorcut"
    bm = bmesh.new(); bm.from_mesh(roof.data)
    kill = [f for f in bm.faces if (roof.matrix_world @ f.calc_center_median()).z < 2.3 and
            abs((roof.matrix_world @ f.calc_center_median()).y - hy) < 0.75 and (roof.matrix_world @ f.calc_center_median()).x > hx]
    bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(roof.data); bm.free()
    # door frame: two timber jambs and a lintel set into the wall at the east entrance
    for dy in (-0.62, 0.62):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=1.9, location=(hx + r + 0.15, hy + dy, 0.95)); j = bpy.context.active_object
        j.rotation_euler = (rng.uniform(-0.03, 0.03), rng.uniform(-0.03, 0.03), 0); j.data.materials.append(wood); j.name = "doorjamb"
    bpy.ops.mesh.primitive_cylinder_add(radius=0.11, depth=1.6, location=(hx + r + 0.15, hy, 1.88)); li = bpy.context.active_object
    li.rotation_euler = (math.pi / 2, 0, 0); li.data.materials.append(wood); li.name = "lintel"
    # hearth and fire
    hcx, hcy = hx + 0.2, hy
    G.hearth.__globals__  # (uses dig.H for the excavation; build a local hearth instead)
    ash = _mat("ash", (0.06, 0.05, 0.045), 0.95)
    bpy.ops.mesh.primitive_circle_add(vertices=32, radius=0.6, fill_type='NGON', location=(hcx, hcy, 0.01)); a_ = bpy.context.active_object
    a_.scale = (1.2, 0.95, 1); a_.data.materials.append(ash); a_.name = "hearth_ash"
    for k in range(11):
        a = 2 * math.pi * k / 11
        G.stone((hcx + 0.72 * math.cos(a), hcy + 0.56 * math.sin(a), 0.06), (0.26, 0.09, 0.15), rot_z=a + math.pi / 2, seed=k, flat=0.9)
    # peat fire: a heap of glowing peat blocks with flame volume and the fire light
    peat = _mat("peatfire", (0.05, 0.03, 0.02), 0.9, emit=(1.0, 0.32, 0.08), strength=3.0 * fire)
    for k in range(9):
        a = 2 * math.pi * k / 9
        bpy.ops.mesh.primitive_cube_add(size=1, location=(hcx + 0.17 * math.cos(a), hcy + 0.13 * math.sin(a), 0.06 + 0.03 * (k % 3)))
        pb = bpy.context.active_object; pb.scale = (0.16, 0.08, 0.07); pb.rotation_euler = (rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), a)
        pb.data.materials.append(peat); pb.name = "peat"
    flame = bpy.data.materials.new("flame"); flame.use_nodes = True; N = flame.node_tree.nodes; Lk = flame.node_tree.links
    N.remove(N["Principled BSDF"])
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 4; nz.inputs['Detail'].default_value = 5
    Lk.new(tc.outputs['Generated'], nz.inputs['Vector'])
    sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(tc.outputs['Generated'], sep.inputs[0])
    gz = N.new("ShaderNodeMapRange"); gz.inputs['From Min'].default_value = 1.0; gz.inputs['From Max'].default_value = 0.0; Lk.new(sep.outputs['Z'], gz.inputs['Value'])
    mm = N.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; Lk.new(nz.outputs['Fac'], mm.inputs[0]); Lk.new(gz.outputs[0], mm.inputs[1])
    th = N.new("ShaderNodeMapRange"); th.inputs['From Min'].default_value = 0.12; th.inputs['From Max'].default_value = 0.5
    th.inputs['To Max'].default_value = 22.0 * fire; Lk.new(mm.outputs[0], th.inputs['Value'])
    v = N.new("ShaderNodeVolumePrincipled"); v.inputs['Density'].default_value = 0.0
    v.inputs['Blackbody Tint'].default_value = (1, 1, 1, 1); v.inputs['Temperature'].default_value = 1300
    Lk.new(th.outputs[0], v.inputs['Blackbody Intensity'])
    Lk.new(v.outputs[0], N["Material Output"].inputs['Volume'])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=(hcx, hcy, 0.3)); fl = bpy.context.active_object
    fl.scale = (1, 1, 1.6); fl.data.materials.append(flame); fl.name = "flame"; fl.visible_shadow = False
    fd = bpy.data.lights.new("firelight", 'POINT'); fd.energy = 140 * fire; fd.color = (1.0, 0.52, 0.2); fd.shadow_soft_size = 0.25
    fo = bpy.data.objects.new("firelight", fd); bpy.context.scene.collection.objects.link(fo); fo.location = (hcx, hcy, 0.75)
    out["fire"] = fo; out["hearth"] = (hcx, hcy)
    # room smoke haze (light from the door and the fire reads in the air)
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=5.5, location=(hx, hy, 2.75)); hz = bpy.context.active_object; hz.name = "roomhaze"
    hm = bpy.data.materials.new("roomhaze"); hm.use_nodes = True; N = hm.node_tree.nodes; Lk = hm.node_tree.links; N.remove(N["Principled BSDF"])
    vv = N.new("ShaderNodeVolumePrincipled"); vv.inputs['Density'].default_value = 0.012; vv.inputs['Anisotropy'].default_value = 0.5
    vv.inputs['Color'].default_value = (0.7, 0.66, 0.62, 1)
    Lk.new(vv.outputs[0], N["Material Output"].inputs['Volume']); hz.data.materials.append(hm)
    # door light: the morning outside (sun through the east doorway) and sky fill
    U.light("dawn")["sun"].hide_render = True          # the dawn sky outside the door (its sun is the doorsun below)
    bpy.context.scene.world.node_tree.nodes["Background"].inputs['Strength'].default_value = 0.5
    dl = bpy.data.lights.new("doorsky", 'AREA'); dl.size = 1.2; dl.shape = 'RECTANGLE'; dl.size_y = 1.7; dl.energy = 60; dl.color = (0.7, 0.78, 0.95)
    do = bpy.data.objects.new("doorsky", dl); bpy.context.scene.collection.objects.link(do)
    do.location = (hx + r + 0.9, hy, 0.95); do.rotation_euler = (0, math.radians(-90), 0); do.visible_camera = False
    if moon > 0:
        # night outside: the sky through the doorway is a cold blue glow, a low moon throws a pale shaft across the floor
        bpy.context.scene.world.node_tree.nodes["Background"].inputs['Strength'].default_value = 0.05
        dl.energy = 160 * moon; dl.color = (0.42, 0.55, 1.0); dl.size = 2.0
        mn = bpy.data.lights.new("moon", 'SUN'); mn.energy = 0.9 * moon; mn.color = (0.55, 0.68, 1.0); mn.angle = math.radians(0.6)
        mo = bpy.data.objects.new("moon", mn); bpy.context.scene.collection.objects.link(mo)
        mo.rotation_euler = (Vector((-1, 0.15, -0.3))).to_track_quat('-Z', 'Y').to_euler()
        out["moon"] = mo
        # moonlight entering by the doorway: a cold spill just inside the door, angled down across the floor
        ms = bpy.data.lights.new("moonspill", 'SPOT'); ms.energy = 2600 * moon; ms.color = (0.5, 0.62, 1.0)
        ms.spot_size = math.radians(70); ms.spot_blend = 0.6; ms.shadow_soft_size = 0.5
        mso = bpy.data.objects.new("moonspill", ms); bpy.context.scene.collection.objects.link(mso)
        mso.location = (hx + r - 0.2, hy, 1.5)
        mso.rotation_euler = (Vector((-1.0, 0.37, -0.28))).to_track_quat('-Z', 'Y').to_euler()
    if door_sun > 0:
        sd = bpy.data.lights.new("doorsun", 'SUN'); sd.energy = 4.0 * door_sun; sd.color = (1.0, 0.66, 0.4); sd.angle = math.radians(0.8)
        so = bpy.data.objects.new("doorsun", sd); bpy.context.scene.collection.objects.link(so)
        so.rotation_euler = (Vector((-1, 0, -0.12))).to_track_quat('-Z', 'Y').to_euler()
        out["sun"] = so
    # the household: quern, pots, baskets, sheepskins, a storage pit lid
    saddle_quern(hx - 1.8, hy - 1.6, 0.0, rot=0.6)
    for k, (px, py) in enumerate(((hx - 2.6, hy + 1.4), (hx - 2.9, hy + 0.9), (hx - 2.3, hy + 1.9), (hx + 1.6, hy + 2.8))):
        pot(px, py, 0.0, h=rng.uniform(0.26, 0.4), r=rng.uniform(0.13, 0.19), seed=k)
    try:
        bk, _ = ph.model("wicker_basket_01", loc=(hx - 1.2, hy + 2.9, 0.0), rot_z=0.4)
    except Exception as ex:
        print("basket", ex)
    try:
        rug, ms = sf.model("dbb23e213aac4832a20a59e26d535c7c", loc=(hx - 1.0, hy - 0.6, 0.01), rot_z=0.5, height=None)
        rug.scale = (18, 18, 18)
        fur = _mat("fleece", (0.55, 0.48, 0.38), 0.95)
        for o in ms:
            o.data.materials.clear(); o.data.materials.append(fur)
    except Exception as ex:
        print("rug", ex)
    return out


class Islander(object):
    """Built on modern.ModernMan with wool tunic (long 'coat' cut) and cloak colours; long hair and beard."""
    def __new__(cls, name="Islander", **kw):
        import modern as MD

        class _I(MD.ModernMan):
            GENDER = 1.0; MUSCLE = 0.6; WEIGHT = 0.45; HEIGHT = 0.45
            HAIR = (0.18, 0.06); HAIR_LEN = (0.06, 0.11); FACIAL = "beard"
            SHIRT = (0.2, 0.16, 0.1); JACKET = "coat"; JACKET_COL = (0.16, 0.11, 0.06)
            TROUSERS = (0.12, 0.09, 0.06); SHOES = (0.08, 0.05, 0.03)
        return _I(name, years=34, **kw)
