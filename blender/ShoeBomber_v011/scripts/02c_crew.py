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
fs(405); bR = RIG[BM]
ua = Wh(bR, "upperarm01.R").lerp(Wh(bR, "lowerarm01.R"), 0.35); el = Wh(bR, "upperarm01.R").lerp(Wh(bR, "lowerarm01.R"), 0.85)
hand_free(PA, "R", 405, el + Vector((0.06, -0.01, 0.0)), Vector((0, 0.2, -1)), Vector((-1, 0, 0)), pose="wrap_grip", pole=el + Vector((0.45, -0.25, -0.25)))
hand_free(PA, "L", 405, ua + Vector((0.06, 0.02, 0.03)), Vector((0, 0.3, -1)), Vector((-1, 0, 0)), pose="wrap_grip", pole=ua + Vector((0.45, 0.35, -0.2)))
stand(PA, 414, 0.0, 0.70, -95.0, spine=18, stance=0.15, twist=-6)
key_head(PA, 400, 5, -15); key_face(PA, 400, brow=-0.8, jaw=0.3)
kneel(BM, 432, 0.05, 1.05, 100.0, lean=45)
for s_ in "LR":
    sx_ = 1 if s_ == "L" else -1
    hand_free(BM, s_, 432, Vector((0.42, 1.05 + sx_ * 0.18, 0.55)), Vector((1, 0, -0.6)), Vector((0, 0, -1)), pose="open_alarm", pole=Vector((0.05, 1.05 + sx_ * 0.5, 0.6)))
kneel(PA, 446, 0.30, 0.55, 180.0, lean=32)
key_head(PA, 446, 0, -25)
def paxa_hands(f, d=0.0):
    fs(f)
    p1 = Wh(RIG[BM], "spine04"); p2 = Wh(RIG[BM], "spine05")
    zt = lambda p: max(q.z for _, q, _ in eval_points(O[BM + ".top"]) if (q.to_2d() - p.to_2d()).length < 0.06)
    on_body(PA, f, "L", Vector((p1.x, p1.y - 0.04, zt(p1))), (0, 1, 0), pole=Vector((p1.x + 0.35, p1.y - 0.55, 0.45)))
    on_body(PA, f, "R", Vector((p2.x + 0.05, p2.y - 0.07, zt(p2))), (0, 1, 0), pole=Vector((p2.x - 0.3, p2.y - 0.55, 0.45)))
for f_ in (446, 500, 560, 620):
    paxa_hands(f_)
    kneel(PA, f_, 0.30, 0.55, 180.0, lean=32 + (2 if f_ % 120 else -2))
key_head(PA, 520, -8, -30); key_head(PA, 600, 20, -12); key_head(PA, 680, 35, -5)
key_face(PA, 446, brow=-0.9, jaw=0.25, squint=0.3); key_face(PA, 600, brow=0.2, jaw=0.05)
blinks(PA, [60, 230, 480, 610, 760]); saccades(PA, 1, 860, seed=5)
for f_ in (700, 800, 870): paxa_hands(f_); kneel(PA, f_, 0.30, 0.55, 180.0, lean=30)

# ================================================================== STEWARD: down the aisle from the galley, grabs, kneels at the bomber's head side
ST = "Steward"
for f_, yw, sd in ((1, 0.0, 0.0), (90, 8.0, 2.0), (180, -6.0, -2.0), (260, 4.0, 1.0), (300, 0.0, 0.0)):
    stand(ST, f_, 0.0, 5.75, yw, side=sd); arms_down(ST, f_, (0.0, 5.75), yw)
for f_, yw, pt in ((1, 0, -5), (70, 25, -8), (150, -20, -4), (230, 10, -12), (300, 0, -6)): key_head(ST, f_, yw, pt)
walk(ST, [(0.0, 5.75), (0.0, 3.2), (-0.05, 1.66)], 300, 398, yaw_fn=lambda f: 0.0, stride=0.85)
fs(405)
for s in "LR":     # no contact in the grab (fewest contacts): hands up, ready, beside PaxA's hold
    sx = 1 if s == "L" else -1
    hand_free(ST, s, 405, body_pt(ST, (sx * 0.22, -0.30, 1.40), 0.0, (-0.05, 1.62, 0)), Vector((0, -0.3, 1)), Vector((0, -1, 0)), pose="open_alarm",
              pole=body_pt(ST, (sx * 0.5, 0.2, 0.95), 0.0, (-0.05, 1.62, 0)))
stand(ST, 405, -0.05, 1.62, 0.0, spine=10); stand(ST, 414, -0.02, 1.60, 0.0, spine=14)
for s in "LR":
    sx = 1 if s == "L" else -1
    hand_free(ST, s, 420, body_pt(ST, (sx * 0.24, -0.32, 1.36), 0.0, (-0.02, 1.60, 0)), Vector((0, -0.3, 1)), Vector((0, -1, 0)), pose="open_alarm",
              pole=body_pt(ST, (sx * 0.5, 0.2, 0.95), 0.0, (-0.02, 1.60, 0)))
key_head(ST, 300, 0, 0); key_head(ST, 405, 0, -18); key_face(ST, 405, brow=-0.8, jaw=0.2)
kneel(ST, 446, 0.98, 0.58, 180.0, lean=30, twist=0)
blinks(ST, [330, 480, 600, 730, 850]); saccades(ST, 300, 860, seed=7)
# syringe: in his right hand from the landing of the takedown (pinched like a dart, needle toward the arm)
A_ = Vector((0.05, 0.50, -0.86)).normalized()
SFD = A_; SPALM = Vector((1, 0, 0))
def needle_at(f, tip):
    P = Vector(tip) - A_ * 0.040            # pinch point on the barrel near the hub
    reach(ST, "R", f, P, SFD, SPALM, pose="pinch", pole=Vector(tip) + Vector((0.40, -0.50, 0.10)))
fs(446)
dl = Wh(bR, "upperarm01.R").lerp(Wh(bR, "lowerarm01.R"), 0.25)
dz = max(q.z for _, q, _ in eval_points(O[BM + ".top"]) if (q.to_2d() - dl.to_2d()).length < 0.05)
DELT = Vector((dl.x, dl.y, dz)); log("deltoid", tuple(round(v, 3) for v in DELT))
TIP0 = DELT + Vector((0.04, -0.14, 0.20))
needle_at(446, TIP0)
fs(446); pp = pinch_pt(RIG[ST], "R")
zA = A_; xA = Vector((0, 0, 1)).cross(zA).normalized(); yA = zA.cross(xA)
Ms = Matrix((xA, yA, zA)).transposed().to_4x4()
Ms.translation = pp - zA * 0.100
SYR.parent = None; SYR.matrix_world = Ms; SYR.rotation_mode = 'QUATERNION'
for k_ in ("location", "rotation_quaternion", "scale"): SYR.keyframe_insert(k_, frame=0)
owner_switch(SYR, 446, RIG[ST], "wrist.R", log=log)
vis(SYR, 1, False); vis(SYR, 440, True)
colorize(SYR, (0.10, 0.55, 1.0), gain=1.6)
needle_at(505, TIP0 + Vector((0, 0.02, 0.04)))
needle_at(535, DELT + A_ * -0.03)
needle_at(552, DELT + A_ * 0.010)
needle_at(575, DELT + A_ * 0.010)
needle_at(596, DELT + A_ * -0.08)
needle_at(640, DELT + Vector((0.04, -0.16, 0.22)))
fs(446)
def st_left(f):
    """his free hand rests on his own left thigh (no arm across the bomber's head)"""
    fs(f); h = Wh(RIG[ST], "upperleg01.L"); k = Wh(RIG[ST], "lowerleg01.L"); p = h.lerp(k, 0.6) + Vector((0, 0, 0.075))
    rest_hand(ST, "L", f, p, (k - h).normalized(), (0, 0, -1), pose="relaxed", pole=p + Vector((0.3, -0.3, 0.35)))
for f_ in (446, 505, 560, 620, 700, 870): kneel(ST, f_, 0.98, 0.58, 180.0, lean=30 + (6 if 530 < f_ < 600 else 0), twist=0); st_left(f_)
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
# 625..870: she goes to his seat, leans over the two shoes left on the cushions and points at the fuses (no grip: R15 simplify)
A_PICK = (-0.78, 0.82)
walk(AT, [A_BACK, (-1.05, 1.18), A_PICK], 625, 668, yaw_fn=lambda f: 75.0 - 55.0 * smoothstep((f - 625) / 43.0))
TL = fuse_tip(FUSE_L); TR = fuse_tip(FUSE_R)
def lean_point(f, yw, tgt, lean, gap=0.11):
    stand(AT, f, A_PICK[0], A_PICK[1], yw, spine=lean)
    fs(f); sh = Wh(RIG[AT], "upperarm01.R"); d = (Vector(tgt) - sh).normalized()
    arms_down(AT, f, A_PICK, yw)
    tip = Vector(tgt) - d * gap
    hand_free(AT, "R", f, tip - d * 0.09, d, Vector((0, 0, -1)), pose="point", pole=sh + Vector((-0.2, 0.45, -0.35)))
    rest = body_pt(AT, (0.16, -0.12, 0.78), yw, (A_PICK[0], A_PICK[1], 0))
    hand_free(AT, "L", f, rest, Ryaw(yw) @ Vector((0, -0.2, -1)), Ryaw(yw) @ Vector((-1, 0, 0)), pose="relaxed", pole=body_pt(AT, (0.5, 0.3, 0.95), yw, (A_PICK[0], A_PICK[1], 0)))
stand(AT, 670, A_PICK[0], A_PICK[1], 20.0, spine=10); arms_down(AT, 670, A_PICK, 20.0)
lean_point(700, 18.0, TL, 34)
lean_point(745, 16.0, TL, 36, gap=0.09)
stand(AT, 768, A_PICK[0], A_PICK[1], 20.0, spine=34); arms_down(AT, 768, A_PICK, 20.0)
for f_, yw in ((810, 26.0), (870, 30.0)):
    stand(AT, f_, A_PICK[0], A_PICK[1], yw, spine=36); arms_down(AT, f_, A_PICK, yw)
key_head(AT, 670, 0, -30); key_head(AT, 700, -4, -42); key_head(AT, 760, -2, -46); key_head(AT, 800, 14, -44); key_head(AT, 870, 18, -42)
key_face(AT, 700, brow=0.7, jaw=0.2); key_face(AT, 760, brow=0.9, jaw=0.45); key_face(AT, 840, brow=0.8, jaw=0.3)
# PaxW keeps watching from her seat (same person, same seat, the whole cabin story)
for f_, yw, pt in ((400, 30, -10), (450, 40, -20), (560, 38, -22), (650, 20, -14), (760, 10, -10), (870, 5, -8)): key_head("PaxW", f_, yaw=yw, pitch=pt)
for f_ in range(373, 900, 60): key_spine("PaxW", f_, flex=10 + 2 * math.sin(f_ / 30.0))
key_face("PaxW", 450, brow=0.9, jaw=0.25); key_face("PaxW", 640, brow=0.4)
blinks("PaxW", [80, 260, 430, 620, 800]); saccades("PaxW", 1, 860, seed=9)
blinks(BM, [])
