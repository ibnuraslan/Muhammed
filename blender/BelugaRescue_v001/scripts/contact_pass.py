"""Close-up clipping pass of every contact moment (270x480, 8 spp, its own temporary camera).
blender -b film.blend --python contact_pass.py -- <out_dir>"""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
D = bpy.data.objects["Diver"]
def bw(o, b, f, w="head"):
    sc.frame_set(f); pb = o.pose.bones[b]; return o.matrix_world @ (pb.head if w == "head" else pb.tail)
def ob(n, f): sc.frame_set(f); return bpy.data.objects[n].matrix_world.translation.copy()
# (name, frame, target fn, camera offset, lens)
SHOTS = [
    ("seated_floor", 300, lambda f: bw(D, "root", f), Vector((0.9, 0.6, 0.15)), 35),
    ("calf_grip", 420, lambda f: bw(D, "lowerleg01.R", f).lerp(bw(D, "foot.R", f), 0.4), Vector((0.45, 0.2, 0.3)), 40),
    ("fins_floor", 470, lambda f: bw(D, "foot.L", f), Vector((0.6, 0.5, 0.15)), 35),
    ("loose_fin", 900, lambda f: ob("Diver.FinBlade_R_loose", f), Vector((0.5, 0.6, 0.35)), 35),
    ("mask_side", 700, lambda f: bw(D, "head", f), Vector((0.35, 0.05, 0.05)), 50),
    ("mask_front", 1720, lambda f: bw(D, "head", f), Vector((0.05, 0.4, 0.05)), 50),
    ("ankle_grip_a", 1450, lambda f: bw(D, "foot.R", f), Vector((0.35, 0.3, 0.2)), 45),
    ("ankle_grip_b", 1600, lambda f: bw(D, "foot.R", f), Vector((-0.3, 0.35, -0.1)), 45),
    ("ankle_grip_c", 1850, lambda f: bw(D, "foot.R", f), Vector((0.3, -0.35, 0.05)), 45),
    ("coping_hands", 2130, lambda f: (bw(D, "wrist.L", f) + bw(D, "wrist.R", f)) / 2, Vector((0.3, 0.6, 0.35)), 35),
    ("glass_hands", 1100, lambda f: bw(bpy.data.objects["Keeper"], "wrist.L", f), Vector((0.4, -0.5, 0.1)), 35),
    ("glass_spec", 800, lambda f: bw(bpy.data.objects["SpecA"], "wrist.L", f), Vector((0.4, -0.5, 0.1)), 35),
    ("clap_gallery", 2020, lambda f: bw(bpy.data.objects["SpecA"], "wrist.L", f).lerp(bw(bpy.data.objects["SpecA"], "wrist.R", f), 0.5), Vector((0.1, 0.55, 0.15)), 35),
    ("mouth_hand", 800, lambda f: bw(bpy.data.objects["SpecD"], "wrist.R", f), Vector((0.2, 0.5, 0.1)), 40),
    ("point_specB", 800, lambda f: bw(bpy.data.objects["SpecB"], "wrist.L", f), Vector((0.3, 0.5, 0.1)), 40),
    ("buoy_grip", 2120, lambda f: bw(bpy.data.objects["SpecF"], "wrist.L", f), Vector((0.5, 0.5, 0.25)), 35),
    ("clap_deck", 2050, lambda f: bw(bpy.data.objects["SpecE"], "wrist.L", f), Vector((0.2, 0.7, 0.2)), 35),
    ("stream_dive", 120, lambda f: bw(D, "wrist.L", f), Vector((0.4, 0.3, 0.3)), 35),
    ("deck_feet", 2150, lambda f: bw(bpy.data.objects["SpecF"], "foot.L", f), Vector((0.6, 0.8, 0.3)), 35),
]
cd = bpy.data.cameras.new("QC"); cam = bpy.data.objects.new("QC", cd); sc.collection.objects.link(cam); cd.clip_start = 0.01
sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 270, 480, 100
sc.cycles.samples = 8; sc.render.use_motion_blur = False; sc.render.image_settings.file_format = "JPEG"
for o in bpy.data.objects:
    if o.name == "Explainer_Card": o.animation_data_clear(); o.hide_render = True
for name, f, tf, off, lens in SHOTS:
    t = tf(f); cam.location = t + off; cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler(); cd.lens = lens
    sc.frame_set(f); sc.render.filepath = os.path.join(OUT, "%s_f%04d.jpg" % (name, f)); bpy.ops.render.render(write_still=True)
print("CONTACT_PASS", len(SHOTS))
