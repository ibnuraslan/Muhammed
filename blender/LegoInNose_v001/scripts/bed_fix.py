"""v008f (found by watching the preview): bedroom framing.
 - 1758-1796: the camera circled the bed with the man mostly out of frame (an arm at the edge) -> the aim blends onto his head.
 - 1836-1867: while the camera held its old framing he sat up out of it (back of his head, then a blank frame at ~1850) ->
   the camera-in-front-of-his-face hold (0.55 m out along his face, aimed at it) now starts at 1836, eased in over 6 frames.
blender -b in.blend --python bed_fix.py -- out.blend"""
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene
CAM, AIM, M = bpy.data.objects["CAM_Film"], bpy.data.objects["CAM_Film_Aim"], bpy.data.objects["Man"]
def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def fl(o): return sorted([c for l in o.animation_data.action.layers for st in l.strips for cb in st.channelbags for c in cb.fcurves if c.data_path == "location"], key=lambda c: c.array_index)
cf, af = fl(CAM), fl(AIM); ev = lambda F, f: Vector([F[i].evaluate(f) for i in range(3)])
def head(f):
    sc.frame_set(f); pb = M.pose.bones["head"]
    R = (M.matrix_world @ pb.matrix @ M.data.bones["head"].matrix_local.inverted()).to_3x3().normalized()
    fw = R @ Vector((0, -1, 0)); up = R @ Vector((0, 0, 1)); return M.matrix_world @ pb.head + up * 0.09, fw, up
new_a, new_c = {}, {}
for f in range(1758, 1797):
    H, fw, up = head(f); w = smooth((f - 1758) / 6.0) if f < 1790 else 1 - smooth((f - 1790) / 6.0)
    new_a[f] = ev(af, f).lerp(H, w)
for f in range(1836, 1868):
    H, fw, up = head(f); w = smooth((f - 1836) / 6.0)
    new_c[f] = ev(cf, f).lerp(H + fw * 0.55 + up * 0.06, w); new_a[f] = ev(af, f).lerp(H + fw * 0.03, w)
for f, p in new_a.items():
    for i in range(3): af[i].keyframe_points.insert(f, p[i], options={"FAST"})
for f, p in new_c.items():
    for i in range(3): cf[i].keyframe_points.insert(f, p[i], options={"FAST"})
for c in cf + af: c.update()
print("BEDFIX ok"); bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
