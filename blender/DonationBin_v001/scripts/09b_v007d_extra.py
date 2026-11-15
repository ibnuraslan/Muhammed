"""DonationBin v007d extras (director, Nov 15), applied after 09_v007d_patch.py.
blender -b in.blend --python 09b_v007d_extra.py -- out.blend
1. The dark puddle discs on the asphalt (read as black holes at 1-26 and 2261-2400) are removed.
2. 166-200: the shover's palms push on her hips, on the surface on his side; his arms stay outside her body.
3. 1162-1179: the in-between hand keys that flung her arms up before the wall-bang are removed (straight move)."""
import sys, math
import bpy
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
rm = [o for o in bpy.data.objects if o.name.startswith("Puddle")]
for o in rm: bpy.data.objects.remove(o, do_unlink=True)
print("PUDDLES_REMOVED", len(rm))
WO = bpy.data.objects["Woman"]; SH = bpy.data.objects["Shover"]
def W(r, b): return r.matrix_world @ r.pose.bones[b].head
for g in (160, 206):
    sc.frame_set(g)
    for s in "LR":
        pb = SH.pose.bones["IK_hand." + s]
        pb.keyframe_insert("location", frame=g, group=pb.name); pb.keyframe_insert("rotation_quaternion", frame=g, group=pb.name)
n = 0
for f in range(166, 201, 4):
    sc.frame_set(f)
    hip = W(WO, "spine05"); lat = (W(WO, "upperleg01.L") - W(WO, "upperleg01.R")); lat.z = 0
    lat = lat.normalized() if lat.length > 1e-3 else Vector((1, 0, 0))
    to_sh = W(SH, "spine03") - hip; to_sh.z = 0; to_sh = to_sh.normalized()
    sideL = 1 if (W(SH, "wrist.L") - W(SH, "wrist.R")).dot(lat) > 0 else -1     # his hands stay on their own sides
    for s in "LR":
        hs = W(SH, "wrist." + s)
        side = sideL if s == "L" else -sideL
        tgt = hip + lat * side * 0.10 + to_sh * 0.17 + Vector((0, 0, -0.04))
        pb = SH.pose.bones["IK_hand." + s]; M = pb.matrix.copy()
        M.translation += SH.matrix_world.inverted().to_3x3() @ (tgt - hs)
        pb.matrix = M; pb.keyframe_insert("location", frame=f, group=pb.name); n += 1
print("SHOVER_HIPS", n)
nk = 0
ad = WO.animation_data
for l in ad.action.layers:
    for st in l.strips:
        for cb in st.channelbags:
            for fc in cb.fcurves:
                if fc.data_path.startswith('pose.bones["IK_hand.') or fc.data_path.startswith('pose.bones["Pole_elbow.'):
                    for kp in [k for k in fc.keyframe_points if 1162 <= k.co.x <= 1179][::-1]:
                        fc.keyframe_points.remove(kp); nk += 1
                    fc.update()
print("FLING_KEYS_REMOVED", nk)
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("V007D_EXTRA_DONE")
