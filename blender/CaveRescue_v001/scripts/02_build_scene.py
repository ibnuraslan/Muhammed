"""CaveRescue sets: S1 jungle hillside + cave mouth, S2 entrance tunnel, S3 1:100 mountain cross-section,
S4 chamber ledge + pool, S5 flooded passage under the pool. Render settings, world, props.

blender -b chars.blend --python 02_build_scene.py -- <assets_dir> <out.blend>
"""
import sys, os, math, random, glob
import bpy, bmesh
from mathutils import Vector, Matrix, noise

argv = sys.argv[sys.argv.index("--") + 1:]
A, OUT = argv[0], argv[1]
sc = bpy.context.scene
FPS, END = 60, 3090
random.seed(23)
R_ = math.radians
V = Vector

# ------------------------------------------------------------------ timeline / render
sc.render.fps, sc.render.fps_base = FPS, 1.0
sc.frame_start, sc.frame_end = 1, END
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.engine = 'CYCLES'
c = sc.cycles
c.device = 'CPU'; c.samples = 48; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.05
c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'
c.max_bounces = 8; c.diffuse_bounces = 3; c.glossy_bounces = 3; c.transmission_bounces = 8; c.volume_bounces = 1
c.caustics_reflective = c.caustics_refractive = False
c.volume_step_rate = 4.0; c.volume_max_steps = 256
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.render.use_persistent_data = True
vs = sc.view_settings
vs.view_transform = 'AgX'; vs.look = 'AgX - Medium High Contrast'; vs.exposure = 0.0
im = sc.render.image_settings
im.file_format = 'PNG'; im.color_mode = 'RGB'; im.color_depth = '8'; im.compression = 15
sc.render.filepath = "//render/CaveRescue_v001_"

# ------------------------------------------------------------------ helpers
def coll(name):
    c_ = bpy.data.collections.new(name); sc.collection.children.link(c_); return c_
S1, S2, S3, S4, PROPS, FX = coll("S1_Hillside"), coll("S2_Tunnel"), coll("S3_CrossSection"), coll("S4S5_Chamber_Passage"), coll("Props"), coll("FX")

def link(o, cl):
    for c_ in o.users_collection: c_.objects.unlink(o)
    cl.objects.link(o); return o

def img(path, nc=False):
    i = bpy.data.images.load(path, check_existing=True)
    if nc: i.colorspace_settings.name = 'Non-Color'
    return i

def tex_files(asset):
    d = os.path.join(A, asset, "textures")
    def f(k):
        g = sorted(glob.glob(os.path.join(d, "%s_%s_1k.*" % (asset, k))))
        return g[0] if g else None
    return f("diff"), f("rough"), f("nor_gl")

def pbr(name, asset, scale, sat=1.0, val=1.0, bump=1.0, rough_mul=1.0, coord='Object'):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    p = n["Principled BSDF"]
    dif, rou, nor = tex_files(asset)
    tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / scale,) * 3
    l.new(tc.outputs[coord], mp.inputs['Vector'])
    d = n.new('ShaderNodeTexImage'); d.image = img(dif); d.projection = 'BOX'; d.projection_blend = 0.3
    hsv = n.new('ShaderNodeHueSaturation'); hsv.name = "HSV"; hsv.inputs['Saturation'].default_value = sat; hsv.inputs['Value'].default_value = val
    l.new(mp.outputs['Vector'], d.inputs['Vector']); l.new(d.outputs['Color'], hsv.inputs['Color']); l.new(hsv.outputs['Color'], p.inputs['Base Color'])
    if rou:
        r = n.new('ShaderNodeTexImage'); r.image = img(rou, True); r.projection = 'BOX'; r.projection_blend = 0.3
        rm = n.new('ShaderNodeMath'); rm.operation = 'MULTIPLY'; rm.inputs[1].default_value = rough_mul; rm.use_clamp = True
        l.new(mp.outputs['Vector'], r.inputs['Vector']); l.new(r.outputs['Color'], rm.inputs[0]); l.new(rm.outputs[0], p.inputs['Roughness'])
    if nor:
        nm = n.new('ShaderNodeTexImage'); nm.image = img(nor, True); nm.projection = 'BOX'; nm.projection_blend = 0.3
        nmap = n.new('ShaderNodeNormalMap'); nmap.inputs['Strength'].default_value = bump
        l.new(mp.outputs['Vector'], nm.inputs['Vector']); l.new(nm.outputs['Color'], nmap.inputs['Color']); l.new(nmap.outputs['Normal'], p.inputs['Normal'])
    return m

def flat(name, rgb, rough=0.5, metal=0.0, emit=None, estr=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*rgb, 1); p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    if emit:
        p.inputs['Emission Color'].default_value = (*emit, 1); p.inputs['Emission Strength'].default_value = estr
    return m

def emis(name, rgb, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n = m.node_tree.nodes; n.clear()
    o = n.new('ShaderNodeOutputMaterial'); e = n.new('ShaderNodeEmission'); e.name = "Emit"
    e.inputs['Color'].default_value = (*rgb, 1); e.inputs['Strength'].default_value = strength
    m.node_tree.links.new(e.outputs[0], o.inputs['Surface'])
    return m

def mix_mud(m, mud_asset, mask_attr):
    """mix a mud layer into material m by a vertex colour attribute"""
    n, l = m.node_tree.nodes, m.node_tree.links
    p = n["Principled BSDF"]
    dif, rou, nor = tex_files(mud_asset)
    at = n.new('ShaderNodeAttribute'); at.attribute_name = mask_attr
    tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.7, 0.7, 0.7)
    l.new(tc.outputs['Object'], mp.inputs['Vector'])
    d = n.new('ShaderNodeTexImage'); d.image = img(dif); d.projection = 'BOX'; l.new(mp.outputs['Vector'], d.inputs['Vector'])
    hs = n.new('ShaderNodeHueSaturation'); hs.inputs['Value'].default_value = 0.6; l.new(d.outputs['Color'], hs.inputs['Color'])
    mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    src = p.inputs['Base Color'].links[0].from_socket
    l.new(at.outputs['Fac'], mx.inputs['Factor']); l.new(src, mx.inputs['A']); l.new(hs.outputs['Color'], mx.inputs['B'])
    l.new(mx.outputs['Result'], p.inputs['Base Color'])
    rr = n.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = 0.75; rr.inputs['To Max'].default_value = 0.25
    l.new(at.outputs['Fac'], rr.inputs['Value'])
    if p.inputs['Roughness'].links:
        mul = n.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
        l.new(p.inputs['Roughness'].links[0].from_socket, mul.inputs[0]); l.new(rr.outputs['Result'], mul.inputs[1])
        l.new(mul.outputs[0], p.inputs['Roughness'])
    else:
        l.new(rr.outputs['Result'], p.inputs['Roughness'])

def load_lib(asset, names=None):
    with bpy.data.libraries.load(os.path.join(A, asset, asset + "_1k.blend"), link=False) as (src, dst):
        dst.objects = [n for n in src.objects if (names is None or n in names)]
    return [o for o in dst.objects if o]

def inst(src, name, loc, rz=0.0, s=1.0, cl=None, tilt=(0, 0)):
    o = bpy.data.objects.new(name, src.data)
    o.location = loc; o.rotation_euler = (tilt[0], tilt[1], rz); o.scale = (s, s, s)
    (cl or sc.collection).objects.link(o); return o

def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)

def grid_mesh(name, x0, x1, y0, y1, nx, ny, hfun, cl, solid=None):
    bm = bmesh.new()
    vs_ = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx; y = y0 + (y1 - y0) * j / ny
            row.append(bm.verts.new((x, y, hfun(x, y))))
        vs_.append(row)
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((vs_[j][i], vs_[j][i + 1], vs_[j + 1][i + 1], vs_[j + 1][i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); cl.objects.link(o)
    for pg in me.polygons: pg.use_smooth = True
    if solid:
        md = o.modifiers.new("Solid", 'SOLIDIFY'); md.thickness = solid; md.offset = -1
    return o

def tube_mesh(name, pts, radius_fn, cl, ring=40, step=0.5, noise_amp=0.25, floor_flat=True, height=1.0, closed=False, seed=0.0):
    """rock tube along polyline pts (floor at the centreline z); radius_fn(t)->(half_width, height)"""
    # resample centreline (Catmull-Rom)
    P = [V(p) for p in pts]
    def cr(i, t):
        p0 = P[max(i - 1, 0)]; p1 = P[i]; p2 = P[min(i + 1, len(P) - 1)]; p3 = P[min(i + 2, len(P) - 1)]
        return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
    dense = []
    for i in range(len(P) - 1):
        n_ = max(2, int((P[i + 1] - P[i]).length / step))
        for k in range(n_):
            dense.append(cr(i, k / n_))
    dense.append(P[-1])
    L = [0.0]
    for a, b in zip(dense, dense[1:]): L.append(L[-1] + (b - a).length)
    bm = bmesh.new(); rings = []
    mud = bm.loops.layers.color.new("mud")
    for k, p in enumerate(dense):
        t = L[k] / L[-1]
        fw = (dense[min(k + 1, len(dense) - 1)] - dense[max(k - 1, 0)]); fw.z = 0; fw.normalize()
        side = fw.cross(V((0, 0, 1))).normalized()
        hw, hh = radius_fn(t)
        rr = []
        for j in range(ring):
            th = 2 * math.pi * j / ring
            cx, cz = math.cos(th), math.sin(th)
            x_ = hw * cx; z_ = hh * 0.5 + hh * 0.55 * cz
            if floor_flat and z_ < 0.0: z_ = 0.0 + 0.04 * (1 - abs(cx))
            q = p + side * x_ + V((0, 0, z_))
            nrm = (side * cx + V((0, 0, cz))).normalized()
            amp = noise_amp * (0.35 if z_ <= 0.05 else 1.0)
            dn = noise.noise(q * 0.6 + V((seed, 0, 0))) * amp + noise.noise(q * 2.1 + V((0, seed, 0))) * amp * 0.35
            q = q + nrm * dn
            rr.append(bm.verts.new(q))
        rings.append(rr)
    for k in range(len(rings) - 1):
        for j in range(ring):
            f = bm.faces.new((rings[k][j], rings[k][(j + 1) % ring], rings[k + 1][(j + 1) % ring], rings[k + 1][j]))
    if closed:
        bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        for lp in f.loops:
            z_rel = lp.vert.co.z
            lp[mud] = (1, 1, 1, 1)
    bm.normal_update()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); cl.objects.link(o)
    for pg in me.polygons: pg.use_smooth = True
    return o, dense

def set_mud_by_height(o, path_pts, h_mud=0.45):
    """vertex colour 'mud' = 1 near the floor of the tube (height above nearest centreline point)"""
    me = o.data
    if "mud" not in me.color_attributes:
        me.color_attributes.new("mud", 'BYTE_COLOR', 'CORNER')
    ca = me.color_attributes["mud"]
    from mathutils.kdtree import KDTree
    kd = KDTree(len(path_pts))
    for i, p in enumerate(path_pts): kd.insert(V((p.x, p.y, 0)), i)
    kd.balance()
    for lp in me.loops:
        co = me.vertices[lp.vertex_index].co
        _, i, _ = kd.find(V((co.x, co.y, 0)))
        h = co.z - path_pts[i].z
        v = 1.0 - smoothstep(0.1, h_mud, h)
        ca.data[lp.index].color = (v, v, v, 1)

def boolean_cut(target, cutter, solver='MANIFOLD'):
    md = target.modifiers.new("Cut", 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = cutter; md.solver = solver
    bpy.context.view_layer.objects.active = target
    for o in bpy.context.selected_objects: o.select_set(False)
    target.select_set(True)
    bpy.ops.object.modifier_apply(modifier=md.name)

def apply_mods(o):
    bpy.context.view_layer.objects.active = o
    for m in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)

# ================================================================== WORLD (keyable sky strength / tint)
w = bpy.data.worlds.new("World_Cave"); sc.world = w; w.use_nodes = True
wn, wl = w.node_tree.nodes, w.node_tree.links; wn.clear()
wo = wn.new('ShaderNodeOutputWorld')
wt = wn.new('ShaderNodeTexEnvironment'); wt.image = img(os.path.join(A, "hdri", "forest_slope_2k.hdr"))
wmap = wn.new('ShaderNodeMapping'); wtc = wn.new('ShaderNodeTexCoord')
wmap.inputs['Rotation'].default_value = (0, 0, R_(200))
wl.new(wtc.outputs['Generated'], wmap.inputs['Vector']); wl.new(wmap.outputs['Vector'], wt.inputs['Vector'])
tint = wn.new('ShaderNodeMix'); tint.name = "SkyTint"; tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'
tint.inputs['Factor'].default_value = 1.0; tint.inputs['B'].default_value = (1, 1, 1, 1)
bg = wn.new('ShaderNodeBackground'); bg.name = "SkyStrength"; bg.inputs['Strength'].default_value = 1.0
wl.new(wt.outputs['Color'], tint.inputs['A']); wl.new(tint.outputs['Result'], bg.inputs['Color']); wl.new(bg.outputs[0], wo.inputs['Surface'])

sun = bpy.data.objects.new("Key_Sun", bpy.data.lights.new("Key_Sun", 'SUN'))
sun.data.energy = 3.0; sun.data.angle = R_(3); sun.rotation_euler = (R_(50), R_(10), R_(-30)); S1.objects.link(sun)

# ================================================================== S1: hillside + cliff
def H1(x, y):
    base = 0.6 * noise.noise(V((x * 0.05, y * 0.05, 0.3))) + 0.12 * noise.noise(V((x * 0.4, y * 0.4, 1.7)))
    path = math.exp(-((x - 0.25 * math.sin(y * 0.15)) ** 2) / 8.0)          # trodden path to the mouth
    base -= 0.25 * path
    side_hills = 6.0 * smoothstep(14, 40, abs(x)) * (1 + 0.5 * noise.noise(V((x * 0.03, y * 0.03, 5))))
    yy = y + 0.8 * noise.noise(V((x * 0.15, 0, 2)))
    cliff = 6.0 * smoothstep(-3.0, 0.5, yy) + 20.0 * smoothstep(0.0, 16.0, yy) + 1.5 * noise.noise(V((x * 0.2, y * 0.2, 3))) * smoothstep(-1, 3, y)
    top = 0.0 if y < 2 else 5.0 * smoothstep(2, 40, y) + 2.5 * noise.noise(V((x * 0.06, y * 0.06, 9)))
    return base + side_hills + cliff + top - 0.04 * y * (y < -2)
terrain = grid_mesh("S1_Terrain", -60, 60, -70, 50, 180, 180, H1, S1, solid=40.0)
m_ground = pbr("M_JungleGround", "leaves_forest_ground", 3.0, sat=1.0, val=0.7, bump=0.8, rough_mul=0.7)
m_cliff = pbr("M_Limestone", "mossy_rock", 5.0, sat=1.0, val=0.8, bump=1.0, rough_mul=0.6)
# ground vs cliff by slope: use geometry normal in the shader
for m_ in (m_ground,):
    pass
m_hill = bpy.data.materials.new("M_Hill"); m_hill.use_nodes = True
hn, hl = m_hill.node_tree.nodes, m_hill.node_tree.links; hn.clear()
ho = hn.new('ShaderNodeOutputMaterial')
g1 = hn.new('ShaderNodeGroup')
# simple: mix two principled via normal z
def mat_to_group_shader(m):
    return m
geo = hn.new('ShaderNodeNewGeometry'); sep = hn.new('ShaderNodeSeparateXYZ'); hl.new(geo.outputs['Normal'], sep.inputs['Vector'])
mr = hn.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.55; mr.inputs['From Max'].default_value = 0.8
hl.new(sep.outputs['Z'], mr.inputs['Value'])
hn.remove(g1)
mixs = hn.new('ShaderNodeMixShader'); hl.new(mr.outputs['Result'], mixs.inputs['Fac'])
# copy the node trees of the two PBR materials into this one
def graft(src_m, tgt_nt):
    mapping = {}
    for nd in src_m.node_tree.nodes:
        if nd.type == 'OUTPUT_MATERIAL': continue
        nn = tgt_nt.nodes.new(nd.bl_idname)
        for k in ('image', 'projection', 'projection_blend', 'operation', 'use_clamp', 'data_type', 'blend_type'):
            if hasattr(nd, k):
                try: setattr(nn, k, getattr(nd, k))
                except Exception: pass
        for i, s in enumerate(nd.inputs):
            if hasattr(s, 'default_value') and i < len(nn.inputs):
                try: nn.inputs[i].default_value = s.default_value
                except Exception: pass
        mapping[nd.name] = nn
    for lk in src_m.node_tree.links:
        if lk.to_node.type == 'OUTPUT_MATERIAL': continue
        a = mapping[lk.from_node.name]; b = mapping[lk.to_node.name]
        tgt_nt.links.new(a.outputs[lk.from_socket.identifier] if lk.from_socket.identifier in a.outputs else a.outputs[list(lk.from_node.outputs).index(lk.from_socket)],
                         b.inputs[list(lk.to_node.inputs).index(lk.to_socket)])
    return mapping["Principled BSDF"]
pc = graft(m_cliff, m_hill.node_tree); pg_ = graft(m_ground, m_hill.node_tree)
hl.new(pc.outputs[0], mixs.inputs[1]); hl.new(pg_.outputs[0], mixs.inputs[2]); hl.new(mixs.outputs[0], ho.inputs['Surface'])
terrain.data.materials.append(m_hill)

# ================================================================== S2: entrance tunnel (floor = centreline z)
TUN = [(0, -7, 0.25), (0, -2, 0.2), (0.4, 4, 0.0), (1.8, 11, -0.4), (2.6, 18, -0.9), (1.5, 26, -1.4), (-0.8, 33, -1.8), (-1.5, 41, -2.1), (0, 50, -2.3)]
def tun_r(t):
    return (2.3 + 0.5 * math.sin(t * 17.0), 3.4 + 0.6 * math.sin(t * 11.0 + 1))
tun_cut, _ = tube_mesh("CUT_Tunnel", TUN[:4], lambda t: (2.1 + 0.25 * math.sin(t * 40), 3.2), S2, step=0.5, noise_amp=0.35, closed=True, seed=3.0)
tunnel, TUN_D = tube_mesh("S2_Tunnel", [(0, -4.0, 0.2)] + TUN[2:], tun_r, S2, noise_amp=0.32, seed=3.0)
_bm = bmesh.new(); _bm.from_mesh(tunnel.data)
_kill = [f for f in _bm.faces if all(v.co.z > H1(v.co.x, v.co.y) + 0.15 for v in f.verts) or all(v.co.y < -3.0 for v in f.verts)]
bmesh.ops.delete(_bm, geom=_kill, context='FACES'); _bm.to_mesh(tunnel.data); _bm.free()
apply_mods(terrain)
boolean_cut(terrain, tun_cut)
bpy.data.objects.remove(tun_cut, do_unlink=True)
m_tun = pbr("M_TunnelRock", "rock_surface", 3.0, sat=0.6, val=0.75, bump=1.2, rough_mul=0.5)
mix_mud(m_tun, "brown_mud_02", "mud")
set_mud_by_height(tunnel, TUN_D, 0.5)
tunnel.data.materials.append(m_tun)
sc["TUN"] = [list(p) for p in TUN]

# mouth dressing: scanned rock faces and mossy boulders around the opening (hides the cut seam)
moss = load_lib("rock_moss_set_01")
boul = load_lib("boulder_01", ["boulder_01_LOD2"])[0]
for i, (x, y, s) in enumerate(((-3.4, -2.2, 1.3), (3.5, -2.0, 1.4), (-4.8, -1.0, 1.6), (4.9, -0.8, 1.5), (-2.6, -0.6, 1.0), (2.8, -0.4, 1.1))):
    inst(random.choice(moss), "S1_MouthRock_%d" % i, (x, y, H1(x, y) - 0.3), random.uniform(0, 6.3), s, S1)
for i in range(40):
    a = random.uniform(0, 2 * math.pi); r = random.uniform(5, 26)
    x, y = r * math.cos(a), -abs(r * math.sin(a)) - 2.5
    if abs(x) < 2.0 and y > -16: x += 3.2 * (1 if x >= 0 else -1)
    src = random.choice(moss + [boul])
    inst(src, "S1_Rock_%d" % i, (x, y, H1(x, y) - 0.25), random.uniform(0, 6.3), random.uniform(0.5, 1.3), S1)
for o in moss + [boul]:
    for c_ in o.users_collection: c_.objects.unlink(o)
# vegetation
trees = [o for o in load_lib("island_tree_01", ["island_tree_01_LOD1"]) + load_lib("island_tree_02", ["island_tree_02_LOD1"])]
ferns = load_lib("fern_02")
shrubs = load_lib("shrub_02", ["shrub_02_a_LOD1", "shrub_02_b_LOD1", "shrub_02_c_LOD1", "shrub_02_d_LOD1"])
for o in trees + ferns + shrubs:
    for c_ in o.users_collection: c_.objects.unlink(o)
TREES = []
for i in range(150):
    for _ in range(20):
        x = random.uniform(-55, 55); y = random.uniform(-65, 45)
        if abs(x) < 5.5 and -34 < y < 1.5: continue      # keep the path open
        if abs(x) < 12 and -30 < y < -8: continue        # rescue clearing
        if -3.5 < y < 2 and abs(x) < 6: continue         # mouth
        break
    s = random.uniform(2.0, 3.4)
    t = inst(random.choice(trees), "S1_Tree_%d" % i, (x, y, H1(x, y) - 0.2), random.uniform(0, 6.3), s, S1); TREES.append(t)
for i in range(1100):
    x = random.gauss(0, 12); y = random.uniform(-45, 25)
    if abs(x - 0.25 * math.sin(y * 0.15)) < 1.5 and y < 0: continue
    if -3.5 < y < 1.0 and abs(x) < 3.0: continue
    if abs(x) < 9 and -30 < y < -9 and random.random() < 0.8: continue
    src = random.choice(ferns + shrubs)
    inst(src, "S1_Plant_%d" % i, (x, y, H1(x, y) - 0.03), random.uniform(0, 6.3), random.uniform(0.9, 2.2) * (1.0 if src in ferns else 0.9), S1)
# vines hanging over the mouth (thin curves)
m_vine = flat("M_Vine", (0.08, 0.16, 0.05), 0.6)
for i in range(14):
    cu = bpy.data.curves.new("Vine%d" % i, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.012
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(2)
    x = random.uniform(-3.5, 3.5); y = -1.5 + random.uniform(-0.3, 0.6); z0 = 4.2 + random.uniform(0, 1.5)
    for k, bp in enumerate(sp.bezier_points):
        bp.co = (x + random.uniform(-0.15, 0.15), y - 0.1 * k, z0 - k * random.uniform(0.6, 1.0)); bp.handle_left_type = bp.handle_right_type = 'AUTO'
    o = bpy.data.objects.new("S1_Vine_%d" % i, cu); S1.objects.link(o); cu.materials.append(m_vine)

# bikes leaning on the rocks left of the mouth (generic, no markings)
m_frame = [flat("M_BikeRed", (0.45, 0.06, 0.05), 0.35, 0.6), flat("M_BikeBlue", (0.05, 0.12, 0.4), 0.35, 0.6), flat("M_BikeBlack", (0.03, 0.03, 0.03), 0.4, 0.5)]
m_tyre = flat("M_Tyre", (0.02, 0.02, 0.02), 0.8)
def bike(name, loc, rz, mat):
    parts = []
    for wx in (-0.52, 0.52):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.33, minor_radius=0.025, location=(wx, 0, 0.35), rotation=(R_(90), 0, 0))
        t = bpy.context.active_object; t.data.materials.append(m_tyre); parts.append(t)
    def bar(a, b, r=0.018):
        a, b = V(a), V(b); d = b - a
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, location=(a + b) / 2)
        o = bpy.context.active_object; o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); o.data.materials.append(mat); parts.append(o)
    seat, bb, head, rear, front = (-0.18, 0, 0.82), (-0.05, 0, 0.32), (0.38, 0, 0.8), (-0.52, 0, 0.35), (0.52, 0, 0.35)
    bar(seat, bb); bar(bb, head); bar(seat, head); bar(bb, rear); bar(seat, rear); bar(head, front); bar(head, (0.34, 0, 0.98))
    bar((0.28, -0.24, 0.98), (0.28, 0.24, 0.98), 0.014)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.2, 0, 0.86)); s_ = bpy.context.active_object; s_.scale = (0.22, 0.09, 0.04); s_.data.materials.append(m_tyre); parts.append(s_)
    for o in bpy.context.selected_objects: o.select_set(False)
    for p in parts: p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join()
    b = bpy.context.active_object; b.name = name
    b.location = loc; b.rotation_euler = (R_(12), 0, rz); link(b, PROPS); return b
for i, (x, y, rz) in enumerate(((-2.7, -4.2, R_(70)), (-3.3, -5.0, R_(64)), (-3.8, -6.1, R_(58)), (2.9, -4.6, R_(-72)), (3.4, -5.6, R_(-66)))):
    bike("Bike_%d" % i, (x, y, H1(x, y) + 0.02), rz, m_frame[i % 3])

# ================================================================== S3: 1:100 mountain cross-section at x = DX
DX = -400.0
prof_top = [(-6, 0), (-3, 1.5), (0, 4.5), (3, 7.0), (6, 8.5), (9, 11.0), (12, 12.5), (15, 11.5), (18, 13.5), (21, 15.0), (24, 13.0),
            (27, 14.2), (30, 12.0), (33, 10.5), (36, 9.0), (39, 7.0), (42, 5.0), (45, 2.0), (48, 0)]
bm = bmesh.new()
top = [bm.verts.new((DX, y, z + (0.25 * noise.noise(V((y * 0.4, 0, 1))) if 0 < z else 0))) for y, z in prof_top]
bot = [bm.verts.new((DX, y, -3.0)) for y, z in prof_top[::-1]]
face = bm.faces.new(top + bot)
ex = bmesh.ops.extrude_face_region(bm, geom=[face])
for v in [e for e in ex['geom'] if isinstance(e, bmesh.types.BMVert)]: v.co.x += 22.0
bm.normal_update()
me = bpy.data.meshes.new("S3_Mountain"); bm.to_mesh(me); bm.free()
mountain = bpy.data.objects.new("S3_Mountain", me); S3.objects.link(mountain)
md = mountain.modifiers.new("Rem", 'TRIANGULATE')
# route through the mountain (cut face plane), sumps are the low U-bends
ROUTE = [(0.2, 0.9), (3.0, 0.8), (5.5, 0.3), (7.0, -0.9), (8.6, 0.25), (11.0, 0.9), (14.0, 0.7), (16.0, -0.6), (18.0, 0.6),
         (21.0, 1.2), (24.0, 1.0), (26.0, -0.3), (27.6, -1.1), (29.4, 0.0), (31.5, 1.1), (34.0, 1.6), (36.5, 1.9)]
ROUTE3 = [V((DX, y, z)) for y, z in ROUTE]
cut3, R3D = tube_mesh("CUT_Route", [(DX, -2.0, 0.9)] + [(p.x, p.y, p.z - 0.25) for p in ROUTE3] + [(DX, 38.4, 1.65)],
                      lambda t: (0.55, 0.7), S3, ring=24, step=0.3, noise_amp=0.06, floor_flat=False, closed=True)
# chamber bulge at the far end
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(DX, 37.6, 2.1), segments=24, ring_count=12)
ch = bpy.context.active_object; ch.scale = (0.9, 1.6, 0.9); apply_mods(ch)
m_void = flat("M_CaveVoid", (0.07, 0.06, 0.055), 0.6)
for o in (cut3, ch): o.data.materials.append(m_void)
m_strata = pbr("M_Strata", "aerial_rocks_02", 8.0, sat=0.5, val=0.9, bump=0.6)
# strata bands on the cut face
sn, sl = m_strata.node_tree.nodes, m_strata.node_tree.links
wv = sn.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'; wv.inputs['Scale'].default_value = 0.35
wv.inputs['Distortion'].default_value = 6.0; wv.inputs['Detail'].default_value = 4
ramp = sn.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = (0.32, 0.29, 0.25, 1); ramp.color_ramp.elements[1].color = (0.62, 0.58, 0.5, 1)
mx = sn.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 0.85
p_ = sn["Principled BSDF"]; src = p_.inputs['Base Color'].links[0].from_socket
sl.new(wv.outputs['Fac'], ramp.inputs['Fac']); sl.new(src, mx.inputs['A']); sl.new(ramp.outputs['Color'], mx.inputs['B']); sl.new(mx.outputs['Result'], p_.inputs['Base Color'])
mountain.data.materials.append(m_strata)
apply_mods(mountain)
md = mountain.modifiers.new("Cut", 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.solver = 'MANIFOLD'
md.operand_type = 'COLLECTION'
cc_ = bpy.data.collections.new("CUTTERS3"); sc.collection.children.link(cc_)
for o in (cut3, ch): link(o, cc_)
md.collection = cc_
apply_mods(mountain)
for o in (cut3, ch): bpy.data.objects.remove(o, do_unlink=True)
bpy.data.collections.remove(cc_)
# green jungle skin on the outer top surface: faces whose normal points up
mountain.data.materials.append(pbr("M_MiniJungle", "forest_ground_04", 0.6, sat=1.4, val=0.55))
for pg in mountain.data.polygons:
    if pg.normal.z > 0.35 and pg.center.x > DX + 0.05: pg.material_index = len(mountain.data.materials) - 1
# tiny trees on the ridge (1:100)
for i in range(120):
    y = random.uniform(-4, 46); x = DX + random.uniform(0.3, 21)
    hit, loc, nrm, idx = mountain.ray_cast(V((x, y, 30)), V((0, 0, -1)))
    if hit and nrm.z > 0.3:
        inst(random.choice(trees), "S3_MiniTree_%d" % i, loc, random.uniform(0, 6.3), random.uniform(0.07, 0.12), S3)
# route line (grows in beat 3), blue under-water segments (beat 4)
def curve_obj(name, pts, bevel, mat, cl):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = bevel; cu.bevel_resolution = 3
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (p.x, p.y, p.z, 1)
    cu.materials.append(mat)
    o = bpy.data.objects.new(name, cu); cl.objects.link(o); return o
route_dense = []
for k in range(len(ROUTE3) - 1):
    for t in range(10):
        a, b = ROUTE3[k], ROUTE3[k + 1]
        p0 = ROUTE3[max(k - 1, 0)]; p3 = ROUTE3[min(k + 2, len(ROUTE3) - 1)]; tt = t / 10
        route_dense.append(0.5 * ((2 * a) + (-p0 + b) * tt + (2 * p0 - 5 * a + 4 * b - p3) * tt * tt + (-p0 + 3 * a - 3 * b + p3) * tt ** 3))
route_dense.append(ROUTE3[-1])
route_dense = [V((DX + 0.12, p.y, p.z)) for p in route_dense]
m_route = emis("M_RouteLine", (1.0, 0.72, 0.32), 12.0)
rl = curve_obj("S3_RouteLine", route_dense, 0.07, m_route, S3)
rl.data.bevel_factor_mapping_end = 'SPLINE'
m_blue = emis("M_RouteBlue", (0.15, 0.55, 1.0), 0.0)
m_water3 = bpy.data.materials.new("M_SumpWater"); m_water3.use_nodes = True
pw = m_water3.node_tree.nodes["Principled BSDF"]; pw.inputs['Base Color'].default_value = (0.18, 0.24, 0.2, 1)
pw.inputs['Roughness'].default_value = 0.15; pw.inputs['Transmission Weight'].default_value = 0.0; pw.inputs['Alpha'].default_value = 0.85
SUMPS = []   # (y0, y1, z_bottom, z_full)
for (y0, y1, zb, zf) in ((4.6, 9.8, -1.4, 0.75), (14.8, 17.6, -1.1, 0.75), (24.8, 30.4, -1.6, 0.85), (11.0, 14.6, 0.35, 0.95), (18.0, 24.8, 0.2, 1.1)):
    bpy.ops.mesh.primitive_cube_add(size=1)
    wb = bpy.context.active_object; wb.name = "S3_Sump_%d" % len(SUMPS)
    wb.data.transform(Matrix.Translation((0, 0, 0.5)))            # origin at the bottom so z-scale = fill height
    wb.location = (DX + 0.35, (y0 + y1) / 2, zb); wb.scale = (0.62, (y1 - y0), 0.001)
    wb.data.materials.append(m_water3); link(wb, S3)
    seg = [p for p in route_dense if y0 - 0.2 <= p.y <= y1 + 0.2 and p.z < zf]
    if len(seg) > 1:
        bl = curve_obj("S3_RouteBlue_%d" % len(SUMPS), [V((p.x - 0.01, p.y, p.z)) for p in seg], 0.085, m_blue, S3)
    SUMPS.append((wb.name, zb, zf))
sc["SUMPS"] = [list(s[1:]) for s in SUMPS]
sc["SUMP_NAMES"] = [s[0] for s in SUMPS]
# tiny people dots in the chamber + the 13 travelling lights (beat 12b, follow the route line)
m_dot = emis("M_PeopleDot", (1.0, 0.85, 0.55), 6.0)
for i in range(13):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, segments=12, ring_count=6, location=(DX + 0.2, 36.4 + 0.12 * (i % 7), 1.75 + 0.12 * (i // 7)))
    d = bpy.context.active_object; d.name = "S3_Dot_%02d" % i; d.data.materials.append(m_dot); link(d, S3)
m_diverdot = emis("M_DiverDot", (0.6, 0.85, 1.0), 8.0)
for i, y in enumerate((5.0, 8.6, 15.2, 17.4, 25.5, 28.8, 33.0)):
    p = min(route_dense, key=lambda q: abs(q.y - y))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.055, segments=12, ring_count=6, location=(DX + 0.05, p.y, p.z + 0.12))
    d = bpy.context.active_object; d.name = "S3_DiverDot_%d" % i; d.data.materials.append(m_diverdot); link(d, S3)
bpy.ops.mesh.primitive_plane_add(size=1, location=(DX + 8, 20, -3.0))
fl3 = bpy.context.active_object; fl3.name = "S3_Floor"; fl3.scale = (60, 90, 1); link(fl3, S3)
fl3.data.materials.append(flat("M_StudioFloor", (0.05, 0.07, 0.09), 0.6))
# studio dome around the diorama (dark blue-grey gradient) + soft key
bpy.ops.mesh.primitive_uv_sphere_add(radius=90, location=(DX - 10, 20, 0), segments=48, ring_count=24)
dome = bpy.context.active_object; dome.name = "S3_StudioDome"; link(dome, S3)
m_studio = bpy.data.materials.new("M_StudioDome"); m_studio.use_nodes = True
nn_, ll_ = m_studio.node_tree.nodes, m_studio.node_tree.links; nn_.clear()
o_ = nn_.new('ShaderNodeOutputMaterial'); e_ = nn_.new('ShaderNodeEmission'); gt = nn_.new('ShaderNodeTexCoord'); sx_ = nn_.new('ShaderNodeSeparateXYZ')
rp = nn_.new('ShaderNodeValToRGB'); rp.color_ramp.elements[0].color = (0.006, 0.01, 0.016, 1); rp.color_ramp.elements[1].color = (0.06, 0.1, 0.13, 1)
mr_ = nn_.new('ShaderNodeMapRange'); mr_.inputs['From Min'].default_value = -0.2; mr_.inputs['From Max'].default_value = 0.6
ll_.new(gt.outputs['Normal'], sx_.inputs['Vector']); ll_.new(sx_.outputs['Z'], mr_.inputs['Value']); ll_.new(mr_.outputs['Result'], rp.inputs['Fac'])
ll_.new(rp.outputs['Color'], e_.inputs['Color']); e_.inputs['Strength'].default_value = 1.0; ll_.new(e_.outputs[0], o_.inputs['Surface'])
dome.data.materials.append(m_studio)
for nm, loc, rot, en, size in (("S3_Key", (DX - 25, 5, 30), (R_(40), R_(-40), R_(-60)), 9000, 20), ("S3_Rim", (DX + 30, 50, 25), (R_(-50), R_(40), 0), 5000, 15)):
    L_ = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'AREA')); L_.data.energy = en; L_.data.size = size
    L_.location = loc; L_.rotation_euler = rot; S3.objects.link(L_)
    tt = L_.constraints.new('TRACK_TO'); tg = bpy.data.objects.new(nm + "_tgt", None); tg.location = (DX, 18, 3); S3.objects.link(tg); tt.target = tg
sc["DX"] = DX
sc["ROUTE"] = [list(p) for p in route_dense]

# ================================================================== S4 chamber + S5 flooded passage at x = CX
CX = 400.0
WATER_Z = -0.35
def H4(x, y):
    x -= CX
    ledge = 0.07 * y + 0.12 * noise.noise(V((x * 0.7, y * 0.7, 4))) + 0.04 * noise.noise(V((x * 3, y * 3, 2)))
    drop = 2.6 * (1 - smoothstep(-2.6, -0.2, y + 0.4 * noise.noise(V((x * 0.5, 0, 7)))))
    wall = 3.0 * smoothstep(4.5, 7.0, abs(x)) + 3.0 * smoothstep(5.5, 8.5, y)
    return ledge - drop + wall
ledge = grid_mesh("S4_Ledge", CX - 8, CX + 8, -9, 9, 96, 108, H4, S4, solid=0.8)
m_mud = pbr("M_LedgeMud", "brown_mud_02", 1.4, sat=0.9, val=0.75, bump=1.0, rough_mul=0.5)
ledge.data.materials.append(m_mud)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(CX, 0.5, -0.6), segments=64, ring_count=32)
cav = bpy.context.active_object; cav.name = "S4_Cavern"; cav.scale = (8.2, 9.5, 4.6); apply_mods(cav)
for v in cav.data.vertices:
    q = v.co.copy(); n_ = (q - V((CX, 0.5, -0.6))).normalized()
    v.co = q + n_ * (0.7 * noise.noise(q * 0.35) + 0.25 * noise.noise(q * 1.3))
link(cav, S4)
# passage under the pool, heading -Y and down; squeeze at y ~ -13
PAS = [(CX, -1.0, -2.6), (CX + 0.3, -5.0, -3.0), (CX - 0.4, -9.0, -3.4), (CX, -13.0, -3.6), (CX + 0.8, -17.0, -3.9), (CX + 0.2, -22.0, -4.3),
       (CX - 1.0, -28.0, -4.8), (CX - 0.5, -36.0, -5.2), (CX + 0.5, -46.0, -5.5)]
def pas_r(t):
    sq = math.exp(-((t - 0.27) ** 2) / 0.0025)        # the squeeze
    return (1.6 - 1.05 * sq + 0.2 * math.sin(t * 23), 2.0 - 1.3 * sq + 0.2 * math.sin(t * 13))
passage, PAS_D = tube_mesh("S5_Passage", PAS, pas_r, S4, noise_amp=0.22, seed=9.0, step=0.4)
pcut, _ = tube_mesh("CUT_Passage", [(CX, 1.0, -2.4)] + PAS[:3] + [(CX - 0.2, -11.0, -3.5)], lambda t: (1.4, 1.75), S4, noise_amp=0.0, closed=True)
boolean_cut(cav, pcut); apply_mods(ledge); boolean_cut(ledge, pcut)
bpy.data.objects.remove(pcut, do_unlink=True)
m_cav = pbr("M_CavernRock", "rock_surface", 3.0, sat=0.5, val=0.55, bump=1.6, rough_mul=0.45)
cav.data.materials.append(m_cav)
m_pas = pbr("M_PassageRock", "dark_rock", 2.0, sat=0.5, val=0.6, bump=1.4, rough_mul=0.5)
mix_mud(m_pas, "brown_mud_02", "mud"); set_mud_by_height(passage, PAS_D, 0.6)
passage.data.materials.append(m_pas)
# water surface (rippled, transmissive) + underwater murk volume
bpy.ops.mesh.primitive_plane_add(size=1, location=(CX, -24, WATER_Z))
wsurf = bpy.context.active_object; wsurf.name = "S4_WaterSurface"; wsurf.scale = (16, 60, 1); link(wsurf, S4)
md = wsurf.modifiers.new("Sub", 'SUBSURF'); md.subdivision_type = 'SIMPLE'; md.levels = md.render_levels = 6
m_ws = bpy.data.materials.new("M_WaterSurface"); m_ws.use_nodes = True
wn_, wl_ = m_ws.node_tree.nodes, m_ws.node_tree.links
pw = wn_["Principled BSDF"]; pw.inputs['Base Color'].default_value = (0.5, 0.55, 0.45, 1); pw.inputs['Roughness'].default_value = 0.03
pw.inputs['Transmission Weight'].default_value = 1.0; pw.inputs['IOR'].default_value = 1.33
nz = wn_.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.name = "Ripple"; nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 4
bmp = wn_.new('ShaderNodeBump'); bmp.inputs['Strength'].default_value = 0.25; bmp.inputs['Distance'].default_value = 0.02
wl_.new(nz.outputs['Fac'], bmp.inputs['Height']); wl_.new(bmp.outputs['Normal'], pw.inputs['Normal'])
drv = nz.inputs['W'].driver_add("default_value"); drv.driver.expression = "frame/90"
wsurf.data.materials.append(m_ws)
bpy.ops.mesh.primitive_cube_add(size=1, location=(CX, -21, (WATER_Z - 9) / 2 - 0.002))
vol = bpy.context.active_object; vol.name = "S5_Murk"; vol.scale = (18, 58, 9 + WATER_Z); link(vol, S4)
m_murk = bpy.data.materials.new("M_Murk"); m_murk.use_nodes = True
mn_, ml_ = m_murk.node_tree.nodes, m_murk.node_tree.links; mn_.clear()
mo_ = mn_.new('ShaderNodeOutputMaterial'); pv = mn_.new('ShaderNodeVolumePrincipled'); pv.name = "MurkVol"
pv.inputs['Color'].default_value = (0.16, 0.15, 0.1, 1); pv.inputs['Density'].default_value = 0.07
pv.inputs['Absorption Color'].default_value = (0.5, 0.55, 0.35, 1)
ml_.new(pv.outputs[0], mo_.inputs['Volume']); vol.data.materials.append(m_murk)
# silt cloud in the squeeze (noise density)
bpy.ops.mesh.primitive_cube_add(size=1, location=(CX, -13, -2.8))
silt = bpy.context.active_object; silt.name = "S5_Silt"; silt.scale = (3.6, 8, 2.6); link(silt, S4)
m_silt = bpy.data.materials.new("M_Silt"); m_silt.use_nodes = True
sn_, sl_ = m_silt.node_tree.nodes, m_silt.node_tree.links; sn_.clear()
so_ = sn_.new('ShaderNodeOutputMaterial'); sv = sn_.new('ShaderNodeVolumePrincipled'); sv.inputs['Color'].default_value = (0.42, 0.36, 0.25, 1)
stc = sn_.new('ShaderNodeTexCoord'); snz = sn_.new('ShaderNodeTexNoise'); snz.noise_dimensions = '4D'; snz.inputs['Scale'].default_value = 1.6; snz.inputs['Detail'].default_value = 3
sdrv = snz.inputs['W'].driver_add("default_value"); sdrv.driver.expression = "frame/240"
smr = sn_.new('ShaderNodeMapRange'); smr.inputs['From Min'].default_value = 0.45; smr.inputs['From Max'].default_value = 0.75; smr.inputs['To Max'].default_value = 1.2
sval = sn_.new('ShaderNodeValue'); sval.name = "SiltAmount"; sval.outputs[0].default_value = 1.0
smul = sn_.new('ShaderNodeMath'); smul.operation = 'MULTIPLY'
sl_.new(stc.outputs['Object'], snz.inputs['Vector']); sl_.new(snz.outputs['Fac'], smr.inputs['Value']); sl_.new(smr.outputs['Result'], smul.inputs[0])
sl_.new(sval.outputs[0], smul.inputs[1]); sl_.new(smul.outputs[0], sv.inputs['Density']); sl_.new(sv.outputs[0], so_.inputs['Volume'])
silt.data.materials.append(m_silt)
# guide rope: from a rock anchor at the pool edge down along the passage wall
m_rope = flat("M_GuideRope", (0.75, 0.62, 0.15), 0.7)
rope_pts = [V((CX - 1.2, -0.3, WATER_Z + 0.25)), V((CX - 1.0, -1.2, -1.2))]
for p in PAS_D[4::6]:
    rope_pts.append(p + V((-0.55 * (1 - 0.6 * math.exp(-((p.y + 13) ** 2) / 6)), 0, 0.35)))
rope = curve_obj("S5_GuideRope", rope_pts, 0.008, m_rope, S4)
rope.data.splines[0].type = 'NURBS'; rope.data.splines[0].order_u = 3; rope.data.splines[0].use_endpoint_u = True
sc["CX"] = CX; sc["WATER_Z"] = WATER_Z
sc["PAS"] = [list(p) for p in PAS_D]
# chamber props: gear bags, tanks lying on the ledge, a candle-ish dim lantern, mud puddles
m_tank = flat("M_Tank", (0.75, 0.75, 0.72), 0.3, 0.8); m_bag = flat("M_GearBag", (0.08, 0.1, 0.12), 0.8)
for i, (x, y, rz) in enumerate(((1.8, 1.2, 0.3), (2.3, 1.5, 0.5), (-2.2, 2.0, -0.4))):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=0.65, location=(CX + x, y, H4(CX + x, y) + 0.09), rotation=(0, R_(90), rz))
    t = bpy.context.active_object; t.name = "S4_SpareTank_%d" % i; t.data.materials.append(m_tank); link(t, S4)
for i, (x, y) in enumerate(((2.8, 0.6), (-2.6, 1.0), (1.2, 3.2))):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(CX + x, y, H4(CX + x, y) + 0.12))
    b = bpy.context.active_object; b.name = "S4_GearBag_%d" % i; b.scale = (0.55, 0.32, 0.26); b.data.materials.append(m_bag); link(b, S4)
    bv = b.modifiers.new("Bev", 'BEVEL'); bv.width = 0.06; bv.segments = 3
# dim ambient in the chamber so the dark reads as rock, not void
fill4 = bpy.data.objects.new("S4_Fill", bpy.data.lights.new("S4_Fill", 'AREA')); fill4.data.energy = 40; fill4.data.size = 6
fill4.data.color = (0.7, 0.8, 1.0); fill4.location = (CX - 1, 1.5, 3.2); S4.objects.link(fill4)

# ================================================================== FX: rain sheets, torrent, tunnel flood water
m_rain = bpy.data.materials.new("M_Rain"); m_rain.use_nodes = True
rn, rl_ = m_rain.node_tree.nodes, m_rain.node_tree.links; rn.clear()
ro = rn.new('ShaderNodeOutputMaterial'); rtc = rn.new('ShaderNodeTexCoord'); rmp = rn.new('ShaderNodeMapping')
rmp.inputs['Scale'].default_value = (60, 3, 1)
rdrv = rmp.inputs['Location'].driver_add("default_value", 1); rdrv.driver.expression = "frame*0.35"
rnz = rn.new('ShaderNodeTexNoise'); rnz.inputs['Scale'].default_value = 1.0; rnz.inputs['Detail'].default_value = 0
rmr = rn.new('ShaderNodeMapRange'); rmr.inputs['From Min'].default_value = 0.66; rmr.inputs['From Max'].default_value = 0.74
rval = rn.new('ShaderNodeValue'); rval.name = "RainAmount"; rval.outputs[0].default_value = 0.0
rmul = rn.new('ShaderNodeMath'); rmul.operation = 'MULTIPLY'
rtr = rn.new('ShaderNodeBsdfTransparent'); rgl = rn.new('ShaderNodeEmission'); rgl.inputs['Color'].default_value = (0.8, 0.85, 0.9, 1); rgl.inputs['Strength'].default_value = 0.9
rmx = rn.new('ShaderNodeMixShader')
for a_, b_ in ((rtc.outputs['UV'], rmp.inputs['Vector']), (rmp.outputs['Vector'], rnz.inputs['Vector']), (rnz.outputs['Fac'], rmr.inputs['Value']),
               (rmr.outputs['Result'], rmul.inputs[0]), (rval.outputs[0], rmul.inputs[1]), (rmul.outputs[0], rmx.inputs['Fac']),
               (rtr.outputs[0], rmx.inputs[1]), (rgl.outputs[0], rmx.inputs[2]), (rmx.outputs[0], ro.inputs['Surface'])):
    rl_.new(a_, b_)
for i, (y, w_) in enumerate(((-3.0, 14), (-6.5, 20), (-11, 30), (-17, 40), (-26, 60))):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, y, 7), rotation=(R_(90), 0, 0))
    rs = bpy.context.active_object; rs.name = "FX_RainSheet_%d" % i; rs.scale = (w_, 16, 1); rs.data.materials.append(m_rain); link(rs, FX)
    rs.visible_shadow = False
# torrent pouring over the mouth lip and flood water in the tunnel
m_flood = bpy.data.materials.new("M_FloodWater"); m_flood.use_nodes = True
fn_, fl_ = m_flood.node_tree.nodes, m_flood.node_tree.links
pf = fn_["Principled BSDF"]; pf.inputs['Base Color'].default_value = (0.22, 0.16, 0.09, 1); pf.inputs['Roughness'].default_value = 0.08
pf.inputs['Specular IOR Level'].default_value = 0.6
ftc = fn_.new('ShaderNodeTexCoord'); fmp = fn_.new('ShaderNodeMapping'); fmp.inputs['Scale'].default_value = (1.5, 0.6, 1.5)
fdrv = fmp.inputs['Location'].driver_add("default_value", 1); fdrv.driver.expression = "-frame*0.06"
fnz = fn_.new('ShaderNodeTexNoise'); fnz.inputs['Scale'].default_value = 2.5; fnz.inputs['Detail'].default_value = 6
fmr = fn_.new('ShaderNodeMapRange'); fmr.inputs['From Min'].default_value = 0.55; fmr.inputs['From Max'].default_value = 0.8
fmix = fn_.new('ShaderNodeMix'); fmix.data_type = 'RGBA'; fmix.inputs['A'].default_value = (0.2, 0.14, 0.08, 1); fmix.inputs['B'].default_value = (0.75, 0.68, 0.55, 1)
fbmp = fn_.new('ShaderNodeBump'); fbmp.inputs['Strength'].default_value = 0.5
for a_, b_ in ((ftc.outputs['Object'], fmp.inputs['Vector']), (fmp.outputs['Vector'], fnz.inputs['Vector']), (fnz.outputs['Fac'], fmr.inputs['Value']),
               (fmr.outputs['Result'], fmix.inputs['Factor']), (fmix.outputs['Result'], pf.inputs['Base Color']), (fnz.outputs['Fac'], fbmp.inputs['Height']),
               (fbmp.outputs['Normal'], pf.inputs['Normal'])):
    fl_.new(a_, b_)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0.8, 24, -3.0))
flood = bpy.context.active_object; flood.name = "S2_FloodWater"; flood.scale = (12, 52, 1); link(flood, S2)
md = flood.modifiers.new("Sub", 'SUBSURF'); md.subdivision_type = 'SIMPLE'; md.levels = md.render_levels = 5
dsp = flood.modifiers.new("Wave", 'DISPLACE'); tx = bpy.data.textures.new("FloodWave", 'CLOUDS'); tx.noise_scale = 0.6; dsp.texture = tx; dsp.strength = 0.12
flood.data.materials.append(m_flood)
# the surge front: a frothy brown wedge that runs along the floor
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=24, ring_count=12)
surge = bpy.context.active_object; surge.name = "S2_SurgeFront"; surge.scale = (2.4, 1.6, 0.45); link(surge, S2)
dsp = surge.modifiers.new("Froth", 'DISPLACE'); tx2 = bpy.data.textures.new("Froth", 'CLOUDS'); tx2.noise_scale = 0.25; dsp.texture = tx2; dsp.strength = 0.35
surge.data.materials.append(m_flood)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -1.9, 3.2), rotation=(R_(80), 0, 0))
torrent = bpy.context.active_object; torrent.name = "FX_MouthTorrent"; torrent.scale = (3.4, 3.6, 1); link(torrent, FX)
md = torrent.modifiers.new("Sub", 'SUBSURF'); md.subdivision_type = 'SIMPLE'; md.levels = md.render_levels = 4
dsp = torrent.modifiers.new("Wave", 'DISPLACE'); dsp.texture = tx; dsp.strength = 0.18
torrent.data.materials.append(m_flood); torrent.hide_render = True

# ================================================================== rescue staging in front of the mouth (beat 13)
m_white = flat("M_VanWhite", (0.82, 0.82, 0.8), 0.3); m_glass = flat("M_DarkGlass", (0.02, 0.025, 0.03), 0.05)
m_stripe = flat("M_VanStripe", (0.55, 0.05, 0.04), 0.4)
m_red = emis("M_BeaconRed", (1.0, 0.05, 0.02), 0.0); m_bluel = emis("M_BeaconBlue", (0.05, 0.2, 1.0), 0.0)
def box(name, size, loc, mat, cl, rz=0.0, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.active_object; o.name = name
    o.scale = size; o.rotation_euler.z = rz; o.data.materials.append(mat); link(o, cl)
    if bevel:
        b = o.modifiers.new("Bev", 'BEVEL'); b.width = bevel; b.segments = 2
    return o
def ambulance(name, loc, rz):
    root = bpy.data.objects.new(name, None); root.location = loc; root.rotation_euler.z = rz; S1.objects.link(root)
    parts = [box(name + "_Body", (2.0, 4.8, 1.9), (0, 0.3, 1.45), m_white, S1, bevel=0.08),
             box(name + "_Cab", (1.95, 1.4, 1.3), (0, -2.6, 1.15), m_white, S1, bevel=0.1),
             box(name + "_Wind", (1.8, 0.05, 0.6), (0, -3.32, 1.5), m_glass, S1),
             box(name + "_StripeL", (2.02, 4.82, 0.18), (0, 0.3, 1.2), m_stripe, S1),
             box(name + "_BarR", (0.5, 0.25, 0.14), (-0.4, -2.2, 1.9), m_red, S1),
             box(name + "_BarB", (0.5, 0.25, 0.14), (0.4, -2.2, 1.9), m_bluel, S1)]
    for wx in (-0.95, 0.95):
        for wy in (-2.4, 1.6):
            bpy.ops.mesh.primitive_cylinder_add(radius=0.42, depth=0.3, location=(wx, wy, 0.42), rotation=(0, R_(90), 0))
            t = bpy.context.active_object; t.data.materials.append(m_tyre); link(t, S1); parts.append(t)
    for p in parts: p.parent = root
    return root
AMB = [ambulance("S1_Ambulance_0", (-7.5, -24, H1(-7.5, -24)), R_(25)), ambulance("S1_Ambulance_1", (8.0, -27, H1(8, -27)), R_(-30))]
# helicopter (plain, no markings) - lands in the clearing during beat 13
m_heli = flat("M_HeliBody", (0.18, 0.22, 0.2), 0.35, 0.3)
heli = bpy.data.objects.new("S1_Heli", None); S1.objects.link(heli); heli.location = (2, -44, 9)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=32, ring_count=16); hb = bpy.context.active_object; hb.name = "S1_Heli_Body"
hb.scale = (1.1, 2.3, 1.1); hb.data.materials.append(m_heli); link(hb, S1); hb.parent = heli; hb.location = (0, 0, 1.4)
bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=5.0, rotation=(R_(90), 0, 0)); tb = bpy.context.active_object; tb.name = "S1_Heli_Tail"
tb.location = (0, 4.2, 1.7); tb.data.materials.append(m_heli); link(tb, S1); tb.parent = heli
box("S1_Heli_Glass", (1.6, 1.2, 0.9), (0, -1.6, 1.75), m_glass, S1).parent = heli
for sx in (-1, 1):
    box("S1_Heli_Skid%d" % sx, (0.08, 3.6, 0.08), (0.9 * sx, 0, 0.05), m_frame[2], S1).parent = heli
rotor = bpy.data.objects.new("S1_Heli_Rotor", None); S1.objects.link(rotor); rotor.parent = heli; rotor.location = (0, 0, 2.7)
for k in range(4):
    bl_ = box("S1_Heli_Blade%d" % k, (0.3, 5.2, 0.04), (0, 2.6, 0), m_frame[2], S1); bl_.parent = rotor
    bl_.location = Matrix.Rotation(R_(90 * k), 3, 'Z') @ V((0, 2.6, 0)); bl_.rotation_euler.z = R_(90 * k)
# tents + tarps + floodlights in the clearing
m_tarp = flat("M_Tarp", (0.12, 0.22, 0.45), 0.7)
for i, (x, y, rz) in enumerate(((-6, -12, 0.2), (6.5, -13, -0.3), (-10, -18, 0.6))):
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=2.6, depth=2.2, location=(x, y, H1(x, y) + 1.1), rotation=(0, 0, R_(45) + rz))
    t = bpy.context.active_object; t.name = "S1_Tent_%d" % i; t.data.materials.append(m_tarp); link(t, S1)
sc["H1_note"] = "terrain is S1_Terrain"
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SCENE_OK objects", len(bpy.data.objects))
