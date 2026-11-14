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
    (60,   V(1.42, 1.86, 1.48), V(1.00, 1.38, 1.30), 32, 2.8),
    (92,   V(1.55, 1.86, 1.58), V(0.95, 1.30, 1.15), 28, 4.0),   # steady 3/4: his face and both hands at the wax
    (240,  V(1.52, 1.86, 1.55), V(0.95, 1.35, 1.08), 30, 4.0),
    # beat 2  (f259) perfect impression
    (290,  V(1.50, 1.86, 1.52), V(0.95, 1.40, 1.08), 30, 4.0),
    (328,  V(1.45, 1.84, 1.55), V(0.95, 1.45, 1.20), 28, 4.0),
    (340,  V(1.25, 1.86, 1.55), V(0.90, 1.35, 1.30), 24, 4.0),
    (350,  V(0.84, 1.86, 1.72), V(0.80, 2.60, 2.05), 24, 5.6),
    (360,  V(0.80, 2.18, 2.05), V(0.95, 3.10, 1.45), 22, 5.6),
    (370,  V(1.55, 3.30, 1.62), V(0.92, 3.05, 1.45), 28, 4.0),
    # beat 3  (f367) smuggled out
    (385,  V(1.80, 3.74, 1.26), V(1.10, 2.95, 0.92), 35, 4.0),
    (430,  V(2.40, 2.70, 1.70), V(1.10, 3.20, 1.20), 24, 5.6),
    (478,  V(3.90, 2.90, 1.40), V(2.50, 3.60, 1.20), 24, 5.6),
    (510,  V(7.00, 4.55, 1.85), V(9.80, 5.90, 1.50), 22, 5.6),
    # beat 4  (f511) cast a metal copy
    (540,  V(7.10, 4.50, 1.85), V(10.0, 6.00, 1.50), 22, 5.6),
    ("CUT", 541),
    (541,  V(15.20, 6.05, 1.50), V(14.20, 6.95, 1.20), 24, 4.0),   # the ally on the long handle, in frame with the pot
    (585,  V(15.20, 6.05, 1.50), V(14.20, 6.95, 1.20), 24, 4.0),
    (632,  V(15.30, 6.15, 1.70), V(14.55, 6.85, 1.10), 26, 4.0),
    (684,  V(15.30, 6.15, 1.70), V(14.60, 6.85, 1.05), 26, 4.0),
    # beat 5  (f685) key into the cake, back through the gate
    (722,  V(16.00, 6.10, 1.65), V(15.00, 6.85, 1.05), 28, 4.0),
    (762,  V(15.25, 7.30, 1.30), V(14.85, 6.45, 1.20), 28, 4.0),
    (805,  V(16.00, 6.00, 1.65), V(15.20, 6.70, 1.35), 26, 4.0),
    (834,  V(13.55, 5.20, 1.55), V(14.15, 6.15, 1.30), 26, 5.6),   # hand-off seen from the side, both faces
    (852,  V(13.30, 5.15, 1.60), V(13.95, 6.10, 1.35), 26, 5.6),
    ("CUT", 853),
    (853,  V(1.70, 0.30, 1.65), V(1.65, 0.92, 1.50), 26, 4.0),   # cut into the night cell, lock side: his face
    (872,  V(1.72, 0.32, 1.62), V(1.70, 0.92, 1.50), 26, 4.0),   # beat 6 from the lock side: his face
    (888,  V(1.85, 0.36, 1.40), V(1.92, 0.70, 1.20), 30, 4.0),
    # beat 6  (f871) it didn't fit
    (912,  V(1.95, 0.36, 1.10), V(1.98, 0.62, 1.07), 40, 2.8),
    (936,  V(1.72, 0.25, 1.55), V(1.80, 0.85, 1.40), 26, 4.0),
    (962,  V(1.72, 0.25, 1.52), V(1.82, 0.80, 1.32), 26, 4.0),
    (977,  V(1.72, 0.40, 1.58), V(1.88, 0.93, 1.55), 26, 4.0),
    (992,  V(1.70, 0.40, 1.62), V(1.88, 0.96, 1.55), 26, 4.0),
    (1005, V(1.70, 0.40, 1.62), V(1.86, 0.97, 1.52), 26, 4.0),
    (1018, V(1.68, 0.42, 1.60), V(1.84, 0.97, 1.48), 26, 4.0),
    (1046, V(1.68, 0.42, 1.60), V(1.60, 0.95, 1.50), 26, 4.0),
    # beat 7  (f1057) another impression, waited
    (1060, V(0.95, 0.22, 1.62), V(1.30, 0.95, 1.50), 26, 4.0),   # around behind him (south, then west), never past him
    (1072, V(0.38, 0.75, 1.60), V(1.00, 0.97, 1.40), 26, 4.0),
    (1082, V(0.30, 1.55, 1.60), V(1.00, 0.97, 1.40), 24, 4.0),
    (1094, V(1.55, 1.75, 1.25), V(0.92, 1.45, 0.85), 28, 4.0),
    (1150, V(1.25, 1.76, 1.15), V(0.90, 1.45, 0.85), 35, 2.8),
    (1172, V(1.75, 1.70, 1.55), V(0.92, 1.15, 1.25), 26, 4.0),
    (1200, V(1.70, 1.10, 1.75), V(0.85, 1.75, 1.65), 24, 4.0),
    (1242, V(-1.20, -1.50, 2.30), V(0.50, 0.80, 0.60), 20, 5.6),
    (1282, V(1.45, 1.55, 1.45), V(0.40, 1.05, 1.05), 24, 4.0),
    # beat 8  (f1303) this time the key worked
    (1322, V(0.85, 1.80, 1.50), V(1.16, 1.30, 1.00), 28, 4.0),
    (1360, V(1.75, 1.90, 1.45), V(1.15, 1.10, 1.20), 26, 4.0),
    (1376, V(1.68, 1.74, 1.55), V(1.30, 0.95, 1.40), 26, 4.0),   # holds on this side and pans: no move past him
    (1398, V(1.70, 1.72, 1.65), V(1.62, 0.88, 1.40), 28, 4.0),
    (1420, V(1.70, 1.70, 1.65), V(1.85, 0.72, 1.28), 30, 4.0),
    (1438, V(1.68, 1.66, 1.65), V(1.95, 0.50, 1.35), 26, 4.0),
    # beat 9  (f1429) through every gate, out of the prison
    (1462, V(1.68, 1.64, 1.65), V(2.05, 0.45, 1.45), 26, 4.0),
    ("CUT", 1463),
    (1463, V(3.15, 0.15, 1.75), V(2.00, 0.50, 1.50), 24, 5.6),   # ahead of him in the corridor, his face
    (1480, V(3.20, 0.18, 1.75), V(2.30, 0.35, 1.50), 24, 5.6),
    (1495, V(3.90, 0.15, 1.75), V(2.90, 0.30, 1.50), 24, 4.0),
    (1518, V(4.60, 0.05, 1.70), V(3.60, 0.20, 1.55), 26, 4.0),
    (1548, V(6.00, 0.00, 1.50), V(4.90, 0.15, 1.45), 24, 4.0),
    (1582, V(7.05, -0.05, 1.15), V(5.90, 0.10, 1.45), 24, 4.0),
    (1610, V(8.00, -0.60, 1.70), V(7.20, 0.10, 1.55), 24, 5.6),   # static corner of the corridor
    (1636, V(8.00, -0.60, 1.70), V(7.45, 0.60, 1.55), 24, 5.6),
    (1645, V(8.00, -0.60, 1.70), V(7.50, 1.00, 1.50), 24, 5.6),
    ("CUT", 1646),
    # beat 10 (f1681) decades later: a yard camera off his path, craning up as he crosses
    (1646, V(6.20, 4.20, 1.90), V(7.51, 1.10, 1.50), 28, 5.6),
    (1666, V(6.20, 4.20, 1.95), V(7.53, 1.50, 1.55), 28, 5.6),
    (1692, V(6.20, 4.20, 2.20), V(7.85, 2.45, 1.55), 26, 5.6),
    (1712, V(6.30, 4.30, 3.00), V(8.20, 3.10, 1.50), 26, 5.6),
    (1732, V(6.60, 4.60, 4.00), V(8.60, 3.80, 1.45), 26, 5.6),
    (1741, V(7.00, 5.00, 5.50), V(8.80, 4.10, 1.40), 24, 5.6),
    (1748, V(4.00, 8.00, 9.00), V(2.00, 20.0, 12.0), 22, 5.6),
    (1785, V(2.60, 13.6, 7.60), V(0.00, 22.0, 2.50), 24, 5.6),
    (1812, V(2.20, 16.0, 6.20), V(0.00, 22.4, 2.80), 26, 5.6),
    (1848, V(1.60, 16.6, 3.90), V(0.00, 22.5, 2.70), 34, 5.6),
    (1890, V(1.20, 16.8, 3.55), V(0.00, 22.55, 2.75), 42, 5.6),
]
CUTS = sorted(k[1] for k in K if k[0] == "CUT")
K = [k for k in K if k[0] != "CUT"]
SEGS = []
_b = [0] + CUTS + [10**6]
for lo, hi in zip(_b, _b[1:]):
    seg = [k for k in K if lo <= k[0] < hi]
    if seg: SEGS.append((lo, hi, seg))
def _pick(f):
    for lo, hi, seg in SEGS:
        if lo <= f < hi: return seg
    return SEGS[-1][2]
_C = [(lo, hi, catmull([(k[0], k[1]) for k in seg]) if len(seg) > 1 else (lambda f, v=seg[0][1]: v.copy()),
       catmull([(k[0], k[2]) for k in seg]) if len(seg) > 1 else (lambda f, v=seg[0][2]: v.copy())) for lo, hi, seg in SEGS]
def fc0(f):
    for lo, hi, c, a in _C:
        if lo <= f < hi: return c(min(max(f, _pick(f)[0][0]), _pick(f)[-1][0]))
def fa0(f):
    for lo, hi, c, a in _C:
        if lo <= f < hi: return a(min(max(f, _pick(f)[0][0]), _pick(f)[-1][0]))
WHIP = []
def _seg(f, idx):
    for (f0, c0, a0, l0, s0), (f1, c1, a1, l1, s1) in zip(WHIP, WHIP[1:]):
        if f0 <= f <= f1:
            u = (f - f0) / float(f1 - f0); u = u * u * (3 - 2 * u)
            p0, p1 = (c0, c1) if idx == 0 else (a0, a1)
            if idx == 0 and f0 == 852:   # out through the tunnel (under its roof), then across the yard to the cell window
                pts = [p0, Vector((13.0, 6.0, 1.6)), Vector((10.2, 6.0, 1.6)), p1]
                L = [(b - a_).length for a_, b in zip(pts, pts[1:])]; d = u * sum(L)
                for (a_, b), l in zip(zip(pts, pts[1:]), L):
                    if d <= l: return a_.lerp(b, d / l)
                    d -= l
                return p1
            if idx == 1 and f0 == 852: return p0.lerp(p1, min(1.0, 3 * u))   # the view turns to the yard first
            q = p0.lerp(p1, u)   # arcs up over the yard walls
            return q
def fc(f): return fc0(f)
def fa(f): return fa0(f)
def segid(f): return sum(1 for c in CUTS if f >= c)
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
for f in range(1, 1891):
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
    for g in range(f - 12, f + 13):
        if g in OFF and segid(g) == segid(f):   # never smooth across a cut
            w = math.exp(-((g - f) / 7.0) ** 2); acc += OFF[g] * w; wsum += w
    SM[f] = acc / wsum
for f in fr:
    if SM[f].length < OFF[f].length:
        SM[f] = SM[f].normalized() * OFF[f].length if SM[f].length > 1e-6 else OFF[f]
print("CLEARANCE frames pushed", sum(1 for f in fr if OFF[f].length > 1e-4), "max", round(max(v.length for v in OFF.values()), 3), "big", [f for f in fr if OFF[f].length > 0.45][:40])
dg = bpy.context.evaluated_depsgraph_get()
nclip = 0
DIRS = [Vector(d).normalized() for d in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1),(1,1,1),(-1,-1,1),(1,-1,-1),(-1,1,-1),(1,1,-1),(-1,-1,-1),(1,-1,1),(-1,1,1))]
for f in range(1, 1891):
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
def fcurves(act):
    if hasattr(act, "fcurves") and len(act.fcurves): return list(act.fcurves)
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []): out += list(cb.fcurves)
    return out
HOLD = {c - 1 for c in CUTS}   # a cut: the key before it holds, the next frame jumps
for ob in (cam, aim, cd):
    for fc_ in fcurves(ob.animation_data.action):
        for kp in fc_.keyframe_points:
            kp.interpolation = 'CONSTANT' if int(round(kp.co.x)) in HOLD else 'LINEAR'
print("CUTS", CUTS)
# beats.json (target times; the director retimes to the VO with pipeline/retime_to_vo.py)
BEATS = [(1, 1, "He got hold of the prison's master key"), (2, 259, "making a perfect impression"), (3, 367, "The mold was smuggled out"),
         (4, 511, "and his allies used it"), (5, 685, "They hid the key inside a cake"), (6, 871, "But when he tried the key"),
         (7, 1057, "So he sent out another"), (8, 1303, "And this time, the key worked"), (9, 1429, "He passed through every locked gate"),
         (10, 1681, "Years later, he became president")]
json.dump([{"beat": b, "frame": f, "first_words": w} for b, f, w in BEATS], open(os.path.join(HERE, "..", "beats.json"), "w"), indent=1)
sc.frame_set(1)
if "L_TunnelFill" not in bpy.data.objects:   # the tunnel reads as a lit passage during the whip
    tl = bpy.data.lights.new("L_TunnelFill", 'POINT'); tl.energy = 160; tl.color = (1.0, 0.92, 0.82); tl.shadow_soft_size = 0.5
    to = bpy.data.objects.new("L_TunnelFill", tl); sc.collection.objects.link(to); to.location = (11.7, 6.0, 2.6)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("CAM saved", OUT)
