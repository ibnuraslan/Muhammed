"""v008f (found by watching): after mom_head.py pushed Mom's left hand out of the boy's head (989-997), her arm went UP behind her
own head. The left hand now follows a smooth path from its 978 pose to its 1004 pose that dips under the boy's chin (15 cm down at
the middle, toward her), keyed every frame 979-1003; then checked against the boy's head and her own head.
blender -b in.blend --python mom_route.py -- out.blend"""
import bpy, sys, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; vl = bpy.context.view_layer
M = bpy.data.objects["Mom"]; IK = M.pose.bones["IK_hand.L"]
def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
sc.frame_set(978); m0 = IK.matrix.copy(); sc.frame_set(1004); m1 = IK.matrix.copy()
W0, W1 = M.matrix_world @ m0.translation, M.matrix_world @ m1.translation
sc.frame_set(990); toward = (M.matrix_world @ M.pose.bones["spine03"].head) - (W0 + W1) / 2; toward.z = 0
toward = toward.normalized() if toward.length > 1e-4 else Vector()
q0, q1 = m0.to_quaternion(), m1.to_quaternion()
keys = {}
for f in range(979, 1004):
    s = smooth((f - 978) / 26.0); p = W0.lerp(W1, s) + (Vector((0, 0, -0.15)) + toward * 0.06) * math.sin(math.pi * s)
    keys[f] = (p, q0.slerp(q1, s))
for f, (p, q) in keys.items():
    sc.frame_set(f); mm = q.to_matrix().to_4x4(); mm.translation = M.matrix_world.inverted() @ p
    IK.matrix = mm; vl.update(); IK.keyframe_insert("location", frame=f, group=IK.name)
    if IK.rotation_mode == "QUATERNION": IK.keyframe_insert("rotation_quaternion", frame=f, group=IK.name)
# check against the boy's head
BB, Bo, MB = bpy.data.objects["Boy_Body"], bpy.data.objects["Boy"], bpy.data.objects["Mom_Body"]
for b in (BB, MB):
    for m in b.modifiers:
        if m.type in ("MASK", "SUBSURF", "MULTIRES"): m.show_viewport = False
def dom(b, arm):
    gi = {g.index: g.name for g in b.vertex_groups if g.name in arm.data.bones}; out = []
    for v in b.data.vertices:
        g = max((g for g in v.groups if g.group in gi), key=lambda g: g.weight, default=None); out.append(gi[g.group].lower() if g else "")
    return out
db, dm = dom(BB, Bo), dom(MB, M)
HEAD = ("head", "neck", "jaw", "eye", "ear", "nose", "lip", "cheek", "brow", "temporal", "tongue", "levator", "oris", "risorius", "special", "orbicularis")
probe = [i for i, n in enumerate(dm) if n.endswith(".l") and n.startswith(("lowerarm", "wrist", "metacarpal", "finger"))]
worst = 9
for f in range(976, 1008):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    e = BB.evaluated_get(dg); me = e.to_mesh(); V = [e.matrix_world @ v.co for v in me.vertices]
    T = BVHTree.FromPolygons(V, [tuple(p.vertices) for p in me.polygons if all(db[i].startswith(HEAD) for i in p.vertices)]); e.to_mesh_clear()
    e = MB.evaluated_get(dg); me = e.to_mesh(); mw = e.matrix_world
    for i in probe:
        p = mw @ me.vertices[i].co; loc, n, _, d = T.find_nearest(p, 0.3)
        if loc is not None: worst = min(worst, d if (p - loc).dot(n) >= 0 else -d)
    e.to_mesh_clear()
print("MOMROUTE min clearance to the boy's head %.1f cm" % (worst * 100))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
