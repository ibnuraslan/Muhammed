"""PopeShot audit: hover / sink of planted feet, hand & fingertip penetration into props/bodies, head-worn item clipping,
camera inside geometry.  blender -b PopeShot_anim.blend --python audit.py -- <report.txt>"""
import sys, bpy, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; O = bpy.data.objects
dg = bpy.context.evaluated_depsgraph_get()
STATIC = [o for o in O if o.type == 'MESH' and not o.hide_render and (o.parent is None or o.parent.type != 'ARMATURE')
          and not o.name.startswith(("XRay", "Trace", "Bullet", "Muzzle", "Pigeon", "CellHaze", "ShrineHaze", "Flag", "Drape", "ECG", "Monitor", "skeleton", "aorta", "guts", "handbones", "spine", "Relic"))
          and all(c.name not in ("Hidden",) for c in o.users_collection)]
def bvh_of(o):
    e = o.evaluated_get(dg); me = e.to_mesh()
    M = o.matrix_world
    b = BVHTree.FromPolygons([M @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons])
    e.to_mesh_clear(); return b
def inside(b, p, tol=0.004):
    loc, n, i, d = b.find_nearest(p)
    if loc is None: return False, 9
    return (p - loc).dot(n) < -tol and d < 0.25, d
REP = []
def log(s): REP.append(s); print(s)
FRAMES = list(range(1, 1621, 20))
HEROES = ["Pope", "Prisoner", "AideA", "AideB", "GuardA", "GuardB", "SurgA", "SurgB", "SurgC", "Nurse", "Shooter"]
TIPS = ["finger%d-3.%s" % (i, s) for i in range(1, 6) for s in "LR"]
counts = dict(hover=0, sink=0, hand_pen=0, head_item=0, cam_inside=0)
FLOORS = {}
for f in FRAMES:
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    cam = sc.camera.matrix_world.translation.copy()
    # static scene BVHs near the camera / characters (cheap filter by distance)
    near = [o for o in STATIC if (o.matrix_world.translation - cam).length < 60 or o.dimensions.length > 20]
    trees = {o.name: bvh_of(o) for o in near if len(o.data.polygons) < 400000}
    for nm, b in trees.items():
        ins, d = inside(b, cam, 0.01)
        if ins and nm not in ("Ground",):
            counts["cam_inside"] += 1; log("CAM_INSIDE f%d %s d=%.3f" % (f, nm, d))
    for h in HEROES:
        r = O.get(h)
        if not r or r.matrix_world.translation.z < -20: continue
        root = r.matrix_world.translation
        if (root - cam).length > 25: continue
        # feet: lowest point of the foot bone vs ground below (ray down into static trees)
        for s in "LR":
            pb = r.pose.bones["foot." + s]; p = r.matrix_world @ pb.head; tip = r.matrix_world @ pb.tail
            best = None
            for nm, b in trees.items():
                hit = b.ray_cast(p + Vector((0, 0, 0.3)), Vector((0, 0, -1)), 2.0)
                if hit[0] is not None and (best is None or hit[0].z > best): best = hit[0].z
            if best is None: continue
            gap = p.z - best
            seated = h in ("Pope", "Prisoner") and 1015 <= f < 1153 or h == "Pope" and f >= 1153 or h == "Pope" and 631 <= f < 763
            if seated: continue
            if gap > 0.16: counts["hover"] += 1; log("HOVER f%d %s foot.%s gap=%.3f" % (f, h, s, gap))
            if gap < 0.03: counts["sink"] += 1; log("SINK f%d %s foot.%s gap=%.3f" % (f, h, s, gap))
        # fingertips inside props
        for t in TIPS:
            p = r.matrix_world @ r.pose.bones[t].tail
            for nm, b in trees.items():
                ins, d = inside(b, p)
                if ins: counts["hand_pen"] += 1; log("HAND_IN f%d %s %s -> %s d=%.3f" % (f, h, t, nm, d)); break
    # head-worn items vs their head (vertices of the shell inside the body)
    for o in O:
        if o.type != 'MESH' or not o.name.endswith(("_Zucchetto", "_Cap", "_Mask")): continue
        r = o.parent
        if not r or r.matrix_world.translation.z < -20 or (r.matrix_world.translation - cam).length > 12: continue
        body = next(c for c in r.children if c.name.endswith(".body"))
        bb = bvh_of(body); e = o.evaluated_get(dg); me = e.to_mesh()
        n_in = sum(1 for v in me.vertices if inside(bb, o.matrix_world @ v.co, 0.002)[0])
        tot = len(me.vertices); e.to_mesh_clear()
        if n_in > 0.02 * tot: counts["head_item"] += 1; log("HEAD_ITEM f%d %s %d/%d verts inside head" % (f, o.name, n_in, tot))
log("SUMMARY frames=%d %s" % (len(FRAMES), counts))
open(out, "w").write("\n".join(REP) + "\n")
