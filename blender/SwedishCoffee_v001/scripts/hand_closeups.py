"""Close-up check of every hand action (STYLE_ANIMATED.md hands rule, step 4).
blender -b film.blend --python hand_closeups.py -- <out_dir>
A temporary camera is placed 0.5 m from the hand, on the side of the film camera, looking at the hand. 270x480, 12 spp.
The film camera is restored afterwards; nothing is saved."""
import sys, os, bpy
from mathutils import Vector, Matrix
import math
OUT = sys.argv[sys.argv.index("--") + 1]; os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
SHOTS = [("TwinA_S1", "R", 100, "shackled hands"), ("King_S2", "R", 220, "king raises hand"), ("Soldier_S3_a", "L", 625, "pot overhead"),
         ("Soldier_S3_b", "R", 650, "pouring sack"), ("Servant_S4_0", "R", 828, "pouring coffee into the resting cup"), ("Servant_S4_1", "L", 1103, "pouring tea"), ("TwinA_S4", "R", 845, "cup grip at table"),
         ("TwinA_S4", "R", 880, "drinking"), ("TwinA_S4", "L", 900, "resting hand"), ("TwinB_S4", "L", 1140, "tea sip"), ("TwinB_S4", "R", 1000, "resting hand"),
         ("Doctor1_S4", "R", 1350, "quill"), ("Doctor2_S4", "L", 1400, "ledger hand"), ("Bearer_S5_0_0", "L", 1760, "coffin grip (hip height)"), ("Dancer_S6_0", "R", 1880, "couple's joined hands"),
         ("Masked_S6", "R", 1906, "flash"), ("King_S6", "R", 1936, "collapse"), ("TwinA_bed_S7", "L", 2100, "hand resting on brother's hand"),
         ("TwinA_vold_S7", "R", 2300, "coffee cup"), ("Cheer_S8_0", "R", 2600, "toast cup")]
cam0 = sc.camera
cd = bpy.data.cameras.new("HandCam"); cd.lens = 45; cd.sensor_width = 36
hc = bpy.data.objects.new("HandCam", cd); sc.collection.objects.link(hc)
r = sc.render; r.resolution_x, r.resolution_y, r.resolution_percentage = 270, 480, 100
sc.cycles.samples = 12; r.use_motion_blur = False; r.image_settings.file_format = "JPEG"
for i, (nm, s, f, what) in enumerate(SHOTS):
    a = bpy.data.objects.get(nm)
    if a is None: print("MISSING", nm); continue
    sc.frame_set(f); sc.camera = cam0; bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    h = a.matrix_world @ a.pose.bones["finger3-1." + s].head
    d0 = (cam0.matrix_world.translation - h); d0.z = max(d0.z, 0.2 * d0.length); d0.normalize()
    cands = [d0] + [(Matrix.Rotation(math.radians(ang), 3, 'Z') @ d0).normalized() for ang in (60, -60, 120, -120, 180)] + [Vector((0, 0, 1))]
    def first_visible_hit(o_, dir_, dist):
        p_ = o_.copy(); left = dist
        for _ in range(40):
            hit, loc, nrm, idx, ob, mx = sc.ray_cast(dg, p_, dir_, distance=left)
            if not hit: return None
            if not ob.hide_render: return loc
            left -= (loc - p_).length + 0.002; p_ = loc + dir_ * 0.002
            if left <= 0: return None
        return None
    cands += [(c_ + Vector((0, 0, 1.2))).normalized() for c_ in cands[:6]]
    pick, best, dist_ = d0, -1.0, 0.5
    for dd in (0.5, 0.8):
        for d in cands:   # first direction whose line of sight reaches the hand before any other rendered surface
            loc = first_visible_hit(h + d * dd, -d, dd + 0.1)
            if loc is None or (loc - h).length < 0.08: pick, dist_ = d, dd; best = 9; break
            clear = (loc - (h + d * dd)).length
            if clear > best: best, pick, dist_ = clear, d, dd
        if best == 9: break
    hc.location = h + pick * dist_
    hc.rotation_euler = (h - hc.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = hc
    r.filepath = os.path.join(OUT, "h%02d_%s_f%04d.jpg" % (i, nm, f)); bpy.ops.render.render(write_still=True)
    print("HAND", i, nm, s, f, what)
sc.camera = cam0
