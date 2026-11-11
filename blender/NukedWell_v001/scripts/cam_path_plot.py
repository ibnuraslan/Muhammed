"""Plot the camera spline (top + front views) with beat markers.
blender -b anim.blend --python cam_path_plot.py -- <out.csv>; then python3 -I cam_path_draw.py <out.csv> <beats.json> <out.png>"""
import sys, json, os
import bpy
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; cam = sc.camera; tg = bpy.data.objects["CAM_Target"]
rows = []
for f in range(1, sc.frame_end + 1, 4):
    sc.frame_set(f); p = cam.matrix_world.translation; t = tg.matrix_world.translation
    rows.append((f, p.x, p.y, p.z, t.x, t.y, t.z, cam.data.lens))
beats = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "beats.json")))
import csv
with open(out, "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["frame", "cx", "cy", "cz", "tx", "ty", "tz", "lens"]); w.writerows(rows)
print("CSV", out)
