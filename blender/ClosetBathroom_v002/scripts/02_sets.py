"""ClosetBathroom sets: hallway/living room with the closet door; the small room behind it in three dressings
(BATH = the bathroom he finds, CLOSET = what he remembers, PRANK = the imagined half-built bathroom); the clinic.
blender -b work/chars.blend --python 02_sets.py -- work/sets.blend"""
import bpy, bmesh, sys, math
from mathutils import Vector, Matrix
HERE = "/home/user/Muhammed/blender/ClosetBathroom_v002/"
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; R_ = math.radians

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
def link(o, c):
    for u in list(o.users_collection): u.objects.unlink(o)
    c.objects.link(o)
def mat(name, rgb, rough=0.5, metal=0.0, emit=None, es=1.0, spec=0.3):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; P = m.node_tree.nodes["Principled BSDF"]
    P.inputs["Base Color"].default_value = (*rgb, 1); P.inputs["Roughness"].default_value = rough
    P.inputs["Metallic"].default_value = metal; P.inputs["Specular IOR Level"].default_value = spec
    if emit: P.inputs["Emission Color"].default_value = (*emit, 1); P.inputs["Emission Strength"].default_value = es
    return m
def img_mat(name, path, rough=0.5, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path); t.image.pack()
    nt.links.new(t.outputs[0], P.inputs["Base Color"]); P.inputs["Roughness"].default_value = rough
    if emit:
        nt.links.new(t.outputs[0], P.inputs["Emission Color"]); P.inputs["Emission Strength"].default_value = emit
    return m
def box(name, size, loc, m, c, bevel=0.006, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); c.objects.link(o); o.location = loc; o.rotation_euler = rot
    if m: me.materials.append(m)
    if bevel:
        b = o.modifiers.new("Bevel", 'BEVEL'); b.width = bevel; b.segments = 2; b.limit_method = 'ANGLE'
    for p in me.polygons: p.use_smooth = False
    return o
def cyl(name, r, h, loc, m, c, rot=(0, 0, 0), verts=24):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r, depth=h)
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); c.objects.link(o)
    o.location = loc; o.rotation_euler = rot; me.materials.append(m)
    for p in me.polygons: p.use_smooth = True
    return o
def glb(name, path, c, height=None, width=None, loc=(0, 0, 0), yaw=0.0, depth_axis=None):
    """import a GLB, join to one object, origin at bottom centre, scaled to the given height (or width)"""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=HERE + "assets/" + path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    bpy.context.view_layer.update()
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o.type != 'MESH': bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(meshes) > 1: bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active; o.name = name; o.data.name = name
    vs = [v.co for v in o.data.vertices]
    mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    d = mx - mn
    s = height / d.z if height else width / d.x
    off = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    o.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation(-off))
    o.rotation_mode = 'XYZ'; o.location = loc; o.rotation_euler = (0, 0, R_(yaw)); link(o, c)   # glTF import leaves QUATERNION mode
    for p in o.data.polygons: p.use_smooth = True
    for m in o.data.materials:   # softened: clean animated look
        if m and m.use_nodes:
            for n in m.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED': n.inputs["Roughness"].default_value = max(0.35, n.inputs["Roughness"].default_value)
                if n.type == 'NORMAL_MAP': n.inputs["Strength"].default_value = 0.35
    print("GLB", name, "dims", tuple(round(x * s, 3) for x in d))
    return o

# ------------------------------------------------------------------ materials
WALL = mat("Wall_Blue", (0.50, 0.70, 0.86), 0.7, spec=0.2)
WALL2 = mat("Wall_Blue_Small", (0.46, 0.68, 0.86), 0.7, spec=0.2)
CEIL = mat("Ceiling_White", (0.93, 0.94, 0.95), 0.8)
TRIM = mat("Trim_White", (0.92, 0.92, 0.9), 0.4)
WOODTRIM = mat("Casing_Wood", (0.42, 0.28, 0.17), 0.45)
DOORM = mat("Door_Wood", (0.55, 0.38, 0.24), 0.45)
CHROME = mat("Chrome", (0.85, 0.86, 0.88), 0.18, metal=1.0)
def wood_floor(name, base=(0.62, 0.43, 0.27)):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1.0, 7.0, 1.0)
    br = nt.nodes.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 1.2; br.offset = 0.5
    br.inputs["Color1"].default_value = (*base, 1); br.inputs["Color2"].default_value = (base[0] * 0.86, base[1] * 0.84, base[2] * 0.82, 1)
    br.inputs["Mortar"].default_value = (base[0] * 0.6, base[1] * 0.6, base[2] * 0.6, 1); br.inputs["Mortar Size"].default_value = 0.004
    br.inputs["Brick Width"].default_value = 1.2; br.inputs["Row Height"].default_value = 0.15
    nt.links.new(tc.outputs["Object"], mp.inputs[0]); nt.links.new(mp.outputs[0], br.inputs["Vector"]); nt.links.new(br.outputs["Color"], P.inputs["Base Color"])
    P.inputs["Roughness"].default_value = 0.42
    return m
def tile_floor(name, a=(0.86, 0.87, 0.88), b=(0.80, 0.81, 0.83)):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); br = nt.nodes.new("ShaderNodeTexBrick"); br.offset = 0.0
    br.inputs["Scale"].default_value = 1.0; br.inputs["Brick Width"].default_value = 0.3; br.inputs["Row Height"].default_value = 0.3
    br.inputs["Color1"].default_value = (*a, 1); br.inputs["Color2"].default_value = (*b, 1)
    br.inputs["Mortar"].default_value = (0.55, 0.57, 0.6, 1); br.inputs["Mortar Size"].default_value = 0.003
    nt.links.new(tc.outputs["Object"], br.inputs["Vector"]); nt.links.new(br.outputs["Color"], P.inputs["Base Color"])
    P.inputs["Roughness"].default_value = 0.35
    return m
WOODF = wood_floor("Floor_Wood", (0.52, 0.34, 0.2)); TILEF = tile_floor("Floor_Tile")
WALLTILE = tile_floor("Wall_Tile", (0.80, 0.90, 0.97), (0.76, 0.87, 0.95))

# ------------------------------------------------------------------ HALL / LIVING (y < 0), closet door in the wall y = 0
H = coll("SET_Hall")
WH = 2.6
box("Hall_Floor", (7.0, 7.0, 0.1), (0, -3.5, -0.05), WOODF, H, 0)
box("Hall_Ceiling", (7.0, 7.0, 0.1), (0, -3.5, WH + 0.05), CEIL, H, 0)
# front wall with the closet door opening x[-0.45, 0.45] z[0, 2.05], and a second (closed) door at x = -2.2
DX0, DX1, DZ = -0.45, 0.45, 2.05
box("Hall_Wall_F1", (3.5 + DX0, 0.12, WH), ((-3.5 + DX0) / 2, 0.0, WH / 2), WALL, H, 0)
box("Hall_Wall_F2", (3.5 - DX1, 0.12, WH), ((3.5 + DX1) / 2, 0.0, WH / 2), WALL, H, 0)
box("Hall_Wall_Lintel", (DX1 - DX0, 0.12, WH - DZ), (0, 0.0, (WH + DZ) / 2), WALL, H, 0)
box("Hall_Wall_L", (0.12, 7.0, WH), (-3.5, -3.5, WH / 2), WALL, H, 0)
box("Hall_Wall_R", (0.12, 7.0, WH), (3.5, -3.5, WH / 2), WALL, H, 0)
box("Hall_Wall_B", (7.0, 0.12, WH), (0, -7.0, WH / 2), WALL, H, 0)
for nm, (x0, x1, y) in {"F1": (-3.5, DX0 - 0.07, -0.07), "F2": (DX1 + 0.07, 3.5, -0.07)}.items():
    box("Hall_Base_" + nm, (x1 - x0, 0.015, 0.09), ((x0 + x1) / 2, y, 0.045), TRIM, H, 0.002)
box("Hall_Base_L", (0.015, 7.0, 0.09), (-3.43, -3.5, 0.045), TRIM, H, 0.002)
box("Hall_Base_R", (0.015, 7.0, 0.09), (3.43, -3.5, 0.045), TRIM, H, 0.002)
box("Hall_Cornice", (7.0, 0.05, 0.06), (0, -0.08, WH - 0.03), TRIM, H, 0.003)
# door casing (both faces) and jamb
for side, y in (("H", -0.07), ("C", 0.07)):
    box("Casing_%s_L" % side, (0.07, 0.02, DZ), (DX0 - 0.035, y, DZ / 2), WOODTRIM, H, 0.004)
    box("Casing_%s_R" % side, (0.07, 0.02, DZ), (DX1 + 0.035, y, DZ / 2), WOODTRIM, H, 0.004)
    box("Casing_%s_T" % side, (DX1 - DX0 + 0.14, 0.02, 0.07), (0, y, DZ + 0.035), WOODTRIM, H, 0.004)
box("Jamb_L", (0.02, 0.12, DZ), (DX0 + 0.01, 0, DZ / 2), WOODTRIM, H, 0.002)
box("Jamb_R", (0.02, 0.12, DZ), (DX1 - 0.01, 0, DZ / 2), WOODTRIM, H, 0.002)
box("Jamb_T", (DX1 - DX0, 0.12, 0.02), (0, 0, DZ - 0.01), WOODTRIM, H, 0.002)
# the door: hinge on the left jamb, opens inwards (into y > 0)
piv = bpy.data.objects.new("DoorPivot", None); H.objects.link(piv); piv.location = (DX0 + 0.02, 0.035, 0.0)
DW = DX1 - DX0 - 0.045
leaf = box("Door_Leaf", (DW, 0.04, DZ - 0.03), (DW / 2 + 0.002, 0, (DZ - 0.03) / 2 + 0.008), DOORM, H, 0.004); leaf.parent = piv
for i, (zc, hh) in enumerate(((1.45, 0.75), (0.55, 0.7))):
    for sy in (-1, 1):
        box("Door_Panel_%d_%d" % (i, sy > 0), (DW - 0.22, 0.012, hh), (DW / 2 + 0.002, sy * 0.022, zc), mat("Door_Panel", (0.5, 0.34, 0.21), 0.45), H, 0.006).parent = piv
for sy, nm in ((-1, "H"), (1, "C")):
    rose = cyl("Door_Rose_" + nm, 0.026, 0.012, (DW - 0.07, sy * 0.026, 1.0), CHROME, H, rot=(R_(90), 0, 0)); rose.parent = piv
    neck = cyl("Door_LeverNeck_" + nm, 0.009, 0.05, (DW - 0.07, sy * 0.045, 1.0), CHROME, H, rot=(R_(90), 0, 0)); neck.parent = piv
    lev = cyl("Door_Lever_" + nm, 0.0095, 0.12, (DW - 0.07 - 0.055, sy * 0.068, 1.0), CHROME, H, rot=(0, R_(90), 0)); lev.parent = piv
# a second, closed door on the same wall (other room), for a real hallway
box("Door2_Leaf", (0.84, 0.04, 2.02), (-2.2, -0.075, 1.01), DOORM, H, 0.004)
for x in (-2.66, -1.74): box("Door2_Casing", (0.07, 0.02, 2.1), (x, -0.08, 1.05), WOODTRIM, H, 0.004)
box("Door2_CasingT", (0.99, 0.02, 0.07), (-2.2, -0.08, 2.08), WOODTRIM, H, 0.004)
cyl("Door2_Knob", 0.028, 0.06, (-1.88, -0.11, 1.0), CHROME, H, rot=(R_(90), 0, 0))
# living area: window with a sunny view on the back wall, sofa, rug, side table, framed picture, plant pot, ceiling lights
WIN = img_mat("WindowView", HERE + "assets/window_view.png", 0.5, emit=2.2)
box("Window_View", (1.6, 0.02, 1.25), (0.9, -6.92, 1.45), WIN, H, 0)
for nm, s, l in (("WinFrameT", (1.72, 0.08, 0.06), (0.9, -6.9, 2.1)), ("WinFrameB", (1.72, 0.12, 0.06), (0.9, -6.88, 0.8)),
                 ("WinFrameL", (0.06, 0.08, 1.3), (0.06, -6.9, 1.45)), ("WinFrameR", (0.06, 0.08, 1.3), (1.74, -6.9, 1.45)),
                 ("WinFrameM", (0.04, 0.06, 1.25), (0.9, -6.9, 1.45))):
    box(nm, s, l, TRIM, H, 0.004)
sofa = glb("Sofa", "sofa.glb", H, height=0.85, loc=(-1.9, -6.3, 0), yaw=-90)
box("Rug", (2.4, 1.6, 0.012), (-1.6, -4.5, 0.006), mat("Rug", (0.82, 0.55, 0.38), 0.9), H, 0.003)
box("SideTable", (0.5, 0.5, 0.5), (2.6, -6.3, 0.25), mat("SideTable", (0.95, 0.95, 0.93), 0.4), H, 0.01)
cyl("Lamp_Base", 0.07, 0.3, (2.6, -6.3, 0.65), mat("LampBase", (0.25, 0.45, 0.6), 0.3), H)
cyl("Lamp_Shade", 0.16, 0.2, (2.6, -6.3, 0.9), mat("LampShade", (0.98, 0.95, 0.88), 0.6, emit=(1.0, 0.92, 0.8), es=1.5), H)
PAINT = img_mat("Painting", HERE + "assets/painting.png", 0.45)
box("Hall_Pic_Frame", (0.92, 0.03, 0.7), (-3.43, -3.0, 1.55), WOODTRIM, H, 0.006, rot=(0, 0, R_(90)))
box("Hall_Pic", (0.82, 0.01, 0.6), (-3.41, -3.0, 1.55), PAINT, H, 0, rot=(0, 0, R_(90)))
cyl("Plant_Pot", 0.17, 0.4, (-3.0, -6.5, 0.2), mat("Pot", (0.85, 0.42, 0.25), 0.5), H)
for i, (dx, dy, dz, r) in enumerate(((0, 0, 0.6, 0.22), (0.1, 0.05, 0.85, 0.18), (-0.1, -0.05, 0.8, 0.17), (0.0, 0.1, 1.0, 0.13))):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=r, location=(-3.0 + dx, -6.5 + dy, dz))
    o = bpy.context.object; o.name = "Plant_Leaf%d" % i; link(o, H); o.data.materials.append(mat("Leaf", (0.22, 0.55, 0.28), 0.6))
    d = o.modifiers.new("D", 'DISPLACE'); t = bpy.data.textures.new("PlantN%d" % i, 'VORONOI'); t.noise_scale = 0.08; d.texture = t; d.strength = 0.06
    bpy.ops.object.shade_smooth()
for i, (x, y) in enumerate(((0, -1.5), (0, -4.6))):
    cyl("CeilLamp%d" % i, 0.22, 0.05, (x, y, WH - 0.03), mat("CeilLampM", (1, 1, 1), 0.5, emit=(1, 0.97, 0.92), es=6), H)
    l = bpy.data.lights.new("HallLight%d" % i, 'AREA'); l.energy = 140; l.size = 1.2; l.color = (1.0, 0.96, 0.9)
    lo = bpy.data.objects.new("HallLight%d" % i, l); H.objects.link(lo); lo.location = (x, y, WH - 0.12)
l = bpy.data.lights.new("WindowFill", 'AREA'); l.energy = 180; l.size = 1.6; l.color = (0.92, 0.96, 1.0)
lo = bpy.data.objects.new("WindowFill", l); H.objects.link(lo); lo.location = (0.9, -6.6, 1.5); lo.rotation_euler = (R_(-90), 0, 0)

# ------------------------------------------------------------------ SMALL ROOM shell (y 0.06 .. 1.96, x -0.8 .. 0.8)
S = coll("SET_Small")
RX, RY0, RY1 = 0.8, 0.06, 1.96
box("Small_Wall_L", (0.1, RY1 - RY0 + 0.1, WH), (-RX - 0.05, (RY0 + RY1) / 2, WH / 2), WALL2, S, 0)
box("Small_Wall_R", (0.1, RY1 - RY0 + 0.1, WH), (RX + 0.05, (RY0 + RY1) / 2, WH / 2), WALL2, S, 0)
box("Small_Wall_B", (2 * RX + 0.2, 0.1, WH), (0, RY1 + 0.05, WH / 2), WALL2, S, 0)
box("Small_Ceiling", (2 * RX + 0.2, RY1 - RY0 + 0.2, 0.08), (0, (RY0 + RY1) / 2, WH + 0.04), CEIL, S, 0)
box("Small_Cornice_B", (2 * RX, 0.05, 0.06), (0, RY1 - 0.025, WH - 0.03), TRIM, S, 0.003)
cyl("Small_CeilLamp", 0.16, 0.04, (0, 1.0, WH - 0.02), mat("CeilLampM", (1, 1, 1)), S)
l = bpy.data.lights.new("SmallLight", 'AREA'); l.energy = 60; l.size = 0.8; l.color = (1.0, 0.97, 0.93)
lo = bpy.data.objects.new("SmallLight", l); S.objects.link(lo); lo.location = (0, 1.0, WH - 0.1)

# BATH dressing
B = coll("DRESS_Bath")
box("Bath_Floor", (2 * RX, RY1 - RY0, 0.02), (0, (RY0 + RY1) / 2, 0.01), TILEF, B, 0)
box("Bath_WallTile_B", (2 * RX, 0.012, 1.2), (0, RY1 - 0.006, 0.6), WALLTILE, B, 0)
box("Bath_WallTile_L", (0.012, RY1 - RY0, 1.2), (-RX + 0.006, (RY0 + RY1) / 2, 0.6), WALLTILE, B, 0)
box("Bath_WallTile_R", (0.012, RY1 - RY0, 1.2), (RX - 0.006, (RY0 + RY1) / 2, 0.6), WALLTILE, B, 0)
box("Bath_TileCap", (2 * RX, 0.025, 0.03), (0, RY1 - 0.02, 1.215), TRIM, B, 0.004)
glb("Toilet", "toilet.glb", B, height=0.76, loc=(0.38, RY1 - 0.33, 0.02), yaw=0)
glb("Sink", "sink.glb", B, height=0.86, loc=(-0.38, RY1 - 0.25, 0.02), yaw=0)
box("Mirror_Frame", (0.5, 0.025, 0.66), (-0.38, RY1 - 0.02, 1.58), mat("MirrorFrame", (0.9, 0.9, 0.88), 0.4), B, 0.006)
box("Mirror_Glass", (0.44, 0.01, 0.6), (-0.38, RY1 - 0.037, 1.58), mat("MirrorGlass", (0.75, 0.82, 0.88), 0.08, metal=0.85), B, 0.002)
box("Bath_Pic_Frame", (0.5, 0.025, 0.4), (0.38, RY1 - 0.02, 1.6), WOODTRIM, B, 0.006)
box("Bath_Pic", (0.42, 0.01, 0.32), (0.38, RY1 - 0.036, 1.6), PAINT, B, 0)
cyl("TowelBar", 0.009, 0.5, (RX - 0.04, 0.9, 1.15), CHROME, B, rot=(R_(90), 0, 0))
box("Towel", (0.025, 0.36, 0.5), (RX - 0.055, 0.9, 0.92), mat("Towel", (0.98, 0.98, 0.97), 0.9), B, 0.012)
glb("ToiletPaper", "tp.glb", B, height=0.11, loc=(RX - 0.07, RY1 - 0.62, 0.62), yaw=90)
cyl("TP_Holder", 0.006, 0.14, (RX - 0.03, RY1 - 0.62, 0.68), CHROME, B, rot=(0, R_(90), 0))
cyl("Bin", 0.11, 0.26, (-0.05, RY1 - 0.2, 0.15), mat("BinGrey", (0.35, 0.37, 0.4), 0.35, metal=0.4), B)
box("BathMat", (0.6, 0.4, 0.012), (0.0, 1.0, 0.026), mat("BathMat", (0.35, 0.55, 0.75), 0.95), B, 0.01)

# CLOSET dressing (what he remembers)
C = coll("DRESS_Closet")
box("Closet_Floor", (2 * RX, RY1 - RY0, 0.02), (0, (RY0 + RY1) / 2, 0.01), WOODF, C, 0)
SHELF = mat("Shelf_Wood", (0.40, 0.27, 0.16), 0.45)
box("Closet_Shelf", (2 * RX - 0.04, 0.4, 0.03), (0, RY1 - 0.21, 1.95), SHELF, C, 0.004)
for x in (-0.6, 0.6): box("Closet_Bracket", (0.03, 0.3, 0.2), (x, RY1 - 0.16, 1.84), SHELF, C, 0.004)
cyl("Closet_Rail", 0.014, 2 * RX - 0.05, (0, RY1 - 0.3, 1.78), CHROME, C, rot=(0, R_(90), 0))
# hanging shirts: the MPFB garment tops (rest pose, sleeves angled down like a hanger), flattened, on wire hooks
TOPS = [("Tom.male_casualsuit04", (0.85, 0.25, 0.22)), ("Ray.male_casualsuit06", (0.25, 0.45, 0.75)), ("Ken.male_casualsuit03", (0.55, 0.2, 0.2)),
        ("Tom.male_casualsuit04", (0.95, 0.95, 0.92)), ("Ken.male_casualsuit03", (0.2, 0.32, 0.55)), ("Ray.male_casualsuit06", (0.3, 0.6, 0.35)),
        ("Tom.male_casualsuit04", (0.15, 0.15, 0.18)), ("Ken.male_casualsuit03", (0.7, 0.5, 0.25))]
HOOK = mat("Hanger", (0.75, 0.77, 0.8), 0.3, metal=0.8)
for i, (src, col) in enumerate(TOPS):
    so = bpy.data.objects[src]; me = so.data.copy(); me.name = "Shirt%d" % i
    rig = so.parent; waist = rig.data.bones["root"].head_local.z + 0.06; neck = rig.data.bones["neck01"].head_local.z
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < waist], context='VERTS'); bm.to_mesh(me); bm.free()
    me.materials.clear(); me.materials.append(mat("ShirtM%d" % i, col, 0.75))
    o = bpy.data.objects.new("Closet_Shirt%d" % i, me); C.objects.link(o)
    for p in me.polygons: p.use_smooth = True
    x = -0.66 + i * 0.185
    o.scale = (1.0, 0.45, 1.0)
    o.rotation_euler = (0, 0, R_(90 + (i % 3 - 1) * 6))
    o.location = (x, RY1 - 0.3, 1.78 - 0.05 - (neck - 0.0) * 1.0 + 0.0)
    o.location.z = 1.78 - 0.06 - neck
    sol = o.modifiers.new("Sol", 'SOLIDIFY'); sol.thickness = 0.004
    hk = cyl("Closet_Hook%d" % i, 0.003, 0.07, (x, RY1 - 0.3, 1.77 - 0.035 + 0.0), HOOK, C)
print("SHIRTS ok")
fold = glb("Closet_Folded", "folded.glb", C, width=0.4, loc=(-0.45, RY1 - 0.2, 1.965), yaw=0)
fold2 = glb("Closet_Folded2", "folded.glb", C, width=0.36, loc=(0.05, RY1 - 0.2, 1.965), yaw=180)
CARD = mat("Cardboard", (0.72, 0.52, 0.32), 0.7)
boxc = box("Closet_Box", (0.42, 0.34, 0.3), (0.52, RY1 - 0.21, 1.965 + 0.15), CARD, C, 0.008)
box("Closet_Basket", (0.5, 0.36, 0.34), (-0.4, 0.9, 0.19), mat("BasketBlue", (0.15, 0.4, 0.8), 0.5), C, 0.02)

# PRANK dressing (imagined: closet stripped, toilet just installed, packaging box on the floor)
Pk = coll("DRESS_Prank")
box("Prank_Floor", (2 * RX, RY1 - RY0, 0.02), (0, (RY0 + RY1) / 2, 0.01), TILEF, Pk, 0)
box("Prank_Shelf", (2 * RX - 0.04, 0.4, 0.03), (0, RY1 - 0.21, 1.95), SHELF, Pk, 0.004)
for x in (-0.6, 0.6): box("Prank_Bracket", (0.03, 0.3, 0.2), (x, RY1 - 0.16, 1.84), SHELF, Pk, 0.004)
glb("Prank_Folded", "folded.glb", Pk, width=0.4, loc=(-0.45, RY1 - 0.2, 1.965), yaw=0)
glb("Prank_Toilet", "toilet.glb", Pk, height=0.76, loc=(0.38, RY1 - 0.33, 0.02), yaw=0)
prb = box("Prank_Box", (0.55, 0.5, 0.6), (-0.12, 0.55, 0.32), CARD, Pk, 0.01, rot=(0, 0, R_(-6)))
cyl("Prank_Bucket", 0.14, 0.3, (-0.1, 1.55, 0.17), mat("BucketOrange", (0.95, 0.5, 0.12), 0.45), Pk)

# logo decals (dark logo on cardboard): closet shelf box front, prank box front
def logo_decal(name, parent, w, loc_local, rot_local, c):
    img = bpy.data.images.load(HERE + "../assets/brand/DaKrasFilms_logo_dark.png"); img.pack()
    m = bpy.data.materials.new(name + "_m"); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img
    nt.links.new(t.outputs["Color"], P.inputs["Base Color"]); nt.links.new(t.outputs["Alpha"], P.inputs["Alpha"])
    P.inputs["Roughness"].default_value = 0.7
    try: m.blend_method = 'HASHED'
    except Exception: pass
    hgt = w * 414 / 967
    bpy.ops.mesh.primitive_plane_add(size=1); o = bpy.context.object; o.name = name; link(o, c)
    o.scale = (w, hgt, 1); o.data.materials.append(m)
    o.parent = parent; o.location = loc_local; o.rotation_euler = rot_local
    return o
logo_decal("Logo_ClosetBox", boxc, 0.36, (0, -0.171, 0.0), (R_(90), 0, 0), C)
logo_decal("Logo_PrankBox", prb, 0.48, (0, -0.2515, 0.03), (R_(90), 0, 0), Pk)

# ------------------------------------------------------------------ CLINIC at X0 = 30
K = coll("SET_Clinic"); X0 = 30.0
KW = mat("Clinic_Wall", (0.86, 0.85, 0.93), 0.7, spec=0.2)
box("Clinic_Floor", (6.0, 6.0, 0.1), (X0, -1.0, -0.05), tile_floor("Clinic_FloorM", (0.84, 0.84, 0.87), (0.8, 0.8, 0.84)), K, 0)
box("Clinic_Ceil", (6.0, 6.0, 0.1), (X0, -1.0, 2.75), CEIL, K, 0)
box("Clinic_Wall_B", (6.0, 0.12, 2.7), (X0, 2.0, 1.35), KW, K, 0)
box("Clinic_Wall_L", (0.12, 6.0, 2.7), (X0 - 3.0, -1.0, 1.35), KW, K, 0)
box("Clinic_Wall_R", (0.12, 6.0, 2.7), (X0 + 3.0, -1.0, 1.35), KW, K, 0)
box("Clinic_Wall_F", (6.0, 0.12, 2.7), (X0, -4.0, 1.35), KW, K, 0)
box("Clinic_Base", (6.0, 0.015, 0.09), (X0, 1.93, 0.045), TRIM, K, 0.002)
desk = glb("Clinic_Desk", "desk.glb", K, width=1.4, loc=(X0 + 0.55, 1.62, 0), yaw=0)
mon = glb("Clinic_Monitor", "monitor.glb", K, width=0.62, loc=(X0 + 0.45, 1.6, 0.76), yaw=-12)
for i_ in range(len(mon.data.materials)): mon.data.materials[i_] = mat("MonitorPlastic", (0.03, 0.03, 0.035), 0.4)   # no brand text
glb("Clinic_DocChair", "ochair.glb", K, height=1.05, loc=(X0 + 0.98, 1.0, 0), yaw=-60)
glb("Clinic_PatChair", "chair.glb", K, height=0.92, loc=(X0 - 0.55, 0.25, 0), yaw=-160)
glb("Clinic_Clock", "clock.glb", K, height=0.34, loc=(X0 - 2.93, 0.55, 1.95), yaw=90)
glb("Clinic_FirstAid", "firstaid.glb", K, height=0.5, loc=(X0 - 2.86, -0.35, 1.25), yaw=90)
CAB = mat("Cabinet_White", (0.95, 0.95, 0.96), 0.35)
for i in range(3):
    cx = X0 + 0.15 + i * 0.5
    box("Clinic_Cab%d" % i, (0.48, 0.36, 0.7), (cx, 1.76, 2.05), CAB, K, 0.008)
    box("Clinic_CabH%d" % i, (0.012, 0.02, 0.14), (cx + 0.17, 1.57, 1.86), CHROME, K, 0.003)
box("Clinic_ExamBed", (0.7, 1.9, 0.62), (X0 + 2.4, -0.8, 0.31), mat("ExamBed", (0.35, 0.6, 0.72), 0.45), K, 0.03)
box("Clinic_ExamSheet", (0.6, 1.8, 0.01), (X0 + 2.4, -0.8, 0.625), mat("PaperSheet", (0.97, 0.97, 0.96), 0.8), K, 0.003)
cyl("Clinic_Plant", 0.15, 0.35, (X0 - 2.5, 1.5, 0.175), mat("Pot", (0.85, 0.42, 0.25)), K)
for i in range(2):
    l = bpy.data.lights.new("ClinicLight%d" % i, 'AREA'); l.energy = 160; l.size = 1.5; l.color = (1.0, 0.98, 0.96)
    lo = bpy.data.objects.new("ClinicLight%d" % i, l); K.objects.link(lo); lo.location = (X0 - 0.6 + i * 1.6, 0.2, 2.6)
    cyl("Clinic_CeilPanel%d" % i, 0.25, 0.03, (X0 - 0.6 + i * 1.6, 0.2, 2.69), mat("CeilLampM", (1, 1, 1)), K)
# screen: an emissive plane on the monitor face (the scan image is set in the shots script)
bpy.context.view_layer.update()
vs = [mon.matrix_world @ v.co for v in mon.data.vertices]
print("MONITOR bbox", [round(min(v[i] for v in vs), 3) for i in range(3)], [round(max(v[i] for v in vs), 3) for i in range(3)])

# ------------------------------------------------------------------ world + look
sc.world = bpy.data.worlds.new("World"); sc.world.use_nodes = True
bg = sc.world.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.75, 0.85, 0.95, 1); bg.inputs[1].default_value = 0.35
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920; sc.render.fps = 60
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception as e: print("LOOK", e)
sc.render.use_motion_blur = False
sc.view_settings.exposure = -0.5
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("SETS_DONE")
