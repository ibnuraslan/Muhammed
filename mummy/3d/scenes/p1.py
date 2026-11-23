"""Part 1 (mummy/vo/MUMMY_P1_VO.txt): "Beneath a house in Scotland..." -> "...given that head someone else's jaw."  32 shots.

Each shot builds its set and cast and returns the camera move:
    dict(a=(loc, target), b=(loc, target), lens=, fstop=, focus=, cine=, hand_ok=)
House rules: no face toward the lens (backs, silhouettes, profiles in shadow); every hand belongs to a person in
frame; camera carries the motion; clipcheck 0; light is motivated (sun/sky, firelight, lab lamp and window).
"""
import math, os
import bpy
from mathutils import Vector
import uist as U, dig as G, cast as K, bones as B, lab as LB, bronze as BR

HAIR = float(os.environ.get("HAIR", "0.5"))
OK = ("trowel", "Uist", "fill", "tubby")


def site(mood="golden", grass_at=(0, 0), grass_r=26, focus=(0, 0), kit=True, burials=True, n=820, core=4.0, sun_az=None,
         grass_density=300):
    T = U.island(mood, grass_at=grass_at, grass_r=grass_r, n=n, core=core, focus=focus, sun_az=sun_az, grass_density=grass_density)
    G.houses()
    if kit:
        G.kit()
    sk = {}
    if burials:
        sk["B1"] = G.Grave(G.burial_scan("B1"))
        sk["B2"] = G.burial("B2", "M", "C", side="L")
    return T, sk


def team(*who):
    """The 2001 team in the north house, all facing away from the south-east (where the cameras are)."""
    out = []
    if "A" in who:
        out.append(K.kneel_trowel(K.DiggerA, (-1.0, 8.15), 128, work=(-1.45, 8.62), density=HAIR))
    if "B" in who:
        out.append(K.kneel_trowel(K.DiggerB, (1.05, 10.85), 165, work=(0.42, 11.05), density=HAIR))
    return out


# ============================================================================ "Beneath a house in Scotland..."
def S01():
    """Drone: in low over the Atlantic swell, across the white surf and the marram dunes; the dig appears ahead.
    Low sun from the north-west (left), so the dunes are rim-lit and throw long shadows toward the lens."""
    U.CUT = True
    T, sk = site("golden", grass_at=None, focus=(-190, -60), core=8.0, n=900, kit=True, burials=False, sun_az=150)
    U.scatter(T["terrain"], (-185, -70), 110, density=5.0, zone=(45, 160), scale=(1.2, 2.2), seed=4, name="MarramS01", avoid_cut=False)
    return dict(a=((-420, -260, 34), (-150, -40, 2)), b=((-175, -100, 40), (0, 0, 3)), lens=24, cine=dict(exposure=0.05))


def S02():
    """Crane down past the machair grass on the trench lip: the north house, two diggers at the graves (backs)."""
    site("golden", grass_at=(12.5, 3.5), grass_r=7, sun_az=200)
    team("A", "B")
    z = G.H(12, 3)
    return dict(a=((12.6, 2.6, z + 2.6), (-0.8, 9.4, 3.3)), b=((11.9, 3.3, z + 0.9), (-0.8, 9.6, 3.4)), lens=35,
                fstop=4.0, focus=(-0.8, 9.4, 3.4), hand_ok=OK)


def S03():
    """Top-down over the grave: the crouched skeleton in the sand, slowly turning."""
    T, sk = site("day", grass_at=None, kit=False, sun_az=215)
    c, size = sk["B1"].centre(); z = c.z
    return dict(a=((c.x + 0.25, c.y - 0.35, z + 2.3), (c.x, c.y, z)), b=((c.x - 0.3, c.y + 0.25, z + 1.85), (c.x, c.y, z)), lens=35,
                fstop=4.0, focus=(c.x, c.y, z))


def S04():
    """Low slider along the body at bone level: knees drawn up, hands at the face, the skull."""
    T, sk = site("day", grass_at=None, kit=False, sun_az=215)
    sp = sk["B1"].part_centre("skull"); fp = sk["B1"].part_centre("femurL")
    return dict(a=((-0.75, 8.05, 3.55), tuple(fp)), b=((-1.05, 9.55, 3.55), tuple(sp)), lens=50,
                fstop=2.8, focus=tuple((sp + fp) / 2))


def S05():
    """Macro: the skull in the ground; slow push, focus on the teeth."""
    T, sk = site("day", grass_at=None, kit=False, sun_az=215)
    sp = sk["B1"].part_centre("skull")
    d = Vector((-0.75, -0.35, 0.0)).normalized()
    a = sp + d * 1.5 + Vector((0, 0, 0.8)); b = sp + d * 1.2 + Vector((0, 0, 0.62))
    return dict(a=(tuple(a), tuple(sp)), b=(tuple(b), tuple(sp)), lens=70, fstop=4.0, focus=tuple(sp))


# ============================================================================ the lab: skull, jaw, the third man
def _cork_ring(x, y, z, r=0.05):
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.012, location=(x, y, z + 0.012))
    o = bpy.context.active_object; o.name = "corkring"
    m = bpy.data.materials.new("cork"); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (0.12, 0.07, 0.035, 1); p.inputs['Roughness'].default_value = 0.95
    o.data.materials.append(m)
    return o


def lab_skull(inverted=True, with_jaw=False, lamp_energy=22.0):
    A = LB.room(window_light=0.45, lamp=True, lamp_at=(0.45, 0.6), lamp_target=(-0.05, 0.35), lamp_energy=lamp_energy)
    LB.velvet(-0.6, 0.6, 0.0, 0.75, LB.TOP)
    cr = B.hero_cranium(healed=True, tone="A")
    if inverted:                     # resting upside down on a cork ring: the palate and the tooth row face up
        _cork_ring(0.0, 0.35, LB.TOP)
        cr.rotation_euler = (math.pi, 0, math.radians(200))
        bpy.context.view_layer.update()
        import numpy as np
        co = np.array([cr.matrix_world @ v.co for v in cr.data.vertices[:]])
        cr.location = (0.0, 0.35, LB.TOP + 0.03 - co[:, 2].min() + cr.location.z)
    else:
        _cork_ring(0.0, 0.35, LB.TOP)
        bpy.context.view_layer.update()
        import numpy as np
        co = np.array([v.co for v in cr.data.vertices])
        cr.location = (0.0, 0.35, LB.TOP + 0.026 - co[:, 2].min() * 0.92)
    bpy.context.view_layer.update()
    out = dict(cr=cr, A=A)
    if with_jaw:
        md = B.hero_mandible(tone="B")
        import numpy as np
        co = np.array([v.co for v in md.data.vertices])
        md.location = (0.2, 0.3, LB.TOP + 0.004 - co[:, 2].min()); md.rotation_euler = (0, 0, math.radians(-25))
        out["md"] = md
    bpy.context.view_layer.update()
    return out


def S06():
    """The cranium upside down on its ring: slow orbit to the smooth healed ridge where the back teeth were."""
    L = lab_skull(inverted=True)
    c = Vector((0.0, 0.35, LB.TOP + 0.13))
    return dict(a=((-0.42, 0.05, LB.TOP + 0.55), tuple(c)), b=((-0.18, -0.12, LB.TOP + 0.6), tuple(c)), lens=60,
                fstop=4.0, focus=tuple(c), cine=dict(exposure=-0.1))


def S07():
    """The mandible on black velvet, teeth up: a slow arc from above; every lower tooth still in place."""
    A = LB.room(window_light=0.4, lamp=True, lamp_at=(0.4, 0.62), lamp_target=(0.0, 0.3), lamp_energy=20)
    LB.velvet(-0.6, 0.6, 0.0, 0.75, LB.TOP)
    md = B.hero_mandible(tone="B")
    import numpy as np
    co = np.array([v.co for v in md.data.vertices])
    md.location = (0.0, 0.32, LB.TOP + 0.003 - co[:, 2].min()); md.rotation_euler = (0, 0, math.radians(15))
    bpy.context.view_layer.update()
    W = np.array([md.matrix_world @ v.co for v in md.data.vertices])
    t = Vector(((W.min(0) + W.max(0)) / 2).tolist())
    return dict(a=(tuple(t + Vector((-0.22, -0.28, 0.3))), tuple(t)), b=(tuple(t + Vector((0.08, -0.33, 0.28))), tuple(t)),
                lens=70, fstop=5.6, focus=tuple(t), cine=dict(exposure=-0.1))


def S08():
    """Skull and jaw side by side: the jaw does not belong to this head. Pull back."""
    L = lab_skull(inverted=False, with_jaw=True)
    c = Vector((0.1, 0.33, LB.TOP + 0.07))
    return dict(a=((0.05, -0.1, LB.TOP + 0.12), tuple(c)), b=((0.1, -0.38, LB.TOP + 0.22), tuple(c)), lens=45,
                fstop=4.0, focus=tuple(c))


def lab_body(osteo=True):
    """The post-cranial skeleton laid out supine on the bench (no skull: the head is from someone else)."""
    A = LB.room(window_light=1.0, lamp=True, lamp_at=(-0.2, 0.62), lamp_target=(0.3, 0.35), lamp_energy=24)
    LB.velvet(-1.15, 1.2, 0.0, 0.78, LB.TOP)
    sk = B.Skeleton("M", "C", name="Third", sand=0.5)
    sk.remove("skull", "mandible")
    sk.root.rotation_euler = (math.radians(-90), 0, math.radians(-90))
    bpy.context.view_layer.update()
    sk.root.location = (0.0, 0.38, 0)
    bpy.context.view_layer.update()
    import numpy as np
    zmin = min((o.matrix_world @ v.co).z for o in sk.parts.values() for v in o.data.vertices[:])
    xs = [(o.matrix_world @ v.co).x for o in sk.parts.values() for v in o.data.vertices[:]]
    sk.root.location = (-(min(xs) + max(xs)) / 2, 0.38, LB.TOP + 0.004 - zmin)
    bpy.context.view_layer.update()
    sk.settle(lambda x, y: LB.TOP + 0.004, sink=0.0, keep=0.55)      # every bone rests on the velvet
    out = dict(A=A, sk=sk)
    if osteo:
        import acts as AC
        m = K.Osteologist()
        st = AC.Stand(m, (0.15, -0.42), 90, lean=12)
        st.hand("L", (-0.05, 0.12, LB.TOP + 0.02), elbow=(0.6, 0.2, -0.8), curl=18)
        st.hand("R", (0.32, 0.18, LB.TOP + 0.03), elbow=(0.6, 0.2, -0.8), curl=24)
        st.head_to((0.1, 0.4, LB.TOP), share=0.9)
        st.finish(look=(0.1, 0.4, LB.TOP), density=HAIR)
        out["st"] = st
    return out


def S09():
    """The rest of the skeleton on the bench under the lamp: low, shallow-focus dolly from the knees up to the pelvis."""
    lab_body(osteo=False)
    return dict(a=((-0.95, -0.2, LB.TOP + 0.2), (-0.35, 0.38, LB.TOP + 0.05)), b=((-0.45, -0.3, LB.TOP + 0.22), (0.1, 0.38, LB.TOP + 0.05)), lens=50,
                fstop=2.8, focus=(-0.15, 0.38, LB.TOP + 0.05), cine=dict(exposure=-0.15))

def S10():
    """Pelvis and femur under the lamp: the body belongs to a third man."""
    L = lab_body(osteo=False)
    sk = L["sk"]
    p = sk.world_pivot("pelvis"); f = sk.world_pivot("femurR")
    t = (p + f) / 2 + Vector((0, 0, 0.03))
    return dict(a=(tuple(t + Vector((-0.12, -0.55, 0.28))), tuple(t)), b=(tuple(t + Vector((0.06, -0.38, 0.2))), tuple(t)), lens=60,
                fstop=3.5, focus=tuple(t))


# ============================================================================ "...arranged to look like one" / another body
def S11():
    """High overhead of the crouched figure: one body - slow rise."""
    T, sk = site("overcast", grass_at=None, kit=False)
    c, size = sk["B1"].centre()
    return dict(a=((c.x + 0.1, c.y - 0.12, c.z + 1.3), (c.x, c.y, c.z)), b=((c.x + 0.25, c.y - 0.2, c.z + 4.0), (c.x, c.y, c.z)), lens=32,
                fstop=5.6, focus=(c.x, c.y, c.z))


def S12():
    """Pan off the first grave across the house floor to the second burial."""
    site("overcast", grass_at=None, kit=True)
    p1 = U.PITS["B1"]; p2 = U.PITS["B2"]
    z = G.H(p1[0], p1[1])
    return dict(a=((-3.9, 6.6, z + 1.35), (p1[0], p1[1], z)), b=((-3.7, 6.9, z + 1.4), (p2[0], p2[1], z)), lens=35,
                fstop=5.6, focus=(p2[0], p2[1], z))


# ============================================================================ "It's 2001..."
def S13():
    """Wide drone: South Uist's Atlantic coast, surf, machair strips, lochans, the hills behind."""
    site("golden", grass_at=None, focus=(-230, -200), core=10.0, n=900, kit=False, burials=False, sun_az=195)
    return dict(a=((-470, -560, 190), (-120, 120, 0)), b=((-430, -470, 175), (-90, 150, 0)), lens=26)


def S14():
    """The site at work in 2001: low across the machair grass, the trench, diggers (backs), spoil heap and barrows. Crane up."""
    site("day", grass_at=(14, -18), grass_r=10)
    team("A", "B")
    K.stand(K.DiggerC, (13.4, -6.3), 25, look=(14.5, -5.8, 5.0), density=HAIR, hands="front")
    K.stand(K.Director, (11.6, 2.2), 175, look=(-1, 9, 3.5), density=HAIR)
    z = G.H(15, -19)
    return dict(a=((15.5, -19.5, z + 0.6), (2, 4, 3.8)), b=((15.0, -18.8, z + 4.2), (1, 4, 3.4)), lens=28, fstop=8.0, focus=(4, 0, 3.6),
                hand_ok=OK + ("sieve",))


def S15():
    """The director on the lip of the trench, from behind, looking over the north house."""
    site("day", grass_at=(13, 2), grass_r=16)
    team("A", "B")
    st = K.stand(K.Director, (11.6, 2.2), 168, look=(-1, 9, 3.5), density=HAIR)
    z = G.H(11.6, 2.2)
    return dict(a=((15.6, 1.2, z + 1.8), (-1.0, 8.6, z - 0.9)), b=((14.6, 1.5, z + 1.75), (-1.0, 8.9, z - 1.0)), lens=35,
                fstop=4.0, focus=(11.6, 2.2, z + 1.6), hand_ok=OK)


# ============================================================================ "Sand has buried layers..."
def S16():
    """The north section: pale shell sand banded with dark floors. Crane down the face in raking light."""
    site("golden", grass_at=(2, 18), grass_r=8, kit=False, burials=False, sun_az=192)
    y = U.DIG["y1"]
    return dict(a=((1.2, y - 2.6, 5.4), (2.6, y, 4.4)), b=((1.6, y - 2.2, 3.85), (2.6, y, 3.85)), lens=32,
                fstop=5.6, focus=(2.6, y, 4.2))


def S17():
    """A digger cleaning the lower section face with a trowel, seen from behind-left; the strata fill the frame."""
    site("golden", grass_at=(4, 18), grass_r=8, kit=False, burials=False, sun_az=192)
    y = U.DIG["y1"]
    K.kneel_trowel(K.DiggerA, (4.2, y - 1.7), 92, work=(4.25, y - 1.12), density=HAIR)
    z = G.H(4.2, y - 1.7)
    return dict(a=((4.75, y - 3.7, z + 1.6), (4.0, y - 0.9, z + 0.55)), b=((4.45, y - 3.4, z + 1.5), (3.95, y - 0.9, z + 0.55)), lens=35,
                fstop=4.0, focus=(4.2, y - 1.3, z + 0.5), hand_ok=OK)


def _ard_marks(cx, cy, w=2.6, n=11, seed=1):
    """Criss-cross ard furrows: soft, broken, dark sandy bands in the paler sand, two crossing directions."""
    import random
    rng = random.Random(seed)
    m = bpy.data.materials.new("ard"); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; Lk = nt.links
    p = N["Principled BSDF"]; p.inputs['Base Color'].default_value = (0.07, 0.05, 0.035, 1); p.inputs['Roughness'].default_value = 0.95
    uv = N.new("ShaderNodeUVMap"); sp = N.new("ShaderNodeSeparateXYZ"); Lk.new(uv.outputs[0], sp.inputs[0])
    d = N.new("ShaderNodeMath"); d.operation = 'SUBTRACT'; d.inputs[1].default_value = 0.5; Lk.new(sp.outputs['Y'], d.inputs[0])
    ab = N.new("ShaderNodeMath"); ab.operation = 'ABSOLUTE'; Lk.new(d.outputs[0], ab.inputs[0])
    edge = N.new("ShaderNodeMapRange"); edge.inputs['From Min'].default_value = 0.5; edge.inputs['From Max'].default_value = 0.1
    Lk.new(ab.outputs[0], edge.inputs['Value'])
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 3.5; nz.inputs['Detail'].default_value = 8
    Lk.new(tc.outputs['Object'], nz.inputs['Vector'])
    br = N.new("ShaderNodeMapRange"); br.inputs['From Min'].default_value = 0.35; br.inputs['From Max'].default_value = 0.65
    Lk.new(nz.outputs['Fac'], br.inputs['Value'])
    al = N.new("ShaderNodeMath"); al.operation = 'MULTIPLY'; Lk.new(edge.outputs[0], al.inputs[0]); Lk.new(br.outputs[0], al.inputs[1])
    al2 = N.new("ShaderNodeMath"); al2.operation = 'MULTIPLY'; al2.inputs[1].default_value = 1.0; Lk.new(al.outputs[0], al2.inputs[0])
    Lk.new(al2.outputs[0], p.inputs['Alpha'])
    for dirn, ang in ((0, 0.12), (1, 1.5)):
        for k in range(n):
            off = (k - n / 2) * w / n + rng.uniform(-0.08, 0.08)
            a = ang + rng.uniform(-0.06, 0.06)
            c, s_ = math.cos(a), math.sin(a)
            along = rng.uniform(-0.4, 0.4)
            x = cx - s_ * off + c * along; y = cy + c * off + s_ * along
            bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y, G.H(x, y) + 0.002)); o = bpy.context.active_object
            o.scale = (w * rng.uniform(0.45, 0.9), rng.uniform(0.05, 0.11), 1); o.rotation_euler.z = a; o.name = "ard"
            o.data.materials.append(m); o.visible_shadow = False


def S18():
    """Ard marks scored in the old ground surface; push in low across them."""
    site("golden", grass_at=None, kit=False, burials=False, sun_az=200)
    _ard_marks(6.8, -3.0)
    z = G.H(6.8, -3.0)
    return dict(a=((8.6, -4.9, z + 0.75), (6.6, -2.8, z)), b=((7.9, -4.1, z + 0.45), (6.5, -2.7, z)), lens=35,
                fstop=4.0, focus=(6.8, -3.0, z))


# ============================================================================ "Later, they built houses over it."
def bronze_site(mood="dawn", grass_r=40, focus=(0, 0)):
    U.CUT = False
    T = U.island(mood, grass_at=(0, 0), grass_r=grass_r, n=820, core=4.0, focus=focus, grass_density=220)
    BR.village(smoke_on=True)
    return T


def S19():
    """Dawn: the three roundhouses on the machair, roofs touching, smoke rising. Drone arc."""
    bronze_site("dawn")
    return dict(a=((42, -30, 17), (0, 0, 4.5)), b=((30, -38, 13), (0, 1, 4.0)), lens=28, cine=dict(exposure=0.1))


def S20():
    """Top-down: three thatched roofs in a row. Rise."""
    bronze_site("dawn")
    return dict(a=((4.0, -0.3, 24), (0.3, 0.2, 0)), b=((4.4, -0.2, 40), (0.3, 0.3, 0)), lens=28)


def S21():
    """Inside, looking east: the low sun through the doorway lays a long bar of light across the floor."""
    U.CUT = False
    BR.interior(fire=0.6, door_sun=1.0)
    return dict(a=((-2.3, 0.6, 1.35), (4.9, 0.0, 0.9)), b=((-0.9, 0.35, 1.25), (4.9, 0.0, 0.85)), lens=24,
                fstop=4.0, focus=(4.9, 0, 0.9), cine=dict(exposure=0.25))


def S22():
    """The hearth: a man kneels at the fire (silhouette, back to us); pots, quern, smoke in the air. Slow dolly."""
    U.CUT = False
    R = BR.interior(fire=1.0, door_sun=0.4)
    import acts as AC
    m = BR.Islander()
    hx, hy = R["hearth"]
    st = AC.Kneel(m, (hx - 1.1, hy + 0.55), -24, lean=40, sit_back=True)
    st.hand("R", (hx - 0.62, hy + 0.3, 0.12), elbow=(0.6, 0.2, -0.8), curl=30)
    st.hand("L", (hx - 0.9, hy + 0.15, 0.42), elbow=(0.6, 0.3, -0.8), curl=20)
    st.head_to((hx, hy, 0.3), share=0.8)
    st.finish(look=(hx, hy, 0.3), density=HAIR)
    return dict(a=((hx - 2.55, hy - 1.45, 0.78), (hx - 0.3, hy + 0.2, 0.5)), b=((hx - 2.2, hy - 1.15, 0.72), (hx - 0.3, hy + 0.2, 0.5)), lens=32,
                fstop=2.8, focus=(hx - 1.0, hy + 0.5, 0.7), cine=dict(exposure=0.2), hand_ok=("floor", "stone"))


# ============================================================================ "Floor after floor has survived beneath the sand."
def S23():
    """Back to 2001: the same house floor in the trench - revetment ring and hearth. Crane down."""
    U.CUT = True
    site("golden", grass_at=(9, -9), grass_r=14, kit=True, burials=True, sun_az=205)
    return dict(a=((9.5, -9.0, 9.5), (0.6, 0.5, 3.4)), b=((6.6, -6.0, 5.6), (0.6, 0.5, 3.3)), lens=28, fstop=8.0, focus=(0.6, 0.0, 3.3))


# ============================================================================ "Under the northern house are the two adults."
def S24():
    """Crane in over the north house to the two graves side by side (overcast)."""
    U.CUT = True
    site("overcast", grass_at=None, kit=True)
    return dict(a=((3.6, 4.2, 7.2), (-1.1, 10.0, 3.3)), b=((1.6, 6.4, 5.3), (-1.1, 10.1, 3.3)), lens=30,
                fstop=5.6, focus=(-1.1, 10.0, 3.3))


def S25():
    """The second body, top-down: tightly curled."""
    T, sk = site("overcast", grass_at=None, kit=False)
    c, size = sk["B2"].centre()
    return dict(a=((c.x + 0.25, c.y - 0.3, c.z + 2.1), (c.x, c.y, c.z)), b=((c.x - 0.15, c.y + 0.2, c.z + 1.7), (c.x, c.y, c.z)), lens=35,
                fstop=4.0, focus=(c.x, c.y, c.z))


def S26():
    """Macro in the grave: the jaw under the skull of the first body; rack from skull to jaw."""
    T, sk = site("day", grass_at=None, kit=False, sun_az=215)
    sp = sk["B1"].part_centre("skull"); jp = sk["B1"].part_centre("mandible")
    d = Vector((0.6, -0.4, 0)).normalized()
    return dict(a=(tuple(sp + d * 1.4 + Vector((0, 0, 0.7))), tuple(sp)), b=(tuple(jp + d * 1.1 + Vector((0, 0, 0.55))), tuple(jp)),
                lens=85, fstop=2.8, focus=tuple(jp))


def S27():
    """Lab macro: the healed upper jaw - smooth bone where the chewing teeth were."""
    L = lab_skull(inverted=True, lamp_energy=18)
    cr = L["cr"]
    import numpy as np
    co = np.array([cr.matrix_world @ v.co for v in cr.data.vertices])
    top = co[co[:, 2] > co[:, 2].max() - 0.03]                    # the tooth row (now facing up)
    c = Vector(top.mean(0))
    return dict(a=(tuple(c + Vector((-0.16, -0.12, 0.1))), tuple(c)), b=(tuple(c + Vector((-0.1, -0.15, 0.08))), tuple(c)), lens=100,
                fstop=5.6, focus=tuple(c))


def S28():
    """The lower molars: wear facets polished by teeth that met them."""
    A = LB.room(window_light=0.6, lamp=True, lamp_at=(0.35, 0.6), lamp_target=(0.0, 0.3), lamp_energy=18)
    LB.velvet(-0.6, 0.6, 0.0, 0.75, LB.TOP)
    md = B.hero_mandible(tone="B")
    import numpy as np
    co = np.array([v.co for v in md.data.vertices])
    md.location = (0.0, 0.32, LB.TOP + 0.003 - co[:, 2].min()); md.rotation_euler = (0, 0, math.radians(-70))
    bpy.context.view_layer.update()
    L_ = np.array([v.co for v in md.data.vertices])
    body = L_[:, 1] < L_[:, 1].min() + 0.6 * np.ptp(L_[:, 1])            # the tooth-bearing body (chin -> molars)
    zt = L_[body, 2].max()
    teeth = body & (L_[:, 2] > zt - 0.008) & (L_[:, 1] > L_[:, 1].min() + 0.03)     # premolar/molar crowns
    c = md.matrix_world @ Vector(L_[teeth].mean(0).tolist())
    return dict(a=(tuple(c + Vector((-0.12, -0.09, 0.06))), tuple(c)), b=(tuple(c + Vector((-0.08, -0.1, 0.05))), tuple(c)), lens=100,
                fstop=5.6, focus=tuple(c))


def S29():
    """The jaw offered up under the skull on foam blocks: its teeth meet a toothless upper jaw. Slow push, side-on."""
    L = lab_skull(inverted=False, with_jaw=True)
    cr, md = L["cr"], L["md"]
    import numpy as np
    lift = 0.085
    foam = bpy.data.materials.new("foam"); foam.use_nodes = True
    foam.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.05, 0.05, 0.055, 1)
    foam.node_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = 0.95
    for o in bpy.data.objects:
        if o.name.startswith("corkring"):
            o.location.z += lift
    cr.location.z += lift
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cr.location.x, cr.location.y + 0.03, LB.TOP + lift / 2)); fb = bpy.context.active_object
    fb.scale = (0.12, 0.1, lift); fb.data.materials.append(foam); fb.name = "foamblock"
    bpy.context.view_layer.update()
    co = np.array([cr.matrix_world @ v.co for v in cr.data.vertices])
    front = co[co[:, 1] < co[:, 1].min() + 0.05]
    zt = float(front[:, 2].min()); yf = float(co[:, 1].min())
    mco = np.array([v.co for v in md.data.vertices])
    md.rotation_euler = (0, 0, 0)
    md.location = (cr.location.x - (mco[:, 0].min() + mco[:, 0].max()) / 2,
                   yf + 0.006 - mco[:, 1].min(), zt - 0.003 - mco[:, 2].max())
    bpy.ops.mesh.primitive_cube_add(size=1, location=(md.location.x, md.location.y + 0.0, LB.TOP + (zt - 0.003 - (mco[:, 2].max() - mco[:, 2].min()) - LB.TOP) / 2))
    fb2 = bpy.context.active_object; fb2.name = "foamblock2"; fb2.data.materials.append(foam)
    hgt = max(0.004, zt - 0.003 - (mco[:, 2].max() - mco[:, 2].min()) - LB.TOP)
    fb2.scale = (0.05, 0.04, hgt); fb2.location.z = LB.TOP + hgt / 2
    c = Vector((cr.location.x, yf + 0.04, zt))
    return dict(a=(tuple(c + Vector((0.42, -0.14, 0.03))), tuple(c)), b=(tuple(c + Vector((0.3, -0.1, 0.02))), tuple(c)), lens=60,
                fstop=5.6, focus=tuple(c), cine=dict(exposure=-0.1))


def _glass(name="glass"):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Transmission Weight'].default_value = 1.0; p.inputs['Roughness'].default_value = 0.05; p.inputs['IOR'].default_value = 1.5
    return m


def _plain(name, col, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    return m


def lab_femur(x=0.05, y=0.36, yaw=8):
    sk = B.Skeleton("M", "C", name="Leg")
    for s_ in list(sk.parts):
        if s_ != "femurR":
            sk.remove(s_)
    fe = sk.parts["femurR"]
    sk.root.rotation_euler = (0, math.radians(90), math.radians(yaw))
    bpy.context.view_layer.update()
    import numpy as np
    W = np.array([fe.matrix_world @ v.co for v in fe.data.vertices])
    sk.root.location = Vector((x - W[:, 0].mean(), y - W[:, 1].mean(), LB.TOP + 0.004 - W[:, 2].min()))
    bpy.context.view_layer.update()
    W = np.array([fe.matrix_world @ v.co for v in fe.data.vertices])
    return fe, W


def S30():
    """Sampling for isotopes: a fresh drill hole in the thigh bone, a little heap of bone powder, sample tubes in a rack,
    the drill laid down beside it. Slow slider under the lamp."""
    A = LB.room(window_light=0.35, lamp=True, lamp_at=(0.3, 0.62), lamp_target=(0.05, 0.34), lamp_energy=22)
    LB.velvet(-0.6, 0.7, 0.0, 0.78, LB.TOP)
    import numpy as np
    fe, W = lab_femur()
    mid = W[np.abs(W[:, 0] - W[:, 0].mean()) < 0.02]
    hole = Vector((float(W[:, 0].mean()), float(mid[:, 1].mean()), float(mid[:, 2].max())))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0045, depth=0.006, location=hole + Vector((0, 0, -0.001)))
    h = bpy.context.active_object; h.name = "drillhole"; h.data.materials.append(_plain("hole", (0.03, 0.02, 0.012), 0.9))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012, location=(hole.x + 0.03, hole.y - 0.05, LB.TOP + 0.002))
    pw = bpy.context.active_object; pw.scale = (1, 1, 0.3); pw.name = "bonepowder"; pw.data.materials.append(_plain("powder", (0.7, 0.62, 0.5), 0.95))
    # tube rack with capped sample tubes
    rack = _plain("rack", (0.85, 0.85, 0.82), 0.4); cap = _plain("cap", (0.05, 0.25, 0.55), 0.4); gl = _glass()
    bpy.ops.mesh.primitive_cube_add(size=1, location=(hole.x + 0.18, hole.y + 0.12, LB.TOP + 0.02)); rk = bpy.context.active_object
    rk.scale = (0.14, 0.04, 0.04); rk.data.materials.append(rack); rk.name = "rack"
    for k in range(5):
        tx = hole.x + 0.125 + k * 0.026
        bpy.ops.mesh.primitive_cylinder_add(radius=0.0075, depth=0.07, location=(tx, hole.y + 0.12, LB.TOP + 0.05)); t = bpy.context.active_object
        t.data.materials.append(gl); t.name = "tube"
        bpy.ops.mesh.primitive_cylinder_add(radius=0.0085, depth=0.012, location=(tx, hole.y + 0.12, LB.TOP + 0.09)); c = bpy.context.active_object
        c.data.materials.append(cap); c.name = "tubecap"
    # the drill handpiece and its burr, laid on the velvet
    steel = _plain("drillsteel", (0.6, 0.6, 0.62), 0.3, 1.0)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.009, depth=0.15, location=(hole.x - 0.08, hole.y - 0.1, LB.TOP + 0.01)); d = bpy.context.active_object
    d.rotation_euler = (0, math.radians(90), math.radians(-30)); d.data.materials.append(steel); d.name = "drill"
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0015, depth=0.03, location=(hole.x - 0.015, hole.y - 0.137, LB.TOP + 0.01)); bu = bpy.context.active_object
    bu.rotation_euler = (0, math.radians(90), math.radians(-30)); bu.data.materials.append(steel); bu.name = "burr"
    return dict(a=(tuple(hole + Vector((-0.28, -0.3, 0.16))), tuple(hole)), b=(tuple(hole + Vector((-0.14, -0.34, 0.15))), tuple(hole + Vector((0.04, 0.02, 0)))),
                lens=60, fstop=3.2, focus=tuple(hole), cine=dict(exposure=-0.1))


def S31():
    """Three parts, three men: skull, jaw and thigh bone laid apart on the velvet. Overhead push."""
    A = LB.room(window_light=0.8, lamp=True, lamp_at=(0.0, 0.66), lamp_target=(0.0, 0.35), lamp_energy=24)
    LB.velvet(-0.8, 0.8, 0.0, 0.78, LB.TOP)
    import numpy as np
    cr = B.hero_cranium(healed=True, tone="A")
    co = np.array([v.co for v in cr.data.vertices]); cr.location = (-0.42, 0.38, LB.TOP + 0.004 - co[:, 2].min() * 0.97)
    cr.rotation_euler = (0, 0, math.radians(-30))
    md = B.hero_mandible(tone="B")
    co = np.array([v.co for v in md.data.vertices]); md.location = (-0.08, 0.36, LB.TOP + 0.003 - co[:, 2].min())
    md.rotation_euler = (0, 0, math.radians(-20))
    sk = B.Skeleton("M", "C", name="Leg")
    for s in list(sk.parts):
        if s != "femurR":
            sk.remove(s)
    fe = sk.parts["femurR"]
    sk.root.rotation_euler = (0, math.radians(90), math.radians(8))
    bpy.context.view_layer.update()
    W = np.array([fe.matrix_world @ v.co for v in fe.data.vertices])
    sk.root.location = Vector((0.4 - W[:, 0].mean(), 0.38 - W[:, 1].mean(), LB.TOP + 0.004 - W[:, 2].min()))
    return dict(a=((-0.62, -0.42, LB.TOP + 0.32), (0.05, 0.37, LB.TOP + 0.04)), b=((-0.42, -0.5, LB.TOP + 0.3), (0.08, 0.37, LB.TOP + 0.04)), lens=32,
                fstop=4.0, focus=(-0.08, 0.36, LB.TOP + 0.03))


def S32():
    """Back in the grave at last light: the head of one man above the body of another. Slow push to the skull."""
    T, sk = site("dusk", grass_at=None, kit=False, sun_az=200)
    sp = sk["B1"].part_centre("skull"); tp = sk["B1"].part_centre("thorax")
    return dict(a=(tuple(tp + Vector((0.9, -0.9, 0.55))), tuple((sp + tp) / 2)), b=(tuple(tp + Vector((0.55, -0.6, 0.35))), tuple(sp)), lens=50,
                fstop=2.8, focus=tuple(sp), cine=dict(exposure=0.3))


VO = [l.strip() for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "vo", "MUMMY_P1_VO.txt"),
                               encoding="utf-8").read().split("\n") if l.strip()]

PLAN = [  # shot, VO paragraph (1-based), seconds (first estimate at 140 wpm; re-timed to the recorded VO), description
    ("S01", 1, 6.5, "Drone in over the Atlantic surf and dunes to the dig on the machair (golden hour)"),
    ("S02", 1, 5.0, "Crane down over the trench lip to the north house: two diggers at the graves (backs)"),
    ("S03", 1, 4.0, "Top-down: the crouched skeleton in its grave, knees to chest"),
    ("S04", 2, 4.5, "Low slider along the body at bone level, raking sun"),
    ("S05", 3, 3.5, "Macro on the skull in the ground"),
    ("S06", 4, 4.5, "Lab: cranium upside down on a cork ring; orbit to the healed ridge where the molars were"),
    ("S07", 4, 4.0, "Lab: the mandible, worn molars still in place (macro slide)"),
    ("S08", 5, 3.5, "Skull and jaw side by side: they do not belong together"),
    ("S09", 6, 4.0, "Lab: the rest of the skeleton on the bench under the lamp; dolly along it"),
    ("S10", 6, 3.5, "Pelvis and femur under the lamp: a third man"),
    ("S11", 7, 3.5, "Overhead of the crouched figure: one body"),
    ("S12", 7, 4.0, "Pan across the house floor to the second grave"),
    ("S13", 8, 6.0, "Wide drone: South Uist's west coast, surf, machair, lochans, hills"),
    ("S14", 8, 5.0, "The site in 2001: marquee, spoil, barrows, diggers in the trench; crane up"),
    ("S15", 8, 4.0, "The director at the trench edge, from behind"),
    ("S16", 9, 5.0, "The section face: shell sand banded with dark floors; crane down"),
    ("S17", 9, 4.5, "A digger cleans the section with a trowel (from behind)"),
    ("S18", 9, 5.0, "Ard marks in the old ground surface"),
    ("S19", 9, 4.5, "Dawn: the three roundhouses on the machair, smoke rising (drone arc)"),
    ("S20", 10, 4.0, "Top-down onto the three conjoined roofs"),
    ("S21", 10, 4.0, "Inside: sunrise through the east doorway, a bar of light on the floor"),
    ("S22", 10, 6.0, "The hearth: a man kneels at the fire (silhouette); pots, quern, smoke"),
    ("S23", 10, 5.0, "2001 again: the same house floor in the trench; crane down"),
    ("S24", 11, 3.5, "Crane in over the north house to the two graves"),
    ("S25", 12, 4.5, "The second body from above: tightly curled"),
    ("S26", 12, 3.5, "Macro in the grave: skull and jaw of the first body"),
    ("S27", 13, 5.0, "Lab macro: the healed upper jaw, smooth bone where the molars were"),
    ("S28", 13, 4.5, "The lower molars: wear facets from teeth that met them"),
    ("S29", 14, 3.5, "The jaw offered up to the skull: its teeth meet nothing"),
    ("S30", 15, 6.0, "Sampling for isotopes: a drill hole in the thigh bone, bone powder, sample tubes"),
    ("S31", 15, 4.5, "Skull, jaw and thigh bone laid apart: three men"),
    ("S32", 16, 6.5, "The grave at last light: the head of one man above the body of another"),
]
SHOTS = {sid: dict(fn=globals()[sid], dur=d, vo=VO[min(ln, len(VO)) - 1], line=ln, desc=desc) for sid, ln, d, desc in PLAN}
