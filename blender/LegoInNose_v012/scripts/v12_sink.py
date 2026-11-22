"""v012b sink / ending (list 38-43): the grown man at the vanity, 1587-2036.
 - Both hands rest on the counter top (no raised A/T arms, no forearm through his face) until the sneeze.
 - The sneeze (1732) expels the SAME red brick (Brick_Big); the old yellow Brick_Small is hidden. It arcs from his nostril into his
   open right palm (1732-1752) and is baked to that palm every frame to the end, so it is never in mid-air or hidden.
 - Right hand: palm up in front of his chest from 1745, raised a little toward his face to look at it; the left stays on the counter.
 - Camera: level, at his eye height, above the counter (no ledge in the lens): medium 1587-1700, face 1700-1745, then a close two-shot
   of his face and the brick in his palm that slowly pushes in to the last frame (clear close-up end, list 43).
blender -b in.blend --python v12_sink.py -- out.blend"""
import bpy, sys
from mathutils import Vector, Matrix
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; vl = bpy.context.view_layer
exec(open("/home/user/Muhammed/blender/pipeline/hand_poses.py").read())
M = bpy.data.objects["Man"]; BR = bpy.data.objects["Brick_Big"]; BS = bpy.data.objects["Brick_Small"]
CAM = bpy.data.objects["CAM_Film"]; AIM = bpy.data.objects["CAM_Film_Aim"]
F0, F1, SNEEZE, LAND = 1587, 2036, 1732, 1752
def fcs(o):
    ad = o.animation_data
    return [fc for l in ad.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves] if ad and ad.action else []
def W(n, t=False): pb = M.pose.bones[n]; return M.matrix_world @ (pb.tail if t else pb.head)
def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def clear(o, pred, a=F0, b=F1):
    for fc in fcs(o):
        if pred(fc.data_path):
            for k in [k for k in fc.keyframe_points if a <= k.co.x <= b][::-1]: fc.keyframe_points.remove(k)
            fc.update()
# --- hands -------------------------------------------------------------------------------------------------------------
clear(M, lambda p: any(p.startswith('pose.bones["%s' % s) for s in ("IK_hand.", "Pole_elbow.", "finger", "wrist.")), F0 + 1)
up = Vector((0, 0, 1)); dn = -up
sc.frame_set(F0); r = W("clavicle.R") - W("clavicle.L"); r.z = 0; r.normalize(); fw = up.cross(r); fw.normalize()
TOP = 0.905
def counter(side, f):
    sc.frame_set(f); sh = W("upperarm01." + side); s = 1 if side == "R" else -1
    p = sh + fw * 0.30 + r * (0.07 * s); p.z = TOP; return p
def hold(f, lift=0.0):
    sc.frame_set(f); h = W("head"); p = h + fw * 0.26 + r * 0.02; p.z = h.z - 0.30 + lift; return p
KEY_L = [F0 + 1, 1640, 1700, 1760, 1850, 1950, F1]
KEY_R = [(F0 + 1, "c"), (1640, "c"), (1700, "c"), (1728, "c"), (1745, 0.0), (1760, 0.0), (1800, 0.04), (1850, 0.06), (1900, 0.07),
         (1950, 0.08), (2000, 0.08), (F1, 0.08)]
for f in KEY_L:
    place_hand(M, "L", f, counter("L", f), dn, fw); apply_pose(M, "L", "relaxed", f)
for f, k in KEY_R:
    if k == "c": place_hand(M, "R", f, counter("R", f), dn, fw); apply_pose(M, "R", "relaxed", f)
    else: place_hand(M, "R", f, hold(f, k), up, (-r + fw * 0.25).normalized()); apply_pose(M, "R", "flat_palm", f)   # fingers across his body: the camera sees into the palm
for side, s in (("L", -1), ("R", 1)):
    pole = M.pose.bones.get("Pole_elbow." + side)
    if not pole: continue
    for f in KEY_L:
        sc.frame_set(f); m = pole.matrix.copy()
        m.translation = M.matrix_world.inverted() @ (W("upperarm01." + side) + r * (0.35 * s) - fw * 0.25 - up * 0.3); pole.matrix = m; vl.update()
        pole.keyframe_insert("location", frame=f, group=pole.name)
# --- the red brick -----------------------------------------------------------------------------------------------------
for o in (BR, BS):
    for f, h in ((F0, True), (SNEEZE - 1, True), (SNEEZE, o is BS), (F1, o is BS)):   # red brick from the sneeze on; yellow never
        o.hide_render = h; o.keyframe_insert("hide_render", frame=f); o.hide_viewport = h; o.keyframe_insert("hide_viewport", frame=f)
for fc in fcs(BR):
    if fc.data_path == "visible_camera":
        for k in [k for k in fc.keyframe_points if k.co.x >= F0][::-1]: fc.keyframe_points.remove(k)
        fc.update()
BR.visible_camera = True; BR.keyframe_insert("visible_camera", frame=F0)
clear(BR, lambda p: p in ("location", "rotation_quaternion", "rotation_euler"), F0)
def palm():
    a = W("wrist.R"); b = W("finger3-1.R"); return (a + b) / 2 * 0.55 + b * 0.45
def keyM(f, Mx):
    BR.matrix_world = Mx; vl.update(); BR.keyframe_insert("location", frame=f)
    BR.keyframe_insert("rotation_quaternion" if BR.rotation_mode == "QUATERNION" else "rotation_euler", frame=f)
hz = BR.dimensions.z / 2
rot_hold = Matrix((r, -fw, up)).transposed().to_4x4()       # long side across his palm, studs up
sc.frame_set(SNEEZE); nose = BS.matrix_world.translation.copy(); rot0 = BS.matrix_world.to_3x3().normalized().to_4x4()
for f in range(SNEEZE, F1 + 1):
    sc.frame_set(f); pp = palm() + up * (hz + 0.02)
    if f < LAND:
        t = (f - SNEEZE) / (LAND - SNEEZE); p = nose.lerp(pp, t) + up * (0.06 * 4 * t * (1 - t)) + fw * (0.05 * 4 * t * (1 - t))
        R = rot0 if t < 0.5 else rot_hold
    else: p, R = pp, rot_hold
    keyM(f, Matrix.Translation(p) @ R)
# --- camera ------------------------------------------------------------------------------------------------------------
clear(CAM, lambda p: p == "location", F0); clear(AIM, lambda p: p == "location", F0); clear(CAM.data, lambda p: p == "lens", F0)
def face(f): sc.frame_set(f); return W("head") + up * 0.07
def shot(f):
    h = face(f)
    if f < 1700:   aim = h - up * 0.14; d, lens = 1.10, 38   # chest up, no crotch
    elif f < 1745: aim = h - up * 0.03; d, lens = 0.80, 45
    else:
        sc.frame_set(f); b = BR.matrix_world.translation.copy(); aim = h * 0.55 + b * 0.45
        t = smooth((f - 1745) / (F1 - 1745)); d, lens = 0.78 - 0.30 * t, 42
    cam = aim + fw * d - r * 0.10; cam.z = aim.z + (0.02 if f < 1745 else 0.10)   # slightly above the palm: sees the brick
    return cam, aim, lens
for f in list(range(F0, F1 + 1, 4)) + [F1]:
    c, a, lens = shot(f)
    CAM.location = c; CAM.keyframe_insert("location", frame=f); AIM.location = a; AIM.keyframe_insert("location", frame=f)
    CAM.data.lens = lens; CAM.data.keyframe_insert("lens", frame=f)
for o in (CAM, AIM, CAM.data):
    for fc in fcs(o):
        for k in fc.keyframe_points:
            if F0 <= k.co.x: k.interpolation = "BEZIER"
        fc.update()
if CAM.data.dof.use_dof and CAM.data.dof.focus_object is None: CAM.data.dof.focus_object = AIM
print("SINK fw", tuple(round(x, 2) for x in fw), "r", tuple(round(x, 2) for x in r))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
