"""Open a farm .blend as the farm would and render frames at low resolution (sanity check of the package).
   blender -b <pkg>/shots/S05.blend --python tools/farm_test.py -- OUTDIR [frames...]"""
import sys, os, bpy
a = sys.argv[sys.argv.index("--") + 1:]; out = a[0]; os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
frames = [int(x) for x in a[1:]] or [sc.frame_start, (sc.frame_start + sc.frame_end) // 2, sc.frame_end]
missing = [i.filepath for i in bpy.data.images if i.source == 'FILE' and not i.packed_file and not os.path.exists(bpy.path.abspath(i.filepath))]
print("MISSING", missing)
sc.render.resolution_percentage = 25; sc.cycles.samples = 16
for f in frames:
    sc.frame_set(f); sc.render.filepath = os.path.join(out, f"{os.path.splitext(os.path.basename(bpy.data.filepath))[0]}_{f:04d}.png")
    bpy.ops.render.render(write_still=True)
print("FARMTEST_OK", frames, sc.frame_start, sc.frame_end, sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples)
