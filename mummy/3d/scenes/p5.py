"""Part 5 (mummy/vo/MUMMY_P5_VO.txt): "So why combine them?" -> "...lowered them into graves, and built above them."

Same contract and house rules as p1-p4. No face toward the lens; clipcheck 0; motivated light; no text in frame.
Built from the approved sets: the roundhouse interior, the osteology lab, the aDNA clean room, the excavation.
"""
import math, os, random
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
import uist as U, dig as G, cast as K, bones as B, lab as LB, bronze as BR, p2sets as P2, sf, ph
import p1, p2, p3

HAIR = p1.HAIR
_plain, _glass, _spot, _haze = p1._plain, p1._glass, p2._spot, p2._haze


# ----------------------------------------------------------------------------- helpers
def _house_bundle(fire=1.0, moon=0.0, at=(-2.35, 0.86), rot=70, door_sun=0.0, raised=False):   # between two posts
    """Inside the middle roundhouse: the wrapped body on its hurdle at the back (west) wall. Returns (R, bundle centre)."""
    U.CUT = False
    R = BR.interior(fire=fire, door_sun=door_sun, moon=moon)
    hx, hy = 0.3, 0.0
    bx, by = hx + at[0], hy + at[1]
    z0 = 0.03
    if raised:       # a low platform of flat stones under the hurdle, hides laid over it
        for k in range(7):
            G.stone((bx + (k - 3) * 0.28, by + random.Random(k).uniform(-0.05, 0.05), 0.07), (0.34, 0.8, 0.14), rot_z=math.radians(rot) + 0.05 * k, seed=k, flat=0.9)
        z0 = 0.16
    P2.hurdle((bx, by, z0), rot=math.radians(rot), length=1.8, width=0.75)
    bo = P2.crouched_bundle((bx, by, z0 + 0.04), rot=math.radians(rot), seed=1)
    bpy.context.view_layer.update()
    W = np.array([bo.matrix_world @ v.co for v in bo.data.vertices])
    return R, Vector((bx, by, float(W[:, 2].mean())))


def _kneeler(i, name, knees, heading, look, lean=12, var=0, hands=None):
    """An islander kneeling sitting back on the heels (from behind), hands resting on the thighs or at `hands`."""
    import acts as AC
    m = BR.villager("man" if i == 0 else "elder", name, var=var, ease=1.3)     # Bronze Age dress: belted wool tunic, wrapped legs
    st = AC.Kneel(m, knees, heading, lean=lean, sit_back=True)
    f = Vector((math.cos(math.radians(heading)), math.sin(math.radians(heading)), 0)); s = Vector((f.y, -f.x, 0))
    k = Vector((knees[0], knees[1], 0))
    for sd, sg in (("L", -1), ("R", 1)):
        w = hands[sd] if hands else tuple(k + f * 0.12 + s * (0.12 * sg) + Vector((0, 0, 0.36)))
        st.hand(sd, w, elbow=(0.5, 0.1, -0.9), curl=24)
    st.head_to(look, share=0.7); st.finish(look=look, density=1.0)
    return st


def _three_parts(lit=True):
    """The three parts of one composite body on the velvet, set apart: an old dark skull, a pale arm bone, a rib cage
    of a third tone. Returns their centres."""
    A = LB.room(window_light=0.12, lamp=False)
    LB.velvet(-0.9, 0.9, 0.0, 0.78, LB.TOP)
    cr = B.hero_cranium(healed=False, tone="D"); p3._old_bone(cr, stain=1.0, etch=0.45)
    co = np.array([v.co for v in cr.data.vertices]); cr.location = (-0.3, 0.4, LB.TOP + 0.004 - co[:, 2].min() * 0.97)
    cr.rotation_euler = (0, 0, math.radians(-25))
    p3.lab_part("upperarmR", sex="M", tone="A", x=0.0, y=0.4, yaw=10, name="ArmPart")
    p3.lab_part("thorax", sex="F", tone="C", x=0.33, y=0.42, yaw=90, name="TorsoPart")
    cs = [Vector((-0.3, 0.4, LB.TOP + 0.08)), Vector((0.0, 0.4, LB.TOP + 0.02)), Vector((0.33, 0.42, LB.TOP + 0.06))]
    if lit:
        for c in cs:
            _spot((c.x - 0.15, c.y - 0.35, c.z + 0.7), tuple(c), 28, size=0.05, color=(1.0, 0.9, 0.78), spot=16)
    return cs


# ============================================================================ "So why combine them?"
def S01():
    """Night in the roundhouse: the wrapped body on its hurdle at the back wall, firelight wavering over it. A very low
    slow glide along the floor toward it."""
    R, c = _house_bundle(fire=1.0, moon=0.6)
    hx, hy = R["hearth"]
    return dict(a=((c.x + 2.4, c.y - 1.3, 0.35), tuple(c)), b=((c.x + 1.7, c.y - 0.95, 0.32), tuple(c)), lens=40,
                fstop=2.8, focus=tuple(c), cine=dict(exposure=0.45, sat=0.85), hand_ok=("floor",))


# ============================================================================ "One possibility is that the bodies represented ancestors..."
def S02():
    """Three parts of one figure, each in its own pool of lamplight on the dark velvet: a dark old skull, a pale arm
    bone, a rib cage - three people. Slow lateral slide across them."""
    cs = _three_parts()
    m = (cs[0] + cs[2]) / 2
    return dict(a=((m.x - 0.18, m.y - 0.95, LB.TOP + 0.5), tuple(m - Vector((0.08, 0, 0)))), b=((m.x + 0.18, m.y - 0.95, LB.TOP + 0.5), tuple(m + Vector((0.08, 0, 0)))),
                lens=40, fstop=4.0, focus=tuple(cs[1]), cine=dict(exposure=0.1))


def S03():
    """The household at the hearth, seen from behind by the doorway: an elder and a man kneeling at the fire, a woman in
    her shawl standing behind them with a child at her side, all facing the wrapped ancestor at the back wall."""
    import acts as AC
    R, c = _house_bundle(fire=1.0, moon=0.4)
    hx, hy = R["hearth"]
    look = (c.x, c.y, 0.6)
    def face(p):
        return math.degrees(math.atan2(c.y - p[1], c.x - p[0]))
    for k, (kind, dx, dy) in enumerate((("elder", 1.15, -0.9), ("man", 1.35, -0.05))):
        kn = (hx + dx, hy + dy)
        m = BR.villager(kind, f"Kin{k}", var=k, ease=1.3)
        st = AC.Kneel(m, kn, face(kn), lean=10, sit_back=True)
        f = Vector((math.cos(math.radians(face(kn))), math.sin(math.radians(face(kn))), 0)); sv = Vector((f.y, -f.x, 0)); kk = Vector((kn[0], kn[1], 0))
        for sd, sg in (("L", -1), ("R", 1)):
            st.hand(sd, tuple(kk + f * 0.12 + sv * (0.12 * sg) + Vector((0, 0, 0.36))), elbow=(0.5, 0.1, -0.9), curl=24)
        st.head_to(look, share=0.9); st.finish(look=look, density=1.0)
    for k, (kind, dx, dy) in enumerate((("woman", 2.1, -0.75), ("child", 2.05, -0.2))):
        f_ = (hx + dx, hy + dy)
        m = BR.villager(kind, f"Kin{k + 2}", var=k + 2)
        st = AC.Stand(m, f_, face(f_), lean=2, weight="L")
        st.head_to(look, share=0.9); st.finish(look=look, density=1.0)
    return dict(a=((hx + 3.4, hy - 2.2, 2.2), (c.x, c.y, 0.4)), b=((hx + 3.0, hy - 1.9, 2.05), (c.x, c.y, 0.4)), lens=30,
                fstop=2.8, focus=(hx + 1.2, hy - 0.4, 0.6), cine=dict(exposure=0.45, sat=0.85), hand_ok=("floor",))


def S04():
    """A lineage: in the lab, the dark skull alone in a narrow pool of light, the other two parts dim beyond. Slow push."""
    cs = _three_parts(lit=False)
    _spot((cs[0].x - 0.3, cs[0].y - 0.3, cs[0].z + 0.6), tuple(cs[0]), 45, size=0.04, color=(1.0, 0.88, 0.74), spot=14)
    _spot((0.2, 0.0, LB.TOP + 0.8), (0.2, 0.4, LB.TOP), 6, size=0.3, color=(0.7, 0.78, 1.0), spot=60)
    return dict(a=((cs[0].x + 0.5, cs[0].y - 0.75, cs[0].z + 0.22), tuple(cs[0] + Vector((0.12, 0, 0)))), b=((cs[0].x + 0.42, cs[0].y - 0.62, cs[0].z + 0.2), tuple(cs[0] + Vector((0.08, 0, 0)))),
                lens=50, fstop=2.8, focus=tuple(cs[0]), cine=dict(exposure=0.0))


# ============================================================================ "If ancestry helped establish who belonged..."
def S05():
    """Dusk outside the middle house: islanders gathered at the doorway, backs to us, the hearth glow inside; smoke from
    the roofs. Slow push toward the door."""
    U.CUT = False
    U.island("dusk", grass_at=(10, -2), grass_r=18, n=820, core=4.0, grass_density=220)
    BR.village(smoke_on=True)
    for o in [o for o in bpy.data.objects if o.name.startswith("path")]:
        o.location.z -= 0.03                     # the worn-path decal sits just under the soles (it floated over the turf)
    import acts as AC
    hx, hy, r = U.HOUSES[1]
    door = Vector((hx + r * 1.75 + 0.4, hy, float(U.surface(hx + r * 1.75 + 0.4, hy))))
    kinds = ("man", "woman", "elder", "child", "man", "woman")
    for k, (dx, dy) in enumerate(((2.2, -0.9), (2.6, 0.5), (3.4, -0.2), (3.1, 0.95), (3.9, -1.3), (4.2, 0.4))):
        f = (door.x + dx, door.y + dy); zf = float(U.surface(*f))
        m = BR.villager(kinds[k], f"Kin{k}", var=k + 1)
        st = AC.Stand(m, f, 180 + random.Random(k).uniform(-12, 12), lean=4 if kinds[k] != "elder" else 9, weight="L" if k % 2 else "R")
        st.head_to((door.x, door.y, door.z + 1.0 - zf), share=0.9)
        st.finish(look=(door.x, door.y, door.z + 1.0 - zf), density=1.0)
        bt = p2._belt(st) if kinds[k] in ("man", "elder") else None     # a leather belt round the tunic
        G.lift(st, zf)
        if bt is not None:
            bt.location.z += zf
    return dict(a=((door.x + 9.0, door.y - 2.6, door.z + 1.7), (door.x, door.y, door.z + 1.0)), b=((door.x + 7.6, door.y - 2.0, door.z + 1.6), (door.x, door.y, door.z + 1.0)),
                lens=35, fstop=4.0, focus=(door.x + 3.0, door.y, door.z + 1.1), cine=dict(exposure=0.3))


def S06():
    """Status: the wrapped body raised on a low stone platform with hides, pots set beside it, in the firelight."""
    R, c = _house_bundle(fire=1.0, moon=0.3, raised=True)
    rng = random.Random(6)
    for k, (dx, dy) in enumerate(((0.65, -0.95), (0.9, -0.6), (0.7, 0.9), (1.0, 1.15))):
        BR.pot(c.x + dx, c.y + dy, 0.0, h=rng.uniform(0.22, 0.34), r=rng.uniform(0.12, 0.17), seed=20 + k)
    return dict(a=((c.x + 2.0, c.y - 1.5, 0.85), tuple(c)), b=((c.x + 1.6, c.y - 1.15, 0.75), tuple(c)), lens=35,
                fstop=2.8, focus=tuple(c), cine=dict(exposure=0.45, sat=0.85), hand_ok=("floor",))


# ============================================================================ "...the bones cannot tell us what the people called these figures..."
def S07():
    """The osteologist at the bench (from behind, over the shoulder), the skeleton under the lamp - the evidence stops
    at the bones. Short neat hair, white lab coat. Slow push past the shoulder."""
    L = p1.lab_body(osteo=False)
    import acts as AC

    m = K.OsteologistNeat("Osteologist")
    st = AC.Stand(m, (0.15, -0.42), 90, lean=14)
    st.hand("L", (-0.05, 0.12, LB.TOP + 0.02), elbow=(0.6, 0.2, -0.8), curl=18)
    st.hand("R", (0.32, 0.18, LB.TOP + 0.03), elbow=(0.6, 0.2, -0.8), curl=24)
    st.head_to((0.1, 0.4, LB.TOP), share=0.9)
    st.finish(look=(0.1, 0.4, LB.TOP), density=1.0)
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.data.type in ('SUN', 'AREA') and "lamp" not in o.name.lower():
            o.data.energy *= 0.3
    t = Vector((0.05, 0.38, LB.TOP + 0.05))
    return dict(a=((0.62, -1.15, LB.TOP + 0.95), tuple(t)), b=((0.5, -0.95, LB.TOP + 0.85), tuple(t)), lens=35,
                fstop=4.0, focus=tuple(t), cine=dict(exposure=0.1), hand_ok=p1.OK)


def S08():
    """The skull in darkness, one hard raking light across the eye socket and brow: what did they call this person?"""
    cs = _three_parts(lit=False)
    c = cs[0]
    _spot((c.x - 0.55, c.y - 0.1, c.z + 0.1), tuple(c), 60, size=0.02, color=(1.0, 0.86, 0.7), spot=12)   # raking across the brow
    return dict(a=((c.x - 0.28, c.y - 0.58, c.z + 0.06), tuple(c)), b=((c.x - 0.18, c.y - 0.62, c.z + 0.07), tuple(c)), lens=70,
                fstop=4.0, focus=tuple(c), cine=dict(exposure=-0.1))


# ============================================================================ "Even the relationships between the original people remain uncertain..."
def S09():
    """The clean room: three racks of sample tubes in the cabinet, each rack a different cap colour - three people's
    DNA. Slow slide along them (violet only as an accent)."""
    p3.clean_room(uv=0.3)
    for k, col in enumerate(((0.85, 0.2, 0.1), (0.15, 0.45, 0.8), (0.9, 0.85, 0.2))):
        pos = p3._rack(-0.45 + k * 0.32, 1.42, 0.9, nx=4, ny=3, col=(0.85, 0.85, 0.82))
        for (px, py) in pos[:9]:
            p3._microtube(px, py, 0.913, cap=col)
    t = Vector((-0.13, 1.42, 0.95))
    return dict(a=((-0.62, 1.12, 1.03), (-0.45, 1.42, 0.94)), b=((0.05, 1.12, 1.03), (0.19, 1.42, 0.94)), lens=50,
                fstop=4.0, focus=tuple(t), cine=dict(exposure=-0.3))


def S10():
    """Related or not, the tests cannot say: low across the bench at velvet level, the three parts in a line receding
    into the dark, each with its capped sample tube beside it - red by the skull, blue by the arm, yellow by the ribs.
    Long lens, focus on the middle one."""
    cs = _three_parts(lit=True)
    for c, col in zip(cs, ((0.85, 0.2, 0.1), (0.15, 0.45, 0.8), (0.9, 0.8, 0.2))):
        p3._microtube(c.x + 0.07, c.y - 0.12, LB.TOP + 0.002, cap=col)
    near = cs[2]
    return dict(a=((near.x + 0.55, near.y - 0.28, LB.TOP + 0.06), tuple(cs[0])), b=((near.x + 0.5, near.y - 0.24, LB.TOP + 0.07), tuple(cs[0])),
                lens=85, fstop=2.8, focus=tuple(cs[1]), cine=dict(exposure=0.05))


# ============================================================================ "Another possibility is more practical..."
def _surface_hit(o, local_xy, up=1.0):
    """Ray from above onto object `o` at a point given in its local xy: returns (world point, world normal)."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    org = o.matrix_world @ Vector((local_xy[0], local_xy[1], 2.0))
    ok, loc, nrm, idx = o.evaluated_get(dg).ray_cast(o.matrix_world.inverted() @ org, Vector((0, 0, -1)))
    if not ok:
        return o.matrix_world @ Vector((local_xy[0], local_xy[1], 0.2)), Vector((0, 0, 1))
    return o.matrix_world @ loc, (o.matrix_world.to_3x3() @ nrm).normalized()


def S11():
    """Damage: close on the wrapped body - the dark hide split open over the hip, and the head of a thigh bone pushing
    out through the gap. Firelight, sharp focus on the bone."""
    R, c = _house_bundle(fire=1.0, moon=0.2)
    bo = bpy.data.objects["bundle"]
    hit, n = _surface_hit(bo, (-0.14, 0.02))
    n = (n + Vector((0, 0, 0.6))).normalized()
    sk = B.Skeleton("M", "C", name="Exposed")
    for s_ in list(sk.parts):
        if s_ != "femurL":
            sk.remove(s_)
    o = sk.parts["femurL"]; p3._knee_mats(o, sand=0.4)
    sk.root.rotation_euler = Vector((0, 0, 1)).rotation_difference(n).to_euler()
    bpy.context.view_layer.update()
    W = np.array([o.matrix_world @ v.co for v in o.data.vertices])
    top = W[np.argmax(W @ np.array(n))]
    tgt = hit + n * 0.065                                  # the femoral head stands 6-7 cm out of the hide
    sk.root.location += Vector((tgt.x - top[0], tgt.y - top[1], tgt.z - top[2]))
    bpy.context.view_layer.update()
    # the split: a dark ragged gap in the hide round the bone, with lifted torn lips
    q = Vector((0, 0, 1)).rotation_difference(n)
    bpy.ops.mesh.primitive_circle_add(vertices=28, radius=0.055, fill_type='NGON', location=tuple(hit + n * 0.003)); gp = bpy.context.active_object
    gp.rotation_euler = q.to_euler(); gp.scale = (1.0, 0.62, 1.0); gp.name = "hidesplit"; gp.data.materials.append(_plain("hidegap", (0.008, 0.005, 0.003), 0.95))
    dg_ = gp.modifiers.new("rag", "DISPLACE"); tr = bpy.data.textures.new("ragged", "CLOUDS"); tr.noise_scale = 0.015; dg_.texture = tr; dg_.strength = 0.01
    bpy.ops.mesh.primitive_torus_add(major_radius=0.058, minor_radius=0.009, location=tuple(hit + n * 0.004)); lp = bpy.context.active_object
    lp.rotation_euler = q.to_euler(); lp.scale = (1.0, 0.62, 1.0); lp.name = "hidelip"; lp.data.materials.append(bo.data.materials[0])
    dl = lp.modifiers.new("rag", "DISPLACE"); dl.texture = tr; dl.strength = 0.012
    hx, hy = R["hearth"]
    _spot((hx - 0.2, hy + 0.2, 0.8), tuple(tgt), 160, size=0.2, color=(1.0, 0.55, 0.22), spot=30)
    side = Vector((n.x, n.y, 0)).normalized() if Vector((n.x, n.y, 0)).length > 0.1 else Vector((1, 0, 0))
    cam = tgt + side * 0.62 + Vector((0, 0, 0.32)) + Vector((-side.y, side.x, 0)) * 0.22     # back enough to see the bone come out of the hide
    return dict(a=(tuple(cam), tuple(tgt - n * 0.03)), b=(tuple(cam - side * 0.08), tuple(tgt - n * 0.03)), lens=50,
                fstop=4.0, focus=tuple(tgt), cine=dict(exposure=0.45, sat=0.85), hand_ok=("floor", "bundle"))


def S12():
    """Repair: fresh pale cord bound tight over the old dark hide beside the worn ropes - wraps and knots, close and
    firelit."""
    R, c = _house_bundle(fire=1.0, moon=0.2)
    bo = bpy.data.objects["bundle"]
    cord = _plain("freshcord", (0.62, 0.52, 0.36), 0.85)
    rot = math.radians(70)
    for k, u in enumerate((0.05, 0.085, 0.12)):
        cc = bo.matrix_world @ Vector((u, -0.03, 0.0))
        P2._cord_ring(bo, cc, (0, math.pi / 2, rot), 0.42, cord, name="freshcord", thick=0.008, knot=(k == 1))
    bpy.context.view_layer.update()
    kn = [o for o in bpy.data.objects if o.name.startswith("freshcordknot")]
    t = kn[0].location.copy() if kn else c
    hx, hy = R["hearth"]
    _spot((hx - 0.2, hy + 0.2, 0.8), tuple(t), 140, size=0.2, color=(1.0, 0.55, 0.22), spot=30)
    along = Vector((math.cos(rot), math.sin(rot), 0)); side = Vector((math.cos(rot - math.pi / 2), math.sin(rot - math.pi / 2), 0))
    cam = t + side * 0.55 + along * 0.3 + Vector((0, 0, 0.35))       # the cords across the body, knots and wraps together
    return dict(a=(tuple(cam), tuple(t)), b=(tuple(cam - side * 0.06), tuple(t)), lens=55,
                fstop=4.0, focus=tuple(t), cine=dict(exposure=0.45, sat=0.85), hand_ok=("floor",))


def S13():
    """How easily an old body comes apart: the broken knee on the velvet from above, the jagged breaks between the
    pieces. Slow top-down drift."""
    d = p3.S25()
    k = Vector(d["focus"])
    return dict(a=(tuple(k + Vector((-0.05, -0.08, 0.42))), tuple(k)), b=(tuple(k + Vector((0.05, -0.06, 0.38))), tuple(k)), lens=50,
                fstop=5.6, focus=tuple(k), cine=dict(exposure=-0.05))


# ============================================================================ "The two explanations could overlap..."
def S14():
    """The mended ancestor: the bundle, freshly bound, in cold moonlight from the doorway and the last of the fire."""
    R, c = _house_bundle(fire=0.4, moon=1.2)
    return dict(a=((c.x + 2.2, c.y + 1.2, 0.9), tuple(c)), b=((c.x + 1.8, c.y + 0.9, 0.8), tuple(c)), lens=35,
                fstop=2.8, focus=tuple(c), cine=dict(exposure=0.55, sat=0.8), hand_ok=("floor",))


# ============================================================================ "The final arrangement is what survives..."
def S15():
    """The two graves side by side at dusk, the composite bodies curled in them. Slow descent from above."""
    T, sk = p1.site("dusk", grass_at=None, kit=False, sun_az=205)
    c1, _ = sk["B1"].centre(); c2, _ = sk["B2"].centre()
    m = (c1 + c2) / 2
    return dict(a=((m.x + 0.8, m.y - 2.6, m.z + 4.6), tuple(m)), b=((m.x + 0.6, m.y - 2.0, m.z + 3.7), tuple(m)), lens=30,
                fstop=5.6, focus=tuple(m), cine=dict(exposure=0.35))


def S16():
    """Built above them: low along the trench floor, past the grave, to the house's drystone wall rising over it."""
    G.SCANNED = True
    T, sk = p1.site("golden", grass_at=None, kit=False, sun_az=215)
    c2, _ = sk["B2"].centre()
    hx, hy, r = U.HOUSES[2]
    a = math.atan2(c2.y - hy, c2.x - hx)
    wall = Vector((hx + r * math.cos(a), hy + r * math.sin(a), G.H(hx + (r - 0.3) * math.cos(a), hy + (r - 0.3) * math.sin(a)) + 0.3))
    mw = (c2 + wall) / 2
    return dict(a=((c2.x - 0.95, c2.y - 0.95, c2.z + 0.7), tuple(c2)), b=((c2.x - 0.8, c2.y - 0.8, c2.z + 0.85), tuple(mw)), lens=28,
                fstop=5.6, focus=tuple(c2), cine=dict(exposure=0.2))


def S17():
    """Night over the village: firelight in the three doorways, smoke under the moon; beneath the floors, the dead.
    Slow pull back and up."""
    U.CUT = False
    U.island("dusk", grass_at=(8, 0), grass_r=30, n=820, core=4.0, grass_density=220)
    BR.village(smoke_on=True)
    w = bpy.context.scene.world
    for n in w.node_tree.nodes:
        if n.type == 'BACKGROUND':
            n.inputs['Strength'].default_value *= 0.25
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.data.type == 'SUN':
            o.data.energy = 1.4; o.data.color = (0.55, 0.66, 1.0)   # a bright moon on the thatch
    for hx, hy, r in U.HOUSES:                        # hearth glow spilling out of each east doorway
        z = float(U.surface(hx + r * 1.75, hy))
        d = bpy.data.lights.new("doorglow", 'AREA'); d.size = 1.0; d.size_y = 1.4; d.shape = 'RECTANGLE'; d.energy = 90; d.color = (1.0, 0.5, 0.18)
        lo = bpy.data.objects.new("doorglow", d); bpy.context.scene.collection.objects.link(lo)
        lo.location = (hx + r * 1.75 + 0.25, hy, z + 0.8); lo.rotation_euler = (0, math.radians(90), 0)
        sp = bpy.data.lights.new("doorspill", 'SPOT'); sp.energy = 260; sp.color = (1.0, 0.5, 0.18); sp.spot_size = math.radians(70); sp.spot_blend = 0.7
        so = bpy.data.objects.new("doorspill", sp); bpy.context.scene.collection.objects.link(so)
        so.location = (hx + r * 1.75 - 0.2, hy, z + 1.2)                           # firelight spilling out over the ground
        so.rotation_euler = (Vector((1.0, 0, -0.7))).to_track_quat('-Z', 'Y').to_euler()
    return dict(a=((20, -12, 4.5), (0, 0, 3.6)), b=((30, -20, 8.5), (0, 0, 3.0)), lens=32, fstop=5.6, focus=(0, 0, 2), cine=dict(exposure=0.6))


# ----------------------------------------------------------------------------- plan
VO = [l.strip() for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "vo", "MUMMY_P5_VO.txt"),
                               encoding="utf-8").read().split("\n") if l.strip()]

PLAN = [  # shot, VO paragraph (1-based), seconds, description
    ("S01", 1, 4.5, "Night: the wrapped body at the roundhouse back wall, low glide"),
    ("S02", 2, 5.5, "Three parts of one figure in three pools of lamplight"),
    ("S03", 2, 5.0, "The household kneeling at the hearth, the ancestor beyond"),
    ("S04", 2, 4.5, "The dark skull alone in the light, the other parts dim"),
    ("S05", 3, 5.0, "Dusk: kin gathered at the house doorway"),
    ("S06", 3, 4.5, "The body raised on a stone platform with pots beside it"),
    ("S07", 4, 4.0, "The osteologist at the bench, over the shoulder"),
    ("S08", 4, 4.5, "The skull in darkness, raking light across the brow"),
    ("S09", 5, 4.5, "Three racks of sample tubes in the clean room"),
    ("S10", 6, 5.0, "Three bones in three pools of light, gaps of shadow"),
    ("S11", 7, 4.5, "Damage: the hide split, a bone end showing"),
    ("S12", 7, 5.0, "Repair: a fresh cord bound round the old hide"),
    ("S13", 7, 4.0, "The broken knee from above"),
    ("S14", 8, 5.0, "The mended ancestor in moonlight"),
    ("S15", 9, 5.0, "The two graves side by side at dusk"),
    ("S16", 9, 4.5, "Past the grave to the house wall built over it"),
    ("S17", 9, 6.0, "Night over the village"),
]
SHOTS = {sid: dict(fn=globals()[sid], dur=d, vo=VO[min(ln, len(VO)) - 1], line=ln, desc=desc) for sid, ln, d, desc in PLAN}
