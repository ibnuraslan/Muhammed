"""Elbow fit: for every frame in the arm runs that limb_check flags (>= 3 points of the arm bone axis inside the own torso),
try a grid of elbow-pole positions and key the one that keeps the arm axis out of the torso (hand IK targets are unchanged,
so every contact stays where it is).
blender -b anim.blend --python 05_elbow_fit.py -- out.blend runs.json
runs.json: {"Nurse.L": [[f0, f1], ...], ...}"""
import bpy, sys, json
from mathutils import Vector as V
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]; OUT, RUNS = a[0], json.load(open(a[1]))
sc = bpy.context.scene; D = bpy.data.objects
TORSO_G = ("spine", "pelvis", "clavicle", "breast", "neck", "root", "shoulder")
ARM = ["upperarm01", "upperarm02", "lowerarm01", "lowerarm02"]

def body_of(r):
    m = [c for c in r.children_recursive if c.type == 'MESH' and "body" in c.name.lower()]
    return max(m, key=lambda c: len(c.data.vertices))
def torso_ids(r, b):
    gi = {g.index: g.name.lower() for g in b.vertex_groups}; bones = {bn.name.lower() for bn in r.data.bones}; out = set()
    for v in b.data.vertices:
        gs = [g for g in v.groups if g.weight > 0.05]
        if any(gi.get(g.group, "").startswith(("helper", "joint")) and g.weight > 0.5 for g in gs): continue
        gs = [g for g in gs if gi.get(g.group, "") in bones]
        if not gs: continue
        dom = gi.get(max(gs, key=lambda g: g.weight).group, "")
        if any(dom.startswith(k) for k in TORSO_G): out.add(v.index)
    return out
def inside(t, p, depth=0.03, rad=0.12):
    loc, nrm, _, d = t.find_nearest(p, rad)
    return loc is not None and d > depth and (p - loc).dot(nrm) < 0
def axis_pts(r, s):
    pts = []
    for bn in ARM:
        pb = r.pose.bones[bn + "." + s]; h, t = r.matrix_world @ pb.head, r.matrix_world @ pb.tail
        pts += [h.lerp(t, k / 4) for k in range(5)]
    pts.append(r.matrix_world @ r.pose.bones["wrist." + s].tail)
    return pts
def set_pole(r, s, pole_arm, f):
    n = "Pole_elbow." + s; bn = r.data.bones[n]; pb = r.pose.bones[n]
    pb.location = bn.matrix_local.to_3x3().inverted() @ (pole_arm - bn.head_local)
    pb.keyframe_insert("location", frame=f, group=n)
def clear_pole_keys(r, s, f0, f1):
    n = "Pole_elbow." + s; ad = r.animation_data
    if not ad or not ad.action: return
    fcs = [fc for fc in getattr(ad.action, "fcurves", []) if fc.data_path == 'pose.bones["%s"].location' % n]
    if not fcs:   # slotted actions (Blender 5): walk layers/strips/channelbags
        for L in ad.action.layers:
            for st in L.strips:
                for cb in st.channelbags: fcs += [fc for fc in cb.fcurves if fc.data_path == 'pose.bones["%s"].location' % n]
    for fc in fcs:
        for kp in [k for k in fc.keyframe_points if f0 <= k.co.x <= f1][::-1]: fc.keyframe_points.remove(kp)

for for_who, runs in RUNS.items():
    nm, s = for_who.split(".")
    r = D[nm]; b = body_of(r)
    for m in b.modifiers:
        if m.type in ("MASK", "SUBSURF", "MULTIRES"): m.show_viewport = False
    tids = torso_ids(r, b)
    for f0, f1 in runs:
        f0 = max(1, f0 - 6); f1 = min(sc.frame_end, f1 + 6)
        frames = list(range(f0, f1 + 1, 2)) + [f1]
        # pass 1: current poles (evaluated) and torso BVH per frame, then choose
        choice = {}
        for f in frames:
            sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
            e = b.evaluated_get(dg); me = e.to_mesh(); vs = [e.matrix_world @ v.co for v in me.vertices]
            ps = [tuple(p.vertices) for p in me.polygons if all(i in tids for i in p.vertices)]; e.to_mesh_clear()
            T = BVHTree.FromPolygons(vs, ps)
            pb = r.pose.bones; sh = pb["upperarm01." + s].head.copy(); wr = pb["wrist." + s].head.copy()
            other = pb["upperarm01." + ("R" if s == "L" else "L")].head
            side = (sh - other); side.z = 0; side.normalize()
            up = (pb["neck01"].head - pb["spine05"].head).normalized(); fwd = up.cross(side if s == "R" else -side).normalized()
            if (pb["head"].tail - pb["head"].head).dot(fwd) < -10: fwd = -fwd
            cur = r.pose.bones["Pole_elbow." + s]
            cur_arm = r.data.bones["Pole_elbow." + s].head_local + r.data.bones["Pole_elbow." + s].matrix_local.to_3x3() @ cur.location
            n_cur = sum(1 for p in axis_pts(r, s) if inside(T, p))
            best = (n_cur, 0.0, cur_arm)
            if n_cur >= 3:
                b.hide_viewport = True     # skip mesh evaluation while trying poles (torso BVH is already built)
                mid = (sh + wr) / 2
                for o_ in (0.3, 0.55, 0.85):
                    for d_ in (0.0, 0.25, 0.5):
                        for f_ in (-0.3, 0.0, 0.3):
                            pole = mid + side * o_ + V((0, 0, -d_)) + fwd * f_
                            set_pole(r, s, pole, f); bpy.context.view_layer.update()
                            k = sum(1 for p in axis_pts(r, s) if inside(T, p))
                            cost = (k, (pole - cur_arm).length)
                            if cost < best[:2]: best = (k, cost[1], pole)
                set_pole(r, s, cur_arm, f); bpy.context.view_layer.update()
                b.hide_viewport = False
            choice[f] = best
        clear_pole_keys(r, s, f0, f1)
        for f, (k, _, pole) in choice.items(): set_pole(r, s, pole, f)
        print("ELBOWFIT", for_who, f0, f1, "flagged-after (frames with >=3 pts):", sum(1 for v in choice.values() if v[0] >= 3), "of", len(choice))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ELBOWFIT_SAVED", OUT)
