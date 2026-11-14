"""v008f: 15.75 s synced (old ~1088-1100): on the way from the beat-6 face to the second nostril dive the camera passed behind the
boy's arm (a blurred striped sleeve filled the frame). Now the camera eases from its 1087 position to a waypoint 10 cm out of the nostril
(below/in front) by 1096, then into its 1101 position (the nostril entry), and the aim holds the nostril until 1100, then blends into the dive aim inside the tunnel (1101-1114).
blender -b in.blend --python dive2_cam.py -- out.blend"""
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene
CAM, AIM, B = bpy.data.objects["CAM_Film"], bpy.data.objects["CAM_Film_Aim"], bpy.data.objects["Boy"]
def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def fcs(o): return [fc for l in o.animation_data.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
cf = sorted([c for c in fcs(CAM) if c.data_path == "location"], key=lambda c: c.array_index)
af = sorted([c for c in fcs(AIM) if c.data_path == "location"], key=lambda c: c.array_index)
ev = lambda fl, f: Vector([fl[i].evaluate(f) for i in range(3)])
c0, c1 = ev(cf, 1087), ev(cf, 1101); A_ORIG = {f: ev(af, f) for f in range(1088, 1115)}
import json, os
_aj = os.environ.get("AIM_ORIG")                # re-run on an already-patched file: give the pre-patch aim values
if _aj: A_ORIG = {int(k): Vector(v) for k, v in json.load(open(_aj)).items()}
def nose(f):
    sc.frame_set(f); h = B.pose.bones["head"]; return B.matrix_world @ (h.head + (h.tail - h.head) * 0.35)
def headM(f):
    sc.frame_set(f); return B.matrix_world @ B.pose.bones["head"].matrix @ B.data.bones["head"].matrix_local.inverted()
NOS_L = headM(1000).inverted() @ bpy.data.objects["Brick_Big"].matrix_world.translation.copy()   # lodged brick = the nostril
def nostril(f): return headM(f) @ NOS_L
def into(f):        # 12 cm INTO the nose along the dive line: stays ahead of the camera as it enters (no flip at the entry)
    Hm = headM(f); R = Hm.to_3x3().normalized(); fw = R @ Vector((0, -1, 0)); up = R @ Vector((0, 0, 1))
    return nostril(f) + (up * 0.8 - fw * 0.6).normalized() * 0.12
def wp(f):     # 10 cm out of the nostril, below and in front (the dive's own approach line)
    sc.frame_set(f); Hm = B.matrix_world @ B.pose.bones["head"].matrix @ B.data.bones["head"].matrix_local.inverted()
    R = Hm.to_3x3().normalized(); fw = R @ Vector((0, -1, 0)); up = R @ Vector((0, 0, 1))
    return nostril(f) + (fw * 0.6 - up * 0.8).normalized() * 0.10
new = {}
for f in range(1088, 1101):
    if f <= 1096: cp = c0.lerp(wp(f), smooth((f - 1087) / 9.0))
    else: cp = wp(f).lerp(c1, smooth((f - 1096) / 5.0))
    new[f] = (cp, nostril(f).lerp(into(f), smooth((f - 1090) / 6.0)))   # the aim holds the nostril, then looks into it
for f in range(1101, 1115):                        # inside the tunnel (only its walls render): blend back to the dive aim
    new[f] = (None, into(f).lerp(A_ORIG[f], smooth((f - 1100) / 14.0)))
for f, (cp, ap) in new.items():
    for i in range(3):
        if cp is not None: cf[i].keyframe_points.insert(f, cp[i], options={"FAST"})
        af[i].keyframe_points.insert(f, ap[i], options={"FAST"})
for c in cf + af: c.update()
print("DIVE2CAM", tuple(round(x, 2) for x in c0), "->", tuple(round(x, 2) for x in c1))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
