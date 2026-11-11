"""Hand audit (client rule, Nov 11 23:00): BVH overlap every 2 frames of
  each hand vs the other hand, each hand vs own torso/clothes/head (arms excluded), each hand vs other characters.
blender -b film.blend --python hand_audit.py -- <report.txt>"""
import sys, bpy
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; O = bpy.data.objects
CAB = ["Bomber", "Attendant", "Steward", "PaxA", "PaxB", "PaxC", "PaxD", "Sleeper1", "Sleeper2", "Sleeper3", "Sleeper4"]
AIR = ["Traveller", "Officer", "PaxA", "PaxB", "Steward", "Attendant", "PaxC", "PaxD"]
WIN = [(n, 1, 1068, CAB) for n in CAB] + [(n, 1393, 1620, AIR) for n in AIR]
HANDK = ("finger", "wrist", "metacarpal")
ARMK = HANDK + ("lowerarm", "upperarm", "shoulder", "clavicle")
TOL = 0.006
def parts(n):
    return [c for c in O[n].children if c.type == 'MESH' and not c.hide_render and not any(k in c.name for k in ("eyebrow", "eyelash", "teeth", "tongue"))]
def gidx(ob, keys, side=None):
    return {g.index for g in ob.vertex_groups if any(g.name.startswith(k) for k in keys) and (side is None or g.name.endswith("." + side))}
CACHE = {}
def masks(ob):
    if ob.name in CACHE: return CACHE[ob.name]
    me = ob.data; arm = gidx(ob, ARMK)
    def w(v, gs): return sum(g.weight for g in v.groups if g.group in gs)
    armv = {v.index for v in me.vertices if w(v, arm) > 0.3}
    hand = {s: [v.index for v in me.vertices if w(v, gidx(ob, HANDK, s)) > 0.5] for s in "LR"} if ob.name.endswith(".body") else None
    CACHE[ob.name] = (armv, hand); return CACHE[ob.name]
def world(ob, dg):
    e = ob.evaluated_get(dg); me = e.to_mesh(); mw = e.matrix_world
    vs = [mw @ v.co for v in me.vertices]; ps = [tuple(p.vertices) for p in me.polygons]; e.to_mesh_clear(); return vs, ps
def inside(t, p):
    loc, nrm, i, d = t.find_nearest(p, 0.04)
    return loc is not None and (p - loc).dot(nrm) < -TOL
# audit on the armature-deformed cage: subdivision / mask / smoothing modifiers removed (file is not saved)
for ob in O:
    if ob.type == 'MESH':
        for md in list(ob.modifiers):
            if md.type in ('SUBSURF', 'MASK', 'CORRECTIVE_SMOOTH'): ob.modifiers.remove(md)
hits = []
frames = sorted({f for _, a, b, _ in WIN for f in range(a, b + 1, 2)})
for f in frames:
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    act = [w for w in WIN if w[1] <= f <= w[2]]
    names = sorted({w[0] for w in act} | {m for w in act for m in w[3]})
    full, own, handpts = {}, {}, {}
    for n in names:
        V_, P_, Vo, Po = [], [], [], []
        for ob in parts(n):
            vs, ps = world(ob, dg); armv, hand = masks(ob)
            off = len(V_); V_ += vs; P_ += [tuple(i + off for i in p) for p in ps]
            keep = [p for p in ps if not any(i in armv for i in p)]
            offo = len(Vo); Vo += vs; Po += [tuple(i + offo for i in p) for p in keep]
            if hand is not None: handpts[n] = {s: [vs[i] for i in hand[s]][::2] for s in "LR"}
        full[n] = BVHTree.FromPolygons(V_, P_) if P_ else None
        own[n] = BVHTree.FromPolygons(Vo, Po) if Po else None
    for n, a, b, others in act:
        hp = handpts.get(n)
        if not hp: continue
        # hand vs hand
        kd = KDTree(len(hp["R"]))
        for i, p in enumerate(hp["R"]): kd.insert(p, i)
        kd.balance()
        hh = sum(1 for p in hp["L"] if kd.find(p)[2] < 0.004)
        if hh > 3: hits.append((f, n, "hand-vs-hand", hh))
        for s in "LR":
            c = sum(1 for p in hp[s] if own[n] and inside(own[n], p))
            if c > 3: hits.append((f, n, "hand.%s-vs-own-body" % s, c))
            for m in others:
                if m == n or m not in full or full[m] is None: continue
                c = sum(1 for p in hp[s] if inside(full[m], p))
                if c > 3: hits.append((f, n, "hand.%s-vs-%s" % (s, m), c))
lines = ["ShoeBomber hand audit: every 2 frames, hand verts (every 2nd) inside another surface by > %.0f mm; a sample is flagged when > 3 verts." % (TOL * 1000),
         "flagged frames: %d" % len({(h[0], h[1], h[2]) for h in hits})]
runs = {}
for f, n, k, c in hits: runs.setdefault((n, k), []).append((f, c))
for (n, k), fs in sorted(runs.items()):
    rr = []
    for f, c in fs:
        if rr and f - rr[-1][1] <= 2: rr[-1][1] = f; rr[-1][2] = max(rr[-1][2], c)
        else: rr.append([f, f, c])
    lines.append("  %-10s %-26s %d frames: %s" % (n, k, len(fs), ", ".join("f%d-%d(max %d)" % tuple(r) for r in rr)))
open(OUT, "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
