# LegoInNose v013 final round (exec'd by 02b_story.py): Mom comes over and KNEELS on the rug at the boy's front-left,
# the boy turns 3/4 to her with his head tilted up, the tweezers (her RIGHT hand) enter in front of his face,
# her hand stays >= 1 cm clear of his face and hair, and the yellow brick comes out readable.
# She is moved from the sofa to the kneel at KF while the camera is close on the boy's face (she is off frame).

KF = 800
# ---- 1. freeze her sofa pose up to KF-1 (every channel keyed at KF-1, CONSTANT into KF)
def hold_channels(obj, f):
    ad = obj.animation_data
    for fc in iter_fcurves(ad.action):
        v = fc.evaluate(f); fc.keyframe_points.insert(f, v, options={'FAST'}); fc.update()
def constant_at(obj, f):
    ad = obj.animation_data
    for fc in iter_fcurves(ad.action):
        for kp in fc.keyframe_points:
            if abs(kp.co.x - f) < 0.5: kp.interpolation = 'CONSTANT'
hold_channels(MOM, KF - 1)

# the book stays on the sofa seat (she put it down), the tweezers go with her
fs(KF - 1)
BOOK.rotation_mode = 'XYZ'
BOOK.keyframe_insert("location", frame=KF - 1); BOOK.keyframe_insert("rotation_euler", frame=KF - 1)
bz = ray_down([SOFA], MOM_X + 0.05, MY + 0.30)
BOOK.location = Vector((MOM_X + 0.05, MY + 0.30, (bz or seat_top) + 0.001)); BOOK.rotation_euler = (0, 0, math.radians(75))
BOOK.keyframe_insert("location", frame=KF); BOOK.keyframe_insert("rotation_euler", frame=KF)
set_interp(BOOK, 'CONSTANT')

# ---- 2. the kneel geometry
fs(858); NOSE = head_M(BOY, 858) @ N_B
KC = Vector((NOSE.x + 0.39, NOSE.y - 0.21, 0.0))                    # knee centre on the rug (his front-left)
F = Vector((NOSE.x - KC.x, NOSE.y - KC.y, 0.0)).normalized()        # she faces his face
LEFT = Vector((-F.y, F.x, 0.0))
YAW = math.degrees(math.atan2(F.x, -F.y))
bl = MOM.data.bones
LT = (bl["lowerleg01.L"].head_local - bl["upperleg01.L"].head_local).length
LS = (bl["foot.L"].head_local - bl["lowerleg01.L"].head_local).length
HIPS_REST = (bl["upperleg01.L"].head_local + bl["upperleg01.R"].head_local) / 2
KZ0, AZ0 = RUG + 0.055, RUG + 0.050
KDZ = [0.0]; ADZ = [0.0]
log("mom kneel KC", tuple(round(x, 3) for x in KC), "yaw", round(YAW, 1), "LT", round(LT, 3), "LS", round(LS, 3))

def kneel(f, th=38.0, flex=12.0, back=0.0, spine=20.0, twist=0.0, side=0.0):
    kz = KZ0 + KDZ[0]; az = AZ0 + ADZ[0]
    K = Vector((KC.x, KC.y, kz)) - F * back
    t = math.radians(th)
    H = K - F * (LT * math.sin(t)) + Vector((0, 0, LT * math.cos(t)))
    Rw = Matrix.Rotation(math.radians(YAW), 3, 'Z') @ Matrix.Rotation(math.radians(flex), 3, 'X')
    root = H - Rw @ (HIPS_REST - HM_.root_head)
    HM_.key_root(f, root, yaw=YAW, flex=flex)
    for s in "LR":
        sg = 1 if s == "L" else -1
        Ks = K + LEFT * sg * 0.105
        A = Ks - F * math.sqrt(max(LS * LS - (kz - az) ** 2, 0.01)); A.z = az
        a = MR.BN["foot." + s].head_local
        M = Matrix.Translation(A) @ Matrix.Rotation(math.radians(YAW), 4, 'Z') @ Matrix.Rotation(math.radians(150), 4, 'X') @ \
            Matrix.Translation(-a) @ MR.rest("IK_foot." + s)
        MR.key_world("IK_foot." + s, f, M)
        key_pole(MR, s, f, Ks + F * 0.7 + Vector((0, 0, 0.10)), kind="knee")
    key_spine(MR, f, flex=spine, twist=twist, side=side)

def low_near(objs, c, r):
    best = 9.0
    for o in objs:
        for p in eval_points(o):
            if (p[1].to_2d() - c.to_2d()).length < r: best = min(best, p[1].z)
    return best
MLEGS = [O["Mom.trousers"], O["Mom.body"]]
kneel(KF, th=28, flex=12, spine=20)     # knee and ankle joints placed geometrically: kneecap and instep on the rug
fs(KF)
log("mom kneel joints: knee z", round(min(Wh(MOM, "lowerleg01." + s)[2] for s in "LR"), 3), "ankle z", round(min(Wh(MOM, "foot." + s)[2] for s in "LR"), 3),
    "toe z", round(min(Wh(MOM, "toe1-1." + s)[2] for s in "LR"), 3))
fs(KF)

# her acting from the kneel (root/spine), keyed before the hands so the reaches see the final body
for f, th, fl, bk, sp, tw in ((KF, 28, 14, 0.03, 22, 0), (826, 28, 18, 0.0, 30, -4), (858, 28, 20, 0.0, 34, -6), (892, 28, 20, 0.0, 32, -6),
                              (925, 26, 12, 0.02, 20, 4), (980, 26, 12, 0.02, 18, 4), (1040, 26, 12, 0.03, 16, 0), (1198, 26, 12, 0.03, 16, 0)):
    kneel(f, th=th, flex=fl, back=bk, spine=sp, twist=tw)
for f, yw, pt in ((KF, 4, 10), (826, 0, 18), (858, -2, 22), (892, 2, 16), (925, 26, -6), (980, 30, -4), (1040, 6, 10), (1198, 4, 8)):
    key_head(MR, f, yw, pt)
for f, kw in ((KF, dict(brow=0.5, jaw=0.1)), (830, dict(brow=0.2, squint=0.3)), (870, dict(brow=-0.2, squint=0.5)),
              (905, dict(smile=0.8, brow=0.4)), (1000, dict(smile=0.8)), (1198, dict(smile=0.6))):
    key_face(MOM, f, **kw)

# left hand rests on her own left thigh the whole time
def thigh_pt(f, s="L", u=0.62):
    fs(f); q = Wh(MOM, "upperleg01." + s).lerp(Wh(MOM, "lowerleg01." + s), u)
    z = ray_down([O["Mom.trousers"]], q.x, q.y); return Vector((q.x, q.y, z if z is not None else q.z + 0.06))
LSH = lambda f: (fs(f), Wh(MOM, "upperarm01.L"))[1]
POLE_ML = lambda f: LSH(f) + LEFT * 0.35 + Vector((0, 0, -0.40)) - F * 0.10      # her left elbow down and out (was still keyed at the sofa)
def thigh_front(f, s, u):
    """front face of her (near-vertical) kneeling thigh: the hand rests on it, palm back"""
    fs(f); h = Wh(MOM, "upperleg01." + s); k = Wh(MOM, "lowerleg01." + s); q = h.lerp(k, u)
    ax = (k - h).normalized(); o = (F - ax * F.dot(ax)).normalized()
    out = LEFT * (1 if s == "L" else -1)
    o = (o + out * 0.8).normalized()          # outer-front of the thigh, hands apart
    return q + o * 0.075, ax, o
def thigh_rest(f, s, u, pose, pole):
    P, ax, o = thigh_front(f, s, u)      # fingers along the thigh, palm onto its front surface
    rest_hand(MOM, MR, s, f, P, ax, -o, pose=pose, pole=pole)
for f in (KF, 858, 925, 1040, 1198):
    thigh_rest(f, "L", 0.40, "relaxed", POLE_ML(f))

# ---- 3. tweezers in her RIGHT hand from KF (pen grip: grip point at the pinch, long axis along the index)
fs(1); TW0 = TWZ.matrix_world.copy(); TWZ.rotation_mode = 'QUATERNION'; key_basis(TWZ, 1, TW0)
tw_len = max(v.co.y for v in TWZ.data.vertices); tw_tail = min(v.co.y for v in TWZ.data.vertices)
TW_TIP = Vector((0, tw_len, 0)); TW_GRIP = Vector((0, tw_tail * 0.15, 0))
def tw_at(f, tip_world, axis_world, up=Vector((0, 0, 1))):
    y = Vector(axis_world).normalized(); M = frame_from(y, up, Vector((0, 0, 0)))
    M.translation = Vector(tip_world) - M.to_3x3() @ TW_TIP; return M
RSH = lambda f: (fs(f), Wh(MOM, "upperarm01.R"))[1]
POLE_MR = lambda f: RSH(f) - LEFT * 0.30 + Vector((0, 0, -0.45)) + F * 0.05     # elbow down and out to her right
def yel_outer(f):
    fs(f); return stud_end(YEL), (YEL.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
def tw_axis(f, z_):
    """tip inward along the passage, tail swung toward Mom (her hand stays off his face)"""
    m = Vector((KC.x, KC.y, 0.55)) - Vector((NOSE.x, NOSE.y, NOSE.z)); m.z = 0; m.normalize()
    return -(z_ + m * 0.55 + Vector((0, 0, -0.10))).normalized()
def grip_world(Mtw): return Mtw @ TW_GRIP
PALM_TW = lambda: (Vector((0, 0, -1)) * 0.3 + LEFT * 0.9).normalized()     # palm toward her left (thumb up), pen grip
# (a) the grip is defined at the key frame 858: natural reach, tweezers along the passage axis
fs(858); P58, z58 = yel_outer(858); M858 = tw_at(858, P58 + z58 * 0.001, tw_axis(858, z58))
ax58 = (M858.to_3x3() @ Vector((0, 1, 0))).normalized()
reach(MOM, MR, "R", 858, grip_world(M858), ax58, PALM_TW(), pose="pinch", pole=POLE_MR(858))
fs(858); OFF_TW = W(MOM, "wrist.R").inverted() @ M858
# (b) at KF the tweezers are already in her hand (she brought them), hand raised at chest height
ch = RSH(KF) + F * 0.24 + LEFT * 0.12 + Vector((0, 0, -0.24))
reach(MOM, MR, "R", KF, ch, (F * 0.7 + Vector((0, 0, 0.6))).normalized(), PALM_TW(), pose="pinch", pole=POLE_MR(KF))
fs(KF); key_basis(TWZ, KF - 1, TW0); key_basis(TWZ, KF, W(MOM, "wrist.R") @ OFF_TW)
grab(MOM, "R", KF + 1, TWZ)
set_interp(TWZ, 'LINEAR')
log("tweezer grip offset check mm", round((PROP_OFF[TWZ.name][2].translation - OFF_TW.translation).length * 1000, 2))
P_, z_ = yel_outer(826)
place_prop(MR, 826, TWZ, tw_at(826, P_ + z_ * 0.09 + Vector((0, 0, -0.02)), tw_axis(826, z_)), pose="pinch", pole=POLE_MR(826))
P_, z_ = yel_outer(842)
place_prop(MR, 842, TWZ, tw_at(842, P_ + z_ * 0.022, tw_axis(842, z_)), pose="pinch", pole=POLE_MR(842))
for f in (852, 858):
    P_, z_ = yel_outer(f); place_prop(MR, f, TWZ, tw_at(f, P_ + z_ * 0.001, tw_axis(f, z_)), pose="pinch", pole=POLE_MR(f))
owner_switch(YEL, 859, TWZ, None, log)
fs(858); Mh858 = head_M(BOY, 858)
for f, out in ((868, 0.008), (880, 0.024), (892, 0.050)):
    Mhf = head_M(BOY, f)
    Mt_ = Mhf @ Mh858.inverted() @ Matrix.Translation(z58 * out) @ M858
    place_prop(MR, f, TWZ, Mt_, pose="pinch", pole=POLE_MR(f))
# she lifts it between their faces, toward the camera, tip up: both look at it (natural hand, the tweezers follow)
def eyes_c(rig, f):
    M = head_M(rig, f); return M @ ((rig.data.bones["eye.L"].head_local + rig.data.bones["eye.R"].head_local) / 2)
def show_pt(f):
    fs(f); b = eyes_c(BOY, f); m = eyes_c(MOM, f); c = b.lerp(m, 0.42)
    return c + Vector((-0.02, -0.16, -0.10))
for f in (925, 980):
    reach(MOM, MR, "R", f, show_pt(f), Vector((-0.2, -0.1, 1.0)), (Vector((0, -1, 0)) * 0.6 + LEFT * 0.6).normalized(), pose="pinch", pole=POLE_MR(f))
# hand down to her right thigh, tweezers lying along it
for f in (1040, 1198):
    thigh_rest(f, "R", 0.40, "pinch", POLE_MR(f))

constant_at(MOM, KF - 1)
log("mom kneel staged; book", tuple(round(x, 3) for x in BOOK.location))

# scatter bricks under her knees/shins go when she arrives (they are off camera then)
SHIN = [Vector((KC.x, KC.y, 0)) - F * (u * 0.5) + LEFT * sg * 0.105 for u in (0, 0.25, 0.5, 0.75, 1.0) for sg in (1, -1)]
for o_ in [o for o in O if o.name.startswith("Scatter")]:
    if min((o_.location.to_2d() - p.to_2d()).length for p in SHIN) < 0.10:
        vis(o_, 1, True); o_.keyframe_insert("hide_render", frame=1); o_.keyframe_insert("hide_viewport", frame=1)
        vis(o_, KF, False); o_.keyframe_insert("hide_render", frame=KF); o_.keyframe_insert("hide_viewport", frame=KF)
        log("scatter hidden from KF", o_.name)
