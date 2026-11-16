"""B20 SafetyPin sets. blender -b --python 02_sets.py
SetWork x=0 (1840s workshop), SetStore x=40 (pin warehouse), SetPark x=80 (park bench). Saves work/sets.blend"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
exec(open("/home/user/Muhammed/blender/SafetyPin_v001/scripts/lib.py").read())
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
exec(open(V + "scripts/props.py").read())
random.seed(20)

def wood_mat(name, base, dark, scale=6.0, rough=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1, scale, 1)
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 3.0; wv.inputs["Distortion"].default_value = 4.0
    wv.inputs["Detail"].default_value = 2.0
    br = nt.nodes.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 1.0
    br.inputs["Color1"].default_value = (1, 1, 1, 1); br.inputs["Color2"].default_value = (0.85, 0.85, 0.85, 1); br.inputs["Mortar"].default_value = (0.4, 0.4, 0.4, 1)
    br.inputs["Mortar Size"].default_value = 0.004; br.offset = 0.5; br.inputs["Brick Width"].default_value = 1.6; br.inputs["Row Height"].default_value = 0.16
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (*dark, 1); cr.color_ramp.elements[1].color = (*base, 1)
    mu = nt.nodes.new("ShaderNodeMix"); mu.data_type = 'RGBA'; mu.blend_type = 'MULTIPLY'; mu.inputs['Factor'].default_value = 1.0
    nt.links.new(tc.outputs["Object"], mp.inputs[0]); nt.links.new(mp.outputs[0], wv.inputs[0]); nt.links.new(wv.outputs["Fac"], cr.inputs[0])
    nt.links.new(tc.outputs["Object"], br.inputs[0])
    nt.links.new(cr.outputs[0], mu.inputs['A']); nt.links.new(br.outputs["Color"], mu.inputs['B']); nt.links.new(mu.outputs['Result'], P.inputs["Base Color"])
    P.inputs["Roughness"].default_value = rough
    return m

# ============================================================ SetWork (x = 0)
cW = col("SetWork")
floor = plane("WorkFloor", cW, (0, 0, 0), (7, 7), wood_mat("FloorPlanks", (0.50, 0.32, 0.18), (0.36, 0.22, 0.12)))
plaster = mat("Plaster", (0.86, 0.77, 0.60), 0.8)
woodpanel = wood_mat("Wainscot", (0.42, 0.25, 0.13), (0.30, 0.17, 0.09), scale=2)
for nm, loc, size, rot in (("WallBack", (0, 2.2, 1.6), (5.4, 3.2), (R_(90), 0, 0)),
                           ("WallLeft", (-2.6, -0.6, 1.6), (6.0, 3.2), (R_(90), 0, R_(90))),
                           ("WallRight", (2.6, -0.6, 1.6), (6.0, 3.2), (R_(90), 0, R_(90)))):
    plane(nm, cW, loc, size, plaster, rot)
box("WainBack", cW, (0, 2.18, 0.45), (5.4, 0.04, 0.9), woodpanel, 0.004)
box("WainLeft", cW, (-2.58, -0.6, 0.45), (0.04, 6.0, 0.9), woodpanel, 0.004)
box("WainRight", cW, (2.58, -0.6, 0.45), (0.04, 6.0, 0.9), woodpanel, 0.004)
box("RailBack", cW, (0, 2.16, 0.92), (5.4, 0.06, 0.05), woodpanel, 0.01)
# window in the back wall (daylight panes, never a black void)
frame_m = mat("WinFrame", (0.93, 0.92, 0.88), 0.5)
sky_m = mat("WinSky", (0.70, 0.86, 1.0), 0.5, emit=((0.70, 0.86, 1.0), 2.2))
wx, wz, ww, wh = 0.35, 1.75, 1.2, 1.3
plane("WinPane", cW, (wx, 2.195, wz), (ww, wh), sky_m, (R_(90), 0, 0))
for i in range(3):
    box("WinMullV%d" % i, cW, (wx - ww / 2 + i * ww / 2, 2.15, wz), (0.05, 0.08, wh + 0.05), frame_m, 0.005)
for j in range(3):
    box("WinMullH%d" % j, cW, (wx, 2.15, wz - wh / 2 + j * wh / 2), (ww + 0.05, 0.08, 0.05), frame_m, 0.005)
box("WinSill", cW, (wx, 2.10, wz - wh / 2 - 0.04), (ww + 0.2, 0.18, 0.04), frame_m, 0.005)
# furniture (Poly Haven CC0)
append_asset("wooden_bookshelf_worn", "Bookshelf", cW, (-1.65, 1.9, 0), 0.0, height=2.0)
append_asset("vintage_cabinet_01", "Cabinet", cW, (-2.25, -1.2, 0), R_(-90), height=2.1)
append_asset("vintage_wooden_drawer_01", "Drawer", cW, (1.75, 1.75, 0), 0.0, height=1.05)
append_asset("mantel_clock_01", "Clock", cW, (1.75, 1.75, 1.05), 0.0, height=0.36, keep=lambda o: not o.name.startswith("wdg"))
lamp2, _ = append_asset("vintage_oil_lamp", "OilLampShelf", cW, (2.2, 1.7, 1.05), 0.0, height=0.5)
# books on the shelf rows (simple coloured spines)
book_cols = [(0.55, 0.12, 0.10), (0.15, 0.25, 0.45), (0.20, 0.38, 0.20), (0.50, 0.38, 0.15), (0.35, 0.15, 0.30)]
for row, z in enumerate((0.42, 0.93, 1.44)):
    x = -2.25
    while x < -1.1:
        w = random.uniform(0.03, 0.06); h = random.uniform(0.22, 0.30)
        box("Book", cW, (x + w / 2, 1.85, z + h / 2), (w, 0.2, h), mat("Book%d" % random.randrange(5), random.choice(book_cols), 0.6), 0.003)
        x += w + 0.004
# workbench: Poly Haven table raised to 0.78 m, long side along X, in front of the inventor (he faces -Y)
bench, bobs = append_asset("WoodenTable_01", "Workbench", cW, (0, -0.45, 0), 0.0)
bench.scale = (bench.scale.x, bench.scale.y * 1.15, bench.scale.z * 0.78 / 0.55)
bpy.context.view_layer.update()
mn, mx = bounds(bobs); BENCH_TOP = mx.z; print("BENCH top", BENCH_TOP, mn, mx)
sc["bench_top"] = BENCH_TOP
for nm, x in (("StoolHunt", -0.30), ("StoolPal", 0.38)):
    append_asset("wooden_stool_01", nm, cW, (x, 0.05, 0), 0.0, height=0.46)
append_asset("wooden_stool_01", "StoolBuyer", cW, (-0.05, -1.02, 0), 0.0, height=0.46)
# bench dressing (kept clear of the working area x -0.6..0.6, y -0.15..-0.55)
append_asset("vintage_oil_lamp", "OilLamp", cW, (0.75, -0.62, BENCH_TOP), 0.0, height=0.42)
append_asset("wooden_candlestick", "Candle", cW, (-0.78, -0.66, BENCH_TOP), 0.0, height=0.2)
append_asset("pliers", "Pliers", cW, (0.52, -0.66, BENCH_TOP + 0.012), R_(70), scale=1.0)
for o in bpy.data.objects["Pliers"].children: pass
bpy.data.objects["Pliers"].rotation_euler = (R_(90), 0, R_(70))
# wire spool
spool_m = mat("SpoolWood", (0.55, 0.38, 0.20), 0.6)
bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=0.05, location=(-0.62, -0.62, BENCH_TOP + 0.04)); sp = bpy.context.object
sp.name = "Spool"; sp.rotation_euler.x = R_(90); link(sp, cW); sp.data.materials.append(steel())
for dx in (-0.027, 0.027):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.006, location=(-0.62, -0.62 + dx, BENCH_TOP + 0.045)); f_ = bpy.context.object
    f_.name = "SpoolFlange"; f_.rotation_euler.x = R_(90); link(f_, cW); f_.data.materials.append(spool_m)
# pin cushion with straight pins (B3)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=(0.42, -0.36, BENCH_TOP + 0.03)); pc = bpy.context.object
pc.name = "PinCushion"; pc.scale.z = 0.65; link(pc, cW); pc.data.materials.append(mat("Cushion", (0.75, 0.10, 0.10), 0.8))
for p in pc.data.polygons: p.use_smooth = True
for i in range(7):
    a = i * 2 * math.pi / 7
    sp_ = straight_pin("CushionPin%d" % i, cW, 0.03)
    sp_.location = (0.42 + 0.03 * math.cos(a), -0.36 + 0.03 * math.sin(a), BENCH_TOP + 0.075)
    sp_.rotation_euler = (R_(25) * math.sin(a), -R_(25) * math.cos(a), 0)
# folded cloth on the bench (B3: he pins two layers of cloth)
cloth_m = mat("Linen", (0.88, 0.84, 0.74), 0.85)
for k, (dz, dx) in enumerate(((0.002, 0.0), (0.008, 0.012))):
    c_ = box("Cloth%d" % k, cW, (0.38 + dx, -0.40, BENCH_TOP + dz), (0.26, 0.20, 0.004), cloth_m, 0.002)
    c_.rotation_euler.z = R_(-8 + 6 * k)
# hero props (positions/animation set in 03_anim)
cP = col("Props")
pin_body, pin_arm = pin_parts("HeroPin", cP, clasp=True)
proto_body, proto_arm = pin_parts("ProtoPin", cP, clasp=False)
wire, *_ = wire_morph("Wire", cP)
spin = straight_pin("StraightPin", cP, 0.036)
paper_m = img_mat("PatentPaper", SCR + "/tex/patent.png", 0.8)
note_m = img_mat("DebtNote", SCR + "/tex/debtnote.png", 0.8)
bill_m = img_mat("Banknote", SCR + "/tex/banknote.png", 0.7)
pat = plane("Patent", cP, (0, 0, 0), (0.21, 0.28), paper_m); pat.scale = (1, 1, 1)
sol = pat.modifiers.new("Solid", 'SOLIDIFY'); sol.thickness = 0.0008
note = plane("DebtNote", cP, (0, 0, 0), (0.15, 0.10), note_m)
sol = note.modifiers.new("Solid", 'SOLIDIFY'); sol.thickness = 0.0006
# banknote stack with a paper band
bills = []
for i in range(12):
    b_ = plane("Bill%d" % i, cP, (random.uniform(-0.002, 0.002), random.uniform(-0.002, 0.002), 0.0012 * i), (0.156, 0.067), bill_m)
    b_.rotation_euler.z = R_(random.uniform(-2, 2)); bills.append(b_)
stack = bpy.data.objects.new("MoneyStack", None); cP.objects.link(stack)
for b_ in bills: b_.parent = stack
band = box("MoneyBand", cP, (0, 0, 0.007), (0.03, 0.07, 0.015), mat("Band", (0.92, 0.88, 0.75), 0.7), 0.001); band.parent = stack
coin_m = mat("Coin", (0.80, 0.66, 0.36), 0.25, 1.0)
for i in range(3):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.002, location=(0, 0, 0)); co = bpy.context.object
    co.name = "Coin%d" % i; link(co, cP); co.data.materials.append(coin_m)
    bv = co.modifiers.new("Bevel", 'BEVEL'); bv.width = 0.0006; bv.segments = 2
# ============================================================ SetStore (x = 40): warehouse of boxed pins
cS = col("SetStore"); X = 40.0
plane("StoreFloor", cS, (X, 0, 0), (14, 14), wood_mat("StoreFloorM", (0.55, 0.38, 0.22), (0.40, 0.26, 0.14)))
brick = mat("Brick", (0.62, 0.34, 0.24), 0.8)
plane("StoreWallBack", cS, (X, 4.0, 2.0), (14, 4), brick, (R_(90), 0, 0))
plane("StoreWallLeft", cS, (X - 4.5, 0, 2.0), (14, 4), brick, (R_(90), 0, R_(90)))
plane("StoreWallRight", cS, (X + 4.5, 0, 2.0), (14, 4), brick, (R_(90), 0, R_(90)))
for i in range(4):
    plane("StoreWin%d" % i, cS, (X - 3 + i * 2, 3.99, 2.3), (1.0, 1.3), sky_m, (R_(90), 0, 0))
card_m = mat("Cardboard", (0.66, 0.48, 0.30), 0.85)
logo_m = img_mat("BoxLogo", BRAND + "DaKrasFilms_logo_dark.png", 0.85, alpha=True)
pin_src = bpy.data.objects.new("PinInstSrc", None); cS.objects.link(pin_src)
ib, ia = pin_parts("PinInst", cS, clasp=True)
for o in (ib, ia): o.data.bevel_resolution = 1
bpy.context.view_layer.objects.active = ib
for o in bpy.context.selected_objects: o.select_set(False)
ib.select_set(True); ia.select_set(True); bpy.data.objects["PinInst_Clasp"].select_set(True)
bpy.ops.object.convert(target='MESH'); bpy.ops.object.join()
inst = bpy.context.object; inst.name = "PinInstMesh"; inst.location = (X, -20, 0); inst.hide_render = True
def open_box(name, loc, rotz=0.0, size=(0.42, 0.32, 0.26)):
    bx, by, bz = size
    root = bpy.data.objects.new(name, None); cS.objects.link(root); root.location = loc; root.rotation_euler.z = rotz
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(bx, by, bz), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(0, 0, bz / 2), verts=bm.verts)
    top = [f for f in bm.faces if f.normal.z > 0.9]; bmesh.ops.delete(bm, geom=top, context='FACES')
    me = bpy.data.meshes.new(name + "_Box"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name + "_Box", me); cS.objects.link(o); o.parent = root; me.materials.append(card_m)
    so = o.modifiers.new("Solid", 'SOLIDIFY'); so.thickness = 0.006
    for k, (px, py, w, ax, sgn) in enumerate(((bx / 2, 0, by, 'Y', 1), (-bx / 2, 0, by, 'Y', -1), (0, by / 2, bx, 'X', -1), (0, -by / 2, bx, 'X', 1))):
        fl = plane(name + "_Flap%d" % k, cS, (0, 0, 0), (0.15 if ax == 'Y' else w, w if ax == 'Y' else 0.12), card_m)
        bm2 = bmesh.new(); bm2.from_mesh(fl.data)
        off = Vector((0.075, 0, 0)) if ax == 'Y' else Vector((0, 0.06, 0))
        if (ax == 'Y' and sgn < 0) or (ax == 'X' and sgn > 0): off = -off
        bmesh.ops.translate(bm2, vec=off, verts=bm2.verts); bm2.to_mesh(fl.data); bm2.free()
        fl.parent = root; fl.location = (px, py, bz)
        ang = R_(125) * sgn
        if ax == 'Y': fl.rotation_euler = (0, -ang if sgn > 0 else ang, 0)
        else: fl.rotation_euler = (ang, 0, 0)
        fl.rotation_euler = (0, R_(-125), 0) if k == 0 else (0, R_(125), 0) if k == 1 else (R_(125), 0, 0) if k == 2 else (R_(-125), 0, 0)
        so2 = fl.modifiers.new("Solid", 'SOLIDIFY'); so2.thickness = 0.005
    lg = plane(name + "_Logo", cS, (0, -by / 2 - 0.0045, bz * 0.48), (bx * 0.86, bx * 0.86 * 414 / 967), logo_m, (R_(90), 0, 0))
    lg.parent = root
    hp = pin_heap(name + "_Pins", cS, inst, size=(bx - 0.02, by - 0.02), z=0.0, seed=hash(name) % 7)
    hp.parent = root; hp.location = (0, 0, bz - 0.06)
    return root
BOXES = []
for r in range(3):
    for c in range(4):
        hero = (r == 0 and c in (1, 2))      # only the two front-centre boxes show the logo to camera
        BOXES.append(open_box("PinBox%d%d" % (r, c), (X - 1.0 + c * 0.62, -0.2 + r * 0.55, 0.0), R_(random.uniform(-3, 3) + (0 if hero else 180))))
for i, (dx, dy, aid) in enumerate(((-2.6, 2.6, "wooden_crate_01"), (-1.7, 2.8, "wooden_crate_02"), (1.9, 2.7, "wooden_crate_01"), (2.8, 2.4, "wooden_crate_02"))):
    append_asset(aid, "Crate%d" % i, cS, (X + dx, dy, 0), R_(random.uniform(-10, 10)), height=0.45)
    append_asset(aid, "CrateTop%d" % i, cS, (X + dx, dy, 0.45), R_(random.uniform(-10, 10)), height=0.45)
for i in range(6):   # back stacks of closed boxes with the logo
    append_asset("cardboard_box_01", "Stack%d" % i, cS, (X - 2.5 + i * 1.0, 3.4, 0), R_(random.uniform(-6, 6)), height=0.34)
# ============================================================ SetPark (x = 80)
cK = col("SetPark"); X = 80.0
grass_m = mat("Lawn", (0.32, 0.58, 0.20), 0.8)
_nt = grass_m.node_tree; _P = _nt.nodes["Principled BSDF"]          # mottled lawn: two greens by noise, light bump
_nz = _nt.nodes.new("ShaderNodeTexNoise"); _nz.inputs["Scale"].default_value = 18.0; _nz.inputs["Detail"].default_value = 6.0
_cr = _nt.nodes.new("ShaderNodeValToRGB"); _cr.color_ramp.elements[0].color = (0.22, 0.45, 0.13, 1); _cr.color_ramp.elements[1].color = (0.42, 0.66, 0.24, 1)
_nt.links.new(_nz.outputs["Fac"], _cr.inputs[0]); _nt.links.new(_cr.outputs[0], _P.inputs["Base Color"])
_bp = _nt.nodes.new("ShaderNodeBump"); _bp.inputs["Strength"].default_value = 0.3; _n2 = _nt.nodes.new("ShaderNodeTexNoise"); _n2.inputs["Scale"].default_value = 160.0
_nt.links.new(_n2.outputs["Fac"], _bp.inputs["Height"]); _nt.links.new(_bp.outputs["Normal"], _P.inputs["Normal"])
gr = plane("ParkGround", cK, (X, 0, 0), (40, 40), grass_m)
path_m = mat("Path", (0.80, 0.72, 0.58), 0.9)
pa = plane("ParkPath", cK, (X, -1.0, 0.003), (40, 1.4), path_m)
curb_m = mat("Curb", (0.62, 0.60, 0.56), 0.7)
for _y in (-0.28, -1.72):    # stone path edges
    box("PathCurb", cK, (X, _y, 0.025), (40, 0.10, 0.05), curb_m, 0.008)
benchP, bobsP = append_asset("painted_wooden_bench", "ParkBench", cK, (X, 0, 0), 0.0, height=0.89)
mnB, mxB = bounds(bobsP); print("PARKBENCH", mnB, mxB)
append_asset("street_lamp_01", "StreetLamp", cK, (X + 1.5, 0.3, 0), 0.0, height=3.6)
for i in range(9):
    append_asset("shrub_01", "Shrub%d" % i, cK, (X - 4 + i * 1.0 + random.uniform(-0.3, 0.3), 1.6 + random.uniform(0, 0.8), 0), random.uniform(0, 6), height=random.uniform(0.7, 1.1))
gsrc, gobs = append_asset("grass_medium_01", "GrassSrc", cK, (X, -30, 0), 0.0, keep=lambda o: o.name.endswith("LOD1"))
# grass clumps scattered on the lawn around the bench (instanced copies of the Poly Haven grass, LOD1)
for i in range(160):
    _g = random.choice(gobs); _c = _g.copy(); cK.objects.link(_c); _c.parent = None
    _x = X + random.uniform(-4, 4); _y = random.uniform(-0.15, 3.5) if random.random() < 0.8 else random.uniform(-4.5, -1.9)
    if abs(_x - X) < 0.7 and -0.35 < _y < 0.35: _y += 0.6
    _c.location = (_x, _y, 0); _c.rotation_euler = (0, 0, random.uniform(0, 6.3)); _s = random.uniform(0.6, 1.1) * gsrc.scale.x; _c.scale = (_s, _s, _s)
# real trees behind the bench (Poly Haven CC0)
for i, (tx, ty, h) in enumerate(((-2.6, 5.0, 4.2), (2.4, 6.2, 4.8), (5.5, 4.4, 3.8))):
    append_asset("tree_small_02", "ParkTree%d" % i, cK, (X + tx, ty, 0), random.uniform(0, 6.3), height=h)
# (old low-poly blob trees disabled: director note)
if False:
    bark = mat("Bark", (0.35, 0.24, 0.16), 0.8); leaf = mat("Leaves", (0.30, 0.55, 0.18), 0.7)
    for i, (tx, ty) in enumerate(((-3, 5), (2.5, 6), (6, 4.5), (-7, 6.5))):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=3.0, location=(X + tx, ty, 1.5)); t_ = bpy.context.object; link(t_, cK); t_.data.materials.append(bark)
        for k in range(6):
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=random.uniform(0.8, 1.2), location=(X + tx + random.uniform(-0.8, 0.8), ty + random.uniform(-0.6, 0.6), 3.2 + random.uniform(-0.3, 0.8)))
            l_ = bpy.context.object; link(l_, cK); l_.data.materials.append(leaf)
            d_ = l_.modifiers.new("Disp", 'DISPLACE'); tx_ = bpy.data.textures.new("LeafN%d%d" % (i, k), 'CLOUDS'); tx_.noise_scale = 0.4; d_.texture = tx_; d_.strength = 0.35
            for p in l_.data.polygons: p.use_smooth = True
# fallen leaves on the ground and the bench
leaf_cols = [(0.85, 0.45, 0.12), (0.75, 0.25, 0.10), (0.88, 0.65, 0.18)]
for i in range(140):
    bpy.ops.mesh.primitive_circle_add(vertices=8, radius=0.035, fill_type='NGON', location=(X + random.uniform(-3, 3), random.uniform(-2.5, 1.5), 0.006))
    l_ = bpy.context.object; l_.scale.y = 0.55; l_.rotation_euler.z = random.uniform(0, 6.3); link(l_, cK)
    l_.data.materials.append(mat("Leaf%d" % (i % 3), leaf_cols[i % 3], 0.7))
# newspaper on the bench seat (two leaves with a soft fold), a pin lying on it
news_m = img_mat("Newspaper", SCR + "/tex/newspaper.png", 0.85)
seat_z = None
dg = bpy.context.evaluated_depsgraph_get()
for o in bobsP:
    oe = o.evaluated_get(dg); inv = oe.matrix_world.inverted()
    hit, loc, nrm, idx = oe.ray_cast(inv @ Vector((X - 0.15, -0.02, 2.0)), inv.to_3x3() @ Vector((0, 0, -1)))
    if hit: seat_z = (oe.matrix_world @ loc).z
print("SEAT z", seat_z)
sc["park_seat_z"] = seat_z or 0.45
bpy.ops.mesh.primitive_grid_add(x_subdivisions=20, y_subdivisions=14, size=1, location=(0, 0, 0)); np_ = bpy.context.object
np_.name = "Newspaper"; link(np_, cK); np_.scale = (0.42, 0.54, 1); bpy.ops.object.transform_apply(scale=True)
for v in np_.data.vertices:
    v.co.z = 0.012 * math.exp(-((v.co.y - 0.0) / 0.03) ** 2) + 0.004 * (v.co.x / 0.21) ** 2
np_.data.materials.append(news_m); np_.location = (X - 0.12, -0.02, (seat_z or 0.45) + 0.004); np_.rotation_euler.z = R_(-14)
so = np_.modifiers.new("Solid", 'SOLIDIFY'); so.thickness = 0.0015
for p in np_.data.polygons: p.use_smooth = True
pb2, pa2 = pin_parts("ParkPin", cK, clasp=True)
pb2.location = (X + 0.04, -0.07, (seat_z or 0.45) + 0.012); pb2.rotation_euler = (R_(90), 0, R_(30))
# ============================================================ world
w = bpy.data.worlds.new("Sky"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.75, 0.95, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.9
sc.render.engine = 'CYCLES'; sc.render.resolution_x, sc.render.resolution_y = 1080, 1920; sc.render.fps = 60
bpy.ops.wm.save_as_mainfile(filepath=W + "sets.blend", compress=True)
print("SETS_OK")
