"""blender -b f --python frames.py -- outdir f1,f2,... [w]"""
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]; out = a[0]; fr = [int(x) for x in a[1].split(",")]; w = int(a[2]) if len(a) > 2 else 270
os.makedirs(out, exist_ok=True); sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = w, round(w * 16 / 9); sc.cycles.samples = 8; sc.cycles.use_denoising = True
sc.render.image_settings.file_format = 'JPEG'
for f in fr:
    sc.frame_set(f)
    ms = [m for m in sc.timeline_markers if m.frame <= f and m.camera]
    if ms: sc.camera = max(ms, key=lambda m: m.frame).camera
    sc.render.filepath = os.path.join(out, "f%04d.jpg" % f); bpy.ops.render.render(write_still=True)
