"""Part 4 shots. One frame of any shot:   blender -b --python shots/board.py -- S05 [t]
t in 0..1 is the time through the shot (cameras and people are functions of t), default 0.5.
Env: PREVIEW (0.5 = half res), SPP, OUT."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import p4
p4.C.reset()
import bpy
from mathutils import Vector, Matrix
import ship, sea
import sets as S
import poses as P, human as H, deveau as D
import briggs as BG

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["S05"]
SHOT = argv[0]; T = float(argv[1]) if len(argv) > 1 else 0.5
OUT = os.environ.get("OUT", os.path.join(p4.ROOT, "mary_celeste_p4", "out", "board", f"{SHOT}.png"))
sc = p4.C.render_setup(samples=int(os.environ.get("SPP", "96")), noise=0.03, bounces=8)
sc.cycles.volume_bounces = 0
E = p4.ease


def lerp(a, b, t):
    return Vector(a).lerp(Vector(b), t)


def cam(loc, tgt, lens=35, fstop=None, focus=None, roll=0.0):
    return p4.C.camera(tuple(loc), tuple(tgt), lens=lens, fstop=fstop, focus=focus, roll=roll)


def man(kind, SHIP, pos, ang_deg, pose, look_local, hair=1.0, **kw):
    """Place Deveau or Briggs on deck. pos: ship-local x, y (feet on the deck); ang: facing, degrees from +X.
    pose(h, dv, M, Mi) sets the joints; look_local: ship-local point the eyes look at."""
    dv = (BG.Briggs if kind == "briggs" else D.Deveau)(wet=kw.get("wet", 0.4))
    h = dv.h
    zd = ship.zdeck(pos[0]) + 0.006 + kw.get("dz", 0.0)
    Mloc = Matrix.Translation((pos[0], pos[1], zd)) @ Matrix.Rotation(math.radians(ang_deg + 90), 4, 'Z')
    M = SHIP @ Mloc; Mi = M.inverted()
    pose(h, dv, M, Mi)
    dv.finish(look_at=SHIP @ Vector(look_local), place=M, density=hair)
    return dv, M


def head_of(M):
    return M @ Vector((0, -0.08, 1.64))


def finish(sat=1.0, exposure=0.0, bloom=0.3):
    p4.C.finish(OUT, cine={"sat": sat, "exposure": exposure}, bloom=bloom)
    print("RENDERED", OUT)


# ----------------------------------------------------------------------------- poses
def pose_lookdown(pitch=30, yaw=0, lean=8):
    def f(h, dv, M, Mi):
        P.stand(h, lean=lean, weight="R", twist=-3); P.head(h, pitch=pitch, yaw=yaw, tilt=2)
        dv.lids(0.6); dv.brow_knit(0.8)
        P.arm_down(h, "L", out=0.1, fwd=0.03, bend=16); P.rest_hand(h, "L", curl=26)
        P.arm_down(h, "R", out=0.1, fwd=0.05, bend=20); P.rest_hand(h, "R", curl=28)
    return f


def pose_sniff(h, dv, M, Mi):
    """Leaning over the open fore hatch, head lowered into it, breathing in: brows up a little, eyes half shut."""
    P.stand(h, lean=26, weight="L", twist=4); P.head(h, pitch=28, yaw=-4, tilt=-3)
    dv.lids(0.75); dv.brow_knit(0.3)
    P.arm_down(h, "L", out=0.12, fwd=0.25, bend=40); P.rest_hand(h, "L", curl=30)
    P.arm_down(h, "R", out=0.12, fwd=0.2, bend=35); P.rest_hand(h, "R", curl=30)


def pose_rod(SHIP, a_loc, b_loc):
    """Holding the sounding rod up in front of him with both hands (a: left hand, b: right), reading it."""
    def f(h, dv, M, Mi):
        P.stand(h, lean=4, weight="L"); P.head(h, pitch=18, yaw=6)
        dv.lids(0.5); dv.brow_knit(0.9)
        for side, wl, el in (("L", a_loc, (0.6, 0.4, -0.6)), ("R", b_loc, (-0.6, 0.4, -0.6))):
            P.hand_reach(h, side, Mi @ (SHIP @ Vector(wl)), elbow=el)
            P.grip(h, side, 0.85)
    return f


def pose_rail(SHIP, cap_local, yaw=0, pitch=-2):
    def f(h, dv, M, Mi):
        P.stand(h, lean=4, weight="R", twist=-2); P.head(h, pitch=pitch, yaw=yaw, tilt=1)
        dv.lids(0.45); dv.brow_knit(0.9)
        P.hand_reach(h, "R", Mi @ (SHIP @ Vector(cap_local)), elbow=(-0.8, 0.4, -0.5))
        h.aim("wrist.R", (Mi.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized() + Vector((0, -0.3, 0)))
        P.rest_hand(h, "R", curl=30)
        P.arm_down(h, "L", out=0.1, fwd=0.03, bend=14); P.rest_hand(h, "L", curl=24)
    return f


def pose_spear(SHIP, lo_local, hi_local):
    """Both hands on the pump spear, drawing it up out of the pump-tree."""
    def f(h, dv, M, Mi):
        P.stand(h, lean=16, weight="L", twist=2); P.head(h, pitch=26, yaw=0)
        dv.lids(0.6); dv.brow_knit(1.0)
        P.hand_reach(h, "L", Mi @ (SHIP @ Vector(hi_local)), elbow=(0.7, 0.3, -0.6)); P.grip(h, "L", 1.0)
        P.hand_reach(h, "R", Mi @ (SHIP @ Vector(lo_local)), elbow=(-0.7, 0.3, -0.6)); P.grip(h, "R", 1.0)
    return f


# ----------------------------------------------------------------------------- shots
def S01():   # GENOA wide: the ship alongside the quay, barrels coming ashore, late sun
    g = S.set_genoa()
    QY, QZ = g["QY"], g["QZ"]
    c0 = Vector((-17.5, QY + 5.5, QZ + 1.75)); c1 = Vector((-16.0, QY + 5.0, QZ + 1.75))
    cam(lerp(c0, c1, E(T)), (6, QY + 3.5, QZ + 4.2), lens=24)
    finish(sat=1.05)


def S02():   # the nine red-oak barrels set apart, chalk X on each head
    g = S.set_genoa()
    n = g["nine"]; c = sum(n, Vector()) / 9
    p = c + Vector((-2.4, -2.6, 2.1)) + Vector((0.25 * E(T), 0.2 * E(T), -0.05 * E(T)))
    cam(p, c + Vector((0, 0, 0.7)), lens=40, fstop=3.2, focus=(p - c).length)
    finish(sat=1.05)


def S03():   # BRIGGS card: on deck at dusk, looking forward at the yawl on the main hatch
    d = S.set_deck(time="dusk", rail_gap=None, pumps="intact", sails="full", forehatch_off=False, sea_k=0.6)
    SHIP = d["SHIP"]
    dv, M = man("briggs", SHIP, (-6.2, -1.4), 15, pose_lookdown(pitch=6, yaw=-8, lean=2), (-1.2, 0.0, 2.4), wet=0.1)
    hw = head_of(M)
    # framing rule: no face close-ups. Medium-wide from behind: Briggs's back, the boat on the main hatch beyond
    cl = SHIP @ Vector((-9.6 + 0.25 * E(T), -2.35, ship.zdeck(-9.6) + 1.7))
    cam(cl, SHIP @ Vector((-1.6, -0.6, ship.zdeck(-1.6) + 0.9)), lens=32, fstop=4.0, focus=(hw - cl).length)
    finish()


def S05():   # CUTAWAY: the hold packed with barrels; vapour gathers under the deck (t drives it)
    S.set_cutaway(vapor=0.4 + 0.6 * T)
    c0 = Vector((9, 15, 1.8)); c1 = Vector((6.5, 12.5, 1.0))
    cam(lerp(c0, c1, E(T)), (0.0, -1.0, -0.8), lens=30)
    finish(sat=1.05)


def S06():   # fire risk: the lantern's flame in the hold among the stow (ECU), haze of vapour
    h = S.set_hold(stain=False, lantern_swing=4.0)
    L = h["lantern"]
    p = L + Vector((-1.15 + 0.08 * E(T), -0.4, -0.12))
    cam(p, L + Vector((0.25, 0.25, -0.15)), lens=40, fstop=2.0, focus=(L - p).length)
    finish(bloom=0.5, exposure=-0.6)


def S07():   # under way before the trouble: the full ship, slow track alongside (from the sea)
    d = S.set_deck(time="dusk", rail_gap=None, pumps="intact", sails="full", forehatch_off=False, sea_k=0.8)
    SHIP = d["SHIP"]
    c = SHIP @ Vector((-30 + 6 * E(T), -42, 2.0))
    cam(c, SHIP @ Vector((2, 0, 9)), lens=35)
    finish()


def S08():   # as found: the ship alone, sails torn, nobody at the wheel (locked off, low on the water)
    d = S.set_deck(time="day")
    SHIP = d["SHIP"]
    cam(SHIP @ Vector((40, -48, 1.2)), SHIP @ Vector((0, 0, 8)), lens=40)
    finish(sat=0.95)


def S09():   # Deveau over the open fore hatch, breathing in: no smell of spirit
    d = S.set_deck(time="day")
    SHIP = d["SHIP"]
    xf = ship.FORE_X + 2.6
    dv, M = man("deveau", SHIP, (xf - 1.35, -0.25), 0, pose_sniff, (xf, 0, ship.zdeck(xf)))
    hw = head_of(M)
    # medium-wide from the side: he bends over the hatch, his face turned down into it (no face close-up)
    cl = SHIP @ Vector((xf + 1.5, -2.6, ship.zdeck(xf) + 1.45))
    cam(cl + Vector((0, 0, 0.05 * E(T))), SHIP @ Vector((xf - 0.6, 0, ship.zdeck(xf) + 0.75)), lens=32, fstop=4.0, focus=(hw - cl).length)
    finish(sat=0.95)


def S10():   # the main hatch still battened down (low insert, push in on the wedges), Deveau soft behind
    d = S.set_deck(time="day")
    SHIP = d["SHIP"]; xm = ship.MAIN_HATCH_X
    dv, M = man("deveau", SHIP, (xm + 2.4, 1.8), 200, pose_lookdown(pitch=34, lean=10), (xm, 0, ship.zdeck(xm) + 0.4))
    tgt = SHIP @ Vector((xm, -1.25, ship.zdeck(xm) + 0.42))
    # the whole battened hatch is the subject: high three-quarter, bars and wedges, Deveau at its far edge
    tgt = SHIP @ Vector((xm, 0.1, ship.zdeck(xm) + 0.45))
    c0 = SHIP @ Vector((xm - 3.2, -3.0, ship.zdeck(xm) + 2.6)); c1 = SHIP @ Vector((xm - 2.9, -2.7, ship.zdeck(xm) + 2.45))
    cam(lerp(c0, c1, E(T)), tgt, lens=30, fstop=5.6, focus=(tgt - c1).length)
    finish(sat=0.95)


def S11():   # OAK explainer: a white-oak barrel beside a red-oak one, staves in front
    o = S.set_oak()
    p = Vector((0.0 + 0.1 * E(T), -2.9, 1.25 - 0.05 * E(T)))
    cam(p, (0, 0.1, 0.72), lens=40, fstop=5.6, focus=3.0)
    finish(sat=1.05)


def S12():   # the two staves' cut ends side by side by lantern light; spirit seeping from the red oak, a drop forming
    o = S.set_staves()
    c = (o["white"] + o["red"]) / 2 + Vector((0, 0, -0.008))
    p = c + Vector((-0.02 - 0.02 * E(T), -0.52 + 0.04 * E(T), 0.13))
    cam(p, c + Vector((-0.04, 0, -0.004)), lens=50, fstop=8.0, focus=(c - p).length)
    finish(sat=1.05, exposure=-0.4)


def S13():   # in the hold: the red-oak barrel, its stave dark with spirit, the stain on the ceiling under it
    h = S.set_hold(stain=True, lantern_swing=-3.0)
    r = h.get("red", Vector((0, -1, -2.1)))
    p = Vector((r.x - 1.3 + 0.15 * E(T), 0.0, r.z + 0.3))
    cam(p, r + Vector((0, 0, -0.15)), lens=40, fstop=2.8, focus=(r - p).length)
    finish(exposure=0.9)


def S14():   # the hold, looking along the gap between the stows; lantern swings with the roll
    h = S.set_hold(stain=False, lantern_swing=-8 + 16 * T)
    p = Vector((-3.9 + 0.5 * E(T), 0.0, -1.4))
    cam(p, (4, 0, -1.2), lens=28)
    finish(exposure=0.9)


def S15():   # the rail gap and the empty boat chocks: "ten people climb over the side"
    d = S.set_deck(time="day")
    SHIP = d["SHIP"]
    c0 = SHIP @ Vector((0.6, -1.1, ship.zdeck(0.6) + 1.6)); c1 = SHIP @ Vector((-0.2, -1.6, ship.zdeck(0.6) + 1.5))
    cam(lerp(c0, c1, E(T)), SHIP @ Vector((-1.7, -3.4, ship.zdeck(-1.7) + 0.4)), lens=30)
    finish(sat=0.95)


def S16():   # Deveau turns: something by the mainmast (MCU, his eyeline aft)
    d = S.set_deck(time="day")
    SHIP = d["SHIP"]; px = d["px"]
    dv, M = man("deveau", SHIP, (px + 3.6, 1.6), 180 + 20 * (1 - E(T)), pose_lookdown(pitch=12, yaw=12, lean=3), (px, 0.7, ship.zdeck(px) + 0.4))
    hw = head_of(M)
    # over his shoulder from behind: as his head turns, the mainmast and the pumps come into his eyeline
    cl = SHIP @ Vector((px + 5.1, 2.25, ship.zdeck(px) + 1.8))
    cam(cl, SHIP @ Vector((px + 0.2, 0.8, ship.zdeck(px) + 0.7)), lens=35, fstop=4.0, focus=(SHIP @ Vector((px, 0.7, ship.zdeck(px))) - cl).length)
    finish(sat=0.95)


def S17():   # the port pump taken apart: spear out on deck, upper box off, brake unshipped; Deveau over it
    d = S.set_deck(time="day")
    SHIP = d["SHIP"]; px = d["px"]
    dv, M = man("deveau", SHIP, (px + 1.6, 2.05), 210, pose_lookdown(pitch=40, yaw=-6, lean=14), (px + 0.6, 1.2, ship.zdeck(px)))
    tgt = SHIP @ Vector((px + 1.0, 1.5, ship.zdeck(px) + 0.7))
    c0 = SHIP @ Vector((px + 3.6, -0.1, ship.zdeck(px) + 1.65)); c1 = SHIP @ Vector((px + 3.3, 0.05, ship.zdeck(px) + 1.55))
    cam(lerp(c0, c1, E(T)), tgt, lens=28, fstop=4.0, focus=(tgt - c1).length)
    finish(sat=0.95)


def S18():   # NEW YORK, refit: the empty hold, coal dust in the bilge and shavings, a shaft of daylight
    S.set_hold(stain=False, coal=True, barrels_on=False, lantern_swing=0)
    # subject: the pump's foot standing in the bilge under the hatch light, coal grit and shavings heaped round it
    import skfab, pump as PU
    fr, fms = skfab.model(PU.SCAN_FOOT, height=0.35, name="pumpfoot")
    fr.matrix_world = Matrix.Translation((2.4, 0.0, -2.445)) @ Matrix.Rotation(0.4, 4, 'Z')
    cm = p4.mat("coalheap", (0.014, 0.012, 0.012), rough=0.8)
    import random
    rng = random.Random(11)
    for k in range(1600):
        a = rng.uniform(0, 6.28); r = abs(rng.gauss(0, 0.2)) + 0.07
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rng.uniform(0.002, 0.01),
                                              location=(2.4 + r * math.cos(a), r * math.sin(a), -2.44 + max(0, 0.06 - r * 0.12)))
        bpy.context.active_object.data.materials.append(cm)
    p = Vector((1.15 + 0.15 * E(T), -0.75, -1.85))
    cam(p, (2.4, 0.0, -2.3), lens=40, fstop=4.0, focus=(Vector((2.4, 0, -2.3)) - p).length)
    finish()


def S19():   # MACGREGOR card: the investigation table, papers, the pump drawing; lamp light (no figure)
    t = S.set_table(map_on=True, slate=True, papers=True)
    p = Vector((0.35, -1.75 + 0.08 * E(T), 2.75))          # high angle over the whole table: papers, slate, map, lamp
    cam(p, (0.2, -0.15, t["TZ"]), lens=32, fstop=5.6, focus=2.6)
    finish()


def S20():   # X-ray of the pump: a section through the pump-tree, the upper box in the bore, its flap valve held open by coal grit
    import pump as PU, cutaway as CX
    m = PU.materials()
    sec = CX.section_material()
    tree = ship.cyl("tree", (0, 0, 0.55), (0, 0, 1.25), PU.TREE * 1.08, mat=m["wood"], verts=8)
    bore = ship.cyl("bore", (0, 0, 0.5), (0, 0, 1.3), PU.BORE, mat=sec, verts=32)
    bl = tree.modifiers.new("b", "BOOLEAN"); bl.object = bore; bl.operation = 'DIFFERENCE'; bl.solver = 'EXACT'; bore.hide_render = True
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(tree.evaluated_get(bpy.context.evaluated_depsgraph_get())); tree.modifiers.clear(); tree.data = me
    CX._bisect(tree, 0.0)
    so = tree.modifiers.new("cap", "SOLIDIFY"); so.thickness = 0.0005; so.use_rim = True
    tree.data.materials.append(sec); so.material_offset_rim = 1
    PU.upper_box("xr", Matrix.Translation((0, 0, 0.86)), m, None, valve_open=22, grit=1.4)
    ship.cyl("spear", (0, 0, 1.0), (0, 0, 1.4), 0.022, mat=m["iron"], verts=12)
    water = p4.mat("bilgewater_in_bore", (0.03, 0.04, 0.035), rough=0.05)
    ship.cyl("water", (0, 0, 0.55), (0, 0, 0.78), PU.BORE * 0.99, mat=water, verts=32)
    tbl = ship.wood("wood_table_worn", 0.6, tint=(0.9, 0.7, 0.5), name="t")
    ship.box("table", (0, 0, 0.52), (1.4, 1.0, 0.06), tbl)
    import skfab                                     # beside it, a real ship's pump foot (museum photoscan)
    fr, fms = skfab.model(PU.SCAN_FOOT, height=0.35, name="pumpfoot")
    fr.matrix_world = Matrix.Translation((0.34, 0.12, 0.55)) @ Matrix.Rotation(0.6, 4, 'Z')
    p4.world_color((0.01, 0.007, 0.005))
    p4.light('SPOT', "lamp", 90, (1.0, 0.76, 0.5), loc=(0.15, -0.7, 1.5), target=(0, 0, 0.95), size=0.08, spot=40, blend=0.7)
    p4.light('AREA', "rim", 25, (1.0, 0.8, 0.6), loc=(-0.6, 0.5, 1.3), target=(0, 0, 0.9), size=0.8)
    a = 1.15 + 0.2 * E(T)
    p = Vector((0.15 + 0.85 * math.cos(a), 0.85 * math.sin(a), 1.15))
    cam(p, (0.14, 0.03, 0.82), lens=40, fstop=5.6, focus=(p - Vector((0.1, 0.0, 0.85))).length)
    finish(sat=1.05)


def S21():   # Briggs at night, drawing the spear up out of the pump to see why it won't draw water
    d = S.set_deck(time="night", rail_gap=None, pumps="intact", sails="full", forehatch_off=False, sea_k=1.2)
    SHIP = d["SHIP"]; px = d["px"]
    S.lantern_on_deck(SHIP, (px + 0.9, 0.2, ship.zdeck(px) + 0.01), energy=160)
    sp = (px, 0.7, ship.zdeck(px) + 1.05)
    dv, M = man("briggs", SHIP, (px + 0.55, 0.95), 200, pose_spear(SHIP, (px, 0.7, ship.zdeck(px) + 1.25), (px, 0.7, ship.zdeck(px) + 1.55)),
                (px, 0.7, ship.zdeck(px) + 1.05), wet=0.7)
    hw = head_of(M)
    cl = SHIP @ Vector((px - 1.7, 1.55, ship.zdeck(px) + 1.6))
    cam(cl + Vector((0.08 * E(T), 0, 0)), hw.lerp(SHIP @ Vector(sp), 0.4), lens=40, fstop=2.8, focus=(hw - cl).length)
    finish(exposure=0.2)


def S22():   # the parts on deck by daylight, as found (locked off; a loose rope end stirs)
    d = S.set_deck(time="day")
    SHIP = d["SHIP"]; px = d["px"]
    tgt = SHIP @ Vector((px + 0.75, 1.25, ship.zdeck(px)))
    cam(SHIP @ Vector((px + 0.75, 0.75, ship.zdeck(px) + 2.3)), tgt, lens=35)
    finish(sat=0.95)


def S23():   # RICHARDSON card / the slate: the last entry in chalk
    t = S.set_table(map_on=True, slate=True, papers=True)
    c = t["slate"]
    S.slate_text(c, ["Monday 25th.", "At 5 made the island of", "St. Mary's bearing ESE.", "At 8 Eastern point bore", "SSW 6 miles distant."])
    p = c + Vector((0.02 + 0.03 * E(T), -0.3, 0.36 - 0.04 * E(T)))
    cam(p, c + Vector((0.0, 0.04, 0)), lens=50, fstop=3.2, focus=(p - c).length)
    finish()


def S24():   # the table map: Azores to the found position, high wide, slow push
    t = S.set_table()
    p = lerp((1.75, -0.35, 0.98), (1.65, -0.3, 0.95), E(T))     # low, past the lamp, across the relief
    cam(p, (-0.6, 0.15, t["TZ"] + 0.05), lens=30, fstop=4.0, focus=1.6)
    finish(exposure=0.5)


def S25():   # Santa Maria in relief; the pin at the last sighting; a soft orange band pulses out from it
    t = S.set_table()
    pin = t["last"]
    ring(pin, T)
    p = pin + Vector((-0.12, -0.42, 0.3)) + Vector((0.03 * E(T), 0.06 * E(T), -0.03 * E(T)))
    cam(p, pin + Vector((0, 0.02, 0.02)), lens=60, fstop=4.0, focus=(pin - p).length)
    finish()


def S26():   # the found position, 400 miles east: second pin and band
    t = S.set_table()
    pin = t["found"]
    ring(pin, T)
    p = pin + Vector((-0.2, -0.5, 0.35))
    cam(p + Vector((0.08 * E(T), 0, 0)), pin + Vector((0, 0.03, 0.02)), lens=55, fstop=4.0, focus=(pin - p).length)
    finish()


def S27():   # the drift: wind as fine streaks over the map, the path inked from pin to pin, a model ship on it
    t = S.set_table()
    drift(t, T)
    a, b = t["last"], t["found"]
    mid = (a + b) / 2
    p = mid + Vector((-0.1 - 0.15 * E(T), -1.05, 0.75))
    cam(p, mid + Vector((0, 0.05, 0)), lens=42, fstop=5.6, focus=(mid - p).length)
    finish()


def S28():   # "It could." the model ship arrives at the second pin
    t = S.set_table()
    drift(t, 1.0)
    b = t["found"]
    p = b + Vector((-0.28, -0.36, 0.2))
    cam(p, b + Vector((-0.02, 0, 0.02)), lens=70, fstop=3.5, focus=(b - p).length)
    finish()


def S29():   # within sight of land: the ship at dawn with Santa Maria grey-blue on the horizon
    d = S.set_deck(time="dawn", rail_gap=None, pumps="intact", sails="full", forehatch_off=False, sea_k=1.2)
    SHIP = d["SHIP"]
    S.santa_maria(dist_km=11.0, bearing_deg=200)
    c = SHIP @ Vector((34 - 4 * E(T), 52, 7.5))
    cam(c, SHIP @ Vector((-24, -22, 5)), lens=30)
    finish()


def S30():   # rough weather: night sea, the ship labouring (low, spray)
    d = S.set_deck(time="night", rail_gap=None, pumps="intact", sails="full", forehatch_off=False, sea_k=1.7)
    SHIP = d["SHIP"]
    S.lantern_on_deck(SHIP, (-12.5, 0.0, ship.zdeck(-12.5) + 1.2), energy=40)
    c = SHIP @ Vector((30, -26, 2.0))
    cam(c + Vector((0, 0, 0.3 * math.sin(T * 3))), SHIP @ Vector((0, 0, 4)), lens=40)
    finish(exposure=0.6)


def S31():   # Briggs sounds the well: the rod on its line, drawn up wet, read by the lantern
    d = S.set_deck(time="night", rail_gap=None, pumps="intact", sails="full", forehatch_off=False, sea_k=1.3)
    SHIP = d["SHIP"]; px = d["px"]
    S.lantern_on_deck(SHIP, (px + 0.3, -1.4, ship.zdeck(px) + 0.01), energy=70)
    rz = ship.zdeck(px) + 1.15
    a = (px + 0.55, -1.25, rz + 0.32); b = (px + 0.55, -1.25, rz - 0.1)
    rod(SHIP, a, b, wet=0.55)
    dv, M = man("briggs", SHIP, (px + 0.95, -1.75), 140, pose_rod(SHIP, a, (px + 0.55, -1.25, rz + 0.05)), (px + 0.55, -1.25, rz - 0.1), wet=0.8)
    hw = head_of(M)
    # over his shoulder by lantern light (no face): the rod comes up wet out of the well
    cl = SHIP @ Vector((px + 2.1, -2.3, ship.zdeck(px) + 1.95))       # behind his right shoulder: head and shoulder in frame
    mark = SHIP @ Vector(a).lerp(Vector(b), 0.5)
    cam(cl, mark.lerp(head_of(M), 0.3), lens=28, fstop=4.0, focus=(mark - cl).length)
    finish(exposure=0.2)


def S32():   # CUTAWAY callback: camera sinks from the hatch through the tiers to the bilge, water unseen from above
    S.set_cutaway(water=0.35, vapor=0.0)
    c0 = Vector((1.0, 7.0, 3.2)); c1 = Vector((1.0, 6.0, -2.3))
    cam(lerp(c0, c1, E(T)), lerp((-1.2, -1.0, 0.8), (-1.2, -1.0, -2.4), E(T)), lens=32)
    finish(sat=1.05)


def S33():   # Briggs at the rail at dawn: the island the only land in sight (OTS / MCU)
    d = S.set_deck(time="dawn", rail_gap=None, pumps="intact", sails="full", forehatch_off=False, sea_k=1.1)
    SHIP = d["SHIP"]
    S.santa_maria(dist_km=11.0, bearing_deg=200)
    x = -7.0; hb = ship.half_breadth((x + ship.L / 2) / ship.L, 1.0)
    cap = (x + 0.2, -(hb - 0.03), ship.zdeck(x) + ship.RAIL_H + 0.1)
    dv, M = man("briggs", SHIP, (x, -(hb - 0.55)), 200 + 70, pose_rail(SHIP, cap, yaw=8), (-200, -240, 50), wet=0.5)
    hw = head_of(M)
    cl = SHIP @ Vector((x + 0.9, -(hb - 1.4), ship.zdeck(x) + 1.7))
    cam(cl, SHIP @ Vector((-90, -120, 8)) * 0.0 + hw.lerp(SHIP @ Vector((-200, -240, 30)), 0.02), lens=50, fstop=2.8, focus=(hw - cl).length)
    finish()


def S34():   # back at the table: one reading of the evidence (the two pins, the lamp)
    t = S.set_table()
    drift(t, 1.0)
    b = t["found"]
    p = lerp(b + Vector((-0.55, -0.75, 0.55)), b + Vector((-0.28, -0.4, 0.3)), E(T))   # slow push to the found pin
    cam(p, b + Vector((-0.05, 0.02, 0.02)), lens=50, fstop=4.0, focus=(b - p).length)
    finish()


def S35():   # Deveau reads the sounding rod: three and a half feet in the hold (day)
    d = S.set_deck(time="day")
    SHIP = d["SHIP"]; px = d["px"]
    rz = ship.zdeck(px) + 1.2
    a = (px + 0.6, -1.2, rz + 0.35); b = (px + 0.6, -1.2, rz - 0.15)
    rod(SHIP, a, b, wet=0.5)
    dv, M = man("deveau", SHIP, (px + 1.0, -1.7), 140, pose_rod(SHIP, a, (px + 0.6, -1.2, rz + 0.05)), (px + 0.6, -1.2, rz - 0.1))
    hw = head_of(M)
    # over his right shoulder onto the rod in his hands: the wet mark is the subject, his face is not shown
    cl = SHIP @ Vector((px + 2.15, -2.25, ship.zdeck(px) + 1.95))     # behind his right shoulder: head and shoulder in frame
    mark = SHIP @ Vector(a).lerp(Vector(b), 0.5)
    cam(cl, mark.lerp(head_of(M), 0.3), lens=28, fstop=4.0, focus=(mark - cl).length)
    finish(sat=0.95)


def S36():   # the empty ship sails on; slow pull back
    d = S.set_deck(time="day")
    SHIP = d["SHIP"]
    c = SHIP @ Vector((-34 - 8 * E(T), 30 + 6 * E(T), 3.0))
    cam(c, SHIP @ Vector((0, 0, 7)), lens=38)
    finish(sat=0.92)


# ----------------------------------------------------------------------------- map graphics (3D, on the table)
def ring(pin, t, n=2):
    """Soft filled orange bands spreading from a pin across the map (emissive, feathered annulus on the relief)."""
    for k in range(n):
        ph_ = (t + k / n) % 1.0
        r = 0.02 + 0.16 * ph_
        m = bpy.data.materials.new("band"); m.use_nodes = True; m.blend_method = 'BLEND'
        N = m.node_tree.nodes; L = m.node_tree.links; N.remove(N["Principled BSDF"])
        em = N.new("ShaderNodeEmission"); em.inputs[0].default_value = (1.0, 0.32, 0.04, 1); em.inputs[1].default_value = 1.4
        tr = N.new("ShaderNodeBsdfTransparent")
        tc = N.new("ShaderNodeTexCoord"); gr = N.new("ShaderNodeTexGradient"); gr.gradient_type = 'SPHERICAL'
        mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (1 / r, 1 / r, 1 / r)
        L.new(tc.outputs['Object'], mp.inputs['Vector']); L.new(mp.outputs[0], gr.inputs['Vector'])
        cr = N.new("ShaderNodeValToRGB"); e = cr.color_ramp
        a = 0.55 * (1 - ph_)
        # a filled disc with a soft feathered rim (spherical gradient: 1 at the centre, 0 at radius r)
        e.elements[0].position = 0.0; e.elements[0].color = (0, 0, 0, 1)
        e.elements[1].position = 1.0; e.elements[1].color = (a * 0.8, a * 0.8, a * 0.8, 1)
        el = e.elements.new(0.22); el.color = (a, a, a, 1)
        L.new(gr.outputs['Fac'], cr.inputs['Fac'])
        mx = N.new("ShaderNodeMixShader"); L.new(cr.outputs['Color'], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
        L.new(mx.outputs[0], N["Material Output"].inputs['Surface'])
        bpy.ops.mesh.primitive_plane_add(size=2 * r * 1.3, location=pin + Vector((0, 0, 0.004)))
        o = bpy.context.active_object; o.data.materials.append(m)
        sw = o.modifiers.new("sw", "SHRINKWRAP"); sw.target = bpy.data.objects["map"]; sw.wrap_method = 'PROJECT'
        sw.use_project_z = True; sw.use_negative_direction = True; sw.offset = 0.003
        sub = o.modifiers.new("sub", "SUBSURF"); sub.subdivision_type = 'SIMPLE'; sub.levels = 5; sub.render_levels = 5
        o.modifiers.move(1, 0)
        o.visible_shadow = False


def drift_path(t):
    """The drift track (lon, lat), NE then E with the prevailing westerlies; a model, not the real (unknown) track."""
    pts = [(-24.98, 37.03), (-24.2, 37.25), (-23.1, 37.5), (-21.9, 37.65), (-20.6, 37.9), (-19.4, 38.1), (-18.3, 38.25), (-17.25, 38.33)]
    return pts


def drift(tb, t):
    import ship as SH
    pts = drift_path(t)
    mp = tb["mp"]
    W = [mp(lo, la, lift=0.003) for lo, la in pts]
    # sample along the polyline
    seg = [(W[i + 1] - W[i]).length for i in range(len(W) - 1)]; tot = sum(seg)
    def at(u):
        d = u * tot
        for i, s in enumerate(seg):
            if d <= s:
                return W[i].lerp(W[i + 1], d / s if s else 0), (W[i + 1] - W[i]).normalized()
            d -= s
        return W[-1], (W[-1] - W[-2]).normalized()
    ink = p4.mat("ink", (0.08, 0.02, 0.01), rough=0.4)
    n = max(2, int(60 * t))
    dots = [at(k / 60)[0] for k in range(n + 1)]
    for k in range(0, len(dots) - 1, 2):                    # dashed inked line
        SH.rope("dash", [dots[k], dots[k + 1]], 0.0018, ink)
    # wind streaks: fine raised strokes NE-ward across the map (the historical westerlies), fixed
    import random
    rng = random.Random(4)
    wm = p4.mat("windstroke", (0.55, 0.45, 0.3), rough=0.6)
    for k in range(45):                                   # curved strokes, westerlies veering NE
        lo = rng.uniform(-27.5, -16.8); la = rng.uniform(35.9, 39.6); L = rng.uniform(0.35, 0.8)
        pts = [mp(lo + L * u, la + 0.05 * L * math.sin(u * 3.0) + 0.12 * L * u, 0.004) for u in [i / 8 for i in range(9)]]
        SH.rope("wind", pts, 0.0005, wm)
    # the model ship (a small brigantine at 1:1500 or so) on the path
    p, d = at(t)
    s = SH.build("mini", sails="found", rail_gap=None, wind=Vector((0.3, -1, 0)), detail=False, wet=0.0, hatches_off=False)
    k = 0.0016
    ang = math.atan2(d.y, d.x)
    s["root"].matrix_world = Matrix.Translation(p + Vector((0, 0, 0.0005))) @ Matrix.Rotation(ang, 4, 'Z') @ Matrix.Diagonal((k, k, k, 1))


def rod(SHIP, top, bottom, wet=0.5):
    """An iron sounding rod (graduated, chalked) on a line; the lower part dark and wet to the water mark."""
    import ship as SH
    a = SHIP @ Vector(top); b = SHIP @ Vector(bottom)
    dry = p4.mat("rod_dry", (0.62, 0.6, 0.55), rough=0.55, metal=0.5)
    wetm = p4.mat("rod_wet", (0.04, 0.04, 0.04), rough=0.08, metal=0.5)
    m = a.lerp(b, wet)
    SH.cyl("rod_dry", a, m, 0.012, mat=dry, verts=12)
    SH.cyl("rod_wet", m, b, 0.0122, mat=wetm, verts=12)
    for k in range(1, 8):                                  # graduations
        q = a.lerp(b, k / 8)
        SH.cyl("grad", q, q + (b - a).normalized() * 0.004, 0.0105, mat=p4.mat("notch", (0.02, 0.02, 0.02), 0.5), verts=12)
    SH.rope("rodline", [a, a + Vector((0, 0, 0.6))], 0.004, SH.tarred_rope("rodline_m"))


globals()[SHOT]()
