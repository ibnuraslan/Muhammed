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
PARCEL = Vector((0.02, -0.17, TABLE_Z))              # where the parcel lies (front of the clerk)
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
    ship.box("dl_window", (-4.14, -0.3, 2.2), (0.02, 0.8, 1.3), p4.mat("dl_night", (0.0, 0.0, 0.0), emit=(0.01, 0.016, 0.03), strength=0.6))
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
    p4.light('POINT', "dl_lamp", 140, (1.0, 0.62, 0.3), loc=(loc[0], loc[1], loc[2] + 0.62 * 0.5), size=0.03)
    # the gas bracket over the far end of the table (off screen), turned low
    p4.light('AREA', "dl_gas", 60, (1.0, 0.7, 0.42), loc=(1.8, -0.6, 2.4), target=(0.3, 0.2, 0.9), size=0.6)
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
    # opened: the brown paper unwrapped and spread flat on the table under the open box (a real crinkled sheet)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=50, y_subdivisions=40, size=1, location=c + Vector((0, 0, 0.0012)))
    sh = bpy.context.active_object; sh.name = "parcel_paper_open"; sh.scale = (w + 2 * h + 0.12, d + 2 * h + 0.1, 1)
    bpy.ops.object.transform_apply(scale=True)
    tx = bpy.data.textures.new("paper_crinkle", 'VORONOI'); tx.noise_scale = 0.05
    dm = sh.modifiers.new("crinkle", "DISPLACE"); dm.texture = tx; dm.strength = 0.003; dm.mid_level = 0.0
    sh.data.materials.append(g["kraft"]); out.append(sh)
    box.hide_render = True; box.hide_viewport = True
    cb = p4.mat("parcel_card", (0.42, 0.3, 0.18), 0.85)
    out.append(ship.box("parcel_base", c + Vector((0, 0, 0.0042)), (w - 0.006, d - 0.006, 0.003), cb))
    for sx in (-1, 1):
        out.append(ship.box("parcel_wall", c + Vector((sx * (w / 2 - 0.0045), 0, h / 2 + 0.003)), (0.003, d - 0.006, h - 0.004), cb))
    for sy in (-1, 1):
        out.append(ship.box("parcel_wall", c + Vector((0, sy * (d / 2 - 0.0045), h / 2 + 0.003)), (w - 0.012, 0.003, h - 0.004), cb))
    # the cut string lying loose
    out.append(ship.rope("parcel_string_cut", [c + Vector((0.18, -0.12, 0.0016)), c + Vector((0.24, -0.1, 0.0016)), c + Vector((0.27, -0.16, 0.0016))], 0.0015, g["string"]))
    # tissue: a crinkled sheet inside the box, over its rim
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=44, size=1, location=c + Vector((0, 0, h - 0.012)))
    ts = bpy.context.active_object; ts.name = "parcel_tissue"; ts.scale = (w * 0.98, d * 0.98, 1)
    bpy.ops.object.transform_apply(scale=True)
    tx = bpy.data.textures.new("tissue_crinkle", 'CLOUDS'); tx.noise_scale = 0.02; tx.noise_depth = 3
    sub = ts.modifiers.new("sub", "SUBSURF"); sub.levels = sub.render_levels = 2
    dm = ts.modifiers.new("crinkle", "DISPLACE"); dm.texture = tx; dm.strength = 0.004; dm.mid_level = 0.0
    sm = ts.modifiers.new("smooth", "SMOOTH"); sm.iterations = 4; sm.factor = 0.8
    ts.data.materials.append(g["tissue"]); out.append(ts)
    for p_ in ts.data.polygons:
        p_.use_smooth = True
    # the card: real cotton board, 1.2 mm, bevelled, the logo letterpressed
    M = Matrix.Translation(c + Vector((0.0, 0.0, h - 0.004))) @ Matrix.Rotation(0.06, 4, 'Z')
    card = si.plate("seldom_card", M, CARD_W, thick=0.0012, mat=si.paper_print_material("card_print"), margin=0.1, screws=0,
                    h=CARD_W * 0.62)
    out += card
    return out, M


def group(name, objs, origin):
    """Parent objects to an empty at `origin` (world), keeping their placement; returns the empty."""
    e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e)
    e.matrix_world = Matrix.Translation(origin)
    bpy.context.view_layer.update()
    for o in objs:
        mw = o.matrix_world.copy(); o.parent = e; o.matrix_parent_inverse = e.matrix_world.inverted(); o.matrix_world = mw
    return e


def closed_parcel(g):
    """The parcel as one movable group (root at its bottom centre); returns (root, strings, loose cut ends)."""
    objs = parcel(g, cut=False)
    strings = [o for o in objs if o.name.startswith("parcel_string")]
    c = PARCEL
    loose = [ship.rope("parcel_string_loose", [c + Vector((0.13, 0.0, 0.071)), c + Vector((0.17, -0.03, 0.06)), c + Vector((0.2, -0.05, 0.03)),
                                                c + Vector((0.21, -0.06, 0.0016))], 0.0015, g["string"]),
             ship.rope("parcel_string_loose", [c + Vector((-0.02, -0.086, 0.071)), c + Vector((-0.04, -0.12, 0.04)), c + Vector((-0.05, -0.15, 0.0016))],
                       0.0015, g["string"])]
    root = group("parcel_root", objs + loose, c)
    return root, strings, loose


def scissors(g):
    """Steel scissors (two blades on a pivot, bow handles), as a group; local +X = blade tips, origin = the bows."""
    st = p4.mat("scissor_steel", (0.55, 0.55, 0.56), rough=0.25, metal=1.0)
    parts = []
    for sg in (1, -1):
        parts.append(ship.box("scissor_blade", (0.09, sg * 0.003, 0.0), (0.11, 0.008, 0.0016), st, rot=(0, 0, sg * 0.06)))
        bpy.ops.mesh.primitive_torus_add(major_radius=0.012, minor_radius=0.0025, location=(0.0, sg * 0.014, 0.0))
        o = bpy.context.active_object; o.name = "scissor_bow"; o.data.materials.append(st); parts.append(o)
    parts.append(ship.cyl("scissor_pivot", (0.035, 0, -0.002), (0.035, 0, 0.002), 0.003, mat=st, verts=12))
    return group("scissors", parts, Vector((0, 0, 0)))


def build(shot, t, out):
    E = si.ease
    si.C.render_setup(samples=64, noise=0.03, bounces=8)
    g = mats(); room(g); envelopes(g)
    lamp((-0.55, 0.22, TABLE_Z))
    pos = (0.12, -TABLE[1] / 2 - 0.22)          # she stands at the front edge, facing the pigeon-holes (+Y)
    face = 90
    look = (0.15, 0.0, TABLE_Z)
    if shot == "A":
        def stamping(h, dv, M, Mi):
            lift = 0.10 * abs(math.sin(math.pi * 2.0 * si.T * 1.5))            # the stamping rhythm, 3 strokes
            P.stand(h, lean=5, weight="L", twist=-3)
            P.head(h, pitch=38, yaw=-6, tilt=2)
            dv.lids(0.55); dv.brow_knit(0.2)
            P.hand_reach(h, "R", Mi @ Vector((0.18 + pos[0] - 0.12, -0.02, TABLE_Z + 0.06 + lift)), elbow=(-0.7, 0.4, -0.6), hand_dir=Vector((0, -0.25, -1)))
            P.grip(h, "R", 1.0)
            P.hand_reach(h, "L", Mi @ Vector((-0.18, -0.05, TABLE_Z + 0.035)), elbow=(0.7, 0.4, -0.5), hand_dir=Vector((-0.1, -0.9, -0.4)))
            P.rest_hand(h, "L", curl=28)
        dv, M = si.person("sarah", pos, face, stamping, look)
        stp, _ = stamp_prop(Matrix())

        @si.dyn
        def _(tt, frame):
            if dv is not None:
                si.place(stp, Matrix.Translation(si.hand(dv, M, "R") - Vector((0, 0, 0.085))) @ Matrix.Rotation(0.3, 4, 'Z'), frame)
        parcel(g)
        c = Vector((-2.6, -3.3, 2.9)) + Vector((0.3, 0.2, -0.1)) * E(t)          # wide, high angle
        si.cam(c, (0.0, 0.3, 1.2), lens=28, fstop=5.6)
    elif shot == "B":
        def held(T):
            """She lifts it off the table (to 0.4), then turns it over in her hands looking for an address."""
            u = si.ease(min(1.0, T / 0.4))
            ctr = PARCEL.lerp(Vector((pos[0], -0.32, TABLE_Z + 0.235)), u)
            rot = 0.25 * u + 0.5 * si.ease(max(0.0, (T - 0.45) / 0.55))
            return ctr, rot

        def lift_parcel(h, dv, M, Mi):
            ctr, rot = held(si.T)
            P.stand(h, lean=6, weight="R", twist=2); P.head(h, pitch=22 + 14 * (1 - min(1.0, si.T / 0.4)), yaw=0, tilt=-4)
            dv.lids(0.3); dv.brow_knit(0.4 + 0.6 * min(1.0, si.T / 0.5))
            R = Matrix.Rotation(rot, 3, 'Z')
            for s_, dx in (("L", -0.11), ("R", 0.11)):
                sg = H.SIDE[s_]
                pw = ctr + R @ Vector((dx * 1.15, 0, 0.035))
                P.hand_reach(h, s_, Mi @ (pw + R @ Vector((sg * 0.035, 0, 0.0))), elbow=(0.8 * sg, 0.3, -0.6), hand_dir=Vector((-0.5 * sg, -0.35, 0.1)))
                P.grip(h, s_, 0.45)                            # fingers wrap the parcel's sides
        dv, M = si.person("sarah", pos, face, lift_parcel, (pos[0], -0.32, TABLE_Z + 0.3))
        root, strings, loose = closed_parcel(g)
        for o in loose:
            o.hide_render = True

        @si.dyn
        def _(tt, frame):
            ctr, rot = held(tt)
            si.place(root, Matrix.Translation(ctr) @ Matrix.Rotation(rot, 4, 'Z'), frame)
        c = Vector((0.95, 0.95, 1.42))                                         # medium, across the table, side-lit
        si.cam(c, (pos[0] - 0.05, pos[1] + 0.05, 1.22), lens=40, fstop=2.8)
    elif shot == "C":
        TCUT = 0.55
        knot = PARCEL + Vector((0.0, 0.0, 0.072))

        def cutting(h, dv, M, Mi):
            u = si.ease(min(1.0, si.T / TCUT))                                # the blades come in to the knot and close
            P.stand(h, lean=5, weight="L", twist=0); P.head(h, pitch=45, yaw=0, tilt=0)
            dv.lids(0.6); dv.brow_knit(0.7)
            P.hand_reach(h, "L", Mi @ (PARCEL + Vector((-0.09, -0.02, 0.08))), elbow=(0.7, 0.3, -0.6), hand_dir=Vector((0.3, -0.5, -0.8)))
            P.rest_hand(h, "L", curl=18)
            hw = knot + Vector((0.2 - 0.1 * u, -0.1 + 0.03 * u, 0.06 - 0.03 * u))
            if si.T > TCUT:                                                  # after the snip: the hand draws back
                hw = hw + Vector((0.05, -0.04, 0.03)) * si.ease(min(1.0, (si.T - TCUT) / 0.3))
            P.hand_reach(h, "R", Mi @ hw, elbow=(-0.7, 0.3, -0.6), hand_dir=Vector((-0.4, 0.2, -0.6)))
            P.grip(h, "R", 0.7)
        dv, M = si.person("sarah", pos, face, cutting, PARCEL)
        root, strings, loose = closed_parcel(g)
        sc_ = scissors(g)

        @si.dyn
        def _(tt, frame):
            cut = tt > TCUT
            for o in strings:
                o.hide_render = cut; si.key(o, "hide_render", frame=frame)
            for o in loose:
                o.hide_render = not cut; si.key(o, "hide_render", frame=frame)
            if dv is not None:
                hp = si.hand(dv, M, "R")
                aim = (knot - hp); aim.z = 0
                q = aim.to_track_quat('X', 'Z')
                si.place(sc_, Matrix.Translation(hp + Vector((0, 0, -0.01))) @ q.to_matrix().to_4x4(), frame)
        c = Vector((pos[0] + 0.36, pos[1] - 0.12, 1.66)) + Vector((-0.03, 0.05, -0.04)) * E(t)   # over her right shoulder
        si.cam(c, PARCEL + Vector((0.03, 0, 0.04)), lens=40, fstop=2.8)
    elif shot in ("D", "LOGO"):
        res = parcel(g, opened=1.0)
        cardM = res[1]
        if shot == "D":
            def frozen(h, dv, M, Mi):
                u = si.ease(min(1.0, si.T / 0.35))                            # the stamp hand stops, held up
                P.stand(h, lean=4, weight="L", twist=-3); P.head(h, pitch=40, yaw=-4, tilt=2)
                dv.lids(0.4); dv.brow_knit(0.0)
                P.hand_reach(h, "R", Mi @ Vector((0.42, -0.25, TABLE_Z + 0.12 + 0.12 * u)), elbow=(-0.7, 0.4, -0.6), hand_dir=Vector((0, -0.3, -1)))
                P.grip(h, "R", 1.0)
                P.hand_reach(h, "L", Mi @ Vector((pos[0] - 0.24, -TABLE[1] / 2 + 0.1, TABLE_Z + 0.03)), elbow=(0.7, 0.4, -0.5), hand_dir=Vector((-0.1, -0.9, -0.4)))
                P.rest_hand(h, "L", curl=30)
            dv, M = si.person("sarah", pos, face, frozen, PARCEL)
            stp, _ = stamp_prop(Matrix())

            @si.dyn
            def _(tt, frame):
                if dv is not None:
                    si.place(stp, Matrix.Translation(si.hand(dv, M, "R") - Vector((0, 0, 0.085))) @ Matrix.Rotation(0.3, 4, 'Z'), frame)
            c = Vector((-0.28, -0.98, 1.78)); si.cam(c, PARCEL + Vector((0.06, 0.0, 0.03)), lens=42, fstop=4.0,
                                                             focus=(c - PARCEL).length)
        else:
            tgt = cardM @ Vector((0, 0, 0)); c = tgt + Vector((0.0, -0.02, 0.38))
            p4.light('AREA', "check_key", 4, (1.0, 0.97, 0.92), loc=tgt + Vector((0.3, -0.3, 0.5)), target=tgt, size=0.5)
            si.cam(c, tgt, lens=60, fstop=8.0)
    si.finish(out, sat=1.08, bloom=0.4, clip_ok=("stamp", "parcel", "dl_env", "dl_table", "card", "tissue", "scissor"))
