"""BVH hand audit every N frames. blender -b anim.blend --python scripts/hand_audit.py -- <report.txt> [step]"""
import bpy, sys
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 2
sc = bpy.context.scene; D = bpy.data.objects
PEOPLE = ("Surgeon", "Nurse", "Anaes")
# evaluate without subsurf (same vertex indices as the base mesh)
for nm in PEOPLE:
    for o in D:
        if o.name.startswith(nm) and o.type == "MESH":
            for m in o.modifiers:
                if m.type != "ARMATURE" and not (o.name.endswith("_Gown") and m.type in ("DISPLACE", "SOLIDIFY")): m.show_viewport = False
glove = {}
for nm in PEOPLE:
    b = D[nm + ".body"]; gi = [i for i, m in enumerate(b.data.materials) if m and m.name.startswith("M_Glove")][0]
    hp = [p for p in b.data.polygons if p.material_index == gi]
    fg = {g.index for g in b.vertex_groups if g.name.startswith(("finger", "metacarpal"))}
    bones = {bn.name for bn in D[nm].data.bones}
    bg = {g.index for g in b.vertex_groups if g.name in bones}
    def fingerish(vi):
        gs = [g for g in b.data.vertices[vi].groups if g.group in bg]
        if not gs: return False
        top = max(gs, key=lambda g: g.weight)
        return top.group in fg and top.weight > 0.5
    armg = {g.index for g in b.vertex_groups if g.name.startswith(("clavicle", "shoulder", "upperarm", "lowerarm", "wrist", "finger", "metacarpal"))}
    def armish(vi):
        gs = [g for g in b.data.vertices[vi].groups if g.group in bg]
        return bool(gs) and max(gs, key=lambda g: g.weight).group in armg
    arm_v = {v.index for v in b.data.vertices if armish(v.index)}
    torso_polys = {p.index for p in b.data.polygons if not any(v in arm_v for v in p.vertices)}
    glove[nm] = {"torso_polys": torso_polys, "L": sorted({v for p in hp for v in p.vertices if b.data.vertices[v].co.x > 0 and fingerish(v)}),
                 "R": sorted({v for p in hp for v in p.vertices if b.data.vertices[v].co.x <= 0 and fingerish(v)}),
                 "polys_hand": {p.index for p in hp}}
def ev_mesh(o, dg):
    e = o.evaluated_get(dg); m = e.to_mesh(); M = e.matrix_world
    vs = [M @ v.co for v in m.vertices]; ps = [tuple(p.vertices) for p in m.polygons]; e.to_mesh_clear(); return vs, ps
def inside(pts, bvh, tol=0.003):
    n = 0
    for p in pts:
        loc, nrm, idx, d = bvh.find_nearest(p, 0.04)
        if loc is not None and (p - loc).dot(nrm) < -tol: n += 1
    return n
print("HANDVERTS", {nm: (len(glove[nm]["L"]), len(glove[nm]["R"])) for nm in PEOPLE})
HS = {nm: {s: set(glove[nm][s]) for s in 'LR'} for nm in PEOPLE}
rows = []; total = 0; flagged = []
for f in range(1, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    data = {}
    for nm in PEOPLE:
        if D[nm + ".body"].hide_render: continue
        vs, ps = ev_mesh(D[nm + ".body"], dg)
        hand_ps = glove[nm]["polys_hand"]
        torso = BVHTree.FromPolygons(vs, [p for i, p in enumerate(ps) if i in glove[nm]["torso_polys"]])
        hands = {s: [vs[i] for i in glove[nm][s][::2]] for s in "LR"}
        hbvh = {s: BVHTree.FromPolygons(vs, [p for i, p in enumerate(ps) if i in hand_ps and all(v in HS[nm][s] for v in p)]) for s in "LR"}
        others = []
        for suf in ("_Gown",):
            o = D.get(nm + suf)
            if o and not o.hide_render:
                v2, p2 = ev_mesh(o, dg); others.append((suf, BVHTree.FromPolygons(v2, p2)))
        data[nm] = dict(torso=torso, hands=hands, hbvh=hbvh, others=others)
    hits = []
    for nm, d in data.items():
        c = inside(d["hands"]["L"], d["hbvh"]["R"]) + inside(d["hands"]["R"], d["hbvh"]["L"])
        if c: hits.append(f"{nm}:hand-hand {c}")
        for s in "LR":
            c = inside(d["hands"][s], d["torso"], 0.006)
            if c: hits.append(f"{nm}.{s}:own-body {c}")
            for suf, bv in d["others"]:
                c = inside(d["hands"][s], bv, 0.006)
                if c: hits.append(f"{nm}.{s}:own{suf} {c}")
            for nm2, d2 in data.items():
                if nm2 == nm: continue
                c = inside(d["hands"][s], d2["torso"], 0.004)
                for suf, bv in d2["others"]: c += inside(d["hands"][s], bv, 0.004)
                if c: hits.append(f"{nm}.{s}:{nm2} {c}")
    if hits:
        flagged.append(f); n = sum(int(h.split()[-1]) for h in hits); total += n
        rows.append(f"f{f}: " + ", ".join(hits))
rows.append(f"HAND AUDIT: step {STEP}, frames flagged {len(flagged)}, sampled hand verts inside {total}")
open(OUT, "w").write("\n".join(rows) + "\n"); print("\n".join(rows[-40:]))
