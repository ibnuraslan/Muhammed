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


def model_h(aid, loc, height, rot_z=0.0):
    """Poly Haven model scaled to a target height (m), standing on loc.z."""
    try:
        root, ms = ph.model(aid, loc=(0, 0, 0), rot_z=rot_z)
    except Exception as e:
        print("[dd] model skipped", aid, e); return None
    lo, hi = ph.bounds(ms)
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
def person(name, gender=1.0, years=40, cloth="male_casualsuit01", hair="short02", cval=0.25, hv=0.3, sat=1.0, hue=0.5,
           skin=None, height=0.5, weight=0.45, shoes="shoes02"):
    h = Human(name, gender=gender, years=years, muscle=0.5, weight=weight, height=height, eyelashes="eyelashes01",
              skin=skin or ("middleage_lightskinned_female_diffuse.png" if gender < 0.5 else "middleage_lightskinned_male_diffuse.png"))
    add_asset(h, "clothes", cloth, val=cval, rough=0.7, sat=sat, hue=hue)
    add_asset(h, "clothes", shoes, val=0.2, rough=0.4)
    if hair:
        add_asset(h, "hair", hair, val=hv, rough=0.45)
    return h


def officer(name, years=40, seed=0, gender=1.0):
    """Plain-clothes detective: dark navy / charcoal jacket."""
    vals = (0.16, 0.2, 0.13, 0.22)
    hairs = ("short02", "short04", "short03", "short01") if gender > 0.5 else ("bob01", "ponytail01", "bob02")
    # (no casualsuit02/04/female_casualsuit01/02: their T-shirts carry a printed logo)
    cloth = ("male_casualsuit05", "male_casualsuit01", "male_casualsuit05", "male_casualsuit03")[seed % 4] if gender > 0.5 else "female_elegantsuit01"
    return person(name, gender, years, cloth, hairs[seed % len(hairs)], cval=vals[seed % 4], hv=0.25 + 0.1 * (seed % 2),
                  sat=0.5, height=0.45 + 0.05 * (seed % 3))


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
def diamond_mesh(name, r=0.01, table=0.56, crown=0.16, pavilion=0.43, n=16):
    """A round brilliant: girdle ring, crown up to a flat table, pavilion down to a culet point. r = girdle radius."""
    bm = bmesh.new()
    g = [bm.verts.new((r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n), 0.0)) for k in range(n)]
    g2 = [bm.verts.new((r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n), r * 0.04)) for k in range(n)]
    t = [bm.verts.new((r * table * math.cos(2 * math.pi * (k + 0.5) / n), r * table * math.sin(2 * math.pi * (k + 0.5) / n), r * (0.04 + crown * 2)))
         for k in range(n)]
    cul = bm.verts.new((0, 0, -r * pavilion * 2))
    for k in range(n):
        k1 = (k + 1) % n
        bm.faces.new((g[k], g[k1], g2[k1], g2[k]))
        bm.faces.new((g2[k], g2[k1], t[k]))
        bm.faces.new((t[k], g2[k1], t[k1]))
        bm.faces.new((g[k1], g[k], cul))
    bm.faces.new(t)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    for p in me.polygons:
        p.use_smooth = False
    return o


_MATS = {}


def jewel_mats():
    if not _MATS:
        d = bpy.data.materials.new("Diamond"); d.use_nodes = True
        p = d.node_tree.nodes["Principled BSDF"]
        p.inputs['Base Color'].default_value = (1, 1, 1, 1); p.inputs['Transmission Weight'].default_value = 1.0
        p.inputs['IOR'].default_value = 2.42; p.inputs['Roughness'].default_value = 0.0
        _MATS["diamond"] = d
        _MATS["plat"] = pbr("Platinum", (0.78, 0.78, 0.8), 0.12, 1.0)
        _MATS["gold"] = pbr("Gold", (0.95, 0.72, 0.36), 0.14, 1.0)
        for nm, col in (("ruby", (0.6, 0.02, 0.05)), ("sapphire", (0.03, 0.08, 0.5)), ("emerald", (0.02, 0.4, 0.15))):
            g = bpy.data.materials.new(nm); g.use_nodes = True; q = g.node_tree.nodes["Principled BSDF"]
            q.inputs['Base Color'].default_value = (*col, 1); q.inputs['Transmission Weight'].default_value = 1.0
            q.inputs['IOR'].default_value = 1.77; q.inputs['Roughness'].default_value = 0.0
            _MATS[nm] = g
    return _MATS


def ring(name, loc, stone_r=0.004, band="plat", stone="diamond", rot=(0, 0, 0), band_r=0.0095, upright=True):
    """A ring: torus band with a stone on top. Returns the parent empty."""
    M = jewel_mats()
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    bpy.ops.mesh.primitive_torus_add(major_radius=band_r, minor_radius=0.0013, major_segments=48, minor_segments=10,
                                     location=(0, 0, 0), rotation=(math.radians(90) if upright else 0, 0, 0))
    b = bpy.context.active_object; b.name = name + "_band"; b.data.materials.append(M[band]); b.parent = root
    bpy.ops.object.shade_smooth()
    top = Vector((0, 0, band_r + 0.0012)) if upright else Vector((band_r, 0, 0.0012))
    st = diamond_mesh(name + "_stone", stone_r); st.data.materials.append(M[stone]); st.parent = root
    st.location = top + Vector((0, 0, stone_r * 0.8))
    # four prongs
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        pr = cyl(name + "_prong", top + Vector((stone_r * 0.9 * math.cos(a), stone_r * 0.9 * math.sin(a), stone_r * 0.7)), 0.0005, stone_r * 1.6, M[band], verts=6)
        pr.parent = root
    root.location = loc; root.rotation_euler = rot
    return root


def earring(name, loc, r=0.003, stone="diamond"):
    M = jewel_mats()
    st = diamond_mesh(name, r); st.data.materials.append(M[stone]); st.location = loc
    cyl(name + "_post", Vector(loc) + Vector((0, 0, -r * 1.4)), 0.0004, 0.01, M["plat"], verts=6)
    return st


def container(name, loc, size=(0.24, 0.17, 0.09), rot_z=0.0, dirt=0.75):
    """A milky plastic food box with no lid (open top), slightly grimy."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    bm = bmesh.new(); bm.from_mesh(o.data)
    for f in list(bm.faces):
        if f.normal.z > 0.9:
            bm.faces.remove(f)
    bm.to_mesh(o.data); bm.free()
    bv = o.modifiers.new("bev", 'BEVEL'); bv.width = 0.012; bv.segments = 3
    so = o.modifiers.new("sol", 'SOLIDIFY'); so.thickness = 0.0025
    m = bpy.data.materials.new(name + "Plastic"); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    p.inputs['Base Color'].default_value = (0.82, 0.84, 0.82, 1); p.inputs['Roughness'].default_value = 0.45
    p.inputs['Transmission Weight'].default_value = 0.35
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 25
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[6].default_value = (0.55, 0.57, 0.56, 1)
    mx.inputs[7].default_value = (0.22, 0.2, 0.17, 1)
    mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.45; mr.inputs['From Max'].default_value = 0.75
    mr.inputs['To Max'].default_value = dirt
    L.new(nz.outputs['Fac'], mr.inputs['Value']); L.new(mr.outputs[0], mx.inputs['Factor']); L.new(mx.outputs[2], p.inputs['Base Color'])
    o.data.materials.append(m)
    o.location = Vector(loc) + Vector((0, 0, size[2] / 2)); o.rotation_euler = (0, 0, rot_z)
    return o


def fill_container(box_obj, size, rng, n_rings=12, n_ear=6, hero_scale=2.4):
    """Rings and earrings resting in the bottom of the container, one big diamond ring on top in the middle."""
    base = box_obj.location - Vector((0, 0, size[2] / 2 - 0.004))
    # a dark cloth the pieces were wrapped in, crumpled in the bottom
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=30, y_subdivisions=24, size=1, location=base + Vector((0, 0, 0.0015)))
    cl = bpy.context.active_object; cl.name = "Cloth"; cl.scale = (size[0] * 0.92, size[1] * 0.9, 1); cl.rotation_euler = box_obj.rotation_euler
    dsp = cl.modifiers.new("crumple", 'DISPLACE'); tx = bpy.data.textures.new("Crumple", 'CLOUDS'); tx.noise_scale = 0.25
    dsp.texture = tx; dsp.strength = 0.006; dsp.mid_level = 0.3
    cl.data.materials.append(fabric("Velvet", (0.025, 0.028, 0.035), 0.9, 0.8, 300))
    bpy.ops.object.shade_smooth()
    stones = ["diamond"] * 7 + ["ruby", "sapphire", "emerald", "diamond", "sapphire"]
    items = []
    for k in range(n_rings):
        x = rng.uniform(-size[0] / 2 + 0.025, size[0] / 2 - 0.025); y = rng.uniform(-size[1] / 2 + 0.025, size[1] / 2 - 0.025)
        r = ring(f"Ring{k}", base + Vector((x, y, 0.0012)), stone_r=rng.uniform(0.0025, 0.0045), band="plat" if k % 3 else "gold",
                 stone=stones[k % len(stones)], upright=False, rot=(rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), rng.uniform(0, 6.28)))
        items.append(r)
    for k in range(n_ear):
        x = rng.uniform(-size[0] / 2 + 0.02, size[0] / 2 - 0.02); y = rng.uniform(-size[1] / 2 + 0.02, size[1] / 2 - 0.02)
        items.append(earring(f"Ear{k}", base + Vector((x, y, 0.004)), rng.uniform(0.0022, 0.0035)))
    hero = ring("HeroRing", base + Vector((0.01, 0.0, 0.006)), stone_r=0.0105, band="plat", upright=False, band_r=0.0105,
                rot=(0.08, -0.05, 0.4))
    return hero, items


# ============================================================================ the pavillon (suburban house)
def pavillon(origin=(0, 0, 0), w=9.0, d=8.0, floors=2, rot_z=0.0, name="House", stone=True):
    """A 1930s Paris-suburb pavillon: millstone (meuliere) walls, a pitched clay-tile roof, white shutters, zinc gutter."""
    ox, oy, oz = origin
    fh = 2.9
    H = floors * fh
    walls = tex_mat("old_stone_wall", 0.45, tint=(0.95, 0.88, 0.78), name=name + "Meuliere", sat=0.6) if stone else \
        tex_mat("plastered_wall_03", 0.5, tint=(0.92, 0.88, 0.8), name=name + "Plaster")
    roof = tex_mat("clay_roof_tiles_02", 0.8, tint=(0.75, 0.5, 0.4), name=name + "Roof")
    trim = pbr(name + "Trim", (0.86, 0.84, 0.8), 0.6)
    shut = pbr(name + "Shutter", (0.82, 0.83, 0.82), 0.5)
    glass_m = pbr(name + "Glass", (0.03, 0.035, 0.04), 0.04, 0.0, **{'Coat Weight': 1.0})
    zinc = pbr(name + "Zinc", (0.42, 0.44, 0.45), 0.35, 0.9)
    parts = []
    parts.append(box(name + "Walls", (0, d / 2, H / 2), (w, d, H), walls))
    parts.append(box(name + "Plinth", (0, d / 2, 0.25), (w + 0.06, d + 0.06, 0.5), pbr(name + "Plinth", (0.45, 0.44, 0.42), 0.8)))
    for k in range(floors):
        parts.append(box(name + "Band", (0, -0.03, (k + 1) * fh - 0.1), (w + 0.04, 0.08, 0.16), trim))
    # roof: two slopes meeting at a ridge along x
    pitch = math.radians(38); half = d / 2 + 0.4; rl = half / math.cos(pitch)
    for sgn in (-1, 1):
        r = box(name + "RoofSlope", (0, d / 2 + sgn * half / 2, H + half * math.tan(pitch) / 2), (w + 0.6, rl, 0.12), roof,
                rot=(sgn * pitch, 0, 0))
        parts.append(r)
    # gable infill
    bm = bmesh.new()
    for sx in (-w / 2, w / 2):
        v = [bm.verts.new((sx, 0, H)), bm.verts.new((sx, d, H)), bm.verts.new((sx, d / 2, H + (d / 2) * math.tan(pitch)))]
        bm.faces.new(v)
    me = bpy.data.meshes.new(name + "Gable"); bm.to_mesh(me); bm.free()
    g = bpy.data.objects.new(name + "Gable", me); bpy.context.collection.objects.link(g); g.data.materials.append(walls)
    g.modifiers.new("s", 'SOLIDIFY').thickness = 0.2
    parts.append(g)
    # windows with shutters on the front (y = 0 face)
    wins = []
    cols = [-w / 2 + 1.6, -0.3, w / 2 - 1.6]
    for k in range(floors):
        z = k * fh + 1.55
        for i, x in enumerate(cols):
            if k == 0 and i == 1:
                # front door
                parts.append(box(name + "Door", (x, -0.02, 1.15), (1.0, 0.06, 2.2), pbr(name + "DoorWood", (0.14, 0.09, 0.06), 0.5)))
                parts.append(box(name + "DoorFrame", (x, -0.03, 2.3), (1.3, 0.08, 0.14), trim))
                parts.append(box(name + "Step", (x, -0.4, 0.09), (1.6, 0.8, 0.18), pbr(name + "Step", (0.5, 0.49, 0.47), 0.7)))
                continue
            parts.append(box(name + "Win", (x, -0.015, z), (1.0, 0.04, 1.4), glass_m))
            parts.append(box(name + "Sill", (x, -0.08, z - 0.75), (1.2, 0.18, 0.08), trim))
            parts.append(box(name + "Lintel", (x, -0.03, z + 0.76), (1.2, 0.08, 0.14), trim))
            parts.append(box(name + "Mull", (x, -0.03, z), (0.05, 0.03, 1.4), trim))
            for sx in (-1, 1):
                s = box(name + "Shut", (x + sx * 0.78, -0.06, z), (0.5, 0.04, 1.45), shut)
                parts.append(s)
                for j in range(9):
                    parts.append(box(name + "Slat", (x + sx * 0.78, -0.085, z - 0.6 + j * 0.15), (0.44, 0.012, 0.03), shut))
            wins.append(Vector((x, 0, z)))
    # gutter + downpipe at the front right
    parts.append(cyl(name + "Gutter", (0, -0.5, H + 0.05), 0.06, w + 0.6, zinc, verts=12, rot=(0, math.radians(90), 0)))
    dp_x = w / 2 - 0.5
    parts.append(cyl(name + "Downpipe", (dp_x, -0.12, H / 2), 0.045, H, zinc, verts=12))
    house = join(parts, name)
    house.location = (ox, oy, oz); house.rotation_euler = (0, 0, rot_z)
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
