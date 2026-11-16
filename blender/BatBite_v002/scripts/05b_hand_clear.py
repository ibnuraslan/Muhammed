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
def key_ik(s, f, dw):
    pb = R.pose.bones["IK_hand." + s]; sc.frame_set(f)
    M = pb.matrix.copy(); M.translation = M.translation + R.matrix_world.inverted().to_3x3() @ dw
    pb.matrix = M; bpy.context.view_layer.update()
    pb.keyframe_insert("location", frame=f, group=pb.name); pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
def solve(f, s, bed):
    p0, _ = push_of(f, s, bed); p = p0
    for it in range(8):
        p, n = push_of(f, s, bed)
        if p < 0.002: break
        key_ik(s, f, n * (p + 0.002))
    return p0, push_of(f, s, bed)[0]
RANGES = [("R", 420, 446, 3, False), ("R", 868, 960, 4, False),
          ("L", 1395, 1599, 4, False), ("R", 1395, 1599, 4, False),
          ("L", 1600, 1930, 6, True), ("R", 1600, 1930, 6, True)]
for s, f0, f1, st, bed in RANGES:
    res = [(f,) + tuple(round(x * 1000, 1) for x in solve(f, s, bed)) for f in range(f0, f1 + 1, st)]
    print("HC", s, f0, f1, "before>2mm", [(f, a) for f, a, b in res if a > 2][:12], "after>2mm", [(f, b) for f, a, b in res if b > 2])
for ps in range(3):
    bad = [(s, f, bed) for s, f0, f1, st, bed in RANGES for f in range(f0, f1 + 1) if push_of(f, s, bed)[0] > 0.010]
    print("HC verify pass", ps, len(bad), [(s, f) for s, f, _ in bad][:40])
    if not bad: break
    for s, f, bed in bad: solve(f, s, bed)
for m, sv in saved: m.show_viewport = sv
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("HC saved", OUT)
