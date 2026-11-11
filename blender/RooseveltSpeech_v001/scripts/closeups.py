"""Clipping check: 270x480 close-ups of every contact moment.  blender -b anim.blend --python closeups.py -- <out_dir>"""
import sys, os, bpy
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene; H = bpy.data.objects["Hero"]; cam = sc.camera
cam.animation_data_clear(); cam.data.animation_data_clear(); cam.rotation_mode = "QUATERNION"; cam.data.lens = 45
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.render.use_motion_blur = False
sc.render.image_settings.file_format = "JPEG"
SHOTS = [("hat_grip", 60, "wrist.R", (0.25, -0.5, 0.1)), ("rail_grip_L", 260, "wrist.L", (0.35, -0.45, 0.15)), ("rail_grip_L_frozen", 900, "wrist.L", (0.1, -0.5, 0.3)),
         ("feet_car", 120, "foot.L", (0.5, -0.8, 0.45)), ("feet_step", 230, "foot.R", (-0.4, -0.8, 0.4)), ("specs_moustache", 300, "head", (0.2, -0.45, 0.05)),
         ("specs_side", 1300, "head", (0.45, -0.1, 0.05)), ("pocket_grasp", 1212, "wrist.R", (-0.3, -0.5, 0.05)), ("manuscript_lift", 1262, "wrist.R", (-0.3, -0.55, 0.0)),
         ("podium_hand_L", 1250, "wrist.L", (0.35, -0.5, 0.15)), ("fist_L", 1320, "wrist.L", (0.4, -0.5, 0.05)), ("podium_slam_L", 1380, "wrist.L", (0.3, -0.5, 0.2)),
         ("feet_stage", 1330, "foot.L", (0.5, -0.8, 0.4)), ("elbow_armpit", 1320, "lowerarm01.L", (0.6, -0.6, 0.1))]
for name, f, bone, off in SHOTS:
    sc.frame_set(f); p = H.matrix_world @ H.pose.bones[bone].head
    cam.location = p + Vector(off); cam.rotation_quaternion = (p - cam.location).to_track_quat("-Z", "Y")
    sc.render.filepath = os.path.join(OUT, f"{name}_f{f}.jpg"); bpy.ops.render.render(write_still=True)
print("CLOSEUPS", len(SHOTS))
