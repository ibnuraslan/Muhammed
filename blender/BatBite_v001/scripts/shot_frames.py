"""render first/last (and mid) frame of every shot through its own camera.
blender -b f.blend --python shot_frames.py -- OUTDIR W SAMPLES [mid|ends]"""
import bpy, sys, os
a = sys.argv[sys.argv.index("--")+1:]; OUT, W, SMP, MODE = a[0], int(a[1]), int(a[2]), a[3]
os.makedirs(OUT, exist_ok=True); sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = W, W * 16 // 9; sc.render.resolution_percentage = 100
sc.cycles.samples = SMP; sc.cycles.use_denoising = True; sc.render.image_settings.file_format = 'JPEG'
sc.render.use_stamp = True; sc.render.use_stamp_frame = True; sc.render.use_stamp_marker = True; sc.render.stamp_font_size = max(10, W // 30)
for k in ("date","time","render_time","camera","lens","scene","filename","memory"): setattr(sc.render, "use_stamp_"+k, False)
mk = sorted(sc.timeline_markers, key=lambda m: m.frame)
for i, m in enumerate(mk):
    f0 = m.frame; f1 = (mk[i+1].frame - 1) if i + 1 < len(mk) else sc.frame_end
    frames = [(f0 + f1) // 2] if MODE == "mid" else [f0, f1]
    for f in frames:
        sc.frame_set(f); sc.camera = m.camera
        sc.render.filepath = os.path.join(OUT, "%s_%04d.jpg" % (m.name, f)); bpy.ops.render.render(write_still=True)
