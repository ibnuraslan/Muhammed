"""v005 hands pass (client 23:00 UTC): Limit Rotation (LOCAL) on every finger, thumb and wrist bone.
Fingers: the spec (curl 0..90 on local +X = never backward, twist +-10, spread +-12) intersected with the keyed range +-5 deg.
Wrists: this rig's rest-relative wrist angles don't map 1:1 onto anatomical flex/side (a +-25 clamp broke the natural typing hand),
so the natural range is taken from every phase that reads right (all frames except the 1180-1280 grab/rip) +-10 deg, and the
over-bent grab/rip frames are clamped to it. Thumb: a cone = its own keyed range +-5 deg (Euler clamps at fixed +-40 flipped it).
blender -b in.blend --python 07_hand_limits.py -- <out.blend>"""
import sys, math, bpy
out = sys.argv[sys.argv.index("--") + 1]
R, D = math.radians, math.degrees
sc = bpy.context.scene; A = bpy.data.objects["Teen"]; B = A.data.bones; P = A.pose.bones
SPEC = {"finger": ((0, 90), (-10, 10), (-12, 12)), "wrist": ((-25, 25), (-70, 70), (-60, 60))}
names = [("finger%d-%d.%s" % (k, j, s)) for s in "LR" for k in range(1, 6) for j in range(1, 4)] + ["wrist.L", "wrist.R"]
def localrot(n):
    pb = P[n]; rest = B[n].matrix_local; prest = B[n].parent.matrix_local
    return ((pb.parent.matrix @ (prest.inverted() @ rest)).inverted() @ pb.matrix).to_euler('XYZ')
# wrists: the natural range measured on the approved v005 (good phases +-10 deg); pinned so the v006 shock-hover pose
# doesn't widen the range and change how the grab is clamped
WRIST_FIXED = {"wrist.L": ((-78.5, 55.4), (-129.6, 49.7), (-61.2, 31.1)), "wrist.R": ((-34.1, 45.3), (-41.3, 138.3), (-49.8, 31.0))}
obs = {n: [[1e9, -1e9] for _ in range(3)] for n in names}
for f in range(1, 1501, 3):
    sc.frame_set(f)
    for n in names:
        if n.startswith("wrist") and 1180 <= f <= 1280: continue     # the over-bent grab/rip phase is what gets clamped
        e = localrot(n)
        for i in range(3):
            v = D(e[i]); o = obs[n][i]; o[0] = min(o[0], v); o[1] = max(o[1], v)
clamped = []
for n in names:
    spec = None if n.startswith(("wrist", "finger1-")) else SPEC["finger"]
    m = 10 if n.startswith("wrist") else 5
    lim = []
    for i in range(3):
        lo, hi = obs[n][i][0] - m, obs[n][i][1] + m
        if spec:
            if lo < spec[i][0] or hi > spec[i][1]: clamped.append((n, "XYZ"[i], round(obs[n][i][0]), round(obs[n][i][1])))
            lo, hi = max(lo, spec[i][0]), min(hi, spec[i][1])
            if lo > hi: lo = hi = (spec[i][0] + spec[i][1]) / 2
        lim.append((lo, hi))
    if n in WRIST_FIXED: lim = WRIST_FIXED[n]
    c = P[n].constraints.new('LIMIT_ROTATION'); c.name = "HandLimit"; c.owner_space = 'LOCAL'
    c.use_limit_x = c.use_limit_y = c.use_limit_z = True
    (c.min_x, c.max_x), (c.min_y, c.max_y), (c.min_z, c.max_z) = [(R(a), R(b)) for a, b in lim]
print("LIMITS", len(names), "bones; clamped (bone, axis, keyed min, max):", clamped)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
