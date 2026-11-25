# ShoeBomber v011 stage B part 2 (exec'd by 02_animate.py): the story keyed in time order.
SHOE_L, SHOE_R, FUSE_L, FUSE_R, MATCH = O["ShoeL"], O["ShoeR"], O["FuseL"], O["FuseR"], O["Match"]
# match rebuilt in its own space: base at the origin, stick along +Z, head 58 mm, teardrop flame above it (no object scales)
def _fix_match():
    m = O["Match"]; m.data.transform(Matrix.Translation((0, 0, -min(v.co.z for v in m.data.vertices)))); m.location = (0, 0, 0)
    h = O["MatchHead"]; f = O["Flame"]; L = O["FlameLight"]
    for o, z in ((h, 0.058), (f, 0.072), (L, 0.085)):
        if o.type == 'MESH':
            o.data.transform(Matrix.Diagonal((*o.scale, 1.0))); o.scale = (1, 1, 1)
        o.parent = m; o.matrix_parent_inverse = Matrix.Identity(4); o.location = (0, 0, z); o.rotation_euler = (0, 0, 0)
    me = f.data
    for v in me.vertices:   # teardrop: narrow tip up
        if v.co.z > 0: v.co.x *= max(0.25, 1 - v.co.z / 0.02); v.co.y *= max(0.25, 1 - v.co.z / 0.02)
    me.update()
_fix_match()
SYR, MBOX = O["Syringe"], O["Matchbox"]

def shoe_frame(shoe):
    """local facts of a shoe mesh: toe direction (+1/-1 along local Y), collar centre, top z"""
    vs = [v.co for v in shoe.data.vertices]; top = max(v.z for v in vs)
    col = [v for v in vs if v.z > top * 0.85]; cy = sum(v.y for v in col) / len(col); cx_ = sum(v.x for v in col) / len(col)
    ymid = (max(v.y for v in vs) + min(v.y for v in vs)) / 2
    toe = 1.0 if cy < ymid else -1.0
    return toe, Vector((cx_, cy, top)), ymid
def place_shoe(shoe, pos, yaw_deg):
    """put the shoe's sole on the surface point pos (origin at the bottom centre), toe pointing along world yaw"""
    toe, col, ymid = shoe_frame(shoe)
    base = 0.0 if toe > 0 else 180.0
    shoe.parent = None; shoe.rotation_mode = 'XYZ'; shoe.rotation_euler = (0, 0, math.radians(yaw_deg + base))
    shoe.location = Vector(pos); upd()
def attach_fuse(shoe, fuse):
    toe, col, ymid = shoe_frame(shoe)
    p = Vector((col.x, col.y + toe * 0.040, col.z - 0.018))
    fuse.parent = shoe; fuse.matrix_parent_inverse = Matrix.Identity(4)
    fuse.location = p; fuse.rotation_euler = (0, 0, 0 if toe > 0 else math.radians(180))
    fuse.rotation_mode = 'XYZ'
def fuse_tip(fuse):
    upd(); sp = fuse.data.splines[0]; return fuse.matrix_world @ sp.points[-1].co.to_3d() if sp.type == 'POLY' else fuse.matrix_world @ sp.bezier_points[-1].co

# ================================================================== BEAT 1-3: seated (1..372)
fs(1)
BX = -0.63
BZ = snap_seat("Bomber", 1, BX, B_SEAT, B_FRONT, spine=20.0, feet_fwd=0.32)
AZ = snap_seat("PaxA", 1, 0.63, P_SEAT, P_FRONT, spine=4.0)
WZ = snap_seat("PaxW", 1, 0.63, W_SEAT, W_FRONT, spine=4.0)
fs(1)
# lap: top of both thighs
def top_of(obj, x, y, z0=1.5):
    b = world_bvh(obj); hit = b.ray_cast(Vector((x, y, z0)), Vector((0, 0, -1)), 3.0)
    return hit[0].z if hit[0] is not None else None
def thigh_top(n, s, u=0.5):
    r = RIG[n]; h = Wh(r, "upperleg01." + s); k = Wh(r, "lowerleg01." + s)
    p = h.lerp(k, u); return Vector((p.x, p.y, p.z + 0.085)), (k - h).normalized()
fs(1)
tl, _ = thigh_top("Bomber", "L", 0.55); tr_, _ = thigh_top("Bomber", "R", 0.55)
LAP_Y = (tl.y + tr_.y) / 2; lap_z = max(tl.z, tr_.z)
log("lap z", round(lap_z, 3), "lap y", round(LAP_Y, 3))
place_shoe(SHOE_L, (BX - 0.02, LAP_Y + 0.02, lap_z + 0.003), 8.0)
attach_fuse(SHOE_L, FUSE_L)
# the second shoe stands on the middle seat cushion beside him
place_shoe(SHOE_R, (-1.13, M_FRONT - 0.18, M_SEAT + 0.001), -12.0)
attach_fuse(SHOE_R, FUSE_R)
T = fuse_tip(FUSE_L); log("fuse tip", tuple(round(x, 3) for x in T))
# matchbox and two spent matches on the middle seat beside the shoe
MBOX.location = (-1.02, M_FRONT - 0.05, M_SEAT + 0.008); MBOX.rotation_euler.z = math.radians(25)
for k in range(2):
    sm = MATCH.copy(); sm.data = MATCH.data.copy(); sm.name = "SpentMatch%d" % k; O["Match"].users_collection[0].objects.link(sm)
    for ch in list(sm.children): pass
    sm.location = (-0.98 + 0.03 * k, M_FRONT - 0.10 - 0.02 * k, M_SEAT + 0.0015); sm.rotation_euler = (math.radians(90), 0, math.radians(60 + 40 * k))
    for m_ in sm.data.materials: pass
    sm.data.materials[0] = bpy.data.materials["M_MatchWood"]
# ---- left hand holds the shoe by its outer side (posed wrap grip), the shoe owned by the hand
upd()
bb = [SHOE_L.matrix_world @ v.co for v in SHOE_L.data.vertices]
xmin = min(p.x for p in bb); ymid_ = sum(p.y for p in bb) / len(bb)
C_L = Vector((xmin, ymid_ - 0.02, lap_z + 0.07))
key_pole("Bomber", "L", 1, (BX - 0.55, LAP_Y - 0.1, 0.75))
rep = grip_object(RIG["Bomber"], "L", 1, SHOE_L, C_L, (1, 0, 0), finger_dir=(0, 0.2, -1))
log("bomber L grip", rep)
# ---- right hand: lit match pinched, flame brought to the fuse tip
D = Vector((-0.80, 0.20, 0.56)).normalized()          # the match stick: up and across, flame beyond the fingers
FDIR = Vector((0.10, 0.60, 0.80)).normalized()        # fingers point up and away; the stick crosses them sideways
PALM = Vector((-0.6, -0.5, -0.3))
def match_at(f, flame_pt):
    P = Vector(flame_pt) - D * 0.066
    reach("Bomber", "R", f, P, FDIR, PALM, pose="pinch", pole=(BX + 0.55, LAP_Y - 0.25, 0.55))
fs(1)
match_at(1, T + Vector((0.10, -0.07, 0.05)))
# match world matrix at frame 1 (base pinched 8 mm from the end, stick along D)
fs(1)
pp = pinch_pt(RIG["Bomber"], "R")
z_ = D; x_ = Vector((0, 0, 1)).cross(z_).normalized(); y_ = z_.cross(x_)
Mm = Matrix((x_, y_, z_)).transposed().to_4x4(); Mm.translation = pp - D * 0.008
MATCH.parent = None; MATCH.matrix_world = Mm
MATCH.rotation_mode = 'QUATERNION'
for k_ in ("location", "rotation_quaternion", "scale"): MATCH.keyframe_insert(k_, frame=0)
owner_switch(MATCH, 1, RIG["Bomber"], "wrist.R", log=log)
JIT = [(70, (0.012, -0.006, 0.004)), (100, (0.0, 0.0, 0.0)), (130, (0.004, 0.003, -0.002)), (160, (-0.002, -0.003, 0.002)),
       (190, (0.003, 0.002, 0.0)), (220, (0.0, -0.002, 0.003)), (250, (0.004, 0.002, -0.002)), (280, (0.0, 0.0, 0.0))]
for f, d in JIT: match_at(f, T + Vector(d) + Vector((0.004, -0.004, -0.004)))
match_at(312, T + Vector((0.08, -0.06, 0.07))); match_at(345, T + Vector((0.10, -0.07, 0.09)))
# head: looking at the fuse, then up at the attendant on "caught him"
for f, (yw, pt) in ((1, (-8, -20)), (60, (-4, -24)), (150, (-6, -26)), (240, (-3, -24)), (296, (-5, -22)), (318, (-20, 8)), (350, (-24, 12))):
    key_head("Bomber", f, yaw=yw, pitch=pt)
for f, fl in ((1, 20), (150, 23), (296, 22), (320, 10), (360, 8)): key_spine("Bomber", f, flex=fl)
key_face("Bomber", 1, brow=-0.4, squint=0.2); key_face("Bomber", 296, brow=-0.5, squint=0.3); key_face("Bomber", 316, brow=0.9, jaw=0.35); key_face("Bomber", 360, brow=0.8, jaw=0.25)
# ---- PaxA (across the aisle) and PaxW (behind him): hands resting on their thighs, heads react
def lap_hands(n, f, x, front, yaw=180.0, u=0.62):
    fs(f)
    for s in "LR":
        p, d = thigh_top(n, s, u); sx = -1 if (p.x < x) else 1
        rest_hand(n, s, f, p, d, (0, 0, -1), pose="relaxed", pole=(p.x + sx * 0.45, p.y - 0.45 * (1 if yaw == 180.0 else -1), 0.75))
fs(1); lap_hands("PaxA", 1, 0.63, P_FRONT); lap_hands("PaxW", 1, 0.63, W_FRONT)
for f, yw, pt in ((1, 5, -12), (120, -6, -10), (232, 28, -4), (262, 42, -8), (300, 50, -10), (340, 55, -14)): key_head("PaxA", f, yaw=yw, pitch=pt)
for f, yw, pt in ((1, -5, -6), (150, 8, -4), (250, 20, -2), (320, 35, -4), (372, 40, -8)): key_head("PaxW", f, yaw=yw, pitch=pt)
key_face("PaxA", 1, smile=0.1); key_face("PaxA", 300, brow=0.8, jaw=0.2); key_face("PaxW", 1, smile=0.15); key_face("PaxW", 330, brow=0.9, jaw=0.3)
for n_, fl in (("PaxA", 4), ("PaxW", 4)):
    for f in range(1, 373, 60): key_spine(n_, f, flex=fl + 1.2 * math.sin(f / 30.0))


# ================================================================== standing / walking / kneeling / lying helpers
def Ryaw(yaw): return Matrix.Rotation(math.radians(yaw), 3, 'Z')
def rest_z(n): return CTRL[n].BN["root"].head_local.z
def stand(n, f, x, y, yaw, spine=2.0, stance=0.10, dz=-0.015, twist=0.0, feet_yaw=None, side=0.0):
    key_root(n, f, (x, y, rest_z(n) + dz), yaw=yaw, side=side)
    fy = yaw if feet_yaw is None else feet_yaw
    for s in "LR":
        sx = 1 if s == "L" else -1
        o = Ryaw(fy) @ Vector((sx * stance, 0.0, 0)); foot(n, s, f, (x + o.x, y + o.y), fy + sx * 6)
    key_spine(n, f, flex=spine, twist=twist)
def body_pt(n, local, yaw, pos):
    """a point given in the character's own frame (x = own left at rest +X, y = back(+)/front(-), z up) -> world"""
    return Vector(pos) + Ryaw(yaw) @ Vector(local)
def arms_down(n, f, pos, yaw, swing=0.0, z=None, out=0.21):
    rz = rest_z(n) if z is None else z
    for s in "LR":
        sx = 1 if s == "L" else -1; sw = swing * (1 if s == "L" else -1)
        P = body_pt(n, (sx * out, -0.03 - sw, rz - 0.15 - 0.03 * abs(sw) * 4), yaw, (pos[0], pos[1], 0))
        fdir = Ryaw(yaw) @ Vector((0.0, -0.25 - sw * 2, -1.0)); palm = Ryaw(yaw) @ Vector((-sx, 0, 0))
        hand_free(n, s, f, P, fdir, palm, pose="relaxed", pole=body_pt(n, (sx * 0.45, 0.5, rz), yaw, (pos[0], pos[1], 0)))
def walk(n, pts, f0, f1, yaw_fn=None, stride=0.70):
    """walk along a polyline of xy points at constant speed (feet planted, arm swing opposite the legs)"""
    P = [Vector((p[0], p[1], 0)) for p in pts]
    L = [0.0]
    for a_, b_ in zip(P, P[1:]): L.append(L[-1] + (b_ - a_).length)
    def path(f):
        u = max(0.0, min(1.0, (f - f0) / (f1 - f0))); u = u * u * (3 - 2 * u) * 0.35 + u * 0.65
        d = u * L[-1]
        for i in range(len(P) - 1):
            if d <= L[i + 1] or i == len(P) - 2:
                t = (d - L[i]) / max(1e-6, L[i + 1] - L[i]); return P[i].lerp(P[i + 1], min(1, t))
    def heading(f):
        a_ = path(max(f0, f - 3)); b_ = path(min(f1, f + 3)); d = b_ - a_
        if d.length < 1e-4: return yaw_fn(f) if yaw_fn else 0.0
        return math.degrees(math.atan2(d.x, -d.y))       # yaw: rest faces -Y
    yf = yaw_fn or heading
    HUM[n].walk(path, yf, f0, f1, stride=stride, lift=0.06, bob=0.018, crouch=0.025, lean=4.0, step=2)
    dist = 0.0; prev = path(f0)
    for f in range(f0, f1 + 1, 4):
        p = path(f); dist += (p - prev).length; prev = p
        sw = 0.09 * math.sin(2 * math.pi * dist / stride)
        arms_down(n, f, p, yf(f), swing=sw)
    return path, yf

# ================================================================== ATTENDANT: walks down the aisle, smells, catches him (1..372)
AT = "Attendant"
A_STOP = (0.08, 1.48)
walk(AT, [(0.05, 4.9), (0.02, 3.0), A_STOP], 1, 205, yaw_fn=lambda f: 0.0)
stand(AT, 215, A_STOP[0], A_STOP[1], 0.0); arms_down(AT, 215, A_STOP, 0.0)
blinks(AT, [40, 170, 255, 360, 470, 590, 700, 820])
saccades(AT, 1, 860, seed=3)
# smell (216..265): chin up, sniff, eyes narrow; then looks down-right at him (her right is -X)
key_head(AT, 1, 0, -4); key_head(AT, 205, 4, -2); key_head(AT, 220, 6, 12); key_head(AT, 248, -8, 14); key_head(AT, 268, -22, -6)
key_head(AT, 290, -32, -22); key_head(AT, 330, -34, -26); key_head(AT, 365, -30, -20)
key_face(AT, 1, smile=0.35); key_face(AT, 205, smile=0.25); key_face(AT, 222, brow=-0.3, squint=0.5); key_face(AT, 262, brow=-0.6, squint=0.4)
key_face(AT, 300, brow=0.9, jaw=0.45); key_face(AT, 340, brow=0.8, jaw=0.3)
stand(AT, 268, A_STOP[0], A_STOP[1], -10.0, spine=6, twist=-6); arms_down(AT, 268, A_STOP, -10.0)
# "caught him": she leans in and points at the match (right hand, point pose), left hand low
stand(AT, 300, A_STOP[0], A_STOP[1] + 0.02, -18.0, spine=14, twist=-10)
fs(300); shR = Wh(RIG[AT], "upperarm01.R")
tgt = T
pdir = (tgt - shR).normalized()
hand_free(AT, "R", 300, shR + pdir * 0.48 + Vector((0, 0, -0.06)), pdir, Vector((0, 0, -1)), pose="point", pole=shR + Vector((0.3, 0.4, -0.4)))
arms_down(AT, 300, (A_STOP[0], A_STOP[1] + 0.02), -18.0)
hand_free(AT, "R", 300, shR + pdir * 0.48 + Vector((0, 0, -0.06)), pdir, Vector((0, 0, -1)), pose="point", pole=shR + Vector((0.3, 0.4, -0.4)))
stand(AT, 345, A_STOP[0], A_STOP[1] + 0.02, -20.0, spine=16, twist=-10)
fs(345); shR = Wh(RIG[AT], "upperarm01.R")
hand_free(AT, "R", 345, shR + pdir * 0.50 + Vector((0, 0, -0.04)), pdir, Vector((0, 0, -1)), pose="point", pole=shR + Vector((0.3, 0.4, -0.4)))
arms_down(AT, 345, (A_STOP[0], A_STOP[1] + 0.02), -20.0); hand_free(AT, "R", 345, shR + pdir * 0.50 + Vector((0, 0, -0.04)), pdir, Vector((0, 0, -1)), pose="point", pole=shR + Vector((0.3, 0.4, -0.4)))

# ================================================================== the bomber rises (373..414) and is taken down (414..450)
BM = "Bomber"
# hold the seated pose to 372
fs(372)
for n_ in (BM,):
    pass
def copy_keys(n, f_from, f_to):
    """duplicate every pose-bone key of rig n evaluated at f_from onto f_to (holds a pose)"""
    r = RIG[n]; fs(f_from)
    vals = {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy()) for pb in r.pose.bones}
    for pb in r.pose.bones:
        l, q = vals[pb.name]; pb.location = l; pb.rotation_quaternion = q
        pb.keyframe_insert("location", frame=f_to, group=pb.name); pb.keyframe_insert("rotation_quaternion", frame=f_to, group=pb.name)
copy_keys(BM, 345, 374)
# the shoe: owned by his left hand from 360, dropped as he rises (falls onto his own cushion), the match falls to the floor
owner_switch(SHOE_L, 360, RIG[BM], "wrist.L", log=log)
owner_switch(MATCH, 382, None, log=log)
fs(382); m0 = MATCH.matrix_world.copy()
ml = Vector((-0.38, 0.62, 0.002)); key_basis(MATCH, 396, Matrix.Translation(ml) @ Matrix.Rotation(math.radians(90), 4, 'Y') @ Matrix.Rotation(math.radians(30), 4, 'X'))
for mo in (O["Flame"], O["FlameLight"]): pass
FL = O["Flame"]; FLL = O["FlameLight"]
vis(FL, 1, True); vis(FL, 383, False); vis(FLL, 1, True); vis(FLL, 383, False)
# rise: root up and forward, then standing in the exit area facing the attendant
STAND_B = (-0.45, 0.82)
key_root(BM, 386, (BX + 0.03, 0.30, 0.78), yaw=180, flex=0); key_spine(BM, 386, flex=35)
for s in "LR":
    sx = -1 if s == "L" else 1
    foot(BM, s, 386, (BX + sx * 0.11, 0.63), 180.0)
stand(BM, 400, STAND_B[0], STAND_B[1], 180.0, spine=10, stance=0.12)
key_head(BM, 386, -10, -10); key_head(BM, 400, -18, 4); key_face(BM, 400, brow=-0.7, jaw=0.2)
fs(395); 
owner_switch(SHOE_L, 394, None, log=log)
fs(394); s0 = SHOE_L.matrix_world.copy()
cush = Vector((BX + 0.02, 0.10, B_SEAT + 0.002))
key_basis(SHOE_L, 404, Matrix.Translation(cush) @ Matrix.Rotation(math.radians(-15), 4, 'Z'))
key_basis(SHOE_L, 400, Matrix.Translation(cush + Vector((0, 0.02, 0.07))) @ Matrix.Rotation(math.radians(-5), 4, 'Z') @ Matrix.Rotation(math.radians(25), 4, 'X'))
# his arms: up defensively while grabbed
fs(400)
for f_, sw in ((400, 0.0), (412, 0.04)):
    for s in "LR":
        sx = -1 if s == "L" else 1
        P = body_pt(BM, (-sx * 0.20, -0.34, 1.32), 180.0, (STAND_B[0], STAND_B[1], 0))
        hand_free(BM, s, f_, P, Vector((0, 0.3, 1)), Vector((0, 1, 0)), pose="open_alarm", pole=body_pt(BM, (-sx * 0.6, 0.3, 0.9), 180.0, (STAND_B[0], STAND_B[1], 0)))
stand(BM, 412, STAND_B[0], STAND_B[1] + 0.05, 175.0, spine=16, stance=0.13, twist=8)
stand(BM, 420, STAND_B[0] + 0.12, STAND_B[1] + 0.12, 140.0, spine=28, stance=0.15)

# ---- prone on the exit-row floor: head to +X, face turned to +Y (his left), wrists crossed on the lower back
PR_X, PR_Y = 0.22, 1.08
def prone(n, f, x, y, z, head_yaw=70.0, breath=0.0):
    key_root(n, f, (x, y, z), yaw=90.0, flex=90.0)
    key_spine(n, f, flex=-3.0 + breath)
    key_head(n, f, yaw=head_yaw, pitch=8)
    r = CTRL[n]
    Mb = Matrix.Rotation(math.radians(90), 3, 'Z') @ Matrix.Rotation(math.radians(90), 3, 'X')
    rh = r.BN["root"].head_local
    for s in "LR":
        a = r.BN["foot." + s].head_local
        p = Vector((x, y, z)) + Mb @ (a - rh)
        p.z = 0.10
        M = Matrix.Translation(p) @ (Mb @ Matrix.Rotation(math.radians(55), 3, 'X')).to_4x4() @ Matrix.Translation(-a) @ r.rest("IK_foot." + s)
        r.key_world("IK_foot." + s, f, M)
        key_pole(n, s, f, p + Vector((0.45, 0, -0.6)), kind="knee")
PZ = 0.13
prone(BM, 446, PR_X, PR_Y, PZ)
fs(446)
TORSO = ("spine", "pelvis", "breast", "clavicle", "neck", "head", "upperleg", "lowerleg")
def torso_low(n, f):
    fs(f); dm = DOM[n]
    return min(p.z for i, p, _ in eval_points(BODY[n]) if (dm.get(i) or "").startswith(TORSO))
for _ in range(2):
    lowb = torso_low(BM, 446); PZ += 0.012 - lowb; prone(BM, 446, PR_X, PR_Y, PZ)
log("prone z", round(PZ, 3), "torso low", round(torso_low(BM, 446), 4))
# wrists crossed on the small of the back
fs(446)
def back_pt(n, bone, up=0.0):
    r = RIG[n]; p = Wh(r, bone); return p
lb = Wh(RIG[BM], "spine02") 
top_z = max(p.z for _, p, _ in eval_points(O[BM + ".top"]) if (p.to_2d() - lb.to_2d()).length < 0.10)
WR = Vector((lb.x - 0.02, lb.y, top_z + 0.035))
rest_hand(BM, "L", 446, WR + Vector((0.0, 0.055, 0.0)), (1, 0, 0.0), (0, 0, -1), pose="relaxed", pole=WR + Vector((0.15, 0.5, 0.12)), skin=0.0)
rest_hand(BM, "R", 446, WR + Vector((0.0, -0.055, 0.0)), (1, 0, 0.0), (0, 0, -1), pose="relaxed", pole=WR + Vector((0.15, -0.5, 0.12)), skin=0.0)
log("wrist target", tuple(round(v, 3) for v in WR), "top z", round(top_z, 3))
# hold, breathe, struggle a little until sedated, then limp
for f_, hy, br in ((470, 72, 1.0), (500, 66, -1.0), (530, 74, 1.5), (565, 70, 0.0), (600, 64, -0.5), (640, 62, 0.5)):
    prone(BM, f_, PR_X, PR_Y, PZ, head_yaw=hy, breath=br)
    rest_hand(BM, "L", f_, WR + Vector((0.0, 0.055, 0.0)), (1, 0, 0.0), (0, 0, -1), pose="relaxed", pole=WR + Vector((0.15, 0.5, 0.12)), skin=0.0)
    rest_hand(BM, "R", f_, WR + Vector((0.0, -0.055, 0.0)), (1, 0, 0.0), (0, 0, -1), pose="relaxed", pole=WR + Vector((0.15, -0.5, 0.12)), skin=0.0)
key_face(BM, 446, brow=-0.8, jaw=0.3, squint=0.4); key_face(BM, 500, brow=-0.6, jaw=0.15, squint=0.3); key_face(BM, 560, brow=-0.2, jaw=0.05)
key_face(BM, 610, brow=0.0, jaw=0.08)
lids(BM, 1, 0); blinks(BM, [90, 200, 470, 520])
lids(BM, 566, 0); lids(BM, 578, 0.5); lids(BM, 586, 0.3); lids(BM, 600, 1.0)
for f_ in range(640, END + 1, 80): prone(BM, f_, PR_X, PR_Y, PZ, head_yaw=62, breath=0.6 * math.sin(f_ / 25))
# flex-cuff restraint: one loop on each wrist (Child Of the wrist bones), joined by a short strap
CUFFS = []
if "M_Cuff" not in bpy.data.materials: mat("M_Cuff", (0.02, 0.02, 0.025), rough=0.45, coat=0.2)
for s in "LR":
    bpy.ops.mesh.primitive_torus_add(major_radius=0.040, minor_radius=0.008, major_segments=32, minor_segments=8)
    c = bpy.context.active_object; c.name = "Cuff_" + s; c.data.materials.append(bpy.data.materials["M_Cuff"]); bpy.ops.object.shade_smooth()
    c.scale = (1.0, 0.8, 1.0)
    fs(446); r = RIG[BM]
    a_ = Wh(r, "lowerarm02." + s); b_ = Wh(r, "wrist." + s); ax = (b_ - a_).normalized()
    Mc = (ax.to_track_quat('Z', 'Y')).to_matrix().to_4x4(); Mc.translation = b_ + ax * 0.012
    c.matrix_world = Mc @ Matrix.Diagonal((1.0, 0.8, 1.0, 1.0))
    cc = c.constraints.new('CHILD_OF'); cc.target = r; cc.subtarget = "lowerarm02." + s
    cc.inverse_matrix = (r.matrix_world @ r.pose.bones["lowerarm02." + s].matrix).inverted()
    CUFFS.append(c)
fs(446)
pa = CUFFS[0].matrix_world.translation; pb_ = CUFFS[1].matrix_world.translation
strap = curve_tube("Cuff_Strap", [tuple(pa), tuple((pa + pb_) / 2 + Vector((0, 0, 0.015))), tuple(pb_)], 0.006, bpy.data.materials["M_Cuff"])
cs = strap.constraints.new('CHILD_OF'); cs.target = RIG[BM]; cs.subtarget = "lowerarm02.L"
cs.inverse_matrix = (RIG[BM].matrix_world @ RIG[BM].pose.bones["lowerarm02.L"].matrix).inverted()
for o in CUFFS + [strap]: vis(o, 1, False); vis(o, 440, True)
log("cuff gap mm", round((pa - pb_).length * 1000, 1))

exec(open(HERE + "/02c_crew.py").read())
if STAGE == "b2":
    bpy.ops.wm.save_as_mainfile(filepath=OUT); open(OUT + ".log.txt", "w").write("\n".join(LOG)); print("STAGE_OK"); raise SystemExit
exec(open(HERE + "/02d_camera.py").read())
for o_ in O:
    for m_ in getattr(o_, "modifiers", []):
        if m_.type == 'SUBSURF': m_.show_viewport = True
open(OUT + ".log.txt", "w").write("\n".join(LOG))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("ANIM_OK", OUT)
