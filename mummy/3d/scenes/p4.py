"""Part 4 (mummy/vo/MUMMY_P4_VO.txt): "This changes the picture..." -> "...the people building above them."

Same contract and house rules as p1-p3. No face toward the lens; clipcheck 0; motivated light; no text in frame.
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
def _calcined(name="calcined"):
    """Cremated bone: chalky white to blue-grey and black-brown where it burned less, crazed with fine cracks."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 18; nz.inputs['Detail'].default_value = 6; L.new(tc.outputs['Object'], nz.inputs['Vector'])
    rp = N.new("ShaderNodeValToRGB"); el = rp.color_ramp.elements
    el[0].position = 0.35; el[0].color = (0.06, 0.055, 0.05, 1)
    e = el.new(0.47); e.color = (0.24, 0.25, 0.27, 1)
    el[-1].position = 0.62; el[-1].color = (0.52, 0.5, 0.47, 1)
    L.new(nz.outputs['Fac'], rp.inputs['Fac'])
    cr = N.new("ShaderNodeTexVoronoi"); cr.feature = 'DISTANCE_TO_EDGE'; cr.inputs['Scale'].default_value = 220; L.new(tc.outputs['Object'], cr.inputs['Vector'])
    cm = N.new("ShaderNodeMapRange"); cm.inputs['From Min'].default_value = 0.0; cm.inputs['From Max'].default_value = 0.04
    cm.inputs['To Min'].default_value = 0.25; cm.inputs['To Max'].default_value = 1.0; L.new(cr.outputs['Distance'], cm.inputs['Value'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    L.new(rp.outputs['Color'], mx.inputs[6]); cc = N.new("ShaderNodeCombineXYZ")
    for k in range(3):
        L.new(cm.outputs[0], cc.inputs[k])
    L.new(cc.outputs[0], mx.inputs[7]); L.new(mx.outputs[2], p.inputs['Base Color'])
    bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.6; bp.inputs['Distance'].default_value = 0.0008
    L.new(cr.outputs['Distance'], bp.inputs['Height']); L.new(bp.outputs['Normal'], p.inputs['Normal'])
    p.inputs['Roughness'].default_value = 0.9
    return m


def cremation(center, radius=0.12, n=90, seed=1, charcoal=40, flat=False):
    """A small heap of cremated bone fragments with charcoal in a little pit: angular, warped, cracked pieces."""
    rng = random.Random(seed)
    cx, cy, cz = center
    bm = bmesh.new()
    for k in range(n):
        a = rng.uniform(0, 6.283); r = radius * math.sqrt(rng.random())
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        big = rng.random() > 0.8
        # a sliver of the wall of a long bone: a curved shell patch, warped and twisted by the heat, jagged at the ends
        L = rng.uniform(0.006, 0.016) * (1.8 if big else 1.0)
        R = rng.uniform(0.004, 0.009); t = R * rng.uniform(0.2, 0.35)
        span = rng.uniform(0.7, 2.4); nu, nv = 5, 4
        bend = rng.uniform(-14, 14); twist = rng.uniform(-0.6, 0.6)
        ends = [[rng.uniform(-0.25, 0.25) * L / nv for _ in range(nu + 1)] for _ in range(2)]
        grid = {}
        for side, rr in (("o", R), ("i", R - t)):
            for i in range(nu + 1):
                for j in range(nv + 1):
                    v = -L / 2 + L * j / nv
                    if j == 0:
                        v += ends[0][i]
                    elif j == nv:
                        v += ends[1][i]
                    th = -span / 2 + span * i / nu + twist * v / L
                    rj = rr * (1 + 0.08 * math.sin(3.1 * i + 1.7 * j + k))
                    co = Vector((rj * math.cos(th), v, rj * math.sin(th) - R + bend * v * v))
                    grid[side, i, j] = bm.verts.new(co)
        def f(*vs):
            try:
                bm.faces.new(vs)
            except ValueError:
                pass
        for i in range(nu):
            for j in range(nv):
                f(grid["o", i, j], grid["o", i + 1, j], grid["o", i + 1, j + 1], grid["o", i, j + 1])
                f(grid["i", i, j + 1], grid["i", i + 1, j + 1], grid["i", i + 1, j], grid["i", i, j])
        for i in range(nu):
            f(grid["o", i, 0], grid["i", i, 0], grid["i", i + 1, 0], grid["o", i + 1, 0])
            f(grid["o", i + 1, nv], grid["i", i + 1, nv], grid["i", i, nv], grid["o", i, nv])
        for j in range(nv):
            f(grid["o", 0, j + 1], grid["i", 0, j + 1], grid["i", 0, j], grid["o", 0, j])
            f(grid["o", nu, j], grid["i", nu, j], grid["i", nu, j + 1], grid["o", nu, j + 1])
        vs = [grid[key] for key in grid]
        Rm = Matrix.Rotation(rng.uniform(0, 6.3), 3, 'Z') @ Matrix.Rotation(rng.uniform(-0.6, 0.6), 3, 'Y') @ \
            (Matrix.Rotation(math.pi, 3, 'Y') if rng.random() < 0.5 else Matrix.Identity(3))
        if flat:                                                     # laid out on a surface: resting, not heaped
            Rm = Matrix.Rotation(rng.uniform(0, 6.3), 3, 'Z') @ (Matrix.Rotation(math.pi, 3, 'Y') if rng.random() < 0.5 else Matrix.Identity(3))
            pts = [Rm @ v.co for v in vs]; zmin = min(p_.z for p_ in pts)
            for v, p_ in zip(vs, pts):
                v.co = p_ + Vector((x, y, cz - zmin + 0.0005))
            continue
        h = (radius - r) * 0.45 * rng.uniform(0.3, 1.0)
        for v in vs:
            v.co = Rm @ v.co + Vector((x, y, cz + h + R * 0.1))       # half bedded in the fill
    me = bpy.data.meshes.new("cremated"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("cremated", me); bpy.context.scene.collection.objects.link(o); me.materials.append(_calcined())
    bmesh_ok = me.polygons
    for pg in me.polygons:
        pg.use_smooth = True
    bv = o.modifiers.new("b", "BEVEL"); bv.width = 0.0005; bv.segments = 1
    bm = bmesh.new()
    for k in range(charcoal):
        a = rng.uniform(0, 6.283); r = radius * 1.1 * math.sqrt(rng.random())
        s = rng.uniform(0.004, 0.012)
        vs = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=s)['verts']
        for v in vs:
            v.co = Vector((v.co.x * rng.uniform(0.8, 1.6), v.co.y, v.co.z * 0.6)) + Vector((cx + r * math.cos(a), cy + r * math.sin(a), cz + s * 0.3))
    me2 = bpy.data.meshes.new("charcoal"); bm.to_mesh(me2); bm.free()
    o2 = bpy.data.objects.new("charcoal", me2); bpy.context.scene.collection.objects.link(o2)
    me2.materials.append(_plain("charcoal", (0.015, 0.014, 0.013), 0.55))
    return o


def pyre(c, rng_seed=3):
    """A funeral pyre: a crib of split logs, a wrapped body on top, burning: flames, embers glow, volumetric smoke."""
    rng = random.Random(rng_seed)
    wood = bpy.data.materials.get("pyrewood") or ph.texture("bark_brown_02", scale=4.0, name="pyrewood", tint=(0.5, 0.42, 0.35))
    cx, cy, cz = c
    for layer in range(6):
        for k in range(5):
            off = (k - 2) * 0.3
            if layer % 2 == 0:
                loc = (cx + off, cy, cz + 0.08 + layer * 0.15); rot = (0, math.pi / 2, rng.uniform(-0.1, 0.1))
            else:
                loc = (cx, cy + off, cz + 0.08 + layer * 0.15); rot = (math.pi / 2, 0, rng.uniform(-0.1, 0.1))
            bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=1.6, location=loc); lg = bpy.context.active_object
            lg.rotation_euler = rot; lg.data.materials.append(wood); lg.name = "log"
    P2.bundle((cx, cy, cz + 1.05), rot=0.3, length=0.95, girth=0.42)
    # flames: tongues of fire in an emissive volume - a cone of turbulent noise, stretched upward, narrowing with height,
    # hottest (yellow) low in the crib, deep orange at the tips, ragged edges
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, cz + 1.25)); fv = bpy.context.active_object
    fv.scale = (1.9, 1.9, 2.5); fv.name = "pyreflame"
    m = bpy.data.materials.new("pyrefire"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; N.remove(N["Principled BSDF"])
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Generated'], sep.inputs[0])
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (2.2, 2.2, 0.7); L.new(tc.outputs['Generated'], mp.inputs['Vector'])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 3.5; nz.inputs['Detail'].default_value = 8; nz.inputs['Roughness'].default_value = 0.6
    nz.inputs['Distortion'].default_value = 2.5; L.new(mp.outputs[0], nz.inputs['Vector'])
    cz_ = N.new("ShaderNodeCombineXYZ"); L.new(sep.outputs['X'], cz_.inputs['X']); L.new(sep.outputs['Y'], cz_.inputs['Y'])
    rx = N.new("ShaderNodeVectorMath"); rx.operation = 'DISTANCE'; rx.inputs[1].default_value = (0.5, 0.5, 0.0); L.new(cz_.outputs[0], rx.inputs[0])
    # allowed radius shrinks with height (a cone of fire): r_max = 0.42 * (1 - z)
    rm = N.new("ShaderNodeMath"); rm.operation = 'MULTIPLY_ADD'; rm.inputs[1].default_value = -0.42; rm.inputs[2].default_value = 0.42; L.new(sep.outputs['Z'], rm.inputs[0])
    rm2 = N.new("ShaderNodeMath"); rm2.operation = 'MAXIMUM'; rm2.inputs[1].default_value = 0.02; L.new(rm.outputs[0], rm2.inputs[0])
    rq = N.new("ShaderNodeMath"); rq.operation = 'DIVIDE'; L.new(rx.outputs['Value'], rq.inputs[0]); L.new(rm2.outputs[0], rq.inputs[1])
    # ragged edge: the noise pushes the boundary in and out
    rn = N.new("ShaderNodeMath"); rn.operation = 'MULTIPLY_ADD'; rn.inputs[1].default_value = 2.2; L.new(nz.outputs['Fac'], rn.inputs[0]); L.new(rq.outputs[0], rn.inputs[2])
    sh_ = N.new("ShaderNodeMapRange"); sh_.inputs['From Min'].default_value = 2.1; sh_.inputs['From Max'].default_value = 1.7; L.new(rn.outputs[0], sh_.inputs['Value'])
    lo_ = N.new("ShaderNodeMapRange"); lo_.inputs['From Min'].default_value = 0.0; lo_.inputs['From Max'].default_value = 0.06; L.new(sep.outputs['Z'], lo_.inputs['Value'])
    tf = N.new("ShaderNodeMath"); tf.operation = 'SUBTRACT'; tf.inputs[0].default_value = 1.0; L.new(sep.outputs['Z'], tf.inputs[1])
    tp = N.new("ShaderNodeMath"); tp.operation = 'POWER'; tp.inputs[1].default_value = 1.5; L.new(tf.outputs[0], tp.inputs[0])
    a0 = N.new("ShaderNodeMath"); a0.operation = 'MULTIPLY'; L.new(sh_.outputs[0], a0.inputs[0]); L.new(tp.outputs[0], a0.inputs[1])
    a1 = N.new("ShaderNodeMath"); a1.operation = 'MULTIPLY'; L.new(a0.outputs[0], a1.inputs[0]); L.new(lo_.outputs[0], a1.inputs[1])
    tmp = N.new("ShaderNodeMapRange"); tmp.inputs['To Min'].default_value = 2100; tmp.inputs['To Max'].default_value = 1150; L.new(sep.outputs['Z'], tmp.inputs['Value'])
    bb = N.new("ShaderNodeBlackbody"); L.new(tmp.outputs[0], bb.inputs['Temperature'])
    em = N.new("ShaderNodeMath"); em.operation = 'MULTIPLY'; em.inputs[1].default_value = 3.0; L.new(a1.outputs[0], em.inputs[0])
    v = N.new("ShaderNodeVolumePrincipled")
    L.new(bb.outputs[0], v.inputs['Emission Color']); L.new(em.outputs[0], v.inputs['Emission Strength'])
    dd = N.new("ShaderNodeMath"); dd.operation = 'MULTIPLY'; dd.inputs[1].default_value = 0.4; L.new(a1.outputs[0], dd.inputs[0]); L.new(dd.outputs[0], v.inputs['Density'])
    v.inputs['Color'].default_value = (0.1, 0.08, 0.07, 1)
    L.new(v.outputs[0], N["Material Output"].inputs['Volume']); fv.data.materials.append(m)
    for k in range(3):
        d = bpy.data.lights.new("pyre", 'POINT'); d.energy = 900; d.color = (1.0, 0.5, 0.18); d.shadow_soft_size = 0.4
        lo = bpy.data.objects.new("pyre", d); bpy.context.scene.collection.objects.link(lo)
        lo.location = (cx + rng.uniform(-0.3, 0.3), cy + rng.uniform(-0.3, 0.3), cz + 0.6 + k * 0.35)
    BR.smoke((cx, cy, cz + 2.9), height=22.0, drift=(0.6, 0.2), r0=0.7, grow=0.5, density=3.0, name="pyresmoke")


# ============================================================================ "This changes the picture..."
def S01():
    """The second grave at dusk, a slow pull up and away: preserved, buried, retrieved, altered, buried again."""
    T, sk = p1.site("dusk", grass_at=None, kit=False, sun_az=205)
    c, _ = sk["B2"].centre()
    return dict(a=((c.x + 0.4, c.y - 0.6, c.z + 1.2), tuple(c)), b=((c.x + 1.2, c.y - 1.8, c.z + 3.2), tuple(c)), lens=35,
                fstop=5.6, focus=tuple(c), cine=dict(exposure=0.35))


def S02():
    """Preserved: the wrapped body on its hurdle in the dim roundhouse, firelight. Slow push."""
    return p3.S30()


def S03():
    """Retrieved: the opened grave at night, two islanders reaching in by torchlight (from behind)."""
    return p3.S31()


def S04():
    """Buried again: at first light they carry the body to the houses."""
    return p3.S34()


def S05():
    """Altered: the head and an arm set apart from the torso on the lab bench - substitutable parts. Lateral slide."""
    L = p1.lab_body(osteo=False)
    cr = B.hero_cranium(healed=True, tone="A")
    co = np.array([v.co for v in cr.data.vertices]); cr.location = (0.95, 0.42, LB.TOP + 0.004 - co[:, 2].min() * 0.97)
    cr.rotation_euler = (0, 0, math.radians(-40))
    p3.lab_part("upperarmR", sex="M", tone="D", x=0.95, y=0.15, yaw=20)
    return dict(a=((0.2, -0.65, LB.TOP + 0.55), (0.4, 0.35, LB.TOP)), b=((0.75, -0.6, LB.TOP + 0.5), (0.9, 0.35, LB.TOP)), lens=35,
                fstop=5.6, focus=(0.9, 0.35, LB.TOP + 0.05), cine=dict(exposure=-0.05))


# ============================================================================ "The team cannot recover every step..."
def S06():
    """The broken knee laid back against the body's leg: they connect. Slow push."""
    return p3.S25()


def S07():
    """The precise moment is uncertain: the composite skeleton in the grave, the light fading. Slow drift."""
    T, sk = p1.site("dusk", grass_at=None, kit=False, sun_az=215)
    s = sk["B2"].part_centre("skull"); c, _ = sk["B2"].centre()
    return dict(a=(tuple(c + Vector((0.9, -0.7, 0.9))), tuple(c)), b=(tuple(c + Vector((0.6, -0.95, 0.8))), tuple(s)), lens=45,
                fstop=2.8, focus=tuple(s), cine=dict(exposure=0.25))


# ============================================================================ "And the knee is part of a much wider pattern."
def S08():
    """A wider pattern: crane up high over the excavation - the house rings, the graves, the knee pit outside."""
    T, sk = p1.site("golden", grass_at=(10, 0), grass_r=30, kit=True, sun_az=200)
    return dict(a=((8, -10, 9), (0, 6, 3)), b=((18, -26, 34), (0, 4, 3)), lens=28, fstop=8.0, focus=(0, 4, 3), cine=dict(exposure=0.1))


# ============================================================================ "Before the roundhouses existed, this ground held a cemetery."
def S09():
    """Before the houses: the open machair at dusk, a funeral pyre burning, two mourners far off (silhouettes)."""
    U.CUT = False
    U.island("dusk", grass_at=(10, -4), grass_r=30, n=820, core=4.0, grass_density=220, sun_az=200)
    c = (6.0, 2.0, float(U.surface(6.0, 2.0)))
    pyre(c)
    import acts as AC
    for i, (dx, dy, hd) in enumerate(((6.2, -8.4, 125), (7.6, -7.6, 130))):
        m = BR.Islander(name=f"Islander{i}") if i == 0 else p2._islander2()
        f = (c[0] + dx, c[1] + dy); zf = float(U.surface(*f))
        st = AC.Stand(m, f, hd, lean=4)
        st.finish(look=(c[0], c[1], c[2] + 1.2 - zf), density=HAIR); G.lift(st, zf)
    return dict(a=((c[0] + 13.5, c[1] - 14.5, c[2] + 1.9), (c[0], c[1], c[2] + 1.4)), b=((c[0] + 12.5, c[1] - 13.5, c[2] + 1.85), (c[0], c[1], c[2] + 1.5)),
                lens=45, fstop=5.6, focus=(c[0] + 6.9, c[1] - 8.0, c[2] + 1.2), cine=dict(exposure=0.25))


def S10():
    """Small quantities of burnt bone into the earth: a little pit with cremated fragments and charcoal. Macro push."""
    U.CUT = False
    U.island("overcast", grass_at=(9.0, 5.0), grass_r=2.5, n=820, core=3.0, focus=(6, 2), grass_density=260)
    z = float(U.surface(6, 2))
    # the little pit: dark charcoal-stained fill, lumpy, its edge feathered into the sand
    bpy.ops.mesh.primitive_circle_add(vertices=64, radius=0.24, fill_type='NGON', location=(6, 2, z + 0.004)); pt = bpy.context.active_object
    pt.data.materials.append(ph.texture("brown_mud_02", scale=6.0, name="pitfill", tint=(0.32, 0.26, 0.2))); pt.name = "pitfloor"
    sb = pt.modifiers.new("s", "SUBSURF"); sb.subdivision_type = 'SIMPLE'; sb.levels = 4; sb.render_levels = 4
    dp = pt.modifiers.new("d", "DISPLACE"); dt = bpy.data.textures.new("pitlump", "CLOUDS"); dt.noise_scale = 0.03; dp.texture = dt; dp.strength = 0.008
    cremation((6, 2, z + 0.004), radius=0.15, n=200, charcoal=110, flat=True)
    t = Vector((6, 2, z + 0.01))
    return dict(a=(tuple(t + Vector((0.18, -0.3, 0.3))), tuple(t)), b=(tuple(t + Vector((0.1, -0.2, 0.2))), tuple(t)), lens=50,
                fstop=4.0, focus=tuple(t), cine=dict(exposure=0.1))


def S11():
    """Cremated bone in the lab: white, grey and black fragments, crazed and warped by fire, on the velvet. Slider."""
    A = LB.room(window_light=0.3, lamp=True, lamp_at=(0.3, 0.62), lamp_target=(0.0, 0.36), lamp_energy=22)
    LB.velvet(-0.6, 0.7, 0.0, 0.78, LB.TOP)
    cremation((0.0, 0.36, LB.TOP + 0.001), radius=0.1, n=80, charcoal=0, flat=True)
    t = Vector((0.0, 0.36, LB.TOP + 0.01))
    return dict(a=(tuple(t + Vector((-0.18, -0.22, 0.16))), tuple(t)), b=(tuple(t + Vector((-0.05, -0.26, 0.15))), tuple(t)), lens=60,
                fstop=5.6, focus=tuple(t), cine=dict(exposure=-0.05))


# ============================================================================ "Later, someone dug down into those graves."
def S12():
    """Night: digging down into the old graves by torchlight (from behind)."""
    return p3.S31()


# ============================================================================ "In one case, a house had been built with its hearth directly over a child's cremation..."
def S13():
    """Inside the roundhouse: the hearth burning on the floor. Low push to the fire."""
    U.CUT = False
    R = BR.interior(fire=1.0, door_sun=0.2)
    hx, hy = R["hearth"]
    return dict(a=((hx - 2.4, hy - 1.2, 0.6), (hx, hy, 0.2)), b=((hx - 1.6, hy - 0.8, 0.45), (hx, hy, 0.2)), lens=35,
                fstop=2.8, focus=(hx, hy, 0.2), cine=dict(exposure=0.2), hand_ok=("floor",))


def S14():
    """Beneath it: the excavated hearth stones in the trench, and under them a small pit of cremated bone (section).
    Crane down to it."""
    T, sk = p1.site("golden", grass_at=None, kit=False, burials=False, sun_az=200)
    hx, hy = U.HOUSES[1][0] + 0.4, U.HOUSES[1][1]              # the middle house's hearth (built by G.houses)
    z = G.H(hx, hy)
    cremation((hx + 0.55, hy - 0.3, z + 0.005), radius=0.1, n=80)
    bpy.ops.mesh.primitive_circle_add(vertices=40, radius=0.16, fill_type='NGON', location=(hx + 0.55, hy - 0.3, z + 0.003)); pt = bpy.context.active_object
    pt.data.materials.append(_plain("pitdark3", (0.07, 0.05, 0.035), 0.95)); pt.name = "pitfloor"
    t = Vector((hx + 0.3, hy - 0.15, z))
    return dict(a=(tuple(t + Vector((0.9, -1.4, 1.6))), tuple(t)), b=(tuple(t + Vector((0.4, -0.7, 0.8))), tuple(t)), lens=40,
                fstop=4.0, focus=tuple(t), cine=dict(exposure=0.1))


def S15():
    """After the house came down: a pit dug through its old floor to reach the remains - the cut through the floor
    layers in the section, the cremation at its base. Push."""
    return S14()


# ============================================================================ "People were returning to the dead across generations."
def S16():
    """Bones within the walls: a human bone fragment wedged among the stones of a house wall. Slow push."""
    T, sk = p1.site("golden", grass_at=None, kit=False, burials=False, sun_az=200)
    hx, hy, r = U.HOUSES[1]
    a = math.radians(-60); wx, wy = hx + (r - 0.2) * math.cos(a), hy + (r - 0.2) * math.sin(a)
    z = G.H(wx, wy)
    fe, W = None, None
    sk2 = B.Skeleton("M", "C", name="WallBone")
    for s_ in list(sk2.parts):
        if s_ != "forearmL":
            sk2.remove(s_)
    o = sk2.parts["forearmL"]
    bpy.context.view_layer.update()
    Wv = np.array([o.matrix_world @ v.co for v in o.data.vertices]); c = Wv.mean(0)
    sk2.root.location += Vector((wx - c[0], wy - c[1], z + 0.22 - c[2]))
    sk2.root.rotation_euler = (0, math.radians(80), a + math.pi / 2)
    p2._bone_detail(o)
    t = Vector((wx, wy, z + 0.22))
    return dict(a=(tuple(t + Vector((0.55 * math.cos(a), 0.55 * math.sin(a), 0.25))), tuple(t)),
                b=(tuple(t + Vector((0.4 * math.cos(a), 0.4 * math.sin(a), 0.2))), tuple(t)), lens=45, fstop=4.0, focus=tuple(t),
                cine=dict(exposure=0.1))


def S17():
    """Under the floors: the house floor in the trench, scattered human bone in its make-up. Low slider."""
    T, sk = p1.site("golden", grass_at=None, kit=False, burials=True, sun_az=200)
    rng = random.Random(17)
    for k in range(11):
        x, y = -1.5 + rng.uniform(-0.6, 0.6), -0.4 + rng.uniform(-0.45, 0.45)      # clear of the hearth kerb
        z = G.H(x, y)
        sk2 = B.Skeleton("M", "C", name=f"Scatter{k}")
        keep = rng.choice(["forearmL", "patellaL", "femurL", "shankR", "mandible", "upperarmR", "forearmR"])
        for s_ in list(sk2.parts):
            if s_ != keep:
                sk2.remove(s_)
        o = sk2.parts[keep]; bpy.context.view_layer.update()
        Wv = np.array([o.matrix_world @ v.co for v in o.data.vertices]); c = Wv.mean(0)
        sk2.root.rotation_euler = (math.radians(90), 0, rng.uniform(0, 6.3)); bpy.context.view_layer.update()
        Wv = np.array([o.matrix_world @ v.co for v in o.data.vertices]); c = Wv.mean(0)
        sk2.root.location += Vector((x - c[0], y - c[1], z - 0.004 - Wv[:, 2].min()))
    zc = G.H(-1.5, -0.4)
    return dict(a=((-2.6, -1.8, zc + 0.7), (-1.5, -0.4, zc)), b=((-2.1, -2.0, zc + 0.65), (-1.2, -0.3, zc)), lens=32,
                fstop=5.6, focus=(-1.5, -0.4, zc), cine=dict(exposure=0.1))


# ============================================================================ "The two assembled bodies belong to a place..."
def S18():
    """A place of the returning dead: the roundhouses at dusk, smoke rising, the burial ground beneath. Slow pull back."""
    U.CUT = False
    U.island("dusk", grass_at=(0, 0), grass_r=40, n=820, core=4.0, grass_density=220)
    BR.village(smoke_on=True)
    return dict(a=((24, -18, 6), (0, 0, 4)), b=((40, -30, 12), (0, 1, 4)), lens=32, cine=dict(exposure=0.35))


VO = [l.strip() for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "vo", "MUMMY_P4_VO.txt"),
                               encoding="utf-8").read().split("\n") if l.strip()]

PLAN = [  # shot, VO paragraph (1-based), seconds, description
    ("S01", 1, 4.5, "The second grave at dusk, pulling away"),
    ("S02", 1, 3.0, "Preserved: the wrapped body in the roundhouse"),
    ("S03", 1, 3.0, "Retrieved: the opened grave by torchlight"),
    ("S04", 1, 3.0, "Buried again: carried to the houses at first light"),
    ("S05", 1, 5.0, "Head and arm set apart from the torso on the lab bench"),
    ("S06", 2, 5.0, "The broken knee connected to the body's leg"),
    ("S07", 2, 5.5, "The composite skeleton in the grave, light fading"),
    ("S08", 3, 4.0, "Crane up over the whole excavation: a wider pattern"),
    ("S09", 4, 6.0, "Before the houses: a funeral pyre at dusk, mourners far off"),
    ("S10", 4, 4.5, "A small pit of cremated bone and charcoal"),
    ("S11", 4, 4.0, "Cremated bone fragments in the lab"),
    ("S12", 5, 3.5, "Digging down into the old graves by night"),
    ("S13", 6, 4.5, "The hearth burning on the house floor"),
    ("S14", 6, 5.0, "Beneath it: the hearth stones and a child's cremation pit"),
    ("S15", 6, 4.5, "A pit dug through the old floor to reach the remains"),
    ("S16", 7, 5.0, "A human bone wedged among the stones of a house wall"),
    ("S17", 7, 5.0, "Scattered human bone in a house floor"),
    ("S18", 8, 6.5, "The roundhouses at dusk: a place where the dead came back"),
]
SHOTS = {sid: dict(fn=globals()[sid], dur=d, vo=VO[min(ln, len(VO)) - 1], line=ln, desc=desc) for sid, ln, d, desc in PLAN}
