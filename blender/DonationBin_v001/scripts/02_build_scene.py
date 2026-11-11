"""DonationBin set: render settings, lot, steel clothing bin with one-way flap mechanism, clothes pile, props, lights.
blender -b humans.blend --python 02_build_scene.py -- <assets_root(/opt/assets)> <out.blend>"""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, noise

argv = sys.argv[sys.argv.index("--") + 1:]
A, OUT = argv[0], argv[1]
PH = os.path.join(A, "ph")
sc = bpy.context.scene
FPS, END = 60, 2490
random.seed(9)

# ------------------------------------------------------------------ render settings
sc.render.fps, sc.render.fps_base = FPS, 1.0
sc.frame_start, sc.frame_end, sc.frame_step = 1, END, 1
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
sc.render.filepath = "//render/DonationBin_v001_"

col_set = bpy.data.collections.new("SET"); sc.collection.children.link(col_set)

# ------------------------------------------------------------------ helpers
def link(o, col=None):
    (col or col_set).objects.link(o); return o

def mat_from(lib_blend, name, scale=None):
    with bpy.data.libraries.load(lib_blend, link=False) as (src, dst):
        dst.materials = [name]
    m = dst.materials[0]
    if scale is not None:
        for nd in m.node_tree.nodes:
            if nd.type == 'MAPPING':
                nd.inputs['Scale'].default_value = (scale, scale, scale)
    return m

def objs_from(lib_blend, names):
    with bpy.data.libraries.load(lib_blend, link=False) as (src, dst):
        dst.objects = [n for n in names if n in src.objects]
    out = []
    for o in dst.objects:
        if o is not None:
            link(o); out.append(o)
    return out

def principled(name, rgb, rough=0.5, metal=0.0, emit=None, estr=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = rgb + (1,); p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    if emit:
        p.inputs['Emission Color'].default_value = emit + (1,); p.inputs['Emission Strength'].default_value = estr
    return m

def box(name, ctr, size, mat=None, col=None, bevel=0.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.location = ctr
    if mat: me.materials.append(mat)
    link(o, col)
    if bevel:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = 2; b.limit_method = 'ANGLE'
    return o

def uv_box(o, s=1.0):
    """cube-project UVs in object space (meters * s)"""
    me = o.data
    if not me.uv_layers: me.uv_layers.new()
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        n = poly.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            co = o.matrix_world @ co if False else co
            u, v = [(co.y, co.z), (co.x, co.z), (co.x, co.y)][ax]
            uv[li].uv = (u * s, v * s)

def join(objs, name):
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active; o.name = name; o.data.name = name
    return o

# ------------------------------------------------------------------ materials
M_ASPH = mat_from(f"{PH}/asphalt_02/asphalt_02_2k.blend", "asphalt_02", 1.0)
M_BRICK = mat_from(f"{PH}/brick_wall_02/brick_wall_02_2k.blend", "brick_wall_02", 1.0)
M_SHUT = mat_from(f"{PH}/painted_metal_shutter/painted_metal_shutter_2k.blend", "painted_metal_shutter", 1.0)
M_CONC = mat_from(f"{PH}/concrete_floor_02/concrete_floor_02_2k.blend", "concrete_floor_02", 1.0)
M_DENIM = mat_from(f"{PH}/denim_fabric/denim_fabric_2k.blend", "denim_fabric", 1.0)
M_TERRY = mat_from(f"{PH}/terry_cloth/terry_cloth_2k.blend", "terry_cloth", 1.0)
M_GREEN = mat_from(f"{PH}/green_metal_rust/green_metal_rust_2k.blend", "green_metal_rust", 1.0)

def xray_wrap(m, name):
    """bin steel -> cyan x-ray ghost, controlled by the node value 'XRAY' (0 steel, 1 ghost)"""
    nt = m.node_tree; n, l = nt.nodes, nt.links
    outn = next(x for x in n if x.type == 'OUTPUT_MATERIAL')
    surf = outn.inputs['Surface'].links[0].from_socket
    val = n.new('ShaderNodeValue'); val.name = val.label = "XRAY"; val.outputs[0].default_value = 0.0
    fr = n.new('ShaderNodeFresnel'); fr.inputs['IOR'].default_value = 1.25
    em = n.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.35, 0.85, 1.0, 1)
    mul = n.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 3.0
    l.new(fr.outputs[0], mul.inputs[0]); l.new(mul.outputs[0], em.inputs['Strength'])
    tr = n.new('ShaderNodeBsdfTransparent'); tr.inputs['Color'].default_value = (0.85, 0.95, 1.0, 1)
    ad = n.new('ShaderNodeAddShader'); l.new(em.outputs[0], ad.inputs[0]); l.new(tr.outputs[0], ad.inputs[1])
    mx = n.new('ShaderNodeMixShader'); l.new(val.outputs[0], mx.inputs['Fac'])
    l.new(surf, mx.inputs[1]); l.new(ad.outputs[0], mx.inputs[2]); l.new(mx.outputs[0], outn.inputs['Surface'])
    if outn.inputs['Displacement'].links:
        nt.links.remove(outn.inputs['Displacement'].links[0])
    m.name = name
    return m

M_BIN = xray_wrap(M_GREEN, "BinSteel")
M_BIN_IN = xray_wrap(M_GREEN.copy(), "BinSteelInner")
# inner faces: darker, smoother galvanised steel look
for nd in M_BIN_IN.node_tree.nodes:
    if nd.type == 'BSDF_PRINCIPLED':
        nd.inputs['Metallic'].default_value = 0.6
M_MECH = xray_wrap(principled("MechSteel", (0.42, 0.42, 0.40), 0.35, 1.0), "MechSteel")
for nd in M_MECH.node_tree.nodes:   # mechanism stays visible (solid-ish orange) in x-ray
    if nd.type == 'EMISSION': nd.inputs['Color'].default_value = (1.0, 0.55, 0.15, 1)
    if nd.type == 'BSDF_TRANSPARENT': nd.inputs['Color'].default_value = (0.2, 0.15, 0.1, 1)
M_LINE = principled("BayLine", (0.85, 0.82, 0.7), 0.6)
M_RUBBER = principled("Rubber", (0.03, 0.03, 0.03), 0.8)

# ------------------------------------------------------------------ ground, wall
bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0)); g = bpy.context.object; g.name = "Ground"
for c_ in g.users_collection: c_.objects.unlink(g)
link(g); g.data.materials.append(M_ASPH)
for uvd in g.data.uv_layers.active.data: uvd.uv = uvd.uv * 26.0
for i, x in enumerate((-9.6, -6.8, -4.0, -1.2, 9.0, 11.8)):  # painted bays (gap left for the bins)
    o = box("BayLine%d" % i, (x, -4.2, 0.002), (0.11, 5.0, 0.004), M_LINE)
box("BayStop", (0.0, -6.75, 0.002), (22, 0.11, 0.004), M_LINE)
WALL_Y = 1.15
wall = box("Wall", (0, WALL_Y + 0.15, 2.5), (44, 0.3, 5.0), M_BRICK); uv_box(wall, 0.45)
curb = box("Curb", (0, WALL_Y - 0.12, 0.06), (44, 0.24, 0.12), M_CONC); uv_box(curb, 0.6)
sh = box("Shutter", (-5.2, WALL_Y - 0.03, 1.55), (3.4, 0.06, 3.1), M_SHUT); uv_box(sh, 0.3)
box("ShutterHood", (-5.2, WALL_Y - 0.15, 3.2), (3.6, 0.3, 0.25), principled("HoodGrey", (0.3, 0.3, 0.3), 0.5, 0.8))
# puddles
M_PUD = principled("Puddle", (0.02, 0.02, 0.025), 0.02, 0.0)
for i, (x, y, s) in enumerate(((1.8, -2.6, 1.0), (-2.9, -4.4, 1.6), (3.9, -6.0, 1.2))):
    bpy.ops.mesh.primitive_circle_add(vertices=24, radius=0.6 * s, fill_type='NGON', location=(x, y, 0.003))
    pd = bpy.context.object; pd.name = "Puddle%d" % i; pd.scale = (1.0, 0.6, 1)
    for c_ in pd.users_collection: c_.objects.unlink(pd)
    link(pd); pd.data.materials.append(M_PUD)

# ------------------------------------------------------------------ the bin
BW, BD, BH = 1.5, 1.2, 2.15
T = 0.012
CH_Z0, CH_Z1, CH_X = 1.12, 1.62, 0.42       # chute opening
FY = -BD / 2                                  # front face plane
sc["bin_front_y"] = FY; sc["chute_z"] = (CH_Z0, CH_Z1); sc["chute_x"] = CH_X
col_bin = bpy.data.collections.new("BIN"); sc.collection.children.link(col_bin)
P = []
P.append(box("b_back", (0, BD / 2 - T / 2, BH / 2), (BW, T, BH), M_BIN, col_bin))
P.append(box("b_left", (-BW / 2 + T / 2, 0, BH / 2), (T, BD, BH), M_BIN, col_bin))
P.append(box("b_right", (BW / 2 - T / 2, 0, BH / 2), (T, BD, BH), M_BIN, col_bin))
P.append(box("b_roof", (0, 0.03, BH + 0.01), (BW + 0.06, BD + 0.1, 0.02), M_BIN, col_bin))
P.append(box("b_frontup", (0, FY + T / 2, (CH_Z1 + BH) / 2), (BW, T, BH - CH_Z1), M_BIN, col_bin))
P.append(box("b_jambL", (-(BW / 2 + CH_X) / 2, FY + T / 2, (CH_Z0 + CH_Z1) / 2), (BW / 2 - CH_X, T, CH_Z1 - CH_Z0), M_BIN, col_bin))
P.append(box("b_jambR", ((BW / 2 + CH_X) / 2, FY + T / 2, (CH_Z0 + CH_Z1) / 2), (BW / 2 - CH_X, T, CH_Z1 - CH_Z0), M_BIN, col_bin))
P.append(box("b_frontlo_strip", (0, FY + T / 2, CH_Z0 - 0.05), (BW, T, 0.10), M_BIN, col_bin))
P.append(box("b_floor", (0, 0, 0.06), (BW, BD, 0.02), M_BIN, col_bin))
for x in (-BW / 2 + 0.06, BW / 2 - 0.06):
    for y in (-BD / 2 + 0.06, BD / 2 - 0.06):
        P.append(box("b_foot", (x, y, 0.025), (0.08, 0.08, 0.05), M_RUBBER, col_bin))
# hood over the chute, sill / stop bar below it
hood = box("b_hood", (0, FY - 0.13, CH_Z1 + 0.10), (2 * CH_X + 0.14, 0.26, 0.012), M_BIN, col_bin)
hood.rotation_euler.x = math.radians(-24); P.append(hood)
for sx in (-1, 1):
    P.append(box("b_hoodside", (sx * (CH_X + 0.07), FY - 0.12, CH_Z1 + 0.02), (0.012, 0.24, 0.26), M_BIN, col_bin))
BIN = join(P, "BinShell")
uv_box(BIN, 0.55)
# inner liner (separate object so its faces render the inner steel)
inner = []
for nm, ctr, size in (("i_back", (0, BD / 2 - T - 0.002, BH / 2), (BW - 2 * T, 0.002, BH - 0.1)),
                      ("i_left", (-BW / 2 + T + 0.002, 0, BH / 2), (0.002, BD - 2 * T, BH - 0.1)),
                      ("i_right", (BW / 2 - T - 0.002, 0, BH / 2), (0.002, BD - 2 * T, BH - 0.1))):
    inner.append(box(nm, ctr, size, M_BIN_IN, col_bin))
INNER = join(inner, "BinLiner"); uv_box(INNER, 0.55)
# cut panel (front, below the chute): the firefighters cut and peel this; hinged on its left edge
cp = box("CutPanel", (0, 0, 0), (BW - 0.04, T, CH_Z0 - 0.15), M_BIN, col_bin)
cp.data.transform(Matrix.Translation(Vector(((BW - 0.04) / 2, 0, (CH_Z0 - 0.15) / 2))))
cp.location = (-BW / 2 + 0.02, FY + T / 2, 0.06)
cpm = cp.data
bm = bmesh.new(); bm.from_mesh(cpm); bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=12, use_grid_fill=True); bm.to_mesh(cpm); bm.free()
uv_box(cp, 0.55)
# (folds down on its bottom edge in 03_animate)
# flap: hinged at the top edge, swings inward (+rot X); plate just inside the opening
fl = box("Flap", (0, 0, 0), (2 * CH_X - 0.03, 0.01, CH_Z1 - CH_Z0 - 0.025), M_MECH, col_bin)
fl.data.transform(Matrix.Translation(Vector((0, 0, -(CH_Z1 - CH_Z0 - 0.025) / 2))))
fl.location = (0, FY + T + 0.012, CH_Z1 - 0.005)
uv_box(fl, 0.55)
pin = box("HingePin", (0, 0, 0), (2 * CH_X + 0.06, 0.03, 0.03), M_MECH, col_bin); pin.parent = fl
arm = box("CounterArm", (0, 0, 0), (0.04, 0.03, 0.30), M_MECH, col_bin); arm.parent = fl
arm.location = (0.30, 0.04, 0.12); arm.rotation_euler.x = math.radians(-30)
cw = box("CounterWeight", (0, 0, 0), (0.12, 0.08, 0.08), M_MECH, col_bin); cw.parent = arm; cw.location = (0, 0, 0.16)
stop = box("StopBar", (0, FY - 0.035, CH_Z0 - 0.005), (2 * CH_X + 0.06, 0.05, 0.03), M_MECH, col_bin)
pawl = box("Pawl", (0, 0, 0), (0.05, 0.12, 0.025), M_MECH, col_bin)
pawl.data.transform(Matrix.Translation(Vector((0, 0.06, 0))))
pawl.location = (-0.25, FY + T + 0.03, CH_Z0 + 0.03)
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.022, depth=0.18, location=(-0.36, FY + 0.06, CH_Z1 + 0.06))
spr = bpy.context.object; spr.name = "Spring"; spr.rotation_euler.x = math.radians(60)
for c_ in spr.users_collection: c_.objects.unlink(spr)
col_bin.objects.link(spr); spr.data.materials.append(M_MECH)
sw = spr.modifiers.new("coil", 'WIREFRAME'); sw.thickness = 0.006
# a slit light leak around the closed flap is part of the opening gap (flap is 3 cm narrower/shorter)

# ------------------------------------------------------------------ clothes pile inside
def pile_h(x, y):
    return 0.25 + 0.20 * math.exp(-((x + 0.15) ** 2 + (y - 0.25) ** 2) / 0.35) + 0.06 * noise.noise(Vector((x * 2.2, y * 2.2, 0.3)))
sc["pile_fn"] = "0.25+0.20*exp(-((x+0.15)^2+(y-0.25)^2)/0.35)+0.06*noise"
bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=48, size=1.0, location=(0, 0, 0))
pile = bpy.context.object; pile.name = "Pile"
for c_ in pile.users_collection: c_.objects.unlink(pile)
col_bin.objects.link(pile)
for v in pile.data.vertices:
    x, y = v.co.x * (BW - 0.04), v.co.y * (BD - 0.04)
    v.co = Vector((x, y, pile_h(x, y) + 0.025 * noise.noise(Vector((x * 9, y * 9, 1.7)))))
M_PILE = bpy.data.materials.new("ClothPile"); M_PILE.use_nodes = True
nt = M_PILE.node_tree; n, l = nt.nodes, nt.links
p = n["Principled BSDF"]; p.inputs['Roughness'].default_value = 0.9
p.inputs['Sheen Weight'].default_value = 0.4
tc = n.new('ShaderNodeTexCoord'); vor = n.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 7.0
l.new(tc.outputs['Object'], vor.inputs['Vector'])
ramp = n.new('ShaderNodeValToRGB'); cr = ramp.color_ramp; cr.interpolation = 'CONSTANT'
pal = [(0.08, 0.12, 0.25), (0.45, 0.08, 0.07), (0.6, 0.55, 0.45), (0.15, 0.25, 0.12), (0.7, 0.68, 0.62), (0.25, 0.2, 0.18), (0.55, 0.35, 0.1), (0.1, 0.1, 0.1)]
for i, rgb in enumerate(pal):
    e = cr.elements[0] if i == 0 else (cr.elements[1] if i == 1 else cr.elements.new(0))
    e.position = i / len(pal); e.color = rgb + (1,)
l.new(vor.outputs['Color'], ramp.inputs['Fac']) if 'Color' in vor.outputs else None
wave = n.new('ShaderNodeTexWave'); wave.inputs['Scale'].default_value = 60; wave.inputs['Distortion'].default_value = 6
l.new(tc.outputs['Object'], wave.inputs['Vector'])
mixc = n.new('ShaderNodeMix'); mixc.data_type = 'RGBA'; mixc.blend_type = 'MULTIPLY'; mixc.inputs['Factor'].default_value = 0.35
sep = n.new('ShaderNodeSeparateColor'); l.new(vor.outputs['Color'], sep.inputs['Color'])
l.new(sep.outputs[0], ramp.inputs['Fac'])
l.new(ramp.outputs['Color'], mixc.inputs['A']); l.new(wave.outputs['Color'], mixc.inputs['B'])
l.new(mixc.outputs['Result'], p.inputs['Base Color'])
bmp = n.new('ShaderNodeBump'); bmp.inputs['Strength'].default_value = 0.4
l.new(wave.outputs['Fac'], bmp.inputs['Height']); l.new(bmp.outputs['Normal'], p.inputs['Normal'])
pile.data.materials.append(M_PILE)
for poly in pile.data.polygons: poly.use_smooth = True
# lumpy bags / bundles on the pile
M_BAG_W = principled("BagWhite", (0.75, 0.75, 0.72), 0.25); M_BAG_B = principled("BagBlack", (0.02, 0.02, 0.025), 0.2)
bag_mats = [M_BAG_W, M_BAG_B, M_DENIM, M_TERRY, M_BAG_W, M_DENIM]
BAGS = []
for i in range(26):
    for _ in range(40):
        x = random.uniform(-BW / 2 + 0.2, BW / 2 - 0.2); y = random.uniform(-BD / 2 + 0.2, BD / 2 - 0.2)
        if not (-0.35 < x < 0.45 and -0.45 < y < 0.15):   # leave her landing zone mostly clear of big bags
            break
    r = random.uniform(0.13, 0.22)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=r, location=(x, y, pile_h(x, y) + r * 0.35))
    b = bpy.context.object; b.name = "Bag%02d" % i
    for c_ in b.users_collection: c_.objects.unlink(b)
    col_bin.objects.link(b)
    b.scale = (random.uniform(1.0, 1.6), random.uniform(0.8, 1.2), random.uniform(0.55, 0.8)); b.rotation_euler.z = random.uniform(0, 6.3)
    for v in b.data.vertices:
        v.co += v.co.normalized() * 0.25 * r * noise.noise(v.co * 6 + Vector((i, 0, 0)))
    for poly in b.data.polygons: poly.use_smooth = True
    b.data.materials.append(bag_mats[i % len(bag_mats)]); BAGS.append(b.name)
sc["bags"] = ",".join(BAGS)
# loose clothes draped near the landing zone: flattened lumpy discs
for i in range(10):
    x = random.uniform(-0.35, 0.45); y = random.uniform(-0.45, 0.15)
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=random.uniform(0.15, 0.25), depth=0.03, location=(x, y, pile_h(x, y) + 0.005))
    cl = bpy.context.object; cl.name = "Cloth%02d" % i
    for c_ in cl.users_collection: c_.objects.unlink(cl)
    col_bin.objects.link(cl); cl.rotation_euler = (random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2), random.uniform(0, 6))
    sd = cl.modifiers.new("sub", 'SUBSURF'); sd.levels = 1; sd.render_levels = 2
    for v in cl.data.vertices:
        v.co.z += 0.03 * noise.noise(v.co * 8 + Vector((0, i, 0)))
    cl.data.materials.append([M_DENIM, M_TERRY][i % 2])
# water bottle (empty) beside her
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.035, depth=0.22, location=(0.42, -0.25, pile_h(0.42, -0.25) + 0.035))
bt = bpy.context.object; bt.name = "Bottle"; bt.rotation_euler = (math.radians(90), 0, math.radians(30))
for c_ in bt.users_collection: c_.objects.unlink(bt)
col_bin.objects.link(bt)
mb = bpy.data.materials.new("BottlePET"); mb.use_nodes = True
pb_ = mb.node_tree.nodes["Principled BSDF"]; pb_.inputs['Transmission Weight'].default_value = 1.0; pb_.inputs['Roughness'].default_value = 0.08
bt.data.materials.append(mb)

# ------------------------------------------------------------------ more bins along the wall (beat 11 irony)
for i, x in enumerate((3.3, 5.0, 6.7)):
    for src in (BIN, INNER, cp, fl):
        d = src.copy(); d.data = src.data; d.name = "Row%d_%s" % (i, src.name)
        d.animation_data_clear()
        if src is cp or src is fl: d.parent = None
        col_bin.objects.link(d)
        d.location = src.location + Vector((x, 0.0, 0.0))
        if d.name.endswith("CutPanel"):
            d.modifiers.clear()
    pl2 = pile.copy(); pl2.data = pile.data; pl2.name = "Row%d_Pile" % i; col_bin.objects.link(pl2); pl2.location.x = x
sc["row_bins_x"] = [3.3, 5.0, 6.7]

# ------------------------------------------------------------------ props (Poly Haven CC0)
def place(objs, loc, rz=0.0, s=1.0):
    root = objs[0]
    for o in objs:
        if o.parent is None:
            o.location = Vector(loc) + (o.location - root.location if o is not root else Vector())
            o.rotation_euler.z += math.radians(rz); o.scale = o.scale * s
    return objs
car = objs_from(f"{PH}/covered_car/covered_car_1k.blend", ["covered_car", "covered_car_wheel_01", "covered_car_wheel_02", "covered_car_wheel_03", "covered_car_wheel_04"])
for o in car:
    if o.parent is None and o.name != "covered_car":
        o.parent = car[0] if car[0].name == "covered_car" else None
carroot = bpy.data.objects["covered_car"]; carroot.location = (-5.6, -4.3, carroot.location.z); carroot.rotation_euler.z = math.radians(88)
lamp = objs_from(f"{PH}/street_lamp_01/street_lamp_01_1k.blend", ["street_lamp_01"]); lamp[0].location = (-2.2, -0.2, 0); lamp[0].rotation_euler.z = math.radians(90)
tc_ = objs_from(f"{PH}/metal_trash_can/metal_trash_can_1k.blend", ["metal_trash_can", "metal_trash_can_lid", "metal_trash_can_handle_left", "metal_trash_can_handle_right"])
for o in tc_:
    o.location += Vector((-1.45, 0.45, 0))
tb = objs_from(f"{PH}/trashbag/trashbag_1k.blend", ["trashbag"]); tb[0].location = (-1.05, 0.62, 0); tb[0].rotation_euler.z = 0.7
tb2 = tb[0].copy(); link(tb2); tb2.location = (1.15, 0.7, 0); tb2.rotation_euler.z = 2.1
cb = objs_from(f"{PH}/compost_bags/compost_bags_1k.blend", ["compost_bags_floorstacked"])
for o in cb: o.location = (-3.3, 0.6, 0)
bar = objs_from(f"{PH}/concrete_road_barrier/concrete_road_barrier_1k.blend", ["concrete_road_barrier_LOD0"])
bar[0].location = (2.6, -3.4, 0); bar[0].rotation_euler.z = math.radians(15)
hyd = objs_from(f"{PH}/fire_hydrant/fire_hydrant_1k.blend", ["fire_hydrant_aged", "fire_hydrant"])
for o in hyd:
    if o.parent is None: o.location = (-3.0, -1.6, 0)
box_ = objs_from(f"{PH}/cardboard_box_01/cardboard_box_01_1k.blend", ["cardboard_box_01"])
box_[0].location = (0.95, -0.95, 0); box_[0].rotation_euler.z = 0.4
bx2 = box_[0].copy(); link(bx2); bx2.location = (1.05, -0.9, 0.34); bx2.rotation_euler.z = 1.1; bx2.scale = (0.8, 0.8, 0.8)
crate = objs_from(f"{PH}/plastic_crate_01/plastic_crate_01_1k.blend", ["plastic_crate_01"]); crate[0].location = (-0.95, -0.85, 0); crate[0].rotation_euler.z = -0.3
ub = objs_from(f"{PH}/utility_box_01/utility_box_01_1k.blend", ["utility_box_01_box_low"]); ub[0].location = (1.95, WALL_Y - 0.05, 1.1); ub[0].rotation_euler.z = math.radians(180)
fence = objs_from(f"{PH}/modular_chainlink_fence/modular_chainlink_fence_1k.blend", ["modular_chainlink_fence_post"])
rat = objs_from(f"{PH}/street_rat/street_rat_1k.blend", ["street_rat"]); rat[0].location = (-2.6, 0.85, 0.12)
shr = objs_from(f"{PH}/shrub_01/shrub_01_1k.blend", ["shrub_01_h_LOD0", "shrub_01_i_LOD0"])
for o, loc in zip(shr, ((8.6, 0.6, 0), (-8.0, 0.55, 0))): o.location = loc
wd = objs_from(f"{PH}/weed_plant_02/weed_plant_02_1k.blend", ["weed_plant_02_d_LOD0", "weed_plant_02_e_LOD0"])
for o, loc in zip(wd, ((0.95, 0.95, 0), (-0.8, 0.95, 0))): o.location = loc
for i, (x, y) in enumerate(((2.3, 0.95), (-1.8, 0.98), (-4.0, 0.95), (7.8, 0.95))):
    w2 = wd[i % 2].copy(); link(w2); w2.location = (x, y, 0); w2.rotation_euler.z = i * 1.3
# background parked cars (simple duplicates of the covered car), far side of the lot
for i, (x, y, rz) in enumerate(((-10.5, -8.5, 90), (3.5, -9.5, 92), (7.8, -9.2, 86), (-3.0, -11.0, 270))):
    for o in car:
        if o.parent is None:
            d = o.copy(); link(d); d.location = (x, y, o.location.z); d.rotation_euler.z = math.radians(rz)
            for ch in o.children:
                dc = ch.copy(); link(dc); dc.parent = d
# leaves / litter scattered on the asphalt
M_LEAF = principled("Leaf", (0.35, 0.2, 0.06), 0.7)
LEAVES = []
for i in range(40):
    bpy.ops.mesh.primitive_plane_add(size=0.07, location=(random.uniform(-4, 4), random.uniform(-4.5, 0.8), 0.004))
    lf = bpy.context.object; lf.name = "Leaf%02d" % i; lf.rotation_euler.z = random.uniform(0, 6.3)
    for c_ in lf.users_collection: c_.objects.unlink(lf)
    link(lf); lf.data.materials.append(M_LEAF); LEAVES.append(lf.name)
sc["leaves"] = ",".join(LEAVES)
bpy.ops.mesh.primitive_plane_add(size=0.35, location=(-1.0, -2.0, 0.01))
pbag = bpy.context.object; pbag.name = "PaperBag"
for c_ in pbag.users_collection: c_.objects.unlink(pbag)
link(pbag); pbag.data.materials.append(principled("Paper", (0.62, 0.5, 0.33), 0.8))
sbd = pbag.modifiers.new("sub", 'SUBSURF'); sbd.levels = 2
wv = pbag.modifiers.new("crumple", 'DISPLACE'); tx = bpy.data.textures.new("crumple", 'CLOUDS'); tx.noise_scale = 0.08; wv.texture = tx; wv.strength = 0.06
bm = bmesh.new(); bm.from_mesh(pbag.data); bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=8, use_grid_fill=True); bm.to_mesh(pbag.data); bm.free()

# ------------------------------------------------------------------ world + lights
w = sc.world or bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
n, l = w.node_tree.nodes, w.node_tree.links
for x in list(n): n.remove(x)
envt = n.new('ShaderNodeTexEnvironment'); envt.image = bpy.data.images.load(f"{PH}/hdri/suburban_parking_area_2k.hdr")
mpw = n.new('ShaderNodeMapping'); tcw = n.new('ShaderNodeTexCoord'); l.new(tcw.outputs['Generated'], mpw.inputs['Vector']); l.new(mpw.outputs['Vector'], envt.inputs['Vector'])
mpw.inputs['Rotation'].default_value = (0, 0, math.radians(30))
bgh = n.new('ShaderNodeBackground'); bgh.name = "BG_HDRI"; l.new(envt.outputs['Color'], bgh.inputs['Color']); bgh.inputs['Strength'].default_value = 1.0
# studio gradient for the x-ray explainer
grad = n.new('ShaderNodeTexGradient'); grad.gradient_type = 'LINEAR'
sepw = n.new('ShaderNodeSeparateXYZ'); l.new(tcw.outputs['Generated'], sepw.inputs['Vector'])
gr = n.new('ShaderNodeValToRGB'); gr.color_ramp.elements[0].color = (0.75, 0.93, 1.0, 1); gr.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1)
gr.color_ramp.elements[0].position = 0.35; gr.color_ramp.elements[1].position = 0.75
l.new(sepw.outputs['Z'], gr.inputs['Fac'])
bgs = n.new('ShaderNodeBackground'); bgs.name = "BG_STUDIO"; l.new(gr.outputs['Color'], bgs.inputs['Color']); bgs.inputs['Strength'].default_value = 1.2
mxw = n.new('ShaderNodeMixShader'); mxw.name = "STUDIO_MIX"; mxw.inputs['Fac'].default_value = 0.0
l.new(bgh.outputs[0], mxw.inputs[1]); l.new(bgs.outputs[0], mxw.inputs[2])
ow = n.new('ShaderNodeOutputWorld'); l.new(mxw.outputs[0], ow.inputs['Surface'])
sun_d = bpy.data.lights.new("Sun", 'SUN'); sun_d.energy = 3.2; sun_d.angle = math.radians(1.5); sun_d.color = (1.0, 0.95, 0.88)
sun = bpy.data.objects.new("Sun", sun_d); link(sun)
sun.rotation_euler = (math.radians(52), 0, math.radians(-160))   # from front-left, high enough to light the chute interior
fill_d = bpy.data.lights.new("BinFill", 'AREA'); fill_d.energy = 6.0; fill_d.size = 0.9; fill_d.color = (0.85, 0.9, 1.0)
fill = bpy.data.objects.new("BinFill", fill_d); col_bin.objects.link(fill); fill.location = (0, 0.1, 1.95)
slot_d = bpy.data.lights.new("SlotBeam", 'SPOT'); slot_d.energy = 120; slot_d.spot_size = math.radians(40); slot_d.spot_blend = 0.4; slot_d.color = (1, 0.93, 0.8)
slot = bpy.data.objects.new("SlotBeam", slot_d); col_bin.objects.link(slot); slot.location = (0, FY - 1.3, CH_Z1 + 1.0)
slot.rotation_euler = (Vector((0, 0.15, 0.45)) - slot.location).to_track_quat("-Z", "Y").to_euler()
studio_d = bpy.data.lights.new("StudioKey", 'AREA'); studio_d.energy = 0.0; studio_d.size = 3.0
studio = bpy.data.objects.new("StudioKey", studio_d); link(studio); studio.location = (-3.0, -3.0, 4.0)
studio.rotation_euler = (math.radians(50), 0, math.radians(-45))
print("SCENE_DONE", len(bpy.data.objects))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
