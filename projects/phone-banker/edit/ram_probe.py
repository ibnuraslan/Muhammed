"""Estimate the RAM the farm needs to open the master: build a copy where only the shots of the given parts are real
(the rest placeholders), open it in a fresh process, record peak RSS after open and after rendering one frame.
  python edit/ram_probe.py prep <iso_copy.blend> <part> [part ...]   -> out/blend/film/_ram_probe.blend
  python edit/ram_probe.py open [frame]                               -> prints [ram] lines, deletes the probe file"""
import os, sys, json, resource
import bpy
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
PROBE = os.path.join(ROOT, "out", "blend", "film", "_ram_probe.blend")
rss = lambda: resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024
if sys.argv[1] == "prep":
    bpy.ops.wm.open_mainfile(filepath=sys.argv[2])
    keep = set(sys.argv[3:]); n = 0
    for lib in bpy.data.libraries:
        part = os.path.basename(os.path.dirname(lib.filepath))
        if part not in keep:
            lib.filepath = "//../_placeholders/" + os.path.basename(lib.filepath)
        else:
            n += 1
    bpy.ops.wm.save_as_mainfile(filepath=PROBE, relative_remap=False)
    print(f"[ram] probe with {n} real shots", flush=True)
else:
    r0 = rss()
    bpy.ops.wm.open_mainfile(filepath=PROBE)
    real = [l for l in bpy.data.libraries if "_placeholders" not in l.filepath]
    print(f"[ram] {len(real)} real shots: before open {r0} MB, peak after open {rss()} MB", flush=True)
    if len(sys.argv) > 2:
        m = bpy.context.scene; m.render.resolution_percentage = 100
        m.frame_set(int(sys.argv[2])); m.render.filepath = os.path.join(ROOT, "out", "verify", "ram_probe_frame.png")
        bpy.ops.render.render(write_still=True)
        print(f"[ram] peak after rendering frame {sys.argv[2]} at 100%: {rss()} MB", flush=True)
    os.remove(PROBE)
