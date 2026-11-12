"""CH1 SET 11B (dramatization): night rain outside the lit glass lobby of a modern Singapore office tower (generic, no
logos). A white police hatchback with a blue band and light bar (vehicles.py, police_fr) pulls up at the kerb and stops;
the driver's door opens, two officers in dark-blue uniforms step out and head for the lobby. Low, slow camera on the
wet road; the light bar flashes by frame drivers (plays in any render).

Singapore drives on the left: the car runs along +X with the kerb on its left (+Y); the driver sits on the right,
on the camera side (-Y)."""
import math
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
from kit import *
from sc_home import facade
from sc_street import wet_asphalt
from human import Human, add_asset, pose_walk, fingers_curl, _world_verts
import vehicles
import ph

EXPOSURE = 0.35
DUR = {"pull_up": 6.0}      # car stops ~2.4 s, door ~2.5-3.3 s, officers out and walking to the end

KERB_Y = 4.0               # road side face of the kerb
GLASS_Y = 10.0             # lobby glass line
CAR_Y = 2.75               # car centre line when parked
STOP_X = 0.0
STOP_T = 2.4
START_X = -15.0
PAVE_Z = 0.15


# ============================================================================ the door: cut out of the one-piece body shell
def _in_front_door(x, z):
    if z < 0.37 or z > 1.415:
        return False
    xf = 0.90 if z < 0.99 else 0.92 - (z - 0.99) * (0.72 / 0.415)       # A-pillar slope above the waist
    return -0.49 < x < xf


def split_door(root, side):
    """Cut the front door (side -1 = right/driver, +1 = left) out of the hatch body into a child hinged at its front
    edge. Keeps the mesh in body-local coordinates so the object-space paint masks (glass, livery) stay put."""
    body = root
    if body.data.users > 1:
        body.data = body.data.copy()
    me = body.data
    bm = bmesh.new(); bm.from_mesh(me)
    sel = []
    for f in bm.faces:
        c = f.calc_center_median()
        if side * c.y > 0.6 and side * f.normal.y > 0.25 and _in_front_door(c.x, c.z):
            sel.append(f.index)
    sel = set(sel)
    door_bm = bm.copy()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index in sel], context='FACES')
    bm.to_mesh(me); bm.free()
    door_bm.faces.ensure_lookup_table()
    bmesh.ops.delete(door_bm, geom=[f for f in door_bm.faces if f.index not in sel], context='FACES')
    dme = bpy.data.meshes.new("DoorMesh"); door_bm.to_mesh(dme); door_bm.free()
    for m in me.materials:
        if m.name not in [x.name for x in dme.materials]:
            pass
    dme.materials.clear()
    for m in me.materials:
        dme.materials.append(m)
    hinge = bpy.data.objects.new(f"DoorHinge{side}", None); bpy.context.collection.objects.link(hinge)
    hinge.parent = body; hinge.location = (0.9, side * 0.86, 0.8)
    door = bpy.data.objects.new(f"Door{side}", dme); bpy.context.collection.objects.link(door)
    door.parent = hinge; door.location = (-0.9, -side * 0.86, -0.8)
    door.color = body.color
    for k in ("dirt", "lamps"):
        if k in body.keys():
            door[k] = body[k]
    # the livery text crosses the door gap: the part on the front door goes with it
    for ch in list(body.children):
        if ch.name.startswith("Txt") and ch.type == 'MESH' and side * (ch.matrix_local.translation.y + sum(v.co.y for v in ch.data.vertices) / max(1, len(ch.data.vertices))) > 0:
            if ch.data.users > 1:
                ch.data = ch.data.copy()
            tb = bmesh.new(); tb.from_mesh(ch.data)
            on = [f for f in tb.faces if f.calc_center_median().x > -0.49]
            tdb = tb.copy(); ids = set(f.index for f in on)
            bmesh.ops.delete(tb, geom=on, context='FACES'); tb.to_mesh(ch.data); tb.free()
            tdb.faces.ensure_lookup_table()
            bmesh.ops.delete(tdb, geom=[f for f in tdb.faces if f.index not in ids], context='FACES')
            tme = bpy.data.meshes.new("DoorTxt"); tdb.to_mesh(tme); tdb.free()
            for m in ch.data.materials:
                tme.materials.append(m)
            t2 = bpy.data.objects.new("DoorTxt", tme); bpy.context.collection.objects.link(t2)
            t2.parent = door; t2.matrix_parent_inverse = Matrix.Identity(4); t2.matrix_basis = ch.matrix_basis.copy()
    return hinge


# ============================================================================ set
def paver_mat(name):
    """Wet granite pavers, 0.3 m grid."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]; tc = N.new("ShaderNodeTexCoord")
    br = N.new("ShaderNodeTexBrick"); br.inputs['Scale'].default_value = 1.0; br.offset = 0.5
    br.inputs['Brick Width'].default_value = 0.6; br.inputs['Row Height'].default_value = 0.3; br.inputs['Mortar Size'].default_value = 0.006
    br.inputs['Color1'].default_value = (0.09, 0.09, 0.095, 1); br.inputs['Color2'].default_value = (0.07, 0.07, 0.075, 1)
    br.inputs['Mortar'].default_value = (0.02, 0.02, 0.02, 1)
    L.new(tc.outputs['Object'], br.inputs['Vector']); L.new(br.outputs['Color'], p.inputs['Base Color'])
    rr = N.new("ShaderNodeMapRange"); rr.inputs['To Min'].default_value = 0.06; rr.inputs['To Max'].default_value = 0.3
    L.new(br.outputs['Fac'], rr.inputs['Value']); L.new(rr.outputs[0], p.inputs['Roughness'])
    p.inputs['Coat Weight'].default_value = 0.6; p.inputs['Coat Roughness'].default_value = 0.04
    return m


def officer(name, years, hair):
    h = Human(name, gender=1.0, years=years, muscle=0.6, weight=0.45, height=0.55, eyelashes="eyelashes01",
              skin="middleage_lightskinned_male_diffuse.png")
    add_asset(h, "clothes", "male_worksuit01", tint=(0.3, 0.4, 0.85), sat=0.15, val=0.2, rough=0.6)
    add_asset(h, "clothes", "shoes02", val=0.08, rough=0.3)
    add_asset(h, "hair", hair, val=0.08, rough=0.45)
    return h


def place(h, xy, face, z=0.0, phase=None):
    """Standing (phase None) or walking; face = rotation z (0 faces -Y, pi/2 faces +X, pi faces +Y)."""
    bob = pose_walk(h, phase or 0.0, stride=0.0 if phase is None else 24, arm_swing=0.0 if phase is None else 14)
    h.arm.rotation_euler = (0, 0, face); h.arm.location = (xy[0], xy[1], z + h.foot0 + (bob if phase is not None else 0.0))
    bpy.context.view_layer.update()


def build(variant=None):
    c = {}
    world_flat((0.006, 0.008, 0.014), 1.0)
    # ---------------------------------------------------------------- street
    road = wet_asphalt("Road")
    box("Road", (0, -3.0, -0.05), (220, 14, 0.1), road)
    paint = pbr("RoadPaint", (0.75, 0.75, 0.72), 0.35, **{'Coat Weight': 0.5, 'Coat Roughness': 0.05})
    yel = pbr("YellowLine", (0.75, 0.55, 0.06), 0.35, **{'Coat Weight': 0.5, 'Coat Roughness': 0.05})
    for k in range(-14, 14):                                       # dashed lane line
        box("Dash", (k * 6.0, -0.6, 0.002), (3.0, 0.12, 0.004), paint)
    for yy in (KERB_Y - 0.22, KERB_Y - 0.38):                      # double yellow along the kerb
        box("Yellow", (0, yy, 0.002), (220, 0.1, 0.004), yel)
    granite = pbr("Kerb", (0.32, 0.31, 0.3), 0.3, 0.0, **{'Coat Weight': 0.6, 'Coat Roughness': 0.05})
    box("Kerb", (0, KERB_Y + 0.15, PAVE_Z / 2), (220, 0.3, PAVE_Z), granite, bevel=0.025)
    box("Pavement", (0, (KERB_Y + 0.3 + GLASS_Y + 6) / 2, PAVE_Z / 2 - 0.01), (220, GLASS_Y + 6 - KERB_Y - 0.3, PAVE_Z - 0.02), paver_mat("Pavers"))
    # ---------------------------------------------------------------- tower lobby: double-height glass, canopy, warm interior
    gl = glass("LobbyGlass", (0.88, 0.92, 0.94), 0.0)
    box("LobbyGlass", (0, GLASS_Y, 3.2), (26, 0.025, 6.4), gl)
    mull = pbr("Mullion", (0.1, 0.105, 0.11), 0.3, 0.9)
    for k in range(14):
        box("Mullion", (-13 + k * 2.0, GLASS_Y, 3.2), (0.06, 0.22, 6.4), mull)
    box("Transom", (0, GLASS_Y, 3.0), (26, 0.18, 0.06), mull)
    box("Sill", (0, GLASS_Y, PAVE_Z + 0.03), (26, 0.3, 0.06), mull)
    stone = pbr("LobbyFloor", (0.62, 0.6, 0.56), 0.12, 0.0, **{'Coat Weight': 0.5, 'Coat Roughness': 0.04})
    box("LobbyFloor", (0, GLASS_Y + 6, PAVE_Z - 0.01), (26, 12, 0.02), stone)
    wd = wood("LobbyWood", dark=(0.12, 0.065, 0.03), light=(0.3, 0.17, 0.08), scale=(1, 30, 30), rough=0.35, coat=0.3)
    box("LobbyBack", (0, GLASS_Y + 9.0, 3.2), (26, 0.2, 6.4), wd)
    box("LobbyCeil", (0, GLASS_Y + 4.5, 6.45), (26, 9.2, 0.1), pbr("LobbyCeil", (0.7, 0.68, 0.64), 0.8))
    desk = pbr("DeskStone", (0.78, 0.76, 0.72), 0.2, 0.0, **{'Coat Weight': 0.4})
    box("Desk", (2.5, GLASS_Y + 6.5, 0.55 + PAVE_Z), (4.0, 0.8, 1.1), desk, bevel=0.03)
    box("DeskTop", (2.5, GLASS_Y + 6.45, 1.12 + PAVE_Z), (4.1, 0.9, 0.04), pbr("DeskTopDark", (0.05, 0.05, 0.05), 0.2), bevel=0.01)
    ph.model("sofa_02", loc=(-4.5, GLASS_Y + 4.0, PAVE_Z), rot_z=math.radians(180))
    ph.model("modern_coffee_table_02", loc=(-4.5, GLASS_Y + 2.8, PAVE_Z))
    for x in (-8.0, 7.5):
        ph.model("potted_plant_02", loc=(x, GLASS_Y + 1.2, PAVE_Z), scale=1.6)
    for x in np.arange(-11, 12, 2.5):                                          # warm interior: lights you don't see
        l = bpy.data.lights.new("LobbyL", 'AREA'); l.energy = 260; l.size = 1.6; l.color = (1.0, 0.82, 0.6)
        o = bpy.data.objects.new("LobbyL", l); bpy.context.collection.objects.link(o); o.location = (x, GLASS_Y + 4.5, 6.3)
        o.visible_camera = False
    for x in np.arange(-10, 11, 4.0):                                          # wall washers on the wood
        l = bpy.data.lights.new("Wash", 'SPOT'); l.energy = 300; l.spot_size = math.radians(70); l.spot_blend = 0.8; l.color = (1.0, 0.78, 0.5)
        o = bpy.data.objects.new("Wash", l); bpy.context.collection.objects.link(o); o.location = (x, GLASS_Y + 8.3, 6.2)
        point_at(o, (x, GLASS_Y + 8.9, 1.0))
    # tower above: dark curtain wall with a few lit floors, rising out of frame
    tw = facade("TowerNight", (0.03, 0.04, 0.05), (0.14, 0.15, 0.16), floor=4.0, bay=1.6, lit_frac=0.12, refl=0.4)
    box("Tower", (0, GLASS_Y + 12, 6.4 + 120), (40, 24, 240), tw)
    # entrance canopy with recessed downlights
    can = pbr("Canopy", (0.12, 0.12, 0.13), 0.35, 0.8)
    box("Canopy", (0, GLASS_Y - 2.2, 4.6), (12, 4.4, 0.25), can, bevel=0.02)
    rim = pbr("DLRim", (0.6, 0.6, 0.62), 0.3, 1.0)
    for k in range(5):
        for j in range(2):
            x, y = -4.8 + k * 2.4, GLASS_Y - 3.3 + j * 2.0
            cyl("DLCan", (x, y, 4.47), 0.09, 0.02, rim, verts=24)
            cyl("DLLens", (x, y, 4.462), 0.07, 0.004, emissive("DLLens", (1.0, 0.86, 0.66), 6.0), verts=24)
            l = bpy.data.lights.new("CanopyL", 'SPOT'); l.energy = 260; l.spot_size = math.radians(90); l.spot_blend = 0.7
            l.color = (1.0, 0.85, 0.65); l.shadow_soft_size = 0.06
            o = bpy.data.objects.new("CanopyL", l); bpy.context.collection.objects.link(o); o.location = (x, y, 4.44)
    # palms in planters along the pavement (scanned tree)
    root, ms = ph.model("island_tree_02", loc=(0, 0, -300))
    lo, hi = ph.bounds(ms)
    sc = 7.5 / max(hi.z - lo.z, 0.1)
    rng = np.random.default_rng(7)
    planter = pbr("Planter", (0.3, 0.3, 0.29), 0.5)
    soil = pbr("Soil", (0.03, 0.025, 0.02), 0.9)
    for x in (-8.0, 8.5, 21.0):
        cyl("Planter", (x, KERB_Y + 1.6, PAVE_Z + 0.25), 0.8, 0.5, planter, verts=48)
        cyl("Soil", (x, KERB_Y + 1.6, PAVE_Z + 0.46), 0.74, 0.04, soil, verts=48)
        instance(ms[0], (x, KERB_Y + 1.6, PAVE_Z + 0.45), rot=(0, 0, rng.uniform(0, 6.28)), scale=(sc, sc, sc))
    # street lamps on the kerb, warm
    pole = pbr("Pole", (0.05, 0.05, 0.055), 0.4, 0.8)
    for x in (-14, 6.5):
        cyl("LampPole", (x, KERB_Y + 0.6, 4.0), 0.07, 8.0, pole, verts=16)
        box("LampArm", (x, KERB_Y - 0.3, 7.95), (0.12, 1.8, 0.1), pole, bevel=0.03)
        l = bpy.data.lights.new("Street", 'SPOT'); l.energy = 1500; l.spot_size = math.radians(110); l.spot_blend = 0.6; l.color = (1.0, 0.72, 0.45)
        o = bpy.data.objects.new("Street", l); bpy.context.collection.objects.link(o); o.location = (x, KERB_Y - 1.1, 7.85)
    sky = bpy.data.lights.new("CityGlow", 'AREA'); sky.energy = 9000; sky.size = 40; sky.color = (0.45, 0.55, 0.8)
    so = bpy.data.objects.new("CityGlow", sky); bpy.context.collection.objects.link(so); so.location = (0, -20, 25); point_at(so, (0, 3, 0))
    # ---------------------------------------------------------------- the police car (shared vehicle kit)
    car = vehicles.make("sedan_modern", loc=(START_X, CAR_Y - 0.5, 0), heading_deg=0, variant="police_fr", lamps=True, real_lights=True)
    c["car"] = car
    for ch in car.children:                               # the word sits wholly on the front doors (it crossed the gap)
        if ch.name.startswith("Txt") and ch.type == 'MESH':
            if ch.data.users > 1:
                ch.data = ch.data.copy()
            ch.data.transform(Matrix.Translation((0.08, 0, 0)))
    c["door_r"] = split_door(car, -1)                     # driver (right, camera side)
    c["door_l"] = split_door(car, +1)                     # passenger (kerb side)
    # ---------------------------------------------------------------- two officers
    offs = []
    for nm, yrs, hr in (("OfficerA", 34, "short02"), ("OfficerB", 29, "short04")):
        h = officer(nm, yrs, hr)
        pose_walk(h, 0.0, stride=0.0, arm_swing=0.0); h.arm.location = (0, 0, 0); bpy.context.view_layer.update()
        w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
        h.foot0 = -float(w[:, 2].min())
        offs.append(h)
    c["offA"], c["offB"] = offs
    # ---------------------------------------------------------------- rain: falling streak curtains
    rm = bpy.data.materials.new("Rain"); rm.use_nodes = True
    N = rm.node_tree.nodes; L = rm.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (30 * 50, 8 * 3.0, 1)
    wn = N.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = '2D'
    L.new(tc.outputs['Object'], mp.inputs['Vector']); L.new(mp.outputs[0], wn.inputs['Vector'])
    gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.95; L.new(wn.outputs['Value'], gt.inputs[0])
    sc_ = N.new("ShaderNodeMath"); sc_.operation = 'MULTIPLY'; sc_.inputs[1].default_value = 0.3; L.new(gt.outputs[0], sc_.inputs[0])
    tr = N.new("ShaderNodeBsdfTransparent"); em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (0.8, 0.84, 0.9, 1); em.inputs['Strength'].default_value = 0.45
    mx = N.new("ShaderNodeMixShader"); L.new(sc_.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs['Surface'])
    rain = []
    for k, y in enumerate((-1.5, 1.0, 5.5, 8.0)):
        for j in range(2):
            bpy.ops.mesh.primitive_plane_add(size=1, location=(0, y, 4 + j * 8), rotation=(math.radians(90), 0, 0))
            o = bpy.context.active_object; o.name = "Rain"; o.scale = (30, 8, 1); o.data.materials.append(rm)
            o.visible_shadow = False; o.visible_diffuse = False; o.visible_glossy = False
            rain.append((o, y, j))
    c["rain"] = rain
    anim_pull(c, 0.0)
    return c


# ============================================================================ animation
def _car_x(sec):
    if sec >= STOP_T:
        return STOP_X
    u = 1 - sec / STOP_T
    return STOP_X + (START_X - STOP_X) * u * u              # constant deceleration to a stop


def _path(pts, d):
    """Point and heading at arc length d along a polyline."""
    for a, b in zip(pts[:-1], pts[1:]):
        a, b = Vector(a), Vector(b); L_ = (b - a).length
        if d <= L_:
            return a.lerp(b, d / max(L_, 1e-6)), (b - a).normalized()
        d -= L_
    a, b = Vector(pts[-2]), Vector(pts[-1])
    return b, (b - a).normalized()


def _face(dv):
    """rotation z that faces direction dv (rest pose faces -Y: z = th faces (sin th, -cos th))."""
    return math.atan2(dv.x, -dv.y)


def _pave_z(y):
    return PAVE_Z * min(1.0, max(0.0, (y - KERB_Y) / 0.25))


def _officer(h, sec, appear, rise_from, out_to, walk_pts, face0, speed=1.3):
    """Rise out of the car beside its door (hidden by the door / body), then walk the path."""
    t_up = appear + 0.75
    if sec < appear:
        h.arm.location = (0, 0, -60); bpy.context.view_layer.update(); return
    if sec < t_up:
        u = (sec - appear) / 0.75; e = ease(u)
        p = Vector(rise_from).lerp(Vector(out_to), e)
        d0 = (Vector(walk_pts[1]) - Vector(walk_pts[0])).normalized()
        f = face0 + (_face(d0) - face0) * ease(max(0.0, (u - 0.4) / 0.6))
        place(h, p, f, z=-0.55 * (1 - e) ** 1.5 + _pave_z(p.y), phase=None)
        h.rot("spine03", (math.cos(f), math.sin(f), 0), 18 * (1 - e))         # leaning forward as he gets up
        return
    d = speed * (sec - t_up)
    p, dv = _path(walk_pts, d)
    place(h, p, _face(dv), z=_pave_z(p.y), phase=(d / 1.35) % 1.0)
    fingers_curl(h, 20)


def anim_pull(c, t):
    sec = t * DUR["pull_up"]
    car = c["car"]
    x = _car_x(sec)
    u = min(1.0, max(0.0, (x - START_X) / (STOP_X - START_X)))
    y = CAR_Y - 0.5 * (1 - u) ** 2                                  # eases in to the kerb as it slows
    dydx = 0.5 * 2 * (1 - u) / (STOP_X - START_X)
    car.location = (x, y, 0); car.rotation_euler = (0, 0, math.atan(dydx))
    car.rotation_euler[1] = math.radians(-0.6) * max(0.0, 1 - abs(sec - STOP_T) / 0.35) if sec > STOP_T - 0.35 else 0.0   # nose dip
    vehicles.spin_wheels(car, x - START_X)
    # doors: driver's opens toward the camera, the passenger's on the kerb side a beat earlier
    c["door_r"].rotation_euler = (0, 0, math.radians(64) * ease(min(1.0, max(0.0, (sec - 2.55) / 0.75))))
    c["door_l"].rotation_euler = (0, 0, -math.radians(60) * ease(min(1.0, max(0.0, (sec - 2.5) / 0.7))))
    bpy.context.view_layer.update()
    # driver: out beside his door, then along the car toward its front (and on round to the lobby)
    _officer(c["offA"], sec, 2.95, (0.1, CAR_Y - 1.05), (0.15, CAR_Y - 1.5),
             [(0.15, CAR_Y - 1.5), (2.75, CAR_Y - 1.4), (3.25, CAR_Y - 0.4), (3.3, GLASS_Y - 1.0)], 0.0)
    # passenger: out on the kerb side and straight across the pavement to the lobby doors
    _officer(c["offB"], sec, 2.8, (0.25, CAR_Y + 1.05), (0.3, CAR_Y + 1.45),
             [(0.3, CAR_Y + 1.45), (0.9, KERB_Y + 0.6), (1.6, GLASS_Y - 0.6)], math.pi)
    for o, yy, j in c["rain"]:
        o.location = (0, yy, 4 + j * 8 - (sec * 7.0) % 8.0)        # 7 m/s (not a divisor of the shot length: bake sees it move)
    bpy.context.view_layer.update()


def cam_pull(c, t):
    e = ease(t)
    loc = Vector((6.4, -3.3, 0.42)).lerp(Vector((5.6, -2.9, 0.5)), e)
    tgt = Vector((-0.6, CAR_Y + 1.6, 1.25)).lerp(Vector((0.4, CAR_Y + 2.0, 1.3)), e)
    return (loc, tgt, 30)


MOVES = {"pull_up": dict(kind="anim", dof=2.8, far=60.0, cam=cam_pull,
                         focus=lambda c, t: c["car"].location + Vector((0.5, -0.6, 1.0)), anim=anim_pull)}
