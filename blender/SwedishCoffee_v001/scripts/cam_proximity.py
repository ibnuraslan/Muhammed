"""Camera proximity check: is the camera inside or almost touching a rendered character?
blender -b film.blend --python cam_proximity.py -- <report.txt> [step=3] [min_m=0.35]
For every sampled frame, every rendered character: distance from the camera to the head, neck, spine, pelvis, arm and leg bones (segments).
Flags CAM_NEAR_BODY when the camera is closer than min_m to any bone segment (that is inside or right at the skin/clothes)."""
import sys, bpy
from mathutils.geometry import intersect_point_line
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 3; MIN = float(a[2]) if len(a) > 2 else 0.35
sc = bpy.context.scene; cam = sc.camera
arms = [o for o in bpy.data.objects if o.type == 'ARMATURE' and o.users_collection[0].name.startswith("S")]
KEYS = ("head", "neck", "spine", "pelvis", "upperarm", "lowerarm", "upperleg", "lowerleg", "root")
hits = []
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); cp = cam.matrix_world.translation
    for arm in arms:
        if arm.hide_render or not any(not c.hide_render for c in arm.children if c.type == 'MESH'): continue
        M = arm.matrix_world; best = 9.0; bn = ""
        for pb in arm.pose.bones:
            if not pb.name.startswith(KEYS): continue
            h, t = M @ pb.head, M @ pb.tail
            p, u = intersect_point_line(cp, h, t); u = max(0.0, min(1.0, u)); q = h.lerp(t, u)
            d = (cp - q).length
            if d < best: best, bn = d, pb.name
        if best < MIN: hits.append((f, arm.name, bn, best))
lines = ["camera proximity: step %d, threshold %.2f m" % (STEP, MIN), "CAM_NEAR_BODY %d" % len(hits)]
for f, n, b, d in hits: lines.append("    f%04d %s %s %.2f m" % (f, n, b, d))
open(OUT, "w").write("\n".join(lines) + "\n"); print("\n".join(lines[:60]))
