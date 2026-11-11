"""Dump CAM_Film per-frame position/target/lens and speed. blender -b film.blend --python camera_path_dump.py -- out.json"""
import bpy, sys, json
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; cam = sc.camera; rows = []
for f in range(sc.frame_start, sc.frame_end + 1):
    sc.frame_set(f); m = cam.matrix_world
    fwd = -(m.to_3x3().col[2])
    rows.append(dict(f=f, p=list(m.translation), d=list(fwd), lens=cam.data.lens))
json.dump(rows, open(out, "w"))
print("DUMPED", len(rows))
