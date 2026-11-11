"""Hand audit (client rule, Nov 11 23:00): every 2 frames, for each visible IK character:
 - hand vs other hand (vertices of one hand closer than 6 mm to the other hand's surface)
 - hand vs own torso/head (hand vertices inside the own body with arm and hand faces removed, > 4 mm)
 - hand vs other characters (hand vertices inside another visible body, > 4 mm)
blender -b film.blend --python audit_hands.py -- [step] [f0] [f1]"""
import sys, bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STEP = int(a[0]) if a else 2; F0 = int(a[1]) if len(a) > 1 else 1; F1 = int(a[2]) if len(a) > 2 else 1890
sc = bpy.context.scene
ACT = ["Prisoner", "Visitor", "Guard", "CrowdB", "YardP1", "YardP2", "Guard2"]
def body(n): return next(c for c in bpy.data.objects[n].children if c.name.endswith(".body"))
HB = lambda s: {"wrist." + s} | {"finger%d-%d.%s" % (k, j, s) for k in range(1, 6) for j in range(1, 4)} | {"metacarpal%d.%s" % (k, s) for k in range(1, 5)}
ARMB = lambda s: HB(s) | {"lowerarm01." + s, "lowerarm02." + s, "upperarm01." + s, "upperarm02." + s}
IDX = {}
dg0 = bpy.context.evaluated_depsgraph_get()
for n in ACT:
    b = body(n)
    for m in b.modifiers:
        if m.type == 'SUBSURF': m.show_viewport = False; m.show_render = False
bpy.context.view_layer.update(); dg0 = bpy.context.evaluated_depsgraph_get()
def make_idx(n, dg):
    b = body(n); gname = {g.index: g.name for g in b.vertex_groups}
    e = b.evaluated_get(dg); me = e.to_mesh()
    def sel(names, thr=0.5):
        return {v.index for v in me.vertices if any(gname.get(g.group) in names and g.weight > thr for g in v.groups)}
    d = {"L": sorted(sel(HB("L"))), "R": sorted(sel(HB("R"))), "arms": sel(ARMB("L") | ARMB("R"), 0.2), "nv": len(me.vertices)}
    d["torso_faces"] = [p.index for p in me.polygons if not any(i in d["arms"] for i in p.vertices)]
    e.to_mesh_clear(); return d
def inside(t, p):
    hit = t.find_nearest(p, 0.05)
    if hit[0] is None: return 1.0
    d = p - hit[0]
    if d.dot(hit[1]) >= 0: return d.length
    for dirn in (Vector((0.0, 0.0, 1.0)), Vector((0.31, 0.47, 0.83)).normalized()):
        cnt, o = 0, p.copy()
        for _ in range(24):
            h = t.ray_cast(o + dirn * 1e-4, dirn)
            if h[0] is None: break
            cnt += 1; o = h[0]
        if cnt % 2 == 0: return d.length
    return -d.length
hits = {}
for f in range(F0, F1 + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    vis = [n for n in ACT if not bpy.data.objects[n].hide_render]
    W = {}
    for n in vis:
        e = body(n).evaluated_get(dg); me = e.to_mesh(); M = e.matrix_world
        co = [M @ v.co for v in me.vertices]
        polys = [tuple(p.vertices) for p in me.polygons]
        e.to_mesh_clear()
        W[n] = (co, polys)
    for n in vis:
        co, polys = W[n]
        if n not in IDX or IDX[n]["nv"] != len(co): IDX[n] = make_idx(n, dg)
        torso = BVHTree.FromPolygons(co, [polys[i] for i in IDX[n]["torso_faces"]])
        for s_ in "LR":
            P_ = [co[i] for i in IDX[n][s_]][::2]
            # own torso/head
            if any(inside(torso, p) < -0.004 for p in P_):
                hits.setdefault((n, s_, "own body"), []).append(f)
            # other hand
            o_ = "R" if s_ == "L" else "L"
            oset = set(IDX[n][o_])
            other = BVHTree.FromPolygons(co, [p for p in polys if all(i in oset for i in p)])
            if any((other.find_nearest(p, 0.006)[0] is not None) for p in P_[::2]):
                hits.setdefault((n, s_, "other hand"), []).append(f)
            # other characters
            for m in vis:
                if m == n: continue
                if (co[IDX[n][s_][0]] - W[m][0][0]).length > 3.0 and min((co[IDX[n][s_][0]] - c).length for c in W[m][0][::400]) > 0.6: continue
                tm = BVHTree.FromPolygons(W[m][0], W[m][1])
                if any(inside(tm, p) < -0.004 for p in P_[::2]):
                    hits.setdefault((n, s_, "char " + m), []).append(f)
total = 0
for k, fr in sorted(hits.items()):
    runs = []
    for f in fr:
        if runs and f - runs[-1][1] <= STEP: runs[-1][1] = f
        else: runs.append([f, f])
    total += len(fr)
    print("HAND %-9s %s %-14s frames=%3d  %s" % (k[0], k[1], k[2], len(fr), " ".join("%d-%d" % tuple(r) for r in runs)))
print("HAND_TOTAL flagged frames", total, "step", STEP)
