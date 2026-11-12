"""Shared helpers for chat B's sets (chapters 3-5 of "The Kidnapper Who Only Played a Radio Jingle").
Cinematic look: one hard directional key, dark negative fill, haze. People are generic MakeHuman figures."""
import math, os
import numpy as np
import bpy
from mathutils import Vector, Matrix
from kit import pbr, box, cyl, haze, emissive, wood, fabric, text_obj, join
from common import area_light, point_at, world_flat, ease
from human import Human, add_asset, reset_pose, pose_walk, pose_sit, _world_verts, reach, fingers_curl
import ph

GEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "generated")
os.makedirs(GEN, exist_ok=True)

SKIN_M = "middleage_lightskinned_male_diffuse.png"
SKIN_F = "middleage_lightskinned_female_diffuse.png"
SKIN_OLD = "old_lightskinned_male_diffuse.png"


# ============================================================================ people
def person(name, gender=1.0, years=40, cloth="male_casualsuit02", hair="short02", hue=0.5, sat=1.0, val=0.35,
           hair_val=0.3, hair_sat=1.0, shoes="shoes02", weight=0.45, height=0.5, skin=None, rough=0.7):
    h = Human(name, gender=gender, years=years, muscle=0.5, weight=weight, height=height, eyelashes="eyelashes01",
              skin=skin or (SKIN_F if gender < 0.5 else (SKIN_OLD if years > 58 else SKIN_M)))
    add_asset(h, "clothes", cloth, hue=hue, sat=sat, val=val, rough=rough)
    add_asset(h, "clothes", shoes, val=0.2, rough=0.4)
    if hair:
        add_asset(h, "hair", hair, val=hair_val, sat=hair_sat, rough=0.45)
    sk = h.skin_mat.node_tree.nodes["Principled BSDF"]
    sk.inputs['Subsurface Weight'].default_value = 0.1
    return h


def ground(h, z=0.0):
    bpy.context.view_layer.update()
    w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
    h.arm.location.z += z - w[:, 2].min(); bpy.context.view_layer.update()


def stand(h, loc, face_z, z=0.0):
    """Standing, arms relaxed. face_z: rotation about Z (0 = facing -Y; pi = facing +Y; pi/2 = facing +X)."""
    pose_walk(h, 0.0, stride=0.0, arm_swing=0.0)
    h.arm.rotation_euler = (0, 0, face_z); h.arm.location = (loc[0], loc[1], 0); bpy.context.view_layer.update()
    ground(h, z)
    arms_down(h)


def seat(h, loc, face_z, seat_z=0.47, lean=12):
    """Seated: the pelvis rests at seat height (thighs level)."""
    reset_pose(h); pose_sit(h, lean=lean)
    h.arm.rotation_euler = (0, 0, face_z); h.arm.location = (loc[0], loc[1], 0); bpy.context.view_layer.update()
    ground(h, 0.0)


def fwd_of(h):
    return (h.arm.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()


def arms_down(h, swing=0.0, phase=0.0):
    M = h.arm.matrix_world.to_3x3(); fwd = (M @ Vector((0, -1, 0))).normalized(); left = (M @ Vector((1, 0, 0))).normalized()
    for sd, sg in (("L", 1), ("R", -1)):
        a = math.radians(swing) * math.sin(2 * math.pi * phase + (math.pi if sd == "L" else 0.0))
        up = (Vector((0, 0, -1)) * math.cos(a) + fwd * math.sin(a) + left * (0.12 * sg)).normalized()
        lo = (up + fwd * (0.25 + 0.15 * max(0.0, math.sin(a)))).normalized()
        h.aim(f"upperarm01.{sd}", up); h.aim(f"upperarm02.{sd}", up)
        h.aim(f"lowerarm01.{sd}", lo); h.aim(f"lowerarm02.{sd}", lo); h.aim(f"wrist.{sd}", lo + left * (0.1 * sg))


def walk_to(h, p0, p1, u, cycles, stride=24, swing=16, z=0.0):
    """Place h walking from p0 to p1 at fraction u (0..1); cycles = number of gait cycles over the path."""
    p0 = Vector(p0); p1 = Vector(p1); d = (p1 - p0)
    face = math.atan2(d.x, -d.y)
    bob = pose_walk(h, (u * cycles) % 1.0, stride=stride, arm_swing=swing)
    p = p0.lerp(p1, u)
    h.arm.rotation_euler = (0, 0, face); h.arm.location = (p.x, p.y, 0); bpy.context.view_layer.update()
    ground(h, z)


def hide_person(h):
    for o in [h.arm] + list(h.parts):
        o.hide_render = True


# ============================================================================ light
def key_spot(loc, target, energy, size_deg=40, color=(1.0, 0.78, 0.52), soft=0.15, blend=0.4, name="Key"):
    d = bpy.data.lights.new(name, 'SPOT'); d.energy = energy; d.spot_size = math.radians(size_deg); d.spot_blend = blend
    d.color = color; d.shadow_soft_size = soft
    o = bpy.data.objects.new(name, d); bpy.context.collection.objects.link(o); o.location = loc; point_at(o, target)
    return o


def key_sun(elev, azim, energy, color=(1.0, 0.78, 0.52), angle=1.0):
    d = bpy.data.lights.new("KeySun", 'SUN'); d.energy = energy; d.color = color; d.angle = math.radians(angle)
    o = bpy.data.objects.new("KeySun", d); bpy.context.collection.objects.link(o)
    o.rotation_euler = (math.radians(90 - elev), 0, math.radians(azim + 90))
    return o


def fill(loc, target, energy, size=2.0, color=(0.55, 0.7, 0.85)):
    l = area_light(loc, (0, 0, 0), size, energy, color); point_at(l, target); l.visible_camera = False
    return l


def practical(loc, energy, color=(1.0, 0.72, 0.42), radius=0.05, name="Practical"):
    d = bpy.data.lights.new(name, 'POINT'); d.energy = energy; d.color = color; d.shadow_soft_size = radius
    o = bpy.data.objects.new(name, d); bpy.context.collection.objects.link(o); o.location = loc
    return o


def room_haze(loc, size, density=0.012, color=(0.9, 0.92, 0.95)):
    return haze(loc, size, density=density, color=color, anis=0.55)


# ============================================================================ materials
def plaster(name, col, rough=0.9, dirt=0.25):
    m = pbr(name, col, rough)
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 8
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    cr = N.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (*[c * (1 - dirt) for c in col], 1); cr.color_ramp.elements[1].color = (*col, 1)
    L.new(nz.outputs['Fac'], cr.inputs['Fac']); L.new(cr.outputs['Color'], p.inputs['Base Color'])
    return m


def tex_mat(name, aid, scale=1.0, tint=None):
    try:
        return ph.texture(aid, scale=scale, name=name, tint=tint)
    except Exception as e:
        print("[b_common] texture fallback", aid, e)
        return pbr(name, tint or (0.4, 0.4, 0.4), 0.7)


def img_mat(name, path, rough=0.7, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
    tc = N.new("ShaderNodeTexCoord"); L.new(tc.outputs['UV'], t.inputs['Vector'])
    L.new(t.outputs['Color'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = rough
    if emit:
        L.new(t.outputs['Color'], p.inputs['Emission Color']); p.inputs['Emission Strength'].default_value = emit
    return m


def sheet(name, loc, size, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (size[0], size[1], 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    return o


def crt_material(name, base=(0.42, 0.5, 0.58), strength=1.6, seed=0.0, roll=True):
    """Old CRT picture: soft moving blotches (an out-of-focus programme), scanlines, a slow roll bar and a
    frame-driven flicker. Frame drivers only, so it plays in any render."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord")
    t = N.new("ShaderNodeValue"); d = t.outputs[0].driver_add("default_value").driver; d.type = 'SCRIPTED'
    d.expression = f"frame / 24 + {seed}"
    nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 2.2; nz.inputs['Detail'].default_value = 3
    L.new(tc.outputs['UV'], nz.inputs['Vector']); L.new(t.outputs[0], nz.inputs['W'])
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['UV'], sep.inputs[0])
    sl = N.new("ShaderNodeMath"); sl.operation = 'MULTIPLY'; sl.inputs[1].default_value = 900; L.new(sep.outputs['Y'], sl.inputs[0])
    sn = N.new("ShaderNodeMath"); sn.operation = 'SINE'; L.new(sl.outputs[0], sn.inputs[0])
    sc = N.new("ShaderNodeMapRange"); sc.inputs['From Min'].default_value = -1; sc.inputs['To Min'].default_value = 0.72
    L.new(sn.outputs[0], sc.inputs['Value'])
    col = N.new("ShaderNodeValToRGB")
    col.color_ramp.elements[0].color = (base[0] * 0.25, base[1] * 0.25, base[2] * 0.3, 1); col.color_ramp.elements[1].color = (*base, 1)
    L.new(nz.outputs['Fac'], col.inputs['Fac'])
    m1 = N.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; m1.inputs[1].default_value = strength; L.new(sc.outputs[0], m1.inputs[0])
    if roll:      # slow bright roll bar moving up the screen
        ry2 = N.new("ShaderNodeMath"); ry2.operation = 'SUBTRACT'; L.new(sep.outputs['Y'], ry2.inputs[0])
        tq = N.new("ShaderNodeMath"); tq.operation = 'MULTIPLY'; tq.inputs[1].default_value = 0.3; L.new(t.outputs[0], tq.inputs[0])
        L.new(tq.outputs[0], ry2.inputs[1])
        fr = N.new("ShaderNodeMath"); fr.operation = 'FRACT'; L.new(ry2.outputs[0], fr.inputs[0])
        bar = N.new("ShaderNodeMapRange"); bar.inputs['From Min'].default_value = 0.0; bar.inputs['From Max'].default_value = 0.12
        bar.inputs['To Min'].default_value = 1.35; bar.inputs['To Max'].default_value = 1.0; bar.clamp = True
        L.new(fr.outputs[0], bar.inputs['Value'])
        m2 = N.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'; L.new(m1.outputs[0], m2.inputs[0]); L.new(bar.outputs[0], m2.inputs[1])
        m1 = m2
    fl = N.new("ShaderNodeValue"); d2 = fl.outputs[0].driver_add("default_value").driver; d2.type = 'SCRIPTED'
    d2.expression = f"0.9 + 0.1 * sin(frame * 2.7 + {seed * 13})"
    m3 = N.new("ShaderNodeMath"); m3.operation = 'MULTIPLY'; L.new(m1.outputs[0], m3.inputs[0]); L.new(fl.outputs[0], m3.inputs[1])
    em = N.new("ShaderNodeEmission"); L.new(col.outputs['Color'], em.inputs['Color']); L.new(m3.outputs[0], em.inputs['Strength'])
    gl = N.new("ShaderNodeBsdfGlossy"); gl.inputs['Roughness'].default_value = 0.08; gl.inputs['Color'].default_value = (0.04, 0.045, 0.05, 1)
    ad = N.new("ShaderNodeAddShader"); L.new(em.outputs[0], ad.inputs[0]); L.new(gl.outputs[0], ad.inputs[1])
    L.new(ad.outputs[0], out.inputs['Surface'])
    return m


def scope_material(name, col=(0.35, 1.0, 0.55), strength=4.0, freq=6.0, speed=1.4):
    """Oscilloscope tube: a thin glowing sine trace that travels (frame driver) over a dark graticule."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['UV'], sep.inputs[0])
    t = N.new("ShaderNodeValue"); d = t.outputs[0].driver_add("default_value").driver; d.type = 'SCRIPTED'; d.expression = f"frame / 24 * {speed}"
    ph_ = N.new("ShaderNodeMath"); ph_.operation = 'MULTIPLY_ADD'; ph_.inputs[1].default_value = freq * 2 * math.pi
    L.new(sep.outputs['X'], ph_.inputs[0]); L.new(t.outputs[0], ph_.inputs[2])
    s1 = N.new("ShaderNodeMath"); s1.operation = 'SINE'; L.new(ph_.outputs[0], s1.inputs[0])
    am = N.new("ShaderNodeMath"); am.operation = 'MULTIPLY_ADD'; am.inputs[1].default_value = 0.28; am.inputs[2].default_value = 0.5
    L.new(s1.outputs[0], am.inputs[0])
    dy = N.new("ShaderNodeMath"); dy.operation = 'SUBTRACT'; L.new(sep.outputs['Y'], dy.inputs[0]); L.new(am.outputs[0], dy.inputs[1])
    ab = N.new("ShaderNodeMath"); ab.operation = 'ABSOLUTE'; L.new(dy.outputs[0], ab.inputs[0])
    ln = N.new("ShaderNodeMapRange"); ln.inputs['From Min'].default_value = 0.0; ln.inputs['From Max'].default_value = 0.025
    ln.inputs['To Min'].default_value = 1.0; ln.inputs['To Max'].default_value = 0.0; ln.clamp = True; L.new(ab.outputs[0], ln.inputs['Value'])
    # graticule
    gx = N.new("ShaderNodeMath"); gx.operation = 'MULTIPLY'; gx.inputs[1].default_value = 10; L.new(sep.outputs['X'], gx.inputs[0])
    gy = N.new("ShaderNodeMath"); gy.operation = 'MULTIPLY'; gy.inputs[1].default_value = 8; L.new(sep.outputs['Y'], gy.inputs[0])
    gl = 0
    grid = []
    for g in (gx, gy):
        fr = N.new("ShaderNodeMath"); fr.operation = 'FRACT'; L.new(g.outputs[0], fr.inputs[0])
        lt = N.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 0.04; L.new(fr.outputs[0], lt.inputs[0])
        grid.append(lt)
    gm = N.new("ShaderNodeMath"); gm.operation = 'MAXIMUM'; L.new(grid[0].outputs[0], gm.inputs[0]); L.new(grid[1].outputs[0], gm.inputs[1])
    gs = N.new("ShaderNodeMath"); gs.operation = 'MULTIPLY'; gs.inputs[1].default_value = 0.08; L.new(gm.outputs[0], gs.inputs[0])
    tot = N.new("ShaderNodeMath"); tot.operation = 'ADD'; L.new(ln.outputs[0], tot.inputs[0]); L.new(gs.outputs[0], tot.inputs[1])
    st = N.new("ShaderNodeMath"); st.operation = 'MULTIPLY'; st.inputs[1].default_value = strength; L.new(tot.outputs[0], st.inputs[0])
    em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (*col, 1); L.new(st.outputs[0], em.inputs['Strength'])
    gls = N.new("ShaderNodeBsdfGlossy"); gls.inputs['Roughness'].default_value = 0.1; gls.inputs['Color'].default_value = (0.03, 0.04, 0.035, 1)
    ad = N.new("ShaderNodeAddShader"); L.new(em.outputs[0], ad.inputs[0]); L.new(gls.outputs[0], ad.inputs[1])
    L.new(ad.outputs[0], out.inputs['Surface'])
    return m


def paper_mat(name, col=(0.86, 0.84, 0.78), lines=True, seed=0):
    """Plain paper with faint grey type lines (unreadable)."""
    m = pbr(name, col, 0.85)
    if not lines:
        return m
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['UV'], sep.inputs[0])
    wv = N.new("ShaderNodeMath"); wv.operation = 'MULTIPLY'; wv.inputs[1].default_value = 38; L.new(sep.outputs['Y'], wv.inputs[0])
    fr = N.new("ShaderNodeMath"); fr.operation = 'FRACT'; L.new(wv.outputs[0], fr.inputs[0])
    ln = N.new("ShaderNodeMath"); ln.operation = 'LESS_THAN'; ln.inputs[1].default_value = 0.35; L.new(fr.outputs[0], ln.inputs[0])
    wn = N.new("ShaderNodeTexNoise"); wn.inputs['Scale'].default_value = 30; wn.inputs['Detail'].default_value = 0
    L.new(tc.outputs['UV'], wn.inputs['Vector'])
    wg = N.new("ShaderNodeMath"); wg.operation = 'GREATER_THAN'; wg.inputs[1].default_value = 0.42; L.new(wn.outputs['Fac'], wg.inputs[0])
    mg = N.new("ShaderNodeMath"); mg.operation = 'MULTIPLY'; L.new(ln.outputs[0], mg.inputs[0]); L.new(wg.outputs[0], mg.inputs[1])
    # margins
    for ax, lo, hi in (('X', 0.1, 0.9), ('Y', 0.08, 0.86)):
        a = N.new("ShaderNodeMath"); a.operation = 'GREATER_THAN'; a.inputs[1].default_value = lo; L.new(sep.outputs[ax], a.inputs[0])
        b = N.new("ShaderNodeMath"); b.operation = 'LESS_THAN'; b.inputs[1].default_value = hi; L.new(sep.outputs[ax], b.inputs[0])
        m1 = N.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; L.new(a.outputs[0], m1.inputs[0]); L.new(b.outputs[0], m1.inputs[1])
        m2 = N.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'; L.new(mg.outputs[0], m2.inputs[0]); L.new(m1.outputs[0], m2.inputs[1]); mg = m2
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(mg.outputs[0], mx.inputs['Factor'])
    mx.inputs[6].default_value = (*col, 1); mx.inputs[7].default_value = (0.3, 0.3, 0.32, 1)
    L.new(mx.outputs[2], p.inputs['Base Color'])
    return m


def envelope_pile(origin, n, rng, mats, spread=0.12, size=(0.22, 0.11)):
    """A loose pile of envelopes (thin boxes) on a surface at origin (top surface z)."""
    out = []
    z = origin[2]
    for k in range(n):
        th = 0.003
        o = box("Env", (origin[0] + rng.uniform(-spread, spread), origin[1] + rng.uniform(-spread * 0.6, spread * 0.6), z + th / 2),
                (size[0], size[1], th), mats[k % len(mats)], rot=(0, 0, rng.uniform(-0.5, 0.5)))
        z += th * 0.9
        out.append(o)
    return out


def stamp_mat(name, base=(0.85, 0.82, 0.74), stripe=(0.55, 0.08, 0.06)):
    """An envelope face with a red stripe band (a generic 'final notice' look, no text)."""
    m = pbr(name, base, 0.8)
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Object'], sep.inputs[0])
    a = N.new("ShaderNodeMath"); a.operation = 'COMPARE'; a.inputs[1].default_value = 0.03; a.inputs[2].default_value = 0.012
    L.new(sep.outputs['Y'], a.inputs[0])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(a.outputs[0], mx.inputs['Factor'])
    mx.inputs[6].default_value = (*base, 1); mx.inputs[7].default_value = (*stripe, 1)
    L.new(mx.outputs[2], p.inputs['Base Color'])
    return m


def model(aid, loc, rot_z=0.0, scale=1.0, hide=False):
    r, ms = ph.model(aid, loc=loc, rot_z=rot_z, scale=scale)
    return r, ms


def hide_tree(root):
    for o in [root] + list(root.children_recursive):
        o.hide_render = True; o.hide_viewport = True


def drift(o, base, sec, amp=(0.01, 0.01, 0.005), rate=0.5):
    o.location = Vector(base) + Vector((amp[0] * math.sin(sec * rate), amp[1] * math.cos(sec * rate * 0.8), amp[2] * math.sin(sec * rate * 1.3)))


def smoke(loc, name="Smoke", density=0.4, size=(0.25, 0.25, 0.8)):
    """A thin rising curl of smoke (noise volume whose W is frame-driven)."""
    o = box(name, (loc[0], loc[1], loc[2] + size[2] / 2), size)
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); L.new(tc.outputs['Generated'], mp.inputs['Vector'])
    dz = mp.inputs['Location'].driver_add("default_value", 2).driver; dz.type = 'SCRIPTED'; dz.expression = "-frame / 24 * 0.25"
    nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 3.5; nz.inputs['Detail'].default_value = 4
    wd = nz.inputs['W'].driver_add("default_value").driver; wd.type = 'SCRIPTED'; wd.expression = "frame / 24 * 0.15"
    L.new(mp.outputs[0], nz.inputs['Vector'])
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Generated'], sep.inputs[0])
    # thin column: falls off from the centre in x/y, fades near top
    cx = N.new("ShaderNodeVectorMath"); cx.operation = 'DISTANCE'; cx.inputs[1].default_value = (0.5, 0.5, 0)
    cmb = N.new("ShaderNodeCombineXYZ"); L.new(sep.outputs['X'], cmb.inputs[0]); L.new(sep.outputs['Y'], cmb.inputs[1])
    L.new(cmb.outputs[0], cx.inputs[0])
    wid = N.new("ShaderNodeMapRange"); wid.inputs['From Min'].default_value = 0.0; wid.inputs['From Max'].default_value = 0.45
    wid.inputs['To Min'].default_value = 1.0; wid.inputs['To Max'].default_value = 0.0; wid.clamp = True; L.new(cx.outputs['Value'], wid.inputs['Value'])
    top = N.new("ShaderNodeMapRange"); top.inputs['From Min'].default_value = 1.0; top.inputs['From Max'].default_value = 0.3; top.clamp = True
    L.new(sep.outputs['Z'], top.inputs['Value'])
    th = N.new("ShaderNodeMapRange"); th.inputs['From Min'].default_value = 0.5; th.inputs['From Max'].default_value = 0.75; th.inputs['To Max'].default_value = density
    L.new(nz.outputs['Fac'], th.inputs['Value'])
    m1 = N.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; L.new(th.outputs[0], m1.inputs[0]); L.new(wid.outputs[0], m1.inputs[1])
    m2 = N.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'; L.new(m1.outputs[0], m2.inputs[0]); L.new(top.outputs[0], m2.inputs[1])
    v = N.new("ShaderNodeVolumePrincipled"); v.inputs['Color'].default_value = (0.8, 0.82, 0.85, 1); v.inputs['Anisotropy'].default_value = 0.5
    L.new(m2.outputs[0], v.inputs['Density']); L.new(v.outputs[0], out.inputs['Volume'])
    o.data.materials.append(m); o.visible_shadow = False
    return o


# ============================================================================ pose capture / blend (sit -> stand etc.)
def capture(h):
    bpy.context.view_layer.update()
    return dict(loc=h.arm.location.copy(), rot=h.arm.rotation_euler.copy(),
                bones={pb.name: pb.rotation_quaternion.copy() for pb in h.arm.pose.bones},
                blocs={pb.name: pb.location.copy() for pb in h.arm.pose.bones})


def apply_pose(h, P):
    h.arm.location = P["loc"]; h.arm.rotation_euler = P["rot"]
    for pb in h.arm.pose.bones:
        pb.rotation_quaternion = P["bones"][pb.name]; pb.location = P["blocs"][pb.name]
    bpy.context.view_layer.update()


def blend_pose(h, A, Bp, u):
    u = min(max(u, 0.0), 1.0)
    h.arm.location = A["loc"].lerp(Bp["loc"], u)
    for pb in h.arm.pose.bones:
        pb.rotation_quaternion = A["bones"][pb.name].slerp(Bp["bones"][pb.name], u)
        pb.location = A["blocs"][pb.name].lerp(Bp["blocs"][pb.name], u)
    bpy.context.view_layer.update()


def shrug(h, amt):
    """Shoulders up (amt 0..1)."""
    for sd, sg in (("L", 1), ("R", -1)):
        h.rot(f"clavicle.{sd}", (0, 1, 0), -sg * 14 * amt)


# ============================================================================ on-screen label ("Court reconstruction")
def label_image(text, path, W=1920, H=816):
    import skia
    from PIL import Image
    from scipy.ndimage import gaussian_filter
    s = skia.Surface(W, H); cv = s.getCanvas(); cv.clear(skia.Color4f(0, 0, 0, 0))
    p = skia.Paint(AntiAlias=True); p.setColor4f(skia.Color4f(1, 1, 1, 1))
    f = skia.Font(skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"), 34)
    x, y = 96, H - 84
    cv.drawRect(skia.Rect.MakeXYWH(x, y - 30, 4, 38), p)                 # a thin bar before the words
    tx = x + 18
    for ch in text.upper():                                              # letter-spaced caps
        cv.drawString(ch, tx, y, f, p); tx += f.measureText(ch) + 4
    a = s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).astype(np.float32) / 255
    al = a[..., 3]
    sh = gaussian_filter(al, 4) * 0.6
    out = np.zeros_like(a); out[..., :3] = 1.0
    out[..., 3] = np.clip(al * 0.92 + sh * (1 - al), 0, 1)
    rgb = out[..., :3] * al[..., None] + 0.0 * (1 - al[..., None])     # shadow is black, letters white
    out[..., :3] = np.where(al[..., None] > 0.01, 1.0, 0.0)
    Image.fromarray((out * 255).astype(np.uint8), "RGBA").save(path)
    return path


def label(c, text, f_in=6, fade=12):
    """Camera-parented plane with a small lower-left caption (fades in by frame driver). Idempotent."""
    if c.get("_label") or "cam" not in c:
        return
    cam = c["cam"]
    path = os.path.join(GEN, "b_label_" + text.lower().replace(" ", "_") + ".png")
    if not os.path.exists(path):
        label_image(text, path)
    m = bpy.data.materials.new("Label"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord")
    tex = N.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(path); tex.image.alpha_mode = 'STRAIGHT'
    L.new(tc.outputs['UV'], tex.inputs['Vector'])
    em = N.new("ShaderNodeEmission"); L.new(tex.outputs['Color'], em.inputs['Color']); em.inputs['Strength'].default_value = 0.9
    tr = N.new("ShaderNodeBsdfTransparent")
    fv = N.new("ShaderNodeValue")
    d = fv.outputs[0].driver_add("default_value").driver; d.type = 'SCRIPTED'; d.expression = f"min(1, max(0, (frame - {f_in}) / {fade}))"
    mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; L.new(tex.outputs['Alpha'], mul.inputs[0]); L.new(fv.outputs[0], mul.inputs[1])
    mx = N.new("ShaderNodeMixShader"); L.new(mul.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs['Surface'])
    dist = 0.5; cd = cam.data; sensor = cd.sensor_width
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0)); o = bpy.context.active_object; o.name = "ReconLabel"
    o.data.materials.append(m); o.parent = cam; o.location = (0, 0, -dist)
    for axis, k in ((0, 1.0), (1, 816 / 1920)):
        dd = o.driver_add("scale", axis).driver; dd.type = 'SCRIPTED'
        v = dd.variables.new(); v.name = "lens"; v.targets[0].id_type = 'CAMERA'; v.targets[0].id = cd; v.targets[0].data_path = "lens"
        dd.expression = f"{dist} * {sensor} / lens * {k}"
    o.visible_shadow = False; o.visible_diffuse = False; o.visible_glossy = False; o.visible_transmission = False
    o.visible_volume_scatter = False
    c["_label"] = o


def ph_instances(aid, placements):
    """Import a Poly Haven model once; linked copies at [(loc, rot_z, scale)]."""
    root, ms = ph.model(aid)
    out = []
    for (loc, rz, sc) in placements:
        r = bpy.data.objects.new(aid + "_inst", None); bpy.context.collection.objects.link(r)
        for o in ms:
            n = o.copy(); bpy.context.collection.objects.link(n); n.parent = r
            n.matrix_parent_inverse = o.matrix_parent_inverse.copy()
            n.matrix_world = n.matrix_world  # keep relative transform
        r.location = loc; r.rotation_euler = (0, 0, rz); r.scale = (sc, sc, sc)
        out.append(r)
    root.location = (0, 0, -1000)
    for o in [root] + ms:
        o.hide_render = True
    return out


def preview_cap():
    """Preview renders only (env B_PREVIEW=1): cap subdivision so heavy shared sets fit in memory.
    Baked deliveries keep full detail (the variable is not set there)."""
    if os.environ.get("B_PREVIEW") != "1":
        return
    n = 0
    for o in bpy.data.objects:
        for m in o.modifiers:
            if m.type == 'SUBSURF' and m.render_levels > 1:
                m.render_levels = 1; n += 1
    print("[b_common] preview: capped subsurf on", n, "objects")


def nod(h, deg, bone="head"):
    """Tilt a bone forward (positive = looking down) whatever way the person faces."""
    h.rot(bone, Vector((0, 0, 1)).cross(fwd_of(h)).normalized(), deg)
