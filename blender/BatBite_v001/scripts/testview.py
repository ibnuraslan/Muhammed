import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--")+1:]; OUT = a[0]
sc = bpy.context.scene
cam = bpy.data.objects.new("TC", bpy.data.cameras.new("TC")); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.render.image_settings.file_format='JPEG'
views = [v.split(":") for v in a[1:]]
for i, (loc, tgt, lens) in enumerate(views):
    L = Vector(map(float, loc.split(","))); T = Vector(map(float, tgt.split(",")))
    cam.location = L; cam.rotation_euler = (T - L).to_track_quat('-Z','Y').to_euler(); cam.data.lens = float(lens); cam.data.clip_end = 5000
    sc.render.filepath = "%s_%02d.jpg" % (OUT, i); bpy.ops.render.render(write_still=True)
