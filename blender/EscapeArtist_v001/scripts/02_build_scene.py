"""Sets for EscapeArtist. blender -b humans.blend --python 02_build_scene.py -- <assets_dir> <out.blend>
assets_dir holds ph/<polyhaven ids>, ph/hdri/, models/*.glb (fetched by fetch_polyhaven.py / find_models.py).
Layout (metres): corridor x[-10,10] y[0,3]; cells y[-3,0] centred x=-6,-3,0(hero),3,6; back wall y=-3..-3.4 with windows;
yard y<-3.4, perimeter fence y=-14; memory house y[3.3,9] x[-3,8]; court x[8.3,12] y[3.3,9]."""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]
AS, OUT = a[0], a[1]
PH, MD = os.path.join(AS, "ph"), os.path.join(AS, "models")
R_ = math.radians
random.seed(7)
sc = bpy.context.scene

def col(name):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name); sc.collection.children.link(c)
    return c

def link(o, c):
    for uc in list(o.users_collection): uc.objects.unlink(o)
    col(c).objects.link(o); return o

# ---------------------------------------------------------------- materials
def tex_mat(name, pid, scale=1.0, tint=None, bump=0.5, rough_mul=1.0, metal=0.0):
    """Poly Haven texture set, box-projected in object space (so any mesh gets real texture without UVs)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    bs = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    d = os.path.join(PH, pid, "textures")
    def img(key, non_color=True):
        fs = [f for f in os.listdir(d) if key in f]
        if not fs: return None
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(d, fs[0]), check_existing=True)
        t.projection = "BOX"; t.projection_blend = 0.25
        if non_color: t.image.colorspace_settings.name = "Non-Color"
        L.new(mp.outputs["Vector"], t.inputs["Vector"]); return t
    dif = img("diff", False)
    if dif:
        if tint:
            mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.inputs["Factor"].default_value = 1.0
            L.new(dif.outputs["Color"], mix.inputs[6]); mix.inputs[7].default_value = tint + (1,)
            L.new(mix.outputs[2], bs.inputs["Base Color"])
        else:
            L.new(dif.outputs["Color"], bs.inputs["Base Color"])
    rg = img("rough")
    if rg:
        mt = N.new("ShaderNodeMath"); mt.operation = "MULTIPLY"; mt.inputs[1].default_value = rough_mul
        L.new(rg.outputs["Color"], mt.inputs[0]); L.new(mt.outputs[0], bs.inputs["Roughness"])
    ds = img("disp")
    if ds:
        b = N.new("ShaderNodeBump"); b.inputs["Strength"].default_value = bump; b.inputs["Distance"].default_value = 0.02
        L.new(ds.outputs["Color"], b.inputs["Height"]); L.new(b.outputs["Normal"], bs.inputs["Normal"])
    bs.inputs["Metallic"].default_value = metal
    return m

def emit_mat(name, color, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True
    bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Emission Color"].default_value = color + (1,); bs.inputs["Emission Strength"].default_value = strength
    bs.inputs["Base Color"].default_value = color + (1,)
    return m

M_CONC = tex_mat("Painted_Wall", "concrete_wall_008", 0.6, tint=(0.95, 0.96, 0.97), bump=0.15)
M_CONC_HALL = None
M_CONC_DIRTY = tex_mat("Painted_Wall_Cell", "concrete_wall_008", 0.9, tint=(0.82, 0.9, 0.98), bump=0.15)
M_FLOOR = tex_mat("Concrete_Floor", "concrete_floor_02", 0.5, tint=(0.85, 0.88, 0.9), bump=0.2, rough_mul=0.8)
M_RUST = bpy.data.materials.new("Painted_Steel_Bars"); M_RUST.use_nodes = True
_pb = M_RUST.node_tree.nodes["Principled BSDF"]; _pb.inputs["Base Color"].default_value = (0.12, 0.17, 0.26, 1)
_pb.inputs["Metallic"].default_value = 0.6; _pb.inputs["Roughness"].default_value = 0.38
M_STEEL = bpy.data.materials.new("Painted_Steel"); M_STEEL.use_nodes = True
_ps = M_STEEL.node_tree.nodes["Principled BSDF"]; _ps.inputs["Base Color"].default_value = (0.32, 0.42, 0.5, 1)
_ps.inputs["Metallic"].default_value = 0.5; _ps.inputs["Roughness"].default_value = 0.4
M_GROUND = tex_mat("Yard_Ground", "dry_ground_rocks", 0.35, bump=1.0)
def plaster(name, col):
    m = bpy.data.materials.new(name); m.use_nodes = True; N, L = m.node_tree.nodes, m.node_tree.links
    bs = N["Principled BSDF"]; nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 18; nz.inputs["Detail"].default_value = 6
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = tuple(c * 0.93 for c in col) + (1,); cr.color_ramp.elements[1].color = col + (1,)
    L.new(nz.outputs["Fac"], cr.inputs["Fac"]); L.new(cr.outputs["Color"], bs.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.05; L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], bs.inputs["Normal"])
    bs.inputs["Roughness"].default_value = 0.6; return m
M_BRICK = plaster("Plaster_Cream", (0.86, 0.8, 0.68))
M_BRICK_OUT = tex_mat("Brick_Outer", "brick_wall_001", 0.5, tint=(1.0, 0.95, 0.9), bump=0.3)
M_WOOD = tex_mat("Wood", "wood_table_001", 1.0, bump=0.3)
M_WOOD_DARK = tex_mat("Wood_Floor", "wood_table_001", 1.4, tint=(1.0, 0.92, 0.8), bump=0.15)
M_LAMP = emit_mat("Fluoro_Tube", (1.0, 0.95, 0.85), 18.0)

def box(name, c, loc, size, mat, bevel=0.01, coll="SET"):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object; o.name = name; o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        bv = o.modifiers.new("bev", "BEVEL"); bv.width = bevel; bv.segments = 2
    o.data.materials.append(mat); link(o, coll); return o

def wall(name, x0, x1, y0, y1, z0, z1, mat, coll="SET", rough=0.012):
    """wall slab with real surface irregularity (subdivided + noise displaced) so it never reads as a flat slab"""
    o = box(name, None, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), mat, bevel=0.015, coll=coll)
    if rough:
        sd = o.modifiers.new("sub", "SUBSURF"); sd.subdivision_type = "SIMPLE"; sd.levels = sd.render_levels = 4
        tx = bpy.data.textures.get("WallNoise") or bpy.data.textures.new("WallNoise", "CLOUDS")
        tx.noise_scale = 0.35
        dp = o.modifiers.new("disp", "DISPLACE"); dp.texture = tx; dp.strength = rough; dp.texture_coords = "GLOBAL"
    return o

def cyl(name, p0, p1, r, mat, coll="SET", verts=10):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length, location=(p0 + p1) / 2)
    o = bpy.context.object; o.name = name
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    o.data.materials.append(mat); link(o, coll)
    for p in o.data.polygons: p.use_smooth = True
    return o

def join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join()
    o = bpy.context.object; o.name = name
    o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)     # mesh in world space, origin at 0 (so hinge offsets are exact)
    return o

def glb(fname, name, size, axis, loc, rotz=0.0, coll="PROPS", rot=(0, 0, 0), floor=True):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(MD, fname + ".glb"))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    root = bpy.data.objects.new(name, None); col(coll).objects.link(root)
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    s = size / (mx - mn)[axis]
    ctr = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z if floor else (mn.z + mx.z) / 2))
    for o in new:
        link(o, coll)
        if o.parent is None:
            o.parent = root; o.matrix_parent_inverse = Matrix.Scale(s, 4) @ Matrix.Translation(-ctr)
    root.location = loc; root.rotation_euler = (rot[0], rot[1], rotz)
    root.empty_display_size = 0.2
    return root, meshes

# ---------------------------------------------------------------- CELL BLOCK: corridor + 5 cells + back wall with windows
CX = [-6.0, -3.0, 0.0, 3.0, 6.0]
wall("Corridor_Floor", -11, 13, -3.4, 3.3, -0.2, 0.0, M_FLOOR, rough=0.004)
wall("Corridor_Ceiling", -11, 13, -3.4, 3.3, 3.0, 3.2, M_CONC, rough=0.0)
wall("Corridor_FarWall", -11, 9.4, 3.0, 3.3, 0.0, 3.0, M_CONC)             # camera flies through this into memory house
wall("Corridor_FarWall_E", 10.8, 13, 3.0, 3.3, 0.0, 3.0, M_CONC)
wall("Corridor_FarWall_Lintel", 9.4, 10.8, 3.0, 3.3, 2.5, 3.0, M_CONC)
box("CourtDoor_Frame_L", None, (9.43, 3.15, 1.25), (0.06, 0.34, 2.5), M_WOOD_DARK, coll="COURT")
box("CourtDoor_Frame_R", None, (10.77, 3.15, 1.25), (0.06, 0.34, 2.5), M_WOOD_DARK, coll="COURT")
for i, x in enumerate([-7.5, -4.5, -1.5, 1.5, 4.5, 7.5]):
    wall("Cell_Divider_%d" % i, x - 0.12, x + 0.12, -3.0, 0.0, 0.0, 3.0, M_CONC_DIRTY)
wall("Cell_Divider_End_W", -11, -7.62, -3.0, 0.0, 0.0, 3.0, M_CONC_DIRTY)
wall("Cell_Divider_End_E", 7.62, 13, -3.0, 0.0, 0.0, 3.0, M_CONC_DIRTY)
# back wall with a window opening per cell (x±0.4, z 1.35..2.05)
WZ0, WZ1, WHW = 1.35, 2.05, 0.4
segs = [-11] + [v for x in CX for v in (x - WHW, x + WHW)] + [13]
for i in range(0, len(segs), 2):
    wall("BackWall_%d" % i, segs[i], segs[i + 1], -3.4, -3.0, 0.0, 3.0, M_CONC_DIRTY)
for x in CX:
    wall("BackWall_Below_%g" % x, x - WHW, x + WHW, -3.4, -3.0, 0.0, WZ0, M_CONC_DIRTY)
    wall("BackWall_Above_%g" % x, x - WHW, x + WHW, -3.4, -3.0, WZ1, 3.0, M_CONC_DIRTY)
    for k in range(5):                                           # window bars
        bx = x - WHW + 0.8 * (k + 0.5) / 5
        cyl("WinBar_%g_%d" % (x, k), (bx, -3.2, WZ0), (bx, -3.2, WZ1), 0.014, M_RUST)
# exterior skin of the block (brick) so the yard side looks like a building
for i in range(0, len(segs), 2):
    wall("BlockExt_%d" % i, segs[i], segs[i + 1], -3.5, -3.4, 0.0, 4.2, M_BRICK_OUT, rough=0.0)
for x in CX:
    wall("BlockExt_Below_%g" % x, x - WHW, x + WHW, -3.5, -3.4, 0.0, WZ0, M_BRICK_OUT, rough=0.0)
    wall("BlockExt_Above_%g" % x, x - WHW, x + WHW, -3.5, -3.4, WZ1, 4.2, M_BRICK_OUT, rough=0.0)
    box("Sill_%g" % x, None, (x, -3.52, WZ0 - 0.03), (0.95, 0.14, 0.06), M_CONC, bevel=0.01)
wall("Block_Roof", -11.2, 13.2, -3.6, 3.3, 4.2, 4.4, M_CONC, rough=0.0)
box("Gutter", None, (1, -3.62, 4.15), (24.4, 0.12, 0.1), M_STEEL, bevel=0.01)
for k, x in enumerate((-9.0, 4.5, 11.5)): cyl("Downpipe_%d" % k, (x, -3.6, 0), (x, -3.6, 4.15), 0.05, M_STEEL)
# cell fronts: vertical bars + two straps; hero cell (x=0) and x=3 get a hinged door
FR_Y = 0.0
for x in CX:
    bars = []
    for k in range(25):
        bx = x - 1.38 + 2.76 * k / 24
        if x in (0.0,) and -0.95 < bx - x < -0.05: continue          # door gap on the hero cell
        bars.append(cyl("Bar", (bx, FR_Y, 0.0), (bx, FR_Y, 3.0), 0.016, M_RUST))
    for z in (0.12, 1.1, 2.2, 2.9):
        bars.append(box("Strap", None, (x, FR_Y, z), (2.8, 0.05, 0.05), M_RUST, bevel=0.005))
    join(bars, "CellFront_%g" % x)
# hero door (hinge at x=-0.95, swings into corridor), with a lock box
door_parts = []
for k in range(7):
    bx = -0.92 + 0.84 * k / 6
    door_parts.append(cyl("DBar", (bx, 0, 0.03), (bx, 0, 2.85), 0.016, M_RUST))
for z in (0.08, 1.05, 2.1, 2.82):
    door_parts.append(box("DStrap", None, (-0.5, 0, z), (0.9, 0.05, 0.05), M_RUST, bevel=0.005))
M_LOCK = bpy.data.materials.new("Lock_Steel"); M_LOCK.use_nodes = True
_lk = M_LOCK.node_tree.nodes["Principled BSDF"]; _lk.inputs["Base Color"].default_value = (0.16, 0.18, 0.2, 1); _lk.inputs["Metallic"].default_value = 0.9; _lk.inputs["Roughness"].default_value = 0.35
M_HOLE = bpy.data.materials.new("Keyhole"); M_HOLE.use_nodes = True; M_HOLE.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.01, 0.01, 0.01, 1)
M_BRASSL = bpy.data.materials.new("Lock_Brass"); M_BRASSL.use_nodes = True
_bl = M_BRASSL.node_tree.nodes["Principled BSDF"]; _bl.inputs["Base Color"].default_value = (0.72, 0.55, 0.28, 1); _bl.inputs["Metallic"].default_value = 1.0; _bl.inputs["Roughness"].default_value = 0.3
lock = box("Lock", None, (-0.15, 0.0, 1.05), (0.16, 0.1, 0.22), M_LOCK, bevel=0.012); door_parts.append(lock)
for sy in (1, -1):
    door_parts.append(cyl("Escutcheon", (-0.15, sy * 0.05, 1.0), (-0.15, sy * 0.056, 1.0), 0.022, M_BRASSL, verts=20))
    door_parts.append(cyl("Keyhole", (-0.15, sy * 0.055, 1.0), (-0.15, sy * 0.058, 1.0), 0.006, M_HOLE, verts=12))
    door_parts.append(box("KeySlot", None, (-0.15, sy * 0.0575, 0.988), (0.005, 0.004, 0.016), M_HOLE, bevel=0.0))
    door_parts.append(box("Handle", None, (-0.15, sy * 0.075, 1.12), (0.03, 0.05, 0.03), M_LOCK, bevel=0.006))
    door_parts.append(cyl("HandleBar", (-0.15, sy * 0.1, 1.12), (-0.04, sy * 0.1, 1.12), 0.012, M_LOCK, verts=12))
for z in (0.97, 1.13):
    door_parts.append(cyl("Rivet", (-0.21, 0.05, z), (-0.21, 0.056, z), 0.006, M_LOCK, verts=8))
    door_parts.append(cyl("Rivet", (-0.09, 0.05, z), (-0.09, 0.056, z), 0.006, M_LOCK, verts=8))
door = join(door_parts, "HeroDoor")
door.data.transform(Matrix.Translation((0.95, 0, 0)))           # origin to hinge
door.location = (-0.95, 0, 0)
# solid solitary door panel (keyed visible in the solitary beats) with a food slot of light
sol = box("SolitaryPanel", None, (0, 0.06, 1.5), (2.9, 0.06, 3.0), M_STEEL, bevel=0.01)
bpy.ops.mesh.primitive_cube_add(location=(0, 0.06, 1.25)); cut = bpy.context.object; cut.scale = (0.25, 0.1, 0.05)
bm_ = sol.modifiers.new("slot", "BOOLEAN"); bm_.object = cut; bm_.operation = "DIFFERENCE"
bpy.context.view_layer.objects.active = sol; bpy.ops.object.modifier_apply(modifier="slot"); bpy.data.objects.remove(cut)
# fluorescent fixtures along corridor + one caged bulb per cell
for i, x in enumerate(range(-9, 13, 3)):
    box("Fixture_%d" % i, None, (x, 1.5, 2.96), (1.25, 0.16, 0.06), M_STEEL, bevel=0.005, coll="LIGHTS")
    box("Tube_%d" % i, None, (x, 1.5, 2.92), (1.15, 0.05, 0.025), M_LAMP, bevel=0.0, coll="LIGHTS")
    bpy.ops.object.light_add(type="AREA", location=(x, 1.5, 2.88)); l = bpy.context.object; l.name = "CorrLight_%d" % i
    l.data.shape = "RECTANGLE"; l.data.size, l.data.size_y = 1.2, 0.15; l.data.energy = 300; l.data.color = (1.0, 0.95, 0.88)
    link(l, "LIGHTS")
# gate across corridor at x=8.7 (slams in beat 7)
gate_parts = [cyl("GBar", (8.7, 0.1 + 2.8 * k / 14, 0.02), (8.7, 0.1 + 2.8 * k / 14, 2.95), 0.02, M_RUST) for k in range(15)]
for z in (0.1, 1.2, 2.85): gate_parts.append(box("GStrap", None, (8.7, 1.5, z), (0.06, 2.9, 0.06), M_RUST, bevel=0.005))
gate = join(gate_parts, "CorridorGate")
gate.data.transform(Matrix.Translation((-8.7, -0.1, 0))); gate.location = (8.7, 0.1, 0)

# ---------------------------------------------------------------- HERO CELL furniture
bunk, _ = glb("bunk", "LoftBed_Neighbour", 1.9, 1, (3.68, -1.95, 0.0), rotz=0.0, coll="PROPS")   # loft bed + desk dresses the cell next door
# hero bunk: steel shelf bolted to the east wall, thin canvas mattress with real sag/wrinkle displacement, folded blanket
M_CANVAS = bpy.data.materials.new("Mattress_Canvas"); M_CANVAS.use_nodes = True
_N, _L = M_CANVAS.node_tree.nodes, M_CANVAS.node_tree.links; _b = _N["Principled BSDF"]
_w = _N.new("ShaderNodeTexWave"); _w.inputs["Scale"].default_value = 60; _w.inputs["Distortion"].default_value = 2
_nz = _N.new("ShaderNodeTexNoise"); _nz.inputs["Scale"].default_value = 8
_cr = _N.new("ShaderNodeValToRGB"); _cr.color_ramp.elements[0].color = (0.16, 0.17, 0.13, 1); _cr.color_ramp.elements[1].color = (0.32, 0.33, 0.27, 1)
_mx = _N.new("ShaderNodeMath"); _mx.operation = "MULTIPLY"
_L.new(_w.outputs["Fac"], _mx.inputs[0]); _L.new(_nz.outputs["Fac"], _mx.inputs[1]); _L.new(_mx.outputs[0], _cr.inputs["Fac"]); _L.new(_cr.outputs["Color"], _b.inputs["Base Color"])
_bp = _N.new("ShaderNodeBump"); _bp.inputs["Strength"].default_value = 0.3; _L.new(_w.outputs["Fac"], _bp.inputs["Height"]); _L.new(_bp.outputs["Normal"], _b.inputs["Normal"])
_b.inputs["Roughness"].default_value = 0.95
box("Bunk_Shelf", None, (0.99, -1.95, 0.38), (0.76, 2.0, 0.05), M_STEEL, coll="PROPS")
for _y in (-2.85, -1.05): box("Bunk_Leg", None, (0.7, _y, 0.18), (0.05, 0.05, 0.36), M_STEEL, coll="PROPS")
_m = wall("Bunk_Mattress", 0.63, 1.35, -2.93, -0.97, 0.405, 0.48, M_CANVAS, coll="PROPS", rough=0.018)
_m.modifiers["disp"].texture = bpy.data.textures.new("MatNoise", "CLOUDS"); _m.modifiers["disp"].texture.noise_scale = 0.12
_bl = wall("Bunk_Blanket", 0.7, 1.3, -2.9, -2.45, 0.48, 0.58, M_CANVAS, coll="PROPS", rough=0.02)
# tally-mark wall: one mesh of scratch marks with an 'ord' attribute; material reveals marks with ord < Reveal
bm = bmesh.new(); ords = []
n_marks = 0
for row in range(14):
    for grp in range(9):
        for k in range(5):
            gx = -1.25 + grp * 0.15 + k * 0.022; gz = 2.3 - row * 0.085
            if k < 4:
                p0, p1 = Vector((gx, 0, gz)), Vector((gx + 0.004, 0, gz + 0.06))
            else:
                p0, p1 = Vector((gx - 0.09, 0, gz + 0.005)), Vector((gx + 0.0, 0, gz + 0.055))
            dvec = (p1 - p0).normalized(); nrm = Vector((-dvec.z, 0, dvec.x)) * 0.0035
            vs = [bm.verts.new(v) for v in (p0 - nrm, p1 - nrm, p1 + nrm, p0 + nrm)]
            bm.faces.new(vs); ords.append((row * 9 + grp) / (14 * 9.0) + k * 0.0005)
me = bpy.data.meshes.new("TallyMarks"); bm.to_mesh(me); bm.free()
at = me.attributes.new("ord", "FLOAT", "FACE")
for i, v in enumerate(ords): at.data[i].value = v
tally = bpy.data.objects.new("TallyMarks", me); link(tally, "PROPS")
tally.rotation_euler.z = R_(90); tally.location = (-1.37, -1.5, 0.0)   # on the inner face of the west divider
mt = bpy.data.materials.new("Tally_Scratch"); mt.use_nodes = True; mt.blend_method = "HASHED"
N, L = mt.node_tree.nodes, mt.node_tree.links
bs = N["Principled BSDF"]; bs.inputs["Base Color"].default_value = (0.05, 0.045, 0.04, 1); bs.inputs["Roughness"].default_value = 0.9
atn = N.new("ShaderNodeAttribute"); atn.attribute_type = "GEOMETRY"; atn.attribute_name = "ord"
rv = N.new("ShaderNodeValue"); rv.name = "Reveal"; rv.outputs[0].default_value = 0.02
cmp_ = N.new("ShaderNodeMath"); cmp_.operation = "LESS_THAN"
L.new(atn.outputs["Fac"], cmp_.inputs[0]); L.new(rv.outputs[0], cmp_.inputs[1]); L.new(cmp_.outputs[0], bs.inputs["Alpha"])
me.materials.append(mt)
# sink / toilet stand-in from steel (small, in the corner) + blanket roll + cup
box("Cell_Shelf", None, (-1.1, -2.85, 1.1), (0.5, 0.25, 0.03), M_STEEL, coll="PROPS")
cyl("Cup", (-1.0, -2.85, 1.115), (-1.0, -2.85, 1.2), 0.035, M_STEEL, coll="PROPS", verts=16)

# ---------------------------------------------------------------- YARD + FENCE (night)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -22, 0)); g = bpy.context.object; g.name = "Yard_Ground"
g.scale = (60, 38, 1); bpy.ops.object.transform_apply(scale=True)
sd = g.modifiers.new("sub", "SUBSURF"); sd.subdivision_type = "SIMPLE"; sd.levels = sd.render_levels = 6
tx = bpy.data.textures.new("GroundNoise", "CLOUDS"); tx.noise_scale = 1.2
dp = g.modifiers.new("disp", "DISPLACE"); dp.texture = tx; dp.strength = 0.12; dp.mid_level = 0.5; dp.texture_coords = "GLOBAL"
g.data.materials.append(M_GROUND); link(g, "YARD")
# keep the strip next to the building and the fence foot flat-ish: a vertex group would be nicer; the noise is small (±6 cm)
FY = -14.0
fence_root, fence_meshes = glb("fence", "Fence", 3.6, 2, (2.0, FY, 0.0), rotz=R_(90), coll="YARD")
# razor wire coils on top of fence (two coils), real wire with barbs
def razor_coil(name, x0, x1, y, z, r=0.32, pitch=0.22):
    bm = bmesh.new(); n = int((x1 - x0) / pitch * 24); prev = None
    for i in range(n + 1):
        t = i / 24.0 * 2 * math.pi; x = x0 + (x1 - x0) * i / n
        p = Vector((x, y + r * math.cos(t), z + r * math.sin(t)))
        v = bm.verts.new(p)
        if prev: bm.edges.new((prev, v))
        prev = v
        if i % 6 == 0:                                                # barb: small flat blade
            tng = Vector((0, -math.sin(t), math.cos(t)))
            for sgn in (1, -1):
                b0 = bm.verts.new(p + tng * 0.012 * sgn); b1 = bm.verts.new(p + Vector((0.018 * sgn, 0, 0)) + tng * 0.03 * sgn)
                bm.edges.new((v, b0)); bm.edges.new((b0, b1))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); link(o, "YARD")
    sk = o.modifiers.new("skin", "SKIN")
    for vtx in me.skin_vertices[0].data: vtx.radius = (0.0035, 0.0035)
    o.data.materials.append(M_RUST)
    return o
FENCE_TOP = 3.4
razor_coil("RazorWire_Top", -5.8, 9.8, FY, FENCE_TOP + 0.3)
razor_coil("RazorWire_Ground", -5.8, 9.8, FY - 0.8, 0.35, r=0.38)
# floodlight towers + searchlight
for i, x in enumerate((-10, 14)):
    cyl("FloodPole_%d" % i, (x, FY + 1.5, 0), (x, FY + 1.5, 7.5), 0.09, M_STEEL, coll="YARD")
    box("FloodHead_%d" % i, None, (x, FY + 1.3, 7.6), (0.6, 0.3, 0.4), M_STEEL, coll="YARD")
bpy.ops.object.light_add(type="SPOT", location=(-10, FY + 1.2, 7.5)); sp = bpy.context.object; sp.name = "Searchlight"
sp.data.energy = 60000; sp.data.spot_size = R_(22); sp.data.spot_blend = 0.4; sp.data.color = (0.85, 0.9, 1.0); link(sp, "LIGHTS")
bpy.ops.object.light_add(type="SPOT", location=(14, FY + 1.2, 7.5)); sp2 = bpy.context.object; sp2.name = "Floodlight"
sp2.data.energy = 60000; sp2.data.spot_size = R_(70); sp2.data.spot_blend = 0.6; sp2.data.color = (1.0, 0.85, 0.6); link(sp2, "LIGHTS")
sp2.rotation_euler = (R_(50), 0, R_(130))
# outer perimeter wall + field tufts beyond the fence (instanced dark grass clumps)
wall("Perimeter_Wall", -30, 30, -31, -30.5, 0, 4.5, M_BRICK_OUT)
bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=0.04, depth=0.35, location=(0, 0, 0.17)); tuft = bpy.context.object; tuft.name = "GrassBlade"
mg = bpy.data.materials.new("DryGrass"); mg.use_nodes = True; mg.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.18, 0.16, 0.08, 1)
tuft.data.materials.append(mg); link(tuft, "YARD")
blades = []
for i in range(1400):
    x = random.uniform(-18, 22); y = random.uniform(-29, FY - 1.3)
    o = tuft.copy(); o.location = (x, y, 0.1); o.rotation_euler = (random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4), random.uniform(0, 6.3))
    o.scale = (1, 1, random.uniform(0.6, 2.2)); col("YARD").objects.link(o); blades.append(o)
grass = join(blades, "FieldGrass")
bpy.data.objects.remove(tuft)
# readable blue moonlight over the yard (night exteriors)
bpy.ops.object.light_add(type="SUN", location=(0, -15, 10)); _mo = bpy.context.object; _mo.name = "YardMoon"
_mo.data.energy = 1.4; _mo.data.color = (0.5, 0.66, 1.0); _mo.data.angle = R_(3); _mo.rotation_euler = (R_(50), 0, R_(200)); link(_mo, "LIGHTS")
# sky / night HDRI
w = bpy.data.worlds.new("Night"); sc.world = w; w.use_nodes = True
en = w.node_tree.nodes.new("ShaderNodeTexEnvironment")
en.image = bpy.data.images.load(os.path.join(PH, "hdri", "moonless_golf_1k.hdr"))
bg = w.node_tree.nodes["Background"]; bg.inputs["Strength"].default_value = 2.6
_mxw = w.node_tree.nodes.new("ShaderNodeMix"); _mxw.data_type = "RGBA"; _mxw.blend_type = "MULTIPLY"; _mxw.inputs["Factor"].default_value = 1.0
_mxw.inputs[7].default_value = (0.55, 0.75, 1.0, 1)
w.node_tree.links.new(en.outputs["Color"], _mxw.inputs[6]); w.node_tree.links.new(_mxw.outputs[2], bg.inputs["Color"])

# ---------------------------------------------------------------- MEMORY HOUSE (behind far corridor wall) y[3.3,9]
HY0, HY1 = 3.3, 9.0
wall("House_Floor", -3, 8.3, HY0, HY1, -0.02, 0.0, M_WOOD_DARK, coll="HOUSE", rough=0.0)
wall("House_Ceiling", -3, 8.3, HY0, HY1, 2.8, 2.9, M_CONC, coll="HOUSE", rough=0.0)
wall("House_BackWall", -3, 8.3, HY1, HY1 + 0.2, 0, 2.8, M_BRICK, coll="HOUSE")
wall("House_WestWall", -3.2, -3.0, HY0, HY1, 0, 2.8, M_BRICK, coll="HOUSE")
# east wall of the living room has a window (police lights) at y 5..6.4
wall("House_EastWall_a", 8.1, 8.3, HY0, 5.0, 0, 2.8, M_BRICK, coll="HOUSE")
wall("House_EastWall_b", 8.1, 8.3, 6.4, HY1, 0, 2.8, M_BRICK, coll="HOUSE")
wall("House_EastWall_c", 8.1, 8.3, 5.0, 6.4, 0, 0.9, M_BRICK, coll="HOUSE")
wall("House_EastWall_d", 8.1, 8.3, 5.0, 6.4, 2.2, 2.8, M_BRICK, coll="HOUSE")
for k, z in enumerate((0.9, 1.55, 2.2)): box("WinFrame_h%d" % k, None, (8.2, 5.7, z), (0.08, 1.4, 0.05), M_WOOD, coll="HOUSE")
for k, y in enumerate((5.0, 5.7, 6.4)): box("WinFrame_v%d" % k, None, (8.2, y, 1.55), (0.08, 0.05, 1.35), M_WOOD, coll="HOUSE")
wb, _ = glb("workbench", "Workbench", 1.6, 0, (0.5, 8.55, 0.0), rotz=0.0, coll="HOUSE")
watch, _ = glb("watch", "ClockWork", 0.16, 0, (0.45, 8.52, 0.755), rotz=R_(20), coll="HOUSE")
tb, _ = glb("toolbox", "Toolbox", 0.55, 0, (2.2, 7.6, 0.0), rotz=R_(-15), coll="HOUSE")
chair, _ = glb("armchair", "Armchair", 0.9, 0, (4.4, 7.4, 0.0), rotz=R_(200), coll="HOUSE")
box("SideTable", None, (6.9, 7.8, 0.36), (0.55, 0.55, 0.72), M_WOOD, coll="HOUSE", bevel=0.02)
phone, pm = glb("phone", "Phone", 0.5, 2, (6.9, 7.8, 0.435), rotz=R_(200), coll="HOUSE")
for o in pm:
    if "Dial Numbers" in o.name: bpy.data.objects.remove(o)          # no text on screen
# loose gears on the bench (small toothed discs)
def gear(name, r, teeth, th, loc, mat):
    bm = bmesh.new(); pts = []
    for i in range(teeth * 4):
        t = 2 * math.pi * i / (teeth * 4); rr = r * (1.0 if (i % 4) in (1, 2) else 0.86)
        pts.append(Vector((rr * math.cos(t), rr * math.sin(t), 0)))
    vs = [bm.verts.new(p) for p in pts]; f = bm.faces.new(vs)
    ex = bmesh.ops.extrude_face_region(bm, geom=[f]); bmesh.ops.translate(bm, vec=(0, 0, th), verts=[v for v in ex["geom"] if isinstance(v, bmesh.types.BMVert)])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); o.location = loc; link(o, "HOUSE")
    me.materials.append(mat); bv = o.modifiers.new("b", "BEVEL"); bv.width = 0.0006; return o
M_BRASS = bpy.data.materials.new("Brass"); M_BRASS.use_nodes = True
bb = M_BRASS.node_tree.nodes["Principled BSDF"]; bb.inputs["Base Color"].default_value = (0.75, 0.55, 0.25, 1); bb.inputs["Metallic"].default_value = 1; bb.inputs["Roughness"].default_value = 0.3
BENCH_Z = 0.0  # resolved later from the bench mesh
for i, (r, t, x, y) in enumerate(((0.025, 18, 0.62, 8.22), (0.016, 12, 0.7, 8.3), (0.034, 24, 0.25, 8.18), (0.012, 10, 0.55, 8.35), (0.02, 15, 0.8, 8.15))):
    gear("Gear_%d" % i, r, t, 0.003, (x, y + 0.3, 0.755), M_BRASS)
# warm practical lamps
bpy.ops.object.light_add(type="POINT", location=(0.6, 8.1, 1.9)); l = bpy.context.object; l.name = "BenchLamp"; l.data.energy = 200; l.data.color = (1.0, 0.72, 0.42); l.data.shadow_soft_size = 0.15; link(l, "LIGHTS")
bpy.ops.object.light_add(type="AREA", location=(4.0, 5.5, 2.7)); l = bpy.context.object; l.name = "HouseFill"; l.data.energy = 700; l.data.size = 2.5; l.data.color = (1.0, 0.8, 0.6); link(l, "LIGHTS")
bpy.ops.object.light_add(type="POINT", location=(7.0, 8.2, 1.6)); l = bpy.context.object; l.name = "PhoneLamp"; l.data.energy = 60; l.data.color = (1.0, 0.75, 0.5); link(l, "LIGHTS")
# police lights outside the window (red/blue, keyed to flash in the animate script)
for nm, c, y in (("PoliceRed", (1.0, 0.05, 0.03), 5.2), ("PoliceBlue", (0.05, 0.2, 1.0), 6.2)):
    bpy.ops.object.light_add(type="POINT", location=(10.5, y, 1.2)); l = bpy.context.object; l.name = nm; l.data.energy = 0; l.data.color = c; l.data.shadow_soft_size = 0.3; link(l, "LIGHTS")

# ---------------------------------------------------------------- COURT (east of house, x[8.3,12.5])
wall("Court_Floor", 8.3, 12.5, HY0, HY1, -0.02, 0.0, M_WOOD_DARK, coll="COURT", rough=0.0)
wall("Court_BackWall", 8.3, 12.5, HY1, HY1 + 0.2, 0, 3.2, M_WOOD_DARK, coll="COURT")
wall("Court_EastWall", 12.5, 12.7, HY0, HY1, 0, 3.2, M_WOOD_DARK, coll="COURT")
box("Court_Bench", None, (10.4, 7.6, 0.55), (2.6, 0.9, 1.1), M_WOOD_DARK, coll="COURT", bevel=0.03)
box("Court_BenchTop", None, (10.4, 7.45, 1.12), (2.8, 1.1, 0.05), M_WOOD, coll="COURT", bevel=0.01)
for k in range(6): box("Court_Panel_%d" % k, None, (9.3 + k * 0.44, 7.13, 0.55), (0.36, 0.03, 0.8), M_WOOD, coll="COURT", bevel=0.01)
gav, _ = glb("gavel", "Gavel", 0.3, 1, (10.2, 7.25, 1.145), rotz=R_(10), coll="COURT")
cyl("SoundBlock", (10.0, 7.25, 1.145), (10.0, 7.25, 1.18), 0.06, M_WOOD, coll="COURT", verts=24)
bpy.ops.object.light_add(type="AREA", location=(10.4, 5.8, 2.9)); l = bpy.context.object; l.name = "CourtKey"; l.data.energy = 800; l.data.size = 1.5; l.data.color = (1.0, 0.86, 0.7); link(l, "LIGHTS")
l.rotation_euler = (R_(35), 0, 0)

# ---------------------------------------------------------------- small hero props (key ring, file, scrap/key, saw, tube, placards, candles)
def key_mesh(name, teeth):
    """flat key: bow ring + shaft + bitting. teeth=False gives the plain scrap strip with the same topology (shape key)."""
    prof = [(0.0, 0.0), (0.045, 0.0)]
    cuts = [0.004, 0.0015, 0.0035, 0.001, 0.003, 0.002]
    for i, c in enumerate(cuts):
        x0 = 0.012 + i * 0.0055
        prof += [(0.045 + 0.0 * x0, 0), ]
    shaft = [(0.0, -0.004), (0.05, -0.004)]
    bm = bmesh.new()
    top = [Vector((0.0 + 0.05 * i / 12, 0.004, 0)) for i in range(13)]
    bot = []
    for i in range(13):
        x = 0.05 * i / 12; d = 0.0
        if teeth and 2 <= i <= 11: d = [0.0035, 0.0012, 0.0032, 0.0008, 0.0028, 0.0015, 0.0036, 0.001, 0.0025, 0.002][i - 2]
        bot.append(Vector((x, -0.004 - 0.005 + d, 0)))
    vs = [bm.verts.new(p) for p in top + bot[::-1]]
    f = bm.faces.new(vs)
    ex = bmesh.ops.extrude_face_region(bm, geom=[f]); bmesh.ops.translate(bm, vec=(0, 0, 0.002), verts=[v for v in ex["geom"] if isinstance(v, bmesh.types.BMVert)])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return me
M_KEY = bpy.data.materials.new("KeyBrass"); M_KEY.use_nodes = True
kb = M_KEY.node_tree.nodes["Principled BSDF"]; kb.inputs["Base Color"].default_value = (0.7, 0.6, 0.38, 1); kb.inputs["Metallic"].default_value = 1; kb.inputs["Roughness"].default_value = 0.35
M_SCRAP = tex_mat("ScrapMetal", "rusty_metal_02", 30.0, tint=(0.75, 0.72, 0.7), bump=0.2, metal=0.8, rough_mul=0.7)
# key ring (guard's belt): torus + 3 keys with bows
bpy.ops.mesh.primitive_torus_add(major_radius=0.03, minor_radius=0.0022, location=(0, 0, 0)); ring = bpy.context.object; ring.name = "KeyRing"
ring.data.materials.append(M_KEY); link(ring, "PROPS")
for i in range(3):
    km = key_mesh("GuardKey_%d" % i, True); ko = bpy.data.objects.new("GuardKey_%d" % i, km); km.materials.append(M_KEY); link(ko, "PROPS")
    bpy.ops.mesh.primitive_torus_add(major_radius=0.011, minor_radius=0.003, location=(-0.008, 0, 0.001)); bw = bpy.context.object; bw.data.materials.append(M_KEY)
    link(bw, "PROPS"); bw.parent = ko
    ko.parent = ring; ko.location = (0.03 * math.cos(i * 0.5 - 0.5) + 0.012, 0.0, -0.03 - 0.005 * i); ko.rotation_euler = (R_(90), R_(-70 - i * 18), 0)
# glowing memory overlay of the key bitting (beat 1)
gk = bpy.data.objects.new("KeyGlow", key_mesh("KeyGlowMesh", True)); link(gk, "PROPS")
gk.data.materials.append(emit_mat("KeyGlow_Emit", (1.0, 0.75, 0.3), 25.0))
# scrap strip that becomes the key: shape key Basis=plain strip, 'Cut'=key bitting
sm = key_mesh("ScrapKeyMesh", False); so = bpy.data.objects.new("ScrapKey", sm); link(so, "PROPS"); sm.materials.append(M_SCRAP)
so.shape_key_add(name="Basis"); kk = so.shape_key_add(name="Cut")
cut_me = key_mesh("tmp", True)
for i, v in enumerate(cut_me.vertices): kk.data[i].co = v.co
bpy.data.meshes.remove(cut_me)
# hand file (rasp): long tapered bar with crosshatch bump + wooden handle
f_ = box("File_Blade", None, (0.09, 0, 0), (0.18, 0.016, 0.004), tex_mat("FileSteel", "rusty_metal_02", 80.0, tint=(0.4, 0.42, 0.45), bump=1.0, metal=0.9), bevel=0.001, coll="PROPS")
fh = cyl("File_Handle", (-0.09, 0, 0), (0.0, 0, 0), 0.011, M_WOOD, coll="PROPS", verts=14); fh.parent = f_; fh.location = (-0.045, 0, 0); fh.rotation_euler = (0, R_(90), 0)
sawr, _ = glb("hacksaw", "Hacksaw", 0.42, 1, (0, 0, 0), coll="PROPS", floor=False)
tube, tm = glb("tube", "ToothpasteTube", 0.17, 2, (0, 0, 0), coll="PROPS", floor=False)
cand, _ = glb("candles", "Candles", 0.35, 0, (0, -18.0, 0), coll="YARD")
print("SCENE OBJECTS", len(bpy.data.objects))
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920; sc.render.fps = 60; sc.frame_start, sc.frame_end = 0, 3750
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
bpy.ops.wm.save_as_mainfile(filepath=OUT)
