"""v008c post-pass (director's v008b review):
 - beat 6 (f1087): the aim swung to the empty sofa on the way to the nostril dive -> the aim holds the boy's nose 1082-1092, blends back by 1098
 - beat 9 (f1867): blank wall between the bedroom macro and the shower -> the camera holds the man's face (old 1835-1840) until
   1867, then one eased move to the shower framing 1867-1882 (the 1871-1892 wall-hide window covers the crossing) (the wall crossing lands inside the 1872-1880 wall-hide window)
 - tweezers: keyed every frame 960-1145 with the origin in Mom's right pinch; the brick in the tips moves with them
blender -b in.blend --python fix_v8c.py -- out.blend"""
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene
def fcs(o):
    return [fc for l in o.animation_data.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
CAM, AIM = bpy.data.objects["CAM_Film"], bpy.data.objects["CAM_Film_Aim"]
# ---- beat 9 remap (camera + aim + lens + every camera fcurve sampled before editing)
def remap(f):
    if f <= 1835 or f >= 1882: return f
    if f <= 1867: return 1835 + (f - 1835) * (5.0 / 32.0)      # hold his face (old 1835-1840)
    return 1840 + (f - 1867) * (42.0 / 15.0)                   # old 1840-1882 pass, wall crossing inside the 1872-1880 hide window
for o in (CAM, AIM, CAM.data):
    if not o.animation_data: continue
    for fc in fcs(o):
        vals = {f: fc.evaluate(remap(f)) for f in range(1835, 1883)}
        for kp in [k for k in fc.keyframe_points if 1835 < k.co.x < 1882][::-1]: fc.keyframe_points.remove(kp)
        for f, v in vals.items(): fc.keyframe_points.insert(f, v, options={"FAST"})
        fc.update()
# ---- beat 9 face hold: he is getting up while the camera holds, so frame his face directly 1856-1867 (blend in from 1848, out by 1873)
M = bpy.data.objects["Man"]; vl = bpy.context.view_layer
cfc = sorted([fc for fc in fcs(CAM) if fc.data_path == "location"], key=lambda c: c.array_index)
afc0 = sorted([fc for fc in fcs(AIM) if fc.data_path == "location"], key=lambda c: c.array_index)
FH = {}
for f in range(1848, 1868):
    sc.frame_set(f); pb = M.pose.bones["head"]
    R = (M.matrix_world @ pb.matrix @ M.data.bones["head"].matrix_local.inverted()).to_3x3().normalized()
    fw = R @ Vector((0, -1, 0)); upv = R @ Vector((0, 0, 1)); H = M.matrix_world @ pb.head + upv * 0.09
    w = smooth((f - 1848) / 8.0) if f <= 1867 else 1 - smooth((f - 1867) / 6.0)
    c0 = Vector([cfc[i].evaluate(f) for i in range(3)]); a0 = Vector([afc0[i].evaluate(f) for i in range(3)])
    FH[f] = (c0.lerp(H + fw * 0.55 + upv * 0.06, w), a0.lerp(H + fw * 0.03, w))
for f, (cp, ap) in FH.items():
    for i in range(3): cfc[i].keyframe_points.insert(f, cp[i], options={"FAST"}); afc0[i].keyframe_points.insert(f, ap[i], options={"FAST"})
for c in cfc + afc0: c.update()
# one eased move from his face (1867) to the shower framing (1882); the wall is hidden from the camera 1871-1892
c0, a0 = FH[1867]; c1 = Vector([cfc[i].evaluate(1882) for i in range(3)]); a1 = Vector([afc0[i].evaluate(1882) for i in range(3)])
for f in range(1868, 1882):
    t = smooth((f - 1867) / 15.0); cp, ap = c0.lerp(c1, t), a0.lerp(a1, t)
    for i in range(3): cfc[i].keyframe_points.insert(f, cp[i], options={"FAST"}); afc0[i].keyframe_points.insert(f, ap[i], options={"FAST"})
for c in cfc + afc0: c.update()
print("FIXV8C beat9 move", tuple(round(x, 2) for x in c0), "->", tuple(round(x, 2) for x in c1))
# ---- beat 6 aim
B = bpy.data.objects["Boy"]
def boy_nose(f):
    sc.frame_set(f); h = B.pose.bones["head"]; return B.matrix_world @ (h.head + (h.tail - h.head) * 0.35) + (B.matrix_world.to_3x3() @ (h.matrix.to_3x3() @ Vector((0, 0.0, 0.0))))
afc = sorted([fc for fc in fcs(AIM) if fc.data_path == "location"], key=lambda c: c.array_index)
new = {}
for f in range(1076, 1099):
    w = smooth((f - 1076) / 6.0) if f < 1092 else 1 - smooth((f - 1092) / 6.0)
    orig = Vector([afc[i].evaluate(f) for i in range(3)]); n = boy_nose(f)
    new[f] = orig.lerp(n, w)
for f, p in new.items():
    for i in range(3): afc[i].keyframe_points.insert(f, p[i], options={"FAST"})
for c in afc: c.update()
# ---- tweezers in the pinch
W = bpy.data.objects["Mom"]; TW = bpy.data.objects["Prop_Tweezers"]; BR = bpy.data.objects["Brick_Big"]
def pinch(): return (W.matrix_world @ W.pose.bones["finger1-3.R"].tail + W.matrix_world @ W.pose.bones["finger2-3.R"].tail) / 2
tf = sorted([fc for fc in fcs(TW) if fc.data_path == "location"], key=lambda c: c.array_index)
bf = sorted([fc for fc in fcs(BR) if fc.data_path == "location"], key=lambda c: c.array_index)
for it in range(3):
    dl = {}
    for f in range(960, 1146):
        sc.frame_set(f); dl[f] = pinch() - TW.matrix_world.translation
    for f, d in dl.items():
        for i in range(3): tf[i].keyframe_points.insert(f, tf[i].evaluate(f) + d[i], options={"FAST"})
        if f >= 1042:
            w = smooth((f - 1042) / 14.0)
            for i in range(3): bf[i].keyframe_points.insert(f, bf[i].evaluate(f) + d[i] * w, options={"FAST"})
    for c in tf + bf: c.update()
ds = []
for f in range(960, 1146):
    sc.frame_set(f); ds.append((TW.matrix_world.translation - pinch()).length)
print("FIXV8C tweezers max %.1f mm mean %.1f mm worst f%d" % (max(ds) * 1000, sum(ds) / len(ds) * 1000, 960 + ds.index(max(ds))))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("FIXV8C saved", OUT)
