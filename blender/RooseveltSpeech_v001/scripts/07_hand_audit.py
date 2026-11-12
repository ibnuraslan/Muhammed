"""Hand audit (client rule, Nov 11 23:00): every 2 frames, hero hands vs own torso/clothes/head, hand vs hand,
joint ranges (finger back-bends, wrist and elbow limits). Crowd hands are checked for hand-vs-hand within each person.
blender -b anim.blend --python 07_hand_audit.py -- report.json [step]"""
import sys, json, math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 2
sc = bpy.context.scene; vl = bpy.context.view_layer
for lc in vl.layer_collection.children:          # only the hero needs evaluating: speeds up frame_set
    if lc.name in ("Crowds", "Street", "Hall", "CrowdLib"): lc.exclude = True
H = bpy.data.objects["Hero"]
body = bpy.data.objects["Hero.body"]; suit = next(o for o in H.children if "elegantsuit" in o.name)
saved = []
for o in (body, suit):
    for m in o.modifiers:
        if m.type in ("SUBSURF", "MASK") and m.show_viewport: m.show_viewport = False; saved.append(m)
TORSO_GROUPS = ("spine", "neck", "head", "breast", "clavicle", "pelvis", "jaw")
gi = {g.index for g in body.vertex_groups if g.name.startswith(TORSO_GROUPS)}
torso_v = {v.index for v in body.data.vertices if sum(g.weight for g in v.groups if g.group in gi) > 0.6}
torso_f = [p.index for p in body.data.polygons if all(i in torso_v for i in p.vertices)]
FING = {s: [b.name for b in H.data.bones if b.name.startswith("finger") and b.name.endswith("." + s)] for s in "LR"}
def hand_pts(s):
    pts = []
    for n in FING[s]:   # finger segments beyond the knuckles (the root of each finger sits inside the palm/cuff)
        if n.split(".")[0].endswith("-1") and not n.startswith("finger1"): continue
        if n.startswith("finger1-1"): continue
        pb = H.pose.bones[n]; h_ = H.matrix_world @ pb.head; t_ = H.matrix_world @ pb.tail
        pts += [h_.lerp(t_, u) for u in (0.5, 1.0)]
    return pts
def tree(o, faces=None):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); me = e.to_mesh(); M = o.matrix_world
    vs = [M @ v.co for v in me.vertices]
    ps = [tuple(me.polygons[i].vertices) for i in faces] if faces is not None else [tuple(p.vertices) for p in me.polygons]
    e.to_mesh_clear(); return BVHTree.FromPolygons(vs, ps)
def inside(t, pts, depth=0.004):
    n = 0
    for v in pts:
        loc, nrm, idx, d = t.find_nearest(v)
        if loc is not None and d < 0.04 and (v - loc).dot(nrm) < -depth: n += 1
    return n
def local_euler(n):
    return H.pose.bones[n].matrix_basis.to_euler("XYZ")
# grips/contacts that are intended (fingers wrap a prop, not the body), so only body/clothes/head + hand-vs-hand count
rep = {"hits": [], "joint": [], "frames": 0}
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); rep["frames"] += 1
    tb = tree(body, torso_f); ts = tree(suit)
    ghost = 460 <= f <= 1192   # x-ray: body and coat are rendered as a see-through ghost (the hand enters the ghost pocket)
    for s in "LR":
        hp = hand_pts(s)
        nb, ns = (0, 0) if ghost else (inside(tb, hp), inside(ts, hp))
        if nb: rep["hits"].append((f, "hand." + s, "own torso/head", nb))
        if ns: rep["hits"].append((f, "hand." + s, "own clothes", ns))
    dmin = min((p - q).length for p in hand_pts("L") for q in hand_pts("R"))
    if dmin < 0.015: rep["hits"].append((f, "hand.L", "hand.R", round(dmin, 3)))
    for s in "LR":   # joint ranges: finger back-bend / spread, wrist, elbow
        for n in FING[s]:
            e = local_euler(n)
            if e.x < math.radians(-5) or e.x > math.radians(95) or abs(e.z) > math.radians(15):
                rep["joint"].append((f, n, [round(math.degrees(x)) for x in e])); break
        wr = H.pose.bones["wrist." + s]; la = H.pose.bones["lowerarm02." + s]
        # flex/side only (twist about the forearm is natural): change of the hand axis relative to the forearm vs rest
        fa = (la.tail - la.head).normalized(); hd = (H.pose.bones["finger3-1." + s].head - wr.head).normalized()
        fa0 = (H.data.bones["lowerarm02." + s].tail_local - H.data.bones["lowerarm02." + s].head_local).normalized()
        hd0 = (H.data.bones["finger3-1." + s].head_local - H.data.bones["wrist." + s].head_local).normalized()
        ang = abs(math.degrees(math.acos(max(-1, min(1, fa.dot(hd))))) - math.degrees(math.acos(max(-1, min(1, fa0.dot(hd0))))))
        if ang > 60: rep["joint"].append((f, "wrist." + s, round(ang)))
        ua = H.pose.bones["upperarm02." + s]; lo = H.pose.bones["lowerarm01." + s]
        d1 = (ua.tail - ua.head).normalized(); d2 = (lo.tail - lo.head).normalized()
        bend = math.degrees(math.acos(max(-1, min(1, d1.dot(d2)))))
        side = d1.cross(d2).dot(H.matrix_world.to_3x3() @ Vector((0, 0, 1)))
        if bend > 150: rep["joint"].append((f, "elbow." + s, round(bend)))
rep["count_hits"] = len(rep["hits"]); rep["count_joint"] = len(rep["joint"])
for m in saved: m.show_viewport = True
json.dump(rep, open(OUT, "w"), indent=0)
print("HANDAUDIT frames", rep["frames"], "hits", rep["count_hits"], "joint", rep["count_joint"])
