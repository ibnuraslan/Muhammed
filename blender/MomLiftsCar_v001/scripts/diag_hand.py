import bpy
from mathutils import Vector
sc = bpy.context.scene; import sys; sc.frame_set(int(sys.argv[-1])); dg = bpy.context.evaluated_depsgraph_get()
rig = bpy.data.objects["Man"]; log = bpy.data.objects["Log"].evaluated_get(dg); inv = log.matrix_world.inverted()
def sd(p):
    ok, loc, n, i = log.closest_point_on_mesh(inv @ p); w = log.matrix_world @ loc; nw = (log.matrix_world.to_3x3() @ n).normalized()
    return round((p - w).length * (1 if (p - w).dot(nw) >= 0 else -1), 3)
for s in "LR":
    for b in ("wrist", "finger3-1", "finger3-3", "finger1-3", "metacarpal1"):
        pb = rig.pose.bones[b + "." + s]; h = rig.matrix_world @ pb.head; t = rig.matrix_world @ pb.tail
        print("DIAG", s, b, tuple(round(x, 3) for x in h), sd(h), sd(t))
    ik = rig.pose.bones["IK_hand." + s]; print("DIAG IK", s, tuple(round(x, 3) for x in rig.matrix_world @ ik.head), "wrist", tuple(round(x, 3) for x in rig.matrix_world @ rig.pose.bones["wrist." + s].head))
