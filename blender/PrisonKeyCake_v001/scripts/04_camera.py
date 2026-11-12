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
    (1,    V(0.45, 1.86, 1.58), V(0.92, 1.05, 1.42), 26, 5.6),
    (28,   V(1.48, 1.66, 1.58), V(0.95, 1.40, 1.05), 24, 4.0),
    (60,   V(1.34, 1.62, 1.34), V(1.01, 1.29, 1.27), 45, 2.8),
    (115,  V(0.70, 1.80, 1.30), V(0.92, 1.12, 1.45), 28, 4.0),
    (145,  V(0.85, 1.88, 1.38), V(0.92, 1.30, 1.10), 30, 4.0),
    (178,  V(1.00, 1.90, 1.12), V(0.94, 1.50, 0.80), 38, 2.8),
    (240,  V(1.16, 1.90, 1.06), V(0.93, 1.50, 0.80), 40, 2.8),
    # beat 2  (f259) perfect impression
    (290,  V(1.08, 1.74, 0.93), V(0.92, 1.50, 0.80), 55, 2.8),
    (328,  V(1.04, 1.60, 1.32), V(0.92, 1.50, 0.86), 36, 4.0),
    (340,  V(1.25, 1.86, 1.55), V(0.90, 1.35, 1.30), 24, 4.0),
    (350,  V(0.84, 1.86, 1.72), V(0.80, 2.60, 2.05), 24, 5.6),
    (360,  V(0.80, 2.18, 2.05), V(0.95, 3.10, 1.45), 22, 5.6),
    (370,  V(1.55, 3.30, 1.62), V(0.92, 3.05, 1.45), 28, 4.0),
    # beat 3  (f367) smuggled out
    (385,  V(1.80, 3.74, 1.26), V(1.10, 2.95, 0.92), 35, 4.0),
    (430,  V(2.40, 2.70, 1.70), V(1.10, 3.20, 1.20), 24, 5.6),
    (478,  V(3.90, 2.90, 1.40), V(2.50, 3.60, 1.20), 24, 5.6),
    (510,  V(7.00, 4.55, 1.85), V(10.5, 6.00, 1.50), 22, 5.6),
    # beat 4  (f511) cast a metal copy
    (545,  V(10.6, 6.00, 1.80), V(14.5, 6.90, 1.10), 22, 5.6),
    (585,  V(15.38, 6.60, 1.15), V(14.65, 7.00, 1.05), 28, 4.0),
    (632,  V(15.20, 6.50, 1.32), V(14.65, 6.95, 0.95), 35, 2.8),
    (684,  V(15.25, 6.55, 1.40), V(14.62, 6.98, 0.94), 45, 2.8),
    # beat 5  (f685) key into the cake, back through the gate
    (722,  V(15.60, 6.55, 1.25), V(15.00, 6.95, 0.95), 40, 2.8),
    (762,  V(15.28, 6.18, 1.62), V(15.25, 6.95, 0.90), 30, 4.0),
    (805,  V(15.65, 6.00, 1.90), V(15.40, 6.90, 1.00), 26, 4.0),
    (834,  V(13.00, 6.00, 1.60), V(14.30, 6.15, 1.10), 26, 5.6),
    (848,  V(11.00, 6.00, 1.80), V(13.50, 6.10, 1.20), 24, 5.6),
    # whip back across the night yard and in through the cell window
    (858,  V(4.00, 3.60, 2.40), V(0.80, 2.20, 1.90), 22, 5.6),
    (866,  V(1.00, 3.00, 2.20), V(1.50, 0.80, 1.45), 24, 5.6),
    (874,  V(0.80, 2.15, 2.05), V(1.55, 0.85, 1.55), 24, 4.0),
    (888,  V(1.05, 1.55, 1.80), V(1.80, 0.70, 1.25), 26, 4.0),
    # beat 6  (f871) it didn't fit
    (903,  V(1.70, 0.50, 2.00), V(1.98, 0.62, 1.10), 30, 4.0),
    (912,  V(1.95, 0.36, 1.10), V(1.98, 0.62, 1.07), 40, 2.8),
    (936,  V(1.95, 0.30, 1.55), V(1.85, 0.88, 1.52), 30, 4.0),
    (962,  V(1.95, 0.38, 1.05), V(1.98, 0.62, 1.07), 40, 2.8),
    (977,  V(1.72, 0.55, 2.05), V(1.80, 0.75, 1.30), 26, 4.0),
    (992,  V(1.20, 1.45, 1.42), V(1.85, 0.62, 1.35), 24, 4.0),
    (1005, V(1.40, 1.30, 2.05), V(1.80, 0.70, 1.40), 26, 4.0),
    (1018, V(1.93, 0.28, 1.48), V(1.95, 0.85, 1.45), 30, 4.0),
    (1046, V(1.82, 1.30, 1.62), V(1.45, 0.90, 1.55), 26, 4.0),
    # beat 7  (f1057) another impression, waited
    (1060, V(1.72, 1.50, 1.62), V(1.30, 0.93, 1.50), 26, 4.0),
    (1082, V(0.30, 1.55, 1.60), V(1.00, 0.97, 1.40), 24, 4.0),
    (1094, V(1.55, 1.75, 1.25), V(0.92, 1.45, 0.85), 28, 4.0),
    (1150, V(1.25, 1.76, 1.15), V(0.90, 1.45, 0.85), 35, 2.8),
    (1172, V(1.75, 1.85, 1.55), V(0.92, 1.15, 1.25), 26, 4.0),
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
    (1610, V(7.50, 0.45, 1.60), V(6.60, 0.10, 1.50), 24, 5.6),
    (1640, V(7.62, 1.95, 1.62), V(7.30, 0.30, 1.55), 24, 5.6),
    (1666, V(7.95, 2.95, 1.70), V(7.50, 1.20, 1.55), 26, 5.6),
    # beat 10 (f1681) decades later: crane over the wall to the government steps
    (1692, V(8.30, 3.95, 2.40), V(7.85, 2.45, 1.55), 24, 5.6),
    (1712, V(8.60, 4.70, 3.10), V(8.20, 3.05, 1.50), 24, 5.6),
    (1732, V(7.60, 5.20, 4.80), V(9.00, 4.60, 1.00), 22, 5.6),
    (1748, V(4.00, 8.00, 9.00), V(2.00, 20.0, 12.0), 22, 5.6),
    (1785, V(2.60, 13.6, 7.60), V(0.00, 22.0, 2.50), 24, 5.6),
    (1812, V(2.20, 16.0, 6.20), V(0.00, 22.4, 2.80), 26, 5.6),
    (1848, V(1.60, 16.6, 3.90), V(0.00, 22.5, 2.70), 34, 5.6),
    (1890, V(1.20, 16.8, 3.55), V(0.00, 22.55, 2.75), 42, 5.6),
]
fc = catmull([(f, c) for f, c, a, l, s in K]); fa = catmull([(f, a) for f, c, a, l, s in K])
fl = pchip([(f, float(l)) for f, c, a, l, s in K]); fs = pchip([(f, float(s)) for f, c, a, l, s in K])
# ---- clearance: keep the camera >= 0.38 m from bodies/heads/legs (0.22 m from hands) using the posed skeletons
ARMS = [o for o in bpy.data.objects if o.type == 'ARMATURE' and "head" in o.pose.bones and "root" in o.pose.bones]
def seg_dist(p, a, b):
    ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / max(1e-9, ab.dot(ab)))); q = a + ab * t; return (p - q).length, q
OFF = {}
dg = bpy.context.evaluated_depsgraph_get()
WALLS = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(("Cell_", "Block_", "Ground", "Tunnel", "Yard", "Gate", "Wall"))]
def bones_of(f):
    out = []
    for arm in ARMS:
        if arm.hide_render or arm.hide_viewport: continue
        M = arm.matrix_world
        for pb in arm.pose.bones:
            n = pb.name
            if n.startswith(("IK_", "Pole_", "root")) or any(k in n for k in ("toe", "oris", "levator", "risorius", "special", "eye", "jaw", "tongue", "breast", "metacarpal")): continue
            if pb.length > 0.6: continue
            hand = n.startswith(("finger", "wrist", "lowerarm"))
            rad = 0.07 if hand or n.startswith(("upperarm", "lowerleg", "foot")) else (0.13 if n.startswith(("neck", "head")) else 0.17)
            out.append((M @ pb.head, M @ pb.tail, rad, 0.22 if hand else 0.38))
    return out
for f in range(1, 1891, 2):
    sc.frame_set(f); p0 = fc(f); p = p0.copy()
    bs = [b for b in bones_of(f) if (b[0] - p0).length < 1.5]
    for it in range(8):
        worst = None
        for a_, b_, rad, need in bs:
            d, q = seg_dist(p, a_, b_); deficit = need - (d - rad)
            if deficit > 1e-3 and d > 1e-6 and (worst is None or deficit > worst[0]): worst = (deficit, (p - q).normalized())
        if worst is None: break
        p = p + worst[1] * worst[0]
    v = p - p0
    if v.length > 0.6: v = v.normalized() * 0.6
    OFF[f] = v
fr = sorted(OFF)
SM = {}
for f in fr:
    acc = Vector((0, 0, 0)); wsum = 0.0
    for g in range(f - 12, f + 13, 2):
        if g in OFF:
            w = math.exp(-((g - f) / 7.0) ** 2); acc += OFF[g] * w; wsum += w
    SM[f] = acc / wsum
for f in fr:
    if SM[f].length < OFF[f].length:
        SM[f] = SM[f].normalized() * OFF[f].length if SM[f].length > 1e-6 else OFF[f]
print("CLEARANCE frames pushed", sum(1 for f in fr if OFF[f].length > 1e-4), "max", round(max(v.length for v in OFF.values()), 3), "big", [f for f in fr if OFF[f].length > 0.45][:40])
dg = bpy.context.evaluated_depsgraph_get()
nclip = 0
DIRS = [Vector(d).normalized() for d in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1),(1,1,1),(-1,-1,1),(1,-1,-1),(-1,1,-1),(1,1,-1),(-1,-1,-1),(1,-1,1),(-1,1,1))]
for f in range(1, 1891, 2):
    p0 = fc(f); v = SM.get(f, Vector())
    if v.length > 1e-4:
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
        hit, loc, nrm, idx, ob, mx = sc.ray_cast(dg, p0, v.normalized(), distance=v.length + 0.15)
        if hit and not (ob and ob.parent and ob.parent.type == 'ARMATURE') and ob.type == 'MESH' and not any(m.type == 'ARMATURE' for m in ob.modifiers):
            v = v.normalized() * max(0.0, (loc - p0).length - 0.15); nclip += 1
    q = p0 + v
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    win = 1.95 < q.y < 2.45 and 0.55 < q.x < 1.05 and 1.6 < q.z < 2.25   # threading the cell-window bars
    if win: q.x = 0.80 + (q.x - 0.80) * 0.1
    for it in range(0 if win else 4):   # stay >= 0.15 m off any surface (props, doors, bars)
        near = None
        for d in DIRS:
            hit, loc, nrm, idx, ob, mx = sc.ray_cast(dg, q, d, distance=0.15)
            if hit and ob.name not in ("CellDust", "Smoke", "Candle_Flame") and nrm.dot(d) < 0:
                dist = (loc - q).length
                if near is None or dist < near[0]: near = (dist, d)
        if near is None: break
        q = q - near[1] * (0.15 - near[0] + 0.005)
    cam.location = q; cam.keyframe_insert("location", frame=f)
    aim.location = fa(f); aim.keyframe_insert("location", frame=f)
    cd.lens = fl(f); cd.keyframe_insert("lens", frame=f)
    cd.dof.aperture_fstop = fs(f); cd.dof.keyframe_insert("aperture_fstop", frame=f)
print("CLEARANCE wall-clipped", nclip)
# beats.json (target times; the director retimes to the VO with pipeline/retime_to_vo.py)
BEATS = [(1, 1, "He got hold of the prison's master key"), (2, 259, "making a perfect impression"), (3, 367, "The mold was smuggled out"),
         (4, 511, "and his allies used it"), (5, 685, "They hid the key inside a cake"), (6, 871, "But when he tried the key"),
         (7, 1057, "So he sent out another"), (8, 1303, "And this time, the key worked"), (9, 1429, "He passed through every locked gate"),
         (10, 1681, "Years later, he became president")]
json.dump([{"beat": b, "frame": f, "first_words": w} for b, f, w in BEATS], open(os.path.join(HERE, "..", "beats.json"), "w"), indent=1)
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("CAM saved", OUT)
