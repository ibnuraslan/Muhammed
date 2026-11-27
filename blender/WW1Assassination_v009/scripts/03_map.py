"""WW1Assassination v009 stage C: the 3D relief map of 1914 Europe under the city (1 m = 1 km, Sarajevo at the origin).
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
ZTOP = -3.6; HSCALE = 90.0
mc = bpy.data.collections.new("Map"); sc.collection.children.link(mc)
st_img = bpy.data.images.load(os.path.join(WD, "map_state.png")); st_img.colorspace_settings.name = 'Non-Color'
ht_img = bpy.data.images.load(os.path.join(WD, "map_height.png")); ht_img.colorspace_settings.name = 'Non-Color'
# terrain: one plane + simple subdivision + displacement by the relief image (small file, no stored dense mesh)
bpy.ops.mesh.primitive_grid_add(x_subdivisions=320, y_subdivisions=356, size=1.0, location=((XMIN + XMAX) / 2, (YMIN + YMAX) / 2, ZTOP))   # a real grid (16 km): previews with Simplify (subdiv 0) match the render
T = bpy.context.active_object; T.name = "MapTerrain"; T.scale = (XMAX - XMIN, YMAX - YMIN, 1)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)     # mesh in world coordinates (UV 0..1 = map extent)
for c in list(T.users_collection): c.objects.unlink(T)
mc.objects.link(T)
tex = bpy.data.textures.new("MapHeight", 'IMAGE'); tex.image = ht_img; tex.extension = 'EXTEND'
dp = T.modifiers.new("relief", 'DISPLACE'); dp.texture = tex; dp.texture_coords = 'UV'; dp.strength = HSCALE; dp.mid_level = 0.0
sm = T.modifiers.new("smooth", 'SMOOTH'); sm.factor = 0.5; sm.iterations = 2
bpy.ops.object.shade_smooth()
# material: sea / neutral land / burned Central (deep red) / burned Allied (deep blue) / fire band / borders / relief shading
m = bpy.data.materials.new("M_Map"); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
p = N["Principled BSDF"]; p.inputs["Roughness"].default_value = 0.6
uv = N.new("ShaderNodeUVMap")
ti = N.new("ShaderNodeTexImage"); ti.image = st_img; ti.interpolation = 'Linear'; ti.extension = 'EXTEND'
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
war_col = mix(central, (0.025, 0.04, 0.42), (0.50, 0.012, 0.004))
land_col = mix(th.outputs["Color"], (0.07, 0.22, 0.025), (0.34, 0.20, 0.05))       # green lowland -> ochre highland
lc = mix(burn, land_col, war_col)
lc = mix(B, lc, (0.06, 0.04, 0.03))                                              # borders
sea = N.new("ShaderNodeTexNoise"); sea.inputs["Scale"].default_value = 60.0
sea_col = mix(sea.outputs["Fac"], (0.0, 0.035, 0.09), (0.0, 0.06, 0.13))
col = mix(A, sea_col, lc)
col = mix(M_('MULTIPLY', front, A), col, (0.06, 0.012, 0.0))      # v009: a dark ember base under the fire band (blue + orange read as pink)
L.new(col, p.inputs["Base Color"])
fire = mix(N.new("ShaderNodeTexNoise").outputs["Fac"], (1.0, 0.16, 0.0), (1.0, 0.38, 0.0))
L.new(fire, p.inputs["Emission Color"])
es = M_('MULTIPLY', M_('MULTIPLY', front, A), 2.2)    # v009: a hot orange fire band (1.3 read as pale pink)
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
FLAGS = []   # v009: no flag poles (seen from straight above they read as grey bars)
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
# v009: no clouds (they gave white-out frames and blurry cloud shadows). The rise to the map is one move: the camera climbs
# while the whole city shrinks onto Sarajevo (the origin) on the flat map patch under it, so the street becomes a dot on Europe.
F_SHRINK0, F_SHRINK1 = 1446, 1560
F_SHOW = F_SHRINK1 + 1           # the city is hidden once it is far below one pixel
piv = bpy.data.objects.new("CityPivot", None); sc.collection.objects.link(piv)
city_roots = [o for o in bpy.data.objects if o.parent is None and o.name not in mc.objects and o.type != 'CAMERA' and o.name not in ("Sun", "CityPivot")]
for o in city_roots:
    o.parent = piv; o.matrix_parent_inverse = Matrix.Identity(4)
for f in range(F_SHRINK0, F_SHRINK1 + 1, 2):
    u = (f - F_SHRINK0) / (F_SHRINK1 - F_SHRINK0)
    k = math.exp(math.log(0.003) * (u ** 1.4))
    piv.scale = (k, k, k); piv.keyframe_insert("scale", frame=f)
print("CITY_PIVOT roots", len(city_roots))
# the city (set, people, cars, props, FX) is hidden from F_SHOW
city = [o for o in bpy.data.objects if o.type in ('MESH', 'CURVE', 'LIGHT') and o.name not in mc.objects and o.name != "Sun"]
sc.frame_set(F_SHOW - 1)
state = {o.name: o.hide_render for o in city}
for o in city:                       # keep each object's own visibility up to the swap (FX stay hidden until they fire)
    o.hide_render = o.hide_viewport = state[o.name]
    o.keyframe_insert("hide_render", frame=F_SHOW - 1); o.keyframe_insert("hide_viewport", frame=F_SHOW - 1)
key_vis(city, F_SHOW, False)
# the map is there from the start of the rise (flat at -3.6 m under the set, below the river bed)
key_vis(list(mc.objects), 1, False)
key_vis(list(mc.objects), 1432, True)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("MAP_DONE", OUT)
