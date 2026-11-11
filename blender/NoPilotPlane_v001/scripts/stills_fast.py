"""Review stills (same framing as pipeline/stills.py) with review-only speedups.
blender -b film.blend --python stills_fast.py -- <out_dir> <step_s> [start_s] [end_s]
- 270x480, 8 spp, max 4 bounces (review only; the farm settings in the .blend are untouched on disk)
- the cabin crowd is excluded when the camera is in the cockpit and cannot see the cabin (it re-deforms 49 rigs every frame)"""
import sys, os, bpy
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; STEP = float(a[1]); T0 = float(a[2]) if len(a) > 2 else 0.0; T1 = float(a[3]) if len(a) > 3 else 999
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene; fps = 60
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 270, 480, 100
sc.render.engine = "CYCLES"; sc.cycles.samples = 8; sc.cycles.use_denoising = True; sc.render.use_motion_blur = False
sc.cycles.max_bounces = 4; sc.cycles.transparent_max_bounces = 8; sc.cycles.texture_limit_render = "1024"; sc.render.use_persistent_data = True
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 85
lc = bpy.context.view_layer.layer_collection.children["PASSENGERS"]
i = round(T0 / STEP)
while True:
    f = sc.frame_start + round(i * STEP * fps)
    if f > sc.frame_end or i * STEP > T1 + 1e-6: break
    t = (f - 1) / fps
    lc.exclude = (16.6 < t < 64.0) or (69.6 < t)
    sc.frame_set(f); sc.render.filepath = os.path.join(OUT, "s%04d.jpg" % i)
    bpy.ops.render.render(write_still=True); i += 1
print("STILLS", i, OUT)
