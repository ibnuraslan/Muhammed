"""ShoeBomber contact audit. blender -b film.blend --python audit.py -- <report.txt>
- sink/hover: lowest evaluated body+shoe vertex per human vs the floor (z=0), every 10 frames while the human is on screen-relevant sets
- reach: IK_hand / IK_foot target vs the solved wrist / ankle (IK failing to reach = hand not on the prop)
- camera: inside closed geometry (nearest hit is a back face) or within 3 cm of a surface
- props: carried shoes / syringe / match vs the holding bone"""
import sys, bpy, math
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; O = bpy.data.objects
lines = []
def log(s): lines.append(s); print(s)
HN = ["Bomber", "Attendant", "Steward", "PaxA", "PaxB", "PaxC", "PaxD", "Traveller", "Officer"]
# frames where each human matters (on the set the camera is on)
ACTIVE = {n: (1, 1068) for n in HN}
ACTIVE.update({"Traveller": (1393, 1620), "Officer": (1393, 1620)})
ACTIVE["PaxC"] = (1, 1068); ACTIVE["PaxD"] = (1, 1068)
def wb(r, b): return (O[r].matrix_world @ O[r].pose.bones[b].matrix).translation
issues = {"sink": [], "hover": [], "reach": [], "camera": [], "prop": []}
dg = bpy.context.evaluated_depsgraph_get()
for f in range(1, 1621, 10):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    for n in HN:
        a, b = ACTIVE[n]
        if not (a <= f <= b): continue
        zmin = 9.0
        for ch in O[n].children:
            if ch.type != 'MESH' or ch.hide_render: continue
            if any(k in ch.name for k in ("eyebrow", "eyelash", "teeth", "tongue", "high-poly")): continue
            e = ch.evaluated_get(dg); me = e.to_mesh(); mw = e.matrix_world
            if len(me.vertices): zmin = min(zmin, min((mw @ v.co).z for v in me.vertices))
            e.to_mesh_clear()
        if n in ("Bomber",) and f < 878 or n == "Traveller" and f < 1445:
            for s in "LR":
                sh = O["Shoe_" + s if n == "Bomber" else "Shoe_%s_Trav" % s].evaluated_get(dg)
                if n == "Traveller" and s == "L": continue
                m2 = sh.to_mesh(); zmin = min(zmin, min((sh.matrix_world @ v.co).z for v in m2.vertices)); sh.to_mesh_clear()
        seated = n in ("PaxC", "PaxD") or (n == "PaxA" and f < 480) or (n == "PaxB" and f < 480) or (n == "Bomber" and f < 480)
        if zmin < -0.025: issues["sink"].append((f, n, round(zmin, 3)))
        elif zmin > 0.03 and not (n == "Bomber" and f < 480):
            issues["hover"].append((f, n, round(zmin, 3)))
        for s in "LR":
            for ik, bn, tol in (("IK_hand." + s, "wrist." + s, 0.03), ("IK_foot." + s, "foot." + s, 0.03)):
                d = (wb(n, ik) - wb(n, bn)).length
                if d > tol: issues["reach"].append((f, n, ik, round(d, 3)))
    # camera
    cam = O["CAM_Film"]; c = cam.matrix_world.translation
    near = []
    for d in [Vector(v) for v in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]:
        hit, loc, nrm, idx, ob, _ = sc.ray_cast(dg, c + d * 0.001, d)
        if hit and ob.name != "WipeCard": near.append(((loc - c).length, ob.name, nrm.dot(d) > 0.2))
    if near:
        dist, ob, back = min(near)
        if back and dist < 1.0 and ob not in ("CabinShell", "StudioCyc"): issues["camera"].append((f, "inside?", ob, round(dist, 3)))
        elif dist < 0.03: issues["camera"].append((f, "touching", ob, round(dist, 3)))
    # props held
    for ob, rig, bone, f0, f1 in (("Shoe_L", "Attendant", "wrist.L", 880, 1068), ("Shoe_R", "Attendant", "wrist.R", 880, 1068),
                                  ("Syringe", "Steward", "wrist.R", 580, 760), ("Match", "Bomber", "finger2-3.R", 1, 480),
                                  ("Shoe_R_Trav", "Traveller", "wrist.R", 1480, 1518)):
        if f0 <= f <= f1:
            d = (O[ob].matrix_world.translation - wb(rig, bone)).length
            if d > 0.25: issues["prop"].append((f, ob, rig, round(d, 3)))

# ---------------------------------------------------------------- penetration (BVH): hand/foot verts inside other bodies, seats or the floor
from mathutils.bvhtree import BVHTree
def mesh_world(ob, dg):
    e = ob.evaluated_get(dg); me = e.to_mesh(); mw = e.matrix_world
    vs = [mw @ v.co for v in me.vertices]; ps = [tuple(p.vertices) for p in me.polygons]; e.to_mesh_clear(); return vs, ps
def bvh_of(obs, dg):
    V_, P_ = [], []
    for o in obs:
        vs, ps = mesh_world(o, dg); off = len(V_); V_ += vs; P_ += [tuple(i + off for i in p) for p in ps]
    return BVHTree.FromPolygons(V_, P_) if P_ else None
def limb_idx(body, keys):
    gi = {g.index for g in body.vertex_groups if any(g.name.startswith(k) for k in keys)}
    return [v.index for v in body.data.vertices if sum(g.weight for g in v.groups if g.group in gi) > 0.5]
LIMB = {}
pen = []
CAB = ["Bomber", "Attendant", "Steward", "PaxA", "PaxB", "PaxC", "PaxD"]
for f in range(1, 1069, 30):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    trees = {n: bvh_of([c for c in O[n].children if c.type == 'MESH' and c.name.split(".")[-1] in ("body",) or (c.type == 'MESH' and "suit" in c.name)], dg) for n in CAB}
    for n in CAB:
        body = O[n + ".body"]
        if n not in LIMB: LIMB[n] = limb_idx(body, ("finger", "wrist", "metacarpal", "toe", "foot"))
        vs, _ = mesh_world(body, dg)
        pts = [vs[i] for i in LIMB[n] if i < len(vs)]
        hits = {}
        for m, t in trees.items():
            if m == n or t is None: continue
            c = 0
            for pnt in pts[::3]:
                loc, nrm, idx, d = t.find_nearest(pnt, 0.05)
                if loc is not None and (pnt - loc).dot(nrm) < -0.006: c += 1
            if c: hits[m] = c
        fl = sum(1 for pnt in pts if pnt.z < -0.01)
        if fl: hits["floor"] = fl
        for m, c in hits.items(): pen.append((f, n, m, c))
log("\n## penetration (hand+foot verts, every 3rd vert, sampled every 30 f, cabin): %d flagged samples, %d verts total" % (len(pen), sum(p[3] for p in pen)))
for x in pen: log("  f%d %s into %s: %d verts" % x)
log("ShoeBomber audit (every 10 frames, 1-1620)")
for k, v in issues.items():
    log("\n## %s: %d flagged samples (every 10 f)" % (k, len(v)))
    groups = {}
    for x in v: groups.setdefault(tuple(x[1:-1]), []).append((x[0], x[-1]))
    for key, fs in groups.items():
        runs = []; 
        for fr, val in fs:
            if runs and fr - runs[-1][1] <= 10: runs[-1][1] = fr; runs[-1][2] = max(runs[-1][2], abs(val))
            else: runs.append([fr, fr, abs(val)])
        log("  %-40s %s" % (" ".join(map(str, key)), ", ".join("f%d-%d (max %.3f)" % tuple(r) for r in runs)))
open(OUT, "w").write("\n".join(lines) + "\n")
