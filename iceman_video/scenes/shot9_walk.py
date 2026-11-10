"""Shot 9 - Ötzi walks away from us into the storm, bow staff in hand, head down against the wind."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from mathutils import Vector
from common import *
from terrain import fbm, eroded_alpine
from human import pose_walk, reset_pose, fingers_curl, _world_verts
from otzi import build_otzi
from env import add_fog, rock_material, make_rock

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
OUT = arg('--out', '/tmp/shot9'); FRAMES = arg('--frames', 1); STEP = arg('--step', 1)
s = reset(samples=arg('--samples', 28), exposure=-0.2)
FOG = (0.30, 0.36, 0.47)
rng = np.random.default_rng(9)
FPS_RENDER = 12.0
SPEED = 0.85                                   # m/s, a tired walk through fresh snow
DIR = Vector((-0.5, 0.866, 0)).normalized()    # away from camera, up the slope
START = Vector((0.6, -1.2, 0))
STRIDE = 1.25                                  # metres per full gait cycle

# ---------------------------------------------------------------- ground
SZ = 80.0; NG = 900
yy, xx = np.mgrid[0:NG, 0:NG].astype(np.float64)
X = (xx / (NG - 1) - 0.5) * SZ; Y = (yy / (NG - 1) - 0.5) * SZ
G = fbm((NG, NG), 3, 6, 1.0) * 2.0 + fbm((NG, NG), 4, 5, 8) * 0.25 + np.maximum(Y, 0) * 0.07
G += np.maximum(fbm((NG, NG), 6, 4, 30), 0) * 0.07
G -= G[NG // 2, NG // 2]
# footprints already left behind him (behind the start point)
for k in range(-14, 0):
    side = 1 if k % 2 else -1
    c = START + DIR * (k * STRIDE / 2) + Vector((DIR.y, -DIR.x, 0)) * (0.11 * side)
    dx = X - c.x; dy = Y - c.y
    u = dx * DIR.y - dy * DIR.x; v = dx * DIR.x + dy * DIR.y
    rr = (u / 0.09) ** 2 + (v / 0.17) ** 2
    G += -np.exp(-rr ** 2.5) * 0.12 + np.exp(-((np.sqrt(rr) - 1.3) / 0.35) ** 2) * 0.03
ground = grid_mesh("Ground", G.astype(np.float32), SZ, SZ, 1.0)
snow = snow_material(scale=5.0, glint=0.993)
pn = snow.node_tree.nodes['Principled BSDF']; pn.inputs['Subsurface Scale'].default_value = 0.015
add_fog(snow, FOG, density=0.055, fog_max=0.98)
ground.data.materials.append(snow)

def gh(x, y):
    c = (x / SZ + 0.5) * (NG - 1); r = (y / SZ + 0.5) * (NG - 1)
    c0, r0 = int(c), int(r); fc, fr = c - c0, r - r0
    g = G[r0:r0 + 2, c0:c0 + 2]
    return float(g[0, 0] * (1 - fc) * (1 - fr) + g[0, 1] * fc * (1 - fr) + g[1, 0] * (1 - fc) * fr + g[1, 1] * fc * fr)

rmat = rock_material("Rock"); add_fog(rmat, FOG, density=0.055, fog_max=0.98)
meshes = [make_rock(700 + k, rmat) for k in range(6)]
for k in range(55):
    x = rng.uniform(-25, 25); y = rng.uniform(-4, 35)
    p = Vector((x, y, 0)); rel = p - START
    if abs(rel.dot(Vector((DIR.y, -DIR.x, 0)))) < 1.5 and rel.dot(DIR) > -3:
        continue
    sc = rng.uniform(0.3, 1.3) * (1.8 if rng.random() < 0.15 else 1)
    o = bpy.data.objects.new("Rock", meshes[k % 6]); bpy.context.collection.objects.link(o)
    o.location = (x, y, gh(x, y) + sc * 0.05); o.rotation_euler = (0, 0, rng.uniform(0, 6.3))
    o.scale = (sc, sc, sc * rng.uniform(0.6, 1))
hb = eroded_alpine(512, seed=37)
far = grid_mesh("Ridge", hb, 9000, 3000, 1200.0, origin=(0, 2600, -150))
fm = snow_rock_material("FarMat", snow_thresh=0.5, fog_color=FOG, fog_density=0.0012, fog_max=0.985, bump_scale=30)
far.data.materials.append(fm)

# ---------------------------------------------------------------- Ötzi
h = build_otzi(hair_density=0.55)
yew = bpy.data.materials.new("Yew"); yew.use_nodes = True
yp = yew.node_tree.nodes["Principled BSDF"]; yp.inputs['Base Color'].default_value = (0.10, 0.05, 0.022, 1); yp.inputs['Roughness'].default_value = 0.6
bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.014, depth=1.82, location=(0, 0, 0))
staff = bpy.context.active_object; staff.data.materials.append(yew)
heading = math.atan2(-DIR.x, -DIR.y)          # rest pose faces -Y; rotate so he faces DIR
h.arm.rotation_euler = (0, 0, heading)

def place(t):
    """Pose + position at time t (seconds)."""
    dist = SPEED * t
    phase = (dist / STRIDE) % 1.0
    # pose in the rig's own frame (world-axis posing helpers assume an unrotated rig), then turn it
    h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0)
    reset_pose(h)
    pose_walk(h, phase, stride=24, arm_swing=12)
    # lean into the wind, head down
    h.rot("spine05", (1, 0, 0), 6); h.rot("spine03", (1, 0, 0), 5); h.rot("neck01", (1, 0, 0), 10); h.rot("head", (1, 0, 0), 8)
    # right hand grips the staff: forearm forward, staff planted ahead-ish
    h.rot("upperarm01.R", (1, 0, 0), 18); h.rot("lowerarm01.R", (1, 0, 0), 40)
    fingers_curl(h, 70, side=("R",), thumb=40)
    p = START + DIR * dist
    h.arm.rotation_euler = (0, 0, heading)
    h.arm.location = (p.x, p.y, 0)
    bpy.context.view_layer.update()
    w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH' and "shoes" in o.name])
    h.arm.location.z = gh(p.x, p.y) - w[:, 2].min() - 0.03     # boots sink a little into the snow
    bpy.context.view_layer.update()
    hand = h.bone_tail("wrist.R")
    staff.location = hand + Vector((0, 0, -0.02)) + DIR * 0.03
    staff.rotation_euler = (DIR.y * 0.25, -DIR.x * 0.25, 0)
    return p

world_flat(FOG, 0.95)
sun(14, 60, energy=1.4, color=(0.8, 0.87, 1.0), angle_deg=6)
cam = camera((0, 0, 0), (0, 0, 0), lens=45, dof_dist=5, fstop=4.0)
CAM0 = START + Vector((2.2, -4.6, 0)); CAM0.z = gh(CAM0.x, CAM0.y) + 1.45

def frame(i, t):
    tt = i / FPS_RENDER
    p = place(tt)
    cam.location = CAM0 + DIR * (0.25 * tt)               # slow drift after him
    chest = h.bone_head("spine02")
    point_at(cam, tuple(chest + Vector((0, 0, 0.15))))
    cam.data.dof.focus_distance = (cam.location - chest).length

render_frames(OUT, frame, FRAMES, STEP)
