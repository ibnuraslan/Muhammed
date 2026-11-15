"""WeepingStatue sets + props + render settings.
  Courtyard at the origin: concrete wall (face at y=0, camera side -Y), concrete cross on it, white marble corpus, plinth, paving, trees.
  Bathroom at x=BX: tiled room, toilet, PVC drain pipe with a leaking joint, floor drain, damp streak.
blender -b chars.blend --python 02_sets.py -- <assets_dir> <out.blend>"""
import sys, os, math, glob, random
import bpy, bmesh
from mathutils import Vector, Matrix

A, OUT = sys.argv[sys.argv.index("--") + 1:][:2]
sc = bpy.context.scene
V = Vector; R_ = math.radians
random.seed(3)
BX = 60.0
sc["BX"] = BX

# ------------------------------------------------------------------ render
sc.render.fps, sc.render.fps_base = 60, 1.0
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.engine = 'CYCLES'
c = sc.cycles
c.device = 'CPU'; c.samples = 48; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.05
c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'
c.max_bounces = 8; c.diffuse_bounces = 3; c.glossy_bounces = 3; c.transmission_bounces = 8
c.caustics_reflective = c.caustics_refractive = False
sc.render.use_motion_blur = False
sc.render.use_persistent_data = True
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: pass
im = sc.render.image_settings; im.file_format = 'PNG'; im.color_mode = 'RGB'; im.color_depth = '8'
sc.render.filepath = "//render/WeepingStatue_"

def coll(name):
    c_ = bpy.data.collections.new(name); sc.collection.children.link(c_); return c_
C1, C2, PR, FX = coll("S1_Courtyard"), coll("S2_Bathroom"), coll("Props"), coll("FX")
def link(o, cl):
    for c_ in o.users_collection: c_.objects.unlink(o)
    cl.objects.link(o); return o

# ------------------------------------------------------------------ materials
def img(path, nc=False):
    i = bpy.data.images.load(path, check_existing=True)
    if nc: i.colorspace_settings.name = 'Non-Color'
    return i
def tex_files(asset):
    d = os.path.join(A, "ph", asset, "textures")
    def f(k):
        g = [x for x in sorted(glob.glob(os.path.join(d, "%s_%s_1k.*" % (asset, k)))) if not x.endswith(".exr")]; return g[0] if g else None
    return f("diff"), f("rough"), f("nor_gl")
def pbr(name, asset, scale, sat=1.0, val=1.0, bump=0.35, rough_min=0.35, tint=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    p = n["Principled BSDF"]
    dif, rou, nor = tex_files(asset)
    tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / scale,) * 3
    l.new(tc.outputs['Object'], mp.inputs['Vector'])
    d = n.new('ShaderNodeTexImage'); d.image = img(dif); d.projection = 'BOX'; d.projection_blend = 0.3
    hsv = n.new('ShaderNodeHueSaturation'); hsv.name = "HSV"; hsv.inputs['Saturation'].default_value = sat; hsv.inputs['Value'].default_value = val
    l.new(mp.outputs['Vector'], d.inputs['Vector']); l.new(d.outputs['Color'], hsv.inputs['Color'])
    out = hsv.outputs['Color']
    if tint:
        mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        mx.inputs['B'].default_value = (*tint, 1); l.new(out, mx.inputs['A']); out = mx.outputs['Result']
    l.new(out, p.inputs['Base Color'])
    if rou:
        r = n.new('ShaderNodeTexImage'); r.image = img(rou, True); r.projection = 'BOX'; r.projection_blend = 0.3
        rm = n.new('ShaderNodeMapRange'); rm.inputs['To Min'].default_value = rough_min; rm.inputs['To Max'].default_value = 1.0
        l.new(mp.outputs['Vector'], r.inputs['Vector']); l.new(r.outputs['Color'], rm.inputs['Value']); l.new(rm.outputs['Result'], p.inputs['Roughness'])
    if nor:
        nm = n.new('ShaderNodeTexImage'); nm.image = img(nor, True); nm.projection = 'BOX'; nm.projection_blend = 0.3
        nmap = n.new('ShaderNodeNormalMap'); nmap.inputs['Strength'].default_value = bump
        l.new(mp.outputs['Vector'], nm.inputs['Vector']); l.new(nm.outputs['Color'], nmap.inputs['Color']); l.new(nmap.outputs['Normal'], p.inputs['Normal'])
    return m
def flat(name, rgb, rough=0.5, metal=0.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*rgb, 1); p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    p.inputs['Coat Weight'].default_value = coat
    return m
def water_mat(name="M_Water"):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (0.6, 0.82, 1.0, 1); p.inputs['Roughness'].default_value = 0.02; p.inputs['Coat Weight'].default_value = 1.0
    p.inputs['Transmission Weight'].default_value = 1.0; p.inputs['IOR'].default_value = 1.33
    return m

def box(name, x0, x1, y0, y1, z0, z1, mat, cl, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object; o.name = name
    o.scale = (x1 - x0, y1 - y0, z1 - z0); o.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = 2; b.limit_method = 'ANGLE'
    o.data.materials.append(mat); link(o, cl); return o
def plane(name, cx, cy, cz, sx, sy, mat, cl, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1)
    o = bpy.context.active_object; o.name = name; o.scale = (sx, sy, 1); o.location = (cx, cy, cz); o.rotation_euler = rot
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat); link(o, cl); return o
def glb(path, cl, name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new: link(o, cl)
    meshes = [o for o in new if o.type == 'MESH']
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o.type != 'MESH': bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(meshes) > 1: bpy.ops.object.join()
    o = bpy.context.active_object; o.name = name
    return o
def fit(o, height=None, scale=None, base=(0, 0, 0), anchor="bottom"):
    pts = [V(c) for c in o.bound_box]
    mn = V([min(p[i] for p in pts) for i in range(3)]); mx = V([max(p[i] for p in pts) for i in range(3)])
    s = scale if scale else height / (mx.z - mn.z)
    me = o.data
    cx, cy = (mn.x + mx.x) / 2, (mn.y + mx.y) / 2
    me.transform(Matrix.Scale(s, 4) @ Matrix.Translation(V((-cx, -cy, -mn.z))))
    me.update(); o.location = base; bpy.context.view_layer.update()
    return s

# ================================================================== S1 courtyard
M_WALL = pbr("M_CourtWall", "concrete_wall_008", 2.2, sat=0.6, val=1.25, tint=(1.0, 0.98, 0.94))
M_CROSS = pbr("M_CrossConcrete", "concrete_wall_008", 1.2, sat=0.3, val=1.55)
M_PAVE = pbr("M_Paving", "patterned_paving", 2.0, sat=1.05, val=1.1)
WALL = box("S1_Wall", -9, 9, 0.0, 0.4, 0, 4.6, M_WALL, C1)
CAP = box("S1_WallCap", -9.05, 9.05, -0.06, 0.46, 4.6, 4.75, M_CROSS, C1, bevel=0.02)
GROUND = plane("S1_Paving", 0, -8, 0, 40, 30, M_PAVE, C1)
BEHIND = plane("S1_GroundBehind", 0, 12, -0.01, 40, 24, pbr("M_Grass", "patterned_paving", 3.0, sat=0.5, val=0.9, tint=(0.55, 0.75, 0.4)), C1)
# cross: vertical beam + crossbar + plinth, mounted ON the wall face (y<0)
CRX = 0.0
BEAM = box("S1_CrossBeam", -0.26, 0.26, -0.30, 0.0, 0.32, 4.15, M_CROSS, C1, bevel=0.015)
BAR = box("S1_CrossBar", -1.45, 1.45, -0.285, 0.0, 2.82, 3.30, M_CROSS, C1, bevel=0.015)
PLINTH = box("S1_Plinth", -0.75, 0.75, -0.75, 0.0, 0.0, 0.32, M_CROSS, C1, bevel=0.02)
sc["CROSS_FRONT_Y"] = -0.30
# corpus (CC0 scan): keep the figure only, white marble look, feet at z=1.45
corpus_src = os.path.join(A, "models", "christ_wood.glb")
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=corpus_src)
new = [o for o in bpy.data.objects if o not in before]
keep = [o for o in new if o.type == 'MESH' and o.name in ("Object_3", "Object_4")]
for o in new:
    if o not in keep: bpy.data.objects.remove(o, do_unlink=True)
for o in keep:
    mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
bpy.ops.object.select_all(action='DESELECT')
for o in keep: o.select_set(True)
bpy.context.view_layer.objects.active = keep[0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.join()
CORPUS = bpy.context.active_object; CORPUS.name = "S1_Statue"; link(CORPUS, C1)
dm_ = CORPUS.modifiers.new("dec", 'DECIMATE'); dm_.ratio = 0.4; bpy.ops.object.modifier_apply(modifier="dec")
s = fit(CORPUS, height=1.62)
pts = [V(c) for c in CORPUS.bound_box]
ymax = max(p.y for p in pts); ymin = min(p.y for p in pts)
CORPUS.location = (0.0, -0.30 - ymax - 0.005, 1.42); bpy.context.view_layer.update()
M_MARBLE = bpy.data.materials.new("M_StatueMarble"); M_MARBLE.use_nodes = True
mn_ = M_MARBLE.node_tree.nodes; ml_ = M_MARBLE.node_tree.links; P = mn_["Principled BSDF"]
P.inputs['Base Color'].default_value = (0.86, 0.85, 0.82, 1); P.inputs['Roughness'].default_value = 0.38
P.inputs['Subsurface Weight'].default_value = 0.15; P.inputs['Subsurface Radius'].default_value = (0.02, 0.02, 0.02)
P.inputs['Coat Weight'].default_value = 0.1
nz = mn_.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 18; nz.inputs['Detail'].default_value = 4
ramp = mn_.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = (0.78, 0.77, 0.75, 1); ramp.color_ramp.elements[1].color = (0.93, 0.92, 0.9, 1)
ml_.new(nz.outputs['Fac'], ramp.inputs['Fac']); ml_.new(ramp.outputs['Color'], P.inputs['Base Color'])
CORPUS.data.materials.clear(); CORPUS.data.materials.append(M_MARBLE)
CORPUS.modifiers.new("ws", 'WEIGHTED_NORMAL') if False else None
# store feet position (lowest toes) for the drips
me = CORPUS.data; mw = CORPUS.matrix_world
vz = sorted((mw @ v.co for v in me.vertices), key=lambda p: p.z)
low = vz[:400]
toe = min(low, key=lambda p: p.y)          # front-most of the lowest verts
sc["TOE"] = tuple(toe); sc["FEET_Z"] = vz[0].z
print("STATUE scale", s, "feet z", vz[0].z, "toe", tuple(round(t, 3) for t in toe), "dims", tuple(round(d, 2) for d in CORPUS.dimensions))
# wet streak on the beam below the feet + wet patch on the plinth (dark, glossy)
M_WET = bpy.data.materials.new("M_WetStreak"); M_WET.use_nodes = True; M_WET.blend_method = 'BLEND'
wn, wl = M_WET.node_tree.nodes, M_WET.node_tree.links; wn.clear()
wo = wn.new('ShaderNodeOutputMaterial'); wp = wn.new('ShaderNodeBsdfPrincipled'); wt = wn.new('ShaderNodeBsdfTransparent'); wm = wn.new('ShaderNodeMixShader')
wp.inputs['Base Color'].default_value = (0.32, 0.31, 0.29, 1); wp.inputs['Roughness'].default_value = 0.12
tcw = wn.new('ShaderNodeTexCoord'); gr = wn.new('ShaderNodeTexGradient'); gr.gradient_type = 'QUADRATIC_SPHERE'
mpw = wn.new('ShaderNodeMapping'); mpw.inputs['Scale'].default_value = (2.2, 0.55, 1); wl.new(tcw.outputs['Generated'], mpw.inputs['Vector'])
sub = wn.new('ShaderNodeVectorMath'); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = (1.1, 0.0, 0.5)
wl.new(mpw.outputs['Vector'], sub.inputs[0]); wl.new(sub.outputs['Vector'], gr.inputs['Vector'])
nz2 = wn.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = 9
mul = wn.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; wl.new(gr.outputs['Fac'], mul.inputs[0]); wl.new(nz2.outputs['Fac'], mul.inputs[1])
cr = wn.new('ShaderNodeMapRange'); cr.inputs['From Min'].default_value = 0.08; cr.inputs['From Max'].default_value = 0.3
wl.new(mul.outputs[0], cr.inputs['Value'])
wl.new(cr.outputs['Result'], wm.inputs['Fac']); wl.new(wt.outputs[0], wm.inputs[1]); wl.new(wp.outputs[0], wm.inputs[2]); wl.new(wm.outputs[0], wo.inputs['Surface'])
STREAK = plane("S1_WetStreak", 0.0, -0.302, 0.95, 0.34, 1.0, M_WET, C1, rot=(R_(90), 0, 0))
POOL = plane("S1_WetPool", 0.0, -0.36, 0.322, 0.7, 0.55, M_WET, C1)
for o in (STREAK, POOL): o.visible_shadow = False
# trees (CC0) behind the wall and at the sides, flowers along the wall
def lib(asset, names=None):
    with bpy.data.libraries.load(os.path.join(A, "ph", asset, asset + "_1k.blend"), link=False) as (src, dst):
        dst.objects = [n for n in src.objects if names is None or n in names]
    return [o for o in dst.objects if o]
TREE_SRC = {}
def place_tree(asset, loc, scale, rotz):
    """geometry-nodes version of the Poly Haven tree (leaves are instances: small file); sources hidden, copies share data"""
    if asset not in TREE_SRC:
        objs = lib(asset, [asset + "_geometry_nodes"])
        g = objs[0]; C1.objects.link(g)
        deps = set()
        for m in g.modifiers:
            if m.type == 'NODES':
                for nd in m.node_group.nodes:
                    for inp in nd.inputs:
                        if getattr(inp, "default_value", None).__class__.__name__ == "Object": deps.add(inp.default_value)
                    if nd.type == 'OBJECT_INFO' and nd.inputs[0].default_value: deps.add(nd.inputs[0].default_value)
                    if nd.type == 'COLLECTION_INFO' and nd.inputs[0].default_value:
                        for o in nd.inputs[0].default_value.all_objects: deps.add(o)
        for o in deps:
            if o and o.name not in C1.objects and not o.users_collection: C1.objects.link(o)
            if o: o.hide_render = True; o.hide_viewport = True; o.location = (0, 0, -200)
        g.location = (0, 0, -300); g.hide_render = True; g.hide_viewport = True
        TREE_SRC[asset] = g
        for m in bpy.data.materials:
            if m.name == "island_tree_02" and m.use_nodes and not m.get("greened"):
                m["greened"] = 1
                for x in m.node_tree.nodes:
                    if x.type == 'TEX_IMAGE' and x.image and "diff" in x.image.name:
                        hs_ = m.node_tree.nodes.new('ShaderNodeHueSaturation'); hs_.inputs['Saturation'].default_value = 0.0
                        mt_ = m.node_tree.nodes.new('ShaderNodeMix'); mt_.data_type = 'RGBA'; mt_.blend_type = 'MULTIPLY'; mt_.inputs['Factor'].default_value = 1.0
                        mt_.inputs['B'].default_value = (0.75, 0.5, 0.32, 1)
                        tg_ = [l.to_socket for l in x.outputs['Color'].links]
                        m.node_tree.links.new(x.outputs['Color'], hs_.inputs['Color']); m.node_tree.links.new(hs_.outputs['Color'], mt_.inputs['A'])
                        for t_ in tg_: m.node_tree.links.new(mt_.outputs['Result'], t_)
                        print("BROWNED", m.name)
            if ("leaves" in m.name.lower() or "branches" in m.name.lower()) and m.use_nodes and not m.get("greened"):
                m["greened"] = 1; nt = m.node_tree
                p = next((x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED'), None)
                tex_ = next((x for x in nt.nodes if x.type == 'TEX_IMAGE' and x.image and "diff" in x.image.name), None)
                if tex_:
                    src_ = tex_.outputs['Color']; tgt_ = [l.to_socket for l in tex_.outputs['Color'].links]
                    hs = nt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Hue'].default_value = 0.5
                    bw_ = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(src_, bw_.inputs[0])
                    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
                    mx.inputs['B'].default_value = (0.35, 0.75, 0.25, 1)
                    br = nt.nodes.new('ShaderNodeMath'); br.operation = 'MULTIPLY'; br.inputs[1].default_value = 1.6; nt.links.new(bw_.outputs[0], br.inputs[0])
                    cc = nt.nodes.new('ShaderNodeCombineColor'); [nt.links.new(br.outputs[0], cc.inputs[k]) for k in range(3)]
                    nt.links.new(cc.outputs[0], mx.inputs['A'])
                    al_ = next((x for x in nt.nodes if x.type == 'TEX_IMAGE' and x.image and "alpha" in x.image.name), None)
                    pl_ = nt.nodes.new('ShaderNodeBsdfPrincipled'); pl_.inputs['Roughness'].default_value = 0.6
                    nt.links.new(mx.outputs['Result'], pl_.inputs['Base Color'])
                    if al_: nt.links.new(al_.outputs['Color'], pl_.inputs['Alpha'])
                    mo_ = next(x for x in nt.nodes if x.type == 'OUTPUT_MATERIAL'); nt.links.new(pl_.outputs[0], mo_.inputs['Surface'])
                    print("GREENED", m.name)
    src = TREE_SRC[asset]
    t = src.copy(); t.name = "S1_Tree_" + asset; C1.objects.link(t)
    t.hide_render = t.hide_viewport = False
    t.location = loc; t.scale = (scale,) * 3; t.rotation_euler = (0, 0, R_(rotz))
    return t
for loc, sc_, rz, a in (((-6.5, 5.0, 0), 1.0, 20, "island_tree_02"), ((6.0, 6.5, 0), 0.95, 140, "island_tree_02"),
                        ((-11.5, -5.5, 0), 0.85, 200, "island_tree_02"), ((11.0, -7.5, 0), 0.9, 80, "island_tree_02"),
                        ((2.5, 9.0, 0), 1.1, 260, "island_tree_02"),
                        ((-15.0, -12.0, 0), 1.0, 30, "island_tree_02"), ((15.5, -13.0, 0), 1.05, 300, "island_tree_02"),
                        ((-8.0, -17.0, 0), 0.95, 120, "island_tree_02"), ((7.0, -18.5, 0), 1.0, 220, "island_tree_02"),
                        ((-18.0, 1.0, 0), 1.1, 70, "island_tree_02"), ((18.0, 0.5, 0), 1.0, 160, "island_tree_02")):
    place_tree(a, loc, sc_, rz)
# church side building suggestion behind wall: simple gabled block in plaster, far back
M_CH = pbr("M_ChurchPlaster", "white_plaster_02", 3.0, sat=0.5, val=1.1, tint=(1.0, 0.95, 0.85))
box("S1_ChurchBlock", -4.0, 4.0, 3.0, 10.0, 0, 7.5, M_CH, C1)
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=5.8, depth=3.0, location=(0, 6.5, 9.0)); roof = bpy.context.active_object
roof.name = "S1_ChurchRoof"; roof.rotation_euler = (0, 0, R_(45)); roof.scale = (1.0, 0.98, 1); roof.data.materials.append(flat("M_Roof", (0.55, 0.2, 0.12), 0.6)); link(roof, C1)

M_BLD = [pbr("M_Bld%d" % i, "white_plaster_02", 3.0, sat=0.5, val=1.05, tint=t) for i, t in enumerate(((1.0, 0.92, 0.78), (0.85, 0.92, 1.0), (1.0, 0.85, 0.8)))]
M_WIN = flat("M_Window", (0.12, 0.16, 0.2), 0.15)
for i, (x0, x1, y0, y1, h, mi) in enumerate(((-24, -14, -26, -14, 9, 0), (-12, -2, -30, -24, 7, 1), (2, 12, -30, -24, 10, 2), (14, 24, -26, -14, 8, 1),
                                             (-24, -16, -10, 4, 8, 2), (16, 24, -10, 4, 9, 0))):
    box("S1_Bld%d" % i, x0, x1, y0, y1, 0, h, M_BLD[mi], C1)
    for k in range(int(h // 3)):
        for j in range(3):
            if abs(y1 - y0) < abs(x1 - x0):
                xx = x0 + (j + 0.5) * (x1 - x0) / 3; yy = y1 if y1 < -10 else y0
                box("S1_Win%d_%d_%d" % (i, k, j), xx - 0.6, xx + 0.6, yy - 0.05, yy + 0.05, 1.5 + 3 * k, 2.8 + 3 * k, M_WIN, C1)
            else:
                yy = y0 + (j + 0.5) * (y1 - y0) / 3; xx = x1 if x1 < 0 else x0
                box("S1_Win%d_%d_%d" % (i, k, j), xx - 0.05, xx + 0.05, yy - 0.6, yy + 0.6, 1.5 + 3 * k, 2.8 + 3 * k, M_WIN, C1)
# sun + sky
sun = bpy.data.objects.new("L_Sun", bpy.data.lights.new("L_Sun", 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.2; sun.data.angle = R_(3); sun.data.color = (1.0, 0.96, 0.9); sun.rotation_euler = (R_(48), R_(0), R_(-28))
w = bpy.data.worlds.new("W_Sky"); sc.world = w; w.use_nodes = True
wn, wl = w.node_tree.nodes, w.node_tree.links; wn.clear()
wout = wn.new('ShaderNodeOutputWorld'); lp = wn.new('ShaderNodeLightPath')
bg_light = wn.new('ShaderNodeBackground'); bg_light.inputs['Color'].default_value = (0.62, 0.78, 1.0, 1); bg_light.inputs['Strength'].default_value = 0.9
tcw = wn.new('ShaderNodeTexCoord'); sep = wn.new('ShaderNodeSeparateXYZ'); wl.new(tcw.outputs['Generated'], sep.inputs[0])
rampw = wn.new('ShaderNodeValToRGB'); rampw.color_ramp.elements[0].position = 0.0; rampw.color_ramp.elements[0].color = (0.80, 0.92, 1.0, 1)
rampw.color_ramp.elements[1].position = 0.35; rampw.color_ramp.elements[1].color = (0.078, 0.55, 0.93, 1)
wl.new(sep.outputs['Z'], rampw.inputs['Fac'])
bg_cam = wn.new('ShaderNodeBackground'); wl.new(rampw.outputs['Color'], bg_cam.inputs['Color']); bg_cam.inputs['Strength'].default_value = 1.0
mixw = wn.new('ShaderNodeMixShader'); wl.new(lp.outputs['Is Camera Ray'], mixw.inputs['Fac'])
wl.new(bg_light.outputs[0], mixw.inputs[1]); wl.new(bg_cam.outputs[0], mixw.inputs[2]); wl.new(mixw.outputs[0], wout.inputs['Surface'])

# ================================================================== S2 bathroom (x = BX)
M_TILE = pbr("M_WallTiles", "long_white_tiles", 1.0, sat=0.6, val=1.1)
M_PLAS = pbr("M_BathPlaster", "worn_mossy_plasterwall", 1.6, sat=0.55, val=1.15)
M_PLAIN = pbr("M_BathPlasterClean", "white_plaster_02", 1.5, sat=0.4, val=1.1, tint=(0.95, 0.97, 1.0))
M_FLOOR = pbr("M_BathFloor", "floor_tiles_06", 0.8, sat=0.8, val=1.0)
X0, X1, Y0, Y1, H = BX - 1.3, BX + 1.3, -1.5, 1.1, 2.7
box("S2_Floor", X0 - 0.2, X1 + 0.2, Y0 - 0.2, Y1 + 0.2, -0.1, 0.0, M_FLOOR, C2)
box("S2_Ceiling", X0 - 0.2, X1 + 0.2, Y0 - 0.2, Y1 + 0.2, H, H + 0.1, M_PLAIN, C2)
# back wall: tiles to 1.3 m, damp plaster above
box("S2_BackTiles", X0, X1, Y1, Y1 + 0.2, 0, 1.3, M_TILE, C2)
box("S2_BackPlaster", X0, X1, Y1, Y1 + 0.2, 1.3, H, M_PLAS, C2)
box("S2_TileTrim", X0, X1, Y1 - 0.012, Y1, 1.29, 1.33, flat("M_Trim", (0.75, 0.78, 0.8), 0.3), C2)
for nm, xa, xb in (("S2_WallL", X0 - 0.2, X0), ("S2_WallR", X1, X1 + 0.2)):
    box(nm + "Tiles", xa, xb, Y0, Y1 + 0.2, 0, 1.3, M_TILE, C2); box(nm + "Plaster", xa, xb, Y0, Y1 + 0.2, 1.3, H, M_PLAIN, C2)
# front wall with a door gap (camera stands in the doorway in the wide)
box("S2_FrontA", X0 - 0.2, BX - 0.45, Y0 - 0.2, Y0, 0, H, M_PLAIN, C2); box("S2_FrontB", BX + 0.45, X1 + 0.2, Y0 - 0.2, Y0, 0, H, M_PLAIN, C2)
box("S2_FrontTop", BX - 0.45, BX + 0.45, Y0 - 0.2, Y0, 2.1, H, M_PLAIN, C2)
sc["BATH"] = (X0, X1, Y0, Y1, H)
# toilet (CC-BY HippoStance) against the back wall, left of centre
T = glb(os.path.join(A, "models", "toilet.glb"), C2, "S2_Toilet")
fit(T, scale=1.0)
pts = [V(c) for c in T.bound_box]; ymx = max(p.y for p in pts)
T.location = (BX - 0.65, Y1 - ymx - 0.01, 0.0)
for m in T.data.materials:
    if m and m.use_nodes:
        p = m.node_tree.nodes.get("Principled BSDF")
        if p: p.inputs['Roughness'].default_value = max(0.2, p.inputs['Roughness'].default_value)
# PVC drain pipe: vertical stack from the ceiling at the right, horizontal run along the back wall at z=1.85, a coupling that leaks
M_PVC = flat("M_PVC", (0.78, 0.8, 0.82), 0.38, coat=0.2)
M_PVC_JOINT = flat("M_PVCJoint", (0.62, 0.64, 0.66), 0.42)
def cyl(name, p0, p1, r, mat, verts=32):
    d = V(p1) - V(p0); L = d.length
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=L)
    o = bpy.context.active_object; o.name = name
    o.location = (V(p0) + V(p1)) / 2; o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat); link(o, C2); return o
PZ, PY, PR_ = 1.85, Y1 - 0.075, 0.05
cyl("S2_PipeRunA", (X0, PY, PZ), (BX + 0.22, PY, PZ), PR_, M_PVC)
cyl("S2_PipeRunB", (BX + 0.38, PY, PZ), (X1 - 0.25, PY, PZ), PR_, M_PVC)
JOINT = cyl("S2_PipeJoint", (BX + 0.20, PY, PZ), (BX + 0.40, PY, PZ), PR_ + 0.012, M_PVC_JOINT)
cyl("S2_PipeElbow", (X1 - 0.27, PY, PZ), (X1 - 0.15, PY, PZ), PR_ + 0.012, M_PVC_JOINT)
cyl("S2_PipeStack", (X1 - 0.16, PY, PZ - 0.05), (X1 - 0.16, PY, H), PR_, M_PVC)
cyl("S2_PipeDown", (X1 - 0.16, PY, 0.0), (X1 - 0.16, PY, PZ - 0.05), PR_, M_PVC)
for i, xx in enumerate((X0 + 0.4, BX - 0.35, BX + 0.85)):
    bpy.ops.mesh.primitive_torus_add(major_radius=PR_ + 0.008, minor_radius=0.008, location=(xx, PY, PZ), rotation=(0, R_(90), 0))
    cl_ = bpy.context.active_object; cl_.name = "S2_PipeClip%d" % i; cl_.data.materials.append(M_PVC_JOINT); link(cl_, C2)
sc["JOINT"] = (BX + 0.30, PY, PZ - PR_ - 0.012)
# floor drain (round grate) in front of the toilet, right side
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.09, depth=0.01, location=(BX + 0.35, 0.35, 0.004))
DR = bpy.context.active_object; DR.name = "S2_FloorDrain"; DR.data.materials.append(flat("M_Grate", (0.55, 0.56, 0.58), 0.3, metal=1.0)); link(DR, C2)
for k in range(5):
    box("S2_GrateSlot%d" % k, BX + 0.35 - 0.06, BX + 0.35 + 0.06, 0.35 - 0.05 + k * 0.025, 0.35 - 0.04 + k * 0.025, 0.0, 0.0105, flat("M_Slot", (0.05, 0.05, 0.05), 0.6), C2)
sc["DRAIN"] = (BX + 0.35, 0.35, 0.0)
# damp streak below the joint on the plaster + tiles (dark green-brown, glossy, noise-edged)
M_DAMP = bpy.data.materials.new("M_Damp"); M_DAMP.use_nodes = True; M_DAMP.blend_method = 'BLEND'
dn, dl = M_DAMP.node_tree.nodes, M_DAMP.node_tree.links; dn.clear()
do = dn.new('ShaderNodeOutputMaterial'); dp = dn.new('ShaderNodeBsdfPrincipled'); dt = dn.new('ShaderNodeBsdfTransparent'); dm = dn.new('ShaderNodeMixShader')
dp.inputs['Roughness'].default_value = 0.25
tcd = dn.new('ShaderNodeTexCoord'); sepd = dn.new('ShaderNodeSeparateXYZ'); dl.new(tcd.outputs['Generated'], sepd.inputs[0])
# width profile: |x-0.5| widening toward the bottom, noisy edge
nzd = dn.new('ShaderNodeTexNoise'); nzd.inputs['Scale'].default_value = 4; nzd.inputs['Detail'].default_value = 8; nzd.inputs['Roughness'].default_value = 0.65
mpd = dn.new('ShaderNodeMapping'); mpd.inputs['Scale'].default_value = (1, 0.25, 1); dl.new(tcd.outputs['Generated'], mpd.inputs['Vector']); dl.new(mpd.outputs['Vector'], nzd.inputs['Vector'])
ax = dn.new('ShaderNodeMath'); ax.operation = 'SUBTRACT'; ax.inputs[1].default_value = 0.5; dl.new(sepd.outputs['X'], ax.inputs[0])
ab = dn.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'; dl.new(ax.outputs[0], ab.inputs[0])
wd = dn.new('ShaderNodeMapRange'); wd.inputs['From Min'].default_value = 0.0; wd.inputs['From Max'].default_value = 1.0
wd.inputs['To Min'].default_value = 0.42; wd.inputs['To Max'].default_value = 0.12; dl.new(sepd.outputs['Y'], wd.inputs['Value'])   # wider at the bottom (y=0)
nadd = dn.new('ShaderNodeMath'); nadd.operation = 'MULTIPLY_ADD'; nadd.inputs[1].default_value = 0.34; nadd.inputs[2].default_value = -0.17
dl.new(nzd.outputs['Fac'], nadd.inputs[0])
edge = dn.new('ShaderNodeMath'); edge.operation = 'ADD'; dl.new(wd.outputs['Result'], edge.inputs[0]); dl.new(nadd.outputs[0], edge.inputs[1])
st = dn.new('ShaderNodeMath'); st.operation = 'SUBTRACT'; dl.new(edge.outputs[0], st.inputs[0]); dl.new(ab.outputs[0], st.inputs[1])
mk = dn.new('ShaderNodeMapRange'); mk.inputs['From Min'].default_value = 0.0; mk.inputs['From Max'].default_value = 0.06; dl.new(st.outputs[0], mk.inputs['Value'])
colr = dn.new('ShaderNodeValToRGB'); colr.color_ramp.elements[0].color = (0.02, 0.035, 0.01, 1); colr.color_ramp.elements[1].color = (0.07, 0.05, 0.02, 1)
dl.new(nzd.outputs['Fac'], colr.inputs['Fac']); dl.new(colr.outputs['Color'], dp.inputs['Base Color'])
fade = dn.new('ShaderNodeMath'); fade.operation = 'MULTIPLY'; fade.inputs[1].default_value = 0.95; dl.new(mk.outputs['Result'], fade.inputs[0])
dl.new(fade.outputs[0], dm.inputs['Fac']); dl.new(dt.outputs[0], dm.inputs[1]); dl.new(dp.outputs[0], dm.inputs[2]); dl.new(dm.outputs[0], do.inputs['Surface'])
DAMP = plane("S2_DampStreak", BX + 0.30, Y1 - 0.003, PZ / 2 - 0.02, 0.7, PZ - 0.02, M_DAMP, C2, rot=(R_(90), 0, 0))
DAMP.visible_shadow = False
# lights: ceiling panel + soft fill (bright clean interior)
lt = bpy.data.objects.new("L_BathCeil", bpy.data.lights.new("L_BathCeil", 'AREA')); sc.collection.objects.link(lt)
lt.data.energy = 260; lt.data.size = 1.2; lt.location = (BX, -0.2, H - 0.05); lt.data.color = (1.0, 0.97, 0.92)
lf = bpy.data.objects.new("L_BathFill", bpy.data.lights.new("L_BathFill", 'AREA')); sc.collection.objects.link(lf)
lf.data.energy = 90; lf.data.size = 1.5; lf.location = (BX, Y0 + 0.2, 1.6); lf.rotation_euler = (R_(90), 0, 0)

# ================================================================== props
# cup: lathe profile, white glazed ceramic
prof = [(0.0, 0.0), (0.030, 0.0), (0.034, 0.004), (0.038, 0.06), (0.042, 0.092), (0.039, 0.092), (0.035, 0.062), (0.031, 0.008), (0.0, 0.008)]
me = bpy.data.meshes.new("Cup"); bm = bmesh.new()
rings = []
N = 40
for i in range(N):
    a = 2 * math.pi * i / N
    rings.append([bm.verts.new((r * math.cos(a), r * math.sin(a), z)) for r, z in prof])
for i in range(N):
    A_, B_ = rings[i], rings[(i + 1) % N]
    for k in range(len(prof) - 1):
        try: bm.faces.new((A_[k], B_[k], B_[k + 1], A_[k + 1]))
        except ValueError: pass
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.to_mesh(me); bm.free()
CUP = bpy.data.objects.new("PR_Cup", me); PR.objects.link(CUP)
for p_ in me.polygons: p_.use_smooth = True
CUP.data.materials.append(flat("M_CupCeramic", (0.92, 0.92, 0.9), 0.2, coat=0.6))
CUP.location = (0, 0, -50)
# water inside the cup (rises with keyed scale)
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.033, depth=0.002)
CW = bpy.context.active_object; CW.name = "PR_CupWater"; CW.data.materials.append(water_mat("M_CupWater")); link(CW, PR)
CW.parent = CUP; CW.location = (0, 0, 0.03)
# trolley case (CC-BY The Motion Tree): flat charcoal (the maker's mark goes), stood on its wheels
TC = glb(os.path.join(A, "models", "trolley.glb"), PR, "PR_Trolley")
dm_ = TC.modifiers.new("dec", 'DECIMATE'); dm_.ratio = 0.25; bpy.ops.object.modifier_apply(modifier="dec")
fit(TC, height=0.98)
TC.data.materials.clear(); TC.data.materials.append(flat("M_TrolleyShell", (0.05, 0.055, 0.065), 0.35, coat=0.3))
TC.location = (0, 0, -60)
# logo decal on the case's broad side (white logo on the dark shell)
pts = [V(c) for c in TC.bound_box]
tx = (min(p.x for p in pts), max(p.x for p in pts)); ty = (min(p.y for p in pts), max(p.y for p in pts)); tz = (min(p.z for p in pts), max(p.z for p in pts))
sc["TROLLEY_BB"] = (*tx, *ty, *tz)
LG = bpy.data.materials.new("M_LogoWhite"); LG.use_nodes = True; LG.blend_method = 'BLEND'
ln, ll = LG.node_tree.nodes, LG.node_tree.links; lo = ln["Material Output"]; lp_ = ln["Principled BSDF"]
li = ln.new('ShaderNodeTexImage'); li.image = img(os.path.join(A, "DaKrasFilms_logo_white.png")); li.extension = 'CLIP'
ll.new(li.outputs['Color'], lp_.inputs['Base Color']); ll.new(li.outputs['Alpha'], lp_.inputs['Alpha']); lp_.inputs['Roughness'].default_value = 0.4
broad_x = (tx[1] - tx[0]) > (ty[1] - ty[0])
w_ = 0.82 * ((tx[1] - tx[0]) if broad_x else (ty[1] - ty[0])); h_ = w_ * 414 / 967
bpy.ops.mesh.primitive_plane_add(size=1)
LOGO = bpy.context.active_object; LOGO.name = "PR_TrolleyLogo"; LOGO.scale = (w_, h_, 1); bpy.ops.object.transform_apply(scale=True)
LOGO.data.materials.append(LG); link(LOGO, PR); LOGO.visible_shadow = False
zl = tz[0] + 0.33 * (tz[1] - tz[0])
LOGO2 = LOGO.copy(); LOGO2.name = "PR_TrolleyLogoBack"; PR.objects.link(LOGO2)
for o_, yv, rz in ((LOGO, ty[0] - 0.003, 0.0), (LOGO2, ty[1] + 0.003, 180.0)):
    o_.parent = TC; o_.matrix_parent_inverse = Matrix.Identity(4)
    if broad_x: o_.rotation_euler = (R_(90), 0, R_(rz)); o_.location = (0, yv, zl)
    else: o_.rotation_euler = (R_(90), 0, R_(rz - 90)); o_.location = ((tx[0] - 0.003) if rz == 0 else (tx[1] + 0.003), 0, zl)
print("TROLLEY bb", [round(v, 3) for v in (*tx, *ty, *tz)], "broad_x", broad_x)
# drops (water): a pool of 8 drop meshes, parked; FX script keys them
M_W = water_mat()
for i in range(8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=0.009)
    d = bpy.context.active_object; d.name = "FX_Drop%d" % i; d.scale = (1, 1, 1.5); bpy.ops.object.shade_smooth()
    d.data.materials.append(M_W); link(d, FX); d.location = (0, 0, -70 - i)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SETS_OK")
