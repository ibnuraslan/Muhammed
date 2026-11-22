"""v012b opening (client A, list 1-2): play -> pick a brick -> it goes up his nose. No hand through his legs.
 - Brick_Big rests on the rug beside his right hip (outside his legs) until he picks it up.
 - Right hand (IK, via hand_poses.place_hand + apply_pose): 1 resting on his knee, 22 reaching down beside his leg, 38-44 pinching the
   brick, 60-100 lifting it up in front of him and looking at it, 112 bringing it toward his face; the insertion keys from 120 stay.
 - The brick is baked to the thumb-index pinch every frame from the grab to 119 (one brick, never in mid-air).
 - Camera 1-100: an eased straight dolly between its 1 and 100 positions, kept >= 0.5 m up so it never runs into his knee or shoe.
blender -b in.blend --python v12_opening.py -- out.blend"""
import bpy, sys
from mathutils import Vector, Matrix
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; vl = bpy.context.view_layer
exec(open("/home/user/Muhammed/blender/pipeline/hand_poses.py").read())
B = bpy.data.objects["Boy"]; BR = bpy.data.objects["Brick_Big"]
def fcs(o): return [fc for l in o.animation_data.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def W(n, t=False): pb = B.pose.bones[n]; return B.matrix_world @ (pb.tail if t else pb.head)
# clear the old right-hand keys 1..119
for fc in fcs(B):
    if fc.data_path.startswith('pose.bones["IK_hand.R"]') or fc.data_path.startswith('pose.bones["Pole_elbow.R"]'):
        for k in [k for k in fc.keyframe_points if k.co.x < 120][::-1]: fc.keyframe_points.remove(k)
        fc.update()
SPOT = Vector((-0.16, -0.12, 0.012))
sc.frame_set(1); bb = [BR.matrix_world @ Vector(c) for c in BR.bound_box]; hh = (max(v.z for v in bb) - min(v.z for v in bb)) / 2
rest = Matrix.Translation(SPOT + Vector((0, 0, hh))) @ BR.matrix_world.to_3x3().normalized().to_4x4()
dn, fwd, up = Vector((0, 0, -1)), Vector((0, -1, 0)), Vector((0, 0, 1))
KEYS = [(1, W("lowerleg01.R") + Vector((0.0, -0.02, 0.07)), dn, fwd, "relaxed"),
        (22, SPOT + Vector((0, 0, 0.09)), dn, fwd, "relaxed"),
        (38, SPOT + Vector((0, 0, 0.05)), dn, fwd, "pinch"), (44, SPOT + Vector((0, 0, 0.05)), dn, fwd, "pinch"),
        (60, Vector((-0.08, -0.22, 0.30)), Vector((0.3, 0.2, 0.9)).normalized(), Vector((0.2, -0.9, 0.2)).normalized(), "pinch"),
        (80, Vector((0.0, -0.27, 0.42)), Vector((0.4, 0.6, 0.6)).normalized(), Vector((0.3, -0.8, 0.4)).normalized(), "pinch"),
        (100, Vector((0.05, -0.25, 0.47)), Vector((0.4, 0.6, 0.6)).normalized(), Vector((0.3, -0.7, 0.6)).normalized(), "pinch"),
        (112, Vector((0.09, -0.2, 0.53)), Vector((0.5, 0.6, 0.4)).normalized(), Vector((0.2, -0.5, 0.8)).normalized(), "pinch")]
for f, p, n, d, pose in KEYS:
    sc.frame_set(f); place_hand(B, "R", f, p, n, d); apply_pose(B, "R", pose, f)
# pole: elbow out to his right side
pole = B.pose.bones.get("Pole_elbow.R")
if pole:
    for f in (1, 40, 80, 112):
        sc.frame_set(f); m = pole.matrix.copy(); m.translation = B.matrix_world.inverted() @ (W("upperarm01.R") + Vector((-0.35, 0.1, -0.15))); pole.matrix = m; vl.update()
        pole.keyframe_insert("location", frame=f, group=pole.name)
# brick: on the rug until 38, then in the pinch to 119
for fc in [c for c in fcs(BR) if c.data_path in ("location", "rotation_euler", "rotation_quaternion")]:
    for k in [k for k in fc.keyframe_points if k.co.x < 120][::-1]: fc.keyframe_points.remove(k)
    fc.update()
def keyM(f, M):
    BR.matrix_world = M; vl.update(); BR.keyframe_insert("location", frame=f)
    BR.keyframe_insert("rotation_quaternion" if BR.rotation_mode == "QUATERNION" else "rotation_euler", frame=f)
keyM(1, rest); keyM(37, rest)
def pinch():
    t1 = B.matrix_world @ B.pose.bones["finger1-3.R"].tail; t2 = B.matrix_world @ B.pose.bones["finger2-3.R"].tail; return (t1 + t2) / 2
sc.frame_set(38); off = rest.translation - pinch()
for f in range(38, 120):
    sc.frame_set(f); w = smooth((f - 38) / 6.0)
    keyM(f, Matrix.Translation(pinch() + off * (1 - w)) @ rest.to_3x3().to_4x4())
# camera 1-100
CAM = bpy.data.objects["CAM_Film"]; cf = sorted([c for c in fcs(CAM) if c.data_path == "location"], key=lambda c: c.array_index)
c0 = Vector((-0.6, -1.3, 0.5)); c1 = Vector([cf[i].evaluate(100) for i in range(3)])   # start on his right-front: the pick-up is visible
for f in range(1, 101):
    p = c0.lerp(c1, smooth((f - 1) / 99.0)); p.z = max(p.z, 0.5)
    for i in range(3): cf[i].keyframe_points.insert(f, p[i], options={"FAST"})
for c in cf: c.update()
AIM = bpy.data.objects["CAM_Film_Aim"]; af = sorted([c for c in fcs(AIM) if c.data_path == "location"], key=lambda c: c.array_index)
orig = {f: Vector([af[i].evaluate(f) for i in range(3)]) for f in range(1, 121)}
for f in range(1, 121):                 # aim between his face and the pinching hand while he picks and lifts the brick
    sc.frame_set(f); face = W("head") + Vector((0, -0.05, 0.05))
    w = smooth((f - 1) / 12.0) * (1 - smooth((f - 105) / 15.0))
    tgt = face.lerp(pinch(), 0.45)
    p = orig[f].lerp(tgt, w)
    for i in range(3): af[i].keyframe_points.insert(f, p[i], options={"FAST"})
for c in af: c.update()
print("OPENING ok, brick rest", [round(x, 3) for x in rest.translation], "cam", [round(x, 2) for x in c0], "->", [round(x, 2) for x in c1])
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
