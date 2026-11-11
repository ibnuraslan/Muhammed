"""blender -b film.blend --python camera_path.py -- out.jpg : top view + height plot of CAM_Film, beats marked"""
import bpy, sys, json, os
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; cam = sc.camera; P = []
for f in range(sc.frame_start, sc.frame_end + 1, 2):
    sc.frame_set(f); P.append((f, tuple(cam.matrix_world.translation)))
json.dump(P, open(out + ".json", "w"))
