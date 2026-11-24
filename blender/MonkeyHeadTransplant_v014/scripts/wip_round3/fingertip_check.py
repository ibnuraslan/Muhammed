"""every frame of the carry: fingertip (distal phalanx tip) of each finger vs the carried head; reports tips inside the skull"""
import bpy
from mathutils.bvhtree import BVHTree
sc = bpy.context.scene; rig = bpy.data.objects["Surgeon"]; h = bpy.data.objects["MK_Head"]
dg = bpy.context.evaluated_depsgraph_get(); me = h.evaluated_get(dg).to_mesh()
bv = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [p.vertices[:] for p in me.polygons])
bad = []; worst = 0
for f in range(1, 400):
    sc.frame_set(f); inv = h.matrix_world.inverted()
    for s in "LR":
        for k in range(1, 6):
            pb = rig.pose.bones["finger%d-3.%s" % (k, s)]
            p = inv @ (rig.matrix_world @ pb.tail)
            loc, n, i, d = bv.find_nearest(p)
            if loc is not None and d < 0.06 and (p - loc).dot(n) < 0 and bv.ray_cast(p, n, 0.08)[0] is not None:
                bad.append((f, pb.name, round(d * 1000, 1))); worst = max(worst, d)
print("FINGERTIPS inside head:", len(bad), "frames", sorted(set(b[0] for b in bad))[:10], "max mm", round(worst * 1000, 1))
