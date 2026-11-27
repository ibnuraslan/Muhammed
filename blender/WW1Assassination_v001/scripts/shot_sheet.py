# first/middle/last frame of every marker shot (or given frames) at 270x480, 4 spp + OIDN
# blender -b film.blend --python shot_sheet.py -- OUTDIR [res_x res_y] [only=S03,S05]
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]; out = a[0]
rx, ry = (int(a[1]), int(a[2])) if len(a) > 2 else (270, 480)
only = a[3].split(",") if len(a) > 3 else None
sc = bpy.context.scene; r = sc.render
r.resolution_x, r.resolution_y, r.resolution_percentage = rx, ry, 100
sc.cycles.samples = 4; sc.cycles.use_denoising = True; r.use_simplify = True; r.simplify_subdivision_render = 0
r.image_settings.file_format = 'JPEG'
ms = sorted(sc.timeline_markers, key=lambda m: m.frame)
for i, m in enumerate(ms):
    if only and not any(m.name.startswith(x) for x in only): continue
    f0 = m.frame; f1 = (ms[i + 1].frame - 1) if i + 1 < len(ms) else sc.frame_end
    for tag, f in (("a", f0), ("b", (f0 + f1) // 2), ("c", f1)):
        sc.frame_set(f); sc.camera = m.camera
        r.filepath = os.path.join(out, "%s_%s_f%04d.jpg" % (m.name.split("_")[0], tag, f)); bpy.ops.render.render(write_still=True)
print("SHEET_DONE")
