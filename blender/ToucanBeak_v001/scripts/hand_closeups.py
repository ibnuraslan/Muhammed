"""Close-up pass of every hand action (hands rule step 4).  blender -b look.blend -P hand_closeups.py -- <out_dir>"""
import bpy, sys, os
from mathutils import Vector
out = sys.argv[sys.argv.index('--') + 1]; os.makedirs(out, exist_ok=True)
sc = bpy.context.scene; OB = bpy.data.objects
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.render.use_motion_blur = False
sc.render.image_settings.file_format = 'JPEG'
cam = bpy.data.objects.new('HandCam', bpy.data.cameras.new('HandCam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50
SHOTS = [(560, "VetB", "R", (-0.3, -0.25, 0.15)), (640, "VetB", "R", (-0.25, 0.3, 0.2)), (600, "VetA", "R", (0.35, -0.3, 0.15)),
         (600, "VetA", "L", (-0.35, -0.3, 0.15)), (1580, "VetB", "R", (-0.3, 0.2, 0.15)), (1660, "VetB", "R", (-0.3, -0.2, 0.15)),
         (1750, "VetB", "L", (-0.3, 0.25, 0.15)), (1780, "VetB", "L", (0.3, 0.3, 0.2)), (1860, "VetB", "R", (-0.3, 0.25, 0.15)),
         (1900, "VetB", "R", (-0.25, -0.2, 0.2)), (1720, "VetB", "R", (-0.3, -0.3, 0.2)), (1900, "VetA", "L", (-0.35, -0.25, 0.15))]
for i, (f, nm, s, off) in enumerate(SHOTS):
    sc.frame_set(f); rg = OB[nm]; w = rg.matrix_world @ rg.pose.bones["wrist." + s].tail
    cam.location = w + Vector(off); cam.rotation_euler = (w - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, "h%02d_f%04d_%s_%s.jpg" % (i, f, nm, s)); bpy.ops.render.render(write_still=True)
print("HANDS_DONE")
