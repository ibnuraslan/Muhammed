"""LegoInNose v013 hand-vs-face audit (blocking pass and final .blend).
blender -b film.blend --python check_hands_face.py -- out.json
 MOM_HAND_FACE: min distance from Mom's right hand/fingers to the boy's head skin and hair, 800-1198 (must be >= 10 mm)
 BOY_HAND_IN_FACE: boy left-hand vertices more than 2 mm inside his own head (insertion beats; fingertips may touch)"""
import bpy, sys, json
from mathutils.bvhtree import BVHTree
out = sys.argv[sys.argv.index("--") + 1:][0]
sc = bpy.context.scene; O = bpy.data.objects
def dom_map(rig, body):
    names = {b.name for b in rig.data.bones}; i2n = {g.index: g.name for g in body.vertex_groups if g.name in names}
    res = []
    for v in body.data.vertices:
        best = (0, "")
        for g in v.groups:
            n = i2n.get(g.group)
            if n and g.weight > best[0]: best = (g.weight, n)
        res.append(best[1])
    return res
HEADB = ("head", "jaw", "oris", "levator", "risor", "special", "orbic", "oculi", "nose", "eye", "temporalis", "mandible", "tongue", "cheek", "neck03")
for n in ("Boy", "Mom"):
    for m in list(O[n + ".body"].modifiers):
        if m.type in ('MASK', 'SUBSURF'): O[n + ".body"].modifiers.remove(m)   # keyed toggles would override show_viewport
DB = dom_map(O["Boy"], O["Boy.body"]); DM = dom_map(O["Mom"], O["Mom.body"])
HAIR = [O[n] for n in ("Boy.short02", "Boy.eyebrow001", "Boy.eyelashes01") if n in O]
def ev(o):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); me = e.to_mesh()
    co = [o.matrix_world @ v.co for v in me.vertices]; po = [p.vertices[:] for p in me.polygons]; e.to_mesh_clear(); return co, po
R = {"MOM_HAND_FACE": [], "BOY_HAND_IN_FACE": [], "hair_objects": [o.name for o in HAIR]}
frames = list(range(800, 1199, 2)) + list(range(40, 140, 2)) + list(range(270, 480, 3))
for f in sorted(set(frames)):
    sc.frame_set(f)
    bc, bp = ev(O["Boy.body"])
    hp = [p for p in bp if all(DB[i].startswith(HEADB) for i in p)]
    hb = BVHTree.FromPolygons(bc, hp)
    if f >= 800:
        targets = [hb] + [BVHTree.FromPolygons(*ev(h)) for h in HAIR]
        mc, _ = ev(O["Mom.body"])
        hand = [mc[i] for i, d in enumerate(DM) if d.endswith(".R") and d.startswith(("wrist", "finger", "metacarpal", "lowerarm"))]
        dmin = 9.0
        for t in targets:
            for p in hand:
                loc, nrm, idx, d = t.find_nearest(p)
                if loc is not None: dmin = min(dmin, d)
        R["MOM_HAND_FACE"].append((f, round(dmin * 1000, 1)))
    else:
        hand = [i for i, d in enumerate(DB) if d.endswith(".L") and d.startswith(("wrist", "finger", "metacarpal"))]
        worst = 0; cnt = 0
        for i in hand:
            loc, nrm, idx, d = hb.find_nearest(bc[i])
            if loc is None or d > 0.03: continue
            s = (bc[i] - loc).dot(nrm)
            if s < -0.002: cnt += 1; worst = max(worst, -s)
        if cnt: R["BOY_HAND_IN_FACE"].append((f, cnt, round(worst * 1000, 1)))
mh = min(R["MOM_HAND_FACE"], key=lambda x: x[1])
R["summary"] = {"mom_hand_face_min_mm": mh, "mom_frames_under_10mm": [x for x in R["MOM_HAND_FACE"] if x[1] < 10],
                "boy_hand_in_face_frames": len(R["BOY_HAND_IN_FACE"])}
json.dump(R, open(out, "w"), indent=0); print("HANDFACE", json.dumps(R["summary"])); print("BOYIN", R["BOY_HAND_IN_FACE"][:30])
