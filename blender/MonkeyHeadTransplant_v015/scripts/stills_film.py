"""render film-camera stills at given frames: blender -b film.blend --python stills_film.py -- outdir f1,f2,... [WxH] [spp]"""
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]
out = a[0]; frames = [int(x) for x in a[1].split(",")]
res = tuple(int(v) for v in a[2].split("x")) if len(a) > 2 else (270, 480); spp = int(a[3]) if len(a) > 3 else 6
sc = bpy.context.scene; r = sc.render
r.engine = 'CYCLES'; sc.cycles.samples = spp; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
r.resolution_x, r.resolution_y = res; r.resolution_percentage = 100
r.use_simplify = True; r.simplify_subdivision_render = 0
r.use_stamp = True
for k in ("date", "time", "render_time", "camera", "lens", "scene", "filename", "memory", "hostname", "marker", "sequencer_strip", "note", "frame_range"):
    if hasattr(r, "use_stamp_" + k): setattr(r, "use_stamp_" + k, False)
r.use_stamp_frame = True; r.stamp_font_size = 12
os.makedirs(out, exist_ok=True)
for f in frames:
    sc.frame_set(f); r.filepath = os.path.join(out, "s_%04d.png" % f); bpy.ops.render.render(write_still=True)
