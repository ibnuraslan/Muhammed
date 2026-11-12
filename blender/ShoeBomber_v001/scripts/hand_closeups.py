"""Close-up pass of every hand action (270x480). blender -b film.blend --python hand_closeups.py -- <out_prefix>"""
import sys, bpy
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; O = bpy.data.objects
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.render.use_motion_blur = False
sc.render.image_settings.file_format = 'JPEG'
cd = bpy.data.cameras.new("HandCheck"); cd.lens = 35; cd.clip_start = 0.01; cam = bpy.data.objects.new("HandCheck", cd); sc.collection.objects.link(cam); sc.camera = cam
for o in O:
    if o.name == "WipeCard": o.hide_render = True
SHOTS = [(60, "Bomber", "wrist.R", (0.35, 0.25, 0.25)), (60, "Bomber", "wrist.L", (0.35, 0.3, 0.2)), (492, "Attendant", "wrist.R", (0.3, -0.3, 0.3)),
         (600, "PaxA", "wrist.L", (0.3, 0.3, 0.4)), (600, "PaxB", "wrist.R", (0.35, 0.2, 0.35)), (640, "Attendant", "wrist.R", (0.35, 0.2, 0.3)),
         (712, "Steward", "wrist.R", (0.1, -0.4, 0.3)), (880, "Attendant", "wrist.L", (-0.35, 0.3, 0.3)), (960, "Attendant", "wrist.R", (0.3, 0.45, 0.1)),
         (1478, "Traveller", "wrist.R", (0.4, -0.3, 0.2)), (1515, "Traveller", "wrist.R", (0.3, -0.4, 0.3)), (1500, "Officer", "wrist.L", (0.0, -0.45, 0.3)),
         (300, "Attendant", "wrist.L", (0.3, -0.35, 0.3)), (900, "Sleeper1", "wrist.L", (0.3, 0.4, 0.3))]
for i, (f, rig, bone, off) in enumerate(SHOTS):
    sc.frame_set(f); r = O[rig]; p = (r.matrix_world @ r.pose.bones[bone].matrix).translation
    cam.location = p + Vector(off); cam.rotation_euler = (p - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = "%s_%02d_f%d_%s_%s.jpg" % (OUT, i, f, rig, bone); bpy.ops.render.render(write_still=True)
