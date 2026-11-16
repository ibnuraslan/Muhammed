"""Store set (re-used from BellyFat_v010: floor, ceiling, walls, stocked gondolas, ceiling tubes) + new glass-door cooler bank,
condensing unit with fan, skeleton (Sketchfab CC-BY), debris for the 2019 store.
blender -b build/chars.blend --python 02_sets.py"""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix
exec(open(os.path.dirname(os.path.abspath(__file__)) + "/common.py").read())
R = math.radians; random.seed(11)
sc = bpy.context.scene
def col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
SET = col("SET"); C09 = col("COOLERS"); PR = col("PROPS")
# ---------------------------------------------------------------- store shell from BellyFat
KEEP = ("Floor", "Ceiling", "ShelfL", "ShelfR", "WallBack", "WallFront", "WallL", "WallR", "StoreArea", "Tube")
with bpy.data.libraries.load(SCR + "/store_src.blend", link=False) as (fd, td):
    td.objects = [n for n in fd.objects if n.split(".")[0] in KEEP]
    td.worlds = ["W_store"]
for o in td.objects:
    SET.objects.link(o)
    if o.animation_data: o.animation_data_clear()          # BellyFat shared actions: keying one object hid the walls
    if o.type == 'LIGHT' and o.data.animation_data: o.data.animation_data_clear()
sc.world = bpy.data.worlds["W_store"]
O = bpy.data.objects
H = 1.0                                          # ceiling raised 1 m (the worker stands on top of the coolers)
O["Ceiling"].location.z += H
for o in O:
    if o.name.startswith(("Tube", "StoreArea")): o.location.z += H
    if o.name.startswith("StoreArea"): o.data.energy *= 1.35
bpy.context.view_layer.update()
for n in ("WallBack", "WallFront", "WallL", "WallR"):
    o = O[n]; o.scale.z *= (3.62 + H + 0.05) / 3.6; bpy.context.view_layer.update()
    zs = [(o.matrix_world @ Vector(c)).z for c in o.bound_box]; o.location.z -= min(zs) + 0.02; bpy.context.view_layer.update()
    zs = [(o.matrix_world @ Vector(c)).z for c in o.bound_box]; print("WALL", n, round(min(zs), 2), round(max(zs), 2))
for n in ("ShelfL", "ShelfR"): O[n].location.x += 2.2           # gondolas end 2.4 m in front of the cooler bank
# empty copies of the gondolas for 2019 (product faces removed)
for n in ("ShelfL", "ShelfR"):
    s = O[n]; e = s.copy(); e.data = s.data.copy(); e.name = n + "_Empty"; SET.objects.link(e)
    bm = bmesh.new(); bm.from_mesh(e.data)
    pack = {i for i, m in enumerate(e.data.materials) if m and m.name.startswith("M_pack")}
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in pack], context='FACES')
    bm.to_mesh(e.data); bm.free(); print("EMPTY", e.name, len(e.data.polygons))
    e.hide_render = True; e.hide_viewport = True

# ---------------------------------------------------------------- materials
def mat(name, rgb, rough=0.4, metal=0.0, emit=None, ew=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; P = m.node_tree.nodes["Principled BSDF"]
    P.inputs["Base Color"].default_value = (*rgb, 1); P.inputs["Roughness"].default_value = rough; P.inputs["Metallic"].default_value = metal
    if emit: P.inputs["Emission Color"].default_value = (*emit, 1); P.inputs["Emission Strength"].default_value = ew
    return m
def glass_mat():
    m = bpy.data.materials.get("CoolerGlass")
    if m: return m
    m = bpy.data.materials.new("CoolerGlass"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); tr = nt.nodes.new("ShaderNodeBsdfTransparent"); tr.inputs[0].default_value = (0.93, 0.97, 1.0, 1)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.08
    fr = nt.nodes.new("ShaderNodeLayerWeight"); fr.inputs[0].default_value = 0.05
    mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(fr.outputs["Fresnel"], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(gl.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs[0])
    m.blend_method = 'BLEND' if hasattr(m, "blend_method") else None
    return m
M_CAB = mat("CoolerEnamel", (0.86, 0.88, 0.90), 0.35)
M_FRAME = mat("CoolerFrameAlu", (0.30, 0.32, 0.35), 0.3, 0.8)
M_CHROME = mat("Chrome", (0.85, 0.86, 0.88), 0.15, 1.0)
M_IN = mat("CoolerInside", (0.95, 0.96, 0.97), 0.4)
M_LED = mat("CoolerLED", (1, 1, 1), 0.3, 0, (0.92, 0.97, 1.0), 6.0)
M_HEAD = mat("CoolerHeader", (0.20, 0.55, 0.85), 0.35, 0, (0.25, 0.6, 1.0), 1.2)
M_GRILLE = mat("Grille", (0.08, 0.08, 0.09), 0.5, 0.3)
M_BACK = mat("CoolerBackPanel", (0.55, 0.57, 0.6), 0.45, 0.4)
M_COIL = mat("CopperCoil", (0.75, 0.42, 0.22), 0.3, 1.0)
M_FAN = mat("FanBlade", (0.12, 0.12, 0.13), 0.4, 0.2)
M_SHELF = mat("WireShelf", (0.7, 0.72, 0.75), 0.3, 0.9)
PROD = [mat("Prod%d" % i, c, 0.3) for i, c in enumerate([(0.9, 0.1, 0.1), (0.1, 0.6, 0.15), (0.95, 0.6, 0.05), (0.1, 0.35, 0.9), (0.95, 0.95, 0.95), (0.6, 0.1, 0.6), (0.95, 0.85, 0.1), (0.05, 0.75, 0.75)])]
M_PLAST = mat("BottlePlastic", (0.75, 0.9, 1.0), 0.15)
M_CAP = mat("Cap", (0.9, 0.9, 0.9), 0.4)

class MB:
    """mesh builder: boxes / cylinders into one bmesh with material slots"""
    def __init__(self): self.bm = bmesh.new(); self.mats = []
    def _mi(self, m):
        if m not in self.mats: self.mats.append(m)
        return self.mats.index(m)
    def box(self, c, d, m, bevel=0.0):
        r = bmesh.ops.create_cube(self.bm, size=1.0)
        for v in r["verts"]: v.co = Vector((v.co.x * d[0], v.co.y * d[1], v.co.z * d[2])) + Vector(c)
        mi = self._mi(m)
        for f in {f for v in r["verts"] for f in v.link_faces}: f.material_index = mi
        if bevel > 0:
            bmesh.ops.bevel(self.bm, geom=[e for e in {e for v in r["verts"] for e in v.link_edges}], offset=bevel, segments=2, affect='EDGES', profile=0.5)
            mi2 = mi
            for f in self.bm.faces:
                if f.material_index == 0 and mi != 0: pass
    def cyl(self, c, r_, h, m, seg=12, axis='Z', r2=None):
        res = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=seg, radius1=r_, radius2=r2 if r2 is not None else r_, depth=h)
        Mr = Matrix.Identity(3) if axis == 'Z' else Matrix.Rotation(R(90), 3, 'X') if axis == 'Y' else Matrix.Rotation(R(90), 3, 'Y')
        for v in res["verts"]: v.co = Mr @ v.co + Vector(c)
        mi = self._mi(m)
        for f in {f for v in res["verts"] for f in v.link_faces}: f.material_index = mi
    def done(self, name, coll, smooth=False):
        me = bpy.data.meshes.new(name); self.bm.to_mesh(me); self.bm.free()
        for m in self.mats: me.materials.append(m)
        if smooth:
            for p in me.polygons: p.use_smooth = True
        o = bpy.data.objects.new(name, me); coll.objects.link(o); return o

# ---------------------------------------------------------------- cooler unit (local: back face at x=0, front at x=+D, centred on y=0, floor z=0)
D, WID, HT, NDOOR = 0.85, 2.0, 2.15, 3
def bottle(mb, x, y, z, m, kind):
    if kind == 0:     # PET bottle
        mb.cyl((x, y, z + 0.11), 0.034, 0.22, M_PLAST, 10); mb.cyl((x, y, z + 0.115), 0.0355, 0.09, m, 10)
        mb.cyl((x, y, z + 0.25), 0.034, 0.06, M_PLAST, 10, r2=0.014); mb.cyl((x, y, z + 0.29), 0.015, 0.02, m if m != PROD[4] else M_CAP, 8)
    elif kind == 1:   # can
        mb.cyl((x, y, z + 0.062), 0.033, 0.124, m, 12); mb.cyl((x, y, z + 0.127), 0.03, 0.006, M_CHROME, 12)
    else:             # carton
        mb.box((x, y, z + 0.11), (0.07, 0.07, 0.2), m); mb.box((x, y, z + 0.225), (0.07, 0.01, 0.04), m)
def make_cooler(name, coll, seed, products=True):
    rnd = random.Random(seed)
    mb = MB(); t = 0.04
    mb.box((D / 2, 0, HT / 2), (D, WID, HT), M_CAB, 0)                 # carcass (front face hidden behind the frame)
    # interior cavity look: inner back + side walls drawn as panels just in front of the carcass front plane
    door_w = (WID - 0.10) / NDOOR; z0, z1 = 0.22, 1.92
    for i in range(NDOOR + 1):                                         # mullions
        y = -WID / 2 + 0.05 + i * door_w
        mb.box((D + 0.025, y, (z0 + z1) / 2), (0.05, 0.05, z1 - z0 + 0.08), M_FRAME)
        if 0 < i < NDOOR: mb.box((D + 0.008, y, (z0 + z1) / 2), (0.012, 0.02, z1 - z0 - 0.04), M_LED)
    mb.box((D + 0.025, 0, z0 - 0.02), (0.05, WID, 0.05), M_FRAME); mb.box((D + 0.025, 0, z1 + 0.02), (0.05, WID, 0.05), M_FRAME)
    mb.box((D + 0.006, 0, z1 + 0.13), (0.012, WID - 0.02, 0.17), M_HEAD)       # blank lit header (no text)
    mb.box((D + 0.006, 0, 0.10), (0.012, WID - 0.02, 0.16), M_GRILLE)           # kick plate
    for k in range(14): mb.box((D + 0.014, -WID / 2 + 0.1 + k * (WID - 0.2) / 13, 0.10), (0.006, 0.05, 0.11), M_CAB)
    # shelves + products (shown through the glass; they sit IN FRONT of the inner panel, in a shallow tray in front of the carcass)
    gl = []
    for i in range(NDOOR):
        yc = -WID / 2 + 0.05 + (i + 0.5) * door_w
        for k in range(5):
            zs = z0 + 0.02 + k * (z1 - z0) / 5
            if products:
                n = 6; kind = rnd.randrange(3); m = PROD[rnd.randrange(len(PROD))]
                for j in range(n):
                    yy = yc - door_w / 2 + 0.06 + j * (door_w - 0.12) / (n - 1)
                    bottle(mb, D - 0.08, yy, zs + 0.012, m, kind)
                    bottle(mb, D - 0.22, yy, zs + 0.012, m, kind)
            mb.box((D - 0.18, yc, zs), (0.36, door_w - 0.04, 0.012), M_SHELF)
        # door: frame + glass + handle
        mb.box((D + 0.06, yc, (z0 + z1) / 2), (0.03, door_w - 0.02, 0.035), M_FRAME)
        for sgn in (-1, 1): mb.box((D + 0.06, yc + sgn * (door_w / 2 - 0.025), (z0 + z1) / 2), (0.03, 0.03, z1 - z0 - 0.02), M_FRAME)
        for zz in (z0 + 0.02, z1 - 0.02): mb.box((D + 0.06, yc, zz), (0.03, door_w - 0.02, 0.035), M_FRAME)
        hy = yc + door_w / 2 - 0.07
        mb.cyl((D + 0.115, hy, (z0 + z1) / 2), 0.012, 0.75, M_CHROME, 10)
        for zz in ((z0 + z1) / 2 - 0.33, (z0 + z1) / 2 + 0.33): mb.box((D + 0.093, hy, zz), (0.04, 0.02, 0.02), M_CHROME)
        gl.append(yc)
    # interior cavity: the products need room -> cut a recess: inner back panel at D-0.40, inner side/top/bottom walls
    mb.box((D - 0.40, 0, (z0 + z1) / 2), (0.01, WID - 0.06, z1 - z0), M_IN)
    # back: coil + panel details (seen in the gap)
    mb.box((-0.005, 0, HT / 2), (0.01, WID - 0.1, HT - 0.2), M_BACK)
    for k in range(9): mb.box((-0.0105, 0, 0.45 + k * 0.13), (0.001, WID - 0.3, 0.012), M_COIL)   # flush coil strips (no relief into the gap)
    o = mb.done(name, coll)
    # carve the recess so products are not inside the carcass: boolean-free -> carcass built hollow instead
    g = MB()
    for yc in gl:
        g.box((D + 0.06, yc, (z0 + z1) / 2), (0.006, door_w - 0.06, z1 - z0 - 0.06), glass_mat())
    go = g.done(name + "_Glass", coll); go.parent = o
    return o
# the carcass box would hide the products: build carcass as 5 panels instead of a solid box
def make_cooler_hollow(name, coll, seed, products=True):
    o = make_cooler(name, coll, seed, products)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    # remove the first cube (carcass, 8 verts -> its 6 faces) and replace by panels
    cube = [f for f in bm.faces if all(v.index < 8 for v in f.verts)]
    bmesh.ops.delete(bm, geom=list({v for f in cube for v in f.verts}), context='VERTS')
    bm.to_mesh(o.data); bm.free()
    mb = MB(); z0, z1 = 0.22, 1.92
    mb.box((D / 2, -WID / 2 + 0.02, HT / 2), (D, 0.04, HT), M_CAB); mb.box((D / 2, WID / 2 - 0.02, HT / 2), (D, 0.04, HT), M_CAB)
    mb.box((D / 2 + 0.01, 0, 0.11), (D - 0.06, WID - 0.081, 0.22), M_CAB)
    mb.box((D / 2 + 0.01, 0, (z1 + HT) / 2), (D - 0.06, WID - 0.081, HT - z1), M_CAB)
    mb.box((0.02, 0, HT / 2 - 0.001), (0.04, WID - 0.081, HT - 0.004), M_CAB)
    for zz in (z0 - 0.002, z1 + 0.002): mb.box((D - 0.2, 0, zz), (0.4, WID - 0.06, 0.004), M_IN)
    p = mb.done(name + "_Shell", coll); p.parent = o
    return o

WALL_X = -10.75; GAP = 0.48
BACK_X = WALL_X + GAP
units = {}
for nm, yc, sd in (("CoolerHero", 0.0, 1), ("CoolerN1", 2.02, 2), ("CoolerN2", -2.02, 3)):
    u = make_cooler_hollow(nm, C09, sd); u.location = (BACK_X, yc, 0); units[nm] = u
# condensing unit + fan on top of the hero unit (back-left corner, +Y end); the worker walks on the free -Y part
cu = MB()
cu.box((0.28, 0, 0.22), (0.5, 0.62, 0.44), M_CAB)
cu.box((0.30, 0, 0.22), (0.02, 0.5, 0.36), M_GRILLE)                              # dark plate deep inside: the fan reads against it
for zz in (0.03, 0.41): cu.box((0.54, 0, zz), (0.03, 0.56, 0.04), M_CAB)           # open grille frame
for yy in (-0.26, 0.26): cu.box((0.546, yy, 0.22), (0.03, 0.04, 0.36), M_CAB)
for k in range(7): cu.box((0.552, -0.18 + k * 0.06, 0.22), (0.006, 0.006, 0.34), M_CHROME)   # thin guard bars
cuo = cu.done("CondUnit", C09); cuo.parent = units["CoolerHero"]; cuo.location = (0.0, 0.62, HT)
fan = MB()
fan.cyl((0, 0, 0), 0.03, 0.03, M_CHROME, 12, axis='X')
for k in range(5):
    a = k * 2 * math.pi / 5
    bm = fan.bm; r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r["verts"]:
        v.co = Vector((v.co.x * 0.006, v.co.y * 0.07, v.co.z * 0.13 + 0.08))
        v.co = Matrix.Rotation(a, 3, 'X') @ (Matrix.Rotation(R(25), 3, 'Z') @ v.co)
    mi = fan._mi(M_FAN)
    for f in {f for v in r["verts"] for f in v.link_faces}: f.material_index = mi
fo = fan.done("CondFan", C09); fo.parent = cuo; fo.location = (0.52, 0, 0.22); fo.rotation_mode = 'XYZ'
# boxes stored on top of the neighbour units (why a worker climbs up there)
M_CARD = mat("Cardboard", (0.62, 0.45, 0.28), 0.6)
for i, (yy, s) in enumerate(((2.3, 0.45), (1.7, 0.4), (-2.78, 0.42))):
    b = MB(); b.box((0, 0, s / 2), (s * 1.2, s, s), M_CARD); b.box((0, 0, s + 0.002), (s * 1.2, 0.05, 0.004), mat("Tape", (0.75, 0.6, 0.4), 0.3))
    bo = b.done("TopBox%d" % i, C09); bo.location = (BACK_X + 0.42, yy, HT); bo.rotation_euler.z = R(random.uniform(-8, 8))
# 2019 debris: flattened boxes, a tipped carton, floor marks where the neighbours stood
for i in range(7):
    b = MB(); w = random.uniform(0.35, 0.7); b.box((0, 0, 0.006), (w, w * 0.7, 0.012), M_CARD)
    bo = b.done("Debris%d" % i, PR); bo.location = (random.uniform(-8.8, -5.0), random.uniform(-3.5, 3.5), 0); bo.rotation_euler.z = random.uniform(0, 6.3)
    if abs(bo.location.y) < 0.9: bo.location.y += 1.6 * (1 if bo.location.y >= 0 else -1)
for nm in ("CoolerN1", "CoolerN2"):
    b = MB(); b.box((0, 0, 0.001), (0.88, 2.0, 0.002), mat("FloorMark", (0.55, 0.55, 0.52), 0.7))
    mo = b.done(nm + "_Mark", PR); mo.location = (BACK_X + D / 2, units[nm].location.y, 0)
for o in PR.objects: o.hide_render = True; o.hide_viewport = True

# ---------------------------------------------------------------- skeleton (CC-BY Ruslan Gadzhiev): clean cream bone, standing wedged in the gap
before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=MODELS + "/skeleton.glb")
new = [o for o in bpy.data.objects if o not in before]; meshes = [o for o in new if o.type == 'MESH']
for o in meshes:
    M = o.matrix_world.copy(); o.parent = None; o.matrix_world = M
bpy.ops.object.select_all(action='DESELECT')
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1: bpy.ops.object.join()
sk = bpy.context.view_layer.objects.active; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for o in new:
    if o != sk and o.name in bpy.data.objects: bpy.data.objects.remove(o, do_unlink=True)
sk.name = "Skeleton"
for c in list(sk.users_collection): c.objects.unlink(sk)
PR.objects.link(sk)
vs = [v.co for v in sk.data.vertices]; mn = Vector([min(v[i] for v in vs) for i in range(3)]); mx = Vector([max(v[i] for v in vs) for i in range(3)])
print("SKEL dims", tuple(round(x, 3) for x in mx - mn))
s = 1.72 / (mx.z - mn.z)
sk.data.transform(Matrix.Translation(-Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))))
sk.data.transform(Matrix.Scale(s, 4))
# which way does it face? the skull's face is on the side where the jaw sticks out: front = side with more verts at head height
top = [v.co for v in sk.data.vertices if v.co.z > 1.55]
yc = sum(v.y for v in top) / len(top); xc = sum(v.x for v in top) / len(top)
print("SKEL head centroid", round(xc, 3), round(yc, 3))
sm = mat("Bone", (0.93, 0.88, 0.76), 0.45); sk.data.materials.clear(); sk.data.materials.append(sm)
for p in sk.data.polygons: p.use_smooth = True
sk.hide_render = True; sk.hide_viewport = True
bpy.ops.wm.save_as_mainfile(filepath=BUILD + "/sets.blend")
print("SETS saved")
