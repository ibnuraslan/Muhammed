"""Character animation, FX, lights and the continuous camera.
blender -b scene.blend --python 03_animate.py -- <out.blend>"""
import sys, os, math
import bpy
from mathutils import Vector, Matrix, Quaternion
HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "/home/user/Muhammed/blender/SpeakWithoutSight_v001/scripts"
OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else None
exec(open(os.path.join(HERE, "03_anim_lib.py")).read())
sc = bpy.context.scene
STOOL = Vector(sc["stool"]); CHAIR = Vector(sc["chair_xy"])
def ground_z(x, y):
    if abs(x - STOOL.x) < 0.2 and abs(y - STOOL.y) < 0.14: return STOOL.z
    return 0.0
V = lambda *a: Vector(a)

class Person:
    def __init__(self, name):
        self.o = bpy.data.objects[name]; self.name = name
        self.r = make_human_ctrl(self.o); self.h = Human(self.r); B = self.r.BN
        self.root_head = B["root"].head_local.copy()
        self.SH = {s: B["upperarm01." + s].head_local.copy() for s in "LR"}
        self.rest_hand = {}
        for s in "LR":
            wv = B["wrist." + s].head_local; d = B["finger3-1." + s].head_local - wv
            a = B["finger2-1." + s].head_local - B["finger5-1." + s].head_local
            n = d.cross(a) if s == "L" else a.cross(d)
            self.rest_hand[s] = self.basis(s, d, n)
        for pb in self.o.pose.bones: pb.rotation_mode = 'QUATERNION'
    @staticmethod
    def basis(s, d, n):
        d = d.normalized(); n = (n - d * n.dot(d)).normalized()
        a = d.cross(n) if s == "R" else n.cross(d)
        return Matrix((d, a, n)).transposed()
    def M(self, yaw, v):
        """character-relative vector (x right of the -Y facing rest, y back, z up) to world"""
        return Matrix.Rotation(R_(yaw), 3, 'Z') @ v
    def root(self, f, pos, yaw=0.0, flex=0.0, side=0.0):
        self.h.key_root(f, Vector(pos), yaw=yaw, flex=flex, side=side)
    def spine(self, f, flex=0.0, twist=0.0, side=0.0, head=(0.0, 0.0)):
        self.h.key_spine(f, flex=flex, twist=twist, side=side, head=head)
    def foot(self, s, f, xy, yaw, lift=0.0, pitch=0.0):
        self.h.key_foot(s, f, Vector(xy), yaw, lift, pitch)
    def hand(self, s, f, W, d, n, pole=None):
        """W wrist (world), d wrist->middle knuckle direction, n back-of-hand normal (world)"""
        Rm = self.basis(s, Vector(d), -Vector(n)) @ self.rest_hand[s].transposed()   # basis takes the palm normal
        wr = self.r.BN["wrist." + s].head_local
        self.r.key_world("IK_hand." + s, f, Matrix.Translation(Vector(W)) @ Rm.to_4x4() @ Matrix.Translation(-wr) @ self.r.rest("IK_hand." + s))
        if pole is not None:
            nm = "Pole_elbow." + s; pb = self.r.PB[nm]
            pb.location = self.r.rest(nm).to_3x3().inverted() @ (Vector(pole) - self.r.BN[nm].head_local)
            pb.keyframe_insert("location", frame=f, group=nm)
    def fingers(self, s, f, curl, thumb=18, spread=0.0):
        Rh = self.rest_hand[s]; d, a = Rh.col[0], Rh.col[1]; sign = 1 if s == "R" else -1
        JW = (0.8, 1.1, 0.8)
        for k in range(2, 6):
            c = curl[k - 2] if isinstance(curl, (list, tuple)) else curl
            sp = spread * (k - 3.5)
            for j in range(1, 4):
                b = "finger%d-%d.%s" % (k, j, s)
                q = Matrix.Rotation(R_(c * JW[j - 1] * sign), 3, a)
                if j == 1: q = Matrix.Rotation(R_(sp * sign), 3, Rh.col[2]) @ q
                self.r.key_q(b, f, self.r.local_q(b, q))
        for j, fl in ((1, thumb * 0.4), (2, thumb * 0.8), (3, thumb)):
            b = "finger1-%d.%s" % (j, s)
            self.r.key_q(b, f, self.r.local_q(b, Matrix.Rotation(R_(fl * sign), 3, a) @ Matrix.Rotation(R_(22 * sign), 3, d)))
    def bone_world(self, n, f=None, tail=False):
        if f is not None: ev(f)
        pb = self.o.pose.bones[n]; return self.o.matrix_world @ (pb.tail if tail else pb.head)
    def bone_mat(self, n, f=None):
        if f is not None: ev(f)
        return self.o.matrix_world @ self.o.pose.bones[n].matrix


    def hem(self, f, xy, yaw, scale=1.0, dz=0.0):
        if "SkirtHem" not in self.r.PB: return
        rb = self.r.rest("SkirtHem"); h0 = rb.translation
        M = Matrix.Translation(Vector((xy[0], xy[1], dz))) @ Matrix.Rotation(R_(yaw), 4, 'Z') @ Matrix.Translation(-h0) @ rb
        self.r.key_world("SkirtHem", f, M)
        pb = self.r.PB["SkirtHem"]; pb.scale = (scale, scale, 1.0); pb.keyframe_insert("scale", frame=f, group="SkirtHem")
    def shift(self, b, f, dv):
        pb = self.r.PB[b]; pb.location = self.r.rest(b).to_3x3().inverted() @ Vector(dv)
        pb.keyframe_insert("location", frame=f, group=b)
    def face(self, f, jaw=0.0, oo=0.0, ee=0.0, mm=0.0, smile=0.0, brow=0.0, eyes=(0.0, 0.0), blink=0.0):
        """mouth shapes for the MPFB default face bones (weights 0..1); eyes = (yaw, pitch) deg"""
        self.r.key_rot("jaw", f, [("X", jaw)])
        for s, sx in (("L", 1), ("R", -1)):
            cx = sx * (-0.006 * oo + 0.007 * ee + 0.006 * smile)
            cz = 0.002 * ee + 0.004 * smile
            cy_ = -0.006 * oo
            self.shift("oris07." + s, f, (cx, cy_, cz + 0.002 * mm)); self.shift("oris03." + s, f, (cx, cy_, cz - 0.002 * mm))
            self.shift("risorius03." + s, f, (sx * 0.004 * (ee + smile), 0, 0.004 * smile))
            self.shift("oculi01." + s, f, (0, 0, 0.004 * brow))
            self.r.key_rot("eye." + s, f, [("Z", eyes[0]), ("X", -eyes[1])])
            self.r.key_rot("orbicularis03." + s, f, [("X", 25 * blink)])
        self.shift("oris01", f, (0, -0.005 * oo, 0.003 * mm)); self.shift("oris02", f, (0, -0.003 * oo, 0.002 * mm))
        self.shift("oris05", f, (0, -0.005 * oo, -0.002 * mm)); self.shift("oris06", f, (0, -0.003 * oo, -0.001 * mm))
    def throat_point(self, f, F, up=0.0):
        """front of the neck below the chin: horizontal rays at several neck heights, rejecting hits far from the neck axis (the chin)"""
        ev(f)
        n1, n2 = self.bone_world("neck01"), self.bone_world("neck02")
        body = bpy.data.objects[self.name + ".body"]; dg = bpy.context.evaluated_depsgraph_get()
        eo = body.evaluated_get(dg); mi = eo.matrix_world.inverted()
        Fh = (F - Vector((0, 0, F.z))).normalized()
        best = None
        for t in (0.55, 0.45, 0.65, 0.35, 0.75, 0.25):
            nk = n1.lerp(n2, t) + Vector((0, 0, up))
            o_ = nk + Fh * 0.25
            hit, loc, nrm, idx = eo.ray_cast(mi @ o_, (mi.to_3x3() @ (-Fh)).normalized())
            if not hit: continue
            w = eo.matrix_world @ loc
            ax = (n2 - n1).normalized(); r = ((w - n1) - ax * (w - n1).dot(ax)).length
            if r < 0.075: return w
            if best is None or r < best[0]: best = (r, w)
        return best[1] if best else n1.lerp(n2, 0.5) + Fh * 0.05
    def surface(self, f, origin, direction, part="body"):
        ev(f)
        body = bpy.data.objects[self.name + "." + part]; dg = bpy.context.evaluated_depsgraph_get()
        eo = body.evaluated_get(dg); mi = eo.matrix_world.inverted()
        hit, loc, nrm, idx = eo.ray_cast(mi @ origin, (mi.to_3x3() @ direction).normalized())
        return ((eo.matrix_world @ loc), (eo.matrix_world.to_3x3() @ nrm).normalized()) if hit else (None, None)
    def hand_len(self, s):
        B = self.r.BN; return (B["finger3-3." + s].tail_local - B["wrist." + s].head_local).length

def fdir(yaw):
    return Vector((math.sin(R_(yaw)), -math.cos(R_(yaw)), 0))
def rdir(yaw):
    return Vector((-math.cos(R_(yaw)), -math.sin(R_(yaw)), 0))
UP = Vector((0, 0, 1))
GIRL, TEACH, MOM, DAD = Person("Girl"), Person("Teacher"), Person("Mother"), Person("Father")
BEATS = [1, 163, 397, 595, 697, 895, 1063, 1261, 1453, 1723, 1843]; END = 1980
sc.frame_start, sc.frame_end = 1, END
def keys_every(f0, f1, step):
    return list(range(f0, f1, step)) + [f1]
def wave(f, period, amp, ph=0.0):
    return amp * math.sin(2 * math.pi * (f / period + ph))

# ================================================================== GIRL (seated in the armchair, feet on the footstool)
G = GIRL; G_HIP = V(CHAIR.x, CHAIR.y - 0.04, 0.575); G_YAW = 0.0
for s, sx in (("L", 1), ("R", -1)):
    for f in (1, END):
        G.foot(s, f, (CHAIR.x + sx * 0.075, STOOL.y + 0.05), sx * 6)
def g_posture(f):
    """hunched and closed (beats 1-9) -> upright and open (beats 10-11)"""
    u = smooth((f - 1723) / 140.0)
    lean_to_teacher = smooth((f - 470) / 80.0) * (1 - 0.5 * smooth((f - 1723) / 120))
    flex = 14 * (1 - u) + 3 * u + wave(f, 240, 1.2) + 10 * lean_to_teacher
    twist = -16 * lean_to_teacher
    head_p = 12 * (1 - u) - 4 * u
    head_y = -18 * lean_to_teacher
    return flex, twist, head_p, head_y
for f in keys_every(1, END, 10):
    fl, tw, hp, hy = g_posture(f)
    G.root(f, G_HIP + V(0, -0.05 * smooth((f - 460) / 60.0) * (1 - smooth((f - 1900) / 60.0)), 0), G_YAW, flex=-8 + fl * 0.3)
    G.spine(f, flex=fl, twist=tw, head=(hp, hy))
# eyes unfocused: slightly divergent, slow drift, never tracking (until the last beat where they still don't track but she smiles)
for f in keys_every(1, END, 40):
    G.face(f, eyes=(wave(f, 900, 7) + 4, wave(f, 700, 4) - 6), blink=1.0 if (f % 520) == 0 else 0.0)
# lap hands (beats 1-2): fingers rubbing, "only touch"
def lap(s, f):
    sx = 1 if s == "L" else -1
    return V(CHAIR.x + sx * 0.085, CHAIR.y - 0.22, 0.655), V(-sx * 0.35, -1, -0.2), V(0, 0.1, 1), V(CHAIR.x + sx * 0.4, CHAIR.y + 0.2, 0.75)
for f in keys_every(1, 450, 20):
    for s in "LR":
        W, d, n, pole = lap(s, f)
        if f > 163 and s == "R":
            W = W + V(0.03 * math.sin(f / 23.0), 0.015 * math.cos(f / 31.0), 0.01)   # right hand strokes the back of the left
        G.hand(s, f, W, d, n, pole); G.fingers(s, f, 25 + 15 * math.sin(f / 17.0 + (s == "L")), 12)

# ================================================================== TEACHER
T = TEACH
T_YAW = 141.0; T_F, T_R = fdir(T_YAW), rdir(T_YAW)
T_KNEEL = V(-0.24, 0.09, 0.50) - fdir(141.0) * 0.15
def t_kneel_keys(f, root, yaw, flex=12.0, twist=0.0, head=(0.0, 0.0), sit=0.0):
    F_, R__ = fdir(yaw), rdir(yaw)
    T.root(f, root - V(0, 0, sit), yaw, flex=flex * 0.3)
    T.spine(f, flex=flex, twist=twist, head=head)
    T.hem(f, (root - F_ * 0.12).to_2d(), yaw, scale=1.25)
def t_kneel_feet(f, root, yaw):
    F_, R__ = fdir(yaw), rdir(yaw)
    for s, sx in (("L", -1), ("R", 1)):
        a = root - F_ * 0.43 + R__ * sx * 0.12
        T.foot(s, f, (a.x, a.y), yaw, lift=0.055, pitch=-72)
# walk in from the hall (260-392)
WALK_END = V(-0.62, -0.32, 0)
pts = [(250, V(-3.8, -1.3, 0)), (300, V(-3.0, -1.22, 0)), (350, V(-1.75, -0.85, 0)), (392, WALK_END)]
tpath = catmull(pts)
tyaw = lambda f: 90 + 25 * smooth((f - 300) / 92.0)
for f in (1, 250):
    p = tpath(250); T.root(f, V(p.x, p.y, T.root_head.z - 0.01), 90); T.spine(f, 0, 0, 0, (0, 0)); T.hem(f, (p.x, p.y), 90)
    for s in "LR": T.foot(s, f, T.h.foot_xy(s, p, 90), 90)
T.h.walk(tpath, tyaw, 250, 392, stride=0.62, lift=0.07, lean=5)
for f in keys_every(250, 392, 2):
    p = tpath(f); T.hem(f, (p.x, p.y), tyaw(f))
# kneel down: right foot steps back (392-410), right knee down (410-425), left knee down (425-440)
ev(392)
for f, root, yaw in ((392, V(WALK_END.x, WALK_END.y, T.root_head.z - 0.03), 115), (412, V(-0.45, -0.15, 0.78), 130), (428, V(-0.3, 0.02, 0.6), 138), (442, T_KNEEL, T_YAW)):
    T.root(f, root, yaw, flex=4); T.spine(f, flex=14, head=(6, 0)); T.hem(f, (root - fdir(yaw) * 0.08 * smooth((f - 392) / 50)).to_2d(), yaw, scale=1.0 + 0.25 * smooth((f - 392) / 50))
F0 = {s: T.h.foot_xy(s, WALK_END, 115) for s in "LR"}
T.foot("L", 400, F0["L"], 115); T.foot("R", 392, F0["R"], 115)
rb = T_KNEEL - T_F * 0.43
T.foot("R", 404, ((F0["R"] + (rb + T_R * 0.12).to_2d()) / 2), 128, lift=0.10, pitch=-30)
T.foot("R", 414, (rb + T_R * 0.12).to_2d(), T_YAW, lift=0.055, pitch=-72)
T.foot("L", 418, F0["L"], 115); T.foot("L", 428, ((F0["L"] + (rb - T_R * 0.12).to_2d()) / 2), 128, lift=0.10, pitch=-30)
T.foot("L", 440, (rb - T_R * 0.12).to_2d(), T_YAW, lift=0.055, pitch=-72)
t_kneel_feet(END, T_KNEEL, T_YAW)
# kneeling body over the rest of the film (posture keyed sparsely; speech adds small head moves)
T_BODY = [(442, 14, 0, (6, 0)), (600, 17, 0, (2, 0)), (895, 15, 0, (-6, 0)), (980, 17, 0, (4, 0)), (1063, 16, -6, (2, -6)),
          (1261, 16, 0, (0, 0)), (1453, 12, 8, (6, 10)), (1600, 14, 8, (8, 12)), (1723, 10, 0, (0, 0)), (1843, 8, 0, (-2, 0))]
for f, fl, tw, hd in T_BODY:
    t_kneel_keys(f, T_KNEEL, T_YAW, fl, tw, (hd[0] - 22, hd[1]))   # chin up: keeps the throat clear of the jaw
# arms at walk: swing (walk() does not key arms)
for f in keys_every(250, 392, 12):
    ph = math.sin((f - 250) / 15.0)
    for s, sx in (("L", -1), ("R", 1)):
        ev(f); sh = T.bone_world("upperarm01." + s); yw = tyaw(f); F_, R__ = fdir(yw), rdir(yw)
        W = sh + R__ * sx * 0.04 - UP * 0.44 + F_ * 0.08 * ph * (1 if s == "L" else -1)
        T.hand(s, f, W, -UP + F_ * 0.15, R__ * sx, sh + R__ * sx * 0.3 - F_ * 0.3)
        T.fingers(s, f, 20, 15)
for f in (1, 249):
    for s, sx in (("L", -1), ("R", 1)):
        ev(250); sh = T.bone_world("upperarm01." + s)
        T.hand(s, f, sh + rdir(90) * sx * 0.04 - UP * 0.44, -UP, rdir(90) * sx, sh + rdir(90) * sx * 0.3 - fdir(90) * 0.3); T.fingers(s, f, 20, 15)

# ---------------------------------------------- contact helpers
def t_throat(f, up=0.0):
    return T.throat_point(f, fdir(T_YAW), up)
def t_mouth(f):
    ev(f); hm = T.bone_mat("head"); hd = T.bone_world("head")
    fwd = (hm.to_3x3() @ V(0, 1, 0)).normalized()   # head bone y axis points up the head; mouth faces the head's -Y in rest
    m_rest = T.r.BN["oris06"].head_local; head_rest = T.r.BN["head"].head_local
    p = T.o.matrix_world @ (T.o.pose.bones["head"].matrix @ (T.r.BN["head"].matrix_local.inverted() @ m_rest))
    face_fwd = (T.o.pose.bones["head"].matrix.to_3x3() @ (T.r.BN["head"].matrix_local.to_3x3().inverted() @ V(0, -1, 0))).normalized()
    hit, nrm = T.surface(f, p + face_fwd * 0.12, -face_fwd)
    return (hit if hit else p), face_fwd
G_HL = G.hand_len("R")
def g_throat_along(f, tp):
    """fingers lie on the throat pointing away from the girl's shoulder, so the wrist stays on her side (shortest reach)"""
    ev(f); sh = G.bone_world("upperarm01.R"); F_ = fdir(T_YAW)
    lat = (tp - sh); lat = lat - F_ * lat.dot(F_)
    return (lat.normalized() + UP * 0.35).normalized()
def g_hand_on(s, f, tip, normal, along, press=0.0, curl=6, pad=0.005):
    """middle fingertip pad at 'tip' (world), palm towards -normal, fingers pointing 'along'; two correction passes"""
    along = (along - normal * along.dot(normal)).normalized()
    goal = tip + normal * (pad - press)
    W = goal - along * (G_HL * 0.95)
    sh = G.bone_world("upperarm01." + s, f)
    pole = sh + (W - sh) * 0.5 + V(0, 0.25, -0.35) + (V(-0.3, 0, 0) if s == "R" else V(0.3, 0, 0))
    for it in range(3):
        G.hand(s, f, W, along, normal, pole); G.fingers(s, f, curl, 10, spread=1)
        if it == 2: break
        ev(f); err = goal - G.bone_world("finger3-3." + s, tail=True)
        if err.length < 1e-3: break
        Wn = W + err
        reach = (G.r.BN["wrist." + s].head_local - G.r.BN["upperarm01." + s].head_local).length * 0.985
        if (Wn - sh).length > reach: Wn = sh + (Wn - sh).normalized() * reach   # never ask the IK for more than the arm
        W = Wn
# ---------------------------------------------- beat 3: teacher takes the girl's right wrist and places the hand on her throat
def g_lap_R(f):
    W, d, n, pole = lap("R", f); return W, d, n, pole
for f in (450, 462):
    W, d, n, pole = g_lap_R(f); G.hand("R", f, W, d, n, pole); G.fingers("R", f, 25, 12)
ev(455)
T_HL = T.hand_len("R")
def t_grip_wrist(f, W, d, n):
    """teacher's right hand wraps the girl's right wrist from above"""
    top = W + n * 0.045 + d * 0.02
    T.hand("R", f, top + n * 0.03 - T_F * 0.02, (-n + d * 0.3), (T_F * -1 + UP * 0.5), T_KNEEL + T_R * 0.45 + UP * 0.45)
    T.fingers("R", f, 55, 35)
# reach
ev(442); sh = T.bone_world("upperarm01.R")
for f in (442,):
    T.hand("R", f, sh + T_R * 0.06 - UP * 0.42 + T_F * 0.1, -UP + T_F * 0.3, T_R, sh + T_R * 0.3 - T_F * 0.2); T.fingers("R", f, 20, 15)
W, d, n, _ = g_lap_R(455); t_grip_wrist(455, W, d, n); t_grip_wrist(462, W, d, n)
# travel: girl's hand rises to the throat (462-530)
throat_keys = list(range(530, 1063, 6)) + [1062]
for f in (480, 500, 516):
    u = smooth((f - 462) / 68.0)
    tp = t_throat(f); W0, d0, n0, _ = g_lap_R(f)
    tipT = tp + fdir(T_YAW) * 0.03
    tip = (W0 + d0.normalized() * G_HL).lerp(tipT, u) + V(0, 0, 0.06 * math.sin(math.pi * u))
    nrm = n0.lerp(-fdir(T_YAW) * -1, u).normalized()
    g_hand_on("R", f, tip, nrm, d0.lerp(UP * 0.6 + T_R * -0.8, u), curl=20 - 14 * u)
    ev(f); Wg = G.bone_world("wrist.R"); t_grip_wrist(f, Wg, d0.lerp(UP, u), nrm)
for f in throat_keys:
    # beat 6: press harder when loud, relax when soft
    press = 0.004 if 895 <= f < 990 else (0.0 if f >= 990 else 0.002)
    tp = t_throat(f)
    g_hand_on("R", f, tp, fdir(T_YAW), g_throat_along(f, tp), press=press, curl=8 if press < 0.004 else 14)
# teacher's right hand lets go and rests on the girl's forearm, then gestures softly
def t_thigh_R(f, lift=0.0):
    ev(f); kn = T.bone_world("lowerleg01.R"); hp = T.bone_world("upperleg01.R")
    p = hp.lerp(kn, 0.55) + V(0, 0, 0.07 + lift) + T_F * 0.02
    T.hand("R", f, p, T_F * 0.8 - UP * 0.3 - T_R * 0.2, UP + T_F * 0.1, p + T_R * 0.35 + UP * 0.25)
    T.fingers("R", f, 28, 18)
for f in (548, 600, 700, 820, 900, 1000, 1040):
    t_thigh_R(f)
# teacher's left hand: on her own thigh, then on the girl's knee
for f, where in ((442, "thigh"), (700, "thigh"), (1063, "thigh"), (1453, "knee"), (1700, "knee"), (1843, "knee")):
    ev(f)
    if where == "thigh":
        p = T_KNEEL + T_F * 0.12 - T_R * 0.12 + V(0, 0, 0.06)
        T.hand("L", f, p, T_F + UP * -0.5, UP + T_F * 0.2, p - T_R * 0.35 + UP * 0.2)
    else:
        kn = G.bone_world("lowerleg01.L")
        T.hand("L", f, kn + V(0, 0, 0.07) - T_F * 0.05, T_F * 0.5 + UP * -0.6 + T_R * 0.3, UP, T_KNEEL - T_R * 0.45 + UP * 0.3)
    T.fingers("L", f, 22, 15)
# ---------------------------------------------- beat 7-9: the girl's hand on the teacher's lips and nose
def lip_key(f, dx=0.0, dz=0.0, press=0.0):
    mp, ff = t_mouth(f)
    side = ff.cross(UP).normalized()
    g_hand_on("R", f, mp + side * dx + UP * dz + ff * 0.002, ff, side * -1 - UP * 0.35, press=press, curl=8)
LIP_KEYS = [(1063, None, None), (1085, None, None)]
for f in range(1110, 1723, 6):
    nose = math.exp(-((f - 1215) / 18.0) ** 2)          # fingertips slide up to the nose and back
    LIP_KEYS.append((f, 0.009 * math.sin((f - 1110) / 23.0) * (1 - nose), 0.026 * nose))
for f, dx, dz in LIP_KEYS:
    if dx is None:
        u = smooth((f - 1063) / 47.0); tp = t_throat(f); mp, ff = t_mouth(f)
        tip = tp.lerp(mp + ff * 0.02, u) + ff * 0.04 * math.sin(math.pi * u)
        g_hand_on("R", f, tip, fdir(T_YAW).lerp(ff, u).normalized(), (UP * 0.55 + rdir(T_YAW) * 0.85).lerp(-ff.cross(UP) + UP * 0.25, u), curl=12)
        ev(f); Wg = G.bone_world("wrist.R"); t_grip_wrist(f, Wg, (UP).normalized(), fdir(T_YAW))
    else:
        lip_key(f, dx, dz)
# teacher's right hand releases after guiding (1110) and rests on the girl's forearm again
for f in (1128, 1300, 1453, 1600, 1722, 1850):
    t_thigh_R(f)
# girl's left hand: lap (to 1470), own lips (1490-1600), own throat (1615-1722)
def g_own_mouth(f):
    ev(f); hm = G.o.pose.bones["head"]
    p = G.o.matrix_world @ (hm.matrix @ (G.r.BN["head"].matrix_local.inverted() @ G.r.BN["oris06"].head_local))
    ff = (hm.matrix.to_3x3() @ (G.r.BN["head"].matrix_local.to_3x3().inverted() @ V(0, -1, 0))).normalized()
    hit, nrm = G.surface(f, p + ff * 0.12, -ff)
    return (hit if hit else p), ff
def g_own_throat(f):
    ev(f); hm = G.o.pose.bones["neck02"]
    ff = (G.o.pose.bones["head"].matrix.to_3x3() @ (G.r.BN["head"].matrix_local.to_3x3().inverted() @ V(0, -1, 0))).normalized()
    ff = (ff - UP * ff.dot(UP)).normalized()
    return G.throat_point(f, ff), ff
for f in keys_every(450, 1470, 60):
    W, d, n, pole = lap("L", f); G.hand("L", f, W, d, n, pole); G.fingers("L", f, 25, 12)
def g_left_on(f, what, dz=0.0):
    p, ff = g_own_mouth(f) if what == "lips" else g_own_throat(f)
    side = ff.cross(UP).normalized()   # points to her left
    along = (-side + UP * (0.2 if what == "lips" else 0.5)).normalized()
    g_hand_on("L", f, p + UP * dz, ff, along, curl=10)
for f in range(1490, 1601, 10):
    g_left_on(f, "lips")
for f in range(1615, 1723, 10):
    g_left_on(f, "throat")
# ---------------------------------------------- beat 10: time-lapse practice bursts (hands alternate fast)
for i, f in enumerate(range(1735, 1843, 18)):
    g_left_on(f, "lips" if i % 2 == 0 else "throat")
    if i % 2 == 0: lip_key(f)
    else:
        tp = t_throat(f); g_hand_on("R", f, tp, fdir(T_YAW), g_throat_along(f, tp), curl=8)
# ---------------------------------------------- beat 11: she speaks (left hand on her own throat), teacher gasps then hugs
for f in range(1843, END + 1, 8):
    g_left_on(f, "throat")
for f in (1843, 1858):
    lip_key(f)
# girl's right hand comes down to the teacher's shoulder for the hug
for f in (1880, 1915, 1950, END):
    ev(f); shT = T.bone_world("upperarm01.L") + UP * 0.05
    g_hand_on("R", f, shT + T_F * -0.02, UP, T_R * -1 + T_F * -0.3, curl=18)
# teacher gasp: both hands to her mouth (no contact), 1866-1905
for f in (1866, 1885, 1905):
    mp, ff = t_mouth(f); side = ff.cross(UP).normalized()
    for s, sx in (("L", 1), ("R", -1)):
        tip = mp + ff * 0.045 + side * sx * 0.03 + UP * 0.01
        along = (UP * 0.8 + side * -sx * 0.3).normalized()
        T.hand(s, f, tip - along * T_HL * 0.95 + ff * 0.01, along, ff, T_KNEEL + T_R * -sx * 0.4 + UP * 0.2)
        T.fingers(s, f, 15, 15)
# hug (1925-END): teacher rises to a high kneel and wraps both arms round the girl's shoulders
T_HUG = T_KNEEL + T_F * 0.03 + V(0, 0, 0.1)
t_kneel_keys(1905, T_KNEEL, T_YAW, 8, 0, (-6, 0)); t_kneel_keys(1930, T_HUG, T_YAW, 22, 0, (10, -12)); t_kneel_keys(END, T_HUG + V(0, 0, -0.01), T_YAW, 23, 0, (11, -12))
for f in (1930, 1955, END):
    ev(f)
    back = G.bone_world("spine02") + V(0, 0, 0.06)
    for s, sx, side_pt in (("L", 1, "upperarm01.L"), ("R", -1, "upperarm01.R")):
        sp = G.bone_world(side_pt)
        hit, nrm = G.surface(f, sp + V(0, 0.35, 0.02), V(0, -1, 0), "female_elegantsuit01")
        p = (hit if hit else sp + V(0, 0.12, 0))
        d = V(sx * -0.6, -0.2, -0.6) if s == "L" else V(0.5, -0.3, -0.6)
        T.hand(s, f, p + V(0, 0.03, 0.04) - d.normalized() * 0.07, d, V(0, 1, 0.2), T_HUG + T_R * -sx * 0.5 + UP * 0.4)
        T.fingers(s, f, 30, 20)
# girl leans in to the hug
for f in (1930, END):
    fl, tw, hp, hy = g_posture(f); G.spine(f, flex=fl + 3, twist=-22, head=(hp + 4, -28))

# ---------------------------------------------- speech (teacher), mouth shapes
def mouth(P, f, shape, k=1.0):
    S = {"rest": {}, "AH": dict(jaw=13), "O": dict(jaw=8, oo=1.0), "E": dict(jaw=4, ee=1.0), "M": dict(jaw=0.5, mm=1.0),
         "OO": dict(jaw=5, oo=1.3), "BIG": dict(jaw=18, oo=0.3, brow=1.0), "GASP": dict(jaw=16, oo=0.6, brow=1.0), "SMILE": dict(jaw=2, smile=1.0)}[shape]
    P.face(f, **{a: b * k for a, b in S.items()})
seq = ["AH", "O", "E", "M", "AH", "E", "OO", "rest"]
for i, f in enumerate(range(600, 895, 14)):
    mouth(T, f, seq[i % len(seq)], 0.8)
for i, f in enumerate(range(895, 985, 12)):
    mouth(T, f, ["BIG", "AH", "BIG", "O"][i % 4], 1.0)
for i, f in enumerate(range(985, 1063, 16)):
    mouth(T, f, ["M", "OO", "E", "rest"][i % 4], 0.45)
for f in (1063, 1240):
    mouth(T, f, "rest")
for i, f in enumerate(range(1261, 1453, 32)):
    mouth(T, f, ["O", "O", "E", "E", "M", "M"][i % 6], 1.0) if False else None
OEM = []
for i, f in enumerate(range(1261, 1453, 36)):
    shp = ["O", "E", "M"][i % 3]; OEM.append((f, shp)); mouth(T, f, shp, 1.1); mouth(T, f + 26, shp, 1.0)
for i, f in enumerate(range(1453, 1723, 40)):
    mouth(T, f, ["O", "E", "M"][i % 3], 0.9); mouth(T, f + 25, "rest")
for i, f in enumerate(range(1723, 1843, 12)):
    mouth(T, f, ["O", "E", "M", "AH"][i % 4], 0.8)
mouth(T, 1843, "rest"); mouth(T, 1860, "SMILE", 0.5); mouth(T, 1872, "GASP"); mouth(T, 1900, "GASP", 0.8); mouth(T, 1925, "SMILE", 1.0); mouth(T, END, "SMILE", 1.0)
# girl mimics a little late and clumsy (beat 9), practice (10), first word (11)
for i, f in enumerate(range(1475, 1723, 40)):
    G.face(f, **{"O": dict(jaw=6, oo=0.7), "E": dict(jaw=3, ee=0.6), "M": dict(jaw=1, mm=0.8)}[["O", "E", "M"][i % 3]], eyes=(5, -6))
    G.face(f + 24, jaw=2, eyes=(5, -6))
for i, f in enumerate(range(1723, 1843, 12)):
    G.face(f, **{"O": dict(jaw=7, oo=0.9), "E": dict(jaw=4, ee=0.9), "M": dict(jaw=1, mm=1.0), "AH": dict(jaw=11)}[["O", "E", "M", "AH"][i % 4]], eyes=(5, -4))
G.face(1846, jaw=1, eyes=(5, -4)); G.face(1858, jaw=12, oo=0.3, eyes=(5, -2), brow=0.6); G.face(1880, jaw=9, oo=0.6, eyes=(5, -2), brow=0.8)
G.face(1898, jaw=2, smile=0.4, eyes=(5, -2), brow=0.5); G.face(1930, jaw=1, smile=1.0, eyes=(4, -2)); G.face(END, jaw=1, smile=1.0, eyes=(4, -2))
# girl's face reacts to the loud/soft pulses (beat 6)
G.face(890, eyes=(6, -6)); G.face(915, jaw=3, brow=1.0, eyes=(6, -2)); G.face(975, jaw=2, brow=0.9, eyes=(6, -2)); G.face(1010, jaw=1, brow=0.2, smile=0.3, eyes=(6, -6))
G.face(1060, eyes=(6, -6))
print("GIRL_TEACHER_DONE")

# ================================================================== MOTHER (sofa, embroidery), FATHER (reading by the table), DOG
Mo = MOM; MO_YAW = 90.0; MO_F, MO_R = fdir(MO_YAW), rdir(MO_YAW)
MO_HIP = V(-2.28, 0.72, 0.47)
def mk(name, mesh_fn, mat):
    import bmesh
    me = bpy.data.meshes.new(name); bm = bmesh.new(); mesh_fn(bm); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.data.collections["PROPS"].objects.link(o); me.materials.append(mat); return o
def matc(name, rgb, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough; p.inputs["Metallic"].default_value = metal; return m
import bmesh
hoop = mk("EmbroideryHoop", lambda bm: bmesh.ops.create_circle(bm, cap_ends=True, radius=0.11, segments=40), matc("M_Linen", (0.85, 0.82, 0.74), 0.9))
ring = mk("EmbroideryRing", lambda bm: bmesh.ops.create_circle(bm, cap_ends=False, radius=0.112, segments=40), matc("M_HoopWood", (0.45, 0.3, 0.16), 0.5))
ring.modifiers.new("Sk", 'SKIN') if False else None
sw_ = ring.modifiers.new("Solid", 'SOLIDIFY'); sw_.thickness = 0.012
ring.parent = hoop
hoop.modifiers.new("Solid", 'SOLIDIFY').thickness = 0.002
for s, sx in (("L", -1), ("R", 1)):
    for f in (1, END):
        a = MO_HIP + MO_F * 0.47 + MO_R * sx * 0.11
        Mo.foot(s, f, (a.x, a.y), MO_YAW)
LAP = MO_HIP + MO_F * 0.3 + V(0, 0, 0.13)
def mo_stand(f):
    return smooth((f - 1885) / 50.0)
for f in keys_every(1, END, 12):
    u = mo_stand(f)
    hip = MO_HIP.lerp(MO_HIP + MO_F * 0.38 + V(0, 0, Mo.root_head.z - 0.04 - MO_HIP.z), u)
    look_up = smooth((f - 55) / 15) * (1 - smooth((f - 150) / 20))
    laugh = look_up * 4 * math.sin(f / 2.2)
    Mo.root(f, hip, MO_YAW, flex=-6 * (1 - u)); Mo.spine(f, flex=(18 - 14 * look_up) * (1 - u) + 5 * u + laugh * 0.4, twist=8 * look_up,
                                                       head=((22 - 30 * look_up) * (1 - u) + (-2) * u, 30 * look_up + 35 * u))
    Mo.hem(f, (MO_HIP + MO_F * (0.28 - 0.1 * u)).to_2d(), MO_YAW, scale=1.2 - 0.15 * u)
    # stitching: left hand holds the hoop, right hand pulls the thread up and pushes it back down
    if u < 0.5:
        ph = (f % 72) / 72.0; up_ = math.sin(math.pi * min(1, ph * 1.6)) if ph < 0.62 else 0.0
        Mo.hand("L", f, LAP + MO_R * 0.09 + V(0, 0, 0.02), MO_F * 0.6 - MO_R * 0.6, UP, LAP + MO_R * 0.4 - MO_F * 0.2 + UP * 0.1); Mo.fingers("L", f, 45, 30)
        Mo.hand("R", f, LAP - MO_R * 0.06 + MO_F * 0.03 + V(0, 0, 0.06 + 0.16 * up_), MO_F * 0.4 + MO_R * 0.4 - UP * 0.3, UP + MO_F * 0.3, LAP - MO_R * 0.4 - MO_F * 0.2)
        Mo.fingers("R", f, [40, 55, 65, 70], 30)
    else:
        ev(f); ch = Mo.bone_world("spine02") + MO_F * 0.17 + V(0, 0, 0.05)
        Mo.hand("L", f, ch + MO_R * 0.05, -MO_R + UP * 0.3, MO_F, ch + MO_R * 0.4 - MO_F * 0.2); Mo.fingers("L", f, 30, 20)
        Mo.hand("R", f, ch - MO_R * 0.07 - UP * 0.08, MO_R + UP * 0.2, MO_F, ch - MO_R * 0.4 - MO_F * 0.2); Mo.fingers("R", f, 30, 20)
c = hoop.constraints.new('CHILD_OF'); c.target = Mo.o; c.subtarget = "wrist.L"
ev(1); hoop.matrix_world = Matrix.Translation(LAP + MO_F * 0.02 + MO_R * 0.02 + V(0, 0, 0.035))
c.inverse_matrix = (Mo.o.matrix_world @ Mo.o.pose.bones["wrist.L"].matrix).inverted()
Mo.face(60, smile=0.0); Mo.face(75, jaw=8, smile=1.0, brow=0.5); Mo.face(150, jaw=2, smile=0.6); Mo.face(200, smile=0.2)
Mo.face(1880, smile=0.2); Mo.face(1905, jaw=12, oo=0.5, brow=1.0); Mo.face(1940, jaw=3, smile=1.0, brow=0.6); Mo.face(END, jaw=2, smile=1.0)

Fa = DAD; FA_YAW = -78.0; FA_F, FA_R = fdir(FA_YAW), rdir(FA_YAW)
FA_POS = V(1.95, 0.75, 0)
for s in "LR":
    for f in (1, END):
        Fa.foot(s, f, Fa.h.foot_xy(s, FA_POS, FA_YAW + (8 if s == "L" else -8)), FA_YAW + (10 if s == "L" else -6))
book = mk("Book", lambda bm: bmesh.ops.create_cube(bm, size=1.0), matc("M_BookCloth", (0.2, 0.08, 0.05), 0.7))
for v in book.data.vertices: v.co = Vector((v.co.x * 0.30, v.co.y * 0.21, v.co.z * 0.025))
page = mk("BookPage", lambda bm: bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5), matc("M_Paper", (0.85, 0.82, 0.72), 0.9))
for v in page.data.vertices: v.co = Vector((v.co.x * 0.28 + 0.07, v.co.y * 0.4, 0.0))
page_piv = bpy.data.objects.new("BookPagePivot", None); bpy.data.collections["PROPS"].objects.link(page_piv)
page_piv.parent = book; page.parent = page_piv; page_piv.location = (0, 0, 0.014)
for f, tf in ((1, 0), (30, 0), (48, 1), (330, 1), (348, 2), (760, 2), (778, 3), (1200, 3), (1218, 4), (1600, 4), (1618, 5)):
    ang = 0 if f in (1, 30, 330, 760, 1200, 1600) else 180
    page_piv.rotation_euler = (0, R_(-ang), 0); page_piv.keyframe_insert("rotation_euler", frame=f)
    if ang == 180:
        page_piv.rotation_euler = (0, 0, 0); page_piv.keyframe_insert("rotation_euler", frame=f + 1)
def fa_book_pos(f):
    low = smooth((f - 1880) / 30.0)
    ev(f); ch = Fa.bone_world("spine03")
    return ch + FA_F * (0.32 - 0.08 * low) + V(0, 0, 0.02 - 0.32 * low)
for f in keys_every(1, END, 12):
    laugh = smooth((f - 60) / 10) * (1 - smooth((f - 140) / 20))
    turn = smooth((f - 1870) / 40.0)
    sway = wave(f, 480, 0.015)
    Fa.root(f, FA_POS + FA_R * sway + V(0, 0, Fa.root_head.z - 0.01 - 0.01 * laugh * abs(math.sin(f / 3.0))), FA_YAW, side=wave(f, 480, 1.5))
    Fa.spine(f, flex=10 - 14 * laugh + laugh * 3 * math.sin(f / 2.5), twist=-20 * turn, head=(18 - 30 * laugh - 14 * turn, -25 * turn))
    bp = fa_book_pos(f)
    Fa.hand("L", f, bp + FA_R * 0.13 - FA_F * 0.06, FA_F * 0.2 + UP * 0.3 - FA_R * 0.6, -FA_R * 0.3 + -UP, bp + FA_R * 0.5 - FA_F * 0.3)
    flip = any(a <= f <= a + 20 for a in (30, 330, 760, 1200, 1600))
    Fa.hand("R", f, bp - FA_R * 0.15 - FA_F * 0.06 + V(0, 0, 0.06 if flip else 0.0), FA_F * 0.2 + UP * 0.3 + FA_R * 0.6, FA_R * 0.3 - UP, bp - FA_R * 0.5 - FA_F * 0.3)
    for s in "LR": Fa.fingers(s, f, 35, 25)
    bk_m = Matrix.Translation(bp) @ Matrix.Rotation(R_(FA_YAW + 180), 4, 'Z') @ Matrix.Rotation(R_(-55 + 50 * smooth((f - 1880) / 30)), 4, 'X')
    book.matrix_world = bk_m; book.keyframe_insert("location", frame=f); book.keyframe_insert("rotation_euler", frame=f)
Fa.face(60, smile=0.2); Fa.face(72, jaw=10, smile=1.0); Fa.face(140, jaw=2, smile=0.6); Fa.face(200, smile=0.1); Fa.face(1880, smile=0.1); Fa.face(1930, jaw=4, smile=1.0, brow=0.8); Fa.face(END, jaw=2, smile=1.0)

# ---------------------------------------------- DOG: trots in, barks at the girl (she doesn't react), wags, settles
dog = bpy.data.objects["Dog_rig"]; DR = Rig(dog)
for pb in dog.pose.bones: pb.rotation_mode = 'QUATERNION'
DOG_END = V(0.98, -0.18, 0)
dpath = catmull([(1, V(2.4, -1.9, 0)), (40, V(1.8, -1.0, 0)), (80, DOG_END)])
dog_head = math.degrees(math.atan2((CHAIR - DOG_END.to_2d()).x, -(CHAIR - DOG_END.to_2d()).y))
hd_fn = quad_move(DR, dpath, 1, 80, 0.32, gait="trot")
hstop = hd_fn(80)
for f in (90, END):
    quad_hold(DR, f, DOG_END, hstop)
for f in keys_every(80, END, 6):
    bark = max([math.exp(-((f - b) / 5.0) ** 2) for b in (95, 118, 142, 1880, 1900)])
    look = 0.0 if f < 300 else (-25 if f < 1840 else 10)
    DR.key_rot("head", f, [("X", -25 * bark + wave(f, 300, 4)), ("Z", look)])
    DR.key_rot("neck1", f, [("X", -12 * bark)])
    wag = 25 if (f < 200 or f > 1860) else 10
    DR.key_rot("tail1", f, [("Z", wag * math.sin(f / (1.6 if wag > 20 else 4.0))), ("X", 20)])
for f in keys_every(1, 80, 6):
    DR.key_rot("tail1", f, [("Z", 25 * math.sin(f / 1.6)), ("X", 20)])

# ---------------------------------------------- clock hands, lamp
clock = bpy.data.objects["rig_vintage_grandfather_clock_01"]
for pb in clock.pose.bones: pb.rotation_mode = 'XYZ'
for b, f, ang in (("ctrl_minutes", 1, 0), ("ctrl_minutes", 1723, 6), ("ctrl_minutes", 1843, 6 + 360 * 6), ("ctrl_minutes", END, 6 + 360 * 6 + 2),
                  ("ctrl_hour", 1, 0), ("ctrl_hour", 1723, 0.5), ("ctrl_hour", 1843, 180), ("ctrl_hour", END, 181)):
    pb = clock.pose.bones[b]; pb.rotation_euler = (0, R_(ang), 0); pb.keyframe_insert("rotation_euler", frame=f)
print("FAMILY_DOG_DONE")
exec(open(os.path.join(HERE, "03b_fx_camera.py")).read())
if OUT:
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
    print("SAVED", OUT)
