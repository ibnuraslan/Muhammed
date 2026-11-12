"""Targeted 270x480 close-ups of the v004 hand contacts from side angles. blender -b film.blend --python hand_closeups_targeted.py -- <out_dir>"""
import sys, os, bpy
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
SH = [(636, (0.75, -1.15, 1.45), (-0.3, -0.45, 1.15), "pulls cell door"), (1484, (6.4, 2.75, 1.7), (7.6, 1.6, 1.1), "guard pushes gate"),
      (2154, (0.0, -2.75, 1.05), (0.55, -2.25, 0.55), "picks up saw"), (2524, (0.75, -1.15, 1.45), (-0.3, -0.45, 1.1), "pulls door again"),
      (2576, (-0.4, 0.55, 1.2), (-1.15, 1.3, 1.0), "draws tube from pocket"), (2940, (-0.45, -0.75, 1.75), (-1.31, -1.4, 1.6), "scratches tally"),
      (3064, (-0.4, -1.4, 1.0), (0.4, -1.85, 0.75), "sits down"), (3458, (-0.4, -1.4, 1.1), (0.4, -1.85, 0.8), "old man stands up"),
      (1300, (1.5, 7.2, 0.9), (0.75, 7.75, 0.5), "boy carries toolbox"), (620, (0.45, -0.55, 1.15), (-0.15, -0.08, 1.0), "key at the lock"),
      (1680, (7.9, -13.2, 3.0), (7.0, -13.8, 2.6), "fence climb hands"), (1750, (7.9, -13.1, 4.1), (7.0, -13.8, 3.6), "fence top hands"),
      (2180, (-0.5, -2.2, 1.2), (0.0, -2.5, 0.9), "carries saw"), (2300, (0.3, -3.75, 1.7), (0.0, -3.2, 1.62), "saw grip"), (1250, (6.1, 6.95, 1.6), (7.15, 8.2, 1.4), "phone + point")]
cam = bpy.data.objects.new("HCam2", bpy.data.cameras.new("HCam2")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 30; cam.data.clip_start = 0.01
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.cycles.use_denoising = True
sc.render.use_motion_blur = False; sc.render.image_settings.file_format = "JPEG"
idx = []
OUTSIDE = {636: 1, 620: 1, 1680: 1, 1750: 1, 2524: 1}
AUTO = {620: ("Prisoner", "R", (0, 0, 0)), 636: ("Prisoner", "L", (0.35, -0.6, 0.15)), 2524: ("Prisoner", "L", (-0.35, 0.75, 0.1)), 1300: ("Boy", "R", (0.5, 0.25, 0.25)),
        1250: ("Stepmother", "R", (-0.45, -0.45, 0.1)), 2940: ("Prisoner", "R", (0.22, -0.3, 0.22)), 1680: ("Prisoner", "mid", (0.95, 0.25, 0.05)),
        1750: ("Prisoner", "mid", (0.9, 0.1, 0.2)), 2180: ("Prisoner", "L", (-0.35, 0.35, 0.1)), 2154: ("Prisoner", "L", (-0.35, -0.35, 0.25))}
for i, (f, p, t, what) in enumerate(SH):
    sc.frame_set(f)
    if f in AUTO:
        n, sd, off = AUTO[f]; A = bpy.data.objects[n]
        wl = A.matrix_world @ A.pose.bones["wrist.L"].head; wr_ = A.matrix_world @ A.pose.bones["wrist.R"].head
        tg = (wl + wr_) / 2 if sd == "mid" else (A.matrix_world @ A.pose.bones["finger3-1." + sd].head)
        t = tuple(tg); p = tuple(tg + Vector(off))
        if f in OUTSIDE:   # camera outside the body: along chest->hand, a bit up and to the side, looking back at the hand
            ch = A.matrix_world @ A.pose.bones["spine03"].head; dv = (tg - ch); dv.z *= 0.3; dv.normalize()
            side = dv.cross(Vector((0, 0, 1))).normalized() * OUTSIDE[f]
            p = tuple(tg + dv * 0.55 + side * 0.25 + Vector((0, 0, 0.12)))
    cam.location = p; cam.rotation_euler = (Vector(t) - Vector(p)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(OUT, "t%02d.jpg" % i); bpy.ops.render.render(write_still=True); idx.append("t%02d f%d %s" % (i, f, what))
open(os.path.join(OUT, "index.txt"), "w").write("\n".join(idx)); print("TARGETED_DONE")
