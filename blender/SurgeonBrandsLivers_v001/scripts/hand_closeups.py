"""270x480 close-ups of every hand action (grips, touches, hands near face/chest), for the hands review.
blender -b film.blend --python hand_closeups.py -- <out_dir>"""
import sys, os
import bpy
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
SHOTS = [  # frame, actor, side, camera offset from the hand, label
    (60, "Surgeon1", "R", Vector((0.25, 0.25, 0.15)), "pen grip"),
    (380, "Surgeon1", "R", Vector((0.2, 0.3, 0.2)), "needle driver"),
    (380, "Surgeon1", "L", Vector((-0.2, 0.3, 0.2)), "hand on drape"),
    (490, "Surgeon1", "R", Vector((0.15, 0.35, 0.05)), "mask pull"),
    (60, "Nurse", "R", Vector((0.3, -0.3, 0.0)), "lamp handle"),
    (620, "Patient", "L", Vector((-0.3, -0.3, 0.1)), "mug"),
    (720, "Patient", "R", Vector((-0.35, -0.25, 0.05)), "clutch side"),
    (720, "Patient", "L", Vector((-0.3, -0.35, 0.1)), "hand on knee"),
    (880, "Nurse", "R", Vector((0.4, -0.3, 0.1)), "bed push"),
    (1016, "Surgeon2", "L", Vector((0.0, -0.4, 0.05)), "glove snap"),
    (1140, "GloveHands", "R", Vector((0.1, -0.35, 0.05)), "liver lift"),
    (1300, "Surgeon1", "L", Vector((-0.35, 0.2, 0.15)), "lectern"),
    (1345, "Surgeon1", "R", Vector((-0.4, -0.2, 0.05)), "spread hands"),
    (1525, "PanelA", "R", Vector((0.35, -0.3, 0.1)), "gavel raised"),
    (1540, "PanelA", "R", Vector((0.35, -0.3, 0.1)), "gavel strike"),
    (1596, "PanelB", "R", Vector((0.35, 0.3, 0.15)), "stamp"),
    (1400, "PanelC", "R", Vector((0.35, -0.3, 0.15)), "writing"),
]
cam = bpy.data.objects.new("HANDCAM", bpy.data.cameras.new("HANDCAM")); sc.collection.objects.link(cam)
cam.data.lens = 50; cam.data.clip_start = 0.01; sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 270, 480, 100
sc.cycles.samples = 8; sc.render.use_motion_blur = False; sc.render.image_settings.file_format = 'JPEG'
for i, (f, n, s, off, lab) in enumerate(SHOTS):
    sc.frame_set(f); r = bpy.data.objects[n]
    h = r.matrix_world @ r.pose.bones["finger3-1." + s].head
    cam.location = h + off; cam.rotation_euler = (h - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, "h%02d_f%04d_%s_%s_%s.jpg" % (i, f, n, s, lab.replace(" ", "_")))
    bpy.ops.render.render(write_still=True)
print("CLOSEUPS", len(SHOTS))
