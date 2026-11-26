"""WW1Assassination v008 animation helpers (exec'd after lib.py, pipeline/anim_lib.py and pipeline/hand_poses.py).
Standing / seated / walking people on MPFB rigs with IK feet and hands (anim_lib.make_human_ctrl), body-relative hand targets,
idle breathing, head looks, waving, a posed pistol grip and a throw."""
import bpy, math, random
from mathutils import Vector, Matrix, Quaternion

PAVE_Z = 0.15
def ground_z(x, y):
    """walkable height: pavements (north y 4..7.5 outside the side street; side-street pavements |x| 5..7.5) are 0.15 up"""
    if 4.0 <= y <= 7.5 and not (-5.0 < x < 5.0): return PAVE_Z
    if y > 7.5 and 5.0 <= abs(x) <= 7.5: return PAVE_Z
    return 0.0

def yawM(yaw): return Matrix.Rotation(math.radians(yaw), 3, 'Z')

class Person:
    """one MPFB character: IK rig + body-frame helpers. Armature space = world for standing people,
    = car-local for seated people (rig parented to the car body with an identity parent inverse)."""
    def __init__(self, rig, seated=False):
        self.o = rig
        self.R = make_human_ctrl(rig)
        self.H = Human(self.R)
        B = rig.data.bones
        self.sh = {s: B["upperarm01." + s].head_local.copy() for s in "LR"}
        self.hip = {s: B["upperleg01." + s].head_local.copy() for s in "LR"}
        self.root = B["root"].head_local.copy()
        self.head = B["head"].head_local.copy()
        self.wr = {s: B["wrist." + s].head_local.copy() for s in "LR"}
        self.arm_len = {s: (B["lowerarm01." + s].head_local - self.sh[s]).length + (self.wr[s] - B["lowerarm01." + s].head_local).length for s in "LR"}
        self.seated = seated
        self.pos = {}; self.yaw = {}
        add_hand_limits(rig)
        # elbows may straighten (MPFB rest elbow ~46 deg; LESSONS 8)
        for s in "LR":
            pb = self.R.PB["lowerarm01." + s]
            for c in pb.constraints:
                if c.type == 'LIMIT_ROTATION': pb.constraints.remove(c)
    # body frame: rest faces -Y; a body yaw rotates about Z. local (x right-of-character?, y back, z up) in rest axes
    def to_arm(self, f, local):
        """rest-pose-relative point (body at self.pos[f], yaw) -> armature space"""
        p, yw = self.at(f)
        return p + yawM(yw) @ (Vector(local) - Vector((0, 0, 0)))
    def at(self, f):
        ks = sorted(self.pos)
        best = max([k for k in ks if k <= f] or [ks[0]])
        return self.pos[best], self.yaw[best]
    def key_body(self, f, pos, yaw=0.0, flex=0.0, side=0.0, spine=(0, 0, 0), head=(0, 0), drop=0.0):
        """pos: ground point under the pelvis (standing) or the pelvis point on the seat (seated, z = cushion top)"""
        self.pos[f] = Vector(pos); self.yaw[f] = yaw
        if self.seated:
            rz = pos[2] + 0.095 + (self.root.z - self.hip["L"].z) - drop
            # pelvis set back so the sitting bones are on the cushion
            P = Vector((pos[0], pos[1], rz))
        else:
            P = Vector((pos[0], pos[1], pos[2] + self.root.z - drop))
        P = P + yawM(yaw) @ Vector((0, self.root.y, 0)) * 0.0
        self.H.key_root(f, P, yaw=yaw, flex=flex, side=side)
        self.H.key_spine(f, flex=spine[0], twist=spine[1], side=spine[2], head=head)
    def key_feet_stand(self, f, pos, yaw, spread=1.0, fwd=(0.0, 0.0), zg=None):
        for s in "LR":
            a = self.H.ankle[s]
            o = yawM(yaw) @ Vector((a.x * spread, a.y - self.root.y - (fwd[0] if s == "L" else fwd[1]), 0))
            xy = Vector((pos[0] + o.x, pos[1] + o.y))
            z = (ground_z(xy.x, xy.y) if zg is None else zg)
            M = Matrix.Translation(Vector((xy.x, xy.y, z + a.z))) @ Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Translation(-a) @ self.R.rest("IK_foot." + s)
            self.R.key_world("IK_foot." + s, f, M)
            pole = Vector((xy.x, xy.y, z + 0.5)) + yawM(yaw) @ Vector((0, -0.8, 0))
            self.key_pole("Pole_knee." + s, f, pole)
    def key_feet_seated(self, f, seat, yaw, floor_z, reach=0.50, spread=1.15):
        for s in "LR":
            a = self.H.ankle[s]
            o = yawM(yaw) @ Vector((a.x * spread, -reach, 0))
            xy = Vector((seat[0], seat[1], 0)) + o
            M = Matrix.Translation(Vector((xy.x, xy.y, floor_z + a.z))) @ Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Translation(-a) @ self.R.rest("IK_foot." + s)
            self.R.key_world("IK_foot." + s, f, M)
            pole = Vector((xy.x, xy.y, floor_z + 0.6)) + yawM(yaw) @ Vector((0, -0.9, 0))
            self.key_pole("Pole_knee." + s, f, pole)
    def key_pole(self, n, f, P):
        pb = self.R.PB[n]
        pb.location = self.R.rest(n).to_3x3().inverted() @ (Vector(P) - self.R.BN[n].head_local)
        pb.keyframe_insert("location", frame=f, group=n)
    def key_hand_local(self, s, f, wrist_local, d_local, n_local, elbow_local=None):
        """wrist target, finger direction and palm normal given in the body frame (rest axes: -Y forward, +X = character's left)."""
        p, yw = self.at(f)
        Ry = yawM(yw)
        if self.seated:
            base = Vector((p.x, p.y, p.z + 0.095 + (self.root.z - self.hip["L"].z))) - Ry @ Vector((0, 0, self.root.z))
        else:
            base = Vector((p.x, p.y, p.z))
        W = base + Ry @ Vector(wrist_local)
        pole = None if elbow_local is None else base + Ry @ Vector(elbow_local)
        self.H.key_hand(s, f, W, Ry @ Vector(d_local), Ry @ Vector(n_local), pole=pole)
    # ---- ready-made arm poses (body frame, rest axes). sx = +1 for L, -1 for R.
    def arm_relaxed(self, s, f, swing=0.0, out=0.0):
        sx = 1 if s == "L" else -1; S = self.sh[s]
        W = Vector((S.x + sx * (0.07 + out), S.y - 0.06 - swing, S.z - 0.50))
        self.key_hand_local(s, f, W, (sx * 0.15, -0.25, -1.0), (-sx, -0.1, 0), elbow_local=(S.x + sx * 0.35, S.y + 0.45, S.z - 0.30))
    def arm_lap(self, s, f, lean=0.0):
        """seated: forearm along the thigh, hand resting just above the knee-side of the thigh"""
        sx = 1 if s == "L" else -1; S = self.sh[s]; Hh = self.hip[s]
        W = Vector((Hh.x + sx * 0.035, S.y - 0.30 - lean, Hh.z + 0.14))
        self.key_hand_local(s, f, W, (sx * 0.05, -1.0, -0.35), (0, 0, -1), elbow_local=(S.x + sx * 0.45, S.y + 0.25, S.z - 0.35))
    def arm_wave(self, s, f, phase=0.0, height=1.0):
        sx = 1 if s == "L" else -1; S = self.sh[s]
        sw = math.sin(phase) * 0.06
        W = Vector((S.x + sx * (0.24 + sw), S.y - 0.16, S.z + 0.22 * height))
        self.key_hand_local(s, f, W, (sx * (0.15 + sw * 2), -0.15, 1.0), (0, -1.0, 0), elbow_local=(S.x + sx * 0.9, S.y + 0.2, S.z - 0.45))
    def arm_chest(self, s, f, k=1.0):
        """hand raised in front of the chest (startle / guard), palm out; never touching the body (>= 12 cm in front)"""
        sx = 1 if s == "L" else -1; S = self.sh[s]
        W = Vector((S.x * 0.45 + sx * 0.02, S.y - 0.30 * k - 0.05, S.z - 0.18))
        self.key_hand_local(s, f, W, (0, -0.2, 1.0), (0, 1.0, 0.0), elbow_local=(S.x + sx * 0.6, S.y + 0.1, S.z - 0.6))
    def arm_aim(self, s, f, target_world, raise_=1.0):
        """pistol arm: shoulder -> target, elbow slightly bent (~15 deg), wrist straight; raise_ blends from relaxed"""
        p, yw = self.at(f); Ry = yawM(yw)
        Sw = p + Ry @ Vector((self.sh[s].x, self.sh[s].y, self.sh[s].z)) if not self.seated else None
        d = (Vector(target_world) - Sw); d.z = d.z; dn = d.normalized()
        W = Sw + dn * (self.arm_len[s] * 0.93)
        sx = 1 if s == "L" else -1
        side = Vector((0, 0, 1)).cross(dn).normalized()
        palm = (-side * sx * 0.8 + Vector((0, 0, -0.6))).normalized()      # palm faces in and a little down: a natural one-hand grip
        el = Sw + dn * self.arm_len[s] * 0.5 + Vector((0, 0, -0.35)) + side * (-sx) * 0.25
        self.H.key_hand(s, f, W, dn, palm, pole=el)
        return W, dn

def breathe(P, f0, f1, base_pos, yaw, step=12, amp=1.2, seed=0, head_keys=None, flex=0.0):
    rng = random.Random(seed)
    for f in range(f0, f1 + 1, step):
        b = math.sin((f + seed * 17) / 38.0 * 2 * math.pi)
        hd = head_keys(f) if head_keys else (0.0, 0.0)
        P.key_body(f, base_pos, yaw=yaw, flex=flex, spine=(amp * b, 0.0, 0.0), head=hd)

def blink_eyes(rig, frames):
    """quick blinks via the eyelid bones (MPFB orbicularis): keyed closed for 4 frames around each frame"""
    pass
