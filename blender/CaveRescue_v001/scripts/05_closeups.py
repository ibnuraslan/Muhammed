"""Clipping close-up pass: a temporary camera 0.5-0.8 m from every contact moment, 270x480, 8 samples.
blender -b anim.blend --python 05_closeups.py -- <out_dir>"""
import sys, os, bpy
from mathutils import Vector as V
OUT = sys.argv[sys.argv.index("--") + 1]; os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
cd = bpy.data.cameras.new("CLOSE"); cd.lens = 35; cd.clip_start = 0.02
cam = bpy.data.objects.new("CLOSE", cd); sc.collection.objects.link(cam); sc.camera = cam
lt = bpy.data.objects.new("CLOSE_L", bpy.data.lights.new("CLOSE_L", 'POINT')); lt.data.energy = 8; lt.visible_volume_scatter = False
sc.collection.objects.link(lt)
wipe = bpy.data.objects.get("CAM_RockWipe")
if wipe: wipe.hide_render = True
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.render.use_motion_blur = False
sc.render.image_settings.file_format = 'JPEG'
SHOTS = [  # label, frame, rig, bone, camera offset (world)
    ("walk_feet", 150, "Boy3", "foot.L", (0.5, -0.5, 0.15)), ("walk_feet_coach", 250, "Coach", "foot.R", (-0.5, -0.4, 0.2)),
    ("run_feet_water", 480, "Boy5", "foot.L", (0.6, 0.3, 0.2)), ("huddle_hands", 1050, "HB2", "wrist.L", (0.4, -0.5, 0.2)),
    ("huddle_seat", 1050, "Boy1", "root", (0.6, -0.4, 0.0)), ("shield_hand", 1160, "Boy4", "head", (0.2, -0.55, 0.1)),
    ("diver_ledge_hands", 1150, "DiverA", "wrist.L", (0.3, 0.5, 0.25)), ("diver_mask", 1150, "DiverA", "head", (0.3, 0.45, 0.1)),
    ("rope_hand", 1330, "DiverB", "wrist.R", (-0.5, 0.0, 0.2)), ("squeeze_tank", 1390, "DiverB", "spine03", (0.6, 0.2, 0.3)),
    ("edge_kneel_hands", 1900, "Boy3", "wrist.L", (0.4, -0.45, 0.15)), ("edge_kneel_knees", 1900, "Boy3", "lowerleg01.L", (0.6, -0.3, 0.1)),
    ("medic_kneel", 2100, "DiverA", "lowerleg01.L", (0.2, -0.7, 0.2)), ("mask_kneel", 2100, "DiverB", "lowerleg01.R", (-0.6, -0.3, 0.2)),
    ("injection", 2240, "Boy2", "upperarm02.L", (0.35, -0.5, 0.1)), ("injection_hand", 2240, "DiverA", "wrist.R", (0.1, -0.5, 0.2)),
    ("mask_fit", 2370, "Boy2", "head", (0.15, -0.5, 0.05)), ("mask_straps", 2395, "Boy2", "head", (0.45, 0.3, 0.1)),
    ("tow_harness", 2500, "DiverB", "wrist.L", (-0.6, 0.1, 0.2)), ("tow_boy_mask", 2500, "Boy2", "head", (-0.5, -0.2, 0.2)),
    ("stretcher_front", 2800, "DiverA", "wrist.R", (0.5, -0.4, 0.1)), ("stretcher_back", 2800, "DiverB", "wrist.L", (-0.5, 0.4, 0.1)),
    ("stretcher_boy", 2850, "Boy4", "spine03", (0.8, 0.1, 0.4)), ("crowd_feet", 2900, "Crowd1", "foot.L", (0.4, -0.5, 0.15)),
    ("crowd_arms", 2900, "Crowd3", "wrist.R", (0.3, -0.6, 0.1)), ("headtorch_walk", 200, "Boy2", "head", (0.25, -0.45, 0.05))]
for i, (lab, f, rn, bn, off) in enumerate(SHOTS):
    sc.frame_set(f); r = bpy.data.objects[rn]
    p = r.matrix_world @ r.pose.bones[bn].head
    cam.location = p + V(off); cam.rotation_euler = (p - cam.location).to_track_quat('-Z', 'Y').to_euler()
    lt.location = cam.location + V((0, 0, 0.2))
    sc.render.filepath = os.path.join(OUT, "c%02d_f%04d_%s.jpg" % (i, f, lab)); bpy.ops.render.render(write_still=True)
print("CLOSEUPS", len(SHOTS))
