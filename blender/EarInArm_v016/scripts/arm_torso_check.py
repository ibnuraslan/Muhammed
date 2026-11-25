"""Per-frame self-intersection test: surgeon's arms (upperarm02..fingers) against his own torso + scrub top.
blender -b film.blend --python arm_torso_check.py -- F0 F1 [step]"""
import bpy, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; f0, f1 = int(a[0]), int(a[1]); step = int(a[2]) if len(a) > 2 else 1
sc = bpy.context.scene; D = bpy.data.objects["Surgeon"]; B = bpy.data.objects["Surgeon.body"]
names = {b.name for b in D.data.bones}; i2n = {g.index: g.name for g in B.vertex_groups if g.name in names}
def dom(v):
    best = (0, None)
    for g in v.groups:
        n = i2n.get(g.group)
        if n and g.weight > best[0]: best = (g.weight, n)
    return best[1] or ""
ARM = ("lowerarm", "wrist", "finger", "metacarpal", "upperarm02")
TORSO = ("spine", "pelvis", "root", "breast", "clavicle")
dm = [dom(v) for v in B.data.vertices]
for m in B.modifiers:
    if m.type in ('MASK', 'SUBSURF'): m.show_viewport = False
hits = []
for f in range(f0, f1 + 1, step):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); me = B.evaluated_get(dg).to_mesh()
    W = B.matrix_world; co = [W @ v.co for v in me.vertices]
    tf = [p.vertices[:] for p in me.polygons if all(dm[i].startswith(TORSO) for i in p.vertices)]
    bvh = BVHTree.FromPolygons(co, tf)
    worst = 0.0; n = 0; sideL = sideR = 0
    for i, d in enumerate(dm):
        if not d.startswith(ARM): continue
        loc, nrm, idx, dist = bvh.find_nearest(co[i])
        if loc is None: continue
        depth = (co[i] - loc).dot(nrm)
        if depth < -0.008 and dist < 0.06:
            n += 1; worst = min(worst, depth)
            if d.endswith(".L"): sideL += 1
            else: sideR += 1
    B.evaluated_get(dg).to_mesh_clear()
    if n: hits.append((f, n, round(worst * 1000), sideL, sideR))
print("ARMTORSO frames_with_hits", len(hits), "of", len(range(f0, f1 + 1, step)), hits[:40])
