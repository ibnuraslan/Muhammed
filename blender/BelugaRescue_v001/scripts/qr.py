"""quick look render: blender -b f.blend --python qr.py -- out.png frame cx cy cz ax ay az lens [w]"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
sc = bpy.context.scene
out, f = a[0], int(a[1]); c = Vector(map(float, a[2:5])); t = Vector(map(float, a[5:8])); lens = float(a[8]); W = int(a[9]) if len(a) > 9 else 270
cam = sc.camera
if cam is None or "--free" in a or len(a) > 2:
    cd = bpy.data.cameras.new("QR"); cam = bpy.data.objects.new("QR", cd); sc.collection.objects.link(cam)
    cam.location = c; cam.rotation_euler = (t - c).to_track_quat('-Z', 'Y').to_euler(); cd.lens = lens; cd.clip_start = 0.02
    sc.camera = cam
sc.frame_set(f)
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, round(W * 16 / 9), 100
sc.cycles.samples = 8; sc.render.use_motion_blur = False; sc.cycles.texture_limit_render = "1024"
sc.render.filepath = out; bpy.ops.render.render(write_still=True)
