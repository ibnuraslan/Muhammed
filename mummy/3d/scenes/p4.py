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
def _calcined(name="calcined2"):
    """Cremated bone: each fragment its own colour (attribute 'frag') from chalky white through blue-grey to near
    black (less completely burnt), with a fine net of checking cracks and a dry, matte, slightly sugary surface."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    at = N.new("ShaderNodeAttribute"); at.attribute_name = "frag"
    rp = N.new("ShaderNodeValToRGB"); el = rp.color_ramp.elements
    el[0].position = 0.0; el[0].color = (0.04, 0.035, 0.03, 1)
    for pos, c in ((0.14, (0.16, 0.16, 0.17)), (0.3, (0.38, 0.42, 0.47)), (0.5, (0.52, 0.53, 0.54)), (0.7, (0.66, 0.64, 0.6))):
        e = el.new(pos); e.color = (*c, 1)
    el[-1].position = 1.0; el[-1].color = (0.74, 0.72, 0.67, 1)
    L.new(at.outputs['Fac'], rp.inputs['Fac'])
    tc = N.new("ShaderNodeTexCoord")
    mo = N.new("ShaderNodeTexNoise"); mo.inputs['Scale'].default_value = 140; mo.inputs['Detail'].default_value = 6; L.new(tc.outputs['Object'], mo.inputs['Vector'])
    mm = N.new("ShaderNodeMapRange"); mm.inputs['To Min'].default_value = 0.78; mm.inputs['To Max'].default_value = 1.08; L.new(mo.outputs['Fac'], mm.inputs['Value'])
    mx0 = N.new("ShaderNodeMix"); mx0.data_type = 'RGBA'; mx0.blend_type = 'MULTIPLY'; mx0.inputs['Factor'].default_value = 1.0
    L.new(rp.outputs['Color'], mx0.inputs[6]); cc0 = N.new("ShaderNodeCombineXYZ")
    for k in range(3):
        L.new(mm.outputs[0], cc0.inputs[k])
    L.new(cc0.outputs[0], mx0.inputs[7])
    # checking: a net of thin dark cracks, 2-4 mm cells, plus a finer crazing
    cr = N.new("ShaderNodeTexVoronoi"); cr.feature = 'DISTANCE_TO_EDGE'; cr.inputs['Scale'].default_value = 200; L.new(tc.outputs['Object'], cr.inputs['Vector'])
    cm = N.new("ShaderNodeMapRange"); cm.inputs['From Min'].default_value = 0.0; cm.inputs['From Max'].default_value = 0.03
    cm.inputs['To Min'].default_value = 0.08; cm.inputs['To Max'].default_value = 1.0; L.new(cr.outputs['Distance'], cm.inputs['Value'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    L.new(mx0.outputs[2], mx.inputs[6]); cc = N.new("ShaderNodeCombineXYZ")
    for k in range(3):
        L.new(cm.outputs[0], cc.inputs[k])
    L.new(cc.outputs[0], mx.inputs[7]); L.new(mx.outputs[2], p.inputs['Base Color'])
    gr = N.new("ShaderNodeTexNoise"); gr.inputs['Scale'].default_value = 900; L.new(tc.outputs['Object'], gr.inputs['Vector'])
    hh = N.new("ShaderNodeMath"); hh.operation = 'MULTIPLY_ADD'; hh.inputs[1].default_value = 0.3; L.new(gr.outputs['Fac'], hh.inputs[0]); L.new(cm.outputs[0], hh.inputs[2])
    bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.8; bp.inputs['Distance'].default_value = 0.0006
    L.new(hh.outputs[0], bp.inputs['Height']); L.new(bp.outputs['Normal'], p.inputs['Normal'])
    p.inputs['Roughness'].default_value = 0.93
    return m


def _crem_pit(c, r=0.24, n=200, charcoal=110):
    """A small pit of cremated bone: dark charcoal-stained fill with a feathered irregular edge, the burnt fragments
    and charcoal lying in it."""
    x, y, z = c
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=60, size=2.2 * r, location=(x, y, z + 0.012)); pt = bpy.context.active_object
    bm_ = bmesh.new(); bm_.from_mesh(pt.data)
    bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if v.co.xy.length > r * (1 + 0.08 * math.sin(7 * math.atan2(v.co.y, v.co.x)))], context='VERTS')
    for v in bm_.verts:                       # the rim dips under the surrounding ground: a soft, irregular pit edge
        t_ = v.co.xy.length / r
        if t_ > 0.75:
            v.co.z -= 0.03 * (t_ - 0.75) / 0.25
    bm_.to_mesh(pt.data); bm_.free()
    pt.data.materials.append(bpy.data.materials.get("pitfill") or ph.texture("brown_mud_02", scale=6.0, name="pitfill", tint=(0.34, 0.27, 0.2)))
    pt.name = "pitfloor"
    dp = pt.modifiers.new("d", "DISPLACE"); dt = bpy.data.textures.new("pitlump", "CLOUDS"); dt.noise_scale = 0.03; dp.texture = dt; dp.strength = 0.005
    cremation((x, y, z + 0.012), radius=r * 0.7, n=n, charcoal=charcoal * 3, bury=0.55)
    return pt


def cremation(center, radius=0.12, n=90, seed=1, charcoal=40, flat=False, rect=None, size=(0.004, 0.016), bury=0.45, burnt=(0.0, 1.0)):
    """Cremated bone: small irregular, warped fragments - angular chunks of compact bone and curved slivers of shaft
    wall - each its own colour (white / blue-grey / black), with charcoal. In a pit they lie partly buried in the fill
    (bury = fraction of their height below the surface); flat=True lays them out resting on a surface (lab).
    rect=(w, d): spread over a rectangle instead of a disc."""
    rng = random.Random(seed)
    cx, cy, cz = center
    bm = bmesh.new()
    fl = bm.verts.layers.float.new("frag")
    for k in range(n):
        if rect:
            x, y = cx + rng.uniform(-rect[0] / 2, rect[0] / 2), cy + rng.uniform(-rect[1] / 2, rect[1] / 2); h = 0.0
        else:
            a = rng.uniform(0, 6.283); r = radius * math.sqrt(rng.random())
            x, y = cx + r * math.cos(a), cy + r * math.sin(a); h = 0.0
        sz = rng.uniform(*size) * (1.6 if rng.random() > 0.9 else 1.0)
        if rng.random() < 0.6:
            # an angular chunk: a jittered, flattened, slightly cupped polyhedron
            vs = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.5)['verts']
            ax, ay, az = sz * rng.uniform(0.8, 1.6), sz * rng.uniform(0.6, 1.0), sz * rng.uniform(0.3, 0.6)
            cup = rng.uniform(-0.6, 0.6)
            for v in vs:
                q = v.co * rng.uniform(0.75, 1.2)
                v.co = Vector((q.x * ax, q.y * ay, q.z * az + cup * az * (q.x * q.x + q.y * q.y)))
        else:
            # a curved sliver of shaft wall, warped and twisted by the fire, jagged ends
            vs = []
            L_ = sz * rng.uniform(1.2, 2.2); R = sz * rng.uniform(0.5, 0.9); t = R * rng.uniform(0.22, 0.35)
            span = rng.uniform(0.7, 2.0); nu, nv = 4, 3; twist = rng.uniform(-0.6, 0.6); bend = rng.uniform(-10, 10)
            grid = {}
            for side, rr in (("o", R), ("i", R - t)):
                for i in range(nu + 1):
                    for j in range(nv + 1):
                        v = -L_ / 2 + L_ * j / nv + (rng.uniform(-0.3, 0.3) * L_ / nv if j in (0, nv) else 0)
                        th = -span / 2 + span * i / nu + twist * v / L_
                        rj = rr * (1 + 0.1 * rng.uniform(-1, 1))
                        grid[side, i, j] = bm.verts.new(Vector((rj * math.cos(th), v, rj * math.sin(th) - R + bend * v * v)))
            def f(*q):
                try:
                    bm.faces.new(q)
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
            vs = list(grid.values())
        burn = rng.uniform(*burnt)
        Rm = Matrix.Rotation(rng.uniform(0, 6.3), 3, 'Z') @ Matrix.Rotation(rng.uniform(-0.5, 0.5), 3, 'Y') @ \
            (Matrix.Rotation(math.pi, 3, 'X') if rng.random() < 0.5 else Matrix.Identity(3))
        if flat:
            Rm = Matrix.Rotation(rng.uniform(0, 6.3), 3, 'Z') @ (Matrix.Rotation(math.pi, 3, 'X') if rng.random() < 0.5 else Matrix.Identity(3))
        pts = [Rm @ v.co for v in vs]; zmin = min(p_.z for p_ in pts); zmax = max(p_.z for p_ in pts)
        dz = cz - zmin + 0.0004 - (0.0 if flat else rng.uniform(0.2, 1.0) * bury * (zmax - zmin))
        for v, p_ in zip(vs, pts):
            v.co = p_ + Vector((x, y, dz)); v[fl] = burn
    me = bpy.data.meshes.new("cremated"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("cremated", me); bpy.context.scene.collection.objects.link(o); me.materials.append(_calcined())
    for pg in me.polygons:
        pg.use_smooth = False
    if charcoal:
        bm = bmesh.new()
        for k in range(charcoal):
            if rect:
                x, y = cx + rng.uniform(-rect[0] / 2, rect[0] / 2), cy + rng.uniform(-rect[1] / 2, rect[1] / 2)
            else:
                a = rng.uniform(0, 6.283); r = radius * 1.15 * math.sqrt(rng.random())
                x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            s_ = rng.uniform(0.0015, 0.006)
            vs = bmesh.ops.create_cube(bm, size=1.0)['verts']
            Rm = Matrix.Rotation(rng.uniform(0, 6.3), 3, 'Z') @ Matrix.Rotation(rng.uniform(-0.6, 0.6), 3, 'X')
            for v in vs:
                q = Vector((v.co.x * s_ * rng.uniform(1.0, 2.2), v.co.y * s_ * rng.uniform(0.8, 1.4), v.co.z * s_ * rng.uniform(0.6, 1.0)))
                v.co = Rm @ q + Vector((x, y, cz + s_ * rng.uniform(-0.3, 0.2)))
        me2 = bpy.data.meshes.new("charcoal"); bm.to_mesh(me2); bm.free()
        o2 = bpy.data.objects.new("charcoal", me2); bpy.context.scene.collection.objects.link(o2)
        cm_ = _plain("charcoal", (0.012, 0.011, 0.01), 0.45)
        me2.materials.append(cm_)
    return o


def pyre(c, rng_seed=3):
    """A funeral pyre: a tall crib of split logs, the wrapped body on top, fully alight - tall flame tongues, a bed of
    glowing embers and coals, sparks, a thick smoke column, strong firelight."""
    rng = random.Random(rng_seed)
    wood = bpy.data.materials.get("pyrewood") or ph.texture("bark_brown_02", scale=4.0, name="pyrewood", tint=(0.5, 0.42, 0.35))
    char = _plain("charlog", (0.02, 0.016, 0.014), 0.7)
    cx, cy, cz = c
    for layer in range(9):
        for k in range(6):
            off = (k - 2.5) * 0.38 + rng.uniform(-0.04, 0.04)
            z = cz + 0.1 + layer * 0.17
            if layer % 2 == 0:
                loc = (cx + off, cy, z); rot = (0, math.pi / 2, rng.uniform(-0.12, 0.12))
            else:
                loc = (cx, cy + off, z); rot = (math.pi / 2, 0, rng.uniform(-0.12, 0.12))
            bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=rng.uniform(0.07, 0.1), depth=rng.uniform(2.2, 2.6), location=loc); lg = bpy.context.active_object
            lg.rotation_euler = rot; lg.data.materials.append(char if layer < 4 or rng.random() < 0.4 else wood); lg.name = "log"
            dd = lg.modifiers.new("d", "DISPLACE"); tt = bpy.data.textures.get("logknots") or bpy.data.textures.new("logknots", "CLOUDS")
            tt.noise_scale = 0.12; dd.texture = tt; dd.strength = 0.02
    P2.bundle((cx, cy, cz + 1.75), rot=0.3, length=0.95, girth=0.42)
    tongues = BR.flames((cx, cy, cz), spread=1.0, n=48, top_z=1.55, low_z=(0.2, 1.4), top_share=0.55, h_top=(1.6, 3.2), h_low=(0.6, 1.4),
                        wid=(0.24, 0.42), strength=0.3, seed=rng_seed)
    if tongues:                         # a deeper, more saturated ramp so the tongues stay orange instead of blooming to gold
        fm = tongues[0].data.materials[0].copy(); fm.name = "pyretongue"
        for n_ in fm.node_tree.nodes:
            if n_.type == 'VALTORGB':
                el = n_.color_ramp.elements
                el[0].color = (1.0, 0.42, 0.06, 1); el[-1].color = (0.5, 0.07, 0.01, 1)
                for e in list(el)[1:-1]:
                    e.color = (0.95, 0.22, 0.02, 1)
        for t_ in tongues:
            t_.data.materials[0] = fm
    # the ember bed and coals round the base, and sparks rising in the hot air
    emb = _plain("embers", (0.02, 0.01, 0.005), 0.8)
    pr = emb.node_tree.nodes["Principled BSDF"]; pr.inputs['Emission Color'].default_value = (1.0, 0.3, 0.05, 1); pr.inputs['Emission Strength'].default_value = 8.0
    bm = bmesh.new()
    for k in range(260):
        a = rng.uniform(0, 6.283); r = rng.uniform(0.2, 1.7)
        s_ = rng.uniform(0.02, 0.06)
        vs = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=s_)['verts']
        for v in vs:
            v.co = Vector((v.co.x, v.co.y, v.co.z * 0.6)) + Vector((cx + r * math.cos(a), cy + r * math.sin(a), cz + 0.01))
    me = bpy.data.meshes.new("embers"); bm.to_mesh(me); bm.free()
    eo = bpy.data.objects.new("embers", me); bpy.context.scene.collection.objects.link(eo); me.materials.append(emb)
    spk = _plain("sparks", (0, 0, 0), 0.5); sp = spk.node_tree.nodes["Principled BSDF"]
    sp.inputs['Emission Color'].default_value = (1.0, 0.55, 0.15, 1); sp.inputs['Emission Strength'].default_value = 40.0
    bm = bmesh.new()
    for k in range(160):
        h = rng.uniform(2.0, 7.0)
        x = cx + rng.gauss(0, 0.5) + 0.12 * h; y = cy + rng.gauss(0, 0.5) + 0.04 * h
        vs = bmesh.ops.create_icosphere(bm, subdivisions=0, radius=rng.uniform(0.008, 0.018))['verts']
        for v in vs:
            v.co = v.co + Vector((x, y, cz + h))
    me = bpy.data.meshes.new("sparks"); bm.to_mesh(me); bm.free()
    so = bpy.data.objects.new("sparks", me); bpy.context.scene.collection.objects.link(so); me.materials.append(spk); so.visible_shadow = False
    for k in range(5):
        d = bpy.data.lights.new("pyre", 'POINT'); d.energy = 1100; d.color = (1.0, 0.5, 0.18); d.shadow_soft_size = 0.6
        lo = bpy.data.objects.new("pyre", d); bpy.context.scene.collection.objects.link(lo)
        lo.location = (cx + rng.uniform(-0.6, 0.6), cy + rng.uniform(-0.6, 0.6), cz + 0.8 + k * 0.45)
    BR.smoke((cx, cy, cz + 4.6), height=30.0, drift=(0.7, 0.2), r0=1.3, grow=0.6, density=4.0, name="pyresmoke")


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
    cr = B.hero_cranium(healed=False, tone="D"); p3._old_bone(cr, stain=1.0)   # the same older, darker head as P3 S05
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
    p1.site("dusk", grass_at=(4, 0), grass_r=55, focus=(0, 0), core=6.0, n=900, kit=True, burials=True, sun_az=230, grass_density=260)
    U.cloud_shadows((0, 0), cover=0.45, seed=7)          # the approved P2 S28 dig-aerial look
    return dict(a=((38, -52, 30), (-4, 6, 0.0)), b=((95, -150, 85), (-70, 40, 0)), lens=26, cine=dict(exposure=0.3))


# ============================================================================ "Before the roundhouses existed, this ground held a cemetery."
def S09():
    """Before the houses: the open machair at dusk, a great funeral pyre burning, mourners standing back from it."""
    U.CUT = False
    U.island("dusk", grass_at=(10, -4), grass_r=30, n=820, core=4.0, grass_density=220, sun_az=200)
    c = (6.0, 2.0, float(U.surface(6.0, 2.0)))
    pyre(c)
    import acts as AC
    # five mourners on the near side, spread out in a loose arc 9-12 m from the fire, backs to us
    spots = ((5.8, -9.0, 120), (8.2, -7.4, 128), (3.2, -10.6, 112), (10.4, -5.0, 136), (1.2, -11.8, 105))
    for k, (dx, dy, hd) in enumerate(spots):
        m = BR.islander_cropped(k % 2, name=f"Mourner{k}", var=k)
        f = (c[0] + dx, c[1] + dy); zf = float(U.surface(*f))
        hd = math.degrees(math.atan2(-dy, -dx)) + (k - 2) * 3          # facing the fire
        st = AC.Stand(m, f, hd, lean=4 + 3 * (k % 2), weight="L" if k % 2 else "R")
        st.head_to((c[0], c[1], c[2] + 1.6 - zf), share=0.6)
        st.finish(look=(c[0], c[1], c[2] + 1.6 - zf), density=1.0); G.lift(st, zf)
    return dict(a=((c[0] + 15.5, c[1] - 17.5, c[2] + 2.0), (c[0], c[1], c[2] + 2.0)), b=((c[0] + 14.0, c[1] - 16.0, c[2] + 1.9), (c[0], c[1], c[2] + 2.0)),
                lens=40, fstop=5.6, focus=(c[0] + 6.0, c[1] - 9.0, c[2] + 1.2), cine=dict(exposure=0.2))


def S10():
    """Small quantities of burnt bone into the earth: a little pit with cremated fragments and charcoal. Macro push."""
    U.CUT = False
    U.island("overcast", grass_at=(9.0, 5.0), grass_r=2.5, n=820, core=3.0, focus=(6, 2), grass_density=260)
    z = float(U.surface(6, 2))
    _crem_pit((6, 2, z), 0.24)
    t = Vector((6, 2, z + 0.01))
    return dict(a=(tuple(t + Vector((0.18, -0.3, 0.3))), tuple(t)), b=(tuple(t + Vector((0.1, -0.2, 0.2))), tuple(t)), lens=50,
                fstop=4.0, focus=tuple(t), cine=dict(exposure=-0.45))


def S11():
    """Cremated bone in the lab: a shallow steel tray divided into compartments, the fragments sorted by size - large
    pieces of shaft and skull vault, medium chunks, small crumbs - white, blue-grey and black, crazed by the fire."""
    A = LB.room(window_light=0.3, lamp=True, lamp_at=(0.3, 0.62), lamp_target=(0.0, 0.36), lamp_energy=22)
    LB.velvet(-0.6, 0.7, 0.0, 0.78, LB.TOP)
    steel = P2._brushed("traysteel", (0.6, 0.61, 0.62), 0.35)
    tx, ty, tz = 0.0, 0.36, LB.TOP + 0.002
    W_, D_, H_ = 0.36, 0.24, 0.022
    bpy.ops.mesh.primitive_cube_add(size=1, location=(tx, ty, tz + 0.0015)); b_ = bpy.context.active_object
    b_.scale = (W_, D_, 0.003); b_.data.materials.append(steel); b_.name = "tray"
    walls = [((tx, ty - D_ / 2, tz + H_ / 2), (W_, 0.003, H_)), ((tx, ty + D_ / 2, tz + H_ / 2), (W_, 0.003, H_)),
             ((tx - W_ / 2, ty, tz + H_ / 2), (0.003, D_, H_)), ((tx + W_ / 2, ty, tz + H_ / 2), (0.003, D_, H_)),
             ((tx - W_ / 6, ty, tz + H_ / 2), (0.002, D_, H_ * 0.8)), ((tx + W_ / 6, ty, tz + H_ / 2), (0.002, D_, H_ * 0.8)),
             ((tx, ty, tz + H_ / 2), (W_, 0.002, H_ * 0.8))]
    for loc, sc in walls:
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc); w_ = bpy.context.active_object; w_.scale = sc
        w_.data.materials.append(steel); w_.name = "tray"
    # six compartments: sizes large -> small along x, the near row more burnt (blue-grey/black), the far row white
    cw, cd = W_ / 3 - 0.012, D_ / 2 - 0.012
    for col, (lo, hi, n) in enumerate(((0.016, 0.028, 16), (0.008, 0.015, 40), (0.003, 0.007, 120))):
        for row, burnt in enumerate(((0.0, 0.4), (0.2, 0.85))):          # more blue-grey and black, fewer white
            cx_ = tx - W_ / 3 + col * W_ / 3; cy_ = ty - D_ / 4 + row * D_ / 2
            cremation((cx_, cy_, tz + 0.003), n=n, seed=10 * col + row, charcoal=0, flat=True, rect=(cw, cd), size=(lo, hi), burnt=burnt)
    t = Vector((tx, ty, tz + 0.01))
    _spot((tx - 0.5, ty - 0.35, tz + 0.45), tuple(t), 60, size=0.08, spot=40)
    return dict(a=(tuple(t + Vector((-0.2, -0.32, 0.26))), tuple(t)), b=(tuple(t + Vector((0.05, -0.34, 0.25))), tuple(t)), lens=50,
                fstop=5.6, focus=tuple(t), cine=dict(exposure=-0.35))


# ============================================================================ "Later, someone dug down into those graves."
def S12():
    """Night: the old grave dug open by torchlight - sand walls, the floor of the pit (no figures; S03 has them)."""
    return p3.S33()


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
    G.SCANNED = True                                          # scanned drystone: angular, lichened faces
    T, sk = p1.site("golden", grass_at=None, kit=False, burials=False, sun_az=200)
    hx, hy = U.HOUSES[1][0] + 0.4, U.HOUSES[1][1]              # the middle house's hearth (built by G.houses)
    z = G.H(hx, hy)
    _crem_pit((hx + 0.62, hy - 0.42, z), 0.2, n=150, charcoal=80)
    t = Vector((hx + 0.45, hy - 0.32, z))
    return dict(a=(tuple(t + Vector((0.9, -1.4, 1.6))), tuple(t)), b=(tuple(t + Vector((0.4, -0.7, 0.8))), tuple(t)), lens=40,
                fstop=4.0, focus=tuple(t), cine=dict(exposure=0.1))


def S15():
    """Close on the little cremation pit beside the hearth kerb: burnt bone and charcoal in its dark fill. Push in."""
    d = S14()
    hx, hy = U.HOUSES[1][0] + 0.4, U.HOUSES[1][1]
    t = Vector((hx + 0.62, hy - 0.42, G.H(hx + 0.62, hy - 0.42)))
    return dict(a=(tuple(t + Vector((0.25, -0.45, 0.42))), tuple(t)), b=(tuple(t + Vector((0.14, -0.28, 0.28))), tuple(t)), lens=45,
                fstop=5.6, focus=tuple(t), cine=dict(exposure=0.35))


# ============================================================================ "People were returning to the dead across generations."
def S16():
    """Bones within the walls: a human forearm bone wedged between two courses of the house's stone revetment, seen
    from the house floor. Slow push."""
    G.SCANNED = True                                          # scanned drystone: angular, lichened faces
    T, sk = p1.site("golden", grass_at=None, kit=False, burials=False, sun_az=200)
    hx, hy, r = U.HOUSES[1]
    a = math.radians(-60)
    zf = G.H(hx + (r - 0.25) * math.cos(a), hy + (r - 0.25) * math.sin(a))
    rr = r - 0.07                                            # the inner face of the wall stones
    wx, wy = hx + rr * math.cos(a), hy + rr * math.sin(a)
    sk2 = B.Skeleton("M", "C", name="WallBone")
    for s_ in list(sk2.parts):
        if s_ != "forearmL":
            sk2.remove(s_)
    o = sk2.parts["forearmL"]
    sk2.root.rotation_euler = (0, math.radians(90), a + math.pi / 2)        # lying along the course, in the joint
    bpy.context.view_layer.update()
    Wv = np.array([o.matrix_world @ v.co for v in o.data.vertices]); c = Wv.mean(0)
    zj = zf + 0.08 + 0.14 * 1.5                               # the bed joint between the 2nd and 3rd course
    sk2.root.location += Vector((wx - c[0], wy - c[1], zj - c[2]))
    p3._knee_mats(o, sand=0.6)
    t = Vector((wx, wy, zj))
    inw = Vector((-math.cos(a), -math.sin(a), 0))
    # low evening sun raking across the wall face from the house floor (motivated: the open trench, sun low in the west)
    _spot(tuple(t + inw * 1.6 + Vector((-0.9, 0.4, 0.5))), tuple(t), 260, size=0.15, color=(1.0, 0.82, 0.62), spot=35)
    return dict(a=(tuple(t + inw * 0.75 + Vector((0.15, 0, 0.12))), tuple(t)),
                b=(tuple(t + inw * 0.5 + Vector((0.08, 0, 0.08))), tuple(t)), lens=45, fstop=8.0, focus=tuple(t),
                cine=dict(exposure=0.3))


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
        p3._knee_mats(o, sand=0.6)                                 # the same stained burial bone as the graves
    zc = G.H(-1.5, -0.4)
    _spot((-0.2, -2.6, zc + 1.2), (-1.5, -0.4, zc), 420, size=0.2, color=(1.0, 0.84, 0.66), spot=40)   # low golden sun raking the floor
    return dict(a=((-2.4, -1.7, zc + 0.75), (-1.5, -0.4, zc)), b=((-2.0, -1.85, zc + 0.7), (-1.3, -0.35, zc)), lens=35,
                fstop=8.0, focus=(-1.45, -0.4, zc), cine=dict(exposure=0.35))


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
