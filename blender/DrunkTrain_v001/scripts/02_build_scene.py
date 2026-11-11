"""DrunkTrain scene: render settings, rail set, train, platform, houses, x-ray studio, props, people.
blender -b people.blend --python 02_build_scene.py -- <assets_root> <out.blend>
assets_root holds ph/ (Poly Haven) and glb/ (Objaverse GLBs)."""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:]
A, OUT = argv[0], argv[1]
PH, GLB = os.path.join(A, "ph"), os.path.join(A, "glb")
sc = bpy.context.scene
FPS, END = 60, 2070
random.seed(16)
GAUGE = 0.7175          # rail centre offset from track centre (1435 mm gauge)
RAIL_H = 0.172          # rail head top above sleeper top (z = 0)
TRACK_B = -4.3          # second track centre x
STOP_Y = -40.0          # where he ends up / studio centre y
sc["stop_y"] = STOP_Y

# ------------------------------------------------------------------ timeline / render
sc.render.fps, sc.render.fps_base = FPS, 1.0
sc.frame_start, sc.frame_end, sc.frame_step = 1, END, 1
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.engine = 'CYCLES'
c = sc.cycles
c.device = 'CPU'; c.samples = 48; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.05
c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'
c.max_bounces = 8; c.diffuse_bounces = 3; c.glossy_bounces = 3; c.transmission_bounces = 8; c.transparent_max_bounces = 16
c.caustics_reflective = c.caustics_refractive = False
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.render.use_persistent_data = True
sc.display_settings.display_device = 'sRGB'
vs = sc.view_settings
vs.view_transform = 'AgX'; vs.look = 'AgX - Medium High Contrast'; vs.exposure = 0.0; vs.gamma = 1.0
im = sc.render.image_settings
im.file_format = 'PNG'; im.color_mode = 'RGB'; im.color_depth = '8'; im.compression = 15
sc.render.filepath = "//render/DrunkTrain_v001_"

COL = {}
def coll(name):
    if name not in COL:
        c_ = bpy.data.collections.new(name); sc.collection.children.link(c_); COL[name] = c_
    return COL[name]
def link(o, cname="Set"):
    for c_ in o.users_collection: c_.objects.unlink(o)
    coll(cname).objects.link(o); return o

# ------------------------------------------------------------------ materials
def img(path, nc=False):
    i = bpy.data.images.load(path, check_existing=True)
    if nc: i.colorspace_settings.name = 'Non-Color'
    return i

def tex_files(tid, res="2k"):
    d = os.path.join(PH, tid, "textures")
    fs = os.listdir(d)
    def pick(key):
        for f in sorted(fs):
            if key in f and res in f: return os.path.join(d, f)
        return None
    out = (pick("_diff_"), pick("_rough_"), pick("_nor_gl_"))
    if out[0] is None and res != "1k": return tex_files(tid, "1k")
    return out

def pbr(name, tid, scale, sat=1.0, val=1.0, bump=1.0, rough_mul=1.0, tint=None, coords='Object', metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    p = n["Principled BSDF"]; p.inputs['Metallic'].default_value = metal
    D, Rr, N = tex_files(tid)
    tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / scale,) * 3
    l.new(tc.outputs[coords], mp.inputs['Vector'])
    d = n.new('ShaderNodeTexImage'); d.image = img(D); d.projection = 'BOX'; d.projection_blend = 0.25
    hsv = n.new('ShaderNodeHueSaturation'); hsv.inputs['Saturation'].default_value = sat; hsv.inputs['Value'].default_value = val
    l.new(mp.outputs['Vector'], d.inputs['Vector']); l.new(d.outputs['Color'], hsv.inputs['Color'])
    out = hsv.outputs['Color']
    if tint is not None:
        mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        mx.inputs['B'].default_value = tint + (1,) if len(tint) == 3 else tint
        l.new(out, mx.inputs['A']); out = mx.outputs['Result']
    l.new(out, p.inputs['Base Color'])
    if Rr:
        r = n.new('ShaderNodeTexImage'); r.image = img(Rr, True); r.projection = 'BOX'; r.projection_blend = 0.25; l.new(mp.outputs['Vector'], r.inputs['Vector'])
        rm = n.new('ShaderNodeMath'); rm.operation = 'MULTIPLY'; rm.inputs[1].default_value = rough_mul; rm.use_clamp = True
        l.new(r.outputs['Color'], rm.inputs[0]); l.new(rm.outputs[0], p.inputs['Roughness'])
    if N:
        nm = n.new('ShaderNodeTexImage'); nm.image = img(N, True); nm.projection = 'BOX'; nm.projection_blend = 0.25; l.new(mp.outputs['Vector'], nm.inputs['Vector'])
        nmap = n.new('ShaderNodeNormalMap'); nmap.inputs['Strength'].default_value = bump
        l.new(nm.outputs['Color'], nmap.inputs['Color']); l.new(nmap.outputs['Normal'], p.inputs['Normal'])
    return m

def flat(name, col, rough=0.5, metal=0.0, emit=None, estr=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = col + (1,) if len(col) == 3 else col
    p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    if emit:
        p.inputs['Emission Color'].default_value = emit + (1,); p.inputs['Emission Strength'].default_value = estr
    if alpha < 1: p.inputs['Alpha'].default_value = alpha
    return m

M_GRAVEL = pbr("Ballast", "gravel_stones", 1.2, sat=0.2, val=2.5, bump=1.4)
M_GRASS = pbr("Grass", "grass_path_2", 3.0, sat=0.9, val=0.85)
M_CONC = pbr("Concrete", "concrete_floor_02", 1.2, sat=0.3, val=1.05)
M_RUST = pbr("RailRust", "rusty_metal_02", 0.6, sat=0.8, val=0.65, rough_mul=1.0, metal=0.3)
M_BRICK = pbr("Brick", "brick_wall_02", 2.5, sat=0.85)
M_RENDER = pbr("Render", "beige_wall_001", 2.5, val=1.05)
M_ROOF = pbr("Roof", "clay_roof_tiles_02", 2.0, sat=0.8, val=0.85)
M_TRAINPAINT = {}

# rail: rusty web/foot, polished steel railhead (top-facing normals)
M_RAIL = M_RUST.copy(); M_RAIL.name = "Rail"
nt = M_RAIL.node_tree; p = nt.nodes["Principled BSDF"]
geo = nt.nodes.new('ShaderNodeNewGeometry'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Normal'], sep.inputs[0])
ramp = nt.nodes.new('ShaderNodeMapRange'); ramp.inputs['From Min'].default_value = 0.75; ramp.inputs['From Max'].default_value = 0.95
nt.links.new(sep.outputs['Z'], ramp.inputs['Value'])
steel = nt.nodes.new('ShaderNodeBsdfPrincipled'); steel.inputs['Base Color'].default_value = (0.62, 0.62, 0.64, 1)
steel.inputs['Metallic'].default_value = 1.0; steel.inputs['Roughness'].default_value = 0.22
mix = nt.nodes.new('ShaderNodeMixShader'); outn = nt.nodes["Material Output"]
nt.links.new(ramp.outputs['Result'], mix.inputs['Fac']); nt.links.new(p.outputs['BSDF'], mix.inputs[1]); nt.links.new(steel.outputs['BSDF'], mix.inputs[2])
nt.links.new(mix.outputs[0], outn.inputs['Surface'])

def mesh_obj(name, bm, mat=None, cname="Set"):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); coll(cname).objects.link(o)
    if mat: me.materials.append(mat)
    for poly in me.polygons: poly.use_smooth = False
    return o

def box(name, size, loc, mat=None, cname="Set", bevel=0.0):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    o = mesh_obj(name, bm, mat, cname); o.location = loc
    if bevel:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = 2
    return o

# ------------------------------------------------------------------ world: daylight HDRI + matching sun
w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
wn, wl = w.node_tree.nodes, w.node_tree.links
env = wn.new('ShaderNodeTexEnvironment'); env.image = img(os.path.join(PH, "hdri", "bloem_train_track_clear_2k.hdr"))
wmap = wn.new('ShaderNodeMapping'); wtc = wn.new('ShaderNodeTexCoord'); wmap.inputs['Rotation'].default_value = (0, 0, math.radians(110))
wl.new(wtc.outputs['Generated'], wmap.inputs['Vector']); wl.new(wmap.outputs['Vector'], env.inputs['Vector'])
bg = wn["Background"]; bg.inputs['Strength'].default_value = 1.0
wl.new(env.outputs['Color'], bg.inputs['Color'])
sun_d = bpy.data.lights.new("Sun", 'SUN'); sun_d.energy = 3.5; sun_d.angle = math.radians(1.2); sun_d.color = (1.0, 0.96, 0.9)
sun = bpy.data.objects.new("Sun", sun_d); coll("Lights").objects.link(sun)
sun.rotation_euler = (math.radians(40), 0, math.radians(-135))   # high afternoon sun from behind-left of the train

# ------------------------------------------------------------------ ground, ballast, sleepers, rails
Y0, Y1 = -160.0, 260.0
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=1.0)
for v in bm.verts: v.co = Vector((v.co.x * 260, v.co.y * 260 + 50, -0.08))
g = mesh_obj("Grass", bm, M_GRASS)
# ballast bed: trapezoid profile across both tracks, extruded along Y
prof = [(-8.6, -0.08), (-7.2, -0.03), (2.6, -0.03), (3.4, -0.08)]
bm = bmesh.new()
vs_ = [[bm.verts.new((x, y, z)) for x, z in prof] for y in (Y0, Y1)]
for i in range(len(prof) - 1):
    bm.faces.new((vs_[0][i], vs_[0][i + 1], vs_[1][i + 1], vs_[1][i]))
ball = mesh_obj("Ballast", bm, M_GRAVEL)
# sleepers (concrete) via array
for tx, nm in ((0.0, "A"), (TRACK_B, "B")):
    s = box("Sleeper" + nm, (2.6, 0.26, 0.2), (tx, Y0 + 1.0, -0.1), M_CONC, bevel=0.015)
    a = s.modifiers.new("arr", 'ARRAY'); a.count = int((Y1 - Y0 - 2) / 0.65); a.use_relative_offset = False
    a.use_constant_offset = True; a.constant_offset_displace = (0, 0.65, 0)
# rail profile (x, z) relative to rail centre at sleeper top
RP = [(-0.075, 0.0), (0.075, 0.0), (0.075, 0.012), (0.0085, 0.03), (0.0085, 0.128), (0.036, 0.14), (0.036, RAIL_H),
      (-0.036, RAIL_H), (-0.036, 0.14), (-0.0085, 0.128), (-0.0085, 0.03), (-0.075, 0.012)]
RAILS = []
for tx in (0.0, TRACK_B):
    for sx in (-1, 1):
        bm = bmesh.new()
        ring0 = [bm.verts.new((tx + sx * GAUGE + x, Y0, z)) for x, z in RP]
        ring1 = [bm.verts.new((tx + sx * GAUGE + x, Y1, z)) for x, z in RP]
        n_ = len(RP)
        for i in range(n_):
            bm.faces.new((ring0[i], ring0[(i + 1) % n_], ring1[(i + 1) % n_], ring1[i]))
        bm.faces.new(list(reversed(ring0))); bm.faces.new(ring1)
        o = mesh_obj("Rail_%s%s" % ("A" if tx == 0 else "B", "L" if sx < 0 else "R"), bm, M_RAIL)
        RAILS.append(o)
sc["rail_h"] = RAIL_H; sc["gauge"] = GAUGE
# loose ballast stones scattered (geometry nodes, evaluated at render; no caches)
def rock_mesh(name, r):
    # angular crushed stone: a jittered, randomly chamfered cube
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2 * r)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=r * random.uniform(0.15, 0.35), segments=1, affect='EDGES')
    for v in bm.verts: v.co = Vector((v.co.x * random.uniform(0.7, 1.3), v.co.y * random.uniform(0.7, 1.3), v.co.z * random.uniform(0.5, 0.85))) + Vector([random.uniform(-0.15, 0.15) * r for _ in range(3)])
    o = mesh_obj(name, bm, M_STONE, "Hidden"); return o
M_STONE = bpy.data.materials.new("BallastStone"); M_STONE.use_nodes = True
_n, _l = M_STONE.node_tree.nodes, M_STONE.node_tree.links
_p = _n["Principled BSDF"]; _p.inputs['Roughness'].default_value = 0.85
_nz = _n.new('ShaderNodeTexNoise'); _nz.inputs['Scale'].default_value = 60.0; _nz.inputs['Detail'].default_value = 6
_cr = _n.new('ShaderNodeValToRGB'); _cr.color_ramp.elements[0].color = (0.16, 0.155, 0.15, 1); _cr.color_ramp.elements[1].color = (0.48, 0.46, 0.43, 1)
_oi = _n.new('ShaderNodeObjectInfo'); _ad = _n.new('ShaderNodeMath'); _ad.operation = 'ADD'
_l.new(_nz.outputs['Fac'], _ad.inputs[0]); _l.new(_oi.outputs['Random'], _ad.inputs[1])
_mm = _n.new('ShaderNodeMath'); _mm.operation = 'MULTIPLY'; _mm.inputs[1].default_value = 0.6; _l.new(_ad.outputs[0], _mm.inputs[0])
_l.new(_mm.outputs[0], _cr.inputs['Fac']); _l.new(_cr.outputs['Color'], _p.inputs['Base Color'])
_bp = _n.new('ShaderNodeBump'); _bp.inputs['Strength'].default_value = 0.4; _l.new(_nz.outputs['Fac'], _bp.inputs['Height']); _l.new(_bp.outputs['Normal'], _p.inputs['Normal'])
rocks = [rock_mesh("Rock%d" % i, random.uniform(0.015, 0.03)) for i in range(8)]
coll("Hidden").hide_render = True; coll("Hidden").hide_viewport = True
rc = bpy.data.collections.new("RockSet"); coll("Hidden").children.link(rc)
for r in rocks: rc.objects.link(r)
def scatter(target, coll_, density, seed, scale=(0.8, 1.4), name="Scatter", keep_base=True):
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N, L = ng.nodes, ng.links
    gi = N.new('NodeGroupInput'); go = N.new('NodeGroupOutput')
    dist = N.new('GeometryNodeDistributePointsOnFaces'); dist.inputs['Density'].default_value = density; dist.inputs['Seed'].default_value = seed
    ci = N.new('GeometryNodeCollectionInfo'); ci.inputs['Collection'].default_value = coll_; ci.inputs['Separate Children'].default_value = True
    ci.inputs['Reset Children'].default_value = True
    inst = N.new('GeometryNodeInstanceOnPoints'); inst.inputs['Pick Instance'].default_value = True
    rr = N.new('FunctionNodeRandomValue'); rr.data_type = 'FLOAT_VECTOR'; rr.inputs['Max'].default_value = (6.3, 6.3, 6.3)
    rs = N.new('FunctionNodeRandomValue'); rs.data_type = 'FLOAT'
    fv = [s_ for s_ in rs.inputs if s_.type == 'VALUE' and s_.name in ('Min', 'Max')]; fv[0].default_value = scale[0]; fv[1].default_value = scale[1]
    fo = [s_ for s_ in rs.outputs if s_.type == 'VALUE'][0]
    real = N.new('GeometryNodeRealizeInstances'); jn = N.new('GeometryNodeJoinGeometry')
    L.new(gi.outputs[0], dist.inputs['Mesh']); L.new(dist.outputs['Points'], inst.inputs['Points'])
    L.new(ci.outputs[0], inst.inputs['Instance']); L.new(rr.outputs[0], inst.inputs['Rotation']); L.new(fo, inst.inputs['Scale'])
    if keep_base: L.new(gi.outputs[0], jn.inputs[0])
    L.new(inst.outputs[0], jn.inputs[0]); L.new(jn.outputs[0], go.inputs[0])
    md = target.modifiers.new(name, 'NODES'); md.node_group = ng
    return md
# a separate near-camera ballast patch gets the stones (keeps memory low)
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0)
for v in bm.verts: v.co = Vector((v.co.x * 4.6 - 1.6, v.co.y * 40 - 22, -0.03))
patch = mesh_obj("BallastStones", bm, M_GRAVEL)
scatter(patch, rc, 900.0, 3, scale=(0.7, 1.2), name="Stones")

# ------------------------------------------------------------------ platform, fence, houses, poles, trees, grass clumps
PLAT = dict(x0=3.05, x1=7.5, y0=-80.0, y1=-46.0, h=0.92)
sc["plat"] = str(PLAT)
M_PAVERS = pbr("Pavers", "concrete_pavers_02", 1.2, sat=0.5, val=0.95, bump=1.2)
M_COPING = pbr("Coping", "concrete_floor_02", 0.8, sat=0.3, val=1.15, bump=1.5)
body = box("Platform", (PLAT["x1"] - PLAT["x0"], PLAT["y1"] - PLAT["y0"], PLAT["h"] - 0.02),
           ((PLAT["x0"] + PLAT["x1"]) / 2, (PLAT["y0"] + PLAT["y1"]) / 2, (PLAT["h"] - 0.02) / 2 - 0.08 / 2 + 0.0), M_BRICK, bevel=0.015)
box("PlatformTop", (PLAT["x1"] - PLAT["x0"] - 0.55, PLAT["y1"] - PLAT["y0"], 0.05), ((PLAT["x0"] + 0.55 + PLAT["x1"]) / 2, (PLAT["y0"] + PLAT["y1"]) / 2, PLAT["h"] - 0.025), M_PAVERS, bevel=0.005)
# coping stones: individual slabs with joints, a slight overhang and small random settling
y_ = PLAT["y0"]; k = 0
while y_ < PLAT["y1"] - 0.3:
    L_ = min(0.9, PLAT["y1"] - y_ - 0.006)
    cs = box("Coping%d" % k, (0.6, L_ - 0.006, 0.08), (PLAT["x0"] + 0.25, y_ + L_ / 2, PLAT["h"] - 0.04 + random.uniform(-0.003, 0.003)), M_COPING, bevel=0.012)
    cs.rotation_euler = (random.uniform(-0.004, 0.004), random.uniform(-0.004, 0.004), random.uniform(-0.003, 0.003))
    y_ += L_; k += 1
M_EDGEPAINT = flat("EdgePaint", (0.78, 0.62, 0.12), 0.75)
_n = M_EDGEPAINT.node_tree.nodes; _l = M_EDGEPAINT.node_tree.links
_nz = _n.new('ShaderNodeTexNoise'); _nz.inputs['Scale'].default_value = 18; _nz.inputs['Detail'].default_value = 8
_cr = _n.new('ShaderNodeValToRGB'); _cr.color_ramp.elements[0].position = 0.42; _cr.color_ramp.elements[1].position = 0.6
_cr.color_ramp.elements[0].color = (0.33, 0.31, 0.28, 1); _cr.color_ramp.elements[1].color = (0.78, 0.62, 0.12, 1)
_l.new(_nz.outputs['Fac'], _cr.inputs['Fac']); _l.new(_cr.outputs['Color'], _n["Principled BSDF"].inputs['Base Color'])
edge = box("PlatformEdge", (0.1, PLAT["y1"] - PLAT["y0"], 0.004), (PLAT["x0"] + 0.48, (PLAT["y0"] + PLAT["y1"]) / 2, PLAT["h"] + 0.0005), M_EDGEPAINT)
# ramp down at the north end
bm = bmesh.new()
v = [bm.verts.new(p_) for p_ in ((PLAT["x0"] + 1.0, PLAT["y1"], PLAT["h"]), (PLAT["x1"], PLAT["y1"], PLAT["h"]), (PLAT["x1"], PLAT["y1"] + 5.5, -0.03),
                                  (PLAT["x0"] + 1.0, PLAT["y1"] + 5.5, -0.03), (PLAT["x0"] + 1.0, PLAT["y1"], -0.03), (PLAT["x1"], PLAT["y1"], -0.03))]
bm.faces.new((v[0], v[3], v[2], v[1])); bm.faces.new((v[0], v[4], v[3])); bm.faces.new((v[1], v[2], v[5])); bm.faces.new((v[0], v[1], v[5], v[4]))
mesh_obj("Ramp", bm, M_PAVERS)
sc["ramp"] = str(dict(x0=PLAT["x0"] + 1.0, x1=PLAT["x1"], y0=PLAT["y1"], y1=PLAT["y1"] + 5.5, h=PLAT["h"]))
M_POLE = flat("PoleGrey", (0.35, 0.36, 0.37), 0.5, 0.6)
# fence (chain link look via procedural mask) along x = +9.5
M_FENCE = flat("ChainLink", (0.55, 0.57, 0.58), 0.4, 0.8)
fn = M_FENCE.node_tree.nodes; fl = M_FENCE.node_tree.links
tc = fn.new('ShaderNodeTexCoord'); mp = fn.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (math.radians(45), 0, 0)
mp.inputs['Scale'].default_value = (18, 18, 18)
fl.new(tc.outputs['Object'], mp.inputs['Vector'])
wv = fn.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.inputs['Scale'].default_value = 1.0
wv2 = fn.new('ShaderNodeTexWave'); wv2.wave_type = 'BANDS'; wv2.bands_direction = 'Y'
fl.new(mp.outputs['Vector'], wv.inputs['Vector']); fl.new(mp.outputs['Vector'], wv2.inputs['Vector'])
mx = fn.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'
fl.new(wv.outputs['Fac'], mx.inputs[0]); fl.new(wv2.outputs['Fac'], mx.inputs[1])
gt = fn.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.93
fl.new(mx.outputs[0], gt.inputs[0]); fl.new(gt.outputs[0], fn["Principled BSDF"].inputs['Alpha'])
bm = bmesh.new()
v = [bm.verts.new(p_) for p_ in ((9.5, -120, -0.08), (9.5, 120, -0.08), (9.5, 120, 1.8), (9.5, -120, 1.8))]
bm.faces.new(v)
fence = mesh_obj("Fence", bm, M_FENCE)
for yy in range(-120, 121, 3):
    box("FPost%d" % yy, (0.05, 0.05, 1.9), (9.5, yy, 0.87), M_POLE)
# poles + wires (no text anywhere)
M_WOOD = pbr("PoleWood", "rust_coarse_01", 0.5, sat=0.25, val=0.6, tint=(0.55, 0.42, 0.3), rough_mul=1.0)
for yy in range(-110, 200, 32):
    bmp = bmesh.new(); bmesh.ops.create_cone(bmp, cap_ends=True, segments=16, radius1=0.14, radius2=0.11, depth=8.5)
    po = mesh_obj("Pole%d" % yy, bmp, M_WOOD); po.location = (8.6, yy, 4.2)
    for poly in po.data.polygons: poly.use_smooth = True
    box("Arm%d" % yy, (1.6, 0.12, 0.12), (8.6, yy, 8.0), M_WOOD)
M_WIRE = flat("Wire", (0.05, 0.05, 0.05), 0.4)
for wx in (7.95, 9.25):
    bm = bmesh.new(); last = None
    pts = []
    for yy in range(-110, 200 - 32 + 1, 32):
        for k in range(9):
            t = k / 8; pts.append((wx, yy + 32 * t, 8.1 - 0.55 * math.sin(math.pi * t)))
    cu = bpy.data.curves.new("Wire%.0f" % wx, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.012
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for i, p_ in enumerate(pts): sp.points[i].co = (p_[0], p_[1], p_[2], 1)
    o = bpy.data.objects.new("Wire%.0f" % wx, cu); coll("Set").objects.link(o); cu.materials.append(M_WIRE)
# houses: a row of suburban houses with gardens beyond the fence (and a few on the far side)
M_WIN = flat("WindowGlass", (0.05, 0.07, 0.08), 0.05, 0.0)
M_FRAME = flat("WindowFrame", (0.9, 0.9, 0.88), 0.4)
M_GARDENFENCE = flat("GardenFence", (0.42, 0.3, 0.2), 0.8)
def house(name, cx, cy, w_, d_, h_, mat, face=-1):
    box(name + "_walls", (w_, d_, h_), (cx, cy, h_ / 2 - 0.08), mat)
    bm = bmesh.new()
    r = 0.4
    a = [bm.verts.new((cx - w_ / 2 - r, y_, h_ - 0.08)) for y_ in (cy - d_ / 2 - r, cy + d_ / 2 + r)]
    b = [bm.verts.new((cx + w_ / 2 + r, y_, h_ - 0.08)) for y_ in (cy - d_ / 2 - r, cy + d_ / 2 + r)]
    t = [bm.verts.new((cx, y_, h_ + w_ * 0.38)) for y_ in (cy - d_ / 2 - r, cy + d_ / 2 + r)]
    bm.faces.new((a[0], a[1], t[1], t[0])); bm.faces.new((b[1], b[0], t[0], t[1]))
    bm.faces.new((a[0], t[0], b[0])); bm.faces.new((a[1], b[1], t[1]))
    mesh_obj(name + "_roof", bm, M_ROOF)
    fx = cx + face * (w_ / 2 + 0.01)
    for fz in (1.2, 3.9):
        for k in range(3):
            yy = cy - d_ / 2 + d_ * (k + 0.5) / 3
            box(name + "_win%d%d" % (k, fz), (0.06, 1.2, 1.25), (fx, yy, fz + 0.3), M_WIN)
            box(name + "_fr%d%d" % (k, fz), (0.04, 1.36, 1.41), (fx - face * 0.02, yy, fz + 0.3), M_FRAME)
    # garden fence toward the rail
    gx = cx + face * (w_ / 2 + 4.5)
    box(name + "_gfence", (0.05, d_ + 6, 1.3), (gx, cy, 0.57), M_GARDENFENCE)
# laundry line in one garden (cloth with wave = wind; no sim)
M_SHEET = flat("Laundry", (0.85, 0.85, 0.9), 0.8)
for k, yy in enumerate((-31.5, -30.0, -28.6)):
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=6, y_segments=8, size=0.5)
    for v_ in bm.verts: v_.co = Vector((0, v_.co.x * 1.2, v_.co.y * 1.6))
    o = mesh_obj("Laundry%d" % k, bm, M_SHEET); o.location = (14.5, yy, 1.4)
    wm = o.modifiers.new("wind", 'WAVE'); wm.use_normal = True; wm.use_x = True; wm.use_y = False; wm.height = 0.08; wm.width = 0.7; wm.speed = 0.04; wm.time_offset = k * 13
    o.data.materials[0] = flat("Laundry%d" % k, [(0.85, 0.85, 0.9), (0.3, 0.45, 0.7), (0.8, 0.5, 0.35)][k], 0.8)
box("LaundryLine", (0.02, 6.0, 0.02), (14.5, -30.0, 2.22), M_WIRE)
# trees (Poly Haven jacaranda), linked duplicates
tree_src = os.path.join(PH, "jacaranda_tree", "jacaranda_tree_1k.blend")
with bpy.data.libraries.load(tree_src, link=False) as (src, dst):
    dst.objects = [n for n in src.objects]
tree_objs = [o for o in dst.objects if o is not None and o.type == 'MESH' and o.name in ("jacaranda_tree_geometry_nodes", "jacaranda_tree_trunk_LOD1")]
tc_ = bpy.data.collections.new("TreeSrc"); coll("Hidden").children.link(tc_)
for o in tree_objs: tc_.objects.link(o)
for o in dst.objects:      # drop the heavy realised LOD meshes; leaves stay as GN instance sources
    if o is not None and o.name in ("jacaranda_tree_LOD0", "jacaranda_tree_LOD1", "jacaranda_tree_trunk_LOD0"):
        bpy.data.objects.remove(o, do_unlink=True)
for i, (tx, ty, s) in enumerate([(13, -70, 1.0), (15.5, -12, 1.2), (12.5, 25, 0.9), (16, 60, 1.1), (-13, -55, 1.0), (-14.5, -5, 1.25),
                                 (-12.5, 40, 1.05), (-16, 85, 1.2), (13.5, 110, 1.0), (14, -105, 1.1)]):
    e = bpy.data.objects.new("Tree%d" % i, None); e.instance_type = 'COLLECTION'; e.instance_collection = tc_
    coll("Set").objects.link(e); e.location = (tx, ty, -0.08); e.scale = (s, s, s); e.rotation_euler.z = random.uniform(0, 6.28)
# grass clumps along the ballast edges
gsrc = os.path.join(PH, "grass_medium_01", "grass_medium_01_1k.blend")
with bpy.data.libraries.load(gsrc, link=False) as (src, dst):
    dst.objects = [n for n in src.objects]
gc = bpy.data.collections.new("GrassSrc"); coll("Hidden").children.link(gc)
for o in dst.objects:
    if o is not None and o.type == 'MESH': gc.objects.link(o)
for nm, x0, x1 in (("GrassStripE", 3.4, 9.3), ("GrassStripW", -12.0, -8.6)):
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0)
    for v_ in bm.verts: v_.co = Vector(((x0 + x1) / 2 + v_.co.x * (x1 - x0) / 2, -20 + v_.co.y * 70, -0.075))
    gs = mesh_obj(nm, bm, M_GRASS); scatter(gs, gc, 1.2, 7, scale=(0.6, 1.2), name="Clumps" + nm)
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0)
for v_ in bm.verts: v_.co = Vector((v_.co.x * 4.6 - 1.6, v_.co.y * 40 - 22, -0.02))
weeds = mesh_obj("BallastWeeds", bm, M_GRAVEL); weeds.hide_render = False
scatter(weeds, gc, 0.35, 11, scale=(0.18, 0.4), name="Weeds", keep_base=False)


# ------------------------------------------------------------------ train: loco + 2 wagons (GLB, re-materialled with grime)
def import_glb(path):
    """import, flatten the hierarchy, apply all transforms; returns mesh objects in world space"""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    objs = [o for o in bpy.data.objects if o not in before]
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    for o in objs:
        if o.type != 'MESH': bpy.data.objects.remove(o, do_unlink=True)
    meshes = [o for o in objs if o.name in bpy.data.objects and bpy.data.objects[o.name] == o] if False else [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.make_single_user(object=True, obdata=True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.context.view_layer.update()
    return meshes

def bbox(objs):
    pts = [o.matrix_world @ Vector(cc) for o in objs if o.type == 'MESH' for cc in o.bound_box]
    return Vector([min(p_[i] for p_ in pts) for i in range(3)]), Vector([max(p_[i] for p_ in pts) for i in range(3)])

def grime(src_mat, name):
    """keep the model's colour, multiply a rust/grime texture over it, rougher"""
    p0 = src_mat.node_tree.nodes.get("Principled BSDF") if src_mat and src_mat.use_nodes else None
    col = tuple(p0.inputs['Base Color'].default_value)[:3] if p0 else (0.3, 0.3, 0.3)
    m = pbr(name, "rust_coarse_01", 1.5, sat=0.35, val=1.0, rough_mul=0.9)
    n, l = m.node_tree.nodes, m.node_tree.links
    pr = n["Principled BSDF"]; link_ = pr.inputs['Base Color'].links[0]; srcsock = link_.from_socket
    mx_ = n.new('ShaderNodeMix'); mx_.data_type = 'RGBA'; mx_.blend_type = 'MULTIPLY'; mx_.inputs['Factor'].default_value = 0.75
    mx_.inputs['A'].default_value = tuple(min(1, c_ * 1.6 + 0.04) for c_ in col) + (1,)
    l.new(srcsock, mx_.inputs['B']); l.new(mx_.outputs['Result'], pr.inputs['Base Color'])
    pr.inputs['Metallic'].default_value = 0.25
    tcw = n.new('ShaderNodeTexCoord'); sxyz = n.new('ShaderNodeSeparateXYZ'); l.new(tcw.outputs['Object'], sxyz.inputs[0])
    mpw = n.new('ShaderNodeMapping'); mpw.inputs['Scale'].default_value = (9.0, 9.0, 0.35); l.new(tcw.outputs['Object'], mpw.inputs['Vector'])
    nzs = n.new('ShaderNodeTexNoise'); nzs.inputs['Scale'].default_value = 3.0; nzs.inputs['Detail'].default_value = 8; l.new(mpw.outputs['Vector'], nzs.inputs['Vector'])
    st_ = n.new('ShaderNodeMapRange'); st_.inputs['From Min'].default_value = 0.52; st_.inputs['From Max'].default_value = 0.68; l.new(nzs.outputs['Fac'], st_.inputs['Value'])
    rs_ = n.new('ShaderNodeMix'); rs_.data_type = 'RGBA'; rs_.blend_type = 'MULTIPLY'; rs_.inputs['B'].default_value = (0.42, 0.22, 0.1, 1)
    l.new(st_.outputs['Result'], rs_.inputs['Factor']); l.new(mx_.outputs['Result'], rs_.inputs['A'])
    dz_ = n.new('ShaderNodeMapRange'); dz_.inputs['From Min'].default_value = 1.4; dz_.inputs['From Max'].default_value = 0.2; l.new(sxyz.outputs['Z'], dz_.inputs['Value'])
    nzd = n.new('ShaderNodeTexNoise'); nzd.inputs['Scale'].default_value = 6.0; l.new(tcw.outputs['Object'], nzd.inputs['Vector'])
    dm_ = n.new('ShaderNodeMath'); dm_.operation = 'MULTIPLY'; l.new(dz_.outputs['Result'], dm_.inputs[0]); l.new(nzd.outputs['Fac'], dm_.inputs[1])
    du_ = n.new('ShaderNodeMix'); du_.data_type = 'RGBA'; du_.inputs['B'].default_value = (0.33, 0.27, 0.2, 1)
    l.new(dm_.outputs[0], du_.inputs['Factor']); l.new(rs_.outputs['Result'], du_.inputs['A'])
    nzo = n.new('ShaderNodeTexNoise'); nzo.inputs['Scale'].default_value = 1.6; l.new(tcw.outputs['Object'], nzo.inputs['Vector'])
    oi_ = n.new('ShaderNodeMapRange'); oi_.inputs['From Min'].default_value = 0.6; oi_.inputs['From Max'].default_value = 0.7; oi_.inputs['To Max'].default_value = 0.7
    l.new(nzo.outputs['Fac'], oi_.inputs['Value'])
    ol_ = n.new('ShaderNodeMix'); ol_.data_type = 'RGBA'; ol_.inputs['B'].default_value = (0.02, 0.018, 0.015, 1)
    l.new(oi_.outputs['Result'], ol_.inputs['Factor']); l.new(du_.outputs['Result'], ol_.inputs['A'])
    l.new(ol_.outputs['Result'], pr.inputs['Base Color'])
    return m

TRAIN = bpy.data.objects.new("TrainRig", None); coll("Train").objects.link(TRAIN)
WHEELS = []
def build_vehicle(path, name, length, y_off, keep_wheels):
    meshes = import_glb(path)
    mn, mx_ = bbox(meshes)
    ext = mx_ - mn
    along_y = ext.y >= ext.x
    s = length / (ext.y if along_y else ext.x)
    ctr = Vector(((mn.x + mx_.x) / 2, (mn.y + mx_.y) / 2, mn.z))
    R = Matrix.Identity(4) if along_y else Matrix.Rotation(math.radians(90), 4, 'Z')
    T = Matrix.Translation((0, y_off + length / 2, RAIL_H * 0)) @ R @ Matrix.Scale(s, 4) @ Matrix.Translation(-ctr)
    mats = {}
    wheels, body = [], []
    for o in meshes:
        o.data.transform(T)
        for i, m_ in enumerate(o.data.materials):
            if m_ is None: continue
            if m_.name not in mats: mats[m_.name] = grime(m_, name + "_" + m_.name[:20])
            o.data.materials[i] = mats[m_.name]
        (wheels if keep_wheels and o.name.startswith("wheel") else body).append(o)
    for o in meshes: link(o, "Train")
    bpy.ops.object.select_all(action='DESELECT')
    for o in body: o.select_set(True)
    bpy.context.view_layer.objects.active = body[0]
    bpy.ops.object.join(); b = bpy.context.view_layer.objects.active; b.name = name
    b.parent = TRAIN
    for wo in wheels:
        # origin at wheel centre so it can spin about its axle (x)
        mnw, mxw = bbox([wo]); cw = (mnw + mxw) / 2
        wo.data.transform(Matrix.Scale((2 * GAUGE + 0.14) / max(0.01, mxw.x - mnw.x), 4, (1, 0, 0)) @ Matrix.Translation(-cw)); wo.location = cw; wo.parent = TRAIN; wo.rotation_mode = 'XYZ'; bpy.context.view_layer.update()
        WHEELS.append(wo)
    bpy.context.view_layer.update(); mnb, mxb = bbox([b] + wheels)
    print("VEHICLE", name, round(s, 3), [round(v, 2) for v in mnb], [round(v, 2) for v in mxb], len(wheels), "wheels")
    return b, wheels

# ---- locomotive: EMD GP18 (CC-BY), detailed real geometry, untextured -> our weathered paint and metal
def paint(name, col, rough=0.55, metal=0.2):
    m = flat("tmp_" + name, col, rough, metal)
    g = grime(m, name); bpy.data.materials.remove(m); return g
LOCO_PAINT = {"Rock_Island_Rusty": paint("LocoPaint", (0.33, 0.07, 0.05), 0.5),           # weathered maroon hood
              "M_0136_Charcoal": paint("LocoTrucks", (0.05, 0.05, 0.05), 0.6, 0.6),
              "black": paint("LocoBlack", (0.03, 0.03, 0.03), 0.6, 0.5),
              "Metal_Corrugated_Shiny_1": paint("LocoMetal", (0.25, 0.25, 0.24), 0.4, 0.8)}
M_GLASS = flat("LocoGlass", (0.03, 0.04, 0.045), 0.05, 0.0)
M_LENS = flat("LocoLens", (1, 1, 0.9), 0.2, emit=(1.0, 0.93, 0.75), estr=8)
gp = import_glb(os.path.join(GLB, "gp18.glb"))
for o in list(gp):
    if o.name.startswith("Cube"): bpy.data.objects.remove(o, do_unlink=True); gp.remove(o)
mn, mx_ = bbox(gp); s = 17.8 / (mx_.y - mn.y)
T = Matrix.Translation((0, 0, RAIL_H)) @ Matrix.Scale(s, 4) @ Matrix.Translation(-Vector(((mn.x + mx_.x) / 2, mn.y, mn.z + 0.0)))
# wheel axles (model space) found by the loose-part survey: 4 axles, wheels r 0.405, centre z 0.13, gauge centre x -1.38
AX_Y = [-3.92, -1.81, 4.06, 6.18]; WZ, WRm = 0.13, 0.405
low = -0.27   # model z of the wheel bottoms
T = Matrix.Translation((0, 0, RAIL_H)) @ Matrix.Scale(s, 4) @ Matrix.Translation(-Vector((-1.38, mn.y, low)))
for o in gp:
    me = o.data
    # cut the model's static wheel discs out; our wheelsets spin in their place
    bmw = bmesh.new(); bmw.from_mesh(me)
    kill = [v for v in bmw.verts if any(math.hypot(v.co.y - ay, v.co.z - WZ) < WRm + 0.03 and abs(abs(v.co.x + 1.38) - 0.575) < 0.11 for ay in AX_Y)]
    bmesh.ops.delete(bmw, geom=kill, context='VERTS'); bmw.to_mesh(me); bmw.free()
    me.transform(T)
    # open a body-sized gap under the loco: centre under-gear and the pilot's lower plate (camera never sees inside the trucks)
    bmw = bmesh.new(); bmw.from_mesh(me)
    kill = [v for v in bmw.verts if (abs(v.co.x) < 0.55 and v.co.z < 0.52) or (v.co.y < 1.3 and v.co.z < 0.48 and abs(v.co.x) < 1.45)]
    bmesh.ops.delete(bmw, geom=kill, context='VERTS'); bmw.to_mesh(me); bmw.free()
    for i, m_ in enumerate(me.materials):
        nm = m_.name if m_ else ""
        if nm in LOCO_PAINT: me.materials[i] = LOCO_PAINT[nm]
        elif "Window" in nm or "Translucent" in nm: me.materials[i] = M_GLASS
        elif nm == "light_marker_effect_white": me.materials[i] = M_LENS
        elif "marker" in nm.lower() or "light" in nm.lower(): me.materials[i] = M_GLASS
        else: me.materials[i] = LOCO_PAINT["black"] if False else paint("LocoPart_" + nm[:12], (0.12, 0.12, 0.11), 0.6, 0.5)
    link(o, "Train")
bpy.ops.object.select_all(action='DESELECT')
for o in gp: o.select_set(True)
bpy.context.view_layer.objects.active = gp[0]; bpy.ops.object.join()
loco = bpy.context.view_layer.objects.active; loco.name = "Loco"; loco.parent = TRAIN
WR = WRm * s
sc["wheel_r"] = WR
M_WHEEL = pbr("WheelSteel", "rusty_metal_02", 0.4, sat=0.3, val=0.55, metal=0.8, rough_mul=0.8)
def wheelset_mesh(name):
    bmw = bmesh.new()
    for sx in (-1, 1):
        for rad, w0, w1 in ((WR, 0.0, 0.13), (WR + 0.03, -0.03, 0.0), (WR * 0.55, 0.13, 0.17)):
            m_ = Matrix.Translation((sx * (GAUGE - 0.035 + (w0 + w1) / 2), 0, 0)) @ Matrix.Rotation(math.radians(90), 4, 'Y')
            bmesh.ops.create_cone(bmw, cap_ends=True, segments=32, radius1=rad, radius2=rad, depth=(w1 - w0), matrix=m_)
    bmesh.ops.create_cone(bmw, cap_ends=True, segments=16, radius1=0.085, radius2=0.085, depth=2 * GAUGE + 0.3, matrix=Matrix.Rotation(math.radians(90), 4, 'Y'))
    me_ = bpy.data.meshes.new(name); bmw.to_mesh(me_); bmw.free(); me_.materials.append(M_WHEEL)
    for poly in me_.polygons: poly.use_smooth = True
    return me_
WS_ME = wheelset_mesh("Wheelset")
lw = []
for k, ay in enumerate(AX_Y):
    wo = bpy.data.objects.new("wheelset%d" % k, WS_ME); coll("Train").objects.link(wo)
    wo.location = ((0.0), (ay - mn.y) * s, RAIL_H + WR); wo.parent = TRAIN; wo.rotation_mode = 'XYZ'
    lw.append(wo); WHEELS.append(wo)
bpy.context.view_layer.update()
print("VEHICLE Loco GP18 scale", round(s, 3), [round(v, 2) for v in bbox([loco])[0]], [round(v, 2) for v in bbox([loco])[1]], "wheel r", round(WR, 3))
wag1, _ = build_vehicle(os.path.join(GLB, "wagon.glb"), "Wagon1", 14.5, 18.4, False)
wag2 = wag1.copy(); wag2.data = wag1.data; wag2.name = "Wagon2"; coll("Train").objects.link(wag2); wag2.location.y += 15.1
mn1, _ = bbox([wag1]); dz = RAIL_H + 0.0 - mn1.z
wag1.location.z += dz; wag2.location.z += dz
print("WHEELS", len(WHEELS), "r", sc["wheel_r"])
mnL, mxL = bbox([loco])
sc["loco_front"] = mnL.y; sc["loco_len"] = mxL.y - mnL.y; sc["loco_halfw"] = (mxL.x - mnL.x) / 2; sc["loco_top"] = mxL.z
# headlight glow points: the GP18's own headlight (above the cab windows) and two ditch lights on the pilot
M_HEAD = flat("Headlamp", (1, 1, 0.9), 0.2, emit=(1.0, 0.93, 0.75), estr=60)
LV = [loco.matrix_world @ v.co for v in loco.data.vertices]
def nose_y(xc, zc, dx=0.25, dz=0.2):
    ys = [v.y for v in LV if abs(v.x - xc) < dx and abs(v.z - zc) < dz]
    return min(ys) if ys else mnL.y
for nm_, (hx_, hz_) in (("HeadlampL", (-0.62, 1.35)), ("HeadlampR", (0.62, 1.35)), ("HeadlampTop", (0.0, (2.08 - low) * s + RAIL_H))):
    bmh = bmesh.new(); bmesh.ops.create_cone(bmh, cap_ends=True, segments=20, radius1=0.11, radius2=0.11, depth=0.04, matrix=Matrix.Rotation(math.radians(90), 4, 'X'))
    hl = mesh_obj(nm_, bmh, M_HEAD, "Train"); hl.location = (hx_, nose_y(hx_, hz_) - 0.025, hz_); hl.parent = TRAIN
for hx_ in (-0.55, 0.55):
    sl = bpy.data.lights.new("HeadSpot", 'SPOT'); sl.energy = 6000; sl.spot_size = math.radians(40); sl.color = (1, 0.92, 0.75); sl.shadow_soft_size = 0.1
    so = bpy.data.objects.new("HeadSpot%s" % ("L" if hx_ < 0 else "R"), sl); coll("Train").objects.link(so); so.parent = TRAIN
    so.location = (hx_, nose_y(hx_, 1.35) - 0.08, 1.35); so.rotation_euler = (math.radians(-85), 0, 0)    # beams forward along the track
sc["plough_tip"] = mnL.y          # the GP18's own pilot is the front-most part

# ---- suburban houses (CC-BY models) and platform street lamps (CC-BY)
def glb_asset(fname, name, target, axis="max", cname="Set"):
    ms_ = import_glb(os.path.join(GLB, fname))
    bpy.ops.object.select_all(action='DESELECT')
    for o in ms_: o.select_set(True)
    bpy.context.view_layer.objects.active = ms_[0]
    if len(ms_) > 1: bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active; o.name = name
    mn_, mx_ = bbox([o]); ext = mx_ - mn_
    sz = (max(ext.x, ext.y) if axis == "max" else ext.z)
    sc_ = target / sz
    o.data.transform(Matrix.Scale(sc_, 4) @ Matrix.Translation(-Vector(((mn_.x + mx_.x) / 2, (mn_.y + mx_.y) / 2, mn_.z))))
    link(o, "Hidden")
    return o
HOUSE_SRC = [glb_asset("houseA.glb", "HouseSrcA", 10.0), glb_asset("houseB.glb", "HouseSrcB", 11.0), glb_asset("houseC.glb", "HouseSrcC", 11.0)]
for i, yy in enumerate(range(-100, 130, 19)):
    src = HOUSE_SRC[i % 3]; o = src.copy(); o.name = "House%d" % i; coll("Set").objects.link(o)
    o.location = (21.0 + random.uniform(-1.5, 1.5), yy + random.uniform(-2, 2), -0.08); o.rotation_euler.z = math.radians(90 + random.choice((0, 180)) + random.uniform(-4, 4))
for i, yy in enumerate(range(-90, 120, 23)):
    src = HOUSE_SRC[(i + 1) % 3]; o = src.copy(); o.name = "HouseW%d" % i; coll("Set").objects.link(o)
    o.location = (-27.0 + random.uniform(-2, 2), yy, -0.08); o.rotation_euler.z = math.radians(-90 + random.choice((0, 180)) + random.uniform(-4, 4))
LAMP_SRC = glb_asset("streetlamp.glb", "LampSrc", 4.2, axis="z")
for yy in (-75, -62, -50):
    o = LAMP_SRC.copy(); o.name = "Lamp%d" % yy; coll("Set").objects.link(o); o.location = (6.9, yy, PLAT["h"]); o.rotation_euler.z = math.radians(90)
# ------------------------------------------------------------------ x-ray studio (cyan-to-white gradient cyclorama around the stop point)
SX, SY = 2.4, STOP_Y
M_CYC = bpy.data.materials.new("StudioCyc"); M_CYC.use_nodes = True
nn, ll = M_CYC.node_tree.nodes, M_CYC.node_tree.links
pc = nn["Principled BSDF"]; pc.inputs['Roughness'].default_value = 0.9
gtc = nn.new('ShaderNodeTexCoord'); gsep = nn.new('ShaderNodeSeparateXYZ'); ll.new(gtc.outputs['Generated'], gsep.inputs[0])
cr = nn.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (0.12, 0.55, 0.72, 1); cr.color_ramp.elements[1].color = (0.01, 0.035, 0.09, 1)
cr.color_ramp.elements[0].position = 0.08; cr.color_ramp.elements[1].position = 0.75
ll.new(gsep.outputs['Z'], cr.inputs['Fac']); ll.new(cr.outputs['Color'], pc.inputs['Base Color'])
pc.inputs['Emission Strength'].default_value = 0.5; ll.new(cr.outputs['Color'], pc.inputs['Emission Color'])
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=1.0)
for v_ in bm.verts:
    v_.co = Vector((v_.co.x * 12, v_.co.y * 12, max(v_.co.z, -0.0) * 9 - 0.03 if v_.co.z > 0 else -0.03))
bmesh.ops.reverse_faces(bm, faces=bm.faces)
cyc = mesh_obj("StudioCyc", bm, M_CYC, "Studio"); cyc.location = (SX, SY, 0)
for poly in cyc.data.polygons: poly.use_smooth = True
for k, (lx, ly, lz, e) in enumerate(((-3, -4, 5, 500), (5, 3, 4, 300), (0, 6, 6, 250))):
    ad = bpy.data.lights.new("StudioKey%d" % k, 'AREA'); ad.energy = e; ad.size = 3.0; ad.color = (0.95, 0.98, 1.0)
    ao = bpy.data.objects.new("StudioKey%d" % k, ad); coll("Studio").objects.link(ao); ao.location = (SX + lx, SY + ly, lz)
    ao.rotation_euler = (Vector((SX, SY, 1.0)) - ao.location).to_track_quat('-Z', 'Y').to_euler()

# ------------------------------------------------------------------ props
# unlabelled green glass bottle (lathe)
prof_b = [(0.0, 0.0), (0.034, 0.0), (0.036, 0.01), (0.036, 0.17), (0.03, 0.2), (0.014, 0.24), (0.013, 0.29), (0.015, 0.295), (0.0, 0.295)]
bm = bmesh.new()
rings = []
for r_, z_ in prof_b:
    rings.append([bm.verts.new((r_ * math.cos(a), r_ * math.sin(a), z_)) for a in [i * 2 * math.pi / 20 for i in range(20)]])
for r0, r1 in zip(rings, rings[1:]):
    for i in range(20):
        bm.faces.new((r0[i], r0[(i + 1) % 20], r1[(i + 1) % 20], r1[i]))
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
M_BOTTLE = bpy.data.materials.new("BottleGlass"); M_BOTTLE.use_nodes = True
pb_ = M_BOTTLE.node_tree.nodes["Principled BSDF"]; pb_.inputs['Base Color'].default_value = (0.12, 0.35, 0.12, 1)
pb_.inputs['Transmission Weight'].default_value = 0.9; pb_.inputs['Roughness'].default_value = 0.08; pb_.inputs['IOR'].default_value = 1.5
bottle = mesh_obj("Bottle", bm, M_BOTTLE, "Props")
for poly in bottle.data.polygons: poly.use_smooth = True
# hard hat (GLB), normalised to 0.30 m wide
hm = import_glb(os.path.join(GLB, "hardhat.glb"))[0]
hm.data.update(); mn_ = Vector([min(v_.co[i] for v_ in hm.data.vertices) for i in range(3)]); mx_ = Vector([max(v_.co[i] for v_ in hm.data.vertices) for i in range(3)]); s_ = 0.30 / max(mx_.x - mn_.x, mx_.y - mn_.y)
hm.data.transform(Matrix.Scale(s_, 4) @ Matrix.Translation(-Vector(((mn_.x + mx_.x) / 2, (mn_.y + mx_.y) / 2, mn_.z))))
hm.name = "HardHat"; link(hm, "Props")
hm.data.update(); bpy.context.view_layer.update(); print("HARDHAT dims", [round(v, 3) for v in hm.dimensions])

# ------------------------------------------------------------------ people: clothing recolours
def tint_by_saturation(mat, color, sat_lo=0.12, sat_hi=0.3, invert=False, mode='MULTIPLY'):
    """recolour only the (un)saturated parts of a clothes texture: white tee -> bright colour, blue denim kept"""
    nt_ = mat.node_tree
    for nd in list(nt_.nodes):
        if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
            for lk in list(nd.outputs['Color'].links):
                sh = nt_.nodes.new('ShaderNodeSeparateColor'); sh.mode = 'HSV'
                nt_.links.new(nd.outputs['Color'], sh.inputs[0])
                mr = nt_.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = sat_lo; mr.inputs['From Max'].default_value = sat_hi
                mr.inputs['To Min'].default_value = 0.0 if invert else 1.0; mr.inputs['To Max'].default_value = 1.0 if invert else 0.0
                nt_.links.new(sh.outputs[1], mr.inputs['Value'])
                mx_ = nt_.nodes.new('ShaderNodeMix'); mx_.data_type = 'RGBA'; mx_.blend_type = mode
                mx_.inputs['B'].default_value = color + (1,)
                nt_.links.new(mr.outputs['Result'], mx_.inputs['Factor']); nt_.links.new(nd.outputs['Color'], mx_.inputs['A'])
                nt_.links.new(mx_.outputs['Result'], lk.to_socket)
                return True
    return False

def tee_recolour(mat, color):
    """everything that is not blue denim becomes a flat bright colour (keeps only the cloth shading), so the printed logo disappears"""
    nt_ = mat.node_tree
    for nd in list(nt_.nodes):
        if nd.type == 'TEX_IMAGE' and nd.image and "diffuse" in nd.image.name.lower():
            for lk in list(nd.outputs['Color'].links):
                N_, L_ = nt_.nodes, nt_.links
                sh = N_.new('ShaderNodeSeparateColor'); sh.mode = 'HSV'; L_.new(nd.outputs['Color'], sh.inputs[0])
                hd = N_.new('ShaderNodeMath'); hd.operation = 'SUBTRACT'; hd.inputs[1].default_value = 0.6; L_.new(sh.outputs[0], hd.inputs[0])
                ha = N_.new('ShaderNodeMath'); ha.operation = 'ABSOLUTE'; L_.new(hd.outputs[0], ha.inputs[0])
                hb = N_.new('ShaderNodeMath'); hb.operation = 'LESS_THAN'; hb.inputs[1].default_value = 0.12; L_.new(ha.outputs[0], hb.inputs[0])
                sb = N_.new('ShaderNodeMath'); sb.operation = 'GREATER_THAN'; sb.inputs[1].default_value = 0.16; L_.new(sh.outputs[1], sb.inputs[0])
                bl = N_.new('ShaderNodeMath'); bl.operation = 'MULTIPLY'; L_.new(hb.outputs[0], bl.inputs[0]); L_.new(sb.outputs[0], bl.inputs[1])
                fac = N_.new('ShaderNodeMath'); fac.operation = 'SUBTRACT'; fac.inputs[0].default_value = 1.0; L_.new(bl.outputs[0], fac.inputs[1])
                vv = N_.new('ShaderNodeMapRange'); vv.inputs['To Min'].default_value = 0.93; vv.inputs['To Max'].default_value = 1.0
                vv.inputs['From Min'].default_value = 0.3; vv.inputs['From Max'].default_value = 0.9; L_.new(sh.outputs[2], vv.inputs['Value'])
                cm = N_.new('ShaderNodeMix'); cm.data_type = 'RGBA'; cm.blend_type = 'MULTIPLY'; cm.inputs['Factor'].default_value = 1.0
                cm.inputs['A'].default_value = color + (1,); L_.new(vv.outputs['Result'], cm.inputs['B'])
                mx_ = N_.new('ShaderNodeMix'); mx_.data_type = 'RGBA'
                L_.new(fac.outputs[0], mx_.inputs['Factor']); L_.new(nd.outputs['Color'], mx_.inputs['A']); L_.new(cm.outputs['Result'], mx_.inputs['B'])
                L_.new(mx_.outputs['Result'], lk.to_socket)
            return True

for o in bpy.data.objects:
    if o.type != 'MESH' or not o.data.materials: continue
    if o.name == "Lad.male_casualsuit06":
        tee_recolour(o.data.materials[0], (0.02, 0.62, 0.72))              # bright plain teal tee (logo removed), denim kept
    if o.name == "Worker.male_worksuit01":
        # blue overall -> fluorescent orange hi-vis, white tee kept
        m_ = o.data.materials[0]
        tint_by_saturation(m_, (1.0, 0.33, 0.02), sat_lo=0.18, sat_hi=0.35, invert=True, mode='COLOR')
    if o.name == "WitB.male_casualsuit03":
        tint_by_saturation(o.data.materials[0], (0.55, 0.42, 0.3), sat_lo=0.15, sat_hi=0.3, invert=True, mode='COLOR')

# Lad: denim jeans -> shorts. cut the trouser legs above the knee and un-hide the body below it
lad_clo = bpy.data.objects["Lad.male_casualsuit06"]; lad_body = bpy.data.objects["Lad.body"]
lad_rig = bpy.data.objects["Lad"]
KNEE_Z = lad_rig.data.bones["lowerleg01.L"].head_local.z + 0.09
bm = bmesh.new(); bm.from_mesh(lad_clo.data)
dl = [v_ for v_ in bm.verts if v_.co.z < KNEE_Z]
bmesh.ops.delete(bm, geom=dl, context='VERTS'); bm.to_mesh(lad_clo.data); bm.free()
vg = lad_body.vertex_groups.get("Delete.male_casualsuit06")
if vg:
    idx = [v_.index for v_ in lad_body.data.vertices if v_.co.z < KNEE_Z - 0.02]
    vg.remove(idx)
# the jeans' shoe-hiding group stays (shoes05 covers feet)
for o in bpy.data.objects:
    if o.type == 'ARMATURE': link(o, "People")
    elif o.parent and o.parent.type == 'ARMATURE': link(o, "People")

# palm cuts (three short clean scratches), parented later to the left hand
M_CUT = flat("Cut", (0.42, 0.05, 0.05), 0.35)
for k in range(3):
    c_ = box("PalmCut%d" % k, (0.028 - 0.005 * k, 0.0022, 0.0012), (0, 0, 0), M_CUT, "Props")
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "02b_fit_muscles.py")).read())
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SCENE_DONE", OUT)
