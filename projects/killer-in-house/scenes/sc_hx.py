"""THE HOUSE, exterior. Variant = (season_tod, cast). Every move: the trees sway, leaves/snow fall, the camera drifts.
  intro (summer 1942 night): street_push, van_away, curtain, window_glow, patrol, officers_leave
  ch1 (autumn 1941 / winter):  title_crane, rake, cross_street, porch_knock, friend_leaves, helen_car,
                               winter_flicker, winter_sweep, search_windows, sedan_watch
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
import house as H
from house import reset_pose
from house import G, D2, ROAD_Y, F2, C1
from human import fingers_curl, reach

DUR = {}
VARIANT_FOR = {}
MOVES = {}
WALK_Y = ROAD_Y + 5.0          # near sidewalk (house side)


def move(name, variant, dur, cast=(), dof=None, title=None, extra=()):
    def deco(fn):
        cam, anim = fn()
        DUR[name] = dur; VARIANT_FOR[name] = (variant, tuple(cast), tuple(extra), name)
        MOVES[name] = dict(kind="anim", dof=dof, far=60, cam=cam, anim=anim, **({"title": title} if title else {}))
        return fn
    return deco


def build(variant=None):
    vv, cast, extra, name = variant or ("autumn_day", (), (), "")
    season, tod = vv.split("_")
    c = H.build_house(season, tod, rooms=("kitchen", "front", "bedroom", "upstairs"))
    c["tod"] = tod
    if season == "autumn":
        c["leaves"] = H.leaf_cloud(70, (0.0, -10.0), (12, 7), 9.0)
    if season == "winter":
        c["snowfall"] = H.leaf_cloud(160, (0.0, -10.0), (14, 8), 9.0, col=(0.9, 0.92, 0.96), seed=4)
        for o in c["snowfall"]:
            o.scale = (0.12, 0.2, 1)
    if tod == "night":            # the house is dark (empty, or Philip is dead inside)
        for k in ("up_light", "k_light", "lamp", "bed_lamp"):
            c[k].data.energy = 0.0
    H.porch_lamp(c)
    c["cast"] = {}
    for k in cast:
        key, kind = k.split(":")
        c["cast"][key] = H.person(kind.capitalize() + key, kind)
    for e in extra:
        if ":car:" in e:
            nm, _, colr, kind = e.split(":")
            col = {"black": (0.03, 0.03, 0.033), "green": (0.03, 0.06, 0.04), "maroon": (0.12, 0.02, 0.02), "grey": (0.12, 0.12, 0.12)}[colr]
            c[nm] = H.vehicle(nm, col, kind)
    c["variant"] = vv
    return c


def P(c, k):
    return c["cast"][k]


def tick(c, t, name):
    sec = t * DUR[name]
    H.sway_trees(c, sec)
    if "leaves" in c:
        H.fall_leaves(c["leaves"], sec)
    if "snowfall" in c:
        H.fall_leaves(c["snowfall"], sec * 0.6, drift=(0.15, 0.05))
    H.porch_lamp(c, math.radians(2.5) * math.sin(1.4 * sec))
    return sec


def carry(h, obj, side="R", off=(0, 0, -0.18)):
    w = h.bone_tail(f"wrist.{side}")
    obj.location = w + Vector(off); obj.rotation_euler = (0, 0, h.arm.rotation_euler.z + math.pi / 2)


# =========================================================================== INTRO (summer 1942, night)
@move("street_push", "summer_night", 5.0)
def _():
    def anim(c, t):
        tick(c, t, "street_push")
    def cam(c, t):
        e = ease(t)
        return (Vector((-10.0, ROAD_Y - 2.5, 1.7)).lerp(Vector((-5.5, ROAD_Y + 0.5, 1.6)), e), Vector((-0.5, -D2, 2.6)).lerp(Vector((0.2, -D2, 2.8)), e), 30)
    return cam, anim


@move("van_away", "summer_night", 4.0, extra=("van:car:maroon:sedan",))
def _():
    def anim(c, t):
        sec = tick(c, t, "van_away")
        H.drive(c["van"], (-1.0, ROAD_Y + 1.8, G - 0.05), (-30.0, ROAD_Y + 1.8, G - 0.05), ease(t) * 0.55 + 0.05 * t, heading=math.pi)
        H.porch_swing(c, math.radians(6) * math.sin(1.5 * sec))
    def cam(c, t):
        e = ease(t)
        return (Vector((3.1, -D2 - 0.6, 1.5)).lerp(Vector((2.9, -D2 - 0.9, 1.5)), e), Vector((-9.0, ROAD_Y + 1.5, 0.4)), 30)
    return cam, anim


@move("curtain", "summer_night", 4.0, cast=("w:neighbour_w",))
def _():
    def anim(c, t):
        sec = tick(c, t, "curtain")
        if "nwin" not in c:
            # a window in the neighbour's front room across the street (seen from inside, behind her)
            c["neighbours"][2].hide_render = True
            y = ROAD_Y - 8.0; pl = H.mat("plaster")
            pl = H.mat("paper")
            H.wall_x("NWin", -9.5, -3.5, y, G, G + 2.8, 0.2, pl, [(-7.2, -5.8, G + 0.9, G + 2.3)])
            H.wall_y("NSide", y - 4.0, y, -9.5, G, G + 2.8, 0.2, pl); box("NCeil", (-6.5, y - 2.0, G + 2.85), (6, 4, 0.1), H.mat("plaster"))
            import ph
            ph.model("ArmChair_01", loc=(-8.6, y - 1.0, G), rot_z=math.radians(140))
            ph.model("side_table_01", loc=(-8.9, y - 0.4, G)); ph.model("vintage_oil_lamp", loc=(-8.9, y - 0.4, G + 0.55), scale=0.8)
            H.point((-8.9, y - 0.4, G + 1.1), 20, (1.0, 0.68, 0.38), 0.06)
            p, g = H.window_unit('x', -6.5, 1.4, y + 0.0, G + 0.9, G + 2.3, lit_glass=None); c["nwin"] = p
            cl = box("NCurtainL", (-6.95, y - 0.15, G + 1.6), (0.5, 0.02, 1.4), H.mat("lace")); c["ncur"] = cl
            box("NCurtainR", (-6.05, y - 0.15, G + 1.6), (0.5, 0.02, 1.4), H.mat("lace"))
            box("NFloor", (-6.5, y - 2.0, G - 0.01), (5, 4, 0.02), H.mat("floor"))
            l = H.point((-6.0, y - 3.0, G + 2.4), 6, (1.0, 0.7, 0.42), 0.2)
        h = P(c, "w"); y = ROAD_Y - 8.0
        H.stand_at(h, (-6.6, y - 0.75, G), math.pi)
        u = ease(min(1.0, sec / 1.6))
        c["ncur"].location.x = -6.95 - 0.35 * u; c["ncur"].scale.x = 1.0 - 0.4 * u
        reach(h, "R", Vector((-6.95 - 0.3 * u + 0.2, y - 0.25, G + 1.45)), Vector((0.3, 0.4, -1)), Vector((0, 1, 0)))
        H.look(h, 6, -4)
    def cam(c, t):
        e = ease(t); y = ROAD_Y - 8.0
        return (Vector((-8.2, y - 3.6, G + 1.6)).lerp(Vector((-7.9, y - 3.2, G + 1.6)), e), Vector((-5.0, -D2, 2.0)), 28)
    return cam, anim


@move("window_glow", "summer_night", 5.0)
def _():
    def anim(c, t):
        sec = tick(c, t, "window_glow")
        k = max(0.0, min(1.0, (sec - 0.8) / 0.6)) * max(0.0, min(1.0, (3.8 - sec) / 0.25))
        c["up_light"].data.energy = 160 * k
    def cam(c, t):
        e = ease(t)
        return (Vector((-4.0, ROAD_Y - 2.5, 1.3)).lerp(Vector((-3.2, ROAD_Y + 1.0, 1.4)), e), Vector((-2.4, -D2, 3.9)), 42)
    return cam, anim


@move("patrol", "summer_night", 4.0, cast=("o1:officer", "o2:officer"), extra=("pcar:car:black:police",))
def _():
    def anim(c, t):
        sec = tick(c, t, "patrol")
        H.drive(c["pcar"], (-14.0, ROAD_Y + 2.1, G - 0.05), (-1.5, ROAD_Y + 2.1, G - 0.05), ease(min(1.0, t * 1.6)))
        if "beams" not in c:
            c["beams"] = [H.flashlight("T1"), H.flashlight("T2")]
        for k, key in enumerate(("o1", "o2")):
            h = P(c, key)
            u = max(0.0, (t - 0.35 - 0.06 * k) / 0.65)
            p = H.walk_to(h, (0.15 + 0.45 * (k - 0.5), WALK_Y + 0.4, G), (0.15 + 0.4 * (k - 0.5), -D2 - 3.4, G), u * 0.75, swing=8)
            hd = h.bone_head("head")
            tgt = Vector((0.2, -D2, 1.2 + 0.6 * math.sin(sec + k)))
            H.aim_obj(c["beams"][k], hd + Vector((0.2, 0.25, -0.45)), tgt)
            reach(h, "R", hd + Vector((0.2, 0.3, -0.45)), Vector((0.3, -0.5, -1)), (tgt - hd).normalized())
    def cam(c, t):
        e = ease(t)
        return (Vector((6.5, ROAD_Y - 2.5, 1.5)).lerp(Vector((5.6, ROAD_Y - 1.5, 1.6)), e), Vector((-2.0, -D2 - 6.0, 0.4)), 26)
    return cam, anim


@move("officers_leave", "summer_night", 4.5, cast=("o1:officer", "o2:officer"))
def _():
    def anim(c, t):
        sec = tick(c, t, "officers_leave")
        H.porch_lamp(c, math.radians(5) * math.sin(1.5 * sec) * (0.5 + 0.5 * min(1, sec / 2)))
        o1, o2 = P(c, "o1"), P(c, "o2")
        H.walk_to(o1, (-0.2, -D2 - 0.5, -0.06), (-0.4, -D2 - 2.6, G + 0.5), min(1.0, t * 1.3), swing=10)
        u = min(1.0, t * 1.4)
        H.walk_to(o2, (0.45, -D2 + 0.1, 0.0), (0.4, -D2 - 0.7, -0.06), min(1.0, u * 1.4), swing=8)
        dz = math.radians(-95) * (1 - ease(min(1.0, max(0.0, (sec - 1.2) / 1.6))))
        c["front_door"].rotation_euler = (0, 0, dz)
        if sec > 1.0:
            reach(o2, "L", Vector((0.5, -D2 - 0.05, 0.95)), Vector((-0.5, 0, -1)), Vector((0, 1, 0)))
    def cam(c, t):
        e = ease(t)
        return (Vector((4.5, -D2 - 7.5, 1.2)).lerp(Vector((3.8, -D2 - 7.0, 1.25)), e), Vector((0.1, -D2 - 1.0, 1.3)), 30)
    return cam, anim


# =========================================================================== CH1 (autumn 1941)
@move("title_crane", "autumn_day", 6.0, title=("CHAPTER 1", "The House on Moncrieff Place", 12, 132))
def _():
    def anim(c, t):
        tick(c, t, "title_crane")
    def cam(c, t):
        e = ease(t)
        return (Vector((3.0, ROAD_Y - 2.0, 7.0)).lerp(Vector((2.6, ROAD_Y + 0.5, 1.4)), e), Vector((0.5, -D2, 4.5)).lerp(Vector((0.0, -D2, 2.8)), e), 30)
    return cam, anim


@move("rake", "autumn_day", 5.0, cast=("p:philip",))
def _():
    def anim(c, t):
        sec = tick(c, t, "rake")
        h = P(c, "p")
        if "rake" not in c:
            c["rake"] = join([cyl("RakeHandle", (0, 0, 0.75), 0.014, 1.5, H.mat("oak"), 10),
                              box("RakeHead", (0, 0, 0.0), (0.45, 0.04, 0.03), H.mat("iron"))], "Rake")
            c["pile"] = []
            lm = H.mat("leafground")
            bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1, location=(-2.2, -D2 - 4.0, G))
            pile = bpy.context.active_object; pile.scale = (0.7, 0.5, 0.22); pile.data.materials.append(lm)
        stroke = math.sin(2 * math.pi * 0.55 * sec)
        H.stand_at(h, (-3.2, -D2 - 4.3, G), math.radians(-70))
        H.rotl(h, "spine03", (1, 0, 0), 12 + 4 * stroke); H.rotl(h, "head", (1, 0, 0), 14)
        M = h.arm.matrix_world.to_3x3(); fwd = (M @ Vector((0, -1, 0))).normalized(); left = (M @ Vector((1, 0, 0))).normalized()
        ch = h.bone_head("spine05")
        head_pt = ch + fwd * (0.95 + 0.35 * stroke) + Vector((0, 0, -ch.z + G + 0.02))
        top = ch + fwd * 0.12 + Vector((0, 0, -0.25)) - left * 0.1
        r = c["rake"]; d = (top - head_pt).normalized()
        r.location = head_pt; r.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        reach(h, "R", head_pt + d * 1.05, -left - Vector((0, 0, 1)), d)
        reach(h, "L", head_pt + d * 0.7 + left * 0.03, left - Vector((0, 0, 1)), d)
        fingers_curl(h, 60)
    def cam(c, t):
        e = ease(t)
        return (Vector((-6.5, -D2 - 7.5, 1.0)).lerp(Vector((-5.6, -D2 - 7.0, 1.1)), e), Vector((-2.8, -D2 - 4.0, 0.3)), 34)
    return cam, anim


@move("cross_street", "autumn_night", 4.5, cast=("m:neighbour_m", "w:neighbour_w"))
def _():
    def anim(c, t):
        tick(c, t, "cross_street")
        for k, key in enumerate(("m", "w")):
            H.walk_to(P(c, key), (-7.0 + 0.6 * k, ROAD_Y - 5.0 - 0.3 * k, G), (0.0 + 0.6 * k, -D2 - 4.0 - 0.3 * k, G), 0.1 + 0.7 * t, swing=12)
    def cam(c, t):
        e = ease(t)
        return (Vector((-12.0, ROAD_Y - 7.5, 1.6)).lerp(Vector((-11.0, ROAD_Y - 6.5, 1.65)), e), Vector((-1.0, -D2, 1.8)), 28)
    return cam, anim


@move("porch_knock", "autumn_night", 4.5, cast=("m:neighbour_m", "w:neighbour_w"))
def _():
    def anim(c, t):
        sec = tick(c, t, "porch_knock")
        m, w = P(c, "m"), P(c, "w")
        H.stand_at(m, (0.15, -D2 - 0.55, -0.06), 0.0 + math.pi)
        H.stand_at(w, (-0.6, -D2 - 2.3, G + 0.36), math.pi + math.radians(15))
        knock = max(0.0, math.sin(2 * math.pi * 2.2 * sec)) if sec < 1.6 else 0.0
        if sec < 2.0:
            reach(m, "R", Vector((0.2, -D2 - 0.12 - 0.05 * knock, 1.45)), Vector((0.5, 0, -1)), Vector((0, 1, 0)))
        else:
            reach(m, "R", Vector((0.55, -D2 - 0.1, 0.95)), Vector((0.5, 0, -1)), Vector((0, 1, 0)))
            c["front_door"].rotation_euler = (0, 0, math.radians(-25) * ease(min(1.0, (sec - 2.8) / 1.2)) if sec > 2.8 else 0.0)
        H.look(w, 10, 4)
    def cam(c, t):
        e = ease(t)
        return (Vector((-2.4, -D2 - 4.6, 1.3)).lerp(Vector((-2.0, -D2 - 4.0, 1.35)), e), Vector((0.1, -D2 - 0.5, 1.3)), 32)
    return cam, anim


@move("friend_leaves", "autumn_day", 4.5, cast=("f:friend",))
def _():
    def anim(c, t):
        tick(c, t, "friend_leaves")
        if "case" not in c:
            import ph
            r, ms = ph.model("vintage_suitcase", scale=0.8); c["case"] = r
            for o in ms:
                if "02" in o.name:
                    o.hide_render = True
        h = P(c, "f")
        z = -0.06 if t < 0.25 else (G if t > 0.55 else -0.06 + (G + 0.06) * (t - 0.25) / 0.3)
        H.walk_to(h, (0.15, -D2 - 0.6, z), (0.6, -D2 - 7.5, z), t * 0.85, swing=12, floor=z)
        carry(h, c["case"], "R", (0.0, 0.0, -0.12))
        c["front_door"].rotation_euler = (0, 0, math.radians(-70))
    def cam(c, t):
        e = ease(t)
        return (Vector((3.8, -D2 - 8.5, 1.2)).lerp(Vector((3.2, -D2 - 8.8, 1.1)), e), Vector((0.3, -D2 - 3.0, 0.8)).lerp(Vector((0.5, -D2 - 5.5, 0.4)), e), 30)
    return cam, anim


@move("helen_car", "autumn_day", 5.0, cast=("hl:helen", "s:son"), extra=("scar:car:green:sedan",))
def _():
    def anim(c, t):
        sec = tick(c, t, "helen_car")
        u = max(0.0, (sec - 2.2) / 2.8)
        H.drive(c["scar"], (1.5, ROAD_Y + 2.1, G - 0.05), (25.0, ROAD_Y + 2.1, G - 0.05), u * u)
        hl, s = P(c, "hl"), P(c, "s")
        if sec < 2.2:
            H.walk_to(hl, (0.6, WALK_Y + 0.6, G), (0.9, ROAD_Y + 3.3, G), min(1.0, sec / 2.2) * 0.8, swing=4, stride=0.7)
            H.stand_at(s, (1.9, ROAD_Y + 3.4, G), math.radians(200))
            reach(s, "R", hl.bone_head("upperarm01.L") + Vector((0.1, 0, -0.2)), Vector((0, 0.5, -1)), Vector((-1, 0, 0)))
        else:
            for h in (hl, s):
                h.arm.location.z = -50
    def cam(c, t):
        e = ease(t)
        return (Vector((-4.5, WALK_Y + 3.0, 1.4)).lerp(Vector((-4.0, WALK_Y + 2.6, 1.4)), e), Vector((2.0, ROAD_Y + 2.0, 0.6)).lerp(Vector((6.0, ROAD_Y + 2.0, 0.6)), e), 32)
    return cam, anim


@move("winter_flicker", "winter_day", 5.0)
def _():
    def anim(c, t):
        sec = tick(c, t, "winter_flicker")
        f = 0.5 + 0.5 * math.sin(23 * sec) * math.sin(7.1 * sec)
        on = 1.0 if 1.2 < sec < 3.6 else 0.0
        c["up_light"].data.energy = 160 * on * (0.4 + 0.6 * f)
    def cam(c, t):
        e = ease(t)
        return (Vector((-6.0, ROAD_Y - 1.0, 1.7)).lerp(Vector((-4.6, ROAD_Y + 2.0, 1.8)), e), Vector((-1.5, -D2, 3.4)), 34)
    return cam, anim


@move("winter_sweep", "winter_day", 5.0, cast=("w:neighbour_w",))
def _():
    def anim(c, t):
        sec = tick(c, t, "winter_sweep")
        h = P(c, "w")
        if "broom" not in c:
            c["broom"] = join([cyl("BroomStick", (0, 0, 0.6), 0.013, 1.2, H.mat("oak"), 10),
                               box("BroomHead", (0, 0, 0.0), (0.3, 0.06, 0.18), pbr("Straw", (0.6, 0.48, 0.25), 0.9))], "Broom")
        stop = ease(min(1.0, max(0.0, (sec - 2.2) / 0.8)))
        stroke = math.sin(2 * math.pi * 0.9 * sec) * (1 - stop)
        H.stand_at(h, (13.0, WALK_Y - 0.2, G), math.radians(-120) + stop * math.radians(-55))
        M = h.arm.matrix_world.to_3x3(); fwd = (M @ Vector((0, -1, 0))).normalized(); left = (M @ Vector((1, 0, 0))).normalized()
        ch = h.bone_head("spine05")
        foot = ch + fwd * (0.55 + 0.2 * stroke) - left * 0.2 + Vector((0, 0, -ch.z + G + 0.1))
        top = ch + fwd * 0.15 - left * 0.15 + Vector((0, 0, -0.2))
        d = (top - foot).normalized(); b = c["broom"]; b.location = foot; b.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        reach(h, "R", foot + d * 1.0, -left - Vector((0, 0, 1)), d); reach(h, "L", foot + d * 0.65, left - Vector((0, 0, 1)), d)
        H.rotl(h, "head", (0, 0, 1), -25 * stop); H.rotl(h, "head", (1, 0, 0), 6 - 10 * stop)
    def cam(c, t):
        e = ease(t)
        return (Vector((16.5, WALK_Y + 1.6, 1.6)).lerp(Vector((16.0, WALK_Y + 1.2, 1.6)), e), Vector((12.0, WALK_Y - 0.6, 1.2)).lerp(Vector((5.0, -D2, 2.0)), ease(max(0.0, (t - 0.45) / 0.55))), 34)
    return cam, anim


@move("search_windows", "winter_night", 5.0)
def _():
    def anim(c, t):
        sec = tick(c, t, "search_windows")
        if "beams" not in c:
            c["beams"] = [H.flashlight("T1"), H.flashlight("T2")]
            for b in c["beams"]:
                b.data.energy = 120
        # two beams inside: ground floor front room, then upstairs bedroom
        p1 = Vector((1.2 + 2.0 * t, -2.0, 1.5)); H.aim_obj(c["beams"][0], p1, Vector((3.0 + 1.2 * math.sin(1.6 * sec), -D2, 1.2)))
        p2 = Vector((-1.4 - 1.6 * t, -1.6, F2 + 1.5)); H.aim_obj(c["beams"][1], p2, Vector((-2.4 + 1.0 * math.sin(1.2 * sec + 1), -D2, F2 + 1.0)))
    def cam(c, t):
        e = ease(t)
        return (Vector((5.0, ROAD_Y - 1.0, 1.6)).lerp(Vector((3.5, ROAD_Y + 1.2, 1.6)), e), Vector((0.0, -D2, 2.6)), 30)
    return cam, anim


def _sedan_cast(c, t, sec, smoke=True):
    car = c["dcar"]; H.drive(car, (-6.0, ROAD_Y - 2.1, G - 0.05), (-6.0 + 0.001, ROAD_Y - 2.1, G - 0.05), 0.0, heading=0.0)
    for k, key in enumerate(("d1", "d2")):
        h = P(c, key)
        reset_pose(h); from human import pose_sit; pose_sit(h, lean=4)
        h.arm.rotation_euler = (0, 0, math.radians(90))
        h.arm.location = (-6.2, ROAD_Y - 2.1 + (0.42 if k == 0 else -0.42), 0); bpy.context.view_layer.update()
        H.ground_to(h, G + 0.1)
        H.look(h, 25 if k == 0 else 15, 0)
    if smoke and "cig" not in c:
        c["cig"] = H.point((0, 0, 0), 0.0, (1.0, 0.35, 0.1), 0.01)
    if smoke:
        h = P(c, "d1"); puff = max(0.0, math.sin(2 * math.pi * sec / 3.0))
        hd = h.bone_head("head"); M = h.arm.matrix_world.to_3x3(); fwd = M @ Vector((0, -1, 0))
        tip = hd + fwd * (0.12 + 0.12 * (1 - puff)) + Vector((0, 0, -0.08 - 0.2 * (1 - puff)))
        reach(h, "R", tip + Vector((0, 0, -0.03)), Vector((0, -0.3, -1)), fwd)
        c["cig"].location = tip; c["cig"].data.energy = 0.2 + 0.6 * puff


@move("sedan_watch", "winter_night", 5.0, cast=("d1:detective", "d2:detective2"), extra=("dcar:car:black:sedan",))
def _():
    def anim(c, t):
        sec = tick(c, t, "sedan_watch")
        _sedan_cast(c, t, sec)
    def cam(c, t):
        e = ease(t)
        return (Vector((-8.8, ROAD_Y - 4.2, 1.5)).lerp(Vector((-8.4, ROAD_Y - 3.9, 1.5)), e), Vector((-4.0, -D2, 1.6)), 28)
    return cam, anim


# =========================================================================== CH2 (summer 1942, night)
@move("sedan_title", "summer_night", 6.0, cast=("d1:detective", "d2:detective2"), extra=("dcar:car:black:sedan",),
      title=("CHAPTER 2", "The Closet", 12, 132))
def _():
    def anim(c, t):
        sec = tick(c, t, "sedan_title")
        _sedan_cast(c, t, sec)
    def cam(c, t):
        e = ease(t)
        return (Vector((-12.5, ROAD_Y - 2.4, 1.3)).lerp(Vector((-9.6, ROAD_Y - 2.2, 1.25)), e), Vector((-3.0, -D2, 2.2)), 30)
    return cam, anim


@move("sedan_inside", "summer_night", 4.5, cast=("d1:detective", "d2:detective2"), extra=("dcar:car:black:sedan",))
def _():
    def anim(c, t):
        sec = tick(c, t, "sedan_inside")
        _sedan_cast(c, t, sec)
        lean = ease(min(1.0, max(0.0, (sec - 2.0) / 1.2)))
        h = P(c, "d1"); H.rotl(h, "spine03", (1, 0, 0), 10 * lean)
    def cam(c, t):
        e = ease(t)
        return (Vector((-6.2, ROAD_Y - 4.6, 1.0)).lerp(Vector((-6.0, ROAD_Y - 4.3, 0.98)), e), Vector((-6.2, ROAD_Y - 1.7, 0.7)), 34)
    return cam, anim


@move("thin_window", "summer_night", 4.0)
def _():
    def anim(c, t):
        sec = tick(c, t, "thin_window")
        if "shape" not in c:
            c["shape"] = H.person("Shape", "thin")
            c["shape_lamp"] = H.point((2.6, -3.0, 1.4), 0.0, (1.0, 0.68, 0.4), 0.05)
        u = min(1.0, max(0.0, (sec - 0.8) / 2.4))
        H.walk_to(c["shape"], (1.5, -3.9, 0.0), (3.7, -3.9, 0.0), u, swing=8, stride=0.9)
        c["shape_lamp"].data.energy = 25 * max(0.0, math.sin(math.pi * min(1.0, sec / 3.6)))
    def cam(c, t):
        e = ease(t)
        return (Vector((4.0, ROAD_Y - 2.0, 1.2)).lerp(Vector((3.6, ROAD_Y - 0.6, 1.2)), e), Vector((2.6, -D2, 1.5)), 46)
    return cam, anim


@move("run_across", "summer_night", 4.0, cast=("d1:detective", "d2:detective2"), extra=("dcar:car:black:sedan",))
def _():
    def anim(c, t):
        sec = tick(c, t, "run_across")
        H.drive(c["dcar"], (-6.0, ROAD_Y - 2.1, G - 0.05), (-5.999, ROAD_Y - 2.1, G - 0.05), 0.0, heading=0.0)
        for k, key in enumerate(("d1", "d2")):
            p0 = (-5.5 + 0.8 * k, ROAD_Y - 1.0, G); p1 = (0.1 + 0.6 * k, -D2 - 2.6, G)
            H.walk_to(P(c, key), p0, p1, min(1.0, t * 1.05 - 0.08 * k + 0.08), swing=26, stride=2.2)
    def cam(c, t):
        e = ease(t)
        return (Vector((6.5, ROAD_Y - 3.0, 1.4)).lerp(Vector((5.0, ROAD_Y - 1.5, 1.4)), e), Vector((-2.0, ROAD_Y + 2.0, 1.0)).lerp(Vector((0.2, -D2 - 2.5, 1.2)), e), 28)
    return cam, anim


# =========================================================================== CH3
@move("watch_leave", "summer_day", 5.0, cast=("y:thin", "p:philip"))
def _():
    def anim(c, t):
        tick(c, t, "watch_leave")
        H.stand_at(P(c, "y"), (-4.5, ROAD_Y - 5.2, G), math.radians(160))
        H.look(P(c, "y"), -10 + 20 * t, 0)
        H.walk_to(P(c, "p"), (0.6, WALK_Y, G), (12.0, WALK_Y, G), 0.1 + 0.8 * t, swing=10, stride=1.1)
    def cam(c, t):
        e = ease(t)
        return (Vector((-6.2, ROAD_Y - 7.6, 1.75)).lerp(Vector((-5.9, ROAD_Y - 7.2, 1.75)), e), Vector((2.0, WALK_Y, 1.0)).lerp(Vector((6.0, WALK_Y, 1.0)), e), 34)
    return cam, anim


@move("seasons_push", "winter_day", 5.0)
def _():
    def anim(c, t):
        tick(c, t, "seasons_push")
    def cam(c, t):
        e = ease(t)
        return (Vector((2.0, ROAD_Y - 2.5, 1.6)).lerp(Vector((1.2, ROAD_Y + 1.5, 1.7)), e), Vector((0.0, -D2, 3.0)), 32)
    return cam, anim


@move("attic_vent", "winter_night", 5.0)
def _():
    def anim(c, t):
        sec = tick(c, t, "attic_vent")
        if "vent" not in c:
            c["vent"] = H.point((H.W2 - 0.25, 0, H.RIDGE - 0.75), 0, (1.0, 0.5, 0.18), 0.1)
            # the gable vent behind the louvres is an actual opening: cut the brick gable there
            for o in bpy.data.objects:
                if o.name.startswith("HGable"):
                    m = o.modifiers.new("vent", 'BOOLEAN'); cutter = box("VentCut", (H.W2, 0, H.RIDGE - 0.75), (0.6, 0.5, 0.4)); cutter.hide_render = True; cutter.display_type = 'WIRE'
                    m.object = cutter; m.operation = 'DIFFERENCE'
            c["ventsmoke"] = H.leaf_cloud(12, (H.W2 + 0.3, 0.0), (0.2, 0.2), H.RIDGE, col=(0.6, 0.6, 0.62), seed=8)
        k = 0.6 + 0.4 * math.sin(2.3 * sec) * math.sin(0.7 * sec)
        c["vent"].data.energy = 40 * k
    def cam(c, t):
        e = ease(t)
        return (Vector((10.0, ROAD_Y + 2.0, 2.0)).lerp(Vector((9.0, ROAD_Y + 4.0, 2.4)), e), Vector((H.W2, 0, H.RIDGE - 1.2)), 40)
    return cam, anim


@move("summer_still", "summer_day", 5.0)
def _():
    def anim(c, t):
        tick(c, t, "summer_still")
    def cam(c, t):
        e = ease(t)
        return (Vector((2.0, ROAD_Y - 2.5, 1.6)).lerp(Vector((1.2, ROAD_Y + 1.5, 1.7)), e), Vector((0.0, -D2, 3.0)), 32)
    return cam, anim


@move("final_glow", "summer_night", 6.0)
def _():
    def anim(c, t):
        sec = tick(c, t, "final_glow")
        c["up_light"].data.energy = 160 * (1 - ease(min(1.0, max(0.0, (sec - 3.2) / 0.5))))
    def cam(c, t):
        e = ease(t)
        return (Vector((-1.0, ROAD_Y - 3.5, 1.4)).lerp(Vector((-1.4, ROAD_Y + 0.5, 1.5)), e), Vector((-1.0, -D2, 3.2)), 32)
    return cam, anim


@move("newsboy", "summer_day", 4.5, cast=("b:son", "c1:detective2", "c2:neighbour_m", "c3:captain"))
def _():
    def anim(c, t):
        sec = tick(c, t, "newsboy")
        if "paper" not in c:
            import sc_press
            bpy.ops.mesh.primitive_plane_add(size=1); o = bpy.context.active_object; o.scale = (0.3, 0.43, 1)
            bpy.ops.object.transform_apply(scale=True); o.data.materials.append(sc_press.paper_mat()); c["paper"] = o
            c["bundle"] = box("Bundle", (-1.6, WALK_Y + 0.3, G + 0.2), (0.45, 0.32, 0.4), pbr("Bundle", (0.82, 0.8, 0.74), 0.85))
        b = P(c, "b"); H.stand_at(b, (-1.2, WALK_Y + 0.2, G), math.radians(-160))
        wave = math.sin(2 * math.pi * 0.9 * sec)
        hand = b.bone_head("head") + Vector((0.3, -0.25, 0.05 + 0.12 * wave))
        reach(b, "R", hand, Vector((1, 0, -1)), Vector((0, 0, 1)))
        c["paper"].location = hand + Vector((0.0, -0.05, 0.22)); c["paper"].rotation_euler = (math.radians(95), 0, math.radians(20 * wave))
        for k, key in enumerate(("c1", "c2", "c3")):
            d = 1 if k % 2 else -1
            H.walk_to(P(c, key), (-8.0 * d, WALK_Y - 0.4 + 0.5 * k, G), (8.0 * d, WALK_Y - 0.4 + 0.5 * k, G), (0.15 + 0.3 * k + 0.5 * t) % 1.0, swing=12, stride=1.3)
    def cam(c, t):
        e = ease(t)
        return (Vector((2.6, WALK_Y - 4.0, 1.4)).lerp(Vector((2.0, WALK_Y - 3.6, 1.4)), e), Vector((-1.2, WALK_Y + 0.3, 1.4)), 34)
    return cam, anim
