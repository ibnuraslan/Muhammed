"""Shared pieces for "The $25 Million Hidden in a Drain": rain, wet ground with frame-driven ripples, people
(unnamed MakeHuman figures, no likeness), poses, jewels, the plastic container, the suburban pavillon."""
import math
import numpy as np
import bpy, bmesh
from mathutils import Vector
from kit import *
import ph
from human import Human, add_asset, pose_walk, reset_pose, pose_sit, fingers_curl, reach, _world_verts, SIDE

FPS = 24


# ============================================================================ frame drivers
def frame_value(N, expr, name="FrameDrv"):
    """A Value node driven by a simple expression of `frame` (plays in any render, no scripts)."""
    v = N.new("ShaderNodeValue"); v.name = name
    d = v.outputs[0].driver_add("default_value").driver; d.type = 'SCRIPTED'; d.expression = expr
    return v


def tex_mat(aid, scale=1.0, tint=None, name=None, rough_mul=None, coat=0.0, sat=1.0):
    try:
        m = ph.texture(aid, scale=scale, tint=tint, name=name)
    except Exception as e:                          # offline fallback: plain colour
        print("[dd] texture fallback", aid, e)
        m = pbr(name or aid, tint or (0.5, 0.5, 0.5), 0.7)
    p = m.node_tree.nodes["Principled BSDF"]
    if sat != 1.0 and p.inputs['Base Color'].is_linked:
        N = m.node_tree.nodes; L = m.node_tree.links
        src = p.inputs['Base Color'].links[0].from_socket
        hs = N.new("ShaderNodeHueSaturation"); hs.inputs['Saturation'].default_value = sat
        L.new(src, hs.inputs['Color']); L.new(hs.outputs['Color'], p.inputs['Base Color'])
    if coat:
        p.inputs['Coat Weight'].default_value = coat; p.inputs['Coat Roughness'].default_value = 0.08
    return m


def wet(m, amount=0.5, puddle_scale=0.5, ripples=True, ripple_scale=9.0):
    """Make a textured material wet: lower roughness, a clear coat, puddles (noise mask) with expanding rain rings."""
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    pn = N.new("ShaderNodeTexNoise"); pn.inputs['Scale'].default_value = puddle_scale; pn.inputs['Detail'].default_value = 5
    L.new(tc.outputs['Object'], pn.inputs['Vector'])
    pm = N.new("ShaderNodeMapRange"); pm.inputs['From Min'].default_value = 0.5; pm.inputs['From Max'].default_value = 0.56
    L.new(pn.outputs['Fac'], pm.inputs['Value'])
    p.inputs['Coat Weight'].default_value = amount
    cr = N.new("ShaderNodeMapRange"); cr.inputs['To Min'].default_value = 0.25; cr.inputs['To Max'].default_value = 0.02
    L.new(pm.outputs[0], cr.inputs['Value']); L.new(cr.outputs[0], p.inputs['Coat Roughness'])
    # darken a touch where wet
    if p.inputs['Base Color'].is_linked:
        src = p.inputs['Base Color'].links[0].from_socket
        dk = N.new("ShaderNodeMix"); dk.data_type = 'RGBA'; dk.blend_type = 'MULTIPLY'; dk.inputs['Factor'].default_value = 1.0
        dk.inputs[7].default_value = (0.72, 0.74, 0.78, 1); L.new(src, dk.inputs[6]); L.new(dk.outputs[2], p.inputs['Base Color'])
    if ripples:
        w = frame_value(N, f"frame / {FPS} * 1.6", "RippleTime")
        vor = N.new("ShaderNodeTexVoronoi"); vor.voronoi_dimensions = '4D'; vor.inputs['Scale'].default_value = ripple_scale
        L.new(tc.outputs['Object'], vor.inputs['Vector']); L.new(w.outputs[0], vor.inputs['W'])
        # ring = sin(distance * k) masked to small radius
        mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 60.0; L.new(vor.outputs['Distance'], mul.inputs[0])
        sn = N.new("ShaderNodeMath"); sn.operation = 'SINE'; L.new(mul.outputs[0], sn.inputs[0])
        fall = N.new("ShaderNodeMapRange"); fall.inputs['From Min'].default_value = 0.0; fall.inputs['From Max'].default_value = 0.35
        fall.inputs['To Min'].default_value = 1.0; fall.inputs['To Max'].default_value = 0.0; L.new(vor.outputs['Distance'], fall.inputs['Value'])
        r = N.new("ShaderNodeMath"); r.operation = 'MULTIPLY'; L.new(sn.outputs[0], r.inputs[0]); L.new(fall.outputs[0], r.inputs[1])
        r2 = N.new("ShaderNodeMath"); r2.operation = 'MULTIPLY'; L.new(r.outputs[0], r2.inputs[0]); L.new(pm.outputs[0], r2.inputs[1])
        bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.35; bp.inputs['Distance'].default_value = 0.002
        L.new(r2.outputs[0], bp.inputs['Height']); L.new(bp.outputs['Normal'], p.inputs['Coat Normal'])
    return m


_MODEL_CACHE = {}


def model_h(aid, loc, height, rot_z=0.0):
    """Poly Haven model scaled to a target height (m), standing on loc.z. Repeats share mesh data (linked copies)."""
    if aid in _MODEL_CACHE:
        src_root, src_ms, lo0, hi0 = _MODEL_CACHE[aid]
        root = bpy.data.objects.new(aid, None); bpy.context.collection.objects.link(root)
        for o in src_root.children_recursive:
            if o.type != 'MESH':
                continue
            n = bpy.data.objects.new(o.name, o.data); bpy.context.collection.objects.link(n)
            from mathutils import Matrix as _Mx
            n.parent = root; n.matrix_parent_inverse = _Mx.Identity(4)
            n.matrix_basis = (src_root.matrix_world.inverted() @ o.matrix_world)
        s_ = height / max(hi0.z - lo0.z, 1e-3)
        root.rotation_euler = (0, 0, rot_z); root.scale = (s_, s_, s_); root.location = Vector(loc) - Vector((0, 0, lo0.z * s_))
        bpy.context.view_layer.update()
        return root
    try:
        root, ms = ph.model(aid, loc=(0, 0, 0), rot_z=0.0)
    except Exception as e:
        print("[dd] model skipped", aid, e); return None
    lo, hi = ph.bounds(ms)
    _MODEL_CACHE[aid] = (root, ms, lo.copy(), hi.copy())
    root.rotation_euler = (0, 0, rot_z)
    s = height / max(hi.z - lo.z, 1e-3)
    root.scale = (s, s, s); root.location = Vector(loc) - Vector((0, 0, lo.z * s))
    bpy.context.view_layer.update()
    return root


# ============================================================================ rain
def rain_material(strength=0.5, density=0.95):
    rm = bpy.data.materials.new("Rain"); rm.use_nodes = True
    N = rm.node_tree.nodes; L = rm.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (30 * 45, 8 * 3.5, 1)
    wn = N.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = '2D'
    L.new(tc.outputs['Object'], mp.inputs['Vector']); L.new(mp.outputs[0], wn.inputs['Vector'])
    gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = density; L.new(wn.outputs['Value'], gt.inputs[0])
    sc = N.new("ShaderNodeMath"); sc.operation = 'MULTIPLY'; sc.inputs[1].default_value = 0.3; L.new(gt.outputs[0], sc.inputs[0])
    tr = N.new("ShaderNodeBsdfTransparent"); gl = N.new("ShaderNodeEmission"); gl.inputs['Color'].default_value = (0.8, 0.84, 0.9, 1)
    gl.inputs['Strength'].default_value = strength
    mx = N.new("ShaderNodeMixShader"); L.new(sc.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(gl.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs['Surface'])
    return rm


def rain(c, x0, ys, width=30, height=8, strength=0.5, density=0.95, rot_z=0.0):
    """Vertical curtains of streaks at depths `ys` (camera looks along +Y); scroll them with rain_fall()."""
    rm = rain_material(strength, density)
    lst = []
    for y in ys:
        for j in range(2):
            bpy.ops.mesh.primitive_plane_add(size=1, location=(x0, y, height / 2 + j * height), rotation=(math.radians(90), 0, rot_z))
            o = bpy.context.active_object; o.name = "Rain"; o.scale = (width, height, 1); o.data.materials.append(rm)
            o.visible_shadow = False; o.visible_diffuse = False; o.visible_glossy = False; o.visible_transmission = False
            lst.append((o, j, height))
    c.setdefault("rain", []).extend(lst)
    return lst


def rain_fall(c, sec, speed=7.0):
    for o, j, hgt in c.get("rain", []):
        o.location.z = hgt / 2 + j * hgt - (sec * speed) % hgt


# ============================================================================ people
def person(name, gender=1.0, years=40, cloth="male_casualsuit01", hair="short02", cval=1.0, hv=0.3, sat=1.0, hue=0.5,
           skin=None, height=0.5, weight=0.45, shoes="shoes02", tint=(1, 1, 1)):
    """cval is the HSV value multiplier of the clothes texture (1 = as authored); tint multiplies its colour."""
    h = Human(name, gender=gender, years=years, muscle=0.5, weight=weight, height=height, eyelashes="eyelashes01",
              skin=skin or ("middleage_lightskinned_female_diffuse.png" if gender < 0.5 else "middleage_lightskinned_male_diffuse.png"))
    add_asset(h, "clothes", cloth, val=cval, rough=0.7, sat=sat, hue=hue, tint=tint)
    add_asset(h, "clothes", shoes, val=0.5, rough=0.4)
    if hair:
        add_asset(h, "hair", hair, val=hv, rough=0.45)
    return h


def armband(h, side="L", col=(0.9, 0.32, 0.04)):
    """An orange POLICE armband: a short tube parented to the upper-arm bone (follows the baked rig)."""
    b = f"upperarm02.{side}"
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.058, depth=0.09)
    o = bpy.context.active_object; o.name = h.name + "_armband"
    o.data.materials.append(pbr("Armband", col, 0.6))
    pb = h.arm.pose.bones[b]
    o.parent = h.arm; o.parent_type = 'BONE'; o.parent_bone = b
    # bone space: Y runs along the bone; the tube's axis is Z -> rotate to Y, sit at the bone's middle
    o.rotation_euler = (math.radians(90), 0, 0)
    o.location = (0, -pb.length * 0.5, 0)
    return o


POLICE_LOOKS = [("male_casualsuit05", 0.5, 1.0, 1.15, (1.0, 1.0, 1.0)),      # (cloth, hue, sat, val, tint)
                ("male_casualsuit01", 0.5, 0.9, 1.0, (1.0, 1.0, 1.0)),
                ("male_casualsuit05", 0.58, 0.8, 1.6, (1.0, 0.92, 0.8)),
                ("male_casualsuit03", 0.5, 0.6, 1.2, (1.0, 1.0, 1.0)),
                ("male_casualsuit01", 0.45, 0.7, 1.3, (0.85, 0.9, 1.0))]


def officer(name, years=40, seed=0, gender=1.0, band=True):
    """Plain-clothes detective: varied coats / shirts and jeans, an orange POLICE armband.
    (no casualsuit02/04/female_casualsuit01/02: their T-shirts carry a printed logo)"""
    if gender > 0.5:
        cl, hue, sat, val, tint = POLICE_LOOKS[seed % len(POLICE_LOOKS)]
        hair = ("short02", "short04", "short03", "short01")[seed % 4]
    else:
        cl, hue, sat, val, tint = "female_elegantsuit01", 0.5, 0.6, 1.5, (0.75, 0.82, 1.0)
        hair = ("bob01", "ponytail01", "bob02")[seed % 3]
    h = person(name, gender, years, cl, hair, cval=val, hv=0.25 + 0.15 * (seed % 3), sat=sat, hue=hue, tint=tint,
               height=0.45 + 0.05 * (seed % 3))
    if band:
        armband(h, "L")
    return h


def staff(name, gender, years, hair, seed=0):
    """Boutique staff: navy or grey suits."""
    cl = "male_elegantsuit01" if gender > 0.5 else "female_elegantsuit01"
    navy = seed % 2 == 0
    if gender > 0.5:
        return person(name, gender, years, cl, hair, cval=1.9 if navy else 2.4, sat=0.0, tint=(0.42, 0.5, 0.82) if navy else (0.8, 0.8, 0.82), hv=0.35)
    return person(name, gender, years, cl, hair, cval=1.3 if navy else 1.6, sat=0.0, tint=(0.5, 0.58, 0.9) if navy else (0.85, 0.85, 0.86), hv=0.35)


def guard(name, years=41, hair="short02"):
    """Security guard: dark navy uniform suit, white shirt."""
    return person(name, 1.0, years, "male_elegantsuit01", hair, cval=1.0, sat=0.0, tint=(0.55, 0.62, 0.85), hv=0.3)


def zero(h):
    """Poses are authored in world directions with the body facing -Y: clear the rig rotation first."""
    h.arm.rotation_euler = (0, 0, 0); bpy.context.view_layer.update()


def ground(h, z=0.0):
    bpy.context.view_layer.update()
    w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
    h.arm.location.z -= w[:, 2].min() - z; bpy.context.view_layer.update()


def place(h, loc, face_z, z=0.0):
    h.arm.rotation_euler = (0, 0, face_z); h.arm.location = Vector(loc); ground(h, z)


def face_to(src, dst):
    """rotation z so a person at src faces dst (rest pose faces -Y: z = theta faces (sin, -cos))."""
    d = Vector(dst) - Vector(src)
    return math.atan2(d.x, -d.y)


def arms_relaxed(h, swing=0.0, phase=0.0):
    M = h.arm.matrix_world.to_3x3(); fwd = (M @ Vector((0, -1, 0))).normalized(); left = (M @ Vector((1, 0, 0))).normalized()
    for sd, sg in (("L", 1), ("R", -1)):
        a = math.radians(swing) * math.sin(2 * math.pi * phase + (math.pi if sd == "L" else 0.0))
        up = (Vector((0, 0, -1)) * math.cos(a) + fwd * math.sin(a) + left * (0.12 * sg)).normalized()
        lo = (up + fwd * (0.25 + 0.15 * max(0.0, math.sin(a)))).normalized()
        h.aim(f"upperarm01.{sd}", up); h.aim(f"upperarm02.{sd}", up)
        h.aim(f"lowerarm01.{sd}", lo); h.aim(f"lowerarm02.{sd}", lo); h.aim(f"wrist.{sd}", lo + left * (0.1 * sg))


def walk_to(h, a, b, sec, speed=1.2, cadence=1.8, face=None):
    """Walk from a toward b at `speed` m/s, stopping at b. Returns True while walking."""
    a, b = Vector(a), Vector(b); d = (b - a); dist = d.length
    s = min(sec * speed, dist)
    pos = a + d.normalized() * s if dist > 1e-6 else a
    walking = s < dist - 1e-3
    zero(h)
    phase = (s / speed * cadence / 2) % 1.0
    bob = pose_walk(h, phase if walking else 0.0, stride=28 if walking else 0.0, arm_swing=22 if walking else 0.0)
    h.arm.rotation_euler = (0, 0, face if face is not None else face_to(a, b))
    h.arm.location = pos; ground(h, pos.z)
    if not walking:
        arms_relaxed(h)
    return walking


def pose_kneel(h, lean=30):
    """Right knee on the ground, left foot planted forward; leaning forward over the work."""
    zero(h); reset_pose(h)
    for sd, sg in SIDE.items():
        if sd == "R":
            h.aim(f"upperleg01.{sd}", (0.12 * sg, -0.15, -1)); h.aim(f"upperleg02.{sd}", (0.12 * sg, -0.15, -1))
            h.aim(f"lowerleg01.{sd}", (0.05 * sg, 1, -0.12)); h.aim(f"lowerleg02.{sd}", (0.05 * sg, 1, -0.12))
            h.aim(f"foot.{sd}", (0.0, 0.3, -1))
        else:
            h.aim(f"upperleg01.{sd}", (0.2 * sg, -1, -0.25)); h.aim(f"upperleg02.{sd}", (0.2 * sg, -1, -0.25))
            h.aim(f"lowerleg01.{sd}", (0.05 * sg, -0.1, -1)); h.aim(f"lowerleg02.{sd}", (0.05 * sg, -0.1, -1))
            h.aim(f"foot.{sd}", (0.05 * sg, -1, -0.2))
    for b, a in (("spine05", 4), ("spine04", 5), ("spine03", 5), ("spine02", 4), ("spine01", 3)):
        h.rot(b, (1, 0, 0), lean * a / 21)
    h.rot("neck01", (1, 0, 0), 10); h.rot("head", (1, 0, 0), 14)


def pose_crouch(h, lean=25):
    zero(h); reset_pose(h)
    for sd, sg in SIDE.items():
        h.aim(f"upperleg01.{sd}", (0.3 * sg, -1, -0.15)); h.aim(f"upperleg02.{sd}", (0.3 * sg, -1, -0.15))
        h.aim(f"lowerleg01.{sd}", (0.06 * sg, 0.45, -1)); h.aim(f"lowerleg02.{sd}", (0.06 * sg, 0.45, -1))
        h.aim(f"foot.{sd}", (0.1 * sg, -1, -0.15))
    for b, a in (("spine05", 4), ("spine04", 5), ("spine03", 5), ("spine02", 4), ("spine01", 3)):
        h.rot(b, (1, 0, 0), lean * a / 21)
    h.rot("head", (1, 0, 0), 16)


def pose_floor_sit(h, hunch=14, hands_back=True):
    """Sitting on the floor, knees up, hands behind the back (tied), head lowered."""
    zero(h); reset_pose(h)
    for sd, sg in SIDE.items():
        h.aim(f"upperleg01.{sd}", (0.18 * sg, -1, 0.35)); h.aim(f"upperleg02.{sd}", (0.18 * sg, -1, 0.35))
        h.aim(f"lowerleg01.{sd}", (0.06 * sg, -0.35, -1)); h.aim(f"lowerleg02.{sd}", (0.06 * sg, -0.35, -1))
        h.aim(f"foot.{sd}", (0.1 * sg, -1, -0.3))
    for b, a in (("spine05", 4), ("spine04", 5), ("spine03", 5), ("spine02", 4), ("spine01", 3)):
        h.rot(b, (1, 0, 0), hunch * a / 21)
    if hands_back:
        for sd, sg in SIDE.items():
            h.aim(f"upperarm01.{sd}", (0.25 * sg, 0.45, -1)); h.aim(f"upperarm02.{sd}", (0.25 * sg, 0.45, -1))
            h.aim(f"lowerarm01.{sd}", (-0.7 * sg, 0.5, -0.25)); h.aim(f"lowerarm02.{sd}", (-0.7 * sg, 0.5, -0.25))
    else:
        for sd, sg in SIDE.items():
            knee = h.bone_tail(f"upperleg02.{sd}"); sh = h.bone_head(f"upperarm01.{sd}")
            reach(h, sd, knee + Vector((0, -0.05, 0.02)), Vector((0.4 * sg, 0.3, -0.5)))
    fingers_curl(h, 30)
    h.rot("head", (1, 0, 0), 18)


# ============================================================================ jewels
def diamond_mesh(name, r=0.01):
    """A round brilliant cut (r = girdle radius): table, star, kite and girdle facets above; pavilion mains and
    lower-girdle facets below, built as the convex hull of the facet corner points (crisp flat facets)."""
    pts = []
    for k in range(8):
        a = 2 * math.pi * k / 8
        pts.append((0.54 * r * math.cos(a), 0.54 * r * math.sin(a), 0.34 * r))             # table
        a2 = a + math.pi / 8
        pts.append((0.80 * r * math.cos(a2), 0.80 * r * math.sin(a2), 0.215 * r))          # star points
        pts.append((0.93 * r * math.cos(a), 0.93 * r * math.sin(a), 0.11 * r))            # kite tips
    for k in range(32):
        a = 2 * math.pi * k / 32
        pts.append((r * math.cos(a), r * math.sin(a), 0.02 * r))                             # girdle
        pts.append((r * math.cos(a), r * math.sin(a), -0.02 * r))
    for k in range(16):
        a = 2 * math.pi * (k + 0.5) / 16
        pts.append((0.62 * r * math.cos(a), 0.62 * r * math.sin(a), -0.33 * r))           # lower girdle
    for k in range(8):
        a = 2 * math.pi * k / 8
        pts.append((0.3 * r * math.cos(a), 0.3 * r * math.sin(a), -0.63 * r))             # pavilion mains
    pts.append((0, 0, -0.86 * r))                                                           # culet
    bm = bmesh.new()
    for p in pts:
        bm.verts.new(p)
    bmesh.ops.convex_hull(bm, input=list(bm.verts))
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(1.0), verts=list(bm.verts), edges=list(bm.edges))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    for p in me.polygons:
        p.use_smooth = False
    return o


_MATS = {}


def muddy(m, amount=0.55, col=(0.16, 0.13, 0.09)):
    """Smear a material with dried mud: noise-masked brown, rough and non-metal."""
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 220; nz.inputs['Detail'].default_value = 6
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.42; mr.inputs['From Max'].default_value = 0.62
    mr.inputs['To Max'].default_value = amount; L.new(nz.outputs['Fac'], mr.inputs['Value'])
    base = tuple(p.inputs['Base Color'].default_value)
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[6].default_value = base; mx.inputs[7].default_value = (*col, 1)
    L.new(mr.outputs[0], mx.inputs['Factor']); L.new(mx.outputs[2], p.inputs['Base Color'])
    for inp, lo, hi in (('Metallic', p.inputs['Metallic'].default_value, 0.0), ('Roughness', p.inputs['Roughness'].default_value, 0.9)):
        r = N.new("ShaderNodeMapRange"); r.inputs['To Min'].default_value = lo; r.inputs['To Max'].default_value = hi
        L.new(mr.outputs[0], r.inputs['Value']); L.new(r.outputs[0], p.inputs[inp])
    return m


def jewel_mats():
    if not _MATS:
        d = bpy.data.materials.new("Diamond"); d.use_nodes = True
        p = d.node_tree.nodes["Principled BSDF"]
        p.inputs['Base Color'].default_value = (1, 1, 1, 1); p.inputs['Transmission Weight'].default_value = 1.0
        p.inputs['IOR'].default_value = 2.42; p.inputs['Roughness'].default_value = 0.0
        if 'Dispersion' in p.inputs:
            p.inputs['Dispersion'].default_value = 0.6
        _MATS["diamond"] = d
        _MATS["plat"] = pbr("Platinum", (0.78, 0.78, 0.8), 0.12, 1.0)
        _MATS["gold"] = pbr("Gold", (0.95, 0.72, 0.36), 0.14, 1.0)
        _MATS["plat_dirty"] = muddy(pbr("PlatinumDirty", (0.7, 0.7, 0.72), 0.3, 1.0))
        _MATS["gold_dirty"] = muddy(pbr("GoldDirty", (0.85, 0.64, 0.32), 0.32, 1.0))
        for nm, col in (("ruby", (0.6, 0.02, 0.05)), ("sapphire", (0.03, 0.08, 0.5)), ("emerald", (0.02, 0.4, 0.15))):
            g = bpy.data.materials.new(nm); g.use_nodes = True; q = g.node_tree.nodes["Principled BSDF"]
            q.inputs['Base Color'].default_value = (*col, 1); q.inputs['Transmission Weight'].default_value = 1.0
            q.inputs['IOR'].default_value = 1.77; q.inputs['Roughness'].default_value = 0.0
            _MATS[nm] = g
    return _MATS


def ring(name, loc, stone_r=0.004, band="plat", stone="diamond", rot=(0, 0, 0), band_r=0.0095, upright=True, setting_h=0.0):
    """A ring: torus band with a stone on top. Returns the parent empty."""
    M = jewel_mats()
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    bpy.ops.mesh.primitive_torus_add(major_radius=band_r, minor_radius=0.0013, major_segments=48, minor_segments=10,
                                     location=(0, 0, 0), rotation=(math.radians(90) if upright else 0, 0, 0))
    b = bpy.context.active_object; b.name = name + "_band"; b.data.materials.append(M[band]); b.parent = root
    bpy.ops.object.shade_smooth()
    top = Vector((0, 0, band_r + 0.0012)) if upright else Vector((band_r, 0, 0.0012))
    st = diamond_mesh(name + "_stone", stone_r); st.data.materials.append(M[stone]); st.parent = root
    st.location = top + Vector((0, 0, stone_r * 0.65 + setting_h))
    if setting_h:
        bc = cyl(name + "_basket", top + Vector((0, 0, setting_h / 2 + 0.0005)), stone_r * 0.45, setting_h, M[band], verts=16); bc.parent = root
    # four prongs
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        pr = cyl(name + "_prong", top + Vector((stone_r * 0.93 * math.cos(a), stone_r * 0.93 * math.sin(a), (stone_r * 0.65 + setting_h) * 0.75)),
                 max(0.0004, stone_r * 0.07), stone_r * 0.65 + setting_h + stone_r * 0.3, M[band], verts=6)
        pr.parent = root
    root.location = loc; root.rotation_euler = rot
    return root


def earring(name, loc, r=0.003, stone="diamond"):
    M = jewel_mats()
    st = diamond_mesh(name, r); st.data.materials.append(M[stone]); st.location = loc
    cyl(name + "_post", Vector(loc) + Vector((0, 0, -r * 1.4)), 0.0004, 0.01, M["plat"], verts=6)
    return st


def tub_material(name, dirt=0.7):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    p.inputs['Base Color'].default_value = (0.78, 0.8, 0.78, 1); p.inputs['Roughness'].default_value = 0.5
    p.inputs['Transmission Weight'].default_value = 0.6
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 30; nz.inputs['Detail'].default_value = 8
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Generated'], sep.inputs[0])
    low = N.new("ShaderNodeMapRange"); low.inputs['From Min'].default_value = 0.6; low.inputs['From Max'].default_value = 0.0
    L.new(sep.outputs['Z'], low.inputs['Value'])                       # more mud toward the bottom
    add = N.new("ShaderNodeMath"); add.operation = 'MULTIPLY'; L.new(nz.outputs['Fac'], add.inputs[0]); L.new(low.outputs[0], add.inputs[1])
    mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.15; mr.inputs['From Max'].default_value = 0.45
    mr.inputs['To Max'].default_value = dirt; L.new(add.outputs[0], mr.inputs['Value'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[6].default_value = (0.78, 0.8, 0.78, 1); mx.inputs[7].default_value = (0.2, 0.16, 0.11, 1)
    L.new(mr.outputs[0], mx.inputs['Factor']); L.new(mx.outputs[2], p.inputs['Base Color'])
    tw = N.new("ShaderNodeMapRange"); tw.inputs['To Min'].default_value = 0.6; tw.inputs['To Max'].default_value = 0.0
    L.new(mr.outputs[0], tw.inputs['Value']); L.new(tw.outputs[0], p.inputs['Transmission Weight'])
    return m


def _open_box(name, size, bevel=0.01):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    bm = bmesh.new(); bm.from_mesh(o.data)
    for f in list(bm.faces):
        if f.normal.z > 0.9:
            bm.faces.remove(f)
    bm.to_mesh(o.data); bm.free()
    bv = o.modifiers.new("bev", 'BEVEL'); bv.width = bevel; bv.segments = 3
    so = o.modifiers.new("sol", 'SOLIDIFY'); so.thickness = 0.002
    return o


def container(name, loc, size=(0.17, 0.12, 0.075), rot_z=0.0, dirt=0.7, lid_open=0.6):
    """A small grimy translucent plastic food tub; its lid sits half off, tipped against the rim."""
    m = tub_material(name + "Plastic", dirt)
    o = _open_box(name, size, 0.012); o.data.materials.append(m)
    o.location = Vector(loc) + Vector((0, 0, size[2] / 2)); o.rotation_euler = (0, 0, rot_z)
    lid = box(name + "Lid", (0, 0, 0), (size[0] + 0.008, size[1] + 0.008, 0.008), m, bevel=0.004)
    lid.parent = o
    lid.location = (size[0] * 0.42 * lid_open, 0.01, size[2] / 2 + 0.008 + 0.02 * lid_open)
    lid.rotation_euler = (0, math.radians(-14 * lid_open), math.radians(6))
    # a film of muddy water in the bottom
    w = box(name + "Mud", (0, 0, -size[2] / 2 + 0.006), (size[0] - 0.01, size[1] - 0.01, 0.008),
            pbr("MudWater", (0.09, 0.075, 0.055), 0.08, 0.0, **{'Coat Weight': 1.0}))
    w.parent = o
    return o


def fill_container(box_obj, size, rng, n_rings=12, n_ear=6, hero_scale=1.0):
    """The pieces bundled together in the bottom of the tub (a heap, not laid out); the big diamond ring on top."""
    base = box_obj.location - Vector((0, 0, size[2] / 2 - 0.01))
    stones = ["diamond"] * 7 + ["ruby", "sapphire", "emerald", "diamond", "sapphire"]
    items = []
    for k in range(n_rings):
        a = rng.uniform(0, 6.28); rr = rng.uniform(0.0, 0.028)
        p = base + Vector((rr * math.cos(a) - 0.01, rr * math.sin(a), 0.0015 + 0.004 * (k % 3) + 0.006 * (rr < 0.012)))
        r = ring(f"Ring{k}", p, stone_r=rng.uniform(0.0022, 0.004), band="plat_dirty" if k % 3 else "gold_dirty",
                 stone=stones[k % len(stones)], upright=False, rot=(rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6), rng.uniform(0, 6.28)))
        items.append(r)
    for k in range(n_ear):
        a = rng.uniform(0, 6.28); rr = rng.uniform(0.0, 0.03)
        items.append(earring(f"Ear{k}", base + Vector((rr * math.cos(a), rr * math.sin(a), 0.006)), rng.uniform(0.002, 0.003)))
    hero = ring("HeroRing", base + Vector((0.012, 0.004, 0.012)), stone_r=0.0072 * hero_scale, band="plat_dirty", upright=True, band_r=0.0095,
                rot=(0.35, 0.1, 0.4), setting_h=0.002)
    return hero, items


# ============================================================================ the pavillon (suburban house)
def roller_shutter_mat(name):
    """White PVC roller-shutter slats (procedural horizontal grooves)."""
    m = pbr(name, (0.8, 0.8, 0.78), 0.45)
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Object'], sep.inputs[0])
    w = N.new("ShaderNodeTexWave"); w.wave_type = 'BANDS'; w.bands_direction = 'Z'; w.inputs['Scale'].default_value = 40
    L.new(tc.outputs['Object'], w.inputs['Vector'])
    bp = N.new("ShaderNodeBump"); bp.inputs['Strength'].default_value = 0.4; L.new(w.outputs['Fac'], bp.inputs['Height'])
    L.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m


def pavillon(origin=(0, 0, 0), w=9.0, d=8.0, floors=2, rot_z=0.0, name="House", stone=True, shutters=(0.55, 0.3, 0.0, 0.7, 0.45)):
    """A 1930s Paris-suburb pavillon: millstone (meuliere) ground storey, cream render above with stone quoins,
    a clay-tile roof, white roller shutters part-down over the windows, a zinc gutter and downpipe."""
    ox, oy, oz = origin
    fh = 2.9
    H = floors * fh
    meul = tex_mat("old_stone_wall", 0.45, tint=(0.95, 0.88, 0.78), name=name + "Meuliere", sat=0.6)
    render_ = tex_mat("plastered_wall_03", 0.4, tint=(0.95, 0.9, 0.8), name=name + "Render", sat=0.7) if stone else \
        tex_mat("plastered_wall_03", 0.4, tint=(0.85, 0.86, 0.84), name=name + "RenderG", sat=0.5)
    roof = tex_mat("clay_roof_tiles_02", 0.8, tint=(0.72, 0.5, 0.42), name=name + "Roof", sat=0.7)
    trim = pbr(name + "Trim", (0.82, 0.8, 0.76), 0.6)
    brick = tex_mat("red_brick_03", 0.9, tint=(0.8, 0.6, 0.5), name=name + "Brick", sat=0.6) if stone else trim
    rs = roller_shutter_mat(name + "Roller")
    glass_m = pbr(name + "Glass", (0.03, 0.035, 0.04), 0.04, 0.0, **{'Coat Weight': 1.0})
    curtain = fabric(name + "Curtain", (0.62, 0.58, 0.5), 0.9, 0.4, 300)
    zinc = pbr(name + "Zinc", (0.42, 0.44, 0.45), 0.35, 0.9)
    B = Builder(name)
    B.box((0, d / 2, fh / 2), (w, d, fh), meul if stone else render_)
    B.box((0, d / 2, fh + (H - fh) / 2), (w, d, H - fh), render_)
    B.box((0, d / 2, 0.25), (w + 0.06, d + 0.06, 0.5), pbr(name + "Plinth", (0.4, 0.39, 0.37), 0.8))
    for sx in (-1, 1):                                    # brick quoins at the corners
        for k in range(int(H / 0.3)):
            ln = 0.42 if k % 2 else 0.26
            B.box((sx * (w / 2 - ln / 2 + 0.02), -0.02, 0.15 + k * 0.3), (ln, 0.06, 0.26), brick)
    for k in range(floors):
        B.box((0, -0.04, (k + 1) * fh - 0.1), (w + 0.04, 0.1, 0.16), trim)
    pitch = math.radians(38); half = d / 2 + 0.4; rl = half / math.cos(pitch)
    for sgn in (-1, 1):
        B.box((0, d / 2 + sgn * half / 2, H + half * math.tan(pitch) / 2), (w + 0.6, rl, 0.12), roof, rot=(sgn * pitch, 0, 0))
    B.box((0, d / 2, H + half * math.tan(pitch) + 0.05), (w + 0.6, 0.25, 0.18), roof)
    B.box((w * 0.25, d * 0.6, H + 2.6), (0.6, 0.6, 1.6), brick)          # chimney
    cols = [-w / 2 + 1.6, -0.3, w / 2 - 1.6]
    wins = []
    si = 0
    for k in range(floors):
        z = k * fh + 1.55
        for i, x in enumerate(cols):
            if k == 0 and i == 1:
                B.box((x, -0.03, 1.15), (1.0, 0.08, 2.2), pbr(name + "DoorWood", (0.16, 0.1, 0.07), 0.45))
                B.box((x, -0.05, 2.33), (1.3, 0.1, 0.16), trim)
                B.box((x, -0.45, 0.09), (1.6, 0.8, 0.18), pbr(name + "Step", (0.5, 0.49, 0.47), 0.7))
                B.box((x + 0.3, -0.08, 1.05), (0.04, 0.03, 0.12), zinc)
                continue
            B.box((x, 0.02, z), (1.0, 0.04, 1.4), glass_m)
            B.box((x, 0.05, z), (1.0, 0.02, 1.4), curtain)
            B.box((x, -0.08, z - 0.75), (1.2, 0.18, 0.08), trim)
            B.box((x, -0.02, z), (0.05, 0.03, 1.4), trim)
            for sx in (-1, 1):
                B.box((x + sx * 0.54, -0.03, z), (0.08, 0.08, 1.45), trim)
            # roller shutter: box above, the slatted curtain drawn part-way down
            down = shutters[si % len(shutters)]; si += 1
            B.box((x, -0.07, z + 0.82), (1.16, 0.2, 0.24), rs)
            if down > 0.02:
                hh = 1.4 * down
                B.box((x, -0.04, z + 0.7 - hh / 2), (1.04, 0.03, hh), rs)
            wins.append(Vector((x, 0, z)))
    B.cyl((0, -0.5, H + 0.05), 0.06, w + 0.6, zinc, verts=12, rot=(0, math.radians(90), 0))
    dp_x = w / 2 - 0.5
    B.cyl((dp_x, -0.12, H / 2 + 0.2), 0.045, H - 0.4, zinc, verts=12)
    house = B.done((ox, oy, oz), rot_z)
    return house, dict(downpipe=Vector((ox + dp_x, oy - 0.12, 0)), door=Vector((ox - 0.3, oy - 0.4, 0)), height=H)


# ============================================================================ fast batched geometry
class Builder:
    """Accumulate many cuboids into ONE mesh (bmesh, no bpy.ops per part): facades with thousands of mouldings and bars."""
    def __init__(self, name):
        self.name = name; self.bm = bmesh.new(); self.mats = []

    def _mi(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def box(self, loc, size, mat, rot=(0, 0, 0)):
        from mathutils import Matrix, Euler
        M = Matrix.Translation(Vector(loc)) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal((*size, 1))
        r = bmesh.ops.create_cube(self.bm, size=1.0, matrix=M)
        mi = self._mi(mat)
        fs = {f for v in r["verts"] for f in v.link_faces}
        for f in fs:
            f.material_index = mi
        return self

    def cyl(self, loc, r, depth, mat, verts=12, rot=(0, 0, 0)):
        from mathutils import Matrix, Euler
        M = Matrix.Translation(Vector(loc)) @ Euler(rot).to_matrix().to_4x4()
        res = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=verts, radius1=r, radius2=r, depth=depth, matrix=M)
        mi = self._mi(mat)
        for f in {f for v in res["verts"] for f in v.link_faces}:
            f.material_index = mi
        return self

    def done(self, loc=(0, 0, 0), rot_z=0.0):
        me = bpy.data.meshes.new(self.name); self.bm.to_mesh(me); self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        o = bpy.data.objects.new(self.name, me); bpy.context.collection.objects.link(o)
        o.location = loc; o.rotation_euler = (0, 0, rot_z)
        return o
