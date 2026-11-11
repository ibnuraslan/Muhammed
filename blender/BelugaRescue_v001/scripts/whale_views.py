"""Beauty check of the beluga: three views at one frame.  blender -b film.blend --python whale_views.py -- out.jpg frame"""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; F = int(a[1])
sc = bpy.context.scene; sc.frame_set(F)
BR = bpy.data.objects["Beluga_Rig"]; M = BR.matrix_world
head = M @ Vector((0, -1.45, 0.1)); mid = M @ Vector((0, 0.0, 0.0))
cd = bpy.data.cameras.new("QW"); cam = bpy.data.objects.new("QW", cd); sc.collection.objects.link(cam); sc.camera = cam
for o in bpy.data.objects:
    if o.name == "Explainer_Card": o.animation_data_clear(); o.hide_render = True
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 12; sc.render.use_motion_blur = False
sc.render.image_settings.file_format = "JPEG"
R3 = M.to_3x3()
views = [(head, R3 @ Vector((1.5, -0.4, 0.25)), 38), (head, R3 @ Vector((0.7, -1.5, 0.3)), 42), (mid, R3 @ Vector((4.2, -0.8, 1.0)), 26)]
paths = []
for k, (t, off, lens) in enumerate(views):
    cam.location = t + off; cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler(); cd.lens = lens
    p = OUT + "_%d.jpg" % k; sc.render.filepath = p; bpy.ops.render.render(write_still=True); paths.append(p)
print("WHALE_VIEWS", paths)
