"""Quick test views. blender -b file.blend --python views.py -- out_dir 'x,y,z;tx,ty,tz;lens;frame' ..."""
import sys, os, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 270, 480, 100
sc.cycles.samples = 8; sc.render.use_motion_blur = False; sc.render.image_settings.file_format = 'JPEG'
cd = bpy.data.cameras.new("VIEW"); cam = bpy.data.objects.new("VIEW", cd); sc.collection.objects.link(cam); sc.camera = cam; cd.clip_start = 0.01
if os.environ.get("BRIGHT"):
    L = bpy.data.lights.new("TL", "POINT"); L.energy = 300; lo = bpy.data.objects.new("TL", L); sc.collection.objects.link(lo)
for i, v in enumerate(a[1:]):
    p, t, l, f = v.split(";"); p = Vector(map(float, p.split(","))); t = Vector(map(float, t.split(",")))
    sc.frame_set(int(f)); cam.location = p
    if os.environ.get("BRIGHT"): lo.location = p + Vector((0, 0, 0.3))
    cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler(); cd.lens = float(l)
    sc.render.filepath = os.path.join(OUT, "v%02d.jpg" % i); bpy.ops.render.render(write_still=True)
