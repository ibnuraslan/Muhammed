# Part of 03_animate.py: the two paramedics (crouch, shift him onto the board, lift, hurry to the ambulance).
MA, MB = Human(make_human_ctrl(bpy.data.objects["MedicA"])), Human(make_human_ctrl(bpy.data.objects["MedicB"]))
for m, nm in ((MA, "MedicA"), (MB, "MedicB")):
    o = bpy.data.objects[nm]
    for ob in [o] + list(o.children):
        for f_, h_ in ((1, True), (1972, False), (2150, True)):
            ob.hide_render = h_; ob.keyframe_insert("hide_render", frame=f_)
END_OFF = 0.925 + 0.42          # medic pelvis distance from the board centre along its axis
def medic_pos(f, sign):
    c = board_xy(f).to_2d(); return c + board_hd(f) * (END_OFF * sign)
def yaw_of(v):                   # facing direction -> yaw (character faces -Y at yaw 0)
    return math.degrees(math.atan2(v.x, -v.y))
# A at the head end facing the feet (= travel direction); B at the feet end, faces the board, turns to travel at 2018-2034
yawA = lambda f: yaw_of(-board_hd(f))
def yawB(f):
    t = smooth((f - 2016) / 18.0)
    return yaw_of(board_hd(f)) * (1 - t) + (yaw_of(board_hd(f)) - 180) * t
def handles(f, sign):
    M = board_matrix(f); hd = board_hd(f).to_3d(); side = Vector((-hd.y, hd.x, 0))
    end = M.translation + hd * (0.86 * sign) + Vector((0, 0, 0.02))
    return end + side * 0.2, end - side * 0.2
def place_crouched(m, f, pos2, yaw, depth, flex, hands, pole_back):
    gz_ = ground_z(pos2.x, pos2.y)
    m.key_root(f, Vector((pos2.x, pos2.y, gz_ + m.root_head.z - depth)), yaw=yaw, flex=flex * 0.5)
    m.key_spine(f, flex=flex, head=(10, 0))
    for s in "LR":
        m.key_foot(s, f, m.foot_xy(s, pos2, yaw) + Matrix.Rotation(R_(yaw), 2) @ Vector((0, -0.12 if s == "L" else 0.06)), yaw + (12 if s == "L" else -12))
    fwd = Matrix.Rotation(R_(yaw), 3, 'Z') @ Vector((0, -1, 0))
    for s, W in zip("LR", hands):
        sx = 1 if s == "L" else -1
        side = Matrix.Rotation(R_(yaw), 3, 'Z') @ Vector((sx, 0, 0))
        m.key_hand(s, f, W, (fwd + Vector((0, 0, -0.6))).normalized(), -side + Vector((0, 0, -0.3)),
                   pole=W + side * 0.5 + Vector((0, 0, 0.3)) - fwd * pole_back)
# shift (1974-1994): hands under his shoulders (A) and knees (B), then onto the board handles
for f in (1974, 1982, 1990, 1996, 2006):
    ev(f)
    sh = [F.matrix_world @ FR.PB["upperarm01." + s].head for s in "LR"]
    kn = [F.matrix_world @ FR.PB["lowerleg01." + s].head for s in "LR"]
    if f <= 1990:
        hA = [p - Vector((0, 0, 0.05)) for p in sh]; hB = [p - Vector((0, 0, 0.04)) for p in kn]
    else:
        hA = list(handles(f, +1)); hB = list(handles(f, -1))
    pA, pB = medic_pos(1996, +1), medic_pos(1996, -1)
    place_crouched(MA, f, pA, yawA(1996), 0.42, 42, hA, 0.3)
    place_crouched(MB, f, pB, yaw_of(board_hd(1996)), 0.42, 42, hB, 0.3)
# lift (2006-2018): stand up with the board
for f, d, fl in ((2012, 0.22, 28), (2018, 0.05, 10)):
    ev(f)
    place_crouched(MA, f, medic_pos(f, +1), yawA(f), d, fl, list(handles(f, +1)), 0.2)
    place_crouched(MB, f, medic_pos(f, -1), yawB(f), d, fl, list(handles(f, -1)), 0.2)
# carry (2018-2149): planted-foot walking, hands on the board handles
MA.walk(lambda f: medic_pos(f, +1).to_3d(), yawA, 2019, 2149, stride=0.95, duty=0.55, lift=0.10, bob=0.03, crouch=0.06, lean=10)
MB.walk(lambda f: medic_pos(f, -1).to_3d(), yawB, 2019, 2149, stride=0.95, duty=0.55, lift=0.10, bob=0.03, crouch=0.06, lean=6)
for f in list(range(2020, 2150, 4)) + [2149]:
    ev(f)
    hd = board_hd(f).to_3d()
    hA = handles(f, +1); hB = handles(f, -1)
    MA.key_hand("L", f, hA[0], (-hd + Vector((0, 0, -0.3))).normalized(), Vector((0, 0, 1)))
    MA.key_hand("R", f, hA[1], (-hd + Vector((0, 0, -0.3))).normalized(), Vector((0, 0, 1)))
    # B carries behind his back once turned
    MB.key_hand("L", f, hB[0], (-hd + Vector((0, 0, -0.5))).normalized(), Vector((0, 0, 1)))
    MB.key_hand("R", f, hB[1], (-hd + Vector((0, 0, -0.5))).normalized(), Vector((0, 0, 1)))
print("MEDICS_DONE")
