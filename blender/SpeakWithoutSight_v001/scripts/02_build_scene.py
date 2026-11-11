"""Parlour set, props, lights, explainer dome, bubble; appends the humans and the dog.
blender -b --factory-startup --python 02_build_scene.py -- <work_dir> <assets_dir> <out.blend>"""
import sys, os, glob, math
import bpy
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]
W, AS, OUT = a[0], a[1], a[2]
R_ = math.radians
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene
r = sc.render
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps, r.fps_base = 60, 1.0
sc.frame_start, sc.frame_end = 1, 1980
r.engine = 'CYCLES'; cy = sc.cycles; cy.device = 'CPU'
cy.samples = 48; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05; cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 8; cy.diffuse_bounces = 3; cy.glossy_bounces = 3; cy.transmission_bounces = 8; cy.transparent_max_bounces = 8
cy.caustics_reflective = cy.caustics_refractive = False
r.use_persistent_data = True; r.use_motion_blur = True; r.motion_blur_shutter = 0.5
sc.display_settings.display_device = 'sRGB'
vs = sc.view_settings; vs.view_transform = 'AgX'; vs.look = 'AgX - Medium High Contrast'; vs.exposure = 0.0; vs.gamma = 1.0
im = r.image_settings; im.file_format = 'PNG'; im.color_mode = 'RGB'; im.color_depth = '8'; im.compression = 15
r.filepath = "//render/SpeakWithoutSight_v001_"

def coll(name):
    c = bpy.data.collections.new(name); sc.collection.children.link(c); return c
SET, PROPS, CHAR, FX = coll("SET"), coll("PROPS"), coll("CHAR"), coll("FX")

def img(path, nc=False):
    i = bpy.data.images.load(path, check_existing=True)
    if nc: i.colorspace_settings.name = 'Non-Color'
    return i
def tex(folder, key):
    fs = [f for f in glob.glob(os.path.join(AS, folder, "textures", "*")) if key in os.path.basename(f)]
    return fs[0] if fs else None
def pbr(name, folder, scale, tint=None, val=1.0, bump=1.0, rough_mul=1.0, coord='UV'):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    p = n["Principled BSDF"]
    tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / scale,) * 3
    l.new(tc.outputs[coord], mp.inputs['Vector'])
    d = n.new('ShaderNodeTexImage'); d.image = img(tex(folder, "_diff_") or tex(folder, "_col_"))
    l.new(mp.outputs['Vector'], d.inputs['Vector'])
    hsv = n.new('ShaderNodeHueSaturation'); hsv.inputs['Value'].default_value = val
    l.new(d.outputs['Color'], hsv.inputs['Color'])
    if tint:
        mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        mx.inputs['B'].default_value = (*tint, 1); l.new(hsv.outputs['Color'], mx.inputs['A']); l.new(mx.outputs['Result'], p.inputs['Base Color'])
    else:
        l.new(hsv.outputs['Color'], p.inputs['Base Color'])
    rf = tex(folder, "_rough_")
    if rf:
        rt = n.new('ShaderNodeTexImage'); rt.image = img(rf, True); l.new(mp.outputs['Vector'], rt.inputs['Vector'])
        rm = n.new('ShaderNodeMath'); rm.operation = 'MULTIPLY'; rm.inputs[1].default_value = rough_mul; rm.use_clamp = True
        l.new(rt.outputs['Color'], rm.inputs[0]); l.new(rm.outputs[0], p.inputs['Roughness'])
    nf = tex(folder, "_nor_gl_")
    if nf:
        nt = n.new('ShaderNodeTexImage'); nt.image = img(nf, True); l.new(mp.outputs['Vector'], nt.inputs['Vector'])
        nm = n.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = bump
        l.new(nt.outputs['Color'], nm.inputs['Color']); l.new(nm.outputs['Normal'], p.inputs['Normal'])
    return m
def flat(name, rgb, rough=0.5, metal=0.0, emit=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough; p.inputs["Metallic"].default_value = metal
    if emit: p.inputs["Emission Color"].default_value = (*emit[0], 1); p.inputs["Emission Strength"].default_value = emit[1]
    return m
def box(name, size, loc, mat, c=SET, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name); import bmesh
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
    for v in me.vertices: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    o = bpy.data.objects.new(name, me); c.objects.link(o); o.location = loc; o.rotation_euler = rot
    me.materials.append(mat)
    uv = me.uv_layers.new()
    return o
def plane(name, sx, sy, loc, mat, c=SET, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-sx / 2, -sy / 2, 0), (sx / 2, -sy / 2, 0), (sx / 2, sy / 2, 0), (-sx / 2, sy / 2, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new()
    for i, lp in enumerate(me.loops):
        co = me.vertices[lp.vertex_index].co; uv.data[i].uv = (co.x + sx / 2, co.y + sy / 2)
    o = bpy.data.objects.new(name, me); c.objects.link(o); o.location = loc; o.rotation_euler = rot
    me.materials.append(mat); return o

# ------------------------------------------------------------------ room shell 6 x 5 x 3.2 (x -3..3, y -2.5..2.5)
RX, RY, RH = 3.0, 2.5, 3.2
m_floor = pbr("M_Parquet", "herringbone_parquet", 1.2, tint=(0.75, 0.6, 0.48), bump=0.6, coord='Object')
m_wall = pbr("M_WallPaper", "painted_plaster_wall", 1.5, tint=(0.55, 0.62, 0.5), bump=0.4, coord='Object')
m_wood = pbr("M_DarkWood", "dark_wood", 1.0, tint=(0.7, 0.55, 0.45), bump=0.5, coord='Object')
m_ceil = flat("M_Ceiling", (0.78, 0.74, 0.66), 0.9)
m_rug = pbr("M_Rug", "fabric_pattern_05", 1.2, tint=(0.75, 0.45, 0.35), bump=0.8)
m_curt = pbr("M_Curtain", "quatrefoil_jacquard_fabric", 0.5, tint=(0.55, 0.15, 0.12), bump=0.6)
floor = plane("Floor", 2 * RX, 2 * RY, (0, 0, 0), m_floor)
ceil = plane("Ceiling", 2 * RX, 2 * RY, (0, 0, RH), m_ceil, rot=(R_(180), 0, 0))
WIN_X, WIN_W, WIN_Z0, WIN_Z1 = 0.9, 1.25, 0.8, 2.6
DOOR_Y, DOOR_W, DOOR_H = -1.3, 1.0, 2.2
def wall_boxes(prefix, axis, pos, normal_sign, holes):
    """wall plane along axis ('x' wall spans x at y=pos; 'y' spans y at x=pos) with rectangular holes (u0,u1,z0,z1)"""
    L = 2 * RX if axis == 'x' else 2 * RY
    t = 0.12
    us = sorted(set([-L / 2, L / 2] + [h[0] for h in holes] + [h[1] for h in holes]))
    k = 0
    for u0, u1 in zip(us, us[1:]):
        zs = [(0, RH)]
        for h in holes:
            if h[0] <= u0 and u1 <= h[1]: zs = [(0, h[2]), (h[3], RH)]
        for z0, z1 in zs:
            if z1 - z0 < 1e-3: continue
            uc, zc = (u0 + u1) / 2, (z0 + z1) / 2
            loc = (uc, pos + normal_sign * t / 2, zc) if axis == 'x' else (pos + normal_sign * t / 2, uc, zc)
            size = (u1 - u0, t, z1 - z0) if axis == 'x' else (t, u1 - u0, z1 - z0)
            box("%s_%d" % (prefix, k), size, loc, m_wall); k += 1
        # wainscot (dark wood panelling) below 0.95 m on the room side
        zs2 = [(0, 0.95)]
        for h in holes:
            if h[0] <= u0 and u1 <= h[1]: zs2 = [(0, min(0.95, h[2]))] if h[2] > 0.05 else []
        for z0, z1 in zs2:
            uc = (u0 + u1) / 2
            loc = (uc, pos - normal_sign * 0.012, (z0 + z1) / 2) if axis == 'x' else (pos - normal_sign * 0.012, uc, (z0 + z1) / 2)
            size = (u1 - u0, 0.025, z1 - z0) if axis == 'x' else (0.025, u1 - u0, z1 - z0)
            box("%s_wainscot_%d" % (prefix, k), size, loc, m_wood); k += 1
wall_boxes("WallBack", 'x', RY, 1, [(WIN_X - WIN_W / 2, WIN_X + WIN_W / 2, WIN_Z0, WIN_Z1)])
wall_boxes("WallFront", 'x', -RY, -1, [])
wall_boxes("WallLeft", 'y', -RX, -1, [(DOOR_Y - DOOR_W / 2, DOOR_Y + DOOR_W / 2, 0.0, DOOR_H)])
wall_boxes("WallRight", 'y', RX, 1, [])
for o in [o for o in SET.objects if o.name.startswith("WallFront")]:
    o.visible_camera = False      # camera roams the front of the room; the wall still bounces light
# rails, skirting, crown, window frame, door
for nm, size, loc in (("DadoRail_B", (2 * RX, 0.05, 0.05), (0, RY - 0.03, 0.97)), ("DadoRail_L", (0.05, 2 * RY, 0.05), (-RX + 0.03, 0, 0.97)),
                      ("DadoRail_R", (0.05, 2 * RY, 0.05), (RX - 0.03, 0, 0.97)), ("Crown_B", (2 * RX, 0.09, 0.12), (0, RY - 0.04, RH - 0.06)),
                      ("Crown_L", (0.09, 2 * RY, 0.12), (-RX + 0.04, 0, RH - 0.06)), ("Crown_R", (0.09, 2 * RY, 0.12), (RX - 0.04, 0, RH - 0.06)),
                      ("Skirt_B", (2 * RX, 0.04, 0.16), (0, RY - 0.03, 0.08)), ("Skirt_R", (0.04, 2 * RY, 0.16), (RX - 0.03, 0, 0.08))):
    box(nm, size, loc, m_wood)
m_paint = flat("M_WindowPaint", (0.82, 0.8, 0.74), 0.45)
wx0, wx1 = WIN_X - WIN_W / 2, WIN_X + WIN_W / 2
for nm, size, loc in (("Win_FrameL", (0.08, 0.2, WIN_Z1 - WIN_Z0), (wx0 + 0.04, RY + 0.06, (WIN_Z0 + WIN_Z1) / 2)),
                      ("Win_FrameR", (0.08, 0.2, WIN_Z1 - WIN_Z0), (wx1 - 0.04, RY + 0.06, (WIN_Z0 + WIN_Z1) / 2)),
                      ("Win_FrameT", (WIN_W, 0.2, 0.08), (WIN_X, RY + 0.06, WIN_Z1 - 0.04)),
                      ("Win_Sill", (WIN_W + 0.2, 0.3, 0.05), (WIN_X, RY - 0.02, WIN_Z0 - 0.02)),
                      ("Win_MeetRail", (WIN_W, 0.06, 0.05), (WIN_X, RY + 0.06, (WIN_Z0 + WIN_Z1) / 2)),
                      ("Win_MullionV", (0.03, 0.04, WIN_Z1 - WIN_Z0), (WIN_X, RY + 0.07, (WIN_Z0 + WIN_Z1) / 2)),
                      ("Win_MullionH1", (WIN_W, 0.04, 0.03), (WIN_X, RY + 0.07, WIN_Z0 + (WIN_Z1 - WIN_Z0) * 0.25)),
                      ("Win_MullionH2", (WIN_W, 0.04, 0.03), (WIN_X, RY + 0.07, WIN_Z0 + (WIN_Z1 - WIN_Z0) * 0.75))):
    box(nm, size, loc, m_paint)
m_glass = bpy.data.materials.new("M_WinGlass"); m_glass.use_nodes = True
gn = m_glass.node_tree.nodes; gl = m_glass.node_tree.links
tr = gn.new('ShaderNodeBsdfTransparent'); gls = gn.new('ShaderNodeBsdfGlossy'); gls.inputs['Roughness'].default_value = 0.05
mxg = gn.new('ShaderNodeMixShader'); mxg.inputs[0].default_value = 0.08
gl.new(tr.outputs[0], mxg.inputs[1]); gl.new(gls.outputs[0], mxg.inputs[2]); gl.new(mxg.outputs[0], gn["Material Output"].inputs['Surface'])
gn.remove(gn["Principled BSDF"])
glass = plane("Win_Glass", WIN_W, WIN_Z1 - WIN_Z0, (WIN_X, RY + 0.08, (WIN_Z0 + WIN_Z1) / 2), m_glass, rot=(R_(90), 0, 0))
# curtains: wavy panels either side of the window
import bmesh
def curtain(name, x0):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    NX, NZ = 24, 10; Wc, Hc = 0.45, 2.75
    vs_ = [[bm.verts.new((x0 + Wc * i / NX - Wc / 2, RY - 0.08 - 0.035 * math.sin(i / NX * 6 * math.pi), 2.95 - Hc * j / NZ)) for i in range(NX + 1)] for j in range(NZ + 1)]
    for j in range(NZ):
        for i in range(NX):
            bm.faces.new((vs_[j][i], vs_[j][i + 1], vs_[j + 1][i + 1], vs_[j + 1][i]))
    bm.to_mesh(me); uvl = me.uv_layers.new()
    for i, lp in enumerate(me.loops):
        co = me.vertices[lp.vertex_index].co; uvl.data[i].uv = (co.x * 2, co.z * 2)
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); SET.objects.link(o); me.materials.append(m_curt)
    o.modifiers.new("Solid", 'SOLIDIFY').thickness = 0.01
    return o
curtain("Curtain_L", wx0 - 0.22); curtain("Curtain_R", wx1 + 0.22)
box("CurtainRod", (WIN_W + 1.2, 0.03, 0.03), (WIN_X, RY - 0.1, 2.97), flat("M_Brass", (0.7, 0.5, 0.25), 0.3, 1.0))
# door (left wall), slightly ajar
box("DoorFrame_T", (0.12, DOOR_W + 0.16, 0.1), (-RX + 0.03, DOOR_Y, DOOR_H + 0.05), m_wood)
for s in (-1, 1): box("DoorFrame_%d" % s, (0.12, 0.08, DOOR_H), (-RX + 0.03, DOOR_Y + s * (DOOR_W / 2 + 0.04), DOOR_H / 2), m_wood)
door = box("Door", (0.05, DOOR_W, DOOR_H), (0, DOOR_W / 2, DOOR_H / 2), m_wood)
door_piv = bpy.data.objects.new("DoorPivot", None); SET.objects.link(door_piv); door_piv.location = (-RX + 0.02, DOOR_Y - DOOR_W / 2, 0)
door.parent = door_piv; door_piv.rotation_euler = (0, 0, R_(-12))
box("Hall_Back", (0.1, 2.0, 2.6), (-RX - 1.2, DOOR_Y, 1.3), m_wall)
plane("Hall_Floor", 1.2, 2.0, (-RX - 0.6, DOOR_Y, 0.0), m_floor)
rug = plane("Rug", 3.0, 2.2, (0.0, 0.1, 0.004), m_rug)

# ------------------------------------------------------------------ outside: HDRI world, lawn, tree (seasons keyed in 03)
wd = bpy.data.worlds.new("World"); sc.world = wd; wd.use_nodes = True
wn, wl = wd.node_tree.nodes, wd.node_tree.links
env = wn.new('ShaderNodeTexEnvironment'); env.image = img(glob.glob(os.path.join(AS, "hdri", "*.hdr"))[0])
mpw = wn.new('ShaderNodeMapping'); tcw = wn.new('ShaderNodeTexCoord'); mpw.inputs['Rotation'].default_value = (0, 0, R_(200))
wl.new(tcw.outputs['Generated'], mpw.inputs['Vector']); wl.new(mpw.outputs['Vector'], env.inputs['Vector'])
wl.new(env.outputs['Color'], wn["Background"].inputs['Color']); wn["Background"].inputs['Strength'].default_value = 1.0
m_lawn = flat("M_Lawn", (0.12, 0.2, 0.06), 0.9)
_n = m_lawn.node_tree.nodes; _p = _n["Principled BSDF"]
_nz = _n.new("ShaderNodeTexNoise"); _nz.inputs["Scale"].default_value = 3.0; _nz.inputs["Detail"].default_value = 10
_cm = _n.new("ShaderNodeMix"); _cm.data_type = 'RGBA'; _cm.inputs["A"].default_value = (0.06, 0.12, 0.03, 1); _cm.inputs["B"].default_value = (0.2, 0.28, 0.08, 1)
m_lawn.node_tree.links.new(_nz.outputs["Fac"], _cm.inputs["Factor"]); m_lawn.node_tree.links.new(_cm.outputs["Result"], _p.inputs["Base Color"])
_vz = _n.new("ShaderNodeTexNoise"); _vz.inputs["Scale"].default_value = 400; _bp = _n.new("ShaderNodeBump"); _bp.inputs["Strength"].default_value = 0.6
m_lawn.node_tree.links.new(_vz.outputs["Fac"], _bp.inputs["Height"]); m_lawn.node_tree.links.new(_bp.outputs["Normal"], _p.inputs["Normal"])
lawn = plane("Lawn", 40, 30, (0, RY + 15.2, -0.3), m_lawn)
box("GardenWall", (14, 0.4, 1.4), (0, RY + 9.0, 0.4), pbr("M_GardenStone", "painted_plaster_wall", 0.8, tint=(0.5, 0.47, 0.42), bump=1.5, coord='Object'))
with bpy.data.libraries.load(os.path.join(AS, "island_tree_01", "island_tree_01_1k.blend"), link=False) as (s_, d_):
    d_.objects = [n for n in s_.objects if "LOD0" in n or "geometry_nodes" in n]
for o in d_.objects:
    if o is None: continue
    PROPS.objects.link(o)
    if "geometry_nodes" not in o.name: o.hide_render = True; o.hide_viewport = True
tree = bpy.data.objects["island_tree_01_geometry_nodes"]; tree.name = "Tree_Outside"
tree.location = (WIN_X - 1.0, RY + 5.0, -0.3); tree.scale = (1.3,) * 3
# a second tree for depth
tree2 = tree.copy(); PROPS.objects.link(tree2); tree2.name = "Tree_Outside2"; tree2.location = (WIN_X + 4.0, RY + 11, -0.3); tree2.rotation_euler.z = R_(70)
leaf_mats = sorted({m.name for o in d_.objects if o and "leaves" in o.name for m in o.data.materials})
sc["leaf_mats"] = leaf_mats
# snow cap on the garden wall + snow ground (shown in the time-lapse winter)
m_snow = flat("M_Snow", (0.9, 0.92, 0.95), 0.6)
snow = plane("SnowGround", 40, 30, (0, RY + 15.2, -0.29), m_snow); snow.hide_render = True
box("SnowWallCap", (14, 0.44, 0.08), (0, RY + 9.0, 1.14), m_snow).hide_render = True

# ------------------------------------------------------------------ props (Poly Haven CC0)
def append_ph(folder, loc, rot_z=0.0, scale=1.0, name=None, only=None):
    p = glob.glob(os.path.join(AS, folder, "*_1k.blend"))[0]
    with bpy.data.libraries.load(p, link=False) as (s_, d_):
        d_.objects = [n for n in s_.objects if (only is None or any(k in n for k in only)) and not n.startswith("Sphere_stash")]
    objs = [o for o in d_.objects if o]
    piv = bpy.data.objects.new(name or folder, None); PROPS.objects.link(piv)
    for o in objs:
        PROPS.objects.link(o)
        if o.parent is None: o.parent = piv
        if o.name.startswith("wdg_"): o.hide_render = True; o.hide_viewport = True
    piv.location = loc; piv.rotation_euler = (0, 0, R_(rot_z)); piv.scale = (scale,) * 3
    return piv, objs
CHAIR_XY = Vector((0.25, 0.55))
with bpy.data.libraries.load(os.path.join(W, "models.blend"), link=False) as (s_, d_):
    d_.objects = [n for n in s_.objects if n.startswith("Model_")]
MODELS = {o.name: o for o in d_.objects if o}
fst = MODELS["Model_Footstool"]; PROPS.objects.link(fst); fst.name = "Footstool"
fst.scale = (0.78, 0.66, 0.6); fst.location = (CHAIR_XY.x, CHAIR_XY.y - 0.5, 0.0)
STOOL = (CHAIR_XY.x, CHAIR_XY.y - 0.5, 0.35 * 0.6)
for nm in ("Model_HandSkeleton", "Model_Larynx", "Model_OpenBook"):
    o = MODELS[nm]; FX.objects.link(o) if nm != "Model_OpenBook" else PROPS.objects.link(o); o.hide_render = True; o.location = (0, 0, -5)
sc["stool"] = STOOL
append_ph("ArmChair_01", (CHAIR_XY.x, CHAIR_XY.y, 0), 0, name="ArmChair")
append_ph("Sofa_01", (-2.35, 0.5, 0), 90, name="Sofa")
append_ph("vintage_grandfather_clock_01", (-2.5, RY - 0.25, 0), 0, name="GrandfatherClock")
append_ph("vintage_cabinet_01", (RX - 0.35, 0.3, 0), -90, scale=0.85, name="Cabinet")
append_ph("round_wooden_table_01", (1.55, 1.55, 0), 0, scale=0.72, name="RoundTable")
TABLE_TOP = 1.01 * 0.72
append_ph("vintage_oil_lamp", (1.45, 1.6, TABLE_TOP), 0, name="OilLamp")
append_ph("tea_set_01", (1.75, 1.35, TABLE_TOP), 30, name="TeaSet")
append_ph("mantel_clock_01", (RX - 0.35, -0.1, 2.24 * 0.85), -90, name="MantelClock")
append_ph("book_encyclopedia_set_01", (RX - 0.35, 0.65, 2.24 * 0.85), -90, scale=0.9, name="Books")
append_ph("wooden_candlestick", (RX - 0.35, 0.95, 2.24 * 0.85), 0, name="Candlestick")
append_ph("potted_plant_01", (RX - 0.45, RY - 0.45, 0), 0, scale=1.1, name="PlantCorner")
append_ph("hanging_picture_frame_01", (-1.0, RY - 0.02, 1.85), 0, name="Picture_Back")
append_ph("hanging_picture_frame_01", (-RX + 0.02, 0.6, 1.8), -90, scale=0.8, name="Picture_Left")
append_ph("hanging_picture_frame_01", (RX - 0.02, -1.4, 1.75), 90, scale=0.7, name="Picture_Right")
append_ph("WoodenChair_01", (-1.2, 1.9, 0), 160, name="SideChair")

# ------------------------------------------------------------------ humans + dog
with bpy.data.libraries.load(os.path.join(W, "humans.blend"), link=False) as (s_, d_):
    d_.objects = list(s_.objects)
for o in d_.objects:
    if o: CHAR.objects.link(o)
for n in ("Girl", "Teacher", "Mother", "Father"):
    bpy.data.objects[n].location = (0, 0, 0)
with bpy.data.libraries.load(os.path.join(W, "dog.blend"), link=False) as (s_, d_):
    d_.objects = [n for n in s_.objects if n.startswith("Dog")]
for o in d_.objects:
    if o: CHAR.objects.link(o)

# ------------------------------------------------------------------ lights
def light(name, kind, energy, loc, rot=(0, 0, 0), color=(1, 1, 1), size=1.0):
    L = bpy.data.lights.new(name, kind); L.energy = energy; L.color = color
    if kind == 'AREA': L.size = size; L.shape = 'RECTANGLE'
    if kind in ('POINT', 'SPOT'): L.shadow_soft_size = size
    o = bpy.data.objects.new(name, L); sc.collection.objects.link(o); o.location = loc; o.rotation_euler = rot
    return o
light("L_Sun", 'SUN', 3.5, (0, 8, 6), (R_(-55), 0, R_(170)), (1.0, 0.92, 0.8), 1.0).data.angle = R_(2)
win = light("L_Window", 'AREA', 260, (WIN_X, RY - 0.05, (WIN_Z0 + WIN_Z1) / 2), (R_(-90), 0, 0), (0.85, 0.92, 1.0))
win.data.size, win.data.size_y = WIN_W, WIN_Z1 - WIN_Z0
light("L_Lamp", 'POINT', 25, (1.45, 1.6, TABLE_TOP + 0.3), color=(1.0, 0.62, 0.3), size=0.04)
light("L_Fill", 'AREA', 90, (0.0, -2.2, 2.6), (R_(55), 0, 0), (1.0, 0.9, 0.8), 2.5)
light("L_Ceil", 'AREA', 40, (0, 0, RH - 0.05), (0, 0, 0), (1.0, 0.85, 0.7), 2.0)
# explainer studio lights (off until beat 5)
light("L_StudioKey", 'AREA', 0.0, (0.6, -1.2, 2.0), (R_(50), 0, R_(20)), (1, 1, 1), 1.2)
light("L_StudioRim", 'AREA', 0.0, (-0.8, 1.4, 1.8), (R_(-60), 0, R_(200)), (0.7, 0.9, 1.0), 1.0)

# ------------------------------------------------------------------ explainer dome (cyan -> white studio gradient) and the dark bubble
def sphere(name, radius, loc, mat, segs=48):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=segs // 2, radius=radius); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); FX.objects.link(o); o.location = loc; me.materials.append(mat); return o
dm = bpy.data.materials.new("M_ExplainerDome"); dm.use_nodes = True
n, l = dm.node_tree.nodes, dm.node_tree.links; n.remove(n["Principled BSDF"])
tcd = n.new('ShaderNodeTexCoord'); sep = n.new('ShaderNodeSeparateXYZ'); l.new(tcd.outputs['Generated'], sep.inputs[0])
ramp = n.new('ShaderNodeValToRGB'); l.new(sep.outputs['Z'], ramp.inputs[0])
ramp.color_ramp.elements[0].position = 0.25; ramp.color_ramp.elements[0].color = (0.25, 0.72, 0.85, 1)
ramp.color_ramp.elements[1].position = 0.85; ramp.color_ramp.elements[1].color = (0.95, 0.98, 1.0, 1)
em = n.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.0; l.new(ramp.outputs['Color'], em.inputs['Color'])
trd = n.new('ShaderNodeBsdfTransparent'); mxd = n.new('ShaderNodeMixShader'); mxd.name = "DomeMix"; mxd.inputs[0].default_value = 0.0
l.new(trd.outputs[0], mxd.inputs[1]); l.new(em.outputs[0], mxd.inputs[2]); l.new(mxd.outputs[0], n["Material Output"].inputs['Surface'])
dome = sphere("ExplainerDome", 3.0, (0, 0.2, 0.9), dm, 64)
dome.visible_shadow = False
bmat = bpy.data.materials.new("M_Bubble"); bmat.use_nodes = True
n, l = bmat.node_tree.nodes, bmat.node_tree.links; n.remove(n["Principled BSDF"])
lw = n.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35
cr = n.new('ShaderNodeValToRGB'); l.new(lw.outputs['Facing'], cr.inputs[0])
cr.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1); cr.color_ramp.elements[1].position = 0.8; cr.color_ramp.elements[1].color = (0.05, 0.08, 0.12, 1)
emb = n.new('ShaderNodeEmission'); emb.inputs['Strength'].default_value = 1.0; l.new(cr.outputs['Color'], emb.inputs['Color'])
trb = n.new('ShaderNodeBsdfTransparent'); mxb = n.new('ShaderNodeMixShader'); mxb.name = "BubbleMix"; mxb.inputs[0].default_value = 0.0
l.new(trb.outputs[0], mxb.inputs[1]); l.new(emb.outputs[0], mxb.inputs[2]); l.new(mxb.outputs[0], n["Material Output"].inputs['Surface'])
bub = sphere("DarkBubble", 1.35, (CHAIR_XY.x, CHAIR_XY.y - 0.25, 0.9), bmat, 48)
bub.visible_shadow = False
sc["chair_xy"] = tuple(CHAIR_XY); sc["table_top"] = TABLE_TOP
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SCENE_OK", OUT)
