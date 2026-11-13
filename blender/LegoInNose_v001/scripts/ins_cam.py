"""v008e: the camera orbits about the boy's head toward his left (the nostril the brick goes into) during the push, so the
thumb/index tips at the nostril read in 3/4 profile instead of the fist covering the face from the front.
blender -b in.blend --python ins_cam.py -- out.blend ANGLE f_in0 f_in1 f_out0 f_out1 [range2 ...]"""
import bpy, sys, math
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; ANG = float(a[1]); R = [tuple(int(x) for x in a[i:i + 4]) for i in range(2, len(a), 4)]
sc = bpy.context.scene; CAM = bpy.data.objects["CAM_Film"]; B = bpy.data.objects["Boy"]
def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def fcs(o): return [fc for l in o.animation_data.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
cf = sorted([fc for fc in fcs(CAM) if fc.data_path == "location"], key=lambda c: c.array_index)
for f0, f1, f2, f3 in R:
    new = {}
    for f in range(f0, f3 + 1):
        sc.frame_set(f); pb = B.pose.bones["head"]; Hm = B.matrix_world @ pb.matrix @ B.data.bones["head"].matrix_local.inverted()
        H = B.matrix_world @ pb.head; left = (Hm.to_3x3() @ Vector((1, 0, 0))); left.z = 0; left.normalize()
        c = Vector([cf[i].evaluate(f) for i in range(3)]); v = c - H; v2 = v.copy(); v2.z = 0
        cr = v2.normalized().cross(left).z      # rotate the camera toward the side his +X (left) points to
        w = smooth((f - f0) / (f1 - f0)) if f < f1 else (1.0 if f <= f2 else 1 - smooth((f - f2) / (f3 - f2)))
        ang = math.radians(ANG) * w * (1 if cr >= 0 else -1)
        new[f] = H + Matrix.Rotation(ang, 3, "Z") @ v
    for f, p in new.items():
        for i in range(3): cf[i].keyframe_points.insert(f, p[i], options={"FAST"})
    for c in cf: c.update()
    print("INSCAM", f0, f3, ANG)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("INSCAM saved", OUT)
