"""v009h (client via director): the handset went into his forehead and temple (1036-1221).
Patched onto the packaged film (no full rebuild): the handset stays on its hook, and he braces with both hands
on the tops of the seat backs, leaning toward the windscreen. Nothing touches his head.
blender -b film.blend --python 10_v009h_patch.py -- out.blend   (then 08_camera.py on the result)"""
import sys, os, bpy, math
from mathutils import Vector, Matrix
out = sys.argv[sys.argv.index("--") + 1]
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
exec(open(os.path.join(HERE, "..", "..", "pipeline", "hand_poses.py")).read())
sc = bpy.context.scene
YOU = bpy.data.objects["YOU"]; HS = bpy.data.objects["HANDSET"]
A, B = 931, 1266            # old 19.7 s (reaches for the radio) .. old 26.6 s (hand back at the panel)

# 1. handset: back on its hook for the whole film
sc.frame_set(A - 5); M0 = HS.matrix_world.copy()
HS.animation_data_clear(); HS.matrix_world = M0

# 2. delete his arm/finger keys inside the window
act = YOU.animation_data.action
fcs = act.fcurves if hasattr(act, "fcurves") else [fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
n_del = 0
for fc in fcs:
    p = fc.data_path
    if not any(k in p for k in ("IK_hand.", "Pole_elbow.", '"finger', '"wrist.')): continue
    for kp in reversed(list(fc.keyframe_points)):
        if A < kp.co.x < B: fc.keyframe_points.remove(kp); n_del += 1
    fc.update()
print("PATCH deleted keys", n_del)

# 3. both hands on the tops of the seat backs, palms down, fingers relaxed, wrists neutral
R = Rig(YOU); H = Human(R)
def hand(s, f, W, d, n, pole=None):
    sx = 1 if s == "L" else -1
    if pole is None: pole = Vector(W) + Vector((sx * 0.35, -0.25, -0.35))
    H.key_hand(s, f, Vector(W), Vector(d), Vector(n), Vector(pole))
    apply_pose(YOU, s, "relaxed", f)
for i, f in enumerate((962, 1010, 1060, 1110, 1160, 1210, 1250)):
    j = 0.006 * (1 if i % 2 else -1)
    hand("L", f, (-0.34, 1.15, 1.19 + j), (0, 1, -0.35), (0, 0, 1))      # captain seat back, inner top corner
    hand("R", f, (0.33, 1.15, 1.19 - j), (0, 1, -0.35), (0, 0, 1))       # FO seat back, inner top corner
print("PATCH keyed hands")
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("PATCH saved", out)
