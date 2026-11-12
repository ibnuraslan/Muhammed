"""CH3 (chat B): callbacks in chat A's outdoor sets, from new angles.
  wire (sc_path, low late sun, seen from the woods side south of the bend):
     wire   (A, TITLE "Chapter 3 / The Man with the Spade"): slow crane down as an investigator follows a low green
            wire strung between the trunks
     lookout(B): knee-height dolly along the wire to the second lookout spot; an officer there looks back down the path
  walk (sc_forest, overcast): two detectives walk an unnamed man through the spruces; he cannot find the spot.
     search (A): the three walk between the trunks; the man in front slows and looks around
     unsure (B): he points one way, turns, points another; the detectives exchange a glance
"""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import pbr, cyl
from common import ease
from human import reach, fingers_curl
import b_common as B

DUR = {"wire": 7.0, "lookout": 5.5, "search": 6.0, "unsure": 5.5}
VARIANT_FOR = {"wire": "wire", "lookout": "wire", "search": "walk", "unsure": "walk"}
EXPOSURE = 0.0
BOUNCES = 5
# the wire: from a lookout west of the bend (watching the path toward Eching) through the trees south of the path
# to a second lookout past the bend (watching toward Schondorf). Plan view, metres (sc_path coordinates).
WIRE_XY = [(-9.0, -3.6), (-6.5, -4.6), (-4.0, -5.0), (-1.5, -5.6), (0.5, -6.4), (2.4, -8.0), (4.0, -9.6), (6.0, -11.0), (8.2, -12.0)]
LOOK1 = Vector((-9.4, -3.2, 0)); LOOK2 = Vector((8.6, -12.4, 0))


def build(variant=None):
    variant = variant or "wire"
    c = {"set": variant}
    if variant == "wire":
        import sc_path as S
        c.update(S.build("lowsun|detective,officer"))
        c["S"] = S
        gz = lambda x, y: S.ground_z(c, x, y)
        rng = np.random.default_rng(140)
        pts = []
        for k in range(len(WIRE_XY) - 1):
            a = Vector(WIRE_XY[k]); b = Vector(WIRE_XY[k + 1])
            for j in range(6):
                p = a.lerp(b, j / 6) + Vector((rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15)))
                pts.append(Vector((p.x, p.y, gz(p.x, p.y) + 0.35 + 0.15 * math.sin(len(pts) * 0.7))))
        pts.append(Vector((WIRE_XY[-1][0], WIRE_XY[-1][1], gz(*WIRE_XY[-1]) + 0.4)))
        cu = bpy.data.curves.new("GreenWire", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.004
        sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1)
        for p, q in zip(sp.points, pts):
            p.co = (*q, 1)
        sp.use_endpoint_u = True; sp.order_u = 3
        o = bpy.data.objects.new("GreenWire", cu); bpy.context.collection.objects.link(o)
        o.data.materials.append(pbr("WireGreen", (0.05, 0.22, 0.06), 0.4, **{'Coat Weight': 0.4}))
        c["wire_pts"] = pts
        # small wooden stakes holding the wire up at a few trunks
        for k in range(2, len(pts) - 1, 7):
            p = pts[k]
            cyl("Stake", (p.x, p.y, p.z / 2 + gz(p.x, p.y) / 2), 0.015, p.z - gz(p.x, p.y) + 0.05, pbr("StakeW", (0.18, 0.13, 0.08), 0.9), verts=8)
    if variant != "wire":
        import sc_woods as F
        c.update(F.build("grey|detective,detective2"))
        c["F"] = F
        man = B.pfaffinger("Guide")
        c["P"]["man"] = man
        clear_path([((-6.0, -9.0), (-2.5, -3.0)), ((-7.2, -10.4), (-3.7, -4.4)), ((-5.2, -10.8), (-1.8, -4.8)), ((-6.8, -7.6), (-2.9, -4.2))], 1.0)
    else:
        pass
    if variant == "wire":
        pts = c["wire_pts"]
        clear_path([((pts[k].x + 0.5, pts[k].y - 0.4), (pts[k + 8].x + 0.5, pts[k + 8].y - 0.4)) for k in (4, 26)], 0.9)
    B.preview_cap()
    return c


def clear_path(segs, r=0.9):
    """Hide tree instances standing on a walk line (so nobody walks through a trunk)."""
    keys = ("tree", "spruce", "fir", "pine", "birch", "trunk", "Tree", "Spruce", "Birch", "Pine", "Fir")
    n = 0
    for o in bpy.data.objects:
        if o.parent is not None or not any(k in o.name for k in keys):
            continue
        p = Vector((o.location.x, o.location.y))
        for a, b in segs:
            a = Vector(a[:2]); b = Vector(b[:2]); ab = b - a
            u = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-6)))
            if (a + ab * u - p).length < r:
                o.hide_render = True; o.hide_viewport = True
                for ch in o.children_recursive:
                    ch.hide_render = True
                n += 1; break
    print("[woods] cleared", n, "trees")


def gz(c, x, y):
    return c["S"].ground_z(c, x, y) if "S" in c else c["F"].ground_z(c, x, y)


def place(c, h, p, face):
    B.stand(h, (p.x, p.y, 0), face, z=gz(c, p.x, p.y))


def walk_on(c, h, p0, p1, u, cycles, stride=20, swing=12):
    B.walk_to(h, p0, p1, u, cycles, stride=stride, swing=swing)
    x, y = h.arm.location.x, h.arm.location.y
    B.ground(h, gz(c, x, y))


def anim(c, t, move):
    sec = t * DUR[move]
    P_ = c["P"]
    if c["set"] == "wire":
        pts = c["wire_pts"]
        det = P_["detective"]; off = P_["officer"]
        # the detective walks along the wire, eyes down on it
        k0 = 4 if move == "wire" else 26
        i = min(len(pts) - 2, k0 + int(sec * 0.9 * 1.6))
        a = pts[k0]; b = pts[min(len(pts) - 1, k0 + 8)]
        u = min(1.0, sec / DUR[move])
        p0 = Vector((a.x + 0.5, a.y - 0.4, 0)); p1 = Vector((b.x + 0.5, b.y - 0.4, 0))
        walk_on(c, det, p0, p1, u * 0.7, 3.2 * u, stride=16, swing=8)
        B.nod(det, 12, "neck01"); B.nod(det, 18)
        # the officer stands at the far lookout, looking back up the path
        place(c, off, LOOK2, math.atan2(-(c["S"].PTS[6].x - LOOK2.x), (c["S"].PTS[6].y - LOOK2.y)) if False else math.radians(150))
        off.rot("head", (0, 0, 1), 20 * ease(min(1.0, max(0.0, (sec - 1.5) / 1.5))))
    else:
        d1, d2, man = P_["detective"], P_["detective2"], P_["man"]
        if move == "search":
            u = ease(min(1.0, sec / DUR[move]))
            slow = 0.75 * u + 0.25 * u * u
            walk_on(c, man, (-6.0, -9.0, 0), (-2.5, -3.0, 0), slow * 0.9, 4.0 * slow, stride=18 - 8 * u, swing=8)
            walk_on(c, d1, (-7.2, -10.4, 0), (-3.7, -4.4, 0), slow * 0.88, 4.0 * slow, stride=18, swing=10)
            walk_on(c, d2, (-5.2, -10.8, 0), (-1.8, -4.8, 0), slow * 0.86, 4.0 * slow, stride=18, swing=10)
            man.rot("head", (0, 0, 1), 25 * math.sin(sec * 0.9) * u)
        else:
            mp = Vector((-2.9, -3.7, 0))
            place(c, man, mp, math.radians(200))
            place(c, d1, Vector((-4.0, -5.1, 0)), math.radians(210))
            place(c, d2, Vector((-2.0, -5.4, 0)), math.radians(185))
            fwd = B.fwd_of(man); side = fwd.cross(Vector((0, 0, 1))).normalized()
            turn = ease(min(1.0, max(0.0, (sec - 2.0) / 1.2)))
            man.arm.rotation_euler.z = math.radians(200 - 95 * turn); bpy.context.view_layer.update()
            fwd = B.fwd_of(man); side = fwd.cross(Vector((0, 0, 1))).normalized()
            sh = man.bone_head("upperarm01.R")
            point = sh + (fwd * 0.9 + side * 0.25 + Vector((0, 0, -0.15))).normalized() * 0.6
            arm_up = 1.0 if (0.5 < sec < 1.9 or sec > 3.3) else 0.0
            if arm_up:
                reach(man, "R", point, Vector((0, 0, -1)), fwd)
            man.rot("head", (0, 0, 1), 10 * math.sin(sec * 1.4))
            d1.rot("head", (0, 0, 1), -28 * ease(min(1.0, max(0.0, (sec - 3.6) / 0.6))))
            d2.rot("head", (0, 0, 1), 24 * ease(min(1.0, max(0.0, (sec - 3.7) / 0.6))))
    bpy.context.view_layer.update()


def cam_wire(c, t):
    e = ease(t)
    a = c["wire_pts"][6]
    return (Vector((a.x - 3.2, a.y - 3.5, gz(c, a.x, a.y) + 4.2 - 2.6 * e)), Vector((a.x + 2.0, a.y - 0.6, gz(c, a.x, a.y) + 0.6)), 28)


def cam_lookout(c, t):
    e = ease(t)
    pts = c["wire_pts"]; a = pts[30]; b = pts[44]
    p = a.lerp(b, 0.15 + 0.6 * e) + Vector((-0.6, -0.9, 0))
    return (Vector((p.x, p.y, gz(c, p.x, p.y) + 0.5)), Vector((LOOK2.x, LOOK2.y, gz(c, LOOK2.x, LOOK2.y) + 1.0)), 32)


MOVES = {
    "wire": dict(kind="anim", dof=None, cam=cam_wire, anim=lambda c, t: anim(c, t, "wire"),
                 title=("CHAPTER 3", "The Man with the Spade", 8, 96)),
    "lookout": dict(kind="anim", dof=2.8, cam=cam_lookout, anim=lambda c, t: anim(c, t, "lookout"),
                    focus=lambda c, t: c["wire_pts"][36]),
    "search": dict(kind="anim", dof=4.0, cam=lambda c, t: (Vector((-1.2, -0.8, 1.7)).lerp(Vector((-1.5, -1.4, 1.65)), ease(t)), Vector((-4.0, -6.5, 1.2)), 30),
                   anim=lambda c, t: anim(c, t, "search"), focus=lambda c, t: c["P"]["man"].bone_head("spine03")),
    "unsure": dict(kind="anim", dof=3.2, cam=lambda c, t: (Vector((-6.8, -7.6, 1.6)).lerp(Vector((-6.2, -7.0, 1.58)), ease(t)), Vector((-2.9, -4.2, 1.3)), 35),
                   anim=lambda c, t: anim(c, t, "unsure"), focus=lambda c, t: c["P"]["man"].bone_head("head")),
}
