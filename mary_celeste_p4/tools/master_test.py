"""Render frames from the MASTER scene (sequencer of Scene strips) at low resolution, as the farm would render it.
   blender -b <MASTER.blend> --python tools/master_test.py -- OUTDIR frame [frame ...]"""
import sys, os, bpy
a = sys.argv[sys.argv.index("--") + 1:]; out = a[0]; os.makedirs(out, exist_ok=True)
m = bpy.data.scenes["MASTER"]; bpy.context.window_manager.windows[0].scene = m if bpy.context.window_manager.windows else None
print("SCENE", bpy.context.scene.name, m.frame_start, m.frame_end, m.render.resolution_x, m.render.resolution_y, m.render.use_sequencer)
missing = [i.name for i in bpy.data.images if i.source == 'FILE' and not i.packed_file]
print("UNPACKED", missing)
m.render.resolution_percentage = 25
for sc in bpy.data.scenes:
    sc.cycles.samples = 16
for f in [int(x) for x in a[1:]]:
    m.frame_set(f); m.render.filepath = os.path.join(out, f"MASTER_{f:04d}.png")
    bpy.ops.render.render(write_still=True, scene="MASTER")
    print("MASTERFRAME", f, flush=True)
