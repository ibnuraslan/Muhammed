"""render chosen frames small (review only).  blender -b f.blend --python frames.py -- OUTDIR W H SAMPLES f1,f2,..."""
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]; out, W, H, S, fr = a[0], int(a[1]), int(a[2]), int(a[3]), [int(x) for x in a[4].split(",")]
sc = bpy.context.scene; r = sc.render; r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100
sc.cycles.samples = S; sc.cycles.use_denoising = True; r.use_simplify = True; r.simplify_subdivision_render = 1
r.image_settings.file_format = 'JPEG'
import os
from mathutils import Vector
if os.environ.get("DBG"):   # debug camera: DBG="cx,cy,cz,ax,ay,az,lens"
    v = [float(x) for x in os.environ["DBG"].split(",")]
    cam = bpy.data.objects.new("DBG", bpy.data.cameras.new("DBG")); sc.collection.objects.link(cam)
    cam.location = v[:3]; cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = (Vector(v[3:6]) - Vector(v[:3])).to_track_quat('-Z', 'Y'); cam.data.lens = v[6]
    for m in list(sc.timeline_markers): m.camera = None
    sc.camera = cam
for f in fr:
    sc.frame_set(f); r.filepath = "%s/f%05d.jpg" % (out, f); bpy.ops.render.render(write_still=True)
