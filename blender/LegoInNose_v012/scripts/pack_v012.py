"""Save the work file as the v012 package: textures packed, VO kept as the sidecar mp3 (relative path), compressed.
blender -b work.blend --python pack_v012.py -- <package.blend>"""
import bpy, sys, os
OUT = sys.argv[sys.argv.index("--") + 1]; d = os.path.dirname(OUT); vo = os.path.join(d, "LegoInNose_v012_VO.mp3")
for im in bpy.data.images:
    if im.source == "FILE" and not im.packed_file and im.filepath:
        try: im.pack()
        except Exception as e: print("PACK_FAIL", im.name, e)
for s in bpy.data.sounds:
    if s.packed_file: s.unpack(method="REMOVE")
    s.filepath = vo
sc = bpy.context.scene; sc.frame_start, sc.frame_end = 1, 2036
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True, relative_remap=True)
for s in bpy.data.sounds: s.filepath = "//LegoInNose_v012_VO.mp3"   # sidecar next to the .blend
bpy.ops.wm.save_mainfile(compress=True)
for s in bpy.data.sounds: print("VO", s.filepath, os.path.exists(bpy.path.abspath(s.filepath)))
print("SAVED", OUT, round(os.path.getsize(OUT) / 1e6, 1), "MB")
