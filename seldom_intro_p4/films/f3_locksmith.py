"""Film 3 - THE LOCKSMITH (13 s). A dead bank vault, 1870s. A locksmith kneels at a cast-iron safe nobody has
opened in a century: stethoscope to the door, he turns the dial a click at a time; the bolts thunk back, the door
groans open. Inside, on worn red velvet, one enamel plaque. His lantern finds it. HOLD.

    blender -b -P films/run.py -- f3 <A|B|C|D|LOGO> [t] [out.png]
"""
import math, random
import bpy
from mathutils import Vector, Matrix
import si, p4, ship, ph, skfab, poses as P, human as H, deveau as D

SW, SD, SH = 0.78, 0.66, 1.02            # safe body width, depth, height (on a 0.08 m plinth)
PL = 0.08
DOOR_T = 0.11
FRONT_Y = -SD / 2
HINGE = Vector((-SW / 2 + 0.03, FRONT_Y, 0))
DIAL = Vector((0.08, FRONT_Y - DOOR_T + 0.002, PL + 0.66))
HANDLE = Vector((0.24, FRONT_Y - DOOR_T + 0.002, PL + 0.5))
PLAQUE_W = 0.2
SAFE = {}
SHOTS = dict(A=(0.0, 3.5), B=(3.5, 7.0), C=(7.0, 10.0), D=(10.0, 13.0), LOGO=(13.0, 15.5))   # ends on a clean logo hold
LANTERN_UID = "46528337bec34fa49f2c71577efc7bc0"


def mats():
    g = {}
    g["body"] = ship.paint("sf_body", (0.018, 0.03, 0.02), rough=0.38, grime=0.7, scale=7, chips=0.35, under=(0.18, 0.08, 0.04))
    g["body"].node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.3
    g["gold"] = p4.mat("sf_gold_leaf", (0.75, 0.52, 0.2), rough=0.3, metal=1.0)
    g["steel"] = p4.mat("sf_steel", (0.32, 0.31, 0.3), rough=0.35, metal=1.0)
    g["nickel"] = p4.mat("sf_nickel", (0.62, 0.6, 0.56), rough=0.22, metal=1.0)
    g["inside"] = ship.paint("sf_inside", (0.1, 0.085, 0.06), rough=0.6, grime=0.6, scale=9, chips=0.1, under=(0.2, 0.1, 0.05))
    v = bpy.data.materials.new("sf_velvet"); v.use_nodes = True; b = v.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.16, 0.012, 0.015, 1); b.inputs["Roughness"].default_value = 0.85
    b.inputs["Sheen Weight"].default_value = 1.0; b.inputs["Sheen Tint"].default_value = (1.0, 0.45, 0.4, 1)
    g["velvet"] = v
    g["brick"] = ship.wood("seaworn_sandstone_brick", 2.0, tint=(0.8, 0.62, 0.5), name="sf_brick")
    g["floor"] = ship.wood("slate_floor", 1.5, tint=(0.6, 0.55, 0.5), name="sf_floor")
    return g


def safe(g, door=0.0):
    """Cast-iron safe, front at -Y. door: open angle in degrees (0 shut). Returns the plaque frame M."""
    out = []
    ship.box("sf_plinth", (0, 0, PL / 2), (SW + 0.04, SD + 0.04, PL), g["body"], bevel=0.01)
    # body as a hollow: back, sides, top, bottom (walls 0.07)
    wt = 0.07; z0 = PL
    ship.box("sf_back", (0, SD / 2 - wt / 2, z0 + SH / 2), (SW, wt, SH), g["body"], bevel=0.012)
    for s in (-1, 1):
        ship.box("sf_side", (s * (SW / 2 - wt / 2), 0, z0 + SH / 2), (wt, SD, SH), g["body"], bevel=0.012)
    ship.box("sf_top", (0, 0, z0 + SH - wt / 2), (SW, SD, wt), g["body"], bevel=0.015)
    ship.box("sf_bottom", (0, 0, z0 + wt / 2), (SW, SD, wt), g["body"], bevel=0.008)
    # interior lining, a shelf, a small drawer, velvet on the lower floor
    iw = SW - 2 * wt; idp = SD - wt
    ship.box("sf_shelf", (0, wt / 2 - 0.01, z0 + SH * 0.58), (iw, idp - 0.02, 0.02), g["inside"])
    ship.box("sf_drawer", (0, wt / 2 + 0.02, z0 + SH * 0.58 + 0.07), (iw * 0.8, idp - 0.1, 0.12), g["inside"], bevel=0.004)
    ship.box("sf_drawer_knob", (0, FRONT_Y + 0.04, z0 + SH * 0.58 + 0.07), (0.03, 0.02, 0.02), g["gold"], bevel=0.004)
    vel = ship.box("sf_velvet", (0, wt / 2 - 0.01, z0 + wt + 0.008), (iw - 0.004, idp - 0.02, 0.016), g["velvet"], bevel=0.006)
    ship.box("sf_inner_back", (0, SD / 2 - wt - 0.002, z0 + SH / 2), (iw, 0.004, SH - 2 * wt), g["inside"])
    # door: a slab hinged at the left front edge; dial, handle, gold pinstripe panels, maker's lettering left blank
    dr = []
    dw, dh = SW - 0.03, SH - 0.03
    d = ship.box("sf_door", (dw / 2, -DOOR_T / 2, z0 + SH / 2), (dw, DOOR_T, dh), g["body"], bevel=0.012); dr.append(d)
    for inset, th in ((0.05, 0.004), (0.065, 0.0025)):            # gold pinstripe border (raised a hair)
        w_, h_ = dw - 2 * inset, dh - 2 * inset
        for cx, cz, sx, sz in ((dw / 2, z0 + SH / 2 + h_ / 2, w_, th), (dw / 2, z0 + SH / 2 - h_ / 2, w_, th),
                               (inset + 0.015, z0 + SH / 2, th, h_), (dw - inset - 0.015, z0 + SH / 2, th, h_)):
            dr.append(ship.box("sf_pinstripe", (cx, -DOOR_T - 0.0004, cz), (sx, 0.001, sz), g["gold"]))
    dx = DIAL.x - HINGE.x; hx = HANDLE.x - HINGE.x
    dr.append(ship.cyl("sf_dial_ring", (dx, -DOOR_T, DIAL.z), (dx, -DOOR_T - 0.012, DIAL.z), 0.075, mat=g["nickel"], verts=48))
    dial = []
    dial.append(ship.cyl("sf_dial", (dx, -DOOR_T - 0.012, DIAL.z), (dx, -DOOR_T - 0.04, DIAL.z), 0.05, mat=g["nickel"], verts=48))
    dial.append(ship.cyl("sf_dial_knob", (dx, -DOOR_T - 0.04, DIAL.z), (dx, -DOOR_T - 0.07, DIAL.z), 0.022, mat=g["steel"], verts=24))
    for k in range(50):                                          # engraved graduations (on the turning dial)
        a_ = 2 * math.pi * k / 50; L = 0.012 if k % 5 == 0 else 0.006
        p = Vector((dx + 0.044 * math.cos(a_), -DOOR_T - 0.0405, DIAL.z + 0.044 * math.sin(a_)))
        dial.append(ship.box("sf_grad", p, (0.0012, 0.0008, L * 0.6), p4.mat("sf_engr", (0.02, 0.02, 0.02), 0.5), rot=(0, -a_ + math.pi / 2, 0)))
    dr.append(ship.box("sf_index", (dx, -DOOR_T - 0.0125, DIAL.z + 0.068), (0.004, 0.002, 0.01), g["gold"]))   # fixed index mark
    dr.append(ship.cyl("sf_handle_hub", (hx, -DOOR_T, HANDLE.z), (hx, -DOOR_T - 0.04, HANDLE.z), 0.028, mat=g["nickel"], verts=24))
    hb = ship.box("sf_handle", (hx, -DOOR_T - 0.045, HANDLE.z - 0.07), (0.028, 0.02, 0.16), g["nickel"], bevel=0.006)
    bolts = []
    for bz in (0.25, 0.5, 0.75):                                 # bolts on the free edge: thrown (out) while locked
        bolts.append(ship.cyl("sf_bolt", (dw - 0.01, -DOOR_T / 2, z0 + SH * bz), (dw + 0.035, -DOOR_T / 2, z0 + SH * bz), 0.018, mat=g["steel"], verts=16))
    import f2_letters as F2
    dial_root = F2.group("sf_dial_root", dial, Vector((dx, -DOOR_T, DIAL.z)))
    handle_root = F2.group("sf_handle_root", [hb], Vector((hx, -DOOR_T, HANDLE.z)))
    bolt_root = F2.group("sf_bolt_root", bolts, Vector((dw, -DOOR_T / 2, z0)))
    door_root = F2.group("sf_door_root", dr + [dial_root, handle_root, bolt_root], Vector((0, 0, 0)))
    door_root.matrix_world = Matrix.Translation(HINGE) @ Matrix.Rotation(math.radians(-door), 4, 'Z')
    SAFE.update(door=door_root, dial=dial_root, handle=handle_root, bolts=bolt_root)
    # the plaque on the velvet (a real enamel plate, lying flat, tilted a little)
    Mp = Matrix.Translation((0.1, -0.1, z0 + wt + 0.0165)) @ Matrix.Rotation(-0.12, 4, 'Z')
    em = si.enamel_material("plaque_enamel", ground=(0.006, 0.008, 0.014), chip=0.15, grime=0.15)
    pl = si.plate("seldom_plaque", Mp, PLAQUE_W, thick=0.004, mat=em, margin=0.1, screws=4)
    return Mp


def vault(g):
    ship.box("sf_floor", (0, 0, -0.03), (8, 8, 0.06), g["floor"])
    ship.box("sf_wall_back", (0, 1.0, 1.6), (6, 0.3, 3.2), g["brick"])
    ship.box("sf_wall_left", (-1.8, -1, 1.6), (0.3, 6, 3.2), g["brick"])
    ship.box("sf_wall_right", (2.2, -1, 1.6), (0.3, 6, 3.2), g["brick"])
    ship.box("sf_ceiling", (0, -1, 3.25), (6, 6, 0.1), g["brick"])
    p4.world_color((0.0008, 0.0008, 0.001))
    # cold light falling in from the vault doorway behind the camera (stair well), high and soft
    fl = p4.light('AREA', "doorway", 200, (0.62, 0.72, 1.0), loc=(0.6, -3.6, 2.6), target=(0, -0.3, 0.6), size=1.2)
    fl.visible_camera = False
    # dust in the air (a faint volume; the lantern beam shows in it)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -1.0, 1.45)); v = bpy.context.active_object; v.name = "sf_dust"
    v.scale = (3.4, 3.8, 3.1)                                           # from below the floor
    m = bpy.data.materials.new("sf_dust_m"); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
    vs = nt.nodes.new("ShaderNodeVolumeScatter"); vs.inputs["Density"].default_value = 0.012; vs.inputs["Anisotropy"].default_value = 0.6
    nt.links.new(vs.outputs[0], nt.nodes["Material Output"].inputs["Volume"]); v.data.materials.append(m)
    # floating dust motes (tiny spheres, a few hundred)
    rng = random.Random(9); dm = p4.mat("mote", (0.7, 0.62, 0.5), rough=0.9)
    items = []
    while len(items) < 500:                                  # floating motes, never inside the man's space
        q = (rng.uniform(-0.8, 0.8), rng.uniform(-1.3, -0.3), rng.uniform(0.3, 1.6))
        if -0.45 < q[0] < 0.95 and -1.55 < q[1] < -0.4 and q[2] < 1.55:
            continue
        items.append((q, (0.0012, 0.0012, 0.0012), 0))
    p4.boxes("sf_motes", items, dm)


def dark_lantern(loc, aim, group_it=False):
    """The storm lantern, its beam aimed at `aim`. group_it: flame and lights parented to it (it is carried)."""
    r, ms = skfab.model(LANTERN_UID, height=0.3, name="lantern")
    for o in ms:
        if len(o.data.polygons) > 20000:
            dm = o.modifiers.new("dec", "DECIMATE"); dm.ratio = 0.12
        o.visible_shadow = False
    r.matrix_world = Matrix.Translation(loc)
    f = Vector(loc) + Vector((0, 0, 0.14))
    fm = p4.mat("lantern_flame", (1, 0.6, 0.2), emit=(1.0, 0.5, 0.15), strength=40)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.008, location=f); fl = bpy.context.active_object; fl.name = "lantern_flame"
    fl.scale = (1, 1, 2.2); fl.data.materials.append(fm); fl.visible_shadow = False
    p4.light('POINT', "lantern_glow", 45, (1.0, 0.6, 0.28), loc=f + Vector((0, 0, 0.02)), size=0.02)
    gl = p4.light('POINT', "lantern_glow", 28, (1.0, 0.6, 0.28), loc=f + Vector((0, 0, 0.02)), size=0.02) if False else None
    bm = p4.light('SPOT', "lantern_beam", 700, (1.0, 0.68, 0.38), loc=f + Vector((0, 0, 0.02)), target=aim, size=0.03, spot=34, blend=0.5)
    if group_it:
        import f2_letters as F2
        kids = [fl, bm] + [o for o in bpy.data.objects if o.name.startswith("lantern_glow") and o.parent is None]
        return F2.group("lantern_carried", [r] + kids, Vector(loc))
    return r


def pose_listen(h, dv, M, Mi):
    """Kneeling at the door, head cocked to the stethoscope; right fingers on the dial knob, left holds the chest
    piece flat on the door beside it."""
    si.kneel(h, down="L", lean=22, drop=0.42, fwd=0.36)
    Mi = si.kmi(Mi)                                        # targets below are world points
    P.head(h, pitch=14, yaw=-22, tilt=-12)
    dv.lids(0.92); dv.brow_knit(0.6)
    R = Mi.to_3x3()                                      # world directions -> rig
    P.hand_reach(h, "R", Mi @ (DIAL + Vector((0.08, -0.16, -0.035))), elbow=(-0.7, 0.2, -0.7),
                 hand_dir=R @ Vector((-0.6, 0.45, 0.0)))      # fingertips on the knob from its right
    P.grip(h, "R", 0.45)
    P.hand_reach(h, "L", Mi @ (DIAL + Vector((-0.17, -0.085, -0.07))), elbow=(0.7, 0.2, -0.6),
                 hand_dir=R @ Vector((0.0, -0.12, 1.0)))       # palm flat over the chest piece, fingers up the door
    P.rest_hand(h, "L", curl=15)


def stethoscope(dv, M):
    """Binaural tubes from both ears to a chest piece pressed on the door (the tubes hang naturally)."""
    rub = p4.mat("steth_rubber", (0.03, 0.025, 0.02), rough=0.45)
    met = D.brass_material("steth_metal")
    if si.CAMDUMP:
        return
    h = dv.h; bpy.context.view_layer.update()
    # ears: head bone frame (approx.: ±0.075 m to the side of the head bone head, 0.03 up)
    head_M = dv.h.arm.matrix_world @ dv.h.arm.pose.bones["head"].matrix if False else None
    # use the evaluated eye positions as a proxy for the head frame
    eyes = [e for e in h.eyes]
    c = (eyes[0].matrix_world.translation + eyes[1].matrix_world.translation) / 2
    side = (eyes[0].matrix_world.translation - eyes[1].matrix_world.translation).normalized()
    fwd = (DIAL - c); fwd.z = 0; fwd.normalize()
    ears = [c + side * s * 0.075 - fwd * 0.08 - Vector((0, 0, 0.02)) for s in (1, -1)]
    chest = DIAL + Vector((-0.17, -0.012, 0.05))
    y_join = c - fwd * 0.02 - Vector((0, 0, 0.28))
    for e in ears:
        mid = e.lerp(y_join, 0.5) - Vector((0, 0, 0.04)) - fwd * 0.03
        ship.rope("steth_tube", [e, mid, y_join], 0.0035, rub)
        ship.cyl("steth_tip", e, e + side * (0.01 if e.x > c.x else -0.01), 0.004, mat=met, verts=10)
    m2 = y_join.lerp(chest, 0.5) - Vector((0, 0, 0.12))
    ship.rope("steth_tube", [y_join, m2, chest - Vector((0, 0.018, 0))], 0.0038, rub)
    ship.cyl("steth_chestpiece", chest, chest - Vector((0, 0.018, 0)), 0.022, mat=met, verts=24)


SHOT_T0 = dict(A=0.0, B=3.5, C=7.0, D=10.0, LOGO=13.0)
SHOT_DUR = dict(A=3.5, B=3.5, C=3.0, D=3.0, LOGO=2.5)


def mechanism(shot):
    """Dial clicks round while he listens (A, B); in C the handle comes down, the bolts draw, the door swings."""
    t0, dur = SHOT_T0[shot], SHOT_DUR[shot]
    dial0 = {k: v for k, v in (("loc", SAFE["dial"].location.copy()),)}

    def dial_angle(sec):                      # 10 clicks a second? no: a deliberate 1.5 clicks/s, 3.6 deg each
        n = sec * 1.5; k = math.floor(n); f = n - k
        return math.radians(3.6) * (k + si.ease(min(1.0, f / 0.35)))

    @si.dyn
    def _(t, frame):
        sec = t0 + t * dur
        if shot in ("A", "B"):
            SAFE["dial"].rotation_euler = (0, dial_angle(sec), 0); si.key(SAFE["dial"], "rotation_euler", frame=frame)
        if shot == "C":
            u = si.ease(min(1.0, t / 0.3))                                     # handle down 70 deg
            SAFE["handle"].rotation_euler = (0, math.radians(-70) * u, 0); si.key(SAFE["handle"], "rotation_euler", frame=frame)
            b = si.ease(min(1.0, max(0.0, (t - 0.18) / 0.15)))                 # the bolts draw back (the thunk)
            SAFE["bolts"].location.x = SAFE["bolts_x0"] - 0.035 * b; si.key(SAFE["bolts"], "location", frame=frame)
            dang = 95 * si.ease(min(1.0, max(0.0, (t - 0.35) / 0.65)))
            SAFE["door"].rotation_euler = (0, 0, math.radians(-dang)); si.key(SAFE["door"], "rotation_euler", frame=frame)
    return dial_angle


def door_angle(shot, t):
    return {"A": 0.0, "B": 0.0, "C": 95 * si.ease(min(1.0, max(0.0, (t - 0.35) / 0.65))), "D": 100.0, "LOGO": 100.0}[shot]


def steth_once(dv, M):
    """Build the stethoscope once, on the first evaluated pose (still: now; animation: frame 1)."""
    done = {}

    @si.dyn
    def _(t, frame):
        if done or dv is None:
            return
        done[1] = True
        stethoscope(dv, M)


def build(shot, t, out):
    E = si.ease
    si.C.render_setup(samples=64, noise=0.03, bounces=8)
    g = mats(); vault(g)
    door = door_angle(shot, t)
    Mp = safe(g, door)
    SAFE["bolts_x0"] = SAFE["bolts"].location.x
    if shot in ("C", "D", "LOGO"):
        SAFE["bolts"].location.x -= 0.035 * (1.0 if shot != "C" else E(min(1.0, max(0.0, (t - 0.18) / 0.15))))
    mechanism(shot)
    pos = (0.12, FRONT_Y - 0.74)                 # far enough back that his forward boot is clear of the door
    if shot in ("A", "B"):
        dark_lantern(Vector((-0.5, FRONT_Y - 0.42, 0.0)), DIAL + Vector((0.0, 0, 0.0)))
        dv, M = si.person("deveau", pos, 90, pose_listen, DIAL, wet=0.0)
        steth_once(dv, M)
        if shot == "A":
            c = Vector((1.55, -0.95, 0.85)) + Vector((-0.1, 0.0, 0.0)) * E(t)
            si.cam(c, (-0.05, FRONT_Y - 0.38, 0.72), lens=24, fstop=4.0)
        else:      # close on the dial, over his right shoulder (his hand and shoulder in frame)
            c = Vector((0.62, FRONT_Y - 0.34, 0.86)) + Vector((-0.04, 0.0, -0.02)) * E(t)
            si.cam(c, DIAL + Vector((-0.06, -0.06, 0.0)), lens=40, fstop=2.4)
    elif shot == "C":
        pos = (0.4, FRONT_Y - 0.72)                  # clear of the door's swing (its free edge sweeps 0.75 m round the hinge)
        dark_lantern(Vector((-0.55, FRONT_Y - 0.55, 0.0)), DIAL + Vector((0.0, 0, 0.0)))

        def grip_point(T):
            d = door_angle("C", T)
            u = si.ease(min(1.0, T / 0.3))
            loc = Matrix.Rotation(math.radians(-70) * u, 3, 'Y') @ Vector((0, -0.065, -0.11))   # down the handle, its end
            return HINGE + Matrix.Rotation(math.radians(-d), 3, 'Z') @ (Vector((HANDLE.x - HINGE.x, -DOOR_T, HANDLE.z)) + loc)

        def haul(h, dv, M, Mi):
            si.kneel(h, down="L", lean=8, drop=0.42, fwd=0.36)
            Mi = si.kmi(Mi)                                        # targets below are world points
            P.stand(h, lean=0, weight="L", twist=10)
            P.head(h, pitch=8, yaw=-6, tilt=0); dv.lids(0.2); dv.brow_knit(0.9)
            let = si.ease(min(1.0, max(0.0, (si.T - 0.5) / 0.3)))           # hauls, then lets the door swing on
            knee_r = Mi @ Vector((pos[0] + 0.12, pos[1] + 0.25, 0.55))
            P.hand_reach(h, "R", (Mi @ grip_point(min(si.T, 0.5))).lerp(knee_r, let), elbow=(-0.8, 0.3, -0.5), hand_dir=Vector((-0.2, -0.4, -0.9)))
            P.grip(h, "R", 1.0 - 0.5 * let)
            P.hand_reach(h, "L", Mi @ Vector((pos[0] - 0.25, pos[1] - 0.02, 0.62)), elbow=(0.7, 0.2, -0.7), hand_dir=Vector((0.1, -0.4, -0.9)))
            P.rest_hand(h, "L", curl=30)
        dv, M = si.person("deveau", pos, 90, haul, DIAL, wet=0.0)
        c = Vector((1.05, -2.1, 1.55)); si.cam(c, (-0.3, FRONT_Y - 0.35, 0.55), lens=26, fstop=4.0)
    elif shot in ("D", "LOGO"):
        if shot == "D":
            def look_in(h, dv, M, Mi):
                u = si.ease(min(1.0, si.T / 0.5))                       # he leans in to look
                si.kneel(h, down="L", lean=12, drop=0.42, fwd=0.36)
                Mi = si.kmi(Mi)                                        # targets below are world points
                P.head(h, pitch=26 + 8 * u, yaw=8, tilt=-3); dv.lids(0.3); dv.brow_knit(0.2)
                P.stand(h, lean=8 * u, weight="L")
                for sd, sg in (("L", 1), ("R", -1)):                     # hands on his thighs, leaning to look in
                    knee = h.bone_head("lowerleg01.R")
                    P.hand_reach(h, sd, knee + Vector((sg * 0.16, 0.12, 0.1)), elbow=(0.7 * sg, 0.4, -0.2), hand_dir=Vector((-0.1 * sg, -0.6, -0.8)))
                    P.rest_hand(h, sd, curl=35)
            dv, M = si.person("deveau", pos, 90, look_in, Mp @ Vector((0, 0, 0)), wet=0.0)
            dark_lantern(Vector((0.46, FRONT_Y - 0.16, 0.0)), Mp @ Vector((0, 0, 0)))    # set down on the floor, beam in
            c = Vector((0.92, FRONT_Y - 1.2, 1.7)); tgt = Mp @ Vector((0, 0, 0))
            si.cam(c, tgt + Vector((0.04, -0.02, 0.1)), lens=34, fstop=3.2, focus=(c - tgt).length)
        else:
            dark_lantern(Vector((0.4, FRONT_Y - 0.5, 0.0)), Mp @ Vector((0, 0, 0)))
            tgt = Mp @ Vector((0, 0, 0)); c = tgt + Vector((0.0, -0.33, 0.3))
            p4.light('AREA', "check_key", 4, (1.0, 0.97, 0.92), loc=tgt + Vector((0.2, -0.4, 0.4)), target=tgt, size=0.4)
            si.cam(c, tgt, lens=60, fstop=8.0)
    si.finish(out, sat=1.08, bloom=0.4, clip_ok=("sf_dial", "sf_door", "sf_handle", "lantern", "steth", "sf_floor", "sf_side"))
