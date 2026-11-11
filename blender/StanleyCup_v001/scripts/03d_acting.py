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
    (1330, 14, 8, 4, (28, 18), 0.0, 0.02), (1380, 18, 10, 5, (32, 22), -0.005, 0.0), (1420, 10, 4, 2, (16, 10), 0.0, 0.02),
    (1460, 14, 2, 0, (18, 4), 0.0, 0.0), (1500, 8, 0, -1, (10, 0), 0.005, 0.02), (1530, 6, -2, -1, (6, -4), 0.005, 0.025)]
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
W_HANDS = {  # frame: (R wrist, R fingers dir, R back-of-hand normal), (L ...)
    1: ((wpt(-0.18, 0.42, 0.02), WF, UP), (wpt(0.2, 0.4, 0.02), WF, UP)),
    40: ((wpt(-0.18, 0.43, 0.02), WF, UP), (wpt(0.22, 0.30, 0.22), WF + UP, -WL)),
    90: ((wpt(-0.17, 0.42, 0.02), WF, UP), (wpt(0.16, 0.34, 0.15), WF + UP * 0.5, -WL)),
    140: ((wpt(-0.18, 0.42, 0.02), WF, UP), (wpt(0.2, 0.36, 0.05), WF, UP)),
    300: ((wpt(-0.18, 0.43, 0.02), WF, UP), (wpt(0.2, 0.40, 0.02), WF, UP)),
    520: ((wpt(-0.17, 0.40, 0.03), WF, UP), (wpt(0.19, 0.38, 0.03), WF, UP)),
    760: ((wpt(-0.17, 0.33, 0.12), WF + UP * 0.6, -WL), (wpt(0.16, 0.32, 0.12), WF + UP * 0.6, WL)),
    960: ((wpt(-0.14, 0.28, 0.24), WF + UP, -WL), (wpt(0.13, 0.27, 0.24), WF + UP, WL)),
    1060: ((wpt(-0.13, 0.2, 0.33), UP + WF * 0.4, -WF), (wpt(0.12, 0.2, 0.33), UP + WF * 0.4, -WF)),
    1284: ((wpt(-0.13, 0.21, 0.32), UP + WF * 0.4, -WF), (wpt(0.12, 0.21, 0.32), UP + WF * 0.4, -WF)),
    1300: ((wpt(-0.15, 0.17, 0.36), UP + WF * 0.2, -WF), (wpt(0.14, 0.17, 0.36), UP + WF * 0.2, -WF)),
    1360: ((wpt(-0.18, 0.34, 0.10), WF, -WL), (wpt(0.03, 0.13, 0.31), -WL + UP * 0.2, -WF)),
    1420: ((wpt(-0.17, 0.40, 0.06), WF, UP), (wpt(0.03, 0.12, 0.30), -WL + UP * 0.2, -WF)),
    1447: ((handle_w + Vector((0.035, 0.035, 0.0)), (handle_w - Vector((0.01, 0.01, 0))) - wpt(-0.17, 0.30, 0.15), UP), (wpt(0.03, 0.12, 0.30), -WL + UP * 0.2, -WF)),
}
for f, (r, l) in W_HANDS.items():
    ws.hand("R", f, r[0], r[1], r[2]); ws.hand("L", f, l[0], l[1], l[2])
# grip: from f1452 the tumbler follows her right hand (child-of constraint keyed on)
# her grip on the handle (fingers curl) and the lift: the cup follows the hand from f1452
def curl(R, s, f, amt, thumb=None):
    for k in range(2, 6):
        for j in range(1, 4):
            R.key_rot("finger%d-%d.%s" % (k, j, s), f, [("X", amt * (55 if j == 1 else 70))])
    t = amt if thumb is None else thumb
    for j in range(1, 4): R.key_rot("finger1-%d.%s" % (j, s), f, [("Z", (-1 if s == "L" else 1) * 25 * t)])
for f, a in ((1, 0.15), (1440, 0.15), (1452, 0.9), (1530, 0.9)): curl(RW, "R", f, a)
for f, a in ((1, 0.15), (1300, 0.4), (1360, 0.2), (1530, 0.25)): curl(RW, "L", f, a, 0.1)
CUP_LIFT = [(1452, Vector((0, 0, 0))), (1478, Vector((0.02, 0.015, 0.018))), (1530, Vector((0.10, 0.07, 0.09)))]
c_rest = CUP.location.copy()       # (after the skid keys, this is the final skid position from 03b)
sc.frame_set(1452); c_rest = CUP.matrix_world.translation.copy()
r_wr = W_HANDS[1447][0][0]; r_d = W_HANDS[1447][0][1]
for f, off in CUP_LIFT:
    CUP.location = c_rest + off; CUP.keyframe_insert("location", frame=f)
    ws.hand("R", f, r_wr + off, r_d, UP)
# ---- him: mid-story gesturing, then turns toward the noise, eyes wide, reaches toward her in slow motion; real time: half-rises,
#      leans across the corner and takes her forearm
F_BODY = [(1, 8, -10, 0, (2, -24), 0.0, 0.0), (45, 12, -14, -2, (-4, -28), 0.0, 0.0), (95, 6, -8, 1, (6, -20), 0.0, 0.01),
          (150, 10, -12, 0, (-2, -26), 0.0, 0.0), (220, 8, -6, 0, (2, -18), 0.0, 0.0), (330, 9, 4, 0, (0, 8), 0.0, 0.0),
          (450, 12, 14, 2, (-4, 32), 0.01, 0.0), (600, 18, 10, 3, (-2, 22), 0.015, -0.03), (800, 22, 4, 4, (-4, 8), 0.02, -0.05),
          (973, 24, -2, 5, (-6, -6), 0.025, -0.06), (1150, 24, -8, 5, (-6, -16), 0.03, -0.065), (1284, 24, -10, 5, (-6, -20), 0.03, -0.065),
          (1298, 16, -6, 3, (-8, -14), 0.05, -0.04), (1330, 26, -16, 8, (10, -30), 0.16, -0.14), (1380, 30, -22, 10, (14, -34), 0.22, -0.2),
          (1430, 28, -24, 10, (8, -38), 0.22, -0.2), (1480, 26, -26, 9, (4, -40), 0.21, -0.21), (1530, 24, -26, 9, (2, -40), 0.21, -0.21)]
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
her_forearm = lambda: wpt(0.13, 0.25, 0.26)
F_HANDS = {
    1: ((fpt(-0.2, 0.42, 0.2), FF + UP * 0.6, -FL), (fpt(0.2, 0.40, 0.02), FF, UP)),
    40: ((fpt(-0.24, 0.36, 0.3), FF + UP, -FL), (fpt(0.2, 0.41, 0.02), FF, UP)),
    95: ((fpt(-0.16, 0.44, 0.12), FF + UP * 0.3, -FL), (fpt(0.2, 0.41, 0.02), FF, UP)),
    150: ((fpt(-0.26, 0.34, 0.32), FF + UP, -FL), (fpt(0.2, 0.40, 0.02), FF, UP)),
    260: ((fpt(-0.2, 0.42, 0.03), FF, UP), (fpt(0.2, 0.40, 0.02), FF, UP)),
    500: ((fpt(-0.3, 0.46, 0.12), FF - FL * 0.5, UP), (fpt(0.2, 0.40, 0.02), FF, UP)),
    800: ((fpt(-0.45, 0.55, 0.2), FF - FL * 0.8 + UP * 0.2, UP), (fpt(0.18, 0.42, 0.02), FF, UP)),
    1284: ((fpt(-0.55, 0.6, 0.24), FF - FL + UP * 0.2, UP), (fpt(0.18, 0.42, 0.02), FF, UP)),
    1298: ((fpt(-0.5, 0.55, 0.22), FF - FL + UP * 0.2, UP), (fpt(0.16, 0.45, 0.03), FF, UP)),
    1340: ((fpt(-0.48, 0.62, 0.02), FF - FL, UP), (fpt(0.05, 0.5, 0.02), FF, UP)),
    1400: ((her_forearm() + Vector((0.0, -0.05, 0.0)), -FL + UP * 0.2, FF), (fpt(0.02, 0.5, 0.02), FF, UP)),
    1530: ((her_forearm() + Vector((0.0, -0.04, -0.01)), -FL + UP * 0.2, FF), (fpt(0.02, 0.5, 0.02), FF, UP)),
}
for f, (r, l) in F_HANDS.items():
    fs.hand("R", f, r[0], r[1], r[2]); fs.hand("L", f, l[0], l[1], l[2])
for f, a in ((1, 0.15), (40, 0.05), (95, 0.3), (150, 0.05), (260, 0.2), (500, 0.05), (1284, 0.1), (1340, 0.3), (1400, 0.75), (1530, 0.8)):
    curl(RF, "R", f, a)
for f, a in ((1, 0.2), (1530, 0.2)): curl(RF, "L", f, a)
