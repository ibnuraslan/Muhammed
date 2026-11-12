"""FOREST: the spruce woods near the path, and the small clearing where the box was buried (Ch2; reused in Ch3).

Coordinates: the clearing is centred on the origin (radius ~5 m). The buried box lies at BOX (its wooden cover flush
with the ground). Dense spruce with some birch, moss, ferns, dead branches and haze. The path is ~800 m away (out of
frame); "toward the path" is -X.
Variants: "<light>|roles+extras" with light = grey (overcast morning) | dusk | night ; extras: dog, cover (box dug out),
lid (lid exposed, bolts), open (lid lifted), spruces (the five little spruces on bare earth), torch (a lone torch).
"""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix
from kit import pbr, box, cyl, join, area_light, point_at, haze
from common import ease
import ph
import rj
from rj import mat, person, stand, walk, forward, upright, reach, fingers_curl, SIDE

EXPOSURE = 0.0
BOUNCES = 5
BOX = Vector((0.6, -0.4, 0.0))
DUR = {}


def ground_mat():
    return mat("forest")


def build_woods(c, seed=4, n_trees=180):
    r = np.random.default_rng(seed)
    # gently uneven ground
    nx = ny = 81; S_ = 70.0
    xs = np.linspace(-S_ / 2, S_ / 2, nx); ys = np.linspace(-S_ / 2, S_ / 2, ny)
    X, Y = np.meshgrid(xs, ys)
    Hh = 0.18 * np.sin(X * 0.21) * np.cos(Y * 0.17) + 0.08 * np.sin(X * 0.7 + Y * 0.5)
    R_ = np.hypot(X - BOX.x, Y - BOX.y)
    Hh *= np.clip((R_ - 2.0) / 4.0, 0, 1)                      # flat around the box
    c["H"] = (xs, ys, Hh)
    me = bpy.data.meshes.new("ForestFloor")
    verts = [(xs[i], ys[j], Hh[j, i]) for j in range(ny) for i in range(nx)]
    faces = [(j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i) for j in range(ny - 1) for i in range(nx - 1)]
    me.from_pydata(verts, [], faces); me.update(); me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    o = bpy.data.objects.new("ForestFloor", me); bpy.context.collection.objects.link(o); o.data.materials.append(mat("forest"))
    pts = []
    while len(pts) < n_trees:
        x, y = r.uniform(-32, 32, 2)
        if math.hypot(x - BOX.x, y - BOX.y) < 5.2:
            continue
        if any(math.hypot(x - a, y - b) < 1.6 for (a, b, _, _) in pts):
            continue
        pts.append((x, y, r.uniform(0, 6.28), r.uniform(0.85, 1.25)))
    gz = lambda x, y: ground_z(c, x, y)
    firs = [(Vector((x, y, gz(x, y) - 0.05)), rz, s) for (x, y, rz, s) in pts[0::5] + pts[1::5] + pts[2::5]]
    pines = [(Vector((x, y, gz(x, y) - 0.05)), rz, s) for (x, y, rz, s) in pts[3::5]]
    birch = [(Vector((x, y, gz(x, y) - 0.05)), rz, s * 1.5) for (x, y, rz, s) in pts[4::5]]
    c["trees"] = rj.ph_instances("fir_tree_01", firs) + rj.ph_instances("pine_tree_01", pines)
    br, bms = rj.birch_template()
    for (loc, rz, s) in birch:
        rr = bpy.data.objects.new("Birch", None); bpy.context.collection.objects.link(rr)
        for ob in bms:
            n_ = ob.copy(); bpy.context.collection.objects.link(n_); n_.parent = rr; n_.matrix_parent_inverse = ob.matrix_parent_inverse.copy()
        rr.location = loc; rr.rotation_euler = (0, 0, rz); rr.scale = (s, s, s); c["trees"].append(rr)
    br.location = (0, 0, -1000); br.hide_render = True
    for ob in bms:
        ob.hide_render = True
    c["tree_pts"] = pts
    # undergrowth
    def sc(n, rmin, rmax, sd):
        rr = np.random.default_rng(sd); out = []
        while len(out) < n:
            x, y = rr.uniform(-30, 30, 2); d = math.hypot(x - BOX.x, y - BOX.y)
            if rmin < d < rmax:
                out.append((Vector((x, y, gz(x, y))), rr.uniform(0, 6.28), rr.uniform(0.8, 1.3)))
        return out
    c["ferns"] = rj.ph_instances("fern_02", sc(220, 3.8, 30, 1))
    c["moss"] = rj.ph_instances("moss_01", sc(90, 2.5, 25, 2))
    rj.ph_instances("dry_branches_medium_01", sc(40, 3.0, 25, 3))
    rj.ph_instances("tree_stump_01", sc(8, 5, 25, 4))
    rj.ph_instances("fir_sapling", sc(25, 4.5, 25, 5))


def ground_z(c, x, y):
    xs, ys, H = c["H"]
    i = int(np.clip(np.searchsorted(xs, x) - 1, 0, len(xs) - 2)); j = int(np.clip(np.searchsorted(ys, y) - 1, 0, len(ys) - 2))
    tx = (x - xs[i]) / (xs[i + 1] - xs[i]); ty = (y - ys[j]) / (ys[j + 1] - ys[j])
    return float((H[j, i] * (1 - tx) + H[j, i + 1] * tx) * (1 - ty) + (H[j + 1, i] * (1 - tx) + H[j + 1, i + 1] * tx) * ty)


# ============================================================================ the buried box (top parts in the ground)
def box_top(c, state):
    """state: 'buried' (nothing visible, moss), 'cover' (wooden cover under a little soil), 'lid' (cover off: the lid with
    seven bolts), 'open' (lid lifted on its hinge), 'spruces' (bare earth with five little spruces and the capped tube)."""
    planks = mat("planks"); steel = pbr("BoltSteel", (0.28, 0.27, 0.25), 0.45, 0.9)
    W, D = 1.05, 0.85
    if state in ("cover", "lid", "open"):
        pit = box("Pit", (BOX.x, BOX.y, -0.08), (W + 1.0, D + 1.0, 0.16), mat("soil"))
        pit.location.z = -0.081
    if state == "cover":
        parts = [box("Cover", (BOX.x, BOX.y + (k - 3) * 0.13, -0.02), (W + 0.12, 0.125, 0.035), planks) for k in range(7)]
        c["cover"] = join(parts, "WoodenCover")
        soil = box("SoilSkin", (BOX.x, BOX.y, 0.0), (W + 0.2, D + 0.3, 0.05), mat("soil"))
        c["soil_skin"] = soil
        mound = []
        for k in range(3):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1, location=(BOX.x - 1.6 + k * 0.3, BOX.y + 1.3 - k * 0.5, -0.1))
            mo = bpy.context.active_object; mo.scale = (0.7, 0.5, 0.35); mo.data.materials.append(mat("soil")); mound.append(mo)
        c["mound"] = mound
    if state in ("lid", "open"):
        hinge = bpy.data.objects.new("LidHinge", None); bpy.context.collection.objects.link(hinge)
        hinge.location = (BOX.x - W / 2, BOX.y, -0.04)
        lid = box("Lid", (BOX.x, BOX.y, -0.02), (W, D, 0.04), mat("pine"), bevel=0.004)
        parts = [lid]
        for k in range(7):                                       # seven sliding bolts along the free edges
            if k < 3:
                x, y, rz = BOX.x + W / 2 - 0.05, BOX.y - 0.28 + k * 0.28, 0.0
            elif k < 5:
                x, y, rz = BOX.x - 0.25 + (k - 3) * 0.5, BOX.y + D / 2 - 0.05, math.pi / 2
            else:
                x, y, rz = BOX.x - 0.25 + (k - 5) * 0.5, BOX.y - D / 2 + 0.05, math.pi / 2
            parts.append(box("BoltPlate", (x, y, 0.004), (0.16, 0.05, 0.006), steel, rot=(0, 0, rz)))
            parts.append(cyl("BoltBar", (x, y, 0.015), 0.009, 0.15, steel, 12, rot=(0, math.radians(90), rz)))
            parts.append(cyl("BoltKnob", (x + 0.02 * math.cos(rz), y + 0.02 * math.sin(rz), 0.03), 0.008, 0.03, steel, 10))
        lj = join(parts, "LidWithBolts")
        lj.parent = hinge; lj.matrix_parent_inverse = hinge.matrix_world.inverted()
        c["lid_hinge"] = hinge
        # the box rim (frame) visible round the lid, dark below
        for (dx, dy, sx, sy) in ((0, D / 2 + 0.03, W + 0.12, 0.06), (0, -D / 2 - 0.03, W + 0.12, 0.06), (W / 2 + 0.03, 0, 0.06, D), (-W / 2 - 0.03, 0, 0.06, D)):
            box("Rim", (BOX.x + dx, BOX.y + dy, -0.04), (sx, sy, 0.06), mat("pine"))
        box("Dark", (BOX.x, BOX.y, -0.3), (W, D, 0.02), pbr("Void", (0.004, 0.004, 0.004), 1.0))
        # tools left by the pit
        try:
            rj.model_fit("rusted_spade_01", (BOX.x - 1.3, BOX.y + 0.9, 0.0), rot_z=0.7, height=1.05)
            sp = bpy.data.objects[-1]
        except Exception:
            pass
    if state == "spruces":
        bare = box("BareEarth", (BOX.x, BOX.y, 0.0), (W + 0.6, D + 0.6, 0.03), mat("soil"))
        c["saplings"] = rj.ph_instances("fir_sapling", [(Vector((BOX.x + dx, BOX.y + dy, 0.0)), rz, 0.55)
                                                        for (dx, dy, rz) in ((-0.35, -0.25, 0.3), (0.35, -0.3, 1.4), (0.0, 0.05, 2.2), (-0.3, 0.32, 3.1), (0.38, 0.3, 4.4))])
        tube = cyl("TalkTube", (BOX.x + 0.12, BOX.y - 0.05, 0.06), 0.03, 0.12, pbr("PVC", (0.45, 0.45, 0.43), 0.4), 20)
        cap = cyl("TubeCap", (BOX.x + 0.12, BOX.y - 0.05, 0.125), 0.034, 0.025, pbr("PVCCap", (0.12, 0.12, 0.12), 0.45), 20)
        c["tube"] = tube


def lighting(c):
    L = c["light"]
    from common import sun
    w, s = rj.sky({"grey": "grey", "dusk": "dusk", "night": "night"}[L])
    if s is not None:
        bpy.data.objects.remove(s, do_unlink=True)
    if L == "grey":
        sun(22, 140, 1.4, (0.9, 0.93, 1.0), 12)          # overcast: a broad soft key through the canopy, dark fill
        haze((0, 0, 3.0), (70, 70, 6.0), density=0.022, color=(0.8, 0.84, 0.86), anis=0.45)
    elif L == "dusk":
        sun(4, 250, 0.6, (1.0, 0.55, 0.3), 3)
        haze((0, 0, 3.0), (70, 70, 6.0), density=0.015, color=(0.65, 0.7, 0.85), anis=0.45)
    else:
        mo = bpy.data.lights.new("Moon", 'SUN'); mo.energy = 0.04; mo.color = (0.55, 0.65, 1.0); mo.angle = math.radians(1)
        o = bpy.data.objects.new("Moon", mo); bpy.context.collection.objects.link(o); o.rotation_euler = (math.radians(50), 0, math.radians(30))
        haze((0, 0, 3.0), (70, 70, 6.0), density=0.008, color=(0.7, 0.75, 0.9), anis=0.5)


def probe_rod(name="Rod"):
    """A 1.6 m metal probing rod with a T handle. Origin at the tip; the rod runs along local +Z."""
    st = pbr("RodSteel", (0.5, 0.5, 0.52), 0.35, 1.0)
    parts = [cyl("RodShaft", (0, 0, 0.8), 0.007, 1.6, st, 10), cyl("RodT", (0, 0, 1.6), 0.012, 0.28, st, 10, rot=(0, math.radians(90), 0))]
    return join(parts, name)


def build(variant=None):
    variant = variant or "grey|officer"
    head = variant.split("|")[0]; L = head.split("+")[0]; extras = set(head.split("+")[1:])
    roles = []
    if "|" in variant:
        rp = variant.split("|")[1].split("+"); roles = [r for r in rp[0].split(",") if r]; extras |= set(rp[1:])
    c = dict(variant=variant, light=L, P={})
    build_woods(c)
    state = next((s for s in ("cover", "lid", "open", "spruces") if s in extras), "buried")
    box_top(c, "lid" if state == "open" else state)
    lighting(c)
    for r in roles:
        base = r if r in rj.ROLES else r.rstrip("0123456789")
        c["P"][r] = person(base, name=r.capitalize())
    c["rods"] = {}
    if "rods" in extras:
        for r in roles:
            c["rods"][r] = probe_rod("Rod_" + r)
    if "dog" in extras:
        c["dog"] = rj.dog("Dog")
    if "torch" in extras:
        t = rj.torch("LoneTorch", energy=45, cone=26)
        c["torch"] = t
    if "tape" in extras:
        cu = bpy.data.curves.new("MarkerTape", 'CURVE'); cu.dimensions = '3D'; cu.extrude = 0.025
        sp = cu.splines.new('POLY'); sp.points.add(11)
        tm = bpy.data.materials.new("Tape"); tm.use_nodes = True
        N = tm.node_tree.nodes; Lk = tm.node_tree.links; p = N["Principled BSDF"]
        tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(tc.outputs['Object'], sep.inputs[0])
        ad = N.new("ShaderNodeMath"); ad.operation = 'ADD'; Lk.new(sep.outputs['X'], ad.inputs[0]); Lk.new(sep.outputs['Y'], ad.inputs[1])
        mu = N.new("ShaderNodeMath"); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = 5.0; Lk.new(ad.outputs[0], mu.inputs[0])
        fr = N.new("ShaderNodeMath"); fr.operation = 'FRACT'; Lk.new(mu.outputs[0], fr.inputs[0])
        gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.5; Lk.new(fr.outputs[0], gt.inputs[0])
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; Lk.new(gt.outputs[0], mx.inputs['Factor'])
        mx.inputs[6].default_value = (0.75, 0.74, 0.7, 1); mx.inputs[7].default_value = (0.5, 0.03, 0.02, 1)
        Lk.new(mx.outputs[2], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.4
        o = bpy.data.objects.new("MarkerTape", cu); bpy.context.collection.objects.link(o); o.data.materials.append(tm)
        c["tape"] = o
    if state == "open":
        c["lid_hinge"].rotation_euler.y = 0.0
    rj.finish_scene()
    return c


# ============================================================================ actions
def stand_on(c, h, pos, face_z):
    rj.stand(h, Vector((pos[0], pos[1], 0)), face_z)
    h.arm.location.z += ground_z(c, pos[0], pos[1])


def walk_on(c, h, p0, p1, sec, speed=0.8, stride=22):
    m = walk(h, p0, p1, sec, speed=speed, stride=stride)
    h.arm.location.z += ground_z(c, h.arm.location.x, h.arm.location.y)
    return m


def probe(c, h, rod, sec, ph=0.0, stuck=False):
    """Two hands on the T handle, thrusting the rod into the ground in front of the feet."""
    fwd = forward(h); right = fwd.cross(Vector((0, 0, 1))).normalized()
    cyc = (sec * 0.8 + ph) % 1.0
    depth = 0.25 * math.sin(math.pi * min(1.0, cyc / 0.6)) if not stuck else 0.12
    tip = Vector(h.arm.location) + fwd * 0.55
    tip.z = ground_z(c, tip.x, tip.y) - depth
    rod.location = tip; rod.rotation_euler = ((-fwd).to_track_quat('Z', 'Y').to_euler()) if False else (0, 0, math.atan2(fwd.y, fwd.x))
    rod.rotation_euler.y = 0.0
    lean = Matrix.Rotation(math.radians(-12), 4, right)
    rod.matrix_world = Matrix.Translation(tip) @ lean @ Matrix.Rotation(math.atan2(fwd.y, fwd.x), 4, 'Z')
    top = tip + (lean.to_3x3() @ Vector((0, 0, 1.6)))
    for sd, sg in SIDE.items():
        reach(h, sd, top + right * sg * 0.09 * (1 if sd == "R" else -1) * -1 + Vector((0, 0, 0.0)), Vector((0, 0, -1)) + right * (0.6 if sd == "R" else -0.6), fwd + Vector((0, 0, -0.5)))
    fingers_curl(h, 60)
    side = fwd.cross(Vector((0, 0, 1))).normalized()
    h.rot("head", side, -18)


# --- 1A title: a line of officers stepping through misty spruce ; 1B: an officer ties marker tape between two trunks
LINE = ["officer", "officer2", "officer3", "officer4", "officer5"]


def anim_line(c, t, shot, dur):
    sec = t * dur
    roles = [r for r in LINE if r in c["P"]]
    for k, r in enumerate(roles):
        h = c["P"][r]; x0 = -10 + k * 2.6; y0 = -9 + (k % 2) * 0.5
        walk_on(c, h, (x0, y0), (x0 + 0.5, y0 + 9), sec + k * 0.4, speed=0.55, stride=20)
        side = forward(h).cross(Vector((0, 0, 1))).normalized(); h.rot("head", side, -14)
        h.rot("head", (0, 0, 1), 18 * math.sin(sec * 0.5 + k))
        if r in c["rods"]:
            probe(c, h, c["rods"][r], sec, ph=k * 0.37)
    if shot == "tape":
        h = c["P"]["officer"]
        stand_on(c, h, (-6.8, -2.0), math.radians(95))
        a = Vector((-6.15, -2.25, 1.15)); b = Vector((-2.0, -6.0, 1.05))
        k = ease(min(1.0, sec / (dur * 0.7)))
        fwd = forward(h); right = fwd.cross(Vector((0, 0, 1))).normalized()
        knot = a + Vector((0, 0, 0.02 * math.sin(sec * 6) * (1 - k)))
        reach(h, "L", knot + right * -0.05, Vector((0, 0, -1)) - right * 0.5, fwd)
        reach(h, "R", knot + right * 0.06 + Vector((0, 0, 0.03 * math.sin(sec * 5))), Vector((0, 0, -1)) + right * 0.5, fwd)
        fingers_curl(h, 40)
        sp = c["tape"].data.splines[0]
        for q, pt in enumerate(sp.points):
            f = q / (len(sp.points) - 1)
            pp = a.lerp(b, f) + Vector((0, 0, -0.18 * math.sin(math.pi * f) + 0.01 * math.sin(sec * 2 + q)))
            pt.co = (*pp, 1)
    rj.sway(c["trees"], sec, 0.004, 0.15)


def cam_line(c, t):
    e = ease(t)
    a = Vector((-3.5, 9.0, 1.6)); b = Vector((-3.0, 7.8, 1.55))
    return (a.lerp(b, e), Vector((-4.5, -4.0, 1.1)), 30)


def cam_tape(c, t):
    e = ease(t)
    a = Vector((-8.6, -4.0, 1.5)); b = Vector((-8.9, -3.4, 1.45))
    return (a.lerp(b, e), Vector((-6.0, -2.4, 1.1)), 38)


# --- 2A: low over the moss, a row of officers probing ; 2B: handler and dog through the ferns past the line
def anim_rods(c, t, shot, dur):
    sec = t * dur
    roles = [r for r in LINE if r in c["P"]]
    for k, r in enumerate(roles):
        h = c["P"][r]; x0 = -6 + k * 1.6
        walk_on(c, h, (x0, -6.0), (x0 + 0.1, -6.0 + 0.25 * sec), 0.0, speed=0.0)
        stand_on(c, h, (x0, -6.0 + 0.18 * sec), 0.0)
        h.arm.rotation_euler.z = math.pi                         # facing +Y (toward the clearing)
        probe(c, h, c["rods"][r], sec, ph=k * 0.29)
    if "dog" in c and "officer5" in c["P"]:
        h = c["P"]["officer5"]; dg = c["dog"]
        a = Vector((-9.0, -3.5)); b = Vector((3.0, -2.0))
        d = (b - a); u = d.normalized(); dist = min(d.length, sec * 1.15)
        dpos = a + u * (dist + 1.4)
        dg["root"].location = (dpos.x, dpos.y, ground_z(c, dpos.x, dpos.y)); dg["root"].rotation_euler.z = math.atan2(u.y, u.x)
        rj.dog_walk(dg, dist, sniff=0.9, sec=sec)
        walk_on(c, h, a, b, sec, speed=1.15)
    rj.sway(c["trees"], sec, 0.004, 0.15)


def cam_rods(c, t):
    e = ease(t)
    a = Vector((-8.5, -2.6, 0.35)); b = Vector((-7.6, -2.4, 0.4))
    return (a.lerp(b, e), Vector((-2.0, -5.0, 0.6)), 30)


def cam_rods_dog(c, t):
    e = ease(t)
    a = Vector((-4.0, 2.5, 1.0)); b = Vector((-2.5, 2.2, 1.0))
    return (a.lerp(b, e), c["dog"]["root"].location + Vector((0, 0, 0.4)), 35)


# --- 3A: a rod stops, the officer straightens and waves the others over ; 3B: they converge on the clearing
def anim_hit(c, t, shot, dur):
    sec = t * dur
    h = c["P"]["officer"]
    stand_on(c, h, (BOX.x - 0.75, BOX.y - 0.2), math.radians(-90 - 5))      # faces +X toward the box spot
    if shot == "hit":
        stuck = sec > 0.8
        if sec < 2.2:
            probe(c, h, c["rods"]["officer"], min(sec, 0.75), stuck=stuck)
        else:
            k = ease(min(1.0, (sec - 2.2) / 0.6))
            rod = c["rods"]["officer"]
            fwd = forward(h); right = fwd.cross(Vector((0, 0, 1))).normalized()
            reach(h, "L", rod.matrix_world @ Vector((0, 0, 1.45)), Vector((0, 0, -1)) - right * 0.5, fwd)
            # right arm up and waving over the head
            sh = h.bone_head("upperarm01.R")
            wv = math.sin((sec - 2.2) * 7.0)
            tgt = sh + Vector((0, 0, 0.45)) * k + right * (0.25 + 0.12 * wv * k) + fwd * 0.1
            reach(h, "R", tgt, right + Vector((0, 0, -0.4)), Vector((0, 0, 1)))
            side = fwd.cross(Vector((0, 0, 1))).normalized(); h.rot("head", (0, 0, 1), 50 * k)
    others = [r for r in ("officer2", "officer3", "officer4", "officer5") if r in c["P"]]
    for k, r in enumerate(others):
        hh = c["P"][r]; ang = 2.2 + k * 0.9
        p0 = Vector((BOX.x + math.cos(ang) * 11, BOX.y + math.sin(ang) * 11)); p1 = Vector((BOX.x + math.cos(ang) * 2.4, BOX.y + math.sin(ang) * 2.4))
        go = sec - (2.5 if shot == "hit" else 0.0)
        walk_on(c, hh, p0, p1, max(0.0, go) + (3.0 if shot == "converge" else 0.0), speed=1.5, stride=28)
    rj.sway(c["trees"], sec, 0.004, 0.15)


def cam_hit(c, t):
    e = ease(t)
    a = Vector((BOX.x - 4.2, BOX.y + 2.6, 1.3)); b = Vector((BOX.x - 3.8, BOX.y + 2.1, 1.35))
    return (a.lerp(b, e), Vector((BOX.x - 0.6, BOX.y - 0.2, 1.1)), 35)


def cam_converge(c, t):
    e = ease(t)
    a = Vector((BOX.x + 8, BOX.y + 7, 7.5)); b = Vector((BOX.x + 6.5, BOX.y + 6.0, 6.8))
    return (a.lerp(b, e), BOX + Vector((0, 0, 0.3)), 28)


# --- 4A: digging, the wooden cover appears ; 4B: sweeping the earth off the planks
def anim_dig(c, t, shot, dur):
    sec = t * dur
    k = ease(t)
    if "soil_skin" in c:
        c["soil_skin"].location.z = 0.0 - 0.05 * k if shot == "dig" else -0.06
        c["soil_skin"].scale = ((1 - 0.6 * k) if shot == "dig" else 0.35, 1.0 - (0.4 * k if shot == "dig" else 0.6), 1)
    diggers = [r for r in ("officer", "officer2", "officer3") if r in c["P"]]
    for j, r in enumerate(diggers):
        h = c["P"][r]; ang = [0.6, 2.4, 4.0][j]
        pos = Vector((BOX.x + math.cos(ang) * 1.05, BOX.y + math.sin(ang) * 0.95))
        dvec = Vector((BOX.x, BOX.y)) - pos
        stand_on(c, h, pos, math.atan2(dvec.x, -dvec.y))
        fwd = forward(h); right = fwd.cross(Vector((0, 0, 1))).normalized()
        cyc = (sec * 0.7 + j * 0.33) % 1.0
        lift = math.sin(math.pi * cyc)
        rj.rjp.bend_to(h, Vector(h.arm.location) + fwd * 0.6 + Vector((0, 0, 0.6 - 0.25 * lift)), frac=0.75, max_deg=30)
        tool = c["tools"][j]
        blade = Vector(h.arm.location) + fwd * (0.55 + 0.1 * lift); blade.z = ground_z(c, blade.x, blade.y) + 0.02 + 0.25 * lift
        top = blade + Vector((0, 0, 1.0)) - fwd * 0.45
        axis = (top - blade).normalized()
        tool.matrix_world = Matrix.Translation(blade) @ axis.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        reach(h, "R", blade.lerp(top, 0.92), Vector((0, 0, -1)) + right * 0.6, axis)
        reach(h, "L", blade.lerp(top, 0.55), Vector((0, 0, -1)) - right * 0.6, axis)
        fingers_curl(h, 60)
    for m in c.get("mound", []):
        m.scale.z = 0.25 + 0.15 * k
    rj.sway(c["trees"], sec, 0.004, 0.15)


def cam_dig(c, t):
    e = ease(t)
    a = BOX + Vector((-3.2, -2.6, 1.7)); b = BOX + Vector((-2.8, -2.2, 1.6))
    return (a.lerp(b, e), BOX + Vector((0, 0, 0.3)), 32)


def cam_sweep(c, t):
    e = ease(t)
    a = BOX + Vector((2.6, 1.6, 0.4)); b = BOX + Vector((2.2, 1.9, 0.45))
    return (a.lerp(b, e), BOX + Vector((0, 0, 0.15)), 35)


# --- 5A: track along the lid and its seven bolts ; 5B: an officer works a bolt with a crowbar (from behind)
def anim_lid(c, t, shot, dur):
    sec = t * dur
    if shot == "bolt":
        h = c["P"]["officer"]
        stand_on(c, h, (BOX.x + 1.05, BOX.y - 0.15), math.radians(90))         # faces -X toward the lid edge
        fwd = forward(h); right = fwd.cross(Vector((0, 0, 1))).normalized()
        rj.rjp.bend_to(h, BOX + Vector((0.45, -0.1, 0.25)), frac=0.7, max_deg=40)
        bar = c["crowbar"]; tip = BOX + Vector((0.47, -0.28 + 0.0, 0.03))
        pry = 0.15 * math.sin(sec * 2.2)
        top = tip + Vector((0.35, 0.05, 0.55 + pry)).normalized() * 0.75
        axis = (top - tip).normalized()
        bar.matrix_world = Matrix.Translation(tip) @ axis.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        reach(h, "R", tip.lerp(top, 0.9), Vector((0, 0, -1)) + right * 0.5, axis)
        reach(h, "L", tip.lerp(top, 0.55), Vector((0, 0, -1)) - right * 0.5, axis)
        fingers_curl(h, 60)
    for r in [r for r in ("officer2", "officer3") if r in c["P"]]:
        hh = c["P"][r]; k = 1 if r == "officer2" else -1
        stand_on(c, hh, (BOX.x - 0.4 + 0.3 * k, BOX.y + 1.4 * k), 0.0)
        dvec = BOX - hh.arm.location; hh.arm.rotation_euler.z = math.atan2(dvec.x, -dvec.y)
        side = forward(hh).cross(Vector((0, 0, 1))).normalized(); hh.rot("head", side, -22)
    rj.sway(c["trees"], sec, 0.004, 0.15)


def cam_lid(c, t):
    e = ease(t)
    a = BOX + Vector((-0.75, -0.75, 0.42)); b = BOX + Vector((0.75, -0.85, 0.45))
    return (a.lerp(b, e), BOX + Vector((-0.1 + 0.2 * e, 0.0, 0.0)), 35)


def cam_bolt(c, t):
    e = ease(t)
    a = BOX + Vector((2.8, -0.9, 1.45)); b = BOX + Vector((2.5, -0.7, 1.4))
    return (a.lerp(b, e), BOX + Vector((0.6, -0.15, 0.4)), 40)


# --- 6A: from far behind the trees, officers lift the lid; the camera stops at the treeline
#     6B: an officer steps back and takes off his cap; the camera turns away to the spruces
def anim_open(c, t, shot, dur):
    sec = t * dur
    lifters = [r for r in ("officer", "officer2") if r in c["P"]]
    ang = 0.0
    if shot == "lift":
        ang = math.radians(-70) * ease(min(1.0, max(0.0, (sec - 1.2) / 2.2)))
    else:
        ang = math.radians(-70)
    c["lid_hinge"].rotation_euler.y = ang
    for j, r in enumerate(lifters):
        h = c["P"][r]; k = 1 if j == 0 else -1
        pos = (BOX.x - 0.75, BOX.y + 0.32 * k)
        stand_on(c, h, pos, math.radians(-90))
        if shot == "lift":
            edge = c["lid_hinge"].matrix_world @ Vector((1.0, 0.32 * k * 0, 0.02)) if False else None
            hm = c["lid_hinge"].matrix_world
            e_ = hm @ Vector((0.95, 0.3 * k, 0.03))
            rj.rjp.bend_to(h, e_, frac=0.8, max_deg=35)
            fwd = forward(h); right = fwd.cross(Vector((0, 0, 1))).normalized()
            reach(h, "R", e_ + right * 0.08, Vector((0, 0, -1)) + right * 0.5, fwd)
            reach(h, "L", e_ - right * 0.08, Vector((0, 0, -1)) - right * 0.5, fwd)
    if shot == "cap":
        h = c["P"]["officer3"]
        back = ease(min(1.0, sec / 1.4))
        stand_on(c, h, (BOX.x + 1.2 + 0.7 * back, BOX.y + 0.9 + 0.4 * back), math.radians(-90 - 30))
        cap = h.cap; k = ease(min(1.0, max(0.0, (sec - 1.4) / 1.0)))
        fwd = forward(h); right = fwd.cross(Vector((0, 0, 1))).normalized()
        if k > 0:
            hd = h.bone_tail("head"); chest = rj.rjp.chest_point(h, 0.22, 0.25)
            hand = hd.lerp(chest, k) + Vector((0, 0, 0.02))
            reach(h, "R", hand, Vector((0, 0, -1)) + right * 0.7, fwd + Vector((0, 0, 0.5 * (1 - k))))
            cap.matrix_world = Matrix.Translation(h.bone_tail("wrist.R") + Vector((0, 0, 0.03))) @ h.arm.matrix_world.to_3x3().to_4x4() @ Matrix.Rotation(math.radians(-80 * k), 4, 'X')
        side = fwd.cross(Vector((0, 0, 1))).normalized(); h.rot("head", side, -20 * k)
    rj.sway(c["trees"], sec, 0.004, 0.15)


def cam_lift(c, t):
    e = ease(t)
    a = BOX + Vector((-17, 9, 1.55)); b = BOX + Vector((-14.5, 7.8, 1.55))
    return (a.lerp(b, e), BOX + Vector((0, 0, 0.6)), 50)


def cam_cap(c, t):
    e = ease(min(1.0, t * 1.15))
    h = c["P"]["officer3"]; p = Vector(h.arm.location)
    cam = BOX + Vector((4.6, 3.6, 1.5))
    t0 = p + Vector((0, 0, 1.5)); t1 = cam + Vector((-1.5, 4.0, 0.6))               # turns away to the spruces
    return (cam, t0.lerp(t1, ease(max(0.0, (t - 0.55) / 0.45))), 40)


# --- 12A / 12B: the five little spruces over the bare earth, the capped tube (dusk) ; 13A/B night ; 14A pull back (grey)
def anim_spruce(c, t, shot, dur):
    sec = t * dur
    for k, s in enumerate(c.get("saplings", [])):
        s.rotation_euler.x = 0.05 * math.sin(sec * 1.6 + k); s.rotation_euler.y = 0.04 * math.sin(sec * 1.2 + k * 1.3)
    if "torch" in c:
        tr = c["torch"]
        if shot == "torch_far":
            p = Vector((-14 + 1.4 * sec, 12 - 1.6 * sec, 1.1 + 0.05 * math.sin(sec * 5)))
        else:
            p = Vector((-8.5, 5.0, 1.0))
        tr.location = p
        aim = (BOX - p); aim.z = 0; aim.normalize(); aim.z = -0.35
        tr.rotation_euler = aim.normalized().to_track_quat('-Y', 'Z').to_euler()
    rj.sway(c["trees"], sec, 0.006, 0.18)


def cam_spr_orbit(c, t):
    a = math.radians(200 + 40 * ease(t)); r = 2.4
    return (BOX + Vector((r * math.cos(a), r * math.sin(a), 1.0)), BOX + Vector((0, 0, 0.15)), 35)


def cam_spr_low(c, t):
    e = ease(t)
    a = BOX + Vector((0.6, -0.75, 0.12)); b = BOX + Vector((0.45, -0.7, 0.14))
    return (a.lerp(b, e), BOX + Vector((-0.1, 0.25, 0.2)), 28)


def cam_torch_far(c, t):
    e = ease(t)
    a = BOX + Vector((3.5, -3.0, 1.2)); b = BOX + Vector((3.1, -2.6, 1.15))
    return (a.lerp(b, e), Vector((-9, 8, 1.2)), 45)


def cam_dark(c, t):
    e = ease(t)
    a = BOX + Vector((-2.5, 1.8, 1.0)); b = BOX + Vector((-2.2, 1.5, 0.95))
    return (a.lerp(b, e), BOX + Vector((0, 0, 0.2)), 32)


def cam_pull(c, t):
    e = ease(t)
    a = BOX + Vector((-3.0, 0.5, 1.5)); b = BOX + Vector((-11.0, 2.2, 1.6))
    return (a.lerp(b, e), BOX + Vector((0, 0, 0.3)), 32)


def _mk(shot, dur, cam, anim_fn, focus=None, dof=None, title=None):
    DUR[shot] = dur
    spec = dict(kind="anim", cam=cam, anim=lambda c, t: anim_fn(c, t, shot, dur))
    if focus:
        spec["focus"] = focus; spec["dof"] = dof or 4.0
    return spec


MOVES = {
    "line": _mk("line", 8.0, cam_line, anim_line),
    "tape": _mk("tape", 5.0, cam_tape, anim_line, lambda c, t: Vector((-6.15, -2.25, 1.15)), 2.8),
    "rods": _mk("rods", 5.0, cam_rods, anim_rods),
    "rods_dog": _mk("rods_dog", 4.5, cam_rods_dog, anim_rods, lambda c, t: c["dog"]["root"].location, 4.0),
    "hit": _mk("hit", 4.5, cam_hit, anim_hit),
    "converge": _mk("converge", 4.0, cam_converge, anim_hit),
    "dig": _mk("dig", 4.5, cam_dig, anim_dig),
    "sweep": _mk("sweep", 4.0, cam_sweep, anim_dig, lambda c, t: BOX, 2.8),
    "lid": _mk("lid", 4.5, cam_lid, anim_lid, lambda c, t: BOX, 2.4),
    "bolt": _mk("bolt", 4.5, cam_bolt, anim_lid),
    "lift": _mk("lift", 4.5, cam_lift, anim_open),
    "cap": _mk("cap", 5.0, cam_cap, anim_open),
    "spr_orbit": _mk("spr_orbit", 5.0, cam_spr_orbit, anim_spruce, lambda c, t: BOX, 2.8),
    "spr_low": _mk("spr_low", 4.5, cam_spr_low, anim_spruce, lambda c, t: BOX + Vector((0.12, -0.05, 0.12)), 1.8),
    "torch_far": _mk("torch_far", 5.0, cam_torch_far, anim_spruce),
    "dark": _mk("dark", 5.0, cam_dark, anim_spruce),
    "pull": _mk("pull", 5.5, cam_pull, anim_spruce),
}
G5 = "officer,officer2,officer3,officer4,officer5"
VARIANT_FOR = {"line": "grey|" + G5, "tape": "grey|officer,officer2,officer3,officer4+tape", "rods": "grey|" + "officer,officer2,officer3,officer4+rods",
               "rods_dog": "grey|officer,officer2,officer3,officer4,officer5+rods+dog", "hit": "grey|officer,officer2,officer3,officer4+rods",
               "converge": "grey|officer,officer2,officer3,officer4,officer5+rods", "dig": "grey|officer,officer2,officer3+cover+tools",
               "sweep": "grey|officer,officer2+cover+tools", "lid": "grey+lid", "bolt": "grey|officer,officer2,officer3+lid+crowbar",
               "lift": "grey|officer,officer2,officer3+open", "cap": "grey|officer,officer2,officer3+open",
               "spr_orbit": "dusk+spruces", "spr_low": "dusk+spruces", "torch_far": "night+spruces+torch", "dark": "night+spruces+torch",
               "pull": "grey+spruces"}

_build = build


def build(variant=None):                      # noqa: F811
    c = _build(variant)
    v = variant or ""
    if "tools" in v:
        c["tools"] = []
        for k in range(3):
            r_, ms = rj.model_fit("rusted_spade_01" if k != 1 else "wooden_broom", (0, 0, -50), height=1.1)
            c["tools"].append(r_)
    if "crowbar" in v:
        c["crowbar"], _ = rj.model_fit("crowbar_01", (0, 0, -50), height=0.75)
    if "dark" in v or True:
        pass
    return c
