"""One continuous camera.  blender -b anim.blend --python 04_camera.py -- <out.blend>"""
import sys
exec(open("/home/user/Muhammed/blender/Tsunami2004_v001/scripts/lib.py").read())
exec(open("/home/user/Muhammed/blender/pipeline/anim_lib.py").read())
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
g = terrain_h
# (t, camera position, look-at point, lens mm)
K = [
    (0.0, (3.6, 5.8, g(3.6, 5.8) + 0.55), (5, 25, 0.4), 26),
    (1.0, (4.0, 22, g(4, 22) + 0.7), (5, 60, -0.6), 22),
    (2.0, (4.0, 52, g(4, 52) + 0.8), (3, 120, -2.2), 24),
    (3.0, (0.3, 88.0, g(0.3, 88) + 0.42), (-1.4, 90.3, g(-1.5, 90) + 0.08), 32),
    (4.0, (4.0, 95, g(4, 95) + 2.4), (10, 104, g(10, 104) + 0.2), 24),
    (5.3, (11, 66, g(11, 66) + 2.6), (3, 42, 0.8), 30),
    (6.3, (8.5, 58, g(8.5, 58) + 1.0), (4.6, 55.3, 0.0), 32),
    (7.2, (1.0, 33.5, g(1, 33.5) + 1.8), (4, 300, 0.5), 32),
    (8.2, (2.5, 37.5, g(2.5, 37.5) + 2.0), (0, 1600, 1.0), 70),
    (9.2, (4.2, 51.6, g(4.2, 51.6) + 1.55), (4.6, 54.3, 0.7), 40),
    (10.0, (6.0, 44, g(6, 44) + 2.4), (4.5, 55, 0.2), 26),
    (10.8, (8.0, 62, 24), (0, 600, 0), 24),
    (11.8, (0.0, 160, 115), (0, 1150, 0), 32),
    (12.6, (0.0, 385, 50), (0, 470, -12), 24),
    (13.1, (-4.0, 458, -5.6), (0, 470, -36), 24),
    (13.8, (-19, 470, -35), (0, 470, -37), 26),
    (14.8, (-12, 469, -36.5), (0, 470.5, -37.5), 32),
    (15.25, (-8.0, 466, -19), (0, 470, -33), 24),
    (15.6, (-2.0, 452, -3.4), (0, 600, 6), 22),
    (16.6, (0.0, 340, g(0, 340) + 1.6), (0, 450, 14), 22),
    (17.5, (2.0, 150, 5), (0, 300, 26), 22),
    (18.3, (6.0, -14, 1.2 + g(6, -14)), (2, 60, 20), 22),
    (19.3, (5.0, -22, 1.7 + 0.6), (3, 30, 12), 22),
    (20.3, (95, -32, 3.5), (0, 5, 14), 30),
    (21.5, (80, -50, 16), (0, -28, 6), 24),
    (22.5, (34, -10, 13), (5, -30, 4), 24),
    (23.5, (48, -45, 14), (32, -70, 3), 24),
    (24.6, (36, -80, 13), (30, -120, 3), 24),
    (25.7, (34, -128, 12), (34, -185, 2), 22),
    (26.8, (28, -160, 10), (20, -215, 1), 22),
    (28.0, (20, -180, 34), (0, -250, 0), 24),
    (29.0, (-60, -150, 92), (0, -222, 0), 24),
    (30.4, (0.0, -198, 150), (0, -204, 0), 24),
    (31.4, (-10, -128, 26), (-44, -162, 8), 24),
    (32.6, (-24, -141, 6.5), (-44, -166, 7), 28),
    (33.8, (-30, -182, 8), (-44, -160, 9), 26),
    (35.5, (-20, -196, 20), (-40, -150, 5), 24),
    (37.5, (-6, -214, 38), (-30, -120, 0), 24),
    (39.4, (0, -224, 50), (-20, -90, 0), 24),
    (40.0, (0.3, -224.6, 50.6), (-19, -88, 0), 24),
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
