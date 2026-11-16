"""LakeSword sets + props. blender -b chars.blend --python 02_sets.py -- <assets_dir> <out.blend>
assets_dir holds: lsmodels/*.glb (Sketchfab CC-BY) and ph/<id>/ (Poly Haven CC0, 1k).
Sets, far apart in one scene:
  LAKE   (0,0)    shallow lake: water z=0, sandy-pebble bed z=-0.25, shore bank toward +y, pines, rocks, grass, far shore at -y
  MUSEUM (100,0)  white hall, wood floor, felt-topped display table, pedestals, pictures, red banner with our logo, crate with logo
  MACRO  (200,0)  sky-blue gradient dome for the sword close-ups
  CAMP   (300,0)  lakeside camp of the past: tents, two boats, fire pit with a small fire, pines, lake toward -y
Hero prop: Sword (Viking sword model). Sword_Found = rusted iron + crusty shell over the blade (the "rust" = old sheath);
Sword_Warrior = the same sword, clean steel, in a clean leather sheath (same shell, leather material)."""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
from mathutils.noise import noise
a = sys.argv[sys.argv.index("--") + 1:]; AS, OUT = a[0], a[1]
sc = bpy.context.scene; V = Vector; R_ = math.radians
random.seed(34)
BRAND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "brand")

# ------------------------------------------------------------------ render + look
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920; sc.render.fps = 60
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.cycles.max_bounces = 8; sc.cycles.transmission_bounces = 8; sc.cycles.transparent_max_bounces = 16
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'
sc.render.use_motion_blur = False

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
def link(o, c):
    for uc in list(o.users_collection): uc.objects.unlink(o)
    c.objects.link(o)

# ------------------------------------------------------------------ materials
def mat(name, rgb, rough=0.5, metal=0.0, emit=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; P = m.node_tree.nodes["Principled BSDF"]
    P.inputs['Base Color'].default_value = (*rgb, 1); P.inputs['Roughness'].default_value = rough; P.inputs['Metallic'].default_value = metal
    if emit: P.inputs['Emission Color'].default_value = (*emit[0], 1); P.inputs['Emission Strength'].default_value = emit[1]
    return m
def tex_nodes(nt, pid, scale=1.0, sat=1.15, bump=0.3, rough_min=0.45, tint=None, P=None):
    d = os.path.join(AS, "ph", pid, "textures")
    P = P or nt.nodes.new('ShaderNodeBsdfPrincipled')
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs['UV'], mp.inputs['Vector'])
    def img(suffix, non_color=False):
        f = next((os.path.join(d, x) for x in sorted(os.listdir(d)) if suffix in x), None)
        if not f: return None
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(f, check_existing=True)
        if non_color: n.image.colorspace_settings.name = 'Non-Color'
        nt.links.new(mp.outputs['Vector'], n.inputs['Vector']); return n
    df = img("_diff_"); hs = nt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = sat
    nt.links.new(df.outputs['Color'], hs.inputs['Color'])
    if tint:
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        mx.inputs['B'].default_value = (*tint, 1); nt.links.new(hs.outputs['Color'], mx.inputs['A']); nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])
    else: nt.links.new(hs.outputs['Color'], P.inputs['Base Color'])
    rg = img("_rough_", True)
    if rg:
        mr = nt.nodes.new('ShaderNodeMath'); mr.operation = 'MAXIMUM'; mr.inputs[1].default_value = rough_min
        nt.links.new(rg.outputs['Color'], mr.inputs[0]); nt.links.new(mr.outputs[0], P.inputs['Roughness'])
    else: P.inputs['Roughness'].default_value = max(0.6, rough_min)
    nr = img("_nor_gl_", True)
    if nr:
        nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = bump
        nt.links.new(nr.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], P.inputs['Normal'])
    return P
def tex_mat(pid, scale=1.0, sat=1.15, bump=0.3, rough_min=0.45, tint=None):
    m = bpy.data.materials.new("M_" + pid); m.use_nodes = True; nt = m.node_tree
    tex_nodes(nt, pid, scale, sat, bump, rough_min, tint, P=nt.nodes["Principled BSDF"]); return m

# ------------------------------------------------------------------ asset loading
def ph_objects(pid, keep=lambda n: True):
    f = os.path.join(AS, "ph", pid, pid + "_1k.blend")
    with bpy.data.libraries.load(f) as (df, dt): dt.objects = [n for n in df.objects if keep(n)]
    return [o for o in dt.objects if o is not None and o.type == 'MESH']
def proto_collection(name, objs):
    """a hidden collection used as an instance source; objects re-centred so the base sits at the origin"""
    c = bpy.data.collections.new("PROTO_" + name)
    for o in objs: c.objects.link(o)
    return c
def instance(c, loc, rot_z=0.0, s=1.0, parent_coll=None, name=None):
    e = bpy.data.objects.new(name or ("I_" + c.name), None); e.instance_type = 'COLLECTION'; e.instance_collection = c
    e.location = loc; e.rotation_euler = (0, 0, rot_z); e.scale = (s, s, s)
    (parent_coll or sc.collection).objects.link(e); return e
def glb(name):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=os.path.join(AS, "lsmodels", name + ".glb"))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    bpy.context.view_layer.update()
    for o in meshes:
        Mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = Mw
    for o in new:
        if o.type != 'MESH': bpy.data.objects.remove(o, do_unlink=True)
    for o in meshes:
        o.data = o.data.copy(); o.data.transform(o.matrix_world); o.matrix_world = Matrix()
    if len(meshes) > 1:
        with bpy.context.temp_override(active_object=meshes[0], selected_editable_objects=meshes, object=meshes[0]):
            bpy.ops.object.join()
    o = meshes[0]; o.name = name; o.rotation_mode = "XYZ"; return o
def fit(o, length=None, height=None, base_to_zero=True):
    pts = [V(c) for c in o.bound_box]; mn = V([min(p[i] for p in pts) for i in range(3)]); mx = V([max(p[i] for p in pts) for i in range(3)])
    s = (length / max(mx - mn)) if length else (height / (mx.z - mn.z))
    c = (mn + mx) / 2; o.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation(V((-c.x, -c.y, -mn.z if base_to_zero else -c.z))))
    return o

# ------------------------------------------------------------------ world
w = bpy.data.worlds.new("W_Sky"); sc.world = w; w.use_nodes = True; nt = w.node_tree
env = nt.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(os.path.join(AS, "ph", "hdri", "kloofendal_48d_partly_cloudy_puresky_1k.hdr"))
bg = nt.nodes["Background"]; bg.inputs['Strength'].default_value = 0.9; nt.links.new(env.outputs['Color'], bg.inputs['Color'])
sun_d = bpy.data.lights.new("Sun", 'SUN'); sun_d.energy = 3.2; sun_d.angle = R_(3); sun_d.color = (1.0, 0.96, 0.9)
sun = bpy.data.objects.new("Sun", sun_d); sc.collection.objects.link(sun); sun.rotation_euler = (R_(48), 0, R_(-35))

# ------------------------------------------------------------------ prototypes (hidden instance sources)
PROTO = coll("PROTOS"); PROTO.hide_render = True; PROTO.hide_viewport = True
def proto(name, objs):
    c = bpy.data.collections.new("P_" + name); PROTO.children.link(c)
    for o in objs:
        for uc in list(o.users_collection): uc.objects.unlink(o)
        c.objects.link(o)
    return c
# pine: one tree variant at LOD2 (the 1k file lays several variants side by side along x; keep the one nearest x=0)
pine = ph_objects("pine_tree_01", lambda n: n == "pine_tree_01_a_LOD2")
fir = ph_objects("fir_tree_01", lambda n: n == "fir_tree_01_a_LOD2")
def first_variant(objs):
    for o in objs: o.matrix_world = Matrix()
    for o in objs:
        c = sum((V(c_) for c_ in o.bound_box), V()) / 8; o.data = o.data.copy(); o.data.transform(Matrix.Translation(V((-c.x, -c.y, 0))))
        print("TREE", o.name, len(o.data.polygons), tuple(round(x, 1) for x in o.dimensions))
    return objs
P_PINE = proto("pine", first_variant(pine)); P_FIR = proto("fir", first_variant(fir))
P_GRASS = proto("grass", ph_objects("grass_medium_01", lambda n: n.endswith("_LOD1")))
P_ROCK = proto("rock", ph_objects("rock_moss_set_01"))
P_FERN = proto("fern", ph_objects("fern_02", lambda n: n.endswith("_a") or n.endswith("_b")))
P_STUMP = proto("stump", ph_objects("tree_stump_01"))
P_BRANCH = proto("branch", ph_objects("dry_branches_medium_01", lambda n: n.endswith("_a")))
print("PROTO pine", [o.name for o in P_PINE.objects], "fir", [o.name for o in P_FIR.objects])

# ------------------------------------------------------------------ terrain helper
def terrain(name, origin, sx, sy, res, hfun, material, coll_):
    bm = bmesh.new(); nx, ny = int(sx / res), int(sy / res); vs = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            x = -sx / 2 + i * res; y = -sy / 2 + j * res
            row.append(bm.verts.new((x, y, hfun(x, y))))
        vs.append(row)
    for j in range(ny):
        for i in range(nx): bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    uv = bm.loops.layers.uv.new()
    for f in bm.faces:
        for l in f.loops: l[uv].uv = (l.vert.co.x / 2.0, l.vert.co.y / 2.0)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); coll_.objects.link(o); o.location = origin
    for m in material: me.materials.append(m)
    return o
def ss(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

def shore_material(name, bed_pid, land_pid, z_split):
    """bed texture below z_split (object space), grass texture above, soft noisy blend"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    out = nt.nodes["Material Output"]; nt.nodes.remove(nt.nodes["Principled BSDF"])
    pb = tex_nodes(nt, bed_pid, 1.0, 1.2, 0.3); pl = tex_nodes(nt, land_pid, 1.0, 1.3, 0.3)
    tc = nt.nodes.new('ShaderNodeTexCoord'); sp = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sp.inputs[0])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.5; nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'MULTIPLY_ADD'; ad.inputs[1].default_value = 0.12
    nt.links.new(nz.outputs['Fac'], ad.inputs[0]); nt.links.new(sp.outputs['Z'], ad.inputs[2])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = z_split; mr.inputs['From Max'].default_value = z_split + 0.12
    nt.links.new(ad.outputs[0], mr.inputs['Value'])
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(mr.outputs['Result'], mx.inputs[0])
    nt.links.new(pb.outputs[0], mx.inputs[1]); nt.links.new(pl.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    return m

def water_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    P.inputs['Base Color'].default_value = (0.75, 0.92, 0.92, 1); P.inputs['Transmission Weight'].default_value = 1.0
    P.inputs['IOR'].default_value = 1.333; P.inputs['Roughness'].default_value = 0.02
    P.inputs['Specular IOR Level'].default_value = 0.35
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'
    nz.inputs['Scale'].default_value = 2.2; nz.inputs['Detail'].default_value = 3.0
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.06; bp.inputs['Distance'].default_value = 0.02
    nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], P.inputs['Normal'])
    # ripples move: noise W keyed linearly (no frame drivers)
    s = nz.inputs['W']; s.default_value = 0.0; s.keyframe_insert("default_value", frame=1)
    s.default_value = 12.0; s.keyframe_insert("default_value", frame=4001)
    for fc in nt.animation_data.action.fcurves if hasattr(nt.animation_data.action, "fcurves") else []:
        for k in fc.keyframe_points: k.interpolation = 'LINEAR'
    try:
        for lay in nt.animation_data.action.layers:
            for st in lay.strips:
                for cb in st.channelbags:
                    for fc in cb.fcurves:
                        for k in fc.keyframe_points: k.interpolation = 'LINEAR'
    except Exception: pass
    return m
def water_plane(name, loc, sx, sy, c_):
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=loc); o = bpy.context.active_object; o.name = name
    o.scale = (sx, sy, 1); link(o, c_); o.data.materials.append(water_mat("M_" + name))
    o.visible_shadow = False          # sunlight reaches the bed (no caustics needed)
    return o

def forest(c_, origin, xs, ys, n, rng, scale=(0.8, 1.2), avoid=None, hz=lambda x, y: 0.0):
    for _ in range(n):
        x = rng.uniform(*xs); y = rng.uniform(*ys)
        if avoid and avoid(x, y): continue
        p = P_PINE if rng.random() < 0.55 else P_FIR
        instance(p, V(origin) + V((x, y, hz(x, y) - 0.05)), rng.uniform(0, 6.28), rng.uniform(*scale), c_)

# ================================================================== LAKE (0,0)
CL = coll("SET_Lake"); O_L = V((0, 0, 0))
def lake_h(x, y):
    z = -0.25 + 0.45 * ss((y - 2.5) / 3.5) + 0.05 * max(0.0, y - 6.0) ** 1.1
    z += 0.35 * ss((-y - 45.0) / 8.0) + 0.03 * max(0.0, -y - 53.0)       # far shore
    return z + 0.025 * noise(V((x * 0.6, y * 0.6, 0.0))) + 0.008 * noise(V((x * 3.1, y * 3.1, 1.0)))
LAKE_H = lake_h
ML = shore_material("M_LakeShore", "forrest_sand_01", "leafy_grass", 0.06)
terrain("Lake_Ground", O_L, 60, 90, 0.25, lake_h, [ML], CL)
WL = water_plane("Lake_Water", (0, -10, 0.0), 60, 90, CL)
rng = random.Random(7)
forest(CL, O_L, (-28, 28), (8.5, 34), 70, rng, hz=lake_h)
forest(CL, O_L, (-30, 30), (-75, -55), 45, rng, (1.0, 1.4), hz=lake_h)
for i in range(7):     # mossy rocks along the waterline
    x = -9 + i * 3.0 + rng.uniform(-0.8, 0.8); y = rng.uniform(4.3, 6.2)
    instance(P_ROCK, V((x, y, lake_h(x, y) - 0.15)), rng.uniform(0, 6.28), rng.uniform(0.18, 0.3), CL)
for i in range(160):   # grass clumps on the bank
    x = rng.uniform(-16, 16); y = rng.uniform(6.0, 14.0)
    instance(P_GRASS, V((x, y, lake_h(x, y) - 0.03)), rng.uniform(0, 6.28), rng.uniform(0.5, 0.9), CL)
for i in range(18):
    x = rng.uniform(-14, 14); y = rng.uniform(7.0, 13.0)
    instance(P_FERN, V((x, y, lake_h(x, y) - 0.02)), rng.uniform(0, 6.28), rng.uniform(0.6, 0.9), CL)
# a few pebbles/stones on the bed near the find spot (real-scale shapes, the bed texture does the rest)
for i in range(14):
    x = rng.uniform(-2.5, 2.5); y = rng.uniform(-2.5, 2.0)
    instance(P_ROCK, V((x, y, lake_h(x, y) - 0.03)), rng.uniform(0, 6.28), rng.uniform(0.02, 0.04), CL)

# ================================================================== SWORD (hero prop)
CP = coll("PROPS")
sw = glb("sword_viking"); link(sw, CP)
# orient: longest axis -> +Y (tip at +Y), hilt end = the end whose 25% slice is wider (cross-guard)
pts = [v.co for v in sw.data.vertices]; mn = V([min(p[i] for p in pts) for i in range(3)]); mx = V([max(p[i] for p in pts) for i in range(3)])
ax = max(range(3), key=lambda i: mx[i] - mn[i]); L0 = mx[ax] - mn[ax]
def width(lo, hi):
    sel = [p for p in pts if lo <= (p[ax] - mn[ax]) / L0 <= hi]; o_ = [i for i in range(3) if i != ax]
    return max(max(p[o_[0]] for p in sel) - min(p[o_[0]] for p in sel), max(p[o_[1]] for p in sel) - min(p[o_[1]] for p in sel)) if sel else 0
hilt_at_min = width(0.0, 0.25) > width(0.75, 1.0)
# rotation taking axis `ax` (sign) to +Y
d = V((0, 0, 0)); d[ax] = 1.0 if hilt_at_min else -1.0
q = d.rotation_difference(V((0, 1, 0)))
sw.data.transform(q.to_matrix().to_4x4())
pts = [v.co for v in sw.data.vertices]; mn = V([min(p[i] for p in pts) for i in range(3)]); mx = V([max(p[i] for p in pts) for i in range(3)])
# flat of the blade -> X (thin axis -> Z)
if (mx.x - mn.x) < (mx.z - mn.z): sw.data.transform(Matrix.Rotation(R_(90), 4, 'Y'))
pts = [v.co for v in sw.data.vertices]; mn = V([min(p[i] for p in pts) for i in range(3)]); mx = V([max(p[i] for p in pts) for i in range(3)])
S_ = 0.86 / (mx.y - mn.y); sw.data.transform(Matrix.Scale(S_, 4) @ Matrix.Translation(V((-(mn.x + mx.x) / 2, -mn.y, -(mn.z + mx.z) / 2))))
# guard position: widest x-slice in the first 30%

def xw(y0, y1):
    sel = [v.co.x for v in sw.data.vertices if y0 <= v.co.y <= y1]; return (max(sel) - min(sel)) if sel else 0
GUARD_Y = max((y / 100 for y in range(2, 26)), key=lambda y: xw(y - 0.006, y + 0.006))
GRIP_Y = GUARD_Y * 0.55                         # grip centre between pommel and guard
sw.data.transform(Matrix.Translation(V((0, -GRIP_Y, 0))))       # origin = grip centre
GUARD_Y -= GRIP_Y; TIP_Y = 0.86 - GRIP_Y
print("SWORD guard y", round(GUARD_Y, 3), "tip y", round(TIP_Y, 3), "dims", tuple(round(x, 3) for x in sw.dimensions))
sw.name = "Sword_Base"; sw.data.name = "Sword_Base"
for p in sw.data.polygons: p.use_smooth = True
# shell over the blade (old sheath): blade verts only, pushed out along normals
sh = sw.copy(); sh.data = sw.data.copy(); sh.name = "Sheath_Base"; sh.data.name = "Sheath_Base"; CP.objects.link(sh)
bm = bmesh.new(); bm.from_mesh(sh.data)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < GUARD_Y + 0.012], context='VERTS')
bm.normal_update()
for v in bm.verts: v.co += v.normal * 0.0045
bm.to_mesh(sh.data); bm.free()
sh.modifiers.new("Sub", 'SUBSURF').levels = 1
# materials
def m_iron_rust():
    m = bpy.data.materials.new("M_SwordRust"); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 60; nz.inputs['Detail'].default_value = 8; nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (0.05, 0.035, 0.02, 1); cr.color_ramp.elements[1].color = (0.30, 0.13, 0.04, 1)
    nt.links.new(nz.outputs['Fac'], cr.inputs[0]); nt.links.new(cr.outputs[0], P.inputs['Base Color'])
    P.inputs['Roughness'].default_value = 0.85; P.inputs['Metallic'].default_value = 0.25
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.7; nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], P.inputs['Normal'])
    return m
def m_steel():
    m = mat("M_SwordSteel", (0.75, 0.76, 0.78), 0.3, 1.0); return m
def m_crust_leather(name, crust):
    """crust (keyable 'Leather' factor 0 = rust crust, 1 = clean leather with an embossed interlace band pattern)"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 28; nz.inputs['Detail'].default_value = 8
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (0.035, 0.03, 0.018, 1); cr.color_ramp.elements[1].color = (0.32, 0.17, 0.06, 1)
    cr.color_ramp.elements.new(0.55).color = (0.14, 0.13, 0.06, 1)          # brown-green lake crust
    nz2 = nt.nodes.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = 7; nt.links.new(tc.outputs['Object'], nz2.inputs['Vector'])
    ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'MULTIPLY_ADD'; ad.inputs[1].default_value = 0.6; nt.links.new(nz.outputs['Fac'], ad.inputs[0])
    m2 = nt.nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; m2.inputs[1].default_value = 0.4; nt.links.new(nz2.outputs['Fac'], m2.inputs[0]); nt.links.new(m2.outputs[0], ad.inputs[2])
    nt.links.new(ad.outputs[0], cr.inputs[0])
    # leather: warm brown + interlace pattern (two crossing wave bands -> embossed knot-like weave, no letters)
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1, 1, 1); nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    w1 = nt.nodes.new('ShaderNodeTexWave'); w1.wave_type = 'BANDS'; w1.bands_direction = 'DIAGONAL'; w1.inputs['Scale'].default_value = 9; w1.inputs['Distortion'].default_value = 4
    w2 = nt.nodes.new('ShaderNodeTexWave'); w2.wave_type = 'RINGS'; w2.inputs['Scale'].default_value = 7; w2.inputs['Distortion'].default_value = 3
    nt.links.new(mp.outputs['Vector'], w1.inputs['Vector']); nt.links.new(mp.outputs['Vector'], w2.inputs['Vector'])
    mn_ = nt.nodes.new('ShaderNodeMath'); mn_.operation = 'MINIMUM'; nt.links.new(w1.outputs['Fac'], mn_.inputs[0]); nt.links.new(w2.outputs['Fac'], mn_.inputs[1])
    lc = nt.nodes.new('ShaderNodeValToRGB'); lc.color_ramp.elements[0].color = (0.16, 0.07, 0.03, 1); lc.color_ramp.elements[1].color = (0.45, 0.22, 0.09, 1)
    nt.links.new(mn_.outputs[0], lc.inputs[0])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.name = "Leather"; mix.inputs['Factor'].default_value = 0.0 if crust else 1.0
    nt.links.new(cr.outputs[0], mix.inputs['A']); nt.links.new(lc.outputs[0], mix.inputs['B']); nt.links.new(mix.outputs['Result'], P.inputs['Base Color'])
    hgt = nt.nodes.new('ShaderNodeMix'); hgt.data_type = 'FLOAT'; hgt.name = "LeatherH"; hgt.inputs['Factor'].default_value = mix.inputs['Factor'].default_value
    nt.links.new(nz.outputs['Fac'], hgt.inputs['A']); nt.links.new(mn_.outputs[0], hgt.inputs['B'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.8; nt.links.new(hgt.outputs['Result'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], P.inputs['Normal'])
    P.inputs['Roughness'].default_value = 0.8
    return m
M_RUST = m_iron_rust(); M_STEEL = m_steel()
sw.data.materials.clear(); sw.data.materials.append(M_STEEL)
def make_sword(name, hilt_mat, shell_mat, coll_=CP):
    s = sw.copy(); s.data = sw.data.copy(); s.name = name; s.data.name = name; coll_.objects.link(s); s.rotation_mode = "XYZ"
    s.data.materials.clear(); s.data.materials.append(hilt_mat)
    h = sh.copy(); h.data = sh.data.copy(); h.name = name + ".sheath"; h.data.name = h.name; coll_.objects.link(h)
    h.data.materials.clear(); h.data.materials.append(shell_mat); h.parent = s; h.matrix_parent_inverse = Matrix()
    if shell_mat is not M_LEATHER:
        h.modifiers["Sub"].levels = 2; h.modifiers["Sub"].render_levels = 2
        tx = bpy.data.textures.get("T_Crust") or bpy.data.textures.new("T_Crust", 'CLOUDS')
        tx.noise_scale = 0.012; tx.noise_depth = 2
        dsp = h.modifiers.new("Crust", 'DISPLACE'); dsp.texture = tx; dsp.texture_coords = 'OBJECT'; dsp.strength = 0.004; dsp.mid_level = 0.35
    return s
M_CRUST = m_crust_leather("M_SheathCrust", True)
M_LEATHER = m_crust_leather("M_SheathLeather", False)
M_MORPH = m_crust_leather("M_SheathMorph", True)
SW_FOUND = make_sword("Sword_Found", M_RUST, M_CRUST)
SW_WAR = make_sword("Sword_Warrior", M_STEEL, M_LEATHER)
SW_MACRO = make_sword("Sword_Macro", M_RUST, M_MORPH)
for o in (sw, sh): bpy.data.objects.remove(o, do_unlink=True)
SW_FOUND.location = (0.25, -0.35, LAKE_H(0.25, -0.35) + 0.008); SW_FOUND.rotation_euler = (0, 0, R_(70))   # lying flat on the bed
SW_WAR.location = (-600, 0, 0)
sc["GUARD_Y"] = GUARD_Y; sc["TIP_Y"] = TIP_Y

# ================================================================== MUSEUM (100,0)
CM = coll("SET_Museum"); O_M = V((100, 0, 0))
def box(name, c_, loc, size, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True); link(o, c_); o.data.materials.append(m)
    if bevel: bm_ = o.modifiers.new("B", 'BEVEL'); bm_.width = bevel; bm_.segments = 2
    return o
M_FLOOR = tex_mat("wood_floor", 0.6, 1.1, 0.25); M_WALL = mat("M_WallPaint", (0.92, 0.90, 0.85), 0.85)
fl = box("Mus_Floor", CM, O_M + V((0, 0, -0.05)), (14, 12, 0.1), M_FLOOR)
for i, (loc, size) in enumerate((((0, 5, 2.2), (14, 0.2, 4.4)), ((0, -6, 2.2), (14, 0.2, 4.4)), ((-7, 0, 2.2), (0.2, 12, 4.4)), ((7, 0, 2.2), (0.2, 12, 4.4)))):
    box("Mus_Wall%d" % i, CM, O_M + V(loc), size, M_WALL)
box("Mus_Ceiling", CM, O_M + V((0, 0, 4.45)), (14, 12, 0.1), mat("M_Ceil", (0.95, 0.95, 0.95), 0.8))
box("Mus_Skirting", CM, O_M + V((0, 4.88, 0.06)), (14, 0.04, 0.12), mat("M_Skirt", (0.35, 0.22, 0.12), 0.5))
for x in (-3.0, 0.0, 3.0):     # soft ceiling panels
    L = bpy.data.lights.new("MusArea", 'AREA'); L.energy = 600; L.size = 2.5; L.color = (1.0, 0.97, 0.92)
    lo = bpy.data.objects.new("MusArea", L); CM.objects.link(lo); lo.location = O_M + V((x, 0, 4.3))
    box("Mus_Lamp", CM, O_M + V((x, 0, 4.39)), (2.5, 2.5, 0.02), mat("M_LampPanel", (1, 1, 1), 0.5, emit=((1, 0.98, 0.94), 3.0)))
# display table (wood) + green felt top, at the room centre, 0.9 m high
tb = ph_objects("WoodenTable_01")[0]; link(tb, CM); tb.location = O_M + V((0, 0.6, 0)); tb.scale = (1.0, 1.25, 1.62)
TABLE_TOP = 0.549 * 1.62
box("Mus_Felt", CM, O_M + V((0, 0.6, TABLE_TOP + 0.006)), (1.7, 0.78, 0.012), mat("M_Felt", (0.05, 0.22, 0.12), 0.9))
sc["TABLE_TOP"] = TABLE_TOP + 0.012
# pedestals with crates along the side walls, pictures on the walls
ped = glb("pedestal"); link(ped, CM); fit(ped, height=1.1)
for i, x in enumerate((-5.0, -3.2, 3.2, 5.0)):
    p = ped.copy(); p.data = ped.data; CM.objects.link(p); p.location = O_M + V((x, 3.6, 0))
bpy.data.objects.remove(ped, do_unlink=True)
crate = ph_objects("wooden_crate_01"); [link(o, CM) for o in crate]
for o in crate: o.location = O_M + V((-4.6, 2.2, 0)) + o.location; o.rotation_euler.z = R_(20)
pf = ph_objects("hanging_picture_frame_01")[0]
for i, x in enumerate((-4.6, 4.6)):
    p = pf.copy(); CM.objects.link(p); p.location = O_M + V((x, 4.88, 2.0)); p.scale = (1.8, 1.8, 1.8)
for i, y in enumerate((-2.0, 1.5)):
    p = pf.copy(); CM.objects.link(p); p.location = O_M + V((-6.88, y, 2.0)); p.rotation_euler.z = R_(-90); p.scale = (1.8, 1.8, 1.8)
    p2 = pf.copy(); CM.objects.link(p2); p2.location = O_M + V((6.88, y, 2.0)); p2.rotation_euler.z = R_(90); p2.scale = (1.8, 1.8, 1.8)

# ---- our logo (DA KRAS FILMS): image decal with alpha on a deep-red banner (back wall) and on the crate side
def logo_mat(name, which):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(BRAND, "DaKrasFilms_logo_%s.png" % which), check_existing=True)
    t.interpolation = 'Cubic'; nt.links.new(t.outputs['Color'], P.inputs['Base Color']); nt.links.new(t.outputs['Alpha'], P.inputs['Alpha'])
    P.inputs['Roughness'].default_value = 0.6
    try: m.surface_render_method = 'BLENDED'
    except Exception: pass
    return m
def decal(name, c_, loc, width, rot, m, parent=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0)); o = bpy.context.active_object; o.name = name
    o.scale = (width, width * 414 / 967, 1); bpy.ops.object.transform_apply(scale=True)
    o.rotation_euler = rot; o.location = loc; link(o, c_); o.data.materials.append(m)
    o.visible_shadow = False
    bpy.context.view_layer.update()
    if parent: Mw = o.matrix_world.copy(); o.parent = parent; o.matrix_world = Mw
    return o
BAN = box("Mus_Banner", CM, O_M + V((0, 4.86, 2.55)), (2.4, 0.03, 1.15), mat("M_Banner", (0.55, 0.05, 0.06), 0.7))
decal("Logo_Banner", CM, O_M + V((0, 4.84, 2.55)), 2.0, (R_(90), 0, 0), logo_mat("M_LogoWhite", "white"))
cr0 = next(o for o in crate if o.name == "wooden_crate_01")
bpy.context.view_layer.update()
cmn = [cr0.matrix_world @ V(c) for c in cr0.bound_box]
front_y = min(p.y for p in cmn); cz = (min(p.z for p in cmn) + max(p.z for p in cmn)) / 2
decal("Logo_Crate", CM, V((sum(p.x for p in cmn) / 8, front_y - 0.004, cz)), 0.55, (R_(90), 0, R_(20)), logo_mat("M_LogoDark", "dark"), parent=cr0)

# ================================================================== MACRO (200,0): sky-blue gradient dome
CX = coll("SET_Macro"); O_X = V((200, 0, 1.5))
bpy.ops.mesh.primitive_uv_sphere_add(radius=12, location=O_X, segments=48, ring_count=24); dome = bpy.context.active_object; dome.name = "Macro_Dome"; link(dome, CX)
m = bpy.data.materials.new("M_SkyGradient"); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
tc = nt.nodes.new('ShaderNodeTexCoord'); sp = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sp.inputs[0])
mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -6; mr.inputs['From Max'].default_value = 8; nt.links.new(sp.outputs['Z'], mr.inputs['Value'])
crp = nt.nodes.new('ShaderNodeValToRGB'); crp.color_ramp.elements[0].color = (0.80, 0.93, 1.0, 1); crp.color_ramp.elements[1].color = (0.08, 0.55, 0.92, 1)
nt.links.new(mr.outputs['Result'], crp.inputs[0])
em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.0; nt.links.new(crp.outputs[0], em.inputs['Color'])
nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs['Surface']); dome.data.materials.append(m)
for p in dome.data.polygons: p.use_smooth = True
dome.visible_shadow = False; dome.visible_diffuse = False; dome.visible_glossy = True
for nm_, loc, e in (("MacKey", (2.0, -2.5, 3.0), 250), ("MacFill", (-2.5, -1.5, 1.0), 90), ("MacRim", (0.0, 3.0, 2.5), 160)):
    L = bpy.data.lights.new(nm_, 'AREA'); L.energy = e; L.size = 1.5; lo = bpy.data.objects.new(nm_, L); CX.objects.link(lo)
    lo.location = O_X + V(loc); lo.rotation_euler = (V(loc) * -1).to_track_quat('-Z', 'Y').to_euler()
SW_MACRO.location = O_X + V((-0.34, 0, 0)); SW_MACRO.rotation_euler = (0, R_(90), R_(-90))      # horizontal along x, flat of the blade to camera (-y)

# ================================================================== CAMP (300,0)
CC = coll("SET_Camp"); O_C = V((300, 0, 0))
def camp_h(x, y):
    z = -0.4 + 0.5 * ss((y + 1.0) / 3.0) + 0.04 * max(0.0, y - 2.0) ** 1.1
    z += 0.35 * ss((-y - 45.0) / 8.0) + 0.03 * max(0.0, -y - 53.0)
    return z + 0.03 * noise(V((x * 0.5, y * 0.5, 2.0))) + 0.01 * noise(V((x * 2.7, y * 2.7, 3.0)))
CAMP_H = camp_h
MC = shore_material("M_CampShore", "forrest_sand_01", "leafy_grass", 0.25)
terrain("Camp_Ground", O_C, 60, 90, 0.25, camp_h, [MC], CC)
water_plane("Camp_Water", O_C + V((0, -25, 0.0)), 60, 50, CC)
rng = random.Random(11)
forest(CC, O_C, (-28, 28), (11, 34), 70, rng, avoid=lambda x, y: abs(x) < 7 and y < 14, hz=camp_h)
forest(CC, O_C, (-30, 30), (-75, -55), 45, rng, (1.0, 1.4), hz=camp_h)
for i in range(110):
    x = rng.uniform(-18, 18); y = rng.uniform(3.0, 14.0)
    if abs(x) < 5 and 3 < y < 9: continue
    instance(P_GRASS, O_C + V((x, y, camp_h(x, y) - 0.03)), rng.uniform(0, 6.28), rng.uniform(0.5, 0.9), CC)
tent = glb("tent"); link(tent, CC); fit(tent, height=2.6)
for i, (x, y, rz) in enumerate(((-3.6, 7.5, 15), (3.8, 8.2, -20))):
    t = tent.copy(); t.data = tent.data; CC.objects.link(t); t.location = O_C + V((x, y, camp_h(x, y) - 0.03)); t.rotation_euler.z = R_(rz)
bpy.data.objects.remove(tent, do_unlink=True)
boat = glb("rowboat"); link(boat, CC); fit(boat, length=4.2)
for o_ in [boat]:      # weathered dark wood, not red paint
    for i, m_ in enumerate(o_.data.materials):
        if m_: o_.data.materials[i] = tex_mat("wood_floor", 1.0, 0.8, 0.2, tint=(0.75, 0.55, 0.38))
B1 = boat.copy(); B1.data = boat.data; CC.objects.link(B1); B1.name = "Boat_Beach"
B1.location = O_C + V((2.6, 1.6, camp_h(2.6, 1.6) - 0.06)); B1.rotation_euler = (R_(2), R_(-4), R_(70))
boat.name = "Boat_Water"; boat.location = O_C + V((-1.5, -3.2, -0.08)); boat.rotation_euler = (0, 0, R_(10))
sc["BOAT_WATER"] = tuple(boat.location)
fp = ph_objects("stone_fire_pit")[0]; link(fp, CC); fp.location = O_C + V((0.4, 5.2, camp_h(0.4, 5.2) + 0.02))
br = ph_objects("dry_branches_medium_01", lambda n: n.endswith("_a"))[0]; link(br, CC); br.location = fp.location + V((0, 0, 0.05)); br.scale = (0.55, 0.55, 0.55)
# small stylised fire: three flame blobs, emissive, scale keyed (no sim)
mfl = mat("M_Flame", (1.0, 0.35, 0.05), 0.5, emit=((1.0, 0.42, 0.06), 6.0))
for i in range(3):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.055, location=fp.location + V((0.06 * math.cos(i * 2.1), 0.06 * math.sin(i * 2.1), 0.12)))
    f_ = bpy.context.active_object; f_.name = "Flame%d" % i; link(f_, CC); f_.data.materials.append(mfl); f_.visible_shadow = False
    for k in range(0, 4000, 9):
        h = 1.6 + 0.6 * math.sin(k * 0.7 + i * 1.9) + 0.3 * math.sin(k * 1.9 + i); f_.scale = (0.8, 0.8, h); f_.keyframe_insert("scale", frame=1 + k)
fl_l = bpy.data.lights.new("FireLight", 'POINT'); fl_l.energy = 40; fl_l.color = (1.0, 0.55, 0.2); fll = bpy.data.objects.new("FireLight", fl_l); CC.objects.link(fll); fll.location = fp.location + V((0, 0, 0.5))
for i in range(5):
    x = rng.uniform(-6, 6); y = rng.uniform(2.6, 4.0)
    instance(P_ROCK, O_C + V((x, y, camp_h(x, y) - 0.1)), rng.uniform(0, 6.28), rng.uniform(0.15, 0.25), CC)
instance(P_STUMP, O_C + V((-1.6, 4.6, camp_h(-1.6, 4.6) - 0.05)), 0.3, 1.0, CC)

sc["LAKE_ORIGIN"] = tuple(O_L); sc["MUS_ORIGIN"] = tuple(O_M); sc["MACRO_ORIGIN"] = tuple(O_X); sc["CAMP_ORIGIN"] = tuple(O_C)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
bpy.context.view_layer.update()
for o in (SW_FOUND, SW_WAR, SW_MACRO): print("SWPOS", o.name, tuple(round(x, 2) for x in o.matrix_world.translation), tuple(round(x, 2) for x in (o.matrix_world.to_3x3() @ V((0, 1, 0)))), o.data.vertices.__len__())
print("SETS_OK")
