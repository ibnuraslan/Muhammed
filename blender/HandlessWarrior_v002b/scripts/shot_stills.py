"""Per-shot review stills: first / middle / last frame of every shot (or 'mid' only).
blender -b film.blend --python shot_stills.py -- <out_dir> [first,mid,last] [width] [samples] [shots e.g. S01,S05]
then python3 sheet.py <out_dir> <sheet.jpg>"""
import sys, os, json
import bpy
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; WHICH = (a[1] if len(a) > 1 else "first,mid,last").split(","); W = int(a[2]) if len(a) > 2 else 270
SMP = int(a[3]) if len(a) > 3 else 8; ONLY = a[4].split(",") if len(a) > 4 and a[4] else None
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, round(W * 16 / 9), 100
sc.render.engine = "CYCLES"; sc.cycles.samples = SMP; sc.cycles.use_denoising = True
sc.render.use_simplify = True; sc.render.simplify_subdivision_render = 0
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 88
for name, f0, f1 in json.loads(sc["SHOTS_JSON"]):
    if ONLY and name not in ONLY: continue
    fr = {"first": f0, "mid": (f0 + f1) // 2, "last": f1}
    for k in WHICH:
        f = fr[k] if k in fr else int(k)
        sc.frame_set(f); sc.render.filepath = os.path.join(OUT, "%s_%s_f%04d.jpg" % (name, k, f))
        bpy.ops.render.render(write_still=True)
print("SHOT_STILLS_DONE")
