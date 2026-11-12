"""The Istanbul building where the packages sat: a dim, high warehouse room with big front doors onto a street
of apartment blocks and traffic, an adjoining room through an inner doorway, rubbish being cleared out.
Ch1: new owners clear it out; the brothers load the two packages and drive off. Ch2: how the packages got there
(a forklift, the move next door) and how they sat near the front behind unlocked doors."""
import math
import numpy as np
import bpy
from mathutils import Vector, Euler
from kit import *
from rs_kit import *
from rs_env import sky, facade_material, puddles
from human import reset_pose, pose_walk, reach, fingers_curl
from durs import dur

EXPOSURE = 0.0
BOUNCES = 8
FRONT = -6.0                      # front wall line (y); street beyond
PKG = [Vector((-1.4, -4.2, 0)), Vector((0.2, -4.4, 0))]   # the two packages just inside the doors
INNER = Vector((9.0, 1.0, 0))     # inner doorway into the adjoining building (east wall)


def forklift(name="Forklift"):
    yellow = painted_steel(name + "Y", (0.75, 0.52, 0.06), 0.45, 0.5); black = pbr(name + "K", (0.03, 0.03, 0.03), 0.6)
    parts = [box("FBody", (0, 0, 0.75), (1.1, 1.8, 0.9), yellow, bevel=0.08), box("FCounter", (0, 0.75, 0.75), (1.15, 0.4, 0.95), yellow, bevel=0.08),
             box("FSeat", (0, 0.25, 1.35), (0.5, 0.5, 0.3), black, bevel=0.05), box("FMast", (0, -1.0, 1.5), (0.9, 0.12, 2.9), black),
             box("FRoofL", (-0.5, 0, 2.15), (0.06, 1.4, 0.06), black), box("FRoofR", (0.5, 0, 2.15), (0.06, 1.4, 0.06), black), box("FRoof", (0, 0, 2.2), (1.1, 1.4, 0.04), black)]
    for sx in (-0.5, 0.5):
        for sy in (-0.6, 0.6):
            parts.append(cyl("FWheel", (sx * 1.1, sy, 0.3), 0.3, 0.25, black, verts=24, rot=(0, math.radians(90), 0)))
    fk = join(parts, name)
    carriage = bpy.data.objects.new(name + "Carriage", None); bpy.context.collection.objects.link(carriage); carriage.parent = fk; carriage.location = (0, -1.1, 0.2)
    for sx in (-0.25, 0.25):
        f = box("Fork", (0, 0, 0), (0.12, 1.2, 0.05), black); f.parent = carriage; f.location = (sx, -0.55, 0)
    return fk, carriage


def build(variant=None):
    c = {}
    v = variant or "clear"
    rng = np.random.default_rng(21)
    sky("overcast")
    bpy.context.scene.view_settings.exposure = 0.35      # exposed for the interior; the street stays readable
    box("Ground", (0, 0, -0.06), (400, 400, 0.1), ph_mat("road_damaged", 0.15, (0.2, 0.2, 0.2), name="StreetAsphalt"))
    puddles(rng, ((-20, -16), (20, -8)), 10, size=(0.5, 1.5), z=0.01)
    # the warehouse room: brick walls, concrete floor, steel roof trusses, high windows, big front doors
    brick = ph_mat("brick_wall_02", 0.5, (0.4, 0.25, 0.2), name="WHBrick")
    floor = ph_mat("concrete_floor_worn_001", 0.08, (0.36, 0.35, 0.33), name="WHFloor", tint=(0.72, 0.7, 0.66))
    room("WH", Vector((0, 2.0, 0)), 18, 16, 6.0, floor, brick, ceil_m=ph_mat("rusty_corrugated_iron", 0.4, (0.3, 0.3, 0.3), name="WHRoof"),
         windows=[("N", -5.0, 3.6, 2.4, 1.6), ("N", 0.0, 3.6, 2.4, 1.6), ("N", 5.0, 3.6, 2.4, 1.6)],
         doors=[("S", -0.6, 0, 4.0, 3.6), ("E", -1.0, 0, 2.0, 2.6)])
    for x in (-5.0, 0.0, 5.0):
        daylight_window(Vector((x, 10.2, 4.4)), "N", (2.4, 1.6), energy=900)
    dl = bpy.data.lights.new("DoorDay", 'AREA'); dl.size = 4.0; dl.size_y = 3.6; dl.energy = 3000; dl.color = (0.88, 0.92, 1.0)
    do = bpy.data.objects.new("DoorDay", dl); bpy.context.collection.objects.link(do); do.location = (-0.6, FRONT - 1.0, 1.8)
    do.rotation_euler = (math.radians(-90), 0, 0); do.visible_camera = False
    steel = painted_steel("Truss", (0.2, 0.22, 0.24), 0.5, 0.6)
    for x in np.arange(-8, 9, 4):
        box("Truss", (x, 2.0, 5.6), (0.25, 16, 0.4), steel)
    # front door leaves (hinged; the wind swings one)
    c["doors"] = []
    for sx in (-1, 1):
        hinge = bpy.data.objects.new("DoorHinge", None); bpy.context.collection.objects.link(hinge)
        hinge.location = (-0.6 + sx * 2.0, FRONT, 0)
        leaf = box("DoorLeaf", (0, 0, 0), (1.95, 0.08, 3.5), ph_mat("painted_metal_shutter", 0.5, (0.3, 0.35, 0.3), name="DoorPaint"), bevel=0.01)
        leaf.parent = hinge; leaf.location = (-sx * 0.98, 0, 1.75)
        c["doors"].append((hinge, sx))
    # adjoining building beyond the inner doorway: a second room, lit by one window
    room("Next", Vector((14.0, 1.0, 0)), 8, 8, 4.5, floor, ph_mat("plastered_wall_04", 0.4, (0.6, 0.55, 0.47), name="NextPlaster", tint=(0.85, 0.82, 0.72)),
         windows=[("N", 0.0, 1.5, 1.6, 1.6)], doors=[("W", 0.0, 0, 2.0, 2.6)])
    daylight_window(Vector((14.0, 5.2, 2.3)), "N", (1.6, 1.6), energy=200)
    for k in range(3):
        tube_light(Vector((-5 + 5 * k, 2.0, 5.5)), energy=260 if v != "dim" else 200)
    # a half-cleared office floor: piles of old office furniture, filing cabinets, boxes, a rolled carpet
    def filing_cabinet(loc, rz, col):
        m = painted_steel(f"FC{loc[0]:.0f}{loc[1]:.0f}", col, 0.45, 0.45); k_ = pbr("FCHandle", (0.55, 0.55, 0.55), 0.3, 0.9)
        parts = [box("FCBody", (0, 0, 0.66), (0.47, 0.62, 1.32), m, bevel=0.01)]
        for j in range(4):
            parts += [box("FCDrawer", (0, -0.315, 0.17 + j * 0.32), (0.43, 0.012, 0.29), m, bevel=0.004), box("FCPull", (0, -0.33, 0.25 + j * 0.32), (0.12, 0.02, 0.02), k_)]
        o = join(parts, "FilingCabinet"); o.location = loc; o.rotation_euler = (0, 0, rz)
        return o
    for (x, y, rz, col) in ((-7.6, 6.6, 0.0, (0.42, 0.45, 0.42)), (-7.0, 6.6, 0.05, (0.5, 0.48, 0.42)), (-6.4, 6.65, -0.04, (0.42, 0.45, 0.42)),
                            (6.8, 1.5, 1.6, (0.38, 0.4, 0.44)), (-3.2, 7.6, 0.4, (0.5, 0.48, 0.42))):
        filing_cabinet((x, y, 0), rz, col)
    fc = filing_cabinet((6.2, 3.4, 0.0), 0, (0.42, 0.45, 0.42)); fc.rotation_euler = (math.radians(90), 0, 0.3); fc.location = (6.2, 3.4, 0.24)   # one lying on its back
    for k in range(14):
        ph_model("cardboard_box_01", loc=(rng.uniform(-7.5, -3.5), rng.uniform(2.5, 8), 0.0 if k < 10 else 0.42), rot_z=rng.uniform(0, 3))
    for k in range(3):
        ph_model("wooden_crate_01", loc=(rng.uniform(3.5, 7.5), rng.uniform(5, 8), 0.0), rot_z=rng.uniform(0, 3))
    for aid, loc, rz in (("metal_office_desk", (5.5, -1.5, 0), 0.3), ("metal_office_desk", (4.6, 6.4, 0), 1.4), ("metal_office_desk", (-5.2, 4.6, 0), -0.2),
                         ("plastic_monobloc_chair_01", (-4.4, 3.2, 0), 0.8), ("metal_stool_01", (4.0, 4.9, 0.78), 2.6), ("plastic_monobloc_chair_01", (5.0, -0.6, 0), 2.0),
                         ("steel_frame_shelves_01", (7.4, 6.8, 0), 3.14), ("wooden_bookshelf_worn", (-8.2, 4.0, 0), 1.57), ("binder_notebook", (5.4, -1.4, 0.76), 0.4)):
        ph_model(aid, loc=loc, rot_z=rz)
    cyl("Carpet", (-5.6, 1.2, 0.18), 0.18, 2.4, fabric("Carpet", (0.4, 0.12, 0.1), 0.9, 0.4, 200), verts=16, rot=(0, math.radians(90), 0.3))
    # paper litter on the floor
    paper = pbr("Paper", (0.75, 0.73, 0.68), 0.8)
    for k in range(40):
        box("Paper", (rng.uniform(-7, 7), rng.uniform(-4, 8), 0.003), (0.21, 0.3, 0.002), paper, rot=(0, 0, rng.uniform(0, 3)))
    # winter sun through the open front doors: a light shaft in the dust
    shaft = bpy.data.lights.new("DoorShaft", 'SPOT'); shaft.energy = 20000; shaft.spot_size = math.radians(16); shaft.spot_blend = 0.4
    shaft.color = (1.0, 0.92, 0.8); shaft.shadow_soft_size = 0.2
    so = bpy.data.objects.new("DoorShaft", shaft); bpy.context.collection.objects.link(so); so.location = (-0.6 - 3.0, FRONT - 9.0, 7.5)
    so.rotation_euler = (Vector((3.4, 12.0, -7.5))).to_track_quat('-Z', 'Y').to_euler()
    haze((0, 2, 3), (17.8, 15.8, 5.8), density=0.014, color=(0.85, 0.82, 0.76), anis=0.6)
    # the two packages near the front
    c["pk"] = []
    for k, p in enumerate(PKG):
        o, kk = container(f"Pkg{k}"); o.location = p; o.rotation_euler = (0, 0, 0.2 * k); kk["trefoil"].hide_render = True
        c["pk"].append(o)
    # street outside: opposite apartment blocks, parked cars, traffic, the truck (placeholder)
    fac = facade_material("StreetFacade", (0.7, 0.66, 0.58), floor=2.9, bay=3.2)
    from sc_hospital import facade_windows
    opp_m = ph_mat("plastered_wall_04", 0.3, (0.7, 0.66, 0.58), name="OppPlaster", tint=(0.85, 0.8, 0.7))
    for k in range(6):
        fl = 4 + (k % 3); h = fl * 2.9 + 0.6
        box("Opp", (-25 + k * 10, -31.0, h / 2), (9.6, 10, h), opp_m)
        facade_windows(f"OppWin{k}", Vector((-25 + k * 10 - 4.8, -26.0, 0)), 9.0, fl, floor_h=2.9, bay=3.0, sill0=0.9, normal_y=1)
    for x in (-16.0, 24.0):
        box("Adj", (x, 2.0, 7.0), (12, 16, 14), fac)
    from rs_vehicles import car
    c["traffic"] = [car(f"Traffic{k}", col, kind) for k, (col, kind) in enumerate((((0.6, 0.6, 0.58), "sedan_1990s_soviet"), ((0.45, 0.1, 0.08), "sedan_1990s_soviet"),
                                                                                    ((0.58, 0.53, 0.44), "sedan_1990s_soviet"), ((0.75, 0.75, 0.72), "van_1990s")))]
    for k, t in enumerate(c["traffic"]):
        t.location = (-60, -16, 0)
    tk, wheels, bed_z, _ = truck("Truck", (0.12, 0.2, 0.3))
    c.update(truck=tk, wheels=wheels, bed_z=bed_z)
    tk.location = (-0.6, -11.2, 0); tk.rotation_euler = (0, 0, math.pi)
    c["plank"] = box("Plank", (0, -150, 0), (0.35, 2.4, 0.05), noisy("PlankW", (0.4, 0.3, 0.18), 0.8))
    c["roller"] = cyl("RollerPipe", (0, -150, 0), 0.05, 1.2, rust_mat("RollerRust"), verts=12, rot=(0, math.radians(90), 0))
    import vehicles as _V
    c["fk"] = _V.make("forklift"); c["fk_car"] = _V.part(c["fk"], "forks"); c["fk_z0"] = c["fk_car"].location.z if c["fk_car"] else 0.0
    c["fk"].location = (0, -150, 0)
    ht, _ = ph_model("hand_truck", loc=(7.5, 8.0, 0)); c["handtruck"] = ht
    c["table"], _ = ph_model("metal_office_desk", loc=(6.0, 7.5, 0))
    P = {}
    P["a"] = person("ClearA", 1.0, 35, "parka_green", "short02", hat="knit", hat_col=(0.15, 0.15, 0.18))
    P["b"] = person("ClearB", 1.0, 48, "wool_grey", "short03", moustache=True)
    P["bro1"] = person("Bro1", 1.0, 38, "wool_brown", "short02", moustache=True)
    P["bro2"] = person("Bro2", 1.0, 33, "parka_green", "short04", hat="knit", hat_col=(0.14, 0.15, 0.2))
    P["buyer"] = person("Buyer", 1.0, 55, "suit_brown", "short03", hv=0.55, moustache=True)
    P["agent"] = person("Agent", 1.0, 40, "suit_grey", "short04")
    c["people"] = P
    for h in P.values():
        place(h, (0, -150, 0), 0)
    return c


def walk_to(h, a, b, sec, speed=1.0, stride=1.25, swing=14):
    a = Vector(a); b = Vector(b); d = b - a; L_ = d.length; s = min(L_, max(0.0, speed * sec))
    h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0); reset_pose(h)
    moving = 0 < s < L_; ph_ = (s / stride) % 1.0 if moving else 0.0
    pose_walk(h, ph_, stride=24 if moving else 0, arm_swing=0); arms_relaxed(h, ph_, swing if moving else 0)
    p = a + d.normalized() * s; place(h, (p.x, p.y, 0), face_angle(a, b)); return p


def doors(c, k_left=1.0, k_right=1.0):
    for hinge, sx in c["doors"]:
        k = k_left if sx < 0 else k_right
        hinge.rotation_euler = (0, 0, sx * math.radians(100) * k)


def C(p0, p1, tgt, lens):
    return lambda c, t: (Vector(p0).lerp(Vector(p1), ease(t)), Vector(tgt), lens)


def carry_pair(c, h1, h2, obj, a, b, sec, speed=0.7):
    """Two men carry a desk between them toward b: the front man walks backwards facing it, each grips his own end."""
    d = (Vector(b) - Vector(a)).normalized()
    p = walk_to(h1, a, b, sec, speed=speed, swing=0)
    place(h1, (p.x, p.y, 0), face_angle(p, p - d))                  # front man faces back along the desk
    q = walk_to(h2, Vector(a) - d * 2.3, Vector(b) - d * 2.3, sec, speed=speed, swing=0)
    mid = p - d * 1.15 + Vector((0, 0, 0.62))
    obj.location = Vector((mid.x, mid.y, 0.06)); obj.rotation_euler = (0, 0, math.atan2(d.y, d.x))   # desk long axis is local X
    for h, end in ((h1, mid + d * 0.62), (h2, mid - d * 0.62)):
        sd = forward(h).cross(Vector((0, 0, 1))).normalized()
        reach(h, "R", end + sd * 0.32, Vector((sd.x, sd.y, -1.0)), forward(h)); reach(h, "L", end - sd * 0.32, Vector((-sd.x, -sd.y, -1.0)), forward(h))
        h.rot("spine03", sd, -12); fingers_curl(h, 70, thumb=40)


def c1_2a(c, t):
    sec = t * dur("ch1_2a"); doors(c)
    if c["table"] is not None:
        carry_pair(c, c["people"]["a"], c["people"]["b"], c["table"], (2.0, 5.0, 0), (0.2, -9.0, 0), sec, speed=0.75)


def c1_2b(c, t):
    sec = t * dur("ch1_2b"); doors(c)
    walk_to(c["people"]["a"], (-1.0, -8.0, 0), (-3.0, 3.0, 0), sec, speed=0.9)


def c1_3a(c, t):           # two men roll a container on a pipe up a plank into the truck bed
    sec = t * dur("ch1_3a"); doors(c)
    tk = c["truck"]; bpy.context.view_layer.update()
    tail = tk.matrix_world @ Vector((-3.7, 0, c["bed_z"]))
    foot = tail + Vector((0, 2.2, -c["bed_z"]))
    pl = c["plank"]; pl.location = (tail + foot) / 2; pl.rotation_euler = (math.atan2(tail.z - foot.z, 2.2), 0, 0)
    k = ease(min(1.0, sec / dur("ch1_3a")))
    p = foot.lerp(tail, k * 0.85)
    ct = c["pk"][0]; ct.location = p + Vector((0, 0, 0.06)); ct.rotation_euler = (pl.rotation_euler.x * 0.8, 0, 0)
    c["roller"].location = p + Vector((0, 0.3, 0.06)); c["pk"][1].location = Vector((-0.6, -8.6, 0.0)) + Vector((-1.5, 0, 0))
    for nm, sx in (("bro1", -0.45), ("bro2", 0.45)):
        h = c["people"][nm]; st = p + Vector((sx, 0.95, 0)); st.z = 0
        stand_pose(h); place(h, st, face_angle(st, p))
        sd = forward(h).cross(Vector((0, 0, 1))); h.rot("spine03", sd, -22)
        hand = p + Vector((sx * 0.6, 0.45, 0.75))
        reach(h, "R", hand + sd * 0.1, Vector((sd.x, sd.y, -0.7)), forward(h)); reach(h, "L", hand - sd * 0.1, Vector((-sd.x, -sd.y, -0.7)), forward(h))


def c1_3b(c, t):           # the truck pulls away and joins the traffic
    sec = t * dur("ch1_3b"); doors(c)
    k = ease(min(1.0, sec / dur("ch1_3b")))
    tk = c["truck"]; tk.location = Vector((-0.6, -11.2, 0)) + Vector((-14.0 * k * k, -4.6 * min(1, k * 2), 0)); tk.rotation_euler = (0, 0, math.pi - 0.25 * math.sin(math.pi * min(1, k * 1.5)))
    for o in c["pk"]:
        o.location = (0, -150, 0)
    for j, car_ in enumerate(c["traffic"]):
        x = -40 + (sec * 8.0 + j * 14) % 80
        car_.location = (x if j % 2 == 0 else -x, -17.5 if j % 2 == 0 else -14.8, 0); car_.rotation_euler = (0, 0, 0 if j % 2 == 0 else math.pi)


def c2_13a(c, t):          # a forklift sets two packages down inside the warehouse
    sec = t * dur("ch2_13a"); doors(c, 0.2, 0.2)
    k = ease(min(1.0, sec / (dur("ch2_13a") * 0.7)))
    fk = c["fk"]; fk.location = Vector((3.5, 5.0 - 3.5 * k, 0)); fk.rotation_euler = (0, 0, math.radians(-90) - math.radians(20) * (1 - k))
    lift = 0.6 * (1 - ease(min(1.0, max(0.0, (sec - dur("ch2_13a") * 0.7) / (dur("ch2_13a") * 0.3)))))
    if c["fk_car"] is not None:
        c["fk_car"].location.z = c["fk_z0"] + lift
    bpy.context.view_layer.update()
    for j, o in enumerate(c["pk"]):
        o.location = fk.matrix_world @ Vector((1.9, 0.55 * (j - 0.5) * 2, 0.15 + lift))
        o.rotation_euler = (0, 0, fk.rotation_euler.z)


def c2_13b(c, t):          # one package wheeled on a hand truck through the doorway into the next building
    sec = t * dur("ch2_13b"); doors(c, 0.2, 0.2)
    a = Vector((6.4, 1.0, 0)); b = Vector((12.0, 1.0, 0))
    h = c["people"]["b"]; p = walk_to(h, a, b, sec, speed=0.7, swing=0)
    d = (b - a).normalized(); cart = p + d * 0.75
    ht = c["handtruck"]
    if ht is not None:
        ht.location = cart; ht.rotation_euler = (0, 0, math.atan2(d.y, d.x) + math.pi / 2)
    c["pk"][0].location = cart + d * 0.25 + Vector((0, 0, 0.08)); c["pk"][0].rotation_euler = (0, math.radians(-12), 0)
    sd = forward(h).cross(Vector((0, 0, 1)))
    grip = p + d * 0.45 + Vector((0, 0, 1.0))
    reach(h, "R", grip + sd * 0.2, Vector((sd.x, sd.y, -0.7)), d); reach(h, "L", grip - sd * 0.2, Vector((-sd.x, -sd.y, -0.7)), d)


def c2_14a(c, t):          # wind swings an unlocked door open onto the two packages near the front
    sec = t * dur("ch2_14a")
    k = ease(min(1.0, sec / (dur("ch2_14a") * 0.8)))
    doors(c, 0.05 + 0.6 * k + 0.04 * math.sin(sec * 2.0), 0.0)


def c2_14b(c, t):          # a buyer and an agent walk past the packages without a glance
    sec = t * dur("ch2_14b"); doors(c, 0.8, 0.8)
    walk_to(c["people"]["agent"], (-6.0, -2.6, 0), (6.0, 0.2, 0), sec, speed=0.85)
    walk_to(c["people"]["buyer"], (-6.8, -3.4, 0), (5.2, -0.6, 0), sec, speed=0.85)


SHOTS = {
    "ch1_2a": ("clear", c1_2a, C(Vector((3.0, 8.5, 1.6)), Vector((2.6, 8.0, 1.6)), Vector((0.0, -7.0, 1.5)), 26), None),
    "ch1_2b": ("clear", c1_2b, C(Vector((-6.5, 5.5, 1.3)), Vector((-2.8, -1.8, 1.0)), Vector((-0.6, -4.3, 0.6)), 30), 4.0),
    "ch1_3a": ("clear", c1_3a, C(Vector((5.5, -11.0, 1.5)), Vector((5.1, -10.6, 1.5)), Vector((-0.6, -8.6, 1.0)), 30), 4.0),
    "ch1_3b": ("clear", c1_3b, C(Vector((7.0, -22.0, 1.6)), Vector((6.0, -22.0, 1.6)), Vector((-4.0, -12.0, 1.5)), 30), None),
    "ch2_13a": ("dim", c2_13a, C(Vector((-3.5, -2.0, 1.4)), Vector((-3.0, -2.6, 1.45)), Vector((2.0, -1.0, 0.9)), 30), 4.0),
    "ch2_13b": ("dim", c2_13b, C(Vector((5.0, -3.0, 1.5)), Vector((5.6, -2.7, 1.5)), Vector((9.5, 1.0, 1.2)), 30), 4.0),
    "ch2_14a": ("dim", c2_14a, C(Vector((-2.0, 4.0, 1.2)), Vector((-1.8, 3.2, 1.2)), Vector((-0.8, -4.6, 0.8)), 32), 4.0),
    "ch2_14b": ("dim", c2_14b, C(Vector((-0.6, 3.6, 1.5)), Vector((0.0, 3.4, 1.5)), Vector((-0.6, -3.6, 1.0)), 28), 4.0),
}
VARIANT_FOR = {k: v[0] for k, v in SHOTS.items()}
DUR = {k: dur(k) for k in SHOTS}
MOVES = {k: dict(kind="anim", far=80.0, anim=v[1], cam=v[2], dof=v[3]) for k, v in SHOTS.items()}
