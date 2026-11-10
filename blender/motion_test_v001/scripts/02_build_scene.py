"""Scene template: 60 fps timeline, Cycles settings, colour management,
lighting, ground, crate, bottle, background grass.

blender -b character.blend --python 02_build_scene.py -- <assets_dir> <out.blend>
assets_dir contains the Poly Haven downloads (hdri/, grass_ground/,
wooden_crate_01/, grass_medium_01/).
"""
import sys, os, math, random
import bpy
from mathutils import Vector, Matrix, Euler

argv = sys.argv[sys.argv.index("--") + 1:]
A, OUT = argv[0], argv[1]
sc = bpy.context.scene
GROUND_Z = -0.003          # shoe soles sit 3 mm below the MPFB zero

# ---------------------------------------------------------------- timeline
sc.render.fps = 60
sc.render.fps_base = 1.0
sc.frame_start, sc.frame_end, sc.frame_step = 1, 600, 1
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.resolution_percentage = 100
sc.render.pixel_aspect_x = sc.render.pixel_aspect_y = 1

# ---------------------------------------------------------------- cycles
sc.render.engine = 'CYCLES'
cy = sc.cycles
cy.device = 'CPU'
cy.samples = 48
cy.use_adaptive_sampling = True
cy.adaptive_threshold = 0.05
cy.use_denoising = True
cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 8
cy.diffuse_bounces = 3
cy.glossy_bounces = 3
cy.transmission_bounces = 8
cy.transparent_max_bounces = 16
cy.caustics_reflective = False
cy.caustics_refractive = False
cy.blur_glossy = 1.0
sc.render.use_motion_blur = True
sc.render.motion_blur_shutter = 0.5
sc.render.use_persistent_data = True
sc.render.film_transparent = False

# ---------------------------------------------------------------- colour
vs = sc.view_settings
sc.display_settings.display_device = 'sRGB'
vs.view_transform = 'AgX'
vs.look = 'AgX - Medium High Contrast'
vs.exposure = 0.0
vs.gamma = 1.0
sc.sequencer_colorspace_settings.name = 'sRGB'

# ---------------------------------------------------------------- output
im = sc.render.image_settings
im.file_format = 'PNG'
im.color_mode = 'RGB'
im.color_depth = '8'
im.compression = 15
sc.render.filepath = "//render/MotionTest_v001_"
sc.render.use_file_extension = True

# ---------------------------------------------------------------- helpers
def img(path, non_color=False):
    i = bpy.data.images.load(path, check_existing=True)
    if non_color:
        i.colorspace_settings.name = 'Non-Color'
    return i

def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links

# ---------------------------------------------------------------- world
w = bpy.data.worlds.new("World_MeadowOvercast")
sc.world = w
w.use_nodes = True
wn, wl = w.node_tree.nodes, w.node_tree.links
wn.clear()
tc = wn.new('ShaderNodeTexCoord')
mp = wn.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (0, 0, math.radians(300))
env = wn.new('ShaderNodeTexEnvironment'); env.image = img(os.path.join(A, "hdri/hausdorf_meadow_2k.hdr"))
bg = wn.new('ShaderNodeBackground'); bg.inputs['Strength'].default_value = 0.85
out = wn.new('ShaderNodeOutputWorld')
wl.new(tc.outputs['Generated'], mp.inputs['Vector'])
wl.new(mp.outputs['Vector'], env.inputs['Vector'])
wl.new(env.outputs['Color'], bg.inputs['Color'])
wl.new(bg.outputs['Background'], out.inputs['Surface'])

# ---------------------------------------------------------------- key light
sun_d = bpy.data.lights.new("Key_Sun", 'SUN')
sun_d.energy = 3.2
sun_d.angle = math.radians(9.0)          # soft but readable shadow edge
sun_d.color = (1.0, 0.94, 0.86)
sun = bpy.data.objects.new("Key_Sun", sun_d)
sc.collection.objects.link(sun)
# azimuth measured from the character's forward (-Y) toward its right (-X):
# key from the front, slightly right, 40 deg up -> ~55 deg off the camera axis
az, el = math.radians(-10), math.radians(40)
d = Vector((math.cos(el) * math.sin(az), -math.cos(el) * math.cos(az), math.sin(el)))  # toward light
sun.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()

# ---------------------------------------------------------------- ground
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, GROUND_Z))
ground = bpy.context.active_object
ground.name = "Ground_Lawn"
ground.scale = (160, 160, 1)
bpy.ops.object.transform_apply(scale=True)
m, n, l = new_mat("M_Lawn_GrassGround")
n.clear()
o = n.new('ShaderNodeOutputMaterial')
p = n.new('ShaderNodeBsdfPrincipled')
tco = n.new('ShaderNodeTexCoord')
mpp = n.new('ShaderNodeMapping'); mpp.inputs['Scale'].default_value = (1 / 2.2, 1 / 2.2, 1)
mpp2 = n.new('ShaderNodeMapping'); mpp2.inputs['Scale'].default_value = (1 / 5.3, 1 / 5.3, 1)
mpp2.inputs['Rotation'].default_value = (0, 0, math.radians(37))
G = os.path.join(A, "grass_ground")
dif = n.new('ShaderNodeTexImage'); dif.image = img(os.path.join(G, "grass_ground_diff_2k.jpg"))
dif2 = n.new('ShaderNodeTexImage'); dif2.image = dif.image
rgh = n.new('ShaderNodeTexImage'); rgh.image = img(os.path.join(G, "grass_ground_rough_2k.jpg"), True)
nor = n.new('ShaderNodeTexImage'); nor.image = img(os.path.join(G, "grass_ground_nor_gl_2k.jpg"), True)
nmap = n.new('ShaderNodeNormalMap'); nmap.inputs['Strength'].default_value = 1.0
noise = n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 0.35; noise.inputs['Detail'].default_value = 3
mix = n.new('ShaderNodeMix'); mix.data_type = 'RGBA'
hsv = n.new('ShaderNodeHueSaturation')
hsv.inputs['Saturation'].default_value = 0.82
hsv.inputs['Value'].default_value = 0.95
for a_, b_ in [(tco.outputs['Object'], mpp.inputs['Vector']), (tco.outputs['Object'], mpp2.inputs['Vector']),
               (mpp.outputs['Vector'], dif.inputs['Vector']), (mpp2.outputs['Vector'], dif2.inputs['Vector']),
               (mpp.outputs['Vector'], rgh.inputs['Vector']), (mpp.outputs['Vector'], nor.inputs['Vector']),
               (tco.outputs['Object'], noise.inputs['Vector']),
               (noise.outputs['Fac'], mix.inputs['Factor']),
               (dif.outputs['Color'], mix.inputs['A']), (dif2.outputs['Color'], mix.inputs['B']),
               (mix.outputs['Result'], hsv.inputs['Color']), (hsv.outputs['Color'], p.inputs['Base Color']),
               (rgh.outputs['Color'], p.inputs['Roughness']),
               (nor.outputs['Color'], nmap.inputs['Color']), (nmap.outputs['Normal'], p.inputs['Normal']),
               (p.outputs['BSDF'], o.inputs['Surface'])]:
    l.new(a_, b_)
p.inputs['Specular IOR Level'].default_value = 0.3
ground.data.materials.append(m)

# ---------------------------------------------------------------- crate
def append_all(blend, prefix):
    with bpy.data.libraries.load(blend, link=False) as (src, dst):
        dst.objects = [x for x in src.objects]
    obs = []
    for ob in dst.objects:
        if ob is None:
            continue
        sc.collection.objects.link(ob)
        obs.append(ob)
    return obs

crate_parts = append_all(os.path.join(A, "wooden_crate_01/wooden_crate_01_2k.blend"), "crate")
crate = bpy.data.objects.new("Crate", None)
crate.empty_display_type = 'CUBE'; crate.empty_display_size = 0.05
sc.collection.objects.link(crate)
for ob in crate_parts:
    ob.parent = crate
# crate placement is finalised by 03_animate.py (it depends on the reach pose)
crate["top_z"] = max((ob.matrix_world @ Vector(c)).z for ob in crate_parts for c in ob.bound_box)

# ---------------------------------------------------------------- bottle
R = [  # (radius cm, height cm) outer profile, bottom to top
    (0.0, 0.0), (2.9, 0.0), (3.25, 0.35), (3.35, 1.2), (3.35, 13.8), (3.2, 15.4),
    (2.6, 17.4), (1.75, 19.0), (1.35, 20.4), (1.3, 22.8), (1.48, 23.1), (1.5, 24.2),
    (1.38, 24.6), (1.12, 24.65)]
verts = [(r / 100, 0, z / 100) for r, z in R]
me = bpy.data.meshes.new("Bottle_profile")
me.from_pydata(verts, [(i, i + 1) for i in range(len(verts) - 1)], [])
bottle = bpy.data.objects.new("Bottle", me)
sc.collection.objects.link(bottle)
scr = bottle.modifiers.new("Lathe", 'SCREW'); scr.axis = 'Z'; scr.steps = 48; scr.render_steps = 48
scr.use_merge_vertices = True; scr.use_normal_calculate = True
sol = bottle.modifiers.new("Glass", 'SOLIDIFY'); sol.thickness = 0.0025; sol.offset = -1
sub = bottle.modifiers.new("Smooth", 'SUBSURF'); sub.levels = 1; sub.render_levels = 2
bpy.context.view_layer.objects.active = bottle
bottle.select_set(True)
for mod in list(bottle.modifiers):
    bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.ops.object.shade_smooth()
m, n, l = new_mat("M_Bottle_GreenGlass")
p = n["Principled BSDF"]
p.inputs['Base Color'].default_value = (0.16, 0.30, 0.13, 1)
p.inputs['Transmission Weight'].default_value = 1.0
p.inputs['Roughness'].default_value = 0.06
p.inputs['IOR'].default_value = 1.5
vol = n.new('ShaderNodeVolumeAbsorption')
vol.inputs['Color'].default_value = (0.20, 0.42, 0.16, 1); vol.inputs['Density'].default_value = 60
l.new(vol.outputs['Volume'], n['Material Output'].inputs['Volume'])
bottle.data.materials.append(m)
# paper label
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.0338, depth=0.07, end_fill_type='NOTHING', location=(0, 0, 0.081))
label = bpy.context.active_object; label.name = "Bottle_Label"
bpy.ops.object.shade_smooth()
m, n, l = new_mat("M_Bottle_Label_Paper")
p = n["Principled BSDF"]
wave = n.new('ShaderNodeTexWave'); wave.wave_type = 'BANDS'; wave.bands_direction = 'Z'
wave.inputs['Scale'].default_value = 1.2; wave.inputs['Distortion'].default_value = 0
ramp = n.new('ShaderNodeValToRGB')
ramp.color_ramp.interpolation = 'CONSTANT'
ramp.color_ramp.elements[0].color = (0.62, 0.55, 0.42, 1)
ramp.color_ramp.elements[1].position = 0.55
ramp.color_ramp.elements[1].color = (0.35, 0.16, 0.10, 1)
tcl = n.new('ShaderNodeTexCoord')
l.new(tcl.outputs['Generated'], wave.inputs['Vector'])
l.new(wave.outputs['Fac'], ramp.inputs['Fac'])
l.new(ramp.outputs['Color'], p.inputs['Base Color'])
p.inputs['Roughness'].default_value = 0.75
label.data.materials.append(m)
label.parent = bottle

# ---------------------------------------------------------------- background grass clumps
gparts = append_all(os.path.join(A, "grass_medium_01/grass_medium_01_2k.blend"), "grass")
lod0 = [o for o in gparts if o.type == 'MESH' and o.name.endswith("LOD0")]
for o in gparts:
    if o not in lod0:
        bpy.data.objects.remove(o, do_unlink=True)
gcol = bpy.data.collections.new("GrassClumps_src")
sc.collection.children.link(gcol)
for o in lod0:
    for c in o.users_collection:
        c.objects.unlink(o)
    gcol.objects.link(o)
    o.location = (0, 0, 0)
gcol.hide_render = True
gcol.hide_viewport = True
scatter = bpy.data.collections.new("GrassClumps")
sc.collection.children.link(scatter)
rnd = random.Random(7)
placed = 0
while placed < 140:
    x, y = rnd.uniform(-5, 5), rnd.uniform(-7, 6)
    # keep the action area (walk path, crate, camera side) clean
    if -1.4 < x < 1.6 and -1.6 < y < 2.6:
        continue
    if x < -1.0 and y < -0.5:      # camera corridor
        continue
    src = rnd.choice(lod0)
    inst = bpy.data.objects.new(f"Grass_{placed:03d}", src.data)
    inst.location = (x, y, GROUND_Z)
    inst.rotation_euler = (0, 0, rnd.uniform(0, 6.283))
    s = rnd.uniform(0.7, 1.25)
    inst.scale = (s, s, s * rnd.uniform(0.8, 1.2))
    scatter.objects.link(inst)
    placed += 1

sc["ground_z"] = GROUND_Z
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SCENE_OK", sc.render.fps, sc.frame_start, sc.frame_end, vs.view_transform, vs.look, crate["top_z"])
