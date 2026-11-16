"""blender -b X.blend -P views.py -- outdir 'name:x,y,z:tx,ty,tz:lens' ..."""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--")+1:]; out = a[0]; os.makedirs(out, exist_ok=True)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 8; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 360, 640
cam = bpy.data.objects.get("ViewCam") or bpy.data.objects.new("ViewCam", bpy.data.cameras.new("ViewCam"))
if cam.name not in sc.collection.objects: sc.collection.objects.link(cam)
sc.camera = cam; cam.data.clip_start = 0.05
for spec in a[1:]:
    n, l, t, lens = spec.split(":")
    cam.location = Vector(map(float, l.split(","))); tg = Vector(map(float, t.split(",")))
    cam.rotation_euler = (tg - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = float(lens)
    sc.render.filepath = os.path.join(out, n + ".jpg"); sc.render.image_settings.file_format = 'JPEG'
    bpy.ops.render.render(write_still=True)
