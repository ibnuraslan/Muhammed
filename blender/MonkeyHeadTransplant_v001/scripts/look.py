import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--")+1:]; out = a[0]; views = eval(a[1])
sc = bpy.context.scene
cam = bpy.data.objects.get("LookCam") or bpy.data.objects.new("LookCam", bpy.data.cameras.new("LookCam"))
if cam.name not in sc.collection.objects: sc.collection.objects.link(cam)
sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 270, 480
sc.cycles.samples = 8; sc.render.use_motion_blur = False
sc.render.image_settings.file_format = "JPEG"
for i, (f, loc, tgt, lens) in enumerate(views):
    sc.frame_set(f)
    cam.location = loc; cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); cam.data.lens = lens
    sc.render.filepath = f"{out}_{i:02d}.jpg"; bpy.ops.render.render(write_still=True)
