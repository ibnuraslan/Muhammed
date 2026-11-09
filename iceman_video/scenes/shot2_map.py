"""Shot 2 - Tilted relief map: route from the valley up to the place of discovery draws itself."""
import sys, os, math, json, heapq
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from common import *
from terrain import eroded_alpine

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
OUT = arg('--out', '/tmp/shot2'); FRAMES = arg('--frames', 1); STEP = arg('--step', 1)
s = reset(samples=arg('--samples', 16), exposure=0.3)
s.view_settings.look = 'AgX - Base Contrast'

SIZE = 16000.0; ZS = 3000.0; NN = 1024
h = eroded_alpine(NN, seed=21, peak_bias=[(0.56, 0.50, 0.10, 0.9), (0.62, 0.38, 0.07, 0.5)])
terr = grid_mesh("Terrain", h, SIZE, SIZE, ZS)

def to_world(r, c):
    x = (c / (NN - 1) - 0.5) * SIZE; y = (r / (NN - 1) - 0.5) * SIZE
    return Vector((x, y, float(h[int(r), int(c)]) * ZS))

# --- route: least-cost path (penalise climbing & steepness) on a downsampled grid
D = 4; hs = h[::D, ::D]; n = hs.shape[0]
gy, gx = np.gradient(hs * ZS / (SIZE / n))
slope = np.hypot(gx, gy)
cost = 1 + 25 * slope ** 2
def low_point(r0, c0, rad):
    sub = hs[max(r0 - rad, 0):r0 + rad, max(c0 - rad, 0):c0 + rad]
    rr, cc = np.unravel_index(np.argmin(sub), sub.shape)
    return rr + max(r0 - rad, 0), cc + max(c0 - rad, 0)
# discovery point: the saddle between the twin peaks (min along the ridge segment)
pa = np.array([0.56, 0.50]) * n; pb = np.array([0.62, 0.38]) * n
best = None
for t in np.linspace(0.2, 0.8, 40):
    r, c = (pa * (1 - t) + pb * t).astype(int)
    if best is None or hs[r, c] < hs[best]:
        best = (r, c)
goal = best
start = low_point(int(0.22 * n), int(0.30 * n), 25)
dist = np.full(hs.shape, np.inf); prev = {}
dist[start] = 0; pq = [(0, start)]
while pq:
    d0, (r, c) = heapq.heappop(pq)
    if (r, c) == goal: break
    if d0 > dist[r, c]: continue
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == dc == 0: continue
            r2, c2 = r + dr, c + dc
            if 0 <= r2 < n and 0 <= c2 < n:
                climb = max(hs[r2, c2] - hs[r, c], 0) * ZS
                nd = d0 + math.hypot(dr, dc) * (cost[r2, c2]) + climb * 0.02
                if nd < dist[r2, c2]:
                    dist[r2, c2] = nd; prev[(r2, c2)] = (r, c); heapq.heappush(pq, (nd, (r2, c2)))
path = [goal]
while path[-1] != start: path.append(prev[path[-1]])
path = path[::-1]
pts = [to_world(r * D, c * D) for r, c in path]
# smooth
P = np.array([tuple(p) for p in pts])
for _ in range(6):
    P[1:-1] = (P[:-2] + P[1:-1] * 2 + P[2:]) / 4
P[:, 2] = [float(h[min(int((y / SIZE + 0.5) * (NN - 1)), NN - 1), min(int((x / SIZE + 0.5) * (NN - 1)), NN - 1)]) * ZS + 25
           for x, y, _ in P]

def curve_obj(name, P, bevel, color, emit=0.0, dashed=False):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    spl = cu.splines.new('POLY'); spl.points.add(len(P) - 1)
    for p_, q in zip(spl.points, P): p_.co = (*q, 1)
    cu.bevel_depth = bevel; cu.bevel_resolution = 2
    o = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(o)
    m = bpy.data.materials.new(name + "M"); nt, N, L = nodes_of(m)
    pbsdf = N["Principled BSDF"]; pbsdf.inputs['Base Color'].default_value = (*color, 1)
    pbsdf.inputs['Emission Color'].default_value = (*color, 1); pbsdf.inputs['Emission Strength'].default_value = emit
    o.data.materials.append(m)
    return o, cu
route, route_cu = curve_obj("Route", P, 26, (0.75, 0.02, 0.015), emit=0.6)

# border: follow the main ridge crest (max height across rows near the peaks), drawn dark
br = []
for r in range(int(0.30 * NN), int(0.92 * NN), 8):
    c0, c1 = int(0.30 * NN), int(0.62 * NN)
    seg = h[r, c0:c1]
    br.append((r, c0 + int(np.argmax(seg))))
cols = np.array([c for _, c in br], float)
k = 9; cols = np.convolve(np.pad(cols, k, mode='edge'), np.ones(2 * k + 1) / (2 * k + 1), mode='same')[k:-k]
B = np.array([tuple(to_world(r, int(c))) for (r, _), c in zip(br, cols)])
for _ in range(8):
    B[1:-1] = (B[:-2] + B[1:-1] * 2 + B[2:]) / 4
B[:, 2] = [float(h[min(int((y / SIZE + 0.5) * (NN - 1)), NN - 1), min(int((x / SIZE + 0.5) * (NN - 1)), NN - 1)]) * ZS + 30 for x, y, _ in B]
border, border_cu = curve_obj("Border", B, 14, (0.02, 0.02, 0.025))

# --- map material: paper white relief + contour lines from world Z
m = bpy.data.materials.new("Map"); nt, N, L = nodes_of(m); N.clear()
out = N.new("ShaderNodeOutputMaterial"); geo = N.new("ShaderNodeNewGeometry")
sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Position'], sep.inputs[0])
def contour(step, width, strength):
    dv = N.new("ShaderNodeMath"); dv.operation = 'DIVIDE'; dv.inputs[1].default_value = step
    L.new(sep.outputs['Z'], dv.inputs[0])
    fr = N.new("ShaderNodeMath"); fr.operation = 'PINGPONG'; fr.inputs[1].default_value = 0.5
    L.new(dv.outputs[0], fr.inputs[0])
    sm = N.new("ShaderNodeMapRange"); sm.inputs['From Min'].default_value = 0; sm.inputs['From Max'].default_value = width
    sm.inputs['To Min'].default_value = strength; sm.inputs['To Max'].default_value = 0
    L.new(fr.outputs[0], sm.inputs['Value'])
    return sm
c1 = contour(100, 0.07, 0.45); c2 = contour(500, 0.05, 0.75)
add = N.new("ShaderNodeMath"); add.operation = 'ADD'; add.use_clamp = True
L.new(c1.outputs[0], add.inputs[0]); L.new(c2.outputs[0], add.inputs[1])
# elevation tint: valleys slightly blue-grey, peaks white
el = N.new("ShaderNodeMapRange"); el.inputs['From Min'].default_value = 300; el.inputs['From Max'].default_value = 2600
L.new(sep.outputs['Z'], el.inputs['Value'])
ramp = N.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (0.66, 0.70, 0.76, 1); ramp.color_ramp.elements[1].color = (0.92, 0.93, 0.95, 1)
L.new(el.outputs[0], ramp.inputs['Fac'])
mix = N.new("ShaderNodeMix"); mix.data_type = 'RGBA'
L.new(add.outputs[0], mix.inputs['Factor']); L.new(ramp.outputs['Color'], mix.inputs[6])
mix.inputs[7].default_value = (0.12, 0.14, 0.18, 1)
pb = N.new("ShaderNodeBsdfPrincipled"); pb.inputs['Roughness'].default_value = 0.9
L.new(mix.outputs[2], pb.inputs['Base Color'])
L.new(pb.outputs[0], out.inputs['Surface'])
terr.data.materials.append(m)

world_flat((0.6, 0.65, 0.75), 0.35)
sun(28, 135, energy=3.2, color=(1.0, 0.98, 0.95), angle_deg=3)

goal_w = to_world(goal[0] * D, goal[1] * D); start_w = to_world(start[0] * D, start[1] * D)
cam = camera((0, 0, 0), (0, 0, 0), lens=50)
cam.data.clip_end = 200000
labels = {"discovery": tuple(goal_w), "start": tuple(start_w),
          "peak": tuple(to_world(int(0.56 * NN), int(0.50 * NN))),
          "austria": tuple(to_world(int(0.62 * NN), int(0.22 * NN))),
          "italy": tuple(to_world(int(0.50 * NN), int(0.74 * NN)))}
proj = {}

def frame(i, t):
    e = ease(t)
    target = Vector(lerp(tuple(start_w * 0.42 + goal_w * 0.58), tuple(goal_w), e))
    ang = math.radians(-102 + 12 * e)
    distc = 15000 - 6000 * e
    cam.location = target + Vector((math.cos(ang) * distc * 0.65, math.sin(ang) * distc * 0.65, distc * 0.85))
    point_at(cam, target)
    route_cu.bevel_factor_end = ease(min(max((t - 0.08) / 0.72, 0), 1))
    bpy.context.view_layer.update()
    pr = {}
    for k, p in labels.items():
        v = world_to_camera_view(s, cam, Vector(p))
        pr[k] = (v.x, 1 - v.y)
    proj[i] = pr
    with open(os.path.join(OUT, "labels.json"), "w") as f:
        json.dump(proj, f)

os.makedirs(OUT, exist_ok=True)
render_frames(OUT, frame, FRAMES, STEP)
