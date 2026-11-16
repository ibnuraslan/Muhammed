"""Render first/middle/last frame of every shot (markers). args: out_dir width samples [only_sids,comma]"""
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]; out = a[0]; W = int(a[1]); smp = int(a[2]); only = a[3].split(",") if len(a) > 3 and a[3] else None
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene; r = sc.render
r.resolution_x = W; r.resolution_y = round(W * 16 / 9); r.resolution_percentage = 100
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = smp; sc.cycles.use_denoising = True; r.use_simplify = True; r.simplify_subdivision_render = 1
sc.cycles.texture_limit_render = '1024'; r.image_settings.file_format = 'JPEG'
mk = sorted(sc.timeline_markers, key=lambda m: m.frame)
for i, m in enumerate(mk):
    sid = m.name[1:]
    if only and sid not in only: continue
    f0 = m.frame; f1 = (mk[i + 1].frame - 1) if i + 1 < len(mk) else sc.frame_end
    for j, f in enumerate([f0, (f0 + f1) // 2, f1]):
        sc.frame_set(f); sc.camera = m.camera
        r.filepath = f"{out}/{sid}_{j}_f{f:04d}.jpg"; bpy.ops.render.render(write_still=True)
print("DONE")
