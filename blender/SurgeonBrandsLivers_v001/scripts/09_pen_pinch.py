"""Re-key the tool-holding hands with the hand_poses 'pinch' preset (thumb + index on the pen / driver) on an already
built film (same as the 03_animate.py HAND_POSE_RULES change). blender -b in.blend --python 09_pen_pinch.py -- out.blend"""
import sys, os, bpy
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "pipeline", "hand_poses.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
n = 0
for name, s, f0, f1 in (("Surgeon1", "R", 1, 460), ("GloveHands", "R", 1, 300)):
    r = bpy.data.objects[name]; rot = _pose_rots(r, s, "pinch")
    fr = set()
    for L in r.animation_data.action.layers:
        for st in L.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    if fc.data_path.startswith('pose.bones["finger') and fc.data_path.split('"')[1].endswith("." + s):
                        fr |= {round(k.co.x) for k in fc.keyframe_points if f0 <= k.co.x <= f1}
    for f in sorted(fr):
        _key(r, s, rot, f, 1.0); n += 1
print("PINCH_KEYS", n)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
