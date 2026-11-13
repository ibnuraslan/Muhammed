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
    c["trees"] = rj.low_instances("birch", trees)
    c["trees"] += rj.ph_instances("shrub_02", [((x, -3.9, 0), x, 1.2) for x in (-7.5, 2.0, 5.5)])
    c["flowers"] = c["home"].get("flowers", [])
    village_east(c)


def village_east(c):
    """The lane runs on east through the village toward the lake: more houses and fences on both sides, garden trees,
    and the lake with its far wooded shore in haze at the end (the "lane" shot looks down it from behind her)."""
    more = [((46, -12, 0), math.pi, 14), ((61, -13, 0), math.pi, 15), ((76, -12, 0), math.pi, 16),
            ((40, 13, 0), 0.0, 17), ((56, 14, 0), 0.0, 18), ((71, 13, 0), 0.0, 19)]
    c["houses"] += [house_block(p, r, s_) for (p, r, s_) in more]
    fm = rj.mat("pine")
    for (a, b) in (((24, -3.2), (38, -3.2)), ((40, -3.2), (54, -3.2)), ((56, -3.2), (70, -3.2)),
                   ((-20, 3.2), (-2, 3.2)), ((0, 3.2), (18, 3.2)), ((20, 3.2), (36, 3.2)), ((38, 3.2), (52, 3.2)), ((54, 3.2), (70, 3.2))):
        fence_x(a, b, 0.95, fm)
    c["trees"] += rj.low_instances("birch", [((x, y, 0), x * 0.37, sc) for (x, y, sc) in
                                             ((22, -6, 1.1), (33, 7, 1.0), (44, -7, 1.2), (52, 6.5, 0.95), (63, -6.5, 1.05), (68, 7, 1.15), (79, -5, 1.2), (82, 6, 1.0))])
    c["trees"] += rj.ph_instances("shrub_02", [((x, y, 0), x, 1.1) for (x, y) in ((28, 3.9), (47, -3.9), (59, 3.9), (66, -3.9))])
    from sc_path import water_material
    box("LakeEast", (240, 0, -0.03), (300, 600, 0.02), water_material())           # the lake begins past the last gardens
    from kit import pbr
    hm = pbr("FarShore", (0.16, 0.20, 0.20), 0.9)                                      # far wooded shore, blued by distance
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=16, location=(900, 0, -10))
    hill = bpy.context.object; hill.name = "FarShore"; hill.scale = (60, 700, 34); hill.data.materials.append(hm)
    for k in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=12, location=(860, k * 420, -8))
        h2 = bpy.context.object; h2.scale = (50, 260, 26); h2.data.materials.append(hm)


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
    import look
    L = c["light"]
    if look.enabled():
        rj.sky("grey")
        az, el = {"afternoon": (70, 16), "garden": (115, 30)}.get(L, (140, 20))   # garden: from the side, over the house (gate shot)
        look.day_light("low_sun", azim=az, elev=el, sky="blue",
                       haze_box=((0, 0, 8), (160, 120, 16)), exposure=1.3)
        rj.sink_haze()
        return
    from common import sun
    w, s = rj.sky("grey" if L in ("grey", "morning") else "lowsun", rot=0)
    if s is not None:
        bpy.data.objects.remove(s, do_unlink=True)
    if L in ("afternoon", "garden"):
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
        c["fiat"] = vehicles.make("fiat600", loc=(GATE.x + 2.4, LANE_Y - 1.25, 0), heading_deg=180, color=(0.78, 0.6, 0.08))
        ex = box("Exhaust", (0, 0, 0), (0.5, 0.3, 0.3), None)
        em = bpy.data.materials.new("ExhaustVol"); em.use_nodes = True
        N = em.node_tree.nodes; Lk = em.node_tree.links; N.clear(); out = N.new("ShaderNodeOutputMaterial"); vol = N.new("ShaderNodeVolumePrincipled")
        tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 6
        Lk.new(tc.outputs['Object'], nz.inputs['Vector']); rj.driven(nz.inputs['W'], "default_value", "frame * 0.04")
        gr = N.new("ShaderNodeTexGradient"); gr.gradient_type = 'SPHERICAL'; Lk.new(tc.outputs['Object'], gr.inputs['Vector'])
        mu = N.new("ShaderNodeMath"); mu.operation = 'MULTIPLY'; Lk.new(nz.outputs['Fac'], mu.inputs[0]); Lk.new(gr.outputs['Fac'], mu.inputs[1])
        mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.12; mr.inputs['From Max'].default_value = 0.45; mr.inputs['To Max'].default_value = 3.0
        Lk.new(mu.outputs[0], mr.inputs['Value']); Lk.new(mr.outputs[0], vol.inputs['Density']); vol.inputs['Color'].default_value = (0.8, 0.8, 0.82, 1)
        Lk.new(vol.outputs[0], out.inputs['Volume']); ex.data.materials.append(em); c["exhaust"] = ex
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
    wheel_bike(c, h, bk, (GATE.x + 0.1, -6.3), (GATE.x + 0.1, 0.5), sec + 0.2, speed=0.85)
    for k, f in enumerate(c["flowers"][::3]):
        f.rotation_euler.x = 0.06 * math.sin(sec * 1.7 + k)
    rj.sway(c["trees"], sec, 0.01, 0.3)


def cam_gate(c, t):
    e = ease(t)
    a = Vector((GATE.x - 0.05, -7.3, 2.7)); b = Vector((GATE.x + 0.05, -7.2, 1.9))    # straight behind her, against the house wall (y -7.5): her back only
    g = c["P"]["sister"].bone_head("spine05")
    return (a.lerp(b, e), g + Vector((0.1, 2.5, -0.35)), 30)


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
    p = Vector(c["bike"]["root"].location)                                    # following behind her down the lane, eye level
    cam = p + Vector((-6.5 + 0.6 * e, 0.9, 1.55))
    return (cam, p + Vector((12.0, 0.2, 0.7)), 35)


# --- 16A: the postman cycles up the lane ; 16B: he drops the envelope in the gate box, a neighbour on her balcony
def anim_post(c, t, shot, dur):
    sec = t * dur
    h = c["P"]["postman"]; bk = c["pbike"]
    if shot == "post_ride":
        d = 3.3 * sec
        bk["root"].location = (-26 + d, LANE_Y + 0.9, 0.02); bk["root"].rotation_euler = (0, 0, 0)
        rj.roll_bike(bk, d); bpy.context.view_layer.update(); rj.ride_pose(h, bk, d)
        bag = c["postbag"]; bag.location = bk["root"].matrix_world @ Vector((-0.37, 0, 0.86)); bag.rotation_euler = (0, 0, 0)
        c["envelope"].location = (0, 0, -20)
    else:
        bk["root"].location = (GATE.x + 2.2, LANE_Y - 1.6, 0.0); bk["root"].rotation_euler = (math.radians(-12), 0, math.radians(180))
        c["postbag"].location = bk["root"].matrix_world @ Vector((-0.37, 0, 0.86))
        stand(h, Vector((GATE.x + 0.75, -2.55, 0)), math.pi)          # faces -Y toward the letterbox
        k = ease(min(1.0, sec / 2.2))
        slot = c["letterbox"].location + Vector((0, -0.11, 0.07))
        fwd = forward(h); right = fwd.cross(Vector((0, 0, 1))).normalized()
        start = rj.rjp.chest_point(h, 0.25, 0.3) + right * 0.15
        hand = start.lerp(slot + Vector((0, -0.03, 0.02)), k) if sec < 2.6 else start.lerp(slot, 0.3)
        reach(h, "R", hand, Vector((0, 0, -1)) + right * 0.5, fwd)
        env = c["envelope"]
        if sec < 2.6:
            env.location = h.bone_tail("wrist.R") + fwd * 0.08; env.rotation_euler = (0, 0, math.atan2(fwd.y, fwd.x) + math.pi / 2)
        else:
            env.location = (0, 0, -20)
        side = right; h.rot("head", side, -10)
    if "neighbour" in c["P"]:
        n = c["P"]["neighbour"]
        hb = c["houses"][4]
        stand(n, Vector((-9.0, 13 - 4.5 - 0.7, hb.get("balcony_z", 3.2) + 0.05)), math.pi)
        n.arm.location.z = hb.get("balcony_z", 3.2) + 0.05
        n.arm.rotation_euler.z = math.pi * 0 + math.radians(-160 + 15 * ease(t))
        fwd = forward(n); right = fwd.cross(Vector((0, 0, 1))).normalized()
        rail = n.arm.location + fwd * 0.5 + Vector((0, 0, 0.95))
        reach(n, "R", rail + right * 0.2, Vector((0, 0, -1)) + right, fwd); reach(n, "L", rail - right * 0.2, Vector((0, 0, -1)) - right, fwd)
    for k_, f in enumerate(c["flowers"][::3]):
        f.rotation_euler.x = 0.06 * math.sin(sec * 1.7 + k_)
    rj.sway(c["trees"], sec, 0.01, 0.3)


def cam_post_ride(c, t):
    e = ease(t)
    a = Vector((6.0, 4.6, 1.5)); b = Vector((5.2, 4.2, 1.45))
    return (a.lerp(b, e), c["pbike"]["root"].location + Vector((0, 0, 1.1)), 40)


def cam_post_box(c, t):
    e = ease(t)
    a = Vector((GATE.x + 3.4, 2.4, 1.7)); b = Vector((GATE.x + 2.9, 2.1, 1.75))
    return (a.lerp(b, e), Vector((GATE.x + 0.4, -3.0, 1.4)).lerp(Vector((-6.5, 6.0, 3.6)), ease(max(0, (t - 0.55) / 0.45))), 35)


# --- 21A: the yellow Fiat at the kerb, the father carries the suitcase to it ; 21B: he waits at the wheel, engine idling
def anim_fiat(c, t, shot, dur):
    sec = t * dur
    f = c["P"]["father"]; car = c["fiat"]; sc = c["suitcase"]
    if shot == "fiat_load":
        walk(f, (GATE.x + 0.05, -5.0), (GATE.x + 0.4, LANE_Y + 1.15), sec + 0.6, speed=1.0, stride=24)
        fwd = forward(f); right = fwd.cross(Vector((0, 0, 1))).normalized()
        hand = Vector(f.arm.location) + right * 0.28 + Vector((0, 0, 0.72))
        reach(f, "R", hand, Vector((0, 0, -1)) + right * 0.3, Vector((0, 0, -1)))
        sc.location = f.bone_tail("wrist.R") + Vector((0, 0, -0.5)); sc.rotation_euler = (0, 0, math.atan2(fwd.y, fwd.x))
        car.location.z = 0.0
    else:
        seat = car.matrix_world @ Vector((0.0, 0.33, 0.0))
        rj.sit_on(f, (seat.x, seat.y), car.rotation_euler.z + math.pi / 2, 0.36, lean=4, feet=0.55)
        fwd = forward(f); right = fwd.cross(Vector((0, 0, 1))).normalized()
        wheel = car.matrix_world @ Vector((0.6, 0.33, 0.78))
        reach(f, "L", wheel - right * 0.15, Vector((0, 0, -1)) - right * 0.4, fwd)
        reach(f, "R", wheel + right * 0.15, Vector((0, 0, -1)) + right * 0.4, fwd)
        sc.location = car.matrix_world @ Vector((-0.75, -0.05, 0.5)); sc.rotation_euler = (0, 0, car.rotation_euler.z)
        car.location.z = 0.004 * math.sin(sec * 35)                      # the idling engine shakes the little car
        if "exhaust" in c:
            c["exhaust"].location = car.matrix_world @ Vector((-1.75 - 0.05 * sec, -0.35, 0.3 + 0.03 * sec))
    rj.sway(c["trees"], sec, 0.01, 0.3)


def cam_fiat_load(c, t):
    e = ease(t)
    a = Vector((GATE.x + 4.6, LANE_Y + 3.2, 1.5)); b = Vector((GATE.x + 4.0, LANE_Y + 3.0, 1.45))
    return (a.lerp(b, e), Vector((GATE.x + 1.6, LANE_Y - 0.6, 0.9)), 32)


def cam_fiat_wide(c, t):
    e = ease(t)
    a = Vector((GATE.x - 4.0, LANE_Y + 8.5, 1.6)); b = Vector((GATE.x - 3.2, LANE_Y + 8.0, 1.55))
    return (a.lerp(b, e), c["fiat"].location + Vector((0, 0, 0.8)), 40)


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
    "post_ride": _mk("post_ride", 5.0, cam_post_ride, anim_post),
    "post_box": _mk("post_box", 5.0, cam_post_box, anim_post),
    "fiat_load": _mk("fiat_load", 5.0, cam_fiat_load, anim_fiat),
    "fiat_wide": _mk("fiat_wide", 5.0, cam_fiat_wide, anim_fiat),
}
VARIANT_FOR = {"gate": "garden|sister", "lane": "afternoon|sister", "post_ride": "grey|postman", "post_box": "grey|postman,neighbour",
               "fiat_load": "grey|father", "fiat_wide": "grey|father"}
