# 02b: the composer PLAYS. Fingers are posed by hand (no presets): every finger of both hands rests on its own white key
# in a five-finger position; for every solved frame the curl/spread of each finger is solved so that the lowest point of the
# fingertip PAD (taken from the subdivided rest mesh) sits exactly on the key's top surface (+0.3 mm), following the key down
# when it is pressed. Keys hinge at their back end. Hands shift position with a lift between phrases.
import time
t_start = time.time()
KEYO = {o.name: o for o in O if o.name.startswith(("KeyW", "KeyB"))}
WHITE = sorted([n for n in KEYO if n.startswith("KeyW")])
def wkey(i): return KEYO["KeyW%02d" % i]
PRESS = math.radians(3.6)                       # front of the key drops ~9.5 mm
KEY_LEN = 0.152; KTOPL = 0.8057 - 0.790         # key top in key-local z
def key_top_z(kobj, y_world):
    M = kobj.matrix_world
    p0 = M @ Vector((0, 0.0, KTOPL)); p1 = M @ Vector((0, KEY_LEN, KTOPL))       # hinge end, front end
    u = (y_world - p0.y) / (p1.y - p0.y) if abs(p1.y - p0.y) > 1e-6 else 0.0
    return p0.z + (p1.z - p0.z) * u

# ---------------------------------------------------------------- fingertip pads from the subdivided REST mesh
COMP.data.pose_position = 'REST'; bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get(); e = CB.evaluated_get(dg); me = e.to_mesh()
RV = [CB.matrix_world @ v.co for v in me.vertices]; e.to_mesh_clear()
COMP.data.pose_position = 'POSE'; bpy.context.view_layer.update()
def seg_d(p, h, t):
    d = t - h; u = max(-0.5, min(1.8, (p - h).dot(d) / d.length_squared)); return (p - (h + d * u)).length, u
PADS = {}
for s in "LR":
    dist = [b for b in ("finger%d-3.%s" % (k, s) for k in range(1, 6))]
    mids = ["finger%d-2.%s" % (k, s) for k in range(1, 6)]
    cand = {b: [] for b in dist}
    for v in RV:
        best = None
        for b, m in zip(dist, mids):
            h, t = BN[b].head_local, BN[b].tail_local
            d1, u = seg_d(v, h, t); d2, _ = seg_d(v, BN[m].head_local, BN[m].tail_local)
            if d1 < 0.0115 and u > 0.2 and d1 < d2 and (best is None or d1 < best[0]): best = (d1, b)
        if best: cand[best[1]].append(v)
    for b in dist:
        Mi = BN[b].matrix_local.inverted(); PADS[b] = [Mi @ v for v in cand[b]]
        log("pad verts", b, len(PADS[b]))

# ---------------------------------------------------------------- matrix FK on the hand (parents of the finger chains from the evaluated pose)
class PHand(_Hand):
    def fkm(self, rot):
        M = {}
        def mat(n):
            if n in M: return M[n]
            b = self.BN[n]; par = b.parent
            P = mat(par.name) if par.name.startswith("finger") else self.base[par.name]
            m = P @ (par.matrix_local.inverted() @ b.matrix_local) @ rot.get(n, Quaternion()).to_matrix().to_4x4()
            M[n] = m; return m
        for n in _chain(self.s): mat(n)
        return M
def pad_low(Mb, b):
    """world lowest pad point of distal bone b under armature matrix Mb (rig object at identity)"""
    best = None
    for p in PADS[b]:
        w = Mb @ p
        if best is None or w.z < best.z: best = w
    return best
def pad_centre(Mb, b):
    ps = [Mb @ p for p in PADS[b]]; zmin = min(p.z for p in ps)
    low = [p for p in ps if p.z < zmin + 0.004]
    return sum(low, Vector()) / len(low)

SIGN = {}
def finger_rot(s, k, x, signs):
    """x = (curl deg, spread deg) for fingers 2..5; thumb x = (cmc flex, cmc abduct, curl)"""
    if k == 1:
        a, b, c = x
        return {"finger1-1.%s" % s: Quaternion((1, 0, 0), math.radians(a)) @ Quaternion((0, 0, 1), math.radians(b)),
                "finger1-2.%s" % s: Quaternion((1, 0, 0), signs[1] * math.radians(c)),
                "finger1-3.%s" % s: Quaternion((1, 0, 0), signs[2] * math.radians(0.8 * c))}
    c, sp = x
    return {"finger%d-1.%s" % (k, s): Quaternion((1, 0, 0), signs[0] * math.radians(c)) @ Quaternion((0, 0, 1), math.radians(sp)),
            "finger%d-2.%s" % (k, s): Quaternion((1, 0, 0), signs[1] * math.radians(1.35 * c)),
            "finger%d-3.%s" % (k, s): Quaternion((1, 0, 0), signs[2] * math.radians(0.55 * c))}
BOUNDS = {1: ((-30, 45), (-40, 40), (0, 40)), 2: ((4, 62), (-32, 32)), 3: ((4, 62), (-15, 15)), 4: ((4, 62), (-26, 26)), 5: ((4, 80), (-46, 46))}
PREF = {1: (5.0, 0.0, 15.0), 2: (30.0, 0.0), 3: (30.0, 0.0), 4: (30.0, 0.0), 5: (30.0, 0.0)}

def solve_finger(Hh, s, k, kobj, x0, ypref=-0.026):
    b = "finger%d-3.%s" % (k, s)
    signs = SIGN[(s, k)]; lo_hi = BOUNDS[k]; pref = PREF[k]
    kx = kobj.matrix_world.translation.x
    def cost(x):
        Mb = Hh.fkm(finger_rot(s, k, x, signs))[b]
        lo = pad_low(Mb, b); pc = pad_centre(Mb, b)
        tz = key_top_z(kobj, lo.y) + 0.0003
        c = (pc.x - kx) ** 2 * 1.0 + (lo.z - tz) ** 2 * 6.0 + 0.04 * (pc.y - ypref) ** 2 + 20.0 * max(0.0, (-0.051 if k == 5 else -0.046) - pc.y) ** 2 + 20.0 * max(0.0, pc.y + 0.006) ** 2
        c += 1e-6 * sum(((xi - pi) / 30.0) ** 2 for xi, pi in zip(x, pref))
        return c, lo, pc, tz
    x = list(x0); best = cost(x)
    step = [6.0] * len(x)
    for it in range(40):
        improved = False
        for i in range(len(x)):
            for sg in (1, -1):
                y = list(x); y[i] = max(lo_hi[i][0], min(lo_hi[i][1], y[i] + sg * step[i]))
                c = cost(y)
                if c[0] < best[0] - 1e-12: best = c; x = y; improved = True
        if not improved:
            step = [v * 0.5 for v in step]
            if max(step) < 0.02: break
    _, lo, pc, tz = best
    return x, dict(dz=(lo.z - tz) * 1000, dx=(pc.x - kx) * 1000, y=pc.y)

def init_signs():
    sc.frame_set(1)
    for s in "LR":
        Hh = PHand(COMP, s); wr, d, n, a = Hh.frame()
        for k in range(1, 6):
            SIGN[(s, k)] = [_flex_sign(Hh, n, "finger%d-%d.%s" % (k, j, s)) for j in (1, 2, 3)]
    log("flex signs", SIGN)

# ---------------------------------------------------------------- the music: five-finger positions, presses, shifts
BEAT = 36
# (frame the position is taken, base white-key index). L: little finger on base .. thumb on base+4; R: thumb on base .. little on base+4
POS = {"L": [(1, 16), (360, 14), (760, 16), (1090, 15), (1260, 16)],
       "R": [(1, 29), (250, 31), (560, 29), (900, 30), (1150, 32), (1300, 30)]}
SHIFT = 16
def finger_key(s, k, base):
    return base + (5 - k if s == "L" else k - 1)
def position_at(s, f):
    cur = POS[s][0]
    for p in POS[s]:
        if f >= p[0]: cur = p
    return cur
PRESSES = {s: [] for s in "LR"}       # (finger, f_down, f_up)
def add_press(s, k, f0, hold):
    PRESSES[s].append((k, f0, f0 + 3 + hold))
for f in range(8, END - 10, BEAT * 2):                   # LH: a chord every half note, a single note on the off-beat
    add_press("L", 5, f, 50); add_press("L", 3, f, 50); add_press("L", 1, f, 50)
    add_press("L", 2, f + BEAT, 20)
MEL = [1, 3, 5, 4, 3, 2, 3, 1, 2, 4, 5, 3, 2, 1, 2, 3]
f = 14; i = 0
while f < END - 8:
    step_ = 18 if f < T["composing"] - 40 else 12
    add_press("R", MEL[i % len(MEL)], f, step_ - 7); f += step_; i += 1
def shifting(s, f):
    for (fp, base) in POS[s][1:]:
        if fp - SHIFT <= f <= fp + 2: return True
    return False
for s in "LR":                                           # drop presses that collide with a hand shift
    PRESSES[s] = [p for p in PRESSES[s] if not any(fp - SHIFT - 8 <= fr <= fp + 6 for (fp, b) in POS[s][1:] for fr in (p[1], p[2] + 4))]
    log("presses", s, len(PRESSES[s]))
# key rotation curves
KEYED = set()
for s in "LR":
    for (k, f0, f1) in PRESSES[s]:
        base = position_at(s, f0)[1]; ko = wkey(finger_key(s, k, base))
        for fr, ang in ((f0, 0.0), (f0 + 3, -PRESS), (f1, -PRESS), (f1 + 4, 0.0)):
            ko.rotation_euler.x = ang; ko.keyframe_insert("rotation_euler", index=0, frame=fr)
        KEYED.add(ko.name)
for n in KEYED:
    for fc in iter_fcurves(KEYO[n].animation_data.action):
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
def pressed(s, k, f):
    for (kk, f0, f1) in PRESSES[s]:
        if kk == k and f0 - 1 <= f <= f1 + 5: return True
    return False
def key_moving(f):
    for s in "LR":
        for (k, f0, f1) in PRESSES[s]:
            if f0 - 1 <= f <= f0 + 4 or f1 - 1 <= f <= f1 + 5: return True
    return False

# ---------------------------------------------------------------- hand placement (IK) per frame
PALM_H = 0.052; PALM_Y = {"L": -0.026, "R": -0.026}
def palm_target(s, f):
    fp_list = POS[s]
    base = position_at(s, f)[1]
    cx = wkey(finger_key(s, 3, base)).matrix_world.translation.x * 0.84 + wkey(finger_key(s, 4, base)).matrix_world.translation.x * 0.16
    lift = 0.0; x = cx
    for (fp, b) in fp_list[1:]:
        if fp - SHIFT <= f <= fp:
            prev = [p for p in fp_list if p[0] < fp][-1][1]
            px = wkey(finger_key(s, 3, prev)).matrix_world.translation.x * 0.84 + wkey(finger_key(s, 4, prev)).matrix_world.translation.x * 0.16
            u = (f - (fp - SHIFT)) / SHIFT
            x = px + (cx - px) * smoothstep(u); lift = 0.038 * math.sin(math.pi * u)
    dip = 0.0
    bob = 0.0025 * math.sin(f / 60.0 * 2 * math.pi / 1.8 + (0 if s == "L" else 1.1))
    return Vector((x, PALM_Y[s] + 0.003 * math.sin(f / 47.0), 0.8057 + PALM_H - (0.006 if s == "L" else 0.002) + lift + bob)), lift
def place(s, f):
    P, lift = palm_target(s, f)
    fd = Vector((-0.10 if s == "L" else 0.10, -1.0, -0.18)).normalized()
    place_hand(COMP, s, f, P, Vector((-0.12 if s == "L" else 0.08, 0.18, -1.0)).normalized(), fd, skin=0.0)
    sh = BN["upperarm01." + s].head_local
    pole = Vector((0.62 if s == "L" else -0.62, SEAT_Y + 0.45, 0.70))
    pb = PB["Pole_elbow." + s]; nme = "Pole_elbow." + s
    pb.location = R.rest(nme).to_3x3().inverted() @ (pole - BN[nme].head_local)
    pb.keyframe_insert("location", frame=f, group=nme)
    return lift

# ---------------------------------------------------------------- solve
init_signs()
hide_meshes = [c for c in COMP.children if c.type == 'MESH']
for c in hide_meshes: c.hide_viewport = True
SOL = {}       # (s,k) -> last x
for s in "LR":
    for k in range(1, 6): SOL[(s, k)] = [5.0, 0.0, 15.0] if k == 1 else [30.0, 0.0]
frames = []
f = 1
while f <= END:
    frames.append(f)
    f += 1 if (key_moving(f) or any(shifting(s, f) for s in "LR")) else (2 if not BLOCKING else 6)
if frames[-1] != END: frames.append(END)
worst = []
for f in frames:
    lifts = {s: place(s, f) for s in "LR"}
    sc.frame_set(f)
    for s in "LR":
        Hh = PHand(COMP, s)
        base = position_at(s, f)[1]
        for k in range(1, 6):
            ko = wkey(finger_key(s, k, base))
            if lifts[s] > 0.004:
                # in the air between positions: keep the last curl, relax slightly (no contact)
                x = SOL[(s, k)]; x = [x[0] + 3.0, x[1]] if k > 1 else x
                info = None
            else:
                x, info = solve_finger(Hh, s, k, ko, SOL[(s, k)])
                SOL[(s, k)] = x
                if abs(info["dz"]) > 0.4 or abs(info["dx"]) > 5 or not (-0.052 < info["y"] < -0.004):
                    worst.append((f, s, k, round(info["dz"], 2), round(info["dx"], 1), round(info["y"], 3), base))
            for n, q in finger_rot(s, k, x, SIGN[(s, k)]).items():
                pb = PB[n]
                if pb.rotation_quaternion.dot(q) < 0: q = -q
                pb.rotation_quaternion = q; pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
for c in hide_meshes: c.hide_viewport = False
log("hands solved frames", len(frames), "in", round(time.time() - t_start), "s; contact misses", len(worst))
import collections
log("MISS by position", collections.Counter((w_[1], w_[6]) for w_ in worst), "frames", collections.Counter((w_[1], w_[6], w_[0] // 100) for w_ in worst).most_common(12))
byf = collections.defaultdict(list)
for w_ in worst: byf[(w_[1], w_[2])].append(w_)
for kf, ws in sorted(byf.items()):
    log("MISS", kf, "n", len(ws), "min dz", min(w_[3] for w_ in ws), "max|dz|", max(abs(w_[3]) for w_ in ws), "max|dx|", max(abs(w_[4]) for w_ in ws), "y range", min(w_[5] for w_ in ws), max(w_[5] for w_ in ws))
