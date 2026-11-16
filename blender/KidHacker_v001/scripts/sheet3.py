"""blender -b p1.blend --python sheet3.py -- outdir width samples [S01,S02]: first/middle/last frame of every shot (marker cameras)"""
import bpy, sys, os, json
a = sys.argv[sys.argv.index("--") + 1:]; out = a[0]; w = int(a[1]); smp = int(a[2]); only = set(a[3].split(",")) if len(a) > 3 else None
os.makedirs(out, exist_ok=True); sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = w, round(w * 16 / 9); sc.cycles.samples = smp; sc.cycles.use_denoising = True
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 88
J = json.load(open("/tmp/claude-0/kh/work/shots.json"))
for s in J["shots"]:
    if only and s["shot"] not in only: continue
    f0, f1 = s["f0"], s["f1"]
    for tag, f in (("a", f0), ("b", (f0 + f1) // 2), ("c", f1)):
        sc.frame_set(f); sc.camera = bpy.data.objects[s["cam"]]
        sc.render.filepath = os.path.join(out, "%s_%s_f%04d.jpg" % (s["shot"], tag, f)); bpy.ops.render.render(write_still=True)
