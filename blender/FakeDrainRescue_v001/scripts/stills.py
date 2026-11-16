"""Render first/mid/last (or chosen) frames of every shot. blender -b film.blend --python stills.py -- outdir pct samples which [S01,S02]
which: fml (first, mid, last) or m (mid only)"""
import bpy, sys, json, os
a = sys.argv[sys.argv.index("--") + 1:]; od, pct, spp, which = a[0], int(a[1]), int(a[2]), a[3]
only = set(a[4].split(",")) if len(a) > 4 else None
SH = json.load(open("/home/user/Muhammed/blender/FakeDrainRescue_v001/shots.json")); os.makedirs(od, exist_ok=True)
sc = bpy.context.scene; sc.render.resolution_percentage = pct; sc.cycles.samples = spp; sc.render.image_settings.file_format = 'JPEG'
for s in SH:
    if only and s["id"] not in only: continue
    fr = {"f": s["f0"], "m": (s["f0"] + s["f1"]) // 2, "l": s["f1"]}
    for k in which:
        f = fr[k]; sc.frame_set(f); sc.camera = bpy.data.objects["CAM_" + s["id"]]
        sc.render.filepath = "%s/%s_%s_%04d.jpg" % (od, s["id"], {"f": "1first", "m": "2mid", "l": "3last"}[k], f); bpy.ops.render.render(write_still=True)
