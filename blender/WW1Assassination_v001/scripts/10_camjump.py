# Ease one-frame camera snaps into a short whip with the same start and end framings (qa_check CAMJUMP criterion:
# full rotation incl. roll > 60 deg in one frame and > 3x the neighbours). The Track-To camera flipped its roll when
# looking near straight down; the camera rotation is baked per frame (constraint removed), and each snap window
# is a smoothstep slerp between its end framings.
# blender -b in.blend --python 10_camjump.py -- out.blend
import bpy, sys, math
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; cam = sc.camera
F0, F1 = sc.frame_start, sc.frame_end
Q = {}
for f in range(F0, F1 + 1):
    sc.frame_set(f); Q[f] = cam.matrix_world.to_quaternion()
def turn(q0, q1):
    a = math.degrees(q0.rotation_difference(q1).angle); return min(a, 360 - a)
def snaps():
    D = {f: turn(Q[f - 1], Q[f]) for f in range(F0 + 1, F1 + 1)}
    out = []
    for f in D:
        nb = sorted(D[x] for x in range(max(F0 + 1, f - 3), min(F1, f + 3) + 1) if x != f)
        va = nb[len(nb) // 2] if nb else 0
        if D[f] > 60 and D[f] > 3 * va + 1: out.append((f, round(D[f])))
    return out, max(D.values())
s0, m0 = snaps(); print("CAMJUMP before", s0, "max", round(m0, 1))
for f, _ in s0:
    a, b = f - 3, f + 3
    qa, qb = Q[a], Q[b]
    for g in range(a + 1, b):
        u = (g - a) / (b - a); w = u * u * (3 - 2 * u); Q[g] = qa.slerp(qb, w)
s1, m1 = snaps(); print("CAMJUMP after", s1, "max", round(m1, 1))
for c in list(cam.constraints): cam.constraints.remove(c)
cam.rotation_mode = 'QUATERNION'; prev = None
for f in range(F0, F1 + 1):
    q = Q[f].copy()
    if prev is not None and prev.dot(q) < 0: q.negate()
    cam.rotation_quaternion = q; cam.keyframe_insert("rotation_quaternion", frame=f); prev = q
for l in cam.animation_data.action.layers:
    for st in l.strips:
        for cb in st.channelbags:
            for fc in cb.fcurves:
                if fc.data_path == "rotation_quaternion":
                    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
print("CAMJUMP baked", F1 - F0 + 1, "rotation keys")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
