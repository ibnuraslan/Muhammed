"""Close-up contact pass at 270x480: renders each contact moment from a debug camera (does not touch the film camera keys on disk).
blender -b work/film.blend --python scripts/contact_pass.py -- <out_dir>"""
import sys, os, bpy
from mathutils import Vector as V
OUT = sys.argv[sys.argv.index("--") + 1]; os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
cam = bpy.data.objects["Cam"]; tg = bpy.data.objects["CamTarget"]
for o in (cam, tg, cam.data): o.animation_data_clear()
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.render.use_motion_blur = False
sc.render.image_settings.file_format = "JPEG"
def bone(n, b, f):
    sc.frame_set(f); o = bpy.data.objects[n]; return o.matrix_world @ o.pose.bones[b].head
SHOTS = [  # name, frame, (char, bone) target, camera offset, lens
 ("toddler_rim", 90, ("Toddler", "foot.R"), (0.5, -0.9, 0.5), 40),
 ("toddler_land", 210, ("Toddler", "root"), (0.25, -0.0, 0.5), 18),
 ("loop_miss", 440, ("Toddler", "wrist.L"), (0.2, -0.15, 0.4), 22),
 ("rb_kneel_rim", 330, ("ResB", "wrist.L"), (0.6, -0.8, 0.3), 35),
 ("knot", 1220, ("Teen", "root"), (-0.6, -0.9, 0.1), 35),
 ("hold_legs", 1340, ("Teen", "foot.L"), (0.9, -1.0, -0.3), 28),
 ("teen_in_pipe", 1400, ("Teen", "spine01"), (0.0, -0.33, -0.6), 14),
 ("grip", 1580, ("Teen", "wrist.L"), (0.25, -0.2, -0.2), 18),
 ("rise", 1700, ("Teen", "wrist.L"), (0.0, -1.6, 0.1), 30),
 ("haul", 1700, ("ResB", "wrist.L"), (1.0, -0.6, 0.3), 30),
 ("emerge", 1795, ("Teen", "wrist.L"), (0.9, -1.0, 0.2), 28),
 ("liftup", 1850, ("Toddler", "root"), (0.9, -1.1, -0.2), 30),
 ("mother_hug", 1920, ("Toddler", "root"), (0.8, -1.0, 0.1), 30),
 ("feet_crowd", 1500, ("Mother", "foot.L"), (0.6, -1.0, 0.3), 35),
 ("hats", 1000, ("ResA", "head"), (0.5, -0.7, 0.1), 40),
 ("torch", 1290, ("Teen", "head"), (0.4, -0.5, 0.05), 45),
]
for name, f, (n, b), off, lens in SHOTS:
    p = bone(n, b, f); tg.location = p; cam.location = p + V(off); cam.data.lens = lens
    sc.render.filepath = os.path.join(OUT, "%04d_%s.jpg" % (f, name)); bpy.ops.render.render(write_still=True)
print("CONTACT done")
