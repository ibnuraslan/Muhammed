"""v008c: Mom's left (chin-cradle) hand 1.5 cm further off the boy's chin, 1005-1031 (eased), so clip_scan (skin-only targets)
no longer counts her fingers inside his jaw at 16.9-17.0 s. blender -b in.blend --python chin_ease.py -- out.blend"""
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; vl = bpy.context.view_layer
A = bpy.data.objects["Mom"]; B = bpy.data.objects["Boy"]; IK = A.pose.bones["IK_hand.L"]
def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
new = {}
for f in range(1005, 1032):
    sc.frame_set(f); chin = B.matrix_world @ B.pose.bones["jaw"].tail; h = A.matrix_world @ A.pose.bones["wrist.L"].head
    w = smooth((f - 1005) / 6) if f < 1025 else 1 - smooth((f - 1025) / 6)
    m = IK.matrix.copy(); m.translation = m.translation + A.matrix_world.inverted().to_3x3() @ ((h - chin).normalized() * 0.015 * w); new[f] = m
for f, m in new.items():
    sc.frame_set(f); IK.matrix = m; vl.update(); IK.keyframe_insert("location", frame=f, group=IK.name)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("CHIN saved", OUT)
