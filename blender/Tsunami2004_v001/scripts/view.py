"""blender -b scene.blend --python view.py -- out_prefix "x,y,z:tx,ty,tz:lens:frame" ..."""
import sys, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
sc = bpy.context.scene
cam = sc.camera
if cam is None:
    cd = bpy.data.cameras.new("TmpCam"); cam = bpy.data.objects.new("TmpCam", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 270, 480, 100
sc.cycles.samples = 8; sc.render.use_motion_blur = False; sc.cycles.texture_limit_render = "1024"
sc.render.image_settings.file_format = "JPEG"
cam.animation_data_clear(); cam.data.animation_data_clear()
for i, spec in enumerate(a[1:]):
    p, t, lens, fr = spec.split(":")
    p = Vector([float(v) for v in p.split(",")]); t = Vector([float(v) for v in t.split(",")])
    sc.frame_set(int(fr)); cam.location = p; cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = float(lens)
    cam.data.clip_end = 8000
    sc.render.filepath = "%s_%02d.jpg" % (a[0], i); bpy.ops.render.render(write_still=True)
