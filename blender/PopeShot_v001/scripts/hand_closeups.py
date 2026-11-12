"""270x480 close-ups of every hand action. blender -b PopeShot_anim.blend --python hand_closeups.py -- <out_dir>"""
import sys, os, bpy
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene; O = bpy.data.objects
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 270, 480, 100
sc.cycles.samples = 8; sc.render.use_motion_blur = False; sc.render.image_settings.file_format = "JPEG"
cam = bpy.data.objects.new("HandCam", bpy.data.cameras.new("HandCam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 35; cam.data.clip_start = 0.01
SHOTS = [  # frame, character, bone, label
    (40, "Shooter", "wrist.R", "shooter_grip"), (240, "Shooter", "wrist.R", "shooter_aim"),
    (150, "Pope", "wrist.R", "pope_wave"), (150, "Pope", "wrist.L", "pope_left"),
    (540, "AideA", "wrist.L", "aideA_catch"), (560, "AideB", "wrist.R", "aideB_catch"), (600, "Pope", "wrist.L", "pope_belly"),
    (700, "SurgA", "wrist.R", "surgeon_A"), (700, "SurgB", "wrist.L", "surgeon_B"), (700, "Nurse", "wrist.R", "nurse"),
    (950, "Pope", "wrist.R", "blessing"), (950, "Pope", "wrist.L", "rail_hand"),
    (1100, "Pope", "wrist.L", "hand_on_shoulder"), (1100, "Prisoner", "wrist.R", "prisoner_hands"),
    (1300, "AideB", "wrist.R", "bullet_pinch"), (1450, "Pope", "wrist.L", "prayer_hands"),
]
FIXED = {"nurse": ((-6.55, 40.45, 8.65), (-7.3, 40.98, 8.05)), "surgeon_A": ((-7.95, 39.55, 8.8), (-8.13, 40.35, 8.28))}
for f, ch, b, lab in SHOTS:
    sc.frame_set(f); r = O[ch]; pb = r.pose.bones[b]
    if lab in FIXED:
        cam.location = FIXED[lab][0]; cam.rotation_euler = (Vector(FIXED[lab][1]) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(OUT, "h%04d_%s.jpg" % (f, lab)); bpy.ops.render.render(write_still=True); continue
    p = r.matrix_world @ ((pb.head + pb.tail) / 2 + (pb.tail - pb.head) * 1.5)
    root = r.matrix_world.translation; fwd = r.matrix_world.to_3x3() @ Vector((0, -1, 0))
    cam.location = p + fwd * 0.45 + Vector((0, 0, 0.12)) + (p - Vector((root.x, root.y, p.z))).normalized() * 0.15
    cam.rotation_euler = (p - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, "h%04d_%s.jpg" % (f, lab)); bpy.ops.render.render(write_still=True)
print("CLOSEUPS", len(SHOTS))
