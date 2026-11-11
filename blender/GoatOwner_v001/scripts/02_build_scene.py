"""GoatOwner scene: render settings, world, farmyard, porch, truck, sanctuary pasture, characters.
blender -b humans.blend --python 02_build_scene.py -- <assets_root> <work_dir> <out.blend>
assets_root holds ph/ (Poly Haven) and objv/ (Objaverse GLBs); work_dir holds goat_rig.blend."""
import sys, os, math, random, glob
import bpy, bmesh
from mathutils import Vector, Matrix, noise

argv = sys.argv[sys.argv.index("--") + 1:]
A, W, OUT = argv[0], argv[1], argv[2]
PH, OB = os.path.join(A, "ph"), os.path.join(A, "objv")
sc = bpy.context.scene
FPS, END = 60, 2190
random.seed(32)

# ------------------------------------------------------------------ render
sc.render.fps, sc.render.fps_base = FPS, 1.0
sc.frame_start, sc.frame_end = 1, END
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.engine = 'CYCLES'
c = sc.cycles
c.device = 'CPU'; c.samples = 48; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.05
c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'
c.max_bounces = 8; c.diffuse_bounces = 3; c.glossy_bounces = 3; c.transmission_bounces = 8; c.transparent_max_bounces = 8
c.caustics_reflective = c.caustics_refractive = False
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.render.use_persistent_data = True
sc.display_settings.display_device = 'sRGB'
vs = sc.view_settings; vs.view_transform = 'AgX'; vs.look = 'AgX - Medium High Contrast'; vs.exposure = 0.0; vs.gamma = 1.0
im = sc.render.image_settings; im.file_format = 'PNG'; im.color_mode = 'RGB'; im.color_depth = '8'; im.compression = 15
sc.render.filepath = "//render/GoatOwner_"

# ------------------------------------------------------------------ helpers
def coll(name):
    c_ = bpy.data.collections.new(name); sc.collection.children.link(c_); return c_
SET, PROPS, ANIM, FX, SANCT = coll("Farm_Set"), coll("Props"), coll("Characters"), coll("FX"), coll("Sanctuary_Set")

def link(ob, col):
    for c_ in list(ob.users_collection): c_.objects.unlink(ob)
    col.objects.link(ob)

def img(path, nc=False):
    i = bpy.data.images.load(path, check_existing=True)
    if nc: i.colorspace_settings.name = 'Non-Color'
    return i

def phfile(aid, kind):
    fs = glob.glob(os.path.join(PH, aid, "**", "*_%s_1k.*" % kind), recursive=True)
    return fs[0] if fs else None

def pbr_nodes(n, l, aid, scale, sat=1.0, val=1.0, bump=1.0, hue=0.5, coord='Object', p=None):
    p = p or n.new('ShaderNodeBsdfPrincipled')
    tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / scale,) * 3
    l.new(tc.outputs[coord], mp.inputs['Vector'])
    d = n.new('ShaderNodeTexImage'); d.image = img(phfile(aid, "diff"))
    hsv = n.new('ShaderNodeHueSaturation'); hsv.inputs['Saturation'].default_value = sat; hsv.inputs['Value'].default_value = val
    hsv.inputs['Hue'].default_value = hue
    l.new(mp.outputs['Vector'], d.inputs['Vector']); l.new(d.outputs['Color'], hsv.inputs['Color']); l.new(hsv.outputs['Color'], p.inputs['Base Color'])
    rf = phfile(aid, "rough")
    if rf:
        r = n.new('ShaderNodeTexImage'); r.image = img(rf, True); l.new(mp.outputs['Vector'], r.inputs['Vector']); l.new(r.outputs['Color'], p.inputs['Roughness'])
    nf = phfile(aid, "nor_gl")
    if nf:
        nm = n.new('ShaderNodeTexImage'); nm.image = img(nf, True); nmap = n.new('ShaderNodeNormalMap'); nmap.inputs['Strength'].default_value = bump
        l.new(mp.outputs['Vector'], nm.inputs['Vector']); l.new(nm.outputs['Color'], nmap.inputs['Color']); l.new(nmap.outputs['Normal'], p.inputs['Normal'])
    return p

def pbr(name, aid, scale, **kw):
    m = bpy.data.materials.new(name); m.use_nodes = True
    pbr_nodes(m.node_tree.nodes, m.node_tree.links, aid, scale, p=m.node_tree.nodes["Principled BSDF"], **kw)
    return m

def import_glb(name, height=None, length=None, loc=(0, 0, 0), rot_z=0.0, col=None, fname=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(OB, (fname or name) + ".glb"))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o.type != 'MESH': bpy.data.objects.remove(o, do_unlink=True)
    for o in bpy.data.objects: o.select_set(False)
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(meshes) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active; ob.name = name
    pts = [Vector(v.co) for v in ob.data.vertices]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    dims = mx - mn
    s = height / dims.z if height else (length / max(dims.x, dims.y) if length else 1.0)
    ob.data.transform(Matrix.Translation(Vector((-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z))))
    ob.data.transform(Matrix.Scale(s, 4))
    ob.location = loc; ob.rotation_euler = (0, 0, rot_z)
    if col: link(ob, col)
    return ob

def inst(src, name, loc, rot_z=0.0, scale=1.0, col=None):
    o = bpy.data.objects.new(name, src.data); o.location = loc; o.rotation_euler = (0, 0, rot_z); o.scale = (scale,) * 3
    (col or SET).objects.link(o); return o

# ------------------------------------------------------------------ world (keyable sky)
w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
wn, wl = w.node_tree.nodes, w.node_tree.links; wn.clear()
tc = wn.new('ShaderNodeTexCoord')
mp = wn.new('ShaderNodeMapping'); mp.name = "SkyRot"; mp.inputs['Rotation'].default_value = (0, 0, math.radians(250))
sky = wn.new('ShaderNodeTexEnvironment'); sky.image = img(os.path.join(PH, "hdri/kloofendal_48d_partly_cloudy_puresky_2k.hdr"))
mp2 = wn.new('ShaderNodeMapping'); mp2.inputs['Rotation'].default_value = (0, 0, math.radians(300))
hor = wn.new('ShaderNodeTexEnvironment'); hor.image = img(os.path.join(PH, "hdri/hausdorf_meadow_2k.hdr"))
sep = wn.new('ShaderNodeSeparateXYZ')
band = wn.new('ShaderNodeMapRange'); band.inputs['From Min'].default_value = -2.0; band.inputs['From Max'].default_value = -1.0
mix = wn.new('ShaderNodeMix'); mix.data_type = 'RGBA'
tint = wn.new('ShaderNodeMix'); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'; tint.name = "SkyTint"
tint.inputs['Factor'].default_value = 1.0; tint.inputs['B'].default_value = (1.0, 0.95, 0.88, 1)
bg = wn.new('ShaderNodeBackground'); bg.name = "SkyStrength"; bg.inputs['Strength'].default_value = 0.9
out = wn.new('ShaderNodeOutputWorld')
for a_, b_ in ((tc.outputs['Generated'], mp.inputs['Vector']), (mp.outputs['Vector'], sky.inputs['Vector']),
               (tc.outputs['Generated'], mp2.inputs['Vector']), (mp2.outputs['Vector'], hor.inputs['Vector']),
               (tc.outputs['Generated'], sep.inputs['Vector']), (sep.outputs['Z'], band.inputs['Value']),
               (band.outputs['Result'], mix.inputs['Factor']), (hor.outputs['Color'], mix.inputs['A']), (sky.outputs['Color'], mix.inputs['B']),
               (mix.outputs['Result'], tint.inputs['A']), (tint.outputs['Result'], bg.inputs['Color']), (bg.outputs['Background'], out.inputs['Surface'])):
    wl.new(a_, b_)
sun = bpy.data.objects.new("Key_Sun", bpy.data.lights.new("Key_Sun", 'SUN'))
sun.data.energy = 3.6; sun.data.angle = math.radians(2.0); sun.data.color = (1.0, 0.93, 0.84)
sun.rotation_euler = (math.radians(52), 0, math.radians(-35))
sc.collection.objects.link(sun)

# ------------------------------------------------------------------ ground: dirt yard blending into grass; hills far away
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=240, y_segments=300, size=1.0)
YARD = [Vector((1.5, 3.0)), Vector((4.0, 9.0))]           # flat action zones (ground_z = 0)
PAST = Vector((2.0, 62.0))
for v in bm.verts:
    x, y = v.co.x * 120.0, v.co.y * 150.0 + 40.0
    d = min(min((Vector((x, y)) - p).length for p in YARD) - 12.0, (Vector((x, y)) - PAST).length - 14.0)
    d = max(0.0, d)
    lane = max(0.0, 1.0 - abs(x - 1.5) / 5.0) if 14 < y < 50 else 0.0       # the lane to the pasture stays flatter
    h = (noise.fractal(Vector((x * 0.025, y * 0.025, 0.2)), 0.6, 2.0, 4) * 3.0 + 0.04 * d) * min(1.0, d / 25.0) * (1 - 0.8 * lane)
    h += noise.noise(Vector((x * 0.7, y * 0.7, 3.1))) * 0.025 * min(1.0, d / 3.0)
    v.co = Vector((x, y, h))
gm_ = bpy.data.meshes.new("Ground"); bm.to_mesh(gm_); bm.free()
for p_ in gm_.polygons: p_.use_smooth = True
ground = bpy.data.objects.new("Ground", gm_); SET.objects.link(ground)
m_g = bpy.data.materials.new("M_Ground"); m_g.use_nodes = True
gn, gl = m_g.node_tree.nodes, m_g.node_tree.links; gn.remove(gn["Principled BSDF"]); o_ = gn["Material Output"]
pd = pbr_nodes(gn, gl, "brown_mud_leaves_01", 1.6, sat=0.55, val=0.8, bump=1.2, hue=0.505)
pg = pbr_nodes(gn, gl, "aerial_grass_rock", 3.0, sat=1.35, val=0.62, hue=0.54)
class _O: pass
sh_d, sh_g = _O(), _O(); sh_d.outputs = [pd.outputs[0]]; sh_g.outputs = [pg.outputs[0]]
tco = gn.new('ShaderNodeTexCoord'); sepg = gn.new('ShaderNodeSeparateXYZ')
gl.new(tco.outputs['Object'], sepg.inputs['Vector'])
# mask = grass where far from yard centre (radius ~11 m, noisy edge) or at the pasture
dist = gn.new('ShaderNodeVectorMath'); dist.operation = 'DISTANCE'; dist.inputs[1].default_value = (2.5, 5.0, 0)
gl.new(tco.outputs['Object'], dist.inputs[0])
nz = gn.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.35; gl.new(tco.outputs['Object'], nz.inputs['Vector'])
addn = gn.new('ShaderNodeMath'); addn.operation = 'MULTIPLY_ADD'; addn.inputs[1].default_value = 6.0; addn.inputs[2].default_value = -3.0
gl.new(nz.outputs['Fac'], addn.inputs[0])
sm = gn.new('ShaderNodeMath'); sm.operation = 'ADD'; gl.new(dist.outputs['Value'], sm.inputs[0]); gl.new(addn.outputs[0], sm.inputs[1])
mr = gn.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 9.0; mr.inputs['From Max'].default_value = 13.0
gl.new(sm.outputs[0], mr.inputs['Value'])
mixs = gn.new('ShaderNodeMixShader'); gl.new(mr.outputs['Result'], mixs.inputs['Fac'])
gl.new(sh_d.outputs[0], mixs.inputs[1]); gl.new(sh_g.outputs[0], mixs.inputs[2]); gl.new(mixs.outputs[0], o_.inputs['Surface'])
ground.data.materials.append(m_g)

# ------------------------------------------------------------------ buildings and props (real models)
house = import_glb("house", height=8.5, loc=(10.6, 6.0, 0), rot_z=math.radians(-90), col=SET)
shed = import_glb("shed2", height=3.2, loc=(-4.4, 5.0, 0), rot_z=math.radians(90), col=SET); shed.name = "Shed"
junk = import_glb("tires_shed", length=9.0, loc=(-11.0, 13.0, 0), rot_z=math.radians(140), col=SET)
truck = import_glb("truck", length=5.4, loc=(-1.5, 13.6, 0), rot_z=0.0, col=PROPS)
truck.data.transform(Matrix.Rotation(math.pi, 4, "Z"))
crate = import_glb("crate", height=0.55, loc=(-2.6, 2.6, 0), rot_z=0.3, col=SET)
inst(crate, "Crate_2", (-2.9, 3.4, 0), 1.2); inst(crate, "Crate_3", (8.9, 9.6, 0), 0.5)
fence = import_glb("fence", length=4.2, loc=(0, -6.0, 0), col=SET)
for i, (x, y, r) in enumerate([(-4.2, -6.1, 0.03), (4.3, -5.9, -0.04), (8.4, -5.6, -0.12), (-8.3, -6.0, 0.05),
                              (-10.6, -2.0, 1.57), (-10.6, 2.2, 1.6), (-10.5, 6.4, 1.55)]):
    inst(fence, "Fence_%d" % i, (x, y, 0), r)
stick = import_glb("stick2", length=0.95, col=PROPS); stick.name = "Stick"
stick.data.transform(Matrix.Diagonal((1, 0.4, 0.4, 1)))
post = import_glb("stick2", length=1.2, col=SET, fname="stick2"); post.name = "TetherPost"
post.data.transform(Matrix.Rotation(math.radians(90), 4, 'Y')); post.data.transform(Matrix.Rotation(math.radians(90), 4, 'X'))
_pz = min(v.co.z for v in post.data.vertices); post.data.transform(Matrix.Translation((0, 0, -_pz)))
post.location = (-1.2, 2.0, -0.15)
# Poly Haven models: trees, grass clumps, dry branches, rocks
def ph_blend(aid):
    fs = glob.glob(os.path.join(PH, aid, "*.blend"))
    with bpy.data.libraries.load(fs[0], link=False) as (src, dst):
        dst.objects = list(src.objects)
    return [o for o in dst.objects if o and o.type == 'MESH']
trees = [o for o in ph_blend("tree_small_02") if o.name.endswith("LOD0") and "leaves" not in o.name]
grass = [o for o in ph_blend("grass_medium_01") if o.name.endswith("LOD1") and "tiny" not in o.name]
branches = ph_blend("dry_branches_medium_01")
rocks = [o for o in ph_blend("rock_moss_set_01") if "LOD1" not in o.name and "LOD2" not in o.name]
print("PH", [o.name for o in trees], len(grass), [o.name for o in rocks])
TREES = []
for i in range(70):
    # tree line between the farm and the pasture plus a few around the yard
    if i < 18:
        x, y = random.uniform(-25, 28), random.uniform(28, 40)
        if abs(x - 1.5) < 3.5: x += 7 * (1 if x > 1.5 else -1)
    elif i < 26:
        x, y = [(-16, 4), (-14, 18), (17, -2), (19, 14), (-18, -8), (16, 24), (-7, 22), (24, 6)][i - 18]
    else:
        a_ = random.uniform(0, 6.28); r_ = random.uniform(28, 70); x, y = 2 + r_ * math.cos(a_), 20 + r_ * math.sin(a_)
        if abs(x - 2) < 20 and 45 < y < 80: x += 26 * (1 if x > 2 else -1)
    src = random.choice(trees)
    t = inst(src, "Tree_%d" % i, (x, y, -0.05), random.uniform(0, 6.28), random.uniform(1.6, 2.6)); TREES.append(t)
    hit, loc, nrm, idx = ground.ray_cast(Vector((x, y, 50)), Vector((0, 0, -1))); t.location.z = (loc.z if hit else 0) - 0.08
def scatter(srcs, n, area, name, scl=(0.8, 1.3), avoid=None, col=None):
    out_ = []
    for i in range(n):
        for _ in range(20):
            x, y = random.uniform(area[0], area[1]), random.uniform(area[2], area[3])
            if not avoid or not avoid(x, y): break
        out_.append(inst(random.choice(srcs), "%s_%d" % (name, i), (x, y, 0), random.uniform(0, 6.28), random.uniform(*scl), col))
    return out_
def yard_core(x, y):
    return (Vector((x, y)) - Vector((2.0, 3.5))).length < 7.5
GRC = bpy.data.collections.new("GrassClumps")
for g_ in grass: GRC.objects.link(g_)
def grass_patch(name, cx, cy, sx, sy, count, inner=None, col=SET, scl=2.2):
    bm_ = bmesh.new(); bmesh.ops.create_grid(bm_, x_segments=60, y_segments=60, size=1.0)
    me_ = bpy.data.meshes.new(name); bm_.to_mesh(me_); bm_.free()
    o = bpy.data.objects.new(name, me_); col.objects.link(o)
    vg = o.vertex_groups.new(name="dens")
    for v in me_.vertices:
        x, y = cx + v.co.x * sx, cy + v.co.y * sy
        hit, loc, nrm, idx = ground.ray_cast(Vector((x, y, 50)), Vector((0, 0, -1)))
        v.co = Vector((x, y, (loc.z if hit else 0) + 0.003))
        wgt = 1.0
        if inner: wgt = max(0.0, min(1.0, ((Vector((x, y)) - Vector(inner[:2])).length - inner[2]) / 2.5))
        wgt *= 0.35 + 0.65 * max(0, noise.noise(Vector((x * 0.3, y * 0.3, 0.5))) + 0.5)
        vg.add([v.index], max(0.0, min(1.0, wgt)), 'REPLACE')
    ps = o.modifiers.new("grass", 'PARTICLE_SYSTEM').particle_system; st = ps.settings
    st.type = 'HAIR'; st.count = count; st.use_advanced_hair = True; st.render_type = 'COLLECTION'; st.instance_collection = GRC
    st.use_collection_pick_random = True; st.particle_size = scl; st.size_random = 0.5; st.hair_length = 1.0
    st.use_rotations = True; st.rotation_mode = 'OB_Z'; st.phase_factor_random = 2.0; st.use_rotation_instance = False
    ps.vertex_group_density = "dens"; ps.seed = random.randint(0, 999)
    o.show_instancer_for_render = False
    return o
grass_patch("GrassPatch_Yard", 2.0, 8.0, 22, 22, 40000, inner=(2.0, 3.5, 8.5))
grass_patch("GrassPatch_Lane", 2.0, 34.0, 26, 14, 25000)
grass_patch("GrassPatch_Pasture", 2.0, 62.0, 22, 16, 60000, col=SANCT, scl=2.6)
scatter(branches, 10, (-9, 9, -4, 9), "Branch", scl=(0.6, 1.0), avoid=lambda x, y: (Vector((x, y)) - Vector((2, 2.5))).length < 3.5)
scatter(rocks, 14, (-12, 14, -7, 20), "Rock", scl=(0.4, 0.9), avoid=yard_core)
for o in list(trees) + list(branches) + list(rocks):
    if o.users_collection: [c_.objects.unlink(o) for c_ in o.users_collection]

# ------------------------------------------------------------------ porch: individual weathered boards on posts (x 5..7, y 3..9, deck z 0.75)
m_plank = pbr("M_Planks", "wood_planks_grey", 1.2, sat=0.8, val=0.85, bump=1.5)
PORCH = dict(x0=5.0, x1=7.2, y0=3.0, y1=9.0, z=0.75)
sc["porch"] = [PORCH[k] for k in ("x0", "x1", "y0", "y1", "z")]
def board(name, c_, size, rot=(0, 0, 0)):
    bm_ = bmesh.new(); bmesh.ops.create_cube(bm_, size=1.0)
    for v in bm_.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    bmesh.ops.bevel(bm_, geom=bm_.edges[:], offset=0.006, segments=2, affect='EDGES')
    me_ = bpy.data.meshes.new(name); bm_.to_mesh(me_); bm_.free()
    o = bpy.data.objects.new(name, me_); o.location = c_; o.rotation_euler = rot; SET.objects.link(o)
    me_.materials.append(m_plank)
    # warp and grain: small displace
    tx = bpy.data.textures.get("T_Warp") or bpy.data.textures.new("T_Warp", 'CLOUDS'); tx.noise_scale = 0.4
    sub = o.modifiers.new("sub", 'SUBSURF'); sub.levels = sub.render_levels = 1; sub.subdivision_type = 'SIMPLE'
    d = o.modifiers.new("warp", 'DISPLACE'); d.texture = tx; d.strength = 0.006; d.texture_coords = 'GLOBAL'
    return o
nb = int((PORCH["y1"] - PORCH["y0"]) / 0.145)
for i in range(nb):
    y = PORCH["y0"] + 0.0725 + i * 0.145
    board("Deck_%02d" % i, (6.1 + random.uniform(-0.01, 0.01), y, PORCH["z"] - 0.016),
          (2.2 + random.uniform(-0.03, 0.03), 0.135, 0.032), (random.uniform(-0.01, 0.01), 0, random.uniform(-0.006, 0.006)))
for j, (x, y) in enumerate([(5.06, 3.06), (5.06, 8.94), (7.1, 3.06), (7.1, 8.94), (5.06, 5.2), (5.06, 6.8)]):
    board("PorchPost_%d" % j, (x, y, 1.6), (0.11, 0.11, 3.2))
for j, (y0, y1) in enumerate([(3.06, 5.2), (6.8, 8.94)]):
    board("Rail_%d" % j, (5.06, (y0 + y1) / 2, PORCH["z"] + 0.9), (0.06, y1 - y0, 0.09))
    for k in range(int((y1 - y0) / 0.32)):
        board("Spindle_%d_%d" % (j, k), (5.06, y0 + 0.16 + k * 0.32, PORCH["z"] + 0.45), (0.04, 0.04, 0.88))
board("Rail_side", (6.1, 3.06, PORCH["z"] + 0.9), (2.1, 0.06, 0.09))   # the side the goat knocks him over (broken: shorter)
STEPS = []
for k in range(3):      # three steps going down toward -X, between y 5.2 and 6.8
    zt = PORCH["z"] - 0.25 * (k + 1) + 0.25
    xs = PORCH["x0"] - 0.3 * (k + 1) + 0.15
    board("Step_%d" % k, (xs, 6.0, zt - 0.02), (0.3, 1.5, 0.04))
    board("Riser_%d" % k, (xs + 0.14, 6.0, zt - 0.14), (0.03, 1.5, 0.22))
    STEPS.append([xs - 0.15, xs + 0.15, zt])
sc["steps"] = STEPS
board("Stringer_L", (4.55, 5.27, 0.37), (1.05, 0.05, 0.22), (0, math.radians(35), 0))
board("Stringer_R", (4.55, 6.73, 0.37), (1.05, 0.05, 0.22), (0, math.radians(35), 0))
board("PorchSkirt", (5.03, 6.0, 0.36), (0.03, 6.0, 0.7))
board("PorchSkirt_S", (6.1, 3.03, 0.36), (2.2, 0.03, 0.7))
board("PorchRoof", (6.1, 6.0, 3.25), (2.6, 6.4, 0.08), (0, math.radians(-8), 0))

# ------------------------------------------------------------------ truck ramp + police tape posts
board("Ramp", (-1.5, 9.6, 0.42), (0.9, 2.2, 0.05), (math.radians(-21), 0, 0))
sc["ramp"] = [-1.5, 8.55, 10.65, 0.0, 0.84]
tape_m = bpy.data.materials.new("M_Tape"); tape_m.use_nodes = True
tp = tape_m.node_tree.nodes["Principled BSDF"]; tp.inputs['Base Color'].default_value = (0.85, 0.62, 0.04, 1); tp.inputs['Roughness'].default_value = 0.45
TAPE_POSTS = [Vector(p) for p in ((3.8, 0.2), (8.6, 0.4), (8.4, 4.0), (3.6, 3.8))]
for i, p in enumerate(TAPE_POSTS):
    q = inst(post, "TapePost_%d" % i, (p.x, p.y, -0.15), random.uniform(0, 6))
    q.scale = (0.8, 0.8, 0.8)
tapes = []
for i in range(4):
    a, b = TAPE_POSTS[i], TAPE_POSTS[(i + 1) % 4]
    segs = 24
    bm_ = bmesh.new()
    vv = []
    for k in range(segs + 1):
        t = k / segs; p = a.lerp(b, t)
        sag = 0.12 * math.sin(math.pi * t)
        for side in (-1, 1):
            vv.append(bm_.verts.new((p.x, p.y, 0.78 - sag + side * 0.025)))
    for k in range(segs):
        bm_.faces.new((vv[2 * k], vv[2 * k + 1], vv[2 * k + 3], vv[2 * k + 2]))
    me_ = bpy.data.meshes.new("Tape_%d" % i); bm_.to_mesh(me_); bm_.free()
    o = bpy.data.objects.new("Tape_%d" % i, me_); PROPS.objects.link(o); me_.materials.append(tape_m)
    tx = bpy.data.textures.new("T_Flutter_%d" % i, 'CLOUDS'); tx.noise_scale = 0.35
    e = bpy.data.objects.new("TapeWind_%d" % i, None); FX.objects.link(e)
    d = o.modifiers.new("flutter", 'DISPLACE'); d.texture = tx; d.texture_coords = 'OBJECT'; d.texture_coords_object = e; d.strength = 0.07
    d.direction = 'Y' if abs(a.x - b.x) > abs(a.y - b.y) else 'X'
    tapes.append(o)
sc["tape_posts"] = [tuple(p) for p in TAPE_POSTS]

# ------------------------------------------------------------------ characters
with bpy.data.libraries.load(os.path.join(W, "goat_rig.blend"), link=False) as (src, dst):
    dst.objects = [n for n in src.objects if n.startswith("Goat")]
for o in dst.objects: ANIM.objects.link(o)
for o in bpy.data.objects:
    if o.type == 'ARMATURE' or (o.parent and o.parent.type == 'ARMATURE'):
        if o.name not in ANIM.objects: link(o, ANIM)
goat = bpy.data.objects["Goat_rig"]
# pasture goats: copies with their own armatures (body data shared)
gbody = [o for o in goat.children if o.type == 'MESH'][0]
for i in range(3):
    r2 = goat.copy(); r2.data = goat.data.copy(); r2.name = "PGoat_%d_rig" % i; SANCT.objects.link(r2)
    b2 = gbody.copy(); b2.name = "PGoat_%d_body" % i; b2.parent = r2; SANCT.objects.link(b2)
    for m in b2.modifiers:
        if m.type == 'ARMATURE': m.object = r2
# rope: tether post -> goat neck (curve hooked to two empties)
rope_m = bpy.data.materials.new("M_Rope"); rope_m.use_nodes = True
rn, rl = rope_m.node_tree.nodes, rope_m.node_tree.links
rp = rn["Principled BSDF"]; rp.inputs['Roughness'].default_value = 0.9
wv = rn.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 60; wv.inputs['Distortion'].default_value = 2; wv.bands_direction = 'DIAGONAL'
cr = rn.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (0.18, 0.13, 0.08, 1); cr.color_ramp.elements[1].color = (0.45, 0.36, 0.22, 1)
rl.new(wv.outputs['Fac'], cr.inputs['Fac']); rl.new(cr.outputs['Color'], rp.inputs['Base Color'])
bmp = rn.new('ShaderNodeBump'); bmp.inputs['Strength'].default_value = 0.6; rl.new(wv.outputs['Fac'], bmp.inputs['Height']); rl.new(bmp.outputs['Normal'], rp.inputs['Normal'])
cu = bpy.data.curves.new("Rope", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.009; cu.bevel_resolution = 3
spl = cu.splines.new('BEZIER'); spl.bezier_points.add(2)
rope = bpy.data.objects.new("Rope", cu); PROPS.objects.link(rope); cu.materials.append(rope_m)
for i, nm in enumerate(("RopeA", "RopeMid", "RopeB")):
    e = bpy.data.objects.new(nm, None); e.empty_display_size = 0.05; FX.objects.link(e)
    spl.bezier_points[i].handle_left_type = spl.bezier_points[i].handle_right_type = 'AUTO'
    h = rope.modifiers.new("hook_" + nm, 'HOOK'); h.object = e
    h.vertex_indices_set([i * 3, i * 3 + 1, i * 3 + 2])

# ------------------------------------------------------------------ dust: a pool of small rough clods + soft dust puffs (keyed later)
m_dust = bpy.data.materials.new("M_DustPuff"); m_dust.use_nodes = True
dn, dl_ = m_dust.node_tree.nodes, m_dust.node_tree.links; dn.remove(dn["Principled BSDF"])
vol = dn.new('ShaderNodeVolumePrincipled'); vol.inputs['Color'].default_value = (0.55, 0.45, 0.33, 1); vol.inputs['Density'].default_value = 1.2
nzd = dn.new('ShaderNodeTexNoise'); nzd.inputs['Scale'].default_value = 3.0; nzd.inputs['Detail'].default_value = 6
mrd = dn.new('ShaderNodeMapRange'); mrd.inputs['From Min'].default_value = 0.45; mrd.inputs['From Max'].default_value = 0.75
gr = dn.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'
mul = dn.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
dens = dn.new('ShaderNodeValue'); dens.name = "Dens"; dens.outputs[0].default_value = 1.0
mul2 = dn.new('ShaderNodeMath'); mul2.operation = 'MULTIPLY'
tcd = dn.new('ShaderNodeTexCoord')
dl_.new(tcd.outputs['Object'], nzd.inputs['Vector']); dl_.new(tcd.outputs['Object'], gr.inputs['Vector'])
dl_.new(nzd.outputs['Fac'], mrd.inputs['Value']); dl_.new(mrd.outputs['Result'], mul.inputs[0]); dl_.new(gr.outputs['Fac'], mul.inputs[1])
dl_.new(mul.outputs[0], mul2.inputs[0]); dl_.new(dens.outputs[0], mul2.inputs[1]); dl_.new(mul2.outputs[0], vol.inputs['Density'])
dl_.new(vol.outputs[0], dn["Material Output"].inputs['Volume'])
sc["n_puffs"] = 10
for i in range(10):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=(0, 0, -20))
    o = bpy.context.active_object; o.name = "DustPuff_%d" % i; link(o, FX)
    md = m_dust.copy(); md.name = "M_DustPuff_%d" % i; o.data.materials.append(md)
m_clod = pbr("M_Clod", "brown_mud_leaves_01", 0.3, sat=0.7, val=0.7)
for i in range(40):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=(0, 0, -20))
    o = bpy.context.active_object; o.name = "Clod_%02d" % i; link(o, FX)
    for v in o.data.vertices: v.co *= 1 + 0.35 * noise.noise(v.co * 2.3 + Vector((i, 0, 0)))
    o.data.materials.append(m_clod); o.scale = (0.018,) * 3

# ------------------------------------------------------------------ camera
cam = bpy.data.objects.new("CAM_Film", bpy.data.cameras.new("CAM_Film")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 30; cam.data.sensor_fit = 'AUTO'; cam.data.clip_start = 0.02; cam.data.clip_end = 400
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 4.0
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
print("SCENE objects", len(bpy.data.objects), "goat", goat.name, "porch", sc["porch"])
bpy.ops.wm.save_as_mainfile(filepath=OUT)
