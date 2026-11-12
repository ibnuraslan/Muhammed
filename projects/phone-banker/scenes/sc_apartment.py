"""APARTMENT BLOCK, Moscow, June 2006 (dramatization; a generic courtyard). Nine-storey panel blocks, poplars, parked cars.
  wait   : plain-clothes officers wait by their cars in the courtyard (Ch2 10A)
  arrest : a man comes out of the entrance; they step in and walk him to a car (Ch2 10B)"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph
from pbkit import joinm, masonry_facade, soviet_car, ph_instances, birch
from pbpeople import person, stand, walk_at, nod, look, hand_to, hide, fwd

EXPOSURE = -1.6
BOUNCES = 6
DUR = {"wait": 5.5, "arrest": 6.5}
VARIANT_FOR = {"wait": None, "arrest": None}
DOOR = Vector((0.0, 0.0, 0.0))     # entrance at the block's foot; the courtyard is toward -Y


def build(variant=None):
    c = {}
    bpy.context.scene.view_settings.exposure = EXPOSURE
    world_sky(sun_elev_deg=40, sun_rot_deg=120, strength=0.45, tint=(0.88, 0.92, 1.0)); sun(40, 120, 0.9, (1.0, 0.95, 0.88), 1.5)
    box("Courtyard", (0, -12, -0.02), (80, 30, 0.04), ph.texture("asphalt_02", scale=0.25))
    box("Walk", (0, -1.5, 0.0), (60, 3.0, 0.08), ph.texture("concrete_pavers", scale=0.8))
    panel = masonry_facade("PanelBlock", (0.3, 0.3, 0.28), 2.8, 3.0, 1.4, 1.35, 0.0, joints=0.8, glass_coat=0.3, frame_col=(0.55, 0.53, 0.5))
    box("Block", (0, 6.0, 12.6), (60, 12, 25.2), panel)
    box("BlockOpp", (0, -34, 12.6), (60, 12, 25.2), panel)
    box("BlockSide", (-34, -12, 12.6), (12, 40, 25.2), panel)
    # entrance: door, canopy, intercom
    box("EntryCanopy", (0, -0.9, 2.6), (2.2, 1.8, 0.15), pbr("CanopyConc", (0.55, 0.55, 0.52), 0.8))
    c["door"] = joinm([box("EntryDoor", (0.5, 0, 1.05), (1.0, 0.06, 2.1), pbr("SteelDoor", (0.25, 0.22, 0.2), 0.5, 0.6), bevel=0.01)], "EntryDoor")
    c["door"].location = (-0.5, -0.03, 0.0)
    box("EntryDark", (0, 0.05, 1.05), (1.0, 0.02, 2.1), pbr("Stairwell", (0.03, 0.03, 0.03), 0.9))
    box("Intercom", (0.75, -0.06, 1.4), (0.12, 0.03, 0.2), pbr("Intercom", (0.4, 0.4, 0.42), 0.4, 0.8))
    for x in (-2.8, 2.8):
        ph.model("painted_wooden_bench", loc=(x, -2.6, 0), rot_z=0.0)
    ph_instances("tree_small_02", [((-9.0, -6.0, 0), 0.4, 1.6), ((8.5, -7.5, 0), 2.0, 1.5), ((16.0, -5.0, 0), 1.1, 1.7), ((-15.0, -9.0, 0), 3.0, 1.4)])
    # the panel block's life: balconies with railings, washing on lines, air-conditioners, satellite dishes
    slab = pbr("BalconySlab", (0.45, 0.45, 0.43), 0.8); rail = pbr("BalconyRail", (0.25, 0.28, 0.3), 0.5, 0.6)
    laundry = [pbr(f"Wash{k}", col, 0.9) for k, col in enumerate(((0.8, 0.8, 0.78), (0.5, 0.15, 0.12), (0.2, 0.3, 0.5), (0.7, 0.62, 0.3)))]
    r_ = np.random.default_rng(6)
    ac = []
    for fl in range(1, 9):
        for bx in range(-9, 10):
            x = bx * 3.0 + 1.5; z = fl * 2.8
            if (bx + fl) % 3 == 0 or abs(x) < 2.5:
                continue
            box("Balcony", (x, -0.55, z), (1.6, 1.1, 0.12), slab)
            box("BalconyFront", (x, -1.08, z + 0.5), (1.6, 0.04, 0.9), rail if (bx * fl) % 2 else pbr("BalconyGlaze", (0.35, 0.38, 0.4), 0.2, 0.0, **{'Coat Weight': 0.8}))
            if r_.random() < 0.35:
                for j in range(int(r_.integers(2, 5))):
                    box("Washing", (x - 0.55 + j * 0.3, -0.9, z + 1.15), (0.22, 0.01, 0.3 + r_.uniform(0, 0.25)), laundry[int(r_.integers(0, 4))])
            if r_.random() < 0.2:
                ac.append(((x + 1.1, -0.15, z + 1.4), 0.0, 0.5))
    ph_instances("exterior_aircon_unit", ac)
    # a playground: climbing frame and swings (painted steel tube), a sandpit
    PX, PY = 11.5, -3.6                                                         # climbing frame and sandpit, right of the entrance
    SX, SY = 1.0, -3.3                                                           # the swing set (its legs at SX + 4 .. SX + 6)
    tube = pbr("PlayTube", (0.55, 0.12, 0.08), 0.45, 0.4)
    for (x, y) in ((PX - 1.0, PY + 0.8), (PX + 1.0, PY + 0.8), (PX - 1.0, PY - 0.8), (PX + 1.0, PY - 0.8)):
        cyl("FramePost", (x, y, 1.0), 0.03, 2.0, tube, verts=10)
    for z in (0.7, 1.4, 2.0):
        for (y) in (PY + 0.8, PY - 0.8):
            cyl("FrameBar", (PX, y, z), 0.025, 2.0, tube, verts=10, rot=(0, math.radians(90), 0))
    for x in (SX + 4.0, SX + 6.0):
        cyl("SwingLeg", (x, SY, 1.1), 0.04, 2.3, pbr("SwingBlue", (0.15, 0.3, 0.55), 0.45, 0.4), verts=10, rot=(0, math.radians(8 if x < SX + 5 else -8), 0))
    cyl("SwingTop", (SX + 5.0, SY, 2.25), 0.04, 2.0, pbr("SwingBlue2", (0.15, 0.3, 0.55), 0.45, 0.4), verts=10, rot=(0, math.radians(90), 0))
    c["swing"] = joinm([cyl("Chain", (-0.25, 0, -0.75), 0.008, 1.5, rail, verts=6), cyl("Chain", (0.25, 0, -0.75), 0.008, 1.5, rail, verts=6),
                        box("Seat", (0, 0, -1.5), (0.55, 0.22, 0.04), pbr("SeatWood2", (0.4, 0.25, 0.12), 0.6))], "Swing")
    c["swing"].location = (SX + 5.0, SY, 2.22)
    box("Sandpit", (PX + 3.0, PY, 0.12), (2.4, 2.4, 0.24), pbr("SandFrame", (0.4, 0.3, 0.15), 0.7))
    box("Sand", (PX + 3.0, PY, 0.2), (2.2, 2.2, 0.06), pbr("Sand", (0.62, 0.55, 0.4), 0.95))
    ph_instances("tree_small_02", [((x, y, 0), float(r_.uniform(0, 6.28)), float(r_.uniform(1.4, 1.9))) for (x, y) in ((-20, -10), (-14, -18), (12, -18), (22, -9), (-26, -4))])
    birch((-5.6, -3.3, 0), 0.8, 1.5); birch((13.5, -8.5, 0), 2.4, 1.4)                  # birches by the benches and the playground
    # parked cars: two unmarked cars of the officers, a few residents' cars
    c["carA"] = soviet_car("UnmarkedA", (0.55, 0.57, 0.6), kind="lada"); c["carA"].location = (4.5, -5.5, 0); c["carA"].rotation_euler = (0, 0, math.radians(180))
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ v.co for o in [c["carA"]] + list(c["carA"].children_recursive) if o.type == 'MESH' for v in o.data.vertices]
    zt = max(p.z for p in pts); top = [p for p in pts if p.z > zt - 0.04]
    c["roofA"] = (min(p.x for p in top), max(p.x for p in top), min(p.y for p in top), max(p.y for p in top), zt)
    print("[apartment] roof A", [round(v, 2) for v in c["roofA"]])
    c["carB"] = soviet_car("UnmarkedB", (0.08, 0.09, 0.1), kind="volga"); c["carB"].location = (-5.0, -5.8, 0)
    for k, x in enumerate((-12.0, 11.0, 17.0)):
        car = soviet_car(f"Resident{k}", ((0.5, 0.1, 0.08), (0.2, 0.3, 0.35), (0.7, 0.68, 0.6))[k], kind="lada")
        car.location = (x, -6.0, 0)
    c["offs"] = [person(f"Plain{k}", 1.0, yrs, cl, hr, cval=v, hv=0.25, sat=0.3)
                 for k, (yrs, cl, hr, v) in enumerate(((38, "male_casualsuit05", "short02", 0.2), (33, "male_casualsuit02", "short04", 0.3), (45, "male_casualsuit03", "short01", 0.25)))]
    c["man"] = person("Arrested", 1.0, 53, "male_elegantsuit01", "short01", hv=0.35, col=(0.24, 0.25, 0.28))
    # two babushkas on the bench by the entrance (they watch)
    from pbpeople import seat
    c["babushkas"] = []
    for k, x in enumerate((-3.15, -2.45)):
        from pbpeople import babushka
        b = babushka(f"Babushka{k}", 70 + 5 * k, coat=((0.1, 0.1, 0.12), (0.16, 0.12, 0.1))[k], scarf=((0.5, 0.14, 0.1), (0.25, 0.3, 0.45))[k])
        seat(b, (x, -2.45, 0), 0.0, lean=8)
        c["babushkas"].append(b)
    animate(c, 0.0, "wait")
    return c


def animate(c, sec, move):
    o1, o2, o3 = c["offs"]; m = c["man"]
    c["swing"].rotation_euler = (math.radians(14 * math.sin(sec * 2.1)), 0, 0)
    for k, b in enumerate(c["babushkas"]):
        from pbpeople import look as _look
        _look(b, m.bone_head("head") if move == "arrest" else Vector((3.2, -4.6, 1.6)), 0.6)
    if move == "wait":
        hide(m, True)
        rx0, rx1, ry0, ry1, rz = c["roofA"]                                             # forearms on the roof of car A, across it from the door
        stand(o1, ((rx0 + rx1) / 2, ry0 - 0.42, 0), math.radians(180)); nod(o1, "spine04", 12); nod(o1, "head", -4)
        look(o1, DOOR + Vector((0, 0, 1.6)), 0.6)
        hand_to(o1, "L", Vector(((rx0 + rx1) / 2 + 0.22, ry0 + 0.12, rz + 0.03)), hand_dir=Vector((0, 0.5, -0.8)), curl=35)
        hand_to(o1, "R", Vector(((rx0 + rx1) / 2 - 0.2, ry0 + 0.18, rz + 0.03)), hand_dir=Vector((0, 0.5, -0.8)), curl=35)
        stand(o2, (-3.8, -4.7, 0), math.radians(180 - 25)); look(o2, DOOR + Vector((0, 0, 1.6)), 0.8)
        hand_to(o2, "R", o2.bone_head("spine02") + fwd(o2) * 0.1 + Vector((0, 0, -0.2)), curl=40)
        stand(o3, (-5.8, -4.6, 0), math.radians(160)); nod(o3, "head", 12)                   # checks his watch
        hand_to(o3, "L", o3.bone_head("spine03") + fwd(o3) * 0.28 + Vector((0.05, 0, -0.05)), curl=40)
        hand_to(o3, "R", o3.bone_head("spine03") + fwd(o3) * 0.25 + Vector((-0.1, 0, 0.0)), curl=40)
    else:
        hide(m, False)
        op = ease(min(1.0, sec / 0.8))
        c["door"].rotation_euler = (0, 0, math.radians(-70 * op * (1 - ease(min(1.0, max(0.0, (sec - 2.5) / 1.0))))))
        # he comes out and walks a few steps; at 1.6 s they close in from both sides and walk him to car A
        if sec < 1.6:
            p = Vector((0.0, -0.3 - 0.8 * sec, 0))
        else:
            p = Vector((0.0, -1.58, 0)).lerp(Vector((3.0, -4.0, 0)), min(1.0, (sec - 1.6) / 4.5))
        d = (Vector((3.0, -4.0, 0)) - Vector((0.0, -1.58, 0))) if sec >= 1.6 else Vector((0, -1, 0))
        face = math.atan2(d.x, -d.y)
        walk_at(m, sec * 0.8, p, face, stride=18, swing=6 if sec < 1.6 else 2)
        nod(m, "head", 6 if sec < 1.6 else 16)
        s = Vector((math.cos(face), math.sin(face), 0))
        k = min(1.0, max(0.0, (sec - 1.0) / 1.0))
        a0, b0 = Vector(((c['roofA'][0] + c['roofA'][1]) / 2, c['roofA'][2] - 0.42, 0)), Vector((-3.8, -4.7, 0))
        pa = a0.lerp(p + s * 0.55, ease(k)); pb = b0.lerp(p - s * 0.55, ease(k))
        walk_at(o1, sec * 0.85, pa, face if k >= 1 else math.atan2((p - a0).x, -(p - a0).y), stride=20, swing=8)
        walk_at(o2, sec * 0.85 + 0.5, pb, face if k >= 1 else math.atan2((p - b0).x, -(p - b0).y), stride=20, swing=8)
        if k >= 1:
            hand_to(o1, "L", m.bone_head("upperarm01.R") + Vector((0, 0, -0.22)), curl=50)
            hand_to(o2, "R", m.bone_head("upperarm01.L") + Vector((0, 0, -0.22)), curl=50)
        stand(o3, (4.2, -6.4, 0), math.radians(0)); look(o3, m.bone_head("head"), 0.7)       # opens the rear door of car A
    bpy.context.view_layer.update()


def _push(a, b, ta, tb, lens):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(ta).lerp(Vector(tb), ease(t)), lens)


MOVES = {
    "wait": dict(kind="anim", dof=4.0, far=60.0, anim=lambda c, t: animate(c, t * DUR["wait"], "wait"),
                 cam=_push((-3.0, -14.5, 1.75), (-2.4, -13.7, 1.75), (1.3, -3.2, 1.45), (1.3, -3.2, 1.55), 27),
                 focus=lambda c, t: Vector((3.2, -4.6, 1.4))),
    "arrest": dict(kind="anim", dof=4.0, far=60.0, anim=lambda c, t: animate(c, t * DUR["arrest"], "arrest"),
                   cam=_push((-6.5, -12.5, 1.65), (-5.8, -11.8, 1.65), (0.5, -1.8, 1.3), (2.4, -3.6, 1.3), 30),
                   focus=lambda c, t: c["man"].bone_head("spine03")),
}


_build_set = build


def build(variant=None):
    c = _build_set(variant)
    from pbkit import finish_scene
    finish_scene()
    return c
