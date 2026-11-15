# exec'd by 03_anim.py: street shots S1, S2, S3, S6, S19, S20, S21
BIKE = OB["Bike"]; K = BIKE["k"]; WB, WF, CR = OB["Bike_wheelB"], OB["Bike_wheelF"], OB["Bike_crank"]
LID, CAN = OB["TrashLid"], OB["TrashCan"]; TRUCK = OB["BoxTruck"]; MBOX = OB["MovingBox"]
WALK_Z = 0.12   # sidewalk top
LAWN_Z = 0.1

def walk_arms(H, fa, fb, path, stride=0.75, step=2, amp=0.09):
    """hands hang and swing opposite to the legs (local frame, facing -Y)"""
    d = 0.0; prev = path(fa)
    for f in range(fa, fb + 1):
        p = path(f); d += (p - prev).length; prev = p
        if (f - fa) % step and f != fb: continue
        ph = math.sin(2 * math.pi * d / stride)
        for s, sx, sg in (("L", 1, 1), ("R", -1, -1)):
            sh = H.r.BN["upperarm01." + s].head_local
            W = Vector((p.x + sh.x + 0.06 * sx, p.y + sh.y - 0.02 - amp * ph * sg, sh.z - 0.57 - 0.03))
            H.key_hand(s, f, W, Vector((0, -0.15 * ph * sg, -1)), Vector((-sx, 0, 0)), pole=W + Vector((0.3 * sx, 0.5, 0.3)))
    for s in "LR": apply_pose(H.r.o, s, "relaxed", fa)

def walk_line(H, fa, fb, start, speed, stride=0.72):
    """walk straight along local -Y from local `start` at `speed` m/s"""
    path = lambda f: Vector((start[0], start[1] - speed * (f - fa) / FPS, 0))
    H.walk(path, lambda f: 0.0, fa, fb, stride=stride, lift=0.07, bob=0.018, lean=4)
    return path

# ================================================================== S1: Boy rides away along the sidewalk, Neighbour behind her fence
BOY = CH["Boy"]; NB = CH["Neighbour"]; D2 = CH["Dad2"]
B0 = Vector((-4.55, -1.0, WALK_Z)); VB = 2.4
put("Boy", [("S1", (0, 0, 0), 180)])        # local = world rotated 180 deg: (x, y) -> (-x, -y); the boy faces +Y
def L180(p): return Vector((-p.x, -p.y, p.z))
BIKE.rotation_mode = 'XYZ'
r_wheel = 0.38 * K; r_crank = 0.13 * K; py_ = 0.19 * K; cz = 0.30 * K
for f in range(f0("S1") - 1, fx("S1") + 2):
    t = (f - f0("S1")) / FPS; dist = VB * t
    pos = B0 + Vector((0, dist, 0))
    key_prop(BIKE, f, pos, (0, 0, 90))
    key_prop(WB, f, None, (0, dist / r_wheel * 57.2958, 0)); key_prop(WF, f, None, (0, dist / r_wheel * 57.2958, 0))
    th = dist / r_wheel / 2.2
    key_prop(CR, f, None, (0, th * 57.2958, 0))
    if (f - f0("S1")) % 2: continue
    ev(f)
    Mb = Matrix.Translation(pos) @ Matrix.Rotation(R_(90), 4, 'Z')
    for s, sy, ph in (("L", py_, 0.0), ("R", -py_, math.pi)):
        a = th + ph
        pw = Mb @ Vector((r_crank * math.cos(a) - 0.03, sy, cz - r_crank * math.sin(a)))     # pedal (model space -> world)
        pl = L180(pw)
        BOY.key_foot(s, f, (pl + Vector((0, 0.06, 0))).to_2d(), 0.0, lift=pl.z - BOY.ankle[s].z + 0.085, pitch=-8)
    seat = Mb @ (Vector((-0.19, 0, 1.0)) * K)
    BOY.key_root(f, L180(seat) + Vector((0, 0.07, 0.13 + 0.006 * math.sin(th * 2))), yaw=0, flex=22)
    BOY.key_spine(f, flex=14, twist=3 * math.sin(th), head=(-22, 0))
    for s, sy in (("L", 0.27), ("R", -0.27)):
        g = Mb @ (Vector((0.36, sy, 1.16)) * K)
        place_hand(BOY.r.o, s, f, g + Vector((0, 0, 0.012)), Vector((0, 0.35, -1)), Vector((0, 1.0, -0.35)) if False else Vector((-0.3 if s == "L" else 0.3, 0.9, -0.3)))
for s in "LR": apply_pose(BOY.r.o, s, "wrap_grip", f0("S1"))
face(BOY, f0("S1"), 0.002, -4); blinks(BOY, f0("S1"), fx("S1"))

NBP = (-7.15, 10.8, LAWN_Z)
put("Neighbour", [("S1", NBP, 90), ("S2", NBP, 90), ("S3", NBP, 90), ("S6", (4.9, 3.0, WALK_Z), 180), ("S21", (-4.9, 50.0, WALK_Z), 180)])
fa = f0("S1")
breathe(NB, fa, fx("S1"), head=(2, 0), step=40)
arms_hang(NB, fa); face(NB, fa, 0.0, -6); blinks(NB, fa, fx("S1"), every=110)
NB.key_spine(fx("S1"), flex=3, head=(-4, 18))

# ================================================================== S2: Neighbour smells it, hand in front of her nose; Dad2 at his can behind
fa = f0("S2")
stand(NB, fa, head=(-4, 18)); face(NB, fa, 0.0, -6)
stand(NB, fa + 18, head=(-8, 10), spine=3); face(NB, fa + 18, -0.004, -14)
stand(NB, fa + 40, head=(2, 0), spine=6, flex=5); face(NB, fa + 40, -0.008, -24, 2)
for i, f in enumerate(range(fa + 60, fx("S2") + 1, 25)):
    stand(NB, f, head=(3, 6 * math.sin(i * 1.9)), spine=6, flex=5); face(NB, f, -0.008, -24 if i % 3 else -30, 2)
arms_hang(NB, fa); arms_hang(NB, fa + 30)
NOSE = face_point(NB, "nose")
for f in range(fa + 54, fx("S2") + 1, 6):
    ev(f)
    nose = world(NB, posed(NB, NOSE)); fwd = (NB.r.o.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()
    up = Vector((0, 0, 1)); left = (NB.r.o.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
    place_hand(NB.r.o, "R", f, nose + fwd * 0.065 + up * -0.015, -fwd, (up * 0.75 + left * 0.45).normalized())
    pb = NB.r.PB["Pole_elbow.R"]
ev(fa + 42); _M = NB.r.o.matrix_world; _ch = _M @ NB.r.PB["spine02"].head; _fw = (_M.to_3x3() @ Vector((0, -1, 0))).normalized(); _lf = (_M.to_3x3() @ Vector((1, 0, 0))).normalized()
place_hand(NB.r.o, "R", fa + 42, _ch + _fw * 0.3 - _lf * 0.08 + Vector((0, 0, 0.08)), -_fw, Vector((0, 0, 1)))
apply_pose(NB.r.o, "R", "relaxed", fa + 30); apply_pose(NB.r.o, "R", "shield", fa + 54)
for f in (fa + 30, fa + 54):
    n_ = "Pole_elbow.R"; pb = NB.r.PB[n_]
    tgt = NB.r.BN["upperarm01.R"].head_local + Vector((-0.45, 0.05, -0.45))
    pb.location = NB.r.rest(n_).to_3x3().inverted() @ (tgt - NB.r.BN[n_].head_local); pb.keyframe_insert("location", frame=f)

D2P = (-5.55, 22.42, WALK_Z)
put("Dad2", [("S2", D2P, 180), ("S3", D2P, 180), ("S19", (4.7, 51.0, WALK_Z), -90), ("S20", (5.5, 44.5, WALK_Z), 0)])
fa = f0("S2")
breathe(D2, fa, f0("S3") - 1, flex=6, spine=10, head=(10, 0), step=30)
arms_hang(D2, fa); face(D2, fa, 0.0, -6); blinks(D2, fa, f0("S3"))

# ================================================================== S3: Dad2 lifts the lid by its handle, recoils and turns his face away
fa = f0("S3"); fe = fx("S3")
HANDLE = Vector((-5.55, 23.0, WALK_Z + 0.95 + 0.018))
key_prop(LID, 0, LID.location.copy(), (0, 0, 0)); key_prop(LID, fa, LID.location.copy(), (0, 0, 0))
stand(D2, fa, flex=8, spine=16, head=(18, 0)); arms_hang(D2, fa); face(D2, fa, 0.0, -8)
stand(D2, fa + 20, flex=10, spine=20, head=(22, 0))
GRIP = fa + 22
for f in range(fa + 10, GRIP + 1, 4):        # reach: palm comes down onto the handle
    u = smooth((f - fa - 10) / 12); ev(f)
    place_hand(D2.r.o, "R", f, HANDLE + Vector((0, -0.12 * (1 - u), 0.05 + 0.18 * (1 - u))), Vector((0, 0.15, -1)), Vector((0, 1, -0.2)))
apply_pose(D2.r.o, "R", "open_alarm", fa + 10); apply_pose(D2.r.o, "R", "cup_hold", GRIP)
# lift: torso leans back, lid comes up and toward him, face turns away
for f in range(GRIP, fe + 1, 2):
    ev(f); u = smooth((f - GRIP) / 36.0); v = smooth((f - GRIP - 14) / 30.0)
    stand(D2, f, flex=10 - 12 * v, spine=20 - 20 * v, twist=-12 * v, head=(22 - 30 * v, -38 * v), side=4 * v, pos=(0, 0.06 * v))
    p = HANDLE + Vector((0, 0.02 * u, 0.30 * u))
    place_hand(D2.r.o, "R", f, p + Vector((0, 0, 0.03)), Vector((0, 0.15, -1)), Vector((0, 1, -0.2)))
face(D2, GRIP + 14, -0.004, -14); face(D2, GRIP + 26, -0.009, -32, 3); face(D2, fe, -0.009, -30, 3)
follow_bone(LID, D2.r.o, "wrist.R", GRIP, min(fe, f1("S3")), step=1)

# ================================================================== S6: the family house; Neighbour walks past on the sidewalk
fa = f0("S6"); fe = fx("S6")
pth = walk_line(NB, fa, fe, (0, 0), 1.25)
walk_arms(NB, fa, fe, pth); face(NB, fa, 0.002, -5); blinks(NB, fa, fe)
for s in "LR": pass

# ================================================================== S19: Dad2 carries a moving box to the truck (logo on the back doors)
TR_POS = Vector((1.9, 46.0, 0.0))
TRUCK.rotation_mode = 'XYZ'
key_prop(TRUCK, 0, TR_POS, (0, 0, -90))         # model +X forward -> world -Y
fa = f0("S19"); fe = fx("S19")
pth = walk_line(D2, fa, fe, (0, 0), 0.95, stride=0.6)
face(D2, fa, 0.0, -6); blinks(D2, fa, fe)
for f in range(fa, fe + 1, 2):
    ev(f)
    M = D2.r.o.matrix_world; ch = M @ D2.r.PB["spine03"].head
    fwd = (M.to_3x3() @ Vector((0, -1, 0))).normalized(); side = (M.to_3x3() @ Vector((1, 0, 0))).normalized()
    c = ch + fwd * 0.43 + Vector((0, 0, -0.02))
    MBOX.rotation_mode = 'XYZ'; MBOX.location = c - Vector((0, 0, 0.225)); MBOX.rotation_euler = (0, 0, R_(-90)); MBOX.keyframe_insert("location", frame=f); MBOX.keyframe_insert("rotation_euler", frame=f)
    for s, sg in (("L", 1), ("R", -1)):
        place_hand(D2.r.o, s, f, c + side * sg * 0.225, -side * sg, (fwd * 0.9 + Vector((0, 0, -0.3))).normalized())
for s in "LR": apply_pose(D2.r.o, s, "flat_palm", fa)
key_vis(MBOX, [(0, False), (fa, True), (f1("S19") + 1, False)])
# logo decal on the back doors (dark version on the white doors), flat to the S19 camera
LOGO_IMG = bpy.data.images.load(os.path.join(FILM, "..", "assets", "brand", "DaKrasFilms_logo_dark.png"))
ml = bpy.data.materials.new("Logo_dark"); ml.use_nodes = True; nt_ = ml.node_tree; P_ = nt_.nodes["Principled BSDF"]
ti = nt_.nodes.new("ShaderNodeTexImage"); ti.image = LOGO_IMG; ti.interpolation = 'Cubic'
nt_.links.new(ti.outputs["Color"], P_.inputs["Base Color"]); nt_.links.new(ti.outputs["Alpha"], P_.inputs["Alpha"]); P_.inputs["Roughness"].default_value = 0.5
ev(1)
tmn, tmx = bbox([TRUCK])
LOGO = plane("TruckLogo", (1.6, 1.6 * 414 / 967), (0, 0, 0), ml, OB["BoxTruck"].users_collection[0])
LOGO.rotation_euler = (R_(90), 0, R_(180))      # faces +Y (the back of the truck)
LOGO.location = Vector((TR_POS.x, tmx.y + 0.012, tmn.z + (tmx.z - tmn.z) * 0.6))
LOGO.parent = TRUCK; LOGO.matrix_parent_inverse = TRUCK.matrix_world.inverted()
camshot("S19", [(0.0, (4.0, 57.6, 1.75), (2.7, 49.4, 1.45), 32), (1.0, (3.8, 56.8, 1.72), (2.7, 49.4, 1.45), 33)])

# ================================================================== S20: the truck pulls away; Dad2 watches it go
fa = f0("S20"); fe = fx("S20")
for f in range(fa, fx("S21") + 1, 2):
    t = (f - fa) / FPS; y = TR_POS.y - (0.8 * t * t if t < 3 else 7.2 + 4.8 * (t - 3))
    key_prop(TRUCK, f, (TR_POS.x, y, 0), (0, 0, -90))
for i, f in enumerate(range(fa, fe + 1, 20)):
    u = (f - fa) / max(1, fe - fa)
    stand(D2, f, flex=3, spine=3, twist=-10 * u, head=(2, -10 + 55 * smooth((u - 0.55) / 0.4)))
arms_hang(D2, fa); arms_hang(D2, fe, sway=0.01)
face(D2, fa, -0.003, -10); face(D2, fe, -0.005, -14); blinks(D2, fa, fe, -0.003, -10)
camshot("S20", [(0.0, (10.6, 45.2, 1.6), (3.0, 42.0, 1.4), 30), (1.0, (10.2, 45.0, 1.6), (3.0, 42.0, 1.4), 32)])

# ================================================================== S21: wide street: the truck far away, Neighbour walks out
fa = f0("S21"); fe = fx("S21")
pth = walk_line(NB, fa, fe, (0, 0), 1.2)
walk_arms(NB, fa, fe, pth); face(NB, fa, -0.003, -8)
camshot("S21", [(0.0, (-1.2, 64.0, 7.0), (-1.8, 38.0, 0.8), 30), (1.0, (-1.3, 62.5, 6.6), (-1.8, 38.0, 0.8), 30)])

# ================================================================== street cameras
camshot("S1", [(0.0, (-4.15, -4.6, 1.1), (-4.7, 6.0, 0.85), 32), (1.0, (-4.2, 1.4, 1.1), (-4.7, 12.0, 0.85), 32)])
camshot("S2", [(0.0, (-4.4, 8.6, 1.55), (-7.1, 10.8, 1.52), 38), (1.0, (-4.6, 9.0, 1.56), (-7.1, 10.8, 1.52), 42)])
camshot("S3", [(0.0, (-3.6, 25.3, 1.45), (-5.55, 22.6, 1.25), 30), (1.0, (-3.75, 25.0, 1.45), (-5.55, 22.6, 1.3), 32)])
camshot("S6", [(0.0, (2.0, 2.2, 1.65), (17.5, 12.0, 3.0), 24), (1.0, (2.4, 2.6, 1.75), (17.5, 12.0, 3.0), 26)])
