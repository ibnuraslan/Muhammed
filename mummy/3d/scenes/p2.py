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
        h = N.new("ShaderNodeMath"); h.operation = 'MULTIPLY'; Lk.new(pit.outputs[0], h.inputs[0]); Lk.new(nz.outputs['Fac'], h.inputs[1])
        bm_ = N.new("ShaderNodeBump"); bm_.inputs['Strength'].default_value = 0.9 * strength; bm_.inputs['Distance'].default_value = 0.0006
        Lk.new(h.outputs[0], bm_.inputs['Height'])
        if p.inputs['Normal'].links:
            Lk.new(p.inputs['Normal'].links[0].from_socket, bm_.inputs['Normal'])
        Lk.new(bm_.outputs['Normal'], p.inputs['Normal'])
        if p.inputs['Base Color'].links:
            src = p.inputs['Base Color'].links[0].from_socket
            mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs['Factor'].default_value = 0.35 * strength
            Lk.new(src, mx.inputs[6]); mx.inputs[7].default_value = (0.78, 0.72, 0.62, 1); Lk.new(mx.outputs[2], p.inputs['Base Color'])
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
    _spot((-0.4, 0.1, LB.TOP + 1.1), (0.05, 0.35, LB.TOP), 60, size=0.3, color=(0.75, 0.85, 1.0), spot=50)
    LB.velvet(-0.6, 0.7, 0.0, 0.78, LB.TOP)
    fe, W = p1.lab_femur()
    end = W[W[:, 0] > np.percentile(W[:, 0], 85)]
    cx = float(end[:, 0].mean()); cy = float(end[:, 1].mean())
    _boat(cx - 0.02, cy - 0.16, LB.TOP)
    # the chip itself, lying on the velvet beside the bone
    bpy.ops.mesh.primitive_cube_add(size=0.012, location=(cx + 0.06, cy - 0.11, LB.TOP + 0.004)); ch = bpy.context.active_object
    ch.scale = (1.2, 0.8, 0.45); ch.rotation_euler.z = 0.5; ch.name = "chip"; ch.data.materials.append(fe.data.materials[0])
    bv = ch.modifiers.new("b", "BEVEL"); bv.width = 0.0012
    t = Vector((cx, cy - 0.1, LB.TOP + 0.01))
    return dict(a=(tuple(t + Vector((-0.24, -0.22, 0.14))), tuple(t)), b=(tuple(t + Vector((-0.1, -0.29, 0.13))), tuple(t + Vector((0.02, 0, 0)))),
                lens=60, fstop=3.5, focus=tuple(t), cine=dict(exposure=-0.1))


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
    A = LB.room(window_light=0.12, lamp=False)
    LB.velvet(-2.0, 2.0, 0.0, 0.78, LB.TOP)
    cr = B.hero_cranium(healed=True, tone="A")
    co = np.array([v.co for v in cr.data.vertices]); cr.location = (-1.25, 0.4, LB.TOP + 0.004 - co[:, 2].min() * 0.97)
    cr.rotation_euler = (0, 0, math.radians(-30))
    md = B.hero_mandible(tone="B")
    co = np.array([v.co for v in md.data.vertices]); md.location = (0.0, 0.38, LB.TOP + 0.003 - co[:, 2].min())
    md.rotation_euler = (0, 0, math.radians(-15))
    p1.lab_femur(x=1.25, y=0.38, yaw=12)
    for x in (-1.25, 0.0, 1.25):
        _spot((x - 0.1, 0.3, LB.TOP + 1.4), (x, 0.38, LB.TOP), 70, size=0.08, spot=22)
    _haze((0, 0, 1.6), (9, 6, 3.2), density=0.02, color=(0.95, 0.9, 0.85))
    return dict(a=((-1.6, -1.2, LB.TOP + 0.4), (-0.6, 0.38, LB.TOP + 0.05)), b=((0.6, -1.25, LB.TOP + 0.4), (0.6, 0.38, LB.TOP + 0.05)), lens=35,
                fstop=5.6, focus=(0.0, 0.38, LB.TOP), cine=dict(exposure=0.0))


def S05():
    """Time passing on the machair: sand blowing low across the burial ground at dusk, the graves filling. Slow crane."""
    T, sk = p1.site("dusk", grass_at=(0, 6), grass_r=14, kit=False, sun_az=200)
    BR.ground_mist((0, 6, float(U.surface(0, 6))), size=(60, 60, 1.2), density=0.08)
    c = U.PITS["B1"]; z = G.H(c[0], c[1])
    return dict(a=((4.5, 3.5, z + 0.5), (c[0], c[1] + 1.5, z - 0.3)), b=((4.2, 3.6, z + 1.6), (c[0], c[1] + 1.5, z - 0.4)), lens=28,
                fstop=5.6, focus=(c[0], c[1], z), cine=dict(exposure=0.25))


def S06():
    """Section crane: from the grave level up through the shell-sand strata to the old house floor above."""
    p1.site("day", grass_at=(2, 18), grass_r=8, kit=False, burials=False, sun_az=178, focus=(2.5, 15.0), core=2.5)
    y = U.DIG["y1"]
    G.section_scan(y, x_center=2.6)
    z = G.H(2.6, y - 1.6)
    return dict(a=((2.2, y - 2.0, z + 0.05), (2.6, y - 1.1, z + 0.05)), b=((2.2, y - 2.3, z + 1.3), (2.6, y - 1.1, z + 0.9)), lens=32,
                fstop=8.0, focus=(2.6, y - 1.1, z + 0.4))


def S07():
    """The dated layers: the section in hard raking light, the camera pushing along the bands. Push."""
    p1.site("golden", grass_at=(5, 18), grass_r=8, kit=False, burials=False, sun_az=170, focus=(4.5, 15.0), core=2.5)
    y = U.DIG["y1"]
    G.section_scan(y, x_center=4.6)
    z = G.H(4.6, y - 1.6)
    return dict(a=((2.6, y - 1.75, z + 0.4), (4.8, y - 1.05, z + 0.3)), b=((3.3, y - 1.5, z + 0.38), (5.2, y - 1.05, z + 0.3)), lens=35,
                fstop=5.6, focus=(4.4, y - 1.1, z + 0.3))


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
    s_ = 2.2 / max(ext[0], ext[1]); o.scale = (s_, s_, s_)
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
    sand = ph.texture("dense_sand", scale=1.2, name="trenchsand", tint=(0.55, 0.48, 0.4))
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, zc)); g = bpy.context.active_object; g.data.materials.append(sand)
    return dict(a=((0.08, -0.3, zs + 1.9), (0.0, 0.0, zs)), b=((-0.08, 0.12, zs + 1.65), (0.0, 0.05, zs)), lens=45,
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
    return dict(lens=50, cine=dict(exposure=-0.2, sat=1.05))


def S13():
    """Down the microscope: a cross-section of bone in transmitted light - osteons, rings round their canals. Slow drift."""
    d = _field("human", attack=0.0)
    d.update(a=((-0.12, -0.08, 2.05), (-0.12, -0.08, 0)), b=((0.06, 0.02, 1.95), (0.06, 0.02, 0)))
    return d


def S14():
    """An animal bone from the same ground: the section riddled with dark bacterial tunnelling. Drift."""
    d = _field("animal")
    d.update(a=((0.1, -0.12, 2.0), (0.1, -0.12, 0)), b=((-0.05, 0.04, 1.9), (-0.05, 0.04, 0)))
    return d


def S15():
    """Back to the human bone: clean rings, only a thin band of damage at the edge. Drift toward the edge."""
    d = _field("human")
    d.update(a=((0.0, 0.0, 2.05), (0.0, 0.0, 0)), b=((0.32, 0.0, 1.6), (0.32, 0.0, 0)))
    return d


def S16():
    """The bone itself under the lamp: macro push along the shaft of the thigh bone."""
    A = LB.room(window_light=0.3, lamp=True, lamp_at=(0.3, 0.62), lamp_target=(0.05, 0.34), lamp_energy=20)
    LB.velvet(-0.6, 0.7, 0.0, 0.78, LB.TOP)
    fe, W = p1.lab_femur()
    t = Vector((float(W[:, 0].mean()), float(W[:, 1].mean()), float(W[:, 2].max()) - 0.01))
    return dict(a=(tuple(t + Vector((-0.2, -0.16, 0.07))), tuple(t)), b=(tuple(t + Vector((-0.1, -0.13, 0.05))), tuple(t + Vector((0.03, 0, 0)))),
                lens=85, fstop=4.0, focus=tuple(t), cine=dict(exposure=-0.1))


def S17():
    """The grave at dusk: slow push toward the skull. They had been mummified."""
    T, sk = p1.site("dusk", grass_at=None, kit=False, sun_az=210)
    s = sk["B2"].part_centre("skull"); t = sk["B2"].part_centre("thorax")
    return dict(a=(tuple(t + Vector((-0.9, -1.0, 0.7))), tuple((s + t) / 2)), b=(tuple(t + Vector((-0.55, -0.62, 0.42))), tuple(s)), lens=45,
                fstop=2.8, focus=tuple(s), cine=dict(exposure=0.35))


# ============================================================================ "...the skin and other soft tissues have disappeared."
def S18():
    """Clean bone: the end of the thigh bone, smooth, no tissue. Slider in the lamp."""
    A = LB.room(window_light=0.3, lamp=True, lamp_at=(0.5, 0.6), lamp_target=(0.2, 0.36), lamp_energy=20)
    LB.velvet(-0.6, 0.7, 0.0, 0.78, LB.TOP)
    fe, W = p1.lab_femur()
    end = W[W[:, 0] > np.percentile(W[:, 0], 90)]
    t = Vector(end.mean(0).tolist())
    return dict(a=(tuple(t + Vector((0.05, -0.22, 0.1))), tuple(t)), b=(tuple(t + Vector((0.16, -0.18, 0.1))), tuple(t)), lens=70,
                fstop=4.0, focus=tuple(t), cine=dict(exposure=-0.1))


def S19():
    """Acid erosion: the bone surface pitted and chalky in a hard raking light. Slow slider."""
    A = LB.room(window_light=0.15, lamp=False)
    LB.velvet(-0.6, 0.7, 0.0, 0.78, LB.TOP)
    fe, W = p1.lab_femur()
    _etch(fe)
    t = Vector((float(W[:, 0].mean()) + 0.04, float(W[:, 1].mean()), float(W[:, 2].max()) - 0.008))
    _spot((t.x - 0.7, t.y + 0.25, LB.TOP + 0.12), tuple(t), 40, size=0.02, spot=25)        # grazing light
    return dict(a=(tuple(t + Vector((-0.1, -0.12, 0.05))), tuple(t)), b=(tuple(t + Vector((0.0, -0.13, 0.05))), tuple(t + Vector((0.03, 0, 0)))),
                lens=100, fstop=5.6, focus=tuple(t), cine=dict(exposure=0.0))


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
    for k in range(2200):                       # curved shell flakes: pieces of thin spherical caps, ribbed
        big = rng.random() < 0.08
        r = rng.uniform(0.004, 0.009) if big else rng.uniform(0.0012, 0.004)
        x, y = rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25)
        ret = bmesh.ops.create_grid(bm, x_segments=5, y_segments=5, size=r)
        vs = ret['verts']; R = Matrix.Rotation(rng.uniform(0, 6.3), 3, 'Z') @ Matrix.Rotation(rng.uniform(-0.6, 0.6), 3, 'X')
        curv = rng.uniform(0.5, 1.6) / r; mi = rng.randrange(len(mats)); sy = rng.uniform(0.5, 1.0)
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
    for k in range(6000):
        r = rng.uniform(0.0003, 0.0011); x, y = rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25)
        vs = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)['verts']
        sc_ = Vector((rng.uniform(0.7, 1.3), rng.uniform(0.7, 1.3), rng.uniform(0.6, 1.0)))
        for v in vs:
            v.co = Vector((v.co.x * sc_.x, v.co.y * sc_.y, v.co.z * sc_.z)) + Vector((x, y, r * 0.5))
    gme = bpy.data.meshes.new("grains"); bm.to_mesh(gme); bm.free()
    gr = bpy.data.objects.new("grains", gme); bpy.context.scene.collection.objects.link(gr)
    q = _plain("quartz", (0.75, 0.68, 0.55), 0.35); q.node_tree.nodes["Principled BSDF"].inputs['Transmission Weight'].default_value = 0.3
    gme.materials.append(q)
    return dict(a=((0.0, -0.11, 0.045), (0.0, 0.02, 0.0)), b=((0.0, -0.08, 0.035), (0.0, 0.03, 0.0)), lens=60,
                fstop=32.0, focus=(0.0, -0.02, 0.002), cine=dict(exposure=0.0))


# ============================================================================ "Elsewhere on South Uist, peat bogs..."
def _clear(M, x, y):
    return any(math.hypot(x - cx, y - cy) < cr for cx, cy, cr in M.get("clear", ()))


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
    w = _plain("tuft", (0.9, 0.9, 0.88), 0.9); w.node_tree.nodes["Principled BSDF"].inputs['Subsurface Weight'].default_value = 0.4
    w.node_tree.nodes["Principled BSDF"].inputs['Sheen Weight'].default_value = 1.0
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
        if "Flower" in m.name:
            for l_ in list(bc.links):
                Lk.remove(l_)
            bc.default_value = (0.16, 0.09, 0.08, 1)        # spent, rusty flower heads
        elif bc.links:
            sc_ = bc.links[0].from_socket
            hs = N.new("ShaderNodeHueSaturation"); hs.inputs['Saturation'].default_value = 0.45; hs.inputs['Value'].default_value = 0.5
            Lk.new(sc_, hs.inputs['Color']); Lk.new(hs.outputs[0], bc)
        else:
            c_ = bc.default_value; bc.default_value = (c_[0] * 0.4 + 0.04, c_[1] * 0.4 + 0.035, c_[2] * 0.3 + 0.02, 1)
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
        _tussocks(M, cotton[:2], cotton[2], n=int(cotton[3] * 2.2))
    if heather:
        _heather(M, heather[:2], heather[2], n=heather[3])
    if mist:
        BR.ground_mist((0, 0, 0), size=(size, size, 4.0), density=mist)
    return M


def S21():
    """Aerial: the peat moor inland - black pools, cut peat banks, mist lying in the hollows. Drone drift."""
    M = moor("dusk", size=420, n=480, cotton=None, heather=None, mist=0.03)      # from 70 m up, tufts are sub-pixel
    return dict(a=((-120, -150, 70), (0, 10, 0)), b=((-90, -140, 62), (15, 15, 0)), lens=28, cine=dict(exposure=0.3))


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


def S22():
    """Bronze Age, dusk: two islanders (backs to us, against the last light) at the edge of a black bog pool, a body
    wrapped in a hide on a wattle hurdle at their feet. Slow push."""
    spot = {}
    def setup(M):
        x0, y0, z0 = _pool_edge(M); spot.update(x=x0, y=y0, z=z0)
        M["clear"] = [(x0, y0, 1.0), (x0 - 1.0, y0 - 0.3, 0.8), (x0 + 1.3, y0 - 0.6, 1.3)]
    M = _bog_scene("dusk", sun_az=95, setup=setup)
    x0, y0, z0 = spot["x"], spot["y"], spot["z"]
    import acts as AC
    poses = ((0.0, 0.0, 92, "L", (x0, y0 + 3.0)), (-1.0, -0.3, 112, "R", (x0 + 1.3, y0 - 0.6)))
    for i, (dx, dy, hd, wt, look) in enumerate(poses):
        m = BR.Islander(name=f"Islander{i}")
        zf = max(P2.moor_height(M, x0 + dx + ex, y0 + dy + ey) for ex in (-0.15, 0, 0.15) for ey in (-0.2, 0, 0.2)) + 0.01
        st = AC.Stand(m, (x0 + dx, y0 + dy), hd, weight=wt, lean=4 + 6 * i)
        lz = P2.moor_height(M, *look) - zf
        st.head_to((look[0], look[1], lz), share=0.8)
        st.finish(look=(look[0], look[1], lz), density=HAIR)
        G.lift(st, zf)
        if i == 1:                                   # not twins: the second wears a lighter, greyer cloth
            for o in bpy.data.objects:
                if o.name.startswith(f"Islander{i}_") and o.type == 'MESH' and any(k in o.name for k in ("jacket", "coat", "shirt", "trousers")):
                    for j, ms in enumerate(o.data.materials):
                        if ms:
                            mc = ms.copy(); o.data.materials[j] = mc
                            pp = [n for n in mc.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']
                            if pp:
                                mixn = mc.node_tree.nodes.new("ShaderNodeMix"); mixn.data_type = 'RGBA'; mixn.blend_type = 'MULTIPLY'
                                mixn.inputs['Factor'].default_value = 1.0; mixn.inputs[7].default_value = (0.85, 0.95, 1.0, 1)
                                if pp[0].inputs['Base Color'].links:
                                    mc.node_tree.links.new(pp[0].inputs['Base Color'].links[0].from_socket, mixn.inputs[6])
                                else:
                                    mixn.inputs[6].default_value = pp[0].inputs['Base Color'].default_value
                                mc.node_tree.links.new(mixn.outputs[2], pp[0].inputs['Base Color'])
    hx, hy = x0 + 1.3, y0 - 0.6
    hz = P2.moor_height(M, hx, hy)
    P2.hurdle((hx, hy, hz + 0.01), rot=math.radians(75))
    P2.bundle((hx, hy, hz + 0.25), rot=math.radians(75))
    return dict(a=((x0 - 1.4, y0 - 6.0, z0 + 1.3), (x0 + 0.3, y0 + 2.0, z0 + 0.9)), b=((x0 - 1.1, y0 - 5.0, z0 + 1.25), (x0 + 0.3, y0 + 2.0, z0 + 0.9)),
                lens=32, fstop=4.0, focus=(x0, y0, z0 + 1.0), cine=dict(exposure=0.25), hand_ok=("moor", "hurdle"))


def S23():
    """The wrapped bundle lying half under the black water among the sphagnum. Top-down drift."""
    M = _bog_scene("dusk", sun_az=250)
    wz = M["water_z"]
    b = P2.bundle((0.4, 0.2, wz - 0.12), rot=math.radians(30))
    return dict(a=((0.2, -0.2, wz + 2.6), (0.4, 0.2, wz)), b=((0.55, 0.35, wz + 2.3), (0.4, 0.25, wz)), lens=35,
                fstop=5.6, focus=(0.4, 0.2, wz), cine=dict(exposure=0.35))


def S24():
    """Later: cold low sun on the same bog; the empty hurdle and its ropes laid out on the bank. Crane."""
    M = _bog_scene("dawn", sun_az=120)
    z = P2.moor_height(M, 0, 7.5)
    P2.hurdle((0, 7.5, z + 0.02), rot=math.radians(10))
    return dict(a=((-2.5, 2.0, z + 0.4), (0, 7.5, z)), b=((-2.2, 2.4, z + 2.0), (0, 7.5, z)), lens=32,
                fstop=5.6, focus=(0, 7.5, z), cine=dict(exposure=0.2))


def S25():
    """A cut peat bank: dark fibrous layers, water seeping at the foot. Slider along the face."""
    M = _bog_scene("overcast")
    z = P2.moor_height(M, 0, 5.4)
    return dict(a=((-1.5, 3.4, z + 0.5), (-0.5, 6.0, z + 0.5)), b=((1.0, 3.4, z + 0.5), (2.0, 6.0, z + 0.5)), lens=35,
                fstop=5.6, focus=(0.5, 5.9, z + 0.5))


# ============================================================================ "Nobody has found a written instruction..."
def S26():
    """The empty moor at dusk, cotton grass in the wind, the pools holding the sky. Low drone drift."""
    M = moor("dusk", size=220, n=500, cotton=(0, 0, 30, 6000), heather=(0, 0, 30, 500), mist=0.03, sun_az=250)
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
    """Pull back from the trench to the island at dusk: the dig, the machair, the sea."""
    p1.site("dusk", grass_at=None, focus=(0, 0), core=8.0, n=900, kit=True, burials=False, sun_az=230)
    U.cloud_shadows((0, 0), cover=0.4)
    return dict(a=((14, -16, 12), (0, 4, 3)), b=((120, -170, 90), (-40, 40, 0)), lens=28, cine=dict(exposure=0.3))


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
    ("S18", 10, 6.0, "Clean bone: the end of the thigh bone, no tissue left (slider)"),
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
