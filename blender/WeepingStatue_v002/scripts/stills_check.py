"""Render given frames: blender -b f.blend --python stills_check.py -- OUT_DIR res_x res_y samples shots.json mode(fml|mid)"""
import bpy, sys, json, os
a = sys.argv[sys.argv.index("--") + 1:]
out, rx, ry, spp, shots, mode = a[0], int(a[1]), int(a[2]), int(a[3]), json.load(open(a[4])), a[5]
sc = bpy.context.scene; r = sc.render
r.resolution_x, r.resolution_y, r.resolution_percentage = rx, ry, 100
sc.cycles.samples = spp; sc.cycles.use_denoising = True; r.use_simplify = True; r.simplify_subdivision_render = 0
r.image_settings.file_format = 'JPEG'
os.makedirs(out, exist_ok=True)
for k in sorted(shots):
    f0, f1 = shots[k]
    frames = [(f0, "a"), ((f0 + f1) // 2, "m"), (f1, "z")] if mode == "fml" else [((f0 + f1) // 2, "m")]
    for f, t in frames:
        sc.frame_set(f); r.filepath = os.path.join(out, "%s_%s_%04d.jpg" % (k, t, f)); bpy.ops.render.render(write_still=True)
