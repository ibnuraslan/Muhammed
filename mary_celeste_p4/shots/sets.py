"""Part 4 sets. Each set_* builds a scene and returns a dict of named anchors (world points / matrices)
that the shots (shots/board.py) use for cameras and blocking. Axes follow ship.py: bow +X, port +Y."""
import os, sys, math, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import p4
import bpy
from mathutils import Vector, Matrix
import ship, sea, ph
import barrels as BR, pump as PU, terrain as T, cutaway as CX

WIND = Vector((0.3, -1.0, 0)).normalized()
RED_SLOTS = [61, 62, 63, 140, 141, 142, 230, 231, 232]


def local_wind(hd):
    return Matrix.Rotation(math.radians(-hd), 3, 'Z') @ WIND


def _sun(azim, elev, energy, color, angle=4):
    return p4.sun(azim, elev, energy, color, angle)


def warm_haze(center, size, density=0.004, color=(1.0, 0.8, 0.6)):
    return sea.haze(center, size, density=density, color=color, aniso=0.5)


# ============================================================================= GENOA: quay, Dec 1872/Jan 1873
def set_genoa():
    sc = bpy.context.scene
    mc = ship.build("MC", sails="found", rail_gap=None, wind=local_wind(0), wet=0.1, detail=True, hatches_off=False, boat_chocks=False)
    p4.hide(("_sail", "shred"))
    for o in list(bpy.data.objects):                 # in port: no canvas set at all (sails unbent, sent ashore)
        if o.type == 'MESH' and any(m and "canvas" in m.name.lower() for m in o.data.materials):
            bpy.data.objects.remove(o, do_unlink=True)
    S = Matrix.Translation((0, 0, 0.35))                      # riding light, unloaded
    mc["root"].matrix_world = S
    # quay: stone wall face along the ship's port side, cobbles on top
    QY = ship.B / 2 + 0.9; QZ = 1.6
    stone = ship.wood("seaworn_sandstone_brick", 0.5, tint=(1.0, 0.85, 0.7), name="quaywall")
    cob = ship.wood("cobblestone_floor_04", 0.35, tint=(1.0, 0.86, 0.7), name="cobbles")
    ship.box("quay_wall", (0, QY + 4, QZ / 2 - 1.5), (120, 8, QZ + 3), stone)
    ship.box("quay_top", (0, QY + 15, QZ + 0.01), (120, 30, 0.02), cob)
    # buildings along the back of the quay: Genoese ochre, terracotta, pale rose plaster, green shutters
    rng = random.Random(4)
    cols = ["yellow_plaster", "red_plaster_weathered", "yellow_plaster_02", "painted_plaster_wall", "clay_plaster"]
    tints = [(1.0, 0.78, 0.45), (1.0, 0.62, 0.45), (1.0, 0.85, 0.6), (1.0, 0.7, 0.55), (1.0, 0.75, 0.5)]
    shutter = ship.paint("shutters", (0.06, 0.16, 0.08), rough=0.6, grime=0.4, chips=0.2)
    roof = ship.wood("red_slate_roof_tiles_01", 0.4, tint=(1, 0.8, 0.7), name="roof")
    darkwin = p4.mat("window", (0.02, 0.015, 0.012), rough=0.2)
    mats = [ship.wood(c, 0.25, tint=t, name=f"facade{k}") for k, (c, t) in enumerate(zip(cols, tints))]
    wins = []; shuts = []
    x = -60
    while x < 60:
        w = rng.uniform(7, 12); h = rng.uniform(13, 22); k = rng.randrange(len(mats))
        cy = QY + 24
        ship.box("bld", (x + w / 2, cy, QZ + h / 2), (w - 0.1, 10, h), mats[k])
        ship.box("roof", (x + w / 2, cy, QZ + h + 0.4), (w + 0.3, 10.6, 0.8), roof)
        z = QZ + 3.6
        while z < QZ + h - 1.5:
            xx = x + 1.3
            while xx < x + w - 1.0:
                wins.append(((xx, cy - 5.02, z), (0.9, 0.06, 1.6), 0.0))
                for sg in (-1, 1):
                    shuts.append(((xx + sg * 0.75, cy - 5.06 - 0.12, z), (0.55, 0.04, 1.65), sg * 0.35))
                xx += 2.3
            z += 3.4
        x += w
    p4.boxes("windows", wins, darkwin); p4.boxes("shutters", shuts, shutter)
    # a hill of the city behind, in haze
    ship.box("hill", (0, QY + 160, 20), (500, 40, 80), p4.mat("hill", (0.32, 0.24, 0.16), rough=0.9), rot=(0.25, 0, 0))
    # barrels on the quay: a long stow of full ones, and the nine red-oak barrels set apart
    out = dict(QY=QY, QZ=QZ)
    for i in range(14):
        for j in range(3):
            for k in range(2):
                M = Matrix.Translation((-14 + i * (BR.LEN + 0.04), QY + 2.4 + j * (BR.DIA + 0.01) + k * BR.R, QZ + BR.R + k * BR.R * math.sqrt(3))) @ \
                    Matrix.Rotation(rng.uniform(0, 6), 4, 'X')
                if k == 1 and j == 2:
                    continue
                BR.place("white", M)
    nine = []
    for k in range(9):
        p = Vector((3.2 + (k % 3) * (BR.DIA + 0.08), QY + 2.3 + (k // 3) * (BR.DIA + 0.1), QZ))
        nine.append(p)
        BR.upright("red", p, rot_z=rng.uniform(0, 6))
    out["nine"] = nine
    # chalk X on the nine heads (white strokes laid on the head)
    chalk = p4.mat("chalk", (0.85, 0.83, 0.78), rough=0.95)
    strokes = []
    for p in nine:                                  # hand-made X: two uneven strokes, each a few broken dabs
        base = rng.uniform(-0.4, 0.4)
        for a in (base + 0.78 + rng.uniform(-0.1, 0.1), base - 0.78 + rng.uniform(-0.1, 0.1)):
            L = rng.uniform(0.2, 0.27); d = Vector((math.cos(a), math.sin(a), 0))
            for k in range(7):
                u = (k / 6 - 0.5) * L
                c = p + Vector((rng.uniform(-0.01, 0.01), rng.uniform(-0.01, 0.01), BR.LEN + 0.0015)) + d * u
                strokes.append((c, (L / 6.5, rng.uniform(0.008, 0.013), 0.0012), a + rng.uniform(-0.05, 0.05)))
    p4.boxes("chalkX", strokes, chalk)
    # a mooring bollard and hawser
    iron = ship.iron("bollard_iron")
    ship.cyl("bollard", (-3, QY + 0.6, QZ), (-3, QY + 0.6, QZ + 0.6), 0.16, mat=iron, verts=24)
    ship.rope("hawser", [(-3, QY + 0.6, QZ + 0.45), (-6, ship.B / 2, ship.zdeck(-6) + 1.2)], 0.03, mc["mats"]["rope"], sag=0.4)
    water = sea.water_material()
    sea.ocean(size=160, res=18, scale=0.35, chop=0.6, wind=4.0, repeat=2, foam=0.0, mat=water, hulls=(), loc=(0, -40, 0))
    sea.far_sea(110, mat=water, center=(0, -40))
    sea.sky(strength=0.45, rot_deg=200, aid="belfast_sunset_puresky")
    _sun(235, 9, 6.0, (1.0, 0.58, 0.3), angle=1.2)
    warm_haze((0, 60, 20), (300, 200, 60), density=0.0016, color=(1.0, 0.82, 0.62))
    out["ship"] = mc
    return out


# ============================================================================= CUTAWAY (explainer)
def set_cutaway(water=0.0, vapor=0.0, lantern=True):
    sc = bpy.context.scene
    s = CX.build("MCX", y_cut=0.02)
    res = BR.stow(ymax=0.02, red_slots=RED_SLOTS)
    p4.world_color((0.03, 0.017, 0.011), 1.0)
    floor = p4.mat("void_floor", (0.04, 0.025, 0.017), rough=0.6)
    ship.box("ground", (0, 0, -3.25), (200, 200, 0.02), floor)
    p4.light('AREA', "key", 7000, (1.0, 0.76, 0.52), loc=(8, 15, 11), target=(0, -1, -0.5), size=9)
    p4.light('AREA', "fill", 900, (0.55, 0.6, 0.75), loc=(-12, 12, 2), target=(0, 0, 0), size=10)
    p4.light('AREA', "rim", 2500, (1.0, 0.7, 0.45), loc=(-16, -8, 9), target=(0, 0, 0), size=6)
    if lantern:
        p4.light('POINT', "holdlamp", 60, (1.0, 0.6, 0.28), loc=(-1.2, -0.6, 0.9), size=0.04)
    if water:
        wm = p4.mat("bilge", (0.02, 0.03, 0.025), rough=0.05)
        ship.box("bilgewater", (0.8, -1.2, -2.55 + water / 2), (21, 2.6, water), wm)
    if vapor:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0.8, -1.45, 0.9)); v = bpy.context.active_object; v.name = "vapor"
        v.scale = (17.5, 2.95, 0.75)                     # the space between the top tier and the deck beams
        vm = bpy.data.materials.new("vapor"); vm.use_nodes = True; N = vm.node_tree.nodes; L = vm.node_tree.links
        N.remove(N["Principled BSDF"]); vol = N.new("ShaderNodeVolumePrincipled")
        vol.inputs['Density'].default_value = 0.0; vol.inputs['Color'].default_value = (1.0, 0.85, 0.6, 1)
        nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 0.9; nz.inputs['Detail'].default_value = 4
        mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.25; mr.inputs['From Max'].default_value = 0.75
        mr.inputs['To Min'].default_value = 1.2 * vapor; mr.inputs['To Max'].default_value = 5.0 * vapor
        L.new(nz.outputs['Fac'], mr.inputs['Value']); L.new(mr.outputs[0], vol.inputs['Density'])
        L.new(vol.outputs[0], N["Material Output"].inputs['Volume']); v.data.materials.append(vm)
    return dict(ship=s, barrels=res)


# ============================================================================= THE HOLD (interior, lantern)
def set_hold(stain=True, lantern_swing=0.0, coal=False, barrels_on=True):
    """Inside the hold amidships, looking along the stow under the main hatch. Ceiling planking, beams,
    barrels in tiers each side of a narrow gap (where a man could crawl). One hanging lantern."""
    wood = ship.wood("brown_planks_05", 0.9, wet=0.25, tint=(0.95, 0.7, 0.5), name="holdwood")
    dark = ship.wood("dark_wooden_planks", 1.2, wet=0.3, tint=(0.8, 0.62, 0.48), name="holddark")
    out = {}
    # simple box hold section 8 m long amidships (x -4..4), real breadth/depth from the hull lines
    hb = ship.half_breadth(0.5, 0.9) - 0.28
    ship.box("hold_floor", (0, 0, -2.47), (10, 2 * hb, 0.05), dark)
    for sg in (1, -1):
        ship.box("hold_side", (0, sg * (hb + 0.02), -0.6), (10, 0.05, 3.9), wood)
    for k in range(9):
        x = -4 + k * 1.15
        ship.box("beam", (x, 0, ship.zdeck(x) - 0.17), (0.2, 2 * hb, 0.22), dark)
        for sg in (1, -1):
            ship.box("knee", (x, sg * (hb - 0.25), ship.zdeck(x) - 0.45), (0.16, 0.5, 0.5), dark, rot=(sg * 0.7, 0, 0))
    if coal:                                   # a hatch open further forward lets the daylight in
        ship.box("hold_deckhead", (-1.55, 0, ship.zdeck(0)), (6.9, 2 * hb, 0.06), dark)
        ship.box("hold_deckhead2", (4.2, 0, ship.zdeck(4)), (1.6, 2 * hb, 0.06), dark)
    else:
        ship.box("hold_deckhead", (0, 0, ship.zdeck(0) + 0.0), (10, 2 * hb, 0.06), dark)
    ship.box("pillar", (1.5, 0.0, -0.6), (0.18, 0.18, 3.8), dark)
    if barrels_on:
        rng = random.Random(8)
        dz = BR.R * math.sqrt(3)
        for side in (1, -1):
            tier = 0; z = -2.45 + BR.R
            while z < 0.9:
                off = (tier % 2) * BR.R
                y = side * (0.55 + BR.R + off)
                while abs(y) < hb - BR.R:
                    for i in range(10):
                        x = -4.2 + i * (BR.LEN + 0.03)
                        kind = "red" if (side == -1 and tier == 0 and i in (3,)) and abs(y) < 1.3 else "white"
                        M = Matrix.Translation((x, y, z)) @ Matrix.Rotation(rng.uniform(0, 6.3), 4, 'X')
                        BR.place(kind, M)
                        if kind == "red":
                            out["red"] = Vector((x, y, z))
                    y += side * (BR.DIA + 0.004)
                tier += 1; z += dz
    if stain and "red" in out:
        r = out["red"]
        st = p4.mat("stain", (0.03, 0.02, 0.012), rough=0.12)
        ship.box("stain", (r.x, r.y * 0.7, -2.443), (0.9, 0.5, 0.002), st, rot=(0, 0, 0.2))
    if coal:
        cm = p4.mat("coaldust", (0.015, 0.013, 0.013), rough=0.85)
        rng = random.Random(3)
        for k in range(1400):
            p = Vector((rng.uniform(-4.5, 4.5), rng.uniform(-hb + 0.1, hb - 0.1), -2.44))
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rng.uniform(0.004, 0.02), location=p)
            g = bpy.context.active_object; g.data.materials.append(cm); g.scale.z = 0.5
        sh = p4.mat("shavings", (0.7, 0.5, 0.3), rough=0.7)
        for k in range(40):
            c = Vector((rng.uniform(-3, 3), rng.uniform(-hb + 0.3, hb - 0.3), -2.43))
            pts = [c + Vector((0.03 * math.cos(t * 6), 0.03 * math.sin(t * 6), 0.006 * t)) for t in [i / 12 for i in range(13)]]
            ship.rope("shaving", pts, 0.003, sh)
    # lantern hanging from a beam on a short lanyard; swing angle in degrees
    ln, lms = ph.model("wooden_lantern_01"); p4.lamp_glass_passes(lms)
    pivot = Vector((0.35, 0.0, ship.zdeck(0.35) - 0.3))
    a = math.radians(lantern_swing)
    ln.matrix_world = Matrix.Translation(pivot) @ Matrix.Rotation(a, 4, 'X') @ Matrix.Translation((0, 0, -0.55))
    ship.rope("lanyard", [pivot, pivot + Matrix.Rotation(a, 3, 'X') @ Vector((0, 0, -0.04))], 0.004, ship.tarred_rope("lanyard_m"))
    flame = p4.light('POINT', "flame", 90, (1.0, 0.55, 0.22), loc=ln.matrix_world @ Vector((0, 0, 0.2)), size=0.02)
    out["lantern"] = ln.matrix_world @ Vector((0, 0, 0.2))
    # lantern light bouncing off the deckhead and the stows: a warm soft fill so the hold reads
    p4.light('AREA', "bounce", 140, (1.0, 0.62, 0.32), loc=(0.3, 0, ship.zdeck(0) - 0.45), target=(0.3, 0, -2.4), size=5.0)
    p4.light('POINT', "low_fill", 25, (1.0, 0.6, 0.3), loc=(-2.5, 0.0, -1.6), size=0.3)
    out["hb"] = hb
    # a grey shaft of daylight from a hatch further forward (the main hatch is battened)
    p4.light('SPOT', "hatchlight", 6000 if coal else 0, (0.85, 0.88, 0.9), loc=(2.6, 0, 5.0), target=(2.4, 0, -2.4), size=0.6, spot=22, blend=0.3)
    warm_haze((0, 0, -0.6), (10, 2 * hb, 4), density=0.03 if not coal else 0.06, color=(1.0, 0.85, 0.7))
    p4.world_color((0.0, 0.0, 0.0))
    return out


# ============================================================================= OAK STUDIO (explainer)
def set_oak():
    """Two staves' end grain on a dark table under a lamp: white oak (tyloses, sealed) vs red oak (open pores).
    Behind them two whole barrels, one of each."""
    out = {}
    tbl = ship.wood("wood_table_worn", 0.6, tint=(0.9, 0.7, 0.5), name="studio_table")
    ship.box("table", (0, 0, 0.4), (3.0, 1.6, 0.06), tbl)
    for kind, x in (("white", -0.55), ("red", 0.55)):
        BR.upright(kind, (x, 0.35, 0.43), rot_z=0.3)
    for kind, x, aid, tint in (("white", -0.32, "white_oak_veneer", (1.0, 0.92, 0.78)), ("red", 0.32, "red_oak_veneer", (1.0, 0.8, 0.7))):
        m = ship.wood(aid, 0.18, tint=tint, name=f"stave_{kind}")
        st = ship.box(f"stave_{kind}", (x, -0.25, 0.43 + 0.012), (0.5, 0.1, 0.024), m, bevel=0.002)
        # end grain face: growth rings with earlywood pores (ring-porous oak). Red oak: big open pores.
        # White oak: the same pores plugged by tyloses (glossy pale fill), so they read closed.
        endm = end_grain(kind)
        e_o = end_face(f"end_{kind}", kind, Vector((x - 0.2501, -0.25, 0.442)), endm)
        out[kind] = Vector((x - 0.25, -0.25, 0.442))
    # beads of spirit sweating out of the red oak stave's end and face
    drop = bpy.data.materials.new("spirit"); drop.use_nodes = True
    dp = drop.node_tree.nodes["Principled BSDF"]; dp.inputs['Transmission Weight'].default_value = 1; dp.inputs['Roughness'].default_value = 0.02
    dp.inputs['IOR'].default_value = 1.36
    rng = random.Random(5)
    for k in range(7):                     # beads standing on the red-oak end grain, where the open vessels end
        r = rng.uniform(0.0005, 0.0011)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(0.32 - 0.2512 - r * 0.45, -0.25 + rng.uniform(-0.045, 0.045), 0.443 + rng.uniform(-0.009, 0.009)))
        o = bpy.context.active_object; o.scale.x = 0.5; o.data.materials.append(drop)
        bpy.ops.object.shade_smooth()
    p4.world_color((0.012, 0.008, 0.006))
    p4.light('SPOT', "rake", 12, (1.0, 0.8, 0.55), loc=(0.035, -0.75, 0.47), target=(0.07, -0.25, 0.442), size=0.02, spot=25, blend=0.5)
    p4.light('SPOT', "lamp", 45, (1.0, 0.76, 0.5), loc=(0.2, -0.6, 1.6), target=(0, -0.1, 0.45), size=0.12, spot=55, blend=0.7)
    p4.light('AREA', "rim", 60, (1.0, 0.8, 0.6), loc=(-0.6, 1.2, 0.9), target=(0, 0, 0.5), size=1.0)
    p4.light('AREA', "fill", 12, (0.6, 0.7, 0.9), loc=(-1.2, -1.3, 0.8), target=(0, 0, 0.5), size=1.5)
    return out


def end_face(name, kind, c, mat, w=0.1, h=0.024, nu=560, nv=136, seed=3, bend=None):
    """The stave's end as a real relief: a fine grid on the end face with the earlywood pores sunk into it
    (red oak: open vessels ~0.3 mm across, 1.5 mm deep; white oak: the same vessels filled level by tyloses)."""
    import numpy as np
    rng = np.random.default_rng(seed)
    ys = np.linspace(-w / 2, w / 2, nu); zs = np.linspace(-h / 2, h / 2, nv)
    Y, Z = np.meshgrid(ys, zs)
    depth = np.zeros_like(Y)
    n = 2600 if kind == "red" else 2600
    py = rng.uniform(-w / 2, w / 2, n); pz = rng.uniform(-h / 2, h / 2, n)
    pr = np.hypot(pz * 0.15, py + 0.6) * 260.0           # quartersawn: rings run across the thickness
    keep = (pr - np.floor(pr)) < 0.26
    rad = 0.00032 if kind == "red" else 0.00022
    dmax = 0.0016 if kind == "red" else 0.00008
    for yy, zz in zip(py[keep], pz[keep]):
        j0 = int((yy + w / 2) / w * (nu - 1)); i0 = int((zz + h / 2) / h * (nv - 1))
        for i in range(max(0, i0 - 3), min(nv, i0 + 4)):
            for j in range(max(0, j0 - 3), min(nu, j0 + 4)):
                d = np.hypot(Y[i, j] - yy, Z[i, j] - zz)
                if d < rad:
                    depth[i, j] = max(depth[i, j], dmax * (1 - (d / rad) ** 4))
    X = -depth                                    # sink into the stave (the face looks toward -X)
    flat = np.stack([X, Y, Z], -1).reshape(-1, 3)
    if bend is not None:
        V = bend(flat)
    else:
        V = flat + np.array([c.x, c.y, c.z])
    idx = np.arange(nu * nv).reshape(nv, nu)
    F = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]], -1).reshape(-1, 4)
    me = bpy.data.meshes.new(name); me.from_pydata(V.tolist(), [], F.tolist()); me.update()
    at = me.attributes.new("flat", 'FLOAT_VECTOR', 'POINT'); at.data.foreach_set("vector", flat.astype(np.float32).reshape(-1))
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); me.materials.append(mat)
    return o


def end_grain(kind):
    m = bpy.data.materials.new(f"endgrain_{kind}"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeAttribute"); tc.attribute_name = "flat"          # the face's own flat coordinates
    # rings: concentric about a pith far off to one side (quartersawn: rings run across the stave's thickness)
    mp = N.new("ShaderNodeMapping"); mp.inputs['Location'].default_value = (0, 0.6, 0)
    mp.inputs['Scale'].default_value = (1, 1, 0.15)
    L.new(tc.outputs['Vector'], mp.inputs['Vector'])
    ln = N.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; L.new(mp.outputs[0], ln.inputs[0])
    wv = N.new("ShaderNodeTexNoise"); wv.inputs['Scale'].default_value = 60.0; wv.inputs['Detail'].default_value = 3
    L.new(tc.outputs['Vector'], wv.inputs['Vector'])
    wa = N.new("ShaderNodeMath"); wa.operation = 'MULTIPLY_ADD'; wa.inputs[1].default_value = 0.0012
    L.new(wv.outputs['Fac'], wa.inputs[0]); L.new(ln.outputs['Value'], wa.inputs[2])
    rs = N.new("ShaderNodeMath"); rs.operation = 'MULTIPLY'; rs.inputs[1].default_value = 260.0; L.new(wa.outputs[0], rs.inputs[0])
    fr = N.new("ShaderNodeMath"); fr.operation = 'FRACT'; L.new(rs.outputs[0], fr.inputs[0])
    early = N.new("ShaderNodeMapRange"); early.inputs['From Min'].default_value = 0.0; early.inputs['From Max'].default_value = 0.3
    early.inputs['To Min'].default_value = 1.0; early.inputs['To Max'].default_value = 0.0; L.new(fr.outputs[0], early.inputs['Value'])
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs['Scale'].default_value = 900.0 if kind == "red" else 1100.0
    vo.inputs['Randomness'].default_value = 0.9; L.new(tc.outputs['Vector'], vo.inputs['Vector'])
    pr = N.new("ShaderNodeMapRange"); pr.inputs['From Min'].default_value = 0.26 if kind == "red" else 0.16
    pr.inputs['From Max'].default_value = 0.34 if kind == "red" else 0.21
    pr.inputs['To Min'].default_value = 1.0; pr.inputs['To Max'].default_value = 0.0; L.new(vo.outputs['Distance'], pr.inputs['Value'])
    pore = N.new("ShaderNodeMath"); pore.operation = 'MULTIPLY'; L.new(pr.outputs[0], pore.inputs[0]); L.new(early.outputs[0], pore.inputs[1])
    base = (0.25, 0.165, 0.10) if kind == "white" else (0.40, 0.21, 0.14)      # aged, oiled-dark end grain
    late = (0.19, 0.125, 0.075) if kind == "white" else (0.26, 0.12, 0.08)
    c1 = N.new("ShaderNodeMix"); c1.data_type = 'RGBA'; c1.inputs[6].default_value = (*late, 1); c1.inputs[7].default_value = (*base, 1)
    L.new(early.outputs[0], c1.inputs['Factor'])
    hole = (0.015, 0.008, 0.005, 1) if kind == "red" else (0.21, 0.14, 0.085, 1)     # open void vs tylose plug (filled, a shade darker)
    c2 = N.new("ShaderNodeMix"); c2.data_type = 'RGBA'; L.new(c1.outputs[2], c2.inputs[6]); c2.inputs[7].default_value = hole
    L.new(pore.outputs[0], c2.inputs['Factor']); L.new(c2.outputs[2], p.inputs['Base Color'])
    rr = N.new("ShaderNodeMapRange"); rr.inputs['To Min'].default_value = 0.7; rr.inputs['To Max'].default_value = 0.9 if kind == "red" else 0.2
    L.new(pore.outputs[0], rr.inputs['Value']); L.new(rr.outputs[0], p.inputs['Roughness'])
    b = N.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.9 if kind == "red" else 0.15; b.invert = True
    L.new(pore.outputs[0], b.inputs['Height'])
    # saw marks: shallow arcs from the cooper's saw, at a slant across the cut
    sm = N.new("ShaderNodeMapping"); sm.inputs['Rotation'].default_value = (0.5, 0, 0)
    L.new(tc.outputs['Vector'], sm.inputs['Vector'])
    sw = N.new("ShaderNodeTexWave"); sw.wave_type = 'RINGS'; sw.inputs['Scale'].default_value = 1.4; sw.inputs['Distortion'].default_value = 2.0
    sw.inputs['Detail'].default_value = 2
    sl = N.new("ShaderNodeMapping"); sl.inputs['Location'].default_value = (0, 0.25, 0.0); sl.inputs['Scale'].default_value = (1, 1, 1)
    L.new(sm.outputs[0], sl.inputs['Vector']); L.new(sl.outputs[0], sw.inputs['Vector'])
    sb = N.new("ShaderNodeBump"); sb.inputs['Strength'].default_value = 0.12; sb.inputs['Distance'].default_value = 0.0004
    L.new(sw.outputs['Fac'], sb.inputs['Height']); L.new(b.outputs['Normal'], sb.inputs['Normal'])
    L.new(sb.outputs['Normal'], p.inputs['Normal'])
    return m


def _aged_oak(aid, tint, name, hoops=((0.13, 0.175),), dark=0.55):
    """Real oak texture (Poly Haven), darkened and aged; grime; dark iron-hoop stains with rust at the hoop seats."""
    m = ship.wood(aid, 0.9, tint=tint, name=name)
    N = m.node_tree.nodes; Lk = m.node_tree.links; p = N["Principled BSDF"]
    src = p.inputs['Base Color'].links[0].from_socket
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(tc.outputs['Object'], sep.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 40; nz.inputs['Detail'].default_value = 8
    Lk.new(tc.outputs['Object'], nz.inputs['Vector'])
    band = None
    for y0, y1 in hoops:
        a1 = N.new("ShaderNodeMapRange"); a1.inputs['From Min'].default_value = y0 - 0.006; a1.inputs['From Max'].default_value = y0 + 0.004
        a2 = N.new("ShaderNodeMapRange"); a2.inputs['From Min'].default_value = y1 + 0.006; a2.inputs['From Max'].default_value = y1 - 0.004
        Lk.new(sep.outputs['Y'], a1.inputs['Value']); Lk.new(sep.outputs['Y'], a2.inputs['Value'])
        mn = N.new("ShaderNodeMath"); mn.operation = 'MINIMUM'; Lk.new(a1.outputs[0], mn.inputs[0]); Lk.new(a2.outputs[0], mn.inputs[1])
        band = mn
    jit = N.new("ShaderNodeMath"); jit.operation = 'MULTIPLY'; Lk.new(band.outputs[0], jit.inputs[0])
    jr = N.new("ShaderNodeMapRange"); jr.inputs['From Min'].default_value = 0.3; jr.inputs['From Max'].default_value = 0.6
    jr.inputs['To Min'].default_value = 0.55; Lk.new(nz.outputs['Fac'], jr.inputs['Value']); Lk.new(jr.outputs[0], jit.inputs[1])
    dk = N.new("ShaderNodeMix"); dk.data_type = 'RGBA'; dk.blend_type = 'MULTIPLY'; dk.inputs['Factor'].default_value = 1
    dk.inputs[7].default_value = (dark, dark * 0.9, dark * 0.82, 1); Lk.new(src, dk.inputs[6])
    gr = N.new("ShaderNodeMix"); gr.data_type = 'RGBA'; gr.blend_type = 'MULTIPLY'
    gr.inputs[7].default_value = (0.6, 0.55, 0.5, 1)
    gm = N.new("ShaderNodeMapRange"); gm.inputs['From Min'].default_value = 0.45; gm.inputs['From Max'].default_value = 0.72; gm.inputs['To Max'].default_value = 0.8
    Lk.new(nz.outputs['Fac'], gm.inputs['Value']); Lk.new(gm.outputs[0], gr.inputs['Factor']); Lk.new(dk.outputs[2], gr.inputs[6])
    hs = N.new("ShaderNodeMix"); hs.data_type = 'RGBA'; hs.inputs[7].default_value = (0.05, 0.03, 0.02, 1)       # iron-black stain
    Lk.new(jit.outputs[0], hs.inputs['Factor']); Lk.new(gr.outputs[2], hs.inputs[6])
    rs = N.new("ShaderNodeMix"); rs.data_type = 'RGBA'; rs.blend_type = 'MIX'; rs.inputs[7].default_value = (0.22, 0.08, 0.03, 1)  # rust bleed
    rq = N.new("ShaderNodeMath"); rq.operation = 'MULTIPLY'; rq.inputs[1].default_value = 0.45
    rn = N.new("ShaderNodeTexNoise"); rn.inputs['Scale'].default_value = 120; Lk.new(tc.outputs['Object'], rn.inputs['Vector'])
    Lk.new(rn.outputs['Fac'], rq.inputs[0])
    rq2 = N.new("ShaderNodeMath"); rq2.operation = 'MULTIPLY'; Lk.new(rq.outputs[0], rq2.inputs[0]); Lk.new(band.outputs[0], rq2.inputs[1])
    Lk.new(rq2.outputs[0], rs.inputs['Factor']); Lk.new(hs.outputs[2], rs.inputs[6])
    Lk.new(rs.outputs[2], p.inputs['Base Color'])
    p.inputs['Coat Weight'].default_value = 0.0; p.inputs['Specular IOR Level'].default_value = 0.3
    return m


def stave_mesh(name, cx, Z0, R=0.30, T=0.022, W=0.10, L=0.55, mat=None, nu=28, nl=40):
    """A real barrel stave: curved across its width (barrel radius R), bevelled (radial) jointed edges, lying on
    its convex outer face, length along +Y from y=0 (the cut end, toward the camera)."""
    import numpy as np
    am = W / 2 / (R - T / 2)
    V = []; F = []
    def P(a, r, y):
        return (cx + r * math.sin(a), y, Z0 + R - r * math.cos(a))
    def grid(fn, nA, nB):
        b0 = len(V)
        for j in range(nB + 1):
            for i in range(nA + 1):
                V.append(fn(i / nA, j / nB))
        for j in range(nB):
            for i in range(nA):
                a = b0 + j * (nA + 1) + i
                F.append([a, a + 1, a + nA + 2, a + nA + 1])
    y0 = 0.0004
    grid(lambda u, v: P(-am + 2 * am * u, R, y0 + L * v), nu, nl)                 # outer (bottom)
    grid(lambda u, v: P(am - 2 * am * u, R - T, y0 + L * v), nu, nl)              # inner (top, concave)
    for sg in (-1, 1):                                                               # jointed edges (radial)
        grid(lambda u, v: P(sg * am, R - T * u if sg > 0 else R - T * (1 - u), y0 + L * v), 4, nl)
    grid(lambda u, v: P(-am + 2 * am * u, R - T * v, y0 + L), nu, 4)               # far end
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    mw = o.modifiers.new("weld", "WELD"); mw.merge_threshold = 0.0002
    bv = o.modifiers.new("bev", "BEVEL"); bv.width = 0.0012; bv.segments = 2; bv.limit_method = 'ANGLE'
    if mat:
        me.materials.append(mat)
    def bend(flat):                                # end-face flat (depth, width, thickness) -> on the stave's cut end
        a = flat[:, 1] / (R - T / 2); r = R - T / 2 - flat[:, 2]
        return np.stack([cx + r * np.sin(a), -flat[:, 0], Z0 + R - r * np.cos(a)], -1)
    return o, bend


def set_staves():
    """S12: a cooper's bench. Two real barrel staves (curved, bevelled, aged oak, hoop stains) lie side by side with
    their saw-cut ends to camera: white oak (left; vessels plugged by tyloses) and red oak (right; open vessels).
    Spirit seeps from the red oak's end grain; one small drop at its foot; a thin wet stain darkens the bench.
    A lantern stands on the bench in a little haze (nobody in frame, so no hand)."""
    out = {}
    bench = ship.wood("wood_table_worn", 0.5, tint=(0.85, 0.62, 0.44), name="bench")
    bench_o = ship.box("bench", (0, 0, 0.42), (1.4, 0.7, 0.06), bench)
    Z0 = 0.45
    for kind, x, aid, tint in (("white", -0.062, "oak_veneer_01", (0.85, 0.72, 0.55)), ("red", 0.062, "red_oak_veneer", (0.8, 0.55, 0.42))):
        m = _aged_oak(aid, tint, f"stavewood_{kind}")
        st, bend = stave_mesh(f"stave_{kind}", x, Z0, mat=m)
        e = end_face(f"end_{kind}", kind, Vector((0, 0, 0)), end_grain(kind), w=0.0985, h=0.0205, nu=760, nv=170,
                     seed=4 if kind == "red" else 9, bend=bend)
        out[kind] = Vector((x, 0.0, Z0 + 0.011))
    # spirit on the red oak's end: beads in the open pores, one small drop gathering at the lowest point
    drop = bpy.data.materials.new("spirit"); drop.use_nodes = True
    dp = drop.node_tree.nodes["Principled BSDF"]; dp.inputs['Transmission Weight'].default_value = 1; dp.inputs['Roughness'].default_value = 0.02
    dp.inputs['IOR'].default_value = 1.36; dp.inputs['Base Color'].default_value = (1, 0.97, 0.9, 1)
    rng = random.Random(5)
    rx = 0.062
    for k in range(16):
        r = rng.uniform(0.00025, 0.0006); u = rng.uniform(-0.045, 0.045)
        a = u / 0.289; rr = 0.289 + rng.uniform(-0.009, 0.009)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(rx + rr * math.sin(a), -r * 0.3, Z0 + 0.30 - rr * math.cos(a)))
        o = bpy.context.active_object; o.scale.y = 0.45; o.data.materials.append(drop); bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.003, location=(rx + 0.002, -0.003, Z0 + 0.003))
    o = bpy.context.active_object; o.scale = (1, 0.9, 1.15); o.data.materials.append(drop); bpy.ops.object.shade_smooth()
    # the wet stain: an irregular, very thin darkening of the bench itself (same texture, darker and satin)
    wet = bench.copy(); wet.name = "bench_wet"
    wp = wet.node_tree.nodes["Principled BSDF"]
    src = wp.inputs['Base Color'].links[0].from_socket
    dk = wet.node_tree.nodes.new("ShaderNodeMix"); dk.data_type = 'RGBA'; dk.blend_type = 'MULTIPLY'; dk.inputs['Factor'].default_value = 1
    dk.inputs[7].default_value = (0.22, 0.16, 0.12, 1); wet.node_tree.links.new(src, dk.inputs[6]); wet.node_tree.links.new(dk.outputs[2], wp.inputs['Base Color'])
    for l in list(wp.inputs['Roughness'].links):
        wet.node_tree.links.remove(l)
    wp.inputs["Roughness"].default_value = 0.16
    import mathutils
    pts = []
    for k in range(48):
        a = 2 * math.pi * k / 48
        rr = 0.026 * (1 + 0.45 * mathutils.noise.noise(Vector((math.cos(a) * 1.7, math.sin(a) * 1.7, 0.3))) + 0.2 * math.sin(3 * a + 1))
        pts.append(Vector((rx + 0.004 + rr * math.cos(a) * 1.3, -0.014 + rr * math.sin(a) * 0.8, 0.0)))
    cen = sum(pts, Vector()) / len(pts)
    bo = bench_o.location
    Vv = [tuple(cen + Vector((0, 0, Z0 + 0.00012)) - bo)] + [tuple(p + Vector((0, 0, Z0 + 0.00012)) - bo) for p in pts]
    Ff = [[0, 1 + k, 1 + (k + 1) % 48] for k in range(48)]
    me = bpy.data.meshes.new("wetstain"); me.from_pydata(Vv, [], Ff); me.update()
    ws = bpy.data.objects.new("wetstain", me); bpy.context.scene.collection.objects.link(ws); ws.location = bo; me.materials.append(wet)
    # lantern on the bench, left and forward; haze around it
    ln, lms = ph.model("wooden_lantern_01"); p4.lamp_glass_passes(lms)
    ln.matrix_world = Matrix.Translation((-0.24, -0.1, Z0)) @ Matrix.Rotation(0.4, 4, 'Z')
    p4.light('POINT', "lantern_flame", 4, (1.0, 0.58, 0.26), loc=(-0.24, -0.1, Z0 + 0.2), size=0.012)
    p4.light('SPOT', "lantern_spill", 1.5, (1.0, 0.6, 0.3), loc=(-0.21, -0.08, Z0 + 0.12), target=(0.02, 0, Z0 + 0.02), size=0.03, spot=30, blend=0.6)
    p4.light('AREA', "rim", 3, (1.0, 0.8, 0.6), loc=(0.3, 0.5, Z0 + 0.3), target=(0, 0, Z0 + 0.05), size=0.4)
    p4.light('AREA', "fill", 0.6, (0.6, 0.7, 0.9), loc=(0.25, -0.5, Z0 + 0.2), target=(0, 0, Z0 + 0.05), size=0.5)
    walls = ship.wood("dark_wooden_planks", 1.2, tint=(0.6, 0.42, 0.3), name="shop")
    ship.box("shopwall", (0, 1.2, 1.0), (4, 0.1, 2), walls)
    for k in range(3):
        BR.upright("white", (-0.7 + k * 0.7, 0.75, 0.0), rot_z=k)
    warm_haze((-0.2, 0.1, 0.65), (1.2, 1.0, 0.5), density=0.12, color=(1.0, 0.8, 0.6))
    warm_haze((0, 0.4, 0.9), (3, 2, 1.6), density=0.02, color=(1.0, 0.85, 0.7))
    p4.world_color((0.006, 0.004, 0.003))
    out["Z0"] = Z0
    return out


# ============================================================================= THE DECK (as found, day)
YAWL = "a9ce4ca0cac14f448c72bb94ad193437"     # "Old Boat" by donnichols (CC BY): stands in for the ship's yawl


def set_deck(time="day", heel=2.5, rail_gap=(-2.7, -0.6, "S"), pumps="found", sails="found", sea_k=1.0,
             forehatch_off=True, boat=None):
    """The Mary Celeste's deck. time: 'day' (grey Atlantic noon, as Deveau found her), 'dusk' (warm low sun,
    before the weather), 'night' (lantern, after rough weather), 'dawn' (grey-rose, Santa Maria on the horizon)."""
    sc = bpy.context.scene
    mc = ship.build("MC", sails=sails, rail_gap=rail_gap, wind=local_wind(0), wet=0.8 if time != "dusk" else 0.25,
                    detail=True, hatches_off=forehatch_off, boat_chocks=True)
    R = Matrix.Rotation(math.radians(-heel), 4, 'X')
    mc["root"].matrix_world = R
    bpy.context.view_layer.update()
    SHIP = mc["root"].matrix_world.copy()
    # replace the library's simple pump posts with the detailed pumps (one each side of the mainmast)
    p4.hide(("MC_pump",))
    px = ship.MAIN_X + 0.9
    out = dict(ship=mc, SHIP=SHIP, px=px)
    pcoll = bpy.data.collections.new("pumps"); sc.collection.children.link(pcoll)
    PU.pump("pumpS", (px, -0.7, ship.zdeck(px)), intact=True, coll=pcoll, brake_angle=8)
    # the main hatch battened down: three iron bars across the cover, wedges along the coaming
    xm = ship.MAIN_HATCH_X; zc = ship.zdeck(xm)
    iron = ship.iron("hatchbar")
    bars = [((xm + dx, 0, zc + 0.505), (0.07, 2.62, 0.03), 0.0) for dx in (-1.05, 0.0, 1.05)]
    wedges = [((xm + dx, sg * 1.33, zc + 0.36), (0.22, 0.06, 0.12), 0.0) for dx in (-1.1, -0.55, 0, 0.55, 1.1) for sg in (1, -1)]
    for o in (p4.boxes("hatchbars", bars, iron), p4.boxes("wedges", wedges, ship.wood("weathered_planks", 0.5, tint=(0.9, 0.7, 0.5), name="wedgewood"))):
        o.matrix_world = SHIP @ o.matrix_world
    if pumps == "found":
        PU.pump("pumpP", (px, 0.7, ship.zdeck(px)), intact=False, coll=pcoll)
        PU.dismantled_parts("pp", Matrix.Translation((px + 0.6, 1.3, ship.zdeck(px + 0.6) + 0.004)), coll=pcoll, grit=1.0)
    else:
        PU.pump("pumpP", (px, 0.7, ship.zdeck(px)), intact=pumps != "apart", coll=pcoll, brake_angle=-6)
        if pumps == "apart":
            PU.dismantled_parts("pp", Matrix.Translation((px + 0.6, 1.3, ship.zdeck(px + 0.6) + 0.004)), coll=pcoll, grit=1.0)
    for o in pcoll.all_objects:
        if o.parent is None:
            o.matrix_world = SHIP @ o.matrix_world
    if boat is None:
        boat = rail_gap is None            # before the evacuation the yawl is still on its chocks on the main hatch
    if boat:
        import skfab
        br, bms = skfab.model(YAWL, height=0.77, name="yawl")          # ~3.6 m yawl, sized to sit on the main hatch
        xm = ship.MAIN_HATCH_X
        br.matrix_world = SHIP @ Matrix.Translation((xm, 0, ship.zdeck(xm) + 0.755)) @ Matrix.Rotation(math.radians(90), 4, 'Z')
        out["yawl"] = br
    water = sea.water_material()
    sky_aid = {"day": sea.SKY, "dusk": "belfast_sunset_puresky", "night": "belfast_sunset_puresky", "dawn": "industrial_sunset_02_puresky"}[time]
    chop = {"day": 1.7, "dusk": 1.2, "night": 2.4, "dawn": 1.5}[time] * sea_k
    sea.ocean(size=240, res=24, scale=2.4 * sea_k, chop=chop, wind=15.0 * sea_k, repeat=3, foam=0.38 * sea_k, mat=water,
              direction=math.degrees(math.atan2(WIND.y, WIND.x)), hulls=(mc["hull"],), loc=(-150, -150, 0),
              cut=(0.0, 0.0, ship.L / 2 - 0.4, ship.B / 2 - 0.15))
    sea.far_sea(370, mat=water, center=(-150, -150))
    if time == "day":
        sea.sky(strength=1.0, rot_deg=60)
        _sun(150, 26, 1.4, (1.0, 0.94, 0.86), angle=5)
    elif time == "dusk":
        sea.sky(strength=0.9, rot_deg=250, aid=sky_aid)
        _sun(200, 8, 3.0, (1.0, 0.6, 0.32), angle=1.5)
    elif time == "night":
        sea.sky(strength=0.07, rot_deg=250, aid=sky_aid)
        _sun(120, 25, 0.12, (0.55, 0.65, 0.95), angle=3)          # moon through broken cloud
        warm_haze((0, 0, 4), (40, 20, 10), density=0.008, color=(0.8, 0.8, 0.85))
    elif time == "dawn":
        sea.sky(strength=0.7, rot_deg=90, aid=sky_aid)
        _sun(80, 4, 1.5, (1.0, 0.66, 0.45), angle=2)
    return out


def lantern_on_deck(SHIP, local, energy=60):
    ln, ms = ph.model("wooden_lantern_01"); p4.lamp_glass_passes(ms)
    ln.matrix_world = SHIP @ Matrix.Translation(local)
    p4.light('POINT', "deck_lantern", energy, (1.0, 0.58, 0.26), loc=SHIP @ (Vector(local) + Vector((0, 0, 0.2))), size=0.03)
    return ln


def santa_maria(dist_km=11.0, bearing_deg=200.0, z0=-0.5, origin=(0, 0)):
    """The island of Santa Maria (Azores) from real elevation at true scale, placed dist_km from origin on bearing
    (0 = +X / ship's bow). The eastern point is the closest. Returns the island object."""
    bbox = (-25.22, 36.92, -24.98, 37.02)
    e, lons, lats = T.grid(*bbox, zoom=12, out_w=520)
    lat_m = 111320.0; lon_m = 111320.0 * math.cos(math.radians(36.97))
    sx = (bbox[2] - bbox[0]) * lon_m; sy = (bbox[3] - bbox[1]) * lat_m
    e = e.clip(-30, None)
    land = p4.mat("island", (0.09, 0.1, 0.06), rough=0.9)
    o = T.relief_mesh("SantaMaria", e, sx, sy, 1.0, 1.0, mat=land)
    import bmesh                                   # keep only the land (and the beach just under the water)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if max(v.co.z for v in f.verts) < -2.0], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(o.data); bm.free()
    b = math.radians(bearing_deg)
    # eastern point (lon -25.01) placed at the given distance
    ex, ey = T.lonlat_to_map(-25.01, 36.96, bbox, (sx, sy))
    tgt = Vector((origin[0] + math.cos(b) * dist_km * 1000, origin[1] + math.sin(b) * dist_km * 1000, z0))
    o.location = tgt - Vector((ex, ey, 0))
    return o, (sx, sy)


# ============================================================================= THE TABLE (investigation, Atrium)
MAP_BBOX = (-28.6, 35.6, -15.6, 39.9)
LAST = (-24.98, 37.03)       # 25 Nov 1872, 8 a.m.: eastern point of Santa Maria bearing SSW, 6 miles
FOUND = (-17.25, 38.33)      # 5 Dec 1872 (sea time 4 Dec): 38 deg 20' N, 17 deg 15' W


def set_table(map_on=True, slate=True, papers=True):
    out = {}
    tbl = ship.wood("wood_table_large", 0.7, tint=(0.85, 0.6, 0.42), name="chart_table")
    ship.box("tabletop", (0, 0, 0.75), (3.2, 1.9, 0.06), tbl, bevel=0.01)
    for sx in (-1.45, 1.45):
        for sy in (-0.8, 0.8):
            ship.box("leg", (sx, sy, 0.36), (0.09, 0.09, 0.72), tbl)
    TZ = 0.78
    if map_on:
        e, lons, lats = T.grid(*MAP_BBOX, zoom=8, out_w=1100)
        SX = 2.2; SY = SX * e.shape[0] / e.shape[1]
        base = ship.wood("oak_veneer_01", 0.5, tint=(0.8, 0.6, 0.42), name="mapbase")
        ship.box("map_frame", (0, 0.1, TZ + 0.012), (SX + 0.08, SY + 0.08, 0.024), base, bevel=0.004)
        mo = T.relief_mesh("map", e, SX, SY, land_k=3.0e-5, sea_k=2.6e-6, mat=T.map_material(), skirt=0.0)
        MZ = TZ + 0.024 + 6200 * 2.6e-6 + 0.001
        mo.location = (0, 0.1, MZ)
        out.update(map=mo, SX=SX, SY=SY, e=e, lons=lons, lats=lats, mapz=MZ)

        def mp(lon, lat, lift=0.0):
            x, y = T.lonlat_to_map(lon, lat, MAP_BBOX, (SX, SY))
            h = T.height_at(e, lons, lats, lon, lat)
            return Vector((x, y + 0.1, MZ + (h * 2.6e-6 if h < 0 else h * 3.0e-5) + lift))
        out["mp"] = mp
        brass = p4.mat("brass", (0.72, 0.5, 0.22), rough=0.25, metal=1.0)
        red = p4.mat("pinhead", (0.5, 0.04, 0.02), rough=0.3)
        for nm, ll in (("last", LAST), ("found", FOUND)):
            p = mp(*ll)
            ship.cyl(f"pin_{nm}", p, p + Vector((0, 0, 0.07)), 0.0016, mat=brass, verts=10)
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.008, location=p + Vector((0, 0, 0.074)))
            bpy.context.active_object.data.materials.append(red); bpy.ops.object.shade_smooth()
            out[nm] = p
    if slate:
        sl = ship.paint("slate", (0.035, 0.038, 0.042), rough=0.85, grime=0.25, scale=30, under=(0.2, 0.2, 0.2))
        fr = ship.wood("oak_veneer_01", 0.3, tint=(0.85, 0.62, 0.42), name="slateframe")
        c = Vector((-1.05, -0.62, TZ + 0.012))
        ship.box("slate", c, (0.42, 0.3, 0.008), sl)
        for sy in (-1, 1):
            ship.box("slf", c + Vector((0, sy * 0.16, 0.002)), (0.46, 0.025, 0.014), fr)
            ship.box("slf", c + Vector((sy * 0.22, 0, 0.002)), (0.025, 0.34, 0.014), fr)
        out["slate"] = c
    if papers:
        pap = p4.mat("paper", (0.78, 0.68, 0.5), rough=0.8)
        rng = random.Random(2)
        for k in range(5):
            ship.box("paper", (1.15 + rng.uniform(-0.1, 0.1), -0.55 + rng.uniform(-0.1, 0.1), TZ + 0.002 + k * 0.0015),
                     (0.21, 0.297, 0.001), pap, rot=(0, 0, rng.uniform(-0.3, 0.3)))
        cp, cms = ph.model("seadogs_compass")
        cp.matrix_world = Matrix.Translation((0.95, 0.62, TZ)) @ Matrix.Rotation(0.4, 4, 'Z') @ Matrix.Diagonal((1.5, 1.5, 1.5, 1))
    lamp, lms = ph.model("vintage_oil_lamp"); p4.lamp_glass_passes(lms)
    lamp.location = (1.3, 0.62, TZ)
    p4.light('POINT', "lampflame", 22, (1.0, 0.6, 0.3), loc=(1.3, 0.62, TZ + 0.42), size=0.02)
    p4.light('SPOT', "key", 420, (1.0, 0.74, 0.48), loc=(0.6, 0.4, 2.6), target=(-0.1, 0.05, TZ), size=0.25, spot=60, blend=0.7)
    p4.light('AREA', "rim", 80, (0.9, 0.7, 0.5), loc=(-1.8, 1.8, 1.4), target=(0, 0, TZ), size=1.5)
    p4.world_color((0.008, 0.005, 0.004))
    # the room: dark panelling behind, out of focus
    walls = ship.wood("dark_wooden_planks", 1.2, tint=(0.6, 0.42, 0.3), name="room")
    ship.box("wall_back", (0, 2.6, 1.6), (8, 0.1, 3.2), walls)
    ship.box("floor", (0, 0, -0.01), (8, 8, 0.02), walls)
    warm_haze((0, 0, 1.3), (6, 6, 2.6), density=0.015, color=(1.0, 0.85, 0.7))
    out["TZ"] = TZ
    return out


def slate_text(c, lines, size=0.018):
    """Chalk writing on the slate, as text objects lying on it."""
    chalk = p4.mat("chalktext", (0.82, 0.82, 0.78), rough=0.95)
    fnt = os.path.join(p4.ROOT, "mary_celeste_p4", "assets", "fonts", "InstrumentSerifItalic.ttf")
    objs = []
    for k, ln in enumerate(lines):
        cu = bpy.data.curves.new("txt", 'FONT'); cu.body = ln; cu.size = size
        if os.path.exists(fnt):
            cu.font = bpy.data.fonts.load(fnt, check_existing=True)
        o = bpy.data.objects.new("slate_txt", cu); bpy.context.scene.collection.objects.link(o)
        o.location = c + Vector((-0.185, 0.1 - k * size * 1.6, 0.0045)); o.data.materials.append(chalk)
        objs.append(o)
    return objs
