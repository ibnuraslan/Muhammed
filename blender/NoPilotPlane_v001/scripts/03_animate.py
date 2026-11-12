"""Characters, props, exterior flight, alarms, POV camera.
blender -b work/set.blend --python 03_animate.py -- <out.blend> [nobake]"""
import sys, os, math, random
import bpy
from mathutils import Vector, Matrix, Euler, Quaternion
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "work")
exec(open(os.path.join(HERE, "lib.py")).read())
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
def ground_z(x, y): return (0.206 if (1.86 < y < 2.08 and 0.31 < abs(x) < 0.73) else 0.0) + 0.012   # soles sit on, not in, the floor
ARGS = sys.argv[sys.argv.index("--") + 1:]
OUT = ARGS[0]; NOBAKE = "nobake" in ARGS
sc = bpy.context.scene
random.seed(7)
FPS = 60
def F(t): return 1 + round(t * FPS)
ROW0, PITCH = -2.4, 0.81
cH = coll("HUMANS")

# ------------------------------------------------------------------ humans
def append_human(name):
    p = os.path.join(WORK, "h_%s.blend" % name)
    with bpy.data.libraries.load(p) as (src, dst):
        dst.objects = [n for n in src.objects]
    arm = None
    for o in dst.objects:
        cH.objects.link(o)
        if o.type == 'ARMATURE': arm = o
    return arm
def dup_human(arm, newname):
    a2 = arm.copy(); a2.name = newname; a2.animation_data_clear(); cH.objects.link(a2)
    for ch in arm.children:
        c2 = ch.copy(); cH.objects.link(c2); c2.parent = a2
        for m in c2.modifiers:
            if m.type == 'ARMATURE': m.object = a2
    return a2
def eyes_closed(rig, f, amt=1.0):
    for s in "LR":
        rig.key_rot("orbicularis03." + s, f, [("X", 28 * amt)])
        rig.key_rot("orbicularis04." + s, f, [("X", -8 * amt)])
SPW = {"spine05": 0.12, "spine04": 0.18, "spine03": 0.22, "spine02": 0.26, "spine01": 0.22}
HDW = {"neck01": 0.25, "neck02": 0.25, "neck03": 0.2, "head": 0.3}
def fk_spine(rig, f, flex=0, side=0, twist=0, hflex=0, hside=0, htwist=0):
    for n, w in SPW.items(): rig.key_rot(n, f, [("X", flex * w), ("Y", side * w), ("Z", twist * w)])
    for n, w in HDW.items(): rig.key_rot(n, f, [("X", hflex * w), ("Y", hside * w), ("Z", htwist * w)])
def fk_arm(rig, s, f, down=40, fwd=20, elbow=60, out=0, twist=0, wrist=0):
    sx = 1 if s == "L" else -1
    rig.key_rot("upperarm01." + s, f, [("Y", sx * down), ("X", -fwd), ("Z", sx * out)])
    rig.key_rot("lowerarm01." + s, f, [("X", -elbow), ("Z", sx * twist)])
    rig.key_rot("wrist." + s, f, [("X", wrist)])
def fk_leg(rig, s, f, hip=88, knee=80, splay=4, ankle=0):
    sx = 1 if s == "L" else -1
    rig.key_rot("upperleg01." + s, f, [("X", -hip), ("Z", sx * splay)])
    rig.key_rot("lowerleg01." + s, f, [("X", knee)])
    rig.key_rot("foot." + s, f, [("X", ankle)])
def fingers_curl(rig, f, s, amt):
    for k in range(1, 6):
        for j in (1, 2, 3):
            n = "finger%d-%d.%s" % (k, j, s)
            if n in rig.PB: rig.key_rot(n, f, [("X", (-amt * (0.6 if k == 1 else 1.0)))])

for pb_name in ("YOU", "CAPT", "FO", "PA", "PB", "PC", "PD", "PE", "PF"):
    append_human(pb_name)
OB = bpy.data.objects
# no logos: swap emblem shirts to the patched textures (scripts/patch_logos.py)
for im in bpy.data.images:
    for nm in ("female_casualsuit01", "male_casualsuit02", "male_casualsuit04"):
        if (nm + "_diffuse") in im.filepath:
            im.filepath = os.path.join(WORK, "tex", nm + "_diffuse_nologo.png"); im.reload()
for a in [o for o in cH.objects if o.type == 'ARMATURE']:
    for pb in a.pose.bones: pb.rotation_mode = 'QUATERNION'

# ---------------------------------------------- passengers (static slumps + dive wobble)
cP = coll("PASSENGERS")
VAR = ["PA", "PB", "PC", "PD", "PE", "PF"]
seats = []
for i in range(14):
    y = ROW0 - PITCH * i
    for side, xs in (("L", (-0.55, -1.03)), ("R", (0.55, 1.03))):
        for k, x in enumerate(xs):
            seats.append((i + 1, side, k, x, y))
EMPTY = {(4, "L", 0), (2, "R", 1), (7, "L", 0), (11, "R", 0), (13, "L", 1), (14, "R", 1), (9, "R", 1)}
PASS = []
used = {v: 0 for v in VAR}
for n, (row, side, k, x, y) in enumerate(seats):
    if (row, side, k) in EMPTY: continue
    v = VAR[n % 6] if (row, side, k) != (4, "L", 1) else "PA"
    base = OB[v]
    arm = base if used[v] == 0 else dup_human(base, "%s_%02d%s%d" % (v, row, side, k))
    used[v] += 1
    for o in [arm] + list(arm.children): link(o, cP)
    arm.location = (x, y - 0.11, -0.30); arm.rotation_euler = (0, 0, math.pi)
    PASS.append((arm, row, side, k, x, y))
print("PASSENGERS", len(PASS), used)

def pose_passenger(arm, row, side, k, x, y, f):
    R = Rig(arm); rnd = random.Random(hash((row, side, k)) & 0xffff)
    aisle = (k == 0)
    to_aisle = (1 if side == "L" else -1)   # +X in world is character's -X (they face +Y after 180 turn): character left = world -X
    fk_leg(R, "L", f, hip=86 + rnd.uniform(-6, 4), knee=78 + rnd.uniform(-8, 8), splay=rnd.uniform(2, 9))
    fk_leg(R, "R", f, hip=86 + rnd.uniform(-6, 4), knee=78 + rnd.uniform(-8, 8), splay=rnd.uniform(2, 9))
    sidelean = rnd.choice([-1, 1]) * rnd.uniform(4, 14)
    if aisle: sidelean = -to_aisle * rnd.uniform(4, 12)      # v007: lean toward the aisle, away from the seatmate
    if not aisle: sidelean = -to_aisle * rnd.uniform(6, 16) * (-1)   # window seat: lean toward the window
    SP = dict(flex=rnd.uniform(-4, 14), side=sidelean, twist=rnd.uniform(-10, 10),
              hflex=rnd.choice([rnd.uniform(25, 50), rnd.uniform(-35, -20)]), hside=sidelean * 2.2 + rnd.uniform(-10, 10), htwist=rnd.uniform(-25, 25))
    fk_spine(R, f, **SP); arm["SP"] = SP
    dangle = aisle and rnd.random() < 0.45
    dangle = False      # v007: arms hanging into the aisle hit YOU walking past and the passenger across
    ELB = arm.get("ELB", {})
    for s in "LR":
        aisle_arm = (s == "L") == (side == "R")   # the arm on the aisle side
        if dangle and aisle_arm:
            fk_arm(R, s, f, down=62, fwd=rnd.uniform(-5, 10), elbow=rnd.uniform(5, 20), out=rnd.uniform(0, 10))
        else:
            dn, fw, el = rnd.uniform(36, 46), rnd.uniform(18, 32), rnd.uniform(48, 68)
            fk_arm(R, s, f, down=dn, fwd=fw, elbow=ELB.get(s, el), out=0)
        fingers_curl(R, f, s, 25)
    eyes_closed(R, f, 1.0)
    R.key_rot("jaw", f, [("X", rnd.uniform(2, 9))])
    return R, sidelean

DIVE0, DIVE1 = F(33.7), F(44.5)
def fit_lap_hands(arm, row, side, k, x, y):
    ELB = {}
    for it in range(6):
        arm["ELB"] = ELB; pose_passenger(arm, row, side, k, x, y, 1); sc.frame_set(1)
        ok = True
        for s_ in "LR":
            w = arm.matrix_world @ arm.pose.bones["wrist." + s_].head
            hip = arm.matrix_world @ arm.pose.bones["upperleg02." + s_].head; kn = arm.matrix_world @ arm.pose.bones["lowerleg01." + s_].head
            ab = kn - hip; t = max(0.0, min(1.0, (w - hip).dot(ab) / ab.length_squared)); top = (hip + ab * t).z + 0.10
            el = ELB.get(s_, None)
            if el is None:
                rnd = random.Random(hash((row, side, k)) & 0xffff); el = 58.0
            if w.z < top + 0.03: ELB[s_] = el + 9; ok = False        # more elbow bend lifts the hand
            elif w.z > top + 0.10: ELB[s_] = el - 6; ok = False
            else: ELB[s_] = el
        if ok: break
    arm["ELB"] = ELB
for (arm, row, side, k, x, y) in PASS:
    fit_lap_hands(arm, row, side, k, x, y)
    R, sl = pose_passenger(arm, row, side, k, x, y, 1)
    # heads/torso sway with the dive (secondary motion), then settle
    rnd = random.Random(row * 10 + k)
    for f in range(DIVE0, DIVE1, 24):
        u = (f - DIVE0) / (DIVE1 - DIVE0); amp = math.sin(math.pi * u)
        fk_spine(R, f, flex=8 + 18 * amp, side=sl + 14 * amp * math.sin(f * 0.11 + rnd.uniform(0, 6)), twist=rnd.uniform(-10, 10) * amp,
                 hflex=30 + 25 * amp * math.sin(f * 0.17), hside=sl * 2 + 25 * amp * math.sin(f * 0.13 + 1), htwist=rnd.uniform(-20, 20))
    pose_passenger(arm, row, side, k, x, y, DIVE1 + 30)
    # breathing: slow chest rise/fall and a slight head nod, random phase (unconscious people still breathe)
    SP = dict(arm["SP"]); ph = rnd.uniform(0, 6.28); per = rnd.uniform(4.0, 5.2) * FPS
    for f in list(range(1, DIVE0 - 40, 40)) + list(range(DIVE1 + 70, 4411, 40)):
        b = math.sin(2 * math.pi * f / per + ph)
        fk_spine(R, f, flex=SP["flex"] + 1.6 * b, side=SP["side"], twist=SP["twist"], hflex=SP["hflex"] + 1.2 * b, hside=SP["hside"], htwist=SP["htwist"])

# ------------------------------------------------------------------ captain (crumpled in doorway)
CA = OB["CAPT"]; RC = Rig(CA)
# lying on his right side, head toward the captain seat, knees drawn up; back to the left wall
CA.location = (0.42, 0.40, 0.125); CA.rotation_euler = (R_(-90), 0, R_(90))
fk_leg(RC, "L", 1, hip=55, knee=75, splay=6); fk_leg(RC, "R", 1, hip=35, knee=60, splay=-4)
fk_spine(RC, 1, flex=18, side=0, twist=8, hflex=-10, hside=10, htwist=20)
fk_arm(RC, "L", 1, down=15, fwd=60, elbow=30); fk_arm(RC, "R", 1, down=20, fwd=80, elbow=55)
for f in range(40, 4411, 40):          # breathing
    b = math.sin(2 * math.pi * f / (4.6 * FPS))
    fk_spine(RC, f, flex=18 + 1.8 * b, side=0, twist=8, hflex=-10 + 1.2 * b, hside=10, htwist=20)
CA.keyframe_insert("location", frame=F(34.0)); CA.keyframe_insert("rotation_euler", frame=F(34.0))
for t_, dy, rz in ((36.0, 0.05, 3), (38.5, 0.10, 6), (41.0, 0.08, 4), (44.5, 0.03, 1), (46.0, 0.02, 0)):   # slides and rolls with the dive
    CA.location = (0.42, 0.40 + dy, 0.125); CA.rotation_euler = (R_(-90), R_(rz), R_(90))
    CA.keyframe_insert("location", frame=F(t_)); CA.keyframe_insert("rotation_euler", frame=F(t_))
eyes_closed(RC, 1); RC.key_rot("jaw", 1, [("X", 6)])
for s in "LR": fingers_curl(RC, 1, s, 30)

# ------------------------------------------------------------------ first officer (slumped in right seat, hauled out)
FO = OB["FO"]; RF = Rig(FO)
FO.rotation_euler = (0, 0, math.pi)
def fo_pose(f, loc, rz=180.0, rx=0.0, ry=0.0, flex=10, side=-30, twist=0, hflex=20, hside=-45, htwist=10, legs=(88, 80),
            armL=(58, 12, 25, 18), armR=(64, 0, 10, 18)):
    FO.location = loc; FO.rotation_euler = (R_(rx), R_(ry), R_(rz))
    FO.keyframe_insert("location", frame=f); FO.keyframe_insert("rotation_euler", frame=f)
    fk_leg(RF, "L", f, hip=legs[0], knee=legs[1]); fk_leg(RF, "R", f, hip=legs[0] - 4, knee=legs[1] + 5)
    fk_spine(RF, f, flex=flex, side=side, twist=twist, hflex=hflex, hside=hside, htwist=htwist)
    fk_arm(RF, "L", f, *armL); fk_arm(RF, "R", f, *armR)
    eyes_closed(RF, f); RF.key_rot("jaw", f, [("X", 7)])
    for s in "LR": fingers_curl(RF, f, s, 30)
SEATED_FO = (0.52, 1.57, -0.23)
# side < 0 leans toward character's -X = world +X (window) since he faces +Y
fo_pose(1, SEATED_FO, flex=12, side=-24, twist=14, hflex=28, hside=-22, htwist=30)        # face turned toward the cabin, readable
fo_pose(F(28.0), SEATED_FO, flex=12, side=-24, twist=14, hflex=28, hside=-22, htwist=30)
fo_pose(F(28.8), (0.47, 1.50, -0.18), flex=-5, side=-10, hflex=-15, hside=-20, armL=(45, 10, 30, 32), armR=(55, 0, 15, 32))   # hauled up/back
fo_pose(F(29.8), (0.45, 1.36, -0.14), rz=200, flex=-10, side=8, hflex=-30, hside=10, armL=(45, 30, 20, 32), armR=(60, -10, 15, 32))
fo_pose(F(30.6), (0.43, 1.27, -0.16), rz=205, flex=-8, side=12, hflex=-35, hside=15, armL=(48, 32, 12, 32), armR=(62, -10, 15, 32))  # left arm swings down onto the yoke
fo_pose(F(31.4), (0.56, 1.18, -0.25), rz=210, rx=-15, flex=-5, side=10, hflex=-30, hside=15, armL=(48, 30, 12, 32), armR=(62, -10, 15, 32))
fo_pose(F(32.4), (0.76, 0.98, -0.48), rz=215, rx=-30, flex=-15, hflex=-30, hside=25, legs=(70, 40), armL=(50, 20, 20, 32), armR=(60, -20, 15, 32))
fo_pose(F(33.4), (0.74, 0.96, -0.55), rz=200, rx=-20, flex=10, side=10, hflex=35, hside=30, legs=(80, 20), armL=(50, 10, 20, 32), armR=(58, 0, 15, 32))
fo_pose(F(38.0), (0.74, 0.96, -0.55), rz=200, rx=-20, flex=18, side=14, hflex=45, hside=35, legs=(80, 20), armL=(55, 5, 10, 20), armR=(60, 0, 10, 20))
for f in range(F(38.0) + 40, 4410, 40):
    fo_pose(f, (0.74, 0.96, -0.55), rz=200, rx=-20, flex=18 + 1.8 * math.sin(2 * math.pi * f / (4.3 * FPS)), side=14, hflex=45 + 1.2 * math.sin(2 * math.pi * f / (4.3 * FPS)), hside=35, legs=(80, 20), armL=(55, 5, 10, 20), armR=(60, 0, 10, 20))

# ------------------------------------------------------------------ pilot uniform details (bone-attached; director v006)
M_gold = mat("M_uniform_gold", (0.95, 0.68, 0.18), rough=0.3, metal=1.0)
M_navy = mat("M_uniform_navy", (0.0103, 0.0176, 0.0513), rough=0.6)
M_shirt = mat("M_uniform_shirt", (0.85, 0.87, 0.9), rough=0.5)
M_tie = mat("M_uniform_tie", (0.012, 0.014, 0.03), rough=0.45)
M_belt = mat("M_uniform_belt", (0.01, 0.01, 0.01), rough=0.35)
def attach(ob, arm, bone):
    pb = arm.pose.bones[bone]
    c = ob.constraints.new('CHILD_OF'); c.target = arm; c.subtarget = bone
    c.inverse_matrix = (arm.matrix_world @ pb.matrix).inverted()
def bone_frame(arm, bone):
    M = arm.matrix_world @ arm.pose.bones[bone].matrix
    return M.translation.copy(), M.to_3x3().normalized()
def uniform(arm, tag):
    sc.frame_set(1); bpy.context.view_layer.update()
    cU = coll("UNIFORM")
    W = arm.matrix_world.to_3x3().normalized()
    fwd = (W @ Vector((0, -1, 0))).normalized()                      # character forward
    for s_ in "LR":
        side = (W @ Vector((1 if s_ == "L" else -1, 0, 0))).normalized()
        # four gold cuff rings near the wrist
        h, R = bone_frame(arm, "lowerarm02." + s_); tail = arm.matrix_world @ arm.pose.bones["lowerarm02." + s_].tail
        ax = (tail - h).normalized()
        cuff = MB("CUFF_%s_%s" % (tag, s_))
        for k in range(4):
            c = tail - ax * (0.035 + k * 0.014)
            bm_ = cuff; g = bmesh.ops.create_cone(bm_.bm, cap_ends=False, segments=20, radius1=0.047, radius2=0.047, depth=0.006)
            M_ = Matrix.Translation(c) @ ax.to_track_quat('Z', 'Y').to_matrix().to_4x4()
            bm_._fin(g["verts"], M_, M_gold)
        co = cuff.obj(cU); attach(co, arm, "lowerarm02." + s_)
        # epaulette with four gold bars on the shoulder top
        h, R = bone_frame(arm, "shoulder01." + s_); tail = arm.matrix_world @ arm.pose.bones["shoulder01." + s_].tail
        up = (arm.matrix_world.to_3x3() @ arm.pose.bones["spine01"].matrix.to_3x3() @ Vector((0, 1, 0))).normalized()
        mid = (h + tail) / 2 + up * 0.075; d = (tail - h).normalized()
        ep = MB("EPAULETTE_%s_%s" % (tag, s_)); rot = Matrix((d, up.cross(d).normalized(), up)).transposed()
        g = bmesh.ops.create_cube(ep.bm, size=1.0); ep._fin(g["verts"], Matrix.Translation(mid) @ rot.to_4x4() @ Matrix.Diagonal((0.13, 0.055, 0.008, 1)), M_navy)
        for k in range(4):
            g = bmesh.ops.create_cube(ep.bm, size=1.0)
            ep._fin(g["verts"], Matrix.Translation(mid + d * (0.03 - k * 0.016) + up * 0.005) @ rot.to_4x4() @ Matrix.Diagonal((0.006, 0.05, 0.004, 1)), M_gold)
        eo = ep.obj(cU); attach(eo, arm, "shoulder01." + s_)
    # collar, tie, wing badge on the chest
    nh = arm.matrix_world @ arm.pose.bones["neck01"].head
    sh = arm.matrix_world @ arm.pose.bones["spine01"].head
    up = (nh - sh).normalized(); side = (W @ Vector((1, 0, 0))).normalized(); f2 = up.cross(side).normalized()
    if f2.dot(fwd) < 0: f2 = -f2
    rot = Matrix((side, up, f2)).transposed().to_4x4()
    ch = MB("CHEST_%s" % tag)
    def bx(c, sz, m, extra=Matrix.Identity(4)):
        g = bmesh.ops.create_cube(ch.bm, size=1.0); ch._fin(g["verts"], Matrix.Translation(c) @ rot @ extra @ Matrix.Diagonal((*sz, 1)), m)
    base = nh + f2 * 0.075 - up * 0.02
    for sg in (-1, 1):
        bx(base + side * sg * 0.035, (0.05, 0.035, 0.01), M_shirt, Matrix.Rotation(R_(sg * 25), 4, 'Z'))       # collar points
        bx(nh + f2 * 0.06 - up * 0.17 + side * sg * 0.075, (0.02, 0.26, 0.008), M_gold if False else M_navy, Matrix.Rotation(R_(-sg * 18), 4, 'Z'))   # lapel edge
        bx(nh + f2 * 0.064 - up * 0.17 + side * sg * 0.088, (0.004, 0.26, 0.004), M_shirt, Matrix.Rotation(R_(-sg * 18), 4, 'Z'))  # lapel highlight line
    bx(base - up * 0.03, (0.03, 0.025, 0.012), M_tie)                                                            # knot
    bx(base - up * 0.15, (0.04, 0.22, 0.006), M_tie)                                                             # tie
    wc = nh + f2 * 0.08 - up * 0.13 + side * 0.10                                                                # wing badge (shape only)
    for sg in (-1, 1):
        bx(wc + side * sg * 0.028, (0.045, 0.012, 0.003), M_gold, Matrix.Rotation(R_(sg * 12), 4, 'Z'))
    bx(wc, (0.016, 0.016, 0.004), M_gold)
    # belt line
    rh = arm.matrix_world @ arm.pose.bones["spine05"].head
    for sg in (-1, 1):
        bx(rh + f2 * 0.12 + side * sg * 0.08 + up * 0.04, (0.14, 0.03, 0.006), M_belt)
    bx(rh + f2 * 0.125 + up * 0.04, (0.035, 0.03, 0.008), M_gold)
    co = ch.obj(cU); attach(co, arm, "spine01")
    # trouser creases (thin lighter navy line down the front of each thigh)
    for s_ in "LR":
        h = arm.matrix_world @ arm.pose.bones["upperleg01." + s_].head; t = arm.matrix_world @ arm.pose.bones["lowerleg01." + s_].head
        d = (t - h).normalized(); n = (fwd - d * fwd.dot(d)).normalized()
        cr = MB("CREASE_%s_%s" % (tag, s_)); g = bmesh.ops.create_cube(cr.bm, size=1.0)
        r3 = Matrix((n.cross(d).normalized(), d, n)).transposed()
        cr._fin(g["verts"], Matrix.Translation((h + t) / 2 + n * 0.085) @ r3.to_4x4() @ Matrix.Diagonal((0.004, (t - h).length * 0.8, 0.003, 1)), mat("M_crease", (0.05, 0.07, 0.14), rough=0.5))
        cro = cr.obj(cU); attach(cro, arm, "upperleg02." + s_)

# ------------------------------------------------------------------ props
DOOR = OB["DOOR"]
def keyrot(o, f, e):
    o.rotation_euler = [R_(a) for a in e]; o.keyframe_insert("rotation_euler", frame=f)
keyrot(DOOR, 1, (0, 0, -28)); keyrot(DOOR, F(11.72), (0, 0, -28)); keyrot(DOOR, F(11.98), (0, 0, -88)); keyrot(DOOR, F(12.2), (0, 0, -82))   # ajar, then pushed flat
keyrot(DOOR, F(15.2), (0, 0, -86)); keyrot(DOOR, F(16.5), (0, 0, -87))
YR, YL = OB["YOKE_R"], OB["YOKE_L"]
yoke_keys = [(1, 0), (F(30.8), 0), (F(31.1), -6), (F(31.5), -16), (F(33.7), -15), (F(38.8), -14), (F(39.8), -10), (F(40.8), -12),
             (F(41.8), -6), (F(42.5), -5), (F(44.0), 4), (F(45.8), 3), (F(47.1), 1), (F(56.8), 2), (F(64.6), 1.5), (F(72.5), 1)]
for f, a in yoke_keys:
    keyrot(YR, f, (a, 0, 0)); keyrot(YL, f, (a, 0, 0))
# shake on the yoke while you fight it
for f in range(F(38.8), F(45.0), 6):
    u = 1 - (f - F(38.8)) / (F(45.0) - F(38.8))
    a = dict(yoke_keys).get(f, None)
for f in range(F(39.0), F(44.6), 8):
    base = YR.animation_data.action
    YR.rotation_euler.y = R_(random.uniform(-4, 4) * (1 - (f - F(39)) / 340)); YR.keyframe_insert("rotation_euler", index=1, frame=f)
    YL.rotation_euler.y = YR.rotation_euler.y; YL.keyframe_insert("rotation_euler", index=1, frame=f)
# throttles nudge when touched
for k in (0, 1):
    T = OB["THROTTLE_%d" % k]
    keyrot(T, 1, (-15, 0, 0)); keyrot(T, F(59.2), (-15, 0, 0)); keyrot(T, F(59.8), (-19, 0, 0)); keyrot(T, F(61.0), (-19, 0, 0))

# tipping drink on the tray in front of the window passenger (row 3 seat back, row 4 window)
M_cupm = mat("M_cup", (0.85, 0.85, 0.82), rough=0.35)
M_liq = mat("M_cola", (0.06, 0.02, 0.005), rough=0.05, coat=0.6)
TRAY_Z = 0.729; CUPX, CUPY, CR = -0.95, ROW0 - 2 * PITCH - 0.50, 0.032
cb = MB("CUP"); cb.cyl((0, CR, 0.05), CR, 0.1, M_cupm, seg=20, r2=CR * 1.18)
cb.cyl((0, CR, 0.088), CR * 1.1, 0.003, M_liq, seg=20)
cup = cb.obj(cSet := bpy.data.collections["SET"], smooth=True); cup.location = (CUPX, CUPY - CR, TRAY_Z)
keyrot(cup, 1, (0, 0, 0)); keyrot(cup, F(1.6), (2, 0, 0)); keyrot(cup, F(2.8), (9, 0, 0)); keyrot(cup, F(3.3), (30, 0, 0)); keyrot(cup, F(3.55), (88, 0, 0))
keyrot(cup, F(3.7), (82, 0, 0)); keyrot(cup, F(3.85), (90, 0, 0))
cup.location = (CUPX, CUPY - CR, TRAY_Z); cup.keyframe_insert("location", frame=F(3.4))
cup.location = (CUPX + 0.02, CUPY - CR - 0.05, TRAY_Z + 0.002); cup.keyframe_insert("location", frame=F(4.6))
pd = MB("SPILL"); pd.cyl((0, 0, 0), 0.09, 0.002, M_liq, seg=24); spill = pd.obj(cSet); spill.location = (CUPX + 0.01, CUPY - 0.12, TRAY_Z + 0.001)
spill.scale = (0.01, 0.01, 1); spill.keyframe_insert("scale", frame=F(3.45))
spill.scale = (1.0, 0.8, 1); spill.keyframe_insert("scale", frame=F(5.0))
for k in range(4):   # drips over the tray edge
    dr = MB("DRIP_%d" % k); dr.sphere((0, 0, 0), 0.006, M_liq, scale=(1, 1, 2.2), seg=8); d_ = dr.obj(cSet)
    x0 = CUPX - 0.03 + 0.02 * k; y0 = ROW0 - 2 * PITCH - 0.52 - 0.13; t0 = 3.9 + 0.35 * k
    for tt in range(0, 50, 5):
        t = t0 + tt / 60 * 1.4; dz = 0.5 * 9.8 * (tt / 60 * 1.4) ** 2
        d_.location = (x0, y0, max(0.02, TRAY_Z - 0.01 - dz)); d_.keyframe_insert("location", frame=F(t))
    d_.scale = (0, 0, 0); d_.keyframe_insert("scale", frame=F(t0) - 1); d_.scale = (1, 1, 1); d_.keyframe_insert("scale", frame=F(t0))
    d_.keyframe_insert("scale", frame=F(t0 + 1.0)); d_.scale = (0, 0, 0); d_.keyframe_insert("scale", frame=F(t0 + 1.05))

uniform(FO, 'FO'); uniform(CA, 'CAPT')

# radio LEDs blink 19.7 .. 27
for i in range(6):
    m = bpy.data.materials["M_led_%d" % i]; e = m.node_tree.nodes["Emission"]
    e.inputs["Strength"].default_value = 0.3; e.inputs["Strength"].keyframe_insert("default_value", frame=1)
    f = F(19.9) + i * 7
    while f < F(27.5):
        on = random.random() < 0.55
        e.inputs["Strength"].default_value = 6.0 if on else 0.3; e.inputs["Strength"].keyframe_insert("default_value", frame=f)
        f += random.choice((9, 14, 20))
    for kp in m.node_tree.animation_data.action.layers[0].strips[0].channelbags[0].fcurves[0].keyframe_points: kp.interpolation = 'CONSTANT'

# alarms: strobe 33.7 .. 46.5 (red lamps, red point lights in cockpit + cabin)
WARN = bpy.data.materials["M_warn"].node_tree.nodes["Emission"].inputs["Strength"]
LA, LAC = OB["L_alarm"].data, OB["L_alarm_cabin"].data
def kv(sock_owner, path, f, v):
    setattr(sock_owner, path, v); sock_owner.keyframe_insert(path, frame=f)
kv(WARN, "default_value", 1, 0.0); kv(LA, "energy", 1, 0.0); kv(LAC, "energy", 1, 0.0)
f = F(33.7); on = True
while f < F(46.5):
    fade = 1.0 if f < F(43) else max(0.0, 1 - (f - F(43)) / (F(46.5) - F(43)))
    kv(WARN, "default_value", f, 40.0 * fade if on else 0.5); kv(LA, "energy", f, 70.0 * fade if on else 0.0); kv(LAC, "energy", f, 150.0 * fade if on else 0.0)
    f += 12; on = not on
kv(WARN, "default_value", F(46.6), 0.5); kv(LA, "energy", F(46.6), 0.0); kv(LAC, "energy", F(46.6), 0.0)
for idb in (bpy.data.materials["M_warn"].node_tree, LA, LAC):
    for kp in idb.animation_data.action.layers[0].strips[0].channelbags[0].fcurves[0].keyframe_points: kp.interpolation = 'CONSTANT'

# ------------------------------------------------------------------ flight profile (EXT_ROT attitude, EXT_MOVE altitude/distance)
ER, EM = OB["EXT_ROT"], OB["EXT_MOVE"]
ER.rotation_mode = 'YXZ'
# (t, pitch nose-down deg, roll deg, heading deg, altitude m, speed m/s)
FL = [(0.0, 0, 0, 0, 3000, 120), (33.7, 0, 0, 0, 3000, 120), (34.6, 8, 6, 0, 2985, 125), (35.5, 18, 16, 4, 2930, 135), (36.5, 26, 28, 12, 2800, 150),
      (37.6, 30, 38, 26, 2590, 165), (38.8, 32, 44, 40, 2330, 175), (39.8, 30, 40, 52, 2100, 180), (40.8, 25, 30, 60, 1890, 180),
      (41.8, 18, 20, 66, 1720, 175), (42.5, 13, 14, 69, 1620, 170), (43.6, 7, 7, 72, 1520, 160), (44.7, 3, 3, 73, 1460, 150),
      (45.8, 1, 1, 73.5, 1420, 140), (47.1, 1.5, -1, 74, 1380, 135), (49.6, 2.5, -7, 72, 1180, 130), (52.3, 2, 6, 73, 900, 125), (53.5, 2, 1, 74, 720, 120), (56.8, 1.5, -5, 74, 520, 110), (60.4, 1.5, 6, 75, 400, 105), (62.6, 1.5, -3, 74, 340, 100),
      (64.6, 1.5, 1, 74, 300, 100), (68.9, 1.5, 0, 74, 210, 95), (72.5, 1.2, 0, 74, 160, 90), (73.5, 1.2, 0, 74, 150, 88)]
def flk(i): return catmull([(F(r[0]), r[i]) for r in FL])
P_, R2_, H_, A_, V_ = flk(1), flk(2), flk(3), flk(4), flk(5)
pos = Vector((0, 0)); POS = {}
for f in range(1, 4411):
    hd = R_(H_(f)); pos += Vector((-math.sin(hd), math.cos(hd))) * V_(f) / FPS * math.cos(R_(P_(f)))
    POS[f] = pos.copy()
TOWN1 = None
for f in range(1, 4411, 2):
    # plane sees the world rotated by the inverse of its attitude
    att = (Matrix.Rotation(R_(H_(f)), 3, 'Z') @ Matrix.Rotation(R_(-P_(f)), 3, 'X') @ Matrix.Rotation(R_(R2_(f)), 3, 'Y'))
    inv = att.inverted()
    ER.rotation_euler = inv.to_euler('YXZ'); ER.keyframe_insert("rotation_euler", frame=f)
    p = POS[f]; EM.location = (-p.x, -p.y, -A_(f)); EM.keyframe_insert("location", frame=f)

# towns, river, the long field -- placed on the flight path
cT = coll("TOWNS", coll("EXTERIOR"))
M_roof = [mat("M_roof_%d" % i, c, rough=0.8, noise=0.3, nscale=0.5) for i, c in enumerate(((0.35, 0.12, 0.08), (0.3, 0.3, 0.3), (0.45, 0.42, 0.38), (0.2, 0.22, 0.25)))]
M_street = mat("M_street", (0.12, 0.12, 0.12), rough=0.9)
def town(name, cx, cy, size, n, tall=1.0):
    t = MB(name); t.box((cx, cy, 0.3), (size * 1.1, size * 1.1, 0.6), M_street)
    for i in range(n):
        x = cx + random.uniform(-size / 2, size / 2); y = cy + random.uniform(-size / 2, size / 2)
        d = math.hypot(x - cx, y - cy) / (size / 2)
        h = random.uniform(6, 18) * tall * (1 + 3 * max(0, 1 - d) ** 2)
        w = random.uniform(10, 28)
        t.box((x, y, h / 2), (w, w * random.uniform(0.6, 1.6), h), random.choice(M_roof))
    o = t.obj(cT); o.parent = EM; return o
def at(f, ahead, side=0.0):
    hd = R_(H_(f)); p = POS[f]
    fw = Vector((-math.sin(hd), math.cos(hd))); rt = Vector((fw.y, -fw.x))
    return p + fw * ahead + rt * side
c1 = at(F(37.8), 2400 * 1.0, 300)          # under the dive
town("TOWN_DIVE", c1.x, c1.y, 1800, 1400, 1.6)
c2 = at(F(53.5), 2600)                     # town before the field
town("TOWN_FIELD", c2.x, c2.y, 900, 500)
hd = R_(H_(F(60)))
cf = at(4410, 2600)
fm = MB("LONG_FIELD")
fw = Vector((-math.sin(hd), math.cos(hd)))
fm.box((cf.x, cf.y, 0.4), (320, 4200, 0.8), mat("M_long_field", (0.22, 0.48, 0.06), rough=0.9, noise=0.35, nscale=0.01), rot=(0, 0, H_(F(60))))
fo_ = fm.obj(cT); fo_.parent = EM
rv = MB("RIVER"); c3 = at(F(45), 4000, -800)
rv.box((c3.x, c3.y, 0.2), (90, 26000, 0.4), mat("M_river", (0.03, 0.06, 0.08), rough=0.08), rot=(0, 0, H_(F(45)) + 60))
rvo = rv.obj(cT); rvo.parent = EM

# instruments: needles, ADI, altimeter
NEED = [o for o in bpy.data.objects if o.name.startswith("NEEDLE_")]
for o in NEED:
    base = random.uniform(-120, 120)
    for f in range(1, 4411, 30):
        t = (f - 1) / FPS
        if F(33.7) <= f <= F(44.0):
            a = base + (f - F(33.7)) * random.uniform(4, 11) * random.choice((-1, 1))
        elif f > F(44):
            a = base + 40 * math.sin(f * 0.004 + base)
        else:
            a = base + 2 * math.sin(f * 0.05)
        keyrot(o, f, (0, a, 0))
ALT = OB["NEEDLE_R3"]
ALT.animation_data_clear()
for f in range(1, 4411, 10):
    keyrot(ALT, f, (0, -A_(f) * 0.36, 0))   # one turn per 1000 m, unwinding as you sink
ATT = bpy.data.materials["M_attitude"].node_tree.nodes["ATT"]
TA = bpy.data.materials["M_tape_alt"].node_tree.nodes["SCROLL"]; TS = bpy.data.materials["M_tape_spd"].node_tree.nodes["SCROLL"]
for f in range(1, 4411, 6):
    ATT.inputs["Rotation"].default_value = (0, 0, R_(-R2_(f))); ATT.inputs["Rotation"].keyframe_insert("default_value", frame=f)
    ATT.inputs["Location"].default_value = (-0.5, -0.5 + P_(f) * 0.012, 0); ATT.inputs["Location"].keyframe_insert("default_value", frame=f)
    TA.inputs["Location"].default_value = (0, A_(f) / 900.0, 0); TA.inputs["Location"].keyframe_insert("default_value", frame=f)
    TS.inputs["Location"].default_value = (0, V_(f) / 120.0, 0); TS.inputs["Location"].keyframe_insert("default_value", frame=f)
CAU = bpy.data.materials["M_caution"].node_tree.nodes["Emission"].inputs["Strength"]
kv(CAU, "default_value", 1, 0.2)
for t0, t1, per in ((33.9, 46.0, 14), (47.3, 53.4, 18)):
    f = F(t0); on = True
    while f < F(t1):
        kv(CAU, "default_value", f, 25.0 if on else 0.2); f += per; on = not on
kv(CAU, "default_value", F(53.5), 0.2)
for kp in bpy.data.materials["M_caution"].node_tree.animation_data.action.layers[0].strips[0].channelbags[0].fcurves[0].keyframe_points: kp.interpolation = 'CONSTANT'

# loose items float up in the dive (negative g), tumble, then drop
for nm, up, lands in (("MUG_L", 0.32, (-0.85, 1.25, 0.05)), ("MUG_R", 0.28, (0.92, 1.05, 0.05)), ("CLIPBOARD", 0.45, (-0.55, 0.95, 0.01)), ("PEN", 0.5, (-0.2, 1.1, 0.01))):
    o = OB[nm]; p0 = o.location.copy(); rnd = random.Random(nm)
    o.keyframe_insert("location", frame=F(34.8)); keyrot(o, F(34.8), (0, 0, 0))
    for i, t in enumerate((35.6, 36.6, 37.6, 38.6, 39.4)):
        u = (i + 1) / 5
        tgt_ = Vector((0.06 + rnd.uniform(-0.15, 0.15), 2.06 + rnd.uniform(-0.03, 0.06), 1.12 + rnd.uniform(0, 0.2)))
        o.location = p0.lerp(tgt_, smooth(u) * 0.85) + Vector((0, 0, 0.05 * math.sin(u * 7)))
        o.keyframe_insert("location", frame=F(t)); keyrot(o, F(t), (rnd.uniform(-90, 90) * u, rnd.uniform(-90, 90) * u, rnd.uniform(-120, 120) * u))
    o.location = lands; o.keyframe_insert("location", frame=F(40.4)); keyrot(o, F(40.4), (90 if "MUG" in nm else 0, 0, rnd.uniform(0, 300)))
    o.location = lands; o.keyframe_insert("location", frame=F(41.0))

# oxygen masks drop in the cabin (seen through the door on the look-back)
cM = coll("MASKS"); M_mask = mat("M_mask", (0.85, 0.62, 0.05), rough=0.5); M_tube = mat("M_mask_tube", (0.8, 0.8, 0.75), rough=0.6)
for i in range(9):
    y = ROW0 - PITCH * i
    for sx in (-1, 1):
        for k in range(2):
            x = sx * (0.8 + 0.1 * k); mb_ = MB("MASK_%d_%d_%d" % (i, sx, k))
            mb_.cyl((0, 0, -0.28), 0.003, 0.56, M_tube, seg=6); mb_.cyl((0, 0, -0.58), 0.032, 0.06, M_mask, seg=12, r2=0.022)
            mo = mb_.obj(cM); mo.location = (x, y - 0.05, 1.55)
            t0 = 34.0 + 0.05 * i + 0.03 * k
            mo.scale = (1, 1, 0.02); mo.keyframe_insert("scale", frame=F(t0))
            mo.scale = (1, 1, 1.08); mo.keyframe_insert("scale", frame=F(t0 + 0.35)); mo.scale = (1, 1, 0.96); mo.keyframe_insert("scale", frame=F(t0 + 0.6))
            mo.scale = (1, 1, 1.0); mo.keyframe_insert("scale", frame=F(t0 + 0.9))
            for f in range(F(t0 + 1.0), 4411, 50):
                keyrot(mo, f, (random.uniform(-8, 8) * (2.5 if f < F(44) else 1), random.uniform(-8, 8) * (2.5 if f < F(44) else 1), 0))

# clouds whipping past beside the plane in the descent, and a bird flock ahead
cW = bpy.data.collections["CLOUDS"]; cm_ = bpy.data.materials["M_cloud"]
for i, t in enumerate([47.4 + 0.55 * k for k in range(18)]):
    f = F(t); hd = R_(H_(f)); fw = Vector((-math.sin(hd), math.cos(hd))); rt = Vector((fw.y, -fw.x))
    side = (1 if i % 2 else -1) * random.uniform(45, 140)
    c = POS[f] + rt * side
    for j in range(3):
        sz = random.uniform(40, 90)
        me = bpy.data.meshes.new("puff"); me.from_pydata([(-sz, 0, -sz * 0.6), (sz, 0, -sz * 0.6), (sz, 0, sz * 0.6), (-sz, 0, sz * 0.6)], [], [(0, 1, 2, 3)])
        me.uv_layers.new(); me.materials.append(cm_)
        o = bpy.data.objects.new("PUFF_%02d_%d" % (i, j), me); cW.objects.link(o); o.parent = EM
        o.location = (c.x + random.uniform(-30, 30), c.y + random.uniform(-30, 30), A_(f) + random.uniform(-35, 25))
        o.rotation_euler = (0, 0, hd + R_(j * 60)); o.visible_shadow = False
cB = coll("BIRDS"); M_bird = mat("M_bird", (0.05, 0.05, 0.05), rough=0.8)
fc = F(61.6); hd = R_(H_(fc)); fw = Vector((-math.sin(hd), math.cos(hd))); rt = Vector((fw.y, -fw.x))
for i in range(22):
    bmb = MB("BIRD_%02d" % i); bmb.box((-0.45, 0, 0), (0.9, 0.18, 0.03), M_bird, rot=(0, 18, 0)); bmb.box((0.45, 0, 0), (0.9, 0.18, 0.03), M_bird, rot=(0, -18, 0))
    bmb.box((0, 0.1, 0), (0.12, 0.6, 0.12), M_bird); bo = bmb.obj(cB); bo.parent = EM
    off = Vector((((i % 11) - 5) * 3.5, -abs((i % 11) - 5) * 3.0 + (i // 11) * 4))
    for f in range(F(57.0), F(64.0), 10):
        p = POS[fc] + fw * 60 + rt * (-60 + (f - F(57)) * 0.32) + rt * off.x + fw * off.y
        bo.location = (p.x, p.y, A_(fc) + 6 + 2 * math.sin(f * 0.05 + i)); bo.keyframe_insert("location", frame=f)
        bo.rotation_euler = (0, 0, hd - R_(90)); bo.keyframe_insert("rotation_euler", frame=f)
        bo.scale = (1, 1, 1 + 0.8 * math.sin(f * 0.6 + i)); bo.keyframe_insert("scale", frame=f)

# ------------------------------------------------------------------ YOU (POV body)
YOU = OB["YOU"]
RY = make_human_ctrl(YOU)
H = Human(RY)
SEAT = Vector((-0.55, ROW0 - 3 * PITCH))     # aisle seat row 4
def hand(s, f, W, d=(0, 1, 0), n=(0, 0, 1), pole=None, curl=20):
    sx = 1 if s == "L" else -1
    if pole is None: pole = Vector(W) + Vector((sx * 0.35, -0.25, -0.35))
    H.key_hand(s, f, Vector(W), Vector(d), Vector(n), Vector(pole))
    fingers_curl(RY, f, s, curl)
def feet(f, L, R, yawL=180, yawR=180, liftL=0, liftR=0):
    H.key_foot("L", f, Vector(L), yawL, liftL); H.key_foot("R", f, Vector(R), yawR, liftR)
def body(f, pos, yaw=180, flex=0, side=0, sflex=0, twist=0, sside=0, head=(0, 0)):
    H.key_root(f, Vector(pos), yaw=yaw, flex=flex, side=side)
    H.key_spine(f, flex=sflex, twist=twist, side=sside, head=head)

sx_, sy_ = SEAT.x, SEAT.y
SIT = (sx_, sy_ - 0.10, 0.60)
FL_ = (sx_ - 0.1, sy_ + 0.42); FR_ = (sx_ + 0.1, sy_ + 0.42)
# --- beat 1-2: waking in the seat
body(1, SIT, flex=-14, sflex=18, head=(25, 0)); feet(1, FL_, FR_)
hand("L", 1, (sx_ - 0.13, sy_ + 0.12, 0.66), d=(0.2, 1, -0.4), n=(0, 0, 1), curl=35)
hand("R", 1, (sx_ + 0.13, sy_ + 0.12, 0.66), d=(-0.2, 1, -0.4), n=(0, 0, 1), curl=35)
body(F(0.8), SIT, flex=-10, sflex=10, head=(10, 0))
hand("L", F(0.8), (sx_ - 0.10, sy_ + 0.12, 1.05), d=(0.4, 0.3, 1), n=(0.3, 1, 0), curl=30)     # hands rise to the face
hand("R", F(0.8), (sx_ + 0.12, sy_ + 0.14, 1.07), d=(-0.4, 0.3, 1), n=(-0.3, 1, 0), curl=30)
hand("L", F(1.6), (sx_ - 0.08, sy_ + 0.16, 0.90), d=(0.3, 1, 0.3), n=(0, 0.2, 1), curl=20)
hand("R", F(1.6), (sx_ + 0.12, sy_ + 0.16, 0.88), d=(-0.3, 1, 0.3), n=(0, 0.2, 1), curl=20)
body(F(1.6), SIT, flex=-8, sflex=4, head=(0, 0))
body(F(2.4), SIT, flex=-8, sflex=4, twist=-25, head=(5, -35))
hand("L", F(2.4), (sx_ - 0.10, sy_ + 0.28, 0.66), d=(0, 1, -0.4), n=(0, 0, 1), curl=45)          # grips own thigh (the shared armrest is the neighbour's)
hand("R", F(2.4), (sx_ + 0.235, sy_ + 0.08, 0.66), d=(0, 1, -0.2), n=(0, 0, 1), curl=45)
body(F(3.4), SIT, flex=-6, sflex=10, twist=15, head=(30, 20))
hand("L", F(3.6), (sx_ - 0.30, sy_ + 0.35, 0.80), d=(-0.4, 1, 0), n=(0, 0, 1), curl=15)            # reaches toward the tipping cup
body(F(4.6), SIT, flex=-6, sflex=6, twist=30, side=4, head=(10, 35))
hand("L", F(4.6), (sx_ - 0.33, sy_ + 0.05, 0.75), d=(-0.5, 1, 0), n=(0, 0, 1), curl=20)
hand("R", F(4.6), (sx_ + 0.235, sy_ + 0.08, 0.66), d=(0, 1, -0.2), n=(0, 0, 1), curl=45)
# beat 2: lean over neighbour to the window
LEAN = (sx_ - 0.20, sy_ - 0.1, 0.59)
body(F(5.8), LEAN, flex=-2, side=-6, sflex=12, twist=40, sside=-20, head=(0, 40))
hand("L", F(5.8), (sx_ - 0.10, sy_ + 0.30, 0.66), d=(0, 1, -0.4), n=(0, 0, 1), curl=45)             # braces on own knee (the armrest is the neighbour's)
body(F(6.9), LEAN, flex=0, side=-8, sflex=14, twist=50, sside=-26, head=(0, 40))
hand("L", F(6.9), (sx_ - 0.11, sy_ + 0.31, 0.66), d=(0, 1, -0.4), n=(0, 0, 1), curl=48)
hand("L", F(8.0), (sx_ - 0.10, sy_ + 0.30, 0.66), d=(0, 1, -0.4), n=(0, 0, 1), curl=45)
body(F(8.0), LEAN, flex=0, side=-8, sflex=18, twist=50, sside=-24, head=(20, 40))
hand("R", F(8.0), (sx_ + 0.235, sy_ + 0.08, 0.66), d=(0, 1, -0.2), n=(0, 0, 1), curl=45)
feet(F(8.6), FL_, FR_)
# beat 3: stand, step into the aisle, walk
body(F(8.6), SIT, flex=4, sflex=10, twist=10, head=(20, 10))
hand("L", F(8.6), (sx_ - 0.235, sy_ + 0.08, 0.66), d=(0, 1, -0.2), n=(0, 0, 1), curl=45)
hand("R", F(8.6), (sx_ + 0.235, sy_ + 0.08, 0.66), d=(0, 1, -0.2), n=(0, 0, 1), curl=45)
body(F(9.2), (sx_ + 0.08, sy_ - 0.02, 0.70), flex=14, sflex=8, head=(10, 0))
hand("L", F(9.2), (sx_ - 0.235, sy_ + 0.12, 0.64), d=(0, 1, -0.3), n=(0, 0, 1), curl=45)
hand("R", F(9.2), (sx_ + 0.235, sy_ + 0.12, 0.64), d=(0, 1, -0.3), n=(0, 0, 1), curl=45)
feet(F(9.2), FL_, FR_)
feet(F(9.6), FL_, (0.05, sy_ + 0.30), liftR=0.0)
H.key_foot("R", F(9.4), Vector(((FR_[0] + 0.05) / 2, sy_ + 0.37)), 180, 0.12)
body(F(9.8), (-0.12, sy_ + 0.18, 0.80), flex=12, sflex=8, head=(0, -10))
hand("L", F(9.8), (-0.60, sy_ + 0.40, 1.0), d=(0, 1, 0), n=(-1, 0, 0), curl=30)                    # hand on the seatback ahead
hand("R", F(9.8), (0.20, sy_ + 0.35, 1.0), d=(0, 1, -1), n=(0, 0, 1), curl=20)
H.key_foot("L", F(9.85), Vector(((FL_[0] - 0.12) / 2, sy_ + 0.33)), 180, 0.10)
feet(F(10.0), (-0.12, sy_ + 0.42), (0.05, sy_ + 0.30))
W0, W1 = F(10.0), F(11.6)
yA, yB = sy_ + 0.27, -1.36
def wpath(f):
    u = (f - W0) / (W1 - W0); u = smooth(u) * 0.35 + u * 0.65
    return Vector((-0.04 + 0.04 * u, yA + (yB - yA) * u, 0))
H.walk(wpath, lambda f: 180.0, W0, W1, stride=0.72, lift=0.09, bob=0.03, lean=10)
for i_, f in enumerate(range(F(10.1), F(11.5), 14)):      # relaxed arm swing while walking (no hands on seats or heads)
    p_ = wpath(f); sw = 0.10 * math.sin(i_ * 1.6)
    hand("L", f, (p_.x - 0.24, p_.y + 0.06 + sw, 0.86), d=(0.1, 0.3, -1), n=(-1, 0, 0), curl=30)
    hand("R", f, (p_.x + 0.24, p_.y + 0.06 - sw, 0.86), d=(-0.1, 0.3, -1), n=(1, 0, 0), curl=30)
# beat 4: door push (door free edge / panel point follows rotation)
def door_pt(f, local):
    sc.frame_set(f); return DOOR.matrix_world @ Vector(local)
STAND_Z = H.root_head.z - 0.03
body(F(11.7), (-0.06, -1.30, STAND_Z), flex=6, sflex=4, head=(0, 0)); feet(F(11.7), (-0.16, -1.36), (0.04, -1.22))
hand("R", F(11.6), (0.10, -0.70, 1.12), d=(0, 0.3, 1), n=(0, -1, 0), curl=5)
for f in (F(11.74), F(11.82), F(11.9), F(11.98)):
    W = door_pt(f, (-0.45, -0.07, 1.12)); hand("R", f, W, d=(0, 0.3, 1), n=(0, -1, 0), curl=5)
hand("L", F(11.9), (-0.44, -0.62, 1.25), d=(0, 0, 1), n=(1, 0, 0), curl=40)                          # left hand on the frame
body(F(12.5), (-0.04, -0.80, STAND_Z - 0.02), flex=12, sflex=8, head=(10, 0)); feet(F(12.5), (-0.14, -0.92), (0.06, -0.66))
H.key_foot("R", F(12.2), Vector((0.04, -0.77)), 180, 0.06)
# beat 5: look down at the captain, step over him
body(F(14.1), (0.02, -0.66, STAND_Z - 0.02), flex=14, sflex=20, head=(35, 0))
hand("L", F(14.1), (-0.44, -0.60, 1.25), d=(0, 0, 1), n=(1, 0, 0), curl=50)
hand("R", F(12.6), (0.40, -0.50, 1.25), d=(0, 0, 1), n=(-1, 0, 0), curl=50)
hand("R", F(14.4), (0.36, -0.48, 1.25), d=(0, 0, 1), n=(-1, 0, 0), curl=50)
feet(F(14.1), (-0.1, -0.92), (0.1, -0.62))
H.key_foot("L", F(14.25), Vector((-0.07, -0.75)), 180, 0.08); H.key_foot("L", F(14.5), Vector((-0.05, -0.40)), 180, 0)
H.key_foot("R", F(14.5), Vector((0.1, -0.62)), 180, 0)
H.key_foot("R", F(14.7), Vector((0.1, -0.3)), 180, 0.10); H.key_foot("R", F(14.9), Vector((0.12, 0.02)), 180, 0)
body(F(14.9), (0.05, -0.22, STAND_Z - 0.04), flex=16, sflex=22, head=(40, -5))
H.key_foot("L", F(14.9), Vector((-0.05, -0.40)), 180, 0)
H.key_foot("L", F(15.15), Vector((-0.03, 0.45)), 180, 0.42); H.key_foot("L", F(15.45), Vector((-0.06, 0.92)), 180, 0)
body(F(15.4), (0.05, 0.48, STAND_Z + 0.04), flex=10, sflex=18, head=(40, -5))
H.key_foot("R", F(15.5), Vector((0.12, 0.02)), 180, 0)
H.key_foot("R", F(15.8), Vector((0.14, 0.5)), 180, 0.40); H.key_foot("R", F(16.1), Vector((0.16, 0.92)), 180, 0)
hand("L", F(15.0), (-0.44, -0.60, 1.25), d=(0, 0, 1), n=(1, 0, 0), curl=50)
hand("L", F(15.6), (-0.30, 0.95, 1.40), d=(0, 1, 0), n=(0, 0, -1), curl=50)                         # grabs captain seat headrest
hand("R", F(15.9), (0.30, 0.95, 1.30), d=(0, 1, 0), n=(0, 0, -1), curl=50)
POSW = (0.04, 0.88, STAND_Z)
body(F(16.3), POSW, flex=4, sflex=4, head=(0, 0)); feet(F(16.3), (-0.06, 0.92), (0.16, 0.92))
# beat 6: look at FO
body(F(16.8), POSW, flex=4, sflex=8, twist=-25, head=(15, -35))
body(F(17.8), (0.10, 0.92, STAND_Z - 0.03), flex=10, sflex=18, twist=-30, sside=10, head=(15, -35))
hand("R", F(17.8), (0.30, 1.18, 1.22), d=(0, 1, -0.2), n=(0, 0, -1), curl=50)                         # on FO seat back
body(F(18.8), POSW, flex=8, sflex=14, twist=-10, head=(20, -10))
# beat 7: grab the radio handset
HS = OB["HANDSET"]; HS0 = HS.matrix_world.copy()
body(F(19.7), (0.05, 0.92, STAND_Z - 0.05), flex=18, sflex=26, twist=-8, head=(30, -10))
hand("R", F(19.7), (0.14, 1.24, 0.95), d=(0, 1, -1), n=(0, 0.6, 1), curl=10)
GRIP = (0.12, 1.33, 0.835)
hand("R", F(20.6), GRIP, d=(0, 1, -0.3), n=(0, 0, -1), curl=15)
hand("R", F(20.9), GRIP, d=(0, 1, -0.3), n=(0, 0, -1), curl=55)            # closed on it
hand("L", F(20.0), (-0.36, 1.10, 1.42), d=(0, 1, 0), n=(0, 0, -1), curl=60)
for t_ in (21.0, 22.2, 23.4, 24.6, 25.8): hand("L", F(t_), (-0.37 + 0.01 * (t_ % 2), 1.11, 1.43), d=(0, 1, 0), n=(0, 0, -1), curl=60)
body(F(21.8), POSW, flex=6, sflex=6, head=(0, -5))
hand("R", F(21.8), (0.14, 1.42, 1.16), d=(-0.3, 0.2, 1), n=(-0.6, -1, 0), curl=80)
for i, t in enumerate((22.8, 23.4, 23.9, 24.5, 25.0)):
    j = 0.012 * (1 if i % 2 else -1)
    hand("R", F(t), (0.12 + j, 1.38, 1.20 + j), d=(-0.3, 0.1, 1), n=(-0.8, -1, 0), curl=80)
    body(F(t), (POSW[0], POSW[1], POSW[2] - 0.01 * (i % 2)), flex=8 + 3 * (i % 2), sflex=10, head=(5 + 4 * (i % 2), -3))
# beat 8: silence, lower handset, put it back
body(F(25.6), POSW, flex=14, sflex=20, head=(30, 0))
hand("R", F(25.6), (0.10, 1.38, 1.08), d=(0, 0.3, 1), n=(-0.6, -1, 0), curl=78)
hand("R", F(26.3), GRIP, d=(0, 1, -0.3), n=(0, 0, -1), curl=55)
hand("R", F(26.6), GRIP, d=(0, 1, -0.3), n=(0, 0, -1), curl=10)
# beat 9: haul the FO out
body(F(26.9), (0.04, 0.84, STAND_Z), flex=10, sflex=10, twist=-25, head=(15, -20))
feet(F(27.2), (-0.08, 0.95), (0.14, 0.98))
body(F(27.8), (0.04, 0.9, STAND_Z - 0.06), flex=10, sflex=10, twist=-15, head=(20, -15))
feet(F(27.8), (-0.08, 0.98), (0.14, 1.02))
def fo_shoulders(f, s):
    sc.frame_set(f); nm = "upperarm01." + s
    return FO.matrix_world @ FO.pose.bones[nm].head
def fo_point(f, bone, off):
    sc.frame_set(f); return FO.matrix_world @ FO.pose.bones[bone].head + Vector(off)
hand("L", F(27.3), (-0.04, 1.08, 1.02), d=(0.3, 1, 0), n=(0, 0, 1), curl=40)      # low approach under the eye line
hand("R", F(27.3), (0.16, 1.10, 1.02), d=(0.3, 1, 0), n=(0, 0, 1), curl=40)
for f in range(F(27.9), F(33.3), 8):          # left hand on the collar, right hand on his near shoulder seam, outside the jacket
    hand("L", f, fo_point(f, "neck01", (-0.04, -0.15, 0.05)), d=(0.3, 1, -0.4), n=(0, -0.5, 1), curl=72)
    hand("R", f, fo_point(f, "upperarm01.L", (-0.07, -0.10, 0.21)), d=(0.3, 1, -0.6), n=(0, -0.3, 1), curl=72)          # top of his near shoulder, outside the jacket
body(F(28.8), (0.0, 0.84, STAND_Z - 0.08), flex=12, sflex=6, twist=-15, head=(10, -10))
feet(F(29.2), (-0.14, 0.72), (0.10, 0.80)); H.key_foot("L", F(29.0), Vector((-0.05, 0.76)), 180, 0.05)
body(F(29.8), (-0.10, 0.64, STAND_Z - 0.10), flex=10, sflex=8, twist=-10, head=(10, -10))
feet(F(30.4), (-0.24, 0.64), (0.0, 0.68)); H.key_foot("R", F(30.1), Vector((0.05, 0.74)), 180, 0.06)
body(F(30.6), (-0.12, 0.64, STAND_Z - 0.12), flex=8, sflex=8, twist=-5, head=(15, 0))
body(F(31.4), (-0.10, 0.64, STAND_Z - 0.16), flex=10, sflex=10, twist=-5, head=(20, 0))
body(F(32.4), (0.12, 0.62, STAND_Z - 0.16), flex=10, sflex=10, twist=-20, head=(25, -10))
feet(F(32.4), (0.04, 0.62), (0.30, 0.68))
body(F(33.2), (0.16, 0.62, STAND_Z - 0.16), flex=10, sflex=10, twist=-25, head=(30, -15))
# beat 10-11: alarms, jolt, stagger forward to the windscreen
body(F(33.7), (0.18, 0.76, STAND_Z - 0.12), flex=20, sflex=0, twist=-5, head=(-10, 0))
hand("L", F(33.9), (-0.30, 0.98, 1.40), d=(0, 1, 0), n=(0, 0, -1), curl=55)
hand("R", F(33.9), (0.35, 1.10, 1.40), d=(0, 1, 0), n=(0, 0, -1), curl=55)
feet(F(34.2), (0.08, 0.74), (0.30, 0.80))
body(F(34.6), (0.16, 0.80, STAND_Z - 0.08), flex=14, sflex=0, side=6, head=(0, 5))
feet(F(35.1), (0.02, 0.90), (0.26, 0.82)); H.key_foot("L", F(34.85), Vector((0.05, 0.82)), 180, 0.07)
body(F(35.5), (0.12, 0.92, STAND_Z - 0.06), flex=18, sflex=6, side=-8, head=(-5, -5))
hand("L", F(35.5), (-0.10, 1.28, 1.0), d=(0, 1, -0.5), n=(0, 0, 1), curl=40)                        # braces on the pedestal
hand("R", F(35.5), (0.30, 1.12, 1.42), d=(0, 1, 0), n=(0, 0, -1), curl=60)
body(F(36.5), (0.14, 0.98, STAND_Z - 0.10), flex=26, sflex=14, side=6, head=(0, 0))
body(F(37.6), (0.20, 0.98, STAND_Z - 0.12), flex=28, sflex=14, side=-6, head=(5, -8))
feet(F(37.6), (0.06, 0.92), (0.30, 0.85))
# beat 12: into the right seat, both hands on the yoke
CS = (0.52, 1.36, 0.66)
body(F(38.3), (0.28, 1.42, 0.80), yaw=180, flex=20, sflex=10, head=(5, 0))
H.key_foot("R", F(38.1), Vector((0.36, 1.30)), 180, 0.1)
feet(F(38.5), (0.30, 1.45), (0.45, 1.50), liftL=0.05)
body(F(38.8), CS, flex=-6, sflex=6, head=(10, 0))
FSEAT = ((0.42, 1.95), (0.62, 1.95))
H.key_foot("L", F(38.9), Vector((0.42, 1.7)), 180, 0.15); H.key_foot("R", F(39.0), Vector((0.62, 1.7)), 180, 0.15)
feet(F(39.3), *FSEAT)
def grip(f, s):
    sc.frame_set(f); M = YR.matrix_world
    return M @ Vector(((-0.16 if s == "L" else 0.16), -0.20, 0.79))
def hands_on_yoke(f, curl=65, jitter=0.0):
    for s in "LR":
        W = grip(f, s) + Vector((random.uniform(-jitter, jitter), random.uniform(-jitter, jitter), random.uniform(-jitter, jitter)))
        sx = 1 if s == "L" else -1
        hand(s, f, W - Vector((sx * 0.012, 0.022, 0.012)), d=(sx * 0.35, 0.6, 1.0), n=(-sx * 0.2, -1.0, 0.3), pole=W + Vector((sx * 0.4, -0.3, -0.25)), curl=max(curl, 78))
for f in range(F(39.2), F(45.0), 15):
    hands_on_yoke(f, 70, 0.006)
SEATB = lambda f, flex=-4, sflex=8, twist=0, head=(10, 0), dz=0.0, dy=0.0, dx=0.0: body(f, (CS[0] + dx, CS[1] + dy, CS[2] + dz), flex=flex, sflex=sflex, twist=twist, head=head)
for t, sf, hd in ((39.8, 26, (30, 0)), (40.8, 16, (10, 20)), (41.8, 10, (0, 0)), (42.5, 8, (0, 0)), (43.6, 14, (25, 0)), (44.7, 6, (0, 0)), (45.8, 4, (0, 0))):
    SEATB(F(t), sflex=sf, head=hd, flex=4 if t < 44 else 0, dy=0.06)
for f in range(F(45.0), F(56.6), 20):
    hands_on_yoke(f, 60, 0.004)
# beat 14-15
SEATB(F(47.1), sflex=16, head=(15, -5)); SEATB(F(48.4), sflex=26, head=(18, -8), dy=0.08)
SEATB(F(49.6), sflex=2, head=(0, 0)); SEATB(F(51.0), sflex=8, twist=-12, head=(0, -50)); SEATB(F(52.3), sflex=2, head=(0, 0))
SEATB(F(53.5), sflex=16, head=(0, 0), dy=0.1); SEATB(F(54.6), sflex=20, head=(5, 0), dy=0.12); SEATB(F(55.7), sflex=10, head=(5, 0), dy=0.05)
# beat 16: hand to throttle, indecision
THR = lambda: (OB["THROTTLE_1"].matrix_world @ Vector((0, 0, 0.19)))
hands_on_yoke(F(56.6), 55)
hand("R", F(57.2), (0.20, 1.80, 1.02), d=(-1, 0.5, -0.5), n=(0, 0, 1), curl=20)
hand("R", F(57.7), (0.09, 1.86, 1.0), d=(-0.6, 1, -0.6), n=(0, 0, 1), curl=15)
SEATB(F(56.8), sflex=20, twist=28, head=(20, 30), dx=-0.08, dy=0.06); SEATB(F(58.0), sflex=4, head=(0, 0))
hand("R", F(58.6), (0.11, 1.82, 1.02), d=(-0.6, 1, -0.6), n=(0, 0, 1), curl=15)
sc.frame_set(F(59.2)); tw = THR()
hand("R", F(59.2), tw + Vector((0.0, -0.035, 0.035)), d=(-0.3, 1, -0.9), n=(0, -0.3, 1), curl=70)
hand("R", F(59.8), tw + Vector((0.0, -0.075, 0.035)), d=(-0.3, 1, -0.9), n=(0, -0.3, 1), curl=70)
SEATB(F(59.2), sflex=30, twist=34, head=(20, 30), dx=-0.2, dy=0.14)
hand("R", F(60.4), grip(F(60.4), "R") - Vector((0, 0.035, 0)), d=(-0.6, 1, 0.5), n=(0.3, 0.2, 1), curl=65)
SEATB(F(60.4), sflex=14, head=(25, 0)); SEATB(F(61.5), sflex=2, head=(0, 0)); SEATB(F(62.6), sflex=4, twist=30, head=(0, 45))
hand("R", F(63.2), (0.12, 1.85, 1.03), d=(-0.6, 1, -0.6), n=(0, 0, 1), curl=20)
SEATB(F(63.6), sflex=20, twist=28, head=(20, 30), dx=-0.08, dy=0.06)
hand("R", F(64.2), (0.13, 1.84, 1.03), d=(-0.6, 1, -0.6), n=(0, 0, 1), curl=25)
for f in range(F(56.6), F(72.6), 60):
    W = grip(f, "L"); hand("L", f, W - Vector((0, 0.035, 0)), d=(0.6, 1, 0.5), n=(-0.3, 0.2, 1), pole=W + Vector((0.4, -0.3, -0.25)), curl=65)
# beat 17: look back over the right shoulder
hand("R", F(65.0), (0.78, 1.36, 0.78), d=(0, 1, -0.3), n=(0, 0, 1), curl=60)                 # own right armrest                     # braces on the pedestal while turning
SEATB(F(64.6), sflex=14, twist=45, head=(0, 50), dy=0.12, dx=-0.10); SEATB(F(65.8), sflex=24, twist=70, head=(25, 70), dy=0.18, dx=-0.18)
SEATB(F(66.9), sflex=16, twist=75, head=(5, 80), dy=0.16, dx=-0.18); SEATB(F(67.9), sflex=10, twist=40, head=(5, 50), dy=0.08, dx=-0.06)
# beat 18-19: forward, hands back on the yoke, wide-eyed
SEATB(F(68.9), sflex=4, twist=-5, head=(0, -5))
for f in range(F(68.9), F(73.5), 20):
    hands_on_yoke(f, 70, 0.004)
SEATB(F(70.0), sflex=8, head=(0, 0), dy=0.06); SEATB(F(71.0), sflex=4, head=(-4, 0), dy=0.03); SEATB(F(72.5), sflex=2, head=(-6, 0)); SEATB(F(73.4), sflex=3, head=(-5, 0))
for s in "LR":
    RY.key_rot("orbicularis03." + s, 1, [("X", 25)]); RY.key_rot("orbicularis03." + s, F(0.6), [("X", 10)])
    RY.key_rot("orbicularis03." + s, F(1.2), [("X", 0)]); RY.key_rot("orbicularis03." + s, F(71.9), [("X", 0)])
    RY.key_rot("orbicularis03." + s, F(72.4), [("X", -8)])                                             # wide-eyed
RY.key_rot("jaw", 1, [("X", 0)]); RY.key_rot("jaw", F(72.0), [("X", 0)]); RY.key_rot("jaw", F(72.6), [("X", 7)])

def quick_steps():
    """turn slow slides between sparse IK_foot keys into quick lifted steps (hold, then step in the last 14 frames)"""
    act = YOU.animation_data.action
    fcs = [fc for fc in act.layers[0].strips[0].channelbags[0].fcurves if fc.data_path.startswith('pose.bones["IK_foot.')]
    for s_ in "LR":
        nm = 'pose.bones["IK_foot.%s"]' % s_
        loc = [fc for fc in fcs if fc.data_path == nm + ".location"]; rot = [fc for fc in fcs if fc.data_path == nm + ".rotation_quaternion"]
        loc.sort(key=lambda c: c.array_index); rot.sort(key=lambda c: c.array_index)
        keys = sorted({round(k.co.x) for fc in loc for k in fc.keyframe_points})
        Rr = RY.rest("IK_foot." + s_).to_3x3()
        lift_local = Rr.inverted() @ Vector((0, 0, 0.07))
        adds = []
        for k0, k1 in zip(keys, keys[1:]):
            if k1 - k0 <= 20: continue
            v0 = Vector([fc.evaluate(k0) for fc in loc]); v1 = Vector([fc.evaluate(k1) for fc in loc])
            if (v1 - v0).length < 0.02: continue
            q0 = [fc.evaluate(k0) for fc in rot]
            adds.append((k1 - 14, v0, q0, None)); adds.append((k1 - 7, (v0 + v1) / 2 + lift_local, None, None))
        for f, v, q, _ in adds:
            for i, fc in enumerate(loc): fc.keyframe_points.insert(f, v[i])
            if q:
                for i, fc in enumerate(rot): fc.keyframe_points.insert(f, q[i])
        print("QUICKSTEPS", s_, len(adds) // 2)
quick_steps()

def add_joint_limits(arm, f_ref):
    """Limit Rotation (local) on every finger, thumb and wrist bone: forward curl only, small spread; wrist +-60 flex / +-25 side"""
    sc.frame_set(f_ref); n = 0
    for pb in arm.pose.bones:
        nm = pb.name
        if nm.startswith("finger"):
            e = pb.matrix_basis.to_euler('XYZ'); ax = max(range(3), key=lambda i: abs(e[i])); sg = 1 if e[ax] >= 0 else -1
            thumb = nm.startswith("finger1")
            lim = R_(70 if thumb else 90); side = R_(30 if thumb else 10)
            c = pb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'; c.name = "HAND_LIMIT"
            c.use_limit_x = c.use_limit_y = c.use_limit_z = True
            for i, a_ in enumerate("xyz"):
                if i == ax and abs(e[ax]) > R_(2):
                    lo, hi = (0.0, lim) if sg > 0 else (-lim, 0.0)
                else:
                    lo, hi = -side, side
                setattr(c, "min_" + a_, lo - R_(1)); setattr(c, "max_" + a_, hi + R_(1))
            n += 1
        elif nm.startswith("wrist."):
            c = pb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'; c.name = "WRIST_LIMIT"
            c.use_limit_x = c.use_limit_y = c.use_limit_z = True
            c.min_x, c.max_x = -R_(60), R_(60); c.min_z, c.max_z = -R_(25), R_(25); c.min_y, c.max_y = -R_(45), R_(45)
            n += 1
        elif nm.startswith("lowerarm01."):
            pb.use_ik_limit_x = True; pb.ik_min_x = R_(-145); pb.ik_max_x = R_(145)
    return n
nl = add_joint_limits(YOU, F(40.2)) + add_joint_limits(FO, 1) + add_joint_limits(CA, 1)
for (arm_, *_r) in PASS: nl += add_joint_limits(arm_, 1)
print("JOINT LIMITS", nl)

# ------------------------------------------------------------------ camera (head-cam baked from the eyes, authored look)
camd = bpy.data.cameras.new("CAM_Film"); camd.lens = 14; camd.clip_start = 0.03; camd.clip_end = 90000; camd.sensor_fit = 'AUTO'
CAM = bpy.data.objects.new("CAM_Film", camd); sc.collection.objects.link(CAM); sc.camera = CAM
LOOK = [(0.0, 0, -48), (0.6, 4, -38), (1.2, 0, -8), (2.3, -65, -10), (3.4, 53, -40), (4.6, 62, -14),
        (5.8, 85, -6), (6.4, 94, -2), (7.1, 104, -30), (7.8, 82, 6), (8.4, 96, -18), (9.0, 30, -32), (9.6, -15, -14), (10.2, 0, -6), (10.8, -32, -14), (11.2, -4, -12),
        (11.6, -14, -34), (12.1, -30, -10), (12.8, -40, -14), (13.5, 10, -32), (14.1, 42, -42), (14.6, 38, -50), (15.1, 5, -66), (15.8, -5, -25), (16.4, -25, -18),
        (17.2, -45, -14), (17.8, -42, -16), (18.8, -22, -26), (19.7, -14, -58), (20.8, -14, -55), (21.8, -5, -30),
        (22.8, 4, -30), (23.9, -6, -26), (25.2, 0, -52), (26.0, 4, -48), (26.9, -48, -20), (28.0, -42, -26), (29.0, -34, -22),
        (30.5, -16, -30), (31.8, -30, -38), (32.5, -78, -58), (33.2, -88, -55), (33.7, -8, -8), (34.6, -4, -4), (35.5, 6, -2), (36.5, 0, -10), (37.6, -10, -22),
        (38.8, 0, -28), (39.8, 0, -48), (40.8, 22, -34), (41.8, 0, -8), (42.5, 0, -5), (43.6, 0, -34), (44.7, 0, -6), (45.8, 4, -4),
        (47.1, -14, -26), (48.0, -16, -30), (48.8, -4, -6), (49.6, 0, -48), (50.4, -38, -14), (51.2, -34, -16), (52.0, -10, -8), (52.9, 60, -34), (53.5, 0, -12), (54.1, -22, -10), (54.8, 14, -20), (55.5, -4, -26), (56.1, 6, -10),
        (56.8, 48, -30), (57.4, 30, -14), (58.0, 0, -8), (58.6, -12, 2), (59.2, 48, -33), (60.4, 5, -44), (61.5, 0, 4), (62.0, 8, -4), (62.6, 72, -12), (63.6, 45, -30),
        (64.6, 100, -12), (65.8, 150, -40), (66.9, 168, -8), (67.9, 110, -14), (68.9, 30, -8), (69.6, -14, -6), (70.3, 12, -16), (70.9, -4, -4), (71.4, 0, -8)]
ROLL = {33.7: 0, 35.5: -6, 36.5: 8, 37.6: -10, 38.8: 6, 40.8: -4, 42.5: 0}
yaw_f = catmull([(F(t), y) for t, y, p in LOOK]); pit_f = catmull([(F(t), p) for t, y, p in LOOK])
rol_f = catmull([(1, 0.0)] + [(F(t), r) for t, r in sorted(ROLL.items())] + [(4410, 0.0)])
def shake(f):
    t = f / FPS; a = 0.0
    if F(21.5) <= f <= F(25.4): a = 0.25
    if F(33.7) <= f <= F(44.5): a = 1.2 * min(1, (f - F(33.7)) / 20) * (1 - max(0, (f - F(42.5)) / (F(44.5) - F(42.5))))
    if F(38.8) <= f <= F(46.0): a = max(a, 0.25)                      # straining on the yoke
    br = Vector((0.15 * math.sin(t * 1.9), 0.1 * math.sin(t * 1.3 + 1), 0.08 * math.sin(t * 0.9)))   # breathing sway, never still
    return Vector((math.sin(t * 37.1) * 0.6 + math.sin(t * 23.3), math.sin(t * 29.7) + math.sin(t * 41.9) * 0.5, math.sin(t * 19.1))) * a + br
FLOAT0, FLOATR, FLOAT1 = F(71.4), F(72.6), F(73.5)
FREE = [(FLOAT0, None), (F(72.0), Vector((0.66, 1.62, 1.44))), (FLOATR, Vector((0.56, 1.93, 1.34))), (4410, Vector((0.535, 1.86, 1.31)))]
def eye(f):
    M = YOU.matrix_world; pb = YOU.pose.bones
    e = (M @ pb["eye.L"].head + M @ pb["eye.R"].head) / 2
    hm = (M @ pb["head"].matrix).to_3x3()
    fwd = -(hm @ Vector((0, 0, 1))).cross(hm @ Vector((1, 0, 0)))   # head bone local -Y? use world-facing from eyes
    return e
def head_look():
    """head bone tracks the authored look so the body agrees with the camera (and the face is right in beat 19)"""
    tgt = empty("LOOK_TGT", (0, 0, 0), bpy.data.collections["HUMANS"])
    Rb = YOU.data.bones["head"].matrix_local.to_3x3()
    fl = Rb.transposed() @ Vector((0, -1, 0))
    ax = max(range(3), key=lambda i: abs(fl[i])); neg = fl[ax] < 0
    c = YOU.pose.bones["head"].constraints.new('DAMPED_TRACK'); c.target = tgt
    c.track_axis = ("TRACK_NEGATIVE_" if neg else "TRACK_") + "XYZ"[ax]
    c.influence = 0.9
    for f in range(1, 4411, 3):
        sc.frame_set(f)
        base = YOU.matrix_world @ YOU.pose.bones["neck03"].head
        Rm = Euler((R_(90 + pit_f(f)), 0, R_(yaw_f(f))), 'XYZ').to_matrix()
        tgt.location = base + Rm @ Vector((0, 0, -3.0)); tgt.keyframe_insert("location", frame=f)
def bake():
    head_look()
    for o in YOU.children:
        if any(k in o.name for k in ("short02", "eyebrow", "eyelashes")):
            o.visible_camera = False; o.keyframe_insert("visible_camera", frame=FLOAT0 - 1)
            o.visible_camera = True; o.keyframe_insert("visible_camera", frame=FLOAT0)
            o.visible_camera = False
            o.keyframe_insert("visible_camera", frame=1)
    hidden = []
    for c in (bpy.data.collections["PASSENGERS"],):
        lc = bpy.context.view_layer.layer_collection.children[c.name]; lc.exclude = True; hidden.append(lc)
    E = {}; HSM = {}
    hold0, hold1 = F(20.9), F(26.3)
    for f in range(1, 4411):
        sc.frame_set(f)
        E[f] = eye(f)
        if hold0 <= f <= hold1:
            Mw = YOU.matrix_world @ YOU.pose.bones["wrist.R"].matrix
            HSM[f] = Mw
    for lc in hidden: lc.exclude = False
    # smooth eye position a little (head-cam stabilisation)
    Es = {}
    for f in E:
        acc = Vector(); n = 0
        for d in range(-4, 5):
            if f + d in E: acc += E[f + d]; n += 1
        Es[f] = acc / n
    # handset: rigid offset from the wrist at the grasp frame
    off = HSM[hold0].inverted() @ HS0
    HS.matrix_world = HS0; HS.keyframe_insert("location", frame=hold0 - 1); HS.keyframe_insert("rotation_euler", frame=hold0 - 1)
    for f in range(hold0, hold1 + 1):
        HS.matrix_world = HSM[f] @ off; HS.keyframe_insert("location", frame=f); HS.keyframe_insert("rotation_euler", frame=f)
    HS.matrix_world = HS0; HS.keyframe_insert("location", frame=hold1 + 1); HS.keyframe_insert("rotation_euler", frame=hold1 + 1)
    face = None
    for f in range(1, 4411):
        fwd = Vector((0, 0.035, 0))
        yw, pt, rl = yaw_f(f), pit_f(f), rol_f(f)
        Rm = Euler((R_(90 + pt), R_(rl), R_(yw)), 'XYZ').to_matrix()
        d = Rm @ Vector((0, 0, -1))
        p = Es[f] + d * 0.045 + Vector((0, 0, 0.005 * math.sin((f / FPS) * 1.6)))
        if f >= FLOAT0:
            if face is None: face = Es[F(72.0)] if F(72.0) in Es else Es[f]
            u = smooth((f - FLOAT0) / (FLOATR - FLOAT0))
            k = catmull([(FREE[0][0], Es[FLOAT0] + d * 0.045)] + FREE[1:])
            q = k(f); p = p.lerp(q, u)
            target_free = Es[min(f, 4410)] + Vector((0, 0.02, -0.03))
            Rf = (target_free - p).to_track_quat('-Z', 'Y').to_matrix()
            Rm = Rm.to_quaternion().slerp(Rf.to_quaternion(), u).to_matrix()
        s = shake(f)
        Rm = Rm @ Euler((R_(s.x), R_(s.z) * 0.5, R_(s.y)), 'XYZ').to_matrix()
        CAM.matrix_world = Matrix.Translation(p) @ Rm.to_4x4()
        CAM.keyframe_insert("location", frame=f); CAM.keyframe_insert("rotation_euler", frame=f)
    camd.lens = 14; camd.keyframe_insert("lens", frame=FLOAT0); camd.lens = 24; camd.keyframe_insert("lens", frame=FLOATR)
if not NOBAKE:
    bake()
# render defaults (farm)
r = sc.render; r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100; r.fps = 60; r.fps_base = 1.0
sc.frame_start, sc.frame_end = 1, 4410
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
r.use_motion_blur = True; r.motion_blur_shutter = 0.5
c_ = sc.cycles; c_.max_bounces = 12; c_.diffuse_bounces = 4; c_.glossy_bounces = 4; c_.transmission_bounces = 12; c_.transparent_max_bounces = 16   # eyes need the depth
c_.caustics_reflective = False; c_.caustics_refractive = False; r.use_persistent_data = True
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'; r.image_settings.color_depth = '8'; r.image_settings.compression = 15
sc.frame_set(1)
camd.dof.use_dof = False
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
