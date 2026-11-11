"""Clipping-check close-ups at every contact moment (270x480, 8 samples).
blender -b film.blend --python clip_closeups.py -- <out_dir>"""
import bpy, sys, os
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]; os.makedirs(out, exist_ok=True)
sc = bpy.context.scene; O = bpy.data.objects
def bone(arm, n, f): sc.frame_set(f); return O[arm].matrix_world @ O[arm].pose.bones[n].head
def obj(n, f): sc.frame_set(f); return O[n].matrix_world.translation.copy()
SHOTS = [("gun_grip", 1, lambda: bone("Robber", "wrist.R", 1), Vector((0.25, 0.1, 0.1)), 45),
         ("ring_up", 400, lambda: obj("WeddingRing", 400), Vector((0.05, -0.1, 0.03)), 60),
         ("hands_face_side", 541, lambda: bone("Owner", "head", 541), Vector((0.45, -0.1, 0.0)), 50),
         ("hand_neck", 1040, lambda: bone("Owner", "wrist.R", 1040), Vector((-0.2, -0.15, 0.06)), 50),
         ("hand_neck_front", 1040, lambda: bone("Owner", "wrist.R", 1040), Vector((0.05, -0.3, 0.05)), 50),
         ("ring_dented", 1150, lambda: obj("WeddingRing", 1150), Vector((0.06, -0.08, 0.06)), 60),
         ("bandage", 1250, lambda: obj("FingerBandage", 1250), Vector((0.08, -0.18, 0.12)), 55),
         ("plaster", 1250, lambda: obj("NeckPlaster", 1250), Vector((-0.18, -0.12, 0.03)), 55),
         ("feet_walk", 1320, lambda: bone("Owner", "foot.L", 1320), Vector((0.1, -1.0, 0.2)), 35),
         ("feet_stand", 300, lambda: bone("Owner", "foot.L", 300), Vector((0.5, -0.7, 0.2)), 35),
         ("walk_hands", 1300, lambda: bone("Owner", "wrist.L", 1300), Vector((-0.2, -0.9, 0.3)), 35)]
cam = sc.camera; cam.animation_data_clear(); cam.data.animation_data_clear()
cam.rotation_mode = 'QUATERNION'; cam.data.dof.use_dof = False
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.render.use_motion_blur = False
sc.render.image_settings.file_format = 'JPEG'
for i, (nm, f, tgt, off, lens) in enumerate(SHOTS):
    t = tgt(); sc.frame_set(f); cam.location = t + off; cam.rotation_quaternion = (t - cam.location).to_track_quat('-Z', 'Y'); cam.data.lens = lens
    sc.render.filepath = os.path.join(out, "c%02d_%s_f%d.jpg" % (i, nm, f)); bpy.ops.render.render(write_still=True)
