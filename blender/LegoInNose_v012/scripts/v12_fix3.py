"""v012b fixes after watching preview pass 2:
 - sink 1752-2036: the red brick sat partly inside his palm (hidden 1756-1871). It now rests ON the palm surface: offset along
   the palm normal (the side facing the camera), every frame.
 - bed 1478-1586 (clip scan 1525-1567, bare arm sweeping across the lens): hands and elbow poles keyed every 6 frames so they
   follow his torso instead of interpolating through it.
 - 496-575 (list 15, 38): the hand holding the yellow brick no longer goes up over his head (sleeve over the lens); it is pulled
   65% toward a point in front of his face, and the yellow brick stays in its pinch.
 - 355-390 (list 11): smeared/defocused close-up: f-stop 16 there.
blender -b in.blend --python v12_fix3.py -- out.blend"""
import bpy, sys
from mathutils import Vector, Matrix
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; vl = bpy.context.view_layer
exec(open("/home/user/Muhammed/blender/pipeline/hand_poses.py").read())
def fcs(o):
    ad = o.animation_data
    return [fc for l in ad.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves] if ad and ad.action else []
def keyM(o, f, Mx):
    o.matrix_world = Mx; vl.update(); o.keyframe_insert("location", frame=f)
    o.keyframe_insert("rotation_quaternion" if o.rotation_mode == "QUATERNION" else "rotation_euler", frame=f)
M = bpy.data.objects["Man"]; BR = bpy.data.objects["Brick_Big"]; CAM = bpy.data.objects["CAM_Film"]
def W(rig, n, t=False): pb = rig.pose.bones[n]; return rig.matrix_world @ (pb.tail if t else pb.head)
# 1. brick on the palm: rigid to his right wrist, in the spot where it sits on the palm at 1950 (fully visible there)
def BMx(n): return M.matrix_world @ M.pose.bones[n].matrix
sc.frame_set(1950); OFF = BMx("wrist.R").inverted() @ BR.matrix_world
for f in range(1752, 2037):
    sc.frame_set(f); keyM(BR, f, BMx("wrist.R") @ OFF)
# 2. bed hands every 6 frames
for fc in fcs(M):
    if fc.data_path.startswith(('pose.bones["IK_hand.', 'pose.bones["Pole_elbow.')):
        for k in [k for k in fc.keyframe_points if 1478 <= k.co.x <= 1586][::-1]: fc.keyframe_points.remove(k)
        fc.update()
z = Vector((0, 0, 1))
for f in list(range(1478, 1587, 6)) + [1586]:
    sc.frame_set(f)
    side = W(M, "clavicle.R") - W(M, "clavicle.L"); side.z = 0; side.normalize()
    along = W(M, "neck01") - W(M, "pelvis.L"); along.z = 0; along.normalize()
    tgt = {"L": W(M, "spine01") - side * 0.09 + z * 0.15, "R": (W(M, "pelvis.L") + W(M, "pelvis.R")) / 2 + side * 0.07 + along * 0.06 + z * 0.15}
    for s, sg in (("L", -1), ("R", 1)):
        place_hand(M, s, f, tgt[s], -z, (-side * sg + along * 0.3).normalized())
        pole = M.pose.bones["Pole_elbow." + s]; m = pole.matrix.copy()
        m.translation = M.matrix_world.inverted() @ (W(M, "upperarm01." + s) + side * (0.35 * sg) - along * 0.2 - z * 0.05); pole.matrix = m; vl.update()
        pole.keyframe_insert("location", frame=f, group=pole.name)
# 3. boy's raised hand 496-575
B = bpy.data.objects["Boy"]; BS = bpy.data.objects["Brick_Small"]; pb = B.pose.bones["IK_hand.R"]
T = (B.matrix_world.to_3x3() @ pb.bone.matrix_local.to_3x3()).inverted()
def pinch(): return (W(B, "finger1-3.R", True) + W(B, "finger2-3.R", True)) / 2
held = {}
for f in range(490, 582):
    sc.frame_set(f)
    if (BS.matrix_world.translation - pinch()).length < 0.012: held[f] = BS.matrix_world.translation - pinch()
cf = sorted([c for c in fcs(B) if c.data_path == 'pose.bones["IK_hand.R"].location'], key=lambda c: c.array_index)
newk = {}
for f in list(range(496, 576, 4)) + [575]:          # key every 4 frames (the old keys were sparse)
    sc.frame_set(f); hd = W(B, "head"); eyes = (W(B, "eye.L") + W(B, "eye.R")) / 2
    fwd = eyes - hd; fwd.z = 0; fwd.normalize()
    tgt = eyes + fwd * 0.20 - z * 0.06                  # in front of his face, just below eye level
    hand = W(B, "IK_hand.R"); w = min(1.0, (f - 496) / 8.0, (575 - f) / 8.0)
    newk[f] = [c.evaluate(f) for c in cf]; d = T @ ((tgt - hand) * w)
    newk[f] = [newk[f][i] + d[i] for i in range(3)]
for f, v in newk.items():
    for c in cf: c.keyframe_points.insert(f, v[c.array_index], options={"FAST"})
for c in cf: c.update()
for f, off in held.items():
    sc.frame_set(f); keyM(BS, f, Matrix.Translation(pinch() + off) @ BS.matrix_world.to_3x3().to_4x4())
# 3b. the 496-575 camera was a worm's-eye shot (arm looked raised overhead, sleeve over the lens): level, at his eye height
AIM = bpy.data.objects["CAM_Film_Aim"]
chans = [fc for o in (CAM, AIM) for fc in fcs(o) if fc.data_path == "location"] + [fc for fc in fcs(CAM.data) if fc.data_path == "lens"]
for fc in chans:
    for k in [k for k in fc.keyframe_points if 496 <= k.co.x <= 575][::-1]: fc.keyframe_points.remove(k)
    fc.update()
for f in list(range(496, 576, 4)) + [575]:
    sc.frame_set(f); eyes = (W(B, "eye.L") + W(B, "eye.R")) / 2; hd = W(B, "head"); fwd = eyes - hd; fwd.z = 0; fwd.normalize()
    side = Vector((-fwd.y, fwd.x, 0)); a = eyes * 0.6 + pinch() * 0.4
    CAM.location = eyes + fwd * 0.62 + side * 0.12; CAM.location.z = eyes.z + 0.01; CAM.keyframe_insert("location", frame=f)
    AIM.location = a; AIM.keyframe_insert("location", frame=f); CAM.data.lens = 40; CAM.data.keyframe_insert("lens", frame=f)
# 4. DOF
dof = CAM.data.dof
for f, v in ((354, dof.aperture_fstop), (355, 16.0), (390, 16.0), (391, dof.aperture_fstop)):
    dof.aperture_fstop = v; CAM.data.keyframe_insert("dof.aperture_fstop", frame=f)
for fc in fcs(CAM.data):
    if fc.data_path == "dof.aperture_fstop":
        for k in fc.keyframe_points:
            if 353 < k.co.x < 392: k.interpolation = "CONSTANT"
print("FIX3 done; brick-held frames", len(held), "hand keys moved", len(newk))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
