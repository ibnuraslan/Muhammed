"""Goat rescue scene: timeline, render settings, farm set, hospital set, animals, props, light rig.

blender -b farmer.blend --python 02_build_scene.py -- <assets_root> <work_dir> <out.blend>
assets_root: /opt/assets (ph/ = Poly Haven, objv/ = Objaverse GLBs)
work_dir:    holds goat_rig.blend, cow_rig.blend, scratch_narration.wav
"""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, noise

argv = sys.argv[sys.argv.index("--") + 1:]
A, W, OUT = argv[0], argv[1], argv[2]
PH, OB = os.path.join(A, "ph"), os.path.join(A, "objv")
sc = bpy.context.scene
FPS, END = 60, 2340
GZ = 0.0

# ------------------------------------------------------------------ timeline / render
sc.render.fps, sc.render.fps_base = FPS, 1.0
sc.frame_start, sc.frame_end, sc.frame_step = 1, END, 1
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.engine = 'CYCLES'
c = sc.cycles
c.device = 'CPU'; c.samples = 48; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.05
c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'
c.max_bounces = 8; c.diffuse_bounces = 3; c.glossy_bounces = 3; c.transmission_bounces = 8
c.caustics_reflective = c.caustics_refractive = False
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.render.use_persistent_data = True
sc.display_settings.display_device = 'sRGB'
vs = sc.view_settings
vs.view_transform = 'AgX'; vs.look = 'AgX - Medium High Contrast'; vs.exposure = 0.0; vs.gamma = 1.0
im = sc.render.image_settings
im.file_format = 'PNG'; im.color_mode = 'RGB'; im.color_depth = '8'; im.compression = 15
sc.render.filepath = "//render/GoatRescue2_v001_"

# ------------------------------------------------------------------ helpers
def img(path, nc=False):
    i = bpy.data.images.load(path, check_existing=True)
    if nc:
        i.colorspace_settings.name = 'Non-Color'
    return i

def pbr(name, folder, base, scale, sat=1.0, val=1.0, bump=1.0, rough_mul=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    p = n["Principled BSDF"]
    tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / scale,) * 3
    l.new(tc.outputs['Object'], mp.inputs['Vector'])
    d = n.new('ShaderNodeTexImage'); d.image = img(os.path.join(folder, base + "_diff_2k.jpg"))
    r = n.new('ShaderNodeTexImage'); r.image = img(os.path.join(folder, base + "_rough_2k.jpg"), True)
    nm = n.new('ShaderNodeTexImage'); nm.image = img(os.path.join(folder, base + "_nor_gl_2k.jpg"), True)
    nmap = n.new('ShaderNodeNormalMap'); nmap.inputs['Strength'].default_value = bump
    hsv = n.new('ShaderNodeHueSaturation'); hsv.inputs['Saturation'].default_value = sat; hsv.inputs['Value'].default_value = val
    rm = n.new('ShaderNodeMath'); rm.operation = 'MULTIPLY'; rm.inputs[1].default_value = rough_mul; rm.use_clamp = True
    for a, b in ((mp.outputs['Vector'], d.inputs['Vector']), (mp.outputs['Vector'], r.inputs['Vector']), (mp.outputs['Vector'], nm.inputs['Vector']),
                 (d.outputs['Color'], hsv.inputs['Color']), (hsv.outputs['Color'], p.inputs['Base Color']),
                 (r.outputs['Color'], rm.inputs[0]), (rm.outputs[0], p.inputs['Roughness']),
                 (nm.outputs['Color'], nmap.inputs['Color']), (nmap.outputs['Normal'], p.inputs['Normal'])):
        l.new(a, b)
    return m, n, l

def import_glb(path, name, height=None, length=None, loc=(0, 0, 0), rot_z=0.0, coll=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o.type != 'MESH':
            bpy.data.objects.remove(o, do_unlink=True)
    for o in bpy.data.objects:
        o.select_set(False)
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    pts = [Vector(v.co) for v in ob.data.vertices]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    dims = mx - mn
    s = 1.0
    if height:
        s = height / dims.z
    elif length:
        s = length / max(dims.x, dims.y)
    ob.data.transform(Matrix.Translation(Vector((-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z))))
    ob.data.transform(Matrix.Scale(s, 4))
    ob.location = loc
    ob.rotation_euler = (0, 0, rot_z)
    if coll:
        for c_ in ob.users_collection:
            c_.objects.unlink(ob)
        coll.objects.link(ob)
    return ob

def coll(name):
    c_ = bpy.data.collections.new(name); sc.collection.children.link(c_); return c_

FARM, HOSP, ANIM, PROPS = coll("Farm_Set"), coll("Hospital_Set"), coll("Animals"), coll("Props")

# ------------------------------------------------------------------ world + light rig (keyable)
w = bpy.data.worlds.new("World_Farm"); sc.world = w; w.use_nodes = True
wn, wl = w.node_tree.nodes, w.node_tree.links; wn.clear()
tc = wn.new('ShaderNodeTexCoord'); mp = wn.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (0, 0, math.radians(300))
env = wn.new('ShaderNodeTexEnvironment'); env.image = img(os.path.join(PH, "hdri/hausdorf_meadow_2k.hdr"))
tint = wn.new('ShaderNodeMix'); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'; tint.name = "SkyTint"
tint.inputs['Factor'].default_value = 1.0; tint.inputs['B'].default_value = (1, 1, 1, 1)
bg = wn.new('ShaderNodeBackground'); bg.name = "SkyStrength"; bg.inputs['Strength'].default_value = 0.85
out = wn.new('ShaderNodeOutputWorld')
wl.new(tc.outputs['Generated'], mp.inputs['Vector']); wl.new(mp.outputs['Vector'], env.inputs['Vector'])
wl.new(env.outputs['Color'], tint.inputs['A']); wl.new(tint.outputs['Result'], bg.inputs['Color'])
wl.new(bg.outputs['Background'], out.inputs['Surface'])
sun = bpy.data.objects.new("Key_Sun", bpy.data.lights.new("Key_Sun", 'SUN'))
sun.data.energy = 3.2; sun.data.angle = math.radians(8); sun.data.color = (1.0, 0.94, 0.86)
sc.collection.objects.link(sun)
moon = bpy.data.objects.new("Moon_Fill", bpy.data.lights.new("Moon_Fill", 'SUN'))
moon.data.energy = 0.0; moon.data.angle = math.radians(3); moon.data.color = (0.55, 0.68, 1.0)
moon.rotation_euler = (math.radians(40), 0, math.radians(-140))
sc.collection.objects.link(moon)

# ------------------------------------------------------------------ ground
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, GZ))
ground = bpy.context.active_object; ground.name = "Ground_Field"; ground.scale = (220, 220, 1)
bpy.ops.object.transform_apply(scale=True)
gm, _, _ = pbr("M_Field_Grass", os.path.join(PH, "grass_ground"), "grass_ground", 2.4, sat=0.9, val=0.95)
ground.data.materials.append(gm)
for c_ in ground.users_collection: c_.objects.unlink(ground)
FARM.objects.link(ground)

# ------------------------------------------------------------------ manure heap (plateau top, body hollow)
PILE_C = Vector((0.0, 0.0)); PILE_R = (2.6, 1.9); PILE_H = 0.72
LIE = dict(center=Vector((0.15, 0.05)), angle=math.radians(12), length=1.0, width=0.28, depth=0.10)
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=160, y_segments=120, size=1.0)
for v in bm.verts:
    x, y = v.co.x * PILE_R[0] * 1.35, v.co.y * PILE_R[1] * 1.35
    r = math.sqrt((x / PILE_R[0]) ** 2 + (y / PILE_R[1]) ** 2)
    t = max(0.0, 1.0 - r)
    h = PILE_H * (t ** 0.55) * (3 * t * t - 2 * t * t * t) ** 0.35 if t > 0 else 0.0
    n1 = noise.fractal(Vector((x * 0.9, y * 0.9, 0.3)), 0.5, 2.0, 4) * 0.07
    n2 = noise.noise(Vector((x * 5.0, y * 5.0, 1.7))) * 0.015
    h = h + (n1 + n2) * min(1.0, t * 4)
    # hollow where he lies (soft body-shaped dip)
    ca, sa = math.cos(-LIE["angle"]), math.sin(-LIE["angle"])
    lx = (x - LIE["center"].x) * ca - (y - LIE["center"].y) * sa
    ly = (x - LIE["center"].x) * sa + (y - LIE["center"].y) * ca
    q = (lx / (LIE["length"] * 0.62)) ** 2 + (ly / (LIE["width"] * 1.25)) ** 2
    if q < 1.0:
        h -= LIE["depth"] * (1 - q) ** 1.5
    v.co = Vector((x, y, max(h, -0.02) - 0.02))
bm.normal_update()
pm = bpy.data.meshes.new("ManureHeap"); bm.to_mesh(pm); bm.free()
pile = bpy.data.objects.new("ManureHeap", pm); FARM.objects.link(pile)
for p_ in pm.polygons: p_.use_smooth = True
mm, mn, ml = pbr("M_Manure_Heap", os.path.join(PH, "brown_mud_02"), "brown_mud_02", 0.9, sat=1.25, val=0.62, bump=1.4, rough_mul=0.8)
hsv0 = [nd for nd in mn if nd.type == "HUE_SAT"][0]; hsv0.inputs["Hue"].default_value = 0.47
# straw: hay-coloured fibres mixed through the top layer (procedural streak mask)
p = mn["Principled BSDF"]
wave = mn.new('ShaderNodeTexWave'); wave.wave_type = 'BANDS'; wave.inputs['Scale'].default_value = 38
wave.inputs['Distortion'].default_value = 14; wave.inputs['Detail'].default_value = 3
nz = mn.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0
mul = mn.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
ramp = mn.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position = 0.50; ramp.color_ramp.elements[1].position = 0.66
mixc = mn.new('ShaderNodeMix'); mixc.data_type = 'RGBA'; mixc.inputs['B'].default_value = (0.42, 0.33, 0.17, 1)
tco = mn.new('ShaderNodeTexCoord')
for a, b in ((tco.outputs['Object'], wave.inputs['Vector']), (tco.outputs['Object'], nz.inputs['Vector']),
             (wave.outputs['Fac'], mul.inputs[0]), (nz.outputs['Fac'], mul.inputs[1]),
             (mul.outputs[0], ramp.inputs['Fac']), (ramp.outputs['Color'], mixc.inputs['Factor'])):
    ml.new(a, b)
hsvn = [nd for nd in mn if nd.type == 'HUE_SAT'][0]
ml.new(hsvn.outputs['Color'], mixc.inputs['A'])
ml.new(mixc.outputs['Result'], p.inputs['Base Color'])
pile.data.materials.append(mm)
sc["lie_center"] = (LIE["center"].x, LIE["center"].y)
sc["lie_angle"] = LIE["angle"]

bpy.context.view_layer.update()
def pile_height(x, y):
    """ray-cast the heap from above"""
    hit, loc, nrm, idx = pile.ray_cast(Vector((x, y, 5)), Vector((0, 0, -1)))
    return loc.z if hit else 0.0
sc["pile_top"] = pile_height(LIE["center"].x, LIE["center"].y)

# ------------------------------------------------------------------ farm props
barn = import_glb(os.path.join(OB, "barn.glb"), "Barn", height=7.5, loc=(-5.5, 16.0, 0), rot_z=math.radians(200), coll=FARM)
for i, (x, y, r) in enumerate([(4.8, 6.5, 10), (5.9, 6.9, -5), (5.3, 7.6, 40), (-7.5, 9.0, 80)]):
    import_glb(os.path.join(OB, "hay_bale.glb"), "HayBale_%d" % i, length=1.0, loc=(x, y, 0), rot_z=math.radians(r), coll=FARM)
for o in [o for o in bpy.data.objects if o.name.startswith("HayBale_")]:
    for m in o.data.materials:
        for nd in m.node_tree.nodes:
            if nd.type == 'BSDF_PRINCIPLED':
                lk = nd.inputs['Base Color'].links
                if lk:
                    hs = m.node_tree.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 0.55; hs.inputs['Value'].default_value = 0.8
                    m.node_tree.links.new(lk[0].from_socket, hs.inputs['Color']); m.node_tree.links.new(hs.outputs['Color'], nd.inputs['Base Color'])
                nd.inputs['Roughness'].default_value = 0.9
for i, (x, y, r) in enumerate([(14, 22, 0), (19, 30, 30), (-16, 26, 60), (24, 14, 10)]):
    import_glb(os.path.join(OB, "hay_round.glb"), "HayRound_%d" % i, height=1.5, loc=(x, y, 0), rot_z=math.radians(r), coll=FARM)
for i in range(7):
    import_glb(os.path.join(OB, "fence.glb"), "Fence_%d" % i, length=3.0, loc=(-9.0 + i * 3.0, 10.5, 0), rot_z=0, coll=FARM)
fork = import_glb(os.path.join(OB, "pitchfork.glb"), "Pitchfork", length=1.45, loc=(-2.9, -0.6, 0.6), coll=PROPS)

# ------------------------------------------------------------------ animals (rigged)
def append_rig(path, prefix):
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith(prefix)]
    for o in dst.objects:
        ANIM.objects.link(o)
    return bpy.data.objects[prefix + "_rig"]
goat = append_rig(os.path.join(W, "goat_rig.blend"), "goat")
cow = append_rig(os.path.join(W, "cow_rig.blend"), "cow")
goat.location = (3.2, 2.6, 0); cow.location = (-7.0, -3.5, 0)

# ------------------------------------------------------------------ ambulance + stretcher
amb = import_glb(os.path.join(OB, "ambulance.glb"), "Ambulance", length=5.6, loc=(-6.5, -4.5, 0), rot_z=math.radians(70), coll=PROPS)
for f_, h_ in ((1, True), (1960, False)):
    amb.hide_render = h_; amb.hide_viewport = False; amb.keyframe_insert("hide_render", frame=f_)
def box(name, size, loc, mat, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    for c_ in o.users_collection: c_.objects.unlink(o)
    PROPS.objects.link(o)
    if parent: o.parent = parent
    return o
def flat(name, rgb, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    pp = m.node_tree.nodes["Principled BSDF"]; pp.inputs['Base Color'].default_value = (*rgb, 1)
    pp.inputs['Roughness'].default_value = rough; pp.inputs['Metallic'].default_value = metal
    return m
st = bpy.data.objects.new("Stretcher", None); PROPS.objects.link(st); st.location = (-4.0, -3.0, 0)
mat_frame, mat_pad = flat("M_Stretcher_Frame", (0.55, 0.56, 0.58), 0.35, 1.0), flat("M_Stretcher_Pad", (0.09, 0.22, 0.36), 0.6)
box("Stretcher_Pad", (0.58, 1.95, 0.08), (0, 0, 0.62), mat_pad, st)
box("Stretcher_Frame", (0.62, 2.0, 0.04), (0, 0, 0.56), mat_frame, st)
for sx in (-0.27, 0.27):
    for sy in (-0.85, 0.85):
        box("Stretcher_Leg", (0.035, 0.035, 0.52), (sx, sy, 0.28), mat_frame, st)
for o in st.children:
    o.location = o.location - Vector((0, 0, 0))

# ------------------------------------------------------------------ hospital room (separate set at x=60)
HX = Vector((60.0, 0.0, 0.0))
wall = flat("M_Hospital_Wall", (0.58, 0.6, 0.57), 0.85)
floor = flat("M_Hospital_Floor", (0.62, 0.64, 0.66), 0.35)
box("Hosp_Floor", (6, 6, 0.1), HX + Vector((0, 0, -0.04)), floor).users_collection[0].objects.unlink(bpy.data.objects["Hosp_Floor"])
HOSP.objects.link(bpy.data.objects["Hosp_Floor"])
def hwall(name, size, loc):
    o = box(name, size, HX + Vector(loc), wall); PROPS.objects.unlink(o); HOSP.objects.link(o); return o
hwall("Hosp_Wall_Back", (6, 0.12, 3.0), (0, 3.0, 1.5))
hwall("Hosp_Wall_L", (0.12, 6, 3.0), (-3.0, 0, 1.5))
# window wall (right side, +X) with an opening 1.6 x 1.3 m
hwall("Hosp_Wall_R_low", (0.12, 6, 0.55), (3.0, 0, 0.275))
hwall("Hosp_Wall_R_high", (0.12, 6, 1.15), (3.0, 0, 2.425))
hwall("Hosp_Wall_R_a", (0.12, 2.2, 1.3), (3.0, -1.9, 1.2))
hwall("Hosp_Wall_R_b", (0.12, 2.2, 1.3), (3.0, 1.9, 1.2))
sill = box("Hosp_Sill", (0.35, 1.7, 0.05), HX + Vector((3.05, 0, 0.565)), flat("M_Sill", (0.85, 0.85, 0.83), 0.4))
PROPS.objects.unlink(sill); HOSP.objects.link(sill)
bed = import_glb(os.path.join(OB, "hospital_bed.glb"), "Hospital_Bed", length=2.15, loc=HX + Vector((1.2, 0.2, 0)), rot_z=0, coll=HOSP)
vase = import_glb(os.path.join(OB, "flowers_vase.glb"), "Flowers_Vase", height=0.48, loc=HX + Vector((2.95, -0.5, 0.59)), coll=HOSP)
light_h = bpy.data.objects.new("Hosp_Window_Light", bpy.data.lights.new("Hosp_Window_Light", 'AREA'))
light_h.data.energy = 140; light_h.data.size = 1.6; light_h.data.color = (1.0, 0.95, 0.88)
light_h.location = HX + Vector((3.6, 0, 1.6)); light_h.rotation_euler = (0, math.radians(90), 0)
HOSP.objects.link(light_h)
outside = bpy.data.objects.new("Hosp_Outside_Ground", None)
# outside the window: the same field continues (ground plane already covers x=60)

# ------------------------------------------------------------------ x-ray bones (hidden until the fracture beat)
femur = import_glb(os.path.join(OB, "femur.glb"), "XRay_Femur", length=0.46, coll=PROPS)
pelvis = import_glb(os.path.join(OB, "pelvis.glb"), "XRay_Pelvis", length=0.28, coll=PROPS)
xr = bpy.data.materials.new("M_XRay_Bone"); xr.use_nodes = True
xn, xl = xr.node_tree.nodes, xr.node_tree.links; xn.clear()
xo = xn.new('ShaderNodeOutputMaterial'); xe = xn.new('ShaderNodeEmission'); xe.inputs['Color'].default_value = (0.75, 0.9, 1.0, 1)
xe.inputs['Strength'].default_value = 2.0
xf = xn.new('ShaderNodeLayerWeight'); xf.inputs['Blend'].default_value = 0.35
xt = xn.new('ShaderNodeBsdfTransparent'); xm = xn.new('ShaderNodeMixShader')
xl.new(xf.outputs['Facing'], xm.inputs['Fac']); xl.new(xt.outputs['BSDF'], xm.inputs[1]); xl.new(xe.outputs['Emission'], xm.inputs[2])
xl.new(xm.outputs['Shader'], xo.inputs['Surface'])
for o in (femur, pelvis):
    o.data.materials.clear(); o.data.materials.append(xr)
    o.hide_render = True

# ------------------------------------------------------------------ farmer to collection, scratch narration
farmer = bpy.data.objects["Farmer"]
sc.sequence_editor_create()
wav = os.path.join(W, "scratch_narration.wav")
try:
    strips = sc.sequence_editor.strips
except AttributeError:
    strips = sc.sequence_editor.sequences
snd = strips.new_sound("SCRATCH_reference_narration_DO_NOT_PUBLISH", wav, channel=1, frame_start=1)

bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SCENE_OK pile_top=%.3f" % sc["pile_top"], "objects", len(bpy.data.objects))
