"""270x480 close-ups of every hand contact. blender -b film.blend --python hand_closeups.py -- out_dir"""
import bpy, sys, os
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]; os.makedirs(out, exist_ok=True)
sc = bpy.context.scene; cam = sc.camera; cam.animation_data_clear(); cam.data.animation_data_clear()
cam.data.dof.use_dof = False; cam.data.lens = 40
for o in bpy.data.objects:
    if o.name == "ExplainerCard": o.hide_render = True
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.render.image_settings.file_format = 'JPEG'
SHOTS = [  # (label, frame, rig, bone, camera offset)
    ("grip_R_rest", 300, "Inventor", "wrist.R", (-0.30, -0.12, 0.02)),
    ("support_L_canister", 300, "Inventor", "wrist.L", (0.10, -0.35, -0.12)),
    ("valve_pinch", 400, "Inventor", "wrist.L", (0.32, -0.18, 0.08)),
    ("trigger_pull", 840, "Inventor", "finger2-2.R", (-0.22, -0.10, -0.06)),
    ("aim_two_hands", 980, "Inventor", "wrist.R", (-0.25, -0.30, 0.05)),
    ("lap_hands", 1250, "Inventor", "wrist.L", (0.05, -0.45, 0.15)),
    ("hand_to_face", 1420, "Inventor", "head", (0.15, -0.45, 0.0)),
    ("eye_wipe", 1490, "Inventor", "head", (-0.15, -0.45, 0.0)),
    ("mentor_desk_slap", 1262, "Mentor", "wrist.R", (0.30, 0.35, 0.15)),
    ("mentor_shield", 1640, "Mentor", "wrist.R", (0.1, 0.5, 0.05)),
    ("pencil_sketch", 1730, "Inventor", "wrist.R", (-0.15, -0.30, 0.20)),
    ("file_at_vice", 1800, "Inventor", "wrist.R", (0.05, -0.40, 0.10)),
    ("gun_pickup", 1895, "Inventor", "wrist.R", (-0.25, -0.30, 0.10)),
    ("finale_fire", 1950, "Inventor", "wrist.R", (-0.25, -0.30, 0.05)),
    ("mentor_chest_pat", 2030, "Mentor", "wrist.R", (0.15, 0.55, 0.05)),
]
for i, (lab, f, rig, bone, off) in enumerate(SHOTS):
    sc.frame_set(f); R = bpy.data.objects[rig]; t = (R.matrix_world @ R.pose.bones[bone].matrix).translation
    p = t + Vector(off); cam.location = p; cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, "c%02d_%s_f%d.jpg" % (i, lab, f)); bpy.ops.render.render(write_still=True)
