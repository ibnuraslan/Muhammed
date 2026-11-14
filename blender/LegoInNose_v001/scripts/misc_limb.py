"""v008f: the last limb_check flags.
 - ARMBACK, Man arm.L ~1841 (sitting up in bed): where the wrist is > 15 cm behind the shoulder plane (limb_check's test), the IK
   hand is moved forward until it is 12 cm behind, every frame 1826-1856.
 - PROPHEAD, shower water streaks crossing the man's head: those FX_Water objects are hidden 2 frames either side of each flag.
blender -b in.blend --python misc_limb.py -- out.blend limb.json"""
import bpy, sys, json
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; LJ = json.load(open(a[1]))["frames"]; sc = bpy.context.scene
M = bpy.data.objects["Man"]
def W(n, tail=False): pb = M.pose.bones[n]; return M.matrix_world @ (pb.tail if tail else pb.head)
def fcs(o): return [fc for l in o.animation_data.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
n_back = 0
for it in range(4):
    for f in range(1826, 1857):
        sc.frame_set(f)
        up = (W("neck01") - W("spine05")).normalized(); side = (W("upperarm01.R") - W("upperarm01.L")).normalized(); fwd = up.cross(side).normalized()
        if (W("jaw", True) - W("head")).dot(fwd) < 0: fwd = -fwd
        sh = W("upperarm01.L"); wr = W("wrist.L"); back = -(wr - sh).dot(fwd)
        if back > 0.15:
            d = fwd * (back - 0.12); n = "IK_hand.L"
            dl = M.data.bones[n].matrix_local.to_3x3().inverted() @ (M.matrix_world.to_3x3().inverted() @ d)
            for fc in [c for c in fcs(M) if c.data_path == 'pose.bones["%s"].location' % n]: fc.keyframe_points.insert(f, fc.evaluate(f) + dl[fc.array_index], options={"FAST"})
            n_back += 1
    for fc in fcs(M): fc.update()
hid = []
for f, v in LJ.items():
    for k, m in v:
        if k == "PROPHEAD" and m.startswith("FX_Water"):
            o = bpy.data.objects[m.split()[0]]; f = int(f)
            o.hide_render = False; o.keyframe_insert("hide_render", frame=f - 3)
            o.hide_render = True
            for g in range(f - 2, f + 3): o.keyframe_insert("hide_render", frame=g)
            o.hide_render = False; o.keyframe_insert("hide_render", frame=f + 3); hid.append((o.name, f))
for o in {bpy.data.objects[n] for n, _ in hid}:
    for fc in fcs(o):
        if fc.data_path == "hide_render":
            for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
print("MISCLIMB armback keys", n_back, "water hidden", hid)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
