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
SHOTS = dict(A=(0.0, 3.5), B=(3.5, 7.0), C=(7.0, 10.0), D=(10.0, 13.0))
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
    dr.append(ship.cyl("sf_dial", (dx, -DOOR_T - 0.012, DIAL.z), (dx, -DOOR_T - 0.04, DIAL.z), 0.05, mat=g["nickel"], verts=48))
    dr.append(ship.cyl("sf_dial_knob", (dx, -DOOR_T - 0.04, DIAL.z), (dx, -DOOR_T - 0.07, DIAL.z), 0.022, mat=g["steel"], verts=24))
    for k in range(50):                                          # engraved graduations
        a = 2 * math.pi * k / 50; L = 0.012 if k % 5 == 0 else 0.006
        p = Vector((dx + 0.066 * math.cos(a), -DOOR_T - 0.0125, DIAL.z + 0.066 * math.sin(a)))
        o = ship.box("sf_grad", p, (0.0012, 0.0008, L), p4.mat("sf_engr", (0.02, 0.02, 0.02), 0.5), rot=(0, -a + math.pi / 2, 0))
        dr.append(o)
    dr.append(ship.cyl("sf_handle_hub", (hx, -DOOR_T, HANDLE.z), (hx, -DOOR_T - 0.04, HANDLE.z), 0.028, mat=g["nickel"], verts=24))
    hb = ship.box("sf_handle", (hx, -DOOR_T - 0.045, HANDLE.z - 0.07), (0.028, 0.02, 0.16), g["nickel"], bevel=0.006); dr.append(hb)
    # bolts on the door's free edge (they slide back when it opens)
    for bz in (0.25, 0.5, 0.75):
        dr.append(ship.cyl("sf_bolt", (dw - 0.01, -DOOR_T / 2, z0 + SH * bz), (dw + (0.0 if door > 0 else 0.035), -DOOR_T / 2, z0 + SH * bz), 0.018, mat=g["steel"], verts=16))
    Mh = Matrix.Translation(HINGE + Vector((0, 0, 0))) @ Matrix.Rotation(math.radians(-door), 4, 'Z')
    for o in dr:
        o.matrix_world = Mh @ o.matrix_world
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
    fl = p4.light('AREA', "doorway", 90, (0.62, 0.72, 1.0), loc=(0.6, -3.6, 2.6), target=(0, -0.3, 0.6), size=1.2)
    fl.visible_camera = False
    # dust in the air (a faint volume; the lantern beam shows in it)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -1.0, 1.5)); v = bpy.context.active_object; v.name = "sf_dust"
    v.scale = (3.8, 3.8, 3.0)
    m = bpy.data.materials.new("sf_dust_m"); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
    vs = nt.nodes.new("ShaderNodeVolumeScatter"); vs.inputs["Density"].default_value = 0.012; vs.inputs["Anisotropy"].default_value = 0.6
    nt.links.new(vs.outputs[0], nt.nodes["Material Output"].inputs["Volume"]); v.data.materials.append(m)
    # floating dust motes (tiny spheres, a few hundred)
    rng = random.Random(9); dm = p4.mat("mote", (0.7, 0.62, 0.5), rough=0.9)
    items = [((rng.uniform(-0.8, 0.8), rng.uniform(-1.3, -0.3), rng.uniform(0.3, 1.6)), (0.0012, 0.0012, 0.0012), 0) for _ in range(500)]
    p4.boxes("sf_motes", items, dm)


def dark_lantern(loc, aim):
    """A tin bullseye lantern standing on the floor, its beam aimed at the safe."""
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
    p4.light('POINT', "lantern_glow", 28, (1.0, 0.6, 0.28), loc=f + Vector((0, 0, 0.02)), size=0.02)
    p4.light('SPOT', "lantern_beam", 700, (1.0, 0.68, 0.38), loc=f + Vector((0, 0, 0.02)), target=aim, size=0.03, spot=34, blend=0.5)


def pose_listen(h, dv, M, Mi):
    """Kneeling at the door, head cocked to the stethoscope; right fingers on the dial knob, left holds the chest
    piece flat on the door beside it."""
    si.kneel(h, down="L", lean=22, drop=0.42, fwd=0.36)
    P.head(h, pitch=14, yaw=-22, tilt=-12)
    dv.lids(0.92); dv.brow_knit(0.6)
    knob = Mi @ (DIAL + Vector((0.0, -0.072, 0.0)))
    P.hand_reach(h, "R", knob + Vector((0.05, 0.0, -0.02)), elbow=(-0.7, 0.2, -0.7), hand_dir=Vector((-0.3, -0.85, 0.2)))
    P.grip(h, "R", 0.55)
    chest = Mi @ (DIAL + Vector((-0.17, -0.005, 0.05)))
    P.hand_reach(h, "L", chest + Vector((0.0, -0.06, 0.0)), elbow=(0.7, 0.2, -0.6), hand_dir=Vector((0.2, -0.95, 0.1)))
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


def build(shot, t, out):
    E = si.ease
    si.C.render_setup(samples=64, noise=0.03, bounces=8)
    g = mats(); vault(g)
    door = {"A": 0.0, "B": 0.0, "C": 95 * E(min(1.0, max(0.0, (t - 0.35) / 0.65))), "D": 100.0, "LOGO": 100.0}[shot]
    Mp = safe(g, door)
    pos = (0.12, FRONT_Y - 0.62)
    if shot in ("A", "B"):
        dark_lantern(Vector((0.66, FRONT_Y - 0.3, 0.0)), DIAL + Vector((-0.05, 0, 0.0)))
        dv, M = si.person("deveau", pos, 90, pose_listen, DIAL, wet=0.0)
        stethoscope(dv, M)
        if shot == "A":
            c = Vector((1.55, -0.95, 0.85)) + Vector((-0.1, 0.0, 0.0)) * E(t)
            si.cam(c, (-0.05, FRONT_Y - 0.38, 0.72), lens=24, fstop=4.0)
        else:      # close on the dial, over his right shoulder (his hand and shoulder in frame)
            c = Vector((0.58, FRONT_Y - 0.62, 0.95)) + Vector((-0.03, 0.03, 0)) * E(t)
            si.cam(c, DIAL + Vector((-0.02, -0.07, 0)), lens=55, fstop=2.4)
    elif shot == "C":
        dark_lantern(Vector((0.66, FRONT_Y - 0.3, 0.0)), DIAL + Vector((-0.05, 0, 0.0)))
        hz = HINGE + (Matrix.Rotation(math.radians(-door), 3, 'Z') @ Vector((HANDLE.x - HINGE.x, -DOOR_T - 0.06, 0)))
        hz.z = HANDLE.z - 0.09
        def haul(h, dv, M, Mi):
            si.kneel(h, down="L", lean=8, drop=0.42, fwd=0.36)
            P.stand(h, lean=0, weight="L", twist=10)
            P.head(h, pitch=8, yaw=-6, tilt=0); dv.lids(0.2); dv.brow_knit(0.9)
            P.hand_reach(h, "R", Mi @ hz + Vector((0, 0, 0)), elbow=(-0.8, 0.3, -0.5), hand_dir=Vector((-0.2, -0.4, -0.9)))
            P.grip(h, "R", 1.0)
            P.hand_reach(h, "L", Mi @ Vector((pos[0] - 0.25, pos[1] - 0.02, 0.62)), elbow=(0.7, 0.2, -0.7), hand_dir=Vector((0.1, -0.4, -0.9)))
            P.rest_hand(h, "L", curl=30)
        dv, M = si.person("deveau", pos, 90, haul, DIAL, wet=0.0)
        c = Vector((1.45, -1.3, 0.95)); si.cam(c, (-0.05, FRONT_Y - 0.25, 0.62), lens=26, fstop=4.0)
    elif shot in ("D", "LOGO"):
        if shot == "D":
            # he holds the lantern up, its beam into the safe, looking in
            def look_in(h, dv, M, Mi):
                si.kneel(h, down="L", lean=12, drop=0.42, fwd=0.36)
                P.head(h, pitch=34, yaw=8, tilt=-3); dv.lids(0.3); dv.brow_knit(0.2)
                P.hand_reach(h, "L", Mi @ Vector((-0.1, FRONT_Y - 0.27, 1.0)), elbow=(0.8, 0.2, -0.6), hand_dir=Vector((-0.1, 0.1, -1)))
                P.grip(h, "L", 1.0)
                knee = h.bone_head("lowerleg01.R")
                P.hand_reach(h, "R", knee + Vector((0.02, -0.03, 0.1)), elbow=(-0.7, 0.4, -0.2), hand_dir=Vector((0.2, -0.6, -0.8)))
                P.rest_hand(h, "R", curl=35)
            dv, M = si.person("deveau", pos, 90, look_in, Mp @ Vector((0, 0, 0)), wet=0.0)
            lt = si.palm(dv, M, "L") - Vector((0, 0, 0.34)) if not si.CAMDUMP else Vector((-0.1, FRONT_Y - 0.27, 0.6))
            dark_lantern(lt, Mp @ Vector((0, 0, 0)))
            c = Vector((0.68, FRONT_Y - 0.52, 1.4)); tgt = Mp @ Vector((0, 0, 0))
            si.cam(c, tgt + Vector((0.04, -0.02, 0.1)), lens=34, fstop=3.2, focus=(c - tgt).length)
        else:
            dark_lantern(Vector((0.4, FRONT_Y - 0.5, 0.0)), Mp @ Vector((0, 0, 0)))
            tgt = Mp @ Vector((0, 0, 0)); c = tgt + Vector((0.0, -0.33, 0.3))
            p4.light('AREA', "check_key", 4, (1.0, 0.97, 0.92), loc=tgt + Vector((0.2, -0.4, 0.4)), target=tgt, size=0.4)
            si.cam(c, tgt, lens=60, fstop=8.0)
    si.finish(out, sat=1.08, bloom=0.4, clip_ok=("sf_dial", "sf_door", "sf_handle", "lantern", "steth", "sf_floor", "sf_side"))
