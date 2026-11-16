"""helpers lifted from B04 LincolnAssassination 03_anim.py (Char wrapper, cameras, grips); exec'd by 03_anim.py"""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion
HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.join(HERE, "..", "..", "pipeline")
exec(open(os.path.join(HERE, "00_lib.py")).read())
exec(open(os.path.join(PIPE, "anim_lib.py")).read())
exec(open(os.path.join(PIPE, "hand_poses.py")).read())
exec(open(os.path.join(HERE, "timing.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
sc.frame_start = 1; sc.frame_end = END_FRAME
ST = START; SE = shot_end
V = lambda *a: Vector(a)

CUR_S = [1.0]
def ground_w(x, y): return 0.0

def ground_z(x, y):            # anim_lib calls this with armature-space xy of the character being keyed
    s = CUR_S[0]; return ground_w(x * s, y * s) / s

_kf0 = Human.key_foot
def _kf(self, s, f, xy, yaw, lift=0.0, pitch=0.0):     # MPFB shoe soles dip ~2 cm below the ankle-derived floor line
    _kf0(self, s, f, xy, yaw, lift + 0.035 / CUR_S[0], pitch)
Human.key_foot = _kf
_kr0 = Human.key_root
def _kr(self, f, pos, yaw=0.0, flex=0.0, side=0.0):    # hips rise with the lifted feet (no knee bend from the lift)
    _kr0(self, f, Vector((pos.x, pos.y, pos.z + 0.035 / CUR_S[0])), yaw=yaw, flex=flex, side=side)
Human.key_root = _kr

def yaw_to(d):
    return math.degrees(math.atan2(d.x, -d.y))

class Char:
    def __init__(self, name, height_scale):
        self.o = bpy.data.objects[name]; self.s = height_scale
        self.o.scale = (height_scale,) * 3; self.o.location = (0, 0, 0)
        self.R = Rig(self.o); self.H = Human(self.R)
        for pb in self.o.pose.bones: pb.rotation_mode = 'QUATERNION'
    def use(self): CUR_S[0] = self.s; return self
    def a(self, v): return Vector(v) / self.s                     # world -> armature space
    def root(self, f, pos_w, yaw=0.0, flex=0.0, side=0.0, dz=0.0):
        self.use(); p = self.a(pos_w); p.z = self.H.root_head.z + (ground_w(pos_w[0], pos_w[1]) + dz) / self.s if len(pos_w) == 2 or pos_w[2] is None else p.z
        self.H.key_root(f, p, yaw=yaw, flex=flex, side=side)
    def foot(self, s, f, xy_w, yaw, lift=0.0, pitch=0.0):
        self.use(); self.H.key_foot(s, f, self.a((xy_w[0], xy_w[1], 0)).to_2d(), yaw, lift / self.s, pitch)
    def stand(self, f, pos_w, yaw, crouch=0.02, flex=3.0, head=(0.0, 0.0), twist=0.0, stance=1.0):
        """both feet planted under the hips, root at standing height"""
        self.use(); g = ground_w(*pos_w[:2]); P = self.a((pos_w[0], pos_w[1], 0))
        self.H.key_root(f, Vector((P.x, P.y, g / self.s + self.H.root_head.z - crouch / self.s)), yaw=yaw, flex=flex * 0.5)
        self.H.key_spine(f, flex=flex, twist=twist, head=head)
        for sd in "LR":
            xy = self.H.foot_xy(sd, Vector((P.x, P.y, 0)), yaw)
            if stance != 1.0:
                c = Vector((P.x, P.y)); xy = c + (xy - c) * stance
            self.H.key_foot(sd, f, xy, yaw)
    def world_bone(self, n, f=None):
        if f is not None: sc.frame_set(int(f))
        return self.o.matrix_world @ self.o.pose.bones[n].matrix
    def hand_w(self, s, f, W, d, n, pole_w=None):
        """IK hand: wrist at world W, fingers along d, palm normal n (world)"""
        self.use(); R3 = self.o.matrix_world.to_3x3().normalized().inverted()
        self.H.key_hand(s, f, self.a(W), R3 @ Vector(d), R3 @ Vector(n), None if pole_w is None else self.a(pole_w))
    def hang(self, f, pos_w, yaw, swing=(0.0, 0.0), out=0.11):
        """relaxed hanging arms beside the thighs (slight elbow bend); swing = forward offset (m) per side L,R"""
        Rz = Matrix.Rotation(R_(yaw), 3, 'Z'); g = ground_w(*pos_w[:2])
        for i, sd in enumerate("LR"):
            sx = 1 if sd == "L" else -1
            sh = self.o.data.bones["upperarm01." + sd].head_local * self.s
            W = V(pos_w[0], pos_w[1], g) + Rz @ V(sx * (abs(sh.x) + out * self.s / 1.2), -0.06 - swing[i], sh.z - 0.56 * self.s)
            d = Rz @ V(0, -0.15 - swing[i] * 0.6, -1).normalized(); n = Rz @ V(-sx, 0, 0)
            pole = V(pos_w[0], pos_w[1], g) + Rz @ V(sx * 0.45 * self.s, 0.5, sh.z - 0.3 * self.s)
            self.hand_w(sd, f, W, d, n, pole)

def lin(o):
    ad = o.animation_data
    if not ad or not ad.action: return
    for fc in fcurves_of(ad.action):
        for k in fc.keyframe_points: k.interpolation = 'LINEAR'

def fcurves_of(act):
    try: return list(act.fcurves)
    except Exception:
        out = []
        for L in act.layers:
            for st in L.strips:
                for cb in st.channelbags: out += list(cb.fcurves)
        return out

def const_keys(o, path, f, val, idx=None):
    setattr(o, path, val) if idx is None else None
    o.keyframe_insert(path, frame=f)


def child_of_now(obj, rig, bone, f):
    """Child Of the bone with the inverse set at frame f (prop stays exactly where it is at f)"""
    sc.frame_set(int(f))
    mw = obj.matrix_world.copy()
    c = obj.constraints.new('CHILD_OF'); c.target = rig; c.subtarget = bone
    bpy.context.view_layer.update()
    PBm = rig.matrix_world @ rig.pose.bones[bone].matrix
    c.inverse_matrix = PBm.inverted()
    obj.matrix_world = mw
    obj.location = mw.translation; obj.rotation_euler = mw.to_euler(); obj.scale = mw.to_scale()
    bpy.context.view_layer.update()
    return c


def curl_free(rig, sd, rep, f):
    pr = _pose_rots(rig, sd, "power_fist")
    for k in (3, 4, 5):
        if rep.get("finger%d-3.%s" % (k, sd)) is None:
            for j in (1, 2, 3):
                n = "finger%d-%d.%s" % (k, j, sd); pb = rig.pose.bones[n]
                pb.rotation_quaternion = pr[n]; pb.keyframe_insert("rotation_quaternion", frame=f, group=n)

def key_pole(c, s, f, W):
    n = "Pole_elbow." + s; pb = c.o.pose.bones[n]
    pb.location = c.R.rest(n).to_3x3().inverted() @ (c.a(W) - c.R.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)

CAMS = coll("Cameras")
def camera(shot, keys, lens=35, fstop=None):
    """keys: [(offset, loc, target)] offsets in frames from the shot start (negative = from the end)"""
    cd = bpy.data.cameras.new("CAM_" + shot); cd.lens = lens; cd.clip_start = 0.05; cd.clip_end = 400
    cd.sensor_fit = 'AUTO'; cd.dof.use_dof = False
    co = bpy.data.objects.new("CAM_" + shot, cd); CAMS.objects.link(co)
    tg = bpy.data.objects.new("CAMT_" + shot, None); CAMS.objects.link(tg)
    c = co.constraints.new('TRACK_TO'); c.target = tg; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    s0, s1 = ST[shot], SE(shot)
    for off, loc, tgt in keys:
        f = s0 + off if off >= 0 else s1 + 1 + off
        co.location = loc; co.keyframe_insert("location", frame=f)
        tg.location = tgt; tg.keyframe_insert("location", frame=f)
    m = sc.timeline_markers.new(shot, frame=s0); m.camera = co
    return co

def frame_pts(pts, view, lens, fill=0.7, push=0.0):
    """camera location + target that fit `pts` (world) in a 9:16 frame looking along `view`"""
    v = view.normalized(); r = v.cross(V(0, 0, 1)).normalized(); u = r.cross(v)
    c = sum(pts, V(0, 0, 0)) / len(pts)
    tx = 10.125 / lens; ty = 18.0 / lens
    d = 0.0
    for p in pts:
        q = p - c; x, y, z = q.dot(r), q.dot(u), q.dot(v)
        d = max(d, abs(x) / (tx * fill) - z, abs(y) / (ty * fill) - z)
    d = max(d, 0.3) - push
    return c - v * d, c
