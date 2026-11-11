"""Hand-contact audit (client hands rule): every 2 frames up to the map swap, fingertip/wrist points vs the other hand,
own torso and head, and other characters (skeleton capsules). blender -b film.blend --python audit_hands.py -- <out.txt>"""
import sys, os, math
import bpy
from collections import Counter
sc = bpy.context.scene
AUD = sys.argv[sys.argv.index("--") + 1]
humans = [o for o in bpy.data.objects if o.type == 'ARMATURE' and "finger1-1.L" in o.pose.bones]
# ---------------------------------------------------------------- hand audit (capsules from the skeleton, every 2 frames)
SW = sc.get("SWAP_F", 1748)
def seg_dist(p, a_, b_):
    ab = b_ - a_; t = max(0.0, min(1.0, (p - a_).dot(ab) / max(1e-9, ab.dot(ab)))); return (p - (a_ + ab * t)).length
counts = {"hand_hand": 0, "hand_own_torso": 0, "hand_own_head": 0, "hand_other_char": 0}
lines = []
watch = humans
for f in range(1, SW, 2):
    sc.frame_set(f)
    vis = [o for o in watch if not o.hide_render]
    P = {}
    for o in vis:
        M = o.matrix_world; pb = o.pose.bones
        tips = {s: [M @ pb[f"finger{i}-3.{s}"].tail for i in (2, 3, 4)] + [M @ pb["wrist." + s].tail] for s in "LR"}
        torso = (M @ pb["spine05"].head, M @ pb["spine01"].tail)
        head = M @ pb["head"].head + (M.to_3x3() @ (pb["head"].tail - pb["head"].head)) * 0.5
        P[o.name] = (tips, torso, head)
    for nm, (tips, torso, head) in P.items():
        if min((p - q).length for p in tips["L"] for q in tips["R"]) < 0.015:
            counts["hand_hand"] += 1; lines.append(f"f{f} {nm} hand-hand")
        for s in "LR":
            for p in tips[s][:3]:
                if seg_dist(p, *torso) < 0.085:
                    counts["hand_own_torso"] += 1; lines.append(f"f{f} {nm} {s} inside own torso {seg_dist(p, *torso):.3f}"); break
            if min((p - head).length for p in tips[s]) < 0.07:
                counts["hand_own_head"] += 1; lines.append(f"f{f} {nm} {s} in head")
        for nm2, (tips2, torso2, head2) in P.items():
            if nm2 == nm or (torso[0] - torso2[0]).length > 1.5: continue
            for s in "LR":
                if any(seg_dist(p, *torso2) < 0.085 or (p - head2).length < 0.07 for p in tips[s][:3]):
                    counts["hand_other_char"] += 1; lines.append(f"f{f} {nm} {s} into {nm2}")
with open(AUD, "w") as fh:
    fh.write(f"HAND AUDIT (every 2 frames, frames 1-{SW}; skeleton capsules: torso r=8.5 cm, head r=7 cm, fingertip/wrist points): {counts}\n")
    fh.write("By character/pair:\n" + "\n".join(f"  {n:5d}  {k}" for k, n in Counter(" ".join(l.split()[1:]).rsplit(" ", 1)[0] if "torso" in l else " ".join(l.split()[1:]) for l in lines).most_common(60)) + "\n\nAll hits:\n" + "\n".join(lines) + "\n")
print("HANDAUDIT", counts)
