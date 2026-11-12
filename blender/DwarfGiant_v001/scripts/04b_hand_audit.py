"""BVH hand audit (client 23:00), every 2 frames while a character renders:
hand vs other hand, hand vs own torso/head/clothes-torso, hand vs other characters (bodies + clothes).
blender -b film.blend --python 04b_hand_audit.py -- <out_txt> [step]"""
import bpy, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 2
sc = bpy.context.scene; OB = bpy.data.objects
CH = [n[4:] for n in OB.keys() if n.startswith("RIG_")]
HAND_P = ("wrist.", "finger", "metacarpal")
TORSO_P = ("spine", "pelvis", "neck", "head", "clavicle", "breast", "shoulder", "jaw", "special", "oris", "levator", "orbic", "oculi",
           "temporalis", "risorius", "eye", "tongue")

def classify(o):
    """vertex index -> 'L','R','T' or None from the dominant deform group"""
    rig = o.parent; bones = set(rig.data.bones.keys()) if rig and rig.type == "ARMATURE" else set()
    names = {g.index: g.name for g in o.vertex_groups if g.name in bones}; out = {}
    bodyg = o.vertex_groups["body"].index if "body" in o.vertex_groups else None
    for v in o.data.vertices:
        if bodyg is not None and not any(g.group == bodyg and g.weight > 0.5 for g in v.groups): continue   # skip MPFB helper geometry
        gs = [g for g in v.groups if g.group in names]
        if not gs: continue
        g = max(gs, key=lambda x: x.weight); n = names[g.group]
        if n.startswith(HAND_P): out[v.index] = "L" if n.endswith(".L") else ("R" if n.endswith(".R") else None)
        elif n.startswith(TORSO_P) or n in ("root",): out[v.index] = "T"
    return out

INFO = {}
for ch in CH:
    body = OB.get(ch + ".body")
    if not body: continue
    clothes = [o for o in OB if o.parent == OB["RIG_" + ch] and o.type == "MESH" and any(k in o.name for k in ("suit", "worksuit"))]
    INFO[ch] = dict(body=body, cls=classify(body), clothes=[(c, classify(c)) for c in clothes])

def tris(o, dg, keep=None, cls=None):
    e = o.evaluated_get(dg); m = e.to_mesh(); M = e.matrix_world
    vs = [M @ v.co for v in m.vertices]
    if keep is not None and len(m.vertices) != len(o.data.vertices):
        e.to_mesh_clear(); return None   # topology changed by modifiers (masks/subsurf) -> mapping unreliable
    polys = [p.vertices[:] for p in m.polygons if keep is None or all(cls.get(i) == keep for i in p.vertices)]
    e.to_mesh_clear()
    if not polys: return None
    return BVHTree.FromPolygons(vs, polys)

def eval_copy_noncage(o):
    """temporarily disable topology-changing modifiers so vertex indices match the base mesh"""
    st = []
    for m in o.modifiers:
        if m.type in ("SUBSURF", "MASK", "SOLIDIFY", "DISPLACE"):
            st.append((m, m.show_viewport)); m.show_viewport = False
    return st

for ch, d in INFO.items():
    for o in [d["body"]] + [c for c, _ in d["clothes"]]:
        d.setdefault("restore", []).extend(eval_copy_noncage(o))

hits = []; count = {"hand_hand": 0, "hand_self": 0, "hand_other": 0}
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    if f % 200 == 1: print('PROG', f, count, flush=True)
    live = [ch for ch, d in INFO.items() if not d["body"].hide_render]
    cache = {}
    for ch in live:
        d = INFO[ch]
        H = {s: tris(d["body"], dg, s, d["cls"]) for s in "LR"}
        T = [tris(d["body"], dg, "T", d["cls"])] + [tris(c, dg, "T", cl) for c, cl in d["clothes"] if not c.hide_render]
        cache[ch] = (H, [t for t in T if t])
    for ch in live:
        H, T = cache[ch]
        if H["L"] and H["R"] and H["L"].overlap(H["R"]):
            count["hand_hand"] += 1; hits.append(f"f{f} {ch} hand L x hand R")
        for s in "LR":
            if not H[s]: continue
            for t in T:
                if H[s].overlap(t):
                    count["hand_self"] += 1; hits.append(f"f{f} {ch} hand {s} x own torso/head/clothes"); break
            for oc in live:
                if oc == ch: continue
                ob, oT = cache[oc]
                if (INFO[oc]["body"].matrix_world.translation - INFO[ch]["body"].matrix_world.translation).length > 3 and \
                   (OB["RIG_" + oc].pose.bones["root"].head - OB["RIG_" + ch].pose.bones["root"].head).length > 3: pass
                for t in oT + [x for x in ob.values() if x]:
                    if H[s].overlap(t):
                        count["hand_other"] += 1; hits.append(f"f{f} {ch} hand {s} x {oc}"); break
for m, v in [x for d in INFO.values() for x in d.get("restore", [])]: m.show_viewport = v
txt = "HAND AUDIT step %d frames %d-%d: %s total %d\n" % (STEP, sc.frame_start, sc.frame_end, count, sum(count.values())) + "\n".join(hits) + "\n"
open(OUT, "w").write(txt); print(txt[:3000])
