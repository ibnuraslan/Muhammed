"""270x480 close-ups of every hand action (camera placed beside each hand, looking at it).
blender -b film.blend --python hand_closeups.py -- <out_dir>"""
import sys, os, bpy
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]; os.makedirs(out, exist_ok=True)
sc = bpy.context.scene; O = bpy.data.objects
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 270, 480, 100
sc.cycles.samples = 12; sc.render.use_motion_blur = False; sc.render.image_settings.file_format = 'JPEG'
cam = bpy.data.objects.new("HandCam", bpy.data.cameras.new("HandCam")); sc.collection.objects.link(cam)
cam.data.lens = 35; cam.data.clip_start = 0.01; cam.data.dof.use_dof = False
main = sc.camera; sc.camera = cam
SHOTS = [("steward_hold", "Steward", "R", 40, (-0.45, -0.25, 0.1)), ("steward_raise", "Steward", "L", 100, (0.45, 0.3, 0.05)),
         ("steward_click", "Steward", "R", 112, (-0.4, 0.35, 0.05)), ("deckhand_coil", "Deckhand", "R", 200, (0.45, -0.3, 0.25)),
         ("tech_tongs", "Tech", "R", 1150, (-0.4, 0.15, 0.25)), ("tech_tray", "Tech", "L", 1150, (0.45, 0.1, 0.25)),
         ("expertA_magnifier", "ExpertA", "R", 1280, (0.45, -0.3, 0.05)), ("expertA_desk", "ExpertA", "L", 1280, (-0.4, -0.3, 0.3)),
         ("expertB_print_L", "ExpertB", "L", 1280, (0.45, -0.35, 0.05)), ("expertB_print_R", "ExpertB", "R", 1280, (-0.45, -0.35, 0.05))]
for n, actor, s, f, off in SHOTS:
    sc.frame_set(f)
    rig = O[actor]
    for o in O:      # make sure the rooms render for these probe frames
        pass
    w = rig.matrix_world @ rig.pose.bones["wrist." + s].tail
    cam.location = w + Vector(off)
    cam.rotation_euler = (w - cam.location).to_track_quat('-Z', 'Y').to_euler()
    hidden = []
    for o in O:   # nothing else should block: hide camera-hidden flags off for this probe
        if not o.visible_camera and (o.matrix_world.translation - w).length < 3:
            o.visible_camera = True; hidden.append(o)
    sc.render.filepath = os.path.join(out, f"{n}_f{f}.jpg"); bpy.ops.render.render(write_still=True)
    for o in hidden: o.visible_camera = False
sc.camera = main
print("CLOSEUPS", len(SHOTS))
