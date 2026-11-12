"""Director acceptance: no frame-to-frame camera move > 0.25 m in 1-1060. blender -b film.blend --python cam_speed_check.py"""
import bpy
sc = bpy.context.scene; cam = sc.camera; prev = None; bad = []
for f in range(1, 1061):
    sc.frame_set(f); p = cam.matrix_world.translation.copy()
    if prev is not None and (p - prev).length > 0.25: bad.append((f, round((p - prev).length, 3)))
    prev = p
print("SPEED_BAD", bad)
