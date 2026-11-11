# Human pose helpers for MPFB 'default' rigs (exec'd after pipeline/anim_lib.py).
# FK body/legs, IK hands in armature space, finger curls, face shape keys.
import math
import bpy
from mathutils import Vector, Matrix, Quaternion

SPINE_W = {"spine05": 0.12, "spine04": 0.18, "spine03": 0.22, "spine02": 0.26, "spine01": 0.22}
HEAD_W = {"neck01": 0.25, "neck02": 0.25, "neck03": 0.2, "head": 0.3}
JW = (0.8, 1.1, 0.8)

class Person:
    def __init__(self, rig_obj):
        self.o = rig_obj
        self.R = make_human_ctrl(rig_obj)
        R = self.R
        self.root_head = R.BN["root"].head_local.copy()
        self.sh = {s: R.BN["upperarm01." + s].head_local.copy() for s in "LR"}
        self.rest_hand = {}
        for s in "LR":
            wv = R.BN["wrist." + s].head_local
            d = R.BN["finger3-1." + s].head_local - wv
            a = R.BN["finger2-1." + s].head_local - R.BN["finger5-1." + s].head_local
            n = d.cross(a) if s == "L" else a.cross(d)
            self.rest_hand[s] = self.basis(s, d, n)
        self.body = next(c for c in rig_obj.children if c.type == 'MESH' and c.name.endswith(".body"))
        # IK hand constraint influence animatable: start with IK on
    @staticmethod
    def basis(s, d, n):
        d = d.normalized(); n = (n - d * n.dot(d)).normalized()
        a = d.cross(n) if s == "R" else n.cross(d)
        return Matrix((d, a, n)).transposed()
    def hand_matrix(self, s, W, d, n):
        Rm = self.basis(s, d, n) @ self.rest_hand[s].transposed()
        wr = self.R.BN["wrist." + s].head_local
        return Matrix.Translation(W) @ Rm.to_4x4() @ Matrix.Translation(-wr) @ self.R.rest("IK_hand." + s)
    def key_hand(self, s, f, W, d, n, pole=None):
        """W wrist (armature space), d = wrist->middle-finger direction, n = palm normal side (back of hand for L, see test)"""
        self.R.key_world("IK_hand." + s, f, self.hand_matrix(s, Vector(W), Vector(d), Vector(n)))
        if pole is not None:
            nme = "Pole_elbow." + s; pb = self.R.PB[nme]
            pb.location = self.R.rest(nme).to_3x3().inverted() @ (Vector(pole) - self.R.BN[nme].head_local)
            pb.keyframe_insert("location", frame=f, group=nme)
    def key_body(self, f, pos, yaw=0.0, pitch=0.0, roll=0.0, spine=(0, 0, 0), head=(0, 0, 0), legs=None, jaw=0.0):
        R = self.R
        Rw = (Matrix.Rotation(R_(yaw), 3, 'Z') @ Matrix.Rotation(R_(pitch), 3, 'X') @ Matrix.Rotation(R_(roll), 3, 'Y'))
        M = Matrix.Translation(Vector(pos)) @ Rw.to_4x4() @ Matrix.Translation(-self.root_head) @ R.rest("root")
        R.key_world("root", f, M)
        fl, sd, tw = spine
        for n, w in SPINE_W.items(): R.key_rot(n, f, [("X", fl * w), ("Y", sd * w), ("Z", tw * w)])
        hp, ht, hr = head
        for n, w in HEAD_W.items(): R.key_rot(n, f, [("X", hp * w), ("Y", hr * w), ("Z", ht * w)])
        if legs is not None:
            for s in "LR":
                sx = 1 if s == "L" else -1
                flex, abd, knee, ank = legs.get(s, (0, 4, 4, 0))
                R.key_rot("upperleg01." + s, f, [("Y", -sx * abd), ("X", -flex)])
                R.key_rot("lowerleg01." + s, f, [("X", knee)])
                R.key_rot("foot." + s, f, [("X", -ank)])
        R.key_rot("jaw", f, [("X", -jaw)])
    def key_fingers(self, s, f, curl, thumb=18):
        """curl = degrees (or [index, middle, ring, pinky]); bone-local +X curls toward the palm (tested on MPFB 'default')"""
        for k in range(2, 6):
            c = curl[k - 2] if isinstance(curl, (list, tuple)) else curl
            for j in range(1, 4):
                b = "finger%d-%d.%s" % (k, j, s); pb = self.R.PB[b]
                q = Quaternion((1, 0, 0), R_(max(5.0, c) * JW[j - 1]))
                if pb.rotation_quaternion.dot(q) < 0: q = -q
                pb.rotation_quaternion = q; pb.keyframe_insert("rotation_quaternion", frame=f, group=b)
        for j, w in ((1, 0.25), (2, 0.6), (3, 0.8)):
            b = "finger1-%d.%s" % (j, s); pb = self.R.PB[b]
            q = Quaternion((1, 0, 0), R_(thumb * w)); pb.rotation_quaternion = q; pb.keyframe_insert("rotation_quaternion", frame=f, group=b)
    def limit_hands(self):
        """no backward finger bends; wrist within a natural range"""
        for s in "LR":
            for k in range(1, 6):
                for j in range(1, 4):
                    pb = self.R.PB["finger%d-%d.%s" % (k, j, s)]
                    c = pb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'
                    c.use_limit_x = c.use_limit_y = c.use_limit_z = True
                    c.min_x, c.max_x = R_(-5), R_(100); c.min_y, c.max_y = R_(-15), R_(15); c.min_z, c.max_z = R_(-15), R_(15)
    def ik(self, s, f, on):
        """switch arm IK on/off (off = FK arm hangs from its keyed rotations)"""
        c = self.R.PB["lowerarm02." + s].constraints[0]; c.influence = 1.0 if on else 0.0; c.keyframe_insert("influence", frame=f)
        cr = self.R.PB["wrist." + s].constraints[0]; cr.influence = c.influence; cr.keyframe_insert("influence", frame=f)
    def face(self, f, **w):
        kb = self.body.data.shape_keys.key_blocks
        for k, v in w.items():
            for nm in (k.replace("_", "-"),):
                key = kb.get("X_" + nm)
                if key: key.value = v; key.keyframe_insert("value", frame=f)
    def wpos(self, bone, head=True):
        pb = self.R.PB[bone]; M = self.o.matrix_world
        return M @ (pb.head if head else pb.tail)
    def wmat(self, bone):
        return self.o.matrix_world @ self.R.PB[bone].matrix

def FACE_NEUTRAL():
    return dict(eye_left_opened_up=0, eye_right_opened_up=0, eyebrows_left_up=0, eyebrows_right_up=0, eyebrows_left_inner_up=0,
                eyebrows_right_inner_up=0, mouth_open=0, mouth_corner_puller=0, mouth_upward_retraction=0, eye_left_slit=0,
                eye_right_slit=0, eye_left_closure=0, eye_right_closure=0, mouth_compression=0, mouth_depression=0)

def to_local(rig_obj, W):
    return rig_obj.matrix_world.inverted() @ Vector(W)
def dir_local(rig_obj, d):
    return rig_obj.matrix_world.to_3x3().inverted() @ Vector(d)
