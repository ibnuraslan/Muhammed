"""NukedWell contact / penetration audit.
blender -b anim.blend --python audit.py -- <report.txt> [step]
Checks (every <step> frames, only while the character is on screen-relevant frames):
  FOOT_HOVER / FOOT_SINK   shoe soles vs the walkable surface (ground 0, shaft collar 0.5) while planted
  HAND_FAR                 a hand that should grip (hose, device) further than 6 cm from that surface
  HAND_IN_PROP             hand/finger vertices inside the device or hose (BVH)
  BODY_CROSS               crew body vertices inside another crew member (BVH)
  CAMERA_INSIDE            camera inside a solid (truck, crane, derrick, device), or behind the strata face below ground
"""
import sys, math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]; STEP = int(argv[1]) if len(argv) > 1 else 10
sc = bpy.context.scene; O = bpy.data.objects
SHAFT = Vector((-14.0, -2.7))
CREW = ["SolA", "SolB", "SolC", "SolD", "EngA", "EngB"]
GRIP = {  # name: (frame range, object, kind)
    "SolA": [((1380, 1449), "Device", "device"), ((860, 1300), "HoseA", "hose")],
    "SolB": [((1380, 1449), "Device", "device"), ((860, 1300), "HoseA", "hose")],
    "SolC": [((860, 1300), "HoseB", "hose")], "SolD": [((860, 1300), "HoseB", "hose")],
}
issues = {}
def flag(kind, f, msg): issues.setdefault(kind, []).append((f, msg))
def ground_z(x, y):
    r = (Vector((x, y)) - SHAFT).length
    return 0.5 if 2.35 < r < 3.45 else 0.0
def jolt(): j = O.get("JoltRoot"); return j.matrix_world.translation.z if j else 0.0
def mesh_pts(o, dg, every=1, vg=None):
    ev = o.evaluated_get(dg); me = ev.to_mesh(); mw = o.matrix_world
    if vg is not None:
        gi = {g.index for g in o.vertex_groups if any(k in g.name for k in vg)}
        pts = [mw @ v.co for v in me.vertices if any(g.group in gi and g.weight > 0.5 for g in v.groups)]
    else:
        pts = [mw @ v.co for v in list(me.vertices)[::every]]
    ev.to_mesh_clear(); return pts
def child(nm, key): return next((c for c in O[nm].children if c.name.split(".")[-1] == key), None)
penetration_total = 0
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); jz = jolt()
    cam = sc.camera.matrix_world.translation
    for nm in CREW:
        rig = O[nm]
        root = rig.matrix_world @ rig.pose.bones["root"].head
        if (root - cam).length > 120: continue     # too far to read in frame
        shoes = child(nm, "shoes03")
        if shoes:
            pts = mesh_pts(shoes, dg, 4)
            for s, sel in (("L", lambda p: (rig.matrix_world.inverted() @ p).x > 0), ("R", lambda p: (rig.matrix_world.inverted() @ p).x <= 0)):
                sp = [p for p in pts if sel(p)]
                if not sp: continue
                low = min(sp, key=lambda p: p.z); gz = ground_z(low.x, low.y) + jz
                sc.frame_set(min(f + 1, sc.frame_end)); f2 = rig.matrix_world @ rig.pose.bones["foot." + s].head; sc.frame_set(f)
                f1_ = rig.matrix_world @ rig.pose.bones["foot." + s].head
                planted = (f2 - f1_).length < 0.004
                if gz - low.z > 0.025: flag("FOOT_SINK", f, "%s %s sole %.1f cm into the ground" % (nm, s, (gz - low.z) * 100)); penetration_total += 1
                elif planted and low.z - gz > 0.03: flag("FOOT_HOVER", f, "%s %s sole %.1f cm above the ground (planted)" % (nm, s, (low.z - gz) * 100))
        for (a, b), pn, kind in GRIP.get(nm, []):
            if not (a <= f <= b): continue
            po = O.get(pn)
            if po is None or po.hide_render: continue
            if po.type == 'CURVE':
                pd = po.evaluated_get(dg).to_mesh(); tree = BVHTree.FromPolygons([po.matrix_world @ v.co for v in pd.vertices], [p.vertices[:] for p in pd.polygons]); po.evaluated_get(dg).to_mesh_clear()
            else:
                tree = BVHTree.FromObject(po, dg)
                tree = BVHTree.FromPolygons([po.matrix_world @ Vector(v) for v in [vv.co for vv in po.data.vertices]], [p.vertices[:] for p in po.data.polygons])
            body = child(nm, "body")
            for s in "LR":
                hp = mesh_pts(body, dg, vg=["finger", "metacarpal"] if False else ["wrist." + s, "finger1", "finger2", "finger3"]) if False else None
                dist = min(tree.find_nearest(rig.matrix_world @ rig.pose.bones[bn + "." + s].head)[3] or 9
                           for bn in ("finger3-1", "finger2-2", "finger3-2", "finger4-2", "metacarpal2", "metacarpal3"))
                if dist > 0.06 + 0.03: flag("HAND_FAR", f, "%s %s palm %.1f cm from the %s" % (nm, s, dist * 100, kind))
            # finger vertices inside the prop
            body = child(nm, "body")
            fp = mesh_pts(body, dg, 3)
            inside = 0
            for p in fp:
                loc, nrm, idx, dist = tree.find_nearest(p)
                if loc is not None and dist < 0.08 and (p - loc).dot(nrm) < -0.008: inside += 1
            if inside > 3: flag("HAND_IN_PROP", f, "%s: %d body samples inside the %s" % (nm, inside, kind)); penetration_total += inside
    # crew vs crew
    trees = {}
    for nm in CREW:
        b = child(nm, "body"); rig = O[nm]
        if (rig.matrix_world @ rig.pose.bones["root"].head - cam).length > 120: continue
        trees[nm] = BVHTree.FromObject(b, dg)
    ks = list(trees)
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            ov = trees[ks[i]].overlap(trees[ks[j]])
            if ov: flag("BODY_CROSS", f, "%s and %s overlap (%d tri pairs)" % (ks[i], ks[j], len(ov))); penetration_total += len(ov)
    # camera
    if cam.z < -0.05 and cam.y > -0.3:
        flag("CAMERA_INSIDE", f, "camera behind the strata face underground (y %.1f)" % cam.y)
    for o in O:
        if o.type != 'MESH' or o.hide_render: continue
        if not o.name.startswith(("Crane_Cab", "Crane_Counterweight", "Device", "Cap_", "WH_", "ShaftCollar", "Derrick_floor", "Sandbag", "Tent")) and not (o.parent and o.parent.name in ("FireTruck1", "FireTruck2", "MixerTruck", "CargoTruck")):
            continue
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        mn = Vector([min(p[i] for p in bb) for i in range(3)]); mx = Vector([max(p[i] for p in bb) for i in range(3)])
        if all(mn[i] + 0.02 <= cam[i] <= mx[i] - 0.02 for i in range(3)):
            flag("CAMERA_INSIDE", f, "camera inside the bounds of %s" % o.name)

def ranges(items):
    fr = sorted(set(f for f, _ in items)); out = []; start = prev = None
    for f in fr:
        if start is None: start = prev = f
        elif f - prev <= STEP: prev = f
        else: out.append((start, prev)); start = prev = f
    if start is not None: out.append((start, prev))
    return out
lines = ["AUDIT NukedWell (step %d frames, 60 fps)" % STEP, "PENETRATION_COUNT %d" % penetration_total]
for kind in sorted(issues):
    its = issues[kind]
    lines.append("%-14s %4d samples | ranges (s): %s" % (kind, len(its), ", ".join("%.1f-%.1f" % ((a - 1) / 60, (b - 1) / 60) for a, b in ranges(its))))
    for f, m in its[:4]: lines.append("      e.g. f%d (%.2fs): %s" % (f, (f - 1) / 60, m))
if not issues: lines.append("no issues found")
open(OUT, "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
