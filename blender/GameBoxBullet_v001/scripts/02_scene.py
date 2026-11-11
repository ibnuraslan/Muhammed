"""Build the set: street, lawn, house wall layers, bedroom, props, the collector's box, bullet.
blender -b work/man.blend --python scripts/02_scene.py -- work/scene.blend"""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix

OUT = sys.argv[sys.argv.index("--") + 1]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "assets")
sc = bpy.context.scene
random.seed(15)
R_ = math.radians

sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.fps, sc.render.fps_base = 60, 1.0
sc.frame_start, sc.frame_end = 1, 1500
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 8; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3
sc.cycles.transmission_bounces = 8; sc.cycles.transparent_max_bounces = 16
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
sc.render.use_persistent_data = True
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
sc.render.image_settings.file_format = "PNG"

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
C_EXT, C_WALL, C_ROOM, C_BOX, C_FX = coll("Exterior"), coll("Wall"), coll("Bedroom"), coll("Box"), coll("FX")

def link(o, c):
    for u in list(o.users_collection): u.objects.unlink(o)
    c.objects.link(o); return o

def mesh_obj(name, bm, c, mat=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); c.objects.link(o)
    if mat: me.materials.append(mat)
    return o

def box(name, c, x0, x1, y0, y1, z0, z1, mat=None, bevel=0.0):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector(((x0 + x1) / 2 + v.co.x * (x1 - x0), (y0 + y1) / 2 + v.co.y * (y1 - y0), (z0 + z1) / 2 + v.co.z * (z1 - z0)))
    uvl = bm.loops.layers.uv.new("UVMap")
    for fc_ in bm.faces:
        nx, ny, nz = (abs(x) for x in fc_.normal)
        for lp in fc_.loops:
            co = lp.vert.co
            lp[uvl].uv = (co.y, co.z) if nx >= max(ny, nz) else ((co.x, co.z) if ny >= nz else (co.x, co.y))
    o = mesh_obj(name, bm, c, mat)
    if bevel:
        m = o.modifiers.new("bev", "BEVEL"); m.width = bevel; m.segments = 2
    return o

def cut_hole(o, r, axis_y=True, y0=-1, y1=1, x=0.0, z=1.47, jag=0.0, seed=0):
    """boolean-difference a ragged hole along Y through o"""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=r, radius2=r, depth=(y1 - y0))
    rnd = random.Random(seed)
    for v in bm.verts:
        a = math.atan2(v.co.y, v.co.x); k = 1 + jag * (rnd.random() - 0.5) * 2
        v.co.x *= k; v.co.y *= k
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(R_(90), 3, 'X'))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(x, (y0 + y1) / 2, z))
    cut = mesh_obj(o.name + "_cut", bm, sc.collection)
    m = o.modifiers.new("hole", "BOOLEAN"); m.object = cut; m.operation = "DIFFERENCE"; m.solver = "EXACT"
    bpy.context.view_layer.objects.active = o
    for s in bpy.context.selected_objects: s.select_set(False)
    o.select_set(True)
    bpy.ops.object.modifier_apply(modifier="hole")
    bpy.data.objects.remove(cut, do_unlink=True)

# ------------------------------------------------------------------ materials
def load_mat(name):
    p = os.path.join(A, name, name + "_1k.blend")
    with bpy.data.libraries.load(p, link=False) as (s, d): d.materials = [name]
    return bpy.data.materials[name]

def mapping_scale(mat, s):
    for n in mat.node_tree.nodes:
        if n.type == "MAPPING": n.inputs["Scale"].default_value = (s, s, s)
        if n.type == "DISPLACEMENT": n.inputs["Scale"].default_value = 0.0

def P(name, col, rough=0.5, metal=0.0, emit=None, ew=0.0, alpha=1.0, trans=0.0, ior=1.45, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    b.inputs["Transmission Weight"].default_value = trans; b.inputs["IOR"].default_value = ior
    b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = ew
    return m

def tint(mat, col, name):
    """copy of a scanned material multiplied by a colour"""
    m = mat.copy(); m.name = name; nt = m.node_tree
    b = [n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"][0]
    l = b.inputs["Base Color"].links
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.inputs[0].default_value = 1.0
    mix.inputs[7].default_value = (*col, 1)
    if l:
        nt.links.new(l[0].from_socket, mix.inputs[6])
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    return m

M_grass = tint(load_mat("leafy_grass"), (0.55, 0.85, 0.45), "M_lawn"); mapping_scale(M_grass, 3)
M_leafy = load_mat("leafy_grass"); mapping_scale(M_leafy, 10)
M_asph = load_mat("asphalt_02"); mapping_scale(M_asph, 8)
M_conc = load_mat("concrete_floor"); mapping_scale(M_conc, 6)
M_siding0 = load_mat("weathered_plank_siding"); mapping_scale(M_siding0, 3)
M_siding = tint(M_siding0, (1.25, 1.35, 1.5), "M_siding_blue")
M_plaster0 = load_mat("painted_plaster_wall"); mapping_scale(M_plaster0, 2)
M_wall_room = tint(M_plaster0, (0.42, 0.47, 0.60), "M_room_wall")
M_drywall = tint(M_plaster0, (0.95, 0.95, 0.93), "M_drywall")
M_floor = tint(load_mat("old_wooden_floor_02"), (1.6, 1.35, 1.1), "M_floor"); mapping_scale(M_floor, 1.5)
M_roof = load_mat("grey_roof_tiles"); mapping_scale(M_roof, 4)
M_carpet = tint(load_mat("dirty_carpet"), (0.75, 0.72, 0.85), "M_rug"); mapping_scale(M_carpet, 2)
M_denim = load_mat("denim_fabric"); mapping_scale(M_denim, 3)

M_osb = P("M_osb", (0.55, 0.40, 0.22), 0.8)
M_stud = P("M_stud", (0.78, 0.62, 0.40), 0.7)
M_insul = P("M_insulation", (0.92, 0.62, 0.62), 1.0)
M_glass = P("M_glass", (0.85, 0.9, 0.95), 0.03, trans=1.0, ior=1.5)
M_trim = P("M_trim", (0.92, 0.92, 0.9), 0.4)
M_door = P("M_door", (0.35, 0.10, 0.08), 0.35, coat=0.5)
M_white = P("M_white_paint", (0.85, 0.85, 0.83), 0.45)
M_blackplastic = P("M_black_plastic", (0.02, 0.02, 0.025), 0.35)
M_desk = P("M_desk", (0.12, 0.10, 0.09), 0.5)
M_metal = P("M_metal", (0.6, 0.6, 0.62), 0.3, metal=1.0)
M_bed = P("M_bedsheet", (0.20, 0.26, 0.36), 0.9)
M_pillow = P("M_pillow", (0.85, 0.85, 0.82), 0.9)
M_wood_light = P("M_shelf", (0.55, 0.42, 0.30), 0.55)
M_led = P("M_led", (0.4, 0.1, 0.9), 0.5, emit=(0.55, 0.2, 1.0), ew=8)
M_bush_dark = P("M_hedge", (0.06, 0.16, 0.05), 0.8)

# ------------------------------------------------------------------ world
wd = bpy.data.worlds.new("W_day"); sc.world = wd; wd.use_nodes = True
nt = wd.node_tree; nt.nodes.clear()
tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value[2] = R_(200)
env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(A, "hdri", "residential_garden_2k.hdr"))
bg = nt.nodes.new("ShaderNodeBackground"); bg.inputs["Strength"].default_value = 1.0
out = nt.nodes.new("ShaderNodeOutputWorld")
nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"]); nt.links.new(mp.outputs[0], env.inputs[0])
nt.links.new(env.outputs[0], bg.inputs[0])
lp_ = nt.nodes.new("ShaderNodeLightPath"); skyg = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], skyg.inputs[0])
sr = nt.nodes.new("ShaderNodeValToRGB"); sr.color_ramp.elements[0].position = 0.0; sr.color_ramp.elements[0].color = (0.75, 0.82, 0.9, 1)
sr.color_ramp.elements[1].position = 0.45; sr.color_ramp.elements[1].color = (0.18, 0.38, 0.85, 1)
nt.links.new(skyg.outputs[2], sr.inputs[0])
sbg = nt.nodes.new("ShaderNodeBackground"); sbg.inputs["Strength"].default_value = 1.2; nt.links.new(sr.outputs[0], sbg.inputs[0])
ms_ = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(lp_.outputs["Is Camera Ray"], ms_.inputs[0])
nt.links.new(bg.outputs[0], ms_.inputs[1]); nt.links.new(sbg.outputs[0], ms_.inputs[2]); nt.links.new(ms_.outputs[0], out.inputs[0])

sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.energy = 4.0; sun_d.angle = R_(1.5); sun_d.color = (1.0, 0.96, 0.9)
sun = bpy.data.objects.new("Sun", sun_d); sc.collection.objects.link(sun)
sun.rotation_euler = (R_(52), 0, R_(150))   # from front-left, over the lawn; reaches into the window

# ------------------------------------------------------------------ exterior ground
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=60, y_segments=40, size=1)
for v in bm.verts: v.co = Vector((v.co.x * 40, -16 + v.co.y * 16, 0))
lawn = mesh_obj("Lawn", bm, C_EXT, M_grass)
bpy.context.view_layer.objects.active = lawn
lawn.data.uv_layers.new(name="UVMap")
for poly in lawn.data.polygons:
    for li in poly.loop_indices:
        co = lawn.data.vertices[lawn.data.loops[li].vertex_index].co
        lawn.data.uv_layers[0].data[li].uv = (co.x / 4, co.y / 4)
road = box("Road", C_EXT, -40, 40, -31, -24.5, -0.02, 0.005, M_asph)
walk = box("Sidewalk", C_EXT, -40, 40, -23.8, -22.2, 0, 0.06, M_conc)
curb = box("Curb", C_EXT, -40, 40, -24.5, -23.8, -0.02, 0.10, M_conc)
path = box("FrontPath", C_EXT, 2.0, 3.1, -22.2, 0, 0, 0.03, M_conc)
lawn.location.z = 0.0
# grass the camera skims: several hundred instanced clumps under the bullet path
with bpy.data.libraries.load(os.path.join(A, "grass_medium_01", "grass_medium_01_1k.blend"), link=False) as (s, d):
    d.objects = [n for n in s.objects if n.endswith("LOD0")]
grass_src = [o for o in d.objects if o]
gc = bpy.data.collections.new("GrassSrc")
for o in grass_src: gc.objects.link(o); o.location = (0, 0, 0)
GRASS = []
for i in range(520):
    y = random.uniform(-22, -0.6); x = random.gauss(0, 1.4) if i < 360 else random.uniform(-9, 9)
    o = bpy.data.objects.new("Grass_%03d" % i, random.choice(grass_src).data); C_EXT.objects.link(o)
    o.location = (x, y, 0); o.rotation_euler.z = random.uniform(0, 6.28); s_ = random.uniform(0.7, 1.4); o.scale = (s_, s_, s_)
    GRASS.append(o)

_MODELS = {}
def decimate(o, ratio):
    bpy.context.view_layer.objects.active = o
    for s_ in bpy.context.selected_objects: s_.select_set(False)
    o.select_set(True)
    m = o.modifiers.new("dec", "DECIMATE"); m.ratio = ratio
    bpy.ops.object.modifier_apply(modifier="dec")
def import_model(asset, c, loc, rot=0.0, scale=1.0, skip=("LOD1", "LOD2", "LOD3", "wdg_", "hlp_", "rig_"), dec=None):
    root = bpy.data.objects.new(asset + "_root", None); c.objects.link(root)
    if asset in _MODELS:   # repeated asset: linked duplicates share the mesh data
        src = _MODELS[asset]; mp = {}
        for o in src:
            n = o.copy(); c.objects.link(n); mp[o] = n
        for o in src:
            mp[o].parent = mp[o.parent] if o.parent in mp else root
    else:
        p = os.path.join(A, asset, asset + "_1k.blend")
        with bpy.data.libraries.load(p, link=False) as (s, d):
            d.objects = [n for n in s.objects if not any(k in n for k in skip)]
        objs = [o for o in d.objects if o is not None and o.type in ("MESH", "EMPTY", "CURVE")]
        for o in objs:
            c.objects.link(o)
            if o.parent is None or o.parent not in objs: o.parent = root
        if dec:
            for o in objs:
                if o.type == "MESH" and len(o.data.vertices) > 60000: decimate(o, dec)
        _MODELS[asset] = objs
    root.location = loc; root.rotation_euler.z = rot; root.scale = (scale,) * 3
    return root

_GLB = {}
def import_glb(name, c, loc, rotz=0.0, height=None, scale=1.0):
    """CC-BY model (Objaverse GLB) normalised: bbox centred on xy, base on z=0, optional target height"""
    root = bpy.data.objects.new("GLB_" + name, None); c.objects.link(root)
    if name in _GLB:
        src, k = _GLB[name]; mp = {}
        for o in src:
            n = o.copy(); c.objects.link(n); mp[o] = n
        for o in src: mp[o].parent = mp[o.parent] if o.parent in mp else root
    else:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=os.path.join(A, "glb", name + ".glb"))
        new = [o for o in bpy.data.objects if o not in before]
        for o in new:
            for cc in list(o.users_collection): cc.objects.unlink(o)
            c.objects.link(o)
        bpy.context.view_layer.update()
        ms = [o for o in new if o.type == "MESH"]
        pts = [o.matrix_world @ Vector(b) for o in ms for b in o.bound_box]
        lo = Vector([min(p_[i] for p_ in pts) for i in range(3)]); hi = Vector([max(p_[i] for p_ in pts) for i in range(3)])
        k = (height / (hi.z - lo.z)) if height else 1.0
        tops = [o for o in new if o.parent is None]
        piv = bpy.data.objects.new("GLBpiv_" + name, None); c.objects.link(piv)
        piv.location = (-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)
        for o in tops: o.parent = piv
        piv.parent = root; new.append(piv)
        for o in new:
            if o.type in ("LIGHT", "CAMERA"): o.hide_render = True
        _GLB[name] = ([o for o in new], k)
    root.location = loc; root.rotation_euler.z = rotz; root.scale = (k * scale,) * 3
    return root

TREE_SKIP = ("LOD0", "LOD2", "LOD3", "wdg_", "hlp_", "rig_")
import_model("tree_small_02", C_EXT, (-4.5, -9.0, 0), 0.7, 1.0, skip=TREE_SKIP, dec=0.3)
import_model("tree_small_02", C_EXT, (7.5, -14.0, 0), 2.1, 1.15, skip=TREE_SKIP)
import_model("street_lamp_01", C_EXT, (-3.0, -23.2, 0.06), 0.0)
import_model("fire_hydrant", C_EXT, (5.0, -23.0, 0.06), 0.8)
import_model("covered_car", C_EXT, (-6.5, -27.2, 0), R_(90))
import_model("covered_car", C_EXT, (11.0, -27.6, 0), R_(-90))
for x in (-5.4, -4.2, -3.0, 4.3, 5.5):
    import_model("shrub_01", C_EXT, (x, -1.0, 0), random.uniform(0, 6), random.uniform(0.8, 1.1), dec=0.4)
import_model("garden_sprinkler_01", C_EXT, (-2.6, -11.0, 0.0), 0.0, 1.0)
# neighbour out for a walk on the sidewalk (MPFB, CC0)
with bpy.data.libraries.load(os.path.join(ROOT, "work", "walker.blend"), link=False) as (s_, d_):
    d_.objects = [n for n in s_.objects]
for o in d_.objects:
    if o: C_EXT.objects.link(o)
# mailbox
box("Mailbox_post", C_EXT, 3.45, 3.55, -21.6, -21.5, 0, 1.0, M_wood_light)
box("Mailbox", C_EXT, 3.35, 3.65, -21.8, -21.3, 1.0, 1.2, M_blackplastic, 0.02)

# ------------------------------------------------------------------ houses
def house(name, x0, x1, y0, y1, h, col, c=C_EXT, door_x=None, windows=()):
    m = tint(M_siding0, col, "M_siding_" + name)
    w = box(name + "_walls", c, x0, x1, y0, y1, 0, h, m)
    # gable roof
    bm = bmesh.new(); ov = 0.4; rz = h + (x1 - x0) * 0.28
    vs = [bm.verts.new(v) for v in [(x0 - ov, y0 - ov, h - 0.1), (x1 + ov, y0 - ov, h - 0.1), ((x0 + x1) / 2, y0 - ov, rz),
                                    (x0 - ov, y1 + ov, h - 0.1), (x1 + ov, y1 + ov, h - 0.1), ((x0 + x1) / 2, y1 + ov, rz)]]
    bm.faces.new((vs[0], vs[2], vs[5], vs[3])); bm.faces.new((vs[2], vs[1], vs[4], vs[5]))
    bm.faces.new((vs[0], vs[1], vs[2])); bm.faces.new((vs[3], vs[5], vs[4]))
    r = mesh_obj(name + "_roof", bm, c, M_roof)
    sol = r.modifiers.new("sol", "SOLIDIFY"); sol.thickness = 0.12
    r.data.uv_layers.new(name="UVMap")
    for poly in r.data.polygons:
        for li in poly.loop_indices:
            co = r.data.vertices[r.data.loops[li].vertex_index].co
            r.data.uv_layers[0].data[li].uv = (co.x / 2 + co.z, co.y / 2)
    for (wx, wz, ww, wh) in windows:
        box(name + "_win", c, wx - ww / 2, wx + ww / 2, y0 - 0.03, y0 + 0.01, wz - wh / 2, wz + wh / 2, P("M_win_" + name, (0.05, 0.07, 0.09), 0.05, metal=0.3))
        box(name + "_wintrim", c, wx - ww / 2 - 0.08, wx + ww / 2 + 0.08, y0 - 0.05, y0 - 0.02, wz - wh / 2 - 0.08, wz - wh / 2, M_trim)
    if door_x is not None:
        box(name + "_door", c, door_x - 0.48, door_x + 0.48, y0 - 0.04, y0 + 0.01, 0, 2.1, M_door)
    return w

# neighbour houses: real model (Suburban House, CC-BY), porch side (+X in the model) turned to face the street
import_glb("houseA", C_EXT, (-14.5, 5.5, 0.0), R_(-90), height=7.8)
import_glb("houseA", C_EXT, (14.5, 6.0, 0.0), R_(-90), height=7.8, scale=1.05)
import_glb("houseA", C_EXT, (-29.0, 7.0, 0.0), R_(-90), height=7.8, scale=0.95)
import_glb("houseA", C_EXT, (28.5, 6.5, 0.0), R_(-90), height=7.8)

# ---- our house: walls except the front, roof, front wall built in layers with the bullet hole at x 0, z 1.30
HX0, HX1, HD, HH = -6.0, 6.0, 9.0, 2.75
box("House_back", C_WALL, HX0, HX1, HD - 0.16, HD, 0, HH, M_siding)
box("House_sideL", C_WALL, HX0, HX0 + 0.16, 0, HD, 0, HH, M_siding)
box("House_sideR", C_WALL, HX1 - 0.16, HX1, 0, HD, 0, HH, M_siding)
bm = bmesh.new(); ov = 0.45; rz = HH + 2.2
vs = [bm.verts.new(v) for v in [(HX0 - ov, -ov, HH - 0.1), (HX1 + ov, -ov, HH - 0.1), (0, -ov - 0.0, rz) ,
                                (HX0 - ov, HD + ov, HH - 0.1), (HX1 + ov, HD + ov, HH - 0.1), (0, HD + ov, rz)]]
# hip-less gable running along X: ridge parallel to X so the front shows a long eave
vs2 = [bm.verts.new(v) for v in [(HX0 - ov, HD / 2, rz), (HX1 + ov, HD / 2, rz)]]
bm.faces.new((vs[0], vs[1], vs2[1], vs2[0])); bm.faces.new((vs2[0], vs2[1], vs[4], vs[3]))
for v in (vs[2], vs[5]): bm.verts.remove(v)
r = mesh_obj("House_roof", bm, C_WALL, M_roof); r.modifiers.new("sol", "SOLIDIFY").thickness = 0.14
r.data.uv_layers.new(name="UVMap")
for poly in r.data.polygons:
    for li in poly.loop_indices:
        co = r.data.vertices[r.data.loops[li].vertex_index].co
        r.data.uv_layers[0].data[li].uv = (co.x / 2, co.y / 2 + co.z)
# gable end triangles closing the roof sides
for x in (HX0, HX1):
    bm = bmesh.new(); a = bm.verts.new((x, 0, HH)); b = bm.verts.new((x, HD, HH)); c_ = bm.verts.new((x, HD / 2, rz - 0.05))
    bm.faces.new((a, b, c_)); g = mesh_obj("House_gable", bm, C_WALL, M_siding); g.modifiers.new("sol", "SOLIDIFY").thickness = 0.16
box("House_ceiling", C_WALL, HX0, HX1, 0, HD, HH, HH + 0.12, M_white)
box("House_fascia", C_WALL, HX0 - 0.45, HX1 + 0.45, -0.47, -0.40, HH - 0.25, HH - 0.05, M_trim)
box("House_foundation", C_WALL, HX0, HX1, -0.06, HD, -0.3, 0.19, M_conc)

WIN = (-2.3, -1.1, 0.95, 2.05)   # front window x0, x1, z0, z1 (bedroom)
DOOR = (2.0, 3.0)
def front_layer(name, y0, y1, mat, hole_r, jag, seed, window=True):
    """front wall layer split around window + door, with the bullet hole"""
    parts = []
    xw0, xw1, zw0, zw1 = WIN
    for (x0, x1, z0, z1) in [(HX0, xw0, 0.25, HH), (xw0, xw1, 0.25, zw0), (xw0, xw1, zw1, HH),
                             (xw1, DOOR[0], 0.25, HH), (DOOR[0], DOOR[1], 2.15, HH), (DOOR[1], HX1, 0.25, HH)]:
        parts.append(box(name, C_WALL, x0, x1, y0, y1, z0, z1, mat))
    hp = parts[3]
    cut_hole(hp, hole_r, y0=y0 - 0.05, y1=y1 + 0.05, jag=jag, seed=seed)
    return parts
front_layer("Wall_siding", -0.025, 0.0, M_siding, 0.075, 0.6, 1)
front_layer("Wall_osb", 0.0, 0.012, M_osb, 0.08, 0.5, 2)
front_layer("Wall_drywall", 0.145, 0.16, M_drywall, 0.11, 0.7, 3)
# intact plugs over the holes until the bullet arrives (hidden on impact in 03)
box("Plug_siding", C_WALL, -0.12, 0.12, -0.0245, -0.0005, 1.35, 1.59, M_siding)
box("Plug_osb", C_WALL, -0.12, 0.12, 0.0, 0.012, 1.35, 1.59, M_osb)
box("Plug_drywall", C_WALL, -0.14, 0.14, 0.145, 0.16, 1.33, 1.61, M_drywall)
# studs (bullet passes between the x = -0.2 and +0.2 studs), plates, insulation batts with a torn tunnel
for i, x in enumerate([HX0 + 0.1] + [-3.4 + 0.4 * k for k in range(int((DOOR[0] - 0.2 + 3.4) / 0.4) + 1)]):
    if WIN[0] - 0.05 < x < WIN[1] + 0.05: continue
    box("Wall_stud", C_WALL, x - 0.02, x + 0.02, 0.012, 0.10, 0.25, HH, M_stud)
box("Wall_plate", C_WALL, HX0, HX1, 0.012, 0.10, 0.25, 0.29, M_stud)
ins = box("Wall_insulation", C_WALL, -0.18, 0.18, 0.012, 0.10, 0.29, HH - 0.05, M_insul)
dp = ins.modifiers.new("fluff", "DISPLACE"); tex = bpy.data.textures.new("fluff", "CLOUDS"); tex.noise_scale = 0.05; dp.texture = tex; dp.strength = 0.01
cut_hole(ins, 0.17, y0=0.0, y1=0.12, jag=0.3, seed=4)
ins.modifiers.new("sub", "SUBSURF").levels = 1
# window frame + glass, door, trims, gutter
box("Win_glass", C_WALL, WIN[0], WIN[1], 0.06, 0.07, WIN[2], WIN[3], M_glass)
for (a0, a1, b0, b1) in [(WIN[0] - 0.08, WIN[0], WIN[2] - 0.08, WIN[3] + 0.08), (WIN[1], WIN[1] + 0.08, WIN[2] - 0.08, WIN[3] + 0.08),
                         (WIN[0], WIN[1], WIN[2] - 0.08, WIN[2]), (WIN[0], WIN[1], WIN[3], WIN[3] + 0.08), (WIN[0], WIN[1], (WIN[2] + WIN[3]) / 2 - 0.02, (WIN[2] + WIN[3]) / 2 + 0.02)]:
    box("Win_frame", C_WALL, a0, a1, -0.06, 0.16, b0, b1, M_trim)
box("Front_door", C_WALL, DOOR[0], DOOR[1], 0.0, 0.05, 0.25, 2.15, M_door, 0.01)
# more front windows (glass + mullions + trim + shutters), porch light and flower beds so the facade reads as a real house
M_shutter = P("M_shutter", (0.08, 0.12, 0.18), 0.45, coat=0.3)
M_winglass = P("M_win_glass_ext", (0.03, 0.04, 0.05), 0.05, metal=0.4)
for (cx, w_) in ((-4.6, 1.3), (4.4, 1.3), (0.0, 0.0)):
    if w_ == 0.0: continue
    x0, x1, z0, z1 = cx - w_ / 2, cx + w_ / 2, 0.95, 2.05
    box("FWin_glass", C_WALL, x0, x1, -0.04, -0.03, z0, z1, M_winglass)
    for (a0, a1, b0, b1) in [(x0 - 0.08, x0, z0 - 0.1, z1 + 0.08), (x1, x1 + 0.08, z0 - 0.1, z1 + 0.08), (x0, x1, z0 - 0.1, z0), (x0, x1, z1, z1 + 0.08),
                             (cx - 0.02, cx + 0.02, z0, z1), (x0, x1, (z0 + z1) / 2 - 0.02, (z0 + z1) / 2 + 0.02)]:
        box("FWin_trim", C_WALL, a0, a1, -0.07, -0.025, b0, b1, M_trim)
    box("FWin_sill", C_WALL, x0 - 0.12, x1 + 0.12, -0.12, -0.02, z0 - 0.14, z0 - 0.1, M_trim)
    for sx_ in (x0 - 0.5, x1 + 0.1):
        sh = box("FWin_shutter", C_WALL, sx_, sx_ + 0.4, -0.06, -0.03, z0 - 0.05, z1 + 0.05, M_shutter)
for sx_ in (WIN[0] - 0.5, WIN[1] + 0.1):
    box("FWin_shutter", C_WALL, sx_, sx_ + 0.4, -0.06, -0.03, WIN[2] - 0.05, WIN[3] + 0.05, M_shutter)
box("Porch_light", C_WALL, DOOR[1] + 0.15, DOOR[1] + 0.27, -0.1, -0.02, 2.0, 2.2, P("M_porchlamp", (0.1, 0.1, 0.1), 0.3, emit=(1.0, 0.8, 0.5), ew=2))
box("Bed_soil", C_WALL, HX0 + 0.3, DOOR[0] - 0.4, -1.0, -0.15, 0, 0.12, P("M_mulch", (0.12, 0.07, 0.04), 0.95))
box("Door_step", C_WALL, DOOR[0] - 0.3, DOOR[1] + 0.3, -0.6, 0, 0, 0.18, M_conc)
box("Gutter", C_WALL, HX0 - 0.45, HX1 + 0.45, -0.58, -0.47, HH - 0.22, HH - 0.12, M_white)
for x in (HX0 + 0.2, -4.0, 4.0, HX1 - 0.2):
    box("Siding_corner", C_WALL, x - 0.05, x + 0.05, -0.05, 0.0, 0.25, HH, M_trim)

# ------------------------------------------------------------------ bedroom (x -2.6..2.6, y 0.16..4.6)
RX0, RX1, RY1 = -2.6, 2.6, 4.6
box("Room_floor", C_ROOM, RX0, RX1, 0.16, RY1, 0.20, 0.25, M_floor)
box("Room_wallL", C_ROOM, RX0 - 0.12, RX0, 0.16, RY1, 0.25, HH, M_wall_room)
box("Room_wallR", C_ROOM, RX1, RX1 + 0.12, 0.16, RY1, 0.25, HH, M_wall_room)
box("Room_wallBack", C_ROOM, RX0, RX1, RY1, RY1 + 0.12, 0.25, HH, M_wall_room)
box("Room_skirting", C_ROOM, RX0, RX1, RY1 - 0.015, RY1, 0.25, 0.33, M_white)
box("Rug", C_ROOM, -1.0, 1.1, 2.1, 4.0, 0.25, 0.262, M_carpet)
FLOOR_Z = 0.25
# LED strip around the ceiling
for (a0, a1, b0, b1) in [(RX0, RX1, RY1 - 0.03, RY1), (RX0, RX0 + 0.03, 0.16, RY1), (RX1 - 0.03, RX1, 0.16, RY1)]:
    box("LED_strip", C_ROOM, a0, a1, b0, b1, HH - 0.06, HH - 0.04, M_led)
# desk + monitor on the left wall
box("Desk_top", C_ROOM, RX0, RX0 + 0.75, 0.9, 2.5, 0.98, 1.02, M_desk, 0.005)
for (y_) in (0.95, 2.45):
    box("Desk_leg", C_ROOM, RX0 + 0.05, RX0 + 0.7, y_ - 0.03, y_ + 0.03, FLOOR_Z, 0.98, M_metal)
box("Monitor_stand", C_ROOM, RX0 + 0.18, RX0 + 0.3, 1.62, 1.78, 1.02, 1.24, M_metal)
mon = box("Monitor", C_ROOM, RX0 + 0.22, RX0 + 0.28, 1.25, 2.15, 1.18, 1.68, M_blackplastic, 0.004)
# abstract screen glow (no text, no UI): animated gradient
ms = bpy.data.materials.new("M_screen"); ms.use_nodes = True; n_ = ms.node_tree.nodes; l_ = ms.node_tree.links; n_.clear()
tc = n_.new("ShaderNodeTexCoord"); wv = n_.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 1.6; wv.inputs["Distortion"].default_value = 6
ramp = n_.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (0.05, 0.25, 0.9, 1); ramp.color_ramp.elements[1].color = (0.9, 0.2, 0.6, 1)
em = n_.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 6; o_ = n_.new("ShaderNodeOutputMaterial")
l_.new(tc.outputs["Object"], wv.inputs["Vector"]); l_.new(wv.outputs["Color"], ramp.inputs[0]); l_.new(ramp.outputs[0], em.inputs[0]); l_.new(em.outputs[0], o_.inputs[0])
wv.inputs["Phase Offset"].default_value = 0.0
wv.inputs["Phase Offset"].keyframe_insert("default_value", frame=1)
wv.inputs["Phase Offset"].default_value = 12.0
wv.inputs["Phase Offset"].keyframe_insert("default_value", frame=1500)
box("Monitor_screen", C_ROOM, RX0 + 0.281, RX0 + 0.283, 1.27, 2.13, 1.20, 1.66, ms)
box("Keyboard", C_ROOM, RX0 + 0.42, RX0 + 0.58, 1.45, 1.95, 1.02, 1.04, M_blackplastic, 0.004)
box("Keyboard_glow", C_ROOM, RX0 + 0.43, RX0 + 0.57, 1.46, 1.94, 1.04, 1.042, M_led)
pc = box("PC_tower", C_ROOM, RX0 + 0.05, RX0 + 0.55, 2.55, 2.75, FLOOR_Z, 0.75, M_blackplastic, 0.01)
box("PC_glow", C_ROOM, RX0 + 0.1, RX0 + 0.5, 2.549, 2.551, 0.30, 0.70, P("M_pc_glow", (0, 0, 0), 0.5, emit=(0.1, 0.9, 0.8), ew=5))
import_model("gaming_console", C_ROOM, (RX0 + 0.35, 1.05, 1.02), R_(90))
import_model("gamepad", C_ROOM, (RX0 + 0.5, 2.25, 1.02), R_(30))
import_model("potted_plant_01", C_ROOM, (RX1 - 0.3, 0.45, FLOOR_Z), 0.3)
fan = import_model("ceiling_fan", C_ROOM, (0.0, 2.3, HH), 0.0)
# chair
box("Chair_seat", C_ROOM, RX0 + 0.75, RX0 + 1.25, 1.45, 1.95, 0.70, 0.78, P("M_chair", (0.6, 0.05, 0.08), 0.5), 0.02)
box("Chair_back", C_ROOM, RX0 + 1.2, RX0 + 1.27, 1.45, 1.95, 0.78, 1.45, bpy.data.materials["M_chair"], 0.02)
box("Chair_post", C_ROOM, RX0 + 0.97, RX0 + 1.03, 1.67, 1.73, FLOOR_Z, 0.70, M_metal)
# bed on the right
box("Bed_frame", C_ROOM, RX1 - 1.5, RX1, 2.6, RY1, FLOOR_Z, 0.55, M_wood_light, 0.01)
box("Bed_mattress", C_ROOM, RX1 - 1.45, RX1 - 0.05, 2.65, RY1 - 0.05, 0.55, 0.75, M_bed, 0.04)
box("Bed_pillow", C_ROOM, RX1 - 1.3, RX1 - 0.2, RY1 - 0.5, RY1 - 0.12, 0.75, 0.87, M_pillow, 0.04)
# shelf with generic game cases (no titles) on the right wall
box("Shelf", C_ROOM, RX1 - 0.25, RX1, 0.6, 2.2, 1.55, 1.58, M_wood_light)
box("Shelf2", C_ROOM, RX1 - 0.25, RX1, 0.6, 2.2, 1.95, 1.98, M_wood_light)
case_cols = [(0.6, 0.1, 0.1), (0.1, 0.2, 0.6), (0.1, 0.45, 0.2), (0.7, 0.5, 0.1), (0.15, 0.15, 0.15), (0.45, 0.1, 0.5)]
yy = 0.65
for i in range(22):
    w = 0.014 + random.random() * 0.01
    zt = 1.58 + (0.0 if i < 13 else 0.40)
    if i == 13: yy = 0.65
    box("GameCase", C_ROOM, RX1 - 0.2, RX1 - 0.04, yy, yy + w, zt, zt + 0.19, P("M_case%d" % i, random.choice(case_cols), 0.35))
    yy += w + 0.002
# posters: procedural abstract art images (no text)
def poster_img(name, seed):
    import numpy as np
    rng = np.random.default_rng(seed); H, W = 384, 256
    yy_, xx_ = np.mgrid[0:H, 0:W] / 256.0
    c1, c2, c3 = rng.random(3), rng.random(3), rng.random(3)
    t = 0.5 + 0.5 * np.sin(xx_ * rng.uniform(3, 9) + np.sin(yy_ * rng.uniform(2, 7)) * 2)
    img = (c1[None, None] * t[..., None] + c2[None, None] * (1 - t[..., None]))
    for k in range(5):
        cx, cy, r = rng.random() * 1.0, rng.random() * 1.5, rng.uniform(0.08, 0.3)
        m = ((xx_ - cx) ** 2 + (yy_ - cy) ** 2) < r ** 2
        img[m] = img[m] * 0.4 + rng.random(3) * 0.6
    im = bpy.data.images.new(name, W, H); px = np.ones((H, W, 4)); px[..., :3] = img ** 2.2; im.pixels = px.ravel(); im.pack()
    return im
def poster(name, img, cx, cy, cz, w, h, rot):
    m = bpy.data.materials.new("M_" + name); m.use_nodes = True; nt_ = m.node_tree
    t_ = nt_.nodes.new("ShaderNodeTexImage"); t_.image = img
    b_ = nt_.nodes["Principled BSDF"]; b_.inputs["Roughness"].default_value = 0.35
    nt_.links.new(t_.outputs[0], b_.inputs["Base Color"])
    bpy.ops.mesh.primitive_plane_add(size=1); o = bpy.context.active_object; o.name = name; link(o, C_ROOM)
    o.scale = (w, h, 1); o.rotation_euler = (R_(90), 0, rot); o.location = (cx, cy, cz); o.data.materials.append(m)
    return o
poster("Poster1", poster_img("poster1", 3), 0.0, RY1 - 0.01, 1.75, 0.6, 0.9, 0)
poster("Poster2", poster_img("poster2", 8), -1.4, RY1 - 0.01, 1.8, 0.5, 0.75, 0)
poster("Poster3", poster_img("poster3", 11), RX0 + 0.01, 3.4, 1.75, 0.6, 0.9, R_(90))
poster("Poster4", poster_img("poster4", 21), RX1 - 0.01, 3.2, 1.65, 0.45, 0.65, R_(-90))
# curtains at the window (inside)
for i, x in enumerate((WIN[0] - 0.15, WIN[1] - 0.05)):
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=16, y_segments=12, size=0.5)
    for v in bm.verts:
        u = v.co.x + 0.5; vv = v.co.y + 0.5
        v.co = Vector((x + u * 0.25, 0.22 + 0.02 * math.sin(u * 30), WIN[2] - 0.2 + vv * (WIN[3] - WIN[2] + 0.45)))
    cu = mesh_obj("Curtain_%d" % i, bm, C_ROOM, P("M_curtain", (0.5, 0.48, 0.42), 0.9))
    cu.data.polygons.foreach_set("use_smooth", [True] * len(cu.data.polygons))
# real furniture replaces the blocked-out pieces: gaming desk + chair + PC (CC-BY) and a wooden bed (CC-BY)
for o in [o for o in C_ROOM.objects if o.name.startswith(("Desk_", "Monitor", "Keyboard", "PC_", "Chair_", "Bed_"))]:
    bpy.data.objects.remove(o, do_unlink=True)
for o in [o for o in C_ROOM.objects if o.name.startswith(("gaming_console", "gamepad"))]:
    bpy.data.objects.remove(o, do_unlink=True)
desk = import_glb("desk", C_ROOM, (RX0 + 0.95, 1.65, FLOOR_Z), R_(90), height=1.35)
bed = import_glb("bed", C_ROOM, (RX1 - 0.55, 3.55, FLOOR_Z), R_(90), height=0.62)
# the monitor shows the abstract animated glow (no UI, no text)
for o in bpy.data.objects:
    if o.type == "MESH" and o.name.lower().startswith(("monitor", "screen")):
        if "wallpaperScreen" in o.name: o.data.materials[0] = bpy.data.materials["M_screen"]
# room lights: monitor glow, lamp, a soft fill, bounce from the window
def area(name, loc, rot, size, energy, col):
    l = bpy.data.lights.new(name, "AREA"); l.size = size; l.energy = energy; l.color = col
    o = bpy.data.objects.new(name, l); C_ROOM.objects.link(o); o.location = loc; o.rotation_euler = rot; return o
area("L_monitor", (RX0 + 0.35, 1.7, 1.43), (0, R_(-90), 0), 0.6, 60, (0.4, 0.5, 1.0))
area("L_fill", (1.5, 1.2, HH - 0.1), (R_(20), R_(25), 0), 1.5, 260, (1.0, 0.92, 0.85))
area("L_window_bounce", (-1.7, 0.6, 1.5), (R_(-90), 0, 0), 1.0, 150, (0.9, 0.95, 1.0))
area("L_rim_purple", (1.8, 4.2, 2.3), (R_(-60), 0, R_(150)), 1.0, 80, (0.6, 0.3, 1.0))

# ------------------------------------------------------------------ the collector's box (local frame: centre at origin, front = -Y)
BOX_C = Vector((0.0, 2.97, 1.42))
broot = bpy.data.objects.new("BoxRoot", None); C_BOX.objects.link(broot); broot.location = BOX_C
broot.empty_display_size = 0.2
CUT = bpy.data.node_groups.new("CutAway", "ShaderNodeTree")   # alpha = 0 where local x > cut (cross-section reveal)
CUT.interface.new_socket("Shader", in_out="INPUT", socket_type="NodeSocketShader")
CUT.interface.new_socket("Shader", in_out="OUTPUT", socket_type="NodeSocketShader")
gi = CUT.nodes.new("NodeGroupInput"); go = CUT.nodes.new("NodeGroupOutput")
tcn = CUT.nodes.new("ShaderNodeTexCoord"); tcn.object = broot
sep = CUT.nodes.new("ShaderNodeSeparateXYZ"); cutv = CUT.nodes.new("ShaderNodeValue"); cutv.name = "cut"; cutv.outputs[0].default_value = 1.0
cmp_ = CUT.nodes.new("ShaderNodeMath"); cmp_.operation = "SUBTRACT"; cmp_.inputs[0].default_value = 1.0
trn = CUT.nodes.new("ShaderNodeBsdfTransparent"); mixs = CUT.nodes.new("ShaderNodeMixShader")
CUT.links.new(cutv.outputs[0], cmp_.inputs[1])   # cut = visibility of the +X halves (1 shown, 0 cut away)
CUT.links.new(cmp_.outputs[0], mixs.inputs[0]); CUT.links.new(gi.outputs[0], mixs.inputs[1]); CUT.links.new(trn.outputs[0], mixs.inputs[2])
CUT.links.new(mixs.outputs[0], go.inputs[0])

def cutmat(m):
    return m
def cutmat_real(m):
    nt_ = m.node_tree; o_ = [n for n in nt_.nodes if n.type == "OUTPUT_MATERIAL"][0]
    src = o_.inputs["Surface"].links[0].from_socket
    g = nt_.nodes.new("ShaderNodeGroup"); g.node_tree = CUT
    nt_.links.new(src, g.inputs[0]); nt_.links.new(g.outputs[0], o_.inputs["Surface"])
    return m

# front cover: dark embossed abstract relief + animated crack mask around the impact point
mc = bpy.data.materials.new("M_box_cover"); mc.use_nodes = True; nt_ = mc.node_tree; N = nt_.nodes; L = nt_.links
bsdf = N["Principled BSDF"]; bsdf.inputs["Roughness"].default_value = 0.5; bsdf.inputs["Coat Weight"].default_value = 0.25; bsdf.inputs["Coat Roughness"].default_value = 0.25
tco = N.new("ShaderNodeTexCoord"); tco.object = broot
vor = N.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 22; vor.feature = "DISTANCE_TO_EDGE"
wave = N.new("ShaderNodeTexWave"); wave.inputs["Scale"].default_value = 3; wave.wave_type = "RINGS"
mxf = N.new("ShaderNodeMath"); mxf.operation = "MINIMUM"
emb = N.new("ShaderNodeMapRange"); emb.inputs[1].default_value = 0.0; emb.inputs[2].default_value = 0.012
L.new(tco.outputs["Object"], vor.inputs["Vector"]); L.new(tco.outputs["Object"], wave.inputs["Vector"])
# abstract embossed emblem (rings + diamond + chevrons), no text: generated image mapped on local x/z
def emblem_img():
    import numpy as np
    W_, H_ = 600, 760; yy_, xx_ = np.mgrid[0:H_, 0:W_].astype(float)
    x = (xx_ / W_ - 0.5) * 0.30; z = (0.5 - yy_ / H_) * 0.38 - 0.03
    r = np.hypot(x, z); E = np.zeros_like(r)
    E = np.maximum(E, (np.abs(r - 0.075) < 0.004) * 1.0); E = np.maximum(E, (np.abs(r - 0.062) < 0.0015) * 1.0)
    d = np.abs(x) + np.abs(z); E = np.maximum(E, ((d < 0.04) & (d > 0.03)) * 1.0); E = np.maximum(E, (d < 0.018) * 1.0)
    for k in range(3):
        zz = z + 0.11 + 0.018 * k; E = np.maximum(E, ((np.abs(zz + 0.6 * np.abs(x)) < 0.0035) & (np.abs(x) < 0.07)) * 1.0)
    fr = (np.abs(np.abs(x) - 0.135) < 0.002) & (np.abs(z + 0.03) < 0.175) | (np.abs(np.abs(z + 0.03) - 0.175) < 0.002) & (np.abs(x) < 0.135)
    E = np.maximum(E, fr * 1.0)
    im = bpy.data.images.new("box_emblem", W_, H_); px = np.ones((H_, W_, 4)); px[..., 0] = px[..., 1] = px[..., 2] = E[::-1]
    im.pixels = px.ravel(); im.pack(); im.colorspace_settings.name = "Non-Color"; return im
eimg = N.new("ShaderNodeTexImage"); eimg.image = emblem_img(); eimg.extension = "CLIP"
esep = N.new("ShaderNodeSeparateXYZ"); L.new(tco.outputs["Object"], esep.inputs[0])
eu = N.new("ShaderNodeMath"); eu.operation = "MULTIPLY_ADD"; eu.inputs[1].default_value = 1 / 0.30; eu.inputs[2].default_value = 0.5; L.new(esep.outputs[0], eu.inputs[0])
ev = N.new("ShaderNodeMath"); ev.operation = "MULTIPLY_ADD"; ev.inputs[1].default_value = 1 / 0.38; ev.inputs[2].default_value = 0.5; L.new(esep.outputs[2], ev.inputs[0])
ecb = N.new("ShaderNodeCombineXYZ"); L.new(eu.outputs[0], ecb.inputs[0]); L.new(ev.outputs[0], ecb.inputs[1]); L.new(ecb.outputs[0], eimg.inputs[0])
emb.inputs[1].default_value = 0.0; emb.inputs[2].default_value = 1.0; emb.inputs[3].default_value = 1.0; emb.inputs[4].default_value = 0.6
L.new(eimg.outputs[0], emb.inputs[0])
colr = N.new("ShaderNodeMix"); colr.data_type = "RGBA"
colr.inputs[6].default_value = (0.20, 0.17, 0.12, 1)   # emblem: dark bronze
colr.inputs[7].default_value = (0.018, 0.018, 0.02, 1)   # matte black case
L.new(emb.outputs[0], colr.inputs[0])
mtl = N.new("ShaderNodeMath"); mtl.operation = "SUBTRACT"; mtl.inputs[0].default_value = 1.0; L.new(emb.outputs[0], mtl.inputs[1])
# crack mask: thin voronoi edges, only inside radius R of the impact (local x 0, z +0.05)
vc = N.new("ShaderNodeTexVoronoi"); vc.feature = "DISTANCE_TO_EDGE"; vc.inputs["Scale"].default_value = 30; vc.inputs["Randomness"].default_value = 1.0
nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 40
vadd = N.new("ShaderNodeVectorMath"); vadd.operation = "MULTIPLY_ADD"; vadd.inputs[1].default_value = (0.01, 0.01, 0.01)
L.new(nz.outputs["Color"], vadd.inputs[0]); L.new(tco.outputs["Object"], vadd.inputs[2]); L.new(vadd.outputs[0], vc.inputs["Vector"])
radial = N.new("ShaderNodeTexGradient"); radial.gradient_type = "SPHERICAL"
cen = N.new("ShaderNodeVectorMath"); cen.operation = "SUBTRACT"; cen.inputs[1].default_value = (0.0, -0.07, 0.05)
sca = N.new("ShaderNodeVectorMath"); sca.operation = "DIVIDE"
crR = N.new("ShaderNodeValue"); crR.name = "crack_radius"; crR.outputs[0].default_value = 0.001
cmb = N.new("ShaderNodeCombineXYZ"); L.new(crR.outputs[0], cmb.inputs[0]); L.new(crR.outputs[0], cmb.inputs[1]); L.new(crR.outputs[0], cmb.inputs[2])
L.new(tco.outputs["Object"], cen.inputs[0]); L.new(cen.outputs[0], sca.inputs[0]); L.new(cmb.outputs[0], sca.inputs[1]); L.new(sca.outputs[0], radial.inputs[0])
radial_ = N.new("ShaderNodeMath"); radial_.operation = "GREATER_THAN"; radial_.inputs[1].default_value = 0.0; L.new(radial.outputs[1], radial_.inputs[0])
ln = N.new("ShaderNodeMath"); ln.operation = "LESS_THAN"; ln.inputs[1].default_value = 0.007; L.new(vc.outputs["Distance"], ln.inputs[0])
# radial spokes too
crk = N.new("ShaderNodeMath"); crk.operation = "MULTIPLY"; L.new(ln.outputs[0], crk.inputs[0]); L.new(radial_.outputs[0], crk.inputs[1])
colc = N.new("ShaderNodeMix"); colc.data_type = "RGBA"; colc.inputs[7].default_value = (0.75, 0.75, 0.72, 1)   # stressed white plastic in the cracks
hl = N.new("ShaderNodeVectorMath"); hl.operation = "LENGTH"; L.new(cen.outputs[0], hl.inputs[0])
hlt = N.new("ShaderNodeMapRange"); hlt.inputs[1].default_value = 0.0065; hlt.inputs[2].default_value = 0.0085; hlt.inputs[3].default_value = 1.0; hlt.inputs[4].default_value = 0.0
L.new(hl.outputs["Value"], hlt.inputs[0])
hon = N.new("ShaderNodeValue"); hon.name = "hole_on"; hon.outputs[0].default_value = 0.0
hm = N.new("ShaderNodeMath"); hm.operation = "MULTIPLY"; L.new(hlt.outputs[0], hm.inputs[0]); L.new(hon.outputs[0], hm.inputs[1])
colh = N.new("ShaderNodeMix"); colh.data_type = "RGBA"; colh.inputs[7].default_value = (0.01, 0.008, 0.006, 1)
L.new(hm.outputs[0], colh.inputs[0])
L.new(crk.outputs[0], colc.inputs[0]); L.new(colr.outputs[2], colc.inputs[6]); L.new(colc.outputs[2], colh.inputs[6]); L.new(colh.outputs[2], bsdf.inputs["Base Color"])
bmp = N.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.8; bmp.inputs["Distance"].default_value = 0.0015; bmp.invert = True
hsum = N.new("ShaderNodeMath"); hsum.operation = "SUBTRACT"; L.new(emb.outputs[0], hsum.inputs[0]); L.new(crk.outputs[0], hsum.inputs[1])
L.new(hsum.outputs[0], bmp.inputs["Height"]); L.new(bmp.outputs[0], bsdf.inputs["Normal"])
mm_ = N.new("ShaderNodeMath"); mm_.operation = "MULTIPLY"; mm_.inputs[1].default_value = 1.4; L.new(mtl.outputs[0], mm_.inputs[0]); L.new(mm_.outputs[0], bsdf.inputs["Metallic"])
cutmat(mc)

M_case = cutmat(P("M_box_shell", (0.035, 0.035, 0.045), 0.35, coat=0.4))
M_tray = cutmat(P("M_disc_tray", (0.16, 0.17, 0.2), 0.3, coat=0.5))
M_card = cutmat(P("M_cardboard", (0.62, 0.47, 0.30), 0.85))
M_page = cutmat(P("M_manual_page", (0.72, 0.70, 0.64), 0.6))
M_page2 = cutmat(P("M_manual_page_print", (0.55, 0.70, 0.85), 0.5))
M_bookc = cutmat(P("M_artbook", (0.25, 0.05, 0.04), 0.5))
M_bookp = cutmat(P("M_artbook_pages", (0.70, 0.68, 0.62), 0.7))
# disc: iridescent data side via thin-film
md = bpy.data.materials.new("M_disc"); md.use_nodes = True; bd = md.node_tree.nodes["Principled BSDF"]
bd.inputs["Base Color"].default_value = (0.85, 0.85, 0.88, 1); bd.inputs["Metallic"].default_value = 1.0; bd.inputs["Roughness"].default_value = 0.08
bd.inputs["Thin Film IOR"].default_value = 1.5
dtc = md.node_tree.nodes.new("ShaderNodeTexCoord"); dwv = md.node_tree.nodes.new("ShaderNodeTexWave"); dwv.wave_type = "RINGS"
dwv.inputs["Scale"].default_value = 18; dwv.inputs["Distortion"].default_value = 0.5
dmr = md.node_tree.nodes.new("ShaderNodeMapRange"); dmr.inputs[3].default_value = 250; dmr.inputs[4].default_value = 900
md.node_tree.links.new(dtc.outputs["Object"], dwv.inputs["Vector"]); md.node_tree.links.new(dwv.outputs["Fac"], dmr.inputs[0])
md.node_tree.links.new(dmr.outputs[0], bd.inputs["Thin Film Thickness"])
cutmat(md)
md_sh = md.copy(); md_sh.name = "M_disc_shard"   # shards are not cut away, they glitter in the cross-section

W2, H2, D2 = 0.15, 0.19, 0.07
def lbox(name, y0, y1, mat, inset=0.006, c=C_BOX, bevel=0.0):
    o = box(name, c, -W2 + inset, W2 - inset, y0, y1, -H2 + inset, H2 - inset, mat, bevel); o.parent = broot; return o
# shell: front cover, back cover, 4 walls
cover = lbox("Box_cover", -0.070, -0.062, mc, inset=0.0, bevel=0.002)
cover.data.uv_layers.new(name="UVMap")
lbox("Box_back", 0.062, 0.070, M_case, inset=0.0, bevel=0.002)
for nm, (x0, x1, z0, z1) in {"Box_wallL": (-W2, -W2 + 0.006, -H2, H2), "Box_wallR": (W2 - 0.006, W2, -H2, H2),
                             "Box_wallT": (-W2, W2, H2 - 0.006, H2), "Box_wallB": (-W2, W2, -H2, -H2 + 0.006)}.items():
    o = box(nm, C_BOX, x0, x1, -0.062, 0.062, z0, z1, M_case); o.parent = broot
lbox("Box_tray", -0.048, -0.046, M_tray)
for nm, (x0, x1, z0, z1) in {"Tray_frameL": (-W2 + 0.006, -W2 + 0.016, -H2 + 0.006, H2 - 0.006), "Tray_frameR": (W2 - 0.016, W2 - 0.006, -H2 + 0.006, H2 - 0.006),
                             "Tray_frameT": (-W2 + 0.006, W2 - 0.006, H2 - 0.016, H2 - 0.006), "Tray_frameB": (-W2 + 0.006, W2 - 0.006, -H2 + 0.006, -H2 + 0.016)}.items():
    o = box(nm, C_BOX, x0, x1, -0.062, -0.048, z0, z1, M_tray); o.parent = broot
M_clear = cutmat(P("M_jewel_clear", (0.95, 0.97, 1.0), 0.04, trans=1.0, ior=1.49))
# discs (2 in the tray, 1 in a sleeve) as thin cylinders lying in the XZ plane, centres offset so the bullet hits off-centre
DISCS = []
def disc(name, y, cx, cz, mat=md):
    bm = bmesh.new()
    ro = bmesh.ops.create_circle(bm, cap_ends=False, segments=64, radius=0.06)["verts"]
    ri = bmesh.ops.create_circle(bm, cap_ends=False, segments=64, radius=0.0075)["verts"]
    bmesh.ops.bridge_loops(bm, edges=bm.edges[:])
    ex = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    bmesh.ops.translate(bm, verts=[e for e in ex["geom"] if isinstance(e, bmesh.types.BMVert)], vec=(0, 0, 0.0012))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(R_(90), 3, 'X'))
    o = mesh_obj(name, bm, C_BOX, mat); o.parent = broot; o.location = (cx, y, cz); DISCS.append(o); return o
disc("Disc_1", -0.0565, 0.022, 0.03); disc("Disc_2", -0.0505, -0.015, 0.068)
lbox("Box_divider", -0.046, -0.041, M_card)
PAGES = []
for i in range(18):
    y0 = -0.040 + i * 0.00105
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=24, y_segments=30, size=1)
    for v in bm.verts: v.co = Vector((v.co.x * (W2 - 0.012), y0, v.co.y * (H2 - 0.012)))
    o = mesh_obj("Page_%02d" % i, bm, C_BOX, M_page if i % 3 else M_page2); o.parent = broot
    o.modifiers.new("sol", "SOLIDIFY").thickness = 0.0006
    # bow-wave shape key: gaussian bulge toward +Y around the bullet line (x 0, z +0.05)
    o.shape_key_add(name="Basis"); k = o.shape_key_add(name="bulge")
    for j, v in enumerate(o.data.vertices):
        d2 = (v.co.x) ** 2 + (v.co.z - 0.05) ** 2
        k.data[j].co.y = v.co.y + 0.006 * math.exp(-d2 / (2 * 0.025 ** 2))
    PAGES.append(o)
lbox("Box_sleeve", -0.0205, -0.0195, M_clear)
disc("Disc_3", -0.0165, 0.01, 0.055)
lbox("Box_sleeve2", -0.0135, -0.0125, M_tray)
lbox("Box_insert", -0.012, 0.004, M_card)
lbox("Artbook_front", 0.004, 0.008, M_bookc); lbox("Artbook_pages", 0.008, 0.056, M_bookp, inset=0.009); lbox("Artbook_back", 0.056, 0.060, M_bookc)
for o in C_BOX.objects:
    if o.type == "MESH" and o.parent is None: o.parent = broot

# split every box part at local x = CUTX: the -X half stays, the +X half fades away for the cross-section
CUTX = -0.011
XP = {}
def xp_mat(m):
    if m.name not in XP:
        c = m.copy(); c.name = m.name + "_xp"; cutmat_real(c); XP[m.name] = c
    return XP[m.name]
for o in [o for o in C_BOX.objects if o.type == "MESH" and not o.name.startswith("Shard_")]:
    of = o.copy(); of.data = o.data.copy(); of.name = o.name + "_full"; C_BOX.objects.link(of); of["full_of"] = o.name
    px = CUTX - o.location.x
    me2 = o.data.copy(); o2 = o.copy(); o2.data = me2; o2.name = o.name + "_xp"; C_BOX.objects.link(o2)
    if o2.data.shape_keys:
        pass
    for ob_, keep_neg in ((o, True), (o2, False)):
        has_sk = ob_.data.shape_keys is not None
        bm = bmesh.new(); bm.from_mesh(ob_.data)
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        r = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(px, 0, 0), plane_no=(1, 0, 0), clear_outer=keep_neg, clear_inner=not keep_neg)
        if not ob_.name.startswith("Page_"):
            edges = [e for e in r["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
            if edges: bmesh.ops.holes_fill(bm, edges=edges, sides=0)
        bm.to_mesh(ob_.data); bm.free(); ob_.data.update()
    for i, m in enumerate(o2.data.materials): o2.data.materials[i] = xp_mat(m)
    o2.parent = broot; o2.matrix_parent_inverse = o.matrix_parent_inverse
    o2["xp_of"] = o.name

# shards: each disc pre-split into ring sectors (pieces), hidden until the impact
SH = []
def shatter(d, n_ring=3, n_sec=14):
    pieces = []
    for ri in range(n_ring):
        r0 = 0.0075 + (0.06 - 0.0075) * ri / n_ring; r1 = 0.0075 + (0.06 - 0.0075) * (ri + 1) / n_ring
        off = random.random()
        for si in range(n_sec):
            a0 = (si + off) / n_sec * 2 * math.pi; a1 = (si + 1 + off) / n_sec * 2 * math.pi
            j0 = random.uniform(-0.12, 0.12); j1 = random.uniform(-0.12, 0.12)
            bm = bmesh.new()
            pts = [(r0, a0 + j0 * 0.3), (r1, a0 + j0), (r1, a1 + j1), (r0, a1 + j1 * 0.3)]
            vs_ = [bm.verts.new((r * math.cos(a), 0, r * math.sin(a))) for r, a in pts]
            f = bm.faces.new(vs_)
            ex = bmesh.ops.extrude_face_region(bm, geom=[f]);
            for v in [e for e in ex["geom"] if isinstance(e, bmesh.types.BMVert)]: v.co.y += 0.0012
            cen_ = sum((v.co for v in bm.verts), Vector()) / len(bm.verts)
            for v in bm.verts: v.co -= cen_
            o = mesh_obj("Shard_%s_%d_%d" % (d.name, ri, si), bm, C_BOX, md_sh); o.parent = broot
            o.location = d.location + cen_; o.hide_render = True; o.hide_viewport = True
            o["home"] = list(o.location); o["disc"] = d.name
            pieces.append(o)
    return pieces
SHARDS = {d.name: shatter(d) for d in DISCS}

# ------------------------------------------------------------------ bullet (plain projectile shape only)
prof = [(0.0, 0.0), (0.0015, 0.0012), (0.0032, 0.0035), (0.0045, 0.0065), (0.0053, 0.010), (0.0055, 0.014), (0.0055, 0.026), (0.0050, 0.028), (0.0, 0.028)]
bm = bmesh.new(); seg = 32; rings = []
for r, y in prof:
    rings.append([bm.verts.new((r * math.cos(2 * math.pi * k / seg), -y, r * math.sin(2 * math.pi * k / seg))) for k in range(seg)])
for a, b in zip(rings, rings[1:]):
    for k in range(seg):
        bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
for v in bm.verts: v.co.y += 0.0   # nose at local y=0, body trails to -0.028 (bullet travels +Y)
for v in bm.verts: v.co.y = -v.co.y - 0.0
bullet = mesh_obj("Bullet", bm, C_FX, P("M_bullet_copper", (0.80, 0.42, 0.25), 0.22, metal=1.0))
for v in bullet.data.vertices: v.co.y = -v.co.y   # nose at +y=0? keep nose at y=0 pointing +Y
bullet.data.polygons.foreach_set("use_smooth", [True] * len(bullet.data.polygons))
# make nose point to +Y: vertices with y in [-0.028, 0]; nose at y=0
ys = [v.co.y for v in bullet.data.vertices]
if max(ys) > 0.001:
    for v in bullet.data.vertices: v.co.y -= max(ys)
bullet.shape_key_add(name="Basis"); mush = bullet.shape_key_add(name="mushroom")
for j, v in enumerate(bullet.data.vertices):
    t = max(0.0, 1 + v.co.y / 0.012)  # 1 at nose, 0 at 12 mm back
    r = math.hypot(v.co.x, v.co.z)
    if r > 1e-6:
        k = 1 + 0.9 * t
        mush.data[j].co.x = v.co.x * k; mush.data[j].co.z = v.co.z * k
    mush.data[j].co.y = v.co.y * (1 - 0.55 * t) - 0.004 * t
bullet.modifiers.new("sub", "SUBSURF").levels = 1
# air-shock trail behind the bullet (outside only): stretched transparent cone
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=24, radius1=0.005, radius2=0.045, depth=1.0)
bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(R_(90), 3, 'X'))
bmesh.ops.translate(bm, verts=bm.verts, vec=(0, -0.53, 0))
mt = bpy.data.materials.new("M_trail"); mt.use_nodes = True; tn = mt.node_tree.nodes; tl = mt.node_tree.links
bsd = tn["Principled BSDF"]; bsd.inputs["Transmission Weight"].default_value = 1.0; bsd.inputs["Roughness"].default_value = 0.0; bsd.inputs["IOR"].default_value = 1.06
lw = tn.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.3
mix = tn.new("ShaderNodeMixShader"); tr = tn.new("ShaderNodeBsdfTransparent")
emt = tn.new("ShaderNodeEmission"); emt.inputs["Color"].default_value = (1.0, 0.95, 0.9, 1); emt.inputs["Strength"].default_value = 1.5
inv = tn.new("ShaderNodeMath"); inv.operation = "MULTIPLY_ADD"; inv.inputs[1].default_value = 0.35; inv.inputs[2].default_value = 0.6
tl.new(lw.outputs["Facing"], inv.inputs[0])
tl.new(inv.outputs[0], mix.inputs[0]); tl.new(emt.outputs[0], mix.inputs[1]); tl.new(tr.outputs[0], mix.inputs[2])
tl.new(mix.outputs[0], tn["Material Output"].inputs[0])
trail = mesh_obj("Bullet_trail", bm, C_FX, mt); trail.parent = bullet

# eyes: textured wet eyeball (MakeHuman CC0 brown eye texture) instead of the procedural eye that renders black here
EYE_TEX = os.path.expanduser("~/.config/blender/5.2/extensions/.user/user_default/mpfb/data/eyes/materials/brown_eye.png")
me_ = bpy.data.materials.new("M_eye"); me_.use_nodes = True; be_ = me_.node_tree.nodes["Principled BSDF"]
ti_ = me_.node_tree.nodes.new("ShaderNodeTexImage"); ti_.image = bpy.data.images.load(EYE_TEX); ti_.image.alpha_mode = "STRAIGHT"; me_.node_tree.links.new(ti_.outputs["Alpha"], be_.inputs["Alpha"])
me_.node_tree.links.new(ti_.outputs[0], be_.inputs["Base Color"]); be_.inputs["Roughness"].default_value = 0.35
me_.node_tree.links.new(ti_.outputs[0], be_.inputs["Emission Color"]); be_.inputs["Emission Strength"].default_value = 0.35   # eyes sit deep under the brow here; a touch of self-light keeps them readable
be_.inputs["Coat Weight"].default_value = 1.0; be_.inputs["Coat Roughness"].default_value = 0.02
for o in bpy.data.objects:
    if o.type == "MESH" and o.name.endswith(".high-poly"):
        for i in range(len(o.data.materials)): o.data.materials[i] = me_
print("SCENE_DONE", len(bpy.data.objects))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
