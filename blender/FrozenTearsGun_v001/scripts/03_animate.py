"""All animation: both humans, gun, tube, tears, ice, gas, spring, pellets, bubble, time-lapse, lights, continuous camera.
blender -b work/scene.blend --python scripts/03_animate.py -- work/film.blend"""
import sys, os, math, random, json
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[sys.argv.index("--") + 1]
exec(open(os.path.join(ROOT, "..", "pipeline", "anim_lib.py")).read())
sc = bpy.context.scene
random.seed(13)
FPS = 60
def F(t): return 1 + round(t * FPS)
BEATS = [(1, 0.0, "As she cries"), (2, 2.3, "her tears roll down into a tube"), (3, 4.5, "and drop into the gun"),
         (4, 5.8, "When she turns the valve"), (5, 7.3, "a CO2 canister releases gas"), (6, 10.1, "freezing the tears into tiny balls of ice"),
         (7, 13.4, "And when the trigger is pulled"), (8, 15.0, "a spring fires the frozen tears"), (9, 18.7, "You see, a while back"),
         (10, 22.4, "and burst into tears"), (11, 25.5, "She was so upset"), (12, 28.3, "So she designed this tear gun"),
         (13, 31.2, "And when it was finished")]
json.dump([{"beat": b, "frame": F(t), "first_words": w} for b, t, w in BEATS], open(os.path.join(ROOT, "beats.json"), "w"), indent=1)
BT = top = sc["bench_top"]; DT = sc["desk_top"]
def OF(lx, ly, lz):   # office-local (relative to office centre) -> world
    return Vector((-lx, -6.5 - ly, lz))
T_OFFICE_IN, T_OFFICE_OUT = 1150, 1700          # characters swap sets on these frames (camera is inside a white flash)

def track(keys):
    f = pchip(keys); return f
def keyv(obj, path, f, v, idx=-1):
    setattr(obj, path, v) if idx < 0 else None
    obj.keyframe_insert(path, frame=f)
def set_interp(obj, kind='LINEAR'):
    ad = obj.animation_data
    if not ad or not ad.action: return
    for layer in getattr(ad.action, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points: kp.interpolation = kind
def node_val(mat_name, node_name):
    return bpy.data.materials[mat_name].node_tree.nodes[node_name].outputs[0]
def key_node(sock, f, v):
    sock.default_value = v; sock.keyframe_insert("default_value", frame=f)
def key_hide(o, pairs):
    for f, h in pairs:
        o.hide_render = h; o.keyframe_insert("hide_render", frame=f)
        o.hide_viewport = h; o.keyframe_insert("hide_viewport", frame=f)

# ------------------------------------------------------------------ rigs
WR = make_human_ctrl(bpy.data.objects["Inventor"]); WH = Human(WR)
MR = make_human_ctrl(bpy.data.objects["Mentor"]); MH = Human(MR)
# tube: drop the hooks; the bezier points are keyed from the anchor empties instead
tube = bpy.data.objects["TearTube"]
for m in list(tube.modifiers): tube.modifiers.remove(m)

def hand_basis(s, d, n):
    d = d.normalized(); n = (n - d * n.dot(d)).normalized()
    a = d.cross(n) if s == "R" else n.cross(d)
    return Matrix((d, a, n)).transposed()
class Body:
    def __init__(self, R, H):
        self.R, self.H = R, H
        self.REST_HAND = {}
        for s in "LR":
            wv = R.BN["wrist." + s].head_local
            d = R.BN["finger3-1." + s].head_local - wv
            a = R.BN["finger2-1." + s].head_local - R.BN["finger5-1." + s].head_local
            n = d.cross(a) if s == "L" else a.cross(d)
            self.REST_HAND[s] = hand_basis(s, d, n)
        self.root_head = R.BN["root"].head_local.copy()
    def hand_matrix(self, s, W, d, n):
        Rm = hand_basis(s, d, n) @ self.REST_HAND[s].transposed()
        wr = self.R.BN["wrist." + s].head_local
        return Matrix.Translation(W) @ Rm.to_4x4() @ Matrix.Translation(-wr) @ self.R.rest("IK_hand." + s)
    def key_hand(self, s, f, W, d, n, pole=None):
        self.R.key_world("IK_hand." + s, f, self.hand_matrix(s, W, d, n))
        if pole is not None:
            pb = self.R.PB["Pole_elbow." + s]; nm = "Pole_elbow." + s
            pb.location = self.R.rest(nm).to_3x3().inverted() @ (pole - self.R.BN[nm].head_local)
            pb.keyframe_insert("location", frame=f, group=nm)
    def key_fingers(self, s, f, curl, thumb=18, thumb_in=22):
        Rh = self.REST_HAND[s]; d, a = Rh.col[0].copy(), Rh.col[1].copy(); sign = 1 if s == "R" else -1
        JW = (0.8, 1.1, 0.8)
        for k in range(2, 6):
            c = curl[k - 2] if isinstance(curl, (list, tuple)) else curl
            for j in range(1, 4):
                b = "finger%d-%d.%s" % (k, j, s)
                self.R.key_q(b, f, self.R.local_q(b, Matrix.Rotation(R_(c * JW[j - 1] * sign), 3, a)))
        for j, fl in ((1, thumb * 0.4), (2, thumb * 0.8), (3, thumb)):
            b = "finger1-%d.%s" % (j, s)
            self.R.key_q(b, f, self.R.local_q(b, Matrix.Rotation(R_(fl * sign), 3, a) @ Matrix.Rotation(R_(thumb_in * sign), 3, d)))
    def key_body(self, f, pos, yaw, flex=0.0, side=0.0, twist=0.0, head=(0, 0, 0), pitch=0.0, clav=0.0, jaw=0.0):
        H = self.H; R = self.R
        Rw = Matrix.Rotation(R_(yaw), 3, 'Z') @ Matrix.Rotation(R_(pitch), 3, 'X') @ Matrix.Rotation(R_(side * 0.3), 3, 'Y')
        M = Matrix.Translation(pos) @ Rw.to_4x4() @ Matrix.Translation(-self.root_head) @ R.rest("root")
        R.key_world("root", f, M)
        for n, w in Human.SPINE_W.items():
            R.key_rot(n, f, [("X", flex * w), ("Y", side * w), ("Z", twist * w)])
        for n, w in Human.HEAD_W.items():
            R.key_rot(n, f, [("X", head[0] * w), ("Y", head[2] * w), ("Z", head[1] * w)])
        for s in "LR":
            R.key_rot("clavicle." + s, f, [("Y", (1 if s == "L" else -1) * clav)])
        R.key_rot("jaw", f, [("X", -jaw)])
    def head_M(self):
        return self.R.o.matrix_world @ self.R.PB["head"].matrix
    def chest_delta(self):
        return self.R.delta("spine01")
    def to_head_world(self, rest_pt):
        return self.head_M() @ (self.R.rest("head").inverted() @ Vector(rest_pt))

W, M = Body(WR, WH), Body(MR, MH)
ROOT_Z_W, ROOT_Z_M = W.root_head.z, M.root_head.z
print("ROOT Z", ROOT_Z_W, ROOT_Z_M)

# face: crying shape from the face bones (small rotations, keyed with the body)
def key_face(B, f, sad=0.0, squint=0.0, smile=0.0):
    R = B.R
    for s in "LR":
        sx = 1 if s == "L" else -1
        if "orbicularis03." + s in R.PB:
            R.key_rot("orbicularis03." + s, f, [("X", 10 * squint)])          # upper lid down
            R.key_rot("orbicularis04." + s, f, [("X", -6 * squint)])          # lower lid up
        if "oculi01." + s in R.PB:
            R.key_rot("oculi01." + s, f, [("X", -8 * sad), ("Z", sx * 6 * sad)])    # inner brow up
        if "risorius03." + s in R.PB:
            R.key_rot("risorius03." + s, f, [("X", 10 * sad - 12 * smile), ("Z", sx * 8 * smile)])  # mouth corner down / up
        if "levator05." + s in R.PB:
            R.key_rot("levator05." + s, f, [("X", -6 * sad)])

# ------------------------------------------------------------------ INVENTOR
POS_WS = Vector((0.0, 0.62, 0.0))
POS_OF = OF(0.3, -0.38, 0.0)          # seated in the office chair, facing world -Y (towards the desk)
SEAT_Z = 0.45
gun = bpy.data.objects["Gun"]
GUN_REST = Matrix.Translation((0.035, -0.33, 1.08)) @ Matrix.Rotation(R_(-4), 4, 'X')   # rest-body coords (gun points -Y)
GUN_AIM = Matrix.Translation((0.03, -0.40, 1.18)) @ Matrix.Rotation(R_(2), 4, 'X')
# hand grips in gun-local coordinates: (wrist, finger direction, palm normal)
GRIP_R = (Vector((-0.016, 0.07, -0.035)), Vector((0.25, -1.0, -0.55)), Vector((1.0, 0.0, 0.0)))
SUPPORT_L = (Vector((0.055, -0.05, -0.045)), Vector((-1.0, -0.5, 0.15)), Vector((0.0, 0.0, 1.0)))
VALVE_L = (Vector((0.135, -0.05, 0.095)), Vector((-0.7, -0.55, 0.05)), Vector((-1.0, 0.0, -0.2)))
inv_f = list(range(1, 2101, 4)) + [T_OFFICE_IN, T_OFFICE_IN + 1, T_OFFICE_OUT, T_OFFICE_OUT + 1]
inv_f = sorted(set(inv_f))
SOB_W = track([(1, 1.0), (F(4), 0.8), (F(6), 0.35), (F(15), 0.3), (F(18.7), 0.2)])
def sob(f, rate=3.6):
    return math.sin(2 * math.pi * f / (FPS / rate))
# office tracks (t in s)
OF_FLEX = track([(F(18.7), 14), (F(21), 22), (F(22.4), 24), (F(23.0), 38), (F(25.3), 36), (F(26.0), 14), (F(28.3), 12)])
OF_HEADP = track([(F(18.7), 12), (F(21), 18), (F(22.4), 20), (F(23.0), 28), (F(25.3), 24), (F(26.0), -6), (F(28.3), -4)])
OF_SOB = track([(F(18.7), 0.15), (F(22.4), 0.2), (F(22.8), 1.4), (F(25.3), 1.2), (F(26.0), 0.3), (F(28.3), 0.2)])
OF_FACE = track([(F(18.7), 0.0), (F(22.4), 0.0), (F(22.8), 1.0), (F(25.5), 1.0), (F(26.2), 0.0)])   # 0 lap, 1 hands on face
# workshop C (time-lapse + finale)
def inv_pose(f):
    t = (f - 1) / FPS
    if f <= T_OFFICE_IN:
        s_ = SOB_W(f) * sob(f)
        head = (14 + (16 if t > 4.3 else 0) * smooth((t - 4.3) / 0.8) - 8 * smooth((t - 13.0) / 1.0) + 2.0 * s_, 6 - 4 * smooth((t - 4.5) / 1), 3)
        flex = 9 + 2.5 * s_ + 3 * smooth((t - 4.5) / 1.0) - 5 * smooth((t - 13.2) / 1.0)
        recoil = 0.0
        if 15.0 <= t <= 15.5: recoil = math.sin(math.pi * (t - 15.0) / 0.5)
        return dict(pos=POS_WS + Vector((0, 0.008 * recoil, ROOT_Z_W - 0.01 + 0.004 * s_)), yaw=0, flex=flex - 4 * recoil, head=head,
                    clav=4 * s_ + 2, jaw=3 + 2 * s_, sad=1.0, squint=0.6 + 0.2 * s_, smile=0.0, recoil=recoil, set="ws")
    if f <= T_OFFICE_OUT:
        s_ = OF_SOB(f) * sob(f, 4.2)
        return dict(pos=POS_OF + Vector((0, 0.14, SEAT_Z + 0.09 + 0.006 * s_)), yaw=0, flex=OF_FLEX(f) + 3 * s_, head=(OF_HEADP(f) + 3 * s_, 0, 0),
                    clav=8 * s_ + 4 * OF_SOB(f), jaw=4 + 4 * OF_SOB(f) * (0.5 + 0.5 * s_), sad=0.6 + 0.4 * min(1, OF_SOB(f)),
                    squint=0.4 + 0.5 * min(1, OF_SOB(f)), smile=0.0, set="of")
    # workshop C
    if t < 31.2:   # time-lapse: three snapped poses (sketch, file at the vice, assemble)
        ph = 0 if t < 29.3 else (1 if t < 30.3 else 2)
        jig = math.sin(f * 0.9) * 0.6
        dx = (0.0, -0.32, 0.0)[ph]
        return dict(pos=POS_WS + Vector((dx, 0, ROOT_Z_W - 0.03)), yaw=(0, -10, 0)[ph], flex=(26, 14, 22)[ph] + jig, head=((22, 12, 24)[ph], (0, -14, 4)[ph], 0),
                    clav=2, jaw=1, sad=0.0, squint=0.15, smile=0.2, phase=ph, set="tl")
    lift = smooth((t - 31.4) / 0.7); fire = 1.0 if t >= 32.4 else 0.0
    recoil = math.sin(math.pi * min(1, max(0, (t - 32.4) / 0.4))) if t >= 32.4 else 0.0
    laugh = smooth((t - 33.2) / 0.5)
    lw = math.sin(2 * math.pi * f / (FPS / 5.0)) * laugh
    return dict(pos=POS_WS + Vector((0, 0.01 * recoil, ROOT_Z_W - 0.01 - 0.01 * laugh + 0.006 * lw)), yaw=0,
                flex=24 * (1 - lift) + 6 - 6 * recoil + 6 * laugh + 3 * lw, head=(20 * (1 - lift) + 2 + 5 * laugh * lw, 0, 0),
                clav=2 + 4 * lw, jaw=2 + 10 * laugh * (0.5 + 0.5 * lw), sad=0.25 * (1 - laugh), squint=0.3 + 0.4 * laugh, smile=laugh,
                lift=lift, recoil=recoil, set="fin")

def gun_world(f, p, D):
    """gun matrix for frame f given the inventor's pose and chest delta"""
    t = (f - 1) / FPS
    if p["set"] == "ws":
        a = smooth((t - 12.8) / 1.0)
        G = GUN_REST.lerp(GUN_AIM, a) if hasattr(Matrix, "lerp") else (GUN_AIM if a > 0.5 else GUN_REST)
        loc = GUN_REST.translation.lerp(GUN_AIM.translation, a)
        rot = GUN_REST.to_quaternion().slerp(GUN_AIM.to_quaternion(), a)
        rec = p.get("recoil", 0.0)
        G = Matrix.Translation(loc + Vector((0, 0.015 * rec, 0.008 * rec))) @ rot.to_matrix().to_4x4() @ Matrix.Rotation(R_(8 * rec), 4, 'X')
        return D @ G
    if p["set"] == "fin":
        rest = Matrix.Translation((0.05, 0.08, BT + 0.016)) @ Matrix.Rotation(R_(90), 4, 'Y') @ Matrix.Rotation(R_(20), 4, 'Z')
        if t < 31.5: return rest
        rec = p.get("recoil", 0.0)
        aim = D @ (Matrix.Translation(GUN_AIM.translation + Vector((0, 0.015 * rec, 0.01 * rec))) @ Matrix.Rotation(R_(2 + 9 * rec), 4, 'X'))
        a = smooth((t - 31.5) / 0.65)
        loc = rest.translation.lerp(aim.translation, a); rot = rest.to_quaternion().slerp(aim.to_quaternion(), a)
        return Matrix.Translation(loc) @ rot.to_matrix().to_4x4()
    return None

def lerp_grip(a, b, s):
    return tuple(x.lerp(y, s) for x, y in zip(a, b))
VALVE_TURN = track([(F(5.9), 0.0), (F(6.3), 0.0), (F(7.1), 1.0), (F(13.0), 1.0)])
for f in inv_f:
    p = inv_pose(f)
    W.key_body(f, p["pos"], p["yaw"], flex=p["flex"], head=p["head"], clav=p["clav"], jaw=p["jaw"])
    key_face(W, f, p["sad"], p["squint"], p["smile"])
    # feet
    yaw = p["yaw"]
    base = p["pos"].to_2d()
    for s in "LR":
        sx = 1 if s == "L" else -1
        if p["set"] == "of":
            xy = Vector((base.x + sx * 0.12, base.y - 0.42)); W.H.key_foot(s, f, xy, 0, 0, 0)
        else:
            xy = W.H.foot_xy(s, Vector((base.x, base.y, 0)), yaw) + Vector((0, 0.03 if s == "L" else -0.02))
            W.H.key_foot(s, f, xy, yaw + sx * 8)
for f in inv_f:
    ev(f); p = inv_pose(f); t = (f - 1) / FPS
    D = W.chest_delta()
    G = gun_world(f, p, D)
    if G is not None and (p["set"] == "ws" or t >= 31.5):
        gun.matrix_world = G; gun.keyframe_insert("location", frame=f); gun.keyframe_insert("rotation_euler", frame=f)
    elif p["set"] == "fin" or p["set"] == "tl":
        gun.matrix_world = gun_world(F(31.3), inv_pose(F(31.3)), D)
        gun.keyframe_insert("location", frame=f); gun.keyframe_insert("rotation_euler", frame=f)
    G3 = G.to_3x3() if G is not None else None
    chest = D
    if p["set"] == "ws":
        Wg, dg, ng = GRIP_R
        W.key_hand("R", f, G @ Wg, G3 @ dg, G3 @ ng, pole=G @ Vector((-0.35, 0.25, -0.25)))
        trig = 26 + 30 * smooth((t - 13.5) / 0.4) * (1 - smooth((t - 15.15) / 0.2))
        W.key_fingers("R", f, [trig, 78, 82, 86], thumb=34)
        v = smooth((t - 5.6) / 0.35) * (1 - smooth((t - 7.4) / 0.4))
        g = lerp_grip(SUPPORT_L, VALVE_L, v)
        turn = VALVE_TURN(f) * v
        Rt = Matrix.Rotation(R_(-35 * turn), 3, 'X')
        W.key_hand("L", f, G @ (Vector((0.05, -0.095, 0.085)) + Rt @ (g[0] - Vector((0.05, -0.095, 0.085)))), G3 @ (Rt @ g[1]), G3 @ (Rt @ g[2]),
                   pole=G @ Vector((0.4, 0.25, -0.3)))
        W.key_fingers("L", f, [40 + 10 * v, 50 + 15 * v, 55 + 20 * v, 60 + 20 * v], thumb=20 + 25 * v)
    elif p["set"] == "of":
        hm = W.head_M(); hm3 = hm.to_3x3()
        fs = OF_FACE(f)
        for s in "LR":
            sx = 1 if s == "L" else -1
            lap_W = Vector((base.x + sx * 0.09, base.y - 0.22, SEAT_Z + 0.2))
            lap = (lap_W, Vector((-sx * 0.35, -1.0, -0.2)), Vector((0, 0, -1)))
            face_W = hm @ (W.R.rest("head").inverted() @ Vector((sx * 0.045, -0.095, W.R.BN["head"].head_local.z + 0.035)))
            # wrist sits below the face, fingers up over the eyes, palm towards the face
            fc = (face_W + Vector((0, -0.03, -0.11)), hm3 @ Vector((-sx * 0.25, -0.05, 1.0)), hm3 @ Vector((0, 1.0, 0.2)))
            g = lerp_grip(lap, fc, fs)
            fist = smooth((t - 26.0) / 0.4)
            W.key_hand(s, f, g[0], g[1], g[2], pole=g[0] + Vector((sx * 0.4, 0.3, -0.3)))
            W.key_fingers(s, f, [15 + 60 * fist + 10 * fs] * 4, thumb=20 + 20 * fist)
    elif p["set"] == "tl":
        ph = p["phase"]
        pts = {0: {"R": (Vector((0.12, 0.18, BT + 0.035)), Vector((0.1, -1, -0.8)), Vector((0, 0, -1))),
                   "L": (Vector((-0.12, 0.15, BT + 0.03)), Vector((0.4, -1, -0.3)), Vector((0, 0, -1)))},
               1: {"R": (Vector((-0.42, -0.02, BT + 0.2)), Vector((-1, -0.3, -0.3)), Vector((0, 0, -1))),
                   "L": (Vector((-0.6, -0.02, BT + 0.2)), Vector((-1, -0.3, -0.2)), Vector((0, 0, -1)))},
               2: {"R": (Vector((-0.02, 0.18, BT + 0.07)), Vector((0.3, -1, -0.4)), Vector((0.5, 0, -1))),
                   "L": (Vector((0.16, 0.18, BT + 0.07)), Vector((-0.3, -1, -0.4)), Vector((-0.5, 0, -1)))}}[ph]
        wob = 0.02 * math.sin(f * 0.8)
        for s in "LR":
            Wp, d_, n_ = pts[s]
            W.key_hand(s, f, Wp + Vector((wob if s == "R" else -wob * 0.5, 0, 0)), d_, n_, pole=Wp + Vector(((1 if s == "L" else -1) * 0.4, 0.3, -0.2)))
            W.key_fingers(s, f, [45, 60, 65, 70] if ph != 1 else 75, thumb=30)
    else:   # finale
        lift = p["lift"]
        Wg, dg, ng = GRIP_R
        restR = (Vector((-0.2, 0.12, BT + 0.06)), Vector((0.1, -1, -0.6)), Vector((0, 0, -1)))
        reach = smooth((t - 31.15) / 0.35)
        if t < 31.5:
            Gs = gun_world(F(31.5), inv_pose(F(31.5)), D); g3 = Gs.to_3x3()
            tgt = (Gs @ Wg, g3 @ dg, g3 @ ng)
            g = lerp_grip(restR, tgt, reach)
        else:
            g = (G @ Wg, G3 @ dg, G3 @ ng)
        W.key_hand("R", f, g[0], g[1], g[2], pole=g[0] + Vector((-0.4, 0.3, -0.3)))
        trig = 26 + 30 * smooth((t - 32.25) / 0.15) * (1 - smooth((t - 32.7) / 0.2))
        W.key_fingers("R", f, [trig, 78, 82, 86] if t >= 31.4 else 30, thumb=34 if t >= 31.4 else 15)
        restL = (Vector((0.22, 0.1, BT + 0.05)), Vector((-0.2, -1, -0.6)), Vector((0, 0, -1)))
        if t < 31.8:
            gl = restL
        else:
            sL = smooth((t - 31.8) / 0.4) * (1 - smooth((t - 33.4) / 0.5))
            tgt = (G @ SUPPORT_L[0], G3 @ SUPPORT_L[1], G3 @ SUPPORT_L[2])
            free = (D @ Vector((0.2, -0.25, 1.0)), Vector((-0.4, -1, 0.2)), Vector((-1, 0, 0)))
            gl = lerp_grip(restL if t < 33.0 else free, tgt, sL)
        W.key_hand("L", f, gl[0], gl[1], gl[2], pole=gl[0] + Vector((0.4, 0.3, -0.3)))
        W.key_fingers("L", f, 45, thumb=25)

# ------------------------------------------------------------------ MENTOR
POS_MO = OF(0.3, 1.32, 0.0)        # behind the desk, facing world +Y (towards her)
POS_MW = Vector((0.25, -2.1, 0.0))  # in the workshop for the finale
men_f = sorted(set(list(range(1, 2101, 4)) + [T_OFFICE_OUT, T_OFFICE_OUT + 1]))
JAB = track([(F(19.0), 0.0), (F(19.6), 1.0), (F(22.2), 1.0), (F(22.6), 0.3), (F(23.5), 0.0)])
PELT = track([(F(26.2), 0.0), (F(26.5), 1.0), (F(28.2), 1.0), (F(28.6), 0.0)])
for f in men_f:
    t = (f - 1) / FPS
    if f <= T_OFFICE_OUT:
        talk = math.sin(2 * math.pi * f / (FPS / 4.5)) * (1 if t < 22.4 else 0)
        jab = JAB(f); pelt = PELT(f)
        flinch = math.sin(f * 1.7) * pelt
        awk = smooth((t - 22.6) / 0.6) * (1 - smooth((t - 26.0) / 0.4))
        pos = POS_MO + Vector((0.0, -0.08 * pelt, ROOT_Z_M - 0.005 - 0.03 * pelt))
        M.key_body(f, pos, 180, flex=10 * jab + 6 + 2 * talk - 14 * pelt, head=(-4 + 3 * talk + 8 * awk + 12 * pelt, 18 * pelt * flinch, 4 * awk),
                   side=6 * flinch, twist=-10 * jab + 25 * pelt, clav=2, jaw=3 + 5 * max(0, talk) + 10 * pelt)
        key_face(M, f, sad=0.3 * awk, squint=0.3 + 0.7 * pelt, smile=0.0)
        for s in "LR":
            sx = 1 if s == "L" else -1
            M.H.key_foot(s, f, M.H.foot_xy(s, Vector((POS_MO.x, POS_MO.y, 0)), 180), 180 + sx * 8)
    else:
        arms = smooth((t - 31.3) / 0.6)
        hit = math.sin(math.pi * min(1, max(0, (t - 32.9) / 0.45))) if t >= 32.9 else 0.0
        laugh = smooth((t - 33.3) / 0.5); lw = math.sin(2 * math.pi * f / (FPS / 4.6)) * laugh
        pos = POS_MW + Vector((0, -0.07 * hit, ROOT_Z_M - 0.035 * arms + 0.008 * lw))
        M.key_body(f, pos, 180, flex=-4 * arms - 12 * hit + 8 * laugh + 3 * lw, head=(-6 * arms + 10 * hit + 6 * lw * laugh, 10 * arms * (1 - laugh), 0),
                   clav=4 * arms + 3 * lw, jaw=2 + 4 * arms * (1 - laugh) + 12 * laugh * (0.5 + 0.5 * lw))
        key_face(M, f, sad=0.0, squint=0.8 * arms * (1 - laugh) + 0.5 * laugh, smile=0.5 * arms + 0.5 * laugh)
        for s in "LR":
            sx = 1 if s == "L" else -1
            M.H.key_foot(s, f, M.H.foot_xy(s, Vector((POS_MW.x, POS_MW.y, 0)), 180) + Vector((sx * 0.04, 0)), 180 + sx * 10)
for f in men_f:
    ev(f); t = (f - 1) / FPS
    D = M.chest_delta()
    if f <= T_OFFICE_OUT:
        jab = JAB(f); pelt = PELT(f); awk = smooth((t - 22.6) / 0.6) * (1 - smooth((t - 26.0) / 0.4))
        talk = math.sin(2 * math.pi * f / (FPS / 4.5)) * (1 if t < 22.4 else 0)
        fw = Vector((0, 1, 0))       # he faces world +Y
        desk_y = POS_MO.y + 0.42
        # left hand planted on the desk
        Wl = Vector((POS_MO.x - 0.28, desk_y, DT + 0.035))
        M.key_hand("L", f, Wl, Vector((0.2, 1, -0.2)), Vector((0, 0, -1)), pole=Wl + Vector((-0.4, -0.3, 0.3)))
        M.key_fingers("L", f, 10, thumb=10)
        # right hand: rest on desk -> jabbing finger -> neck rub; pelting: both arms shield the face
        rest = (Vector((POS_MO.x + 0.25, desk_y, DT + 0.035)), Vector((-0.2, 1, -0.2)), Vector((0, 0, -1)))
        jabW = D @ Vector((-0.12, -0.55 - 0.06 * talk, 1.36 + 0.04 * talk))
        jb = (jabW, Vector((0.1, 1, 0.1)), Vector((0.9, 0, -0.3)))
        hm = M.head_M()
        neck = (hm @ (M.R.rest("head").inverted() @ Vector((-0.07, 0.09, M.R.BN["head"].head_local.z - 0.06))), Vector((0.7, 0.2, 0.6)), Vector((0, -1, 0)))
        g = lerp_grip(rest, jb, jab)
        g = lerp_grip(g, neck, awk)
        shieldR = (D @ Vector((-0.02, -0.33, 1.55)), Vector((0.8, 0.1, 0.6)), Vector((0, -1, 0)))
        shieldL = (D @ Vector((0.05, -0.36, 1.48)), Vector((-0.8, 0.1, 0.6)), Vector((0, -1, 0)))
        g = lerp_grip(g, shieldR, pelt)
        M.key_hand("R", f, g[0], g[1], g[2], pole=g[0] + Vector((-0.45, -0.25, -0.2)))
        if pelt > 0.01:
            gl = lerp_grip((Wl, Vector((0.2, 1, -0.2)), Vector((0, 0, -1))), shieldL, pelt)
            M.key_hand("L", f, gl[0], gl[1], gl[2], pole=gl[0] + Vector((0.45, -0.25, -0.2)))
        pointing = jab * (1 - awk) * (1 - pelt)
        M.R.key_q("finger2-1.R", f, Quaternion()); M.key_fingers("R", f, [8 * (1 - pointing) + 4, 20 + 60 * pointing, 20 + 65 * pointing, 20 + 70 * pointing], thumb=20 + 20 * pointing)
    else:
        arms = smooth((t - 31.3) / 0.6); hit = math.sin(math.pi * min(1, max(0, (t - 32.9) / 0.45))) if t >= 32.9 else 0.0
        laugh = smooth((t - 33.3) / 0.5)
        for s in "LR":
            sx = 1 if s == "L" else -1
            hang = D @ Vector((sx * 0.24, -0.02, 0.86))
            outW = D @ Vector((sx * 0.72, -0.12 - 0.06 * hit, 1.42 + 0.1 * hit))
            belly = D @ Vector((sx * 0.07, -0.2, 1.05))
            Wp = hang.lerp(outW, arms * (1 - laugh)).lerp(belly, laugh * (1 if s == "R" else 0.5))
            d_ = Vector((sx * 1, -0.2, 0.0)).lerp(Vector((0, 0, -1)), 1 - arms) if laugh < 0.5 else Vector((-sx, -0.2, -0.3))
            n_ = Vector((0, -1, 0)) if laugh < 0.5 else Vector((0, 1, 0))
            M.key_hand(s, f, Wp, d_, n_, pole=Wp + Vector((sx * 0.2, 0.4, -0.3)))
            M.key_fingers(s, f, 20, thumb=15)

# ------------------------------------------------------------------ tube points + hero tear path
anchors = [bpy.data.objects["TubeH%d" % i] for i in range(5)]
sp = tube.data.splines[0]
for bp in sp.bezier_points: bp.handle_left_type = bp.handle_right_type = 'FREE'
TUBE = {}
def tube_ctrl():
    P = [a.matrix_world.translation.copy() for a in anchors]
    Hs = []
    for i, p in enumerate(P):
        a_ = P[max(0, i - 1)]; b_ = P[min(len(P) - 1, i + 1)]
        tg = (b_ - a_) / (6 if 0 < i < len(P) - 1 else 3)
        if i == len(P) - 1: tg = Vector((0, 0, -1)) * (P[i] - P[i - 1]).length / 3 if False else (P[i] - P[i - 1]) / 3
        Hs.append((p - tg, p + tg))
    return P, Hs
def bez(p0, p1, p2, p3, u):
    v = 1 - u; return p0 * v ** 3 + p1 * 3 * v * v * u + p2 * 3 * v * u * u + p3 * u ** 3
def tube_point(P, Hs, u):
    """u in [0,1] along the whole tube (approx. uniform per segment by chord length)"""
    L = [(P[i + 1] - P[i]).length for i in range(len(P) - 1)]; tot = sum(L); d = u * tot
    for i, l in enumerate(L):
        if d <= l or i == len(L) - 1:
            return bez(P[i], Hs[i][1], Hs[i + 1][0], P[i + 1], max(0, min(1, d / l)))
        d -= l
for f in range(1, T_OFFICE_IN + 1, 2):
    ev(f); P, Hs = tube_ctrl(); TUBE[f] = (P, Hs)
    for bp, p, h in zip(sp.bezier_points, P, Hs):
        bp.co = p; bp.handle_left = h[0]; bp.handle_right = h[1]
        bp.keyframe_insert("co", frame=f); bp.keyframe_insert("handle_left", frame=f); bp.keyframe_insert("handle_right", frame=f)
def tube_at(f, u):
    f2 = f if f % 2 == 1 else f - 1
    f2 = max(1, min(f2, max(TUBE)))
    P, Hs = TUBE[f2]; return tube_point(P, Hs, u)
for nm in ("TearTube", "Funnel", "Funnel_Arm", "Funnel_Rim"):
    key_hide(bpy.data.objects[nm], [(1, False), (T_OFFICE_IN + 1, True)])

def chamber_world(f, local):
    return gun_mat(f) @ Vector(local)
GUN_M = {}
def gun_mat(f):
    if f not in GUN_M:
        ev(f); GUN_M[f] = gun.matrix_world.copy()
    return GUN_M[f]

head_rest_inv = W.R.rest("head").inverted()
def head_pt(f, rest_pt, fwd=0.0):
    ev(f); hm = W.head_M()
    return hm @ (head_rest_inv @ (Vector(rest_pt) + Vector((0, -fwd, 0))))
lidL, lidR = Vector(sc["lidL"]), Vector(sc["lidR"])
fun = bpy.data.objects["Funnel"]
CH_BOTTOM_Z = 0.0715
pool = [Vector((0.012 * math.cos(a), -0.095 + 0.012 * math.sin(a), CH_BOTTOM_Z + 0.001 * (i % 2))) for i, a in enumerate([k * 2.4 for k in range(9)])]
pool.append(Vector((0.0, -0.095, CH_BOTTOM_Z + 0.004)))
tears = [bpy.data.objects["Tear_%02d" % i] for i in range(14)]
def key_obj(o, f, loc, scale=None):
    o.location = loc; o.keyframe_insert("location", frame=f)
    if scale is not None:
        o.scale = scale if isinstance(scale, (tuple, Vector)) else (scale,) * 3; o.keyframe_insert("scale", frame=f)
# hero tear (Tear_00): well on the lid, roll to the funnel, ride the tube, fall into the chamber
hero = tears[0]
T_WELL, T_ROLL, T_TIP, T_TUBE, T_INLET, T_LAND = 0.3, 1.8, 2.3, 2.55, 4.4, 4.78
for f in range(1, F(5.2)):
    t = (f - 1) / FPS
    if t < T_ROLL:
        s = 0.25 + 0.95 * smooth((t - T_WELL) / 1.3)
        p = head_pt(f, lidL, 0.0042 + 0.0012 * s); sc_ = (s * 1.15, s * 0.95, s * 0.85)
    elif t < T_TIP:
        u = smooth((t - T_ROLL) / (T_TIP - T_ROLL))
        a = head_pt(f, lidL, 0.0055); b = fun.matrix_world @ Vector((0, 0, -0.004))
        p = a.lerp(b, u); sc_ = (1.1, 1.0, 1.2 + 0.3 * math.sin(math.pi * u))
    elif t < T_TUBE:
        u = (t - T_TIP) / (T_TUBE - T_TIP); ev(f)
        p = (fun.matrix_world @ Vector((0, 0, -0.004))).lerp(fun.matrix_world @ Vector((0, 0, -0.02)), u); sc_ = (0.9, 0.9, 1.3)
    elif t < T_INLET:
        u = (t - T_TUBE) / (T_INLET - T_TUBE); u = u * u * (1.6 - 0.6 * u)
        p = tube_at(f, u); sc_ = (0.85, 0.85, 1.4)
    else:
        u = min(1.0, (t - T_INLET) / (T_LAND - T_INLET))
        G = gun_mat(f); top_ = G @ Vector((0, -0.095, 0.14)); bot = G @ pool[-1]
        p = top_.lerp(bot, u * u); sc_ = (0.9, 0.9, 1.25) if u < 1 else (1.25, 1.25, 0.6 + 0.5 * smooth((t - T_LAND) / 0.25))
    key_obj(hero, f, p, sc_)
for f in range(F(5.2), F(15.1), 3):
    key_obj(hero, f, gun_mat(f) @ pool[-1], (1.25, 1.25, 1.1) if f < F(10.4) else (1.0, 1.0, 1.0))
# pooled drops in the chamber (parented to the gun)
for i, o in enumerate(tears[1:10]):
    o.parent = gun; o.location = pool[i]; o.scale = (1.2, 1.2, 0.75)
    key_obj(o, 1, pool[i], (1.2, 1.2, 0.75))
# drops already travelling the tube (keep the tube alive before and during the ride)
for o, t0 in zip(tears[10:14], (0.2, 1.1, 3.0, 3.7)):
    for f in range(1, T_OFFICE_IN, 2):
        t = (f - 1) / FPS; u = (t - t0) / 1.9
        if u < 0: p = head_pt(f, lidL, 0.003) if False else tube_at(f, 0.0); s = 0.0
        elif u < 1: p = tube_at(f, u); s = 0.8
        else:
            G = gun_mat(f); k = min(1, (u - 1) * 6); p = (G @ Vector((0, -0.095, 0.14))).lerp(G @ (pool[tears.index(o) % 9] + Vector((0, 0, 0.004))), k * k); s = 0.8 if k < 1 else 0.0
        key_obj(o, f, p, (s, s, s * 1.4))
# right-eye tears running down the cheek (no funnel on that side)
cheekR = [lidR] + [Vector(sc[k]) for k in ("cheekR1", "cheekR2", "cheekR3", "chinR")]
for i in range(6):
    o = bpy.data.objects["TearR_%02d" % i]; t0 = 0.2 + i * 0.85
    for f in range(1, T_OFFICE_IN, 2):
        t = (f - 1) / FPS; u = (t - t0) / 1.6
        if u < 0 or u > 1.25: key_obj(o, f, Vector((0, 0, -50)), 0.0); continue
        if u <= 1:
            k = u * (len(cheekR) - 1); i0 = min(int(k), len(cheekR) - 2); w = k - i0
            rp = cheekR[i0].lerp(cheekR[i0 + 1], w); p = head_pt(f, rp, 0.0034); s = 0.9 + 0.3 * (1 - u)
        else:
            p0 = head_pt(f, cheekR[-1], 0.002); dt = (u - 1) * 1.6; p = p0 + Vector((0, -0.05 * dt, -4.9 * dt * dt)); s = 0.8
        key_obj(o, f, p, (s, s * 0.9, s * 1.3))

# ------------------------------------------------------------------ freeze, frost, gas, spring, trigger, pellets
for i, o in enumerate(tears[:10]):
    m = o.data.materials[0]; sock = m.node_tree.nodes["Freeze"].outputs[0]
    t0 = 10.25 + 0.17 * i
    key_node(sock, 1, 0.0); key_node(sock, F(t0), 0.0); key_node(sock, F(t0 + 0.8), 1.0)
    key_node(sock, F(19.0), 1.0); key_node(sock, F(19.1), 0.0)
    if i > 0:
        key_obj(o, F(t0), pool[i - 1], (1.2, 1.2, 0.75)); key_obj(o, F(t0 + 0.9), pool[i - 1] + Vector((0, 0, 0.0012)), (0.95, 0.95, 0.95))
fm = bpy.data.materials["M_Frost"]; nt = fm.node_tree; n = nt.nodes
pb_ = n["Principled BSDF"]; out = n["Material Output"]
tcn = n.new('ShaderNodeTexCoord'); sep = n.new('ShaderNodeSeparateXYZ'); grow = n.new('ShaderNodeValue'); grow.name = "FrostGrow"
nz = n.new('ShaderNodeTexNoise'); nz.inputs["Scale"].default_value = 120
mr = n.new('ShaderNodeMapRange'); mr.inputs["From Min"].default_value = -0.03; mr.inputs["From Max"].default_value = 0.03
add = n.new('ShaderNodeMath'); add.operation = 'ADD'; mul = n.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 0.3
lt = n.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'
trn = n.new('ShaderNodeBsdfTransparent'); mx = n.new('ShaderNodeMixShader')
L = nt.links
L.new(tcn.outputs["Object"], sep.inputs[0]); L.new(sep.outputs["Z"], mr.inputs["Value"])          # grows from the bottom up
L.new(tcn.outputs["Object"], nz.inputs["Vector"]); L.new(nz.outputs["Fac"], mul.inputs[0])
L.new(mr.outputs["Result"], add.inputs[0]); L.new(mul.outputs[0], add.inputs[1])
L.new(add.outputs[0], lt.inputs[0]); L.new(grow.outputs[0], lt.inputs[1])
L.new(lt.outputs[0], mx.inputs[0]); L.new(trn.outputs[0], mx.inputs[1]); L.new(pb_.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs["Surface"])
for f, v in ((1, -0.2), (F(10.3), -0.2), (F(12.8), 1.35), (F(18.0), 1.35)):
    key_node(grow.outputs[0], f, v)
gsock = node_val("M_Gas", "GasDensity")
for f, v in ((1, 0.0), (F(7.45), 0.0), (F(7.8), 1.0), (F(10.6), 1.0), (F(12.6), 0.0)):
    key_node(gsock, f, v)
for i in range(6):
    o = bpy.data.objects["Gas_%d" % i]; o.parent = gun
    start = Vector((0.03, -0.095, 0.085)) if i < 5 else Vector((0.0, -0.162, -0.004))
    for k, t in enumerate([7.3, 7.5 + 0.12 * i, 8.6 + 0.2 * i, 10.0, 12.6]):
        if i < 5:
            ang = i * 1.3 + k * 0.7
            p = start.lerp(Vector((0.006 * math.cos(ang), -0.095 + 0.008 * math.sin(ang), 0.09 + 0.005 * (i - 2))), min(1, k / 2))
            s = (0.15, 0.4, 1.0, 1.3, 1.6)[k] * (0.9 + 0.1 * i)
        else:
            p = start + Vector((0, -0.01 * k, 0.003 * k)); s = (0.1, 0.6, 1.0, 1.2, 0.2)[k]
        key_obj(o, F(t), p, s)
    key_obj(o, 1, start, 0.01)
spring = bpy.data.objects["Gun_Spring"]; plunger = bpy.data.objects["Gun_Plunger"]; trig = bpy.data.objects["Gun_TriggerPivot"]
for t, L_ in ((0, 0.075), (13.6, 0.075), (14.5, 0.036), (14.95, 0.036), (15.0, 0.088), (15.08, 0.068), (15.18, 0.079), (15.3, 0.075),
              (32.38, 0.075), (32.42, 0.088), (32.5, 0.07), (32.62, 0.075)):
    f = F(t); spring.scale = (1, L_, 1); spring.keyframe_insert("scale", frame=f)
    plunger.location = (0, -0.052 - L_ - 0.003, 0.034); plunger.keyframe_insert("location", frame=f)
for t, a in ((0, 0), (13.5, 0), (13.9, -22), (15.15, -22), (15.35, 0), (32.2, 0), (32.35, -22), (32.6, 0)):
    trig.rotation_euler = (R_(a), 0, 0); trig.keyframe_insert("rotation_euler", frame=F(t))
wheel = bpy.data.objects["Gun_ValveWheel"]
for f in (1, F(6.3), F(7.1)):
    wheel.rotation_euler = (-R_(180) * VALVE_TURN(f), 0, 0); wheel.keyframe_insert("rotation_euler", frame=f)
# hide the chamber ice as it is fired
for i, o in enumerate(tears[:10]):
    key_hide(o, [(1, False), (F(15.0 + 0.05 * i), False), (F(15.05 + 0.05 * i), True)])
pellets = [bpy.data.objects["Pellet_%02d" % i] for i in range(12)]
sparks = [bpy.data.objects["Spark_%02d" % i] for i in range(24)]
FRAME_PHOTO = Vector((0.05, -3.76, 1.3))
def fire(objs, t0, t1, f_src, target, spread, hide_after=True, gap=0.1, tag=0):
    G = gun_mat(f_src)
    muzzle = G @ Vector((0, -0.26, 0.034))
    paths = []
    for i, o in enumerate(objs):
        ts = t0 + gap * i; te = t1 + gap * i * 0.7
        off = Vector((random.uniform(-1, 1), random.uniform(-0.3, 0.3), random.uniform(-1, 1))) * spread * (0 if i == 0 else 1)
        tgt = target + off
        mid = muzzle.lerp(tgt, 0.5) + Vector((0, 0, 0.04 + 0.02 * i))
        for f in range(F(ts) - 1, F(te) + 2):
            t = (f - 1) / FPS
            if t < ts:
                key_obj(o, f, G @ Vector((0, -0.2, 0.034)), 0.0); continue
            u = min(1.0, (t - ts) / (te - ts))
            p = bez(muzzle, muzzle.lerp(mid, 0.66), mid.lerp(tgt, 0.33), tgt, u)
            key_obj(o, f, p, 1.5 if u < 1 else 0.0)
        paths.append((ts, te, muzzle, mid, tgt))
        key_obj(o, 1, Vector((0, 0, -50)), 0.0) if tag == 0 else None
    return paths
pel_paths = fire(pellets, 15.0, 18.72, F(15.0), FRAME_PHOTO, 0.22, gap=0.09)
for o in pellets: key_obj(o, F(19.6), Vector((0, 0, -50)), 0.0)
fin_paths = None
# sparks ride along the pellets and twinkle
for i, s_ in enumerate(sparks):
    pi = i % 12; ts, te, m0, mid, tgt = pel_paths[pi]
    key_obj(s_, 1, Vector((0, 0, -50)), 0.0)
    for f in range(F(ts), F(te), 3):
        t = (f - 1) / FPS; u = (t - ts) / (te - ts)
        p = bez(m0, m0.lerp(mid, 0.66), mid.lerp(tgt, 0.33), tgt, u) + Vector((math.sin(f * 0.7 + i), math.cos(f * 0.5 + i), math.sin(f * 0.3 + 2 * i))) * 0.012
        tw = max(0.0, math.sin(f * 0.45 + i * 1.7)) * 1.6
        key_obj(s_, f, p, tw)
    key_obj(s_, F(te) + 2, Vector((0, 0, -50)), 0.0)
mp = bpy.data.objects["MuzzlePuff"]; mpm = mp.data.materials[0]
mpd = mpm.node_tree.nodes["PuffDensity"].outputs[0]
for f, v in ((1, 0.0), (F(15.0), 0.0), (F(15.1), 1.0), (F(16.0), 0.0), (F(32.4), 0.0), (F(32.5), 1.0), (F(33.4), 0.0)):
    key_node(mpd, f, v)
for t in (15.0, 32.4):
    G = gun_mat(F(t)); mz = G @ Vector((0, -0.29, 0.034))
    key_obj(mp, F(t) - 1, mz, 0.2); key_obj(mp, F(t + 0.9), mz + (G.to_3x3() @ Vector((0, -0.12, 0.02))), 2.2)
key_obj(mp, 1, Vector((0, 0, -50)), 0.2)

# ------------------------------------------------------------------ office: tear projectiles pelt the mentor (inside the thought bubble)
ev(F(27.0)); mhead = M.head_M().translation.copy(); mchest = (M.R.o.matrix_world @ M.R.PB["spine01"].matrix).translation.copy()
ev(F(26.0)); ihead = W.head_M().translation.copy()
pelt_drops = [tears[0]] + tears[10:14] + [bpy.data.objects["TearR_%02d" % k] for k in range(6)]
for i, o in enumerate(pelt_drops):
    t0 = 26.3 + 0.13 * i; t1 = t0 + 0.42
    src = ihead + Vector((random.uniform(-0.12, 0.12), -0.15, 0.12 + random.uniform(0, 0.15)))
    tgt = (mhead if i % 2 else mchest) + Vector((random.uniform(-0.12, 0.12), 0.05, random.uniform(-0.1, 0.1)))
    for f in range(F(t0) - 1, F(t1) + 6):
        t = (f - 1) / FPS
        if t < t0: key_obj(o, f, src, 0.0); continue
        u = min(1, (t - t0) / (t1 - t0)); p = src.lerp(tgt, u) + Vector((0, 0, 0.12 * math.sin(math.pi * u)))
        s = 4.0 if u < 1 else max(0.0, 4.5 - (t - t1) * 40)
        key_obj(o, f, p, (s, s, s * (1.3 if u < 1 else 0.4)))
    o.hide_render = False
    key_hide(o, [(F(t0) - 2, False)])
    key_obj(o, F(28.4), Vector((0, 0, -50)), 0.0)
# un-parent the chamber drops for the office use: Tear_01..09 are parented to the gun; give them world keys after the office starts
# (their location keys are in gun space; in the office they are used in gun space too, so instead convert: keep simple, hide them there)
# ------------------------------------------------------------------ thought bubble
bub = bpy.data.objects["ThoughtBubble"]; bon = node_val("M_Bubble", "BubbleOn")
for f, v in ((1, 0.0), (F(25.55), 0.0), (F(25.7), 1.0), (F(28.15), 1.0), (F(28.3), 0.0)):
    key_node(bon, f, v)
bc0 = ihead + Vector((0.0, -0.05, 0.42)); bc1 = OF(0.3, 0.45, 1.5)
for t, c, r in ((25.5, bc0, 0.02), (26.0, bc0, 0.28), (26.35, bc0.lerp(bc1, 0.4), 0.9), (26.7, bc1, 1.6), (28.15, bc1, 1.65), (28.25, bc1, 2.4)):
    key_obj(bub, F(t), c, r)
key_obj(bub, 1, Vector((0, 0, -50)), 0.01)
for i in range(3):
    o = bpy.data.objects["ThoughtBubbleSmall_%d" % i]
    c = ihead + Vector((0.08 - 0.03 * i, -0.08, 0.16 + 0.09 * i))
    key_obj(o, 1, Vector((0, 0, -50)), 0.0); key_obj(o, F(25.5 + 0.08 * i), c, 0.0)
    key_obj(o, F(25.7 + 0.08 * i), c, 0.025 + 0.02 * i); key_obj(o, F(28.15), c + Vector((0, 0, 0.03)), 0.03 + 0.02 * i); key_obj(o, F(28.3), c, 0.0)

# ------------------------------------------------------------------ time-lapse props + grinder sparks (beat 12)
tl = {n: bpy.data.objects[n] for n in ("TL_Sketch", "TL_Pencil", "TL_File")}
key_obj(tl["TL_Sketch"], 1, Vector((0, 0, -50))); key_obj(tl["TL_Sketch"], F(28.3), Vector((0.1, -0.05, BT + 0.001)))
tl["TL_Sketch"].rotation_euler = (0, 0, R_(8))
for f in range(F(28.3), F(29.3), 4):
    hm = Vector((0.12 + 0.03 * math.sin(f * 0.6), -0.07 + 0.02 * math.cos(f * 0.9), BT + 0.012))
    key_obj(tl["TL_Pencil"], f, hm); tl["TL_Pencil"].rotation_euler = (R_(-40), 0, R_(25)); tl["TL_Pencil"].keyframe_insert("rotation_euler", frame=f)
key_obj(tl["TL_Pencil"], 1, Vector((0, 0, -50))); key_obj(tl["TL_Pencil"], F(28.3) - 1, Vector((0, 0, -50)))
key_obj(tl["TL_Pencil"], F(29.32), Vector((0.3, -0.1, BT + 0.004)))
tl["TL_Pencil"].rotation_euler = (0, R_(90), R_(30)); tl["TL_Pencil"].keyframe_insert("rotation_euler", frame=F(29.32))
key_obj(tl["TL_File"], 1, Vector((0, 0, -50))); key_obj(tl["TL_File"], F(29.3) - 1, Vector((0, 0, -50)))
for f in range(F(29.3), F(30.3), 3):
    key_obj(tl["TL_File"], f, Vector((-0.5 + 0.05 * math.sin(f * 0.9), -0.02, BT + 0.21)))
    tl["TL_File"].rotation_euler = (0, R_(90), R_(90)); tl["TL_File"].keyframe_insert("rotation_euler", frame=f)
key_obj(tl["TL_File"], F(30.32), Vector((-0.3, -0.25, BT + 0.006)))
for i in range(5):
    o = bpy.data.objects["TL_Blank_%d" % i]
    key_obj(o, 1, Vector((0, 0, -50))); key_obj(o, F(29.0 + 0.3 * i) - 1, Vector((0, 0, -50)))
    key_obj(o, F(29.0 + 0.3 * i), Vector((-0.25 + 0.09 * i, -0.18, BT + 0.015)))
    key_obj(o, F(30.4 + 0.12 * i), Vector((-0.25 + 0.09 * i, -0.18, BT + 0.015))); key_obj(o, F(30.5 + 0.12 * i), Vector((0, 0, -50)))
for i in range(20):
    o = bpy.data.objects["GSpark_%02d" % i]
    key_obj(o, 1, Vector((0, 0, -50)))
    for f in range(F(29.35) + i % 3, F(30.25), 3):
        u = ((f * 7 + i * 13) % 11) / 11.0
        a = R_(-120 + 70 * ((i * 37 % 17) / 17.0))
        p = Vector((-0.5, -0.03, BT + 0.2)) + Vector((math.cos(a) * 0.3 * u, -0.25 * u, math.sin(a) * 0.12 * u - 0.15 * u * u))
        key_obj(o, f, p)
        o.rotation_euler = (R_(30), 0, a); o.keyframe_insert("rotation_euler", frame=f)
    key_obj(o, F(30.3), Vector((0, 0, -50)))
    set_interp(o, 'CONSTANT')
# gun visibility: hidden in the office and while it is being built
for o in [gun] + [c for c in bpy.data.objects if c.name.startswith("Gun_")]:
    if o is gun: continue
    key_hide(o, [(1, False), (T_OFFICE_IN + 1, True), (F(30.4), False)])

# ------------------------------------------------------------------ finale: pellets hit his shirt
ev(F(32.9)); mchest = (M.R.o.matrix_world @ M.R.PB["spine02"].matrix).translation + Vector((0, 0.13, 0.05))
fin_paths = fire(pellets[:8], 32.42, 32.9, F(32.42), mchest, 0.06, gap=0.03, tag=1)
for o in pellets[:8]: key_obj(o, F(33.1), Vector((0, 0, -50)), 0.0)
ip = bpy.data.objects["ImpactPuff"]; ipd = node_val("M_FrostPuff", "PuffDensity")
key_obj(ip, 1, Vector((0, 0, -50)), 0.1); key_obj(ip, F(32.88), mchest + Vector((0, 0.03, 0)), 0.1)
key_obj(ip, F(33.4), mchest + Vector((0, 0.12, 0.06)), 1.4); key_obj(ip, F(34.6), mchest + Vector((0.05, 0.25, 0.2)), 2.4)
for f, v in ((1, 0.0), (F(32.88), 0.0), (F(32.95), 1.0), (F(33.8), 0.6), (F(34.8), 0.0)):
    key_node(ipd, f, v)
for i, s_ in enumerate(sparks):
    a = i * 2.4; el = (i % 5 - 2) * 0.3
    d_ = Vector((math.cos(a), 0.6 + 0.4 * abs(math.sin(a)), math.sin(a) * 0.8 + el)).normalized()
    key_obj(s_, F(32.9) - 1, Vector((0, 0, -50)), 0.0)
    for k, t in enumerate((32.9, 33.15, 33.5, 33.9)):
        key_obj(s_, F(t), mchest + d_ * (0.03 + 0.22 * k * (0.7 + 0.3 * (i % 3))) + Vector((0, 0, -0.05 * k * k)), (1.8, 1.4, 0.8, 0.0)[k])

# ------------------------------------------------------------------ lights: cutaway studio on, time-lapse daylight sweep, finale warm
key_studio = bpy.data.objects["L_StudioKey"]; rim = bpy.data.objects["L_StudioRim"]
for o, loc in ((key_studio, (-0.3, -0.25, 0.3)), (rim, (0.25, 0.3, 0.25))):
    o.parent = gun; o.location = loc
    c = o.constraints.new('TRACK_TO'); c.target = gun; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
for o, e in ((key_studio, 18.0), (rim, 12.0)):
    for f, v in ((1, 0.0), (F(4.3), 0.0), (F(4.8), e), (F(15.2), e), (F(15.8), 0.0)):
        o.data.energy = v; o.data.keyframe_insert("energy", frame=f)
moon = bpy.data.objects["L_WindowMoon"].data
for t, e, c in ((0, 25, (0.55, 0.7, 1.0)), (28.4, 25, (0.55, 0.7, 1.0)), (29.2, 220, (1.0, 0.85, 0.6)), (30.2, 300, (1.0, 0.97, 0.9)), (31.0, 30, (0.55, 0.7, 1.0))):
    moon.energy = e; moon.color = c; moon.keyframe_insert("energy", frame=F(t)); moon.keyframe_insert("color", frame=F(t))
nightw = bpy.data.materials["M_NightOutside"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for t, v in ((0, 0.6), (28.4, 0.6), (29.2, 6.0), (30.2, 8.0), (31.0, 0.6)):
    key_node(nightw, F(t), v)

# ------------------------------------------------------------------ camera: one camera, Catmull-Rom through framings
cam_d = bpy.data.cameras.new("CAM_Film"); cam = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(cam); sc.camera = cam
cam_d.sensor_fit = 'AUTO'; cam_d.clip_start = 0.004; cam_d.clip_end = 60; cam_d.dof.use_dof = True
def EYE(f): return head_pt(f, Vector(sc["eyeL"]) * 0.5 + Vector(sc["lidR"]) * 0.0 + Vector((0, 0, 0)) * 0 + Vector(sc["eyeL"]) * 0.5 * 0, 0) if False else head_pt(f, (Vector(sc["eyeL"]) + Vector(sc["lidR"]) + Vector((0, 0, 0.016))) / 2, 0)
def HEAD(B, f): ev(f); return B.head_M().translation.copy()
def G(f, v): return gun_mat(f) @ Vector(v)
def P_(f, o): ev(f); return o.matrix_world.translation.copy()
CH = (0, -0.095, 0.09)
# waypoints: (t, camera position, look target, lens, fstop)
WP = []
def wp(t, pos, tgt, lens, fs=4.0): WP.append((F(t), Vector(pos), Vector(tgt), lens, fs))
f0 = 1
e0 = EYE(1)
wp(0.0, e0 + Vector((0.16, -0.40, 0.02)), e0 + Vector((0, 0, -0.01)), 55, 2.8)
wp(1.0, EYE(F(1)) + Vector((0.08, -0.30, -0.01)), EYE(F(1)) + Vector((0.01, 0, -0.01)), 60, 2.8)
wp(1.8, P_(F(1.8), hero) + Vector((0.07, -0.16, 0.0)), P_(F(1.8), hero), 70, 5.6)
for t in (2.4, 2.9, 3.4, 3.9, 4.35):
    h = P_(F(t), hero); d = (tube_at(F(t), 0.5) - tube_at(F(t), 0.4)).normalized()
    side = d.cross(Vector((0, -1, 0))).normalized()
    wp(t, h - Vector((0, 0.11, 0)) + side * 0.03 - d * 0.03, h + d * 0.01, 70, 8)
wp(4.8, G(F(4.8), (0.06, -0.21, 0.13)), G(F(4.8), (0, -0.095, 0.085)), 70, 11)
wp(5.4, G(F(5.4), (0.02, -0.16, 0.22)), G(F(5.4), CH), 60, 11)
wp(6.2, G(F(6.2), (0.24, -0.20, 0.14)), G(F(6.2), (0.05, -0.09, 0.08)), 50, 11)
wp(7.0, G(F(7.0), (0.26, -0.02, 0.10)), G(F(7.0), (0.04, -0.09, 0.07)), 55, 11)
wp(7.8, G(F(7.8), (0.16, -0.24, -0.05)), G(F(7.8), (0.0, -0.14, 0.0)), 60, 11)
wp(8.7, G(F(8.7), (0.08, -0.25, 0.04)), G(F(8.7), (0.02, -0.11, 0.05)), 60, 11)
wp(9.5, G(F(9.5), (0.06, -0.16, 0.10)), G(F(9.5), CH), 70, 11)
wp(10.3, G(F(10.3), (0.035, -0.15, 0.09)), G(F(10.3), (0, -0.095, 0.074)), 85, 16)
wp(11.2, G(F(11.2), (-0.03, -0.15, 0.085)), G(F(11.2), (0, -0.095, 0.074)), 90, 16)
wp(12.2, G(F(12.2), (-0.12, -0.08, 0.10)), G(F(12.2), (-0.02, -0.095, 0.085)), 85, 16)
wp(13.0, G(F(13.0), (-0.16, -0.08, 0.22)), G(F(13.0), CH), 60, 11)
wp(13.7, G(F(13.7), (-0.22, 0.06, 0.02)), G(F(13.7), (0, -0.01, 0.01)), 55, 11)
wp(14.4, G(F(14.4), (-0.22, -0.06, 0.05)), G(F(14.4), (0, -0.08, 0.034)), 60, 11)
wp(15.0, G(F(15.0), (-0.18, -0.2, 0.06)), G(F(15.0), (0, -0.2, 0.034)), 55, 8)
for t in (15.8, 16.7, 17.6, 18.4):
    ts, te, m0, mid, tgt = pel_paths[0]; u = (t - ts) / (te - ts)
    p = bez(m0, m0.lerp(mid, 0.66), mid.lerp(tgt, 0.33), tgt, u)
    wp(t, p + Vector((-0.07 + 0.03 * (t - 16), 0.10 - 0.01 * (t - 16), 0.035 + 0.015 * math.sin(t))), p + Vector((0, -0.08, 0)), 45, 5.6)
wp(18.85, FRAME_PHOTO + Vector((0, 0.18, 0)), FRAME_PHOTO + Vector((0, -1, 0)), 35, 2.0)
wp(19.05, OF(0.3, -2.4, 1.45), OF(0.3, 0.5, 1.3), 28, 2.0)
wp(19.4, OF(0.62, -1.15, 1.28), HEAD(M, F(19.4)), 32, 4.0)
wp(20.4, OF(0.95, -0.75, 1.36), HEAD(M, F(20.4)), 35, 4.0)
wp(21.4, OF(1.25, 0.35, 1.5), HEAD(M, F(21.4)), 32, 4.0)
wp(22.3, OF(0.85, 0.75, 1.3), HEAD(W, F(22.3)) + Vector((0, 0, 0.05)), 32, 4.0)
wp(23.2, OF(0.65, 0.45, 1.0), HEAD(W, F(23.2)) + Vector((0, 0, 0.02)), 35, 4.0)
wp(24.2, OF(0.3, 0.42, 1.0), HEAD(W, F(24.2)) + Vector((0, 0, 0.02)), 38, 4.0)
wp(25.1, OF(-0.15, 0.3, 1.15), HEAD(W, F(25.1)) + Vector((0, 0, 0.05)), 35, 4.0)
wp(25.9, OF(0.2, -0.95, 1.7), HEAD(W, F(25.9)) + Vector((0, 0, 0.3)), 32, 4.0)
wp(26.6, OF(0.3, -0.25, 1.85), HEAD(M, F(26.6)), 30, 4.0)
wp(27.4, OF(0.35, 0.35, 1.7), HEAD(M, F(27.4)), 30, 4.0)
wp(28.15, OF(0.35, 0.45, 1.72), HEAD(M, F(28.15)) + Vector((0, 0, 0.05)), 35, 2.0)
wp(28.45, Vector((0.05, -3.4, 1.45)), Vector((0, 0.2, 1.0)), 28, 2.0)
wp(28.8, Vector((0.9, -1.15, 1.45)), Vector((0.0, 0.1, BT + 0.1)), 30, 4.0)
wp(29.7, Vector((0.15, -0.95, 1.75)), Vector((-0.2, 0.1, BT + 0.1)), 30, 4.0)
wp(30.6, Vector((-1.05, -0.75, 1.3)), Vector((-0.3, 0.2, BT + 0.15)), 30, 4.0)
wp(31.3, Vector((-0.85, 0.15, 1.25)), Vector((0.0, 0.3, 1.05)), 30, 4.0)
wp(32.1, Vector((-0.38, 1.25, 1.62)), HEAD(M, F(32.1)) + Vector((0, 0, -0.25)), 30, 4.0)
wp(32.8, Vector((-0.12, 0.05, 1.32)), HEAD(M, F(32.8)) + Vector((0, 0, -0.35)), 35, 4.0)
wp(33.5, Vector((0.05, -1.05, 1.42)), HEAD(M, F(33.5)) + Vector((0, 0, -0.25)), 40, 4.0)
wp(34.3, Vector((0.85, -3.25, 1.75)), Vector((0.15, -1.0, 1.3)), 28, 4.0)
wp(35.0, Vector((1.05, -3.5, 1.95)), Vector((0.1, -0.8, 1.25)), 26, 4.0)
cpos = catmull([(w[0], w[1]) for w in WP]); ctgt = catmull([(w[0], w[2]) for w in WP])
clen = pchip([(w[0], w[3]) for w in WP]); cfs = pchip([(w[0], w[4]) for w in WP])
card = bpy.data.objects["ExplainerCard"]; card.parent = cam; card.location = (0, 0, -1); card.rotation_euler = (0, 0, 0)
con = node_val("M_ExplainerGradient", "CardOn")
for f, v in ((1, 0.0), (F(4.35), 0.0), (F(4.8), 1.0), (F(15.0), 1.0), (F(15.7), 0.0)):
    key_node(con, f, v)
for f in range(1, 2101):
    p = cpos(f); tg = ctgt(f)
    cam.location = p; cam.rotation_euler = (tg - p).to_track_quat('-Z', 'Y').to_euler()
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
    cam_d.lens = clen(f); cam_d.keyframe_insert("lens", frame=f)
    cam_d.dof.focus_distance = max(0.02, (tg - p).length); cam_d.dof.keyframe_insert("focus_distance", frame=f)
    cam_d.dof.aperture_fstop = cfs(f); cam_d.dof.keyframe_insert("aperture_fstop", frame=f)
    if F(4.2) <= f <= F(15.9):
        dgun = (gun_mat(f).translation - p).length + 0.13
        h = 2 * dgun * 18 / cam_d.lens * 1.25
        card.location = (0, 0, -dgun); card.scale = (h * 0.75, h, 1)
        card.keyframe_insert("location", frame=f); card.keyframe_insert("scale", frame=f)
for nm in ("WS_FrontWall", "OF_FrontWall", "WS_PhotoFrame"):
    o = bpy.data.objects[nm]; objs = [o] + list(o.children_recursive)
    for o2 in objs:
        key_hide(o2, [(1, False), (F(18.86), False), (F(18.88), True), (F(19.12), True), (F(19.14), False),
                      (F(28.28), False), (F(28.3), True), (F(28.6), True), (F(28.62), False)])
# exposure: white flashes for the memory in / out, office a touch brighter
vs = sc.view_settings
for t, e in ((0, 0.0), (18.62, 0.0), (18.92, 5.5), (19.05, 5.5), (19.35, -0.4), (28.05, -0.4), (28.32, 5.5), (28.45, 5.5), (28.8, 0.0)):
    vs.exposure = e; vs.keyframe_insert("exposure", frame=F(t))
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("FILM SAVED", OUT)
