"""270x480 close-ups of every hand action. blender -b film.blend --python hand_closeups.py -- <out_dir>"""
import sys, os, bpy
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
SHOTS = [(120, "Prisoner", "bars grip"), (420, "Prisoner", "filing"), (620, "Prisoner", "key in lock"), (636, "Prisoner", "pulls door"), (800, "Boy", "clockwork"),
         (1300, "Boy", "holds toolbox"), (1480, "Guard", "pushes gate"), (2153, "Prisoner", "picks up saw"), (2520, "Prisoner", "pulls door"), (2574, "Prisoner", "draws tube"),
         (2940, "Prisoner", "scratches tally"), (3062, "Prisoner", "sits down"), (3456, "PrisonerOld", "stands up"),
         (1010, "Father", "lifts toolbox"), (1100, "Boy", "takes toolbox"), (1250, "Stepmother", "phone + point"), (1440, "Judge", "gavel"),
         (1680, "Prisoner", "fence climb"), (1750, "Prisoner", "fence top"), (2300, "Prisoner", "saw"), (2600, "Prisoner", "tube"),
         (2600, "Guard", "hands up"), (3560, "Protester1", "placard"), (3720, "PrisonerOld", "window grip")]
cam = bpy.data.objects.new("HCam", bpy.data.cameras.new("HCam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 35; cam.data.clip_start = 0.01
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.cycles.use_denoising = True
sc.render.use_motion_blur = False; sc.render.image_settings.file_format = "JPEG"
for o in bpy.data.objects:
    if o.name.startswith(("Solitary",)) : pass
lines = []
for i, (f, n, what) in enumerate(SHOTS):
    sc.frame_set(f); a = bpy.data.objects[n]; M = a.matrix_world
    wl = M @ a.pose.bones["wrist.L"].head; wr = M @ a.pose.bones["wrist.R"].head; c = (wl + wr) / 2
    root = M @ a.pose.bones["root"].head; fw = (c - root); fw.z = 0
    if fw.length < 0.05: fw = M.to_3x3() @ Vector((0, -1, 0))
    fw.normalize()
    d = max(0.55, (wl - wr).length * 1.3)
    cam.location = c + fw * d + Vector((0, 0, 0.25))
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(OUT, "h%02d.jpg" % i); bpy.ops.render.render(write_still=True)
    lines.append("h%02d f%d %s %s" % (i, f, n, what))
open(os.path.join(OUT, "index.txt"), "w").write("\n".join(lines))
print("CLOSEUPS_DONE")
