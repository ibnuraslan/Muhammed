"""INTRO SET 2 / THE BANK EXTERIOR, Moscow, August 1995, dusk (dramatization).
A four-storey stucco building on a Moscow street (Poly Haven modular facade kit, retinted ochre), granite steps to the
entrance, lamps coming on. Militia Ladas pull up at the kerb, blue beacons turning (2A). On the steps an officer sits,
unwell; a colleague crouches and hands him a glass of water (2B)."""
import os, math
import numpy as np
import bpy
from mathutils import Vector, Matrix
from kit import *
from human import Human, add_asset, reset_pose, fingers_curl, pose_walk, pose_sit, _world_verts, reach
import ph
from pbkit import soviet_car, masonry_facade, joinm
from sc_bankoffice import person, stand, nod, look, _fwd, retint

EXPOSURE = 0.9
BOUNCES = 6
DUR = {"pullup": 4.8, "steps": 4.8}
FRONT_Y = 0.0                # facade plane; the street is toward -Y
KERB_Y = -5.0                # pavement 5 m deep
ROAD_W = 12.0
STEP_N, STEP_H, STEP_D = 4, 0.16, 0.36
rng = np.random.default_rng(8)


# ============================================================================ facade from the modular kit
def kit_facade(x0, bays, top_bay="centered_large", door_bays=(), tint=(0.78, 0.8, 0.82)):
    """Assemble ground floor + two floors + top floor + crown, `bays` x 3 m, starting at x0, facing -Y."""
    root, ms = ph.model("modular_urban_apartments_facade")
    by = {}
    for o in ms:
        by.setdefault(o.name.split(".")[0], o)
    retint(ms, tint)
    out = []

    def put(name, bay_x0_src, z_src, x, z):
        o = by.get(name)
        if o is None:
            return
        n = o.copy(); bpy.context.collection.objects.link(n); n.parent = None
        n.matrix_world = Matrix.Translation((x - bay_x0_src, 0, z - z_src)) @ o.matrix_world
        out.append(n)

    SRC = {"standard": -3.0, "centered_large": 8.0, "centered_small": 12.0, "centered_double": 16.0, "offset_small": 20.0}
    for i in range(bays):
        x = x0 + i * 3.0
        kind = "centered_large" if i in door_bays else top_bay
        sx = SRC[kind]
        # ground floor: tall glazed doors (shopfront-like banking hall), the entrance bay included
        put(f"wall_door_{kind}_01", sx, 0.0, x, 0.0); put(f"door_{kind}_01", sx, 0.0, x, 0.0)
        put("cornice_standard_standard_01", -3.0, 3.4, x, 3.0)
        for f, (zsrc, suf) in enumerate(((4.0, "01"), (8.0, "02"), (8.0, "02"), (12.0, "03"))):
            z = 3.2 + f * 3.0
            put(f"wall_window_{top_bay}_{suf}", SRC[top_bay], zsrc, x, z); put(f"window_{top_bay}_{suf}", SRC[top_bay], zsrc, x, z)
        put("crown_standard_standard_01", -3.0, 4.0, x, 3.2 + 4 * 3.0)
        put("base_standard_01", -3.0, -2.0, x, -0.55)
    for i in range(bays + 1):
        x = x0 + i * 3.0
        for f in range(5):
            put("wall_pier_standard_01", -22.12 - 0.0, 0.0, x - 0.125 + 0.0, f * 3.0 + (0.2 if f else 0.0))
    bpy.data.objects.remove(root, do_unlink=True)
    for o in ms:
        bpy.data.objects.remove(o, do_unlink=True)
    # infill behind the openings (the building has a body)
    box("BankBody", (x0 + bays * 1.5, 6.6, 8.0), (bays * 3.0, 12.0, 16.0), pbr("Interior", (0.05, 0.045, 0.04), 0.9))
    return out


# ============================================================================ build
def build(variant=None):
    c = {}
    world_sky(sun_elev_deg=-4.0, sun_rot_deg=250, strength=2.6, tint=(0.62, 0.74, 1.0))      # blue hour, just after sunset
    # ground: pavement, kerb, road
    pave = ph.texture("concrete_pavers", scale=0.8)
    road = ph.texture("asphalt_02", scale=0.25)
    box("Pavement", (0, KERB_Y / 2, -0.01), (90, -KERB_Y, 0.16), pave)
    box("Kerb", (0, KERB_Y, 0.0), (90, 0.25, 0.18), pbr("Granite", (0.32, 0.31, 0.3), 0.55))
    box("Road", (0, KERB_Y - ROAD_W / 2, -0.12), (90, ROAD_W, 0.1), road)
    box("FarPave", (0, KERB_Y - ROAD_W - 3, -0.01), (90, 6, 0.16), pave)
    # the bank: 7 bays, entrance in the middle bay (x = 0)
    kit_facade(-10.5, 7, door_bays=(3,))
    # granite steps up to the entrance, with a low parapet each side
    gran = ph.texture("granite_tile", scale=1.0)
    for k in range(STEP_N):
        d = STEP_D * (STEP_N - k)
        box("Step", (0, -d / 2 - 0.05, STEP_H * (k + 0.5)), (4.2, d, STEP_H), gran)
    for sx in (-2.25, 2.25):
        box("Parapet", (sx, -STEP_D * STEP_N / 2 - 0.05, 0.42), (0.3, STEP_D * STEP_N, 0.84), gran)
    c["step_top"] = STEP_H * STEP_N
    # brass plate beside the door, plain lettering
    plate = pbr("PlateBrass", (0.55, 0.42, 0.2), 0.3, 1.0)
    box("BankPlate", (1.4, -0.12, 2.0), (0.7, 0.02, 0.45), plate, bevel=0.005)
    text_obj("BankPlateText", "БАНК", (1.4, -0.135, 2.03), 0.12, pbr("PlateInk", (0.05, 0.04, 0.03), 0.4), rot=(math.radians(90), 0, 0), extrude=0.001)
    # neighbours (CG stucco, punched windows) to close the street
    for x, w, h, col in ((-25.0, 9.0, 18.0, (0.6, 0.55, 0.45)), (17.5, 14.0, 21.0, (0.5, 0.44, 0.38)), (32.0, 12.0, 17.0, (0.58, 0.5, 0.4))):
        box("Neighbour", (x, 6.0, h / 2), (w, 12.0, h), masonry_facade(f"N{x}", col, 3.2, 2.6, 1.2, 1.7, 0.18, lit_strength=0.5))
    box("OppositeRow", (0, KERB_Y - ROAD_W - 12, 10), (90, 12, 20), masonry_facade("Opp", (0.55, 0.5, 0.42), 3.2, 2.6, 1.2, 1.7, 0.2, lit_strength=0.5))
    # street lamps (scanned) along the kerb, lit; linden-like small trees
    for x in (-16.0, -4.0, 8.0, 20.0):
        r, lm = ph.model("street_lamp_01", loc=(x, KERB_Y + 0.5, 0), rot_z=math.radians(180))
        l = bpy.data.lights.new("StreetLamp", 'POINT'); l.energy = 160; l.color = (1.0, 0.8, 0.6); l.shadow_soft_size = 0.15
        lo = bpy.data.objects.new("StreetLamp", l); bpy.context.collection.objects.link(lo); lo.location = (x, KERB_Y + 0.5, 3.75)
    for x in (-12.5, 12.0, 24.0):
        ph.model("tree_small_02", loc=(x, KERB_Y + 1.1, 0), rot_z=rng.uniform(0, 6.28), scale=1.25)
    # warm light inside the banking hall
    for x in (-7.5, -1.5, 4.5):
        l = area_light((x, 1.5, 2.8), (0, 0, 0), 3.0, 140, (1.0, 0.82, 0.6)); l.visible_camera = False
    # ---------------------------------------------------------------- militia cars
    blue = (0.05, 0.12, 0.42)
    cars = []
    for k in range(2):
        car = soviet_car(f"Militia{k}", (0.7, 0.7, 0.72) if k == 0 else (0.72, 0.6, 0.22), kind="lada", stripe=blue, beacon=True, label="МИЛИЦИЯ")
        cars.append(car)
    c["cars"] = cars
    parked = soviet_car("ParkedVolga", (0.16, 0.18, 0.2), kind="volga")
    parked.location = (14.0, KERB_Y - 1.1, 0.0)
    c["parked"] = parked
    # ---------------------------------------------------------------- officers (2B on the steps; 2A one walks to the door)
    def officer(name, years, hv):
        h = person(name, 1.0, years, "male_casualsuit01", "short02", cval=0.75, hv=hv, hue=0.58, sat=0.3)   # grey-blue uniform shirt
        return h
    a = officer("OffSit", 44, 0.25)
    b = officer("OffHelp", 31, 0.2)
    w = officer("OffWalk", 38, 0.3)
    c["people"] = {"sit": a, "help": b, "walk": w}
    animate(c, 0.0, "pullup")
    return c


def seat_on_steps(h, x, k_seat):
    """Sit on step k_seat, feet two steps down, facing the street (-Y)."""
    reset_pose(h); h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0); bpy.context.view_layer.update()
    pose_sit(h, lean=22)
    y_front = -STEP_D * (STEP_N - k_seat) - 0.05                 # front edge of the seat step
    h.arm.location = (x, y_front + 0.12, 0); bpy.context.view_layer.update()
    pelvis = h.bone_head("pelvis") if "pelvis" in h.arm.pose.bones else h.bone_head("spine05")
    seat_z = STEP_H * (k_seat + 1)
    w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
    # rest the body's lowest point behind the knees on the step: put the pelvis ~0.1 m above the seat
    h.arm.location.z += seat_z + 0.1 - pelvis.z
    bpy.context.view_layer.update()


# ============================================================================ animation
def car_x(sec, x_stop, arrive=2.8, v0=11.0, start=-26.0):
    """Decelerate uniformly from v0 so the car stops exactly at x_stop at time `arrive`."""
    d = x_stop - start
    v0 = 2 * d / arrive
    if sec >= arrive:
        return x_stop, 0.0
    return start + v0 * sec - 0.5 * (v0 / arrive) * sec * sec, v0 * (1 - sec / arrive)


def animate(c, sec, shot):
    y_lane = KERB_Y - 1.2
    for k, car in enumerate(c["cars"]):
        if shot == "pullup":
            x, v = car_x(max(0.0, sec - 0.9 * k), -3.5 - 5.2 * k, arrive=3.2, start=-34.0 - 6 * k)
        else:
            x, v = -3.5 - 5.2 * k, 0.0
        car.location = (x, y_lane, 0.0); car.rotation_euler = (0, 0, 0)
    a, b, w = c["people"]["sit"], c["people"]["help"], c["people"]["walk"]
    # walker: an officer climbing toward the door (2A); out of the way in 2B
    if shot == "pullup":
        ph_ = (sec * 0.9) % 1.0
        pose_walk_at(w, ph_, Vector((2.6, -4.4 + 1.2 * min(sec, 3.2), 0.0)), math.pi)
    else:
        for o in [w.arm] + list(w.parts):
            o.hide_render = True
    # seated officer and the colleague with the glass (2B); in 2A they are already there, small in the background
    seat_on_steps(a, -0.8, 1)
    nod(a, "spine04", 10); nod(a, "neck01", 10); nod(a, "head", 14)
    fwd = _fwd(a)
    knees = (a.bone_tail("upperleg02.L") + a.bone_tail("upperleg02.R")) / 2
    hand_out = ease(min(1.0, max(0.0, (sec - 1.0) / 1.4))) if shot == "steps" else 0.0
    glass_pos = None
    # helper crouches on the step below, to the seated man's left, holding out a glass
    stand(b, (-0.05, -STEP_D * STEP_N - 0.35, 0), math.radians(-50))       # on the pavement, angled toward him
    nod(b, "spine04", 16); nod(b, "spine03", 8); nod(b, "head", 8)
    bpy.context.view_layer.update()
    gp0 = b.bone_head("spine03") + _fwd(b) * 0.25 + Vector((0, 0, -0.15))
    gp1 = knees + fwd * 0.18 + Vector((0.12, 0, 0.18))
    glass_pos = gp0.lerp(gp1, hand_out)
    reach(b, "R", glass_pos + Vector((0, 0, -0.03)), Vector((0.5, 0.3, -0.7)), Vector((0, 0, 1)))
    fingers_curl(b, 45, side=("R",), thumb=25)
    look(b, a.bone_head("head"), 1.0)
    # seated man's right hand comes up to take it at the end
    take = ease(min(1.0, max(0.0, (sec - 2.6) / 1.2))) if shot == "steps" else 0.0
    rest = knees + Vector((0.0, 0, 0.05))
    reach(a, "R", rest.lerp(glass_pos + Vector((0.03, 0.02, 0.0)), take), Vector((-0.5, -0.5, -0.6)), Vector((0, 0.5, -0.8)))
    reach(a, "L", knees + Vector((0.12, 0.05, 0.04)), Vector((0.5, -0.5, -0.6)), Vector((0, -0.5, -0.8)))
    if "glass" not in c:
        gm = glass("WaterGlass", (0.95, 0.97, 0.98), 0.02)
        g = cyl("Glass", (0, 0, 0.05), 0.035, 0.1, gm, verts=24)
        water = cyl("Water", (0, 0, 0.035), 0.032, 0.07, pbr("Water", (0.8, 0.85, 0.9), 0.0, 0.0, **{'Transmission Weight': 1.0}), verts=24)
        water.parent = g
        c["glass"] = g
    c["glass"].location = glass_pos + Vector((0, 0, -0.05))
    bpy.context.view_layer.update()


def pose_walk_at(h, phase, loc, face_z):
    h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0); bpy.context.view_layer.update()
    bob = pose_walk(h, phase, stride=24, arm_swing=16)
    h.arm.rotation_euler = (0, 0, face_z)
    # stairs: lift the walker with the step under him
    step_k = max(0, min(STEP_N, int((loc.y + STEP_D * STEP_N + 0.05) / STEP_D) + 1)) if loc.y > -STEP_D * STEP_N - 0.05 else 0
    h.arm.location = (loc.x, loc.y, STEP_H * step_k + bob); bpy.context.view_layer.update()


def anim_pullup(c, t):
    animate(c, t * DUR["pullup"], "pullup")


def anim_steps(c, t):
    animate(c, t * DUR["steps"], "steps")


# ============================================================================ cameras
def cam_pullup(c, t):
    e = ease(t)
    loc = Vector((-12.0, KERB_Y - ROAD_W + 1.5, 1.5)).lerp(Vector((-10.8, KERB_Y - ROAD_W + 1.8, 1.55)), e)
    tgt = Vector((-6.0, -2.0, 2.6)).lerp(Vector((-2.0, -1.5, 2.4)), e)
    return (loc, tgt, 28)


def cam_steps(c, t):
    e = ease(t)
    a = c["people"]["sit"]
    tgt = Vector((-0.55, -1.0, 0.85))
    return (tgt + Vector((-2.9, -4.6, 0.75)).lerp(Vector((-2.5, -4.0, 0.68)), e), tgt + Vector((0.3, 0, 0.25)), 35)


MOVES = {
    "pullup": dict(kind="anim", dof=5.6, far=60.0, cam=cam_pullup, anim=anim_pullup, focus=lambda c, t: c["cars"][0].location + Vector((0, 0, 1.0))),
    "steps": dict(kind="anim", dof=2.8, far=30.0, cam=cam_steps, anim=anim_steps, focus=lambda c, t: Vector((-0.55, -1.0, 0.85))),
}
