"""Cabin shots (storyboard + final). blender -b --python scenes/sc_cabin.py -- SHOT=02
Shot ids follow STORYBOARD.md."""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "p2lib"))
import env
import common as C
C.reset()
import bpy
from mathutils import Vector, Matrix
import stage as S, cabin, cast, acts as A, poses as P
import human as H

SHOT = S.shot_arg() or "02"
HAIR = float(os.environ.get("HAIR", "1.0"))
sc = S.setup(samples=160)
T = cabin.TABLE
SET = None


def seated(person, chair, lean=4, yaw=None, back=0.0, lift=0.0):
    chair_pos, cyaw, _ = SET["chairs"][chair]
    A.sit_chair(person.h, lean=lean)
    yaw = (0.0 if chair == 1 else 180.0) if yaw is None else yaw
    dy = (-0.01 + back) if chair == 1 else (0.06 - back)
    Mw = A.sit_place(person.h, (chair_pos.x, chair_pos.y + dy), yaw, SET["seat_z"] + lift)
    A.feet_to_floor(person.h, Mw, 0.013)
    return Mw


def briggs_writing(pause=False, expr=None):
    b = cast.Briggs(expr=expr, seated=True)
    Mw = seated(b, 1)
    Mi = Mw.inverted()
    paper = SET["letter"] + Vector((0.0, 0.02, 0.0))
    A.write(b.h, Mi, paper, side="R", other_on_table=SET["letter"] + Vector((-0.2, 0.06, 0)), lean=14,
            head_pitch=(6 if pause else 28))
    if pause:
        b.lids(0.3)
    b.finish_live(place=Mw, density=HAIR)
    b.look(paper if not pause else T + Vector((-1.6, -1.4, 0.75)))
    cabin.pen("pen", b, "R")
    return b


def sarah_writing(look_up=False, temple=False, expr=None):
    s = cast.Sarah(seated=True, expr=expr)
    Mw = seated(s, 0)
    Mi = Mw.inverted()
    paper = SET["letter"] + Vector((0.0, -0.02, 0.0))
    A.write(s.h, Mi, paper, side="R", other_on_table=SET["letter"] + Vector((0.2, -0.05, 0)), lean=10,
            head_pitch=(-14 if look_up else 26))
    if temple:
        P.head(s.h, pitch=-12, yaw=-6, tilt=8)
        A.hand_to_temple(s.h, "L")
    s.finish_live(place=Mw, density=HAIR)
    if look_up:
        s.look(T + Vector((0.3, -0.5, 2.2)))
    elif temple:
        s.look(T + Vector((-1.2, 0.6, 0.6)))
    else:
        s.look(paper)
    cabin.pen("pen", s, "R")
    return s


def white_maquette():
    """Explainer look: every surface a warm white clay, the lamp still glowing; deckhead and one wall lifted off."""
    clay = cabin.plain("clay", (0.62, 0.58, 0.52), rough=0.6)
    hide = ("ceil", "beam", "skylight", "well", "glazing", "air", "wall_s", "wain_y-1", "wall_x1", "wain_x1", "rail_y-1", "rail_x1",
            "stile", "wframe", "wglass", "comp_coaming", "comp_beam")
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.name == "flame":
            continue
        if o.name.startswith(hide) or any(k in o.name for k in ("beam", "glazing")):
            o.hide_render = True
        else:
            o.data.materials.clear(); o.data.materials.append(clay)


cine = {"sat": 1.06, "exposure": -0.05}

if SHOT in ("02", "03", "11"):
    SET = cabin.build("warm", letter_side=1)
    b = briggs_writing(pause=(SHOT == "11"), expr=({"mouth-corner-puller": 0.25, "eyebrows-left-inner-up": 0.4,
                                                     "eyebrows-right-inner-up": 0.4} if SHOT == "11" else None))
    head = b.h.bone_head("head")
    if SHOT == "02":        # MS: Briggs writes home (person card right)
        S.cam(Vector((T.x + 1.35, T.y - 1.05, 1.22)), head.lerp(SET["letter"], 0.35) + Vector((0, 0, -0.05)), lens=40, fstop=2.8)
    elif SHOT == "03":      # OTS insert: over his right shoulder onto the nib and the page
        S.cam(head + Vector((-0.36, 0.12, 0.34)), SET["letter"] + Vector((0.03, 0.0, 0)), lens=40, fstop=2.4)
    else:                   # CU: he pauses mid-letter, a small sad smile
        # MS profile, lamp-lit side toward camera's far side: face half in shadow
        S.cam(head + Vector((-1.1, -0.4, 0.02)), head + Vector((0, -0.12, -0.25)), lens=40, fstop=2.8)

elif SHOT == "12":          # WS: Briggs stands and looks round the crowded cabin; no corner left for a boy
    SET = cabin.build("warm", letter_side=1)
    b = cast.Briggs()
    P.stand(b.h, weight="R", twist=-6)
    P.head(b.h, pitch=-6, yaw=-28)
    P.arm_down(b.h, "L"); P.rest_hand(b.h, "L")
    P.arm_down(b.h, "R", bend=20); P.rest_hand(b.h, "R")
    Mw = A.stand_place((0.95, 0.55), -120)
    b.finish_live(place=Mw, density=HAIR)
    b.look(Vector((-1.4, 1.2, 0.9)))
    bh = b.h.bone_head("head")
    S.cam(Vector((-0.7, -1.38, 1.4)), Vector((0.6, 0.45, 1.45)), lens=22, fstop=5.6)

elif SHOT == "13":          # top-down white maquette of the cabin: every corner used
    SET = cabin.build("warm", letter_side=1)
    for o in bpy.data.objects:          # the real cabin, opened up: deckhead and the near bulkheads lifted off
        if o.type == 'MESH' and (o.name.startswith(("ceil", "beam", "skylight", "well", "glazing", "air", "wall_s", "wain_y-1",
                                                      "wall_x1", "wain_x1", "rail_y-1", "rail_x1", "stile", "wframe", "wglass",
                                                      "comp_coaming", "comp_beam")) or "glazing" in o.name):
            o.hide_render = True
    for n in ("berth_top", "berth_valance", "shelf"):
        for o in bpy.data.objects:
            if o.name.startswith(n):
                o.hide_render = True
    for o in [o for o in bpy.data.objects if o.type == 'LIGHT' and o.name not in ("LampLight",)]:
        o.hide_render = True
    sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.01, 0.008, 0.006, 1)
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.1
    S.cam(Vector((2.6, -4.4, 6.4)), Vector((-0.1, 0.1, 0.3)), lens=35)
    bpy.data.objects["LampLight"].data.energy = 60
    k = bpy.data.objects.new("MaqSun", bpy.data.lights.new("MaqSun", 'SUN')); sc.collection.objects.link(k)
    k.data.energy = 3.0; k.data.angle = math.radians(4); k.data.color = (1, 0.93, 0.84)
    k.rotation_euler = (math.radians(50), 0, math.radians(-130))
    cine = {"sat": 1.05, "exposure": 0.1}

elif SHOT in ("07", "08"):  # Sarah at the table; Sophia beside her holds up her doll
    SET = cabin.build("warm", letter_side=-1, letters=False)
    s = cast.Sarah(seated=True, expr={"mouth-corner-puller": 0.35})
    Mw = seated(s, 0, lean=-6, yaw=192.0, back=0.06, lift=0.015)
    A.hands_in_lap(s.h)
    P.head(s.h, pitch=16, yaw=-34, tilt=4)
    s.finish_live(place=Mw, density=HAIR)
    k = cast.Child(expr={"mouth-corner-puller": 0.5})
    P.stand(k.h, weight="L")
    tgt = k.h.bone_head("head") + Vector((0.0, -0.22, -0.14))
    A.hold_up(k.h, "R", tgt + Vector((-0.03, 0, 0)), elbow=(-0.6, 0.2, -0.8))
    A.hold_up(k.h, "L", tgt + Vector((0.03, 0, -0.03)), elbow=(0.6, 0.2, -0.8))
    P.head(k.h, pitch=-12, yaw=-10)
    cp = SET["chairs"][0][0]
    Mk = A.stand_place((cp.x + 0.55, cp.y - 0.2), A.yaw_to((cp.x + 0.55, cp.y - 0.2), (cp.x, cp.y + 0.05)))
    k.finish_live(place=Mk, density=HAIR)
    hand = (k.h.bone_tail("wrist.R") + k.h.bone_tail("wrist.L")) / 2
    d = cabin.doll("doll", hand + Vector((0, 0, -0.07)), s=0.85)
    cabin.attach(d, k, "wrist.R")
    sh, kh = s.h.bone_head("head"), k.h.bone_head("head")
    s.look(kh); k.look(sh)
    if SHOT == "07":
        S.frame([sh, kh, sh - Vector((0, 0, 0.5)), d.location], Vector((1.0, 0.45, 0.4)), lens=28, fill=0.8,
                bounds=SET["bounds"], fstop=4.0)
    else:
        S.ots(sh, kh - Vector((0, 0, 0.12)), side=1, back=0.4, out=0.42, up=0.25, lens=35, fstop=2.8)

elif SHOT == "14":          # the visitor ducks under the companion beam; her bonnet brim knocks it; Sarah rises
    SET = cabin.build("warm", letter_side=-1)
    v = cast.Visitor(expr={"mouth-corner-puller": 0.5, "mouth-open": 0.15})
    P.stand(v.h, lean=26, weight="L")
    P.head(v.h, pitch=10)
    P.arm_down(v.h, "R", out=0.25, fwd=0.3, bend=50); P.rest_hand(v.h, "R")
    P.arm_down(v.h, "L", out=0.2, fwd=0.2, bend=30); P.rest_hand(v.h, "L")
    xs = cabin.COMP["x0"] - 0.4
    Mv = A.stand_place((xs, -1.1), -90)
    v.finish_live(place=Mv, density=HAIR)
    cabin.bonnet(v)
    s = cast.Sarah(expr={"mouth-corner-puller": 0.4})
    P.stand(s.h, weight="R", lean=4)
    P.head(s.h, pitch=-14, yaw=8)
    P.arm_down(s.h, "L", out=0.1, fwd=0.2, bend=40); P.rest_hand(s.h, "L")
    P.arm_down(s.h, "R", out=0.1, fwd=0.25, bend=50); P.rest_hand(s.h, "R")
    ch0 = SET["chairs"][0][2][0]
    while ch0.parent is not None:
        ch0 = ch0.parent
    ch0.location += Vector((-1.05, 0.5, 0))        # she has pushed her chair back from the table
    bpy.context.view_layer.update()
    Ms = A.stand_place((0.04, -1.12), A.yaw_to((0.04, -1.12), (xs, -1.1)))
    s.finish_live(place=Ms, density=HAIR)
    s.look(v.h.bone_head("head")); v.look(s.h.bone_head("head"))
    vh, shh = v.h.bone_head("head"), s.h.bone_head("head")
    S.cam(Vector((-1.2, -0.45, 0.95)), Vector((1.3, -1.25, 1.85)), lens=24, fstop=4.0)

elif SHOT in ("17", "19"):  # Sarah writing; a bang overhead (17); fingers to her temple (19)
    SET = cabin.build("warm", letter_side=-1)
    s = sarah_writing(look_up=(SHOT == "17"), temple=(SHOT == "19"),
                      expr=({"eyebrows-left-up": 0.6, "eyebrows-right-up": 0.6, "mouth-open": 0.15} if SHOT == "17"
                            else {"mouth-corner-puller": 0.3, "eyebrows-left-inner-up": 0.5, "eyebrows-right-inner-up": 0.5}))
    head = s.h.bone_head("head")
    if SHOT == "17":
        S.cam(Vector((T.x - 1.25, T.y + 0.85, 1.2)), head + Vector((0, 0.1, -0.12)), lens=50, fstop=2.8)
    else:
        S.frame([head + Vector((0, 0, 0.12)), head - Vector((0, 0, 0.7)), SET["letter"]], Vector((1.0, 0.25, 0.15)), lens=40,
                fill=0.85, bounds=SET["bounds"], fstop=2.8)

elif SHOT == "23":          # 7 November, evening: Sarah writes by the lamp; Sophia asleep in the berth behind
    SET = cabin.build("night", letter_side=-1)
    s = sarah_writing()
    head = s.h.bone_head("head")
    S.cam(Vector((T.x + 1.05, T.y - 0.95, 1.12)), head.lerp(Vector((-1.4, 1.2, 0.7)), 0.3), lens=35, fstop=2.8)
    cine = {"sat": 1.08, "exposure": 0.25}

elif SHOT in ("30", "31", "32"):   # 25 November, dawn: the mate chalks the morning entry on the slate
    SET = cabin.build("dawn", letters=False, slate=True, slate_at=(0.32, 0.0))
    sl = SET["slate"]
    lines = ["Nov 24  Lat 36.56 N", "        Lon 27.20 W", "", "Nov 25  At 8, Eastern point", "        bore SSW 6 miles"]
    cabin.chalk_text("chalk", sl, 0.32, 0.22, lines, size=0.0135)
    if SHOT == "30":
        m = cast.Sailor(name="Mate", years=31, cap=False)
        P.stand(m.h, lean=28, weight="L")
        P.head(m.h, pitch=34)
        Mm = A.stand_place((T.x + cabin.TW / 2 + 0.3, sl.y), -90)
        Mi = Mm.inverted()
        P.hand_reach(m.h, "R", Mi @ (sl + Vector((0.06, -0.05, 0.05))), elbow=(-0.8, 0.3, -0.3)); A.pen_grip(m.h, "R")
        P.hand_reach(m.h, "L", Mi @ (sl + Vector((0.12, 0.2, 0.04))), elbow=(0.8, 0.3, -0.3)); P.rest_hand(m.h, "L", 15)
        m.finish_live(place=Mm, density=HAIR)
        m.look(sl)
        hd = m.h.bone_head("head")
        S.cam(Vector((0.5, -0.98, 1.5)), sl + Vector((0.12, 0.0, 0.08)), lens=35, fstop=2.8)
    elif SHOT == "31":        # the real slate close: frame, chalk, the stub of chalk set down
        ship = cabin.ship
        ship.cyl("chalk_stub", sl + Vector((0.2, -0.06, 0.005)), sl + Vector((0.2, -0.015, 0.006)), 0.0055, mat=cabin.plain("chalkstick", (0.75, 0.74, 0.7), rough=0.95), verts=10)
        S.cam(sl + Vector((0.34, -0.3, 0.3)), sl + Vector((0.0, 0.0, 0)), lens=50, fstop=4.0)
    else:
        S.cam(Vector((T.x + 1.2, T.y - 0.9, 1.25)), sl, lens=40, fstop=4.0)
    cine = {"sat": 1.05, "exposure": 0.1}

elif SHOT in ("34", "35", "38", "39"):   # 4 December: Deveau goes through the captain's things
    SET = cabin.build("cold", wet=0.6, lamp_on=False, letters=False, chrono="empty")
    sbt = SET["sideboard_top"]
    cabin.sextant_case(sbt + Vector((0.32, 0.0, 0.0)), cabin.M("brown_planks_05", 5.0, tint=(0.75, 0.42, 0.26), name="mh2"))
    d = cast.Deveau2(wet=0.4)
    P.stand(d.h, lean=18, weight="R")
    P.head(d.h, pitch=30)
    Md = A.stand_place((sbt.x + 0.05, sbt.y + 0.62), 0)
    Mi = Md.inverted()
    tgt = {"34": SET["chrono_box"], "35": SET["chrono_box"], "38": sbt + Vector((0.32, 0, 0.12)),
           "39": sbt + Vector((-0.4, 0.25, -0.3))}[SHOT]
    P.hand_reach(d.h, "R", Mi @ (tgt + Vector((0.04, 0.12, 0.06))), elbow=(-0.8, 0.3, -0.6)); P.rest_hand(d.h, "R", 20)
    P.hand_reach(d.h, "L", Mi @ (sbt + Vector((-0.25, 0.18, 0.04))), elbow=(0.8, 0.3, -0.6)); P.rest_hand(d.h, "L", 18)
    d.lids(0.6); d.brow_knit(0.7)
    d.finish_live(place=Md, density=HAIR)
    d.look(tgt)
    hd = d.h.bone_head("head")
    if SHOT == "34":
        S.frame([hd, hd - Vector((0, 0, 1.4)), sbt + Vector((-0.6, 0, 0)), sbt + Vector((0.6, 0, 0))], Vector((0.9, 0.5, 0.3)),
                lens=26, fill=0.9, bounds=SET["bounds"], fstop=4.0)
    elif SHOT == "35":
        S.cam(hd + Vector((0.12, 0.22, 0.2)), SET["chrono_box"] + Vector((0.0, 0.03, 0)), lens=28, fstop=4.0)
    elif SHOT == "38":
        S.cam(hd + Vector((-0.12, 0.22, 0.2)), sbt + Vector((0.32, 0.03, 0.1)), lens=28, fstop=4.0)
    else:
        S.frame([hd, tgt, sbt, hd - Vector((0, 0, 1.0))], Vector((1.0, 0.6, 0.35)), lens=30, fill=0.9, bounds=SET["bounds"], fstop=3.2)
    S.area("ColdKey", Vector((0.15, -0.3, cabin.RZ + 0.6)), sbt, 1400, size=0.7, color=(0.8, 0.86, 1.0))
    S.area("DevFace", hd + Vector((0.6, 1.0, 0.3)), hd, 25, size=0.6, color=(0.85, 0.9, 1.0))
    cine = {"sat": 1.0, "exposure": 0.3}

elif SHOT == "36":          # flashback, warm: Briggs winds the chronometer
    SET = cabin.build("warm", letters=False, chrono="full")
    b = cast.Briggs()
    cb = SET["chrono_box"]
    P.stand(b.h, lean=24, weight="L")
    P.head(b.h, pitch=30)
    Mb = A.stand_place((cb.x + 0.1, cb.y + 0.56), 0)
    Mi = Mb.inverted()
    P.hand_reach(b.h, "R", Mi @ (cb + Vector((0.0, 0.08, 0.06))), elbow=(-0.8, 0.3, -0.6)); A.pen_grip(b.h, "R")
    P.hand_reach(b.h, "L", Mi @ (cb + Vector((-0.12, 0.05, -0.04))), elbow=(0.8, 0.3, -0.6)); P.rest_hand(b.h, "L", 20)
    b.finish_live(place=Mb, density=HAIR)
    b.look(cb)
    hd = b.h.bone_head("head")
    S.frame([hd, cb, b.h.bone_tail("wrist.R")], Vector((-1.0, -0.2, 0.3)), lens=45, fill=0.85, bounds=SET["bounds"], fstop=2.8)
    cine = {"sat": 1.1, "exposure": 0.0}

S.finish(S.out_path(SHOT), cine=cine)
