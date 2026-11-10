# Part 2 of 03_animate.py (exec'd in the same namespace):
# crate/bottle placement from the reach pose, arm IK targets, grasp, fingers.

bottle = bpy.data.objects["Bottle"]
crate = bpy.data.objects["Crate"]
BOTTLE_R = 0.0335
GRIP_H = 0.112                     # grip height above bottle bottom
MOUTH_H = 0.2465                   # rim top in bottle space
TOP_Z = crate["top_z"] + GZ

def world_delta(bone):
    """posed-from-rest transform of a bone (armature == world)"""
    return PB[bone].matrix @ rest(bone).inverted()

# ---------------------------------------------------------------- hand frames
def hand_basis(s, d, n):
    d = d.normalized()
    n = (n - d * n.dot(d)).normalized()
    a = d.cross(n) if s == "R" else n.cross(d)
    return Matrix((d, a, n)).transposed()          # columns d, a, n

REST_HAND = {}
for s in "LR":
    w = BN["wrist." + s].head_local
    d = (BN["finger3-1." + s].head_local - w)
    a = (BN["finger2-1." + s].head_local - BN["finger5-1." + s].head_local)
    n = d.cross(a) if s == "L" else a.cross(d)
    REST_HAND[s] = hand_basis(s, d, n)

def hand_matrix(s, W, d, n):
    Rm = hand_basis(s, d, n) @ REST_HAND[s].transposed()
    wr = BN["wrist." + s].head_local
    return Matrix.Translation(W) @ Rm.to_4x4() @ Matrix.Translation(-wr) @ rest("IK_hand." + s)

def key_pole(n, f, P):
    pb = PB[n]
    pb.location = rest(n).to_3x3().inverted() @ (P - BN[n].head_local)
    pb.keyframe_insert("location", frame=f, group=n)

SH = {s: BN["upperarm01." + s].head_local.copy() for s in "LR"}

def swing_pose(s, deg, bend=0.0):
    """hanging arm in rest-body coordinates. deg<0 = forward swing"""
    sx = 1 if s == "L" else -1
    L = 0.48 - bend
    v = Matrix.Rotation(R_(deg), 3, 'X') @ Vector((0.0, 0.0, -L))
    W = SH[s] + Vector((sx * 0.045, -0.02, 0.0)) + v
    d = Matrix.Rotation(R_(deg * 1.25), 3, 'X') @ Vector((sx * 0.08, -0.12, -1.0))
    n = Vector((-sx * 0.9, 0.35, 0.0))
    return W, d, n

# ---------------------------------------------------------------- reach / grasp geometry at f240
evaluate(240)
S240 = PB["upperarm01.R"].head.copy()
ARM_L = (BN["upperarm01.R"].head_local - BN["lowerarm01.R"].head_local).length + \
        (BN["lowerarm01.R"].head_local - BN["wrist.R"].head_local).length
reach = 0.88 * ARM_L
# grasp direction: forward, slightly outward, pitched down
yaw_out = R_(-8)
hdir = Vector((math.sin(yaw_out) * -1, -math.cos(yaw_out), 0.0))   # forward, a bit to the right
dG = (hdir + Vector((0, 0, -0.22))).normalized()
nG = Vector((0, 0, 1)).cross(dG).normalized()           # horizontal, palm toward +X side
if nG.x < 0:
    nG = -nG
palm_off = dG * 0.048 + nG * (0.021 + BOTTLE_R)         # wrist -> bottle axis at grip height
Wz = TOP_Z + GRIP_H - palm_off.z
dz = S240.z - Wz
horiz = math.sqrt(max(reach ** 2 - dz ** 2, 0.01))
WG = Vector((S240.x, S240.y, Wz)) + hdir * horiz + Vector((-0.03, 0, 0))
AX = WG + palm_off                                      # bottle axis point at grip height
B = Vector((AX.x, AX.y, TOP_Z))
print("GRASP", tuple(round(v, 3) for v in WG), "BOTTLE", tuple(round(v, 3) for v in B),
      "reach", round((WG - S240).length, 3), "armlen", round(ARM_L, 3))

# crate under the bottle: bottle 9 cm in from near edge, 14 cm in from right end, crate yawed 7 deg
CRATE_YAW = R_(7)
local = Vector((-0.4125 + 0.14, 0.204 - 0.09, 0))
crate.rotation_euler = (0, 0, CRATE_YAW)
crate.location = B - Matrix.Rotation(CRATE_YAW, 3, 'Z') @ local
crate.location.z = GZ
bottle.location = B
bottle.rotation_mode = 'QUATERNION'
bottle.rotation_quaternion = (1, 0, 0, 0)

# ---------------------------------------------------------------- bottle path
def bottle_key(f, loc, q):
    if bottle.rotation_quaternion.dot(q) < 0:
        q = -q
    bottle.location = loc
    bottle.rotation_quaternion = q
    bottle.keyframe_insert("location", frame=f)
    bottle.keyframe_insert("rotation_quaternion", frame=f)

Q0 = Quaternion((1, 0, 0, 0))
for f in (1, 272):
    bottle_key(f, B, Q0)
bottle_key(290, B + Vector((0, 0.004, 0.035)), Q0)
bottle_key(312, B + Vector((-0.005, 0.03, 0.15)), Quaternion(Vector((1, 0, 0)), R_(-4)))

def body_rel(bone, f, P, q_rest):
    evaluate(f)
    M = world_delta(bone)
    return M @ P, M.to_quaternion() @ q_rest

# chest-relative carry poses (rest-body coords). tilt: top toward the face (-X rot)
CARRY = [(345, "root", Vector((-0.17, -0.28, 0.92)), Quaternion(Vector((1, 0, 0)), R_(-6))),
         (385, "spine01", Vector((-0.12, -0.34, 1.10)), Quaternion(Vector((1, 0, 0)), R_(-14)))]
for f, bone, P, q in CARRY:
    loc, qq = body_rel(bone, f, P, q)
    bottle_key(f, loc, qq)

# drinking: placed in head space so the rim meets the lips
HEAD_REST = rest("head")
LIPS_REST = Vector((0.0, -0.1635, 1.6015))
def drink_pose(f, gap, down_deg, right_deg, drop=0.0):
    """gap: rim distance in front of the lips (m), along the bottle axis"""
    evaluate(f)
    Mh = world_delta("head")
    # axis from mouth toward bottle bottom, in rest-head coordinates
    ax = Matrix.Rotation(R_(right_deg), 3, 'Z') @ Matrix.Rotation(R_(-down_deg), 3, 'X') @ Vector((0, -1, 0))
    rim = LIPS_REST + ax * gap + Vector((0, 0, -drop))
    up_rest = -ax                                   # bottle +Z (bottom -> mouth)
    rim_w = Mh @ rim
    up_w = (Mh.to_3x3() @ up_rest).normalized()
    q_prev = bottle.rotation_quaternion.copy()
    up_prev = q_prev @ Vector((0, 0, 1))
    q = up_prev.rotation_difference(up_w) @ q_prev
    loc = rim_w - up_w * MOUTH_H
    return loc, q

# frame, rim gap, axis down (head space), axis to right, drop
DRINK = [(410, 0.07, 18, 16, 0.03), (424, 0.018, 10, 12, 0.004), (432, 0.002, 8, 11, 0.0),
         (445, 0.002, 7, 11, 0.0), (460, 0.002, 6, 11, 0.0), (476, 0.002, 7, 11, 0.0),
         (488, 0.03, 12, 13, 0.012)]
for f, gap, dn, rt, dr in DRINK:
    loc, q = drink_pose(f, gap, dn, rt, dr)
    bottle_key(f, loc, q)

LOWER = [(515, "spine01", Vector((-0.20, -0.26, 0.98)), Quaternion(Vector((1, 0, 0)), R_(-6))),
         (548, "root", Vector((-0.23, -0.13, 0.835)), Quaternion(Vector((0, 1, 0)), R_(-4))),
         (575, "root", Vector((-0.23, -0.11, 0.84)), Quaternion(Vector((0, 1, 0)), R_(-3))),
         (600, "root", Vector((-0.23, -0.115, 0.837)), Quaternion(Vector((0, 1, 0)), R_(-3)))]
for f, bone, P, q in LOWER:
    loc, qq = body_rel(bone, f, P, q)
    # keep bottle roll continuous: re-derive from the up vector only
    q_prev = bottle.rotation_quaternion.copy()
    up_w = qq @ Vector((0, 0, 1))
    qn = (q_prev @ Vector((0, 0, 1))).rotation_difference(up_w) @ q_prev
    bottle_key(f, loc, qn)


# ---------------------------------------------------------------- right arm targets
def key_hand_rest_coords(s, f, bone, W, d, n):
    evaluate(f)
    M = world_delta(bone)
    R3 = M.to_3x3()
    key_world("IK_hand." + s, f, hand_matrix(s, M @ W, R3 @ d, R3 @ n))

def key_pole_rest(s, f, bone, P):
    evaluate(f)
    key_pole("Pole_elbow." + s, f, world_delta(bone) @ P)

# walk swing (right arm forward when left leg forward)
SWR = pchip([(1, 2), (14, 4), (46, 16), (90, -20), (110, -24), (130, -28)])
SWL = pchip([(1, 2), (14, 0), (46, -18), (90, 14), (118, 6), (140, 0), (160, -5)])
def bendf(deg):
    return 0.03 * max(0.0, min(1.0, -deg / 20.0))
for f in list(range(1, 131, 6)) + [130]:
    W, d, n = swing_pose("R", SWR(f), bend=bendf(SWR(f)))
    key_hand_rest_coords("R", f, "spine01", W, d, n)
for f in list(range(1, 161, 6)) + [160]:
    W, d, n = swing_pose("L", SWL(f), bend=bendf(SWL(f)))
    key_hand_rest_coords("L", f, "spine01", W, d, n)

# reach (world space) -> grasp at 240, holds until bottle takes over at 272
Wg = WG
dirs = [(150, None), (172, "mid"), (195, Vector((0.06, 0.12, 0.17))), (222, Vector((0.015, 0.035, 0.035))),
        (240, Vector((0, 0, 0)))]
evaluate(130)
for f, off in dirs:
    if isinstance(off, str):
        evaluate(f)
        M = world_delta("spine01")
        W, d, n = swing_pose("R", -38, bend=0.08)
        W = (M @ W).lerp(Wg + Vector((0.06, 0.12, 0.17)), 0.35)
        d = (M.to_3x3() @ d).lerp(dG, 0.6)
        key_world("IK_hand.R", f, hand_matrix("R", W, d, (M.to_3x3() @ n).lerp(nG, 0.7)))
        continue
    if off is None:
        evaluate(f)
        M = world_delta("spine01")
        W, d, n = swing_pose("R", -30, bend=0.06)
        W, d, n = M @ W, M.to_3x3() @ d, M.to_3x3() @ n
        d = d.lerp(dG, 0.35)
        key_world("IK_hand.R", f, hand_matrix("R", W, d, n.lerp(nG, 0.4)))
    else:
        t = 1.0 - min(off.length / 0.22, 1.0)
        d = dG.lerp(Vector((0.1, -0.5, -1)).normalized(), 0.25 * (1 - t))
        key_world("IK_hand.R", f, hand_matrix("R", Wg + off, d, nG))
key_world("IK_hand.R", 272, hand_matrix("R", Wg, dG, nG))

# bottle carries the hand from 272 on
co = PB["IK_hand.R"].constraints.new('CHILD_OF')
co.name = "Grip_Bottle"
co.target = bottle
evaluate(272)
co.inverse_matrix = bottle.matrix_world.inverted()
co.influence = 0.0
co.keyframe_insert("influence", frame=271)
co.influence = 1.0
co.keyframe_insert("influence", frame=272)

# elbow poles (rest-body coords relative to chest)
POLE_R = [(1, (-0.42, 0.55, 1.05)), (130, (-0.45, 0.55, 1.10)), (240, (-0.55, 0.50, 1.25)),
          (330, (-0.55, 0.45, 1.10)), (385, (-0.55, 0.30, 0.95)), (420, (-0.65, 0.10, 0.85)),
          (480, (-0.65, 0.10, 0.85)), (515, (-0.50, 0.35, 0.95)), (548, (-0.42, 0.50, 1.05)),
          (600, (-0.42, 0.50, 1.05))]
POLE_L = [(1, (0.42, 0.55, 1.05)), (150, (0.45, 0.55, 1.10)), (205, (0.55, 0.45, 1.20)),
          (330, (0.55, 0.45, 1.20)), (370, (0.42, 0.55, 1.05)), (600, (0.42, 0.55, 1.05))]
for f, P in POLE_R:
    key_pole_rest("R", f, "spine01", Vector(P))
for f, P in POLE_L:
    key_pole_rest("L", f, "spine01", Vector(P))

# ---------------------------------------------------------------- left hand on thigh
def thigh_contact(f):
    evaluate(f)
    pb = PB["upperleg02.L"]
    h, t = pb.head, pb.tail
    along = (t - h).normalized()
    p = h.lerp(t, 0.66)
    # thigh front/outer surface (bone frame), hand slightly above the knee
    fwd = world_delta("root").to_3x3() @ Vector((0, -1, 0))
    fwd = (fwd - along * fwd.dot(along)).normalized()
    side = along.cross(fwd).normalized()
    if side.x < 0:
        side = -side
    out = (fwd * 0.75 + side * 0.45).normalized()
    W = p + out * 0.078 - along * 0.05
    d = (along * 0.85 + side * 0.15).normalized()       # fingers toward the knee
    n = -out                                             # palm on thigh
    return W, d, n

for f in range(205, 321, 15):
    W, d, n = thigh_contact(f)
    key_world("IK_hand.L", f, hand_matrix("L", W, d, n))
# approach + release
W, d, n = thigh_contact(182)
key_world("IK_hand.L", 182, hand_matrix("L", W + Vector((0.025, -0.03, 0.06)), d.lerp(Vector((0, 0, -1)), 0.4), n))
W, d, n = thigh_contact(196)
key_world("IK_hand.L", 196, hand_matrix("L", W + Vector((0.008, -0.01, 0.018)), d, n))
W, d, n = thigh_contact(330)
key_world("IK_hand.L", 338, hand_matrix("L", W + Vector((0.02, -0.01, 0.05)), d.lerp(Vector((0, 0, -1)), 0.5), n))
for f, deg in [(357, -10), (372, -6), (420, 3), (470, 4), (520, 0), (548, -3), (575, 1), (600, 0)]:
    W, d, n = swing_pose("L", deg)
    key_hand_rest_coords("L", f, "spine01", W, d, n)

# ---------------------------------------------------------------- fingers
def finger_axes(s):
    Rh = REST_HAND[s]
    return Rh.col[0].copy(), Rh.col[1].copy(), Rh.col[2].copy()   # d, a, n (rest)

def curl_q(s, bone, deg):
    d, a, n = finger_axes(s)
    sign = 1 if s == "R" else -1
    return local_q(bone, Matrix.Rotation(R_(deg * sign), 3, a))

def thumb_q(s, bone, opp, flex):
    d, a, n = finger_axes(s)
    sign = 1 if s == "R" else -1
    return local_q(bone, Matrix.Rotation(R_(flex * sign), 3, a) @ Matrix.Rotation(R_(opp * sign), 3, d))

JW = (0.85, 1.1, 0.75)            # curl distribution over the 3 phalanges
def set_hand(s, f, curl, thumb_opp, thumb_flex, spread=0.0, key=True):
    for k in range(2, 6):
        c = curl[k - 2] if isinstance(curl, (list, tuple)) else curl
        for j in range(1, 4):
            b = "finger%d-%d.%s" % (k, j, s)
            q = curl_q(s, b, c * JW[j - 1])
            if j == 1 and spread:
                d, a, n = finger_axes(s)
                q = q @ local_q(b, Matrix.Rotation(R_(spread * (k - 3.5) * (1 if s == "R" else -1)), 3, n))
            if key:
                key_q(b, f, q)
            else:
                PB[b].rotation_quaternion = q
    for j, (o, fl) in enumerate([(thumb_opp, thumb_flex * 0.4), (0, thumb_flex * 0.8), (0, thumb_flex)], 1):
        b = "finger1-%d.%s" % (j, s)
        q = thumb_q(s, b, o, fl)
        if key:
            key_q(b, f, q)
        else:
            PB[b].rotation_quaternion = q

# solve the closed grip: curl each finger until it meets the bottle surface
evaluate(268)
axis_xy = Vector((B.x, B.y))
def clearance(k):
    pts = [PB["finger%d-2.R" % k].head, PB["finger%d-3.R" % k].head, PB["finger%d-3.R" % k].tail]
    th = (0.0085, 0.0075, 0.0062)
    return min((Vector((p.x, p.y)) - axis_xy).length - BOTTLE_R - t for p, t in zip(pts, th))

GRIP = []
for k in range(2, 6):
    lo, hi = 0.0, 90.0
    for _ in range(14):
        mid = (lo + hi) / 2
        c = [0, 0, 0, 0]; c[k - 2] = mid
        set_hand("R", 268, [mid if i == k - 2 else 0 for i in range(4)], 30, 10, key=False)
        bpy.context.view_layer.update()
        if clearance(k) > 0:
            lo = mid
        else:
            hi = mid
    GRIP.append(round(lo, 1))
print("GRIP_CURL", GRIP)
GRIP = [min(g, 70.0) for g in GRIP]

# thumb: search opposition/flex so the tip wraps the far side at grip height
# and no thumb joint enters the bottle
evaluate(268)
tips = [PB["finger%d-3.R" % k].tail.copy() for k in range(2, 6)]
gz = B.z + GRIP_H
best = None
for opp in range(-30, 91, 6):
    for fl in range(-10, 71, 5):
        set_hand("R", 268, GRIP, opp, fl, key=False)
        bpy.context.view_layer.update()
        js = [PB["finger1-2.R"].head, PB["finger1-3.R"].head, PB["finger1-3.R"].tail]
        ds = [(Vector((p.x, p.y)) - axis_xy).length - BOTTLE_R for p in js]
        if min(ds) < 0.006:
            continue
        tip = js[-1]
        cost = abs(ds[-1] - 0.0075) * 10 + abs(tip.z - gz) * 2
        cost -= min((tip - t).length for t in tips) * 0.5     # oppose the fingers
        if best is None or cost < best[0]:
            best = (cost, opp, fl)
THUMB_OPP, THUMB = best[1], best[2]
print("THUMB", THUMB_OPP, THUMB, round(best[0], 4))

RELAX = 14
# right hand
set_hand("R", 1, RELAX, 8, 10)
set_hand("R", 150, RELAX + 4, 8, 10)
set_hand("R", 200, 4, 22, 0, spread=4)       # opening, fingers extend as the hand nears
set_hand("R", 238, 3, 30, 0, spread=5)
set_hand("R", 244, [g * 0.25 for g in GRIP], THUMB_OPP * 0.6, THUMB * 0.2, spread=4)
set_hand("R", 262, [g * 0.97 for g in GRIP], THUMB_OPP, THUMB * 0.95, spread=1)
set_hand("R", 270, [g + 2.5 for g in GRIP], THUMB_OPP, THUMB + 2)      # squeeze before the lift
set_hand("R", 600, [g + 2.5 for g in GRIP], THUMB_OPP, THUMB + 2)
# left hand
set_hand("L", 1, RELAX, 8, 10)
set_hand("L", 180, 6, 15, 4, spread=3)
set_hand("L", 205, 18, 12, 8)
set_hand("L", 330, 18, 12, 8)
set_hand("L", 360, RELAX + 3, 8, 10)
set_hand("L", 600, RELAX + 2, 8, 10)

print("ARMS_DONE")
