"""v012b boy section (list 4, 6, 10, 12-14, 18, 22-24; client B, D, E):
 - the red brick sits INSIDE the nostril (0.6 cm deeper along the nostril axis than before: only a small tip shows), fixed size,
   from 151 on; Mom's tweezers FAIL: the brick never leaves his nose (no brick in the tweezers, list 23).
 - cutaway: both bricks stay in the nasal passage (the red one no longer leaves in the second cutaway, list 18).
 - the floating dream bricks are gone (v12_global); 380-495 now frames his face with the yellow brick in his hand (sharp).
 - flailing arms (730-800, 875-925): the hands come 35% closer to his chest, so the elbows bend (no A/T pose, list 14).
 - the tweezers are thicker so they read in the shot (list 22).
blender -b in.blend --python v12_boy.py -- out.blend"""
import bpy, sys
from mathutils import Vector, Matrix
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; vl = bpy.context.view_layer
B = bpy.data.objects["Boy"]; BR = bpy.data.objects["Brick_Big"]
def fcs(o): return [fc for l in o.animation_data.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves] if o.animation_data and o.animation_data.action else []
def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def headM(): pb = B.pose.bones["head"]; return B.matrix_world @ pb.matrix @ B.data.bones["head"].matrix_local.inverted()
def keyM(o, f, M):
    o.matrix_world = M; vl.update(); o.keyframe_insert("location", frame=f)
    o.keyframe_insert("rotation_quaternion" if o.rotation_mode == "QUATERNION" else "rotation_euler", frame=f)
# 1. brick deeper, and stuck through Mom's attempt
sc.frame_set(880); STUCK = headM().inverted() @ BR.matrix_world.copy()          # head-space pose while stuck (before the tweezers)
R0 = headM().to_3x3().normalized(); fw = R0 @ Vector((0, -1, 0)); up = R0 @ Vector((0, 0, 1))
into_l = R0.inverted() @ (up * 0.8 - fw * 1.0).normalized()                       # into the nose, head space
DEEP = Matrix.Translation(into_l * 0.006) @ STUCK
new = {}
for f in range(151, 994):
    sc.frame_set(f); H = headM()
    if f < 880:
        cur = H.inverted() @ BR.matrix_world.copy(); w = smooth((f - 151) / 6.0)
        new[f] = H @ (Matrix.Translation(into_l * 0.006 * w) @ cur)
    else:
        new[f] = H @ DEEP
for fc in [c for c in fcs(BR) if c.data_path in ("location", "rotation_euler", "rotation_quaternion")]:
    for k in [k for k in fc.keyframe_points if 151 <= k.co.x < 994][::-1]: fc.keyframe_points.remove(k)
    fc.update()
for f, M in new.items(): keyM(BR, f, M)
# 2. cutaway: the red brick stays in the passage (it used to shrink away when the tweezers "removed" it)
X = bpy.data.objects["XS_Brick_Big"]; sc.frame_set(960); XM = X.matrix_world.copy()
XM.translation.y = bpy.data.objects["XS_Brick_Small"].matrix_world.translation.y + 0.005      # same cut plane as the yellow one
for fc in fcs(X):
    for k in [k for k in fc.keyframe_points if k.co.x > 960][::-1]: fc.keyframe_points.remove(k)
    fc.update()
X.matrix_world = XM; vl.update()
for path in ("location", "rotation_euler", "rotation_quaternion", "scale"):
    try:
        X.keyframe_insert(path, frame=961); X.keyframe_insert(path, frame=1300)
    except Exception: pass
# brain: pink tissue instead of a white blob (list 17)
bm_ = bpy.data.materials.get("XS_Brain_M")
if bm_:
    for n in bm_.node_tree.nodes:
        if n.type == "VALTORGB":
            el = n.color_ramp.elements; el[0].color = (0.72, 0.42, 0.46, 1); el[-1].color = (0.93, 0.7, 0.72, 1)
# 3. dream window: his face + the yellow brick in his hand
CAM, AIM = bpy.data.objects["CAM_Film"], bpy.data.objects["CAM_Film_Aim"]
cf = sorted([c for c in fcs(CAM) if c.data_path == "location"], key=lambda c: c.array_index); af = sorted([c for c in fcs(AIM) if c.data_path == "location"], key=lambda c: c.array_index)
SM = bpy.data.objects["Brick_Small"]; cv = {}
for f in range(380, 496):
    sc.frame_set(f); H = headM(); R = H.to_3x3().normalized(); fwv = R @ Vector((0, -1, 0)); hd = B.matrix_world @ B.pose.bones["head"].head + R @ Vector((0, 0, 0.07))
    w = smooth((f - 380) / 8.0) * (1 - smooth((f - 487) / 8.0))
    tgt = hd.lerp(SM.matrix_world.translation, 0.35)
    cpos = tgt + fwv * 0.6 + Vector((0, 0, 0.05))
    c0 = Vector([cf[i].evaluate(f) for i in range(3)]); a0 = Vector([af[i].evaluate(f) for i in range(3)])
    cv[f] = (c0.lerp(cpos, w), a0.lerp(tgt, w))
for f, (c, a_) in cv.items():
    for i in range(3): cf[i].keyframe_points.insert(f, c[i], options={"FAST"}); af[i].keyframe_points.insert(f, a_[i], options={"FAST"})
for c in cf + af: c.update()
# 4. bend the flailing arms
def W(n, t=False): pb = B.pose.bones[n]; return B.matrix_world @ (pb.tail if t else pb.head)
for s in "LR":
    ik = B.pose.bones["IK_hand." + s]; vals = {}
    for f in list(range(730, 801)) + list(range(875, 926)):
        sc.frame_set(f); chest = W("spine03") + Vector((0, -0.12, 0.05)); hp = B.matrix_world @ ik.matrix.translation
        a, b = (730, 800) if f <= 800 else (875, 925); w = smooth((f - a) / 8.0) * (1 - smooth((f - (b - 8)) / 8.0))
        vals[f] = hp.lerp(chest, 0.35 * w)
    for f, p in vals.items():
        sc.frame_set(f); m = ik.matrix.copy(); m.translation = B.matrix_world.inverted() @ p; ik.matrix = m; vl.update(); ik.keyframe_insert("location", frame=f, group=ik.name)
# 5. tweezers thicker
for o in bpy.data.objects:
    if o.name.startswith("Prop_TweezerArm"): o.scale = (o.scale[0] * 2.6, o.scale[1], o.scale[2] * 2.6)
print("BOY ok")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
