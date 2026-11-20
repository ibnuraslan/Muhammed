"""Pack one exported shot's textures into it and save it compressed:  blender -b <in.blend> --python pack_shot.py -- <out.blend>"""
import bpy, sys, os
out = os.path.abspath(sys.argv[sys.argv.index("--") + 1:][0])
bpy.ops.file.pack_all()
sc = bpy.context.scene
sc.render.filepath = "//../frames/" + os.path.splitext(os.path.basename(out))[0] + "/" + os.path.splitext(os.path.basename(out))[0] + "_"
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, relative_remap=True)
print("PACKED", out, round(os.path.getsize(out) / 1e6, 1), "MB", flush=True)
