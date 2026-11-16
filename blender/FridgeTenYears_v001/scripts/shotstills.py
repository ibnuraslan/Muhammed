"""3 frames per shot (first, middle, last) -> one sheet.  blender -b film.blend --python shotstills.py -- outdir W H samples [S01,S02]"""
import bpy, sys, json, os
a = sys.argv[sys.argv.index("--") + 1:]; out, W, H, spp = a[0], int(a[1]), int(a[2]), int(a[3]); only = a[4].split(",") if len(a) > 4 else None
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene; S = json.loads(sc["SHOTS"])
sc.render.engine = 'CYCLES'; sc.cycles.samples = spp; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.render.resolution_x = W; sc.render.resolution_y = H; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 88
for k, (f0, f1) in sorted(S.items()):
    if only and k not in only: continue
    for tag, f in (("a", f0), ("b", (f0 + f1) // 2), ("c", f1)):
        sc.frame_set(f); sc.camera = bpy.data.objects["CAM_" + k]
        sc.render.filepath = "%s/%s_%s_%04d.jpg" % (out, k, tag, f); bpy.ops.render.render(write_still=True)
        print("STILL", k, tag, f)
