"""quick stills: blender -b in.blend --python still.py -- out_prefix frame 'x,y,z>tx,ty,tz>lens' ... [--res 270x480] [--samples 8]"""
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
res = (270, 480); spp = 8
if "--res" in a: i = a.index("--res"); res = tuple(int(v) for v in a[i + 1].split("x")); del a[i:i + 2]
if "--samples" in a: i = a.index("--samples"); spp = int(a[i + 1]); del a[i:i + 2]
pre, frame, views = a[0], int(a[1]), a[2:]
sc = bpy.context.scene; sc.frame_set(frame)
sc.render.engine = 'CYCLES'; sc.cycles.samples = spp; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
for i, v in enumerate(views):
    if v == "film":
        cam = sc.camera
    else:
        p, t, lens = v.split(">"); p = Vector(map(float, p.split(","))); t = Vector(map(float, t.split(",")))
        cd = bpy.data.cameras.new("tmp"); cam = bpy.data.objects.new("tmpcam", cd); sc.collection.objects.link(cam)
        cd.lens = float(lens); cd.dof.use_dof = False; cd.clip_start = 0.02
        cam.location = p; cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    sc.render.filepath = f"{pre}_{i}.png"; bpy.ops.render.render(write_still=True)
