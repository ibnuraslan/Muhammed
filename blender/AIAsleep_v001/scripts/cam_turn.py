"""Per-frame camera turn (deg) and move (m); prints frames turning > 15 deg.  blender -b f.blend --python cam_turn.py"""
import bpy, math
sc = bpy.context.scene; c = sc.camera; prev = None; worst = []
for f in range(sc.frame_start, sc.frame_end + 1):
    sc.frame_set(f); M = c.matrix_world; d = M.to_quaternion(); p = M.translation.copy()
    if prev:
        a = math.degrees(prev[0].rotation_difference(d).angle); a = min(a, 360 - a); mv = (p - prev[1]).length
        if a > 15: worst.append((f, round(a, 1), round(mv, 3)))
    prev = (d, p)
print("TURNS>15", worst)
