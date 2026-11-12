"""Clipping-check close-ups at every hand contact / hand action (270x480, 8 samples).
blender -b film.blend --python clip_closeups.py -- <out_dir>
Each shot tries several camera offsets around the target and keeps the first one with a clear line of sight
(ray from the camera reaches the target point unobstructed), so no shot is filled by a suit, wall or desk."""
import bpy, sys, os, math
from mathutils import Vector, Matrix
out = sys.argv[sys.argv.index("--") + 1]; os.makedirs(out, exist_ok=True)
sc = bpy.context.scene; O = bpy.data.objects
def bone(arm, n, f, t=0.0):
    sc.frame_set(f); pb = O[arm].pose.bones[n]; return O[arm].matrix_world @ pb.head.lerp(pb.tail, t)
def mid(*ps): return sum(ps, Vector()) / len(ps)
def hand(arm, s, f): return mid(bone(arm, "wrist." + s, f), bone(arm, "finger3-1." + s, f), bone(arm, "finger3-2." + s, f))
def obj(n, f): sc.frame_set(f); return O[n].matrix_world.translation.copy()
# (name, frame, target fn, preferred offset, lens)
SHOTS = [("gun_grip", 1, lambda: hand("Robber", "R", 1), Vector((0.3, -0.05, 0.1)), 45),
         ("shield_hands_front", 400, lambda: mid(hand("Owner", "L", 400), hand("Owner", "R", 400)), Vector((0.0, -0.8, 0.0)), 40),
         ("shield_side_gap", 400, lambda: hand("Owner", "L", 400), Vector((0.45, 0.05, 0.0)), 45),
         ("impact_hands", 560, lambda: mid(hand("Owner", "L", 560), hand("Owner", "R", 560)), Vector((0.15, -0.75, 0.05)), 40),
         ("wince_recoil", 920, lambda: hand("Owner", "L", 920), Vector((0.15, -0.5, 0.05)), 45),
         ("hand_on_chest", 960, lambda: hand("Owner", "L", 960), Vector((0.2, -0.5, 0.05)), 45),
         ("neck_cup_side", 1030, lambda: hand("Owner", "R", 1030), Vector((-0.4, -0.25, 0.0)), 45),
         ("neck_cup_front", 1030, lambda: hand("Owner", "R", 1030), Vector((-0.1, -0.5, 0.0)), 45),
         ("hand_lowering", 1083, lambda: hand("Owner", "R", 1083), Vector((-0.3, -0.45, 0.05)), 40),
         ("ring_up", 400, lambda: obj("WeddingRing", 400), Vector((0.05, -0.12, 0.03)), 60),
         ("ring_dented_look", 1150, lambda: hand("Owner", "L", 1150), Vector((0.1, -0.45, 0.15)), 45),
         ("bandage", 1256, lambda: obj("FingerBandage", 1256), Vector((0.12, -0.25, 0.15)), 50),
         ("plaster", 1256, lambda: obj("NeckPlaster", 1256), Vector((-0.2, -0.15, 0.03)), 55),
         ("walk_hands", 1300, lambda: mid(hand("Owner", "L", 1300), hand("Owner", "R", 1300)), Vector((0.0, -1.3, 0.2)), 35),
         ("walk_feet", 1320, lambda: mid(bone("Owner", "foot.L", 1320), bone("Owner", "foot.R", 1320)), Vector((0.0, -1.2, 0.25)), 35),
         ("stand_feet", 300, lambda: mid(bone("Owner", "foot.L", 300), bone("Owner", "foot.R", 300)), Vector((-0.6, -0.4, 0.25)), 35)]
cam = sc.camera; cam.animation_data_clear(); cam.data.animation_data_clear()
cam.rotation_mode = 'QUATERNION'; cam.data.dof.use_dof = False; cam.data.clip_start = 0.005
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.render.use_motion_blur = False
sc.render.image_settings.file_format = 'JPEG'
def clear(p, t):
    dg = bpy.context.evaluated_depsgraph_get(); d = t - p; L = d.length
    hit, loc, n, i, ob, M = sc.ray_cast(dg, p, d.normalized(), distance=L)
    return (not hit) or (loc - t).length < 0.03 or (loc - p).length > L - 0.03
log = []
for i, (nm, f, tgt, off, lens) in enumerate(SHOTS):
    t = tgt(); sc.frame_set(f)
    cands = []
    for ang in (0, 30, -30, 60, -60, 90, -90, 135, -135):
        for up in (0.0, 0.12, -0.08):
            cands.append(Matrix.Rotation(math.radians(ang), 3, 'Z') @ off + Vector((0, 0, up)))
    p = next((t + c for c in cands if clear(t + c, t)), t + off)
    cam.location = p; cam.rotation_quaternion = (t - p).to_track_quat('-Z', 'Y'); cam.data.lens = lens
    sc.render.filepath = os.path.join(out, "c%02d_%s_f%d.jpg" % (i, nm, f)); bpy.ops.render.render(write_still=True)
    log.append("c%02d %-20s f%-5d cam %s" % (i, nm, f, tuple(round(x, 2) for x in p)))
print("\n".join(log))
