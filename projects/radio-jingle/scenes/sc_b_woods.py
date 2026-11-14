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

DUR = {"wire": 26.0, "lookout": 5.5, "search": 6.0, "unsure": 5.5, "spots": 9.0}
VARIANT_FOR = {"wire": "wire", "lookout": "wire", "search": "walk", "unsure": "walk", "spots": "walk"}
EXPOSURE = 0.0
BOUNCES = 5
# 3-8 v2: the loop they walked looking for the spot; a flag goes in wherever he stops and points
ROUTE = [(-6.0, -9.0), (-3.2, -8.6), (-2.6, -5.8), (-4.4, -4.3), (-6.5, -5.2), (-5.7, -7.4), (-4.0, -6.8), (-3.6, -5.4)]
# the wire: from a lookout west of the bend (watching the path toward Eching) through the trees south of the path
# to a second lookout past the bend (watching toward Schondorf). Plan view, metres (sc_path coordinates).
WIRE_XY = [(-9.0, -3.6), (-6.5, -4.6), (-4.0, -5.0), (-1.5, -5.6), (0.5, -6.4), (2.4, -8.0), (4.0, -9.6), (6.0, -11.0), (8.2, -12.0)]
LOOK1 = Vector((-9.4, -3.2, 0)); LOOK2 = Vector((8.6, -12.4, 0))


def suit_detective(name, col, years):
    """The same two 1981 detectives as the interrogation room (grey suit, brown suit)."""
    h = B.person(name, 1.0, years, "male_elegantsuit01", "short02" if years > 40 else "short04", hair_val=0.9 if years > 40 else 0.3, hair_sat=0.3)
    B.flat_clothes(h, col)
    return h


def build(variant=None):
    variant = variant or "wire"
    c = {"set": variant}
    if variant == "wire":
        import sc_path as S
        c.update(S.build("lowsun|officer"))
        c["P"]["detective"] = suit_detective("Det1", (0.06, 0.06, 0.065), 48)
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
        cu = bpy.data.curves.new("GreenWire", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0055
        sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1)
        for p, q in zip(sp.points, pts):
            p.co = (*q, 1)
        sp.use_endpoint_u = True; sp.order_u = 3
        o = bpy.data.objects.new("GreenWire", cu); bpy.context.collection.objects.link(o)
        o.data.materials.append(pbr("WireGreen", (0.05, 0.22, 0.06), 0.4, **{'Coat Weight': 0.4}))
        c["wire_pts"] = pts
        cu.bevel_factor_mapping_end = 'SPLINE'
        c["wire"] = o
        # v2: what the investigators left when they traced it: survey flags along the line, a paper tag with the
        # measured length tied to the wire, numbered evidence tents at the two lookout positions
        import b_fx as FX
        c["flags"] = []
        for k in range(3, len(pts) - 2, 4):
            p = pts[k]; g = gz(p.x, p.y)
            c["flags"].append((FX.survey_flag(f"SFlag{k}", (p.x + 0.25, p.y - 0.2, g)), k / (len(pts) - 1)))
        mid = pts[len(pts) // 2]
        dmid = (pts[len(pts) // 2 + 1] - pts[len(pts) // 2 - 1]); ang = math.atan2(dmid.y, dmid.x)
        tag = FX.card_plane("LenTag", mid - Vector((0, 0, 0.11)), 0.22, 0.13, FX.paper("LenTagP", (0.86, 0.82, 0.68), 120),
                            rot=(math.radians(90), 0, ang))
        txt = FX.fact_text("LenTxt", "≈ 140 m", mid - Vector((0, 0, 0.115)), 0.06, color=(0.07, 0.06, 0.05), rot=(math.radians(90), 0, ang))
        nrm = Vector((math.cos(ang + math.pi / 2), math.sin(ang + math.pi / 2), 0)); txt.location -= nrm * 0.003
        FX.curve("TagString", [mid, mid - Vector((0, 0, 0.045))], pbr("TagStr", (0.8, 0.78, 0.7), 0.8), bevel=0.0012)
        c["tag"] = [tag, txt]
        c["tents"] = [FX.marker_tent("Tent1", (LOOK1.x + 0.5, LOOK1.y - 0.3, gz(LOOK1.x + 0.5, LOOK1.y - 0.3)), 1, math.radians(-30), 0.16),
                      FX.marker_tent("Tent2", (LOOK2.x - 0.5, LOOK2.y + 0.3, gz(LOOK2.x - 0.5, LOOK2.y + 0.3)), 2, math.radians(150), 0.16)]
        # small wooden stakes holding the wire up at a few trunks
        for k in range(2, len(pts) - 1, 7):
            p = pts[k]
            cyl("Stake", (p.x, p.y, p.z / 2 + gz(p.x, p.y) / 2), 0.015, p.z - gz(p.x, p.y) + 0.05, pbr("StakeW", (0.18, 0.13, 0.08), 0.9), verts=8)
    if variant != "wire":
        import sc_woods as F
        c.update(F.build("grey"))
        c.setdefault("P", {})
        c["P"]["detective"] = suit_detective("Det1", (0.06, 0.06, 0.065), 48)
        c["P"]["detective2"] = suit_detective("Det2", (0.075, 0.045, 0.025), 36)
        c["F"] = F
        man = B.pfaffinger("Guide")
        c["P"]["man"] = man
        clear_path([((-6.0, -9.0), (-2.5, -3.0)), ((-7.2, -10.4), (-3.7, -4.4)), ((-5.2, -10.8), (-1.8, -4.8)), ((-6.8, -7.6), (-2.9, -4.2))], 1.0)
        clear_path([(ROUTE[k], ROUTE[k + 1]) for k in range(len(ROUTE) - 1)], 1.1)
        import b_fx as FX
        c["spot_flags"] = [FX.survey_flag(f"Spot{k}", (x + 0.35, y - 0.3, gz(c, x + 0.35, y - 0.3)), h=0.7) for k, (x, y) in enumerate(ROUTE[1:])]
    else:
        pass
    if variant == "wire":
        pts = c["wire_pts"]
        clear_path([((pts[k].x + 0.5, pts[k].y - 0.4), (pts[k + 8].x + 0.5, pts[k + 8].y - 0.4)) for k in (4, 26)], 0.9)
    B.preview_cap()
    c["exp0"] = bpy.context.scene.view_settings.exposure
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
    if move == "wire":                                    # v2 long take: the line draws itself, then its markers land
        import b_fx as FX
        dw = min(1.0, max(0.0, (t - 0.2) / 0.52))
        FX.draw(c["wire"], dw)
        for fl, k in c["flags"]:
            FX.show(fl, (dw - k) / 0.06)
        for o in c["tag"]:
            FX.show(o, (t - 0.55) / 0.06)
        for i, o in enumerate(c["tents"]):
            FX.show(o, (t - 0.64 - 0.05 * i) / 0.05)
    if move == "wire":                                    # the crane starts high under the canopy: open it up there
        bpy.context.scene.view_settings.exposure = c["exp0"] + 0.3 + 0.8 * (1.0 - t)
    P_ = c["P"]
    if move == "spots":
        route = [Vector((x, y, 0)) for x, y in ROUTE]
        seg = [(route[k + 1] - route[k]).length for k in range(len(route) - 1)]
        def at(d):                                         # point and heading on the route at distance d
            d = max(0.0, d)
            for k, L in enumerate(seg):
                if d <= L or k == len(seg) - 1:
                    f = min(1.0, d / max(L, 1e-6)); return route[k].lerp(route[k + 1], f), route[k + 1] - route[k], k, f
                d -= L
        def stop_time(sec_):                               # walk 0.85 m/s, pause 0.6 s at each vertex (he stops, looks, points)
            return sec_
        speed = 0.95
        for i, (key, lag) in enumerate((("man", 0.0), ("detective", 1.3), ("detective2", 2.4))):
            h = P_[key]
            d = max(0.0, (sec - 0.3) * speed - lag)
            p, dv, k, f = at(d)
            p1, _, _, _ = at(d + 0.05)
            fz = math.atan2(-dv.x, dv.y) + math.pi
            walk_on(c, h, p - dv.normalized() * 0.02, p1 + dv.normalized() * 0.02 if (p1 - p).length > 0 else p, 0.5, d / 0.75, stride=18, swing=10)
            if key == "man":
                B.nod(h, 8); h.rot("head", (0, 0, 1), 25 * math.sin(sec * 1.1))            # looking around as he walks
        dman = max(0.0, (sec - 0.3) * speed)
        for k, fl in enumerate(c["spot_flags"]):
            reach_d = sum(seg[:k + 1])
            FX_ = __import__("b_fx"); FX_.show(fl, (dman - reach_d - 0.4) / 0.3)
        bpy.context.view_layer.update()
        return
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
    """26 s long take. Crane down out of the dusk sky into the gap over the path bend; then dolly at chest height
    beside the wire while it draws itself ahead (flags land behind it); end between the two lookouts, turning
    from one view to the other ("views in opposite directions")."""
    pts = c["wire_pts"]; n = len(pts)
    g = lambda x, y: gz(c, x, y)
    if t < 0.28:
        u = ease(t / 0.28)
        pos = Vector((0.5, 4.0, 16.0)).lerp(Vector((-2.4, -0.2, 2.6)), u); pos.z = max(pos.z, g(pos.x, pos.y) + 2.6)
        tgt = Vector((-1.5, -2.5, g(-1.5, -2.5) + 0.3)).lerp(pts[3], u)
        return pos, tgt, 30
    if t < 0.74:
        u = (t - 0.28) / 0.46
        i = 2 + (n - 14) * ease(u); k = int(i); f = i - k
        p = pts[k].lerp(pts[k + 1], f)
        d = (pts[min(n - 1, k + 4)] - pts[k]); d.z = 0; d.normalize()
        side = Vector((-d.y, d.x, 0))
        pos = p + side * 1.3 - d * 0.9; pos.z = g(pos.x, pos.y) + 1.1
        if u < 0.08:                                                        # blend in from the crane end
            w = ease(u / 0.08); a0 = Vector((-2.4, -0.2, g(-2.4, -0.2) + 2.6)); pos = a0.lerp(pos, w)
        head = pts[min(n - 1, k + 7)]
        return pos, Vector((head.x, head.y, head.z - 0.2)), 30
    u = ease((t - 0.74) / 0.26)
    pos = Vector((1.2, -4.6, 0)); pos.z = g(pos.x, pos.y) + 1.5
    l1 = Vector((LOOK1.x, LOOK1.y, g(LOOK1.x, LOOK1.y) + 0.5)); l2 = Vector((LOOK2.x, LOOK2.y, g(LOOK2.x, LOOK2.y) + 0.5))
    k0 = int(2 + (n - 14)); p0 = pts[k0]
    if u < 0.25:
        w = ease(u / 0.25); d = (pts[min(n - 1, k0 + 4)] - p0); d.z = 0; d.normalize(); side = Vector((-d.y, d.x, 0))
        a0 = p0 + side * 1.3 - d * 0.9; a0.z = g(a0.x, a0.y) + 1.1
        pos = a0.lerp(pos, w)
        return pos, pts[min(n - 1, k0 + 7)].lerp(l2, w), 30
    w = ease((u - 0.25) / 0.75)
    tgt = l2.lerp(l1, w)                                                   # look down one way, then the other
    return pos, tgt, 30 + 4 * w


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
    "spots": dict(kind="anim", dof=None, cam=lambda c, t: (Vector((-0.8, -12.8, 9.5)).lerp(Vector((-1.6, -11.6, 7.6)), ease(t)), Vector((-4.5, -6.6, 0.0)), 30),
                  anim=lambda c, t: anim(c, t, "spots")),
    "unsure": dict(kind="anim", dof=3.2, cam=lambda c, t: (Vector((-6.8, -7.6, 1.6)).lerp(Vector((-6.2, -7.0, 1.58)), ease(t)), Vector((-2.9, -4.2, 1.3)), 35),
                   anim=lambda c, t: anim(c, t, "unsure"), focus=lambda c, t: c["P"]["man"].bone_head("head")),
}
