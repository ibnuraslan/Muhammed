import bpy, sys
from mathutils import Vector as V
out = sys.argv[sys.argv.index("--") + 1]
cam = bpy.data.objects["CAM_Film"]
P = [(594, V((-0.05, 2.65, 1.75))), (606, V((-0.05, 2.65, 1.75))), (625, V((0.05, 2.25, 1.95))), (640, V((-0.24, 1.45, 1.35))),
     (655, V((-0.192, -0.419, 0.593))), (668, V((-0.192, -0.419, 0.593)))]
def cat(f):
    for k in range(len(P) - 1):
        (f1, p1), (f2, p2) = P[k], P[k + 1]
        if f1 <= f <= f2:
            p0 = P[k - 1][1] if k > 0 else p1; p3 = P[k + 2][1] if k + 2 < len(P) else p2
            t = (f - f1) / (f2 - f1); t2 = t * t; t3 = t2 * t
            return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
act = cam.animation_data.action; n = 0
for layer in act.layers:
    for strip in layer.strips:
        for cb in strip.channelbags:
            for fc in cb.fcurves:
                if fc.data_path != "location": continue
                for kp in fc.keyframe_points:
                    f = kp.co.x
                    if 606 <= f <= 655:
                        v = cat(f)[fc.array_index]; dlt = v - kp.co.y
                        kp.co.y = v; kp.handle_left.y += dlt; kp.handle_right.y += dlt; n += 1
                fc.update()
print("REKEYED", n)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
