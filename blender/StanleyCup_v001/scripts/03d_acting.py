# Part of 03_animate.py: acting for the couple. Story-time is slowed ~x40 from f271 to f1285; real time before (beat 1-2 they are seen
# only through the window) and after the bullet drops.
WB = Vector((WOMAN_SEAT.x, WOMAN_SEAT.y, TOP)); FB = Vector((FIANCE_SEAT.x, FIANCE_SEAT.y, TOP))
UP = Vector((0, 0, 1))
def wpt(lx, ly, lz): return to_w(WB, -90.0, lx, ly, lz)       # her frame: lx = her left (-Y), ly = forward (-X)
def fpt(lx, ly, lz): return to_w(FB, 180.0, lx, ly, lz)       # his frame: lx = his left (-X), ly = forward (+Y)
WF = fwd(-90.0); FF = fwd(180.0); WL = side(-90.0); FL = side(180.0)
# ---- her: talking/laughing -> hears it, turns -> freezes, eyes wide -> hands come up -> flinch at impact -> real time: jolt, looks down,
#      hand to chest, grabs the dented tumbler by the handle and pulls it to her
W_BODY = [  # frame, lean, twist, side, head(pitch, yaw), dz, back
    (1, 10, 8, 0, (4, 18), 0.0, 0.0), (40, 14, 10, 2, (-6, 22), 0.0, 0.0), (85, 6, 6, -2, (8, 15), 0.0, 0.01), (130, 12, 10, 1, (-4, 24), 0.0, 0.0),
    (180, 8, 6, 0, (6, 16), 0.0, 0.0), (240, 10, 4, 0, (2, 10), 0.0, 0.0), (330, 9, -2, 0, (-2, 2), 0.004, 0.0),
    (420, 6, -6, 0, (-4, -4), 0.012, 0.01), (520, 3, -8, 0, (-5, -6), 0.02, 0.025), (640, 1, -8, -1, (-4, -6), 0.024, 0.04),
    (800, 0, -9, -1, (-3, -5), 0.026, 0.05), (960, -1, -10, -2, (-2, -5), 0.028, 0.055), (1060, -5, -18, -4, (4, -22), 0.03, 0.075),
    (1200, -6, -16, -3, (2, -18), 0.03, 0.08), (1284, -6, -14, -3, (0, -15), 0.03, 0.08), (1296, -9, -10, -2, (-6, -8), 0.045, 0.1),
    (1330, -4, 4, 2, (6, 8), 0.0, 0.02), (1380, 0, 4, 2, (12, 2), 0.0, 0.02), (1420, 4, 1, 1, (14, -6), 0.0, 0.02),
    (1460, 6, -1, 0, (16, -10), 0.0, 0.0), (1500, 6, -2, -1, (12, -12), 0.005, 0.02), (1530, 5, -3, -1, (10, -14), 0.005, 0.025)]
for f, lean, tw, sd, hd, dz, bk in W_BODY:      # hips stay on the seat: the recoil is in the spine/head (dz -> shoulders via lean)
    ws.body(f, lean=lean, twist=tw, sidebend=sd, head=hd, dz=0.0, back=min(bk, 0.02) * 0.5)
for f in (1, 1290, 1300, 1530):
    ws.feet(f, l_fwd=0.0 if f < 1290 else -0.06, r_fwd=0.02 if f < 1290 else -0.03)
W_FACE = [  # frame, lids, brows, jaw, smile, look(yaw, pitch)
    (1, 0.0, 0.2, 7, 0.9, (14, 0)), (30, -0.1, 0.3, 12, 1.0, (14, 2)), (60, 0.0, 0.2, 4, 0.9, (12, 0)), (95, -1.0, 0.1, 9, 1.0, (12, 0)),
    (102, 0.0, 0.2, 9, 1.0, (12, 0)), (150, 0.0, 0.3, 11, 0.9, (14, 0)), (210, 0.1, 0.2, 5, 0.7, (10, 0)), (300, 0.3, 0.4, 3, 0.4, (0, 0)),
    (380, 0.6, 0.6, 5, 0.1, (-8, 0)), (460, 1.0, 1.0, 10, 0.0, (-10, -2)), (560, 1.0, 1.0, 13, 0.0, (-8, -4)), (700, 1.0, 1.0, 14, 0.0, (-6, -5)),
    (900, 1.0, 1.0, 15, 0.0, (-5, -6)), (975, 1.0, 1.0, 15, 0.0, (-5, -6)), (1010, -0.8, 0.6, 8, 0.0, (-5, -6)), (1150, -0.7, 0.6, 6, 0.0, (0, 0)),
    (1240, 0.8, 0.9, 12, 0.0, (-6, -8)), (1290, 1.0, 1.0, 14, 0.0, (0, -12)), (1330, 0.6, 0.8, 8, 0.0, (8, -18)), (1400, 0.4, 0.8, 5, 0.0, (6, -16)),
    (1440, 0.2, 0.6, 7, 0.0, (2, -8)), (1450, -1.0, 0.6, 7, 0.0, (2, -8)), (1457, 0.2, 0.6, 7, 0.1, (2, -8)), (1500, 0.1, 0.5, 9, 0.25, (-4, -8)), (1530, 0.0, 0.4, 6, 0.35, (-6, -6))]
for f, lids, brows, jaw, smile, look in W_FACE:
    ws.face(f, lids, brows, jaw, smile, look)
# her hands: right (+Y side) and left (-Y side)
cupW = Vector(CUP_C) + Vector((0, 0, sc["cup_top"]))
handle_w = cupW + Matrix.Rotation(R_(35), 3, 'Z') @ Vector((0.082, 0, 0.14))
W_HANDS = {  # frame: (R wrist, R fingers dir, R palm normal), (L ...). Resting hands lie palm-down ON the cloth (table end is 0.53 m in front of her seat)
    1: ((wpt(-0.13, 0.30, -0.10), WF, -UP * 0.98 + WF * 0.2), (wpt(0.12, 0.49, 0.065), WF, -UP)),
    40: ((wpt(-0.13, 0.30, -0.10), WF, -UP * 0.98 + WF * 0.2), (wpt(0.22, 0.38, 0.22), WF + UP, -WL)),
    90: ((wpt(-0.13, 0.30, -0.10), WF, -UP * 0.98 + WF * 0.2), (wpt(0.16, 0.40, 0.15), WF + UP * 0.5, -WL)),
    140: ((wpt(-0.13, 0.30, -0.10), WF, -UP * 0.98 + WF * 0.2), (wpt(0.12, 0.49, 0.065), WF, -UP)),
    300: ((wpt(-0.13, 0.30, -0.10), WF, -UP * 0.98 + WF * 0.2), (wpt(0.12, 0.50, 0.065), WF, -UP)),
    520: ((wpt(-0.13, 0.30, -0.10), WF, -UP * 0.98 + WF * 0.2), (wpt(0.12, 0.49, 0.065), WF, -UP)),
    580: ((wpt(-0.16, 0.50, 0.14), WF, -UP), (wpt(0.18, 0.50, 0.14), WF, -UP)),
    760: ((wpt(-0.17, 0.33, 0.12), WF + UP * 0.6, -WL), (wpt(0.16, 0.32, 0.12), WF + UP * 0.6, WL)),
    870: ((wpt(-0.16, 0.30, 0.18), WF + UP * 0.8, -WL), (wpt(0.15, 0.31, 0.2), WF + UP * 0.8, WL)),
    960: ((wpt(-0.14, 0.28, 0.24), WF + UP, -WL), (wpt(0.13, 0.27, 0.24), WF + UP, WL)),
    1060: ((wpt(-0.14, 0.33, 0.26), UP + WF * 0.4, WF), (wpt(0.13, 0.33, 0.26), UP + WF * 0.4, WF)),
    1170: ((wpt(-0.15, 0.34, 0.25), UP + WF * 0.5, WF), (wpt(0.12, 0.33, 0.24), UP + WF * 0.5, WF)),
    1284: ((wpt(-0.14, 0.33, 0.26), UP + WF * 0.4, WF), (wpt(0.12, 0.33, 0.25), UP + WF * 0.4, WF)),
    1300: ((wpt(-0.16, 0.32, 0.30), UP + WF * 0.2, -WF), (wpt(0.13, 0.37, 0.21), UP + WF * 0.2, -WF)),
    1335: ((wpt(-0.05, 0.30, 0.27), UP + WL * 0.5, -WF), (wpt(0.15, 0.30, 0.12), WF * 0.6 - UP * 0.8, -WF * 0.8 - UP * 0.6)),
    1370: ((wpt(-0.04, 0.29, 0.28), UP + WL * 0.5, -WF), (wpt(0.13, 0.31, -0.08), WF, -UP * 0.98 + WF * 0.2)),
    1420: ((wpt(-0.04, 0.30, 0.26), UP + WL * 0.4, -WF), (wpt(0.13, 0.30, -0.10), WF, -UP * 0.98 + WF * 0.2)),
    1443: ((wpt(-0.09, 0.32, 0.18), WF + WL * 0.2 + UP * 0.2, -UP * 0.6 - WF * 0.4), (wpt(0.13, 0.30, -0.10), WF, -UP * 0.98 + WF * 0.2)),
    1465: ((wpt(-0.13, 0.30, 0.08), WF * 0.6 - UP * 0.8, -WF * 0.8 - UP * 0.6), (wpt(0.12, 0.31, -0.10), WF, -UP * 0.98 + WF * 0.2)),
    1500: ((wpt(-0.13, 0.30, -0.10), WF, -UP * 0.98 + WF * 0.2), (wpt(0.13, 0.30, -0.10), WF, -UP * 0.98 + WF * 0.2)),
    1530: ((wpt(-0.12, 0.31, -0.09), WF, -UP * 0.98 + WF * 0.2), (wpt(0.12, 0.31, -0.09), WF, -UP * 0.98 + WF * 0.2)),
}
W_HANDS[550] = ((wpt(-0.15, 0.27, 0.10), WF + UP * 0.5, -UP + WF * 0.4), (wpt(0.15, 0.495, 0.095), WF, -UP))   # lift off the cloth before the hands rise
for f_ in (360, 420, 470): W_HANDS[f_] = W_HANDS[300]       # dense rest keys: the leaning spine must not drag the resting hand into the cloth
W_HANDS = dict(sorted(W_HANDS.items()))
REST = (1, 140, 300, 360, 420, 470, 520, 550)
for f, (r, l) in W_HANDS.items():
    if f in REST:   # forearms resting on the table: elbows out and up so the palm can lie flat
        ws.hand("R", f, r[0], r[1], r[2]); ws.hand("L", f, l[0], l[1], l[2], elbow_out=0.5, elbow_down=0.02); continue
    ws.hand("R", f, r[0], r[1], r[2])
    if f >= 1370:   # left hand in her lap
        ws.hand("L", f, l[0], l[1], l[2]); continue
    if f >= 1300:   # hand to chest / raised in front: elbow down and out, in front of the body (no arm wrapping over the shoulder)
        ws.hand("L", f, l[0], l[1], l[2], elbow_out=0.35, elbow_down=0.55, elbow_back=-0.05)
    else:
        ws.hand("L", f, l[0], l[1], l[2])
# ---- him: mid-story gesturing, then turns toward the noise, eyes wide, reaches toward her in slow motion; real time: half-rises,
#      leans across the corner and takes her forearm
F_BODY = [(1, 8, -10, 0, (2, -24), 0.0, 0.0), (45, 12, -14, -2, (-4, -28), 0.0, 0.0), (95, 6, -8, 1, (6, -20), 0.0, 0.01),
          (150, 10, -12, 0, (-2, -26), 0.0, 0.0), (220, 8, -6, 0, (2, -18), 0.0, 0.0), (330, 9, 4, 0, (0, 8), 0.0, 0.0),
          (450, 12, 14, 2, (-4, 32), 0.01, 0.0), (600, 18, 10, 3, (-2, 22), 0.015, -0.03), (800, 22, 4, 4, (-4, 8), 0.02, -0.05),
          (973, 24, -2, 5, (-6, -6), 0.025, -0.06), (1150, 24, -8, 5, (-6, -16), 0.03, -0.065), (1284, 24, -10, 5, (-6, -20), 0.03, -0.065),
          (1298, 16, -6, 3, (-8, -14), 0.05, -0.04), (1330, 30, -4, 4, (12, -16), 0.24, -0.18), (1380, 40, 6, 2, (20, -6), 0.32, -0.26),
          (1430, 40, 8, 2, (22, -4), 0.34, -0.28), (1480, 34, 6, 2, (14, -12), 0.34, -0.26), (1530, 30, 4, 2, (8, -22), 0.34, -0.24)]
for f, lean, tw, sd, hd, dz, bk in F_BODY:
    fs.body(f, lean=lean, twist=tw, sidebend=sd, head=hd, dz=dz, back=bk)
for f in (1, 1298, 1330, 1530):
    fs.feet(f, l_fwd=0.0 if f < 1330 else 0.03, r_fwd=0.0 if f < 1330 else 0.06, spread=0.03 if f >= 1330 else 0.0)
F_FACE = [(1, 0.0, 0.4, 9, 0.5, (-14, 0)), (40, 0.0, 0.5, 4, 0.6, (-14, 0)), (80, -1.0, 0.3, 10, 0.6, (-12, 0)), (87, 0.0, 0.4, 10, 0.6, (-12, 0)),
          (140, 0.0, 0.6, 12, 0.5, (-14, 2)), (230, 0.1, 0.3, 4, 0.4, (-10, 0)), (330, 0.4, 0.6, 4, 0.1, (12, 0)), (450, 1.0, 1.0, 9, 0.0, (16, -2)),
          (620, 1.0, 1.0, 16, 0.0, (6, -4)), (973, 1.0, 1.0, 18, 0.0, (-8, -6)), (1150, 0.9, 1.0, 18, 0.0, (-10, -6)), (1290, 1.0, 1.0, 20, 0.0, (-12, -10)),
          (1340, 0.6, 0.9, 10, 0.0, (-14, -8)), (1420, 0.3, 0.8, 6, 0.0, (-16, -6)), (1500, 0.2, 0.7, 4, 0.1, (-16, -6)), (1530, 0.1, 0.6, 4, 0.15, (-16, -6))]
for f, lids, brows, jaw, smile, look in F_FACE:
    fs.face(f, lids, brows, jaw, smile, look)
her_forearm = lambda: wpt(0.13, 0.33, 0.19)
F_HANDS = {  # his table edge is 0.69 m in front of his seat: resting hands at ly ~0.73, palm down
    1: ((fpt(-0.2, 0.42, 0.2), FF + UP * 0.6, -FL), (fpt(-0.04, 0.73, 0.085), FF, -UP)),
    40: ((fpt(-0.24, 0.40, 0.3), FF + UP, -FL), (fpt(-0.04, 0.73, 0.085), FF, -UP)),
    95: ((fpt(-0.16, 0.50, 0.12), FF + UP * 0.3, -FL), (fpt(-0.04, 0.73, 0.085), FF, -UP)),
    150: ((fpt(-0.26, 0.40, 0.32), FF + UP, -FL), (fpt(-0.04, 0.73, 0.085), FF, -UP)),
    260: ((fpt(-0.2, 0.55, 0.14), FF + UP * 0.3, -FL), (fpt(-0.04, 0.73, 0.085), FF, -UP)),
    300: ((fpt(-0.19, 0.68, 0.16), FF, -UP), (fpt(-0.04, 0.73, 0.085), FF, -UP)),
    330: ((fpt(-0.23, 0.73, 0.11), FF, -UP), (fpt(-0.04, 0.73, 0.11), FF, -UP)),
    390: ((fpt(-0.22, 0.72, 0.11), FF, -UP), (fpt(-0.04, 0.73, 0.11), FF, -UP)),
    450: ((fpt(-0.20, 0.70, 0.11), FF, -UP), (fpt(-0.04, 0.73, 0.11), FF, -UP)),
    490: ((fpt(-0.18, 0.64, 0.21), FF - FL * 0.3 + UP * 0.2, -UP), (fpt(-0.04, 0.73, 0.11), FF, -UP)),
    600: ((fpt(-0.31, 0.62, 0.17), FF - FL * 0.6, -UP - FL * 0.4), (fpt(-0.04, 0.73, 0.085), FF, -UP)),
    800: ((fpt(-0.33, 0.70, 0.23), FF - FL * 0.8 + UP * 0.3, -UP - FL * 0.5), (fpt(-0.04, 0.73, 0.085), FF, -UP)),
    1000: ((fpt(-0.31, 0.69, 0.24), FF - FL + UP * 0.3, -UP - FL * 0.5), (fpt(-0.04, 0.74, 0.085), FF, -UP)),
    1284: ((fpt(-0.33, 0.71, 0.24), FF - FL + UP * 0.3, -UP - FL * 0.5), (fpt(-0.04, 0.74, 0.085), FF, -UP)),
    1298: ((fpt(-0.32, 0.70, 0.26), FF - FL + UP * 0.3, -UP - FL * 0.5), (fpt(0.15, 0.75, 0.085), FF, -UP)),
    1340: ((fpt(-0.30, 0.62, 0.22), FF - FL * 0.6 + UP * 0.2, -UP - FL * 0.5), (fpt(0.06, 0.78, 0.12), FF, -UP)),
    1530: ((fpt(-0.30, 0.62, 0.22), FF, -UP), (fpt(0.04, 0.78, 0.12), FF, -UP)),
}
F_ELB = dict(elbow_out=0.45, elbow_down=0.35, elbow_back=0.2)     # reaching arm: elbow out and down, never locked straight
for f, (r, l) in F_HANDS.items():
    if f >= 600 and f <= 1298: fs.hand("R", f, r[0], r[1], r[2], **F_ELB)
    elif f == 1530: pass                                  # 1385-1530: the grip below keys the right hand on the handle
    else: fs.hand("R", f, r[0], r[1], r[2])
    fs.hand("L", f, l[0], l[1], l[2])
# his right hand takes the tumbler by the handle (1385) and lifts it toward himself to look at the dent; the cup only moves in his hand
HANDLE = bpy.data.objects["Tumbler_Handle"]
G_FR = [1385, 1400, 1420, 1440, 1460, 1480, 1505, 1530]
CUP_LIFT = {1400: (Vector((0, 0, 0)), 0.0), 1440: (Vector((-0.01, -0.03, 0.035)), -6.0), 1480: (Vector((-0.025, -0.07, 0.09)), -14.0),
            1530: (Vector((-0.035, -0.10, 0.12)), -20.0)}
sc.frame_set(1400); c_rest = CUP.location.copy(); rz0 = CUP.rotation_euler.z
for f, (off, rz) in CUP_LIFT.items():
    CUP.location = c_rest + off; CUP.keyframe_insert("location", frame=f)
    CUP.rotation_euler.z = rz0 + R_(rz); CUP.keyframe_insert("rotation_euler", frame=f)
def handle_frame(f):
    sc.frame_set(f); M = HANDLE.matrix_world.copy()
    h = M.to_3x3() @ Vector((1, 0, 0)); h.z = 0; h.normalize()
    return M, h, M @ Vector((0.0895, 0.0, 0.14))
for f in [1360] + G_FR:     # wrist / elbow pole first (fs.hand), the exact grip is solved after the finger schedule
    M, h, c = handle_frame(f)
    fd = UP.cross(h)
    fs.hand("R", f, c + h * 0.03 - fd * 0.06 + (Vector((0, -0.08, 0.06)) if f == 1360 else Vector()), fd, -h, elbow_out=0.4, elbow_down=0.3, elbow_back=0.1)

# ---- fingers: shared pose library (pipeline/hand_poses.py, director 14:59) instead of hand-set angles
exec(open(os.path.join(PIPE, "hand_poses.py")).read())
for rig_ in (W_RIG, F_RIG): add_hand_limits(rig_)
# wrist limit: the IK chain carries no forearm twist, so the wrist must take the pronation (50-180 deg about the bone axis).
# Clamping that twist in XYZ order gimbal-flips the hand (a 180-degree pop); YXZ puts the gimbal on flexion (clamped to 60) and leaves twist free.
for rig_ in (W_RIG, F_RIG):
    for s_ in "LR":
        c_ = rig_.pose.bones["wrist." + s_].constraints["HandLimit"]; c_.euler_order = 'YXZ'; c_.use_limit_y = False
HAND_SCHEDULE = {
    (W_RIG, "R"): [(1, "relaxed"), (600, "relaxed"), (700, "open_alarm"), (1290, "open_alarm"), (1330, "relaxed"), (1420, "relaxed"), (1530, "relaxed")],
    (W_RIG, "L"): [(1, "relaxed"), (40, "relaxed"), (140, "relaxed"), (600, "relaxed"), (700, "open_alarm"), (1285, "open_alarm"), (1320, "relaxed"), (1345, "relaxed")],
    (F_RIG, "R"): [(1, "shield"), (260, "shield"), (330, "flat_palm"), (450, "flat_palm"), (560, "relaxed"), (700, "open_alarm"), (1298, "open_alarm"), (1340, "relaxed"), (1360, "shield")],
    (F_RIG, "L"): [(1, "flat_palm"), (1530, "flat_palm")],
}
for (rig_, side_), sched in HAND_SCHEDULE.items():
    for f_, pose_ in sched: apply_pose(rig_, side_, pose_, f_)

# ---- resting hands: the library places the palm ON the cloth (palm normal toward the table), flat palm pose
def _lift_off_table(rig_, side_, f_):
    """the wrist limit can tip a flat hand forward: raise IK_hand until no finger bone is below the cloth (tips touch it)"""
    pb = rig_.pose.bones["IK_hand." + side_]; Mi = rig_.data.bones["IK_hand." + side_].matrix_local.to_3x3().inverted() @ rig_.matrix_world.inverted().to_3x3()
    for _ in range(3):
        sc.frame_set(f_); Mw = rig_.matrix_world
        zs = [(Mw @ rig_.pose.bones["finger%d-%d.%s" % (k, j, side_)].tail).z for k in range(1, 6) for j in (1, 2, 3)]
        lack = TOP + 0.007 - min(zs)
        if lack <= 0.001: break
        pb.location = pb.location + Mi @ Vector((0, 0, lack)); pb.keyframe_insert("location", frame=f_, group=pb.name)
    print("LIFT", rig_.name, side_, f_, round(TOP + 0.007 - min(zs), 4))
def _rest_on_table(rig_, side_, frames_, keyset, base_fn):
    for f_ in frames_:
        key = keyset[f_][0 if side_ == "R" else 1]
        w_, d_, n_ = key
        if (n_ + UP).length > 1e-6: continue          # only the palm-down table keys
        sc.frame_set(f_); Mw_ = rig_.matrix_world; la = rig_.pose.bones["lowerarm02." + side_]
        fa = (Mw_ @ la.tail) - (Mw_ @ la.head); fa.z = 0.0
        if fa.length > 1e-4: d_ = (d_.normalized() * 0.3 + fa.normalized() * 0.7)   # fingers follow the forearm: no wrist yaw for the limit to clamp
        d_ = Vector((d_.x, d_.y, 0.0)).normalized()
        p_ = Vector((w_.x, w_.y, TOP + (0.018 if rig_ is W_RIG else 0.0))) + d_ * 0.07
        place_hand(rig_, side_, f_, p_, Vector((0, 0, -1)), d_)
        apply_pose(rig_, side_, "flat_palm", f_)
        _lift_off_table(rig_, side_, f_)
_rest_on_table(W_RIG, "L", [f for f in W_HANDS if f in REST], W_HANDS, wpt)
_rest_on_table(F_RIG, "L", list(F_HANDS), F_HANDS, fpt)
_rest_on_table(F_RIG, "R", [330, 390, 450], F_HANDS, fpt)
F_LREST = {500: F_HANDS[450], 550: F_HANDS[450], 1315: F_HANDS[1298], 1380: F_HANDS[1340], 1420: F_HANDS[1340], 1440: F_HANDS[1340], 1480: F_HANDS[1340]}
for f_, (r_, l_) in F_LREST.items(): fs.hand("L", f_, l_[0], l_[1], l_[2])
_rest_on_table(F_RIG, "L", list(F_LREST), F_LREST, fpt)
# exact handle grip (library): palm on the outside of the handle bar facing the cup, fingers wrap through the loop, thumb on top
_tmp = bpy.data.objects.new("_grip_tmp", bpy.data.meshes.new_from_object(HANDLE.evaluated_get(bpy.context.evaluated_depsgraph_get())))
sc.collection.objects.link(_tmp)
for f in G_FR:
    M, h, c = handle_frame(f); _tmp.matrix_world = M
    rep_ = grip_object(F_RIG, "R", f, _tmp, c, -h, finger_dir=UP.cross(h))
    print("GRIP", f, rep_)
bpy.data.objects.remove(_tmp)
# twist cap: a hand key that asks for more than 110 deg of forearm twist is turned back about the forearm axis (the arm itself is
# unchanged: IK uses only the target location and pole). Keeps every hand away from the 180-degree flip point.
def _twist(rig_, s_):
    la = rig_.pose.bones["lowerarm02." + s_]; ik = rig_.pose.bones["IK_hand." + s_]
    Rl = la.matrix.to_3x3() @ (rig_.data.bones["lowerarm02." + s_].matrix_local.to_3x3().inverted() @ rig_.data.bones["wrist." + s_].matrix_local.to_3x3())
    q = (Rl.inverted() @ ik.matrix.to_3x3()).to_quaternion()
    return (math.degrees(2 * math.atan2(q.y, q.w)) + 180) % 360 - 180, Rl
CAP = 110.0
for rig_ in (W_RIG, F_RIG):
    fcs = rig_.animation_data.action.fcurves if hasattr(rig_.animation_data.action, "fcurves") else None
    for s_ in "LR":
        pb = rig_.pose.bones["IK_hand." + s_]; path = 'pose.bones["IK_hand.%s"].rotation_quaternion' % s_
        frames = sorted({int(round(k.co.x)) for fc in (fcs or []) if fc.data_path == path for k in fc.keyframe_points})
        if not frames:
            frames = sorted({int(round(k.co.x)) for lay in getattr(rig_.animation_data.action, "layers", []) for st in lay.strips
                             for cb in st.channelbags for fc in cb.fcurves if fc.data_path == path for k in fc.keyframe_points})
        n_fix = 0; prevq = None; turned = []
        keep = {(W_RIG, "L"): set(REST), (F_RIG, "L"): set(F_HANDS) | set(F_LREST), (F_RIG, "R"): {330, 390, 450} | set(G_FR)}.get((rig_, s_), set())
        for f_ in frames:
            if f_ in keep: continue          # table rests and the handle grip were placed by contact: leave them
            sc.frame_set(f_); tw, Rl = _twist(rig_, s_)
            if abs(tw) > CAP:
                ex = math.radians(tw - math.copysign(CAP, tw))
                ax = (Rl @ Vector((0, 1, 0))).normalized()                   # forearm-aligned wrist axis, armature space
                M = pb.matrix.copy(); R3 = Matrix.Rotation(-ex, 3, ax) @ M.to_3x3()
                pb.matrix = Matrix.Translation(M.translation) @ R3.to_4x4()
                q = pb.rotation_quaternion.copy()
                if prevq is not None and q.dot(prevq) < 0: q.negate()
                pb.rotation_quaternion = q; pb.keyframe_insert("rotation_quaternion", frame=f_, group=pb.name); n_fix += 1; turned.append((f_, round(tw)))
            prevq = pb.rotation_quaternion.copy()
        print("TWIST_CAP", rig_.name, s_, len(frames), "keys,", n_fix, "turned", turned)
# dust motes that drift through a head are hidden (a mote inside the face reads as a stuck prop)
_motes = [o for o in bpy.data.objects if o.name.startswith("DustMote")]
for f in range(1, END + 1, 5):
    sc.frame_set(f); hs = [r_.matrix_world @ r_.pose.bones["head"].center for r_ in (W_RIG, F_RIG)]
    for o in _motes:
        if not o.hide_render and any((o.matrix_world.translation - hp).length < 0.2 for hp in hs):
            o.hide_render = True; o.hide_viewport = True; print("MOTE_HIDDEN", o.name, f)
