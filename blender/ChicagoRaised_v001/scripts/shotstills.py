"""One still per shot: blender -b film.blend -P shotstills.py -- out_dir W samples frac [frac...]  (frac of the shot: 0=first frame, 1=last)"""
import bpy, sys, os, json
a = sys.argv[sys.argv.index("--") + 1:]; out, W, spp = a[0], int(a[1]), int(a[2]); fr = [float(x) for x in a[3:]] or [0.5]
os.makedirs(out, exist_ok=True)
shots = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "work", "shots.json")))
sc = bpy.context.scene; sc.render.resolution_x = W; sc.render.resolution_y = round(W * 16 / 9); sc.render.resolution_percentage = 100
sc.cycles.samples = spp; sc.cycles.use_denoising = True; sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 88
sc.cycles.texture_limit_render = '1024'
ONLY = [x for x in os.environ.get("SHOTS", "").split(",") if x]
for s in shots:
    if ONLY and s["shot"] not in ONLY: continue
    for x in fr:
        f = s["frame"] + round((s["end"] - s["frame"]) * x)
        sc.frame_set(f); sc.render.filepath = os.path.join(out, "%s_%04d.jpg" % (s["shot"].replace("S", "S%02d" % int(s["shot"][1:]))[:3], f))
        bpy.ops.render.render(write_still=True)
