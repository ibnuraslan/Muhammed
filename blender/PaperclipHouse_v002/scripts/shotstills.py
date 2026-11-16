"""first/middle/last frame of each shot. blender -b anim.blend --python shotstills.py -- outdir W H samples [S01,S02]"""
import bpy, sys, json, os
a = sys.argv[sys.argv.index("--") + 1:]
out, W, H, spp = a[0], int(a[1]), int(a[2]), int(a[3])
only = set(a[4].split(",")) if len(a) > 4 else None
exec(open(os.path.dirname(os.path.abspath(__file__)) + "/common.py").read())
T = json.load(open(BUILD + "/timing_used.json"))
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = spp; sc.cycles.use_denoising = True
sc.render.resolution_x = W; sc.render.resolution_y = H; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'JPEG'; sc.render.use_stamp = False
os.makedirs(out, exist_ok=True)
for k in sorted(T):
    if only and k not in only: continue
    c = bpy.data.objects.get("CAM_" + k)
    if c is None: continue
    t0, t1 = T[k]
    for i, f in enumerate((t0, (t0 + t1 - 1) // 2, t1 - 1)):
        sc.frame_set(f); sc.camera = c
        sc.render.filepath = f"{out}/{k}_{i}_f{f:05d}.jpg"
        bpy.ops.render.render(write_still=True)
        print("STILL", k, i, f, flush=True)
