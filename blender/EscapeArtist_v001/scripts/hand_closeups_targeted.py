"""Targeted 270x480 close-ups of the v004 hand contacts from side angles. blender -b film.blend --python hand_closeups_targeted.py -- <out_dir>"""
import sys, os, bpy
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
SH = [(636, (0.75, -1.15, 1.45), (-0.3, -0.45, 1.15), "pulls cell door"), (1484, (6.4, 2.75, 1.7), (7.6, 1.6, 1.1), "guard pushes gate"),
      (2154, (0.0, -2.75, 1.05), (0.55, -2.25, 0.55), "picks up saw"), (2524, (0.75, -1.15, 1.45), (-0.3, -0.45, 1.1), "pulls door again"),
      (2576, (-0.4, 0.55, 1.2), (-1.15, 1.3, 1.0), "draws tube from pocket"), (2940, (-0.45, -0.75, 1.75), (-1.31, -1.4, 1.6), "scratches tally"),
      (3064, (-0.4, -1.4, 1.0), (0.4, -1.85, 0.75), "sits down"), (3458, (-0.4, -1.4, 1.1), (0.4, -1.85, 0.8), "old man stands up"),
      (1300, (1.6, 7.0, 1.1), (0.9, 7.8, 0.85), "boy holds toolbox"), (1250, (6.1, 6.95, 1.6), (7.15, 8.2, 1.4), "phone + point")]
cam = bpy.data.objects.new("HCam2", bpy.data.cameras.new("HCam2")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 30; cam.data.clip_start = 0.01
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.cycles.use_denoising = True
sc.render.use_motion_blur = False; sc.render.image_settings.file_format = "JPEG"
idx = []
for i, (f, p, t, what) in enumerate(SH):
    sc.frame_set(f); cam.location = p; cam.rotation_euler = (Vector(t) - Vector(p)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(OUT, "t%02d.jpg" % i); bpy.ops.render.render(write_still=True); idx.append("t%02d f%d %s" % (i, f, what))
open(os.path.join(OUT, "index.txt"), "w").write("\n".join(idx)); print("TARGETED_DONE")
