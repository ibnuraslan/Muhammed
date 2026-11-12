"""LegoInNose animation: characters, props, FX, lights, one continuous camera.
blender -b sets.blend --python 03_animate.py -- <out.blend>"""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion, Euler
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
exec(open(os.path.join(HERE, "..", "..", "pipeline", "hand_poses.py")).read())   # shared hand poses + limits (Nov 12)
OUT = sys.argv[sys.argv.index("--") + 1:][0]
random.seed(7)
def ground_z(x, y):
    if 7.75 < x < 8.95 and 1.25 < y < 2.35: return 0.06          # shower tray
    if -1.2 < x < 1.4 and -0.9 < y < 1.0: return 0.012            # rug
    return 0.0
V = lambda *a: Vector(a)
sc = bpy.context.scene
FPS = 60
def F(t): return 1 + round(t * FPS)

# ------------------------------------------------------------------ helpers
def key_vis(obj_names, ranges, f_end=2400):
    """visible (render+viewport) only inside [a, b) ranges"""
    for nm in obj_names:
        o = bpy.data.objects[nm]
        obs = [o] + [c for c in o.children_recursive]
        for ob in obs:      # hide_viewport is keyed too, so scene ray casts (QA) also skip hidden objects
            for attr in ("hide_render", "hide_viewport"):
                setattr(ob, attr, True); ob.keyframe_insert(attr, frame=0)
                for a, b in ranges:
                    setattr(ob, attr, False); ob.keyframe_insert(attr, frame=a)
                    setattr(ob, attr, True); ob.keyframe_insert(attr, frame=b)
def set_const(obj, data_path_prefix=""):
    ad = obj.animation_data
    if not ad or not ad.action: return
    for fc in all_fcurves(ad.action):
        if fc.data_path.startswith(data_path_prefix):
            for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
def all_fcurves(act):
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []):
                out += list(cb.fcurves)
    return out
def const_at(obj, frames):
    """make keys at the given frames CONSTANT (teleports hidden by flashes / walls)"""
    ad = obj.animation_data
    if not ad or not ad.action: return
    for fc in all_fcurves(ad.action):
        for kp in fc.keyframe_points:
            if int(round(kp.co.x)) in frames: kp.interpolation = "CONSTANT"

def face(body, f, **vals):
    kb = bpy.data.objects[body].data.shape_keys.key_blocks
    for k in ("mouth-corner-puller", "mouth-open", "mouth-pursing", "mouth-depression", "mouth-elevation",
              "eyebrows-left-up", "eyebrows-right-up", "eyebrows-left-inner-up", "eyebrows-right-inner-up",
              "eyebrows-left-down", "eyebrows-right-down", "eye-left-opened-up", "eye-right-opened-up",
              "eye-left-slit", "eye-right-slit", "nose-left-dilatation", "nose-right-dilatation", "nose-compression"):
        v = vals.get(k.replace("-", "_"), 0.0)
        for alias, keys in (("smile", ("mouth-corner-puller",)), ("open", ("mouth-open",)), ("brows", ("eyebrows-left-up", "eyebrows-right-up")),
                            ("worry", ("eyebrows-left-inner-up", "eyebrows-right-inner-up")), ("frown", ("eyebrows-left-down", "eyebrows-right-down")),
                            ("wide", ("eye-left-opened-up", "eye-right-opened-up")), ("squint", ("eye-left-slit", "eye-right-slit")),
                            ("flare", ("nose-left-dilatation", "nose-right-dilatation")), ("purse", ("mouth-pursing",)), ("sad", ("mouth-depression",))):
            if k in keys and alias in vals: v = vals[alias]
        kb["expr_" + k].value = v; kb["expr_" + k].keyframe_insert("value", frame=f)

def pose(c, s, f, name, amount=1.0):
    """hand_poses.apply_pose wrapper: never hand-set finger angles"""
    apply_pose(c.arm, s, name, f, amount=amount)
def fingers(r, s, f, curl=0.0, index=None, thumb=None, spread=0.0):
    """curl 0..1 for fingers 3-5 (and index/thumb if given)"""
    def rot(n, a, ax="X"):
        pb = r.PB[n]; q = Quaternion(Vector((1, 0, 0)) if ax == "X" else Vector((0, 0, 1)), a)
        pb.rotation_quaternion = q; pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
    for fi in (2, 3, 4, 5):
        c = (index if (fi == 2 and index is not None) else curl)
        for j, w in ((1, 0.9), (2, 1.2), (3, 0.9)):
            rot("finger%d-%d.%s" % (fi, j, s), R_(c * 70 * w))
    tc = thumb if thumb is not None else curl * 0.5
    for j, w in ((2, 0.8), (3, 0.8)):
        rot("finger1-%d.%s" % (j, s), R_(tc * 45 * w))

class Char:
    def __init__(self, name):
        self.name = name; self.arm = bpy.data.objects[name]
        self.h = Human(make_human_ctrl(self.arm)); self.r = self.h.r; self.body = name + "_Body"
        add_hand_limits(self.arm)
        self.nose_rest = None
    def bone_world(self, n, tail=False):
        pb = self.r.PB[n]; return self.arm.matrix_world @ (pb.tail if tail else pb.head)
    def head_M(self):
        return self.arm.matrix_world @ self.r.PB["head"].matrix @ self.r.BN["head"].matrix_local.inverted()
    def nose(self, side=0.0):
        """nose tip (side=0) or nostril (side=+1 left / -1 right) in world, current frame"""
        p = Vector(NOSE_REST_C[self.name])
        if side: p = p + Vector((0.0085 * side * self.s, 0.007 * self.s, -0.013 * self.s))
        return self.head_M() @ p
    def pinch(self, s):
        return (self.bone_world("finger1-3." + s, True) + self.bone_world("finger2-3." + s, True)) / 2

NOSE_REST = sc["NOSE_TIP_REST"]
# per-character nose tip in rest space: lowest-y vertex near the head-bone height
NOSE_REST_C = {}
for nm in ("Boy", "Teen", "Man", "Mom"):
    body = bpy.data.objects[nm + "_Body"]; arm = bpy.data.objects[nm]
    arm.data.pose_position = "REST"; bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); ob = body.evaluated_get(dg); me_ = ob.to_mesh()
    hz = arm.data.bones["head"].head_local.z; hx = arm.data.bones["head"].head_local.x
    Mw = arm.matrix_world.inverted() @ body.matrix_world
    vs = [Mw @ v.co for v in me_.vertices]
    vs = [v for v in vs if abs(v.z - hz) < 0.06 and abs(v.x - hx) < 0.02]
    NOSE_REST_C[nm] = list(min(vs, key=lambda v: v.y)); ob.to_mesh_clear()
    arm.data.pose_position = "POSE"
for o in bpy.data.objects:
    if o.type == "ARMATURE": o.location = (0, 0, 0)
B, T, M, W = Char("Boy"), Char("Teen"), Char("Man"), Char("Mom")
for c in (B, T, M, W):
    c.s = 1.0 if c.name == "Boy" else 1.25
print("NOSES", {k: [round(x, 3) for x in v] for k, v in NOSE_REST_C.items()})

# ------------------------------------------------------------------ poses
BOYP = V(0.15, 0.15, 0.0)
def sit_floor(c, f, pos, yaw=0.0, lean=5.0, side=0.0, twist=0.0, head=(0, 0), legs=(0.17, 0.52), root_z=None, knee_up=0.55, feet_lift=0.02):
    h = c.h; rz = root_z if root_z is not None else 0.11 * (c.r.BN["root"].head_local.z / 0.684)
    h.key_root(f, V(pos.x, pos.y, rz), yaw=yaw, flex=lean * 0.4, side=side * 0.5)
    h.key_spine(f, flex=lean, twist=twist, side=side, head=head)
    Rz = Matrix.Rotation(R_(yaw), 3, "Z")
    sc_ = c.r.BN["root"].head_local.z / 0.684
    for s, sx in (("L", 1), ("R", -1)):
        xy = pos + Rz @ V(sx * legs[0] * sc_, -legs[1] * sc_, 0)
        h.key_foot(s, f, xy.to_2d(), yaw + sx * 12, lift=feet_lift, pitch=-55)
        pole = pos + Rz @ V(sx * 0.2 * sc_, -0.25 * sc_, knee_up * sc_ + 0.3)
        n = "Pole_knee." + s; pb = c.r.PB[n]
        pb.location = c.r.rest(n).to_3x3().inverted() @ (pole - c.r.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)

def hand_at(c, s, f, tip, d, n, pole=None):
    """put the pinch point (thumb+index tips) of hand s at world 'tip' (hand rest offset); d: finger direction, n: palm normal"""
    r = c.r; wr = r.BN["wrist." + s].head_local
    pt = (r.BN["finger1-3." + s].tail_local + r.BN["finger2-3." + s].tail_local) / 2
    dd = r.BN["finger3-1." + s].head_local - wr
    aa = r.BN["finger2-1." + s].head_local - r.BN["finger5-1." + s].head_local
    nn = dd.cross(aa) if s == "L" else aa.cross(dd)
    def basis(d_, n_):
        d_ = d_.normalized(); n_ = (n_ - d_ * n_.dot(d_)).normalized()
        a_ = d_.cross(n_) if s == "R" else n_.cross(d_)
        return Matrix((d_, a_, n_)).transposed()
    Rm = basis(d, n) @ basis(dd, nn).transposed()
    W_ = tip - Rm @ (pt - wr) * 0.85
    c.h.key_hand(s, f, W_, d, n, pole)

def hand_rest_on(c, s, f, W_, yaw=0.0, pole=None):
    """flat hand on a surface (palm down), fingers forward"""
    fw = Matrix.Rotation(R_(yaw), 3, "Z") @ V(0, -1, 0)
    c.h.key_hand(s, f, W_, (fw + V(0, 0, -0.25)).normalized(), V(0, 0, -1), pole)

# ================================================================== BOY (beats 1-7, rug)
b = B
def bk(f, **k): sit_floor(b, f, BOYP, **k)
TUBW = V(-0.27, 0.0, 0.0)
for f, kw in ((1, dict(lean=18, head=(22, 0), twist=-8)), (60, dict(lean=12, head=(12, 0))), (110, dict(lean=4, head=(-6, 0))),
              (150, dict(lean=0, head=(-14, 4))), (190, dict(lean=6, head=(-4, -8), side=4)), (230, dict(lean=4, head=(-8, 8), side=-4)),
              (275, dict(lean=26, twist=-22, side=-10, head=(25, -10))), (330, dict(lean=30, twist=-26, side=-12, head=(28, -12))),
              (380, dict(lean=12, twist=-8, head=(10, -4))), (440, dict(lean=4, head=(0, 0))),
              (520, dict(lean=2, head=(-4, 6))), (580, dict(lean=0, head=(-6, -4))), (640, dict(lean=-6, head=(-12, 0), side=2)),
              (690, dict(lean=-8, head=(-16, 3))), (740, dict(lean=0, head=(-18, 0))),
              (800, dict(lean=-2, head=(-12, 0))), (880, dict(lean=-4, head=(-10, 0))),
              (900, dict(lean=-18, head=(-8, 10), side=6)), (915, dict(lean=-10, head=(-6, -12), side=-8)), (930, dict(lean=-20, head=(-10, 12), side=8)),
              (950, dict(lean=-6, head=(-8, -8), side=-4)), (1000, dict(lean=0, head=(-10, 18), twist=8)), (1040, dict(lean=-4, head=(-14, 22), twist=10)),
              (1070, dict(lean=-8, head=(-6, 16), twist=8)), (1100, dict(lean=6, head=(6, 10), twist=6)), (1360, dict(lean=6, head=(6, 10), twist=6))):
    bk(f, **kw)
# boy hands
b_tip_R = {}
def boyR(f, tip, d=V(0, 0.2, 1), n=V(-1, 0, 0), pole=None):
    hand_at(b, "R", f, tip, d, n, pole); b_tip_R[f] = tip
# right hand: hold red brick at chest -> nose -> push -> wiggle; to tub; yellow up; dream; push yellow; panic flaps
ev(1)
for f in (1, 60, 110, 128, 140, 150, 170, 190, 210, 230, 250, 275, 300, 330, 360, 400, 440, 480, 560, 620, 660, 690, 715, 740):
    ev(f)
# (hand targets are keyed after the body so that the nose can be read per frame)
NOSE_FR = {}
def nose_at(f, side=1.0):
    ev(f); return b.nose(side)
hand_keys_R = []
for f, what in ((1, "chest"), (60, "chest_up"), (110, "near_nose"), (128, "at_nose"), (140, "push"), (150, "push2"), (170, "wiggle_a"),
                (190, "wiggle_b"), (210, "wiggle_a"), (232, "pull"), (255, "drop"), (290, "tub"), (315, "tub_dig"), (335, "tub_pick"),
                (370, "lift"), (410, "show"), (450, "show2"), (520, "show3"), (600, "show2"), (650, "proud"), (690, "near_nose"),
                (712, "at_nose"), (735, "push"), (760, "push2"), (800, "pull"), (870, "pull"), (895, "flapA"), (910, "flapB"), (925, "flapA"),
                (940, "flapB"), (960, "flapA"), (985, "lap"), (1360, "lap")):
    ev(f)
    nz = b.nose(1.0); nt = b.nose(0.0)
    hm = b.head_M(); fw = (hm.to_3x3() @ V(0, -1, 0)).normalized(); up = (hm.to_3x3() @ V(0, 0, 1)).normalized()
    chest = b.bone_world("spine02") + V(0, -0.16, 0.02)
    sh = b.bone_world("upperarm01.R")
    if what == "chest": tip, d, n = chest + V(-0.06, -0.06, 0.05), V(0.3, -0.4, 0.6), V(-1, 0, 0.3)
    elif what == "chest_up": tip, d, n = chest + V(-0.03, -0.1, 0.15), V(0.4, -0.3, 0.7), V(-1, 0, 0.2)
    elif what == "near_nose": tip, d, n = nz + fw * 0.06 - up * 0.035, (up * 1.0 - fw * 0.4 + V(0.3, 0, 0)).normalized(), V(-1, 0, 0)
    elif what == "at_nose": tip, d, n = nz + fw * 0.012 - up * 0.012, (up - fw * 0.5 + V(0.3, 0, 0)).normalized(), V(-1, 0, 0)
    elif what in ("push", "push2"): tip, d, n = nz + fw * 0.004 - up * (0.006 if what == "push" else 0.002), (up - fw * 0.4 + V(0.3, 0, 0)).normalized(), V(-1, 0, 0)
    elif what == "wiggle_a": tip, d, n = nz + fw * 0.01 - up * 0.008 + V(0.006, 0, 0), (up - fw * 0.5 + V(0.5, 0, 0)).normalized(), V(-1, 0, 0)
    elif what == "wiggle_b": tip, d, n = nz + fw * 0.01 - up * 0.008 - V(0.006, 0, 0), (up - fw * 0.5).normalized(), V(-1, 0, 0)
    elif what == "pull": tip, d, n = nz + fw * 0.03 - up * 0.02, (up - fw * 0.5 + V(0.3, 0, 0)).normalized(), V(-1, 0, 0)
    elif what == "drop": tip, d, n = chest + V(-0.12, -0.12, 0.0), V(-0.3, -0.5, -0.6), V(-1, 0, 0)
    elif what == "tub": tip, d, n = TUBW + V(0.03, -0.02, 0.17), V(-0.3, -0.3, -1), V(0.3, 0, -1)
    elif what == "tub_dig": tip, d, n = TUBW + V(0.0, -0.03, 0.095), V(-0.2, -0.3, -1), V(0.3, 0, -1)
    elif what == "tub_pick": tip, d, n = TUBW + V(0.02, -0.02, 0.105), V(-0.2, -0.4, -1), V(0.3, 0, -1)
    elif what == "lift": tip, d, n = chest + V(-0.15, -0.12, 0.08), V(0.2, -0.5, 0.6), V(-1, 0, 0.2)
    elif what == "show": tip, d, n = nt + fw * 0.17 - up * 0.04 + V(-0.03, 0, 0), V(0.5, -0.2, 0.8), V(-0.6, -0.6, 0)
    elif what == "show2": tip, d, n = nt + fw * 0.18 - up * 0.06 + V(-0.05, 0, 0), V(0.5, -0.2, 0.8), V(-0.6, -0.6, 0)
    elif what == "show3": tip, d, n = nt + fw * 0.2 - up * 0.08 + V(-0.08, 0, 0), V(0.4, -0.2, 0.8), V(-0.6, -0.6, 0)
    elif what == "proud": tip, d, n = nt + fw * 0.22 - up * 0.02 + V(-0.08, 0, 0), V(0.3, -0.1, 1.0), V(-0.7, -0.5, 0)
    elif what == "flapA": tip, d, n = sh + V(-0.2, -0.12, 0.22), V(-0.4, -0.2, 1.0), V(0, -1, 0)
    elif what == "flapB": tip, d, n = sh + V(-0.26, -0.18, 0.05), V(-0.6, -0.3, 0.6), V(0, -1, 0)
    elif what == "lap": tip, d, n = BOYP + V(-0.12, -0.18, 0.18), V(0.3, -0.6, -0.5), V(0, 0, -1)
    hand_keys_R.append((f, what, tip.copy()))
    boyR(f, tip, d, n, pole=sh + V(-0.35, 0.15, -0.25))
# left hand: on the floor (support) / on the knee, flaps in the panic, chin during the tweezers
for f, what in ((1, "knee"), (230, "knee"), (275, "knee"), (420, "knee"), (640, "chest"), (700, "knee"), (880, "knee"), (895, "flapB"), (910, "flapA"),
                (925, "flapB"), (940, "flapA"), (960, "flapB"), (990, "knee"), (1360, "knee")):
    ev(f)
    sh = b.bone_world("upperarm01.L")
    if what == "floor": W_ = BOYP + V(0.24, 0.12, 0.062); b.h.key_hand("L", f, W_, V(0.3, -0.85, -0.22).normalized(), V(0, 0, -1), sh + V(0.4, 0.1, -0.1))
    elif what == "knee": W_ = BOYP + V(0.16, -0.24, 0.27); b.h.key_hand("L", f, W_, V(0.0, -0.6, -0.6).normalized(), V(0, 0, -1), sh + V(0.4, 0.1, -0.1))
    elif what == "chest": W_ = b.bone_world("spine02") + V(0.08, -0.13, -0.02); b.h.key_hand("L", f, W_, V(-1, -0.2, 0).normalized(), V(0, 1, 0), sh + V(0.4, 0.1, -0.2))
    elif what == "flapA": W_ = sh + V(0.22, -0.12, 0.22); b.h.key_hand("L", f, W_, V(0.4, -0.2, 1.0).normalized(), V(0, -1, 0), sh + V(0.4, 0.2, -0.1))
    elif what == "flapB": W_ = sh + V(0.27, -0.18, 0.05); b.h.key_hand("L", f, W_, V(0.6, -0.3, 0.6).normalized(), V(0, -1, 0), sh + V(0.4, 0.2, -0.1))
# fingers
for f, nm_ in ((1, "pinch"), (240, "pinch"), (262, "relaxed"), (300, "relaxed"), (325, "pinch"), (338, "pinch"), (880, "pinch"),
               (893, "open_alarm"), (975, "open_alarm"), (995, "relaxed")):
    pose(b, "R", f, nm_)
for f, nm_ in ((1, "relaxed"), (885, "relaxed"), (893, "open_alarm"), (975, "open_alarm"), (995, "relaxed")):
    pose(b, "L", f, nm_)
# face (Boy)
for f, kw in ((1, dict(brows=0.2)), (60, dict(brows=0.35, smile=0.2)), (128, dict(squint=0.3, purse=0.3)), (150, dict(wide=0.6, open=0.25, flare=0.6)),
              (190, dict(worry=0.5, squint=0.3, flare=0.5)), (230, dict(worry=0.4, sad=0.3)), (300, dict(brows=0.3)), (400, dict(smile=0.4, brows=0.5)),
              (470, dict(smile=0.6, brows=0.6, wide=0.3)), (530, dict(smile=0.8, brows=0.7, open=0.2, wide=0.4)), (600, dict(smile=0.7, brows=0.5)),
              (640, dict(smile=1.0, brows=0.6, squint=0.2)), (690, dict(smile=0.8, brows=0.4, purse=0.1)), (720, dict(squint=0.5, purse=0.4)),
              (760, dict(wide=0.5, flare=0.7)), (880, dict(wide=0.8, worry=0.8, open=0.4)), (900, dict(wide=1.0, worry=1.0, open=0.9, sad=0.4)),
              (950, dict(wide=0.9, worry=0.9, open=0.7, sad=0.3)), (1000, dict(worry=0.7, squint=0.4, sad=0.3)), (1050, dict(squint=0.7, open=0.3)),
              (1075, dict(smile=0.5, brows=0.3)), (1100, dict(smile=0.6, brows=0.2)), (1360, dict(smile=0.3))):
    face(b.body, f, **kw)
key_vis(["Boy"], [(1, 1395)])

# ================================================================== MOM (beat 6)
w = W
MOMK = BOYP + V(0.5, -0.42, 0)
yaw_mom_k = math.degrees(math.atan2(-(BOYP - MOMK).normalized().x, (BOYP - MOMK).normalized().y)) + 180
def yaw_to(v): return math.degrees(math.atan2(v.x, -v.y))
yaw_mom_k = yaw_to((BOYP - MOMK).to_2d().to_3d())
DOORP = V(3.3, 1.65, 0)
mpath_pts = [(870, DOORP), (905, V(2.3, 1.2, 0)), (940, V(1.1, 0.25, 0)), (965, MOMK + V(0.1, -0.1, 0))]
mpath = catmull([(f, p) for f, p in mpath_pts])
w.h.walk(lambda f: mpath(f), lambda f: yaw_to((mpath(min(965, f + 3)) - mpath(max(870, f - 3)))) if f < 958 else yaw_mom_k, 870, 965,
         stride=0.85, duty=0.55, lift=0.1, bob=0.03, crouch=0.05, lean=12)
def mom_kneel(f, depth, lean, head=(20, 0), twist=0.0):
    hz = w.r.BN["root"].head_local.z
    Rz = Matrix.Rotation(R_(yaw_mom_k), 3, "Z")
    w.h.key_root(f, V(MOMK.x, MOMK.y, hz - depth), yaw=yaw_mom_k, flex=lean * 0.4)
    w.h.key_spine(f, flex=lean, twist=twist, head=head)
    for s, sx in (("L", 1), ("R", -1)):
        knee = MOMK + Rz @ V(sx * 0.12, -0.12, 0)
        foot = MOMK + Rz @ V(sx * 0.13, 0.36, 0)
        w.h.key_foot(s, f, foot.to_2d(), yaw_mom_k, lift=0.02 if depth > 0.3 else 0.0, pitch=70 if depth > 0.3 else 0)
        pole = knee + Rz @ V(0, -0.6, 0.1); n = "Pole_knee." + s; pb = w.r.PB[n]
        pb.location = w.r.rest(n).to_3x3().inverted() @ (pole - w.r.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)
for f, dpt, ln, hd in ((975, 0.25, 25, (20, 0)), (990, 0.52, 22, (25, 0)), (1100, 0.52, 18, (15, 0)), (1140, 0.4, 12, (10, 0))):
    mom_kneel(f, dpt, ln, hd)
# tweezers + chin hold
for f, what in ((965, "reach"), (990, "approach"), (1015, "at_nose"), (1040, "grip"), (1058, "pull"), (1075, "show"), (1100, "show"), (1140, "down")):
    ev(f)
    nz = b.nose(1.0); hm = b.head_M(); fw = (hm.to_3x3() @ V(0, -1, 0)).normalized(); up = (hm.to_3x3() @ V(0, 0, 1)).normalized()
    shR = w.bone_world("upperarm01.R"); shL = w.bone_world("upperarm01.L")
    toward = (nz - shR).normalized()
    if what == "reach": tip = shR + V(0, -0.25, -0.2)
    elif what == "approach": tip = nz + fw * 0.12 + V(0.05, 0, -0.02)
    elif what == "at_nose": tip = nz + fw * 0.075 - up * 0.02
    elif what == "grip": tip = nz + fw * 0.072 - up * 0.022
    elif what == "pull": tip = nz + fw * 0.14 - up * 0.05
    elif what == "show": tip = nz + fw * 0.25 + up * 0.12 + V(0.08, 0, 0)
    else: tip = MOMK + V(0, -0.15, 0.25)
    hand_at(w, "R", f, tip, (toward + V(0, 0, 0.2)).normalized(), V(0, 0, 1), shR + V(0.2, 0.2, -0.3))
    chin = b.bone_world("jaw", True) + fw * 0.015 - up * 0.02
    if what in ("at_nose", "grip", "pull"):
        w.h.key_hand("L", f, chin + V(0.04, 0.0, -0.03), (chin - shL).normalized(), V(-1, 0, 0), shL + V(0.3, 0.2, -0.3))
    elif what in ("reach", "approach"):
        w.h.key_hand("L", f, chin + V(0.15, -0.05, -0.15), (chin - shL).normalized(), V(-1, 0, 0), shL + V(0.3, 0.2, -0.3))
    else:
        w.h.key_hand("L", f, MOMK + V(0.12, -0.2, 0.22), V(0, -0.5, -0.8).normalized(), V(0, 0, -1), shL + V(0.3, 0.2, -0.3))
pose(w, "R", 870, "relaxed"); pose(w, "R", 960, "pinch"); pose(w, "L", 870, "relaxed"); pose(w, "L", 1000, "cup_hold"); pose(w, "L", 1065, "relaxed")
for f, kw in ((870, dict(worry=0.8, open=0.3)), (960, dict(worry=0.7, frown=0.2)), (1015, dict(squint=0.4, purse=0.3)), (1058, dict(wide=0.4, open=0.2)),
              (1075, dict(smile=0.8, brows=0.5)), (1140, dict(smile=0.6))):
    face(w.body, f, **kw)
key_vis(["Mom"], [(870, 1145)])

# ================================================================== TEEN + MAN aging on the rug (beat 8), then the bench (beat 9a,b)
# teen (~15, long-sleeve sweatshirt) hunched over a gamepad; man (33) with a laptop on his thighs: visible ageing + room change
TEEN_PAD = {}
for f in range(1395, 1439, 6):
    sit_floor(T, f, BOYP, lean=18 + 4 * math.sin(f * 0.3), head=(8, 4 * math.sin(f * 0.2)), legs=(0.22, 0.62), knee_up=0.75)
for f in range(1395, 1439, 6):
    ev(f); hm = T.head_M(); fwT = fw_of_c = (hm.to_3x3() @ V(0, -1, 0)).normalized()
    pad = T.bone_world("spine02") + V(0, -0.3, -0.08) + V(0, 0, 0.01 * math.sin(f * 0.9)); TEEN_PAD[f] = pad
    for s, sx in (("L", 1), ("R", -1)):
        hand_at(T, s, f, pad + V(sx * 0.055, 0.0, 0.0), V(-sx * 0.3, -0.5, 0.6).normalized(), V(0, 0.4, 1).normalized(),
                pole=T.bone_world("upperarm01." + s) + V(sx * 0.35, 0.1, -0.3))
        pose(T, s, f, "wrap_grip", amount=0.85 + 0.1 * math.sin(f * 1.3 + sx))
for f, kw in ((1395, dict(squint=0.4, frown=0.3)), (1420, dict(squint=0.5, open=0.2)), (1438, dict(smile=0.3, squint=0.3))):
    face(T.body, f, **kw)
MAN_LAP = {}
for f in range(1440, 1469, 7):
    sit_floor(M, f, BOYP, lean=14, head=(10, 0), legs=(0.18, 0.72), knee_up=0.35)
for f in range(1440, 1469, 7):
    ev(f); kn = (M.bone_world("lowerleg01.L") + M.bone_world("lowerleg01.R")) / 2; hp = M.bone_world("root")
    lap = M.bone_world("spine02") + V(0, -0.32, -0.12); MAN_LAP[f] = lap
    for s, sx in (("L", 1), ("R", -1)):
        tip = lap + V(sx * 0.04, 0.0, 0.005 * math.sin(f * 1.7 + sx))
        hand_at(M, s, f, tip, V(-sx * 0.3, -0.5, 0.6).normalized(), V(0, 0.4, 1).normalized(), pole=M.bone_world("upperarm01." + s) + V(sx * 0.35, 0.1, -0.3))
for f, kw in ((1440, dict(frown=0.4, squint=0.3)), (1468, dict(frown=0.5, sad=0.3, flare=0.4))):
    face(M.body, f, **kw)
BENCH = V(-1.2, 1.98, 0.0)
SEATZ = 0.47
def man_bench(f, lean=10, head=(0, 0), twist=0.0, side=0.0):
    m = M.h; hz = M.r.BN["root"].head_local.z
    m.key_root(f, V(BENCH.x, BENCH.y - 0.05, SEATZ + 0.09), yaw=0, flex=lean * 0.4, side=side * 0.4)
    m.key_spine(f, flex=lean, twist=twist, side=side, head=head)
    for s, sx in (("L", 1), ("R", -1)):
        m.key_foot(s, f, V(BENCH.x + sx * 0.14, BENCH.y - 0.55), sx * 6)
        pole = V(BENCH.x + sx * 0.14, BENCH.y - 1.2, 0.6); n = "Pole_knee." + s; pb = M.r.PB[n]
        pb.location = M.r.rest(n).to_3x3().inverted() @ (pole - M.r.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)
MB_KEYS = ((1470, dict(lean=12, head=(8, 0))), (1500, dict(lean=6, head=(-14, 0))), (1520, dict(lean=14, head=(10, 0))), (1545, dict(lean=4, head=(-12, 4))),
           (1570, dict(lean=10, head=(4, 0))), (1600, dict(lean=10, head=(6, 0))), (1630, dict(lean=14, head=(4, -6))), (1660, dict(lean=8, head=(-8, 0))),
           (1690, dict(lean=-6, head=(-16, 0))), (1708, dict(lean=4, head=(0, 0))), (1720, dict(lean=4, head=(0, 0))))
for f, kw in MB_KEYS: man_bench(f, **kw)
# tissue / inhaler hands
for f, what in ((1470, "lap"), (1495, "sniff"), (1515, "tissue_box"), (1535, "blow"), (1560, "blow2"), (1580, "toss"), (1605, "lap"),
                (1625, "shake1"), (1635, "shake2"), (1645, "shake1"), (1655, "shake2"), (1672, "mouth"), (1706, "mouth"), (1720, "lap")):
    ev(f)
    nt = M.nose(0.0); hm = M.head_M(); fw = (hm.to_3x3() @ V(0, -1, 0)).normalized(); up = (hm.to_3x3() @ V(0, 0, 1)).normalized()
    shR = M.bone_world("upperarm01.R"); shL = M.bone_world("upperarm01.L")
    lap = BENCH + V(0, -0.3, SEATZ + 0.16)
    if what == "lap": tR = lap + V(-0.1, -0.05, 0); tL = lap + V(0.1, -0.05, 0)
    elif what == "sniff": tR = nt + fw * 0.075 - up * 0.03 + V(-0.035, 0, 0); tL = lap + V(0.1, -0.05, 0)
    elif what == "tissue_box": tR = BENCH + V(-0.38, -0.05, SEATZ + 0.12); tL = lap + V(0.1, -0.05, 0)
    elif what in ("blow", "blow2"): tR = nt + fw * 0.06 - up * 0.01 + V(-0.025, 0, 0); tL = lap + V(0.1, -0.05, 0)
    elif what == "toss": tR = BENCH + V(-0.3, -0.6, 0.55); tL = lap + V(0.1, -0.05, 0)
    elif what in ("shake1", "shake2"): tR = shR + V(0.1, -0.35, -0.05 if what == "shake1" else 0.08); tL = lap + V(0.1, -0.05, 0)
    elif what == "mouth": tR = nt + fw * 0.05 - up * 0.06; tL = lap + V(0.1, -0.05, 0)
    hand_at(M, "R", f, tR, (V(0.3, 0, 1) if what != "lap" else V(0, -0.7, -0.5)).normalized(), V(-1, 0, 0) if what != "lap" else V(0, 0, -1), shR + V(-0.3, 0.2, -0.3))
    hand_at(M, "L", f, tL, V(0, -0.7, -0.5).normalized(), V(0, 0, -1), shL + V(0.3, 0.2, -0.3))
for f, nm_ in ((1440, "hold_flat_object"), (1470, "relaxed"), (1505, "relaxed"), (1515, "wrap_grip"), (1582, "wrap_grip"), (1596, "relaxed"),
               (1606, "wrap_grip"), (1718, "wrap_grip"), (1724, "relaxed")):
    pose(M, "R", f, nm_)
for f, nm_ in ((1440, "hold_flat_object"), (1470, "relaxed"), (1530, "relaxed"), (1724, "relaxed")):
    pose(M, "L", f, nm_)
for f, kw in ((1470, dict(squint=0.3, sad=0.3)), (1495, dict(squint=0.6, flare=1.0, purse=0.3)), (1535, dict(squint=0.9, purse=0.6)), (1580, dict(sad=0.5, worry=0.5)),
              (1640, dict(worry=0.6, open=0.2)), (1672, dict(open=0.6, wide=0.4)), (1700, dict(open=0.3, squint=0.3)), (1715, dict(sad=0.4, worry=0.4))):
    face(M.body, f, **kw)

# ================================================================== MAN in bed (beat 9c, night)
BEDP = V(5.1, 1.45, 0.62)      # chest position on the mattress
def man_bed(f, side=0.0, flex=0.0, head=(0, 0), arm=("side", "side"), knee=0.0, sit=0.0):
    m = M.h; hz = M.r.BN["root"].head_local.z
    # lying on the back: root rotated -90 about X so the face points up, head toward +Y (headboard)
    pitch = -90 + sit * 70
    pelvis = V(BEDP.x, BEDP.y - 0.55 + sit * 0.2, BEDP.z - 0.02 + sit * 0.05)
    Rw = Matrix.Rotation(R_(180), 3, "Z")
    m.key_root(f, pelvis, yaw=0, flex=pitch, side=side)
    m.key_spine(f, flex=flex, side=side * 0.5, head=head)
    for s, sx in (("L", -1), ("R", 1)):
        ft = V(BEDP.x + sx * 0.16, BEDP.y - 1.3 + knee * 0.35 + sit * 0.15, BEDP.z - 0.02)
        m.key_foot(s, f, ft.to_2d(), sx * 10, lift=BEDP.z - 0.02, pitch=-80)
        pole = ft + V(0, 0.3, 0.6 + knee); n = "Pole_knee." + s; pb = M.r.PB[n]
        pb.location = M.r.rest(n).to_3x3().inverted() @ (pole - M.r.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)
BED_KEYS = ((1724, dict(side=0, head=(0, 10))), (1745, dict(side=-8, head=(0, -10))), (1775, dict(side=25, head=(0, 30), knee=0.3)), (1800, dict(side=-25, head=(-10, -30), knee=0.1)),
            (1820, dict(side=10, head=(-25, 0))), (1835, dict(side=-5, head=(-10, -10), knee=0.2)), (1852, dict(sit=0.7, head=(10, 0))), (1868, dict(sit=0.75, head=(8, 6))))
for f, kw in BED_KEYS: man_bed(f, **kw)
for f, kw in ((1724, dict(squint=1.0)), (1775, dict(squint=1.0, open=0.4, frown=0.5)), (1800, dict(squint=1.0, open=0.9, worry=0.6)), (1820, dict(squint=0.8, open=1.0, flare=1.0)),
              (1840, dict(wide=0.6, open=0.6, worry=0.7)), (1855, dict(wide=0.4, frown=0.5, sad=0.3)), (1868, dict(worry=0.5, frown=0.4))):
    face(M.body, f, **kw)
for f in (1724, 1800, 1852, 1868):
    ev(f)
    for s in "LR":
        sh = M.bone_world("upperarm01." + s); sx = 1 if s == "R" else -1
        W_ = sh + V(sx * 0.25, -0.35 if f != 1800 else 0.1, -0.12 if f < 1852 else -0.25); W_.z = max(W_.z, 0.64)
        M.h.key_hand(s, f, W_, V(0, -1, 0.15).normalized(), V(0, 0, -1))

# ================================================================== MAN in the shower (beats 10-11)
SHW = V(8.35, 1.8, 0.06)
yaw_sh = -60
def man_shower(f, lean=0.0, head=(0, 0), twist=0.0, side=0.0):
    m = M.h; hz = M.r.BN["root"].head_local.z
    m.key_root(f, V(SHW.x, SHW.y, SHW.z + hz - 0.02), yaw=yaw_sh, flex=lean * 0.4)
    m.key_spine(f, flex=lean, twist=twist, side=side, head=head)
    for s in "LR":
        xy = m.foot_xy(s, V(SHW.x, SHW.y, 0), yaw_sh)
        m.key_foot(s, f, xy, yaw_sh + (8 if s == "L" else -8), lift=SHW.z)
SH_KEYS = ((1870, dict(head=(-20, 0))), (1930, dict(head=(-10, 10), lean=4)), (1960, dict(head=(4, 0), lean=6)), (1990, dict(head=(6, 0), lean=8)),
           (2020, dict(head=(8, 0), lean=10)), (2060, dict(head=(6, 0), lean=8)), (2085, dict(head=(10, 0), lean=12)), (2100, dict(head=(4, 0), lean=6)),
           (2150, dict(head=(20, 0), lean=14)), (2200, dict(head=(18, 0), lean=12)), (2230, dict(head=(-20, 0), lean=-6)), (2250, dict(head=(-26, 4), lean=-10, side=4)),
           (2270, dict(head=(-18, -4), lean=-4, side=-4)), (2290, dict(head=(-24, 4), lean=-8, side=4)), (2310, dict(head=(-14, 0), lean=-2)))
for f, kw in SH_KEYS: man_shower(f, **kw)
M_PALM = {}
for f, what in ((1870, "wash"), (1910, "wash2"), (1935, "wash"), (1960, "press"), (2077, "press"), (2090, "palm"), (2150, "palm"), (2200, "palm_up"), (2310, "palm_up")):
    ev(f)
    nt = M.nose(0.0); hm = M.head_M(); fw = (hm.to_3x3() @ V(0, -1, 0)).normalized(); up = (hm.to_3x3() @ V(0, 0, 1)).normalized()
    rt = (hm.to_3x3() @ V(-1, 0, 0)).normalized()
    shR = M.bone_world("upperarm01.R"); shL = M.bone_world("upperarm01.L")
    if what in ("wash", "wash2"):
        hd = M.bone_world("head", True)
        tR = hd + rt * 0.06 + fw * 0.05 + V(0, 0, 0.02 if what == "wash" else -0.02); tL = hd - rt * 0.06 + fw * 0.05 + V(0, 0, -0.02 if what == "wash" else 0.02)
        dR, nR, dL, nL = V(0, 0, 1), -rt, V(0, 0, 1), rt
    elif what == "press":
        tR = nt + rt * 0.012 + fw * 0.004; dR, nR = (up + rt * 0.3).normalized(), -rt
        tL = shL + fw * 0.38 - up * 0.22 - rt * 0.08; dL, nL = fw, up
    else:
        tR = shR + rt * 0.1 + fw * 0.02 - up * 0.5; dR, nR = (-up + fw * 0.2).normalized(), rt
        cup = nt + fw * (0.2 if what == "palm" else 0.24) - up * (0.2 if what == "palm" else 0.12)
        tL = cup; dL, nL = (fw + rt * 0.3).normalized(), up
        M_PALM[f] = cup.copy()
    bk_ = -fw
    hand_at(M, "R", f, tR, dR, nR, shR + rt * 0.45 - up * 0.35 + bk_ * 0.25)
    hand_at(M, "L", f, tL, dL, nL, shL - rt * 0.45 - up * 0.35 + bk_ * 0.25)
for f, nm_ in ((1870, "relaxed"), (1945, "relaxed"), (1958, "point"), (2077, "point"), (2088, "relaxed")):
    pose(M, "R", f, nm_)
for f, nm_ in ((1870, "relaxed"), (2077, "relaxed"), (2088, "cup_hold")):
    pose(M, "L", f, nm_)
for f, kw in ((1870, dict(squint=0.6, sad=0.2)), (1960, dict(squint=0.7, purse=0.3)), (1990, dict(squint=1.0, purse=0.8, flare=1.0)), (2040, dict(squint=1.0, purse=1.0, flare=1.0)),
              (2085, dict(squint=1.0, purse=1.0, flare=1.0)), (2095, dict(wide=1.0, open=0.5, brows=0.8)), (2150, dict(wide=1.0, open=0.6, brows=1.0)),
              (2200, dict(wide=0.6, brows=0.8, open=0.3, smile=0.3)), (2230, dict(smile=1.0, open=0.8, squint=0.4, brows=0.4)), (2310, dict(smile=1.0, open=0.6, squint=0.5))):
    face(M.body, f, **kw)
key_vis(["Teen"], [(1395, 1440)])
key_vis(["Man"], [(1440, 2400)])
# man's clothes off in the shower
for o in bpy.data.objects["Man"].children:
    if "casualsuit" in o.name or "shoes" in o.name:
        o.hide_render = False; o.keyframe_insert("hide_render", frame=1440)
        o.hide_render = True; o.keyframe_insert("hide_render", frame=1870)
# MPFB hides the skin under clothes with mask modifiers: show the whole body in the shower
for ob in [bpy.data.objects["Man_Body"]]:
    for md in ob.modifiers:
        if md.type == "MASK" and md.name.startswith("Delete"):
            md.show_render = True; md.keyframe_insert("show_render", frame=1); md.show_viewport = True; md.keyframe_insert("show_viewport", frame=1)
            md.show_render = False; md.keyframe_insert("show_render", frame=1870); md.show_viewport = False; md.keyframe_insert("show_viewport", frame=1870)
            print("MASK_OFF", ob.name, md.name)
const_at(M.arm, {1468, 1720, 1868})

print("CHAR_DONE")
exec(open(os.path.join(HERE, "03b_props_fx_camera.py")).read())
bpy.ops.wm.save_as_mainfile(filepath=OUT)
