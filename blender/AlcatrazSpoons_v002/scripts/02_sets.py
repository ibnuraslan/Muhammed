"""AlcatrazSpoons sets and props.  blender -b chars.blend --python 02_sets.py -- <assets_dir> <brand_dir> <out.blend>
S1 cell (origin) | S2 service corridor (x=30) | S3 ladder shaft (x=60) | S3b outside wall + vent pipe (x=90) | S4 bay (x=300)."""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
a = sys.argv[sys.argv.index("--") + 1:]; AS, BRAND, OUT = a[0], a[1], a[2]
sc = bpy.context.scene; V = Vector; R_ = math.radians
random.seed(11)
COLS = {}
def col(name):
    if name not in COLS:
        c = bpy.data.collections.new(name); sc.collection.children.link(c); COLS[name] = c
    return COLS[name]
def link(o, cname):
    for c in o.users_collection: c.objects.unlink(o)
    col(cname).objects.link(o); return o

# ------------------------------------------------------------------ materials
def tex_mat(name, tid, tint=(1, 1, 1), scale=1.0, bump=0.3, rough_min=0.45, sat=1.0):
    """Poly Haven texture set -> clean, lightly bumped, tinted material (STYLE_ANIMATED: bump <=0.35, roughness >=0.35)"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    d = os.path.join(AS, tid, "textures")
    def img(key, non_color):
        f = [x for x in os.listdir(d) if key in x]
        if not f: return None
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(os.path.join(d, f[0]), check_existing=True)
        if non_color: n.image.colorspace_settings.name = 'Non-Color'
        n.projection = 'BOX'; n.projection_blend = 0.25
        return n
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale,) * 3
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    dif = img("diff", False)
    if dif:
        nt.links.new(mp.outputs[0], dif.inputs[0])
        hs = nt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = sat
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        mx.inputs['B'].default_value = (*tint, 1)
        nt.links.new(dif.outputs['Color'], hs.inputs['Color']); nt.links.new(hs.outputs[0], mx.inputs['A']); nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])
    rg = img("rough", True)
    if rg:
        nt.links.new(mp.outputs[0], rg.inputs[0]); mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = rough_min
        nt.links.new(rg.outputs['Color'], mr.inputs['Value']); nt.links.new(mr.outputs[0], P.inputs['Roughness'])
    nr = img("nor_gl", True)
    if nr:
        nt.links.new(mp.outputs[0], nr.inputs[0]); nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = bump
        nt.links.new(nr.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs[0], P.inputs['Normal'])
    return m

def flat(name, rgb, rough=0.5, metal=0.0, emit=None, estr=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; P = m.node_tree.nodes["Principled BSDF"]
    P.inputs['Base Color'].default_value = (*rgb, 1); P.inputs['Roughness'].default_value = rough; P.inputs['Metallic'].default_value = metal
    if emit: P.inputs['Emission Color'].default_value = (*emit, 1); P.inputs['Emission Strength'].default_value = estr
    return m

def paint(name, rgb, var=0.06):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 4.0
    tc = nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 1 - var; mr.inputs['To Max'].default_value = 1 + var
    nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    mx.inputs['A'].default_value = (*rgb, 1); nt.links.new(mr.outputs[0], mx.inputs['B']); nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.08; nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], P.inputs['Normal'])
    P.inputs['Roughness'].default_value = 0.6
    return m
M_WALL = paint("M_CellWall", (0.46, 0.6, 0.44))          # pale prison green, clean paint
M_WALL_LO = paint("M_CellWallLow", (0.22, 0.34, 0.25))   # darker dado band
M_FLOOR = tex_mat("M_Floor", "concrete_floor_02", tint=(0.7, 0.7, 0.68), scale=0.5, bump=0.25, sat=0.4)
M_CONC = tex_mat("M_Concrete", "concrete_wall_006", tint=(0.8, 0.8, 0.78), scale=0.5, bump=0.3)
M_BRICK = tex_mat("M_Brick", "red_brick_03", tint=(0.95, 0.8, 0.75), scale=0.9, bump=0.3, sat=0.85)
M_BRICK_GREY = tex_mat("M_BrickGrey", "red_brick_03", tint=(0.7, 0.75, 0.82), scale=0.9, bump=0.3, sat=0.15)
M_STEEL = flat("M_Steel", (0.32, 0.34, 0.36), 0.38, 0.85)
M_BARS = flat("M_Bars", (0.18, 0.2, 0.22), 0.4, 0.8)
M_GRILLE = flat("M_Grille", (0.55, 0.58, 0.55), 0.45, 0.7)
M_SPOON = flat("M_Spoon", (0.85, 0.85, 0.86), 0.22, 1.0)
M_DARK = flat("M_HoleDark", (0.015, 0.015, 0.015), 0.9)
M_RUBBLE = paint("M_Rubble", (0.62, 0.62, 0.58), var=0.15)
M_MATT = flat("M_Mattress", (0.55, 0.52, 0.42), 0.8)
M_BLANKET = flat("M_Blanket", (0.13, 0.16, 0.12), 0.85)      # dark olive army blanket
M_PILLOW = flat("M_Pillow", (0.88, 0.87, 0.82), 0.8)
M_PORC = flat("M_Porcelain", (0.92, 0.93, 0.92), 0.2)
M_RED = flat("M_RedCord", (0.75, 0.06, 0.04), 0.5)
M_MOTOR = flat("M_MotorBody", (0.16, 0.22, 0.18), 0.4, 0.35)     # enamelled motor housing
M_MOTOR_CAP = flat("M_MotorCap", (0.12, 0.25, 0.42), 0.4, 0.2)
M_COPPER = flat("M_Copper", (0.85, 0.45, 0.25), 0.3, 1.0)
M_WOODB = flat("M_Board", (0.5, 0.36, 0.22), 0.6)

def box(name, size, loc, mat, cname, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel: o.modifiers.new("Bev", 'BEVEL').width = bevel
    o.data.materials.append(mat); return link(o, cname)
def cyl(name, r, depth, loc, mat, cname, rot=(0, 0, 0), verts=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.data.materials.append(mat)
    for p in o.data.polygons: p.use_smooth = True
    return link(o, cname)
def append_model(tid, cname, loc, rot=(0, 0, 0), scale=1.0, names=None):
    f = os.path.join(AS, tid, tid + "_1k.blend")
    with bpy.data.libraries.load(f) as (df, dt): dt.objects = [n for n in df.objects if names is None or n in names]
    out = []
    for o in dt.objects:
        if o is None or o.type != 'MESH': continue
        sc.collection.objects.link(o); link(o, cname); o.location = V(loc) + Euler(rot).to_matrix() @ (o.location * scale)
        o.rotation_euler = rot; o.scale = (scale,) * 3; out.append(o)
    return out
def area(name, loc, rot, size, energy, color, cname, shape='RECTANGLE', sy=None):
    L = bpy.data.lights.new(name, 'AREA'); L.size = size; L.energy = energy; L.color = color; L.shape = shape
    if sy: L.size_y = sy
    o = bpy.data.objects.new(name, L); o.location = loc; o.rotation_euler = rot; col(cname).objects.link(o); return o
def point(name, loc, energy, color, cname, r=0.05):
    L = bpy.data.lights.new(name, 'POINT'); L.energy = energy; L.color = color; L.shadow_soft_size = r
    o = bpy.data.objects.new(name, L); o.location = loc; col(cname).objects.link(o); return o

# ================================================================== S1 CELL (origin)
C1 = "S1_Cell"
W, D, H = 2.4, 3.2, 2.6           # interior: x -1.2..1.2, y -1.6..1.6
VX, VZ = 0.20, 0.42               # vent centre on the back wall (y = +1.6)
BAX = 0.80                        # basin beside the vent (head room for a man kneeling at it)
box("S1_Floor", (8, 9, 0.2), (0, -1.0, -0.1), M_FLOOR, C1)
box("S1_Ceiling", (2.8, 3.6, 0.2), (0, 0, H + 0.1), M_WALL, C1)
box("S1_WallL", (0.2, 3.6, H), (-1.3, 0, H / 2), M_WALL, C1)
box("S1_WallR", (0.2, 3.6, H), (1.3, 0, H / 2), M_WALL, C1)
for nm, x in (("S1_DadoL", -1.195), ("S1_DadoR", 1.195)):
    box(nm, (0.01, 3.2, 0.9), (x, 0, 0.45), M_WALL_LO, C1)
# back wall with the dug hole round the vent (boolean, the cutter grows in shot 2d)
bw = box("S1_WallBack", (2.8, 0.25, H), (0, 1.6 + 0.125, H / 2), M_WALL, C1)
box("S1_DadoBack", (2.4, 0.01, 0.9), (0, 1.595, 0.45), M_WALL_LO, C1)
db = bpy.data.objects["S1_DadoBack"]
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=28, radius1=1.0, radius2=1.0, depth=1.2)
for v in bm.verts:
    ang = math.atan2(v.co.y, v.co.x); rr = 1.0 + 0.10 * math.sin(3 * ang + 0.7) + 0.06 * math.sin(7 * ang)
    v.co.x *= 0.215 * rr; v.co.y *= 0.165 * rr
me = bpy.data.meshes.new("S1_HoleCutter"); bm.to_mesh(me); bm.free()
cut = bpy.data.objects.new("S1_HoleCutter", me); col(C1).objects.link(cut)
cut.rotation_euler = (R_(90), 0, 0); cut.location = (VX, 1.6, VZ); cut.display_type = 'WIRE'; cut.hide_render = True
cut.scale = (0.78, 0.78, 1.0)        # dug to just round the grille at the start (shot 2d grows it to 1.0)
for o in (bw, db):
    b = o.modifiers.new("Hole", 'BOOLEAN'); b.object = cut; b.operation = 'DIFFERENCE'; b.solver = 'EXACT'
box("S1_HoleBack", (0.9, 0.05, 0.8), (VX, 1.6 + 0.30, VZ + 0.1), M_DARK, C1)    # darkness behind the hole
# vent grille (frame + louvres) sitting in the hole
def make_grille(name, cname, loc, rot):
    parts = []
    gw, gh, t = 0.30, 0.21, 0.018
    for nm, sz, lc in (("T", (gw, 0.02, t), (0, 0, gh / 2 - t / 2)), ("B", (gw, 0.02, t), (0, 0, -gh / 2 + t / 2)),
                       ("L", (t, 0.02, gh), (-gw / 2 + t / 2, 0, 0)), ("R", (t, 0.02, gh), (gw / 2 - t / 2, 0, 0))):
        parts.append(box(name + "_" + nm, sz, lc, M_GRILLE, cname, bevel=0.002))
    for i in range(7):
        z = -gh / 2 + t + (i + 0.5) * (gh - 2 * t) / 7
        s = box(name + "_s%d" % i, (gw - 2 * t, 0.003, 0.022), (0, 0, z), M_GRILLE, cname)
        s.rotation_euler = (R_(40), 0, 0); parts.append(s)
    for p in parts: p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.select_all(action='DESELECT')
    for p in parts: p.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    bpy.ops.object.join(); g = bpy.context.active_object; g.name = name
    g.location = loc; g.rotation_euler = rot
    return g
G1 = make_grille("S1_Grille", C1, (VX, 1.6 - 0.005, VZ), (0, 0, 0))
# basin above the vent
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > 0.05], context='VERTS')
for v in bm.verts: v.co = V((v.co.x * 0.24, v.co.y * 0.19, v.co.z * 0.14))
me = bpy.data.meshes.new("S1_Basin"); bm.to_mesh(me); bm.free()
bas = bpy.data.objects.new("S1_Basin", me); col(C1).objects.link(bas); bas.location = (BAX, 1.6 - 0.2, 0.86)
bas.modifiers.new("Sol", 'SOLIDIFY').thickness = 0.02; bas.modifiers.new("Sub", 'SUBSURF').levels = 1; me.materials.append(M_PORC)
for p in me.polygons: p.use_smooth = True
box("S1_BasinRim", (0.5, 0.40, 0.03), (BAX, 1.6 - 0.2, 0.875), M_PORC, C1, bevel=0.01)
cyl("S1_Tap", 0.012, 0.12, (BAX, 1.6 - 0.04, 0.95), M_STEEL, C1, rot=(R_(90), 0, 0))
cyl("S1_Drain", 0.025, 0.3, (BAX, 1.6 - 0.2, 0.68), M_STEEL, C1)
cyl("S1_DrainBend", 0.025, 0.22, (BAX, 1.6 - 0.1, 0.53), M_STEEL, C1, rot=(R_(90), 0, 0))
# steel bunk on the left wall: frame, mattress, blanket, pillow at the FRONT end (the guard sees the dummy head)
BX = -0.78
box("S1_BunkFrame", (0.78, 1.95, 0.05), (BX, -0.45, 0.42), M_STEEL, C1, bevel=0.005)
for y in (-1.38, 0.48):
    box("S1_BunkLeg%.0f" % (y * 10), (0.04, 0.04, 0.42), (BX + 0.35, y, 0.21), M_STEEL, C1)
box("S1_BunkChainA", (0.01, 0.01, 0.7), (-1.18, -1.3, 0.8), M_STEEL, C1)
box("S1_Mattress", (0.74, 1.9, 0.11), (BX, -0.45, 0.50), M_MATT, C1, bevel=0.035)
# blanket: subdivided plane draped over the "body" (rolled clothes) and the mattress
bpy.ops.mesh.primitive_plane_add(size=1); bl = bpy.context.active_object; bl.name = "S1_Blanket"
bl.scale = (0.9, 1.96, 1); bpy.ops.object.transform_apply(scale=True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.subdivide(number_cuts=70); bpy.ops.object.mode_set(mode='OBJECT')
for v in bl.data.vertices:
    x, y = v.co.x, v.co.y
    body = 0.11 * math.exp(-((x + 0.02) / 0.2) ** 2) * (1 if -0.75 < y < 0.75 else math.exp(-((abs(y) - 0.75) / 0.1) ** 2))
    edge = max(0.0, abs(x) - 0.37); drop = -min(0.36, edge * 3.5)
    roll = 0.17 * math.exp(-((y + 0.91) / 0.06) ** 2) * max(0.0, 1 - (abs(x) / 0.42) ** 4)
    v.co.z = body + drop + roll + 0.004 * math.sin(14 * y + 3 * x)
bl.location = (BX, -0.04, 0.565); bl.data.materials.append(M_BLANKET)
bl.modifiers.new("Sol", 'SOLIDIFY').thickness = 0.012; bl.modifiers.new("Sub", 'SUBSURF').levels = 1
for p in bl.data.polygons: p.use_smooth = True
link(bl, C1)
bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1); pil = bpy.context.active_object; pil.name = "S1_Pillow"
pil.scale = (0.3, 0.2, 0.065); pil.location = (BX, -1.18, 0.6); pil.data.materials.append(M_PILLOW)
for p in pil.data.polygons: p.use_smooth = True
link(pil, C1)
# shelf with folded clothes, cup, books on the right wall
box("S1_Shelf", (0.28, 1.0, 0.03), (1.06, 0.4, 1.55), M_STEEL, C1, bevel=0.004)
box("S1_Folded", (0.24, 0.3, 0.08), (1.06, 0.7, 1.605), flat("M_Folded", (0.85, 0.85, 0.82), 0.8), C1, bevel=0.01)
cyl("S1_Cup", 0.04, 0.09, (1.06, 0.3, 1.61), flat("M_Tin", (0.6, 0.62, 0.6), 0.35, 0.8), C1)
for i, c_ in enumerate(((0.55, 0.15, 0.12), (0.15, 0.25, 0.5), (0.3, 0.45, 0.25))):
    box("S1_Book%d" % i, (0.16, 0.035, 0.22), (1.08, 0.0 + i * 0.04, 1.68), flat("M_Book%d" % i, c_, 0.6), C1, bevel=0.003)
box("S1_Table", (0.5, 0.35, 0.03), (1.0, -0.5, 0.75), M_STEEL, C1, bevel=0.004)
box("S1_TableLeg", (0.03, 0.03, 0.75), (0.8, -0.38, 0.375), M_STEEL, C1)
# wooden stool in the cell (P1 sits on it in shots 1a/1b)
M_STOOL = flat("M_Stool", (0.42, 0.28, 0.16), 0.55)
cyl("S1_StoolSeat", 0.17, 0.035, (0.15, 0.5, 0.435), M_STOOL, C1, verts=32)
for k in range(3):
    ang = R_(90 + k * 120); lg = cyl("S1_StoolLeg%d" % k, 0.017, 0.44, (0.15 + math.cos(ang) * 0.11, 0.5 + math.sin(ang) * 0.11, 0.21), M_STOOL, C1, verts=10)
    lg.rotation_euler = (math.sin(ang) * R_(-8), math.cos(ang) * R_(8), 0)
# bars at the front (y = -1.6) with a door section; corridor beyond and the opposite cell row
for i in range(21):
    x = -1.2 + i * 0.12
    cyl("S1_Bar%02d" % i, 0.013, H, (x, -1.62, H / 2), M_BARS, C1, verts=12)
for z in (0.1, 1.05, 2.0, 2.55):
    box("S1_BarStrap%.0f" % (z * 100), (2.5, 0.03, 0.05), (0, -1.62, z), M_BARS, C1)
box("S1_CorrCeil", (8, 2.4, 0.2), (0, -2.8, H + 0.6), M_WALL, C1)
box("S1_OppWall", (8, 0.2, H + 0.6), (0, -4.2, (H + 0.6) / 2), M_WALL, C1)
for i in range(40):
    x = -3.6 + i * 0.18
    cyl("S1_OppBar%02d" % i, 0.013, H, (x, -4.05, H / 2), M_BARS, C1, verts=8)
# rubble at the vent (grows during the digging shots via its own scale keys)
rub = []
for i in range(70):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1)
    r = bpy.context.active_object; r.name = "S1_Rub%02d" % i
    for v in r.data.vertices: v.co *= 0.7 + 0.6 * random.random()
    s = 0.005 + 0.014 * random.random() ** 1.8
    ang = random.uniform(R_(200), R_(340)); rad = 0.05 + 0.4 * random.random() ** 1.3
    r.location = (VX + math.cos(ang) * rad * 1.3, 1.6 - 0.04 + math.sin(ang) * rad * 0.7, s * 0.6)
    r.scale = (s, s * random.uniform(0.7, 1.3), s * 0.7); r.rotation_euler = (random.random() * 6, random.random() * 6, random.random() * 6)
    r.data.materials.append(M_RUBBLE); link(r, C1); rub.append(r)
bpy.ops.object.select_all(action='DESELECT')
for r in rub: r.select_set(True)
bpy.context.view_layer.objects.active = rub[0]; bpy.ops.object.join(); RUB = bpy.context.active_object; RUB.name = "S1_Rubble"
bpy.ops.object.origin_set(type='ORIGIN_CURSOR'); RUB.location = (0, 0, 0)
# light fixture (caged hanging light) + lights: warm lamp, cool moonlight from the corridor, soft fill
lamp = append_model("caged_hanging_light", C1, (0, 0.6, H - 0.22), scale=0.28)
point("S1_LampBulb", (0, 0.6, H - 0.12), 35, (1.0, 0.78, 0.52), C1, r=0.06)
area("S1_Moon", (0.3, -3.3, 2.9), (R_(-55), 0, R_(10)), 2.5, 260, (0.55, 0.68, 1.0), C1)
area("S1_Fill", (-0.2, -1.0, 2.4), (R_(-15), 0, 0), 1.5, 70, (0.9, 0.92, 1.0), C1)
area("S1_CorrLight", (0, -2.8, H + 0.45), (0, 0, 0), 1.2, 120, (1.0, 0.85, 0.65), C1)

# ---------------------------------------------------------------- props in S1: spoons, drill, dummy head
def make_spoon(name):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=1.0)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > 0.25], context='VERTS')
    for v in bm.verts: v.co = V((v.co.x * 0.021, v.co.y * 0.032 + 0.165, v.co.z * 0.009))
    # handle: tapered strip from y=0 to y=0.14
    prev = None
    for i in range(12):
        y = i * 0.135 / 11; wv = 0.0085 - 0.0035 * math.sin(math.pi * i / 11) + (0.004 if i < 2 else 0)
        rv = [bm.verts.new((-wv, y, 0.004 + 0.003 * math.sin(math.pi * i / 11))), bm.verts.new((wv, y, 0.004 + 0.003 * math.sin(math.pi * i / 11)))]
        if prev: bm.faces.new((prev[0], prev[1], rv[1], rv[0]))
        prev = rv
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    o.modifiers.new("Sol", 'SOLIDIFY').thickness = 0.0022; o.modifiers.new("Sub", 'SUBSURF').levels = 1
    for p in me.polygons: p.use_smooth = True
    me.materials.append(M_SPOON); return o
SP = {n: link(make_spoon("Spoon_" + n), "Props") for n in ("P1", "P2", "P3")}
for i, o in enumerate(SP.values()): o.location = (5 + i * 0.3, 5, 0)         # parked; 03 attaches them to hands
# home-made drill: motor housing with cooling fins, end caps, fan cage, shaft and a spoon-bit, red cord
def make_drill():
    parts = []
    parts.append(cyl("Drill_Body", 0.045, 0.11, (0, 0, 0), M_MOTOR, "Props", rot=(0, R_(90), 0), verts=32))
    for i in range(9):
        parts.append(cyl("Drill_Fin%d" % i, 0.049, 0.004, (-0.045 + i * 0.011, 0, 0), M_MOTOR, "Props", rot=(0, R_(90), 0), verts=32))
    parts.append(cyl("Drill_CapA", 0.042, 0.02, (0.064, 0, 0), M_MOTOR_CAP, "Props", rot=(0, R_(90), 0), verts=32))
    parts.append(cyl("Drill_CapB", 0.042, 0.02, (-0.064, 0, 0), M_MOTOR_CAP, "Props", rot=(0, R_(90), 0), verts=32))
    parts.append(cyl("Drill_Shaft", 0.005, 0.12, (0.13, 0, 0), M_STEEL, "Props", rot=(0, R_(90), 0), verts=12))
    parts.append(cyl("Drill_Coil", 0.018, 0.012, (-0.08, 0, 0), M_COPPER, "Props", rot=(0, R_(90), 0), verts=16))
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts: p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.join(); d = bpy.context.active_object; d.name = "Drill"
    bit = make_spoon("Drill_Bit"); link(bit, "Props"); bit.parent = d; bit.location = (0.19, 0, 0); bit.rotation_euler = (0, 0, R_(-90))
    bit.scale = (0.6, 0.6, 0.6)
    fan = cyl("Drill_Fan", 0.036, 0.004, (-0.076, 0, 0), M_STEEL, "Props", rot=(0, R_(90), 0), verts=6); fan.parent = d
    # cord: a bezier from the motor's back cap to the floor and off
    cu = bpy.data.curves.new("Drill_Cord", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.004; cu.bevel_resolution = 3
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(3)
    for bp, p in zip(sp.bezier_points, ((-0.08, 0, -0.02), (-0.2, 0.05, -0.25), (-0.5, 0.1, -0.33), (-1.2, 0.3, -0.33))):
        bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    cord = bpy.data.objects.new("Drill_Cord", cu); sc.collection.objects.link(cord); link(cord, "Props"); cu.materials.append(M_RED)
    cord.parent = d
    return d, fan, cord
DRILL, FAN, CORD = make_drill(); DRILL.location = (6, 5, 0)

# dummy head: a painted plaster head built from P2's own head (rest pose, hair tuft = P2's hidden hair), eyes painted shut
def make_dummy():
    src = bpy.data.objects["P2"]
    dg = bpy.context.evaluated_depsgraph_get(); parts = []
    for k in src.children:
        if k.type != 'MESH': continue
        if not (k.name.endswith(".body") or k.name.endswith(".high-poly") or "short0" in k.name or k.name.endswith("eyebrow001")): continue
        hr, hv = k.hide_render, k.hide_viewport; k.hide_viewport = False
        arm = [m for m in k.modifiers if m.type == 'ARMATURE']
        for m in arm: m.show_viewport = False
        for m in k.modifiers:
            if m.type == 'SUBSURF': m.show_viewport = False
        bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(k.evaluated_get(dg), depsgraph=dg)
        for m in arm: m.show_viewport = True
        for m in k.modifiers:
            if m.type == 'SUBSURF': m.show_viewport = True
        k.hide_viewport = hv
        o = bpy.data.objects.new("Dummy_" + k.name, me); sc.collection.objects.link(o); o.matrix_world = k.matrix_world
        o["src"] = k.name; parts.append(o)
    body = next(o for o in parts if o["src"].endswith(".body"))
    neck_z = src.data.bones["neck02"].head_local.z
    bm = bmesh.new(); bm.from_mesh(body.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < neck_z - 0.01], context='VERTS'); bm.to_mesh(body.data); bm.free()
    mp = bpy.data.materials.new("M_DummyPaint"); mp.use_nodes = True; P = mp.node_tree.nodes["Principled BSDF"]
    P.inputs['Base Color'].default_value = (0.74, 0.5, 0.37, 1); P.inputs['Roughness'].default_value = 0.7
    me_ = bpy.data.materials.new("M_DummyEyes"); me_.use_nodes = True; nt = me_.node_tree; Pe = nt.nodes["Principled BSDF"]
    Pe.inputs['Roughness'].default_value = 0.7
    # painted shut: skin-paint eyeball with a thin dark lash line across the middle (object Z of the eye mesh)
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); mr = nt.nodes.new('ShaderNodeMapRange')
    sub = nt.nodes.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'; ab = nt.nodes.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'
    eye_z = (src.data.bones["eye.L"].head_local.z + src.data.bones["eye.R"].head_local.z) / 2
    sub.inputs[1].default_value = eye_z - 0.002
    mr.inputs['From Min'].default_value = 0.0015; mr.inputs['From Max'].default_value = 0.003
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (0.1, 0.06, 0.05, 1); mx.inputs['B'].default_value = (0.7, 0.46, 0.34, 1)
    nt.links.new(tc.outputs['Object'], sep.inputs[0]); nt.links.new(sep.outputs['Z'], sub.inputs[0]); nt.links.new(sub.outputs[0], ab.inputs[0])
    nt.links.new(ab.outputs[0], mr.inputs['Value']); nt.links.new(mr.outputs[0], mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], Pe.inputs['Base Color'])
    for o in parts:
        if o is body: o.data.materials.clear(); o.data.materials.append(mp)
        elif o["src"].endswith(".high-poly"): o.data.materials.clear(); o.data.materials.append(me_)
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active = body; bpy.ops.object.join(); d = bpy.context.active_object; d.name = "DummyHead"
    hz = src.data.bones["head"].head_local
    bpy.context.scene.cursor.location = hz; bpy.ops.object.origin_set(type='ORIGIN_CURSOR'); bpy.context.scene.cursor.location = (0, 0, 0)
    d.modifiers.new("Sub", 'SUBSURF').levels = 1
    for p in d.data.polygons: p.use_smooth = True
    return link(d, C1)
DUMMY = make_dummy()
# lying on its back on the pillow: face up (rest face looks -Y -> +90 deg about X), crown toward the bars (-Y), turned 25 deg to the room (+X)
# built from directions: crown C toward the bars, tipped 20 deg up (the neck dips into the bed); face F up, turned 25 deg to the room
Cd = V((0, -math.cos(R_(20)), math.sin(R_(20)))); F0 = V((math.sin(R_(25)), 0, math.cos(R_(25))))
Fd = (F0 - Cd * F0.dot(Cd)).normalized(); Yd = -Fd; Zd = Cd; Xd = Yd.cross(Zd)
DUMMY.rotation_mode = 'XYZ'; DUMMY.rotation_euler = Matrix((Xd, Yd, Zd)).transposed().to_euler()
DUMMY.location = V((BX, -1.17, 0.76)) - Cd * 0.08
# rolled blanket edge across the neck (hides the prop's neck cut)
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.095, depth=0.62, location=(BX, -1.02, 0.685), rotation=(0, R_(90), 0))
rl = bpy.context.active_object; rl.name = "S1_BlanketRoll"; rl.data.materials.append(M_BLANKET)
rl.scale = (1.0, 1.0, 1.0); rl.modifiers.new("Bev", 'BEVEL').width = 0.03; rl.modifiers.new("Sub", 'SUBSURF').levels = 2
for p_ in rl.data.polygons: p_.use_smooth = True
link(rl, C1)

# guard flashlight (Poly Haven), parked
FL = append_model("vintage_flashlight", "Props", (7, 5, 0))[0]; FL.name = "Flashlight"
bpy.context.view_layer.objects.active = FL; bpy.ops.object.select_all(action='DESELECT'); FL.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
spot = bpy.data.lights.new("FlashBeam", 'SPOT'); spot.energy = 0; spot.spot_size = R_(28); spot.spot_blend = 0.5; spot.color = (1.0, 0.92, 0.75)
sp_o = bpy.data.objects.new("FlashBeam", spot); col("Props").objects.link(sp_o); sp_o.parent = FL

# ================================================================== S2 SERVICE CORRIDOR (x = 30): the vent from behind
C2 = "S2_Corridor"; X2 = 30.0
box("S2_Floor", (8, 3.0, 0.2), (X2, 1.5, 0.1), M_FLOOR, C2)      # stops at the vent wall (nothing under the duct)
S2_FZ = 0.2
box("S2_Ceil", (8, 4, 0.2), (X2, 1.0, 3.1), M_CONC, C2)
w2 = box("S2_WallVent", (8, 0.25, 3.0), (X2, -0.125, 1.5), M_WALL, C2)
box("S2_WallFar", (8, 0.25, 3.0), (X2, 2.35, 1.5), M_CONC, C2)
box("S2_EndWall", (0.25, 3.0, 3.0), (X2 - 3.8, 1.0, 1.5), M_CONC, C2)
cut2 = cut.copy(); cut2.data = cut.data.copy(); col(C2).objects.link(cut2); cut2.location = (X2, 0.0, 0.56); cut2.scale = (2.7, 2.7, 1.0)       # dug out to crawl size on this side
b = w2.modifiers.new("Hole", 'BOOLEAN'); b.object = cut2; b.operation = 'DIFFERENCE'; b.solver = 'EXACT'
M_DUCT = paint("M_Duct", (0.3, 0.32, 0.3), var=0.1)
box("S2_DuctFloor", (0.9, 2.4, 0.05), (X2, -1.45, -0.01), M_DUCT, C2)
box("S2_DuctL", (0.05, 2.4, 0.8), (X2 - 0.45, -1.45, 0.6), M_DUCT, C2)
box("S2_DuctR", (0.05, 2.4, 0.8), (X2 + 0.45, -1.45, 0.6), M_DUCT, C2)
box("S2_DuctTop", (0.9, 2.4, 0.05), (X2, -1.45, 1.0), M_DUCT, C2)
box("S2_DuctEnd", (0.9, 0.05, 0.8), (X2, -2.65, 0.6), M_DARK, C2)
G2 = make_grille("S2_Grille", C2, (X2, 0.012, 0.58), (0, 0, R_(180)))
G2.scale = (2.0, 1.0, 2.6)        # the corridor-side vent cover is the bigger duct grille
# pipe runs along both walls (+ Poly Haven fittings), conduits, a valve wheel
for i, (y, z, r) in enumerate(((0.14, 2.55, 0.06), (0.14, 2.3, 0.04), (2.1, 2.6, 0.08), (2.12, 1.1, 0.05), (2.12, 0.6, 0.035))):
    cyl("S2_Pipe%d" % i, r, 8, (X2, y, z), M_STEEL if i % 2 else flat("M_PipeGrey%d" % i, (0.45, 0.5, 0.55), 0.45, 0.6), C2, rot=(0, R_(90), 0), verts=20)
    for k in range(5):
        cyl("S2_Flange%d_%d" % (i, k), r * 1.35, 0.03, (X2 - 3.2 + k * 1.6, y, z), M_STEEL, C2, rot=(0, R_(90), 0), verts=20)
for k in range(6):
    cyl("S2_Vert%d" % k, 0.035, 3.0, (X2 - 3 + k * 1.3, 2.13, 1.5), M_STEEL, C2, verts=16)
fit = append_model("modular_industrial_pipes_01", C2, (X2 + 1.6, 2.0, 1.6), rot=(0, 0, R_(180)), scale=1.0, names=["modular_industrial_pipes_01_pipe08"])
cr = append_model("wooden_crate_01", C2, (X2 - 0.55, 1.58, 0.2), rot=(0, 0, R_(90)), scale=1.25, names=["wooden_crate_01", "wooden_crate_01_lid", "wooden_crate_01_latch"])
cr2 = append_model("wooden_crate_01", C2, (X2 - 0.6, 1.6, 0.6), rot=(0, 0, R_(93)), scale=1.25, names=["wooden_crate_01", "wooden_crate_01_lid", "wooden_crate_01_latch"])
CRATE = next(o for o in cr if o.name.startswith("wooden_crate_01") and "lid" not in o.name and "latch" not in o.name)
# DA KRAS FILMS logo: decal on the crate's long side facing the corridor (-y), dark version (light wood)
def logo_decal(name, img, parent, loc, rot, width, cname):
    im = bpy.data.images.load(os.path.join(BRAND, img), check_existing=True)
    m = bpy.data.materials.new("M_" + name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = im; t.interpolation = 'Cubic'
    nt.links.new(t.outputs['Color'], P.inputs['Base Color']); nt.links.new(t.outputs['Alpha'], P.inputs['Alpha']); P.inputs['Roughness'].default_value = 0.7
    bpy.ops.mesh.primitive_plane_add(size=1); o = bpy.context.active_object; o.name = name
    o.scale = (width, width * im.size[1] / im.size[0], 1); bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m); o.location = loc; o.rotation_euler = rot
    bpy.context.view_layer.update()
    if parent: Mw = o.matrix_world.copy(); o.parent = parent; o.matrix_world = Mw
    return link(o, cname)
bpy.context.view_layer.update()
cb = CRATE.matrix_world.translation; dims = CRATE.dimensions * 1.25
LOGO = logo_decal("Logo_Crate", "DaKrasFilms_logo_dark.png", CRATE, (cb.x + dims.y / 2 + 0.004, cb.y, cb.z + dims.z * 0.5),
                  (R_(90), 0, R_(90)), min(0.62, dims.x * 0.8), C2)      # long side faces +x (down the corridor)
lamp2 = append_model("caged_hanging_light", C2, (X2 + 0.3, 1.0, 2.75), scale=0.35)
point("S2_Bulb", (X2 + 0.3, 1.0, 2.68), 45, (1.0, 0.8, 0.55), C2)
point("S2_Bulb2", (X2 - 2.6, 1.0, 2.68), 30, (1.0, 0.8, 0.55), C2)
area("S2_CrateLight", (X2 - 1.6, 1.2, 2.2), (R_(60), 0, R_(90)), 1.2, 90, (1.0, 0.9, 0.75), C2)
area("S2_Fill", (X2, 2.2, 1.6), (R_(90), 0, R_(180)), 2.0, 60, (0.75, 0.85, 1.0), C2)
area("S2_Key", (X2 + 1.5, 1.6, 2.6), (R_(40), 0, R_(130)), 1.5, 120, (0.85, 0.9, 1.0), C2)
# dust motes: a few small, slow particles (keyed empties instancing tiny spheres would be heavy; use a sparse static cloud)
M_MOTE = flat("M_Mote", (0.9, 0.88, 0.8), 0.9, emit=(0.6, 0.58, 0.5), estr=0.4)
for i in range(30):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.0025, location=(X2 + random.uniform(-1.2, 1.2), random.uniform(0.2, 1.8), random.uniform(0.2, 1.9)))
    o = bpy.context.active_object; o.name = "S2_Mote%02d" % i; o.data.materials.append(M_MOTE); link(o, C2)

# ================================================================== S3 LADDER SHAFT (x = 60) and S3b OUTSIDE WALL (x = 90)
C3 = "S3_Shaft"; X3 = 60.0; HS = 7.0
box("S3_Floor", (4, 4, 0.2), (X3, -1.0, -0.1), M_FLOOR, C3)
box("S3_Back", (3.4, 0.3, HS), (X3, 0.15, HS / 2), M_BRICK_GREY, C3)
box("S3_SideL", (0.3, 3.4, HS), (X3 - 1.55, -1.4, HS / 2), M_BRICK_GREY, C3)
box("S3_SideR", (0.3, 3.4, HS), (X3 + 1.55, -1.4, HS / 2), M_BRICK_GREY, C3)
box("S3_Roof_a", (3.4, 1.6, 0.25), (X3, -2.3, HS + 0.12), M_CONC, C3)
box("S3_Roof_b", (1.0, 1.3, 0.25), (X3 - 1.2, -0.85, HS + 0.12), M_CONC, C3)
box("S3_Roof_c", (1.0, 1.3, 0.25), (X3 + 1.2, -0.85, HS + 0.12), M_CONC, C3)
# fixed steel ladder: rails + rungs every 0.30 m, 0.18 m off the wall
LAD_X, LAD_Y, RUNG = X3, -0.18, 0.30
for sx in (-0.23, 0.23):
    cyl("S3_Rail%+.0f" % (sx * 10), 0.02, HS + 0.9, (LAD_X + sx, LAD_Y, (HS + 0.9) / 2), M_STEEL, C3, verts=16)      # round rails: hands slide up them
    for z in (1.0, 3.0, 5.0, 6.6):
        box("S3_Bracket%+.0f_%d" % (sx * 10, z * 10), (0.04, 0.2, 0.04), (LAD_X + sx, LAD_Y + 0.1, z), M_STEEL, C3)
for k in range(int(HS / RUNG) + 2):
    cyl("S3_Rung%02d" % k, 0.014, 0.46, (LAD_X, LAD_Y, 0.30 + k * RUNG), M_STEEL, C3, rot=(0, R_(90), 0), verts=12)
for k in range(4):
    cyl("S3_ShaftPipe%d" % k, 0.04 + 0.01 * k, HS, (X3 - 1.2 + k * 0.18 + (1.9 if k > 1 else 0), -0.06, HS / 2), M_STEEL, C3, verts=16)
# steep open-tread steel stair up the shaft (6a): 12 treads, rise 0.2, run 0.25, from y -3.2 to -0.2, centred at x X3-0.7
ST_X, ST_Y0, ST_RISE, ST_RUN = X3 - 0.7, -3.5, 0.2, 0.29
for k in range(1, 13):
    box("S3_Tread%02d" % k, (0.8, ST_RUN - 0.01, 0.04), (ST_X, ST_Y0 + (k - 0.5) * ST_RUN, k * ST_RISE - 0.02), M_STEEL, C3, bevel=0.004)
L_ = math.hypot(12 * ST_RUN, 12 * ST_RISE); ang_ = math.atan2(12 * ST_RISE, 12 * ST_RUN)
for sx_ in (-0.42, 0.42):
    st_ = box("S3_Stringer%+.0f" % (sx_ * 10), (0.03, L_, 0.22), (ST_X + sx_, ST_Y0 + 6 * ST_RUN, 6 * ST_RISE - 0.1), M_STEEL, C3)
    st_.rotation_euler = (ang_, 0, 0)
area("S3_Sky", (X3, -0.85, HS + 0.6), (0, 0, 0), 1.0, 300, (0.6, 0.72, 1.0), C3)
area("S3_Key", (X3 + 0.9, -2.6, 2.5), (R_(70), 0, R_(25)), 1.5, 160, (0.95, 0.85, 0.7), C3)
area("S3_Fill", (X3 - 1.0, -2.8, 4.5), (R_(75), 0, R_(-20)), 2.0, 120, (0.6, 0.7, 1.0), C3)
point("S3_CageLamp", (X3 + 1.1, -0.3, 3.2), 25, (1.0, 0.8, 0.55), C3)

C3B = "S3b_Outside"; X4 = 90.0; HB = 9.0
box("S3b_Ground", (40, 30, 0.2), (X4, -10, -0.1), tex_mat("M_Yard", "concrete_floor_02", tint=(0.6, 0.62, 0.62), scale=0.3, bump=0.3), C3B)
box("S3b_Facade", (16, 0.4, HB), (X4, 0.2, HB / 2), M_BRICK, C3B)
box("S3b_Parapet", (16, 0.5, 0.25), (X4, 0.15, HB + 0.12), M_CONC, C3B)
for i in range(6):
    for row in (2.2, 5.2):
        wx = X4 - 6.5 + i * 2.6 + (0 if i < 3 else 1.3)
        if abs(wx - X4) < 1.0: continue
        box("S3b_Win%d_%d" % (i, row), (0.9, 0.05, 1.3), (wx, -0.01, row + 0.6), flat("M_WinGlow%d%d" % (i, row), (0.2, 0.18, 0.12), 0.4,
            emit=(1.0, 0.55, 0.2), estr=3.0 if (i + int(row)) % 2 else 0.8), C3B)
        for b_ in range(4):
            cyl("S3b_WinBar%d_%d_%d" % (i, row, b_), 0.01, 1.3, (wx - 0.33 + b_ * 0.22, -0.05, row + 0.6), M_BARS, C3B, verts=8)
PIPE_X, PIPE_Y, PIPE_R = X4, -0.30, 0.065
cyl("S3b_VentPipe", PIPE_R, HB + 1.2, (PIPE_X, PIPE_Y, (HB + 1.2) / 2), flat("M_VentPipe", (0.25, 0.4, 0.6), 0.4, 0.6), C3B, verts=24)
cyl("S3b_PipeCap", PIPE_R * 1.8, 0.12, (PIPE_X, PIPE_Y, HB + 1.25), M_STEEL, C3B, verts=24)
for z in (1.2, 3.6, 6.0, 8.4):
    box("S3b_PipeClamp%d" % z, (0.04, 0.3, 0.04), (PIPE_X, -0.15, z), M_STEEL, C3B)
lw = append_model("industrial_wall_lamp", C3B, (X4 + 1.6, -0.05, 4.2), rot=(0, 0, R_(180)), scale=1.4)
point("S3b_WallLampBulb", (X4 + 1.6, -0.3, 4.0), 120, (1.0, 0.75, 0.45), C3B)
area("S3b_Moon", (X4 - 5, -10, 12), (R_(50), 0, R_(-30)), 6, 1800, (0.55, 0.65, 1.0), C3B)
area("S3b_Fill", (X4 + 3, -7, 3), (R_(75), 0, R_(25)), 3, 300, (0.7, 0.78, 1.0), C3B)
for i in range(8):                                # a low fence and a few shrubs at the yard edge (silhouettes)
    cyl("S3b_Post%d" % i, 0.04, 2.2, (X4 - 7 + i * 2, -9, 1.1), M_STEEL, C3B, verts=8)
box("S3b_FenceRail", (16, 0.04, 0.04), (X4, -9, 2.1), M_STEEL, C3B)

# ================================================================== S4 THE BAY (x = 300)
C4 = "S4_Bay"; X5 = 300.0
bpy.ops.mesh.primitive_plane_add(size=1, location=(X5, 40, 0)); wat = bpy.context.active_object; wat.name = "S4_Water"
oc = wat.modifiers.new("Ocean", 'OCEAN'); oc.geometry_mode = 'GENERATE'; oc.size = 1.0; oc.spatial_size = 60; oc.repeat_x = 4; oc.repeat_y = 5
oc.resolution = 10; oc.wave_scale = 0.35; oc.choppiness = 0.6; oc.wind_velocity = 6; oc.wave_alignment = 0.3
oc.time = 1.0
mw = bpy.data.materials.new("M_Water"); mw.use_nodes = True; P = mw.node_tree.nodes["Principled BSDF"]
P.inputs['Base Color'].default_value = (0.02, 0.12, 0.22, 1); P.inputs['Roughness'].default_value = 0.3
P.inputs['Specular IOR Level'].default_value = 0.05      # low specular: no bright sky sheet at grazing angles (LESSONS s8)
P.inputs['Coat Weight'].default_value = 0.0
wat.data.materials.append(mw); link(wat, C4)
for p in wat.data.polygons: p.use_smooth = True
wat.location = (X5 - 120, -120, 0)
# raincoat raft: rounded-rectangle tube (bevelled curve) + floor + side rope, rubberised patchwork
def rr_curve(name, w, l, r_corner, z, bevel):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = bevel; cu.bevel_resolution = 6
    sp = cu.splines.new('POLY'); pts = []
    for cx, cy, a0 in ((w / 2 - r_corner, l / 2 - r_corner, 0), (-w / 2 + r_corner, l / 2 - r_corner, 90),
                       (-w / 2 + r_corner, -l / 2 + r_corner, 180), (w / 2 - r_corner, -l / 2 + r_corner, 270)):
        for k in range(9):
            t = R_(a0 + k * 90 / 8); pts.append((cx + math.cos(t) * r_corner, cy + math.sin(t) * r_corner, z))
    sp.points.add(len(pts) - 1)
    for p, c_ in zip(sp.points, pts): p.co = (*c_, 1)
    sp.use_cyclic_u = True
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o); return o
M_RAFT = bpy.data.materials.new("M_RaincoatRaft"); M_RAFT.use_nodes = True; nt = M_RAFT.node_tree; P = nt.nodes["Principled BSDF"]
vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 3.0
vo2 = nt.nodes.new('ShaderNodeTexVoronoi'); vo2.feature = 'DISTANCE_TO_EDGE'; vo2.inputs['Scale'].default_value = 3.0
cr_ = nt.nodes.new('ShaderNodeValToRGB'); cr_.color_ramp.interpolation = 'CONSTANT'
els = cr_.color_ramp.elements; els[0].color = (0.24, 0.27, 0.2, 1); els[1].position = 0.35; els[1].color = (0.32, 0.30, 0.18, 1)
e3 = els.new(0.7); e3.color = (0.12, 0.14, 0.13, 1)
seam = nt.nodes.new('ShaderNodeMapRange'); seam.inputs['From Min'].default_value = 0.0; seam.inputs['From Max'].default_value = 0.03
mxs = nt.nodes.new('ShaderNodeMix'); mxs.data_type = 'RGBA'; mxs.inputs['A'].default_value = (0.04, 0.04, 0.035, 1)
tc = nt.nodes.new('ShaderNodeTexCoord')
nt.links.new(tc.outputs['Object'], vo.inputs['Vector']); nt.links.new(tc.outputs['Object'], vo2.inputs['Vector'])
nt.links.new(vo.outputs['Color'], cr_.inputs['Fac']); nt.links.new(vo2.outputs['Distance'], seam.inputs['Value'])
nt.links.new(seam.outputs[0], mxs.inputs['Factor']); nt.links.new(cr_.outputs['Color'], mxs.inputs['B']); nt.links.new(mxs.outputs['Result'], P.inputs['Base Color'])
P.inputs['Roughness'].default_value = 0.45; P.inputs['Coat Weight'].default_value = 0.3
RAFT = bpy.data.objects.new("Raft", None); col(C4).objects.link(RAFT); RAFT.location = (X5, 0, 0)
RW, RL = 1.35, 2.55
tube = rr_curve("Raft_Tube", RW, RL, 0.45, 0.17, 0.17); tube.data.materials.append(M_RAFT); link(tube, C4); tube.parent = RAFT
floor_ = box("Raft_Floor", (RW - 0.12, RL - 0.12, 0.03), (0, 0, 0.03), M_RAFT, C4, bevel=0.012); floor_.parent = RAFT
rope = rr_curve("Raft_Rope", RW + 0.36, RL + 0.36, 0.62, 0.2, 0.008); link(rope, C4); rope.parent = RAFT
rope.data.materials.append(flat("M_Rope", (0.72, 0.62, 0.42), 0.8))
for k in range(12):
    t = k / 12.0; ang = t * 2 * math.pi
    x_ = math.cos(ang) * (RW / 2 + 0.17); y_ = math.sin(ang) * (RL / 2 + 0.17)
    x_ = max(-RW / 2 - 0.17, min(RW / 2 + 0.17, x_ * 1.25)); y_ = max(-RL / 2 - 0.17, min(RL / 2 + 0.17, y_ * 1.25))
    box("Raft_Loop%d" % k, (0.03, 0.03, 0.05), (x_, y_, 0.27), flat("M_Loop", (0.1, 0.1, 0.1), 0.6), C4).parent = RAFT
PADDLE = box("Paddle", (0.12, 0.55, 0.018), (0, 0, 0), M_WOODB, "Props", bevel=0.006); PADDLE.location = (8, 5, 0)
# Alcatraz-like rocky island behind (generic: rock base, cell-house block, lit windows, a light tower) at y = -45
def island(name, loc, size, cname, seed):
    random.seed(seed)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1, location=loc); o = bpy.context.active_object; o.name = name
    o.scale = (size[0], size[1], size[2])
    tx = bpy.data.textures.new(name + "_n", 'CLOUDS'); tx.noise_scale = 0.35
    dm = o.modifiers.new("Rock", 'DISPLACE'); dm.texture = tx; dm.strength = 0.25
    o.data.materials.append(flat("M_" + name, (0.16, 0.17, 0.16), 0.8)); link(o, cname)
    for p in o.data.polygons: p.use_smooth = True
    return o
island("S4_Island", (X5 + 4, -48, -2), (26, 12, 7), C4, 3)
box("S4_CellHouse", (18, 6, 4), (X5 + 4, -48, 6.5), flat("M_CellHouse", (0.55, 0.55, 0.5), 0.7), C4)
for i in range(14):
    box("S4_HouseWin%d" % i, (0.5, 0.05, 0.9), (X5 - 4.5 + i * 1.25, -44.97, 6.6 + (i % 2) * 1.4), flat("M_HouseWin%d" % i, (0.2, 0.2, 0.1), 0.5, emit=(1.0, 0.8, 0.45), estr=4.0 if i % 3 else 1.0), C4)
cyl("S4_Tower", 0.9, 9, (X5 - 6, -47, 9), flat("M_Tower", (0.75, 0.75, 0.7), 0.6), C4, verts=16)
cyl("S4_TowerLamp", 1.0, 1.0, (X5 - 6, -47, 14), flat("M_TowerLamp", (1, 0.95, 0.8), 0.3, emit=(1.0, 0.9, 0.7), estr=12), C4, verts=16)
# searchlight beam (stylised, emissive cone, transparent toward the tip) on the tower: swept in 8a
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=2.4, radius2=0.45, depth=60, location=(0, 0, -30))
beam = bpy.context.active_object; beam.name = "S4_Beam"; bpy.ops.object.transform_apply(location=True)
mb = bpy.data.materials.new("M_Beam"); mb.use_nodes = True; nt = mb.node_tree; nt.nodes.clear()
o_ = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (1.0, 0.95, 0.8, 1); em.inputs['Strength'].default_value = 1.2
tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); add = nt.nodes.new('ShaderNodeAddShader')
gc = nt.nodes.new('ShaderNodeTexCoord'); sp_ = nt.nodes.new('ShaderNodeSeparateXYZ'); rmp = nt.nodes.new('ShaderNodeMapRange')
rmp.inputs['From Min'].default_value = 0.0; rmp.inputs['From Max'].default_value = 1.0; rmp.inputs['To Min'].default_value = 1.0; rmp.inputs['To Max'].default_value = 0.9
nt.links.new(gc.outputs['Generated'], sp_.inputs[0]); nt.links.new(sp_.outputs['Z'], rmp.inputs['Value'])
nt.links.new(rmp.outputs[0], mx.inputs['Fac']); nt.links.new(em.outputs[0], mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], o_.inputs['Surface'])
beam.data.materials.append(mb); link(beam, C4); beam.visible_shadow = False
BEAM_PIV = bpy.data.objects.new("S4_BeamPivot", None); col(C4).objects.link(BEAM_PIV); BEAM_PIV.location = (X5 - 6, -47, 14)
beam.parent = BEAM_PIV; beam.rotation_euler = (R_(90), 0, 0)
bl_ = bpy.data.lights.new("S4_SearchSpot", 'SPOT'); bl_.energy = 0; bl_.spot_size = R_(10); bl_.color = (1, 0.95, 0.8)
so = bpy.data.objects.new("S4_SearchSpot", bl_); col(C4).objects.link(so); so.parent = BEAM_PIV; so.rotation_euler = (R_(90), 0, 0)
# generic far suspension bridge ahead (y = +160): two towers, deck, main cables and hangers, warm deck lights
BR = "S4_Bridge"; BY = 170.0; BZ = 22.0
M_BRIDGE = flat("M_Bridge", (0.28, 0.2, 0.18), 0.6)
box("S4_Deck", (220, 4, 1.2), (X5 + 20, BY, BZ), M_BRIDGE, C4)
for tx_ in (-40.0, 60.0):
    for dy in (-1.8, 1.8):
        box("S4_Tower%.0f%.0f" % (tx_, dy), (2.2, 1.4, 75), (X5 + tx_, BY + dy, 37.5), M_BRIDGE, C4)
    for zz in (BZ + 6, 50, 72):
        box("S4_TowerBeam%.0f_%.0f" % (tx_, zz), (2.2, 5, 1.6), (X5 + tx_, BY, zz), M_BRIDGE, C4)
for dy in (-1.8, 1.8):
    cu = bpy.data.curves.new("S4_Cable%.0f" % dy, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.25
    sp = cu.splines.new('POLY'); xs = [-120 + i * 2.5 for i in range(97)]; sp.points.add(len(xs) - 1)
    for p, x in zip(sp.points, xs):
        if x < -40: z = 74 - (74 - BZ - 2) * ((-40 - x) / 80) ** 0.8
        elif x > 60: z = 74 - (74 - BZ - 2) * ((x - 60) / 60) ** 0.8
        else: u = (x - 10) / 50; z = BZ + 3 + (74 - BZ - 3) * u * u
        p.co = (X5 + x, BY + dy, z, 1)
    co = bpy.data.objects.new("S4_Cable%.0f" % dy, cu); sc.collection.objects.link(co); link(co, C4); cu.materials.append(M_BRIDGE)
for i in range(30):
    box("S4_DeckLight%d" % i, (0.6, 0.6, 0.6), (X5 - 90 + i * 7, BY - 2.3, BZ + 1.2), flat("M_DeckLight", (1, 0.8, 0.5), 0.4, emit=(1.0, 0.75, 0.4), estr=20), C4)
# far shoreline hills at the horizon (dark, low)
for i, (x, y, sx, sz) in enumerate(((-150, 260, 160, 18), (60, 300, 200, 26), (240, 250, 150, 15))):
    island("S4_Hills%d" % i, (X5 + x, y, -4), (sx, 25, sz), C4, 10 + i)
# bay lights: moonlight key + a cool fill, the raft gets its own soft rim
sunL = bpy.data.lights.new("S4_Moon", 'SUN'); sunL.energy = 0.9; sunL.color = (0.65, 0.75, 1.0); sunL.angle = R_(3)
sun = bpy.data.objects.new("S4_Moon", sunL); col(C4).objects.link(sun); sun.rotation_euler = (R_(62), 0, R_(150))
for _lo in (area("S4_RaftKey", (X5 + 2.5, -3.5, 3.0), (R_(55), 0, R_(35)), 3.0, 260, (0.8, 0.86, 1.0), C4), area("S4_RaftRim", (X5 - 2.0, 4.0, 2.5), (R_(-60), 0, R_(200)), 3.0, 180, (1.0, 0.8, 0.6), C4)):
    _lo.visible_glossy = False      # no blown-out hot spots on the water
# patrol boat (8a): plain hull + cabin + spotlight, no markings
def patrol_boat():
    bm = bmesh.new()
    prof = [(-0.0, 3.4, 0.9), (-0.9, 2.2, 0.9), (-1.2, 0.0, 0.9), (-1.15, -3.0, 0.9), (1.15, -3.0, 0.9), (1.2, 0.0, 0.9), (0.9, 2.2, 0.9)]
    top = [bm.verts.new(p) for p in prof]; bot = [bm.verts.new((x * 0.55, y * 0.95, -0.2)) for x, y, z in prof]
    bm.faces.new(top[::-1]); bm.faces.new(bot)
    for i in range(len(prof)):
        j = (i + 1) % len(prof); bm.faces.new((top[i], top[j], bot[j], bot[i]))
    me = bpy.data.meshes.new("S4_Boat"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("S4_Boat", me); sc.collection.objects.link(o); link(o, C4)
    o.data.materials.append(flat("M_BoatHull", (0.85, 0.86, 0.84), 0.45)); o.modifiers.new("Bev", 'BEVEL').width = 0.06
    cab = box("S4_BoatCabin", (1.6, 1.8, 1.0), (0, -0.4, 1.4), flat("M_BoatCabin", (0.75, 0.77, 0.78), 0.5), C4, bevel=0.05); cab.parent = o
    win = box("S4_BoatWin", (1.62, 0.6, 0.35), (0, 0.2, 1.55), flat("M_BoatWin", (0.05, 0.08, 0.1), 0.15), C4); win.parent = o
    lamp = cyl("S4_BoatLamp", 0.18, 0.3, (0, 0.4, 2.05), flat("M_BoatLamp", (1, 1, 0.9), 0.3, emit=(1, 0.95, 0.8), estr=30), C4, rot=(R_(90), 0, 0)); lamp.parent = o
    st = bpy.data.lights.new("S4_BoatSpot", 'SPOT'); st.energy = 0; st.spot_size = R_(18); st.color = (1, 0.95, 0.85)
    so_ = bpy.data.objects.new("S4_BoatSpot", st); col(C4).objects.link(so_); so_.parent = o; so_.location = (0, 0.6, 2.05); so_.rotation_euler = (R_(80), 0, 0)
    return o
BOAT = patrol_boat(); BOAT.location = (X5 - 20, -20, 0)

# ------------------------------------------------------------------ world: moonrise sky (seen only in S3b and S4)
w = bpy.data.worlds.new("W_Night"); sc.world = w; w.use_nodes = True; nt = w.node_tree
env = nt.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(os.path.join(AS, "hdri", "qwantani_moonrise_puresky_1k.hdr"))
bg = nt.nodes["Background"]; nt.links.new(env.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.22
mp_ = nt.nodes.new('ShaderNodeMapping'); tc_ = nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tc_.outputs['Generated'], mp_.inputs['Vector']); nt.links.new(mp_.outputs[0], env.inputs['Vector'])
mp_.inputs['Rotation'].default_value = (0, 0, R_(200))

# ------------------------------------------------------------------ render defaults (look per STYLE_ANIMATED)
r = sc.render; r.engine = 'CYCLES'; r.resolution_x, r.resolution_y = 1080, 1920; r.fps = 60
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except TypeError: sc.view_settings.look = 'Punchy'
r.use_motion_blur = False
sc["VX"], sc["VZ"], sc["BX"] = VX, VZ, BX
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SETS_OK", len(bpy.data.objects))
