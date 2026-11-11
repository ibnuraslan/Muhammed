"""APARTMENT BLOCK, Moscow, June 2006 (dramatization; a generic courtyard). Nine-storey panel blocks, poplars, parked cars.
  wait   : plain-clothes officers wait by their cars in the courtyard (Ch2 10A)
  arrest : a man comes out of the entrance; they step in and walk him to a car (Ch2 10B)"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import ph
from pbkit import joinm, masonry_facade, soviet_car, ph_instances
from pbpeople import person, stand, walk_at, nod, look, hand_to, hide, fwd

EXPOSURE = -1.0
BOUNCES = 6
DUR = {"wait": 5.5, "arrest": 6.5}
VARIANT_FOR = {"wait": None, "arrest": None}
DOOR = Vector((0.0, 0.0, 0.0))     # entrance at the block's foot; the courtyard is toward -Y


def build(variant=None):
    c = {}
    world_sky(sun_elev_deg=40, sun_rot_deg=120, strength=0.45, tint=(0.88, 0.92, 1.0)); sun(40, 120, 1.3, (1.0, 0.95, 0.88), 1.5)
    box("Courtyard", (0, -12, -0.02), (80, 30, 0.04), ph.texture("asphalt_02", scale=0.25))
    box("Walk", (0, -1.5, 0.0), (60, 3.0, 0.08), ph.texture("concrete_pavers", scale=0.8))
    panel = masonry_facade("PanelBlock", (0.38, 0.38, 0.37), 2.8, 3.0, 1.4, 1.35, 0.0)
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
        ph.model("painted_wooden_bench", loc=(x, -2.6, 0), rot_z=math.pi)
    ph_instances("tree_small_02", [((-9.0, -6.0, 0), 0.4, 1.6), ((8.5, -7.5, 0), 2.0, 1.5), ((16.0, -5.0, 0), 1.1, 1.7), ((-15.0, -9.0, 0), 3.0, 1.4)])
    # parked cars: two unmarked cars of the officers, a few residents' cars
    c["carA"] = soviet_car("UnmarkedA", (0.55, 0.57, 0.6), kind="lada"); c["carA"].location = (4.5, -5.5, 0); c["carA"].rotation_euler = (0, 0, math.radians(180))
    c["carB"] = soviet_car("UnmarkedB", (0.08, 0.09, 0.1), kind="volga"); c["carB"].location = (-5.0, -5.8, 0)
    for k, x in enumerate((-12.0, 11.0, 17.0)):
        car = soviet_car(f"Resident{k}", ((0.5, 0.1, 0.08), (0.2, 0.3, 0.35), (0.7, 0.68, 0.6))[k], kind="lada")
        car.location = (x, -6.0, 0)
    c["offs"] = [person(f"Plain{k}", 1.0, yrs, cl, hr, cval=v, hv=0.25, sat=0.3)
                 for k, (yrs, cl, hr, v) in enumerate(((38, "male_casualsuit05", "short02", 0.2), (33, "male_casualsuit02", "short04", 0.3), (45, "male_casualsuit03", "short01", 0.25)))]
    c["man"] = person("Arrested", 1.0, 53, "male_elegantsuit01", "short01", cval=0.25, hv=0.35, hue=0.6, sat=0.4)
    animate(c, 0.0, "wait")
    return c


def animate(c, sec, move):
    o1, o2, o3 = c["offs"]; m = c["man"]
    if move == "wait":
        hide(m, True)
        stand(o1, (3.2, -4.6, 0), math.radians(180 + 20)); nod(o1, "head", 4)              # leaning by the car, eyes on the door
        look(o1, DOOR + Vector((0, 0, 1.6)), 0.8)
        hand_to(o1, "L", Vector((3.6, -5.0, 1.0)), curl=20)
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
        a0, b0 = Vector((3.2, -4.6, 0)), Vector((-3.8, -4.7, 0))
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
                 cam=_push((-1.5, -13.0, 1.6), (-1.0, -12.0, 1.6), (0.0, -2.0, 1.5), (0.0, -2.0, 1.6), 30),
                 focus=lambda c, t: Vector((3.2, -4.6, 1.4))),
    "arrest": dict(kind="anim", dof=4.0, far=60.0, anim=lambda c, t: animate(c, t * DUR["arrest"], "arrest"),
                   cam=_push((-6.5, -12.5, 1.65), (-5.8, -11.8, 1.65), (0.5, -1.8, 1.3), (2.4, -3.6, 1.3), 30),
                   focus=lambda c, t: c["man"].bone_head("spine03")),
}
