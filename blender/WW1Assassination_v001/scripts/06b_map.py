"""3D relief map of 1914 Europe (no text), fire spreading state by state on a keyed clock, flags on poles, marching columns,
smoke plumes and front-line flashes. Cloud layer for the city->map wipe. City objects hidden while the map shows.
blender -b scene.blend --python 06b_map.py -- <map.npz> <out.blend>"""
import sys, os, math, random
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "00_lib.py")).read())
exec(open(os.path.join(HERE, "00_story.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
NPZ, OUT = a[0], a[1]
sc = bpy.context.scene
random.seed(1918)
CM = coll("Map")
D = np.load(NPZ)
sid, hgt, ign, bord = D["sid"], D["height"], D["ignite"], D["border"]
XMIN, XMAX, YMIN, YMAX = [float(v) for v in D["ext"]]
LON0, LAT0, KX, KY = 18.41, 43.86, 7.98, 11.1
def ll(lon, lat): return Vector(((lon - LON0) * KX, (lat - LAT0) * KY))
STEP = 4
ny, nx = sid.shape
ys = list(range(0, ny, STEP)); xs = list(range(0, nx, STEP))
NXv, NYv = len(xs), len(ys)
H = hgt[::STEP, ::STEP]; S = sid[::STEP, ::STEP]; I = ign[::STEP, ::STEP]; B = bord[::STEP, ::STEP]
X = XMIN + (np.array(xs) + 0.5) / nx * (XMAX - XMIN); Y = YMAX - (np.array(ys) + 0.5) / ny * (YMAX - YMIN)
Z_MAP = 0.0
me = bpy.data.meshes.new("MapRelief")
GX, GY = np.meshgrid(X, Y)
verts = np.stack([GX.ravel(), GY.ravel(), (H.ravel() + Z_MAP)], 1).astype(np.float32)
qi = np.arange(NXv * NYv).reshape(NYv, NXv)
quads = np.stack([qi[:-1, :-1].ravel(), qi[1:, :-1].ravel(), qi[1:, 1:].ravel(), qi[:-1, 1:].ravel()], 1)
me.vertices.add(len(verts)); me.vertices.foreach_set("co", verts.ravel())
me.loops.add(quads.size); me.loops.foreach_set("vertex_index", quads.ravel().astype(np.int32))
me.polygons.add(len(quads)); me.polygons.foreach_set("loop_start", (np.arange(len(quads)) * 4).astype(np.int32))
me.update(calc_edges=True)
for nm, arr in (("ignite", I.ravel().astype(np.float32)), ("state", S.ravel().astype(np.float32)), ("border", B.ravel().astype(np.float32)),
                ("elev", H.ravel().astype(np.float32))):
    at = me.attributes.new(nm, 'FLOAT', 'POINT'); at.data.foreach_set("value", arr)
mp = bpy.data.objects.new("MapRelief", me); CM.objects.link(mp)
for p in me.polygons: p.use_smooth = True

# --- map material: terrain + state tints + borders + fire front on MapClock
M = bpy.data.materials.new("MapMat"); n, l = nodes_of(M); n.clear()
out = n.new('ShaderNodeOutputMaterial'); bs = n.new('ShaderNodeBsdfPrincipled'); bs.inputs['Roughness'].default_value = 0.85
def A(name):
    x = n.new('ShaderNodeAttribute'); x.attribute_name = name; x.attribute_type = 'GEOMETRY'; return x.outputs['Fac']
def math_(op, a_, b_=None, v=None):
    m = n.new('ShaderNodeMath'); m.operation = op
    l.new(a_, m.inputs[0]) if not isinstance(a_, float) else setattr(m.inputs[0], "default_value", a_)
    if b_ is not None:
        l.new(b_, m.inputs[1]) if not isinstance(b_, float) else setattr(m.inputs[1], "default_value", b_)
    return m.outputs[0]
elev = A("elev"); state = A("state"); bdr = A("border"); igt = A("ignite")
rock_d, _, rock_r = tex_files("aerial_rocks_02")
tc = n.new('ShaderNodeTexCoord'); mpn = n.new('ShaderNodeMapping'); mpn.inputs['Scale'].default_value = (0.08, 0.08, 0.08)
l.new(tc.outputs['Object'], mpn.inputs[0])
rt = n.new('ShaderNodeTexImage'); rt.image = img(rock_d); l.new(mpn.outputs[0], rt.inputs[0])
ramp = n.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
cr.elements[0].position = 0.0; cr.elements[0].color = (0.18, 0.24, 0.09, 1); cr.elements[1].position = 0.55; cr.elements[1].color = (0.42, 0.36, 0.22, 1)
e3 = cr.elements.new(0.85); e3.color = (0.55, 0.52, 0.48, 1)
e4 = cr.elements.new(1.0); e4.color = (0.92, 0.92, 0.95, 1)
l.new(math_('DIVIDE', elev, 4.0), ramp.inputs[0])
terr = n.new('ShaderNodeMix'); terr.data_type = 'RGBA'; terr.blend_type = 'OVERLAY'; terr.inputs['Factor'].default_value = 0.45
l.new(ramp.outputs[0], terr.inputs['A']); l.new(rt.outputs['Color'], terr.inputs['B'])
# state tint (muted parchment variety), neutral states stay plain
tint = n.new('ShaderNodeValToRGB'); tr = tint.color_ramp; tr.interpolation = 'CONSTANT'
CP_ = (0.62, 0.3, 0.26); EN_ = (0.3, 0.4, 0.62); NE_ = (0.62, 0.6, 0.52)
COLS = {k: (CP_ if k in (1, 4, 8, 9) else EN_) for k in range(1, 14)}; COLS[0] = NE_; COLS[20] = NE_
tr.elements[0].position = 0.0; tr.elements[0].color = (0.5, 0.5, 0.5, 1)
tr.elements[1].position = 0.999; tr.elements[1].color = (*COLS[20], 1)
for k in range(1, 14):
    e = tr.elements.new((k - 0.5) / 21.0); e.color = (*COLS[k], 1)
e = tr.elements.new(13.5 / 21.0); e.color = (*COLS[20], 1)
l.new(math_('DIVIDE', state, 21.0), tint.inputs[0])
mixt = n.new('ShaderNodeMix'); mixt.data_type = 'RGBA'; mixt.blend_type = 'MULTIPLY'; mixt.inputs['Factor'].default_value = 0.8
l.new(terr.outputs['Result'], mixt.inputs['A']); l.new(tint.outputs[0], mixt.inputs['B'])
bmix = n.new('ShaderNodeMix'); bmix.data_type = 'RGBA'; bmix.inputs['B'].default_value = (0.95, 0.9, 0.75, 1)
l.new(math_('MULTIPLY', bdr, 0.85), bmix.inputs['Factor']); l.new(mixt.outputs['Result'], bmix.inputs['A'])
# fire: clock - ignite (frames), noisy front
clock = n.new('ShaderNodeValue'); clock.name = "MapClock"; clock.label = "MapClock"
nz = n.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 0.09; nz.inputs['Detail'].default_value = 6
l.new(tc.outputs['Object'], nz.inputs['Vector']); l.new(math_('DIVIDE', clock.outputs[0], 45.0), nz.inputs['W'])
front = math_('SUBTRACT', math_('ADD', clock.outputs[0], math_('MULTIPLY', math_('SUBTRACT', nz.outputs['Fac'], 0.5), 50.0)), igt)
burn = math_('MINIMUM', math_('MAXIMUM', math_('DIVIDE', front, 25.0), 0.0), 1.0)
edge = math_('MULTIPLY', math_('MINIMUM', math_('MAXIMUM', math_('DIVIDE', front, 12.0), 0.0), 1.0),
             math_('MAXIMUM', math_('SUBTRACT', 1.0, math_('DIVIDE', front, 28.0)), 0.0))
fcol = n.new('ShaderNodeValToRGB'); fc = fcol.color_ramp
fc.elements[0].color = (0.8, 0.03, 0.0, 1); fc.elements[1].color = (1.0, 0.22, 0.0, 1)
l.new(nz.outputs['Fac'], fcol.inputs[0])
scorch = n.new('ShaderNodeMix'); scorch.data_type = 'RGBA'; scorch.inputs['B'].default_value = (0.07, 0.025, 0.015, 1)
l.new(math_('MULTIPLY', burn, 0.5), scorch.inputs['Factor']); l.new(bmix.outputs['Result'], scorch.inputs['A'])
l.new(scorch.outputs['Result'], bs.inputs['Base Color'])
l.new(fcol.outputs[0], bs.inputs['Emission Color'])
ember = math_('MULTIPLY', burn, math_('MINIMUM', math_('MAXIMUM', math_('MULTIPLY', math_('SUBTRACT', nz.outputs['Fac'], 0.56), 7.0), 0.0), 1.0))
l.new(math_('ADD', math_('MULTIPLY', edge, 3.5), math_('MULTIPLY', ember, 2.2)), bs.inputs['Emission Strength'])
l.new(bs.outputs[0], out.inputs[0])
me.materials.append(M)
for f, v in ((1, 1.0), (F_END_ := 2130, 2130.0)):
    clock.outputs[0].default_value = v; clock.outputs[0].keyframe_insert("default_value", frame=f)
for fcv in M.node_tree.animation_data.action.layers[0].strips[0].channelbags[0].fcurves:
    for kp in fcv.keyframe_points: kp.interpolation = 'LINEAR'

# sea
bm = bmesh.new(); add_box(bm, V(XMIN - 400, YMIN - 400, -3.0), V(XMAX + 400, YMAX + 400, -0.45), 0)
SEA = flat("MapSea", (0.012, 0.03, 0.06), rough=0.3)
sea = mesh_obj("MapSea", bm, [SEA], CM)
# a dark table base under the map edge
# --- flags on poles: Austria-Hungary (black/yellow) at Vienna, Serbia (red/blue/white) at Belgrade
def map_flag(name, lonlat, cols, t_pop):
    p = ll(*lonlat)
    hz = float(hgt[int((YMAX - p.y) / (YMAX - YMIN) * ny), int((p.x - XMIN) / (XMAX - XMIN) * nx)])
    root = bpy.data.objects.new(name, None); CM.objects.link(root); root.location = (p.x, p.y, hz); SC_ = 5.0
    bm = bmesh.new(); add_box(bm, V(-0.12, -0.12, 0), V(0.12, 0.12, 9.0), 0)
    pole = mesh_obj(name + "_Pole", bm, [flat("MapPole", (0.8, 0.7, 0.4), rough=0.3, metal=1.0)], CM); pole.parent = root
    bm = bmesh.new(); nseg = 16
    for j in range(nseg):
        for s_, c in enumerate(cols):
            z0, z1 = 8.8 - 3.6 * s_ / len(cols), 8.8 - 3.6 * (s_ + 1) / len(cols)
            x0, x1 = 5.4 * j / nseg, 5.4 * (j + 1) / nseg
            f = bm.faces.new([bm.verts.new(v) for v in ((x0, 0, z0), (x1, 0, z0), (x1, 0, z1), (x0, 0, z1))]); f.material_index = s_
    mats = [flat("MapFlag_" + c, rgb, rough=0.7) for c, rgb in cols_rgb(cols)]
    fl = mesh_obj(name + "_Cloth", bm, mats, CM); fl.parent = root
    wv = fl.modifiers.new("Flutter", 'WAVE'); wv.use_normal = False; wv.use_x = False; wv.use_y = True
    wv.height = 0.45; wv.width = 2.2; wv.speed = 0.15
    f0 = f_of(t_pop)
    for f, s_ in ((1, 0.0), (f0, 0.0), (f0 + 12, 1.25), (f0 + 20, 0.92), (f0 + 28, 1.0)):
        root.scale = (s_ * SC_ + 1e-3,) * 3; root.keyframe_insert("scale", frame=f)
    return root
def cols_rgb(cols):
    T = {"Black": (0.02, 0.02, 0.02), "Yellow": (0.9, 0.66, 0.05), "Red": (0.65, 0.04, 0.03), "Blue": (0.05, 0.12, 0.45), "White": (0.86, 0.86, 0.83)}
    return [(c, T[c]) for c in cols]
map_flag("Flag_AH", (16.37, 48.2), ("Black", "Yellow"), 29.55)
map_flag("Flag_SRB", (20.46, 44.8), ("Red", "Blue", "White"), 29.75)

# --- marching columns (tiny soldiers in blocks) along fronts/roads
SOLDIER = flat("MapSoldier", (0.12, 0.12, 0.1), rough=0.8)
def column(name, pts, t0, t1, nrow=8, ncol=3):
    bm = bmesh.new()
    for r in range(nrow):
        for c in range(ncol):
            x = (c - (ncol - 1) / 2) * 0.55; y = r * 0.7
            add_box(bm, V(x - 0.14, y - 0.14, 0), V(x + 0.14, y + 0.14, 0.75), 0)
    o = mesh_obj(name, bm, [SOLDIER], CM); o.scale = (2.5, 2.5, 2.5)
    P = [ll(*q) for q in pts]
    L = [0.0]
    for p0, p1 in zip(P, P[1:]): L.append(L[-1] + (p1 - p0).length)
    def at(u):
        d = u * L[-1]
        for i in range(len(P) - 1):
            if d <= L[i + 1] or i == len(P) - 2:
                v = (d - L[i]) / max(1e-6, L[i + 1] - L[i]); return P[i].lerp(P[i + 1], max(0, min(1, v))), (P[i + 1] - P[i])
    f0, f1 = f_of(t0), f_of(t1)
    for f in range(1, 2131, 6):
        u = max(0.0, min(1.0, (f - f0) / (f1 - f0)))
        p, dvec = at(u)
        ix = int((YMAX - p.y) / (YMAX - YMIN) * ny); iy = int((p.x - XMIN) / (XMAX - XMIN) * nx)
        hz = float(hgt[max(0, min(ny - 1, ix)), max(0, min(nx - 1, iy))])
        bob = 0.08 * abs(math.sin(f * 0.7))
        o.location = (p.x, p.y, max(hz, -0.4) + bob); o.rotation_euler = (0, 0, math.atan2(dvec.x, -dvec.y) + math.pi)
        o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
    return o
COLS_ = [("ColWest1", [(13.4, 52.5), (9.0, 51.0), (6.5, 50.6), (4.5, 50.4)], 30.4, 35.5),
         ("ColWest2", [(11.6, 48.1), (8.5, 48.6), (6.5, 48.9)], 30.6, 35.5),
         ("ColFr", [(2.35, 48.85), (4.0, 49.2), (5.5, 49.3)], 31.0, 35.5),
         ("ColEast1", [(30.3, 50.4), (27.0, 50.0), (24.5, 49.6)], 30.3, 35.5),
         ("ColEast2", [(21.0, 52.2), (21.5, 53.5), (21.8, 54.5)], 30.5, 35.5),
         ("ColBalk", [(16.37, 48.2), (18.0, 46.5), (19.5, 45.2)], 29.8, 34.5),
         ("ColSrb", [(20.46, 44.8), (20.0, 44.2), (19.6, 43.9)], 30.0, 34.0),
         ("ColUK", [(-0.1, 51.5), (1.3, 51.1), (2.2, 50.6), (3.2, 50.4)], 31.4, 35.5),
         ("ColOtt", [(32.8, 39.9), (30.0, 40.6), (28.9, 41.0)], 31.8, 35.5)]
for nm, pts, t0, t1 in COLS_: column(nm, pts, t0, t1)

# --- smoke plumes rising where the fire has passed, and front flashes
SMOKE = bpy.data.materials.new("MapSmoke"); n, l = nodes_of(SMOKE)
SMOKE.blend_method = 'BLEND' if hasattr(SMOKE, "blend_method") else None
bs_ = n["Principled BSDF"]; bs_.inputs['Base Color'].default_value = (0.42, 0.4, 0.38, 1); bs_.inputs['Roughness'].default_value = 1.0
tc2 = n.new('ShaderNodeTexCoord'); nz2 = n.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = 2.5; nz2.inputs['Detail'].default_value = 4
l.new(tc2.outputs['Object'], nz2.inputs['Vector'])
lw = n.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.45
fac = n.new('ShaderNodeMath'); fac.operation = 'SUBTRACT'; fac.inputs[0].default_value = 1.0; l.new(lw.outputs['Facing'], fac.inputs[1])
th = n.new('ShaderNodeMapRange'); th.inputs['From Min'].default_value = 0.35; th.inputs['From Max'].default_value = 0.7; l.new(nz2.outputs['Fac'], th.inputs['Value'])
m1 = n.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; l.new(fac.outputs[0], m1.inputs[0]); l.new(th.outputs['Result'], m1.inputs[1])
m2 = n.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; m2.inputs[1].default_value = 0.8; l.new(m1.outputs[0], m2.inputs[0]); l.new(m2.outputs[0], bs_.inputs['Alpha'])
land_pts = np.argwhere((sid > 0) & (sid < 14))
plumes = []
for k in range(46):
    iy, ix = land_pts[random.randrange(len(land_pts))]
    x = XMIN + (ix + 0.5) / nx * (XMAX - XMIN); y = YMAX - (iy + 0.5) / ny * (YMAX - YMIN)
    t_ig = float(ign[iy, ix])
    if t_ig > 2100: continue
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    o = mesh_obj(f"Plume_{k:02d}", bm, [SMOKE], CM); z0 = float(hgt[iy, ix]); o.visible_shadow = False
    for p_ in o.data.polygons: p_.use_smooth = True
    f0 = int(t_ig) + random.randint(10, 40)
    for f, sc_, dz in ((1, 0.01, 0), (f0, 0.01, 0), (f0 + 40, 3.5, 4), (f0 + 120, 7.0, 12), (2130, 9.0, 22)):
        o.location = (x, y, z0 + dz * 1.4); o.scale = (sc_ * 0.8, sc_ * 0.8, sc_ * 2.6)
        o.keyframe_insert("location", frame=f); o.keyframe_insert("scale", frame=f)
    plumes.append(o)
FL = flat("MapFlash", (1, 0.8, 0.5), emit=(1.0, 0.7, 0.35), emit_str=0.0)
FRONTS = [[(3.0, 51.2), (4.5, 50.0), (5.6, 49.2), (7.0, 48.2), (7.5, 47.6)], [(21.5, 54.6), (22.5, 52.0), (24.0, 50.0), (25.5, 48.2)],
          [(19.3, 44.9), (19.4, 44.0)]]
k = 0
for fr in FRONTS:
    for i in range(len(fr) - 1):
        for j in range(4):
            p = ll(*fr[i]).lerp(ll(*fr[i + 1]), (j + 0.5) / 4)
            bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.6)
            m = FL.copy(); m.name = f"MapFlash_{k}"
            o = mesh_obj(f"Flash_{k:02d}", bm, [m], CM); o.location = (p.x, p.y, 1.2)
            bsdf = next(x for x in m.node_tree.nodes if x.type == 'BSDF_PRINCIPLED')
            es = bsdf.inputs['Emission Strength']
            start = 1880 + random.randint(0, 80)
            for f in range(1, 2131, 4):
                v = 0.0
                if f > start and (f + k * 7) % 28 < 5: v = 40.0
                es.default_value = v; es.keyframe_insert("default_value", frame=f)
            for fcv in m.node_tree.animation_data.action.layers[0].strips[0].channelbags[0].fcurves:
                for kp in fcv.keyframe_points: kp.interpolation = 'CONSTANT'
            k += 1

# ================================================================ clouds and the city/map swap
SWAP_F = f_of(29.12)
bm = bmesh.new(); add_box(bm, V(-420, -380, 58), V(420, 420, 118), 0)
CLOUD = bpy.data.materials.new("Clouds"); n, l = nodes_of(CLOUD); n.clear()
o_ = n.new('ShaderNodeOutputMaterial'); pv = n.new('ShaderNodeVolumePrincipled')
tc = n.new('ShaderNodeTexCoord'); nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.035; nz.inputs['Detail'].default_value = 8
l.new(tc.outputs['Object'], nz.inputs['Vector'])
rmp = n.new('ShaderNodeMapRange'); rmp.inputs['From Min'].default_value = 0.45; rmp.inputs['From Max'].default_value = 0.68
l.new(nz.outputs['Fac'], rmp.inputs['Value'])
dens = n.new('ShaderNodeValue'); dens.name = "CloudDensity"
mul = n.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; l.new(rmp.outputs['Result'], mul.inputs[0]); l.new(dens.outputs[0], mul.inputs[1])
l.new(mul.outputs[0], pv.inputs['Density']); pv.inputs['Color'].default_value = (1, 1, 1, 1)
l.new(pv.outputs[0], o_.inputs['Volume'])
clouds = mesh_obj("CloudLayer", bm, [CLOUD], CM)
for f, v in ((1, 0.0), (f_of(27.6), 0.0), (f_of(28.6), 0.07), (SWAP_F - 6, 0.08), (SWAP_F + 6, 0.08), (f_of(29.8), 0.05), (f_of(30.6), 0.0), (2130, 0.0)):
    dens.outputs[0].default_value = v; dens.outputs[0].keyframe_insert("default_value", frame=f)
# whiteout near the swap: a camera-parented white card fades in/out (added in 05 where the camera exists)
sc["SWAP_F"] = SWAP_F
map_objs = [o for o in CM.objects if o.name != "CloudLayer"]
city = [o for o in bpy.data.objects if o.type in ('MESH', 'CURVE') and o not in CM.objects[:] and o.name not in ("CloudLayer",)]
def key_hide(o, f_show_from=None, f_hide_from=None):
    if f_show_from:   # hidden until f
        for f, h in ((1, True), (f_show_from, False)):
            o.hide_render = h; o.keyframe_insert("hide_render", frame=f)
    if f_hide_from:
        for f, h in ((1, False), (f_hide_from, True)):
            o.hide_render = h; o.keyframe_insert("hide_render", frame=f)
    ad = o.animation_data
    for layer in ad.action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fcv in cb.fcurves:
                    if fcv.data_path == "hide_render":
                        for kp in fcv.keyframe_points: kp.interpolation = 'CONSTANT'
for o in map_objs: key_hide(o, f_show_from=SWAP_F)
n_city = 0
for o in city:
    if o.hide_render: continue   # already hidden (crowd bases)
    if o.animation_data and o.animation_data.action and any(fc.data_path == "hide_render" for fc in
        [fc for layer in o.animation_data.action.layers for st in layer.strips for cb in st.channelbags for fc in cb.fcurves]):
        # already has visibility keys (pistol, bomb): add a final hide
        o.hide_render = True; o.keyframe_insert("hide_render", frame=SWAP_F); continue
    key_hide(o, f_hide_from=SWAP_F); n_city += 1
sun = bpy.data.objects["Key_Sun"]
for f, e in ((1, 3.6), (SWAP_F - 1, 3.6), (SWAP_F, 1.6), (2130, 1.6)):
    sun.data.energy = e; sun.data.keyframe_insert("energy", frame=f)
print("MAP_DONE verts", len(me.vertices), "city hidden", n_city, "swap", SWAP_F)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
