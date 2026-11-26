# ShoeBomber v011 stage B part 3 (exec'd from 02b_story.py): PaxA, the steward, the attendant through the takedown,
# the sedation and the shoe check (373..870).
# flame colour (true orange, not white)
fm = bpy.data.materials["M_Flame"]
for nd in fm.node_tree.nodes:
    if nd.type == 'VALTORGB':
        nd.color_ramp.elements[0].color = (1.0, 0.55, 0.08, 1); nd.color_ramp.elements[1].color = (1.0, 0.18, 0.0, 1)
    if nd.type == 'EMISSION': nd.inputs["Strength"].default_value = 5.0

def kneel(n, f, kx, ky, yaw, lean=25.0, twist=0.0, spread=0.12):
    """kneeling upright on both knees at (kx, ky), facing yaw; shins flat behind, toes tucked"""
    r = CTRL[n]; rh = r.BN["root"].head_local; hj = r.BN["upperleg01.L"].head_local; kn = r.BN["lowerleg01.L"].head_local
    thigh = (hj - kn).length
    z = 0.085 + thigh * 0.97 + (rh.z - hj.z)
    key_root(n, f, (kx, ky, z), yaw=yaw)
    key_spine(n, f, flex=lean, twist=twist)
    back = Ryaw(yaw) @ Vector((0, 1, 0))
    for s in "LR":
        sx = 1 if s == "L" else -1
        side = Ryaw(yaw) @ Vector((sx * spread, 0, 0))
        a = r.BN["foot." + s].head_local
        p = Vector((kx, ky, 0)) + side + back * 0.42; p.z = 0.075
        M = Matrix.Translation(p) @ (Ryaw(yaw) @ Matrix.Rotation(math.radians(-70), 3, 'X')).to_4x4() @ Matrix.Translation(-a) @ r.rest("IK_foot." + s)
        r.key_world("IK_foot." + s, f, M)
        key_pole(n, s, f, Vector((kx, ky, 0.3)) + side - back * 0.8, kind="knee")
def on_body(n, f, s, P, fdir, pose="relaxed", pole=None, skin=0.014):
    """palm resting ON a body surface point P (normal +Z unless given by fdir/palm)"""
    rest_hand(n, s, f, P, fdir, (0, 0, -1), pose=pose, pole=pole, skin=skin)

# ================================================================== PaxA: up from his seat, grabs, kneels on the bomber's right side
PA = "PaxA"
copy_keys(PA, 340, 374)
key_root(PA, 386, (0.55, 0.28, 0.80), yaw=-140, flex=0); key_spine(PA, 386, flex=30)
stand(PA, 400, 0.02, 0.72, -95.0, spine=12, stance=0.14)
bR = RIG[BM]
kneel(BM, 432, 0.05, 1.05, 100.0, lean=45)
for s_ in "LR":
    sx_ = 1 if s_ == "L" else -1
    hand_free(BM, s_, 432, Vector((0.42, 1.05 + sx_ * 0.18, 0.55)), Vector((1, 0, -0.6)), Vector((0, 0, -1)), pose="open_alarm", pole=Vector((0.05, 1.05 + sx_ * 0.5, 0.6)))
PA_POS = {405: ((0.02, 0.72), -95.0, 12), 414: ((0.0, 0.70), -95.0, 18), 420: ((0.02, 0.70), -90.0, 22), 432: ((0.08, 0.66), -75.0, 34)}
for f_, ((px, py), yw, sp) in PA_POS.items():
    stand(PA, f_, px, py, yw, spine=sp, stance=0.15)
for f_, ((px, py), yw, sp) in PA_POS.items():
    fs(f_)
    el = Wh(bR, "upperarm01.R").lerp(Wh(bR, "lowerarm01.R"), 0.80)
    ax = (Wh(bR, "lowerarm01.R") - Wh(bR, "upperarm01.R")).normalized()
    outw = (Wh(bR, "upperarm01.R") - Wh(bR, "spine05")); outw.z = 0; outw = outw.normalized()
    hand_free(PA, "R", f_, el + outw * 0.065, ax, -outw, pose="wrap_grip", pole=el + outw * 0.45 + Vector((0, 0, -0.25)))
    hand_free(PA, "L", f_, body_pt(PA, (0.27, -0.06, rest_z(PA) - 0.20), yw, (px, py, 0)), Ryaw(yw) @ Vector((0.15, -0.25, -1)), Ryaw(yw) @ Vector((-1, 0, 0)),
              pose="relaxed", pole=body_pt(PA, (0.55, 0.45, rest_z(PA)), yw, (px, py, 0)))
key_head(PA, 400, 5, -15); key_face(PA, 400, brow=-0.8, jaw=0.3); key_head(PA, 432, 0, -35)
kneel(PA, 446, 0.18, 0.46, 180.0, lean=16)
key_head(PA, 446, 0, -25)
def paxa_hands(f, d=0.0):
    fs(f)
    p1 = Wh(RIG[BM], "spine03"); p2 = Wh(RIG[BM], "spine04")
    zt = lambda p: max(q.z for _, q, _ in eval_points(O[BM + ".top"]) if (q.to_2d() - p.to_2d()).length < 0.06)
    on_body(PA, f, "L", Vector((p1.x, p1.y - 0.04, zt(p1))), (0, 1, 0), pole=Vector((p1.x + 0.35, p1.y - 0.55, 0.45)))
    on_body(PA, f, "R", Vector((p2.x + 0.05, p2.y - 0.07, zt(p2))), (0, 1, 0), pole=Vector((p2.x - 0.3, p2.y - 0.55, 0.45)))
for f_ in (446, 500, 560, 620):
    paxa_hands(f_)
    kneel(PA, f_, 0.18, 0.46, 180.0, lean=16 + (2 if f_ % 120 else -2))
key_head(PA, 520, -8, -30); key_head(PA, 600, 20, -12); key_head(PA, 680, 35, -5)
key_face(PA, 446, brow=-0.9, jaw=0.25, squint=0.3); key_face(PA, 600, brow=0.2, jaw=0.05)
blinks(PA, [60, 230, 480, 610, 760]); saccades(PA, 1, 860, seed=5)
# once he is sedated PaxA gets up and goes back to his own seat (clears the floor for the shoe check)
stand(PA, 662, 0.35, 0.42, 160.0, spine=8); arms_down(PA, 662, (0.35, 0.42), 160.0)
stand(PA, 680, 0.55, 0.36, 180.0, spine=12); arms_down(PA, 680, (0.55, 0.36), 180.0)
for f_ in (700, 870): copy_keys(PA, 300, f_)

# ================================================================== STEWARD: down the aisle from the galley, grabs, kneels at the bomber's head side
ST = "Steward"
for f_, yw, sd in ((1, 0.0, 0.0), (90, 8.0, 2.0), (180, -6.0, -2.0), (260, 4.0, 1.0), (300, 0.0, 0.0)):
    stand(ST, f_, 0.0, 5.75, yw, side=sd); arms_down(ST, f_, (0.0, 5.75), yw)
for f_, yw, pt in ((1, 0, -5), (70, 25, -8), (150, -20, -4), (230, 10, -12), (300, 0, -6)): key_head(ST, f_, yw, pt)
walk(ST, [(0.0, 5.75), (0.05, 3.2), (0.22, 1.74)], 300, 398, yaw_fn=lambda f: 0.0, stride=0.85)
for f_, yw in ((405, -15.0), (414, -20.0), (434, -25.0)):
    stand(ST, f_, 0.22, 1.74, yw, spine=10)
    for s_ in "LR":
        sx_ = 1 if s_ == "L" else -1
        hand_free(ST, s_, f_, body_pt(ST, (sx_ * 0.22, -0.28, 1.34), yw, (0.22, 1.74, 0)), Ryaw(yw) @ Vector((0, -0.3, 1)), Ryaw(yw) @ Vector((0, -1, 0)), pose="open_alarm",
                  pole=body_pt(ST, (sx_ * 0.5, 0.2, 0.95), yw, (0.22, 1.74, 0)))
key_head(ST, 300, 0, 0); key_head(ST, 405, 10, -18); key_face(ST, 405, brow=-0.8, jaw=0.2)
# round the head end of the struggle (camera on the attendant 439-450), never through the bomber
stand(ST, 440, 0.95, 1.62, -90.0, spine=10); stand(ST, 444, 1.50, 0.75, 180.0, spine=10)
kneel(ST, 450, 0.98, 0.58, 180.0, lean=30, twist=0)
blinks(ST, [330, 480, 600, 730, 850]); saccades(ST, 300, 860, seed=7)
for f_ in (450, 505, 560, 620, 700, 870): kneel(ST, f_, 0.64, 0.30, 180.0, lean=26 + (8 if 530 < f_ < 600 else 0), twist=0)
def st_left(f):
    """his free hand rests on his own left thigh (no arm across the bomber's head)"""
    fs(f); h = Wh(RIG[ST], "upperleg01.L"); k = Wh(RIG[ST], "lowerleg01.L"); p = h.lerp(k, 0.6) + Vector((0, 0, 0.075))
    rest_hand(ST, "L", f, p, (k - h).normalized(), (0, 0, -1), pose="relaxed", pole=p + Vector((0.3, -0.3, 0.35)))
for f_ in (450, 505, 560, 620, 700, 870): st_left(f_)
# syringe: pinched like a dart, needle down into the outside of his right upper arm (deltoid), measured on the sweater per frame
A_ = Vector((0.05, 0.45, -0.89)).normalized()
SFD = A_; SPALM = Vector((1, 0, 0))
TOPBVH = {}
def delt_surface(f):
    fs(f); r = RIG[BM]
    c = Wh(r, "upperarm01.R").lerp(Wh(r, "lowerarm01.R"), 0.22)
    b = world_bvh(O[BM + ".top"]); hit = b.ray_cast(c - A_ * 0.25, A_, 0.5)
    return hit[0] if hit[0] is not None else c
def needle_at(f, tip):
    P = Vector(tip) - A_ * 0.040            # pinch point on the barrel near the hub
    reach(ST, "R", f, P, SFD, SPALM, pose="pinch", pole=Vector(tip) + Vector((0.40, -0.50, 0.10)))
D446 = delt_surface(446); log("deltoid surface", tuple(round(v, 3) for v in D446))
TIP0 = D446 - A_ * 0.20
needle_at(452, TIP0)
fs(452); pp = pinch_pt(RIG[ST], "R")
zA = A_; xA = Vector((0, 0, 1)).cross(zA).normalized(); yA = zA.cross(xA)
Ms = Matrix((xA, yA, zA)).transposed().to_4x4()
Ms.translation = pp - zA * 0.100
SYR.parent = None; SYR.matrix_world = Ms; SYR.rotation_mode = 'QUATERNION'
for k_ in ("location", "rotation_quaternion", "scale"): SYR.keyframe_insert(k_, frame=0)
owner_switch(SYR, 452, RIG[ST], "wrist.R", log=log)
vis(SYR, 1, False); vis(SYR, 450, True)
colorize(SYR, (0.10, 0.55, 1.0), gain=1.6)
def tip_world(f):
    fs(f); return SYR.matrix_world @ Vector((0, 0, max(v.co.z for v in SYR.data.vertices)))
for f_, depth in ((505, -0.16), (530, -0.05), (548, 0.008), (578, 0.008), (598, -0.09), (640, -0.20)):
    tgt = delt_surface(f_) + A_ * depth; aim = tgt.copy()
    needle_at(f_, aim)
    for _ in range(4):      # correct for the grip offset so the real needle tip lands on the target
        err = tgt - tip_world(f_)
        if err.length < 0.003: break
        aim = aim + err; needle_at(f_, aim)
    log("needle", f_, "depth", depth, "tip err mm", round((delt_surface(f_) + A_ * depth - tip_world(f_)).length * 1000, 1))
key_head(ST, 446, -10, -30); key_head(ST, 540, -5, -40); key_head(ST, 600, -15, -20); key_head(ST, 660, 30, 5); key_head(ST, 760, 45, 0)
key_face(ST, 446, brow=-0.6, jaw=0.1, squint=0.2); key_face(ST, 560, brow=-0.4, squint=0.4); key_face(ST, 640, brow=0.2)

# ================================================================== ATTENDANT: steps back, watches, then checks the shoes (373..870)
A_BACK = (-1.22, 1.52)
walk(AT, [(A_STOP[0], A_STOP[1] + 0.02), (-0.55, 1.62), A_BACK], 374, 428, yaw_fn=lambda f: -20.0 + 95.0 * smoothstep((f - 374) / 54.0))
stand(AT, 432, A_BACK[0], A_BACK[1], 75.0, spine=6)
fs(432)
for f_ in (432, 520, 600):
    for s in "LR":
        sx = 1 if s == "L" else -1
        P = body_pt(AT, (sx * 0.12, -0.30, 1.00 if s == "R" else 0.94), 75.0, (A_BACK[0], A_BACK[1], 0))
        hand_free(AT, s, f_, P, Ryaw(75) @ Vector((-sx * 0.3, -0.2, 1)), Ryaw(75) @ Vector((0, 1, 0)), pose="open_alarm" if s == "R" else "relaxed",
                  pole=body_pt(AT, (sx * 0.5, 0.25, 0.95), 75.0, (A_BACK[0], A_BACK[1], 0)))
    stand(AT, f_, A_BACK[0], A_BACK[1], 75.0, spine=6 + (f_ % 3))
key_head(AT, 400, 20, -15); key_head(AT, 446, 0, -30); key_head(AT, 520, 5, -34); key_head(AT, 600, -10, -28)
key_face(AT, 446, brow=0.7, jaw=0.25); key_face(AT, 560, brow=0.3, jaw=0.05)
# 625..870: she goes to his seat, lifts his shoe off the cushion by the collar (posed grip, the shoe owned by her hand), shows the fuse
A_PICK = (-0.60, 0.68)
walk(AT, [A_BACK, (-1.05, 1.18), A_PICK], 625, 668, yaw_fn=lambda f: 75.0 - 75.0 * smoothstep((f - 625) / 43.0))
TL = fuse_tip(FUSE_L); TR = fuse_tip(FUSE_R)
stand(AT, 672, A_PICK[0], A_PICK[1], 0.0, spine=10); arms_down(AT, 672, A_PICK, 0.0)
def bend(f, dz, sp):
    key_root(AT, f, (A_PICK[0], A_PICK[1] + 0.05, rest_z(AT) + dz), yaw=0.0); key_spine(AT, f, flex=sp)
    for s_ in "LR":
        sx_ = 1 if s_ == "L" else -1
        foot(AT, s_, f, (A_PICK[0] + sx_ * 0.14, A_PICK[1] + 0.02), sx_ * 6.0)
bend(700, -0.22, 48); bend(708, -0.22, 48)
fs(700)
sv = [SHOE_L.matrix_world @ v.co for v in SHOE_L.data.vertices]
top = max(p.z for p in sv); col = [p for p in sv if p.z > top - 0.035]; cp = sum(col, Vector()) / len(col)
GRIP_FD = Vector((0.0, -0.35, -1.0)).normalized(); GRIP_PALM = Vector((-1.0, 0.0, -0.15))
gp = cp + Vector((0.035, 0.0, 0.025))
want = cp + Vector((0.030, 0.0, 0.020))
for _ in range(4):     # palm onto the collar (the IK lands a few cm off; correct it before the shoe is taken)
    for f_ in (700, 708): hand_free(AT, "R", f_, gp, GRIP_FD, GRIP_PALM, pose="wrap_grip", pole=gp + Vector((0.40, 0.25, 0.30)))
    fs(708); pm = Wh(RIG[AT], "wrist.R").lerp(Wh(RIG[AT], "finger3-1.R"), 0.6)
    if (want - pm).length < 0.008: break
    gp = gp + (want - pm)
hand_free(AT, "L", 700, body_pt(AT, (0.18, -0.20, 0.80), 0.0, (A_PICK[0], A_PICK[1], 0)), Vector((0, -0.3, -1)), Vector((-1, 0, 0)), pose="relaxed",
          pole=body_pt(AT, (0.5, 0.3, 0.95), 0.0, (A_PICK[0], A_PICK[1], 0)))
fs(708); r_ = RIG[AT]; palm = Wh(r_, "wrist.R").lerp(Wh(r_, "finger3-1.R"), 0.6)
log("attendant palm to collar mm", round((palm - cp).length * 1000, 1))
owner_switch(SHOE_L, 710, RIG[AT], "wrist.R", log=log)
# up to chest height, the shoe hanging from her hand, fuse toward the camera (camera faces her from the seat side)
for f_, yw, up in ((740, 25.0, 1.10), (775, 45.0, 1.14), (810, 52.0, 1.14), (870, 55.0, 1.12)):
    stand(AT, f_, A_PICK[0], A_PICK[1], yw, spine=8)
    hp = body_pt(AT, (-0.05, -0.36, up), yw, (A_PICK[0], A_PICK[1], 0))
    hand_free(AT, "R", f_, hp, Ryaw(yw) @ GRIP_FD, Ryaw(yw) @ GRIP_PALM, pose="wrap_grip", pole=hp + Ryaw(yw) @ Vector((-0.40, 0.30, -0.35)))
    hand_free(AT, "L", f_, body_pt(AT, (0.20, -0.08, 0.80), yw, (A_PICK[0], A_PICK[1], 0)), Ryaw(yw) @ Vector((0, -0.3, -1)), Ryaw(yw) @ Vector((-1, 0, 0)), pose="relaxed",
              pole=body_pt(AT, (0.5, 0.3, 0.95), yw, (A_PICK[0], A_PICK[1], 0)))
key_head(AT, 672, 0, -30); key_head(AT, 700, 0, -40); key_head(AT, 740, -8, -22); key_head(AT, 790, -10, -26); key_head(AT, 830, -30, -30); key_head(AT, 870, -36, -32)
key_face(AT, 700, brow=0.5, jaw=0.1); key_face(AT, 760, brow=0.9, jaw=0.45); key_face(AT, 840, brow=0.8, jaw=0.3)
# PaxW keeps watching from her seat (same person, same seat, the whole cabin story)
for f_, yw, pt in ((400, 30, -10), (450, 40, -20), (560, 38, -22), (650, 20, -14), (760, 10, -10), (870, 5, -8)): key_head("PaxW", f_, yaw=yw, pitch=pt)
for f_ in range(373, 900, 60): key_spine("PaxW", f_, flex=10 + 2 * math.sin(f_ / 30.0))
key_face("PaxW", 450, brow=0.9, jaw=0.25); key_face("PaxW", 640, brow=0.4)
blinks("PaxW", [80, 260, 430, 620, 800]); saccades("PaxW", 1, 860, seed=9)
blinks(BM, [])
