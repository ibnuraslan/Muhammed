"""Review stills at given frames.  blender -b anim.blend --python frames.py -- <out_dir> f1,f2,... [width]"""
import sys, os, bpy
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; FR = [int(x) for x in a[1].split(",")]; W = int(a[2]) if len(a) > 2 else 270
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, round(W * 16 / 9), 100
sc.cycles.samples = 8; sc.cycles.use_denoising = True; sc.render.use_motion_blur = False; sc.cycles.texture_limit_render = "1024"
sc.render.image_settings.file_format = "JPEG"
for f in FR:
    sc.frame_set(f); sc.render.filepath = os.path.join(OUT, "f%04d.jpg" % f); bpy.ops.render.render(write_still=True)
