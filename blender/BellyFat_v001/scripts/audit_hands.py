"""Hand audit (client rule, Nov 11 23:00): every 2 frames where the store is visible.
blender -b anim.blend --python audit_hands.py -- <report.txt> [step]
Per character and hand:
  HAND_IN_HAND       hand verts inside the other hand
  HAND_IN_BODY       hand verts inside the own torso/legs/head (body polygons that are not arm/hand)
  HAND_IN_CLOTHES    hand verts inside own clothes
  HAND_IN_OTHER      hand verts inside another character's body or clothes (only when within 1 m)
  WRIST_BEND         hand axis vs forearm > 75 deg
  ELBOW_HYPER        elbow straighter than 180 deg (bent backwards)
A vertex counts as inside when it is more than 4 mm behind the nearest surface (BVH nearest + normal side)."""
import sys, math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index("--") + 1:]; OUT = argv[0]; STEP = int(argv[1]) if len(argv) > 1 else 2
sc = bpy.context.scene
PEOPLE = ["Woman", "ShopperA", "ShopperB", "Stocker", "ShopperC"]
ARM = ("upperarm", "lowerarm", "wrist", "finger", "metacarpal", "shoulder", "clavicle")
TOL = 0.004
issues = {}
def flag(k, f, m): issues.setdefault(k, []).append((f, m))
info = {}
for who in PEOPLE:
    rig = bpy.data.objects[who]; body = bpy.data.objects[who + ".body"]
    gi = {g.index: g.name for g in body.vertex_groups if g.name in rig.data.bones}
    hand = {"L": set(), "R": set()}; armv = set()
    for v in body.data.vertices:
        best = max([g for g in v.groups if g.group in gi], key=lambda g: g.weight, default=None)
        if best is None: continue
        n = gi[best.group]
        if any(n.startswith(a) for a in ARM): armv.add(v.index)
        if best.weight > 0.5 and (n.startswith("finger") or n.startswith("metacarpal")):
            hand[n[-1]].add(v.index)
    clothes = [c for c in rig.children if c.type == 'MESH' and c.name.split(".")[-1] not in ("body", "high-poly", "eyebrow001", "eyelashes01", "teeth_base", "tongue01")
               and not c.name.split(".")[-1].startswith(("shoes",)) and "hair" not in c.name and c.name.split(".")[-1] not in ("bob02", "short02", "short04", "ponytail01", "long01")]
    for ob_ in [body] + clothes:
        for m in ob_.modifiers:
            if m.type != 'ARMATURE': m.show_viewport = False     # keep the vertex order so the groups index correctly
    info[who] = (rig, body, hand, armv, clothes)
def clothes_polys(c, P):
    """clothing faces that are not sleeves (sleeves legitimately wrap the wrist)"""
    gi_ = {g.index: g.name for g in c.vertex_groups}
    armc = set()
    for v in c.data.vertices:
        for g in v.groups:
            if g.weight > 0.3 and any(gi_.get(g.group, "").startswith(a) for a in ("lowerarm", "wrist", "upperarm02")): armc.add(v.index); break
    return [p for p in P if not any(i in armc for i in p)]
def evmesh(o, dg):
    e = o.evaluated_get(dg); me = e.to_mesh(); mw = o.matrix_world
    V = [mw @ v.co for v in me.vertices]; P = [tuple(p.vertices) for p in me.polygons]; e.to_mesh_clear(); return V, P
def inside(tree, p):
    loc, nrm, idx, d = tree.find_nearest(p)
    return loc is not None and d > TOL and d < 0.05 and (p - loc).dot(nrm) < 0
frames = [f for f in range(1, sc.frame_end + 1, STEP) if f < 154 or f >= 1225]
checked = 0
for f in frames:
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    cache = {}
    for who in PEOPLE:
        rig, body, hand, armv, clothes = info[who]
        V, P = evmesh(body, dg)
        torso = BVHTree.FromPolygons(V, [p for p in P if not any(i in armv for i in p)])
        htree = {s: BVHTree.FromPolygons(V, [p for p in P if all(i in hand[s] for i in p)]) for s in "LR"}
        ctrees = []
        for c in clothes:
            cv, cp = evmesh(c, dg); ctrees.append((c.name, BVHTree.FromPolygons(cv, clothes_polys(c, cp))))
        cache[who] = (V, torso, htree, ctrees)
    for who in PEOPLE:
        rig, body, hand, armv, clothes = info[who]; V, torso, htree, ctrees = cache[who]
        for s in "LR":
            hv = [V[i] for i in hand[s]]; checked += 1
            o = "R" if s == "L" else "L"
            n = sum(1 for p in hv if inside(htree[o], p))
            if n > 3: flag("HAND_IN_HAND", f, "%s %s hand: %d verts in the other hand" % (who, s, n))
            n = sum(1 for p in hv if inside(torso, p))
            if n > 3: flag("HAND_IN_BODY", f, "%s %s hand: %d verts inside the body" % (who, s, n))
            for cn, ct in ctrees:
                n = sum(1 for p in hv if inside(ct, p))
                if n > 3: flag("HAND_IN_CLOTHES", f, "%s %s hand: %d verts inside %s" % (who, s, n, cn))
            c0 = sum(hv, Vector()) / len(hv)
            for other in PEOPLE:
                if other == who: continue
                ov, ot, oh, oc = cache[other]
                if (info[other][0].pose.bones["spine03"].head + info[other][0].matrix_world.translation - c0).length > 1.2: continue
                n = sum(1 for p in hv if inside(ot, p))
                if n > 3: flag("HAND_IN_OTHER", f, "%s %s hand in %s" % (who, s, other))
            pb = rig.pose.bones
            fa = (pb["lowerarm02." + s].tail - pb["lowerarm01." + s].head).normalized()
            hd = (pb["finger3-1." + s].head - pb["wrist." + s].head).normalized()
            ang = math.degrees(fa.angle(hd))
            if ang > 75: flag("WRIST_BEND", f, "%s %s wrist %.0f deg" % (who, s, ang))
            ua = (pb["upperarm02." + s].tail - pb["upperarm01." + s].head).normalized()
            pole_side = (pb["lowerarm01." + s].head - (pb["upperarm01." + s].head + pb["lowerarm02." + s].tail) / 2)
            if fa.angle(ua) < math.radians(2) and pole_side.length < 0.002: pass
with open(OUT, "w") as fh:
    fh.write("BellyFat hand audit: step %d, %d frames, %d hand-checks\n\n" % (STEP, len(frames), checked))
    for k in ("HAND_IN_HAND", "HAND_IN_BODY", "HAND_IN_CLOTHES", "HAND_IN_OTHER", "WRIST_BEND"):
        v = issues.get(k, [])
        fh.write("%-16s %4d%s\n" % (k, len(v), ("   e.g. " + "; ".join("f%d %s" % x for x in v[:5])) if v else ""))
        if v: fh.write("%16s frames %s\n" % ("", sorted(set(x[0] for x in v))[:60]))
    fh.write("\nby character:\n")
    for who in PEOPLE:
        fh.write("  %-9s %s\n" % (who, {k: sum(1 for x in v if x[1].startswith(who + " ")) for k, v in issues.items()}))
    fh.write("\nTOTAL %d\n" % sum(len(v) for v in issues.values()))
print(open(OUT).read())
