"""Soft high-key fill lights per interior set + render settings. blender -b build/anim.blend --python 04_lights.py"""
import bpy, os, math
from mathutils import Vector
exec(open(os.path.dirname(os.path.abspath(__file__)) + "/common.py").read())
sc = bpy.context.scene
LC = bpy.data.collections.get("LIGHTS") or bpy.data.collections.new("LIGHTS")
if LC.name not in sc.collection.children: sc.collection.children.link(LC)
def area(name, loc, tgt, size, energy, col=(1, 1, 1)):
    L = bpy.data.objects.get(name) or bpy.data.objects.new(name, bpy.data.lights.new(name, 'AREA'))
    if L.name not in LC.objects: LC.objects.link(L)
    L.data.shape = 'RECTANGLE'; L.data.size = size; L.data.size_y = size * 0.7; L.data.energy = energy; L.data.color = col
    L.location = loc; L.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
for key, (e_key, e_fill) in {"HOME": (320, 140), "OFFICE": (320, 140), "GARAGE": (380, 160), "STUDIO": (420, 180)}.items():
    ox, oy = sc[key]
    area(key + "_Key", (ox - 2.0, oy - 2.8, 3.2), (ox, oy + 0.2, 1.2), 3.0, e_key, (1.0, 0.96, 0.9))
    area(key + "_Fill", (ox + 2.4, oy - 2.2, 2.2), (ox, oy + 0.2, 1.3), 3.0, e_fill, (0.9, 0.95, 1.0))
    area(key + "_Top", (ox, oy + 0.3, 3.9), (ox, oy + 0.3, 0.0), 4.0, 260)
ox, oy = sc["STUDIO"]
for dx in (-4.0, 4.0):
    area(f"STUDIO_Key{dx:+.0f}", (ox + dx - 1.5, oy - 2.8, 3.2), (ox + dx, oy + 0.4, 1.2), 3.0, 380, (1.0, 0.96, 0.9))
    area(f"STUDIO_Top{dx:+.0f}", (ox + dx, oy + 0.4, 4.2), (ox + dx, oy + 0.4, 0.0), 4.0, 240)
area("STUDIO_FilmSpot", (ox + 3.0, oy - 0.5, 2.6), (ox + 4.5, oy + 1.2, 1.4), 1.0, 220, (1.0, 0.92, 0.8))
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.max_bounces = 8; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.render.use_motion_blur = False; sc.render.image_settings.file_format = 'PNG'
bpy.ops.wm.save_as_mainfile(filepath=BUILD + "/lit.blend")
print("LIT saved")
