"""Control rig + choreography for the 10 s motion test (60 fps, frames 1-600).

blender -b scene.blend --python 03_animate.py -- <out.blend>

Action plan (frame = 60 fps):
  1-14     anticipation: weight onto left foot, lean begins
  10-54    step 1 (right foot) heel-off, toe-off, swing, heel strike, flat
  50-96    step 2 (left foot) -> lands next to the crate, staggered stance
  96-130   decelerate, weight settles forward, small inhale (anticipation of bend)
  125-240  bend: knees + hip hinge + spine flex, right arm reaches, left hand onto left thigh,
           right heel peels up (weight forward), head/eyes on bottle
  240-268  fingers close round bottle (bottle still)
  272-330  lift (bottle leaves crate, slow start), legs begin to push
  290-400  rise: hips/knees extend, left hand pushes off thigh, bottle to chest
  400-432  bottle to lips, head tilts back
  432-478  drink, small swallow
  478-545  bottle leaves lips, lowered to waist, head comes level, exhale
  515-560  right foot steps up beside the left (squaring the stance)
  560-600  settle + breathing
"""
import sys, math
import bpy
from mathutils import Vector, Matrix, Quaternion

OUT = sys.argv[sys.argv.index("--") + 1]
R_ = math.radians
sc = bpy.context.scene
arm = bpy.data.objects["Farmer"]
A = arm.data
GZ = sc["ground_z"]
assert arm.matrix_world == Matrix.Identity(4)

# =============================================================== control rig
bpy.context.view_layer.objects.active = arm
for o in bpy.context.selected_objects:
    o.select_set(False)
arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
eb = A.edit_bones

def dup(src, name):
    s = eb[src]
    b = eb.new(name)
    b.head, b.tail, b.roll = s.head.copy(), s.tail.copy(), s.roll
    b.use_deform = False
    b.parent = None
    return b

def point_bone(name, head):
    b = eb.new(name)
    b.head = head
    b.tail = head + Vector((0, 0, 0.08))
    b.use_deform = False
    return b

for s in "LR":
    dup("foot." + s, "IK_foot." + s)
    dup("wrist." + s, "IK_hand." + s)
    knee = eb["lowerleg01." + s].head
    point_bone("Pole_knee." + s, knee + Vector((0, -0.6, 0)))
    elbow = eb["lowerarm01." + s].head
    sx = 1 if s == "L" else -1
    point_bone("Pole_elbow." + s, elbow + Vector((0.25 * sx, 0.55, -0.1)))
bpy.ops.object.mode_set(mode='POSE')
PB = arm.pose.bones
BN = A.bones

ctrl_coll = A.collections.new("Controls")
for n in ["IK_foot.L", "IK_foot.R", "IK_hand.L", "IK_hand.R", "Pole_knee.L", "Pole_knee.R",
          "Pole_elbow.L", "Pole_elbow.R"]:
    ctrl_coll.assign(BN[n])

for pb in PB:
    pb.rotation_mode = 'QUATERNION'

def add_ik(bone, target, pole, chain):
    c = PB[bone].constraints.new('IK')
    c.target, c.subtarget = arm, target
    c.pole_target, c.pole_subtarget = arm, pole
    c.chain_count = chain
    c.use_tail = True
    c.iterations = 500
    return c

IK = {}
for s in "LR":
    IK["leg" + s] = add_ik("lowerleg02." + s, "IK_foot." + s, "Pole_knee." + s, 4)
    IK["arm" + s] = add_ik("lowerarm02." + s, "IK_hand." + s, "Pole_elbow." + s, 4)
    for twist in ("upperleg02.", "lowerleg02.", "upperarm02.", "lowerarm02."):
        p = PB[twist + s]
        p.lock_ik_x = p.lock_ik_y = p.lock_ik_z = True
    k = PB["lowerleg01." + s]
    k.lock_ik_y = k.lock_ik_z = True
    for bone, tgt in (("foot." + s, "IK_foot." + s), ("wrist." + s, "IK_hand." + s)):
        c = PB[bone].constraints.new('COPY_ROTATION')
        c.target, c.subtarget = arm, tgt

def evaluate(frame=None):
    if frame is not None:
        sc.frame_set(frame)
    else:
        bpy.context.view_layer.update()

# pole angles: brute-force the value that reproduces the rest pose
def calib_pole(key, end_bone, mid_bone):
    c = IK[key]
    rest_mid = BN[mid_bone].head_local.copy()
    best = None
    for deg in range(-180, 180, 5):
        c.pole_angle = R_(deg)
        evaluate()
        err = (PB[mid_bone].head - rest_mid).length
        if best is None or err < best[1]:
            best = (deg, err)
    lo = best[0]
    for deg10 in range((lo - 5) * 10, (lo + 5) * 10):
        c.pole_angle = R_(deg10 / 10)
        evaluate()
        err = (PB[mid_bone].head - rest_mid).length
        if err < best[1]:
            best = (deg10 / 10, err)
    c.pole_angle = R_(best[0])
    print("POLE", key, best)

for s in "LR":
    calib_pole("leg" + s, "lowerleg02." + s, "lowerleg01." + s)
    calib_pole("arm" + s, "lowerarm02." + s, "lowerarm01." + s)

# =============================================================== maths helpers
def rest(n):
    return BN[n].matrix_local.copy()

def rotw(seq):
    """seq of (axis, deg) applied in order, world/anatomical axes.
    X+: top tips forward (-Y) / flex.  Y+: top leans to character's left (+X).
    Z+: turn toward character's left."""
    M = Matrix.Identity(3)
    for ax, d in seq:
        M = Matrix.Rotation(R_(d), 3, ax) @ M
    return M

def local_q(n, Rw):
    R = rest(n).to_3x3().normalized()
    return (R.inverted() @ Rw @ R).to_quaternion()

def key_q(n, f, q):
    pb = PB[n]
    if pb.rotation_quaternion.dot(q) < 0:  # keep shortest path vs previous value
        q = -q
    pb.rotation_quaternion = q
    pb.keyframe_insert("rotation_quaternion", frame=f, group=n)

def key_world(n, f, M):
    """parentless bone: desired armature-space matrix -> basis keys"""
    pb = PB[n]
    basis = rest(n).inverted() @ M
    loc, q, _ = basis.decompose()
    if pb.rotation_quaternion.dot(q) < 0:
        q = -q
    pb.location = loc
    pb.rotation_quaternion = q
    pb.keyframe_insert("location", frame=f, group=n)
    pb.keyframe_insert("rotation_quaternion", frame=f, group=n)

def pchip(keys):
    """monotone cubic through (frame, value) -> callable"""
    xs = [k[0] for k in keys]; ys = [k[1] for k in keys]
    n = len(xs)
    if n == 1:
        return lambda x: ys[0]
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    dl = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    m[0], m[-1] = 0.0, 0.0                 # ease in/out at ends
    for i in range(1, n - 1):
        if dl[i - 1] * dl[i] <= 0:
            m[i] = 0.0
        else:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / dl[i - 1] + w2 / dl[i])
    def f(x):
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        i = max(j for j in range(n - 1) if xs[j] <= x)
        t = (x - xs[i]) / h[i]
        h00 = (1 + 2 * t) * (1 - t) ** 2; h10 = t * (1 - t) ** 2
        h01 = t * t * (3 - 2 * t); h11 = t * t * (t - 1)
        return h00 * ys[i] + h10 * h[i] * m[i] + h01 * ys[i + 1] + h11 * h[i] * m[i + 1]
    return f

class Track:
    """named channels -> union key frames"""
    def __init__(self, **ch):
        self.f = {k: pchip(v) for k, v in ch.items()}
        self.frames = sorted({k[0] for v in ch.values() for k in v})
    def __call__(self, name, x):
        return self.f[name](x)

def merge_frames(*tracks, extra=()):
    return sorted(set(f for t in tracks for f in t.frames) | set(extra))

# =============================================================== BODY (root/pelvis)
ROOT_HEAD = BN["root"].head_local.copy()
Z0 = 0.0  # vertical offsets are relative to rest

root = Track(
    x=[(1, 0.0), (12, 0.028), (30, 0.018), (46, -0.012), (62, -0.022), (78, -0.004), (92, 0.022),
       (130, 0.026), (240, 0.010), (300, 0.018), (400, 0.012), (505, 0.014), (522, 0.045),
       (548, 0.020), (572, 0.004), (600, -0.012)],
    y=[(1, 1.00), (12, 0.985), (30, 0.86), (46, 0.70), (62, 0.52), (78, 0.36), (92, 0.22),
       (108, 0.19), (122, 0.20), (135, 0.205), (180, 0.22), (240, 0.235), (290, 0.235),
       (340, 0.22), (400, 0.22), (470, 0.225), (505, 0.215), (522, 0.19), (548, 0.13), (575, 0.10), (600, 0.095)],
    z=[(1, -0.004), (12, -0.010), (30, -0.004), (46, -0.036), (62, -0.004), (76, -0.006),
       (90, -0.038), (106, -0.034), (122, -0.030), (128, -0.026), (150, -0.08), (200, -0.30),
       (240, -0.352), (256, -0.366), (272, -0.360), (300, -0.31), (340, -0.14), (385, -0.042), (410, -0.036),
       (470, -0.038), (510, -0.046), (530, -0.042), (548, -0.036), (570, -0.016), (600, -0.012)],
    flex=[(1, 2.0), (12, 4.0), (46, 5.0), (90, 6.0), (122, 3.0), (130, 4.0), (200, 27.0),
          (240, 30.0), (258, 32.5), (272, 31.5), (300, 27.0), (340, 14.0), (390, 2.0), (440, -3.0),
          (480, -2.0), (520, 1.0), (560, 1.5), (600, 1.0)],
    side=[(1, 0.0), (12, -1.5), (30, -2.0), (46, 1.0), (62, 2.5), (78, 1.0), (92, -2.0),
          (130, -1.5), (240, -3.0), (300, -2.0), (400, 0.0), (505, -0.5), (522, -3.0),
          (548, -1.0), (600, 0.0)],
    yaw=[(1, 0.0), (20, 1.5), (46, 5.0), (70, 0.0), (90, -5.5), (120, -4.0), (200, -6.0),
         (240, -8.0), (300, -6.0), (400, -3.0), (505, -2.5), (548, -0.5), (600, 0.0)],
)

def root_matrix(f):
    Rw = rotw([("X", root("flex", f)), ("Y", root("side", f)), ("Z", root("yaw", f))])
    delta = Vector((root("x", f), root("y", f), root("z", f)))
    M = Matrix.Translation(ROOT_HEAD + delta) @ Rw.to_4x4() @ Matrix.Translation(-ROOT_HEAD) @ rest("root")
    return M

for f in root.frames:
    key_world("root", f, root_matrix(f))

# =============================================================== spine / neck / head
# torso flex (total, distributed), twist (neg = right shoulder forward), side
spine = Track(
    flex=[(1, 3.0), (12, 4.0), (46, 2.0), (70, 3.0), (90, 2.0), (115, -1.0), (128, -2.0),
          (200, 22.0), (240, 26.0), (258, 28.0), (272, 27.5), (300, 24.0), (340, 13.0), (390, 2.0),
          (420, -4.0), (440, -6.0), (470, -6.5), (490, -3.0), (505, 0.0), (520, 6.0),
          (540, 4.5), (575, 2.5), (600, 3.0)],
    twist=[(1, 0.0), (20, -2.0), (46, -6.0), (70, 0.0), (90, 6.0), (115, 3.0), (150, 6.0),
           (240, 17.0), (270, 17.0), (330, 11.0), (400, 6.0), (440, 5.0), (505, 3.0),
           (548, 1.0), (600, 0.0)],
    side=[(1, 0.0), (46, -1.5), (90, 1.5), (130, 0.0), (240, -6.0), (300, -4.0), (400, -1.0),
          (440, -2.0), (505, -1.0), (600, 0.0)],
)
SPINE_W = {"spine05": 0.12, "spine04": 0.18, "spine03": 0.22, "spine02": 0.26, "spine01": 0.22}
for n, w in SPINE_W.items():
    for f in spine.frames:
        key_q(n, f, local_q(n, rotw([("X", spine("flex", f) * w), ("Y", spine("side", f) * w),
                                       ("Z", spine("twist", f) * w)])))

# head: pitch is *relative to torso*, positive = chin down
head = Track(
    pitch=[(1, 10.0), (46, 13.0), (90, 16.0), (120, 20.0), (160, 14.0), (210, 4.0), (240, 0.0),
           (270, 2.0), (300, 6.0), (350, 8.0), (395, 2.0), (420, -14.0), (440, -22.0),
           (465, -26.0), (478, -24.0), (495, -8.0), (520, 6.0), (545, 2.0), (570, -1.0),
           (600, 9.0)],
    turn=[(1, 0.0), (46, -2.0), (90, -2.0), (130, -8.0), (240, -20.0), (270, -18.0), (300, -14.0),
          (400, -6.0), (440, -6.0), (500, -3.0), (548, 3.0), (572, 1.0), (600, -9.0)],
    tilt=[(1, 0.0), (46, 1.5), (90, -1.5), (130, 0.0), (240, 4.0), (300, 2.0), (420, -3.0),
          (470, -3.0), (520, 0.0), (600, 1.0)],
    swallow=[(1, 0.0), (448, 0.0), (456, 1.0), (464, 0.0), (600, 0.0)],
)
HEAD_W = {"neck01": 0.25, "neck02": 0.25, "neck03": 0.2, "head": 0.3}
for n, w in HEAD_W.items():
    for f in head.frames:
        p = head("pitch", f) * w
        if n == "neck01":
            p += head("swallow", f) * 2.0
        key_q(n, f, local_q(n, rotw([("X", p), ("Y", head("tilt", f) * w), ("Z", head("turn", f) * w)])))

jaw = Track(open=[(1, 0.0), (405, 0.0), (428, 4.0), (470, 4.0), (482, 1.0), (500, 0.5),
                  (515, 3.5), (540, 2.5), (565, 0.0), (600, 0.0)])
for f in jaw.frames:
    key_q("jaw", f, local_q("jaw", rotw([("X", -jaw("open", f))])))

# breathing / exhale on clavicles (positive = shoulders up)
clav = Track(
    up=[(1, 0.0), (60, 1.0), (120, 2.0), (128, 3.0), (200, 0.0), (330, 0.0), (380, 1.5),
        (430, 2.5), (470, 3.0), (505, 3.0), (530, -2.5), (560, -1.0), (582, 1.2), (600, 0.2)],
    fwdR=[(1, 0.0), (130, 0.0), (240, 9.0), (300, 7.0), (380, 3.0), (430, 6.0), (478, 6.0),
          (540, 1.0), (600, 0.0)],
)
for s, sx in (("L", 1), ("R", -1)):
    for f in clav.frames:
        fw = clav("fwdR", f) if s == "R" else 0.0
        key_q("clavicle." + s, f, local_q("clavicle." + s,
              rotw([("Y", -sx * clav("up", f) * 1.2), ("Z", -sx * fw * 0.8)])))

# =============================================================== FEET
FOOT_REST = {s: rest("foot." + s) for s in "LR"}
ANKLE_REST = {s: BN["foot." + s].head_local.copy() for s in "LR"}
BALL = Vector((0, -0.125, -ANKLE_REST["L"].z + GZ))     # ankle -> ball contact (foot frame)
HEEL = Vector((0, 0.05, -ANKLE_REST["L"].z + GZ))       # ankle -> heel contact

def foot_matrix(s, x, y, yaw, pitch, lift=0.0):
    """pitch>0: heel up about ball, pitch<0: toes up about heel. yaw>0 toes toward +X"""
    A0 = Vector((x, y, ANKLE_REST[s].z))
    Ryaw = Matrix.Rotation(R_(yaw), 3, 'Z')
    Rp = Matrix.Rotation(R_(pitch), 3, 'X')
    piv_local = BALL if pitch >= 0 else HEEL
    piv = A0 + Ryaw @ piv_local
    ankle = piv + Ryaw @ (Rp @ (-piv_local)) + Vector((0, 0, lift))
    Rw = Ryaw @ Rp
    M = Matrix.Translation(ankle) @ Rw.to_4x4() @ Matrix.Translation(-ANKLE_REST[s]) @ FOOT_REST[s]
    return M, ankle, Ryaw

# foot plans: (frame, x, y, yaw, pitch, lift)
LYAW, RYAW = 6.0, -6.0
foot_plan = {
    "R": [(1, -0.10, 1.00, RYAW, 0, 0), (10, -0.10, 1.00, RYAW, 0, 0),
          (14, -0.10, 1.00, RYAW, 8, 0), (18, -0.10, 1.00, RYAW, 22, 0),
          (22, -0.10, 1.00, RYAW, 38, 0.0),
          (27, -0.103, 0.93, RYAW, 30, 0.035), (33, -0.105, 0.76, RYAW, 5, 0.06),
          (39, -0.105, 0.56, RYAW, -12, 0.05), (44, -0.105, 0.42, RYAW, -18, 0.012),
          (46, -0.105, 0.40, RYAW, -16, 0), (49, -0.105, 0.40, RYAW, -8, 0),
          (53, -0.105, 0.40, RYAW, 0, 0), (82, -0.105, 0.40, RYAW, 0, 0),
          (96, -0.105, 0.40, RYAW, 13, 0), (114, -0.105, 0.40, RYAW, 11, 0),
          (140, -0.105, 0.40, RYAW, 3, 0), (160, -0.105, 0.40, RYAW, 0, 0),
          # stays planted through the bend; heel peels as weight goes forward
          (190, -0.105, 0.40, RYAW, 0, 0), (215, -0.105, 0.40, RYAW, 10, 0),
          (240, -0.105, 0.40, RYAW, 16, 0), (275, -0.105, 0.40, RYAW, 16, 0),
          (305, -0.105, 0.40, RYAW, 5, 0), (320, -0.105, 0.40, RYAW, 0, 0),
          # settle step forward
          (514, -0.105, 0.40, RYAW, 0, 0), (518, -0.105, 0.40, RYAW, 10, 0),
          (523, -0.105, 0.40, RYAW, 24, 0), (529, -0.108, 0.35, RYAW, 15, 0.03),
          (536, -0.11, 0.24, RYAW - 1, 0, 0.035), (542, -0.112, 0.15, RYAW - 2, -8, 0.012),
          (545, -0.112, 0.125, RYAW - 2, -6, 0), (549, -0.112, 0.125, RYAW - 2, 0, 0),
          (600, -0.112, 0.125, RYAW - 2, 0, 0)],
    "L": [(1, 0.10, 1.00, LYAW, 0, 0), (46, 0.10, 1.00, LYAW, 0, 0),
          (50, 0.10, 1.00, LYAW, 8, 0), (55, 0.10, 1.00, LYAW, 22, 0),
          (60, 0.10, 1.00, LYAW, 36, 0.0),
          (65, 0.098, 0.90, LYAW, 26, 0.035), (71, 0.096, 0.62, LYAW, 3, 0.06),
          (77, 0.095, 0.36, LYAW, -10, 0.05), (83, 0.095, 0.10, LYAW, -16, 0.014),
          (86, 0.095, 0.02, LYAW, -15, 0), (90, 0.095, 0.02, LYAW, -7, 0),
          (95, 0.095, 0.02, LYAW, 0, 0), (600, 0.095, 0.02, LYAW, 0, 0)],
}

def interp_plan(plan, f):
    """for dense roll keys: linear between plan entries"""
    for (f0, *a), (f1, *b) in zip(plan, plan[1:]):
        if f0 <= f <= f1:
            t = (f - f0) / (f1 - f0) if f1 > f0 else 0
            return [u + (v - u) * t for u, v in zip(a, b)]
    return list(plan[-1][1:])

for s, plan in foot_plan.items():
    frames = set(p[0] for p in plan)
    # densify every roll / swing span so the arc about ball/heel is exact
    for (f0, *a), (f1, *b) in zip(plan, plan[1:]):
        if a != b and f1 - f0 <= 30:
            frames.update(range(f0, f1 + 1, 2))
    pole_keys = []
    for f in sorted(frames):
        x, y, yaw, pitch, lift = interp_plan(plan, f)
        M, ankle, Ryaw = foot_matrix(s, x, y, yaw, pitch, lift)
        key_world("IK_foot." + s, f, M)
        # knee pole: in front of the foot, at knee height, follows foot yaw
        pole = Vector((x, y, 0.5)) + Ryaw @ Vector((0, -0.7, 0))
        pb = PB["Pole_knee." + s]
        pb.location = rest("Pole_knee." + s).to_3x3().inverted() @ (pole - BN["Pole_knee." + s].head_local)
        pb.keyframe_insert("location", frame=f, group="Pole_knee." + s)
    # toes stay flat while the heel is up
    for f in sorted(frames):
        x, y, yaw, pitch, lift = interp_plan(plan, f)
        tb = -max(pitch, 0) * 0.9 if lift < 0.02 else -max(pitch, 0) * 0.4
        for t in ("toe1-1.", "toe2-1.", "toe3-1.", "toe4-1.", "toe5-1."):
            key_q(t + s, f, local_q(t + s, rotw([("X", tb)])))

print("BODY_KEYS_DONE")
exec(open(__file__.replace("03_animate.py", "03b_arms_bottle.py")).read())
exec(open(__file__.replace("03_animate.py", "04_camera.py")).read())
bpy.ops.wm.save_as_mainfile(filepath=OUT)
