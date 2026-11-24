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
    P2.bundle((bx, by, z0 + 0.2), rot=math.radians(rot), length=0.95, girth=0.42)
    return R, Vector((bx, by, z0 + 0.22))


def _kneeler(i, name, knees, heading, look, lean=12, var=0, hands=None):
    """An islander kneeling sitting back on the heels (from behind), hands resting on the thighs or at `hands`."""
    import acts as AC
    m = BR.islander_cropped(i, name=name, var=var)
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
    """The household at the hearth, seen from behind by the doorway: three islanders kneeling round the fire, and beyond
    it, at the back wall, the wrapped ancestor on its hurdle. Slow push between them."""
    R, c = _house_bundle(fire=1.0, moon=0.4)
    hx, hy = R["hearth"]
    look = (c.x, c.y, 0.6)
    for k, (dx, dy) in enumerate(((1.15, -1.0), (1.35, -0.1), (0.55, -1.6))):     # on the south-east side: the view past them stays open
        kn = (hx + dx, hy + dy)
        hd = math.degrees(math.atan2(c.y - kn[1], c.x - kn[0]))
        _kneeler(k % 2, f"Kin{k}", kn, hd, look, lean=10, var=k)
    return dict(a=((hx + 2.9, hy - 2.1, 1.55), (c.x, c.y, 0.4)), b=((hx + 2.5, hy - 1.8, 1.45), (c.x, c.y, 0.4)), lens=32,
                fstop=2.8, focus=(hx, hy, 0.4), cine=dict(exposure=0.45, sat=0.85), hand_ok=("floor",))


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
    import acts as AC
    hx, hy, r = U.HOUSES[1]
    door = Vector((hx + r * 1.75 + 0.4, hy, float(U.surface(hx + r * 1.75 + 0.4, hy))))
    for k, (dx, dy) in enumerate(((2.2, -0.9), (2.6, 0.5), (3.4, -0.2), (3.0, 1.4), (3.9, -1.3))):
        f = (door.x + dx, door.y + dy); zf = float(U.surface(*f))
        m = BR.islander_cropped(k % 2, name=f"Kin{k}", var=k + 1, ease=1.1)      # standing: tunic hangs straight
        st = AC.Stand(m, f, 180 + random.Random(k).uniform(-12, 12), lean=4, weight="L" if k % 2 else "R")
        st.finish(look=(door.x, door.y, door.z + 1.0 - zf), density=1.0); G.lift(st, zf + 0.012)      # boots on the trodden path
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
    """The osteologist at the bench (from behind, over the shoulder), the skeleton under the lamp - the
    evidence stops at the bones. Slow push past the shoulder."""
    L = p1.lab_body(osteo=True)
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.data.type in ('SUN', 'AREA') and "lamp" not in o.name.lower():
            o.data.energy *= 0.15
    t = Vector((0.0, 0.38, LB.TOP + 0.05))
    return dict(a=((0.55, -0.95, LB.TOP + 0.85), tuple(t)), b=((0.42, -0.78, LB.TOP + 0.75), tuple(t)), lens=35,
                fstop=4.0, focus=tuple(t), cine=dict(exposure=0.1), hand_ok=p1.OK if hasattr(p1, "OK") else ())


def S08():
    """The skull in darkness, one hard raking light across the eye socket and brow: what did they call this person?"""
    cs = _three_parts(lit=False)
    c = cs[0]
    _spot((c.x + 0.55, c.y + 0.05, c.z + 0.08), tuple(c), 60, size=0.02, color=(1.0, 0.86, 0.7), spot=12)
    return dict(a=((c.x + 0.05, c.y - 0.34, c.z + 0.03), tuple(c)), b=((c.x - 0.05, c.y - 0.33, c.z + 0.04), tuple(c)), lens=85,
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
    """Three bones, three pools of light in the dark, wide gaps of shadow between them: separate people - related or
    not, the tests cannot say. High, still, slow descent."""
    cs = _three_parts(lit=True)
    m = (cs[0] + cs[2]) / 2
    return dict(a=((m.x, m.y - 0.55, LB.TOP + 1.05), tuple(m)), b=((m.x, m.y - 0.42, LB.TOP + 0.85), tuple(m)), lens=35,
                fstop=5.6, focus=tuple(m), cine=dict(exposure=0.0))


# ============================================================================ "Another possibility is more practical..."
def S11():
    """Damage: close on the wrapped body - the old hide split along a fold, a dark bone end showing through. Firelight."""
    R, c = _house_bundle(fire=1.0, moon=0.2)
    sk = B.Skeleton("M", "C", name="Exposed")
    for s_ in list(sk.parts):
        if s_ != "forearmL":
            sk.remove(s_)
    o = sk.parts["forearmL"]; p3._knee_mats(o, sand=0.5)
    sk.root.rotation_euler = (0, math.radians(84), math.radians(90))
    bpy.context.view_layer.update()
    W = np.array([o.matrix_world @ v.co for v in o.data.vertices]); cc = W.mean(0)
    tip = Vector((c.x + 0.05, c.y - 0.42, c.z + 0.05))
    sk.root.location += Vector((tip.x - cc[0], tip.y - cc[1], tip.z - cc[2]))
    bpy.context.view_layer.update()
    t = Vector((c.x + 0.05, c.y - 0.45, c.z + 0.05))
    return dict(a=((t.x + 0.55, t.y - 0.45, t.z + 0.25), tuple(t)), b=((t.x + 0.42, t.y - 0.36, t.z + 0.2), tuple(t)), lens=50,
                fstop=2.8, focus=tuple(t), cine=dict(exposure=0.45, sat=0.85), hand_ok=("floor", "bundle"))


def S12():
    """Repair: an islander kneels at the bundle on the floor, binding a new cord round it (from behind, firelit)."""
    R, c = _house_bundle(fire=1.0, moon=0.2)
    kn = (c.x + 0.25, c.y - 0.75)
    hands = {"L": (c.x - 0.05, c.y - 0.2, c.z + 0.12), "R": (c.x + 0.18, c.y - 0.22, c.z + 0.1)}
    _kneeler(0, "Mender", kn, 90, (c.x, c.y, c.z), lean=42, var=0, hands=hands)
    return dict(a=((kn[0] + 1.1, kn[1] - 1.5, 1.35), (c.x, c.y - 0.2, 0.3)), b=((kn[0] + 0.9, kn[1] - 1.25, 1.25), (c.x, c.y - 0.2, 0.3)), lens=35,
                fstop=2.8, focus=(c.x, c.y - 0.3, 0.3), cine=dict(exposure=0.45, sat=0.85), hand_ok=("floor", "bundle", "hurdle"))


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
    return dict(a=((m.x + 1.0, m.y - 2.2, m.z + 3.6), tuple(m)), b=((m.x + 0.7, m.y - 1.6, m.z + 2.7), tuple(m)), lens=32,
                fstop=5.6, focus=tuple(m), cine=dict(exposure=0.35))


def S16():
    """Built above them: low along the trench floor, past the grave, to the house's drystone wall rising over it."""
    G.SCANNED = True
    T, sk = p1.site("golden", grass_at=None, kit=False, sun_az=215)
    c2, _ = sk["B2"].centre()
    hx, hy, r = U.HOUSES[2]
    a = math.atan2(c2.y - hy, c2.x - hx)
    wall = Vector((hx + r * math.cos(a), hy + r * math.sin(a), G.H(hx + (r - 0.3) * math.cos(a), hy + (r - 0.3) * math.sin(a)) + 0.3))
    return dict(a=((c2.x - 1.6, c2.y - 1.4, c2.z + 0.45), tuple(c2)), b=((c2.x - 1.3, c2.y - 1.1, c2.z + 0.6), tuple(wall)), lens=28,
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
            n.inputs['Strength'].default_value *= 0.12
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.data.type == 'SUN':
            o.data.energy = 0.35; o.data.color = (0.6, 0.7, 1.0)
    for hx, hy, r in U.HOUSES:                        # hearth glow spilling out of each east doorway
        z = float(U.surface(hx + r * 1.75, hy))
        d = bpy.data.lights.new("doorglow", 'AREA'); d.size = 1.0; d.size_y = 1.4; d.shape = 'RECTANGLE'; d.energy = 90; d.color = (1.0, 0.5, 0.18)
        lo = bpy.data.objects.new("doorglow", d); bpy.context.scene.collection.objects.link(lo)
        lo.location = (hx + r * 1.75 + 0.25, hy, z + 0.8); lo.rotation_euler = (0, math.radians(90), 0)
    return dict(a=((22, -14, 6), (0, 0, 2)), b=((34, -24, 12), (0, 0, 1.5)), lens=32, fstop=5.6, focus=(0, 0, 2), cine=dict(exposure=0.6))


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
    ("S12", 7, 5.0, "Repair: an islander binding a new cord round the bundle"),
    ("S13", 7, 4.0, "The broken knee from above"),
    ("S14", 8, 5.0, "The mended ancestor in moonlight"),
    ("S15", 9, 5.0, "The two graves side by side at dusk"),
    ("S16", 9, 4.5, "Past the grave to the house wall built over it"),
    ("S17", 9, 6.0, "Night over the village"),
]
SHOTS = {sid: dict(fn=globals()[sid], dur=d, vo=VO[min(ln, len(VO)) - 1], line=ln, desc=desc) for sid, ln, d, desc in PLAN}
