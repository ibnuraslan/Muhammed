"""blender -b x.blend --python multiview.py -- out_prefix W 'f cx cy cz tx ty tz lens;...'"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; pre, W = a[0], int(a[1])
sc = bpy.context.scene
cam = bpy.data.objects.new("TestCam", bpy.data.cameras.new("TestCam")); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, round(W * 16 / 9), 100
sc.render.engine = 'CYCLES'; sc.cycles.samples = 8; sc.cycles.use_denoising = True
for i, spec in enumerate(a[2].split(";")):
    v = [float(x) for x in spec.split()]
    sc.frame_set(int(v[0])); cam.location = Vector(v[1:4]); t = Vector(v[4:7]); cam.data.lens = v[7]; cam.data.clip_start = 0.005
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f"{pre}_{i:02d}.png"; bpy.ops.render.render(write_still=True)
