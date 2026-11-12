"""Hand audit (STYLE_ANIMATED.md "Hands"): every 2 frames, for every on-screen rigged hero within 12 m of the camera:
  - hand vs other hand (same character)
  - hand vs own torso / clothes / head (body minus hands, plus clothing meshes)
  - hand vs other characters' bodies + clothes (within 1.5 m)
A hit = more than HIT_MIN hand vertices inside the other surface (nearest-point normal test, depth > 4 mm).
blender -b PopeShot_anim.blend --python hand_audit.py -- <report.txt> [step]"""
import sys, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]
out = a[0]; STEP = int(a[1]) if len(a) > 1 else 2
sc = bpy.context.scene; O = bpy.data.objects
HEROES = ["Pope", "Prisoner", "AideA", "AideB", "GuardA", "GuardB", "SurgA", "SurgB", "SurgC", "Nurse", "Shooter"]
HANDG = ("finger", "metacarpal")
HIT_MIN = 6
# viewport evaluation without subdivision (speed); masks keep hidden body parts out
for o in O:
    for m in o.modifiers:
        if m.type in ('SUBSURF', 'MASK'): m.show_viewport = False
def hand_side(body):
    """vertex index -> 'L'/'R' for hand vertices (rest weights)"""
    gi = {g.index: g.name for g in body.vertex_groups}; res = {}
    for v in body.data.vertices:
        wl = sum(g.weight for g in v.groups if gi[g.group].startswith(HANDG) and gi[g.group].endswith(".L"))
        wr = sum(g.weight for g in v.groups if gi[g.group].startswith(HANDG) and gi[g.group].endswith(".R"))
        if wl > 0.6: res[v.index] = "L"
        elif wr > 0.6: res[v.index] = "R"
    return res
def near_hand(body):
    """verts of wrist/forearm (excluded from the 'torso' surface: fingers legitimately curl next to them)"""
    gi = {g.index: g.name for g in body.vertex_groups}; out = set()
    for v in body.data.vertices:
        if sum(g.weight for g in v.groups if gi[g.group].startswith(("wrist", "lowerarm", "finger", "metacarpal"))) > 0.2: out.add(v.index)
    return out
INFO = {}; NEAR = {}
for h in HEROES:
    r = O.get(h)
    if not r: continue
    body = next(c for c in r.children if c.name.endswith(".body"))
    clothes = [c for c in r.children if c.type == 'MESH' and c != body and not c.name.split(".")[-1].startswith(("high-poly", "eyebrow", "eyelash", "teeth", "tongue"))
               and not c.name.endswith(("_Gloves",))]
    INFO[h] = (r, body, clothes, hand_side(body)); NEAR[h] = near_hand(body)
def mesh_world(o, dg):
    e = o.evaluated_get(dg); me = e.to_mesh(); M = o.matrix_world
    vs = [M @ v.co for v in me.vertices]; polys = [p.vertices[:] for p in me.polygons]
    e.to_mesh_clear(); return vs, polys
def inside_count(tree, pts, tol=0.004):
    n = 0
    for p in pts:
        loc, nrm, i, d = tree.find_nearest(p, 0.03)
        if loc is not None and (p - loc).dot(nrm) < -tol: n += 1
    return n
hits = []; frames = 0
for f in range(1, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); cam = sc.camera.matrix_world.translation
    act = [h for h, (r, b, c, hs) in INFO.items() if r.matrix_world.translation.z > -20 and (r.matrix_world.translation - cam).length < 12]
    if not act: continue
    frames += 1
    data = {}
    for h in act:
        r, body, clothes, hs = INFO[h]
        vs, polys = mesh_world(body, dg)
        if len(vs) != len(body.data.vertices):
            continue
        handL = [vs[i] for i, s in hs.items() if s == "L"]; handR = [vs[i] for i, s in hs.items() if s == "R"]
        hset = set(hs) | NEAR[h]
        torso_polys = [p for p in polys if not any(i in hset for i in p)]
        trees = {"torso": BVHTree.FromPolygons(vs, torso_polys)}
        for c in clothes:
            cv, cp = mesh_world(c, dg)
            if cp: trees["clothes:" + c.name.split(".")[-1]] = BVHTree.FromPolygons(cv, cp)
        trees["handL"] = BVHTree.FromPolygons(vs, [p for p in polys if all(hs.get(i) == "L" for i in p)])
        trees["handR"] = BVHTree.FromPolygons(vs, [p for p in polys if all(hs.get(i) == "R" for i in p)])
        data[h] = (handL, handR, trees, r.matrix_world.translation.copy())
    for h, (hL, hR, trees, root) in data.items():
        for side, pts, other in (("L", hL, "handR"), ("R", hR, "handL")):
            n = inside_count(trees[other], pts)
            if n > HIT_MIN: hits.append((f, h, side, "other hand", n))
            for k, t in trees.items():
                if k.startswith("hand"): continue
                n = inside_count(t, pts)
                if n > HIT_MIN: hits.append((f, h, side, "own " + k, n))
            for h2, (_, _, trees2, root2) in data.items():
                if h2 == h or (root2 - root).length > 1.5: continue
                for k, t in trees2.items():
                    if k.startswith("hand"): continue
                    n = inside_count(t, pts)
                    if n > HIT_MIN: hits.append((f, h, side, h2 + " " + k, n))
lines = ["HIT f%d %s hand.%s -> %s (%d verts)" % x for x in hits]
summ = {}
for f, h, s, what, n in hits: summ[(h, s, what)] = summ.get((h, s, what), 0) + 1
lines += ["GROUP %s hand.%s -> %s : %d frames" % (k[0], k[1], k[2], v) for k, v in sorted(summ.items(), key=lambda x: -x[1])]
lines.append("HAND_AUDIT frames_checked=%d step=%d hits=%d" % (frames, STEP, len(hits)))
open(out, "w").write("\n".join(lines) + "\n"); print(lines[-1])
for l in lines[-25:]: print(l)
