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
    oc = sea.ocean(size=900, res=18, scale=0.5, chop=0.8, wind=5.0, repeat=6, foam=0.05, mat=water)
    sea.far_sea(9000, mat=water)
    sea.sky(strength=0.55, rot_deg=100, res="4k", aid="qwantani_late_afternoon_puresky")
    mc = ship.build("MC", sails="found", rail_gap=None, wind=(0.3, -1, 0), wet=0.2, detail=False)
    mc["root"].location = (0, 0, -0.1); mc["root"].rotation_euler = (0, 0, math.radians(-25))
    # the Rock and the head of the bay from real elevation (P4's terrain.py), true scale, in evening haze; the
    # ship lies at anchor in the bay off the town (world origin = 36.132 N, 5.372 W)
    import land
    rock, height, world = land.gibraltar()
    # the town on the lower west slope of the Rock: rows of whitewashed / ochre houses set on the real ground
    rng = np.random.default_rng(2)
    for k in range(700):
        lon = rng.uniform(-5.3585, -5.3485); lat = rng.uniform(36.128, 36.146)
        p = world(lon, lat); z = height(p.x, p.y)
        if not (2.0 < z < 70.0):
            continue
        w = rng.uniform(12, 22); h = rng.uniform(9, 16); d = rng.uniform(12, 18)
        col = [(0.6, 0.55, 0.47), (0.62, 0.46, 0.3), (0.52, 0.42, 0.33), (0.66, 0.62, 0.54)][rng.integers(4)]
        ship.box("house", (p.x, p.y, z + h / 2 - 2.0), (d, w, h + 4.0), mat(f"h{k}", col, 0.85))
        ship.box("roof", (p.x, p.y, z + h + 0.5), (d + 0.5, w + 0.5, 1.0), mat("roof", (0.38, 0.13, 0.06), 0.8))
    # other ships at anchor
    for k, (x, y, r) in enumerate(((180, 220, 30), (-150, 420, -70), (320, -260, 10))):
        try:
            root, _ = PR.put("dutch_ship_medium", (x, y, -1.0), rot_z=math.radians(r), size=32, axis=0, res="1k")
        except Exception as e:
            print("ship model failed", e)
    sun((-0.35, -0.9, 0.22), 4.0, (1.0, 0.72, 0.48), 1.2)
    C.camera(Vector((-150, 30, 6)), Vector((2400, -330, 180)), lens=50)          # past the ship to the Rock
    cine = {"sat": 1.12, "exposure": 0.0}
else:
    # Genoa: Part 4's quay set used as is (mary_celeste_p4/shots/sets.py set_genoa: the ship alongside, the stone
    # quay, the casks of alcohol landed and stowed, Genoese ochre / terracotta / rose plaster fronts with green
    # shutters, late sun), so Genoa looks the same in both parts. Our framing: along the stow toward the houses.
    P4S = os.path.abspath(os.path.join(p5.ROOT, "mary_celeste_p4", "shots"))
    if P4S not in sys.path:
        sys.path.append(P4S)
    import sets as P4set
    g = P4set.set_genoa()
    QY, QZ = g["QY"], g["QZ"]
    C.camera(Vector((-19.0, QY + 1.2, QZ + 1.6)), Vector((4.0, QY + 9.0, QZ + 5.0)), lens=26, fstop=8.0)
    cine = {"sat": 1.08, "exposure": 0.0}

C.finish(OUT, cine=cine, bloom=0.4)
print("RENDERED", OUT)
