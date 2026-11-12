import bpy, math
sc = bpy.context.scene; cam = sc.camera; prev = None; out = []
for f in range(1, 1061):
    sc.frame_set(f); q = cam.matrix_world.to_quaternion()
    if prev is not None:
        a = math.degrees(prev.rotation_difference(q).angle); a = min(a, 360 - a)
        if a > 20: out.append((f, round(a)))
    prev = q
print("TURN_GT20", out)
