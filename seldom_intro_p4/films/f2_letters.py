"""Film 2 - DEAD LETTERS (11 s). A dead-letter office after midnight (1870s). The clerk stamps letters RETURN TO
SENDER under one lamp; a parcel has no address at all; she cuts the string, folds back the paper: on tissue lies
a letterpress card. Her stamp hand stops in the air. HOLD.

    blender -b -P films/run.py -- f2 <A|B|C|D|LOGO> [t] [out.png]
"""
import math, random
import bpy
from mathutils import Vector, Matrix
import si, p4, ship, ph, skfab, poses as P, human as H, deveau as D

STAMP_UID = "be402a8d73c74fd6b9ca5acc057a208d"       # "Old Victorian Rubber Stamp" (CC BY)
TABLE_Z = 0.80
TABLE = (3.2, 0.95)                                  # long sorting table, along X, centred at origin
SHOTS = dict(A=(0.0, 3.0), B=(3.0, 6.0), C=(6.0, 9.0), D=(9.0, 11.0))
PARCEL = Vector((0.02, -0.05, TABLE_Z))              # where the parcel lies (front of the clerk)
CARD_W = 0.15


def mats():
    g = {}
    g["oak"] = ship.wood("oak_veneer_01", 1.2, tint=(0.9, 0.62, 0.38), name="dl_oak")
    g["dark_oak"] = ship.wood("dark_wooden_planks", 1.5, tint=(0.7, 0.45, 0.3), name="dl_pigeon")
    g["floor"] = ship.wood("brown_planks_05", 1.6, tint=(0.7, 0.5, 0.35), name="dl_floor")
    g["wall"] = p4.mat("dl_wall", (0.16, 0.1, 0.06), rough=0.85)
    g["paper"] = p4.mat("dl_paper", (0.72, 0.66, 0.55), rough=0.85)
    g["paper2"] = p4.mat("dl_paper2", (0.62, 0.55, 0.43), rough=0.88)
    g["kraft"] = kraft()
    g["string"] = p4.mat("dl_string", (0.5, 0.42, 0.3), rough=0.95)
    g["ink"] = p4.mat("dl_ink", (0.25, 0.02, 0.02), rough=0.5)
    g["tissue"] = p4.mat("dl_tissue", (0.85, 0.83, 0.78), rough=0.9)
    g["tissue"].node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 0.3
    g["brass"] = D.brass_material("dl_brass")
    return g


def kraft():
    m = bpy.data.materials.new("dl_kraft"); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.36, 0.22, 0.11, 1); b.inputs["Roughness"].default_value = 0.8
    tc = nt.nodes.new("ShaderNodeTexCoord")
    w = nt.nodes.new("ShaderNodeTexWave"); w.inputs["Scale"].default_value = 30; w.inputs["Distortion"].default_value = 8
    nt.links.new(tc.outputs["Object"], w.inputs["Vector"])
    bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = 0.12
    nt.links.new(w.outputs["Fac"], bm.inputs["Height"]); nt.links.new(bm.outputs["Normal"], b.inputs["Normal"])
    return m


def room(g):
    ship.box("dl_floor", (0, 0.6, -0.02), (9, 8, 0.04), g["floor"])
    ship.box("dl_backwall", (0, 1.9, 2.5), (9, 0.1, 5), g["wall"])
    ship.box("dl_sidewall", (-4.2, 0.6, 2.5), (0.1, 8, 5), g["wall"])
    # the table
    tw, td = TABLE
    ship.box("dl_table_top", (0, 0, TABLE_Z - 0.025), (tw, td, 0.05), g["oak"], bevel=0.006)
    for sx in (-1, 1):
        for sy in (-1, 1):
            ship.box("dl_table_leg", (sx * (tw / 2 - 0.08), sy * (td / 2 - 0.08), (TABLE_Z - 0.05) / 2), (0.08, 0.08, TABLE_Z - 0.05), g["oak"], bevel=0.004)
    ship.box("dl_table_apron", (0, td / 2 - 0.06, TABLE_Z - 0.12), (tw - 0.2, 0.025, 0.14), g["oak"])
    # pigeon-hole wall behind the table: towering, dozens of cells, letters in most
    rng = random.Random(3)
    cols, rows = 26, 18; cw, ch = 0.26, 0.2; depth = 0.32; x0 = -cols * cw / 2; y0 = 1.85 - depth / 2
    items = []
    for i in range(cols + 1):
        items.append(((x0 + i * cw, y0, rows * ch / 2 + 0.6), (0.015, depth, rows * ch), 0))
    for j in range(rows + 1):
        items.append(((0, y0, 0.6 + j * ch), (cols * cw, depth, 0.015), 0))
    items.append(((0, y0 + depth / 2, rows * ch / 2 + 0.6), (cols * cw, 0.01, rows * ch), 0))
    p4.boxes("dl_pigeonholes", items, g["dark_oak"])
    letters = []; letters2 = []
    for i in range(cols):
        for j in range(rows):
            if rng.random() < 0.25:
                continue
            n = rng.randint(1, 6)
            for k in range(n):
                cx = x0 + (i + 0.5) * cw + rng.uniform(-0.06, 0.06)
                lw = rng.uniform(0.14, 0.2); lh = rng.uniform(0.09, 0.12)
                z = 0.6 + j * ch + 0.0075 + lh / 2 + 0.002
                lean = rng.uniform(-0.15, 0.15)
                (letters if rng.random() < 0.6 else letters2).append(((cx, y0 - depth / 2 + 0.04 + k * 0.012, z), (lw, 0.004, lh), lean * 0.2))
    p4.boxes("dl_letters", letters, g["paper"]); p4.boxes("dl_letters2", letters2, g["paper2"])
    # window behind her on the side wall: night, rain
    ship.box("dl_window", (-4.14, -0.3, 2.2), (0.02, 1.0, 1.6), p4.mat("dl_night", (0.0, 0.0, 0.0), emit=(0.02, 0.035, 0.06), strength=1.0))
    p4.world_color((0.001, 0.0012, 0.002))


def lamp(loc):
    r, ms = ph.model("vintage_oil_lamp")
    r.location = loc; r.scale = (0.62, 0.62, 0.62)
    for o in ms:
        if "glass" in o.name or "flame" in o.name:
            o.visible_shadow = False
    # a green glass shade over the chimney (a student-lamp shade): a real glass cone, cased white inside
    sh = bpy.data.materials.new("dl_shade"); sh.use_nodes = True; b = sh.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.02, 0.16, 0.06, 1); b.inputs["Roughness"].default_value = 0.08
    b.inputs["Coat Weight"].default_value = 1.0
    z = loc[2] + 0.62 * 0.62
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.17, radius2=0.05, depth=0.12, location=(loc[0], loc[1], z), end_fill_type='NOTHING')
    c = bpy.context.active_object; c.name = "dl_lampshade"; c.data.materials.append(sh)
    c.modifiers.new("s", "SOLIDIFY").thickness = 0.003
    bpy.ops.object.shade_smooth()
    p4.light('POINT', "dl_lamp", 55, (1.0, 0.62, 0.3), loc=(loc[0], loc[1], loc[2] + 0.62 * 0.5), size=0.03)
    return r


def envelopes(g, n=70, area=((-1.2, -0.5), (-0.25, 0.3)), seed=5):
    rng = random.Random(seed); items = []; items2 = []
    for k in range(n):
        x = rng.uniform(*area[0]); y = rng.uniform(*area[1])
        st = rng.randint(0, 4)
        (items if rng.random() < 0.6 else items2).append(((x, y, TABLE_Z + 0.002 + 0.003 * st), (0.16, 0.1, 0.0025), rng.uniform(-0.3, 0.3)))
    # a squared stack at her left
    for k in range(40):
        items.append(((0.55 + rng.uniform(-0.003, 0.003), -0.12, TABLE_Z + 0.0015 + k * 0.0028), (0.16, 0.1, 0.0025), rng.uniform(-0.03, 0.03)))
    p4.boxes("dl_env", items, g["paper"]); p4.boxes("dl_env2", items2, g["paper2"])


def stamp_prop(M):
    r, ms = skfab.model(STAMP_UID, height=0.11, name="stamp")
    r.matrix_world = M
    return r, ms


def parcel(g, opened=0.0, cut=False):
    """A small parcel, brown paper and string, no address. opened 0..1 folds the paper back to show tissue + card."""
    c = PARCEL; w, d, h = 0.24, 0.17, 0.07
    out = []
    box = ship.box("parcel_box", c + Vector((0, 0, h / 2)), (w - 0.006, d - 0.006, h - 0.004), p4.mat("parcel_card", (0.42, 0.3, 0.18), 0.85))
    out.append(box)
    if opened <= 0.0:
        out.append(ship.box("parcel_paper", c + Vector((0, 0, h / 2)), (w, d, h), g["kraft"], bevel=0.004))
        if not cut:
            out.append(ship.rope("parcel_string", [c + Vector((-w / 2 - 0.001, 0, h + 0.002)) + Vector((0, 0, 0)), c + Vector((w / 2 + 0.001, 0, h + 0.002))], 0.0015, g["string"]))
            out.append(ship.rope("parcel_string", [c + Vector((0, -d / 2 - 0.001, h + 0.002)), c + Vector((0, d / 2 + 0.001, h + 0.002))], 0.0015, g["string"]))
            for s in (-1, 1):
                out.append(ship.rope("parcel_string", [c + Vector((s * (w / 2 + 0.0015), 0, h + 0.001)), c + Vector((s * (w / 2 + 0.0015), 0, 0.001))], 0.0015, g["string"]))
                out.append(ship.rope("parcel_string", [c + Vector((0, s * (d / 2 + 0.0015), h + 0.001)), c + Vector((0, s * (d / 2 + 0.0015), 0.001))], 0.0015, g["string"]))
        return out
    # opened: the box's lid is off; paper flaps folded back flat-ish onto the table (each flap a real thin sheet)
    ang = math.radians(100 * opened)
    for sx, sy, fw, fd in ((1, 0, d, 0.12), (-1, 0, d, 0.12), (0, 1, w, 0.1), (0, -1, w, 0.1)):
        hinge = c + Vector((sx * w / 2, sy * d / 2, h))
        o = ship.box("parcel_flap", (0, 0, 0), (fd, fw, 0.0008) if sx else (fw, fd, 0.0008), g["kraft"])
        if sx:
            o.matrix_world = Matrix.Translation(hinge) @ Matrix.Rotation(-sx * ang, 4, 'Y') @ Matrix.Translation((sx * fd / 2, 0, 0))
        else:
            o.matrix_world = Matrix.Translation(hinge) @ Matrix.Rotation(sy * ang, 4, 'X') @ Matrix.Translation((0, sy * fd / 2, 0))
        out.append(o)
    # the cut string lying loose
    out.append(ship.rope("parcel_string_cut", [c + Vector((0.18, -0.12, 0.0016)), c + Vector((0.24, -0.1, 0.0016)), c + Vector((0.27, -0.16, 0.0016))], 0.0015, g["string"]))
    # tissue: a crinkled sheet inside the box, over its rim
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=44, size=1, location=c + Vector((0, 0, h - 0.006)))
    ts = bpy.context.active_object; ts.name = "parcel_tissue"; ts.scale = (w * 0.98, d * 0.98, 1)
    bpy.ops.object.transform_apply(scale=True)
    tx = bpy.data.textures.new("tissue_crinkle", 'VORONOI'); tx.noise_scale = 0.012
    dm = ts.modifiers.new("crinkle", "DISPLACE"); dm.texture = tx; dm.strength = 0.004; dm.mid_level = 0.0
    ts.data.materials.append(g["tissue"]); out.append(ts)
    # the card: real cotton board, 1.2 mm, bevelled, the logo letterpressed
    M = Matrix.Translation(c + Vector((0.0, 0.0, h - 0.0015))) @ Matrix.Rotation(0.06, 4, 'Z')
    card = si.plate("seldom_card", M, CARD_W, thick=0.0012, mat=si.paper_print_material("card_print"), margin=0.1, screws=0,
                    h=CARD_W * 0.62)
    out += card
    return out, M


def pose_stamp(phase, lift):
    """Standing at the table, leaning in; right hand holds the stamp (up `lift` m), left hand flat on the letters."""
    def f(h, dv, M, Mi):
        P.stand(h, lean=16, weight="L", twist=-3)
        P.head(h, pitch=30, yaw=-6, tilt=2)
        dv.lids(0.55); dv.brow_knit(0.2)
        tgt = Mi @ Vector((0.18, -0.02, TABLE_Z + 0.06 + lift))
        P.hand_reach(h, "R", tgt, elbow=(-0.7, 0.4, -0.6), hand_dir=Vector((0, -0.25, -1)))
        P.grip(h, "R", 1.0)
        tl = Mi @ Vector((-0.18, -0.05, TABLE_Z + 0.035))
        P.hand_reach(h, "L", tl, elbow=(0.7, 0.4, -0.5), hand_dir=Vector((-0.1, -0.9, -0.4)))
        P.rest_hand(h, "L", curl=12)
    return f


def build(shot, t, out):
    E = si.ease
    si.C.render_setup(samples=64, noise=0.03, bounces=8)
    g = mats(); room(g); envelopes(g)
    lamp((-0.55, 0.22, TABLE_Z))
    # her place: behind the table (+Y side), facing -Y toward camera side? No: she faces +Y? She stands at the
    # front edge (-Y), facing the pigeon-holes behind the table (+Y).
    pos = (0.12, -TABLE[1] / 2 - 0.28)
    face = 90
    look = (0.15, 0.0, TABLE_Z)
    if shot == "A":
        lift = 0.10 * abs(math.sin(math.pi * 2.0 * t))                 # stamping rhythm
        dv, M = si.person("sarah", pos, face, pose_stamp(t, lift), look, shawl=True)
        stamp_prop(Matrix.Translation(Vector((0.18 + pos[0], -0.02, TABLE_Z + 0.004 + lift))) @ Matrix.Rotation(0.3, 4, 'Z'))
        parcel(g)
        c = Vector((-2.6, -3.3, 2.9)) + Vector((0.3, 0.2, -0.1)) * E(t)          # wide, high angle
        si.cam(c, (0.0, 0.3, 1.2), lens=28, fstop=5.6)
    elif shot == "B":
        def lift_parcel(h, dv, M, Mi):
            P.stand(h, lean=6, weight="R", twist=2); P.head(h, pitch=22, yaw=0, tilt=-4)
            dv.lids(0.3); dv.brow_knit(1.0)
            for s, dx in (("L", -0.11), ("R", 0.11)):
                sg = H.SIDE[s]
                P.hand_reach(h, s, Mi @ (Vector((pos[0] + dx * 1.15, -0.32, TABLE_Z + 0.27))), elbow=(0.8 * sg, 0.3, -0.6),
                             hand_dir=Vector((-0.6 * sg, -0.3, 0.2)))
                P.rest_hand(h, s, curl=30)
        dv, M = si.person("sarah", pos, face, lift_parcel, (pos[0], -0.32, TABLE_Z + 0.3))
        # the parcel held between her palms, turned a little
        PAR = Vector((pos[0], -0.32, TABLE_Z + 0.27 - 0.035))
        globals()["PARCEL"] = PAR
        ps = parcel(g)
        for o in ps:
            o.matrix_world = Matrix.Translation(PAR) @ Matrix.Rotation(0.25, 4, 'Z') @ Matrix.Translation(-PAR) @ o.matrix_world
        globals()["PARCEL"] = Vector((0.02, -0.05, TABLE_Z))
        c = Vector((pos[0] + 1.35, pos[1] - 0.55, 1.45))                       # medium, side-lit, at her side
        si.cam(c, (pos[0] - 0.05, pos[1] + 0.05, 1.25), lens=45, fstop=2.8)
    elif shot == "C":
        cut = t > 0.3
        def cutting(h, dv, M, Mi):
            P.stand(h, lean=24, weight="L", twist=0); P.head(h, pitch=38, yaw=0, tilt=0)
            dv.lids(0.6); dv.brow_knit(0.7)
            P.hand_reach(h, "L", Mi @ (PARCEL + Vector((-0.09, -0.02, 0.08))), elbow=(0.7, 0.3, -0.6), hand_dir=Vector((0.3, -0.5, -0.8)))
            P.rest_hand(h, "L", curl=18)
            P.hand_reach(h, "R", Mi @ (PARCEL + Vector((0.1, -0.06, 0.09))), elbow=(-0.7, 0.3, -0.6), hand_dir=Vector((-0.4, 0.2, -0.6)))
            P.grip(h, "R", 0.7)
        dv, M = si.person("sarah", pos, face, cutting, PARCEL)
        if E(t) < 0.6:
            parcel(g, cut=cut)
        else:
            parcel(g, opened=(E(t) - 0.6) / 0.4)
        c = Vector((pos[0] + 0.45, pos[1] - 0.25, 1.38)) + Vector((-0.05, 0.08, -0.05)) * E(t)   # over her right shoulder
        si.cam(c, PARCEL + Vector((0, 0, 0.04)), lens=50, fstop=2.8)
    elif shot in ("D", "LOGO"):
        res = parcel(g, opened=1.0)
        cardM = res[1]
        if shot == "D":
            def frozen(h, dv, M, Mi):
                P.stand(h, lean=14, weight="L", twist=-3); P.head(h, pitch=34, yaw=-4, tilt=2)
                dv.lids(0.4); dv.brow_knit(0.0)
                P.hand_reach(h, "R", Mi @ Vector((0.42, -0.25, TABLE_Z + 0.24)), elbow=(-0.7, 0.4, -0.6), hand_dir=Vector((0, -0.3, -1)))
                P.grip(h, "R", 1.0)
                P.hand_reach(h, "L", Mi @ (PARCEL + Vector((-0.16, -0.06, 0.03))), elbow=(0.7, 0.4, -0.5), hand_dir=Vector((0.2, -0.9, -0.3)))
                P.rest_hand(h, "L", curl=10)
            dv, M = si.person("sarah", pos, face, frozen, PARCEL)
            stamp_prop(Matrix.Translation(Vector((0.42, -0.25, TABLE_Z + 0.24 - 0.065))) @ Matrix.Rotation(0.3, 4, 'Z'))
            c = PARCEL + Vector((0.0, 0.12, 1.25)); si.cam(c, PARCEL + Vector((0, -0.12, 0)), lens=30, fstop=4.0,
                                                          focus=(c - PARCEL).length, roll=180)
        else:
            tgt = cardM @ Vector((0, 0, 0)); c = tgt + Vector((0.0, -0.02, 0.38))
            p4.light('AREA', "check_key", 4, (1.0, 0.97, 0.92), loc=tgt + Vector((0.3, -0.3, 0.5)), target=tgt, size=0.5)
            si.cam(c, tgt, lens=60, fstop=8.0)
    si.finish(out, sat=1.08, bloom=0.4, clip_ok=("stamp", "parcel", "dl_env", "dl_table", "card", "tissue"))
