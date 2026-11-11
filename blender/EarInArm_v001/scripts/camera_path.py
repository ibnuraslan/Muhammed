"""Dump CAM_Film path (every 2 frames) and plot top/side views per space. blender -b film.blend --python camera_path.py -- review/camera_path.png"""
import sys, json, bpy
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; cam = sc.camera; pts = []
for f in range(1, sc.frame_end + 1, 2):
    sc.frame_set(f); p = cam.matrix_world.translation; pts.append((f, p.x, p.y, p.z, cam.data.lens))
json.dump(pts, open(out.replace(".png", ".json"), "w"))
