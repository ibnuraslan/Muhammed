"""Heads merging: every 2 frames, any two characters' head bones closer than 0.22 m (head volumes overlapping).
blender -b film.blend --python head_check.py"""
import bpy, itertools
sc = bpy.context.scene
R = [o for o in bpy.data.objects if o.type == 'ARMATURE' and "head" in o.pose.bones and not o.hide_render]
hits = []
for f in range(1, 1621, 2):
    sc.frame_set(f)
    H = {r.name: r.matrix_world @ r.pose.bones["head"].tail.lerp(r.pose.bones["head"].head, 0.5) for r in R}
    for a, b in itertools.combinations(H, 2):
        d = (H[a] - H[b]).length
        if d < 0.22: hits.append((f, a, b, round(d, 2)))
runs = {}
for f, a, b, d in hits: runs.setdefault((a, b), []).append((f, d))
out = []
for k, l in runs.items():
    rr = []
    for f, d in l:
        if rr and f - rr[-1][1] <= 2: rr[-1][1] = f; rr[-1][2] = min(rr[-1][2], d)
        else: rr.append([f, f, d])
    out.append((k, rr))
print("HEADS", out)
