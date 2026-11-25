# 02a: seat the composer on the bench, feet on the floor, upright playing posture with breathing and sway,
# head acting (small nods to the music, the rod keeps it near), jaw open on the rod, eye darts and blinks.
R = make_human_ctrl(COMP); H = Human(R)
PB = COMP.pose.bones; BN = COMP.data.bones
add_hand_limits(COMP)
for s in "LR":                                   # wrist limits must not clamp the piano wrists (fingers are solved by hand)
    for n in _chain(s):
        for c in list(PB[n].constraints):
            if c.name == "HandLimit": PB[n].constraints.remove(c)
ROOT0 = BN["root"].head_local.copy()
SEAT_Y = 0.555
def root_at(f, dz=0.0, dy=0.0, flex=6.0, side=0.0, yaw=0.0):
    H.key_root(f, Vector((0.0, SEAT_Y + dy, ROOT_Z + dz)), yaw=yaw, flex=flex, side=side)
ROOT_Z = 0.64
FOOT = {"L": Vector((0.17, 0.07)), "R": Vector((-0.17, 0.07))}
def legs(f):
    for s in "LR": H.key_foot(s, f, FOOT[s], 0.0)
# ---- find the seat height: suit trouser seat must rest on the bench cushion (garment, not skin)
root_at(1); legs(1); H.key_spine(1, flex=8.0)
sc.frame_set(1)
SUIT_O = [c for c in COMP.children if "suit_3" in c.name][0]
def seat_bottom():
    dg = bpy.context.evaluated_depsgraph_get(); e = SUIT_O.evaluated_get(dg); me = e.to_mesh()
    z = min((SUIT_O.matrix_world @ v.co).z for v in me.vertices if abs((SUIT_O.matrix_world @ v.co).x) < 0.12 and (SUIT_O.matrix_world @ v.co).y > 0.45)
    e.to_mesh_clear(); return z
zb = seat_bottom()
BENCH_TOP_Z = 0.525
ROOT_Z += (BENCH_TOP_Z - 0.004) - zb
log("seat: trouser seat was", round(zb, 4), "-> root z", round(ROOT_Z, 4))

# ---- body acting: playing sway, breathing; bigger passion at the end. Keys every 12 frames, smooth.
random.seed(4)
def sway(f):
    t = f / 60.0
    amp = 1.0 if f < T["using"] else 1.0 + 0.6 * smoothstep((f - T["using"]) / 120.0)
    still = 1.0
    if T["into"] - 20 < f < T["using"]:            # x-ray: calmer, he concentrates (still moving, breathing)
        still = 0.45
    k = 0.45 * amp * still
    return dict(flex=7.0 + k * 2.2 * math.sin(t * 2 * math.pi / 1.8) + k * 0.8 * math.sin(t * 2 * math.pi / 3.7),
                side=k * 1.6 * math.sin(t * 2 * math.pi / 3.6 + 0.7),
                twist=k * 2.5 * math.sin(t * 2 * math.pi / 4.4 + 1.3),
                dz=0.004 * math.sin(t * 2 * math.pi / 3.9),            # breathing
                nod=k * 2.0 * math.sin(t * 2 * math.pi / 1.8 + 0.6), turn=k * 1.5 * math.sin(t * 2 * math.pi / 5.1))
def smoothstep(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
for f in range(1, END + 13, 12):
    p = sway(f)
    root_at(f, dz=p["dz"], flex=5.0, side=0.4 * p["side"])
    legs(f)
    H.key_spine(f, flex=p["flex"], twist=p["twist"], side=p["side"], head=(-6.0 + p["nod"], p["turn"]))
# ---- jaw: open just enough for the rod between the incisors (solved on the teeth mesh)
TEETH = [c for c in COMP.children if "teeth" in c.name][0]
_tg = {g.index: g.name for g in TEETH.vertex_groups}
TEETH_JAW = set()
for v in TEETH.data.vertices:
    if v.groups:
        g = max(v.groups, key=lambda g: g.weight)
        if _tg.get(g.group) == "jaw": TEETH_JAW.add(v.index)
log("teeth verts on jaw", len(TEETH_JAW), "of", len(TEETH.data.vertices))
def incisal_gap():
    sc.frame_set(1)
    dg = bpy.context.evaluated_depsgraph_get(); e = TEETH.evaluated_get(dg); me = e.to_mesh()
    Hi = Matrix.Identity(4); Mw = TEETH.matrix_world        # world space at frame 1 (head upright, facing -Y)
    nsub = len(me.vertices) == len(TEETH.data.vertices)
    up, lo_ = [], []
    for v in me.vertices:
        p = Hi @ (Mw @ v.co)
        if abs(p.x) > 0.007: continue
        (lo_ if v.index in TEETH_JAW else up).append(p)
    e.to_mesh_clear()
    yu = min(p.y for p in up); yl = min(p.y for p in lo_)
    upf = [p for p in up if p.y < yu + 0.005]; lof = [p for p in lo_ if p.y < yl + 0.005]
    zu = min(p.z for p in upf); zl = max(p.z for p in lof)
    return zu - zl, zl, zu, min(yu, yl)
JAW_OPEN = 0.0; JAW_AX = "X"
g0 = incisal_gap()[0]
R.key_rot("jaw", 1, [("X", 6.0)]); g1 = incisal_gap()[0]
JSGN = 1.0 if g1 > g0 else -1.0
log("jaw gap closed mm", round(g0 * 1000, 2), "at +6deg", round(g1 * 1000, 2), "sign", JSGN)
for it in range(14):
    R.key_rot("jaw", 1, [("X", JSGN * JAW_OPEN)])
    g, zlo, zhi, ymin = incisal_gap()
    log("jaw", round(JAW_OPEN, 2), "deg gap mm", round(g * 1000, 2))
    if abs(g - 0.0064) < 0.0003: break
    JAW_OPEN = max(0.0, JAW_OPEN + (0.0064 - g) * 600.0)
GAP = incisal_gap()
# bite point in HEAD space (between the incisal edges, 10 mm behind the front of the incisors)
sc.frame_set(1)
BITE_W1 = Vector((0.0, GAP[3] + 0.010, (GAP[1] + GAP[2]) / 2))
BITE_HEAD = (COMP.matrix_world @ PB["head"].matrix).inverted() @ BITE_W1
log("bite world f1", tuple(round(x, 4) for x in BITE_W1))
log("bite (head space)", tuple(round(x, 4) for x in BITE_HEAD))
# the jaw stays at that opening for the whole film (keys only at 1: constant)
for fc in iter_fcurves(COMP.animation_data.action):
    if 'pose.bones["jaw"]' in fc.data_path:
        for kp in list(fc.keyframe_points)[1:]: fc.keyframe_points.remove(kp)

# ---- eyes: look at the music / hands, blinks; closed in bliss on "hear clearly"
EYE_TARGETS = []
def eye_rot(f, pitch, yaw):
    for s in "LR": R.key_rot("eye." + s, f, [("X", pitch), ("Z", yaw)])
def lids(f, close):
    """upper lids down by `close` (0..1); MPFB default rig: orbicularis03 = upper lid"""
    for s in "LR":
        R.key_rot("orbicularis03." + s, f, [("X", 28.0 * close * LID_SIGN)])
        R.key_rot("orbicularis04." + s, f, [("X", -6.0 * close * LID_SIGN)])
LID_SIGN = 1.0
# sign check: closing must move the upper-lid bone tail down
sc.frame_set(1); t0 = (COMP.matrix_world @ PB["orbicularis03.L"].tail).z
R.key_rot("orbicularis03.L", 1, [("X", 20.0)]); sc.frame_set(1); t1 = (COMP.matrix_world @ PB["orbicularis03.L"].tail).z
if t1 > t0: LID_SIGN = -1.0
log("lid sign", LID_SIGN, round((t1 - t0) * 1000, 2))
lids(1, 0.0)
blinks = [40, 150, 262, 371, 470, 585, 700, 790, 890, 1120, 1240, 1355]
for b in blinks:
    lids(b - 3, 0.0); lids(b, 0.95); lids(b + 4, 0.0)
H_CLOSE0, H_CLOSE1 = T["hear"] - 6, T["using"] + 10
lids(H_CLOSE0 - 10, 0.0); lids(H_CLOSE0 + 8, 0.92); lids(H_CLOSE1 - 6, 0.92); lids(H_CLOSE1 + 8, 0.0)
EYE_SIGN = 1.0
sc.frame_set(1); e0 = (COMP.matrix_world @ PB["eye.L"].tail).z
eye_rot(1, 10, 0); sc.frame_set(1); e1 = (COMP.matrix_world @ PB["eye.L"].tail).z
if e1 > e0: EYE_SIGN = -1.0          # positive pitch below must look DOWN
log("eye sign", EYE_SIGN)
_er = eye_rot
def eye_rot(f, pitch, yaw): _er(f, -EYE_SIGN * 0.75 * pitch, yaw)
eye_rot(1, -14, 0)
for f, (p_, y_) in ((60, (-12, 4)), (120, (-20, -6)), (200, (-24, -3)), (270, (-12, 3)), (380, (-16, -4)), (500, (-13, 2)),
                     (640, (-18, -2)), (780, (-12, 3)), (900, (-14, 0)), (1080, (-18, 5)), (1200, (-24, -5)), (1320, (-12, 2)), (END, (-15, 0))):
    eye_rot(f, p_, y_)
