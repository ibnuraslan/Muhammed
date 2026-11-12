"""Contact pass (director QA, Nov 12): a hand that is within 12 cm of a prop must touch it.
blender -b film_h.blend --python 08_contacts.py -- <out.blend> <report.txt>

Same test as pipeline/qa_check.py HOVER (first prop whose surface is within 12 cm of the wrist; touching = a fingertip
within 1.2 cm). For every visible hand that hovers, the IK hand target is moved along the shortest fingertip-to-surface
vector so that fingertip rests on the surface (5 mm skin gap). Contiguous runs are re-keyed every 2 frames from the
original motion, so the hand still moves the same way, only in contact. A hand already touching some other prop
(e.g. holding the stamp handle next to the certificate) is left alone and reported."""
import sys, os
import bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
a = sys.argv[sys.argv.index("--") + 1:]
OUT, REP = a[0], a[1]
sc = bpy.context.scene; cam = sc.camera
RIGS = [o for o in bpy.data.objects if o.type == 'ARMATURE' and "head" in o.pose.bones and "finger2-1.L" in o.pose.bones]
CHAR = {c.name for r in RIGS for c in r.children_recursive if c.type == 'MESH'}
PROPS = [o for o in bpy.data.objects if o.type == 'MESH' and o.name not in CHAR and len(o.data.polygons) < 200000
         and not any(k in o.name.lower() for k in ("ground", "floor", "terrain", "sky", "backdrop", "water", "ocean", "pile", "heap"))]
def body(r):
    m = [c for c in r.children_recursive if c.type == 'MESH' and (c.name.endswith(".body") or "body" in c.name.lower())]
    return max(m, key=lambda c: len(c.data.vertices)) if m else None
BODY = {r.name: body(r) for r in RIGS}
def hidden(r):
    b = BODY.get(r.name); return r.hide_render or (b is not None and b.hide_render)
def W(r, n, tail=False):
    pb = r.pose.bones[n]; return r.matrix_world @ (pb.tail if tail else pb.head)
def in_view(p, m=0.05):
    c = world_to_camera_view(sc, cam, p); return -m <= c.x <= 1 + m and -m <= c.y <= 1 + m and c.z > 0.05
_bvh = {}
def bvh(o, dg, f):
    k = (o.name, f)
    if k not in _bvh:
        if len(_bvh) > 400: _bvh.clear()
        ev = o.evaluated_get(dg); me = ev.to_mesh(); mw = o.matrix_world
        _bvh[k] = BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons]) if me.polygons else None
        ev.to_mesh_clear()
    return _bvh[k]
def tips(r, s):
    return [W(r, "finger%d-3.%s" % (i, s), True) for i in range(1, 6)] + [W(r, "finger3-1." + s)]

HELD = ("Stamp", "Gavel", "ND_", "Liver", "Mug", "ArgonPen", "Needle")
def hover(r, s, f, dg):
    """(prop, shift vector) if this hand hovers by qa_check's rule, else None"""
    w = W(r, "wrist." + s)
    if not in_view(w): return None
    T = tips(r, s)
    for o in PROPS:
        if (o.matrix_world.translation - w).length > 3.0: continue
        t = bvh(o, dg, f)
        if t is None: continue
        if t.find_nearest(w, 0.12)[0] is None: continue
        best = None
        for p in T:
            loc, n, i, d = t.find_nearest(p, 0.2)
            if loc is not None and (best is None or d < best[0]): best = (d, loc - p)
        if best is None or best[0] <= 0.010: return None
        # really holding a tool / prop next to it? (a fingertip on a held object) -> leave the grip alone
        for o2 in PROPS:
            if o2 is o or not o2.name.startswith(HELD) or (o2.matrix_world.translation - w).length > 1.0: continue
            t2 = bvh(o2, dg, f)
            if t2 and any((t2.find_nearest(p, 0.012)[0] is not None) for p in T[:5]):
                return ("held", o.name, o2.name)
        d, v = best
        if d > 0.12:
            return ("far", o.name, "%.1f cm" % (d * 100))
        return (o.name, v * ((d - 0.005) / d))
    return None

# --- tool holds: thumb and index tips close on the tool (tripod grip), every 2 frames
TOOL_HOLDS = [("Surgeon1", "R", 1, 300, "ArgonPen_OR"), ("Surgeon1", "R", 318, 458, "ND_"), ("GloveHands", "R", 1, 300, "ArgonPen_Studio")]
def ik_keys_remove(r, s, a0, b0):
    ad = r.animation_data
    for fc in [fc for L in ad.action.layers for st in L.strips for cb in st.channelbags for fc in cb.fcurves
               if fc.data_path in ('pose.bones["IK_hand.%s"].location' % s, 'pose.bones["IK_hand.%s"].rotation_quaternion' % s)]:
        kps = fc.keyframe_points
        for i in reversed(range(len(kps))):
            if a0 < kps[i].co.x < b0:
                kps.remove(kps[i], fast=True)
        fc.update()
report = []; n_tool = 0
for name, s, f0, f1, pre in TOOL_HOLDS:
    r = bpy.data.objects[name]; pb = r.pose.bones["IK_hand." + s]
    objs = [o for o in PROPS if o.name.startswith(pre)]
    plan = {}
    for f in range(f0, f1 + 1, 2):
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
        mid = (W(r, "finger1-3." + s, True) + W(r, "finger2-3." + s, True)) / 2
        best = None
        for o in objs:
            t = bvh(o, dg, f)
            if t is None: continue
            loc, n, i, d = t.find_nearest(mid, 0.3)
            if loc is not None and (best is None or d < best[0]): best = (d, loc - mid)
        v = best[1] * ((best[0] - 0.004) / best[0]) if best and best[0] > 0.006 else Vector()
        plan[f] = (r.matrix_world @ pb.matrix).copy(), v
    ik_keys_remove(r, s, f0 - 1, f1 + 1)
    for f, (M, v) in sorted(plan.items()):
        sc.frame_set(f); pb.matrix = r.matrix_world.inverted() @ (Matrix.Translation(v) @ M)
        pb.keyframe_insert("location", frame=f, group=pb.name); pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name); n_tool += 1
    report.append("  tool hold %s.%s %d-%d on %s* (max shift %.1f cm)" % (name, s, f0, f1, pre, 100 * max(v.length for M, v in plan.values())))
print("TOOL_KEYS", n_tool)
todo = {}
for f in range(1, sc.frame_end + 1, 2):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    for r in RIGS:
        if hidden(r): continue
        for s in "LR":
            h = hover(r, s, f, dg)
            if h is None: continue
            if h[0] in ("held", "far"):
                report.append("  %5d %s.%s near %s, %s %s - left" % (f, r.name, s, h[1], "holding" if h[0] == "held" else "gap", h[2])); continue
            if any(n_ == r.name and s_ == s and f0 <= f <= f1 for n_, s_, f0, f1, _ in TOOL_HOLDS): continue
            todo.setdefault((r.name, s), {})[f] = h
print("HOVER_FRAMES", sum(len(v) for v in todo.values()))

def runs(fs):
    fs = sorted(fs); out = [[fs[0], fs[0]]]
    for x in fs[1:]:
        if x - out[-1][1] <= 6: out[-1][1] = x
        else: out.append([x, x])
    return out
n_keys = 0
for (name, s), fr in todo.items():
    r = bpy.data.objects[name]; pb = r.pose.bones["IK_hand." + s]
    for a0, b0 in runs(fr):
        span = list(range(max(1, a0 - 4), min(sc.frame_end, b0 + 4) + 1, 2))
        # world IK matrices from the original motion, shifted by the (interpolated) contact vector
        known = sorted(fr.items())
        def shift_at(f):
            pts = [(k, v[1]) for k, v in known if a0 <= k <= b0]
            if f <= pts[0][0]: return pts[0][1] * max(0.0, 1 - (pts[0][0] - f) / 4.0)
            if f >= pts[-1][0]: return pts[-1][1] * max(0.0, 1 - (f - pts[-1][0]) / 4.0)
            for (k0, v0), (k1, v1) in zip(pts, pts[1:]):
                if k0 <= f <= k1:
                    u = (f - k0) / max(1, k1 - k0); return v0.lerp(v1, u)
            return Vector()
        mats = {}
        for f in span:
            sc.frame_set(f); mats[f] = (r.matrix_world @ pb.matrix).copy()
        ad = r.animation_data
        for fc in [fc for L in ad.action.layers for st in L.strips for cb in st.channelbags for fc in cb.fcurves
                   if fc.data_path in ('pose.bones["IK_hand.%s"].location' % s, 'pose.bones["IK_hand.%s"].rotation_quaternion' % s)]:
            kps = fc.keyframe_points
            for i in reversed(range(len(kps))):
                if span[0] < kps[i].co.x < span[-1]:
                    kps.remove(kps[i], fast=True)
            fc.update()
        for f in span:
            M = Matrix.Translation(shift_at(f)) @ mats[f]
            sc.frame_set(f)
            pb.matrix = r.matrix_world.inverted() @ M
            pb.keyframe_insert("location", frame=f, group=pb.name); pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
            n_keys += 1
        report.append("  %s.%s %d-%d onto %s (max %.1f cm)" % (name, s, a0, b0, fr[a0][0], 100 * max(v[1].length for k, v in fr.items() if a0 <= k <= b0)))
with open(REP, "w") as fh:
    fh.write("Contact pass (qa_check HOVER rule): %d hovering hand-frames moved onto the surface, %d IK keys\n" % (sum(len(v) for v in todo.values()), n_keys))
    fh.write("\n".join(report) + "\n")
print("CONTACTS", n_keys)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("CONTACTS_DONE", OUT)
