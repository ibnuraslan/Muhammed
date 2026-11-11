"""One continuous camera for PrisonKeyCake (no cuts, no markers).
blender -b work/anim.blend --python scripts/04_camera.py -- work/film.blend"""
import sys, os, math, json
import bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
V = lambda *a: Vector(a)
for o in [o for o in bpy.data.objects if o.type == 'CAMERA']:
    bpy.data.objects.remove(o, do_unlink=True)
cd = bpy.data.cameras.new("CAM_Film"); cd.lens = 24; cd.sensor_fit = 'AUTO'; cd.clip_start = 0.02; cd.clip_end = 200
cd.dof.use_dof = True; cd.dof.aperture_fstop = 4.0
cam = bpy.data.objects.new("CAM_Film", cd); sc.collection.objects.link(cam); sc.camera = cam
aim = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(aim)
tt = cam.constraints.new('TRACK_TO'); tt.target = aim; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
cd.dof.focus_object = aim

# frame, camera position, aim point, lens, f-stop
K = [
    # beat 1  (f1) master key into candle wax
    (1,    V(1.62, 0.40, 1.90), V(0.95, 1.45, 0.95), 22, 5.6),
    (28,   V(1.48, 1.66, 1.58), V(0.95, 1.40, 1.05), 24, 4.0),
    (60,   V(1.34, 1.62, 1.34), V(1.01, 1.29, 1.27), 45, 2.8),
    (115,  V(0.70, 1.80, 1.30), V(0.92, 1.12, 1.45), 28, 4.0),
    (175,  V(0.98, 1.86, 1.12), V(0.94, 1.50, 0.80), 45, 2.8),
    (240,  V(1.12, 1.84, 0.98), V(0.93, 1.50, 0.80), 50, 2.8),
    # beat 2  (f259) perfect impression
    (290,  V(1.08, 1.74, 0.93), V(0.92, 1.50, 0.80), 55, 2.8),
    (328,  V(0.97, 1.68, 1.12), V(0.92, 1.52, 0.795), 45, 4.0),
    (350,  V(0.84, 1.86, 1.72), V(0.80, 2.60, 2.05), 24, 5.6),
    (362,  V(0.80, 2.18, 2.16), V(0.88, 3.20, 1.40), 22, 5.6),
    # beat 3  (f367) smuggled out
    (385,  V(1.60, 3.50, 1.15), V(1.10, 2.95, 0.90), 40, 4.0),
    (430,  V(2.40, 2.70, 1.70), V(1.10, 3.20, 1.20), 24, 5.6),
    (478,  V(3.90, 2.90, 1.40), V(2.50, 3.60, 1.20), 24, 5.6),
    (510,  V(7.00, 4.55, 1.85), V(10.5, 6.00, 1.50), 22, 5.6),
    # beat 4  (f511) cast a metal copy
    (545,  V(10.6, 6.00, 1.80), V(14.5, 6.90, 1.10), 22, 5.6),
    (585,  V(15.15, 6.25, 0.98), V(14.65, 7.00, 1.05), 28, 4.0),
    (632,  V(15.20, 6.50, 1.32), V(14.65, 6.95, 0.95), 35, 2.8),
    (684,  V(15.25, 6.55, 1.40), V(14.62, 6.98, 0.94), 45, 2.8),
    # beat 5  (f685) key into the cake, back through the gate
    (722,  V(15.60, 6.55, 1.25), V(15.00, 6.95, 0.95), 40, 2.8),
    (762,  V(15.28, 6.18, 1.62), V(15.25, 6.95, 0.90), 30, 4.0),
    (805,  V(15.65, 6.00, 1.90), V(15.40, 6.90, 1.00), 26, 4.0),
    (838,  V(13.00, 6.00, 1.60), V(14.30, 6.15, 1.10), 26, 5.6),
    (858,  V(11.00, 6.00, 1.80), V(13.50, 6.10, 1.20), 24, 5.6),
    # whip back across the night yard and in through the cell window
    (876,  V(4.00, 3.60, 2.40), V(0.80, 2.20, 1.90), 22, 5.6),
    (886,  V(1.00, 3.00, 2.20), V(1.50, 0.70, 1.20), 24, 5.6),
    (894,  V(0.80, 2.15, 2.16), V(1.90, 0.60, 1.10), 24, 4.0),
    # beat 6  (f871) it didn't fit
    (903,  V(1.70, 0.50, 2.00), V(1.98, 0.62, 1.10), 30, 4.0),
    (912,  V(1.95, 0.36, 1.10), V(1.98, 0.62, 1.07), 40, 2.8),
    (936,  V(1.95, 0.30, 1.55), V(1.85, 0.88, 1.52), 30, 4.0),
    (962,  V(1.95, 0.38, 1.05), V(1.98, 0.62, 1.07), 40, 2.8),
    (977,  V(1.72, 0.55, 2.05), V(1.80, 0.75, 1.30), 26, 4.0),
    (992,  V(1.20, 1.45, 1.42), V(1.85, 0.62, 1.35), 24, 4.0),
    (1005, V(1.40, 1.30, 2.05), V(1.80, 0.70, 1.40), 26, 4.0),
    (1018, V(1.93, 0.28, 1.48), V(1.95, 0.85, 1.45), 30, 4.0),
    (1046, V(1.25, 1.55, 1.65), V(1.40, 0.60, 1.30), 24, 4.0),
    # beat 7  (f1057) another impression, waited
    (1068, V(0.40, 1.45, 1.50), V(0.92, 1.30, 1.00), 24, 4.0),
    (1094, V(1.55, 1.75, 1.25), V(0.92, 1.45, 0.85), 28, 4.0),
    (1150, V(1.25, 1.76, 1.15), V(0.90, 1.45, 0.85), 35, 2.8),
    (1200, V(1.40, 1.20, 1.40), V(0.80, 2.10, 2.00), 24, 4.0),
    (1242, V(-1.20, -1.50, 2.30), V(0.50, 0.80, 0.60), 20, 5.6),
    (1282, V(0.12, 1.36, 0.92), V(0.55, 1.72, 0.86), 30, 2.8),
    # beat 8  (f1303) this time the key worked
    (1322, V(0.92, 1.85, 1.22), V(1.18, 1.42, 0.86), 32, 4.0),
    (1360, V(1.58, 1.80, 1.25), V(1.15, 1.30, 1.05), 30, 4.0),
    (1392, V(0.75, 1.15, 1.50), V(1.90, 0.60, 1.10), 24, 4.0),
    (1404, V(1.30, 0.30, 1.75), V(1.90, 0.60, 1.15), 28, 4.0),
    (1416, V(1.95, 0.36, 1.10), V(1.98, 0.62, 1.07), 40, 2.8),
    (1432, V(1.95, 0.30, 1.55), V(1.85, 0.88, 1.55), 30, 4.0),
    # beat 9  (f1429) through every gate, out of the prison
    (1450, V(1.20, 0.95, 1.55), V(2.30, 0.20, 1.25), 22, 5.6),
    (1478, V(2.08, 0.38, 1.98), V(3.40, 0.15, 1.30), 22, 5.6),
    (1500, V(3.30, 0.25, 2.30), V(2.70, 0.30, 1.55), 24, 4.0),
    (1518, V(4.30, 0.05, 1.70), V(3.40, 0.25, 1.55), 26, 4.0),
    (1548, V(6.00, 0.00, 1.50), V(4.90, 0.15, 1.45), 24, 4.0),
    (1582, V(7.05, -0.05, 1.15), V(5.90, 0.10, 1.45), 24, 4.0),
    (1630, V(7.40, -0.55, 0.70), V(7.30, 0.80, 1.20), 22, 5.6),
    (1700, V(7.45, 1.40, 1.60), V(8.20, 3.20, 1.20), 22, 5.6),
    # beat 10 (f1681) decades later: crane over the wall to the government steps
    (1725, V(7.00, 4.50, 4.60), V(9.50, 5.60, 0.90), 22, 5.6),
    (1748, V(4.00, 8.00, 9.00), V(2.00, 20.0, 12.0), 22, 5.6),
    (1785, V(2.60, 13.6, 7.60), V(0.00, 22.0, 2.50), 24, 5.6),
    (1812, V(2.20, 16.0, 6.20), V(0.00, 22.4, 2.80), 26, 5.6),
    (1848, V(1.60, 16.6, 3.90), V(0.00, 22.5, 2.70), 34, 5.6),
    (1890, V(1.20, 16.8, 3.55), V(0.00, 22.55, 2.75), 42, 5.6),
]
fc = catmull([(f, c) for f, c, a, l, s in K]); fa = catmull([(f, a) for f, c, a, l, s in K])
fl = pchip([(f, float(l)) for f, c, a, l, s in K]); fs = pchip([(f, float(s)) for f, c, a, l, s in K])
for f in range(1, 1891, 2):
    cam.location = fc(f); cam.keyframe_insert("location", frame=f)
    aim.location = fa(f); aim.keyframe_insert("location", frame=f)
    cd.lens = fl(f); cd.keyframe_insert("lens", frame=f)
    cd.dof.aperture_fstop = fs(f); cd.dof.keyframe_insert("aperture_fstop", frame=f)
# beats.json (target times; the director retimes to the VO with pipeline/retime_to_vo.py)
BEATS = [(1, 1, "He got hold of the prison's master key"), (2, 259, "making a perfect impression"), (3, 367, "The mold was smuggled out"),
         (4, 511, "and his allies used it"), (5, 685, "They hid the key inside a cake"), (6, 871, "But when he tried the key"),
         (7, 1057, "So he sent out another"), (8, 1303, "And this time, the key worked"), (9, 1429, "He passed through every locked gate"),
         (10, 1681, "Years later, he became president")]
json.dump([{"beat": b, "frame": f, "first_words": w} for b, f, w in BEATS], open(os.path.join(HERE, "..", "beats.json"), "w"), indent=1)
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("CAM saved", OUT)
