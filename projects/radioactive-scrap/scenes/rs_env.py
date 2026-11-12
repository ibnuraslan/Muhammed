"""Environment for the radioactive-scrap film: winter skies with real cloud texture, a cold key light, the
Istanbul periphery (hills of low-rise concrete apartment blocks fading into haze, minarets, power lines,
chimney smoke), puddles.

  sky(kind)                 "overcast" | "afternoon" | "morning" (clear, long shadows) | "dusk" | "rain"
  periphery(c, rng, ...)    hills + apartment blocks + minarets + smoke around a centre, outside a radius
  puddles(rng, area, n)     dark glossy water patches on mud
  smoke(loc, h)             a slow rising chimney plume (frame-driven, plays in any render)
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import pbr, box, cyl, instance, join, haze
from common import sun

SKIES = {
    #            horizon               zenith               cloud col            cover  sun elev/az  sun col              energy angle  strength exposure
    "overcast":  ((0.62, 0.66, 0.70), (0.42, 0.48, 0.56), (0.70, 0.72, 0.75), 0.75, 16, 210, (0.92, 0.95, 1.0), 1.4, 18, 0.9, 0.35),
    "afternoon": ((0.68, 0.70, 0.72), (0.40, 0.47, 0.58), (0.78, 0.78, 0.78), 0.6, 14, 230, (0.95, 0.94, 0.92), 2.2, 8, 0.9, 0.2),
    "morning":   ((0.78, 0.76, 0.72), (0.30, 0.42, 0.62), (0.92, 0.88, 0.84), 0.3, 9, 120, (1.0, 0.86, 0.68), 4.5, 1.5, 0.9, 0.0),
    "dusk":      ((0.42, 0.42, 0.52), (0.10, 0.14, 0.26), (0.30, 0.30, 0.38), 0.55, 2, 240, (0.70, 0.72, 0.95), 0.3, 10, 0.9, 0.9),
    "rain":      ((0.50, 0.53, 0.57), (0.36, 0.40, 0.45), (0.48, 0.50, 0.53), 0.95, 20, 200, (0.88, 0.92, 1.0), 0.6, 30, 0.9, 0.5),
}


def sky(kind="overcast"):
    bpy.context.scene.cycles.sample_clamp_indirect = 3.0      # no fireflies / speckle in sheets or film
    hor, zen, ccol, cover, el, az, scol, en, ang, strength, expo = SKIES[kind]
    w = bpy.data.worlds.new("Sky"); bpy.context.scene.world = w; w.use_nodes = True
    N = w.node_tree.nodes; L = w.node_tree.links; N.clear()
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Generated'], sep.inputs[0])
    # sky gradient on view elevation
    mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = -0.05; mr.inputs['From Max'].default_value = 0.6
    L.new(sep.outputs['Z'], mr.inputs['Value'])
    grad = N.new("ShaderNodeMix"); grad.data_type = 'RGBA'; L.new(mr.outputs[0], grad.inputs['Factor'])
    grad.inputs[6].default_value = (*hor, 1); grad.inputs[7].default_value = (*zen, 1)
    # cloud plane: direction / (z + 0.12) -> 3D noise, streaked a little along X
    zz = N.new("ShaderNodeMath"); zz.operation = 'ADD'; zz.inputs[1].default_value = 0.12; L.new(sep.outputs['Z'], zz.inputs[0])
    zm = N.new("ShaderNodeMath"); zm.operation = 'MAXIMUM'; zm.inputs[1].default_value = 0.02; L.new(zz.outputs[0], zm.inputs[0])
    dv = N.new("ShaderNodeVectorMath"); dv.operation = 'DIVIDE'; L.new(tc.outputs['Generated'], dv.inputs[0])
    cz = N.new("ShaderNodeCombineXYZ"); L.new(zm.outputs[0], cz.inputs[0]); L.new(zm.outputs[0], cz.inputs[1]); L.new(zm.outputs[0], cz.inputs[2])
    L.new(cz.outputs[0], dv.inputs[1])
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (0.55, 1.1, 1.0); L.new(dv.outputs[0], mp.inputs['Vector'])
    n1 = N.new("ShaderNodeTexNoise"); n1.noise_dimensions = '4D'; n1.inputs['Scale'].default_value = 1.6; n1.inputs['Detail'].default_value = 12
    n1.inputs['Roughness'].default_value = 0.6
    L.new(mp.outputs[0], n1.inputs['Vector'])
    vw = N.new("ShaderNodeValue"); d = vw.outputs[0].driver_add("default_value").driver; d.type = 'SCRIPTED'; d.expression = "frame * 0.0015"
    L.new(vw.outputs[0], n1.inputs['W'])                 # clouds drift slowly (driver: plays anywhere)
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].position = 1.0 - cover - 0.05; cr.color_ramp.elements[1].position = min(0.98, 1.0 - cover + 0.3)
    cr.color_ramp.elements[0].color = (0, 0, 0, 1); cr.color_ramp.elements[1].color = (1, 1, 1, 1)
    L.new(n1.outputs['Fac'], cr.inputs['Fac'])
    shade = N.new("ShaderNodeMix"); shade.data_type = 'RGBA'; L.new(n1.outputs['Fac'], shade.inputs['Factor'])
    shade.inputs[6].default_value = (*[c * 1.1 for c in ccol], 1); shade.inputs[7].default_value = (*[c * 0.7 for c in ccol], 1)
    # fade clouds toward the horizon (haze)
    hz = N.new("ShaderNodeMapRange"); hz.inputs['From Min'].default_value = 0.0; hz.inputs['From Max'].default_value = 0.25
    L.new(sep.outputs['Z'], hz.inputs['Value'])
    cf = N.new("ShaderNodeMath"); cf.operation = 'MULTIPLY'; L.new(cr.outputs['Color'], cf.inputs[0]); L.new(hz.outputs[0], cf.inputs[1])
    mix = N.new("ShaderNodeMix"); mix.data_type = 'RGBA'; L.new(cf.outputs[0], mix.inputs['Factor'])
    L.new(grad.outputs[2], mix.inputs[6]); L.new(shade.outputs[2], mix.inputs[7])
    bg = N.new("ShaderNodeBackground"); bg.inputs['Strength'].default_value = strength
    out = N.new("ShaderNodeOutputWorld")
    L.new(mix.outputs[2], bg.inputs['Color']); L.new(bg.outputs[0], out.inputs['Surface'])
    s = sun(el, az, energy=en, color=scol, angle_deg=ang)
    bpy.context.scene.view_settings.exposure = expo
    return w, s


def facade_material(name, base, rng_seed=0, floor=2.9, bay=3.2):
    """Concrete apartment facade: painted render with a grid of dark windows and balcony bands (object coords)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    geo = N.new("ShaderNodeNewGeometry"); oi = N.new("ShaderNodeObjectInfo")
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (1 / bay, 1 / bay, 1 / floor); L.new(geo.outputs['Position'], mp.inputs['Vector'])
    fr = N.new("ShaderNodeVectorMath"); fr.operation = 'FRACTION'; L.new(mp.outputs[0], fr.inputs[0])
    sp = N.new("ShaderNodeSeparateXYZ"); L.new(fr.outputs[0], sp.inputs[0])
    nsep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Normal'], nsep.inputs[0])
    nx = N.new("ShaderNodeMath"); nx.operation = 'ABSOLUTE'; L.new(nsep.outputs[0], nx.inputs[0])
    hsel = N.new("ShaderNodeMix"); hsel.data_type = 'FLOAT'; L.new(nx.outputs[0], hsel.inputs['Factor'])
    L.new(sp.outputs[0], hsel.inputs[2]); L.new(sp.outputs[1], hsel.inputs[3])         # horizontal coordinate along the wall
    def band(src, lo, hi):
        a = N.new("ShaderNodeMath"); a.operation = 'GREATER_THAN'; a.inputs[1].default_value = lo; L.new(src, a.inputs[0])
        b = N.new("ShaderNodeMath"); b.operation = 'LESS_THAN'; b.inputs[1].default_value = hi; L.new(src, b.inputs[0])
        m_ = N.new("ShaderNodeMath"); m_.operation = 'MULTIPLY'; L.new(a.outputs[0], m_.inputs[0]); L.new(b.outputs[0], m_.inputs[1]); return m_.outputs[0]
    win = N.new("ShaderNodeMath"); win.operation = 'MULTIPLY'
    L.new(band(hsel.outputs[0], 0.22, 0.78), win.inputs[0]); L.new(band(sp.outputs[2], 0.3, 0.8), win.inputs[1])
    nz = N.new("ShaderNodeMath"); nz.operation = 'ABSOLUTE'; L.new(nsep.outputs[2], nz.inputs[0])
    wall = N.new("ShaderNodeMath"); wall.operation = 'LESS_THAN'; wall.inputs[1].default_value = 0.5; L.new(nz.outputs[0], wall.inputs[0])
    w2 = N.new("ShaderNodeMath"); w2.operation = 'MULTIPLY'; L.new(win.outputs[0], w2.inputs[0]); L.new(wall.outputs[0], w2.inputs[1])
    # base colour varies per building; stains
    hs = N.new("ShaderNodeHueSaturation"); hs.inputs['Color'].default_value = (*base, 1)
    hv = N.new("ShaderNodeMath"); hv.operation = 'MULTIPLY_ADD'; hv.inputs[1].default_value = 0.08; hv.inputs[2].default_value = 0.46
    L.new(oi.outputs['Random'], hv.inputs[0]); L.new(hv.outputs[0], hs.inputs['Hue'])
    vv = N.new("ShaderNodeMath"); vv.operation = 'MULTIPLY_ADD'; vv.inputs[1].default_value = 0.5; vv.inputs[2].default_value = 0.75
    L.new(oi.outputs['Random'], vv.inputs[0]); L.new(vv.outputs[0], hs.inputs['Value'])
    tc = N.new("ShaderNodeTexCoord"); nn = N.new("ShaderNodeTexNoise"); nn.inputs['Scale'].default_value = 0.3; nn.inputs['Detail'].default_value = 6
    L.new(tc.outputs['Object'], nn.inputs['Vector'])
    st = N.new("ShaderNodeMix"); st.data_type = 'RGBA'; st.blend_type = 'MULTIPLY'; st.inputs['Factor'].default_value = 0.45
    L.new(hs.outputs['Color'], st.inputs[6]); L.new(nn.outputs['Color'], st.inputs[7])
    col = N.new("ShaderNodeMix"); col.data_type = 'RGBA'; L.new(w2.outputs[0], col.inputs['Factor'])
    L.new(st.outputs[2], col.inputs[6]); col.inputs[7].default_value = (0.03, 0.035, 0.04, 1)
    L.new(col.outputs[2], p.inputs['Base Color'])
    rg = N.new("ShaderNodeMapRange"); L.new(w2.outputs[0], rg.inputs['Value']); rg.inputs['To Min'].default_value = 0.85; rg.inputs['To Max'].default_value = 0.15
    L.new(rg.outputs[0], p.inputs['Roughness'])
    return m


def minaret(loc, h=34, mat=None):
    x, y, z = loc
    parts = [cyl("MinShaft", (x, y, z + h / 2), 1.0, h, mat, verts=16),
             cyl("MinBase", (x, y, z + 3), 1.5, 6, mat, verts=12),
             cyl("MinBalcony", (x, y, z + h * 0.78), 1.45, 0.5, mat, verts=16),
             cyl("MinUpper", (x, y, z + h + 1.5), 0.85, 3.0, mat, verts=16)]
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.95, depth=5.5, location=(x, y, z + h + 5.7))
    c = bpy.context.active_object; c.data.materials.append(mat); parts.append(c)
    return join(parts, "Minaret")


def dome(loc, r, mat):
    x, y, z = loc
    b = box("MosqueHall", (x, y, z + r * 0.6), (r * 2.4, r * 2.4, r * 1.2), mat)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=r, location=(x, y, z + r * 1.2))
    d = bpy.context.active_object; d.scale = (1, 1, 0.75); d.data.materials.append(mat)
    return b, d


def smoke(loc, height=14.0, radius=1.2, density=0.6, name="Smoke"):
    """Rising chimney plume: a tall volume whose noise scrolls upward with the frame (driver)."""
    x, y, z = loc
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=radius * 2.2, depth=height, location=(x + radius, y, z + height / 2))
    o = bpy.context.active_object; o.name = name
    m = bpy.data.materials.new(name + "M"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); v = N.new("ShaderNodeVolumePrincipled")
    v.inputs['Color'].default_value = (0.62, 0.62, 0.64, 1)
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Object'], sep.inputs[0])
    # radial falloff that widens with height and leans downwind (+X)
    zr = N.new("ShaderNodeMath"); zr.operation = 'MULTIPLY_ADD'; zr.inputs[1].default_value = 1.0 / height; zr.inputs[2].default_value = 0.5
    L.new(sep.outputs['Z'], zr.inputs[0])
    lean = N.new("ShaderNodeMath"); lean.operation = 'MULTIPLY'; lean.inputs[1].default_value = radius * 1.6; L.new(zr.outputs[0], lean.inputs[0])
    dx = N.new("ShaderNodeMath"); dx.operation = 'SUBTRACT'; L.new(sep.outputs['X'], dx.inputs[0]); L.new(lean.outputs[0], dx.inputs[1])
    cxy = N.new("ShaderNodeCombineXYZ"); L.new(dx.outputs[0], cxy.inputs[0]); L.new(sep.outputs['Y'], cxy.inputs[1])
    ln = N.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; L.new(cxy.outputs[0], ln.inputs[0])
    wdt = N.new("ShaderNodeMath"); wdt.operation = 'MULTIPLY_ADD'; wdt.inputs[1].default_value = radius * 1.4; wdt.inputs[2].default_value = radius * 0.35
    L.new(zr.outputs[0], wdt.inputs[0])
    rr = N.new("ShaderNodeMath"); rr.operation = 'DIVIDE'; L.new(ln.outputs['Value'], rr.inputs[0]); L.new(wdt.outputs[0], rr.inputs[1])
    fall = N.new("ShaderNodeMapRange"); fall.inputs['From Min'].default_value = 1.0; fall.inputs['From Max'].default_value = 0.0; L.new(rr.outputs[0], fall.inputs['Value'])
    top = N.new("ShaderNodeMapRange"); top.inputs['From Min'].default_value = 1.0; top.inputs['From Max'].default_value = 0.55; L.new(zr.outputs[0], top.inputs['Value'])
    # scrolling noise
    vw = N.new("ShaderNodeValue"); d = vw.outputs[0].driver_add("default_value").driver; d.type = 'SCRIPTED'; d.expression = "frame * 0.04"
    off = N.new("ShaderNodeCombineXYZ"); L.new(vw.outputs[0], off.inputs[2])
    sub = N.new("ShaderNodeVectorMath"); sub.operation = 'SUBTRACT'; L.new(tc.outputs['Object'], sub.inputs[0]); L.new(off.outputs[0], sub.inputs[1])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 0.45; nz.inputs['Detail'].default_value = 6; L.new(sub.outputs[0], nz.inputs['Vector'])
    nm = N.new("ShaderNodeMapRange"); nm.inputs['From Min'].default_value = 0.42; nm.inputs['From Max'].default_value = 0.7; L.new(nz.outputs['Fac'], nm.inputs['Value'])
    d1 = N.new("ShaderNodeMath"); d1.operation = 'MULTIPLY'; L.new(fall.outputs[0], d1.inputs[0]); L.new(nm.outputs[0], d1.inputs[1])
    d2 = N.new("ShaderNodeMath"); d2.operation = 'MULTIPLY'; L.new(d1.outputs[0], d2.inputs[0]); L.new(top.outputs[0], d2.inputs[1])
    d3 = N.new("ShaderNodeMath"); d3.operation = 'MULTIPLY'; d3.inputs[1].default_value = density; L.new(d2.outputs[0], d3.inputs[0])
    L.new(d3.outputs[0], v.inputs['Density']); L.new(v.outputs[0], out.inputs['Volume'])
    o.data.materials.append(m); o.visible_shadow = False
    return o


def periphery(rng, center=(0, 0), r_min=140.0, r_max=520.0, arc=(0, 360), n_blocks=260, hill_h=40.0, minarets=2, smokes=3, z0=0.0):
    """Istanbul periphery around `center`: rolling hills dotted with 4-8 storey concrete apartment blocks
    (instanced, varied facades) that fade into haze, a couple of minarets, a few smoking chimneys."""
    cx, cy = center
    hill_m = bpy.data.materials.new("HillGround"); hill_m.use_nodes = True
    Nn = hill_m.node_tree.nodes; Ll = hill_m.node_tree.links; p = Nn["Principled BSDF"]
    tc = Nn.new("ShaderNodeTexCoord"); nz = Nn.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 0.02; nz.inputs['Detail'].default_value = 8
    Ll.new(tc.outputs['Object'], nz.inputs['Vector'])
    cr = Nn.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.13, 0.12, 0.1, 1); cr.color_ramp.elements[1].color = (0.24, 0.22, 0.18, 1)
    Ll.new(nz.outputs['Fac'], cr.inputs['Fac']); Ll.new(cr.outputs['Color'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.95
    phs = rng.uniform(0, 6.28, 4)

    def hz(x, y):
        r = math.hypot(x - cx, y - cy)
        k = min(1.0, max(0.0, (r - r_min * 0.8) / (r_max - r_min)))
        a = math.atan2(y - cy, x - cx)
        return z0 + hill_h * k ** 0.8 * (0.65 + 0.2 * math.sin(2 * a + phs[0]) + 0.15 * math.sin(5 * a + phs[1]) + 0.1 * math.sin(r * 0.02 + phs[2]))
    n = 80
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=n, y_subdivisions=n, size=2 * r_max * 1.6, location=(cx, cy, 0))
    g = bpy.context.active_object; g.name = "Hills"
    for v in g.data.vertices:
        x, y = v.co.x + cx, v.co.y + cy
        r = math.hypot(x - cx, y - cy)
        v.co.z = hz(x, y) - 0.6 if r > r_min * 0.85 else -3.0
    g.data.materials.append(hill_m)
    # apartment block prototypes: a few footprints x storeys, flat roofs with a parapet and roof clutter
    bases = [(0.58, 0.54, 0.47), (0.55, 0.48, 0.45), (0.5, 0.5, 0.5), (0.56, 0.5, 0.4), (0.46, 0.48, 0.5)]
    mats = [facade_material(f"Facade{k}", b) for k, b in enumerate(bases)]
    roof_m = pbr("FlatRoof", (0.3, 0.29, 0.28), 0.9)
    protos = []
    for k in range(10):
        w = rng.uniform(10, 22); d = rng.uniform(9, 14); fl = int(rng.integers(4, 9)); h = fl * 2.9
        body = box("BlockP", (0, 0, h / 2), (w, d, h), mats[k % len(mats)])
        par = box("Parapet", (0, 0, h + 0.4), (w + 0.2, d + 0.2, 0.8), roof_m)
        tank = cyl("RoofTank", (w * 0.3, 0, h + 1.0), 0.6, 1.2, pbr("Tank", (0.4, 0.4, 0.42), 0.4, 0.6), verts=10)
        pr = join([body, par, tank], f"BlockProto{k}"); pr.location = (0, 0, -500)
        protos.append(pr)
    from rs_kit import gn_instances
    a0, a1 = math.radians(arc[0]), math.radians(arc[1])
    PL, PR, PS, PI = [], [], [], []
    for k in range(n_blocks):
        a = rng.uniform(a0, a1); r = r_min + (r_max - r_min) * rng.uniform(0, 1) ** 0.8
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        PL.append((x, y, hz(x, y) - 0.5)); PR.append((0, 0, a + rng.choice([0, math.pi / 2]) + rng.uniform(-0.15, 0.15)))
        PS.append(1.0); PI.append(int(rng.integers(len(protos))))
    gn_instances("Blocks", protos, PL, PR, PS, PI)
    stone = pbr("MinaretStone", (0.72, 0.7, 0.66), 0.8)
    for k in range(minarets):
        a = rng.uniform(a0, a1); r = rng.uniform(r_min * 1.4, r_max * 0.8)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        minaret((x, y, hz(x, y)), rng.uniform(30, 40), stone)
        dome((x + 9, y, hz(x, y)), 7, pbr("Lead", (0.4, 0.42, 0.44), 0.5, 0.4))
    for k in range(smokes):
        a = rng.uniform(a0, a1); r = rng.uniform(r_min * 1.1, r_max * 0.6)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a); z = hz(x, y)
        cyl("FactoryStack", (x, y, z + 15), 1.2, 30, pbr("Stack", (0.35, 0.3, 0.27), 0.85), verts=12)
        smoke((x, y, z + 30), height=40, radius=2.2, density=0.25)
    return hz


def pylons(rng, a, b, n=6, h=26, mat=None):
    """Distant high-voltage line: simple tapered lattice-like towers with sagging conductors."""
    a = Vector(a); b = Vector(b)
    mat = mat or pbr("Pylon", (0.25, 0.26, 0.27), 0.6, 0.5)
    pts = []
    for k in range(n):
        p = a.lerp(b, k / max(1, n - 1))
        legs = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                lb = Vector((p.x + sx * 2.5, p.y + sy * 2.5, p.z)); lt = Vector((p.x + sx * 0.5, p.y + sy * 0.5, p.z + h))
                o = cyl("PylonLeg", (lb + lt) / 2, 0.12, (lt - lb).length, mat, verts=4)
                o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = (lt - lb).to_track_quat('Z', 'Y')
        box("PylonArm", (p.x, p.y, p.z + h * 0.82), (0.4, 12, 0.4), mat)
        box("PylonArm", (p.x, p.y, p.z + h * 0.62), (0.4, 9, 0.4), mat)
        pts.append(p)
    wm = pbr("Conductor", (0.05, 0.05, 0.05), 0.5)
    for p, q in zip(pts[:-1], pts[1:]):
        for dy, zz in ((-6, 0.82), (6, 0.82), (-4.5, 0.62), (4.5, 0.62)):
            cu = bpy.data.curves.new("Cond", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.03
            sp = cu.splines.new('POLY'); sp.points.add(11)
            for i in range(12):
                t = i / 11; v = p.lerp(q, t) + Vector((0, dy, h * zz - 3.0 * 4 * t * (1 - t)))
                sp.points[i].co = (*v, 1)
            o = bpy.data.objects.new("Cond", cu); bpy.context.collection.objects.link(o); cu.materials.append(wm)


def water_material(name="Puddle"):
    m = pbr(name, (0.02, 0.022, 0.025), 0.03, 0.0, **{'Coat Weight': 0.0})
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); n = N.new("ShaderNodeTexNoise"); n.inputs['Scale'].default_value = 8; n.inputs['Detail'].default_value = 3
    L.new(tc.outputs['Object'], n.inputs['Vector'])
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.04; L.new(n.outputs['Fac'], b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


def puddles(rng, area, n=12, avoid=(), size=(0.8, 3.0), z=0.004):
    (x0, y0), (x1, y1) = area
    m = water_material()
    out = []
    for k in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if any(math.hypot(x - ax, y - ay) < ar for ax, ay, ar in avoid):
            continue
        s = rng.uniform(*size)
        bpy.ops.mesh.primitive_circle_add(vertices=20, radius=1.0, fill_type='NGON', location=(x, y, z))
        o = bpy.context.active_object; o.name = "Puddle"
        for v in o.data.vertices:                       # irregular outline
            a = math.atan2(v.co.y, v.co.x); r = 1 + 0.25 * math.sin(3 * a + k) + 0.15 * math.sin(5 * a + 2 * k)
            v.co.x *= r; v.co.y *= r
        o.scale = (s, s * rng.uniform(0.4, 0.8), 1); o.rotation_euler = (0, 0, rng.uniform(0, 3.14))
        o.data.materials.append(m)
        out.append(o)
    return out


# ------------------------------------------------------------------ cinematic house look (look.py, Nov 2026)
KEY_PREFIXES = ("Daylight", "DoorDay", "DoorShaft", "RoofShaft", "RoofDay", "FurnaceLight", "ORLamp", "LightField")
NIGHT_VARIANTS = ("night", "dusk", "yard_dusk")
EXT_EXPOSURE = {"mist": -0.2, "dusk": 0.2}


def cinematic(c, mod_name, mood="mist", keys=KEY_PREFIXES, night=("night",), dusk=("dusk", "yard_dusk"), gain=1.8):
    """Apply the house look recipe at the end of a set's build(), per shot: the move is read from argv (run.py /
    bake.py <set> <move>). Benchmark: nvidia_doc/review/cinematic_look_v3.jpg (mist day, dusk).
    The camera's start position decides the recipe:
      open sky  -> exterior: dark slate "mist" sky (or "dusk"), one low sun key BEHIND the subject (from ahead of
                   the camera, 35 deg off axis), ground haze around the camera, darker ground and walls;
      ceiling   -> interior by day: the room's window/door/shaft lights become the keys, everything else negative
                   fill, dark walls, warm practicals;
      night     -> night_interior (the set's own lights, deeper walls, warm practicals)."""
    import sys
    import look
    if not look.enabled():
        return None
    mod = sys.modules[mod_name]
    move = sys.argv[2] if len(sys.argv) > 2 else None
    spec = getattr(mod, "MOVES", {}).get(move)
    var = getattr(mod, "VARIANT_FOR", {}).get(move)
    if var in night:
        return look.night_interior()
    camp = tgt = None
    if spec:
        for pre in (False, True):
            try:
                if pre:
                    spec["anim"](c, 0.0)
                r = spec["cam"](c, 0.0); camp, tgt = Vector(r[0]), Vector(r[1]); break
            except Exception:
                camp = tgt = None
    sc = bpy.context.scene; bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    inside = False
    if camp is not None:
        hit, *_ = sc.ray_cast(dg, camp, Vector((0, 0, 1)), distance=8.0)
        inside = bool(hit)
    if not inside:
        md = "dusk" if var in dusk else mood
        azim = 200.0
        if camp is not None:
            v = tgt - camp
            azim = math.degrees(math.atan2(v.x, -v.y)) + 35.0       # sun ahead of the camera: subjects backlit
        for o in sc.objects:                       # the set's own haze would double the new ground haze
            if o.name.startswith("Haze") and o.data.materials:
                for n in o.data.materials[0].node_tree.nodes:
                    if n.type == 'PRINCIPLED_VOLUME':
                        n.inputs['Density'].default_value *= 0.4
        look.negative_fill(0.2)                    # no flat fill outdoors: the sun is the key
        k = look.day_light(md, azim=azim, exposure=EXT_EXPOSURE[md])   # open yards: the forest exposure would blow out
        ctr = camp if camp is not None else Vector((0, 0, 0))
        look.ground_haze((ctr.x, ctr.y), (320.0, 320.0), md, height=7.0, density=0.004)
        look.darken_surfaces(0.25, 0.85)
        return k
    near = [o for o in sc.objects if o.type == 'LIGHT' and o.name.startswith(keys)
            and (camp is None or (o.location - camp).length < 18.0)]
    for o in near:
        o["look_key"] = True
        if not (o.data.animation_data and o.data.animation_data.drivers):
            o.data.energy *= gain
    look.let_light_through()
    look.negative_fill(0.15 if near else 0.4)
    look.world_strength(0.35)
    look.warm_practicals()
    look.darken_surfaces(0.3)
    return dict(keys=near)
