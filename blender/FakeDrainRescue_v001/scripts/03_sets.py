"""Sets: storm drain street (dirty + clean states), culvert, houses, garbage truck with the logo, complaints office, props.
blender -b work/dressed.blend --python 03_sets.py -- work/sets.blend"""
import bpy, bmesh, sys, math, random
from mathutils import Vector, Matrix
exec(open("/home/user/Muhammed/blender/FakeDrainRescue_v001/scripts/fdr_lib.py").read())
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; random.seed(7); R_ = math.radians
for o in bpy.data.objects:
    if o.type == 'ARMATURE': o.location = (0, 0, -50)   # parked below the world until animated
# ---------------------------------------------------------------- materials
CONC = append_ph_mat("brushed_concrete/brushed_concrete_1k.blend", "brushed_concrete")
CONC2 = append_ph_mat("concrete/concrete_1k.blend", "concrete")
ASPH = append_ph_mat("asphalt_02/asphalt_02_1k.blend", "asphalt_02")
for m in (CONC, CONC2, ASPH):   # brighten / clean the scans (animated look)
    P = m.node_tree.nodes.get("Principled BSDF")
    for l in list(P.inputs["Base Color"].links):
        mx = m.node_tree.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        mx.inputs['B'].default_value = (1.35, 1.33, 1.3, 1) if m is not ASPH else (0.8, 0.8, 0.85, 1)
        m.node_tree.links.new(l.from_socket, mx.inputs['A']); m.node_tree.links.new(mx.outputs['Result'], P.inputs["Base Color"])
GRASS = mat("Grass", (0.22, 0.5, 0.12), 0.8, sheen=0.4)
WDIRTY = mat("WaterMurky", (0.20, 0.17, 0.08), 0.22, spec=0.1)
WCLEAN = mat("WaterClean", (0.10, 0.17, 0.14), 0.07, spec=0.35)   # director P1: murky green-grey with reflections, not pool cyan
for m in (WDIRTY, WCLEAN):   # gentle ripple bump
    nt = m.node_tree; P = nt.nodes["Principled BSDF"]; nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.08; nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], P.inputs["Normal"])
PIPEM = mat("PipeInside", (0.32, 0.31, 0.29), 0.7)
# ---------------------------------------------------------------- drain channel (inner x -1.6..1.6, floor z -1.9, y -14..40)
Y0, Y1 = -14.0, 40.0; YC = (Y0 + Y1) / 2; L = Y1 - Y0
box("Drain_WallL", (0.3, L, 1.87), (-1.75, YC, -0.965), CONC, "Drain")
box("Drain_WallR", (0.3, L, 1.87), (1.75, YC, -0.965), CONC, "Drain")
box("Drain_Floor", (3.8, L, 0.1), (0, YC, -1.95), CONC, "Drain")
# end wall with the culvert hole + pipe
ew = box("Drain_EndWall", (3.8, 0.4, 1.95), (0, Y0 - 0.2, -0.95), CONC, "Drain")
cut = bpy.data.objects.new("cut", bpy.data.meshes.new("cut")); bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=0.8, radius2=0.8, depth=2.0); bm.to_mesh(cut.data); bm.free()
sc.collection.objects.link(cut); cut.location = (0, Y0, -1.0); cut.rotation_euler = (R_(90), 0, 0)
bo = ew.modifiers.new("hole", 'BOOLEAN'); bo.object = cut; bo.operation = 'DIFFERENCE'
bpy.context.view_layer.objects.active = ew
with bpy.context.temp_override(object=ew, active_object=ew): bpy.ops.object.modifier_apply(modifier="hole")
bpy.data.objects.remove(cut)
pm = bpy.data.meshes.new("Culvert_Pipe"); bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=0.8, radius2=0.8, depth=8.0)
bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(pm); bm.free()
pipe = bpy.data.objects.new("Culvert_Pipe", pm); coll("Drain").objects.link(pipe); pipe.location = (0, Y0 - 4.0, -1.0); pipe.rotation_euler = (R_(90), 0, 0)
pm.materials.append(PIPEM); sol = pipe.modifiers.new("t", 'SOLIDIFY'); sol.thickness = 0.12; sol.offset = 1
for p in pm.polygons: p.use_smooth = True
# rim ring at the pipe mouth
bpy.ops.mesh.primitive_torus_add(major_radius=0.86, minor_radius=0.07, major_segments=48, minor_segments=10, location=(0, Y0 + 0.02, -1.0), rotation=(R_(90), 0, 0))
rim = bpy.context.object; rim.name = "Culvert_Rim"; rim.data.materials.append(mat("PipeRim", (0.55, 0.54, 0.5), 0.6)); link(rim, "Drain")
# water: murky (dirty state, z -0.75) and clean (z -1.55)
plane("Water_Murky", 3.22, L + 9, (0, YC - 4.5, -0.75), WDIRTY, "Water")
plane("Water_Clean", 3.22, L + 9, (0, YC - 4.5, -1.45), WCLEAN, "Water")
# ---------------------------------------------------------------- ground
def gp(name, x0, x1, y0, y1, m, z=0.0, cname="Ground"):
    o = plane(name, x1 - x0, y1 - y0, ((x0 + x1) / 2, (y0 + y1) / 2, z), m, cname)
    # UV scaled by size so textures tile at ~2 m
    uv = o.data.uv_layers[0]
    for lp in o.data.loops:
        co = o.data.vertices[lp.vertex_index].co; uv.data[lp.index].uv = ((co.x + o.location.x) / 2.5, (co.y + o.location.y) / 2.5)
    return o
gp("G_Coping_R", 1.6, 4.6, -60, 70, CONC2); gp("G_Street", 4.6, 13.0, -60, 70, ASPH, -0.1)
box("G_Curb_R", (0.25, 130, 0.12), (4.6, 5, -0.04), CONC2, "Ground"); box("G_Curb_F", (0.25, 130, 0.12), (13.0, 5, -0.04), CONC2, "Ground")
gp("G_FarWalk", 13.0, 15.5, -60, 70, CONC2); gp("G_FarGrass", 15.5, 60, -60, 70, GRASS)
gp("G_Coping_L", -2.6, -1.6, -60, 70, CONC2); gp("G_Grass_L", -60, -2.6, -60, 70, GRASS)
gp("G_EndSlab", -1.6, 1.6, -60, Y0, CONC2); gp("G_FarEnd", -1.6, 1.6, Y1, 70, CONC2)
# ---------------------------------------------------------------- dressing: fence, shrubs, trees, lamps, hydrant, houses
fence_src = append_ph("modular_chainlink_fence/modular_chainlink_fence_1k.blend", ["modular_chainlink_fence_double", "modular_chainlink_fence_post"], "BG")
fl = fence_src[0] if "double" in fence_src[0].name else fence_src[1]; fpost = [o for o in fence_src if o is not fl][0]
bpy.context.view_layer.update(); fw = fl.dimensions.x if fl.dimensions.x > fl.dimensions.y else fl.dimensions.y
print("FENCE dims", tuple(round(v, 2) for v in fl.dimensions), tuple(round(v, 2) for v in fpost.dimensions))
fl.location = (-5.5, -50, 0); fl.rotation_euler = (0, 0, R_(90) if fl.dimensions.x > fl.dimensions.y else 0)
y = -50 + fw
while y < 66:
    c = fl.copy(); c.location = (-5.5, y, 0); coll("BG").objects.link(c); y += fw
fpost.location = (-5.5, -50 - fw / 2, 0)
shr = append_ph("shrub_02/shrub_02_1k.blend", ["shrub_02_a_LOD0", "shrub_02_b_LOD0", "shrub_02_c_LOD0"], "BG")
tre = append_ph("tree_small_02/tree_small_02_1k.blend", ["tree_small_02_LOD1"], "BG")
for o in shr + tre: o.location = (0, 0, -60)
for i in range(26):
    s = random.choice(shr).copy(); coll("BG").objects.link(s); s.location = (-4.6 + random.uniform(-0.4, 0.3), -40 + i * 4.0 + random.uniform(-1, 1), 0)
    s.rotation_euler = (0, 0, random.uniform(0, 6.28)); s.scale = [random.uniform(0.8, 1.3)] * 3
for i in range(9):
    t = tre[0].copy(); coll("BG").objects.link(t); t.location = (-8.0 + random.uniform(-1, 1), -40 + i * 12 + random.uniform(-2, 2), 0)
    t.rotation_euler = (0, 0, random.uniform(0, 6.28)); t.scale = [random.uniform(1.0, 1.4)] * 3
for i in range(6):
    t = tre[0].copy(); coll("BG").objects.link(t); t.location = (17.5 + random.uniform(-1, 1), -36 + i * 16, 0); t.rotation_euler = (0, 0, random.uniform(0, 6.28))
lamp = append_ph("street_lamp_01/street_lamp_01_1k.blend", ["street_lamp_01"], "BG")[0]
lamp.location = (4.35, -6, 0); lamp.rotation_euler = (0, 0, R_(180))
for i, yy in enumerate((14, 34, 54)):
    c = lamp.copy(); coll("BG").objects.link(c); c.location = (4.35, yy, 0)
hyd = append_ph("fire_hydrant/fire_hydrant_1k.blend", ["fire_hydrant"], "BG")[0]; hyd.location = (4.1, 9.0, 0)
WALLC = [(0.95, 0.93, 0.86), (0.98, 0.85, 0.7), (0.8, 0.9, 0.95), (0.95, 0.95, 0.95), (0.9, 0.8, 0.85)]
ROOFC = [(0.6, 0.18, 0.12), (0.3, 0.32, 0.36), (0.45, 0.25, 0.15)]
GLASS = mat("WinGlass", (0.45, 0.62, 0.78), 0.12, spec=0.3); FRAME = mat("WinFrame", (0.96, 0.96, 0.95), 0.4)
DOOR = mat("Door", (0.35, 0.2, 0.12), 0.5)
def house(name, x, y, w, d, h, face):
    """face = +1: windows on the -X wall (house on the +X side looks at the drain); -1 the other way"""
    wm = mat(name + "_wall", random.choice(WALLC), 0.7); rm = mat(name + "_roof", random.choice(ROOFC), 0.6)
    box(name, (d, w, h), (x, y, h / 2), wm, "Houses", bevel=0.02)
    # gable roof (prism along y)
    me = bpy.data.meshes.new(name + "_roof"); bm = bmesh.new()
    hw = d / 2 + 0.35; rh = 1.6; yy = w / 2 + 0.3
    vs = [bm.verts.new(v) for v in ((-hw, -yy, 0), (hw, -yy, 0), (0, -yy, rh), (-hw, yy, 0), (hw, yy, 0), (0, yy, rh))]
    for f in ((0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)): bm.faces.new([vs[i] for i in f])
    bm.to_mesh(me); bm.free(); r = bpy.data.objects.new(name + "_roof", me); coll("Houses").objects.link(r); r.location = (x, y, h); me.materials.append(rm)
    xs = x - face * (d / 2 + 0.01)
    for k in range(int(w // 2.2)):
        yy = y - w / 2 + 1.1 + k * 2.2
        for zz in ([1.5, 4.2] if h > 5 else [1.5]):
            if k == 1 and zz == 1.5:
                box(name + "_door%d" % k, (0.08, 1.0, 2.1), (xs, yy, 1.05), DOOR, "Houses"); continue
            box(name + "_wf%d_%d" % (k, zz), (0.08, 1.2, 1.3), (xs, yy, zz + 0.2), FRAME, "Houses")
            box(name + "_wg%d_%d" % (k, zz), (0.1, 1.0, 1.1), (xs - face * 0.02, yy, zz + 0.2), GLASS, "Houses")
for i in range(8):
    house("HouseR%d" % i, 20.5, -30 + i * 12, 8.8, 7, random.choice([3.2, 6.0]), +1)
    house("HouseL%d" % i, -14.0, -26 + i * 12, 8.8, 7, random.choice([3.2, 6.0]), -1)
# ---------------------------------------------------------------- trash (dirty state): bags, bottles, cans, tires, boxes floating
bag_ph = append_ph("trashbag/trashbag_1k.blend", ["trashbag"], "Lib")[0]
bpy.context.view_layer.update(); print("BAG dims", tuple(round(v, 2) for v in bag_ph.dimensions))
bag_sk = import_glb("Lib_Bag2", HERE + "assets/trashbag.glb", 0.75, 2, "Lib")
bottle = import_glb("Lib_Bottle", HERE + "assets/bottle.glb", 0.28, 2, "Lib")
tire = import_glb("Lib_Tire", HERE + "assets/tire.glb", 0.65, 0, "Lib")
for o in (bag_ph, bag_sk, bottle, tire): o.location = (0, 0, -80)
s_ = 0.8 / max(bag_ph.dimensions); bag_ph.data.transform(Matrix.Scale(s_, 4)); bag_ph.scale = (1, 1, 1)
BAGC = [(0.03, 0.03, 0.035), (0.03, 0.03, 0.035), (0.1, 0.25, 0.75), (0.75, 0.08, 0.08), (0.9, 0.35, 0.65), (0.1, 0.55, 0.2), (0.85, 0.85, 0.85)]
bag_mats = [mat("Bag_%d" % i, c, 0.28, spec=0.4, sheen=0.0) for i, c in enumerate(BAGC)]
can_m = [mat("Can_%d" % i, c, 0.3, metal=0.7) for i, c in enumerate([(0.85, 0.1, 0.1), (0.7, 0.72, 0.75), (0.1, 0.3, 0.8), (0.95, 0.75, 0.1)])]
box_m = mat("Cardboard", (0.62, 0.42, 0.22), 0.8)
bottle_m = mat("BottlePlastic", (0.55, 0.8, 0.95), 0.15, spec=0.4)
bottle.data.materials.clear(); bottle.data.materials.append(bottle_m)
cmesh = bpy.data.meshes.new("Lib_Can"); bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=0.033, radius2=0.033, depth=0.12); bm.to_mesh(cmesh); bm.free()
bmesh_box = bpy.data.meshes.new("Lib_Box"); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts: v.co = Vector((v.co.x * 0.45, v.co.y * 0.35, v.co.z * 0.3))
bm.to_mesh(bmesh_box); bm.free(); bmesh_box.materials.append(box_m)
CLEAR = [((-0.35, 16.0), (-0.35, 22.5), 0.75), ((0.55, 22.0), (0.55, 28.0), 0.75), ((0.0, -14.0), (0.0, -10.0), 1.0)]  # wading corridors (a, b, radius)
def clear(x, y, rr=0.0):
    for (ax, ay), (bx, by), r in CLEAR:
        a = Vector((ax, ay)); b = Vector((bx, by)); p = Vector((x, y)); t = max(0, min(1, (p - a).dot(b - a) / (b - a).length_squared))
        if (p - (a + (b - a) * t)).length < r + rr: return False
    return True
placed = []
WZ = -0.75; n = 0
for i in range(40000):
    if n >= 900: break
    x = random.uniform(-1.4, 1.4); y = random.uniform(-13.6, 32)
    kind = random.choices(["bag", "bag2", "bottle", "can", "tire", "box"], [46, 22, 12, 9, 4, 7])[0]
    r = {"bag": 0.38, "bag2": 0.33, "bottle": 0.12, "can": 0.07, "tire": 0.36, "box": 0.3}[kind]
    if not clear(x, y, r): continue
    if abs(x) + r > 1.58: continue
    if any((Vector((x, y)) - p).length < r + pr - 0.2 for p, pr in placed): continue
    placed.append((Vector((x, y)), r)); n += 1
    if kind in ("bag", "bag2"):
        src = bag_ph if kind == "bag" else bag_sk
        o = bpy.data.objects.new("T_%s_%d" % (kind, n), src.data); o.material_slots and None
        o.data = src.data.copy() if False else src.data
        o.location = (x, y, WZ - random.uniform(0.22, 0.34)); o.rotation_euler = (random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4), random.uniform(0, 6.28))
        o.scale = [random.uniform(0.85, 1.15)] * 3
        o.active_material = None
    elif kind == "bottle":
        o = bpy.data.objects.new("T_bottle_%d" % n, bottle.data); o.location = (x, y, WZ - 0.03); o.rotation_euler = (R_(90), 0, random.uniform(0, 6.28))
    elif kind == "can":
        o = bpy.data.objects.new("T_can_%d" % n, cmesh); o.location = (x, y, WZ + 0.0); o.rotation_euler = (R_(90), 0, random.uniform(0, 6.28))
    elif kind == "tire":
        o = bpy.data.objects.new("T_tire_%d" % n, tire.data); o.location = (x, y, WZ - 0.30); o.rotation_euler = (R_(random.uniform(70, 110)), 0, random.uniform(0, 6.28))
    else:
        o = bpy.data.objects.new("T_box_%d" % n, bmesh_box); o.location = (x, y, WZ + 0.02); o.rotation_euler = (random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2), random.uniform(0, 6.28))
    coll("TrashDirty").objects.link(o)
    if kind in ("bag", "bag2"):
        o.material_slots[0].link = 'OBJECT'; o.material_slots[0].material = random.choice(bag_mats)
    if kind == "can":
        if not o.material_slots: cmesh.materials.append(can_m[0])
        o.material_slots[0].link = 'OBJECT'; o.material_slots[0].material = random.choice(can_m)
print("TRASH", n)
# clean state: bag rows on the sidewalk (x 2.2..3.4) and on the grass edge
n2 = 0
for i in range(46):
    side = 1 if i < 30 else -1
    yy = (2.0 + (i % 30) * 0.62) if side > 0 else (6.0 + (i - 30) * 0.7)
    for row in (0, 1) if side > 0 else (0,):
        o = bpy.data.objects.new("C_bag_%d_%d" % (i, row), bag_ph.data); coll("TrashClean").objects.link(o)
        o.location = (side * (2.35 + row * 0.62), yy + row * 0.3 + random.uniform(-0.08, 0.08), 0.0); o.rotation_euler = (0, 0, random.uniform(0, 6.28))
        o.scale = [random.uniform(0.85, 1.1)] * 3
        o.material_slots[0].link = 'OBJECT'; o.material_slots[0].material = random.choice(bag_mats); n2 += 1
print("CLEANBAGS", n2)
# ---------------------------------------------------------------- garbage truck + logo (white logo on the green side box)
truck = import_glb("Truck", HERE + "assets/truck.glb", 8.6, 1, "Truck")
bpy.context.view_layer.update(); print("TRUCK dims", tuple(round(v, 2) for v in truck.dimensions))
truck.location = (8.0, 24.0, -0.1); truck.rotation_euler = (0, 0, 0)
_oi = [i for i, m in enumerate(truck.data.materials) if m.name.startswith("Outline")]
bm = bmesh.new(); bm.from_mesh(truck.data); bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in _oi], context='FACES'); bm.to_mesh(truck.data); bm.free()
for m in truck.data.materials:
    P = m.node_tree.nodes.get("Principled BSDF") if m.use_nodes else None
    if not P: continue
    if m.name == "MainBody": P.inputs["Base Color"].default_value = (0.08, 0.42, 0.14, 1)
    if m.name == "Silver": P.inputs["Base Color"].default_value = (0.75, 0.77, 0.8, 1); P.inputs["Metallic"].default_value = 0.6
    if m.name == "material": P.inputs["Base Color"].default_value = (0.92, 0.92, 0.9, 1)
for m in truck.data.materials: print("TRUCKMAT", m.name, [tuple(round(c, 2) for c in m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value) if m.use_nodes and "Principled BSDF" in m.node_tree.nodes else None])
# ---------------------------------------------------------------- props: torch, phone (+screen), forms
torch = append_ph("small_plastic_torch/small_plastic_torch_1k.blend", ["small_plastic_torch"], "Props")[0]
bpy.context.view_layer.update(); print("TORCH dims", tuple(round(v, 3) for v in torch.dimensions))
phone = import_glb("Phone", HERE + "assets/phone.glb", 0.15, 2, "Props")
phone.data.materials.clear(); phone.data.materials.append(mat("PhoneBody", (0.08, 0.08, 0.1), 0.3, metal=0.3))
bpy.context.view_layer.update(); print("PHONE dims", tuple(round(v, 3) for v in phone.dimensions))
scr = plane("Phone_Screen", 0.064, 0.138, (0, 0, 0), img_mat("PhoneScreenM", HERE + "assets/tex/phone_screen.png", 0.3, emit=1.2), "Props")
# office (offset +80 x): floor, walls, desk, chair, forms, cabinet, poster with trash photos, plant
OX = 80.0
plane("Off_Floor", 8, 8, (OX, 0, 0), mat("OffFloor", (0.62, 0.45, 0.3), 0.5), "Office")
plane("Off_Ceil", 8, 8, (OX, 0, 3.0), mat("OffCeil", (0.95, 0.95, 0.95), 0.8), "Office", rot=(R_(180), 0, 0))
WALLM = mat("OffWall", (0.72, 0.84, 0.92), 0.8)
box("Off_WallB", (8, 0.1, 3), (OX, 3.0, 1.5), WALLM, "Office"); box("Off_WallL", (0.1, 8, 3), (OX - 3.5, 0, 1.5), WALLM, "Office")
box("Off_WallR", (0.1, 8, 3), (OX + 3.5, 0, 1.5), WALLM, "Office"); box("Off_WallF", (8, 0.1, 3), (OX, -4.0, 1.5), WALLM, "Office")
box("Off_Skirt", (7.0, 0.03, 0.12), (OX, 2.94, 0.06), mat("Skirt", (0.95, 0.95, 0.95), 0.5), "Office")
desk = append_ph("metal_office_desk/metal_office_desk_1k.blend", [n for n in ["metal_office_desk", "metal_office_desk_drawer_01", "metal_office_desk_drawer_02", "metal_office_desk_drawer_03", "metal_office_desk_drawer_04", "metal_office_desk_drawer_05", "metal_office_desk_drawer_06", "metal_office_desk_tray_01", "metal_office_desk_tray_02"]], "Office")
dk = next(o for o in desk if o.name.startswith("metal_office_desk") and "drawer" not in o.name and "tray" not in o.name)
bpy.context.view_layer.update(); print("DESK dims", tuple(round(v, 2) for v in dk.dimensions), tuple(round(v, 2) for v in dk.location))
for o in desk:
    if o.parent is None: o.location += Vector((OX, 1.45, 0))
# office stool sized to the seated clerk (seat top 0.45 under his pelvis, no backrest: the PH chair crossed his thighs and back)
STM = mat("StoolBlack", (0.08, 0.08, 0.09), 0.4); STL = mat("StoolMetal", (0.7, 0.72, 0.75), 0.3, metal=0.8)
box("Off_StoolSeat", (0.44, 0.40, 0.06), (OX, 2.56, 0.36), STM, "Office", bevel=0.02)
for dx in (-0.17, 0.17):
    for dy in (-0.15, 0.15):
        box("Off_StoolLeg", (0.03, 0.03, 0.33), (OX + dx, 2.56 + dy, 0.165), STL, "Office")
box("Off_Cabinet", (0.5, 0.6, 1.3), (OX + 2.6, 2.5, 0.65), mat("CabGrey", (0.6, 0.62, 0.65), 0.4, metal=0.4), "Office", bevel=0.01)
box("Off_Board", (1.6, 0.04, 1.0), (OX - 1.4, 2.93, 1.7), mat("Cork", (0.7, 0.5, 0.3), 0.8), "Office")
for k in range(6):
    p = plane("Off_Pin%d" % k, 0.3, 0.42, (OX - 2.0 + (k % 3) * 0.55, 2.9, 1.95 - (k // 3) * 0.5), img_mat("FormPin%d" % k, HERE + "assets/tex/form_%d.png" % (k % 3), 0.6), "Office", rot=(R_(90), R_(random.uniform(-6, 6)), 0))
pl = random.choice(shr).copy(); coll("Office").objects.link(pl); pl.location = (OX + 2.8, 1.2, 0); pl.scale = (0.5, 0.5, 0.5)
FORMM = [img_mat("FormM%d" % k, HERE + "assets/tex/form_%d.png" % k, 0.6) for k in range(3)]
print("SETS done")
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
