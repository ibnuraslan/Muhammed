"""Part 3 sets built from the shared library (ship, sea, deveau, look, grade) plus Part 3 assets in this folder.
Exterior moods are rich and warm (Atrium): low winter sun, golden light on wood and canvas, deep blue-green sea;
the gale is the one cold, dark location."""
import os, sys, math, random
import numpy as np
import bpy
from mathutils import Vector, Matrix, Euler
import ship, sea, ph
import crew

E = os.environ.get
HDRI = {
    "day":    ("kloofendal_48d_partly_cloudy_puresky", 1.0),
    "gold":   ("kloofendal_38d_partly_cloudy_puresky", 1.0),
    "dusk":   ("qwantani_dusk_2_puresky", 1.3),
    "storm":  ("overcast_soil_puresky", 0.22),
    "sunset": ("qwantani_sunset_puresky", 1.2),
    "grey":   ("kloofendal_overcast_puresky", 0.7),
}
SUN = {   # energy, colour, angle (deg)
    "day": (3.2, (1.0, 0.86, 0.68), 3.0), "gold": (3.6, (1.0, 0.78, 0.55), 2.0), "dusk": (1.2, (1.0, 0.55, 0.32), 2.0),
    "storm": (0.0, (0.8, 0.85, 0.9), 10.0), "sunset": (2.6, (1.0, 0.62, 0.36), 1.5), "grey": (1.2, (0.98, 0.92, 0.84), 12.0),
}
WATER = {  # deep, crest, fog colour
    "day": ((0.004, 0.016, 0.022), (0.02, 0.085, 0.08), (0.55, 0.58, 0.62)),
    "gold": ((0.005, 0.017, 0.024), (0.03, 0.09, 0.085), (0.62, 0.6, 0.58)),
    "dusk": ((0.003, 0.008, 0.016), (0.015, 0.04, 0.05), (0.42, 0.36, 0.42)),
    "storm": ((0.002, 0.006, 0.008), (0.012, 0.035, 0.035), (0.12, 0.13, 0.14)),
    "sunset": ((0.005, 0.012, 0.02), (0.03, 0.06, 0.07), (0.7, 0.52, 0.42)),
    "grey": ((0.004, 0.012, 0.016), (0.02, 0.06, 0.06), (0.4, 0.42, 0.44)),
}


def sun_dir(az, el):
    a, e = math.radians(az), math.radians(el)
    return Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)))


def exterior(mood="day", sky_rot=0.0, sun_az=150.0, sun_el=18.0, strength=None):
    aid, s = HDRI[mood]
    sea.sky(strength=strength if strength is not None else s, rot_deg=sky_rot, res="4k", aid=aid)
    en, col, ang = SUN[mood]
    if en > 0:
        sn = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); bpy.context.scene.collection.objects.link(sn)
        sn.data.energy = en; sn.data.color = col; sn.data.angle = math.radians(ang)
        sn.rotation_euler = (-sun_dir(sun_az, sun_el)).to_track_quat('-Z', 'Y').to_euler()
        return sn
    return None


def water(mood):
    d, c, f = WATER[mood]
    return sea.water_material(deep=d, crest=c, fog_color=f)


def spare_course(s, name, wind=(0.25, -1.0, 0)):
    """The spare sail Deveau's men bent on in place of the lost fore course: clean new canvas on the course yard."""
    Y = s["spars"]["yards"]
    a, b, _ = Y["course"]
    m = ship.canvas(name + "_spare", wet=0.2, dirt=0.15, color=(0.74, 0.68, 0.56))
    tl = a.lerp(b, 0.03) - Vector((0, 0, 0.12)); tr = b.lerp(a, 0.03) - Vector((0, 0, 0.12))
    bl = a + Vector((0, 0, -6.6)) + (b - a) * 0.06; br = b + Vector((0, 0, -6.6)) - (b - a) * 0.06
    o = ship.sail_mesh(f"{name}_sail_spare", (tl, tr, br, bl), 26, 18, 1.25, Vector(wind).normalized(), m, s["coll"], seed=21)
    o.parent = s["root"]
    return o


def mc(sails="spare", wind=(0.25, -1.0, 0), wet=0.5, detail=True, gap=True):
    st = "found" if sails in ("spare", "found") else sails
    s = ship.build("MC", sails=st, rail_gap=(-2.7, -0.6, "S") if gap else None, wind=wind, wet=wet, detail=detail,
                   hatches_off=False)
    if sails == "spare":
        spare_course(s, "MC", wind)
    return s


def dg(sails="full", wind=(0.25, -1.0, 0), wet=0.4, detail=False):
    return ship.build("DG", sails=sails, wind=wind, wet=wet, detail=detail, hatches_off=False)


def set_ship(s, loc=(0, 0, 0), heading=0.0, heel=0.0, pitch=0.0):
    s["root"].matrix_world = (Matrix.Translation(loc) @ Matrix.Rotation(math.radians(heading), 4, 'Z')
                              @ Matrix.Rotation(math.radians(pitch), 4, 'Y') @ Matrix.Rotation(math.radians(-heel), 4, 'X'))
    bpy.context.view_layer.update()
    return s["root"].matrix_world.copy()


def local_wind(world_wind, heading):
    return Matrix.Rotation(math.radians(-heading), 3, 'Z') @ Vector(world_wind).normalized()


def ocean_around(center, hulls=(), mood="day", size=200, res=None, scale=1.6, chop=1.4, wind=11.0, foam=0.3,
                 wind_dir=(0.3, -1.0, 0), time=11.0, cut=None, far=True):
    mat = water(mood)
    res = res or int(E("OCEAN_RES", "20"))
    wd = Vector(wind_dir)
    o = sea.ocean(size=size, res=res, scale=scale, chop=chop, wind=wind, repeat=3, foam=foam, mat=mat,
                  direction=math.degrees(math.atan2(wd.y, wd.x)), hulls=hulls, loc=center, cut=cut, time=time)
    if far:
        sea.far_sea(size * 1.45, mat=mat, center=center[:2])
    return o


# ----------------------------------------------------------------------------- people on a ship
def on_ship(SHIP, x, y, heading_local, drop=0.0):
    """Place matrix for a man standing on the ship's deck at local (x, y), facing heading_local (0 = toward bow)."""
    z = ship.zdeck(x) + 0.006
    return SHIP @ crew.place((x, y, z), heading_local, drop=drop)


def deck_world(SHIP, x, y, dz=0.0):
    return SHIP @ Vector((x, y, ship.zdeck(x) + dz))


# ----------------------------------------------------------------------------- terrain pieces
def terrain_mat(name="land", scrub=(0.05, 0.06, 0.03), rock=(0.32, 0.28, 0.22), sand=(0.42, 0.36, 0.26), scale=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Position'], sep.inputs[0])
    # slope: steep faces are limestone, gentle ones scrub; low bands near sea level sand
    dp = N.new("ShaderNodeVectorMath"); dp.operation = 'DOT_PRODUCT'; dp.inputs[1].default_value = (0, 0, 1)
    L.new(geo.outputs['Normal'], dp.inputs[0])
    sl = N.new("ShaderNodeMapRange"); sl.inputs['From Min'].default_value = 0.6; sl.inputs['From Max'].default_value = 0.85
    L.new(dp.outputs['Value'], sl.inputs['Value'])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 0.02 / scale; nz.inputs['Detail'].default_value = 12
    L.new(geo.outputs['Position'], nz.inputs['Vector'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[6].default_value = (*rock, 1); mx.inputs[7].default_value = (*scrub, 1)
    sl2 = N.new("ShaderNodeMath"); sl2.operation = 'MULTIPLY'; L.new(sl.outputs[0], sl2.inputs[0]); L.new(nz.outputs['Fac'], sl2.inputs[1])
    sl3 = N.new("ShaderNodeMath"); sl3.operation = 'MULTIPLY'; sl3.inputs[1].default_value = 1.8; sl3.use_clamp = True
    L.new(sl2.outputs[0], sl3.inputs[0]); L.new(sl3.outputs[0], mx.inputs['Factor'])
    bz = N.new("ShaderNodeMapRange"); bz.inputs['From Min'].default_value = 6 * scale; bz.inputs['From Max'].default_value = 1 * scale
    L.new(sep.outputs['Z'], bz.inputs['Value'])
    mx2 = N.new("ShaderNodeMix"); mx2.data_type = 'RGBA'; mx2.inputs[7].default_value = (*sand, 1)
    L.new(mx.outputs[2], mx2.inputs[6]); L.new(bz.outputs[0], mx2.inputs['Factor'])
    L.new(mx2.outputs[2], p.inputs['Base Color'])
    bump = N.new("ShaderNodeBump"); bump.inputs['Strength'].default_value = 0.4
    n2 = N.new("ShaderNodeTexNoise"); n2.inputs['Scale'].default_value = 0.2 / scale; n2.inputs['Detail'].default_value = 14
    L.new(geo.outputs['Position'], n2.inputs['Vector']); L.new(n2.outputs['Fac'], bump.inputs['Height']); L.new(bump.outputs['Normal'], p.inputs['Normal'])
    p.inputs['Roughness'].default_value = 0.9
    return m


def town(name, rng_seed, pts, mat_walls, mat_roof, size=(9, 7, 7)):
    """Low-detail houses (seen from a mile off): boxes with pitched roofs on given points (x, y, z)."""
    rng = random.Random(rng_seed)
    objs = []
    for i, (x, y, z) in enumerate(pts):
        w = size[0] * rng.uniform(0.6, 1.4); d = size[1] * rng.uniform(0.6, 1.3); h = size[2] * rng.uniform(0.7, 1.6)
        a = rng.uniform(-0.4, 0.4)
        b = ship.box(f"{name}_h{i}", (x, y, z + h / 2 - 1), (w, d, h), mat_walls[i % len(mat_walls)], rot=(0, 0, a))
        r = ship.box(f"{name}_r{i}", (x, y, z + h - 1 + 0.9), (w * 1.04, d * 0.75, 1.8), mat_roof, rot=(0.0, 0, a))
        objs += [b, r]
    return objs


# ----------------------------------------------------------------------------- real coasts (terrain.py)
import terrain as TR


def coast(name, box, z, origin, mat=None, res=500, vex=1.0, clip_low=-40.0):
    """box = (lat_n, lon_w, lat_s, lon_e). Returns the relief object in local metres around origin (lat, lon)."""
    hm, info = TR.heightmap(box[0], box[1], box[2], box[3], z)
    return TR.relief_mesh(name, hm, info, origin, scale=1.0, vex=vex, res=res, clip_low=clip_low, mat=mat or terrain_mat(name + "_m"))


def rain(name, center, size, count=20000, drop_len=0.5, wind=(0.35, -0.15), seed=3):
    """Rain streaks: points in a box instanced with thin elongated drops, slanted by the wind."""
    rng = np.random.default_rng(seed)
    P_ = (rng.random((count, 3)) - 0.5) * np.array(size) + np.array(center)
    me = bpy.data.meshes.new(name); me.from_pydata(P_.tolist(), [], []); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    bpy.ops.mesh.primitive_cylinder_add(vertices=5, radius=0.0009, depth=drop_len)
    drop = bpy.context.active_object; drop.name = name + "_drop"
    w = Vector((wind[0], wind[1], -1)).normalized()
    drop.rotation_euler = w.to_track_quat('Z', 'Y').to_euler(); bpy.ops.object.transform_apply(rotation=True)
    m = bpy.data.materials.new(name + "_m"); m.use_nodes = True; q = m.node_tree.nodes["Principled BSDF"]
    q.inputs['Base Color'].default_value = (0.8, 0.85, 0.9, 1); q.inputs['Transmission Weight'].default_value = 0.6
    q.inputs['Roughness'].default_value = 0.2; q.inputs['Alpha'].default_value = 0.2
    drop.data.materials.append(m); drop.hide_render = True; drop.hide_viewport = True
    ng = bpy.data.node_groups.new(name + "_gn", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = ng.nodes; L = ng.links; gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    mp = N.new("GeometryNodeMeshToPoints"); L.new(gi.outputs[0], mp.inputs['Mesh'])
    oi = N.new("GeometryNodeObjectInfo"); oi.inputs['Object'].default_value = drop
    ip = N.new("GeometryNodeInstanceOnPoints"); L.new(mp.outputs['Points'], ip.inputs['Points']); L.new(oi.outputs['Geometry'], ip.inputs['Instance'])
    L.new(ip.outputs['Instances'], go.inputs[0])
    md = o.modifiers.new("rain", "NODES"); md.node_group = ng
    o.visible_shadow = False
    return o


def ripple_bands(name, center, normal=(0, 0, 1), r0=0.02, r1=0.12, n=3, phase=0.0, color=(1.0, 0.45, 0.12), strength=3.0):
    """Location marker: filled soft orange bands expanding from a point (each band a flat annulus, soft edges)."""
    objs = []
    n_ = Vector(normal).normalized()
    Mq = n_.to_track_quat('Z', 'Y').to_matrix().to_4x4(); Mq.translation = Vector(center)
    for k in range(n):
        f = ((phase + k / n) % 1.0)
        r = r0 + (r1 - r0) * f; w = (r1 - r0) / n * 0.7
        a = (1 - f) ** 1.5
        bpy.ops.mesh.primitive_circle_add(vertices=64, radius=1, fill_type='NOTHING')
        c = bpy.context.active_object; c.name = f"{name}{k}"
        me = c.data
        bm_ = __import__("bmesh").new(); bm_.from_mesh(me)
        ret = __import__("bmesh").ops.extrude_edge_only(bm_, edges=bm_.edges[:])
        for v in [e for e in ret["geom"] if isinstance(e, __import__("bmesh").types.BMVert)]:
            v.co *= (r - w) / max(r, 1e-6)
        bm_.to_mesh(me); bm_.free()
        c.matrix_world = Mq @ Matrix.Diagonal((r, r, 1, 1))
        m = bpy.data.materials.new(f"{name}{k}_m"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
        N.remove(N["Principled BSDF"])
        em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (*color, 1); em.inputs['Strength'].default_value = strength * a
        tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader"); mx.inputs[0].default_value = 0.35 + 0.6 * a
        L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], N["Material Output"].inputs['Surface'])
        me.materials.append(m); c.visible_shadow = False
        objs.append(c)
    # the filled centre dot
    bpy.ops.mesh.primitive_circle_add(vertices=48, radius=r0 * 0.8, fill_type='NGON')
    d = bpy.context.active_object; d.name = name + "_dot"; d.matrix_world = Mq @ Matrix.Translation((0, 0, 0.0005))
    m = bpy.data.materials.new(name + "_dot_m"); m.use_nodes = True; N = m.node_tree.nodes
    N.remove(N["Principled BSDF"]); em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (*color, 1); em.inputs['Strength'].default_value = strength * 1.4
    m.node_tree.links.new(em.outputs[0], N["Material Output"].inputs['Surface']); d.data.materials.append(m)
    objs.append(d)
    return objs
