"""Part 3 (mummy/vo/MUMMY_P3_VO.txt): "And at some point, preserved parts..." -> "The rest was moved beneath the house."

Same contract and house rules as p1/p2: each shot builds its set and cast and returns the camera move.
No face toward the lens; every hand belongs to a person in frame; clipcheck 0; motivated light; no text in frame.
"""
import math, os, random
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
import uist as U, dig as G, cast as K, bones as B, lab as LB, bronze as BR, p2sets as P2, sf, ph
import p1, p2

HAIR = p1.HAIR
_plain, _glass, _spot, _haze = p1._plain, p1._glass, p2._spot, p2._haze


# ----------------------------------------------------------------------------- helpers
def lab_part(seg, sex="F", tone="C", x=0.0, y=0.38, yaw=0.0, name=None, keep=()):
    """One body segment (or a few) of the ZBrush skeleton laid flat on the velvet: long axis levelled by PCA."""
    sk = B.Skeleton(sex, tone, name=name or ("Part_" + seg))
    for s_ in list(sk.parts):
        if s_ != seg and s_ not in keep:
            sk.remove(s_)
    objs = list(sk.parts.values())
    if seg == "pelvis":                       # lying as in a body on its back: the inlet faces up
        sk.root.rotation_euler = (math.radians(-90), 0, math.radians(yaw - 90))
        bpy.context.view_layer.update()
    else:
        sk.root.rotation_euler = (0, math.radians(90), math.radians(yaw))
        bpy.context.view_layer.update()
        W = np.concatenate([np.array([o.matrix_world @ v.co for v in o.data.vertices]) for o in objs])
        c0 = W.mean(0); u, sv, vt = np.linalg.svd(W[::max(1, len(W) // 20000)] - c0, full_matrices=False)
        ax = Vector(vt[0].tolist()); ax = ax if ax.z >= 0 else -ax
        flat = Vector((ax.x, ax.y, 0)).normalized() if Vector((ax.x, ax.y, 0)).length > 1e-4 else Vector((1, 0, 0))
        R = ax.rotation_difference(flat).to_matrix().to_4x4()
        sk.root.matrix_world = Matrix.Translation(Vector(c0.tolist())) @ R @ Matrix.Translation(-Vector(c0.tolist())) @ sk.root.matrix_world
        bpy.context.view_layer.update()
    W = np.concatenate([np.array([o.matrix_world @ v.co for v in o.data.vertices]) for o in objs])
    sk.root.location += Vector((x - W[:, 0].mean(), y - W[:, 1].mean(), LB.TOP + 0.004 - W[:, 2].min()))
    bpy.context.view_layer.update()
    for o in objs:
        p2._bone_detail(o)
    W = np.concatenate([np.array([o.matrix_world @ v.co for v in o.data.vertices]) for o in objs])
    return sk, W


def knee_pieces(sk, side="L", keep_femur=0.09, keep_tibia=0.07, keep="near"):
    """Cut the knee out of a skeleton: the distal end of the femur (condyles), the patella and the tibial plateau,
    as separate broken pieces (dry, straight-ish breaks). Returns the three objects; the rest of those bones is deleted."""
    bpy.context.view_layer.update()
    kj = sk.world_pivot("shank" + side)                          # knee joint
    out = []
    for seg, keep in (("femur" + side, keep_femur), ("shank" + side, keep_tibia)):
        o = sk.parts[seg]
        Mi = o.matrix_world.inverted()
        bm = bmesh.new(); bm.from_mesh(o.data)
        co = np.array([o.matrix_world @ v.co for v in bm.verts])
        d = np.linalg.norm(co - np.array(kj), axis=1)
        far = co[np.argmax(d)]
        axis = (Vector(far.tolist()) - kj).normalized()            # along the bone away from the knee
        cut_w = kj + axis * keep
        rng = random.Random(len(seg))
        nrm_w = (axis + Vector((rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25), rng.uniform(-0.2, 0.2)))).normalized()
        res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Mi @ cut_w,
                                     plane_no=(Mi.to_3x3() @ nrm_w).normalized(), clear_outer=(keep == "near"), clear_inner=(keep != "near"))
        bmesh.ops.contextual_create(bm, geom=[e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)])
        bm.to_mesh(o.data); bm.free(); o.data.update()
        out.append(o)
    if keep == "near":
        out.append(sk.parts["patella" + side])
    else:
        sk.remove("patella" + side)
    return out


def _tube(x, y, z, cap=(0.05, 0.25, 0.55)):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0075, depth=0.07, location=(x, y, z + 0.035)); t = bpy.context.active_object
    t.data.materials.append(_glass("tubeglass")); t.name = "tube"
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0085, depth=0.012, location=(x, y, z + 0.076)); c = bpy.context.active_object
    c.data.materials.append(_plain("tubecap", cap, 0.4)); c.name = "tubecap"
    bpy.ops.mesh.primitive_cylinder_add(radius=0.006, depth=0.012, location=(x, y, z + 0.007)); p = bpy.context.active_object
    p.data.materials.append(_plain("powder", (0.75, 0.68, 0.56), 0.95)); p.name = "tubepowder"
    return t


def _drillhole(W, frac=0.5, r=0.0045):
    xm = np.percentile(W[:, 0], frac * 100); mid = W[np.abs(W[:, 0] - xm) < 0.01]
    hole = Vector((float(xm), float(mid[:, 1].mean()), float(mid[:, 2].max())))
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=0.006, location=hole + Vector((0, 0, -0.0034)))
    h = bpy.context.active_object; h.name = "drillhole"; h.data.materials.append(_plain("hole", (0.03, 0.02, 0.012), 0.9))
    return hole


def _sample_shot(seg, sex="M", yaw=10, cap=(0.05, 0.25, 0.55), frac=0.5, lens=60):
    A = LB.room(window_light=0.3, lamp=True, lamp_at=(0.3, 0.62), lamp_target=(0.05, 0.34), lamp_energy=22)
    LB.velvet(-0.6, 0.7, 0.0, 0.78, LB.TOP)
    sk, W = lab_part(seg, sex=sex, yaw=yaw)
    hole = _drillhole(W, frac)
    for k in range(3):
        _tube(hole.x + 0.12 + k * 0.022, hole.y + 0.2, LB.TOP, cap=cap)
    return hole


# ============================================================================ "And at some point, preserved parts..."
def S01():
    """Bronze Age, inside the roundhouse by firelight: three wrapped bundles on hurdles laid side by side in the gloom,
    the fire low. Slow push between them."""
    U.CUT = False
    R = BR.interior(fire=0.7, door_sun=0.0)
    hx, hy = R["hearth"]
    for k, (dx, rot) in enumerate(((-1.6, 80), (-0.7, 95), (0.3, 70))):
        P2.hurdle((hx + dx, hy + 1.7, 0.03), rot=math.radians(rot), length=1.6, width=0.7, seed=k)
        P2.bundle((hx + dx, hy + 1.7, 0.22), rot=math.radians(rot), length=0.85 + 0.1 * k, girth=0.4, seed=k)
    return dict(a=((hx - 2.3, hy - 0.6, 0.9), (hx - 0.6, hy + 1.7, 0.2)), b=((hx - 1.8, hy - 0.2, 0.8), (hx - 0.6, hy + 1.7, 0.2)), lens=32,
                fstop=2.8, focus=(hx - 0.7, hy + 1.7, 0.25), cine=dict(exposure=0.25), hand_ok=("floor",))


def S02():
    """The second grave from above at last light: the tightly curled body. Slow descent."""
    T, sk = p1.site("dusk", grass_at=None, kit=False, sun_az=200)
    c, _ = sk["B2"].centre()
    return dict(a=((c.x + 0.15, c.y - 0.2, c.z + 3.6), tuple(c)), b=((c.x + 0.1, c.y - 0.12, c.z + 2.4), tuple(c)), lens=35,
                fstop=5.6, focus=tuple(c), cine=dict(exposure=0.35))


# ============================================================================ "The second adult now demands a closer look."
def S03():
    """Push in low over the second skeleton toward its skull, side light."""
    T, sk = p1.site("overcast", grass_at=None, kit=False)
    s = sk["B2"].part_centre("skull"); t = sk["B2"].part_centre("thorax")
    return dict(a=(tuple(t + Vector((0.9, -0.9, 0.9))), tuple((s + t) / 2)), b=(tuple(t + Vector((0.45, -0.5, 0.55))), tuple(s)), lens=45,
                fstop=3.5, focus=tuple(s))


# ============================================================================ "Its pelvis is identified as female..."
def S04():
    """Lab: a female pelvis on the velvet, the wide pelvic inlet and sciatic notch in the lamp light. Slow orbit."""
    A = LB.room(window_light=0.3, lamp=True, lamp_at=(0.25, 0.62), lamp_target=(0.0, 0.38), lamp_energy=24)
    LB.velvet(-0.6, 0.7, 0.0, 0.78, LB.TOP)
    sk, W = lab_part("pelvis", sex="F", tone="C")
    t = Vector(((W.min(0) + W.max(0)) / 2).tolist())
    return dict(a=(tuple(t + Vector((-0.25, -0.3, 0.42))), tuple(t)), b=(tuple(t + Vector((0.08, -0.36, 0.42))), tuple(t)), lens=50,
                fstop=4.0, focus=tuple(t), cine=dict(exposure=-0.05))


def S05():
    """The head: a male cranium, heavier brow ridges and mastoids, darker and more stained than the pelvis. Slow slide."""
    A = LB.room(window_light=0.3, lamp=True, lamp_at=(0.4, 0.62), lamp_target=(0.0, 0.36), lamp_energy=22)
    LB.velvet(-0.6, 0.7, 0.0, 0.78, LB.TOP)
    cr = B.hero_cranium(healed=False, tone="D")
    co = np.array([v.co for v in cr.data.vertices]); cr.location = (0.0, 0.36, LB.TOP + 0.004 - co[:, 2].min() * 0.97)
    cr.rotation_euler = (0, 0, math.radians(-60))
    p1._cork_ring(0.0, 0.36, LB.TOP)
    c = Vector((0.0, 0.36, LB.TOP + 0.08))
    return dict(a=((0.4, -0.08, LB.TOP + 0.16), tuple(c)), b=((0.32, -0.2, LB.TOP + 0.18), tuple(c)), lens=60,
                fstop=4.0, focus=tuple(c), cine=dict(exposure=-0.1))


def S06():
    """Head and pelvis side by side on the bench: the skull darker, older. Pull back between them."""
    A = LB.room(window_light=0.3, lamp=True, lamp_at=(0.0, 0.62), lamp_target=(0.0, 0.36), lamp_energy=26)
    LB.velvet(-0.8, 0.8, 0.0, 0.78, LB.TOP)
    lab_part("pelvis", sex="F", tone="C", x=0.22, y=0.4)
    cr = B.hero_cranium(healed=False, tone="D")
    co = np.array([v.co for v in cr.data.vertices]); cr.location = (-0.22, 0.4, LB.TOP + 0.004 - co[:, 2].min() * 0.97)
    cr.rotation_euler = (0, 0, math.radians(-30))
    c = Vector((0.0, 0.4, LB.TOP + 0.06))
    return dict(a=((0.0, -0.05, LB.TOP + 0.14), tuple(c)), b=((0.0, -0.4, LB.TOP + 0.26), tuple(c)), lens=40,
                fstop=4.0, focus=tuple(c), cine=dict(exposure=-0.05))


# ============================================================================ "Researchers take samples from four places."
def S07():
    """The skull: a small sampling hole drilled at its base, the dust collected, capped tubes beside it."""
    A = LB.room(window_light=0.3, lamp=True, lamp_at=(0.35, 0.62), lamp_target=(0.0, 0.36), lamp_energy=22)
    LB.velvet(-0.6, 0.7, 0.0, 0.78, LB.TOP)
    cr = B.hero_cranium(healed=False, tone="D")
    co = np.array([v.co for v in cr.data.vertices]); cr.location = (0.0, 0.36, LB.TOP + 0.004 - co[:, 2].min() * 0.97)
    cr.rotation_euler = (0, 0, math.radians(-120))
    for k in range(3):
        _tube(0.14 + k * 0.022, 0.5, LB.TOP, cap=(0.55, 0.1, 0.05))
    c = Vector((0.03, 0.4, LB.TOP + 0.06))
    return dict(a=((0.3, 0.0, LB.TOP + 0.14), tuple(c)), b=((0.22, -0.06, LB.TOP + 0.12), tuple(c)), lens=60,
                fstop=4.0, focus=tuple(c), cine=dict(exposure=-0.1))


def S08():
    """The lower jaw: the sample taken from the root of a molar, a tube beside it."""
    A = LB.room(window_light=0.3, lamp=True, lamp_at=(0.4, 0.62), lamp_target=(0.0, 0.32), lamp_energy=20)
    LB.velvet(-0.6, 0.6, 0.0, 0.75, LB.TOP)
    md = B.hero_mandible(tone="B")
    co = np.array([v.co for v in md.data.vertices]); md.location = (0.0, 0.32, LB.TOP + 0.003 - co[:, 2].min()); md.rotation_euler = (0, 0, math.radians(35))
    for k in range(2):
        _tube(0.12 + k * 0.022, 0.46, LB.TOP, cap=(0.1, 0.4, 0.15))
    bpy.context.view_layer.update()
    Wm = np.array([md.matrix_world @ v.co for v in md.data.vertices]); t = Vector(((Wm.min(0) + Wm.max(0)) / 2).tolist())
    return dict(a=(tuple(t + Vector((-0.2, -0.24, 0.18))), tuple(t)), b=(tuple(t + Vector((0.0, -0.3, 0.18))), tuple(t)), lens=60,
                fstop=4.0, focus=tuple(t), cine=dict(exposure=-0.1))


def S09():
    """The upper arm: a drill hole in the shaft of the humerus, sample tubes. Slider."""
    hole = _sample_shot("upperarmR", sex="M", cap=(0.6, 0.45, 0.05), frac=0.5)
    return dict(a=(tuple(hole + Vector((-0.2, -0.22, 0.13))), tuple(hole + Vector((0.03, 0.06, 0)))), b=(tuple(hole + Vector((-0.08, -0.25, 0.12))), tuple(hole + Vector((0.05, 0.08, 0)))),
                lens=50, fstop=4.0, focus=tuple(hole), cine=dict(exposure=-0.1))


def S10():
    """The thigh bone: a drill hole in the femur, sample tubes. Slider."""
    hole = _sample_shot("femurR", sex="M", cap=(0.05, 0.25, 0.55), frac=0.55)
    return dict(a=(tuple(hole + Vector((0.2, -0.22, 0.13))), tuple(hole + Vector((-0.03, 0.06, 0)))), b=(tuple(hole + Vector((0.08, -0.25, 0.12))), tuple(hole + Vector((-0.05, 0.08, 0)))),
                lens=50, fstop=4.0, focus=tuple(hole), cine=dict(exposure=-0.1))


# ============================================================================ "Ancient DNA is damaged and difficult to recover..."
def clean_room(uv=1.0):
    """Ancient-DNA clean room: white walls, a laminar-flow cabinet with a glass sash and violet UV tubes, racks of capped
    tubes, a pipette on its stand; cold overhead light."""
    white = _plain("cleanwall", (0.3, 0.33, 0.37), 0.6)
    for loc, sc in (((0, 2.0, 1.5), (8, 0.1, 3)), ((-3.5, 0, 1.5), (0.1, 6, 3)), ((3.5, 0, 1.5), (0.1, 6, 3)), ((0, 0, 3.0), (8, 6, 0.1))):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.active_object; o.scale = sc; o.data.materials.append(white)
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0)); f = bpy.context.active_object; f.data.materials.append(_plain("cleanfloor", (0.18, 0.2, 0.22), 0.3))
    steel = p2._plain("cabsteel", (0.7, 0.7, 0.72), 0.3, 1.0) if hasattr(p2, "_plain") else _plain("cabsteel", (0.7, 0.7, 0.72), 0.3, 1.0)
    # cabinet body
    for loc, sc in (((0, 1.55, 0.45), (1.6, 0.8, 0.9)), ((0, 1.55, 1.75), (1.6, 0.8, 0.5)), ((-0.79, 1.55, 1.25), (0.04, 0.8, 0.6)), ((0.79, 1.55, 1.25), (0.04, 0.8, 0.6)),
                    ((0, 1.93, 1.25), (1.6, 0.04, 0.6))):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.active_object; o.scale = sc; o.data.materials.append(steel); o.name = "cabinet"
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 1.16, 1.32)); sash = bpy.context.active_object; sash.scale = (1.56, 0.008, 0.46)
    sash.rotation_euler.x = math.radians(-8); sash.data.materials.append(_glass("sash")); sash.name = "sash"
    # UV tubes inside the cabinet top: violet glow
    for xx in (-0.4, 0.4):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.6, location=(xx, 1.6, 1.48)); tb = bpy.context.active_object
        tb.rotation_euler.y = math.pi / 2; tb.name = "uvtube"
        tb.data.materials.append(P2._mat("uvglow", (0, 0, 0), 0.4, emit=(0.45, 0.2, 1.0), strength=60 * uv))
    d = bpy.data.lights.new("uv", 'AREA'); d.size = 1.3; d.size_y = 0.5; d.shape = 'RECTANGLE'; d.energy = 90 * uv; d.color = (0.5, 0.3, 1.0)
    lo = bpy.data.objects.new("uv", d); bpy.context.scene.collection.objects.link(lo); lo.location = (0, 1.6, 1.45)
    # work surface items: tube racks, a pipette on its stand, a bone-powder tube
    rack = _plain("rack", (0.85, 0.85, 0.82), 0.4)
    for rx in (-0.35, 0.25):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(rx, 1.6, 0.92)); r_ = bpy.context.active_object; r_.scale = (0.2, 0.08, 0.04); r_.data.materials.append(rack)
        for k in range(6):
            _tube(rx - 0.075 + k * 0.03, 1.6, 0.94, cap=(0.9, 0.9, 0.88) if k % 2 else (0.1, 0.35, 0.65))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.22, location=(0.0, 1.7, 1.05)); pp = bpy.context.active_object
    pp.rotation_euler.x = math.radians(12); pp.data.materials.append(_plain("pipette", (0.85, 0.85, 0.85), 0.4)); pp.name = "pipette"
    for xx in (-1.5, 1.5):
        dd = bpy.data.lights.new("ceil", 'AREA'); dd.size = 1.2; dd.energy = 35; dd.color = (0.8, 0.88, 1.0)
        oo = bpy.data.objects.new("ceil", dd); bpy.context.scene.collection.objects.link(oo); oo.location = (xx, 0.2, 2.9)
    # side benches with instruments in the gloom: centrifuge, thermal cycler, a fridge with a glowing panel, shelving
    dark = _plain("instr", (0.12, 0.13, 0.14), 0.4); pale = _plain("instrpale", (0.55, 0.57, 0.6), 0.35)
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(sx * 2.6, 0.6, 0.45)); bb = bpy.context.active_object; bb.scale = (1.4, 2.6, 0.9); bb.data.materials.append(dark)
        for k, (yy, sz, mt) in enumerate(((-0.3, (0.45, 0.45, 0.32), pale), (0.4, (0.5, 0.38, 0.25), dark), (1.2, (0.35, 0.3, 0.22), pale))):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(sx * 2.6, yy, 0.9 + sz[2] / 2)); ib = bpy.context.active_object; ib.scale = sz
            ib.data.materials.append(mt); bv = ib.modifiers.new("b", "BEVEL"); bv.width = 0.02; bv.segments = 2
            bpy.ops.mesh.primitive_cube_add(size=1, location=(sx * (2.6 - sz[0] / 2 - 0.002), yy, 0.95 + sz[2] * 0.6)); led = bpy.context.active_object
            led.scale = (0.004, 0.04, 0.012); led.data.materials.append(P2._mat(f"lcd{k}", (0, 0, 0), 0.3, emit=(0.3, 0.8, 1.0) if k != 1 else (0.3, 1.0, 0.4), strength=8))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-2.9, -1.6, 0.95)); fr = bpy.context.active_object; fr.scale = (0.75, 0.75, 1.9); fr.data.materials.append(pale)
    w = bpy.data.worlds.new("clean"); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs['Color'].default_value = (0.02, 0.02, 0.025, 1)


def S11():
    """The ancient-DNA clean room: a scientist in a full white suit and hood works at the UV cabinet, seen from behind;
    the violet light through the sash. Slow push."""
    clean_room()
    import acts as AC
    m = K.Osteologist(name="Cleansuit")
    st = AC.Stand(m, (0.0, 0.62), 90, lean=10)
    st.hand("L", (-0.18, 1.32, 0.98), elbow=(0.6, 0.2, -0.8), curl=20)
    st.hand("R", (0.15, 1.32, 1.0), elbow=(0.6, 0.2, -0.8), curl=20)
    st.head_to((0, 1.6, 0.95), share=0.8)
    st.finish(look=(0, 1.6, 0.95), density=HAIR)
    return dict(a=((1.3, -2.2, 1.7), (-0.1, 1.3, 1.05)), b=((1.0, -1.6, 1.65), (-0.1, 1.3, 1.05)), lens=30,
                fstop=2.8, focus=(0.0, 0.7, 1.3), cine=dict(exposure=0.1), hand_ok=("sash", "cabinet"))


def S12():
    """Inside the cabinet under UV: capped tubes of bone powder in a rack, the pipette, violet glow. Macro slide."""
    clean_room(uv=1.3)
    return dict(a=((-0.45, 1.22, 1.08), (-0.3, 1.62, 0.95)), b=((-0.1, 1.22, 1.08), (0.05, 1.62, 0.95)), lens=50,
                fstop=2.8, focus=(-0.25, 1.6, 0.97), cine=dict(exposure=0.0))


def S13():
    """A sample tube in the cabinet with the bone powder at its tip, sharp; the rack soft behind. Push."""
    clean_room(uv=1.2)
    t = Vector((0.25 - 0.075 + 2 * 0.03, 1.6, 0.97))
    return dict(a=(tuple(t + Vector((-0.12, -0.26, 0.08))), tuple(t)), b=(tuple(t + Vector((-0.06, -0.15, 0.05))), tuple(t)), lens=70,
                fstop=2.0, focus=tuple(t), cine=dict(exposure=0.1))


# ============================================================================ "The results are published in 2012."
def S14():
    """Sequencing lab at night: the instrument's status lights and flow-cell glow in the dark, a window of black glass.
    Slow track (no screens, no text)."""
    P2.ams_hall(length=6.0)
    _haze((1, 0, 3), (16, 12, 6), density=0.01, color=(0.8, 0.88, 1.0))
    return dict(a=((5.0, -2.8, 1.6), (-1.0, 0.0, 1.3)), b=((4.2, -2.5, 1.5), (-1.0, 0.0, 1.35)), lens=35, fstop=2.8, focus=(-0.6, 0, 1.35),
                cine=dict(exposure=0.0))


# ============================================================================ "The jaw, upper arm, and thigh come from different individuals."
def S15():
    """Jaw, upper arm and thigh bone far apart on the bench, three pools of light. Lateral dolly."""
    A = LB.room(window_light=0.05, lamp=False)
    if A.get("microscope") is not None:
        for o in [A["microscope"]] + list(A["microscope"].children_recursive):
            bpy.data.objects.remove(o)
    LB.velvet(-2.0, 2.0, 0.0, 0.78, LB.TOP)
    md = B.hero_mandible(tone="B")
    co = np.array([v.co for v in md.data.vertices]); md.location = (-1.1, 0.4, LB.TOP + 0.003 - co[:, 2].min()); md.rotation_euler = (0, 0, math.radians(-20))
    lab_part("upperarmR", sex="M", tone="A", x=0.0, y=0.4, yaw=70)
    lab_part("femurR", sex="M", tone="D", x=1.2, y=0.4, yaw=75)
    for x in (-1.1, 0.0, 1.2):
        _spot((x - 0.1, 0.3, LB.TOP + 1.4), (x, 0.4, LB.TOP), 420, size=0.1, spot=24)
    f = bpy.data.lights.new("fill", 'AREA'); f.size = 4.5; f.size_y = 1.2; f.shape = 'RECTANGLE'; f.energy = 120; f.color = (0.75, 0.8, 0.9)
    fo = bpy.data.objects.new("fill", f); bpy.context.scene.collection.objects.link(fo); fo.location = (0.0, -0.4, LB.TOP + 1.6)
    return dict(a=((-1.6, -0.9, LB.TOP + 0.5), (-0.6, 0.4, LB.TOP)), b=((0.4, -0.95, LB.TOP + 0.5), (0.9, 0.4, LB.TOP)), lens=35,
                fstop=5.6, focus=(0.0, 0.4, LB.TOP), cine=dict(exposure=0.0))


def S16():
    """The skull alone, the lamp low: it gives no answer. Slow push in the dark."""
    A = LB.room(window_light=0.05, lamp=True, lamp_at=(0.5, 0.62), lamp_target=(0.0, 0.36), lamp_energy=8)
    LB.velvet(-0.6, 0.7, 0.0, 0.78, LB.TOP)
    cr = B.hero_cranium(healed=False, tone="D")
    co = np.array([v.co for v in cr.data.vertices]); cr.location = (0.0, 0.36, LB.TOP + 0.004 - co[:, 2].min() * 0.97)
    cr.rotation_euler = (0, 0, math.radians(-150))
    p1._cork_ring(0.0, 0.36, LB.TOP)
    c = Vector((0.0, 0.36, LB.TOP + 0.08))
    return dict(a=((-0.55, -0.2, LB.TOP + 0.2), tuple(c)), b=((-0.36, -0.1, LB.TOP + 0.15), tuple(c)), lens=50,
                fstop=2.8, focus=tuple(c), cine=dict(exposure=-0.2))


# ============================================================================ "...this second body also contains remains from at least three people."
def S17():
    """The second skeleton in its grave: a slow track along it from the feet to the head."""
    T, sk = p1.site("overcast", grass_at=None, kit=False)
    s = sk["B2"].part_centre("skull"); c, _ = sk["B2"].centre(); f = c.lerp(s, -0.6)
    return dict(a=(tuple(f + Vector((0.6, -0.7, 0.7))), tuple(f)), b=(tuple(s + Vector((0.6, -0.7, 0.7))), tuple(s)), lens=40,
                fstop=4.0, focus=tuple(c))


def S18():
    """Under one house, two assembled bodies: crane up from the graves until the whole house floor is in frame, dusk."""
    T, sk = p1.site("dusk", grass_at=None, kit=True, sun_az=210)
    p1_ = U.PITS["B1"]; p2_ = U.PITS["B2"]; z = G.H(p1_[0], p1_[1])
    m = Vector(((p1_[0] + p2_[0]) / 2, (p1_[1] + p2_[1]) / 2, z - 0.3))
    return dict(a=(tuple(m + Vector((2.0, -2.5, 1.6))), tuple(m)), b=(tuple(m + Vector((4.0, -6.0, 7.0))), tuple(m)), lens=32,
                fstop=8.0, focus=tuple(m), cine=dict(exposure=0.35))


def S19():
    """Six lives: the Bronze Age roundhouses at dusk, smoke in the still air. Slow lateral drift."""
    U.CUT = False
    U.island("dusk", grass_at=(0, 0), grass_r=40, n=820, core=4.0, grass_density=220)
    BR.village(smoke_on=True)
    return dict(a=((30, -24, 7), (0, 0, 4)), b=((34, -16, 7), (0, 1, 4)), lens=35, cine=dict(exposure=0.35))


# ============================================================================ "The second skeleton is missing part of its left knee."
def S20():
    """Macro in the second grave: the legs, one lying across the other, and the gap where the left knee should be."""
    T, sk = p1.site("overcast", grass_at=None, kit=False)
    c, _ = sk["B2"].centre(); s = sk["B2"].part_centre("skull"); k = c.lerp(s, -0.35)
    return dict(a=(tuple(k + Vector((0.45, -0.5, 0.5))), tuple(k)), b=(tuple(k + Vector((0.25, -0.35, 0.35))), tuple(k)), lens=60,
                fstop=4.0, focus=tuple(k))


def S21():
    """The same legs from the other side, lower: the right leg laid over the incomplete left. Slider."""
    T, sk = p1.site("overcast", grass_at=None, kit=False)
    c, _ = sk["B2"].centre(); s = sk["B2"].part_centre("skull"); k = c.lerp(s, -0.35)
    return dict(a=(tuple(k + Vector((-0.5, -0.35, 0.4))), tuple(k)), b=(tuple(k + Vector((-0.3, -0.5, 0.4))), tuple(k)), lens=60,
                fstop=4.0, focus=tuple(k))


def S22():
    """The order of events: a slow rack across the crossed legs, the upper leg sharp, then the break beneath it."""
    T, sk = p1.site("day", grass_at=None, kit=False, sun_az=215)
    c, _ = sk["B2"].centre(); s = sk["B2"].part_centre("skull"); k = c.lerp(s, -0.35)
    return dict(a=(tuple(k + Vector((0.3, -0.55, 0.55))), tuple(k + Vector((0, 0, 0.03)))), b=(tuple(k + Vector((0.2, -0.45, 0.45))), tuple(k)), lens=70,
                fstop=2.8, focus=tuple(k), cine=dict(exposure=0.1))


# ============================================================================ "Outside the house, in a separate pit..."
def _lying_knee(name="Knee"):
    """A skeleton laid on its back (as in the lab), knee cut out; returns (skeleton, pieces)."""
    skk = B.Skeleton("M", "C", name=name, sand=0.6)
    skk.root.rotation_euler = (math.radians(-90), 0, math.radians(-90))
    bpy.context.view_layer.update()
    pcs = knee_pieces(skk)
    return skk, pcs


def _knee_pit(kneel=True):
    T, sk = p1.site("day", grass_at=(6, 18), grass_r=6, kit=False, burials=True, sun_az=210)
    kx, ky = U.PITS["KNEE"][0], U.PITS["KNEE"][1]
    zf = float(U.surface(kx, ky))
    skk, pcs = _lying_knee()
    for s_ in list(skk.parts):
        if skk.parts[s_] not in pcs:
            skk.remove(s_)
    bpy.context.view_layer.update()
    W = np.concatenate([np.array([o.matrix_world @ v.co for v in o.data.vertices]) for o in pcs])
    c = W.mean(0)
    skk.root.location += Vector((kx - c[0], ky - c[1], zf - 0.015 - W[:, 2].min()))      # bedded a little into the sand
    bpy.context.view_layer.update()
    for o in pcs:
        p2._bone_detail(o)
    out = dict(knee=Vector((kx, ky, zf + 0.03)), pieces=pcs)
    if kneel:
        out["st"] = K.kneel_trowel(K.DiggerB, (kx + 0.15, ky - 0.75), 95, work=(kx + 0.05, ky - 0.25), density=HAIR)
    return out


def S23():
    """Outside the house: a digger (from behind) kneels at a small separate pit, trowelling; the house rings beyond."""
    o = _knee_pit()
    k = o["knee"]
    return dict(a=(tuple(k + Vector((1.6, -2.6, 1.6))), tuple(k + Vector((-0.3, 0.6, -0.1)))), b=(tuple(k + Vector((1.3, -2.2, 1.4))), tuple(k)), lens=35,
                fstop=4.0, focus=tuple(k), hand_ok=p1.OK)


def S24():
    """In the pit: the pieces of a human knee - the end of a thigh bone, the kneecap, the top of a shin - in the sand."""
    o = _knee_pit(kneel=False)
    k = o["knee"]
    return dict(a=(tuple(k + Vector((0.3, -0.35, 0.4))), tuple(k)), b=(tuple(k + Vector((0.1, -0.4, 0.32))), tuple(k)), lens=60,
                fstop=4.0, focus=tuple(k), cine=dict(exposure=0.1))


# ============================================================================ "The broken surfaces match."
def S25():
    """Lab: the broken knee pieces from the pit laid against the broken ends of the leg bones - the break lines meet,
    a hairline apart. Slow push along the join under a raking lamp."""
    A = LB.room(window_light=0.2, lamp=True, lamp_at=(0.35, 0.62), lamp_target=(0.0, 0.38), lamp_energy=18)
    LB.velvet(-0.8, 0.8, 0.0, 0.78, LB.TOP)
    legs = []
    for nm, keep in (("Shafts", "far"), ("Pieces", "near")):
        sk = B.Skeleton("M", "C", name=nm)
        for s_ in list(sk.parts):
            if s_ not in ("femurL", "patellaL", "shankL"):
                sk.remove(s_)
        sk.root.rotation_euler = (math.radians(-90), 0, math.radians(-90))
        bpy.context.view_layer.update()
        knee_pieces(sk, keep=keep)
        legs.append(sk)
    objs = [o for sk in legs for o in sk.parts.values()]
    W = np.concatenate([np.array([o.matrix_world @ v.co for v in o.data.vertices]) for o in objs])
    off = Vector((-W[:, 0].mean(), 0.4 - W[:, 1].mean(), LB.TOP + 0.004 - W[:, 2].min()))
    for sk in legs:
        sk.root.location += off
    legs[1].root.location += Vector((0.0, -0.006, 0.004))      # the pit pieces a hairline off the breaks
    bpy.context.view_layer.update()
    for o in objs:
        p2._bone_detail(o)
    _spot((-0.6, 0.15, LB.TOP + 0.25), (0.0, 0.4, LB.TOP + 0.03), 60, size=0.04, spot=30)
    k = legs[0].world_pivot("shankL")
    return dict(a=(tuple(k + Vector((-0.12, -0.42, 0.3))), tuple(k)), b=(tuple(k + Vector((0.04, -0.4, 0.26))), tuple(k)), lens=55,
                fstop=5.6, focus=tuple(k), cine=dict(exposure=-0.05))


def S26():
    """About five metres: high over the trench, from the second grave across the house wall to the knee pit. Crane."""
    T, sk = p1.site("golden", grass_at=None, kit=True, sun_az=200)
    b2 = Vector((U.PITS["B2"][0], U.PITS["B2"][1], G.H(U.PITS["B2"][0], U.PITS["B2"][1])))
    kp = Vector((U.PITS["KNEE"][0], U.PITS["KNEE"][1], G.H(U.PITS["KNEE"][0], U.PITS["KNEE"][1])))
    m = (b2 + kp) / 2
    return dict(a=(tuple(m + Vector((3.0, -3.0, 4.0))), tuple(b2)), b=(tuple(m + Vector((3.5, -2.5, 6.0))), tuple(kp)), lens=30,
                fstop=8.0, focus=tuple(m), cine=dict(exposure=0.1))


# ============================================================================ "The fractures tell the team something else."
def S27():
    """Macro on a dry break: the flat, chalky fracture face of the femur end in grazing light."""
    A = LB.room(window_light=0.15, lamp=False)
    LB.velvet(-0.6, 0.7, 0.0, 0.78, LB.TOP)
    skk, pcs = _lying_knee()
    for s_ in list(skk.parts):
        if skk.parts[s_] not in pcs:
            skk.remove(s_)
    fem = pcs[0]
    for s_ in list(skk.parts):
        if skk.parts[s_] is not fem:
            skk.remove(s_)
    bpy.context.view_layer.update()
    W = np.array([fem.matrix_world @ v.co for v in fem.data.vertices]); c = W.mean(0)
    skk.root.location += Vector((-c[0], 0.38 - c[1], LB.TOP + 0.004 - W[:, 2].min()))
    bpy.context.view_layer.update()
    p2._bone_detail(fem)
    W = np.array([fem.matrix_world @ v.co for v in fem.data.vertices]); t = Vector(((W.min(0) + W.max(0)) / 2).tolist())
    _spot((t.x - 0.6, t.y + 0.2, t.z + 0.1), tuple(t), 60, size=0.02, spot=22)
    return dict(a=(tuple(t + Vector((0.18, -0.16, 0.1))), tuple(t)), b=(tuple(t + Vector((0.1, -0.2, 0.09))), tuple(t)), lens=85,
                fstop=8.0, focus=tuple(t), cine=dict(exposure=0.05))


def S28():
    """Brittle bone: the shaft of the femur in hard raking light, fine cracking and flaking. Slider."""
    A = LB.room(window_light=0.15, lamp=False)
    LB.velvet(-0.6, 0.7, 0.0, 0.78, LB.TOP)
    fe, W = p1.lab_femur(); p2._bone_detail(fe); p2._etch(fe, strength=0.6)
    xm = float(W[:, 0].mean()); mid = W[np.abs(W[:, 0] - xm) < 0.015]
    t = Vector((xm, float(mid[:, 1].mean()), float(mid[:, 2].max()) - 0.003))
    _spot((t.x + 0.5, t.y + 0.35, t.z + 0.06), tuple(t), 90, size=0.02, spot=20)
    return dict(a=(tuple(t + Vector((0.06, -0.13, 0.09))), tuple(t)), b=(tuple(t + Vector((-0.02, -0.13, 0.09))), tuple(t + Vector((-0.02, 0, 0)))),
                lens=90, fstop=11.0, focus=tuple(t), cine=dict(exposure=0.05))


# ============================================================================ "But parts of the broken joint are still together."
def S29():
    """In the knee pit: the kneecap still in place against the femur end, the joint held together. Close, low."""
    o = _knee_pit(kneel=False)
    k = o["knee"]
    return dict(a=(tuple(k + Vector((-0.28, -0.22, 0.16))), tuple(k)), b=(tuple(k + Vector((-0.18, -0.28, 0.14))), tuple(k)), lens=70,
                fstop=4.0, focus=tuple(k), cine=dict(exposure=0.1))


def S30():
    """An old body that kept its tissue: a dried, wrapped bundle on a hurdle in the dim roundhouse, firelight. Push."""
    U.CUT = False
    R = BR.interior(fire=0.6, door_sun=0.0)
    hx, hy = R["hearth"]
    P2.hurdle((hx - 0.8, hy + 1.6, 0.03), rot=math.radians(80), length=1.8, width=0.75)
    P2.bundle((hx - 0.8, hy + 1.6, 0.23), rot=math.radians(80), length=0.95, girth=0.42)
    t = Vector((hx - 0.8, hy + 1.6, 0.25))
    return dict(a=(tuple(t + Vector((-1.3, -1.4, 0.6))), tuple(t)), b=(tuple(t + Vector((-0.8, -0.9, 0.45))), tuple(t)), lens=40,
                fstop=2.8, focus=tuple(t), cine=dict(exposure=0.25), hand_ok=("floor",))


# ============================================================================ "In the team's later reconstruction..."
def _night_pit():
    """Bronze Age night on the machair: the earlier grave dug open, torchlight from a pole torch; returns the pit centre."""
    U.CUT = False
    T = U.island("dusk", grass_at=(3, 14), grass_r=14, n=820, core=4.0, grass_density=220)
    BR.village(smoke_on=False)
    kx, ky = 19.0, 3.0                                    # open machair east of the houses
    z = float(U.surface(kx, ky))
    # night: the sky down to a deep blue glow, a weak cold moon instead of the sun
    w = bpy.context.scene.world
    for n in w.node_tree.nodes:
        if n.type == 'BACKGROUND':
            n.inputs['Strength'].default_value *= 0.06
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.data.type == 'SUN':
            o.data.energy = 0.08; o.data.color = (0.6, 0.7, 1.0)
    # a raised rim of upcast earth round the hole
    bpy.ops.mesh.primitive_torus_add(major_radius=0.62, minor_radius=0.12, location=(kx, ky, z + 0.02)); rim = bpy.context.active_object
    rim.scale = (1.45, 1.0, 0.6); rim.name = "pitrim"; rim.data.materials.append(G.mat("sand"))
    d_ = rim.modifiers.new("d", "DISPLACE"); t_ = bpy.data.textures.new("rimlump", "CLOUDS"); t_.noise_scale = 0.15; d_.texture = t_; d_.strength = 0.05
    # an open pit with a heap of sand beside it
    bpy.ops.mesh.primitive_cylinder_add(radius=0.55, depth=0.6, location=(kx, ky, z - 0.28)); pit = bpy.context.active_object
    pit.scale = (1.5, 1.0, 1.0); pit.data.materials.append(_plain("pitdark", (0.03, 0.025, 0.02), 0.95)); pit.name = "openpit"
    G.spoil_heap(kx + 0.2, ky + 1.6, 0.9, 0.6, 0.38)          # upcast on the far side, clear of where they stand
    # pole torch: a flame on a stake, a warm point light
    bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=1.6, location=(kx - 1.3, ky + 0.6, z + 0.8)); st = bpy.context.active_object
    st.data.materials.append(_plain("stake", (0.12, 0.08, 0.05), 0.8)); st.name = "torchstake"
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.09, location=(kx - 1.3, ky + 0.6, z + 1.68)); fl = bpy.context.active_object
    fl.scale = (0.8, 0.8, 1.6); fl.data.materials.append(P2._mat("flame", (0, 0, 0), 0.5, emit=(1.0, 0.45, 0.1), strength=40)); fl.name = "torchflame"
    d = bpy.data.lights.new("torch", 'POINT'); d.energy = 220; d.color = (1.0, 0.55, 0.2); d.shadow_soft_size = 0.12
    lo = bpy.data.objects.new("torch", d); bpy.context.scene.collection.objects.link(lo); lo.location = (kx - 1.3, ky + 0.6, z + 1.65)
    return Vector((kx, ky, z))


def S31():
    """Night: two islanders kneel at the opened grave, reaching down into it by torchlight (from behind). Slow push."""
    c = _night_pit()
    import acts as AC
    m1 = BR.Islander(name="Islander0")
    st1 = AC.Kneel(m1, (c.x - 0.25, c.y - 0.95), 90, lean=50, sit_back=True)
    for sd, dx in (("L", -0.3), ("R", 0.0)):
        st1.hand(sd, (c.x + dx, c.y - 0.25, -0.05), elbow=(0.6, 0.2, -0.8), curl=30)
    st1.head_to((c.x, c.y, -0.3), share=0.8); st1.finish(look=(c.x, c.y, -0.3), density=HAIR); G.lift(st1, c.z)
    m2 = p2._islander2()
    st2 = AC.Kneel(m2, (c.x + 0.75, c.y - 0.85), 105, lean=45, sit_back=True)
    for sd, dx in (("L", 0.25), ("R", 0.5)):
        st2.hand(sd, (c.x + dx, c.y - 0.25, -0.05), elbow=(0.6, 0.2, -0.8), curl=30)
    st2.head_to((c.x + 0.3, c.y, -0.3), share=0.8); st2.finish(look=(c.x + 0.3, c.y, -0.3), density=HAIR); G.lift(st2, c.z)
    return dict(a=((c.x + 0.6, c.y - 2.6, c.z + 2.6), (c.x + 0.2, c.y + 0.1, c.z)), b=((c.x + 0.5, c.y - 2.2, c.z + 2.4), (c.x + 0.2, c.y + 0.1, c.z)),
                lens=32, fstop=2.8, focus=(c.x + 0.2, c.y - 0.3, c.z + 0.3), cine=dict(exposure=0.6), hand_ok=("openpit", "Uist", "pitrim"))


def S32():
    """They lift the preserved body out on its hurdle, silhouetted against the torch. Low angle."""
    c = _night_pit()
    import acts as AC
    piv = bpy.data.objects.new("hurdle_rig", None); bpy.context.scene.collection.objects.link(piv); piv.location = (c.x, c.y - 0.2, c.z + 0.55)
    before = set(bpy.data.objects)
    P2.hurdle((c.x, c.y - 0.2, c.z + 0.55), rot=0.0, length=1.8, width=0.75)
    P2.bundle((c.x, c.y - 0.2, c.z + 0.75), rot=0.0, length=0.95, girth=0.42)
    bpy.context.view_layer.update()
    for o in set(bpy.data.objects) - before:
        o.parent = piv; o.matrix_parent_inverse = piv.matrix_world.inverted()
    for i, (dx, hd) in enumerate(((-1.25, 0), (1.25, 180))):
        m = BR.Islander(name=f"Islander{i}") if i == 0 else p2._islander2()
        f = (c.x + dx * 1.05, c.y - 0.2)
        zf = float(U.surface(*f))
        px = c.x + dx * 0.72
        palms = {"L": (px, c.y - 0.2 + (0.37 if hd == 0 else -0.37), c.z + 0.55 - zf + 0.03 - 0.035),
                 "R": (px, c.y - 0.2 - (0.37 if hd == 0 else -0.37), c.z + 0.55 - zf + 0.03 - 0.035)}
        st = AC.Lean(m, f, hd, palms, lean=35)
        st.finish(look=(c.x, c.y - 0.2, 0.6), density=HAIR); G.lift(st, zf)
    return dict(a=((c.x + 0.3, c.y - 4.0, c.z + 0.5), (c.x, c.y, c.z + 0.9)), b=((c.x + 0.25, c.y - 3.4, c.z + 0.55), (c.x, c.y, c.z + 0.9)),
                lens=32, fstop=2.8, focus=(c.x, c.y - 0.2, c.z + 0.8), cine=dict(exposure=0.4), hand_ok=("hurdle", "bundle"))


def S33():
    """The empty grave by torchlight: in the bottom, the broken knee left behind. Slow descent."""
    c = _night_pit()
    skk, pcs = _lying_knee()
    for s_ in list(skk.parts):
        if skk.parts[s_] not in pcs:
            skk.remove(s_)
    bpy.context.view_layer.update()
    W = np.concatenate([np.array([o.matrix_world @ v.co for v in o.data.vertices]) for o in pcs]); cc = W.mean(0)
    skk.root.location += Vector((c.x - cc[0], c.y - cc[1], c.z - 0.56 - W[:, 2].min()))
    bpy.context.view_layer.update()
    pit = bpy.data.objects.get("openpit")
    if pit:
        pit.data.materials.clear(); pit.data.materials.append(G.mat("sand"))
        for p_ in pit.data.polygons:
            pass
        bm = bmesh.new(); bm.from_mesh(pit.data)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.9], context='FACES')
        for f in bm.faces:
            f.normal_flip()
        bm.to_mesh(pit.data); bm.free()
    k = Vector((c.x, c.y, c.z - 0.5))
    return dict(a=(tuple(k + Vector((0.2, -0.7, 1.6))), tuple(k)), b=(tuple(k + Vector((0.1, -0.4, 1.0))), tuple(k)), lens=40,
                fstop=4.0, focus=tuple(k), cine=dict(exposure=0.45))


# ============================================================================ "The rest was moved beneath the house."
def S34():
    """First light: two islanders carry the hurdle with the body toward the roundhouse door (backs, walking). Track."""
    U.CUT = False
    U.island("dawn", grass_at=(6, -4), grass_r=24, n=820, core=4.0, grass_density=220)
    BR.village(smoke_on=True)
    import acts as AC
    hx, hy = 17.5, -9.5                     # out on the machair, walking toward the houses
    zc = float(U.surface(hx, hy))
    P2.hurdle((hx, hy, zc + 0.78), rot=math.radians(150), length=1.8, width=0.75)
    P2.bundle((hx, hy, zc + 0.98), rot=math.radians(150), length=0.95, girth=0.42)
    d = Vector((math.cos(math.radians(150)), math.sin(math.radians(150)), 0))
    s = Vector((-d.y, d.x, 0))
    for i, sg in enumerate((1, -1)):
        m = BR.Islander(name=f"Islander{i}") if i == 0 else p2._islander2()
        f = Vector((hx, hy, 0)) + d * (sg * 1.1)
        zf = float(U.surface(f.x, f.y))
        st = AC.Stand(m, (f.x, f.y), 150, lean=4)
        st.walk(0.25 if i == 0 else 0.75)
        for sd, sgn in (("L", 1), ("R", -1)):
            w = Vector((hx, hy, zc + 0.78)) + d * (sg * 0.72) + s * (sgn * 0.37)
            st.hand(sd, (w.x, w.y, w.z - zf), elbow=(0.6, 0.2, -0.8), grip=0.85)
        st.finish(look=(hx + d.x * 6, hy + d.y * 6, 1.6), density=HAIR); G.lift(st, zf)
    return dict(a=((hx + 6.5, hy - 1.6, zc + 1.7), (hx - 6, hy + 4, zc + 1.4)), b=((hx + 5.4, hy - 1.0, zc + 1.65), (hx - 7, hy + 4.5, zc + 1.4)),
                lens=32, fstop=4.0, focus=(hx, hy, zc + 1.0), cine=dict(exposure=0.3), hand_ok=("hurdle", "bundle"))


def S35():
    """And under the house: the second grave again at dusk, slow push to the crossed legs."""
    T, sk = p1.site("dusk", grass_at=None, kit=False, sun_az=210)
    c, _ = sk["B2"].centre(); s = sk["B2"].part_centre("skull"); k = c.lerp(s, -0.35)
    return dict(a=(tuple(c + Vector((0.9, -1.0, 1.1))), tuple(c)), b=(tuple(k + Vector((0.45, -0.55, 0.6))), tuple(k)), lens=45,
                fstop=2.8, focus=tuple(k), cine=dict(exposure=0.35))


VO = [l.strip() for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "vo", "MUMMY_P3_VO.txt"),
                               encoding="utf-8").read().split("\n") if l.strip()]

PLAN = [  # shot, VO paragraph (1-based), seconds (at 133 wpm; re-timed to the recorded VO), description
    ("S01", 1, 5.0, "Bronze Age roundhouse by firelight: three wrapped bundles on hurdles"),
    ("S02", 1, 4.0, "The second grave from above at last light"),
    ("S03", 2, 4.0, "Push in over the second skeleton toward its skull"),
    ("S04", 3, 4.5, "Lab: a female pelvis under the lamp (orbit)"),
    ("S05", 3, 4.0, "The male cranium, darker and stained"),
    ("S06", 3, 5.0, "Head and pelvis side by side: the skull older"),
    ("S07", 4, 3.0, "Sampling the skull: tubes beside it"),
    ("S08", 4, 2.5, "Sampling the lower jaw"),
    ("S09", 4, 2.5, "A drill hole in the upper arm bone"),
    ("S10", 4, 2.5, "A drill hole in the thigh bone"),
    ("S11", 5, 6.0, "Ancient-DNA clean room: a suited scientist at the UV cabinet (from behind)"),
    ("S12", 5, 5.0, "Inside the cabinet: tubes of bone powder under violet UV"),
    ("S13", 5, 4.5, "A sample tube, sharp; the rack soft behind"),
    ("S14", 6, 3.5, "Sequencing lab at night: status lights in the dark"),
    ("S15", 7, 5.0, "Jaw, upper arm and thigh bone apart: three pools of light"),
    ("S16", 7, 4.0, "The skull alone in low light: no answer"),
    ("S17", 8, 5.5, "Track along the second skeleton, feet to head"),
    ("S18", 9, 5.0, "Crane up from both graves to the whole house floor at dusk"),
    ("S19", 10, 4.5, "The roundhouses at dusk: six lives"),
    ("S20", 11, 5.0, "Macro: the crossed legs and the gap at the left knee"),
    ("S21", 11, 4.5, "The legs from the other side: right over the incomplete left"),
    ("S22", 12, 5.5, "Rack across the crossed legs to the break beneath"),
    ("S23", 13, 4.0, "Outside the house: a digger at a small separate pit (from behind)"),
    ("S24", 13, 3.5, "In the pit: pieces of a human knee"),
    ("S25", 14, 3.0, "Lab: the knee pieces against the broken leg - the breaks meet"),
    ("S26", 15, 3.5, "High over the trench: grave to knee pit, five metres"),
    ("S27", 16, 5.0, "Macro: a dry, chalky fracture face in grazing light"),
    ("S28", 16, 4.0, "Brittle bone: the shaft in raking light"),
    ("S29", 17, 3.5, "In the pit: the kneecap still against the femur end"),
    ("S30", 18, 5.0, "A dried, wrapped body on a hurdle in the dim roundhouse"),
    ("S31", 19, 4.5, "Night: two islanders reach into an opened grave by torchlight"),
    ("S32", 19, 4.5, "They lift the preserved body out on its hurdle (silhouettes)"),
    ("S33", 19, 4.0, "The empty grave: the broken knee left behind"),
    ("S34", 20, 5.0, "First light: they carry the body toward the roundhouse"),
    ("S35", 20, 4.5, "The second grave at dusk, push to the crossed legs"),
]
SHOTS = {sid: dict(fn=globals()[sid], dur=d, vo=VO[min(ln, len(VO)) - 1], line=ln, desc=desc) for sid, ln, d, desc in PLAN}
