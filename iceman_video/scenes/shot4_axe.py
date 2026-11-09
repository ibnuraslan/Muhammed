"""Shot 4 - Macro: the Iceman's copper axe, half-buried in glacier snow, blue hour + faint firelight."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy, bmesh
from mathutils import Vector
from common import *
from terrain import fbm, perlin

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
OUT = arg('--out', '/tmp/shot4'); FRAMES = arg('--frames', 1); STEP = arg('--step', 1)
s = reset(samples=arg('--samples', 64), exposure=0.0)
s.cycles.max_bounces = 8

# ---------------------------------------------------------------- snow field
N = 900; SZ = 1.6
yy, xx = np.mgrid[0:N, 0:N].astype(np.float64)
X = (xx / (N - 1) - 0.5) * SZ; Y = (yy / (N - 1) - 0.5) * SZ
drift = fbm((N, N), 5, 6, 1.2) * 0.035 + fbm((N, N), 9, 5, 9.0) * 0.006
lumps = np.maximum(fbm((N, N), 17, 5, 22.0), 0) ** 1.5 * 0.010
warp = fbm((N, N), 23, 4, 3.0) * 0.08
ripples = (np.sin((X * 0.8 + Y * 0.6 + warp) * 2 * np.pi * 28) * 0.5 + 0.5) ** 2 * 0.0014 * (fbm((N, N), 29, 3, 4.0) * 0.5 + 0.6)
grain = fbm((N, N), 13, 4, 70.0) * 0.0010
H = drift + lumps + ripples + grain

HAFT_R = 0.016
def axis_y(x):
    return 0.02 * np.sin(x * 2.2) - 0.01

inside = (X > -0.46) & (X < 0.26)
d = np.abs(Y - axis_y(X))
d = np.where(inside, d, np.hypot(d, np.minimum(np.abs(X + 0.46), np.abs(X - 0.26))))
# variable burial along the haft; head end (x > 0.05) left exposed
bury = 0.5 + 0.5 * np.sin(X * 19 + 2.0) * np.cos(X * 7.0)
bury = np.clip(bury * 1.4 - 0.45, 0, 1) * np.clip((0.05 - X) / 0.12, 0, 1)
snow_level_at_axe = 0.002 + bury * 0.026 + perlin(X * 40, Y * 40, 3) * 0.003
w = np.exp(-(d / 0.032) ** 2)
# blade / fork footprint: snow sits just below the copper
bx0, by0 = 0.17, float(axis_y(0.17))
dh = np.hypot(np.maximum(np.abs(X - (bx0 + 0.04)) - 0.05, 0), np.maximum(np.abs(Y - (by0 + 0.07)) - 0.06, 0))
wb = np.exp(-(dh / 0.025) ** 2)
rim = np.exp(-((d - 0.042) / 0.018) ** 2) * 0.005
H = H - np.median(H)
H = H * (1 - w) + snow_level_at_axe * w + rim * (1 - wb)
H = H * (1 - wb) + (0.0035 + grain * 2) * wb
ground = grid_mesh("Snow", H.astype(np.float32), SZ, SZ, 1.0)

from common import snow_material
ground.data.materials.append(snow_material())

# ---------------------------------------------------------------- axe haft (yew)
def wood_material():
    m = bpy.data.materials.new("Yew"); nt, Nn, L = nodes_of(m); Nn.clear()
    out = Nn.new("ShaderNodeOutputMaterial"); tc = Nn.new("ShaderNodeTexCoord")
    mp = Nn.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (1, 40, 40)
    L.new(tc.outputs['Object'], mp.inputs['Vector'])
    wave = Nn.new("ShaderNodeTexWave"); wave.wave_type = 'BANDS'; wave.bands_direction = 'X'
    wave.inputs['Scale'].default_value = 1.5; wave.inputs['Distortion'].default_value = 12
    wave.inputs['Detail'].default_value = 6; wave.inputs['Detail Scale'].default_value = 2
    # grain runs along the haft (x axis) -> stretch noise along x
    mp2 = Nn.new("ShaderNodeMapping"); mp2.inputs['Scale'].default_value = (4, 90, 90)
    L.new(tc.outputs['Object'], mp2.inputs['Vector'])
    gn = Nn.new("ShaderNodeTexNoise"); gn.inputs['Scale'].default_value = 1.0; gn.inputs['Detail'].default_value = 10
    L.new(mp2.outputs[0], gn.inputs['Vector'])
    ramp = Nn.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.05, 0.022, 0.010, 1)
    ramp.color_ramp.elements[1].color = (0.42, 0.21, 0.09, 1)
    L.new(gn.outputs['Fac'], ramp.inputs['Fac'])
    p = Nn.new("ShaderNodeBsdfPrincipled"); L.new(ramp.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.78; p.inputs['Coat Weight'].default_value = 0.0
    bump = Nn.new("ShaderNodeBump"); bump.inputs['Strength'].default_value = 1.0; bump.inputs['Distance'].default_value = 0.002
    L.new(gn.outputs['Fac'], bump.inputs['Height']); L.new(bump.outputs['Normal'], p.inputs['Normal'])
    L.new(p.outputs[0], out.inputs['Surface'])
    return m

def tube_along(points, radii, name, mat, res=24):
    """Lofted tube through 3D points with per-point radius (smooth), built with bmesh."""
    bm = bmesh.new()
    pts = [Vector(p) for p in points]
    rings = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        up = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((0, 1, 0))
        u = t.cross(up).normalized(); v = t.cross(u).normalized()
        ring = []
        for k in range(res):
            a = 2 * math.pi * k / res
            # slightly irregular cross-section (hand carved)
            rr = radii[i] * (1 + 0.04 * math.sin(3 * a + i * 0.3) + 0.03 * math.cos(5 * a + i * 0.7))
            ring.append(bm.verts.new(p + (u * math.cos(a) + v * math.sin(a)) * rr))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(res):
            bm.faces.new((rings[i][k], rings[i][(k + 1) % res], rings[i + 1][(k + 1) % res], rings[i + 1][k]))
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for f in me.polygons: f.use_smooth = True
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    o.data.materials.append(mat)
    return o

wood = wood_material()
xs = np.linspace(-0.44, 0.17, 70)[:-1]
pts_all = [(x, float(axis_y(x)), HAFT_R * 0.65) for x in xs]
r_all = [HAFT_R * (0.85 + 0.15 * (x + 0.44) / 0.61) * (1 + 0.05 * math.sin(x * 60)) for x in xs]
r_all[0] *= 0.7; r_all[1] *= 0.9
fork_pts = []; fork_r = []
for k, a in enumerate(np.linspace(0, math.radians(72), 26)):
    R = 0.075
    cx, cy = 0.17, float(axis_y(0.17)) + R
    fork_pts.append((cx + R * math.sin(a), cy - R * math.cos(a), HAFT_R * 0.65 + 0.004 * math.sin(a)))
    fork_r.append(HAFT_R * (1.0 + 0.30 * math.sin(a * 1.2)))
haft = tube_along(pts_all + fork_pts, r_all + fork_r, "Haft", wood)

# ---------------------------------------------------------------- copper blade
def copper_material():
    m = bpy.data.materials.new("Copper"); nt, Nn, L = nodes_of(m); Nn.clear()
    out = Nn.new("ShaderNodeOutputMaterial"); tc = Nn.new("ShaderNodeTexCoord")
    n1 = Nn.new("ShaderNodeTexNoise"); n1.inputs['Scale'].default_value = 120; n1.inputs['Detail'].default_value = 10
    L.new(tc.outputs['Object'], n1.inputs['Vector'])
    n2 = Nn.new("ShaderNodeTexNoise"); n2.inputs['Scale'].default_value = 90; n2.inputs['Detail'].default_value = 8
    L.new(tc.outputs['Object'], n2.inputs['Vector'])
    pat = Nn.new("ShaderNodeMapRange"); pat.inputs['From Min'].default_value = 0.35; pat.inputs['From Max'].default_value = 0.75; pat.inputs['To Max'].default_value = 0.85
    L.new(n2.outputs['Fac'], pat.inputs['Value'])
    cu = Nn.new("ShaderNodeBsdfPrincipled"); cu.inputs['Metallic'].default_value = 1.0
    cu.inputs['Base Color'].default_value = (0.50, 0.19, 0.085, 1)
    rr = Nn.new("ShaderNodeMapRange"); rr.inputs['To Min'].default_value = 0.35; rr.inputs['To Max'].default_value = 0.7
    L.new(n1.outputs['Fac'], rr.inputs['Value']); L.new(rr.outputs[0], cu.inputs['Roughness'])
    patina = Nn.new("ShaderNodeBsdfPrincipled")
    patina.inputs['Base Color'].default_value = (0.09, 0.06, 0.035, 1); patina.inputs['Roughness'].default_value = 0.75
    bump = Nn.new("ShaderNodeBump"); bump.inputs['Strength'].default_value = 0.4; bump.inputs['Distance'].default_value = 0.0006
    L.new(n1.outputs['Fac'], bump.inputs['Height'])
    L.new(bump.outputs['Normal'], cu.inputs['Normal']); L.new(bump.outputs['Normal'], patina.inputs['Normal'])
    mix = Nn.new("ShaderNodeMixShader")
    L.new(pat.outputs[0], mix.inputs['Fac']); L.new(cu.outputs[0], mix.inputs[1]); L.new(patina.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs['Surface'])
    return m

# blade: tapered slab, narrow butt inside the fork, flaring to a curved cutting edge
bm = bmesh.new()
L_bl = 0.095; segs = 24
end = Vector(fork_pts[-1]); prev = Vector(fork_pts[-4])
dirv = (end - prev).normalized(); dirv.z = 0; dirv.normalize()
side = Vector((-dirv.y, dirv.x, 0))
top = []; bot = []
for i in range(segs + 1):
    t = i / segs
    width = 0.011 + 0.021 * t ** 1.6 + (0.003 * math.sin(math.pi * t))
    thick = 0.0055 * (1 - 0.85 * t ** 2) + 0.0006
    c = end - dirv * 0.03 + dirv * (L_bl * t)
    row_t = []; row_b = []
    for j in range(9):
        sgn = (j / 8) * 2 - 1
        edge_curve = 0.016 * (sgn ** 2) * t ** 3  # convex curved edge
        pt = c + side * (sgn * width) - dirv * edge_curve
        th = thick * (1 - 0.6 * sgn ** 2)
        row_t.append(bm.verts.new(pt + Vector((0, 0, th / 2 + HAFT_R * 0.65))))
        row_b.append(bm.verts.new(pt + Vector((0, 0, -th / 2 + HAFT_R * 0.65))))
    top.append(row_t); bot.append(row_b)
for i in range(segs):
    for j in range(8):
        bm.faces.new((top[i][j], top[i][j + 1], top[i + 1][j + 1], top[i + 1][j]))
        bm.faces.new((bot[i][j], bot[i + 1][j], bot[i + 1][j + 1], bot[i][j + 1]))
    bm.faces.new((top[i][0], top[i + 1][0], bot[i + 1][0], bot[i][0]))
    bm.faces.new((top[i][8], bot[i][8], bot[i + 1][8], top[i + 1][8]))
for j in range(8):
    bm.faces.new((top[-1][j], top[-1][j + 1], bot[-1][j + 1], bot[-1][j]))
    bm.faces.new((top[0][j], bot[0][j], bot[0][j + 1], top[0][j + 1]))
me = bpy.data.meshes.new("Blade"); bm.to_mesh(me); bm.free()
blade = bpy.data.objects.new("Blade", me); bpy.context.collection.objects.link(blade)
blade.data.materials.append(copper_material())
sub = blade.modifiers.new("sub", 'SUBSURF'); sub.levels = 2; sub.render_levels = 2
for f in me.polygons: f.use_smooth = True

# ---------------------------------------------------------------- leather binding
def leather_material():
    m = bpy.data.materials.new("Leather"); nt, Nn, L = nodes_of(m); Nn.clear()
    out = Nn.new("ShaderNodeOutputMaterial"); tc = Nn.new("ShaderNodeTexCoord")
    n = Nn.new("ShaderNodeTexNoise"); n.inputs['Scale'].default_value = 400; n.inputs['Detail'].default_value = 8
    L.new(tc.outputs['Object'], n.inputs['Vector'])
    p = Nn.new("ShaderNodeBsdfPrincipled"); p.inputs['Base Color'].default_value = (0.16, 0.085, 0.045, 1)
    p.inputs['Roughness'].default_value = 0.7; p.inputs['Sheen Weight'].default_value = 0.3
    b = Nn.new("ShaderNodeBump"); b.inputs['Strength'].default_value = 0.6; b.inputs['Distance'].default_value = 0.0005
    L.new(n.outputs['Fac'], b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    L.new(p.outputs[0], out.inputs['Surface'])
    return m
leather = leather_material()
c = Vector(fork_pts[-1]); dv = dirv
u = dv.cross(Vector((0, 0, 1))).normalized(); v = Vector((0, 0, 1))
def strap_helix(name, turns, phase, hand, rad_mul, length, offset):
    pts = []; n_pts = 240
    for k in range(n_pts):
        t = k / (n_pts - 1)
        a = hand * t * turns * 2 * math.pi + phase + 0.3 * math.sin(t * 17)
        base = c - dv * (offset - length * t)
        rad = fork_r[-1] * rad_mul + 0.0012 * math.sin(a * 2.3 + phase)
        pts.append(base + (u * math.cos(a) * 1.1 + v * math.sin(a)) * rad)
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    spl = cu.splines.new('POLY'); spl.points.add(len(pts) - 1)
    for p_, q in zip(spl.points, pts): p_.co = (q.x, q.y, q.z, 1)
    cu.bevel_depth = 0.0016; cu.bevel_resolution = 2
    o = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(o)
    o.data.materials.append(leather)
    o.scale = (1, 1, 1)
    return o
strap_helix("WrapA", 4.5, 0.0, 1, 1.12, 0.05, 0.048)
strap_helix("WrapB", 3.5, 1.7, -1, 1.16, 0.044, 0.044)
# birch tar: glossy black resin smeared at the joint
tar_m = bpy.data.materials.new("Tar"); nt, Nn, Lk = nodes_of(tar_m)
pb = Nn["Principled BSDF"]; pb.inputs['Base Color'].default_value = (0.008, 0.006, 0.005, 1); pb.inputs['Roughness'].default_value = 0.25
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=48, ring_count=24, location=tuple(c - dv * 0.022))
tar = bpy.context.active_object; tar.name = "Tar"
tar.scale = (0.034, fork_r[-1] * 1.12, fork_r[-1] * 1.08)
tar.rotation_euler = (0, 0, math.atan2(dv.y, dv.x))
tex = bpy.data.textures.new("tarN", 'CLOUDS'); tex.noise_scale = 0.4
dm = tar.modifiers.new("d", 'DISPLACE'); dm.texture = tex; dm.strength = 0.08; dm.mid_level = 0.6
tar.data.materials.append(tar_m)
for f in tar.data.polygons: f.use_smooth = True
s_ = tar.modifiers.new("s", 'SMOOTH'); s_.iterations = 4
# a loose strap trailing onto the snow
cu2 = bpy.data.curves.new("Strap", 'CURVE'); cu2.dimensions = '3D'
sp2 = cu2.splines.new('BEZIER'); sp2.bezier_points.add(3)
ctrl = [c + u * 0.02, c + u * 0.05 + dv * 0.01 + Vector((0, 0, -0.012)), c + u * 0.09 - dv * 0.03 + Vector((0, 0, -0.02)),
        c + u * 0.13 - dv * 0.02 + Vector((0, 0, -0.022))]
for bp, q in zip(sp2.bezier_points, ctrl):
    bp.co = q; bp.handle_left_type = bp.handle_right_type = 'AUTO'
cu2.bevel_depth = 0.0014; cu2.bevel_resolution = 2
strap = bpy.data.objects.new("Strap", cu2); bpy.context.collection.objects.link(strap)
strap.data.materials.append(leather)

# ---------------------------------------------------------------- lighting
world_flat((0.012, 0.022, 0.05), 1.0)
# low raking moonlight/blue-hour key to reveal snow texture
key = area_light((-0.9, 0.9, 0.38), (0, 0, 0), 0.5, 9, (0.55, 0.72, 1.0)); point_at(key, (0.1, 0.0, 0.0))
fill = area_light((0.8, -1.0, 0.9), (0, 0, 0), 1.2, 1.2, (0.35, 0.5, 0.9)); point_at(fill, (0.1, 0.0, 0.0))
fire_d = bpy.data.lights.new("Fire", 'POINT'); fire_d.energy = 5; fire_d.color = (1.0, 0.40, 0.10); fire_d.shadow_soft_size = 0.12
fire = bpy.data.objects.new("Fire", fire_d); bpy.context.collection.objects.link(fire)
fire.location = (-0.9, -0.6, 0.15)

cam = camera((0, 0, 0), (0, 0, 0), lens=55, dof_dist=0.4, fstop=2.4)

def frame(i, t):
    e = ease(t)
    cam.location = lerp((0.52, -0.26, 0.30), (0.46, -0.10, 0.24), e)
    look = lerp((0.16, 0.05, 0.0), (0.18, 0.06, 0.008), e)
    point_at(cam, look)
    cam.data.dof.focus_distance = (Vector(cam.location) - Vector((0.24, 0.10, 0.012))).length
    fl = 1 + 0.18 * math.sin(i * 1.7) + 0.12 * math.sin(i * 4.3 + 1) + 0.08 * math.sin(i * 9.1)
    fire_d.energy = 5 * fl

render_frames(OUT, frame, FRAMES, STEP)
