"""Room, piano, props, lights, world, materials.  blender -b composer.blend --python 02_build_scene.py -- <assets_dir> <out.blend>
assets_dir holds glb/*.glb (find_models.py) and ph/ (fetch_polyhaven.py)."""
import sys, os, math, random
import bpy
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]
AS, OUT = a[0], a[1]
HERE = os.path.dirname(os.path.abspath(__file__)); TEX = os.path.join(HERE, "..", "assets", "tex")
R_ = math.radians; sc = bpy.context.scene; RND = random.Random(8)
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.fps, sc.render.fps_base = 60, 1.0; sc.frame_start, sc.frame_end = 1, 1590
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'

def bbox(objs):
    pts = [o.matrix_world @ v.co for o in objs if o.type == 'MESH' for v in o.data.vertices]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])

def imp(name, coll):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(AS, "glb", name + ".glb"))
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        for c in o.users_collection: c.objects.unlink(o)
        coll.objects.link(o)
    return new

def bake_group(new, name, scale, drop=()):
    """apply transforms, join meshes into one object with origin at bottom centre"""
    for o in list(new):
        if o.type == 'MESH' and any(k in o.name for k in drop) or (o.type == 'MESH' and any(k in [m.name for m in o.data.materials if m] for k in drop)):
            bpy.data.objects.remove(o); new.remove(o)
    meshes = [o for o in new if o.type == 'MESH']
    bpy.context.view_layer.update()
    for o in meshes:
        M = o.matrix_world.copy(); o.parent = None; o.matrix_world = M
    for o in [o for o in new if o.type != 'MESH']:
        bpy.data.objects.remove(o)
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(meshes) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active; ob.name = name; ob.data.name = name
    mn, mx = bbox([ob])
    ob.data.transform(Matrix.Translation(-Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))))
    ob.data.transform(Matrix.Scale(scale, 4))
    ob.location = (0, 0, 0)
    return ob

def ph_mat(name, pid, scale=1.0, tint=None, rough_mul=1.0, bump=0.3):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; n, l = nt.nodes, nt.links; P = n["Principled BSDF"]
    d = os.path.join(AS, "ph", pid, "textures")
    tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale, scale, scale)
    l.new(tc.outputs['UV'], mp.inputs['Vector'])
    def img(suffix, cs):
        f = [x for x in os.listdir(d) if ("_%s_" % suffix) in x][0]
        t = n.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(d, f), check_existing=True)
        t.image.colorspace_settings.name = cs; l.new(mp.outputs['Vector'], t.inputs['Vector']); return t
    dif = img("diff", 'sRGB'); src = dif.outputs['Color']
    if tint:
        mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        mx.inputs['B'].default_value = (*tint, 1); l.new(src, mx.inputs['A']); src = mx.outputs['Result']
    l.new(src, P.inputs['Base Color'])
    try:
        ro = img("rough", 'Non-Color'); mm = n.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = rough_mul
        l.new(ro.outputs['Color'], mm.inputs[0]); l.new(mm.outputs[0], P.inputs['Roughness'])
    except IndexError: pass
    try:
        no = img("nor_gl", 'Non-Color'); nm = n.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = bump * 2
        l.new(no.outputs['Color'], nm.inputs['Color']); l.new(nm.outputs['Normal'], P.inputs['Normal'])
    except IndexError: pass
    return m

def simple_mat(name, col, rough=0.5, metal=0.0, emit=None, es=0.0, alpha=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; P = m.node_tree.nodes["Principled BSDF"]
    P.inputs['Base Color'].default_value = (*col, 1); P.inputs['Roughness'].default_value = rough; P.inputs['Metallic'].default_value = metal
    if emit: P.inputs['Emission Color'].default_value = (*emit, 1); P.inputs['Emission Strength'].default_value = es
    return m

def box(name, size, loc, mat, coll, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.active_object; o.name = name
    o.scale = size; bpy.ops.object.transform_apply(scale=True)
    if bevel: md = o.modifiers.new("bev", 'BEVEL'); md.width = bevel; md.segments = 2
    o.data.materials.append(mat)
    for c in o.users_collection: c.objects.unlink(o)
    coll.objects.link(o); return o

def uv_cube_project(o, s=1.0):
    bpy.context.view_layer.objects.active = o
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=s); bpy.ops.object.mode_set(mode='OBJECT')

def newcoll(n):
    c = bpy.data.collections.new(n); sc.collection.children.link(c); return c
C_SET, C_PROPS, C_FX, C_XR = newcoll("Set"), newcoll("Props"), newcoll("FX"), newcoll("XRay")

# ---------------------------------------------------------------- piano: keyboard faces -Y, front edge at y=0, floor at z=0
piano = bake_group(imp("piano", C_SET), "Piano", 0.0095)
mn, mx = bbox([piano]); piano.data.transform(Matrix.Translation((0, -mn.y, 0)))
mn, mx = bbox([piano]); print("PIANO", tuple(mn), tuple(mx))
# keyboard height: highest hit just behind the front edge in the middle
dg = bpy.context.evaluated_depsgraph_get(); bpy.context.view_layer.update()
def ray_down(o, x, y, z0=3.0):
    inv = o.matrix_world.inverted(); ok, loc, nrm, idx = o.ray_cast(inv @ Vector((x, y, z0)), Vector((0, 0, -1)))
    return (o.matrix_world @ loc).z if ok else None
prof = [(round(y, 3), ray_down(piano, 0.05, y)) for y in [i * 0.02 for i in range(0, 40)]]
print("PROFILE", prof)
# the fallboard carries a maker's name inlay in its texture: cover it with a plain panel in the piano's own wood (no brand names on screen)
FB = []
for i in range(60):
    z = 0.80 + i * 0.004
    ok, loc, nrm, idx = piano.ray_cast(Vector((0.0, -0.5, z)), Vector((0, 1, 0)))
    if ok and 0.13 < loc.y < 0.25 and abs(nrm.y) > 0.8: FB.append((z, loc.y, piano.data.polygons[idx].material_index))
FB.sort(key=lambda t: t[1]); yf = FB[len(FB) // 2][1]; zs = [z for z, y, m in FB if abs(y - yf) < 0.006]
mi = FB[len(FB) // 2][2]
print("FALLBOARD", yf, min(zs), max(zs), piano.data.materials[mi].name)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, yf - 0.0025, (min(zs) + max(zs)) / 2)); fbp = bpy.context.active_object; fbp.name = "Fallboard_Panel"
fbp.scale = (1.36, 0.004, max(zs) - min(zs) + 0.004); bpy.ops.object.transform_apply(scale=True)
fbp.modifiers.new("bev", 'BEVEL').width = 0.0015
fbp.data.materials.append(piano.data.materials[mi]); uv_cube_project(fbp, 0.6)
for c_ in fbp.users_collection: c_.objects.unlink(fbp)
C_SET.objects.link(fbp)
# ---- replace the model's fused keys with 88 separate hinged keys (so each can go down under a finger)
import bmesh
KEY_TOP, KEY_BACK, KXH = 0.8057, 0.152, 0.672
bm = bmesh.new(); bm.from_mesh(piano.data)
kill = [f for f in bm.faces if all(-0.006 <= v.co.y <= 0.166 and 0.755 <= v.co.z <= 0.832 and abs(v.co.x) < KXH + 0.001 for v in f.verts)]
bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(piano.data); bm.free(); piano.data.update()
print("KEYFACES_REMOVED", len(kill))
ivory = simple_mat("M_KeyIvory", (0.86, 0.82, 0.72), 0.28); ivory.node_tree.nodes["Principled BSDF"].inputs['Subsurface Weight'].default_value = 0.15
ebony = simple_mat("M_KeyEbony", (0.025, 0.02, 0.018), 0.22)
bedm = simple_mat("M_KeyBed", (0.05, 0.03, 0.02), 0.7)
box("KeyBed", (2 * KXH + 0.01, 0.17, 0.03), (0, 0.083, KEY_TOP - 0.045), bedm, C_SET)
NW = 52; WW = 2 * KXH / NW; KEYS = []
def key_obj(name, x0, x1, y0, y1, z0, z1, mat):
    bpy.ops.mesh.primitive_cube_add(size=1); o = bpy.context.active_object; o.name = name
    o.data.transform(Matrix.Translation((0, -0.5, 0)) ); o.data.transform(Matrix.Diagonal((x1 - x0, y1 - y0, z1 - z0, 1)))
    o.data.transform(Matrix.Translation((0, 0, (z0 + z1) / 2 - KEY_TOP + 0.0)))
    o.location = ((x0 + x1) / 2, y1, KEY_TOP)      # origin = hinge at the back of the key, at key-top height
    bv = o.modifiers.new("bev", 'BEVEL'); bv.width = 0.0012; bv.segments = 2
    o.data.materials.append(mat)
    for c_ in o.users_collection: c_.objects.unlink(o)
    C_SET.objects.link(o); return o
for i in range(NW):
    x0 = -KXH + i * WW
    KEYS.append(key_obj("Key_W%02d" % i, x0 + 0.0006, x0 + WW - 0.0006, 0.0, KEY_BACK, KEY_TOP - 0.022, KEY_TOP, ivory))
    if i % 7 in (0, 1, 3, 4, 5) and i < NW - 1:
        xc = x0 + WW
        KEYS.append(key_obj("Key_B%02d" % i, xc - 0.0062, xc + 0.0062, 0.055, KEY_BACK, KEY_TOP - 0.004, KEY_TOP + 0.012, ebony))
sc["keys"] = [k.name for k in KEYS]; print("KEYS", len(KEYS))
sc["piano_len"] = mx.y; sc["piano_w"] = mx.x - mn.x
for m in piano.data.materials:
    if not m or not m.use_nodes: continue
    P = next((x for x in m.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'), None)
    if P: P.inputs['Roughness'].default_value = 0.32; P.inputs['Coat Weight'].default_value = 0.6; P.inputs['Coat Roughness'].default_value = 0.12

bench = bake_group(imp("bench", C_SET), "Bench", 0.0105)
bmn, bmx = bbox([bench]); print("BENCH", tuple(bmn), tuple(bmx))

# ---------------------------------------------------------------- room shell 7 x 7 x 3.8, piano near the middle
floor_m = ph_mat("M_Parquet", "herringbone_parquet", 1.4, tint=(0.75, 0.6, 0.5), rough_mul=1.5, bump=0.25)
wall_m = ph_mat("M_Plaster", "plastered_wall_02", 1.0, tint=(0.78, 0.66, 0.52), bump=0.4)
wood_m = ph_mat("M_DarkWood", "dark_wooden_planks", 1.5, tint=(0.7, 0.55, 0.42), bump=0.2)
table_m = ph_mat("M_TableWood", "wood_table_worn", 1.0, tint=(0.8, 0.6, 0.45), bump=0.2)
velvet_m = ph_mat("M_Velvet", "velour_velvet", 2.0, tint=(0.75, 0.12, 0.1), bump=0.3)
RX0, RX1, RY0, RY1, RH = -3.6, 3.6, -3.2, 4.2, 3.8
fl = box("Floor", (RX1 - RX0, RY1 - RY0, 0.05), ((RX0 + RX1) / 2, (RY0 + RY1) / 2, -0.025), floor_m, C_SET); uv_cube_project(fl, 1.0)
ce = box("Ceiling", (RX1 - RX0, RY1 - RY0, 0.05), ((RX0 + RX1) / 2, (RY0 + RY1) / 2, RH + 0.025), wall_m, C_SET); uv_cube_project(ce, 2.0)
walls = []
for nm, size, loc in (("Wall_Back", (RX1 - RX0, 0.1, RH), ((RX0 + RX1) / 2, RY1 + 0.05, RH / 2)),
                      ("Wall_Front", (RX1 - RX0, 0.1, RH), ((RX0 + RX1) / 2, RY0 - 0.05, RH / 2)),
                      ("Wall_Left", (0.1, RY1 - RY0, RH), (RX0 - 0.05, (RY0 + RY1) / 2, RH / 2)),
                      ("Wall_Right", (0.1, RY1 - RY0, RH), (RX1 + 0.05, (RY0 + RY1) / 2, RH / 2))):
    w = box(nm, size, loc, wall_m, C_SET); uv_cube_project(w, 2.0); walls.append(w)
# dado panelling + skirting around the walls
for nm, size, loc in (("Dado_B", (RX1 - RX0, 0.04, 1.0), ((RX0 + RX1) / 2, RY1 - 0.02, 0.5)), ("Dado_L", (0.04, RY1 - RY0, 1.0), (RX0 + 0.02, (RY0 + RY1) / 2, 0.5)),
                      ("Dado_R", (0.04, RY1 - RY0, 1.0), (RX1 - 0.02, (RY0 + RY1) / 2, 0.5)), ("Dado_F", (RX1 - RX0, 0.04, 1.0), ((RX0 + RX1) / 2, RY0 + 0.02, 0.5))):
    d = box(nm, size, loc, wood_m, C_SET, bevel=0.01); uv_cube_project(d, 1.0)
for i in range(-5, 6):   # vertical panel stiles on the back + left walls
    box("Stile_B%d" % i, (0.05, 0.06, 0.92), (i * 0.66, RY1 - 0.04, 0.5), wood_m, C_SET, 0.01)
    box("Stile_L%d" % i, (0.06, 0.05, 0.92), (RX0 + 0.04, 0.5 + i * 0.66, 0.5), wood_m, C_SET, 0.01)
box("DadoRail_B", (RX1 - RX0, 0.08, 0.05), ((RX0 + RX1) / 2, RY1 - 0.05, 1.02), wood_m, C_SET, 0.01)
box("DadoRail_L", (0.08, RY1 - RY0, 0.05), (RX0 + 0.05, (RY0 + RY1) / 2, 1.02), wood_m, C_SET, 0.01)
box("Cornice_B", (RX1 - RX0, 0.14, 0.12), ((RX0 + RX1) / 2, RY1 - 0.07, RH - 0.06), wood_m, C_SET, 0.02)
box("Cornice_L", (0.14, RY1 - RY0, 0.12), (RX0 + 0.07, (RY0 + RY1) / 2, RH - 0.06), wood_m, C_SET, 0.02)
# tall window in the left wall: night sky beyond, mullions, velvet curtains
night = simple_mat("M_NightSky", (0.02, 0.03, 0.06), emit=(0.18, 0.28, 0.55), es=0.6)
box("Window_Night", (0.02, 1.3, 2.3), (RX0 - 0.12, 0.9, 2.05), night, C_SET)
WL = walls[2]; cut = box("Window_Cut", (0.4, 1.3, 2.3), (RX0, 0.9, 2.05), night, C_SET)
bo = WL.modifiers.new("win", 'BOOLEAN'); bo.object = cut; bo.operation = 'DIFFERENCE'; cut.hide_render = True; cut.hide_viewport = True
for z in (1.2, 1.97, 2.74):
    box("Mullion_H%.0f" % (z * 10), (0.06, 1.3, 0.04), (RX0 - 0.05, 0.9, z), wood_m, C_SET)
box("Mullion_V", (0.06, 0.04, 2.3), (RX0 - 0.05, 0.9, 2.05), wood_m, C_SET)
box("WindowSill", (0.3, 1.5, 0.06), (RX0 + 0.08, 0.9, 0.88), wood_m, C_SET, 0.01)
CURTAINS = []
for side, y in (("L", 0.9 - 0.95), ("R", 0.9 + 0.95)):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=40, y_subdivisions=30, size=1, location=(0, 0, 0))
    c = bpy.context.active_object; c.name = "Curtain_" + side
    for c_ in c.users_collection: c_.objects.unlink(c)
    C_SET.objects.link(c)
    for v in c.data.vertices:   # pleats: vertical wave in the plane, then stand up against the wall
        u, w = v.co.x + 0.5, v.co.y + 0.5
        v.co = Vector((0.06 * math.sin(u * 2 * math.pi * 7) * (0.6 + 0.4 * w), (u - 0.5) * 0.75, w * 3.3))
    c.location = (RX0 + 0.22, y, 0.35); c.data.materials.append(velvet_m)
    c.modifiers.new("sol", 'SOLIDIFY').thickness = 0.01
    sw = c.modifiers.new("sway", 'WAVE'); sw.use_normal = False; sw.use_x = True; sw.use_y = False; sw.height = 0.025; sw.width = 0.9; sw.speed = 0.004
    sw.start_position_object = None; sw.time_offset = -RND.uniform(0, 200); CURTAINS.append(c)
    uv_cube_project(c, 0.6)
box("CurtainRod", (0.04, 2.6, 0.04), (RX0 + 0.25, 0.9, 3.5), simple_mat("M_Brass", (0.8, 0.6, 0.3), 0.25, 1.0), C_SET)
# framed paintings (abstract landscape, no text) and a tall mirror on the back wall
def painting(name, loc, size, rot_z, seed):
    fr = box(name + "_Frame", (size[0] + 0.12, 0.05, size[1] + 0.12), (0, 0, 0), simple_mat(name + "_Gilt", (0.75, 0.55, 0.25), 0.35, 1.0), C_SET, 0.02)
    m = bpy.data.materials.new(name + "_Canvas"); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.5; nz.inputs['Detail'].default_value = 6; nz.noise_dimensions = '4D'; nz.inputs['W'].default_value = seed
    cr = nt.nodes.new('ShaderNodeValToRGB'); e = cr.color_ramp.elements
    e[0].color = (0.05, 0.06, 0.04, 1); e[1].color = (0.55, 0.45, 0.28, 1); e.new(0.5).color = (0.18, 0.22, 0.12, 1)
    nt.links.new(nz.outputs['Fac'], cr.inputs['Fac']); nt.links.new(cr.outputs['Color'], P.inputs['Base Color']); P.inputs['Roughness'].default_value = 0.6
    cv = box(name, (size[0], 0.02, size[1]), (0, -0.02, 0), m, C_SET); cv.parent = fr
    fr.location = loc; fr.rotation_euler = (0, 0, rot_z)
painting("Painting_A", (-1.9, RY1 - 0.06, 2.3), (1.1, 0.8), 0, 1.3)
painting("Painting_B", (1.9, RY1 - 0.06, 2.4), (0.7, 0.95), 0, 4.1)
painting("Painting_C", (RX1 - 0.06, 1.2, 2.3), (1.2, 0.85), R_(90), 7.7)
# bookcase-like cabinet on the right wall, filled with leather spines
cab = box("Cabinet", (0.45, 1.8, 2.2), (RX1 - 0.25, -1.2, 1.1), table_m, C_SET, 0.02); uv_cube_project(cab, 1.0)
spine_m = [simple_mat("M_Book%d" % i, c, 0.6) for i, c in enumerate([(0.25, 0.06, 0.04), (0.08, 0.12, 0.07), (0.3, 0.2, 0.1), (0.12, 0.07, 0.05)])]
for shelf in range(4):
    z0 = 0.35 + shelf * 0.48; y = -2.05
    box("Shelf%d" % shelf, (0.4, 1.7, 0.03), (RX1 - 0.46, -1.2, z0 - 0.02), table_m, C_SET)
    while y < -0.38:
        w = RND.uniform(0.03, 0.07); h = RND.uniform(0.25, 0.4)
        b = box("Book", (0.26, w, h), (RX1 - 0.52, y + w / 2, z0 + h / 2), RND.choice(spine_m), C_SET, 0.004)
        b.rotation_euler.x = RND.uniform(-0.04, 0.04); y += w + 0.004

# ---------------------------------------------------------------- props: candelabras, candles, side table, quill + inkwell, paper stacks
brass = simple_mat("M_BrassOld", (0.65, 0.45, 0.2), 0.32, 1.0)
wax = simple_mat("M_Wax", (0.92, 0.86, 0.72), 0.45); wax.node_tree.nodes["Principled BSDF"].inputs['Subsurface Weight'].default_value = 0.5
flame_m = bpy.data.materials.new("M_Flame"); flame_m.use_nodes = True; fn = flame_m.node_tree.nodes; fn.clear()
fo = fn.new('ShaderNodeOutputMaterial'); fe = fn.new('ShaderNodeEmission'); fe.inputs['Color'].default_value = (1.0, 0.55, 0.18, 1); fe.inputs['Strength'].default_value = 18
fe.name = "FlameEmit"; flame_m.node_tree.links.new(fe.outputs[0], fo.inputs['Surface'])
FLAMES = []
def candle(loc, h=0.18, r=0.012, light=True, coll=C_PROPS):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=h, location=(loc[0], loc[1], loc[2] + h / 2))
    c = bpy.context.active_object; c.name = "Candle"; c.data.materials.append(wax)
    for c_ in c.users_collection: c_.objects.unlink(c)
    coll.objects.link(c)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.008, location=(loc[0], loc[1], loc[2] + h + 0.018))
    f = bpy.context.active_object; f.name = "Flame"; f.scale = (1, 1, 2.4); f.data.materials.append(flame_m)
    for c_ in f.users_collection: c_.objects.unlink(f)
    C_FX.objects.link(f); FLAMES.append(f)
    if light:
        ld = bpy.data.lights.new("CandleLight", 'POINT'); ld.energy = 9.0; ld.color = (1.0, 0.62, 0.3); ld.shadow_soft_size = 0.03
        L = bpy.data.objects.new("CandleLight", ld); L.location = f.location + Vector((0, 0, 0.01)); C_FX.objects.link(L)
    return c
cand = bake_group(imp("candelabra", C_PROPS), "Candelabra_A", 1.25, drop=("M_Candle",))
cand.data.materials.clear(); cand.data.materials.append(brass)
cb = cand.copy(); cb.data = cand.data; cb.name = "Candelabra_B"; C_PROPS.objects.link(cb)
cc = cand.copy(); cc.data = cand.data; cc.name = "Candelabra_C"; C_PROPS.objects.link(cc)
sc["candelabra_h"] = bbox([cand])[1].z
# arm tips of the candelabra (3 cups): measured from its bbox: centre + both ends
CA_TIPS = [(-0.155 * 1.25 * 0.92, 0, 0.30 * 1.25), (0, 0, 0.382 * 1.25 - 0.01), (0.155 * 1.25 * 0.92, 0, 0.30 * 1.25)]
sc["ca_tips"] = [list(t) for t in CA_TIPS]
# side table with quill, inkwell, paper stacks (stage left of the piano)
TX, TY = -1.55, -0.6
tbl_top = box("SideTable_Top", (0.7, 0.5, 0.04), (TX, TY, 0.74), table_m, C_PROPS, 0.01); uv_cube_project(tbl_top, 1.0)
for dx in (-0.3, 0.3):
    for dy in (-0.2, 0.2):
        bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.02, depth=0.72, location=(TX + dx, TY + dy, 0.36))
        lg = bpy.context.active_object; lg.name = "SideTable_Leg"; lg.data.materials.append(table_m)
inkm = simple_mat("M_InkGlass", (0.03, 0.03, 0.04), 0.08)
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.035, depth=0.05, location=(TX + 0.2, TY + 0.1, 0.785)); ink = bpy.context.active_object; ink.name = "Inkwell"; ink.data.materials.append(inkm)
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.004, radius2=0.0005, depth=0.28, location=(TX + 0.2, TY + 0.12, 0.88)); q = bpy.context.active_object; q.name = "Quill"
q.rotation_euler = (R_(18), R_(-12), 0); q.data.materials.append(simple_mat("M_Quill", (0.85, 0.82, 0.75), 0.6))
bpy.ops.mesh.primitive_plane_add(size=1, location=(TX + 0.2 + 0.03, TY + 0.13 + 0.0, 0.96)); vane = bpy.context.active_object; vane.name = "QuillVane"
vane.scale = (0.03, 0.12, 1); vane.rotation_euler = (R_(18 + 90), R_(-12), R_(90)); vane.data.materials.append(q.data.materials[0])
vane.parent = q; vane.matrix_parent_inverse = q.matrix_world.inverted()
for o in (ink, q):
    for c_ in o.users_collection: c_.objects.unlink(o)
    C_PROPS.objects.link(o)
for o in [x for x in bpy.data.objects if x.name.startswith("SideTable_Leg")]:
    for c_ in o.users_collection: c_.objects.unlink(o)
    C_PROPS.objects.link(o)
# manuscript paper material (3 page variants)
PAGE_M = []
for i in (1, 2, 3):
    m = bpy.data.materials.new("M_Manuscript%d" % i); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(TEX, "manuscript_%d.jpg" % i))
    nt.links.new(t.outputs['Color'], P.inputs['Base Color']); P.inputs['Roughness'].default_value = 0.75
    P.inputs['Subsurface Weight'].default_value = 0.1; PAGE_M.append(m)
def page(name, loc, rot, coll=C_PROPS, m=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc); p = bpy.context.active_object; p.name = name
    p.data.transform(Matrix.Diagonal((0.23, 0.31, 1, 1))); p.rotation_euler = rot
    md = p.modifiers.new("curl", 'SIMPLE_DEFORM'); md.deform_method = 'BEND'; md.deform_axis = 'Y'; md.angle = R_(RND.uniform(-12, 12))
    p.modifiers.new("sol", 'SOLIDIFY').thickness = 0.0008
    p.data.materials.append(m or RND.choice(PAGE_M))
    for c_ in p.users_collection: c_.objects.unlink(p)
    coll.objects.link(p); return p
for i in range(9):   # messy stack on the table
    page("TablePage", (TX - 0.12 + RND.uniform(-0.04, 0.04), TY + RND.uniform(-0.03, 0.03), 0.762 + i * 0.0018), (0, 0, R_(RND.uniform(-25, 25))))
for i in range(14):   # pages already on the floor round the piano and bench (stay still)
    ang = RND.uniform(0, 2 * math.pi); rr = RND.uniform(0.9, 2.2)
    x, y = 0.0 + math.cos(ang) * rr, 0.4 + math.sin(ang) * rr * 0.9
    if -0.9 < x < 0.9 and -0.9 < y < 2.2: x += 1.2 * (1 if x > 0 else -1)
    page("FloorPage", (x, y, 0.0015 + i * 0.0003), (0, 0, RND.uniform(0, 6.3)))
# side table candles + floor candlestick
candle((TX - 0.22, TY + 0.12, 0.76), 0.2); candle((TX - 0.28, TY - 0.05, 0.76), 0.14)
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.12, depth=0.03, location=(1.5, -0.4, 0.015)); stb = bpy.context.active_object; stb.name = "FloorStand_Base"; stb.data.materials.append(brass)
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.018, depth=1.3, location=(1.5, -0.4, 0.66)); stp = bpy.context.active_object; stp.name = "FloorStand_Pole"; stp.data.materials.append(brass)
cc.location = (1.5, -0.4, 1.31)
for t in CA_TIPS: candle((1.5 + t[0], -0.4 + t[1], 1.31 + t[2]), 0.16)
for o in (stb, stp):
    for c_ in o.users_collection: c_.objects.unlink(o)
    C_PROPS.objects.link(o)
# a high-backed chair + a coat stand in the background
chair_seat = box("Chair_Seat", (0.48, 0.46, 0.06), (-2.6, 2.3, 0.46), velvet_m, C_PROPS, 0.02)
box("Chair_Back", (0.48, 0.06, 0.75), (-2.6, 2.53, 0.85), velvet_m, C_PROPS, 0.02)
for dx in (-0.21, 0.21):
    for dy in (-0.19, 0.21):
        box("Chair_Leg", (0.04, 0.04, 0.44), (-2.6 + dx, 2.3 + dy, 0.22), table_m, C_PROPS)
uv_cube_project(chair_seat, 0.5)

# two candelabras on the piano lid (left front + far curve), lit
LID_Z = 1.0206
for o, (x, y) in ((cand, (-0.5, 0.42)), (cb, (0.45, 1.45))):
    o.location = (x, y, LID_Z); o.rotation_euler = (0, 0, R_(RND.uniform(-30, 30)))
    for t in CA_TIPS:
        tw = Matrix.Rotation(o.rotation_euler.z, 3, 'Z') @ Vector(t)
        candle((x + tw.x, y + tw.y, LID_Z + tw.z), 0.15)
# wall sconces either side of the back paintings
for x in (-3.0, -0.8, 0.8, 3.0):
    box("Sconce_Plate", (0.08, 0.03, 0.14), (x, RY1 - 0.02, 1.9), brass, C_PROPS, 0.01)
    candle((x, RY1 - 0.1, 1.86), 0.14)
# dust motes drifting in the candlelight (keyed, no simulation)
mote_m = bpy.data.materials.new("M_Mote"); mote_m.use_nodes = True; mn_ = mote_m.node_tree.nodes; mn_.clear()
mo_ = mn_.new('ShaderNodeOutputMaterial'); me_ = mn_.new('ShaderNodeEmission'); me_.inputs['Color'].default_value = (1.0, 0.8, 0.55, 1); me_.inputs['Strength'].default_value = 0.5
mote_m.node_tree.links.new(me_.outputs[0], mo_.inputs['Surface'])
for i in range(70):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=RND.uniform(0.0006, 0.0013)); m_ = bpy.context.active_object; m_.name = "Mote"
    m_.data.materials.append(mote_m); m_.visible_shadow = False
    for c_ in m_.users_collection: c_.objects.unlink(m_)
    C_FX.objects.link(m_)
    p0 = Vector((RND.uniform(-1.4, 1.4), RND.uniform(-1.4, 1.6), RND.uniform(0.6, 2.2))); ph = RND.uniform(0, 6.3)
    for f in range(1, 1591, 30):
        t = f / 60.0
        m_.location = p0 + Vector((0.05 * math.sin(t * 0.4 + ph), 0.05 * math.cos(t * 0.33 + ph), 0.02 * t - 0.04 * math.sin(t * 0.5 + ph)))
        m_.keyframe_insert("location", frame=f)
# ---------------------------------------------------------------- world: old-hall HDRI, very dim (candles are the key)
w = bpy.data.worlds.new("World_Room"); sc.world = w; w.use_nodes = True; nt = w.node_tree; n = nt.nodes
bg = n["Background"]; env = n.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(os.path.join(AS, "ph", "hdri", "old_hall_2k.hdr"))
nt.links.new(env.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.03; bg.name = "RoomBG"
# soft cool moonlight through the window + warm key bounce (so the room never goes black)
ld = bpy.data.lights.new("Moon_Window", 'AREA'); ld.energy = 200; ld.size = 1.4; ld.color = (0.55, 0.68, 1.0)
L = bpy.data.objects.new("Moon_Window", ld); L.location = (RX0 + 0.4, 0.9, 2.2); L.rotation_euler = (0, R_(-90), 0); C_FX.objects.link(L)
ld = bpy.data.lights.new("Warm_Fill", 'AREA'); ld.energy = 40; ld.size = 3.0; ld.color = (1.0, 0.7, 0.45)
L = bpy.data.objects.new("Warm_Fill", ld); L.location = (0.8, -2.4, 3.2); L.rotation_euler = (Vector((0, 0.5, 0.8)) - L.location).to_track_quat('-Z', 'Y').to_euler(); C_FX.objects.link(L)
ld = bpy.data.lights.new("Rim_Back", 'AREA'); ld.energy = 55; ld.size = 1.0; ld.color = (1.0, 0.75, 0.5)
L = bpy.data.objects.new("Rim_Back", ld); L.location = (-0.6, 2.8, 2.6); L.rotation_euler = (Vector((0, -0.4, 1.3)) - L.location).to_track_quat('-Z', 'Y').to_euler(); C_FX.objects.link(L)

# colour management
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = -0.35
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.max_bounces = 8; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3; sc.cycles.transmission_bounces = 8; sc.cycles.transparent_max_bounces = 16
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False; sc.render.use_persistent_data = True
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc["flames"] = [f.name for f in FLAMES]
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SCENE_DONE")
