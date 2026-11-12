"""270x480 close-ups of every hand action.  blender -b film.blend --python hand_closeups.py -- <out_dir>"""
import sys, os, bpy
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]; os.makedirs(out, exist_ok=True)
sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 270, 480, 100
sc.cycles.samples = 8; sc.render.image_settings.file_format = 'JPEG'
cam = sc.camera; cam.animation_data_clear(); cam.data.animation_data_clear(); cam.data.lens = 40; cam.data.dof.use_dof = False
SHOTS = [("Fisher_reach_fish", "Fisher", "wrist.R", 6.75, (0.9, 0.5, 0.4)), ("Fisher_grip_tail", "Fisher", "wrist.R", 7.6, (0.5, -0.7, 0.2)),
         ("Fisher_grip_tail_b", "Fisher", "wrist.R", 8.4, (-0.35, 0.85, 0.05)), ("Fisher_wave_shout", "Fisher", "wrist.L", 9.9, (0.4, -1.0, 0.0)),
         ("TouristW_point", "TouristW", "wrist.R", 6.7, (-0.75, 0.25, 0.1)), ("LocalW_point", "LocalW", "wrist.R", 8.6, (-0.75, 0.3, 0.1)),
         ("LocalM_point", "LocalM", "wrist.L", 9.5, (0.75, 0.3, 0.1)), ("OldM_shade_eyes", "OldM", "wrist.R", 8.0, (0.3, -0.9, 0.0)),
         ("TouristM_shade_eyes", "TouristM", "wrist.L", 9.2, (-0.3, -0.9, 0.0)), ("LocalW_hang", "LocalW", "wrist.R", 5.3, (-0.6, 0.5, 0.1)),
         ("KidA_run_arms", "KidA", "wrist.R", 2.0, (-0.8, 0.6, 0.2)), ("TouristW_run", "TouristW", "wrist.R", 19.3, (-0.9, -0.6, 0.2)),
         ("LocalM_run", "LocalM", "wrist.L", 20.0, (0.9, -0.7, 0.2)), ("Fisher_run", "Fisher", "wrist.R", 19.0, (-0.8, -0.8, 0.2))]
for name, rig, bone, t, off in SHOTS:
    sc.frame_set(1 + round(t * 60)); r = bpy.data.objects[rig]
    w = r.matrix_world @ r.pose.bones[bone].head
    cam.location = w + Vector(off); cam.rotation_euler = (w - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, "%05.2f_%s.jpg" % (t, name)); bpy.ops.render.render(write_still=True)
print("CLOSEUPS", len(SHOTS))
