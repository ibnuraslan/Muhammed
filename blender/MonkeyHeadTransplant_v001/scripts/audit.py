"""Contact audit for MonkeyHeadTransplant. blender -b anim.blend --python scripts/audit.py -- <report.txt>"""
import bpy, sys, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; D = bpy.data.objects
lines = []
def log(*a):
    s = " ".join(str(x) for x in a); print("AUDIT", s); lines.append(s)
def world_verts(o, step=1):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); m = e.to_mesh()
    vs = [e.matrix_world @ v.co for v in list(m.vertices)[::step]]; e.to_mesh_clear(); return vs
TZ = 0.92
# 1. monkeys on the tables / in the chair: lowest point vs support
for f in (1, 200, 400, 900):
    sc.frame_set(f)
    for nm, sup in (("MK_BodyA", TZ), ("MK_BodyB", TZ)):
        z = min(v.z for v in world_verts(D[nm], 5)); log(f"f{f} {nm} lowest {z:.4f} table {sup} gap {z - sup:+.4f}")
for f in (1210, 1400, 1700):
    sc.frame_set(f)
    vs = world_verts(D["MK_BodyB"], 3)
    dg = bpy.context.evaluated_depsgraph_get()
    worst = 0.0; worst_in = 0.0
    for v in vs:
        if v.z < 0.6:
            h = sc.ray_cast(dg, v + Vector((0, 0, 0.3)), Vector((0, 0, -1)))
            if h[0] and h[4].name == "Chair" and h[1].z < 0.5 and v.z < h[1].z + 0.02:
                d = v.z - h[1].z
                if d < worst_in: worst_in = d
    z = min(v.z for v in vs)
    log(f"f{f} chair monkey lowest {z:.4f}, deepest sink below chair surface {worst_in:+.4f}")
# 2. head on body B after placement: distance between head neck cap and body neck cap centres
for f in (380, 700, 1000, 1210):
    sc.frame_set(f)
    hb = D["MK_Head"].matrix_world @ D["NeckRef"].location; bb = D["MK_BodyB"].matrix_world @ D["NeckRef"].location
    log(f"f{f} head-to-neck offset {(hb - bb).length * 1000:.1f} mm")
# 3. surgeon / nurse feet: ankle height and slide while planted
for nm in ("Surgeon", "Nurse"):
    rig = D[nm]; prev = {}
    worst_slide = {"L": 0, "R": 0}; zr = {"L": [9, -9], "R": [9, -9]}
    for f in range(1, 1771, 4):
        if f > 1030 and f < 1190: continue
        sc.frame_set(f)
        for s in "LR":
            p = rig.matrix_world @ rig.pose.bones["foot." + s].head
            zr[s][0] = min(zr[s][0], p.z); zr[s][1] = max(zr[s][1], p.z)
            if s in prev and p.z < 0.12 and prev[s][1] < 0.12:
                d = (p.to_2d() - prev[s][0].to_2d()).length
                if d > worst_slide[s] and d < 0.3: worst_slide[s] = d
            prev[s] = (p, p.z)
    log(f"{nm} ankle z range L {zr['L'][0]:.3f}..{zr['L'][1]:.3f}  R {zr['R'][0]:.3f}..{zr['R'][1]:.3f}; max planted slide per 4f L {worst_slide['L']*100:.1f} cm R {worst_slide['R']*100:.1f} cm")
# 4. hands on the head during the transfer
for f in (262, 300, 340, 370):
    sc.frame_set(f)
    hv = world_verts(D["MK_Head"], 4)
    rig = D["Surgeon"]
    for s in "LR":
        w = rig.matrix_world @ rig.pose.bones["wrist." + s].head
        tip = rig.matrix_world @ rig.pose.bones["finger3-3." + s].tail if "finger3-3." + s in rig.pose.bones else w
        d = min((v - tip).length for v in hv)
        log(f"f{f} surgeon {s} fingertip to head surface {d * 100:.1f} cm")
# 5. bowl lands on the floor
for f in (945, 960, 1000):
    sc.frame_set(f); z = min(v.z for v in world_verts(D["Bowl"])); log(f"f{f} bowl lowest z {z:+.4f}")
# 6. camera inside geometry / too close
cam = sc.camera; bad = 0
for f in range(1, 1771, 5):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    p = cam.matrix_world.translation; fwd = -(cam.matrix_world.to_3x3().col[2])
    h = sc.ray_cast(dg, p, fwd)
    inside = 0
    for dv in (Vector((0, 0, 1)), Vector((0, 0, -1)), Vector((1, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, -1, 0))):
        hh = sc.ray_cast(dg, p, dv)
        if hh[0] and hh[4].name != "XR_Void" and hh[2].dot(dv) > 0 and (hh[1] - p).length < 0.4: inside += 1
    if (h[0] and h[4].name != "XR_Void" and (h[1] - p).length < 0.03) or inside >= 4:
        bad += 1; log(f"f{f} CAMERA problem: front {h[4].name if h[0] else None} {(h[1]-p).length if h[0] else 0:.3f} inside-votes {inside}")
log(f"camera frames flagged: {bad} of {len(range(1, 1771, 5))}")
# 7. one camera, no markers
log("cameras", [o.name for o in D if o.type == "CAMERA"], "markers", len(sc.timeline_markers))
open(OUT, "w").write("\n".join(lines) + "\n")
# 8. penetration count: people (hands, gowns, bodies) vs monkey meshes, tables, chair, each other
def bvh_of(o):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); m = e.to_mesh()
    vs = [e.matrix_world @ v.co for v in m.vertices]; ps = [tuple(p.vertices) for p in m.polygons]; e.to_mesh_clear()
    return BVHTree.FromPolygons(vs, ps), vs
def inside_count(pts, bvh, tol=0.004):
    n = 0
    for p in pts:
        loc, nrm, idx, d = bvh.find_nearest(p, 0.05)
        if loc is not None and (p - loc).dot(nrm) < -tol: n += 1
    return n
TARGETS = ["MK_Head", "MK_BodyA", "MK_BodyB", "T1_Pad", "T2_Pad", "Chair"]
PEOPLE = {nm: [o for o in D if o.name.startswith(nm) and o.type == "MESH" and (o.name.endswith((".body", "_Gown", "_Cap", "_Mask")))] for nm in ("Surgeon", "Nurse", "Anaes")}
total = 0
for f in (100, 230, 262, 300, 340, 372, 450, 560, 900, 1250, 1300, 1500, 1700):
    sc.frame_set(f)
    tb = {t: bvh_of(D[t]) for t in TARGETS if not D[t].hide_render}
    pb = {nm: [(o.name, bvh_of(o)) for o in objs if not o.hide_render] for nm, objs in PEOPLE.items()}
    row = []
    for nm, lst in pb.items():
        for on, (bv, vs) in lst:
            pts = vs[::3]
            for t, (tbv, tvs) in tb.items():
                c = inside_count(pts, tbv)
                if c: row.append(f"{on}->{t}:{c}"); total += c
            # monkey verts inside the person (fingers through fur is the other direction)
    for t in ("MK_Head",):
        if t in tb:
            for nm, lst in pb.items():
                for on, (bv, vs) in lst:
                    if on.endswith(".body"):
                        c = inside_count(tb[t][1][::2], bv)
                        if c: row.append(f"{t}->{on}:{c}"); total += c
    # people vs each other
    names = list(pb)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            for on, (bv, vs) in pb[names[i]]:
                for on2, (bv2, vs2) in pb[names[j]]:
                    c = inside_count(vs[::4], bv2)
                    if c: row.append(f"{on}->{on2}:{c}"); total += c
    log(f"f{f} penetrations: {', '.join(row) if row else 'none'}")
log(f"PENETRATION TOTAL (sampled verts inside other meshes, 13 frames): {total}")
open(OUT, "w").write("\n".join(lines) + "\n")
