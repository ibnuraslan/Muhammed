"""v012b client B (list 6): the red brick read as a block stuck ACROSS the outside of his nostril (long side showing).
It is now turned lengthwise along the nostril axis and pushed in so only its 3.5 mm end (the 0.8 x 1.1 cm face) shows:
 - 120-131 the fingers carry it in (blend from the pinch pose to the inserted pose), 132-993 it stays in that head-space pose,
   through Mom's failed tweezer attempt; it then stays visible (stuck) on the boy to 1229 instead of vanishing (list 10).
blender -b in.blend --python v12_nostril.py -- out.blend"""
import bpy, sys
from mathutils import Vector, Matrix
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; vl = bpy.context.view_layer
B = bpy.data.objects["Boy"]; BR = bpy.data.objects["Brick_Big"]
def fcs(o): return [fc for l in o.animation_data.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def headM(): pb = B.pose.bones["head"]; return B.matrix_world @ pb.matrix @ B.data.bones["head"].matrix_local.inverted()
F_IN, F_SET, F_END, F_BOY = 120, 132, 993, 1229
sc.frame_set(400); H = headM(); E = (H.inverted() @ BR.matrix_world).translation.copy() + Vector((-0.0012, 0, -0.002))   # nostril opening, head space (nudged to the canal centre)
R0 = H.to_3x3().normalized(); fw = R0 @ Vector((0, -1, 0)); up = R0 @ Vector((0, 0, 1))
A = (R0.inverted() @ (up * 0.15 - fw * 1.0)).normalized()                                       # into the nose, head space: mostly straight back (steeper pokes through the nose wall)
Z = Vector((1, 0, 0)); Z = (Z - A * Z.dot(A)).normalized(); Y = Z.cross(A)   # 1.1 cm side across, 0.8 cm side vertical: fits the nostril
half = BR.dimensions.x / 2                                                                     # long axis = local X
POSE = Matrix.Translation(E + A * (half - 0.0035)) @ Matrix((A, Y, Z)).transposed().to_4x4()
new = {}
for f in range(F_IN, F_BOY + 1):
    sc.frame_set(f); H = headM()
    if f < F_SET:
        cur = H.inverted() @ BR.matrix_world.copy(); w = smooth((f - F_IN) / (F_SET - F_IN))
        q = cur.to_quaternion().slerp(POSE.to_quaternion(), w)
        new[f] = H @ (Matrix.Translation(cur.translation.lerp(POSE.translation, w)) @ q.to_matrix().to_4x4())
    else: new[f] = H @ POSE
for fc in [c for c in fcs(BR) if c.data_path in ("location", "rotation_euler", "rotation_quaternion")]:
    for k in [k for k in fc.keyframe_points if F_IN <= k.co.x <= F_BOY][::-1]: fc.keyframe_points.remove(k)
    fc.update()
for f, Mx in new.items():
    BR.matrix_world = Mx; vl.update(); BR.keyframe_insert("location", frame=f)
    BR.keyframe_insert("rotation_quaternion" if BR.rotation_mode == "QUATERNION" else "rotation_euler", frame=f)
for fc in fcs(BR):
    if fc.data_path in ("hide_render", "hide_viewport"):
        for k in fc.keyframe_points:
            if 994 < k.co.x < 995: k.co.x = k.handle_left.x = k.handle_right.x = F_BOY + 0.5
        fc.update()
print("NOSTRIL E", tuple(round(x, 4) for x in E), "A", tuple(round(x, 3) for x in A), "protrude 3.5 mm")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
