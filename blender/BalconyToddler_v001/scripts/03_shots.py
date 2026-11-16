# exec'd by 02_build.py: per-shot animation (1x, keyed from each shot's own start frame), cameras, markers.
CAMC = coll("CAMS"); CAMS = {}
CATCH = []          # (light obj, sid)
def F(sid, u):      # frame at fraction u of a shot
    f0, f1 = SH[sid]; return int(round(f0 + u * (f1 - f0)))
def FR(sid, sec):   # frame at `sec` seconds into a shot (1x timing), clamped to the shot
    f0, f1 = SH[sid]; return min(f1, f0 + int(round(sec * 60)))

def camera(sid, lens=35, fstop=8.0, catch=0.0):
    cd = bpy.data.cameras.new("CAM_" + sid); cd.lens = lens; cd.clip_start = 0.03
    cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop
    o = bpy.data.objects.new("CAM_" + sid, cd); CAMC.objects.link(o); CAMS[sid] = o
    if catch > 0:      # small catchlight near the lens (not seen by the camera)
        L = bpy.data.lights.new("Catch_" + sid, 'POINT'); L.shadow_soft_size = 0.03; L.energy = catch
        lo = bpy.data.objects.new("Catch_" + sid, L); CAMC.objects.link(lo); lo.parent = o; lo.location = (0.06, 0.10, 0.0)
        lo.visible_camera = False; CATCH.append((lo, sid))
    return o
def cam_key(o, f, loc, tgt, lens=None, focus=None):
    o.location = loc; o.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
    if lens: o.data.lens = lens; o.data.keyframe_insert("lens", frame=f)
    o.data.dof.focus_distance = focus if focus else (Vector(tgt) - Vector(loc)).length
    o.data.dof.keyframe_insert("focus_distance", frame=f)
def shot_cam(sid, keys, lens=35, fstop=8.0, catch=0.0):
    """keys: [(u, loc, tgt[, lens])] with u in 0..1 of the shot"""
    o = camera(sid, lens, fstop, catch)
    for k in keys:
        cam_key(o, F(sid, k[0]), k[1], k[2], k[3] if len(k) > 3 else None)
    return o

# ------------------------------------------------------------------ character helpers
def Ry(yaw): return Matrix.Rotation(R_(yaw), 3, 'Z')
def C_(n): return CAST[n]
def armlen(n):
    R = CAST[n][1]; return (R.BN["upperarm01.L"].head_local - R.BN["wrist.L"].head_local).length
def key_pole(n, s, f, P, kind="elbow"):
    R = CAST[n][1]; nm = ("Pole_elbow." if kind == "elbow" else "Pole_knee.") + s
    pb = R.PB[nm]; pb.location = R.rest(nm).to_3x3().inverted() @ (Vector(P) - R.BN[nm].head_local)
    pb.keyframe_insert("location", frame=f, group=nm)
def body(n, f, pos, yaw=0.0, flex=0.0, side=0.0, sflex=0.0, twist=0.0, sside=0.0, head=(0.0, 0.0)):
    H = CAST[n][2]; H.key_root(f, Vector(pos), yaw, flex, side); H.key_spine(f, sflex, twist, sside, head)
def feet(n, f, pos, yaw=0.0, gz=0.0, spread=1.0, fwd=(0.0, 0.0), pitch=(0.0, 0.0), lift=(0.0, 0.0)):
    H = CAST[n][2]; GZ[0] = gz
    for i, s in enumerate("LR"):
        xy = H.foot_xy(s, Vector(pos), yaw)
        off = Ry(yaw) @ Vector(((H.ankle[s].x * 0.75) * (spread - 1), -fwd[i], 0))
        H.key_foot(s, f, Vector((xy.x + off.x, xy.y + off.y)), yaw, lift[i], pitch[i])
def foot_air(n, s, f, W, yaw=0.0, pitch=0.0, knee_fwd=0.6):
    """IK foot target with the ankle at world W (no ground)"""
    R = CAST[n][1]; H = CAST[n][2]; a = H.ankle[s]
    M = Matrix.Translation(Vector(W)) @ Matrix.Rotation(R_(yaw), 4, 'Z') @ Matrix.Rotation(R_(pitch), 4, 'X') @ \
        Matrix.Translation(-a) @ R.rest("IK_foot." + s)
    R.key_world("IK_foot." + s, f, M)
    key_pole(n, s, f, Vector(W) + Vector((0, 0, 0.35)) + Ry(yaw) @ Vector((0, -knee_fwd, 0)), "knee")
def shoulder(n, s, f):
    sc.frame_set(f); rig = CAST[n][0]; return rig.matrix_world @ rig.pose.bones["upperarm01." + s].head
def bonew(n, b, f=None, tail=False):
    if f is not None: sc.frame_set(f)
    rig = CAST[n][0]; pb = rig.pose.bones[b]; return rig.matrix_world @ (pb.tail if tail else pb.head)
def hand(n, s, f, palm, normal, fdir, pole, pose="relaxed", amount=1.0, skin=0.012):
    rig = CAST[n][0]
    place_hand(rig, s, f, Vector(palm), Vector(normal).normalized(), Vector(fdir).normalized(), skin=skin)
    key_pole(n, s, f, pole); apply_pose(rig, s, pose, f, amount)
def relax(n, s, f, yaw=0.0, fwd=0.0, out=0.0, up=0.0, S=None, pose="relaxed"):
    """arm hanging relaxed with a slight elbow bend; palm toward the thigh"""
    sx = 1 if s == "L" else -1
    S = S if S is not None else shoulder(n, s, f); L = armlen(n)
    palm = S + Ry(yaw) @ Vector((sx * (0.035 + out), -0.03 - fwd, -(L * 0.90 + 0.05) + up))
    hand(n, s, f, palm, Ry(yaw) @ Vector((-sx, 0, 0)), Ry(yaw) @ Vector((0, -0.12 - fwd, -1)), S + Ry(yaw) @ Vector((sx * 0.35, 0.5, -0.3)), pose, skin=0.0)
def relax_both(n, f, yaw=0.0, **kw):
    for s in "LR": relax(n, s, f, yaw, **kw)
def stand(n, f, pos, yaw=0.0, gz=0.0, sflex=4.0, head=(0.0, 0.0), twist=0.0, arms=True, flex=0.0, side=0.0):
    body(n, f, pos, yaw, flex, side, sflex, twist, 0.0, head); feet(n, f, pos, yaw, gz)
    if arms: relax_both(n, f, yaw)
def root_z(n, gz=0.0, crouch=0.02):
    return gz + CAST[n][2].root_head.z - crouch
def sw(pos, yaw): return Vector(pos)

PARKED = {}
def park(n, f):
    k = list(CAST).index(n); P = Vector((30 + 3 * k, 30, CAST[n][2].root_head.z))
    body(n, f, P); feet(n, f, P, 0.0, 0.0)
    S0 = {s: CAST[n][1].BN["upperarm01." + s].head_local - CAST[n][2].root_head + P for s in "LR"}
    for s in "LR": relax(n, s, f, 0.0, S=S0[s])
def park_shot(n, sid):
    f0, f1 = SH[sid]; park(n, f0); park(n, f1)

def walk_arms(n, f0, f1, path, yaw_fn, stride, swing=0.16, step=4, bend=0.0, skip=()):
    """arm swing opposite to the legs (walk() puts the left foot at phase 0)"""
    frames = list(range(f0, f1 + 1)); dist = [0.0]
    for a_, b_ in zip(frames, frames[1:]): dist.append(dist[-1] + (path(b_) - path(a_)).to_2d().length)
    H = CAST[n][2]; R = CAST[n][1]; L = armlen(n)
    for i, f in enumerate(frames):
        if (i % step) and i != len(frames) - 1: continue
        ph = 2 * math.pi * dist[i] / stride; yaw = yaw_fn(f); p = path(f)
        for s, sg in (("L", -1), ("R", 1)):
            if s in skip: continue
            sx = 1 if s == "L" else -1
            S = Vector((p.x, p.y, 0)) + Vector((0, 0, root_z(n, GZ[0]))) + Ry(yaw) @ (R.BN["upperarm01." + s].head_local - H.root_head)
            a = sg * swing * math.sin(ph)
            palm = S + Ry(yaw) @ Vector((sx * 0.05, -a - 0.04 - bend * 0.5, -(L * 0.88 + 0.04) + abs(a) * 0.35 + bend * 0.4))
            hand(n, s, f, palm, Ry(yaw) @ Vector((-sx, 0, 0)), Ry(yaw) @ Vector((0, -0.25 - a - bend, -1)),
                 S + Ry(yaw) @ Vector((sx * 0.3, 0.55, -0.3)), "relaxed", skin=0.0)

def lin(a, b):
    a = Vector(a); b = Vector(b)
    def path(f, a=a, b=b): return a
    return a, b
def path_lin(f0, f1, a, b, ease=True):
    a = Vector(a); b = Vector(b)
    def p(f):
        u = (f - f0) / max(1, (f1 - f0)); u = max(0.0, min(1.0, u))
        if ease: u = u * u * (3 - 2 * u) * 0.35 + u * 0.65
        return a.lerp(b, u)
    return p

USED = {sid: set() for sid in SH}
def use(sid, *names): USED[sid].update(names)

# ------------------------------------------------------------------ the toddler
TH = CAST["Toddler"][2]
Q_HEAD = Vector((0.0, -0.025, 0.665))      # toddler-local point that rests on the bars (calibrated below)
def tod_pos(drop, x=0.0, y=SLOT_Y):
    return Vector((x, y, BAR_Z + drop)) - Q_HEAD + TH.root_head
def tod_legs(f, drop, x=0.0, y=SLOT_Y, kick=0.0, ph=0.0, bend=0.03):
    for i, s in enumerate("LR"):
        a = TH.ankle[s]; sgn = 1 if i == 0 else -1
        k = kick * math.sin(ph + (0 if i == 0 else math.pi))
        W = tod_pos(drop, x, y) - TH.root_head + Vector((a.x * 0.9, a.y - 0.02 - k, a.z + bend + abs(k) * 0.3))
        foot_air("Toddler", s, f, W, 0.0, 22 + (40 * k if kick else 0.0), 0.6)
def tod_grip(f, side_x=0.20):
    """both hands on the front edge bar beside the chin"""
    rig = CAST["Toddler"][0]; bar = BARS[2]
    for s, sx in (("L", 1), ("R", -1)):
        place_hand(rig, s, f, Vector((sx * side_x, BAR_Y[2], BAR_Z + BAR_R)), Vector((0, 0, -1)), Vector((0, -1, 0)), skin=0.010)
        apply_pose(rig, s, "flat_palm", f)
        key_pole("Toddler", s, f, Vector((sx * 0.45, SLOT_Y + 0.05, BAR_Z - 0.10)))
def tod_hang(f, drop, head=(4.0, 0.0), sflex=0.0, kick=0.0, ph=0.0, x=0.0, grip=True, side=0.0):
    body("Toddler", f, tod_pos(drop, x), 0.0, 0.0, side, sflex, 0.0, 0.0, head)
    tod_legs(f, drop, x, kick=kick, ph=ph)
    if grip: tod_grip(f)

# calibrate the stuck height: head/neck vertices (|x| < 7 cm) clear the two slot bars by 3 mm
sc.frame_set(1)
tod_hang(1, 0.0)
sc.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()
def tod_pts(names=("body", "male_casualsuit04", "short02")):
    out = []
    for ch in TOD.children:
        if ch.type == 'MESH' and any(k in ch.name for k in names):
            e = ch.evaluated_get(dg); me = e.to_mesh(); vs = [ch.matrix_world @ v.co for v in me.vertices]; out += vs
            for ed in me.edges:      # edge samples too (long hair-card edges can cross a bar between two clear vertices)
                a_, b_ = vs[ed.vertices[0]], vs[ed.vertices[1]]
                if (a_ - b_).length > 0.01: out += [a_.lerp(b_, t) for t in (0.25, 0.5, 0.75)]
            e.to_mesh_clear()
    return out
pts = []
for hd_ in ((14, 0), (4, 0), (2, 6), (3, -4), (10, 0)):
    tod_hang(1, 0.0, head=hd_); sc.frame_set(1); dg = bpy.context.evaluated_depsgraph_get()
    pts += [p for p in tod_pts(("body", "male_casualsuit04", "short02", "eyebrow", "eyelash")) if abs(p.x) < CX - 0.05 and p.z > BAR_Z - 0.10]
tod_hang(1, 0.0)
import numpy as _np
_P = _np.array([(p.y, p.z) for p in pts])
def clearance(dz, dy=0.0):
    c = 9.0
    for yb in (BAR_Y[1], BAR_Y[2]):
        c = min(c, float(_np.min(_np.hypot(_P[:, 0] + dy - yb, _P[:, 1] + dz - BAR_Z))) - BAR_R)
    return c
# smallest upward shift that clears (search from below: below the head the neck would pass, so scan down from +0.15)
best = None; bdy = 0.0
for dy in [i * 0.002 for i in range(-10, 11)]:
    for k in range(300):
        dz = 0.15 - k * 0.001
        if clearance(dz, dy) < 0.005:
            if best is None or dz + 0.001 < best: best = dz + 0.001; bdy = dy
            break
Q_HEAD.z -= best if best is not None else 0.0
Q_HEAD.y -= bdy
print("BUILD toddler slot centring dy", bdy)
print("BUILD toddler head calib dz", best, "clearance at 0", round(clearance(0.0), 4))

# ------------------------------------------------------------------ chairs and table (the tower)
TABLE = dup(PH["PH_WoodenTable_01"], "Table", (0.0, -0.80, 0.0), (0, 0, 0), 1.0, CS)
TAB_H = ray_down(TABLE, 0.0, -0.80)
print("BUILD table top", round(TAB_H, 3))
CHB_FINAL = Vector((0.0, -0.80, TAB_H))
CHB = chair("ChairTop", CHB_FINAL, R_(180))        # on the table, backrest to the street (behind the climber)
CHA = chair("ChairStep", (1.25, -0.95, 0.0), R_(-90))   # step chair beside the table
CHC = chair("ChairCarry", (5.0, -1.5, 0.0), R_(90))
CHC_END = ((-1.45, -0.95, 0.0), R_(90))      # carried in shot 12 (ends beside the table)
CH_SEAT_TOP = TAB_H + SEAT_H
BARS_N = [b.name for b in BARS]

# ================================================================== SHOTS
# ---------- 01 He slipped: legs dangle below the floor bars, kicking (camera above-front, looking down past the bars)
sid = "01"; f0, f1 = SH[sid]; use(sid, "Toddler")
for f in range(f0, f1 + 1, 6):
    u = (f - f0) / (f1 - f0)
    tod_hang(f, 0.30 - 0.02 * u, head=(14, 0), sflex=2, kick=0.06, ph=f * 0.16)
tod_hang(f1, 0.28, head=(14, 0), sflex=2, kick=0.06, ph=f1 * 0.16)
shot_cam(sid, [(0, (0.55, -2.05, 4.05), (0.0, -0.55, 2.95)), (1, (0.40, -1.95, 3.95), (0.0, -0.55, 2.90))], 32, 8, 6)

# ---------- 02 through the bars: low under the cage, the legs between the bars
sid = "02"; f0, f1 = SH[sid]; use(sid, "Toddler")
for f in range(f0, f1 + 1, 6):
    tod_hang(f, 0.28, head=(10, 0), sflex=2, kick=0.07, ph=f * 0.18)
tod_hang(f1, 0.28, head=(10, 0), sflex=2, kick=0.07, ph=f1 * 0.18)
shot_cam(sid, [(0, (0.9, -1.9, 2.55), (0.0, -0.52, 3.05)), (1, (0.75, -1.75, 2.60), (0.0, -0.52, 3.05))], 30, 8, 0)

# ---------- 03 of a second floor: wide across the street, the boy on the cage (hanging)
sid = "03"; f0, f1 = SH[sid]; use(sid, "Toddler")
for f in (f0, F(sid, 0.5), f1):
    tod_hang(f, 0.0, head=(4, 0), kick=0.03, ph=f * 0.1)
shot_cam(sid, [(0, (2.2, -9.5, 2.3), (0.0, 0.0, 3.6)), (1, (1.9, -8.6, 2.5), (0.0, 0.0, 3.5))], 32, 8)

# ---------- 04 balcony: low from the pavement, crane down
sid = "04"; f0, f1 = SH[sid]; use(sid, "Toddler")
for f in (f0, F(sid, 0.5), f1):
    tod_hang(f, 0.0, head=(4, 0), kick=0.03, ph=f * 0.1)
shot_cam(sid, [(0, (-2.6, -4.6, 4.6), (0.0, -0.4, 3.0)), (1, (-2.4, -4.4, 3.4), (0.0, -0.4, 3.1))], 30, 8)

# ---------- 05 His body fell: front of the cage, he slides down until the head stops
sid = "05"; f0, f1 = SH[sid]; use(sid, "Toddler")
drop_keys = [(0.0, 0.28), (0.25, 0.28), (0.45, 0.08), (0.53, 0.0), (0.60, 0.006), (0.70, 0.0), (1.0, 0.0)]
for u, d in drop_keys:
    f = F(sid, u); tod_hang(f, d, head=(8 if d > 0.1 else 3, 0), sflex=3, kick=0.05 if d > 0.05 else 0.02, ph=f * 0.2)
shot_cam(sid, [(0, (0.25, -2.25, 3.35), (0.0, -0.55, 3.05)), (1, (0.20, -2.05, 3.30), (0.0, -0.55, 3.05))], 35, 8, 8)

# ---------- 06 through the gap: closer, he settles, a breath, hands on the bar
sid = "06"; f0, f1 = SH[sid]; use(sid, "Toddler")
for f, hd in ((f0, (3, 0)), (F(sid, 0.5), (2, 6)), (f1, (3, -4))):
    tod_hang(f, 0.0, head=hd, kick=0.02, ph=f * 0.1)
shot_cam(sid, [(0, (-0.55, -1.75, 3.40), (0.0, -0.55, 3.10)), (1, (-0.45, -1.60, 3.38), (0.0, -0.55, 3.12))], 40, 8, 8)

# ---------- 07 But his head: close on his face above the bars (calm)
sid = "07"; f0, f1 = SH[sid]; use(sid, "Toddler")
for f, hd in ((f0, (2, -3)), (F(sid, 0.5), (3, 3)), (f1, (2, 0))):
    tod_hang(f, 0.0, head=hd, kick=0.02, ph=f * 0.1)
shot_cam(sid, [(0, (0.10, -1.95, 3.62), (0.0, -0.57, 3.25)), (1, (0.06, -1.80, 3.60), (0.0, -0.57, 3.25))], 65, 10, 10)

# ---------- 08 got stuck: 3/4 side at bar level, head resting between the two bars
sid = "08"; f0, f1 = SH[sid]; use(sid, "Toddler")
for f, hd in ((f0, (3, 0)), (F(sid, 0.5), (3, 4)), (f1, (3, 0))):
    tod_hang(f, 0.0, head=hd, kick=0.02, ph=f * 0.1)
shot_cam(sid, [(0, (1.15, -1.45, 3.62), (0.0, -0.53, 3.22)), (1, (1.05, -1.32, 3.60), (0.0, -0.53, 3.22))], 45, 9, 6)

# ---------- 09 Leaving him hanging in the air: from below/front, the whole boy under the cage, legs swaying
sid = "09"; f0, f1 = SH[sid]; use(sid, "Toddler")
for f in range(f0, f1 + 1, 10):
    tod_hang(f, 0.0, head=(5, 0), kick=0.04, ph=f * 0.08, side=1.5 * math.sin(f * 0.05))
tod_hang(f1, 0.0, head=(5, 0), kick=0.04, ph=f1 * 0.08)
shot_cam(sid, [(0, (0.9, -2.6, 1.9), (0.0, -0.53, 2.95)), (1, (0.6, -2.4, 2.0), (0.0, -0.53, 2.95))], 30, 8, 0)

# from here the boy keeps hanging (drop 0) in every street shot
def tod_static(sid, head=(4, 0)):
    use(sid, "Toddler")
    for f in (SH[sid][0], F(sid, 0.5), SH[sid][1]):
        tod_hang(f, 0.0, head=head, kick=0.025, ph=f * 0.1)

# ---------- 10 on the street: people look up, one points
sid = "10"; f0, f1 = SH[sid]; tod_static(sid); use(sid, "OldMan", "Woman", "Lady", "YoungMan")
TOD_C = Vector((0.0, -0.53, 2.95))
def look_at(n, pos, tgt, yaw):
    d = Vector(tgt) - (Vector(pos) + Vector((0, 0, 0.7)))
    ay = math.degrees(math.atan2(d.x, -d.y)) - yaw
    ay = (ay + 180) % 360 - 180
    pitch = -math.degrees(math.atan2(d.z, d.to_2d().length))
    return (max(-40, min(40, pitch)), max(-50, min(50, ay)))
crowd10 = [("OldMan", (-1.1, -2.5), 205), ("Woman", (0.4, -3.1), 170), ("Lady", (1.5, -2.3), 150), ("YoungMan", (-0.3, -3.9), 190)]
for n, (x, y), yaw in crowd10:
    pos = Vector((x, y, root_z(n)))
    for k, f in enumerate((f0, F(sid, 0.5), f1)):
        hd = look_at(n, pos, TOD_C, yaw)
        stand(n, f, pos, yaw, 0.0, sflex=-6, head=(hd[0] * 0.55, hd[1] * 0.6 + (k - 1) * 3), arms=(n != "Lady"))
    if n == "Lady":   # right arm pointing up at the boy (elbow slightly bent), left arm relaxed
        for f, ext in ((f0, 0.55), (F(sid, 0.3), 0.80), (f1, 0.82)):
            S = shoulder(n, "R", f); d = (TOD_C - S).normalized()
            hand(n, "R", f, S + d * armlen(n) * ext + Vector((0, 0, -0.05)), Vector((0, 0, 1)).cross(d).normalized() * -1, d,
                 S + Vector((-0.4, 0.2, -0.4)), "point")
            relax(n, "L", f, yaw)
shot_cam(sid, [(0, (3.6, -5.2, 1.05), (0.0, -1.6, 2.35)), (1, (3.4, -4.9, 1.1), (0.0, -1.5, 2.45))], 24, 8)

# ---------- 11 saw him: the man hurries toward the building (camera low in front, he comes at us then passes)
sid = "11"; f0, f1 = SH[sid]; tod_static(sid); use(sid, "Man")
p11 = path_lin(f0, f1, (-2.2, -7.4, 0), (-0.9, -3.4, 0), ease=False)
yaw11 = lambda f: math.degrees(math.atan2(1.3, -4.0))
TH_M = CAST["Man"][2]
TH_M.walk(p11, yaw11, f0, f1, stride=1.25, lift=0.10, bob=0.03, crouch=0.04, lean=10, step=2)
walk_arms("Man", f0, f1, p11, yaw11, 1.25, swing=0.20, bend=0.10)
shot_cam(sid, [(0, (-0.2, -2.2, 1.1), (-1.8, -6.6, 1.3)), (1, (-0.05, -2.0, 1.15), (-1.0, -3.8, 1.4))], 30, 8)

# ---------- 12 And rushed to stack: a young man carries a chair by its seat, walking along the pavement
sid = "12"; f0, f1 = SH[sid]; tod_static(sid); use(sid, "YoungMan")
p12 = path_lin(f0, f1, (4.2, -1.75, 0), (1.9, -1.75, 0), ease=False)
yaw12 = lambda f: -90.0
CAST["YoungMan"][2].walk(p12, yaw12, f0, f1, stride=1.0, lift=0.08, bob=0.025, crouch=0.04, lean=6, step=2)
walk_arms("YoungMan", f0, f1, p12, yaw12, 1.0, swing=0.16, skip=("L",))
# chair hangs from the left hand (street side) by the seat's side rail
YM_L = armlen("YoungMan")
for f in list(range(f0, f1 + 1, 4)) + [f1]:
    p = p12(f); yaw = yaw12(f)
    S = Vector((p.x, p.y, root_z("YoungMan"))) + Ry(yaw) @ (CAST["YoungMan"][1].BN["upperarm01.L"].head_local - CAST["YoungMan"][2].root_head)
    grip = S + Ry(yaw) @ Vector((0.16, -0.02, -(YM_L * 0.80)))
    # chair: seat side rail (chair local -X edge at seat height) at the grip, chair yawed so its side faces the man
    cyaw = yaw
    edge = Ry(cyaw) @ Vector((SEAT_XMIN + 0.012, 0.02, SEAT_H - 0.01))
    CHC.location = grip - edge; CHC.rotation_euler = (0, 0, R_(cyaw) + 0.03 * math.sin(f * 0.2))
    CHC.keyframe_insert("location", frame=f); CHC.keyframe_insert("rotation_euler", frame=f)
    hand("YoungMan", "L", f, grip + Ry(yaw) @ Vector((-0.012, 0, -0.03)), Ry(yaw) @ Vector((1, 0, 0)), Vector((0, 0, -1)),
         S + Ry(yaw) @ Vector((0.4, 0.4, -0.3)), "cup_hold", 1.0, skin=0.014)
cam12 = shot_cam(sid, [(0, (1.2, -4.6, 1.2), (3.6, -1.7, 0.9)), (1, (0.9, -4.4, 1.2), (2.2, -1.7, 0.9))], 30, 8)
# outside shot 12 the carried chair stands beside the table (constant)
for f in (f0 - 1, f1 + 1):
    CHC.location = CHC_END[0] if f > f0 else (5.0, -1.5, 0.0); CHC.rotation_euler = (0, 0, CHC_END[1] if f > f0 else R_(90))
    CHC.keyframe_insert("location", frame=f); CHC.keyframe_insert("rotation_euler", frame=f)

# ---------- 13 nearby chairs: the old man lowers a chair onto the table (hands on the backrest top rail)
sid = "13"; f0, f1 = SH[sid]; tod_static(sid); use(sid, "OldMan")
OM = "OldMan"; omp = Vector((0.05, -1.78, root_z(OM)))
top_local = None
_pp = [v.co for v in CHAIR_SRC.data.vertices]
_top = max(p.z for p in _pp); _rail = [p for p in _pp if p.z > _top - 0.05]
RAIL_Y = sum(p.y for p in _rail) / len(_rail); RAIL_X = max(p.x for p in _rail)
def rail_pt(ch, sx, f):
    sc.frame_set(f); return ch.matrix_world @ Vector((sx * RAIL_X * 0.55, RAIL_Y, _top - 0.012))
for u, dz in ((0.0, 0.16), (0.2, 0.15), (0.65, 0.0), (1.0, 0.0)):
    f = F(sid, u); CHB.location = CHB_FINAL + Vector((0, -0.05 * dz, dz)); CHB.keyframe_insert("location", frame=f)
    CHB.rotation_euler = (0, 0, R_(180)); CHB.keyframe_insert("rotation_euler", frame=f)
    lean = 6 + 14 * (0.16 - dz) / 0.16
    body(OM, f, omp - Vector((0, 0, 0.03 + 0.10 * (0.16 - dz))), 180, 6, 0, lean, 0, 0, (-14, 0))
    feet(OM, f, omp, 180, 0.0)
    for s, sx in (("L", -1), ("R", 1)):
        P = rail_pt(CHB, sx, f)
        hand(OM, s, f, P, Vector((0, 0, -1)), Vector((0, 1, -0.6)), shoulder(OM, s, f) + Vector((sx * -0.45, -0.3, -0.3)), "cup_hold", 1.0, skin=0.03)
shot_cam(sid, [(0, (2.5, -3.3, 1.55), (0.1, -1.2, 1.25)), (1, (2.35, -3.15, 1.55), (0.1, -1.2, 1.25))], 26, 8, 0)

# ---------- 14 into a tower: the woman steadies the tower (hand on the top chair's backrest) and looks up
sid = "14"; f0, f1 = SH[sid]; tod_static(sid); use(sid, "Woman")
WP = Vector((0.45, -1.42, root_z("Woman")))
for k, f in enumerate((f0, F(sid, 0.5), f1)):
    hd = look_at("Woman", WP, TOD_C, 228)
    body("Woman", f, WP, 228, 0, 0, 2, 0, 0, (hd[0] * 0.5, hd[1] * 0.5 - 5 + 5 * k))
    feet("Woman", f, WP, 228, 0.0)
    P = rail_pt(CHB, 1, f)
    hand("Woman", "R", f, P, Vector((0, 0, -1)), Vector((-0.6, 1, -0.5)), shoulder("Woman", "R", f) + Ry(228) @ Vector((-0.45, 0.2, -0.35)), "cup_hold", 1.0, skin=0.02)
    relax("Woman", "L", f, 228)
shot_cam(sid, [(0, (1.95, -2.45, 1.0), (0.15, -1.1, 1.7)), (1, (1.85, -2.35, 1.05), (0.1, -1.0, 1.85))], 26, 8)

# ---------- 15 Then one man: he steps to the tower, hand on the step chair's backrest, looks up
sid = "15"; f0, f1 = SH[sid]; tod_static(sid); use(sid, "Man")
p15 = path_lin(f0, F(sid, 0.6), (1.6, -2.6, 0), (1.25, -1.60, 0))
yaw15 = lambda f: 200.0
CAST["Man"][2].walk(p15, yaw15, f0, F(sid, 0.6), stride=0.8, lift=0.07, bob=0.02, lean=4, step=2)
walk_arms("Man", f0, F(sid, 0.6), p15, yaw15, 0.8, swing=0.12)
mp = Vector((1.25, -1.60, root_z("Man")))
for f, hd in ((F(sid, 0.6) + 2, (-20, 0)), (f1, (-32, 10))):
    stand("Man", f, mp, 215, 0.0, sflex=-3, head=hd)
shot_cam(sid, [(0, (1.85, -0.40, 1.35), (1.3, -1.9, 1.45)), (1, (1.80, -0.40, 1.30), (1.2, -1.7, 1.6))], 26, 8)

# ---------- 16 climbed up: low angle, he rises from a crouch on the top chair, arms coming up
sid = "16"; f0, f1 = SH[sid]; tod_static(sid); use(sid, "Man")
MANP = Vector((0.0, -0.92, 0.0))            # standing point on the top chair seat (feet)
def man_on_top(f, crouch, armsup, head=(-25, 0), reach=None):
    n = "Man"; rz = CH_SEAT_TOP + CAST[n][2].root_head.z - 0.02 - crouch
    body(n, f, (MANP.x, MANP.y + 0.02 + crouch * 0.05, rz), 180, 4 + crouch * 55, 0, 6 + crouch * 30 - armsup * 8, 0, 0, head)
    feet(n, f, (MANP.x, MANP.y, rz), 180, CH_SEAT_TOP + 0.006)
    if reach is None:
        for s in "LR":
            if armsup <= 0: relax(n, s, f, 180)
            else:
                S = shoulder(n, s, f); sx = 1 if s == "L" else -1
                palm = S + Ry(180) @ Vector((sx * 0.06, -0.25 * armsup, 0.45 * armsup - 0.35 * (1 - armsup)))
                hand(n, s, f, palm, Ry(180) @ Vector((-sx, -0.3, 0)), Ry(180) @ Vector((0, -0.4, 1)), S + Ry(180) @ Vector((sx * 0.5, 0.2, -0.3)), "relaxed")
for f, cr, au, hd in ((f0, 0.24, 0.0, (-15, 0)), (F(sid, 0.35), 0.20, 0.0, (-25, 0)), (F(sid, 0.75), 0.04, 0.3, (-35, 0)), (f1, 0.0, 0.45, (-38, 0))):
    man_on_top(f, cr, au, hd)
shot_cam(sid, [(0, (2.2, -2.2, 0.6), (0.0, -0.8, 2.0)), (1, (2.1, -2.05, 0.65), (0.0, -0.8, 2.3))], 26, 8)

# ---------- 18 the boy's legs / Holding: his hands round the boy's shins (static proxy of the legs to close the fingers on)
def tod_hold_pose(f, lift=0.015, hd=(3, 0)):
    tod_hang(f, lift, head=hd, kick=0.0)
def legs_proxy(f):
    sc.frame_set(f); dg_ = bpy.context.evaluated_depsgraph_get(); bm = bmesh.new()
    for ch in TOD.children:
        if ch.type == 'MESH' and any(k in ch.name for k in ("casualsuit", "body")):
            e = ch.evaluated_get(dg_); me = e.to_mesh(); bm.from_mesh(me); e.to_mesh_clear()
            bmesh.ops.transform(bm, matrix=ch.matrix_world, verts=[v for v in bm.verts if not v.tag])
            for v in bm.verts: v.tag = True
    me = bpy.data.meshes.new("LegsProxy"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("LegsProxy_%d" % f, me); coll("PROXY").objects.link(o); o.hide_render = True; return o
def man_hold(f, hd=(-40, 0), breathe=0.0):
    n = "Man"; rz = CH_SEAT_TOP + CAST[n][2].root_head.z - 0.02
    body(n, f, (MANP.x, MANP.y + 0.02, rz - breathe * 0.01), 180, 3, 0, 4, 0, 0, hd)
    feet(n, f, (MANP.x, MANP.y, rz), 180, CH_SEAT_TOP + 0.006)
    prox = PROX.get("p")
    for s, tsx in (("L", -1), ("R", 1)):     # man's left hand (world -X) on the boy's right shin (world -X)
        knee = bonew("Toddler", "lowerleg01." + ("R" if tsx < 0 else "L"), f)
        ank = bonew("Toddler", "foot." + ("R" if tsx < 0 else "L"), f)
        C = knee.lerp(ank, 0.55) + Vector((0, -0.032, 0))
        grip_object(CAST[n][0], s, f, prox, C, Vector((0, 1, 0)), Vector((-tsx, 0, 0.0)))
        S = shoulder(n, s, f); key_pole(n, s, f, S + Vector((tsx * 0.45, -0.25, -0.25)))
PROX = {}
sid = "17"; use(sid, "Man", "Toddler")
sid = "18"; use(sid, "Man", "Toddler")
sid = "19"; use(sid, "Man", "Toddler")
sid = "20"; use(sid, "Man", "Toddler")
fA = SH["17"][0]
for s_ in ("17", "18", "19", "20"):
    for f in (SH[s_][0], F(s_, 0.5), SH[s_][1]):
        tod_hold_pose(f, 0.0 if s_ == "17" else 0.015)
PROX["p"] = legs_proxy(SH["19"][0])
# 17 and grabbed: close on his face looking up, arms rising toward the legs
sid = "17"; f0, f1 = SH[sid]
for f, au, hd in ((f0, 0.45, (-38, 0)), (F(sid, 0.5), 0.75, (-42, 4)), (f1, 0.95, (-42, 0))):
    man_on_top(f, 0.0, au, hd)
shot_cam(sid, [(0, (0.42, -0.14, 2.12), (0.0, -0.88, 2.52)), (1, (0.40, -0.16, 2.15), (0.0, -0.88, 2.55))], 28, 8, 6)
for s_ in ("18", "19", "20"):
    for k, f in enumerate((SH[s_][0], F(s_, 0.5), SH[s_][1])):
        man_hold(f, (-42, 3 * (k - 1)), breathe=k % 2)
# 18: from below between the man and the wall, looking up: his hands on the shins, the boy above
sid = "18"; shot_cam(sid, [(0, (0.75, -1.45, 1.75), (0.0, -0.55, 2.80)), (1, (0.68, -1.38, 1.80), (0.0, -0.55, 2.85))], 24, 8, 0)
# 19: close on the boy, calm, lifted a little (neck free)
sid = "19"; shot_cam(sid, [(0, (-0.30, -1.75, 3.62), (0.0, -0.56, 3.26)), (1, (-0.22, -1.62, 3.60), (0.0, -0.56, 3.26))], 55, 9, 8)
# 20: close on the man's hand (watch) on the shin
sid = "20"; shot_cam(sid, [(0, (-0.95, -0.70, 2.95), (0.0, -0.62, 2.68)), (1, (-0.88, -0.68, 2.93), (0.0, -0.62, 2.68))], 38, 9, 0)

# ---------- 21 Until the boy's: outside the cage at head height, the boy's head in front, grandma at the far door
GM = "Grandma"
sid = "21"; f0, f1 = SH[sid]; use(sid, "Toddler", "Grandma", "Man")
for f in (f0, F(sid, 0.5), f1):
    tod_hold_pose(f, 0.015, (3, 0)); man_hold(f)
p21 = path_lin(f0, f1, (AD_X0 + 0.45, HY + 0.9, 0), (AD_X0 + 0.55, HY - 0.25, 0), ease=False)
yaw21 = lambda f: 0.0
GZ[0] = FLOOR2
CAST[GM][2].walk(p21, yaw21, f0, f1, stride=0.62, lift=0.06, bob=0.015, lean=8, step=2)
walk_arms(GM, f0, f1, p21, yaw21, 0.62, swing=0.10, bend=0.05)
for f in range(f0, f1 + 1, 2):
    pass
shot_cam(sid, [(0, (0.15, 0.75, FLOOR2 + 1.45), (AD_X0 + 0.45, HY, FLOOR2 + 1.15)), (1, (0.12, 0.90, FLOOR2 + 1.45), (AD_X0 + 0.5, HY - 0.2, FLOOR2 + 1.15))], 26, 8, 4)

# ---------- 22 got inside: inside the room, grandma comes through the doorway
sid = "22"; f0, f1 = SH[sid]; use(sid, "Grandma", "Toddler", "Man")
for f in (f0, F(sid, 0.5), f1):
    tod_hold_pose(f, 0.015, (3, 0)); man_hold(f)
p22 = path_lin(f0, f1, (AD_X0 + 0.5, HY + 0.3, 0), (AD_X0 + 0.9, HY - 1.4, 0), ease=False)
yaw22 = lambda f: 13.0
GZ[0] = FLOOR2
CAST[GM][2].walk(p22, yaw22, f0, f1, stride=0.66, lift=0.06, bob=0.015, lean=8, step=2)
walk_arms(GM, f0, f1, p22, yaw22, 0.66, swing=0.11, bend=0.05)
shot_cam(sid, [(0, (0.3, 1.3, FLOOR2 + 1.35), (AD_X0 + 0.5, HY, FLOOR2 + 1.3)), (1, (0.3, 1.15, FLOOR2 + 1.35), (AD_X0 + 0.8, HY - 1.2, FLOOR2 + 1.3))], 30, 8, 6)

# ---------- 23 the apartment: grandma hurries toward the balcony (camera backs off in front of her)
sid = "23"; f0, f1 = SH[sid]; use(sid, "Grandma", "Toddler", "Man")
for f in (f0, F(sid, 0.5), f1):
    tod_hold_pose(f, 0.015, (3, 0)); man_hold(f)
p23 = path_lin(f0, f1, (-0.65, 3.1, 0), (-0.15, 1.35, 0), ease=False)
yaw23 = lambda f: 16.0
GZ[0] = FLOOR2
CAST[GM][2].walk(p23, yaw23, f0, f1, stride=0.66, lift=0.06, bob=0.015, lean=10, step=2)
walk_arms(GM, f0, f1, p23, yaw23, 0.66, swing=0.11, bend=0.05)
shot_cam(sid, [(0, (0.15, 0.75, FLOOR2 + 1.45), (-0.55, 3.0, FLOOR2 + 1.3)), (1, (0.12, 0.45, FLOOR2 + 1.45), (-0.2, 1.4, FLOOR2 + 1.3))], 28, 8, 6)

# ---------- 24 And pulled: grandma kneels on the slab and lifts him under the arms (camera outside, front)
def kneel(n, f, knee_y, lean, x=0.0, head=(0.0, 0.0), gz=FLOOR2):
    """kneeling upright on both knees at y=knee_y (facing -Y), torso leaning forward `lean` deg"""
    R = CAST[n][1]; H = CAST[n][2]
    thigh = (R.BN["upperleg01.L"].head_local - R.BN["lowerleg01.L"].head_local).length
    shin = (R.BN["lowerleg01.L"].head_local - R.BN["foot.L"].head_local).length
    rz = gz + 0.14 + thigh * 0.97 + (H.root_head.z - R.BN["upperleg01.L"].head_local.z)
    body(n, f, (x, knee_y + 0.03, rz), 0.0, lean * 0.45, 0, lean * 0.55, 0, 0, head)
    for s in "LR":
        a = H.ankle[s]
        foot_air(n, s, f, Vector((x + a.x * 0.85, knee_y + shin * 0.95, gz + 0.095)), 0.0, 165, 0.6)
def gma_hands_on_tod(f, out=0.072, up=0.0):
    """palms on the boy's chest sides just under the armpits, fingers forward"""
    sp = bonew("Toddler", "spine02", f); sp2 = bonew("Toddler", "spine03", f)
    for s, sx in (("L", 1), ("R", -1)):          # grandma's left hand (world +X) on the boy's left side (+X)
        P = sp.lerp(sp2, 0.5) + Vector((sx * out, 0.01, up))
        S = shoulder(GM, s, f)
        hand(GM, s, f, P, Vector((-sx, 0, 0)), Vector((0, -1, 0.15)), S + Vector((sx * 0.55, 0.10, -0.45)), "cup_hold", skin=0.004)
def tod_lift(f, drop, y, arms_out=0.75):
    body("Toddler", f, tod_pos(drop, 0.0, y), 0.0, 0.0, 0.0, -2, 0.0, 0.0, (-4, 0))
    tod_legs(f, drop, 0.0, y, kick=0.0, bend=0.015)
    for s, sx in (("L", 1), ("R", -1)):
        S = shoulder("Toddler", s, f)
        hand("Toddler", s, f, S + Vector((sx * 0.20 * arms_out, -0.06, 0.04)), Vector((0, 0, -1)), Vector((sx, -0.3, 0.2)),
             S + Vector((sx * 0.2, 0.3, -0.2)), "relaxed", skin=0.0)
sid = "24"; f0, f1 = SH[sid]; use(sid, "Toddler", "Grandma")
for u, d, y, ln in ((0.0, 0.64, SLOT_Y, 44), (0.25, 0.65, SLOT_Y, 42), (0.65, 0.72, SLOT_Y, 36), (0.85, 0.73, SLOT_Y + 0.06, 34), (1.0, 0.73, SLOT_Y + 0.09, 33)):
    f = F(sid, u)
    tod_lift(f, d, y)
    kneel(GM, f, -0.02, ln, head=(-6, 22))
    gma_hands_on_tod(f)
shot_cam(sid, [(0, (0.40, -1.85, 3.98), (0.0, -0.35, 3.70)), (1, (0.34, -1.75, 4.00), (0.0, -0.30, 3.78))], 32, 8, 8)

# ---------- 25/26 the toddler back up / completely unharmed: he stands on the slab, grandma kneels behind, hands at his sides
TODP = Vector((0.0, -0.10, 0.0))
def tod_stand(f, head=(0.0, 0.0), twist=0.0):
    pos = Vector((TODP.x, TODP.y, FLOOR2 + TH.root_head.z + 0.008))
    body("Toddler", f, pos, 0.0, 0.0, 0.0, 2, twist, 0.0, head); feet("Toddler", f, pos, 0.0, FLOOR2 + 0.018)
    relax_both("Toddler", f, 0.0, out=0.02)
for sid in ("25", "26"):
    use(sid, "Toddler", "Grandma")
sid = "25"; f0, f1 = SH[sid]
for f, hd, ln in ((f0, (-4, 0), 22), (F(sid, 0.5), (-2, -6), 20), (f1, (-6, 4), 18)):
    tod_stand(f, hd); kneel(GM, f, 0.22, ln, head=(14, 0)); gma_hands_on_tod(f, 0.074, -0.01)
shot_cam(sid, [(0, (0.55, -1.80, 4.02), (0.0, -0.05, 3.85)), (1, (0.45, -1.65, 4.02), (0.0, -0.05, 3.88))], 30, 8, 8)
sid = "26"; f0, f1 = SH[sid]
for f, hd, tw, ln, gh in ((f0, (-6, 0), 0, 18, (14, 0)), (F(sid, 0.4), (-24, 18), 8, 20, (24, 8)), (F(sid, 0.7), (-26, 20), 10, 21, (26, 10)), (f1, (-22, 16), 8, 20, (24, 8))):
    tod_stand(f, hd, tw); kneel(GM, f, 0.22, ln, head=gh); gma_hands_on_tod(f, 0.074, -0.01)
shot_cam(sid, [(0, (0.15, -1.75, 4.02), (0.0, -0.05, 3.95)), (1, (0.10, -1.45, 4.02), (0.0, -0.05, 3.98))], 38, 8, 8)

# ------------------------------------------------------------------ park everyone not used in a shot
for sid in SH:
    for n in CAST:
        if n not in USED[sid]: park_shot(n, sid)
# the top chair sits on the table from shot 13 on; before that it waits beside the shop (constant)
CHB.location = (3.6, -1.0, 0.0); CHB.rotation_euler = (0, 0, R_(200))
for f in (1, SH["13"][0] - 1):
    CHB.keyframe_insert("location", frame=f); CHB.keyframe_insert("rotation_euler", frame=f)
for ob in (CHB, CHC):
    for fc in ob.animation_data.action.fcurves if hasattr(ob.animation_data.action, "fcurves") else []:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
# table: only from shot 10 on in place (before that it stands at the cafe door further along)
TABLE.location = (3.9, -1.2, 0.0); TABLE.keyframe_insert("location", frame=1); TABLE.keyframe_insert("location", frame=SH["13"][0] - 1)
TABLE.location = (0.0, -0.80, 0.0); TABLE.keyframe_insert("location", frame=SH["13"][0])

# catchlights: on only during their own shot
for lo, sid in CATCH:
    e = lo.data.energy; f0, f1 = SH[sid]
    for f, v in ((1, 0.0), (f0 - 1, 0.0), (f0, e), (f1, e), (f1 + 1, 0.0)):
        if f >= 1: lo.data.energy = v; lo.data.keyframe_insert("energy", frame=f)
# markers (hard cuts)
for sid, (f0, f1) in SH.items():
    mk = sc.timeline_markers.new("S" + sid, frame=f0); mk.camera = CAMS[sid]
sc.camera = CAMS["01"]
