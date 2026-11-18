"""A two-masted merchant brigantine of the 1870s (Mary Celeste / Dei Gratia class), built in code.

Axes: bow toward +X, port +Y, starboard -Y, waterline at z = 0. About 31 m on deck, 7.8 m beam.
Hull lines are a parametric surface (s along the ship, t keel->deck); bulwarks with timberheads and a cap
rail; planked deck; aft cabin trunk with skylight and companion; galley house; main and fore hatches;
helm and binnacle; pumps; windlass; bowsprit and jib-boom; foremast square-rigged (five yards), mainmast
fore-and-aft (boom and gaff); shrouds with ratlines, stays, backstays, lifts and braces.

Sails are a list of states so the same model is the Dei Gratia under full sail or the Mary Celeste as found:
    build(name, sails="found" | "full", rail_gap=(x0, x1, side) | None, boat=True | False)
"""
import math, os, random
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix, noise
import ph

L = 31.4; B = 7.8; DRAFT = 3.1


def zdeck(x):
    u = x / (L / 2)
    return 1.35 + (0.85 * u * u if u > 0 else 0.45 * u * u)


RAIL_H = 0.95


# ----------------------------------------------------------------------------- materials
def _mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links, m.node_tree.nodes["Principled BSDF"]


def paint(name, color, rough=0.5, grime=0.35, wet=0.0, scale=3.0, chips=0.0, under=(0.25, 0.18, 0.12)):
    m, N, Lk, p = _mat(name)
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 8
    Lk.new(tc.outputs['Object'], nz.inputs['Vector'])
    streak = N.new("ShaderNodeMapping"); streak.inputs['Scale'].default_value = (6, 6, 0.4)
    Lk.new(tc.outputs['Object'], streak.inputs['Vector'])
    sn = N.new("ShaderNodeTexNoise"); sn.inputs['Scale'].default_value = 4; sn.inputs['Detail'].default_value = 6
    Lk.new(streak.outputs[0], sn.inputs['Vector'])
    c = N.new("ShaderNodeRGB"); c.outputs[0].default_value = (*color, 1)
    g = N.new("ShaderNodeMix"); g.data_type = 'RGBA'; g.blend_type = 'MULTIPLY'; g.inputs['Factor'].default_value = grime
    g.inputs[7].default_value = (0.55, 0.5, 0.42, 1)
    rr = N.new("ShaderNodeMapRange"); rr.inputs['From Min'].default_value = 0.4; rr.inputs['From Max'].default_value = 0.65
    Lk.new(sn.outputs['Fac'], rr.inputs['Value']); Lk.new(rr.outputs[0], g.inputs['Factor'])
    Lk.new(c.outputs[0], g.inputs[6])
    out = g.outputs[2]
    if chips:
        vo = N.new("ShaderNodeTexNoise"); vo.inputs['Scale'].default_value = 22; vo.inputs['Detail'].default_value = 10
        Lk.new(tc.outputs['Object'], vo.inputs['Vector'])
        cr = N.new("ShaderNodeMapRange"); cr.inputs['From Min'].default_value = 0.68 - 0.1 * chips; cr.inputs['From Max'].default_value = 0.7 - 0.1 * chips
        Lk.new(vo.outputs['Fac'], cr.inputs['Value'])
        ch = N.new("ShaderNodeMix"); ch.data_type = 'RGBA'; ch.inputs[7].default_value = (*under, 1)
        Lk.new(cr.outputs[0], ch.inputs['Factor']); Lk.new(out, ch.inputs[6]); out = ch.outputs[2]
    Lk.new(out, p.inputs['Base Color'])
    rm = N.new("ShaderNodeMapRange"); rm.inputs['To Min'].default_value = rough * (1 - 0.7 * wet); rm.inputs['To Max'].default_value = min(1, rough * (1 - 0.4 * wet) + 0.2)
    Lk.new(nz.outputs['Fac'], rm.inputs['Value']); Lk.new(rm.outputs[0], p.inputs['Roughness'])
    if wet:
        p.inputs['Coat Weight'].default_value = 0.6 * wet; p.inputs['Coat Roughness'].default_value = 0.08
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.15; Lk.new(nz.outputs['Fac'], b.inputs['Height'])
    Lk.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


def wood(aid, scale=0.6, wet=0.0, tint=None, name=None):
    m = ph.texture(aid, scale=scale, res="2k", name=name or aid, tint=tint)
    p = m.node_tree.nodes["Principled BSDF"]
    if wet:
        N = m.node_tree.nodes; Lk = m.node_tree.links
        r = p.inputs['Roughness']
        if r.links:
            src = r.links[0].from_socket
            mr = N.new("ShaderNodeMath"); mr.operation = 'MULTIPLY'; mr.inputs[1].default_value = 1 - 0.6 * wet
            Lk.new(src, mr.inputs[0]); Lk.new(mr.outputs[0], r)
        bc = p.inputs['Base Color']
        if bc.links:
            src = bc.links[0].from_socket
            dk = N.new("ShaderNodeMix"); dk.data_type = 'RGBA'; dk.blend_type = 'MULTIPLY'; dk.inputs['Factor'].default_value = 1
            dk.inputs[7].default_value = (1 - 0.45 * wet, 1 - 0.45 * wet, 1 - 0.42 * wet, 1)
            Lk.new(src, dk.inputs[6]); Lk.new(dk.outputs[2], bc)
        p.inputs['Coat Weight'].default_value = 0.35 * wet; p.inputs['Coat Roughness'].default_value = 0.12
    return m


def canvas(name, wet=0.6, dirt=0.5, color=(0.62, 0.56, 0.45)):
    """Sailcloth: panels (seams), weathering, wet darkening, light passes through."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; Lk = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(tc.outputs['UV'], sep.inputs[0])
    seams = N.new("ShaderNodeMath"); seams.operation = 'MULTIPLY'; seams.inputs[1].default_value = 18.0
    Lk.new(sep.outputs['X'], seams.inputs[0])
    fr = N.new("ShaderNodeMath"); fr.operation = 'FRACT'; Lk.new(seams.outputs[0], fr.inputs[0])
    sm = N.new("ShaderNodeMapRange"); sm.inputs['From Min'].default_value = 0.0; sm.inputs['From Max'].default_value = 0.06
    Lk.new(fr.outputs[0], sm.inputs['Value'])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 8
    Lk.new(tc.outputs['Object'], nz.inputs['Vector'])
    c = N.new("ShaderNodeRGB"); c.outputs[0].default_value = (*color, 1)
    g = N.new("ShaderNodeMix"); g.data_type = 'RGBA'; g.blend_type = 'MULTIPLY'; g.inputs['Factor'].default_value = dirt
    Lk.new(c.outputs[0], g.inputs[6]); Lk.new(nz.outputs['Color'], g.inputs[7])
    w = N.new("ShaderNodeMix"); w.data_type = 'RGBA'; w.blend_type = 'MULTIPLY'; w.inputs['Factor'].default_value = 1
    w.inputs[7].default_value = (1 - 0.4 * wet, 1 - 0.4 * wet, 1 - 0.38 * wet, 1)
    Lk.new(g.outputs[2], w.inputs[6])
    Lk.new(w.outputs[2], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.85 - 0.35 * wet
    p.inputs['Sheen Weight'].default_value = 0.2
    # thin translucent cloth: a share of the light goes through
    tr = N.new("ShaderNodeBsdfTranslucent"); Lk.new(w.outputs[2], tr.inputs['Color'])
    mix = N.new("ShaderNodeMixShader"); mix.inputs[0].default_value = 0.28
    Lk.new(p.outputs[0], mix.inputs[1]); Lk.new(tr.outputs[0], mix.inputs[2])
    Lk.new(mix.outputs[0], N["Material Output"].inputs['Surface'])
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.35
    Lk.new(sm.outputs[0], b.inputs['Height']); Lk.new(b.outputs['Normal'], p.inputs['Normal'])
    m.use_backface_culling = False
    return m


def tarred_rope(name="rope", color=(0.028, 0.02, 0.013)):
    """Tarred hemp: near-black brown, matte with a waxy sheen on the strands, a visible right-hand lay."""
    m, N, Lk, p = _mat(name)
    p.inputs['Base Color'].default_value = (*color, 1); p.inputs['Roughness'].default_value = 0.72
    p.inputs['Sheen Weight'].default_value = 0.25; p.inputs['Specular IOR Level'].default_value = 0.3
    tc = N.new("ShaderNodeTexCoord")
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'DIAGONAL'
    wv.inputs['Scale'].default_value = 160; Lk.new(tc.outputs['Object'], wv.inputs['Vector'])
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.8
    Lk.new(wv.outputs['Fac'], b.inputs['Height']); Lk.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


def iron(name="iron"):
    m, N, Lk, p = _mat(name)
    p.inputs['Base Color'].default_value = (0.03, 0.028, 0.026, 1); p.inputs['Metallic'].default_value = 0.8
    p.inputs['Roughness'].default_value = 0.55
    return m


# ----------------------------------------------------------------------------- mesh helpers
def mesh_obj(name, verts, faces, mat=None, smooth=True, coll=None):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
    if smooth:
        me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool))
    o = bpy.data.objects.new(name, me); (coll or bpy.context.collection).objects.link(o)
    if mat:
        o.data.materials.append(mat)
    return o


def box(name, center, size, mat=None, rot=(0, 0, 0), bevel=0.0, coll=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        b = o.modifiers.new("Bevel", "BEVEL"); b.width = bevel; b.segments = 2; b.limit_method = 'ANGLE'
    if mat:
        o.data.materials.append(mat)
    _move(o, coll)
    return o


def cyl(name, p0, p1, r0, r1=None, mat=None, verts=20, coll=None, caps=True):
    p0 = Vector(p0); p1 = Vector(p1); r1 = r0 if r1 is None else r1
    d = p1 - p0; n = verts
    q = d.to_track_quat('Z', 'Y')
    V = []; F = []
    for k, (pp, rr) in enumerate(((p0, r0), (p1, r1))):
        for i in range(n):
            a = 2 * math.pi * i / n
            V.append(pp + q @ Vector((math.cos(a) * rr, math.sin(a) * rr, 0)))
    for i in range(n):
        F.append([i, (i + 1) % n, n + (i + 1) % n, n + i])
    if caps:
        F.append(list(range(n))[::-1]); F.append([n + i for i in range(n)])
    o = mesh_obj(name, V, F, mat, coll=coll)
    if caps:
        for pl in o.data.polygons[-2:]:
            pl.use_smooth = False
        ee = o.modifiers.new("EdgeSplit", "EDGE_SPLIT"); ee.split_angle = math.radians(50)
    return o


def _move(o, coll):
    if coll is None:
        return
    for c in o.users_collection:
        c.objects.unlink(o)
    coll.objects.link(o)


def rope(name, pts, radius, mat, coll=None, sag=0.0, n=12):
    """A rope through points (polyline) with optional catenary sag between first and last."""
    P = [Vector(p) for p in pts]
    if len(P) == 2 and sag:
        a, b = P
        P = [a.lerp(b, i / (n - 1)) - Vector((0, 0, sag * 4 * (i / (n - 1)) * (1 - i / (n - 1)))) for i in range(n)]
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    cu.bevel_depth = radius; cu.bevel_resolution = 2; cu.use_fill_caps = True
    sp = cu.splines.new('POLY'); sp.points.add(len(P) - 1)
    for i, p in enumerate(P):
        sp.points[i].co = (*p, 1)
    o = bpy.data.objects.new(name, cu); (coll or bpy.context.collection).objects.link(o)
    cu.materials.append(mat)
    return o


# ----------------------------------------------------------------------------- hull
def _ends(t):
    """x of stern and bow at height fraction t (0 keel .. 1 deck)."""
    xb = L / 2 - 2.6 * (1 - t) ** 1.4            # raked, rounded stem
    xs = -L / 2 + 3.2 * (1 - t) ** 1.8           # counter stern overhang
    return xs, xb


def half_breadth(s, t):
    sec = (1 - (1 - t) ** 2.4) ** (1 / 2.4)
    sec = 0.05 + 0.95 * sec
    sec *= 1 - 0.035 * t ** 6                     # a touch of tumblehome
    if s > 0.52:                                  # entrance
        u = (s - 0.52) / 0.48
        pl = (1 - u ** 2.0) ** (0.55 + 0.35 * (1 - t))
    elif s < 0.34:                                # run; flat transom above the waterline
        u = s / 0.34
        trans = 0.6 * max(0.0, (t - 0.55) / 0.45) ** 0.8
        pl = trans + (1 - trans) * (u ** (0.55 + 0.9 * (1 - t)))
    else:
        pl = 1.0
    return B / 2 * sec * max(pl, 0.0)


def hull_z(x, t):
    zk = -DRAFT + 0.25 * max(0, -x / (L / 2)) * 0  # level keel
    return zk + t * (zdeck(x) - zk)


def build_hull(name, mats, coll, ns=140, nt=36):
    V = []; idx = {}
    for j in range(nt + 1):
        t = j / nt
        xs, xb = _ends(t)
        for i in range(ns + 1):
            s = i / ns
            x = xs + s * (xb - xs)
            b = half_breadth(s, t)
            z = hull_z(x, t)
            for side, sg in (("P", 1), ("S", -1)):
                idx[(i, j, side)] = len(V); V.append((x, sg * b, z))
    F = []
    for j in range(nt):
        for i in range(ns):
            F.append([idx[(i, j, "P")], idx[(i + 1, j, "P")], idx[(i + 1, j + 1, "P")], idx[(i, j + 1, "P")]])
            F.append([idx[(i, j, "S")], idx[(i, j + 1, "S")], idx[(i + 1, j + 1, "S")], idx[(i + 1, j, "S")]])
    for i in range(ns):                           # keel bottom strip
        F.append([idx[(i, 0, "S")], idx[(i + 1, 0, "S")], idx[(i + 1, 0, "P")], idx[(i, 0, "P")]])
    for j in range(nt):                           # transom / sternpost and stem closures
        F.append([idx[(0, j, "P")], idx[(0, j + 1, "P")], idx[(0, j + 1, "S")], idx[(0, j, "S")]])
        F.append([idx[(ns, j, "P")], idx[(ns, j, "S")], idx[(ns, j + 1, "S")], idx[(ns, j + 1, "P")]])
    o = mesh_obj(name + "_hull", V, F, coll=coll)
    o.data.materials.append(hull_material(name, mats))
    return o


def hull_material(name, mats):
    """Topsides / boot-top / bottom by height, with a sheer wale (a pale stripe under the rail)."""
    m = bpy.data.materials.new(name + "_hullmat"); m.use_nodes = True
    N = m.node_tree.nodes; Lk = m.node_tree.links
    out = N["Material Output"]; N.remove(N["Principled BSDF"])
    def shader(mm):
        g = N.new("ShaderNodeGroup") if False else None
        # copy a material's node tree into this one as a group-less duplicate: reuse its Principled output
        return mm
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(tc.outputs['Object'], sep.inputs[0])
    wob = N.new("ShaderNodeTexNoise"); wob.inputs['Scale'].default_value = 0.6; Lk.new(tc.outputs['Object'], wob.inputs['Vector'])
    zz = N.new("ShaderNodeMath"); zz.operation = 'MULTIPLY_ADD'; zz.inputs[1].default_value = 0.04
    Lk.new(wob.outputs['Fac'], zz.inputs[0]); Lk.new(sep.outputs['Z'], zz.inputs[2])
    def band(lo, hi):
        a = N.new("ShaderNodeMath"); a.operation = 'GREATER_THAN'; a.inputs[1].default_value = lo; Lk.new(zz.outputs[0], a.inputs[0])
        b = N.new("ShaderNodeMath"); b.operation = 'LESS_THAN'; b.inputs[1].default_value = hi; Lk.new(zz.outputs[0], b.inputs[0])
        c = N.new("ShaderNodeMath"); c.operation = 'MULTIPLY'; Lk.new(a.outputs[0], c.inputs[0]); Lk.new(b.outputs[0], c.inputs[1])
        return c.outputs[0]
    def bsdf(col, rough, coat=0.0):
        p = N.new("ShaderNodeBsdfPrincipled"); p.inputs['Base Color'].default_value = (*col, 1)
        p.inputs['Roughness'].default_value = rough; p.inputs['Coat Weight'].default_value = coat; p.inputs['Coat Roughness'].default_value = 0.1
        nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 7; nz.inputs['Detail'].default_value = 8
        Lk.new(tc.outputs['Object'], nz.inputs['Vector'])
        bm = N.new("ShaderNodeBump"); bm.inputs['Strength'].default_value = 0.12; Lk.new(nz.outputs['Fac'], bm.inputs['Height'])
        Lk.new(bm.outputs['Normal'], p.inputs['Normal'])
        # planking seams (horizontal strakes)
        wv = N.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'; wv.inputs['Scale'].default_value = 0.55
        wv.inputs['Distortion'].default_value = 0.0; Lk.new(tc.outputs['Object'], wv.inputs['Vector'])
        rm = N.new("ShaderNodeMapRange"); rm.inputs['From Min'].default_value = 0.0; rm.inputs['From Max'].default_value = 0.08
        Lk.new(wv.outputs['Fac'], rm.inputs['Value'])
        b2 = N.new("ShaderNodeBump"); b2.inputs['Strength'].default_value = 0.25; Lk.new(rm.outputs[0], b2.inputs['Height'])
        Lk.new(bm.outputs['Normal'], b2.inputs['Normal']); Lk.new(b2.outputs['Normal'], p.inputs['Normal'])
        return p
    top = bsdf((0.012, 0.012, 0.014), 0.3, 0.5)
    wale = bsdf((0.45, 0.42, 0.36), 0.45, 0.3)
    boot = bsdf((0.38, 0.36, 0.32), 0.5)
    bot = bsdf((0.16, 0.055, 0.03), 0.55)
    m1 = N.new("ShaderNodeMixShader"); Lk.new(band(-0.3, 0.06), m1.inputs[0]); Lk.new(bot.outputs[0], m1.inputs[1]); Lk.new(boot.outputs[0], m1.inputs[2])
    hi = N.new("ShaderNodeMath"); hi.operation = 'GREATER_THAN'; hi.inputs[1].default_value = 0.06; Lk.new(zz.outputs[0], hi.inputs[0])
    m2 = N.new("ShaderNodeMixShader"); Lk.new(hi.outputs[0], m2.inputs[0]); Lk.new(m1.outputs[0], m2.inputs[1]); Lk.new(top.outputs[0], m2.inputs[2])
    # pale wale just below the deck line (follows the sheer: use distance below the deck via a gradient in x)
    Lk.new(m2.outputs[0], out.inputs['Surface'])
    return m


def bulwark(name, mats, coll, gap=None, ns=140):
    """Bulwarks from deck to rail on both sides: outer planking continues the hull, an inner lining, timberheads
    every 1.1 m and a cap rail. gap = (x0, x1, side) leaves an opening with the section removed."""
    out = []
    xs0, xb0 = _ends(1.0)
    th = 0.11
    for side, sg in (("P", 1), ("S", -1)):
        segs = [(xs0 + 0.05, xb0 - 0.35)]
        if gap and gap[2] == side:
            segs = [(xs0 + 0.05, gap[0]), (gap[1], xb0 - 0.35)]
        for k, (a, b) in enumerate(segs):
            n = max(4, int(ns * (b - a) / (xb0 - xs0)))
            V = []; F = []
            for i in range(n + 1):
                x = a + (b - a) * i / n
                s = (x - xs0) / (xb0 - xs0)
                hb = half_breadth(s, 1.0)
                z0 = zdeck(x); z1 = z0 + RAIL_H
                V += [(x, sg * hb, z0 - 0.02), (x, sg * (hb + 0.015), z1), (x, sg * (hb - th + 0.015), z1), (x, sg * (hb - th), z0 - 0.02)]
            for i in range(n):
                q = 4 * i; r = 4 * (i + 1)
                quads = [[q, r, r + 1, q + 1], [q + 1, r + 1, r + 2, q + 2], [q + 2, r + 2, r + 3, q + 3]]
                F += [f if sg > 0 else f[::-1] for f in quads]
            F += [[0, 1, 2, 3][::(1 if sg < 0 else -1)], [4 * n, 4 * n + 1, 4 * n + 2, 4 * n + 3][::(-1 if sg < 0 else 1)]]
            o = mesh_obj(f"{name}_bulwark_{side}{k}", V, F, coll=coll, smooth=False)
            o.data.materials.append(mats["topside"]); o.data.materials.append(mats["lining"])
            for pl in o.data.polygons:
                pl.material_index = 1 if (pl.normal.y * sg) > 0.3 else 0
            out.append(o)
            # cap rail
            CV = []; CF = []
            for i in range(n + 1):
                x = a + (b - a) * i / n; s = (x - xs0) / (xb0 - xs0); hb = half_breadth(s, 1.0); z1 = zdeck(x) + RAIL_H
                CV += [(x, sg * (hb + 0.05), z1), (x, sg * (hb + 0.05), z1 + 0.07), (x, sg * (hb - th - 0.04), z1 + 0.07), (x, sg * (hb - th - 0.04), z1)]
            for i in range(n):
                q = 4 * i; r = 4 * (i + 1)
                for f in ([q, r, r + 1, q + 1], [q + 1, r + 1, r + 2, q + 2], [q + 2, r + 2, r + 3, q + 3], [q + 3, r + 3, r, q]):
                    CF.append(f if sg > 0 else f[::-1])
            CF += [[0, 1, 2, 3][::(1 if sg < 0 else -1)], [4 * n, 4 * n + 1, 4 * n + 2, 4 * n + 3][::(-1 if sg < 0 else 1)]]
            c = mesh_obj(f"{name}_caprail_{side}{k}", CV, CF, mats["rail"], coll=coll, smooth=False)
            bv = c.modifiers.new("Bevel", "BEVEL"); bv.width = 0.012; bv.segments = 2
            out.append(c)
            # timberheads (stanchions) on the inboard face
            x = a + 0.3
            while x < b - 0.2:
                s = (x - xs0) / (xb0 - xs0); hb = half_breadth(s, 1.0); z0 = zdeck(x)
                out.append(box(f"{name}_stanchion", (x, sg * (hb - th - 0.05), z0 + RAIL_H / 2), (0.12, 0.1, RAIL_H), mats["lining"], bevel=0.01, coll=coll))
                x += 1.1
    return out


def deck(name, mats, coll, n=120):
    xs0, xb0 = _ends(1.0)
    V = []; F = []
    for i in range(n + 1):
        x = xs0 + 0.03 + (xb0 - 0.3 - xs0) * i / n
        s = (x - xs0) / (xb0 - xs0); hb = max(half_breadth(s, 1.0) - 0.1, 0.05)
        z = zdeck(x)
        for k in range(9):
            y = -hb + 2 * hb * k / 8
            V.append((x, y, z + 0.06 * (1 - (y / max(hb, 0.1)) ** 2) * 0 + 0.012 * (1 - (y / max(hb, 0.1)) ** 2)))  # camber
    for i in range(n):
        for k in range(8):
            a = i * 9 + k
            F.append([a, a + 9, a + 10, a + 1])
    o = mesh_obj(name + "_deck", V, F, mats["deck"], coll=coll)
    # UVs for the planks: world x/y
    uv = o.data.uv_layers.new(name="UVMap")
    for l in o.data.loops:
        v = o.data.vertices[l.vertex_index].co
        uv.data[l.index].uv = (v.x * 0.35, v.y * 0.35)
    return o


# ----------------------------------------------------------------------------- spars & sails
FORE_X = L / 2 - 9.4
MAIN_X = -4.6
MAIN_HATCH_X = -1.2


class Mast:
    def __init__(self, x, lower, top, tg, rake=4.0):
        self.x = x; self.lower = lower; self.top = top; self.tg = tg
        self.base = Vector((x, 0, zdeck(x)))
        r = math.radians(rake); self.dir = Vector((-math.sin(r), 0, math.cos(r)))

    def at(self, h):
        return self.base + self.dir * h


def build_spars(name, mats, coll):
    sp = {}
    fm = Mast(FORE_X, 14.5, 9.5, 7.0, rake=3.0); mm = Mast(MAIN_X, 15.5, 9.5, 0.0, rake=5.0)
    sp["fore"] = fm; sp["main"] = mm
    for m, nm in ((fm, "fore"), (mm, "main")):
        cyl(f"{name}_{nm}mast", m.at(-0.2), m.at(m.lower + 1.6), 0.27, 0.22, mats["spar"], coll=coll)
        cyl(f"{name}_{nm}top_mast", m.at(m.lower - 1.6) + Vector((0.45, 0, 0)), m.at(m.lower + m.top + 0.8) + Vector((0.45, 0, 0)), 0.17, 0.12, mats["spar"], coll=coll)
        # top (platform) and trestle trees
        t = m.at(m.lower)
        box(f"{name}_{nm}_top", t + Vector((0.2, 0, 0)), (1.6, 3.2, 0.1), mats["spar"], bevel=0.01, coll=coll)
        box(f"{name}_{nm}_cap", m.at(m.lower + 1.6) + Vector((0.22, 0, 0)), (0.9, 0.45, 0.25), mats["spar"], coll=coll)
        if m.tg:
            cyl(f"{name}_{nm}tg_mast", m.at(m.lower + m.top - 1.0) + Vector((0.75, 0, 0)), m.at(m.lower + m.top + m.tg) + Vector((0.75, 0, 0)), 0.1, 0.06, mats["spar"], coll=coll)
            box(f"{name}_{nm}_xtree", m.at(m.lower + m.top) + Vector((0.5, 0, 0)), (0.9, 2.2, 0.08), mats["spar"], coll=coll)
        sp[nm + "_head"] = m.at(m.lower + 1.4)
        sp[nm + "_tophead"] = m.at(m.lower + m.top + 0.5) + Vector((0.45, 0, 0))
        sp[nm + "_tghead"] = m.at(m.lower + m.top + m.tg) + Vector((0.75, 0, 0))
        cyl(f"{name}_{nm}_truck", sp[nm + "_tghead" if m.tg else nm + "_tophead"], sp[nm + "_tghead" if m.tg else nm + "_tophead"] + Vector((0, 0, 0.12)), 0.11, 0.11, mats["spar"], coll=coll)
    # fore yards: height above deck, length
    yards = [("course", 12.3, 15.6), ("ltop", 15.4, 13.6), ("utop", 19.2, 12.0), ("tgal", 23.4, 9.6), ("royal", 26.6, 7.4)]
    sp["yards"] = {}
    for nm, h, ln in yards:
        c = fm.at(h) + Vector((0.45 if h > fm.lower else 0, 0, 0)) + Vector((0.32 if h > fm.lower + fm.top else 0, 0, 0)) + Vector((0.35, 0, 0))
        a = c + Vector((0, ln / 2, 0)); b = c - Vector((0, ln / 2, 0))
        # yards braced round a little (wind from starboard quarter)
        R = Matrix.Rotation(math.radians(-14), 3, 'Z')
        a = c + R @ (a - c); b = c + R @ (b - c)
        cyl(f"{name}_yard_{nm}", a, b, 0.05 + 0.006 * ln * 0.3, mat=mats["spar"], verts=14, coll=coll)
        # tapering is implied by the arms
        sp["yards"][nm] = (a, b, c)
    # main boom and gaff
    g0 = mm.at(2.0); g1 = g0 + Vector((-12.6, 0, 0.6))
    R = Matrix.Rotation(math.radians(10), 3, 'Z')
    g1 = g0 + R @ (g1 - g0)
    cyl(f"{name}_boom", g0, g1, 0.14, 0.11, mats["spar"], coll=coll)
    gf0 = mm.at(12.8); gf1 = gf0 + R @ Vector((-8.4, 0, 4.4))
    cyl(f"{name}_gaff", gf0, gf1, 0.12, 0.08, mats["spar"], coll=coll)
    sp["boom"] = (g0, g1); sp["gaff"] = (gf0, gf1)
    # bowsprit and jib-boom
    xb = _ends(1.0)[1]
    b0 = Vector((xb - 2.5, 0, zdeck(xb) + 0.35)); bd = Vector((math.cos(math.radians(12)), 0, math.sin(math.radians(12))))
    cyl(f"{name}_bowsprit", b0, b0 + bd * 8.6, 0.25, 0.16, mats["spar"], coll=coll)
    jb0 = b0 + bd * 5.5 + Vector((0, 0, 0.32)); jb1 = jb0 + bd * 8.0
    cyl(f"{name}_jibboom", jb0, jb1, 0.13, 0.07, mats["spar"], coll=coll)
    sp["bowsprit_end"] = b0 + bd * 8.4; sp["jibboom_end"] = jb1; sp["bowsprit_root"] = b0
    sp["martingale"] = b0 + bd * 8.0 - Vector((0, 0, 1.6))
    cyl(f"{name}_dolphin", b0 + bd * 8.0, sp["martingale"], 0.05, 0.04, mats["spar"], coll=coll)
    return sp


def sail_mesh(name, corners, nu, nv, billow, wind, mat, coll, tear=None, seed=0, hang=0.0, flog=0.0):
    """Quad sail between 4 corners (top-left, top-right, bottom-right, bottom-left), billowed downwind.
    tear(u, v) -> True deletes that cell (rips); hang lets the foot droop."""
    c = [Vector(p) for p in corners]
    rng = random.Random(seed)
    V = []; UV = []
    for j in range(nv + 1):
        v = j / nv
        for i in range(nu + 1):
            u = i / nu
            p = (c[0].lerp(c[1], u)).lerp(c[3].lerp(c[2], u), v)
            bul = billow * math.sin(math.pi * u) * (math.sin(math.pi * min(1.0, v * 0.85 + 0.08)) ** 0.8)
            wr = noise.noise(Vector((u * 4 + seed, v * 4, 0.3))) * 0.08 * billow + noise.noise(Vector((u * 11, v * 9 + seed, 1.7))) * flog
            p = p + Vector(wind) * (bul + wr)
            p.z -= hang * math.sin(math.pi * u) * v ** 2
            V.append(p); UV.append((u, v))
    F = []
    for j in range(nv):
        for i in range(nu):
            if tear and tear((i + 0.5) / nu, (j + 0.5) / nv):
                continue
            a = j * (nu + 1) + i
            F.append([a, a + 1, a + nu + 2, a + nu + 1])
    o = mesh_obj(name, V, F, mat, coll=coll)
    uvl = o.data.uv_layers.new(name="UVMap")
    for l in o.data.loops:
        uvl.data[l.index].uv = UV[l.vertex_index]
    so = o.modifiers.new("Thick", "SOLIDIFY"); so.thickness = 0.004
    s = o.modifiers.new("Sub", "SUBSURF"); s.levels = 1; s.render_levels = 1
    bpy.ops.object.select_all(action='DESELECT')
    return o


def shreds(name, a, b, n, length, mat, coll, wind, seed=3):
    """Strips of canvas left hanging from a yard after the sail blew out."""
    rng = random.Random(seed); out = []
    for k in range(n):
        u = rng.uniform(0.05, 0.95); w = rng.uniform(0.15, 0.5); ln = length * rng.uniform(0.25, 1.0)
        p0 = Vector(a).lerp(Vector(b), u); d = (Vector(b) - Vector(a)).normalized()
        V = []; F = []; segs = 10
        for j in range(segs + 1):
            t = j / segs
            off = Vector(wind) * (0.9 * t * ln * 0.45) + Vector((0, 0, -ln * t)) + d * (math.sin(t * 3 + k) * 0.15 * t)
            tw = math.sin(t * 2.2 + k) * 0.6 * t
            side = (d * math.cos(tw) + Vector(wind).normalized() * math.sin(tw)) * (w / 2) * (1 - 0.7 * t)
            V += [p0 + off - side, p0 + off + side]
        for j in range(segs):
            F.append([2 * j, 2 * j + 1, 2 * j + 3, 2 * j + 2])
        o = mesh_obj(f"{name}_{k}", V, F, mat, coll=coll)
        uvl = o.data.uv_layers.new(name="UVMap")
        for l in o.data.loops:
            uvl.data[l.index].uv = (0.5 + (l.vertex_index % 2) * 0.05, l.vertex_index // 2 / segs)
        so = o.modifiers.new("Thick", "SOLIDIFY"); so.thickness = 0.004
        out.append(o)
    return out


def furled(name, a, b, r, mat, coll, sag=0.25, seed=1):
    """A sail furled on a spar: a lumpy roll lashed with gaskets."""
    rng = random.Random(seed)
    a = Vector(a); b = Vector(b); n = 28; V = []; F = []; m = 12
    d = (b - a); q = d.to_track_quat('Z', 'Y')
    for i in range(n + 1):
        t = i / n
        c = a.lerp(b, t) - Vector((0, 0, r * 0.9 + sag * 4 * t * (1 - t) * 0.2))
        rr = r * (0.55 + 0.45 * math.sin(math.pi * t) ** 0.5) * (1 + 0.18 * noise.noise(Vector((t * 9, seed, 0))))
        lash = 1 - 0.18 * (abs(math.sin(t * math.pi * 7)) ** 8)
        for k in range(m):
            ang = 2 * math.pi * k / m
            V.append(c + q @ Vector((math.cos(ang) * rr * lash, math.sin(ang) * rr * lash * 1.2, 0)))
    for i in range(n):
        for k in range(m):
            F.append([i * m + k, i * m + (k + 1) % m, (i + 1) * m + (k + 1) % m, (i + 1) * m + k])
    o = mesh_obj(name, V, F, mat, coll=coll)
    uvl = o.data.uv_layers.new(name="UVMap")
    for l in o.data.loops:
        uvl.data[l.index].uv = ((l.vertex_index % m) / m * 0.3, (l.vertex_index // m) / n)
    return o


def tri_sail(name, head, tack, clew, mat, coll, billow, wind, nu=16, nv=24, tear=None, seed=0):
    """Headsail (jib / staysail): triangle billowed downwind."""
    head, tack, clew = Vector(head), Vector(tack), Vector(clew)
    V = []; UV = []; F = []
    idx = {}
    for j in range(nv + 1):
        v = j / nv                      # 0 at head, 1 at foot
        for i in range(nu + 1):
            u = i / nu                  # 0 luff .. 1 leech
            p = head.lerp(tack.lerp(clew, u), v)
            bul = billow * math.sin(math.pi * u) * math.sin(math.pi * min(1, v * 0.95 + 0.05)) * v ** 0.4
            p = p + Vector(wind) * (bul + noise.noise(Vector((u * 5, v * 5, seed))) * 0.06 * billow)
            idx[(i, j)] = len(V); V.append(p); UV.append((u * v, v))
    for j in range(nv):
        for i in range(nu):
            if tear and tear((i + 0.5) / nu, (j + 0.5) / nv):
                continue
            F.append([idx[(i, j)], idx[(i + 1, j)], idx[(i + 1, j + 1)], idx[(i, j + 1)]])
    o = mesh_obj(name, V, F, mat, coll=coll)
    bpy.context.view_layer.objects.active = o
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bm.to_mesh(o.data); bm.free()
    uvl = o.data.uv_layers.new(name="UVMap")
    for l in o.data.loops:
        uvl.data[l.index].uv = UV[min(l.vertex_index, len(UV) - 1)]
    so = o.modifiers.new("Thick", "SOLIDIFY"); so.thickness = 0.004
    s = o.modifiers.new("Sub", "SUBSURF"); s.levels = 1; s.render_levels = 1
    return o


def build_sails(name, sp, mats, coll, state="found", wind=(0.25, -1.0, 0.0)):
    wind = Vector(wind).normalized()
    Y = sp["yards"]; fm = sp["fore"]
    can = mats["canvas"]; out = []
    def sq(nm, upper, lower, billow, tear=None, hang=0.0, seed=0, foot_in=0.0):
        a, b, _ = Y[upper]; c2, d2, _ = Y[lower] if lower in Y else (None, None, None)
        if lower in Y:
            bl, br = c2, d2
        else:
            bl = a + Vector((0, 0, -lower)) + (b - a) * -0.05; br = b + Vector((0, 0, -lower)) - (b - a) * -0.05
        tl = a.lerp(b, 0.03) - Vector((0, 0, 0.12)); tr = b.lerp(a, 0.03) - Vector((0, 0, 0.12))
        bl = bl.lerp(br, foot_in) + Vector((0, 0, 0.1)); br = br.lerp(bl, foot_in) + Vector((0, 0, 0.1))
        return sail_mesh(f"{name}_sail_{nm}", (tl, tr, br, bl), 26, 18, billow, wind, can, coll, tear=tear, seed=seed, hang=hang)
    if state == "full":
        out.append(sq("course", "course", 8.0, 1.2, seed=1))
        out.append(sq("ltop", "ltop", "course", 1.1, seed=2))
        out.append(sq("utop", "utop", "ltop", 1.0, seed=3))
        out.append(sq("tgal", "tgal", "utop", 0.8, seed=4))
        out.append(furled(f"{name}_royal_furl", Y["royal"][0], Y["royal"][1], 0.16, can, coll))
    else:
        # As found: fore course gone; lower fore-topsail set but torn; upper fore-topsail blown out (shreds);
        # topgallant and royal furled.
        rip = lambda u, v: (abs(u - 0.62 - 0.12 * math.sin(v * 7)) < 0.035 and v > 0.25) or (v > 0.86 and u > 0.55)
        out.append(sq("ltop", "ltop", "course", 2.3, tear=rip, hang=0.55, seed=5))
        # upper fore-topsail: the top half still bent to its yard, the rest blown out in rags
        ragged = lambda u, v: v > 0.42 + 0.18 * math.sin(u * 11.0) * math.sin(u * 3.7 + 1) + 0.1 * math.sin(u * 29)
        out.append(sq("utop", "utop", "ltop", 1.6, tear=ragged, hang=0.3, seed=8))
        a, b, _ = Y["utop"]
        out += shreds(f"{name}_utop_shred", a, b, 14, 5.2, can, coll, wind, seed=7)
        # fore course: torn loose, hanging from the fore yard by its corners, a long rip through the middle
        a2, b2, _ = Y["course"]
        hang_rip = lambda u, v: (abs(u - 0.45 - 0.08 * math.sin(v * 9)) < 0.03) or (v > 0.8 and 0.2 < u < 0.7)
        ca = a2 - Vector((0, 0, 0.1)); cb = b2 - Vector((0, 0, 0.1))
        out.append(sail_mesh(f"{name}_course_hanging", (ca, cb, cb - Vector((0, 0, 3.4)) + (a2 - b2) * 0.08, ca - Vector((0, 0, 3.4)) - (a2 - b2) * 0.08),
                             28, 20, 0.9, wind, can, coll, tear=hang_rip, seed=9, hang=2.2, flog=0.25))
        out.append(furled(f"{name}_tgal_furl", Y["tgal"][0], Y["tgal"][1], 0.2, can, coll, seed=2))
        out.append(furled(f"{name}_royal_furl", Y["royal"][0], Y["royal"][1], 0.15, can, coll, seed=3))
    # headsails: fore-topmast staysail and jib (both set when found)
    fore_top = sp["fore_tophead"]
    jtear = (lambda u, v: (u > 0.8 and v > 0.7 and (u + v * 0.3) % 0.12 < 0.05)) if state == "found" else None
    jt = sp["jibboom_end"] - Vector((0.8, 0, 0.05)); jh = fore_top.lerp(jt, 0.22)
    out.append(tri_sail(f"{name}_jib", jh, jt, jt.lerp(Vector((FORE_X + 4.5, -1.6, zdeck(FORE_X + 4.5) + 3.2)), 0.72),
                        can, coll, 2.0, wind, tear=jtear, seed=11))
    st = sp["bowsprit_end"] - Vector((1.4, 0, 0.1)); sh = fore_top.lerp(st, 0.12)
    out.append(tri_sail(f"{name}_fstay", sh, st, st.lerp(Vector((FORE_X + 1.0, -1.4, zdeck(FORE_X) + 2.2)), 0.8), can, coll, 1.7, wind, seed=12))
    # mainsail: set on the Dei Gratia, furled on the Mary Celeste
    g0, g1 = sp["boom"]; f0, f1 = sp["gaff"]
    if state == "full":
        out.append(sail_mesh(f"{name}_mainsail", (f0 + Vector((0, 0, -0.2)), f1 - Vector((0, 0, 0.15)), g1 + Vector((0.3, 0, 0.15)), g0 + Vector((0, 0, 0.2))),
                             24, 22, 1.2, wind, can, coll, seed=13))
    else:
        out.append(furled(f"{name}_main_furl", g0, g1, 0.32, can, coll, seed=4))
        out.append(furled(f"{name}_gaff_furl", f0, f1, 0.12, can, coll, seed=5))
    return out


def build_rigging(name, sp, mats, coll):
    rp = mats["rope"]; out = []
    fm, mm = sp["fore"], sp["main"]
    xs0, xb0 = _ends(1.0)
    def chain(x, sg):
        s = (x - xs0) / (xb0 - xs0); return Vector((x, sg * (half_breadth(s, 1.0) + 0.12), zdeck(x) + RAIL_H - 0.25))
    for m, nm in ((fm, "fore"), (mm, "main")):
        head = sp[nm + "_head"] - Vector((0, 0, 0.7))
        for sg in (1, -1):
            pts = []
            for k in range(4):
                x = m.x + 0.9 - k * 0.75
                c = chain(x, sg); h = head + Vector((0, sg * 0.25, 0))
                # deadeye pair with a laced lanyard at the channel; the shroud starts at the upper deadeye
                d = (h - c).normalized(); lo_ = c + d * 0.05; up_ = c + d * 0.42
                for q in (lo_, up_):
                    out.append(cyl(f"{name}_deadeye", q - d * 0.04, q + d * 0.04, 0.085, mat=mats["rail"], verts=18, coll=coll))
                sd = Vector((0, sg, 0)).cross(d).normalized() if abs(sg) else Vector((1, 0, 0))
                for k2 in (-1, 0, 1):
                    out.append(rope(f"{name}_lanyard", (lo_ + sd * 0.045 * k2 + d * 0.03, up_ + sd * 0.045 * k2 - d * 0.03), 0.008, rp, coll))
                out.append(rope(f"{name}_shroud", (up_ + d * 0.04, h), 0.022, rp, coll)); pts.append((up_, h))
            # ratlines
            for r in range(1, 30):
                f = r / 31
                if f > 0.9:
                    break
                P = [a.lerp(b, f) for a, b in pts]
                out.append(rope(f"{name}_ratline", P, 0.007, rp, coll))
            # topmast shrouds from the top's rim
            th = sp[nm + "_tophead"] - Vector((0, 0, 0.6)); rim = sp[nm + "_head"] - Vector((0, -sg * 1.5, 1.3))
            for k in range(3):
                out.append(rope(f"{name}_tshroud", (rim + Vector((0.4 - k * 0.4, 0, 0)), th), 0.015, rp, coll))
            # backstays to the hull
            out.append(rope(f"{name}_backstay", (sp[nm + "_tophead"], chain(m.x - 3.4, sg)), 0.02, rp, coll))
            if m.tg:
                out.append(rope(f"{name}_tgbackstay", (sp[nm + "_tghead"], chain(m.x - 4.6, sg)), 0.015, rp, coll))
    # stays
    out.append(rope(f"{name}_forestay", (sp["fore_head"], sp["bowsprit_root"] + Vector((1.2, 0, 0.3))), 0.035, rp, coll))
    out.append(rope(f"{name}_ftmstay", (sp["fore_tophead"], sp["bowsprit_end"]), 0.022, rp, coll))
    out.append(rope(f"{name}_jibstay", (sp["fore_tophead"] - Vector((0.2, 0, 0.3)), sp["jibboom_end"]), 0.02, rp, coll))
    out.append(rope(f"{name}_tgstay", (sp["fore_tghead"], sp["jibboom_end"] + Vector((-0.4, 0, 0))), 0.014, rp, coll))
    out.append(rope(f"{name}_mainstay", (sp["main_head"], fm.at(1.2) + Vector((0, 0, 0))), 0.03, rp, coll))
    out.append(rope(f"{name}_maintstay", (sp["main_tophead"], sp["fore_head"] + Vector((0, 0, 0.3))), 0.02, rp, coll))
    out.append(rope(f"{name}_martingale", (sp["jibboom_end"], sp["martingale"]), 0.015, rp, coll))
    out.append(rope(f"{name}_bobstay", (sp["bowsprit_end"] - Vector((0.6, 0, 0)), Vector((xb0 - 0.3, 0, 0.2))), 0.03, mats["iron"], coll))
    # yard lifts and braces
    for nm, (a, b, c) in sp["yards"].items():
        for e in (a, b):
            out.append(rope(f"{name}_lift", (e, fm.at(fm.lower + fm.top + 0.4) + Vector((0.5, 0, 0)) if nm != "royal" else sp["fore_tghead"]), 0.009, rp, coll))
            tgt = Vector((MAIN_X + 1.0, math.copysign(1.0, e.y) * 2.0, sp["main_head"].z - 1.0)) if nm in ("course", "ltop") else sp["main_tophead"]
            out.append(rope(f"{name}_brace", (e, tgt), 0.01, rp, coll, sag=0.35))
    # peak / throat halyards and topping lift
    g0, g1 = sp["boom"]; f0, f1 = sp["gaff"]
    out.append(rope(f"{name}_toplift", (g1, sp["main_head"]), 0.012, rp, coll))
    out.append(rope(f"{name}_peak", (f1, sp["main_head"] + Vector((0, 0, 0.5))), 0.012, rp, coll))
    out.append(rope(f"{name}_vang", (f1, Vector((-L / 2 + 1.5, -3.2, zdeck(-L / 2 + 1.5) + 1))), 0.009, rp, coll, sag=0.6))
    out.append(rope(f"{name}_sheet", (g1, Vector((-L / 2 + 1.4, 0, zdeck(-L / 2 + 1.4) + 0.3))), 0.016, rp, coll))
    return out


# ----------------------------------------------------------------------------- deck furniture
def build_fittings(name, mats, coll, hatches_off=True, boat_chocks=True):
    out = []; W = mats["deckwood"]; P = mats["lining"]
    def dz(x):
        return zdeck(x)
    # aft cabin trunk with skylight and companion
    x0 = -L / 2 + 3.2
    out.append(box(f"{name}_cabin", (x0 + 2.6, 0, dz(x0 + 2.6) + 0.42), (5.6, 4.4, 0.9), P, bevel=0.02, coll=coll))
    out.append(box(f"{name}_cabin_roof", (x0 + 2.6, 0, dz(x0 + 2.6) + 0.9), (5.8, 4.6, 0.07), W, bevel=0.01, coll=coll))
    out.append(box(f"{name}_skylight", (x0 + 2.2, 0, dz(x0 + 2.2) + 1.1), (1.3, 1.1, 0.35), mats["rail"], bevel=0.01, coll=coll))
    out.append(box(f"{name}_companion", (x0 + 4.7, 1.2, dz(x0 + 4.7) + 1.15), (0.9, 1.0, 0.6), P, bevel=0.01, coll=coll))
    # wheel and binnacle aft
    xw = -L / 2 + 1.7
    out.append(box(f"{name}_binnacle", (xw + 0.75, 0, dz(xw) + 0.55), (0.5, 0.5, 1.0), mats["rail"], bevel=0.02, coll=coll))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.62, minor_radius=0.035, location=(xw, 0, dz(xw) + 1.25), rotation=(0, math.pi / 2, 0))
    wh = bpy.context.active_object; wh.name = f"{name}_wheel"; wh.data.materials.append(mats["rail"]); _move(wh, coll); out.append(wh)
    for k in range(8):
        a = k * math.pi / 4
        p0 = Vector((xw, 0, dz(xw) + 1.25)); d = Vector((0, math.cos(a), math.sin(a)))
        out.append(cyl(f"{name}_spoke", p0, p0 + d * 0.82, 0.022, 0.016, mats["rail"], verts=8, coll=coll))
    out.append(box(f"{name}_wheelbox", (xw + 0.15, 0, dz(xw) + 0.6), (0.35, 0.9, 1.0), P, bevel=0.02, coll=coll))
    # main hatch (boat chocks on it), fore hatch, lazarette
    xm = MAIN_HATCH_X
    out.append(box(f"{name}_mainhatch_coaming", (xm, 0, dz(xm) + 0.22), (3.0, 2.6, 0.44), W, bevel=0.02, coll=coll))
    out.append(box(f"{name}_mainhatch_cover", (xm, 0, dz(xm) + 0.46), (2.9, 2.5, 0.06), W, bevel=0.01, coll=coll))
    for k in ((-1, 1) if boat_chocks else ()):
        out.append(box(f"{name}_boat_chock", (xm + k * 1.0, 0, dz(xm) + 0.62), (0.22, 2.0, 0.26), W, bevel=0.03, coll=coll))
    xf = FORE_X + 2.6
    out.append(box(f"{name}_forehatch_coaming", (xf, 0, dz(xf) + 0.2), (1.8, 1.8, 0.4), W, bevel=0.02, coll=coll))
    if hatches_off:
        out.append(box(f"{name}_forehatch_hole", (xf, 0, dz(xf) + 0.39), (1.55, 1.55, 0.05), mats["dark"], coll=coll))
        out.append(box(f"{name}_forehatch_cover", (xf + 1.9, 1.1, dz(xf + 1.9) + 0.04), (1.7, 1.7, 0.07), W, rot=(0, 0, 0.3), bevel=0.01, coll=coll))
    else:
        out.append(box(f"{name}_forehatch_cover", (xf, 0, dz(xf) + 0.42), (1.75, 1.75, 0.06), W, bevel=0.01, coll=coll))
    # galley / forecastle house between the masts
    xg = FORE_X - 3.4
    out.append(box(f"{name}_house", (xg, 0, dz(xg) + 0.95), (4.2, 3.4, 1.9), P, bevel=0.02, coll=coll))
    out.append(box(f"{name}_house_roof", (xg, 0, dz(xg) + 1.93), (4.4, 3.6, 0.07), W, bevel=0.01, coll=coll))
    out.append(cyl(f"{name}_stovepipe", (xg + 1.2, 0.8, dz(xg) + 1.9), (xg + 1.2, 0.8, dz(xg) + 2.7), 0.09, mat=mats["iron"], coll=coll))
    # pumps by the mainmast
    for sg in (1, -1):
        out.append(cyl(f"{name}_pump", (MAIN_X + 0.9, sg * 0.7, dz(MAIN_X)), (MAIN_X + 0.9, sg * 0.7, dz(MAIN_X) + 1.05), 0.12, mat=W, coll=coll))
    out.append(cyl(f"{name}_pumpbrake", (MAIN_X + 0.9, -1.4, dz(MAIN_X) + 1.15), (MAIN_X + 0.9, 1.4, dz(MAIN_X) + 1.15), 0.035, mat=W, coll=coll))
    # windlass at the bow
    xwl = _ends(1)[1] - 3.6
    out.append(cyl(f"{name}_windlass", (xwl, -1.3, dz(xwl) + 0.45), (xwl, 1.3, dz(xwl) + 0.45), 0.24, mat=W, verts=8, coll=coll))
    for sg in (1, -1):
        out.append(box(f"{name}_bitt", (xwl, sg * 1.45, dz(xwl) + 0.5), (0.3, 0.25, 1.0), W, bevel=0.02, coll=coll))
    # fife rails / pin rails at the masts
    for mx in (FORE_X, MAIN_X):
        out.append(box(f"{name}_fiferail", (mx + 0.4, 0, dz(mx) + 0.85), (1.2, 1.6, 0.08), W, bevel=0.01, coll=coll))
        for sg in (1, -1):
            out.append(box(f"{name}_fifepost", (mx + 0.4, sg * 0.75, dz(mx) + 0.42), (0.1, 0.1, 0.85), W, coll=coll))
    return out


def hull_detail(name, mats, coll):
    """Heavier hull: two rubbing strakes following the sheer, channels (chain-wale ledges) with deadeyes at the
    masts, catheads at the bow, quarter badges aft."""
    out = []; xs0, xb0 = _ends(1.0)
    wale = paint(name + "_wale", (0.32, 0.29, 0.24), rough=0.45, grime=0.6, chips=0.3)
    for sg in (1, -1):
        for dz, r in ((-0.18, 0.045), (-0.55, 0.035)):
            pts = []
            for i in range(60):
                x = xs0 + 0.4 + (xb0 - 0.8 - xs0) * i / 59; s_ = (x - xs0) / (xb0 - xs0)
                t = 1.0 + dz / (zdeck(x) + DRAFT)
                pts.append(Vector((x, sg * (half_breadth(s_, t) + 0.02), zdeck(x) + dz)))
            out.append(rope(f"{name}_strake", pts, r, wale if dz > -0.3 else mats["topside"], coll))
        for mx in (FORE_X, MAIN_X):
            s_ = (mx - xs0) / (xb0 - xs0); hb = half_breadth(s_, 1.0)
            z = zdeck(mx) + RAIL_H - 0.3
            out.append(box(f"{name}_channel", (mx - 0.35, sg * (hb + 0.2), z), (3.0, 0.32, 0.09), mats["rail"], bevel=0.01, coll=coll))
            for k in range(4):
                x = mx + 0.9 - k * 0.75
                out.append(cyl(f"{name}_deadeye", (x, sg * (hb + 0.12), z + 0.05), (x, sg * (hb + 0.24), z + 0.05), 0.08, mat=mats["rail"], verts=16, coll=coll))
                out.append(cyl(f"{name}_chainplate", (x, sg * (hb + 0.1), z - 0.02), (x, sg * (hb + 0.05), z - 0.75), 0.018, mat=mats["iron"], verts=8, coll=coll))
        x = xb0 - 2.0; s_ = (x - xs0) / (xb0 - xs0)
        out.append(box(f"{name}_cathead", (x, sg * (half_breadth(s_, 1.0) + 0.35), zdeck(x) + RAIL_H - 0.1), (0.3, 0.9, 0.3), mats["rail"], rot=(0, 0, sg * 0.5), bevel=0.02, coll=coll))
    return out


def bow_wave(name, coll, height=0.9, length=4.5):
    """White water piled against the stem and peeling off both bows (a curling foam sheet)."""
    m = bpy.data.materials.new(name + "_bowwave"); m.use_nodes = True
    N = m.node_tree.nodes; Lk = m.node_tree.links; p = N["Principled BSDF"]
    p.inputs['Base Color'].default_value = (0.85, 0.88, 0.88, 1); p.inputs['Roughness'].default_value = 0.45
    p.inputs['Subsurface Weight'].default_value = 0.4; p.inputs['Transmission Weight'].default_value = 0.25
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 9; nz.inputs['Detail'].default_value = 10
    Lk.new(tc.outputs['UV'], nz.inputs['Vector'])
    sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(tc.outputs['UV'], sep.inputs[0])
    edge = N.new("ShaderNodeMath"); edge.operation = 'SUBTRACT'; Lk.new(nz.outputs['Fac'], edge.inputs[0]); Lk.new(sep.outputs['Y'], edge.inputs[1])
    al = N.new("ShaderNodeMapRange"); al.inputs['From Min'].default_value = -0.35; al.inputs['From Max'].default_value = -0.1
    Lk.new(edge.outputs[0], al.inputs['Value']); Lk.new(al.outputs[0], p.inputs['Alpha'])
    out = []; xs0, xb0 = _ends(1.0)
    for sg in (1, -1):
        V = []; F = []; UV = []; nu, nv = 40, 8
        for i in range(nu + 1):
            u = i / nu; x = xb0 - 0.6 - length * u
            s_ = (x - xs0) / (xb0 - xs0); t = DRAFT / (zdeck(x) + DRAFT)
            hb = half_breadth(s_, t) + 0.05
            hh = height * (1 - u) ** 1.3 + 0.12
            for j in range(nv + 1):
                v = j / nv
                curl = 0.25 * (1 - u) * v ** 2
                V.append((x - 0.15 * v, sg * (hb + 0.08 + 0.55 * v * (0.4 + u) + curl), -0.1 + hh * math.sin(math.pi * 0.5 * v) - curl * 0.6))
                UV.append((u, v))
        for i in range(nu):
            for j in range(nv):
                a = i * (nv + 1) + j
                F.append([a, a + nv + 1, a + nv + 2, a + 1] if sg > 0 else [a, a + 1, a + nv + 2, a + nv + 1])
        o = mesh_obj(f"{name}_bowwave", V, F, m, coll=coll)
        uv = o.data.uv_layers.new(name="UVMap")
        for l in o.data.loops:
            uv.data[l.index].uv = UV[l.vertex_index]
        so = o.modifiers.new("Thick", "SOLIDIFY"); so.thickness = 0.03
        out.append(o)
    return out


def rail_section(name, mats, coll, gap, side="S", shift=0.0):
    """The section taken out of the bulwark, laid flat on the deck inboard of the gap: lining planks face up,
    the cap rail along its outboard edge, two iron pins at the foot."""
    x0, x1 = gap[0] + 0.05, gap[1] - 0.05; sg = 1 if side == "P" else -1
    xs0, xb0 = _ends(1.0)
    xc = (x0 + x1) / 2 + 0.25 + shift; s = (xc - xs0) / (xb0 - xs0); hb = half_breadth(s, 1.0)
    y = sg * (hb - 0.11 - RAIL_H / 2 - 0.55); z = zdeck(xc) + 0.012
    ln = x1 - x0; out = []
    rot = (0, 0, math.radians(4))
    # four boards with seams between them, painted on the face that was inboard (now up)
    nb = 4; bw = (RAIL_H - 0.02) / nb
    ca, sa = math.cos(rot[2]), math.sin(rot[2])
    for k in range(nb):
        off = -RAIL_H / 2 + bw / 2 + k * (bw + 0.006)
        out.append(box(f"{name}_railsec_board{k}", (xc - sg * off * sa, y + sg * off * ca, z + 0.034), (ln, bw - 0.004, 0.06),
                       mats["lining"], rot=rot, bevel=0.006, coll=coll))
    for k in (-1, 1):                                          # the stanchion stubs that held it, now on top
        out.append(box(f"{name}_railsec_batten", (xc + k * (ln / 2 - 0.12) * ca, y + k * (ln / 2 - 0.12) * sa, z + 0.085),
                       (0.11, RAIL_H - 0.06, 0.05), mats["lining"], rot=rot, bevel=0.008, coll=coll))
    out.append(box(f"{name}_railsec_back", (xc, y, z + 0.075), (ln - 0.02, RAIL_H - 0.02, 0.012), mats["topside"], rot=rot, coll=coll))
    o = out[-1]; o.location.z = z + 0.003                                  # black outboard face, now underneath
    cy = y + sg * RAIL_H / 2 * math.cos(rot[2]) ; cx = xc - sg * RAIL_H / 2 * math.sin(rot[2])
    out.append(box(f"{name}_railsec_cap", (cx, cy, z + 0.06), (ln + 0.04, 0.2, 0.12), mats["rail"], rot=rot, bevel=0.012, coll=coll))
    for k in (-1, 1):
        p = Vector((xc + k * (ln / 2 - 0.25), y - sg * (RAIL_H / 2 + 0.05), z + 0.04))
        out.append(cyl(f"{name}_railsec_pin", p, p + Vector((0, -sg * 0.18, 0)), 0.02, mat=mats["iron"], verts=10, coll=coll))
    # bolt holes through the battens and torn iron straps where it was fastened to the stanchions
    for k in (-1, 1):
        bx = xc + k * (ln / 2 - 0.12) * ca; by = y + k * (ln / 2 - 0.12) * sa
        for j in (-0.3, 0.0, 0.3):
            q = Vector((bx - sg * j * sa, by + sg * j * ca, z + 0.111))
            out.append(cyl(f"{name}_railsec_bolthole", q - Vector((0, 0, 0.004)), q + Vector((0, 0, 0.002)), 0.011, mat=mats["dark"], verts=12, coll=coll))
        q = Vector((bx + sg * 0.42 * sa, by - sg * 0.42 * ca, z + 0.112))
        strap = [q, q + Vector((0.02 * k, -sg * 0.09, 0.0)), q + Vector((0.05 * k, -sg * 0.16, 0.035)), q + Vector((0.06 * k, -sg * 0.19, 0.08))]
        o = rope(f"{name}_railsec_strap", strap, 0.006, mats["iron"], coll); o.data.bevel_resolution = 0
        o2 = rope(f"{name}_railsec_bolt", [q + Vector((0, sg * 0.05, 0)), q + Vector((0, sg * 0.05, 0.06)), q + Vector((0.03, sg * 0.07, 0.085))], 0.009, mats["iron"], coll)
        out += [o, o2]
    # the stumps either side of the gap: iron sockets in the waterway
    for xx in gap[:2]:
        s2 = (xx - xs0) / (xb0 - xs0); hb2 = half_breadth(s2, 1.0)
        out.append(box(f"{name}_gap_socket", (xx, sg * (hb2 - 0.06), zdeck(xx) + 0.03), (0.08, 0.1, 0.06), mats["iron"], coll=coll))
    return out


def build(name="ship", sails="found", rail_gap=None, wind=(0.25, -1.0, 0), coll_name=None, detail=True, wet=0.6,
          hatches_off=True, boat_chocks=True, bow_wave_h=0.0, rail_shift=0.0):
    coll = bpy.data.collections.new(coll_name or name); bpy.context.scene.collection.children.link(coll)
    mats = dict(
        bottom=paint(name + "_bottom", (0.2, 0.07, 0.04), rough=0.6, grime=0.5),
        boot=paint(name + "_boot", (0.5, 0.48, 0.42), rough=0.5, grime=0.6),
        topside=paint(name + "_topside", (0.012, 0.012, 0.013), rough=0.35, grime=0.25, wet=wet, chips=0.4, under=(0.2, 0.15, 0.1)),
        lining=(wood("weathered_planks", 1.1, wet=wet, tint=(0.62, 0.55, 0.46), name=name + "_lining") if detail
                else paint(name + "_lining", (0.2, 0.17, 0.13), rough=0.5, grime=0.65, wet=wet, chips=0.35, scale=9)),
        rail=wood("brown_planks_05", 1.2, wet=wet, name=name + "_rail") if detail else paint(name + "_rail", (0.12, 0.07, 0.035)),
        deck=wood("wood_floor_deck", 1.0, wet=wet, name=name + "_deckmat") if detail else paint(name + "_deckp", (0.3, 0.25, 0.18)),
        deckwood=wood("weathered_planks", 0.8, wet=wet, name=name + "_dw") if detail else paint(name + "_dwp", (0.25, 0.2, 0.15)),
        spar=paint(name + "_spar", (0.32, 0.22, 0.12), rough=0.5, grime=0.4, wet=wet * 0.5),
        canvas=canvas(name + "_canvas", wet=wet),
        rope=tarred_rope(name + "_rope"), iron=iron(name + "_iron"),
        dark=paint(name + "_dark", (0.01, 0.008, 0.006), rough=0.9, grime=0.0),
    )
    for k in ("deck",):
        # deck UVs are world-planar: scale the texture by UV instead of object coords
        pass
    hull = build_hull(name, mats, coll)
    parts = [hull] + bulwark(name, mats, coll, gap=rail_gap) + [deck(name, mats, coll)]
    parts += build_fittings(name, mats, coll, hatches_off=hatches_off, boat_chocks=boat_chocks)
    if rail_gap:
        parts += rail_section(name, mats, coll, rail_gap, rail_gap[2], shift=rail_shift)
    parts += hull_detail(name, mats, coll)
    if bow_wave_h:
        parts += bow_wave(name, coll, height=bow_wave_h)
    sp = build_spars(name, mats, coll)
    parts += build_sails(name, sp, mats, coll, state=sails, wind=wind)
    parts += build_rigging(name, sp, mats, coll)
    root = bpy.data.objects.new(name + "_root", None); coll.objects.link(root)
    for o in coll.objects:
        if o is not root and o.parent is None:
            o.parent = root
    return dict(root=root, coll=coll, mats=mats, spars=sp, hull=hull)
