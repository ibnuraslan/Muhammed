"""First / middle / last frame of every shot (marker-bound cameras). blender -b x.blend --python shot_frames.py -- out_dir W [samples] [shots]"""
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]; O, W = a[0], int(a[1]); SMP = int(a[2]) if len(a) > 2 else 8
ONLY = a[3].split(",") if len(a) > 3 else None
os.makedirs(O, exist_ok=True); sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, round(W * 16 / 9), 100
sc.render.engine = 'CYCLES'; sc.cycles.samples = SMP; sc.cycles.use_denoising = True; sc.render.use_motion_blur = False
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 88
mk = sorted(sc.timeline_markers, key=lambda m: m.frame)
for i, m in enumerate(mk):
    if ONLY and m.name not in ONLY: continue
    f0 = m.frame; f1 = (mk[i + 1].frame - 1) if i + 1 < len(mk) else sc.frame_end
    for tag, f in (("a", f0), ("b", (f0 + f1) // 2), ("c", f1)):
        sc.frame_set(f); sc.camera = m.camera
        sc.render.filepath = os.path.join(O, f"{m.name}_{tag}_{f:05d}.jpg"); bpy.ops.render.render(write_still=True)
print("SHOTFRAMES done")
