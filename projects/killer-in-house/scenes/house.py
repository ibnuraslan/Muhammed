"""THE HOUSE (hero set, built once): a modest two-storey 1941 Denver brick house on a quiet elm street.

Coordinates (metres): the house is centred at the origin, front wall at y = -5 facing the street (-Y).
  grade z = -0.6 ; ground floor 0 .. 2.7 ; upstairs floor 2.9 .. 5.4 ; ceiling joists 5.4 .. 5.5 ; attic to the ridge 7.25
  ground floor:  front bedroom  x[-4.2,-0.6] y[-4.7,-0.2]   hall x[-0.6,0.9] (stairs x[0,0.9] rising +y)   front room x[0.9,4.2]
                 back room      x[-4.2,-1.5] y[-0.2, 4.7]   kitchen x[-1.5,4.2] y[-0.2,4.7]  (icebox, iron stove, back door)
  upstairs:      bedroom        x[-4.2,-0.6] y[-4.7,-0.2]   closet x[-1.8,-0.6] y[-1.2,-0.2] with the 8 x 15 in hatch
  attic:         crawl space under the sloping roof boards, reached only through the closet hatch
  cellar:        z[-2.7,-0.15] under the back rooms, shelves of preserve jars
The street runs along x at y = -15 (road), neighbours left/right and across the street.

build_house(season, tod, ...) -> ctx dict.  season: autumn | winter | summer ; tod: day | night | dusk
"""
import os, sys, math
import numpy as np
import bpy
from mathutils import Vector, Matrix
from kit import *
import ph
import human as _hm
from human import Human, add_asset, pose_walk, fingers_curl, rotate_bone, aim_bone, _world_verts, reach, pose_sit

HERE = os.path.dirname(os.path.abspath(__file__))
W2, D2 = 4.5, 5.0                  # half width / half depth of the brick shell (outer faces)
T = 0.3                            # exterior wall thickness
G = -0.6                           # grade
F1, C1 = 0.0, 2.7                  # ground floor / ceiling
F2, C2 = 2.9, 5.4                  # upstairs floor / ceiling
EAVE, RIDGE = 5.55, 7.25
ROAD_Y = -15.5
HATCH = (-1.1, -0.9)               # closet ceiling hatch centre (x, y)
HATCH_W, HATCH_L = 0.2, 0.38       # about eight by fifteen inches

_MAT = {}


# ============================================================================ materials
def mat(key):
    if key in _MAT:
        return _MAT[key]
    T_ = lambda aid, sc, tint=None: ph.texture(aid, scale=sc, name=key, tint=tint)
    table = {
        "brick": lambda: T_("red_brick_03", 0.8, (0.95, 0.86, 0.8)),
        "brick2": lambda: T_("red_brick_03", 0.8, (0.8, 0.82, 0.85)),
        "brick3": lambda: T_("red_brick_03", 0.8, (1.0, 0.95, 0.75)),
        "roof": lambda: T_("grey_roof_tiles", 0.45, (0.55, 0.5, 0.48)),
        "floor": lambda: T_("old_wood_floor", 0.5),
        "lino": lambda: T_("old_linoleum_flooring_01", 0.5),
        "plaster": lambda: T_("painted_plaster_wall", 0.4, (0.95, 0.88, 0.74)),
        "paper": lambda: wallpaper("paper", (0.80, 0.74, 0.60), (0.55, 0.30, 0.26), (0.38, 0.45, 0.32)),
        "paper2": lambda: wallpaper("paper2", (0.70, 0.74, 0.66), (0.62, 0.52, 0.34), (0.42, 0.36, 0.30), seed=5),
        "conc": lambda: T_("rough_concrete", 0.4),
        "stone": lambda: T_("stone_wall", 0.5, (0.8, 0.78, 0.74)),
        "planks": lambda: T_("roof_planks", 0.5, (0.85, 0.75, 0.62)),
        "raw": lambda: T_("raw_plank_wall", 0.6, (0.8, 0.72, 0.62)),
        "grass": lambda: T_("leafy_grass", 0.25),
        "leafground": lambda: T_("dry_decay_leaves", 0.3),
        "asphalt": lambda: T_("asphalt_02", 0.12),
        "pave": lambda: T_("concrete_pavement", 0.35),
        "snow": lambda: T_("snow_02", 0.25),
        "trim": lambda: pbr("Trim", (0.78, 0.74, 0.64), 0.45),
        "darktrim": lambda: pbr("DarkTrim", (0.12, 0.14, 0.12), 0.45),
        "door": lambda: wood("DoorWood", (0.09, 0.045, 0.02), (0.2, 0.11, 0.055), scale=(0.3, 6, 6), rough=0.4, coat=0.3),
        "oak": lambda: wood("Oak", (0.14, 0.08, 0.04), (0.3, 0.18, 0.09), scale=(0.3, 6, 6), rough=0.4, coat=0.3),
        "enamel": lambda: pbr("Enamel", (0.82, 0.8, 0.74), 0.2, 0.0, **{'Coat Weight': 0.6}),
        "iron": lambda: pbr("CastIron", (0.035, 0.035, 0.037), 0.55, 0.9),
        "chrome": lambda: pbr("Chrome", (0.7, 0.7, 0.72), 0.18, 1.0),
        "glass": lambda: window_glass(),
        "black": lambda: pbr("Black", (0.01, 0.01, 0.01), 0.7),
        "shade": lambda: shade_mat(),
        "lace": lambda: lace_mat(),
    }
    _MAT[key] = table[key]()
    return _MAT[key]


def window_glass():
    """Reflective for the camera, transparent to shadow rays so daylight reaches the rooms cleanly."""
    m = bpy.data.materials.new("WinGlass"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); lp = N.new("ShaderNodeLightPath")
    tr = N.new("ShaderNodeBsdfTransparent"); gl = N.new("ShaderNodeBsdfGlossy"); gl.inputs['Roughness'].default_value = 0.03
    fr = N.new("ShaderNodeFresnel"); fr.inputs['IOR'].default_value = 1.6
    refl = N.new("ShaderNodeMixShader"); L.new(fr.outputs[0], refl.inputs[0]); L.new(tr.outputs[0], refl.inputs[1]); L.new(gl.outputs[0], refl.inputs[2])
    mx = N.new("ShaderNodeMixShader"); L.new(lp.outputs['Is Shadow Ray'], mx.inputs[0])
    L.new(refl.outputs[0], mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs['Surface'])
    return m


def wallpaper_image(path, ground, flower, leaf, seed=1, W=512):
    """A small 1940s floral wallpaper tile (seamless): five-petal sprigs with leaves on a soft ground."""
    import skia
    srf = skia.Surface(W, W); cv = srf.getCanvas()
    cv.clear(skia.Color(*[int(255 * v) for v in ground]))
    p = skia.Paint(AntiAlias=True)
    p.setColor(skia.Color(*[int(255 * v * 0.94) for v in ground]))
    for k in range(0, W, 16):
        cv.drawRect(skia.Rect.MakeXYWH(k, 0, 1, W), p)
    def sprig(cx, cy):
        p.setColor(skia.Color(*[int(255 * v) for v in leaf]))
        for a in (0.6, 2.4, 4.0):
            cv.save(); cv.translate(cx + 15 * math.cos(a), cy + 15 * math.sin(a)); cv.rotate(math.degrees(a))
            cv.drawOval(skia.Rect.MakeXYWH(-7, -3, 14, 6), p); cv.restore()
        p.setColor(skia.Color(*[int(255 * v) for v in flower]))
        for k in range(5):
            aa = k * 2 * math.pi / 5
            cv.drawCircle(cx + 5 * math.cos(aa), cy + 5 * math.sin(aa), 4.3, p)
        p.setColor(skia.Color(232, 212, 150)); cv.drawCircle(cx, cy, 2.3, p)
    for i in range(4):
        for j in range(4):
            cx = (i + 0.5 * (j % 2)) * W / 4 + W / 8; cy = j * W / 4 + W / 8
            for dx in (-W, 0, W):
                for dy in (-W, 0, W):
                    sprig(cx + dx, cy + dy)
    srf.makeImageSnapshot().save(path, skia.kPNG)
    return path


def wallpaper(name, ground, flower, leaf, seed=1, scale=3.2):
    """Patterned paper (tiles every 1/scale m) with a faint paper bump."""
    d = os.path.join(HERE, "..", "out", "generated"); os.makedirs(d, exist_ok=True)
    path = os.path.join(d, name + "_tile.png")
    if not os.path.exists(path):
        wallpaper_image(path, ground, flower, leaf, seed)
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (scale,) * 3
    L.new(tc.outputs['Object'], mp.inputs['Vector'])
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path); t.projection = 'BOX'; t.projection_blend = 0.1
    L.new(mp.outputs[0], t.inputs['Vector']); L.new(t.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.8
    n = N.new("ShaderNodeTexNoise"); n.inputs['Scale'].default_value = 60; L.new(tc.outputs['Object'], n.inputs['Vector'])
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.05; L.new(n.outputs['Fac'], b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


def drape(name, targets, margin=0.25, res=0.03, floor=0.0, lift=0.015, seed=0):
    """A dust sheet draped over furniture: a height-field cloth from ray casts onto `targets`, softened, with
    folds that spill onto the floor (no simulation needed)."""
    from scipy.ndimage import gaussian_filter, distance_transform_edt
    lo, hi = ph.bounds([o for t in targets for o in ([t] + list(t.children_recursive)) if o.type == 'MESH'])
    x0, y0, x1, y1 = lo.x - margin, lo.y - margin, hi.x + margin, hi.y + margin
    nx, ny = int((x1 - x0) / res) + 1, int((y1 - y0) / res) + 1
    dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene
    tset = {o.name for t in targets for o in ([t] + list(t.children_recursive))}
    Hh = np.full((ny, nx), floor)
    hitm = np.zeros((ny, nx), bool)
    for j in range(ny):
        for i in range(nx):
            o = Vector((x0 + i * res, y0 + j * res, hi.z + 1.0))
            ok, loc, nrm, idx, ob, M = sc.ray_cast(dg, o, Vector((0, 0, -1)))
            if ok and ob.name in tset:
                Hh[j, i] = loc.z; hitm[j, i] = True
    from scipy.ndimage import grey_dilation
    Hh = np.where(hitm, grey_dilation(Hh, size=(9, 9)), Hh)                    # cloth bridges thin rails and gaps
    hitm = grey_dilation(hitm.astype(np.uint8), size=(5, 5)).astype(bool)
    Hh = np.where(hitm, grey_dilation(np.where(hitm, Hh, floor), size=(5, 5)), floor)
    dist = distance_transform_edt(~hitm) * res
    top = gaussian_filter(np.where(hitm, Hh, 0), 3) / np.maximum(gaussian_filter(hitm.astype(float), 3), 1e-3)
    edge = np.where(hitm, gaussian_filter(Hh, 3), np.maximum(floor, top - dist * 5.0))   # falls steeply off the edges
    Hs = gaussian_filter(edge, 2.5) + lift
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:ny, 0:nx]
    folds = 0.012 * np.sin(xx * 0.9 + rng.uniform(0, 6)) * np.sin(yy * 0.35) + 0.008 * gaussian_filter(rng.standard_normal((ny, nx)), 2)
    Hs = np.maximum(Hs + folds * (Hs > floor + 0.05), floor + 0.004)
    from common import grid_mesh
    o = grid_mesh(name, Hs.astype(np.float32), x1 - x0, y1 - y0, 1.0, origin=((x0 + x1) / 2, (y0 + y1) / 2, 0))
    o.data.materials.append(fabric("DustSheet", (0.62, 0.6, 0.55), 0.95, 0.5, 350))
    for t in targets:
        for ob in [t] + list(t.children_recursive):
            ob.hide_render = True if False else ob.hide_render
    return o


def shade_mat():
    """Cream roller shade: diffuse + translucent, so a lamp behind it glows through like real cloth."""
    m = bpy.data.materials.new("Shade"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); d = N.new("ShaderNodeBsdfDiffuse"); d.inputs['Color'].default_value = (0.78, 0.7, 0.52, 1)
    tl = N.new("ShaderNodeBsdfTranslucent"); tl.inputs['Color'].default_value = (0.95, 0.8, 0.55, 1)
    mx = N.new("ShaderNodeMixShader"); mx.inputs[0].default_value = 0.45
    L.new(d.outputs[0], mx.inputs[1]); L.new(tl.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs['Surface'])
    return m


def lace_mat():
    m = bpy.data.materials.new("Lace"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); d = N.new("ShaderNodeBsdfDiffuse"); d.inputs['Color'].default_value = (0.82, 0.8, 0.74, 1)
    tr = N.new("ShaderNodeBsdfTransparent"); tl = N.new("ShaderNodeBsdfTranslucent"); tl.inputs['Color'].default_value = (0.9, 0.88, 0.8, 1)
    m1 = N.new("ShaderNodeMixShader"); m1.inputs[0].default_value = 0.4; L.new(d.outputs[0], m1.inputs[1]); L.new(tl.outputs[0], m1.inputs[2])
    m2 = N.new("ShaderNodeMixShader"); m2.inputs[0].default_value = 0.55; L.new(m1.outputs[0], m2.inputs[1]); L.new(tr.outputs[0], m2.inputs[2])
    L.new(m2.outputs[0], out.inputs['Surface'])
    return m


def retint(m, mul=(1, 1, 1), hue=0.5, sat=1.0, val=1.0):
    """Multiply/hue-shift a material's base colour (autumn leaves, faded paint)."""
    N = m.node_tree.nodes; L = m.node_tree.links
    p = next((n for n in N if n.type == 'BSDF_PRINCIPLED'), None)
    if p is None:
        return m
    src = p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].links else None
    hs = N.new("ShaderNodeHueSaturation"); hs.inputs['Hue'].default_value = hue; hs.inputs['Saturation'].default_value = sat; hs.inputs['Value'].default_value = val
    if src is not None:
        L.new(src, hs.inputs['Color'])
    else:
        hs.inputs['Color'].default_value = p.inputs['Base Color'].default_value
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    L.new(hs.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (*mul, 1)
    L.new(mx.outputs[2], p.inputs['Base Color'])
    return m


def driven_emission(m_or_light, expr, base, prop="energy"):
    """Frame-driven light/emission strength (flicker, lights dying) that plays in any render of the .blend."""
    if isinstance(m_or_light, bpy.types.Light):
        d = m_or_light.driver_add(prop).driver
    else:
        p = m_or_light.node_tree.nodes["Principled BSDF"]
        d = p.inputs['Emission Strength'].driver_add("default_value").driver
    d.type = 'SCRIPTED'; d.expression = f"{base} * ({expr})"
    return d


# ============================================================================ geometry helpers
def _wall_cells(u0, u1, z0, z1, holes):
    """Solid (ua, ub, za, zb) cells of a wall from u0..u1, z0..z1 with rectangular holes (any arrangement)."""
    cuts = sorted({u0, u1} | {h[0] for h in holes if u0 < h[0] < u1} | {h[1] for h in holes if u0 < h[1] < u1})
    cells = []
    for ua, ub in zip(cuts[:-1], cuts[1:]):
        um = (ua + ub) / 2
        hz = sorted((h[2], h[3]) for h in holes if h[0] <= um <= h[1])
        cz = z0
        for (za, zb) in hz:
            if za > cz:
                cells.append((ua, ub, cz, min(za, z1)))
            cz = max(cz, zb)
        if z1 > cz:
            cells.append((ua, ub, cz, z1))
    # merge vertically identical neighbours along u to keep the object count low
    merged = []
    for c in cells:
        if merged and merged[-1][1] == c[0] and merged[-1][2:] == c[2:]:
            merged[-1] = (merged[-1][0], c[1], c[2], c[3])
        else:
            merged.append(c)
    return [c for c in merged if c[1] - c[0] > 1e-4 and c[3] - c[2] > 1e-4]


def wall_x(name, x0, x1, y, z0, z1, t, m, holes=()):
    """Wall running along X at y (thickness t along Y). holes: (xa, xb, za, zb)."""
    return [box(name, ((a + b) / 2, y, (za + zb) / 2), (b - a, t, zb - za), m) for (a, b, za, zb) in _wall_cells(x0, x1, z0, z1, holes)]


def wall_y(name, y0, y1, x, z0, z1, t, m, holes=()):
    return [box(name, (x, (a + b) / 2, (za + zb) / 2), (t, b - a, zb - za), m) for (a, b, za, zb) in _wall_cells(y0, y1, z0, z1, holes)]


def window_unit(axis, u, w, pos, za, zb, depth=0.12, panes=True, lit_glass=None):
    """Double-hung sash window filling a hole. axis 'x': wall along X at y=pos ; 'y': wall along Y at x=pos."""
    tr = mat("trim"); parts = []; g = []
    def B(nm, cu, cz, su, sz, sd, mm, off=0.0):
        if axis == 'x':
            return box(nm, (cu, pos + off, cz), (su, sd, sz), mm)
        return box(nm, (pos + off, cu, cz), (sd, su, sz), mm)
    f = 0.06
    parts += [B("WFrame", u, za + f / 2, w, f, depth, tr), B("WFrame", u, zb - f / 2, w, f, depth, tr),
              B("WFrame", u - w / 2 + f / 2, (za + zb) / 2, f, zb - za, depth, tr), B("WFrame", u + w / 2 - f / 2, (za + zb) / 2, f, zb - za, depth, tr)]
    zm = (za + zb) / 2
    parts.append(B("WRail", u, zm, w - 2 * f, 0.05, 0.08, tr))
    if panes:
        for k in (-1, 1):
            parts.append(B("WMunt", u, (zm + (zb if k > 0 else za)) / 2, 0.025, (zb - za) / 2 - f, 0.04, tr))
    g.append(B("WGlass", u, zm, w - 2 * f, zb - za - 2 * f, 0.008, lit_glass or mat("glass")))
    # pull-down shade (cream) and lace curtains just inside: the windows read as lived-in rooms
    inward = 0.12 if (pos < 0) else -0.12
    if lit_glass is None:
        sh = (zb - za) * 0.38
        parts.append(B("WShade", u, zb - f - sh / 2, w - 2 * f, sh, 0.01, mat("shade"), off=inward))
        for k in (-1, 1):
            parts.append(B("WCurtain", u + k * (w / 2 - f - 0.1), zm, 0.2, zb - za - 2 * f, 0.02, mat("lace"), off=inward + (0.03 if pos < 0 else -0.03)))
    parts.append(B("WSill", u, za - 0.03, w + 0.16, 0.05, depth + 0.14, tr, off=0.0))
    return parts, g


def hinge_door(name, hinge, width, height, thick, m, axis='x', open_dir=1, knob=True):
    """A door panel parented to a hinge empty (rotate the empty about Z to open)."""
    e = bpy.data.objects.new(name + "Hinge", None); bpy.context.collection.objects.link(e); e.location = hinge
    if axis == 'x':
        d = box(name, (hinge[0] + width / 2, hinge[1], hinge[2] + height / 2), (width, thick, height), m, bevel=0.004)
    else:
        d = box(name, (hinge[0], hinge[1] + width / 2, hinge[2] + height / 2), (thick, width, height), m, bevel=0.004)
    parts = [d]
    # raised panels
    for k in range(3):
        zc = hinge[2] + height * (0.22 + 0.3 * k)
        if axis == 'x':
            for s in (-1, 1):
                parts.append(box(name + "Pan", (hinge[0] + width / 2, hinge[1] + s * thick / 2, zc), (width * 0.7, 0.012, height * 0.22), m, bevel=0.005))
        else:
            for s in (-1, 1):
                parts.append(box(name + "Pan", (hinge[0] + s * thick / 2, hinge[1] + width / 2, zc), (0.012, width * 0.7, height * 0.22), m, bevel=0.005))
    if knob:
        kz = hinge[2] + 0.95
        if axis == 'x':
            for s in (-1, 1):
                parts.append(cyl(name + "Knob", (hinge[0] + width - 0.07, hinge[1] + s * (thick / 2 + 0.03), kz), 0.028, 0.05, mat("chrome"), 16, rot=(math.radians(90), 0, 0)))
        else:
            for s in (-1, 1):
                parts.append(cyl(name + "Knob", (hinge[0] + s * (thick / 2 + 0.03), hinge[1] + width - 0.07, kz), 0.028, 0.05, mat("chrome"), 16, rot=(0, math.radians(90), 0)))
    dj = join(parts, name)
    dj.parent = e; dj.matrix_parent_inverse = e.matrix_world.inverted()
    return e


def gable_roof(name, m, w2=W2 + 0.45, d2=D2 + 0.45, eave=EAVE, ridge=RIDGE, thick=0.12):
    """Gable roof, ridge along X at y=0, two slopes front/back; gable ends brick-filled."""
    import bmesh
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    def slab(sign):
        a = bm.verts.new((-w2, sign * d2, eave)); b = bm.verts.new((w2, sign * d2, eave))
        c = bm.verts.new((w2, 0, ridge)); d = bm.verts.new((-w2, 0, ridge))
        a2 = bm.verts.new((-w2, sign * d2, eave - thick)); b2 = bm.verts.new((w2, sign * d2, eave - thick))
        c2 = bm.verts.new((w2, 0, ridge - thick)); d2_ = bm.verts.new((-w2, 0, ridge - thick))
        fs = [(a, b, c, d), (d2_, c2, b2, a2), (a, a2, b2, b), (b, b2, c2, c), (d, c2 if False else d2_, a2, a)]
        for f in fs:
            try:
                bm.faces.new(f if sign > 0 else f[::-1])
            except Exception:
                pass
    slab(1); slab(-1)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); o.data.materials.append(m)
    for p in o.data.polygons:
        p.use_smooth = False
    return o


def gable_fill(name, m, w=W2, d=D2, z0=EAVE - 0.15, ridge=RIDGE - 0.1, t=T):
    import bmesh
    objs = []
    for sx in (-1, 1):
        me = bpy.data.meshes.new(name); bm = bmesh.new()
        x0, x1 = sx * w - t / 2, sx * w + t / 2
        v = [bm.verts.new((x, y, z)) for x in (x0, x1) for (y, z) in ((-d, z0), (d, z0), (0, ridge))]
        bm.faces.new((v[0], v[1], v[2])); bm.faces.new((v[5], v[4], v[3]))
        for i, j in ((0, 1), (1, 2), (2, 0)):
            bm.faces.new((v[i], v[3 + i], v[3 + j], v[j]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); o.data.materials.append(m); objs.append(o)
    return objs


# ============================================================================ the shell (used for the hero and the neighbours)
FRONT_WINDOWS_1 = [(-2.4, 1.3), (2.6, 1.6)]           # (x centre, width) ground floor front: bedroom, front room
FRONT_WINDOWS_2 = [(-2.4, 1.1), (-0.0, 0.7), (2.6, 1.1)]
SIDE_WINDOWS = [(-2.5, 1.0), (2.2, 0.9)]
BACK_WINDOWS_1 = [(1.1, 1.1), (-2.9, 0.9)]            # kitchen sink window, back room
BACK_WINDOWS_2 = [(-2.4, 0.9), (2.4, 0.9)]
FRONT_DOOR = (0.15, 0.95)                             # x centre, width
BACK_DOOR = (3.05, 0.85)


def shell(prefix="H", brick="brick", detail=False, lit=None):
    """Brick shell + roof + porch. Returns (objects, glass list, ctx bits). lit: material for glowing panes (neighbours)."""
    out = []; glass_ = []; c = {}
    bm_ = mat(brick)
    w1a, w1b = 0.9, 2.25        # window sill/head heights, ground floor
    w2a, w2b = 3.75, 5.05
    holes_f = [(x - w / 2, x + w / 2, w1a, w1b) for x, w in FRONT_WINDOWS_1] + [(FRONT_DOOR[0] - FRONT_DOOR[1] / 2, FRONT_DOOR[0] + FRONT_DOOR[1] / 2, 0.0, 2.15)]
    holes_f += [(x - w / 2, x + w / 2, w2a, w2b) for x, w in FRONT_WINDOWS_2]
    out += wall_x(prefix + "Front", -W2, W2, -D2 + T / 2, G, EAVE, T, bm_, holes_f)
    holes_b = [(x - w / 2, x + w / 2, w1a + (0.25 if x > 0 else 0), w1b) for x, w in BACK_WINDOWS_1] + [(BACK_DOOR[0] - BACK_DOOR[1] / 2, BACK_DOOR[0] + BACK_DOOR[1] / 2, 0.0, 2.1)]
    holes_b += [(x - w / 2, x + w / 2, w2a, w2b) for x, w in BACK_WINDOWS_2]
    out += wall_x(prefix + "Back", -W2, W2, D2 - T / 2, G, EAVE, T, bm_, holes_b)
    for sx in (-1, 1):
        hs = [(y - w / 2, y + w / 2, w1a, w1b) for y, w in SIDE_WINDOWS] + [(y - w / 2, y + w / 2, w2a, w2b) for y, w in SIDE_WINDOWS]
        out += wall_y(prefix + "Side", -D2 + T, D2 - T, sx * (W2 - T / 2), G, EAVE, T, bm_, hs)
    out += gable_fill(prefix + "Gable", bm_)
    if detail:          # plaster lining on the inside faces (rooms are plaster, not brick)
        pl = mat("paper"); lz0, lz1 = F1 - 0.05, EAVE - 0.06
        clip = lambda hs: [(a, b, max(za, lz0), min(zb, lz1)) for (a, b, za, zb) in hs]
        wall_x("LineF", -W2 + T, W2 - T, -D2 + T + 0.011, lz0, lz1, 0.02, pl, clip(holes_f))
        wall_x("LineB", -W2 + T, W2 - T, D2 - T - 0.011, lz0, lz1, 0.02, pl, clip(holes_b))
        for sx in (-1, 1):
            hs = [(y - w / 2, y + w / 2, w1a, w1b) for y, w in SIDE_WINDOWS] + [(y - w / 2, y + w / 2, w2a, w2b) for y, w in SIDE_WINDOWS]
            wall_y("LineS", -D2 + T, D2 - T, sx * (W2 - T - 0.011), lz0, lz1, 0.02, pl, hs)
        box("CellarCeil", (0, 2.25, -0.14), (2 * (W2 - T), D2 - T + 0.2, 0.04), mat("raw"))
    # cellar window wells / foundation band
    out.append(box(prefix + "Found", (0, 0, G + 0.2), (2 * W2 + 0.04, 2 * D2 + 0.04, 0.4), mat("conc")))
    # windows
    for x, w in FRONT_WINDOWS_1:
        p, g = window_unit('x', x, w, -D2 + 0.08, w1a, w1b, lit_glass=lit); out += p; glass_ += g
    for x, w in FRONT_WINDOWS_2:
        p, g = window_unit('x', x, w, -D2 + 0.08, w2a, w2b, lit_glass=lit); out += p; glass_ += g
    for x, w in BACK_WINDOWS_1:
        p, g = window_unit('x', x, w, D2 - 0.08, w1a + (0.25 if x > 0 else 0), w1b, lit_glass=lit); out += p; glass_ += g
    for x, w in BACK_WINDOWS_2:
        p, g = window_unit('x', x, w, D2 - 0.08, w2a, w2b, lit_glass=lit); out += p; glass_ += g
    for sx in (-1, 1):
        for y, w in SIDE_WINDOWS:
            for (a, b) in ((w1a, w1b), (w2a, w2b)):
                p, g = window_unit('y', y, w, sx * (W2 - 0.08), a, b, lit_glass=lit); out += p; glass_ += g
    # brick lintels / sills in a lighter course
    for x, w in FRONT_WINDOWS_1 + FRONT_WINDOWS_2:
        for z in ((w1b, w2b) if True else ()):
            pass
    # roof + fascia + chimney
    rf = gable_roof(prefix + "Roof", mat("roof")); out.append(rf)
    for sy in (-1, 1):
        out.append(box(prefix + "Fascia", (0, sy * (D2 + 0.45), EAVE - 0.1), (2 * W2 + 0.95, 0.04, 0.22), mat("trim")))
        out.append(box(prefix + "Soffit", (0, sy * (D2 + 0.22), EAVE - 0.2), (2 * W2 + 0.9, 0.5, 0.03), mat("trim")))
    out.append(box(prefix + "Chimney", (3.4, 1.6, (EAVE + RIDGE) / 2 + 0.8), (0.7, 0.5, RIDGE - EAVE + 2.4), bm_))
    out.append(box(prefix + "ChimCap", (3.4, 1.6, RIDGE + 1.38), (0.8, 0.6, 0.06), mat("conc")))
    for k in range(4):
        out.append(box(prefix + "Louvre", (W2 + 0.03, 0, RIDGE - 0.6 - k * 0.1), (0.06, 0.5, 0.035), mat("trim"), rot=(0, math.radians(30), 0)))
    # porch: slab, steps, two columns, a flat roof
    pz = -0.06
    out.append(box(prefix + "PorchDeck", (0.6, -D2 - 1.1, pz - 0.27), (4.2, 2.2, 0.54), mat("conc")))
    for k in range(3):
        out.append(box(prefix + "Step", (0.15, -D2 - 2.35 - k * 0.3, G + 0.42 - k * 0.18), (1.6, 0.32, 0.18), mat("conc")))
    for x in (-1.3, 2.5):
        out.append(box(prefix + "PCol", (x, -D2 - 2.0, 1.25), (0.32, 0.32, 2.6), bm_))
    out.append(box(prefix + "PRoof", (0.6, -D2 - 1.15, 2.62), (4.5, 2.5, 0.16), mat("trim")))
    out.append(box(prefix + "PRail", (2.0, -D2 - 2.0, 0.42), (1.0, 0.12, 0.9), bm_))
    out.append(box(prefix + "PRail", (-0.8, -D2 - 2.0, 0.42), (0.6, 0.12, 0.9), bm_))
    return out, glass_, c


# ============================================================================ interiors (hero house only)
def interiors(c):
    """Floors, partitions, stairs, closet + hatch, attic, cellar. Doors are hinge empties in c."""
    pl = mat("paper"); fl = mat("floor"); tr = mat("trim"); cl = mat("plaster")
    IX, IY = W2 - T, D2 - T       # inner faces
    # floors / ceilings
    box("FloorFront", (0, (-IY - 0.2) / 2, -0.06), (2 * IX, IY - 0.2, 0.12), fl)
    box("FloorKitchen", (1.35, (IY - 0.2) / 2, -0.06), (IX + 1.5, IY + 0.2, 0.12), mat("lino"))
    box("FloorBack", (-2.85, (IY - 0.2) / 2, -0.06), (IX - 1.5, IY + 0.2, 0.12), fl)
    c["cellar_hole"] = (-3.6, 3.0)
    # ceiling of ground floor / floor upstairs (with stair opening x[0,0.9] y[-3.6,-0.2])
    sl = []
    sl.append(box("Slab", (-(IX + 0.0) / 2, 0, (C1 + F2) / 2), (IX, 2 * IY, F2 - C1), cl))
    sl.append(box("Slab", ((0.9 + IX) / 2, 0, (C1 + F2) / 2), (IX - 0.9, 2 * IY, F2 - C1), cl))
    sl.append(box("Slab", (0.45, (-0.2 + IY) / 2, (C1 + F2) / 2), (0.9, IY + 0.2, F2 - C1), cl))
    sl.append(box("Slab", (0.45, (-IY - 3.6) / 2, (C1 + F2) / 2), (0.9, IY - 3.6, F2 - C1), cl))
    box("FloorUp", (0, 0, F2 + 0.005), (2 * IX, 2 * IY, 0.01), fl).hide_render = True     # (visual floor pieces below)
    for (cx, cy, sx, sy) in ((-(IX) / 2, 0, IX, 2 * IY), ((0.9 + IX) / 2, 0, IX - 0.9, 2 * IY), (0.45, (-0.2 + IY) / 2, 0.9, IY + 0.2), (0.45, (-IY - 3.6) / 2, 0.9, IY - 3.6)):
        box("FloorUp", (cx, cy, F2 + 0.006), (sx, sy, 0.012), fl)
    # upstairs ceiling with the closet hatch hole
    hx, hy = HATCH
    cz = (C2 + EAVE - 0.05) / 2; ct = EAVE - 0.05 - C2
    box("CeilUp", ((-IX + hx - HATCH_W / 2) / 2, 0, cz), (hx - HATCH_W / 2 + IX, 2 * IY, ct), cl)
    box("CeilUp", ((IX + hx + HATCH_W / 2) / 2, 0, cz), (IX - hx - HATCH_W / 2, 2 * IY, ct), cl)
    box("CeilUp", (hx, (-IY + hy - HATCH_L / 2) / 2, cz), (HATCH_W, hy - HATCH_L / 2 + IY, ct), cl)
    box("CeilUp", (hx, (IY + hy + HATCH_L / 2) / 2, cz), (HATCH_W, IY - hy - HATCH_L / 2, ct), cl)
    # hatch panel (slides aside over the boards in the crawl space)
    c["hatch"] = box("HatchPanel", (hx, hy, EAVE - 0.03), (HATCH_W + 0.06, HATCH_L + 0.06, 0.02), mat("raw"))
    c["hatch_home"] = Vector((hx, hy, EAVE - 0.03))
    # ---------- partitions, ground floor (t = 0.12)
    t = 0.12; DH = 2.1
    wall_y("PartA", -IY, -0.2, -0.6, F1, C1, t, pl, [(-1.6, -0.75, F1, DH)])                  # bedroom | hall (door)
    wall_y("PartB", -IY, -0.2, 0.9, F1, C1, t, pl, [(-3.3, -1.3, F1, 2.3)])                    # hall | front room (wide arch)
    wall_x("PartC", -IX, IX, -0.2, F1, C1, t, pl, [(-0.55, 0.0, F1, DH), (2.4, 3.3, F1, DH), (-3.0, -2.2, F1, DH)])  # front | back
    wall_y("PartD", -0.2, IY, -1.5, F1, C1, t, pl, [(1.2, 2.1, F1, DH)])                       # back room | kitchen
    # ---------- partitions, upstairs
    wall_y("PartUA", -IY, 1.8, -0.6, F2, C2, t, pl, [(-3.1, -2.3, F2, F2 + DH)])
    wall_y("PartUB", -IY, 1.8, 0.9, F2, C2, t, pl, [(-1.2, -0.4, F2, F2 + DH)])
    wall_x("PartUC", -IX, IX, -0.2, F2, C2, t, pl, [(-0.55, 0.85, F2, F2 + DH)])
    wall_x("PartUD", -0.6, 0.9, 1.8, F2, C2, t, pl, [(-0.3, 0.5, F2, F2 + DH)])
    # the closet in the upstairs bedroom (back-right corner): x[-1.8,-0.6] y[-1.2,-0.2]
    # the closet (about 1 m wide): x[-1.6,-0.6] y[-1.2,-0.2]; shelf + hanging rail at the back, the slot above
    cpl = mat("plaster")
    wall_x("ClosetF", -1.6, -0.6, -1.2, F2, C2, 0.1, pl, [(-1.45, -0.75, F2, F2 + 2.0)])
    wall_y("ClosetS", -1.2, -0.2, -1.6, F2, C2, 0.1, pl)
    box("ClosetLiningL", (-1.545, -0.7, F2 + 1.25), (0.01, 0.98, 2.5), cpl)
    box("ClosetLiningR", (-0.665, -0.7, F2 + 1.25), (0.01, 0.98, 2.5), cpl)
    box("ClosetLiningB", (-1.1, -0.265, F2 + 1.25), (0.86, 0.01, 2.5), cpl)
    c["closet_door"] = hinge_door("ClosetDoor", (-1.45, -1.25, F2), 0.7, 2.0, 0.035, mat("door"))
    box("ClosetShelf", (-1.1, -0.43, F2 + 1.78), (0.9, 0.34, 0.025), mat("oak"))
    box("ClosetRod", (-1.1, -0.52, F2 + 1.7), (0.9, 0.02, 0.02), mat("chrome"))
    for k, (x, col) in enumerate(((-1.45, (0.3, 0.25, 0.2)), (-1.33, (0.35, 0.33, 0.3)))):
        box("ClosetCoat", (x, -0.52, F2 + 1.15), (0.06, 0.45, 1.0), fabric("Coat%d" % k, col, 0.95, 0.3, 300), bevel=0.02)
    for k in range(3):
        box("HatBox", (-1.35 + 0.28 * k, -0.42, F2 + 1.88), (0.24, 0.24, 0.18), pbr("Box%d" % k, (0.5 - 0.06 * k, 0.42, 0.32), 0.8), bevel=0.01)
    # doors
    c["front_door"] = hinge_door("FrontDoor", (FRONT_DOOR[0] - FRONT_DOOR[1] / 2 + 0.03, -D2 + 0.12, F1), FRONT_DOOR[1] - 0.06, 2.1, 0.045, mat("door"))
    c["back_door"] = hinge_door("BackDoor", (BACK_DOOR[0] - BACK_DOOR[1] / 2 + 0.03, D2 - 0.12, F1), BACK_DOOR[1] - 0.06, 2.05, 0.045, mat("door"))
    c["bed_door"] = hinge_door("BedDoor", (-0.6, -1.58, F1), 0.8, 2.05, 0.04, mat("door"), axis='y')
    c["upbed_door"] = hinge_door("UpBedDoor", (-0.6, -3.08, F2), 0.75, 2.05, 0.04, mat("door"), axis='y')
    # stairs: 13 risers from y=-3.55 to -0.2 along +y, x[0.0,0.9]
    n = 13; rise = F2 / n; run = 3.35 / n
    for k in range(n):
        box("Tread", (0.45, -3.55 + run * (k + 0.5), rise * (k + 1) - 0.02), (0.9, run + 0.03, 0.04), mat("oak"))
        box("Riser", (0.45, -3.55 + run * k, rise * (k + 0.5)), (0.9, 0.02, rise), tr)
    box("Stringer", (0.02, -1.9, 1.45), (0.04, 3.6, 0.3), tr, rot=(math.atan2(F2, 3.35), 0, 0))
    for k in range(12):
        y = -3.4 + k * 0.28; z = rise * ((y + 3.55) / run) + 0.45
        box("Baluster", (0.03, y, z), (0.03, 0.03, 0.9), tr)
    box("Handrail", (0.03, -1.9, 1.45 + 0.95), (0.06, 4.4, 0.06), mat("oak"), rot=(math.atan2(F2, 3.35), 0, 0))
    box("UpRail", (-0.02, -2.0, F2 + 0.9), (0.06, 3.4, 0.06), mat("oak"))
    for k in range(10):
        box("UpBal", (-0.02, -3.5 + k * 0.33, F2 + 0.45), (0.03, 0.03, 0.9), tr)
    # baseboards & picture rails along the main rooms (cheap: a few strips)
    for (x0, x1, y) in ((-IX, -0.6, -IY + 0.01), (0.9, IX, -IY + 0.01)):
        box("Base", ((x0 + x1) / 2, y, 0.08), (x1 - x0, 0.02, 0.16), tr)
        box("Base", ((x0 + x1) / 2, y, F2 + 0.08), (x1 - x0, 0.02, 0.16), tr)
    # ---------- attic crawl space: joists, boards, rafters underside
    for k in range(16):
        x = -IX + 0.25 + k * 0.55
        box("Joist", (x, 0, EAVE + 0.02), (0.05, 2 * IY, 0.08), mat("raw"))
    boards = [(-2.6, 0.5), (-1.2, 1.4), (0.6, 1.2)]            # loose boards laid over the joists near the hatch
    for (bx, bw) in boards:
        box("AtticBoard", (bx, 0.1, EAVE - 0.025), (bw, 1.6, 0.025), mat("raw"))
    for k in range(18):
        x = -W2 + 0.25 + k * 0.5
        for sy in (-1, 1):
            ang = math.atan2(RIDGE - EAVE, D2 + 0.45)
            box("Rafter", (x, sy * (D2 + 0.45) / 2, (EAVE + RIDGE) / 2 - 0.2), (0.05, (D2 + 0.45) / math.cos(ang), 0.14), mat("raw"), rot=(-sy * ang, 0, 0))
    for sy in (-1, 1):
        ang = math.atan2(RIDGE - EAVE, D2 + 0.45)
        box("Sheathing", (0, sy * (D2 + 0.45) / 2, (EAVE + RIDGE) / 2 - 0.29), (2 * W2, (D2 + 0.45) / math.cos(ang), 0.02), mat("planks"), rot=(-sy * ang, 0, 0))
    # ---------- cellar under the back rooms
    cz0 = -2.7
    box("CellarFloor", (0, 2.25, cz0), (2 * IX, IY + 0.2 + 0.4, 0.1), mat("conc"))
    for x in (-IX, IX):
        box("CellarWall", (x, 2.25, (cz0 + G) / 2), (0.3, IY + 0.6, -cz0 + G), mat("stone"))
    box("CellarWall", (0, IY, (cz0 + G) / 2), (2 * IX, 0.3, -cz0 + G), mat("stone"))
    box("CellarWall", (0, -0.35, (cz0 + G) / 2), (2 * IX, 0.3, -cz0 + G), mat("stone"))
    box("CellarWallHi", (0, 2.25, (G - 0.12) / 2), (2 * IX + 0.6, IY + 0.6, 0.0), mat("stone")).hide_render = True
    return c


def stove(loc, rot_z=0.0):
    """Cast-iron kitchen range with a stove pipe, and the iron shaker tool hung on its rail."""
    ir = mat("iron"); parts = []
    parts.append(box("Stove", (0, 0, 0.42), (1.05, 0.68, 0.7), ir, bevel=0.02))
    parts.append(box("StoveTop", (0, 0, 0.8), (1.12, 0.72, 0.05), ir, bevel=0.01))
    for x in (-0.28, 0.28):
        for y in (-0.15, 0.15):
            parts.append(cyl("Lid", (x - 0.05, y, 0.83), 0.11, 0.012, ir, 24))
    parts.append(box("Warmer", (0, 0.22, 1.42), (1.05, 0.28, 0.05), ir, bevel=0.01))
    parts.append(box("WarmerBack", (0, 0.34, 1.1), (1.05, 0.04, 0.6), ir, bevel=0.01))
    parts.append(box("Oven", (0.22, -0.345, 0.45), (0.45, 0.02, 0.42), mat("enamel"), bevel=0.01))
    parts.append(box("Firebox", (-0.3, -0.345, 0.55), (0.3, 0.02, 0.3), ir, bevel=0.01))
    for x in (-0.4, 0.45):
        parts.append(cyl("Leg", (x, -0.25, 0.04), 0.035, 0.09, ir, 12))
        parts.append(cyl("Leg", (x, 0.25, 0.04), 0.035, 0.09, ir, 12))
    parts.append(cyl("Pipe", (-0.3, 0.3, 2.1), 0.075, 1.6, ir, 20))
    parts.append(box("Rail", (0, -0.4, 0.72), (1.0, 0.02, 0.02), mat("chrome")))
    s = join(parts, "Stove"); s.location = loc; s.rotation_euler = (0, 0, rot_z)
    return s


def shaker_tool(name="StoveTool"):
    """The heavy iron grate shaker: a bar with a forked socket end and a looped handle (modelled lying along X)."""
    ir = mat("iron")
    parts = [cyl("ToolBar", (0, 0, 0.015), 0.012, 0.62, ir, 12, rot=(0, math.radians(90), 0)),
             box("ToolSocket", (0.33, 0, 0.02), (0.07, 0.05, 0.04), ir),
             box("ToolFork", (0.38, 0.018, 0.02), (0.05, 0.012, 0.03), ir), box("ToolFork", (0.38, -0.018, 0.02), (0.05, 0.012, 0.03), ir)]
    bpy.ops.mesh.primitive_torus_add(major_radius=0.045, minor_radius=0.01, location=(-0.35, 0, 0.012), rotation=(0, 0, 0))
    tor = bpy.context.active_object; tor.data.materials.append(ir); parts.append(tor)
    return join(parts, name)


def icebox(loc, rot_z=0.0):
    """1930s oak icebox: two doors (the lower one hinged so it can open), nickel latches."""
    oak = mat("oak"); parts = [box("Icebox", (0, 0, 0.72), (0.8, 0.55, 1.44), oak, bevel=0.015)]
    parts.append(box("IceTop", (0, 0, 1.46), (0.84, 0.58, 0.04), oak, bevel=0.01))
    parts.append(box("IceUpper", (0.0, -0.28, 1.18), (0.7, 0.02, 0.4), oak, bevel=0.01))
    parts.append(box("IceLatch", (0.28, -0.3, 1.18), (0.05, 0.03, 0.1), mat("chrome")))
    ib = join(parts, "Icebox"); ib.location = loc; ib.rotation_euler = (0, 0, rot_z)
    # interior (pale zinc) and the lower door on a hinge
    e = bpy.data.objects.new("IceDoorHinge", None); bpy.context.collection.objects.link(e)
    dpart = [box("IceDoor", (0.35, 0, 0.0), (0.7, 0.03, 0.75), oak, bevel=0.01), box("IceLatch2", (0.62, -0.03, 0.05), (0.05, 0.03, 0.1), mat("chrome"))]
    d = join(dpart, "IceDoor"); d.parent = e
    lin = box("IceLining", (0, -0.25, 0.52), (0.68, 0.02, 0.72), pbr("Zinc", (0.6, 0.62, 0.62), 0.35, 0.8))
    lin.hide_render = True
    M = Matrix.Translation(loc) @ Matrix.Rotation(rot_z, 4, 'Z')
    e.matrix_world = M @ Matrix.Translation((-0.35, -0.29, 0.52))
    return ib, e


def kitchen_set(c):
    """Kitchen x[-1.5,4.2] y[-0.2,4.7]: stove on the right wall, icebox by the back door, table, sink under the window."""
    c["stove"] = stove((3.75, 1.6, 0), math.radians(90))
    ib, door = icebox((-0.85, 4.35, 0), 0.0); c["icebox"] = ib; c["ice_door"] = door
    for (cx, cy, sx, sy) in ((1.35, 4.68, 5.6, 0.02), (4.18, 2.25, 0.02, 4.8), (1.35, -0.13, 5.6, 0.02)):
        box("Wainscot", (cx, cy, 0.6), (sx, sy, 1.2), pbr("Beadboard", (0.72, 0.74, 0.62), 0.5))
        box("WainCap", (cx, cy, 1.21), (sx + 0.01, sy + 0.03, 0.03), mat("trim"))
    box("Sink", (1.1, 4.4, 0.85), (1.1, 0.5, 0.2), mat("enamel"), bevel=0.03)
    box("SinkCab", (1.1, 4.4, 0.4), (1.2, 0.52, 0.75), mat("trim"), bevel=0.01)
    box("Counter", (2.4, 4.4, 0.9), (1.4, 0.55, 0.04), mat("oak"))
    box("CounterCab", (2.4 - 0.4, 4.4, 0.44), (0.6, 0.52, 0.85), mat("trim"), bevel=0.01)
    box("WallCab", (2.3, 4.5, 1.85), (1.0, 0.34, 0.6), mat("trim"), bevel=0.01)
    r, _ = ph.model("WoodenTable_02", loc=(1.2, 1.9, 0.0)); c["k_table"] = r
    chairs = []
    for (x, y, rz) in ((0.4, 1.9, math.radians(-90)), (2.0, 1.9, math.radians(90)), (1.2, 2.7, math.radians(180))):
        ch, _ = ph.model("dining_chair_02", loc=(x, y, 0), rot_z=rz); chairs.append(ch)
    c["k_chairs"] = chairs
    try:
        r, _ = ph.model("vintage_electric_kettle", loc=(3.6, 1.35, 0.83))
    except Exception:
        pass
    sock, _ = ph.model("pull_chain_light_socket", loc=(1.3, 2.0, C1)); c["k_bulb_obj"] = sock
    c["k_light"] = point((1.3, 2.0, C1 - 0.25), 60, (1.0, 0.72, 0.42), 0.05)
    c["tool"] = shaker_tool(); c["tool"].location = (3.62, 1.75, 0.6); c["tool"].rotation_euler = (math.radians(90), 0, math.radians(90))


def front_room_set(c):
    """Front room x[0.9,4.2] y[-4.7,-0.2]: armchair by a lamp, sofa, radio cabinet, guitar, railroad lantern, photos."""
    ar, _ = ph.model("ArmChair_01", loc=(3.2, -2.0, 0), rot_z=math.radians(120)); c["armchair"] = ar
    ar2, _ = ph.model("Rockingchair_01", loc=(2.2, -3.6, 0), rot_z=math.radians(200)); c["chair2"] = ar2
    ph.model("painted_wooden_shelves", loc=(4.0, -3.0, 0), rot_z=math.radians(90))
    ph.model("vintage_radio_transceiver", loc=(3.9, -3.9, 0.0), rot_z=math.radians(90), scale=0.9)
    st, _ = ph.model("side_table_01", loc=(3.75, -1.2, 0)); c["side_table"] = st
    lamp, _ = ph.model("vintage_oil_lamp", loc=(3.75, -1.2, 0.55), scale=0.9); c["lamp_obj"] = lamp
    c["lamp"] = point((3.75, -1.2, 1.15), 45, (1.0, 0.68, 0.38), 0.08)
    ph.model("Lantern_01", loc=(4.0, -3.6, 1.55), scale=0.8)
    ph.model("mantel_clock_01", loc=(4.0, -2.4, 1.57), rot_z=math.radians(90))
    ph.model("standing_picture_frame_01", loc=(2.35, -4.45, 0.0), rot_z=math.radians(170), scale=1.0) if False else None
    rug = box("Rug", (2.6, -2.4, 0.004), (2.6, 2.0, 0.008), fabric("Rug", (0.32, 0.1, 0.07), 0.95, 0.3, 300))
    for k, y in enumerate((-3.2, -2.6)):
        ph.model("fancy_picture_frame_01", loc=(4.18, y, 1.75), rot_z=math.radians(90), scale=0.6)


def front_bedroom_set(c):
    """Front bedroom x[-4.2,-0.6] y[-4.7,-0.2]: iron bed, nightstand with a lamp, a wooden chair, a dresser."""
    b, _ = ph.model("old_bed_frame", loc=(-3.4, -2.2, 0), scale=1.0); c["bed1"] = b
    box("Mattress1", (-3.4, -2.2, 0.48), (0.86, 1.9, 0.18), fabric("Ticking", (0.75, 0.72, 0.65), 0.9, 0.3, 500), bevel=0.04)
    box("Quilt1", (-3.4, -2.0, 0.59), (0.95, 1.4, 0.05), fabric("Quilt", (0.5, 0.25, 0.18), 0.9, 0.5, 300), bevel=0.02)
    ns, _ = ph.model("ClassicNightstand_01", loc=(-3.4, -3.5, 0)); c["ns1"] = ns
    ch, _ = ph.model("dining_chair_02", loc=(-1.6, -3.6, 0), rot_z=math.radians(30)); c["bed_chair"] = ch
    ph.model("painted_wooden_cabinet", loc=(-4.0, -0.9, 0), rot_z=math.radians(-90), scale=0.9)
    lamp, _ = ph.model("vintage_oil_lamp", loc=(-3.4, -3.5, 0.7), scale=0.7)
    c["bed_lamp"] = point((-3.4, -3.5, 1.2), 25, (1.0, 0.68, 0.38), 0.06)
    sock, _ = ph.model("pull_chain_light_socket", loc=(-2.4, -2.4, C1)); c["bed_bulb_obj"] = sock


def upstairs_set(c):
    """Upstairs bedroom x[-4.2,-0.6] y[-4.7,-0.2]: a bed, a dresser and the closet; a ceiling bulb."""
    b, _ = ph.model("old_bed_frame", loc=(-3.4, -2.7, F2), rot_z=0.0, scale=1.0); c["bed2"] = b
    box("Mattress2", (-3.4, -2.7, F2 + 0.48), (0.86, 1.9, 0.18), fabric("Ticking2", (0.75, 0.72, 0.65), 0.9, 0.3, 500), bevel=0.04)
    box("Quilt2", (-3.4, -2.5, F2 + 0.59), (0.98, 1.45, 0.05), fabric("Quilt2", (0.42, 0.5, 0.58), 0.9, 0.5, 300), bevel=0.02)
    box("Pillow2", (-3.4, -1.95, F2 + 0.66), (0.6, 0.3, 0.1), fabric("Pillow2", (0.88, 0.87, 0.84), 0.9, 0.3, 600), bevel=0.04)
    ph.model("hanging_picture_frame_01", loc=(-4.17, -3.0, F2 + 1.7), rot_z=math.radians(-90), scale=0.8)
    ph.model("hanging_picture_frame_03", loc=(-2.0, -0.33, F2 + 1.65), rot_z=math.pi, scale=0.7)
    # moonlight through the front window: a spot outside, so the sash bars cast their shape on the floor
    ml = bpy.data.lights.new("MoonSpot", 'SPOT'); ml.energy = 0.0; ml.spot_size = math.radians(30); ml.spot_blend = 0.15
    ml.color = (0.6, 0.72, 1.0); ml.shadow_soft_size = 0.02
    mo = bpy.data.objects.new("MoonSpot", ml); bpy.context.collection.objects.link(mo); aim_obj(mo, (-2.4, -D2 - 3.0, F2 + 4.0), (-2.6, -3.2, F2))
    c["moonspot"] = mo
    ph.model("painted_wooden_nightstand", loc=(-4.0, -3.9, F2), rot_z=math.radians(-90))
    sock, _ = ph.model("pull_chain_light_socket", loc=(-2.4, -2.4, C2)); c["up_bulb_obj"] = sock
    c["up_light"] = point((-2.4, -2.4, C2 - 0.25), 40, (1.0, 0.7, 0.42), 0.05)
    cab, _ = ph.model("painted_wooden_cabinet", loc=(-2.6, -0.5, F2), rot_z=math.pi, scale=0.85); c["up_cab"] = cab
    ph.model("hanging_picture_frame_02", loc=(-3.4, -0.33, F2 + 1.7), rot_z=math.pi, scale=0.8)
    uc, _ = ph.model("dining_chair_02", loc=(-0.95, -2.0, F2), rot_z=math.radians(-110)); c["up_chair"] = uc
    rug = box("RugUp", (-2.6, -2.6, F2 + 0.015), (2.2, 1.6, 0.008), fabric("RugUp", (0.25, 0.12, 0.08), 0.95, 0.3, 300))
    c["closet_light"] = point((-1.1, -0.7, C2 - 0.3), 0.0, (1.0, 0.7, 0.42), 0.05)


def attic_set(c):
    """The crawl space beside the hatch: a hot plate, a 1940s radio, a bare wire to the outlet, a thin blanket."""
    hx, hy = HATCH; z = EAVE
    # single-coil electric hot plate: black enamel drum on three stubby feet, an open spiral coil on top
    blk = pbr("HPBlack", (0.03, 0.03, 0.03), 0.35, 0.2)
    coil = emissive("Coil", (1.0, 0.28, 0.05), 0.0)
    cpb = coil.node_tree.nodes.get("Principled BSDF")
    if cpb: cpb.inputs['Base Color'].default_value = (0.08, 0.06, 0.05, 1); cpb.inputs['Roughness'].default_value = 0.5
    parts = [cyl("HPBody", (0, 0, 0.055), 0.11, 0.07, blk, 40), cyl("HPRim", (0, 0, 0.092), 0.105, 0.008, pbr("HPChrome", (0.6, 0.6, 0.6), 0.25, 1.0), 40)]
    for k in range(3):
        a_ = k * 2.094
        parts.append(cyl("HPFoot", (0.08 * math.cos(a_), 0.08 * math.sin(a_), 0.01), 0.012, 0.02, blk, 10))
    cu = bpy.data.curves.new("HPSpiral", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.004; cu.bevel_resolution = 2
    sp = cu.splines.new('POLY'); n = 140; sp.points.add(n - 1)
    for i in range(n):
        th = i / n * 5 * 2 * math.pi; r = 0.012 + 0.075 * i / n
        sp.points[i].co = (r * math.cos(th), r * math.sin(th), 0.1, 1)
    so = bpy.data.objects.new("HPSpiral", cu); bpy.context.collection.objects.link(so); so.data.materials.append(coil)
    hp = join(parts, "HotPlate")
    hp.location = (hx + 0.85, hy + 0.55, z); c["hotplate"] = hp
    so.location = hp.location
    c["coil_mat"] = coil
    # 1930s tombstone radio: walnut cabinet with an arched top, cloth grille with fretwork bars, round dial, two knobs
    wd = wood("RadioWood", (0.09, 0.045, 0.02), (0.25, 0.13, 0.06), scale=(0.3, 6, 6))
    grille = fabric("Grille", (0.55, 0.45, 0.3), 0.9, 0.2, 800); bake = pbr("Knob", (0.06, 0.035, 0.02), 0.3)
    rp = [box("RadioBody", (0, 0, 0.15), (0.3, 0.2, 0.3), wd, bevel=0.012),
          cyl("RadioArch", (0, 0, 0.3), 0.15, 0.2, wd, 40, rot=(math.radians(90), 0, 0)),
          box("RadioGrille", (0, -0.101, 0.27), (0.17, 0.004, 0.17), grille),
          cyl("RadioGrilleTop", (0, -0.101, 0.355), 0.085, 0.004, grille, 32, rot=(math.radians(90), 0, 0)),
          cyl("RadioDial", (0, -0.103, 0.09), 0.032, 0.006, emissive("Dial", (1.0, 0.72, 0.38), 0.5), 24, rot=(math.radians(90), 0, 0))]
    for k in range(3):
        rp.append(box("Fret", (-0.05 + 0.05 * k, -0.105, 0.3), (0.012, 0.006, 0.2), wd))
    for sx in (-1, 1):
        rp.append(cyl("RKnob", (sx * 0.09, -0.108, 0.07), 0.018, 0.02, bake, 16, rot=(math.radians(90), 0, 0)))
    rad = join(rp, "Radio")
    rad.location = (hx + 0.35, hy + 0.85, z); rad.rotation_euler = (0, 0, math.radians(-10)); c["radio"] = rad
    # cloth-covered cords along the joist to a crude splice into the house wiring on a post
    cord = fabric("ClothCord", (0.22, 0.16, 0.1), 0.95, 0.3, 2000)
    def wire(nm, pts, d=0.0045):
        cu = bpy.data.curves.new(nm, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = d
        sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
        for bp, p_ in zip(sp.bezier_points, pts):
            bp.co = p_; bp.handle_left_type = bp.handle_right_type = 'AUTO'
        o = bpy.data.objects.new(nm, cu); bpy.context.collection.objects.link(o); o.data.materials.append(cord); return o
    wire("Wire", [(hx + 0.4, hy + 0.97, z + 0.06), (hx + 0.7, hy + 1.0, z + 0.015), (hx + 1.1, hy + 1.02, z + 0.015), (hx + 1.27, hy + 1.06, z + 0.28)])
    wire("Wire2", [(hx + 0.96, hy + 0.55, z + 0.05), (hx + 1.05, hy + 0.8, z + 0.015), (hx + 1.2, hy + 1.0, z + 0.02), (hx + 1.28, hy + 1.06, z + 0.27)])
    wire("HouseWire", [(hx + 1.3, hy + 1.06, z + 0.3), (hx + 1.32, hy + 1.07, z + 0.6), (hx + 1.33, hy + 1.08, z + 0.95)], d=0.005)
    box("Post", (hx + 1.3, hy + 1.12, z + 0.45), (0.08, 0.08, 0.9), mat("raw"))
    tape = pbr("Tape", (0.02, 0.02, 0.02), 0.6)
    cyl("Splice", (hx + 1.29, hy + 1.06, z + 0.3), 0.012, 0.07, tape, 12)                   # a lump of black friction tape
    cyl("SpliceTwist", (hx + 1.29, hy + 1.06, z + 0.355), 0.004, 0.04, pbr("Copper", (0.7, 0.4, 0.25), 0.3, 1.0), 8)
    bl = box("Blanket", (hx + 0.1, hy + 1.9, z + 0.02), (0.8, 1.7, 0.03), fabric("Blanket", (0.32, 0.3, 0.24), 0.95, 0.4, 250), bevel=0.012)
    bl.rotation_euler = (0, 0, math.radians(8)); c["blanket"] = bl
    # a few cans and a jar
    for k in range(3):
        cyl("Can", (hx + 0.5 + 0.09 * k, hy + 0.15, z + 0.06), 0.035, 0.11, pbr("Tin", (0.55, 0.52, 0.48), 0.35, 0.9), 16)
    c["hp_light"] = point((hx + 0.9, hy + 0.5, z + 0.15), 0.0, (1.0, 0.35, 0.08), 0.06)
    c["attic_fill"] = point((hx + 0.3, hy + 1.2, z + 0.9), 1.5, (0.7, 0.75, 0.9), 0.6)
    c["attic_fill2"] = area_light((hx - 1.5, hy + 0.5, z + 1.2), (0, 0, 0), 2.0, 0.0, (0.75, 0.8, 0.95))
    c["attic_fill2"].visible_camera = False          # faint light leaking in at the eaves
    c["upstairs_hall"] = point((0.2, 0.8, C2 - 0.3), 0.0, (1.0, 0.75, 0.5), 0.05)


def cellar_set(c):
    """Cellar: wooden shelves of preserve jars along the back wall; one gap where a jar is missing; steps down."""
    z0 = -2.65
    sh = mat("raw")
    c["jars"] = []
    cols = [(0.55, 0.12, 0.08), (0.7, 0.45, 0.08), (0.35, 0.3, 0.12), (0.6, 0.2, 0.25)]
    rng = np.random.default_rng(3)
    jar_glass = lambda col: pbr("JarGlass", col, 0.08, 0.0, **{'Transmission Weight': 0.85, 'IOR': 1.45})
    jm = [jar_glass(col) for col in cols]; lid = pbr("JarLid", (0.6, 0.55, 0.4), 0.3, 1.0)
    for row in range(4):
        z = z0 + 0.45 + row * 0.48
        box("Shelf", (0.0, 4.35, z), (4.2, 0.34, 0.03), sh)
        for k in range(14):
            x = -1.95 + k * 0.3
            if row == 2 and k == 7:
                c["gap"] = Vector((x, 4.33, z + 0.1)); continue
            jx = cyl("Jar", (x, 4.33, z + 0.1), 0.055, 0.17, jm[int(rng.integers(0, 4))], 20)
            cyl("JarLid", (x, 4.33, z + 0.195), 0.052, 0.02, lid, 20)
            c["jars"].append(jx)
    for x in (-2.1, 2.1):
        box("ShelfPost", (x, 4.35, z0 + 1.0), (0.05, 0.34, 2.0), sh)
    # the taken jar (moves in the cellar shots)
    c["jar_taken"] = cyl("JarTaken", (c["gap"].x, c["gap"].y, c["gap"].z), 0.055, 0.17, jm[0], 20)
    # steps down from the back room hole (x -3.6 .. -2.8, y 1.0 .. 3.4)
    n = 11
    for k in range(n):
        box("CStep", (-3.5, 0.5 + k * 0.26, -0.12 - (k + 1) * 0.235), (0.8, 0.28, 0.04), sh)
    sock, _ = ph.model("pull_chain_light_socket", loc=(0.0, 3.2, G - 0.05))
    c["cellar_light"] = point((0.0, 3.2, G - 0.3), 30, (1.0, 0.7, 0.42), 0.05)


def point(loc, energy, col, radius=0.05):
    l = bpy.data.lights.new("Point", 'POINT'); l.energy = energy; l.color = col; l.shadow_soft_size = radius
    o = bpy.data.objects.new("Point", l); bpy.context.collection.objects.link(o); o.location = loc
    o.visible_glossy = False
    return o


# ============================================================================ street, trees, leaves, snow
_TREE = {}


def tree_collection(season):
    """An elm stand-in (Poly Haven jacaranda, broad vase crown) as a collection to instance along the street."""
    key = season
    if key in _TREE:
        return _TREE[key]
    col = bpy.data.collections.new("Elm_" + season)
    root, ms = ph.model("jacaranda_tree", loc=(0, 0, -1000), scale=0.5)
    for o in [root] + list(root.children_recursive):
        for cc in o.users_collection:
            cc.objects.unlink(o)
        col.objects.link(o)
    root.location = (0, 0, 0)
    for m in ms:
        for mm in m.data.materials:
            if "leaves" in mm.name:
                if season == "autumn":
                    retint(mm, (1.0, 0.75, 0.42), hue=0.42, sat=1.25, val=1.0)
                elif season == "summer":
                    retint(mm, (0.55, 0.85, 0.45), hue=0.62, sat=0.8, val=0.8)
        if season == "winter" and any("leaves" in mm.name for mm in m.data.materials):
            m.hide_render = True
    _TREE[key] = col
    return col


def tree_at(col, loc, rot_z, scale=1.0, name="Elm"):
    e = bpy.data.objects.new(name, None); e.instance_type = 'COLLECTION'; e.instance_collection = col
    bpy.context.collection.objects.link(e); e.location = loc; e.rotation_euler = (0, 0, rot_z); e.scale = (scale,) * 3
    e["base_rot"] = rot_z
    return e


def sway_trees(c, sec, amp=0.006):
    for k, e in enumerate(c.get("trees", [])):
        e.rotation_euler = (amp * math.sin(0.9 * sec + k * 1.7), amp * 0.7 * math.sin(0.7 * sec + k), e["base_rot"])


def leaf_cloud(n, center, spread, z_top, col=(0.75, 0.33, 0.06), seed=1):
    """Small falling leaves (flat planes) to animate with fall_leaves()."""
    rng = np.random.default_rng(seed)
    lm = pbr("FallLeaf", col, 0.6, 0.0, **{'Subsurface Weight': 0.0})
    lm2 = pbr("FallLeaf2", (col[0] * 0.8, col[1] * 1.2, col[2]), 0.6)
    leaves = []
    for k in range(n):
        bpy.ops.mesh.primitive_plane_add(size=1)
        o = bpy.context.active_object; o.name = "Leaf"; o.scale = (0.06, 0.035, 1)
        bpy.ops.object.transform_apply(scale=True)
        o.data.materials.append(lm if k % 2 else lm2)
        o["p0"] = (center[0] + rng.uniform(-spread[0], spread[0]), center[1] + rng.uniform(-spread[1], spread[1]), z_top + rng.uniform(-3, 3))
        o["ph"] = float(rng.uniform(0, 6.28)); o["sp"] = float(rng.uniform(0.6, 1.1))
        leaves.append(o)
    return leaves


def fall_leaves(leaves, sec, ground=G + 0.01, drift=(0.35, 0.1)):
    for o in leaves:
        x0, y0, z0 = o["p0"]; ph_ = o["ph"]; sp = o["sp"]
        h = z0 - ground
        z = z0 - (sec * sp + ph_ * 1.6) % (h + 0.001)
        tt = sec + ph_
        o.location = (x0 + drift[0] * tt + 0.35 * math.sin(1.7 * tt), y0 + drift[1] * tt + 0.25 * math.cos(1.3 * tt), z)
        o.rotation_euler = (1.2 * math.sin(2.1 * tt), 1.4 * math.cos(1.6 * tt), tt * 1.1)


def street(c, season, tod):
    """Road, sidewalks, lawns, neighbours (left, right, across), elms, street lamps, a picket of hedges."""
    ground = mat("snow") if season == "winter" else (mat("leafground") if season == "autumn" else mat("grass"))
    box("Lawn", (0, -2, G - 0.05), (90, 60, 0.1), ground)
    box("Road", (0, ROAD_Y, G - 0.1), (120, 7.0, 0.1), mat("snow") if season == "winter" else mat("asphalt"))
    for sy in (-1, 1):
        box("Curb", (0, ROAD_Y + sy * 3.6, G - 0.04), (120, 0.25, 0.14), mat("conc"))
        box("Walk", (0, ROAD_Y + sy * 5.0, G - 0.02), (120, 1.6, 0.06), mat("snow") if season == "winter" else mat("pave"))
    box("Path", (0.15, (ROAD_Y + 5.8 - D2 - 2.6) / 2, G - 0.015), (1.4, -(ROAD_Y + 5.8) - D2 - 2.6 + 0.0, 0.06), mat("snow") if season == "winter" else mat("pave"))
    # neighbours: copies of the shell with different brick and lit windows at night
    lit = tod != "day"
    nb = []
    for k, (x, y, rz, br) in enumerate(((-13.0, 0.0, 0, "brick2"), (13.0, 0.5, 0, "brick3"), (-6.5, ROAD_Y * 2 - 0.0, math.pi, "brick3"), (6.5, ROAD_Y * 2 + 0.5, math.pi, "brick2"), (-26, 0.2, 0, "brick"), (26, 0.0, 0, "brick2"))):
        parts, g, _ = shell("N%d" % k, br, detail=False)
        o = join(parts + g, "Neighbour%d" % k); o.location = (x, y, 0); o.rotation_euler = (0, 0, rz)
        if lit and k in (1, 2, 4):          # a lamp behind the shades (real glass, no glowing cards)
            for (lx, lz) in ((-2.4, 1.4), (2.6, 1.4)) if k != 4 else ((2.6, 3.9),):
                M = Matrix.Translation((x, y, 0)) @ Matrix.Rotation(rz, 4, 'Z')
                point(tuple(M @ Vector((lx, -D2 + 0.9, lz))), 40, (1.0, 0.7, 0.42), 0.15)
        nb.append(o)
    c["neighbours"] = nb
    col = tree_collection(season)
    trees = []
    for k, (x, y) in enumerate(((-8.5, ROAD_Y + 4.3), (9.0, ROAD_Y + 4.2), (-21, ROAD_Y + 4.3), (21.5, ROAD_Y + 4.3),
                                (-9.0, ROAD_Y - 4.3), (8.0, ROAD_Y - 4.3), (-22, ROAD_Y - 4.3), (22, ROAD_Y - 4.2), (34, ROAD_Y + 4.3), (-34, ROAD_Y - 4.3))):
        trees.append(tree_at(col, (x, y, G), k * 1.3, 0.95 + 0.1 * (k % 3)))
    c["trees"] = trees
    lamps = []
    for x in (-15.0, 16.0):
        r, ms = ph.model("street_lamp_01", loc=(x, ROAD_Y + 4.3, G), scale=1.1)
        if tod != "day":
            lamps.append(point((x, ROAD_Y + 4.3, G + 4.1), 220, (1.0, 0.74, 0.45), 0.12))
    c["street_lamps"] = lamps
    for x in (-3.2, 3.6):
        for k in range(4):
            box("Hedge", (x + (k - 1.5) * 0.7 * (1 if x > 0 else -1), -D2 - 1.0, G + 0.35), (0.8, 0.7, 0.75), pbr("Hedge", (0.06, 0.09, 0.04) if season != "autumn" else (0.12, 0.09, 0.03), 0.85), bevel=0.25)


def snow_cover(c):
    """Snow on the roof slopes, the porch roof and window sills (thin white slabs)."""
    sn = mat("snow")
    ang = math.atan2(RIDGE - EAVE, D2 + 0.45)
    for sy in (-1, 1):
        o = box("RoofSnow", (0, sy * (D2 + 0.45) / 2, (EAVE + RIDGE) / 2 + 0.02), (2 * W2 + 0.9, (D2 + 0.45) / math.cos(ang), 0.06), sn, rot=(-sy * ang, 0, 0))
    box("PorchSnow", (0.6, -D2 - 1.15, 2.73), (4.5, 2.5, 0.06), sn)


def lighting(c, season, tod):
    s = bpy.context.scene
    if tod == "night":
        world_flat((0.022, 0.036, 0.07), 1.0)
        moon = sun(32, -120, energy=0.6, color=(0.62, 0.74, 1.0), angle_deg=1.0); c["moon"] = moon
        s.view_settings.exposure = 1.5
    elif season == "winter":
        world_sky(sun_elev_deg=14, sun_rot_deg=200, strength=0.45, tint=(0.78, 0.82, 0.9), air=2.0, aerosol=4.0)
        sun(14, -70, energy=0.6, color=(0.85, 0.88, 0.95), angle_deg=8.0)
        s.view_settings.exposure = 0.1
    elif season == "autumn":
        world_sky(sun_elev_deg=16, sun_rot_deg=235, strength=0.45, tint=(1.0, 0.92, 0.82))
        sun(18, -55, energy=3.2, color=(1.0, 0.8, 0.58), angle_deg=1.5)
        s.view_settings.exposure = -0.1
    else:
        world_sky(sun_elev_deg=38, sun_rot_deg=150, strength=0.4, tint=(0.95, 0.97, 1.0))
        sun(38, -40, energy=3.2, color=(1.0, 0.93, 0.84), angle_deg=1.2)
        s.view_settings.exposure = -0.3


# ============================================================================ people (1941-42, unnamed MakeHuman figures)
HAT = {}


def person(name, kind):
    """kind: philip | helen | friend | neighbour_m | neighbour_w | detective | officer | thin | captain | nurse | boy"""
    spec = {
        "philip": dict(gender=1.0, years=86, weight=0.38, height=0.4, cloth="male_casualsuit05", cv=dict(hue=0.47, sat=0.5, val=0.8), hair="short02", hv=0.9, hat=False, skin="old_lightskinned_male_diffuse.png"),
        "helen": dict(gender=0.0, years=82, weight=0.5, height=0.4, cloth="female_elegantsuit01", cv=dict(hue=0.95, sat=0.35, val=1.4), hair="roll", roll=(0.12, 0.75), hv=0.8, hat=False, skin="old_lightskinned_female_diffuse.png"),
        "friend": dict(gender=0.0, years=66, weight=0.55, height=0.45, cloth="female_elegantsuit01", cv=dict(hue=0.35, sat=0.4, val=1.1), hair="roll", roll=(0.35, 0.45), hv=0.6, hat=False, skin="old_lightskinned_female_diffuse.png"),
        "neighbour_m": dict(gender=1.0, years=50, weight=0.5, height=0.5, cloth="male_casualsuit03", cv=dict(hue=0.55, sat=0.5, val=0.8), hair="short01", hv=0.3, hat=False),
        "neighbour_w": dict(gender=0.0, years=45, weight=0.5, height=0.5, cloth="female_elegantsuit01", cv=dict(hue=0.6, sat=0.45, val=1.2), hair="roll", roll=(0.6, 0.05), hv=0.25, hat=False),
        "detective": dict(gender=1.0, years=45, weight=0.5, height=0.55, cloth="male_elegantsuit01", cv=dict(hue=0.08, sat=0.3, val=0.42), hair="short02", hv=0.2, hat=True),
        "detective2": dict(gender=1.0, years=38, weight=0.55, height=0.5, cloth="male_casualsuit01", cv=dict(hue=0.6, sat=0.2, val=0.38), hair="short01", hv=0.15, hat=True),
        "officer": dict(gender=1.0, years=35, weight=0.5, height=0.55, cloth="male_elegantsuit01", cv=dict(hue=0.64, sat=0.45, val=0.26), hair="short01", hv=0.15, hat=True),
        "captain": dict(gender=1.0, years=58, weight=0.6, height=0.5, cloth="male_elegantsuit01", cv=dict(hue=0.55, sat=0.15, val=0.38), hair="short02", hv=0.7, hat=False),
        "thin": dict(gender=1.0, years=66, weight=0.0, height=0.45, muscle=0.1, skin="old_lightskinned_male_diffuse2.png", cloth="male_casualsuit01", cv=dict(hue=0.1, sat=0.1, val=1.9), hair="short02", hv=0.12, hat=False),
        "nurse": dict(gender=0.0, years=30, weight=0.45, height=0.5, cloth="female_elegantsuit01", cv=dict(hue=0.5, sat=0.0, val=2.2), hair="roll", roll=(0.5, 0.0), hv=0.25, hat=False),
        "son": dict(gender=1.0, years=42, weight=0.5, height=0.55, cloth="male_casualsuit01", cv=dict(hue=0.08, sat=0.3, val=0.25), hair="short02", hv=0.25, hat=True),
    }[kind]
    sk = spec.get("skin") or ("middleage_lightskinned_female_diffuse.png" if spec["gender"] < 0.5 else "middleage_lightskinned_male_diffuse.png")
    h = Human(name, gender=spec["gender"], years=spec["years"], muscle=spec.get("muscle", 0.5), weight=spec["weight"], height=spec["height"],
              skin=sk, eyelashes="eyelashes01")
    add_asset(h, "clothes", spec["cloth"], rough=0.8, sheen=0.3, **spec["cv"])
    add_asset(h, "clothes", "shoes02" if spec["gender"] < 0.5 else "shoes01", sat=0.3 if kind == "thin" else 1.0, val=0.08 if kind == "thin" else 0.15, rough=0.6)
    if spec["hat"]:
        add_hat(h, "grey" if kind in ("detective", "son") else "black")
    elif spec["hair"] == "roll":
        roll_hair(h, *spec["roll"])
    else:
        add_asset(h, "hair", spec["hair"], sat=0.1 if spec["hv"] > 0.6 else 0.5, val=spec["hv"], rough=0.45)
    if spec["gender"] < 0.5:
        long_skirt(h)
    elif kind != "thin" and "casualsuit" in spec["cloth"]:
        wool_trousers(h, (0.2, 0.17, 0.13) if kind == "philip" else (0.14, 0.14, 0.15))
    if kind == "thin":
        ragged(h); coneys_hair(h)
    h.kind = kind
    return h


def ragged(h):
    """Coneys after nine months in the crawl space: grime and torn dark patches on the clothes, a matted beard,
    hollow cheeks (darkened), unkempt hair (scaled up, roughened)."""
    for o in h.parts:
        for m in o.data.materials:
            if m is None or not m.use_nodes or "Principled BSDF" not in m.node_tree.nodes:
                continue
            N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
            if "casualsuit" in m.name or "shoes" in m.name:
                tc = N.new("ShaderNodeTexCoord")
                n = N.new("ShaderNodeTexNoise"); n.inputs['Scale'].default_value = 5; n.inputs['Detail'].default_value = 10; L.new(tc.outputs['Object'], n.inputs['Vector'])
                v = N.new("ShaderNodeTexVoronoi"); v.inputs['Scale'].default_value = 3.0; L.new(tc.outputs['Object'], v.inputs['Vector'])
                tear = N.new("ShaderNodeMath"); tear.operation = 'LESS_THAN'; tear.inputs[1].default_value = 0.22; L.new(v.outputs['Distance'], tear.inputs[0])
                src = p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].links else None
                grime = N.new("ShaderNodeMix"); grime.data_type = 'RGBA'; grime.blend_type = 'MULTIPLY'
                gr_ = N.new("ShaderNodeMapRange"); gr_.inputs['From Min'].default_value = 0.48; gr_.inputs['From Max'].default_value = 0.62
                L.new(n.outputs['Fac'], gr_.inputs['Value']); L.new(gr_.outputs['Result'], grime.inputs['Factor'])      # blotchy stains
                if src: L.new(src, grime.inputs[6])
                grime.inputs[7].default_value = (0.16, 0.12, 0.08, 1)
                holes = N.new("ShaderNodeMix"); holes.data_type = 'RGBA'; L.new(tear.outputs[0], holes.inputs['Factor'])
                L.new(grime.outputs[2], holes.inputs[6]); holes.inputs[7].default_value = (0.42, 0.3, 0.23, 1)
                if "casualsuit" in m.name:
                    me_ = o.data; zz = np.array([v.co.z for v in me_.vertices]); cut = zz.min() + 0.52 * (zz.max() - zz.min())
                    la = me_.color_attributes.new("legs", 'FLOAT_COLOR', 'POINT')
                    for i, z_ in enumerate(zz):
                        f_ = 1.0 if z_ < cut else 0.0; la.data[i].color = (f_, f_, f_, 1)
                    at = N.new("ShaderNodeAttribute"); at.attribute_name = "legs"; at.attribute_type = 'GEOMETRY'
                    dk = N.new("ShaderNodeMix"); dk.data_type = 'RGBA'; dk.blend_type = 'MULTIPLY'; L.new(at.outputs['Fac'], dk.inputs['Factor'])
                    L.new(holes.outputs[2], dk.inputs[6]); dk.inputs[7].default_value = (0.1, 0.085, 0.07, 1)
                    L.new(dk.outputs[2], p.inputs['Base Color'])
                else:
                    L.new(holes.outputs[2], p.inputs['Base Color'])
                p.inputs['Roughness'].default_value = 0.95
                for k_ in ('Sheen Weight', 'Specular IOR Level', 'Coat Weight'):
                    if k_ in p.inputs: p.inputs[k_].default_value = 0.0 if k_ != 'Specular IOR Level' else 0.15
    # beard + sunken cheeks: a vertex colour on the body, darkening the lower face (follows the rig)
    me = h.body.data
    co = np.array([v.co[:] for v in me.vertices])
    hv = h.vertex_region(["head", "jaw"], 0.5) if "jaw" in h.rig.bones else h.vertex_region(["head"], 0.5)
    face = np.zeros(len(co))
    if len(hv):
        hc = co[hv]; zmin = hc[:, 2].min(); zmax = hc[:, 2].max(); ymin = hc[:, 1].min()
        for i in np.where((co[:, 2] > zmin) & (np.abs(co[:, 0]) < 0.1))[0]:      # by position: the lips/cheeks are weighted to face bones, not 'head'
            x, y, z = co[i]
            top = zmin + (0.088 if abs(x) < 0.045 else 0.112)                     # full beard: jaw, cheeks, moustache
            beard = min(1.0, max(0.0, (top - z) / 0.018)) * (1.0 if y < ymin + 0.125 else max(0.0, 1.0 - (y - ymin - 0.125) / 0.03))
            if zmin + 0.058 < z < zmin + 0.071 and abs(x) < 0.02 and y < ymin + 0.04:
                beard *= 0.3                                                          # lips show through
            cheek = 0.5 * max(0.0, 1.0 - abs(z - (zmin + 0.1)) / 0.03) * (1.0 if abs(x) > 0.035 and y < ymin + 0.07 else 0.0)
            eye = 0.55 * max(0.0, 1.0 - abs(z - (zmin + 0.145)) / 0.022) * max(0.0, 1.0 - abs(abs(x) - 0.033) / 0.02) * (1.0 if y < ymin + 0.06 else 0.0)
            face[i] = min(1.0, beard + cheek + eye)
    attr = me.color_attributes.new("beard", 'FLOAT_COLOR', 'POINT')
    for i, f in enumerate(face):
        attr.data[i].color = (f, f, f, 1.0)
    m = h.skin_mat; N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    a = N.new("ShaderNodeAttribute"); a.attribute_name = "beard"; a.attribute_type = 'GEOMETRY'
    tc = N.new("ShaderNodeTexCoord"); n = N.new("ShaderNodeTexNoise"); n.inputs['Scale'].default_value = 900; L.new(tc.outputs['Object'], n.inputs['Vector'])
    f = N.new("ShaderNodeMath"); f.operation = 'MULTIPLY'; L.new(a.outputs['Fac'], f.inputs[0]); L.new(n.outputs['Fac'], f.inputs[1])
    f2 = N.new("ShaderNodeMath"); f2.operation = 'MULTIPLY'; f2.inputs[1].default_value = 2.2; f2.use_clamp = True; L.new(f.outputs[0], f2.inputs[0])
    src = p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].links else None
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(f2.outputs[0], mx.inputs['Factor'])
    if src: L.new(src, mx.inputs[6])
    mx.inputs[7].default_value = (0.13, 0.115, 0.1, 1)
    dn = N.new("ShaderNodeTexNoise"); dn.inputs['Scale'].default_value = 14; dn.inputs['Detail'].default_value = 8; L.new(tc.outputs['Object'], dn.inputs['Vector'])
    dr = N.new("ShaderNodeMapRange"); dr.inputs['From Min'].default_value = 0.4; dr.inputs['From Max'].default_value = 0.68; dr.inputs['To Max'].default_value = 0.75; L.new(dn.outputs['Fac'], dr.inputs['Value'])
    dmx = N.new("ShaderNodeMix"); dmx.data_type = 'RGBA'; dmx.blend_type = 'MULTIPLY'; L.new(dr.outputs['Result'], dmx.inputs['Factor'])
    L.new(mx.outputs[2], dmx.inputs[6]); dmx.inputs[7].default_value = (0.42, 0.33, 0.24, 1)
    L.new(dmx.outputs[2], p.inputs['Base Color'])
    inv = N.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; L.new(f2.outputs[0], inv.inputs[1])
    for k_ in ('Subsurface Weight', 'Specular IOR Level'):         # beard: no skin translucency or sheen through it
        if k_ in p.inputs and not p.inputs[k_].links:
            sv = N.new("ShaderNodeMath"); sv.operation = 'MULTIPLY'; sv.inputs[1].default_value = p.inputs[k_].default_value
            L.new(inv.outputs[0], sv.inputs[0]); L.new(sv.outputs[0], p.inputs[k_])
    bmp = N.new("ShaderNodeBump"); bmp.inputs['Strength'].default_value = 0.6; L.new(f.outputs[0], bmp.inputs['Height'])
    if not p.inputs['Normal'].links: L.new(bmp.outputs['Normal'], p.inputs['Normal'])
    vg = h.body.vertex_groups.new(name="beardvg")
    if len(hv):
        hc_ = co[hv]; z0_ = hc_[:, 2].min(); y0_ = hc_[:, 1].min()
        sel = [int(i) for i in hv if z0_ + 0.005 < co[i, 2] < (z0_ + 0.083 if abs(co[i, 0]) < 0.05 else z0_ + 0.1) and co[i, 1] < y0_ + 0.12
               and not (z0_ + 0.06 < co[i, 2] < z0_ + 0.072 and abs(co[i, 0]) < 0.022 and co[i, 1] < y0_ + 0.045)]   # lips
        vg.add(sel, 1.0, 'REPLACE')
    bd = h.body.copy(); bd.name = h.name + "_beard"; bpy.context.collection.objects.link(bd)
    mk = bd.modifiers.new("beardmask", 'MASK'); mk.vertex_group = "beardvg"
    tx = bpy.data.textures.new(h.name + "_beardtx", 'CLOUDS'); tx.noise_scale = 0.003
    dsp = bd.modifiers.new("beardfuzz", 'DISPLACE'); dsp.texture = tx; dsp.strength = 0.009; dsp.mid_level = 0.0
    bd.modifiers.new("beardshell", 'SOLIDIFY').thickness = 0.003
    bm_ = bpy.data.materials.new("BeardHair"); bm_.use_nodes = True; bp_ = bm_.node_tree.nodes["Principled BSDF"]
    bp_.inputs['Base Color'].default_value = (0.1, 0.085, 0.07, 1); bp_.inputs['Roughness'].default_value = 0.95
    if 'Sheen Weight' in bp_.inputs: bp_.inputs['Sheen Weight'].default_value = 0.0
    bN = bm_.node_tree.nodes; bL = bm_.node_tree.links
    btc = bN.new("ShaderNodeTexCoord"); bn = bN.new("ShaderNodeTexNoise"); bn.inputs['Scale'].default_value = 400; bL.new(btc.outputs['Object'], bn.inputs['Vector'])
    bmx = bN.new("ShaderNodeMix"); bmx.data_type = 'RGBA'; bL.new(bn.outputs['Fac'], bmx.inputs['Factor'])
    bmx.inputs[6].default_value = (0.07, 0.06, 0.05, 1); bmx.inputs[7].default_value = (0.17, 0.155, 0.14, 1); bL.new(bmx.outputs[2], bp_.inputs['Base Color'])
    for sl in bd.material_slots:
        sl.link = 'OBJECT'; sl.material = bm_
    bpy.data.objects.remove(bd, do_unlink=True)          # painted beard reads better than a shell
    for o in h.parts:            # hair: bigger, matted
        if "long01" in o.name:   # long hair cut ragged at the collar: strands, face left clear
            import bmesh
            bm2 = bmesh.new(); bm2.from_mesh(o.data)
            hz = h.body.data.vertices; ztop = max(v.co.z for v in hz)
            rng_ = np.random.default_rng(5)
            kill = [v for v in bm2.verts if v.co.z < ztop - 0.27 - 0.05 * rng_.random()]
            bmesh.ops.delete(bm2, geom=kill, context='VERTS'); bm2.to_mesh(o.data); bm2.free()
            for m in o.data.materials:
                if m and m.use_nodes and "Principled BSDF" in m.node_tree.nodes:
                    hN = m.node_tree.nodes; hL = m.node_tree.links; hp_ = hN["Principled BSDF"]
                    hp_.inputs['Roughness'].default_value = 0.95
                    for k_ in ('Sheen Weight', 'Coat Weight'):
                        if k_ in hp_.inputs: hp_.inputs[k_].default_value = 0.0
                    if 'Specular IOR Level' in hp_.inputs: hp_.inputs['Specular IOR Level'].default_value = 0.1
                    if hp_.inputs['Base Color'].links:
                        src_ = hp_.inputs['Base Color'].links[0].from_socket
                        htc = hN.new("ShaderNodeTexCoord"); hw = hN.new("ShaderNodeTexNoise"); hw.inputs['Scale'].default_value = 300; hw.inputs['Detail'].default_value = 2
                        hL.new(htc.outputs['Object'], hw.inputs['Vector'])
                        hr = hN.new("ShaderNodeMapRange"); hr.inputs['From Min'].default_value = 0.35; hr.inputs['From Max'].default_value = 0.75; hr.inputs['To Min'].default_value = 0.05; hr.inputs['To Max'].default_value = 0.4
                        hL.new(hw.outputs['Fac'], hr.inputs['Value'])
                        hm = hN.new("ShaderNodeMix"); hm.data_type = 'RGBA'; hL.new(hr.outputs['Result'], hm.inputs['Factor'])
                        hL.new(src_, hm.inputs[6]); hm.inputs[7].default_value = (0.3, 0.29, 0.27, 1); hL.new(hm.outputs[2], hp_.inputs['Base Color'])
            tx = bpy.data.textures.new(o.name + "_clump", 'CLOUDS'); tx.noise_scale = 0.02
            dm = o.modifiers.new("clump", 'DISPLACE'); dm.texture = tx; dm.strength = 0.012; dm.mid_level = 0.5
        if "bob01" in o.name or "short02" in o.name:
            tx = bpy.data.textures.new(o.name + "_mat", 'CLOUDS'); tx.noise_scale = 0.015
            dm = o.modifiers.new("matted", 'DISPLACE'); dm.texture = tx; dm.strength = 0.014; dm.mid_level = 0.4
            for m in o.data.materials:
                if m and m.use_nodes and "Principled BSDF" in m.node_tree.nodes:
                    m.node_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = 0.9
    return h


def add_hat(h, tone="grey"):
    from human import textured_material, MH
    d = os.path.join(MH, "clothes", "fedora01")
    tex = os.path.join(d, "materials", "fedora_texture_grey.png" if tone == "grey" else "fedora_texture_black.png")
    m = textured_material(h.name + "_fedora", tex, os.path.join(d, "materials", "fedora_normal.png"), rough=0.75, val=0.7 if tone == "grey" else 1.0)
    o, _ = h.add_proxy(os.path.join(d, "fedora.mhpxy"), "fedora", mat=m, subsurf=1)
    return o


def reset_pose(h):
    """Rest pose AND zero body rotation, so procedural poses (world-axis bone turns) are built facing -Y."""
    h.arm.rotation_euler = (0, 0, 0)
    _hm.reset_pose(h)


def rotl(h, bone, axis, deg):
    """Rotate a bone about an axis given in the BODY frame (x = character's left, -y = forward, z = up)."""
    bpy.context.view_layer.update()
    ax = h.arm.matrix_world.to_3x3() @ Vector(axis)
    h.rot(bone, ax, deg)


def ground_to(h, z):
    bpy.context.view_layer.update()
    w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
    h.arm.location.z += z - w[:, 2].min(); bpy.context.view_layer.update()


def arms_relaxed(h, swing=0.0, phase=0.0):
    M = h.arm.matrix_world.to_3x3(); fwd = (M @ Vector((0, -1, 0))).normalized(); left = (M @ Vector((1, 0, 0))).normalized()
    for sd, sg in (("L", 1), ("R", -1)):
        a = math.radians(swing) * math.sin(2 * math.pi * phase + (math.pi if sd == "L" else 0.0))
        up = (Vector((0, 0, -1)) * math.cos(a) + fwd * math.sin(a) + left * (0.12 * sg)).normalized()
        lo = (up + fwd * (0.25 + 0.15 * max(0.0, math.sin(a)))).normalized()
        h.aim(f"upperarm01.{sd}", up); h.aim(f"upperarm02.{sd}", up)
        h.aim(f"lowerarm01.{sd}", lo); h.aim(f"lowerarm02.{sd}", lo); h.aim(f"wrist.{sd}", lo + left * (0.1 * sg))
    fingers_curl(h, 25)


def stand_at(h, loc, face_z, z=None):
    """Standing, arms relaxed; face_z rotation (0 faces -Y). z = floor height (default loc[2])."""
    reset_pose(h); h.arm.location = (loc[0], loc[1], 0); pose_walk(h, 0.0, stride=0.0, arm_swing=0.0)
    h.arm.rotation_euler = (0, 0, face_z); h.arm.location = (loc[0], loc[1], 0); bpy.context.view_layer.update()
    arms_relaxed(h)
    ground_to(h, loc[2] if z is None else z)


def walk_to(h, p0, p1, u, stride=1.25, face=None, swing=14, floor=None):
    """Walk from p0 to p1 (fraction u, 0..1). Faces the direction of travel."""
    p0 = Vector(p0); p1 = Vector(p1); d = p1 - p0; L_ = d.length
    pos = p0.lerp(p1, u)
    reset_pose(h)
    phase = (u * L_ / stride) % 1.0
    pose_walk(h, phase, stride=24, arm_swing=0)
    fz = face if face is not None else math.atan2(d.x, -d.y)
    h.arm.rotation_euler = (0, 0, fz); h.arm.location = (pos.x, pos.y, 0); bpy.context.view_layer.update()
    arms_relaxed(h, swing, phase)
    ground_to(h, pos.z if floor is None else floor)
    return pos


def face_dir(target, frm):
    d = Vector(target) - Vector(frm)
    return math.atan2(d.x, -d.y)


def look(h, yaw=0.0, pitch=0.0):
    """yaw: + turns toward the character's left ; pitch: + looks down."""
    rotl(h, "neck01", (0, 0, 1), yaw * 0.4); rotl(h, "head", (0, 0, 1), yaw * 0.6)
    rotl(h, "head", (1, 0, 0), pitch)


def flashlight(name="Torch"):
    """A 1940s flashlight: spot light with a visible beam (needs haze) parented to an empty."""
    l = bpy.data.lights.new(name, 'SPOT'); l.energy = 60; l.spot_size = math.radians(28); l.spot_blend = 0.5
    l.color = (1.0, 0.88, 0.7); l.shadow_soft_size = 0.02
    o = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(o)
    return o


def aim_obj(o, loc, tgt):
    o.location = loc; d = Vector(tgt) - Vector(loc)
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


# ============================================================================ the whole set
def build_house(season="autumn", tod="day", ext=True, rooms=("kitchen", "front", "bedroom", "upstairs", "attic", "cellar"), haze_room=None):
    _MAT.clear(); _TREE.clear()
    c = dict(season=season, tod=tod)
    lighting(c, season, tod)
    parts, g, _ = shell("H", "brick", detail=True)
    c["shell"] = parts; c["glass"] = g
    interiors(c)
    if "kitchen" in rooms:
        kitchen_set(c)
    if "front" in rooms:
        front_room_set(c)
    if "bedroom" in rooms:
        front_bedroom_set(c)
    if "upstairs" in rooms:
        upstairs_set(c)
    if "attic" in rooms:
        attic_set(c)
    if "cellar" in rooms:
        cellar_set(c)
    if ext:
        street(c, season, tod)
    if season == "winter":
        snow_cover(c)
    # porch light (dim at night) and a window portal for daylight interiors
    c["porch_light"] = point((0.15, -D2 - 0.4, 2.45), 25 if tod == "night" else 0, (1.0, 0.75, 0.45), 0.05)
    if haze_room:
        lo, hi = haze_room
        hz = haze(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2), (hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]), density=0.06, color=(0.9, 0.9, 0.95), anis=0.55)
        c["haze"] = hz
    return c


def day_fill(loc, size, energy, col=(0.9, 0.93, 1.0), rot=(0, 0, 0)):
    """Soft hidden fill (window bounce) for interiors."""
    l = area_light(loc, rot, size, energy, col); l.visible_camera = False; l.visible_glossy = False
    return l


# ============================================================================ 1940s vehicles
def car1940(name, col=(0.02, 0.02, 0.022), kind="sedan", length=5.0, width=1.85):
    """A rounded 1940s sedan / panel van: body, pontoon fenders, running boards, chrome grille, round lamps.
    Returns the root empty (moves the car; local +X is forward) with ['wheels'] and ['tail'] lamp lights."""
    body = pbr(name + "Paint", col, 0.25, 0.5, **{'Coat Weight': 1.0, 'Coat Roughness': 0.06})
    chrome = mat("chrome"); glassm = pbr("CarGlass", (0.015, 0.02, 0.025), 0.04, 0.0, **{'Coat Weight': 1.0})
    tyre = pbr("Tyre", (0.02, 0.02, 0.02), 0.85); white = pbr("Whitewall", (0.75, 0.74, 0.7), 0.6)
    L_, W_ = length, width; parts = []
    parts.append(box("CBody", (0, 0, 0.72), (L_ * 0.98, W_ - 0.2, 0.55), body, bevel=0.2))
    if kind != "van":       # hollow cockpit: the body top is open where the seats are (people inside read through glass)
        parts.append(box("CSeat", (-L_ * 0.1, 0, 1.0), (L_ * 0.4, W_ - 0.3, 0.02), pbr("Seat", (0.08, 0.06, 0.05), 0.7)))
    parts.append(box("CHood", (L_ * 0.28, 0, 0.92), (L_ * 0.38, W_ * 0.62, 0.32), body, bevel=0.14))
    if kind == "van":
        parts.append(box("CCabin", (-L_ * 0.12, 0, 1.55), (L_ * 0.72, W_ - 0.2, 1.4), body, bevel=0.12))
        parts.append(box("CWind", (L_ * 0.235, 0, 1.55), (0.02, W_ - 0.5, 0.45), glassm))
    else:
        cx, cl, cw = -L_ * 0.1, L_ * 0.44, W_ - 0.32
        parts.append(box("CRoof", (cx, 0, 1.6), (cl - 0.1, cw, 0.08), body, bevel=0.035))
        for sx in (-1, 1):
            for sy in (-1, 1):
                parts.append(box("CPillar", (cx + sx * (cl / 2 - 0.06), sy * (cw / 2 - 0.03), 1.3), (0.08, 0.05, 0.6), body))
            parts.append(box("CPillarB", (cx, sx * (cw / 2 - 0.03), 1.3), (0.06, 0.05, 0.6), body))
        gm = mat("glass")
        for sy in (-1, 1):
            parts.append(box("CGlassS", (cx, sy * (cw / 2 - 0.03), 1.3), (cl - 0.16, 0.01, 0.56), gm))
        parts.append(box("CWind", (cx + cl / 2 - 0.02, 0, 1.3), (0.01, cw - 0.1, 0.56), gm))
        parts.append(box("CRear", (cx - cl / 2 + 0.02, 0, 1.3), (0.01, cw - 0.1, 0.56), gm))
        parts.append(box("CDash", (cx + cl / 2 - 0.25, 0, 1.0), (0.3, cw - 0.1, 0.1), pbr("Dash", (0.05, 0.035, 0.03), 0.5)))
    for sy in (-1, 1):
        for sx in (-1, 1):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1, location=(sx * L_ * 0.33, sy * (W_ / 2 - 0.12), 0.62))
            f = bpy.context.active_object; f.scale = (0.62, 0.2, 0.36); f.data.materials.append(body); parts.append(f)
        parts.append(box("CBoard", (0, sy * (W_ / 2 - 0.05), 0.33), (L_ * 0.42, 0.18, 0.04), pbr("Board", (0.05, 0.05, 0.05), 0.7)))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.1, location=(L_ * 0.43, sy * 0.62, 0.95))
        hl = bpy.context.active_object; hl.data.materials.append(emissive("CarHead", (1.0, 0.9, 0.72), 0.0)); parts.append(hl)
        parts.append(box("CTail", (-L_ * 0.49, sy * 0.68, 0.85), (0.04, 0.1, 0.14), emissive("CarTail", (1.0, 0.05, 0.02), 6.0)))
    parts.append(box("CGrille", (L_ * 0.49, 0, 0.78), (0.04, 0.6, 0.38), chrome, bevel=0.04))
    for k in range(7):
        parts.append(box("CGBar", (L_ * 0.505, -0.27 + k * 0.09, 0.78), (0.02, 0.02, 0.34), mat("black")))
    for sx in (-1, 1):
        parts.append(box("CBumper", (sx * L_ * 0.51, 0, 0.45), (0.08, W_ - 0.1, 0.12), chrome, bevel=0.04))
    car = join(parts, name)
    root = bpy.data.objects.new(name + "Root", None); bpy.context.collection.objects.link(root)
    car.parent = root
    wheels = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            w = join([cyl("Tyre", (0, 0, 0), 0.36, 0.2, tyre, 28, rot=(math.radians(90), 0, 0)),
                      cyl("Wall", (0, sy * 0.101, 0), 0.25, 0.005, white, 28, rot=(math.radians(90), 0, 0)),
                      cyl("Hub", (0, sy * 0.105, 0), 0.14, 0.01, chrome, 20, rot=(math.radians(90), 0, 0))], "Wheel")
            w.parent = root; w.location = (sx * L_ * 0.33, sy * (W_ / 2 - 0.15), 0.36); wheels.append(w)
    root["L"] = L_
    root["wheels"] = [w.name for w in wheels]
    return root


def vehicle(name, col, kind="sedan"):
    """The shared realistic 1940s US sedan (nvidia_doc/scenes/vehicles.py); kind 'police' = black and white patrol car."""
    import vehicles
    r = vehicles.make("sedan_1940s_us", color=col, variant="police" if kind == "police" else None, lamps=True)
    r.name = name + "Root"; r["kit"] = 1
    return r


def drive(root, p0, p1, u, heading=None):
    """Place the car along p0->p1 (u in 0..1), wheels rolling."""
    p0 = Vector(p0); p1 = Vector(p1); pos = p0.lerp(p1, u)
    hz = heading if heading is not None else math.atan2((p1 - p0).y, (p1 - p0).x)
    root.location = (pos.x, pos.y, pos.z + (0.05 if root.get("kit") else 0.0)); root.rotation_euler = (0, 0, hz)
    dist = (pos - p0).length
    if root.get("kit"):
        import vehicles
        vehicles.spin_wheels(root, dist)
        return
    for n in root["wheels"]:
        w = bpy.data.objects[n]; w.rotation_euler = (0, -dist / 0.36, 0)


def porch_lamp(c, swing=0.0):
    """A small lantern hanging from the porch ceiling on a chain (can swing)."""
    if "plamp" not in c:
        piv = Vector((0.15, -D2 - 0.6, 2.54))
        l = join([box("PLChain", (0, 0, -0.15), (0.01, 0.01, 0.3), mat("black")),
                  box("PLCage", (0, 0, -0.42), (0.16, 0.16, 0.24), mat("black"), bevel=0.02),
                  box("PLGlass", (0, 0, -0.42), (0.13, 0.13, 0.2), emissive("PLGlow", (1.0, 0.75, 0.45), 2.0 if c.get("tod") == "night" else 0.0))], "PorchLamp")
        e = bpy.data.objects.new("PorchLampPivot", None); bpy.context.collection.objects.link(e); e.location = piv
        l.parent = e; l.location = (0, 0, 0); c["plamp"] = e
        c["porch_light"].parent = e; c["porch_light"].location = (0, 0, -0.5)
    c["plamp"].rotation_euler = (swing, swing * 0.3, 0)


def porch_swing(c, a=0.0):
    if "pswing" not in c:
        piv = Vector((2.2, -D2 - 0.5, 2.52))
        sw = join([box("SwSeat", (0, 0, -1.95), (1.3, 0.5, 0.06), mat("oak")), box("SwBack", (0, 0.24, -1.7), (1.3, 0.04, 0.45), mat("oak")),
                   box("SwChain", (-0.62, 0, -1.0), (0.012, 0.012, 1.9), mat("black")), box("SwChain", (0.62, 0, -1.0), (0.012, 0.012, 1.9), mat("black"))], "PorchSwing")
        e = bpy.data.objects.new("SwingPivot", None); bpy.context.collection.objects.link(e); e.location = piv
        sw.parent = e; c["pswing"] = e
    c["pswing"].rotation_euler = (a, 0, 0)


# ----------------------------------------------------------------------------- strand hair (Coneys)
def hair_mat(name, melanin=0.6, grey=0.3, rough=0.5):
    """Principled Hair BSDF (melanin), a share of strands grey (per-strand random)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    def hb(mel):
        b = N.new("ShaderNodeBsdfHairPrincipled"); b.parametrization = 'MELANIN'
        b.inputs['Melanin'].default_value = mel; b.inputs['Melanin Redness'].default_value = 0.12
        b.inputs['Roughness'].default_value = rough; b.inputs['Radial Roughness'].default_value = 0.6
        if 'Random Roughness' in b.inputs: b.inputs['Random Roughness'].default_value = 0.3
        if 'Random Color' in b.inputs: b.inputs['Random Color'].default_value = 0.2
        return b
    # opaque strands (thin Principled Hair strands read see-through at these sizes): dark brown, and ash grey
    dark = N.new("ShaderNodeBsdfPrincipled"); light = N.new("ShaderNodeBsdfPrincipled")
    dv = 0.11 * (1.0 - melanin) + 0.02
    dark.inputs["Base Color"].default_value = (0.13, 0.085, 0.055, 1); dark.inputs['Roughness'].default_value = rough
    light.inputs["Base Color"].default_value = (0.2, 0.19, 0.175, 1); light.inputs['Roughness'].default_value = rough + 0.1
    hi = N.new("ShaderNodeAttribute"); hi.attribute_name = "strand_rand"; hi.attribute_type = 'GEOMETRY'     # per-strand random (curve attribute)
    lt = N.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = grey; L.new(hi.outputs['Fac'], lt.inputs[0])
    mix = N.new("ShaderNodeMixShader"); L.new(lt.outputs[0], mix.inputs[0]); L.new(dark.outputs[0], mix.inputs[1]); L.new(light.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs['Surface'])
    return m


def strand_hair(h, name, roots, normals, center, n_pts, length, gravity, radius, mat, rng, clump=0.0, frizz=0.002, min_r=None):
    """Grow one strand per root: out along the normal, bending down under gravity, kept outside a head sphere;
    pulled toward a few guide strands (matted clumps); jittered (frizz). Parented to the head bone."""
    n = len(roots)
    P = np.zeros((n, n_pts, 3))
    pos = roots.copy(); d = normals.copy()
    lens = length * (0.7 + 0.6 * rng.random(n))
    step = (lens / (n_pts - 1))[:, None]
    for k in range(n_pts):
        P[:, k] = pos
        d = d + gravity * np.array([0, 0, -1.0]) + 0.15 * rng.normal(size=(n, 3))
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        pos = pos + d * step
        if min_r is not None:                       # keep strands outside the skull, and off the face
            v = pos - center; r = np.linalg.norm(v, axis=1, keepdims=True)
            pos = np.where(r < min_r, center + v / np.maximum(r, 1e-6) * min_r, pos)
            face = (pos[:, 1] < center[1] - 0.03) & (pos[:, 2] < center[2] + 0.05)
            d[:, 1] = np.where(face, np.abs(d[:, 1]) + 0.3, d[:, 1])     # steer back off the face
    if clump > 0:
        g = rng.choice(n, size=max(8, n // 60), replace=False)
        nearest = g[np.argmin(((roots[:, None, :] - roots[g][None, :, :]) ** 2).sum(-1), axis=1)]
        w = (np.linspace(0, 1, n_pts) ** 1.5 * clump)[None, :, None]
        P = P * (1 - w) + (P[nearest] - roots[nearest][:, None, :] + roots[:, None, :]) * w * 0.4 + P[nearest] * w * 0.6
    P += frizz * rng.normal(size=P.shape) * np.linspace(0, 1, n_pts)[None, :, None]
    if min_r is not None:                           # clumping can drag strands back across the face: clear it again
        face = (P[..., 1] < center[1] - 0.025) & (P[..., 2] < center[2] + 0.06) & (np.abs(P[..., 0]) < 0.075)
        first = np.where(face.any(1), face.argmax(1), n_pts)       # cut each strand where it would enter the face
        for i in np.where(first < n_pts)[0]:
            f_ = max(1, first[i]); P[i, f_:] = P[i, f_ - 1]
    cv = bpy.data.hair_curves.new(name)
    cv.add_curves([n_pts] * n)
    cv.position_data.foreach_set('vector', P.reshape(-1).astype(np.float32))
    ra = cv.attributes.get('radius') or cv.attributes.new('radius', 'FLOAT', 'POINT')
    rr = (radius * np.linspace(1.0, 0.35, n_pts))[None, :].repeat(n, 0).reshape(-1)
    ra.data.foreach_set('value', rr.astype(np.float32))
    sr = cv.attributes.new('strand_rand', 'FLOAT', 'POINT'); sr.data.foreach_set('value', np.repeat(rng.random(n), n_pts).astype(np.float32))
    cv.materials.append(mat)
    o = bpy.data.objects.new(name, cv); bpy.context.collection.objects.link(o)
    bpy.context.view_layer.update()
    mw = o.matrix_world.copy()
    o.parent = h.arm; o.parent_type = 'BONE'; o.parent_bone = "head"
    bpy.context.view_layer.update(); o.matrix_world = mw
    h.parts.append(o)
    return o


def coneys_hair(h):
    """Collar-length matted hair and a full scraggly beard as strands on the head (rest pose)."""
    rng = np.random.default_rng(11)
    me = h.body.data; M = h.body.matrix_world
    co = np.array([M @ v.co for v in me.vertices]); nr = np.array([(M.to_3x3() @ v.normal).normalized() for v in me.vertices])
    hv = h.vertex_region(["head"], 0.5)
    hc = co[hv]; zmin, ztop, ymin = hc[:, 2].min(), hc[:, 2].max(), hc[:, 1].min()
    center = np.array([0.0, hc[:, 1].mean() + 0.01, ztop - 0.11])
    # scalp: above the brow at the front, above the ears at the sides, down to the nape at the back
    allv = np.where(co[:, 2] > zmin)[0]
    cy = center[1]
    def scalp(i):
        x, y, z = co[i]
        if y < cy - 0.02: return z > ztop - 0.035               # front: hairline set back, forehead clear
        if y < cy + 0.03: return z > center[2] + 0.0            # sides: above the ears
        return z > zmin + 0.05                                  # back: down to the nape
    sc = np.array([i for i in allv if abs(co[i, 0]) < 0.11 and scalp(i)])
    k = 16000; pick = rng.choice(sc, size=k)
    roots = co[pick] + 0.002 * rng.normal(size=(k, 3)); nrm = nr[pick]
    nrm = nrm + np.where((co[pick][:, 1] < center[1] - 0.02)[:, None], np.array([0, 1.3, 0.5]), 0.0)   # combed back off the brow
    rmin = np.linalg.norm(co[sc] - center, axis=1).mean() + 0.006
    hm = hair_mat("ConeysHair", 0.62, 0.4, 0.55)
    strand_hair(h, h.name + "_hair", roots, nrm * 0.25 + np.array([0, 0.4, 0.1]), center, 12, 0.19, 0.8, 0.00045, hm, rng,
                clump=0.55, frizz=0.0038, min_r=rmin)
    # beard: jaw, chin, cheeks below the cheekbone, moustache
    def bz(i):
        x, y, z = co[i]
        top = zmin + (0.074 if abs(x) < 0.03 else 0.068 if abs(x) < 0.055 else 0.09)
        if y > ymin + 0.12 or z > top or z < zmin - 0.01: return False
        if zmin + 0.058 < z < zmin + 0.071 and abs(x) < 0.02 and y < ymin + 0.04: return False    # lips
        return True
    bvs = np.array([i for i in np.where((co[:, 2] > zmin - 0.03) & (np.abs(co[:, 0]) < 0.1))[0] if bz(i)])
    kb = 9000; pb = rng.choice(bvs, size=kb)
    broots = co[pb] + 0.001 * rng.normal(size=(kb, 3))
    strand_hair(h, h.name + "_beard", broots, nr[pb] * 0.4 + np.array([0, -0.1, -0.8]), center, 6, 0.035, 0.6, 0.00035,
                hair_mat("ConeysBeard", 0.5, 0.45, 0.6), rng, clump=0.3, frizz=0.0045)
    return h


def roll_hair(h, melanin=0.5, grey=0.0, seed=3):
    """1940s set hair: strands swept back from the brow and sides over the crown into a roll at the nape."""
    rng = np.random.default_rng(seed)
    me = h.body.data; M = h.body.matrix_world
    co = np.array([M @ v.co for v in me.vertices]); nr = np.array([(M.to_3x3() @ v.normal).normalized() for v in me.vertices])
    hv = h.vertex_region(["head"], 0.5)
    hc = co[hv]; zmin, ztop, ymin = hc[:, 2].min(), hc[:, 2].max(), hc[:, 1].min()
    center = np.array([0.0, hc[:, 1].mean() + 0.01, ztop - 0.11]); cy = center[1]
    allv = np.where((co[:, 2] > zmin) & (np.abs(co[:, 0]) < 0.11))[0]
    def scalp(i):
        x, y, z = co[i]
        if y < cy - 0.02: return z > ztop - 0.05
        if y < cy + 0.03: return z > center[2] + 0.005
        return z > center[2] - 0.03
    sc = np.array([i for i in allv if scalp(i)])
    rmin = np.linalg.norm(co[sc] - center, axis=1).mean() + 0.004
    k = 9000; pick = rng.choice(sc, size=k)
    roots = co[pick]
    # each strand: along the skull toward the nape roll, then once around the roll
    roll_c = np.stack([np.clip(roots[:, 0] * 0.9, -0.07, 0.07), np.full(k, cy + rmin * 0.85), np.full(k, center[2] - 0.055)], 1)
    rr = 0.026
    n1, n2 = 9, 6; P = np.zeros((k, n1 + n2, 3))
    a = (roots - center) / np.linalg.norm(roots - center, axis=1, keepdims=True)
    b = (roll_c + np.array([0, 0, rr]) - center); b /= np.linalg.norm(b, axis=1, keepdims=True)
    for j in range(n1):
        s = j / (n1 - 1); v = a * (1 - s) + b * s; v /= np.linalg.norm(v, axis=1, keepdims=True)
        P[:, j] = center + v * (rmin + 0.006 * math.sin(math.pi * s))
    start = P[:, n1 - 1]
    for j in range(n2):                                   # curl under, around the horizontal roll axis
        ang = math.pi / 2 + (j + 1) / n2 * 1.7 * math.pi
        P[:, n1 + j] = roll_c + np.array([0.0, rr * math.cos(ang), rr * math.sin(ang)])
    P += 0.0012 * rng.normal(size=P.shape)
    mat = hair_mat(h.name + "_RollHair", melanin, grey, 0.4)
    cv = bpy.data.hair_curves.new(h.name + "_roll"); n_pts = n1 + n2
    cv.add_curves([n_pts] * k); cv.position_data.foreach_set('vector', P.reshape(-1).astype(np.float32))
    ra = cv.attributes.get('radius') or cv.attributes.new('radius', 'FLOAT', 'POINT')
    ra.data.foreach_set('value', np.full(k * n_pts, 0.0005, np.float32))
    sr = cv.attributes.new('strand_rand', 'FLOAT', 'POINT'); sr.data.foreach_set('value', np.repeat(rng.random(k), n_pts).astype(np.float32))
    cv.materials.append(mat)
    o = bpy.data.objects.new(h.name + "_roll", cv); bpy.context.collection.objects.link(o); bpy.context.view_layer.update()
    mw = o.matrix_world.copy(); o.parent = h.arm; o.parent_type = 'BONE'; o.parent_bone = "head"
    bpy.context.view_layer.update(); o.matrix_world = mw; h.parts.append(o)
    return o


def long_skirt(h, top=0.52, bottom=0.25):
    """Extend a knee skirt to mid-calf: a flared open cone weighted to the legs, in the suit's own material."""
    cl = [o for o in h.parts if o.type == 'MESH' and "elegantsuit" in o.name]
    if not cl:
        return None
    me0 = cl[0]; co = np.array([v.co[:] for v in me0.data.vertices])
    band = co[np.abs(co[:, 2] - top - 0.02) < 0.03]
    rx = max(0.15, np.abs(band[:, 0]).max() + 0.005) if len(band) else 0.18
    ry = max(0.12, (band[:, 1].max() - band[:, 1].min()) / 2 + 0.005) if len(band) else 0.14
    cy_ = (band[:, 1].max() + band[:, 1].min()) / 2 if len(band) else 0.0
    nu, nv = 48, 8
    verts, faces = [], []
    for j in range(nv):
        s = j / (nv - 1); z = top - s * (top - bottom); fl = 1.0 + 0.22 * s
        for i in range(nu):
            a = 2 * math.pi * i / nu
            verts.append((rx * fl * math.cos(a), cy_ + ry * fl * math.sin(a), z))
    for j in range(nv - 1):
        for i in range(nu):
            faces.append((j * nu + i, j * nu + (i + 1) % nu, (j + 1) * nu + (i + 1) % nu, (j + 1) * nu + i))
    me = bpy.data.meshes.new(h.name + "_skirt"); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(h.name + "_skirt", me); bpy.context.collection.objects.link(o)
    for m in me0.data.materials: me.materials.append(m)
    me.shade_smooth() if hasattr(me, "shade_smooth") else None
    g = {n: o.vertex_groups.new(name=n) for n in ("root", "upperleg02.L", "lowerleg01.L", "upperleg02.R", "lowerleg01.R")}
    for idx, (x, y, z) in enumerate(verts):
        s = (top - z) / (top - bottom); sd = "L" if x > 0 else "R"; side = min(1.0, abs(x) / (rx * 0.5))
        g["root"].add([idx], 0.6 * (1 - side) + 0.25, 'REPLACE')
        g["upperleg02." + sd].add([idx], side * (1 - 0.5 * s), 'REPLACE')
        g["lowerleg01." + sd].add([idx], side * 0.5 * s, 'REPLACE')
    o.parent = h.arm; am = o.modifiers.new("arm", 'ARMATURE'); am.object = h.arm
    o.modifiers.new("thick", 'SOLIDIFY').thickness = 0.004
    o.modifiers.new("sub", 'SUBSURF').levels = 1
    h.parts.append(o)
    return o


def wool_trousers(h, col=(0.16, 0.14, 0.12)):
    """Casual suits come with jeans: tint everything below the hips to plain wool (rest-pose height mask)."""
    for o in h.parts:
        if o.type != 'MESH' or "casualsuit" not in o.name:
            continue
        me = o.data; zz = np.array([v.co.z for v in me.vertices]); cut = zz.min() + 0.52 * (zz.max() - zz.min())
        if "legs" not in me.color_attributes:
            la = me.color_attributes.new("legs", 'FLOAT_COLOR', 'POINT')
            la.data.foreach_set('color', np.repeat((zz < cut).astype(np.float32), 4))
        for m in me.materials:
            N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
            src = p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].links else None
            at = N.new("ShaderNodeAttribute"); at.attribute_name = "legs"; at.attribute_type = 'GEOMETRY'
            hs = N.new("ShaderNodeHueSaturation"); hs.inputs['Saturation'].default_value = 0.0
            if src: L.new(src, hs.inputs['Color'])
            tint = N.new("ShaderNodeMix"); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'; tint.inputs['Factor'].default_value = 1.0
            L.new(hs.outputs['Color'], tint.inputs[6]); tint.inputs[7].default_value = (*[c_ * 2.2 for c_ in col], 1)
            mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(at.outputs['Fac'], mx.inputs['Factor'])
            if src: L.new(src, mx.inputs[6])
            L.new(tint.outputs[2], mx.inputs[7]); L.new(mx.outputs[2], p.inputs['Base Color'])


def blanket_over(h, mat_, mattress_z, head_clear=0.32, name="Blanket"):
    """A bed blanket fitted over a lying/sitting figure: from the feet end to the chest, over the highest point."""
    bpy.context.view_layer.update()
    w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH' and not o.hide_render])
    hd = h.bone_head("head")
    axis = 1 if abs(w[:, 1].max() - w[:, 1].min()) > abs(w[:, 0].max() - w[:, 0].min()) else 0
    lo, hi = w[:, axis].min(), w[:, axis].max()
    if abs(hd[axis] - hi) < abs(hd[axis] - lo):       # head at the high end
        a, b = lo - 0.08, hd[axis] - head_clear
    else:
        a, b = hd[axis] + head_clear, hi + 0.08
    sel = w[(w[:, axis] > min(a, b)) & (w[:, axis] < max(a, b))]
    other = 1 - axis
    c0 = (sel[:, other].min() + sel[:, other].max()) / 2 if len(sel) else hd[other]
    top = (sel[:, 2].max() if len(sel) else mattress_z + 0.2) + 0.03
    size = [0, 0, top - mattress_z]; size[axis] = abs(b - a); size[other] = 1.0
    loc = [0, 0, (top + mattress_z) / 2]; loc[axis] = (a + b) / 2; loc[other] = c0
    return box(name, tuple(loc), tuple(size), mat_, bevel=0.05)
