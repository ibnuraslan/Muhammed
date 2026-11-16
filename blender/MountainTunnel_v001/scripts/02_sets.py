"""MountainTunnel sets and props.  blender -b chars.blend --python 02_sets.py -- <assets_dir> <brand_dir> <out.blend>
One landscape: a rock ridge along X (crest ~30 m, feet at |y|=55), the village south of it (y<-70), the hospital north (y=+100),
the only road loops round the ridge's east end (x~270). The gorge (the man's passage) runs along Y at x=0; its length is keyed
in 03_shots via the 'Cutter' object (y of its +Y end)."""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Euler, noise
a = sys.argv[sys.argv.index("--") + 1:]; AS, BRAND, OUT = os.path.abspath(a[0]), os.path.abspath(a[1]), a[2]
sc = bpy.context.scene; V = Vector; R_ = math.radians
random.seed(30)
COLS = {}
def col(name):
    if name not in COLS:
        c = bpy.data.collections.new(name); sc.collection.children.link(c); COLS[name] = c
    return COLS[name]
def link(o, cname):
    for c in o.users_collection: c.objects.unlink(o)
    col(cname).objects.link(o); return o
def ss(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

def tex_mat(name, tid, tint=(1, 1, 1), scale=1.0, bump=0.3, rough_min=0.45, sat=1.0, coord='Object'):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    d = os.path.join(AS, tid, "textures")
    def img(key, non_color):
        f = [x for x in os.listdir(d) if key in x]
        if not f: return None
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(os.path.join(d, f[0]), check_existing=True)
        if non_color: n.image.colorspace_settings.name = 'Non-Color'
        n.projection = 'BOX'; n.projection_blend = 0.3
        return n
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale,) * 3
    nt.links.new(tc.outputs[coord], mp.inputs['Vector'])
    dif = img("diff", False)
    hs = nt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = sat
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    mx.inputs['B'].default_value = (*tint, 1); mx.name = "Tint"
    nt.links.new(mp.outputs[0], dif.inputs[0]); nt.links.new(dif.outputs['Color'], hs.inputs['Color']); nt.links.new(hs.outputs[0], mx.inputs['A'])
    nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])
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
def mesh_obj(name, verts, faces, mat, cname, smooth=False, recalc=False):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    if recalc:
        bm_ = bmesh.new(); bm_.from_mesh(me); bmesh.ops.recalc_face_normals(bm_, faces=bm_.faces); bm_.to_mesh(me); bm_.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    if mat: me.materials.append(mat)
    if smooth:
        for p in me.polygons: p.use_smooth = True
    return link(o, cname)
def box(name, dims, loc, mat, cname, rot=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot); o = bpy.context.active_object; o.name = name
    o.scale = dims; bpy.ops.object.transform_apply(scale=True)
    if mat: o.data.materials.append(mat)
    if bevel: b = o.modifiers.new("Bev", 'BEVEL'); b.width = bevel; b.segments = 2
    return link(o, cname)
def append_model(tid, cname, loc, rot=(0, 0, 0), scale=1.0):
    f = os.path.join(AS, tid, tid + "_1k.blend")
    before = set(bpy.data.images)
    with bpy.data.libraries.load(f) as (df, dt): dt.objects = [n for n in df.objects if "LOD" not in n or "LOD1" in n]
    for im in set(bpy.data.images) - before:          # point the new images at their absolute file (packed at the end)
        fn = os.path.join(AS, tid, "textures", os.path.basename(im.filepath))
        if os.path.exists(fn): im.filepath = fn; im.reload()
        else: print("MISSING TEX", im.filepath)
    out = []
    for o in dt.objects:
        if o is None or o.type != 'MESH': continue
        sc.collection.objects.link(o); link(o, cname); o.location = V(loc) + Euler(rot).to_matrix() @ (o.location * scale)
        for md in list(o.modifiers):
            if md.type in ('SUBSURF', 'MULTIRES', 'DISPLACE'): print("DROPMOD", o.name, md.type); o.modifiers.remove(md)
        try: o.cycles.use_adaptive_subdivision = False
        except Exception: pass
        for m in o.data.materials:
            if m: m.displacement_method = 'BUMP'
            if m and m.node_tree:
                for l in [l for l in m.node_tree.links if l.to_socket.name == 'Displacement']: m.node_tree.links.remove(l)
        o.rotation_euler = rot; o.scale = (scale,) * 3; out.append(o)
    return out
SRCCOL = {}
def inst(src_objs, cname, loc, rot_z, scale, name):
    """collection instance of the source model (geometry shared in Cycles: 70 tree copies stay cheap)"""
    key = src_objs[0].name
    if key not in SRCCOL:
        c = bpy.data.collections.new("SRC_" + key[:20]); sc.collection.children.link(c)
        for s in src_objs:
            for uc in list(s.users_collection): uc.objects.unlink(s)
            c.objects.link(s); s.location.z += 0.0
        bpy.context.view_layer.layer_collection.children[c.name].exclude = True
        SRCCOL[key] = c
    e = bpy.data.objects.new(name, None); e.instance_type = 'COLLECTION'; e.instance_collection = SRCCOL[key]
    col(cname).objects.link(e); e.location = loc; e.rotation_euler = (0, 0, rot_z); e.scale = (scale,) * 3
    return [e]

# ================================================================== materials
M_ROCK = tex_mat("M_Rock", "rock_face_03", tint=(1.25, 1.02, 0.78), scale=0.12, bump=0.35, sat=0.9)
M_ROCK_CU = tex_mat("M_RockCU", "rock_face_03", tint=(1.0, 0.86, 0.68), scale=0.6, bump=0.35, sat=0.9)
M_GRASS = tex_mat("M_Grass", "grass_path_2", tint=(0.62, 0.95, 0.42), scale=0.22, bump=0.25, sat=1.2)
M_DIRT = tex_mat("M_GorgeFloor", "grass_path_2", tint=(0.85, 0.72, 0.55), scale=0.3, bump=0.3, sat=0.3)
M_ASPH = tex_mat("M_Asphalt", "asphalt_02", tint=(0.55, 0.55, 0.57), scale=0.25, bump=0.2, sat=0.3, coord='Object')
M_THATCH = tex_mat("M_Thatch", "thatch_roof_angled", tint=(1.5, 1.25, 0.85), scale=0.5, bump=0.35)
M_MUD = tex_mat("M_MudWall", "clay_plaster", tint=(1.35, 1.1, 0.8), scale=0.5, bump=0.3)
M_WHITE = flat("M_HospWall", (0.86, 0.83, 0.74), 0.6)
M_GLASS = flat("M_Window", (0.12, 0.22, 0.32), 0.15)
M_WOOD = flat("M_DoorWood", (0.32, 0.18, 0.09), 0.6)
M_RED = flat("M_CrossRed", (0.8, 0.03, 0.03), 0.4)
M_SIGNW = flat("M_SignWhite", (0.92, 0.92, 0.92), 0.4)
M_TRIM = flat("M_Trim", (0.55, 0.32, 0.2), 0.5)
M_STEEL = flat("M_ChiselSteel", (0.42, 0.43, 0.45), 0.35, 0.9)
M_BAMBOO = flat("M_Bamboo", (0.72, 0.58, 0.3), 0.55)
M_CLOTH = flat("M_StretcherCloth", (0.85, 0.78, 0.6), 0.85)
M_YEL = flat("M_LineYellow", (0.95, 0.75, 0.1), 0.5)

# ================================================================== terrain
CT = "Terrain"
bpy.ops.mesh.primitive_plane_add(size=1); g = bpy.context.active_object; g.name = "Ground"; g.scale = (3000, 3000, 1)
bpy.ops.object.transform_apply(scale=True); g.data.materials.append(M_GRASS); link(g, CT)

H0, YF, YC = 30.0, 55.0, 20.0           # crest height, foot |y|, crest plateau |y|
def ridge_h(x, y):
    t = ss((265.0 - abs(x)) / 70.0)
    H = H0 * t * (0.82 + 0.32 * noise.noise(V((x / 45.0, 3.1, 0.7))))
    t_ = max(0.0, min(1.0, (YF - abs(y)) / (YF - YC))); p = 1 - (1 - t_) ** 2.2
    lump = noise.noise(V((x / 11.0, y / 11.0, 1.3))) * 4.0 + abs(noise.noise(V((x / 4.0, y / 4.0, 5.1)))) * 1.6
    return H * p + lump * min(1.0, p * 3) - 0.6 * (1 - p)
def grid(name, x0, x1, nx, y0, y1, ny, solid):
    xs = [x0 + (x1 - x0) * i / nx for i in range(nx + 1)]; ys = [y0 + (y1 - y0) * j / ny for j in range(ny + 1)]
    verts = [(x, y, ridge_h(x, y)) for y in ys for x in xs]
    faces = [(j * (nx + 1) + i, j * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i) for j in range(ny) for i in range(nx)]
    if solid:     # closed volume for the boolean: border walls down to z=-3 and one bottom face
        border = [i for i in range(nx + 1)] + [j * (nx + 1) + nx for j in range(1, ny + 1)] + \
                 [ny * (nx + 1) + i for i in range(nx - 1, -1, -1)] + [j * (nx + 1) for j in range(ny - 1, 0, -1)]
        nv = len(verts); verts += [(verts[k][0], verts[k][1], -3.0) for k in border]; nb = len(border)
        for k in range(nb):
            faces.append((border[(k + 1) % nb], border[k], nv + k, nv + (k + 1) % nb))
        faces.append(tuple(nv + k for k in range(nb)))
    o = mesh_obj(name, verts, faces, M_ROCK, CT, smooth=True)
    if solid:
        bpy.context.view_layer.objects.active = o
        for ob in bpy.context.selected_objects: ob.select_set(False)
        o.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
    return o
ridge = grid("Ridge", -30, 30, 100, -62, 62, 206, True)        # the hero section the passage is cut through
grid("RidgeW", -265, -30, 160, -62, 62, 80, False)
grid("RidgeE", 30, 265, 160, -62, 62, 80, False)
# the passage: a box cutter whose +Y face is at the object's origin; 03_shots keys its y (years of cutting)
cv = [(-1.8, -90, -2), (1.8, -90, -2), (1.8, 0, -2), (-1.8, 0, -2), (-1.8, -90, 80), (1.8, -90, 80), (1.8, 0, 80), (-1.8, 0, 80)]
cf = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
cutter = mesh_obj("Cutter", cv, cf, None, CT, recalc=True); cutter.location = (0, -YF + 2.0, 0)
cutter.hide_render = True; cutter.display_type = 'WIRE'
bo = ridge.modifiers.new("Passage", 'BOOLEAN'); bo.object = cutter; bo.operation = 'DIFFERENCE'
bo.solver = 'EXACT'
# the wife's ledge path: a shelf carved into the west face at z=6 (second cutter)
LZ = 6.0
def y_at(x, z):
    y = -YF
    while ridge_h(x, y) < z and y < 0: y += 0.05
    return y
LY_IN = max(y_at(x, LZ + 2.6) for x in range(-27, -12))
LY_EDGE = min(y_at(x, LZ) for x in range(-27, -12))
lv = [(-28, -90, LZ), (-12, -90, LZ), (-12, LY_IN, LZ), (-28, LY_IN, LZ), (-28, -90, 60), (-12, -90, 60), (-12, LY_IN, 60), (-28, LY_IN, 60)]
lcut = mesh_obj("LedgeCutter", lv, cf, None, CT, recalc=True); lcut.hide_render = True; lcut.display_type = 'WIRE'
bo2 = ridge.modifiers.new("Ledge", 'BOOLEAN'); bo2.object = lcut; bo2.operation = 'DIFFERENCE'
bo2.solver = 'EXACT'
print("LEDGE in", round(LY_IN, 2), "edge", round(LY_EDGE, 2))
E18 = y_at(-18.0, LZ); EMAX = max(y_at(x * 0.5, LZ) for x in range(-50, -35))
YW = max(EMAX + 0.35, E18 + 0.45)
print("LEDGE walk", round(YW, 2), "edge@-18", round(E18, 2), "edge max", round(EMAX, 2))
sc["LEDGE"] = (YW, LZ, E18)
# gorge floor (packed dirt) and the close-up rock face at the end of the cut, both ride on the cutter
gf = mesh_obj("GorgeFloor", [(-1.8, -90, 0.02), (1.8, -90, 0.02), (1.8, 0, 0.02), (-1.8, 0, 0.02)], [(0, 1, 2, 3)], M_DIRT, CT)
gf.parent = cutter
bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=60, size=1); rf = bpy.context.active_object; rf.name = "CutFace"
rf.scale = (3.6, 5.0, 1); bpy.ops.object.transform_apply(scale=True)
rf.rotation_euler = (R_(90), 0, 0); rf.location = (0, -0.03, 2.5); rf.data.materials.append(M_ROCK_CU); link(rf, CT)
tx = bpy.data.textures.new("T_CutFace", 'CLOUDS'); tx.noise_scale = 0.18
dm = rf.modifiers.new("Rough", 'DISPLACE'); dm.texture = tx; dm.strength = 0.05; dm.mid_level = 1.0
rf.parent = cutter; rf.hide_render = rf.hide_viewport = True     # shown only in the close-up shots (03_shots)
for p in rf.data.polygons: p.use_smooth = True

# ================================================================== props
CP = "Props"
hammer = append_model("cross_pein_hammer", CP, (0, 0, 0))
for i, h in enumerate(hammer): h.name = "Hammer" if i == 0 else "Hammer_part%d" % i
HAM = bpy.data.objects["Hammer"]
bpy.context.view_layer.update()
print("HAMMER dims", tuple(round(d, 3) for d in HAM.dimensions), [o.name for o in hammer])
# chisel: octagonal steel bar, flat chisel edge at one end (+Y), mushroomed striking head at the other
bm = bmesh.new()
rings = [(-0.12, 0.011), (-0.105, 0.0095), (-0.10, 0.009), (0.08, 0.009), (0.11, 0.006), (0.125, 0.0015)]
prev = None
for y, r in rings:
    ring = [bm.verts.new((r * math.cos(k * math.pi / 4 + math.pi / 8) * (1.0 if y < 0.08 else 1.6), y, r * math.sin(k * math.pi / 4 + math.pi / 8) * (1.0 if y < 0.08 else 0.35))) for k in range(8)]
    if prev:
        for k in range(8): bm.faces.new((prev[k], prev[(k + 1) % 8], ring[(k + 1) % 8], ring[k]))
    else: bm.faces.new(list(reversed(ring)))
    prev = ring
bm.faces.new(prev)
me = bpy.data.meshes.new("Chisel"); bm.to_mesh(me); bm.free()
chisel = bpy.data.objects.new("Chisel", me); sc.collection.objects.link(chisel); me.materials.append(M_STEEL); link(chisel, CP)
pot = append_model("brass_pot_01", CP, (0, 0, 0))
for i, o in enumerate(pot): o.name = "Pot" if i == 0 else "Pot_part%d" % i
print("POT dims", tuple(round(d, 3) for d in bpy.data.objects["Pot"].dimensions))
# rock chips: a few irregular small stones (instanced per strike in 03_shots)
for i in range(6):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.012 + 0.006 * i % 3)
    o = bpy.context.active_object; o.name = "Chip%d" % i
    for v in o.data.vertices: v.co *= random.uniform(0.6, 1.3)
    o.data.materials.append(M_ROCK_CU); link(o, CP); o.location = (500, 500 + i, 0)
# bamboo stretcher (drag litter): two poles 2.6 m, 0.6 m apart, slats and a cloth bed; origin at the rear pole ends (ground contact)
SW, SL = 0.62, 2.6
st_parts = []
for sx in (-1, 1):
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.028, depth=SL, location=(sx * SW / 2, SL / 2, 0.028), rotation=(R_(90), 0, 0))
    o = bpy.context.active_object; o.name = "Stretcher_Pole%s" % ("L" if sx < 0 else "R"); o.data.materials.append(M_BAMBOO); st_parts.append(o)
for k in range(7):
    y = 0.35 + k * 0.27
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.016, depth=SW + 0.06, location=(0, y, 0.056), rotation=(0, R_(90), 0))
    o = bpy.context.active_object; o.name = "Stretcher_Slat%d" % k; o.data.materials.append(M_BAMBOO); st_parts.append(o)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 1.15, 0.075)); o = bpy.context.active_object; o.name = "Stretcher_Cloth"
o.scale = (SW - 0.04, 1.75, 1); bpy.ops.object.transform_apply(scale=True); o.data.materials.append(M_CLOTH)
o.modifiers.new("S", 'SOLIDIFY').thickness = 0.01; st_parts.append(o)
stretcher = bpy.data.objects.new("Stretcher", None); sc.collection.objects.link(stretcher); link(stretcher, CP)
for o in st_parts:
    link(o, CP); o.parent = stretcher
stretcher.location = (600, 0, 0)

# ================================================================== village (south)
CV = "Village"
def hut(name, loc, rot, w=4.2, d=3.4, h=2.3):
    o = box(name + "_Walls", (w, d, h), (0, 0, h / 2), M_MUD, CV, bevel=0.05)
    # gable thatch roof with overhang
    oh = 0.45; rh = 1.6
    vs = [(-w / 2 - oh, -d / 2 - oh, h - 0.15), (w / 2 + oh, -d / 2 - oh, h - 0.15), (w / 2 + oh, 0, h + rh), (-w / 2 - oh, 0, h + rh),
          (-w / 2 - oh, d / 2 + oh, h - 0.15), (w / 2 + oh, d / 2 + oh, h - 0.15)]
    r = mesh_obj(name + "_Roof", vs, [(0, 1, 2, 3), (3, 2, 5, 4)], M_THATCH, CV)
    r.modifiers.new("S", 'SOLIDIFY').thickness = 0.18
    gab = mesh_obj(name + "_Gable", [(-w / 2, -d / 2, h), (-w / 2, d / 2, h), (-w / 2, 0, h + rh - 0.2), (w / 2, -d / 2, h), (w / 2, d / 2, h), (w / 2, 0, h + rh - 0.2)],
                   [(0, 1, 2), (3, 5, 4)], M_MUD, CV)
    door = box(name + "_Door", (1.0, 0.06, 1.85), (0.6, -d / 2 - 0.02, 0.93), M_WOOD, CV)
    win = box(name + "_Win", (0.7, 0.06, 0.55), (-1.1, -d / 2 - 0.02, 1.45), M_WOOD, CV)
    root = bpy.data.objects.new(name, None); sc.collection.objects.link(root); link(root, CV)
    for p in (o, r, gab, door, win): p.parent = root
    root.location = loc; root.rotation_euler = (0, 0, rot)
    return root
HUTS = [(-30, -82, R_(5)), (-18, -88, R_(-8)), (-5, -84, R_(2)), (9, -90, R_(12)), (22, -83, R_(-4)), (-42, -95, R_(20)), (-14, -102, R_(-15)), (16, -104, R_(6)), (34, -97, R_(-20))]
for i, (x, y, r) in enumerate(HUTS): hut("Hut%d" % i, (x, y, 0), r)
def crate_at(name, loc, rz):
    parts = append_model("wooden_crate_01", CV, (0, 0, 0), scale=1.6)
    root = bpy.data.objects.new(name, None); sc.collection.objects.link(root); link(root, CV)
    for o in parts: o.parent = root
    root.location = loc; root.rotation_euler = (0, 0, rz)
    print("CRATE parts", [(o.name, tuple(round(d, 2) for d in o.dimensions)) for o in parts])
    return root, parts
CRATE, CRP = crate_at("Crate_Village", (-8.9, -65.2, 0), R_(-67))
CRATE2, CRP2 = crate_at("Crate_Hospital", (4.5, 88.5, 0), R_(8))
bpy.context.view_layer.update()
print("CRATE dims", tuple(round(d, 3) for d in CRATE.dimensions))
def logo_decal(name, img, target, side_point, rot, width, cname):
    im = bpy.data.images.load(os.path.join(BRAND, img), check_existing=True)
    m = bpy.data.materials.new("M_" + name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = im; t.interpolation = 'Cubic'
    nt.links.new(t.outputs['Color'], P.inputs['Base Color']); nt.links.new(t.outputs['Alpha'], P.inputs['Alpha']); P.inputs['Roughness'].default_value = 0.7
    bpy.ops.mesh.primitive_plane_add(size=1); o = bpy.context.active_object; o.name = name
    o.scale = (width, width * im.size[1] / im.size[0], 1); bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m); o.location = side_point; o.rotation_euler = rot
    bpy.context.view_layer.update(); Mw = o.matrix_world.copy(); o.parent = target; o.matrix_world = Mw
    return link(o, cname)
bpy.context.view_layer.update()
for cr, parts, nm in ((CRATE, CRP, "Logo_Village"), (CRATE2, CRP2, "Logo_Hospital")):
    body_ = next(o for o in parts if not o.name.split(".")[0].endswith(("lid", "latch")))
    lb = [V(c) for c in body_.bound_box]
    lx = (min(p.x for p in lb) + max(p.x for p in lb)) / 2; lz = (min(p.z for p in lb) + max(p.z for p in lb)) / 2
    side = -1 if nm == "Logo_Hospital" else 1           # village: +Y side (faces the 3a camera), hospital: -Y side
    ly = (min(p.y for p in lb) - 0.004) if side < 0 else (max(p.y for p in lb) + 0.004)
    pt = body_.matrix_world @ V((lx, ly, lz))
    wdt = (max(p.x for p in lb) - min(p.x for p in lb)) * body_.matrix_world.to_scale().x * 0.72
    rz = cr.rotation_euler.z + (0 if side < 0 else math.pi)
    logo_decal(nm, "DaKrasFilms_logo_white.png", cr, pt, (R_(90), 0, rz), wdt, CV)
    print("LOGO", nm, round(wdt, 2), tuple(round(c, 2) for c in pt))

# ================================================================== hospital (north, straight through the ridge from the village)
CH_ = "Hospital"
HY = 100.0
box("Hosp_Main", (34, 12, 9.0), (0, HY + 6, 4.5), M_WHITE, CH_, bevel=0.08)
box("Hosp_WingL", (10, 16, 6.2), (-21, HY + 8, 3.1), M_WHITE, CH_, bevel=0.08)
box("Hosp_WingR", (10, 16, 6.2), (21, HY + 8, 3.1), M_WHITE, CH_, bevel=0.08)
box("Hosp_Roof", (35, 13, 0.4), (0, HY + 6, 9.2), M_TRIM, CH_)
box("Hosp_RoofL", (10.8, 16.8, 0.35), (-21, HY + 8, 6.35), M_TRIM, CH_)
box("Hosp_RoofR", (10.8, 16.8, 0.35), (21, HY + 8, 6.35), M_TRIM, CH_)
for fl, z in ((0, 1.9), (1, 5.6)):
    for k in range(-6, 7):
        if fl == 0 and abs(k) < 2: continue
        box("Hosp_Win_%d_%d" % (fl, k), (1.5, 0.08, 1.5), (k * 2.5, HY - 0.02, z), M_GLASS, CH_)
for sx in (-1, 1):
    for k in range(3):
        box("Hosp_WWin_%d_%d" % (sx, k), (1.4, 0.08, 1.4), (sx * (18 + k * 3), HY - 0.02, 2.4), M_GLASS, CH_)
box("Hosp_Door", (3.2, 0.1, 2.6), (0, HY - 0.03, 1.3), M_GLASS, CH_)
box("Hosp_Canopy", (6.0, 2.6, 0.25), (0, HY - 1.3, 3.1), M_WHITE, CH_)
for sx in (-1, 1): box("Hosp_Post%d" % sx, (0.25, 0.25, 3.0), (sx * 2.8, HY - 2.4, 1.5), M_WHITE, CH_)
def red_cross(name, loc, rot, s):
    box(name + "_Panel", (s, 0.12, s), loc, M_SIGNW, CH_, rot=rot)
    off = Matrix.Rotation(rot[2], 3, 'Z') @ V((0, -0.08, 0)) if rot[0] == 0 else V((0, 0, 0.08))
    hw = (s * 0.7 - s * 0.22) / 2; R3 = Euler(rot).to_matrix()       # two side arms beside the vertical bar: no overlapping faces (they rendered a black centre)
    for sx in (-1, 1):
        box(name + "_H%d" % sx, (hw, 0.12, s * 0.22), V(loc) + off + R3 @ V((sx * (s * 0.11 + hw / 2), 0, 0)), M_RED, CH_, rot=rot)
    box(name + "_V", (s * 0.22, 0.12, s * 0.7), V(loc) + off, M_RED, CH_, rot=rot)
red_cross("Cross_Front", (0, HY - 0.1, 7.3), (0, 0, 0), 2.6)
red_cross("Cross_Roof", (0, HY + 6, 9.5), (R_(90), 0, 0), 7.0)     # flat on the roof, reads from the map views
# forecourt
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, HY - 12, 0.015)); fc = bpy.context.active_object; fc.name = "Hosp_Court"
fc.scale = (46, 24, 1); bpy.ops.object.transform_apply(scale=True); fc.data.materials.append(M_DIRT); link(fc, CH_)

# ================================================================== road: village -> east round the ridge end -> hospital
CR = "Road"
pts = [V((p[0], p[1], 0.0)) for p in [(-420, -73), (-200, -74), (-40, -74), (60, -73), (160, -74), (240, -68), (285, -30), (295, 10), (280, 50), (230, 75),
                      (140, 80), (60, 82), (20, 84), (0, 86)]]
def cr(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
samp = []
P_ = [pts[0]] + pts + [pts[-1]]
for i in range(1, len(P_) - 2):
    for k in range(40): samp.append(cr(P_[i - 1], P_[i], P_[i + 1], P_[i + 2], k / 40))
samp.append(pts[-1])
RW = 3.6
rv, rf_, cl = [], [], []
acc = 0.0
for i, p in enumerate(samp):
    d = (samp[min(i + 1, len(samp) - 1)] - samp[max(i - 1, 0)]); d.z = 0; d.normalize()
    n = V((-d.y, d.x, 0))
    rv += [(p.x + n.x * RW, p.y + n.y * RW, 0.04), (p.x - n.x * RW, p.y - n.y * RW, 0.04)]
    if i: rf_.append((2 * i - 2, 2 * i - 1, 2 * i + 1, 2 * i))
road = mesh_obj("Road", rv, rf_, M_ASPH, CR)
# centre line (double yellow) as thin strips
lv, lf = [], []
for off in (-0.12, 0.12):
    base = len(lv)
    for i, p in enumerate(samp):
        d = (samp[min(i + 1, len(samp) - 1)] - samp[max(i - 1, 0)]); d.z = 0; d.normalize(); n = V((-d.y, d.x, 0))
        q = p + n * off
        lv += [(q.x + n.x * 0.06, q.y + n.y * 0.06, 0.05), (q.x - n.x * 0.06, q.y - n.y * 0.06, 0.05)]
        if i: lf.append((base + 2 * i - 2, base + 2 * i - 1, base + 2 * i + 1, base + 2 * i))
mesh_obj("Road_Line", lv, lf, M_YEL, CR)
# the route line for the map shot (white glowing ribbon over the road; its build is keyed in 03_shots)
cu = bpy.data.curves.new("RouteLine", 'CURVE'); cu.dimensions = '3D'; spl = cu.splines.new('POLY'); spl.points.add(len(samp) - 1)
for i, p in enumerate(samp): spl.points[i].co = (p.x, p.y, 3.0, 1)
cu.bevel_depth = 2.2; cu.bevel_resolution = 2
M_ROUTE = flat("M_Route", (1, 1, 1), 0.5, emit=(1, 1, 1), estr=2.0)
rl = bpy.data.objects.new("RouteLine", cu); sc.collection.objects.link(rl); cu.materials.append(M_ROUTE); link(rl, CR)
rl.hide_render = rl.hide_viewport = True
sc["ROAD"] = [list(p[:2]) for p in samp]

# ================================================================== map graphics: blue straight arrow, red X, green length arrow
CM = "MapFX"
def arrow(name, length, width, head_l, head_w, mat, two_heads=False):
    """flat arrow along +Y from the origin (tail) to `length` (tip); 0.6 m thick"""
    t = 0.3; hl = head_l
    pts2 = [(-width / 2, hl if two_heads else 0), (width / 2, hl if two_heads else 0), (width / 2, length - hl), (head_w / 2, length - hl), (0, length),
            (-head_w / 2, length - hl), (-width / 2, length - hl)]
    if two_heads: pts2 = pts2[:2] + pts2[2:] + [(-head_w / 2, hl), (0, 0), (head_w / 2, hl)]
    bm = bmesh.new()
    bot = [bm.verts.new((x, y, -t)) for x, y in pts2]; top = [bm.verts.new((x, y, t)) for x, y in pts2]
    bm.faces.new(list(reversed(bot))); bm.faces.new(top)
    for k in range(len(pts2)): bm.faces.new((bot[k], bot[(k + 1) % len(pts2)], top[(k + 1) % len(pts2)], top[k]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); me.materials.append(mat); return link(o, CM)
M_BLUE = flat("M_ArrowBlue", (0.15, 0.35, 1.0), 0.4, emit=(0.15, 0.35, 1.0), estr=1.2)
M_XRED = flat("M_XRed", (1.0, 0.08, 0.12), 0.4, emit=(1.0, 0.08, 0.12), estr=1.2)
M_GREEN = flat("M_ArrowGreen", (0.2, 0.95, 0.3), 0.4, emit=(0.2, 0.95, 0.3), estr=1.2)
ab = arrow("Arrow_Blue", 1.0, 7.0, 0.0, 0.0, M_BLUE)      # placeholder replaced below (shaft only scales; the head is separate)
bpy.data.objects.remove(ab, do_unlink=True)
shaft = arrow("ArrowBlue_Shaft", 1.0, 7.0, 0.0001, 7.0, M_BLUE); shaft.location = (0, -66, 40)       # y-scale keyed (length)
head = arrow("ArrowBlue_Head", 16.0, 0.0001, 16.0, 20.0, M_BLUE); head.location = (0, -66, 40)       # y keyed to ride the shaft tip
xa = box("RedX_A", (34, 6, 1.0), (0, 0, 44), M_XRED, CM, rot=(0, 0, R_(45)))
xb = box("RedX_B", (34, 6, 1.0), (0, 0, 44), M_XRED, CM, rot=(0, 0, R_(-45)))
xr = bpy.data.objects.new("RedX", None); sc.collection.objects.link(xr); link(xr, CM); xr.location = (0, 0, 0)
for o in (xa, xb): o.parent = xr
ga = arrow("Arrow_Green", 2 * YF, 5.0, 10.0, 13.0, M_GREEN, two_heads=True); ga.location = (0, -YF, 33)
for o in (shaft, head, xa, xb, ga):
    o.hide_render = o.hide_viewport = True

# ================================================================== vegetation and boulders
CVG = "Vegetation"
tree_src = append_model("island_tree_01", CVG, (0, 0, 0))
shrub_src = append_model("shrub_01", CVG, (0, 0, 0))
boul_src = append_model("namaqualand_boulder_02", CVG, (0, 0, 0))
print("TREE parts", [(o.name, o.parent.name if o.parent else None) for o in tree_src][:6])
def far_from(p, pts, d): return all((V(p) - V(q)).length > d for q in pts)
KEEP = [(0, -60), (0, -66), (0, 60), (0, 75), (-8, -70), (0, -80)]
TP = []
for i in range(70):
    for _ in range(30):
        x = random.uniform(-90, 90); y = random.choice([random.uniform(-125, -58), random.uniform(58, 140)])
        if abs(x) < 9 and abs(y) < 100: continue            # keep the passage line and the village->ridge view clear
        if abs(y - 86) < 6 and x > -10 or abs(y + 73.5) < 7: continue  # keep the road clear
        if 75 < y < 120 and abs(x) < 30: continue          # hospital block and court
        if far_from((x, y), TP, 7) and far_from((x, y), [(h[0], h[1]) for h in HUTS], 6): break
    TP.append((x, y)); inst(tree_src, CVG, (x, y, 0), random.uniform(0, 6.28), random.uniform(0.8, 1.3), "Tree%02d" % i)
for i in range(60):
    x = random.uniform(-80, 80); y = random.choice([random.uniform(-120, -57), random.uniform(57, 130)])
    if abs(x) < 6 or abs(y + 73.5) < 6 or abs(y - 86) < 5: continue
    inst(shrub_src, CVG, (x, y, 0), random.uniform(0, 6.28), random.uniform(0.8, 1.6), "Shrub%02d" % i)
for i, (x, y, s) in enumerate([(-14, -55, 2.0), (13, -55, 1.6), (-12, 56, 1.3), (11, 57, 1.5), (-24, -57, 1.0), (22, -56, 1.3)]):
    inst(boul_src, CVG, (x, y, -0.2), random.uniform(0, 6.28), s, "Boulder%d" % i)
print("PSYS", [(o.name, len(o.particle_systems)) for o in tree_src])

# ================================================================== far land: rolling hills and tree belts (no bare plane to the horizon)
NH = 120; HS_ = 4000.0
hv_, hf_ = [], []
for j in range(NH + 1):
    for i in range(NH + 1):
        x = -HS_ / 2 + HS_ * i / NH; y = -HS_ / 2 + HS_ * j / NH
        r = math.hypot(x / 1.6, y)
        t = max(0.0, min(1.0, (r - 260.0) / 700.0))
        h = t ** 1.4 * (55 + 45 * noise.noise(V((x / 500.0, y / 500.0, 2.2)))) + t * 14 * noise.noise(V((x / 120.0, y / 120.0, 7.7)))
        hv_.append((x, y, h - 0.4 * (1 - t)))
for j in range(NH):
    for i in range(NH):
        hf_.append((j * (NH + 1) + i, j * (NH + 1) + i + 1, (j + 1) * (NH + 1) + i + 1, (j + 1) * (NH + 1) + i))
M_HILL = bpy.data.materials.new("M_Hills"); M_HILL.use_nodes = True; _nt = M_HILL.node_tree; _P = _nt.nodes["Principled BSDF"]
_tc = _nt.nodes.new('ShaderNodeTexCoord'); _nz = _nt.nodes.new('ShaderNodeTexNoise'); _nz.inputs['Scale'].default_value = 0.004; _nz.inputs['Detail'].default_value = 6.0
_nt.links.new(_tc.outputs['Object'], _nz.inputs['Vector'])
_cr = _nt.nodes.new('ShaderNodeValToRGB'); _nt.links.new(_nz.outputs['Fac'], _cr.inputs['Fac'])
_cr.color_ramp.elements[0].color = (0.16, 0.30, 0.09, 1); _cr.color_ramp.elements[1].color = (0.36, 0.48, 0.16, 1)
_nt.links.new(_cr.outputs['Color'], _P.inputs['Base Color']); _P.inputs['Roughness'].default_value = 0.85     # no visible texture tiling from the air
mesh_obj("FarHills", hv_, hf_, M_HILL, CT, smooth=True)
random.seed(77); far_trees = 0
for k in range(260):
    ang = random.uniform(0, 6.283); rr = random.uniform(150, 420)
    x, y = math.cos(ang) * rr * 1.5, math.sin(ang) * rr
    if abs(x) < 280 and abs(y) < 70: continue          # not on the ridge
    if abs(y + 73.5) < 8 or (x > 200 and abs(y) < 90): continue
    if 80 < y < 125 and abs(x) < 35: continue
    inst(tree_src, CVG, (x, y, 0), random.uniform(0, 6.28), random.uniform(1.0, 1.8), "FarTree%03d" % k); far_trees += 1
print("FAR trees", far_trees)

# ================================================================== light and world
sunL = bpy.data.lights.new("Sun", 'SUN'); sunL.energy = 4.2; sunL.angle = R_(2.5); sunL.color = (1.0, 0.96, 0.9)
sun = bpy.data.objects.new("Sun", sunL); sc.collection.objects.link(sun); sun.rotation_euler = (R_(48), 0, R_(-25))
# soft skylight down the passage (it is 3.6 m wide and up to 30 m deep): invisible to camera, lights the gorge floor and walls
GL = bpy.data.lights.new("GorgeSky", 'AREA'); GL.shape = 'RECTANGLE'; GL.size = 3.4; GL.size_y = 130; GL.energy = 30000; GL.color = (0.92, 0.96, 1.0)
gl = bpy.data.objects.new("GorgeSky", GL); sc.collection.objects.link(gl); gl.location = (0, 0, 9.0); gl.visible_camera = False
w = bpy.data.worlds.new("W_Day"); sc.world = w; w.use_nodes = True; nt = w.node_tree
bg = nt.nodes["Background"]; bg.inputs['Strength'].default_value = 1.0
tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Generated'], sep.inputs[0])
ramp = nt.nodes.new('ShaderNodeValToRGB'); nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (0.72, 0.86, 1.0, 1)
ramp.color_ramp.elements[1].position = 0.6; ramp.color_ramp.elements[1].color = (0.2, 0.45, 0.9, 1)
nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
r = sc.render; r.engine = 'CYCLES'; r.resolution_x, r.resolution_y = 1080, 1920; r.fps = 60
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except TypeError: sc.view_settings.look = 'Punchy'
r.use_motion_blur = False
sc["YF"] = YF; sc["HY"] = HY
for o in (cutter, lcut):     # cutters must never block a ray (LESSONS s2.14)
    for a_ in ("visible_camera", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter", "visible_shadow"):
        setattr(o, a_, False)
for m in [m for m in bpy.data.materials if m.name.startswith("M_Mud") or m.name.startswith("M_Thatch")]: pass
# (texture packing happens at packaging time in Phase 2)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SETS_OK", len(bpy.data.objects))
