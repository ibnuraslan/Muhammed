import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--")+1:]; OUT = a[0]
sc = bpy.context.scene
cam = bpy.data.objects.new("TC", bpy.data.cameras.new("TC")); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.render.image_settings.file_format='JPEG'
sc.render.use_stamp = True; sc.render.use_stamp_frame = True; sc.render.stamp_font_size = 10
for k in ("date","time","render_time","camera","lens","scene","filename","memory"): setattr(sc.render, "use_stamp_"+k, False)
for i, v in enumerate(a[1:]):
    f, loc, tgt, lens = v.split(":"); sc.frame_set(int(f))
    L = Vector(map(float, loc.split(","))); T = Vector(map(float, tgt.split(",")))
    cam.location = L; cam.rotation_euler = (T - L).to_track_quat('-Z','Y').to_euler(); cam.data.lens = float(lens); cam.data.clip_end = 5000
    sc.render.filepath = "%s_%02d.jpg" % (OUT, i); bpy.ops.render.render(write_still=True)
