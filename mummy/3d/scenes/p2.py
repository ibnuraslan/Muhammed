"""Part 2 (mummy/vo/MUMMY_P2_VO.txt): "To find out what happened..." -> "...more than three thousand years ago."  28 shots.

Same contract and house rules as p1.py: each shot builds its set and cast and returns the camera move
    dict(a=(loc, target), b=(loc, target), lens=, fstop=, focus=, cine=, hand_ok=)
No face toward the lens, every hand belongs to a person in frame, camera carries the motion, clipcheck 0, motivated light,
no text anywhere in frame.
"""
import math, os, random
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
import uist as U, dig as G, cast as K, bones as B, lab as LB, bronze as BR, p2sets as P2, sf, ph
import p1

HAIR = p1.HAIR
_plain, _glass = p1._plain, p1._glass


# ----------------------------------------------------------------------------- helpers
def _single(uid, height=None, name="asset", hide=False):
    """Import a Sketchfab scan as ONE mesh object, base at z = 0, centred in x/y (for placing or instancing)."""
    root, ms = sf.model(uid, height=height)
    bpy.context.view_layer.update()
    for o in ms:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    bpy.ops.object.select_all(action='DESELECT')
    for o in ms:
        o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]
    if len(ms) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    co = np.empty(len(o.data.vertices) * 3, np.float32); o.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    off = np.array([(co[:, 0].min() + co[:, 0].max()) / 2, (co[:, 1].min() + co[:, 1].max()) / 2, co[:, 2].min()])
    co -= off; o.data.vertices.foreach_set("co", co.ravel()); o.data.update()
    o.location = (0, 0, 0); o.name = name
    for c in list(root.children_recursive):
        if c.type != 'MESH' and c.name in bpy.data.objects:
            bpy.data.objects.remove(c)
    if root.name in bpy.data.objects:
        bpy.data.objects.remove(root)
    if hide:
        o.hide_render = True; o.hide_viewport = True
    return o


def _vial(x, y, z, h=0.055, r=0.011, fill=0.25):
    """Small glass vial with a screw cap and a pinch of bone powder at the bottom (no label)."""
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=(x, y, z + h / 2)); v = bpy.context.active_object
    v.data.materials.append(_glass("vialglass")); v.name = "vial"
    bpy.ops.mesh.primitive_cylinder_add(radius=r * 1.08, depth=h * 0.22, location=(x, y, z + h + h * 0.1)); c = bpy.context.active_object
    c.data.materials.append(_plain("vialcap", (0.02, 0.02, 0.022), 0.45)); c.name = "vialcap"
    bpy.ops.mesh.primitive_cylinder_add(radius=r * 0.85, depth=h * fill, location=(x, y, z + 0.002 + h * fill / 2)); p = bpy.context.active_object
    p.data.materials.append(_plain("vialpowder", (0.85, 0.78, 0.66), 0.95)); p.name = "vialpowder"
    return v


def _boat(x, y, z, w=0.05, powder=(0.16, 0.13, 0.1)):
    """Weighing boat (thin aluminium dish) with a heap of drill dust."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=4, radius=w * 0.7, depth=0.008, location=(x, y, z + 0.004)); b = bpy.context.active_object
    b.rotation_euler.z = math.pi / 4; b.name = "boat"
    bm = bmesh.new(); bm.from_mesh(b.data)
    top = [f for f in bm.faces if f.normal.z > 0.9]
    bmesh.ops.delete(bm, geom=top, context='FACES_ONLY')
    for v in bm.verts:
        if v.co.z > 0:
            v.co.x *= 1.2; v.co.y *= 1.2
    bm.to_mesh(b.data); bm.free()
    sol = b.modifiers.new("t", "SOLIDIFY"); sol.thickness = 0.0006
    b.data.materials.append(_plain("alu", (0.8, 0.8, 0.82), 0.3, 1.0))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=w * 0.28, location=(x, y, z + 0.001)); p = bpy.context.active_object
    p.scale = (1, 1, 0.35); p.data.materials.append(_plain("dust", powder, 0.95)); p.name = "dust"
    d = p.modifiers.new("l", "DISPLACE"); t = bpy.data.textures.new("dustl", "CLOUDS"); t.noise_scale = 0.004; d.texture = t; d.strength = 0.002
    return b


def _spot(loc, target, energy, size=0.1, color=(1.0, 0.86, 0.68), spot=40):
    d = bpy.data.lights.new("pool", 'SPOT'); d.energy = energy; d.color = color; d.spot_size = math.radians(spot); d.spot_blend = 0.6
    d.shadow_soft_size = size
    lo = bpy.data.objects.new("pool", d); bpy.context.scene.collection.objects.link(lo); lo.location = loc
    lo.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return lo


def _haze(center, size, density=0.02, color=(0.9, 0.9, 0.92)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center); o = bpy.context.active_object; o.scale = size; o.name = "haze"
    m = bpy.data.materials.new("haze"); m.use_nodes = True; N = m.node_tree.nodes; N.remove(N["Principled BSDF"])
    v = N.new("ShaderNodeVolumePrincipled"); v.inputs['Density'].default_value = density; v.inputs['Color'].default_value = (*color, 1)
    v.inputs['Anisotropy'].default_value = 0.5
    m.node_tree.links.new(v.outputs[0], N["Material Output"].inputs['Volume']); o.data.materials.append(m); o.visible_shadow = False
    return o


def _bone_detail(obj):
    """Archaeological bone surface on the smooth femur model: fine pores, lengthwise grain, patchy darker staining."""
    for i, m0 in enumerate(obj.data.materials):
        if not m0 or not m0.use_nodes:
            continue
        m = m0.copy(); obj.data.materials[i] = m
        N = m.node_tree.nodes; Lk = m.node_tree.links; p = [n for n in N if n.type == 'BSDF_PRINCIPLED']
        if not p:
            continue
        p = p[0]; tc = N.new("ShaderNodeTexCoord")
        mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (40.0, 40.0, 4.0); Lk.new(tc.outputs['Object'], mp.inputs['Vector'])
        gr = N.new("ShaderNodeTexNoise"); gr.inputs['Scale'].default_value = 30; gr.inputs['Detail'].default_value = 10; Lk.new(mp.outputs[0], gr.inputs['Vector'])
        po = N.new("ShaderNodeTexVoronoi"); po.inputs['Scale'].default_value = 1400; Lk.new(tc.outputs['Object'], po.inputs['Vector'])
        pm = N.new("ShaderNodeMapRange"); pm.inputs['From Min'].default_value = 0.0; pm.inputs['From Max'].default_value = 0.25; Lk.new(po.outputs['Distance'], pm.inputs['Value'])
        h = N.new("ShaderNodeMath"); h.operation = 'MULTIPLY'; Lk.new(gr.outputs['Fac'], h.inputs[0]); Lk.new(pm.outputs[0], h.inputs[1])
        bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.6; bp.inputs['Distance'].default_value = 0.0008; Lk.new(h.outputs[0], bp.inputs['Height'])
        if p.inputs['Normal'].links:
            Lk.new(p.inputs['Normal'].links[0].from_socket, bp.inputs['Normal'])
        Lk.new(bp.outputs['Normal'], p.inputs['Normal'])
        st = N.new("ShaderNodeTexNoise"); st.inputs['Scale'].default_value = 14; st.inputs['Detail'].default_value = 6; Lk.new(tc.outputs['Object'], st.inputs['Vector'])
        sm = N.new("ShaderNodeMapRange"); sm.inputs['From Min'].default_value = 0.45; sm.inputs['From Max'].default_value = 0.7
        sm.inputs['To Min'].default_value = 0.0; sm.inputs['To Max'].default_value = 0.55; Lk.new(st.outputs['Fac'], sm.inputs['Value'])
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; Lk.new(sm.outputs[0], mx.inputs['Factor'])
        if p.inputs['Base Color'].links:
            Lk.new(p.inputs['Base Color'].links[0].from_socket, mx.inputs[6])
        else:
            mx.inputs[6].default_value = p.inputs['Base Color'].default_value
        mx.inputs[7].default_value = (0.32, 0.22, 0.12, 1)
        hs = N.new("ShaderNodeHueSaturation"); hs.inputs['Saturation'].default_value = 0.55; hs.inputs['Value'].default_value = 1.08
        Lk.new(mx.outputs[2], hs.inputs['Color']); Lk.new(hs.outputs[0], p.inputs['Base Color'])          # ivory-grey bone, not tan
        p.inputs['Roughness'].default_value = 0.8
        if 'Subsurface Weight' in p.inputs:
            p.inputs['Subsurface Weight'].default_value = 0.0      # SSS made it read as flesh


def _etch(obj, strength=1.0):
    """Acid-etched bone surface: chalky, paler, pitted (mineral lost from the surface)."""
    for m in obj.data.materials:
        if not m or not m.use_nodes:
            continue
        N = m.node_tree.nodes; Lk = m.node_tree.links; p = [n for n in N if n.type == 'BSDF_PRINCIPLED']
        if not p:
            continue
        p = p[0]
        tc = N.new("ShaderNodeTexCoord")
        vo = N.new("ShaderNodeTexVoronoi"); vo.inputs['Scale'].default_value = 900; Lk.new(tc.outputs['Object'], vo.inputs['Vector'])
        nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 120; nz.inputs['Detail'].default_value = 8; Lk.new(tc.outputs['Object'], nz.inputs['Vector'])
        pit = N.new("ShaderNodeMapRange"); pit.inputs['From Min'].default_value = 0.0; pit.inputs['From Max'].default_value = 0.35
        Lk.new(vo.outputs['Distance'], pit.inputs['Value'])
        # pits come in eroded patches, of mixed sizes, with smoother bone between
        vo2 = N.new("ShaderNodeTexVoronoi"); vo2.inputs['Scale'].default_value = 320; Lk.new(tc.outputs['Object'], vo2.inputs['Vector'])
        pit2 = N.new("ShaderNodeMapRange"); pit2.inputs['From Min'].default_value = 0.0; pit2.inputs['From Max'].default_value = 0.3
        Lk.new(vo2.outputs['Distance'], pit2.inputs['Value'])
        both = N.new("ShaderNodeMath"); both.operation = 'MINIMUM'; Lk.new(pit.outputs[0], both.inputs[0]); Lk.new(pit2.outputs[0], both.inputs[1])
        patch = N.new("ShaderNodeTexNoise"); patch.inputs['Scale'].default_value = 25; patch.inputs['Detail'].default_value = 4; Lk.new(tc.outputs['Object'], patch.inputs['Vector'])
        pmask = N.new("ShaderNodeMapRange"); pmask.inputs['From Min'].default_value = 0.5; pmask.inputs['From Max'].default_value = 0.62
        pmask.inputs['To Min'].default_value = 1.0; pmask.inputs['To Max'].default_value = 0.0; Lk.new(patch.outputs['Fac'], pmask.inputs['Value'])
        keep = N.new("ShaderNodeMath"); keep.operation = 'MAXIMUM'; Lk.new(both.outputs[0], keep.inputs[0]); Lk.new(pmask.outputs[0], keep.inputs[1])
        h = N.new("ShaderNodeMath"); h.operation = 'MULTIPLY'; Lk.new(keep.outputs[0], h.inputs[0]); Lk.new(nz.outputs['Fac'], h.inputs[1])
        bm_ = N.new("ShaderNodeBump"); bm_.inputs['Strength'].default_value = 0.9 * strength; bm_.inputs['Distance'].default_value = 0.0006
        Lk.new(h.outputs[0], bm_.inputs['Height'])
        if p.inputs['Normal'].links:
            Lk.new(p.inputs['Normal'].links[0].from_socket, bm_.inputs['Normal'])
        Lk.new(bm_.outputs['Normal'], p.inputs['Normal'])
        if p.inputs['Base Color'].links:
            src = p.inputs['Base Color'].links[0].from_socket
            mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs['Factor'].default_value = 0.35 * strength
            Lk.new(src, mx.inputs[6]); mx.inputs[7].default_value = (0.78, 0.72, 0.62, 1); Lk.new(mx.outputs[2], p.inputs['Base Color'])
            Lk.new(patch.outputs['Fac'], mx.inputs['Factor'])          # chalky where eroded
        p.inputs['Roughness'].default_value = 0.95


# ============================================================================ "To find out what happened..."
def S01():
    """Lab at night: a bone sample in a small glass vial in the lamp pool; the skull soft behind. Slow push."""
    L = p1.lab_skull(inverted=False, lamp_energy=18)
    _vial(-0.1, 0.27, LB.TOP)
    t = Vector((-0.1, 0.27, LB.TOP + 0.035))
    return dict(a=((-0.36, -0.22, LB.TOP + 0.12), tuple(t + Vector((0.04, 0.05, 0)))), b=((-0.27, -0.08, LB.TOP + 0.09), tuple(t + Vector((0.03, 0.04, 0)))),
                lens=60, fstop=2.0, focus=tuple(t), cine=dict(exposure=-0.15))


def S02():
    """Sampling for radiocarbon: a small chip cut from the thigh bone, the dark drill dust in a weighing boat; cold bench
    light. Slider."""
    A = LB.room(window_light=0.25, lamp=True, lamp_at=(0.3, 0.62), lamp_target=(0.05, 0.34), lamp_energy=14)
    _spot((-0.4, 0.1, LB.TOP + 1.1), (0.05, 0.35, LB.TOP), 160, size=0.3, color=(0.75, 0.85, 1.0), spot=50)
    LB.velvet(-0.6, 0.7, 0.0, 0.78, LB.TOP)
    fe, W = p1.lab_femur(); _bone_detail(fe)
    end = W[W[:, 0] > np.percentile(W[:, 0], 85)]
    cx = float(end[:, 0].mean()); cy = float(end[:, 1].mean())
    _boat(cx - 0.02, cy - 0.16, LB.TOP)
    # the chip itself, lying on the velvet beside the bone
    bpy.ops.mesh.primitive_cube_add(size=0.012, location=(cx + 0.06, cy - 0.11, LB.TOP + 0.004)); ch = bpy.context.active_object
    ch.scale = (1.2, 0.8, 0.45); ch.rotation_euler.z = 0.5; ch.name = "chip"; ch.data.materials.append(fe.data.materials[0])
    bv = ch.modifiers.new("b", "BEVEL"); bv.width = 0.0012
    t = Vector((cx - 0.03, cy - 0.08, LB.TOP + 0.01))
    f = Vector((cx - 0.02, cy - 0.16, LB.TOP + 0.004))            # the weighing boat
    return dict(a=(tuple(t + Vector((-0.32, -0.34, 0.3))), tuple(t)), b=(tuple(t + Vector((-0.18, -0.4, 0.28))), tuple(t + Vector((0.02, 0, 0)))),
                lens=50, fstop=5.6, focus=tuple(f), cine=dict(exposure=0.05))


def S03():
    """The accelerator hall: a long stainless beamline in blue half-dark, magnets, the sample wheel at the ion source.
    Low dolly along the beamline."""
    H = P2.ams_hall()
    _haze((2, 0, 4), (40, 14, 8), density=0.006, color=(0.8, 0.88, 1.0))
    z = H["beam_z"]
    _spot((-4.0, -3.0, 6.5), (-5.5, 0, z), 900, size=0.4, color=(0.75, 0.85, 1.0), spot=35)      # a pool on the tank
    return dict(a=((15.0, -1.7, z + 0.45), (-4.0, 0.0, z + 0.3)), b=((12.0, -1.6, z + 0.4), (-5.0, 0.0, z + 0.4)), lens=35,
                fstop=4.0, focus=(6.0, 0, z), cine=dict(exposure=-0.2))


def S04():
    """The three parts on one long dark bench, each in its own pool of light, far apart. Lateral track."""
    A = LB.room(window_light=0.03, lamp=False)
    if A.get("microscope") is not None:                  # nothing on the bench but the three parts
        for o in [A["microscope"]] + list(A["microscope"].children_recursive):
            bpy.data.objects.remove(o)
    LB.velvet(-2.0, 2.0, 0.0, 0.78, LB.TOP)
    cr = B.hero_cranium(healed=True, tone="A")
    co = np.array([v.co for v in cr.data.vertices]); cr.location = (-1.1, 0.42, LB.TOP + 0.004 - co[:, 2].min() * 0.97)
    cr.rotation_euler = (0, 0, math.radians(-30))
    md = B.hero_mandible(tone="B")
    co = np.array([v.co for v in md.data.vertices]); md.location = (0.0, 0.38, LB.TOP + 0.003 - co[:, 2].min())
    md.rotation_euler = (0, 0, math.radians(-15))
    p1.lab_femur(x=1.25, y=0.4, yaw=75)
    for x in (-1.1, 0.0, 1.25):
        _spot((x - 0.1, 0.3, LB.TOP + 1.4), (x, 0.38, LB.TOP), 420, size=0.1, spot=24)
    _haze((0, 0, 1.6), (9, 6, 3.2), density=0.02, color=(0.95, 0.9, 0.85))
    # low along the bench: skull near, jaw in the middle, thigh bone far - three pools receding into the dark
    return dict(a=((-2.6, -0.55, LB.TOP + 0.42), (0.3, 0.42, LB.TOP + 0.02)), b=((-1.9, -0.6, LB.TOP + 0.42), (1.0, 0.42, LB.TOP + 0.02)), lens=40,
                fstop=5.6, focus=(0.0, 0.38, LB.TOP), cine=dict(exposure=0.1))


def _sand_drift(c, size=(60, 60, 0.7), density=0.9):
    """Wind-blown sand: low, streaky streamers racing along the ground (noise stretched downwind along x)."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(c[0], c[1], c[2] + size[2] / 2 - 0.05)); o = bpy.context.active_object
    o.name = "sanddrift"; o.scale = size
    m = bpy.data.materials.new("sanddrift"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; N.remove(N["Principled BSDF"])
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Generated'], sep.inputs[0])
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (3.0, 40.0, 14.0); L.new(tc.outputs['Generated'], mp.inputs['Vector'])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 1.5; nz.inputs['Detail'].default_value = 6; nz.inputs['Distortion'].default_value = 0.6
    L.new(mp.outputs[0], nz.inputs['Vector'])
    st = N.new("ShaderNodeMapRange"); st.inputs['From Min'].default_value = 0.52; st.inputs['From Max'].default_value = 0.7; L.new(nz.outputs['Fac'], st.inputs['Value'])
    fz = N.new("ShaderNodeMapRange"); fz.inputs['From Min'].default_value = 0.0; fz.inputs['From Max'].default_value = 1.0
    fz.inputs['To Min'].default_value = 1.0; fz.inputs['To Max'].default_value = 0.0; L.new(sep.outputs['Z'], fz.inputs['Value'])
    p2 = N.new("ShaderNodeMath"); p2.operation = 'POWER'; p2.inputs[1].default_value = 2.5; L.new(fz.outputs[0], p2.inputs[0])
    m1 = N.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; L.new(st.outputs[0], m1.inputs[0]); L.new(p2.outputs[0], m1.inputs[1])
    m2 = N.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'; m2.inputs[1].default_value = density; L.new(m1.outputs[0], m2.inputs[0])
    v = N.new("ShaderNodeVolumePrincipled"); v.inputs['Color'].default_value = (0.85, 0.72, 0.52, 1); v.inputs['Anisotropy'].default_value = 0.5
    L.new(m2.outputs[0], v.inputs['Density']); L.new(v.outputs[0], N["Material Output"].inputs['Volume'])
    o.data.materials.append(m); o.visible_shadow = False
    return o


def S05():
    """Time passing: the open machair over the burial ground before the houses, at dusk - wind driving streamers of sand
    low across the turf, burying, layer on layer. Slow low crane."""
    U.CUT = False
    T = U.island("dusk", grass_at=(2, 4), grass_r=22, n=820, core=4.0, grass_density=260, sun_az=200)
    z = float(U.surface(2, 4))
    _sand_drift((2, 4, z), size=(70, 70, 0.7), density=1.2)
    return dict(a=((10, -6, z + 0.3), (-8, 6, z + 0.25)), b=((9.5, -5.6, z + 0.75), (-8, 6, z + 0.2)), lens=28,
                fstop=5.6, focus=(2, 2, z), cine=dict(exposure=0.3))


def S06():
    """Section crane: from the grave level up through the shell-sand strata to the old house floor above."""
    p1.site("day", grass_at=(2, 18), grass_r=8, kit=False, burials=False, sun_az=178, focus=(2.5, 15.0), core=2.5)
    y = U.DIG["y1"]
    G.section_scan(y, x_center=2.6)
    z = G.H(2.6, y - 1.6)
    return dict(a=((2.2, y - 2.0, z + 0.05), (2.6, y - 1.1, z + 0.05)), b=((2.2, y - 2.1, z + 0.72), (2.6, y - 1.1, z + 0.52)), lens=32,
                fstop=8.0, focus=(2.6, y - 1.1, z + 0.4))


def S07():
    """The dated layers: the section in hard raking light, the camera pushing along the bands. Push."""
    p1.site("golden", grass_at=(5, 18), grass_r=8, kit=False, burials=False, sun_az=170, focus=(4.5, 15.0), core=2.5)
    y = U.DIG["y1"]
    G.section_scan(y, x_center=4.6)
    z = G.H(4.6, y - 1.6)
    # ~55 deg to the face: the whole frame lands on the real section (its end and the trench walls stay out of shot)
    return dict(a=((3.85, y - 2.0, z + 0.45), (4.55, y - 1.02, z + 0.36)), b=((4.05, y - 1.95, z + 0.44), (4.75, y - 1.02, z + 0.36)), lens=45,
                fstop=5.6, focus=(4.4, y - 1.05, z + 0.3))


def S08():
    """Bronze Age at dusk: the roundhouses, the burial ground under them. Drone descent toward the doorways."""
    U.CUT = False
    U.island("dusk", grass_at=(0, 0), grass_r=40, n=820, core=4.0, grass_density=220)
    BR.village(smoke_on=True)
    return dict(a=((38, -26, 26), (0, 0, 4)), b=((24, -16, 9), (0, 1, 5)), lens=30, cine=dict(exposure=0.35))


# ============================================================================ "For a body to be kept that long..."
def S09():
    """The crouched skeleton in its grave, joints still articulated: slider over the knees and elbows."""
    T, sk = p1.site("overcast", grass_at=None, kit=False)
    g = sk["B1"]; c, _ = g.centre(); k = g.part_centre("skull")
    a = c.lerp(k, -0.25)
    return dict(a=(tuple(a + Vector((0.55, -0.5, 0.55))), tuple(a)), b=(tuple(a + Vector((0.2, -0.65, 0.5))), tuple(c)), lens=50,
                fstop=4.0, focus=tuple(a))


def S10():
    """Joints in situ: the hands up at the face, the spine still in order. Macro pull back."""
    T, sk = p1.site("overcast", grass_at=None, kit=False)
    g = sk["B1"]; s = g.part_centre("skull"); t = g.part_centre("thorax")
    m = s.lerp(t, 0.35)
    return dict(a=(tuple(m + Vector((0.18, -0.25, 0.3))), tuple(m)), b=(tuple(m + Vector((0.35, -0.5, 0.6))), tuple(m.lerp(t, 0.3))), lens=60,
                fstop=4.0, focus=tuple(m))


def _level(o):
    """Rotate a photogrammetry patch so its flattest principal axis is vertical (z up), base back at z = 0."""
    co = np.empty(len(o.data.vertices) * 3, np.float32); o.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    c0 = co.mean(0); u, sv, vt = np.linalg.svd((co - c0)[::max(1, len(co) // 20000)], full_matrices=False)
    n = vt[2] if vt[2][2] > 0 else -vt[2]
    R = np.array(Vector(n.tolist()).rotation_difference(Vector((0, 0, 1))).to_matrix())
    co = (co - c0) @ R.T
    co[:, 2] -= co[:, 2].min(); co[:, 0] -= (co[:, 0].min() + co[:, 0].max()) / 2; co[:, 1] -= (co[:, 1].min() + co[:, 1].max()) / 2
    o.data.vertices.foreach_set("co", co.ravel()); o.data.update()
    return co


def S11():
    """Contrast: an animal from the same kind of ground, excavated (a real burial scan): the skeleton has come apart as
    the body rotted. Top-down drift in flat overcast light."""
    U.light("overcast")
    o = _single("d75c134c72a5408a9b66bd04170da311", name="animalburial")
    co = _level(o)
    ext = co.max(0) - co.min(0)
    s_ = 2.2 / max(ext[0], ext[1]); o.scale = (s_, s_, s_); o.rotation_euler.z = math.radians(-14)      # square to the frame
    rr = np.maximum(np.abs(co[:, 0]) / (ext[0] / 2), np.abs(co[:, 1]) / (ext[1] / 2))
    zc = float(np.percentile(co[:, 2], 2)) * s_ - 0.02        # a floor under everything (only seen past the scan's edge)
    zs = float(np.percentile(co[np.abs(co[:, 0]) < ext[0] * 0.25, 2], 50)) * s_      # the burial itself
    # warm the soil toward the machair sand
    for m in o.data.materials:
        N = m.node_tree.nodes; Lk = m.node_tree.links; p = [n for n in N if n.type == 'BSDF_PRINCIPLED']
        if p and p[0].inputs['Base Color'].links:
            src = p[0].inputs['Base Color'].links[0].from_socket
            mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
            Lk.new(src, mx.inputs[6]); mx.inputs[7].default_value = (1.6, 1.25, 0.8, 1); Lk.new(mx.outputs[2], p[0].inputs['Base Color'])
    # the surrounding trench floor, the scan edges sink into it
    sand = ph.texture("dense_sand", scale=1.2, name="trenchsand", tint=(0.36, 0.34, 0.31))
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, zc)); g = bpy.context.active_object; g.data.materials.append(sand)
    return dict(a=((0.08, -0.3, zs + 1.9), (0.0, 0.0, zs)), b=((-0.08, 0.12, zs + 1.65), (0.0, 0.05, zs)), lens=38,
                fstop=8.0, focus=(0, 0, zs), cine=dict(exposure=0.1))


# ============================================================================ "The team looks inside the bones."
def S12():
    """Lab: a binocular microscope under the lamp, a box of thin sections and one slide out beside it. Push to the stage."""
    A = LB.room(window_light=0.3, lamp=True, lamp_at=(0.45, 0.62), lamp_target=(0.0, 0.38), lamp_energy=16)
    mc = _single("2435e338bf7541a4b919e53df50eeeea", height=0.42, name="compound")
    mc.location = (0.0, 0.42, LB.TOP); mc.rotation_euler.z = math.radians(200)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.26, 0.3, LB.TOP + 0.02)); bx = bpy.context.active_object
    bx.scale = (0.09, 0.08, 0.04); bx.data.materials.append(_plain("slidebox", (0.05, 0.05, 0.05), 0.5)); bx.name = "slidebox"
    gl = _glass("slideglass")
    for k in range(9):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.295 + k * 0.009, 0.3, LB.TOP + 0.04)); sl = bpy.context.active_object
        sl.scale = (0.0012, 0.075, 0.026); sl.data.materials.append(gl); sl.name = "slide"
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.14, 0.24, LB.TOP + 0.001)); s1 = bpy.context.active_object
    s1.scale = (0.075, 0.026, 0.0012); s1.data.materials.append(gl); s1.name = "slide"
    bpy.ops.mesh.primitive_cylinder_add(radius=0.008, depth=0.0004, location=(-0.14, 0.24, LB.TOP + 0.0018)); d = bpy.context.active_object
    d.data.materials.append(_plain("section", (0.55, 0.38, 0.18), 0.4)); d.name = "section"
    t = Vector((-0.08, 0.38, LB.TOP + 0.16))
    return dict(a=((-0.95, -0.62, LB.TOP + 0.4), tuple(t)), b=((-0.75, -0.45, LB.TOP + 0.34), tuple(t + Vector((0.02, 0.02, -0.02)))), lens=40,
                fstop=2.8, focus=tuple(t), cine=dict(exposure=-0.1))


def _field(kind, attack=None):
    P2.microscope_field(kind, size=1.0, attack=attack)
    return dict(lens=50, cine=dict(exposure=-0.1, sat=1.0))


def S13():
    """Down the microscope: a ground section of bone in brightfield - osteons, lamellae round each canal, canaliculi,
    lacunae; the round field of view. Slow drift."""
    d = _field("human", attack=0.0)
    d.update(a=((-0.12, -0.06, 3.7), (-0.12, -0.06, 0)), b=((0.05, 0.03, 3.45), (0.05, 0.03, 0)))
    return d


def S14():
    """An animal bone from the same ground: Wedl tunnels branching through the lamellae in foci, stained brown. Drift."""
    d = _field("animal")
    d.update(a=((0.12, -0.1, 3.6), (0.12, -0.1, 0)), b=((-0.04, 0.05, 3.35), (-0.04, 0.05, 0)))
    return d


def S15():
    """Back to the human bone: intact osteons, only a thin band of tunnelling at the outer edge. Drift toward it."""
    d = _field("human")
    d.update(a=((0.0, 0.0, 3.6), (0.0, 0.0, 0)), b=((0.35, 0.03, 3.1), (0.35, 0.03, 0)))
    return d


def S16():
    """The bone itself under the lamp: low macro push along the shaft of the thigh bone, the shaft running across frame."""
    A = LB.room(window_light=0.3, lamp=True, lamp_at=(0.3, 0.62), lamp_target=(0.05, 0.34), lamp_energy=20)
    LB.velvet(-0.6, 0.7, 0.0, 0.78, LB.TOP)
    fe, W = p1.lab_femur(); _bone_detail(fe)
    xm = float(W[:, 0].mean()); mid = W[np.abs(W[:, 0] - xm) < 0.015]
    t = Vector((xm, float(mid[:, 1].mean()), float(mid[:, 2].max()) - 0.004))
    # higher and wider: the whole bone on the velvet, both ends in frame, sliding along it
    return dict(a=(tuple(t + Vector((-0.12, -0.42, 0.32))), tuple(t + Vector((-0.04, 0, -0.01)))), b=(tuple(t + Vector((0.06, -0.42, 0.32))), tuple(t + Vector((0.03, 0, -0.01)))),
                lens=45, fstop=8.0, focus=tuple(t), cine=dict(exposure=-0.05))


def S17():
    """The grave at dusk: slow push toward the skull. They had been mummified."""
    T, sk = p1.site("dusk", grass_at=None, kit=False, sun_az=210)
    s = sk["B2"].part_centre("skull"); t = sk["B2"].part_centre("thorax")
    return dict(a=(tuple(t + Vector((-0.85, -0.95, 1.1))), tuple((s + t) / 2)), b=(tuple(t + Vector((-0.5, -0.58, 0.8))), tuple(s)), lens=45,
                fstop=2.8, focus=tuple(s), cine=dict(exposure=0.35))


# ============================================================================ "...the skin and other soft tissues have disappeared."
def S18():
    """No skin, no tissue: the whole skeleton laid out on the lab bench, seen from straight above; a slow slide from the
    feet up the legs and the pelvis."""
    L = p1.lab_body(osteo=False)
    return dict(a=((-0.55, 0.38, LB.TOP + 0.95), (-0.55, 0.39, LB.TOP)), b=((0.05, 0.38, LB.TOP + 0.95), (0.05, 0.39, LB.TOP)), lens=40,
                fstop=5.6, focus=(0.0, 0.38, LB.TOP), cine=dict(exposure=-0.05))


def S19():
    """Acid erosion: the bone surface pitted and chalky in a hard raking light. Slow slider."""
    A = LB.room(window_light=0.15, lamp=False)
    LB.velvet(-0.6, 0.7, 0.0, 0.78, LB.TOP)
    fe, W = p1.lab_femur(); _bone_detail(fe)
    _etch(fe)
    xm = float(W[:, 0].mean()) + 0.03; mid = W[np.abs(W[:, 0] - xm) < 0.015]
    t = Vector((xm, float(mid[:, 1].mean()), float(mid[:, 2].max()) - 0.003))
    _spot((t.x - 0.5, t.y + 0.35, t.z + 0.06), tuple(t), 90, size=0.02, spot=20)        # grazing light across the surface
    return dict(a=(tuple(t + Vector((-0.06, -0.13, 0.09))), tuple(t)), b=(tuple(t + Vector((0.02, -0.13, 0.09))), tuple(t + Vector((0.02, 0, 0)))),
                lens=90, fstop=11.0, focus=tuple(t), cine=dict(exposure=0.05))


def S20():
    """The machair sand close up: crushed shell, white, pink and grey, among the quartz grains. Low push in the sun."""
    U.light("golden", sun_az=190)
    sand = ph.texture("dense_sand", scale=30.0, name="macrosand", tint=(1.2, 1.1, 0.95))
    bpy.ops.mesh.primitive_plane_add(size=1.2, location=(0, 0, 0)); g = bpy.context.active_object; g.data.materials.append(sand)
    sub = g.modifiers.new("s", "SUBSURF"); sub.levels = 5; sub.render_levels = 5; sub.subdivision_type = 'SIMPLE'
    d = g.modifiers.new("d", "DISPLACE"); t = bpy.data.textures.new("ripple", "CLOUDS"); t.noise_scale = 0.08; d.texture = t; d.strength = 0.003
    rng = random.Random(7)
    cols = [(0.88, 0.85, 0.8), (0.82, 0.6, 0.55), (0.62, 0.6, 0.58), (0.92, 0.88, 0.82), (0.55, 0.42, 0.35), (0.75, 0.66, 0.5)]
    mats = [_plain(f"shell{i}", c, 0.3) for i, c in enumerate(cols)]
    for m in mats:
        pp = m.node_tree.nodes["Principled BSDF"]; pp.inputs['Coat Weight'].default_value = 0.4; pp.inputs['Subsurface Weight'].default_value = 0.2
    bm = bmesh.new()
    for k in range(900):                        # curved shell flakes: pieces of thin spherical caps, ribbed
        big = rng.random() < 0.08
        r = rng.uniform(0.004, 0.009) if big else rng.uniform(0.0012, 0.004)
        x, y = rng.uniform(-0.09, 0.09), rng.uniform(-0.09, 0.22)
        ret = bmesh.ops.create_grid(bm, x_segments=5, y_segments=5, size=r)
        vs = ret['verts']; R = Matrix.Rotation(rng.uniform(0, 6.3), 3, 'Z') @ Matrix.Rotation(rng.uniform(-0.6, 0.6), 3, 'X')
        curv = rng.uniform(0.15, 0.8) / r; mi = rng.randrange(len(mats)); sy = rng.uniform(0.5, 1.0)
        for v in vs:
            px_, py_ = v.co.x, v.co.y * sy
            pz = -curv * (px_ ** 2 + py_ ** 2) * 0.5 + 0.06 * r * math.sin(px_ / r * 9)     # cap + growth ribs
            v.co = R @ Vector((px_, py_, pz)) + Vector((x, y, 0.0008 + r * 0.3))
        for f in {f for v in vs for f in v.link_faces}:
            f.material_index = mi; f.smooth = True
    me = bpy.data.meshes.new("shells"); bm.to_mesh(me); bm.free()
    sh = bpy.data.objects.new("shells", me); bpy.context.scene.collection.objects.link(sh)
    for m in mats:
        me.materials.append(m)
    sol = sh.modifiers.new("t", "SOLIDIFY"); sol.thickness = 0.0004
    # quartz grains
    bm = bmesh.new()
    gcols = [(0.75, 0.68, 0.55), (0.55, 0.5, 0.42), (0.85, 0.8, 0.7), (0.4, 0.33, 0.25), (0.7, 0.55, 0.45)]
    for k in range(16000):
        r = rng.uniform(0.0003, 0.0012); x, y = rng.uniform(-0.09, 0.09), rng.uniform(-0.09, 0.22)
        vs = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)['verts']
        sc_ = Vector((rng.uniform(0.7, 1.3), rng.uniform(0.7, 1.3), rng.uniform(0.6, 1.0)))
        gi = rng.randrange(5)
        for v in vs:
            v.co = Vector((v.co.x * sc_.x, v.co.y * sc_.y, v.co.z * sc_.z)) + Vector((x, y, r * 0.5))
        for f in {f for v in vs for f in v.link_faces}:
            f.material_index = gi
    gme = bpy.data.meshes.new("grains"); bm.to_mesh(gme); bm.free()
    gr = bpy.data.objects.new("grains", gme); bpy.context.scene.collection.objects.link(gr)
    for i, c_ in enumerate(gcols):
        q = _plain(f"grain{i}", c_, 0.35); q.node_tree.nodes["Principled BSDF"].inputs['Transmission Weight'].default_value = 0.25 if i in (0, 2) else 0.0
        gme.materials.append(q)
    return dict(a=((0.0, -0.11, 0.045), (0.0, 0.02, 0.0)), b=((0.0, -0.08, 0.035), (0.0, 0.03, 0.0)), lens=60,
                fstop=32.0, focus=(0.0, -0.02, 0.002), cine=dict(exposure=0.0))


# ============================================================================ "Elsewhere on South Uist, peat bogs..."
def _clear(M, x, y):
    """Keep plants off cleared ground and off steep faces (the cut peat bank)."""
    if any(math.hypot(x - cx, y - cy) < cr for cx, cy, cr in M.get("clear", ())):
        return True
    h = P2.moor_height
    return max(abs(h(M, x + 0.15, y) - h(M, x - 0.15, y)), abs(h(M, x, y + 0.15) - h(M, x, y - 0.15))) > 0.12


def _cotton(M, center, radius, n=2500, seed=1):
    """Cotton grass: thin stems with white tufts, scattered over the moor (one joined mesh)."""
    rng = random.Random(seed)
    bm = bmesh.new()
    patches = [(center[0] + radius * math.sqrt(rng.random()) * math.cos(t_), center[1] + radius * math.sqrt(rng.random()) * math.sin(t_))
               for t_ in [rng.uniform(0, 6.283) for _ in range(max(6, n // 120))]]
    for k in range(n):
        px_, py_ = rng.choice(patches); a = rng.uniform(0, 6.283); r = 2.2 * math.sqrt(rng.random())
        x, y = px_ + r * math.cos(a), py_ + r * math.sin(a)
        z = P2.moor_height(M, x, y)
        if z < M.get("water_z", -9) + 0.03 or _clear(M, x, y):
            continue
        h = rng.uniform(0.16, 0.3); lean = Vector((rng.uniform(-0.05, 0.05) + 0.04, rng.uniform(-0.04, 0.04), 0))     # leaning in the wind
        st = bmesh.ops.create_cone(bm, cap_ends=False, segments=4, radius1=0.0025, radius2=0.0015, depth=h)['verts']
        for v in st:
            v.co = Vector((x, y, z + h / 2)) + v.co + lean * ((v.co.z + h / 2) / h)
        hd = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=rng.uniform(0.011, 0.016))['verts']
        for v in hd:
            v.co = Vector((x, y, z + h)) + lean + Vector((v.co.x * 0.9, v.co.y * 0.9, v.co.z * 1.7 + 0.01))
        for f in {f for v in hd for f in v.link_faces}:
            f.material_index = 1
    me = bpy.data.meshes.new("cotton"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("cottongrass", me); bpy.context.scene.collection.objects.link(o)
    me.materials.append(_plain("stem", (0.12, 0.1, 0.04), 0.8))
    w = _plain("tuft", (0.66, 0.65, 0.62), 0.95); w.node_tree.nodes["Principled BSDF"].inputs['Subsurface Weight'].default_value = 0.2
    w.node_tree.nodes["Principled BSDF"].inputs['Sheen Weight'].default_value = 0.25
    me.materials.append(w)
    return o


def _tussocks(M, center, radius, n=5000, seed=3):
    """Purple moor-grass / deer-grass tussocks: clumps of thin bleached blades, darker at the base (one joined mesh)."""
    rng = random.Random(seed)
    bm = bmesh.new()
    for k in range(n):
        a = rng.uniform(0, 6.283); r = radius * math.sqrt(rng.random())
        x, y = center[0] + r * math.cos(a), center[1] + r * math.sin(a)
        z = P2.moor_height(M, x, y)
        if z < M.get("water_z", -9) + 0.02 or _clear(M, x, y):
            continue
        h0 = rng.uniform(0.18, 0.42); wind = Vector((0.05, 0.01, 0))
        for b_ in range(rng.randint(7, 13)):
            ang = rng.uniform(0, 6.283); sp = rng.uniform(0.0, 0.05); h = h0 * rng.uniform(0.6, 1.1)
            base = Vector((x + sp * math.cos(ang), y + sp * math.sin(ang), z - 0.01))
            out = Vector((math.cos(ang), math.sin(ang), 0)) * rng.uniform(0.05, 0.16) + wind
            w = 0.004
            side = Vector((-math.sin(ang), math.cos(ang), 0)) * w
            pts = [base + out * (t * t) + Vector((0, 0, h * t)) for t in (0.0, 0.5, 1.0)]
            v = [bm.verts.new(pts[0] - side), bm.verts.new(pts[0] + side), bm.verts.new(pts[1] + side * 0.7), bm.verts.new(pts[1] - side * 0.7), bm.verts.new(pts[2])]
            bm.faces.new((v[0], v[1], v[2], v[3])); bm.faces.new((v[3], v[2], v[4]))
    me = bpy.data.meshes.new("tussocks"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("tussocks", me); bpy.context.scene.collection.objects.link(o)
    m = bpy.data.materials.new("moorgrass"); m.use_nodes = True; N = m.node_tree.nodes; Lk = m.node_tree.links; p = N["Principled BSDF"]
    geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(geo.outputs['Position'], sep.inputs[0])
    ob = N.new("ShaderNodeObjectInfo")
    rnd = N.new("ShaderNodeTexNoise"); rnd.inputs['Scale'].default_value = 0.6; tc = N.new("ShaderNodeTexCoord"); Lk.new(tc.outputs['Object'], rnd.inputs['Vector'])
    rp = N.new("ShaderNodeValToRGB"); el = rp.color_ramp.elements
    el[0].position = 0.3; el[0].color = (0.16, 0.13, 0.07, 1); el[1].position = 0.7; el[1].color = (0.36, 0.3, 0.17, 1)
    e = el.new(0.5); e.color = (0.24, 0.17, 0.09, 1)
    Lk.new(rnd.outputs['Fac'], rp.inputs['Fac']); Lk.new(rp.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.7; p.inputs['Subsurface Weight'].default_value = 0.15
    me.materials.append(m)
    return o


def _heather(M, center, radius, n=500, seed=2):
    """Heather clumps (real scan) instanced over the moor, out of the pools."""
    src = _single("109204e9a5c74ec390f374ac62e92196", height=0.35, name="heather_src", hide=True)
    for m in src.data.materials:                  # the scan is in full pink flower: take it to late-season brown
        N = m.node_tree.nodes; Lk = m.node_tree.links; p = [n for n in N if n.type == 'BSDF_PRINCIPLED']
        if not p:
            continue
        p = p[0]; bc = p.inputs['Base Color']
        if "flower" in m.name.lower() or "surface2" in m.name.lower():
            for l_ in list(bc.links):
                Lk.remove(l_)
            bc.default_value = (0.11, 0.065, 0.05, 1)       # spent, rusty flower heads
        elif bc.links:
            sc_ = bc.links[0].from_socket
            hs = N.new("ShaderNodeHueSaturation"); hs.inputs['Saturation'].default_value = 0.3; hs.inputs['Value'].default_value = 0.45
            Lk.new(sc_, hs.inputs['Color']); Lk.new(hs.outputs[0], bc)
        else:
            bc.default_value = (0.07, 0.055, 0.035, 1)
    rng = random.Random(seed)
    col = bpy.data.collections.new("heather"); bpy.context.scene.collection.children.link(col)
    for k in range(n):
        a = rng.uniform(0, 6.283); r = radius * math.sqrt(rng.random())
        x, y = center[0] + r * math.cos(a), center[1] + r * math.sin(a)
        z = P2.moor_height(M, x, y)
        if z < M.get("water_z", -9) + 0.05 or _clear(M, x, y):
            continue
        o = bpy.data.objects.new("heather", src.data); col.objects.link(o)
        s = rng.uniform(0.6, 1.5); o.scale = (s, s, s * rng.uniform(0.7, 1.1)); o.location = (x, y, z - 0.04); o.rotation_euler.z = rng.uniform(0, 6.3)
    return col


def moor(mood="overcast", size=220.0, n=420, cotton=(0, 0, 30, 2500), heather=(0, 0, 25, 400), mist=0.03, sun_az=None, setup=None):
    Lh = U.light(mood, sun_az)
    M = P2.peat_moor(size=size, n=n)
    if setup:
        setup(M)                     # e.g. choose where people stand and keep that ground clear
    if cotton:
        _cotton(M, cotton[:2], cotton[2], n=cotton[3])
        _tussocks(M, cotton[:2], cotton[2], n=int(cotton[3] * 6))
    if heather:
        _heather(M, heather[:2], heather[2], n=heather[3])
    if mist:
        BR.ground_mist((0, 0, 0), size=(size, size, 4.0), density=mist)
    return M


def _moor_tone(terrain):
    """Replace the island material's flat moor colour with varied peat, heather, bleached grass and rusty sphagnum."""
    if terrain is None:
        return
    for m in terrain.data.materials:
        nt = m.node_tree
        for n in nt.nodes:
            if n.type == 'MIX' and n.data_type == 'RGBA' and not n.inputs[7].is_linked:
                c = n.inputs[7].default_value
                if abs(c[0] - 0.09) < 1e-3 and abs(c[1] - 0.075) < 1e-3:
                    tc = nt.nodes.new("ShaderNodeTexCoord")
                    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 0.012; nz.inputs['Detail'].default_value = 8
                    nz.inputs['Roughness'].default_value = 0.65; nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
                    rp = nt.nodes.new("ShaderNodeValToRGB"); el = rp.color_ramp.elements
                    el[0].position = 0.35; el[0].color = (0.03, 0.025, 0.016, 1)
                    e = el.new(0.47); e.color = (0.07, 0.05, 0.03, 1)
                    e = el.new(0.56); e.color = (0.11, 0.05, 0.03, 1)
                    el[1].position = 0.68; el[1].color = (0.15, 0.14, 0.08, 1)
                    nt.links.new(nz.outputs['Fac'], rp.inputs['Fac']); nt.links.new(rp.outputs['Color'], n.inputs[7])
                    return


def S21():
    """Low drone over the peat moor at dusk: black pools holding the sky, a cut peat bank, tussocks and cotton grass,
    mist lying in the hollows, gliding forward a few metres up."""
    M = moor("dusk", size=220, n=480, cotton=(0, -10, 34, 3000), heather=(0, -10, 34, 250), mist=0.035, sun_az=95)
    P2.peat_face(M, -40, 40, stack_at=-6.0)
    z = P2.moor_height(M, 0, -30)
    return dict(a=((-6, -38, z + 8.5), (2, 10, z - 1)), b=((-3, -26, z + 7.5), (4, 18, z - 1)), lens=26, cine=dict(exposure=0.35))


def _bog_scene(mood="dusk", sun_az=None, setup=None):
    M = moor(mood, size=80, n=560, cotton=(0, 0, 18, 2500), heather=(0, 0, 18, 300), mist=0.02, sun_az=sun_az, setup=setup)
    # a black pool in front of the bank at (0, 3): carve the terrain down and set water there
    return M


def _pool_edge(M, near=(0.0, -1.0)):
    """A firm standing spot with open black water 1.5-3.5 m ahead of it (+y)."""
    wz = M["water_z"]; best = None
    for x in np.linspace(-8, 8, 65):
        for y in np.linspace(-8, 3, 45):
            z = P2.moor_height(M, x, y)
            if z < wz + 0.12:
                continue
            firm = all(P2.moor_height(M, x + dx, y + dy) > wz + 0.08 for dx in (-1.2, 0, 1.2) for dy in (-0.8, 0, 0.5))
            wet = sum(P2.moor_height(M, x + dx, y + dy) < wz for dx in (-1, 0, 1) for dy in (1.5, 2.5, 3.5))
            if firm and wet >= 5:
                sc_ = abs(x - near[0]) + abs(y - near[1]) - wet * 0.3
                if best is None or sc_ < best[0]:
                    best = (sc_, x, y, z)
    if best is None:
        return 0.0, 0.0, P2.moor_height(M, 0, 0)
    return best[1:]


def _islander2(name="Islander1"):
    """The second islander: slighter, long fair-brown hair, an undyed pale wool tunic (long), belted."""
    import modern as MD

    class _J(MD.ModernMan):
        GENDER = 0.0; MUSCLE = 0.4; WEIGHT = 0.35; HEIGHT = 0.4
        HAIR = (0.45, 0.25); HAIR_LEN = (0.12, 0.2)
        SHIRT = (0.24, 0.2, 0.15); JACKET = "coat"; JACKET_COL = (0.25, 0.21, 0.15)
        TROUSERS = (0.16, 0.13, 0.09); SHOES = (0.08, 0.05, 0.03)
        TROUSER_EASE = 1.3; TROUSER_EXTRA = 0.03
    return _J(name, years=24)


def _belt(st, col=(0.07, 0.045, 0.025)):
    """A leather belt round the tunic at the waist (from the rig's lower spine)."""
    h = st.m.h
    for b in ("spine04", "spine05", "spine03"):
        if b in h.arm.pose.bones:
            c = st.M @ h.bone_head(b); break
    else:
        return None
    zs = []
    for o in bpy.data.objects:
        if o.name.startswith(st.m.name + "_jacket") and o.type == 'MESH':
            dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg)
            W = np.array([oe.matrix_world @ v.co for v in oe.data.vertices])
            band = W[np.abs(W[:, 2] - c.z) < 0.02]
            if len(band) > 8:
                ctr = band.mean(0); rad = float(np.percentile(np.hypot(band[:, 0] - ctr[0], band[:, 1] - ctr[1]), 90)) + 0.006
                bpy.ops.mesh.primitive_torus_add(major_radius=rad, minor_radius=0.012, location=(ctr[0], ctr[1], c.z)); t = bpy.context.active_object
                t.scale = (1.0, 0.8, 1.6); t.name = st.m.name + "_belt"; t.data.materials.append(_plain("belt", col, 0.6))
                return t
    return None


def S22():
    """Bronze Age, dusk, from behind against the last light: two islanders lowering the hurdle into a black bog pool -
    one kneeling at the edge gripping the near end of a pole, the other on the bank above, knees bent, bracing it; the
    hide-wrapped body bound on the hurdle tipping down toward the water. Slow push."""
    spot = {}
    def setup(M):
        x0, y0, z0 = _pool_edge(M); spot.update(x=x0, y=y0, z=z0)
        M["clear"] = [(x0, y0, 1.6), (x0, y0 + 1.2, 1.2)]
    M = _bog_scene("dusk", sun_az=95, setup=setup)
    x0, y0, z0 = spot["x"], spot["y"], spot["z"]; wz = M["water_z"]
    import acts as AC
    # the hurdle: long axis running out into the pool (+y), near end on the bank edge, far end dipping into the water
    Lh, Wh = 2.0, 0.9
    hx, hy = x0, y0 + 0.2 + Lh / 2
    z_near = z0 + 0.55; z_far = wz - 0.12
    tilt = math.atan2(z_near - z_far, Lh)
    piv = bpy.data.objects.new("hurdle_rig", None); bpy.context.scene.collection.objects.link(piv); piv.location = (hx, hy, (z_near + z_far) / 2)
    before = set(bpy.data.objects)
    P2.hurdle((hx, hy, (z_near + z_far) / 2), rot=math.radians(90), length=Lh, width=Wh)
    P2.bundle((hx, hy, (z_near + z_far) / 2 + 0.22), rot=math.radians(90))
    bpy.context.view_layer.update()
    for o in set(bpy.data.objects) - before:
        mw = o.matrix_world.copy(); o.parent = piv; o.matrix_parent_inverse = piv.matrix_world.inverted()
    piv.rotation_euler.x = -tilt
    bpy.context.view_layer.update()
    def pole(side, d):                        # a point on a pole, d metres from the near end
        x = hx + side * Wh / 2
        return Vector((x, hy - Lh / 2 + d, z_near - (z_near - z_far) * d / Lh + 0.03))
    # islander 1: heavy-set, dark cloak - kneels behind the left pole end, both hands on it
    m1 = BR.Islander(name="Islander0")
    k1 = (hx - Wh / 2 - 0.05, hy - Lh / 2 - 0.55)
    zk = max(P2.moor_height(M, k1[0] + ex, k1[1] + ey) for ex in (-0.2, 0, 0.2) for ey in (-0.3, 0, 0.3)) + 0.01
    st1 = AC.Kneel(m1, k1, 90, lean=38, sit_back=True)
    for sd, d in (("L", 0.12), ("R", 0.42)):
        w = pole(-1, d) - Vector((0, 0, zk)); st1.hand(sd, w, elbow=(0.6, 0.2, -0.8), grip=0.85)
    st1.head_to(tuple(pole(-1, 1.2) - Vector((0, 0, zk))), share=0.8)
    st1.finish(look=tuple(pole(-1, 1.2) - Vector((0, 0, zk))), density=HAIR)
    G.lift(st1, zk)
    # islander 2: slighter, pale belted tunic, long hair - on the bank to the right, one foot forward, bent over the
    # right pole, bracing it with both hands
    m2 = _islander2()
    f2 = (hx + Wh / 2 + 0.12, hy - Lh / 2 - 0.62)
    zs = max(P2.moor_height(M, f2[0] + ex, f2[1] + ey) for ex in (-0.2, 0, 0.2) for ey in (-0.3, 0, 0.3)) + 0.01
    palms = {"L": tuple(pole(1, 0.12) - Vector((0.03, 0, zs + 0.035))), "R": tuple(pole(1, 0.4) - Vector((-0.03, 0, zs + 0.035)))}
    st2 = AC.Lean(m2, f2, 90, palms, lean=42)
    st2.finish(look=tuple(pole(1, 1.3) - Vector((0, 0, zs))), density=HAIR)
    G.lift(st2, zs)
    return dict(a=((x0 + 1.9, y0 - 3.9, z0 + 2.1), (x0, y0 + 1.4, z0 + 0.3)), b=((x0 + 1.6, y0 - 3.2, z0 + 1.95), (x0, y0 + 1.4, z0 + 0.3)),
                lens=35, fstop=4.0, focus=(x0, y0 + 0.3, z0 + 0.6), cine=dict(exposure=0.3), hand_ok=("moor", "hurdle", "bundle", "belt"))


def _pool_spot(M, near=(0.0, 0.0), margin=0.6):
    """The centre of open water nearest `near`: low ground at least 0.6 m from any bank."""
    wz = M["water_z"]; best = None
    for x in np.linspace(-10, 10, 81):
        for y in np.linspace(-10, 5, 61):
            if all(P2.moor_height(M, x + dx, y + dy) < wz - 0.04 for dx in (-margin, 0, margin) for dy in (-margin, 0, margin)) and \
                    any(P2.moor_height(M, x + dx, y + dy) > wz + 0.05 for dx in (-1.4, 0, 1.4) for dy in (-1.4, 0, 1.4)):
                d = math.hypot(x - near[0], y - near[1])
                if best is None or d < best[0]:
                    best = (d, x, y)
    return (best[1], best[2]) if best else near


def _moss(M, px, py, wz, n=110, seed=23):
    """Sphagnum cushions round a pool margin: low lumpy mounds, green to rust-red, densely bumpy (capitula)."""
    rng = random.Random(seed)
    m = bpy.data.materials.get("sphagnum")
    if m is None:
        m = bpy.data.materials.new("sphagnum"); m.use_nodes = True; N = m.node_tree.nodes; Lk = m.node_tree.links; p = N["Principled BSDF"]
        tc = N.new("ShaderNodeTexCoord")
        nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 5; Lk.new(tc.outputs['Object'], nz.inputs['Vector'])
        rp = N.new("ShaderNodeValToRGB"); el = rp.color_ramp.elements
        el[0].position = 0.4; el[0].color = (0.05, 0.08, 0.02, 1); e = el.new(0.55); e.color = (0.1, 0.1, 0.03, 1)
        el[1].position = 0.7; el[1].color = (0.12, 0.035, 0.02, 1)
        Lk.new(nz.outputs['Fac'], rp.inputs['Fac']); Lk.new(rp.outputs['Color'], p.inputs['Base Color'])
        vo = N.new("ShaderNodeTexVoronoi"); vo.inputs['Scale'].default_value = 160; Lk.new(tc.outputs['Object'], vo.inputs['Vector'])
        bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 1.0; bp.inputs['Distance'].default_value = 0.004
        Lk.new(vo.outputs['Distance'], bp.inputs['Height']); Lk.new(bp.outputs['Normal'], p.inputs['Normal'])
        p.inputs['Roughness'].default_value = 0.55; p.inputs['Subsurface Weight'].default_value = 0.1
    for k in range(n):
        a = rng.uniform(0, 6.283); r = rng.uniform(0.7, 1.7)
        x, y = px + r * math.cos(a), py + r * math.sin(a)
        z = max(P2.moor_height(M, x, y), wz + 0.01)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0, location=(x, y, z - 0.005)); o = bpy.context.active_object
        rr = rng.uniform(0.08, 0.2); o.scale = (rr * rng.uniform(0.8, 1.5), rr, rr * 0.22); o.rotation_euler.z = rng.uniform(0, 6.3); o.name = "moss"
        d = o.modifiers.new("lump", "DISPLACE"); t = bpy.data.textures.get("mosslump") or bpy.data.textures.new("mosslump", "CLOUDS")
        t.noise_scale = 0.06; d.texture = t; d.strength = 0.03
        o.data.materials.append(m)


def S23():
    """From the peat bank, looking down and out over the pool at dusk: the hide-wrapped body half-sunk in the brown
    water, the sky reflected round it; cotton grass and tussocks soft in the foreground. Slow push."""
    M = _bog_scene("dusk", sun_az=95)
    wz = M["water_z"]
    bx, by = _pool_spot(M, margin=0.45)
    P2.bundle((bx, by, wz - 0.09), rot=math.radians(70))
    # the bank: the firm ground nearest the bundle on its south side (so the low sun is ahead, over the water)
    best = None
    for r in np.linspace(1.2, 3.5, 12):
        for a in np.linspace(math.radians(200), math.radians(340), 15):
            x, y = bx + r * math.cos(a), by + r * math.sin(a)
            if all(P2.moor_height(M, x + dx, y + dy) > wz + 0.12 for dx in (-0.3, 0, 0.3) for dy in (-0.3, 0, 0.3)):
                if best is None or r < best[0]:
                    best = (r, x, y, a)
    if best is None:
        best = (2.5, bx, by - 2.5, math.radians(270))
    r, cx, cy, a = best
    back = Vector((math.cos(a), math.sin(a), 0)) * 0.9
    cz = P2.moor_height(M, cx, cy)
    c0 = Vector((cx, cy, cz + 1.15)) + back
    c1 = Vector((cx, cy, cz + 1.0)) + back * 0.4
    return dict(a=(tuple(c0), (bx, by, wz)), b=(tuple(c1), (bx, by, wz)), lens=35,
                fstop=4.0, focus=(bx, by, wz), cine=dict(exposure=0.35))


def S24():
    """Later: cold low sun on the same bog; the empty hurdle and its ropes laid out on the bank. Crane."""
    M = _bog_scene("dawn", sun_az=120)
    P2.peat_face(M, -15, 15)
    z = P2.moor_height(M, 0, 7.5)
    P2.hurdle((0, 7.5, z + 0.02), rot=math.radians(10))
    return dict(a=((-2.5, 3.2, z + 1.0), (0, 7.5, z)), b=((-2.2, 3.6, z + 2.4), (0, 7.5, z)), lens=32,
                fstop=5.6, focus=(0, 7.5, z), cine=dict(exposure=0.2))


def S25():
    """A cut peat bank: dark fibrous layers, water seeping at the foot. Slider along the face."""
    M = _bog_scene("overcast")
    P2.peat_face(M, -12, 12)
    z = P2.moor_height(M, 0, 5.4)
    return dict(a=((-1.5, 3.4, z + 0.5), (-0.5, 6.0, z + 0.5)), b=((1.0, 3.4, z + 0.5), (2.0, 6.0, z + 0.5)), lens=35,
                fstop=5.6, focus=(0.5, 5.9, z + 0.5), cine=dict(exposure=0.45))


# ============================================================================ "Nobody has found a written instruction..."
def S26():
    """The empty moor at dusk, cotton grass in the wind, the pools holding the sky. Low drone drift."""
    M = moor("dusk", size=220, n=460, cotton=(0, 0, 26, 3000), heather=(0, 0, 26, 250), mist=0.03, sun_az=250)
    z = P2.moor_height(M, 0, -10)
    return dict(a=((-10, -18, z + 1.6), (6, 20, z)), b=((-5, -16, z + 1.4), (10, 20, z)), lens=24, fstop=8.0, focus=(0, 0, z),
                cine=dict(exposure=0.35))


def S27():
    """The skull in the lab under the lamp: slow push. The bones record the result."""
    L = p1.lab_skull(inverted=False, lamp_energy=20)
    c = Vector((0.0, 0.35, LB.TOP + 0.09))
    return dict(a=((0.45, -0.25, LB.TOP + 0.2), tuple(c)), b=((0.3, -0.12, LB.TOP + 0.16), tuple(c)), lens=50,
                fstop=2.8, focus=tuple(c), cine=dict(exposure=-0.15))


def S28():
    """Pull back from the trench to the island at dusk: low over the excavation (house rings, graves, baulks, spoil,
    marquee, cabin), rising and pulling away until the dig is a scar on the machair, the dunes and the Atlantic beyond."""
    p1.site("dusk", grass_at=(4, 0), grass_r=55, focus=(0, 0), core=6.0, n=900, kit=True, burials=True, sun_az=230, grass_density=260)
    return dict(a=((9, -12, 9.5), (-1, 4, 3.6)), b=((95, -135, 70), (-60, 30, 0)), lens=28, cine=dict(exposure=0.3))


VO = [l.strip() for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "vo", "MUMMY_P2_VO.txt"),
                               encoding="utf-8").read().split("\n") if l.strip()]

PLAN = [  # shot, VO paragraph (1-based), seconds (at 133 wpm; re-timed to the recorded VO), description
    ("S01", 1, 5.0, "Lab at night: a bone sample in a glass vial; the skull soft behind (push)"),
    ("S02", 2, 4.5, "Radiocarbon sampling: a chip from the thigh bone, drill dust in a weighing boat"),
    ("S03", 2, 5.5, "The accelerator hall: dolly along the beamline in the half-dark"),
    ("S04", 2, 6.0, "Skull, jaw and thigh bone far apart on one dark bench, each in its own pool of light"),
    ("S05", 2, 5.0, "Time passing on the machair: sand blowing over the burial ground at dusk"),
    ("S06", 2, 5.5, "Crane up the section from the grave level to the house floor"),
    ("S07", 3, 6.0, "The dated layers in raking light (push along the section)"),
    ("S08", 3, 6.0, "Bronze Age at dusk: drone descent toward the roundhouses"),
    ("S09", 4, 4.5, "The crouched skeleton: joints still articulated (slider)"),
    ("S10", 5, 6.0, "Hands at the face, spine in order: macro pull back"),
    ("S11", 5, 6.0, "An animal skeleton from the same sand, top-down"),
    ("S12", 6, 3.5, "Lab: the microscope and a box of thin sections (push)"),
    ("S13", 7, 5.0, "Down the microscope: a bone section, osteon rings in transmitted light"),
    ("S14", 7, 6.0, "Animal bone section riddled with bacterial tunnels"),
    ("S15", 8, 5.0, "The human section: clean rings, a thin band of damage at the edge"),
    ("S16", 8, 5.0, "Macro along the thigh bone under the lamp"),
    ("S17", 9, 5.0, "The grave at dusk, slow push to the skull: mummified"),
    ("S18", 10, 6.0, "No soft tissue left: the whole skeleton on the lab bench from above (slide)"),
    ("S19", 11, 5.0, "Acid-etched bone surface in grazing light"),
    ("S20", 11, 6.0, "Machair sand macro: crushed shell among the grains"),
    ("S21", 12, 5.0, "Aerial: the peat moor, black pools, peat banks, mist"),
    ("S22", 13, 6.0, "Bronze Age dusk: two islanders (backs) at a bog pool, the wrapped body on a hurdle"),
    ("S23", 13, 5.0, "The wrapped bundle half under the black water (top-down)"),
    ("S24", 13, 4.5, "Cold dawn: the empty hurdle on the bank (crane)"),
    ("S25", 13, 5.0, "A cut peat bank: dark layered peat (slider)"),
    ("S26", 14, 6.0, "The empty moor at dusk, cotton grass, pools holding the sky"),
    ("S27", 14, 4.5, "The skull in the lab under the lamp (push)"),
    ("S28", 14, 7.0, "Pull back from the dig to the island at dusk"),
]
SHOTS = {sid: dict(fn=globals()[sid], dur=d, vo=VO[min(ln, len(VO)) - 1], line=ln, desc=desc) for sid, ln, d, desc in PLAN}
