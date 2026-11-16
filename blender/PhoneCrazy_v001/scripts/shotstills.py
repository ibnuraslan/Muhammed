"""blender -b anim.blend -P shotstills.py -- <outdir> <w> <h> <samples> <which: mid|fml> [shots comma]
Renders the first/mid/last (or mid) frame of each shot from work/shots.json."""
import bpy, sys, os, json
a = sys.argv[sys.argv.index("--") + 1:]; out, W, H, S, which = a[0], int(a[1]), int(a[2]), int(a[3]), a[4]
only = a[5].split(",") if len(a) > 5 else None
sh = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "work", "shots.json")))
sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = W, H; sc.render.resolution_percentage = 100
sc.cycles.samples = S; sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'; sc.render.use_motion_blur = False
sc.cycles.max_bounces = 4; sc.render.image_settings.file_format = 'JPEG'
os.makedirs(out, exist_ok=True)
for s in sh:
    if only and s["shot"] not in only: continue
    fr = [(s["frame"] + s["end"]) // 2] if which == "mid" else [s["frame"], (s["frame"] + s["end"]) // 2, s["end"]]
    for f in fr:
        sc.frame_set(f); sc.render.filepath = os.path.join(out, "%s_%05d.jpg" % (s["shot"], f)); bpy.ops.render.render(write_still=True)
