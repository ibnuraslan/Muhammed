"""TenDimes sets + props. blender -b build/chars.blend --python 02_sets.py
Sets are laid out along X, one per location:
  CLUB   x=0    stage floor (planks), red velvet curtain, stand microphone (CC-BY), round tables in front
  ROOM   x=30   son's room: light-blue walls, bed (CC-BY), door with frame, window with sky, planks floor, potted plant
  STREET x=60   red brick wall, wall payphone (CC-BY), concrete pavement, kerb, road, street lamp, club poster with our logo
  SUBURB x=90   lawn, pavement, house facade (CC-BY), 1950s car (CC-BY, recoloured black), trees
  CEMET  x=120  lawn, gravestones (CC-BY), casket on a bier with a flower spray, trees
Props: Dime pile (10), Dime pile (2), single Dime, daughter's pile, Handset (separated from the payphone model) + cord."""
import bpy, bmesh, os, math, random
from mathutils import Vector, Matrix
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "common.py")).read())
sc = bpy.context.scene; R = math.radians
random.seed(26)
SETX = dict(CLUB=0.0, ROOM=30.0, STREET=60.0, SUBURB=90.0, CEMET=120.0)
sc["SETX"] = SETX

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c

def mat(name, rgb, rough=0.6, metal=0.0, emit=None):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; P = m.node_tree.nodes["Principled BSDF"]
    P.inputs['Base Color'].default_value = (*rgb, 1); P.inputs['Roughness'].default_value = rough; P.inputs['Metallic'].default_value = metal
    if emit: P.inputs['Emission Color'].default_value = (*emit, 1); P.inputs['Emission Strength'].default_value = 1.0
    return m

def ph_mat(name, asset, scale=1.0, tint=None, bump=0.3):
    """Poly Haven texture set -> material (diffuse + normal, low bump, rough >= 0.35)"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    d = ASSETS.replace("/assets", "/ph") + "/" + asset + "/textures/"
    fs = os.listdir(d)
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs['UV'], mp.inputs['Vector'])
    dif = next(f for f in fs if "diff" in f)
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(d + dif); nt.links.new(mp.outputs[0], t.inputs[0])
    if tint:
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        mx.inputs['B'].default_value = (*tint, 1); nt.links.new(t.outputs['Color'], mx.inputs['A']); nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])
    else:
        nt.links.new(t.outputs['Color'], P.inputs['Base Color'])
    nr = [f for f in fs if "nor_gl" in f]
    if nr:
        tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = bpy.data.images.load(d + nr[0]); tn.image.colorspace_settings.name = 'Non-Color'
        nt.links.new(mp.outputs[0], tn.inputs[0]); nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = bump
        nt.links.new(tn.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs[0], P.inputs['Normal'])
    P.inputs['Roughness'].default_value = 0.7
    return m

def box(name, c, size, m, col, bevel=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=c, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = 3; b.limit_method = 'ANGLE'
    o.data.materials.append(m); move(o, col); return o

def plane(name, c, sx, sy, m, col, rot=(0, 0, 0), uv01=False):
    bpy.ops.mesh.primitive_plane_add(size=1, location=c, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (sx, sy, 1); bpy.ops.object.transform_apply(scale=True)
    if not uv01:
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.uv.cube_project(cube_size=1.0); bpy.ops.object.mode_set(mode='OBJECT')
    o.data.materials.append(m); move(o, col); return o

def move(o, col):
    for c in list(o.users_collection): c.objects.unlink(o)
    col.objects.link(o)

def import_glb(path, name, col, target_h=None, target_w=None, loc=(0, 0, 0), rotz=0.0, join=True, keep_mats=True, drop=()):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in [o for o in new if any(d in o.name for d in drop)]:
        new.remove(o); bpy.data.objects.remove(o, do_unlink=True)
    meshes = [o for o in new if o.type == 'MESH']
    for o in meshes:
        Mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = Mw
    for o in new:
        if o.type != 'MESH': bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if join and len(meshes) > 1:
        bpy.ops.object.join(); meshes = [bpy.context.view_layer.objects.active]
    vs = [v.co for o in meshes for v in o.data.vertices]
    mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    sz = mx - mn
    s = target_h / sz.z if target_h else (target_w / max(sz.x, sz.y) if target_w else 1.0)
    base = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    for o in meshes:
        for v in o.data.vertices: v.co = (v.co - base) * s
        o.location = loc; o.rotation_euler = (0, 0, rotz); move(o, col)
    if join: meshes[0].name = name
    print("GLB", name, "size", tuple(round(c * s, 3) for c in sz))
    return meshes[0] if join else meshes

PH_CACHE = {}
def append_ph(asset, name, col, loc, rotz=0.0, scale=1.0):
    """Poly Haven model appended ONCE into an unlinked collection, then placed as collection instances (trees are 1.5M polys)"""
    if asset not in PH_CACHE:
        p = ASSETS.replace("/assets", "/ph") + "/" + asset + "/" + asset + "_1k.blend"
        with bpy.data.libraries.load(p, link=False) as (df, dt):
            dt.objects = [n for n in df.objects]
        pc = bpy.data.collections.new("PH_" + asset)
        for o in dt.objects:
            if o and o.type in ('MESH', 'EMPTY'): pc.objects.link(o)
        PH_CACHE[asset] = pc
    root = bpy.data.objects.new(name, None); col.objects.link(root)
    root.instance_type = 'COLLECTION'; root.instance_collection = PH_CACHE[asset]
    root.location = loc; root.rotation_euler = (0, 0, rotz); root.scale = (scale,) * 3
    return root

def soften(m, sat=1.0):
    """anim look on imported materials: rough >= 0.4, normal strength low"""
    if not m or not m.use_nodes: return
    for n in m.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            if not n.inputs['Roughness'].links: n.inputs['Roughness'].default_value = max(0.4, n.inputs['Roughness'].default_value)
        if n.type == 'NORMAL_MAP': n.inputs['Strength'].default_value = min(0.35, n.inputs['Strength'].default_value)

# ====================================================================== CLUB (x=0): stage faces -Y, singer at (0,0)
C = coll("SET_CLUB"); X = SETX["CLUB"]
M_PLANK = ph_mat("M_StagePlanks", "brown_planks_09", 2.0, tint=(1.0, 0.85, 0.7))
plane("Club_Stage", (X, 0.5, 0.0), 10, 7, M_PLANK, C)
box("Club_StageFront", (X, -3.05, -0.35), (10, 0.1, 0.7), mat("M_StageFront", (0.18, 0.06, 0.04), 0.5), C, 0.01)
plane("Club_FloorHall", (X, -8, -0.7), 14, 10, mat("M_HallFloor", (0.25, 0.1, 0.08), 0.6), C)
# curtain: a pleated sheet (sine folds) behind the singer
bm = bmesh.new(); W, H, NX, NZ = 12.0, 6.0, 240, 2
verts = [[bm.verts.new((X - W / 2 + W * i / NX, 2.6 + 0.09 * math.sin(i / NX * W * 2 * math.pi / 0.45), H * k / NZ)) for k in range(NZ + 1)] for i in range(NX + 1)]
for i in range(NX):
    for k in range(NZ): bm.faces.new((verts[i][k], verts[i + 1][k], verts[i + 1][k + 1], verts[i][k + 1]))
me = bpy.data.meshes.new("Club_Curtain"); bm.to_mesh(me); bm.free()
cur = bpy.data.objects.new("Club_Curtain", me); C.objects.link(cur)
for p in me.polygons: p.use_smooth = True
mc = mat("M_Velvet", (0.55, 0.03, 0.04), 0.75); mc.node_tree.nodes["Principled BSDF"].inputs['Sheen Weight'].default_value = 0.6
mc.node_tree.nodes["Principled BSDF"].inputs['Sheen Tint'].default_value = (1.0, 0.5, 0.5, 1)
me.materials.append(mc)
# gold valance on top + side drapes (pleated)
box("Club_Valance", (X, 2.45, 4.6), (12, 0.25, 0.8), mat("M_Gold", (0.75, 0.5, 0.15), 0.35, 0.8), C, 0.03)
mic = import_glb(ASSETS.replace("/assets", "/assets2") + "/mic.glb", "Club_Mic", C, target_h=1.62, loc=(X, -0.62, 0.0), rotz=R(180))
for m in mic.data.materials: soften(m)
M_DARKWOOD = mat("M_DarkWood", (0.12, 0.05, 0.025), 0.3)
bpy.ops.mesh.primitive_cylinder_add(radius=0.24, depth=0.035, vertices=48, location=(X + 0.62, -0.30, 0.76)); o = bpy.context.active_object; o.name = "Club_SideTableTop"
o.data.materials.append(M_DARKWOOD); move(o, C); b = o.modifiers.new("bev", 'BEVEL'); b.width = 0.008; b.segments = 3
bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=0.74, location=(X + 0.62, -0.30, 0.37)); o = bpy.context.active_object; o.name = "Club_SideTableStem"; o.data.materials.append(M_BRASS0 := mat("M_Brass", (0.8, 0.6, 0.25), 0.3, 1.0)); move(o, C)
bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=0.03, vertices=48, location=(X + 0.62, -0.30, 0.015)); o = bpy.context.active_object; o.name = "Club_SideTableFoot"; o.data.materials.append(M_BRASS0); move(o, C)
bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.16, vertices=32, location=(X + 0.72, -0.20, 0.778 + 0.08)); o = bpy.context.active_object; o.name = "Club_Glass"
o.data.materials.append(mat("M_GlassWater", (0.85, 0.9, 0.95), 0.1)); move(o, C)
sc["TABLE_TOP"] = [X + 0.56, -0.40, 0.778]
# round tables with lamps in the hall (camera looks over them in wides)
for i, (tx, ty) in enumerate([(-2.6, -5.2), (2.4, -5.6), (-0.4, -6.8), (4.0, -7.6), (-4.4, -7.4)]):
    t = append_ph("round_wooden_table_01", "Club_Table%d" % i, C, (X + tx, ty, -0.7), rotz=random.random() * 3)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=0.22, location=(X + tx, ty, -0.7 + 0.86))
    lmp = bpy.context.active_object; lmp.name = "Club_TableLamp%d" % i
    lmp.data.materials.append(mat("M_LampShade", (1.0, 0.75, 0.4), 0.5, emit=(1.0, 0.7, 0.35))); move(lmp, C)

# ====================================================================== ROOM (x=30): son's room, door on the right wall
C = coll("SET_ROOM"); X = SETX["ROOM"]
plane("Room_Floor", (X, 0, 0), 7, 7, ph_mat("M_RoomPlanks", "brown_planks_09", 2.5), C)
M_WALL = mat("M_RoomWall", (0.45, 0.62, 0.78), 0.8)
box("Room_WallBack", (X, 2.2, 1.5), (7, 0.1, 3.0), M_WALL, C)
box("Room_WallLeft", (X - 2.6, 0, 1.5), (0.1, 7, 3.0), M_WALL, C)
# right wall with a door opening (x = X+2.6, door centre y = 0.4, 0.95 m wide, 2.1 m high)
DY, DW, DH = 0.4, 0.95, 2.1
box("Room_WallRightA", (X + 2.6, (-3.5 + DY - DW / 2) / 2, 1.5), (0.1, (DY - DW / 2) + 3.5, 3.0), M_WALL, C)
box("Room_WallRightB", (X + 2.6, (3.5 + DY + DW / 2) / 2, 1.5), (0.1, 3.5 - (DY + DW / 2), 3.0), M_WALL, C)
box("Room_WallRightTop", (X + 2.6, DY, (3.0 + DH) / 2), (0.1, DW, 3.0 - DH), M_WALL, C)
M_TRIM = mat("M_Trim", (0.92, 0.92, 0.9), 0.4)
for nm, c, s in (("L", (X + 2.55, DY - DW / 2 - 0.04, DH / 2), (0.14, 0.08, DH)), ("R", (X + 2.55, DY + DW / 2 + 0.04, DH / 2), (0.14, 0.08, DH)), ("T", (X + 2.55, DY, DH + 0.04), (0.14, DW + 0.16, 0.08))):
    box("Room_DoorFrame" + nm, c, s, M_TRIM, C, 0.01)
door = box("Room_Door", (X + 2.6, DY, DH / 2), (0.045, DW - 0.02, DH - 0.02), mat("M_Door", (0.55, 0.36, 0.2), 0.5), C, 0.008)
# hinge at the back edge: set origin there so it can swing open
bpy.context.view_layer.objects.active = door
sc.cursor.location = (X + 2.6, DY + DW / 2 - 0.01, 0); bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
knob = bpy.data.objects.new("Room_DoorKnob", None); C.objects.link(knob)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=(X + 2.55, DY - DW / 2 + 0.1, 1.0)); kb = bpy.context.active_object; kb.name = "Room_DoorKnobMesh"
kb.data.materials.append(mat("M_Brass", (0.8, 0.6, 0.25), 0.3, 1.0)); move(kb, C); kb.parent = door; kb.matrix_parent_inverse = door.matrix_world.inverted()
# hallway behind the door (lit, not a void)
box("Room_Hall", (X + 4.2, DY, 1.5), (3.0, 3.0, 3.0), mat("M_HallWall", (0.85, 0.82, 0.72), 0.8), C)
for p in bpy.data.objects["Room_Hall"].data.polygons: p.flip()
# window on the back wall with sky behind
box("Room_WindowFrame", (X - 0.9, 2.14, 1.6), (1.3, 0.06, 1.2), M_TRIM, C, 0.01)
plane("Room_WindowSky", (X - 0.9, 2.1, 1.6), 1.16, 1.06, mat("M_WinSky", (0.6, 0.85, 1.0), 0.5, emit=(0.55, 0.8, 1.0)), C, rot=(R(90), 0, 0))
box("Room_WindowBar", (X - 0.9, 2.09, 1.6), (0.04, 0.03, 1.06), M_TRIM, C)
bed = import_glb(ASSETS.replace("/assets", "/assets2") + "/bed.glb", "Room_Bed", C, target_w=2.1, loc=(X - 0.6, 0.9, 0.0), rotz=0.0)
for m in bed.data.materials: soften(m)
append_ph("potted_plant_02", "Room_Plant", C, (X - 2.2, 1.8, 0.0))
append_ph("painted_wooden_chair_01", "Room_Chair", C, (X + 1.7, 1.7, 0.0), rotz=R(200))

# ====================================================================== STREET (x=60): brick wall along y=0.6, payphone on it
C = coll("SET_STREET"); X = SETX["STREET"]
wall = box("Street_Wall", (X, 0.75, 2.5), (14, 0.3, 5.0), ph_mat("M_Brick", "red_brick_03", 3.0, bump=0.3), C)
bpy.context.view_layer.objects.active = wall; bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.uv.cube_project(cube_size=1.0); bpy.ops.object.mode_set(mode='OBJECT')
M_CONC = mat("M_Pavement", (0.62, 0.62, 0.6), 0.8)
plane("Street_Pavement", (X, -1.4, 0.0), 14, 4.0, M_CONC, C)
box("Street_Kerb", (X, -3.45, -0.06), (14, 0.15, 0.12), mat("M_Kerb", (0.7, 0.7, 0.68), 0.7), C, 0.01)
plane("Street_Road", (X, -7.0, -0.14), 14, 7.0, mat("M_Asphalt", (0.12, 0.12, 0.13), 0.8), C)
# pavement slab joints
for i in range(-7, 8):
    box("Street_Joint%d" % (i + 7), (X + i * 1.0, -1.4, 0.001), (0.012, 4.0, 0.002), mat("M_Joint", (0.4, 0.4, 0.4), 0.9), C)
pay = import_glb(ASSETS + "/payphone.glb", "Street_Payphone", C, target_h=None, join=False, loc=(0, 0, 0))
# the model: housing + (handset & cord). scale from housing height 260 units -> 0.62 m
hous = max(pay, key=lambda o: len(o.data.polygons)); rec = [o for o in pay if o is not hous][0]
vs = [v.co for v in hous.data.vertices]; hh = max(v.z for v in vs) - min(v.z for v in vs)
s = 0.62 / hh
for o in pay:
    for v in o.data.vertices: v.co *= s
vs = [v.co for v in hous.data.vertices]
hmn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs))); hmx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
print("PAY housing", hmn, hmx)
hous.name = "Street_Payphone"; rec.name = "Street_PayHandsetCord"
# split handset vs cord (loose parts): keep each as its own object
bpy.ops.object.select_all(action='DESELECT'); rec.select_set(True); bpy.context.view_layer.objects.active = rec
bpy.ops.mesh.separate(type='LOOSE')
parts = [o for o in bpy.data.objects if o.name.startswith("Street_PayHandsetCord")]
for o in parts:
    vv = [v.co for v in o.data.vertices]
    print("PAYPART", o.name, len(vv), [round(min(v[i] for v in vv), 3) for i in range(3)], [round(max(v[i] for v in vv), 3) for i in range(3)])
M_PAYM = mat("M_PayMetal", (0.55, 0.57, 0.6), 0.38, 0.85); M_PAYD = mat("M_PayDark", (0.05, 0.05, 0.055), 0.4)
for o in pay + parts:
    o.data.materials.clear(); o.data.materials.append(M_PAYM if o is hous else M_PAYD)
# coin ledge under the phone (holds the last two dimes in S10)

PAYROOT = bpy.data.objects.new("Street_PayRoot", None); C.objects.link(PAYROOT)
for o in pay + parts: o.parent = PAYROOT
PAYROOT.location = (X, 0.6 - hmx.y - 0.002, 0.55)
sc["PAY_PARTS"] = [o.name for o in parts]
led = box("Street_PayLedge", (X + 0.02, 0.6 - 0.11, PAYROOT.location.z + hmn.z - 0.035), (0.50, 0.22, 0.03), M_PAYM, C, 0.004)
sc["LEDGE_TOP"] = list(Vector((X + 0.12, 0.6 - 0.15, PAYROOT.location.z + hmn.z - 0.02)))
sc["PAY_BOX"] = [list(hmn), list(hmx)]
# logo poster on the brick wall (dark logo on a cream club poster), right of the payphone
pst = plane("Street_Poster", (X + 1.6, 0.585, 1.75), 1.0, 1.4, mat("M_PosterPaper", (0.95, 0.9, 0.75), 0.7), C, rot=(R(90), 0, 0))
logo = bpy.data.images.load(REPO + "/assets/brand/DaKrasFilms_logo_dark.png"); logo.name = "DaKrasFilms_logo_dark"
lm = bpy.data.materials.new("M_LogoPoster"); lm.use_nodes = True; nt = lm.node_tree; nt.nodes.clear()
o_ = nt.nodes.new("ShaderNodeOutputMaterial"); t_ = nt.nodes.new("ShaderNodeTexImage"); t_.image = logo; t_.extension = 'CLIP'
pr = nt.nodes.new("ShaderNodeBsdfPrincipled"); pr.inputs["Roughness"].default_value = 0.7
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx_ = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(t_.outputs["Color"], pr.inputs["Base Color"]); nt.links.new(t_.outputs["Alpha"], mx_.inputs[0])
nt.links.new(tr.outputs[0], mx_.inputs[1]); nt.links.new(pr.outputs[0], mx_.inputs[2]); nt.links.new(mx_.outputs[0], o_.inputs[0])
plane("Street_PosterLogo", (X + 1.6, 0.58, 1.95), 0.86, 0.86 * 414 / 967, lm, C, rot=(R(90), 0, 0), uv01=True)
# a red band + a simple microphone silhouette drawn as shapes (no text) under the logo
box("Street_PosterBand", (X + 1.6, 0.582, 1.4), (0.86, 0.004, 0.22), mat("M_PosterRed", (0.7, 0.08, 0.06), 0.6), C)
append_ph("tree_small_02", "Street_Tree", C, (X + 5.0, -3.0, 0.0), scale=0.9)

# ====================================================================== SUBURB (x=90): lawn, pavement along x, house behind, car at kerb
C = coll("SET_SUBURB"); X = SETX["SUBURB"]
M_GRASS = ph_mat("M_Grass", "grass_path_2", 6.0, tint=(0.75, 1.0, 0.6))
plane("Sub_Lawn", (X, 30, 0.0), 28, 60, M_GRASS, C)   # x 76..104
plane("Sub_Pavement", (X, -1.0, 0.01), 40, 2.0, M_CONC, C)
box("Sub_Kerb", (X, -2.05, -0.03), (40, 0.15, 0.12), mat("M_Kerb", (0.7, 0.7, 0.68), 0.7), C, 0.01)
plane("Sub_Road", (X, -6.0, -0.1), 40, 8.0, mat("M_Asphalt", (0.12, 0.12, 0.13), 0.8), C)
for i in range(-20, 21):
    box("Sub_Joint%d" % (i + 20), (X + i * 1.0, -1.0, 0.012), (0.012, 2.0, 0.002), mat("M_Joint", (0.4, 0.4, 0.4), 0.9), C)
house = import_glb(ASSETS.replace("/assets", "/assets2") + "/house.glb", "Sub_House", C, target_h=None, loc=(X + 1.0, 9.0, 0.0))
for m in house.data.materials: soften(m)
car = import_glb(ASSETS + "/car.glb", "Sub_Car", C, target_w=5.0, drop=("Light_0", "Bulb", "Floor_0"), loc=(X + 3.2, -3.1, -0.1), rotz=R(90))
for m in car.data.materials:
    soften(m)
    if m.name.startswith("aiStandardSurface17"):
        P = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        for l in list(P.inputs['Base Color'].links): m.node_tree.links.remove(l)
        P.inputs['Base Color'].default_value = (0.015, 0.015, 0.018, 1); P.inputs['Roughness'].default_value = 0.25
        P.inputs['Metallic'].default_value = 0.3
    if m.name.startswith("Sticker") or m.name.startswith("lambert1"):
        P = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        for l in list(P.inputs['Base Color'].links): m.node_tree.links.remove(l)
        P.inputs['Base Color'].default_value = (0.7, 0.7, 0.7, 1)
for i, (tx, ty, sc_) in enumerate([(-6, 4, 1.2), (8, 5, 1.0), (-12, 7, 1.3), (14, 3.5, 1.1)]):
    append_ph("tree_small_02", "Sub_Tree%d" % i, C, (X + tx, ty, 0.0), rotz=random.random() * 6, scale=sc_)

# ====================================================================== CEMETERY (x=120): casket on a bier at (0,0) running along x
C = coll("SET_CEMET"); X = SETX["CEMET"]
plane("Cem_Lawn", (X + 37.5, 20, 0.0), 105, 120, M_GRASS, C)   # x 105..210, clear of the suburb set
gr = import_glb(ASSETS + "/graves.glb", "Cem_Graves", C, join=False, loc=(0, 0, 0))
for i, o in enumerate(gr):
    vv = [v.co for v in o.data.vertices]; cx = sum((v for v in vv), Vector()) / len(vv)
    for v in o.data.vertices: v.co -= Vector((cx.x, cx.y, 0))
    o.name = "Cem_Grave%d" % i
for m in {m for o in gr for m in o.data.materials}: soften(m)
spots = [(-3.2, 3.5, 0.2), (-1.0, 4.2, -0.1), (1.6, 3.8, 0.15), (3.8, 4.5, -0.2), (-5.0, 5.5, 0.1), (5.5, 2.8, 0.0), (0.4, 6.5, 0.1), (-2.4, 7.0, -0.1)]
src = list(gr)
for i, (gx, gy, rz) in enumerate(spots):
    o = src[i % len(src)] if i < len(src) else src[i % len(src)].copy()
    if o.name not in C.objects: C.objects.link(o)
    o.location = (X + gx, gy, 0.0); o.rotation_euler = (0, 0, R(90) + rz); o.scale = (1.0,) * 3
for i, (tx, ty, s_) in enumerate([(-7, 9, 1.4), (6, 10, 1.2), (-11, 5, 1.1), (10, 6, 1.3)]):
    append_ph("tree_small_02", "Cem_Tree%d" % i, C, (X + tx, ty, 0.0), rotz=random.random() * 6, scale=s_)
# casket: polished wood, rounded lid, brass rails; long axis along x; lid closed (we never show the body inside)
M_WOOD = mat("M_CasketWood", (0.10, 0.035, 0.015), 0.25)
M_BRASS = mat("M_Brass", (0.8, 0.6, 0.25), 0.3, 1.0)
CZ = 0.62
# draped dark stand: a cloth-covered plinth to the ground (no shelves, no legs)
M_DRAPE = mat("M_Drape", (0.035, 0.012, 0.015), 0.85)
dr = box("Cem_BierTop", (X, 0, (CZ - 0.01) / 2), (2.18, 0.70, CZ - 0.01), M_DRAPE, C, 0.02)
bm = bmesh.new()                                  # a soft hanging skirt with folds around the plinth
NF = 120; Hs = CZ - 0.02
pts = []
for i in range(NF):
    u = i / NF; per = 2 * (2.2 + 0.72)
    d = u * per
    if d < 2.2: p = Vector((-1.1 + d, -0.36, 0))
    elif d < 2.2 + 0.72: p = Vector((1.1, -0.36 + (d - 2.2), 0))
    elif d < 4.4 + 0.72: p = Vector((1.1 - (d - 2.92), 0.36, 0))
    else: p = Vector((-1.1, 0.36 - (d - 5.12), 0))
    n = Vector((0 if abs(p.x) < 1.09 else (1 if p.x > 0 else -1), 0 if abs(p.y) < 0.355 else (1 if p.y > 0 else -1), 0))
    off = 0.012 * (1 + math.sin(i * 1.7))
    pts.append((p + n * off, p + n * (off + 0.015)))
top_v = [bm.verts.new((X + a.x, a.y, Hs + 0.005)) for a, b in pts]
bot_v = [bm.verts.new((X + b.x, b.y, 0.0)) for a, b in pts]
for i in range(NF):
    bm.faces.new((top_v[i], top_v[(i + 1) % NF], bot_v[(i + 1) % NF], bot_v[i]))
me = bpy.data.meshes.new("Cem_Skirt"); bm.to_mesh(me); bm.free()
sk = bpy.data.objects.new("Cem_Skirt", me); C.objects.link(sk); me.materials.append(M_DRAPE)
for p_ in me.polygons: p_.use_smooth = True
cb = box("Cem_Casket", (X, 0, CZ + 0.2), (2.05, 0.6, 0.4), M_WOOD, C, 0.03)
lid = box("Cem_CasketLid", (X, 0, CZ + 0.45), (2.08, 0.62, 0.12), M_WOOD, C, 0.05)
bpy.context.view_layer.objects.active = lid
sd = lid.modifiers.new("sub", 'SUBSURF'); sd.levels = 2
for dy in (-0.32, 0.32):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=1.7, location=(X, dy, CZ + 0.22), rotation=(0, R(90), 0))
    o = bpy.context.active_object; o.name = "Cem_CasketRail"; o.data.materials.append(M_BRASS); move(o, C)
# flower spray on the lid: clusters of petals (white roses, red roses, greens)
FLW = [mat("M_FlowerWhite", (0.95, 0.95, 0.92), 0.5), mat("M_FlowerRed", (0.75, 0.04, 0.08), 0.5), mat("M_FlowerPink", (0.95, 0.5, 0.6), 0.5)]
LEAF = mat("M_Leaf", (0.08, 0.3, 0.06), 0.5)
bm = bmesh.new()
for i in range(70):
    a = random.random() * 2 * math.pi; r = random.random() ** 0.6
    p = Vector((X - 0.35 + 0.42 * r * math.cos(a), 0.2 * r * math.sin(a), CZ + 0.52 + 0.09 * (1 - r * r)))
    res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.045 + 0.015 * random.random())
    for v in res['verts']: v.co = p + Vector((v.co.x, v.co.y, v.co.z * 0.75)) + Vector((0, 0, 0.004 * math.sin(v.co.x * 160) * math.cos(v.co.y * 160)))
me = bpy.data.meshes.new("Cem_Flowers"); bm.to_mesh(me); bm.free()
fl = bpy.data.objects.new("Cem_Flowers", me); C.objects.link(fl)
for m in FLW: me.materials.append(m)
for p in me.polygons: p.material_index = (p.index // 80) % 3; p.use_smooth = True
bm = bmesh.new()
for i in range(60):
    a = random.random() * 2 * math.pi; r = 0.5 + 0.5 * random.random()
    p = Vector((X - 0.35 + 0.55 * r * math.cos(a), 0.27 * r * math.sin(a), CZ + 0.52))
    d = Vector((math.cos(a), math.sin(a), 0.15)).normalized()
    v1 = bm.verts.new(p); v2 = bm.verts.new(p + d * 0.16 + Vector((-d.y, d.x, 0)) * 0.035); v3 = bm.verts.new(p + d * 0.2); v4 = bm.verts.new(p + d * 0.16 - Vector((-d.y, d.x, 0)) * 0.035)
    bm.faces.new((v1, v2, v3, v4))
me = bpy.data.meshes.new("Cem_Leaves"); bm.to_mesh(me); bm.free()
lv = bpy.data.objects.new("Cem_Leaves", me); C.objects.link(lv); me.materials.append(LEAF)
lv.modifiers.new("sol", 'SOLIDIFY').thickness = 0.003
# ====================================================================== PROPS
P = coll("PROPS")
M_DIME = mat("M_Dime", (0.82, 0.83, 0.85), 0.32, 1.0)
def coin_bm(bm, Mx):
    r = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=40, radius1=0.00895, radius2=0.00895, depth=0.00135, matrix=Mx)
    return r
def pile(name, n, spread=0.022, seed=1):
    random.seed(seed); bm = bmesh.new(); pts = []
    for i in range(n):
        for _ in range(200):
            q = Vector((random.uniform(-spread, spread), random.uniform(-spread, spread)))
            if all((q - p).length > 0.0135 for p in pts) or len(pts) < 1: break
        lay = sum(1 for p in pts if (q - p).length < 0.018)
        pts.append(q)
        Mx = Matrix.Translation((q.x, q.y, 0.0007 + lay * 0.0014)) @ Matrix.Rotation(random.uniform(-0.06, 0.06), 4, 'X')
        coin_bm(bm, Mx)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); P.objects.link(o); me.materials.append(M_DIME)
    b = o.modifiers.new("bev", 'BEVEL'); b.width = 0.0003; b.segments = 2
    for p in me.polygons: p.use_smooth = True
    return o
pile("DimePile10", 10, 0.021, 3); pile("DimePile2", 2, 0.012, 5); pile("DimePileD", 10, 0.021, 7)
bm = bmesh.new(); coin_bm(bm, Matrix.Rotation(R(90), 4, 'X')); me = bpy.data.meshes.new("Dime"); bm.to_mesh(me); bm.free()
d1 = bpy.data.objects.new("Dime", me); P.objects.link(d1); me.materials.append(M_DIME)
for p in me.polygons: p.use_smooth = True
for o in P.objects: o.location = (0, -30, -5)
bpy.ops.wm.save_as_mainfile(filepath=BUILD + "/sets.blend")
print("SETS_OK")
