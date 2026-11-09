"""Shot 3 - Storm light on the glacier col: footprints lead up between boulders toward the ridge."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy, bmesh
from mathutils import Vector
from common import *
from terrain import fbm, eroded_alpine, perlin

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
OUT = arg('--out', '/tmp/shot3'); FRAMES = arg('--frames', 1); STEP = arg('--step', 1)
s = reset(samples=arg('--samples', 32), exposure=-0.2)
FOG = (0.34, 0.40, 0.51)
rng = np.random.default_rng(5)

def add_fog(mat, color=FOG, density=0.012, fog_max=1.0):
    """Wrap a material's surface output with camera-distance haze (cheap aerial perspective)."""
    nt = mat.node_tree; N = nt.nodes; L = nt.links
    out = [n for n in N if n.type == 'OUTPUT_MATERIAL'][0]
    src = out.inputs['Surface'].links[0].from_socket
    cam = N.new("ShaderNodeCameraData")
    k = N.new("ShaderNodeMath"); k.operation = 'MULTIPLY'; k.inputs[1].default_value = -density
    L.new(cam.outputs['View Distance'], k.inputs[0])
    ex = N.new("ShaderNodeMath"); ex.operation = 'EXPONENT'; L.new(k.outputs[0], ex.inputs[0])
    inv = N.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = fog_max; L.new(ex.outputs[0], inv.inputs[1])
    inv.use_clamp = True
    lp = N.new("ShaderNodeLightPath")
    g = N.new("ShaderNodeMath"); g.operation = 'MULTIPLY'; L.new(inv.outputs[0], g.inputs[0]); L.new(lp.outputs['Is Camera Ray'], g.inputs[1])
    em = N.new("ShaderNodeEmission"); em.inputs['Color'].default_value = (*color, 1)
    mx = N.new("ShaderNodeMixShader"); L.new(g.outputs[0], mx.inputs['Fac']); L.new(src, mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs['Surface'])

# ---------------------------------------------------------------- near ground with footprints
SZ = 70.0; NG = 1400
yy, xx = np.mgrid[0:NG, 0:NG].astype(np.float64)
X = (xx / (NG - 1) - 0.5) * SZ; Y = (yy / (NG - 1) - 0.5) * SZ
Hg = fbm((NG, NG), 3, 6, 1.0) * 1.6 + fbm((NG, NG), 4, 5, 8) * 0.25 + Y * 0.05 + np.maximum(Y, 0) ** 2 * 0.004  # gentle rise toward ridge
Hg += fbm((NG, NG), 5, 4, 60) * 0.035 + np.maximum(fbm((NG, NG), 6, 4, 25), 0) * 0.06
# trail path: wanders away from camera along +y
def trail_x(y):
    return 0.8 * np.sin(y * 0.09) + 0.4 * np.sin(y * 0.23 + 1)
steps = np.arange(-30, 33, 0.72)
for k, yc in enumerate(steps):
    side = 1 if k % 2 else -1
    xc = trail_x(yc) + side * 0.14 + rng.normal(0, 0.03)
    ang = math.atan(0.09 * 0.8 * math.cos(yc * 0.09)) + rng.normal(0, 0.08)
    dx = X - xc; dy = Y - yc
    u = dx * math.cos(ang) - dy * math.sin(ang); v = dx * math.sin(ang) + dy * math.cos(ang)
    r = (u / 0.085) ** 2 + (v / 0.16) ** 2
    depth = 0.15 * (1 - 0.3 * min(abs(yc - 0) / 40, 1))
    print_ = np.exp(-r ** 2.5) * depth
    rim = np.exp(-((np.sqrt(r) - 1.3) / 0.35) ** 2) * 0.035
    Hg += -print_ + rim
edge_z = float(np.median(Hg[int((26 / SZ + 0.5) * (NG - 1))]))
Hg -= np.maximum(Y - 27, 0) ** 2 * 0.12
ground = grid_mesh("Ground", Hg.astype(np.float32), SZ, SZ, 1.0)
snow = snow_material(scale=6.0, glint=0.992)
pn = snow.node_tree.nodes['Principled BSDF']; pn.inputs['Base Color'].default_value = (0.80, 0.85, 0.93, 1)
pn.inputs['Subsurface Scale'].default_value = 0.015
add_fog(snow, density=0.013)
ground.data.materials.append(snow)

def ground_h(x, y):
    c = int((x / SZ + 0.5) * (NG - 1)); r = int((y / SZ + 0.5) * (NG - 1))
    return float(Hg[min(max(r, 0), NG - 1), min(max(c, 0), NG - 1)])

# ---------------------------------------------------------------- distant ridge
hb = eroded_alpine(512, seed=33)
far = grid_mesh("Ridge", hb, 7000, 3000, 1100.0, origin=(0, 2700, -150))
# mid-ground snowfield that continues the near ground up to the ridge foot
hm = fbm((500, 500), 61, 6, 2.0) * 0.5 + 0.5
ramp_ = np.linspace(0, 1, 500)[:, None]
mid = grid_mesh("Mid", (hm * 8 * ramp_ + ramp_ ** 1.6 * 330).astype(np.float32), 4000, 2600, 1.0,
                origin=(0, 1325, edge_z - 0.25))
fm = snow_rock_material("FarMat", snow_thresh=0.48, fog_color=FOG, fog_density=0.0005, fog_max=0.95, bump_scale=30,
                        rock_col=(0.02, 0.02, 0.022))
far.data.materials.append(fm)
mm = snow_material(scale=20.0, glint=0.999); add_fog(mm, density=0.0006, fog_max=0.95); mid.data.materials.append(mm)

# ---------------------------------------------------------------- boulders (fractured spheres)
def rock_material():
    m = bpy.data.materials.new("Rock"); nt, N, L = nodes_of(m); N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord"); geo = N.new("ShaderNodeNewGeometry")
    n1 = N.new("ShaderNodeTexNoise"); n1.inputs['Scale'].default_value = 9; n1.inputs['Detail'].default_value = 14
    L.new(tc.outputs['Object'], n1.inputs['Vector'])
    vor = N.new("ShaderNodeTexVoronoi"); vor.inputs['Scale'].default_value = 4; vor.feature = 'DISTANCE_TO_EDGE'
    L.new(tc.outputs['Object'], vor.inputs['Vector'])
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.018, 0.018, 0.02, 1)
    cr.color_ramp.elements[1].color = (0.11, 0.105, 0.10, 1)
    L.new(n1.outputs['Fac'], cr.inputs['Fac'])
    rock = N.new("ShaderNodeBsdfPrincipled"); L.new(cr.outputs['Color'], rock.inputs['Base Color'])
    rock.inputs['Roughness'].default_value = 0.8
    hb_ = N.new("ShaderNodeMath"); hb_.operation = 'MULTIPLY_ADD'; hb_.inputs[1].default_value = 0.6
    L.new(n1.outputs['Fac'], hb_.inputs[0]); L.new(vor.outputs['Distance'], hb_.inputs[2])
    bump = N.new("ShaderNodeBump"); bump.inputs['Strength'].default_value = 1.0; bump.inputs['Distance'].default_value = 0.05
    L.new(hb_.outputs[0], bump.inputs['Height']); L.new(bump.outputs['Normal'], rock.inputs['Normal'])
    sn = N.new("ShaderNodeBsdfPrincipled"); sn.inputs['Base Color'].default_value = (0.82, 0.86, 0.93, 1)
    sn.inputs['Roughness'].default_value = 0.6; sn.inputs['Subsurface Weight'].default_value = 0.5
    sn.inputs['Subsurface Radius'].default_value = (0.5, 0.8, 1.0); sn.inputs['Subsurface Scale'].default_value = 0.02
    L.new(bump.outputs['Normal'], sn.inputs['Normal'])
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Normal'], sep.inputs[0])
    n2 = N.new("ShaderNodeTexNoise"); n2.inputs['Scale'].default_value = 3; n2.inputs['Detail'].default_value = 8
    L.new(tc.outputs['Object'], n2.inputs['Vector'])
    ad = N.new("ShaderNodeMath"); ad.operation = 'MULTIPLY_ADD'; ad.inputs[1].default_value = 0.5
    L.new(n2.outputs['Fac'], ad.inputs[0]); L.new(sep.outputs['Z'], ad.inputs[2])
    rp = N.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].position = 0.95; rp.color_ramp.elements[1].position = 1.02
    L.new(ad.outputs[0], rp.inputs['Fac'])
    mx = N.new("ShaderNodeMixShader"); L.new(rp.outputs['Color'], mx.inputs['Fac']); L.new(rock.outputs[0], mx.inputs[1]); L.new(sn.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs['Surface'])
    return m
rmat = rock_material(); add_fog(rmat, density=0.013)

def make_rock(seed):
    r = np.random.default_rng(seed)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0)
    V = np.array([v.co[:] for v in bm.verts])
    # broad lumpy deformation
    n = (perlin(V[:, 0] * 1.3 + seed, V[:, 1] * 1.3, seed) + perlin(V[:, 1] * 1.3, V[:, 2] * 1.3 + seed, seed + 1)) * 0.18
    V *= (1 + n)[:, None]
    # fracture planes: clamp to random half-spaces -> angular facets
    for _ in range(r.integers(6, 11)):
        nrm = r.normal(size=3); nrm /= np.linalg.norm(nrm)
        dist = r.uniform(0.55, 0.85)
        dd = V @ nrm - dist
        V -= np.maximum(dd, 0)[:, None] * nrm[None, :]
    V *= r.uniform(0.6, 1.4, 3)
    V[:, 2] = np.maximum(V[:, 2], -0.3)  # flat base sunk into snow
    fine = perlin(V[:, 0] * 7, V[:, 1] * 7 + V[:, 2] * 3, seed + 7) * 0.03 + perlin(V[:, 0] * 23 + V[:, 2] * 5, V[:, 1] * 23, seed + 9) * 0.012
    lens = np.linalg.norm(V, axis=1, keepdims=True)
    V += V / np.maximum(lens, 1e-6) * fine[:, None]
    for v, p in zip(bm.verts, V): v.co = p
    me = bpy.data.meshes.new(f"rock{seed}"); bm.to_mesh(me); bm.free()
    for f in me.polygons: f.use_smooth = True
    me.materials.append(rmat)
    return me

rock_meshes = [make_rock(100 + k) for k in range(7)]
placed = 0
while placed < 70:
    x = rng.uniform(-26, 26); y = rng.uniform(-8, 33)
    if abs(x - trail_x(y)) < 1.6:
        continue
    sc = rng.uniform(0.25, 1.1) * (1.6 if rng.random() < 0.15 else 1.0)
    o = bpy.data.objects.new("Rock", rock_meshes[placed % len(rock_meshes)])
    bpy.context.collection.objects.link(o)
    o.location = (x, y, ground_h(x, y) + sc * 0.05)
    o.rotation_euler = (rng.normal(0, 0.15), rng.normal(0, 0.15), rng.uniform(0, 6.28))
    o.scale = (sc, sc, sc * rng.uniform(0.6, 1.0))
    placed += 1
# two hero boulders flanking the trail near camera
for (x, y, sc, k) in [(-2.4, 1.2, 1.1, 3), (3.1, 4.0, 1.4, 5), (-3.5, 9.0, 1.8, 1)]:
    o = bpy.data.objects.new("Hero", rock_meshes[k]); bpy.context.collection.objects.link(o)
    o.location = (x, y, ground_h(x, y)); o.scale = (sc, sc * 0.9, sc * 0.75); o.rotation_euler = (0, 0, k)

# ---------------------------------------------------------------- light: overcast storm
world_flat(FOG, 0.75)
sun(12, -150, energy=2.4, color=(0.80, 0.87, 1.0), angle_deg=3)

cam = camera((0, 0, 0), (0, 0, 0), lens=28)

def frame(i, t):
    e = t
    y0 = -6.0 + 5.0 * e
    x0 = trail_x(y0) - 0.6
    cam.location = (x0, y0, ground_h(x0, y0) + 0.9 + 0.03 * math.sin(i * 0.35))
    look_y = y0 + 12
    point_at(cam, (trail_x(look_y) * 0.6, look_y, ground_h(0, look_y) + 0.6))
    cam.rotation_euler.rotate_axis('Z', 0.006 * math.sin(i * 0.21))

render_frames(OUT, frame, FRAMES, STEP)
