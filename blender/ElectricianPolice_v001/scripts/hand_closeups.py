"""270x480 close-ups of every hand action (client hands rule). blender -b film.blend --python hand_closeups.py -- outdir"""
import bpy, sys, os
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]; os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
cd = bpy.data.cameras.new("HandCam"); cd.lens = 50; hc = bpy.data.objects.new("HandCam", cd); sc.collection.objects.link(hc); sc.camera = hc
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.render.use_motion_blur = False
sc.render.image_settings.file_format = "JPEG"
SHOTS = [(60, "Man", "L"), (60, "Man", "R"), (276, "Man", "R"), (276, "OfficerA", "R"), (255, "OfficerA", "L"), (312, "Man", "L"),
         (412, "ManW", "R"), (560, "ManW", "L"), (940, "ManW", "R"), (1060, "Man", "R"), (1300, "OfficerB", "R"), (1306, "OfficerD", "R"),
         (1330, "OfficerC", "R"), (1340, "OfficerE", "L"), (1530, "ManW", "R"), (230, "Vendor", "R")]
for i, (f, n, s) in enumerate(SHOTS):
    sc.frame_set(f); arm = bpy.data.objects[n]
    w = arm.matrix_world @ arm.pose.bones["wrist." + s].head
    r = arm.matrix_world @ arm.pose.bones["root"].head
    side = (w - Vector((r.x, r.y, w.z)))
    side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
    hc.location = w + side * 0.45 + Vector((0, 0, 0.12))
    hc.rotation_euler = (w - hc.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(out, "h%02d_f%04d_%s_%s.jpg" % (i, f, n, s)); bpy.ops.render.render(write_still=True)
