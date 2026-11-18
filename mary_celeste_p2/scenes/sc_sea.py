"""Shots on the water: New York harbour, the Atlantic off Santa Maria, the ship as found.
blender -b --python scenes/sc_sea.py -- SHOT=21"""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "p2lib"))
import env
import common as C
C.reset()
import bpy
from mathutils import Vector, Matrix
import stage as S, seaset as W, cast, acts as A, poses as P, cabin
import ship, sea

SHOT = S.shot_arg() or "21"
HAIR = float(os.environ.get("HAIR", "1.0"))
sc = S.setup(samples=128)
cine = {"sat": 1.08, "exposure": 0.0}


def on_deck(x, y, yaw, heel_M):
    return heel_M @ Matrix.Translation((x, y, ship.zdeck(x) + 0.005)) @ Matrix.Rotation(math.radians(yaw), 4, 'Z')


def wind_local(world_dir, hd_deg):
    return Matrix.Rotation(math.radians(-hd_deg), 3, 'Z') @ Vector(world_dir).normalized()


def pennant(SM, mast_top, wind_dir, length=5.0, name="pennant"):
    """A long narrow masthead pennant streaming downwind, with a slow travelling wave."""
    n = 40
    red = cabin.cloth_material("bunting", (0.45, 0.03, 0.03), sheen=0.3)
    V = []; F = []
    d = Vector(wind_dir).normalized(); side = d.cross(Vector((0, 0, 1))).normalized()
    for i in range(n + 1):
        u = i / n
        w = 0.32 * (1 - u) + 0.03
        p0 = mast_top + d * (length * u) + Vector((0, 0, -0.5 * u * u)) + side * (0.25 * math.sin(u * 9) * u)
        V.append(tuple(p0)); V.append(tuple(p0 + Vector((0, 0, -w))))
    for i in range(n):
        F.append([2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1])
    o = ship.mesh_obj(name, V, F, red)
    o.data.materials[0].use_backface_culling = False
    return o


def _sextant(person, M):
    """A brass sextant held up to the eye: arc, frame, index arm, telescope, mirrors; parented to the right wrist."""
    h = person.h
    br = cabin.brass(); dk = cabin.plain("sx_black", (0.02, 0.02, 0.02), rough=0.4)
    wr, wl = h.bone_tail("wrist.R"), h.bone_tail("wrist.L")
    c = (wr + wl) / 2 + Vector((0, 0, 0.02))
    fw = M.to_3x3() @ Vector((0, -1, 0)); sd = M.to_3x3() @ Vector((1, 0, 0)); up = Vector((0, 0, 1))
    parts = []
    pts = [c + up * (0.16 * math.cos(a) - 0.1) + sd * (0.16 * math.sin(a)) for a in [math.radians(t) for t in range(-32, 33, 4)]]
    parts.append(ship.rope("sx_arc", pts, 0.006, br))
    apex = c + up * 0.07
    for p in (pts[0], pts[-1], pts[len(pts) // 2]):
        parts.append(ship.cyl("sx_frame", apex, p, 0.004, mat=br, verts=8))
    parts.append(ship.cyl("sx_scope", apex - fw * 0.06 + sd * 0.03, apex + fw * 0.08 + sd * 0.03, 0.012, mat=dk, verts=14))
    parts.append(ship.box("sx_mirror", tuple(apex + sd * 0.0), (0.03, 0.005, 0.04), cabin.plain("mirror", (0.9, 0.9, 0.9), rough=0.02, metal=1.0)))
    for o in parts:
        cabin.attach(o, person, "wrist.R")


if SHOT in ("21", "22", "24", "25", "26", "27"):
    mood = {"21": "grey", "22": "grey", "24": "harbour", "25": "harbour", "26": "harbour", "27": "harbour"}[SHOT]
    sun_d = W.light(mood)
    state = "sail" if SHOT in ("26", "27") else "port"
    mc = ship.build("MC", sails=("full" if state == "sail" else "found"), wet=0.05, detail=(SHOT not in ("27",)), hatches_off=False,
                    wind=(-1.0, -0.2, 0) if SHOT != "21" else (1, 0.3, 0))
    if state == "port":
        W.furl_all(mc)
    SM = mc["root"].matrix_world.copy()
    W.water(mood, hulls=(mc["hull"],), cut=(0.0, 0.0, ship.L / 2 - 0.4, ship.B / 2 - 0.15))
    if SHOT in ("21", "22"):
        W.land("staten", (-200, 520), 2200, 55, houses=14)
        W.land("bklyn", (900, -900), 3000, 25, color=(0.12, 0.11, 0.1), houses=0, seed=8)
        # the anchor chain out of the hawse, down into the water
        rope = mc["mats"]["iron"]
        hz = Vector((ship.L / 2 - 1.2, 0.9, ship.zdeck(ship.L / 2 - 1.2) + 0.3))
        ship.rope("chain", [hz, hz + Vector((3.0, 0.6, -hz.z - 0.3))], 0.035, rope)
    mt = mc["spars"]["main_top"] if "main_top" in mc["spars"] else Vector((-3.6, 0, 24.0))
    if SHOT == "21":     # at anchor off Staten Island; wind ahead (the pennant streams aft)
        pennant(SM, mt, (-1, 0.15, 0))
        S.cam(Vector((90, -70, 6)), Vector((0, 8, 8)), lens=50, fstop=None)
    elif SHOT == "22":   # MCU: Briggs watches the pennant stream the wrong way; a small shrug
        pennant(SM, mt, (-1, 0.15, 0))
        b = cast.Briggs()
        P.stand(b.h, weight="L"); P.head(b.h, pitch=-28, yaw=-12)
        P.arm_down(b.h, "L"); P.rest_hand(b.h, "L"); P.arm_down(b.h, "R"); P.rest_hand(b.h, "R")
        M = on_deck(-6.0, -2.7, 160, SM)
        b.finish_live(place=M, density=HAIR)
        b.look(mt)
        hd = b.h.bone_head("head")
        fw = M.to_3x3() @ Vector((0, -1, 0)); sd = M.to_3x3() @ Vector((1, 0, 0))
        S.frame([hd + Vector((0, 0, 0.1)), hd - Vector((0, 0, 0.9)), mt], -fw + sd * 0.3 + Vector((0, 0, -0.15)), lens=35, fill=0.9, fstop=5.6)
    elif SHOT == "24":   # the pennant now streams forward: the wind has turned
        pennant(SM, mt, (1, -0.1, 0))
        S.cam(mt + Vector((-6, -12, -6)), mt + Vector((2.0, 0, -0.6)), lens=55)
    elif SHOT == "25":   # MS: Sarah hands her letter to the pilot at the rail
        s = cast.Sarah(expr={"mouth-corner-puller": 0.3})
        pl = cast.Sailor(name="Pilot", years=50, jacket=(0.02, 0.02, 0.03), beard=True, cap=True)
        xr = -5.0; yr = -(ship.B / 2 - 0.95)
        P.stand(s.h, weight="L"); P.head(s.h, pitch=6, yaw=6)
        Ms = on_deck(xr - 0.35, yr + 0.15, 75, SM); Mp = on_deck(xr + 0.45, yr + 0.05, -105, SM)
        mid = (Ms.to_translation() + Mp.to_translation()) / 2 + Vector((0, 0, 1.2))
        P.hand_reach(s.h, "R", Ms.inverted() @ mid, elbow=(-0.7, 0.4, -0.7)); P.rest_hand(s.h, "R", 30)
        P.arm_down(s.h, "L", out=0.1, fwd=0.15, bend=30); P.rest_hand(s.h, "L")
        P.stand(pl.h, weight="R"); P.head(pl.h, pitch=10)
        P.hand_reach(pl.h, "L", Mp.inverted() @ (mid + Vector((0.0, 0, -0.02))), elbow=(0.7, 0.4, -0.7)); P.rest_hand(pl.h, "L", 30)
        P.arm_down(pl.h, "R"); P.rest_hand(pl.h, "R")
        s.finish_live(place=Ms, density=HAIR); pl.finish_live(place=Mp, density=HAIR)
        let = cabin.sheet("letter", mid + Vector((0, 0, -0.03)), 0.11, 0.16, cabin.paper_material("env", ink=False), rot=0.5)
        let.rotation_euler = (math.radians(70), 0, 0)
        s.look(pl.h.bone_head("head")); pl.look(mid)
        S.cam(SM @ Vector((xr + 0.9, yr + 2.6, ship.zdeck(xr) + 1.55)), mid + Vector((0, 0, -0.15)), lens=35, fstop=4.0)
    elif SHOT == "26":   # the pilot boat pulls away; the Mary Celeste sets sail behind it
        bt, _ = W.pilot_boat("pilotboat", Vector((-30, -26, 0.0)), 200)
        S.cam(Vector((-58, -52, 3.5)), Vector((-8, 0, 7)), lens=35)
    elif SHOT == "27":   # EWS: she sails out into the haze, getting smaller
        mc["root"].location = (380, 220, 0); mc["root"].rotation_euler = (0, 0, math.radians(25))
        S.cam(Vector((0, 0, 9)), Vector((380, 220, 10)), lens=60)
    cine = {"sat": 1.08, "exposure": 0.05 if mood != "grey" else 0.2}

elif SHOT in ("28", "29", "33", "37"):  # 25 November, dawn: Santa Maria in view (37: a noon sight, flashback)
    mood = "noon" if SHOT == "37" else "dawn"
    sun_d = W.light(mood)
    WIND = Vector((0.3, -1.0, 0)).normalized()
    hd_deg = 120.0
    mc = ship.build("MC", sails="full", wet=0.2, detail=True, hatches_off=False, wind=wind_local(WIND, hd_deg),
                    rail_gap=((-2.7, -0.6, "S") if SHOT == "33" else None))
    mc["root"].rotation_euler = (math.radians(-3), 0, math.radians(hd_deg))
    bpy.context.view_layer.update()
    SM = mc["root"].matrix_world.copy()
    W.water(mood, hulls=(mc["hull"],), cut=(0.0, 0.0, ship.L / 2 - 0.4, ship.B / 2 - 0.15))
    isl = W.island_santa_maria(Vector((-9000, -9000, 0)) if SHOT != "37" else Vector((-40000, 0, 0)))
    if SHOT == "28":
        S.cam(SM @ Vector((14, -42, 3.2)), SM @ Vector((-4, 0, 7)), lens=30)
    elif SHOT == "29":   # two crewmen at the bow; one points; Briggs behind with a telescope (out of focus)
        a = cast.Sailor(name="Seaman1", years=24, jacket=(0.15, 0.12, 0.08))
        b = cast.Sailor(name="Seaman2", years=35, scarf=(0.1, 0.12, 0.3))
        isl_c = Vector((-9000, -9000, 300))
        xb = ship.L / 2 - 4.5
        Ma = on_deck(xb, -1.2, 0, SM); Mb = on_deck(xb - 0.8, -2.1, 0, SM)
        for p_, Mx, point in ((a, Ma, True), (b, Mb, False)):
            Mi = Mx.inverted()
            d = (Mi @ isl_c).normalized()
            yaw = math.degrees(math.atan2(-d.x, -d.y))
            p_.h.arm.rotation_euler = (0, 0, 0)
            P.stand(p_.h, weight="L", twist=0)
            P.head(p_.h, pitch=-4, yaw=0)
            if point:
                P.hand_reach(p_.h, "R", p_.h.bone_head("upperarm01.R") + d * 0.62 + Vector((0, 0, 0.05)), elbow=(-0.3, 0.4, -0.6))
                for f in (3, 4, 5):
                    for k in (1, 2, 3):
                        p_.h.rot(f"finger{f}-{k}.R", (1, 0, 0), 70)
            else:
                P.arm_down(p_.h, "R"); P.rest_hand(p_.h, "R")
            P.arm_down(p_.h, "L"); P.rest_hand(p_.h, "L")
            Mx2 = Mx @ Matrix.Rotation(math.radians(yaw), 4, 'Z')
            p_.finish_live(place=Mx2, density=HAIR * 0.7)
            p_.look(isl_c)
        ha, hb = a.h.bone_head("head"), b.h.bone_head("head")
        di = (isl_c - ha); di.z = 0; di.normalize()
        perp = Vector((-di.y, di.x, 0))
        S.frame([ha, hb, ha - Vector((0, 0, 1.0)), ha + di * 1.2], -di * 1.0 + perp * 0.8 + Vector((0, 0, 0.12)), lens=35,
                fill=0.75, fstop=5.6, aim_offset=(0, 0, 0.2))
    elif SHOT == "33":   # LOW: through the rail gap, open sea, the island far off, empty water (callback)
        g = SM @ Vector((-1.65, -(ship.B / 2), ship.zdeck(-1.65) + 0.5))
        S.cam(SM @ Vector((-1.7, 0.2, ship.zdeck(-1.7) + 1.25)), SM @ Vector((-1.7, -40, -1.5)), lens=24)
    elif SHOT == "37":   # flashback, warm noon: Briggs takes a sight with the sextant
        b = cast.Briggs()
        M = on_deck(-6.2, -2.8, 0, SM)
        P.stand(b.h, weight="R", lean=-4)
        P.head(b.h, pitch=-12, yaw=0)
        eye = b.h.bone_head("head") + Vector((0.0, -0.11, 0.06))
        P.hand_reach(b.h, "R", eye + Vector((-0.06, -0.12, -0.12)), elbow=(-0.9, 0.2, -0.6)); P.grip(b.h, "R", 0.8)
        P.hand_reach(b.h, "L", eye + Vector((0.08, -0.2, -0.2)), elbow=(0.9, 0.2, -0.6)); P.grip(b.h, "L", 0.6)
        b.finish_live(place=M, density=HAIR)
        _sextant(b, M)
        hd = b.h.bone_head("head")
        S.cam(hd + (M.to_3x3() @ Vector((1.2, -1.6, -0.25))), hd + Vector((0, 0, -0.15)), lens=45, fstop=4.0)
    cine = {"sat": 1.1, "exposure": 0.1}

elif SHOT in ("42", "43", "44", "45"):   # 4 December: the ship as found (overcast), Deveau aboard
    sun_d = W.light("overcast")
    WIND = Vector((0.3, -1.0, 0)).normalized()
    GAP = (-2.7, -0.6, "S")
    mc = ship.build("MC", sails="found", rail_gap=GAP, wind=wind_local(WIND, 0), wet=0.8, detail=True)
    mc["root"].matrix_world = Matrix.Rotation(math.radians(-2.5), 4, 'X')
    bpy.context.view_layer.update()
    SM = mc["root"].matrix_world.copy()
    W.water("overcast", hulls=(mc["hull"],), cut=(0.0, 0.0, ship.L / 2 - 0.4, ship.B / 2 - 0.15))
    if SHOT == "42":
        g = SM @ Vector((-1.65, -(ship.B / 2), ship.zdeck(-1.65) + 0.5))
        S.cam(SM @ Vector((-1.75, 0.6, ship.zdeck(-1.75) + 1.25)), SM @ Vector((-1.7, -40, -1.8)), lens=24)
    elif SHOT == "43":   # reconstruction: figures (faces away) lower the boat through the gap; one passes a box down
        cine = {"sat": 0.9, "exposure": 0.05}
        bt, ms = W.pilot_boat("yawl", SM @ Vector((-1.65, -(ship.B / 2) - 1.9, 0.0)), 0)
        for o in ms:
            if any(k in o.name.lower() for k in ("rig", "mast", "sail", "rope")):
                o.hide_render = True; o.hide_viewport = True
        figs = []
        for k, (x, y, yaw) in enumerate(((-3.05, -3.0, 20), (0.15, -3.0, -20), (-1.6, -1.75, 0))):
            f = cast.Sailor(name=f"fig{k}", years=30 + k * 6, jacket=[(0.05, 0.04, 0.03), (0.02, 0.02, 0.03), (0.1, 0.08, 0.05)][k])
            P.stand(f.h, lean=22, weight="L"); P.head(f.h, pitch=30)
            M = on_deck(x, y, yaw, SM)
            Mi = M.inverted()
            tgt = SM @ Vector((x, -(ship.B / 2) - 0.2, ship.zdeck(x) + 0.7))
            P.hand_reach(f.h, "R", Mi @ tgt + Vector((-0.15, 0, 0)), elbow=(-0.8, 0.3, -0.6)); P.grip(f.h, "R")
            P.hand_reach(f.h, "L", Mi @ tgt + Vector((0.15, 0, 0.05)), elbow=(0.8, 0.3, -0.6)); P.grip(f.h, "L")
            f.finish_live(place=M, density=HAIR * 0.6)
            for dz in (0,):
                ship.rope("fall", [tgt, tgt + Vector((0, -0.8, -2.0))], 0.014, mc["mats"]["rope"])
        S.cam(SM @ Vector((0.6, 2.0, ship.zdeck(-1.6) + 1.9)), SM @ Vector((-1.6, -5.2, 0.6)), lens=26, fstop=5.6)
    elif SHOT in ("44", "45"):   # Deveau at the pump well with the sounding rod; then determined
        d = cast.Deveau2(wet=0.6)
        xp = ship.MAIN_X + 0.9 if hasattr(ship, "MAIN_X") else -3.0
        pump = SM @ Vector((xp, 0.7, ship.zdeck(xp) + 1.05))
        M = on_deck(xp + 0.65, 1.2, A.yaw_to((xp + 0.65, 1.2), (xp, 0.7)), SM)
        Mi = M.inverted()
        P.stand(d.h, lean=12, weight="L")
        P.head(d.h, pitch=(34 if SHOT == "44" else 6), yaw=(0 if SHOT == "44" else -20))
        rod_top = pump + Vector((0, 0, 0.35))
        P.hand_reach(d.h, "R", Mi @ (rod_top + Vector((0.0, 0, -0.1))), elbow=(-0.8, 0.3, -0.6)); P.grip(d.h, "R")
        P.hand_reach(d.h, "L", Mi @ (rod_top + Vector((0.0, 0, -0.42))), elbow=(0.8, 0.3, -0.6)); P.grip(d.h, "L")
        d.lids(0.4 if SHOT == "44" else 0.1); d.brow_knit(1.0)
        d.finish_live(place=M, density=HAIR)
        rod = ship.cyl("sounding_rod", rod_top + Vector((0, 0, 0.12)), pump - Vector((0, 0, 0.6)), 0.008, mat=mc["mats"]["iron"], verts=10)
        hd = d.h.bone_head("head")
        if SHOT == "44":
            d.look(rod_top - Vector((0, 0, 0.5)))
            S.frame([hd, rod_top, pump - Vector((0, 0, 0.9))], SM.to_3x3() @ Vector((-1.0, -1.3, 0.25)), lens=35, fill=0.85, fstop=4.0)
        else:
            d.look(SM @ Vector((ship.L / 2, -2, 3)))
            fw = M.to_3x3() @ Vector((0, -1, 0)); sd = M.to_3x3() @ Vector((1, 0, 0))
            S.frame([hd + Vector((0, 0, 0.1)), hd - Vector((0, 0, 1.0))], -fw + sd * 0.45 + Vector((0, 0, 0.05)), lens=40, fill=0.8, fstop=4.0)
    cine = {"sat": 1.0, "exposure": 0.05}

S.finish(S.out_path(SHOT), cine=cine)
