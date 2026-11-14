"""Chat B low-res motion preview: build a set once, render every Nth frame of a move as EXR, grade each exactly like
the sheets (grade.grade_file), then encode an H.264 MP4 at 24 fps (frames held to keep timing).
  python b_anim.py <set> <move> --pct 44 --samples 8 --fps 8 --out DIR --mp4 out.mp4 [--label "3-10A ..."]
"""
import os, sys, json, importlib, subprocess, shutil
import bpy
import kit
from common import reset, camera

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
scene_name, move = sys.argv[1], sys.argv[2]
OUT = arg('--out', "/tmp/b_anim"); os.makedirs(OUT, exist_ok=True)
FPS = arg('--fps', 8); MP4 = arg('--mp4', os.path.join(OUT, f"{scene_name}_{move}.mp4"))
mod = importlib.import_module("sc_" + scene_name)
s = reset(res=kit.RES, samples=arg('--samples', 8), exposure=getattr(mod, "EXPOSURE", 0.0))
s.render.resolution_percentage = arg('--pct', 44)
s.cycles.max_bounces = getattr(mod, "BOUNCES", 6)
s.cycles.use_denoising = True
ctx = mod.build(getattr(mod, "VARIANT_FOR", {}).get(move, None))
spec = mod.MOVES[move]
cam = camera((0, 0, 0), (0, 1, 0), lens=35, dof_dist=3.0, fstop=spec.get("dof", 2.8) or 2.8)
cam.data.dof.use_dof = bool(spec.get("dof"))
ctx["cam"] = cam
if spec.get("title"):
    import title_card
    small, big, f_in, f_out = spec["title"]
    title_card.add_title(cam, small, big, f_in, f_out)
dur = getattr(mod, "DUR", {}).get(move, 5.0)
nfr = int(round(dur * 24))
step = max(1, int(round(24 / FPS)))
s.render.image_settings.file_format = 'OPEN_EXR'; s.render.image_settings.color_depth = '16'
s.render.use_compositing = False
frames = list(range(1, nfr + 1, step))
for i, f in enumerate(frames):
    t = (f - 1) / max(1, nfr - 1)
    s.frame_set(f)
    kit.apply_cam(cam, ctx, spec, t)
    bpy.context.view_layer.update()
    s.render.filepath = os.path.join(OUT, f"f{i:04d}.exr")
    bpy.ops.render.render(write_still=True)
    print(f"[b_anim] {i + 1}/{len(frames)}", flush=True)
json.dump(dict(exposure=s.view_settings.exposure, cine=json.loads(s.get("look_cine", "{}")), step=step, n=len(frames)),
          open(os.path.join(OUT, "plate.json"), "w"))
print("[b_anim] rendered", OUT, flush=True)
