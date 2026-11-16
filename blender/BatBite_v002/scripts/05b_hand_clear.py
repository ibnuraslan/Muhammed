"""Hand clearance (Phase 2 clip_scan): fingers must stay OUT of his own legs / torso, and on top of the blanket in bed.
Runs on the saved anim.blend: measures the posed fingers (armature only) against the posed body and moves IK_hand.<side>
out along the surface normal until every finger point is >= 1.2 cm clear; then verifies every frame of each range.
blender -b anim.blend --python 05b_hand_clear.py -- out.blend"""
import bpy, sys
from mathutils import Vector as V
from mathutils.bvhtree import BVHTree
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; R = bpy.data.objects["Singer"]; body = bpy.data.objects["Singer.body"]
gn = {g.index: g.name for g in body.vertex_groups}; bones = {b.name for b in R.data.bones}
dom = {}
for v in body.data.vertices:
    gs = [g for g in v.groups if gn[g.group] in bones and g.weight > 0]
    if gs: dom[v.index] = gn[max(gs, key=lambda g: g.weight).group]
ARMK = ("hand", "finger", "metacarpal", "thumb", "palm")
TGTK = ("upperleg", "lowerleg", "foot", "toe", "pelvis", "spine", "glute", "root")
PROBE = {s: [i for i, n in dom.items() if n.endswith("." + s) and any(k in n.lower() for k in ARMK)] for s in "LR"}
TV = {i for i, n in dom.items() if any(k in n.lower() for k in TGTK)}
TP = [list(p.vertices) for p in body.data.polygons if all(i in TV for i in p.vertices)]
saved = [(m, m.show_viewport) for m in body.modifiers if m.type != 'ARMATURE']
for m, _ in saved: m.show_viewport = False
blk = bpy.data.objects.get("Blanket"); BLK = None
if blk:
    dg = bpy.context.evaluated_depsgraph_get(); e = blk.evaluated_get(dg); me = e.to_mesh()
    BLK = BVHTree.FromPolygons([blk.matrix_world @ v.co for v in me.vertices], [list(p.vertices) for p in me.polygons]); e.to_mesh_clear()
HCLEAR = 0.012
def push_of(f, s, bed):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); e = body.evaluated_get(dg); me = e.to_mesh()
    vs = [body.matrix_world @ v.co for v in me.vertices]; e.to_mesh_clear(); t = BVHTree.FromPolygons(vs, TP)
    worst = []
    for i in PROBE[s]:
        p = vs[i]
        for tree, up in ((t, False), (BLK if bed else None, True)):
            if tree is None: continue
            loc, n, _, d = tree.find_nearest(p, 0.10)
            if loc is None: continue
            if up and n.z < 0: n = -n
            sd = d if (p - loc).dot(n) >= 0 else -d
            if sd < HCLEAR: worst.append((HCLEAR - sd, n))
    if not worst: return 0.0, None
    worst.sort(key=lambda w: -w[0]); top = worst[:12]
    return top[0][0], sum((w[1] for w in top), V((0, 0, 0))).normalized()
import math
INV3 = R.matrix_world.inverted().to_3x3()
def smooth_offsets(O, f0, f1, pad_l, pad_r, dil=5, sig=4.0):
    """dilate (max length in a +-dil window, keeping that frame's vector) then gaussian-smooth componentwise;
    zero-padded on a side that is not a hard cut, edge-padded on a cut side"""
    fs = list(range(f0, f1 + 1)); n = len(fs)
    D_ = []
    for i in range(n):
        w = [O[fs[j]] for j in range(max(0, i - dil), min(n, i + dil + 1))]
        D_.append(max(w, key=lambda v: v.length))
    K = [math.exp(-0.5 * (k / sig) ** 2) for k in range(-12, 13)]
    out = {}
    for i in range(n):
        acc = V((0, 0, 0)); wsum = 0.0
        for k, wk in zip(range(-12, 13), K):
            j = i + k
            if 0 <= j < n: v = D_[j]
            elif j < 0: v = D_[0] if not pad_l else V((0, 0, 0))
            else: v = D_[-1] if not pad_r else V((0, 0, 0))
            acc += v * wk; wsum += wk
        out[fs[i]] = acc / wsum
    if pad_l:
        for i in range(min(4, n)): out[fs[i]] = out[fs[i]] * (i / 4.0)
    if pad_r:
        for i in range(min(4, n)): out[fs[n - 1 - i]] = out[fs[n - 1 - i]] * (i / 4.0)
    return out
def write_keys(s, f0, f1, B, O):
    pb = R.pose.bones["IK_hand." + s]
    for f in list(range(f0, f1 + 1, 2)) + [f1]:
        M = B[f].copy(); M.translation = M.translation + O[f]
        sc.frame_set(f); pb.matrix = M; bpy.context.view_layer.update()
        pb.keyframe_insert("location", frame=f, group=pb.name); pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
# (side, first, last, bed, pad_left, pad_right): pad = blend back to the original motion; no pad at a hard cut (1599|1600)
RANGES = [("R", 418, 446, False, True, True), ("R", 866, 962, False, True, True),
          ("L", 1393, 1599, False, True, False), ("R", 1393, 1599, False, True, False),
          ("L", 1600, 1930, True, False, False), ("R", 1600, 1930, True, False, False)]
for s, f0, f1, bed, pl, pr in RANGES:
    pb = R.pose.bones["IK_hand." + s]; B = {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f); B[f] = pb.matrix.copy()
    O = {f: V((0, 0, 0)) for f in range(f0, f1 + 1)}
    for it in range(5):
        raw = {}; worst = 0.0
        for f in range(f0, f1 + 1):
            p, n = push_of(f, s, bed); worst = max(worst, p)
            raw[f] = INV3 @ (n * (p + 0.003)) if p > 0.0005 else V((0, 0, 0))
        print("HC", s, f0, f1, "iter", it, "worst push mm", round(worst * 1000, 1))
        if worst < 0.004: break
        add = smooth_offsets(raw, f0, f1, pl, pr)
        for f in O: O[f] = O[f] + add[f]
        write_keys(s, f0, f1, B, O)
    print("HC", s, f0, f1, "max offset cm", round(max(v.length for v in O.values()) * 100, 1))
for m, sv in saved: m.show_viewport = sv
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("HC saved", OUT)
