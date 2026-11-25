"""forearm/wrist points in FRONT of the carried head (toward the camera side, -y of the head centre) during the hold"""
import bpy
from mathutils import Vector
sc = bpy.context.scene; rig = bpy.data.objects["Surgeon"]; h = bpy.data.objects["MK_Head"]
worst = []
for f in range(60, 380, 4):
    sc.frame_set(f)
    hv = [h.matrix_world @ Vector(c) for c in h.bound_box]
    lo = Vector([min(v[i] for v in hv) for i in range(3)]); hi = Vector([max(v[i] for v in hv) for i in range(3)]); c = (lo + hi) / 2
    for bn in ("lowerarm01.L", "lowerarm02.L", "wrist.L", "lowerarm01.R", "lowerarm02.R", "wrist.R"):
        pb = rig.pose.bones[bn]
        for u in (0.0, 0.5, 1.0):
            p = rig.matrix_world @ pb.head.lerp(pb.tail, u)
            if lo.x - 0.03 < p.x < hi.x + 0.03 and lo.z - 0.05 < p.z < hi.z + 0.03 and p.y < c.y:
                worst.append((f, bn, round((c.y - p.y) * 1000)))
print("FOREARM_FRONT", len(worst), worst[:12])
