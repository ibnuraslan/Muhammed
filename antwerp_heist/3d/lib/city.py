"""The Antwerp diamond district as a place, not a backdrop.

    city.district(hour)          blocks of brick terraces round the Diamond Center (aerial / wide exteriors)
    city.dress_street(A, hour)   wet asphalt, tram rails + wires, parked cars, lit windows, bins, light pools, haze
    city.sky(hour)               a physical (Nishita) sky + sun for dawn / dusk / night

Cars: Sketchfab CC-BY ("Generic passenger car pack" comrade1280, "2000 Audi A4" tonielpro520,
"Compact Hatchback" rccdesign) - credited in README CREDITS.
"""
import math, random
import bpy
from mathutils import Vector
from sets import flat, emit, box, tex, light_point, light_spot, light_area, steel_paint, haze_box
import ship as S

CAR_PACK = "20f9af9b8a404d5cb022ac6fe87f21f5"
AUDI = "22f072849b6a409ebac3a0b13dbb099a"
GOLF = "abbd4e65bbf1475b866d84735088b8ff"


# ----------------------------------------------------------------------------- sky
def sky(hour="dawn", strength=None):
    """Nishita sky + matching sun. hour: dawn (blue hour, sun just under the roofs) | dusk | day | night."""
    sc = bpy.context.scene
    w = sc.world or bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
    N = w.node_tree.nodes; L = w.node_tree.links
    for n in list(N):
        if n.type != 'OUTPUT_WORLD':
            N.remove(n)
    st = N.new("ShaderNodeTexSky")
    elev = {"dawn": 1.5, "dusk": 2.5, "day": 35.0, "night": -12.0}[hour]
    try:
        st.sky_type = 'NISHITA'
        st.sun_elevation = math.radians(max(elev, -2.0)); st.sun_rotation = math.radians(115)
        st.air_density = 1.2; st.dust_density = 2.0; st.altitude = 20
        st.sun_disc = False
    except Exception:
        pass
    bg = N.new("ShaderNodeBackground")
    bg.inputs['Strength'].default_value = strength if strength is not None else {"dawn": 0.35, "dusk": 0.3, "day": 0.6, "night": 0.012}[hour]
    L.new(st.outputs['Color'], bg.inputs['Color']); L.new(bg.outputs[0], N["World Output"].inputs['Surface'])
    if hour in ("day",):
        l = bpy.data.lights.new("city_sun", 'SUN'); l.energy = 3.0; l.color = (1.0, 0.9, 0.78); l.angle = math.radians(1.0)
        o = bpy.data.objects.new("city_sun", l); sc.collection.objects.link(o)
        o.rotation_euler = (math.radians(90 - elev), 0, math.radians(115 + 180))
    return w


# ----------------------------------------------------------------------------- materials
def wet_asphalt(name="wet_asphalt", scale=3.0, wet=0.7):
    """Asphalt after rain: the texture darkened, glossy where water stands (noise puddle mask), streaks of reflections."""
    m = tex("asphalt_02", scale, tint=(0.42, 0.4, 0.39), name=name)
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 0.35; nz.inputs['Detail'].default_value = 6; nz.inputs['Roughness'].default_value = 0.6
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    ramp = N.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].position = 0.42; ramp.color_ramp.elements[1].position = 0.56
    L.new(nz.outputs['Fac'], ramp.inputs['Fac'])
    rough = N.new("ShaderNodeMapRange"); rough.inputs['To Min'].default_value = 0.55; rough.inputs['To Max'].default_value = 0.04
    rough.inputs['From Max'].default_value = 1.0
    mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = wet
    L.new(ramp.outputs['Color'], mul.inputs[0]); L.new(mul.outputs[0], rough.inputs['Value'])
    L.new(rough.outputs['Result'], p.inputs['Roughness'])
    # water flattens the bump in the puddles
    for lk in list(p.inputs['Normal'].links):
        bmp = lk.from_node
        if bmp.type == 'BUMP':
            inv = N.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
            L.new(mul.outputs[0], inv.inputs[1]); L.new(inv.outputs[0], bmp.inputs['Strength'])
    p.inputs['Specular IOR Level'].default_value = 0.6
    return m


def wet_patches(m, wet=0.6, scale=0.35):
    """Add standing water / oil sheen to an existing floor material: glossy, darker patches from a noise mask."""
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 6
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    ramp = N.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].position = 0.5; ramp.color_ramp.elements[1].position = 0.62
    L.new(nz.outputs['Fac'], ramp.inputs['Fac'])
    mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = wet; L.new(ramp.outputs['Color'], mul.inputs[0])
    rough = N.new("ShaderNodeMapRange"); rough.inputs['To Min'].default_value = 0.7; rough.inputs['To Max'].default_value = 0.05
    L.new(mul.outputs[0], rough.inputs['Value']); L.new(rough.outputs['Result'], p.inputs['Roughness'])
    if p.inputs['Base Color'].links:
        src = p.inputs['Base Color'].links[0].from_socket
        dk = N.new("ShaderNodeMix"); dk.data_type = 'RGBA'; dk.blend_type = 'MULTIPLY'; L.new(mul.outputs[0], dk.inputs['Factor'])
        L.new(src, dk.inputs['A']); dk.inputs['B'].default_value = (0.45, 0.45, 0.45, 1); L.new(dk.outputs['Result'], p.inputs['Base Color'])
    return m


def _window_mat(name, lit_col=(1.0, 0.72, 0.42), strength=6.0):
    """Lit window: warm interior glow behind glass, varied per object (random) so a facade is not uniform."""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
    p = N["Principled BSDF"]; p.inputs['Base Color'].default_value = (0.02, 0.02, 0.025, 1); p.inputs['Roughness'].default_value = 0.08
    oi = N.new("ShaderNodeObjectInfo")
    ramp = N.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (*lit_col, 1)
    ramp.color_ramp.elements[1].color = (lit_col[0] * 0.75, lit_col[1] * 0.85, lit_col[2] * 1.1, 1)
    L.new(oi.outputs['Random'], ramp.inputs['Fac'])
    L.new(ramp.outputs['Color'], p.inputs['Emission Color']); p.inputs['Emission Strength'].default_value = strength
    return m


# ----------------------------------------------------------------------------- buildings
def facade_mat(name, base, lit_frac=0.25, night=True, period=(1.9, 3.2)):
    """A city facade in one shader: the base material (brick/render) with a grid of windows (dark glass, a share of
    them lit warm at random), cells keyed to world position so one material serves a whole district."""
    m = base.copy(); m.name = name
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Position'], sep.inputs[0])
    nsep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Normal'], nsep.inputs[0])
    ay = N.new("ShaderNodeMath"); ay.operation = 'ABSOLUTE'; L.new(nsep.outputs['Y'], ay.inputs[0])
    gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.5; L.new(ay.outputs[0], gt.inputs[0])
    hmix = N.new("ShaderNodeMix"); hmix.data_type = 'FLOAT'; L.new(gt.outputs[0], hmix.inputs['Factor'])
    L.new(sep.outputs['Y'], hmix.inputs['A']); L.new(sep.outputs['X'], hmix.inputs['B'])        # along-facade coordinate
    def cell(src, per, lo, hi):
        d = N.new("ShaderNodeMath"); d.operation = 'DIVIDE'; d.inputs[1].default_value = per; L.new(src, d.inputs[0])
        fr = N.new("ShaderNodeMath"); fr.operation = 'FRACT'; L.new(d.outputs[0], fr.inputs[0])
        fl = N.new("ShaderNodeMath"); fl.operation = 'FLOOR'; L.new(d.outputs[0], fl.inputs[0])
        a = N.new("ShaderNodeMath"); a.operation = 'GREATER_THAN'; a.inputs[1].default_value = lo; L.new(fr.outputs[0], a.inputs[0])
        b = N.new("ShaderNodeMath"); b.operation = 'LESS_THAN'; b.inputs[1].default_value = hi; L.new(fr.outputs[0], b.inputs[0])
        mm = N.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; L.new(a.outputs[0], mm.inputs[0]); L.new(b.outputs[0], mm.inputs[1])
        return mm.outputs[0], fl.outputs[0]
    hz = N.new("ShaderNodeMath"); hz.operation = 'ADD'; hz.inputs[1].default_value = -0.6; L.new(sep.outputs['Z'], hz.inputs[0])
    mh, ch = cell(hmix.outputs['Result'], period[0], 0.22, 0.78)
    mv, cv = cell(hz.outputs[0], period[1], 0.25, 0.75)
    win = N.new("ShaderNodeMath"); win.operation = 'MULTIPLY'; L.new(mh, win.inputs[0]); L.new(mv, win.inputs[1])
    above = N.new("ShaderNodeMath"); above.operation = 'GREATER_THAN'; above.inputs[1].default_value = 1.0; L.new(sep.outputs['Z'], above.inputs[0])
    nz_ = N.new("ShaderNodeMath"); nz_.operation = 'ABSOLUTE'; L.new(nsep.outputs['Z'], nz_.inputs[0])
    side = N.new("ShaderNodeMath"); side.operation = 'LESS_THAN'; side.inputs[1].default_value = 0.3; L.new(nz_.outputs[0], side.inputs[0])
    w2 = N.new("ShaderNodeMath"); w2.operation = 'MULTIPLY'; L.new(win.outputs[0], w2.inputs[0]); L.new(side.outputs[0], w2.inputs[1])
    w3 = N.new("ShaderNodeMath"); w3.operation = 'MULTIPLY'; L.new(w2.outputs[0], w3.inputs[0]); L.new(above.outputs[0], w3.inputs[1])
    # random per window cell
    cc = N.new("ShaderNodeCombineXYZ"); L.new(ch, cc.inputs['X']); L.new(cv, cc.inputs['Y'])
    wn = N.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = '3D'; L.new(cc.outputs[0], wn.inputs['Vector'])
    # whole buildings differ: a slow noise over the city scales how many of a facade's windows are lit
    bn = N.new("ShaderNodeTexNoise"); bn.inputs['Scale'].default_value = 0.06; bn.inputs['Detail'].default_value = 1
    L.new(geo.outputs['Position'], bn.inputs['Vector'])
    bsq = N.new("ShaderNodeMath"); bsq.operation = 'POWER'; bsq.inputs[1].default_value = 3.0; L.new(bn.outputs['Fac'], bsq.inputs[0])
    thr = N.new("ShaderNodeMath"); thr.operation = 'MULTIPLY'; thr.inputs[1].default_value = (lit_frac * 3.0) if night else 0.0
    L.new(bsq.outputs[0], thr.inputs[0])
    litc = N.new("ShaderNodeMath"); litc.operation = 'LESS_THAN'
    L.new(wn.outputs['Value'], litc.inputs[0]); L.new(thr.outputs[0], litc.inputs[1])
    litw = N.new("ShaderNodeMath"); litw.operation = 'MULTIPLY'; L.new(litc.outputs[0], litw.inputs[0]); L.new(w3.outputs[0], litw.inputs[1])
    # base colour -> glass where windows
    old = p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].links else None
    mixc = N.new("ShaderNodeMix"); mixc.data_type = 'RGBA'; L.new(w3.outputs[0], mixc.inputs['Factor'])
    if old is not None:
        L.new(old, mixc.inputs['A'])
    else:
        mixc.inputs['A'].default_value = p.inputs['Base Color'].default_value
    mixc.inputs['B'].default_value = (0.02, 0.022, 0.026, 1); L.new(mixc.outputs['Result'], p.inputs['Base Color'])
    rmix = N.new("ShaderNodeMix"); rmix.data_type = 'FLOAT'; L.new(w3.outputs[0], rmix.inputs['Factor'])
    rmix.inputs['A'].default_value = 0.85; rmix.inputs['B'].default_value = 0.06; L.new(rmix.outputs['Result'], p.inputs['Roughness'])
    tint = N.new("ShaderNodeMix"); tint.data_type = 'RGBA'; L.new(wn.outputs['Value'], tint.inputs['Factor'])
    tint.inputs['A'].default_value = (1.0, 0.7, 0.4, 1); tint.inputs['B'].default_value = (0.9, 0.78, 0.6, 1)
    L.new(tint.outputs['Result'], p.inputs['Emission Color'])
    es = N.new("ShaderNodeMath"); es.operation = 'MULTIPLY'; es.inputs[1].default_value = 5.0; L.new(litw.outputs[0], es.inputs[0])
    L.new(es.outputs[0], p.inputs['Emission Strength'])
    return m


def _add_box(bm, c, sz, mi):
    import bmesh
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r["verts"]:
        v.co = Vector((c[0] + v.co.x * sz[0], c[1] + v.co.y * sz[1], c[2] + v.co.z * sz[2]))
    for f in {f for v in r["verts"] for f in v.link_faces}:
        f.material_index = mi


def _add_roof(bm, c, sx, sy, h, along_x, mi):
    """A gabled roof (triangular prism) over a box sx x sy, ridge along the row."""
    hx, hy = sx / 2, sy / 2
    if along_x:
        P = [(-hx, -hy, 0), (hx, -hy, 0), (hx, hy, 0), (-hx, hy, 0), (-hx, 0, h), (hx, 0, h)]
        F = [(0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5), (0, 3, 2, 1)]
    else:
        P = [(-hx, -hy, 0), (hx, -hy, 0), (hx, hy, 0), (-hx, hy, 0), (0, -hy, h), (0, hy, h)]
        F = [(1, 2, 5, 4), (3, 0, 4, 5), (0, 1, 4), (2, 3, 5), (0, 3, 2, 1)]
    vs = [bm.verts.new((c[0] + p[0], c[1] + p[1], c[2] + p[2])) for p in P]
    for f in F:
        bm.faces.new([vs[k] for k in f]).material_index = mi


def townhouse_row(bm, x0, y0, length, facing, rng, nfront, depth=10.0, base_z=0.0):
    """A terrace along a street edge added to the district mesh: narrow Antwerp houses (5-9 m, 3-6 floors) with
    varied roofs - ridge along the street, or a gable to the street (plain or Flemish stepped), chimneys - and now
    and then a post-war block with a flat roof and parapet. facing: the street side (unit x or y)."""
    fx, fy = facing
    ax = Vector((-fy, fx, 0)); nrm = Vector((fx, fy, 0))
    n_slate, n_stone, n_tile = nfront, nfront + 1, nfront + 2
    s = 0.0
    while s < length - 4:
        modern = rng.random() < 0.06
        w = min(rng.uniform(14.0, 24.0) if modern else rng.uniform(5.0, 9.0), length - s)
        floors = rng.choice((6, 7, 8, 9, 11)) if modern else rng.choice((3, 4, 4, 5, 5, 6))
        h = floors * 3.2 + 0.6
        c = Vector((x0, y0, base_z)) + ax * (s + w / 2) - nrm * (depth / 2)
        sx = abs(ax.x) * w + abs(nrm.x) * depth; sy = abs(ax.y) * w + abs(nrm.y) * depth
        _add_box(bm, (c.x, c.y, base_z + h / 2), (sx, sy, h), rng.randrange(nfront))
        top = base_z + h
        if modern:                                   # flat roof, parapet, a plant room
            for k in (-1, 1):
                p_ = c + nrm * k * (depth / 2 - 0.15)
                _add_box(bm, (p_.x, p_.y, top + 0.5), (abs(ax.x) * w + abs(nrm.x) * 0.3, abs(ax.y) * w + abs(nrm.y) * 0.3, 1.0), n_stone)
            _add_box(bm, (c.x, c.y, top + 1.3), (sx * 0.3, sy * 0.4, 2.6), n_stone)
        else:
            gable = rng.random() < 0.45                # ridge runs back from the street: a gable faces it
            rh = rng.uniform(3.0, 5.5) if gable else rng.uniform(2.4, 4.6)
            along_x = (abs(ax.x) > 0.5) != gable
            _add_roof(bm, (c.x, c.y, top), sx, sy, rh, along_x, n_tile if rng.random() < 0.35 else n_slate)
            if gable and rng.random() < 0.55:          # Flemish stepped gable on the street front
                steps = 4; fp = c + nrm * (depth / 2 + 0.05)
                for k in range(steps):
                    ww = w * (1 - (k + 0.5) / steps); zz = top + rh * k / steps
                    _add_box(bm, (fp.x, fp.y, zz + rh / steps / 2 + 0.25), (abs(ax.x) * ww + abs(nrm.x) * 0.35, abs(ax.y) * ww + abs(nrm.y) * 0.35, rh / steps + 0.5), rng.randrange(nfront))
            if rng.random() < 0.7:                     # chimney
                cp = c + ax * rng.uniform(-w / 3, w / 3) - nrm * rng.uniform(-1.5, 1.5)
                _add_box(bm, (cp.x, cp.y, top + rh * 0.6 + 0.6), (0.6, 0.6, 1.4), n_stone)
            cp = c + nrm * (depth / 2 + 0.12)
            _add_box(bm, (cp.x, cp.y, top - 0.15), (abs(ax.x) * w + abs(nrm.x) * 0.3, abs(ax.y) * w + abs(nrm.y) * 0.3, 0.3), n_stone)
        s += w


def district(hour="dawn", seed=11, R=4, skip=None):
    """A grid of city blocks (terraces round courtyards) with streets and sodium lamps around the Diamond Center block
    at the origin (exterior() is built by the caller), as ONE mesh with a handful of materials (fast to build and
    render). R: blocks out from the centre; skip: (x0, x1, y0, y1) areas left empty."""
    import bmesh
    rng = random.Random(seed)
    import detail as DT
    night = hour in ("dawn", "dusk", "night")
    bases = [tex("red_brick_03", 3.0, tint=t, name=f"th_brick{k}") for k, t in enumerate(((0.75, 0.55, 0.45), (0.62, 0.42, 0.33), (0.85, 0.7, 0.6)))] \
        + [DT.wall_paint(f"th_render{k}", c, rough=0.85, scuff=0.0, z_dirty=0.5) for k, c in enumerate(((0.62, 0.58, 0.5), (0.48, 0.45, 0.4)))]
    fronts = [facade_mat(f"th_front{k}", b, lit_frac=0.12, night=night) for k, b in enumerate(bases)]
    mats = fronts + [flat("th_slate", (0.06, 0.065, 0.075), 0.55), flat("th_stone", (0.55, 0.52, 0.46), 0.8),
                     flat("th_tile", (0.32, 0.12, 0.07), 0.7)]
    BX, BY, ST = 46.0, 38.0, 14.0
    bm = bmesh.new()
    skip = skip or []
    lamps = []
    for i in range(-R, R + 1):
        for j in range(-R, R + 1):
            cx = i * (BX + ST); cy = j * (BY + ST) + 20.0
            if any(a <= cx <= b and c <= cy <= d for a, b, c, d in skip):
                continue
            x0, x1, y0, y1 = cx - BX / 2, cx + BX / 2, cy - BY / 2, cy + BY / 2
            n = len(fronts)
            townhouse_row(bm, x0, y0, BX, (0, -1), rng, n)
            townhouse_row(bm, x1, y1, BX, (0, 1), rng, n)
            townhouse_row(bm, x1, y0 + 10, BY - 20, (1, 0), rng, n)
            townhouse_row(bm, x0, y1 - 10, BY - 20, (-1, 0), rng, n)
            for k in range(3):                       # lamps along both sides of the streets round the block
                lamps.append((x0 + 8 + k * 15, y0 - 3.0)); lamps.append((x0 + 8 + k * 15, y1 + 3.0))
            for k in range(2):
                lamps.append((x0 - 3.0, y0 + 9 + k * 18)); lamps.append((x1 + 3.0, y0 + 9 + k * 18))
    o = _bm_obj_link("district", bm, mats)
    asphalt = tex("asphalt_02", 6.0, tint=(0.4, 0.38, 0.37), name="city_asphalt")
    box("city_ground", (0, 0, -0.13), (2 * R * (BX + ST) + 300, 2 * R * (BY + ST) + 300, 0.1), asphalt)
    if night:
        lm = bmesh.new()
        for lx, ly in lamps:
            _add_box(lm, (lx, ly, 3.5), (0.16, 0.16, 7.0), 0)
            _add_box(lm, (lx, ly - 0.6, 7.0), (0.35, 1.3, 0.14), 1)
        _bm_obj_link("city_lamps", lm, [steel_paint("city_lamp", (0.05, 0.06, 0.06), 0.45), emit("city_sodium", (1.0, 0.6, 0.25), 30)])
        for lx, ly in lamps:
            if math.hypot(lx, ly) < 140:              # real light near the centre; further out the heads glow only
                light_point("city_lamp_light", (lx, ly - 0.8, 6.8), 650, (1.0, 0.6, 0.26), radius=0.25)
    return dict(BX=BX, BY=BY, ST=ST, obj=o, lamps=lamps)


def centraal(loc=(-150.0, 150.0, 0.0)):
    """Antwerp-Centraal beside the diamond district: the domed stone station hall and the iron-and-glass train shed
    (the district's landmark seen from the air)."""
    import bmesh
    stone = flat("cs_stone", (0.62, 0.58, 0.5), 0.8); slate = flat("cs_dome", (0.12, 0.14, 0.15), 0.4, metal=0.3)
    glass = bpy.data.materials.new("cs_glass"); glass.use_nodes = True; gp = glass.node_tree.nodes["Principled BSDF"]
    gp.inputs['Base Color'].default_value = (0.25, 0.3, 0.32, 1); gp.inputs['Roughness'].default_value = 0.15; gp.inputs['Metallic'].default_value = 0.6
    x, y, z = loc
    box("cs_hall", (x, y, z + 14), (60, 40, 28), stone)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=17, location=(x, y, z + 28))
    d = bpy.context.active_object; d.name = "cs_dome"; d.scale = (1, 1, 1.3); d.data.materials.append(slate)
    for k in (-1, 1):
        box("cs_tower", (x + k * 26, y - 16, z + 22), (8, 8, 44), stone)
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=5, depth=10, location=(x + k * 26, y - 16, z + 49))
        bpy.context.active_object.data.materials.append(slate)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=33, depth=180, location=(x, y + 110, z + 10), rotation=(math.radians(90), 0, 0))
    sh = bpy.context.active_object; sh.name = "cs_shed"; sh.scale = (1.0, 0.75, 1.0); sh.data.materials.append(glass)
    box("cs_tracks_bed", (x, y + 110, z + 0.05), (64, 180, 0.2), flat("ballast", (0.18, 0.17, 0.16), 0.9))
    glow = emit("cs_warm", (1.0, 0.75, 0.45), 2.0)
    box("cs_glow", (x, y - 20.1, z + 12), (40, 0.2, 10), glow)


def car_lights(lamps, n=50, seed=4, frames=240, speed=10.0):
    """Moving traffic at dawn from the air: pairs of headlights / tail-lights sliding along the streets (keyed, so the
    motion blur streaks them). Positions follow the lamp lines (the streets)."""
    rng = random.Random(seed)
    head = emit("car_head", (1.0, 0.93, 0.8), 40); tail = emit("car_tail", (1.0, 0.08, 0.04), 30)
    for k in range(n):
        lx, ly = rng.choice(lamps)
        along_x = rng.random() < 0.5; d = rng.choice((-1, 1))
        y_lane = ly + (1.5 if d > 0 else -1.5) * (1 if along_x else 0)
        x_lane = lx + (0 if along_x else (2.5 if d > 0 else -2.5))
        o = bpy.data.objects.new("traffic", None); bpy.context.scene.collection.objects.link(o)
        for sgn, m in ((1, head), (-1, tail)):
            b = box("traffic_light", (sgn * 2.1 * (1 if along_x else 0), sgn * 2.1 * (0 if along_x else 1), 0.7),
                    (0.3 if along_x else 1.4, 1.4 if along_x else 0.3, 0.12), m)
            b.parent = o
        o.rotation_euler = (0, 0, 0 if d > 0 else math.pi)
        p0 = Vector((x_lane, y_lane, 0)); v = Vector((d, 0, 0)) if along_x else Vector((0, d, 0))
        o.location = p0; o.keyframe_insert("location", frame=1)
        o.location = p0 + v * speed * frames / 24.0; o.keyframe_insert("location", frame=frames)
        if o.animation_data and o.animation_data.action:
            import acts
            for fc in acts._fcurves(o):
                for kp in fc.keyframe_points:
                    kp.interpolation = 'LINEAR'



def _bm_obj_link(name, bm, mats):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in mats:
        me.materials.append(m)
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    return o


# ----------------------------------------------------------------------------- street dressing (the DC street)
def _car(uid_or_part, loc, rz, length=4.3, color=None, pack_part=None):
    """Place a car on the street, scaled to a real length. pack_part: name prefix of one car in the pack."""
    import sf
    from mathutils import Vector as _V
    before = set(bpy.data.objects)
    root, ms = sf.model(uid_or_part, loc=(0, 0, 0), rot_z=0.0)
    new = [o for o in bpy.data.objects if o not in before]
    if pack_part:          # keep only one car of the pack (body + its wheels: nearest wheels to the body)
        body = [o for o in new if o.type == 'MESH' and o.name.startswith(pack_part)]
        if not body:
            raise RuntimeError("car part " + pack_part)
        bc = sum((body[0].matrix_world @ _V(c) for c in body[0].bound_box), _V()) / 8
        keep = set(body)
        for o in new:
            if o.type == 'MESH' and o not in keep:
                oc = sum((o.matrix_world @ _V(c) for c in o.bound_box), _V()) / 8
                if (oc - bc).xy.length < 2.4:
                    keep.add(o)
        for o in new:
            if o.type == 'MESH' and o not in keep:
                bpy.data.objects.remove(o)
        ms = [o for o in keep]
    bpy.context.view_layer.update()
    import ph
    lo, hi = ph.bounds(ms)
    ln = max(hi.x - lo.x, hi.y - lo.y); s = length / ln
    piv = bpy.data.objects.new("car", None); bpy.context.scene.collection.objects.link(piv)
    piv.location = ((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)
    for o in ms:
        mw = o.matrix_world.copy(); o.parent = piv; o.matrix_world = mw
    if root is not None and root.name in bpy.data.objects:
        for o in ms:
            pass
    piv.scale = (s, s, s)
    # long axis along x
    if (hi.y - lo.y) > (hi.x - lo.x):
        rz += math.pi / 2
    piv.rotation_euler = (0, 0, rz)
    bpy.context.view_layer.update()
    d = _V(loc) - piv.location; piv.location += _V((d.x, d.y, loc[2] if len(loc) > 2 else 0.0)) - _V((0, 0, piv.location.z))
    return piv


def dress_street(A, hour="night", wet=True, cars=True, seed=5, haze=0.006):
    """Turn exterior()'s street into a lived-in Antwerp street: wet asphalt with puddles, tram rails and overhead
    wires, parked cars both sides, lit windows opposite, bins and a bike rack, sodium pools of light, a little haze."""
    rng = random.Random(seed)
    night = hour in ("night", "dawn", "dusk")
    if wet:
        st = bpy.data.objects.get("street")
        if st:
            st.data.materials.clear(); st.data.materials.append(wet_asphalt())
        for n in ("pavement", "pavement2"):
            o = bpy.data.objects.get(n)
            if o:
                m = o.active_material
                if m and m.node_tree:
                    p = m.node_tree.nodes.get("Principled BSDF")
                    if p:
                        p.inputs['Roughness'].default_value = 0.25
    rail = flat("tram_rail", (0.35, 0.34, 0.33), 0.15, metal=1.0)
    for y in (-8.2, -6.8, -12.0, -10.6):
        box("tram_rail", (0, y, -0.065), (140, 0.07, 0.012), rail)
    wire = flat("tram_wire", (0.03, 0.03, 0.03), 0.4, metal=0.6)
    for y in (-7.5, -11.3):
        S.cyl("tram_wire", (-70, y, 6.1), (70, y, 6.1), 0.008, mat=wire, verts=6)
    for x in range(-60, 61, 20):
        S.cyl("tram_span", (x, -4.8, 6.3), (x, -15.2, 6.3), 0.006, mat=wire, verts=6)
    # lamps: the existing posts get sodium heads lit, plus pools on the far pavement
    if night:
        for ix in (-20, 0, 20):
            if not any(o.name.startswith("lamp_glass") for o in bpy.data.objects):
                box("lamp_glass", (ix, -5.8, 6.41), (0.3, 0.6, 0.02), emit("sodium", (1.0, 0.55, 0.2), 25))
                light_spot("street_lamp", (ix, -5.8, 6.35), (ix, -6.0, 0), 900, angle=110, color=(1.0, 0.55, 0.22), radius=0.2)
        lampm = steel_paint("lamppost2", (0.05, 0.06, 0.06), 0.45)
        for ix in (-30, -10, 10, 30):
            S.cyl("lamppost", (ix, -15.0, 0), (ix, -15.0, 6.5), 0.08, mat=lampm, verts=16)
            box("lamphead", (ix, -14.2, 6.5), (0.4, 1.6, 0.15), lampm)
            box("lamp_glass", (ix, -14.0, 6.41), (0.3, 0.6, 0.02), emit("sodium", (1.0, 0.55, 0.2), 25))
            light_spot("street_lamp", (ix, -14.0, 6.35), (ix, -13.5, 0), 900, angle=110, color=(1.0, 0.55, 0.22), radius=0.2)
    # lit windows in the houses opposite
    litm = _window_mat("opp_win_lit", strength=5.0 if night else 0.0)
    for o in list(bpy.data.objects):
        if o.name.startswith(("opp_win", "nb_win")) and night and rng.random() < 0.35:
            o.data.materials.clear(); o.data.materials.append(litm)
    # parked cars: kerbside along both pavements
    if cars:
        specs = [(AUDI, None, 4.5), (GOLF, None, 4.0)]      # the pack's cars sit diagonally in their file: axis-clean models only
        spots = [(x, -14.0) for x in (-26, -19, -12, 9, 16.5, 24)] + [(x, -6.15) for x in (-24, -17, 12.0, 19.0, 31)]   # >= 6.5 m apart
        for k, (x, y) in enumerate(spots):
            uid, part, ln = specs[k % len(specs)]
            try:
                before = set(bpy.data.materials)
                c = _car(uid, (x + rng.uniform(-0.25, 0.25), y, -0.07), math.pi if (k + (y > -10)) % 2 else 0.0, length=ln, pack_part=part)
                paint = [(0.08, 0.1, 0.16), (0.35, 0.03, 0.03), (0.5, 0.5, 0.52), (0.04, 0.04, 0.045), (0.12, 0.22, 0.14), (0.6, 0.58, 0.52)][k % 6]
                for o in c.children_recursive:              # vary the paint so the street isn't one model repeated
                    for sl in getattr(o, "material_slots", []):
                        m = sl.material
                        if m and m.node_tree and m not in before:
                            pb = m.node_tree.nodes.get("Principled BSDF")
                            if pb and pb.inputs['Metallic'].default_value > 0.3 or (m.name.lower().find("body") >= 0 or m.name.lower().find("paint") >= 0):
                                if pb and not pb.inputs['Base Color'].links:
                                    pb.inputs['Base Color'].default_value = (*paint, 1)
            except Exception as e:
                print("car", e)
    # street furniture: bins, a bike rack with bikes as simple frames, a tram stop sign
    binm = flat("bin_green", (0.05, 0.12, 0.07), 0.5)
    for x in (-16.0, 5.0, 22.0):
        S.cyl("street_bin", (x, -4.2, 0), (x, -4.2, 0.85), 0.25, mat=binm, verts=20)
    rackm = flat("rack_steel", (0.4, 0.4, 0.42), 0.3, metal=0.9)
    for k in range(6):
        x = -3.0 + k * 0.7
        bpy.ops.mesh.primitive_torus_add(major_radius=0.35, minor_radius=0.02, location=(x, -16.4, 0.35), rotation=(math.radians(90), 0, math.radians(90)))
        bpy.context.active_object.data.materials.append(rackm)
    S.cyl("tram_sign", (12, -16.0, 0), (12, -16.0, 2.6), 0.04, mat=steel_paint("signpost", (0.3, 0.3, 0.3), 0.4), verts=10)
    box("tram_sign_plate", (12, -16.0, 2.4), (0.5, 0.04, 0.35), flat("sign_white", (0.85, 0.85, 0.82), 0.4))
    if haze:
        haze_box("street_haze", (0, -9, 4.0), (140, 30, 8.5), density=haze, aniso=0.6, color=(1.0, 0.92, 0.85))
