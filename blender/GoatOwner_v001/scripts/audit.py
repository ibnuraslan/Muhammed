"""GoatOwner contact / penetration audit.  blender -b anim.blend --python audit.py -- <report.txt> [step]
Checks every <step> frames:
  HOOF_SINK / HOOF_FLOAT    planted goat hooves vs the walk surface (ground, steps, porch, ramp, truck bed)
  FOOT_SINK / FOOT_FLOAT    planted human feet (ankle height) vs the surface
  BODY_OVERLAP              BVH overlap: owner vs goat, owner vs porch/steps, rescuer/officials vs goat (polygon pairs)
  LIE_HOVER / LIE_SINK      owner lying: lowest body point vs the ground
  STICK_GRIP                stick more than 6 cm from the right palm while held
  CAMERA_INSIDE             camera under the surface, inside a building/truck bounds or within 3 cm of a character mesh"""
import sys, math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]; STEP = int(argv[1]) if len(argv) > 1 else 10
sc = bpy.context.scene
PX0, PX1, PY0, PY1, PZ = list(sc["porch"]); STEPS = [list(s) for s in sc["steps"]]
ramp = bpy.data.objects["Ramp"]
RL = ramp.matrix_world @ Vector((0, -1.1, 0)); RH = ramp.matrix_world @ Vector((0, 1.1, 0))
BED = 1.03
def ground_z(x, y):
    if PX0 <= x <= PX1 and PY0 <= y <= PY1: return PZ
    for xa, xb, zt in STEPS:
        if xa <= x <= xb and 5.25 <= y <= 6.75: return zt
    if -2.0 <= x <= -1.0 and RL.y <= y <= RH.y: return BED * (y - RL.y) / (RH.y - RL.y)
    if -2.4 <= x <= -0.6 and RH.y < y < RH.y + 3.5: return BED
    return 0.0
issues = {}; counts = {}
def flag(kind, f, msg): issues.setdefault(kind, []).append((f, msg))
G = bpy.data.objects["Goat_rig"]
HUM = {n: bpy.data.objects[n] for n in ("Owner", "Passer", "OffA", "OffB", "Rescuer")}
def mesh_of(rig, suffix): return [c for c in rig.children if c.type == 'MESH' and c.name.endswith(suffix)]
def tree(objs, dg):
    vs, ps = [], []
    for o in objs:
        e = o.evaluated_get(dg); me = e.to_mesh(); mw = o.matrix_world; off = len(vs)
        vs += [mw @ v.co for v in me.vertices]; ps += [[off + i for i in p.vertices] for p in me.polygons]; e.to_mesh_clear()
    return BVHTree.FromPolygons(vs, ps) if ps else None, vs
porch = [o for o in bpy.data.objects if o.name.startswith(("Deck_", "Step_", "Riser_", "Rail", "PorchPost", "Spindle", "PorchSkirt"))]
BLD = [bpy.data.objects[n] for n in ("house", "Shed", "truck", "tires_shed")]
prev = {}
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    # hooves
    for k in ("FL", "FR", "HL", "HR"):
        tip = G.matrix_world @ G.pose.bones["hoof." + k].tail
        key = ("h", k); moving = key in prev and (prev[key] - tip).length > 0.004 * STEP; prev[key] = tip.copy()
        gz = ground_z(tip.x, tip.y)
        if gz - tip.z > 0.025: flag("HOOF_SINK", f, "%s %.1f cm into the surface" % (k, (gz - tip.z) * 100))
        elif tip.z - gz > 0.03 and not moving: flag("HOOF_FLOAT", f, "%s %.1f cm above the surface while planted" % (k, (tip.z - gz) * 100))
    # human feet
    for n, r in HUM.items():
        if r.hide_render: continue
        for s in "LR":
            pb = r.pose.bones["foot." + s]; a = r.matrix_world @ pb.head; rest = r.data.bones["foot." + s].head_local.z
            key = (n, s); moving = key in prev and (prev[key] - a).length > 0.004 * STEP; prev[key] = a.copy()
            if n == "Owner" and 1450 <= f <= 1910: continue
            gz = ground_z(a.x, a.y); h = a.z - gz
            if h < rest - 0.035: flag("FOOT_SINK", f, "%s %s ankle %.1f cm low" % (n, s, (rest - h) * 100))
            elif h > rest + 0.04 and not moving: flag("FOOT_FLOAT", f, "%s %s %.1f cm above the surface while planted" % (n, s, (h - rest) * 100))
    # overlaps
    gt, _ = tree(mesh_of(G, "body"), dg)
    ow = HUM["Owner"]
    if not ow.hide_render:
        ot, ov = tree(mesh_of(ow, ".body"), dg)
        n_ = len(ot.overlap(gt)) if ot and gt else 0
        counts["owner-goat"] = counts.get("owner-goat", 0) + n_
        if n_ > 40: flag("BODY_OVERLAP", f, "owner/goat %d polygon pairs" % n_)
        if 1183 <= f <= 1460:
            pt, _ = tree(porch, dg); n2 = len(ot.overlap(pt)); counts["owner-porch"] = counts.get("owner-porch", 0) + n2
            if n2 > 10: flag("BODY_OVERLAP", f, "owner/porch %d polygon pairs" % n2)
        if 1490 <= f <= 1905:
            low = min(v.z for v in ov[::3])
            if low > 0.02: flag("LIE_HOVER", f, "lowest body point %.1f cm above the ground" % (low * 100))
            if sum(1 for v in ov[::5] if v.z < -0.01) > 0.3 * len(ov[::5]): flag("LIE_SINK", f, "over 30% of the body below the ground")
        if f < 958:
            st = bpy.data.objects["Stick"].matrix_world
            ax = st.to_3x3() @ Vector((1, 0, 0)); c = st.translation
            w = ow.matrix_world @ ow.pose.bones["finger3-1.R"].head
            d = (w - c) - ax * (w - c).dot(ax)
            if d.length > 0.06: flag("STICK_GRIP", f, "palm %.1f cm from the stick axis" % (d.length * 100))
    for n in ("Rescuer", "OffA", "OffB"):
        r = HUM[n]
        if r.hide_render: continue
        rt, _ = tree(mesh_of(r, ".body"), dg); n_ = len(rt.overlap(gt)) if rt and gt else 0
        counts[n + "-goat"] = counts.get(n + "-goat", 0) + n_
        if n_ > 25: flag("BODY_OVERLAP", f, "%s/goat %d polygon pairs" % (n, n_))
    # camera
    cp = sc.camera.matrix_world.translation
    if cp.z < ground_z(cp.x, cp.y) + 0.05: flag("CAMERA_INSIDE", f, "camera at/below the surface")
    for o in BLD:
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        mn = Vector([min(p[i] for p in bb) for i in range(3)]); mx = Vector([max(p[i] for p in bb) for i in range(3)])
        if all(mn[i] <= cp[i] <= mx[i] for i in range(3)): flag("CAMERA_INSIDE", f, "inside the bounds of " + o.name)
    for r in [G] + [h for h in HUM.values() if not h.hide_render]:
        t_, _ = tree(mesh_of(r, "body"), dg)
        if t_:
            loc, nrm, idx, dist = t_.find_nearest(cp)
            if dist is not None and dist < 0.03: flag("CAMERA_INSIDE", f, "within 3 cm of " + r.name)
def ranges(items):
    fr = sorted(set(f for f, _ in items)); out = []; s0 = p0 = None
    for f in fr:
        if s0 is None: s0 = p0 = f
        elif f - p0 <= STEP: p0 = f
        else: out.append((s0, p0)); s0 = p0 = f
    if s0 is not None: out.append((s0, p0))
    return out
L = ["AUDIT GoatOwner (step %d frames, 60 fps)" % STEP, "Penetration polygon pairs summed over samples: " + ", ".join("%s %d" % kv for kv in sorted(counts.items()))]
for kind in sorted(issues):
    its = issues[kind]
    L.append("%-14s %4d samples | ranges (s): %s" % (kind, len(its), ", ".join("%.1f-%.1f" % ((a - 1) / 60, (b - 1) / 60) for a, b in ranges(its))))
    for f, m in its[:3]: L.append("      e.g. f%d (%.2fs): %s" % (f, (f - 1) / 60, m))
if not issues: L.append("no issues found")
open(OUT, "w").write("\n".join(L) + "\n"); print("\n".join(L))
