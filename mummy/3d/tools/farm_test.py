"""Fresh-unzip test (FARM_DELIVERY_RULES.md 3, 7): open MASTER.blend from a folder made only by unzipping the
delivery zips, check every linked shot and image resolves, render frames (reduced size/samples for the test), and
render the same frames straight from the shot files so the colour can be compared.

    blender -b <dir>/MASTER.blend --python tools/farm_test.py -- <outdir> <frame> [<frame> ...]
"""
import os, sys
import bpy

args = sys.argv[sys.argv.index("--") + 1:]
OUT, FRAMES = os.path.abspath(args[0]), [int(a) for a in args[1:]]
os.makedirs(OUT, exist_ok=True)
m = bpy.data.scenes["MASTER"]
missing = [l.filepath for l in bpy.data.libraries if not os.path.exists(bpy.path.abspath(l.filepath))]
for im in bpy.data.images:
    if im.source == 'FILE' and not im.packed_file and im.filepath:
        p = bpy.path.abspath(im.filepath, library=im.library)
        if not os.path.exists(p):
            missing.append(p)
print("TEST camera:", m.camera.name if m.camera else None, "| frames", m.frame_start, m.frame_end,
      "| res", m.render.resolution_x, m.render.resolution_y, m.render.fps, "| samples", m.cycles.samples,
      "| view", m.view_settings.view_transform, m.view_settings.look, flush=True)
print("TEST libraries:", len(bpy.data.libraries), "| missing files:", len(missing), missing[:10], flush=True)
assert m.camera is not None and not missing
m.render.resolution_percentage = 25          # test size; the strips render with their own 64 spp
for f in FRAMES:
    m.frame_set(f)
    m.render.filepath = os.path.join(OUT, f"master_{f:05d}.png")
    bpy.ops.render.render(write_still=True)
    print("TEST rendered frame", f, flush=True)
print("TEST DONE", flush=True)
