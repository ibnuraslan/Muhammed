"""v008d (director, Nov 13): held props measured to the FINGERTIPS (bbox to the nearest finger k-3 tail <= 1 cm while held).
blender -b in.blend --python tip_fix.py -- out.blend
 carry : the prop's bbox centre is keyed every frame onto the pinch (midpoint of thumb tip finger1-3 and index tip finger2-3)
 insert: the prop's path into the nostril stays; the IK hand is keyed every frame so the pinch sits on the prop (the fingers push it in)
 palm  : the prop is moved just enough that its bbox is within 0.8 cm of the nearest fingertip"""
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene
JOBS = [("insert", "Brick_Big", "Boy", "R", 132, 150), ("insert", "Brick_Small", "Boy", "R", 714, 736),
        ("carry", "Brick_Big", "Boy", "R", 1, 131), ("carry", "Brick_Small", "Boy", "R", 336, 713),
        ("palm", "Brick_Small", "Man", "L", 2152, 2310), ("palm", "Prop_Phone", "Man", "R", 1440, 1469), ("palm", "Prop_Inhaler", "Man", "R", 1606, 1720)]
def tips(a, s): return [a.matrix_world @ a.pose.bones["finger%d-3.%s" % (k, s)].tail for k in (1, 2, 3, 4, 5)]
def pinch(a, s): t = tips(a, s); return (t[0] + t[1]) / 2
def bbox(o):
    dg = bpy.context.evaluated_depsgraph_get(); pts = []
    for x in [o] + list(o.children_recursive):
        if x.type == "MESH": e = x.evaluated_get(dg); pts += [e.matrix_world @ Vector(c) for c in e.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])
def bd(lo, hi, p): return Vector((max(lo.x - p.x, 0, p.x - hi.x), max(lo.y - p.y, 0, p.y - hi.y), max(lo.z - p.z, 0, p.z - hi.z))).length
def fcs(o): return [fc for l in o.animation_data.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
def shift_obj(o, f, d):
    for fc in [c for c in fcs(o) if c.data_path == "location"]: fc.keyframe_points.insert(f, fc.evaluate(f) + d[fc.array_index], options={"FAST"})
def shift_ik(a, s, f, d):
    n = "IK_hand." + s; dl = a.data.bones[n].matrix_local.to_3x3().inverted() @ (a.matrix_world.to_3x3().inverted() @ d)
    for fc in [c for c in fcs(a) if c.data_path == 'pose.bones["%s"].location' % n]: fc.keyframe_points.insert(f, fc.evaluate(f) + dl[fc.array_index], options={"FAST"})
for kind, pn, cn, s, f0, f1 in JOBS:
    o = bpy.data.objects[pn]; a = bpy.data.objects[cn]
    for it in range(10 if kind == "insert" else 4):
        D = {}
        for f in range(f0, f1 + 1):
            sc.frame_set(f)
            if o.hide_render: continue                     # not held while hidden (put away)
            lo, hi = bbox(o); c = (lo + hi) / 2
            if kind == "carry": D[f] = pinch(a, s) - c
            elif kind == "insert": D[f] = (c - pinch(a, s)) * 0.6    # damped: the IK answers ~0.8 of a target move and overshoots undamped
            else:
                d, t = min(((bd(lo, hi, q), q) for q in tips(a, s)), key=lambda x: x[0])
                D[f] = (t - c).normalized() * (d - 0.008) if d > 0.008 else None
        for f, d in D.items():
            if d is None: continue
            if kind == "insert": shift_ik(a, s, f, d)
            else: shift_obj(o, f, d)
        for fc in fcs(a) + fcs(o): fc.update()
    ds = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        if o.hide_render: continue
        lo, hi = bbox(o); ds.append((min(bd(lo, hi, q) for q in tips(a, s)), f))
    print("TIPFIX", kind, pn, cn, s, f0, f1, "max bbox-to-fingertip %.2f cm at f%d" % (max(ds)[0] * 100, max(ds)[1]))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("TIPFIX saved", OUT)
