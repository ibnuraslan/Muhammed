"""One continuous camera.  blender -b anim.blend --python 04_camera.py -- <out.blend>"""
import sys
exec(open("/home/user/Muhammed/blender/Tsunami2004_v001/scripts/lib.py").read())
exec(open("/home/user/Muhammed/blender/pipeline/anim_lib.py").read())
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
g = terrain_h
# (t, camera position, look-at point, lens mm)
K = [
    (0.0, (12.0, 13.0, g(12, 13) + 0.9), (4.5, 10.0, 0.7), 32),
    (1.0, (6.0, 28, g(6, 28) + 0.8), (4, 18, 0.6), 40),
    (2.0, (7.5, 50, g(7.5, 50) + 0.8), (5, 40, 0.3), 38),
    (3.0, (0.3, 88.0, g(0.3, 88) + 0.42), (-1.4, 90.3, g(-1.5, 90) + 0.08), 32),
    (4.0, (9, 50, g(9, 50) + 1.4), (7, 40, 0.5), 32),
    (5.3, (11, 66, g(11, 66) + 2.6), (3, 42, 0.8), 30),
    (6.3, (8.5, 58, g(8.5, 58) + 1.0), (4.6, 55.3, 0.0), 32),
    (7.2, (3.0, 50.5, g(3, 50.5) + 1.6), (0, 40, 1.4), 34),
    (8.2, (2.5, 37.5, g(2.5, 37.5) + 2.0), (0, 1600, 1.0), 70),
    (9.2, (4.2, 51.6, g(4.2, 51.6) + 1.55), (4.6, 54.3, 0.7), 40),
    (10.0, (6.0, 44, g(6, 44) + 2.4), (4.5, 55, 0.2), 26),
    (10.8, (7.0, 58, 14), (4, 38, 0), 24),
    (11.8, (3.0, 32, g(3, 32) + 1.6), (0, 900, 9), 40),
    (12.4, (1.5, 36, g(1.5, 36) + 1.8), (0, 900, 7), 55),
    (12.8, (1.0, 70, 6.0), (0, 400, 2), 26),
    (13.0, (0.7, 88, 2.4), (0, 600, 2), 26),
    (13.12, (0.5, 95, 0.0), (0, 101, -10), 24),
    (13.2, (0.0, 99, -14.0), (0, 101, -32), 24),
    (13.8, (-23, 100, -36), (0, 100, -37.5), 22),
    (14.8, (-18, 99.5, -36.5), (0, 100, -37.5), 26),
    (15.25, (-8, 96, -19), (0, 100, -33), 24),
    (15.5, (-3.0, 98.5, -13.0), (0, 100, -34), 24),
    (15.6, (-1.0, 100, g(-1, 100) + 0.9), (0, 500, 6), 24),
    (16.6, (0.0, 112, g(0, 112) + 1.4), (0, 330, 10), 26),
    (17.5, (2.0, 72, g(2, 72) + 1.3), (0, 180, 12), 24),
    (18.3, (15.0, -8, 1.45), (3, 80, 13), 20),
    (19.3, (15.0, -10, 1.7), (5, 40, 15), 18),
    (20.3, (17.0, -15, 1.8), (5, 12, 17), 16),
    (21.5, (85, -55, 16), (0, -26, 6), 30),
    (22.5, (34, -10, 13), (5, -30, 4), 24),
    (23.5, (48, -45, 14), (32, -70, 3), 24),
    (24.6, (34, -95, 8.0), (34, -132, 2), 24),
    (25.7, (33, -138, 8.5), (33, -178, 1.5), 22),
    (26.8, (31, -172, 9.0), (28, -212, 1), 22),
    (28.0, (26, -200, 22), (5, -250, 0), 24),
    (29.0, (-30, -192, 30), (-5, -245, 0), 24),
    (30.4, (-18, -185, 22), (-42, -160, 4), 24),
    (31.4, (-10, -128, 26), (-44, -162, 8), 24),
    (32.6, (-14, -140, 9.0), (-44, -164, 8), 28),
    (33.8, (-22, -190, 10), (-44, -160, 9), 26),
    (35.5, (-26, -186, 12), (-44, -162, 7), 26),
    (37.5, (-22, -195, 18), (-44, -160, 5), 26),
    (39.4, (-19, -200, 23), (-43, -157, 4), 26),
    (40.0, (-18.8, -200.4, 23.3), (-43, -157, 4), 26),
]
ts = [F(k[0]) for k in K]
posf = catmull([(f, Vector(k[1])) for f, k in zip(ts, K)])
dirf = catmull([(f, (Vector(k[2]) - Vector(k[1])).normalized()) for f, k in zip(ts, K)])
lensf = pchip([(f, float(k[3])) for f, k in zip(ts, K)])
cd = bpy.data.cameras.new("CAM_Film"); cam = bpy.data.objects.new("CAM_Film", cd); sc.collection.objects.link(cam); sc.camera = cam
cd.clip_start = 0.05; cd.clip_end = 9000; cd.sensor_fit = 'AUTO'; cd.sensor_width = 36
prev = None
for f in range(1, 2401):
    p = posf(f); d = dirf(f).normalized()
    # impact shake 21.5–23.0 s
    if F(21.55) <= f <= F(23.2):
        a = 0.12 * math.exp(-(f - F(21.6)) / 40.0)
        p = p + Vector((a * math.sin(f * 1.7), a * math.sin(f * 2.3 + 1), a * 0.7 * math.sin(f * 2.9 + 2)))
    tt_ = (f - 1) / 60.0
    if not (12.9 < tt_ < 15.7):
        p = Vector((p.x, p.y, max(p.z, g(p.x, p.y) + 0.7)))
    q = d.to_track_quat('-Z', 'Y'); e = q.to_euler()
    if prev is not None: e.make_compatible(prev)
    prev = e
    cam.location = p; cam.rotation_euler = e; cd.lens = lensf(f)
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f); cd.keyframe_insert("lens", frame=f)
for fc in _fcurves(cam.animation_data.action) + _fcurves(cd.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
json.dump if False else None
import json
beats = [(1, 0.0, "The sea began pulling back fast"), (2, 3.0, "exposing the ocean floor"), (3, 5.3, "People on the beach were confused"),
         (4, 7.2, "noticed a wave coming toward the shore"), (5, 10.8, "a massive tsunami"), (6, 13.1, "triggered by an undersea earthquake"),
         (7, 15.6, "As the wave got closer, it grew taller"), (8, 18.3, "up to 100 feet in some places"), (9, 21.5, "slammed into the coast with unimaginable force"),
         (10, 25.7, "destroying everything in its path"), (11, 28.0, "swept entire neighbourhoods away"), (12, 31.4, "leaving nothing behind but rubble"),
         (13, 33.8, "more than 167,000 people lost their lives")]
for b, t, w in beats:
    m = sc.timeline_markers.new("B%02d" % b, frame=F(t))
json.dump([{"beat": b, "frame": F(t), "first_words": w} for b, t, w in beats], open(HERE + "/beats.json", "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=out)
print("CAM_DONE")
