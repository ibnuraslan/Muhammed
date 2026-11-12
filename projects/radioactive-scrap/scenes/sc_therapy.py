"""A 1990s hospital radiotherapy room: a cobalt-60 teletherapy unit (stand, rotating gantry, heavy source head
with a collimator), the treatment couch, a shielded maze entrance with a heavy door and a trefoil sign; outside,
a store-room door that gets padlocked and a new sign (Ch4). Generic equipment, no brands."""
import math
import numpy as np
import bpy
from mathutils import Vector, Euler
from kit import *
from rs_kit import *
from rs_env import sky
from human import reset_pose, pose_walk, reach, fingers_curl
from durs import dur

EXPOSURE = 0.0
BOUNCES = 8
ISO = Vector((0.0, 0.0, 1.25))       # isocentre above the couch
DOOR = Vector((-4.5, -3.2, 0))       # treatment-room doorway (west end of the south wall)
STORE = Vector((-10.0, -6.76, 0))     # store-room door in the corridor outside


def sign_plate(name, loc, rot_z, size=0.3):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc, rotation=(math.radians(90), 0, rot_z))
    o = bpy.context.active_object; o.name = name; o.data.materials.append(trefoil_material(name + "M"))
    return o


def build(variant=None):
    c = {}
    v = variant or "room"
    sky("afternoon")
    tile = ph_mat("interior_tiles", 1.0, (0.7, 0.72, 0.7), name="TherapyTiles")
    floor = ph_mat("large_grey_tiles", 0.6, (0.5, 0.5, 0.48), name="TherapyFloor")
    room("Therapy", Vector((0, 0, 0)), 9, 6.4, 3.2, floor, two_tone("TherapyWall", (0.55, 0.62, 0.6), (0.82, 0.83, 0.8), split=1.5),
         doors=[("S", -4.5 + 0.9, 0, 1.4, 2.2)])
    for k in range(3):
        tube_light(Vector((-3 + 3 * k, 0.6, 3.15)), energy=55)
    # corridor outside (south) with the store-room door
    room("TherCor", Vector((-4.0, -5.2, 0)), 14, 3.2, 3.0, floor, two_tone("TherCorWall"), windows=[("S", 3.0, 1.0, 1.6, 1.4)], doors=[("N", 0.4, 0, 1.4, 2.2)])
    daylight_window(Vector((-1.0, -6.95, 1.7)), "S", (1.6, 1.4), energy=220)
    tube_light(Vector((-8.0, -5.2, 2.95)), energy=45); tube_light(Vector((0.0, -5.2, 2.95)), energy=45)
    heavy = painted_steel("HeavyDoor", (0.55, 0.58, 0.6), 0.45, 0.4)
    hinge = bpy.data.objects.new("TDoorHinge", None); bpy.context.collection.objects.link(hinge); hinge.location = Vector((-4.5 + 0.2, -3.2, 0))
    dl = box("TDoorLeaf", (0, 0, 0), (1.35, 0.25, 2.15), heavy, bevel=0.02); dl.parent = hinge; dl.location = (0.68, -0.15, 1.08)
    c["tdoor"] = hinge
    c["door_sign"] = sign_plate("DoorTrefoil", Vector((-4.5 + 0.9, -3.31, 1.85)), 0.0, 0.28)
    store = box("StoreDoor", STORE + Vector((0, 0.0, 1.05)), (0.95, 0.06, 2.1), painted_steel("StoreDoorM", (0.35, 0.4, 0.38), 0.5, 0.4))
    hasp = box("Hasp", STORE + Vector((0.42, -0.05, 1.05)), (0.08, 0.02, 0.15), pbr("HaspSteel", (0.5, 0.5, 0.5), 0.4, 0.9))
    lock = join([box("LockBody", (0, 0, 0), (0.05, 0.025, 0.06), pbr("Brass", (0.6, 0.45, 0.15), 0.3, 1.0), bevel=0.005),
                 cyl("Shackle", (0, 0, 0.045), 0.018, 0.03, pbr("SteelS", (0.6, 0.6, 0.6), 0.3, 0.9), verts=10, rot=(math.radians(90), 0, 0))], "Padlock")
    c["lock"] = lock; c["lock_at"] = STORE + Vector((0.42, -0.08, 0.98))
    c["new_sign"] = sign_plate("NewSign", Vector((0, -150, 0)), 0.0, 0.32); c["new_sign_at"] = STORE + Vector((0.0, -0.04, 1.75))
    # the cobalt unit: floor stand, rotating gantry arm, heavy source head with collimator jaws
    unit = painted_steel("UnitPaint", (0.82, 0.82, 0.78), 0.4, 0.2)
    dark = painted_steel("UnitDark", (0.2, 0.22, 0.24), 0.45, 0.4)
    box("Stand", (0.0, 2.6, 1.3), (1.6, 1.0, 2.6), unit, bevel=0.06)
    cyl("Bearing", (0.0, 2.05, 1.25), 0.55, 0.15, dark, verts=40, rot=(math.radians(90), 0, 0))
    gantry = bpy.data.objects.new("Gantry", None); bpy.context.collection.objects.link(gantry); gantry.location = Vector((0, 1.95, 1.25))
    arm = join([box("Arm", (0, -0.6, 0.0), (0.5, 1.2, 0.45), unit, bevel=0.05), box("ArmUp", (0, -1.1, 0.9), (0.55, 0.45, 1.8), unit, bevel=0.05)], "GantryArm")
    arm.parent = gantry; arm.location = (0, 0, 0)
    head = join([cyl("Head", (0, -1.95, 1.35), 0.42, 0.75, unit, verts=36, rot=(0, 0, 0)), cyl("HeadRing", (0, -1.95, 0.98), 0.44, 0.08, dark, verts=36)], "SourceHead")
    head.parent = gantry; head.location = (0, 0, 0)
    c["jaws"] = []
    for sx in (-1, 1):
        j = box("Jaw", (0, 0, 0), (0.18, 0.3, 0.12), dark, bevel=0.01); j.parent = gantry; j.location = (sx * 0.1, -1.95, 0.88); c["jaws"].append((j, sx))
    cw = box("Counterweight", (0, 0, 0), (0.6, 0.5, 0.5), dark, bevel=0.04); cw.parent = gantry; cw.location = (0, -1.4, -1.3)
    c["gantry"] = gantry
    # treatment couch
    couch = join([box("CouchTop", (0, -0.3, 0.88), (0.55, 2.2, 0.06), pbr("CouchPad", (0.15, 0.17, 0.2), 0.5), bevel=0.02),
                  box("CouchBase", (0, 0.2, 0.42), (0.5, 0.8, 0.84), unit, bevel=0.04)], "Couch")
    c["pillow"] = box("Pillow", (0, -150, 0), (0.45, 0.3, 0.1), fabric("PillowF", (0.88, 0.88, 0.85), 0.9, 0.3, 500), bevel=0.04)
    c["pillow_at"] = Vector((0, 0.55, 0.96))
    box("ControlDesk", (3.5, -2.6, 0.45), (1.2, 0.6, 0.9), unit)
    # a shielded transport container and its trolley (the old source going out)
    cont, kk = container("TCont"); cont.scale = (0.8, 0.8, 0.8)
    trolley = join([box("TrolleyTop", (0, 0, 0.35), (1.0, 0.8, 0.05), painted_steel("Trolley", (0.3, 0.35, 0.4), 0.5, 0.5)),
                    box("TrolleyBar", (-0.55, 0, 0.75), (0.04, 0.7, 0.04), pbr("TBar", (0.1, 0.1, 0.1), 0.5, 0.6))], "Trolley")
    for sx in (-0.4, 0.4):
        for sy in (-0.3, 0.3):
            cyl("Castor", (sx, sy, 0.08), 0.08, 0.05, pbr("CastorM", (0.03, 0.03, 0.03), 0.6), verts=12, rot=(math.radians(90), 0, 0)).parent = trolley
    cont.parent = trolley; cont.location = (0, 0, 0.38)
    trolley.location = (0, -150, 0); c["trolley"] = trolley
    P = {}
    P["rad"] = person("Radiographer", 0.0, 36, "nurse", "bob02", hv=0.12)
    P["t1"] = person("TechA", 1.0, 41, "doctor", "short03", moustache=True)
    P["t2"] = person("TechB", 1.0, 30, "overall_white", "short02", dosimeter=True)
    P["insp"] = person("Inspector", 1.0, 50, "suit_grey", "short03", hv=0.55, moustache=True)
    c["people"] = P
    for h in P.values():
        place(h, (0, -150, 0), 0)
    c["clip"] = box("Clipboard", (0, -150, 0), (0.24, 0.015, 0.32), pbr("Clip", (0.45, 0.35, 0.2), 0.5))
    return c


def walk_to(h, a, b, sec, speed=1.0, stride=1.25):
    a = Vector(a); b = Vector(b); d = b - a; L_ = d.length; s = min(L_, max(0.0, speed * sec))
    h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0); reset_pose(h)
    moving = 0 < s < L_; ph_ = (s / stride) % 1.0 if moving else 0.0
    pose_walk(h, ph_, stride=24 if moving else 0, arm_swing=0); arms_relaxed(h, ph_, 14 if moving else 0)
    p = a + d.normalized() * s; place(h, (p.x, p.y, 0), face_angle(a, b)); return p


def gantry(c, ang_deg, jaw=0.0):
    c["gantry"].rotation_euler = (0, math.radians(ang_deg), 0)
    for j, sx in c["jaws"]:
        j.location = (sx * (0.1 + 0.1 * jaw), -1.95, 0.88)


def C(p0, p1, tgt, lens):
    return lambda c, t: (Vector(p0).lerp(Vector(p1), ease(t)), Vector(tgt), lens)


def c2_9a(c, t):
    sec = t * dur("ch2_9a"); gantry(c, 20 + 2 * sec); c["tdoor"].rotation_euler = (0, 0, math.radians(80))


def c2_9b(c, t):           # the radiographer settles a pillow on the couch (medium)
    sec = t * dur("ch2_9b"); gantry(c, 22); c["tdoor"].rotation_euler = (0, 0, math.radians(80))
    h = c["people"]["rad"]; st = Vector((0.75, 0.55, 0)); stand_pose(h); place(h, st, face_angle(st, Vector((0, 0.55, 0))))
    k = ease(min(1.0, sec / 1.8)); sd = forward(h).cross(Vector((0, 0, 1)))
    pil = (h.bone_head("spine02") + forward(h) * 0.35).lerp(c["pillow_at"], k)
    h.rot("spine03", sd, -18 * k)
    reach(h, "R", pil + sd * 0.15 + Vector((0, 0, 0.04)), Vector((sd.x, sd.y, -0.7)), forward(h)); reach(h, "L", pil - sd * 0.15 + Vector((0, 0, 0.04)), Vector((-sd.x, -sd.y, -0.7)), forward(h))
    c["pillow"].location = pil


def c2_10a(c, t):          # the heavy head rotates slowly around the empty couch
    sec = t * dur("ch2_10a"); gantry(c, 30 + 40 * ease(t)); c["pillow"].location = c["pillow_at"]


def c2_10b(c, t):          # push in on the thick head as its collimator opens
    sec = t * dur("ch2_10b"); gantry(c, 0, jaw=ease(min(1.0, sec / dur("ch2_10b")))); c["pillow"].location = c["pillow_at"]


def c2_11a(c, t):          # technicians wheel a grey shielded container out on a trolley
    sec = t * dur("ch2_11a"); gantry(c, 0); c["tdoor"].rotation_euler = (0, 0, math.radians(85))
    p0 = Vector((-1.5, -0.5, 0)); p1 = Vector((-3.6, -4.2, 0)); k = min(1.0, sec / dur("ch2_11a"))
    p = p0.lerp(p1, ease(k)); c["trolley"].location = p; c["trolley"].rotation_euler = (0, 0, math.atan2(p1.y - p0.y, p1.x - p0.x))
    d = (p1 - p0).normalized()
    for nm, off in (("t1", -1.0), ("t2", 0.9)):
        h = c["people"][nm]; a_ = p0 + d * off; walk_to(h, a_, a_ + (p1 - p0), sec, speed=(p1 - p0).length / dur("ch2_11a") * 1.05, stride=1.0)
    hh = c["people"]["t1"]; sd = forward(hh).cross(Vector((0, 0, 1)))
    bar = c["trolley"].matrix_world @ Vector((-0.55, 0, 0.75))
    reach(hh, "R", bar + sd * 0.15, Vector((sd.x, sd.y, -0.7)), forward(hh)); reach(hh, "L", bar - sd * 0.15, Vector((-sd.x, -sd.y, -0.7)), forward(hh))


def c2_11b(c, t):          # the container rolls past the trefoil sign on the door
    sec = t * dur("ch2_11b"); gantry(c, 0); c["tdoor"].rotation_euler = (0, 0, math.radians(85))
    p0 = Vector((-3.6, -4.2, 0)); p1 = Vector((-9.0, -5.0, 0)); p = p0.lerp(p1, ease(min(1.0, sec / dur("ch2_11b"))))
    c["trolley"].location = p; c["trolley"].rotation_euler = (0, 0, math.pi)
    walk_to(c["people"]["t1"], p0 + Vector((1.0, 0, 0)), p1 + Vector((1.0, 0, 0)), sec, speed=(p1 - p0).length / dur("ch2_11b"))
    walk_to(c["people"]["t2"], p0 + Vector((0.5, -0.9, 0)), p1 + Vector((0.5, -0.9, 0)), sec, speed=(p1 - p0).length / dur("ch2_11b"))


def c4_10a(c, t):          # an inspector with a clipboard enters the room
    sec = t * dur("ch4_10a"); gantry(c, 0); c["pillow"].location = c["pillow_at"]
    c["tdoor"].rotation_euler = (0, 0, math.radians(85 * ease(min(1.0, sec / 1.2))))
    h = c["people"]["insp"]; p = walk_to(h, Vector((-3.6, -4.6, 0)), Vector((-2.0, 0.2, 0)), sec - 0.6, speed=0.9)
    sd = forward(h).cross(Vector((0, 0, 1)))
    board = h.bone_head("spine02") + forward(h) * 0.25 + Vector((0, 0, -0.12))
    reach(h, "L", board, Vector((-sd.x, -sd.y, -0.7)), forward(h))
    c["clip"].location = board + forward(h) * 0.02; c["clip"].rotation_euler = (math.radians(-40), 0, math.atan2(-forward(h).x, forward(h).y))
    stand_pose(c["people"]["t1"], crossed=True); place(c["people"]["t1"], Vector((2.0, -1.5, 0)), face_angle((2.0, -1.5), (-2.0, 0.2)))


def c4_10b(c, t):          # the store door is padlocked; a new trefoil sign goes up (medium, people in frame)
    sec = t * dur("ch4_10b"); gantry(c, 0)
    h = c["people"]["t2"]; st = STORE + Vector((0.35, 0.8, 0)); stand_pose(h); place(h, st, face_angle(st, STORE + Vector((0.4, 0, 0))))
    sd = forward(h).cross(Vector((0, 0, 1))); k = ease(min(1.0, sec / 1.5))
    lp = (h.bone_head("spine02") + forward(h) * 0.3).lerp(c["lock_at"], k)
    reach(h, "R", lp + Vector((0, -0.04, 0)), Vector((sd.x, sd.y, -0.7)), forward(h)); c["lock"].location = lp
    i = c["people"]["insp"]; st2 = STORE + Vector((-0.45, 0.85, 0)); stand_pose(i); place(i, st2, face_angle(st2, STORE))
    s2 = forward(i).cross(Vector((0, 0, 1))); k2 = ease(min(1.0, max(0.0, (sec - 1.0) / 1.6)))
    sg = (i.bone_head("spine02") + forward(i) * 0.35 + Vector((0, 0, 0.1))).lerp(c["new_sign_at"], k2)
    reach(i, "R", sg + s2 * 0.14, Vector((s2.x, s2.y, -0.7)), forward(i)); reach(i, "L", sg - s2 * 0.14, Vector((-s2.x, -s2.y, -0.7)), forward(i))
    c["new_sign"].location = sg


SHOTS = {
    "ch2_9a": ("room", c2_9a, C(Vector((-4.1, -2.9, 1.7)), Vector((-3.0, -2.9, 1.7)), Vector((0.0, 1.0, 1.6)), 20), None),
    "ch2_9b": ("room", c2_9b, C(Vector((2.6, -1.6, 1.5)), Vector((2.3, -1.3, 1.5)), Vector((0.4, 0.55, 1.1)), 35), 2.8),
    "ch2_10a": ("room", c2_10a, C(Vector((4.2, -2.6, 1.4)), Vector((4.0, -2.2, 1.5)), Vector((0.0, 0.8, 1.7)), 22), None),
    "ch2_10b": ("room", c2_10b, C(Vector((1.6, -1.8, 0.7)), Vector((0.9, -0.9, 0.8)), Vector((0.0, 0.0, 1.9)), 35), 4.0),
    "ch2_11a": ("room", c2_11a, C(Vector((3.0, 1.0, 1.7)), Vector((2.6, 0.6, 1.7)), Vector((-2.4, -2.5, 0.9)), 24), 4.0),
    "ch2_11b": ("room", c2_11b, C(Vector((-10.5, -6.0, 1.4)), Vector((-10.2, -5.9, 1.4)), Vector((-3.6, -3.6, 1.3)), 28), 4.0),
    "ch4_10a": ("room", c4_10a, C(Vector((3.6, 1.6, 1.7)), Vector((3.3, 1.3, 1.7)), Vector((-2.5, -2.0, 1.4)), 24), 4.0),
    "ch4_10b": ("room", c4_10b, C(Vector((STORE.x + 2.6, STORE.y + 2.6, 1.6)), Vector((STORE.x + 2.3, STORE.y + 2.5, 1.6)), Vector((STORE.x, STORE.y + 0.5, 1.3)), 28), 2.8),
}
VARIANT_FOR = {k: v[0] for k, v in SHOTS.items()}
DUR = {k: dur(k) for k in SHOTS}
MOVES = {k: dict(kind="anim", far=60.0, anim=v[1], cam=v[2], dof=v[3]) for k, v in SHOTS.items()}
