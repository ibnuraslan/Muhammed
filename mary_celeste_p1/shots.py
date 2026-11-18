"""Part 1 shot table: one entry per shot, in film order. Each fn() builds the set, cast and camera for the
storyboard key frame. vo = the script words under the shot (verbatim, in order, nothing added or changed).

Ship coordinates (lib/ship.py): bow +X, port +Y, starboard -Y, deck at ship.zdeck(x).
Person headings on deck (sets.deck_place): 0 faces starboard, 90 the bow, -90 the stern, 180 port."""
import math, os
import bpy
from mathutils import Vector, Matrix
import env as E
import sets as S
import crew as Cw
import poses as P
import ship

SHOTS = {}
ORDER = []


def shot(sid, vo, dur, desc, sfx, cine=None, card=None):
    def deco(fn):
        SHOTS[sid] = dict(fn=fn, vo=vo, dur=dur, desc=desc, sfx=sfx, cine=cine, card=card); ORDER.append(sid)
        return fn
    return deco


HAIR = float(os.environ.get("HAIR", "1.0"))
ANIM = {}          # set by run_anim.py: {"on": True, "dur": seconds, "actors": [], "actions": {index: fn(dv, M, t)}}


# ============================================================================ set builders
def mc_at_sea(heel=3.0, heading=0.0, dg=None, cut=True, detail=True, **kw):
    """The Mary Celeste with us aboard (cut=True keeps the sea out of her hull)."""
    E.render_setup(samples=96)
    mc = S.mary_celeste(heel=heel, heading=heading, detail=detail)
    hulls = [mc["hull"]]; d = None
    if dg:
        d = S.dei_gratia(**dg); hulls.append(d["hull"])
    S.atlantic(center=kw.pop("center", (-120, -120)), hulls=hulls,
               cut=(mc["M"].translation.x, mc["M"].translation.y, ship.L / 2 - 0.4, ship.B / 2 - 0.15) if cut else None, **kw)
    return mc, d


def dg_at_sea(heading=0.0, heel=-4.0, mc=None, detail=True, cut=True, **kw):
    """The Dei Gratia with us aboard; mc = dict(heading, loc) puts the Mary Celeste out on the sea."""
    E.render_setup(samples=96)
    d = S.dei_gratia(heading=heading, heel=heel, detail=detail)
    hulls = [d["hull"]]; m = None
    if mc:
        m = S.mary_celeste(heel=mc.get("heel", 6.0), heading=mc["heading"], loc=mc["loc"], detail=False); hulls.append(m["hull"])
    S.atlantic(center=kw.pop("center", (80, -60)), hulls=hulls,
               cut=(0.0, 0.0, ship.L / 2 - 0.4, ship.B / 2 - 0.15) if cut else None, **kw)
    return d, m


def person(kind, M, pose, look_w=None, density=None, seat=False):
    """kind: 'deveau' | 'morehouse' | 0..2 (sailor). pose(dv, M) poses the rig (rig frame) before finish."""
    if kind == "deveau":
        dv = Cw.deveau()
    elif kind == "morehouse":
        dv = Cw.morehouse()
    else:
        dv = Cw.sailor(int(kind))
    if seat:
        # seated: fold the legs, find how far the boots now hang below the rig origin, and lift the placement so
        # the soles rest on the floor (z of M); hand targets are then computed against the corrected placement
        import human as H
        H.pose_sit(dv.h, lean=0)
        bpy.context.view_layer.update()
        low = min(float(H._world_verts(o)[:, 2].min()) for o in dv.h.parts if o.type == 'MESH' and len(o.data.polygons))
        M = M @ Matrix.Translation((0, 0, -low))
        H.reset_pose(dv.h)
    pose(dv, M)
    bpy.context.view_layer.update()
    dv.hip_w = M @ ((dv.h.bone_head("upperleg01.L") + dv.h.bone_head("upperleg01.R")) / 2)
    dv.place_M = M
    if ANIM.get("on"):
        # live rig for the final render: key the pose over the shot with a breathing/idle layer and blinks,
        # grow the hair on the first pose and ride it on the head bone (p1/anim.py)
        import anim as A
        A.live(dv, M, pose, look_w, ANIM["dur"], density=HAIR if density is None else density, seed=len(ANIM["actors"]),
               action=ANIM.get("actions", {}).get(len(ANIM["actors"])))
        ANIM["actors"].append(dv)
        return dv
    dv.finish(look_at=look_w, place=M, density=HAIR if density is None else density)
    return dv


def A_ease(u):
    u = min(max(u, 0.0), 1.0); return u * u * (3 - 2 * u)


def heading_to(px, py, tx, ty):
    """Heading (deg) that turns a person at (px, py) to face (tx, ty): the rig faces (sin h, -cos h)."""
    return math.degrees(math.atan2(tx - px, -(ty - py)))


def head_w(M, up=1.64, fwd=0.06):
    return M @ Vector((0, -fwd, up))


def relaxed(pitch=0.0, yaw=0.0, lean=3, weight="L", brow=0.0, lids=0.0):
    def f(dv, M):
        Cw.stand_relaxed(dv, pitch=pitch, yaw=yaw, lean=lean, weight=weight)
        if brow:
            dv.brow_knit(brow)
        if lids:
            dv.lids(lids)
    return f


def seat_chest(dv):
    """A sea chest under a seated man, its lid just under his seat (hip joints ~0.1 m above the lid)."""
    import interiors as I
    for o in [o for o in bpy.data.objects if o.name.startswith("wooden_stool")]:
        o.hide_render = True
        for c in o.children_recursive:
            c.hide_render = True
    h = dv.hip_w; top = h.z - 0.11
    m = I.wood("wood_table_worn", 1.5, wet=0.2, tint=(0.62, 0.42, 0.28), name="seatchest")
    th = dv.place_M.to_euler().z
    ship.box("seat_chest", (h.x, h.y, top / 2), (0.52, 0.42, top), m, rot=(0, 0, th), bevel=0.01)


def crew_in_boat(b, rowers=(0, 1), cox="deveau", look=None):
    """Two men rowing on the thwarts (facing aft, hands on the oar looms) and one at the stern sheets facing forward."""
    import smallboat as SB, human as H
    Bm = b["root"].matrix_world
    for k, who in enumerate(rowers):
        th = b["thwarts"][1 + k]
        Mp = Bm @ Matrix.Translation((th.x, 0, SB.GUN - SB.DEPTH + 0.115)) @ Matrix.Rotation(math.radians(-90), 4, 'Z')
        handles = [o for o in b["oars"] if abs(o[1].x - (th.x - 0.32)) < 0.05]
        def row(dv, Mx, handles=handles):
            H.pose_sit(dv.h, lean=26, hands="knees"); P.head(dv.h, pitch=-8)
            if len(handles) == 2:
                (iL, _), (iR, _) = sorted(handles, key=lambda h: -h[0].y)
                Cw.hands_on(dv, Mx, left_w=Bm @ iR, right_w=Bm @ iL, elbow_l=(0.8, 0.0, -0.6), elbow_r=(-0.8, 0.0, -0.6))
        person(who, Mp, row, look_w=look, density=0.35, seat=True)
    Mp = Bm @ Matrix.Translation((-SB.LB / 2 + 0.75, 0, SB.GUN - SB.DEPTH + 0.115)) @ Matrix.Rotation(math.radians(90), 4, 'Z')
    def cx(dv, Mx):
        H.pose_sit(dv.h, lean=8, hands="knees"); P.head(dv.h, pitch=-4)
    person(cox, Mp, cx, look_w=look, density=0.35, seat=True)


def soft_band(M, x, y, rx, ry, color=(1.0, 0.45, 0.12), strength=1.5, z=0.012, name="softband"):
    """The house highlight on a surface: a filled soft orange band (elliptical ring, soft inner and outer edge)."""
    import explain as X
    V = []; F = []; n = 64
    for i in range(n):
        t = 2 * math.pi * i / n
        for k in (0.55, 1.0, 1.35):
            V.append(tuple(S.deck_point(M, x + rx * k * math.cos(t), y + ry * k * math.sin(t), z)))
    for i in range(n):
        j = (i + 1) % n
        F.append([3 * i, 3 * j, 3 * j + 1, 3 * i + 1]); F.append([3 * i + 1, 3 * j + 1, 3 * j + 2, 3 * i + 2])
    o = ship.mesh_obj(name, V, F, None, smooth=True)
    ca = o.data.color_attributes.new("a", 'FLOAT_COLOR', 'POINT')
    for i in range(len(V)):
        v = 1.0 if i % 3 == 1 else 0.0
        ca.data[i].color = (v, v, v, 1)
    m = bpy.data.materials.new(name + "_m"); m.use_nodes = True; N = m.node_tree.nodes; Lk = m.node_tree.links
    N.remove(N["Principled BSDF"])
    at = N.new("ShaderNodeAttribute"); at.attribute_name = "a"
    em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (*color, 1); em.inputs['Strength'].default_value = strength
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    Lk.new(at.outputs['Fac'], mx.inputs[0]); Lk.new(tr.outputs[0], mx.inputs[1]); Lk.new(em.outputs[0], mx.inputs[2])
    Lk.new(mx.outputs[0], N["Material Output"].inputs['Surface'])
    o.data.materials.append(m); o.visible_shadow = False
    return o


def clay_people(points, M=None):
    """Atrium device for people who are only mentioned: plain grey clay figures (MakeHuman bodies, no clothes
    detail, no hair, no faces painted), standing still. points: list of (x, y, heading) in ship coords."""
    import human as H
    clay = E.principled("clay", (0.33, 0.32, 0.3), rough=0.75, **{"Subsurface Weight": 0.05})
    shapes = [dict(gender=1.0, years=32, height=0.55), dict(gender=1.0, years=24, height=0.5), dict(gender=0.0, years=30, height=0.42),
              dict(gender=1.0, years=1.6, height=0.5), dict(gender=1.0, years=40, height=0.5), dict(gender=1.0, years=27, height=0.6),
              dict(gender=1.0, years=22, height=0.48), dict(gender=1.0, years=35, height=0.52), dict(gender=1.0, years=29, height=0.5),
              dict(gender=1.0, years=45, height=0.47)]
    out = []
    for k, (x, y, hd) in enumerate(points):
        sh = shapes[k % len(shapes)]
        h = H.Human(f"Clay{k}", eyebrows=None, eyelashes=None, skin=None, eyes=False, muscle=0.5, weight=0.5, **sh)
        h.body.data.materials[0] = clay
        P.stand(h, lean=2, weight="L" if k % 2 else "R")
        P.arm_down(h, "L", out=0.1, fwd=0.04, bend=10); P.arm_down(h, "R", out=0.1, fwd=0.04, bend=10)
        P.rest_hand(h, "L"); P.rest_hand(h, "R")
        Mp = S.deck_place(M, x, y, hd) if M is not None else Matrix.Translation((x, y, 0)) @ Matrix.Rotation(math.radians(hd), 4, 'Z')
        H.bake_pose(h)
        for o in h.parts:
            o.matrix_world = Mp @ o.matrix_world
        h.arm.hide_render = True
        out.append(h)
    return out


# ============================================================================ 1. the boarding (cold open)
@shot("S01", "Oliver Deveau steps onto", 2.4,
      "Low wide from the sea: the Mary Celeste moving through the swell, sails drawing; the Dei Gratia's boat alongside her waist.",
      ["sea wash", "hull creak", "canvas flap", "oars knock in the tholes"])
def s01():
    mc, _ = mc_at_sea(heel=4.0, heading=20.0, cut=False, center=(0, 0))
    M = mc["M"]
    import smallboat as SB
    b = SB.build("DGboat", oars_out=False)
    b["root"].matrix_world = M @ Matrix.Translation((-1.6, -ship.B / 2 - 1.3, 0.0)) @ Matrix.Rotation(math.radians(4), 4, 'Z')
    bpy.context.view_layer.update()
    Bm = b["root"].matrix_world
    for k, (xs, hd) in enumerate(((-1.25, 90), (-0.1, 90))):
        Mp = Bm @ Matrix.Translation((xs, 0, b["thwarts"][0].z + 0.01)) @ Matrix.Rotation(math.radians(hd), 4, 'Z')
        def sit(dv, Mx):
            import human as H
            H.pose_sit(dv.h, lean=12, hands="knees")
            P.head(dv.h, pitch=-10, yaw=-20)
        person(k, Bm @ Matrix.Translation((xs + 0.4, 0, SB.GUN - SB.DEPTH + 0.115)) @ Matrix.Rotation(math.radians(hd), 4, 'Z'), sit,
               density=0.25, seat=True)
    cam = M @ Vector((26.0, -44.0, 0)); cam.z = 2.0
    E.camera(cam, M @ Vector((-2.0, 0.0, 8.5)), lens=32, fstop=8, roll=1.5)


@shot("S02", "a ship that's still moving.", 2.6,
      "On the Mary Celeste's deck: Deveau steps in through the gap in the rail, one hand on the bulwark end, the sea "
      "running past behind him. Camera at chest height on the deck, handheld sway.",
      ["boot on wet planks", "hand slaps the rail", "sea rush"], card="person:OLIVER DEVEAU|FIRST MATE, DEI GRATIA")
def s02():
    mc, _ = mc_at_sea(heel=3.0)
    M = mc["M"]
    gx = (S.GAP[0] + S.GAP[1]) / 2
    hb = ship.half_breadth((gx + ship.L / 2) / ship.L, 1.0)
    Mp = S.deck_place(M, gx + 0.2, -hb + 0.55, 180 + 15)          # just inboard of the gap, facing port (inboard)
    cap = M @ Vector((S.GAP[1] + 0.18, -(ship.half_breadth((S.GAP[1] + ship.L / 2) / ship.L, 1.0) - 0.03),
                      ship.zdeck(S.GAP[1]) + ship.RAIL_H + 0.1))
    def pose(dv, Mx):
        Cw.stand_relaxed(dv, pitch=8, yaw=-12, lean=10, weight="R")
        Cw.hands_on(dv, Mx, left_w=None, right_w=cap, elbow_r=(-0.8, 0.5, -0.4), grip=False, curl=34)
        dv.brow_knit(0.5)
    look = S.deck_point(M, -4.0, 0.6, 1.0)
    person("deveau", Mp, pose, look_w=look)
    hw = head_w(Mp)
    cam = S.deck_point(M, gx - 2.6, -hb + 2.7, 1.55)
    E.camera(cam, hw + Vector((0, 0, -0.18)), lens=40, fstop=2.8, focus=(hw - cam).length)


@shot("S03", "He searches the deck,", 1.6,
      "From behind, Deveau stops on the wet deck by the mainmast and the pumps and looks left, then right.",
      ["footsteps on wet deck", "rigging creak", "slack sail flogging"])
def s03():
    mc, _ = mc_at_sea(heel=3.0)
    M = mc["M"]
    Mp = S.deck_place(M, -3.2, 1.6, -90)
    def pose(dv, Mx):
        Cw.stand_relaxed(dv, pitch=4, yaw=0, lean=4, weight="R")     # stopped, scanning the deck (run_anim turns his head)
    person("deveau", Mp, pose, look_w=S.deck_point(M, -9, -1.5, 1.2))
    cam = S.deck_point(M, -0.9, 1.1, 1.05)
    E.camera(cam, S.deck_point(M, -6.5, 1.8, 1.15), lens=40, fstop=3.2, focus=2.4)


@shot("S04", "then goes below.", 1.6,
      "High angle over the companion: Deveau, head and shoulders, going down the ladder into the dark of the after cabin.",
      ["ladder creak", "boots on rungs", "sea muffles"])
def s04():
    mc, _ = mc_at_sea(heel=3.0)
    M = mc["M"]
    x0 = -ship.L / 2 + 3.2; cx = x0 + 4.7
    open_companion(mc, "MC")
    zc = ship.zdeck(cx)
    Mp = M @ Matrix.Translation((cx - 0.05, 1.2, zc - 0.55)) @ Matrix.Rotation(math.radians(90 + 180), 4, 'Z')
    rung = M @ Vector((cx - 0.25, 1.2 + 0.2, zc + 0.9))
    def pose(dv, Mx):
        Cw.stand_relaxed(dv, pitch=30, yaw=0, lean=8)
        Cw.hands_on(dv, Mx, left_w=rung - M.to_3x3() @ Vector((0, 0.42, 0)), right_w=rung + M.to_3x3() @ Vector((0, 0.05, 0)),
                    elbow_l=(0.8, 0.3, -0.5), elbow_r=(-0.8, 0.3, -0.5))
    person("deveau", Mp, pose, look_w=M @ Vector((cx, 1.2, zc - 2.0)))
    cam = M @ Vector((cx + 1.9, 2.6, zc + 2.6))
    E.camera(cam, M @ Vector((cx - 0.1, 1.2, zc + 0.7)), lens=32, fstop=4)


def open_companion(sh, tag):
    """The companion over the after cabin stairs, open: its sliding cover pushed back, a ladder down into the dark."""
    x0 = -ship.L / 2 + 3.2; cx = x0 + 4.7
    E.hide([f"{tag}_companion"])
    wd = sh["mats"]["deckwood"]; dk = sh["mats"]["dark"]
    zc = ship.zdeck(cx)
    made = []
    for sy in (-1, 1):
        made.append(ship.box("comp_side", (cx, 1.2 + sy * 0.45, zc + 0.95), (0.9, 0.06, 0.8), sh["mats"]["lining"]))
    made.append(ship.box("comp_fwd", (cx + 0.45, 1.2, zc + 0.95), (0.06, 0.96, 0.8), sh["mats"]["lining"]))
    made.append(ship.box("comp_slide", (cx - 0.25, 1.2, zc + 1.39), (0.6, 1.0, 0.05), wd))
    made.append(ship.box("comp_well", (cx, 1.2, zc - 0.4), (0.84, 0.84, 2.6), dk))
    for k in range(5):
        made.append(ship.box("rung", (cx - 0.25, 1.2, zc + 0.9 - k * 0.3), (0.05, 0.6, 0.04), wd))
    S._parent(made, sh["root"])
    return cx


# ============================================================================ 2. the captain's cabin
def cabin_with_deveau(cam_fn, lantern_side="L", **kw):
    import interiors as I
    E.render_setup(samples=128)
    a = I.captain_cabin()
    M = Matrix.Translation((0.22, 0.3, 0.0)) @ Matrix.Rotation(math.radians(223), 4, 'Z')
    dv = Cw.deveau(wet=0.55)
    P.cabin(dv, M, (0.48, I.CAB["BY0"] - 0.02, I.CAB["BOARD"] + 0.045), (-0.3, 0.62, 1.40), lantern_side=lantern_side)
    bpy.context.view_layer.update()
    grip_local = P.palm_point(dv.h, lantern_side)
    dv.finish(look_at=a["child"] + Vector((-0.05, 0, 0)), place=M, density=HAIR)
    lan = I.lantern(M @ grip_local + Vector((0, 0, 0.005)), energy=55.0)
    head = M @ Vector((0, -0.05, 1.66))
    E.area("lantern_bounce", lan["center"].lerp(head, 0.35) + Vector((0, 0, -0.15)), head, 4.0, size=0.35, color=(1.0, 0.62, 0.36))
    cam_fn(a, M, head, lan)
    return a


@shot("S05", "In the captain's cabin, the bedding is wet.", 3.5,
      "The captain's cabin from the doorway: Deveau holds the lantern over the berth; soaked bedding, water on the floor, "
      "grey daylight through the skylight.", ["water drip", "lantern creak", "hull groan"], cine={"exposure": 0.15})
def s05():
    def cam(a, M, head, lan):
        c = Vector((-1.6, 0.05, 1.72))
        aim = head.lerp(a["child"], 0.62) + Vector((0.16, -0.12, 0.0))
        E.camera(c, aim, lens=21, fstop=3.5, focus=(head - c).length, roll=-1.0)
    cabin_with_deveau(cam)


@shot("S06", "On the bed is an impression", 2.2,
      "Top-down over the berth: the small hollow pressed into the wet sheet, the lantern's light sliding across it.",
      ["lantern swing creak", "drip"], cine={"exposure": 0.2})
def s06():
    def cam(a, M, head, lan):
        c = a["child"] + Vector((-0.85, -0.55, 0.85))
        E.camera(c, a["child"] + Vector((0.08, 0.03, 0)), lens=38, fstop=3.2)
    cabin_with_deveau(cam)


@shot("S07", "that looks to him as though a child has been lying there.", 4.2,
      "Deveau, leaning over the berth with the lantern held up: he looks down at the hollow, brows drawn. Slow push-in.",
      ["breath", "lantern creak", "sea against the hull"], cine={"exposure": 0.15})
def s07():
    def cam(a, M, head, lan):
        c = head + Vector((-0.95, -0.55, -0.12))
        E.camera(c, head + Vector((0.0, 0.0, -0.1)), lens=45, fstop=2.4, focus=(head - c).length)
    cabin_with_deveau(cam)


@shot("S08", "He finds no child.", 1.6,
      "Over Deveau's shoulder: the lantern lifted toward the dark end of the cabin, the sea chest and the empty corner.",
      ["lantern creak", "footstep in water"], cine={"exposure": 0.55})
def s08():
    import interiors as I
    E.render_setup(samples=128)
    a = I.captain_cabin()
    M = Matrix.Translation((-0.4, -0.1, 0.0)) @ Matrix.Rotation(math.radians(heading_to(-0.4, -0.1, 1.2, 0.9)), 4, 'Z')
    lw = M @ Vector((-0.28, -0.42, 1.35))
    def pose(dv, Mx):
        Cw.stand_relaxed(dv, pitch=6, yaw=-6, lean=2)
        P.hand_reach(dv.h, "R", Mx.inverted() @ lw, elbow=(-0.8, 0.3, -0.6)); P.grip(dv.h, "R")
        dv.brow_knit(0.6)
    dv = person("deveau", M, pose, look_w=Vector((1.3, 0.9, 0.5)))
    lan = I.lantern(lw + Vector((0, 0, -0.02)), energy=110.0)
    head = M @ Vector((0, -0.05, 1.66))
    E.area("lantern_bounce", lan["center"].lerp(head, 0.4) + Vector((0, 0, -0.1)), head, 5.0, size=0.35, color=(1.0, 0.62, 0.36))
    c = M @ Vector((-0.45, 0.85, 1.75))
    E.camera(c, Vector((1.2, 0.75, 0.8)), lens=26, fstop=2.8, focus=(Vector((1.2, 0.9, 0.5)) - c).length)


@shot("S09", "He finds no one.", 1.8,
      "The empty cabin, locked off: only the skylight's grey light on the wet bed. Deveau has gone.",
      ["drip", "hull creak", "distant sea"], cine={"exposure": 0.6})
def s09():
    import interiors as I
    E.render_setup(samples=128)
    a = I.captain_cabin(skylight=800)
    c = Vector((1.55, -1.1, 1.45))
    E.camera(c, Vector((-0.9, 0.85, 0.6)), lens=20, fstop=5)


# ============================================================================ 3. the rail and the missing boat
@shot("S10", "Back on deck, a section of railing has been taken out and laid flat.", 5.5,
      "Low along the deck: the rail section lying flat on the planks in the foreground; beyond it the gap in the bulwark "
      "and Deveau standing at it, hand on the rail end.", ["sea through the gap", "rope slap", "wood knock"])
def s10():
    mc, d = mc_at_sea(heel=2.5, dg=dict(heading=205.0, loc=(-330.0, -300.0, -0.1), detail=False, heel=3.0))
    M = mc["M"]; gap = S.GAP
    hb0 = ship.half_breadth((gap[0] + ship.L / 2) / ship.L, 1.0)
    Mp = S.deck_place(M, -3.45, -3.05, -35 + 90)
    cap = M @ Vector((gap[0] - 0.22, -(hb0 - 0.03), ship.zdeck(gap[0]) + ship.RAIL_H + 0.1))
    def pose(dv, Mx):
        P.stand(dv.h, lean=6, weight="R", twist=-3); P.head(dv.h, pitch=22, yaw=10, tilt=2)
        dv.lids(0.7); dv.brow_knit(0.8)
        P.hand_reach(dv.h, "R", Mx.inverted() @ cap, elbow=(-0.8, 0.4, -0.5)); P.rest_hand(dv.h, "R", curl=26)
        P.arm_down(dv.h, "L", out=0.1, fwd=0.02, bend=14); P.rest_hand(dv.h, "L", curl=24)
    person("deveau", Mp, pose, look_w=S.deck_point(M, -1.4, -2.9, 0))
    cam = S.deck_point(M, 1.6, -2.1, 0.42)
    E.camera(cam, S.deck_point(M, -2.6, -3.3, 0.55), lens=28, fstop=5.6)


@shot("S11", "There's a gap wide enough to launch a small boat.", 3.9,
      "Through the gap: the sea running past at deck level; filled soft orange bands mark the opening on the deck edge.",
      ["sea rush", "water slap on the hull"])
def s11():
    import explain as X
    mc, _ = mc_at_sea(heel=2.5)
    M = mc["M"]; gap = S.GAP
    gx = (gap[0] + gap[1]) / 2
    hb = ship.half_breadth((gx + ship.L / 2) / ship.L, 1.0)
    # soft orange filled bands on the deck at the gap (the house highlight)
    soft_band(M, gx, -hb + 0.35, 1.05, 0.32)
    cam = S.deck_point(M, gx + 0.3, -hb + 3.4, 1.5)
    E.camera(cam, S.deck_point(M, gx, -hb - 6.0, -0.9), lens=26, fstop=6)


@shot("S12", "The ship's boat is gone.", 2.2,
      "High over the main hatch: the two empty boat chocks; a glass ghost of the missing boat sits on them, then fades.",
      ["wind gust", "slack line taps the hatch"])
def s12():
    import explain as X, smallboat as SB
    mc, _ = mc_at_sea(heel=2.0)
    M = mc["M"]
    b = SB.build("ghostboat", oars_out=False)
    g = X.ghost_mat("ghostboat_m", edge=(1.0, 0.55, 0.2), alpha=0.06)
    for o in b["coll"].objects:
        if o.type in ('MESH', 'CURVE'):
            o.data.materials.clear(); o.data.materials.append(g); o.visible_shadow = False
    xm = ship.MAIN_HATCH_X
    b["root"].matrix_world = M @ Matrix.Translation((xm, 0, ship.zdeck(xm) + 0.75 - (SB.GUN - SB.DEPTH))) @ Matrix.Rotation(math.radians(90), 4, 'Z')
    cam = S.deck_point(M, xm + 3.2, -4.6, 5.2)
    E.camera(cam, S.deck_point(M, xm, 0, 0.5), lens=30, fstop=8)


@shot("S13", "Deveau goes back for two men.", 2.6,
      "Wide on the sea: the Dei Gratia's boat pulling back across to her, two men at the oars, Deveau at the tiller.",
      ["oars dip and pull", "sea wash"])
def s13():
    E.render_setup(samples=96)
    d = S.dei_gratia(heading=200.0, loc=(-60, 40, -0.2), heel=2.0, detail=False, sails="full")
    mc = S.mary_celeste(heel=4.0, heading=15.0, loc=(60, -10, -0.32), detail=False)
    import smallboat as SB
    b = SB.build("DGboat", oars_out=True)
    b["root"].matrix_world = Matrix.Translation((-8, 8, 0.0)) @ Matrix.Rotation(math.radians(150), 4, 'Z')
    crew_in_boat(b, rowers=(0, 1), cox="deveau", look=Vector((-60, 40, 3)))
    S.atlantic(center=(0, 0), hulls=(d["hull"], mc["hull"], b["hull"]))
    cam = Vector((2, -6, 2.0))
    E.camera(cam, Vector((-14, 14, 3)), lens=38, fstop=8)


@shot("S14", "Then the three of them climb aboard", 2.0,
      "On the Mary Celeste's deck by the gap: Deveau and the two men, one still stepping in through the gap.",
      ["boots land on deck", "bag dropped", "rope coil thrown down"])
def s14():
    mc, _ = mc_at_sea(heel=3.0)
    M = mc["M"]; gx = (S.GAP[0] + S.GAP[1]) / 2
    hb = ship.half_breadth((gx + ship.L / 2) / ship.L, 1.0)
    # Deveau turned aft, pointing the way with his left arm; one man just in through the gap with a hand on the
    # bulwark end; the other looking aloft at the sails
    def dpose(dv, Mx):
        Cw.stand_relaxed(dv, pitch=-2, yaw=18, lean=4, weight="R")
        P.hand_reach(dv.h, "L", Mx.inverted() @ S.deck_point(M, gx - 4.5, -hb + 2.6, 1.55), elbow=(0.6, 0.3, -0.7))
        P.rest_hand(dv.h, "L", curl=12)
    person("deveau", S.deck_place(M, gx - 1.5, -hb + 1.7, 180 - 55), dpose, look_w=S.deck_point(M, gx - 6, -1, 1.4))
    capE = M @ Vector((S.GAP[1] + 0.18, -(ship.half_breadth((S.GAP[1] + ship.L / 2) / ship.L, 1.0) - 0.03),
                       ship.zdeck(S.GAP[1]) + ship.RAIL_H + 0.1))
    def p0(dv, Mx):
        Cw.stand_relaxed(dv, pitch=14, yaw=-8, lean=10, weight="L")
        Cw.hands_on(dv, Mx, left_w=None, right_w=capE, elbow_r=(-0.8, 0.5, -0.4), grip=False, curl=34)
    person(0, S.deck_place(M, S.GAP[1] - 0.35, -hb + 0.55, 180 + 25), p0, look_w=S.deck_point(M, gx - 1.5, -hb + 1.7, 1.0))
    person(1, S.deck_place(M, gx + 0.6, -hb + 2.3, 180 + 70), relaxed(pitch=-28, yaw=10, weight="R"), look_w=M @ Vector((ship.MAIN_X, 0, 16)))
    cam = S.deck_point(M, gx + 2.2, 2.2, 1.6)
    E.camera(cam, S.deck_point(M, gx - 0.6, -hb + 1.3, 1.15), lens=30, fstop=4)


@shot("S15", "and sail the ship to Gibraltar.", 3.0,
      "Wide from astern: the Mary Celeste under her remaining sail heading east, one man at her wheel.",
      ["canvas fills", "bow wave", "hull creak"])
def s15():
    mc, _ = mc_at_sea(heel=5.0, heading=80.0, cut=False, center=(0, 0))
    M = mc["M"]; xw = -ship.L / 2 + 1.7
    person("deveau", S.deck_place(M, xw - 0.55, 0, 90), relaxed(pitch=-4), look_w=S.deck_point(M, 20, 0, 3), density=0.3)
    cam = M @ Vector((-60.0, -26.0, 0)); cam.z = 3.5
    E.camera(cam, M @ Vector((0.0, 0.0, 6.0)), lens=45, fstop=8, roll=-1)


@shot("S16", "Ten people had been on the Mary Celeste.", 3.2,
      "High wide over her deck: ten plain grey clay figures standing where the crew would have been (Atrium device for "
      "people only mentioned): the captain, his wife, their small daughter and seven men.",
      ["low wind", "a single bell-like rigging ping", "sea"])
def s16():
    mc, _ = mc_at_sea(heel=2.0)
    M = mc["M"]
    # on the open deck only (clear of the cabin trunk, hatches, pumps, masts and the galley house)
    pts = [(-12.0, -2.8, 95), (-11.3, -2.95, 100), (-10.75, -2.75, 115), (-14.7, 0.0, 90), (-5.5, 2.4, 160), (-2.0, -2.6, 70),
           (0.9, -2.7, 90), (5.5, 2.5, 110), (8.2, -2.0, 70), (-8.0, -2.9, 95)]
    clay_people(pts, M)
    cam = S.deck_point(M, 0.6, -2.9, 2.3)
    E.camera(cam, S.deck_point(M, -8.5, 0.2, 0.9), lens=24, fstop=8)


@shot("S17", "Whatever made them leave, the ship survived it.", 3.6,
      "The same high wide, now empty: the deck, the hatches, the sails still working. Slow push-in.",
      ["wind", "rigging creak", "sea"])
def s17():
    mc, _ = mc_at_sea(heel=2.0)
    M = mc["M"]
    cam = S.deck_point(M, 0.2, -2.8, 2.2)
    E.camera(cam, S.deck_point(M, -8.5, 0.2, 0.9), lens=26, fstop=8)


# ============================================================================ 4. the Dei Gratia, 4 December 1872
@shot("S18", "On December fourth, 1872,", 2.0,
      "Establishing: the Dei Gratia under full sail on the open Atlantic, low and wide from the sea.",
      ["ocean bed", "bow wave", "canvas"], card="place:ATLANTIC OCEAN|DECEMBER 4, 1872")
def s18():
    E.render_setup(samples=96)
    d = S.dei_gratia(heading=95.0, loc=(0, 0, -0.2), heel=-5.0, detail=False)
    S.atlantic(center=(0, 0), hulls=(d["hull"],))
    cam = Vector((40, -48, 1.8))
    E.camera(cam, Vector((0, 0, 9.0)), lens=30, fstop=8, roll=1)


@shot("S19", "Deveau is first mate aboard the Dei Gratia,", 2.8,
      "Below in the Dei Gratia's mate's cabin, lamp lit: Deveau seated at the table, writing up the log.",
      ["pen scratch", "lamp creak", "hull work"], cine={"exposure": 0.6})
def s19():
    import interiors as I, human as H
    E.render_setup(samples=128)
    a = I.mate_cabin()
    t = a["table"]
    M = Matrix.Translation((t.x + 0.05, t.y + 0.62, 0.0)) @ Matrix.Rotation(math.radians(0), 4, 'Z')
    def pose(dv, Mx):
        H.pose_sit(dv.h, lean=22, hands="knees")
        P.head(dv.h, pitch=32)
        Cw.hands_on(dv, Mx, left_w=t + Vector((0.2, 0.1, 0.07)), right_w=t + Vector((-0.05, 0.06, 0.07)),
                    elbow_l=(0.8, 0.5, -0.6), elbow_r=(-0.8, 0.5, -0.6), grip=False, curl=30)
    # seat height: the stool top ~0.45
    dv = person("deveau", M, pose, look_w=t + Vector((-0.1, 0.02, 0.05)), seat=True)
    seat_chest(dv)
    c = Vector((t.x - 1.0, t.y - 0.45, 1.5))
    hw = dv.place_M @ Vector((0, -0.16, 1.6))
    E.camera(c, hw.lerp(t, 0.3) + Vector((0, 0, 0.0)), lens=26, fstop=2.8, focus=(hw - c).length)


@shot("S20", "a cargo ship crossing the Atlantic.", 2.4,
      "The Dei Gratia from her quarter, long lens: barrels lashed on deck, men small at the rail.", ["sea", "hull creak", "rigging"])
def s20():
    E.render_setup(samples=96)
    d = S.dei_gratia(heading=95.0, loc=(0, 0, -0.2), heel=-5.0, detail=True)
    S.atlantic(center=(0, 0), hulls=(d["hull"],))
    cam = d["M"] @ Vector((-55.0, 35.0, 0)); cam.z = 4.0
    E.camera(cam, d["M"] @ Vector((0, 0, 5.0)), lens=55, fstop=8)


@shot("S21", "Shortly after noon, the man at the wheel", 2.4,
      "The Dei Gratia's helmsman at the wheel, both hands on the spokes; he narrows his eyes at something off the bow.",
      ["wheel creak", "wind in rigging"])
def s21():
    d, _ = dg_at_sea(heading=95.0)
    M = d["M"]; xw = -ship.L / 2 + 1.7; zc = ship.zdeck(xw) + 1.25
    Mp = S.deck_place(M, xw - 0.5, 0.0, 90)
    a = math.radians(95)
    L = M @ Vector((xw, 0.62 * math.sin(a), zc + 0.62 * math.cos(a))); R = M @ Vector((xw, -0.62 * math.sin(a), zc + 0.62 * math.cos(a)))
    def pose(dv, Mx):
        Cw.stand_relaxed(dv, pitch=-3, yaw=-10, lean=6)
        Cw.hands_on(dv, Mx, left_w=L, right_w=R, elbow_l=(0.9, 0.2, -0.5), elbow_r=(-0.9, 0.2, -0.5))
        dv.lids(0.35); dv.brow_knit(0.6)
    person(2, Mp, pose, look_w=M @ Vector((200, -60, 3)))
    hw = head_w(Mp)
    c = M @ Vector((xw + 1.9, -1.2, ship.zdeck(xw) + 1.55))
    E.camera(c, hw + Vector((0, 0, -0.12)), lens=45, fstop=2.8, focus=(hw - c).length)


@shot("S22", "spots sails in the distance.", 2.6,
      "His POV over the bow: far off on the horizon, the small pale shape of a brigantine's sails.", ["wind", "sea"],
      cine={"exposure": -0.55})
def s22():
    d, mc = dg_at_sea(heading=95.0, mc=dict(heading=40.0, loc=(2200.0, -900.0, -0.32)), detail=False)
    M = d["M"]
    c = M @ Vector((-12.0, -0.6, ship.zdeck(-12) + 1.65))
    E.camera(c, Vector((2200.0, -900.0, 10.0)), lens=120, fstop=None)


@shot("S23", "Captain David Morehouse calls Deveau up from below.", 3.4,
      "Captain Morehouse at the companion, turned to call down it, one hand on its top; the deck and sails behind him.",
      ["voice off (no lip-sync)", "boots on ladder below"], card="person:DAVID MOREHOUSE|CAPTAIN, DEI GRATIA")
def s23():
    d, _ = dg_at_sea(heading=95.0)
    M = d["M"]; cx = open_companion(d, "DG")
    zc = ship.zdeck(cx)
    Mp = S.deck_place(M, cx + 0.78, 1.05, heading_to(cx + 0.78, 1.05, cx, 1.2))   # at the companion's door, facing aft
    top = M @ Vector((cx + 0.4, 1.4, zc + 1.47))                     # right hand on its top (port side of him)
    def pose(dv, Mx):
        Cw.stand_relaxed(dv, pitch=6, yaw=-10, lean=12)
        Cw.hands_on(dv, Mx, left_w=None, right_w=top, elbow_r=(-0.8, 0.4, -0.5), grip=False, curl=20)
        dv.brow_knit(0.4)
    person("morehouse", Mp, pose, look_w=M @ Vector((cx, 1.2, zc + 0.4)))
    hw = head_w(Mp)
    c = M @ Vector((cx - 1.25, 0.55, zc + 1.7))
    E.camera(c, hw + Vector((0, 0, -0.2)), lens=45, fstop=2.8, focus=(hw - c).length)


@shot("S24", "They change course", 2.0,
      "The helmsman puts the wheel over: his hands haul the spokes round, his body leaning into it.",
      ["wheel spins, pawl clicks", "rudder chain rattles"])
def s24():
    d, _ = dg_at_sea(heading=95.0)
    M = d["M"]; xw = -ship.L / 2 + 1.7; zc = ship.zdeck(xw) + 1.25
    Mp = S.deck_place(M, xw - 0.42, 0.0, 90)
    a1, a2 = math.radians(60), math.radians(150)
    L = M @ Vector((xw, 0.62 * math.sin(a1), zc + 0.62 * math.cos(a1))); R = M @ Vector((xw, -0.62 * math.sin(a2), zc + 0.62 * math.cos(a2)))
    def pose(dv, Mx):
        Cw.stand_relaxed(dv, pitch=8, yaw=-6, lean=12, weight="R")
        Cw.hands_on(dv, Mx, left_w=L, right_w=R, elbow_l=(0.9, 0.2, -0.3), elbow_r=(-0.9, 0.2, -0.6))
    if ANIM.get("on"):
        # the wheel goes over ~75 degrees: the wheel and spokes turn about the hub, his hands travel with the rim
        import anim as A
        dur = ANIM["dur"]
        pivot = bpy.data.objects.new("wheel_pivot", None); bpy.context.scene.collection.objects.link(pivot)
        pivot.matrix_world = M @ Matrix.Translation((xw, 0, zc)); pivot.parent = d["root"]
        bpy.context.view_layer.update(); pivot.matrix_world = M @ Matrix.Translation((xw, 0, zc))
        bpy.context.view_layer.update()
        for o in [o for o in bpy.data.objects if o.name.startswith(("DG_wheel", "DG_spoke")) and not o.name.startswith("DG_wheelbox")]:
            mw = o.matrix_world.copy(); o.parent = pivot; o.matrix_world = mw
        th = lambda t: math.radians(32) * A_ease(t / dur)
        pivot.rotation_mode = 'XYZ'
        for i in range(0, int(dur * 24) + 2, 2):
            pivot.rotation_euler = (-th(i / 24), 0, 0); pivot.keyframe_insert("rotation_euler", frame=1 + i)
        pivot.rotation_euler = (0, 0, 0)
        # hands grip two spokes (at the horizontal, between the rim and the handles), the wrist just aft of the spoke
        spoke = lambda a: M @ Vector((xw - 0.07, 0.74 * math.sin(a), zc + 0.74 * math.cos(a)))
        ANIM["actions"][0] = lambda dv, Mx, t: Cw.hands_on(dv, Mx, left_w=spoke(math.pi / 2 + th(t)), right_w=spoke(-math.pi / 2 + th(t)),
                                                         elbow_l=(0.9, 0.2, -0.6), elbow_r=(-0.9, 0.2, -0.6))
    person(2, Mp, pose, look_w=M @ Vector((xw, 0, zc)))
    c = M @ Vector((xw + 1.3, 1.6, ship.zdeck(xw) + 1.7))
    E.camera(c, M @ Vector((xw - 0.25, 0, zc - 0.05)), lens=35, fstop=3.5)


@shot("S25", "to see if the other ship needs help.", 2.6,
      "Wide: the Dei Gratia leaning as she comes round, her wake curving; the other ship small ahead of her.",
      ["sails thunder as they fill", "sea"])
def s25():
    E.render_setup(samples=96)
    d = S.dei_gratia(heading=60.0, loc=(0, 0, -0.2), heel=-7.0, detail=False)
    mc = S.mary_celeste(heel=6.0, heading=40.0, loc=(900, 600, -0.32), detail=False)
    S.atlantic(center=(0, 0), hulls=(d["hull"],))
    cam = Vector((-30, -60, 9.0))
    E.camera(cam, Vector((40, 30, 4.0)), lens=32, fstop=8)


@shot("S26", "As they come within hailing distance, the crew calls out.", 4.2,
      "From behind Morehouse and a hand at the Dei Gratia's bow rail, the Mary Celeste a few hundred yards off; Morehouse "
      "cups a hand to his mouth.", ["shout (off, no lip-sync)", "wind takes it", "sea"])
def s26():
    d, mc = dg_at_sea(heading=95.0, mc=dict(heading=128.0, loc=(230.0, -60.0, -0.32)))
    M = d["M"]; xb = ship.L / 2 - 4.5
    hb = ship.half_breadth((xb + ship.L / 2) / ship.L, 1.0)
    Mp = S.deck_place(M, xb, -hb + 0.55, 60)
    cap = M @ Vector((xb + 0.2, -(hb - 0.03), ship.zdeck(xb) + ship.RAIL_H + 0.1))
    mouth_off = Vector((0.05, -0.12, 1.6))
    def pose(dv, Mx):
        Cw.stand_relaxed(dv, pitch=-4, yaw=0, lean=6)
        Cw.hands_on(dv, Mx, left_w=Mx @ Vector((0.07, -0.14, 1.58)), right_w=cap, elbow_l=(0.6, 0.0, -0.8), elbow_r=(-0.8, 0.4, -0.5),
                    grip=False, curl=25)
    person("morehouse", Mp, pose, look_w=Vector((230, -60, 3)))
    person(0, S.deck_place(M, xb - 1.3, -hb + 0.7, 45), relaxed(pitch=-3, yaw=-8), look_w=Vector((230, -60, 3)), density=0.5)
    c = M @ Vector((xb - 3.0, -hb + 1.9, ship.zdeck(xb) + 1.75))
    E.camera(c, (M @ Vector((xb, -hb + 0.5, ship.zdeck(xb) + 1.4))).lerp(Vector((230.0, -60.0, 4.0)), 0.004), lens=32, fstop=5.6, focus=3.2)


@shot("S27", "Nobody answers.", 2.0,
      "Long lens across the water: the Mary Celeste's after deck, her wheel with no one at it.", ["wind", "sea", "silence beat"])
def s27():
    d, mc = dg_at_sea(heading=95.0, mc=dict(heading=128.0, loc=(150.0, -40.0, -0.32)), detail=False)
    tgt = mc["M"] @ Vector((-ship.L / 2 + 1.7, 0, ship.zdeck(-14) + 1.0))
    c = d["M"] @ Vector((ship.L / 2 - 4.0, -3.0, ship.zdeck(11) + 1.7))
    E.camera(c, tgt, lens=180, fstop=8)


@shot("S28", "A few sails are still drawing wind.", 2.4,
      "Looking up her foremast: the lower topsail full and pulling, sunlight through the canvas.", ["canvas boom", "block creak"])
def s28():
    mc, _ = mc_at_sea(heel=4.0)
    M = mc["M"]
    c = S.deck_point(M, ship.FORE_X - 2.5, -2.4, 1.2)
    E.camera(c, M @ Vector((ship.FORE_X, 0, 14.0)), lens=22, fstop=8)


@shot("S29", "Others are torn away or hanging loose.", 3.0,
      "Her upper sails in rags, strips streaming and flogging in the wind against the blue sky.", ["sail flogging", "wind"])
def s29():
    mc, _ = mc_at_sea(heel=4.0)
    M = mc["M"]
    c = S.deck_point(M, ship.FORE_X + 4.0, 3.0, 2.0)
    E.camera(c, M @ Vector((ship.FORE_X, 0, 19.0)), lens=40, fstop=8)


@shot("S30", "Morehouse sends men across to board her.", 3.0,
      "Low on the sea: the Dei Gratia's boat pulling across toward the Mary Celeste, Deveau in the stern.",
      ["oars", "boat slaps the swell"])
def s30():
    E.render_setup(samples=96)
    mc = S.mary_celeste(heel=4.0, heading=128.0, loc=(40, -20, -0.32), detail=False)
    import smallboat as SB
    b = SB.build("DGboat", oars_out=True)
    b["root"].matrix_world = Matrix.Translation((8, 4, 0.0)) @ Matrix.Rotation(math.radians(-30), 4, 'Z')
    crew_in_boat(b, rowers=(0, 1), cox="deveau", look=Vector((40, -20, 3)))
    S.atlantic(center=(0, 0), hulls=(mc["hull"], b["hull"]))
    E.camera(Vector((2.2, -2.4, 1.5)), Vector((8.6, 3.2, 0.7)), lens=30, fstop=6)


# ============================================================================ 5. what he finds on board
@shot("S31", "On the deck of the Mary Celeste, Deveau finds", 3.0,
      "Deveau steps up to the binnacle at the after end of the deck and looks down into it.", ["boots", "glass grit underfoot"])
def s31():
    mc, _ = mc_at_sea(heel=2.5)
    M = mc["M"]; xw = -ship.L / 2 + 1.7; bx = xw + 0.75
    Mp = S.deck_place(M, bx + 0.62, -0.1, heading_to(bx + 0.62, -0.1, bx, 0.0))
    top = M @ Vector((bx + 0.22, -0.2, ship.zdeck(xw) + 1.07))         # the binnacle top, on his left (starboard) side
    def pose(dv, Mx):
        Cw.stand_relaxed(dv, pitch=36, yaw=0, lean=14)
        Cw.hands_on(dv, Mx, left_w=top, right_w=None, elbow_l=(0.8, 0.4, -0.5), grip=False, curl=30)
        dv.brow_knit(0.9); dv.lids(0.6)
    person("deveau", Mp, pose, look_w=M @ Vector((bx, 0, ship.zdeck(xw) + 1.1)))
    hw = head_w(Mp)
    c = M @ Vector((bx - 1.6, -1.4, ship.zdeck(xw) + 1.45))
    E.camera(c, hw.lerp(M @ Vector((bx, 0, ship.zdeck(xw) + 1.1)), 0.4), lens=40, fstop=2.8, focus=(hw - c).length)


@shot("S32", "the compass at the helm smashed.", 3.0,
      "Insert, top-down into the binnacle: the compass glass broken into wedges, the card showing through, shards scattered.",
      ["glass crunch", "card ticks"])
def s32():
    mc, _ = mc_at_sea(heel=2.5)
    M = mc["M"]; xw = -ship.L / 2 + 1.7; bx = xw + 0.75
    c = M @ Vector((bx + 0.15, -0.12, ship.zdeck(xw) + 1.75))
    E.camera(c, M @ Vector((bx, 0, ship.zdeck(xw) + 1.15)), lens=60, fstop=4)


@shot("S33", "Two hatch covers are off.", 2.2,
      "High over the deck: the fore hatch and the lazarette open, their covers beside them, each ringed by a filled soft orange band.",
      ["wind", "hatch cover scrape"])
def s33():
    import explain as X
    mc, _ = mc_at_sea(heel=2.0)
    M = mc["M"]
    for k, (x, y, r) in enumerate(((ship.FORE_X + 2.6, 0, 1.25), (-ship.L / 2 + 9.3, -1.5, 0.8))):
        soft_band(M, x, y, r, r, name=f"hatchband{k}", z=0.03)
    c = S.deck_point(M, 4.0, -10.0, 10.0)
    E.camera(c, S.deck_point(M, 1.0, 0.0, 0.0), lens=24, fstop=8)


@shot("S34", "Down in the galley, water has sloshed high enough", 3.5,
      "Inside the galley, looking aft at the doorway and the daylit deck: the floor under dark water, pots thrown down, Deveau's lantern light.",
      ["water slosh", "pot rolls", "drip"], cine={"exposure": 0.25})
def s34():
    import interiors as I
    E.render_setup(samples=128)
    a = I.galley()
    lan = I.lantern((0.6, 0.9, 1.75), energy=40)
    ship.cyl("lamp_hook", (0.6, 0.9, 1.75), (0.6, 0.9, 1.95), 0.006, mat=ship.iron("hk"), verts=8)
    c = Vector((1.6, -0.6, 1.35))
    E.camera(c, Vector((-1.9, 0.35, 0.55)), lens=22, fstop=4)


@shot("S35", "to reach the raised lip around the doorway.", 3.5,
      "Low and close on the door sill: the water standing right up to the top of the raised lip, a tide line on the wood.",
      ["water laps against wood"], cine={"exposure": 0.3})
def s35():
    import interiors as I
    E.render_setup(samples=128)
    a = I.galley()
    I.lantern((0.6, 0.9, 1.75), energy=40)
    s = a["sill"]
    c = Vector((s.x + 0.9, s.y - 0.55, 0.42))
    E.camera(c, Vector((s.x, s.y + 0.05, 0.3)), lens=45, fstop=2.8)


@shot("S36", "The stove has been knocked out of place.", 3.2,
      "The iron galley stove shoved off its hearth and leaning, its pipe torn from the deckhead collar; Deveau in the "
      "background holding up the lantern.", ["iron scrape", "water slop"], cine={"exposure": 0.25})
def s36():
    import interiors as I
    E.render_setup(samples=128)
    a = I.galley()
    Mp = Matrix.Translation((-0.9, 0.55, 0.0)) @ Matrix.Rotation(math.radians(-90 + 30), 4, 'Z')
    lw = Mp @ Vector((0.28, -0.4, 1.4))
    def pose(dv, Mx):
        Cw.stand_relaxed(dv, pitch=18, yaw=-10, lean=6)
        P.hand_reach(dv.h, "L", Mx.inverted() @ lw, elbow=(0.8, 0.3, -0.6)); P.grip(dv.h, "L")
        dv.brow_knit(0.7)
    person("deveau", Mp, pose, look_w=a["stove"])
    I.lantern(lw + Vector((0, 0, -0.02)), energy=45)
    c = Vector((1.55, -1.25, 0.75))
    E.camera(c, a["stove"] + Vector((-0.4, 0.3, 0.3)), lens=28, fstop=3.5, focus=(a["stove"] - c).length)


@shot("S37", "He measures the water in the bottom of the ship.", 3.4,
      "At the pumps: Deveau lowers the sounding rod on its line down the pump well, hand over hand, watching it go.",
      ["line runs through hands", "rod knocks the well", "splash below"])
def s37():
    mc, _ = mc_at_sea(heel=2.5)
    M = mc["M"]; px = ship.MAIN_X + 0.9
    well = Vector((px + 0.45, 0.0))
    E.hide(["MC_pumpbrake"])
    iron = mc["mats"]["iron"]
    made = [ship.box("well_cap", (well.x, well.y, ship.zdeck(px) + 0.06), (0.24, 0.24, 0.12), mc["mats"]["deckwood"]),
            ship.box("well_hole", (well.x, well.y, ship.zdeck(px) + 0.121), (0.12, 0.12, 0.004), mc["mats"]["dark"])]
    S._parent(made, mc["root"])
    Mp = S.deck_place(M, well.x + 0.45, well.y - 0.2, heading_to(well.x + 0.45, well.y - 0.2, well.x, well.y))
    lineTop = M @ Vector((well.x + 0.05, well.y, ship.zdeck(px) + 1.15))
    lineLow = M @ Vector((well.x + 0.02, well.y, ship.zdeck(px) + 0.85))
    def pose(dv, Mx):
        Cw.stand_relaxed(dv, pitch=40, yaw=0, lean=24)
        Cw.hands_on(dv, Mx, left_w=lineTop, right_w=lineLow, elbow_l=(0.8, 0.4, -0.4), elbow_r=(-0.8, 0.4, -0.4))
        dv.lids(0.8); dv.brow_knit(0.5)
    person("deveau", Mp, pose, look_w=M @ Vector((well.x, well.y, ship.zdeck(px))))
    rope_m = mc["mats"]["rope"]
    ship.rope("sounding_line", [lineTop + Vector((0, 0, 0.25)), lineTop, lineLow, M @ Vector((well.x, well.y, ship.zdeck(px) + 0.12))], 0.006, rope_m)
    hw = head_w(Mp)
    c = M @ Vector((well.x - 1.4, well.y - 1.5, ship.zdeck(px) + 1.2))
    E.camera(c, hw.lerp(lineLow, 0.5), lens=35, fstop=3.5, focus=(hw - c).length)


@shot("S38", "Three and a half feet.", 2.0,
      "Insert: the sounding rod laid on the deck, wet and dark up to its three-and-a-half-foot mark, a filled soft orange band at the mark.",
      ["rod set down on planks", "drip"])
def s38():
    import explain as X
    mc, _ = mc_at_sea(heel=2.5)
    M = mc["M"]; x0 = ship.MAIN_X + 1.6; RY_ = 2.45          # port walkway, clear of the rail section and the hatch
    zd = ship.zdeck(x0) + 0.012
    dry = ship.paint("rod_dry", (0.55, 0.42, 0.26), rough=0.6, grime=0.3, scale=8)
    wet = ship.paint("rod_wet", (0.22, 0.14, 0.08), rough=0.2, grime=0.2, wet=1.0, scale=8)
    ft = 0.3048
    a = M @ Vector((x0, RY_, zd + 0.02)); b = M @ Vector((x0 + 3.5 * ft, RY_, zd + 0.02)); c_ = M @ Vector((x0 + 6 * ft, RY_, zd + 0.02))
    ship.cyl("rod_wet", a, b, 0.02, mat=wet, verts=16); ship.cyl("rod_dry", b, c_, 0.02, mat=dry, verts=16)
    notch = E.principled("notch", (0.03, 0.02, 0.01), rough=0.8)
    for k in range(1, 7):
        p = M @ Vector((x0 + k * ft, RY_, zd + 0.02))
        ship.cyl("rod_notch", p - M.to_3x3() @ Vector((0.004, 0, 0)), p + M.to_3x3() @ Vector((0.004, 0, 0)), 0.0175, mat=notch, verts=12)
    soft_band(M, x0 + 3.5 * ft, RY_, 0.09, 0.16, name="markband", z=0.004)
    X.text3d("ftlabel", "3½ FT", M @ Vector((x0 + 3.5 * ft, RY_ - 0.3, zd + 0.004)), size=0.12, color=(1, 0.93, 0.85), strength=2.5,
             rot=M.to_euler())
    E.hide(["MC_pumpbrake", "MC_pump"])
    c = M @ Vector((x0 + 1.0, RY_ - 1.05, zd + 0.7))
    E.camera(c, M @ Vector((x0 + 1.0, RY_ - 0.05, zd)), lens=32, fstop=5.6)


@shot("S39", "The hull looks in good shape.", 2.2,
      "X-ray cutaway: the Mary Celeste as glass on a dark studio floor, the water in her hold a solid blue body, the "
      "3½ ft dimension beside it. Slow orbit.", ["low drone", "water settle"])
def s39():
    import explain as X
    X.hold_cutaway()
    E.camera(Vector((10.0, -19.0, 4.0)), Vector((-1.0, 0.0, -1.0)), lens=32, fstop=None)


@shot("S40", "The masts are standing.", 1.6,
      "Low on deck looking up the mainmast to the sky, shrouds and ratlines converging.", ["mast creak", "wind"])
def s40():
    mc, _ = mc_at_sea(heel=2.5)
    M = mc["M"]
    c = S.deck_point(M, ship.MAIN_X + 1.2, -2.6, 0.5)
    E.camera(c, M @ Vector((ship.MAIN_X, 0.0, 20.0)), lens=18, fstop=8, roll=8)


@shot("S41", "There's enough sail left to keep her moving.", 2.8,
      "From the sea: the Mary Celeste leaning to the wind under her remaining canvas, a bow wave curling.", ["bow wave", "canvas"])
def s41():
    mc, _ = mc_at_sea(heel=5.0, heading=40.0, cut=False, center=(0, 0))
    M = mc["M"]
    cam = M @ Vector((38.0, -26.0, 0)); cam.z = 1.6
    E.camera(cam, M @ Vector((2.0, 0.0, 7.0)), lens=35, fstop=8)


@shot("S42", "The question is whether three men can handle her", 3.6,
      "Deveau alone by the mainmast, looking aloft and then aft along the deck: weighing it. Slow push-in.",
      ["wind", "rigging", "his breath"])
def s42():
    mc, _ = mc_at_sea(heel=2.5)
    M = mc["M"]
    px, py = ship.MAIN_X + 1.4, -1.65
    Mp = S.deck_place(M, px, py, heading_to(px, py, -0.6, -2.6) + 25)
    person("deveau", Mp, relaxed(pitch=-14, yaw=14, brow=0.8, lids=0.2), look_w=M @ Vector((ship.MAIN_X, 0, 14)))
    hw = head_w(Mp)
    c = S.deck_point(M, -0.6, -2.6, 1.55)
    E.camera(c, hw + Vector((0, 0, -0.12)), lens=50, fstop=2.8, focus=(hw - c).length)


@shot("S43", "and keep the water down all the way to Gibraltar.", 4.0,
      "3D map: from the hexagon where the Dei Gratia found her, a dashed orange route east to Gibraltar.",
      ["map whoosh", "marker thump"], card="place:GIBRALTAR|BRITISH TERRITORY, 1872")
def s43():
    import explain as X
    X.atlas()
    found = (-17.25, 38.33)
    X.hex_marker("found", *found); X.hex_marker("gib", -5.35, 36.14, color=X.ORANGE)
    X.dashed_route("route", [found, (-12.0, 37.0), (-8.0, 36.2), (-5.6, 36.1)])
    X.label("lab_gib", "GIBRALTAR", -5.35, 36.14, dy=0.75)
    c = X.geo(-12.8, 29.2, 13.5)
    E.camera(c, X.geo(-11.6, 36.0, 0), lens=33)


# ============================================================================ 6. the mate's cabin: log and slate
def mate_scene():
    import interiors as I
    E.render_setup(samples=128)
    return I.mate_cabin()


@shot("S44", "Before he takes that chance, Deveau finds something that tells him", 4.2,
      "The mate's cabin door: Deveau steps in with the lantern held up, its light spilling across the table.",
      ["door latch", "boots", "lantern creak"], cine={"exposure": 0.2})
def s44():
    import interiors as I
    a = mate_scene()
    d = a["door"]
    Mp = Matrix.Translation((d.x - 0.35, d.y, 0)) @ Matrix.Rotation(math.radians(-90 + 25), 4, 'Z')
    lw = Mp @ Vector((-0.25, -0.45, 1.42))
    def pose(dv, Mx):
        Cw.stand_relaxed(dv, pitch=14, yaw=8, lean=4)
        P.hand_reach(dv.h, "R", Mx.inverted() @ lw, elbow=(-0.8, 0.3, -0.6)); P.grip(dv.h, "R")
        dv.brow_knit(0.4)
    person("deveau", Mp, pose, look_w=a["table"])
    I.lantern(lw + Vector((0, 0, -0.02)), energy=45)
    c = Vector((-1.15, -0.95, 1.5))
    E.camera(c, Vector((d.x - 0.4, d.y - 0.1, 1.2)), lens=26, fstop=3.5)


@shot("S45", "where to start looking for the people who were here.", 4.4,
      "Slow push-in across the table: the open logbook and the slate in the lantern light.", ["lamp hiss", "creak"], cine={"exposure": 0.25})
def s45():
    a = mate_scene()
    t = a["table"]
    c = t + Vector((-0.95, -0.55, 0.55))
    E.camera(c, t + Vector((0.05, 0.0, 0.05)), lens=35, fstop=2.8)


@shot("S46", "In the mate's cabin is the ship's logbook.", 3.2,
      "Insert: the open logbook, its last written page, lantern light raking across the paper.", ["page turn"], cine={"exposure": 0.3})
def s46():
    a = mate_scene()
    b = a["book"].location
    c = b + Vector((-0.12, -0.35, 0.38))
    E.camera(c, b + Vector((0, 0, 0.02)), lens=50, fstop=4)


@shot("S47", "On the cabin table is the slate", 2.6,
      "Top-down: the slate in its wooden frame, chalk lines, a stub of chalk beside it.", ["chalk tap"], cine={"exposure": 0.3})
def s47():
    a = mate_scene()
    s = a["slate"].location
    c = s + Vector((0.0, 0.0, 0.62))
    E.camera(c, s, lens=40, fstop=5.6, roll=-14)


@shot("S48", "the crew used to jot things down during a watch.", 3.8,
      "Deveau seated at the table reading, the lantern beside him lighting his face from below; his eyes move along the lines.",
      ["breath", "hull creak"], cine={"exposure": 0.2})
def s48():
    import interiors as I, human as H
    a = mate_scene()
    t = a["table"]
    M = Matrix.Translation((t.x + 0.05, t.y + 0.62, 0.0))
    def pose(dv, Mx):
        H.pose_sit(dv.h, lean=16, hands="knees")
        P.head(dv.h, pitch=4, yaw=-18)
        Cw.hands_on(dv, Mx, left_w=t + Vector((0.42, 0.06, 0.07)), right_w=t + Vector((0.12, 0.1, 0.07)),
                    elbow_l=(0.8, 0.5, -0.6), elbow_r=(-0.8, 0.5, -0.6), grip=False, curl=25)
        dv.brow_knit(0.6); dv.lids(0.6)
    dv = person("deveau", M, pose, look_w=a["slate"].location, seat=True)
    seat_chest(dv)
    hw = dv.place_M @ Vector((0, -0.16, 1.6))
    c = Vector((t.x - 0.85, t.y - 0.3, 1.42))
    E.camera(c, hw + Vector((0.0, -0.1, -0.12)), lens=38, fstop=2.4, focus=(hw - c).length)


@shot("S49", "The book stops on November twenty-fourth.", 2.8,
      "Macro on the log's last entry, 'Nov 24', the rest of the page blank below it.", ["page settles"], cine={"exposure": 0.35})
def s49():
    a = mate_scene()
    b = a["book"].matrix_world
    tgt = b @ Vector((-0.08, 0.02, 0.025))
    c = b @ Vector((-0.06, -0.08, 0.22))
    E.camera(c, tgt, lens=80, fstop=3.5)


@shot("S50", "The slate carries on into the next morning.", 3.0,
      "Macro on the slate: 'Nov 25' and the morning's lines in chalk.", ["chalk scratch"], cine={"exposure": 0.35})
def s50():
    a = mate_scene()
    s = a["slate"].matrix_world
    c = s @ Vector((-0.06, -0.06, 0.25))
    E.camera(c, s @ Vector((-0.06, 0.04, 0.0)), lens=70, fstop=4)


# ============================================================================ 7. where she should have been
@shot("S51", "It puts the Mary Celeste six miles from Santa Maria, an island in the Azores.", 6.0,
      "3D map close on the Azores: Santa Maria marked with a red hexagon and filled soft orange bands; '6 MILES' callout.",
      ["map whoosh", "marker thump"], card="place:SANTA MARIA|AZORES")
def s51():
    import explain as X
    X.atlas()
    sm = (-25.1, 36.97)
    X.hex_marker("sm", sm[0] + 0.18, sm[1] + 0.05, r=0.16)
    X.ripple_bands("smr", sm[0] + 0.18, sm[1] + 0.05, radii=((0.28, 0.42), (0.55, 0.68)))
    X.label("lab_sm", "SANTA MARIA", *sm, size=0.32, dy=-0.75)
    X.label("lab_6", "6 MILES", sm[0] + 0.18, sm[1] + 0.05, size=0.22, dx=0.9, dy=0.35, color=(1.0, 0.75, 0.5))
    c = X.geo(-25.8, 35.0, 4.0)
    E.camera(c, X.geo(-25.0, 37.1, 0), lens=40)


@shot("S52", "Deveau is hundreds of miles east of that island.", 3.8,
      "The map pulls back and slides east: a second hexagon where the Dei Gratia found her, far from the Azores.",
      ["whoosh", "marker thump"])
def s52():
    import explain as X
    X.atlas()
    X.hex_marker("sm", -24.92, 37.02, r=0.3); X.hex_marker("found", -17.25, 38.33)
    X.label("lab_az", "AZORES", -27.0, 38.3, size=0.7, dy=1.1)
    X.label("lab_dg", "DEI GRATIA, DEC 4", -17.25, 38.33, size=0.6, dy=0.9)
    c = X.geo(-21.8, 30.8, 10.5)
    E.camera(c, X.geo(-21.8, 37.9, 0), lens=30)


@shot("S53", "He has no record of what happened in between.", 4.2,
      "The open water between the two markers: no line joins them; filled soft orange bands pulse over the empty sea. Hold.",
      ["low drone", "sea under"])
def s53():
    import explain as X
    X.atlas()
    X.hex_marker("sm", -24.92, 37.02, r=0.3); X.hex_marker("found", -17.25, 38.33)
    X.ripple_bands("gap", -21.0, 37.7, radii=((1.0, 1.5), (2.0, 2.4)))
    X.text3d("q", "?", X.geo(-21.0, 37.7, 0.4), size=1.2, color=(1.0, 0.8, 0.6), strength=2.0)
    c = X.geo(-21.0, 33.5, 7.0)
    E.camera(c, X.geo(-21.0, 37.8, 0), lens=35)
