# PrisonKeyCake v011 stage B part 2 (exec'd by 02_animate.py): the story, keyed in time order.
UPTO = int(args[1]) if len(args) > 1 else END

def lerpv(a, b, u): return Vector(a).lerp(Vector(b), u)
def KM(pos, xdir, zup=(0, 0, 1)):
    X = Vector(xdir).normalized(); Z = Vector(zup); Z = (Z - X * Z.dot(X)).normalized(); Y = Z.cross(X)
    M = Matrix((X, Y, Z)).transposed().to_4x4(); M.translation = Vector(pos); return M
def pchip_keys(keys):
    """keys: [(f, value)] -> f(x) monotone cubic"""
    return pchip(keys)
def interp_mats(keys, f):
    """keys [(frame, Matrix)] -> slerp/lerp between neighbours (smoothstep)"""
    if f <= keys[0][0]: return keys[0][1]
    if f >= keys[-1][0]: return keys[-1][1]
    for (f0, M0), (f1, M1) in zip(keys, keys[1:]):
        if f0 <= f <= f1:
            u = smoothstep((f - f0) / (f1 - f0))
            l0, q0, _ = M0.decompose(); l1, q1, _ = M1.decompose()
            if q0.dot(q1) < 0: q1 = -q1
            M = q0.slerp(q1, u).to_matrix().to_4x4(); M.translation = l0.lerp(l1, u); return M

def seat_snap(H, ctrl, f, pos, yaw, trousers, seat_top, xy, r=0.12, flex=0.0):
    z = pos[2]
    for _ in range(4):
        seat_root(H, ctrl, f, (pos[0], pos[1], z), yaw, flex=flex); fs(f)
        low = min(p[1].z for p in eval_points(trousers) if (p[1].to_2d() - Vector(xy)).length < r)
        z += (seat_top + 0.004) - low
    seat_root(H, ctrl, f, (pos[0], pos[1], z), yaw, flex=flex)
    log("seat snapped", ctrl.o.name, f, round(z, 4)); return z

# ==================================================================================== S1  CELL, NIGHT (1-340)
# He sits on the stool facing -Y, presses the brass master key flat into the wax tin with his index finger on the shaft.
STOOL_TOP = 0.47
P_SEAT = Vector((-0.45, 0.90, 0.56))
fs(1)
PZ = seat_snap(HP, PR, 1, P_SEAT, 0.0, O["Pris.trousers"], STOOL_TOP, (-0.45, 0.88))
P_SEAT.z = PZ
FEET_S = {"L": Vector((-0.33, 0.47, PR.BN["foot.L"].head_local.z)), "R": Vector((-0.57, 0.47, PR.BN["foot.R"].head_local.z))}

def pris_seated(f0, f1, flexf, twistf=lambda f: 0.0, step=10, seat=None):
    seat = seat or P_SEAT
    for f in list(range(f0, f1, step)) + [f1]:
        br = 1.2 * math.sin(2 * math.pi * f / 210.0)
        seat_root(HP, PR, f, seat, 0.0, flex=flexf(f) * 0.35)
        key_spine(PR, f, flex=flexf(f) * 0.65 + br, twist=twistf(f))
        plant_feet(PR, f, FEET_S, 0.0)

flex1 = pchip([(1, 6.0), (90, 8.0), (125, 17.0), (205, 18.0), (240, 12.0), (300, 9.0), (340, 9.0)])
pris_seated(1, 340, flex1, twistf=pchip([(1, -4.0), (120, -6.0), (240, -5.0), (340, -3.0)]))

# choose the tin heading that the seated right hand reaches naturally (wrist limits), so the key lies flat in its imprint
best = None
for yd in range(-100, 1, 10):
    for t_ in (TIN1, TIN2): t_.rotation_euler = (0, 0, math.radians(yd))
    upd()
    Kt = TIN1.matrix_world @ Matrix.Translation((-0.045, 0.0, 0.016 + 0.0042 - 0.0035))
    e, a_ = key_prop_hand(PR, "R", 138, Kt, R_PRESS_P, pose="point", pole=Vector((-0.95, 0.95, 0.85)))
    if best is None or a_ + e * 300 < best[0]: best = (a_ + e * 300, yd, e, a_)
for t_ in (TIN1, TIN2): t_.rotation_euler = (0, 0, math.radians(best[1]))
upd(); log("tin yaw chosen", best)
TIN_W = TIN1.matrix_world.copy()
K_PRESS = TIN_W @ Matrix.Translation((-0.045, 0.0, 0.016 + 0.0042 - 0.0035))
UP = Vector((0, 0, 1))
KEYS_S1 = [
    (1,   KM((-0.50, 0.60, 1.01), (0.55, -0.60, 0.55), (0.25, 0.2, 1))),
    (45,  KM((-0.49, 0.59, 1.03), (0.72, -0.52, 0.45), (0.2, 0.25, 1))),
    (85,  KM((-0.50, 0.55, 0.94), (0.70, -0.68, 0.20))),
    (115, Matrix.Translation((0, 0, 0.030)) @ K_PRESS),
    (128, Matrix.Translation((0, 0, 0.004)) @ K_PRESS),
    (138, K_PRESS),
    (205, K_PRESS),
    (222, Matrix.Translation((0, 0, 0.022)) @ K_PRESS),
    (262, KM((-0.53, 0.62, 0.99), (0.55, -0.62, 0.50), (0.2, 0.2, 1))),
    (340, KM((-0.54, 0.63, 1.01), (0.58, -0.60, 0.50), (0.2, 0.2, 1))),
]
for f in sorted(set(list(range(1, 341, 6)) + [k[0] for k in KEYS_S1])):
    Kw = interp_mats(KEYS_S1, f)
    if 138 <= f <= 205: Kw = Matrix.Translation((0, 0, -0.0004 * math.sin((f - 138) / 9.0))) @ Kw   # small press rock
    key_prop_hand(PR, "R", f, Kw, R_PRESS_P, pose="point", pole=Vector((-0.95, 0.95, 0.85)))
# the key IN the hand from frame 1 (Child Of the wrist)
fs(1); MKEY.matrix_world = interp_mats(KEYS_S1, 1) if False else W(PRIS, "wrist.R") @ R_PRESS_P
key_basis(MKEY, 0, MKEY.matrix_world.copy()); own(MKEY, 1, PRIS, "wrist.R")
# on contact the key settles flat into the wax under the fingertip (static), then is gripped again for the lift
own(MKEY, 129)
key_basis(MKEY, 138, K_PRESS); key_basis(MKEY, 209, K_PRESS); set_interp(MKEY, 'BEZIER')
own(MKEY, 210, PRIS, "wrist.R")
# wax imprint (one shape key, R5) as the key sinks
sk = WAX1.data.shape_keys.key_blocks["imprint"]
for f, v in ((1, 0.0), (126, 0.0), (138, 1.0)):
    sk.value = v; sk.keyframe_insert("value", frame=f)
# left hand: flat on the table, beside the tin (R2)
for f in (1, 60, 120, 200, 260, 340):
    dy = 0.01 * math.sin(f / 50.0)
    surface_hand(PR, "L", f, Vector((-0.22, 0.30 + dy, 0.76)), Vector((0.25, -1, 0)), pose="relaxed",
                 pole=Vector((0.15, 0.95, 0.75)))
# head + face
for f, tgt in ((1, "key"), (30, "key"), (48, (1.5, 0.6, 1.1)), (70, (1.5, 0.6, 1.1)), (88, "key"), (110, "tin"), (200, "tin"), (240, "tin"), (300, "tin"), (340, "tin")):
    fs(f)
    T_ = (MKEY.matrix_world @ Vector((0.04, 0, 0))) if tgt == "key" else (TIN1.matrix_world.translation + Vector((0, 0, 0.02))) if tgt == "tin" else Vector(tgt)
    look_at(PR, f, T_, blend=0.9)
for f, sm, br in ((1, 0.15, -0.2), (60, 0.0, -0.5), (110, 0.1, -0.4), (200, 0.2, -0.3), (250, 0.55, 0.3), (330, 0.6, 0.3)):
    key_face(PRIS, f, smile=sm, brow=br)
saccades(PR, 1, 340, every=45, amp=(2, 3), seed=3)
blinks(PRIS, [32, 150, 228, 310])
log("S1 done")

# ---------------------------------------------------------------- shared helpers for the later beats
def path_fn(pts):
    """pts [(f, (x, y))] -> f -> Vector (monotone cubic per axis)"""
    fx = pchip([(f, p[0]) for f, p in pts]); fy = pchip([(f, p[1]) for f, p in pts])
    return lambda f: Vector((fx(f), fy(f), 0.0))
def yaw_from_path(path, f0, f1, end_yaw=None, look=6):
    def yf(f):
        a = path(max(f0, f - look)); b = path(min(f1, f + look)); d = b - a
        if d.length < 0.02:
            return end_yaw if end_yaw is not None else 0.0
        return math.degrees(math.atan2(d.x, -d.y))
    return yf
def cut(rig, f):
    """a hidden relocation between f and f+1: hold f, no overshoot from f+1 on"""
    ad = rig.animation_data
    for fc in iter_fcurves(ad.action):
        for kp in fc.keyframe_points:
            if abs(kp.co.x - f) < 0.5: kp.interpolation = 'CONSTANT'
            if abs(kp.co.x - (f + 1)) < 0.5: kp.handle_left_type = kp.handle_right_type = 'VECTOR'
        fc.update()
def walk_arms(ctrl, path, f0, f1, stride=0.7, sides="LR", amp=0.10, step=4):
    d = 0.0; prev = path(f0)
    for f in range(f0, f1 + 1):
        p = path(f); d += (p - prev).length; prev = p
        if (f - f0) % step and f != f1: continue
        ph = 2 * math.pi * d / (2 * stride)
        for s_ in sides:
            sg = 1 if s_ == "L" else -1
            hang_hand(ctrl, s_, f, swing=amp * math.sin(ph) * sg * -1, bend=0.12)
def idle_stand(H, ctrl, f0, f1, pos, yaw, flex=3.0, step=12, sway=0.006, seed=0):
    for f in list(range(f0, f1, step)) + [f1]:
        br = math.sin(2 * math.pi * f / 200.0 + seed)
        stand(H, ctrl, f, pos + Vector((sway * math.sin(f / 37.0 + seed), 0, 0)), yaw, flex=flex + 0.8 * br)
def ktween(keys, f):
    return interp_mats(keys, f)
def actual_rel(rig, s, obj, f):
    fs(f); return W(rig, "wrist." + s).inverted() @ obj.matrix_world

# MasterKey goes back onto the table after S1 (hidden by the flame void), lying flat
own(MKEY, 343)
MK_TABLE = KM((-0.18, 0.22, 0.76 + 0.0042), (0.8, -0.6, 0))
key_basis(MKEY, 344, MK_TABLE); set_interp(MKEY, 'CONSTANT')
# the right hand comes down to rest on the table edge (off camera from 343)
surface_hand(PR, "R", 344, Vector((-0.62, 0.42, 0.76)), Vector((0.3, -1, 0)), pole=Vector((-1.0, 1.0, 0.7)))
vis(TIN1, 1, True); vis(TIN1, 343, False); vis(WAX1, 1, True); vis(WAX1, 343, False)
vis(TIN2, 1, False); vis(TIN2, 1030, True); vis(WAX2, 1, False); vis(WAX2, 1030, True)

# ==================================================================================== S2  LANE, DUSK (341-560): the visitor smuggles the mould out
VPATH = path_fn([(330, (5.55, 0.72)), (345, (5.85, 0.74)), (470, (9.30, 0.86)), (520, (10.25, 1.08)), (552, (10.72, 1.20)), (565, (10.80, 1.21))])
V_END = Vector((10.80, 1.21, 0)); V_YAW = 29.0
vy = yaw_from_path(VPATH, 330, 565, end_yaw=V_YAW)
def vyaw(f):
    if f >= 548: u = smoothstep((f - 548) / 22.0); return vy(548) * (1 - u) + V_YAW * u
    return vy(f)
fs(330); HV.walk(VPATH, vyaw, 330, 566, stride=0.68, lift=0.07, bob=0.018, lean=4.0)
walk_arms(VR, VPATH, 330, 566, sides="L", amp=0.09)
# right hand carries the basket (wrap grip on the handle), arm hanging with a small swing
for f in range(330, 567, 4):
    hang_hand(VR, "R", f, swing=0.02 * math.sin(f / 9.0), bend=0.18, pose="wrap_grip", out=0.05)
fs(330); BASKET.matrix_world = W(VIS, "wrist.R") @ R_WRAP_V; key_basis(BASKET, 329, BASKET.matrix_world.copy())
own(BASKET, 330, VIS, "wrist.R")
idle_stand(HV, VR, 568, 805, V_END, V_YAW, flex=2.0, seed=1.0)
for f in range(568, 806, 12):
    hang_hand(VR, "R", f, swing=0.0, bend=0.2, pose="wrap_grip", out=0.05)
    hang_hand(VR, "L", f, swing=0.02, bend=0.15)
for f, tgt in ((330, (8.0, 0.0, 1.5)), (372, (8.0, 0.2, 1.5)), (392, (5.3, 0.8, 1.6)), (418, (5.3, 0.8, 1.6)), (438, (9.3, 0.9, 1.6)),
               (520, (11.4, 0.4, 1.1)), (575, (11.45, 0.05, 1.0)), (640, (11.45, 0.05, 1.0)), (700, (11.25, 0.62, 1.0)),
               (750, (10.75, 0.30, 1.6)), (775, (11.25, 0.62, 1.0)), (805, (11.25, 0.62, 1.0))):
    fs(f); look_at(VR, f, Vector(tgt), blend=0.85)
for f, sm, br in ((330, 0.0, -0.4), (400, 0.0, 0.3), (560, 0.1, 0.4), (700, 0.4, 0.3), (760, 0.6, 0.4), (805, 0.5, 0.3)):
    key_face(VIS, f, smile=sm, brow=br)
saccades(VR, 330, 805, every=40, seed=5); blinks(VIS, [360, 455, 590, 690, 770])
log("S2 done")

# ==================================================================================== S3  WORKSHOP (480-800): the pour, the copy, the cake
S_POS = Vector((10.80, 0.22, 0)); S_YAW = 90.0
idle_stand(HS, SR, 1, 805, S_POS, S_YAW, flex=11.0, seed=2.0)
for f in range(1, 806, 12):
    look_at(SR, f, Vector((11.40, 0.05, 0.98)) if f < 690 else Vector((11.25, 0.62, 0.98)), blend=0.8)
PIVOT = CRUC.matrix_world.translation.copy()
def cruc_angle(f): return pchip([(1, 0.0), (535, 0.0), (560, -18.0), (575, -34.0), (605, -34.0), (628, 0.0), (900, 0.0)])(f)
for f in range(1, 806, 3):
    CRUC.rotation_euler = (0, math.radians(cruc_angle(f)), 0); CRUC.keyframe_insert("rotation_euler", frame=f)
set_interp(CRUC, 'LINEAR')
GRIP_LOCAL = Vector((-0.36, 0.12, 0.0))
def grip_w(f):
    fs(f); return CRUC.matrix_world @ GRIP_LOCAL
# right hand on the lever grip (wrap), palm down; before/after: resting on the bench edge
for f in range(470, 650, 3):
    g = grip_w(f)
    if 515 <= f <= 632:
        apply_pose(SMITH, "R", "wrap_grip", f)
        place_hand(SMITH, "R", f, g + Vector((0, 0, 0.024)), Vector((0, 0, -1)), Vector((0.2, -1, 0)), skin=0.0)
        key_pole(SR, "R", f, Vector((10.6, -0.4, 0.9)))
    else:
        surface_hand(SR, "R", f, Vector((11.05, 0.05, 0.91)), Vector((1, -0.2, 0)), pole=Vector((10.6, -0.4, 0.8)))
for f in (1, 300, 469, 650, 805):
    surface_hand(SR, "R", f, Vector((11.05, 0.05, 0.91)), Vector((1, -0.2, 0)), pole=Vector((10.6, -0.4, 0.8)))
# the hot metal: KEY1 appears in the cavity as the stream fills it, glows, then cools to steel
vis(KEY1, 1, False); vis(KEY1, 572, True)
em = [n for n in bpy.data.materials["M_KeyCopy1"].node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0].inputs["Emission Strength"]
for f, v in ((1, 0.0), (571, 0.0), (572, 2.2), (612, 2.0), (660, 0.6), (690, 0.0)):
    em.default_value = v; em.keyframe_insert("default_value", frame=f)
LIP_LOCAL = Vector((-0.10, 0.0, -0.025))
SPRUE = Vector((11.43, 0.03, 0.985))
vis(STREAM, 1, False); vis(STREAM, 566, True); vis(STREAM, 612, False)
for f in range(560, 616):
    fs(f); lip = CRUC.matrix_world @ LIP_LOCAL; d = SPRUE - lip
    STREAM.location = lip; STREAM.rotation_mode = 'QUATERNION'; STREAM.rotation_quaternion = (-d).to_track_quat('Z', 'Y')
    STREAM.scale = (1, 1, d.length)
    for k in ("location", "rotation_quaternion", "scale"): STREAM.keyframe_insert(k, frame=f)
# left hand: on the bench while pouring, then pinches the cooled key from the mould and pushes it into the cake
for f in (1, 300, 560, 640, 700, 760, 805):
    surface_hand(SR, "L", f, Vector((11.06, 0.55, 0.91)), Vector((1, 0.2, 0)), pole=Vector((10.7, 0.9, 0.8)))
K_MOULD = KEY1.matrix_world.copy()
K_IN_WS = CAKE_WS.matrix_world @ Matrix([list(r) for r in sc["KEY_IN_CAKE"]])
K_PRE = Matrix.Translation(K_IN_WS.to_3x3() @ Vector((-0.07, 0, 0))) @ K_IN_WS
K_LIFT = Matrix.Translation((0, 0, 0.10)) @ K_MOULD
PL = Vector((10.80, -0.45, 0.85))
for f in (640,):
    surface_hand(SR, "R", f, Vector((11.05, 0.02, 0.91)), Vector((1, -0.2, 0)), pole=PL)
def pinch_pt(rig, s_):
    return (Wt(rig, "finger1-3." + s_) + Wt(rig, "finger2-3." + s_)) / 2
def reach(ctrl, s_, f, P, fdir, palm, pose="pinch", pole=None, it=6):
    rig = ctrl.o
    apply_pose(rig, s_, pose, f)
    place_hand(rig, s_, f, Vector(P) - Vector(fdir).normalized() * 0.07, Vector(palm), Vector(fdir), skin=0.0)
    if pole is not None: key_pole(ctrl, s_, f, pole)
    pb = rig.pose.bones["IK_hand." + s_]; Rr = rig.data.bones["IK_hand." + s_].matrix_local.to_3x3().inverted()
    for _ in range(it):
        fs(f); err = Vector(P) - pinch_pt(rig, s_)
        if err.length < 0.0008: break
        pb.location = pb.location + Rr @ err; pb.keyframe_insert("location", frame=f, group=pb.name)
    fs(f); e = (Vector(P) - pinch_pt(rig, s_)).length
    if e > 0.005: log("REACH_ERR", rig.name, s_, f, round(e * 1000, 1))
def bow(M): return M @ Vector((0.011, 0, 0))
FD, PALM = Vector((0.55, 0.15, -0.8)), Vector((0.2, 0.25, -1.0))
for f, Kw in ((652, Matrix.Translation((0, 0, 0.05)) @ K_MOULD), (668, Matrix.Translation((0, 0, 0.004)) @ K_MOULD), (674, K_MOULD)):
    reach(SR, "R", f, bow(Kw), FD, PALM, pole=PL)
own(KEY1, 675, SMITH, "wrist.R")
for f, P in ((690, bow(K_LIFT)), (712, Vector((11.06, 0.47, 1.00)))):
    reach(SR, "R", f, P, Vector((1, 0.1, -0.2)), Vector((0, -0.3, -1)), pole=PL)
own(KEY1, 723)
key_basis(KEY1, 748, K_IN_WS); set_interp(KEY1, 'BEZIER')
for f in (723, 735, 748):
    fs(f); P = KEY1.matrix_world @ Vector((0.011, 0, 0))
    reach(SR, "R", f, P, Vector((1, 0.1, -0.2)), Vector((0, -0.3, -1)), pole=PL)
for f in (768, 805):
    surface_hand(SR, "R", f, Vector((11.05, 0.02, 0.91)), Vector((1, -0.2, 0)), pose="relaxed", pole=PL)
for f, sm, br in ((1, 0.0, -0.5), (560, 0.0, -0.6), (640, 0.2, 0.0), (700, 0.3, 0.2), (760, 0.6, 0.4), (805, 0.5, 0.3)):
    key_face(SMITH, f, smile=sm, brow=br)
saccades(SR, 480, 805, every=45, seed=7); blinks(SMITH, [500, 630, 720, 790])
# the key travels with the cake: from 800 it lies in the cut cake on the cell shelf (same cake-relative pose)
K_IN_C = CAKE_C.matrix_world @ (CAKE_WS.matrix_world.inverted() @ K_IN_WS)
key_basis(KEY1, 799, K_IN_WS); key_basis(KEY1, 800, K_IN_C)
for fc in iter_fcurves(KEY1.animation_data.action):
    for kp in fc.keyframe_points:
        if abs(kp.co.x - 799) < 0.5: kp.interpolation = 'CONSTANT'
log("S3 done")

# ==================================================================================== S4  CELL (800-1060): the cake arrives, the key doesn't fit
P_SH = Vector((0.83, -0.30, 0)); P_DOOR = Vector((0.98, 0.30, 0))
def pris_stand_path(f):
    return P_SH if f <= 905 else P_SH.lerp(P_DOOR, smoothstep((f - 905) / 40.0))
idle_stand(HP, PR, 800, 905, P_SH, 90.0, flex=5.0, seed=0.5)
# a short sidestep to the door (two steps), then standing at the lock
for f in range(905, 950, 2):
    p = pris_stand_path(f); u = (f - 905) / 45.0
    HP.key_root(f, Vector((p.x, p.y, HP.root_head.z - 0.015 - 0.012 * math.sin(u * 2 * math.pi))), yaw=90.0, flex=5.0)
for s_, f0, f1 in (("R", 905, 925), ("L", 922, 945)):
    a = PR.BN["foot." + s_].head_local; lat = -0.11 if s_ == "R" else 0.11   # facing +X: right foot at -Y
    p0 = Vector((P_SH.x + 0.02, P_SH.y + lat, a.z)); p1 = Vector((P_DOOR.x + 0.02, P_DOOR.y + lat, a.z))
    for f in range(f0, f1 + 1, 2):
        u = smoothstep((f - f0) / (f1 - f0)); q = p0.lerp(p1, u) + Vector((0, 0, 0.05 * math.sin(u * math.pi)))
        M = Matrix.Translation(q) @ Matrix.Rotation(math.radians(90), 4, 'Z') @ Matrix.Translation(-a) @ PR.rest("IK_foot." + s_)
        PR.key_world("IK_foot." + s_, f, M)
    other = "L" if s_ == "R" else "R"
idle_stand(HP, PR, 950, 1060, P_DOOR, 90.0, flex=4.0, seed=0.9)
# hand the cut-out key out of the cake
K1_OUT = Matrix.Translation(K_IN_C.to_3x3() @ Vector((-0.08, 0, 0))) @ K_IN_C
K_LOCK_IN = KM((1.4795 - 0.040, 0.34, 1.05), (1, 0, 0), (0, 1, 0))
K_LOCK_PRE = Matrix.Translation((-0.07, 0, 0)) @ K_LOCK_IN
K_LOOK = KM((1.00, -0.02, 1.32), (0.6, -0.2, 0.5), (0.2, 1, 0))
PRP = Vector((0.6, -0.9, 0.8))
for f in (800, 830):
    surface_hand(PR, "R", f, Vector((0.84, -0.47, 0.95)) if False else Vector((1.20, -0.55, 0.95)), Vector((1, 0.2, 0)), pole=PRP)
for f, Kw in ((852, Matrix.Translation(K_IN_C.to_3x3() @ Vector((-0.05, 0, 0.03))) @ K_IN_C), (866, K_IN_C)):
    key_prop_hand(PR, "R", f, Kw, R_PINCH_P, pose="pinch", pole=PRP)
own(KEY1, 867, PRIS, "wrist.R")
R_K1P = actual_rel(PRIS, "R", KEY1, 867)
for f, Kw in ((882, K1_OUT), (905, K_LOOK), (925, K_LOOK), (950, K_LOCK_PRE), (958, K_LOCK_PRE)):
    key_prop_hand(PR, "R", f, Kw, R_K1P, pose="pinch", pole=Vector((0.6, -0.3, 0.7)))
own(KEY1, 959)
def jam(f):   # tries to turn it: it jams twice
    return pchip([(959, 0.0), (970, 0.0), (978, 14.0), (984, -4.0), (991, 15.0), (998, -5.0), (1004, 12.0), (1010, 0.0)])(f)
for f in range(959, 1011, 3):
    Kw = Matrix.Translation(K_LOCK_IN.translation) @ Matrix.Rotation(math.radians(jam(f)), 4, Vector((1, 0, 0))) @ \
        Matrix.Translation(-K_LOCK_IN.translation) @ (K_LOCK_IN if f >= 970 else interp_mats([(959, K_LOCK_PRE), (970, K_LOCK_IN)], f))
    key_basis(KEY1, f, Kw)
    key_prop_hand(PR, "R", f, Kw, R_K1P, pose="pinch", pole=Vector((0.6, -0.3, 0.7)), search=False)
set_interp(KEY1, 'BEZIER')
own(KEY1, 1012, PRIS, "wrist.R")
for f, Kw in ((1026, K_LOCK_PRE), (1045, KM((1.22, 0.22, 1.08), (0.9, -0.1, -0.3), (0.1, 1, 0)))):
    key_prop_hand(PR, "R", f, Kw, R_K1P, pose="pinch", pole=Vector((0.6, -0.3, 0.7)))
key_prop_hand(PR, "R", 1060, KM((1.20, 0.20, 1.02), (0.9, -0.1, -0.4), (0.1, 1, 0)), R_K1P, pose="pinch", pole=Vector((0.6, -0.3, 0.7)))
for f in (800, 900, 1000, 1060):
    hang_hand(PR, "L", f, bend=0.15, swing=0.02)
for f, tgt in ((800, (1.33, -0.32, 1.0)), (850, (1.30, -0.36, 0.98)), (890, "k"), (925, "k"), (940, (1.48, 0.34, 1.05)), (1008, (1.48, 0.34, 1.05)),
               (1020, (1.48, 0.30, 1.4)), (1040, (1.2, 0.2, 0.7)), (1060, (1.1, 0.0, 0.8))):
    fs(f); look_at(PR, f, (KEY1.matrix_world.translation if tgt == "k" else Vector(tgt)), blend=0.85)
for f, sm, br in ((800, 0.5, 0.4), (860, 0.6, 0.5), (905, 0.7, 0.5), (960, 0.2, -0.3), (985, -0.2, -0.8), (1010, -0.4, -1.0), (1060, -0.3, -0.9)):
    key_face(PRIS, f, smile=sm, brow=br)
saccades(PR, 800, 1060, every=45, seed=8); blinks(PRIS, [818, 935, 1030])
vis(KEY1, 1062, False)
log("S4 done")

# ==================================================================================== S6  CELL (1062-1235): another impression, waiting all night
cut(PRIS, 1061)
pris_seated(1062, 1236, pchip([(1062, 14.0), (1100, 17.0), (1150, 15.0), (1175, 2.0), (1236, 0.0)]),
            twistf=pchip([(1062, -5.0), (1236, -2.0)]))
own(MKEY, 1063, PRIS, "wrist.R") if False else None
fs(1066); K_START2 = Matrix.Translation((0, 0, 0.05)) @ K_PRESS
key_prop_hand(PR, "R", 1062, K_START2, R_PRESS_P, pose="point", pole=Vector((-0.95, 0.95, 0.85)))
fs(1062); key_basis(MKEY, 1061, MK_TABLE); key_basis(MKEY, 1062, W(PRIS, "wrist.R") @ R_PRESS_P)
for fc in iter_fcurves(MKEY.animation_data.action):
    for kp in fc.keyframe_points:
        if abs(kp.co.x - 1061) < 0.5: kp.interpolation = 'CONSTANT'
own(MKEY, 1063, PRIS, "wrist.R")
for f, Kw in ((1085, Matrix.Translation((0, 0, 0.012)) @ K_PRESS), (1094, Matrix.Translation((0, 0, 0.002)) @ K_PRESS)):
    key_prop_hand(PR, "R", f, Kw, R_PRESS_P, pose="point", pole=Vector((-0.95, 0.95, 0.85)))
own(MKEY, 1095); key_basis(MKEY, 1104, K_PRESS); key_basis(MKEY, 1140, K_PRESS); set_interp(MKEY, 'BEZIER')
for f in (1104, 1120, 1140):
    key_prop_hand(PR, "R", f, K_PRESS, R_PRESS_P, pose="point", pole=Vector((-0.95, 0.95, 0.85)))
own(MKEY, 1141, PRIS, "wrist.R")
sk2 = WAX2.data.shape_keys.key_blocks["imprint"]
for f, v in ((1, 0.0), (1093, 0.0), (1104, 1.0)):
    sk2.value = v; sk2.keyframe_insert("value", frame=f)
# he sets the master key down beside the tin and leans back to wait
key_prop_hand(PR, "R", 1160, Matrix.Translation((0, 0, 0.04)) @ MK_TABLE, R_PRESS_P, pose="point", pole=Vector((-0.95, 0.95, 0.85)))
key_prop_hand(PR, "R", 1172, Matrix.Translation((0, 0, 0.001)) @ MK_TABLE, R_PRESS_P, pose="point", pole=Vector((-0.95, 0.95, 0.85)))
own(MKEY, 1173); key_basis(MKEY, 1180, MK_TABLE); set_interp(MKEY, 'BEZIER')
for f in (1195, 1236):
    surface_hand(PR, "R", f, Vector((-0.60, 0.48, 0.76)), Vector((0.4, -1, 0)), pole=Vector((-1.0, 1.0, 0.7)))
for f in (1062, 1120, 1180, 1236):
    surface_hand(PR, "L", f, Vector((-0.22, 0.32, 0.76)), Vector((0.25, -1, 0)), pole=Vector((0.15, 0.95, 0.75)))
for f, tgt in ((1062, "tin"), (1140, "tin"), (1170, (0.0, 0.3, 0.8)), (1190, (1.4, 0.6, 1.2)), (1215, (1.4, 0.6, 1.2)), (1236, (1.3, -0.3, 1.0))):
    fs(f); look_at(PR, f, (TIN2.matrix_world.translation if tgt == "tin" else Vector(tgt)), blend=0.85)
for f, sm, br in ((1062, 0.0, -0.4), (1110, 0.3, -0.1), (1170, 0.1, 0.0), (1236, 0.3, 0.3)):
    key_face(PRIS, f, smile=sm, brow=br)
saccades(PR, 1062, 1236, every=40, seed=9); blinks(PRIS, [1075, 1150, 1205])
# the candle burns down, the window turns from night to dawn
for f, sz in ((1, 1.0), (1070, 1.0), (1225, 0.38), (END, 0.38)):
    CAND.scale = (1, 1, sz); CAND.keyframe_insert("scale", frame=f)
    WICK.location.z = 0.79 + 0.14 * sz; WICK.keyframe_insert("location", frame=f)
vis(CAKE_C, 1, True); vis(CAKE_C, 1180, False); vis(CAKE_C2, 1, False); vis(CAKE_C2, 1180, True)
log("S6 done")

# ==================================================================================== S7  (1236-1340): the second key turns
cut(PRIS, 1236)
idle_stand(HP, PR, 1237, 1338, P_DOOR, 90.0, flex=4.0, seed=1.3)
vis(KEY2, 1, False); vis(KEY2, 1237, True)
def turn(f): return pchip([(1237, 0.0), (1292, 0.0), (1318, 50.0), (1400, 50.0)])(f)
def k2_lock(f, ang):
    return Matrix.Translation(K_LOCK_IN.translation) @ Matrix.Rotation(math.radians(ang), 4, Vector((1, 0, 0))) @ Matrix.Translation(-K_LOCK_IN.translation) @ K_LOCK_IN
own(KEY2, 1237)
for f in range(1237, 1328, 3):
    Kw = k2_lock(f, turn(f)); key_basis(KEY2, f, Kw)
    key_prop_hand(PR, "R", f, Kw, R_K1P, pose="pinch", pole=Vector((0.6, -0.3, 0.7)), search=(f == 1237))
set_interp(KEY2, 'BEZIER')
BOLT = O["DoorBolt"]
for f, dy in ((1, 0.0), (1320, 0.0), (1328, 0.05)):
    BOLT.location.y = dy if False else BOLT.location.y; 
fs(1); b0 = BOLT.location.copy()
for f, dy in ((1, 0.0), (1320, 0.0), (1328, 0.05)):
    BOLT.location = b0 + BOLT.matrix_parent_inverse.to_3x3().inverted() @ Vector((0, dy, 0)) if False else b0 + Vector((0, dy, 0))
    BOLT.keyframe_insert("location", frame=f)
for f, sm, br in ((1237, 0.0, -0.4), (1300, 0.1, -0.2), (1327, 0.8, 0.8), (1338, 0.8, 0.6)):
    key_face(PRIS, f, smile=sm, brow=br)
for f in (1237, 1300, 1330):
    hang_hand(PR, "L", f, bend=0.2, swing=0.03)
for f, tgt in ((1237, (1.48, 0.34, 1.05)), (1320, (1.48, 0.34, 1.05)), (1338, (1.5, 0.7, 1.5))):
    fs(f); look_at(PR, f, Vector(tgt), blend=0.85)
blinks(PRIS, [1260])
log("S7 done")

# ==================================================================================== S8  (1338-1622): every gate, and out
def door_pt(obj, local_rest_world, f):
    """a point fixed on a hinged object, given in world at rest (frame 1)"""
    fs(1); L = obj.matrix_world.inverted() @ Vector(local_rest_world); fs(f); return obj.matrix_world @ L
# pull the key out, then the left hand pushes the door open
own(KEY2, 1338, PRIS, "wrist.R")
for f, Kw in ((1348, Matrix.Translation((-0.07, 0, 0)) @ k2_lock(1348, 50.0)),):
    key_prop_hand(PR, "R", f, Kw, R_K1P, pose="pinch", pole=Vector((0.6, -0.3, 0.7)))
for f, ang in ((1, 0.0), (1346, 0.0), (1392, 100.0), (END, 100.0)):
    DOOR.rotation_euler = (0, 0, math.radians(ang)); DOOR.keyframe_insert("rotation_euler", frame=f)
for f, ang in ((1, 0.0), (1456, 0.0), (1500, 75.0), (END, 75.0)):
    GATE1.rotation_euler = (0, 0, math.radians(ang)); GATE1.keyframe_insert("rotation_euler", frame=f)
for f, ang in ((1, 85.0), (470, 85.0), (500, 0.0), (1543, 0.0), (1585, 92.0), (END, 92.0)):
    WICKET.rotation_euler = (0, 0, math.radians(ang)); WICKET.keyframe_insert("rotation_euler", frame=f)
def push(ctrl, s_, obj, p_rest, f0, f1, nrm=(1, 0, 0)):
    for f in range(f0, f1 + 1, 3):
        P = door_pt(obj, p_rest, f)
        fs(f); n_ = (obj.matrix_world.to_3x3() @ Vector(nrm)).normalized()
        surface_hand(ctrl, s_, f, P, Vector((0, 0, 1)).cross(n_) * (1 if s_ == "L" else -1) + Vector((0, 0, 0.6)), pose="relaxed",
                     skin=0.012, normal=n_)
push(PR, "L", DOOR, (1.53, 0.36, 1.15), 1340, 1360)
# walk to gate 1
G_POS = Vector((2.02, 0.12, 0))
WP1 = path_fn([(1362, (0.98, 0.30)), (1380, (1.30, 0.52)), (1396, (1.72, 0.58)), (1414, (2.02, 0.14)), (1418, (2.02, 0.12))])
HP.walk(WP1, yaw_from_path(WP1, 1362, 1418, end_yaw=90.0), 1362, 1418, stride=0.6, lift=0.07, bob=0.015, lean=4.0)
idle_stand(HP, PR, 1420, 1478, G_POS, 90.0, flex=4.0, step=10, seed=2.2)
walk_arms(PR, WP1, 1362, 1418, sides="L", amp=0.08)
for f in range(1362, 1408, 4):
    fs(f); key_prop_hand(PR, "R", f, W(PRIS, "wrist.R") @ R_K1P, R_K1P, search=False) if False else hang_hand(PR, "R", f, bend=0.25, pose="pinch")
K_G_IN = KM((2.535 - 0.040, 0.02, 1.05), (1, 0, 0), (0, 1, 0)); K_G_PRE = Matrix.Translation((-0.07, 0, 0)) @ K_G_IN
def kg(f, ang): return Matrix.Translation(K_G_IN.translation) @ Matrix.Rotation(math.radians(ang), 4, Vector((1, 0, 0))) @ Matrix.Translation(-K_G_IN.translation) @ K_G_IN
key_prop_hand(PR, "R", 1412, K_G_PRE, R_K1P, pose="pinch", pole=Vector((1.7, -0.5, 0.7)))
own(KEY2, 1419)
gturn = pchip([(1419, 0.0), (1430, 0.0), (1442, 50.0), (1452, 50.0)])
for f in range(1419, 1453, 3):
    Kw = kg(f, gturn(f)) if f >= 1428 else interp_mats([(1419, K_G_PRE), (1428, K_G_IN)], f)
    key_basis(KEY2, f, Kw); key_prop_hand(PR, "R", f, Kw, R_K1P, pose="pinch", pole=Vector((1.7, -0.5, 0.7)), search=(f == 1419))
set_interp(KEY2, 'BEZIER')
own(KEY2, 1453, PRIS, "wrist.R")
key_prop_hand(PR, "R", 1460, Matrix.Translation((-0.08, 0, -0.05)) @ kg(1460, 50.0), R_K1P, pose="pinch", pole=Vector((1.7, -0.5, 0.7)))
push(PR, "L", GATE1, (2.585, 0.36, 1.12), 1452, 1474)
# through the corridor to the wicket
WP2 = path_fn([(1478, (2.02, 0.12)), (1500, (2.55, 0.32)), (1522, (3.35, 0.55)), (1544, (4.15, 0.64)), (1556, (4.62, 0.66)), (1560, (4.66, 0.66))])
HP.walk(WP2, yaw_from_path(WP2, 1478, 1560, end_yaw=90.0), 1478, 1560, stride=0.66, lift=0.07, bob=0.018, lean=5.0)
walk_arms(PR, WP2, 1478, 1540, sides="LR", amp=0.10)
push(PR, "L", WICKET, (5.265, 0.42, 1.10), 1543, 1556)
for f in range(1542, 1600, 4): hang_hand(PR, "R", f, bend=0.25, pose="pinch")
WP3 = path_fn([(1560, (4.66, 0.66)), (1576, (5.05, 0.70)), (1594, (5.70, 0.66)), (1610, (6.15, 0.60)), (1622, (6.25, 0.58))])
HP.walk(WP3, yaw_from_path(WP3, 1560, 1622, end_yaw=80.0), 1560, 1622, stride=0.66, lift=0.07, bob=0.018, lean=3.0)
walk_arms(PR, WP3, 1560, 1622, sides="L", amp=0.08)
for f in range(1600, 1623, 4): hang_hand(PR, "R", f, bend=0.25, pose="pinch")
# looks back at the prison over his shoulder, then smiles at the open sky
for f, tgt in ((1340, (1.6, 0.6, 1.3)), (1366, (0.6, -0.4, 1.6)), (1398, (0.6, -0.4, 1.6)), (1408, (2.53, 0.02, 1.05)), (1412, (2.53, 0.02, 1.05)), (1450, (2.53, 0.02, 1.05)), (1470, (3.5, 0.6, 1.6)),
               (1540, (5.27, 0.6, 1.4)), (1560, (6.5, 0.5, 1.8)), (1576, (3.5, -0.4, 1.7)), (1614, (3.0, -0.4, 1.7)), (1622, (3.0, -0.4, 1.7))):
    fs(f); look_at(PR, f, Vector(tgt), blend=0.9, limit=(95, 45))
for f in range(1570, 1623, 6):
    key_spine(PR, f, flex=2.0, twist=-22.0 * smoothstep((f - 1568) / 14.0))
for f, sm, br in ((1340, 0.7, 0.6), (1420, 0.2, -0.2), (1450, 0.6, 0.4), (1540, 0.4, 0.2), (1600, 0.8, 0.6), (1622, 0.9, 0.6)):
    key_face(PRIS, f, smile=sm, brow=br)
saccades(PR, 1340, 1622, every=50, seed=10); blinks(PRIS, [1375, 1488, 1570])
vis(KEY2, 1623, False); vis(BASKET, 1, True); vis(BASKET, 1623, False)
log("S8 done")

# ==================================================================================== S9  STEPS, YEARS LATER (1623-1836)
SXX = 40.0
cut(PRIS, 1622); cut(VIS, 1622); cut(SMITH, 1622)
P_TOPS = Vector((SXX, 2.75, 0.85))
idle_stand(HP, PR, 1623, END, P_TOPS, 0.0, flex=1.0, step=10, seed=0.3)
def wave(ctrl, H, s_, f0, f1, f_down, f_end, per=34):
    rig = ctrl.o; sg = 1 if s_ == "L" else -1
    for f in list(range(f0, f_down, 3)) + [f_down]:
        fs(f); sh = Wh(rig, "upperarm01." + s_)
        fwd = (Wh(rig, "eye.L") + Wh(rig, "eye.R")) / 2 - Wh(rig, "head"); fwd.z = 0; fwd.normalize()
        lat = Vector((-fwd.y, fwd.x, 0)) * sg
        up = smoothstep((f - f0) / 22.0)
        osc = math.sin(2 * math.pi * (f - f0) / per) * 0.11 * smoothstep((f - f0 - 15) / 10.0) * (1 - smoothstep((f - f_down + 25) / 20.0))
        Wp = sh.lerp(sh + lat * 0.22 + fwd * 0.10 + Vector((0, 0, 0.30)), up) + lat * osc
        d = (Vector((0, 0, 1)) * up + Vector((0, 0, -1)) * (1 - up) + lat * osc * 2).normalized()
        apply_pose(rig, s_, "flat_palm" if up > 0.5 else "relaxed", f)
        H.key_hand(s_, f, Wp, d, fwd, pole=sh + lat * 0.45 + Vector((0, 0, -0.35)) - fwd * 0.2)
    for f in (f_down + 40, f_end):
        hang_hand(ctrl, s_, f, bend=0.15)
wave(PR, HP, "R", 1640, 1790, 1765, END)
for f in (1623, 1700, END): hang_hand(PR, "L", f, bend=0.15)
for f, tgt in ((1623, (SXX, -3.0, 1.6)), (1700, (SXX - 0.8, -2.0, 1.4)), (1760, (SXX + 0.8, -2.0, 1.4)), (1800, (SXX, -3.5, 1.5)), (1818, (SXX, -3.5, 1.2)), (1828, (SXX, -3.5, 1.6)), (END, (SXX, -3.5, 1.6))):
    fs(f); look_at(PR, f, Vector(tgt), blend=0.9)
for f, sm, br in ((1623, 0.8, 0.6), (1700, 0.9, 0.7), (1800, 0.8, 0.5), (END, 0.9, 0.6)):
    key_face(PRIS, f, smile=sm, brow=br)
blinks(PRIS, [1660, 1745])            # no blink after 1760: the film ends on an open-eyed nod
saccades(PR, 1623, 1790, every=50, seed=11)
for rig, ctrl, H, pos, yaw, s_ in ((VIS, VR, HV, Vector((SXX - 0.95, 3.05, 0.85)), -12.0, "L"), (SMITH, SR, HS, Vector((SXX + 1.00, 3.05, 0.85)), 12.0, "R")):
    idle_stand(H, ctrl, 1623, END, pos, yaw, flex=-2.0, step=10, seed=pos.x)
    wave(ctrl, H, s_, 1650 if rig is VIS else 1665, 1800, 1790 if rig is VIS else 1770, END, per=30)
    other = "R" if s_ == "L" else "L"
    for f in (1623, END): hang_hand(ctrl, other, f, bend=0.15)
    for f in (1623, 1700, END): fs(f); look_at(ctrl, f, Vector((SXX, -3.0, 1.6)) if f != 1700 else P_TOPS + Vector((0, 0, 1.6)), blend=0.8)
    for f in (1623, END): key_face(rig, f, smile=0.8, brow=0.5)
# costume + hair for "years later" (switched inside the flash)
for n in ("Pris.top", "Pris.trousers"): vis(O[n], 1, True); vis(O[n], 1623, False)
for n in ("Pris.suittop", "Pris.suittrousers"): vis(O[n], 1, False); vis(O[n], 1623, True)
for c in PRIS.children:
    if c.type == 'MESH' and any(k in c.name.lower() for k in ("short", "eyebrow")):
        for m in c.data.materials:
            for nd in m.node_tree.nodes:
                if nd.type == 'MIX' and nd.blend_type == 'MULTIPLY':
                    c0 = tuple(nd.inputs[7].default_value)
                    for f, col in ((1, c0[:3]), (1622, c0[:3]), (1623, (0.85, 0.85, 0.85))):
                        nd.inputs[7].default_value = (*col, 1); nd.inputs[7].keyframe_insert("default_value", frame=f)
                    for fc in iter_fcurves(m.node_tree.animation_data.action):
                        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
log("S9 done")
