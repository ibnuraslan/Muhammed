"""v008b: props IN the hand while held (qa_check PROPMOVE, director e7b25f7: a moving prop needs a fingertip/palm within 3 cm).
blender -b in.blend --python prop_snap.py -- out.blend
For each held range the brick is keyed every frame; if its bounding box is more than 2 cm from the nearest finger joint that
qa_check measures (wrist head, finger k-2 / k-3 tails) it is moved straight toward that joint until it is 2 cm off."""
import bpy, sys
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene
HELD = (("Brick_Big", "Boy", "R", 1, 150), ("Brick_Small", "Boy", "R", 336, 736), ("Brick_Small", "Man", "L", 2152, 2310))
LIM = 0.02
def joints(arm, s):
    out = [arm.matrix_world @ arm.pose.bones["wrist." + s].head]
    for k in (1, 2, 3, 4, 5):
        for j in (2, 3):
            n = "finger%d-%d.%s" % (k, j, s)
            if n in arm.pose.bones: out.append(arm.matrix_world @ arm.pose.bones[n].tail)
    return out
def bbox(o):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); mw = e.matrix_world
    pts = [mw @ Vector(c) for c in e.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])
def bd(lo, hi, p): return Vector((max(lo.x - p.x, 0, p.x - hi.x), max(lo.y - p.y, 0, p.y - hi.y), max(lo.z - p.z, 0, p.z - hi.z))).length
for pn, cn, s, f0, f1 in HELD:
    o = bpy.data.objects[pn]; arm = bpy.data.objects[cn]; moved = []
    locs = {}
    for f in range(f0, f1 + 1):                       # sample the existing animation first (keys change interpolation)
        sc.frame_set(f); lo, hi = bbox(o); J = joints(arm, s)
        d, j = min(((bd(lo, hi, q), q) for q in J), key=lambda x: x[0])
        loc = o.matrix_world.translation.copy(); dl = Vector()
        if d > LIM:
            c = (lo + hi) / 2; dl = (j - c).normalized() * (d - LIM + 0.002)
        locs[f] = (o.location.copy() + (o.parent.matrix_world.inverted().to_3x3() @ dl if o.parent else dl), o.rotation_euler.copy() if o.rotation_mode != "QUATERNION" else o.rotation_quaternion.copy(), d)
    for f, (l, r, d) in locs.items():
        o.location = l; o.keyframe_insert("location", frame=f)
        if o.rotation_mode == "QUATERNION": o.rotation_quaternion = r; o.keyframe_insert("rotation_quaternion", frame=f)
        else: o.rotation_euler = r; o.keyframe_insert("rotation_euler", frame=f)
    print("SNAP", pn, cn, s, f0, f1, "frames moved", sum(1 for v in locs.values() if v[2] > LIM), "max before %.1f cm" % (max(v[2] for v in locs.values()) * 100))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SNAP saved", OUT)
