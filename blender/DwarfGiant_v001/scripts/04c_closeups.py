"""270x480 close-ups of hand contacts + head items, camera placed from evaluated bones"""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene; OB = bpy.data.objects
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.render.image_settings.file_format = "JPEG"
cam = sc.camera; cam.constraints.clear(); cam.animation_data_clear(); cam.data.animation_data_clear(); cam.data.dof.use_dof = False
tgt = bpy.data.objects.new("CU_T", None); sc.collection.objects.link(tgt)
tc = cam.constraints.new("TRACK_TO"); tc.target = tgt; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
SHOTS_ALL = [("hero_desk_hand", 740, "Hero", "wrist.L", Vector((-0.2, -0.35, 0.25))), ("hero_desk_hand2", 840, "Hero", "wrist.L", Vector((0.3, -0.35, 0.2))),
         ("hero_ear_cup", 1440, "Hero", "wrist.L", Vector((0.35, -0.3, 0.1))), ("hero_idle_hands", 60, "Hero", "wrist.R", Vector((-0.25, -0.45, 0.1))),
         ("officer1_slider", 100, "Officer1", "wrist.R", Vector((0.0, -0.5, 0.2))), ("officer1_cap", 100, "Officer1", "head", Vector((0.3, -0.5, 0.1))),
         ("officer2_hands", 1000, "Officer2", "wrist.L", Vector((0.3, -0.5, 0.2))), ("clerk_writing", 300, "Clerk", "wrist.R", Vector((0.0, -0.6, 0.3))),
         ("surgeon1_cap_mask_hands", 1560, "Surgeon1", "head", Vector((0.4, -0.5, 0.0))), ("surgeon2_hands", 1600, "Surgeon2", "wrist.L", Vector((0.4, -0.4, 0.3))),
         ("nurse_hands", 1600, "Nurse", "wrist.R", Vector((0.3, -0.5, 0.2))), ("hero_lying_hands", 1790, "Hero", "wrist.L", Vector((-0.4, 0.0, 0.4))),
         ("normal_hands", 1900, "Normal", "wrist.L", Vector((-0.5, 0.0, 0.1))), ("young_old_hands", 2250, "Young", "wrist.R", Vector((0.0, -0.6, 0.2)))]
SHOTS = [x for x in SHOTS_ALL if (sys.argv[-1] == "all" or x[0] in sys.argv[-1].split(","))]
for nm, f, ch, bone, off in SHOTS:
    sc.frame_set(f); rig = OB["RIG_" + ch]; p = rig.matrix_world @ rig.pose.bones[bone].head
    tgt.location = p; cam.location = p + off * (1.0 if bone != "head" else 1.0); cam.data.lens = 35
    sc.render.filepath = os.path.join(OUT, f"{nm}_f{f}.jpg"); bpy.ops.render.render(write_still=True)
print("CLOSEUPS", len(SHOTS))
