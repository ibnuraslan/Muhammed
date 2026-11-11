"""Contact audit for FrozenTearsGun: feet hover/sink/slide, fingertips inside body or props, tears inside skin,
camera inside geometry. blender -b film.blend --python audit.py -- <report.txt> [step]"""
import sys, math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 6
sc = bpy.context.scene; cam = sc.camera
lines = []
def log(*x): lines.append(" ".join(str(v) for v in x))
def bvh(o, dg):
    oe = o.evaluated_get(dg); me = oe.to_mesh()
    mw = oe.matrix_world
    verts = [mw @ v.co for v in me.vertices]; polys = [tuple(p.vertices) for p in me.polygons]
    oe.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys), verts
def inside(tree, p, maxd=0.05):
    loc, nrm, idx, d = tree.find_nearest(p, maxd)
    if loc is None: return None
    return (p - loc).dot(nrm) < 0, d
PERIODS = {"Inventor": [(1, 1150, "workshop"), (1151, 1700, "office"), (1701, 2100, "workshop")],
           "Mentor": [(1, 1700, "office"), (1701, 2100, "workshop")]}
SEEN = {"Inventor": [(1, 1150), (1160, 1700), (1720, 2100)], "Mentor": [(1160, 1700), (1880, 2100)]}
stats = {}
DET = {}
def bump(k, v, f, who=""):
    s = stats.setdefault(k, [0, 0.0, None]); s[0] += 1
    if abs(v) > abs(s[1]): s[1] = v; s[2] = f
    DET.setdefault(k, []).append("%d%s" % (f, (":" + who) if who else ""))
prev_foot = {}
cam_bad = []
props = [o for o in bpy.data.objects if o.type == 'MESH' and (o.name.startswith("Gun_") or o.name.startswith("OF_Desk") or o.parent and o.parent.name in ("OF_Desk", "WS_Bench"))]
for f in range(1, 2101, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    for hn in ("Inventor", "Mentor"):
        if not any(a_ <= f <= b_ for a_, b_ in SEEN[hn]): continue
        rig = bpy.data.objects[hn]
        shoes = [o for o in rig.children if "shoes" in o.name][0]
        oe = shoes.evaluated_get(dg); me = oe.to_mesh(); mw = oe.matrix_world
        root_x = (rig.matrix_world @ rig.pose.bones["root"].head)
        for side, sg in (("L", 1), ("R", -1)):
            fb = rig.matrix_world @ rig.pose.bones["foot." + side].head
            zs = [(mw @ v.co) for v in me.vertices]
            zs = [p for p in zs if (p - fb).to_2d().length < 0.2]
            if not zs: continue
            mz = min(p.z for p in zs)
            if mz > 0.012: bump(hn + " foot hover >1.2cm", mz, f)
            if mz < -0.015: bump(hn + " foot sink >1.5cm", mz, f)
            k = (hn, side)
            if k in prev_foot and mz < 0.012:
                pf_, pz, pfr = prev_foot[k]
                if pz < 0.012 and pfr == f - STEP:
                    sl = (fb - pf_).to_2d().length
                    if sl > 0.012 and not any(abs(f - x) <= STEP for x in (1151, 1701, 1759, 1819)): bump(hn + " planted foot slide >1.2cm/step", sl, f, side)
            prev_foot[k] = (fb.copy(), mz, f)
        oe.to_mesh_clear()
        # fingertips inside own body or props
        body = [o for o in rig.children if o.name.endswith(".body")][0]
        tb, _ = bvh(body, dg)
        for side in "LR":
            for k_ in range(1, 6):
                tip = rig.matrix_world @ rig.pose.bones["finger%d-3.%s" % (k_, side)].tail
                r = inside(tb, tip, 0.03)
                if r and r[0] and r[1] > 0.006: bump(hn + " fingertip inside body >6mm", r[1], f)
    # tears vs skin
    if f <= 1150:
        tb, _ = bvh(bpy.data.objects["Inventor.body"], dg)
        for o in [x for x in bpy.data.objects if x.name.startswith("Tear") and x.type == 'MESH' and "Tube" not in x.name and "Streak" not in x.name]:
            p = o.matrix_world.translation
            if p.z < -10 or o.matrix_world.to_scale().x < 0.05: continue
            r = inside(tb, p, 0.02)
            if r is None: continue
            rad = 0.0028 * o.matrix_world.to_scale().x
            if r[0]: bump("tear centre inside skin", r[1], f, o.name)
            elif r[1] < rad * 0.5: bump("tear sunk >half radius into skin", r[1], f)
    # camera inside geometry: shoot 6 rays; if most nearest hits are back faces we are inside
    p = cam.matrix_world.translation; back = 0; hits = 0
    for d in (Vector((1, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((0, 0, -1))):
        h, loc, nrm, idx, ob, _ = sc.ray_cast(dg, p, d, distance=0.5)
        if h:
            hits += 1
            if nrm.dot(d) > 0 and not ob.name.startswith(("ThoughtBubble", "ExplainerCard", "Gas", "ImpactPuff", "MuzzlePuff", "OF_", "WS_")): back += 1
    if back >= 3: cam_bad.append((f, back))
    fwd = -(cam.matrix_world.to_3x3().col[2])
    h, loc, nrm, idx, ob, _ = sc.ray_cast(dg, p, fwd, distance=cam.data.clip_start * 2)
    if h and not ob.name.startswith(("ThoughtBubble", "ExplainerCard")): bump("camera clip plane touches " + ob.name, (loc - p).length, f)
log("FrozenTearsGun audit, every %d frames" % STEP)
for k, (n, worst, wf) in sorted(stats.items()):
    log("%-48s count %4d  worst %.4f m at frame %s" % (k, n, worst, wf))
    log("    frames: " + " ".join(DET[k][:40]))
if not stats: log("no contact problems found")
log("camera inside closed geometry:", cam_bad if cam_bad else "none")
open(OUT, "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
