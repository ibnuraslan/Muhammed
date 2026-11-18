"""Part 5: the records. SHOT=S24 (the Mary Celeste at anchor in Gibraltar Bay, the Rock behind, evening) or S25
(her cargo, casks of alcohol, landed on a quay at Genoa, morning)."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p5; C = p5.C
C.reset()
import numpy as np
import bpy
from mathutils import Vector, Matrix, noise
import ship, sea, props5 as PR

SHOT = os.environ.get("SHOT", "S24")
OUT = os.environ.get("OUT", os.path.join(p5.OUTDIR, f"{SHOT}.png"))
sc = C.render_setup(samples=int(os.environ.get("SPP", "160")), noise=0.03)


def mat(name, col, rough=0.8):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Roughness'].default_value = rough
    return m


def facade(name, col):
    """Plastered front with rows of dark shuttered windows (a brick texture used as a window grid)."""
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); br = N.new("ShaderNodeTexBrick")
    br.inputs['Scale'].default_value = 1.0; br.inputs['Brick Width'].default_value = 2.6; br.inputs['Row Height'].default_value = 3.2
    br.inputs['Mortar Size'].default_value = 1.1; br.offset = 0.0
    br.inputs['Color1'].default_value = (0.04, 0.035, 0.03, 1); br.inputs['Color2'].default_value = (0.05, 0.04, 0.035, 1)
    br.inputs['Mortar'].default_value = (*col, 1)
    L.new(tc.outputs['Object'], br.inputs['Vector']); L.new(br.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.85
    return m


def sun(d, energy, col, angle=1.0):
    s = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(s)
    s.data.energy = energy; s.data.color = col; s.data.angle = math.radians(angle)
    s.rotation_euler = (-Vector(d).normalized()).to_track_quat('-Z', 'Y').to_euler()


def town(x0, x1, y0, depth, zf, n, seed=1, colours=None, hmin=6, hmax=14):
    """Rows of houses: whitewashed / ochre boxes with tiled roofs and window rows (material)."""
    rng = np.random.default_rng(seed)
    cols = colours or [(0.75, 0.7, 0.6), (0.7, 0.55, 0.38), (0.62, 0.5, 0.4), (0.78, 0.74, 0.66), (0.55, 0.35, 0.25)]
    mats = []
    for k, c in enumerate(cols):
        m = bpy.data.materials.new(f"house{k}"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
        tc = N.new("ShaderNodeTexCoord"); br = N.new("ShaderNodeTexBrick"); br.inputs['Scale'].default_value = 0.35
        br.inputs['Mortar Size'].default_value = 0.0; br.inputs['Color1'].default_value = (*c, 1); br.inputs['Color2'].default_value = (*c, 1)
        br.inputs['Brick Width'].default_value = 1.0; br.inputs['Row Height'].default_value = 1.0
        ck = N.new("ShaderNodeTexChecker")
        mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (1.6, 1.6, 0.9); L.new(tc.outputs['Object'], mp.inputs['Vector'])
        L.new(mp.outputs[0], ck.inputs['Vector']); ck.inputs['Color1'].default_value = (*c, 1); ck.inputs['Color2'].default_value = (0.04, 0.035, 0.03, 1)
        ck.inputs['Scale'].default_value = 1.0
        L.new(ck.outputs['Color'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.85
        mats.append(m)
    roof = mat("roof", (0.35, 0.12, 0.06), 0.8)
    x = x0
    while x < x1:
        w = rng.uniform(5, 11); h = rng.uniform(hmin, hmax); d = rng.uniform(6, depth); y = y0 + rng.uniform(-1.5, 1.5)
        z = zf(x, y)
        ship.box("house", (x + w / 2, y + d / 2, z + h / 2), (w - 0.3, d, h), mats[rng.integers(len(mats))])
        ship.box("roof", (x + w / 2, y + d / 2, z + h + 0.4), (w - 0.1, d + 0.4, 0.8), roof)
        x += w


if SHOT == "S24":
    # Gibraltar Bay, from the west: the ship at anchor, the town along the shore, the Rock rising to the north
    water = sea.water_material()
    oc = sea.ocean(size=180, res=18, scale=0.5, chop=0.8, wind=5.0, repeat=2, foam=0.05, mat=water)
    sea.far_sea(190, mat=water)
    sea.sky(strength=0.55, rot_deg=100, res="4k", aid="qwantani_late_afternoon_puresky")
    mc = ship.build("MC", sails="found", rail_gap=None, wind=(0.3, -1, 0), wet=0.2, detail=False)
    mc["root"].location = (0, 0, -0.1); mc["root"].rotation_euler = (0, 0, math.radians(-25))
    # the Rock: a long limestone ridge (426 m) 2.5 km off, sheer north face, scrub on the slopes
    nx, ny = 200, 60; V = []; F = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            u = i / nx; v = j / ny
            x = 2600 + v * 1800; y = -2200 + u * 5200
            ridge = (np.clip(u * 1.25, 0, 1) ** 1.4) * (1 - np.clip((u - 0.83) / 0.17, 0, 1) ** 0.5)
            prof = math.sin(math.pi * min(1, v * 1.4)) ** 0.7
            n = noise.noise(Vector((u * 9, v * 5, 2))) * 0.12 + noise.noise(Vector((u * 30, v * 15, 3))) * 0.04
            V.append((x, y, max(-5.0, 420 * ridge * prof * (1 + n))))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i; F.append([a, a + 1, a + nx + 2, a + nx + 1])
    me = bpy.data.meshes.new("rock"); me.from_pydata(V, [], F); me.update()
    rock = bpy.data.objects.new("rock", me); sc.collection.objects.link(rock)
    m = bpy.data.materials.new("limestone"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    geo = N.new("ShaderNodeNewGeometry"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Normal'], sp.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 0.01; nz.inputs['Detail'].default_value = 10
    L.new(geo.outputs['Position'], nz.inputs['Vector'])
    flat = N.new("ShaderNodeMapRange"); flat.inputs['From Min'].default_value = 0.55; flat.inputs['From Max'].default_value = 0.8
    L.new(sp.outputs['Z'], flat.inputs['Value'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[6].default_value = (0.36, 0.33, 0.29, 1); mx.inputs[7].default_value = (0.1, 0.13, 0.05, 1)
    f2 = N.new("ShaderNodeMath"); f2.operation = 'MULTIPLY'; L.new(flat.outputs[0], f2.inputs[0]); L.new(nz.outputs['Fac'], f2.inputs[1])
    L.new(f2.outputs[0], mx.inputs['Factor']); L.new(mx.outputs[2], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.95
    rock.data.materials.append(m)
    for pl in me.polygons:
        pl.use_smooth = True
    # the town on the shore below the Rock's west face: three rows of houses climbing the slope
    rng = np.random.default_rng(2)
    yy = -1500
    while yy < 1600:
        for row in range(3):
            w = rng.uniform(8, 16); h = rng.uniform(7, 14); x = 2480 + row * 22 + rng.uniform(-3, 3)
            col = [(0.82, 0.78, 0.68), (0.78, 0.62, 0.42), (0.7, 0.58, 0.46), (0.86, 0.82, 0.74)][rng.integers(4)]
            ship.box("house", (x, yy, row * 6 + h / 2), (16, w - 0.5, h), mat(f"h{yy}{row}", col, 0.85))
            ship.box("roof", (x, yy, row * 6 + h + 0.5), (16.5, w, 1.0), mat("roof", (0.38, 0.13, 0.06), 0.8))
        yy += rng.uniform(9, 17)
    # other ships at anchor
    for k, (x, y, r) in enumerate(((180, 220, 30), (-150, 420, -70), (320, -260, 10))):
        try:
            root, _ = PR.put("dutch_ship_medium", (x, y, -1.0), rot_z=math.radians(r), size=32, axis=0, res="1k")
        except Exception as e:
            print("ship model failed", e)
    sun((-0.35, -0.9, 0.22), 4.0, (1.0, 0.72, 0.48), 1.2)
    C.camera(Vector((-95, -70, 7)), Vector((800, 380, 70)), lens=35)
    cine = {"sat": 1.12, "exposure": 0.0}
else:
    # Genoa: a stone quay, the casks landed and stacked, a ship's side alongside, the harbour front behind in haze
    water = sea.water_material()
    oc = sea.ocean(size=120, res=16, scale=0.2, chop=0.5, wind=3.0, repeat=2, foam=0.0, mat=water, loc=(0, -40, 0))
    sea.far_sea(130, mat=water, center=(0, -40))
    sea.sky(strength=1.0, rot_deg=200, res="4k", aid="qwantani_morning_puresky")
    import ph
    try:
        stone = ph.texture("cobblestone_floor_04", scale=1.0, res="1k", name="quay")
    except Exception:
        stone = mat("quay", (0.42, 0.38, 0.32), 0.9)
    ship.box("quay", (0, 15, -0.5), (200, 30, 3.0), stone)
    ship.box("quay_face", (0, 0.0, -1.0), (200, 0.6, 4.0), mat("quayface", (0.33, 0.3, 0.26), 0.95))
    rng = np.random.default_rng(5)
    roots = []
    for row in range(3):
        for k in range(9):
            for lvl in range(2 if row < 2 else 1):
                x = -6 + k * 0.95 + (0.47 if lvl else 0); y = 2.2 + row * 1.25
                z = 1.0 + lvl * 0.62
                r, bms = PR.put("wine_barrel_01", (x, y, z), size=1.0, axis=2, res="1k")
                r.rotation_euler = (math.radians(90), 0, math.radians(90 + rng.uniform(-4, 4)))
                bpy.context.view_layer.update()
                lo, hi = ph.bounds(bms)                       # lying on its side: rest it on the quay / the casks below
                r.location.z += (1.0 + lvl * 0.62) - lo[2]
                bpy.context.view_layer.update()
    mc = ship.build("MC", sails="found", rail_gap=None, wind=(0.3, -1, 0), wet=0.2, detail=False)
    mc["root"].location = (2, -ship.B / 2 - 1.2, -0.6); mc["root"].rotation_euler = (0, 0, 0)
    # harbour front: tall Genoese houses (ochre, rose) across the water in haze
    rng = np.random.default_rng(9)
    y = -260
    while y < 160:
        w = rng.uniform(10, 20); h = rng.uniform(16, 30)
        col = [(0.72, 0.45, 0.22), (0.7, 0.36, 0.28), (0.8, 0.62, 0.38), (0.62, 0.5, 0.36)][rng.integers(4)]
        ship.box("palazzo", (170 + rng.uniform(0, 10), y + w / 2, h / 2 + 2), (12, w - 0.5, h), facade(f"p{y}", col))
        y += w
    sun((0.5, -0.9, 0.35), 3.5, (1.0, 0.82, 0.62), 1.2)
    C.camera(Vector((-10.5, 4.6, 2.3)), Vector((20, -1.5, 3.0)), lens=30, fstop=5.6, focus=8.0)
    cine = {"sat": 1.1, "exposure": 0.0}

C.finish(OUT, cine=cine, bloom=0.4)
print("RENDERED", OUT)
