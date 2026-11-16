"""First/middle/last frame of every shot. blender -b film.blend -P sheet3.py -- outdir [width] [SHOT,SHOT]"""
import bpy, sys, os, json
a = sys.argv[sys.argv.index("--")+1:]; out = a[0]; W = int(a[1]) if len(a) > 1 else 540
only = a[2].split(",") if len(a) > 2 else None
os.makedirs(out, exist_ok=True); sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = 8; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, W * 16 // 9, 100
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 88; sc.cycles.texture_limit_render = '1024'
shots = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shots.json")))
for s in shots:
    if only and s["name"].split("_")[0] not in only: continue
    for tag, f in (("a", s["f0"]), ("b", (s["f0"] + s["f1"]) // 2), ("c", s["f1"])):
        sc.frame_set(f); sc.render.filepath = os.path.join(out, "%s_%s_%05d.jpg" % (s["name"], tag, f))
        bpy.ops.render.render(write_still=True)
