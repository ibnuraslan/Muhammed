"""Numeric penetration check (client clipping check): hand/finger and shoe vertices inside props and the set,
head items vs heads, characters through each other.  blender -b film.blend --python audit_penetration.py -- [step]"""
import sys, bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STEP = int(a[0]) if a else 4
DEPTH = 0.004
sc = bpy.context.scene
ACT = ["Prisoner", "Visitor", "Guard", "CrowdB", "YardP1", "YardP2", "Guard2"]
SKIP = ("CellDust", "Smoke", "PourStream", "Ground", "Laundry", "Flag", "Spark", "Pigeon", "CrowdHat", "President_Glasses", "Lantern_Patrol")
hand_bones = lambda s: [b for b in ("wrist.%s" % s,) + tuple("finger%d-%d.%s" % (k, j, s) for k in range(1, 6) for j in range(1, 4))]
def body_of(n): return next(c for c in bpy.data.objects[n].children if c.name.endswith(".body"))
def shoes_of(n): return next(c for c in bpy.data.objects[n].children if "shoes" in c.name)
HAND_IDX = {}
for n in ACT:
    b = body_of(n); names = set(hand_bones("L") + hand_bones("R"))
    gi = {g.index for g in b.vertex_groups if g.name in names}
    HAND_IDX[n] = [v.index for v in b.data.vertices if any(g.group in gi and g.weight > 0.5 for g in v.groups)][::3]
props = [o for o in bpy.data.objects if o.type == 'MESH' and not o.name.startswith(SKIP) and not any(o.name.startswith(n + ".") for n in ACT)
         and not o.name.startswith(("President.", "CrowdA.", "CrowdC.", "Crowd0", "Crowd1")) and o.parent not in [bpy.data.objects.get(x) for x in ("President", "CrowdA", "CrowdC")]]
def bvh(o, dg):
    e = o.evaluated_get(dg); me = e.to_mesh(); bm = bmesh.new(); bm.from_mesh(me); bm.transform(e.matrix_world); t = BVHTree.FromBMesh(bm); bm.free(); e.to_mesh_clear(); return t
def inside(t, p):
    """negative depth if p is inside the closed surface: near a face (<5 cm), behind its normal, and odd ray parity"""
    hit = t.find_nearest(p, 0.05)
    if hit[0] is None: return 1.0
    d = p - hit[0]
    if d.dot(hit[1]) >= 0: return d.length
    for dirn in (Vector((0.0, 0.0, 1.0)), Vector((0.31, 0.47, 0.83)).normalized()):
        cnt, o = 0, p.copy()
        for _ in range(24):
            h = t.ray_cast(o + dirn * 1e-4, dirn)
            if h[0] is None: break
            cnt += 1; o = h[0]
        if cnt % 2 == 0: return d.length
    return -d.length
res = {}; frames = 0; overlaps = 0
for f in range(1, 1891, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); frames += 1
    vis = [n for n in ACT if not bpy.data.objects[n].hide_render]
    pts = {}
    for n in vis:
        b = body_of(n).evaluated_get(dg); me = b.to_mesh(); M = b.matrix_world
        pts[(n, "hand")] = [M @ me.vertices[i].co for i in HAND_IDX[n] if i < len(me.vertices)]; b.to_mesh_clear()
        s_ = shoes_of(n).evaluated_get(dg); me = s_.to_mesh(); M = s_.matrix_world
        pts[(n, "foot")] = [M @ v.co for v in me.vertices][::4]; s_.to_mesh_clear()
    if not pts: continue
    allp = [p for v in pts.values() for p in v]
    lo = Vector([min(p[i] for p in allp) - 0.3 for i in range(3)]); hi = Vector([max(p[i] for p in allp) + 0.3 for i in range(3)])
    near = []
    for o in props:
        if o.hide_render: continue
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        if all(any(lo[i] <= max(c[i] for c in bb) and min(c[i] for c in bb) <= hi[i] for _ in (0,)) for i in range(3)): near.append(o)
    trees = {o.name: bvh(o, dg) for o in near}
    for (n, part), P_ in pts.items():
        for on, t in trees.items():
            if part == "foot" and on.startswith(("Cell_Floor", "Corr_Floor", "Shop_Floor")):  # floors checked by audit_contacts
                continue
            dmin = min((inside(t, p) for p in P_), default=1)
            if dmin < -DEPTH:
                k = (n, part, on); r = res.setdefault(k, [0, 0.0, f]); r[0] += 1; r[1] = min(r[1], dmin)
    for i, n in enumerate(vis):
        for m in vis[i + 1:]:
            pa = bpy.data.objects[n].pose.bones["root"].head; pb = bpy.data.objects[m].pose.bones["root"].head
            if (pa - pb).to_2d().length < 0.35: overlaps += 1
# head items: hat / glasses vertices inside the head (head poking through)
hat_bad = 0
for f in (1740, 1800, 1860, 1890):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    for h in [o for o in bpy.data.objects if o.name.startswith(("CrowdHat", "President_Glasses"))]:
        arm = h.constraints[0].target; body = next(c for c in arm.children if c.name.endswith(".body") or "body" in c.name)
        if h.constraints[0].subtarget != "head": continue
        t = bvh(body, dg); e = h.evaluated_get(dg); me = e.to_mesh()
        hat_bad += sum(1 for v in me.vertices if inside(t, e.matrix_world @ v.co) < -DEPTH); e.to_mesh_clear()
total = sum(r[0] for r in res.values())
print("PEN frames_checked", frames, "step", STEP, "depth_threshold_m", DEPTH)
for (n, part, on), (c, d, f0) in sorted(res.items(), key=lambda x: -x[1][0]):
    print("PEN %-9s %-4s in %-28s frames=%3d max_depth=%.3f first=%d" % (n, part, on, c, -d, f0))
print("PEN_TOTAL hand/foot penetration frame-hits", total, "| character overlaps", overlaps, "| head-item verts through", hat_bad)
