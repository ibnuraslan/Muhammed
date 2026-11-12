"""Hand close-up pass: a temporary camera 0.35-0.5 m from each HAND in every hand action, lit, 270x480, 8 samples.
blender -b film.blend --python 05_closeups.py -- <out_dir>"""
import sys, os, bpy
from mathutils import Vector as V
OUT = sys.argv[sys.argv.index("--") + 1]; os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
cd = bpy.data.cameras.new("CLOSE"); cd.lens = 32; cd.clip_start = 0.02; cd.dof.use_dof = False
cam = bpy.data.objects.new("CLOSE", cd); sc.collection.objects.link(cam); sc.camera = cam
lt = bpy.data.objects.new("CLOSE_L", bpy.data.lights.new("CLOSE_L", 'AREA')); lt.data.energy = 25; lt.data.size = 0.6
lt.visible_volume_scatter = False; lt.visible_camera = False; sc.collection.objects.link(lt)
wipe = bpy.data.objects.get("CAM_RockWipe")
if wipe: wipe.hide_render = True
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.render.use_motion_blur = False
sc.render.image_settings.file_format = 'JPEG'
SHOTS = [  # label, frame, rig, hand bone, extra up
    ("walk_hand", 200, "Boy2", "wrist.L", 0.1), ("run_hand", 480, "Boy5", "wrist.R", 0.1),
    ("huddle_hands_on_knees", 1050, "HB2", "wrist.L", 0.15), ("huddle_hands_boy1", 1050, "Boy1", "wrist.R", 0.15),
    ("shield_hand", 1160, "Boy4", "wrist.R", 0.05), ("diver_hands_on_ledge", 1150, "DiverA", "wrist.L", 0.2),
    ("rope_hand", 1330, "DiverB", "wrist.R", 0.1), ("edge_palms_on_rock", 1900, "Boy3", "wrist.L", 0.2),
    ("medic_syringe_grip", 2240, "DiverA", "wrist.R", 0.1), ("medic_steadying_hand", 2240, "DiverA", "wrist.L", 0.1),
    ("mask_fit_L", 2350, "DiverB", "wrist.L", 0.05), ("mask_fit_R", 2350, "DiverB", "wrist.R", 0.05),
    ("mask_straps", 2395, "DiverB", "wrist.L", 0.3), ("tow_harness_grip", 2500, "DiverB", "wrist.L", 0.15),
    ("stretcher_front_grip", 2800, "DiverA", "wrist.R", 0.1), ("stretcher_back_grip", 2800, "DiverB", "wrist.L", 0.1),
    ("stretcher_boy_hands", 2850, "Boy4", "wrist.L", 0.3), ("crowd_clap", 2900, "Crowd1", "wrist.R", 0.05),
    ("boy_wave", 2900, "Boy1", "wrist.R", 0.05)]
for i, (lab, f, rn, bn, up) in enumerate(SHOTS):
    sc.frame_set(f); r = bpy.data.objects[rn]
    h = r.matrix_world @ r.pose.bones[bn].tail        # centre of the hand (wrist tail = palm)
    root = r.matrix_world @ r.pose.bones["root"].head
    side = V((h.x - root.x, h.y - root.y, 0))
    side = side.normalized() if side.length > 1e-3 else V((1, 0, 0))
    cam.location = h + side * 0.38 + V((0, 0, 0.12 + up))
    cam.rotation_euler = (h - cam.location).to_track_quat('-Z', 'Y').to_euler()
    lt.location = cam.location + V((0, 0, 0.25)); lt.rotation_euler = (h - lt.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, "c%02d_f%04d_%s.jpg" % (i, f, lab)); bpy.ops.render.render(write_still=True)
print("CLOSEUPS", len(SHOTS))
