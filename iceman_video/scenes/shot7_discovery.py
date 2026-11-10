"""Shot 7 - 19 September 1991: the body, face-down, half-frozen into glacier ice and meltwater in a rocky
gully; the two hikers who found it stand behind, looking down."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from mathutils import Vector
from common import *
from terrain import fbm, eroded_alpine
from human import Human, add_asset, lay_down, settle, bake_pose, flatten_contact, _chain, fingers_curl, SIDE, _world_verts
from mummy import build_mummy
from env import add_fog, rock_material, make_rock

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
OUT = arg('--out', '/tmp/shot7'); FRAMES = arg('--frames', 1); STEP = arg('--step', 1)
s = reset(samples=arg('--samples', 40), exposure=-0.35)
s.cycles.max_bounces = 10; s.cycles.transmission_bounces = 8
FOG = (0.62, 0.66, 0.72)
rng = np.random.default_rng(11)
ICE_Z = 0.0          # meltwater / ice surface level

# ---------------------------------------------------------------- ground: snowy rocky gully
SZ = 40.0; NG = 900
yy, xx = np.mgrid[0:NG, 0:NG].astype(np.float64)
X = (xx / (NG - 1) - 0.5) * SZ; Y = (yy / (NG - 1) - 0.5) * SZ
trough = -0.45 * np.exp(-(X / 3.2) ** 2)                     # gully runs along Y
G = 0.35 + trough + fbm((NG, NG), 3, 6, 1.4) * 1.2 + fbm((NG, NG), 4, 5, 9) * 0.12 + np.maximum(Y, 0) * 0.04
G += np.maximum(fbm((NG, NG), 6, 4, 22), 0) * 0.08
G = np.maximum(G, ICE_Z + 0.06 + np.abs(fbm((NG, NG), 8, 4, 6)) * 0.15)   # gully floor stays above the meltwater
pool = np.exp(-((X / 1.0) ** 2 + ((Y - 0.85) / 1.6) ** 2) ** 1.5)   # the melt hollow around the body
G = G * (1 - pool) + (ICE_Z - 0.12) * pool
ground = grid_mesh("Ground", G.astype(np.float32), SZ, SZ, 1.0)
snow = snow_material(scale=4.0, glint=0.99)
add_fog(snow, FOG, density=0.004, fog_max=0.9)
ground.data.materials.append(snow)

def gh(x, y):
    c = int((x / SZ + 0.5) * (NG - 1)); r = int((y / SZ + 0.5) * (NG - 1))
    return float(G[min(max(r, 0), NG - 1), min(max(c, 0), NG - 1)])

# ---------------------------------------------------------------- meltwater
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.7, ICE_Z - 0.035))
water = bpy.context.active_object; water.scale = (2.4, 3.8, 1)
wm = bpy.data.materials.new("Meltwater"); wm.use_nodes = True
N = wm.node_tree.nodes; L = wm.node_tree.links; p = N["Principled BSDF"]
p.inputs['Base Color'].default_value = (0.80, 0.90, 0.92, 1); p.inputs['Transmission Weight'].default_value = 1.0
p.inputs['Roughness'].default_value = 0.05; p.inputs['IOR'].default_value = 1.333
tc = N.new("ShaderNodeTexCoord"); rn = N.new("ShaderNodeTexNoise"); rn.inputs['Scale'].default_value = 18; rn.inputs['Detail'].default_value = 4
L.new(tc.outputs['Object'], rn.inputs['Vector'])
bmp = N.new("ShaderNodeBump"); bmp.inputs['Strength'].default_value = 0.08; L.new(rn.outputs['Fac'], bmp.inputs['Height']); L.new(bmp.outputs['Normal'], p.inputs['Normal'])
water.data.materials.append(wm)
water.visible_shadow = False   # let sunlight reach the snow under the meltwater (no refractive caustics)

# ---------------------------------------------------------------- glacier ice holding the lower body
NI = 220
iy, ix = np.mgrid[0:NI, 0:NI].astype(np.float64)
IX = (ix / (NI - 1) - 0.5) * 1.9; IY = (iy / (NI - 1) - 0.5) * 1.6
ice_top = 0.10 + fbm((NI, NI), 21, 5, 4.0) * 0.05 + 0.06 * np.clip((0.1 - IY) / 0.5, 0, 1) + np.maximum(fbm((NI, NI), 22, 4, 14.0), 0) * 0.03
warp_e = fbm((NI, NI), 23, 4, 3.0) * 0.25
edge = np.clip((0.78 + warp_e - np.hypot(IX / 0.95, IY / 0.8) ** 1.5) / 0.22, 0, 1)   # melted, irregular rim
ice_h = ice_top * edge - (1 - edge) * 0.12
ice = grid_mesh("Ice", ice_h.astype(np.float32), 1.9, 1.6, 1.0, origin=(0.05, 0.05, ICE_Z))
so = ice.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.3; so.offset = -1
im = bpy.data.materials.new("Ice"); im.use_nodes = True
N = im.node_tree.nodes; L = im.node_tree.links; p = N["Principled BSDF"]
p.inputs['Base Color'].default_value = (0.82, 0.93, 1.0, 1); p.inputs['Transmission Weight'].default_value = 1.0
p.inputs['IOR'].default_value = 1.31
tc = N.new("ShaderNodeTexCoord"); n1 = N.new("ShaderNodeTexNoise"); n1.inputs['Scale'].default_value = 7; n1.inputs['Detail'].default_value = 8
L.new(tc.outputs['Object'], n1.inputs['Vector'])
rr = N.new("ShaderNodeMapRange"); rr.inputs['To Min'].default_value = 0.18; rr.inputs['To Max'].default_value = 0.6
L.new(n1.outputs['Fac'], rr.inputs['Value']); L.new(rr.outputs[0], p.inputs['Roughness'])
n2 = N.new("ShaderNodeTexNoise"); n2.inputs['Scale'].default_value = 60; n2.inputs['Detail'].default_value = 6
L.new(tc.outputs['Object'], n2.inputs['Vector'])
b2 = N.new("ShaderNodeBump"); b2.inputs['Strength'].default_value = 0.25; L.new(n2.outputs['Fac'], b2.inputs['Height']); L.new(b2.outputs['Normal'], p.inputs['Normal'])
iv = N.new("ShaderNodeVolumePrincipled"); iv.inputs['Color'].default_value = (0.85, 0.95, 1.0, 1)
iv.inputs['Density'].default_value = 5.0; iv.inputs['Absorption Color'].default_value = (0.55, 0.8, 0.95, 1)
L.new(iv.outputs[0], N["Material Output"].inputs['Volume'])
p.inputs['Transmission Weight'].default_value = 0.85
crust = N.new("ShaderNodeBsdfPrincipled"); crust.inputs['Base Color'].default_value = (0.86, 0.9, 0.96, 1)
crust.inputs['Roughness'].default_value = 0.65; crust.inputs['Subsurface Weight'].default_value = 0.6
crust.inputs['Subsurface Radius'].default_value = (0.5, 0.8, 1.0); crust.inputs['Subsurface Scale'].default_value = 0.02
L.new(b2.outputs['Normal'], crust.inputs['Normal'])
geo = N.new("ShaderNodeNewGeometry"); sepn = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs['Normal'], sepn.inputs[0])
cn = N.new("ShaderNodeTexNoise"); cn.inputs['Scale'].default_value = 9; cn.inputs['Detail'].default_value = 6
L.new(tc.outputs['Object'], cn.inputs['Vector'])
cm = N.new("ShaderNodeMath"); cm.operation = 'MULTIPLY_ADD'; cm.inputs[1].default_value = 0.6
L.new(cn.outputs['Fac'], cm.inputs[0]); L.new(sepn.outputs['Z'], cm.inputs[2])
cr_ = N.new("ShaderNodeMapRange"); cr_.inputs['From Min'].default_value = 1.18; cr_.inputs['From Max'].default_value = 1.32
L.new(cm.outputs[0], cr_.inputs['Value'])
mx = N.new("ShaderNodeMixShader"); L.new(cr_.outputs[0], mx.inputs['Fac']); L.new(p.outputs[0], mx.inputs[1]); L.new(crust.outputs[0], mx.inputs[2])
L.new(mx.outputs[0], N["Material Output"].inputs['Surface'])
ice.data.materials.append(im)
ice.visible_shadow = False

# ---------------------------------------------------------------- the body, face-down
m = build_mummy("Otzi", pose=False)
_chain(m, [("upperarm01.L", (-0.85, 0.10, 0.42)), ("upperarm02.L", (-0.85, 0.10, 0.42)),
           ("lowerarm01.L", (-1, 0.12, 0.25)), ("lowerarm02.L", (-1, 0.12, 0.25))])
_chain(m, [("upperarm01.R", (-0.12, 0.05, -1)), ("upperarm02.R", (-0.12, 0.05, -1)),
           ("lowerarm01.R", (-0.05, 0.0, -1)), ("lowerarm02.R", (-0.05, 0.0, -1))])
for sd, sg in SIDE.items():
    m.rot(f"foot.{sd}", (1, 0, 0), 40)
m.rot("head", (0, 0, 1), 55); m.rot("neck01", (0, 0, 1), 15)
fingers_curl(m, 40, thumb=20)
lay_down(m, face_up=False, z=0.0)
m.arm.location = (0.0, 0.05, 0)
settle(m, ICE_Z - 0.06)       # sunk a few cm: back and head stand proud of the water, legs locked in the ice
bake_pose(m)
flatten_contact(m.body, ICE_Z - 0.06, band=0.07, squash=0.3)
# soak: darker, wetter skin where it sits in the meltwater
sk = m.body.data.materials[0]; pb = sk.node_tree.nodes["Principled BSDF"]
src = pb.inputs['Base Color'].links[0].from_socket
dkn = sk.node_tree.nodes.new("ShaderNodeMix"); dkn.data_type = 'RGBA'; dkn.blend_type = 'MULTIPLY'; dkn.inputs['Factor'].default_value = 1
sk.node_tree.links.new(src, dkn.inputs[6]); dkn.inputs[7].default_value = (0.55, 0.5, 0.5, 1)
sk.node_tree.links.new(dkn.outputs[2], pb.inputs['Base Color'])
pb.inputs['Coat Weight'].default_value = 0.6; pb.inputs['Coat Roughness'].default_value = 0.08
head_w = m.parts[0]
print("body extent", _world_verts(m.body).min(0), _world_verts(m.body).max(0))

# ---------------------------------------------------------------- the hikers (1991)
def hiker(name, gender, years, x, y, outfit, hair, hue=0.5, sat=1.0, val=1.0, look=(0, 0.6, 0.0), lean=6):
    h = Human(name, gender=gender, years=years, muscle=0.55, weight=0.45 if gender > 0.5 else 0.4, height=0.5 if gender > 0.5 else 0.38,
              skin="middleage_lightskinned_male_diffuse.png" if gender > 0.5 else "middleage_lightskinned_female_diffuse.png")
    add_asset(h, "clothes", outfit, hue=hue, sat=sat, val=val, rough=0.8, sheen=0.3)
    add_asset(h, "clothes", "shoes02", rough=0.7)
    add_asset(h, "hair", hair, rough=0.5, val=0.7)
    for sd, sg in SIDE.items():                       # relaxed arms
        h.rot(f"upperarm01.{sd}", (0, 1, 0), sg * 44)
        h.rot(f"lowerarm01.{sd}", (1, 0, 0), -22)
    fingers_curl(h, 20)
    h.rot("spine04", (1, 0, 0), lean); h.rot("neck01", (1, 0, 0), 12); h.rot("head", (1, 0, 0), 16)
    h.arm.rotation_euler = (0, 0, math.atan2(-(look[0] - x), (look[1] - y)) + math.pi)
    h.arm.location = (x, y, gh(x, y) - 0.02)
    return h

helmut = hiker("Helmut", 1.0, 51, 0.65, -2.3, "male_casualsuit05", "short02", lean=8)
erika = hiker("Erika", 0.0, 51, -0.55, -2.75, "male_casualsuit01", "bob02", hue=0.5, val=0.9, lean=4)
erika.rot("upperarm01.R", (1, 0, 0), -35); erika.rot("lowerarm01.R", (1, 0, 0), -70)   # hand raised to her face

# ---------------------------------------------------------------- boulders
rmat = rock_material("Rock"); add_fog(rmat, FOG, density=0.004, fog_max=0.9)
meshes = [make_rock(300 + k, rmat) for k in range(6)]
placed = 0
while placed < 45:
    x = rng.uniform(-14, 14); y = rng.uniform(-6, 16)
    if abs(x) < 2.0 and -4 < y < 4:
        continue
    sc = rng.uniform(0.3, 1.3) * (2.0 if rng.random() < 0.15 else 1)
    o = bpy.data.objects.new("Rock", meshes[placed % 6]); bpy.context.collection.objects.link(o)
    o.location = (x, y, gh(x, y) + sc * 0.05); o.rotation_euler = (rng.normal(0, .2), rng.normal(0, .2), rng.uniform(0, 6.3))
    o.scale = (sc, sc, sc * rng.uniform(0.6, 1)); placed += 1
for (x, y, sc, k) in [(-1.9, 1.6, 0.9, 1), (2.2, 2.4, 1.2, 3), (1.8, -0.6, 0.6, 4), (-2.4, -1.2, 0.7, 2)]:
    o = bpy.data.objects.new("Hero", meshes[k]); bpy.context.collection.objects.link(o)
    o.location = (x, y, gh(x, y) - 0.05); o.scale = (sc, sc * 0.9, sc * 0.7); o.rotation_euler = (0, 0, k)

# ---------------------------------------------------------------- distant ridge
hb = eroded_alpine(512, seed=34)
far = grid_mesh("Ridge", hb, 9000, 3000, 1200.0, origin=(0, -3200, -250))
fm = snow_rock_material("FarMat", snow_thresh=0.5, fog_color=FOG, fog_density=0.0005, fog_max=0.93, bump_scale=30)
far.data.materials.append(fm)

# ---------------------------------------------------------------- light: bright overcast high-alpine day
world_flat(FOG, 1.15)
sun(32, 30, energy=1.6, color=(1.0, 0.97, 0.92), angle_deg=6)

cam = camera((0, 0, 0), (0, 0, 0), lens=32, dof_dist=2.0, fstop=4.0)
head_pt = Vector(_world_verts(m.body)[np.argmax(_world_verts(m.body)[:, 1])])

def frame(i, t):
    e = ease(t)
    cam.location = Vector(lerp((1.05, 3.45, 0.44), (0.88, 3.05, 0.47), e))
    target = Vector(lerp((0.0, -0.4, 0.42), (-0.03, -0.55, 0.40), e))   # keep the body in frame
    point_at(cam, tuple(target))
    cam.data.dof.focus_distance = (cam.location - Vector((0.0, 0.9, 0.05))).length

render_frames(OUT, frame, FRAMES, STEP)
