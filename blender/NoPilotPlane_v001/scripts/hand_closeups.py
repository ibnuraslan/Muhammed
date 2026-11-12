"""Hand close-ups for review: a 35 mm camera at YOU's eye aimed at the acting hand.
blender -b film.blend --python hand_closeups.py -- out_dir t:side ..."""
import sys, os, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; out = a[0]; os.makedirs(out, exist_ok=True)
sc = bpy.context.scene; Y = bpy.data.objects["YOU"]
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 12; sc.render.use_motion_blur = False
sc.render.image_settings.file_format = "JPEG"
cd = bpy.data.cameras.new("HC"); cd.lens = 30; cd.clip_start = 0.02; c = bpy.data.objects.new("HC", cd); sc.collection.objects.link(c)
film = sc.camera
for i, spec in enumerate(a[1:]):
    t, s = spec.split(":"); f = 1 + round(float(t) * 60); sc.frame_set(f)
    hand = Y.matrix_world @ Y.pose.bones["finger3-1." + s].head
    eye = film.matrix_world.translation
    p = eye + (hand - eye) * 0.35
    c.location = p; c.rotation_euler = (hand - p).to_track_quat('-Z', 'Y').to_euler(); sc.camera = c
    sc.render.filepath = os.path.join(out, "h%02d_%s_%s.jpg" % (i, t, s)); bpy.ops.render.render(write_still=True)
