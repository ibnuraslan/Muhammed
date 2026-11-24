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
    for seg, klen in (("femur" + side, keep_femur), ("shank" + side, keep_tibia)):
        o = sk.parts[seg]
        o.data = o.data.copy()                                    # skeletons share mesh data: cut a private copy
        Mi = o.matrix_world.inverted()
        bm = bmesh.new(); bm.from_mesh(o.data)
        co = np.array([o.matrix_world @ v.co for v in bm.verts])
        d = np.linalg.norm(co - np.array(kj), axis=1)
        far = co[np.argmax(d)]
        axis = (Vector(far.tolist()) - kj).normalized()            # along the bone away from the knee
        cut_w = kj + axis * klen
        rng = random.Random(len(seg))
        nrm_w = (axis + Vector((rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25), rng.uniform(-0.2, 0.2)))).normalized()
        pc = Mi @ cut_w; pn = (Mi.to_3x3() @ nrm_w).normalized()
        res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=pc, plane_no=pn)
        # delete the unwanted side ourselves (world-side test is unambiguous): near = toward the knee joint
        sgn = 1.0 if keep == "near" else -1.0
        kill = [v for v in bm.verts if sgn * (v.co - pc).dot(pn) > 1e-6]
        bmesh.ops.delete(bm, geom=kill, context='VERTS')
        edges = [e for e in bm.edges if e.is_boundary]
        if edges:
            cr_ = bmesh.ops.contextual_create(bm, geom=edges)
            caps = [f for f in cr_.get("faces", [])]
            if caps:
                pk = bmesh.ops.poke(bm, faces=caps)                  # a fan of triangles: the break face can be roughened
                for f in pk.get("faces", []):
                    f.material_index = 1; f.smooth = False          # broken face: trabecular bone, crisp
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        # a dry break is jagged, not sawn: push every vertex near the cut along the plane normal by a noise field taken
        # in WORLD space - both sides of the same break (pieces and shafts) get the same displacement, so they interlock
        from mathutils import noise as _nz
        Mw = o.matrix_world
        bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if all(abs((v.co - pc).dot(pn)) < 0.003 for v in e.verts)],
                                  cuts=3, use_grid_fill=True)
        for v in bm.verts:
            dist = (v.co - pc).dot(pn)
            if abs(dist) < 0.004:
                w = Mw @ v.co
                j = 0.006 * _nz.noise(w * 90.0) + 0.003 * _nz.noise(w * 260.0)
                v.co = v.co + pn * (j - dist * 0.0)
        bm.to_mesh(o.data); bm.free(); o.data.update()
        out.append(o)
    if keep == "near":
        out.append(sk.parts["patella" + side])
    else:
        sk.remove("patella" + side)
    return out


def _trabecular(name="trabecular"):
    """The broken face of a long bone: spongy trabecular bone - a lattice of pale struts round dark pores, with a
    thin dense cortical rim - stained like the rest of the bone."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    v1 = N.new("ShaderNodeTexVoronoi"); v1.feature = 'DISTANCE_TO_EDGE'; v1.inputs['Scale'].default_value = 420; L.new(tc.outputs['Object'], v1.inputs['Vector'])
    v2 = N.new("ShaderNodeTexVoronoi"); v2.feature = 'DISTANCE_TO_EDGE'; v2.inputs['Scale'].default_value = 170; L.new(tc.outputs['Object'], v2.inputs['Vector'])
    mn = N.new("ShaderNodeMath"); mn.operation = 'MINIMUM'; L.new(v1.outputs['Distance'], mn.inputs[0]); L.new(v2.outputs['Distance'], mn.inputs[1])
    st = N.new("ShaderNodeMapRange"); st.inputs['From Min'].default_value = 0.02; st.inputs['From Max'].default_value = 0.09
    st.inputs['To Min'].default_value = 1.0; st.inputs['To Max'].default_value = 0.0; L.new(mn.outputs[0], st.inputs['Value'])   # 1 on struts
    col = N.new("ShaderNodeMix"); col.data_type = 'RGBA'; L.new(st.outputs[0], col.inputs['Factor'])
    col.inputs[6].default_value = (0.05, 0.035, 0.02, 1); col.inputs[7].default_value = (0.55, 0.45, 0.32, 1)
    L.new(col.outputs[2], p.inputs['Base Color'])
    bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 1.0; bp.inputs['Distance'].default_value = 0.0015
    L.new(st.outputs[0], bp.inputs['Height']); L.new(bp.outputs['Normal'], p.inputs['Normal'])
    p.inputs['Roughness'].default_value = 0.9
    return m


def _knee_mats(o, sand=0.5):
    """Aged knee-piece materials: stained, pored, root-etched bone; the broken faces (slot 1) spongy trabecular bone."""
    o.data.materials.clear(); o.data.materials.append(B.bone_material("C", dirt=1.0, sand=sand))
    p2._bone_detail(o); _old_bone(o, stain=0.6)
    for mt in o.data.materials:                            # a harder, crisper bone surface: stronger pores and grain
        for n in mt.node_tree.nodes:
            if n.type == 'BUMP':
                n.inputs['Strength'].default_value = min(1.0, n.inputs['Strength'].default_value * 1.6)
                n.inputs['Distance'].default_value *= 1.8
    o.data.materials.append(_trabecular())


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
    R = BR.interior(fire=1.0, door_sun=0.0, moon=1.0)
    hx, hy = R["hearth"]
    for k, (dx, rot) in enumerate(((-1.75, 88), (-0.7, 92), (0.35, 86))):
        P2.hurdle((hx + dx, hy + 1.7, 0.03), rot=math.radians(rot), length=1.6, width=0.7, seed=k)
        P2.bundle((hx + dx, hy + 1.7, 0.22), rot=math.radians(rot), length=0.85 + 0.1 * k, girth=0.4, seed=k)
    return dict(a=((hx - 2.3, hy - 0.6, 0.9), (hx - 0.6, hy + 1.7, 0.2)), b=((hx - 1.8, hy - 0.2, 0.8), (hx - 0.6, hy + 1.7, 0.2)), lens=32,
                fstop=2.8, focus=(hx - 0.7, hy + 1.7, 0.25), cine=dict(exposure=0.45, sat=0.8), hand_ok=("floor",))


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
    sk, W = lab_part("pelvis", sex="F", tone="C", yaw=90)
    t = Vector(((W.min(0) + W.max(0)) / 2).tolist())
    return dict(a=(tuple(t + Vector((-0.38, -0.5, 0.6))), tuple(t)), b=(tuple(t + Vector((0.12, -0.6, 0.6))), tuple(t)), lens=40,
                fstop=4.0, focus=tuple(t), cine=dict(exposure=-0.05))


def _old_bone(obj, stain=0.8):
    """Long-buried bone: deep brown mineral staining in blotches, surface erosion, and dendritic root etching (pale
    branching grooves where rootlets dissolved the surface)."""
    for i, m0 in enumerate(obj.data.materials):
        if not m0 or not m0.use_nodes:
            continue
        m = m0.copy(); obj.data.materials[i] = m
        N = m.node_tree.nodes; Lk = m.node_tree.links; p = [n for n in N if n.type == 'BSDF_PRINCIPLED']
        if not p:
            continue
        p = p[0]; tc = N.new("ShaderNodeTexCoord")
        src = p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].links else None
        # staining: blotchy dark brown
        st = N.new("ShaderNodeTexNoise"); st.inputs['Scale'].default_value = 9; st.inputs['Detail'].default_value = 8; Lk.new(tc.outputs['Object'], st.inputs['Vector'])
        sm = N.new("ShaderNodeMapRange"); sm.inputs['From Min'].default_value = 0.38; sm.inputs['From Max'].default_value = 0.66
        sm.inputs['To Min'].default_value = 0.35 * stain; sm.inputs['To Max'].default_value = 0.95 * stain; Lk.new(st.outputs['Fac'], sm.inputs['Value'])
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; Lk.new(sm.outputs[0], mx.inputs['Factor'])
        if src:
            Lk.new(src, mx.inputs[6])
        else:
            mx.inputs[6].default_value = p.inputs['Base Color'].default_value
        mx.inputs[7].default_value = (0.36, 0.24, 0.13, 1)
        # root etching: thin branching channels (voronoi cell edges on warped coordinates)
        wn = N.new("ShaderNodeTexNoise"); wn.inputs['Scale'].default_value = 18; wn.inputs['Detail'].default_value = 3; Lk.new(tc.outputs['Object'], wn.inputs['Vector'])
        wm = N.new("ShaderNodeMix"); wm.data_type = 'VECTOR'; wm.inputs['Factor'].default_value = 0.12
        Lk.new(tc.outputs['Object'], wm.inputs[4]); Lk.new(wn.outputs['Color'], wm.inputs[5])
        ve = N.new("ShaderNodeTexVoronoi"); ve.feature = 'DISTANCE_TO_EDGE'; ve.inputs['Scale'].default_value = 55; Lk.new(wm.outputs[1], ve.inputs['Vector'])
        rl = N.new("ShaderNodeMapRange"); rl.inputs['From Min'].default_value = 0.0; rl.inputs['From Max'].default_value = 0.027
        rl.inputs['To Min'].default_value = 1.0; rl.inputs['To Max'].default_value = 0.0; Lk.new(ve.outputs['Distance'], rl.inputs['Value'])
        mk = N.new("ShaderNodeTexNoise"); mk.inputs['Scale'].default_value = 6; Lk.new(tc.outputs['Object'], mk.inputs['Vector'])
        mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.52; mr.inputs['From Max'].default_value = 0.6; Lk.new(mk.outputs['Fac'], mr.inputs['Value'])
        root = N.new("ShaderNodeMath"); root.operation = 'MULTIPLY'; Lk.new(rl.outputs[0], root.inputs[0]); Lk.new(mr.outputs[0], root.inputs[1])
        rc = N.new("ShaderNodeMix"); rc.data_type = 'RGBA'; Lk.new(root.outputs[0], rc.inputs['Factor']); Lk.new(mx.outputs[2], rc.inputs[6])
        rc.inputs[7].default_value = (0.56, 0.47, 0.34, 1)
        hs = N.new("ShaderNodeHueSaturation"); hs.inputs['Value'].default_value = 0.8; Lk.new(rc.outputs[2], hs.inputs['Color'])
        Lk.new(hs.outputs[0], p.inputs['Base Color'])
        # erosion pitting plus the etched grooves in the bump
        er = N.new("ShaderNodeTexNoise"); er.inputs['Scale'].default_value = 160; er.inputs['Detail'].default_value = 10; Lk.new(tc.outputs['Object'], er.inputs['Vector'])
        hh = N.new("ShaderNodeMath"); hh.operation = 'MULTIPLY_ADD'; hh.inputs[1].default_value = -0.8; Lk.new(root.outputs[0], hh.inputs[0]); Lk.new(er.outputs['Fac'], hh.inputs[2])
        bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.7; bp.inputs['Distance'].default_value = 0.0012; Lk.new(hh.outputs[0], bp.inputs['Height'])
        if p.inputs['Normal'].links:
            Lk.new(p.inputs['Normal'].links[0].from_socket, bp.inputs['Normal'])
        Lk.new(bp.outputs['Normal'], p.inputs['Normal'])
        p.inputs['Roughness'].default_value = 0.85
        if 'Subsurface Weight' in p.inputs:
            p.inputs['Subsurface Weight'].default_value = 0.0


def S05():
    """The head: a male cranium, heavier brow ridges and mastoids, darker and more stained than the pelvis. Slow slide."""
    A = LB.room(window_light=0.3, lamp=True, lamp_at=(0.4, 0.62), lamp_target=(0.0, 0.36), lamp_energy=22)
    LB.velvet(-0.6, 0.7, 0.0, 0.78, LB.TOP)
    cr = B.hero_cranium(healed=False, tone="D"); _old_bone(cr)
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
    lab_part("pelvis", sex="F", tone="C", x=0.22, y=0.4, yaw=90)
    cr = B.hero_cranium(healed=False, tone="D"); _old_bone(cr)
    co = np.array([v.co for v in cr.data.vertices]); cr.location = (-0.22, 0.4, LB.TOP + 0.004 - co[:, 2].min() * 0.97)
    cr.rotation_euler = (0, 0, math.radians(-30))
    c = Vector((0.0, 0.4, LB.TOP + 0.06))
    return dict(a=((0.0, -0.3, LB.TOP + 0.2), tuple(c)), b=((0.0, -0.75, LB.TOP + 0.38), tuple(c)), lens=40,
                fstop=4.0, focus=tuple(c), cine=dict(exposure=-0.05))


# ============================================================================ "Researchers take samples from four places."
def S07():
    """The skull, upside down on its ring with the base turned up: a small hole drilled beside the foramen magnum into
    the dense petrous bone, the dust collected; capped tubes beside it. Slow push."""
    L = p1.lab_skull(inverted=True, lamp_energy=22)
    cr = L["cr"]
    bpy.context.view_layer.update()
    W = np.array([cr.matrix_world @ v.co for v in cr.data.vertices])
    top = W[W[:, 2] > np.percentile(W[:, 2], 97)]
    hole = Vector((float(top[:, 0].mean()) + 0.025, float(top[:, 1].mean()), float(top[:, 2].mean())))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0045, depth=0.008, location=hole); h = bpy.context.active_object
    h.name = "drillhole"; h.data.materials.append(_plain("hole", (0.03, 0.02, 0.012), 0.9))
    for k in range(3):
        _tube(0.16 + k * 0.022, 0.5, LB.TOP, cap=(0.55, 0.1, 0.05))
    c = Vector((0.04, 0.38, LB.TOP + 0.1))
    return dict(a=((-0.25, -0.15, LB.TOP + 0.38), tuple(c)), b=((-0.15, -0.08, LB.TOP + 0.32), tuple(hole)), lens=50,
                fstop=4.0, focus=tuple(hole), cine=dict(exposure=-0.1))


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
def _pp(name="polyprop"):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (0.92, 0.92, 0.9, 1); p.inputs['Transmission Weight'].default_value = 0.85
    p.inputs['Roughness'].default_value = 0.15; p.inputs['IOR'].default_value = 1.49
    return m


def _microtube(x, y, z, cap=(0.15, 0.45, 0.8), powder=True, open_=False):
    """A 1.5 ml microcentrifuge tube standing in a rack: conical polypropylene body, ribbed collar, hinged snap cap."""
    prof = [(0.0, 0.0), (0.0018, 0.001), (0.0045, 0.012), (0.0052, 0.022), (0.0054, 0.037), (0.0062, 0.038), (0.0062, 0.041),
            (0.0056, 0.041), (0.0048, 0.040), (0.0046, 0.024), (0.0038, 0.012), (0.0014, 0.0015), (0.0, 0.0015)]
    o = BR._lathe2("microtube", prof, _pp(), (x, y, z), segs=28)
    bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=0.0058, depth=0.004, location=(x, y, z + 0.043)); c = bpy.context.active_object
    c.data.materials.append(_plain(f"cap{cap}", cap, 0.35)); c.name = "tubecap"
    if open_:
        c.location = (x + 0.006, y, z + 0.047); c.rotation_euler.y = math.radians(-100)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x + 0.0062, y, z + 0.042)); hg = bpy.context.active_object
    hg.scale = (0.004, 0.003, 0.0012); hg.data.materials.append(c.data.materials[0]); hg.name = "tubehinge"
    if powder:
        bpy.ops.mesh.primitive_cone_add(vertices=20, radius1=0.0012, radius2=0.0036, depth=0.008, location=(x, y, z + 0.0055)); pw = bpy.context.active_object
        pw.data.materials.append(_plain("bonepowder", (0.82, 0.78, 0.7), 0.95)); pw.name = "tubepowder"
    return o


def _rack(x, y, z, nx=6, ny=4, pitch=0.013, col=(0.15, 0.35, 0.75)):
    """A perforated tube rack (blue polypropylene) and tubes in some of its holes; returns tube positions."""
    m = _plain(f"rack{col}", col, 0.45)
    w, d = nx * pitch + 0.01, ny * pitch + 0.01
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z + 0.03)); top = bpy.context.active_object
    top.scale = (w, d, 0.003); top.data.materials.append(m); top.name = "rack"
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x + sx * w / 2, y, z + 0.015)); leg = bpy.context.active_object
        leg.scale = (0.003, d, 0.03); leg.data.materials.append(m); leg.name = "rack"
    pos = []
    for i in range(nx):
        for j in range(ny):
            px = x - (nx - 1) * pitch / 2 + i * pitch; py = y - (ny - 1) * pitch / 2 + j * pitch
            bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.0042, depth=0.0034, location=(px, py, z + 0.0302)); hole = bpy.context.active_object
            hole.data.materials.append(_plain("holedark", (0.01, 0.01, 0.015), 0.5)); hole.name = "rackhole"
            pos.append((px, py))
    return pos


def clean_room(uv=1.0):
    """Ancient-DNA clean room: white walls, a laminar-flow cabinet with a glass sash and violet UV tubes, racks of capped
    tubes, a pipette on its stand; cold overhead light."""
    white = _plain("cleanwall", (0.3, 0.33, 0.37), 0.6)
    for loc, sc in (((0, 2.0, 1.5), (8, 0.1, 3)), ((-3.5, 0, 1.5), (0.1, 6, 3)), ((3.5, 0, 1.5), (0.1, 6, 3)), ((0, 0, 3.0), (8, 6, 0.1))):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.active_object; o.scale = sc; o.data.materials.append(white)
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0)); f = bpy.context.active_object; f.data.materials.append(_plain("cleanfloor", (0.18, 0.2, 0.22), 0.3))
    steel = P2._brushed("cabsteel", (0.62, 0.63, 0.65), 0.3)
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
        tb.data.materials.append(P2._mat("uvglow", (0, 0, 0), 0.4, emit=(0.45, 0.2, 1.0), strength=25 * uv))
    d = bpy.data.lights.new("uv", 'AREA'); d.size = 1.3; d.size_y = 0.5; d.shape = 'RECTANGLE'; d.energy = 40 * uv; d.color = (0.5, 0.3, 1.0)
    wl = bpy.data.lights.new("cabwhite", 'AREA'); wl.size = 1.3; wl.size_y = 0.4; wl.shape = 'RECTANGLE'; wl.energy = 8; wl.color = (0.92, 0.96, 1.0)
    wo = bpy.data.objects.new("cabwhite", wl); bpy.context.scene.collection.objects.link(wo); wo.location = (0, 1.45, 1.46)
    lo = bpy.data.objects.new("uv", d); bpy.context.scene.collection.objects.link(lo); lo.location = (0, 1.6, 1.45)
    # work surface: two racks of 1.5 ml tubes, an open tube, a pipette with a tip on its stand
    for rx, col in ((-0.3, (0.15, 0.35, 0.75)), (0.22, (0.85, 0.85, 0.82))):
        pos = _rack(rx, 1.6, 0.9, col=col)
        rng_ = random.Random(int(rx * 100))
        for k, (px, py) in enumerate(pos):
            if rng_.random() < 0.6:
                _microtube(px, py, 0.913, cap=rng_.choice([(0.15, 0.45, 0.8), (0.9, 0.9, 0.88), (0.85, 0.2, 0.1)]), open_=(k == 9))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.011, depth=0.17, location=(0.0, 1.72, 1.03)); pp = bpy.context.active_object
    pp.rotation_euler.x = math.radians(10); pp.data.materials.append(_plain("pipette", (0.85, 0.86, 0.86), 0.4)); pp.name = "pipette"
    bpy.ops.mesh.primitive_cone_add(radius1=0.0012, radius2=0.004, depth=0.05, location=(0.0, 1.705, 0.925)); tip = bpy.context.active_object
    tip.rotation_euler.x = math.radians(10); tip.data.materials.append(_pp()); tip.name = "pipettetip"
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


def _cleansuit(name="Cleansuit"):
    """A clean-room worker: white long coat cut straight (no back vent), loose white trousers, slight build."""
    import modern as MD

    class _C(MD.ModernMan):
        GENDER = 1.0; MUSCLE = 0.4; WEIGHT = 0.3; HEIGHT = 0.5
        HAIR = (0.25, 0.1); HAIR_LEN = (0.01, 0.02)
        SHIRT = (0.85, 0.86, 0.86); JACKET = "cagoule"; JACKET_COL = (0.86, 0.87, 0.88)
        TROUSERS = (0.8, 0.81, 0.82); SHOES = (0.85, 0.85, 0.85)
        TROUSER_EASE = 1.35; TROUSER_EXTRA = 0.035
    return _C(name, years=33)


def _suit_up(m, st=None):
    """Clean-room suit details on a posed figure: a Tyvek hood enclosing the head (sized from the head itself, so it
    cannot clip), purple nitrile gloves on the hands, and a smoother suit fabric (soft folds, no lumpy creases)."""
    import numpy as np
    dg = bpy.context.evaluated_depsgraph_get()
    body = [o for o in bpy.data.objects if o.name == m.name + "_body"]
    if not body:
        return
    body = body[0]; be = body.evaluated_get(dg); me = be.to_mesh()
    W = np.array([be.matrix_world @ v.co for v in me.vertices])
    h = m.h
    hc = np.array(h.arm.matrix_world @ h.bone_head("head")) if False else None
    neck_z = float((st.M @ h.bone_head("head")).z) - 0.03 if st is not None else float(np.percentile(W[:, 2], 87))
    # the hood follows the head itself: the head-and-neck skin of the posed body, lifted off it along the normals,
    # smoothed into soft fabric - it covers the face (mask and goggles under it are never seen from behind)
    tyvek = _plain("tyvek", (0.9, 0.91, 0.92), 0.72)
    nz_ = neck_z - 0.06
    # the head under the hood is never seen: drop the eyes and the body's head skin so nothing can poke through
    hidden = [i for i, v in enumerate(me.vertices) if (be.matrix_world @ v.co).z > nz_ + 0.03]
    same_topo = len(me.vertices) == len(body.data.vertices)
    for o_ in [o_ for o_ in bpy.data.objects if o_.name.startswith(m.name + "_eye") or o_.name.startswith(m.name + "_cornea")]:
        bpy.data.objects.remove(o_)
    bm = bmesh.new(); bm.from_mesh(me); bm.transform(be.matrix_world)
    bm.verts.ensure_lookup_table()
    drop = [f for f in bm.faces if min(v.co.z for v in f.verts) < nz_]
    bmesh.ops.delete(bm, geom=drop, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.normal_update()
    for v in bm.verts:
        v.co += v.normal * 0.03
    hm = bpy.data.meshes.new(m.name + "_hood"); bm.to_mesh(hm); bm.free()
    be.to_mesh_clear()
    # remove the head and upper neck skin by its bone weights (rest-pose mesh; topology of the evaluated one may differ)
    hg = {g.index for g in body.vertex_groups if any(k in g.name.lower() for k in ("head", "neck02", "neck03", "jaw", "eye", "ear", "tongue", "teeth", "levator", "orbicularis", "oris", "temporalis", "special"))}
    if hg:
        kill = [v.index for v in body.data.vertices if sum(g.weight for g in v.groups if g.group in hg) > 0.12]
        bb = bmesh.new(); bb.from_mesh(body.data); bb.verts.ensure_lookup_table()
        bmesh.ops.delete(bb, geom=[bb.verts[i] for i in kill], context='VERTS'); bb.to_mesh(body.data); bb.free(); body.data.update()
        print("hood: removed", len(kill), "head verts")
    hd = bpy.data.objects.new(m.name + "_hood", hm); bpy.context.scene.collection.objects.link(hd); hm.materials.append(tyvek)
    for p_ in hm.polygons:
        p_.use_smooth = True
    sm = hd.modifiers.new("soft", "SMOOTH"); sm.factor = 0.5; sm.iterations = 5
    so = hd.modifiers.new("thick", "SOLIDIFY"); so.thickness = 0.004; so.offset = 1.0
    d = hd.modifiers.new("folds", "DISPLACE"); t = bpy.data.textures.new("hoodfold", "CLOUDS"); t.noise_scale = 0.05; d.texture = t; d.strength = 0.006
    # gloves: hand faces of the body get a purple nitrile material
    glove = _plain("nitrile", (0.32, 0.28, 0.72), 0.45)
    body.data.materials.append(glove); gi = len(body.data.materials) - 1
    groups = {g.index for g in body.vertex_groups if ("hand" in g.name.lower() or "finger" in g.name.lower() or "metacarpal" in g.name.lower() or "wrist" in g.name.lower())}
    if groups:
        hv = set()
        for v in body.data.vertices:
            if sum(g.weight for g in v.groups if g.group in groups) > 0.5:
                hv.add(v.index)
        for p_ in body.data.polygons:
            if all(i in hv for i in p_.vertices):
                p_.material_index = gi
    # smoother suit: soften the crease bump on the smock
    for o in bpy.data.objects:
        if o.name.startswith(m.name + "_jacket"):
            for mt in o.data.materials:
                if mt:
                    for n in mt.node_tree.nodes:
                        if n.type == 'BUMP':
                            n.inputs['Strength'].default_value = min(n.inputs['Strength'].default_value, 0.25)


def S11():
    """The ancient-DNA clean room: a scientist in a full white suit and hood works at the UV cabinet, seen from behind;
    the violet light through the sash. Slow push."""
    clean_room(uv=0.35)
    import acts as AC
    m = _cleansuit()
    st = AC.Stand(m, (0.0, 0.62), 90, lean=10)
    st.hand("L", (-0.18, 1.32, 0.98), elbow=(0.6, 0.2, -0.8), curl=20)
    st.hand("R", (0.15, 1.32, 1.0), elbow=(0.6, 0.2, -0.8), curl=20)
    st.head_to((0, 1.6, 0.95), share=0.8)
    st.finish(look=(0, 1.6, 0.95), density=0.0, hair=False)
    _suit_up(m, st)
    # over the shoulder into the UV cabinet: hands at the tube racks, the violet light on the sash (waist out of frame)
    return dict(a=((0.42, 0.05, 1.9), (-0.05, 1.55, 0.95)), b=((0.36, 0.18, 1.85), (-0.05, 1.58, 0.95)), lens=30,
                fstop=2.8, focus=(0.0, 0.7, 1.3), cine=dict(exposure=0.1), hand_ok=("sash", "cabinet", "hood"))


def S12():
    """Inside the cabinet under UV: capped tubes of bone powder in a rack, the pipette, violet glow. Macro slide."""
    clean_room(uv=0.35)
    return dict(a=((-0.52, 1.2, 1.06), (-0.36, 1.6, 0.94)), b=((-0.4, 1.2, 1.06), (-0.24, 1.6, 0.94)), lens=60,
                fstop=4.0, focus=(-0.3, 1.6, 0.94), cine=dict(exposure=-0.5))


def S13():
    """A sample tube in the cabinet with the bone powder at its tip, sharp; the rack soft behind. Push."""
    clean_room(uv=0.55)
    t = Vector((0.25 - 0.075 + 2 * 0.03, 1.6, 0.97))
    return dict(a=(tuple(t + Vector((-0.16, -0.5, 0.16))), tuple(t)), b=(tuple(t + Vector((-0.1, -0.4, 0.12))), tuple(t)), lens=70,
                fstop=2.8, focus=tuple(t), cine=dict(exposure=-0.5))


# ============================================================================ "The results are published in 2012."
def S14():
    """The lab at night, the work done: the UV cabinet almost dark, the side bench of instruments with their small
    status lights glowing in the gloom. Slow glide along the bench (no screens, no text)."""
    clean_room(uv=0.12)
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.name.startswith("ceil"):
            o.data.energy = 6
    # the finished samples: the rack of capped tubes in the darkened cabinet, one cold strip light left on
    d = bpy.data.lights.new("strip", 'AREA'); d.shape = 'RECTANGLE'; d.size = 1.2; d.size_y = 0.08; d.energy = 25; d.color = (0.85, 0.92, 1.0)
    lo = bpy.data.objects.new("strip", d); bpy.context.scene.collection.objects.link(lo); lo.location = (0.0, 1.45, 1.45)
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.name.startswith("cabwhite"):
            o.data.energy = 0.0
    d.energy = 8
    t = Vector((0.1, 1.5, 1.0))
    return dict(a=((-2.3, -1.3, 1.55), tuple(t)), b=((-1.9, -1.5, 1.5), tuple(t + Vector((0.3, 0, 0)))), lens=32, fstop=4.0, focus=tuple(t),
                cine=dict(exposure=-0.2))


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
    return dict(a=((-2.6, -0.55, LB.TOP + 0.42), (0.3, 0.42, LB.TOP + 0.02)), b=((-1.9, -0.6, LB.TOP + 0.42), (1.0, 0.42, LB.TOP + 0.02)), lens=40,
                fstop=5.6, focus=(0.0, 0.4, LB.TOP), cine=dict(exposure=-0.1))


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
    """The missing knee, close: the second body's legs drawn up; the uppermost (left) leg stops short at dry breaks -
    thigh bone and shin end with a gap where the knee should be. Slow push from above."""
    T, sk0 = p1.site("day", grass_at=None, kit=False, burials=True, sun_az=215)
    gx, gy = -4.2, 3.4                                     # a clear patch of the house floor
    z = G.H(gx, gy)
    bpy.ops.mesh.primitive_circle_add(vertices=48, radius=0.85, fill_type='NGON', location=(gx, gy, z + 0.003)); fl = bpy.context.active_object
    fl.scale = (1.0, 0.7, 1.0); fl.data.materials.append(G.mat("gravefloor")); fl.name = "gravefloor_patch"
    sk = B.Skeleton("M", "C", name="Second", sand=0.6)
    sk.pose_crouched(tight=1.0, side="R")                  # lying on its right side: the broken left leg uppermost
    sk.place((gx, gy, z), heading=30, ground_fn=lambda x, y: G.H(x, y) + 0.003)
    knee_pieces(sk, side="L", keep="far")                  # the left knee is gone: femur and shin end in breaks
    for o_ in sk.parts.values():                           # the same long-buried brown bone as the other grave shots
        _knee_mats(o_, sand=0.6)
    bpy.context.view_layer.update()
    kj = sk.world_pivot("shankL")
    t = Vector((kj.x, kj.y, kj.z))
    th = sk.world_pivot("thorax"); aw = Vector((t.x - th.x, t.y - th.y, 0)).normalized()     # away from the body, past the knees
    sd = Vector((-aw.y, aw.x, 0))
    # low, in front of the drawn-up knees: the right knee on top, intact; under it the left leg ends in breaks
    return dict(a=(tuple(t + aw * 0.3 + sd * 0.15 + Vector((0, 0, 0.75))), tuple(t)), b=(tuple(t + aw * 0.22 + sd * 0.1 + Vector((0, 0, 0.58))), tuple(t)), lens=45,
                fstop=4.0, focus=tuple(t), cine=dict(exposure=0.05))


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
        _knee_mats(o, sand=0.7)
    out = dict(knee=Vector((kx, ky, zf + 0.03)), pieces=pcs)
    if kneel:
        out["st"] = K.kneel_trowel(K.DiggerB, (kx + 0.15, ky - 0.75), 95, work=(kx + 0.05, ky - 0.25), density=HAIR)
    return out


def S23():
    """Outside the house: a digger (from behind) kneels at a small separate pit, trowelling; the house rings beyond."""
    o = _knee_pit()
    k = o["knee"]
    # over the right shoulder, from the digger's own rig: camera above and just behind his right shoulder, looking down
    # past the trowel hand into the pit (hips and legs below and behind the frame)
    st = o["st"]; h = st.m.h
    shR = st.M @ h.bone_head("upperarm01.R"); shL = st.M @ h.bone_head("upperarm01.L")
    hd = st.M @ h.bone_head("head")
    rt = Vector((shR.x - shL.x, shR.y - shL.y, 0)).normalized()
    hand = st.palm("R")
    fw = Vector((hand.x - hd.x, hand.y - hd.y, 0)).normalized()
    cam = shR + rt * 0.32 - fw * 0.12 + Vector((0, 0, 0.42))
    tgt = hand + fw * 0.08
    return dict(a=(tuple(cam), tuple(tgt)), b=(tuple(cam + fw * 0.06 - Vector((0, 0, 0.04))), tuple(tgt)), lens=28,
                fstop=4.0, focus=tuple(hand), hand_ok=p1.OK)


def S24():
    """In the pit: the pieces of a human knee - the end of a thigh bone, the kneecap, the top of a shin - in the sand."""
    o = _knee_pit(kneel=False)
    k = o["knee"]
    return dict(a=(tuple(k + Vector((0.35, -0.55, 0.65))), tuple(k)), b=(tuple(k + Vector((0.12, -0.6, 0.55))), tuple(k)), lens=45,
                fstop=5.6, focus=tuple(k), cine=dict(exposure=0.1))


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
    legs[1].root.location += Vector((0.0, -0.003, 0.002))
    bpy.context.view_layer.update()
    # open each break by a centimetre so the spongy broken faces and the matching jagged edges both read
    kc = Vector(np.concatenate([np.array([o.matrix_world @ v.co for v in o.data.vertices]) for o in legs[1].parts.values()]).mean(0).tolist())
    moves = []
    for nm in ("femurL", "shankL"):
        o = legs[0].parts.get(nm)
        if o is not None:
            cc = Vector(np.array([o.matrix_world @ v.co for v in o.data.vertices]).mean(0).tolist())
            d = (cc - kc); d.z = 0
            moves.append((o, o.matrix_world.copy(), Matrix.Translation(d.normalized() * 0.011)))
    for o, mw, T in moves:                                   # in world space (the shin is parented to the thigh)
        o.matrix_world = T @ mw
        bpy.context.view_layer.update()      # the pit pieces a hairline off the breaks
    bpy.context.view_layer.update()
    for o in objs:
        _knee_mats(o, sand=0.35)
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
    """Macro on the dry break: the thigh bone's fracture line where the pit piece meets the shaft, in grazing light."""
    d = S25()
    sh = [o for o in bpy.data.objects if o.name.startswith("Shafts_femurL")][0]
    W = np.array([sh.matrix_world @ v.co for v in sh.data.vertices])
    kj = Vector(d["focus"])
    near = W[np.argsort(np.linalg.norm(W - np.array(kj), axis=1))[:200]]          # the broken end of the shaft
    t = Vector(near.mean(0).tolist())
    _spot((t.x - 0.5, t.y - 0.25, t.z + 0.12), tuple(t), 70, size=0.02, spot=18)
    return dict(a=(tuple(t + Vector((0.05, -0.2, 0.12))), tuple(t)), b=(tuple(t + Vector((-0.03, -0.2, 0.11))), tuple(t)), lens=85,
                fstop=8.0, focus=tuple(t), cine=dict(exposure=0.0))


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
    return dict(a=(tuple(k + Vector((-0.3, -0.38, 0.5))), tuple(k)), b=(tuple(k + Vector((-0.18, -0.4, 0.42))), tuple(k)), lens=60,
                fstop=4.0, focus=tuple(k), cine=dict(exposure=0.1))


def S30():
    """An old body that kept its tissue: a dried, wrapped bundle on a hurdle in the dim roundhouse, firelight. Push."""
    U.CUT = False
    R = BR.interior(fire=1.0, door_sun=0.0, moon=1.0)
    hx, hy = R["hearth"]
    P2.hurdle((hx - 0.8, hy + 1.6, 0.03), rot=math.radians(80), length=1.8, width=0.75)
    P2.bundle((hx - 0.8, hy + 1.6, 0.23), rot=math.radians(80), length=0.95, girth=0.42)
    t = Vector((hx - 0.8, hy + 1.6, 0.25))
    return dict(a=(tuple(t + Vector((-1.3, -1.4, 0.6))), tuple(t)), b=(tuple(t + Vector((-0.8, -0.9, 0.45))), tuple(t)), lens=40,
                fstop=2.8, focus=tuple(t), cine=dict(exposure=0.45, sat=0.8), hand_ok=("floor",))


# ============================================================================ "In the team's later reconstruction..."
def _hood_cloak(st, col=(0.085, 0.065, 0.045), seed=0):
    """A Bronze Age hooded wool cloak-cape over a posed islander: the head, neck, shoulders and upper chest of the posed
    body (by bone weight), lifted well off it and softened into heavy wool, open at the face. Replaces the strand hair
    (which read as round puffs by torchlight)."""
    m = st.m
    dg = bpy.context.evaluated_depsgraph_get()
    body = bpy.data.objects.get(m.name + "_body")
    if body is None:
        print("cloak: no body for", m.name); return None
    keys = ("head", "neck", "spine01", "spine02", "clavicle", "shoulder01", "breast", "pectoral", "levator", "trapez")
    gi = {g.index for g in body.vertex_groups if any(k in g.name.lower() for k in keys)}
    wsel = np.array([sum(g.weight for g in v.groups if g.group in gi) > 0.3 for v in body.data.vertices])
    off = [md for md in body.modifiers if md.type != 'ARMATURE' and md.show_viewport]
    for md in off:
        md.show_viewport = False                      # posed but unmasked: one evaluated vertex per base vertex
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    be = body.evaluated_get(dg); me = be.to_mesh()
    for md in off:
        md.show_viewport = True
    if len(me.vertices) != len(wsel):
        print("cloak: vertex mismatch", len(me.vertices), len(wsel)); be.to_mesh_clear(); return None
    hd = m.h.bone_head("head")                    # world (the rig is placed and lifted by now)
    eyes = [o for o in bpy.data.objects if o.name.startswith(m.name + "_eye")]
    fwd = ((sum((o.matrix_world.translation for o in eyes), Vector()) / len(eyes)) - hd).normalized() if eyes else Vector((0, -1, 0))
    bm = bmesh.new(); bm.from_mesh(me); bm.transform(be.matrix_world); bm.verts.ensure_lookup_table(); bm.normal_update()
    be.to_mesh_clear()
    drop = []
    for f in bm.faces:
        if not all(wsel[v.index] for v in f.verts):
            drop.append(f); continue
        c = f.calc_center_median()
        if (c - hd).dot(fwd) > 0.035 and f.normal.dot(fwd) > 0.3:        # the face opening
            drop.append(f)
    bmesh.ops.delete(bm, geom=drop, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.normal_update()
    for v in bm.verts:
        v.co += v.normal * 0.05
    cm = bpy.data.meshes.new(m.name + "_cloak"); bm.to_mesh(cm); bm.free()
    co = bpy.data.objects.new(m.name + "_cloak", cm); bpy.context.scene.collection.objects.link(co)
    wool = bpy.data.materials.get("cloakwool")
    if wool is None:
        wool = _plain("cloakwool", col, 0.95)
        N = wool.node_tree.nodes; L = wool.node_tree.links; pr = N["Principled BSDF"]
        tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 260; nz.inputs['Detail'].default_value = 8
        L.new(tc.outputs['Object'], nz.inputs['Vector']); bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.35
        L.new(nz.outputs['Fac'], bp.inputs['Height']); L.new(bp.outputs['Normal'], pr.inputs['Normal'])
        if 'Sheen Weight' in pr.inputs:
            pr.inputs['Sheen Weight'].default_value = 0.4
    cm.materials.append(wool)
    for pg in cm.polygons:
        pg.use_smooth = True
    sm = co.modifiers.new("soft", "SMOOTH"); sm.factor = 0.5; sm.iterations = 6
    so = co.modifiers.new("thick", "SOLIDIFY"); so.thickness = 0.008; so.offset = 1.0
    t = bpy.data.textures.new(m.name + "_cloakfold", "CLOUDS"); t.noise_scale = 0.09
    d = co.modifiers.new("folds", "DISPLACE"); d.texture = t; d.strength = 0.012
    for o in [o for o in bpy.data.objects if o.name.startswith(m.name + "_hair")]:
        bpy.data.objects.remove(o)
    return co


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
            o.data.energy = 0.3; o.data.color = (0.6, 0.7, 1.0)
    # a raised rim of upcast earth round the hole
    bpy.ops.mesh.primitive_torus_add(major_radius=0.62, minor_radius=0.12, location=(kx, ky, z + 0.02)); rim = bpy.context.active_object
    rim.scale = (1.9, 1.0, 0.35); rim.name = "pitrim"; rim.data.materials.append(G.mat("sand"))
    d_ = rim.modifiers.new("d", "DISPLACE"); t_ = bpy.data.textures.new("rimlump", "CLOUDS"); t_.noise_scale = 0.15; d_.texture = t_; d_.strength = 0.05
    # an open pit with a heap of sand beside it
    bpy.ops.mesh.primitive_cylinder_add(radius=0.55, depth=0.6, location=(kx, ky, z - 0.28)); pit = bpy.context.active_object
    pit.scale = (1.5, 1.0, 1.0); pit.data.materials.append(G.mat("sand")); pit.name = "openpit"
    bm = bmesh.new(); bm.from_mesh(pit.data)                     # an open hole: no lid, walls and floor seen from inside
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.9], context='FACES')
    for f in bm.faces:
        f.normal_flip()
    bm.to_mesh(pit.data); bm.free()
    # cut the hole in the ground itself: drop the terrain faces inside the pit outline so the sand walls show
    ter = bpy.data.objects["Uist"]; me = ter.data
    pc = np.zeros(len(me.polygons) * 3, np.float32); me.polygons.foreach_get("center", pc); pc = pc.reshape(-1, 3)
    ins = ((pc[:, 0] - kx) / 1.12) ** 2 + ((pc[:, 1] - ky) / 0.58) ** 2 < 1.0
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in np.nonzero(ins)[0]], context='FACES_ONLY')
    bm.to_mesh(me); bm.free()
    pit.scale = (2.06, 1.07, 1.0)                              # walls just outside the cut edge
    # loose sand and a few stones on the floor
    for j in range(7):
        a_ = random.uniform(0, 6.28); r_ = random.uniform(0.1, 0.6)
        G.stone((kx + r_ * 1.3 * math.cos(a_), ky + r_ * 0.8 * math.sin(a_), z - 0.57), (0.06, 0.05, 0.03), seed=j, flat=0.5)
    G.spoil_heap(kx + 0.2, ky + 1.75, 0.9, 0.6, 0.38)          # upcast on the far side, clear of where they stand
    # pole torch: a flame on a stake, a warm point light
    bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=1.6, location=(kx - 1.3, ky + 0.6, z + 0.8)); st = bpy.context.active_object
    st.data.materials.append(_plain("stake", (0.12, 0.08, 0.05), 0.8)); st.name = "torchstake"
    bpy.ops.mesh.primitive_cone_add(radius1=0.06, radius2=0.0, depth=0.26, location=(kx - 1.3, ky + 0.6, z + 1.72)); fl = bpy.context.active_object
    fl.data.materials.append(P2._mat("flame", (0, 0, 0), 0.5, emit=(1.0, 0.45, 0.1), strength=18)); fl.name = "torchflame"
    fd = fl.modifiers.new("lick", "DISPLACE"); ft = bpy.data.textures.new("flamelick", "CLOUDS"); ft.noise_scale = 0.05; fd.texture = ft; fd.strength = 0.03
    d = bpy.data.lights.new("torch", 'POINT'); d.energy = 220; d.color = (1.0, 0.55, 0.2); d.shadow_soft_size = 0.12
    lo = bpy.data.objects.new("torch", d); bpy.context.scene.collection.objects.link(lo); lo.location = (kx - 1.3, ky + 0.6, z + 1.65)
    # a second torch stuck in the ground on the near side: front light on the hurdle and the body
    bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=1.5, location=(kx - 1.9, ky - 1.8, z + 0.75)); st2 = bpy.context.active_object
    st2.data.materials.append(_plain("stake", (0.12, 0.08, 0.05), 0.8)); st2.name = "torchstake"
    bpy.ops.mesh.primitive_cone_add(radius1=0.055, radius2=0.0, depth=0.24, location=(kx - 1.9, ky - 1.8, z + 1.62)); fl2 = bpy.context.active_object
    fl2.data.materials.append(bpy.data.materials["flame"]); fl2.name = "torchflame"
    d2 = bpy.data.lights.new("torch2", 'POINT'); d2.energy = 160; d2.color = (1.0, 0.55, 0.2); d2.shadow_soft_size = 0.12
    l2 = bpy.data.objects.new("torch2", d2); bpy.context.scene.collection.objects.link(l2); l2.location = (kx - 1.9, ky - 1.8, z + 1.55)
    return Vector((kx, ky, z))


def S31():
    """Night: two islanders kneel on the lip of the opened grave and take hold of the hurdle the body lies on, ready to
    lift - hands closed on the near pole, backs to us, torchlight on the sand walls. Slow push."""
    c = _night_pit()
    import acts as AC
    P2.hurdle((c.x, c.y, c.z - 0.2), rot=0.0, length=1.8, width=0.75)
    P2.bundle((c.x, c.y, c.z - 0.0), rot=0.0, length=0.95, girth=0.42)
    py = c.y - 0.375; pz = -0.2 + 0.03                        # near pole, in the kneelers' ground frame
    zk = max(float(U.surface(c.x + ex, c.y - 0.85 + ey)) for ex in (-0.8, 0, 0.8) for ey in (-0.2, 0, 0.2)) + 0.06
    sts = []
    for i, x0 in enumerate((-0.62, 0.62)):
        m = BR.Islander(name="Islander0") if i == 0 else p2._islander2()
        st = AC.Kneel(m, (c.x + x0, c.y - 0.82), 90, lean=62, sit_back=True)
        for sd, dx in (("L", -0.2), ("R", 0.2)):
            st.grip(sd, (c.x + x0 + dx, py, pz + c.z - zk), (1, 0, 0), radius=0.03)
        st.head_to((c.x + x0, c.y, -0.4), share=0.8); st.finish(look=(c.x + x0, c.y, -0.4), density=HAIR)
        G.lift(st, zk); _hood_cloak(st, col=(0.085, 0.065, 0.045) if i == 0 else (0.16, 0.13, 0.09)); sts.append(st)
    return dict(a=((c.x + 1.9, c.y - 3.3, c.z + 2.9), (c.x + 0.1, c.y + 0.1, c.z - 0.25)), b=((c.x + 1.6, c.y - 2.9, c.z + 2.7), (c.x + 0.1, c.y + 0.1, c.z - 0.25)),
                lens=32, fstop=2.8, focus=(c.x, c.y - 0.4, c.z), cine=dict(exposure=0.6), hand_ok=("openpit", "Uist", "pitrim", "hurdle", "bundle"))


def S32():
    """They haul the preserved body up out of the grave on its hurdle: both on the near side, knees bent, hands closed
    on the pole, the far edge still in the pit. From behind, the torch beyond them. Low angle."""
    c = _night_pit()
    import acts as AC
    hc = Vector((c.x, c.y - 0.05, c.z + 0.42))
    piv = bpy.data.objects.new("hurdle_rig", None); bpy.context.scene.collection.objects.link(piv); piv.location = hc
    before = set(bpy.data.objects)
    P2.hurdle(tuple(hc), rot=0.0, length=1.8, width=0.75)
    P2.bundle(tuple(hc + Vector((0, 0, 0.2))), rot=0.0, length=0.95, girth=0.42)
    bpy.context.view_layer.update()
    for o in set(bpy.data.objects) - before:
        o.parent = piv; o.matrix_parent_inverse = piv.matrix_world.inverted()
    piv.rotation_euler.x = math.radians(-22)                  # near edge up, far edge still down in the grave
    bpy.context.view_layer.update()
    poles = sorted([o for o in bpy.data.objects if o.name.startswith("hurdlepole")], key=lambda o: o.matrix_world.translation.y)
    pc = poles[0].matrix_world.translation.copy()
    for i, x0 in enumerate((-0.5, 0.5)):
        m = BR.Islander(name=f"Islander{i}") if i == 0 else p2._islander2()
        f = (c.x + x0, pc.y - 0.72)
        zf = max(float(U.surface(f[0] + ex, f[1] + ey)) for ex in (-0.15, 0.15) for ey in (-0.15, 0.15))
        st = AC.Haul(m, f, 90, knee=40, lean=34, weight="L" if i == 0 else "R")
        for sd, dx in (("L", -0.22), ("R", 0.22)):
            st.grip(sd, (c.x + x0 + dx, pc.y, pc.z - zf), (1, 0, 0), radius=0.03)
        st.head_to((c.x + x0, c.y + 0.5, 0.3), share=0.6); st.finish(look=(c.x + x0, c.y + 0.5, 0.3), density=HAIR); G.lift(st, zf)
        _hood_cloak(st, col=(0.085, 0.065, 0.045) if i == 0 else (0.16, 0.13, 0.09))
    return dict(a=((c.x + 2.6, c.y - 3.4, c.z + 1.15), (c.x, c.y, c.z + 0.5)), b=((c.x + 2.3, c.y - 3.0, c.z + 1.1), (c.x, c.y, c.z + 0.5)),
                lens=32, fstop=2.8, focus=(c.x, pc.y, c.z + 0.6), cine=dict(exposure=0.45), hand_ok=("hurdle", "bundle"))


def S33():
    """The empty grave by torchlight: in the bottom, the broken knee left behind. Slow descent."""
    c = _night_pit()
    skk, pcs = _lying_knee()
    for s_ in list(skk.parts):
        if skk.parts[s_] not in pcs:
            skk.remove(s_)
    bpy.context.view_layer.update()
    W = np.concatenate([np.array([o.matrix_world @ v.co for v in o.data.vertices]) for o in pcs]); cc = W.mean(0)
    skk.root.location += Vector((c.x - cc[0], c.y - cc[1], c.z + 0.012 - W[:, 2].min()))
    bpy.context.view_layer.update()
    k = Vector((c.x, c.y, c.z + 0.03))
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
    ("S14", 6, 3.5, "The DNA lab at night, the work done: instrument lights in the dark"),
    ("S15", 7, 5.0, "Jaw, upper arm and thigh bone apart: three pools of light"),
    ("S16", 7, 4.0, "The skull alone in low light: no answer"),
    ("S17", 8, 5.5, "Track along the second skeleton, feet to head"),
    ("S18", 9, 5.0, "Crane up from both graves to the whole house floor at dusk"),
    ("S19", 10, 4.5, "The roundhouses at dusk: six lives"),
    ("S20", 11, 6.0, "Close from above: the uppermost left leg ends in dry breaks where the knee should be"),
    ("S21", 12, 7.0, "The legs in the grave from the other side, slow slider"),
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
