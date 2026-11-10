"""Shot 8 - Night. Ötzi sits by a small fire on the high pasture; firelight on his face, blue night around."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from mathutils import Vector
from common import *
from terrain import fbm, eroded_alpine
from human import pose_sit, _world_verts
from otzi import build_otzi
from env import add_fog, rock_material, make_rock

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
OUT = arg('--out', '/tmp/shot8'); FRAMES = arg('--frames', 1); STEP = arg('--step', 1)
s = reset(samples=arg('--samples', 32), exposure=0.2)
s.cycles.volume_step_rate = 2.0
NIGHT = (0.012, 0.02, 0.045)
FIRE = Vector((0.05, -0.80, 0.0))
rng = np.random.default_rng(8)

# ---------------------------------------------------------------- ground
SZ = 60.0; NG = 700
yy, xx = np.mgrid[0:NG, 0:NG].astype(np.float64)
X = (xx / (NG - 1) - 0.5) * SZ; Y = (yy / (NG - 1) - 0.5) * SZ
G = fbm((NG, NG), 3, 6, 1.5) * 1.4 + fbm((NG, NG), 4, 5, 10) * 0.12 + np.maximum(Y - 6, 0) * 0.08
G -= G[NG // 2, NG // 2]
flat = np.exp(-((X - FIRE.x) ** 2 + (Y - FIRE.y + 0.4) ** 2) / 4.0)
G *= (1 - flat)
ground = grid_mesh("Ground", G.astype(np.float32), SZ, SZ, 1.0)
snow = snow_material(scale=4.0, glint=0.99)
add_fog(snow, NIGHT, density=0.03, fog_max=0.97)
ground.data.materials.append(snow)
# trampled, bare patch around the hearth
bpy.ops.mesh.primitive_circle_add(vertices=64, radius=1.2, fill_type='NGON', location=(FIRE.x, FIRE.y, 0.004))
dirt = bpy.context.active_object
dm = bpy.data.materials.new("Dirt"); dm.use_nodes = True
N = dm.node_tree.nodes; L = dm.node_tree.links; p = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); n1 = N.new("ShaderNodeTexNoise"); n1.inputs['Scale'].default_value = 6; n1.inputs['Detail'].default_value = 10
L.new(tc.outputs['Object'], n1.inputs['Vector'])
cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.02, 0.016, 0.012, 1); cr.color_ramp.elements[1].color = (0.30, 0.32, 0.36, 1)
cr.color_ramp.elements[0].position = 0.45; cr.color_ramp.elements[1].position = 0.62
gr = N.new("ShaderNodeTexGradient"); gr.gradient_type = 'SPHERICAL'; L.new(tc.outputs['Object'], gr.inputs['Vector'])
mx_ = N.new("ShaderNodeMath"); mx_.operation = 'SUBTRACT'; L.new(n1.outputs['Fac'], mx_.inputs[0]); L.new(gr.outputs['Fac'], mx_.inputs[1])
L.new(mx_.outputs[0], cr.inputs['Fac']); L.new(cr.outputs['Color'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.9
dirt.data.materials.append(dm)

# ---------------------------------------------------------------- the hearth: stones, logs, embers
rmat = rock_material("Stone", snow=False)
stone_meshes = [make_rock(500 + k, rmat) for k in range(5)]
for k in range(11):
    a = k / 11 * 2 * math.pi + rng.normal(0, 0.1)
    o = bpy.data.objects.new("Stone", stone_meshes[k % 5]); bpy.context.collection.objects.link(o)
    o.location = (FIRE.x + math.cos(a) * 0.36, FIRE.y + math.sin(a) * 0.36, 0.02)
    sc = rng.uniform(0.07, 0.11); o.scale = (sc, sc * 0.9, sc * 0.7); o.rotation_euler = (0, 0, rng.uniform(0, 6))

bark = bpy.data.materials.new("Log"); bark.use_nodes = True
N = bark.node_tree.nodes; L = bark.node_tree.links; p = N["Principled BSDF"]
tc = N.new("ShaderNodeTexCoord"); nn = N.new("ShaderNodeTexNoise"); nn.inputs['Scale'].default_value = 25; nn.inputs['Detail'].default_value = 10
L.new(tc.outputs['Object'], nn.inputs['Vector'])
cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.006, 0.005, 0.004, 1); cr.color_ramp.elements[1].color = (0.045, 0.03, 0.02, 1)
L.new(nn.outputs['Fac'], cr.inputs['Fac']); L.new(cr.outputs['Color'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.9
# glowing cracks near the burning ends
vo = N.new("ShaderNodeTexVoronoi"); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = 55
vo.inputs['Randomness'].default_value = 1.0
L.new(tc.outputs['Object'], vo.inputs['Vector'])
gl = N.new("ShaderNodeMapRange"); gl.inputs['From Min'].default_value = 0.0; gl.inputs['From Max'].default_value = 0.035
gl.inputs['To Min'].default_value = 1.0; gl.inputs['To Max'].default_value = 0.0
L.new(vo.outputs['Distance'], gl.inputs['Value'])
gw = N.new("ShaderNodeTexGradient"); gw.gradient_type = 'SPHERICAL'
mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (5.0, 5.0, 5.0)
L.new(tc.outputs['Object'], mp.inputs['Vector']); L.new(mp.outputs[0], gw.inputs['Vector'])
heat = N.new("ShaderNodeMath"); heat.operation = 'MULTIPLY'; L.new(gl.outputs[0], heat.inputs[0]); L.new(gw.outputs['Fac'], heat.inputs[1])
bb = N.new("ShaderNodeBlackbody"); bb.inputs['Temperature'].default_value = 1500
L.new(bb.outputs[0], p.inputs['Emission Color'])
es = N.new("ShaderNodeMath"); es.operation = 'MULTIPLY'; es.inputs[1].default_value = 1.5
L.new(heat.outputs[0], es.inputs[0]); L.new(es.outputs[0], p.inputs['Emission Strength'])
for k in range(5):
    a = k / 5 * 2 * math.pi + 0.3
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=rng.uniform(0.025, 0.04), depth=0.5,
                                        location=(FIRE.x + math.cos(a) * 0.12, FIRE.y + math.sin(a) * 0.12, 0.09))
    lg = bpy.context.active_object
    lg.rotation_euler = (0, math.radians(62), a + math.pi)
    lg.data.materials.append(bark)
# ember bed


# ---------------------------------------------------------------- volumetric flame
bpy.ops.mesh.primitive_cube_add(size=1, location=(FIRE.x, FIRE.y, 0.38))
flame = bpy.context.active_object; flame.scale = (0.55, 0.55, 0.8)
fm = bpy.data.materials.new("Flame"); fm.use_nodes = True
N = fm.node_tree.nodes; L = fm.node_tree.links; N.clear()
out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord")
# generated coords: (0..1)^3 in the box; flame axis at x=y=0.5, base at z~0.1
sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Generated'], sep.inputs[0])
def m_(op, a=None, b=None, v1=None, v2=None):
    """Math node helper: a/b are sockets, v1/v2 constants for inputs 1/2."""
    n = N.new("ShaderNodeMath"); n.operation = op
    if a is not None: L.new(a, n.inputs[0])
    if b is not None: L.new(b, n.inputs[1])
    if v1 is not None: n.inputs[1].default_value = v1
    if v2 is not None: n.inputs[2].default_value = v2
    return n.outputs[0]
noise = N.new("ShaderNodeTexNoise"); noise.noise_dimensions = '4D'; noise.inputs['Scale'].default_value = 6.5
noise.inputs['Detail'].default_value = 8; noise.inputs['Roughness'].default_value = 0.62; noise.inputs['Distortion'].default_value = 1.2
# advect noise upward over time: offset z by -time
off = N.new("ShaderNodeVectorMath"); off.operation = 'ADD'; off.inputs[1].default_value = (0, 0, 0)
L.new(tc.outputs['Generated'], off.inputs[0]); L.new(off.outputs[0], noise.inputs['Vector'])
cx = m_('SUBTRACT', sep.outputs['X'], v1=0.5); cy = m_('SUBTRACT', sep.outputs['Y'], v1=0.5)
# lateral wobble from the noise so the flame licks sideways
wob = m_('SUBTRACT', noise.outputs['Fac'], v1=0.5)
z = sep.outputs['Z']
cxw = m_('ADD', cx, m_('MULTIPLY', wob, m_('MULTIPLY', z, v1=1.4)))
r = m_('SQRT', m_('ADD', m_('POWER', cxw, v1=2.0), m_('POWER', cy, v1=2.0)))
# cone radius shrinks with height
width = m_('MULTIPLY_ADD', m_('SQRT', z), v1=-0.45, v2=0.40)   # wide base, narrowing tongues
shape = m_('SUBTRACT', width, r)
shape = m_('MULTIPLY', shape, v1=9.0)
nz = m_('MULTIPLY_ADD', noise.outputs['Fac'], v1=2.4, v2=-0.50)
dens = m_('MULTIPLY', m_('MAXIMUM', shape, v1=0.0), m_('MAXIMUM', nz, v1=0.0))   # both >= 0, else (-)(-) lights the box walls
# split the flame into separate licking tongues: vertically stretched noise, thresholded
mp2 = N.new("ShaderNodeMapping"); mp2.inputs['Scale'].default_value = (3.2, 3.2, 1.0)
L.new(off.outputs[0], mp2.inputs['Vector'])
tn = N.new("ShaderNodeTexNoise"); tn.noise_dimensions = '4D'; tn.inputs['Scale'].default_value = 5.0
tn.inputs['Detail'].default_value = 3; L.new(mp2.outputs[0], tn.inputs['Vector'])
tongues = N.new("ShaderNodeMapRange"); tongues.inputs['From Min'].default_value = 0.42; tongues.inputs['From Max'].default_value = 0.6
L.new(tn.outputs['Fac'], tongues.inputs['Value'])
# tongues matter more higher up; the base stays a continuous bed of fire
tw = m_('MAXIMUM', tongues.outputs[0], m_('MULTIPLY_ADD', z, v1=-4.0, v2=1.0))
dens = m_('MULTIPLY', dens, tw)
flame_tn = tn
base = m_('MULTIPLY', m_('SUBTRACT', z, v1=0.06), v1=12.0)
dens = m_('MINIMUM', dens, base)
dens = m_('MAXIMUM', dens, v1=0.0)
dens = m_('POWER', dens, v1=1.6)
vol = N.new("ShaderNodeVolumePrincipled")
vol.inputs['Density'].default_value = 0.0
tmp = m_('MULTIPLY_ADD', z, v1=-1300.0, v2=2600.0)       # hotter at the base
temp_ = m_('ADD', tmp, m_('MULTIPLY', dens, v1=250.0))
bbf = N.new("ShaderNodeBlackbody"); L.new(temp_, bbf.inputs['Temperature'])
L.new(bbf.outputs[0], vol.inputs['Emission Color'])
emul = N.new("ShaderNodeMath"); emul.operation = 'MULTIPLY'; emul.inputs[1].default_value = 220.0
L.new(dens, emul.inputs[0]); L.new(emul.outputs[0], vol.inputs['Emission Strength'])
L.new(vol.outputs[0], out.inputs['Volume'])
flame.data.materials.append(fm)
flame.visible_shadow = False
flame_noise = noise; flame_off = off

# light from the fire (the volume emission alone is too noisy to light the scene)
fire_lights = []
for k, (dx, dy, dz, e) in enumerate([(0, 0, 0.42, 70), (0.05, 0.04, 0.62, 35), (-0.06, 0.03, 0.30, 20)]):
    d = bpy.data.lights.new(f"FireL{k}", 'POINT'); d.energy = e; d.color = (1.0, 0.45, 0.14); d.shadow_soft_size = 0.12
    o = bpy.data.objects.new(f"FireL{k}", d); bpy.context.collection.objects.link(o)
    o.location = (FIRE.x + dx, FIRE.y + dy, dz); fire_lights.append((d, e))

# ---------------------------------------------------------------- Ötzi
h = build_otzi(hair_density=0.85)
pose_sit(h, lean=14)
w = _world_verts(h.body)
seat_z = 0.40
h.arm.location = (0, 0.75, 0)
bpy.context.view_layer.update()
# put the soles on the ground (measure every visible mesh: covered skin was removed from the body)
w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
h.arm.location.z -= w[:, 2].min() - 0.0
bpy.context.view_layer.update()
# the stone he sits on
o = bpy.data.objects.new("Seat", stone_meshes[2]); bpy.context.collection.objects.link(o)
hip = h.bone_head("pelvis.L").lerp(h.bone_head("pelvis.R"), 0.5)
o.location = (hip.x, hip.y + 0.06, hip.z - 0.30); o.scale = (0.3, 0.26, 0.24)
# ---------------------------------------------------------------- night backdrop
rmat2 = rock_material("Rock"); add_fog(rmat2, NIGHT, density=0.03, fog_max=0.97)
meshes = [make_rock(600 + k, rmat2) for k in range(5)]
for k in range(30):
    x = rng.uniform(-14, 14); y = rng.uniform(4.0, 22)
    sc = rng.uniform(0.4, 1.6)
    ob = bpy.data.objects.new("Rock", meshes[k % 5]); bpy.context.collection.objects.link(ob)
    c = int((x / SZ + 0.5) * (NG - 1)); rr_ = int((y / SZ + 0.5) * (NG - 1))
    ob.location = (x, y, G[rr_, c] - 0.1); ob.scale = (sc, sc, sc * 0.7); ob.rotation_euler = (0, 0, rng.uniform(0, 6))
hb = eroded_alpine(512, seed=36)
far = grid_mesh("Ridge", hb, 9000, 3000, 1300.0, origin=(0, 2800, -200))
fmm = snow_rock_material("FarMat", snow_thresh=0.5, fog_color=(0.03, 0.05, 0.09), fog_density=0.0004, fog_max=0.9, bump_scale=30)
far.data.materials.append(fmm)

world_flat(NIGHT, 1.0)
moon = sun(28, 200, energy=0.12, color=(0.55, 0.68, 1.0), angle_deg=0.6)

cam = camera((0, 0, 0), (0, 0, 0), lens=40, dof_dist=1.6, fstop=2.8)
eye = (h.eyes[0].matrix_world.to_translation() + h.eyes[1].matrix_world.to_translation()) / 2
print("eye", eye)

def frame(i, t):
    e = ease(t)
    # crane: start low behind the flames (focus on the fire), rise and rack focus to his face
    cam.location = Vector(lerp((0.30, -2.15, 0.48), (0.20, -1.50, 0.95), e))
    fire_c = FIRE + Vector((0, 0, 0.22))
    d_eye = (eye - cam.location).normalized(); d_fire = (fire_c - cam.location).normalized()
    w_eye = 0.25 + 0.72 * e
    point_at(cam, tuple(cam.location + d_eye * w_eye + d_fire * (1 - w_eye)))
    rf = ease((t - 0.25) / 0.5)
    cam.data.dof.focus_distance = (cam.location - fire_c).length * (1 - rf) + (cam.location - eye).length * rf
    tt = i / 12.0
    flame_off.inputs[1].default_value = (0, 0, -tt * 1.6)
    flame_noise.inputs['W'].default_value = tt * 0.9
    flame_tn.inputs['W'].default_value = tt * 1.3
    for k, (d, e0) in enumerate(fire_lights):
        fl = 1 + 0.22 * math.sin(tt * 11 + k) + 0.14 * math.sin(tt * 23.7 + 2 * k) + 0.08 * math.sin(tt * 41 + k)
        d.energy = e0 * fl

if '--debugfire' in sys.argv:
    s.render.resolution_percentage = 50
    cam.location = (FIRE.x + 0.2, FIRE.y - 1.6, 0.5); point_at(cam, (FIRE.x, FIRE.y, 0.35)); cam.data.dof.use_dof = False
    print("flame", flame.location, flame.dimensions, flame.hide_render, [m.name for m in flame.data.materials])
    s.render.filepath = OUT + '_dbg.png'; bpy.ops.render.render(write_still=True)
else:
    render_frames(OUT, frame, FRAMES, STEP)
