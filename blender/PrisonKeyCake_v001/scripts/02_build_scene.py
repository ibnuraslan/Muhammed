"""PrisonKeyCake set: cell, corridor, yard, gate arch, foundry, government steps + props, lights, world.
blender -b work/humans.blend --python scripts/02_build_scene.py -- work/scene.blend
All set geometry is built in world coordinates (objects at identity) so Object texture coords == world metres."""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix

OUT = sys.argv[sys.argv.index("--") + 1]
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); AS = os.path.join(ROOT, "assets")
R_ = math.radians
def DIAG(x, y, z):
    return Matrix(((x, 0, 0, 0), (0, y, 0, 0), (0, 0, z, 0), (0, 0, 0, 1)))
sc = bpy.context.scene
random.seed(6)
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.fps, sc.render.fps_base = 60, 1.0
sc.frame_start, sc.frame_end = 1, 1890
sc.cycles.samples = 48; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.05
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.max_bounces = 8; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3
sc.cycles.transmission_bounces = 8; sc.cycles.transparent_max_bounces = 8; sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
sc.render.use_persistent_data = True
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'

COL = {}
def coll(name):
    if name not in COL:
        c = bpy.data.collections.new(name); sc.collection.children.link(c); COL[name] = c
    return COL[name]

# ------------------------------------------------------------------ materials
def load_mat(asset):
    p = os.path.join(AS, asset, asset + "_1k.blend")
    with bpy.data.libraries.load(p) as (s, d):
        d.materials = [m for m in s.materials]
    return [m for m in d.materials if m]

def world_mat(asset, scale=1.0, tint=None, rough_add=0.0, name=None):
    """Poly Haven texture material re-mapped to box-projected Object coords (scale = repeats per metre)."""
    m = load_mat(asset)[0]
    if name: m.name = name
    nt = m.node_tree; N, L = nt.nodes, nt.links
    tc = next(n for n in N if n.type == 'TEX_COORD'); mp = next(n for n in N if n.type == 'MAPPING')
    for l in list(mp.inputs['Vector'].links): L.remove(l)
    L.new(tc.outputs['Object'], mp.inputs['Vector'])
    mp.inputs['Scale'].default_value = (scale, scale, scale)
    for n in N:
        if n.type == 'TEX_IMAGE':
            n.projection = 'BOX'; n.projection_blend = 0.25
    out = next(n for n in N if n.type == 'OUTPUT_MATERIAL')
    for l in list(out.inputs['Displacement'].links): L.remove(l)
    bs = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    if tint:
        src = bs.inputs['Base Color'].links[0].from_socket
        mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        mx.inputs['B'].default_value = (*tint, 1); L.new(src, mx.inputs['A']); L.new(mx.outputs['Result'], bs.inputs['Base Color'])
    return m

def flat_mat(name, rgb, rough=0.5, metal=0.0, emit=None, estr=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs['Base Color'].default_value = (*rgb, 1); bs.inputs['Roughness'].default_value = rough; bs.inputs['Metallic'].default_value = metal
    if emit:
        bs.inputs['Emission Color'].default_value = (*emit, 1); bs.inputs['Emission Strength'].default_value = estr
    if alpha < 1: bs.inputs['Alpha'].default_value = alpha
    return m

def noise_mat(name, c1, c2, scale=20, rough=0.6, metal=0.0, bump=0.3):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N, L = nt.nodes, nt.links
    bs = N["Principled BSDF"]; tc = N.new('ShaderNodeTexCoord'); nz = N.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 8
    cr = N.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (*c1, 1); cr.color_ramp.elements[1].color = (*c2, 1)
    bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump
    L.new(tc.outputs['Object'], nz.inputs['Vector']); L.new(nz.outputs['Fac'], cr.inputs['Fac']); L.new(cr.outputs['Color'], bs.inputs['Base Color'])
    L.new(nz.outputs['Fac'], bp.inputs['Height']); L.new(bp.outputs['Normal'], bs.inputs['Normal'])
    bs.inputs['Roughness'].default_value = rough; bs.inputs['Metallic'].default_value = metal
    return m

M_BRICK = world_mat("castle_brick_01", 0.6, tint=(0.8, 0.78, 0.74), name="M_CellBrick")
M_STONE = world_mat("old_stone_wall", 0.45, name="M_YardWall")
M_COBBLE = world_mat("cobblestone_floor_01", 0.5, name="M_Cobble")
M_FLOOR = world_mat("stone_floor", 0.55, tint=(0.75, 0.72, 0.68), name="M_CellFloor")
M_RUST = world_mat("rusty_metal", 4.0, name="M_Rust")
M_WOOD = world_mat("wood_planks", 0.7, name="M_Planks")
M_SAND = world_mat("sand_01", 3.0, tint=(0.45, 0.33, 0.24), name="M_MouldSand")
M_SANDST = world_mat("large_sandstone_blocks", 0.35, tint=(1.35, 1.28, 1.15), name="M_Sandstone")
M_WBRICK = world_mat("castle_brick_01", 0.6, tint=(0.75, 0.55, 0.42), name="M_ShopBrick")
M_IRON = flat_mat("M_Iron", (0.05, 0.05, 0.05), 0.45, 1.0)
M_WAX = flat_mat("M_Wax", (0.82, 0.74, 0.55), 0.12)
M_WAX.node_tree.nodes["Principled BSDF"].inputs['Subsurface Weight'].default_value = 0.4
M_WAX.node_tree.nodes["Principled BSDF"].inputs['Subsurface Radius'].default_value = (0.02, 0.012, 0.006)
M_CANDLE = flat_mat("M_Candle", (0.86, 0.8, 0.66), 0.35); M_CANDLE.node_tree.nodes["Principled BSDF"].inputs['Subsurface Weight'].default_value = 0.6
M_FLAME = flat_mat("M_Flame", (1, 0.6, 0.2), 1.0, emit=(1.0, 0.55, 0.15), estr=40)
M_TIN = flat_mat("M_Tin", (0.55, 0.55, 0.52), 0.35, 1.0)
M_KEY = noise_mat("M_KeyIron", (0.16, 0.14, 0.12), (0.42, 0.38, 0.33), scale=300, rough=0.32, metal=1.0, bump=0.15)
M_MOLTEN = flat_mat("M_Molten", (1.0, 0.4, 0.05), 0.3, emit=(1.0, 0.45, 0.08), estr=30)
M_CRUC = noise_mat("M_Crucible", (0.08, 0.07, 0.07), (0.25, 0.22, 0.2), scale=40, rough=0.8)
M_CRUMB = noise_mat("M_Crumb", (0.18, 0.08, 0.035), (0.42, 0.24, 0.12), scale=180, rough=0.85, bump=0.6)
M_CLOTH = flat_mat("M_Linen", (0.78, 0.74, 0.66), 0.8)
M_GREEN = flat_mat("M_FlagG", (0.03, 0.32, 0.12), 0.75)
M_WHITE = flat_mat("M_FlagW", (0.85, 0.85, 0.82), 0.75)
M_ORANGE = flat_mat("M_FlagO", (0.85, 0.36, 0.06), 0.75)
M_DARK = flat_mat("M_Dark", (0.01, 0.01, 0.01), 0.9)
M_FURN = flat_mat("M_FurnaceMouth", (1, 0.4, 0.1), 0.5, emit=(1.0, 0.38, 0.08), estr=25)
M_GLASS = flat_mat("M_Window", (0.05, 0.06, 0.07), 0.08, 0.3)
M_BRASS = flat_mat("M_Brass", (0.6, 0.42, 0.18), 0.3, 1.0)
M_POLE = flat_mat("M_Pole", (0.75, 0.72, 0.65), 0.4, 0.6)

# ------------------------------------------------------------------ geometry helpers
def box(name, mn, mx, mat, c="Set", bevel=0.0):
    mn, mx = Vector(mn), Vector(mx)
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector(((mn.x + mx.x) / 2 + v.co.x * (mx.x - mn.x), (mn.y + mx.y) / 2 + v.co.y * (mx.y - mn.y), (mn.z + mx.z) / 2 + v.co.z * (mx.z - mn.z)))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); coll(c).objects.link(o); me.materials.append(mat)
    if bevel:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = 2
    return o

def cyl(name, center, r, h, mat, c="Set", verts=24, r2=None, axis='Z'):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=verts, radius1=r, radius2=r if r2 is None else r2, depth=h)
    if axis == 'X': bmesh.ops.rotate(bm, verts=bm.verts, matrix=Matrix.Rotation(R_(90), 3, 'Y'))
    if axis == 'Y': bmesh.ops.rotate(bm, verts=bm.verts, matrix=Matrix.Rotation(R_(90), 3, 'X'))
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); coll(c).objects.link(o); o.location = center; me.materials.append(mat)
    return o

def wall_with_holes(name, axis, a0, a1, t0, t1, z0, z1, holes, mat, c="Set"):
    """wall spanning a0..a1 along axis ('X' or 'Y'), thickness t0..t1 on the other axis, with rectangular holes [(a0,a1,z0,z1)]"""
    cuts_a = sorted({a0, a1} | {h[0] for h in holes} | {h[1] for h in holes})
    parts = []
    for i in range(len(cuts_a) - 1):
        lo, hi = cuts_a[i], cuts_a[i + 1]
        zs = [(z0, z1)]
        for h in holes:
            if h[0] <= lo and hi <= h[1]:
                new = []
                for (za, zb) in zs:
                    if h[2] > za: new.append((za, min(zb, h[2])))
                    if h[3] < zb: new.append((max(za, h[3]), zb))
                zs = new
        for (za, zb) in zs:
            if zb - za > 1e-4:
                parts.append((lo, hi, za, zb))
    obs = []
    for j, (lo, hi, za, zb) in enumerate(parts):
        if axis == 'X': obs.append(box(f"{name}_{j}", (lo, t0, za), (hi, t1, zb), mat, c))
        else: obs.append(box(f"{name}_{j}", (t0, lo, za), (t1, hi, zb), mat, c))
    return obs

def append_obj(asset, names=None, c="Props"):
    p = os.path.join(AS, asset, asset + "_1k.blend")
    with bpy.data.libraries.load(p) as (s, d):
        d.objects = [n for n in s.objects if names is None or n in names]
    obs = [o for o in d.objects if o]
    for o in obs: coll(c).objects.link(o)
    return obs

def dup(o, name, loc=None, rot=None, scale=None, c="Props"):
    n = o.copy(); n.name = name; coll(c).objects.link(n)
    if loc is not None: n.location = loc
    if rot is not None: n.rotation_euler = rot
    if scale is not None: n.scale = scale
    return n

# ================================================================== CELL  (interior x[-2,2] y[-2,2] z[0,3])
WIN = (0.45, 1.15, 1.62, 2.24)     # x0,x1,z0,z1 in the north wall
DOOR = (-0.15, 0.85, 0.0, 2.15)    # y0,y1,z0,z1 in the east wall
box("Cell_Floor", (-2.4, -2.4, -0.1), (2.4, 2.4, 0.004), M_FLOOR)
wall_with_holes("Cell_WallW", 'Y', -2.35, 2.35, -2.35, -2.0, 0, 3.0, [], M_BRICK)
wall_with_holes("Cell_WallS", 'X', -2.0, 2.0, -2.35, -2.0, 0, 3.0, [], M_BRICK)
wall_with_holes("Cell_WallN", 'X', -2.0, 2.0, 2.0, 2.35, 0, 3.0, [(WIN[0], WIN[1], WIN[2], WIN[3])], M_BRICK)
wall_with_holes("Cell_WallE", 'Y', -2.35, 2.35, 2.0, 2.35, 0, 3.0, [(DOOR[0], DOOR[1], DOOR[2], DOOR[3])], M_BRICK)
box("Cell_Ceiling", (-2.4, -2.4, 3.0), (2.4, 2.4, 3.3), M_BRICK)
for i, x in enumerate((0.59, 0.73, 0.87, 1.01)):
    cyl(f"Cell_WinBar{i}", (x, 2.2, (WIN[2] + WIN[3]) / 2), 0.016, WIN[3] - WIN[2], M_IRON, verts=12)
box("Cell_WinBarH", (WIN[0], 2.18, 1.88), (WIN[1], 2.22, 1.90), M_IRON)
# straw on the floor, bucket, tin cup
for i in range(60):
    x, y = random.uniform(-1.9, -0.6), random.uniform(-1.9, 0.6)
    s = cyl(f"Straw{i}", (x, y, 0.006), 0.0018, random.uniform(0.06, 0.14), flat_mat("M_Straw", (0.55, 0.45, 0.22), 0.7) if i == 0 else bpy.data.materials["M_Straw"], verts=4, axis='X')
    s.rotation_euler = (0, 0, random.uniform(0, 6.28))

# door (castle door leaf, hinged at y=DOOR[0] on the corridor side of the opening), lock box on the inside face
dl = append_obj("large_castle_door", ["large_castle_door_right"], c="Cell")[0]
dl.data = dl.data.copy()
me = dl.data
xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]; zs = [v.co.z for v in me.vertices]
w, t, hgt = max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)
me.transform(Matrix.Translation((-min(xs), -(min(ys) + max(ys)) / 2, -min(zs))))
me.transform(DIAG(1.0 / w * (DOOR[1] - DOOR[0] - 0.02), 0.09 / t, (DOOR[3] - 0.04) / hgt))
me.transform(Matrix.Translation((0, 0, 0.035)))
door_piv = bpy.data.objects.new("CellDoor_Pivot", None); coll("Cell").objects.link(door_piv)
door_piv.location = (2.1, DOOR[0] + 0.01, 0.0); door_piv.rotation_euler = (0, 0, R_(90))
dl.parent = door_piv; dl.location = (0, 0, 0); dl.rotation_euler = (0, 0, 0); dl.name = "CellDoor"
bpy.context.view_layer.update()
LOCK_C = Vector((2.03, 0.62, 1.08))   # lock box centre, inside face
lk = box("CellLock", (-0.025, -0.11, -0.08), (0.025, 0.11, 0.08), noise_mat("M_LockIron", (0.03, 0.03, 0.03), (0.14, 0.1, 0.08), 90, 0.5, 0.9, 0.3), c="Cell", bevel=0.004)
kh = box("CellLock_Keyhole", (-0.028, -0.006, -0.02), (-0.024, 0.006, 0.012), M_DARK, c="Cell")
for o in (lk, kh):
    o.parent = door_piv; o.matrix_parent_inverse = door_piv.matrix_world.inverted()
bolt = box("CellLock_Bolt", (1.99, 0.62, 1.03), (2.01, 0.86, 1.06), M_IRON, c="Cell")
bolt.parent = door_piv; bolt.matrix_parent_inverse = door_piv.matrix_world.inverted()
lk.location = LOCK_C - Vector((0, 0, 0)); kh.location = LOCK_C
# geometry for lk/kh is local around origin, so place them in world then parent-inverse handles it
door_grille = []
for i in range(4):
    door_grille.append(cyl(f"CellDoor_GrilleBar{i}", (2.1, 0.17 + i * 0.12, 1.65), 0.01, 0.3, M_IRON, c="Cell", verts=8))
for o in door_grille:
    o.parent = door_piv; o.matrix_parent_inverse = door_piv.matrix_world.inverted()
# table under the window, stool, bed
tb = append_obj("WoodenTable_01", c="Cell")[0]
tb.scale = (0.72, 0.9, 1.42); tb.location = (0.85, 1.6, 0.0)
TABLE_Z = 0.549 * 1.42
bed = append_obj("old_bed_frame", c="Cell")[0]; bed.location = (-1.45, -0.7, 0); bed.rotation_euler = (0, 0, 0)
box("Bed_Mattress", (-1.88, -1.66, 0.42), (-1.02, 0.26, 0.52), noise_mat("M_Mattress", (0.32, 0.28, 0.2), (0.48, 0.42, 0.3), 8, 0.9), c="Cell", bevel=0.03)
box("Bed_Blanket", (-1.9, -1.0, 0.52), (-1.0, 0.28, 0.56), noise_mat("M_Blanket", (0.18, 0.16, 0.13), (0.3, 0.27, 0.2), 30, 0.95), c="Cell", bevel=0.02)
st = append_obj("painted_wooden_stool", c="Cell")[0]; st.location = (-0.6, 1.2, 0); st.rotation_euler = (0, 0, R_(20))
bk = cyl("Cell_Bucket", (-1.6, 1.6, 0.16), 0.15, 0.32, M_TIN, c="Cell", r2=0.13)
# candle (own geometry so it can burn down), tin lid with wax pool, iron key
CANDLE_P = Vector((0.52, 1.72, TABLE_Z))
cyl("Candle_Saucer", CANDLE_P + Vector((0, 0, 0.006)), 0.055, 0.012, M_TIN, c="Cell", verts=32)
cnd = cyl("Candle", CANDLE_P + Vector((0, 0, 0.012)), 0.022, 0.2, M_CANDLE, c="Cell", verts=24)
cnd.data.transform(Matrix.Translation((0, 0, 0.1)))   # origin at the base so scale.z burns it down
flm = bpy.data.objects.new("Candle_Flame", bpy.data.meshes.new("Candle_Flame")); coll("Cell").objects.link(flm)
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.009)
for v in bm.verts:
    v.co.z = v.co.z * 2.4 + (0.012 if v.co.z > 0 else 0) ; v.co.x *= 1 - max(0, v.co.z) * 25; v.co.y *= 1 - max(0, v.co.z) * 25
bm.to_mesh(flm.data); bm.free(); flm.data.materials.append(M_FLAME)
flm.location = CANDLE_P + Vector((0, 0, 0.012 + 0.2 + 0.018))
wick = cyl("Candle_Wick", CANDLE_P + Vector((0, 0, 0.219)), 0.0012, 0.014, M_DARK, c="Cell", verts=6)
cl = bpy.data.lights.new("L_Candle", 'POINT'); cl.energy = 6; cl.color = (1.0, 0.62, 0.3); cl.shadow_soft_size = 0.02
clo = bpy.data.objects.new("L_Candle", cl); coll("Cell").objects.link(clo); clo.location = flm.location + Vector((0, 0, 0.02))
TIN_P = Vector((0.92, 1.5, TABLE_Z))
cyl("WaxTin", TIN_P + Vector((0, 0, 0.006)), 0.075, 0.012, M_TIN, c="Cell", verts=40)
box("Table_Rag", (1.1, 1.35, TABLE_Z), (1.3, 1.62, TABLE_Z + 0.004), M_CLOTH, c="Cell")
sc["TABLE_Z"] = TABLE_Z; sc["CANDLE_P"] = CANDLE_P; sc["TIN_P"] = TIN_P; sc["LOCK_C"] = LOCK_C

# key: bow ring + shaft + bit, x along the shaft, z = thickness; origin at the shaft middle
def key_mesh(name, notch=False):
    bm = bmesh.new()
    def add_ring(cx, R, rr, segs=28):
        g = bmesh.ops.create_circle(bm, cap_ends=False, radius=R, segments=segs)
        # torus by sweeping: approximate with small cylinders around the ring
    # build from boxes/cylinders merged
    parts = []
    for i in range(20):
        a0, a1 = 2 * math.pi * i / 20, 2 * math.pi * (i + 1) / 20
        p0 = Vector((-0.05 + 0.021 * math.cos(a0), 0.021 * math.sin(a0), 0)); p1 = Vector((-0.05 + 0.021 * math.cos(a1), 0.021 * math.sin(a1), 0))
        parts.append((p0, p1, 0.0045))
    for (p0, p1, r) in parts:
        d = p1 - p0; c = (p0 + p1) / 2
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=r, radius2=r, depth=d.length * 1.15)
        q = Vector((0, 0, 1)).rotation_difference(d.normalized())
        bmesh.ops.rotate(bm, verts=res['verts'], matrix=q.to_matrix()); bmesh.ops.translate(bm, verts=res['verts'], vec=c)
    # inner decorative trefoil
    for k in range(3):
        a = 2 * math.pi * k / 3
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.006, radius2=0.006, depth=0.004)
        bmesh.ops.translate(bm, verts=res['verts'], vec=Vector((-0.05 + 0.009 * math.cos(a), 0.009 * math.sin(a), 0)))
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.0048, radius2=0.0048, depth=0.092)
    bmesh.ops.rotate(bm, verts=res['verts'], matrix=Matrix.Rotation(R_(90), 3, 'Y')); bmesh.ops.translate(bm, verts=res['verts'], vec=Vector((0.017, 0, 0)))
    for (x0, x1) in ((-0.03, -0.024), (0.0, 0.004)):   # collars
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.0068, radius2=0.0068, depth=x1 - x0)
        bmesh.ops.rotate(bm, verts=res['verts'], matrix=Matrix.Rotation(R_(90), 3, 'Y')); bmesh.ops.translate(bm, verts=res['verts'], vec=Vector(((x0 + x1) / 2, 0, 0)))
    bits = [(0.044, 0.062, -0.026, 0.0)] if not notch else [(0.044, 0.050, -0.026, 0.0), (0.053, 0.062, -0.018, 0.0)]
    bits += [(0.050, 0.053, -0.020, 0.0)] if not notch else []
    for (x0, x1, y0, y1) in bits:
        res = bmesh.ops.create_cube(bm, size=1.0)
        for v in res['verts']:
            v.co = Vector(((x0 + x1) / 2 + v.co.x * (x1 - x0), (y0 + y1) / 2 + v.co.y * (y1 - y0), v.co.z * 0.0055))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.transform(Matrix.Translation((0.005, 0, 0)))
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); coll("Props").objects.link(o); me.materials.append(M_KEY)
    return o
KEY_M = key_mesh("Key_Master")              # the prison master key (beats 1, 7)
KEY_C1 = key_mesh("Key_Copy1", notch=True)  # first cast: wrong bit, jams (beats 4-6)
KEY_C2 = key_mesh("Key_Copy2")              # second cast: works (beat 8)
for k in (KEY_C1, KEY_C2):
    k.data.materials[0] = noise_mat("M_KeyCast_" + k.name, (0.22, 0.21, 0.19), (0.5, 0.47, 0.42), 400, 0.3, 1.0, 0.2) if k is KEY_C1 else bpy.data.materials["M_KeyCast_Key_Copy1"]

def key_sdf(px, py):
    """>0 inside the key's silhouette (key-local, origin at shaft middle +0.005)"""
    px -= 0.005
    ring = 0.0055 - abs(math.hypot(px + 0.05, py) - 0.021)
    tref = max(0.006 - math.hypot(px + 0.05 - 0.009 * math.cos(2 * math.pi * k / 3), py - 0.009 * math.sin(2 * math.pi * k / 3)) for k in range(3))
    shaft = min(0.0052 - abs(py), min(px + 0.03, 0.063 - px))
    bit = min(min(px - 0.044, 0.062 - px), min(py + 0.026, 0.0 - py))
    return max(ring, tref, shaft, bit)

def wax_pool(name, center, angle):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=150, y_segments=150, size=0.068)
    for v in list(bm.verts):
        if v.co.xy.length > 0.066: bm.verts.remove(v)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); coll("Cell").objects.link(o); o.location = center; o.rotation_euler = (0, 0, angle)
    me.materials.append(M_WAX)
    for v in me.vertices: v.co.z = 0.0035 * (1 - (v.co.xy.length / 0.066) ** 6)
    o.shape_key_add(name="Basis")
    sk = o.shape_key_add(name="Imprint")
    for i, v in enumerate(me.vertices):
        d = key_sdf(v.co.x, v.co.y)
        if d > -0.0015:
            s = min(1.0, (d + 0.0015) / 0.002)
            sk.data[i].co.z = v.co.z - 0.0042 * s
    for p in me.polygons: p.use_smooth = True
    return o
WAX = wax_pool("WaxPool", TIN_P + Vector((0, 0, 0.012)), R_(205))
WAX_MOLD = wax_pool("WaxMold_Pocket", Vector((0, 0, 0)), 0)   # the copy that goes into the visitor's pocket
WAX_MOLD.data.shape_keys.key_blocks["Imprint"].value = 1.0
tin2 = cyl("WaxTin_Pocket", (0, 0, -0.007), 0.075, 0.012, M_TIN, c="Cell", verts=40); tin2.parent = WAX_MOLD
WAX_MOLD.location = (0, 0, -50)

# ================================================================== CORRIDOR  x[2.35, 8.2], y[-0.9, 0.9], z[0, 2.8]
CEX = (7.0, 7.9)   # exit opening in the north wall (x range)
box("Corr_Floor", (2.35, -1.25, -0.1), (8.55, 1.25, 0.004), M_FLOOR, c="Corridor")
wall_with_holes("Corr_WallS", 'X', 2.35, 8.55, -1.25, -0.9, 0, 2.8, [(3.0, 3.5, 1.9, 2.4), (5.5, 6.0, 1.9, 2.4)], M_BRICK, c="Corridor")
wall_with_holes("Corr_WallN", 'X', 2.35, 8.55, 0.9, 1.25, 0, 2.8, [(CEX[0], CEX[1], 0.0, 2.2)], M_BRICK, c="Corridor")
box("Corr_WallE", (8.2, -1.25, 0), (8.55, 1.25, 2.8), M_BRICK, c="Corridor")
box("Corr_Ceiling", (2.35, -1.25, 2.8), (8.55, 1.25, 3.1), M_BRICK, c="Corridor")
# the cell's east wall doubles as the corridor's west end (door opening y[-0.15,0.85]); corridor spans y[-0.9,0.9]
gate_src = append_obj("large_iron_gate", ["large_iron_gate_right_door"], c="Corridor")[0]
gs = gate_src.data
xs = [v.co.x for v in gs.vertices]; ys = [v.co.y for v in gs.vertices]; zs = [v.co.z for v in gs.vertices]
gw, gt, gh = max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)
gs.transform(Matrix.Translation((-min(xs), -(min(ys) + max(ys)) / 2, -min(zs))))
GATES = []
for i, gx in enumerate((3.6, 5.0, 6.4)):
    for side, yy, rz in (("N", 0.88, -90), ("S", -0.88, 90)):
        piv = bpy.data.objects.new(f"CorrGate{i}{side}_Pivot", None); coll("Corridor").objects.link(piv)
        piv.location = (gx, yy, 0.0); piv.rotation_euler = (0, 0, R_(rz))
        g = dup(gate_src, f"CorrGate{i}{side}", c="Corridor"); g.parent = piv; g.location = (0, 0, 0); g.rotation_euler = (0, 0, 0)
        g.scale = (0.875 / gw, 1.0, 2.75 / gh)
    box(f"CorrGate{i}_FrameT", (gx - 0.06, -0.9, 2.75), (gx + 0.06, 0.9, 2.8), M_IRON, c="Corridor")
coll("Corridor").objects.unlink(gate_src); bpy.data.objects.remove(gate_src)
lan = append_obj("Lantern_01", c="Corridor")
for o in lan:
    if o.name == "Lantern_01": lan_src = o
for i, x in enumerate((4.3, 7.1)):
    for o in lan:
        d = dup(o, f"{o.name}_C{i}", loc=(x, -0.86, 1.75), c="Corridor")
    ll = bpy.data.lights.new(f"L_CorrLantern{i}", 'POINT'); ll.energy = 40; ll.color = (1.0, 0.6, 0.28); ll.shadow_soft_size = 0.05
    lo = bpy.data.objects.new(f"L_CorrLantern{i}", ll); coll("Corridor").objects.link(lo); lo.location = (x, -0.82, 1.9)
for o in lan: coll("Corridor").objects.unlink(o)
gst = dup(st, "Corr_GuardStool", loc=(6.12, -0.62, 0), rot=(0, 0, R_(-10)), c="Corridor")

# ================================================================== YARD  x[-10,10] y[~1.25,16]
box("Ground", (-14, -8, -0.2), (40, 42, 0.0), M_COBBLE, c="Yard")
# the cell block's outer north face and roof: cell block x[-2.35,2.35] y[-2.35,2.35]; corridor block x[2.35,8.55] y[-1.25,1.25]
box("Block_Roof", (-2.45, -2.45, 3.3), (8.65, 2.45, 3.45), M_STONE, c="Yard")
box("Block_UpperWall", (-2.35, 2.0, 3.0), (2.35, 2.35, 3.3), M_STONE, c="Yard")
wall_with_holes("YardWallS", 'X', -10.0, -2.35, 2.0, 2.35, 0, 5.0, [], M_STONE, c="Yard")
wall_with_holes("YardWallW", 'Y', -8, 16.35, -10.35, -10.0, 0, 5.0, [], M_STONE, c="Yard")
YARD_GATE = (5.0, 7.0)
wall_with_holes("YardWallE", 'Y', 1.25, 16.35, 10.0, 10.35, 0, 5.0, [(YARD_GATE[0], YARD_GATE[1], 0, 3.0)], M_STONE, c="Yard")
box("YardWallE_S", (8.55, 1.0, 0), (10.35, 1.25, 5.0), M_STONE, c="Yard")
wall_with_holes("YardWallN", 'X', -10.35, 10.35, 16.0, 16.35, 0, 5.0, [], M_STONE, c="Yard")
for x in (-6, -2, 2, 6):      # wall-top walkway brackets / buttresses
    box(f"YardButtress{x}", (x - 0.3, 15.6, 0), (x + 0.3, 16.0, 4.2), M_STONE, c="Yard", bevel=0.05)
# yard gate: both iron leaves at x=10.15 hinged on the tunnel sides
gl = append_obj("large_iron_gate", ["large_iron_gate_right_door", "large_iron_gate_left_door"], c="Yard")
YG = []
for i, o in enumerate(gl):
    me = o.data
    xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]; zs = [v.co.z for v in me.vertices]
    ww, hh = max(xs) - min(xs), max(zs) - min(zs)
    hinge_x = min(xs) if "right" in o.name else max(xs)
    me.transform(Matrix.Translation((-hinge_x, -(min(ys) + max(ys)) / 2, -min(zs))))
    me.transform(DIAG(1.0 / ww, 1, 2.95 / hh))
    piv = bpy.data.objects.new("YardGate_Pivot_" + ("R" if "right" in o.name else "L"), None); coll("Yard").objects.link(piv)
    if "right" in o.name:
        piv.location = (10.15, YARD_GATE[0] + 0.02, 0); piv.rotation_euler = (0, 0, R_(90))
    else:
        piv.location = (10.15, YARD_GATE[1] - 0.02, 0); piv.rotation_euler = (0, 0, R_(90))
    o.parent = piv; o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0)
    YG.append(piv)
# tunnel x[10.35, 13.0]
box("Tunnel_S", (10.35, 4.65, 0), (13.0, 5.0, 3.0), M_STONE, c="Yard")
box("Tunnel_N", (10.35, 7.0, 0), (13.0, 7.35, 3.0), M_STONE, c="Yard")
box("Tunnel_Roof", (10.35, 4.65, 3.0), (13.0, 7.35, 5.0), M_STONE, c="Yard")
# yard life: barrels, crates, a hand cart, a laundry line, lamp posts
bar_ = append_obj("WoodenTable_01", c="Yard")[0]; bar_.location = (-6.5, 9.0, 0); bar_.rotation_euler = (0, 0, R_(70))
for i, (x, y) in enumerate(((-8.8, 4.2), (-8.2, 4.6), (-8.9, 5.2), (8.9, 14.5), (9.2, 13.7))):
    cyl(f"Yard_Barrel{i}", (x, y, 0.45), 0.3, 0.9, M_WOOD, c="Yard", r2=0.27)
for i, (x, y, s) in enumerate(((-9.2, 12.0, 0.6), (-8.5, 12.1, 0.5), (-9.1, 12.2, 0.45))):
    box(f"Yard_Crate{i}", (x - s / 2, y - s / 2, (i == 2) * 0.6), (x + s / 2, y + s / 2, (i == 2) * 0.6 + s), M_WOOD, c="Yard", bevel=0.01)
cyl("Line_PoleA", (-7.5, 6.0, 1.2), 0.04, 2.4, M_WOOD, c="Yard"); cyl("Line_PoleB", (-3.5, 9.5, 1.2), 0.04, 2.4, M_WOOD, c="Yard")
_ln = cyl("Line_Rope", (-5.5, 7.75, 2.27), 0.006, 5.32, flat_mat("M_Rope", (0.5, 0.45, 0.35), 0.9), c="Yard", verts=6, axis='Y'); _ln.rotation_euler = (0, 0, -math.atan2(4.0, 3.5))
LAUNDRY = []
for i in range(5):
    t = (i + 0.5) / 5; p = Vector((-7.5, 6.0, 2.25)).lerp(Vector((-3.5, 9.5, 2.25)), t)
    me = bpy.data.meshes.new(f"Laundry{i}"); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=8, y_segments=10, size=0.3)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(f"Laundry{i}", me); coll("Yard").objects.link(o)
    o.location = p - Vector((0, 0, 0.3)); o.rotation_euler = (R_(90), 0, math.atan2(3.5, 4.0)); o.scale = (1.0, 1.2 + 0.2 * (i % 2), 1)
    me.materials.append([M_CLOTH, bpy.data.materials["M_Blanket"], flat_mat("M_Shirt%d" % i, (0.55, 0.5, 0.42), 0.85)][i % 3])
    wv = o.modifiers.new("wave", 'WAVE'); wv.height = 0.03; wv.width = 0.25; wv.speed = 0.012 + 0.003 * i; wv.use_normal = True; wv.use_x = True; wv.use_y = False
    LAUNDRY.append(o)
for i, (x, y) in enumerate(((-4.0, 15.0), (4.0, 15.0), (8.8, 8.8))):
    cyl(f"Yard_LampPost{i}", (x, y, 1.6), 0.05, 3.2, M_IRON, c="Yard")
    for o in lan:
        dup(o, f"{o.name}_Y{i}", loc=(x, y - 0.25, 3.0), c="Yard")
    ll = bpy.data.lights.new(f"L_YardLamp{i}", 'POINT'); ll.energy = 40; ll.color = (1.0, 0.62, 0.3); ll.shadow_soft_size = 0.06
    lo = bpy.data.objects.new(f"L_YardLamp{i}", ll); coll("Yard").objects.link(lo); lo.location = (x, y - 0.25, 3.15)
box("Yard_LampArm", (3.95, 14.7, 3.25), (4.05, 15.0, 3.3), M_IRON, c="Yard")
# watch tower in the NW corner
box("Tower", (-10.35, 13.5, 0), (-7.8, 16.35, 8.0), M_STONE, c="Yard")
box("Tower_Window", (-7.82, 14.4, 6.0), (-7.79, 15.2, 6.8), M_GLASS, c="Yard")

# ================================================================== FOUNDRY  x[13,21] y[2,10] z[0,4]
box("Shop_Floor", (13.0, 2.0, -0.1), (21.0, 10.0, 0.004), M_WOOD, c="Foundry")
wall_with_holes("Shop_WallW", 'Y', 1.65, 10.35, 13.0, 13.35, 0, 4.0, [(5.0, 7.0, 0, 3.0)], M_WBRICK, c="Foundry")
box("Shop_WallE", (20.65, 1.65, 0), (21.0, 10.35, 4.0), M_WBRICK, c="Foundry")
box("Shop_WallS", (13.0, 1.65, 0), (21.0, 2.0, 4.0), M_WBRICK, c="Foundry")
wall_with_holes("Shop_WallN", 'X', 13.0, 21.0, 10.0, 10.35, 0, 4.0, [(15.0, 16.4, 1.4, 2.8), (18.0, 19.4, 1.4, 2.8)], M_WBRICK, c="Foundry")
box("Shop_Roof", (12.9, 1.6, 4.0), (21.1, 10.4, 4.2), M_WOOD, c="Foundry")
for x in (14.5, 16.5, 18.5):
    box(f"Shop_Beam{x}", (x - 0.1, 2.0, 3.6), (x + 0.1, 10.0, 3.8), M_WOOD, c="Foundry")
BENCH_P = Vector((15.0, 7.0, 0))
bench = append_obj("WoodenTable_01", c="Foundry")[0]; bench.location = BENCH_P; bench.scale = (1.0, 1.0, 1.6)
BENCH_Z = 0.549 * 1.6
sc["BENCH_Z"] = BENCH_Z; sc["BENCH_P"] = BENCH_P
MOULD_P = BENCH_P + Vector((-0.35, -0.05, BENCH_Z))
mb = box("Mould_Bottom", (-0.17, -0.12, 0), (0.17, 0.12, 0.06), M_SAND, c="Foundry", bevel=0.004); mb.location = MOULD_P
mbf = box("Mould_FlaskB", (-0.18, -0.13, 0), (0.18, 0.13, 0.05), M_RUST, c="Foundry"); mbf.location = MOULD_P + Vector((0, 0, -0.001))
mt = box("Mould_Top", (-0.17, -0.12, 0), (0.17, 0.12, 0.06), M_SAND, c="Foundry", bevel=0.004); mt.location = MOULD_P + Vector((0, 0, 0.062))
box("Mould_Sprue", (-0.012, -0.012, 0.06), (0.012, 0.012, 0.061), M_DARK, c="Foundry").parent = mt
sc["MOULD_P"] = MOULD_P
# glowing key cavity on the bottom half (the fresh casting)
cast = key_mesh("Key_Casting", notch=True); cast.data.materials[0] = M_MOLTEN; cast.location = MOULD_P + Vector((0, 0, 0.061))
# crucible with long shank
cru = cyl("Crucible", (0, 0, 0), 0.07, 0.16, M_CRUC, c="Foundry", r2=0.085)
cmol = cyl("Crucible_Molten", (0, 0, 0.07), 0.078, 0.01, M_MOLTEN, c="Foundry"); cmol.parent = cru
shank = box("Crucible_Shank", (-0.75, -0.012, -0.012), (-0.08, 0.012, 0.012), M_IRON, c="Foundry"); shank.parent = cru
ring = cyl("Crucible_Ring", (0, 0, 0.0), 0.088, 0.03, M_IRON, c="Foundry"); ring.parent = cru
cru.location = (17.0, 8.6, 0.6)   # resting by the furnace until animated
# pour stream
cu = bpy.data.curves.new("PourStream", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.008; cu.bevel_resolution = 3
sp = cu.splines.new('BEZIER'); sp.bezier_points.add(1)
pour = bpy.data.objects.new("PourStream", cu); coll("Foundry").objects.link(pour); cu.materials.append(M_MOLTEN)
# furnace
box("Furnace", (18.8, 8.4, 0), (20.6, 9.9, 1.3), M_WBRICK, c="Foundry", bevel=0.02)
box("Furnace_Mouth", (19.3, 8.38, 0.45), (20.1, 8.42, 0.95), M_FURN, c="Foundry")
cyl("Furnace_Chimney", (19.7, 9.4, 2.7), 0.25, 2.8, M_WBRICK, c="Foundry")
fl_ = bpy.data.lights.new("L_Furnace", 'AREA'); fl_.energy = 220; fl_.color = (1.0, 0.42, 0.12); fl_.size = 0.8
fo = bpy.data.objects.new("L_Furnace", fl_); coll("Foundry").objects.link(fo); fo.location = (19.7, 8.2, 0.7); fo.rotation_euler = (R_(90), 0, 0)
gl_ = bpy.data.lights.new("L_PourGlow", 'POINT'); gl_.energy = 0; gl_.color = (1.0, 0.45, 0.1); gl_.shadow_soft_size = 0.05
go = bpy.data.objects.new("L_PourGlow", gl_); coll("Foundry").objects.link(go); go.location = MOULD_P + Vector((0, 0, 0.25))
for i, x in enumerate((14.0, 18.0)):
    ll = bpy.data.lights.new(f"L_ShopLamp{i}", 'POINT'); ll.energy = 70; ll.color = (1.0, 0.65, 0.35); ll.shadow_soft_size = 0.1
    lo = bpy.data.objects.new(f"L_ShopLamp{i}", ll); coll("Foundry").objects.link(lo); lo.location = (x, 4.5 + i * 3, 3.0)
    for o in lan: dup(o, f"{o.name}_S{i}", loc=(x, 4.5 + i * 3, 2.85), c="Foundry")
# clutter: tools on the wall, barrels, anvil-ish block, sand pile, bucket
for i in range(6):
    box(f"Shop_Tool{i}", (13.36, 3.0 + i * 0.25, 1.2), (13.4, 3.04 + i * 0.25, 1.8 + 0.1 * (i % 3)), M_IRON, c="Foundry")
cyl("Shop_Barrel0", (20.2, 3.0, 0.45), 0.3, 0.9, M_WOOD, c="Foundry", r2=0.27)
cyl("Shop_Barrel1", (19.6, 2.6, 0.45), 0.3, 0.9, M_WOOD, c="Foundry", r2=0.27)
box("Shop_Anvil", (17.6, 5.2, 0), (18.1, 5.5, 0.75), M_IRON, c="Foundry", bevel=0.02)
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.7)
for v in bm.verts: v.co.z = max(0, v.co.z) * 0.45
me = bpy.data.meshes.new("Shop_SandPile"); bm.to_mesh(me); bm.free()
sp_o = bpy.data.objects.new("Shop_SandPile", me); coll("Foundry").objects.link(sp_o); sp_o.location = (14.2, 9.2, 0); me.materials.append(M_SAND)
# cake + box on the bench
ck = append_obj("carrot_cake", c="Foundry")[0]
cm = ck.data.materials[0]; nt = cm.node_tree
bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
if bs.inputs['Base Color'].links:
    src = bs.inputs['Base Color'].links[0].from_socket
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    mx.inputs['B'].default_value = (0.62, 0.42, 0.3, 1); nt.links.new(src, mx.inputs['A']); nt.links.new(mx.outputs['Result'], bs.inputs['Base Color'])
CAKE_P = BENCH_P + Vector((0.25, -0.05, BENCH_Z))
ck.name = "Cake1"; ck.location = CAKE_P
def cake_halves(src, name):
    halves = []
    for sgn in (1, -1):
        me = src.data.copy(); bm = bmesh.new(); bm.from_mesh(me)
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        r = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=(sgn, 0, 0), clear_outer=True)
        edges = [e for e in r['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
        f = bmesh.ops.contextual_create(bm, geom=edges)
        bm.to_mesh(me); bm.free()
        if M_CRUMB.name not in me.materials: me.materials.append(M_CRUMB)
        ci = list(me.materials).index(M_CRUMB)
        for p in me.polygons:
            if abs(p.normal.x) > 0.95 and abs(p.center.x) < 1e-3: p.material_index = ci
        o = bpy.data.objects.new(f"{name}_{'R' if sgn < 0 else 'L'}", me); coll("Cell").objects.link(o); halves.append(o)
    return halves
CAKE2 = cake_halves(ck, "Cake2")      # the second cake, cut open in the cell (beat 8)
CAKE2_P = Vector((1.2, 1.45, TABLE_Z)); sc["CAKE2_P"] = CAKE2_P
for h in CAKE2: h.location = CAKE2_P
# knife
kn = box("Knife_Blade", (0.0, -0.011, -0.001), (0.15, 0.011, 0.001), flat_mat("M_Steel", (0.6, 0.6, 0.6), 0.25, 1.0), c="Cell")
kh_ = box("Knife_Handle", (-0.1, -0.012, -0.008), (0.0, 0.012, 0.008), M_WOOD, c="Cell"); kh_.parent = kn
kn.location = (1.33, 1.75, TABLE_Z + 0.008)
# parcel box: wooden box + lid
PBOX_P = BENCH_P + Vector((0.65, -0.05, BENCH_Z)); sc["PBOX_P"] = PBOX_P
pb_ = box("ParcelBox", (-0.15, -0.15, 0), (0.15, 0.15, 0.13), M_WOOD, c="Foundry", bevel=0.004)
pin = box("ParcelBox_Inside", (-0.135, -0.135, 0.012), (0.135, 0.135, 0.1305), M_DARK, c="Foundry"); pin.parent = pb_
plid = box("ParcelBox_Lid", (-0.155, -0.155, 0), (0.155, 0.155, 0.015), M_WOOD, c="Foundry", bevel=0.003)
pb_.location = PBOX_P; plid.location = PBOX_P + Vector((0.0, 0.32, 0.0))
twine = box("ParcelBox_Twine", (-0.16, -0.006, 0.0), (0.16, 0.006, 0.017), flat_mat("M_Twine", (0.6, 0.5, 0.32), 0.9), c="Foundry"); twine.parent = plid
# sparks (keyed later)
M_SPARK = flat_mat("M_Spark", (1, 0.7, 0.3), 0.5, emit=(1.0, 0.65, 0.25), estr=60)
for i in range(40):
    s = cyl(f"Spark{i}", (0, 0, -50), 0.0035, 0.02, M_SPARK, c="Foundry", verts=4)
# smoke: one light volume puff over the mould
bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.35)
me = bpy.data.meshes.new("Smoke"); bm.to_mesh(me); bm.free()
smk = bpy.data.objects.new("Smoke", me); coll("Foundry").objects.link(smk); smk.location = MOULD_P + Vector((0, 0, 0.5)); smk.scale = (1, 1, 1.6)
msm = bpy.data.materials.new("M_Smoke"); msm.use_nodes = True; nt = msm.node_tree
nt.nodes.remove(nt.nodes["Principled BSDF"]); vol = nt.nodes.new('ShaderNodeVolumePrincipled')
vol.inputs['Color'].default_value = (0.5, 0.48, 0.45, 1)
nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 4
mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.45; mr.inputs['From Max'].default_value = 0.7; mr.inputs['To Max'].default_value = 1.5
grad = nt.nodes.new('ShaderNodeTexGradient'); grad.gradient_type = 'SPHERICAL'
mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
dv = nt.nodes.new('ShaderNodeValue'); dv.name = "SmokeAmt"; dv.outputs[0].default_value = 0.0
mul2 = nt.nodes.new('ShaderNodeMath'); mul2.operation = 'MULTIPLY'
tco = nt.nodes.new('ShaderNodeTexCoord'); mpn = nt.nodes.new('ShaderNodeMapping'); mpn.name = "SmokeMap"
nt.links.new(tco.outputs['Object'], mpn.inputs['Vector']); nt.links.new(mpn.outputs['Vector'], nz.inputs['Vector'])
nt.links.new(tco.outputs['Object'], grad.inputs['Vector'])
nt.links.new(nz.outputs['Fac'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], mul.inputs[0]); nt.links.new(grad.outputs['Fac'], mul.inputs[1])
nt.links.new(mul.outputs[0], mul2.inputs[0]); nt.links.new(dv.outputs[0], mul2.inputs[1]); nt.links.new(mul2.outputs[0], vol.inputs['Density'])
nt.links.new(vol.outputs['Volume'], nt.nodes["Material Output"].inputs['Volume'])
me.materials.append(msm)

# ================================================================== GOVERNMENT STEPS (north of the yard wall)
GY = 20.0   # first step
for i in range(7):
    box(f"Gov_Step{i}", (-8.0 + i * 0.05, GY + i * 0.4, 0), (8.0 - i * 0.05, GY + 6.0, 0.22 * (i + 1)), M_SANDST, c="Gov")
TOPZ = 0.22 * 7; sc["GOV_TOPZ"] = TOPZ; sc["GOV_Y"] = GY
for i, x in enumerate((-6.5, -4.3, -2.1, 2.1, 4.3, 6.5)):
    cyl(f"Gov_Column{i}", (x, GY + 3.3, TOPZ + 3.5), 0.42, 7.0, M_SANDST, c="Gov", verts=28, r2=0.36)
    box(f"Gov_ColBase{i}", (x - 0.55, GY + 2.75, TOPZ), (x + 0.55, GY + 3.85, TOPZ + 0.35), M_SANDST, c="Gov")
box("Gov_Entablature", (-7.6, GY + 2.6, TOPZ + 7.0), (7.6, GY + 4.0, TOPZ + 8.3), M_SANDST, c="Gov", bevel=0.05)
me = bpy.data.meshes.new("Gov_Pediment"); bm = bmesh.new()
vs = [bm.verts.new(v) for v in ((-7.8, GY + 2.6, TOPZ + 8.3), (7.8, GY + 2.6, TOPZ + 8.3), (0, GY + 2.6, TOPZ + 10.6),
                                 (-7.8, GY + 4.0, TOPZ + 8.3), (7.8, GY + 4.0, TOPZ + 8.3), (0, GY + 4.0, TOPZ + 10.6))]
for f in ((0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)): bm.faces.new([vs[i] for i in f])
bm.to_mesh(me); bm.free(); pd = bpy.data.objects.new("Gov_Pediment", me); coll("Gov").objects.link(pd); me.materials.append(M_SANDST)
wall_with_holes("Gov_Facade", 'X', -8, 8, GY + 5.6, GY + 6.0, TOPZ, TOPZ + 8.3, [(-1.0, 1.0, TOPZ, TOPZ + 3.6), (-5.0, -3.8, TOPZ + 1.2, TOPZ + 3.6), (3.8, 5.0, TOPZ + 1.2, TOPZ + 3.6)], M_SANDST, c="Gov")
box("Gov_Door", (-1.0, GY + 5.7, TOPZ), (1.0, GY + 5.75, TOPZ + 3.6), M_DARK, c="Gov")
for x in (-4.4, 4.4):
    box(f"Gov_Win{x}", (x - 0.6, GY + 5.62, TOPZ + 1.2), (x + 0.6, GY + 5.65, TOPZ + 3.6), M_GLASS, c="Gov")
box("Gov_Wings", (-20, GY + 4.0, 0), (-8, GY + 14, 9.0), M_SANDST, c="Gov"); box("Gov_WingsE", (8, GY + 4.0, 0), (20, GY + 14, 9.0), M_SANDST, c="Gov")
for i in range(6):
    for side in (-1, 1):
        box(f"Gov_WingWin{side}_{i}", (side * (9 + i * 1.8) - 0.4, GY + 3.97, 3.0), (side * (9 + i * 1.8) + 0.4, GY + 4.0, 5.0), M_GLASS, c="Gov")
# flags: poles + 3-stripe cloth grid (green / white / orange), wave modifier (time-based, no simulation)
FLAGS = []
for i, (x, y, z) in enumerate(((-3.2, GY + 1.7, TOPZ * 0.55), (3.2, GY + 1.7, TOPZ * 0.55), (-12, GY - 0.8, 0), (12, GY - 0.8, 0))):
    cyl(f"FlagPole{i}", (x, y, z + 3.5), 0.045, 7.0, M_POLE, c="Gov")
    cyl(f"FlagPole{i}_Ball", (x, y, z + 7.05), 0.08, 0.1, M_BRASS, c="Gov")
    me = bpy.data.meshes.new(f"Flag{i}"); bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=36, y_segments=18, size=0.5)
    for v in bm.verts: v.co.x = (v.co.x + 0.5) * 2.7; v.co.y = (v.co.y + 0.5) * 1.35
    bm.to_mesh(me); bm.free()
    for m_ in (M_GREEN, M_WHITE, M_ORANGE): me.materials.append(m_)
    for p in me.polygons: p.material_index = min(2, int(p.center.x / 0.9))
    o = bpy.data.objects.new(f"Flag{i}", me); coll("Gov").objects.link(o)
    o.location = (x + 0.05, y, z + 5.6); o.rotation_euler = (R_(90), 0, 0)
    wv = o.modifiers.new("wave", 'WAVE'); wv.use_normal = True; wv.height = 0.16; wv.width = 0.7; wv.narrowness = 1.0; wv.speed = 0.07
    wv.start_position_x = 0.0; wv.use_y = False; wv.falloff_radius = 0; wv.time_offset = -i * 13
    o.modifiers.new("sub", 'SUBSURF').levels = 1
    for p in me.polygons: p.use_smooth = True
    FLAGS.append(o)
# plaza buildings behind the crowd (east/west) for depth
for side in (-1, 1):
    for j in range(2):
        box(f"Town{side}_{j}", (min(side * 11.5, side * 17), 16.6 + j * 3.6, 0), (max(side * 11.5, side * 17), 19.8 + j * 3.6, 8 + 3 * j), M_SANDST if j % 2 else M_STONE, c="Gov")

# ================================================================== LIGHT + WORLD
sun = bpy.data.lights.new("L_Sun", 'SUN'); sun.energy = 2.5; sun.angle = R_(8); sun.color = (1.0, 0.86, 0.68)
so = bpy.data.objects.new("L_Sun", sun); sc.collection.objects.link(so); so.rotation_euler = (R_(50), R_(10), R_(-25))
moon = bpy.data.lights.new("L_Moon", 'SUN'); moon.energy = 0.0; moon.angle = R_(2); moon.color = (0.55, 0.68, 1.0)
mo = bpy.data.objects.new("L_Moon", moon); sc.collection.objects.link(mo); mo.rotation_euler = (R_(55), 0, R_(200))
wl = bpy.data.lights.new("L_Window", 'AREA'); wl.energy = 30; wl.size = 0.7; wl.size_y = 0.6; wl.shape = 'RECTANGLE'; wl.color = (0.75, 0.82, 1.0)
wo = bpy.data.objects.new("L_Window", wl); coll("Cell").objects.link(wo); wo.location = ((WIN[0] + WIN[1]) / 2, 2.4, (WIN[2] + WIN[3]) / 2); wo.rotation_euler = (R_(-80), 0, 0)
fill = bpy.data.lights.new("L_CellFill", 'POINT'); fill.energy = 12; fill.color = (0.9, 0.75, 0.6); fill.shadow_soft_size = 0.6
fo2 = bpy.data.objects.new("L_CellFill", fill); coll("Cell").objects.link(fo2); fo2.location = (-0.8, -0.8, 2.4)
w = bpy.data.worlds.new("W_Sky"); sc.world = w; w.use_nodes = True; nt = w.node_tree
bg = nt.nodes["Background"]
def env(path):
    t = nt.nodes.new('ShaderNodeTexEnvironment'); t.image = bpy.data.images.load(path); return t
eday = env(os.path.join(AS, "hdri", "kloofendal_overcast_puresky_2k.hdr"))
enight = env(os.path.join(AS, "hdri", "qwantani_night_puresky_2k.hdr"))
mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.name = "DayNight"; mix.inputs['Factor'].default_value = 0.0
nt.links.new(eday.outputs['Color'], mix.inputs['A']); nt.links.new(enight.outputs['Color'], mix.inputs['B'])
nt.links.new(mix.outputs['Result'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 1.0
sc["WIN"] = WIN; sc["DOOR"] = DOOR; sc["CEX"] = CEX; sc["YARD_GATE"] = YARD_GATE
exec(open(os.path.join(HERE, "02b_costume.py")).read())
exec(open(os.path.join(HERE, "02c_cake.py")).read())
exec(open(os.path.join(HERE, "02d_realmodels.py")).read())
exec(open(os.path.join(HERE, "02e_props.py")).read())
print("SCENE objects", len(bpy.data.objects))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
