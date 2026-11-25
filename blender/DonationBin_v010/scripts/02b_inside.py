# DonationBin v010 stage B part 2 (exec'd by 02_animate.py): the woman inside the bin (451-1993), her exit (1993-2388),
# the passer-by, the firefighters. Inside the bin she always faces the FRONT wall (-Y): her left is +X, her right is -X.
FI = BY0 + 0.012 + 0.009            # the flap's inner face (closed): y
WI = BY0 + T                         # the front wall's inner face: y
def hz(x, y): return heap(x, y)
def stand_at(x, y, bend=0.02): return Vector((x, y, max(hz(x - 0.1, y), hz(x + 0.1, y)) + 0.777 - bend))
def feet_on_heap(A, f, x, y, dy_l=0.0, dy_r=0.0, tip=0.0, yaw=0.0):
    """both feet planted ON the heap around (x, y), toes toward the front wall (-Y) rotated by yaw"""
    fw = Vector((math.sin(R_(yaw)), -math.cos(R_(yaw)), 0)); lf = Vector((math.cos(R_(yaw)), math.sin(R_(yaw)), 0))
    d = {}
    for s, sx, dy in (("L", 1, dy_l), ("R", -1, dy_r)):
        p = Vector((x, y, 0)) + lf * sx * 0.10 + fw * dy
        up = Vector((0, 0, 1)); toe = fw.copy()
        if tip:
            up = (up * math.cos(R_(tip)) - fw * math.sin(R_(tip))).normalized(); toe = (fw * math.cos(R_(tip)) + Vector((0, 0, 1)) * -math.sin(R_(tip))).normalized()
        d["foot_" + s] = WH((p.x, p.y, hz(p.x, p.y) + 0.064 + (0.05 if tip else 0.0)), up, toe)
    A.key(f, **d)
FRONT = Vector((0, -1, 0))
def on_flap(x, z): return WH((x, FI, z), (0, -1, 0), (0.0, 0, 1))
def on_wall_front(x, z, fd=(0, 0, 1)): return WH((x, WI, z), (0, -1, 0), fd)

# D (451-673): she gets up (kneel, half-kneel, stand) and pushes the flap with both palms: it will not swing out
K1 = Vector((0.0, 0.02, 0.0)); K1.z = hz(0, 0.02) + 0.43
W.key(485, pos=K1, rot=Rf(FRONT, lean=12), spine=(10, 0, 0), head=(-10, 0, 0),
      hand_L=WH((0.22, -0.20, hz(0.22, -0.20)), (0, 0, -1), (0, -1, 0)), hand_R=WH((-0.22, -0.20, hz(-0.22, -0.20)), (0, 0, -1), (0, -1, 0)),
      foot_L=WH((0.10, 0.40, hz(0.10, 0.40) + 0.05), (0, -0.2, 1), (0, 1, -0.3)), foot_R=WH((-0.10, 0.40, hz(-0.10, 0.40) + 0.05), (0, -0.2, 1), (0, 1, -0.3)),
      knee_L=WH((0.2, -1.0, 0.3), (0, 0, 1), (0, 0, 1)), knee_R=WH((-0.2, -1.0, 0.3), (0, 0, 1), (0, 0, 1)), grip_L="relaxed", grip_R="relaxed")
K2 = Vector((0.0, -0.05, 0.0)); K2.z = hz(0, -0.05) + 0.52
W.key(520, pos=K2, rot=Rf(FRONT, lean=18), spine=(8, 0, 0), head=(-15, 0, 0),
      hand_L=LH((0.20, -0.25, -0.05), (0, 0, -1), (0, -1, 0)), hand_R=hang(-1, 0.1),
      foot_L=WH((0.11, -0.32, hz(0.11, -0.32) + 0.064), (0, 0, 1), (0, -1, 0)), foot_R=WH((-0.10, 0.36, hz(-0.10, 0.36) + 0.05), (0, -0.2, 1), (0, 1, -0.3)))
SP = stand_at(0.0, -0.24)
W.key(555, pos=SP + Vector((0, 0.03, -0.02)), rot=Rf(FRONT, lean=6), spine=(4, 0, 0), head=(-18, 0, 0), hand_L=hang(1), hand_R=hang(-1),
      knee_L=LH((0.16, -0.75, -0.25), (0, 0, 1), (0, 0, 1)), knee_R=LH((-0.16, -0.75, -0.25), (0, 0, 1), (0, 0, 1)))
feet_on_heap(W, 555, 0.0, -0.26, dy_l=0.0, dy_r=0.04)
W.key(585, pos=SP, rot=Rf(FRONT, lean=8), spine=(4, 0, 0), head=(-20, 0, 0),
      hand_L=LH((0.20, -0.30, 0.40), (0, -1, 0), (0, 0, 1)), hand_R=LH((-0.20, -0.30, 0.40), (0, -1, 0), (0, 0, 1)), grip_L="flat_palm", grip_R="flat_palm")
feet_on_heap(W, 600, 0.0, -0.27, dy_l=0.02, dy_r=-0.04)
for f, lean, zl, zr in ((600, 10, 1.46, 1.50), (618, 15, 1.44, 1.48), (632, 6, 1.46, 1.50), (648, 16, 1.43, 1.47), (662, 6, 1.46, 1.50), (673, 13, 1.45, 1.49)):
    W.key(f, pos=SP + Vector((0, -0.01 * (lean - 6) / 10, 0)), rot=Rf(FRONT, lean=lean), spine=(4 + lean * 0.3, 0, 0), head=(-12, 0, 0),
          hand_L=on_flap(0.18, zl), hand_R=on_flap(-0.18, zr), face=(0.0, 0.25 if lean > 10 else 0.05, -0.6, 0.3))
# E (673-847): the latch holds; she gives up for a moment
for f, lean in ((700, 14), (722, 6), (740, 15)):
    W.key(f, pos=SP + Vector((0, -0.01 * (lean - 6) / 10, 0)), rot=Rf(FRONT, lean=lean), spine=(5 + lean * 0.3, 0, 0), head=(-10, 0, 0),
          hand_L=on_flap(0.18, 1.45), hand_R=on_flap(-0.18, 1.49))
W.key(770, pos=SP + Vector((0, 0.04, -0.01)), rot=Rf(FRONT, lean=2), spine=(10, 0, 0), head=(18, 0, 0),
      hand_L=on_flap(0.16, 1.32), hand_R=on_flap(-0.16, 1.34), face=(0.0, 0.0, -0.8, 0.2))
W.key(800, pos=SP + Vector((0, 0.07, -0.015)), rot=Rf(FRONT, lean=0), spine=(14, 0, 0), head=(22, 0, 0), hand_L=hang(1, 0.05), hand_R=hang(-1, 0.05), grip_L="relaxed", grip_R="relaxed")
feet_on_heap(W, 800, 0.0, -0.22, dy_l=0.0, dy_r=-0.02)
W.key(830, pos=SP + Vector((0, 0.06, -0.01)), rot=Rf(FRONT, lean=0), spine=(6, 0, 0), head=(-15, 8, 0), face=(0.0, 0.0, 0.6, 0.0))
# F (847-1285): no handle (palms over the flap), no latch (fingers along its edges), smooth walls, too high to climb
SP2 = stand_at(0.0, -0.27)
feet_on_heap(W, 850, 0.0, -0.27, dy_l=0.02, dy_r=-0.02)
for f, (xl, zl), (xr, zr) in ((852, (0.26, 1.55), (-0.26, 1.50)), (868, (0.10, 1.36), (-0.12, 1.60)), (884, (0.34, 1.32), (-0.34, 1.42)), (900, (0.20, 1.58), (-0.08, 1.33))):
    W.key(f, pos=SP2, rot=Rf(FRONT, lean=8), spine=(5, 0, 0), head=(-14, 4 * math.sin(f), 0), hand_L=on_flap(xl, zl), hand_R=on_flap(xr, zr),
          grip_L="flat_palm", grip_R="flat_palm", face=(0.0, 0.05, 0.4, 0.0))
for f, z in ((915, 1.30), (935, 1.50), (955, 1.62)):
    W.key(f, pos=SP2, rot=Rf(FRONT, lean=7), spine=(5, 0, 0), head=(-16, 0, 0),
          hand_L=WH((0.44, FI, z), (0, -1, 0), (0, 0, 1)), hand_R=WH((-0.44, FI, z), (0, -1, 0), (0, 0, 1)), grip_L="relaxed", grip_R="relaxed")
# she moves to her RIGHT (-X) along the front wall and pats it, then the side wall near the corner
SP3 = stand_at(-0.32, -0.27)
feet_on_heap(W, 990, -0.32, -0.27, dy_l=-0.02, dy_r=0.02, yaw=-12)
W.key(990, pos=SP3, rot=Rf((-0.2, -1, 0), lean=6), spine=(4, -8, 0), head=(-10, -15, 0),
      hand_R=on_wall_front(-0.66, 1.30), hand_L=on_wall_front(-0.38, 1.85), grip_L="flat_palm", grip_R="flat_palm")
W.key(1030, pos=SP3, rot=Rf((-0.2, -1, 0), lean=6), spine=(4, -8, 0), head=(-25, -18, 0), hand_R=on_wall_front(-0.70, 1.62), hand_L=on_wall_front(-0.48, 1.55))
W.key(1070, pos=SP3 + Vector((-0.04, 0, 0)), rot=Rf((-0.5, -1, 0), lean=6), spine=(4, -14, 0), head=(-15, -30, 0),
      hand_R=WH((IX0, -0.52, 1.25), (-1, 0, 0), (0, 0, 1)), hand_L=WH((IX0, -0.60, 1.70), (-1, 0, 0), (0, 0.2, 1)))
W.key(1110, pos=SP3 + Vector((-0.04, 0, 0)), rot=Rf((-0.5, -1, 0), lean=6), spine=(4, -14, 0), head=(-10, -28, 0),
      hand_R=WH((IX0, -0.48, 1.45), (-1, 0, 0), (0, 0, 1)), hand_L=WH((IX0, -0.62, 1.50), (-1, 0, 0), (0, 0.2, 1)))
# too high to climb: back to the centre, reaches up the front wall above the flap on tiptoe, looks up at the roof
SP4 = stand_at(0.02, -0.33)
W.key(1145, pos=SP4, rot=Rf(FRONT, lean=4), spine=(-4, 0, 0), head=(-35, 0, 0), hand_L=on_wall_front(0.22, 1.86), hand_R=on_wall_front(-0.20, 1.84))
feet_on_heap(W, 1145, 0.02, -0.33)
W.key(1185, pos=SP4 + Vector((0, 0, 0.05)), rot=Rf(FRONT, lean=3), spine=(-8, 0, 0), head=(-45, 0, 0), hand_L=on_wall_front(0.20, 2.00), hand_R=on_wall_front(-0.18, 1.98),
      face=(0.0, 0.2, 0.8, 0.0))
feet_on_heap(W, 1185, 0.02, -0.33, tip=28)
W.key(1225, pos=SP4 + Vector((0, 0, 0.05)), rot=Rf(FRONT, lean=3), spine=(-8, 0, 0), head=(-42, 6, 0), hand_L=on_wall_front(0.21, 2.01), hand_R=on_wall_front(-0.17, 1.99))
feet_on_heap(W, 1225, 0.02, -0.33, tip=28)
W.key(1262, pos=SP4, rot=Rf(FRONT, lean=6), spine=(2, 0, 0), head=(-10, 0, 0), hand_L=on_flap(0.18, 1.52), hand_R=on_flap(-0.18, 1.55), face=(0.0, 0.0, -0.4, 0.0))
feet_on_heap(W, 1262, 0.02, -0.33)
# G (1285-1465): she screams for help and slaps the flap; then she listens: nothing
for f, touch in ((1288, False), (1298, True), (1310, False), (1320, True), (1332, False), (1342, True), (1356, False), (1366, True)):
    hl = on_flap(0.17, 1.50) if touch else LH((0.20, -0.30, 0.48), (0, -1, 0), (0, 0, 1))
    hr = on_flap(-0.17, 1.53) if touch else LH((-0.20, -0.30, 0.50), (0, -1, 0), (0, 0, 1))
    W.key(f, pos=SP4 + Vector((0, 0.0 if touch else 0.02, 0)), rot=Rf(FRONT, lean=10 if touch else 4), spine=(6, 0, 0), head=(-22, 0, 0),
          hand_L=hl, hand_R=hr, face=(0.0, 0.85, 0.9, 0.2))
W.key(1385, pos=SP4, rot=Rf(FRONT, lean=6), spine=(4, 0, 0), head=(-12, 22, 8), hand_L=on_flap(0.17, 1.46), hand_R=on_flap(-0.17, 1.48), face=(0.0, 0.1, 0.7, 0.0))
W.key(1425, pos=SP4, rot=Rf(FRONT, lean=6), spine=(6, 0, 0), head=(-8, 26, 10), face=(0.0, 0.05, 0.5, 0.0))
W.key(1450, pos=SP4 + Vector((0, 0.05, -0.02)), rot=Rf(FRONT, lean=2), spine=(16, 0, 0), head=(20, 0, 0), hand_L=hang(1, 0.05), hand_R=hang(-1, 0.05), face=(0.0, 0.0, -0.6, 0.0))
feet_on_heap(W, 1450, 0.02, -0.30)
# H (1465-1753): three days: she sits, then lies curled on the clothes (head +X, facing the front wall)
SIT2 = Vector((-0.02, 0.10, 0.0)); SIT2.z = hz(SIT2.x, SIT2.y) + 0.10
W.key(1500, pos=SIT2, rot=Rb((0, 0.08, 1), FRONT), spine=(16, 0, 0), head=(5, 0, 0),
      hand_R=WH((SIT2.x - 0.24, SIT2.y + 0.05, hz(SIT2.x - 0.24, SIT2.y + 0.05)), (0, 0, -1), (0, -1, 0)),
      hand_L=WH((SIT2.x + 0.25, SIT2.y + 0.05, hz(SIT2.x + 0.25, SIT2.y + 0.05)), (0, 0, -1), (0, -1, 0)), grip_L="relaxed", grip_R="relaxed",
      foot_L=WH((SIT2.x + 0.12, SIT2.y - 0.42, hz(SIT2.x + 0.12, SIT2.y - 0.42) + 0.07), (0, 0, 1), (0, -1, 0)),
      foot_R=WH((SIT2.x - 0.12, SIT2.y - 0.40, hz(SIT2.x - 0.12, SIT2.y - 0.40) + 0.07), (0, 0, 1), (0, -1, 0)),
      knee_L=WH((SIT2.x + 0.25, SIT2.y - 0.9, 1.0), (0, 0, 1), (0, 0, 1)), knee_R=WH((SIT2.x - 0.25, SIT2.y - 0.9, 1.0), (0, 0, 1), (0, 0, 1)))
CURL = Vector((-0.22, 0.14, 0.0)); CURL.z = hz(CURL.x, CURL.y) + 0.135
def curl_key(f, breath=0.0, head=(-8, 0, 0), face=None):
    kw = dict(pos=CURL + Vector((0, 0, 0.004 * breath)), rot=Q_LIE, spine=(48 + 2 * breath, 0, 0), head=head,
              hand_L=WH((CURL.x + 0.42, CURL.y - 0.22, hz(CURL.x + 0.42, CURL.y - 0.22)), (0, 0, -1), (1, -0.3, 0)),
              hand_R=LH((-0.02, -0.38, -0.05), (0, 0.3, -1), (0, -0.4, -1)),
              foot_L=LH((0.10, -0.42, -0.50), (0, 0.3, 1), (0, -1, 0)), foot_R=LH((-0.08, -0.38, -0.48), (0, 0.3, 1), (0, -1, 0)),
              knee_L=LH((0.20, -1.0, 0.0), (0, 0, 1), (0, 0, 1)), knee_R=LH((-0.20, -1.0, 0.0), (0, 0, 1), (0, 0, 1)))
    if face: kw["face"] = face
    W.key(f, **kw)
W.key(1525, pos=SIT2 + Vector((0.12, 0.02, 0.06)), rot=Rb((0.7, 0.05, 0.7), FRONT), spine=(25, 0, 0), head=(-5, 0, 0))
for f, b in ((1555, 0), (1590, 1), (1625, -1), (1660, 1), (1695, -1), (1730, 1)):
    curl_key(f, b, head=(-8 + 4 * b, 5 * b, 0), face=(0.0, 0.0, -0.5, 0.0))
# I (1753-1867): the flap opens from outside - she lifts her head into the light, props up, reaches a hand toward it
curl_key(1785, 0, head=(-25, 0, 0), face=(0.0, 0.1, 0.6, 0.0))
W.key(1815, pos=CURL + Vector((0.0, -0.02, 0.08)), rot=Rb((0.75, -0.05, 0.62), (0, -1, 0.25)), spine=(30, 0, 0), head=(-35, 0, 0))
W.key(1840, hand_R=LH((-0.10, -0.40, 0.42), (0, 0.2, 1), (0, -0.6, 1)), grip_R="open_alarm", face=(0.0, 0.35, 0.8, 0.0))
W.key(1865, pos=CURL + Vector((0.0, -0.02, 0.10)), rot=Rb((0.7, -0.05, 0.7), (0, -1, 0.25)), spine=(28, 0, 0), head=(-38, 0, 0),
      hand_R=LH((-0.08, -0.44, 0.48), (0, 0.2, 1), (0, -0.6, 1)))
# J (1867-1993): the flap falls shut; then sparks: she sits up and shrinks back from the front wall; the panel falls open
W.key(1885, hand_R=LH((-0.05, -0.38, 0.05), (0, 0.3, -1), (0, -0.4, -1)), grip_R="relaxed")
SIT3 = Vector((0.0, 0.16, 0.0)); SIT3.z = hz(SIT3.x, SIT3.y) + 0.10
def sit3(f, lean=0.0, head=(0, 0, 0), dy=0.0, face=None):
    p = SIT3 + Vector((0, dy, 0))
    kw = dict(pos=p, rot=Rb((0, 0.08 + math.sin(R_(-lean)) * 0.5, 1), FRONT), spine=(12 + lean, 0, 0), head=head,
              hand_R=WH((p.x - 0.24, p.y + 0.05, hz(p.x - 0.24, p.y + 0.05)), (0, 0, -1), (0, -1, 0)),
              hand_L=WH((p.x + 0.25, p.y + 0.05, hz(p.x + 0.25, p.y + 0.05)), (0, 0, -1), (0, -1, 0)), grip_L="relaxed", grip_R="relaxed",
              foot_L=WH((p.x + 0.12, p.y - 0.42, hz(p.x + 0.12, p.y - 0.42) + 0.07), (0, 0, 1), (0, -1, 0)),
              foot_R=WH((p.x - 0.12, p.y - 0.40, hz(p.x - 0.12, p.y - 0.40) + 0.07), (0, 0, 1), (0, -1, 0)),
              knee_L=WH((p.x + 0.25, p.y - 0.9, 1.0), (0, 0, 1), (0, 0, 1)), knee_R=WH((p.x - 0.25, p.y - 0.9, 1.0), (0, 0, 1), (0, 0, 1)))
    if face: kw["face"] = face
    W.key(f, **kw)
W.key(1900, pos=SIT3 + Vector((0.08, 0, 0.04)), rot=Rb((0.35, 0.05, 1), FRONT), spine=(20, 0, 0), head=(-10, 0, 0))
sit3(1925, lean=-6, head=(-5, 0, 0), face=(0.0, 0.2, 0.9, 0.3))
sit3(1950, lean=-8, head=(-2, -8, 0))
sit3(1975, lean=0, head=(-10, 0, 0), face=(0.15, 0.1, 0.8, 0.0))
sit3(1993, lean=8, head=(-8, 0, 0))
# K (1993-2388): she scoots forward on the clothes and sits IN the cut opening, feet out on the fallen panel
EDGE = Vector((0.0, -0.58, 0.0)); EDGE.z = max(hz(0.0, -0.58), CP[2] + 0.02) + 0.10
def seat(f, p, lean, feet_y, head=(0, 0, 0), hands="heap", face=None, feet_z=None):
    kw = dict(pos=p, rot=Rb((0, math.sin(R_(lean)) * -1, 1), FRONT), spine=(12 + lean * 0.5, 0, 0), head=head)
    for s, sx in (("L", 1), ("R", -1)):
        fy = feet_y; fz = feet_z if feet_z is not None else hz(p.x + sx * 0.12, fy) + 0.07
        kw["foot_" + s] = WH((p.x + sx * 0.12, fy, fz), (0, 0, 1), (0, -1, 0))
        kw["knee_" + s] = WH((p.x + sx * 0.25, p.y - 0.9, 1.0), (0, 0, 1), (0, 0, 1))
        if hands == "heap":
            kw["hand_" + s] = WH((p.x + sx * 0.25, p.y + 0.06, hz(p.x + sx * 0.25, p.y + 0.06)), (0, 0, -1), (0, -1, 0))
    if face: kw["face"] = face
    W.key(f, **kw)
seat(2020, SIT3 + Vector((0, -0.12, 0.0)), 10, -0.38, head=(-8, 0, 0))
seat(2050, Vector((0.0, -0.20, hz(0, -0.20) + 0.10)), 14, -0.62)
seat(2080, Vector((0.0, -0.38, hz(0, -0.38) + 0.10)), 14, -0.95, feet_z=CP[2] + 0.10)
PANEL_TOP = 0.06
seat(2110, EDGE + Vector((0, 0.02, 0.0)), 16, -1.18, feet_z=PANEL_TOP + 0.064)
seat(2140, EDGE, 18, -1.20, feet_z=PANEL_TOP + 0.064, hands=None, head=(-6, -10, 0))
for s, sx in (("L", 1), ("R", -1)):   # forearms resting on her knees
    W.key(2140, **{"hand_" + s: LH((sx * 0.16, -0.52, 0.06), (0, 0.2, -1), (0, -1, -0.3)), "grip_" + s: "relaxed"})
for f, lean, hd, face in ((2180, 20, (-10, -25, 0), (0.0, 0.05, 0.4, 0.0)), (2230, 18, (-14, -30, 0), (0.15, 0.0, 0.5, 0.0)),
                          (2260, 19, (-4, -28, 0), (0.25, 0.0, 0.3, 0.0)), (2300, 17, (-12, -20, 0), (0.3, 0.0, 0.2, 0.0)),
                          (2345, 18, (-16, -8, 0), (0.25, 0.0, 0.2, 0.0)), (2388, 17, (-14, -2, 0), (0.25, 0.0, 0.2, 0.0))):
    seat(f, EDGE + Vector((0, 0, 0.004 * math.sin(f))), lean, -1.20, head=hd, hands=None, feet_z=PANEL_TOP + 0.064, face=face)
    for s, sx in (("L", 1), ("R", -1)):
        W.key(f, **{"hand_" + s: LH((sx * 0.16, -0.52, 0.06 + 0.01 * math.sin(f / 9.0)), (0, 0.2, -1), (0, -1, -0.3))})

# ==================================================================================== PASSER-BY: pushes the flap in to donate, sees her
PY = -1.24
P.key(1700, pos=Vector((0.10, -1.85, 0.775)), rot=Rf((0, 1, 0)), spine=(0, 0, 0), head=(0, 0, 0), hand_L=hang(1), hand_R=hang(-1),
      foot_L=WH((0.0, -1.85, 0.067), (0, 0, 1), (0, 1, 0)), foot_R=WH((0.2, -1.85, 0.067), (0, 0, 1), (0, 1, 0)), grip_L="relaxed", grip_R="relaxed")
P.key(1699, pos=Vector((-14, -16, 0.95)), rot=Rb((0, 0, 1), (0, -1, 0)))
P.key(1745, pos=Vector((0.10, -1.80, 0.77)), rot=Rf((0, 1, 0), lean=2))
P.key(1765, pos=Vector((0.08, -1.52, 0.76)), rot=Rf((0, 1, 0), lean=4), foot_L=WH((-0.02, -1.45, 0.067), (0, 0, 1), (0, 1, 0)))
P.key(1782, pos=Vector((0.08, PY, 0.80)), rot=Rf((0, 1, 0), lean=6), foot_R=WH((0.18, PY + 0.04, 0.067 + 0.04), (0, 0.35, 0.94), (0, 0.94, -0.35)),
      head=(-5, 0, 0))
P.key(1790, foot_L=WH((-0.02, PY + 0.02, 0.067 + 0.04), (0, 0.35, 0.94), (0, 0.94, -0.35)), hand_R=LH((-0.20, -0.32, 0.42), (0, -1, 0), (0, 0, 1)), grip_R="flat_palm")
P2_FLAP = [(1792, 0.0), (1812, 32.0), (1858, 30.0), (1864, 28.0), (1872, 10.0), (1878, 0.0), (1881, 2.5), (1884, 0.0)]
def p_flap_hand(f):
    a = pchip(P2_FLAP)(min(max(f, 1792), 1864))
    p_ = flap_pt(a, 0.46, 0.12); n_ = flap_in_normal(a)
    return WH(p_ - n_ * 0.009, n_, (0, -math.sin(R_(a)), math.cos(R_(a))))
P.key(1796, hand_R=p_flap_hand); P.key(1862, hand_R=p_flap_hand)
P.key(1815, pos=Vector((0.08, PY + 0.04, 0.805)), rot=Rf((0, 1, 0), lean=12), spine=(10, 0, 0), head=(18, 0, 0), face=(0.0, 0.3, 0.9, 0.0))
P.key(1845, pos=Vector((0.08, PY + 0.04, 0.805)), rot=Rf((0, 1, 0), lean=12), spine=(10, 0, 0), head=(22, -6, 0), face=(0.0, 0.45, 1.0, 0.0))
P.key(1872, pos=Vector((0.08, PY - 0.06, 0.78)), rot=Rf((0, 1, 0), lean=2), spine=(0, 0, 0), head=(0, 0, 0), hand_R=LH((-0.22, -0.20, 0.30), (0, -1, 0), (0, 0, 1)), grip_R="relaxed",
      foot_L=WH((-0.02, PY - 0.06, 0.067), (0, 0, 1), (0, 1, 0)), foot_R=WH((0.18, PY - 0.02, 0.067), (0, 0, 1), (0, 1, 0)))
P.key(1889, pos=Vector((0.08, PY - 0.20, 0.775)), hand_R=hang(-1))
# later she waits with the firefighters, watching (placed while the camera is inside the closed bin)
BYST = Vector((1.55, -2.35, 0.775)); BYF = (Vector((0, -0.7, 0)) - BYST).normalized(); BYF.z = 0
P.key(1890, pos=BYST, rot=Rf(BYF), spine=(2, 0, 0), head=(5, 0, 0), hand_L=hang(1), hand_R=hang(-1),
      foot_L=WH(BYST + Vector((-0.10, 0, -0.708)), (0, 0, 1), BYF), foot_R=WH(BYST + Vector((0.10, -0.05, -0.708)), (0, 0, 1), BYF))
for f, tw in ((1990, 0), (2100, 6), (2200, -4), (2300, 5), (2388, 0)):
    P.key(f, pos=BYST + Vector((0.01 * math.sin(f), 0, 0)), rot=Rf(BYF, side=2 * math.sin(f / 40)), spine=(2, tw, 0), head=(6, -tw, 0))

# ==================================================================================== FIREFIGHTERS (placed while the panel is still closed)
F1P = Vector((-0.92, -1.02, 0.0)); F1F = Vector((1, 0.15, 0)).normalized()
def kneel1(f, lean=10, head=(0, 0, 0), gesture=0.0):
    p = F1P + Vector((0, 0, 0.60))
    lf = Vector((-F1F.y, F1F.x, 0))                 # his left
    kw = dict(pos=p, rot=Rf(F1F, lean=lean), spine=(8, 0, 0), head=head,
              foot_L=WH(F1P + F1F * 0.38 + lf * 0.12 + Vector((0, 0, 0.077)), (0, 0, 1), F1F),          # left foot planted forward
              foot_R=WH(F1P - F1F * 0.36 - lf * 0.12 + Vector((0, 0, 0.13)), -F1F, (0, 0, -1)),   # right knee down, toes tucked under
              knee_L=WH(F1P + F1F * 1.0 + lf * 0.2 + Vector((0, 0, 0.6)), (0, 0, 1), (0, 0, 1)),
              knee_R=WH(F1P + F1F * 0.6 - lf * 0.2 + Vector((0, 0, -0.3)), (0, 0, 1), (0, 0, 1)),
              hand_L=WH(F1P + F1F * 0.36 + lf * 0.14 + Vector((0, 0, 0.60)), (0, 0, -1), F1F), grip_L="relaxed")
    if gesture > 0:
        kw["hand_R"] = LH((-0.20 + 0.0, -0.40 * gesture - 0.10, 0.30), (0, 0.3, -1), (0, -1, 0.2)); kw["grip_R"] = "relaxed"
    else:
        kw["hand_R"] = WH(F1P - F1F * 0.05 - lf * 0.16 + Vector((0, 0, 0.44)), (0, 0, -1), F1F); kw["grip_R"] = "relaxed"
    F1.key(f, **kw)
F1.key(1859, pos=Vector((-16, -16, 0.95)), rot=Rb((0, 0, 1), (0, -1, 0)))
kneel1(1860, head=(10, 15, 0))
kneel1(1975, head=(5, 20, 0))
kneel1(2030, lean=14, head=(8, 10, 0), gesture=1.0)
kneel1(2070, lean=12, head=(5, 12, 0), gesture=0.8)
kneel1(2110, lean=8, head=(10, 15, 0))
for f, hd in ((2170, (6, 22, 0)), (2240, (2, 18, 4)), (2310, (8, 24, 0)), (2388, (6, 20, 0))):
    kneel1(f, lean=9, head=hd)
F2P = Vector((0.92, -1.55, 0.0)); F2F = (Vector((0, -0.8, 0)) - F2P).normalized(); F2F.z = 0
F2.key(1859, pos=Vector((-18, -16, 0.95)), rot=Rb((0, 0, 1), (0, -1, 0)))
for f, tw, hd in ((1860, 0, (8, 0, 0)), (1975, 4, (12, -5, 0)), (2060, -3, (14, 4, 0)), (2150, 2, (10, 0, 0)), (2250, -4, (6, 6, 0)), (2388, 0, (8, 2, 0))):
    F2.key(f, pos=F2P + Vector((0, 0, 0.955)), rot=Rf(F2F, lean=3), spine=(3, tw, 0), head=hd, hand_L=hang(1, 0.02), hand_R=hang(-1, 0.02), grip_L="relaxed", grip_R="relaxed",
           foot_L=WH(F2P + Vector((-0.12 * F2F.y, 0.12 * F2F.x, 0.077)), (0, 0, 1), F2F), foot_R=WH(F2P + Vector((0.12 * F2F.y, -0.12 * F2F.x, 0.077)), (0, 0, 1), F2F))
