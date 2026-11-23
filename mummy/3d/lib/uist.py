"""South Uist, Cladh Hallan: the machair coast and the excavation, in one seamless terrain.

World axes: +x east (inland, peat moor and hills), -x west (Atlantic), +y north. 1 unit = 1 m.
The dig is at the origin. The terrain grid is sinh-warped: ~8 cm spacing at the dig, ~10 m spacing 1 km out,
so close-ups in the trench and aerials over the coast use the same mesh (no seams, no swaps).

    T = island(mood="golden")        # terrain + sea + surf + sky + sun + grass near the dig; returns dict of handles
    T["h"](x, y)                     # ground height (m) of the undisturbed surface (before the excavation is cut)
"""
import math, os
import numpy as np
import bpy
from mathutils import Vector, Matrix
import ph

COAST_X = -260.0          # mean waterline
SITE_Z = 5.0
CUT = True                # False: the Bronze Age (no excavation)
DIG = dict(x0=-9.0, x1=10.0, y0=-15.5, y1=16.0, depth=1.6)     # open-area excavation (m)
# the three conjoined roundhouses (centre x, y, inner radius); entrances face east (+x). North house = burials.
HOUSES = [(0.0, -9.2, 4.3), (0.3, 0.0, 4.6), (0.0, 9.6, 4.4)]
HOUSE_SINK = 0.32         # house floors are sunk into the sand below the excavated surface
# grave pits under the north house floor: (x, y, half-length, half-width, depth, angle deg). B1 = the man, B2 = the second adult
PIT_CUT = {"B1": (0.24, 0.66, 1.0), "B2": (-0.23, 0.62, 0.95)}   # (offset along the pit axis, a, b): hides the pot corner
PITS = {"B1": (-1.8, 8.9, 0.86, 0.95, 0.5, 20.0), "B2": (-0.3, 11.6, 0.82, 0.9, 0.5, 150.0),
        "KNEE": (3.2, 14.6, 0.45, 0.38, 0.28, 0.0)}        # knee pit: outside the house, ~5 m from B2


# ----------------------------------------------------------------------------- numpy value noise
def _hash(ix, iy, seed):
    h = (ix * 374761393 + iy * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def vnoise(x, y, seed=0):
    ix = np.floor(x).astype(np.int64); iy = np.floor(y).astype(np.int64)
    fx = x - ix; fy = y - iy
    ux = fx * fx * (3 - 2 * fx); uy = fy * fy * (3 - 2 * fy)
    a = _hash(ix, iy, seed); b = _hash(ix + 1, iy, seed); c = _hash(ix, iy + 1, seed); d = _hash(ix + 1, iy + 1, seed)
    return (a + (b - a) * ux) + ((c + (d - c) * ux) - (a + (b - a) * ux)) * uy


def fbm(x, y, octaves=5, seed=0, lac=2.03, gain=0.5):
    s = 0.0; amp = 1.0; f = 1.0; norm = 0.0
    for o in range(octaves):
        s = s + amp * (vnoise(x * f, y * f, seed + o * 17) - 0.5); norm += amp
        amp *= gain; f *= lac
    return s / norm * 2


def _smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ----------------------------------------------------------------------------- landform
def coast_x(y):
    return COAST_X + 35 * fbm(y / 400.0, 0.3, 3, seed=3) + 18 * np.sin(y / 230.0)


def surface(x, y, cut=None):
    """Undisturbed ground height. Sea floor < 0 < beach < dunes < machair < moor/hills."""
    x = np.asarray(x, np.float64); y = np.asarray(y, np.float64)
    cx = coast_x(y); d = x - cx                     # metres inland from the waterline
    beach = np.where(d < 0, np.maximum(d * 0.035, -9.0), 1.8 * _smooth(0, 60, d))   # gentle shelving beach
    # dune ridge 60..150 m inland: hummocky marram dunes with blowouts
    ridge = _smooth(40, 75, d) * (1 - _smooth(120, 175, d))
    hum = 0.55 + 0.45 * fbm(x / 38.0, y / 26.0, 4, seed=11)
    blow = 1 - 0.6 * _smooth(0.25, 0.5, fbm(x / 70.0, y / 55.0, 2, seed=21))
    dunes = ridge * (9.0 * hum * blow + 2.5 * fbm(x / 9.0, y / 7.0, 3, seed=5))
    # machair plain behind the dunes: low, flat, slightly undulating (~3.5-5 m)
    mach = _smooth(60, 160, d) * (3.6 + 0.9 * fbm(x / 120.0, y / 120.0, 4, seed=7) + 0.25 * fbm(x / 14.0, y / 14.0, 3, seed=8))
    # peat moor and hills to the east (Beinn Mhor / Hecla read as a far wall of hills)
    moor = _smooth(700, 1400, x) * (12 + 25 * (0.5 + fbm(x / 400.0, y / 300.0, 5, seed=31)))
    hills = _smooth(1600, 3200, x) * (260 * (0.55 + 0.6 * fbm(x / 900.0, y / 700.0, 6, seed=41)))
    h = np.where(d < 60, beach + dunes, np.maximum(beach, 0) + dunes + mach) + moor + hills
    h = h + _smooth(0, 30, d) * 0.12 * fbm(x / 2.2, y / 2.2, 3, seed=9)      # small-scale lumps on land
    # lochans on the machair (shallow, filled by the loch planes)
    for lx, ly, r in ((420, 260, 90), (560, -320, 140), (300, -520, 70)):
        rr = np.hypot((x - lx) / r, (y - ly) / (r * 0.7))
        h = h - 2.2 * (1 - _smooth(0.6, 1.1, rr))
    # the dig site sits on a low rise of the machair: flatten a working area around it
    near = 1 - _smooth(18, 90, np.hypot(x, y))
    h = h * (1 - near) + near * (SITE_Z + 0.06 * fbm(x / 3, y / 3, 2, seed=13))
    if (CUT if cut is None else cut):
        h = h - _cut(x, y)
    return h


def _cut(x, y):
    """Excavated depth: open area with steep sections, a step (bench) on the north side, and spoil-free floor."""
    D = DIG
    ex = np.minimum(x - D["x0"], D["x1"] - x); ey = np.minimum(y - D["y0"], D["y1"] - y)
    e = np.minimum(ex, ey)                          # distance inside the edge (m)
    wall = _smooth(-0.02, 0.10, e)                  # near-vertical section faces (10 cm run)
    floor_var = 0.03 * fbm(x / 1.6, y / 1.6, 3, seed=17) + 0.008 * fbm(x / 0.35, y / 0.35, 2, seed=18)
    depth = D["depth"] + floor_var
    # a 1 m bench half way down along the north and east sides (safety step, as dug)
    bench = _smooth(0.95, 1.05, e)
    dd = wall * (0.55 + 0.45 * bench) * depth
    for hx, hy, r in HOUSES:          # sunken house floors, revetted edges (stones placed by dig.houses)
        rr = np.hypot(x - hx, y - hy)
        dd = dd + wall * HOUSE_SINK * (1 - _smooth(r - 0.12, r + 0.05, rr))
    for key, (px, py, a, b, dep, ang) in PITS.items():
        c, s_ = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        if key in PIT_CUT:                      # the cut is offset/narrowed (the trench floor covers part of a scan)
            du, a, b = PIT_CUT[key]
            px, py = px + du * c, py + du * s_
        u = ((x - px) * c + (y - py) * s_) / a; v = (-(x - px) * s_ + (y - py) * c) / b
        e = np.hypot(u, v)
        bowl = (1 - _smooth(0.86, 1.03, e)) if key in ("B1", "B2") else (1 - _smooth(0.55, 1.0, e))   # scanned graves: cut to fit
        dd = dd + wall * dep * bowl
    return np.maximum(dd, 0)


# ----------------------------------------------------------------------------- mesh
def _warp(n, half, core=6.0):
    k = math.asinh(half / core)
    u = np.linspace(-1, 1, n)
    return core * np.sinh(k * u)


def terrain_mesh(n=900, half=2600.0, name="Uist", focus=(0.0, 0.0), core=6.0):
    """focus: the point the grid is densest around (the dig for ground shots, the coast under a drone)."""
    xs = _warp(n, half, core) + focus[0]; ys = _warp(n, half, core) + focus[1]
    X, Y = np.meshgrid(xs, ys)
    Z = surface(X, Y)
    verts = np.stack([X, Y, Z], -1).reshape(-1, 3).astype(np.float32)
    idx = np.arange(n * n).reshape(n, n)
    a = idx[:-1, :-1].ravel(); b = idx[:-1, 1:].ravel(); c = idx[1:, 1:].ravel(); d = idx[1:, :-1].ravel()
    quads = np.stack([a, b, c, d], -1).astype(np.int32)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(verts)); me.vertices.foreach_set("co", verts.ravel())
    nl = len(quads) * 4
    me.loops.add(nl); me.loops.foreach_set("vertex_index", quads.ravel())
    me.polygons.add(len(quads)); me.polygons.foreach_set("loop_start", np.arange(0, nl, 4, dtype=np.int32))
    me.polygons.foreach_set("use_smooth", np.ones(len(quads), bool))
    me.update(calc_edges=True)
    # per-vertex fields the material reads: inland distance, excavated depth
    dcoast = (X - coast_x(Y)).ravel().astype(np.float32)
    cut = (_cut(X, Y) if CUT else np.zeros_like(X)).ravel().astype(np.float32)
    for nm, arr in (("inland", dcoast), ("cut", cut)):
        at = me.attributes.new(nm, 'FLOAT', 'POINT'); at.data.foreach_set("value", arr)
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    return o


# ----------------------------------------------------------------------------- materials
def _n(nt, kind, **kw):
    n = nt.nodes.new(kind)
    for k, v in kw.items():
        if k in n.inputs:
            n.inputs[k].default_value = v
        else:
            setattr(n, k, v)
    return n


def _ph_maps(aid, res="2k"):
    f = ph._files(aid); d = os.path.join(ph.ROOT, aid); out = {}
    for key in ("Diffuse", "nor_gl", "Rough", "Displacement"):
        if key in f and res in f[key]:
            info = f[key][res].get("jpg") or f[key][res].get("png")
            if info:
                out[key] = ph._get(info["url"], os.path.join(d, os.path.basename(info["url"])))
    return out


def _tex_set(nt, aid, vec, res="2k"):
    """Image nodes (colour, roughness, normal height-ish) for a Poly Haven texture at mapping `vec`."""
    mp = _ph_maps(aid, res); r = {}
    for key, path in mp.items():
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
        t.image.colorspace_settings.name = 'sRGB' if key == "Diffuse" else 'Non-Color'
        t.projection = 'BOX'; t.projection_blend = 0.25            # no vertical stretching on section faces
        nt.links.new(vec, t.inputs['Vector']); r[key] = t
    return r


def fog_wrap(m, color=(0.62, 0.66, 0.7), density=0.0011, max_fac=0.85):
    """Aerial perspective: camera rays fade into `color` with distance (cheap; no volume)."""
    nt = m.node_tree; N = nt.nodes; L = nt.links
    out = [n for n in N if n.type == 'OUTPUT_MATERIAL'][0]
    src = out.inputs['Surface'].links[0].from_socket
    cam = _n(nt, "ShaderNodeCameraData")
    k = _n(nt, "ShaderNodeMath", operation='MULTIPLY'); k.inputs[1].default_value = -density
    L.new(cam.outputs['View Distance'], k.inputs[0])
    ex = _n(nt, "ShaderNodeMath", operation='EXPONENT'); L.new(k.outputs[0], ex.inputs[0])
    inv = _n(nt, "ShaderNodeMath", operation='SUBTRACT'); inv.inputs[0].default_value = max_fac; L.new(ex.outputs[0], inv.inputs[1])
    cl = _n(nt, "ShaderNodeMath", operation='MAXIMUM'); cl.inputs[1].default_value = 0.0; L.new(inv.outputs[0], cl.inputs[0])
    lp = _n(nt, "ShaderNodeLightPath")
    g = _n(nt, "ShaderNodeMath", operation='MULTIPLY'); L.new(cl.outputs[0], g.inputs[0]); L.new(lp.outputs['Is Camera Ray'], g.inputs[1])
    em = _n(nt, "ShaderNodeEmission"); em.inputs['Color'].default_value = (*color, 1); em.inputs['Strength'].default_value = 1.0
    mx = _n(nt, "ShaderNodeMixShader"); L.new(g.outputs[0], mx.inputs['Fac']); L.new(src, mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs['Surface'])
    m["fog_emission"] = em.name
    return em


STRATA = [  # (depth below surface m, colour) top-down: turf, blown shell sand, occupation floors, ploughsoil, burial horizon
    (0.00, (0.06, 0.05, 0.03)), (0.07, (0.08, 0.06, 0.04)), (0.085, (0.78, 0.72, 0.58)), (0.30, (0.82, 0.76, 0.62)),
    (0.315, (0.09, 0.07, 0.05)), (0.36, (0.10, 0.08, 0.06)), (0.375, (0.76, 0.70, 0.56)), (0.58, (0.80, 0.74, 0.60)),
    (0.595, (0.14, 0.11, 0.08)), (0.66, (0.05, 0.04, 0.03)), (0.675, (0.74, 0.68, 0.55)), (0.89, (0.78, 0.72, 0.58)),
    (0.905, (0.20, 0.15, 0.10)), (0.96, (0.22, 0.17, 0.11)), (0.975, (0.80, 0.74, 0.60)), (1.15, (0.82, 0.76, 0.62)),
    (1.165, (0.11, 0.09, 0.06)), (1.26, (0.07, 0.06, 0.04)), (1.275, (0.72, 0.65, 0.52)), (1.52, (0.75, 0.68, 0.55)),
    (1.535, (0.30, 0.24, 0.17)), (1.8, (0.24, 0.19, 0.13)),
]


def ground_material(fog=None, grass_tint=(0.22, 0.27, 0.09)):
    """One material for the whole island: wet/dry sand, marram dunes, machair turf, moor; strata on cut faces."""
    m = bpy.data.materials.new("UistGround"); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    p = N["Principled BSDF"]; p.inputs['Roughness'].default_value = 0.9
    tc = _n(nt, "ShaderNodeTexCoord")
    geo = _n(nt, "ShaderNodeNewGeometry")
    sep = _n(nt, "ShaderNodeSeparateXYZ"); L.new(geo.outputs['Position'], sep.inputs[0])
    nsep = _n(nt, "ShaderNodeSeparateXYZ"); L.new(geo.outputs['Normal'], nsep.inputs[0])
    inl = _n(nt, "ShaderNodeAttribute", attribute_name="inland")
    cut = _n(nt, "ShaderNodeAttribute", attribute_name="cut")
    def mapping(scale):
        mp = _n(nt, "ShaderNodeMapping"); mp.inputs['Scale'].default_value = (scale, scale, scale)
        L.new(tc.outputs['Object'], mp.inputs['Vector']); return mp.outputs[0]
    sand = _tex_set(nt, "dense_sand", mapping(0.5))
    grass = _tex_set(nt, "leafy_grass", mapping(0.35))
    marr = _tex_set(nt, "withered_grass", mapping(0.3))
    wsand = _tex_set(nt, "damp_beach_sand", mapping(0.4))
    soil = _tex_set(nt, "excavated_soil_wall", mapping(0.6))
    # large-scale breakup noise
    nz = _n(nt, "ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 0.02; nz.inputs['Detail'].default_value = 6
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    nz2 = _n(nt, "ShaderNodeTexNoise"); nz2.inputs['Scale'].default_value = 0.25; nz2.inputs['Detail'].default_value = 8
    L.new(tc.outputs['Object'], nz2.inputs['Vector'])

    def mixc(fac, a, b):
        mx = _n(nt, "ShaderNodeMix", data_type='RGBA'); L.new(fac, mx.inputs['Factor'])
        (L.new(a, mx.inputs[6]) if not isinstance(a, tuple) else setattr(mx.inputs[6], 'default_value', (*a, 1)))
        (L.new(b, mx.inputs[7]) if not isinstance(b, tuple) else setattr(mx.inputs[7], 'default_value', (*b, 1)))
        return mx.outputs[2]

    def ramp(src, stops):
        r = _n(nt, "ShaderNodeValToRGB"); el = r.color_ramp.elements
        el[0].position, el[0].color = stops[0][0], (*stops[0][1], 1)
        el[1].position, el[1].color = stops[-1][0], (*stops[-1][1], 1)
        for pos, col in stops[1:-1]:
            e = el.new(pos); e.color = (*col, 1)
        L.new(src, r.inputs['Fac']); return r

    def fac(src, a, b):
        mr = _n(nt, "ShaderNodeMapRange"); mr.inputs['From Min'].default_value = a; mr.inputs['From Max'].default_value = b
        L.new(src, mr.inputs['Value']); return mr.outputs[0]

    def mul(a, b):
        mm = _n(nt, "ShaderNodeMath", operation='MULTIPLY'); L.new(a, mm.inputs[0]); L.new(b, mm.inputs[1]); return mm.outputs[0]

    # inland distance with noise wobble (so the zones do not follow contour lines)
    wob = _n(nt, "ShaderNodeMath", operation='MULTIPLY_ADD'); L.new(nz.outputs['Fac'], wob.inputs[0])
    wob.inputs[1].default_value = 60; wob.inputs[2].default_value = -30
    d = _n(nt, "ShaderNodeMath", operation='ADD'); L.new(inl.outputs['Fac'], d.inputs[0]); L.new(wob.outputs[0], d.inputs[1])
    # wet sand -> dry sand -> marram dune (sand showing through) -> machair turf -> moor
    dry = fac(d.outputs[0], 4, 14); dune = fac(d.outputs[0], 45, 70); mach = fac(d.outputs[0], 150, 190); moor = fac(sep.outputs['X'], 650, 1100)
    tint_sand = _n(nt, "ShaderNodeMix", data_type='RGBA', blend_type='MULTIPLY'); tint_sand.inputs['Factor'].default_value = 1
    L.new(sand["Diffuse"].outputs['Color'], tint_sand.inputs[6]); tint_sand.inputs[7].default_value = (1.25, 1.18, 1.02, 1)   # pale shell sand
    c = mixc(dry, wsand["Diffuse"].outputs['Color'], tint_sand.outputs[2])
    marram = _n(nt, "ShaderNodeMix", data_type='RGBA', blend_type='MULTIPLY'); marram.inputs['Factor'].default_value = 1
    L.new(grass["Diffuse"].outputs['Color'], marram.inputs[6]); marram.inputs[7].default_value = (0.82, 0.9, 0.6, 1)       # straw-green marram
    patch = fac(nz2.outputs['Fac'], 0.30, 0.44)
    dune_col = mixc(patch, tint_sand.outputs[2], marram.outputs[2])
    c = mixc(dune, c, dune_col)
    turf = _n(nt, "ShaderNodeMix", data_type='RGBA', blend_type='MULTIPLY'); turf.inputs['Factor'].default_value = 1
    L.new(grass["Diffuse"].outputs['Color'], turf.inputs[6]); turf.inputs[7].default_value = (0.85, 1.0, 0.62, 1)
    # machair strip fields: long narrow strips (NE-SW), each a different crop/fallow tint, soft edges
    rot = _n(nt, "ShaderNodeMapping"); rot.inputs['Rotation'].default_value = (0, 0, 0.5)
    rot.inputs['Scale'].default_value = (1 / 34.0, 1 / 240.0, 1)
    L.new(tc.outputs['Object'], rot.inputs['Vector'])
    vor = _n(nt, "ShaderNodeTexVoronoi"); vor.inputs['Randomness'].default_value = 0.35; L.new(rot.outputs[0], vor.inputs['Vector'])
    strip = ramp(vor.outputs['Color'], [(0.0, (1.0, 1.0, 1.0)), (0.25, (1.0, 1.0, 1.0)), (0.32, (1.15, 1.05, 0.6)), (0.45, (1.15, 1.05, 0.6)),
                                         (0.52, (0.8, 0.95, 0.75)), (0.66, (0.8, 0.95, 0.75)), (0.72, (0.9, 0.75, 0.55)), (0.8, (0.9, 0.75, 0.55)),
                                         (0.86, (1.05, 1.1, 0.7)), (1.0, (1.05, 1.1, 0.7))])
    # sheep-grazed mottling and flower drifts (yellow/white specks read as colour at distance)
    mot = _n(nt, "ShaderNodeTexNoise"); mot.inputs['Scale'].default_value = 0.6; mot.inputs['Detail'].default_value = 6
    L.new(tc.outputs['Object'], mot.inputs['Vector'])
    motr = ramp(mot.outputs['Fac'], [(0.35, (0.85, 0.9, 0.8)), (0.65, (1.12, 1.08, 0.85))])
    tf = _n(nt, "ShaderNodeMix", data_type='RGBA', blend_type='MULTIPLY'); tf.inputs['Factor'].default_value = 1
    L.new(turf.outputs[2], tf.inputs[6]); L.new(strip.outputs['Color'], tf.inputs[7])
    tf2 = _n(nt, "ShaderNodeMix", data_type='RGBA', blend_type='MULTIPLY'); tf2.inputs['Factor'].default_value = 1
    L.new(tf.outputs[2], tf2.inputs[6]); L.new(motr.outputs['Color'], tf2.inputs[7])
    farm = fac(d.outputs[0], 220, 300)            # strips start a little back from the dunes
    turf_c = mixc(farm, turf.outputs[2], tf2.outputs[2])
    c = mixc(mach, c, turf_c)
    c = mixc(moor, c, (0.09, 0.075, 0.045))
    # excavated surfaces: floor sand + strata on the faces
    zrel = _n(nt, "ShaderNodeMath", operation='SUBTRACT'); zrel.inputs[0].default_value = SITE_Z
    warp = _n(nt, "ShaderNodeTexNoise"); warp.inputs['Scale'].default_value = 0.9; warp.inputs['Detail'].default_value = 4
    L.new(tc.outputs['Object'], warp.inputs['Vector'])
    zw = _n(nt, "ShaderNodeMath", operation='MULTIPLY_ADD'); L.new(warp.outputs['Fac'], zw.inputs[0]); zw.inputs[1].default_value = 0.05
    L.new(sep.outputs['Z'], zw.inputs[2])
    L.new(zw.outputs[0], zrel.inputs[1])
    stmax = STRATA[-1][0]
    zn = _n(nt, "ShaderNodeMath", operation='DIVIDE'); L.new(zrel.outputs[0], zn.inputs[0]); zn.inputs[1].default_value = stmax
    st = ramp(zn.outputs[0], [(dd / stmax, col) for dd, col in STRATA])
    st.color_ramp.interpolation = 'LINEAR'
    grain = _n(nt, "ShaderNodeMix", data_type='RGBA', blend_type='SOFT_LIGHT'); grain.inputs['Factor'].default_value = 0.12
    L.new(st.outputs['Color'], grain.inputs[6]); L.new(soil["Diffuse"].outputs['Color'], grain.inputs[7])
    iscut = fac(cut.outputs['Fac'], 0.01, 0.06)
    steep = fac(nsep.outputs['Z'], 0.75, 0.45)
    face = mul(iscut, steep)
    floor_col = _n(nt, "ShaderNodeMix", data_type='RGBA', blend_type='MULTIPLY'); floor_col.inputs['Factor'].default_value = 1
    L.new(sand["Diffuse"].outputs['Color'], floor_col.inputs[6]); floor_col.inputs[7].default_value = (0.74, 0.71, 0.66, 1)
    occ = _n(nt, "ShaderNodeTexNoise"); occ.inputs['Scale'].default_value = 0.35; occ.inputs['Detail'].default_value = 6
    occ.inputs['Roughness'].default_value = 0.65; L.new(tc.outputs['Object'], occ.inputs['Vector'])
    occr = ramp(occ.outputs['Fac'], [(0.38, (1.0, 1.0, 1.0)), (0.5, (0.78, 0.72, 0.62)), (0.62, (0.42, 0.36, 0.3)), (0.7, (0.3, 0.26, 0.22))])
    fl2 = _n(nt, "ShaderNodeMix", data_type='RGBA', blend_type='MULTIPLY'); fl2.inputs['Factor'].default_value = 1
    L.new(floor_col.outputs[2], fl2.inputs[6]); L.new(occr.outputs['Color'], fl2.inputs[7])
    c = mixc(iscut, c, fl2.outputs[2])
    c = mixc(face, c, grain.outputs[2])
    L.new(c, p.inputs['Base Color'])
    # normals: sand/grass/soil normal maps by zone
    nm = _n(nt, "ShaderNodeNormalMap"); nm.inputs['Strength'].default_value = 0.35
    nmix = mixc(mach, sand["nor_gl"].outputs['Color'], grass["nor_gl"].outputs['Color'])
    nmix = mixc(face, nmix, sand["nor_gl"].outputs['Color'])
    L.new(nmix, nm.inputs['Color']); L.new(nm.outputs[0], p.inputs['Normal'])
    rough = mixc(dry, (0.35, 0.35, 0.35), (0.92, 0.92, 0.92))
    L.new(rough, p.inputs['Roughness'])
    if fog:
        fog_wrap(m, **fog)
    return m


# ----------------------------------------------------------------------------- sea, surf, lochs
def sea(fog=None, wind=9.0, choppy=1.2):
    import sea as SEA
    mat = SEA.water_material("Atlantic", deep=(0.002, 0.02, 0.03), crest=(0.01, 0.12, 0.11), fog_color=(0.5, 0.56, 0.6))
    o = SEA.ocean(size=200.0, res=20, scale=0.9, chop=choppy, wind=wind, seed=4, repeat=4, foam=0.35, mat=mat,
                  loc=(COAST_X - 300, 0, -0.05))
    far = SEA.far_sea(380.0, r1=12000.0, mat=mat, z=-0.08, center=(COAST_X - 300, 0))
    if fog:
        for oo in (o, far):
            fog_wrap(oo.data.materials[0], **fog)
    return o, far


def surf(rows=5, y0=-2600, y1=2600, seed=1):
    """White water along the beach: bands of foam parallel to the waterline, broken by noise (alpha)."""
    ys = np.linspace(y0, y1, 1200); V = []; F = []
    w = 70.0
    for i, y in enumerate(ys):
        cx = float(coast_x(y))
        V += [(cx - w, y, 0.06), (cx + 6, y, 0.06)]
        if i:
            a = 2 * (i - 1); F.append([a, a + 2, a + 3, a + 1])
    me = bpy.data.meshes.new("Surf"); me.from_pydata(V, [], F); me.update()
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index; uv.data[li].uv = ((vi % 2), (vi // 2) / len(ys))
    o = bpy.data.objects.new("Surf", me); bpy.context.collection.objects.link(o)
    m = bpy.data.materials.new("Surf"); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    p = N["Principled BSDF"]; p.inputs['Base Color'].default_value = (0.85, 0.88, 0.88, 1); p.inputs['Roughness'].default_value = 0.6
    uvn = _n(nt, "ShaderNodeUVMap")
    sp = _n(nt, "ShaderNodeSeparateXYZ"); L.new(uvn.outputs[0], sp.inputs[0])
    # bands across U (distance from shore) with along-shore breakup
    mp = _n(nt, "ShaderNodeMapping"); mp.inputs['Scale'].default_value = (1, 160, 1); L.new(uvn.outputs[0], mp.inputs['Vector'])
    wav = _n(nt, "ShaderNodeTexWave"); wav.wave_type = 'BANDS'; wav.bands_direction = 'X'
    wav.inputs['Scale'].default_value = rows * 0.5; wav.inputs['Distortion'].default_value = 6; wav.inputs['Detail'].default_value = 4
    wav.inputs['Detail Scale'].default_value = 2.5
    L.new(mp.outputs[0], wav.inputs['Vector'])
    nz = _n(nt, "ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 9; nz.inputs['Detail'].default_value = 10
    L.new(mp.outputs[0], nz.inputs['Vector'])
    a = _n(nt, "ShaderNodeMath", operation='MULTIPLY'); L.new(wav.outputs['Fac'], a.inputs[0]); L.new(nz.outputs['Fac'], a.inputs[1])
    th = _n(nt, "ShaderNodeMapRange"); th.inputs['From Min'].default_value = 0.42; th.inputs['From Max'].default_value = 0.6
    L.new(a.outputs[0], th.inputs['Value'])
    shore = _n(nt, "ShaderNodeMapRange"); shore.inputs['From Min'].default_value = 0.0; shore.inputs['From Max'].default_value = 0.85
    L.new(sp.outputs['X'], shore.inputs['Value'])
    al = _n(nt, "ShaderNodeMath", operation='MULTIPLY'); L.new(th.outputs[0], al.inputs[0]); L.new(shore.outputs[0], al.inputs[1])
    L.new(al.outputs[0], p.inputs['Alpha'])
    o.data.materials.append(m)
    o.visible_shadow = False
    return o


def lochs():
    m = bpy.data.materials.new("Loch"); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (0.01, 0.015, 0.02, 1); p.inputs['Roughness'].default_value = 0.04
    out = []
    for lx, ly, r in ((420, 260, 90), (560, -320, 140), (300, -520, 70)):
        z = float(surface(lx, ly)) + 1.0
        bpy.ops.mesh.primitive_circle_add(vertices=48, radius=r * 1.25, fill_type='NGON', location=(lx, ly, z))
        o = bpy.context.active_object; o.name = "Loch"; o.scale = (1, 0.7, 1); o.data.materials.append(m); out.append(o)
    return out


# ----------------------------------------------------------------------------- vegetation (geometry nodes scatter)
_GRASS = None


def grass_collection():
    """Poly Haven grass clumps, re-tinted: machair turf (short) and marram (tall, straw)."""
    global _GRASS
    if _GRASS:
        return _GRASS
    col = bpy.data.collections.new("GrassSrc")
    hidden = []
    for aid in ("grass_medium_01", "grass_medium_02"):
        root, ms = ph.model(aid, loc=(0, 0, -500))
        for o in ms:
            for c in o.users_collection:
                c.objects.unlink(o)
            col.objects.link(o); o.location = (0, 0, 0); o.parent = None; o.matrix_world.identity()
            hidden.append(o)
        bpy.data.objects.remove(root)
    _GRASS = col
    return col


def scatter(target, center, radius, density=40.0, zone=(150, 1e9), scale=(0.7, 1.3), seed=0, name="Grass", avoid_cut=None):
    avoid_cut = CUT if avoid_cut is None else avoid_cut
    """Instance grass on `target` within `radius` of `center` (x, y) where inland distance is in `zone`."""
    col = grass_collection()
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = ng.nodes; L = ng.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    pos = N.new("GeometryNodeInputPosition")
    cen = N.new("FunctionNodeInputVector"); cen.vector = (center[0], center[1], 0)
    sub = N.new("ShaderNodeVectorMath"); sub.operation = 'SUBTRACT'; L.new(pos.outputs[0], sub.inputs[0]); L.new(cen.outputs[0], sub.inputs[1])
    mulz = N.new("ShaderNodeVectorMath"); mulz.operation = 'MULTIPLY'; mulz.inputs[1].default_value = (1, 1, 0)
    L.new(sub.outputs[0], mulz.inputs[0])
    ln = N.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; L.new(mulz.outputs[0], ln.inputs[0])
    inr = N.new("ShaderNodeMath"); inr.operation = 'LESS_THAN'; inr.inputs[1].default_value = radius; L.new(ln.outputs['Value'], inr.inputs[0])
    inl = N.new("GeometryNodeInputNamedAttribute"); inl.data_type = 'FLOAT'; inl.inputs['Name'].default_value = "inland"
    z0 = N.new("ShaderNodeMath"); z0.operation = 'GREATER_THAN'; z0.inputs[1].default_value = zone[0]; L.new(inl.outputs['Attribute'], z0.inputs[0])
    z1 = N.new("ShaderNodeMath"); z1.operation = 'LESS_THAN'; z1.inputs[1].default_value = zone[1]; L.new(inl.outputs['Attribute'], z1.inputs[0])
    m1 = N.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; L.new(inr.outputs[0], m1.inputs[0]); L.new(z0.outputs[0], m1.inputs[1])
    m2 = N.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'; L.new(m1.outputs[0], m2.inputs[0]); L.new(z1.outputs[0], m2.inputs[1])
    sel = m2.outputs[0]
    if avoid_cut:
        ct = N.new("GeometryNodeInputNamedAttribute"); ct.data_type = 'FLOAT'; ct.inputs['Name'].default_value = "cut"
        nc = N.new("ShaderNodeMath"); nc.operation = 'LESS_THAN'; nc.inputs[1].default_value = 0.005; L.new(ct.outputs['Attribute'], nc.inputs[0])
        # keep grass back from the section edge (trampled margin)
        D = DIG
        m3 = N.new("ShaderNodeMath"); m3.operation = 'MULTIPLY'; L.new(sel, m3.inputs[0]); L.new(nc.outputs[0], m3.inputs[1]); sel = m3.outputs[0]
        sx = N.new("ShaderNodeSeparateXYZ"); L.new(pos.outputs[0], sx.inputs[0])
        def outside(axis, lo, hi):
            a = N.new("ShaderNodeMath"); a.operation = 'LESS_THAN'; a.inputs[1].default_value = lo; L.new(sx.outputs[axis], a.inputs[0])
            b = N.new("ShaderNodeMath"); b.operation = 'GREATER_THAN'; b.inputs[1].default_value = hi; L.new(sx.outputs[axis], b.inputs[0])
            o_ = N.new("ShaderNodeMath"); o_.operation = 'MAXIMUM'; L.new(a.outputs[0], o_.inputs[0]); L.new(b.outputs[0], o_.inputs[1]); return o_.outputs[0]
        ox = outside('X', D["x0"] - 1.6, D["x1"] + 1.6); oy = outside('Y', D["y0"] - 1.6, D["y1"] + 1.6)
        oo = N.new("ShaderNodeMath"); oo.operation = 'MAXIMUM'; L.new(ox, oo.inputs[0]); L.new(oy, oo.inputs[1])
        m4 = N.new("ShaderNodeMath"); m4.operation = 'MULTIPLY'; L.new(sel, m4.inputs[0]); L.new(oo.outputs[0], m4.inputs[1]); sel = m4.outputs[0]
    # density falls off toward the radius (no visible edge): keep a point if random < falloff
    fo = N.new("ShaderNodeMapRange"); fo.interpolation_type = 'SMOOTHSTEP'
    fo.inputs['From Min'].default_value = radius; fo.inputs['From Max'].default_value = radius * 0.3
    L.new(ln.outputs['Value'], fo.inputs['Value'])
    rk = N.new("FunctionNodeRandomValue"); rk.data_type = 'FLOAT'; rk.inputs['Seed'].default_value = seed + 11
    keep = N.new("ShaderNodeMath"); keep.operation = 'LESS_THAN'; L.new(rk.outputs[0], keep.inputs[0]); L.new(fo.outputs[0], keep.inputs[1])
    dist = N.new("GeometryNodeDistributePointsOnFaces"); dist.distribute_method = 'RANDOM'
    dist.inputs['Density'].default_value = density; dist.inputs['Seed'].default_value = seed
    L.new(gi.outputs[0], dist.inputs['Mesh']); L.new(sel, dist.inputs['Selection'])
    ci = N.new("GeometryNodeCollectionInfo"); ci.inputs['Collection'].default_value = col
    ci.inputs['Separate Children'].default_value = True; ci.inputs['Reset Children'].default_value = True
    inst = N.new("GeometryNodeInstanceOnPoints"); inst.inputs['Pick Instance'].default_value = True
    L.new(dist.outputs['Points'], inst.inputs['Points']); L.new(keep.outputs[0], inst.inputs['Selection']); L.new(ci.outputs[0], inst.inputs['Instance'])
    ri = N.new("FunctionNodeRandomValue"); ri.data_type = 'INT'; ri.inputs['Max'].default_value = 100; ri.inputs['Seed'].default_value = seed + 3
    L.new(ri.outputs[0], inst.inputs['Instance Index'])
    rr = N.new("FunctionNodeRandomValue"); rr.data_type = 'FLOAT_VECTOR'; rr.inputs['Min'].default_value = (-0.15, -0.15, 0); rr.inputs['Max'].default_value = (0.15, 0.15, 6.28)
    rr.inputs['Seed'].default_value = seed + 5
    L.new(rr.outputs[0], inst.inputs['Rotation'])
    rs = N.new("FunctionNodeRandomValue"); rs.data_type = 'FLOAT'; rs.inputs['Min'].default_value = scale[0]; rs.inputs['Max'].default_value = scale[1]
    rs.inputs['Seed'].default_value = seed + 7
    L.new(rs.outputs[0], inst.inputs['Scale'])
    jn = N.new("GeometryNodeJoinGeometry"); L.new(gi.outputs[0], jn.inputs[0]); L.new(inst.outputs[0], jn.inputs[0])
    L.new(jn.outputs[0], go.inputs[0])
    md = target.modifiers.new(name, 'NODES'); md.node_group = ng
    return md


# ----------------------------------------------------------------------------- light
MOODS = {
    #           HDRI                                 hdri str  lamp elev  sun azim  lamp energy colour          fog colour
    "golden":   ("belfast_sunset_puresky",             0.45,     6.0,     196,      8.0, (1.0, 0.6, 0.34),  (0.50, 0.44, 0.42)),
    "overcast": ("overcast_soil_puresky",              1.1,      30.0,    220,      0.0, (1.0, 0.95, 0.9),  (0.52, 0.55, 0.58)),
    "dawn":     ("qwantani_dawn_puresky",              0.5,      6.0,      10,      5.5, (1.0, 0.68, 0.45), (0.50, 0.46, 0.48)),
    "dusk":     ("qwantani_dusk_2_puresky",            0.4,      3.0,     185,      2.2, (1.0, 0.5, 0.28),  (0.30, 0.27, 0.30)),
    "day":      ("kloofendal_48d_partly_cloudy_puresky", 0.7,   30.0,     225,      4.8, (1.0, 0.93, 0.85), (0.52, 0.58, 0.66)),
}


def hdri_sun(aid):
    """Azimuth (deg, 0 = +x, ccw) and elevation of the brightest pixel of a Poly Haven sky (cached)."""
    import json
    cache = os.path.join(ph.ROOT, aid, "sun.json")
    if os.path.exists(cache):
        return json.load(open(cache))
    im = bpy.data.images.load(ph.hdri(aid, "1k")); w, h = im.size
    a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a); a = a.reshape(h, w, 4)[..., :3].sum(-1)
    y, x = np.unravel_index(a.argmax(), a.shape)
    r = dict(az=(0.5 - (x + 0.5) / w) * 360.0, el=((y + 0.5) / h - 0.5) * 180.0)
    bpy.data.images.remove(im); json.dump(r, open(cache, "w"))
    return r


def light(mood="golden", sun_az=None):
    """Poly Haven sky rotated so its sun sits at the mood's azimuth, plus a matching sun lamp for crisp shadows."""
    aid, hs, el, az, se, col, fogc = MOODS[mood]
    az = az if sun_az is None else sun_az
    s0 = hdri_sun(aid)
    w, bg, mp = ph.world_hdri(aid, strength=hs, rot_z=math.radians(s0["az"] - az))
    sun = None
    if se > 0:
        d = bpy.data.lights.new("Sun", 'SUN'); d.energy = se; d.color = col; d.angle = math.radians(1.0)
        sun = bpy.data.objects.new("Sun", d); bpy.context.scene.collection.objects.link(sun)
        e = math.radians(el); a = math.radians(az)
        to_sun = Vector((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)))
        sun.rotation_euler = (-to_sun).to_track_quat('-Z', 'Y').to_euler()
    return dict(world=w, bg=bg, map=mp, sun=sun, fog=fogc, az=az, el=el)


def island(mood="golden", grass_at=None, grass_r=30.0, n=900, sun_az=None, fog_density=0.00018, grass_density=120.0,
           focus=(0.0, 0.0), core=6.0):
    """Build the whole environment. grass_at=(x, y) puts real grass clumps within grass_r of that point."""
    Lh = light(mood, sun_az)
    fog = dict(color=Lh["fog"], density=fog_density)
    t = terrain_mesh(n=n, focus=focus, core=core)
    t.data.materials.append(ground_material(fog=fog))
    s, far = sea(fog=fog)
    sf = surf()
    lochs()
    if grass_at is not None:
        scatter(t, grass_at, grass_r, density=grass_density, zone=(150, 1e9), scale=(0.22, 0.42), seed=1, name="Machair")
        scatter(t, grass_at, grass_r, density=grass_density * 0.6, zone=(50, 150), scale=(1.1, 1.9), seed=2, name="Marram")
    return dict(terrain=t, sea=s, far=far, surf=sf, light=Lh, h=lambda x, y: float(surface(x, y)), fog=fog)


# ----------------------------------------------------------------------------- coast detail
def coast_rocks(y0=-700, y1=500, n=70, seed=3):
    """Gneiss outcrops and boulders along the waterline (Poly Haven coast rocks), and tide pools among them."""
    import random
    rng = random.Random(seed)
    srcs = []
    for aid in ("coast_rocks_01", "coast_rocks_02", "coast_rocks_05", "coast_land_rocks_02"):
        try:
            root, ms = ph.model(aid, loc=(0, 0, -900)); srcs.append((root, ms))
        except Exception as ex:
            print("rock", aid, ex)
    if not srcs:
        return []
    out = []
    for k in range(n):
        y = rng.uniform(y0, y1); x = float(coast_x(y)) + rng.uniform(-25, 18)
        root, ms = srcs[k % len(srcs)]
        for m in ms:
            o = m.copy(); bpy.context.scene.collection.objects.link(o); o.parent = None
            s_ = rng.uniform(1.5, 5.0)
            o.matrix_world = Matrix.Translation((x, y, float(surface(x, y)) - 0.4 * s_)) @ Matrix.Rotation(rng.uniform(0, 6.3), 4, 'Z') @ Matrix.Scale(s_, 4)
            out.append(o)
    for root, ms in srcs:
        for m in ms:
            m.hide_render = True
    # tide pools: small sky-reflecting water patches on the lower beach
    m = bpy.data.materials.get("Loch")
    for k in range(40):
        y = rng.uniform(y0, y1); x = float(coast_x(y)) + rng.uniform(2, 20)
        bpy.ops.mesh.primitive_circle_add(vertices=24, radius=rng.uniform(1.0, 4.0), fill_type='NGON', location=(x, y, float(surface(x, y)) + 0.03))
        o = bpy.context.active_object; o.scale = (1, rng.uniform(0.4, 0.8), 1); o.rotation_euler.z = rng.uniform(0, 3.14); o.name = "tidepool"
        if m:
            o.data.materials.append(m)
    return out


def cloud_shadows(center=(0, 0), size=4000.0, height=900.0, cover=0.45, seed=2):
    """Big cloud shadows drifting over the machair: a shadow-only plane high up, alpha from noise (invisible to camera)."""
    bpy.ops.mesh.primitive_plane_add(size=size, location=(center[0], center[1], height)); o = bpy.context.active_object; o.name = "cloudshadow"
    m = bpy.data.materials.new("cloudshadow"); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 4.0; nz.inputs['Detail'].default_value = 5
    nz.noise_dimensions = '4D'; nz.inputs['W'].default_value = seed
    L.new(tc.outputs['Generated'], nz.inputs['Vector'])
    mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 1 - cover; mr.inputs['From Max'].default_value = 1 - cover + 0.12
    L.new(nz.outputs['Fac'], mr.inputs['Value']); L.new(mr.outputs[0], p.inputs['Alpha'])
    o.data.materials.append(m)
    o.visible_camera = False; o.visible_glossy = False; o.visible_diffuse = False; o.visible_transmission = False
    o.visible_volume_scatter = False
    return o


def surf_mist(y0=-700, y1=500, width=50.0, height=9.0, density=0.012):
    """Sea spray hanging over the breakers: a long thin volume along the waterline."""
    ym = (y0 + y1) / 2; xm = float(coast_x(ym)) - width * 0.4
    bpy.ops.mesh.primitive_cube_add(size=1, location=(xm, ym, height / 2 - 0.5)); o = bpy.context.active_object; o.name = "surfmist"
    o.scale = (width, y1 - y0, height)
    m = bpy.data.materials.new("surfmist"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; N.remove(N["Principled BSDF"])
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Generated'], sep.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 25; nz.inputs['Detail'].default_value = 4; L.new(tc.outputs['Generated'], nz.inputs['Vector'])
    fz = N.new("ShaderNodeMapRange"); fz.inputs['From Min'].default_value = 0.0; fz.inputs['From Max'].default_value = 1.0
    fz.inputs['To Min'].default_value = 1.0; fz.inputs['To Max'].default_value = 0.0; L.new(sep.outputs['Z'], fz.inputs['Value'])
    br = N.new("ShaderNodeMapRange"); br.inputs['From Min'].default_value = 0.4; br.inputs['From Max'].default_value = 0.65; L.new(nz.outputs['Fac'], br.inputs['Value'])
    m1 = N.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; L.new(fz.outputs[0], m1.inputs[0]); L.new(br.outputs[0], m1.inputs[1])
    m2 = N.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'; m2.inputs[1].default_value = density; L.new(m1.outputs[0], m2.inputs[0])
    v = N.new("ShaderNodeVolumePrincipled"); v.inputs['Color'].default_value = (0.9, 0.9, 0.92, 1); v.inputs['Anisotropy'].default_value = 0.6
    L.new(m2.outputs[0], v.inputs['Density']); L.new(v.outputs[0], N["Material Output"].inputs['Volume'])
    o.data.materials.append(m); o.visible_shadow = False
    return o
