"""quick look: blender -b x.blend --python testview.py -- out.png frame camx camy camz tx ty tz lens [w]"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
sc = bpy.context.scene; sc.frame_set(int(a[1]))
cam = bpy.data.objects.get("TestCam") or bpy.data.objects.new("TestCam", bpy.data.cameras.new("TestCam"))
if cam.name not in sc.collection.objects: sc.collection.objects.link(cam)
cam.location = Vector(map(float, a[2:5])); t = Vector(map(float, a[5:8])); cam.data.lens = float(a[8])
cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler(); sc.camera = cam
W = int(a[9]) if len(a) > 9 else 270
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, round(W * 16 / 9), 100
sc.cycles.samples = 8; sc.cycles.use_denoising = True; sc.render.filepath = a[0]; bpy.ops.render.render(write_still=True)
