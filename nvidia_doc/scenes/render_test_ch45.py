"""Render a few master frames at 100% / 32 samples (as the farm will) and report time per frame and peak RAM.
  python scenes/render_test_ch45.py c4_03_corp_lobby_busy c5_06_invest_filing_officer ...
Each named shot is rendered at its middle frame through the master's sequencer."""
import os, sys, json, time, resource
import bpy
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
tim = json.load(open(os.path.join(ROOT, "vo", "ch45_timing.json")))
start, f = {}, 1
for c in ("4", "5"):
    for sh in tim[c]:
        start[sh["name"]] = (f, sh["frames"]); f += sh["frames"]
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "out", "blend", "ch45", "nvidia_ch45.blend"))
m = bpy.data.scenes["NVIDIA_CH45"]
bpy.context.window.scene = m if bpy.context.window else None
outdir = os.path.join(ROOT, "out", "ch45_rendertest"); os.makedirs(outdir, exist_ok=True)
res = {}
for name in sys.argv[1:]:
    if name.startswith("f:"):
        fr = int(name[2:])
    else:
        f0, n = start[name]; fr = f0 + n // 2
    m.frame_set(fr); m.render.filepath = os.path.join(outdir, f"{name}_f{fr:05d}.png")
    t0 = time.time()
    bpy.ops.render.render(write_still=True, scene=m.name)
    dt = time.time() - t0
    res[name] = dict(frame=fr, seconds=round(dt, 1))
    print(f"[rtest] {name} frame {fr}: {dt:.1f} s, peak RSS {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6:.2f} GB", flush=True)
res["peak_rss_gb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 2)
json.dump(res, open(os.path.join(outdir, "render_test.json"), "w"), indent=1)
print("[rtest]", res, flush=True)
