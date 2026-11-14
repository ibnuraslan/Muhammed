"""v007 fixes from the second preview pass (pv7):
- 2386-2401: the medic shuffled toward the mask diver after the injection and his face met DiverB's head. He now holds
  his injection kneel (pose at 2345) until the camera dives (2420); later keys are untouched.
- 2411-2426: the dive through the water surface into the passage read as 0.25 s of dark blur: covered by a rock wipe (J 2418).
- 2522-2552: the towing diver's hand and the boy filled the lens: the camera dollies back 0.6 m (aim unchanged), eased.
blender -b in.blend --python 17_v007_fix2.py -- out.blend"""
import bpy, sys
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; cam = sc.camera; aim = cam.constraints[0].target
def fcs(o, path=None):
    ad = o.animation_data
    return [fc for lay in ad.action.layers for st in lay.strips for cb in st.channelbags for fc in cb.fcurves if path is None or fc.data_path == path]
# 1. medic hold
rig = bpy.data.objects["DiverA"]; n = 0
for fc in fcs(rig):
    if not fc.data_path.startswith("pose.bones"): continue
    v0 = fc.evaluate(2345)
    for kp in fc.keyframe_points:
        if 2345 < kp.co.x <= 2420:
            d = v0 - kp.co.y; kp.co.y = v0; kp.handle_left.y += d; kp.handle_right.y += d; n += 1
    fc.update()
print("MEDIC_HOLD keys", n)
# 2. rock wipe at the dive
wv = bpy.data.materials["M_RockWipe"].node_tree.nodes["Wipe"].outputs[0]
J = 2418
for f, v in ((J - 7, 0.0), (J - 1, 1.0), (J + 2, 1.0), (J + 8, 0.0)):
    wv.default_value = v; wv.keyframe_insert("default_value", frame=f)
# 3. dolly back
F0, F1, RAMP, BACK = 2516, 2556, 10, 0.6
cl = sorted(fcs(cam, "location"), key=lambda f: f.array_index); al = sorted(fcs(aim, "location"), key=lambda f: f.array_index)
for f in range(F0, F1 + 1):
    c = [fc.evaluate(f) for fc in cl]; a = [fc.evaluate(f) for fc in al]
    d = [c[i] - a[i] for i in range(3)]; L = sum(x * x for x in d) ** 0.5 or 1.0
    e = min(1.0, (f - F0) / RAMP, (F1 - f) / RAMP); e = e * e * (3 - 2 * e)
    for i, fc in enumerate(cl):
        for kp in fc.keyframe_points:
            if int(round(kp.co.x)) == f:
                dv = d[i] / L * BACK * e; kp.co.y += dv; kp.handle_left.y += dv; kp.handle_right.y += dv
for fc in cl: fc.update()
print("FIX2_OK")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
