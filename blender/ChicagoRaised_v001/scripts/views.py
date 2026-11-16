"""Quick look renders: blender -b f.blend -P views.py -- out_dir W "name:x,y,z:tx,ty,tz:lens[:frame]" ...  (Cycles 8 spp, temp camera)"""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; out = a[0]; W = int(a[1]); os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
cam = bpy.data.objects.new("ViewCam", bpy.data.cameras.new("ViewCam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.clip_start = 0.05; cam.data.clip_end = 2000
sc.render.resolution_x = W; sc.render.resolution_y = round(W * 16 / 9); sc.render.resolution_percentage = 100
sc.cycles.samples = 8; sc.cycles.use_denoising = True; sc.render.image_settings.file_format = 'JPEG'
for spec in a[2:]:
    p = spec.split(":"); n = p[0]; loc = Vector([float(v) for v in p[1].split(",")]); tg = Vector([float(v) for v in p[2].split(",")])
    cam.data.lens = float(p[3]); 
    if len(p) > 4: sc.frame_set(int(p[4]))
    cam.location = loc; cam.rotation_euler = (tg - loc).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, n + ".jpg"); bpy.ops.render.render(write_still=True)
