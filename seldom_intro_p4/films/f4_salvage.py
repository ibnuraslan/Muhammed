"""Film 4 - SALVAGE (12 s). Grey dawn on a harbour. A dockside crane lifts a crate out of the black water; a
stevedore steadies it with a boathook, sets it down on the quay stones and wipes the mud off its side with his
sleeve: under the mud, the stencilled word. He looks back at the water. HOLD.

    blender -b -P films/run.py -- f4 <A|B|C|D|LOGO> [t] [out.png]
"""
import math, random
import bpy
from mathutils import Vector, Matrix
import si, p4, ship, ph, sea, poses as P, human as H, deveau as D

QUAY_Z = 1.6                    # quay top above the water
EDGE_Y = 0.0                    # quay edge (water at y < 0)
CW, CD, CH = 0.9, 0.62, 0.6     # crate
CRANE = Vector((-1.6, 1.4, QUAY_Z))
SHOTS = dict(A=(0.0, 3.0), B=(3.0, 6.0), C=(6.0, 9.5), D=(9.5, 12.0))
LANDED = Vector((0.15, 1.15, QUAY_Z))       # crate centre-bottom when set down on the stones


def mats():
    g = {}
    g["stone"] = ship.wood("seaworn_sandstone_brick", 1.4, wet=0.5, tint=(0.62, 0.6, 0.58), name="hb_stone")
    g["cobble"] = ship.wood("cobblestone_floor_04", 1.2, wet=0.6, tint=(0.6, 0.58, 0.56), name="hb_cobble")
    g["iron"] = ship.paint("hb_iron", (0.03, 0.03, 0.032), rough=0.5, grime=0.6, wet=0.5, scale=8, chips=0.5, under=(0.3, 0.12, 0.05))
    g["iron"].node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.6
    g["timber"] = ship.wood("weathered_planks", 0.8, wet=0.4, tint=(0.75, 0.62, 0.5), name="hb_timber")
    g["chain"] = p4.mat("hb_chain", (0.08, 0.05, 0.035), rough=0.55, metal=0.9)
    g["crate"] = ship.wood("weathered_planks", 0.7, wet=0.85, tint=(0.55, 0.42, 0.32), name="hb_crate")
    return g


def crate_material(g):
    m = g["crate"].copy(); m.name = "hb_crate_painted"
    # stencil paint on the front planks (local -Y face of the crate object): logo 0.62 m wide, centred
    lw = 0.66; lh = lw / si.LOGO_ASPECT
    proj = Matrix.Scale(1 / lw, 4, Vector((1, 0, 0))) @ Matrix.Scale(1 / lh, 4, Vector((0, 1, 0))) @ Matrix.Scale(1 / 0.02, 4, Vector((0, 0, 1)))
    # object (x, z) -> logo (u, v); object y = -CD/2 -> logo w = 0
    R = Matrix.Rotation(math.radians(-90), 4, 'X')                         # (x, y, z) -> (x, z, -y)
    T = Matrix.Translation((lw / 2, lh / 2 - (CH / 2 + 0.02), -CD / 2))
    si.paint_logo(m, proj @ T @ R, wear=0.42, wet=0.85, fade=0.92)
    return m


def mud_material(name, wipe):
    """Grey-black harbour mud on the crate face, wiped off (object x < wipe -> clean) by his sleeve."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.03, 0.028, 0.022, 1); b.inputs["Roughness"].default_value = 0.25
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 30; nz.inputs["Detail"].default_value = 8
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = 0.6; bm.inputs["Distance"].default_value = 0.004
    nt.links.new(nz.outputs["Fac"], bm.inputs["Height"]); nt.links.new(bm.outputs["Normal"], b.inputs["Normal"])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
    # sleeve streaks: a band in z wiped in two strokes; edge ragged with noise
    e = nt.nodes.new("ShaderNodeMath"); e.operation = 'MULTIPLY_ADD'; nt.links.new(nz.outputs["Fac"], e.inputs[0]); e.inputs[1].default_value = 0.06
    nt.links.new(sep.outputs[0], e.inputs[2])
    wv = nt.nodes.new("ShaderNodeValue"); wv.name = "WIPE"; wv.outputs[0].default_value = wipe
    gt = nt.nodes.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; nt.links.new(e.outputs[0], gt.inputs[0]); nt.links.new(wv.outputs[0], gt.inputs[1])
    # patchy: some mud stays in the plank seams even after the wipe
    pn = nt.nodes.new("ShaderNodeTexNoise"); pn.inputs["Scale"].default_value = 6; nt.links.new(tc.outputs["Object"], pn.inputs["Vector"])
    pr = nt.nodes.new("ShaderNodeMapRange"); pr.inputs[1].default_value = 0.35; pr.inputs[2].default_value = 0.6; pr.inputs[3].default_value = 0.1
    nt.links.new(pn.outputs["Fac"], pr.inputs[0])
    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = 'MAXIMUM'; nt.links.new(gt.outputs[0], mx.inputs[0]); nt.links.new(pr.outputs[0], mx.inputs[1])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); ms = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mx.outputs[0], ms.inputs[0]); nt.links.new(tr.outputs[0], ms.inputs[1]); nt.links.new(b.outputs[0], ms.inputs[2])
    nt.links.new(ms.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m


def crate(g, M, wipe=-1.0, mud=True):
    """A planked shipping crate: six faces of boards with battens, iron corner straps. M: centre-bottom frame."""
    root = bpy.data.objects.new("crate", None); bpy.context.scene.collection.objects.link(root)
    pm = crate_material(g)
    parts = []
    # boards: front/back faces (y = ±CD/2): 5 horizontal boards; sides, top, bottom similar
    nb = 5; bh = CH / nb
    for s in (-1, 1):
        for k in range(nb):
            o = ship.box("crate_board", (0, s * (CD / 2 - 0.011), bh * (k + 0.5)), (CW, 0.022, bh - 0.006), pm if s < 0 else g["crate"], bevel=0.003)
            parts.append(o)
        for k in range(nb):
            parts.append(ship.box("crate_board", (s * (CW / 2 - 0.011), 0, bh * (k + 0.5)), (0.022, CD - 0.044, bh - 0.006), g["crate"], bevel=0.003))
    for zz in (0.011, CH - 0.011):
        for k in range(4):
            parts.append(ship.box("crate_board", (-CW / 2 + CW / 8 * (2 * k + 1), 0, zz), (CW / 4 - 0.006, CD - 0.044, 0.022), g["crate"], bevel=0.003))
    for s in (-1, 1):                       # battens on the ends, iron corner straps
        parts.append(ship.box("crate_batten", (s * (CW / 2 + 0.012), 0, CH / 2), (0.024, CD * 0.9, 0.07), g["crate"], bevel=0.004))
        for sy in (-1, 1):
            parts.append(ship.box("crate_strap", (s * (CW / 2 - 0.02), sy * (CD / 2 + 0.002), CH / 2), (0.05, 0.004, CH + 0.004), g["iron"]))
    for o in parts:                         # bake each board's offset into its mesh: object coords = crate coords
        o.data.transform(Matrix.Translation(o.location)); o.location = (0, 0, 0)
        o.parent = root
    if mud:
        bpy.ops.mesh.primitive_plane_add(size=1); m = bpy.context.active_object; m.name = "crate_mud"
        m.scale = (CW - 0.01, CH - 0.01, 1); bpy.ops.object.transform_apply(scale=True)
        sub = m.modifiers.new("sub", "SUBSURF"); sub.subdivision_type = 'SIMPLE'; sub.levels = sub.render_levels = 4
        tx = bpy.data.textures.new("mud_lumps", 'CLOUDS'); tx.noise_scale = 0.04
        dm = m.modifiers.new("lumps", "DISPLACE"); dm.texture = tx; dm.strength = 0.004; dm.mid_level = 0.0
        m.matrix_world = Matrix.Translation((0, -CD / 2 - 0.0035, CH / 2)) @ Matrix.Rotation(math.radians(90), 4, 'X')
        m.data.materials.append(mud_material("mud", wipe)); m.parent = root
    root.matrix_world = M
    return root


def quay(g):
    # quay wall face (stone) down to below the water, the quay top (cobbles), a granite coping at the edge
    ship.box("hb_quay_top", (0, 6, QUAY_Z - 0.2), (30, 12, 0.4), g["cobble"])
    ship.box("hb_quay_wall", (0, EDGE_Y + 0.25, QUAY_Z / 2 - 1.5), (30, 0.5, QUAY_Z + 3.0), g["stone"])
    ship.box("hb_coping", (0, EDGE_Y + 0.25, QUAY_Z + 0.06), (30, 0.55, 0.12), g["stone"], bevel=0.02)
    # an iron bollard and a coil of rope by the edge
    ship.cyl("hb_bollard", (3.3, 0.7, QUAY_Z), (3.3, 0.7, QUAY_Z + 0.55), 0.15, 0.12, mat=g["iron"], verts=24)
    ship.cyl("hb_bollard_cap", (3.3, 0.7, QUAY_Z + 0.55), (3.3, 0.7, QUAY_Z + 0.62), 0.19, mat=g["iron"], verts=24)
    rope = ship.tarred_rope("hb_rope")
    for k in range(5):
        r = 0.32 - 0.03 * k
        pts = [Vector((2.4 + r * math.cos(a), 1.2 + r * math.sin(a), QUAY_Z + 0.02 + 0.03 * k)) for a in [i / 23 * 2 * math.pi for i in range(24)]]
        ship.rope("hb_rope_coil", pts, 0.018, rope)
    # wooden piles along the quay face
    for x in (-4.5, -1.0, 3.5, 6.0):
        ship.cyl("hb_pile", (x, EDGE_Y - 0.12, -3), (x, EDGE_Y - 0.12, QUAY_Z + 0.35), 0.13, mat=g["timber"], verts=12)


def crane(g, hook):
    """A hand/steam dockside crane: cast-iron pillar, timber jib with iron ties, a chain to the hook."""
    base = CRANE
    ship.cyl("hb_crane_pillar", base, base + Vector((0, 0, 1.4)), 0.35, 0.26, mat=g["iron"], verts=24)
    ship.box("hb_crane_house", base + Vector((0.45, 0.35, 0.75)), (1.1, 0.9, 1.5), g["timber"], bevel=0.02)
    ship.cyl("hb_crane_chimney", base + Vector((0.75, 0.55, 1.5)), base + Vector((0.75, 0.55, 2.6)), 0.08, mat=g["iron"], verts=12)
    top = hook + Vector((0, 0, 2.3)); foot = base + Vector((0, 0, 1.2))
    for s in (-1, 1):
        off = Vector((-0.12, 0.12, 0)) * s
        ship.cyl("hb_crane_jib", foot + off, top + off * 0.5, 0.09, 0.07, mat=g["timber"], verts=8)
    ship.cyl("hb_crane_tie", base + Vector((0, 0, 2.0)), top, 0.025, mat=g["iron"], verts=8)
    ship.cyl("hb_crane_sheave", top + Vector((-0.08, 0.08, 0)), top + Vector((0.08, -0.08, 0)), 0.16, mat=g["iron"], verts=24)
    # chain: links as small tori along the fall
    ch = g["chain"]
    n = int((top.z - hook.z) / 0.06)
    for k in range(n):
        p = top.lerp(hook + Vector((0, 0, 0.12)), (k + 0.5) / n)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.026, minor_radius=0.008, location=p, rotation=(0, math.pi / 2, (k % 2) * math.pi / 2),
                                         major_segments=12, minor_segments=6)
        o = bpy.context.active_object; o.name = "hb_chain"; o.scale = (1, 1, 1.6); o.data.materials.append(ch)
    ship.cyl("hb_hook", hook + Vector((0, 0, 0.12)), hook, 0.03, mat=g["iron"], verts=12)


def slings(g, hook, Mc):
    """Four chain legs from the hook to the crate's top corners."""
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = Mc @ Vector((sx * (CW / 2 - 0.03), sy * (CD / 2 - 0.03), CH + 0.01))
            ship.rope("hb_sling", [hook, c], 0.008, g["chain"])


def harbour_world():
    sea.sky(strength=0.35, rot_deg=40, res="4k", aid="kloppenheim_06_puresky")
    w = sea.water_material("harbour", deep=(0.002, 0.006, 0.007), crest=(0.01, 0.025, 0.025))
    o = sea.ocean(size=50, res=12, scale=0.22, chop=0.6, wind=4.0, seed=11, repeat=2, foam=0.05, mat=w, time=5.0)
    sea.far_sea(50, mat=w, z=-0.02)
    sea.haze((0, -30, 4), (140, 80, 12), density=0.035, color=(0.72, 0.74, 0.76))
    p4.sun(205, 4, 1.2, color=(1.0, 0.72, 0.45), angle=8)          # a weak low sun behind the mist
    # a moored brig's masts dim in the mist across the harbour
    tm = p4.mat("hb_far_mast", (0.04, 0.04, 0.045), rough=0.8)
    for x, hgt in ((-14, 22), (-10.5, 20)):
        ship.cyl("hb_far_mast", (x, -38, 0), (x, -38, hgt), 0.25, 0.14, mat=tm, verts=8)
    ship.box("hb_far_hull", (-12, -38, 1.0), (16, 4, 3), tm)


def build(shot, t, out):
    E = si.ease
    si.C.render_setup(samples=64, noise=0.03, bounces=8)
    g = mats(); quay(g); harbour_world()
    pos = (1.25, 0.9)
    wipe = {"A": -1.0, "B": -1.0, "C": -CW / 2 + CW * E(t), "D": 1.0, "LOGO": 1.0}[shot]
    if shot in ("A", "B"):
        rise = {"A": -0.3 + 1.0 * E(t), "B": 0.6 + 1.4 * E(t)}[shot]          # crate bottom height (water at 0)
        cx = Vector((0.15, -1.1, rise))
        hook = cx + Vector((0, 0, CH + 0.75))
        Mc = Matrix.Translation(cx) @ Matrix.Rotation(0.12 * math.sin(4 * t), 4, 'Z')
        crate(g, Mc, wipe=wipe); slings(g, hook, Mc); crane(g, hook)
        if rise < 0.5:                                          # water pouring off it / the slough round it
            sea.mist_puff("hb_slough", cx + Vector((0, 0, max(0.0, rise) + 0.1)), (0.9, 0.7, 0.25), density=0.4, seed=3)
        if shot == "A":
            def signal(h, dv, M, Mi):
                P.stand(h, lean=-2, weight="L", twist=-4); P.head(h, pitch=-6, yaw=20, tilt=0)
                dv.lids(0.1); dv.brow_knit(0.5)
                P.hand_reach(h, "R", Vector((-0.35, -0.12, 1.85)), elbow=(-0.7, 0.4, -0.3), hand_dir=Vector((-0.1, -0.2, 1)))
                P.rest_hand(h, "R", curl=10)
                P.arm_down(h, "L", out=0.12, fwd=0.04, bend=14); P.rest_hand(h, "L", curl=26)
            dv, M = si.person("deveau", pos, 260, signal, hook + Vector((0, 0, 1.5)), floor_z=QUAY_Z, wet=0.5, cap=True)
            c = Vector((5.8, -4.2, QUAY_Z + 0.6)) + Vector((-0.4, 0.2, 0)) * E(t)
            si.cam(c, (0.4, -0.2, 1.75), lens=28, fstop=5.6)
        else:
            hk = cx + Vector((CW / 2 + 0.02, -0.15, CH * 0.6))
            def steady(h, dv, M, Mi):
                P.stand(h, lean=14, weight="R", twist=-8); P.head(h, pitch=18, yaw=-10, tilt=0)
                dv.lids(0.3); dv.brow_knit(0.8)
                a = Mi @ (pos3 + (hk - pos3) * 0.38); b = Mi @ (pos3 + (hk - pos3) * 0.58)
                P.hand_reach(h, "L", a, elbow=(0.7, 0.4, -0.5)); P.grip(h, "L", 1.0)
                P.hand_reach(h, "R", b, elbow=(-0.7, 0.4, -0.5)); P.grip(h, "R", 1.0)
            pos3 = Vector((pos[0], pos[1], QUAY_Z + 1.1))
            dv, M = si.person("deveau", (pos[0], pos[1] - 0.25), 245, steady, hk, floor_z=QUAY_Z, wet=0.5, cap=True)
            ship.cyl("hb_boathook", pos3 + (pos3 - hk).normalized() * 0.5, hk, 0.018, mat=g["timber"], verts=10)
            ship.cyl("hb_boathook_iron", hk, hk + (hk - pos3).normalized() * 0.12, 0.012, mat=g["iron"], verts=10)
            c = Vector((3.3, 2.8, QUAY_Z + 1.55)) + Vector((-0.15, -0.05, 0.05)) * E(t)
            si.cam(c, Vector((0.75, -0.35, QUAY_Z + 0.55)), lens=24, fstop=4.0)
    else:
        Mc = Matrix.Translation(LANDED) @ Matrix.Rotation(0.1, 4, 'Z')
        crate(g, Mc, wipe=wipe)
        hook = LANDED + Vector((0, 0, CH + 0.8))
        crane(g, hook + Vector((0, 0, 0.6)))
        front = Mc @ Vector((0, -CD / 2, CH * 0.5))
        if shot == "C":
            x = -CW / 2 + 0.08 + (CW - 0.16) * E(t)
            def wipe_pose(h, dv, M, Mi):
                si.kneel(h, down="R", lean=24, drop=0.42, fwd=0.40)
                P.head(h, pitch=24, yaw=-6, tilt=0); dv.lids(0.4); dv.brow_knit(0.7)
                P.hand_reach(h, "R", Mi @ (Mc @ Vector((x, -CD / 2 - 0.07, CH * 0.5))), elbow=(-0.6, 0.3, -0.7), hand_dir=Vector((-0.6, -0.2, -0.7)))
                P.rest_hand(h, "R", curl=50)
                P.hand_reach(h, "L", Mi @ (Mc @ Vector((-CW / 2 - 0.02, -CD / 2 + 0.05, CH + 0.03))), elbow=(0.7, 0.3, -0.4))
                P.rest_hand(h, "L", curl=20)
            dv, M = si.person("deveau", tuple(Mc @ Vector((0.1, -CD / 2 - 0.62, 0)))[:2], 100, wipe_pose, front, floor_z=QUAY_Z, wet=0.5, cap=True)
            c = Mc @ Vector((0.75, -1.05, 0.95)); si.cam(c, front, lens=45, fstop=3.2)
        elif shot == "D":
            def look_back(h, dv, M, Mi):
                si.kneel(h, down="R", lean=6, drop=0.42, fwd=0.40)
                P.head(h, pitch=-2, yaw=-55, tilt=0); dv.lids(0.2); dv.brow_knit(0.9)
                P.hand_reach(h, "R", Mi @ (Mc @ Vector((0.05, -CD / 2 - 0.04, CH * 0.55))), elbow=(-0.6, 0.3, -0.7), hand_dir=Vector((-0.2, 0.3, -0.9)))
                P.rest_hand(h, "R", curl=25)
                knee = h.bone_head("lowerleg01.L")
                P.hand_reach(h, "L", knee + Vector((0.0, -0.03, 0.1)), elbow=(0.7, 0.4, -0.2), hand_dir=Vector((-0.2, -0.6, -0.8)))
                P.rest_hand(h, "L", curl=35)
            dv, M = si.person("deveau", tuple(Mc @ Vector((0.62, -CD / 2 - 0.55, 0)))[:2], 100, look_back, Vector((0.5, -8, 0.3)), floor_z=QUAY_Z, wet=0.5, cap=True)
            c = Mc @ Vector((-0.5, -2.1, 0.75)) + Vector((0.15, 0.4, 0.0)) * E(t)
            si.cam(c, front + Vector((0.2, 0, 0.1)), lens=35, fstop=4.0)
        else:
            c = front + Vector((0.05, -1.15, 0.05))
            p4.light('AREA', "check_key", 25, (1.0, 0.97, 0.92), loc=front + Vector((0.6, -1.0, 0.8)), target=front, size=0.8)
            si.cam(c, front, lens=50, fstop=8.0)
    si.finish(out, sat=1.0, bloom=0.3, clip_ok=("crate", "boathook", "hb_quay", "hb_coping", "hb_sling"))
