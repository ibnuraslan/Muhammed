"""Alcohol barrels of 1872 (about 40 US gallons: ~0.6 m across the bilge, 0.87 m long) and the hold stow.
Mesh: Poly Haven `wine_barrel_01` (CC0), scaled radially to the 40-gallon size. Two woods:
  white oak - pale tan, closed grain (tyloses block the vessels): the 1,692 that arrived full
  red oak   - pinker brown, open coarse pores: the nine that arrived empty
Barrels are collection instances, so a hold of ~1,700 costs one mesh."""
import math, random
import bpy
from mathutils import Vector, Matrix
import ph, ship

DIA = 0.60; LEN = 0.87; R = DIA / 2
_PROTO = {}


def _wood_variant(src, kind):
    """Matte, weathered oak staves; the hoops (the texture's metal mask) become dark wrought iron with rust bloom."""
    m = src.copy(); m.name = f"oak_{kind}"
    N = m.node_tree.nodes; Lk = m.node_tree.links
    p = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    sep = next(n for n in N if n.bl_idname == 'ShaderNodeSeparateColor')
    mask = sep.outputs['Blue']
    diff = p.inputs['Base Color'].links[0].from_socket
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 9.0; nz.inputs['Detail'].default_value = 8
    Lk.new(tc.outputs['Object'], nz.inputs['Vector'])
    # wood: tint toward the species, desaturate a little, grime in the noise, weathered grey on the bilge
    mul = N.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1
    mul.inputs[7].default_value = (0.95, 0.80, 0.62, 1) if kind == "white" else (1.0, 0.62, 0.50, 1)
    Lk.new(diff, mul.inputs[6])
    hs = N.new("ShaderNodeHueSaturation"); hs.inputs['Saturation'].default_value = 0.8; hs.inputs['Value'].default_value = 0.85
    Lk.new(mul.outputs[2], hs.inputs['Color'])
    gr = N.new("ShaderNodeMix"); gr.data_type = 'RGBA'; gr.blend_type = 'MULTIPLY'
    gr.inputs[7].default_value = (0.55, 0.5, 0.44, 1)
    gm = N.new("ShaderNodeMapRange"); gm.inputs['From Min'].default_value = 0.45; gm.inputs['From Max'].default_value = 0.7
    gm.inputs['To Max'].default_value = 0.7
    Lk.new(nz.outputs['Fac'], gm.inputs['Value']); Lk.new(gm.outputs[0], gr.inputs['Factor'])
    Lk.new(hs.outputs[0], gr.inputs[6])
    # iron: near-black with rust blooms
    rn = N.new("ShaderNodeTexNoise"); rn.inputs['Scale'].default_value = 40.0; rn.inputs['Detail'].default_value = 10
    Lk.new(tc.outputs['Object'], rn.inputs['Vector'])
    rr = N.new("ShaderNodeMapRange"); rr.inputs['From Min'].default_value = 0.5; rr.inputs['From Max'].default_value = 0.68
    Lk.new(rn.outputs['Fac'], rr.inputs['Value'])
    ir = N.new("ShaderNodeMix"); ir.data_type = 'RGBA'
    ir.inputs[6].default_value = (0.035, 0.032, 0.03, 1); ir.inputs[7].default_value = (0.22, 0.08, 0.03, 1)
    Lk.new(rr.outputs[0], ir.inputs['Factor'])
    mk = N.new("ShaderNodeMapRange"); mk.inputs['From Min'].default_value = 0.3; mk.inputs['From Max'].default_value = 0.6
    Lk.new(mask, mk.inputs['Value'])
    col = N.new("ShaderNodeMix"); col.data_type = 'RGBA'
    Lk.new(mk.outputs[0], col.inputs['Factor']); Lk.new(gr.outputs[2], col.inputs[6]); Lk.new(ir.outputs[2], col.inputs[7])
    Lk.new(col.outputs[2], p.inputs['Base Color'])
    met = N.new("ShaderNodeMath"); met.operation = 'MULTIPLY'; met.inputs[1].default_value = 0.45
    Lk.new(mk.outputs[0], met.inputs[0]); Lk.new(met.outputs[0], p.inputs['Metallic'])
    ro = N.new("ShaderNodeMix"); ro.data_type = 'FLOAT'
    ro.inputs['A'].default_value = 0.88; ro.inputs['B'].default_value = 0.62
    Lk.new(mk.outputs[0], ro.inputs['Factor']); Lk.new(ro.outputs['Result'], p.inputs['Roughness'])
    p.inputs['Specular IOR Level'].default_value = 0.35
    if kind == "red":                                   # open pores: fine dark pits along the grain
        mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (900, 900, 40)
        Lk.new(tc.outputs['Object'], mp.inputs['Vector'])
        vo = N.new("ShaderNodeTexVoronoi"); vo.feature = 'F1'; Lk.new(mp.outputs[0], vo.inputs['Vector'])
        r2 = N.new("ShaderNodeMapRange"); r2.inputs['From Min'].default_value = 0.0; r2.inputs['From Max'].default_value = 0.18
        Lk.new(vo.outputs['Distance'], r2.inputs['Value'])
        bb = N.new("ShaderNodeBump"); bb.inputs['Strength'].default_value = 0.25; Lk.new(r2.outputs[0], bb.inputs['Height'])
        nrm = p.inputs['Normal']
        if nrm.links:
            Lk.new(nrm.links[0].from_socket, bb.inputs['Normal'])
        Lk.new(bb.outputs['Normal'], nrm)
    return m


def proto(kind="white"):
    """Collection holding one barrel lying on its side, axis along +X, centred at the origin."""
    if kind in _PROTO:
        return _PROTO[kind]
    if "white" not in _PROTO and kind == "red":
        proto("white")
    base = bpy.data.collections.get("barrel_src")
    if base is None:
        root, ms = ph.model("wine_barrel_01")
        base = bpy.data.collections.new("barrel_src")
        for o in [root] + ms:
            for c in o.users_collection:
                c.objects.unlink(o)
            base.objects.link(o)
        # lying down: axis z -> x, centred, radial scale to 40 gal
        k = DIA / 0.742
        root.matrix_world = Matrix.Rotation(math.radians(90), 4, 'Y') @ Matrix.Translation((0, 0, -0.436)) @ \
            Matrix.Diagonal((k, k, LEN / 0.872, 1))
        base["orig_mat"] = ms[0].data.materials[0].name
    src = bpy.data.materials[base["orig_mat"]]
    m = _wood_variant(src, kind)
    coll = bpy.data.collections.new(f"barrel_{kind}")
    for o in base.objects:
        c = o.copy()
        if o.type == 'MESH':
            c.data = o.data                      # shared mesh
            c.material_slots[0].link = 'OBJECT'; c.material_slots[0].material = m
        coll.objects.link(c)
    # re-parent copies to the copied root
    roots = [c for c in coll.objects if c.type == 'EMPTY']
    for c in coll.objects:
        if c.parent and c.type != 'EMPTY':
            c.parent = roots[0]
    _PROTO[kind] = coll
    return coll


def place(kind, M, name="barrel", parent_coll=None):
    """An instance of a barrel at world matrix M (barrel axis = M's X)."""
    e = bpy.data.objects.new(name, None); e.instance_type = 'COLLECTION'; e.instance_collection = proto(kind)
    e.matrix_world = M
    (parent_coll or bpy.context.scene.collection).objects.link(e)
    return e


def upright(kind, loc, rot_z=0.0, name="barrel_up", parent_coll=None):
    M = Matrix.Translation(Vector(loc) + Vector((0, 0, LEN / 2))) @ Matrix.Rotation(rot_z, 4, 'Z') @ Matrix.Rotation(math.radians(-90), 4, 'Y')
    return place(kind, M, name, parent_coll)


# ----------------------------------------------------------------------------- the hold
HOLD_X = (-7.9, 9.6)          # after bulkhead (cabin) .. fore peak bulkhead
FLOOR_Z = -2.45               # top of the floors / ceiling over the keelson


def inside(x, y, z, r=R, margin=0.05):
    """Is a circle of radius r at (y, z) in the cross-section at x clear of the planking (and under the beams)?"""
    for dz in (-r, 0.0, r * 0.7):
        zz = z + dz
        zd = ship.zdeck(x)
        if zz + (r if dz >= 0 else 0) > zd - 0.32:            # deck beams
            return False
        t = (zz + ship.DRAFT) / (zd + ship.DRAFT)
        if t <= 0.02:
            return False
        xs, xb = ship._ends(t)
        for xx in (x - LEN / 2, x + LEN / 2):
            s = (xx - xs) / (xb - xs)
            if s <= 0 or s >= 1:
                return False
            hb = ship.half_breadth(s, t) - 0.28                # frames + ceiling thickness
            if abs(y) + (r if dz == 0 else r * 0.75) > hb - margin:
                return False
    return True


def stow(M=Matrix(), red_slots=None, ymax=None, xr=HOLD_X, coll=None, seed=3, jitter=0.012):
    """Fill the hold with barrels in tiers, each tier nested in the cantlines of the one below (bilge and cantline).
    Returns list of (instance, (x, y, z), kind). ymax keeps only barrels with y <= ymax (for a cutaway)."""
    rng = random.Random(seed)
    out = []
    dz = R * math.sqrt(3)
    tier = 0
    z = FLOOR_Z + R
    while z < 1.4:
        off = (tier % 2) * R
        nx = int((xr[1] - xr[0]) / (LEN + 0.03))
        for i in range(nx):
            x = xr[0] + (i + 0.5) * (LEN + 0.03)
            y = -4.0 + off
            while y < 4.0:
                if inside(x, y, z) and (ymax is None or y <= ymax):
                    out.append((x, y, z))
                y += DIA + 0.004
        tier += 1
        z += dz
    red_slots = set(red_slots or [])
    res = []
    for k, (x, y, z) in enumerate(out):
        kind = "red" if k in red_slots else "white"
        Mi = M @ Matrix.Translation((x + rng.uniform(-0.02, 0.02), y, z)) @ Matrix.Rotation(rng.uniform(0, 6.28), 4, 'X') @ \
            Matrix.Rotation(rng.uniform(-jitter, jitter), 4, 'Z')
        res.append((place(kind, Mi, f"b{k}", coll), (x, y, z), kind))
    return res


def count_full_hold():
    n = 0; dz = R * math.sqrt(3); tier = 0; z = FLOOR_Z + R
    while z < 1.4:
        off = (tier % 2) * R; nx = int((HOLD_X[1] - HOLD_X[0]) / (LEN + 0.03))
        for i in range(nx):
            x = HOLD_X[0] + (i + 0.5) * (LEN + 0.03); y = -4.0 + off
            while y < 4.0:
                n += inside(x, y, z); y += DIA + 0.004
        tier += 1; z += dz
    return n
