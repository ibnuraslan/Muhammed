"""v012b fixes after watching the preview:
 - render.use_persistent_data OFF: with it on, an object un-hidden mid-animation (the red brick at the sneeze) rendered BLACK in
   animation renders (stills were fine).
 - inhaler (list 33): baked to his right wrist for its whole time on screen (1392-1477), as gripped at 1436: no floating.
 - bench -> bed (list 34): the camera holds the 1466 framing to 1477 (hard cut to the bed at 1478), no pan across the wall.
 - bed (list 35, client F): both hands rest on his chest / belly, palms down, elbows out to the sides: no arm across his face or neck.
blender -b in.blend --python v12_fix2.py -- out.blend"""
import bpy, sys
from mathutils import Vector, Matrix
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; vl = bpy.context.view_layer
exec(open("/home/user/Muhammed/blender/pipeline/hand_poses.py").read())
sc.render.use_persistent_data = False
M = bpy.data.objects["Man"]
def fcs(o):
    ad = o.animation_data
    return [fc for l in ad.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves] if ad and ad.action else []
def BM(n): return M.matrix_world @ M.pose.bones[n].matrix
def W(n): return M.matrix_world @ M.pose.bones[n].head
# inhaler
I = bpy.data.objects["Prop_Inhaler"]
sc.frame_set(1436); off = BM("wrist.R").inverted() @ I.matrix_world
for fc in fcs(I):
    if fc.data_path in ("location", "rotation_euler", "rotation_quaternion", "scale"):
        for k in [k for k in fc.keyframe_points if 1390 <= k.co.x <= 1478][::-1]: fc.keyframe_points.remove(k)
        fc.update()
rp = "rotation_quaternion" if I.rotation_mode == "QUATERNION" else "rotation_euler"
for f in range(1390, 1479):
    sc.frame_set(f); I.matrix_world = BM("wrist.R") @ off; vl.update()
    I.keyframe_insert("location", frame=f); I.keyframe_insert(rp, frame=f)
# camera hold before the bed cut
CAM = bpy.data.objects["CAM_Film"]; AIM = bpy.data.objects["CAM_Film_Aim"]
chans = [fc for o in (CAM, AIM) for fc in fcs(o) if fc.data_path == "location"] + [fc for fc in fcs(CAM.data) if fc.data_path == "lens"]
for fc in chans:
    v = fc.evaluate(1466); nxt = fc.evaluate(1478)
    for k in [k for k in fc.keyframe_points if 1466 <= k.co.x < 1478][::-1]: fc.keyframe_points.remove(k)
    a = fc.keyframe_points.insert(1466, v, options={"FAST"}); b = fc.keyframe_points.insert(1477, v, options={"FAST"}); b.interpolation = "CONSTANT"
    fc.update()
# bed hands
for fc in fcs(M):
    if fc.data_path.startswith(('pose.bones["IK_hand.', 'pose.bones["Pole_elbow.', 'pose.bones["finger', 'pose.bones["wrist.')):
        for k in [k for k in fc.keyframe_points if 1478 <= k.co.x <= 1586][::-1]: fc.keyframe_points.remove(k)
        fc.update()
z = Vector((0, 0, 1))
for f in (1478, 1520, 1560, 1586):
    sc.frame_set(f)
    side = W("clavicle.R") - W("clavicle.L"); side.z = 0; side.normalize()           # his right, lying face up
    along = W("neck01") - W("pelvis.L"); along.z = 0; along.normalize()               # toward his head
    tgt = {"L": W("spine01") - side * 0.09 + z * 0.15, "R": W("pelvis.L") * 0.5 + W("pelvis.R") * 0.5 + side * 0.07 + along * 0.06 + z * 0.15}   # both on his belly
    for s, sg in (("L", -1), ("R", 1)):
        fd = (-side * sg + along * 0.3).normalized()                                  # fingers across his body
        place_hand(M, s, f, tgt[s], -z, fd); apply_pose(M, s, "relaxed", f)
        pole = M.pose.bones.get("Pole_elbow." + s)
        if pole:
            m = pole.matrix.copy(); m.translation = M.matrix_world.inverted() @ (W("upperarm01." + s) + side * (0.35 * sg) - along * 0.2); pole.matrix = m; vl.update()
            pole.keyframe_insert("location", frame=f, group=pole.name)
# bed camera from 1492: level (world-up track), from above his chest toward his face; no roll (list 35)
for fc in chans:
    for k in [k for k in fc.keyframe_points if 1492 <= k.co.x <= 1586][::-1]: fc.keyframe_points.remove(k)
    fc.update()
for f in list(range(1492, 1587, 4)) + [1586]:
    sc.frame_set(f); along = W("neck01") - W("pelvis.L"); along.z = 0; along.normalize(); h = W("head") + z * 0.05
    t = (f - 1492) / 94.0
    CAM.location = h - along * (0.62 - 0.12 * t) + z * 0.48; CAM.keyframe_insert("location", frame=f)
    AIM.location = h - along * 0.05; AIM.keyframe_insert("location", frame=f)
    CAM.data.lens = 38; CAM.data.keyframe_insert("lens", frame=f)
for fc in chans:
    for k in fc.keyframe_points:
        if abs(k.co.x - 1491) < 1.0 or abs(k.co.x - 1490) < 0.5: k.interpolation = "CONSTANT"
    fc.update()
print("FIX2 done")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
