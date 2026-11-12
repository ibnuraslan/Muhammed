# Ease one-frame camera snaps (view turns > MAXDEG in one frame) into a short whip with the same start and end framings.
# Run on the baked film: blender -b in.blend --python 10_camjump.py -- out.blend
import bpy, sys, math
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; cam = sc.camera; aim = bpy.data.objects["CAM_Film_Aim"]
F0, F1 = sc.frame_start, sc.frame_end; MAXDEG = 45.0
def state(f):
    sc.frame_set(f); c = cam.matrix_world.translation.copy(); a = aim.matrix_world.translation.copy()
    return c, a
S = {f: state(f) for f in range(F0, F1 + 1)}
def ang(f):
    (c0, a0), (c1, a1) = S[f - 1], S[f]
    d0, d1 = (a0 - c0).normalized(), (a1 - c1).normalized()
    return math.degrees(d0.angle(d1))
snaps = [f for f in range(F0 + 1, F1 + 1) if ang(f) > MAXDEG]
print("CAMJUMP snaps", [(f, round(ang(f))) for f in snaps])
done = set()
for f in snaps:
    if f in done: continue
    a, b = f - 3, f + 2
    while b < F1 and ang(b + 1) > MAXDEG: b += 1
    ca, aa = S[a]; cb, ab = S[b]
    da, db = (aa - ca).normalized(), (ab - cb).normalized(); La, Lb = (aa - ca).length, (ab - cb).length
    tot = da.angle(db)
    for g in range(a + 1, b):
        u = (g - a) / (b - a); w = u * u * (3 - 2 * u)
        c, _ = S[g]
        # slerp of the view direction
        if tot < 1e-4: d = da
        else: d = (da * math.sin((1 - w) * tot) + db * math.sin(w * tot)) / math.sin(tot)
        aim.location = c + d.normalized() * (La + (Lb - La) * w)
        aim.keyframe_insert("location", frame=g)
    for g in (a, b):   # pin the end framings exactly
        aim.location = S[g][1]; aim.keyframe_insert("location", frame=g)
    done.update(range(a, b + 1))
    print("CAMJUMP eased", a, "->", b, "total turn", round(math.degrees(tot)), "deg over", b - a, "frames")
S = {f: state(f) for f in range(F0, F1 + 1)}
print("CAMJUMP max turn after", round(max(ang(f) for f in range(F0 + 1, F1 + 1)), 1), "deg/frame")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=False)
