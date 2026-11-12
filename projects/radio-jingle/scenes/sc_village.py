"""VILLAGE: Eching am Ammersee, 1981. A lane of Bavarian houses (white plaster, shallow tiled gable roofs with deep
eaves, wooden balconies with red geraniums, painted shutters), garden fences, a gate with a letterbox.

  house_block(loc, rot_z, seed)   one house, front (balcony side) facing local -Y; returns dict(root, balcony_z, door)
  lane(c)                         the lane for the street shots
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import pbr, box, cyl, join, area_light, point_at, fabric
import rj
from rj import mat

DUR = {}


def _gable(name, w, d, z0, pitch_deg, over, m):
    """A gable roof along X (ridge along X), eaves overhanging by `over`. Returns the roof object."""
    import bmesh
    hw = w / 2 + over; hd = d / 2 + over; rise = math.tan(math.radians(pitch_deg)) * hd
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    th = 0.14
    V = lambda x, y, z: bm.verts.new((x, y, z))
    for sgn in (-1, 1):
        a = V(-hw, sgn * hd, z0); b = V(hw, sgn * hd, z0); c = V(hw, 0, z0 + rise); dd = V(-hw, 0, z0 + rise)
        a2 = V(-hw, sgn * hd, z0 + th); b2 = V(hw, sgn * hd, z0 + th); c2 = V(hw, 0, z0 + rise + th); d2 = V(-hw, 0, z0 + rise + th)
        for f in ((a, b, c, dd), (a2, d2, c2, b2), (a, a2, b2, b), (b, b2, c2, c), (dd, d2, a2, a)):
            bm.faces.new(f if sgn > 0 else f[::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    uv = bm.loops.layers.uv.new()
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); o.data.materials.append(m)
    return o, rise


def house_block(loc, rot_z=0.0, seed=1, w=11.0, d=9.0, floors=2, balcony=True, lit=0.0):
    rng = np.random.default_rng(seed)
    root = bpy.data.objects.new(f"House{seed}", None); bpy.context.collection.objects.link(root)
    pl = mat("plaster_ext"); wd = rj.mat("darkwood"); trim = mat("trim")
    fh = 2.8; H = floors * fh + 0.4
    parts = [box("HBody", (0, 0, H / 2), (w, d, H), pl)]
    base = pbr("Socle", (0.32, 0.31, 0.29), 0.85)
    parts.append(box("HSocle", (0, 0, 0.25), (w + 0.04, d + 0.04, 0.5), base))
    # upper storey timber cladding (common on Ammersee houses)
    parts.append(box("HClad", (0, 0, H - 0.6), (w + 0.03, d + 0.03, 1.2), mat("rawwood")))
    roof, rise = _gable("HRoof", w, d, H, 22, 1.4, mat("roof"))
    roof.rotation_euler = (0, 0, math.pi / 2)            # ridge along Y? keep the gable facing -Y
    roof.rotation_euler = (0, 0, 0)
    roof.rotation_euler.z = math.pi / 2
    # the gable faces -Y: ridge along Y
    gtri = []
    import bmesh
    me = bpy.data.meshes.new("Gable"); bm = bmesh.new()
    hw = w / 2; r2 = math.tan(math.radians(22)) * (w / 2)
    for sgn in (-1, 1):
        a = bm.verts.new((-hw, sgn * d / 2, H)); b = bm.verts.new((hw, sgn * d / 2, H)); c = bm.verts.new((0, sgn * d / 2, H + r2))
        bm.faces.new((a, b, c) if sgn < 0 else (c, b, a))
    bm.to_mesh(me); bm.free()
    gob = bpy.data.objects.new("Gable", me); bpy.context.collection.objects.link(gob); gob.data.materials.append(mat("rawwood"))
    sol = gob.modifiers.new("s", 'SOLIDIFY'); sol.thickness = 0.1
    # windows with shutters on the front and sides
    glass_m = mat("glass")
    win_lit = pbr("WinLit", (0.05, 0.04, 0.03), 0.3, 0.0, **{'Emission Color': (1.0, 0.7, 0.4, 1), 'Emission Strength': 0.0})
    shut = pbr(f"Shutter{seed}", [(0.10, 0.22, 0.12), (0.12, 0.09, 0.06), (0.25, 0.10, 0.07)][seed % 3], 0.55)
    win_parts = []
    for fl in range(floors):
        zc = 0.4 + fl * fh + 1.45
        for k in range(4):
            x = -w / 2 + w * (k + 0.5) / 4
            if fl == 0 and k == 1:
                continue                                             # the front door goes here
            for (fx, fy, along) in ((x, -d / 2, 'x'),):
                win_parts.append(box("HWinFrame", (fx, fy - 0.02, zc), (1.0, 0.06, 1.3), trim))
                win_parts.append(box("HWinDark", (fx, fy - 0.045, zc), (0.86, 0.02, 1.16), win_lit if rng.random() < lit else pbr("WinDark", (0.02, 0.022, 0.025), 0.1, 0.0, **{'Coat Weight': 1.0})))
                win_parts.append(box("HMull", (fx, fy - 0.06, zc), (0.05, 0.02, 1.16), trim))
                for s in (-1, 1):
                    win_parts.append(box("HShut", (fx + s * 0.78, fy - 0.05, zc), (0.5, 0.04, 1.3), shut))
        for k in range(3):                                               # side walls
            y = -d / 2 + d * (k + 0.5) / 3
            for sx in (-1, 1):
                win_parts.append(box("HWinS", (sx * (w / 2 + 0.02), y, zc), (0.06, 0.9, 1.2), trim))
                win_parts.append(box("HWinSD", (sx * (w / 2 + 0.045), y, zc), (0.02, 0.78, 1.08), pbr("WinDarkS", (0.02, 0.022, 0.025), 0.1)))
    door = box("HDoor", (-w / 2 + w * 1.5 / 4, -d / 2 - 0.03, 1.15), (1.1, 0.06, 2.2), wd)
    box("HDoorRoof", (-w / 2 + w * 1.5 / 4, -d / 2 - 0.55, 2.55), (1.8, 1.1, 0.08), mat("roof"), rot=(math.radians(-12), 0, 0))
    out = dict(root=root)
    if balcony and floors >= 2:
        bz = 0.4 + fh
        bal = [box("BalFloor", (0, -d / 2 - 0.65, bz), (w * 0.86, 1.3, 0.1), wd)]
        n = int(w * 0.86 / 0.13)
        for k in range(n):                                               # carved boards, the Bavarian balustrade
            x = -w * 0.43 + (k + 0.5) * w * 0.86 / n
            bal.append(box("BalBoard", (x, -d / 2 - 1.28, bz + 0.5), (0.11, 0.03, 0.9), wd))
        bal.append(box("BalRail", (0, -d / 2 - 1.28, bz + 0.97), (w * 0.86, 0.08, 0.06), wd))
        for sx in (-1, 1):
            bal.append(box("BalSide", (sx * w * 0.43, -d / 2 - 0.65, bz + 0.5), (0.06, 1.3, 0.9), wd))
        flowers = []
        geranium = pbr("Geranium", (0.55, 0.03, 0.03), 0.6, 0.0, **{'Sheen Weight': 0.4})
        leaf = pbr("GeraniumLeaf", (0.04, 0.12, 0.03), 0.6)
        for k in range(int(w * 0.86 / 0.9)):
            x = -w * 0.43 + 0.45 + k * 0.9
            bal.append(box("FlowerBox", (x, -d / 2 - 1.36, bz + 0.92), (0.8, 0.18, 0.16), shut))
            for q in range(10):
                bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=rng.uniform(0.05, 0.09),
                                                      location=(x + rng.uniform(-0.35, 0.35), -d / 2 - 1.36 + rng.uniform(-0.12, 0.05), bz + 1.05 + rng.uniform(-0.04, 0.14)))
                f = bpy.context.active_object; f.data.materials.append(geranium if q % 3 else leaf)
                d_ = f.modifiers.new("d", 'DISPLACE'); tx = bpy.data.textures.get("FlowerNoise") or bpy.data.textures.new("FlowerNoise", 'CLOUDS'); tx.noise_scale = 0.03
                d_.texture = tx; d_.strength = 0.04
                flowers.append(f)
        out["flowers"] = flowers
        out["balcony_z"] = bz
        for o in bal:
            o.parent = root
        for f in flowers:
            f.parent = root
    allp = parts + win_parts + [door, roof, gob]
    for o in allp:
        o.parent = root
    root.location = loc; root.rotation_euler = (0, 0, rot_z)
    out["door_local"] = Vector((-w / 2 + w * 1.5 / 4, -d / 2 - 0.1, 0))
    return out


def fence(a, b, h=1.0, m=None):
    m = m or rj.mat("pine")
    a = Vector(a); b = Vector(b); d = b - a; L = d.length; n = int(L / 0.12)
    ang = math.atan2(d.y, d.x)
    parts = []
    for k in range(n):
        p = a + d * ((k + 0.5) / n)
        parts.append(box("Picket", (p.x, p.y, h / 2), (0.08, 0.025, h), m))
    for z in (0.25, h - 0.2):
        mid = (a + b) / 2
        parts.append(box("FRail", (mid.x, mid.y, z), (L, 0.03, 0.07), m, rot=(0, 0, ang)))
    o = join(parts, "Fence")
    return o


# ============================================================================ the lane (Ch1 sets 2, 16, 21)
import ph
from common import ease
from rj import person, stand, walk, forward, upright, reach, fingers_curl, SIDE
import rj_vehicles  # noqa: F401  (registers fiat600, polizei_1981, helicopter_police, boat_police)
import vehicles

EXPOSURE = 0.0
BOUNCES = 5
HOUSE = Vector((0.0, -12.0, 0.0))          # the family house, front (balcony) facing the lane (+Y)
GATE = Vector((-2.4, -3.2, 0.0))           # garden gate in the fence along y = -3.2
LANE_Y = 0.0


def letterbox(loc):
    m = rj.pbr("LetterboxM", (0.10, 0.14, 0.10), 0.45, 0.3) if hasattr(rj, "pbr") else None
    from kit import pbr
    m = pbr("Letterbox", (0.12, 0.15, 0.11), 0.45, 0.3)
    parts = [box("LBox", (0, 0, 0), (0.36, 0.2, 0.3), m, bevel=0.01), box("LSlot", (0, -0.101, 0.07), (0.24, 0.004, 0.025), pbr("Slot", (0.01, 0.01, 0.01), 0.5)),
             box("LRoof", (0, 0, 0.165), (0.4, 0.24, 0.03), m, bevel=0.01, rot=(math.radians(6), 0, 0))]
    o = join(parts, "Letterbox"); o.location = loc
    return o


def lane(c):
    box("Lane", (0, LANE_Y, -0.02), (160, 4.6, 0.04), mat("asphalt"))
    for s in (-1, 1):
        box("Verge", (0, LANE_Y + s * 3.6, -0.03), (160, 2.6, 0.04), mat("gravel"))
    box("Gardens", (0, 0, -0.06), (200, 120, 0.04), mat("grass"))
    c["home"] = house_block(HOUSE, rot_z=math.pi, seed=1, lit=0.0)
    others = [((-16, -12, 0), math.pi, 2), ((16, -13, 0), math.pi, 4), ((-31, -11, 0), math.pi, 6), ((31, -12, 0), math.pi, 8),
              ((-9, 13, 0), 0.0, 9), ((8, 14, 0), 0.0, 10), ((24, 13, 0), 0.0, 12), ((-25, 14, 0), 0.0, 13)]
    c["houses"] = [house_block(p, r, s) for (p, r, s) in others]
    # fences with the gate gap, the letterbox on the gate post
    fm = rj.mat("pine")
    for (a, b) in (((-8, -3.2), (GATE.x - 0.6, -3.2)), ((GATE.x + 0.6, -3.2), (8, -3.2)), ((-24, -3.2), (-9, -3.2)), ((9, -3.2), (23, -3.2))):
        fence_x(a, b, 0.95, fm)
    for x in (GATE.x - 0.6, GATE.x + 0.6):
        box("GatePost", (x, -3.2, 0.6), (0.12, 0.12, 1.2), rj.mat("darkwood"))
    c["gate"] = gate_leaf(GATE + Vector((-0.55, 0, 0)), 1.1, fm)
    c["letterbox"] = letterbox((GATE.x + 0.6, -3.2 - 0.17, 1.05))
    box("GardenPath", (GATE.x, -7.5, -0.01), (1.2, 8.4, 0.03), mat("gravel"))
    trees = [((x, y, 0), x * 0.7, s) for (x, y, s) in ((-6, -6, 1.0), (6.5, -7, 1.15), (-13, 6, 1.1), (14, 6, 0.95), (36, -4, 1.1), (-38, 5, 1.2), (3, 8, 0.9))]
    c["trees"] = rj.ph_instances("tree_small_02", trees)
    c["trees"] += rj.ph_instances("shrub_02", [((x, -3.9, 0), x, 1.2) for x in (-7, -5.2, 1.0, 3.2, 5.5)])
    c["flowers"] = c["home"].get("flowers", [])


def fence_x(a, b, h, m):
    a = Vector((a[0], a[1], 0)); b = Vector((b[0], b[1], 0)); L_ = (b - a).length; n = max(1, int(L_ / 0.13))
    parts = [box("Picket", (a.x + (b.x - a.x) * (k + 0.5) / n, a.y, h / 2), (0.085, 0.022, h), m) for k in range(n)]
    for z in (0.25, h - 0.2):
        parts.append(box("FRail", ((a.x + b.x) / 2, a.y + 0.03, z), (L_, 0.03, 0.07), m))
    return join(parts, "Fence")


def gate_leaf(hinge, w, m):
    e = bpy.data.objects.new("GateHinge", None); bpy.context.collection.objects.link(e); e.location = hinge
    n = int(w / 0.13)
    parts = [box("GPicket", (hinge.x + w * (k + 0.5) / n, hinge.y, 0.5), (0.085, 0.022, 0.95), m) for k in range(n)]
    for z in (0.25, 0.75):
        parts.append(box("GRail", (hinge.x + w / 2, hinge.y + 0.03, z), (w, 0.03, 0.07), m))
    g = join(parts, "Gate"); g.parent = e; g.matrix_parent_inverse = e.matrix_world.inverted()
    return e


def light(c):
    L = c["light"]
    from common import sun
    w, s = rj.sky("grey" if L in ("grey", "morning") else "lowsun", rot=0)
    if s is not None:
        bpy.data.objects.remove(s, do_unlink=True)
    if L == "afternoon":
        sun(22, 210, 3.5, (1.0, 0.78, 0.55), 1.5)            # low warm afternoon key across the lane
    else:
        sun(18, 160, 1.6, (0.85, 0.9, 1.0), 8)               # grey morning: a soft cool key, dark fill


def build(variant=None):
    variant = variant or "afternoon|sister"
    L = variant.split("|")[0]; roles = variant.split("|")[1].split(",") if "|" in variant else []
    c = dict(variant=variant, light=L, P={})
    lane(c)
    light(c)
    for r in roles:
        c["P"][r] = person(r)
    if "sister" in roles:
        c["bike"] = rj.bicycle("Bike")
    if "postman" in roles:
        c["pbike"] = rj.bicycle("PostBike", frame_m=rj.pbr("PostYellow", (0.75, 0.55, 0.02), 0.35, 0.1, **{'Coat Weight': 0.6}) if hasattr(rj, "pbr") else None)
        from kit import pbr
        bag = box("PostBag", (0, 0, 0), (0.36, 0.16, 0.28), pbr("PostBag", (0.12, 0.09, 0.06), 0.7), bevel=0.02)
        c["postbag"] = bag
        c["envelope"] = box("Envelope", (0, 0, 0), (0.22, 0.005, 0.11), pbr("EnvelopePaper", (0.78, 0.74, 0.62), 0.8))
    if "neighbour" in roles:
        pass
    if "father" in roles and L in ("grey", "morning"):
        c["fiat"] = vehicles.make("fiat600", loc=(GATE.x + 3.2, 2.6 + LANE_Y - 0.6, 0), heading_deg=180, color=(0.78, 0.6, 0.08))
        from kit import pbr
        c["suitcase"], _ = rj.model_fit("vintage_suitcase", (0, 0, -50), height=0.45)
    rj.finish_scene()
    return c


# --- 2A: the gate; 2B: the lane (afternoon, the sister with the red bicycle, seen from behind / far)
def wheel_bike(c, h, bk, p0, p1, sec, speed=0.9):
    """Walk beside the bike (bike on her right), pushing it by the handlebar."""
    moving = walk(h, p0, p1, sec, speed=speed, stride=22)
    fwd = forward(h); right = fwd.cross(Vector((0, 0, 1))).normalized()
    hp = h.arm.location + right * 0.42
    hd = math.atan2(fwd.y, fwd.x)
    bk["root"].location = (hp.x, hp.y, 0.0); bk["root"].rotation_euler = (0, 0, hd)
    rj.roll_bike(bk, (Vector(h.arm.location) - Vector((p0[0], p0[1], 0))).length)
    bpy.context.view_layer.update()
    rw = bk["root"].matrix_world
    # bike on her right: left hand on the near (left) grip, right hand on the saddle
    reach(h, "L", rw @ (bk["bars"] + Vector((0, 0.28, 0))), Vector((0, 0, -1)) - right * 0.3 - fwd * 0.3, fwd)
    reach(h, "R", rw @ (bk["saddle"] + Vector((0, 0, 0.03))), Vector((0, 0, -1)) + right * 0.3 - fwd * 0.2, fwd + Vector((0, 0, -0.6)))
    fingers_curl(h, 45)


def anim_gate(c, t, shot, dur):
    sec = t * dur
    h = c["P"]["sister"]; bk = c["bike"]
    c["gate"].rotation_euler.z = math.radians(-80) * ease(min(1, sec / 0.8))
    wheel_bike(c, h, bk, (GATE.x + 0.1, -6.6), (GATE.x + 0.1, -0.4), sec + 1.2, speed=0.85)
    for k, f in enumerate(c["flowers"][::3]):
        f.rotation_euler.x = 0.06 * math.sin(sec * 1.7 + k)
    rj.sway(c["trees"], sec, 0.01, 0.3)


def cam_gate(c, t):
    e = ease(t)
    a = Vector((GATE.x + 5.5, 4.2, 5.2)); b = Vector((GATE.x + 4.6, 3.6, 1.7))      # crane down the house front
    tgt = Vector((GATE.x + 0.2, -6.0, 3.5)).lerp(Vector((GATE.x, -3.6, 0.9)), e)
    return (a.lerp(b, e), tgt, 30)


def anim_lane(c, t, shot, dur):
    sec = t * dur
    h = c["P"]["sister"]; bk = c["bike"]
    d = 2.0 + 3.6 * sec
    bk["root"].location = (GATE.x + 0.5 + d, LANE_Y - 0.8, 0.02); bk["root"].rotation_euler = (0, 0, 0)
    rj.roll_bike(bk, d)
    bpy.context.view_layer.update()
    rj.ride_pose(h, bk, d)
    c["gate"].rotation_euler.z = math.radians(-80)
    rj.sway(c["trees"], sec, 0.01, 0.3)


def cam_lane(c, t):
    e = ease(t)
    a = Vector((GATE.x - 1.5, -5.2, 1.5)); b = Vector((GATE.x - 1.2, -4.9, 1.45))
    tgt = c["bike"]["root"].location + Vector((0, 0, 0.8))
    return (a.lerp(b, e), tgt, 85)


def _mk(shot, dur, cam, anim_fn, focus=None, dof=None):
    DUR[shot] = dur
    spec = dict(kind="anim", cam=cam, anim=lambda c, t: anim_fn(c, t, shot, dur))
    if focus:
        spec["focus"] = focus; spec["dof"] = dof or 4.0
    return spec


def _f_girl(c, t):
    return c["P"]["sister"].bone_head("spine05")


MOVES = {
    "gate": _mk("gate", 6.5, cam_gate, anim_gate, _f_girl, 4.0),
    "lane": _mk("lane", 5.5, cam_lane, anim_lane, _f_girl, 8.0),
}
VARIANT_FOR = {"gate": "afternoon|sister", "lane": "afternoon|sister"}
