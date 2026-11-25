"""quick look stills: blender -b in.blend --python stills.py -- outprefix 'f:cx,cy,cz:tx,ty,tz:lens' ..."""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; out = a[0]
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 540, 960; sc.cycles.samples = 20; sc.cycles.use_adaptive_sampling = True
cam = bpy.data.cameras.new("QC"); co = bpy.data.objects.new("QC", cam); sc.collection.objects.link(co); sc.camera = co
e = bpy.data.objects.new("QCT", None); sc.collection.objects.link(e)
t = co.constraints.new('TRACK_TO'); t.target = e; t.track_axis = 'TRACK_NEGATIVE_Z'; t.up_axis = 'UP_Y'
cam.clip_start = 0.005
for i, spec in enumerate(a[1:]):
    f, c, tg, lens = spec.split(":")
    sc.frame_set(int(f)); co.location = Vector(map(float, c.split(","))); e.location = Vector(map(float, tg.split(","))); cam.lens = float(lens)
    sc.render.filepath = "%s_%02d_f%s.png" % (out, i, f); bpy.ops.render.render(write_still=True)
