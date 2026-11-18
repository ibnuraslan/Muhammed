"""Part 3 shot list (5:20-7:50): every shot is a function of t in [0, 1] that builds its set, people and camera.
VO, sizes and actions follow the master shot list (mary_celeste/storyboard/shots.py, sentences 77-110)."""
import os, math
import numpy as np
from mathutils import Vector, Matrix
import bpy
import common as C
import ship, sea, poses as P, human as H
import crew, sets as ST

E = os.environ.get
SHOTS = {}


def shot(sid, vo, size, dur, action, sfx, card=None, tag=None):
    def deco(f):
        SHOTS[sid] = dict(fn=f, vo=vo, size=size, dur=dur, frames=int(round(dur * 24)), action=action, sfx=sfx,
                          card=card, tag=tag)
        return f
    return deco


def build(sid, t):
    s = SHOTS[sid]
    spp = int(E("SPP", "96"))
    C.render_setup(samples=spp, noise=0.03, bounces=8)
    info = s["fn"](t) or {}
    if E("SIDECAM"):           # SIDECAM=x,y,z,tx,ty,tz : a fixed check camera
        v = [float(x) for x in E("SIDECAM").split(",")]
        C.camera(Vector(v[:3]), Vector(v[3:]), lens=28)
    if E("DEBUGCAM"):          # a wide look from behind/above the shot camera, to check staging
        c = bpy.context.scene.camera
        d = c.matrix_world.to_3x3() @ Vector((0, 0, -1))
        off = [float(v) for v in E("DEBUGCAM").split(",")]
        loc = c.location - d * off[0] + Vector((0, 0, off[1]))
        C.camera(loc, c.location + d * off[2], lens=24)
    return info


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return Vector(a).lerp(Vector(b), t)


def cam(loc, target, lens=50, fstop=None, focus=None, roll=0.0):
    c = C.camera(Vector(loc), Vector(target), lens=lens, fstop=fstop, focus=focus, roll=roll)
    return c


def eyes(p):
    e = p.h.eyes
    return (e[0].location + e[1].location) / 2 if e else None


def hair(p):
    return float(E("HAIR", "1.0"))


def man(key, M, pose, look=None, wet=0.3, wig=False, idx=0):
    p = crew.person(key, wet=wet, wig=wig, idx=idx)
    pose(p)
    p.finish(look_at=look, place=M, density=hair(p))
    return p


# ============================================================================ DEI GRATIA DECK, 5 DEC 1872
DG_HEAD = 20.0               # the Dei Gratia's heading (world deg); the Mary Celeste lies off her starboard beam
WIND = (0.35, -1.0, 0)


def dg_deck(mood="day", t=0.0, mc_far=True, sun_az=200, sun_el=19):
    ST.exterior(mood, sky_rot=40, sun_az=sun_az, sun_el=sun_el)
    d = ST.dg("full", wind=ST.local_wind(WIND, DG_HEAD), detail=True)
    SHIP = ST.set_ship(d, heading=DG_HEAD, heel=3.0 + 0.6 * math.sin(t * 2.2), pitch=0.4 * math.sin(t * 1.7 + 1))
    hulls = [d["hull"]]
    if mc_far:
        m = ST.mc("found", wind=ST.local_wind(WIND, 250), detail=False, gap=True)
        ST.set_ship(m, loc=SHIP @ Vector((30, -380, 0)) * Vector((1, 1, 0)), heading=250, heel=4)
        hulls.append(m["hull"])
    ST.ocean_around((0, -150, 0), hulls=hulls, mood=mood, size=260, time=11 + t * 3.0,
                    cut=None)
    return SHIP


def pose_warn(p, t):
    """Morehouse: weight back, right hand opens toward the Mary Celeste as he makes his point."""
    h = p.h
    P.stand(h, lean=-2, weight="L", twist=-4)
    P.head(h, pitch=-3, yaw=-6 + 4 * ease(t), tilt=-2)
    P.arm_down(h, "L", out=0.1, fwd=0.05, bend=20); P.rest_hand(h, "L", curl=30)
    a = ease(min(1, t * 1.6))
    elb = Vector((-0.1, -0.35, -1)); hand = Vector((-0.32, -0.42 - 0.08 * a, 1.05 + 0.08 * a))
    P.hand_reach(h, "R", hand, elbow=(-0.8, 0.3, -0.6))
    h.aim("wrist.R", Vector((-0.5, -0.8, 0.15)))
    P.rest_hand(h, "R", curl=10)
    p.brow_knit(0.8); p.lids(0.25)


def pose_listen(p, t, turn=0.0):
    h = p.h
    P.stand(h, lean=3, weight="R", twist=4 + 18 * turn)
    P.head(h, pitch=4 + 6 * turn, yaw=8 - 40 * turn, tilt=1)
    P.arm_down(h, "L", out=0.1, fwd=0.03, bend=14); P.rest_hand(h, "L", curl=26)
    P.arm_down(h, "R", out=0.1, fwd=0.03, bend=16); P.rest_hand(h, "R", curl=28)
    p.brow_knit(0.6 + 0.4 * turn); p.lids(0.3 + 0.3 * turn)


DV_POS = (-6.2, -1.45)     # Deveau on the Dei Gratia's quarterdeck, starboard side
MO_POS = (-5.1, -2.75)


def _pair(SHIP, t, turn=0.0):
    hdv = math.degrees(math.atan2(MO_POS[1] - DV_POS[1], MO_POS[0] - DV_POS[0]))
    Mdv = ST.on_ship(SHIP, *DV_POS, hdv)
    Mmo = ST.on_ship(SHIP, *MO_POS, hdv + 180)
    mo = crew.person("morehouse", wet=0.1); pose_warn(mo, t)
    dv = crew.person("deveau", wet=0.1); pose_listen(dv, t, turn)
    # eyes on each other (world): rough head heights, refined after finish
    mo.finish(look_at=Mdv @ Vector((0, 0, 1.66)), place=Mmo, density=hair(mo))
    dv.finish(look_at=Mmo @ Vector((0, 0, 1.66)), place=Mdv, density=hair(dv))
    return mo, dv, Mmo, Mdv


@shot("p3_01", "Morehouse warns him that taking her in could put both crews at risk.", "OTS · 35mm", 3.6,
      "Over Deveau's shoulder: Morehouse makes his point, right hand opening toward the derelict",
      "Wind in the rigging, hull creak, Morehouse's boots shift", card=("r", "DAVID MOREHOUSE", "Captain, Dei Gratia"))
def s01(t):
    SHIP = dg_deck(t=t)
    mo, dv, Mmo, Mdv = _pair(SHIP, t)
    em = eyes(mo); ed = eyes(dv)
    back = (ed - em).normalized(); side = back.cross(Vector((0, 0, 1))).normalized()
    loc = ed + back * 1.0 + side * 0.42 + Vector((0, 0, 0.0)) + back * 0.06 * ease(t)
    cam(loc, em + Vector((0, 0, -0.32)) - side * 0.15, lens=35, fstop=4.0, focus=(em - loc).length)
    return dict(cine={"sat": 1.08, "exposure": -0.05})


@shot("p3_02", "The Dei Gratia will have to give up men it needs for its own voyage.", "OTS · 35mm", 3.4,
      "Reverse over Morehouse onto Deveau, who listens", "Wind, rigging slap")
def s02(t):
    SHIP = dg_deck(t=t)
    mo, dv, Mmo, Mdv = _pair(SHIP, t)
    em = eyes(mo); ed = eyes(dv)
    back = (em - ed).normalized(); side = back.cross(Vector((0, 0, 1))).normalized()
    loc = em + back * 1.0 - side * 0.42 + Vector((0, 0, 0.0))
    cam(loc, ed + Vector((0, 0, -0.32)) + side * 0.15, lens=35, fstop=4.0, focus=(ed - loc).length)
    return dict(cine={"sat": 1.08, "exposure": -0.05})


def pose_haul(p, t, phase=0.0):
    """A sailor hauling on a line overhead, hand over hand (both hands on the same rope)."""
    h = p.h
    s = math.sin(2 * math.pi * (t * 1.3 + phase))
    P.stand(h, lean=8 + 4 * s, weight="L")
    P.head(h, pitch=-18, yaw=0)
    for sd, sg, k in (("L", 1, 0.0), ("R", -1, 1.0)):
        z = 1.75 + 0.18 * math.sin(2 * math.pi * (t * 1.3 + phase) + k * math.pi)
        P.hand_reach(h, sd, Vector((0.02 * sg, -0.22, z)), elbow=(0.6 * sg, 0.2, -0.7))
        h.aim(f"wrist.{sd}", Vector((-0.2 * sg, -0.3, 1)))
        P.grip(h, sd, 1.0)


@shot("p3_03", "The Dei Gratia will have to give up men it needs for its own voyage.", "WS · 28mm", 3.6,
      "Track along the Dei Gratia's deck: two of her small crew haul on the main sheet", "Blocks squeal, rope, footsteps")
def s03(t):
    SHIP = dg_deck(t=t)
    rope_top = []
    for i, (x, y, key) in enumerate(((-2.9, 2.75, "sailor_a"), (-3.7, 2.8, "sailor_b"))):
        M = ST.on_ship(SHIP, x, y, 180)
        p = crew.person(key, wet=0.1, idx=i); pose_haul(p, t, phase=0.5 * i)
        p.finish(look_at=M @ Vector((0, -0.3, 3)), place=M, density=hair(p))
        rope_top.append(M @ Vector((0, -0.22, 1.75)))
    # the sheet they haul: runs from the boom block overhead down through their hands to a pin on the rail
    a = ST.deck_world(SHIP, -3.2, 2.6, 7.0); b = ST.deck_world(SHIP, -4.6, 3.4, 0.9)
    pts = [a, rope_top[0] + Vector((0, 0, 0.05)), rope_top[1] + Vector((0, 0, 0.05)), b]
    ship.rope("sheet", pts, 0.012, bpy.data.materials.get("DG_rope") or ship.tarred_rope("r"))
    loc = lerp(ST.deck_world(SHIP, -0.6, 0.9, 1.35), ST.deck_world(SHIP, -1.2, 1.2, 1.35), ease(t))
    cam(loc, ST.deck_world(SHIP, -3.4, 2.75, 1.55), lens=30, fstop=4.0)
    return dict(cine={"sat": 1.08})


@shot("p3_04", "Deveau goes anyway.", "MS · 35mm", 2.2,
      "From behind Morehouse: Deveau turns away from him toward the rail and the waiting boat", "One footstep, music beat")
def s04(t):
    SHIP = dg_deck(t=t)
    mo, dv, Mmo, Mdv = _pair(SHIP, 0.9, turn=ease(t))
    ed = eyes(dv); em = eyes(mo)
    back = (em - ed).normalized(); side = back.cross(Vector((0, 0, 1))).normalized()
    loc = em + back * 1.6 - side * 0.55 + Vector((0, 0, -0.1))
    cam(loc, ed + Vector((0, 0, -0.45)), lens=35, fstop=4.0, focus=(ed - loc).length)
    return dict(cine={"sat": 1.06})


# ============================================================================ THE TRANSFER
import props as PR


def boat_alongside(SHIP, x=-2.0, gap=1.0, t=0.0):
    """The Dei Gratia's boat lying alongside her starboard side, riding the swell a little."""
    b = PR.boat("dgboat")
    hb = ship.half_breadth((x + ship.L / 2) / ship.L, 0.75)
    Mb = SHIP @ Matrix.Translation((x, -(hb + gap + b["B"] / 2), -0.28 + 0.05 * math.sin(t * 2.5))) @ Matrix.Rotation(math.radians(1.5 * math.sin(t * 2 + 1)), 4, 'X')
    for o in b["objs"]:
        o.matrix_world = Mb @ o.matrix_world
    return b, Mb


def pose_lower(p, t, rope_top_local):
    """Sailor at the rail paying out a line hand under hand (both hands on the rope)."""
    h = p.h
    P.stand(h, lean=14, weight="L", twist=-3)
    P.head(h, pitch=38, yaw=0)
    for sd, sg, dz in (("L", 1, 0.0), ("R", -1, -0.16)):
        z = rope_top_local.z + dz + 0.04 * math.sin(t * 6 + (0 if sd == "L" else 2))
        P.hand_reach(h, sd, Vector((rope_top_local.x + 0.015 * sg, rope_top_local.y, z)), elbow=(0.7 * sg, 0.2, -0.6))
        h.aim(f"wrist.{sd}", Vector((-0.25 * sg, -0.5, -0.8)))
        P.grip(h, sd, 1.0)


def pose_guide(p, t, hands_local):
    """Man standing in the boat, reaching up to steady the load as it comes down."""
    h = p.h
    P.stand(h, lean=-6, weight="R")
    P.head(h, pitch=-30, yaw=4)
    for sd, sg in (("L", 1), ("R", -1)):
        hp = Vector(hands_local[sd])
        P.hand_reach(h, sd, hp, elbow=(0.7 * sg, 0.3, -0.5))
        h.aim(f"wrist.{sd}", Vector((-0.6 * sg, -0.3, 0.6)))
        P.rest_hand(h, sd, curl=40)


@shot("p3_05", "He brings two sailors, his own navigation instruments, and food from his ship.", "MS · 35mm", 3.8,
      "From the Dei Gratia's rail: a sailor lowers the food sack on a line; Deveau, standing in the boat, steadies it; his sextant case is already on the thwart",
      "Rope through hands, sack thump, oarlocks knock, water slap")
def s05(t):
    SHIP = dg_deck(t=0.3, mc_far=False)
    b, Mb = boat_alongside(SHIP, t=t)
    # the sack hangs on a line from the rail down to the boat
    rail_x = -1.6
    hb = ship.half_breadth((rail_x + ship.L / 2) / ship.L, 1.0)
    Msl = ST.on_ship(SHIP, rail_x, -(hb - 0.55), -90)
    rope_local = Vector((0.0, -0.5, 1.25))
    sl = crew.person("sailor_b", wet=0.1, idx=1); pose_lower(sl, t, rope_local)
    sl.finish(look_at=Mb @ Vector((0, 0, 0.5)), place=Msl, density=hair(sl))
    hand_w = Msl @ (rope_local + Vector((0, 0, 0.04 * math.sin(t * 6))))
    drop = 0.55 + 0.35 * ease(t)
    sack_top = Mb @ Vector((0.1, 0.0, b["gunwale"] + 1.25 - drop))
    sk = PR.sack("food_sack")
    for o in sk:
        o.matrix_world = Matrix.Translation(sack_top - Vector((0, 0, 0.5 * 1.02))) @ o.matrix_world
    ship.rope("lowering_line", [hand_w, hand_w.lerp(sack_top, 0.5) + Vector((0, 0, -0.03)), sack_top + Vector((0, 0, 0.02))], 0.009,
              ship.tarred_rope("line", (0.32, 0.26, 0.17)))
    # Deveau standing in the boat, hands on the sack
    Mdv = Mb @ crew.place((0.62, 0.25, b["floor_z"]), 160)
    Mi = Mdv.inverted()
    sc = sack_top - Vector((0, 0, 0.28))
    dv = crew.person("deveau", wet=0.2)
    hands = {"L": Mi @ (sc + (Mb.to_3x3() @ Vector((0.0, 0.2, 0)))), "R": Mi @ (sc + (Mb.to_3x3() @ Vector((0.2, -0.05, 0.05))))}
    pose_guide(dv, t, hands)
    dv.finish(look_at=sack_top, place=Mdv, density=hair(dv))
    # his sextant case on the after thwart
    cs = PR.sextant_case("dv_case")
    xth, zth = b["thwarts"][0]
    for o in cs:
        o.matrix_world = Mb @ Matrix.Translation((xth, 0.25, zth + 0.02)) @ Matrix.Rotation(0.3, 4, 'Z') @ o.matrix_world
    loc = Mb @ Vector((-1.7, 0.55, b["gunwale"] + 0.8 + 0.04 * math.sin(t * 2.5)))
    tgt = eyes(dv).lerp(eyes(sl), 0.45)
    cam(loc, tgt, lens=28, fstop=4.0, focus=(eyes(dv) - loc).length)
    return dict(cine={"sat": 1.08})


@shot("p3_06", "He brings two sailors, his own navigation instruments, and food from his ship.", "OTS insert · 50mm", 2.4,
      "In the boat: Deveau sets his own sextant case down on the thwart beside him", "Wood on wood, brass handle clicks")
def s06(t):
    SHIP = dg_deck(t=0.5, mc_far=False)
    b, Mb = boat_alongside(SHIP, t=0.4 + t * 0.3)
    xth, zth = b["thwarts"][1]
    dv = crew.person("deveau", wet=0.2, seated=True)
    h = dv.h
    drop = crew.hip_height(h) - 0.1
    seat = zth + 0.075
    Mdv = Mb @ crew.place((xth, -0.12, seat), 180, drop=drop)
    crew.sit(h, drop - seat + b["floor_z"], lean=24, feet_fwd=0.42)
    Mi = Mdv.inverted()
    # the case is set down on the thwart at his right (boat +Y side)
    case_pos = Mb @ Vector((xth, 0.38, seat + 0.05 * (1 - ease(t))))
    P.head(h, pitch=34, yaw=-28, tilt=-4)
    hp = Mi @ (case_pos + Vector((0, 0, 0.17 + 0.012)))
    P.hand_reach(h, "R", hp, elbow=(-0.8, 0.3, -0.4))
    h.aim("wrist.R", Vector((-0.2, -0.2, -1))); P.grip(h, "R", 0.85)
    knee = h.bone_tail("upperleg02.L")
    P.hand_reach(h, "L", knee + Vector((0.0, -0.05, 0.08)), elbow=(0.7, 0.3, -0.5))
    h.aim("wrist.L", Vector((0.1, -1, -0.4))); P.rest_hand(h, "L", curl=35)
    dv.lids(0.6)
    dv.finish(look_at=case_pos + Vector((0, 0, 0.15)), place=Mdv, density=hair(dv))
    cs = PR.sextant_case("dv_case")
    for o in cs:
        o.matrix_world = Matrix.Translation(case_pos) @ Mb.to_3x3().to_4x4() @ Matrix.Rotation(math.radians(90), 4, 'Z') @ o.matrix_world
    ed = eyes(dv)
    loc = case_pos + (Mb.to_3x3() @ Vector((-0.95, 0.75, 0.55)))
    cam(loc, case_pos.lerp(ed, 0.5), lens=40, fstop=2.8, focus=(case_pos - loc).length)
    return dict(cine={"sat": 1.08})


# ============================================================================ ON THE MARY CELESTE: PUMPS AND SAIL
MC_HEAD = 75.0


def mc_deck(mood="day", t=0.0, sails="spare", heel=4.0, sun_az=210, sun_el=20, wet=0.6, sea_kw=None):
    ST.exterior(mood, sky_rot=40, sun_az=sun_az, sun_el=sun_el)
    m = ST.mc(sails, wind=ST.local_wind(WIND, MC_HEAD), wet=wet, detail=True, gap=True)
    SHIP = ST.set_ship(m, heading=MC_HEAD, heel=heel + 0.8 * math.sin(t * 2.0), pitch=0.5 * math.sin(t * 1.6 + 0.4))
    kw = dict(mood=mood, size=240, time=11 + t * 3.0, cut=(0.0, 0.0, ship.L / 2 - 0.4, ship.B / 2 - 0.15))
    kw.update(sea_kw or {})
    ST.ocean_around((0, -100, 0), hulls=[m["hull"]], **kw)
    return SHIP, m


def pose_pump(p, t, grip_w, M, phase=0.0, up=True):
    h = p.h; Mi = M.inverted()
    s = math.sin(2 * math.pi * (t * 1.2 + phase))
    P.stand(h, lean=18 + 10 * s, weight="L", twist=0)
    P.head(h, pitch=12 + 6 * s, yaw=0)
    for sd, sg in (("L", 1), ("R", -1)):
        hp = Mi @ grip_w[sd]
        P.hand_reach(h, sd, hp, elbow=(0.7 * sg, 0.25, -0.6))
        h.aim(f"wrist.{sd}", Vector((0.0, -0.6, -0.8)))
        P.grip(h, sd, 1.0)
    p.brow_knit(0.6)


def water_gush(name, a, b, width=0.12, mat=None):
    """Bilge water pouring from a pump spout and running across the deck toward the scupper."""
    mat = mat or bpy.data.materials.get("gush")
    if mat is None:
        mat = bpy.data.materials.new("gush"); mat.use_nodes = True; q = mat.node_tree.nodes["Principled BSDF"]
        q.inputs['Base Color'].default_value = (0.45, 0.4, 0.3, 1); q.inputs['Transmission Weight'].default_value = 0.85
        q.inputs['Roughness'].default_value = 0.05; q.inputs['IOR'].default_value = 1.33
    return ship.cyl(name, a, b, width * 0.25, width * 0.6, mat, verts=14)


@shot("p3_07", "They pump out the Mary Celeste", "MS · 35mm", 3.2,
      "Two sailors work the pump brake; water gushes from the spouts across the deck to the scuppers",
      "Pump clank and suck, water gush, scupper gurgle, grunts")
def s07(t):
    SHIP, m = mc_deck(t=t)
    for o in bpy.data.objects:
        if o.name.startswith("MC_pumpbrake"):
            o.hide_render = True
    ang = 14 * math.sin(2 * math.pi * t * 1.2)
    wood = m["mats"]["deckwood"]
    objs, ends, fwd = PR.pump_brake("brake", SHIP, ang, wood)
    men = []
    for i, (key, end, sg) in enumerate((("sailor_a", ends[0], 1), ("sailor_b", ends[1], -1))):
        # each man stands outboard of his end of the brake, facing inboard, hands on the cross handle
        endl = SHIP.inverted() @ end
        M = ST.on_ship(SHIP, endl.x, endl.y + sg * 0.42, -90 * sg)
        grip = {"L": end + fwd * 0.16 * sg, "R": end - fwd * 0.16 * sg}
        p = crew.person(key, wet=0.5, idx=i); pose_pump(p, t, grip, M, phase=0.5 * i)
        p.finish(look_at=end - Vector((0, 0, 0.6)), place=M, density=hair(p))
        men.append(p)
    # spouts and the water running to the starboard scupper
    X = ship.MAIN_X + 0.9; zd = ship.zdeck(ship.MAIN_X)
    for sgy in (1, -1):
        sp = SHIP @ Vector((X + 0.12, sgy * 0.7, zd + 0.85))
        water_gush(f"gush{sgy}", sp, SHIP @ Vector((X + 0.45, sgy * 0.75 - 0.2, zd + 0.02)), 0.11 * (0.7 + 0.3 * abs(math.sin(t * 7.5))))
        sheet = ship.box(f"runoff{sgy}", SHIP @ Vector((X + 0.6, sgy * 0.7 - 1.3, zd + 0.008)), (0.6, 2.4, 0.01), bpy.data.materials["gush"])
        sheet.rotation_euler = SHIP.to_euler()
    loc = ST.deck_world(SHIP, X + 3.6, -0.6, 1.7) + Vector((0.03 * math.sin(t * 5), 0.02 * math.sin(t * 3.3), 0.02 * math.sin(t * 4.1)))
    cam(loc, ST.deck_world(SHIP, X, 0.0, 0.95), lens=26, fstop=4.0)
    return dict(cine={"sat": 1.08})


def pose_sheet(p, t, rope_w, M):
    h = p.h; Mi = M.inverted()
    P.stand(h, lean=-14 + 4 * math.sin(t * 5), weight="R", twist=6)
    P.head(h, pitch=-35, yaw=10)
    for sd, sg, k in (("L", 1, 0.0), ("R", -1, 0.22)):
        hp = Mi @ rope_w(k)
        P.hand_reach(h, sd, hp, elbow=(0.6 * sg, 0.3, -0.7))
        h.aim(f"wrist.{sd}", Vector((0, -0.5, 0.5)))
        P.grip(h, sd, 1.0)
    p.brow_knit(0.5)


@shot("p3_08", "and put up a spare sail in place of one she's lost.", "LOW · 24mm", 3.4,
      "Low on the foredeck, tilting up: Deveau hauls the sheet home and the spare fore course fills",
      "Halyard and block squeal, canvas cracks as it fills")
def s08(t):
    SHIP, m = mc_deck(t=t)
    fx = ship.FORE_X
    hb = ship.half_breadth((fx - 1.2 + ship.L / 2) / ship.L, 1.0)
    pin = ST.deck_world(SHIP, fx - 1.2, -(hb - 0.12), 1.1)
    top = ST.deck_world(SHIP, fx + 0.4, -3.2, 3.0)
    def rope_at(k):
        return pin.lerp(top, 0.35 + k)
    M = ST.on_ship(SHIP, fx - 1.4, -(hb - 0.95), 30)
    dv = crew.person("deveau", wet=0.4); pose_sheet(dv, t, rope_at, M)
    dv.finish(look_at=ST.deck_world(SHIP, fx, -1, 7), place=M, density=hair(dv))
    ship.rope("sheet", [pin, rope_at(0.0), rope_at(0.22), top], 0.013, m["mats"]["rope"])
    loc = ST.deck_world(SHIP, fx - 2.9, -2.55, 0.5)
    tgt = lerp(eyes(dv) + Vector((0, 0, 0.3)), ST.deck_world(SHIP, fx, 0, 7.5), 0.25 + 0.6 * ease(t))
    cam(loc, tgt, lens=24, fstop=5.6, focus=(eyes(dv) - loc).length)
    return dict(cine={"sat": 1.08})


@shot("p3_09", "For the first few days, they make progress.", "EWS · 35mm", 4.0,
      "Low over the water, tracking alongside: the Mary Celeste under her spare course, making way east in warm sun",
      "Bow wash, steady wind, canvas", tag=None)
def s09(t):
    ST.exterior("gold", sky_rot=120, sun_az=240, sun_el=16)
    hd = 95.0
    m = ST.mc("spare", wind=ST.local_wind(WIND, hd), wet=0.4, detail=False)
    SHIP = ST.set_ship(m, loc=(0, 0, 0), heading=hd, heel=6 + 1.0 * math.sin(t * 2), pitch=0.8 * math.sin(t * 1.5))
    # three men aboard, small at the wheel and in the waist
    for i, (x, y, key, hdg) in enumerate(((-ship.L / 2 + 1.0, 0.4, "deveau", 0), (-2.0, -2.6, "sailor_a", 160), (6.0, 2.3, "sailor_b", 200))):
        M = ST.on_ship(SHIP, x, y, hdg)
        p = crew.person(key, wet=0.2, idx=i); P.stand(p.h, lean=4); P.arm_down(p.h, "L"); P.arm_down(p.h, "R")
        if key == "deveau":
            for sd in ("L", "R"):
                P.hand_reach(p.h, sd, Vector((H.SIDE[sd] * 0.2, -0.42, 1.25)), elbow=(0.6 * H.SIDE[sd], 0.3, -0.6)); P.grip(p.h, sd)
        p.finish(place=M, hair=False)
    ST.ocean_around((0, 0, 0), hulls=[m["hull"]], mood="gold", size=260, time=11 + t * 4, chop=1.2, scale=1.3)
    sea.spray("bowspray", SHIP @ Vector((ship.L / 2 - 1.5, -3.0, 0.4)), (0.8, 2.0, 2.5), count=3000, up=1.2,
              dirv=(SHIP.to_3x3() @ Vector((0.2, -1, 0))))
    loc = lerp((-60, -95, 3.0), (-20, -100, 3.2), ease(t))
    cam(Vector(loc), SHIP @ Vector((-2, 0, 6)), lens=35, fstop=None)
    return dict(cine={"sat": 1.1, "exposure": 0.0})


# ============================================================================ THE PASSAGE: MAQUETTE
import terrain as TR

MAQ_BOX = (39.4, -12.5, 35.3, -4.6)          # SW Iberia, Morocco, the Strait (lat_n, lon_w, lat_s, lon_e)
MAQ_ORIGIN = (37.1, -8.55)
MAQ_SCALE = 1.7 / 700000.0                   # 1.7 m wide table maquette
MAQ_VEX = 18.0
GIB = (36.135, -5.35)
ROUTE = [(38.45, -12.2), (38.0, -10.6), (37.3, -9.4), (36.75, -8.0), (36.25, -6.6), (35.98, -5.75), (36.02, -5.52), (36.13, -5.37)]


def maq_xy(lat, lon, table_z):
    x, y = TR.to_xy(lat, lon, MAQ_ORIGIN)
    return Vector((x * MAQ_SCALE, y * MAQ_SCALE, table_z))


def maquette(table_z=0.8):
    """Painted relief model on a chart table: land carved from the real elevation, sea a flat lacquered blue."""
    hm, info = TR.heightmap(*MAQ_BOX, 7)
    land = crew.flat("maq_land", (0.42, 0.33, 0.2), rough=0.75)
    N = land.node_tree.nodes; Lk = land.node_tree.links; p = N["Principled BSDF"]
    geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(geo.outputs['Position'], sep.inputs[0])
    mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = table_z + 0.001; mr.inputs['From Max'].default_value = table_z + 0.04
    Lk.new(sep.outputs['Z'], mr.inputs['Value'])
    cr = N.new("ShaderNodeValToRGB"); el = cr.color_ramp.elements
    el[0].color = (0.30, 0.30, 0.13, 1); el[1].color = (0.62, 0.5, 0.33, 1)
    Lk.new(mr.outputs[0], cr.inputs['Fac']); Lk.new(cr.outputs['Color'], p.inputs['Base Color'])
    o = TR.relief_mesh("maq_relief", hm, info, MAQ_ORIGIN, scale=MAQ_SCALE, vex=MAQ_VEX, res=420, clip_low=-2000, mat=land)
    o.location.z = table_z
    seam = crew.flat("maq_sea", (0.02, 0.09, 0.14), rough=0.6)
    seam.node_tree.nodes["Principled BSDF"].inputs['Coat Weight'].default_value = 0.1
    xw, yn = TR.to_xy(MAQ_BOX[0], MAQ_BOX[1], MAQ_ORIGIN); xe, ys = TR.to_xy(MAQ_BOX[2], MAQ_BOX[3], MAQ_ORIGIN)
    cx, cy = (xw + xe) / 2 * MAQ_SCALE, (yn + ys) / 2 * MAQ_SCALE
    wx, wy = (xe - xw) * MAQ_SCALE, (yn - ys) * MAQ_SCALE
    ship.box("maq_sea", (cx, cy, table_z + 0.0008), (wx, wy, 0.004), seam)
    frame = PR.mat_wood("maq_frame", "dark_wooden_planks", 2.0, tint=(0.75, 0.45, 0.28))
    ship.box("maq_base", (cx, cy, table_z - 0.06), (wx + 0.08, wy + 0.08, 0.1), frame, bevel=0.005)
    for sg in (1, -1):
        ship.box("maq_rim", (cx, cy + sg * (wy / 2 + 0.02), table_z + 0.01), (wx + 0.08, 0.04, 0.04), frame, bevel=0.004)
        ship.box("maq_rim", (cx + sg * (wx / 2 + 0.02), cy, table_z + 0.01), (0.04, wy, 0.04), frame, bevel=0.004)
    return o, (cx, cy, wx, wy)


def route_line(frac, table_z, mat=None):
    pts = [maq_xy(la, lo, table_z + 0.006) for la, lo in ROUTE]
    # resample to the drawn fraction
    seg = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]; tot = sum(seg); want = tot * frac
    out = [pts[0]]; acc = 0.0
    for i, s_ in enumerate(seg):
        if acc + s_ >= want:
            out.append(pts[i].lerp(pts[i + 1], (want - acc) / s_)); break
        out.append(pts[i + 1]); acc += s_
    mat = mat or crew.flat("graphite", (0.06, 0.06, 0.065), rough=0.35, metal=0.3)
    if len(out) >= 2:
        ship.rope("route", out, 0.0035, mat)
    return out[-1]


def lamp_room(center, energy=40.0, key_from=(-0.8, 0.9, 1.4), key=90.0, fill=12.0):
    """Lamplit room: warm overhead key (the lamp's pool), a weak warm bounce, dark walls far off."""
    w = bpy.data.worlds.new("W"); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.09, 0.06, 0.04, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.35
    c = Vector(center)
    for nm, off, en, sz, col in (("key", key_from, key, 0.6, (1.0, 0.7, 0.45)), ("fill", (1.2, -1.4, 0.6), fill, 1.5, (1.0, 0.8, 0.62))):
        L = bpy.data.lights.new(nm, 'AREA'); L.energy = en; L.size = sz; L.color = col
        o = bpy.data.objects.new(nm, L); bpy.context.scene.collection.objects.link(o)
        o.location = c + Vector(off); o.rotation_euler = (c - o.location).to_track_quat('-Z', 'Y').to_euler()
        o.visible_camera = False


@shot("p3_10", "For the first few days, they make progress.", "MAQUETTE · 50mm", 3.4,
      "Over Deveau's shoulder at the chart table: his pencil draws the route east toward Gibraltar on the relief",
      "Pencil on paper, lamp hiss, clock tick")
def s10(t):
    tz = 0.8
    o, (cx, cy, wx, wy) = maquette(tz)
    lamp_room((cx, cy, tz), key=35.0, fill=6.0)
    frac = 0.35 + 0.3 * ease(t)
    tip = route_line(frac, tz)
    PR.dip_pen  # (pen for the letter scene; the route is drawn with a pencil)
    pencil_dir = Vector((0.25, -0.55, 0.8)).normalized()
    pen = [ship.cyl("pencil", tip + Vector((0, 0, 0.003)), tip + pencil_dir * 0.16, 0.0035, 0.004, crew.flat("pencil_w", (0.5, 0.32, 0.1), 0.5), verts=6)]
    # Deveau stands at the near (south) edge, leaning over the table, right hand on the pencil
    dv = crew.person("deveau", wet=0.0)
    h = dv.h
    M = crew.place((tip.x - 0.12, cy - wy / 2 - 0.42, 0.0), 90)
    Mi = M.inverted()
    P.stand(h, lean=34, weight="L", twist=-6)
    P.head(h, pitch=36, yaw=6)
    grip_w = tip + pencil_dir * 0.06
    P.hand_reach(h, "R", Mi @ (grip_w + Vector((0.0, -0.03, 0.03))), elbow=(-0.8, 0.2, -0.5))
    h.aim("wrist.R", Mi.to_3x3() @ Vector((0.1, 0.6, -0.8)))
    P.grip(h, "R", 0.7)
    lp = Vector((tip.x - 0.25, cy - wy / 2 - 0.02, tz + 0.012))
    P.hand_reach(h, "L", Mi @ (lp + Vector((0, 0, 0.04))), elbow=(0.8, 0.3, -0.4))
    h.aim("wrist.L", Mi.to_3x3() @ Vector((0.2, 0.9, -0.5))); P.rest_hand(h, "L", curl=18)
    dv.brow_knit(0.6); dv.lids(0.7)
    dv.finish(look_at=tip, place=M, density=hair(dv))
    PR.table("chart_table", (cx, cy, 0.0), size=(wx + 0.3, wy + 0.3, tz - 0.11))
    lo, fl, lt = PR.oil_lamp("lamp", (cx + wx / 2 + 0.06, cy - wy / 2 + 0.05, tz + 0.01), flame_energy=12)
    key = bpy.data.objects.new("lampkey", bpy.data.lights.new("lampkey", 'POINT')); bpy.context.scene.collection.objects.link(key)
    key.data.energy = 22; key.data.color = (1.0, 0.66, 0.38); key.data.shadow_soft_size = 0.15; key.location = fl + Vector((0, 0, 0.05))
    gib = maq_xy(*GIB, tz + 0.007)
    ST.ripple_bands("gibmark", gib, r0=0.006, r1=0.045, n=3, phase=t * 1.5)
    ed = eyes(dv)
    loc = ed + Vector((0.42, -0.8, 0.38)) + Vector((0.04, 0.0, 0.0)) * ease(t)
    cam(loc, tip.lerp(gib, 0.5), lens=35, fstop=4.0, focus=(tip - loc).length)
    return dict(cine={"sat": 1.12, "exposure": 0.1})


# ============================================================================ THE GALE
def _rim(M, ang, r=0.6):
    """Point on the wheel rim in world, angle measured in the wheel plane (0 = to starboard... the man's right)."""
    R = M.to_3x3()
    # in the rig frame the man faces -Y; his right is -X; the wheel plane is X-Z in his frame
    return R @ Vector((-math.cos(ang) * r, 0.0, math.sin(ang) * r))


def pose_wheel(p, wheel_c, M, t):
    h = p.h; Mi = M.inverted()
    P.stand(h, lean=8, weight="L", twist=0)
    P.head(h, pitch=-4, yaw=0)
    turn = 12 * math.sin(t * 2.4)
    for sd, sg, a in (("L", 1, 118 + turn), ("R", -1, 62 + turn)):
        ang = math.radians(a)
        hp = wheel_c + _rim(M, ang)
        P.hand_reach(h, sd, Mi @ hp, elbow=(0.8 * sg, 0.3, -0.5))
        h.aim(f"wrist.{sd}", Vector((0.15 * sg, -0.75, 0.6)))
        P.grip(h, sd, 1.0)
    p.brow_knit(1.0); p.lids(0.5)


def gale(t, cam_near=True):
    ST.exterior("storm", sky_rot=10)
    cold = bpy.data.objects.new("stormkey", bpy.data.lights.new("stormkey", 'SUN')); bpy.context.scene.collection.objects.link(cold)
    cold.data.energy = 0.5 + (6.0 if 0.42 < t < 0.47 else 0.0); cold.data.color = (0.75, 0.82, 0.95); cold.data.angle = math.radians(25)
    cold.rotation_euler = (math.radians(40), 0, math.radians(30))
    hd = 100.0
    m = ST.mc("spare", wind=ST.local_wind((0.9, -0.4, 0), hd), wet=1.0, detail=True)
    SHIP = ST.set_ship(m, heading=hd, heel=8 + 2.5 * math.sin(t * 2.4), pitch=2.5 * math.sin(t * 1.9 + 0.5))
    ST.ocean_around((0, 0, 0), hulls=[m["hull"]], mood="storm", size=240, scale=1.8, chop=1.9, wind=24, foam=0.75,
                    wind_dir=(0.9, -0.4, 0), time=20 + t * 3, cut=(0.0, 0.0, ship.L / 2 - 0.4, ship.B / 2 - 0.15))
    sea.haze((0, 0, 30), (700, 700, 60), density=0.004, color=(0.45, 0.5, 0.55))
    return SHIP, m


@shot("p3_11", "Then a gale catches them near the Strait of Gibraltar.", "WS · 24mm", 3.6,
      "Handheld on deck: she heels hard into the gale; a sea comes over the rail, rain lashing", "Gale roar, rain, timbers groan, sea over the deck")
def s11(t):
    SHIP, m = gale(t)
    ST.rain("rain", SHIP @ Vector((-4, 0, 6)), (30, 20, 14), count=int(E("RAIN", "40000")))
    sea.spray("greenwater", SHIP @ Vector((2.0, -3.6, 2.2)), (2.5, 3.0, 1.0), count=9000, rmax=0.008, up=2.2, dirv=(SHIP.to_3x3() @ Vector((0, 1, 0.2))))
    sea.mist_puff("spraymist", SHIP @ Vector((1.0, -4.0, 2.6)), (3.0, 2.0, 1.4), density=0.18, seed=t)
    loc = ST.deck_world(SHIP, -6.4, 2.2, 2.7) + Vector((0.05 * math.sin(t * 9), 0.04 * math.sin(t * 7), 0.04 * math.sin(t * 11)))
    cam(loc, ST.deck_world(SHIP, 5.0, -2.4, 1.0), lens=24, fstop=None, roll=-4)
    return dict(cine={"sat": 0.95, "exposure": 0.2})


@shot("p3_12", "Then a gale catches them near the Strait of Gibraltar.", "MS · 35mm", 2.6,
      "From behind and to leeward: Deveau at the wheel, soaked, fighting the helm; the bow buries in grey seas", "Rain on wool, wheel strain, wind")
def s12(t):
    SHIP, m = gale(t)
    xw = -ship.L / 2 + 1.7
    wc = SHIP @ Vector((xw, 0, ship.zdeck(xw) + 1.25))
    M = ST.on_ship(SHIP, xw - 0.42, 0.0, 0)
    dv = crew.person("deveau", wet=1.0); pose_wheel(dv, wc, M, t)
    dv.finish(look_at=SHIP @ Vector((10, -2, 3)), place=M, density=hair(dv))
    ed = eyes(dv)
    ST.rain("rain", ed, (8, 8, 5), count=int(E("RAIN", "30000")) // 3, drop_len=0.25)
    loc = SHIP @ Vector((xw - 2.1, -1.5, ship.zdeck(xw) + 1.75)) + Vector((0.02 * math.sin(t * 10), 0, 0.02 * math.sin(t * 8)))
    cam(loc, SHIP @ Vector((xw + 3.0, 0.2, ship.zdeck(xw) + 1.2)), lens=35, fstop=4.0, focus=(ed - loc).length, roll=-5)
    rim = bpy.data.objects.new("rim", bpy.data.lights.new("rim", 'AREA')); bpy.context.scene.collection.objects.link(rim)
    rim.data.energy = 220; rim.data.size = 3; rim.data.color = (0.7, 0.8, 1.0); rim.visible_camera = False
    rim.location = SHIP @ Vector((xw + 3.5, 1.5, ship.zdeck(xw) + 3.0)); rim.rotation_euler = (ed - rim.location).to_track_quat('-Z', 'Y').to_euler()
    return dict(cine={"sat": 0.95, "exposure": 0.3})


# ============================================================================ GIBRALTAR AND THE COASTS
GIB_BAY = (36.135, -5.392)            # a point in the bay ~3.5 km west of the Rock


def gib_land(mood="gold", rock=True, far=True, town_on=True):
    o = []
    if rock:
        o.append(ST.coast("rock", (36.165, -5.372, 36.105, -5.334), 13, GIB_BAY, res=700))
        if town_on:
            hm, info = TR.heightmap(36.152, -5.362, 36.128, -5.348, 13)
            rng = np.random.default_rng(4); pts = []
            for _ in range(160):
                la = rng.uniform(36.13, 36.15); lo = rng.uniform(-5.358, -5.349)
                r = int((info["lat_n"] - la) / (info["lat_n"] - info["lat_s"]) * (hm.shape[0] - 1))
                c = int((lo - info["lon_w"]) / (info["lon_e"] - info["lon_w"]) * (hm.shape[1] - 1))
                zz = hm[min(max(r, 0), hm.shape[0] - 1), min(max(c, 0), hm.shape[1] - 1)]
                if 4 < zz < 70:
                    x, y = TR.to_xy(la, lo, GIB_BAY); pts.append((x, y, zz))
            walls = [crew.flat(f"wall{k}", c_, 0.8) for k, c_ in enumerate(((0.62, 0.55, 0.42), (0.7, 0.62, 0.48), (0.55, 0.42, 0.3), (0.66, 0.6, 0.52)))]
            roof = crew.flat("roof", (0.33, 0.12, 0.07), 0.7)
            ST.town("gibtown", 3, pts, walls, roof, size=(11, 9, 8))
    if far:
        o.append(ST.coast("bayhills", (36.30, -5.60, 36.02, -5.36), 11, GIB_BAY, res=500))
        o.append(ST.coast("africa", (35.95, -5.55, 35.85, -5.25), 11, GIB_BAY, res=300))
    return o


@shot("p3_13", "Deveau can't make the bay.", "POV · 85mm", 2.4,
      "Through the rain from the deck: the Rock faint in the murk, then lost", "Wind roar, rain")
def s13(t):
    ST.exterior("storm", sky_rot=10)
    o = ST.coast("rock", (36.165, -5.372, 36.105, -5.334), 12, (36.11, -5.48), res=400)
    ST.ocean_around((0, 0, 0), mood="storm", size=240, scale=3.0, chop=2.0, wind=24, foam=0.7, time=20 + t * 3)
    sea.haze((4000, 1000, 120), (16000, 16000, 260), density=0.00006 + 0.00012 * ease(t), color=(0.42, 0.46, 0.5))
    ST.rain("rain", (0, 0, 3), (20, 20, 8), count=20000)
    rx, ry = TR.to_xy(36.135, -5.345, (36.11, -5.48))
    cam((0, 0, 3.2 + 0.4 * math.sin(t * 3)), (rx, ry, 180), lens=85, roll=3 * math.sin(t * 2))
    return dict(cine={"sat": 0.9, "exposure": 0.3})


@shot("p3_14", "He shelters off the North African coast,", "WS · 35mm", 3.0,
      "Dusk after the storm: she lies hove-to in the lee of the African mountains", "Quieter sea, chain, gulls")
def s14(t):
    org = (35.955, -5.40)
    ST.exterior("dusk", sky_rot=200, sun_az=250, sun_el=3)
    ST.coast("africa", (35.93, -5.52, 35.80, -5.28), 12, org, res=600)
    hd = 260.0
    m = ST.mc("spare", wind=ST.local_wind((0.3, 1.0, 0), hd), wet=0.8, detail=False)
    SHIP = ST.set_ship(m, loc=(0, 0, 0), heading=hd, heel=2 + 0.5 * math.sin(t * 2), pitch=0.4 * math.sin(t * 1.4))
    ST.ocean_around((0, 0, 0), hulls=[m["hull"]], mood="dusk", size=240, scale=1.0, chop=1.0, wind=8, foam=0.15, time=11 + t * 3)
    sea.haze((0, -3000, 100), (12000, 12000, 220), density=0.00012, color=(0.6, 0.5, 0.55))
    loc = lerp((-25, 85, 4.5), (-15, 88, 4.5), ease(t))
    cam(Vector(loc), (0, -900, 140), lens=35)
    return dict(cine={"sat": 1.12, "exposure": 0.25})


@shot("p3_15", "then off Spain.", "WS · 35mm", 2.6,
      "Grey morning off the Spanish shore: she rides at anchor under the hills", "Gulls return, swell, chain")
def s15(t):
    org = (35.985, -5.56)
    ST.exterior("day", sky_rot=80, sun_az=110, sun_el=9)
    ST.coast("spain", (36.14, -5.72, 36.0, -5.40), 12, org, res=600)
    hd = 200.0
    m = ST.mc("found", wind=ST.local_wind((0.3, -1.0, 0), hd), wet=0.7, detail=False)
    SHIP = ST.set_ship(m, loc=(0, 0, 0), heading=hd, heel=1.5, pitch=0.3 * math.sin(t * 1.4))
    ST.ocean_around((0, 0, 0), hulls=[m["hull"]], mood="day", size=240, scale=1.1, chop=1.1, wind=9, foam=0.15, time=11 + t * 3)
    sea.haze((0, 3000, 100), (12000, 12000, 220), density=0.00005, color=(0.7, 0.66, 0.62))
    loc = lerp((30, -95, 4.0), (22, -96, 4.0), ease(t))
    cam(Vector(loc), (0, 900, 120), lens=35)
    return dict(cine={"sat": 1.05, "exposure": 0.15})


@shot("p3_16", "By the time he finally brings the ship in on December thirteenth, the Dei Gratia is already there.", "EWS · 24mm", 5.0,
      "Crane down over Gibraltar Bay: the Mary Celeste sails in under the Rock; the Dei Gratia already at anchor",
      "Harbour bells, gulls, anchor chain", card=("l", "GIBRALTAR", "British territory · 1872"), tag="DECEMBER 13, 1872")
def s16(t):
    ST.exterior("gold", sky_rot=160, sun_az=215, sun_el=24)
    gib_land()
    rx, ry = TR.to_xy(36.135, -5.36, GIB_BAY)
    d = ST.dg("bare" if False else "full", wind=ST.local_wind(WIND, 30), detail=False)
    for o in bpy.data.objects:
        if o.name.startswith("DG_sail"):
            o.hide_render = True                 # at anchor: sails furled (yards bare)
    ST.set_ship(d, loc=(rx - 700, ry + 350, 0), heading=30, heel=0.5)
    m = ST.mc("spare", wind=ST.local_wind(WIND, 70), wet=0.4, detail=False)
    SHIP = ST.set_ship(m, loc=(rx - 1500 + 120 * t, ry - 300 + 40 * t, 0), heading=70, heel=4)
    ST.ocean_around((rx - 1300, ry - 100, 0), hulls=[m["hull"], d["hull"]], mood="gold", size=400, scale=0.8, chop=1.0, wind=7, foam=0.1, time=11 + t * 4)
    sea.haze((rx - 1500, ry, 150), (9000, 9000, 300), density=0.00008, color=(0.75, 0.68, 0.6))
    mcp = SHIP.translation
    loc = lerp(mcp + Vector((-260, -170, 70)), mcp + Vector((-150, -110, 9)), ease(t))
    cam(Vector(loc), lerp(Vector((rx, ry, 200)), mcp + Vector((60, 30, 8)), 0.25 + 0.5 * ease(t)), lens=30)
    return dict(cine={"sat": 1.12, "exposure": 0.0})


@shot("p3_17", "the Dei Gratia is already there.", "MS · 50mm", 2.6,
      "Morehouse at the Dei Gratia's rail, at anchor, watches her come in; the Rock behind him", "Gulls, halyards tapping")
def s17(t):
    ST.exterior("gold", sky_rot=160, sun_az=215, sun_el=24)
    gib_land(town_on=True)
    rx, ry = TR.to_xy(36.135, -5.36, GIB_BAY)
    d = ST.dg("full", wind=ST.local_wind(WIND, 30), detail=True)
    for o in bpy.data.objects:
        if o.name.startswith("DG_sail"):
            o.hide_render = True
    loc0 = Vector((rx - 700, ry + 350, 0))
    SHIP = ST.set_ship(d, loc=loc0, heading=90, heel=0.5 + 0.3 * math.sin(t * 2))
    ST.ocean_around(loc0, hulls=[d["hull"]], mood="gold", size=240, scale=0.8, chop=1.0, wind=7, foam=0.1, time=11 + t * 3)
    x = -4.0; hb = ship.half_breadth((x + ship.L / 2) / ship.L, 1.0)
    M = ST.on_ship(SHIP, x, (hb - 0.45), 90)
    mo = crew.person("morehouse", wet=0.0)
    h = mo.h; P.stand(h, lean=4, weight="R"); P.head(h, pitch=-2, yaw=8 - 10 * ease(t))
    for sd in ("L", "R"):
        sg = H.SIDE[sd]
        P.hand_reach(h, sd, Vector((sg * 0.22, -0.4, 0.98)), elbow=(0.7 * sg, 0.4, -0.5)); h.aim(f"wrist.{sd}", Vector((0, -1, -0.3))); P.rest_hand(h, sd, 40)
    mo.lids(0.25)
    target = loc0 + Vector((-900, -300, 5))
    mo.finish(look_at=target, place=M, density=hair(mo))
    em = eyes(mo)
    camloc = em + Vector((-2.4, -0.9, -0.2))
    cam(camloc, em + Vector((0, 0, -0.15)) + Vector((0, 0.45, 0)), lens=50, fstop=4.0, focus=(em - camloc).length)
    return dict(cine={"sat": 1.1})


# ============================================================================ THE LETTER HOME (14 DEC)
import rooms as RM
TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "tex")


def seated_writer(room, t, pen_lift=0.0, rub=0.0):
    """Deveau on the cabin chair at the table: right hand writing, left forearm on the table; or (rub > 0)
    the heel of his right hand pressed to his eyes."""
    dv = crew.person("deveau", wet=0.0, seated=True)
    h = dv.h
    cx, cy = room["chair"]; tz = room["table_z"]
    seat = 0.45
    drop = crew.hip_height(h) - seat - 0.08
    M = crew.place((cx - 0.08, cy, 0.0), 0, drop=drop)           # facing +X, toward the table
    crew.sit(h, drop, lean=28 - 8 * rub, feet_fwd=0.42)
    Mi = M.inverted()
    paper_c = Vector((cx + 0.62, cy + 0.02, tz + 0.002))
    tip = paper_c + Vector((-0.02 + 0.06 * math.sin(t * 9) * (1 - pen_lift), -0.05 + 0.08 * t, 0.002 + 0.02 * pen_lift))
    P.head(h, pitch=30 - 14 * rub, yaw=4, tilt=2)
    if rub > 0:
        ed0 = Vector((cx + 0.2, cy, 0)) # placeholder: the head pose decides; target the right eye socket after posing
        eye = h.bone_head("eye.R") if "eye.R" in h.arm.pose.bones else h.bone_head("head") + Vector((-0.03, -0.09, 0.04))
        P.hand_reach(h, "R", eye + Vector((0.0, -0.055, -0.035)), elbow=(-0.4, -0.2, -1.0))
        h.aim("wrist.R", Vector((0.25, 0.25, 1)))
        P.rest_hand(h, "R", curl=35)
    else:
        P.hand_reach(h, "R", Mi @ (tip + Vector((0.0, -0.02, 0.05))), elbow=(-0.8, 0.3, -0.5))
        h.aim("wrist.R", Mi.to_3x3() @ Vector((0.6, 0.1, -0.75)))
        P.grip(h, "R", 0.6)
    lp = Vector((cx + 0.5, cy + 0.24, tz + 0.03))
    P.hand_reach(h, "L", Mi @ lp, elbow=(0.8, 0.2, -0.4))
    h.aim("wrist.L", Mi.to_3x3() @ Vector((0.8, -0.3, -0.25))); P.rest_hand(h, "L", curl=25)
    dv.lids(0.75 if rub == 0 else 1.0); dv.brow_knit(0.5)
    dv.finish(look_at=tip, place=M, density=hair(dv))
    PR.paper("letter", paper_c, size=(0.21, 0.27), rot_z=math.radians(-80), text_img=os.path.join(TEX, "letter.png"))
    PR.inkwell("ink", (cx + 0.82, cy - 0.22, tz))
    pen_dir = Vector((-0.35, -0.45, 0.82))
    if rub == 0:
        PR.dip_pen("pen", tip, pen_dir)
    else:
        PR.dip_pen("pen", Vector((cx + 0.7, cy - 0.12, tz + 0.006)), Vector((-0.5, 0.86, 0.04)))
    return dv, M, tip


@shot("p3_18", "The next day, he writes to his wife about how exhausted he is.", "MS · 50mm", 3.6,
      "Deveau writing a letter at the cabin table, slumped; daylight from the port, lamp beside him",
      "Pen scratch, chair creak, a long breath, harbour gulls outside")
def s18(t):
    room = RM.cabin_letter()
    dv, M, tip = seated_writer(room, t)
    ed = eyes(dv)
    loc = lerp((1.2, -1.15, 1.32), (1.08, -1.02, 1.3), ease(t))
    cam(Vector(loc), ed.lerp(tip, 0.4), lens=40, fstop=2.8, focus=(ed - Vector(loc)).length)
    return dict(cine={"sat": 1.12, "exposure": 0.15})


@shot("p3_19", "He says he wouldn't take on the job again.", "MS · 40mm", 2.8,
      "Side-lit by the port: he sits back from the letter and presses the heel of his hand to his eyes, face in shadow", "Long exhale, chair creak")
def s19(t):
    room = RM.cabin_letter()
    dv, M, tip = seated_writer(room, 0.5, rub=0.3 + 0.7 * ease(min(1, t * 1.5)))
    ed = eyes(dv)
    loc = ed + Vector((0.55, 1.15, -0.05))
    cam(loc, ed + Vector((0.15, 0, -0.3)), lens=40, fstop=2.8, focus=(ed - loc).length)
    return dict(cine={"sat": 1.1, "exposure": 0.05})


@shot("p3_20", "He also asks whether his little boy, James, can talk yet.", "OTS insert · 50mm", 3.4,
      "Over his shoulder: the pen pauses above the letter; he writes again, slowly", "Pen lifts, pause, pen scratch")
def s20(t):
    room = RM.cabin_letter()
    lift = 1.0 - ease(max(0, (t - 0.5) * 2))
    dv, M, tip = seated_writer(room, 0.6 + 0.2 * t, pen_lift=lift)
    ed = eyes(dv)
    loc = ed + Vector((-0.32, -0.35, 0.22))
    cam(loc, tip + Vector((0.0, 0.03, 0.0)), lens=50, fstop=2.8, focus=(tip - loc).length)
    return dict(cine={"sat": 1.12, "exposure": 0.15})


# ============================================================================ GIBRALTAR: SEIZURE AND THE COURT
def mc_at_gib(t=0.0, mood="gold", heel=0.4, detail=True, crew_on=()):
    ST.exterior(mood, sky_rot=160, sun_az=215, sun_el=22)
    gib_land(town_on=True, far=False)
    rx, ry = TR.to_xy(36.135, -5.36, GIB_BAY)
    m = ST.mc("spare", wind=ST.local_wind(WIND, 90), wet=0.2, detail=detail)
    for o in bpy.data.objects:
        if o.name.startswith("MC_sail") and "spare" not in o.name:
            pass
    loc0 = Vector((rx - 900, ry - 150, 0))
    SHIP = ST.set_ship(m, loc=loc0, heading=180, heel=heel + 0.25 * math.sin(t * 2), pitch=0.2 * math.sin(t * 1.5))
    ST.ocean_around(loc0, hulls=[m["hull"]], mood=mood, size=200, scale=0.7, chop=0.9, wind=6, foam=0.05, time=11 + t * 3,
                    cut=(loc0.x, loc0.y, ship.L / 2 - 0.4, ship.B / 2 - 0.15))
    return SHIP, m


def stand_pose(p, lean=3, weight="L", yaw=0.0, pitch=0.0, hands="down"):
    h = p.h
    P.stand(h, lean=lean, weight=weight); P.head(h, pitch=pitch, yaw=yaw)
    if hands == "down":
        P.arm_down(h, "L", bend=16); P.arm_down(h, "R", bend=16); P.rest_hand(h, "L", 26); P.rest_hand(h, "R", 26)
    elif hands == "behind":
        for sd in ("L", "R"):
            sg = H.SIDE[sd]
            P.hand_reach(h, sd, Vector((0.02 * sg, 0.16, 0.98)), elbow=(0.6 * sg, 0.5, -0.4)); P.rest_hand(h, sd, 40)


def point_hand(h, side):
    sg = H.SIDE[side]
    for f in (3, 4, 5):
        for k in (1, 2, 3):
            h.rot(f"finger{f}-{k}.{side}", (1, 0, 0), 70 if k == 1 else 80)
    h.rot(f"finger1-2.{side}", (0, 0, sg), 25)


@shot("p3_21", "At Gibraltar, the authorities seize the Mary Celeste", "WS · 35mm", 3.4,
      "The Admiralty marshal and an officer stand on the Mary Celeste's deck at anchor; the Rock behind",
      "Boat bumps the side, boots on deck, gulls")
def s21(t):
    SHIP, m = mc_at_gib(t)
    ppl = []
    for i, (key, x, y, hdg) in enumerate((("surveyor", -3.3, -2.8, 10), ("captain2", -4.2, -1.9, -20))):
        M = ST.on_ship(SHIP, x, y, hdg)
        p = crew.person(key, wet=0.0, idx=i); stand_pose(p, hands="behind" if i == 0 else "down", yaw=-10 + 20 * ease(t) if i == 0 else 0)
        p.finish(look_at=ST.deck_world(SHIP, -6, 0, 3), place=M, density=hair(p))
        crew.top_hat(p)
        ppl.append(p)
    loc = ST.deck_world(SHIP, 4.2, -2.75, 1.55)
    cam(lerp(loc, loc + Vector((0, 0, 0.1)), ease(t)), ST.deck_world(SHIP, -2.7, -2.4, 1.75), lens=35, fstop=5.6)
    return dict(cine={"sat": 1.1})


@shot("p3_22", "At Gibraltar, the authorities seize the Mary Celeste", "CU · 50mm", 2.6,
      "The marshal (face in frame) nails the arrest warrant to the mainmast", "Hammer blows on wood")
def s22(t):
    SHIP, m = mc_at_gib(t)
    mast = ST.deck_world(SHIP, ship.MAIN_X, 0, 1.55)
    fwd = SHIP.to_3x3() @ Vector((1, 0, 0)); side = SHIP.to_3x3() @ Vector((0, -1, 0))
    face_n = side.normalized()
    note_c = mast + face_n * 0.17
    PR.notice("warrant", note_c, face_n, text_img=os.path.join(TEX, "warrant.png"))
    M = ST.on_ship(SHIP, ship.MAIN_X - 0.35, -0.95, 75)
    p = crew.person("captain2", wet=0.0)
    h = p.h; Mi = M.inverted()
    P.stand(h, lean=6, weight="L"); P.head(h, pitch=8, yaw=6)
    lh = note_c + fwd * -0.1 + Vector((0, 0, 0.17)) + face_n * 0.03
    P.hand_reach(h, "L", Mi @ lh, elbow=(0.7, 0.3, -0.6)); h.aim("wrist.L", Mi.to_3x3() @ (-face_n + Vector((0, 0, 0.3)))); P.rest_hand(h, "L", 12)
    swing = math.sin(t * math.pi * 5) ** 2           # 0 = the blow lands, 1 = hammer raised
    nail = note_c + fwd * 0.11 + Vector((0, 0, 0.16))
    up = Vector((0, 0, 1))
    head = nail + face_n * (0.035 + 0.12 * swing) + up * (0.22 * swing)
    hd = (face_n * 0.95 - up * (0.15 + 0.6 * swing)).normalized()
    hand = head + hd * 0.26
    P.hand_reach(h, "R", Mi @ hand, elbow=(-0.8, 0.2, -0.6))
    h.aim("wrist.R", Mi.to_3x3() @ (-hd + up * 0.2)); P.grip(h, "R", 1.0)
    p.brow_knit(0.4)
    p.finish(look_at=nail, place=M, density=hair(p))
    crew.top_hat(p)
    PR.hammer("hammer", head, hd, -face_n)
    em = eyes(p)
    loc = note_c + face_n * 0.9 + fwd * 1.7 + Vector((0, 0, 0.05))
    cam(loc, note_c.lerp(em, 0.5), lens=50, fstop=3.5, focus=(note_c - loc).length)
    return dict(cine={"sat": 1.1})


def court_people(ct, which, t=0.0):
    out = {}
    if "salvors" in which:
        for i, (key, dx) in enumerate((("deveau", -0.6), ("sailor_a", 0.1), ("sailor_b", 0.8))):
            px, py = ct["pews"][0]
            p = crew.person(key, wet=0.0, idx=i, seated=True)
            h = p.h; seat = 0.47; drop = crew.hip_height(h) - seat - 0.08
            M = crew.place((px + dx, py + 0.05, 0.0), 90, drop=drop)
            crew.sit(h, drop, lean=6, feet_fwd=0.45)
            for sd in ("L", "R"):
                sg = H.SIDE[sd]; knee = h.bone_tail(f"upperleg02.{sd}")
                P.hand_reach(h, sd, knee + Vector((0, -0.04, 0.07)), elbow=(0.7 * sg, 0.3, -0.5)); h.aim(f"wrist.{sd}", Vector((0, -1, -0.5))); P.rest_hand(h, sd, 30)
            P.head(h, pitch=-2, yaw=-15 if key == "deveau" else 0)
            p.finish(look_at=(3.2, 7.2, 1.9), place=M, density=hair(p))
            out[key] = (p, M)
    if "flood" in which:
        p = crew.person("flood", wet=0.0, wig=True)
        h = p.h; Mi = None
        rise = which["flood"]
        cxl, cyl = ct["counsel"]
        M = crew.place((cxl - 0.6, cyl - 0.75, 0.0), 90, drop=0.0)
        P.stand(h, lean=24 * (1 - rise) + 6, weight="L"); P.head(h, pitch=-6 + 10 * (1 - rise), yaw=-28)
        for sd in ("L", "R"):
            sg = H.SIDE[sd]
            P.hand_reach(h, sd, (M.inverted() @ Vector((cxl - 0.6 - 0.22 * sg, cyl - 0.33, 0.82))), elbow=(0.7 * sg, 0.3, -0.5))
            h.aim(f"wrist.{sd}", Vector((0, -1, -0.7))); P.rest_hand(h, sd, 15)
        p.brow_knit(0.9); p.lids(0.35)
        p.finish(look_at=(3.2, 7.2, 1.85), place=M, density=hair(p))
        crew.bands(p)
        out["flood"] = (p, M)
    if "witness" in which:
        wx, wy = ct["witness"]
        p = crew.person("deveau", wet=0.0, idx=5)
        h = p.h
        M = crew.place((wx + 0.12, wy, 0.4), 180, drop=0.0)
        P.stand(h, lean=4, weight="R"); P.head(h, pitch=2, yaw=8)
        for sd in ("L", "R"):
            sg = H.SIDE[sd]
            P.hand_reach(h, sd, M.inverted() @ Vector((wx - 0.6, wy - sg * 0.2, 1.57)), elbow=(0.7 * sg, 0.3, -0.5))
            h.aim(f"wrist.{sd}", Vector((0, -1, -0.6))); P.rest_hand(h, sd, 30)
        p.finish(look_at=(-1.2, 4.4, 1.6), place=M, density=hair(p))
        out["witness"] = (p, M)
    if "clerk" in which:
        cx_, cy_ = ct["clerk"]
        p = crew.person("chemist", wet=0.0, idx=7, seated=True)
        h = p.h; seat = 0.46; drop = crew.hip_height(h) - seat - 0.08
        PR.chair("clerk_chair", (cx_, cy_ + 0.82, 0.0), 90)
        M = crew.place((cx_, cy_ + 0.75, 0.0), -90, drop=drop)
        crew.sit(h, drop, lean=26, feet_fwd=0.4)
        tip = Vector((cx_ + 0.05 * math.sin(t * 8), cy_ + 0.05, 0.762))
        P.hand_reach(h, "R", M.inverted() @ (tip + Vector((0.02, 0.03, 0.05))), elbow=(-0.8, 0.3, -0.5)); P.grip(h, "R", 0.6)
        P.hand_reach(h, "L", M.inverted() @ Vector((cx_ + 0.3, cy_ + 0.1, 0.79)), elbow=(0.8, 0.3, -0.4)); P.rest_hand(h, "L", 20)
        P.head(h, pitch=32)
        p.finish(look_at=tip, place=M, density=hair(p))
        PR.paper("clerk_paper", (cx_, cy_ + 0.02, 0.762), size=(0.21, 0.29), rot_z=0.1, text_img=os.path.join(TEX, "papers.png"))
        PR.dip_pen("clerk_pen", tip, Vector((0.3, 0.4, 0.85)))
        out["clerk"] = (p, M)
    if "judge" in which:
        jx, jy, jz = ct["judge"]
        p = crew.person("judge", wet=0.0, wig=True, idx=8, seated=True)
        p.jacket.data.materials[0] = crew.flat("judge_robe", (0.28, 0.03, 0.025), rough=0.8)
        h = p.h; drop = crew.hip_height(h) - 0.78 - 0.08
        M = crew.place((jx, jy, jz), -90, drop=drop)
        crew.sit(h, drop, lean=10, feet_fwd=0.4)
        for sd in ("L", "R"):
            sg = H.SIDE[sd]
            P.hand_reach(h, sd, M.inverted() @ Vector((jx + 0.13 * sg, jy - 0.6, 1.88)), elbow=(0.7 * sg, 0.3, -0.5)); P.grip(h, sd, 0.4)
        P.head(h, pitch=24)
        p.finish(look_at=(jx, jy - 0.65, 1.8), place=M, density=hair(p))
        PR.paper("award", (jx, jy - 0.66, 1.80), size=(0.22, 0.3), rot_z=0.0, text_img=os.path.join(TEX, "warrant.png"))
        out["judge"] = (p, M)
    return out


@shot("p3_23", "while a court decides what to pay the men who saved her.", "WS · 24mm", 3.6,
      "The Vice-Admiralty Court: Deveau and his two men on the salvors' bench; sun through the tall windows",
      "Room tone, rustle, a cough, clock tick")
def s23(t):
    ct = RM.court()
    court_people(ct, {"salvors": 1, "clerk": 1}, t)
    loc = lerp((3.6, 1.0, 2.2), (3.3, 1.2, 2.15), ease(t))
    cam(Vector(loc), (-1.5, 6.5, 1.5), lens=24, fstop=None)
    return dict(cine={"sat": 1.12, "exposure": 0.1}, card=None)


@shot("p3_24", "Deveau and the crew stand to earn a share of the value they brought into port.", "MS · 50mm", 3.8,
      "Deveau on the bench, hands on his knees, watching the court; his men beside him", "Quill scratch, murmur")
def s24(t):
    ct = RM.court()
    ppl = court_people(ct, {"salvors": 1}, t)
    p, M = ppl["deveau"]
    ed = eyes(p)
    loc = ed + Vector((2.6, 0.9, 0.05))
    cam(lerp(loc, loc + Vector((-0.1, -0.15, 0)), ease(t)), ed + Vector((0.3, 0, -0.35)), lens=40, fstop=2.8, focus=(ed - loc).length)
    return dict(cine={"sat": 1.12, "exposure": 0.1})


@shot("p3_25", "That gives the court a reason to go through their story in detail.", "MS · 50mm", 3.4,
      "Deveau in the witness box gives his evidence; the clerk writes it down", "Quill scratch, Deveau's voice under (no lip-sync)")
def s25(t):
    ct = RM.court()
    ppl = court_people(ct, {"witness": 1, "clerk": 1}, t)
    p, M = ppl["witness"]
    ed = eyes(p)
    loc = Vector((0.4, 5.8, 1.75))
    cam(lerp(loc, loc + Vector((0.12, 0.0, 0.0)), ease(t)), ed + Vector((0, -0.6, -0.35)), lens=45, fstop=3.2, focus=(ed - loc).length)
    return dict(cine={"sat": 1.12, "exposure": 0.1})


@shot("p3_26", "It also gives Gibraltar's attorney general, Frederick Solly Flood, a question to pursue.", "LOW MS · 35mm", 4.4,
      "Flood rises from the counsel's table, hands on the cloth, and turns to the witness box",
      "Chair scrape, robe rustle", card=("r", "FREDERICK SOLLY FLOOD", "Attorney General, Gibraltar"))
def s26(t):
    ct = RM.court()
    ppl = court_people(ct, {"flood": ease(t)}, t)
    p, M = ppl["flood"]
    ef = eyes(p)
    loc = ef + Vector((1.9, 1.9, -0.8)) + Vector((-0.05, -0.12, 0.0)) * ease(t)
    cam(loc, ef + Vector((0, 0, -0.45)), lens=28, fstop=2.8, focus=(ef - loc).length)
    return dict(cine={"sat": 1.12, "exposure": 0.1})


@shot("p3_27", "Could the men who found the ship know more than they're saying?", "OTS · 50mm", 2.4,
      "Over Flood's wigged shoulder: Deveau in the witness box, across the court", "Clock tick, the room falls quiet")
def s27(t):
    ct = RM.court()
    ppl = court_people(ct, {"flood": 1.0, "witness": 1}, t)
    p, M = ppl["flood"]; w, Mw = ppl["witness"]
    ef = eyes(p); ew = eyes(w)
    d = (ew - ef).normalized(); side = d.cross(Vector((0, 0, 1))).normalized()
    loc = ef - d * (0.75 - 0.1 * ease(t)) - side * 0.28 + Vector((0, 0, 0.06))
    cam(loc, ew + Vector((0, 0, -0.2)), lens=50, fstop=2.8, focus=(ew - loc).length)
    return dict(cine={"sat": 1.1, "exposure": 0.05})


@shot("p3_28", "Could the men who found the ship know more than they're saying?", "OTS · 50mm", 2.2,
      "Reverse over Deveau's shoulder from the box: Flood waits at the counsel's table, side-lit by the windows", "Clock tick")
def s28(t):
    ct = RM.court()
    ppl = court_people(ct, {"flood": 1.0, "witness": 1}, t)
    p, M = ppl["flood"]; w, Mw = ppl["witness"]
    ef = eyes(p); ew = eyes(w)
    d = (ef - ew).normalized(); side = d.cross(Vector((0, 0, 1))).normalized()
    loc = ew - d * 0.7 + side * 0.3 + Vector((0, 0, 0.05))
    cam(loc, ef + Vector((0, 0, -0.25)), lens=50, fstop=2.8, focus=(ef - loc).length)
    return dict(cine={"sat": 1.1, "exposure": 0.05})


# ============================================================================ THE INSPECTION
@shot("p3_29", "Flood has the vessel inspected.", "WS · 35mm", 3.0,
      "On the Mary Celeste's deck Flood points out the rail and hatches to the surveyor (arm with his body)", "Gulls, harbour, boots")
def s29(t):
    SHIP, m = mc_at_gib(t)
    Mf = ST.on_ship(SHIP, -0.9, -2.2, -150)
    fl = crew.person("flood", wet=0.0)
    h = fl.h; P.stand(h, lean=2, weight="L", twist=-6); P.head(h, pitch=4, yaw=-10)
    target = ST.deck_world(SHIP, -2.7, -3.6, 0.9)
    Mi = Mf.inverted()
    sh_ = Mf @ h.bone_head("upperarm01.R")
    hand = sh_ + (target - sh_).normalized() * 0.58
    P.hand_reach(h, "R", Mi @ hand, elbow=(-0.6, 0.4, -0.5)); h.aim("wrist.R", Mi.to_3x3() @ (target - sh_).normalized())
    point_hand(h, "R")
    P.arm_down(h, "L", bend=18); P.rest_hand(h, "L", 30)
    fl.finish(look_at=target, place=Mf, density=hair(fl))
    crew.top_hat(fl)
    Ms = ST.on_ship(SHIP, 0.1, -2.35, -165)
    sv = crew.person("surveyor", wet=0.0, idx=1)
    h2 = sv.h; P.stand(h2, lean=4, weight="R"); P.head(h2, pitch=10, yaw=12)
    nb = Ms @ Vector((0.05, -0.3, 1.1))
    for sd in ("L", "R"):
        sg = H.SIDE[sd]
        P.hand_reach(h2, sd, Vector((0.08 * sg, -0.3, 1.08)), elbow=(0.6 * sg, 0.4, -0.5)); h2.aim(f"wrist.{sd}", Vector((-0.3 * sg, -0.7, 0.4))); P.grip(h2, sd, 0.5)
    sv.finish(look_at=target, place=Ms, density=hair(sv))
    crew.top_hat(sv)
    PR.paper("notebook", nb, size=(0.1, 0.16), rot_z=0)
    loc = ST.deck_world(SHIP, -5.6, -2.9, 1.6)
    cam(lerp(loc, loc + (SHIP.to_3x3() @ Vector((0.4, 0, 0))), ease(t)), ST.deck_world(SHIP, -1.2, -2.3, 1.35), lens=35, fstop=5.6)
    return dict(cine={"sat": 1.1})


def diver_scene(t, depth=5.4):
    RM.underwater(depth)
    m = ST.mc("found", wind=(0.3, -1, 0), wet=1.0, detail=False, gap=False)
    for o in bpy.data.objects:
        if o.name.startswith(("MC_sail", "MC_rig", "MC_shroud")):
            o.hide_render = True
    SHIP = ST.set_ship(m, heading=0, heel=0.3)
    dv = crew.person("diver", wet=1.0)
    return SHIP, m, dv


@shot("p3_29b", "A diver goes under her and checks the hull for damage.", "UNDERWATER · 24mm", 3.6,
      "Under the hull: the helmet diver walks along the sand, one glove on the planking above him", "Air-pump hiss, bubbles, muffled water")
def s29b(t):
    SHIP, m, dv = diver_scene(t)
    h = dv.h
    bed = -5.4
    x = -4 + 0.8 * t
    M = crew.place((x, -1.9, bed + 0.02), 0)
    Mi = M.inverted()
    P.stand(h, lean=12, weight="L" if t < 0.5 else "R")
    P.head(h, pitch=-30, yaw=20)
    # the hull's bottom planking just above his reach
    hullp = SHIP @ Vector((x + 0.3, -1.3, -2.5))
    P.hand_reach(h, "L", Mi @ (hullp + Vector((0, 0, -0.06))), elbow=(0.7, 0.3, -0.4)); h.aim("wrist.L", Vector((0.2, -0.2, 1))); P.rest_hand(h, "L", 12)
    P.arm_down(h, "R", bend=25); P.rest_hand(h, "R", 30)
    dv.finish(look_at=hullp, place=M, hair=False)
    parts, back = crew.diver_helmet(dv); crew.hide_head(dv)
    ship.rope("airhose", [back, back + Vector((-0.6, -0.4, 1.2)), back + Vector((-1.2, -1.0, 3.0)), Vector((back.x - 1.5, back.y - 1.5, 0.2))], 0.02,
              crew.flat("hose", (0.08, 0.06, 0.05), 0.6))
    loc = Vector((x + 3.2, -5.0, bed + 1.2))
    cam(loc, Vector((x, -1.6, bed + 1.6)), lens=24)
    return dict(cine={"sat": 1.05, "exposure": 1.4}, bloom=0.4)


@shot("p3_30", "He finds no sign of a collision.", "CU · 50mm", 2.6,
      "The diver (helmet in frame) runs his glove along the stem: sound planks, no damage", "Bubbles, glove on wood")
def s30(t):
    SHIP, m, dv = diver_scene(t)
    h = dv.h; bed = -5.4
    xs = ship.L / 2 - 2.0
    M = crew.place((xs, -1.4, bed + 0.02), 60)
    Mi = M.inverted()
    P.stand(h, lean=8); P.head(h, pitch=-35, yaw=-15)
    hp = SHIP @ Vector((xs + 0.3, -0.75 + 0.2 * t, -2.6))
    P.hand_reach(h, "R", Mi @ hp, elbow=(-0.6, 0.3, -0.5)); h.aim("wrist.R", Vector((-0.4, -0.5, 0.8))); P.rest_hand(h, "R", 15)
    P.arm_down(h, "L", bend=20)
    dv.finish(look_at=hp, place=M, hair=False)
    parts, back = crew.diver_helmet(dv); crew.hide_head(dv)
    loc = hp + Vector((1.5, -2.3, -0.9))
    cam(loc, hp + Vector((0, 0, -0.45)), lens=35, fstop=4.0, focus=(hp - loc).length)
    return dict(cine={"sat": 1.05, "exposure": 1.4}, bloom=0.4)


@shot("p3_31", "The surveyor comes away unable to explain why anybody would have abandoned the vessel.", "MS · 50mm", 4.2,
      "On deck the surveyor stops writing in his notebook, looks round the empty ship and shakes his head", "Pencil stops, wind, gulls")
def s31(t):
    SHIP, m = mc_at_gib(t)
    Ms = ST.on_ship(SHIP, -5.6, -2.3, 150)
    sv = crew.person("surveyor", wet=0.0, idx=1)
    h = sv.h; P.stand(h, lean=3, weight="R"); P.head(h, pitch=4, yaw=-14 * math.sin(t * math.pi * 2), tilt=2)
    for sd in ("L", "R"):
        sg = H.SIDE[sd]
        P.hand_reach(h, sd, Vector((0.08 * sg, -0.28, 1.05)), elbow=(0.6 * sg, 0.4, -0.5)); h.aim(f"wrist.{sd}", Vector((-0.3 * sg, -0.7, 0.4))); P.grip(h, sd, 0.5)
    sv.brow_knit(1.0); sv.lids(0.3)
    sv.finish(look_at=ST.deck_world(SHIP, -6, -1, 2.0), place=Ms, density=hair(sv))
    crew.top_hat(sv)
    PR.paper("notebook", Ms @ Vector((0.0, -0.3, 1.1)), size=(0.1, 0.16), rot_z=0)
    es = eyes(sv)
    fwd = (Ms.to_3x3() @ Vector((0, -1, 0)))
    loc = es + fwd * 1.9 + Vector((0, 0, -0.1)) + (Ms.to_3x3() @ Vector((0.5, 0, 0)))
    cam(loc, es + Vector((0, 0, -0.18)), lens=50, fstop=2.8, focus=(es - loc).length)
    return dict(cine={"sat": 1.1})


@shot("p3_32", "Flood looks for evidence of violence.", "MS · 35mm", 3.0,
      "Flood kneels on the deck by the rail with a magnifying glass", "Knee on wood, coat rustle")
def s32(t):
    SHIP, m = mc_at_gib(t)
    fl = crew.person("flood", wet=0.0, kneel=True)
    h = fl.h
    drop = 0.45
    M = ST.on_ship(SHIP, -6.0, -2.75, -90, drop=drop)
    crew.kneel(h, drop, knee="L", lean=26)
    P.head(h, pitch=44, yaw=0)
    Mi = M.inverted()
    spot = ST.deck_world(SHIP, -5.95, -3.4, 0.0)
    mg = spot + Vector((0, 0, 0.16 + 0.03 * math.sin(t * 3)))
    P.hand_reach(h, "R", Mi @ (mg + Vector((0.0, 0.08, 0.0))), elbow=(-0.7, 0.3, -0.6)); h.aim("wrist.R", Vector((0, -1, -0.2))); P.grip(h, "R", 0.9)
    knee = h.bone_tail("upperleg02.R")
    P.hand_reach(h, "L", knee + Vector((0, -0.03, 0.08)), elbow=(0.7, 0.3, -0.5)); P.rest_hand(h, "L", 30)
    fl.brow_knit(0.9)
    fl.finish(look_at=spot, place=M, density=hair(fl))
    crew.top_hat(fl)
    PR.magnifier("glass", mg, (0, 0, 1), (SHIP.to_3x3() @ Vector((0, 1, 0.3))))
    loc = ST.deck_world(SHIP, -3.7, -1.9, 1.0)
    cam(loc, ST.deck_world(SHIP, -6.0, -2.9, 0.65), lens=35, fstop=4.0)
    return dict(cine={"sat": 1.1})


@shot("p3_33", "There are marks on the deck that he thinks might be blood.", "OTS insert · 50mm", 2.8,
      "Over Flood's shoulder: dark stains soaked into the deck grain under the glass", "Wind, a breath")
def s33(t):
    SHIP, m = mc_at_gib(t)
    # stains in the deck planking (object-space points of the deck)
    deck = next(o for o in bpy.data.objects if o.name.startswith("MC_deck") and o.type == 'MESH' and "house" not in o.name)
    spotl = Vector((-5.95, -3.4, ship.zdeck(-5.95)))
    mat = deck.data.materials[0]
    bpy.context.view_layer.update()
    dgr = bpy.context.evaluated_depsgraph_get()
    def on_deck(pl):
        w = SHIP @ (pl + Vector((0, 0, 1.0)))
        r = bpy.context.scene.ray_cast(dgr, w, (SHIP.to_3x3() @ Vector((0, 0, -1))))
        return r[1] if r[0] else SHIP @ pl
    cs = [on_deck(spotl), on_deck(spotl + Vector((0.13, 0.09, 0))), on_deck(spotl + Vector((-0.11, 0.16, 0))), on_deck(spotl + Vector((0.05, -0.12, 0)))]
    for k in range(len(deck.data.materials)):
        deck.data.materials[k] = PR.stain_decal_mat(deck.data.materials[k], cs, radius=0.06)

    spotl = SHIP.inverted() @ cs[0]
    fl = crew.person("flood", wet=0.0, kneel=True)
    h = fl.h; drop = 0.45
    M = ST.on_ship(SHIP, -6.0, -2.75, -90, drop=drop)
    crew.kneel(h, drop, knee="L", lean=30); P.head(h, pitch=48)
    Mi = M.inverted()
    spot = SHIP @ spotl
    mg = spot + Vector((0, 0, 0.14))
    P.hand_reach(h, "R", Mi @ (mg + Vector((0.0, 0.08, 0.0))), elbow=(-0.7, 0.3, -0.6)); h.aim("wrist.R", Vector((0, -1, -0.2))); P.grip(h, "R", 0.9)
    P.arm_down(h, "L", bend=30)
    fl.finish(look_at=spot, place=M, density=hair(fl))
    crew.top_hat(fl)
    PR.magnifier("glass", mg, (0, 0, 1), (SHIP.to_3x3() @ Vector((0, 1, 0.3))))
    ef = eyes(fl)
    fill = bpy.data.objects.new("stainfill", bpy.data.lights.new("stainfill", 'AREA')); bpy.context.scene.collection.objects.link(fill)
    fill.data.energy = 25; fill.data.size = 0.8; fill.data.color = (1.0, 0.85, 0.7); fill.visible_camera = False
    fill.location = spot + (SHIP.to_3x3() @ Vector((0.5, 0.9, 0.9))); fill.rotation_euler = (spot - fill.location).to_track_quat('-Z', 'Y').to_euler()
    loc = spot + (SHIP.to_3x3() @ Vector((0.55, 0.35, 0.5)))
    cam(loc + (spot - loc) * 0.1 * ease(t), spot, lens=50, fstop=2.8, focus=(spot - loc).length)
    return dict(cine={"sat": 1.12})


# ============================================================================ THE SWORD
def sword_under_berth(cab, drawn=0.0):
    bx1, uy, uz = cab["under"]
    hilt = Vector((bx1 + 0.12 - 0.5 * drawn, uy - 0.05, uz + 0.03))
    d = Vector((-1, 0.05, 0)).normalized()
    sw, steel = PR.sword("sword", hilt, d)
    sc = PR.scabbard("scabbard", hilt + d * 0.012, d, length=0.8)
    return hilt, d


@shot("p3_34", "There's also a sword from beneath the captain's berth.", "MS · 35mm", 3.2,
      "In the captain's cabin an officer kneels and draws a sword in its scabbard out from under the berth",
      "Scabbard scrapes on the boards")
def s34(t):
    cab = RM.mc_cabin()
    hilt, d = sword_under_berth(cab, drawn=ease(t))
    p = crew.person("captain2", wet=0.0, kneel=True)
    h = p.h; drop = 0.45
    M = crew.place((hilt.x + 0.85, hilt.y - 0.1, 0.0), 180, drop=drop)
    crew.kneel(h, drop, knee="R", lean=30)
    P.head(h, pitch=40, yaw=0)
    Mi = M.inverted()
    P.hand_reach(h, "R", Mi @ (hilt - d * 0.07 + Vector((0, 0, 0.02))), elbow=(-0.7, 0.3, -0.6)); h.aim("wrist.R", Mi.to_3x3() @ (-d)); P.grip(h, "R", 1.0)
    knee = h.bone_tail("upperleg02.L")
    P.hand_reach(h, "L", knee + Vector((0, -0.03, 0.08)), elbow=(0.7, 0.3, -0.5)); P.rest_hand(h, "L", 30)
    p.finish(look_at=hilt, place=M, density=hair(p))
    loc = Vector((1.3, -1.25, 1.45))
    cam(loc, Vector((hilt.x + 0.3, hilt.y - 0.2, 0.55)), lens=28, fstop=4.0)
    return dict(cine={"sat": 1.1, "exposure": 0.2})


def deveau_draws(cab, t):
    dv = crew.person("deveau", wet=0.5)
    h = dv.h
    M = crew.place((0.0, -0.15, 0.0), 160)
    Mi = M.inverted()
    P.stand(h, lean=6, weight="R"); P.head(h, pitch=18, yaw=-12)
    # left hand holds the scabbard at waist height; right hand draws the blade out along it
    sc_mouth = M @ Vector((0.12, -0.32, 1.02))
    d = (M.to_3x3() @ Vector((0.9, -0.15, -0.35))).normalized()
    out = 0.15 + 0.62 * ease(t)
    hilt = sc_mouth - d * out
    PR.scabbard("scabbard", sc_mouth, d, length=0.8)
    PR.sword("sword", hilt, d, rust=0.8)
    P.hand_reach(h, "L", Mi @ (sc_mouth + d * 0.06), elbow=(0.7, 0.3, -0.6)); h.aim("wrist.L", Mi.to_3x3() @ d); P.grip(h, "L", 1.0)
    P.hand_reach(h, "R", Mi @ (hilt - d * 0.06), elbow=(-0.7, 0.4, -0.5)); h.aim("wrist.R", Mi.to_3x3() @ (-d)); P.grip(h, "R", 1.0)
    dv.brow_knit(0.7); dv.lids(0.5)
    dv.finish(look_at=hilt + d * 0.4, place=M, density=hair(dv))
    return dv, hilt, d


@shot("p3_35", "Deveau says he drew it from its sheath when he first boarded.", "MS · 50mm", 3.0,
      "Flashback, 5 December: Deveau in the cabin draws the sword from its sheath and looks along the blade", "Blade rasps out of the sheath")
def s35(t):
    cab = RM.mc_cabin()
    dv, hilt, d = deveau_draws(cab, t)
    ed = eyes(dv)
    fwd = Vector((math.cos(math.radians(160)), math.sin(math.radians(160)), 0))
    side = fwd.cross(Vector((0, 0, 1)))
    loc = ed + fwd * 0.6 + side * 1.1 + Vector((0, 0, -0.25))
    cam(loc, ed.lerp(hilt, 0.6), lens=35, fstop=2.8, focus=(ed - loc).length)
    return dict(cine={"sat": 0.95, "exposure": 0.2})


@shot("p3_36", "It looked rusty to him.", "INSERT · 50mm", 2.4,
      "Along the drawn blade: rust bloom on the steel, Deveau's hand on the grip and his sleeve in frame; focus runs down the blade",
      "End of the rasp, a drip")
def s36(t):
    cab = RM.mc_cabin()
    dv, hilt, d = deveau_draws(cab, 1.0)
    side = d.cross(Vector((0, 0, 1))).normalized()
    bp = hilt + d * 0.35
    loc = bp + side * 0.32 + Vector((0, 0, 0.16)) - d * 0.12
    near = (hilt + d * 0.15 - loc).length; far = (hilt + d * 0.6 - loc).length
    cam(loc, hilt + d * 0.3, lens=50, fstop=2.0, focus=near + (far - near) * ease(t))
    return dict(cine={"sat": 0.95, "exposure": 0.2})


# ============================================================================ THE CHEMIST
def chemist(lb, t, hold=0.0):
    p = crew.person("chemist", wet=0.0, idx=2)
    h = p.h
    bx, by = lb["bench"]; bz = lb["bench_z"]
    M = crew.place((bx, by - 0.65, 0.0), 90)
    Mi = M.inverted()
    P.stand(h, lean=20 * (1 - hold) + 4, weight="L"); P.head(h, pitch=34 * (1 - hold) - 6 * hold, yaw=0)
    dish = Vector((bx + 0.05, by - 0.12, bz + 0.005))
    tube_hold = Vector((bx + 0.1, by - 0.3, 1.55))
    if hold > 0:
        P.hand_reach(h, "R", Mi @ (tube_hold + Vector((0, 0, -0.05))), elbow=(-0.8, 0.3, -0.5)); h.aim("wrist.R", Vector((0, -0.3, 1))); P.grip(h, "R", 0.7)
        P.hand_reach(h, "L", Mi @ Vector((bx - 0.3, by - 0.2, bz + 0.03)), elbow=(0.8, 0.3, -0.4)); P.rest_hand(h, "L", 20)
    else:
        P.hand_reach(h, "R", Mi @ (dish + Vector((0.05, 0, 0.06 + 0.01 * math.sin(t * 12)))), elbow=(-0.8, 0.3, -0.5)); P.grip(h, "R", 0.8)
        P.hand_reach(h, "L", Mi @ (dish + Vector((-0.12, 0.0, 0.04))), elbow=(0.8, 0.3, -0.4)); P.grip(h, "L", 0.5)
    p.finish(look_at=tube_hold if hold > 0 else dish, place=M, density=hair(p))
    # bench things: dish, rack of tubes, the sword laid along the bench
    ship.cyl("dish", dish, dish + Vector((0, 0, 0.012)), 0.05, 0.055, crew.flat("porcelain", (0.8, 0.78, 0.74), 0.2), verts=32)
    for k in range(4):
        PR.test_tube(f"tube{k}", Vector((bx - 0.55 + k * 0.035, by + 0.15, bz)), liquid=(0.75, 0.72, 0.55))
    ship.box("rack", (bx - 0.5, by + 0.15, bz + 0.05), (0.18, 0.05, 0.02), PR.mat_wood("rackw", "dark_wooden_planks", 2.0))
    PR.sword("lab_sword", Vector((bx + 0.6, by + 0.1, bz + 0.012)), Vector((1, 0.05, 0)), rust=0.8)
    if hold > 0:
        PR.test_tube("held", tube_hold - Vector((0, 0, 0.1)), height=0.16, r=0.009, liquid=(0.85, 0.8, 0.55))
    return p, M, dish, tube_hold


@shot("p3_37", "The marks and the sword go for chemical examination.", "MS · 50mm", 3.4,
      "A chemist at his bench scrapes a sample into a dish; the sword lies on the bench", "Scraping, glass clink")
def s37(t):
    lb = RM.lab()
    p, M, dish, th = chemist(lb, t)
    ec = eyes(p)
    loc = ec + Vector((1.05, 0.62, -0.2))
    cam(loc, ec.lerp(dish, 0.5), lens=35, fstop=3.2, focus=(ec - loc).length)
    return dict(cine={"sat": 1.1, "exposure": -0.35})


@shot("p3_38", "The examination finds no trace of blood.", "MS · 50mm", 3.0,
      "Behind the chemist: he holds the test tube up against the bright window; no change; he lowers it", "SILENCE, then glass on wood")
def s38(t):
    lb = RM.lab()
    p, M, dish, th = chemist(lb, t, hold=1.0)
    ec = eyes(p)
    loc = ec + Vector((-0.55, -1.25, -0.05))
    cam(loc, th + Vector((0, 0, -0.05)), lens=50, fstop=2.8, focus=(th - loc).length)
    return dict(cine={"sat": 1.1, "exposure": -0.3})


# ============================================================================ THE AWARD AND THE END OF THE VOYAGE
@shot("p3_39", "The court hears evidence for months.", "WS · 24mm", 3.0,
      "Locked wide of the court: papers stacked high on the clerk's desk; the light has moved across the floor", "Clock tick, quill, rain on glass")
def s39(t):
    ct = RM.court()
    court_people(ct, {"clerk": 1}, t)
    cx_, cy_ = ct["clerk"]
    for k in range(14):
        PR.paper(f"pile{k}", (cx_ + 0.45, cy_ - 0.05, 0.765 + k * 0.006), size=(0.21, 0.3), rot_z=0.05 * math.sin(k * 3), text_img=os.path.join(TEX, "papers.png"))
    cam(Vector((3.8, 2.0, 2.6)), Vector((-0.5, 8.5, 1.3)), lens=24)
    return dict(cine={"sat": 1.12, "exposure": 0.1})


@shot("p3_40", "It awards the salvors seventeen hundred pounds.", "MS · 50mm", 3.6,
      "The judge reads the award from the bench; below him Deveau listens on the bench", "Paper rustle, murmur")
def s40(t):
    ct = RM.court()
    court_people(ct, {"judge": 1, "salvors": 1}, t)
    jx, jy, jz = ct["judge"]
    cam(lerp((-1.3, 6.4, 1.75), (-1.2, 6.7, 1.75), ease(t)), Vector((jx, jy, 2.25)), lens=50, fstop=4.0)
    return dict(cine={"sat": 1.12, "exposure": 0.1}, callout="£1,700")


@shot("p3_41", "No murder is established.", "OTS · 35mm", 2.4,
      "Behind Flood: he sits back slowly at the counsel's table; the empty witness box beyond", "Chair creak")
def s41(t):
    ct = RM.court()
    p = crew.person("flood", wet=0.0, wig=True, seated=True)
    h = p.h; seat = 0.46; drop = crew.hip_height(h) - seat - 0.08
    cxl, cyl = ct["counsel"]
    PR.chair("flood_chair", (cxl - 0.6, cyl - 0.75, 0.0), 90)
    M = crew.place((cxl - 0.6, cyl - 0.72, 0.0), 90, drop=drop)
    crew.sit(h, drop, lean=14 - 12 * ease(t), feet_fwd=0.45)
    for sd in ("L", "R"):
        sg = H.SIDE[sd]
        P.hand_reach(h, sd, M.inverted() @ Vector((cxl - 0.6 - 0.22 * sg, cyl - 0.38 - 0.05 * ease(t), 0.82)), elbow=(0.7 * sg, 0.3, -0.5))
        h.aim(f"wrist.{sd}", Vector((0, -1, -0.7))); P.rest_hand(h, sd, 25)
    P.head(h, pitch=8 - 6 * ease(t), yaw=-10)
    p.lids(0.5); p.brow_knit(0.6)
    p.finish(look_at=(0.0, 9.0, 1.9), place=M, density=hair(p))
    crew.bands(p)
    ef = eyes(p)
    loc = ef + Vector((0.6, -1.4, 0.3))
    cam(loc, ef + Vector((0.35, 1.2, -0.35)), lens=32, fstop=4.0, focus=(ef - loc).length)
    return dict(cine={"sat": 1.1, "exposure": 0.05})


def pose_carry(p, M, chest_c):
    h = p.h; Mi = M.inverted()
    P.stand(h, lean=10, weight="L"); P.head(h, pitch=8)
    for sd in ("L", "R"):
        sg = H.SIDE[sd]
        P.hand_reach(h, sd, Mi @ (chest_c + (M.to_3x3() @ Vector((0.33 * sg, 0, -0.08)))), elbow=(0.7 * sg, 0.3, -0.6))
        h.aim(f"wrist.{sd}", Vector((-sg * 1.0, 0, 0.2))); P.rest_hand(h, sd, 45)


@shot("p3_42", "By then, the owners have recovered the ship and put a new captain and crew on board.", "WS · 35mm", 4.2,
      "A new crew carries sea chests aboard; the new captain stands at the gangway", "Boots, chests set down, harbour")
def s42(t):
    SHIP, m = mc_at_gib(t)
    wood = PR.mat_wood("chestw", "dark_wooden_planks", 2.0, tint=(0.75, 0.5, 0.3))
    for i, (key, x, y, hdg) in enumerate((("sailor_a", -1.4, -2.7, 0), ("sailor_b", 0.4, -2.6, 10))):
        M = ST.on_ship(SHIP, x, y, hdg)
        cc = M @ Vector((0, -0.52, 0.98))
        p = crew.person(key, wet=0.0, idx=i); pose_carry(p, M, cc)
        p.finish(look_at=cc + Vector((0, 0, -1)), place=M, density=hair(p))
        b = ship.box(f"seachest{i}", cc, (0.6, 0.38, 0.36), wood, bevel=0.01); b.rotation_euler = M.to_euler()
    Mc = ST.on_ship(SHIP, -3.6, -2.4, 10)
    c2 = crew.person("captain2", wet=0.0, idx=3); stand_pose(c2, hands="behind", yaw=-10)
    c2.finish(look_at=ST.deck_world(SHIP, 0, -2, 1.6), place=Mc, density=hair(c2))
    loc = ST.deck_world(SHIP, 4.6, -2.8, 1.6)
    cam(lerp(loc, loc + (SHIP.to_3x3() @ Vector((-0.5, 0, 0))), ease(t)), ST.deck_world(SHIP, -1.5, -2.5, 1.35), lens=32, fstop=5.6)
    return dict(cine={"sat": 1.1})


@shot("p3_43", "The Mary Celeste can finish the voyage Briggs began.", "EWS · 24mm", 5.0,
      "She sails out past the Rock under full sail in low gold light, bound for Genoa", "Sails fill, wind; music lifts")
def s43(t):
    ST.exterior("sunset", sky_rot=120, sun_az=245, sun_el=9)
    gib_land(town_on=True)
    rx, ry = TR.to_xy(36.135, -5.36, GIB_BAY)
    hd = 150.0
    m = ST.mc("full", wind=ST.local_wind(WIND, hd), wet=0.2, detail=False, gap=False)
    loc0 = Vector((rx - 1400 + 60 * t, ry - 1500 - 100 * t, 0))
    SHIP = ST.set_ship(m, loc=loc0, heading=hd, heel=5 + 0.6 * math.sin(t * 2))
    ST.ocean_around(loc0, hulls=[m["hull"]], mood="sunset", size=300, scale=1.0, chop=1.1, wind=9, foam=0.15, time=11 + t * 4)
    sea.haze((rx - 1500, ry - 1200, 150), (9000, 9000, 300), density=0.00008, color=(0.85, 0.66, 0.5))
    loc = lerp(loc0 + Vector((-75, -110, 6)), loc0 + Vector((-90, -95, 6)), ease(t))
    cam(loc, lerp(loc0 + Vector((0, 0, 10)), Vector((rx, ry, 200)), 0.08), lens=32)
    return dict(cine={"sat": 1.14, "exposure": 0.05})
