"""Copy a shot .blend with all its images packed (self-contained):  blender -b <shot.blend> --python pack_shots.py -- <out.blend>"""
import sys, os, bpy
out = sys.argv[sys.argv.index("--") + 1]
bpy.ops.file.pack_all()
r = bpy.context.scene.render
sid = os.path.splitext(os.path.basename(out))[0]
r.filepath = f"//../frames/{sid}/{sid}_"
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, relative_remap=True, copy=True)
print("PACKED", out, round(os.path.getsize(out) / 1e6, 1), "MB", flush=True)
