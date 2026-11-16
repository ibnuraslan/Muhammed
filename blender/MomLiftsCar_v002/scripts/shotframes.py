"""blender -b f --python shotframes.py -- outdir width samples  -> first/mid/last frame of every marker shot"""
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]; out = a[0]; w = int(a[1]); smp = int(a[2]); only = a[3].split(",") if len(a) > 3 else None
os.makedirs(out, exist_ok=True); sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = w, round(w * 16 / 9); sc.cycles.samples = smp; sc.cycles.use_denoising = True
sc.render.image_settings.file_format = 'JPEG'; sc.render.use_stamp = False
ms = sorted([m for m in sc.timeline_markers if m.camera], key=lambda m: m.frame)
for i, m in enumerate(ms):
    if only and m.name not in only: continue
    f1 = (ms[i + 1].frame - 1) if i + 1 < len(ms) else sc.frame_end
    for tag, f in (("a", m.frame), ("b", (m.frame + f1) // 2), ("c", f1)):
        sc.frame_set(f); sc.camera = m.camera
        sc.render.filepath = os.path.join(out, "%s_%s_f%04d.jpg" % (m.name, tag, f)); bpy.ops.render.render(write_still=True)
