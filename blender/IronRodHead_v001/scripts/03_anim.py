"""B12 IronRodHead: animation, props, diagram, cameras and look. Every action is keyed at an offset from its shot's start
(timing.py), at 1x speed; one camera per shot, bound by timeline markers (hard cuts).
blender -b sets.blend --python 03_anim.py -- <out.blend>"""
import sys, os, math, random, json
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "00_lib.py")).read())
exec(open(os.path.join(HERE, "timing.py")).read())
_H = open(os.path.join(HERE, "_helpers.py")).read().replace('exec(open(os.path.join(HERE, "timing.py")).read())', "")
exec(_H)
sc.frame_start = 1; sc.frame_end = END_FRAME
rnd = random.Random(12)

def ground_w(x, y):       # ballast bed under the track is 16 cm high (|x| < 1.55, sloping to 2.1)
    ax = abs(x)
    return 0.16 if ax < 1.55 else (0.16 * (2.1 - ax) / 0.55 if ax < 2.1 else 0.0)

SHOTS = [s for s, _ in SHOT_LEN]
def F(shot, off=0):        # absolute frame for an offset in a shot (negative = from its end)
    return ST[shot] + off if off >= 0 else SE(shot) + 1 + off

# =========================================================================== characters
G = Char("Gage", 1.03)
WB = Char("WorkerB", 1.2)
WC = Char("WorkerC", 0.98)
EA = Char("ExtraA", 0.98)
EB = Char("ExtraB", 0.97)
ALL = [G, WB, WC, EA, EB]
for c in ALL:
    for s in "LR": apply_pose(c.o, s, "relaxed", 1)
PARK = {c.o.name: V(300 + 4 * i, 0, 0) for i, c in enumerate(ALL)}
def park(c, f):
    p = PARK[c.o.name]; c.stand(f, p, 0); c.hang(f, p, 0)
USED = {c.o.name: set() for c in ALL}       # shots where each character acts
def uses(c, *shots):
    USED[c.o.name].update(shots)

def hands_fp(c, f, pos_w, yaw, sd, W_rel, d_rel, n_rel, pole_rel):
    """hand target given in the character's yaw frame relative to pos_w (x = character's left, y = back, z = up)"""
    Rz = Matrix.Rotation(R_(yaw), 3, 'Z'); P0 = V(pos_w[0], pos_w[1], ground_w(pos_w[0], pos_w[1]))
    c.hand_w(sd, f, P0 + Rz @ V(*W_rel), Rz @ V(*d_rel).normalized(), Rz @ V(*n_rel).normalized(), P0 + Rz @ V(*pole_rel))

# --------------------------------------------------------------------------- props
CP = coll("Props")
IRON = flat("Iron", (0.10, 0.11, 0.13), rough=0.38, metal=0.85)
def rod_mesh(name, L, r, tip, scale=1.0):
    """tamping iron: blunt round end at z=0, straight bar, last `tip` m tapered to a point (local +Z)"""
    bm = bmesh.new(); seg = 20; rings = [(0.0, r * 0.92), (0.004 * scale, r), (L - tip, r), (L - 0.02 * scale, r * 0.15), (L, 0.0015 * scale)]
    prev = None; vs0 = None
    for z, rr in rings:
        ring = [bm.verts.new((rr * math.cos(2 * math.pi * k / seg), rr * math.sin(2 * math.pi * k / seg), z)) for k in range(seg)]
        if prev:
            for k in range(seg): bm.faces.new((prev[k], prev[(k + 1) % seg], ring[(k + 1) % seg], ring[k]))
        else: vs0 = ring
        prev = ring
    bm.faces.new(list(reversed(vs0))); bm.faces.new(prev)
    o = mesh_obj(name, bm, [IRON], CP); shade_smooth(o)
    return o
ROD_L = 1.1
rod = rod_mesh("TampingIron", ROD_L, 0.016, 0.30)
HOLE = V(*sc["HOLE"])

# =========================================================================== TAMPING (S01-S03): Gage at the drill hole
GP = HOLE + V(0.33, 0.0, 0); GYAW = yaw_to(V(-1, 0, 0))           # stands behind the hole, faces the track (-x)
RzG = Matrix.Rotation(R_(GYAW), 3, 'Z')
ROD_Z0 = -0.06                                                   # blunt end 6 cm down the hole
def rod_M(z_off=0.0, tilt=0.0):
    return Matrix.Translation(HOLE + V(0, 0, ROD_Z0 + z_off)) @ Matrix.Rotation(R_(tilt), 4, 'Y')
def tamp(f):               # lift 11 cm and drop, 46-frame cycle (a firm tamp, then a pause)
    u = ((f - ST["S01"]) % 46) / 46.0
    return 0.11 * (smooth(u / 0.55) if u < 0.55 else 1 - smooth((u - 0.55) / 0.2) if u < 0.75 else 0.0)
TAMP0, TAMP1 = ST["S01"], ST["S03"] + 40
BLAST = ST["S03"] + 46                                           # spark/flash frame (rod leaves the hole)
FGRIP = ST["S01"] + 2
rod.matrix_world = rod_M(); bpy.context.view_layer.update()
uses(G, "S01", "S02", "S03")
for f in range(TAMP0, TAMP1 + 1, 4):
    G.stand(f, (GP.x, GP.y), GYAW, crouch=0.03, flex=9, head=(14, 0))
G.stand(SE("S03"), (GP.x, GP.y), GYAW, crouch=0.03, flex=9, head=(14, 0))
# grips: right hand high, left hand lower; both wrap the bar from Gage's side (+x)
apply_pose(G.o, "R", "relaxed", FGRIP); apply_pose(G.o, "L", "relaxed", FGRIP)
for sd, zc, pole in (("R", 0.90, V(0.25, 0.65, 1.05)),):          # one-hand grip (the left hand hangs relaxed: §2.15 simplest staging)
    sy = 1 if sd == "R" else -1              # his right is +y: each hand closes on the bar from its own side, fingers forward
    c_pt = HOLE + V(0, sy * 0.016, zc)
    rep = grip_object(G.o, sd, FGRIP, rod, c_pt, V(0, -sy, 0), finger_dir=V(-1, 0, 0), finger_radius=0.017)
    print("ROD GRIP", sd, rep)
    curl_free(G.o, sd, rep, FGRIP)
    key_pole(G, sd, FGRIP, GP + pole)
sc.frame_set(FGRIP)
H0 = {sd: G.o.pose.bones["IK_hand." + sd].matrix.copy() for sd in "R"}
FINGQ = {pb.name: pb.rotation_quaternion.copy() for pb in G.o.pose.bones if pb.name.startswith("finger") and pb.name.endswith(".R")}
M0 = rod_M()
def key_rod_hands(f, Mrod):
    for sd, pole in (("R", V(0.25, 0.65, 1.05)),):
        A = G.o.matrix_world.inverted() @ Mrod @ M0.inverted() @ G.o.matrix_world @ H0[sd]
        G.R.key_world("IK_hand." + sd, f, A); key_pole(G, sd, f, GP + pole)
for f in list(range(TAMP0, BLAST + 1, 2)):
    zf = tamp(f) if f < TAMP1 else 0.0
    rod.matrix_world = rod_M(zf); rod.keyframe_insert("location", frame=f); rod.keyframe_insert("rotation_euler", frame=f)
    key_rod_hands(f, rod_M(zf))
    if f % 4 == 0:
        hands_fp(G, f, GP, GYAW, "L", (0.27, 0.0, 0.42), (0, -0.15, -1), (-1, 0, 0), (0.55, 0.45, 0.95))
        G.stand(f, (GP.x, GP.y), GYAW, crouch=0.03 + 0.03 * zf / 0.11, flex=9 + 4 * zf / 0.11, head=(14, 0))
for n, q in FINGQ.items():
    pb = G.o.pose.bones[n]
    for f in (TAMP0, BLAST):
        pb.rotation_quaternion = q; pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
# blast: the bar shoots straight up out of the hole and out of frame (hands stay where they were: framed out in S03)
for f, dz in ((BLAST, 0.0), (BLAST + 3, 0.9), (BLAST + 8, 4.0), (BLAST + 14, 9.0), (SE("S03"), 12.0)):
    rod.matrix_world = rod_M(dz); rod.keyframe_insert("location", frame=f); rod.keyframe_insert("rotation_euler", frame=f)
key_rod_hands(SE("S03"), rod_M(0))
# blast flash + dust (keyed scale, no Scene Time)
def ico(name, r, mat, sub=2):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r); o = mesh_obj(name, bm, [mat], CP); shade_smooth(o); return o
bm = bmesh.new(); pts = []
for i in range(20):
    a = i * math.pi / 10; r = 0.32 if i % 2 == 0 else 0.11
    pts.append(bm.verts.new((r * math.cos(a), r * math.sin(a), 0)))
bm.faces.new(pts)
flash = mesh_obj("BlastFlash", bm, [flat("FlashMat", (1, 0.85, 0.4), emit=(1, 0.75, 0.3), emit_str=30.0)], CP); flash.visible_shadow = False
flash.location = HOLE + V(0, 0, 0.03)
for f, s_ in ((1, 0.01), (BLAST, 0.01), (BLAST + 1, 1.3), (BLAST + 5, 0.8), (BLAST + 10, 0.01)):
    flash.scale = (s_,) * 3; flash.keyframe_insert("scale", frame=f)
key_vis(flash, 1, False); key_vis(flash, BLAST + 1, True); key_vis(flash, BLAST + 11, False)
dust_m = bpy.data.materials.new("DustVol"); _n, _l = nodes_of(dust_m); _n.clear()
_vo = _n.new('ShaderNodeOutputMaterial'); _pv = _n.new('ShaderNodeVolumePrincipled'); _pv.inputs['Density'].default_value = 3.0
_pv.inputs['Color'].default_value = (0.75, 0.68, 0.58, 1); _l.new(_pv.outputs[0], _vo.inputs['Volume'])
def dust_puff(prefix, at, f0, n=4, size=0.35, rise=0.6, until=None):
    out = []
    for k in range(n):
        o = ico("%s%d" % (prefix, k), 0.1, dust_m, 2); r_ = random.Random(k + len(prefix))
        p0 = at + V(r_.uniform(-0.08, 0.08), r_.uniform(-0.08, 0.08), 0.05)
        p1 = p0 + V(r_.uniform(-0.5, 0.5), r_.uniform(-0.5, 0.5), rise * r_.uniform(0.6, 1.2))
        for f, s_, p in ((f0, 0.3, p0), (f0 + 12, size * 2.0, p0.lerp(p1, 0.6)), (f0 + 60, size * 3.2, p1)):
            o.location = p; o.scale = (s_,) * 3; o.keyframe_insert("location", frame=f); o.keyframe_insert("scale", frame=f)
        key_vis(o, 1, False); key_vis(o, f0, True); key_vis(o, until or (f0 + 90), False)
        out.append(o)
    return out
dust_puff("BlastDust", HOLE, BLAST + 1, n=5, size=0.3, rise=0.9, until=SE("S04"))
PEB = flat("Pebble", (0.35, 0.32, 0.3), rough=0.8)
for k in range(8):       # grit kicked out of the hole
    o = ico("Grit%d" % k, 0.018, PEB, 1); r_ = random.Random(40 + k)
    v = V(r_.uniform(-1, 1), r_.uniform(-1, 1), 0).normalized() * r_.uniform(0.8, 1.6) + V(0, 0, r_.uniform(2.5, 4.0))
    for f in range(BLAST, BLAST + 31, 3):
        t = (f - BLAST) / 60.0; p = HOLE + V(0, 0, 0.02) + v * t + V(0, 0, -4.9 * t * t)
        p.z = max(p.z, 0.015); o.location = p; o.keyframe_insert("location", frame=f)
    key_vis(o, 1, False); key_vis(o, BLAST + 1, True); key_vis(o, SE("S03") + 1, False)

# =========================================================================== S04: thrown back, drops to sitting
uses(G, "S04", "S05", "S09", "S10")
SIT = GP + V(0.75, 0.0, 0)                 # pelvis lands ~0.75 m behind where he stood
def sit_pose(f, lean=0.0, head=(0, 0), hands="behind", twist=0.0, breath=0.0):
    root = SIT + V(0, 0, 0.17 * G.s + 0.01 * breath)
    G.H.key_root(f, G.a(root), yaw=GYAW, flex=-8 - 10 * lean)
    G.H.key_spine(f, flex=10 - 8 * lean + 2 * breath, twist=twist, head=head)
    for sd, sx in (("L", -1), ("R", 1)):      # Gage faces -x: his left is -y
        foot = SIT + RzG @ V(-sx * 0.16, -0.62, 0)
        G.use(); G.H.key_foot(sd, f, G.a(V(foot.x, foot.y, 0)).to_2d(), GYAW)
        key_knee(G, sd, f, SIT + RzG @ V(-sx * 0.25, -1.2, 0.9))
    for sd, sx in (("L", -1), ("R", 1)):
        if hands == "behind" or (hands == "knee" and sd == "R"):
            W = SIT + RzG @ V(-sx * 0.27, 0.24, 0.035)
            G.hand_w(sd, f, W, RzG @ V(-sx * 0.25, 1, -0.15).normalized(), V(0, 0, -1), SIT + RzG @ V(-sx * 0.7, 0.3, 0.45))
        else:                                    # forearm resting on the raised knee
            W = SIT + RzG @ V(-sx * 0.17, -0.48, 0.47)
            G.hand_w(sd, f, W, RzG @ V(0, -1, -0.5).normalized(), RzG @ V(sx * 0.3, 0, -1).normalized(), SIT + RzG @ V(-sx * 0.6, 0.0, 0.5))
def key_knee(c, sd, f, W):
    n = "Pole_knee." + sd; pb = c.o.pose.bones[n]
    pb.location = c.R.rest(n).to_3x3().inverted() @ (c.a(W) - c.R.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)
S4 = ST["S04"]
# 0-8 jolt back (head snaps back, hands fly open to the sides below the shoulders), 8-44 two stagger steps, 44-74 drop to sitting
apply_pose(G.o, "L", "open_alarm", S4 + 4); apply_pose(G.o, "R", "open_alarm", S4 + 4)
for f in range(S4, S4 + 75, 2):
    u_j = smooth((f - S4) / 8.0); u_s = smooth((f - S4 - 8) / 36.0); u_d = smooth((f - S4 - 44) / 30.0)
    back = 0.10 * u_j + 0.45 * u_s + 0.20 * u_d
    pos = GP + RzG @ V(0, back, 0)
    hip = G.H.root_head.z * G.s - 0.04 - 0.05 * u_j
    hip = hip * (1 - u_d) + (0.17 * G.s) * u_d
    G.H.key_root(f, G.a(V(pos.x, pos.y, hip)), yaw=GYAW, flex=16 - 22 * u_j + 4 * u_s - 6 * u_d)
    G.H.key_spine(f, flex=12 - 24 * u_j + 14 * u_s + 4 * u_d, head=(14 - 34 * u_j + 18 * u_s, 6 * u_s))
    for sd, sx, ph in (("L", -1, 0.0), ("R", 1, 0.5)):
        # feet: stand, then step back alternately, then slide forward under the knees as he sits
        st_ = GP + RzG @ V(-sx * 0.12, 0.0, 0)
        step = smooth(min(1, max(0, (u_s - ph * 0.5) * 2))) * 0.45
        lift = 0.10 * math.sin(math.pi * min(1, max(0, (u_s - ph * 0.5) * 2)))
        p_stand = st_ + RzG @ V(0, step, 0)
        p_sit = SIT + RzG @ V(-sx * 0.16, -0.62, 0)
        p = p_stand.lerp(p_sit, u_d)
        G.use(); G.H.key_foot(sd, f, G.a(V(p.x, p.y, 0)).to_2d(), GYAW, lift=lift / G.s)
        key_knee(G, sd, f, (pos + RzG @ V(-sx * 0.2, -0.8, 0.6)).lerp(SIT + RzG @ V(-sx * 0.25, -1.2, 0.9), u_d))
        # hands: from the grip, out to the sides at chest height, then down behind to the ground
        sh = V(-sx * 0.30, 0.0, 1.35)
        Wopen = pos + RzG @ V(-sx * 0.55, 0.05, 1.05)
        Wsit = SIT + RzG @ V(-sx * 0.27, 0.24, 0.035)
        if f < S4 + 44:
            W = Wopen; d = RzG @ V(-sx * 0.6, -0.4, -0.5); n = RzG @ V(0, -1, 0)
        else:
            W = Wopen.lerp(Wsit, u_d); d = (RzG @ V(-sx * 0.6, -0.4, -0.5)).lerp(RzG @ V(-sx * 0.25, 1, -0.15), u_d); n = (RzG @ V(0, -1, 0)).lerp(V(0, 0, -1), u_d)
        G.hand_w(sd, f, W, d, n, pos + RzG @ V(-sx * 0.8, 0.4, 0.9))
apply_pose(G.o, "L", "relaxed", S4 + 46); apply_pose(G.o, "R", "relaxed", S4 + 46)
apply_pose(G.o, "L", "flat_palm", S4 + 74, amount=0.8); apply_pose(G.o, "R", "flat_palm", S4 + 74, amount=0.8)
for f in range(S4 + 76, SE("S05") + 1, 6):    # sitting, dazed: slow head roll, breathing
    t = (f - S4) / 60.0
    sit_pose(f, lean=0.6, head=(8 * math.sin(t * 1.3), 10 * math.sin(t * 0.8)), breath=math.sin(t * 3.0))
sit_pose(SE("S05"), lean=0.6, head=(0, 0))
key_rod_hands(S4, rod_M(0))    # (IK hand keys from the grip are overwritten by hand_w above; keep the rod hidden)
key_vis(rod, 1, True); key_vis(rod, ST["S04"], False)

# =========================================================================== S05: the bar falls and sticks in the dirt; co-workers run in
LAND = V(2.45, -8.0, 0.0); S5 = ST["S05"]; TLAND = S5 + 40
uses(WB, "S05", "S09", "S12", "S21"); uses(WC, "S05", "S12", "S21")
tilt_end = Matrix.Rotation(R_(24), 4, 'X') @ Matrix.Rotation(R_(-10), 4, 'Y')
for f in list(range(S5, TLAND + 1, 2)):
    u = (f - S5) / (TLAND - S5)
    tip = LAND + V(1.6 * (1 - u), -0.8 * (1 - u), 9.0 * (1 - u) ** 1.6 - 0.28)   # pointed end first? no: blunt end lands
    R4 = Matrix.Rotation(R_(200 * (1 - u)), 4, 'X') @ tilt_end
    rod.matrix_world = Matrix.Translation(tip) @ R4
    rod.keyframe_insert("location", frame=f); rod.keyframe_insert("rotation_euler", frame=f)
rod.matrix_world = Matrix.Translation(LAND + V(0, 0, -0.28)) @ tilt_end
for f in (TLAND + 1, TLAND + 3, TLAND + 6, SE("S05")):          # a small quiver after it sticks
    q = {TLAND + 1: 4, TLAND + 3: -2.5, TLAND + 6: 1}.get(f, 0)
    rod.matrix_world = Matrix.Translation(LAND + V(0, 0, -0.28)) @ Matrix.Rotation(R_(q), 4, 'X') @ tilt_end
    rod.keyframe_insert("location", frame=f); rod.keyframe_insert("rotation_euler", frame=f)
key_vis(rod, ST["S05"], True); key_vis(rod, ST["S06"], False)
dust_puff("LandDust", LAND, TLAND + 1, n=4, size=0.25, rise=0.5, until=SE("S05") + 1)
# co-workers run from the far side of the cutting toward Gage (cross the frame, faces in profile / 3-4)
def run(c, p0, p1, f0, f1, speed_strides=1.15):
    path = lambda f: p0.lerp(p1, min(1, max(0, (f - f0) / (f1 - f0))))
    yaw = yaw_to(p1 - p0)
    c.use(); c.H.walk(lambda f: c.a(path(f)), lambda f: yaw, f0, f1, stride=speed_strides / c.s, duty=0.45, lift=0.13 / c.s, bob=0.035, lean=12)
    for f in range(f0, f1 + 1, 2):
        cyc = math.sin((path(f) - p0).length / speed_strides * math.pi)
        p = path(f); Rz = Matrix.Rotation(R_(yaw), 3, 'Z')
        for sd, sx in (("L", 1), ("R", -1)):
            k = cyc * (1 if sd == "L" else -1)
            sh = c.o.data.bones["upperarm01." + sd].head_local * c.s
            W = V(p.x, p.y, ground_w(p.x, p.y)) + Rz @ V(sx * (abs(sh.x) + 0.06), -0.10 - 0.22 * k, sh.z - 0.42 * c.s + 0.10 * abs(k))
            c.hand_w(sd, f, W, Rz @ V(0, -0.7 - 0.3 * k, -0.6).normalized(), Rz @ V(-sx, 0, 0), V(p.x, p.y, 0) + Rz @ V(sx * 0.5, 0.6, sh.z - 0.3))
    return path
run(WB, V(-4.6, -5.0, 0), V(2.6, -1.3, 0), S5 + 30, SE("S05"))
run(WC, V(-5.0, -2.6, 0), V(2.2, 0.9, 0), S5 + 44, SE("S05"))
for c in (WB, WC):
    p = {WB: V(-4.6, -5.0, 0), WC: V(-5.0, -2.6, 0)}[c]
    c.stand(S5, p, yaw_to(V(1, 0.3, 0))); c.hang(S5, p, yaw_to(V(1, 0.3, 0)))
    c.stand(S5 + 26, p, yaw_to(V(1, 0.3, 0)), head=(0, 20)); c.hang(S5 + 26, p, yaw_to(V(1, 0.3, 0)))

# =========================================================================== S09: conscious, sitting up; co-workers at his side
S9 = ST["S09"]
for f in range(S9, SE("S09") + 1, 6):
    t = (f - S9) / 60.0; look = smooth((f - S9 - 60) / 40.0) - smooth((f - S9 - 150) / 40.0)
    sit_pose(f, lean=0.2, head=(4 - 6 * look, -25 * look + 4 * math.sin(t)), hands="knee", breath=math.sin(t * 2.4))
apply_pose(G.o, "L", "relaxed", S9); apply_pose(G.o, "R", "flat_palm", S9, amount=0.8)
# WorkerB squats at his left front (between Gage and camera-left), hands on his own knees; WorkerC stands behind, bent
WBp = SIT + RzG @ V(0.75, -0.75, 0); WBy = yaw_to((SIT - WBp))
WCp = SIT + RzG @ V(-0.85, -0.2, 0); WCy = yaw_to((SIT - WCp))
for f in range(S9, SE("S09") + 1, 6):
    t = (f - S9) / 60.0
    Rz = Matrix.Rotation(R_(WBy), 3, 'Z')
    root = WBp + V(0, 0, WB.H.root_head.z * WB.s - 0.42 + 0.01 * math.sin(t * 2))
    WB.H.key_root(f, WB.a(root), yaw=WBy, flex=24)
    WB.H.key_spine(f, flex=16, head=(10, 6 * math.sin(t)))
    for sd, sx in (("L", 1), ("R", -1)):
        ft = WBp + Rz @ V(sx * 0.17, -0.12, 0); WB.use(); WB.H.key_foot(sd, f, WB.a(V(ft.x, ft.y, 0)).to_2d(), WBy)
        key_knee(WB, sd, f, WBp + Rz @ V(sx * 0.3, -1.0, 0.7))
        W = WBp + Rz @ V(sx * 0.19, -0.40, 0.53)
        WB.hand_w(sd, f, W, Rz @ V(0, -1, -0.6).normalized(), V(0, 0, -1), WBp + Rz @ V(sx * 0.6, 0.0, 0.9))

# =========================================================================== head bandage (from S11 on), fitted to Gage's head
def make_bandage(f_fit):
    sc.frame_set(f_fit)
    body = bpy.data.objects["Gage.body"]; dg = bpy.context.evaluated_depsgraph_get(); e = body.evaluated_get(dg)
    Hm = G.o.matrix_world @ G.o.pose.bones["head"].matrix
    Hi = Hm.inverted()
    vs = [Hi @ (body.matrix_world @ v.co) for v in e.data.vertices]
    # head-bone space: y runs up the head; find the crown height
    top = max(v.y for v in vs)
    bm = bmesh.new(); rows = []
    for j, hy in enumerate((top - 0.092, top - 0.072, top - 0.052)):   # forehead band, ~6 cm tall
        sl = [v for v in vs if abs(v.y - hy) < 0.012]
        ring = []
        for k in range(36):
            a = 2 * math.pi * k / 36; d = V(math.cos(a), 0, math.sin(a))
            best = max((v.x * d.x + v.z * d.z for v in sl if (V(v.x, 0, v.z).normalized().dot(d) > 0.96)), default=0.08)
            r = best + 0.006 + 0.002 * j
            ring.append(bm.verts.new((d.x * r, hy, d.z * r)))
        rows.append(ring)
    for a_, b_ in zip(rows, rows[1:]):
        for k in range(36): bm.faces.new((a_[k], a_[(k + 1) % 36], b_[(k + 1) % 36], b_[k]))
    # gauze pad on the crown (exit wound, left-front of the top), a small domed square
    pad = [v for v in vs if v.y > top - 0.03]
    o = mesh_obj("Gage_Bandage", bm, [flat("Gauze", (0.92, 0.9, 0.86), rough=0.85)], CP); shade_smooth(o)
    m = o.modifiers.new("Solid", 'SOLIDIFY'); m.thickness = 0.004
    o.matrix_world = Hm
    bm2 = bmesh.new(); bmesh.ops.create_uvsphere(bm2, u_segments=16, v_segments=8, radius=0.032)
    for v in bm2.verts: v.co.y *= 0.2
    p2 = mesh_obj("Gage_Pad", bm2, [bpy.data.materials["Gauze"]], CP); shade_smooth(p2)
    crown = max(vs, key=lambda v: v.y - 0.3 * abs(v.x))
    p2.matrix_world = Hm @ Matrix.Translation(V(crown.x + 0.012, crown.y - 0.008, crown.z + 0.015))
    for ob in (o, p2):
        child_of_now(ob, G.o, "head", f_fit)
    return o, p2

# =========================================================================== S11: weeks later, walking beside the track, bandaged
S11 = ST["S11"]; uses(G, "S11")
P11a, P11b = V(2.7, 8.5, 0), V(2.7, 2.6, 0)
p11 = lambda f: P11a.lerp(P11b, min(1, max(0, (f - S11 - 6) / (SE("S11") - S11 - 6))))
G.stand(S11, P11a, 0.0); G.hang(S11, P11a, 0.0)
G.use(); G.H.walk(lambda f: G.a(p11(f)), lambda f: 0.0, S11 + 6, SE("S11"), stride=0.72 / G.s, lift=0.08 / G.s, lean=5)
for f in range(S11 + 6, SE("S11") + 1, 3):
    k = math.sin((p11(f) - P11a).length / 0.72 * math.pi)
    G.hang(f, p11(f), 0.0, swing=(0.13 * k, -0.13 * k))
for f in range(S11, SE("S11") + 1, 12):
    G.H.key_spine(f, flex=5, twist=0, head=(-2, 8 * math.sin((f - S11) / 50.0)))

# =========================================================================== S12: co-workers by the supply crates: "he's not the same"
S12 = ST["S12"]
SUP = V(3.75, 2.6, 0)
B12p, C12p = SUP + V(-1.0, 0.95, 0), SUP + V(-1.0, -0.95, 0)
for f in range(S12, SE("S12") + 1, 6):
    t = (f - S12) / 60.0
    lk = smooth((f - S12 - 40) / 25.0); sh = math.sin(math.pi * min(1, max(0, (f - S12 - 70) / 45.0)))
    yb = yaw_to(V(-1, -0.25, 0)) * (1 - lk) + yaw_to(C12p - B12p) * lk * 0.55 + yaw_to(V(-1, -0.25, 0)) * lk * 0.45
    yc = yaw_to(V(-1, 0.25, 0)) * (1 - lk) + yaw_to(B12p - C12p) * lk * 0.55 + yaw_to(V(-1, 0.25, 0)) * lk * 0.45
    WB.stand(f, B12p, yb, head=(4, 0))
    WC.stand(f, C12p, yc, head=(2, 22 * math.sin(t * 5.0) * sh))          # WorkerC shakes his head
    # WorkerB: a small shrug, both palms up at waist height
    Rz = Matrix.Rotation(R_(yb), 3, 'Z')
    for sd, sx in (("L", 1), ("R", -1)):
        shz = WB.o.data.bones["upperarm01." + sd].head_local.z * WB.s
        Wh = B12p + Rz @ V(sx * 0.25, -0.06, shz - 0.56)
        Wu = B12p + Rz @ V(sx * 0.36, -0.30, shz - 0.40)
        W = Wh.lerp(Wu, sh)
        d = (Rz @ V(0, -0.15, -1)).normalized().lerp((Rz @ V(sx * 0.3, -1, 0.1)).normalized(), sh)
        n = (Rz @ V(-sx, 0, 0)).lerp(V(0, 0, 1), sh)
        WB.hand_w(sd, f, W, d, n, B12p + Rz @ V(sx * 0.55, 0.4, shz - 0.3))
    WC.hang(f, C12p, yc)
for sd in "LR":
    apply_pose(WB.o, sd, "relaxed", S12); apply_pose(WB.o, sd, "open_alarm", S12 + 90); apply_pose(WB.o, sd, "relaxed", SE("S12"))

# =========================================================================== S18-S19: glare, then kicks the crate stack over
KP = V(-3.0, -8.0, 0)
P18 = V(-1.9, -8.0, 0); S18 = ST["S18"]; uses(G, "S18", "S19", "S20", "S21", "S22")
for f in range(S18, SE("S18") + 1, 4):
    u = smooth((f - S18 - 30) / 22.0)
    G.stand(f, P18, 0.0, flex=6 + 4 * u, head=(-6 + 12 * u, -20 * u))
    G.hang(f, P18, 0.0, swing=(0.0, 0.0))
apply_pose(G.o, "L", "power_fist", S18 + 40, amount=0.6); apply_pose(G.o, "R", "power_fist", S18 + 40, amount=0.6)
S19 = ST["S19"]; KYAW = yaw_to(V(-1, 0, 0)); RzK = Matrix.Rotation(R_(KYAW), 3, 'Z')
P19 = V(-1.98, -8.05, 0); KICK_F = S19 + 62
for f in range(S19, SE("S19") + 1, 2):
    wind = smooth((f - S19 - 30) / 22.0) * (1 - smooth((f - KICK_F) / 6.0))
    strike = smooth((f - KICK_F + 8) / 8.0) * (1 - smooth((f - KICK_F - 6) / 20.0))
    pos = P19 + RzK @ V(0, 0.04 * wind, 0)
    hip = G.H.root_head.z * G.s - 0.05
    G.H.key_root(f, G.a(V(pos.x, pos.y, hip)), yaw=KYAW, flex=4 - 10 * strike + 6 * wind)
    G.H.key_spine(f, flex=6 + 8 * wind - 6 * strike, head=(10, 0), twist=-6 * strike)
    # left foot planted; right foot winds back then swings into the bottom crate's face
    pl = P19 + RzK @ V(0.13, -0.05, 0); G.use(); G.H.key_foot("L", f, G.a(pl).to_2d(), KYAW)
    rf0 = P19 + RzK @ V(-0.13, 0.0, 0)
    rfb = P19 + RzK @ V(-0.13, 0.42, 0)
    rfk = V(-2.50, -8.06, 0)
    p = rf0.lerp(rfb, wind)
    if f >= KICK_F - 8: p = p.lerp(rfk, strike)
    lift = 0.12 * wind + 0.20 * strike
    G.use(); G.H.key_foot("R", f, G.a(V(p.x, p.y, 0)).to_2d(), KYAW, lift=lift / G.s, pitch=-35 * wind + 20 * strike)
    key_knee(G, "R", f, pos + RzK @ V(-0.2, -0.9, 0.6))
    for sd, sx in (("L", 1), ("R", -1)):     # arms counter-swing for balance (below the shoulders)
        shz = G.o.data.bones["upperarm01." + sd].head_local.z * G.s
        k = (strike - wind * 0.5) * (1 if sd == "L" else -1)
        W = pos + RzK @ V(sx * 0.36, -0.12 - 0.22 * k, shz - 0.52 + 0.12 * abs(k))
        G.hand_w(sd, f, W, RzK @ V(sx * 0.2, -0.6 - 0.3 * k, -0.7).normalized(), RzK @ V(-sx, 0, 0), pos + RzK @ V(sx * 0.6, 0.5, shz - 0.3))
# crates: bottom slides back, middle and top topple off the far side and land on the ground (keyed, gravity-eased)
KO = [bpy.data.objects[n] for n in sc["KICK"]]
for o in KO:
    o.rotation_mode = 'XYZ'; o.keyframe_insert("location", frame=1); o.keyframe_insert("rotation_euler", frame=1)
    o.keyframe_insert("location", frame=KICK_F); o.keyframe_insert("rotation_euler", frame=KICK_F)
b0 = KO[0]; L0 = b0.location.copy()
for f, dx, ry in ((KICK_F + 4, -0.10, 0), (KICK_F + 12, -0.26, 0), (KICK_F + 20, -0.30, 0)):
    b0.location = L0 + V(dx, 0, 0); b0.keyframe_insert("location", frame=f)
for i, o in enumerate(KO[1:], 1):
    L1 = o.location.copy(); h = {1: 0.55, 2: 0.5}[i]; w = {1: 0.7, 2: 0.62}[i]
    d0 = KICK_F + 3 + 4 * i
    piv = V(L1.x - w / 2 - 0.02, L1.y, L1.z)        # far bottom edge
    for k in range(0, 31, 3):
        u = k / 30.0; ang = (90 if i == 1 else 100) * (u ** 1.8)
        fall = max(0.0, (u - 0.25) / 0.75)
        R = Matrix.Rotation(R_(-ang), 3, 'Y')
        cen = piv + R @ (V(L1.x, L1.y, L1.z + h / 2) - piv)
        cen.z -= (L1.z) * (fall ** 2)
        cen.x -= 0.45 * fall * (i - 1)
        cen.z = max(cen.z, w / 2 if ang > 60 else cen.z)
        o.location = cen - R @ V(0, 0, h / 2); o.rotation_euler = (0, R_(-ang), o.rotation_euler.z)
        o.keyframe_insert("location", frame=d0 + k); o.keyframe_insert("rotation_euler", frame=d0 + k)
for o in KO:     # back in place for the earlier shots only matters before KICK_F; hold after
    o.keyframe_insert("location", frame=END_FRAME); o.keyframe_insert("rotation_euler", frame=END_FRAME)
dust_puff("KickDust", KP + V(-0.6, 0, 0), KICK_F + 26, n=3, size=0.25, rise=0.3, until=SE("S19") + 1)

# =========================================================================== S20: storms along the track toward camera
S20 = ST["S20"]; P20a, P20b = V(2.7, -3.2, 0), V(2.7, -8.6, 0)
p20 = lambda f: P20a.lerp(P20b, min(1, max(0, (f - S20) / (SE("S20") - S20))))
G.use(); G.H.walk(lambda f: G.a(p20(f)), lambda f: 0.0, S20, SE("S20"), stride=0.86 / G.s, lift=0.1 / G.s, lean=12, bob=0.03)
for f in range(S20, SE("S20") + 1, 2):
    k = math.sin((p20(f) - P20a).length / 0.86 * math.pi)
    G.hang(f, p20(f), 0.0, swing=(0.2 * k, -0.2 * k))
for f in range(S20, SE("S20") + 1, 10):
    G.H.key_spine(f, flex=12, twist=6 * math.sin(f / 9.0), head=(8, 0))

# =========================================================================== S21: points at WorkerC; WorkerC leans back, palms up
S21 = ST["S21"]; P21 = V(2.4, -11.6, 0); C21 = V(3.45, -11.75, 0)
gy21 = yaw_to(V(1, -0.35, 0)); cy21 = yaw_to(V(-1, -0.25, 0))
R21 = Matrix.Rotation(R_(gy21), 3, 'Z'); RC = Matrix.Rotation(R_(cy21), 3, 'Z')
for f in range(S21, SE("S21") + 1, 3):
    t = (f - S21) / 60.0; u = smooth((f - S21 - 18) / 16.0); jab = 0.04 * math.sin(t * 9.0) * u
    lean = smooth((f - S21 - 22) / 14.0)
    G.stand(f, P21, gy21, flex=10 + 6 * u, head=(6, 0), twist=-6 * u)
    shz = G.o.data.bones["upperarm01.R"].head_local.z * G.s
    Wh = P21 + R21 @ V(-0.26, -0.06, shz - 0.56)
    Wp = P21 + R21 @ V(-0.17, -0.50 - jab, shz - 0.10)
    G.hand_w("R", f, Wh.lerp(Wp, u), (R21 @ V(0, -0.15, -1)).normalized().lerp(R21 @ V(0.1, -1, 0.05), u).normalized(),
             (R21 @ V(1, 0, 0)).lerp(R21 @ V(0, 0, -1), u), P21 + R21 @ V(-0.6, 0.2, shz - 0.4))
    G.hand_w("L", f, P21 + R21 @ V(0.27, -0.04, shz - 0.56), R21 @ V(0, -0.1, -1), R21 @ V(-1, 0, 0), P21 + R21 @ V(0.6, 0.4, shz - 0.3))
    WC.stand(f, C21, cy21, flex=4 - 12 * lean, head=(-6 * lean, 0))
    shc = WC.o.data.bones["upperarm01.L"].head_local.z * WC.s
    for sd, sx in (("L", 1), ("R", -1)):
        Wd = C21 + RC @ V(sx * 0.25, -0.05, shc - 0.56)
        Wu = C21 + RC @ V(sx * 0.30, -0.28 + 0.06 * lean, shc - 0.30)
        WC.hand_w(sd, f, Wd.lerp(Wu, lean), (RC @ V(0, -0.1, -1)).normalized().lerp(RC @ V(sx * 0.15, -0.2, 1).normalized(), lean).normalized(),
                  (RC @ V(-sx, 0, 0)).lerp(RC @ V(0, -1, 0), lean), C21 + RC @ V(sx * 0.6, 0.3, shc - 0.4))
apply_pose(G.o, "R", "relaxed", S21); apply_pose(G.o, "R", "point", S21 + 30)
apply_pose(G.o, "L", "power_fist", S21, amount=0.5)
for sd in "LR": apply_pose(WC.o, sd, "relaxed", S21); apply_pose(WC.o, sd, "open_alarm", S21 + 36)

# =========================================================================== S22: final close-up, the glare, head jerks toward camera
S22 = ST["S22"]; P22 = V(2.4, -11.6, 0); gy22 = yaw_to(V(0.35, -1, 0))
for f in range(S22, SE("S22") + 1, 3):
    t = (f - S22) / 60.0; u = smooth((f - S22 - 30) / 10.0); v2 = smooth((f - S22 - 95) / 12.0)
    G.stand(f, P22, gy22, flex=8 + 8 * u, head=(10 * u - 4 * v2, 28 * (1 - u) - 18 * v2), twist=10 * (1 - u))
    G.hang(f, P22, gy22)
apply_pose(G.o, "L", "power_fist", S22, amount=0.6); apply_pose(G.o, "R", "power_fist", S22, amount=0.6)

# =========================================================================== S01 extras walking in the background; idle co-workers
uses(EA, "S01", "S05"); uses(EB, "S01", "S05")
def walker(c, a, b, f0, f1, stride=0.72):
    pth = lambda f: a.lerp(b, min(1, max(0, (f - f0) / (f1 - f0)))); yw = yaw_to(b - a)
    c.stand(f0, a, yw); c.use(); c.H.walk(lambda f: c.a(pth(f)), lambda f: yw, f0, f1, stride=stride / c.s, lift=0.08 / c.s)
    for f in range(f0, f1 + 1, 3):
        k = math.sin((pth(f) - a).length / stride * math.pi); c.hang(f, pth(f), yw, swing=(0.13 * k, -0.13 * k))
walker(EA, V(-4.2, 9.0, 0), V(-4.2, 2.2, 0), ST["S01"], SE("S01"))
walker(EB, V(-3.0, -14.0, 0), V(-3.4, -7.0, 0), ST["S01"], SE("S01"))
walker(EA, V(-5.2, 6.0, 0), V(-3.0, 1.5, 0), ST["S05"], SE("S05"), stride=0.9)
walker(EB, V(-5.6, -8.0, 0), V(-4.4, -6.5, 0), ST["S05"], ST["S05"] + 60)
EB.stand(SE("S05"), V(-4.4, -6.5, 0), yaw_to(V(1, 0.3, 0)), head=(0, 10)); EB.hang(SE("S05"), V(-4.4, -6.5, 0), yaw_to(V(1, 0.3, 0)))

# park every character outside its shots (keys at both ends of each unused shot)
for c in ALL:
    for s in SHOTS:
        if s not in USED[c.o.name]:
            park(c, ST[s]); park(c, SE(s))

# bandage: fitted on a neutral standing frame (S11 start), visible from S11 on
band, pad = make_bandage(ST["S11"])
for ob in (band, pad):
    key_vis(ob, 1, False); key_vis(ob, ST["S11"], True)

# =========================================================================== DIAGRAM: skull + brain + iron (S06-S08, S10, S13-S17)
CD = bpy.data.collections["Diagram"]
DG = V(*sc["DIAG"]); DS = sc["DSCALE"]
skull = bpy.data.objects["Skull"]; brain = bpy.data.objects["Brain"]
drod = rod_mesh("DiagramIron", ROD_L * DS, 0.016 * DS, 0.30 * DS, scale=DS); CD.objects.link(drod); CP.objects.unlink(drod)
ENTRY = DG + V(0.155, -0.300, -0.085)        # under the left cheekbone (skull faces -y; its left is +x)
EXIT = DG + V(0.035, -0.115, 0.415)          # top of the skull, left of the midline, toward the front
AX = (EXIT - ENTRY).normalized()
RQ = AX.to_track_quat('Z', 'Y')
def drod_at(f, tip_s):      # tip_s: distance of the pointed tip past ENTRY along the axis
    base = ENTRY + AX * (tip_s - ROD_L * DS)
    drod.matrix_world = Matrix.Translation(base) @ RQ.to_matrix().to_4x4()
    drod.keyframe_insert("location", frame=f); drod.keyframe_insert("rotation_euler", frame=f)
SPAN = (EXIT - ENTRY).length
def ramp(shot, a, b, s0, s1, step=3):
    for f in range(F(shot, a), F(shot, b) + 1, step):
        drod_at(f, s0 + (s1 - s0) * smooth((f - F(shot, a)) / max(1, F(shot, b) - F(shot, a))))
ramp("S06", 0, 120, -0.35, SPAN + 0.35); drod_at(SE("S06"), SPAN + 0.35)
ramp("S07", 0, -1, SPAN + 0.40, SPAN + 0.55)
ramp("S08", 0, 90, SPAN - 0.25, SPAN + 0.9); drod_at(SE("S08"), SPAN + 0.9)
ramp("S10", 0, 15, SPAN + 0.9, SPAN + 0.9); ramp("S10", 20, 130, SPAN + 0.9, -0.5); drod_at(SE("S10"), -0.5)
ramp("S13", 0, 110, -0.2, SPAN + 0.6); drod_at(SE("S13"), SPAN + 0.6)
ramp("S14", 0, -1, SPAN + 0.6, SPAN + 0.75)
for o in (drod,):
    for fc in fcurves_of(o.animation_data.action):
        pass
# entry / exit holes in the bone (dark discs, visible once the iron is pulled out)
HOLEM = flat("BoneHole", (0.18, 0.06, 0.05), rough=0.7)
holes = []
for nm, p, nrm in (("HoleEntry", ENTRY, -AX), ("HoleExit", EXIT, AX)):
    bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=24, radius=0.016 * DS * 1.25)
    o = mesh_obj(nm, bm, [HOLEM], CD); o.matrix_world = Matrix.Translation(p + nrm * 0.004) @ nrm.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    holes.append(o)
# bone chips at the exit (S08): small cream fragments thrown up and out
BONE = bpy.data.materials["BoneCream"]
chips = []
for k in range(9):
    r_ = random.Random(100 + k)
    o = ico("Chip%d" % k, 0.02, BONE, 1)
    for v in o.data.vertices: v.co *= r_.uniform(0.6, 1.4)
    o.data.update(); CD.objects.link(o); CP.objects.unlink(o)
    f0 = F("S08", 46); vel = (AX * r_.uniform(0.8, 1.6) + V(r_.uniform(-1, 1), r_.uniform(-1, 1), 0) * 0.9)
    for f in range(f0, SE("S08") + 1, 3):
        t = (f - f0) / 60.0; o.location = EXIT + vel * t + V(0, 0, -2.5 * t * t)
        o.rotation_euler = (t * 7 * r_.random(), t * 5, t * 3); o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
    key_vis(o, 1, False); key_vis(o, f0, True); key_vis(o, SE("S08") + 1, False)
    chips.append(o)
# frontal-lobe highlight on the brain: yellow mask (front third, object space -y) + violet glow; keyed values (no Scene Time)
bm_ = brain.data.materials[0].copy(); brain.data.materials[0] = bm_
nt = bm_.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sep.inputs[0])
mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -0.16; mr.inputs['From Max'].default_value = -0.09
mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 0.0; nt.links.new(sep.outputs['Y'], mr.inputs['Value'])
HI = nt.nodes.new('ShaderNodeValue'); HI.name = "HI"; GL = nt.nodes.new('ShaderNodeValue'); GL.name = "GLOW"; DM = nt.nodes.new('ShaderNodeValue'); DM.name = "DAMAGE"
mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; nt.links.new(mr.outputs[0], mul.inputs[0]); nt.links.new(HI.outputs[0], mul.inputs[1])
src = bsdf.inputs['Base Color'].links[0].from_socket if bsdf.inputs['Base Color'].links else None
mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; nt.links.new(mul.outputs[0], mix.inputs['Factor'])
if src: nt.links.new(src, mix.inputs['A'])
else: mix.inputs['A'].default_value = bsdf.inputs['Base Color'].default_value
mix.inputs['B'].default_value = (1.0, 0.72, 0.04, 1)
for _f, _c in ((1, (1.0, 0.72, 0.04, 1)), (F("S15", 0), (0.55, 0.22, 1.0, 1))):
    mix.inputs['B'].default_value = _c; mix.inputs['B'].keyframe_insert("default_value", frame=_f)
mul2 = nt.nodes.new('ShaderNodeMath'); mul2.operation = 'MULTIPLY'; nt.links.new(mr.outputs[0], mul2.inputs[0]); nt.links.new(DM.outputs[0], mul2.inputs[1])
mixd = nt.nodes.new('ShaderNodeMix'); mixd.data_type = 'RGBA'; nt.links.new(mul2.outputs[0], mixd.inputs['Factor'])
nt.links.new(mix.outputs['Result'], mixd.inputs['A']); mixd.inputs['B'].default_value = (0.42, 0.36, 0.38, 1)
nt.links.new(mixd.outputs['Result'], bsdf.inputs['Base Color'])
mul3 = nt.nodes.new('ShaderNodeMath'); mul3.operation = 'MULTIPLY'; nt.links.new(mr.outputs[0], mul3.inputs[0]); nt.links.new(GL.outputs[0], mul3.inputs[1])
bsdf.inputs['Emission Color'].default_value = (0.45, 0.12, 1.0, 1); nt.links.new(mul3.outputs[0], bsdf.inputs['Emission Strength'])
def kv(node, f, v):
    node.outputs[0].default_value = v; node.outputs[0].keyframe_insert("default_value", frame=f)
for nd in (HI, GL, DM): kv(nd, 1, 0.0)
kv(HI, F("S14", 0), 0.0); kv(HI, F("S14", 50), 1.0); kv(HI, SE("S16"), 1.0); kv(HI, F("S17", 30), 0.35)
kv(GL, F("S15", 0), 0.0)
for k, f in enumerate(range(F("S15", 10), SE("S16"), 22)):       # violet pulses: decision making, self-control
    kv(GL, f, 0.0 if k % 2 else 0.9)
kv(GL, SE("S16"), 0.7); kv(GL, F("S17", 6), 0.0); kv(GL, F("S17", 10), 1.2); kv(GL, F("S17", 16), 0.0); kv(GL, F("S17", 24), 0.6); kv(GL, F("S17", 30), 0.0)
kv(DM, F("S17", 0), 0.0); kv(DM, F("S17", 50), 0.85); kv(DM, END_FRAME, 0.85)
kv(HI, END_FRAME, 0.35); kv(GL, END_FRAME, 0.0)
# visibility per shot
DIAG_SKULL = {"S06", "S07", "S08", "S10"}; DIAG_BRAIN = DIAG_SKULL | {"S13", "S14", "S15", "S16", "S17"}
ROD_SHOTS = {"S06", "S07", "S08", "S10", "S13", "S14"}
def vis_by(o, shots):
    prev = None
    for s in SHOTS:
        v = s in shots
        if v != prev: key_vis(o, ST[s], v); prev = v
    if 1 < ST[SHOTS[0]]: key_vis(o, 1, SHOTS[0] in shots)
vis_by(skull, DIAG_SKULL); vis_by(brain, DIAG_BRAIN); vis_by(drod, ROD_SHOTS)
for h in holes: vis_by(h, {"S10"})
# soft diagram key light (only on in diagram shots; Gage scenes use the sun)
dl = bpy.data.lights.new("DiagramKey", 'AREA'); dl.size = 2.0; dl.color = (1.0, 0.97, 0.93)
dlo = bpy.data.objects.new("DiagramKey", dl); CD.objects.link(dlo); dlo.location = DG + V(-1.6, -2.2, 1.4)
dlo.rotation_euler = (DG - dlo.location).to_track_quat('-Z', 'Y').to_euler()
for s in SHOTS:
    dl.energy = 120.0 if s in DIAG_BRAIN else 0.0; dl.keyframe_insert("energy", frame=ST[s])
for fc in fcurves_of(dl.animation_data.action):
    for k in fc.keyframe_points: k.interpolation = 'CONSTANT'

# =========================================================================== cameras (one per shot, hard cuts)
def headw(c, f): return c.world_bone("head", f).translation + V(0, 0, 0.06)
hG1 = headw(G, F("S01", 60))
camera("S01", [(0, V(-1.6, -1.4, 5.0), V(3.2, 1.0, 0.6)), (-1, V(0.0, 0.4, 1.75), V(3.5, 1.25, 0.95))], lens=28)
camera("S02", [(0, GP + V(-1.15, -0.95, 0.55), GP + V(-0.4, 0, 0.95)), (-1, GP + V(-1.0, -0.82, 0.42), GP + V(-0.4, 0, 0.80))], lens=30)
camera("S03", [(0, HOLE + V(-0.48, -0.30, 0.16), HOLE + V(0, 0, 0.17)), (-1, HOLE + V(-0.44, -0.27, 0.15), HOLE + V(0, 0, 0.17))], lens=35)
camera("S04", [(0, GP + V(-0.6, -3.3, 1.1), GP + V(0.35, 0, 0.8)), (-1, GP + V(-0.3, -2.9, 0.9), SIT + V(0, 0, 0.5))], lens=28)
camera("S05", [(0, V(2.9, -10.6, 0.45), V(2.6, -1.5, 1.5)), (-1, V(2.85, -10.3, 0.5), V(2.6, -1.0, 1.0))], lens=24)
# diagram cameras: skull faces -y; its left side (+x) carries the window and the entry point
def orbit(shot, ang0, ang1, r0, r1, z0, z1, tgt, lens, n=4):
    keys = []
    for i in range(n + 1):
        u = i / n; a = R_(ang0 + (ang1 - ang0) * u); r = r0 + (r1 - r0) * u
        off = int((SE(shot) - ST[shot]) * u) if i < n else -1
        keys.append((off, tgt + V(r * math.sin(a), -r * math.cos(a), z0 + (z1 - z0) * u), tgt))
    return camera(shot, keys, lens=lens)
orbit("S06", 55, 30, 2.6, 2.3, 0.35, 0.25, DG + V(0.05, 0, 0.05), 35)
orbit("S07", 62, 55, 1.55, 1.25, 0.15, 0.12, DG + V(0.13, -0.18, 0.08), 40)
orbit("S08", 20, 45, 1.8, 1.7, 1.5, 1.2, DG + V(0.03, -0.1, 0.35), 35)
orbit("S10", 85, 70, 2.5, 2.4, 0.2, 0.25, DG + V(0.05, 0, 0.0), 35)
sc.frame_set(F("S09", 100)); hS9 = headw(G, F("S09", 100))
camera("S09", [(0, V(1.35, 0.75, 1.1), (SIT + WBp) / 2 + V(0, 0, 0.62)), (-1, V(1.55, 0.6, 1.05), (SIT + WBp) / 2 + V(0, 0, 0.6))], lens=28)
camera("S11", [(0, V(2.5, 5.6, 1.6), V(2.7, 8.5, 1.35)), (117, V(2.5, 2.7, 1.6), V(2.7, 5.6, 1.35)), (-1, V(2.5, 0.0, 1.6), V(2.7, 2.6, 1.35))], lens=32)
camera("S12", [(0, V(-0.6, SUP.y - 0.5, 1.6), SUP + V(-0.8, 0, 1.15)), (-1, V(-0.3, SUP.y + 0.25, 1.6), SUP + V(-0.8, 0, 1.15))], lens=24)
orbit("S13", 50, 25, 2.3, 2.0, 0.3, 0.25, DG + V(0.02, 0.05, 0.12), 35)
orbit("S14", 35, 50, 1.8, 1.45, 0.25, 0.2, DG + V(0.03, -0.05, 0.12), 35)
orbit("S15", -20, 25, 2.1, 2.0, 0.6, 0.5, DG + V(0, 0.05, 0.12), 35)
orbit("S16", 70, 40, 1.9, 1.8, 0.9, 0.6, DG + V(0, 0.0, 0.12), 35)
orbit("S17", 15, 5, 1.9, 1.6, 0.3, 0.25, DG + V(0, 0.0, 0.12), 35)
hS18 = headw(G, F("S18", 50))
camera("S18", [(0, P18 + V(0.15, -1.25, 1.62), hS18 + V(0, 0, -0.08)), (-1, P18 + V(0.05, -1.0, 1.6), hS18 + V(0, 0, -0.06))], lens=40)
camera("S19", [(0, V(-1.6, -11.6, 1.05), V(-2.4, -8.0, 0.75)), (-1, V(-1.9, -11.2, 0.95), V(-2.6, -8.0, 0.65))], lens=28)
camera("S20", [(0, V(2.55, -5.6, 1.6), V(2.7, -3.2, 1.35)), (-1, V(2.55, -11.0, 1.6), V(2.7, -8.6, 1.35))], lens=30)
camera("S21", [(0, V(2.75, -14.2, 1.5), V(2.95, -11.65, 1.35)), (-1, V(2.85, -13.8, 1.5), V(2.95, -11.65, 1.35))], lens=30)
hS22 = headw(G, F("S22", 60))
camera("S22", [(0, hS22 + V(0.42, -1.35, -0.1), hS22 + V(0, 0, -0.22)), (-1, hS22 + V(0.32, -1.0, -0.1), hS22 + V(0, 0, -0.22))], lens=40)
sc.camera = bpy.data.objects["CAM_S01"]
for co in [o for o in CAMS.objects if o.type == 'CAMERA']:
    co.data.dof.use_dof = False

# =========================================================================== hold the last key of every shot until the cut
CUTS = sorted(ST[x] for x in SHOTS)
def crosses(a, b):
    return any(a < c <= b for c in CUTS)
for ob in bpy.data.objects:
    ad = ob.animation_data
    if not ad or not ad.action or ob.name.startswith(("CAM_", "CAMT_")): continue
    for fc in fcurves_of(ad.action):
        kp = fc.keyframe_points
        for i in range(len(kp) - 1):
            if crosses(kp[i].co.x, kp[i + 1].co.x) and kp[i + 1].co.x - kp[i].co.x > 1: kp[i].interpolation = 'CONSTANT'
# =========================================================================== look
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'; sc.view_settings.exposure = 0.0
sc.render.use_motion_blur = False
sc.render.fps = 60; sc.render.resolution_x = 1080; sc.render.resolution_y = 1920
sc["SHOTS_JSON"] = json.dumps([[s, ST[s], SE(s)] for s in SHOTS])
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ANIM_DONE frames", sc.frame_start, sc.frame_end)
