"""Part 2 sets: what the bones tell under the microscope, the radiocarbon lab, the peat moor and the wrapped dead.

  microscope_field(kind)   the view down a microscope at a stained thin section of bone (transmitted light):
                           osteons (concentric lamellae round a Haversian canal), canaliculi; kind="human" = Cladh
                           Hallan (clean, a thin rim of bacterial attack), "animal" = sheep bone from the same sand
                           (riddled with dark bacterial tunnelling). Built in a dark void, round field stop, camera above.
  ams_hall()               an accelerator mass spectrometry hall: a long stainless beamline, magnets, cable trays,
                           pools of cold practical light in the dark
  peat_moor(...)           the peat moor east of the machair: hummocks, black pools, cut peat banks, heather, cotton grass
  bundle(...) / hurdle(...) a body wrapped in a hide and bound with rope, on a wattle hurdle (no body is ever seen)
"""
import math, random
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
import ph


def _mat(name, col, rough=0.6, metal=0.0, emit=None, strength=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    if emit:
        p.inputs['Emission Color'].default_value = (*emit, 1); p.inputs['Emission Strength'].default_value = strength
    return m


# ----------------------------------------------------------------------------- the microscope field
def microscope_field(kind="human", size=1.0, attack=None):
    """A thin section seen in transmitted light: emission shader (light passing through the slide), built at the
    origin on z = 0, radius `size`. Returns the section object; a field-stop ring (black) sits just above it."""
    attack = attack if attack is not None else (0.12 if kind == "human" else 0.55)
    bpy.ops.mesh.primitive_circle_add(vertices=128, radius=size, fill_type='NGON', location=(0, 0, 0)); o = bpy.context.active_object
    o.name = "section_" + kind
    m = bpy.data.materials.new("histo_" + kind); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    N.remove(N["Principled BSDF"])
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (5.0, 5.0, 5.0); L.new(tc.outputs['Object'], mp.inputs['Vector'])
    # warp the osteon lattice so it is organic
    wn = N.new("ShaderNodeTexNoise"); wn.inputs['Scale'].default_value = 1.5; wn.inputs['Detail'].default_value = 3; L.new(mp.outputs[0], wn.inputs['Vector'])
    wv = N.new("ShaderNodeVectorMath"); wv.operation = 'MULTIPLY_ADD'; wv.inputs[1].default_value = (0.35, 0.35, 0.0)
    L.new(wn.outputs['Color'], wv.inputs[0]); L.new(mp.outputs[0], wv.inputs[2])
    vor = N.new("ShaderNodeTexVoronoi"); vor.inputs['Scale'].default_value = 1.0; vor.inputs['Randomness'].default_value = 0.85
    L.new(wv.outputs[0], vor.inputs['Vector'])
    d = vor.outputs['Distance']
    # lamellae: concentric rings round each canal
    ring = N.new("ShaderNodeMath"); ring.operation = 'MULTIPLY'; ring.inputs[1].default_value = 95.0; L.new(d, ring.inputs[0])
    sn = N.new("ShaderNodeMath"); sn.operation = 'SINE'; L.new(ring.outputs[0], sn.inputs[0])
    ringc = N.new("ShaderNodeMapRange"); ringc.inputs['From Min'].default_value = -1; ringc.inputs['From Max'].default_value = 1
    ringc.inputs['To Min'].default_value = 0.74; ringc.inputs['To Max'].default_value = 1.0; L.new(sn.outputs[0], ringc.inputs['Value'])
    # Haversian canal (dark hole) and the cement line at the osteon edge
    canal = N.new("ShaderNodeMapRange"); canal.inputs['From Min'].default_value = 0.09; canal.inputs['From Max'].default_value = 0.14
    canal.inputs['To Min'].default_value = 0.03; canal.inputs['To Max'].default_value = 1.0; L.new(d, canal.inputs['Value'])
    vor2 = N.new("ShaderNodeTexVoronoi"); vor2.feature = 'DISTANCE_TO_EDGE'; vor2.inputs['Scale'].default_value = 1.0; vor2.inputs['Randomness'].default_value = 0.85
    L.new(wv.outputs[0], vor2.inputs['Vector'])
    cem = N.new("ShaderNodeMapRange"); cem.inputs['From Min'].default_value = 0.0; cem.inputs['From Max'].default_value = 0.025
    cem.inputs['To Min'].default_value = 0.3; cem.inputs['To Max'].default_value = 1.0; L.new(vor2.outputs['Distance'], cem.inputs['Value'])
    # canaliculi / lacunae: fine dark specks
    lac = N.new("ShaderNodeTexVoronoi"); lac.inputs['Scale'].default_value = 16; L.new(wv.outputs[0], lac.inputs['Vector'])
    lacm = N.new("ShaderNodeMapRange"); lacm.inputs['From Min'].default_value = 0.08; lacm.inputs['From Max'].default_value = 0.16
    lacm.inputs['To Min'].default_value = 0.25; lacm.inputs['To Max'].default_value = 1.0; L.new(lac.outputs['Distance'], lacm.inputs['Value'])
    def mul(a, b):
        n = N.new("ShaderNodeMath"); n.operation = 'MULTIPLY'; L.new(a, n.inputs[0]); L.new(b, n.inputs[1]); return n.outputs[0]
    trans = mul(mul(mul(ringc.outputs[0], canal.outputs[0]), cem.outputs[0]), lacm.outputs[0])
    # bacterial tunnelling (Wedl / non-Wedl foci): dark, spongy, brown patches; for the human bone only near the edge
    bt = N.new("ShaderNodeTexNoise"); bt.inputs['Scale'].default_value = 14; bt.inputs['Detail'].default_value = 8; bt.inputs['Roughness'].default_value = 0.75
    L.new(mp.outputs[0], bt.inputs['Vector'])
    bz = N.new("ShaderNodeTexNoise"); bz.inputs['Scale'].default_value = 3.0; bz.inputs['Detail'].default_value = 4; L.new(mp.outputs[0], bz.inputs['Vector'])
    zone = N.new("ShaderNodeMapRange"); zone.inputs['From Min'].default_value = 1.0 - attack; zone.inputs['From Max'].default_value = 1.0 - attack + 0.05
    L.new(bz.outputs['Fac'], zone.inputs['Value'])
    if kind == "human":                  # attack only in a thin band at one edge of the section
        sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Object'], sep.inputs[0])
        edge = N.new("ShaderNodeMapRange"); edge.inputs['From Min'].default_value = size * 0.62; edge.inputs['From Max'].default_value = size * 0.82
        L.new(sep.outputs['X'], edge.inputs['Value'])
        zone_o = mul(zone.outputs[0], edge.outputs[0])
    else:
        zone_o = zone.outputs[0]
    spong = N.new("ShaderNodeMapRange"); spong.inputs['From Min'].default_value = 0.38; spong.inputs['From Max'].default_value = 0.5
    L.new(bt.outputs['Fac'], spong.inputs['Value'])
    dmg = mul(zone_o, spong.outputs[0])
    col = N.new("ShaderNodeMix"); col.data_type = 'RGBA'; L.new(dmg, col.inputs['Factor'])
    col.inputs[6].default_value = (0.95, 0.66, 0.34, 1); col.inputs[7].default_value = (0.08, 0.05, 0.03, 1)    # stained bone / brown tunnels
    tcol = N.new("ShaderNodeMix"); tcol.data_type = 'RGBA'; tcol.blend_type = 'MULTIPLY'; tcol.inputs['Factor'].default_value = 1.0
    L.new(col.outputs[2], tcol.inputs[6]); cc = N.new("ShaderNodeCombineXYZ")
    for k in range(3):
        L.new(trans, cc.inputs[k])
    L.new(cc.outputs[0], tcol.inputs[7])
    em = N.new("ShaderNodeEmission"); em.inputs['Strength'].default_value = 0.85; L.new(tcol.outputs[2], em.inputs['Color'])
    L.new(em.outputs[0], N["Material Output"].inputs['Surface'])
    o.data.materials.append(m)
    # field stop: black annulus over the edge, and a dark world
    bpy.ops.mesh.primitive_circle_add(vertices=128, radius=size * 3, fill_type='NGON', location=(0, 0, 0.002)); fs = bpy.context.active_object
    fs.name = "fieldstop"; bm = bmesh.new(); bm.from_mesh(fs.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces], context='FACES_ONLY'); bm.to_mesh(fs.data); bm.free()
    bm = bmesh.new()
    segs = 128; inner = []; outer = []
    for k in range(segs):
        a = 2 * math.pi * k / segs
        inner.append(bm.verts.new((size * 0.92 * math.cos(a), size * 0.92 * math.sin(a), 0.002)))
        outer.append(bm.verts.new((size * 3 * math.cos(a), size * 3 * math.sin(a), 0.002)))
    for k in range(segs):
        bm.faces.new((inner[k], inner[(k + 1) % segs], outer[(k + 1) % segs], outer[k]))
    bm.to_mesh(fs.data); bm.free()
    fs.data.materials.append(_mat("fieldstop", (0, 0, 0), 1.0))
    w = bpy.data.worlds.new("void"); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs['Color'].default_value = (0, 0, 0, 1)
    return o


# ----------------------------------------------------------------------------- AMS hall
def _brushed(name, col=(0.72, 0.72, 0.74), rough=0.28):
    """Brushed stainless: anisotropic-looking streaks via stretched noise in roughness."""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Metallic'].default_value = 1.0
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (2.0, 2.0, 220.0)
    L.new(tc.outputs['Object'], mp.inputs['Vector'])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 6; nz.inputs['Detail'].default_value = 6; L.new(mp.outputs[0], nz.inputs['Vector'])
    r = N.new("ShaderNodeMapRange"); r.inputs['To Min'].default_value = rough * 0.6; r.inputs['To Max'].default_value = rough * 1.5
    L.new(nz.outputs['Fac'], r.inputs['Value']); L.new(r.outputs[0], p.inputs['Roughness'])
    p.inputs['Anisotropic'].default_value = 0.6
    return m


def _paint(name, col, rough=0.45):
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 9; nz.inputs['Detail'].default_value = 8; L.new(tc.outputs['Object'], nz.inputs['Vector'])
    c = N.new("ShaderNodeMix"); c.data_type = 'RGBA'; c.inputs['Factor'].default_value = 0.12; L.new(nz.outputs['Fac'], c.inputs['Factor'])
    c.inputs[6].default_value = (*col, 1); c.inputs[7].default_value = (col[0] * 0.6, col[1] * 0.6, col[2] * 0.6, 1)
    L.new(c.outputs[2], p.inputs['Base Color'])
    r = N.new("ShaderNodeMapRange"); r.inputs['To Min'].default_value = rough * 0.8; r.inputs['To Max'].default_value = rough * 1.25
    L.new(nz.outputs['Fac'], r.inputs['Value']); L.new(r.outputs[0], p.inputs['Roughness'])
    p.inputs['Coat Weight'].default_value = 0.25
    return m


def _cyl(r, depth, loc, rot=(0, 0, 0), mat=None, name="part", verts=48, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc); o = bpy.context.active_object
    o.rotation_euler = rot; o.name = name
    if mat:
        o.data.materials.append(mat)
    if bevel:
        b = o.modifiers.new("b", "BEVEL"); b.width = bevel; b.segments = 2
    for p_ in o.data.polygons:
        p_.use_smooth = True
    o.data.shade_smooth() if hasattr(o.data, "shade_smooth") else None
    return o


def _box2(name, c, s, mat, bevel=0.01):
    bpy.ops.mesh.primitive_cube_add(size=1, location=c); o = bpy.context.active_object; o.scale = s; o.name = name
    o.data.materials.append(mat)
    if bevel:
        b = o.modifiers.new("b", "BEVEL"); b.width = bevel; b.segments = 2
    return o


def ams_hall(length=16.0, seed=3):
    """Accelerator mass spectrometry hall (tandem-accelerator type): the long pressure-vessel tank of the accelerator,
    a stainless beamline on stands running out of it past a C-yoke analysing magnet and quadrupoles, flanges, bellows,
    vacuum pumps and gauges, cable trays with bundled cables, racks of electronics with small indicator lights; a
    concrete-walled hall lit by cold overhead fittings in haze. Beam axis along x at z = 1.3 m; the tank sits at x < 0."""
    rng = random.Random(seed)
    Z = 1.3
    ss = _brushed("ss"); ssd = _brushed("ssdark", (0.4, 0.4, 0.42), 0.4)
    tankp = _paint("tankpaint", (0.22, 0.3, 0.3), 0.4); red = _paint("magnetred", (0.28, 0.05, 0.035), 0.4)
    blue = _paint("quadblue", (0.05, 0.09, 0.17), 0.38); copper = _paint("coil", (0.55, 0.25, 0.1), 0.3)
    copper.node_tree.nodes["Principled BSDF"].inputs['Metallic'].default_value = 0.8
    rackp = _paint("rack", (0.12, 0.12, 0.13), 0.55); yellow = _paint("yellowstand", (0.38, 0.3, 0.06), 0.5)
    floor = ph.texture("concrete_floor_worn_001", scale=0.4, name="hallfloor", tint=(0.55, 0.56, 0.6))
    wall = ph.texture("painted_plaster_wall", scale=0.25, name="hallwall", tint=(0.12, 0.13, 0.15))
    W = 14.0
    _box2("floor", (length / 2 - 6, 0, -0.05), (length + 30, W, 0.1), floor, 0)
    for y in (-W / 2, W / 2):
        _box2("wall", (length / 2 - 6, y, 4), (length + 30, 0.3, 8), wall, 0)
    _box2("endwall", (length + 6, 0, 4), (0.3, W, 8), wall, 0)
    _box2("ceiling", (length / 2 - 6, 0, 8), (length + 30, W, 0.3), wall, 0)
    # the accelerator tank: a long horizontal pressure vessel with domed ends and a bolted girth flange
    tl = 9.0; tr = 1.35; tx0 = -tl - 1.5
    _cyl(tr, tl, (tx0 + tl / 2, 0, Z + 0.2), rot=(0, math.pi / 2, 0), mat=tankp, name="tank", verts=96)
    for xe in (tx0, tx0 + tl):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=tr, location=(xe, 0, Z + 0.2)); d = bpy.context.active_object
        d.scale = (0.35, 1, 1); d.data.materials.append(tankp); d.name = "tankdome"
        for p_ in d.data.polygons:
            p_.use_smooth = True
    for xg in (tx0 + tl * 0.5,):
        _cyl(tr + 0.07, 0.16, (xg, 0, Z + 0.2), rot=(0, math.pi / 2, 0), mat=tankp, name="girth", verts=96)
        for k in range(48):
            a = 2 * math.pi * k / 48
            _cyl(0.025, 0.2, (xg, (tr + 0.1) * math.cos(a), Z + 0.2 + (tr + 0.1) * math.sin(a)), rot=(0, math.pi / 2, 0), mat=ssd, name="bolt", verts=8)
    for xs in (tx0 + 1.2, tx0 + tl - 1.2):                     # saddles
        _box2("saddle", (xs, 0, 0.3), (0.5, 2.2, 0.6), yellow, 0.02)
    # beamline from the tank exit to the far end, flanges every 0.9 m, bellows, gate valves
    x0 = tx0 + tl + tr * 0.35
    _cyl(0.05, length - x0 + 0.5, ((x0 + length) / 2, 0, Z), rot=(0, math.pi / 2, 0), mat=ss, name="beamline", verts=32)
    x = x0 + 0.4
    while x < length:
        _cyl(0.1, 0.035, (x, 0, Z), rot=(0, math.pi / 2, 0), mat=ss, name="flange", verts=32)
        for k in range(8):
            a = 2 * math.pi * k / 8 + 0.2
            _cyl(0.008, 0.06, (x, 0.08 * math.cos(a), Z + 0.08 * math.sin(a)), rot=(0, math.pi / 2, 0), mat=ssd, name="bolt", verts=6)
        if rng.random() < 0.3:                                   # bellows
            for j in range(7):
                bpy.ops.mesh.primitive_torus_add(major_radius=0.065, minor_radius=0.012, location=(x + 0.08 + j * 0.03, 0, Z)); b = bpy.context.active_object
                b.rotation_euler.y = math.pi / 2; b.data.materials.append(ss); b.name = "bellows"
        x += 0.9
    # gate valve + turbo pump + gauge clusters
    for xv in (x0 + 1.6, x0 + 6.4, x0 + 11.0):
        _box2("valve", (xv, 0, Z + 0.12), (0.16, 0.24, 0.42), ss, 0.01)
        _cyl(0.05, 0.4, (xv, 0, Z + 0.5), mat=ss, name="actuator", verts=24)
        _cyl(0.11, 0.3, (xv + 0.35, 0, Z - 0.3), mat=ssd, name="turbopump")
        _cyl(0.05, 0.25, (xv + 0.35, 0, Z - 0.1), mat=ss, name="pumpneck", verts=24)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(xv + 0.35, 0.16, Z - 0.3)); g = bpy.context.active_object
        g.scale = (0.08, 0.02, 0.05); g.data.materials.append(rackp); g.name = "gaugebox"
        bpy.ops.mesh.primitive_cube_add(size=1, location=(xv + 0.35, 0.171, Z - 0.29)); e = bpy.context.active_object
        e.scale = (0.035, 0.002, 0.012); e.name = "gaugeled"
        e.data.materials.append(_mat("gaugeled", (0.0, 0.1, 0.0), 0.3, emit=(0.2, 1.0, 0.35), strength=25))
    # the analysing magnet: C-yoke, red paint, copper coils
    mx = x0 + 4.0
    _box2("yokeback", (mx, -0.55, Z), (1.4, 0.35, 1.3), red, 0.03)
    for zz in (Z + 0.42, Z - 0.42):
        _box2("pole", (mx, -0.12, zz), (1.4, 0.55, 0.45), red, 0.03)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.55, minor_radius=0.09, location=(mx, -0.12, zz - 0.0)); c = bpy.context.active_object
        c.scale = (1.25, 0.6, 0.9); c.data.materials.append(copper); c.name = "coil"
    _box2("magnetbase", (mx, -0.2, 0.3), (1.6, 1.2, 0.6), yellow, 0.02)
    # quadrupole doublets (blue)
    for qx in (x0 + 2.2, x0 + 7.6, x0 + 9.6):
        _cyl(0.2, 0.34, (qx, 0, Z), rot=(0, math.pi / 2, 0), mat=blue, name="quad", verts=64, bevel=0.02)
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            bpy.ops.mesh.primitive_torus_add(major_radius=0.06, minor_radius=0.022, location=(qx - 0.18, 0.12 * math.cos(a), Z + 0.12 * math.sin(a)))
            c = bpy.context.active_object; c.rotation_euler.y = math.pi / 2; c.data.materials.append(copper); c.name = "quadcoil"
    # stands under the beamline
    xs = x0 + 0.8
    while xs < length:
        for sy in (-1, 1):
            _box2("standleg", (xs, sy * 0.22, (Z - 0.12) / 2), (0.05, 0.05, Z - 0.12), yellow, 0.005)
        _box2("standtop", (xs, 0, Z - 0.12), (0.1, 0.55, 0.04), yellow, 0.005)
        _box2("standfoot", (xs, 0, 0.02), (0.3, 0.6, 0.04), yellow, 0.005)
        xs += 1.8
    # electronics racks along the +y wall, indicator LEDs; cable trays overhead with cable bundles
    for sgn in (1, -1):
        for k in range(int((length + 10) / 0.62)):
            rx = -9 + k * 0.62
            if sgn < 0 and rng.random() < 0.25:
                continue                                   # gaps on the far wall: doors, a desk, open floor
            _box2("rack", (rx, sgn * (W / 2 - 0.75), 1.0), (0.6, 0.8, 2.0), rackp, 0.01)
            fy = sgn * (W / 2 - 1.152)
            for j in range(rng.randint(3, 9)):
                col = rng.choice([(1.0, 0.25, 0.05), (0.2, 1.0, 0.3), (0.3, 0.6, 1.0), (1.0, 0.75, 0.2)])
                bpy.ops.mesh.primitive_cube_add(size=1, location=(rx + rng.uniform(-0.25, 0.25), fy, rng.uniform(0.4, 1.9)))
                e = bpy.context.active_object; e.scale = (0.008, 0.002, 0.006); e.name = "led"
                mm = bpy.data.materials.get(f"led{col}") or _mat(f"led{col}", (0, 0, 0), 0.3, emit=col, strength=40)
                e.data.materials.append(mm)
            _box2("rackface", (rx, sgn * (W / 2 - 1.151), 1.0), (0.56, 0.002, 1.9), bpy.data.materials.get("rackface") or _paint("rackface", (0.18, 0.18, 0.19), 0.4), 0)
    for ty in (-1.3, 1.6):
        _box2("tray", (length / 2 - 6, ty, 3.0), (length + 24, 0.45, 0.06), ssd, 0.005)
        for c in range(9):
            _cyl(0.02, length + 24, (length / 2 - 6, ty - 0.18 + c * 0.045, 3.06), rot=(0, math.pi / 2, 0),
                 mat=_paint(f"cable{c}", rng.choice([(0.02, 0.02, 0.02), (0.05, 0.05, 0.06), (0.3, 0.02, 0.01), (0.02, 0.05, 0.2)]), 0.5), name="cable", verts=10)
        for xh in np.arange(-10, length + 6, 2.4):
            _cyl(0.012, 4.9, (xh, ty, 5.5), mat=ssd, name="hanger", verts=8)
    # overhead fittings: visible emissive strips + area lights; a pool on the tank; haze is added by the shot
    for xf in np.arange(-12, length + 6, 3.2):
        for yf in (-3.0, 3.0):
            _box2("fitting", (xf, yf, 7.75), (1.5, 0.22, 0.08), rackp, 0)
            bpy.ops.mesh.primitive_plane_add(size=1, location=(xf, yf, 7.705)); e = bpy.context.active_object
            e.scale = (1.4, 0.16, 1); e.rotation_euler.x = math.pi; e.name = "tube"
            e.data.materials.append(bpy.data.materials.get("tubeglow") or _mat("tubeglow", (0, 0, 0), 0.5, emit=(0.78, 0.88, 1.0), strength=12))
            d = bpy.data.lights.new("fit", 'AREA'); d.shape = 'RECTANGLE'; d.size = 1.4; d.size_y = 0.15; d.energy = 55; d.color = (0.78, 0.88, 1.0)
            lo = bpy.data.objects.new("fit", d); bpy.context.scene.collection.objects.link(lo); lo.location = (xf, yf, 7.6)
    w = bpy.data.worlds.new("hall"); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs['Color'].default_value = (0.005, 0.006, 0.008, 1)
    return dict(beam_z=Z, length=length, tank_x=(tx0, tx0 + tl), magnet_x=mx, x0=x0)


# ----------------------------------------------------------------------------- the peat moor
def peat_moor(center=(0.0, 0.0), size=220.0, n=420, seed=4, pools=True):
    """Blanket bog: low hummocks and hollows, black pools in the hollows, a few cut peat banks; dark peat, heather,
    sphagnum (rust-red and green), bleached grass. Flat-ish at z = 0 around `center`."""
    from uist import fbm, _smooth
    rng = random.Random(seed)
    xs = np.linspace(-size / 2, size / 2, n); X, Y = np.meshgrid(xs, xs)
    Z = 1.2 * fbm(X / 40, Y / 40, 4, seed=seed) + 0.35 * fbm(X / 6, Y / 6, 3, seed=seed + 1) + 0.12 * fbm(X / 1.5, Y / 1.5, 2, seed=seed + 2)
    # cut peat bank: a straight step 1.2 m high running across, with the cut face toward -y
    bank = _smooth(-0.15, 0.15, Y - 6.0 - 0.6 * fbm(X / 8, 0, 2, seed=9)) * 1.2
    Z = Z + bank
    V = np.stack([X + center[0], Y + center[1], Z], -1).reshape(-1, 3).astype(np.float32)
    idx = np.arange(n * n).reshape(n, n)
    F = np.stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()], -1).astype(np.int32)
    me = bpy.data.meshes.new("moor"); me.vertices.add(len(V)); me.vertices.foreach_set("co", V.ravel())
    me.loops.add(len(F) * 4); me.loops.foreach_set("vertex_index", F.ravel()); me.polygons.add(len(F))
    me.polygons.foreach_set("loop_start", np.arange(0, len(F) * 4, 4, dtype=np.int32)); me.polygons.foreach_set("use_smooth", np.ones(len(F), bool))
    me.update(calc_edges=True)
    o = bpy.data.objects.new("moor", me); bpy.context.scene.collection.objects.link(o)
    m = bpy.data.materials.new("moorground"); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); geo = N.new("ShaderNodeNewGeometry")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 0.08; nz.inputs['Detail'].default_value = 6; L.new(tc.outputs['Object'], nz.inputs['Vector'])
    nz2 = N.new("ShaderNodeTexNoise"); nz2.inputs['Scale'].default_value = 1.2; nz2.inputs['Detail'].default_value = 8; L.new(tc.outputs['Object'], nz2.inputs['Vector'])
    rp = N.new("ShaderNodeValToRGB"); el = rp.color_ramp.elements
    el[0].position = 0.3; el[0].color = (0.035, 0.03, 0.018, 1)          # wet black peat / heather
    e = el.new(0.45); e.color = (0.09, 0.07, 0.03, 1)                     # heather brown
    e = el.new(0.55); e.color = (0.16, 0.06, 0.03, 1)                     # rust-red sphagnum
    e = el.new(0.65); e.color = (0.18, 0.17, 0.08, 1)                     # bleached moor grass
    el[1].position = 0.8; el[1].color = (0.12, 0.14, 0.05, 1)             # green sphagnum
    mx = N.new("ShaderNodeMath"); mx.operation = 'MULTIPLY_ADD'; mx.inputs[1].default_value = 0.5
    L.new(nz2.outputs['Fac'], mx.inputs[0]); L.new(nz.outputs['Fac'], mx.inputs[2])
    sub = N.new("ShaderNodeMath"); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = 0.25; L.new(mx.outputs[0], sub.inputs[0])
    L.new(sub.outputs[0], rp.inputs['Fac'])
    # peat bank faces: dark brown fibrous peat with paler bands
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Normal'], sep.inputs[0])
    steep = N.new("ShaderNodeMapRange"); steep.inputs['From Min'].default_value = 0.7; steep.inputs['From Max'].default_value = 0.4
    L.new(sep.outputs['Z'], steep.inputs['Value'])
    ps = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Position'], ps.inputs[0])
    band = N.new("ShaderNodeTexWave"); band.bands_direction = 'Z'; band.inputs['Scale'].default_value = 5.0; band.inputs['Distortion'].default_value = 9; band.inputs['Detail'].default_value = 8; band.inputs['Detail Roughness'].default_value = 0.8
    L.new(tc.outputs['Object'], band.inputs['Vector'])
    pc = N.new("ShaderNodeMix"); pc.data_type = 'RGBA'; L.new(band.outputs['Fac'], pc.inputs['Factor'])
    pc.inputs[6].default_value = (0.04, 0.026, 0.014, 1); pc.inputs[7].default_value = (0.075, 0.048, 0.026, 1)
    fin = N.new("ShaderNodeMix"); fin.data_type = 'RGBA'; L.new(steep.outputs[0], fin.inputs['Factor'])
    L.new(rp.outputs['Color'], fin.inputs[6]); L.new(pc.outputs[2], fin.inputs[7])
    # photographic detail: withered moor grass, and wet peat mud in the low ground, modulating the procedural tones
    import os
    PH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "polyhaven")
    def img(path, color=True, scale=0.6):
        mp_ = N.new("ShaderNodeMapping"); mp_.inputs['Scale'].default_value = (scale, scale, scale); L.new(tc.outputs['Object'], mp_.inputs['Vector'])
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True); t.projection = 'BOX'; t.projection_blend = 0.3
        t.image.colorspace_settings.name = 'sRGB' if color else 'Non-Color'; L.new(mp_.outputs[0], t.inputs['Vector']); return t
    try:
        g_d = img(os.path.join(PH, "withered_grass", "withered_grass_diff_2k.jpg"))
        g_n = img(os.path.join(PH, "withered_grass", "withered_grass_nor_gl_2k.jpg"), False)
        m_d = img(os.path.join(PH, "brown_mud_02", "brown_mud_02_diff_2k.jpg"), scale=0.4)
        low = N.new("ShaderNodeMapRange"); low.inputs['From Min'].default_value = float(np.percentile(Z, 22)); low.inputs['From Max'].default_value = float(np.percentile(Z, 9))
        L.new(ps.outputs['Z'], low.inputs['Value'])
        surf = N.new("ShaderNodeMix"); surf.data_type = 'RGBA'; L.new(low.outputs[0], surf.inputs['Factor'])
        L.new(g_d.outputs['Color'], surf.inputs[6]); L.new(m_d.outputs['Color'], surf.inputs[7])
        mul = N.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
        L.new(fin.outputs[2], mul.inputs[6]); L.new(surf.outputs[2], mul.inputs[7])
        br = N.new("ShaderNodeMath"); br.operation = 'MULTIPLY'; br.inputs[1].default_value = 3.2
        gain = N.new("ShaderNodeMix"); gain.data_type = 'RGBA'; gain.blend_type = 'MULTIPLY'; gain.inputs['Factor'].default_value = 1.0
        L.new(mul.outputs[2], gain.inputs[6]); gain.inputs[7].default_value = (3.2, 3.0, 2.8, 1)
        L.new(gain.outputs[2], p.inputs['Base Color'])
        nm = N.new("ShaderNodeNormalMap"); nm.inputs['Strength'].default_value = 0.8; L.new(g_n.outputs['Color'], nm.inputs['Color'])
        wet = N.new("ShaderNodeMapRange"); wet.inputs['To Min'].default_value = 0.9; wet.inputs['To Max'].default_value = 0.62
        L.new(low.outputs[0], wet.inputs['Value']); L.new(wet.outputs[0], p.inputs['Roughness'])
        bm_ = N.new("ShaderNodeBump"); bm_.inputs['Strength'].default_value = 0.3; L.new(nz2.outputs['Fac'], bm_.inputs['Height'])
        L.new(nm.outputs[0], bm_.inputs['Normal']); L.new(bm_.outputs['Normal'], p.inputs['Normal'])
    except Exception as ex:
        print("moor textures:", ex)
        L.new(fin.outputs[2], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.85
    o.data.materials.append(m)
    # the moor runs on to the horizon: a big skirt plane just under the edge, same ground
    zf = float(np.percentile(Z, 30)) - 0.05; hi_ = size / 2 - 0.5; ho = 4000.0
    fb = bmesh.new()
    inn = [fb.verts.new((center[0] + a * hi_, center[1] + b * hi_, zf)) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    outr = [fb.verts.new((center[0] + a * ho, center[1] + b * ho, zf)) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for k in range(4):
        fb.faces.new((inn[k], outr[k], outr[(k + 1) % 4], inn[(k + 1) % 4]))
    fme = bpy.data.meshes.new("moorfar"); fb.to_mesh(fme); fb.free(); fme.materials.append(m)
    far = bpy.data.objects.new("moorfar", fme); bpy.context.scene.collection.objects.link(far)
    out = dict(ground=o, Z=Z, xs=xs)
    if pools:
        water = _mat("bogwater", (0.004, 0.003, 0.002), 0.03)
        lvl = float(np.percentile(Z, 9))
        bpy.ops.mesh.primitive_plane_add(size=size, location=(center[0], center[1], lvl)); w = bpy.context.active_object; w.name = "bogpools"
        w.data.materials.append(water)
        out["water_z"] = lvl
    return out


def moor_height(M, x, y, center=(0.0, 0.0)):
    xs = M["xs"]; Z = M["Z"]
    i = int(np.clip(np.searchsorted(xs, x - center[0]), 1, len(xs) - 1)); j = int(np.clip(np.searchsorted(xs, y - center[1]), 1, len(xs) - 1))
    return float(Z[j, i])


# ----------------------------------------------------------------------------- the wrapped dead
def bundle(loc, rot=0.0, length=0.95, girth=0.44, seed=0):
    """A body drawn up and wrapped in a hide, bound with rope: an irregular soft bundle (nothing of the body shows)."""
    rng = random.Random(seed)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.5, location=loc); o = bpy.context.active_object
    o.name = "bundle"; o.scale = (length, girth, girth * 0.62); o.rotation_euler = (rng.uniform(-0.05, 0.05), 0, rot)
    d = o.modifiers.new("lumps", "DISPLACE"); t = bpy.data.textures.new("bundlelump", "CLOUDS"); t.noise_scale = 0.22; d.texture = t; d.strength = 0.08
    d2 = o.modifiers.new("folds", "DISPLACE"); t2 = bpy.data.textures.new("bundlefold", "WOOD"); t2.wood_type = 'BANDNOISE'; t2.noise_scale = 0.08; t2.turbulence = 8; d2.texture = t2; d2.strength = 0.015
    hide = ph.texture("leather_white", scale=2.0, name="hide", tint=(0.42, 0.3, 0.18)) if False else _mat("hide", (0.13, 0.085, 0.05), 0.8)
    hn = hide.node_tree.nodes; hl = hide.node_tree.links; hp = hn["Principled BSDF"]
    tc = hn.new("ShaderNodeTexCoord"); nz = hn.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 12; nz.inputs['Detail'].default_value = 10
    hl.new(tc.outputs['Object'], nz.inputs['Vector']); bmp = hn.new("ShaderNodeBump"); bmp.inputs['Strength'].default_value = 0.5
    hl.new(nz.outputs['Fac'], bmp.inputs['Height']); hl.new(bmp.outputs['Normal'], hp.inputs['Normal'])
    hp.inputs['Sheen Weight'].default_value = 0.08
    o.data.materials.append(hide)
    rope = _mat("rope2", (0.18, 0.13, 0.08), 0.9)
    for k in range(3):
        u = -0.25 + k * 0.25 + rng.uniform(-0.02, 0.02)
        f = math.sqrt(max(0.05, 1 - (u / 0.5) ** 2))            # the bundle narrows toward its ends
        bpy.ops.mesh.primitive_torus_add(major_radius=girth * 0.5 * f * 0.93, minor_radius=0.012, location=loc); r = bpy.context.active_object
        r.scale = (0.76, 1, 1); r.rotation_euler = (0, math.pi / 2, rot)
        r.location = Vector(loc) + Matrix.Rotation(rot, 3, 'Z') @ Vector((u * length, 0, 0)); r.data.materials.append(rope); r.name = "bundlerope"
    return o


def hurdle(loc, rot=0.0, length=2.0, width=0.9, seed=0):
    """Wattle hurdle (carrying frame): two poles with woven hazel rods."""
    rng = random.Random(seed)
    wood = bpy.data.materials.get("hazel") or ph.texture("bark_brown_02", scale=8.0, name="hazel", tint=(0.8, 0.7, 0.6))
    R = Matrix.Rotation(rot, 4, 'Z'); T = Matrix.Translation(Vector(loc))
    for sy in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=length + 0.5, location=(0, 0, 0)); p = bpy.context.active_object
        p.matrix_world = T @ R @ Matrix.Translation((0, sy * width / 2, 0.03)) @ Matrix.Rotation(math.pi / 2, 4, 'Y'); p.data.materials.append(wood); p.name = "hurdlepole"
    for k in range(int(length / 0.07)):
        x = -length / 2 + k * 0.07
        bpy.ops.mesh.primitive_cylinder_add(radius=0.011, depth=width + 0.08, location=(0, 0, 0)); r = bpy.context.active_object
        r.matrix_world = T @ R @ Matrix.Translation((x, 0, 0.03 + 0.012 * (1 if k % 2 else -1))) @ Matrix.Rotation(math.pi / 2, 4, 'X')
        r.data.materials.append(wood); r.name = "hurdlerod"
