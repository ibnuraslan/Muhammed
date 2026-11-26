"""WW1Assassination v008 stage C: the 3D relief map of 1914 Europe under the city (1 m = 1 km, Sarajevo at the origin).
blender -b anim.blend --python 03_map.py -- <work_dir with map_state.png, map_height.png> <out.blend>
No text anywhere. The war spreads like fire from Austria-Hungary and Serbia across the alliances (map_state.png R channel =
ignite time per pixel); a fire band glows on every wave front; flags rise on poles in Vienna and Belgrade (no emblems)."""
import bpy, sys, os, math
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
WD, OUT = os.path.abspath(a[0]), os.path.abspath(a[1])
XMIN, XMAX, YMIN, YMAX = -2600.0, 2600.0, -2400.0, 3400.0
IGN0, IGN1 = 1400, 1826
F_SHOW = 1487
ZTOP = -3.6; HSCALE = 90.0
mc = bpy.data.collections.new("Map"); sc.collection.children.link(mc)
st_img = bpy.data.images.load(os.path.join(WD, "map_state.png")); st_img.colorspace_settings.name = 'Non-Color'
ht_img = bpy.data.images.load(os.path.join(WD, "map_height.png")); ht_img.colorspace_settings.name = 'Non-Color'
# terrain: one plane + simple subdivision + displacement by the relief image (small file, no stored dense mesh)
bpy.ops.mesh.primitive_plane_add(size=1.0, location=((XMIN + XMAX) / 2, (YMIN + YMAX) / 2, ZTOP))
T = bpy.context.active_object; T.name = "MapTerrain"; T.scale = (XMAX - XMIN, YMAX - YMIN, 1)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)     # mesh in world coordinates (UV 0..1 = map extent)
for c in list(T.users_collection): c.objects.unlink(T)
mc.objects.link(T)
sd = T.modifiers.new("grid", 'SUBSURF'); sd.subdivision_type = 'SIMPLE'; sd.levels = 9; sd.render_levels = 9
tex = bpy.data.textures.new("MapHeight", 'IMAGE'); tex.image = ht_img; tex.extension = 'EXTEND'
dp = T.modifiers.new("relief", 'DISPLACE'); dp.texture = tex; dp.texture_coords = 'UV'; dp.strength = HSCALE; dp.mid_level = 0.0
sm = T.modifiers.new("smooth", 'SMOOTH'); sm.factor = 0.5; sm.iterations = 2
bpy.ops.object.shade_smooth()
# material: sea / neutral land / burned Central (deep red) / burned Allied (deep blue) / fire band / borders / relief shading
m = bpy.data.materials.new("M_Map"); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
p = N["Principled BSDF"]; p.inputs["Roughness"].default_value = 0.6
uv = N.new("ShaderNodeUVMap")
ti = N.new("ShaderNodeTexImage"); ti.image = st_img; ti.interpolation = 'Closest'; ti.extension = 'EXTEND'
th = N.new("ShaderNodeTexImage"); th.image = ht_img; th.extension = 'EXTEND'
L.new(uv.outputs["UV"], ti.inputs["Vector"]); L.new(uv.outputs["UV"], th.inputs["Vector"])
sep = N.new("ShaderNodeSeparateColor"); L.new(ti.outputs["Color"], sep.inputs["Color"])
R, G, B = sep.outputs[0], sep.outputs[1], sep.outputs[2]; A = ti.outputs["Alpha"]
tval = N.new("ShaderNodeValue"); tval.name = "WarTime"; tval.outputs[0].default_value = 0.0
def M_(op, x, y=None, clamp=False):
    n = N.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
    for i, v in enumerate((x, y)):
        if v is None: continue
        if isinstance(v, (int, float)): n.inputs[i].default_value = v
        else: L.new(v, n.inputs[i])
    return n.outputs[0]
def mix(fac, c1, c2):
    n = N.new("ShaderNodeMix"); n.data_type = 'RGBA'
    L.new(fac, n.inputs["Factor"])
    for sock, c in ((n.inputs["A"], c1), (n.inputs["B"], c2)):
        if isinstance(c, tuple): sock.default_value = (*c, 1)
        else: L.new(c, sock)
    return n.outputs["Result"]
T_ = tval.outputs[0]
valid = M_('LESS_THAN', R, 0.995)
burn = M_('MULTIPLY', M_('SUBTRACT', 1.0, M_('SMOOTH_MAX' if False else 'MAXIMUM', 0.0, M_('MULTIPLY', M_('SUBTRACT', R, T_), 120.0), ), clamp=True), valid)
# burn = clamp(1 - max(0, (R - T)*120)) * valid  -> 1 once the fire front passed the pixel
front = M_('MULTIPLY', M_('MULTIPLY', M_('GREATER_THAN', T_, R), M_('LESS_THAN', M_('SUBTRACT', T_, R), 0.014)), valid)
central = M_('LESS_THAN', G, 0.75)
war_col = mix(central, (0.12, 0.10, 0.80), (0.92, 0.05, 0.02))
land_col = mix(th.outputs["Color"], (0.20, 0.42, 0.08), (0.62, 0.42, 0.16))       # green lowland -> ochre highland
lc = mix(burn, land_col, war_col)
lc = mix(B, lc, (0.06, 0.04, 0.03))                                              # borders
sea = N.new("ShaderNodeTexNoise"); sea.inputs["Scale"].default_value = 60.0
sea_col = mix(sea.outputs["Fac"], (0.0, 0.17, 0.19), (0.0, 0.26, 0.27))
col = mix(A, sea_col, lc)
L.new(col, p.inputs["Base Color"])
fire = mix(N.new("ShaderNodeTexNoise").outputs["Fac"], (1.0, 0.18, 0.01), (1.0, 0.45, 0.03))
L.new(fire, p.inputs["Emission Color"])
es = M_('MULTIPLY', M_('MULTIPLY', front, A), 1.3)
L.new(es, p.inputs["Emission Strength"])
T.data.materials.append(m)
# WarTime keyed linear over the ignite window
for f, v in ((IGN0, 0.0), (IGN1, 1.0)):
    tval.outputs[0].default_value = v; tval.outputs[0].keyframe_insert("default_value", frame=f)
for fc in (m.node_tree.animation_data.action.fcurves if hasattr(m.node_tree.animation_data.action, "fcurves") else []):
    for k in fc.keyframe_points: k.interpolation = 'LINEAR'
try:
    act = m.node_tree.animation_data.action
    for layer in act.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    for k in fc.keyframe_points: k.interpolation = 'LINEAR'
except Exception: pass
# flags on poles: Austria-Hungary (red-white-red) at Vienna, Serbia (red-blue-white) at Belgrade; poles grow, cloth unfurls
KX = 111.32 * math.cos(math.radians(46.0)); KY = 111.0
def lonlat(lon, lat): return Vector(((lon - 18.41) * KX, (lat - 43.86) * KY, 0))
def h_at(v):
    u = (v.x - XMIN) / (XMAX - XMIN); w = (v.y - YMIN) / (YMAX - YMIN)
    W_, H_ = ht_img.size; px = ht_img.pixels
    i = int(min(H_ - 1, max(0, w * H_))) * W_ + int(min(W_ - 1, max(0, u * W_)))
    return ZTOP + px[i * 4] * HSCALE
FLAGS = [((16.37, 48.21), [(0.80, 0.03, 0.04), (0.96, 0.95, 0.92), (0.80, 0.03, 0.04)], 1462),
         ((20.46, 44.80), [(0.80, 0.03, 0.04), (0.03, 0.12, 0.55), (0.96, 0.95, 0.92)], 1480)]
pole_m = mat("M_FlagPole", (0.85, 0.75, 0.45), rough=0.3, metal=0.8)
for i, ((lon, lat), cols, f0) in enumerate(FLAGS):
    base = lonlat(lon, lat); base.z = h_at(base) - 1.0
    root = bpy.data.objects.new("MapFlag%d" % i, None); mc.objects.link(root); root.location = base
    pole = cyl("MapFlagPole%d" % i, 3.0, 170.0, base + Vector((0, 0, 85.0)), pole_m, verts=12); pole.parent = root
    pole.location = Vector((0, 0, 85.0))
    for k, c in enumerate(cols):
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=12, y_subdivisions=3, size=1.0, location=(0, 0, 0))
        fl = bpy.context.active_object; fl.name = "MapFlag%d_band%d" % (i, k)
        for cc in list(fl.users_collection): cc.objects.unlink(fl)
        mc.objects.link(fl)
        fl.data.transform(Matrix.Translation((0.5, 0.5, 0)))
        fl.parent = root; fl.rotation_euler = (math.radians(90), 0, 0)
        fl.location = (3.0, 0, 168.0 - (k + 1) * 26.0); fl.scale = (120.0, 26.0, 1)
        fl.data.materials.append(mat("M_MapFlag%d_%d" % (i, k), c, rough=0.6, sheen=0.4))
        wv = fl.modifiers.new("wave", 'WAVE'); wv.use_normal = True; wv.use_x = False; wv.use_y = False
        wv.height = 5.0; wv.width = 40.0; wv.speed = 0.6; wv.time_offset = -f0
        so = fl.modifiers.new("solid", 'SOLIDIFY'); so.thickness = 0.6
        for ff, sx in ((f0 + 18, 0.02), (f0 + 40, 120.0)):
            fl.scale.x = sx; fl.keyframe_insert("scale", index=0, frame=ff)
    for ff, sz in ((f0, 0.02), (f0 + 22, 1.0)):
        root.scale = (1, 1, sz) if ff == f0 else (1, 1, 1); root.keyframe_insert("scale", frame=ff)
# a cloud deck over the city (55-85 m): the camera rises through it; inside it the city is swapped for the map below
cloud_m = mat("M_Cloud", (0.97, 0.97, 1.0), rough=0.9, sheen=0.6, emit=((0.9, 0.93, 1.0), 0.35))
def soften(m, edge=0.85):
    """soft, volumetric-looking edges for puffs: mix toward transparent at grazing angles (fresnel)"""
    nt = m.node_tree; N = nt.nodes; L = nt.links
    out = N["Material Output"]; pr = N["Principled BSDF"]
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.45
    mr = N.new("ShaderNodeMath"); mr.operation = 'MULTIPLY'; mr.inputs[1].default_value = edge
    L.new(lw.outputs["Facing"], mr.inputs[0])
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(mr.outputs[0], mx.inputs[0]); L.new(pr.outputs[0], mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])
soften(cloud_m, 0.9)
import random as _r
rr = _r.Random(21)
CLOUDS = []
for i in range(30):
    ang = rr.uniform(0, 2 * math.pi); rad = rr.uniform(34.0, 140.0)
    c = Vector((1.6 + rad * math.cos(ang), 3.0 + rad * math.sin(ang), rr.uniform(64.0, 70.0)))
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1.0, location=c)
    o = bpy.context.active_object; o.name = "Cloud%02d" % i
    for cc in list(o.users_collection): cc.objects.unlink(o)
    mc.objects.link(o); o.data.materials.append(cloud_m)
    s_ = rr.uniform(12.0, 26.0); o.scale = (s_ * rr.uniform(1.0, 1.8), s_ * rr.uniform(1.0, 1.8), s_ * 0.22)
    tx = bpy.data.textures.new("cloud%d" % i, 'CLOUDS'); tx.noise_scale = 0.5
    dpp = o.modifiers.new("billow", 'DISPLACE'); dpp.texture = tx; dpp.strength = 0.35
    smm = o.modifiers.new("soft", 'SMOOTH'); smm.factor = 0.8; smm.iterations = 4
    bpy.ops.object.shade_smooth(); CLOUDS.append(o)
# the camera climbs straight through one big cloud at the swap (whiteout ~0.2 s), so the swap is never seen
camo = bpy.data.objects["CAM_Film"]; sc.frame_set(F_SHOW); cpos = camo.matrix_world.translation.copy()
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1.0, location=cpos)
core = bpy.context.active_object; core.name = "CloudCore"
for cc in list(core.users_collection): cc.objects.unlink(core)
mc.objects.link(core); core.data.materials.append(cloud_m); core.scale = (11.0, 11.0, 4.5)
tx = bpy.data.textures.new("cloudcore", 'CLOUDS'); tx.noise_scale = 0.5
dpp = core.modifiers.new("billow", 'DISPLACE'); dpp.texture = tx; dpp.strength = 0.25
smm = core.modifiers.new("soft", 'SMOOTH'); smm.factor = 0.8; smm.iterations = 4
bpy.ops.object.shade_smooth(); CLOUDS.append(core)
print("CLOUDCORE", tuple(round(c, 1) for c in cpos))
key_vis(CLOUDS, 1, False); key_vis(CLOUDS, 1440, True)
for o in CLOUDS:    # the deck thins out and is gone once the camera is above it (no blobs left on the map)
    s0 = o.scale.copy()
    o.keyframe_insert("scale", frame=1500)
    o.scale = s0 * 0.02; o.keyframe_insert("scale", frame=1524)
key_vis(CLOUDS, 1525, False)
# the city (set, people, cars, props, FX) is hidden from the moment the camera is inside the deck
city = [o for o in bpy.data.objects if o.type in ('MESH', 'CURVE', 'LIGHT') and o.name not in mc.objects and o.name != "Sun"]
sc.frame_set(F_SHOW - 1)
state = {o.name: o.hide_render for o in city}
for o in city:                       # keep each object's own visibility up to the swap (FX stay hidden until they fire)
    o.hide_render = o.hide_viewport = state[o.name]
    o.keyframe_insert("hide_render", frame=F_SHOW - 1); o.keyframe_insert("hide_viewport", frame=F_SHOW - 1)
key_vis(city, F_SHOW, False)
# visibility: the map exists only from the rise (the city keeps its own ground before)
key_vis([o for o in mc.objects if o not in CLOUDS], 1, False)
key_vis([o for o in mc.objects if o not in CLOUDS], F_SHOW, True)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("MAP_DONE", OUT)
