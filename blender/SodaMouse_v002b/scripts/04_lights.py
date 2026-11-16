"""Bright high-key lights for both sets + render settings. blender -b build/anim.blend --python 04_lights.py"""
import bpy, os, math
from mathutils import Vector
exec(open(os.path.dirname(__file__) + "/common.py").read())
sc = bpy.context.scene
LC = bpy.data.collections.get("LIGHTS") or bpy.data.collections.new("LIGHTS")
if LC.name not in sc.collection.children: sc.collection.children.link(LC)
def area(name, loc, tgt, size, energy, col=(1, 1, 1)):
    L = bpy.data.objects.get(name) or bpy.data.objects.new(name, bpy.data.lights.new(name, 'AREA'))
    if L.name not in LC.objects: LC.objects.link(L)
    L.data.shape = 'RECTANGLE'; L.data.size = size; L.data.size_y = size * 0.7; L.data.energy = energy; L.data.color = col
    L.location = loc; L.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return L
LX = sc["LX"]
for ox, nm in ((0.0, "K"), (LX, "L")):
    area(nm + "_Key", (ox - 1.6, -2.4, 2.8), (ox, 0.2, 1.1), 2.5, 370, (1.0, 0.96, 0.9))
    area(nm + "_Fill", (ox + 2.0, -1.8, 1.8), (ox, 0.2, 1.2), 2.5, 150, (0.9, 0.95, 1.0))
    area(nm + "_Top", (ox, 0.2, 2.9), (ox, 0.2, 0.0), 3.0, 210)
    area(nm + "_Rim", (ox + 0.8, 1.6, 2.4), (ox, 0.3, 1.4), 1.2, 160, (0.9, 0.95, 1.0))
w = sc.world or bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.85, 0.9, 0.97, 1); bg.inputs[1].default_value = 0.4
# back light behind the beaker so the sinking mouse reads (S10)
area("L_BeakerBack", (LX + 0.06, 0.45, 1.05), (LX + 0.06, -0.12, 0.98), 0.35, 45, (1.0, 1.0, 0.95))
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.max_bounces = 8; sc.cycles.transmission_bounces = 8; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.render.use_motion_blur = False
sc.render.image_settings.file_format = 'PNG'
bpy.ops.wm.save_as_mainfile(filepath=BUILD + "/lit.blend")
