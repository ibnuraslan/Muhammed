"""Close views of the mouth on the ankle from four sides. blender -b film.blend --python grip_views.py -- out_dir f1 f2 ..."""
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene; D = bpy.data.objects["Diver"]
cd = bpy.data.cameras.new("QG"); cam = bpy.data.objects.new("QG", cd); sc.collection.objects.link(cam); cd.clip_start = 0.01; cd.lens = 40
sc.camera = cam
for o in bpy.data.objects:
    if o.name == "Explainer_Card": o.animation_data_clear(); o.hide_render = True
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.render.use_motion_blur = False
sc.render.image_settings.file_format = "JPEG"
for f in map(int, a[1:]):
    sc.frame_set(f); t = D.matrix_world @ D.pose.bones["foot.R"].head
    for k, ang in enumerate((0, 90, 180, 270)):
        off = Vector((math.cos(math.radians(ang)) * 0.55, math.sin(math.radians(ang)) * 0.55, 0.18))
        cam.location = t + off; cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(OUT, "g%04d_%d.jpg" % (f, k)); bpy.ops.render.render(write_still=True)
