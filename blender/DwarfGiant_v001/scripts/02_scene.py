"""Sets + assets for DwarfGiant.  blender -b people.blend --python 02_scene.py -- <assets_dir> <out.blend>"""
import bpy, bmesh, os, sys, math, glob
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]
A, OUT = a[0], a[1]
R_ = math.radians
sc = bpy.context.scene
sc.render.fps = 60; sc.frame_start = 1; sc.frame_end = 2340
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 48
sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"

def col(name):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name); sc.collection.children.link(c)
    return c

def link(o, c):
    for cc in list(o.users_collection): cc.objects.unlink(o)
    col(c).objects.link(o)

# ------------------------------------------------------------------ materials
def tex(nt, path, cs="Non-Color", proj="BOX"):
    n = nt.nodes.new("ShaderNodeTexImage"); n.image = bpy.data.images.load(path, check_existing=True)
    n.image.colorspace_settings.name = cs; n.projection = proj; n.projection_blend = 0.2
    return n

def pbr(name, folder, scale=1.0, tint=None, coords="Object", bump=0.4, rough_mul=1.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs[coords], mp.inputs[0])
    fs = glob.glob(f"{A}/{folder}/textures/*") + glob.glob(f"{A}/{folder}/*.jpg")
    pick = lambda k: next((f for f in sorted(fs) if k in os.path.basename(f) and not f.endswith(".blend")), None)
    proj = "BOX" if coords == "Object" else "FLAT"
    d = pick("_diff_")
    if d:
        t = tex(nt, d, "sRGB", proj); nt.links.new(mp.outputs[0], t.inputs[0])
        if tint:
            mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"
            mx.inputs[0].default_value = 1.0; mx.inputs[7].default_value = (*tint, 1)
            nt.links.new(t.outputs[0], mx.inputs[6]); nt.links.new(mx.outputs[2], bs.inputs["Base Color"])
        else:
            nt.links.new(t.outputs[0], bs.inputs["Base Color"])
    r = pick("_rough_")
    if r:
        t = tex(nt, r, proj=proj); nt.links.new(mp.outputs[0], t.inputs[0])
        if rough_mul != 1.0:
            mm = nt.nodes.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.inputs[1].default_value = rough_mul
            nt.links.new(t.outputs[0], mm.inputs[0]); nt.links.new(mm.outputs[0], bs.inputs["Roughness"])
        else:
            nt.links.new(t.outputs[0], bs.inputs["Roughness"])
    n = pick("_nor_gl_")
    if n:
        t = tex(nt, n, proj=proj); nt.links.new(mp.outputs[0], t.inputs[0])
        nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs[0].default_value = 1.0
        nt.links.new(t.outputs[0], nm.inputs[1])
        dp = pick("_disp_")
        if dp and bump:
            t2 = tex(nt, dp, proj=proj); nt.links.new(mp.outputs[0], t2.inputs[0])
            bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.01
            nt.links.new(t2.outputs[0], bp.inputs["Height"]); nt.links.new(nm.outputs[0], bp.inputs["Normal"])
            nt.links.new(bp.outputs[0], bs.inputs["Normal"])
        else:
            nt.links.new(nm.outputs[0], bs.inputs["Normal"])
    return m

def box(name, c, lo, hi, mat, bevel=0.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector([lo[i] + (v.co[i] + 0.5) * (hi[i] - lo[i]) for i in range(3)])
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); col(c).objects.link(o); me.materials.append(mat)
    if bevel:
        b = o.modifiers.new("bev", "BEVEL"); b.width = bevel; b.segments = 2
    return o

def imp(name, path, size, loc, rz=0.0, c="SET", axis=2, rx=0.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(name, None); col(c).objects.link(root)
    pts = [o.matrix_world @ Vector(b) for o in new if o.type == "MESH" for b in o.bound_box]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    s = size / (mx - mn)[axis]
    ctr = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    for o in new:
        link(o, c)
        if o.parent is None:
            o.parent = root; o.matrix_parent_inverse = Matrix.Scale(s, 4) @ Matrix.Translation(-ctr)
    root.location = loc; root.rotation_euler = (R_(rx), 0, R_(rz))
    print("IMP", name, round(s, 4), tuple(round(v, 2) for v in (mx - mn) * s))
    return root

def append_ph(folder, c="SET"):
    p = glob.glob(f"{A}/{folder}/*.blend")[0]
    with bpy.data.libraries.load(p) as (src, dst): dst.objects = list(src.objects)
    objs = [o for o in dst.objects if o]
    for o in objs: col(c).objects.link(o)
    return objs

M = lambda n: f"{A}/models/{n}.glb"
WALL = pbr("M_Plaster", "plastered_wall_02", 0.6, tint=(0.93, 0.86, 0.72), bump=0.6)
WALL_LOW = pbr("M_PlasterBrick", "rough_plasterbrick_05", 0.5, tint=(0.75, 0.68, 0.58))
FLOOR = pbr("M_Parquet", "herringbone_parquet", 0.5, tint=(0.85, 0.72, 0.58))
PLANK = pbr("M_Planks", "worn_planks", 0.6)
TILE = pbr("M_Tiles", "long_white_tiles", 0.7, tint=(0.88, 0.93, 0.9))
WOOD = pbr("M_WoodTrim", "wood_table_001", 1.0, tint=(0.55, 0.38, 0.25))
GRASS = pbr("M_Grass", "leafy_grass", 0.6, tint=(0.75, 0.9, 0.6))
MUD = pbr("M_ForestGround", "forrest_ground_01", 0.25)

# ------------------------------------------------------------------ OFFICE (x -3.5..3.5, y -3..3, h 3.2)
H = 3.2
box("Off_Floor", "OFFICE", (-3.5, -3.0, -0.05), (3.5, 3.0, 0.0), FLOOR)
box("Off_Ceil", "OFFICE", (-3.5, -3.0, H), (3.5, 3.0, H + 0.1), WALL)
box("Off_WallL", "OFFICE", (-3.65, -3.0, 0), (-3.5, 3.15, H), WALL)
box("Off_WallR", "OFFICE", (3.5, -3.0, 0), (3.65, 3.15, H), WALL)       # shared with theatre
box("Off_WallF", "OFFICE", (-3.65, -3.15, 0), (3.65, -3.0, H), WALL)
WX0, WX1, WZ0, WZ1 = 0.9, 2.3, 1.0, 2.55
box("Off_WallB1", "OFFICE", (-3.65, 3.0, 0), (WX0, 3.15, H), WALL)
box("Off_WallB2", "OFFICE", (WX1, 3.0, 0), (3.65, 3.15, H), WALL)
box("Off_WallB3", "OFFICE", (WX0, 3.0, 0), (WX1, 3.15, WZ0), WALL)
box("Off_WallB4", "OFFICE", (WX0, 3.0, WZ1), (WX1, 3.15, H), WALL)
# wainscot + skirting
for nm, lo, hi in (("Off_WainB", (-3.5, 2.97, 0), (WX0, 3.0, 0.95)), ("Off_WainB2", (WX1, 2.97, 0), (3.5, 3.0, 0.95)),
                   ("Off_WainL", (-3.5, -3.0, 0), (-3.47, 3.0, 0.95)), ("Off_WainR", (3.47, -3.0, 0), (3.5, 3.0, 0.95))):
    box(nm, "OFFICE", lo, hi, PLANK)
for nm, lo, hi in (("Off_RailB", (-3.5, 2.955, 0.93), (WX0, 3.0, 0.98)), ("Off_RailB2", (WX1, 2.955, 0.93), (3.5, 3.0, 0.98)),
                   ("Off_RailL", (-3.5, -3.0, 0.93), (-3.455, 3.0, 0.98)), ("Off_RailR", (3.455, -3.0, 0.93), (3.5, 3.0, 0.98))):
    box(nm, "OFFICE", lo, hi, WOOD, 0.008)
# window frame + mullions + glass
for nm, lo, hi in (("Win_L", (WX0 - 0.06, 2.95, WZ0 - 0.06), (WX0, 3.15, WZ1 + 0.06)), ("Win_R", (WX1, 2.95, WZ0 - 0.06), (WX1 + 0.06, 3.15, WZ1 + 0.06)),
                   ("Win_T", (WX0, 2.95, WZ1), (WX1, 3.15, WZ1 + 0.06)), ("Win_Sill", (WX0 - 0.1, 2.88, WZ0 - 0.05), (WX1 + 0.1, 3.15, WZ0)),
                   ("Win_MV", ((WX0 + WX1) / 2 - 0.025, 3.06, WZ0), ((WX0 + WX1) / 2 + 0.025, 3.1, WZ1)),
                   ("Win_MH", (WX0, 3.06, 1.85), (WX1, 3.1, 1.89))):
    box(nm, "OFFICE", lo, hi, WOOD, 0.006)
GLASS = bpy.data.materials.new("M_Glass"); GLASS.use_nodes = True
gb = GLASS.node_tree.nodes["Principled BSDF"]; gb.inputs["Transmission Weight"].default_value = 1.0; gb.inputs["Roughness"].default_value = 0.03
gb.inputs["IOR"].default_value = 1.2
box("Win_Glass", "OFFICE", (WX0, 3.075, WZ0), (WX1, 3.08, WZ1), GLASS)
# props
imp("Door", M("door"), 2.15, (-1.75, 2.96, 0.0), rz=90, c="OFFICE")
imp("Gauge", M("gauge"), 2.05, (-0.3, 2.82, 0.0), rz=180, c="OFFICE")
dk = imp("Desk", M("desk"), 1.55, (0.36, 1.95, 0.0), rz=90, c="OFFICE", axis=0); dk.scale = (1, 1, 1.2)   # tall standing clerk desk
imp("DeskLamp", M("lamp"), 0.42, (0.45, 2.5, 0.948), rz=200, c="OFFICE")
imp("Chair", M("chair"), 0.95, (1.75, 1.2, 0.0), rz=60, c="OFFICE")
imp("Mirror", M("mirror"), 2.15, (1.25, 2.72, 0.0), rz=-79, c="OFFICE")
try:
    for o in append_ph("wooden_bookshelf_worn", "OFFICE"):
        if o.parent is None: o.location = (-3.25, -0.6, 0); o.rotation_euler = (0, 0, R_(-90))
    for o in append_ph("book_encyclopedia_set_01", "OFFICE"):
        if o.parent is None: o.location = (0.4, 1.45, 0.948); o.rotation_euler = (0, 0, R_(90)); o.scale = (0.8,) * 3
except Exception as e: print("PH ERR", e)
for o in bpy.data.objects:                     # mirror glass: real mirror
    if o.type == "MESH" and o.data.materials and any(m and m.name.startswith("Mirror") for m in o.data.materials):
        for m in o.data.materials:
            if m and m.name.startswith("Mirror"):
                b = m.node_tree.nodes.get("Principled BSDF")
                for k in ("Base Color", "Metallic", "Roughness"):
                    for l_ in list(b.inputs[k].links): m.node_tree.links.remove(l_)
                if b: b.inputs["Metallic"].default_value = 1.0; b.inputs["Roughness"].default_value = 0.03; b.inputs["Base Color"].default_value = (0.9, 0.9, 0.9, 1)
# bench for recruits
imp("Chair2", M("chair"), 0.95, (-3.05, 0.9, 0.0), rz=-90, c="OFFICE")
imp("Chair3", M("chair"), 0.95, (-3.05, -0.1, 0.0), rz=-90, c="OFFICE")

# ------------------------------------------------------------------ THEATRE (x 3.65..10, y -3..3)
TX0, TX1 = 3.65, 10.0
box("Th_Floor", "THEATRE", (TX0, -3.0, -0.05), (TX1, 3.0, 0.0), TILE)
box("Th_Ceil", "THEATRE", (TX0, -3.0, H), (TX1, 3.0, H + 0.1), WALL)
box("Th_WallR", "THEATRE", (TX1, -3.0, 0), (TX1 + 0.15, 3.15, H), TILE)
box("Th_WallF", "THEATRE", (TX0, -3.15, 0), (TX1 + 0.15, -3.0, H), TILE)
TW0, TW1, TZ0, TZ1 = 6.0, 8.2, 1.1, 2.9
box("Th_WallB1", "THEATRE", (TX0, 3.0, 0), (TW0, 3.15, H), TILE)
box("Th_WallB2", "THEATRE", (TW1, 3.0, 0), (TX1 + 0.15, 3.15, H), TILE)
box("Th_WallB3", "THEATRE", (TW0, 3.0, 0), (TW1, 3.15, TZ0), TILE)
box("Th_WallB4", "THEATRE", (TW0, 3.0, TZ1), (TW1, 3.15, H), TILE)
box("Th_WallL", "THEATRE", (TX0 - 0.004, -3.0, 0), (TX0 + 0.01, 3.15, H), TILE)   # theatre face only; must not overlap Off_WallR   # theatre side of the shared wall
for i in range(4):
    x = TW0 + i * (TW1 - TW0) / 3
    box(f"ThWin_M{i}", "THEATRE", (x - 0.03, 2.98, TZ0), (x + 0.03, 3.12, TZ1), WOOD, 0.005)
box("ThWin_H", "THEATRE", (TW0, 2.98, 2.0), (TW1, 3.12, 2.05), WOOD, 0.005)
box("ThWin_Glass", "THEATRE", (TW0, 3.075, TZ0), (TW1, 3.08, TZ1), GLASS)
imp("Bed", M("ironbed"), 1.77, (6.9, 0.6, 0.0), rz=0, c="THEATRE", axis=1)
imp("Trolley", M("optable"), 1.3, (5.2, 1.6, 0.0), rz=90, c="THEATRE", axis=0)
imp("ThDoor", M("door"), 2.15, (9.97, -1.4, 0.0), rz=0, c="THEATRE")
try:
    for o in append_ph("hanging_industrial_lamp", "THEATRE"):
        if o.parent is None: o.location = (6.9, 0.85, 2.75); o.scale = (1.0,) * 3
except Exception as e: print("PH ERR", e)

# ------------------------------------------------------------------ EXTERIOR (behind the back walls, y > 3.15)
me = bpy.data.meshes.new("Ext_Ground"); bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=120, y_segments=120, size=40)
for v in bm.verts:
    v.co.y += 43.2
    d = max(0.0, v.co.y - 6.0)
    v.co.z = -0.02 + 0.03 * math.sin(v.co.x * 1.3) * math.sin(v.co.y * 0.9) + 0.06 * math.sin(v.co.x * 0.35) * math.sin(v.co.y * 0.27) * (d > 2)
bm.to_mesh(me); bm.free()
gnd = bpy.data.objects.new("Ext_Ground", me); col("EXTERIOR").objects.link(gnd); me.materials.append(GRASS)
for p in me.polygons: p.use_smooth = True
try:
    tree_objs = append_ph("tree_small_02", "EXTERIOR")
    for o in [o for o in tree_objs if "LOD1" in o.name or "LOD2" in o.name or "LOD3" in o.name]:
        tree_objs.remove(o); bpy.data.objects.remove(o, do_unlink=True)
    troots = [o for o in tree_objs if o.parent is None]
    import random as _r; _r.seed(5)
    for o in tree_objs:                      # thin the heavy leaf/twig meshes (memory + package size)
        if o.type != "MESH" or len(o.data.polygons) < 50000: continue
        bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
        seen = set(); kill = []
        keep_ratio = 0.22 if len(o.data.polygons) > 800000 else 0.4
        for f in bm.faces:
            if f.index in seen: continue
            isl = []; stack = [f]; seen.add(f.index)
            while stack:
                g = stack.pop(); isl.append(g)
                for e in g.edges:
                    for h in e.link_faces:
                        if h.index not in seen: seen.add(h.index); stack.append(h)
            if len(isl) < 400 and _r.random() > keep_ratio: kill += isl
        bmesh.ops.delete(bm, geom=kill, context="FACES"); bm.to_mesh(o.data); bm.free()
        print("TREE THIN", o.name, len(o.data.polygons))
    for k, (x, y, s, rz) in enumerate(((1.9, 6.5, 1.0, 0), (-2.0, 9.5, 1.3, 70), (5.0, 12.0, 1.2, 140), (14.5, 10.5, 1.1, 200), (-6, 14, 1.4, 30), (6, 25, 1.8, 10), (13, 23, 1.9, 220))):
        for o in troots:
            oo = o if k == 0 else o.copy()
            if k: col("EXTERIOR").objects.link(oo)
            oo.location = (x, y, 0); oo.scale = (s,) * 3; oo.rotation_euler = (0, 0, R_(rz)); oo.name = f"Tree{k}"
except Exception as e: print("PH ERR", e)
gr = imp("Graves", M("celtic"), 1.45, (5.2, 9.2, -0.02), rz=180, c="EXTERIOR", axis=2)
for o in list(gr.children_recursive):
    if o.type == "MESH" and any(m and "snow" in m.name for m in o.data.materials): bpy.data.objects.remove(o, do_unlink=True)
gr3 = imp("HeroStone", M("tombs"), 1.25, (8.6, 8.55, -0.02), rz=180, c="EXTERIOR", axis=2)
gr2 = imp("Graves2", M("tombs"), 1.4, (4.6, 13.0, -0.02), rz=165, c="EXTERIOR", axis=2)
try:
    gobjs = append_ph("grass_medium_01", "EXTERIOR")
    gcol = bpy.data.collections.new("GRASS_INST")
    keep = [o for o in gobjs if o.type == "MESH" and "geonodes" not in o.name and "sphere" not in o.name and "geometry" not in o.name and o.name.endswith("LOD1") and any(k in o.name for k in ("_mid_", "_small_", "_tall_"))]
    for o in gobjs:
        if o not in keep: bpy.data.objects.remove(o, do_unlink=True)
    gobjs = keep
    for o in gobjs:
        o.location = (0, 0, -50)
        for c in list(o.users_collection): c.objects.unlink(o)
        gcol.objects.link(o)
    sc.collection.children.link(gcol); gcol.hide_render = False
    vg = gnd.vertex_groups.new(name="dense")
    for v in gnd.data.vertices:
        w = 1.0 if (6.5 < v.co.x < 14.0 and 4.5 < v.co.y < 13.5) else 0.0
        vg.add([v.index], w, "REPLACE")
    ps = gnd.modifiers.new("grass", "PARTICLE_SYSTEM").particle_system; st = ps.settings
    st.type = "HAIR"; st.use_advanced_hair = True; st.count = 2500; st.hair_length = 1.0; st.render_type = "COLLECTION"
    st.instance_collection = gcol; st.particle_size = 0.9; st.size_random = 0.5; st.use_rotations = True; st.rotation_mode = "OB_Z"
    st.phase_factor_random = 2.0; ps.vertex_group_density = "dense"; st.use_collection_pick_random = True
except Exception as e: print("GRASS ERR", e)
# fresh grave mound for the hero (soil, displaced)
me = bpy.data.meshes.new("Grave_Mound"); bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=24, y_segments=48, size=1.0)
for v in bm.verts:
    u, w = v.co.x, v.co.y
    v.co.x *= 0.55; v.co.y *= 1.35
    v.co.z = max(0.0, 0.22 * (1 - u * u) * (1 - w ** 4)) + 0.012 * math.sin(u * 37) * math.sin(w * 23)
bm.to_mesh(me); bm.free()
mound = bpy.data.objects.new("Grave_Mound", me); col("EXTERIOR").objects.link(mound); me.materials.append(MUD)
mound.location = (8.6, 7.0, -0.02)
for p in me.polygons: p.use_smooth = True
sub = mound.modifiers.new("sub", "SUBSURF"); sub.levels = 1; sub.render_levels = 2

# ------------------------------------------------------------------ cutaway backdrop (sphere, inward), gradient teal -> navy, fade via alpha
me = bpy.data.meshes.new("XBack"); bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=1.0)
bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
xb = bpy.data.objects.new("XBack", me); col("CUTAWAY").objects.link(xb)
m = bpy.data.materials.new("M_XBack"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
o_ = nt.nodes.new("ShaderNodeOutputMaterial"); tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Object"], sep.inputs[0])
ramp = nt.nodes.new("ShaderNodeValToRGB"); mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value = -1; mr.inputs[2].default_value = 1
nt.links.new(sep.outputs[2], mr.inputs[0]); nt.links.new(mr.outputs[0], ramp.inputs[0])
ramp.color_ramp.elements[0].color = (0.004, 0.012, 0.045, 1); ramp.color_ramp.elements[1].color = (0.02, 0.16, 0.2, 1)
ramp.color_ramp.elements[1].position = 0.8
em = nt.nodes.new("ShaderNodeEmission"); nt.links.new(ramp.outputs[0], em.inputs[0]); em.inputs[1].default_value = 1.0
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mix = nt.nodes.new("ShaderNodeMixShader"); mix.name = "FADE"
nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], o_.inputs[0])
mix.inputs[0].default_value = 0.0
me.materials.append(m)
xb.visible_shadow = False

# brain + pituitary/tumour
br = imp("Brain", M("brain"), 0.155, (0, 0, 0), c="CUTAWAY", axis=0)
for o in br.children_recursive:
    if o.type == "MESH":
        for mm in o.data.materials:
            b = mm.node_tree.nodes.get("Principled BSDF")
            if b:
                b.inputs["Subsurface Weight"].default_value = 0.35; b.inputs["Subsurface Radius"].default_value = (0.9, 0.35, 0.25)
                b.inputs["Subsurface Scale"].default_value = 0.004; b.inputs["Roughness"].default_value = 0.28
                b.inputs["Coat Weight"].default_value = 0.4; b.inputs["Coat Roughness"].default_value = 0.08
for nm, r, colr, emis in (("Pituitary", 0.0055, (0.75, 0.42, 0.36), 0.0), ("Tumour", 0.006, (0.85, 0.5, 0.3), 1.0)):
    me = bpy.data.meshes.new(nm); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=4, radius=r); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(nm, me); col("CUTAWAY").objects.link(o)
    for p in me.polygons: p.use_smooth = True
    tx = bpy.data.textures.new(nm + "_n", "VORONOI" if nm == "Tumour" else "CLOUDS"); tx.noise_scale = 0.25 if nm == "Tumour" else 0.4
    d = o.modifiers.new("disp", "DISPLACE"); d.texture = tx; d.strength = r * 0.35; d.texture_coords = "LOCAL"
    mm = bpy.data.materials.new("M_" + nm); mm.use_nodes = True; b = mm.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*colr, 1); b.inputs["Subsurface Weight"].default_value = 0.6
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.4, 0.3); b.inputs["Subsurface Scale"].default_value = 0.003
    b.inputs["Roughness"].default_value = 0.25; b.inputs["Coat Weight"].default_value = 0.5
    b.inputs["Emission Color"].default_value = (1.0, 0.55, 0.2, 1); b.inputs["Emission Strength"].default_value = 0.0
    nt = mm.node_tree; tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 900.0; nz.inputs["Detail"].default_value = 8.0
    vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 1400.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
    rp = nt.nodes.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].color = (colr[0] * 0.55, colr[1] * 0.3, colr[2] * 0.3, 1)
    rp.color_ramp.elements[1].color = (*colr, 1); nt.links.new(nz.outputs["Fac"], rp.inputs[0]); nt.links.new(rp.outputs[0], b.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; bp.inputs["Distance"].default_value = 0.0004
    mxv = nt.nodes.new("ShaderNodeMath"); mxv.operation = "ADD"; nt.links.new(nz.outputs["Fac"], mxv.inputs[0]); nt.links.new(vo.outputs["Distance"], mxv.inputs[1])
    nt.links.new(mxv.outputs[0], bp.inputs["Height"]); nt.links.new(bp.outputs[0], b.inputs["Normal"])
    d.strength = r * 0.7
    me.materials.append(mm)
imp("Spine", M("spine"), 0.62, (0, 0, 0), c="CUTAWAY")

# ------------------------------------------------------------------ world + lights
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; nt = w.node_tree
env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(f"{A}/hdri/kloppenheim_06_2k.hdr")
env2 = nt.nodes.new("ShaderNodeTexSky")
for t_ in ("MULTIPLE_SCATTERING", "NISHITA", "SINGLE_SCATTERING", "HOSEK_WILKIE"):
    try: env2.sky_type = t_; break
    except Exception: pass
try:
    env2.sun_elevation = math.radians(2.5); env2.sun_rotation = math.radians(90); env2.air_density = 1.2; env2.aerosol_density = 3.0
except Exception as e: print("SKY ERR", e)
print("SKY", env2.sky_type)
mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.name = "DUSK"; mx.inputs[0].default_value = 0.0
nt.links.new(env.outputs[0], mx.inputs[6]); nt.links.new(env2.outputs[0], mx.inputs[7])
bg = nt.nodes["Background"]; nt.links.new(mx.outputs[2], bg.inputs[0]); bg.inputs[1].default_value = 1.0
sun = bpy.data.lights.new("Sun", "SUN"); sun.energy = 3.5; sun.angle = R_(1.5); sun.color = (1.0, 0.92, 0.8)
so = bpy.data.objects.new("Sun", sun); col("LIGHTS").objects.link(so); so.rotation_euler = (R_(62), 0, R_(165))
sl = bpy.data.lights.new("Off_Sconce", "POINT"); sl.energy = 70; sl.color = (1.0, 0.8, 0.55); sl.shadow_soft_size = 0.05
slo = bpy.data.objects.new("Off_Sconce", sl); col("LIGHTS").objects.link(slo); slo.location = (3.2, 0.6, 2.35)
for nm, loc, e, sz, colr in (("Off_Key", (0.6, 0.0, 3.1), 260, 2.0, (1.0, 0.9, 0.75)), ("Off_Fill", (-2.5, -2.0, 2.4), 90, 2.5, (0.8, 0.85, 1.0)),
                             ("Th_Key", (6.9, 0.9, 3.1), 300, 1.5, (0.95, 1.0, 1.0)), ("Th_Fill", (5.0, -2.0, 2.5), 80, 2.5, (0.9, 0.95, 1.0))):
    l = bpy.data.lights.new(nm, "AREA"); l.energy = e; l.size = sz; l.color = colr
    lo = bpy.data.objects.new(nm, l); col("LIGHTS").objects.link(lo); lo.location = loc
print("MESHES", len([o for o in bpy.data.objects if o.type == "MESH"]))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
