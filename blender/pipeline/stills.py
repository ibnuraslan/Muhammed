"""Low-res review stills: one frame every <step_s> seconds (default 1.0; use 0.2 for polish sheets).
blender -b film.blend --python stills.py -- <out_dir> [step_s] [width]
Then: python3 -I contact_sheet.py <out_dir> sheet.jpg 10 <1/step_s>"""
import sys, os
import bpy
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; STEP = float(a[1]) if len(a) > 1 else 1.0; W = int(a[2]) if len(a) > 2 else 270
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene; fps = sc.render.fps / sc.render.fps_base
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, round(W * 16 / 9), 100
sc.render.engine = "CYCLES"; sc.cycles.samples = 8; sc.cycles.use_denoising = True
sc.render.use_motion_blur = False; sc.cycles.texture_limit_render = "1024"
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 85
i = 0
while True:
    f = sc.frame_start + round(i * STEP * fps)
    if f > sc.frame_end: break
    sc.frame_set(f); sc.render.filepath = os.path.join(OUT, "s%04d.jpg" % i)
    bpy.ops.render.render(write_still=True); i += 1
print("STILLS", i, OUT)
