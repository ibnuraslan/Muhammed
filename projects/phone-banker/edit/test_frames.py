"""Render a few frames of the master at 25% through its real links, without loading all 71 shots:
  python edit/test_frames.py prep <iso_copy.blend> f1 f2 f3  -> out/blend/film/_test_frames.blend (only the shots under
         those frames point at their real files, the rest at the placeholders)
  python edit/test_frames.py render f1 f2 f3                 -> out/verify/master_f<frame>.png, then deletes the test file
"""
import os, sys, json
import bpy
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
FILMDIR = os.path.join(ROOT, "out", "blend", "film"); TEST = os.path.join(FILMDIR, "_test_frames.blend")
EDL = json.load(open(os.path.join(HERE, "film_edl.json")))
frames = [int(x) for x in sys.argv[3 if sys.argv[1] == "prep" else 2:]]
if sys.argv[1] == "prep":
    bpy.ops.wm.open_mainfile(filepath=sys.argv[2])
    keep = {n for f0, f1, n in EDL["shots"] for f in frames if f0 <= f < f1}
    for lib in bpy.data.libraries:
        n = os.path.splitext(os.path.basename(lib.filepath))[0]
        if n not in keep:
            lib.filepath = "//../_placeholders/" + n + ".blend"
    bpy.ops.wm.save_as_mainfile(filepath=TEST, relative_remap=False)
    print("[test] real shots:", sorted(keep))
else:
    bpy.ops.wm.open_mainfile(filepath=TEST)
    m = bpy.context.scene
    m.render.resolution_percentage = 25
    out = os.path.join(ROOT, "out", "verify"); os.makedirs(out, exist_ok=True)
    for f in frames:
        m.frame_set(f); m.render.filepath = os.path.join(out, f"master_f{f:05d}.png")
        bpy.ops.render.render(write_still=True); print("[test] rendered", f, flush=True)
    os.remove(TEST)
