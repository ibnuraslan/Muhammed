"""first/mid/last frame of every shot. blender -b f.blend --python shotstills.py -- out_dir width samples [shots] [fracs]"""
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; W = int(a[1]); S = int(a[2])
only = a[3].split(",") if len(a) > 3 and a[3] else None
fr = [float(x) for x in a[4].split(",")] if len(a) > 4 else [0.0, 0.5, 1.0]
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
sc.render.resolution_x = W; sc.render.resolution_y = round(W * 16 / 9); sc.render.resolution_percentage = 100
sc.cycles.samples = S; sc.cycles.use_denoising = True; sc.render.image_settings.file_format = "JPEG"
ms = sorted(sc.timeline_markers, key=lambda m: m.frame)
for i, m in enumerate(ms):
    if only and m.name not in only: continue
    end = (ms[i + 1].frame if i + 1 < len(ms) else sc.frame_end + 1) - 1
    for k, u in enumerate(fr):
        f = int(round(m.frame + u * (end - m.frame)))
        sc.frame_set(f); sc.camera = m.camera; sc.render.filepath = os.path.join(OUT, "%s_%d_f%04d.jpg" % (m.name, k, f))
        bpy.ops.render.render(write_still=True)
print("DONE")
