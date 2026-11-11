"""Hand audit (client rule, Nov 11 23:00): BVH overlap every <step> frames of
  - each hand vs the other hand
  - each hand vs its own torso/head (body faces weighted to spine/neck/head/clavicle) and its own clothes
  - each hand vs other characters (body + clothes)
Hand faces = body faces whose vertices are mostly weighted to finger/metacarpal bones (palm and fingers; sleeve cuffs over the wrist are normal).
blender -b anim.blend --python 06_hand_audit.py -- <report.txt> [step]"""
import sys
import bpy
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]; STEP = int(argv[1]) if len(argv) > 1 else 2
sc = bpy.context.scene
NAMES = ("Lad", "WitA", "WitB", "Worker")
rigs = {n: bpy.data.objects[n] for n in NAMES}
def part(rig, suffix):
    for c in rig.children:
        if c.name.endswith(suffix): return c
bodies = {n: part(r, ".body") for n, r in rigs.items()}
clothes = {n: [c for c in r.children if c.type == 'MESH' and any(k in c.name for k in ("suit", "worksuit"))] for n, r in rigs.items()}
def classify(body):
    """per-vertex region: 'L'/'R' hand, 'T' torso/head, None"""
    gi = {g.index: g.name for g in body.vertex_groups}
    reg = {}
    for v in body.data.vertices:
        w = {"L": 0.0, "R": 0.0, "T": 0.0}
        if any(gi.get(g.group, "") in ("HelperGeometry", "JointCubes") and g.weight > 0.1 for g in v.groups):
            reg[v.index] = None; continue
        for g in v.groups:
            nm = gi.get(g.group, "")
            side = nm[-1] if nm.endswith((".L", ".R")) else None
            if nm.startswith(("finger", "metacarpal")) and side: w[side] += g.weight      # palm + fingers (a sleeve cuff over the wrist is normal)
            elif nm.startswith(("spine", "neck", "head", "clavicle", "breast", "pelvis", "root", "jaw", "special", "levator", "oris", "risorius", "orbicularis", "eye", "tongue", "temporalis")): w["T"] += g.weight
        k = max(w, key=w.get)
        reg[v.index] = k if w[k] > 0.5 else None
    return reg
REG = {n: classify(b) for n, b in bodies.items()}
def non_cuff_faces(cl):
    """clothes faces except the sleeve cuffs (weighted to forearm-twist / wrist / hand bones): a cuff over the wrist is normal"""
    gi = {g.index: g.name for g in cl.vertex_groups}
    cuff = set()
    for v in cl.data.vertices:
        w = sum(g.weight for g in v.groups if gi.get(g.group, "").startswith(("lowerarm02", "wrist", "finger", "metacarpal")))
        if w > 0.4: cuff.add(v.index)
    return [p.index for p in cl.data.polygons if not any(vi in cuff for vi in p.vertices)]
CLF = {c.name: non_cuff_faces(c) for n in NAMES for c in clothes[n]}
def faces_of(body, reg, key):
    return [p.index for p in body.data.polygons if sum(1 for vi in p.vertices if reg[vi] == key) >= len(p.vertices) - 1]
FACES = {n: {k: faces_of(bodies[n], REG[n], k) for k in ("L", "R", "T")} for n in NAMES}
def tree(obj, dg, face_ids=None):
    ev = obj.evaluated_get(dg); me = ev.to_mesh()
    # body evaluated mesh keeps original vertex order before subdivision only if no topology modifiers: use original-cage indices via
    # the armature-only evaluation (subsurf is disabled for the audit below)
    mw = obj.matrix_world
    vs = [mw @ v.co for v in me.vertices]
    polys = me.polygons if face_ids is None else [me.polygons[i] for i in face_ids if i < len(me.polygons)]
    ps = [tuple(p.vertices) for p in polys]
    ev.to_mesh_clear()
    return BVHTree.FromPolygons(vs, ps, epsilon=0.0) if ps else None
# audit on the deform cage: switch off subdivision / masks so face indices match the base mesh
saved = []
for n in NAMES:
    for o in [bodies[n]] + clothes[n]:
        for m in o.modifiers:
            if m.type in ('SUBSURF', 'MASK') and m.show_viewport:
                saved.append(m); m.show_viewport = False
hits = []
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    vis = [n for n in NAMES if not bodies[n].hide_render]
    T = {}
    for n in vis:
        T[n] = {k: tree(bodies[n], dg, FACES[n][k]) for k in ("L", "R", "T")}
        T[n]["C"] = [tree(c, dg, CLF[c.name]) for c in clothes[n] if not c.hide_render]
        T[n]["ALL"] = tree(bodies[n], dg)
    for n in vis:
        for s_ in "LR":
            h = T[n][s_]
            if h is None: continue
            if s_ == "L" and T[n]["R"] is not None:
                ov = h.overlap(T[n]["R"])
                if ov: hits.append((f, n, "hand L x hand R", len(ov)))
            if T[n]["T"] is not None:
                ov = h.overlap(T[n]["T"])
                if ov: hits.append((f, n, "hand %s x own torso/head" % s_, len(ov)))
            for ct in T[n]["C"]:
                if ct is None: continue
                ov = h.overlap(ct)
                if len(ov) > 3: hits.append((f, n, "hand %s x own clothes" % s_, len(ov)))
            for m in vis:
                if m == n: continue
                ov = h.overlap(T[m]["ALL"])
                if ov: hits.append((f, n, "hand %s x %s" % (s_, m), len(ov)))
for m in saved: m.show_viewport = True
with open(OUT, "w") as fh:
    fh.write("Hand audit every %d frames: %d hits\n" % (STEP, len(hits)))
    by = {}
    for f, n, k, c in hits: by.setdefault((n, k), []).append(f)
    for (n, k), fs in sorted(by.items()):
        fh.write("%s %s: %d frames (%d-%d) %s\n" % (n, k, len(fs), fs[0], fs[-1], fs[:30]))
print(open(OUT).read())
