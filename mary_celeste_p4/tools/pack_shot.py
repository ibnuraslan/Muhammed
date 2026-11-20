"""Re-save a farm shot .blend fully self-contained: textures and fonts packed, compressed.
   blender -b <pkg>/shots/S05.blend --python tools/pack_shot.py -- <out.blend>"""
import sys, os, bpy
out = sys.argv[sys.argv.index("--") + 1]
bpy.ops.file.pack_all()
for f in bpy.data.fonts:
    if f.filepath and f.filepath != "<builtin>" and not f.packed_file:
        f.pack()
un = [i.name for i in bpy.data.images if i.source == 'FILE' and not i.packed_file]
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("PACKED", os.path.basename(out), round(os.path.getsize(out) / 1e6, 1), "MB unpacked:", un, flush=True)
