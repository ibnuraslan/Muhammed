"""Clipping-check pass: 270x480 close-ups of every contact moment (hands, feet, hooves, head contact).
blender -b anim.blend --python contact_closeups.py -- <out_dir>"""
import sys, os
import bpy
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene; cam = sc.camera
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.render.use_motion_blur = False
sc.render.image_settings.file_format = 'JPEG'
cam.animation_data_clear(); cam.data.animation_data_clear(); cam.data.dof.use_dof = False
O = {n: bpy.data.objects[n] for n in ("Owner", "OffA", "OffB", "Rescuer", "Goat_rig")}
def bone(o, b, end="head"):
    pb = O[o].pose.bones[b]; return O[o].matrix_world @ (pb.head if end == "head" else pb.tail)
SHOTS = [  # (frame, name, target fn, camera offset, lens)
    (100, "stick_grip", lambda: bone("Owner", "wrist.R"), Vector((0.5, -0.4, 0.1)), 50),
    (958, "impact_hands", lambda: bone("Owner", "wrist.L"), Vector((-0.5, -0.6, 0.1)), 45),
    (1060, "doubled_over_hands", lambda: bone("Owner", "wrist.L"), Vector((-0.6, -0.5, 0.2)), 45),
    (1250, "belly_clutch", lambda: bone("Owner", "wrist.R"), Vector((0.5, -0.7, 0.15)), 45),
    (1350, "stair_belly_clutch", lambda: bone("Owner", "wrist.R"), Vector((-0.6, -0.6, 0.2)), 45),
    (1760, "official_hand_on_goat", lambda: bone("OffB", "wrist.R"), Vector((0.6, -0.6, 0.3)), 45),
    (1438, "porch_hands", lambda: bone("Owner", "wrist.L"), Vector((-0.6, -0.8, 0.2)), 45),
    (1600, "lying_ground", lambda: bone("Owner", "spine03"), Vector((1.2, -1.2, 0.6)), 35),
    (1820, "catch_pole_hands", lambda: bone("OffA", "wrist.R"), Vector((0.6, -0.6, 0.2)), 45),
    (1870, "ramp_hooves", lambda: bone("Goat_rig", "IK_hoof.FL"), Vector((1.0, -0.6, 0.3)), 40),
    (2150, "feeding_hand", lambda: bone("Rescuer", "wrist.R"), Vector((0.3, 0.9, 0.25)), 45),
    (2150, "stroking_hand", lambda: bone("Rescuer", "wrist.L"), Vector((0.6, 0.7, 0.35)), 45),
    (2060, "feeding_palm_2", lambda: bone("Rescuer", "wrist.R"), Vector((0.4, -0.7, 0.2)), 45),
]
for f, name, tf, off, lens in SHOTS:
    sc.frame_set(f); t = tf(); p = t + off
    cam.location = p; cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = lens
    sc.render.filepath = os.path.join(OUT, "%04d_%s.jpg" % (f, name)); bpy.ops.render.render(write_still=True)
print("CLOSEUPS", len(SHOTS))
