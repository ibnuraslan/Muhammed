"""Part 6 (mummy/vo/MUMMY_P6_VO.txt): "The houses continued to change..." -> "...had buried at least six."

Same contract and house rules as p1-p5. No face toward the lens; clipcheck 0; motivated light; no text in frame.
Built from the approved sets (roundhouse interior, excavation, lab, clean room, AMS hall, microscope field, bog) plus a
museum store, a slide tray, a sanded-over ruin and a drying platform.
"""
import math, os, random
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
import uist as U, dig as G, cast as K, bones as B, lab as LB, bronze as BR, p2sets as P2, sf, ph
import p1, p2, p3, p4, p5

HAIR = p1.HAIR
_plain, _glass, _spot, _haze = p1._plain, p1._glass, p2._spot, p2._haze


# ----------------------------------------------------------------------------- helpers
def _cardboard():
    m = bpy.data.materials.get("cardboard")
    if m:
        return m
    m = _plain("cardboard", (0.36, 0.27, 0.17), 0.85)
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 60; nz.inputs['Detail'].default_value = 6
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.15; L.new(nz.outputs['Fac'], bp.inputs['Height']); L.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m


def store_room(length=9.0, lights=(1, 3, 4)):
    """A museum store: a long aisle between grey steel shelving, three shelves high, packed with plain archive boxes;
    overhead strip lights, only some of them on. Aisle along +y from y = 0."""
    steel = _plain("shelfsteel", (0.35, 0.37, 0.38), 0.45, 0.6)
    card = _cardboard()
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, length / 2, 0)); f = bpy.context.active_object
    f.scale = (6, length + 4, 1); f.data.materials.append(_plain("storefloor", (0.12, 0.12, 0.12), 0.35)); f.name = "floor"
    for loc, sc in (((0, length / 2, 3.0), (6, length + 4, 0.05)), ((0, length + 1.5, 1.5), (6, 0.05, 3.0)), ((-3, length / 2, 1.5), (0.05, length + 4, 3)), ((3, length / 2, 1.5), (0.05, length + 4, 3))):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.active_object; o.scale = sc
        o.data.materials.append(_plain("storewall", (0.22, 0.22, 0.21), 0.8)); o.name = "storewall"
    rng = random.Random(5)
    for sx in (-1, 1):
        x0 = sx * 0.85
        for k in range(int(length / 1.0)):
            y = 0.5 + k * 1.0
            for zz in (0.08, 0.75, 1.42, 2.09):
                bpy.ops.mesh.primitive_cube_add(size=1, location=(x0 + sx * 0.3, y, zz)); sh = bpy.context.active_object
                sh.scale = (0.6, 1.0, 0.025); sh.data.materials.append(steel); sh.name = "shelf"
            for dy in (-0.49, 0.49):
                bpy.ops.mesh.primitive_cube_add(size=1, location=(x0 + sx * 0.02, y + dy, 1.1)); up = bpy.context.active_object
                up.scale = (0.03, 0.03, 2.2); up.data.materials.append(steel); up.name = "shelf"
            for zz in (0.08, 0.75, 1.42):
                xx = 0
                while xx < 0.95:
                    w = rng.choice((0.3, 0.3, 0.42))
                    if xx + w > 0.98:
                        break
                    h = rng.uniform(0.22, 0.3)
                    bpy.ops.mesh.primitive_cube_add(size=1, location=(x0 + sx * 0.3, y - 0.48 + xx + w / 2, zz + 0.013 + h / 2)); bx = bpy.context.active_object
                    bx.scale = (0.48, w - 0.015, h); bx.rotation_euler.z = rng.uniform(-0.02, 0.02); bx.data.materials.append(card); bx.name = "archivebox"
                    bv = bx.modifiers.new("b", "BEVEL"); bv.width = 0.004; bv.segments = 1
                    xx += w
    em = _plain("striplight", (1, 1, 1), 0.3)
    for k in range(int(length / 2) + 1):
        y = 1.0 + k * 2.0
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, y, 2.9)); t = bpy.context.active_object; t.scale = (0.08, 1.2, 0.03); t.name = "strip"
        t.data.materials.append(em)
        if k in lights:
            d = bpy.data.lights.new("strip", 'AREA'); d.shape = 'RECTANGLE'; d.size = 0.08; d.size_y = 1.2; d.energy = 70; d.color = (0.9, 0.95, 1.0)
            lo = bpy.data.objects.new("strip", d); bpy.context.scene.collection.objects.link(lo); lo.location = (0, y, 2.86)
    w = bpy.context.scene.world or bpy.data.worlds.new("w"); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs['Color'].default_value = (0.02, 0.02, 0.025, 1)
    return length


def slide_tray(c, n_x=6, n_y=6, mark=None):
    """A black slide tray of 36 thin sections: glass slides, each with a round ground section of bone on it."""
    cx, cy, cz = c
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, cz + 0.006)); t = bpy.context.active_object
    t.scale = (n_x * 0.033 + 0.02, n_y * 0.08 + 0.02, 0.012); t.data.materials.append(_plain("slidetray", (0.32, 0.33, 0.35), 0.45)); t.name = "slidetray"
    gl = _glass("slideglass"); rng = random.Random(15)
    for i in range(n_x):
        for j in range(n_y):
            x = cx - (n_x - 1) * 0.033 / 2 + i * 0.033; y = cy - (n_y - 1) * 0.08 / 2 + j * 0.08
            bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, cz + 0.0135)); s = bpy.context.active_object
            s.scale = (0.026, 0.075, 0.0012); s.data.materials.append(gl); s.name = "slide"
            bpy.ops.mesh.primitive_cylinder_add(radius=0.0085 * rng.uniform(0.8, 1.15), depth=0.0004, location=(x, y + 0.01, cz + 0.0145)); d = bpy.context.active_object
            tone = rng.uniform(0.3, 0.6)
            d.data.materials.append(_plain(f"section{k_(i, j)}", (0.55 * tone + 0.2, 0.38 * tone + 0.12, 0.18 * tone + 0.05), 0.4)); d.name = "section"
    return t


def k_(i, j):
    return (i * 7 + j * 3) % 5


def ruin(hx, hy, r, sand=0.55, seed=0):
    """A roundhouse after abandonment: the low stone wall ring, roof gone, sand blown in and heaped against it."""
    z0 = float(U.surface(hx, hy)) - 0.2
    BR.drystone_wall(hx, hy, r, z0, h=0.7, seed=seed)
    G.spoil_heap(hx, hy, r * 1.5, r * 1.4, sand)                        # the interior filled with blown sand
    for k in range(6):
        a = random.Random(seed + k).uniform(0, 6.28)
        G.spoil_heap(hx + (r + 0.6) * math.cos(a), hy + (r + 0.6) * math.sin(a), 2.6, 1.6, sand * 0.8)   # drifts banked against the wall


def drying_platform(c):
    """A raised platform of four posts and a hurdle deck, the wrapped body laid on it to dry in the wind and smoke of
    a smouldering peat fire below."""
    cx, cy, cz = c
    wood = bpy.data.materials.get("postbark") or ph.texture("bark_brown_02", scale=3.0, name="postbark", tint=(0.6, 0.5, 0.42))
    for dx in (-0.85, 0.85):
        for dy in (-0.42, 0.42):
            bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.9, location=(cx + dx, cy + dy, cz + 0.95)); p = bpy.context.active_object
            p.rotation_euler = (random.uniform(-0.04, 0.04), random.uniform(-0.04, 0.04), 0); p.data.materials.append(wood); p.name = "platformpost"
    P2.hurdle((cx, cy, cz + 1.55), rot=0.0, length=1.9, width=0.95)
    P2.bundle((cx, cy, cz + 1.75), rot=0.0, length=0.95, girth=0.42)
    for k in range(9):
        a = 2 * math.pi * k / 9
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx + 0.15 * math.cos(a), cy + 0.12 * math.sin(a), cz + 0.05)); pb = bpy.context.active_object
        pb.scale = (0.14, 0.07, 0.06); pb.rotation_euler = (0.3, 0.2, a); pb.data.materials.append(bpy.data.materials.get("peatfire") or _plain("peatlow", (0.02, 0.012, 0.008), 0.9)); pb.name = "peat"
    d = bpy.data.lights.new("smoulder", 'POINT'); d.energy = 60; d.color = (1.0, 0.4, 0.12)
    lo = bpy.data.objects.new("smoulder", d); bpy.context.scene.collection.objects.link(lo); lo.location = (cx, cy, cz + 0.2)
    BR.smoke((cx, cy, cz + 0.2), height=8.0, drift=(0.8, 0.25), r0=0.35, grow=0.35, density=1.6, name="dryingsmoke")


# ============================================================================ "The houses continued to change..."
def S01():
    """Daylight through the doorway into the middle house: the hearth, quern, pots, sheepskins - a lived-in room."""
    U.CUT = False
    R = BR.interior(fire=0.5, door_sun=1.0)
    hx, hy = R["hearth"]
    return dict(a=((hx - 3.0, hy - 1.8, 1.4), (hx + 1.0, hy + 0.3, 0.5)), b=((hx - 2.6, hy - 1.4, 1.3), (hx + 1.4, hy + 0.3, 0.5)), lens=24,
                fstop=4.0, focus=(hx, hy, 0.3), cine=dict(exposure=0.3), hand_ok=("floor",))


def S02():
    """Floors renewed: the excavated section through the house floors, layer over layer, in raking light. Slow crane up."""
    p1.site("golden", grass_at=(5, 18), grass_r=8, kit=False, burials=False, sun_az=160, focus=(3.0, 15.0), core=2.5)
    y = U.DIG["y1"]
    G.section_scan(y, x_center=3.2)
    z = G.H(3.2, y - 1.6)
    return dict(a=((2.5, y - 2.0, z + 0.35), (3.2, y - 1.02, z + 0.45)), b=((2.6, y - 2.1, z + 0.85), (3.3, y - 1.02, z + 0.75)), lens=40,
                fstop=5.6, focus=(3.2, y - 1.05, z + 0.3))


def S03():
    """Grinding grain: a woman kneels at the saddle quern by the hearth, both hands on the rubbing stone (from behind)."""
    U.CUT = False
    R = BR.interior(fire=0.8, door_sun=0.6)
    hx, hy = 0.3, 0.0
    qx, qy = hx - 1.8, hy - 1.6                    # the quern placed by interior()
    look = (qx, qy, 0.1)
    hands = {"L": (qx - 0.06, qy + 0.05, 0.16), "R": (qx + 0.06, qy + 0.05, 0.16)}
    p5._kneeler(0, "Grinder", (qx, qy - 0.55), 90, look, lean=48, var=3, hands=hands)
    _spot((qx + 2.4, qy + 0.3, 1.3), (qx, qy, 0.1), 160, size=0.6, color=(1.0, 0.92, 0.8), spot=40)     # daylight from the door
    return dict(a=((qx + 1.3, qy - 1.3, 1.6), (qx, qy, 0.12)), b=((qx + 1.1, qy - 1.1, 1.5), (qx, qy, 0.12)), lens=35,
                fstop=4.0, focus=(qx, qy, 0.15), cine=dict(exposure=0.45), hand_ok=("floor", "quern", "saddle"))


def S04():
    """Sleeping and storage: sheepskins and baskets against the wall, pots in the dim back of the house. Slow slide."""
    U.CUT = False
    R = BR.interior(fire=0.7, door_sun=0.5)
    hx, hy = 0.3, 0.0
    t = Vector((hx - 2.3, hy + 1.6, 0.2))                         # the pots and the basket against the north-west wall
    _spot((hx + 1.0, hy - 0.4, 1.6), tuple(t), 260, size=0.8, color=(1.0, 0.9, 0.78), spot=45)      # daylight carried in from the door
    return dict(a=((hx - 0.4, hy + 0.1, 1.05), tuple(t)), b=((hx - 0.7, hy + 0.35, 1.0), tuple(t)), lens=32,
                fstop=2.8, focus=tuple(t), cine=dict(exposure=0.45), hand_ok=("floor",))


# ============================================================================ "Above the buried remains, people ground grain..."
def S05():
    """Working materials: an islander kneels at the doorway light scraping a stretched hide (from behind)."""
    U.CUT = False
    R = BR.interior(fire=0.6, door_sun=1.0)
    hx, hy = 0.3, 0.0
    px, py = hx + 3.75, hy + 0.05                         # in the doorway, outside the post ring
    hide = _plain("rawhide", (0.42, 0.3, 0.18), 0.7)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(px, py, 0.02)); hd = bpy.context.active_object
    hd.scale = (0.9, 0.7, 1); hd.data.materials.append(hide); hd.name = "hide"
    dd = hd.modifiers.new("s", "SUBSURF"); dd.subdivision_type = 'SIMPLE'; dd.levels = 3
    dp = hd.modifiers.new("d", "DISPLACE"); tt = bpy.data.textures.new("hidewrinkle", "CLOUDS"); tt.noise_scale = 0.12; dp.texture = tt; dp.strength = 0.02
    hands = {"L": (px - 0.1, py + 0.05, 0.06), "R": (px + 0.1, py + 0.08, 0.06)}
    p5._kneeler(0, "Scraper", (px - 0.05, py - 0.55), 90, (px, py, 0.0), lean=52, var=4, hands=hands)
    return dict(a=((px - 0.7, py - 1.7, 1.45), (px, py, 0.05)), b=((px - 0.55, py - 1.45, 1.35), (px, py, 0.05)), lens=35,
                fstop=2.8, focus=(px, py, 0.05), cine=dict(exposure=0.3), hand_ok=("floor", "hide"))


def S06():
    """New floors over old: the excavated house floor in the trench, its hearth and the darker floor layers, raking sun."""
    G.SCANNED = True                                          # scanned stone kerb and wall
    T, sk = p1.site("golden", grass_at=None, kit=False, burials=True, sun_az=205)
    hx, hy, r = U.HOUSES[1]
    z = G.H(hx, hy)
    hz = Vector((hx + 0.4, hy, z))
    return dict(a=((hx + 1.7, hy - 1.5, z + 0.55), tuple(hz)), b=((hx + 1.3, hy - 1.15, z + 0.48), tuple(hz)), lens=30,
                fstop=5.6, focus=tuple(hz), cine=dict(exposure=0.15))


# ============================================================================ "By the time sand covered the settlement..."
def S07():
    """Abandonment: the roofless stone rings of the houses, half full of blown sand, marram on the drifts. Dusk crane."""
    U.CUT = False
    U.island("dusk", grass_at=(30, 0), grass_r=14, n=820, core=4.0, grass_density=200, sun_az=215)   # bare sand round the ruins
    for k, (hx, hy, r) in enumerate(U.HOUSES):
        ruin(hx, hy, r * 1.75, sand=0.6, seed=k)
    z = float(U.surface(0, 0))
    p2._sand_drift((0, 0, z), size=(60, 60, 0.6), density=1.0)
    return dict(a=((14, -10, z + 2.5), (0, 0, z)), b=((16, -12, z + 6.0), (0, 0, z)), lens=28, fstop=5.6, focus=(0, 0, z), cine=dict(exposure=0.3))


def S08():
    """Sand moving: wind streaming sand low over the dunes, marram bending, the light going. Low slider."""
    U.CUT = False
    U.island("dusk", grass_at=(-60, 0), grass_r=30, n=820, core=4.0, grass_density=260, sun_az=220)
    x = -60.0; z = float(U.surface(x, 0))
    p2._sand_drift((x, 0, z), size=(60, 60, 0.7), density=1.3)
    return dict(a=((x + 6, -6, z + 0.5), (x - 8, 4, z + 0.6)), b=((x + 5, -4.5, z + 0.55), (x - 8, 5, z + 0.6)), lens=32,
                fstop=5.6, focus=(x, 0, z), cine=dict(exposure=0.3))


# ============================================================================ "The excavation brings those bodies back into view..."
def S09():
    """The excavation: a digger (from behind, over the shoulder) trowelling beside a crouched skeleton in its grave."""
    T, sk = p1.site("golden", grass_at=None, kit=True, burials=True, sun_az=205)
    c, _ = sk["B1"].centre()
    st = K.kneel_trowel(K.DiggerA, (c.x + 0.75, c.y - 0.85), 135, work=(c.x + 0.3, c.y - 0.35), density=HAIR)
    h = st.m.h
    shR = st.M @ h.bone_head("upperarm01.R"); shL = st.M @ h.bone_head("upperarm01.L")
    rt = Vector((shR.x - shL.x, shR.y - shL.y, 0)).normalized()
    cam = shR + rt * 0.35 + Vector((0, 0, 0.45))
    return dict(a=(tuple(cam), tuple(c)), b=(tuple(cam + Vector((0, 0, 0.15))), tuple(c)), lens=28, fstop=4.0, focus=tuple(c), hand_ok=p1.OK)


def S10():
    """Teeth: a lower jaw beside a skull on the bench - the jaw's teeth do not fit the skull's. Slow push to the teeth."""
    A = LB.room(window_light=0.3, lamp=True, lamp_at=(0.35, 0.62), lamp_target=(0.0, 0.38), lamp_energy=20)
    LB.velvet(-0.6, 0.7, 0.0, 0.78, LB.TOP)
    cr = B.hero_cranium(healed=False, tone="D"); p3._old_bone(cr, stain=0.9, etch=0.45)
    co = np.array([v.co for v in cr.data.vertices]); cr.location = (-0.12, 0.42, LB.TOP + 0.004 - co[:, 2].min() * 0.97)
    cr.rotation_euler = (0, 0, math.radians(-35))
    p3.lab_part("mandible", sex="M", tone="B", x=0.14, y=0.36, yaw=15, name="OtherJaw")
    t = Vector((0.02, 0.38, LB.TOP + 0.04))
    return dict(a=(tuple(t + Vector((0.1, -0.75, 0.32))), tuple(t)), b=(tuple(t + Vector((0.05, -0.62, 0.27))), tuple(t)), lens=45,
                fstop=4.0, focus=tuple(t), cine=dict(exposure=-0.05))


def S11():
    """Chemistry: the accelerator hall - the beamline running away under the work lights. Slow push."""
    P2.ams_hall()
    return dict(a=((0.6, -6.5, 1.5), (0, 4, 1.2)), b=((0.4, -5.4, 1.45), (0, 4, 1.2)), lens=28, fstop=4.0, focus=(0, -1, 1.2), cine=dict(exposure=0.1))


def S12():
    """DNA: the suited scientist at the cabinet (from behind), hands in at the sample racks, the violet accent."""
    d = p3.S11()
    d.update(a=((-0.55, 0.15, 1.75), (0.05, 1.55, 0.95)), b=((-0.45, 0.25, 1.7), (0.05, 1.58, 0.95)))
    return d


# ============================================================================ "Then the broken knee reconnects a body to a place outside the house..."
def S13():
    """Outside the house: the small knee pit beyond the house wall in the trench - high, the two places in one frame."""
    o = p3._knee_pit(kneel=False)                     # the pit with the knee pieces in it
    kp = Vector(o["knee"])
    b2 = Vector((U.PITS["B2"][0], U.PITS["B2"][1], G.H(U.PITS["B2"][0], U.PITS["B2"][1])))
    m = (kp + b2) / 2
    return dict(a=(tuple(kp + Vector((0.6, -0.9, 1.2))), tuple(kp)), b=(tuple(m + Vector((1.6, -2.4, 4.4))), tuple(m)), lens=30,
                fstop=8.0, focus=tuple(m), cine=dict(exposure=0.1))


# ============================================================================ "The discovery also gives researchers a way to look..."
def S14():
    """A museum store: the long aisle of shelving and archive boxes, a few lights on. Slow dolly down the aisle."""
    L_ = store_room()
    return dict(a=((0.0, -0.6, 1.5), (0.0, L_, 1.2)), b=((0.0, 1.2, 1.45), (0.0, L_ + 1, 1.2)), lens=28, fstop=4.0, focus=(0, 4, 1.2), cine=dict(exposure=0.2))


def S15():
    """In a box from the store: a skeleton packed in its archive box, the lid off, under a lamp - long recorded as bones."""
    store_room(lights=(0, 1))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.0, 1.0, 0.45)); tb = bpy.context.active_object
    tb.scale = (1.2, 0.7, 0.9); tb.data.materials.append(_plain("storetable", (0.3, 0.31, 0.32), 0.4, 0.5)); tb.name = "table"
    top = 0.9
    card = _cardboard()
    for loc, sc in (((0, 1.0, top + 0.004), (0.7, 0.42, 0.008)), ((0, 0.79, top + 0.11), (0.7, 0.006, 0.22)), ((0, 1.21, top + 0.11), (0.7, 0.006, 0.22)),
                    ((-0.35, 1.0, top + 0.11), (0.006, 0.42, 0.22)), ((0.35, 1.0, top + 0.11), (0.006, 0.42, 0.22))):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.active_object; o.scale = sc; o.data.materials.append(card); o.name = "archivebox"
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.55, 0.95, top + 0.01)); lid = bpy.context.active_object
    lid.scale = (0.25, 0.44, 0.02); lid.rotation_euler.z = 0.3; lid.data.materials.append(card); lid.name = "archivebox"
    rng = random.Random(3)
    for k, (seg, x, y) in enumerate((("femurL", -0.15, 1.05), ("femurR", -0.12, 0.92), ("shankL", 0.12, 1.08), ("upperarmR", 0.15, 0.93))):
        sk, W = p3.lab_part(seg, sex="M", tone="C", x=x, y=y, yaw=rng.uniform(-8, 8), name=f"Boxed{k}")
        dz = top + 0.009 - float(W[:, 2].min())
        sk.root.location.z += dz
    _spot((-0.4, 0.4, top + 0.9), (0, 1.0, top), 80, size=0.1, color=(1.0, 0.92, 0.82), spot=40)
    t = Vector((0, 1.0, top + 0.03))
    return dict(a=(tuple(t + Vector((0.0, -0.7, 0.75))), tuple(t)), b=(tuple(t + Vector((0.08, -0.58, 0.65))), tuple(t)), lens=35,
                fstop=4.0, focus=tuple(t), cine=dict(exposure=0.0))


def S16():
    """Under the microscope: a section of well-preserved bone - intact osteons, almost no tunnelling. Slow drift."""
    d = p2._field("human", attack=0.0)
    d.update(a=((0.2, 0.15, 3.6), (0.2, 0.15, 0)), b=((0.05, 0.0, 3.3), (0.05, 0.0, 0)))
    return d


# ============================================================================ "In a study published in 2015..."
def S17():
    """Thirty-six samples: a tray of thin sections of bone on glass under the lamp. Slow slide across the rows."""
    A = LB.room(window_light=0.3, lamp=True, lamp_at=(0.35, 0.62), lamp_target=(0.0, 0.38), lamp_energy=18)
    slide_tray((0.0, 0.38, LB.TOP))
    t = Vector((0.0, 0.38, LB.TOP + 0.015))
    return dict(a=(tuple(t + Vector((-0.2, -0.32, 0.26))), tuple(t)), b=(tuple(t + Vector((0.16, -0.3, 0.24))), tuple(t)), lens=45,
                fstop=5.6, focus=tuple(t), cine=dict(exposure=-0.05))


def S18():
    """A researcher at the microscope (from behind), a slide from the tray on the stage. Push past the shoulder."""
    d = p2.S12()
    slide_tray((-0.3, 0.3, LB.TOP + 0.002), n_x=3, n_y=3)
    import acts as AC
    m = K.OsteologistNeat("Osteologist")
    st = AC.Stand(m, (0.05, -0.35), 90, lean=22)
    st.hand("L", (-0.05, 0.3, LB.TOP + 0.03), elbow=(0.6, 0.2, -0.8), curl=18)
    st.hand("R", (0.07, 0.32, LB.TOP + 0.05), elbow=(0.6, 0.2, -0.8), curl=18)
    st.head_to((0.0, 0.42, LB.TOP + 0.3), share=0.8); st.finish(look=(0.0, 0.42, LB.TOP + 0.3), density=1.0)
    t = Vector((0.0, 0.42, LB.TOP + 0.2))
    return dict(a=((0.55, -1.05, LB.TOP + 0.75), tuple(t)), b=((0.45, -0.85, LB.TOP + 0.7), tuple(t)), lens=35, fstop=4.0, focus=tuple(t),
                cine=dict(exposure=0.0), hand_ok=("slide", "slidetray", "velvet", "bench"))


# ============================================================================ "It suggests the practice extended beyond this island..."
def S19():
    """Beyond the island: the long Atlantic coast at dawn from high above, headland after headland. Slow drone."""
    U.CUT = False
    U.island("dawn", grass_at=None, n=820, core=6.0)
    return dict(a=((-120, -260, 160), (-260, 60, 0)), b=((-100, -210, 150), (-260, 120, 0)), lens=28, fstop=8.0, focus=(-200, 0, 0), cine=dict(exposure=0.2))


def S20():
    """Some may have dried their dead: a wrapped body on a raised platform on the machair, smoke drifting from a peat
    fire smouldering beneath it, dusk wind. Slow push."""
    U.CUT = False
    U.island("dusk", grass_at=(8, 0), grass_r=20, n=820, core=4.0, grass_density=240, sun_az=210)
    c = (8.0, 0.0, float(U.surface(8.0, 0.0)))
    drying_platform(c)
    return dict(a=((c[0] + 6.5, c[1] - 5.5, c[2] + 1.3), (c[0], c[1], c[2] + 1.4)), b=((c[0] + 5.2, c[1] - 4.4, c[2] + 1.25), (c[0], c[1], c[2] + 1.4)),
                lens=35, fstop=5.6, focus=(c[0], c[1], c[2] + 1.4), cine=dict(exposure=0.3))


def S21():
    """Others may have used wetlands: the wrapped body sinking in a bog pool, the sky in the dark water. High and still."""
    M = p2._bog_scene("dawn", sun_az=120)
    wz = M["water_z"]
    bx, by = p2._pool_spot(M, margin=0.45)
    P2.bundle((bx, by, wz - 0.12), rot=math.radians(20))
    return dict(a=((bx + 2.2, by - 2.6, wz + 3.2), (bx, by, wz)), b=((bx + 1.8, by - 2.1, wz + 2.6), (bx, by, wz)), lens=35,
                fstop=5.6, focus=(bx, by, wz), cine=dict(exposure=0.25))


# ============================================================================ "The implication reaches into collections already excavated..."
def S22():
    """The store again, from the far end: rows of boxes going back into the dark. Slow lateral move across the aisle end."""
    L_ = store_room(lights=(0, 2, 4))
    return dict(a=((-0.5, L_ + 0.8, 1.2), (0.3, 0.0, 1.1)), b=((0.5, L_ + 0.8, 1.2), (-0.3, 0.0, 1.1)), lens=32, fstop=4.0,
                focus=(0, L_ - 2, 1.1), cine=dict(exposure=0.2))


def S23():
    """Cladh Hallan: the two graves under the house floor in the trench at golden hour, the diggers' kit at the edge."""
    T, sk = p1.site("golden", grass_at=None, kit=True, burials=True, sun_az=200)
    c1, _ = sk["B1"].centre(); c2, _ = sk["B2"].centre()
    m = (c1 + c2) / 2
    return dict(a=(tuple(m + Vector((2.2, -3.4, 2.4))), tuple(m)), b=(tuple(m + Vector((1.8, -2.8, 2.0))), tuple(m)), lens=30,
                fstop=5.6, focus=tuple(m), cine=dict(exposure=0.15))


# ============================================================================ "There are still missing pieces..."
def S24():
    """Missing pieces: the composite skeleton on the bench with the gaps where parts were never found. Overhead drift."""
    A = LB.room(window_light=0.2, lamp=True, lamp_at=(-0.2, 0.62), lamp_target=(0.3, 0.35), lamp_energy=18)
    LB.velvet(-1.15, 1.2, 0.0, 0.78, LB.TOP)
    sk = B.Skeleton("M", "C", name="Incomplete", sand=0.5)
    sk.remove("skull", "mandible", "handL", "footR", "forearmR", "patellaL", "shankL")
    sk.root.rotation_euler = (math.radians(-90), 0, math.radians(-90))
    bpy.context.view_layer.update()
    xs = [(o.matrix_world @ v.co).x for o in sk.parts.values() for v in o.data.vertices[:]]
    zmin = min((o.matrix_world @ v.co).z for o in sk.parts.values() for v in o.data.vertices[:])
    sk.root.location = (-(min(xs) + max(xs)) / 2, 0.38, LB.TOP + 0.004 - zmin)
    bpy.context.view_layer.update()
    sk.settle(lambda x, y: LB.TOP + 0.004, sink=0.0, keep=0.55)
    for o in sk.parts.values():
        p3._knee_mats(o, sand=0.5)
    t = Vector((0.0, 0.38, LB.TOP))
    return dict(a=((0.25, 0.0, LB.TOP + 1.25), tuple(t)), b=((-0.25, 0.05, LB.TOP + 1.15), tuple(t)), lens=28, fstop=5.6, focus=tuple(t),
                cine=dict(exposure=0.0))


def S25():
    """Their names are gone: the empty grave in the trench at dusk, the cut edges, a trowel left on the spoil."""
    T, sk = p1.site("dusk", grass_at=None, kit=True, burials=False, sun_az=210)
    b1 = Vector((U.PITS["B1"][0], U.PITS["B1"][1], G.H(U.PITS["B1"][0], U.PITS["B1"][1])))
    return dict(a=(tuple(b1 + Vector((1.4, -1.6, 1.3))), tuple(b1)), b=(tuple(b1 + Vector((1.0, -1.2, 1.0))), tuple(b1)), lens=32,
                fstop=5.6, focus=tuple(b1), cine=dict(exposure=0.3))


# ============================================================================ "What survives is the result of someone's decisions." / "A skull was kept..."
def S26():
    """A skull was kept: the old dark skull alone, lamplight across the brow. Very slow push."""
    cs = p5._three_parts(lit=False)
    c = cs[0]
    _spot((c.x - 0.45, c.y - 0.2, c.z + 0.35), tuple(c), 55, size=0.04, color=(1.0, 0.88, 0.74), spot=14)
    return dict(a=((c.x + 0.25, c.y - 0.55, c.z + 0.08), tuple(c)), b=((c.x + 0.2, c.y - 0.47, c.z + 0.07), tuple(c)), lens=60,
                fstop=4.0, focus=tuple(c), cine=dict(exposure=-0.05))


def S27():
    """A jaw was chosen: the lower jaw on the velvet, the teeth catching the lamp. Slow slide."""
    A = LB.room(window_light=0.15, lamp=False)
    LB.velvet(-0.6, 0.7, 0.0, 0.78, LB.TOP)
    sk, W = p3.lab_part("mandible", sex="M", tone="B", x=0.0, y=0.4, yaw=20, name="ChosenJaw")
    t = Vector(((W.min(0) + W.max(0)) / 2).tolist())
    _spot((t.x - 0.4, t.y - 0.3, t.z + 0.35), tuple(t), 45, size=0.04, color=(1.0, 0.9, 0.78), spot=16)
    return dict(a=(tuple(t + Vector((-0.12, -0.3, 0.12))), tuple(t)), b=(tuple(t + Vector((0.06, -0.31, 0.12))), tuple(t)), lens=60,
                fstop=4.0, focus=tuple(t), cine=dict(exposure=-0.05))


def S28():
    """An arm was moved: the arm bone laid across the dark velvet in a narrow beam. Slow slide along it."""
    A = LB.room(window_light=0.15, lamp=False)
    LB.velvet(-0.6, 0.7, 0.0, 0.78, LB.TOP)
    sk, W = p3.lab_part("upperarmR", sex="M", tone="A", x=0.0, y=0.4, yaw=-12, name="MovedArm")
    t = Vector(((W.min(0) + W.max(0)) / 2).tolist())
    _spot((t.x + 0.1, t.y - 0.5, t.z + 0.45), tuple(t), 45, size=0.04, color=(1.0, 0.9, 0.78), spot=18)
    return dict(a=(tuple(t + Vector((-0.14, -0.36, 0.14))), tuple(t + Vector((-0.06, 0, 0)))), b=(tuple(t + Vector((0.12, -0.36, 0.14))), tuple(t + Vector((0.06, 0, 0)))),
                lens=55, fstop=4.0, focus=tuple(t), cine=dict(exposure=-0.05))


# ============================================================================ "More than three thousand years later..." / "...at least six."
def S29():
    """They still look like individual people: the crouched skeleton in its grave in the last light. Slow push."""
    T, sk = p1.site("golden", grass_at=None, kit=False, burials=True, sun_az=200)
    g = sk["B2"]; c, _ = g.centre(); s = g.part_centre("skull")
    return dict(a=(tuple(c + Vector((1.0, -1.0, 1.1))), tuple(c)), b=(tuple(c + Vector((0.7, -0.7, 0.85))), tuple((c + s) / 2)), lens=35,
                fstop=4.0, focus=tuple(c), cine=dict(exposure=0.25))


def S30():
    """Two bodies uncovered; at least six buried: rising from the two graves up and away over the dig, the houses'
    rings and the island at dusk. Final crane."""
    p1.site("dusk", grass_at=(4, 0), grass_r=55, focus=(0, 0), core=6.0, n=900, kit=True, burials=True, sun_az=230, grass_density=260)
    U.cloud_shadows((0, 0), cover=0.45, seed=11)
    b1 = Vector((U.PITS["B1"][0], U.PITS["B1"][1], G.H(U.PITS["B1"][0], U.PITS["B1"][1])))
    return dict(a=(tuple(b1 + Vector((0.8, -1.2, 1.6))), tuple(b1)), b=((60, -90, 70), (-20, 30, 0)), lens=26, cine=dict(exposure=0.3))


# ----------------------------------------------------------------------------- plan
VO = [l.strip() for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "vo", "MUMMY_P6_VO.txt"),
                               encoding="utf-8").read().split("\n") if l.strip()]

PLAN = [  # shot, VO paragraph (1-based), seconds, description
    ("S01", 1, 5.0, "Daylight through the door: a lived-in roundhouse"),
    ("S02", 1, 5.0, "Floors renewed: the section through the house floors"),
    ("S03", 1, 5.0, "Grinding grain at the saddle quern"),
    ("S04", 1, 4.5, "Sleeping and storage: sheepskins, baskets, pots"),
    ("S05", 2, 5.0, "Working materials: scraping a hide in the doorway light"),
    ("S06", 2, 5.0, "The excavated house floor and hearth"),
    ("S07", 3, 6.0, "Abandonment: roofless stone rings filling with sand"),
    ("S08", 3, 5.0, "Wind streaming sand over the dunes"),
    ("S09", 4, 5.0, "The excavation: trowelling beside a skeleton"),
    ("S10", 4, 4.5, "Teeth: a jaw beside a skull it does not fit"),
    ("S11", 4, 4.0, "Chemistry: the accelerator hall"),
    ("S12", 4, 4.0, "DNA: the suited scientist at the cabinet"),
    ("S13", 5, 5.5, "The knee pit outside the house, and the grave"),
    ("S14", 6, 5.0, "A museum store: the long aisle of boxes"),
    ("S15", 7, 5.5, "A skeleton in its archive box"),
    ("S16", 7, 5.0, "Under the microscope: well-preserved bone"),
    ("S17", 8, 5.0, "Thirty-six samples: a tray of thin sections"),
    ("S18", 8, 5.0, "A researcher at the microscope"),
    ("S19", 9, 5.0, "Beyond the island: the long coast from above"),
    ("S20", 9, 5.5, "Drying the dead: a body on a platform over a peat fire"),
    ("S21", 9, 5.0, "Wetlands: a body sinking in a bog pool"),
    ("S22", 10, 5.0, "The store from the far end: rows into the dark"),
    ("S23", 10, 5.0, "Cladh Hallan: the two graves under the house floor"),
    ("S24", 11, 5.5, "Missing pieces: the incomplete skeleton on the bench"),
    ("S25", 11, 4.5, "The empty grave at dusk"),
    ("S26", 13, 3.0, "A skull was kept"),
    ("S27", 13, 3.0, "A jaw was chosen"),
    ("S28", 13, 3.0, "An arm was moved"),
    ("S29", 14, 5.5, "The crouched skeleton in the last light"),
    ("S30", 15, 8.0, "Final: rising from the graves over the island at dusk"),
]
SHOTS = {sid: dict(fn=globals()[sid], dur=d, vo=VO[min(ln, len(VO)) - 1], line=ln, desc=desc) for sid, ln, d, desc in PLAN}
