"""270x480 close-ups of every hand action (client hands rule, step 4).
blender -b anim.blend --python 07_hand_closeups.py -- <out_dir>"""
import sys, os
import bpy
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1:][0]; os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 270, 480, 100
sc.cycles.samples = 8; sc.render.use_motion_blur = False; sc.render.image_settings.file_format = 'JPEG'
cam = bpy.data.objects.new("CAM_Hand", bpy.data.cameras.new("CAM_Hand")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50; cam.data.clip_start = 0.01
SHOTS = [(60, "Lad", "wrist.R", "bottle grip while staggering"), (100, "Lad", "wrist.R", "bottle grip"),
         (1300, "Lad", "wrist.R", "swig: bottle to the mouth"), (1330, "Lad", "wrist.R", "swig hold"),
         (1195, "Lad", "wrist.L", "crawl: hand planted"), (1210, "Lad", "wrist.R", "crawl: hand planted"),
         (2025, "Lad", "wrist.L", "looks at his palm"), (2060, "Lad", "wrist.L", "palm, final"),
         (1100, "WitA", "wrist.L", "hand over the mouth"), (1100, "WitA", "wrist.R", "hand off the chest"),
         (1120, "WitB", "wrist.L", "hands on the head"), (1100, "Worker", "wrist.L", "steadying arm"),
         (2000, "Worker", "wrist.R", "scratches his hard hat"), (420, "Lad", "wrist.R", "lying: hand over the rail"),
         (250, "Lad", "wrist.L", "sitting: forearm on the knee"), (420, "Lad", "wrist.L", "lying: hand on the belly"), (1236, "WitA", "wrist.L", "steps back")]
for i, (f, rn, bn, what) in enumerate(SHOTS):
    sc.frame_set(f); r = bpy.data.objects[rn]
    w = r.matrix_world @ r.pose.bones[bn].head
    head = r.matrix_world @ r.pose.bones["head"].head
    d = (w - head); d.z = 0
    side = d.normalized() if d.length > 1e-3 else Vector((1, 0, 0))
    cam.location = w + side * 0.45 + Vector((0, 0, 0.12)) + (Vector((0.0, -0.25, 0.0)))
    cam.rotation_euler = (w - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, "h%02d_f%04d_%s.jpg" % (i, f, rn)); bpy.ops.render.render(write_still=True)
    print("HAND", i, f, rn, bn, what)
