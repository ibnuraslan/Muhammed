"""TitanicIceberg scene: timeline, render settings, ocean, iceberg, steamship deck, debris, ghost liner,
rooms hidden inside the iceberg (darkroom, office, explainer cyc), lights.
blender -b humans.blend --python 02_build_scene.py -- <assets_dir> <out.blend>
assets_dir holds glb/ (find_models.py), hdri/ and Poly Haven texture folders (fetch_polyhaven.py)."""
import sys, os, math, random, glob
import bpy, bmesh
from mathutils import Vector, Matrix, noise, Euler

argv = sys.argv[sys.argv.index("--") + 1:]
A, OUT = argv[0], argv[1]
sc = bpy.context.scene
FPS, END = 60, 1830
R_ = math.radians
random.seed(35)

# ---------------------------------------------------------------- timeline / render
sc.render.fps, sc.render.fps_base = FPS, 1.0
sc.frame_start, sc.frame_end = 0, END
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.engine = 'CYCLES'
c = sc.cycles
c.device = 'CPU'; c.samples = 48; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.05
c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'
c.max_bounces = 8; c.diffuse_bounces = 3; c.glossy_bounces = 3; c.transmission_bounces = 6; c.volume_bounces = 1
c.caustics_reflective = c.caustics_refractive = False
c.transparent_max_bounces = 64
c.volume_step_rate = 4.0
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.render.use_persistent_data = True
sc.display_settings.display_device = 'sRGB'
vs = sc.view_settings; vs.view_transform = 'AgX'; vs.look = 'AgX - Medium High Contrast'
im = sc.render.image_settings; im.file_format = 'PNG'; im.color_mode = 'RGB'; im.color_depth = '8'
sc.render.filepath = "//render/TitanicIceberg_"

def coll(name):
    c_ = bpy.data.collections.new(name); sc.collection.children.link(c_); return c_
C_OCEAN, C_SHIP, C_DEBRIS, C_GHOST, C_ROOMS, C_CYC, C_FX = [coll(n) for n in
    ("Ocean_Set", "Steamship", "Debris", "Ghost_Liner", "Rooms_In_Berg", "Explainer_Cyc", "FX")]
for o in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
    pass

def link(ob, col):
    for c_ in list(ob.users_collection): c_.objects.unlink(ob)
    col.objects.link(ob); return ob

def img(path, nc=False):
    i = bpy.data.images.load(path, check_existing=True)
    if nc: i.colorspace_settings.name = 'Non-Color'
    return i

def tex_files(tid):
    d = os.path.join(A, tid, "textures") if os.path.isdir(os.path.join(A, tid, "textures")) else os.path.join(A, tid)
    g = lambda k: (glob.glob(os.path.join(d, f"*_{k}_*")) or [None])[0]
    return g("diff"), g("nor_gl"), g("rough"), g("disp")

def pbr(name, tid, scale, tint=None, bump=1.0, rough_mul=1.0, coord='Object', disp=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links; p = n["Principled BSDF"]
    df, nf, rf, dsf = tex_files(tid)
    tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / scale,) * 3
    l.new(tc.outputs[coord], mp.inputs['Vector'])
    def T(f, nc):
        t = n.new('ShaderNodeTexImage'); t.image = img(f, nc); t.projection = 'BOX' if coord == 'Object' else 'FLAT'
        t.projection_blend = 0.2; l.new(mp.outputs['Vector'], t.inputs['Vector']); return t
    d = T(df, False); col = d.outputs['Color']
    if tint:
        mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1
        mx.inputs['B'].default_value = (*tint, 1); l.new(col, mx.inputs['A']); col = mx.outputs['Result']
    l.new(col, p.inputs['Base Color'])
    if rf:
        r = T(rf, True); rm = n.new('ShaderNodeMath'); rm.operation = 'MULTIPLY'; rm.inputs[1].default_value = rough_mul; rm.use_clamp = True
        l.new(r.outputs['Color'], rm.inputs[0]); l.new(rm.outputs[0], p.inputs['Roughness'])
    if nf:
        nm = T(nf, True); nmap = n.new('ShaderNodeNormalMap'); nmap.inputs['Strength'].default_value = bump
        l.new(nm.outputs['Color'], nmap.inputs['Color']); l.new(nmap.outputs['Normal'], p.inputs['Normal'])
    return m

def mat_simple(name, rgb, rough=0.5, metal=0.0, emit=None, es=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*rgb, 1); p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    if emit: p.inputs['Emission Color'].default_value = (*emit, 1); p.inputs['Emission Strength'].default_value = es
    return m

def import_glb(name, length=None, height=None, col=None, keep_mats=True):
    path = os.path.join(A, "glb", name + ".glb")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
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
    pts = [v.co for v in ob.data.vertices]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    dims = mx - mn; s = 1.0
    if height: s = height / dims.z
    elif length: s = length / max(dims.x, dims.y)
    ob.data.transform(Matrix.Translation(Vector((-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z))))
    ob.data.transform(Matrix.Scale(s, 4))
    if col: link(ob, col)
    return ob

def box(name, size, loc, mat=None, col=None, bevel=0.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    bm.to_mesh(me); bm.free(); ob = bpy.data.objects.new(name, me); ob.location = loc
    (col or sc.collection).objects.link(ob)
    if mat: me.materials.append(mat)
    if bevel:
        b = ob.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = 2
    return ob

# ---------------------------------------------------------------- world (dawn / night / navy blend, keyable)
w = bpy.data.worlds.new("World_Atlantic"); sc.world = w; w.use_nodes = True
wn, wl = w.node_tree.nodes, w.node_tree.links; wn.clear()
tc = wn.new('ShaderNodeTexCoord'); mp = wn.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (0, 0, R_(200))
wl.new(tc.outputs['Generated'], mp.inputs['Vector'])
dawn = wn.new('ShaderNodeTexEnvironment'); dawn.image = img(os.path.join(A, "hdri/kloofendal_48d_partly_cloudy_puresky_2k.hdr"))
night = wn.new('ShaderNodeTexEnvironment'); night.image = img(os.path.join(A, "hdri/qwantani_night_puresky_2k.hdr"))
for t in (dawn, night): wl.new(mp.outputs['Vector'], t.inputs['Vector'])
dsat = wn.new('ShaderNodeHueSaturation'); dsat.inputs['Saturation'].default_value = 1.15; dsat.inputs['Value'].default_value = 1.0
wl.new(dawn.outputs['Color'], dsat.inputs['Color'])
nmul = wn.new('ShaderNodeMix'); nmul.data_type = 'RGBA'; nmul.blend_type = 'MULTIPLY'; nmul.inputs['Factor'].default_value = 1
nmul.inputs['B'].default_value = (0.1, 0.18, 0.45, 1); wl.new(night.outputs['Color'], nmul.inputs['A'])
mixDN = wn.new('ShaderNodeMix'); mixDN.data_type = 'RGBA'; mixDN.name = "DayNight"
wl.new(dsat.outputs['Color'], mixDN.inputs['A']); wl.new(nmul.outputs['Result'], mixDN.inputs['B'])
bg = wn.new('ShaderNodeBackground'); bg.name = "SkyStrength"; bg.inputs['Strength'].default_value = 1.6
wl.new(mixDN.outputs['Result'], bg.inputs['Color'])
out = wn.new('ShaderNodeOutputWorld'); wl.new(bg.outputs['Background'], out.inputs['Surface'])

sun = bpy.data.objects.new("Key_Sun", bpy.data.lights.new("Key_Sun", 'SUN'))
sun.data.energy = 4.0; sun.data.angle = R_(4); sun.data.color = (1.0, 0.95, 0.88)
sun.rotation_euler = (R_(48), 0, R_(25)); link(sun, C_OCEAN) if False else sc.collection.objects.link(sun)
moon = bpy.data.objects.new("Moon_Key", bpy.data.lights.new("Moon_Key", 'SUN'))
moon.data.energy = 0.0; moon.data.angle = R_(1); moon.data.color = (0.55, 0.68, 1.0)
moon.rotation_euler = (R_(62), 0, R_(15)); sc.collection.objects.link(moon)

# ---------------------------------------------------------------- ocean
bpy.ops.mesh.primitive_plane_add(size=2, location=(0, -40, 0)); sea = bpy.context.object; sea.name = "Ocean"; link(sea, C_OCEAN)
om = sea.modifiers.new("Ocean", 'OCEAN'); om.geometry_mode = 'GENERATE'; om.size = 1.0; om.spatial_size = 120
om.repeat_x = om.repeat_y = 2; om.resolution = 11; om.wave_scale = 0.9; om.choppiness = 1.1; om.wind_velocity = 9
om.use_foam = True; om.foam_layer_name = "foam"; om.foam_coverage = 0.05; om.wave_alignment = 0.4; om.random_seed = 3
om.time = 1.0
fc = om.driver_add("time"); fc.driver.expression = "1 + frame / 60"
sea.data.polygons.foreach_set("use_smooth", [True] * len(sea.data.polygons))
wm = bpy.data.materials.new("M_Sea"); wm.use_nodes = True; n, l = wm.node_tree.nodes, wm.node_tree.links
p = n["Principled BSDF"]; p.inputs['Base Color'].default_value = (0.01, 0.07, 0.17, 1); p.inputs['Roughness'].default_value = 0.08
p.inputs['IOR'].default_value = 1.333
at = n.new('ShaderNodeAttribute'); at.attribute_name = "foam"; fr = n.new('ShaderNodeMapRange'); fr.inputs['From Min'].default_value = 0.35
fr.inputs['From Max'].default_value = 1.0
nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 14; nz.inputs['Detail'].default_value = 8
fm = n.new('ShaderNodeMath'); fm.operation = 'MULTIPLY'
l.new(at.outputs['Fac'], fr.inputs['Value']); l.new(fr.outputs['Result'], fm.inputs[0]); l.new(nz.outputs['Fac'], fm.inputs[1])
foam = n.new('ShaderNodeBsdfPrincipled'); foam.inputs['Base Color'].default_value = (0.75, 0.8, 0.82, 1); foam.inputs['Roughness'].default_value = 0.7
mx = n.new('ShaderNodeMixShader'); l.new(fm.outputs[0], mx.inputs['Fac']); l.new(p.outputs[0], mx.inputs[1]); l.new(foam.outputs[0], mx.inputs[2])
bmp = n.new('ShaderNodeBump'); bmp.inputs['Strength'].default_value = 0.15; nz2 = n.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = 40
l.new(nz2.outputs['Fac'], bmp.inputs['Height']); l.new(bmp.outputs['Normal'], p.inputs['Normal'])
l.new(mx.outputs[0], n["Material Output"].inputs['Surface'])
sea.data.materials.append(wm)
# far sea skirt (flat) out to the fog
bpy.ops.mesh.primitive_plane_add(size=3000, location=(0, 0, -0.05)); far = bpy.context.object; far.name = "Ocean_Far"; link(far, C_OCEAN)
far.data.materials.append(wm)
# fog volume (keyable density)
fog = box("Fog_Volume", (1400, 1400, 120), (0, 0, 55), col=C_OCEAN)
fmat = bpy.data.materials.new("M_Fog"); fmat.use_nodes = True; fn = fmat.node_tree.nodes; fn.remove(fn["Principled BSDF"])
pv = fn.new('ShaderNodeVolumePrincipled'); pv.name = "FogVol"; pv.inputs['Density'].default_value = 0.0004
pv.inputs['Color'].default_value = (0.8, 0.9, 1.0, 1); pv.inputs['Anisotropy'].default_value = 0.3
fmat.node_tree.links.new(pv.outputs[0], fn["Material Output"].inputs['Volume']); fog.data.materials.append(fmat)
# low mist bank around the berg (noise-modulated)
mist = box("Mist_Bank", (180, 120, 10), (0, -20, 4), col=C_OCEAN)
mm = bpy.data.materials.new("M_Mist"); mm.use_nodes = True; mn_ = mm.node_tree.nodes; ml = mm.node_tree.links; mn_.remove(mn_["Principled BSDF"])
pv2 = mn_.new('ShaderNodeVolumePrincipled'); pv2.inputs['Color'].default_value = (0.85, 0.88, 0.92, 1)
tcm = mn_.new('ShaderNodeTexCoord'); mpm = mn_.new('ShaderNodeMapping'); mpm.name = "MistDrift"
nzm = mn_.new('ShaderNodeTexNoise'); nzm.inputs['Scale'].default_value = 0.035; nzm.inputs['Detail'].default_value = 3
sz = mn_.new('ShaderNodeSeparateXYZ'); hz = mn_.new('ShaderNodeMapRange'); hz.inputs['From Min'].default_value = 0.0; hz.inputs['From Max'].default_value = 9.0
hz.inputs['To Min'].default_value = 1.0; hz.inputs['To Max'].default_value = 0.0
cr = mn_.new('ShaderNodeMapRange'); cr.inputs['From Min'].default_value = 0.45; cr.inputs['From Max'].default_value = 0.75; cr.inputs['To Max'].default_value = 0.008
mul = mn_.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
ml.new(tcm.outputs['Object'], mpm.inputs['Vector']); ml.new(mpm.outputs['Vector'], nzm.inputs['Vector'])
ml.new(nzm.outputs['Fac'], cr.inputs['Value']); ml.new(tcm.outputs['Object'], sz.inputs['Vector'])
ml.new(sz.outputs['Z'], hz.inputs['Value'])
ml.new(cr.outputs['Result'], mul.inputs[0]); ml.new(hz.outputs['Result'], mul.inputs[1]); ml.new(mul.outputs[0], pv2.inputs['Density'])
ml.new(pv2.outputs[0], mn_["Material Output"].inputs['Volume']); mist.data.materials.append(mm)
# mist bank object space z: box centred at 4 with half height 5 -> object z -5..5; remap From Min/Max accordingly
hz.inputs['From Min'].default_value = -5.0; hz.inputs['From Max'].default_value = 5.0

# ---------------------------------------------------------------- the iceberg (procedural sculpt, flattened scrape face on -Y)
Y0 = -17.0            # scrape face plane (berg's -Y face)
SMEAR_X = (-14.0, 16.0)
bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=6, radius=1.0)
FLAT_W = {}
peaks = [(Vector((-8, 4, 0)), 34, 14), (Vector((10, 2, 0)), 24, 12), (Vector((-20, 8, 0)), 16, 10), (Vector((18, 12, 0)), 14, 9)]
for v in bm.verts:
    d = v.co.copy()
    x, y, z = d.x * 36, d.y * 26, d.z
    if z >= 0:
        h = 6.0 + z * 6.0
        for pc, ph, pr in peaks:
            r = math.hypot(x - pc.x, y - pc.y) / pr
            h = max(h, ph * max(0.0, 1 - r ** 1.6) * (0.75 + 0.25 * z) + 4 * z)
        zz = h * z ** 0.55
    else:
        zz = 24 * z
    p = Vector((x, y, zz))
    # big faceted fracture: voronoi cells via cell noise
    q = p * 0.09
    p += d * (6.0 * noise.noise(q * 0.8, noise_basis='VORONOI_F2F1') + 3.0 * noise.noise(q * 2.3, noise_basis='VORONOI_F1') +
              1.6 * noise.fractal(q * 4.0, 0.6, 2.0, 4, noise_basis='PERLIN_ORIGINAL'))
    # flatten the scrape face (the side that met the hull) around the waterline
    if d.y < -0.2 and SMEAR_X[0] - 10 < p.x < SMEAR_X[1] + 10 and -6 < p.z < 9:
        wx = min(1, (p.x - (SMEAR_X[0] - 10)) / 8, ((SMEAR_X[1] + 10) - p.x) / 8)
        wz = min(1, (p.z + 6) / 3, (9 - p.z) / 4)
        wgt = max(0, min(1, wx)) * max(0, min(1, wz))
        p.y = p.y + (Y0 - p.y) * wgt
        p.y += 0.18 * wgt * noise.noise(p * 0.7)
        FLAT_W[v.index] = wgt
    v.co = p
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new("Iceberg"); bm.to_mesh(me); bm.free()
berg = bpy.data.objects.new("Iceberg", me); C_OCEAN.objects.link(berg)
vg = berg.vertex_groups.new(name="facet_mask")
for vi in range(len(me.vertices)): vg.add([vi], 1.0 - FLAT_W.get(vi, 0.0) * 0.85, 'REPLACE')
me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
# fine displacement on top (crystals, pits)
t1 = bpy.data.textures.new("IceFine", 'VORONOI'); t1.noise_scale = 0.9; t1.distance_metric = 'DISTANCE'
d1 = berg.modifiers.new("subd", 'SUBSURF'); d1.levels = d1.render_levels = 1
d2 = berg.modifiers.new("fine", 'DISPLACE'); d2.texture = t1; d2.strength = 0.35; d2.mid_level = 0.5
t2 = bpy.data.textures.new("IceStriae", 'DISTORTED_NOISE'); t2.noise_scale = 0.35; t2.distortion = 1.5
d3 = berg.modifiers.new("striae", 'DISPLACE'); d3.texture = t2; d3.strength = 0.12
t3 = bpy.data.textures.new("IceFacets", 'VORONOI'); t3.noise_scale = 3.0; t3.distance_metric = 'DISTANCE'; t3.color_mode = 'INTENSITY'
t3.weight_1 = -1.0; t3.weight_2 = 1.0; t3.noise_intensity = 1.6
d4 = berg.modifiers.new("facets", 'DISPLACE'); d4.texture = t3; d4.strength = 1.4; d4.mid_level = 0.3; d4.vertex_group = "facet_mask"
berg.modifiers.move(berg.modifiers.find("facets"), 1)
# ice material: SSS + snow texture, blue crevasses by pointiness, wet band, red paint mask (keyable)
icem = bpy.data.materials.new("M_Ice"); icem.use_nodes = True; n, l = icem.node_tree.nodes, icem.node_tree.links
p = n["Principled BSDF"]
df, nf, rf, _ = tex_files("snow_02")
tc_ = n.new('ShaderNodeTexCoord'); mp_ = n.new('ShaderNodeMapping'); mp_.inputs['Scale'].default_value = (0.25,) * 3
l.new(tc_.outputs['Object'], mp_.inputs['Vector'])
sd = n.new('ShaderNodeTexImage'); sd.image = img(df); sd.projection = 'BOX'; sd.projection_blend = 0.3; l.new(mp_.outputs['Vector'], sd.inputs['Vector'])
sn = n.new('ShaderNodeTexImage'); sn.image = img(nf, True); sn.projection = 'BOX'; sn.projection_blend = 0.3; l.new(mp_.outputs['Vector'], sn.inputs['Vector'])
geo = n.new('ShaderNodeNewGeometry')
crev = n.new('ShaderNodeMapRange'); crev.inputs['From Min'].default_value = 0.42; crev.inputs['From Max'].default_value = 0.52
l.new(geo.outputs['Pointiness'], crev.inputs['Value'])
blue = n.new('ShaderNodeMix'); blue.data_type = 'RGBA'; blue.inputs['B'].default_value = (0.86, 0.96, 1.0, 1)
blue.inputs['A'].default_value = (0.3, 0.72, 0.92, 1); l.new(crev.outputs['Result'], blue.inputs['Factor'])
base = n.new('ShaderNodeMix'); base.data_type = 'RGBA'; base.blend_type = 'MULTIPLY'; base.inputs['Factor'].default_value = 0.35
l.new(blue.outputs['Result'], base.inputs['A']); l.new(sd.outputs['Color'], base.inputs['B'])
# vertical meltwater streaks (stretched noise)
st_map = n.new('ShaderNodeMapping'); st_map.inputs['Scale'].default_value = (1.4, 1.4, 0.08); l.new(tc_.outputs['Object'], st_map.inputs['Vector'])
st_n = n.new('ShaderNodeTexNoise'); st_n.inputs['Scale'].default_value = 1.0; st_n.inputs['Detail'].default_value = 6
l.new(st_map.outputs['Vector'], st_n.inputs['Vector'])
st_r = n.new('ShaderNodeMapRange'); st_r.inputs['From Min'].default_value = 0.35; st_r.inputs['From Max'].default_value = 0.75
st_r.inputs['To Min'].default_value = 0.93; st_r.inputs['To Max'].default_value = 1.04; l.new(st_n.outputs['Fac'], st_r.inputs['Value'])
stm = n.new('ShaderNodeMix'); stm.data_type = 'RGBA'; stm.blend_type = 'MULTIPLY'; stm.inputs['Factor'].default_value = 1
l.new(base.outputs['Result'], stm.inputs['A']); l.new(st_r.outputs['Result'], stm.inputs['B'])
# red hull-paint smear: object-space band at the waterline on the scrape face, revealed by a keyable sweep
ox = n.new('ShaderNodeSeparateXYZ'); l.new(tc_.outputs['Object'], ox.inputs['Vector'])
bandz = n.new('ShaderNodeMapRange'); bandz.inputs['From Min'].default_value = 0.0; bandz.inputs['From Max'].default_value = 1.0
# z band 0.2..3.4 m with soft edges, made with two ramps
def ramp(src, a, b):
    r = n.new('ShaderNodeMapRange'); r.inputs['From Min'].default_value = a; r.inputs['From Max'].default_value = b; l.new(src, r.inputs['Value']); return r.outputs['Result']
def mult(a, b):
    m_ = n.new('ShaderNodeMath'); m_.operation = 'MULTIPLY'; l.new(a, m_.inputs[0]); l.new(b, m_.inputs[1]) if not isinstance(b, float) else None
    if isinstance(b, float): m_.inputs[1].default_value = b
    return m_.outputs[0]
zb = mult(ramp(ox.outputs['Z'], 1.15, 1.3), ramp(ox.outputs['Z'], 1.62, 1.5))
yb = ramp(ox.outputs['Y'], Y0 + 2.0, Y0 + 0.4)      # only on the scrape face
xb = mult(ramp(ox.outputs['X'], SMEAR_X[0], SMEAR_X[0] + 3), ramp(ox.outputs['X'], SMEAR_X[1], SMEAR_X[1] - 3))
sweep = n.new('ShaderNodeValue'); sweep.name = "SmearSweep"; sweep.outputs[0].default_value = SMEAR_X[0] - 5
sw = n.new('ShaderNodeMath'); sw.operation = 'SUBTRACT'; l.new(sweep.outputs[0], sw.inputs[0]); l.new(ox.outputs['X'], sw.inputs[1])
swr = ramp(sw.outputs[0], -1.0, 1.5)   # x < sweep -> painted (liner runs +X to -X, the sweep value moves down)
# reveal: painted where x > sweep  (sweep goes from SMEAR_X[1]+5 down to SMEAR_X[0]-5)
inv = n.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; l.new(swr, inv.inputs[1])
brk = n.new('ShaderNodeTexNoise'); brk.inputs['Scale'].default_value = 1.2; brk.inputs['Detail'].default_value = 10; brk.inputs['Roughness'].default_value = 0.7
smap = n.new('ShaderNodeMapping'); smap.inputs['Scale'].default_value = (0.6, 1, 4.0); l.new(tc_.outputs['Object'], smap.inputs['Vector']); l.new(smap.outputs['Vector'], brk.inputs['Vector'])
brr = ramp(brk.outputs['Fac'], 0.4, 0.52)
paint = mult(mult(mult(zb, yb), mult(xb, inv.outputs[0])), brr)
paint_s = n.new('ShaderNodeMath'); paint_s.operation = 'MULTIPLY'; paint_s.use_clamp = True; paint_s.inputs[1].default_value = 1.4
l.new(paint, paint_s.inputs[0])
pc = n.new('ShaderNodeMix'); pc.data_type = 'RGBA'; pc.inputs['B'].default_value = (0.2, 0.025, 0.018, 1)
l.new(paint_s.outputs[0], pc.inputs['Factor']); l.new(stm.outputs['Result'], pc.inputs['A'])
zk = mult(ramp(ox.outputs['Z'], 1.62, 1.72), ramp(ox.outputs['Z'], 1.98, 1.88))
blk = mult(mult(mult(zk, yb), mult(xb, inv.outputs[0])), brr)
blk_s = n.new('ShaderNodeMath'); blk_s.operation = 'MULTIPLY'; blk_s.use_clamp = True; blk_s.inputs[1].default_value = 1.3; l.new(blk, blk_s.inputs[0])
pk = n.new('ShaderNodeMix'); pk.data_type = 'RGBA'; pk.inputs['B'].default_value = (0.018, 0.016, 0.016, 1)
l.new(blk_s.outputs[0], pk.inputs['Factor']); l.new(pc.outputs['Result'], pk.inputs['A'])
l.new(pk.outputs['Result'], p.inputs['Base Color'])
l.new(pc.outputs['Result'], p.inputs['Subsurface Radius']) if False else None
p.inputs['Subsurface Weight'].default_value = 0.6; p.inputs['Subsurface Radius'].default_value = (0.4, 0.8, 1.2)
p.inputs['Subsurface Scale'].default_value = 0.6
rr = n.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = 0.35; rr.inputs['To Max'].default_value = 0.12
wet = ramp(ox.outputs['Z'], 3.0, 0.5)
l.new(wet, rr.inputs['Value']); l.new(rr.outputs['Result'], p.inputs['Roughness'])
p.inputs['Coat Weight'].default_value = 0.3
nm = n.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 0.3; l.new(sn.outputs['Color'], nm.inputs['Color'])
l.new(nm.outputs['Normal'], p.inputs['Normal'])
me.materials.append(icem)
berg.rotation_euler = (0, 0, 0)

# ice chunks (bergy bits) bobbing around: fractured chunks from the same sculpt approach
def chunk(name, size, loc, col=C_OCEAN):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    off = Vector((random.random() * 50, random.random() * 50, 0))
    for v in bm.verts:
        d = v.co.copy(); q = d * 1.3 + off
        v.co = Vector((d.x * size[0], d.y * size[1], d.z * size[2])) * (1 + 0.45 * noise.noise(q, noise_basis='VORONOI_F2F1') + 0.15 * noise.noise(q * 3))
    mee = bpy.data.meshes.new(name); bm.to_mesh(mee); bm.free()
    ob = bpy.data.objects.new(name, mee); ob.location = loc; col.objects.link(ob); mee.materials.append(icem)
    ob.rotation_euler = (random.random(), random.random(), random.random() * 6)
    return ob
BITS = []
for i in range(16):
    a = random.uniform(-2.6, 0.6); r = random.uniform(40, 70)
    BITS.append(chunk(f"Bergy_Bit_{i}", (random.uniform(0.6, 2.2), random.uniform(0.6, 1.8), random.uniform(0.4, 1.0)),
                      (r * math.cos(a), r * math.sin(a) * 0.9 - 10, 0.0)))
# a few large floes on the far (+Y) side, so the exit from the berg (beat 9) always has ice in frame
for i, (x, y, sz) in enumerate(((10, 58, 6.0), (24, 74, 8.0), (-2, 86, 7.0))):
    BITS.append(chunk(f"Bergy_Bit_Far_{i}", (sz, sz * 0.8, sz * 0.5), (x, y, 0.0)))
# small chunks at the scrape face waterline (macro beat)
for i in range(10):
    BITS.append(chunk(f"Ice_Shard_{i}", (random.uniform(0.15, 0.5),) * 2 + (random.uniform(0.1, 0.3),),
                      (random.uniform(SMEAR_X[0], SMEAR_X[1]), Y0 - random.uniform(0.8, 4), 0.0)))

# ---------------------------------------------------------------- steamship (the steward's ship) + our deck set
ship = import_glb("steamship", length=78, col=C_SHIP)
ship.data.transform(Matrix.Rotation(R_(90), 4, 'Z'))   # length along X
ship_root = bpy.data.objects.new("Ship_Root", None); C_SHIP.objects.link(ship_root)
ship.parent = ship_root
SHIP_START = Vector((-30, -112, -4.0))
ship_root.location = SHIP_START
dg = bpy.context.evaluated_depsgraph_get(); bpy.context.view_layer.update()
# find deck height near the berg-facing rail
DECK_X = float(os.environ.get('DECK_X', '6'))
def all_hits(o, x, y):
    hs = []; z = 80.0
    while True:
        h, lc, nr, _ = o.ray_cast(Vector((x, y, z)), Vector((0, 0, -1)))
        if not h: break
        hs.append((round(lc.z, 2), round(nr.z, 2))); z = lc.z - 0.01
    return hs
for xx in (-20, -10, 0, 6, 15, 25):
    print("HITS", xx, all_hits(ship, xx, 0), all_hits(ship, xx, 3))
cand = [h[0] for h in all_hits(ship, DECK_X, 3) if h[1] > 0.9 and h[0] > 2]
DECK_Z = min(cand) if cand else 6.0
side_pts = [v.co.y for v in ship.data.vertices if abs(v.co.x - DECK_X) < 4 and DECK_Z - 0.5 < v.co.z < DECK_Z + 1.5]
SIDE_Y = max(side_pts) if side_pts else 5.0
print("SHIP deck z", DECK_Z, "side y", SIDE_Y)
# deck planks + rail (local to ship root), placed on the berg-facing (+Y) side
DK = Vector((DECK_X, SIDE_Y - 2.6, DECK_Z + 0.02))
deck = box("Deck_Planks", (14, 5.4, 0.12), DK - Vector((0, 0, 0.06)), pbr("M_Deck", "wood_floor_deck", 2.0, tint=(0.85, 0.75, 0.62), rough_mul=0.9), C_SHIP)
deck.parent = ship_root
wood_rail = pbr("M_RailTeak", "wood_table_worn", 0.6, tint=(0.8, 0.55, 0.35))
metal = pbr("M_PaintedSteel", "rusty_painted_metal", 1.2, tint=(0.95, 0.95, 0.9))
for i in range(15):
    px = DK.x - 7 + i
    post = box(f"Rail_Post_{i}", (0.06, 0.06, 1.05), (px, DK.y + 2.55, DK.z + 0.52), metal, C_SHIP, bevel=0.01); post.parent = ship_root
for k, hz_ in enumerate((0.4, 0.75)):
    bar = box(f"Rail_Bar_{k}", (14, 0.035, 0.035), (DK.x, DK.y + 2.55, DK.z + hz_), metal, C_SHIP, bevel=0.008); bar.parent = ship_root
cap = box("Rail_Cap", (14.1, 0.16, 0.08), (DK.x, DK.y + 2.55, DK.z + 1.08), wood_rail, C_SHIP, bevel=0.025); cap.parent = ship_root
# bulkhead with portholes behind the steward (painted steel, riveted look by texture)
bulk = box("Deck_Bulkhead", (14, 0.25, 2.6), (DK.x, DK.y - 2.75, DK.z + 1.3), metal, C_SHIP, bevel=0.02); bulk.parent = ship_root
for i in range(5):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.22, minor_radius=0.045, location=(DK.x - 5 + i * 2.5, DK.y - 2.6, DK.z + 1.6), rotation=(R_(90), 0, 0))
    ph = bpy.context.object; ph.name = f"Porthole_{i}"; link(ph, C_SHIP); ph.parent = ship_root
    ph.data.materials.append(mat_simple("M_Brass", (0.6, 0.42, 0.18), 0.3, 1.0))
    bpy.ops.mesh.primitive_circle_add(radius=0.2, fill_type='NGON', location=(DK.x - 5 + i * 2.5, DK.y - 2.62, DK.z + 1.6), rotation=(R_(90), 0, 0))
    gl = bpy.context.object; gl.name = f"Porthole_Glass_{i}"; link(gl, C_SHIP); gl.parent = ship_root
    gl.data.materials.append(mat_simple("M_PortGlow", (0.1, 0.08, 0.05), 0.1, 0, (1.0, 0.7, 0.35), 2.0))
# props on deck: coiled rope (spiral tube), deck chairs, crate, lifebuoy, camera
chair = import_glb("deckchair", height=0.85, col=C_SHIP); chair.location = DK + Vector((-4.2, -1.4, 0)); chair.rotation_euler.z = R_(-20); chair.parent = ship_root
chair2 = chair.copy(); chair2.location = DK + Vector((-5.4, -1.2, 0)); chair2.rotation_euler.z = R_(10); C_SHIP.objects.link(chair2)
buoy = import_glb("lifebuoy", length=0.75, col=C_SHIP); buoy.rotation_euler = (R_(90), 0, 0); buoy.location = DK + Vector((3.0, -2.55, 1.2)); buoy.parent = ship_root
crate = import_glb("crate", height=0.7, col=C_SHIP); crate.location = DK + Vector((5.0, -1.6, 0)); crate.parent = ship_root
coil = bpy.data.curves.new("Rope_Coil", 'CURVE'); coil.dimensions = '3D'; sp = coil.splines.new('POLY'); pts_ = []
for i in range(220):
    a = i * 0.35; r = 0.18 + 0.12 * ((i % 60) / 60); pts_.append((r * math.cos(a), r * math.sin(a), 0.025 + 0.05 * (i // 60)))
sp.points.add(len(pts_) - 1)
for pt, co in zip(sp.points, pts_): pt.co = (*co, 1)
coil.bevel_depth = 0.022; coil.bevel_resolution = 3
rope = bpy.data.objects.new("Rope_Coil", coil); C_SHIP.objects.link(rope); rope.location = DK + Vector((1.5, -1.0, 0)); rope.parent = ship_root
ropem = pbr("M_Rope", "wood_table_worn", 0.08, tint=(0.75, 0.62, 0.42)); coil.materials.append(ropem)
bcam = import_glb("bcamera", length=0.32, col=C_SHIP)
gull = import_glb("gull", length=1.0, col=C_SHIP)       # the steward's bellows camera (animated later)
# funnel smoke (volume) above the ship's chimney
smoke = box("Funnel_Smoke", (10, 10, 30), (0, 0, 0), col=C_SHIP)
smm = bpy.data.materials.new("M_Smoke"); smm.use_nodes = True; sn_ = smm.node_tree.nodes; sl = smm.node_tree.links; sn_.remove(sn_["Principled BSDF"])
pv3 = sn_.new('ShaderNodeVolumePrincipled'); pv3.inputs['Color'].default_value = (0.25, 0.24, 0.23, 1)
tcs = sn_.new('ShaderNodeTexCoord'); ns = sn_.new('ShaderNodeTexNoise'); ns.inputs['Scale'].default_value = 0.4; ns.inputs['Detail'].default_value = 4
mps = sn_.new('ShaderNodeMapping'); mps.name = "SmokeDrift"; sl.new(tcs.outputs['Object'], mps.inputs['Vector']); sl.new(mps.outputs['Vector'], ns.inputs['Vector'])
sg = sn_.new('ShaderNodeTexGradient'); sg.gradient_type = 'SPHERICAL'
mps2 = sn_.new('ShaderNodeMapping'); mps2.inputs['Scale'].default_value = (0.25, 0.25, 0.07); sl.new(tcs.outputs['Object'], mps2.inputs['Vector']); sl.new(mps2.outputs['Vector'], sg.inputs['Vector'])
smul = sn_.new('ShaderNodeMath'); smul.operation = 'MULTIPLY'; smul2 = sn_.new('ShaderNodeMath'); smul2.operation = 'MULTIPLY'; smul2.inputs[1].default_value = 1.2
sl.new(ns.outputs['Fac'], smul.inputs[0]); sl.new(sg.outputs['Fac'], smul.inputs[1]); sl.new(smul.outputs[0], smul2.inputs[0]); sl.new(smul2.outputs[0], pv3.inputs['Density'])
sl.new(pv3.outputs[0], sn_["Material Output"].inputs['Volume']); smoke.data.materials.append(smm)
# chimney location: top-most point of the ship mesh
top = max(ship.data.vertices, key=lambda v: v.co.z).co
smoke.location = Vector((top.x - 8, top.y, top.z + 12)); smoke.rotation_euler = (0, R_(-35), 0); smoke.parent = ship_root

# ---------------------------------------------------------------- debris field (beat 4): chairs, planks, crates, lifebuoys
deckw = pbr("M_DebrisWood", "old_wood_floor", 1.2, tint=(0.8, 0.72, 0.6))
DEBRIS = []
for i in range(60):
    x = random.uniform(-30, 25); y = random.uniform(-80, -24)
    k = i % 5
    if k == 0:
        o = chair.copy(); o.data = chair.data; o.parent = None; o.scale = (1, 1, 1)
        C_DEBRIS.objects.link(o); o.rotation_euler = (random.uniform(1.2, 1.9), random.uniform(-.4, .4), random.uniform(0, 6))
    elif k == 1:
        o = crate.copy(); o.parent = None; C_DEBRIS.objects.link(o); o.rotation_euler = (random.uniform(-.3, .3), random.uniform(-.3, .3), random.uniform(0, 6))
    elif k == 2:
        o = buoy.copy(); o.parent = None; C_DEBRIS.objects.link(o); o.rotation_euler = (random.uniform(-.2, .2), random.uniform(-.2, .2), 0)
    else:
        o = box(f"Debris_Plank_{i}", (random.uniform(1.5, 3.5), random.uniform(0.18, 0.3), 0.05), (0, 0, 0), deckw, C_DEBRIS, bevel=0.01)
        o.rotation_euler = (0, 0, random.uniform(0, 6))
    o.location = (x, y, 0.0); o.name = f"Debris_{i}"; DEBRIS.append(o)

# ---------------------------------------------------------------- ghost liner (four funnels, no name/text)
liner = import_glb("liner", length=269, col=C_GHOST)
liner.data.transform(Matrix.Rotation(R_(0), 4, 'Z'))
dec = liner.modifiers.new("dec", 'DECIMATE'); dec.ratio = 0.4
bpy.context.view_layer.objects.active = liner; bpy.ops.object.modifier_apply(modifier="dec")
gm = bpy.data.materials.new("M_Ghost"); gm.use_nodes = True; gn, gl_ = gm.node_tree.nodes, gm.node_tree.links; gn.clear()
lw = gn.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
em = gn.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.3, 0.62, 1.0, 1)
fr_ = gn.new('ShaderNodeMath'); fr_.operation = 'MULTIPLY'; fr_.inputs[1].default_value = 2.0
sepz = gn.new('ShaderNodeSeparateXYZ'); tcg = gn.new('ShaderNodeTexCoord'); gl_.new(tcg.outputs['Object'], sepz.inputs['Vector'])
# red band at the hull bottom (glows in the explainer): object z below waterline height
band = gn.new('ShaderNodeMapRange'); band.inputs['From Min'].default_value = 0.0; band.inputs['From Max'].default_value = 0.2
gl_.new(sepz.outputs['Z'], band.inputs['Value'])
ghostAlpha = gn.new('ShaderNodeValue'); ghostAlpha.name = "GhostAlpha"; ghostAlpha.outputs[0].default_value = 0.0
redGlow = gn.new('ShaderNodeValue'); redGlow.name = "RedBand"; redGlow.outputs[0].default_value = 0.0
fpow = gn.new('ShaderNodeMath'); fpow.operation = 'POWER'; fpow.inputs[1].default_value = 5.0
gl_.new(lw.outputs['Facing'], fpow.inputs[0])
fbase = gn.new('ShaderNodeMath'); fbase.operation = 'ADD'; fbase.inputs[1].default_value = 0.06
gl_.new(fpow.outputs[0], fbase.inputs[0]); gl_.new(fbase.outputs[0], fr_.inputs[0])
emr = gn.new('ShaderNodeEmission'); emr.inputs['Color'].default_value = (1.0, 0.08, 0.04, 1)
emr_s = gn.new('ShaderNodeMath'); emr_s.operation = 'MULTIPLY'; gl_.new(redGlow.outputs[0], emr_s.inputs[0]); emr_s.inputs[1].default_value = 8.0
gl_.new(emr_s.outputs[0], emr.inputs['Strength'])
gl_.new(fr_.outputs[0], em.inputs['Strength'])
mxr = gn.new('ShaderNodeMixShader'); bandinv = gn.new('ShaderNodeMath'); bandinv.operation = 'SUBTRACT'; bandinv.inputs[0].default_value = 1.0
gl_.new(band.outputs['Result'], bandinv.inputs[1])
bandr = gn.new('ShaderNodeMath'); bandr.operation = 'MULTIPLY'; gl_.new(bandinv.outputs[0], bandr.inputs[0]); gl_.new(redGlow.outputs[0], bandr.inputs[1])
gl_.new(bandr.outputs[0], mxr.inputs['Fac']); gl_.new(em.outputs[0], mxr.inputs[1]); gl_.new(emr.outputs[0], mxr.inputs[2])
tr = gn.new('ShaderNodeBsdfTransparent')
# additive ghost: fully transparent + fresnel emission scaled by GhostAlpha, plus the red band glow
ga = gn.new('ShaderNodeMath'); ga.operation = 'MULTIPLY'; gl_.new(fr_.outputs[0], ga.inputs[0]); gl_.new(ghostAlpha.outputs[0], ga.inputs[1])
lpth = gn.new('ShaderNodeLightPath'); first = gn.new('ShaderNodeMath'); first.operation = 'LESS_THAN'; first.inputs[1].default_value = 0.5
gl_.new(lpth.outputs['Transparent Depth'], first.inputs[0])
ga2 = gn.new('ShaderNodeMath'); ga2.operation = 'MULTIPLY'; gl_.new(ga.outputs[0], ga2.inputs[0]); gl_.new(first.outputs[0], ga2.inputs[1])
gl_.new(ga2.outputs[0], em.inputs['Strength'])
emr_b = gn.new('ShaderNodeMath'); emr_b.operation = 'MULTIPLY'; gl_.new(bandr.outputs[0], emr_b.inputs[0]); emr_b.inputs[1].default_value = 6.0
emr_c = gn.new('ShaderNodeMath'); emr_c.operation = 'MULTIPLY'; gl_.new(emr_b.outputs[0], emr_c.inputs[0]); gl_.new(first.outputs[0], emr_c.inputs[1])
gl_.new(emr_c.outputs[0], emr.inputs['Strength'])
add1 = gn.new('ShaderNodeAddShader'); gl_.new(tr.outputs[0], add1.inputs[0]); gl_.new(em.outputs[0], add1.inputs[1])
mxa = gn.new('ShaderNodeAddShader'); gl_.new(add1.outputs[0], mxa.inputs[0]); gl_.new(emr.outputs[0], mxa.inputs[1])
go = gn.new('ShaderNodeOutputMaterial'); gl_.new(mxa.outputs[0], go.inputs['Surface'])
liner.data.materials.clear(); liner.data.materials.append(gm)
for sl_ in liner.material_slots: sl_.link = 'DATA'
liner.data.materials.clear(); liner.data.materials.append(gm)
for sl_ in liner.material_slots: sl_.material = gm
for pl in liner.data.polygons: pl.material_index = 0
liner.visible_shadow = False; liner.visible_diffuse = False; liner.visible_glossy = False
liner.visible_transmission = False; liner.visible_volume_scatter = False
pts = [v.co for v in liner.data.vertices]
LINER_LEN = max(p.x for p in pts) - min(p.x for p in pts); LINER_BEAM = max(p.y for p in pts) - min(p.y for p in pts)
print("LINER", LINER_LEN, LINER_BEAM, max(p.z for p in pts))
# hull waterline offset: sink the model so ~11 m of hull is under water
liner.data.transform(Matrix.Translation(Vector((0, 0, -10.5))))
band.inputs['From Min'].default_value = 0.6; band.inputs['From Max'].default_value = 1.4   # red band: object z < ~1 m (waterline zone)
band2 = gn.new('ShaderNodeMapRange'); band2.inputs['From Min'].default_value = -2.6; band2.inputs['From Max'].default_value = -1.8
gl_.new(sepz.outputs['Z'], band2.inputs['Value'])
bandm = gn.new('ShaderNodeMath'); bandm.operation = 'MULTIPLY'; gl_.new(bandr.outputs[0], bandm.inputs[0]); gl_.new(band2.outputs['Result'], bandm.inputs[1])
gl_.new(bandm.outputs[0], emr_b.inputs[0])
# second copy for the explainer (static, side-on)
liner.location = (0, -60, 0)
liner_x = liner.copy(); liner_x.name = "Liner_Explainer"; C_CYC.objects.link(liner_x)
gmx = gm.copy(); gmx.name = "M_Ghost_Explainer"; liner_x.material_slots[0].link = 'OBJECT'; liner_x.material_slots[0].material = gmx

# sparks emitter (beat 5): particle system on a small plane that follows the contact point
bpy.ops.mesh.primitive_plane_add(size=1.0); spk = bpy.context.object; spk.name = "Spark_Emitter"; link(spk, C_FX)
ps = spk.modifiers.new("sparks", 'PARTICLE_SYSTEM').particle_system; pst = ps.settings
pst.count = 2500; pst.frame_start = 930; pst.frame_end = 1080; pst.lifetime = 28; pst.lifetime_random = 0.6
pst.normal_factor = 6; pst.factor_random = 5; pst.effector_weights.gravity = 1.0; pst.render_type = 'OBJECT'; pst.particle_size = 0.012; pst.size_random = 0.6
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0, location=(0, 0, -500)); sdot = bpy.context.object; sdot.name = "Spark_Dot"; link(sdot, C_FX)
sdot.data.materials.append(mat_simple("M_Spark", (1, 0.4, 0.05), 0.5, 0, (1.0, 0.35, 0.05), 12.0))
pst.instance_object = sdot; sdot.hide_render = False
spk.show_instancer_for_render = False
glow = bpy.data.objects.new("Scrape_Glow", bpy.data.lights.new("Scrape_Glow", 'POINT')); glow.data.energy = 0; glow.data.color = (1.0, 0.55, 0.25)
glow.data.shadow_soft_size = 0.2; C_FX.objects.link(glow); glow.parent = spk; glow.location = (0, 0, 1.5)

# ---------------------------------------------------------------- rooms inside the berg (enclosed, red darkroom -> office), explainer cyc
plaster = pbr("M_Plaster", "painted_plaster_wall", 1.5, tint=(1.25, 1.12, 0.92), bump=0.3)
plaster_dark = pbr("M_Plaster_Dark", "painted_plaster_wall", 1.5, tint=(0.35, 0.3, 0.27))
floorw = pbr("M_Floor", "old_wood_floor", 1.6)
def room(name, x0, x1, y0, y1, z0, z1, wallm, door=None):
    """six walls as separate thin boxes so the camera-facing ones can be hidden as the camera flies through"""
    t = 0.12; parts = {}
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    parts["floor"] = box(name + "_Floor", (x1 - x0, y1 - y0, t), (cx, cy, z0 - t / 2), floorw, C_ROOMS)
    parts["ceil"] = box(name + "_Ceiling", (x1 - x0, y1 - y0, t), (cx, cy, z1 + t / 2), wallm, C_ROOMS)
    parts["front"] = box(name + "_WallFront", (x1 - x0, t, z1 - z0), (cx, y0 - t / 2, cz), wallm, C_ROOMS)
    parts["back"] = box(name + "_WallBack", (x1 - x0, t, z1 - z0), (cx, y1 + t / 2, cz), wallm, C_ROOMS)
    parts["left"] = box(name + "_WallLeft", (t, y1 - y0, z1 - z0), (x0 - t / 2, cy, cz), wallm, C_ROOMS)
    parts["right"] = box(name + "_WallRight", (t, y1 - y0, z1 - z0), (x1 + t / 2, cy, cz), wallm, C_ROOMS)
    if door:   # cut a door into the right wall: (y centre, width, height)
        w_ = parts["right"]; bo = w_.modifiers.new("door", 'BOOLEAN')
        cutter = box(name + "_DoorCut", (1.0, door[1], door[2]), (x1, door[0], z0 + door[2] / 2), None, C_ROOMS); cutter.hide_render = True; cutter.hide_viewport = True
        bo.object = cutter; bo.operation = 'DIFFERENCE'
    return parts
RZ0, RZ1 = 0.9, 4.1
DR = room("Darkroom", -2.0, 4.5, Y0 + 0.6, Y0 + 6.6, RZ0, RZ1, plaster_dark, door=(Y0 + 4.4, 1.6, 2.5))
OF = room("Office", 4.5, 12.0, Y0 + 0.6, Y0 + 7.6, RZ0, RZ1, plaster)
_bo = OF["left"].modifiers.new("door", 'BOOLEAN'); _bo.object = bpy.data.objects["Darkroom_DoorCut"]; _bo.operation = 'DIFFERENCE'
# explainer cyc: big curved gradient sweep inside the berg (deep teal -> navy)
CYC_C = Vector((8.0, Y0 + 15.5, RZ0))
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=7.0, location=CYC_C + Vector((0, 0, 3.0)))
cyc = bpy.context.object; cyc.name = "Explainer_Cyc"; link(cyc, C_CYC)
for f_ in cyc.data.polygons: f_.use_smooth = True
cm = bpy.data.materials.new("M_CycGradient"); cm.use_nodes = True; cn, cl = cm.node_tree.nodes, cm.node_tree.links; cn.clear()
ctc = cn.new('ShaderNodeTexCoord'); csz = cn.new('ShaderNodeSeparateXYZ'); cl.new(ctc.outputs['Object'], csz.inputs['Vector'])
cr_ = cn.new('ShaderNodeMapRange'); cr_.inputs['From Min'].default_value = -7; cr_.inputs['From Max'].default_value = 7; cl.new(csz.outputs['Z'], cr_.inputs['Value'])
crp = cn.new('ShaderNodeValToRGB'); crp.color_ramp.elements[0].color = (0.80, 0.93, 1.0, 1); crp.color_ramp.elements[1].color = (0.08, 0.55, 0.93, 1)
crp.color_ramp.elements[0].position = 0.25
cl.new(cr_.outputs['Result'], crp.inputs['Fac'])
cnz = cn.new('ShaderNodeTexNoise'); cnz.inputs['Scale'].default_value = 2.0
cbg = cn.new('ShaderNodeEmission'); cl.new(crp.outputs['Color'], cbg.inputs['Color']); cbg.inputs['Strength'].default_value = 1.0
cyc_fade = cn.new('ShaderNodeValue'); cyc_fade.name = "CycFade"; cyc_fade.outputs[0].default_value = 1.0
ctr = cn.new('ShaderNodeBsdfTransparent'); cmx = cn.new('ShaderNodeMixShader')
cgeo = cn.new('ShaderNodeNewGeometry'); cfm = cn.new('ShaderNodeMath'); cfm.operation = 'MULTIPLY'
cl.new(cyc_fade.outputs[0], cfm.inputs[0]); cl.new(cgeo.outputs['Backfacing'], cfm.inputs[1]); cl.new(cfm.outputs[0], cmx.inputs['Fac'])
cl.new(ctr.outputs[0], cmx.inputs[1]); cl.new(cbg.outputs[0], cmx.inputs[2])
co_ = cn.new('ShaderNodeOutputMaterial'); cl.new(cmx.outputs[0], co_.inputs['Surface']); cyc.data.materials.append(cm)
cyc.visible_shadow = False
# explainer floor: dark wet reflective stage
stage = box("Explainer_Stage", (13, 13, 0.1), CYC_C - Vector((0, 0, 0.05)), mat_simple("M_Stage", (0.55, 0.78, 0.92), 0.4, 0.0), C_CYC)

# ---------------------------------------------------------------- the photo image (filled in by 03 with a render of beat 1)
pimg = bpy.data.images.new("Photo_Iceberg", 540, 720); pimg.generated_color = (0.5, 0.48, 0.44, 1)
def photo_mat(name, develop=True, flat=False):
    m = bpy.data.materials.new(name); m.use_nodes = True; n, l = m.node_tree.nodes, m.node_tree.links; p = n["Principled BSDF"]
    t = n.new('ShaderNodeTexImage'); t.image = pimg; t.extension = 'CLIP'
    gtc = n.new('ShaderNodeTexCoord'); gs = n.new('ShaderNodeSeparateXYZ'); gc = n.new('ShaderNodeCombineXYZ')
    l.new(gtc.outputs['Generated'], gs.inputs['Vector']); l.new(gs.outputs['X'], gc.inputs['X'])
    l.new(gs.outputs['Y' if flat else 'Z'], gc.inputs['Y']); l.new(gc.outputs['Vector'], t.inputs['Vector'])
    v = n.new('ShaderNodeValue'); v.name = "Develop"; v.outputs[0].default_value = 1.0
    paper = n.new('ShaderNodeMix'); paper.data_type = 'RGBA'; paper.inputs['A'].default_value = (0.85, 0.82, 0.75, 1)
    l.new(v.outputs[0], paper.inputs['Factor']); l.new(t.outputs['Color'], paper.inputs['B'])
    l.new(paper.outputs['Result'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.25 if develop else 0.45
    return m
# ---------------------------------------------------------------- darkroom dressing
redL = bpy.data.objects.new("Safelight", bpy.data.lights.new("Safelight", 'AREA')); redL.data.energy = 230; redL.data.color = (1.0, 0.08, 0.03)
redL.data.size = 0.4; redL.location = (1.2, Y0 + 5.0, RZ1 - 0.25); C_ROOMS.objects.link(redL)
redL2 = bpy.data.objects.new("Safelight_Fill", bpy.data.lights.new("Safelight_Fill", 'POINT')); redL2.data.energy = 70; redL2.data.color = (1.0, 0.12, 0.05)
redL2.location = (-1.0, Y0 + 2.0, RZ1 - 0.5); C_ROOMS.objects.link(redL2)
faceL = bpy.data.objects.new("Darkroom_Face_Fill", bpy.data.lights.new("Darkroom_Face_Fill", 'AREA')); faceL.data.energy = 35; faceL.data.size = 0.5
faceL.data.color = (1.0, 0.3, 0.2); faceL.location = (2.1, Y0 + 5.2, 2.0); faceL.rotation_euler = (R_(70), 0, R_(125)); C_ROOMS.objects.link(faceL)
lampbox = box("Safelight_Housing", (0.45, 0.25, 0.3), (1.2, Y0 + 5.1, RZ1 - 0.12), mat_simple("M_SafelightBox", (0.05, 0.04, 0.035), 0.4, 0.6), C_ROOMS, bevel=0.02)
lampglass = box("Safelight_Glass", (0.36, 0.02, 0.2), (1.2, Y0 + 4.97, RZ1 - 0.15), mat_simple("M_SafelightGlass", (0.3, 0.0, 0.0), 0.2, 0, (1, 0.05, 0.02), 25), C_ROOMS)
# v004 fix: the object rotation did not stick, so the desks stood side-on (the tech and expert B stood inside them); rotate the mesh data instead
bench = import_glb("desk", length=2.2, col=C_ROOMS); bench.data.transform(Matrix.Rotation(R_(90), 4, 'Z')); bench.location = (1.2, Y0 + 5.6, RZ0)
BENCH_TOP = RZ0 + max(v.co.z for v in bench.data.vertices)
print("BENCH extent x", min(v.co.x for v in bench.data.vertices), max(v.co.x for v in bench.data.vertices), "y", min(v.co.y for v in bench.data.vertices), max(v.co.y for v in bench.data.vertices))
enamel = mat_simple("M_Enamel", (0.85, 0.84, 0.8), 0.15)
liquid = mat_simple("M_Developer", (0.7, 0.62, 0.5), 0.02)
liquid.node_tree.nodes["Principled BSDF"].inputs['Transmission Weight'].default_value = 1.0
TRAYS = []
for i, tx in enumerate((0.45, 1.2, 1.95)):
    tray = box(f"Tray_{i}", (0.6, 0.45, 0.07), (tx, Y0 + 5.45, BENCH_TOP + 0.035), enamel, C_ROOMS)
    bm_ = bmesh.new(); bm_.from_mesh(tray.data); top_ = [f_ for f_ in bm_.faces if f_.normal.z > 0.9]
    bmesh.ops.delete(bm_, geom=top_, context='FACES_ONLY'); bm_.to_mesh(tray.data); bm_.free()
    so_ = tray.modifiers.new("wall", 'SOLIDIFY'); so_.thickness = 0.008; so_.offset = -1
    bv_ = tray.modifiers.new("bev", 'BEVEL'); bv_.width = 0.006; bv_.segments = 2
    sol = box(f"Tray_Liquid_{i}", (0.57, 0.42, 0.002), (tx, Y0 + 5.45, BENCH_TOP + 0.05), liquid, C_ROOMS)
    sol.visible_shadow = False
    TRAYS.append((tray, sol))
print_dev = box("Print_Developing", (0.36, 0.27, 0.003), (1.2, Y0 + 5.45, BENCH_TOP + 0.03), photo_mat("M_Print_Dev", flat=True), C_ROOMS)
line = box("Drying_Line", (6.2, 0.008, 0.008), (1.25, Y0 + 3.6, RZ1 - 0.6), mat_simple("M_Line", (0.5, 0.45, 0.4), 0.8), C_ROOMS)
HANG = []
for i in range(5):
    hp = box(f"Hanging_Print_{i}", (0.3, 0.004, 0.38), (-1.2 + i * 1.2, Y0 + 3.6, RZ1 - 0.8), photo_mat(f"M_Print_Hang_{i}"), C_ROOMS)
    HANG.append(hp)
tongs = box("Tongs", (0.22, 0.012, 0.01), (1.2, Y0 + 5.3, BENCH_TOP + 0.1), mat_simple("M_Bamboo", (0.55, 0.42, 0.25), 0.5), C_ROOMS, bevel=0.004)
# ---------------------------------------------------------------- office dressing
desk = import_glb("desk", length=1.9, col=C_ROOMS); desk.data.transform(Matrix.Rotation(R_(90), 4, 'Z')); desk.location = (8.2, Y0 + 4.6, RZ0)
DESK_TOP = RZ0 + max(v.co.z for v in desk.data.vertices)
lamp = import_glb("lamp", height=0.5, col=C_ROOMS); lamp.location = (7.6, Y0 + 4.85, DESK_TOP)
lampL = bpy.data.objects.new("Desk_Lamp_Light", bpy.data.lights.new("Desk_Lamp_Light", 'POINT')); lampL.data.energy = 60; lampL.data.color = (1.0, 0.75, 0.45)
lampL.location = (7.62, Y0 + 4.75, DESK_TOP + 0.38); lampL.data.shadow_soft_size = 0.08; C_ROOMS.objects.link(lampL)
winL = bpy.data.objects.new("Office_Window_Light", bpy.data.lights.new("Office_Window_Light", 'AREA')); winL.data.energy = 650; winL.data.size = 4.0
winL.data.color = (1.0, 0.93, 0.82); winL.location = (11.6, Y0 + 3.5, 3.0); winL.rotation_euler = (0, R_(90), 0); C_ROOMS.objects.link(winL)
fillO = bpy.data.objects.new("Office_Fill", bpy.data.lights.new("Office_Fill", 'AREA')); fillO.data.energy = 900; fillO.data.size = 3
fillO.location = (6.0, Y0 + 1.5, 3.8); fillO.rotation_euler = (R_(30), 0, 0); C_ROOMS.objects.link(fillO)
backO = bpy.data.objects.new("Office_Back_Light", bpy.data.lights.new("Office_Back_Light", 'AREA')); backO.data.energy = 600; backO.data.size = 2
backO.data.color = (1.0, 0.85, 0.65); backO.location = (9.5, Y0 + 3.0, 3.9); backO.rotation_euler = (R_(-35), R_(25), 0); C_ROOMS.objects.link(backO)
clock = import_glb("clock", height=0.55, col=C_ROOMS); clock.location = (10.5, Y0 + 7.5, 2.4); clock.rotation_euler.z = R_(180)
mag = import_glb("magnifier", height=0.28, col=C_ROOMS)
office_print = box("Print_Office", (0.36, 0.003, 0.27), (8.2, Y0 + 4.0, DESK_TOP + 0.4), photo_mat("M_Print_Office"), C_ROOMS)
office_print.rotation_euler = (R_(-6), 0, 0)
# a stack of papers / books on the desk for life
for i in range(3):
    bk = box(f"Book_{i}", (0.24, 0.17, 0.04), (8.9, Y0 + 4.85 - i * 0.02, DESK_TOP + 0.02 + i * 0.04), mat_simple(f"M_Book_{i}", (0.2 + 0.1 * i, 0.08, 0.05), 0.6), C_ROOMS, bevel=0.004)
# explainer giant print (vertical, faces -Y toward camera)
giant = box("Print_Giant", (5.4, 0.02, 4.05), CYC_C + Vector((-1.5, 3.2, 2.6)), photo_mat("M_Print_Giant"), C_CYC)
# explainer key lights
for nm_, loc_, e_ in (("Cyc_Key", (3, Y0 + 9.5, 6), 600), ("Cyc_Rim", (13, Y0 + 20, 5), 400)):
    L = bpy.data.objects.new(nm_, bpy.data.lights.new(nm_, 'AREA')); L.data.energy = e_; L.data.size = 2.5; L.location = loc_
    L.rotation_euler = (Vector(CYC_C + Vector((0, 0, 2))) - Vector(loc_)).to_track_quat('-Z', 'Y').to_euler(); C_CYC.objects.link(L)
    L.data.color = (0.8, 0.92, 1.0)

# deck key/rim for dawn (warm low key from the sun + cool fill)
fill = bpy.data.objects.new("Deck_Fill", bpy.data.lights.new("Deck_Fill", 'AREA')); fill.data.energy = 0; fill.data.size = 4
fill.data.color = (0.7, 0.8, 1.0); C_SHIP.objects.link(fill); fill.parent = ship_root; fill.location = DK + Vector((-3, 3, 3)); fill.rotation_euler = (R_(-50), 0, R_(200))

# persist layout numbers for the animation script
sc["Y0"] = Y0; sc["SMEAR_X"] = list(SMEAR_X); sc["DECK"] = list(DK); sc["SHIP_START"] = list(SHIP_START)
sc["BENCH_TOP"] = BENCH_TOP; sc["DESK_TOP"] = DESK_TOP; sc["CYC_C"] = list(CYC_C); sc["RZ0"] = RZ0
print("LAYOUT", dict(Y0=Y0, DK=tuple(DK), BENCH_TOP=BENCH_TOP, DESK_TOP=DESK_TOP))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
