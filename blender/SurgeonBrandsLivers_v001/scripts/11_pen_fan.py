"""Pen hands: ring + little fingers follow the middle finger (no 'starfish' fan, qa FAN <= 28 deg). Thumb/index - the pinch
that seats the pen - are untouched, so the baked pen stays seated. blender -b in.blend --python 11_pen_fan.py -- out.blend"""
import sys, os, math, bpy
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene
def fcs(r):
    return [fc for L in r.animation_data.action.layers for st in L.strips for cb in st.channelbags for fc in cb.fcurves]
for name, s, f0, f1 in (("Surgeon1", "R", 1, 460), ("GloveHands", "R", 1, 300)):
    r = bpy.data.objects[name]; F = fcs(r)
    def get(b):
        return sorted([fc for fc in F if fc.data_path == 'pose.bones["%s"].rotation_quaternion' % b], key=lambda c: c.array_index)
    for j in (1, 2, 3):
        src = get("finger3-%d.%s" % (j, s))
        for k in (4, 5):
            for fc_s, fc_d in zip(src, get("finger%d-%d.%s" % (k, j, s))):
                for kp in fc_s.keyframe_points:
                    if f0 <= kp.co.x <= f1:
                        fc_d.keyframe_points.insert(kp.co.x, kp.co.y)
    sc.frame_set(60 if name == "Surgeon1" else 160)
    P = r.pose.bones
    v = lambda k: (P["finger%d-1.%s" % (k, s)].tail - P["finger%d-1.%s" % (k, s)].head).normalized()
    print("FAN", name, round(math.degrees(v(2).angle(v(5))), 1))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("FAN_DONE")
