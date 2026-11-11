"""blender -b scene.blend --python probe_views.py -- outdir  (quick set check renders)"""
import bpy, sys, os
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]; os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
cd = bpy.data.cameras.new("probe"); cd.lens = 24; cam = bpy.data.objects.new("probe", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.render.use_motion_blur = False
sc.render.image_settings.file_format = "JPEG"
VIEWS = [((-1.0, 8.0, 1.6), (-2.0, 25.0, 1.4)), ((-1.0, 20.0, 1.7), (9.0, 26.0, 2.5)), ((14.0, 14.0, 12.0), (0, 60, 0)),
         ((21.5, 34.0, 1.8), (21.5, 43.5, 1.0)), ((21.0, 41.0, 1.6), (21.5, 44.0, 0.9)), ((2.0, 50.0, 3.0), (-8.0, 57.0, 3.0)),
         ((-8.0, 55.0, 1.7), (-16.0, 58.0, 1.4)), ((0.0, 70.0, 6.0), (0.0, 0.0, 1.0))]
for i, (c, a) in enumerate(VIEWS):
    cam.location = c; d = Vector(a) - Vector(c); cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, "v%02d.jpg" % i); bpy.ops.render.render(write_still=True)
