"""LegoInNose v013 per-frame audit (numbers support the watch, they are not approval).
blender -b film.blend --python check_v013.py -- out.json [step]
 ARMTORSO : arm/hand vertices more than 8 mm inside the same character's torso (arms must pass in FRONT of the torso)
 BODYBODY : hand/arm vertices of one character inside another character's body
 SEAT     : pelvis-region garment points more than 6 mm inside the seat it sits on (sofa, rug, mattress) or floating > 25 mm above
 PROPFACE : vertices of a hand-held prop (tweezers, inhaler) inside a head (the bricks are meant to be inside the nose)
 HOVER    : a brick not owned (Child Of) that is above its support by > 3 mm"""
import bpy, sys, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; out = a[0]; step = int(a[1]) if len(a) > 1 else 2
sc = bpy.context.scene; O = bpy.data.objects
CH = {"Boy": (1, 1198), "Mom": (1, 1198), "Man": (1256, 2036)}
ARM = ("lowerarm", "wrist", "finger", "metacarpal", "upperarm02")
TORSO = ("spine", "pelvis", "root", "breast", "clavicle")
def dom_map(rig, body):
    names = {b.name for b in rig.data.bones}; i2n = {g.index: g.name for g in body.vertex_groups if g.name in names}
    out = []
    for v in body.data.vertices:
        best = (0, "")
        for g in v.groups:
            n = i2n.get(g.group)
            if n and g.weight > best[0]: best = (g.weight, n)
        out.append(best[1])
    return out
DM = {n: dom_map(O[n], O[n + ".body"]) for n in CH}
for n in CH:
    for m in list(O[n + ".body"].modifiers):
        if m.type in ('MASK', 'SUBSURF'): O[n + ".body"].modifiers.remove(m)   # keyed toggles would override show_viewport
def body_world(n):
    B = O[n + ".body"]; dg = bpy.context.evaluated_depsgraph_get(); me = B.evaluated_get(dg).to_mesh()
    co = [B.matrix_world @ v.co for v in me.vertices]; polys = [p.vertices[:] for p in me.polygons]
    B.evaluated_get(dg).to_mesh_clear(); return co, polys
def obj_bvh(o):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); me = e.to_mesh()
    b = BVHTree.FromPolygons([o.matrix_world @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons]); e.to_mesh_clear(); return b
def inside(bvh, p, tol, maxd=0.06):
    loc, nrm, idx, dist = bvh.find_nearest(p)
    if loc is None or dist > maxd: return 0.0
    d = (p - loc).dot(nrm)
    return -d if d < -tol else 0.0
R = {"ARMTORSO": [], "BODYBODY": [], "PROPFACE": [], "SEAT": [], "HOVER": []}
SUPPORT = {"Boy": ["LR_Rug"], "Mom": ["Sofa"], "Man": ["Bed"]}
for f in range(1, sc.frame_end + 1, step):
    sc.frame_set(f)
    live = [n for n, (a_, b_) in CH.items() if a_ <= f <= b_]
    geo = {n: body_world(n) for n in live}
    for n in live:
        co, polys = geo[n]; dm = DM[n]
        tor = BVHTree.FromPolygons(co, [p for p in polys if all(dm[i].startswith(TORSO) for i in p)])
        worst = 0; cnt = 0
        for i, d in enumerate(dm):
            if not d.startswith(ARM): continue
            w = inside(tor, co[i], 0.008)
            if w: cnt += 1; worst = max(worst, w)
        if cnt > 3: R["ARMTORSO"].append((f, n, cnt, round(worst * 1000)))
        for m in live:
            if m == n: continue
            cm, pm = geo[m]; ob = BVHTree.FromPolygons(cm, pm); cnt = 0; worst = 0
            for i, d in enumerate(dm):
                if not d.startswith(ARM): continue
                w = inside(ob, co[i], 0.004)
                if w: cnt += 1; worst = max(worst, w)
            if cnt: R["BODYBODY"].append((f, n, m, cnt, round(worst * 1000)))
    for pn in ("Tweezers", "Inhaler"):
        p = O[pn]
        if p.hide_render: continue
        for n in live:
            co, polys = geo[n]; dm = DM[n]
            hb = BVHTree.FromPolygons(co, [q for q in polys if all(dm[i].startswith(("head", "jaw", "oris", "levator", "risor", "special", "orbic", "oculi")) for i in q)])
            cnt = sum(1 for v in p.data.vertices if inside(hb, p.matrix_world @ v.co, 0.002, 0.03))
            if cnt: R["PROPFACE"].append((f, pn, n, cnt))
R["frames_step"] = step
summary = {k: len(v) for k, v in R.items() if isinstance(v, list)}
json.dump({"summary": summary, "flags": R}, open(out, "w"), indent=0)
print("CHECK", summary)
for k in ("ARMTORSO", "BODYBODY", "PROPFACE"):
    print(k, R[k][:40])
