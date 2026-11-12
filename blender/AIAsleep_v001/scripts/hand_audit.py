"""Hand audit (STYLE_ANIMATED.md "Hands"): every 2 frames, BVH checks of
hand vs other hand, hand vs own torso/shirt, hand vs head; plus hands off the rim while meant to grip.
blender -b work/final.blend --python scripts/hand_audit.py -- <report>"""
import sys, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
rep = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; O = bpy.data.objects; rig = O["Driver"]; RM = rig.matrix_world
for o in (O["Driver.body"], O["Driver.male_casualsuit01"]):
    for md in o.modifiers:
        if md.type == "SUBSURF": md.show_viewport = False
TORSO = ("spine", "pelvis", "clavicle", "neck", "breast", "pectoral", "shoulder01", "root")
def region_bvh(o, prefixes, dg):
    e = o.evaluated_get(dg); m = e.to_mesh(); M = o.matrix_world
    names = {g.index: g.name for g in o.vertex_groups}
    keep = []
    for v in m.vertices:
        w = sum(g.weight for g in v.groups if names.get(g.group, "").startswith(prefixes))
        keep.append(w > 0.6)
    vs = [M @ v.co for v in m.vertices]
    fs = [list(p.vertices) for p in m.polygons if all(keep[i] for i in p.vertices)]
    e.to_mesh_clear(); return BVHTree.FromPolygons(vs, fs)
def hand_pts(s):
    pts = []
    for pb in rig.pose.bones:
        if pb.name.endswith("." + s) and pb.name.startswith(("finger", "metacarpal")):
            for t in (0.0, 0.5, 1.0): pts.append(RM @ pb.head.lerp(pb.tail, t))
    return pts
wheel = [o for o in O if o.type == "MESH" and o.name.startswith("Wheel_Steering")]
hits = {"hand_vs_hand": [], "hand_vs_torso_shirt": [], "hand_vs_head": [], "hand_in_rim": []}
def inside(bvh, p, tol):
    loc, n, _, d = bvh.find_nearest(p)
    return loc is not None and ((p - loc).dot(n) < 0 and d < 0.03 or d < tol)
FR = [int(x) for x in sys.argv[sys.argv.index("--") + 2:]] or list(range(1, sc.frame_end + 1, 2))
for f in FR:
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    tor = region_bvh(O["Driver.male_casualsuit01"], TORSO, dg); head = region_bvh(O["Driver.body"], ("head", "neck", "jaw"), dg)
    vs, fs, off = [], [], 0
    for o in wheel:
        e = o.evaluated_get(dg); m = e.to_mesh(); vs += [o.matrix_world @ v.co for v in m.vertices]; fs += [[i + off for i in p.vertices] for p in m.polygons]; off += len(m.vertices); e.to_mesh_clear()
    wb = BVHTree.FromPolygons(vs, fs)
    L, Rr = hand_pts("L"), hand_pts("R")
    if min((a - b).length for a in L for b in Rr) < 0.03: hits["hand_vs_hand"].append(f)
    for s, P in (("L", L), ("R", Rr)):
        if sum(inside(tor, p, 0.006) for p in P) > 0: hits["hand_vs_torso_shirt"].append((f, s))
        if sum(inside(head, p, 0.006) for p in P) > 0: hits["hand_vs_head"].append((f, s))
        n_in = sum(1 for p in P for loc, nrm, _, d in [wb.find_nearest(p)] if loc is not None and (p - loc).dot(nrm) < -0.004)
        if n_in: hits["hand_in_rim"].append((f, s, n_in))
txt = "AIAsleep hand audit, every 2 frames (%d frames)\n" % len(FR)
for k, v in hits.items(): txt += "%s: %d  %s\n" % (k, len(v), v[:30])
print(txt); open(rep, "w").write(txt)
