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
    if abs(x - STOOL.x) < 0.13 and abs(y - STOOL.y) < 0.11: return STOOL.z
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
        W = Vector(W)
        if getattr(self, "clamp", True):
            ev(f); sh = self.bone_world("upperarm01." + s)
            L = (self.r.BN["wrist." + s].head_local - self.r.BN["upperarm01." + s].head_local).length * 0.92
            if (W - sh).length > L: W = sh + (W - sh).normalized() * L
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
# ---------------------------------------------- hand joint limits (client rule, Nov 11 23:00): no backward or twisted bends
def add_hand_limits(P):
    """Limit Rotation (local space) on every finger, thumb and wrist bone. The flexion axis and its sign are found from the
    rig itself: the same curl rotation fingers() keys is converted to local euler, the dominant axis is the bend axis."""
    out = []
    for s_ in "LR":
        Rh = P.rest_hand[s_]; a_ = Rh.col[1]; sign = 1 if s_ == "R" else -1
        for k in range(1, 6):
            for j in range(1, 4):
                b = "finger%d-%d.%s" % (k, j, s_)
                if b not in P.r.PB: continue
                e = P.r.local_q(b, Matrix.Rotation(R_(40 * sign), 3, a_)).to_euler()
                ax = max(range(3), key=lambda i: abs(e[i])); sg = 1 if e[ax] > 0 else -1
                c = P.r.PB[b].constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'; c.name = "HandLimit"
                c.use_limit_x = c.use_limit_y = c.use_limit_z = True
                lim = {0: (c, "x"), 1: (c, "y"), 2: (c, "z")}
                bend_max = R_(95 if k > 1 else 70)
                side = R_(12 if k > 1 else 35)
                for i, nm in enumerate("xyz"):
                    if i == ax:
                        lo, hi = (-R_(5), bend_max) if sg > 0 else (-bend_max, R_(5))
                        if k == 1: lo, hi = (lo - R_(25), hi) if sg > 0 else (lo, hi + R_(25))
                    else:
                        lo, hi = -side, side
                    setattr(c, "min_" + nm, lo); setattr(c, "max_" + nm, hi)
                out.append(b)
        # wrist: +/-60 flex, +/-25 side, +/-40 twist (after its Copy Rotation from the IK control)
        c = P.r.PB["wrist." + s_].constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'; c.name = "WristLimit"
        c.use_limit_x = c.use_limit_y = c.use_limit_z = True
        c.min_x, c.max_x = -R_(60), R_(60); c.min_y, c.max_y = -R_(40), R_(40); c.min_z, c.max_z = -R_(30), R_(30)
        # elbow: the IK solver honours IK limits - no hyper-extension past straight
        for eb_ in ("lowerarm01." + s_,):
            pb = P.r.PB[eb_]; pb.ik_stretch = 0.0
    return len(out)
for P_ in (GIRL, TEACH, MOM, DAD):
    print("HAND_LIMITS", P_.name, add_hand_limits(P_))
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
    flex = 14 * (1 - u) + 3 * u + wave(f, 230, 2.2) + 10 * lean_to_teacher
    twist = -16 * lean_to_teacher
    head_p = 12 * (1 - u) - 4 * u
    head_y = -18 * lean_to_teacher
    return flex, twist, head_p, head_y
for f in keys_every(1, END, 10):
    fl, tw, hp, hy = g_posture(f)
    hp -= 9 * smooth((f - 1440) / 40.0)   # lifts her face when she starts to practise
    hp -= 18 * smooth((f - 500) / 70.0) * (1 - smooth((f - 1075) / 45.0))   # face up towards the voice under her hand (beats 4-6)
    G.root(f, G_HIP + V(0, -0.05 * smooth((f - 460) / 60.0) * (1 - smooth((f - 1900) / 60.0)), 0), G_YAW, flex=-8 + fl * 0.3)
    G.spine(f, flex=fl, twist=tw, head=(hp, hy))
# eyes unfocused: slightly divergent, slow drift, never tracking (until the last beat where they still don't track but she smiles)
for f in keys_every(1, END, 40):
    G.face(f, eyes=(wave(f, 900, 7) + 4, wave(f, 700, 4) - 6), blink=1.0 if (f % 520) == 0 else 0.0)
# lap hands (beats 1-2): fingers rubbing, "only touch"
def lap(s, f):
    sx = 1 if s == "L" else -1
    return V(CHAIR.x + sx * 0.1, CHAIR.y - 0.22, 0.715), V(-sx * 0.1, -1, -0.25), V(0, 0.1, 1), V(CHAIR.x + sx * 0.4, CHAIR.y + 0.2, 0.75)
for f in keys_every(1, 450, 20):
    for s in "LR":
        W, d, n, pole = lap(s, f)
        if f > 163 and s == "R":
            W = W + V(0.03 * math.sin(f / 23.0), 0.015 * math.cos(f / 31.0), 0.012)  # right hand strokes the lap beside the left (no overlap)
        G.hand(s, f, W, d, n, pole); G.fingers(s, f, 25 + 15 * math.sin(f / 17.0 + (s == "L")), 12)

# ================================================================== TEACHER
T = TEACH
T_YAW = 141.0; T_F, T_R = fdir(T_YAW), rdir(T_YAW)
T_KNEEL = V(-0.24, 0.09, 0.50) - fdir(141.0) * 0.12
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
T_BODY = [(442, 14, 0, (6, 0)), (462, 36, -8, (16, -8)), (505, 24, -4, (8, 0)), (600, 17, 0, (2, 0)), (895, 15, 0, (-6, 0)), (980, 17, 0, (4, 0)), (1063, 16, -6, (2, -6)),
          (1261, 16, 0, (0, 0)), (1453, 12, 8, (6, 10)), (1600, 14, 8, (8, 12)), (1723, 4, 0, (0, 0)), (1843, 4, 0, (-2, 0))]
_tb = [(f_, fl_, tw_, hd_[0], hd_[1]) for f_, fl_, tw_, hd_ in T_BODY]
_fl = pchip([(x[0], x[1]) for x in _tb]); _tw = pchip([(x[0], x[2]) for x in _tb]); _hp = pchip([(x[0], x[3]) for x in _tb]); _hy = pchip([(x[0], x[4]) for x in _tb])
for f in range(472, 1900, 30):
    if any(abs(f - x[0]) < 12 for x in _tb): continue
    chin = -22 if f < 1063 else -4
    t_kneel_keys(f, T_KNEEL, T_YAW, _fl(f) + (0 if f < 1063 else 5) + wave(f, 250, 1.5), _tw(f) + wave(f, 410, 2.0),
                 (_hp(f) + chin + wave(f, 95, 1.2), _hy(f) + wave(f, 330, 3.0)))
for f, fl, tw, hd in T_BODY:
    chin = -22 if f < 1063 else -4      # chin up while the hand is on her throat, back down to offer her lips
    t_kneel_keys(f, T_KNEEL, T_YAW, fl + (0 if f < 1063 else 5), tw, (hd[0] + chin, hd[1]))
# arms at walk: swing (walk() does not key arms)
for f in keys_every(250, 392, 12):
    ph = math.sin((f - 250) / 15.0)
    for s, sx in (("L", -1), ("R", 1)):
        ev(f); sh = T.bone_world("upperarm01." + s); yw = tyaw(f); F_, R__ = fdir(yw), rdir(yw)
        W = sh + R__ * sx * 0.1 - UP * 0.42 + F_ * 0.08 * ph * (1 if s == "L" else -1)
        T.hand(s, f, W, -UP + F_ * 0.15, R__ * sx, sh + R__ * sx * 0.3 - F_ * 0.3)
        T.fingers(s, f, 20, 15)
for f in (1, 249):
    for s, sx in (("L", -1), ("R", 1)):
        ev(250); sh = T.bone_world("upperarm01." + s)
        T.hand(s, f, sh + rdir(90) * sx * 0.04 - UP * 0.44, -UP, rdir(90) * sx, sh + rdir(90) * sx * 0.3 - fdir(90) * 0.3); T.fingers(s, f, 20, 15)

# ---------------------------------------------- contact helpers
def t_throat(f, up=-0.015):
    return T.throat_point(f, fdir(T_YAW), up)      # over the larynx, well below the jaw
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
    return (lat.normalized() + UP * 0.1).normalized()      # around the neck: clear of the chin above and the collar below
exec(open(os.path.join(HERE, "..", "..", "pipeline", "hand_poses.py")).read())   # shared director hand-pose library (7155c8d)
def g_throat_pad(f, tp, press=0.0):
    """girl's right palm flat on the teacher's larynx (hand_poses: place_hand + flat_palm), light touch"""
    F_ = fdir(T_YAW); along = g_throat_along(f, tp); along = (along - F_ * along.dot(F_)).normalized()
    g_hand_on("R", f, tp, F_, along, press=press, curl=[2, 2, 2, 3], tilt=0.5, pad=0.012)   # reach-checked placement (place_hand's IK frame does not match this rig's controls)
    apply_pose(G.o, "R", "shield", f)       # hand_poses.py: flat fingers, thumb tucked beside the index (flat_palm thumb sticks out into the neck)
def g_hand_on(s, f, tip, normal, along, press=0.0, curl=6, pad=0.005, tilt=0.0):
    """middle fingertip pad at 'tip' (world), palm towards -normal, fingers pointing 'along'; two correction passes"""
    along = (along - normal * along.dot(normal)).normalized()
    if tilt: along = (along * (1 - tilt) - normal * tilt).normalized()     # fingers angled in: only the pads touch, palm stays off
    goal = tip + normal * (pad - press)
    W = goal - along * (G_HL * 0.95)
    sh = G.bone_world("upperarm01." + s, f)
    pole = sh + (W - sh) * 0.5 + V(0, 0.25, -0.35) + (V(-0.3, 0, 0) if s == "R" else V(0.3, 0, 0))
    for it in range(3):
        G.hand(s, f, W, along, normal, pole); G.fingers(s, f, curl if isinstance(curl, list) else max(curl, 14), 14, spread=0)
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
    """teacher's right hand lies over the girl's wrist, fingers wrapping across it (not pointing into it)"""
    n = Vector(n).normalized(); d = Vector(d).normalized()
    across = n.cross(d).normalized()
    if across.dot(T_F) < 0: across = -across          # fingers point away from the teacher, over the far side of the wrist
    top = W + n * 0.085 - across * 0.03
    T.hand("R", f, top, across, n, T_KNEEL + T_R * 0.45 + UP * 0.45)
    T.fingers("R", f, 3, 12)      # flat hand laid over the back of her wrist: guides without digging in
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
    tip = (W0 + d0.normalized() * G_HL).lerp(tipT, u) + (UP * 0.02 - fdir(T_YAW) * 0.05) * math.sin(math.pi * u)   # arc out toward the teacher, clear of her own face
    nrm = n0.lerp(-fdir(T_YAW) * -1, u).normalized()
    g_hand_on("R", f, tip, nrm, d0.lerp(UP * 0.6 + T_R * -0.8, u), curl=20 - 14 * u)
    ev(f); Wg = G.bone_world("wrist.R"); t_grip_wrist(f, Wg, d0.lerp(UP, u), nrm)
for f in throat_keys:
    # beat 6: press harder when loud, relax when soft
    press = 0.004 if 895 <= f < 990 else (0.0 if f >= 990 else 0.002)
    tp = t_throat(f)
    g_throat_pad(f, tp, press)
# teacher's right hand lets go and rests on the girl's forearm, then gestures softly
def t_thigh_R(f, lift=0.0, sd="R"):
    """hand rests on the FRONT of her (vertical, kneeling) thigh, on the skirt surface"""
    ev(f); kn = T.bone_world("lowerleg01." + sd); hp = T.bone_world("upperleg01." + sd); mid = hp.lerp(kn, 0.82)
    sk = bpy.data.objects.get("Teacher.long_skirt")
    hit = None
    if sk:
        dg_ = bpy.context.evaluated_depsgraph_get(); es = sk.evaluated_get(dg_); mi = es.matrix_world.inverted()
        o_ = mid + T_F * 0.35; ok, loc, nrm, idx = es.ray_cast(mi @ o_, (mi.to_3x3() @ (-T_F)).normalized())
        if ok: hit = es.matrix_world @ loc
    p = (hit if hit else mid + T_F * 0.12) + T_F * 0.045 + V(0, 0, lift)
    sx_ = 1 if sd == "R" else -1
    T.hand(sd, f, p, -UP * 0.9 + T_F * 0.2, T_F, p + T_R * 0.35 * sx_ + UP * 0.25)
    T.fingers(sd, f, 22, 15)
    T.fingers("R", f, 28, 18)
def t_rest(f, sd):
    """reachable resting spots while she kneels upright: L on the armchair arm (away from her hip), R on the girl's knee"""
    ev(f); dg_ = bpy.context.evaluated_depsgraph_get()
    sh = T.bone_world("upperarm01." + sd); hip = T.bone_world("upperleg01." + sd)
    if sd == "L":
        chair = bpy.data.objects["ArmChair_01"]; ec = chair.evaluated_get(dg_); mi = ec.matrix_world.inverted(); best = None
        for k in range(0, 8):
            probe = T_KNEEL + T_F * 0.4 - T_R * 0.06 + V(0, 0.04 * k, 0.6)
            ok, loc, nrm, idx = ec.ray_cast(mi @ probe, (mi.to_3x3() @ V(0, 0, -1)).normalized())
            if not ok: continue
            w = ec.matrix_world @ loc
            if w.z > 0.6 and (w - hip).length > 0.24 and (w - sh).length < 0.5: best = w; break
        top = best if best else T_KNEEL + T_F * 0.42 + V(0, 0.1, 0.16)
        p = top + V(0, 0, 0.03)
        T.hand("L", f, p, (T_F + V(0, 0.4, 0)).normalized() * 0.8 - UP * 0.3, UP, p - T_R * 0.35 - T_F * 0.15 + UP * 0.1); T.fingers("L", f, 30, 18)
    else:
        kn = G.bone_world("lowerleg01.R") + V(-0.055, 0.05, 0)     # outer side of her knee, clear of her own forearm above it
        sk = bpy.data.objects["Girl.long_skirt"]; es = sk.evaluated_get(dg_); mi = es.matrix_world.inverted()
        ok, loc, nrm, idx = es.ray_cast(mi @ (kn + UP * 0.3), (mi.to_3x3() @ V(0, 0, -1)).normalized())
        top = (es.matrix_world @ loc) if ok else kn + UP * 0.07
        p = top + V(0, 0, 0.028) - T_F * 0.05
        p = p + V(0, 0, 0.032)
        T.hand("R", f, p, T_F, UP, T_KNEEL + T_R * 0.45 + UP * 0.35); T.fingers("R", f, 2, 12)
for f in list(range(548, 1041, 30)) + [1040]:
    t_rest(f, "R")
# teacher's left hand: on her own thigh, then on the girl's knee
for f in (412, 430, 445):     # left hand stays down at her side while she kneels (no sweep past the girl's lap)
    ev(f); sh_ = T.bone_world("upperarm01.L"); yw_ = T_YAW if f >= 430 else 130
    T.hand("L", f, sh_ - rdir(yw_) * 0.1 - UP * 0.4 - fdir(yw_) * 0.03, -UP + fdir(yw_) * 0.15, -rdir(yw_), sh_ - rdir(yw_) * 0.3 - fdir(yw_) * 0.3)
    T.fingers("L", f, 22, 15)
for f, where in ((458, "thigh"), (700, "thigh"), (1063, "thigh"), (1453, "knee"), (1700, "knee"), (1843, "knee"), (1925, "knee"), (END, "knee")):
    ev(f)
    if True:
        # left hand steadies her on the armchair's arm in front of her (clear of her skirt)
        chair = bpy.data.objects["ArmChair_01"]; dg_ = bpy.context.evaluated_depsgraph_get(); ec = chair.evaluated_get(dg_); mi = ec.matrix_world.inverted()
        probe = T_KNEEL + T_F * 0.4 - T_R * 0.06 + V(0, 0, 0.6)
        hit, loc, nrm, idx = ec.ray_cast(mi @ probe, (mi.to_3x3() @ V(0, 0, -1)).normalized())
        top = (ec.matrix_world @ loc) if hit else (T_KNEEL + T_F * 0.4 + V(0, 0, 0.15))
        if f == 442: print("ARMREST", tuple(round(x, 3) for x in top), hit)
        p = top + V(0, 0, 0.03) - T_F * 0.07
        t_rest(f, "L")
    else:
        kn = G.bone_world("lowerleg01.L")
        T.hand("L", f, kn + V(0, 0, 0.07) - T_F * 0.05, T_F * 0.5 + UP * -0.6 + T_R * 0.3, UP, T_KNEEL - T_R * 0.45 + UP * 0.3)
    T.fingers("L", f, 22, 15)
# ---------------------------------------------- beat 7-9: the girl's hand on the teacher's lips and nose
def lip_key(f, dx=0.0, dz=0.0, press=0.0):
    mp, ff = t_mouth(f)
    if dz > 0.005:          # on the nose: re-find the skin surface there so the pad rests on it
        hit, nrm = T.surface(f, mp + UP * dz + ff * 0.12, -ff)
        if hit: mp = hit - UP * dz
    side = ff.cross(UP).normalized()
    # Tadoma hold: fingers upright across the mouth, middle fingertip on the upper lip by the nose, palm on the face
    g_hand_on("R", f, mp + side * dx * 0.5 + UP * (0.03 + dz * 0.6) + ff * 0.001, ff, UP * 0.92 - side * 0.38, press=press, curl=4, pad=0.004)
LIP_KEYS = [(1063, None, None), (1085, None, None)]
for f in range(1110, 1723, 6):
    nose = math.exp(-((f - 1215) / 18.0) ** 2)          # fingertips slide up to the nose and back
    LIP_KEYS.append((f, 0.009 * math.sin((f - 1110) / 23.0) * (1 - nose), 0.024 * nose))
for f, dx, dz in LIP_KEYS:
    if dx is None:
        u = smooth((f - 1063) / 47.0); tp = t_throat(f); mp, ff = t_mouth(f)
        tip = tp.lerp(mp + ff * 0.02, u) + ff * 0.085 * math.sin(math.pi * u)
        g_hand_on("R", f, tip, fdir(T_YAW).lerp(ff, u).normalized(), (UP * 0.55 + rdir(T_YAW) * 0.85).lerp(-ff.cross(UP) + UP * 0.25, u), curl=12)
        ev(f); Wg = G.bone_world("wrist.R"); t_grip_wrist(f, Wg, (UP).normalized(), fdir(T_YAW))
    else:
        lip_key(f, dx, dz)
# teacher's right hand releases after guiding (1110) and rests on the girl's forearm again
for f in list(range(1128, 1851, 30)) + [1850]:
    t_rest(f, "R")
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
    along = (-side + UP * (0.2 if what == "lips" else 0.0)).normalized()
    g_hand_on("L", f, p + UP * (dz - (0.02 if what == "throat" else 0.0)), ff, along, curl=10)
for f in range(1490, 1601, 10):
    g_left_on(f, "lips")
for f in range(1615, 1723, 10):
    g_left_on(f, "throat")
# ---------------------------------------------- beat 10: time-lapse practice bursts (hands alternate fast)
for i, f in enumerate(range(1735, 1843, 18)):
    g_left_on(f, "lips" if i % 2 == 0 else "throat")
    if i % 2 == 0: lip_key(f)
    else:
        tp = t_throat(f); g_throat_pad(f, tp)
    # lift off between touches so the hand never slides through the face
    if f + 9 < 1843:
        fm = f + 9; mp_, ff_ = t_mouth(fm); tp_ = t_throat(fm)
        g_hand_on("R", fm, mp_.lerp(tp_, 0.5) + ff_ * 0.06, ff_, UP, curl=15, pad=0.02)
        p_, gf_ = g_own_mouth(fm); g_hand_on("L", fm, p_ + gf_ * 0.06 - UP * 0.03, gf_, UP, curl=15, pad=0.02)
# ---------------------------------------------- beat 11: she speaks (left hand on her own throat), teacher gasps then hugs
for f in range(1843, END + 1, 8):
    g_left_on(f, "throat")
for f in (1843, 1858):
    lip_key(f)
# girl's right hand comes down to the teacher's shoulder for the hug
for f in (1872, 1915):
    W, d, n, pole = lap("R", f); G.hand("R", f, W, d, n, pole); G.fingers("R", f, 25, 12)
for f in (1955, END):
    W, d, n, pole = lap("R", f); G.hand("R", f, W, d, n, pole); G.fingers("R", f, 25, 12)
# teacher gasp: both hands to her mouth (no contact), 1866-1905
for f in (1866, 1885, 1905):
    mp, ff = t_mouth(f); side = ff.cross(UP).normalized()
    for s, sx in (("L", 1), ("R", -1)):
        tip = mp + ff * 0.045 + side * sx * 0.03 + UP * 0.01
        along = (UP * 0.8 + side * -sx * 0.3).normalized()
        T.hand(s, f, tip - along * T_HL * 0.95 + ff * 0.01, along, ff, T_KNEEL + T_R * -sx * 0.4 + UP * 0.2)
# the teacher's skirt only wraps her legs once she kneels (a straight column while she walks in)
ts = bpy.data.objects["Teacher.long_skirt"]
for mn in ("DrapeOnLegs", "DrapeIn", "Bridge"):
    md = ts.modifiers[mn]
    for f, v in ((1, False), (398, False), (399, True)):
        md.show_render = v; md.show_viewport = v; md.keyframe_insert("show_render", frame=f); md.keyframe_insert("show_viewport", frame=f)
        T.fingers(s, f, 15, 15)
# hug (1925-END): teacher rises to a high kneel and wraps both arms round the girl's shoulders
T_HUG = T_KNEEL + V(0, 0, 0.06)
t_kneel_keys(1905, T_KNEEL, T_YAW, 8, 0, (-6, 0)); t_kneel_keys(1930, T_HUG, T_YAW, 22, 0, (10, -12)); t_kneel_keys(END, T_HUG + V(0, 0, -0.01), T_YAW, 23, 0, (11, -12))
def t_hand_on(sd, f, tip, normal, along, curl=10, pad=0.006):
    """teacher fingertip (middle) on a surface point, palm towards -normal, two correction passes (reach-capped in hand())"""
    along = (along - normal * along.dot(normal)).normalized(); goal = tip + normal * pad
    W = goal - along * (T_HL * 0.95)
    for it in range(3):
        T.hand(sd, f, W, along, normal, T_HUG + T_R * (-0.45 if sd == "L" else 0.45) + UP * 0.2); T.fingers(sd, f, curl, 20)
        if it == 2: break
        ev(f); err = goal - T.bone_world("finger3-3." + sd, tail=True)
        if err.length < 1e-3: break
        W = W + err
# joy: the teacher lays her right hand on her own heart (left hand steadies her on the armrest); no body-to-body contact
for f in (1932, 1955, END):
    ev(f); ch = T.bone_world("spine02"); TFn = fdir(T_YAW)
    hit, nrm = T.surface(f, ch + TFn * 0.3 - T_R * 0.06 + UP * 0.05, -TFn, "female_elegantsuit01")
    heart = (hit if hit else ch + TFn * 0.12)
    t_hand_on("R", f, heart + UP * 0.04, nrm if hit else TFn, -T_R * 0.6 + UP * 0.8, curl=14, pad=0.035)
# 1905 -> 1932 the hands come down from the mouth in front of her own chest (never through the girl's arm)
for f in (1912, 1920):
    ev(f); ch = T.bone_world("spine03"); TFn = fdir(T_YAW)
    for sd, sx in (("L", -1), ("R", 1)):
        tip = ch + TFn * 0.3 + T_R * sx * 0.11 + UP * 0.06
        T.hand(sd, f, tip - UP * T_HL * 0.9, UP, TFn, T_KNEEL + T_R * sx * 0.4 + UP * 0.2); T.fingers(sd, f, 18, 15)
# girl leans in to the hug
for f in (1930, END):
    fl, tw, hp, hy = g_posture(f); G.spine(f, flex=fl, twist=-14, head=(hp - 4, -22))

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
T.face(540, smile=0.4, blink=0.5, brow=0.3); T.face(560, smile=0.2, jaw=1); T.face(1112, smile=0.5, blink=0.4); T.face(1130, smile=0.2)
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
    return 0.0
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
        Mo.hand("L", f, LAP - MO_R * 0.14 + V(0, 0, 0.09), MO_F * 1.0 + MO_R * 0.05, UP, LAP - MO_R * 0.45 - MO_F * 0.2 + UP * 0.1); Mo.fingers("L", f, 35, 25)
        Mo.hand("R", f, LAP + MO_R * 0.16 + MO_F * 0.03 + V(0, 0, 0.10 + 0.16 * up_), MO_F * 0.9 - MO_R * 0.1 - UP * 0.25, UP + MO_F * 0.3, LAP + MO_R * 0.45 - MO_F * 0.2)
        Mo.fingers("R", f, [40, 55, 65, 70], 30)
    else:
        ev(f); ch = Mo.bone_world("spine02") + MO_F * 0.17 + V(0, 0, 0.05)
        Mo.hand("L", f, ch + MO_R * 0.05, -MO_R + UP * 0.3, MO_F, ch + MO_R * 0.4 - MO_F * 0.2); Mo.fingers("L", f, 30, 20)
        Mo.hand("R", f, ch - MO_R * 0.07 - UP * 0.08, MO_R + UP * 0.2, MO_F, ch - MO_R * 0.4 - MO_F * 0.2); Mo.fingers("R", f, 30, 20)
c = hoop.constraints.new('CHILD_OF'); c.target = Mo.o; c.subtarget = "wrist.L"
pm = bpy.data.materials["M_Linen"]; pmn = pm.node_tree.nodes; pp = pmn["Principled BSDF"]
wv_ = pmn.new("ShaderNodeTexWave"); wv_.inputs["Scale"].default_value = 900; bp_ = pmn.new("ShaderNodeBump"); bp_.inputs["Strength"].default_value = 0.3
pm.node_tree.links.new(wv_.outputs["Fac"], bp_.inputs["Height"]); pm.node_tree.links.new(bp_.outputs["Normal"], pp.inputs["Normal"])
hw = bpy.data.materials["M_HoopWood"]; hwn = hw.node_tree.nodes; hp_ = hwn["Principled BSDF"]
wg = hwn.new("ShaderNodeTexWave"); wg.wave_type = 'RINGS'; wg.inputs["Scale"].default_value = 40; wg.inputs["Distortion"].default_value = 6
cm = hwn.new("ShaderNodeMix"); cm.data_type = 'RGBA'; cm.inputs["A"].default_value = (0.3, 0.17, 0.08, 1); cm.inputs["B"].default_value = (0.5, 0.33, 0.17, 1)
hw.node_tree.links.new(wg.outputs["Fac"], cm.inputs["Factor"]); hw.node_tree.links.new(cm.outputs["Result"], hp_.inputs["Base Color"])
ev(1); hoop.matrix_world = Matrix.Translation(LAP - MO_R * 0.02 + MO_F * 0.04 + V(0, 0, 0.06))
c.inverse_matrix = (Mo.o.matrix_world @ Mo.o.pose.bones["wrist.L"].matrix).inverted()
Mo.face(60, smile=0.0); Mo.face(75, jaw=8, smile=1.0, brow=0.5); Mo.face(150, jaw=2, smile=0.6); Mo.face(200, smile=0.2)
Mo.face(1880, smile=0.2); Mo.face(1905, jaw=12, oo=0.5, brow=1.0); Mo.face(1940, jaw=3, smile=1.0, brow=0.6); Mo.face(END, jaw=2, smile=1.0)

Fa = DAD; FA_YAW = -78.0; FA_F, FA_R = fdir(FA_YAW), rdir(FA_YAW)
FA_POS = V(1.95, 0.75, 0)
for s in "LR":
    for f in (1, END):
        Fa.foot(s, f, Fa.h.foot_xy(s, FA_POS, FA_YAW + (8 if s == "L" else -8)), FA_YAW + (10 if s == "L" else -6))
book = bpy.data.objects["Model_OpenBook"]; book.name = "Book"; book.hide_render = False
page = mk("BookPage", lambda bm: bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5), matc("M_Paper", (0.85, 0.82, 0.72), 0.9))
for v in page.data.vertices: v.co = Vector((v.co.x * 0.26 + 0.068, v.co.y * 0.3, 0.0))
page.modifiers.new("Curl", 'SIMPLE_DEFORM').deform_method = 'BEND'
page.modifiers["Curl"].angle = R_(25); page.modifiers["Curl"].deform_axis = 'Y'
page_piv = bpy.data.objects.new("BookPagePivot", None); bpy.data.collections["PROPS"].objects.link(page_piv)
page_piv.parent = book; page.parent = page_piv; page_piv.location = (0, 0, 0.024)
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
    Fa.hand("L", f, bp - FA_R * 0.15 - FA_F * 0.06, FA_F * 0.2 + UP * 0.3 + FA_R * 0.6, FA_R * 0.3 - UP, bp - FA_R * 0.5 - FA_F * 0.3)
    flip = any(a <= f <= a + 20 for a in (30, 330, 760, 1200, 1600))
    Fa.hand("R", f, bp + FA_R * 0.15 - FA_F * 0.06 + V(0, 0, 0.06 if flip else 0.0), FA_F * 0.2 + UP * 0.3 - FA_R * 0.6, -FA_R * 0.3 - UP, bp + FA_R * 0.5 - FA_F * 0.3)
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
DOG_END2 = V(0.55, -0.75, 0)
for f in (90, 690):
    quad_hold(DR, f, DOG_END, hstop)
dpath2 = catmull([(690, DOG_END), (735, V(0.85, -0.55, 0)), (780, DOG_END2)])
hd2 = quad_move(DR, dpath2, 690, 780, 0.32, gait="walk")
for f in (790, END):
    quad_hold(DR, f, DOG_END2, hd2(780))
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
# dog breathing (chest) and ear-like head twitches
for f in keys_every(90, END, 20):
    DR.key_rot("chest", f, [("X", 2.5 * math.sin(f / 9.0))]) if "chest" in DR.PB else None
# ribbon bow at the back of the girl's head (child of the head bone)
m_rib = matc("M_Ribbon", (0.45, 0.04, 0.05), 0.35)
ev(1); hb = GIRL.o.pose.bones["head"]; hm = GIRL.o.matrix_world @ hb.matrix
back = (hm.to_3x3() @ (GIRL.r.BN["head"].matrix_local.to_3x3().inverted() @ V(0, 1, 0))).normalized()
hd0 = GIRL.bone_world("head")
bow_c = hd0 + back * 0.085 + UP * 0.07
for k, (sx, rz) in enumerate(()):   # ribbon removed: sphere-built bow read as a primitive; her braids carry the period look
    o = mk("HairRibbon_%d" % k, lambda bm: bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.02), m_rib)
    o.scale = (1.4, 0.45, 0.9) if sx else (0.6, 0.5, 0.6)
    side_ = back.cross(UP).normalized()
    o.matrix_world = Matrix.Translation(bow_c + side_ * sx * 0.024) @ Matrix.Rotation(R_(rz), 4, back) @ Vector((0, 1, 0)).rotation_difference(back).to_matrix().to_4x4() @ Matrix.Diagonal((*o.scale, 1))
    c_ = o.constraints.new('CHILD_OF'); c_.target = GIRL.o; c_.subtarget = "head"
    c_.inverse_matrix = (GIRL.o.matrix_world @ hb.matrix).inverted()
print("FAMILY_DOG_DONE")
# ================================================================== de-intersection pass (acting fix, Nov 12)
from mathutils.bvhtree import BVHTree
def _nomask(ob, on):
    for m in ob.modifiers:
        if m.type in ('MASK', 'SUBSURF'): m.show_viewport = on
_HELPERC = {}
def _helper_verts(o):
    if o.name not in _HELPERC:
        hg = {g.index for g in o.vertex_groups if g.name.lower().startswith(("helper", "joint")) or g.name in ("HelperGeometry", "JointCubes")}
        _HELPERC[o.name] = {v.index for v in o.data.vertices if any(x.group in hg and x.weight > 0.5 for x in v.groups)} if hg else set()
    return _HELPERC[o.name]
_HANDCACHE = {}
def hand_vidx(P, sd):
    key = (P.name, sd)
    if key not in _HANDCACHE:
        body = bpy.data.objects[P.name + ".body"]; bones = set(P.o.data.bones.keys())
        names = {g.index: g.name for g in body.vertex_groups if g.name in bones}; out = []
        for v in body.data.vertices:
            gs = [x for x in v.groups if x.group in names]
            if not gs: continue
            g = max(gs, key=lambda x: x.weight); n = names[g.group]
            if n.endswith("." + sd) and any(k in n for k in ("finger", "metacarpal", "wrist")): out.append(v.index)
        _HANDCACHE[key] = out
    return _HANDCACHE[key]
def ik_keyframes(P, sd, f0, f1):
    ad = P.o.animation_data; out = set()
    for layer in ad.action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    if fc.data_path == 'pose.bones["IK_hand.%s"].location' % sd:
                        out |= {int(round(k.co.x)) for k in fc.keyframe_points if f0 <= k.co.x <= f1}
    return sorted(out)
def deintersect(P, sd, f0, f1, targets, allow=0.008, iters=5, away=None):
    body = bpy.data.objects[P.name + ".body"]; idx = hand_vidx(P, sd); fixed = 0
    tobs = [bpy.data.objects[t] for t in targets if t in bpy.data.objects]
    self_polys = None
    if body in tobs:      # own body as target: only polygons away from the arms
        bones = set(P.o.data.bones.keys()); nm = {g.index: g.name for g in body.vertex_groups if g.name in bones}
        def dom(v):
            gs = [x for x in body.data.vertices[v].groups if x.group in nm]
            return nm[max(gs, key=lambda x: x.weight).group] if gs else ""
        arm = ("finger", "metacarpal", "wrist", "lowerarm", "upperarm", "shoulder", "clavicle")
        self_polys = [tuple(p.vertices) for p in body.data.polygons if not any(any(k in dom(v) for k in arm) for v in p.vertices)]
    for o in [body] + tobs: _nomask(o, False)
    total_ = {}
    for f in ik_keyframes(P, sd, f0, f1):
        for it in range(iters):
            ev(f); dg = bpy.context.evaluated_depsgraph_get()
            eb = body.evaluated_get(dg); mb = eb.to_mesh(); pts = [eb.matrix_world @ mb.vertices[i].co for i in idx if i < len(mb.vertices)]; eb.to_mesh_clear()
            worst = (0.0, None)
            for o in tobs:
                eo = o.evaluated_get(dg); mo = eo.to_mesh()
                polys = self_polys if (o is body and self_polys is not None) else [tuple(p.vertices) for p in mo.polygons if not any(i in _helper_verts(o) for i in p.vertices)]   # hidden MPFB helper shells are not skin
                tr = BVHTree.FromPolygons([eo.matrix_world @ v.co for v in mo.vertices], polys); eo.to_mesh_clear()
                for p in pts:
                    loc, nrm, i_, d = tr.find_nearest(p, 0.12)
                    if loc is not None and (p - loc).dot(nrm) < 0 and d > worst[0]: worst = (d, nrm.normalized())
            if worst[0] <= allow: break
            dirv = away(f, pts) if away else worst[1]            # escape direction known per contact (nearest-normal fails when deep)
            step_ = worst[0] - allow + 0.004
            push = dirv.normalized() * step_
            M = P.o.pose.bones["IK_hand." + sd].matrix.copy()
            P.r.key_world("IK_hand." + sd, f, Matrix.Translation(push) @ M); fixed += 1
    for o in [body] + tobs: _nomask(o, True)
    print("DEINTERSECT", P.name, sd, f0, f1, "pushes", fixed)
def bake_ik(P, sd, f0, f1, step=3):
    """densify IK hand keys (re-key the evaluated pose) so the de-intersection checks every few frames"""
    mats = []
    for f in range(f0, f1 + 1, step):
        ev(f); mats.append((f, P.o.pose.bones["IK_hand." + sd].matrix.copy()))
    for f, M in mats: P.r.key_world("IK_hand." + sd, f, M)
bake_ik(TEACH, "R", 425, 530); bake_ik(TEACH, "R", 440, 470, 1); bake_ik(GIRL, "R", 425, 530); bake_ik(TEACH, "L", 425, 460); bake_ik(GIRL, "L", 425, 470); bake_ik(TEACH, "R", 1600, 1690); bake_ik(GIRL, "R", 1310, 1360, 1); bake_ik(GIRL, "R", 1612, 1630, 1); bake_ik(TEACH, "R", 1890, 1945); bake_ik(TEACH, "L", 1890, 1945); bake_ik(TEACH, "R", 1908, 1922, 1); bake_ik(TEACH, "L", 1908, 1922, 1)
TCL = ["Teacher.body", "Teacher.female_elegantsuit01", "Teacher.long_skirt"]
GCL = ["Girl.body", "Girl.female_elegantsuit01", "Girl.long_skirt"]
def _away_from_teacher(f, pts):
    c = sum(pts, Vector()) / len(pts)
    nk = T.bone_world("neck01").lerp(T.bone_world("head"), 0.5)
    return (c - nk)
_up = lambda f, pts: UP.copy()
deintersect(TEACH, "R", 430, 530, ["Teacher.body", "Teacher.long_skirt"], away=lambda f, pts: (sum(pts, Vector()) / len(pts) - T.bone_world("spine03")))
deintersect(TEACH, "L", 430, 530, ["Teacher.body", "Teacher.long_skirt"], away=lambda f, pts: (sum(pts, Vector()) / len(pts) - T.bone_world("spine03")))
deintersect(GIRL, "R", 400, 529, TCL, away=_away_from_teacher)
deintersect(GIRL, "R", 530, 1066, ["Teacher.body"], allow=0.012, away=_away_from_teacher)   # throat pad: skin only
deintersect(GIRL, "R", 1066, END, TCL, away=_away_from_teacher)
deintersect(GIRL, "L", 400, 520, TCL, away=_away_from_teacher)
deintersect(TEACH, "R", 425, END, GCL, away=_up, iters=8)
deintersect(TEACH, "L", 425, END, GCL, away=_up)
deintersect(GIRL, "L", 1, 470, ["Girl.body", "Girl.long_skirt"], away=_up)
deintersect(GIRL, "R", 1, 470, ["Girl.body", "Girl.long_skirt"], away=_up)
deintersect(GIRL, "R", 1300, 1460, ["Teacher.body"], iters=8, away=lambda f, pts: (sum(pts, Vector()) / len(pts) - T.bone_world("head")))   # fingers on her lips: on the skin, not through it
deintersect(GIRL, "R", 1036, 1115, ["Girl.body"], away=lambda f, pts: (sum(pts, Vector()) / len(pts) - G.bone_world("head")))
deintersect(GIRL, "R", 1580, 1610, TCL, away=_away_from_teacher, allow=0.004)
_from_neck = lambda f, pts: (sum(pts, Vector()) / len(pts) - G.bone_world("neck01"))
_from_girl = lambda f, pts: (sum(pts, Vector()) / len(pts) - G.bone_world("spine03"))
deintersect(TEACH, "R", 1880, END, GCL, away=_from_girl, iters=8)   # hug: hands rest on her back/shoulder, outside the jacket
deintersect(TEACH, "L", 1880, END, GCL, away=_from_girl, iters=8)
deintersect(GIRL, "L", 1600, END, ["Girl.body", "Girl.female_elegantsuit01"], away=_from_neck)   # own-throat touch stays on the skin, not inside the collar
exec(open(os.path.join(HERE, "03b_fx_camera.py")).read())
if OUT:
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
    print("SAVED", OUT)
