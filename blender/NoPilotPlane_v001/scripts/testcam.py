"""blender -b X.blend --python testcam.py -- out_prefix frame 'x,y,z:tx,ty,tz:lens' ..."""
import sys, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
sc = bpy.context.scene; sc.frame_set(int(a[1]))
cd = bpy.data.cameras.new("TC"); cd.clip_start = 0.02; cd.clip_end = 90000
c = bpy.data.objects.new("TC", cd); sc.collection.objects.link(c); sc.camera = c
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.render.engine = "CYCLES"; sc.cycles.samples = 8; sc.cycles.use_denoising = True
sc.render.image_settings.file_format = "JPEG"
for i, s in enumerate(a[2:]):
    p, t, l = s.split(":"); p = Vector(map(float, p.split(","))); t = Vector(map(float, t.split(",")))
    c.location = p; c.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler(); cd.lens = float(l)
    sc.render.filepath = "%s_%d.jpg" % (a[0], i); bpy.ops.render.render(write_still=True)
