"""Close-up hand pass at 270x480: renders each contact moment from a debug camera (does not touch the film camera keys on disk).
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
SHOTS = [  # every hand action: name, frame, (char, bone) target, camera offset, lens
 ("resA_feed_rope", 330, ("ResA", "wrist.R"), (-0.35, -0.45, 0.2), 35),
 ("resB_hand_on_rim", 330, ("ResB", "wrist.L"), (0.3, -0.5, 0.25), 35),
 ("operator_levers", 640, ("Operator", "wrist.L"), (0.35, 0.25, 0.15), 30),
 ("crowd1_restrains_mother", 900, ("Crowd1", "wrist.R"), (-0.5, 0.1, 0.15), 30),
 ("mother_hands_face", 960, ("Mother", "head"), (0.2, -0.7, 0.0), 40),
 ("teen_points_self", 1085, ("Teen", "wrist.R"), (0.35, -0.45, 0.1), 35),
 ("resB_knot", 1220, ("ResB", "wrist.L"), (-0.5, -0.35, 0.2), 35),
 ("resA_tripod_leg", 1240, ("ResA", "wrist.L"), (0.2, -0.5, 0.2), 30),
 ("holders_hold_belt", 1322, ("ResA", "wrist.R"), (-0.1, -0.5, -0.25), 30),
 ("holders_hold_legs", 1336, ("ResB", "wrist.L"), (0.1, -0.6, -0.2), 30),
 ("teen_grips_toddler", 1580, ("Teen", "wrist.L"), (0.15, -0.7, 0.0), 32),
 ("toddler_clings_rise", 1700, ("Toddler", "wrist.L"), (0.1, -0.75, 0.0), 32),
 ("haul_hand_over_hand", 1700, ("ResB", "wrist.L"), (0.6, -0.5, 0.2), 30),
 ("resA_guides_hips", 1792, ("ResA", "wrist.L"), (0.6, -0.6, 0.1), 30),
 ("teen_lifts_toddler", 1840, ("Teen", "wrist.L"), (0.6, -0.6, -0.1), 30),
 ("mother_hug", 1920, ("Mother", "wrist.L"), (0.5, -0.6, 0.1), 30),
 ("handoff_teen_to_mother", 1900, ("Mother", "wrist.R"), (-0.5, -0.6, 0.1), 30),
 ("cheer_clap", 1880, ("ResA", "wrist.L"), (0.4, -0.6, 0.0), 30),
 ("toddler_arms_up_bottom", 300, ("Toddler", "wrist.R"), (0.1, -0.1, 0.35), 18),
]
for name, f, (n, b), off, lens in SHOTS:
    p = bone(n, b, f); tg.location = p; cam.location = p + V(off); cam.data.lens = lens
    sc.render.filepath = os.path.join(OUT, "%04d_%s.jpg" % (f, name)); bpy.ops.render.render(write_still=True)
print("CONTACT done")
