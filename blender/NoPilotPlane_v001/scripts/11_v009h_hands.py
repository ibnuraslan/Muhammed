"""v009h (client via director, item 3): his hands and wrists bent at unnatural angles while he sits and walks.
On every frame where his hands are idle (seated in the cabin, the aisle walk, hanging at his sides, resting on his knees,
braced palm-down on the seat backs and the pedestal), the wrist is clamped to zero twist and a small bend, and
the fingers take the hand_poses 'relaxed' preset. Grips (the door push, the haul, the yoke and the throttle) are left as they are.
blender -b film.blend --python 11_v009h_hands.py -- out.blend"""
import sys, os, bpy, math
out = sys.argv[sys.argv.index("--") + 1]
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
exec(open(os.path.join(HERE, "..", "..", "pipeline", "hand_poses.py")).read())
sc = bpy.context.scene; END = sc.frame_end
YOU = bpy.data.objects["YOU"]
IDLE = [(1, 528), (562, 1290), (1545, 1700)]          # film frames; 529-561 door push, 1291-1544 the haul, 1701+ yoke/throttle
def idle(f): return any(a <= f <= b for a, b in IDLE)

# 1. wrist clamp, keyed: idle = no twist, bend within +-25 / +-12 deg; otherwise the original HandLimit
R0 = {}
for s in "LR":
    c = YOU.pose.bones["wrist." + s].constraints["HandLimit"]
    R0[s] = (c.min_x, c.max_x, c.min_y, c.max_y, c.min_z, c.max_z)
def key_limits(s, f, on):
    c = YOU.pose.bones["wrist." + s].constraints["HandLimit"]
    v = (-math.radians(25), math.radians(25), 0.0, 0.0, -math.radians(12), math.radians(12)) if on else R0[s]
    for k, x in zip(("min_x", "max_x", "min_y", "max_y", "min_z", "max_z"), v):
        setattr(c, k, x); c.keyframe_insert(k, frame=f)
edges = sorted({1, END} | {a for a, b in IDLE} | {b + 1 for a, b in IDLE})
for s in "LR":
    for f in edges: key_limits(s, f, idle(f))
for fc in YOU.animation_data.action.fcurves if hasattr(YOU.animation_data.action, "fcurves") else []:
    pass
def all_fcurves(act):
    if hasattr(act, "fcurves"): return list(act.fcurves)
    return [fc for l in act.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
for fc in all_fcurves(YOU.animation_data.action):
    if "HandLimit" in fc.data_path:
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'

# 2. fingers: relaxed through every idle window (old curl keys inside the windows removed)
nd = 0
for fc in all_fcurves(YOU.animation_data.action):
    if '"finger' not in fc.data_path: continue
    for kp in reversed(list(fc.keyframe_points)):
        if any(a < kp.co.x < b for a, b in IDLE): fc.keyframe_points.remove(kp); nd += 1
    fc.update()
for a, b in IDLE:
    for f in list(range(a, b + 1, 60)) + [b]:
        for s in "LR": apply_pose(YOU, s, "relaxed", f)
print("HANDS11 removed finger keys", nd, "idle windows", IDLE)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("HANDS11 saved", out)
