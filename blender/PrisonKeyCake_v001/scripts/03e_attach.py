"""Props in hand: re-key each held prop from the hand's actual grasp point (thumb tip + index/middle), so a carried
prop sits IN the fingers on every frame (no offset gap). Run last in the 03 chain (after 03d_hands)."""
import bpy, os, sys
from mathutils import Vector, Matrix
sc = bpy.context.scene
MEASURE = os.environ.get("ATTACH_MEASURE") == "1"
def arm_of(name): return [o for o in bpy.data.objects if o.type == 'ARMATURE' and o.name.startswith(name)][0]
def grasp(arm, s):
    M = arm.matrix_world; pb = arm.pose.bones
    pts = [M @ pb["finger1-3." + s].tail, M @ pb["finger2-2." + s].tail, M @ pb["finger3-2." + s].tail]
    return sum(pts, Vector()) / len(pts)
V = Vector
# object, actor, side, ranges, grip point in the prop's local space
HOLD = [
    ("Key_Master", "Prisoner", "R", [(1, 109), (259, 380), (1098, 1111), (1159, 1180)], V((-0.045, 0, 0))),
    ("Key_Copy1", "CrowdB", "R", [(730, 772)], V((-0.045, 0, 0))),
    ("Key_Copy1", "Prisoner", "R", [(845, 893), (1019, 1040)], V((-0.045, 0, 0))),
    ("Key_Copy2", "Prisoner", "R", [(1354, 1399)], V((-0.045, 0, 0))),
    ("WaxMold_Pocket", "Visitor", "R", [(330, 410)], V((0, 0.07, 0))),
    ("WaxMold_Pocket", "Prisoner", "R", [(1190, 1216)], V((0, 0.075, 0))),
    ("ParcelBox_Lid", "CrowdB", "R", [(798, 813)], V((0, 0, 0.03))),
    ("Knife_Blade", "Prisoner", "R", [(1294, 1346)], V((-0.05, 0, 0))),
    ("Crucible", "CrowdB", "R", [(470, 640)], V((-0.5, 0, 0))),
]
BL = 3
for name, actor, s, ranges, loc in HOLD:
    o = bpy.data.objects.get(name)
    if o is None: print("ATTACH missing", name); continue
    arm = arm_of(actor)
    for a, b in ranges:
        D = {}
        for f in range(a, b + 1, 2):
            sc.frame_set(f)
            D[f] = grasp(arm, s) - o.matrix_world @ loc
        mx = max(d.length for f, d in D.items() if a + 2 * BL <= f <= b - 2 * BL) if b - a > 4 * BL else max(d.length for d in D.values())
        print("ATTACH %-15s %-8s %4d-%4d max gap %.3f" % (name, actor, a, b, mx))
        if MEASURE: continue
        for f, d in D.items():
            w = min(1.0, (f - a + 1) / BL, (b - f + 1) / BL) if (b - a) > 2 * BL else 1.0
            sc.frame_set(f)
            o.location = o.location + d * w; o.keyframe_insert("location", frame=f)
# glasses: sit on the nose (median gap to the skin under 1.5 cm)
from mathutils.bvhtree import BVHTree
g = bpy.data.objects.get("President_Glasses")
if g is not None and not MEASURE:
    sc.frame_set(1800); dg = bpy.context.evaluated_depsgraph_get()
    gw = g.matrix_world @ (sum((Vector(c) for c in g.bound_box), Vector()) / 8)
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE' and "head" in o.pose.bones]
    r = min(arms, key=lambda q: (q.matrix_world @ q.pose.bones["head"].head - gw).length)
    body = max([c for c in r.children_recursive if c.type == 'MESH' and "body" in c.name.lower()], key=lambda c: len(c.data.vertices))
    for it in range(3):
        sc.frame_set(1800); dg = bpy.context.evaluated_depsgraph_get()
        eb = body.evaluated_get(dg); mb = eb.to_mesh(); mw = eb.matrix_world
        bvh = BVHTree.FromPolygons([mw @ v.co for v in mb.vertices], [tuple(p.vertices) for p in mb.polygons]); eb.to_mesh_clear()
        gm = g.matrix_world; ds = []
        for v in g.data.vertices:
            w = gm @ v.co; loc, n, i, d = bvh.find_nearest(w, 0.5)
            if loc is not None: ds.append((d, loc - w))
        ds.sort(key=lambda x: x[0]); med = ds[len(ds) // 2][0]
        print("ATTACH glasses median gap %.3f" % med)
        if med < 0.010: break
        mv = sum((x[1] for x in ds[:len(ds) // 2 + 1]), Vector()) / (len(ds) // 2 + 1)
        mv = mv.normalized() * (med - 0.006)
        lv = gm.to_3x3().inverted() @ mv
        for v in g.data.vertices: v.co += lv
print("ATTACH done")
