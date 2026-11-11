"""THE HOUSE, interiors (ground floor, upstairs, closet, cellar). Same geometry as sc_hx; variants set the light.
Variants: day (autumn daylight through the windows), night (bulbs / lamps / moon), dusk (lamp-lit evening).
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import house as H
from house import reset_pose
from house import G, D2, F2, C1, C2, EAVE, HATCH
from human import fingers_curl, reach, pose_sit

DUR = {}
VARIANT_FOR = {}
MOVES = {}
_CAST = {}


def move(name, variant, dur, cast=(), dof=None, title=None, rooms=None, haze=None):
    """Register a move: decorator for (cam_fn, anim_fn) pairs defined below."""
    def deco(fn):
        cam, anim = fn()
        DUR[name] = dur; VARIANT_FOR[name] = (variant, tuple(cast), rooms, haze, name)
        MOVES[name] = dict(kind="anim", dof=dof, far=30, cam=cam, anim=anim, **({"title": title} if title else {}))
        return fn
    return deco


def build(variant=None):
    tod, cast, rooms, hz, name = variant or ("day", (), None, None, "")
    season = "autumn"
    c = H.build_house(season, "night" if tod in ("night", "dusk") else "day", ext=(tod == "day"),
                      rooms=rooms or ("kitchen", "front", "bedroom", "upstairs", "attic", "cellar"), haze_room=hz)
    s = bpy.context.scene
    if tod == "day":
        # daylight interiors: portals in the windows + soft hidden bounce from the window side
        for (x, y, rz) in ((-2.4, -D2 + 0.2, 0), (2.6, -D2 + 0.2, 0), (1.1, D2 - 0.2, math.pi), (-2.9, D2 - 0.2, math.pi)):
            H.day_fill((x, y, 1.6), 1.4, 120, (0.92, 0.95, 1.0), rot=(math.radians(90 if rz == 0 else -90), 0, 0))
        for (x, y, z) in ((-2.4, -2.5, 2.5), (2.6, -2.5, 2.5), (1.2, 2.2, 2.5), (-2.4, -2.5, 5.2)):
            H.day_fill((x, y, z), 2.0, 60, (1.0, 0.95, 0.88))
        s.view_settings.exposure = 0.3
    elif tod == "dusk":
        s.view_settings.exposure = 0.7
    else:
        s.view_settings.exposure = 1.4
        for k in ("lamp", "bed_lamp", "k_light", "up_light", "cellar_light"):
            if k in c:
                c[k].data.energy = 0.0
        # cool moonlight through the windows (soft, hidden)
        for (x, z) in ((-2.4, 1.6), (2.6, 1.6), (-2.4, F2 + 1.5), (2.6, F2 + 1.5)):
            H.day_fill((x, -D2 + 0.45, z), 1.2, 30, (0.55, 0.68, 1.0), rot=(math.radians(65), 0, 0))
        H.day_fill((1.1, D2 - 0.45, 1.7), 1.0, 15, (0.55, 0.68, 1.0), rot=(math.radians(-65), 0, 0))
    c["tod"] = tod
    c["cast"] = {}
    for k in cast:
        c["cast"][k.split(":")[0]] = H.person(k.split(":")[-1].capitalize() + k.split(":")[0], k.split(":")[-1])
    _CAST.clear(); _CAST.update(c["cast"])
    return c


def P(c, key):
    return c["cast"][key]


# =========================================================================== INTRO
@move("hall_beams", "night", 4.0, cast=("o1:officer", "o2:officer"), haze=((-0.6, -4.7, 0.0), (0.9, -0.2, 2.7)))
def _():
    def anim(c, t):
        sec = t * DUR["hall_beams"]
        if "beams" not in c:
            c["beams"] = [H.flashlight("T1"), H.flashlight("T2")]
            for b in c["beams"]:
                b.data.energy = 300
        o1, o2 = P(c, "o1"), P(c, "o2")
        H.walk_to(o1, (0.15, -4.4, 0), (0.15, -3.4, 0), t * 0.6, swing=6)
        H.stand_at(o2, (-0.25, -4.3, 0), math.radians(165))
        for k, (h, sw) in enumerate(((o1, 1.0), (o2, -1.0))):
            hd = h.bone_head("head")
            a = 0.9 * math.sin(0.9 * sec + k * 2.0) * sw
            tgt = Vector((hd.x + 1.8 + 1.4 * math.sin(a), hd.y + 1.5 + 1.0 * math.cos(a), 0.6 + 0.5 * math.sin(1.3 * sec + k)))
            H.aim_obj(c["beams"][k], hd + Vector((0.2 * sw, -0.15, -0.35)), tgt)
            reach(h, "R", hd + Vector((0.18 * sw, 0.25, -0.35)), Vector((0.3, -0.5, -1)), (tgt - hd).normalized())
    def cam(c, t):
        e = ease(t)
        return (Vector((3.4, -0.9, 1.6)).lerp(Vector((2.6, -0.8, 1.7)), e), Vector((0.2, -3.9, 1.3)).lerp(Vector((0.3, -1.5, 2.0)), e), 26)
    return cam, anim


@move("closet_creep", "night", 5.0, rooms=("upstairs", "attic"))
def _():
    def anim(c, t):
        if "moonwin" not in c:
            c["moonwin"] = H.day_fill((-2.4, -D2 + 0.35, F2 + 1.6), 1.0, 40, (0.55, 0.68, 1.0), rot=(math.radians(70), 0, 0))
    def cam(c, t):
        e = ease(t)
        return (Vector((-3.6, -4.2, F2 + 1.6)).lerp(Vector((-2.7, -2.8, F2 + 1.75)), e), Vector((-1.25, -1.2, F2 + 1.3)).lerp(Vector((-1.25, -1.2, F2 + 1.8)), e), 30)
    return cam, anim


# =========================================================================== CH1
@move("guitar", "dusk", 5.0, cast=("p:philip",), rooms=("front", "kitchen"))
def _():
    def anim(c, t):
        sec = t * DUR["guitar"]
        h = P(c, "p"); fz = math.radians(-60)
        if "posed_chair" not in c:
            c["armchair"].rotation_euler = (0, 0, fz); c["armchair"].location = (3.2, -2.0, 0); c["posed_chair"] = True
        reset_pose(h); pose_sit(h, lean=8)
        h.arm.rotation_euler = (0, 0, fz); h.arm.location = (3.2, -2.0, 0); bpy.context.view_layer.update()
        H.ground_to(h, 0.0)
        M = h.arm.matrix_world.to_3x3(); fwd = (M @ Vector((0, -1, 0))).normalized(); left = (M @ Vector((1, 0, 0))).normalized()
        up = Vector((0, 0, 1))
        if "guitar" not in c:
            import ph
            g, _ = ph.model("Ukulele_01", scale=1.9); c["guitar"] = g
        hip = h.bone_head("spine01")
        base = hip + fwd * 0.32 - left * 0.34 - up * 0.12
        axis = (left * 0.96 + up * 0.27).normalized()
        g = c["guitar"]; g.location = base; g.rotation_euler = (0, math.radians(74), fz)
        if "key" not in c:
            c["key"] = H.day_fill((1.4, -3.2, 1.9), 1.2, 30, (1.0, 0.72, 0.45), rot=(math.radians(60), 0, math.radians(-120)))
        strum = 0.035 * math.sin(2 * math.pi * 1.4 * sec)
        reach(h, "R", base + axis * 0.22 + fwd * 0.06 + up * strum, -left - up, (axis * -0.3 - up).normalized())
        reach(h, "L", base + axis * 0.82 + fwd * 0.03, -up + fwd * 0.3, (-fwd + up * 0.3).normalized())
        fingers_curl(h, 45)
        H.look(h, 20, 22 + 2 * math.sin(sec))
    def cam(c, t):
        e = ease(t)
        return (Vector((1.2, -4.2, 1.4)).lerp(Vector((1.6, -3.8, 1.35)), e), Vector((3.2, -2.0, 0.85)), 32)
    return cam, anim


DUR["guitar_dolly"] = 5.0; VARIANT_FOR["guitar_dolly"] = VARIANT_FOR["guitar"]
MOVES["guitar_dolly"] = dict(MOVES["guitar"], cam=lambda c, t: (Vector((1.2, -4.35, 0.95)).lerp(Vector((2.3, -4.4, 1.05)), ease(t)),
                                                                   Vector((2.2, -3.6, 0.7)).lerp(Vector((3.2, -2.0, 0.95)), ease(t)), 30))


@move("aftermath_push", "dusk", 5.0, rooms=("bedroom",))
def _():
    def anim(c, t):
        sec = t * DUR["aftermath_push"]
        if "fallen" not in c:
            ch = c["bed_chair"]; ch.location = (-2.3, -2.6, 0.22); ch.rotation_euler = (math.radians(90), 0, math.radians(70))
            c["fallen"] = True
            b = c["bed_bulb_obj"]; c["swing"] = b
            c["bulb_light"] = H.point((-2.4, -2.4, C1 - 0.6), 18, (1.0, 0.7, 0.42), 0.03)
            cord = box("Cord", (-2.4, -2.4, C1 - 0.25), (0.008, 0.008, 0.5), H.mat("black")); c["cord"] = cord
        a = math.radians(9) * math.cos(1.9 * sec) * math.exp(-0.05 * sec)
        piv = Vector((-2.4, -2.4, C1))
        off = Vector((0.0, math.sin(a), -math.cos(a))) * 0.6
        c["cord"].location = piv + off * 0.5; c["cord"].rotation_euler = (a, 0, 0)
        c["bulb_light"].location = piv + off
        c["swing"].location = piv + off + Vector((0, 0, 0.12)); c["swing"].rotation_euler = (a, 0, 0)
    def cam(c, t):
        e = ease(t)
        return (Vector((-0.3, -1.0, 1.55)).lerp(Vector((-0.9, -1.4, 1.5)), e), Vector((-2.4, -2.7, 0.95)).lerp(Vector((-2.6, -2.8, 1.05)), e), 24)
    return cam, anim


@move("kitchen_latch", "day", 4.5, cast=("d:detective",), rooms=("kitchen",))
def _():
    def anim(c, t):
        sec = t * DUR["kitchen_latch"]
        h = P(c, "d")
        H.stand_at(h, (2.75, 4.05, 0), math.radians(160))
        knob = Vector((3.48, D2 - 0.17, 0.95))
        u = min(1.0, sec / 1.2)
        rest = h.bone_head("upperarm01.R") + Vector((0, 0.1, -0.55))
        tgt = rest.lerp(knob, ease(u)) + Vector((0, 0, 0.02 * math.sin(10 * sec) if sec > 1.4 and sec < 2.6 else 0))
        reach(h, "R", tgt, Vector((1, -0.3, -0.5)), Vector((0, 1, -0.3)))
        fingers_curl(h, 45)
        shake = math.radians(9) * math.sin(6 * (sec - 3.0)) if 3.0 < sec < 4.2 else 0.0
        H.look(h, math.degrees(shake), 8)
    def cam(c, t):
        e = ease(t)
        return (Vector((1.6, 2.6, 1.6)).lerp(Vector((1.8, 2.9, 1.6)), e), Vector((3.2, 4.6, 1.1)), 30)
    return cam, anim


@move("kitchen_glide", "day", 5.0, cast=("d:detective2",), rooms=("kitchen",))
def _():
    def anim(c, t):
        sec = t * DUR["kitchen_glide"]
        h = P(c, "d")
        H.stand_at(h, (2.2, 0.9, 0), math.radians(160))
        if "pad" not in c:
            c["pad"] = box("Notebook", (0, 0, 0), (0.1, 0.15, 0.012), pbr("Pad", (0.85, 0.83, 0.75), 0.8))
        sh = h.bone_head("spine05" if False else "neck01"); M = h.arm.matrix_world.to_3x3()
        fwd = M @ Vector((0, -1, 0)); left = M @ Vector((1, 0, 0))
        pad = sh + fwd * 0.32 + Vector((0, 0, -0.38))
        c["pad"].location = pad; c["pad"].rotation_euler = (math.radians(35), 0, h.arm.rotation_euler.z)
        reach(h, "L", pad + left * 0.05, left + Vector((0, 0, -1)), fwd)
        reach(h, "R", pad - left * 0.03 + Vector((0.02 * math.sin(7 * sec), 0, 0.02)), -left + Vector((0, 0, -1)), fwd)
        H.look(h, 0, 25)
    def cam(c, t):
        e = ease(t)
        return (Vector((-1.0, 3.6, 1.5)).lerp(Vector((1.0, 3.2, 1.45)), e), Vector((3.4, 1.4, 0.9)).lerp(Vector((2.4, 0.9, 1.3)), e), 30)
    return cam, anim


@move("doorway_behind", "dusk", 4.5, cast=("m:neighbour_m", "w:neighbour_w"), rooms=("bedroom", "front", "kitchen"))
def _():
    """From behind: the couple stop in the front-bedroom doorway; she turns away into his shoulder."""
    def anim(c, t):
        sec = t * DUR["doorway_behind"]
        if "fallen" not in c:
            ch = c["bed_chair"]; ch.location = (-2.3, -2.6, 0.22); ch.rotation_euler = (math.radians(90), 0, math.radians(70)); c["fallen"] = True
            c["bed_lamp"].data.energy = 8
        m, w = P(c, "m"), P(c, "w")
        u = min(1.0, sec / 1.6)
        H.walk_to(m, (0.2, -1.4, 0), (-0.45, -1.35, 0), u, swing=6, face=math.radians(-90))
        turn = ease(min(1.0, max(0.0, (sec - 2.0) / 1.0)))
        H.walk_to(w, (0.3, -0.85, 0), (-0.25, -0.9, 0), u, swing=6, face=math.radians(-90) + turn * math.radians(150))
        if turn > 0:
            H.rotl(w, "head", (1, 0, 0), 15 * turn)
            reach(w, "R", m.bone_head("upperarm01.L") + Vector((0.05, 0.05, -0.15)), Vector((0, 0, -1)), Vector((-1, 0, 0)))
    def cam(c, t):
        e = ease(t)
        return (Vector((0.75, -0.3, 1.7)).lerp(Vector((0.7, -0.45, 1.7)), e), Vector((-2.4, -2.2, 1.0)), 26)
    return cam, anim


@move("tool_floor", "dusk", 5.0, rooms=("bedroom",))
def _():
    def anim(c, t):
        sec = t * DUR["tool_floor"]
        if "placed" not in c:
            tl = H.shaker_tool("FloorTool"); tl.location = (-2.9, -3.3, 0.0); tl.rotation_euler = (0, 0, math.radians(-25)); c["placed"] = True
            ch = c["bed_chair"]; ch.location = (-2.0, -2.4, 0.22); ch.rotation_euler = (math.radians(90), 0, math.radians(70))
            c["bed_lamp"].data.energy = 10
            c["dust"] = H.leaf_cloud(40, (-2.6, -3.0), (1.2, 1.0), 1.8, col=(0.8, 0.75, 0.65), seed=9)
            for o in c["dust"]:
                o.scale = (0.03, 0.03, 1)
        H.fall_leaves(c["dust"], sec * 0.08, ground=0.0, drift=(0.02, 0.01))
    def cam(c, t):
        e = ease(t)
        return (Vector((-0.9, -1.3, 0.18)).lerp(Vector((-1.2, -1.6, 0.16)), e), Vector((-2.9, -3.3, 0.05)), 40)
    return cam, anim


@move("flash_hall", "night", 4.0, cast=("ph:detective2", "d:detective"), rooms=("bedroom", "front", "kitchen"))
def _():
    def anim(c, t):
        sec = t * DUR["flash_hall"]
        if "flash" not in c:
            c["flash"] = H.point((0, 0, 0), 0, (0.92, 0.95, 1.0), 0.08)
            c["hallbulb"] = H.point((0.2, -2.5, C1 - 0.3), 25, (1.0, 0.7, 0.42), 0.05)
            c["camera_box"] = box("PressCam", (0, 0, 0), (0.14, 0.12, 0.12), H.mat("black"), bevel=0.01)
        phg, d = P(c, "ph"), P(c, "d")
        H.stand_at(phg, (-0.2, -2.0, 0), math.radians(90))
        H.stand_at(d, (0.35, -3.5, 0), math.radians(160))
        hd = phg.bone_head("head"); M = phg.arm.matrix_world.to_3x3(); fwd = M @ Vector((0, -1, 0))
        cp = hd + fwd * 0.25 + Vector((0, 0, -0.08)); c["camera_box"].location = cp; c["camera_box"].rotation_euler = (0, 0, phg.arm.rotation_euler.z)
        reach(phg, "R", cp + Vector((0, -0.08, -0.04)), Vector((0, 0, -1)), fwd); reach(phg, "L", cp + Vector((0, 0.08, -0.04)), Vector((0, 0, -1)), fwd)
        pops = (1.2, 3.0)
        e = sum(max(0.0, 1 - abs(sec - p) / 0.06) for p in pops)
        c["flash"].location = cp + fwd * 0.1 + Vector((0, 0, 0.15)); c["flash"].data.energy = 4000 * e
        H.look(d, 20, 5)
    def cam(c, t):
        e = ease(t)
        return (Vector((0.55, -0.6, 1.6)).lerp(Vector((0.45, -0.9, 1.6)), e), Vector((-1.2, -2.8, 1.3)), 28)
    return cam, anim


@move("tilt_ceiling", "day", 5.0, cast=("d1:detective", "d2:detective2"), rooms=("upstairs", "attic"))
def _():
    def anim(c, t):
        sec = t * DUR["tilt_ceiling"]
        c["closet_door"].rotation_euler = (0, 0, math.radians(-100))
        d1, d2 = P(c, "d1"), P(c, "d2")
        H.stand_at(d1, (-2.6, -2.0, F2), math.radians(60), z=F2)
        H.stand_at(d2, (-2.0, -2.9, F2), math.radians(240), z=F2)
        H.look(d1, 5 * math.sin(sec), 4); H.look(d2, -5 * math.sin(1.3 * sec), 0)
    def cam(c, t):
        e = ease(t)
        tgt = Vector((-2.3, -2.4, F2 + 1.5)).lerp(Vector((-1.2, -0.75, C2 - 0.05)), e)
        return (Vector((-3.8, -4.3, F2 + 1.55)).lerp(Vector((-3.6, -4.1, F2 + 1.4)), e), tgt, 26)
    return cam, anim


@move("helen_return", "day", 5.0, cast=("hl:helen", "f:friend"), rooms=("front", "bedroom", "kitchen"))
def _():
    def anim(c, t):
        sec = t * DUR["helen_return"]
        c["front_door"].rotation_euler = (0, 0, math.radians(-80) * ease(min(1.0, sec / 1.0)))
        if "cane" not in c:
            c["cane"] = cyl("Cane", (0, 0, 0), 0.012, 0.9, H.mat("oak"), 10)
            import ph
            r, ms = ph.model("vintage_suitcase", scale=0.8); c["case"] = r
            for o in ms:
                if "02" in o.name:
                    o.hide_render = True
        hl, f = P(c, "hl"), P(c, "f")
        H.walk_to(hl, (0.15, -D2 - 0.4, 0), (0.1, -3.2, 0), min(1.0, sec / 5.0) * 0.9, swing=3, stride=0.6)
        wr = hl.bone_tail("wrist.R")
        cane_tip = Vector((wr.x + 0.05, wr.y - 0.1, 0.0)); d = (wr - cane_tip).normalized()
        c["cane"].location = cane_tip.lerp(wr, 0.5); c["cane"].rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        H.walk_to(f, (0.3, -D2 - 1.6, -0.06), (0.4, -4.0, 0), max(0.0, (sec - 0.8) / 4.2) * 0.9, swing=10, floor=0.0)
        carry(f, c["case"])
    def cam(c, t):
        e = ease(t)
        return (Vector((-0.3, -1.0, 1.55)).lerp(Vector((-0.35, -1.4, 1.5)), e), Vector((0.2, -4.4, 1.1)), 28)
    return cam, anim


def carry(h, obj, side="R", off=(0, 0, -0.12)):
    w = h.bone_tail(f"wrist.{side}")
    obj.location = w + Vector(off); obj.rotation_euler = (0, 0, h.arm.rotation_euler.z + math.pi / 2)


def _tea_pose(c, sec):
    hl, f = P(c, "hl"), P(c, "f")
    for h, (x, y, rz) in ((hl, (0.55, 1.9, math.radians(-90))), (f, (1.85, 1.9, math.radians(90)))):
        reset_pose(h); pose_sit(h, lean=6)
        h.arm.rotation_euler = (0, 0, rz); h.arm.location = (x, y, 0); bpy.context.view_layer.update(); H.ground_to(h, 0.0)
    if "cups" not in c:
        c["cups"] = [cyl("Cup", (0.95, 1.95, 0.80), 0.04, 0.07, H.mat("enamel"), 20), cyl("Cup", (1.45, 1.85, 0.80), 0.04, 0.07, H.mat("enamel"), 20)]
        cyl("Pot", (1.2, 2.15, 0.84), 0.08, 0.15, H.mat("enamel"), 24)
    sip = max(0.0, math.sin(2 * math.pi * (sec - 1.0) / 3.5)) if sec > 1.0 else 0.0
    cup = c["cups"][0]; hd = hl.bone_head("head")
    cup.location = Vector((0.95, 1.95, 0.80)).lerp(hd + Vector((0.12, 0, -0.08)), sip)
    reach(hl, "R", cup.location + Vector((-0.02, -0.06, 0.0)), Vector((0, 0, -1)), Vector((1, 0, 0)))
    reach(f, "L", c["cups"][1].location + Vector((0.04, 0.05, 0.0)), Vector((0, 0, -1)), Vector((-1, 0, 0)))
    H.look(hl, 0, 6); H.look(f, 0, 10)


@move("tea_table", "day", 5.0, cast=("hl:helen", "f:friend"), rooms=("kitchen", "upstairs"))
def _():
    def anim(c, t):
        _tea_pose(c, t * DUR["tea_table"])
        for ch in c["k_chairs"][:2]:
            ch.hide_render = True
    def cam(c, t):
        e = ease(t)
        return (Vector((1.2, -0.0, 1.5)).lerp(Vector((1.2, 0.2, 1.75)), e), Vector((1.2, 2.0, 0.9)).lerp(Vector((1.2, 2.6, C1 + 0.1)), e), 28)
    return cam, anim


@move("icebox_open", "day", 4.5, cast=("f:friend",), rooms=("kitchen",))
def _():
    def anim(c, t):
        sec = t * DUR["icebox_open"]
        h = P(c, "f")
        H.stand_at(h, (-0.6, 3.4, 0), math.radians(170))
        op = ease(min(1.0, sec / 1.3))
        c["ice_door"].rotation_euler = (0, 0, math.radians(-100) * op)
        if "food" not in c:
            # a nearly empty shelf: one plate, an empty bottle (seen inside when the door opens)
            box("IceInside", (-0.85, 4.28, 0.52), (0.66, 0.42, 0.72), pbr("Zinc", (0.55, 0.57, 0.57), 0.35, 0.8)).hide_render = False
            cyl("IcePlate", (-0.95, 4.2, 0.45), 0.1, 0.015, H.mat("enamel"), 24)
            cyl("Bottle", (-0.65, 4.2, 0.55), 0.03, 0.2, pbr("Milk", (0.85, 0.85, 0.82), 0.2, 0.0, **{'Transmission Weight': 0.6}), 16)
            c["food"] = True
        reach(h, "L", Vector((-1.15, 4.0, 0.62)) if op < 0.9 else Vector((-1.25, 3.9, 0.75)), Vector((0, 0, -1)), Vector((0, 1, 0)))
        H.rotl(h, "spine03", (1, 0, 0), 14); H.look(h, -6 if sec > 2.4 else 0, 22)
    def cam(c, t):
        e = ease(t)
        return (Vector((0.9, 2.3, 1.45)).lerp(Vector((0.7, 2.6, 1.45)), e), Vector((-0.8, 4.0, 0.8)), 30)
    return cam, anim


@move("chair_moved", "day", 4.5, cast=("f:friend",), rooms=("kitchen",))
def _():
    def anim(c, t):
        sec = t * DUR["chair_moved"]
        ch = c["k_chairs"][2]; ch.location = (3.0, 1.6, 0); ch.rotation_euler = (0, 0, math.radians(110))
        h = P(c, "f")
        H.stand_at(h, (0.6, 0.6, 0), math.radians(-120) + math.radians(8) * ease(min(1.0, sec / 3.0)))
        H.look(h, 0, 4)
    def cam(c, t):
        e = ease(t)
        return (Vector((-0.6, 0.2, 1.5)).lerp(Vector((-0.4, 0.35, 1.48)), e), Vector((3.0, 1.6, 0.6)).lerp(Vector((2.2, 1.3, 0.9)), e), 30)
    return cam, anim


@move("bed_listen", "night", 5.0, cast=("hl:helen",), rooms=("bedroom",))
def _():
    def anim(c, t):
        sec = t * DUR["bed_listen"]
        h = P(c, "hl")
        reset_pose(h); pose_sit(h, lean=4)
        h.arm.rotation_euler = (0, 0, math.radians(-90)); h.arm.location = (-3.0, -2.1, 0); bpy.context.view_layer.update(); H.ground_to(h, 0.0)
        up = ease(min(1.0, max(0.0, (sec - 1.2) / 1.5)))
        H.look(h, -10 * up, -28 * up)
        if "moonbed" not in c:
            c["moonbed"] = H.day_fill((-2.4, -D2 + 0.4, 1.6), 1.0, 25, (0.55, 0.68, 1.0), rot=(math.radians(60), 0, 0))
    def cam(c, t):
        e = ease(t)
        return (Vector((-1.0, -3.6, 1.2)).lerp(Vector((-1.3, -3.3, 1.25)), e), Vector((-3.0, -2.1, 1.1)), 34)
    return cam, anim


@move("stair_dust", "night", 5.0, rooms=("front", "upstairs"), haze=((0.0, -3.6, 0.0), (0.9, -0.2, 5.4)))
def _():
    def anim(c, t):
        sec = t * DUR["stair_dust"]
        if "dust" not in c:
            c["dust"] = H.leaf_cloud(60, (0.45, -1.5), (0.5, 1.5), C2, col=(0.8, 0.78, 0.72), seed=11)
            for o in c["dust"]:
                o.scale = (0.02, 0.02, 1)
            c["moonst"] = H.point((0.45, -0.5, F2 + 2.0), 6, (0.55, 0.68, 1.0), 0.3)
        H.fall_leaves(c["dust"], sec * 0.15, ground=0.0, drift=(0.0, 0.02))
    def cam(c, t):
        e = ease(t)
        return (Vector((0.45, -4.4, 1.0)).lerp(Vector((0.45, -3.3, 1.9)), e), Vector((0.45, -0.5, F2 + 1.2)), 24)
    return cam, anim


# =========================================================================== CH2 (summer 1942, night): the closet
def thin_man(c):
    if "thin" not in c:
        c["thin"] = H.person("Thin", "thin")
    return c["thin"]


def beams(c, n=2, energy=260):
    if "beams" not in c:
        c["beams"] = [H.flashlight("T%d" % k) for k in range(n)]
        for b in c["beams"]:
            b.data.energy = energy
    return c["beams"]


def hold_torch(h, beam, tgt, side="R"):
    hd = h.bone_head("head"); M = h.arm.matrix_world.to_3x3(); fwd = (M @ Vector((0, -1, 0))).normalized()
    lft = (M @ Vector((1, 0, 0))).normalized()
    sg = 1 if side == "L" else -1
    hand = hd + fwd * 0.35 + lft * (0.18 * sg) + Vector((0, 0, -0.42))
    H.aim_obj(beam, hand + fwd * 0.08, tgt)
    reach(h, side, hand, Vector((0, 0, -1)) + lft * sg, (Vector(tgt) - hand).normalized())


@move("burst_hall", "night", 4.0, cast=("d1:detective", "d2:detective2"), rooms=("front", "bedroom", "kitchen", "upstairs"), haze=((-0.6, -4.7, 0.0), (4.2, -0.2, 2.7)))
def _():
    def anim(c, t):
        sec = t * DUR["burst_hall"]
        c["front_door"].rotation_euler = (0, 0, math.radians(-100) * ease(min(1.0, sec / 0.5)))
        bm = beams(c)
        for k, key in enumerate(("d1", "d2")):
            h = P(c, key); u = max(0.0, min(1.0, (sec - 0.3 - 0.5 * k) / 2.5))
            H.walk_to(h, (0.15 - 0.3 * k, -D2 - 0.4, 0.0), (0.0 + 1.6 * k, -3.0 + 0.4 * k, 0.0), u, swing=10, stride=1.5)
            a = math.sin(1.4 * sec + 2 * k)
            hold_torch(h, bm[k], Vector((-2.5 + 5.5 * k + 1.2 * a, -2.0 + 0.8 * a, 0.9)))
    def cam(c, t):
        e = ease(t)
        return (Vector((0.35, -0.6, 1.65)).lerp(Vector((0.3, -1.0, 1.65)), e), Vector((0.15, -4.8, 1.3)), 26)
    return cam, anim


@move("stairwell_drift", "night", 4.5, cast=("d1:detective",), rooms=("front", "upstairs", "attic"), haze=((0.0, -3.6, 0.0), (0.9, -0.2, 5.4)))
def _():
    def anim(c, t):
        sec = t * DUR["stairwell_drift"]
        bm = beams(c, 1)
        h = P(c, "d1"); H.walk_to(h, (2.2, -2.2, 0.0), (3.0, -1.4, 0.0), t, swing=6, stride=1.0)
        hold_torch(h, bm[0], Vector((3.8, -3.5 + math.sin(sec), 0.8)))
    def cam(c, t):
        e = ease(t)
        return (Vector((0.45, -4.3, 1.4)).lerp(Vector((0.45, -3.6, 2.2)), e), Vector((0.45, -1.0, 2.6)).lerp(Vector((0.4, 0.2, F2 + 1.8)), e), 24)
    return cam, anim


@move("freeze_look", "night", 4.0, cast=("d1:detective", "d2:detective2"), rooms=("front", "upstairs"))
def _():
    def anim(c, t):
        sec = t * DUR["freeze_look"]
        bm = beams(c)
        up = ease(min(1.0, max(0.0, (sec - 0.6) / 0.8)))
        for k, key in enumerate(("d1", "d2")):
            h = P(c, key)
            H.stand_at(h, (0.3 - 0.75 * k, -4.0 - 0.3 * k, 0.0), math.radians(180))
            hold_torch(h, bm[k], Vector((0.45, -0.5, 1.0)).lerp(Vector((0.45, 0.0, F2 + 1.2)), up))
            H.look(h, 0, -30 * up)
    def cam(c, t):
        e = ease(t)
        return (Vector((0.4, -1.2, 1.9)).lerp(Vector((0.4, -1.4, 2.1)), e), Vector((0.0, -4.2, 1.3)), 30)
    return cam, anim


@move("hall_push", "night", 4.5, rooms=("upstairs", "attic"))
def _():
    def anim(c, t):
        c["upbed_door"].rotation_euler = (0, 0, math.radians(80))
    def cam(c, t):
        e = ease(t)
        return (Vector((0.3, 1.4, F2 + 1.55)).lerp(Vector((-0.2, -1.6, F2 + 1.55)), e), Vector((-1.4, -2.6, F2 + 1.2)).lerp(Vector((-1.4, -1.3, F2 + 1.1)), e), 26)
    return cam, anim


@move("closet_open", "night", 4.0, cast=("d1:detective",), rooms=("upstairs", "attic"), haze=((-1.8, -1.2, F2), (-0.6, -0.2, C2)))
def _():
    def anim(c, t):
        sec = t * DUR["closet_open"]
        c["upbed_door"].rotation_euler = (0, 0, math.radians(80))
        op = ease(min(1.0, sec / 1.2))
        c["closet_door"].rotation_euler = (0, 0, math.radians(-105) * op)
        bm = beams(c, 1)
        h = P(c, "d1"); H.stand_at(h, (-1.0, -2.1, F2), math.radians(180), z=F2)
        tgt = Vector((-1.2, -0.6, F2 + 0.8)).lerp(Vector((-1.2, -0.7, C2)), ease(max(0.0, (sec - 1.0) / 2.5)))
        hold_torch(h, bm[0], tgt)
        reach(h, "L", Vector((-1.0, -1.35, F2 + 1.0)) if sec < 1.0 else Vector((-0.8, -1.6, F2 + 0.95)), Vector((0.3, 0, -1)), Vector((0, 1, 0)))
        H.look(h, 0, -30 * ease(max(0.0, (sec - 1.2) / 1.5)))
    def cam(c, t):
        e = ease(t)
        return (Vector((-2.6, -3.3, F2 + 1.4)).lerp(Vector((-2.3, -3.0, F2 + 1.35)), e), Vector((-1.2, -1.1, F2 + 1.3)), 28)
    return cam, anim


def legs_in_hatch(c, rise):
    """The thin man hanging in the hatch: body vertical, hips at the hatch, rising by `rise` metres."""
    h = thin_man(c); hx, hy = HATCH
    reset_pose(h)
    for sd in ("L", "R"):
        H.rotl(h, f"foot.{sd}", (1, 0, 0), 40)
        h.aim(f"upperarm01.{sd}", (0, 0, 1)); h.aim(f"upperarm02.{sd}", (0, 0, 1)); h.aim(f"lowerarm01.{sd}", (0, 0, 1)); h.aim(f"lowerarm02.{sd}", (0, 0, 1))
    H.rotl(h, "upperleg01.L", (0, 1, 0), -3); H.rotl(h, "upperleg01.R", (0, 1, 0), 3)
    h.arm.rotation_euler = (0, 0, math.radians(90)); bpy.context.view_layer.update()
    hip0 = h.joint("upperleg01.L").z if False else 0.95
    h.arm.location = (hx, hy, C2 - hip0 - 0.05 + rise); bpy.context.view_layer.update()
    return h


@move("legs_hatch", "night", 4.0, rooms=("upstairs", "attic"), dof=4.0, haze=((-1.8, -1.2, F2), (-0.6, -0.2, C2)))
def _():
    def anim(c, t):
        sec = t * DUR["legs_hatch"]
        c["closet_door"].rotation_euler = (0, 0, math.radians(-105))
        c["hatch"].location = c["hatch_home"] + Vector((0.4, 0, 0.02))
        rise = 0.55 * ease(min(1.0, sec / 3.6))
        legs_in_hatch(c, rise + 0.15 * math.sin(6 * sec) * 0.1)
        bm = beams(c, 1)
        H.aim_obj(bm[0], Vector((-1.0, -2.2, F2 + 1.2)), Vector((HATCH[0], HATCH[1], C2 - 0.6)))
    def cam(c, t):
        e = ease(t)
        return (Vector((-1.25, -1.1, F2 + 0.35)).lerp(Vector((-1.25, -1.15, F2 + 0.45)), e), Vector((HATCH[0], HATCH[1], C2 - 0.3)), 18, (0, 1, 0))
    return cam, anim


@move("haul_down", "night", 4.0, cast=("d1:detective", "d2:detective2"), rooms=("upstairs", "attic"), haze=((-4.2, -4.7, F2), (-0.6, -0.2, C2)))
def _():
    def anim(c, t):
        sec = t * DUR["haul_down"]
        c["closet_door"].rotation_euler = (0, 0, math.radians(-105))
        c["hatch"].location = c["hatch_home"] + Vector((0.4, 0, 0.02))
        pull = 0.25 * ease(min(1.0, sec / 3.0)) + 0.04 * math.sin(9 * sec)
        h = legs_in_hatch(c, 0.35 - pull)
        bm = beams(c, 1)
        d1, d2 = P(c, "d1"), P(c, "d2")
        H.stand_at(d1, (-1.35, -0.95, F2), math.radians(30), z=F2); H.stand_at(d2, (-1.0, -1.45, F2), math.radians(-20), z=F2)
        ank = h.bone_head("foot.L"); kn = h.bone_head("lowerleg01.R")
        reach(d1, "R", ank + Vector((0.05, 0, 0)), Vector((0, -1, -1)), Vector((0, 0, 1))); reach(d1, "L", ank + Vector((0.0, 0.05, 0.08)), Vector((0, -1, -1)), Vector((0, 0, 1)))
        reach(d2, "R", kn + Vector((0, -0.05, 0)), Vector((0, -1, -1)), Vector((0, 0, 1)))
        H.look(d1, 0, -35); H.look(d2, 0, -40)
        H.aim_obj(bm[0], Vector((-2.4, -2.6, F2 + 0.3)), Vector((-1.2, -0.8, C2 - 0.6)))
    def cam(c, t):
        e = ease(t)
        return (Vector((-3.2, -3.4, F2 + 1.5)).lerp(Vector((-3.0, -3.1, F2 + 1.45)), e), Vector((-1.2, -0.9, F2 + 1.6)), 26)
    return cam, anim


@move("drop_out", "night", 4.0, cast=("d1:detective", "d2:detective2"), rooms=("upstairs", "attic"))
def _():
    def anim(c, t):
        sec = t * DUR["drop_out"]
        c["closet_door"].rotation_euler = (0, 0, math.radians(-105))
        h = thin_man(c)
        u = ease(min(1.0, sec / 3.5))
        H.walk_to(h, (-1.2, -0.9, F2), (-2.1, -2.3, F2), u * 0.8, swing=4, stride=0.8, floor=F2)
        H.rotl(h, "spine03", (1, 0, 0), 25); H.rotl(h, "head", (1, 0, 0), 25)
        d1, d2 = P(c, "d1"), P(c, "d2")
        H.walk_to(d1, (-1.6, -1.4, F2), (-2.5, -2.4, F2), u * 0.8, swing=3, stride=0.8, floor=F2)
        H.stand_at(d2, (-1.0, -1.9, F2), math.radians(200), z=F2)
        reach(d1, "R", h.bone_head("upperarm01.L") + Vector((0, 0, -0.1)), Vector((0, 0, -1)), Vector((1, 0, 0)))
        bm = beams(c, 1); hold_torch(d2, bm[0], h.bone_head("spine05"))
    def cam(c, t):
        e = ease(t)
        return (Vector((-3.5, -4.0, F2 + 1.6)).lerp(Vector((-3.3, -3.8, F2 + 1.55)), e), Vector((-1.7, -1.6, F2 + 1.0)), 28)
    return cam, anim


def thin_on_bed(c, sec):
    h = thin_man(c)
    reset_pose(h); pose_sit(h, lean=22)
    h.arm.rotation_euler = (0, 0, math.radians(0)); h.arm.location = (-3.2, -3.5, F2); bpy.context.view_layer.update(); H.ground_to(h, F2)
    H.rotl(h, "head", (1, 0, 0), 30 + 2 * math.sin(sec))
    return h


@move("gaunt_bed", "night", 4.5, cast=("d1:detective",), rooms=("upstairs", "attic"))
def _():
    def anim(c, t):
        sec = t * DUR["gaunt_bed"]
        c["up_light"].data.energy = 30
        thin_on_bed(c, sec)
        H.stand_at(P(c, "d1"), (-2.3, -4.0, F2), math.radians(-60), z=F2); H.look(P(c, "d1"), 0, 18)
    def cam(c, t):
        e = ease(t)
        return (Vector((-1.5, -1.6, F2 + 1.6)).lerp(Vector((-1.7, -1.9, F2 + 1.55)), e), Vector((-3.0, -3.7, F2 + 0.8)), 30)
    return cam, anim


@move("gaunt_orbit", "night", 5.0, rooms=("upstairs", "attic"), dof=2.8)
def _():
    def anim(c, t):
        c["up_light"].data.energy = 30
        c["closet_door"].rotation_euler = (0, 0, math.radians(-105))
        thin_on_bed(c, t * DUR["gaunt_orbit"])
    def cam(c, t):
        a = math.radians(-60 + 40 * ease(t)); hd = Vector((-3.2, -3.85, F2 + 1.05))
        return (hd + Vector((1.3 * math.sin(a), -1.3 * math.cos(a), 0.15)), hd, 50)
    return cam, anim


@move("officer_hatch", "night", 4.5, cast=("z:officer",), rooms=("upstairs", "attic"))
def _():
    def anim(c, t):
        sec = t * DUR["officer_hatch"]
        c["closet_door"].rotation_euler = (0, 0, math.radians(-105)); c["closet_light"].data.energy = 15
        c["hatch"].location = c["hatch_home"] + Vector((0.4, 0, 0.02))
        if "stool" not in c:
            import ph
            ch, _ = ph.model("dining_chair_02", loc=(-1.2, -0.8, F2), rot_z=math.pi); c["stool"] = ch
        h = P(c, "z")
        rise = 0.47 * ease(min(1.0, sec / 2.5))
        H.stand_at(h, (-1.2, -0.75, F2 + 0.47), math.radians(90), z=F2 + rise)
        for sd in ("L", "R"):
            reach(h, sd, Vector((HATCH[0] + (0.08 if sd == "L" else -0.08), HATCH[1] + (0.14 if sd == "L" else -0.14), C2 + 0.02)), Vector((0, 0, -1)), Vector((0, 0, 1)))
    def cam(c, t):
        e = ease(t)
        return (Vector((-2.2, -2.6, F2 + 1.1)).lerp(Vector((-2.0, -2.3, F2 + 1.2)), e), Vector((-1.2, -0.75, F2 + 1.9)), 28)
    return cam, anim


def attic_light(c, on=True, hot=0.0):
    c["hp_light"].data.energy = 2.5 * hot
    c["coil_mat"].node_tree.nodes["Principled BSDF"].inputs['Emission Strength'].default_value = 6.0 * hot


@move("attic_torch", "night", 4.5, rooms=("upstairs", "attic"), haze=((-4.2, -4.7, EAVE), (4.2, 4.7, 7.2)))
def _():
    def anim(c, t):
        sec = t * DUR["attic_torch"]
        c["hatch"].location = c["hatch_home"] + Vector((0.4, 0, 0.02))
        bm = beams(c, 1, 400)
        hx, hy = HATCH
        a = 1.2 * math.sin(0.8 * sec)
        H.aim_obj(bm[0], Vector((hx, hy, EAVE + 0.15)), Vector((hx + 2.5 * math.sin(a), hy + 2.5 * math.cos(a), EAVE + 0.3)))
    def cam(c, t):
        e = ease(t); hx, hy = HATCH
        return (Vector((hx - 2.6, hy + 2.2, EAVE + 0.55)).lerp(Vector((hx - 2.2, hy + 1.9, EAVE + 0.5)), e), Vector((hx, hy, EAVE + 0.1)), 26)
    return cam, anim


@move("attic_track", "night", 5.0, rooms=("upstairs", "attic"), haze=((-4.2, -4.7, EAVE), (4.2, 4.7, 7.2)))
def _():
    def anim(c, t):
        sec = t * DUR["attic_track"]
        bm = beams(c, 1, 400); hx, hy = HATCH
        H.aim_obj(bm[0], Vector((hx, hy, EAVE + 0.2)), Vector((hx + 0.2 + 0.8 * math.sin(0.5 * sec), hy + 2.0, EAVE + 0.1)))
    def cam(c, t):
        e = ease(t); hx, hy = HATCH
        return (Vector((hx - 3.0, hy + 0.6, EAVE + 0.55)).lerp(Vector((hx - 0.6, hy + 0.9, EAVE + 0.6)), e), Vector((hx + 1.2, hy + 1.6, EAVE + 0.15)), 24)
    return cam, anim


@move("attic_finds", "night", 4.5, rooms=("upstairs", "attic"), haze=((-4.2, -4.7, EAVE), (4.2, 4.7, 7.2)))
def _():
    def anim(c, t):
        sec = t * DUR["attic_finds"]
        bm = beams(c, 1, 400); hx, hy = HATCH
        tgt = Vector((hx - 0.9, hy + 0.6, EAVE + 0.15)).lerp(Vector((hx + 0.9, hy + 0.5, EAVE + 0.05)), ease(t))
        H.aim_obj(bm[0], Vector((hx, hy - 0.1, EAVE + 0.25)), tgt)
    def cam(c, t):
        e = ease(t); hx, hy = HATCH
        return (Vector((hx - 0.3, hy - 0.6, EAVE + 0.45)).lerp(Vector((hx + 0.1, hy - 0.5, EAVE + 0.45)), e), Vector((hx - 0.6, hy + 0.7, EAVE + 0.1)).lerp(Vector((hx + 0.7, hy + 0.6, EAVE + 0.05)), e), 28)
    return cam, anim


@move("recoil", "night", 4.0, cast=("z:officer",), rooms=("upstairs", "attic"))
def _():
    def anim(c, t):
        sec = t * DUR["recoil"]
        c["closet_door"].rotation_euler = (0, 0, math.radians(-105)); c["closet_light"].data.energy = 15
        c["hatch"].location = c["hatch_home"] + Vector((0.4, 0, 0.02))
        if "stool" not in c:
            import ph
            ch, _ = ph.model("dining_chair_02", loc=(-1.2, -0.8, F2), rot_z=math.pi); c["stool"] = ch
        h = P(c, "z")
        down = ease(min(1.0, max(0.0, (sec - 0.4) / 0.8)))
        H.stand_at(h, (-1.2, -0.75 - 0.15 * down, F2 + 0.47), math.radians(90), z=F2 + 0.47 - 0.05 * down)
        H.rotl(h, "spine03", (1, 0, 0), 20 * down); H.rotl(h, "head", (0, 0, 1), -30 * down)
        hd = h.bone_head("head")
        reach(h, "R", hd + Vector((0.12, -0.15, -0.08)), Vector((1, 0, -1)), Vector((0, 1, 0.3)))
    def cam(c, t):
        e = ease(t)
        return (Vector((-3.0, -3.2, F2 + 1.5)).lerp(Vector((-2.8, -3.0, F2 + 1.5)), e), Vector((-1.2, -0.85, F2 + 1.6)), 30)
    return cam, anim


@move("window_air", "night", 4.5, cast=("z:officer", "d2:detective2"), rooms=("upstairs", "attic"))
def _():
    def anim(c, t):
        sec = t * DUR["window_air"]
        c["up_light"].data.energy = 25
        z, d = P(c, "z"), P(c, "d2")
        H.stand_at(z, (-0.85, -3.6, F2), math.radians(-90), z=F2); H.rotl(z, "spine03", (1, 0, 0), 25); H.rotl(z, "head", (1, 0, 0), 25)
        H.stand_at(d, (-2.4, -4.25, F2), math.radians(0), z=F2)
        up = ease(min(1.0, max(0.0, (sec - 0.8) / 1.5)))
        reach(d, "R", Vector((-2.35, -4.75, F2 + 1.0 + 0.4 * up)), Vector((0, 0, -1)), Vector((0, -1, 0.5)))
        reach(d, "L", Vector((-2.55, -4.75, F2 + 1.0 + 0.4 * up)), Vector((0, 0, -1)), Vector((0, -1, 0.5)))
    def cam(c, t):
        e = ease(t)
        return (Vector((-1.4, -1.3, F2 + 1.6)).lerp(Vector((-1.6, -1.5, F2 + 1.6)), e), Vector((-1.8, -4.2, F2 + 1.1)), 28)
    return cam, anim


@move("eyes_hatch", "night", 5.0, rooms=("upstairs", "attic"))
def _():
    def anim(c, t):
        sec = t * DUR["eyes_hatch"]
        c["closet_door"].rotation_euler = (0, 0, math.radians(-105))
        c["hatch"].location = c["hatch_home"] + Vector((0.12, 0, 0.0))
        h = thin_man(c)
        reset_pose(h)
        h.arm.rotation_euler = (math.radians(80), 0, math.radians(0)); h.arm.location = (HATCH[0] - 0.05, HATCH[1] + 1.55, EAVE + 0.02); bpy.context.view_layer.update()
        H.rotl(h, "head", (1, 0, 0), -35)
        if "eyelight" not in c:
            c["eyelight"] = H.point((HATCH[0], HATCH[1] - 0.3, C2 - 0.4), 0.0, (1.0, 0.85, 0.65), 0.01)
        c["eyelight"].data.energy = 0.4 * ease(min(1.0, max(0.0, (sec - 1.5) / 2.0)))
    def cam(c, t):
        e = ease(t); hx, hy = HATCH
        return (Vector((hx - 0.2, hy - 1.0, F2 + 1.3)).lerp(Vector((hx - 0.05, hy - 0.35, C2 - 0.55)), e), Vector((hx, hy, C2)), 35)
    return cam, anim


@move("hotplate_glow", "night", 5.0, rooms=("upstairs", "attic"))
def _():
    def anim(c, t):
        sec = t * DUR["hotplate_glow"]
        attic_light(c, hot=0.8 + 0.2 * math.sin(3 * sec))
        h = thin_man(c)
        reset_pose(h); pose_sit(h, lean=30)
        h.arm.rotation_euler = (0, 0, math.radians(-110)); h.arm.location = (HATCH[0] + 0.3, HATCH[1] + 0.9, EAVE); bpy.context.view_layer.update(); H.ground_to(h, EAVE)
        H.rotl(h, "head", (1, 0, 0), 25)
    def cam(c, t):
        e = ease(t); hx, hy = HATCH
        return (Vector((hx + 2.6, hy - 0.4, EAVE + 0.55)).lerp(Vector((hx + 2.2, hy - 0.2, EAVE + 0.55)), e), Vector((hx + 0.5, hy + 0.8, EAVE + 0.5)), 30)
    return cam, anim


@move("joist_drift", "night", 5.0, rooms=("upstairs", "attic"))
def _():
    def anim(c, t):
        sec = t * DUR["joist_drift"]
        attic_light(c, hot=1.0 - ease(t))
    def cam(c, t):
        e = ease(t); hx, hy = HATCH
        return (Vector((hx + 1.0, hy + 1.6, EAVE + 0.4)).lerp(Vector((hx - 1.6, hy - 0.4, EAVE + 0.3)), e), Vector((hx, hy, EAVE)).lerp(Vector((hx - 3.5, hy - 1.0, EAVE + 0.2)), e), 26)
    return cam, anim


# =========================================================================== CH3: five weeks earlier
@move("club_title", "dusk", 6.0, cast=("p:philip", "hl:helen", "g1:neighbour_m", "g2:friend"), rooms=("front", "kitchen"),
      title=("CHAPTER 3", "Five Weeks Earlier", 12, 132))
def _():
    def anim(c, t):
        sec = t * DUR["club_title"]
        _club(c, sec, with_guest=False)
    def cam(c, t):
        e = ease(t)
        return (Vector((1.3, -0.6, 1.7)).lerp(Vector((1.6, -1.0, 1.6)), e), Vector((3.0, -3.0, 0.9)), 28)
    return cam, anim


@move("club_guest", "dusk", 4.5, cast=("p:philip", "hl:helen", "g1:neighbour_m", "g2:friend", "y:thin"), rooms=("front", "kitchen"))
def _():
    def anim(c, t):
        _club(c, t * DUR["club_guest"], with_guest=True)
    def cam(c, t):
        e = ease(t)
        return (Vector((1.4, -0.7, 1.45)).lerp(Vector((1.55, -0.85, 1.45)), e), Vector((2.6, -2.6, 0.9)), 34)
    return cam, anim


def _club(c, sec, with_guest):
    import ph
    if "gtrs" not in c:
        c["gtrs"] = [ph.model("Ukulele_01", scale=1.9)[0] for _ in range(5)]
        c["lamp"].data.energy = 70
        c["chairs_c"] = []
    ring = [("p", (3.2, -2.0), -60), ("hl", (2.2, -3.6), 20), ("g1", (3.4, -3.6), -20), ("g2", (2.0, -2.0), -130)]
    if with_guest:
        ring.append(("y", (1.7, -2.9), -100))
    for k, (key, (x, y), deg) in enumerate(ring):
        h = P(c, key); fz = math.radians(deg)
        reset_pose(h); pose_sit(h, lean=8)
        h.arm.rotation_euler = (0, 0, fz); h.arm.location = (x, y, 0); bpy.context.view_layer.update(); H.ground_to(h, 0.0)
        M = h.arm.matrix_world.to_3x3(); fwd = (M @ Vector((0, -1, 0))).normalized(); left = (M @ Vector((1, 0, 0))).normalized(); up = Vector((0, 0, 1))
        hip = h.bone_head("spine01"); base = hip + fwd * 0.32 - left * 0.34 - up * 0.12
        axis = (left * 0.96 + up * 0.27).normalized()
        g = c["gtrs"][k]; g.location = base; g.rotation_euler = (0, math.radians(74), fz)
        strum = 0.035 * math.sin(2 * math.pi * 1.4 * sec + k)
        reach(h, "R", base + axis * 0.22 + fwd * 0.06 + up * strum, -left - up, (axis * -0.3 - up).normalized())
        reach(h, "L", base + axis * 0.82 + fwd * 0.03, -up + fwd * 0.3, (-fwd + up * 0.3).normalized())
        fingers_curl(h, 45); H.look(h, 0, 20)
    if "armchair" in c:
        c["armchair"].location = (3.2, -2.0, 0); c["armchair"].rotation_euler = (0, 0, math.radians(-60))
        c["chair2"].location = (8, 8, -20)


@move("back_door_open", "day", 4.5, rooms=("kitchen",))
def _():
    def anim(c, t):
        sec = t * DUR["back_door_open"]
        c["back_door"].rotation_euler = (0, 0, math.radians(75) * ease(min(1.0, max(0.0, (sec - 0.6) / 3.0))))
        if "sunin" not in c:
            c["sunin"] = H.day_fill((3.05, D2 + 0.8, 1.2), 0.9, 0, (1.0, 0.9, 0.75), rot=(math.radians(-70), 0, 0))
        c["sunin"].data.energy = 300 * ease(min(1.0, max(0.0, (sec - 0.6) / 3.0)))
    def cam(c, t):
        e = ease(t)
        return (Vector((1.2, 0.6, 1.4)).lerp(Vector((1.6, 1.2, 1.35)), e), Vector((3.05, D2, 1.1)), 30)
    return cam, anim


@move("closet_look", "day", 4.5, cast=("y:thin",), rooms=("upstairs", "attic"))
def _():
    def anim(c, t):
        sec = t * DUR["closet_look"]
        c["closet_door"].rotation_euler = (0, 0, math.radians(-105) * ease(min(1.0, sec / 1.2)))
        h = P(c, "y"); H.stand_at(h, (-1.25, -1.55, F2), math.radians(180), z=F2)
        H.look(h, 0, -38 * ease(min(1.0, max(0.0, (sec - 1.4) / 1.2))))
        reach(h, "L", Vector((-0.85, -1.75, F2 + 0.95)), Vector((0.3, 0, -1)), Vector((0, 1, 0)))
    def cam(c, t):
        e = ease(t)
        return (Vector((-3.4, -3.6, F2 + 1.5)).lerp(Vector((-3.1, -3.3, F2 + 1.45)), e), Vector((-1.2, -1.2, F2 + 1.4)), 30)
    return cam, anim


@move("hatch_slide", "day", 4.5, rooms=("upstairs", "attic"), dof=4.0)
def _():
    def anim(c, t):
        sec = t * DUR["hatch_slide"]
        c["closet_door"].rotation_euler = (0, 0, math.radians(-105))
        c["hatch"].location = c["hatch_home"] + Vector((0.32 * ease(min(1.0, max(0.0, (sec - 0.8) / 2.5))), 0, 0.02))
        if "dust" not in c:
            c["dust"] = H.leaf_cloud(25, HATCH, (0.12, 0.2), C2 - 0.05, col=(0.75, 0.7, 0.6), seed=5)
            for o in c["dust"]:
                o.scale = (0.012, 0.012, 1)
        H.fall_leaves(c["dust"], sec * 0.25, ground=F2, drift=(0.0, 0.0))
    def cam(c, t):
        e = ease(t)
        return (Vector((-1.25, -1.1, F2 + 0.35)).lerp(Vector((-1.25, -1.0, F2 + 0.5)), e), Vector((HATCH[0], HATCH[1], C2)), 20, (0, 1, 0))
    return cam, anim


@move("closet_crack", "night", 4.5, cast=("y:thin",), rooms=("upstairs", "attic"))
def _():
    def anim(c, t):
        sec = t * DUR["closet_crack"]
        c["closet_door"].rotation_euler = (0, 0, math.radians(-50) * ease(min(1.0, max(0.0, (sec - 0.6) / 1.6))))
        h = P(c, "y"); u = min(1.0, max(0.0, (sec - 1.8) / 2.7))
        H.walk_to(h, (-1.25, -1.0, F2), (-0.9, -2.6, F2), u * 0.8, swing=5, stride=0.7, floor=F2)
        H.rotl(h, "spine03", (1, 0, 0), 15)
    def cam(c, t):
        e = ease(t)
        return (Vector((-3.6, -4.2, F2 + 1.3)).lerp(Vector((-3.5, -4.0, F2 + 1.25)), e), Vector((-1.2, -1.4, F2 + 1.0)), 26)
    return cam, anim


@move("kitchen_cross", "night", 4.5, cast=("y:thin",), rooms=("kitchen",))
def _():
    def anim(c, t):
        h = P(c, "y")
        H.walk_to(h, (-0.6, -0.1, 0), (-0.6, 3.6, 0), t * 0.9, swing=5, stride=0.8)
        H.rotl(h, "spine03", (1, 0, 0), 12)
    def cam(c, t):
        e = ease(t)
        return (Vector((3.5, 0.6, 1.5)).lerp(Vector((3.3, 1.0, 1.45)), e), Vector((-0.6, 2.6, 0.9)), 26)
    return cam, anim


def _icebox_scene(c, sec):
    c["ice_door"].rotation_euler = (0, 0, math.radians(-100))
    if "iceglow" not in c:
        c["iceglow"] = H.point((-0.85, 4.05, 0.55), 6, (0.8, 0.9, 1.0), 0.15)
        c["roast"] = cyl("Roast", (0, 0, 0), 0.09, 0.08, pbr("Roast", (0.28, 0.12, 0.05), 0.6), 20)
    h = P(c, "y")
    reset_pose(h); pose_sit(h, lean=35)
    h.arm.rotation_euler = (0, 0, math.radians(180)); h.arm.location = (-0.85, 3.35, 0); bpy.context.view_layer.update(); H.ground_to(h, 0.0)
    hd = h.bone_head("head"); tear = 0.04 * math.sin(2 * math.pi * 1.3 * sec)
    r = hd + Vector((0.0, 0.25, -0.25 + tear)); c["roast"].location = r
    reach(h, "R", r + Vector((-0.08, -0.02, 0)), Vector((0, 0, -1)), Vector((1, 1, 0))); reach(h, "L", r + Vector((0.08, -0.02, 0)), Vector((0, 0, -1)), Vector((-1, 1, 0)))
    H.rotl(h, "head", (1, 0, 0), 20)


@move("icebox_crouch", "night", 4.5, cast=("y:thin",), rooms=("kitchen",))
def _():
    def anim(c, t):
        _icebox_scene(c, t * DUR["icebox_crouch"])
    def cam(c, t):
        e = ease(t)
        return (Vector((1.4, 1.6, 1.4)).lerp(Vector((1.1, 1.9, 1.35)), e), Vector((-0.8, 3.6, 0.7)), 32)
    return cam, anim


@move("philip_doorway", "night", 4.5, cast=("p:philip", "y:thin"), rooms=("kitchen", "front", "bedroom"))
def _():
    def anim(c, t):
        sec = t * DUR["philip_doorway"]
        _icebox_scene(c, sec)
        p = P(c, "p"); u = min(1.0, sec / 1.4)
        H.walk_to(p, (-0.25, -1.6, 0), (-0.25, -0.35, 0), u, swing=6, stride=0.8)
        if sec > 1.4:
            reach(p, "R", Vector((-0.02, -0.2, 1.3)), Vector((1, 0, -1)), Vector((1, 0, 0)))
        H.look(p, 15, 10)
    def cam(c, t):
        e = ease(t)
        return (Vector((0.6, 3.2, 1.3)).lerp(Vector((0.4, 3.0, 1.35)), e), Vector((-0.25, -0.4, 1.3)), 34)
    return cam, anim


@move("walk_kitchen", "day", 5.0, cast=("y:thin", "d1:detective", "d2:detective2"), rooms=("kitchen", "front", "bedroom"))
def _():
    def anim(c, t):
        sec = t * DUR["walk_kitchen"]
        y, d1, d2 = P(c, "y"), P(c, "d1"), P(c, "d2")
        H.walk_to(y, (0.5, 3.0, 0), (-0.1, 0.4, 0), t * 0.8, swing=0, stride=0.8)
        for sd in ("L", "R"):
            reach(y, sd, y.bone_head("spine01") + y.arm.matrix_world.to_3x3() @ Vector((0.04 * (1 if sd == "L" else -1), -0.22, 0.0)), Vector((0, 0, -1)), Vector((0, -1, 0)))
        if sec > 2.6:
            reach(y, "R", y.bone_head("head") + Vector((-0.4, -0.5, -0.1)), Vector((0, 0, -1)), Vector((-0.5, -1, 0)))
        H.walk_to(d1, (1.3, 3.6, 0), (0.7, 1.0, 0), t * 0.8, swing=8, stride=0.8)
        H.walk_to(d2, (2.3, 3.4, 0), (1.6, 1.4, 0), t * 0.7, swing=8, stride=0.8)
    def cam(c, t):
        e = ease(t)
        return (Vector((2.4, -0.1, 1.6)).lerp(Vector((2.1, 0.1, 1.6)), e), Vector((0.6, 2.4, 1.1)).lerp(Vector((0.2, 1.0, 1.2)), e), 26)
    return cam, anim


@move("walk_track", "day", 5.0, cast=("y:thin", "d1:detective", "d2:detective2"), rooms=("kitchen", "front", "bedroom"))
def _():
    def anim(c, t):
        y, d1, d2 = P(c, "y"), P(c, "d1"), P(c, "d2")
        c["bed_door"].rotation_euler = (0, 0, math.radians(-80))
        path = lambda u: (Vector((-0.25, -0.3, 0)).lerp(Vector((-0.25, -1.2, 0)), u))
        H.walk_to(y, (-0.25, -0.4, 0), (-0.3, -1.25, 0), t, swing=0, stride=0.8)
        if t > 0.7:
            y.arm.rotation_euler.z = math.radians(90)
        H.walk_to(d1, (-0.1, 0.6, 0), (-0.05, -0.6, 0), t, swing=8, stride=0.8)
        H.walk_to(d2, (0.4, 1.4, 0), (0.35, 0.1, 0), t, swing=8, stride=0.8)
    def cam(c, t):
        e = ease(t)
        return (Vector((0.6, 1.6, 1.6)).lerp(Vector((0.5, 0.3, 1.6)), e), Vector((-0.3, -1.2, 1.2)).lerp(Vector((-1.4, -1.8, 1.1)), e), 26)
    return cam, anim


@move("doorway_stop", "day", 4.5, cast=("y:thin", "d1:detective", "d2:detective2"), rooms=("bedroom", "front", "kitchen"))
def _():
    def anim(c, t):
        sec = t * DUR["doorway_stop"]
        c["bed_door"].rotation_euler = (0, 0, math.radians(-80))
        y, d1, d2 = P(c, "y"), P(c, "d1"), P(c, "d2")
        H.stand_at(y, (-0.5, -1.2, 0), math.radians(90))
        H.rotl(y, "head", (1, 0, 0), 30 * ease(min(1.0, max(0.0, (sec - 1.0) / 1.5))))
        H.stand_at(d1, (0.25, -0.7, 0), math.radians(120)); H.stand_at(d2, (0.3, -1.7, 0), math.radians(60))
        H.look(d1, 0, 5); H.look(d2, 0, 5)
    def cam(c, t):
        e = ease(t)
        return (Vector((-2.4, -2.7, 1.6)).lerp(Vector((-2.2, -2.5, 1.6)), e), Vector((-0.3, -1.2, 1.4)), 30)
    return cam, anim


@move("door_closing", "dusk", 5.0, rooms=("bedroom", "front", "kitchen"))
def _():
    def anim(c, t):
        sec = t * DUR["door_closing"]
        if "fallen" not in c:
            ch = c["bed_chair"]; ch.location = (-2.3, -2.6, 0.22); ch.rotation_euler = (math.radians(90), 0, math.radians(70)); c["fallen"] = True
            c["bulb_light"] = H.point((-2.4, -2.4, C1 - 0.6), 14, (1.0, 0.7, 0.42), 0.03)
        a = math.radians(8) * math.cos(1.9 * sec)
        piv = Vector((-2.4, -2.4, C1)); off = Vector((0.0, math.sin(a), -math.cos(a))) * 0.6
        c["bulb_light"].location = piv + off; c["bed_bulb_obj"].location = piv + off + Vector((0, 0, 0.12)); c["bed_bulb_obj"].rotation_euler = (a, 0, 0)
        c["bed_door"].rotation_euler = (0, 0, math.radians(-80) * (1 - ease(min(1.0, sec / 4.6))))
    def cam(c, t):
        e = ease(t)
        return (Vector((-3.9, -4.4, 1.9)).lerp(Vector((-3.8, -4.2, 1.8)), e), Vector((-1.2, -1.4, 1.0)), 24)
    return cam, anim


@move("hatch_shut", "night", 4.0, rooms=("upstairs", "attic"), dof=4.0)
def _():
    def anim(c, t):
        sec = t * DUR["hatch_shut"]
        c["closet_door"].rotation_euler = (0, 0, math.radians(-105)); c["closet_light"].data.energy = 3
        c["hatch"].location = c["hatch_home"] + Vector((0.32 * (1 - ease(min(1.0, max(0.0, (sec - 0.5) / 2.0)))), 0, 0.02))
        if "dust" not in c:
            c["dust"] = H.leaf_cloud(25, HATCH, (0.12, 0.2), C2 - 0.05, col=(0.75, 0.7, 0.6), seed=6)
            for o in c["dust"]:
                o.scale = (0.012, 0.012, 1)
        H.fall_leaves(c["dust"], sec * 0.25, ground=F2, drift=(0.0, 0.0))
    def cam(c, t):
        e = ease(t)
        return (Vector((-1.25, -1.1, F2 + 0.4)).lerp(Vector((-1.25, -1.05, F2 + 0.5)), e), Vector((HATCH[0], HATCH[1], C2)), 22, (0, 1, 0))
    return cam, anim


@move("search_below", "day", 5.0, cast=("d1:detective", "d2:detective2"), rooms=("upstairs", "attic"))
def _():
    def anim(c, t):
        sec = t * DUR["search_below"]
        c["closet_door"].rotation_euler = (0, 0, math.radians(-105))
        d1, d2 = P(c, "d1"), P(c, "d2")
        H.walk_to(d1, (-3.6, -1.5, F2), (-2.6, -1.2, F2), t * 0.6, swing=6, stride=0.8, floor=F2)
        H.stand_at(d2, (-1.3, -2.0, F2), math.radians(180), z=F2); H.rotl(d2, "spine03", (1, 0, 0), 25)
    def cam(c, t):
        e = ease(t)
        tgt = Vector((-2.0, -1.8, F2 + 1.0)).lerp(Vector((-1.2, -0.75, C2 - 0.05)), e)
        return (Vector((-3.7, -4.3, F2 + 1.4)).lerp(Vector((-3.4, -3.9, F2 + 1.3)), e), tgt, 26)
    return cam, anim


@move("dust_sheets", "day", 5.0, cast=("s:son",), rooms=("front", "kitchen"))
def _():
    def anim(c, t):
        sec = t * DUR["dust_sheets"]
        if "sheets" not in c:
            sh = fabric("DustSheet", (0.86, 0.84, 0.78), 0.9, 0.5, 400)
            c["sheets"] = []
            for (x, y, sx, sy, sz) in ((3.2, -2.0, 1.0, 1.0, 1.1), (4.0, -3.0, 0.6, 0.6, 1.2)):
                bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1, location=(x, y, 0))
                o = bpy.context.active_object; o.scale = (sx / 1.6, sy / 1.6, sz); o.data.materials.append(sh); c["sheets"].append(o)
            c["armchair"].location = (3.2, -2.0, 0)
            c["flying"] = box("FlyingSheet", (0, 0, 0), (1.6, 1.4, 0.01), sh)
            c["flying"].modifiers.new("w", 'WAVE').height = 0.06
        h = P(c, "s"); H.stand_at(h, (2.2, -1.4, 0), math.radians(-130))
        u = ease(min(1.0, sec / 3.0))
        c["flying"].location = Vector((2.6, -1.7, 1.4)).lerp(Vector((3.2, -2.0, 1.15)), u); c["flying"].rotation_euler = (math.radians(20) * (1 - u), 0, math.radians(-40))
        c["flying"].scale = (1.0, 1.0, 1.0)
        for sd in ("L", "R"):
            reach(h, sd, c["flying"].location + Vector((-0.6, 0.35 * (1 if sd == "L" else -1), 0.0)), Vector((0, 0, -1)), Vector((1, -1, -0.5)))
    def cam(c, t):
        e = ease(t)
        return (Vector((1.0, -0.6, 1.6)).lerp(Vector((1.3, -0.8, 1.55)), e), Vector((3.0, -2.2, 0.9)), 28)
    return cam, anim


@move("jar_track", "night", 5.0, rooms=("kitchen", "cellar"))
def _():
    def anim(c, t):
        c["cellar_light"].data.energy = 30
    def cam(c, t):
        e = ease(t); gp = c["gap"]
        return (Vector((-1.9, 3.3, gp.z + 0.1)).lerp(Vector((gp.x - 0.1, 3.45, gp.z + 0.12)), e), Vector((-1.2, 4.33, gp.z)).lerp(gp, e), 32)
    return cam, anim


@move("candle_steps", "night", 5.0, cast=("y:thin",), rooms=("kitchen", "cellar"))
def _():
    def anim(c, t):
        sec = t * DUR["candle_steps"]
        c["cellar_light"].data.energy = 0
        h = P(c, "y")
        u = min(1.0, sec / 3.0)
        p0 = Vector((-3.5, 0.6, -0.35)); p1 = Vector((-3.5, 3.0, -2.65))
        pos = p0.lerp(p1, u)
        H.walk_to(h, p0, p1, u, swing=3, stride=0.7, floor=pos.z)
        if sec > 3.0:
            H.walk_to(h, p1, Vector((c["gap"].x, 3.9, -2.65)), min(1.0, (sec - 3.0) / 2.0), swing=3, stride=0.7, floor=-2.65)
        if "candle" not in c:
            c["candle"] = H.point((0, 0, 0), 4, (1.0, 0.6, 0.25), 0.02)
            c["candlestick"] = cyl("Candle", (0, 0, 0), 0.012, 0.12, pbr("Wax", (0.9, 0.86, 0.75), 0.5), 12)
        w = h.bone_tail("wrist.R"); c["candlestick"].location = w + Vector((0, 0, 0.06)); c["candle"].location = w + Vector((0, 0, 0.16))
        c["candle"].data.energy = 4 + 0.8 * math.sin(17 * sec) * math.sin(5 * sec)
    def cam(c, t):
        e = ease(t)
        return (Vector((1.6, 2.2, -1.2)).lerp(Vector((1.2, 2.5, -1.3)), e), Vector((-3.0, 2.0, -1.8)).lerp(Vector((-1.5, 3.6, -1.6)), e), 26)
    return cam, anim
