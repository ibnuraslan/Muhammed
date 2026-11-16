"""Render the first, middle and last frame of every shot (Cycles 8 samples), for the P1 3-frame sheet.
blender -b film.blend --python shot_frames.py -- <layout.json> <out_dir> [width=540] [samples=8] [only=S01,S02]"""
import bpy, sys, json, os
a = sys.argv[sys.argv.index("--") + 1:]
L = json.load(open(a[0]))["shots"]; OUT = a[1]; W = int(a[2]) if len(a) > 2 else 540; SMP = int(a[3]) if len(a) > 3 else 8
ONLY = a[4].split(",") if len(a) > 4 and a[4] else None
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene; r = sc.render
r.resolution_x, r.resolution_y, r.resolution_percentage = W, round(W * 16 / 9), 100
sc.cycles.samples = SMP; sc.cycles.use_denoising = True; r.use_simplify = True; r.simplify_subdivision_render = 1
r.image_settings.file_format = 'JPEG'; r.image_settings.quality = 88
for sid, (f0, f1) in L.items():
    if ONLY and sid not in ONLY: continue
    for tag, f in (("a", f0), ("b", (f0 + f1) // 2), ("c", f1)):
        sc.frame_set(f); r.filepath = os.path.join(OUT, "%s_%s_%05d.jpg" % (sid, tag, f))
        bpy.ops.render.render(write_still=True)
print("SHOTFRAMES_DONE")
