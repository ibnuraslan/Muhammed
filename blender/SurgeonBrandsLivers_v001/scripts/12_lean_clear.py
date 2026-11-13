"""Close-lean pass (client, Nov 13): a face/mask never rests on the character's own hands. Over a range, the spine,
neck and head rotations are eased back toward upright (only as far as needed) until the head stays >= CLEAR from
every hand joint. Hands are IK targets keyed in world space, so grips and tool contact are untouched.
Then the whole film is scanned for any other close lean and reported.
blender -b in.blend --python 12_lean_clear.py -- out.blend report.txt"""
import sys, bpy
from mathutils import Vector, Quaternion
a = sys.argv[sys.argv.index("--") + 1:]; OUT, REP = a[0], a[1]
sc = bpy.context.scene
FACE_R = 0.10          # head centre -> face/mask surface
CLEAR = 0.12           # required face/mask -> hand clearance
SPINE = ["spine05", "spine04", "spine03", "spine02", "spine01", "neck01", "neck02", "neck03", "head"]
HAND = ["wrist", "metacarpal1", "metacarpal2", "metacarpal3", "metacarpal4"] + ["finger%d-%d" % (k, j) for k in range(1, 6) for j in (1, 2, 3)]
def head_c(r):
    pb = r.pose.bones["head"]; return r.matrix_world @ (pb.head + (pb.tail - pb.head) * 0.45)
def hand_pts(r):
    out = []
    for s in "LR":
        for b in HAND:
            pb = r.pose.bones.get(b + "." + s)
            if pb: out += [r.matrix_world @ pb.head, r.matrix_world @ pb.tail]
    return out
def clearance(r):
    h = head_c(r); return min((p - h).length for p in hand_pts(r)) - FACE_R
def bones(r): return [r.pose.bones[n] for n in SPINE if n in r.pose.bones]

def fix(rig, f0, f1, step=2):
    r = bpy.data.objects[rig]; B = bones(r); plan = {}
    for f in range(f0, f1 + 1, step):
        sc.frame_set(f); q0 = {pb.name: pb.rotation_quaternion.copy() for pb in B}
        k = 1.0; c = clearance(r)
        while c < CLEAR and k > 0.15:
            k -= 0.05
            for pb in B: pb.rotation_quaternion = Quaternion().slerp(q0[pb.name], k)
            bpy.context.view_layer.update(); c = clearance(r)
        plan[f] = ({n: Quaternion().slerp(q, k) for n, q in q0.items()}, k, c)
    # smooth the easing factor so the rise is gradual (no pops), then key
    fs = sorted(plan); ks = [plan[f][1] for f in fs]
    sm = [min(ks[max(0, i - 4):i + 5]) for i in range(len(ks))]
    for f, kk in zip(fs, sm):
        sc.frame_set(f)
        for pb in B:
            q = pb.rotation_quaternion.copy() if False else None
    for f, kk in zip(fs, sm):
        sc.frame_set(f)
        q0 = {pb.name: pb.rotation_quaternion.copy() for pb in B}
    keyed = {}
    for f, kk in zip(fs, sm):
        sc.frame_set(f)
        for pb in B:
            keyed[(f, pb.name)] = Quaternion().slerp(pb.rotation_quaternion.copy(), kk)
    for (f, n), q in keyed.items():
        pb = r.pose.bones[n]; pb.rotation_quaternion = q; pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
    worst = 9.0
    for f in range(f0, f1 + 1):
        sc.frame_set(f); worst = min(worst, clearance(r))
    return min(sm), worst

rep = []
k, w = fix("Surgeon1", 372, 470)
rep.append("Surgeon1 372-470 (needle driver stitching): spine/neck/head eased to %.0f%% of the lean at most; face/mask to hand min %.1f cm" % (k * 100, w * 100))
k, w = fix("Surgeon1", 1, 368)
rep.append("Surgeon1 1-368 (pen at the incision, first stitches): eased to %.0f%% at most; face/mask to hand min %.1f cm" % (k * 100, w * 100))
# whole-film scan for any other close lean (every 3 frames, visible characters); the mask-off grip 462-512 is an intended hand-on-mask
RIGS = [o for o in bpy.data.objects if o.type == 'ARMATURE' and "head" in o.pose.bones and "finger2-1.L" in o.pose.bones]
def hidden(r):
    b = bpy.data.objects.get(r.name + ".body"); return r.hide_render or (b is not None and b.hide_render)
low = {}
for f in range(1, sc.frame_end + 1, 3):
    sc.frame_set(f)
    for r in RIGS:
        if hidden(r) or r.name == "GloveHands": continue
        if r.name == "Surgeon1" and 462 <= f <= 512: continue
        c = clearance(r)
        if c < CLEAR: low.setdefault(r.name, []).append((f, round(c * 100, 1)))
rep.append("Other close leans (face/mask < %d cm from own hands): %s" % (CLEAR * 100, {k: (v[0], v[-1], len(v), min(x[1] for x in v)) for k, v in low.items()} or "none"))
open(REP, "w").write("\n".join(rep) + "\n"); print("\n".join(rep))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("LEAN_DONE")
