"""FanCancer animation: rigs, acting, faces, crowd, props, FX, one camera. Exec'd after 02_build_scene.py."""
import os, math, random, json
import bpy
from mathutils import Vector, Matrix, Euler
_D = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else D
exec(open(os.path.join(D, "..", "..", "pipeline", "anim_lib.py")).read())
R_ = math.radians
sc = bpy.context.scene
random.seed(7)
F = lambda t: 1 + round(t * 60)          # seconds -> frame
BEATS = [(1, 0.0, "At a hockey game, she spotted a strange mole"), (2, 2.2, "on the back of a man's neck"),
         (3, 3.9, "It was an odd color, and she thought it could be cancer"), (4, 8.2, "She was nervous about upsetting a stranger"),
         (5, 13.0, "So she typed a note in big letters on her phone"), (6, 15.8, "and pressed it against the glass"),
         (7, 17.8, "The team's equipment manager read the message"), (8, 22.2, "Still, he went to a doctor just in case"),
         (9, 25.0, "and when they checked the mole, they found cancer"), (10, 30.8, "He asked people to help him find the woman"),
         (11, 33.8, "Strangers shared the story"), (12, 35.6, "and when she was finally identified"),
         (13, 37.9, "both teams surprised her with a ten thousand dollar scholarship")]
json.dump([{"beat": b, "frame": F(t), "first_words": w} for b, t, w in BEATS],
          open(os.path.join(D, "..", "beats.json"), "w"), indent=1)

def C(n): return bpy.data.collections[n]

# ------------------------------------------------------------------ rig duplication (shared mesh data)
def dup_rig(src_name, new_name, cl):
    src = bpy.data.objects[src_name]
    r = src.copy(); r.data = src.data.copy(); r.name = new_name; r.animation_data_clear(); r.location = (0, 0, 0); r.rotation_euler = (0, 0, 0)
    r["src"] = src["src"] if "src" in src.keys() else src_name
    for pb in r.pose.bones: pb.rotation_mode = 'QUATERNION'
    cl.objects.link(r)
    for ch in src.children:
        c = ch.copy(); c.name = ch.name.replace(src_name, new_name); c.parent = r; c["src"] = src_name
        for m in c.modifiers:
            if m.type == 'ARMATURE': m.object = r
        cl.objects.link(c)
    return r

def move_to(o, cl):
    for u in list(o.users_collection): u.objects.unlink(o)
    cl.objects.link(o)
    for ch in o.children: move_to(ch, cl)

C_CHAR = bpy.data.collections.new("CHARS"); sc.collection.children.link(C_CHAR)
for n in ("Fan", "Manager", "Doctor", "Nurse", "Crowd0", "Crowd1", "Crowd2", "Crowd3", "Crowd4", "Crowd5", "Player0", "Player1"):
    move_to(bpy.data.objects[n], C_CHAR)
ManB = dup_rig("Manager", "ManagerB", C_CHAR)

# ------------------------------------------------------------------ face
def face(rig, f, brow=0.0, frown=0.0, lid=0.0, jaw=0.0, smile=0.0, bite=0.0, squint=0.0):
    """brow: raise (+) / lower (-); frown: inner brows down+in; lid: upper lid close (0..1); jaw open deg; smile -1..1; bite: lower lip in"""
    PB = rig.pose.bones
    def loc(n, v):
        pb = PB[n]; pb.location = v; pb.keyframe_insert("location", frame=f, group=n)
    def rot(n, e):
        pb = PB[n]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = e; pb.keyframe_insert("rotation_euler", frame=f, group=n)
    for s, sx in (("L", 1), ("R", -1)):
        loc(f"oculi01.{s}", (0, 0.006 * brow - 0.004 * frown, 0))
        loc(f"oculi02.{s}", (0, 0.004 * brow, 0))
        rot(f"orbicularis03.{s}", (R_(28 * lid + 10 * squint), 0, 0))
        rot(f"orbicularis04.{s}", (R_(-10 * squint), 0, 0))
        loc(f"risorius03.{s}", (0, 0.006 * smile, 0.0))
        loc(f"oris03.{s}", (0, 0.004 * smile, 0))
        loc(f"oris07.{s}", (0, 0.004 * smile, 0))
    rot("jaw", (R_(jaw), 0, 0))
    loc("oris06", (0, 0.003 * bite, 0)); loc("oris02", (0, -0.004 * bite, 0))

# ------------------------------------------------------------------ IK humans
def setup(name):
    rig = bpy.data.objects[name]; R = make_human_ctrl(rig); H = Human(R); H.name = name; return R, H

def Ry(yaw): return Matrix.Rotation(R_(yaw), 3, 'Z')
def W(pos, yaw, v): return Vector(pos) + Ry(yaw) @ Vector(v)

class Actor:
    def __init__(self, name):
        self.R, self.H = setup(name); self.o = self.R.o
        self.sh = {s: self.R.BN["upperarm01." + s].head_local.copy() for s in "LR"}
        self.plant = None; self.fov = None
    def set_plant(self, pos, yaw):
        self.plant = {s: (self.H.foot_xy(s, Vector(pos), yaw), yaw) for s in "LR"}
    def pose(self, f, pos, yaw=0.0, flex=0.0, side=0.0, twist=0.0, head=(0.0, 0.0), hip=0.0,
             feet=None, hands=None, crouch=0.0, foot_lift=0.0):
        """pos = ground point under the pelvis; feet: {'L': (dx,dy) local}, hands: {'L': (local_pos, local_d, local_n)} body-local"""
        pos = Vector(pos); H = self.H
        rp = Vector((pos.x, pos.y, pos.z + H.root_head.z - crouch + hip))
        H.key_root(f, rp, yaw=yaw, flex=flex * 0.4, side=side * 0.4)
        H.key_spine(f, flex=flex, twist=twist, side=side, head=head)
        for s in "LR":
            if feet and s in feet and feet[s] is not None:
                dx, dy = feet[s][:2]; fy = feet[s][2] if len(feet[s]) > 2 else 0.0
                xy = W(pos, yaw, (dx, dy, 0)).to_2d(); H.key_foot(s, f, Vector(xy), yaw + fy, lift=pos.z + foot_lift, pitch=-25 if foot_lift else 0)
            elif self.fov and s in self.fov:
                xy, fyaw, lf = self.fov[s]; H.key_foot(s, f, Vector(xy), fyaw, lift=pos.z + lf, pitch=12 * (lf > 0))
            elif self.plant:
                xy, fyaw = self.plant[s]; H.key_foot(s, f, xy, fyaw, lift=pos.z)
            else:
                xy = H.foot_xy(s, pos, yaw); H.key_foot(s, f, xy, yaw, lift=pos.z)
        for s in "LR":
            sx = 1 if s == "L" else -1
            if hands and s in hands:
                lp, ld, ln = hands[s]
                Wp = W(pos, yaw, lp); d = Ry(yaw) @ Vector(ld); n = Ry(yaw) @ Vector(ln)   # n = palm normal
                pole = W(pos, yaw, (sx * 0.55, 0.45, 0.85))
                H.key_hand(s, f, Wp, d, n, pole=pole)
            else:   # relaxed at the side
                Wp = W(pos, yaw, (sx * 0.31, -0.06, 0.84 - crouch + hip)); H.key_hand(s, f, Wp, Ry(yaw) @ Vector((0.05 * sx, -0.1, -1)),
                                                                            Ry(yaw) @ Vector((-sx, 0, 0)), pole=W(pos, yaw, (sx * 0.55, 0.45, 1.0)))

def arm_swing(A, path, yaw_fn, f0, f1, stride):
    d = 0.0; prev = path(f0)
    for f in range(f0, f1 + 1):
        p = path(f); d += (p - prev).to_2d().length; prev = p
        if (f - f0) % 4: continue
        ph = math.sin(2 * math.pi * d / stride)
        amp = min(1.0, (path(min(f + 6, f1)) - p).to_2d().length / 0.05)
        yw = yaw_fn(f); pos = Vector((p.x, p.y, 0))
        for s, sg in (("L", -1), ("R", 1)):
            sx = 1 if s == "L" else -1; sw = sg * ph * 0.16 * amp
            A.H.key_hand(s, f, W(pos, yw, (sx * 0.27, -sw, 0.86 - 0.03 * abs(sw))), Ry(yw) @ Vector((0.05 * sx, -0.25 * sw * 4, -1)),
                         Ry(yw) @ Vector((-sx, 0, 0)), pole=W(pos, yw, (sx * 0.5, 0.5, 1.0)))

def sit(A, f, pos, yaw, seat_h, hands=None, flex=8, head=(0, 0), twist=0, side=0, knee=0.42, foot_lift=0.0):
    """seated on a seat of height seat_h, feet on the floor in front"""
    A.pose(f, pos, yaw, flex=flex, head=head, twist=twist, side=side, hip=seat_h + 0.10 - A.H.root_head.z,
           feet={"L": (0.12, -knee), "R": (-0.12, -knee)}, hands=hands, foot_lift=foot_lift)

# palm helpers (body-local, character faces -Y): d = finger direction, n = palm normal
HANDS_ON_BOARDS = {"L": ((0.25, -0.38, 1.11), (0, -1, -0.3), (0, 0, -1)), "R": ((-0.25, -0.38, 1.11), (0, -1, -0.3), (0, 0, -1))}
def phone_hold(dz=0.0, both=True, spread=0.0):
    hd = {"R": ((-0.05, -0.44, 1.10 + dz), (0.1, -0.2, 1), (0.05, 0.6, 0.8))}
    if both: hd["L"] = ((0.10 + spread, -0.43, 1.09 + dz), (-0.2, -0.3, 1), (-0.4, 0.5, 0.8))
    return hd

# ================================================================== FAN
fan = Actor("Fan"); FR = fan.o
FAN0 = (0.0, 0.62, 0.0)
def fan_rink():
    f = F
    fan.set_plant(FAN0, 0)
    fan.pose(f(0.0), FAN0, 0, flex=6, head=(0, 8), hands=HANDS_ON_BOARDS, twist=6)
    face(FR, f(0.0), brow=0.2, smile=0.4)
    fan.pose(f(0.8), FAN0, 0, flex=8, head=(-4, -10), hands=HANDS_ON_BOARDS, twist=-4)
    fan.pose(f(1.4), FAN0, 0, flex=12, head=(4, -4), hands=HANDS_ON_BOARDS, twist=-2)   # notices, leans in
    face(FR, f(1.2), brow=0.3, smile=0.2); face(FR, f(1.8), brow=-0.2, frown=0.6, squint=0.8)
    fan.pose(f(2.4), (0.0, 0.58, 0), 0, flex=14, head=(6, -6), hands=HANDS_ON_BOARDS)
    fan.pose(f(3.6), (0.0, 0.56, 0), 0, flex=16, head=(8, -8), hands=HANDS_ON_BOARDS)
    face(FR, f(3.4), brow=-0.4, frown=0.9, squint=1.0, jaw=2)
    fan.pose(f(8.0), (0.0, 0.56, 0), 0, flex=14, head=(6, -6), hands=HANDS_ON_BOARDS)
    # beat 4: nervous
    hs = {"L": ((0.18, -0.25, 1.15), (0, -0.3, 1), (0, -1, 0)), "R": ((-0.25, -0.38, 1.11), (0, -1, -0.3), (0, 0, -1))}
    fan.pose(f(8.6), (0.0, 0.6, 0), 0, flex=8, head=(4, 30), twist=12, hands=HANDS_ON_BOARDS)       # glance left
    face(FR, f(8.6), brow=0.5, frown=0.8, bite=1.0, lid=0.1)
    fan.pose(f(9.4), (0.0, 0.6, 0), 0, flex=8, head=(2, -32), twist=-12, hands=HANDS_ON_BOARDS)     # glance right
    face(FR, f(9.6), brow=0.7, frown=1.0, bite=1.0)
    fan.pose(f(10.3), (0.0, 0.62, 0), 0, flex=4, head=(-6, 0), hands=hs)                            # hand to mouth, unsure
    face(FR, f(10.4), brow=0.6, frown=1.0, bite=0.4, lid=0.2)
    fan.pose(f(11.2), (0.0, 0.6, 0), 0, flex=8, head=(2, -6), hands=HANDS_ON_BOARDS)              # looks back at him
    face(FR, f(11.4), brow=0.3, frown=0.7, bite=1.0)
    fan.pose(f(12.2), (0.0, 0.6, 0), 0, flex=6, head=(-16, 0), hands=HANDS_ON_BOARDS)              # nod down
    fan.pose(f(12.6), (0.0, 0.6, 0), 0, flex=8, head=(4, 0), hands=HANDS_ON_BOARDS)
    face(FR, f(12.6), brow=-0.3, frown=0.4, smile=-0.2)
    fan.pose(f(12.85), (0.0, 0.62, 0), 0, flex=6, head=(6, -12), twist=-6,
             hands={"R": ((-0.19, -0.05, 0.87), (0, -0.1, -1), (1, 0, 0)), "L": HANDS_ON_BOARDS["L"]})     # draws the phone from her pocket
    # beat 5: typing (thumbs animated below)
    fan.pose(f(13.4), (0.0, 0.64, 0), 0, flex=4, head=(14, 0), hands=phone_hold())
    face(FR, f(13.6), brow=-0.2, frown=0.6, squint=0.4)
    fan.pose(f(14.4), (0.0, 0.63, 0), 0, flex=5, head=(16, 4), hands=phone_hold(0.01))
    fan.pose(f(15.4), (0.0, 0.63, 0), 0, flex=5, head=(15, -3), hands=phone_hold(0.02))
    # beat 6: slap phone on the glass, knock with the left
    glassR = {"R": ((-0.05, -0.465, 1.40), (0, 0, 1), (0, -1, 0))}
    fan.pose(f(15.9), (0.0, 0.58, 0), 0, flex=10, head=(4, 0), hands={"R": ((-0.08, -0.38, 1.30), (0, -0.4, 1), (0, -1, 0.3)),
                                                                     "L": ((0.06, -0.29, 1.07), (-0.2, -0.3, 1), (-0.4, 0.5, 0.8))})
    fan.pose(f(16.15), (0.0, 0.5, 0), 0, flex=12, head=(0, 0), hands={**glassR, "L": ((0.20, -0.30, 1.2), (0, -0.4, 1), (0, -1, 0))})
    face(FR, f(16.1), brow=0.6, jaw=6, frown=0.3)
    knock = ((0.30, -0.47, 1.36), (0, -0.2, 1), (1, 0, 0))
    for k, t in enumerate((16.5, 16.65, 16.8, 16.95)):
        L = knock if k % 2 else ((0.30, -0.39, 1.36), (0, -0.2, 1), (1, 0, 0))
        fan.pose(f(t), (0.0, 0.5, 0), 0, flex=12, head=(0, 2), hands={**glassR, "L": L})
    fan.pose(f(17.5), (0.0, 0.5, 0), 0, flex=12, head=(4, 0), hands={**glassR, "L": ((0.20, -0.30, 1.2), (0, -0.4, 1), (0, -1, 0))})
    face(FR, f(17.6), brow=0.8, smile=0.2, jaw=4)
    fan.pose(f(19.6), (0.0, 0.5, 0), 0, flex=12, head=(10, 0), hands={**glassR, "L": ((0.20, -0.30, 1.2), (0, -0.4, 1), (0, -1, 0))})
    face(FR, f(20.4), brow=0.9, frown=0.5, jaw=8)     # he walks away
    fan.pose(f(20.6), (0.0, 0.56, 0), 0, flex=6, head=(6, 28), twist=14, hands={"R": ((-0.16, -0.46, 1.25), (0, -0.4, 1), (0, -1, 0.3))})
    fan.pose(f(23.0), (0.0, 0.6, 0), 0, flex=4, head=(4, 34), twist=16)
    face(FR, f(23.0), brow=0.6, frown=0.8, smile=-0.4)
fan_rink()
fan.plant = None
# HOME: on the sofa at (-300,200) facing -Y (laptop on the coffee table in front)
HM = Vector((-300, 200, 0))
def fan_home():
    p = HM + Vector((0, 1.45, 0)); f = F
    lap = {"L": ((0.18, -0.38, 0.62), (0, -1, 0), (0, 0, -1)), "R": ((-0.18, -0.38, 0.62), (0, -1, 0), (0, 0, -1))}
    sit(fan, f(34.0), p, 0, 0.45, hands=lap, flex=12, head=(14, 0))
    sit(fan, f(35.4), p, 0, 0.45, hands=lap, flex=14, head=(16, 0))
    face(FR, f(35.4), brow=0.0, smile=0.0)
    mouth = {"R": ((-0.03, -0.33, 1.02), (0.2, 0.3, 1), (0, 1, 0)), "L": ((0.10, -0.25, 0.80), (0, -0.2, 1), (-1, 0, 0))}
    sit(fan, f(36.4), p, 0, 0.45, hands=mouth, flex=-6, head=(-6, 0))
    face(FR, f(36.4), brow=1.0, lid=-0.4, jaw=14)
    both = {"R": ((-0.05, -0.33, 1.02), (0.2, 0.3, 1), (0, 1, 0)), "L": ((0.07, -0.32, 0.97), (-0.2, 0.3, 1), (0, 1, 0))}
    sit(fan, f(37.2), p, 0, 0.45, hands=both, flex=-8, head=(-4, 6))
    face(FR, f(37.2), brow=1.0, lid=-0.3, jaw=10, smile=0.5)
    sit(fan, f(37.8), p, 0, 0.45, hands=both, flex=-4, head=(0, -4))
# FINALE on the ice, holding the cheque
FIN = Vector((0.0, -12.0, 0.0))
def fan_finale():
    f = F; p = FIN + Vector((-0.35, 0, 0))
    ch = {"L": ((0.42, -0.38, 1.02), (0, 0, 1), (0, 1, 0)), "R": ((-0.42, -0.38, 1.02), (0, 0, 1), (0, 1, 0))}
    for i, t in enumerate((38.0, 39.0, 40.0, 41.0, 42.0, 43.0, 44.0)):  # faces -Y: the camera and the home crowd
        up = 0.04 * (i % 2)
        hd = {k: ((v[0][0], v[0][1], v[0][2] + up), v[1], v[2]) for k, v in ch.items()}
        fan.pose(f(t), p, 12 * math.sin(i), flex=-4, head=(-6, 8 * math.sin(i * 1.3)), hands=hd, hip=up * 0.5)
        face(FR, f(t), brow=0.8, smile=1.0, jaw=12 + 6 * (i % 2))
fan_home(); fan_finale()
# teleports: hold before the jump, one-frame jump
def hold_until(A, f_hold, f_jump):
    """duplicate all keys from the last key <= f_hold onto f_jump-1 so the jump is a single frame"""
    act = A.o.animation_data.action
    for fc in _fcurves(act):
        v = fc.evaluate(f_hold)
        fc.keyframe_points.insert(f_jump - 1, v, options={'FAST'})
def _fcurves(act):
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags: out.extend(cb.fcurves)
    if not out and hasattr(act, "fcurves"): out = list(act.fcurves)
    return out
hold_until(fan, F(23.0), F(34.0))     # stays at the glass until the camera is in the city
hold_until(fan, F(37.8), F(38.0))     # home -> ice when the laptop screen fills the frame

# thumbs typing (beat 5): finger1 bones jitter
for t in [13.6 + 0.12 * k for k in range(18)]:
    for s, ph in (("R", 0), ("L", 1)):
        pb = FR.pose.bones[f"finger1-2.{s}"]; pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (R_(20 if (int((t - 13.6) / 0.12) + ph) % 2 else -5), 0, 0)
        pb.keyframe_insert("rotation_euler", frame=F(t))

# ================================================================== MANAGER (rink + tunnel + finale) and ManagerB (clinic)
man = Actor("Manager"); MR = man.o
MAN0 = Vector((0.25, -0.62, 0.0))
def man_rink():
    f = F
    man.set_plant(MAN0, 0)
    cross = {"L": ((-0.12, -0.20, 1.05), (-1, 0, 0.1), (0, 1, 0)), "R": ((0.12, -0.22, 1.0), (1, 0, 0.1), (0, 1, 0))}
    hips = {"L": ((0.22, -0.02, 0.98), (0, 0, -1), (-1, 0, 0)), "R": ((-0.22, -0.02, 0.98), (0, 0, -1), (1, 0, 0))}
    for i, t in enumerate((0.0, 1.5, 3.0, 4.5, 6.0, 7.5, 9.0, 10.5, 12.0, 13.5, 15.0, 16.2)):
        man.pose(f(t), MAN0, 6 * math.sin(i), flex=4, head=(-4 + 6 * math.sin(i * 0.7), 18 * math.sin(i * 1.1)),
                 hands=hips if i % 4 < 2 else None, twist=6 * math.sin(i))
        face(MR, f(t), brow=0.1 * (i % 2), frown=0.3)
    # turns to the knock
    # stepping turn toward the knock: head leads, then R, L, R steps with weight shift
    P0 = man.plant; C0 = MAN0 + Vector((0, 0.12, 0))
    endp = {s: (man.H.foot_xy(s, C0, 180), 180) for s in "LR"}
    midR = (man.H.foot_xy("R", MAN0 + Vector((0.03, 0.06, 0)), 90), 90)
    man.pose(f(16.4), MAN0, 10, flex=2, head=(2, 45))
    man.fov = {"R": (P0["R"][0].lerp(midR[0], 0.5), 45, 0.07)}; man.pose(f(16.6), MAN0 + Vector((0.04, 0.02, 0)), 30, flex=2, head=(2, 40), side=-4); man.fov = None
    man.plant = {"L": P0["L"], "R": midR}; man.pose(f(16.85), MAN0 + Vector((0.0, 0.04, 0)), 60, flex=2, head=(4, 35))
    man.fov = {"L": (P0["L"][0].lerp(endp["L"][0], 0.5), 120, 0.07)}; man.pose(f(17.1), MAN0 + Vector((-0.03, 0.06, 0)), 100, flex=2, head=(4, 25), side=4); man.fov = None
    man.plant = {"L": endp["L"], "R": midR}; man.pose(f(17.35), MAN0 + Vector((0, 0.08, 0)), 140, flex=2, head=(6, 15))
    man.fov = {"R": (midR[0].lerp(endp["R"][0], 0.5), 160, 0.06)}; man.pose(f(17.6), MAN0 + Vector((0.02, 0.10, 0)), 165, flex=3, head=(6, 6), side=-3); man.fov = None
    man.plant = endp
    man.pose(f(18.0), MAN0 + Vector((0, 0.10, 0)), 180, flex=6, head=(8, 0))
    face(MR, f(18.0), brow=0.5, frown=0.4)
    man.pose(f(18.8), MAN0 + Vector((0, 0.18, 0)), 180, flex=14, head=(10, -6))     # leans in, reads
    face(MR, f(18.8), brow=-0.4, frown=1.0, squint=1.0, jaw=2)
    man.pose(f(19.8), MAN0 + Vector((0, 0.18, 0)), 180, flex=12, head=(-6, 10))     # looks up at her, puzzled
    face(MR, f(19.8), brow=1.0, frown=0.6, squint=0.2, smile=-0.3)
    shrug = {"L": ((0.30, -0.10, 1.02), (0.3, -1, 0.2), (0, 0, 1)), "R": ((-0.30, -0.10, 1.02), (-0.3, -1, 0.2), (0, 0, 1))}
    man.pose(f(20.3), MAN0 + Vector((0, 0.14, 0)), 180, flex=2, head=(0, 12), hands=shrug, hip=0.02)
    face(MR, f(20.3), brow=0.7, smile=-0.6)
    man.pose(f(20.8), MAN0 + Vector((0, 0.1, 0)), 150, flex=2, head=(0, 0))
    # walks off along -x into the tunnel
    pts = [(F(20.9), Vector((0.2, -0.55, 0))), (F(21.6), Vector((-1.4, -0.85, 0))), (F(23.0), Vector((-5.0, -1.05, 0))),
           (F(26.0), Vector((-13.0, -1.05, 0))), (F(28.0), Vector((-18.5, -1.05, 0)))]
    path = catmull(pts)
    def yaw_fn(fr):
        a = path(fr); b = path(fr + 2); d = b - a
        return math.degrees(math.atan2(d.x, -d.y)) if d.length > 1e-4 else 90
    man.plant = None
    man.H.walk(path, yaw_fn, F(20.9), F(28.0), stride=0.72, lift=0.08)
    arm_swing(man, path, yaw_fn, F(20.9), F(28.0), 0.72)
    face(MR, f(21.4), brow=0.2, frown=0.5)
man_rink()
def man_finale():
    f = F; p = FIN + Vector((0.45, 0.05, 0))
    clap_o = {"L": ((0.025, -0.44, 1.15), (0, -0.3, 1), (-1, 0, 0)), "R": ((-0.025, -0.44, 1.15), (0, -0.3, 1), (1, 0, 0))}
    clap_c = {"L": ((0.13, -0.44, 1.12), (0, -0.3, 1), (-1, 0, 0)), "R": ((-0.13, -0.44, 1.12), (0, -0.3, 1), (1, 0, 0))}
    for i in range(24):
        t = 38.0 + i * 0.25
        man.pose(f(t), p, -15, flex=2, head=(-4, -14), hands=clap_o if i % 2 else clap_c)
        if i % 4 == 0: face(MR, f(t), brow=0.6, smile=1.0, jaw=6)
man_finale()
hold_until(man, F(28.0), F(38.0))

# ManagerB: sits on the exam bed in the clinic, facing +Y
manb = Actor("ManagerB"); MBR = manb.o
BEDP = Vector((-28.5, -2.34, 0.0))
def manb_clinic():
    f = F
    knees = {"L": ((0.17, -0.30, 1.03), (0, -1, -0.4), (0, 0, -1)), "R": ((-0.17, -0.30, 1.03), (0, -1, -0.4), (0, 0, -1))}
    for i, t in enumerate((20.0, 22.4, 23.4, 24.4)):
        sit(manb, f(t), BEDP, 180, 0.83, hands=knees, flex=18, head=(30, -24 + 4 * i), knee=0.30, foot_lift=0.28)      # head bowed + turned right, neck exposed
    face(MBR, f(22.4), brow=0.2, frown=0.4)
    face(MBR, f(25.6), brow=0.7, frown=0.9, lid=0.2)                 # "they found cancer"
    sit(manb, f(26.0), BEDP, 180, 0.83, hands=knees, flex=20, head=(34, -26), knee=0.30, foot_lift=0.28)
    sit(manb, f(28.0), BEDP, 180, 0.83, hands=knees, flex=20, head=(34, -26), knee=0.30, foot_lift=0.28)
    face(MBR, f(28.4), brow=0.4, frown=0.6, lid=0.5)
    sit(manb, f(29.0), BEDP, 180, 0.83, hands=knees, flex=6, head=(4, 0), knee=0.30, foot_lift=0.28)                 # relief: sits up, exhale
    face(MBR, f(29.4), brow=0.5, smile=0.8, lid=0.4, jaw=4)
    sit(manb, f(29.95), BEDP, 180, 0.83, hands={"R": ((-0.20, -0.12, 0.95), (0, -0.2, -1), (1, 0, 0)), "L": knees["L"]}, flex=6, head=(8, -10), knee=0.30, foot_lift=0.28)   # pocket
    ph = {"R": ((-0.06, -0.42, 1.02), (0, -1, 0.15), (0, 0.25, 1)), "L": ((0.16, -0.28, 0.98), (0, -1, -0.4), (0, 0, -1))}
    sit(manb, f(30.4), BEDP, 180, 0.83, hands=ph, flex=8, head=(16, 4), knee=0.30, foot_lift=0.28)
    face(MBR, f(30.6), brow=0.2, smile=0.4)
    tap = {"R": ((-0.06, -0.43, 1.04), (0, -1, 0.15), (0, 0.25, 1)), "L": ((0.16, -0.28, 0.98), (0, -1, -0.4), (0, 0, -1))}
    for k, t in enumerate((31.0, 31.4, 31.8, 32.2, 33.0)):
        sit(manb, f(t), BEDP, 180, 0.83, hands=tap if k % 2 else ph, flex=8, head=(18, 2), knee=0.30, foot_lift=0.28)
manb_clinic()

# ================================================================== DOCTOR, NURSE
doc = Actor("Doctor"); DR = doc.o
DOCP = Vector((-29.2, -2.4, 0.0))
def doc_anim():
    f = F
    # gloves: hand faces get a nitrile material (the MPFB hand mesh)
    body = bpy.data.objects["Doctor.body"]
    gm = bpy.data.materials.new("NitrileGlove"); gm.use_nodes = True; gp = gm.node_tree.nodes["Principled BSDF"]
    gp.inputs['Base Color'].default_value = (0.25, 0.35, 0.75, 1); gp.inputs['Roughness'].default_value = 0.35
    gp.inputs['Subsurface Weight'].default_value = 0.1; gp.inputs['Coat Weight'].default_value = 0.3
    body.data = body.data.copy(); body.data.materials.append(gm); gi = len(body.data.materials) - 1
    vg = {g.index: g.name for g in body.vertex_groups}
    hand_v = set()
    for v in body.data.vertices:
        for g in v.groups:
            nm = vg.get(g.group, "")
            if g.weight > 0.3 and (nm.startswith("finger") or nm.startswith("wrist") or nm.startswith("metacarpal")): hand_v.add(v.index)
    for p_ in body.data.polygons:
        if all(i in hand_v for i in p_.vertices): p_.material_index = gi
    scope = {"R": ((-0.15, -0.53, 1.30), (0.2, -0.5, 0.6), (0.8, 0, 0.3)), "L": ((0.16, -0.51, 1.30), (-0.2, -0.6, 0.4), (-0.8, 0, 0.3))}
    rest = None
    doc.set_plant(DOCP + Vector((0.04, 0, 0)), 90)
    doc.pose(f(20.0), DOCP, 90, flex=10, head=(16, 0))
    doc.pose(f(22.6), DOCP, 90, flex=24, head=(26, -10), hands=scope)
    face(DR, f(22.6), brow=-0.2, frown=0.6, squint=0.6)
    doc.pose(f(23.8), DOCP + Vector((0.05, 0, 0)), 95, flex=30, head=(30, -6), hands=scope)
    doc.pose(f(24.8), DOCP + Vector((0.08, 0, 0)), 95, flex=32, head=(32, -4), hands=scope)
    face(DR, f(25.2), brow=0.4, frown=1.0, smile=-0.4)                         # serious
    doc.pose(f(25.45), DOCP + Vector((0.04, 0, 0)), 88, flex=12, head=(14, 12), hands={"R": ((-0.21, -0.03, 0.92), (0, -0.1, -1), (1, 0, 0))})   # scope into her coat pocket
    doc.pose(f(25.6), DOCP, 80, flex=10, head=(4, 26))                         # turns to him, explains
    face(DR, f(25.8), brow=0.3, frown=0.5, jaw=8); face(DR, f(26.0), jaw=2, frown=0.5)
    doc.pose(f(26.0), DOCP, 85, flex=8, head=(4, 20), hands={"R": ((-0.21, -0.03, 0.92), (0, -0.1, -1), (1, 0, 0))})   # forceps from the pocket
    cut = {"R": ((-0.15, -0.55, 1.27), (0.1, -0.6, 0.3), (0.5, 0, 0.8)), "L": ((0.15, -0.55, 1.28), (-0.1, -0.6, 0.3), (-0.5, 0, 0.8))}
    for i, t in enumerate((26.4, 27.0, 27.6, 28.2)):
        doc.pose(f(t), DOCP + Vector((0.08, 0, 0)), 95, flex=32, head=(34, -2), hands={k: ((v[0][0], v[0][1] - 0.01 * (i % 2), v[0][2]), v[1], v[2]) for k, v in cut.items()})
    face(DR, f(26.6), brow=-0.3, frown=0.8, squint=0.7)
    _c = dict(cut); _c["L"] = ((0.21, -0.03, 0.92), (0, -0.1, -1), (-1, 0, 0))
    doc.pose(f(27.85), DOCP + Vector((0.06, 0, 0)), 93, flex=26, head=(30, -2), hands=_c)            # left hand fetches the bandage
    doc.pose(f(28.7), DOCP + Vector((0.04, 0, 0)), 90, flex=14, head=(16, 4), hands={"R": ((-0.21, -0.03, 0.92), (0, -0.1, -1), (1, 0, 0))})   # forceps back to the pocket
    doc.pose(f(29.2), DOCP, 80, flex=4, head=(0, 20))
    doc.plant = None
    face(DR, f(29.4), brow=0.5, smile=0.9)
    dpts = [(F(29.4), DOCP + Vector((0.0, 0.0, 0))), (F(30.4), DOCP + Vector((0.5, 1.0, 0))), (F(31.6), DOCP + Vector((1.5, 2.6, 0))), (F(32.4), DOCP + Vector((2.2, 3.1, 0)))]
    dpath = catmull(dpts)
    def dyaw(fr):
        a_ = dpath(fr); b_ = dpath(min(fr + 6, F(32.4))); d_ = b_ - a_
        return math.degrees(math.atan2(d_.x, -d_.y)) if d_.length > 1e-3 else 180
    doc.H.walk(dpath, dyaw, F(29.6), F(32.4), stride=0.6, lift=0.06)
    arm_swing(doc, dpath, dyaw, F(29.6), F(32.4), 0.6)
doc_anim()
nur = Actor("Nurse"); NR = nur.o
def nurse_anim():
    pts = [(F(20.0), Vector((-26.6, 0.6, 0))), (F(23.0), Vector((-26.8, 0.6, 0))), (F(25.0), Vector((-27.6, -0.4, 0))),
           (F(27.0), Vector((-27.4, 0.5, 0))), (F(29.0), Vector((-26.5, 0.7, 0))), (F(33.0), Vector((-27.0, 0.0, 0)))]
    path = catmull(pts)
    def yaw_fn(fr):
        a = path(fr); b = path(fr + 6); d = b - a
        return math.degrees(math.atan2(d.x, -d.y)) if d.length > 1e-3 else 180
    nur.H.walk(path, yaw_fn, F(20.0), F(33.0), stride=0.6, lift=0.06)
    arm_swing(nur, path, yaw_fn, F(20.0), F(33.0), 0.6)
    face(NR, F(22), brow=0.2); face(NR, F(28), smile=0.5)
nurse_anim()

# ================================================================== crowd + players (FK)
def fk(rig, f, n, seq):
    Rg = Rig(rig); Rg.key_rot(n, f, seq)
def fk_root(rig, f, pos, yaw=0.0):
    H = Human(Rig(rig)); H.key_root(f, Vector(pos) + Vector((0, 0, H.root_head.z)), yaw=yaw)
def seated_fk(rig, f, pos, yaw, cheer=0.0, sway=0.0, head=(0, 0), phone=False, relax=False):
    H = Human(Rig(rig)); Rg = H.r
    H.key_root(f, Vector(pos) + Vector((0, 0, 0.55)), yaw=yaw, side=sway * 3)
    H.key_spine(f, flex=6 - 10 * cheer, twist=sway * 8, head=head)
    for s in "LR":
        Rg.key_rot("upperleg01." + s, f, [("X", -88)]); Rg.key_rot("lowerleg01." + s, f, [("X", 92)])
        a = -40 - 120 * cheer if not (phone and s == "R") else -70
        if relax and cheer < 0.1:
            Rg.key_rot("upperarm01." + s, f, [("Y", -10 if s == "L" else 10), ("X", -22)]); Rg.key_rot("lowerarm01." + s, f, [("X", -75)]); continue
        Rg.key_rot("upperarm01." + s, f, [("Y", (-15 if s == "L" else 15) * (1 - cheer)), ("X", a)])
        Rg.key_rot("lowerarm01." + s, f, [("X", -50 * (1 - cheer) - (60 if phone and s == "R" else 0))])
def standing_fk(rig, f, pos, yaw, cheer=0.0, sway=0.0, head=(0, 0), stick=False):
    H = Human(Rig(rig)); Rg = H.r
    H.key_root(f, Vector(pos) + Vector((0, 0, H.root_head.z - 0.01)), yaw=yaw, side=sway * 2)
    H.key_spine(f, flex=-6 * cheer, twist=sway * 8, head=head)
    for s in "LR":
        Rg.key_rot("upperleg01." + s, f, [("X", 0)]); Rg.key_rot("lowerleg01." + s, f, [("X", 0)])
        Rg.key_rot("upperarm01." + s, f, [("Y", (-15 if s == "L" else 15) * (1 - cheer)), ("X", -10 - 150 * cheer)])
        Rg.key_rot("lowerarm01." + s, f, [("X", -20 - 30 * cheer)])

CROWD = []
k = 0
SRC = ["Crowd%d" % i for i in range(6)]
for row in range(4):
    y = 1.65 + 0.85 * row + 0.30; z = 0.42 * row + 0.42
    for j in range(12):
        x = -8.0 + j * 1.4 + (0.6 if row % 2 else 0) + random.uniform(-0.1, 0.1)
        if row == 0 and abs(x) < 1.2: continue
        name = f"Fanc{row}_{j}"; r = dup_rig(SRC[k % 6], name, C_CHAR); k += 1
        CROWD.append((r, Vector((x, y, z)), random.random() * 6.28))
for row in range(3):   # far side, across the ice
    y = -32.0 - (1.65 + 0.85 * row + 0.30); z = 0.42 * row + 0.42
    for j in range(7):
        x = -9.0 + j * 3.0 + random.uniform(-0.3, 0.3)
        name = f"FarFan{row}_{j}"; r = dup_rig(SRC[k % 6], name, C_CHAR); k += 1
        CROWD.append((r, Vector((x, y, z)), random.random() * 6.28, 180))
for item in CROWD:
    r, p, ph = item[:3]; yaw = item[3] if len(item) > 3 else 0
    phone = random.random() < 0.15
    for f in range(1, 2641, 30):
        t = f / 60.0
        goal = 1.0 if 38.4 < t < 44.5 else (0.6 if (3.0 < (t + ph) % 11 < 4.0) else 0.0)
        ch = goal * (0.6 + 0.4 * math.sin(t * 7 + ph)) if goal else 0.0
        if 38.4 < t:      # the finale: everyone up and cheering
            standing_fk(r, f, p + Vector((0, -0.25 if yaw == 0 else 0.25, 0)), yaw, cheer=ch, sway=math.sin(t * 3 + ph), head=(0, 10 * math.sin(t + ph)))
        else:
            seated_fk(r, f, p, yaw, cheer=ch, sway=math.sin(t * 1.3 + ph), head=(5 * math.sin(t * 0.9 + ph), 25 * math.sin(t * 0.5 + ph)), phone=phone)
    face(r, 1, smile=0.5, brow=0.3); face(r, F(38.5), smile=1.0, brow=0.8, jaw=10)

# bench players (sitting, watching), skaters on the ice, players at the finale
PLAY = []
for i, x in enumerate((-2.6, -1.5, 1.4, 2.5)):
    r = dup_rig(f"Player{i % 2}", f"Bench{i}", C_CHAR)
    for f in range(1, 1500, 40):
        t = f / 60.0
        seated_fk(r, f, Vector((x, -1.55, 0.0)), 0, cheer=0.0 if (t + i) % 9 > 1 else 0.35, sway=0.5 * math.sin(t + i), head=(0, 20 * math.sin(t * 0.6 + i)), relax=True)
    hold = Human(Rig(r));
SKATE = []
for i in range(6):
    r = dup_rig(f"Player{i % 2}", f"Skater{i}", C_CHAR); SKATE.append(r)
    cx, cy, ax, ay = 0.0, -15.0, 11.0 - i * 0.8, 8.0 - i * 0.6
    sp = 0.18 + 0.03 * i; ph = i * 1.1
    for f in range(1, 2641, 4):
        t = f / 60.0
        if t > 37.9:      # finale: lined up behind her, sticks up
            pos = FIN + Vector((-2.6 + i * 1.05, 1.6 + 0.3 * (i % 2), 0))
            standing_fk(r, f, pos, 0, cheer=0.7 + 0.3 * math.sin(t * 6 + i), sway=math.sin(t * 2 + i))
            continue
        a = t * sp * 2 * math.pi / 3 + ph
        pos = Vector((cx + ax * math.cos(a), cy + ay * math.sin(a), 0))
        tan = Vector((-ax * math.sin(a), ay * math.cos(a), 0))
        yaw = math.degrees(math.atan2(tan.x, -tan.y))
        H = Human(Rig(r)); Rg = H.r
        st = math.sin(t * 5.5 + ph)
        H.key_root(f, pos + Vector((0, 0, H.root_head.z - 0.12)), yaw=yaw, flex=25, side=10 * st - 12)
        H.key_spine(f, flex=25, twist=12 * st, head=(-20, 0))
        Rg.key_rot("upperleg01.L", f, [("X", -35 + 25 * st), ("Y", 18 * max(0, st))]); Rg.key_rot("lowerleg01.L", f, [("X", 50)])
        Rg.key_rot("upperleg01.R", f, [("X", -35 - 25 * st), ("Y", -18 * max(0, -st))]); Rg.key_rot("lowerleg01.R", f, [("X", 50)])
        Rg.key_rot("upperarm01.L", f, [("X", -45)]); Rg.key_rot("upperarm01.R", f, [("X", -55)])
        Rg.key_rot("lowerarm01.L", f, [("X", -40)]); Rg.key_rot("lowerarm01.R", f, [("X", -30)])
    face(r, 1, frown=0.4, brow=-0.2); face(r, F(38.3), smile=1.0, brow=0.6, jaw=12)
for n in ("Crowd0", "Crowd1", "Crowd2", "Crowd3", "Crowd4", "Crowd5", "Player0", "Player1"):
    o = bpy.data.objects[n]; o.location = (0, 0, -50)
    for ch in o.children: ch.hide_render = True
    o.hide_render = True

# ================================================================== props parented to bones
def bone_parent(obj, rig, bone, world_M):
    """parent obj to rig bone so that at REST pose it sits at world_M"""
    rig.data.pose_position = 'REST'; bpy.context.view_layer.update()
    obj.parent = rig; obj.parent_type = 'BONE'; obj.parent_bone = bone
    bpy.context.view_layer.update()
    obj.matrix_world = world_M
    rig.data.pose_position = 'POSE'; bpy.context.view_layer.update()

def palm_frame(rig, s):
    B = rig.data.bones
    wr = B["wrist." + s].head_local; f3 = B["finger3-1." + s].head_local
    dd = (f3 - wr).normalized(); aa = (B["finger2-1." + s].head_local - B["finger5-1." + s].head_local).normalized()
    nn = dd.cross(aa) if s == "L" else aa.cross(dd); nn.normalize()
    ctr = wr + (f3 - wr) * 0.75
    return ctr, dd, aa, nn

def screen_mat(name, image, reveal=False, strength=3.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    for x in list(n):
        if x.type != 'OUTPUT_MATERIAL': n.remove(x)
    tc = n.new('ShaderNodeTexCoord'); ti = n.new('ShaderNodeTexImage'); ti.image = image; l.new(tc.outputs['UV'], ti.inputs['Vector'])
    # pixel grid for macro passes
    grid = n.new('ShaderNodeTexBrick'); grid.inputs['Scale'].default_value = 300; grid.inputs['Mortar Size'].default_value = 0.08
    grid.inputs['Color1'].default_value = (1, 1, 1, 1); grid.inputs['Color2'].default_value = (1, 1, 1, 1); grid.inputs['Mortar'].default_value = (0.2, 0.2, 0.2, 1)
    l.new(tc.outputs['UV'], grid.inputs['Vector'])
    mm = n.new('ShaderNodeMix'); mm.data_type = 'RGBA'; mm.blend_type = 'MULTIPLY'; mm.inputs['Factor'].default_value = 1.0
    l.new(ti.outputs['Color'], mm.inputs['A']); l.new(grid.outputs['Color'], mm.inputs['B']); col = mm.outputs['Result']
    if reveal:
        sp = n.new('ShaderNodeSeparateXYZ'); l.new(tc.outputs['UV'], sp.inputs['Vector'])
        rv = n.new('ShaderNodeValue'); rv.name = "Reveal"; rv.outputs[0].default_value = 0.0
        cm = n.new('ShaderNodeMath'); cm.operation = 'GREATER_THAN'; l.new(sp.outputs['Y'], cm.inputs[0]); l.new(rv.outputs[0], cm.inputs[1])
        mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['B'].default_value = (0.96, 0.96, 0.94, 1)
        l.new(cm.outputs[0], mx.inputs['Factor']); l.new(col, mx.inputs['A']); col = mx.outputs['Result']
    em = n.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = strength; l.new(col, em.inputs['Color'])
    l.new(em.outputs['Emission'], n["Material Output"].inputs['Surface'])
    return m

WORK = os.path.join(D, "..", "work"); os.makedirs(WORK, exist_ok=True)
note_img = bpy.data.images.load(os.path.join(WORK, "note_blur.png")); note_img.pack()
share_img = bpy.data.images.load(os.path.join(WORK, "share_icons.png")); share_img.pack()
M_note = screen_mat("PhoneNote", note_img, reveal=True, strength=2.0)
M_share = screen_mat("PhoneShare", share_img, strength=4.0)

def make_phone(name, scr_mat, cl):
    o = glb(os.path.join(A, "objv", "phone.glb"), name, cl)
    # phone mesh: thickness along X; centre it
    o.data.transform(Matrix.Translation(Vector((0, 0, -o.dimensions.z / 2))))
    bpy.ops.mesh.primitive_plane_add(size=1); s = bpy.context.object; s.name = name + "_screen"
    s.scale = (0.138, 0.064, 1); bpy.ops.object.transform_apply(scale=True)
    for lp in s.data.uv_layers[0].data: lp.uv = (lp.uv[1], 1 - lp.uv[0])
    s.rotation_euler = (0, math.radians(-90), 0); s.location = (-o.dimensions.x / 2 - 0.0006, 0, 0)   # screen faces away from the palm
    s.data.materials.append(scr_mat); s.parent = o
    for u in list(s.users_collection): u.objects.unlink(s)
    cl.objects.link(s)
    s2 = s.copy(); s2.data = s.data.copy(); s2.name = name + "_screenB"; s2.parent = o
    s2.rotation_euler = (0, math.radians(90), 0); s2.location = (o.dimensions.x / 2 + 0.0006, 0, 0); cl.objects.link(s2)
    return o, s

def attach_phone(phone, rig, s="R"):
    ctr, dd, aa, nn = palm_frame(rig, s)
    # phone local axes: +X = screen normal (= palm normal), +Z = long axis (= finger direction), Y = across
    Xa = nn; Za = (dd - nn * dd.dot(nn)).normalized(); Ya = Za.cross(Xa)
    M = Matrix((Xa, Ya, Za)).transposed().to_4x4(); M.translation = ctr + nn * 0.016
    bone_parent(phone, rig, "wrist." + s, rig.matrix_world @ M)

ph1, ph1s = make_phone("FanPhone", M_note, C_CHAR)
attach_phone(ph1, FR, "R")
nd = M_note.node_tree.nodes["Reveal"].outputs[0]
for t, v in ((13.4, 1.0), (13.6, 0.86), (14.2, 0.72), (14.8, 0.58), (15.2, 0.44), (15.6, 0.30), (15.8, 0.1)):
    nd.default_value = v; nd.keyframe_insert("default_value", frame=F(t))
ph1.scale = (1, 1, 1)
for t, v in ((12.8, 0.0), (12.85, 1.0)):   # drawn from her pocket under her hand
    ph1.scale = (v, v, v) if v else (0.001,) * 3; ph1.keyframe_insert("scale", frame=F(t))
for t in (34.0,):
    ph1.keyframe_insert("scale", frame=F(t) - 1); ph1.scale = (0.001,) * 3; ph1.keyframe_insert("scale", frame=F(t))
ph2, ph2s = make_phone("ManPhone", M_share, C_CHAR)
attach_phone(ph2, MBR, "R")
ph2.scale = (0.001,) * 3; ph2.keyframe_insert("scale", frame=F(29.93)); ph2.scale = (1, 1, 1); ph2.keyframe_insert("scale", frame=F(29.97))

# beanie + scarf on the fan's head / neck bones
def fit_to_head(obj, rig, bone, height_frac=0.62, scale_mul=1.0, z_off=0.0, y_off=0.0):
    B = rig.data.bones[bone]; hd = B.head_local
    body = [c for c in rig.children if c.name.endswith(".body")][0]
    top = max((rig.matrix_world @ v.co).z for v in body.data.vertices if abs(v.co.x) < 0.02 and v.co.z > hd.z)
    dims = obj.dimensions
    s = 0.205 / max(dims.x, dims.y) * scale_mul
    obj.data.transform(Matrix.Scale(s, 4))
    M = Matrix.Translation(Vector((0, y_off, top - obj.dimensions.z * height_frac + z_off)))
    bone_parent(obj, rig, bone, rig.matrix_world @ M)
beanie = glb(os.path.join(A, "objv", "beanie.glb"), "Beanie", C_CHAR)
beanie.data.transform(Matrix.Rotation(math.pi / 2 * 0, 4, 'Z'))
for m in beanie.data.materials: pass
fit_to_head(beanie, FR, "head", height_frac=0.70, scale_mul=1.02, y_off=0.012)
sh = beanie.modifiers.new("fit", 'SHRINKWRAP'); sh.target = [c for c in FR.children if c.name.endswith(".body")][0]
sh.wrap_mode = 'OUTSIDE'; sh.offset = 0.006; sh.wrap_method = 'NEAREST_SURFACEPOINT'
sh.vertex_group = ""
scarf = glb(os.path.join(A, "objv", "scarf.glb"), "Scarf", C_CHAR)
sd = scarf.dimensions; scarf.data.transform(Matrix.Scale(0.30 / max(sd.x, sd.y), 4))
nb = FR.data.bones["neck01"].head_local
bone_parent(scarf, FR, "neck01", FR.matrix_world @ Matrix.Translation(Vector((0, 0.0, nb.z - scarf.dimensions.z * 0.55))))
sw = scarf.modifiers.new("fit", 'SHRINKWRAP'); sw.target = sh.target; sw.wrap_mode = 'OUTSIDE'; sw.offset = 0.01
M_knit = pbr("ScarfKnit", "knitted_fleece", 0.06, tint=(0.75, 0.18, 0.12))
M_beanie = pbr("BeanieKnit", "knitted_fleece", 0.05, tint=(0.25, 0.30, 0.42))
scarf.data.materials.clear(); scarf.data.materials.append(M_knit)
beanie.data.materials.clear(); beanie.data.materials.append(M_beanie)
for o in (beanie, scarf):
    uvbox(o, 0.1)
for m in (M_knit, M_beanie):
    for n_ in m.node_tree.nodes:
        if n_.type == 'TEX_COORD': pass

# the mole on the manager's neck: decal shrinkwrapped to the skin, parented to the neck bone
def neck_mole(rig, nm):
    body = [c for c in rig.children if c.name.endswith(".body")][0]
    nb = rig.data.bones["neck02"].head_local
    best = None
    tgt = Vector((0.035, 0.07, nb.z + 0.01))
    for v in body.data.vertices:
        d = (v.co - tgt).length
        if best is None or d < best[0]: best = (d, v)
    v = best[1]; co = v.co.copy(); nrm = v.normal.copy()
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=12, y_subdivisions=12, size=0.016)
    o = bpy.context.object; o.name = nm
    for u in list(o.users_collection): u.objects.unlink(o)
    C_CHAR.objects.link(o)
    m = skin_material(nm + "Mat", mole=True, scale=1000.0)
    n, l = m.node_tree.nodes, m.node_tree.links
    out = n["Material Output"]; pr = n["Principled BSDF"]; mk = n["MoleMask"]
    tr = n.new('ShaderNodeBsdfTransparent'); mix = n.new('ShaderNodeMixShader')
    l.new(mk.outputs['Result'], mix.inputs['Fac']); l.new(tr.outputs['BSDF'], mix.inputs[1]); l.new(pr.outputs['BSDF'], mix.inputs[2])
    l.new(mix.outputs['Shader'], out.inputs['Surface'])
    # mapping uses object coordinates of the decal itself
    o.data.materials.append(m)
    z = nrm.normalized(); x = Vector((1, 0, 0)); x = (x - z * x.dot(z)).normalized(); y = z.cross(x)
    M = Matrix((x, y, z)).transposed().to_4x4(); M.translation = co + nrm * 0.0008
    bone_parent(o, rig, "neck02", rig.matrix_world @ M)
    s = o.modifiers.new("fit", 'SHRINKWRAP'); s.target = body; s.wrap_mode = 'OUTSIDE'; s.offset = 0.0006
    return o, co, nrm
moleA, MOLE_CO, MOLE_N = neck_mole(MR, "NeckMoleA")
moleB, _, _ = neck_mole(MBR, "NeckMoleB")
# bandage on ManagerB after the excision
bpy.ops.mesh.primitive_grid_add(x_subdivisions=10, y_subdivisions=10, size=0.03)
band = bpy.context.object; band.name = "Bandage"
for u in list(band.users_collection): u.objects.unlink(band)
C_CHAR.objects.link(band)
band.data.materials.append(pbr("Gauze", "knitted_fleece", 0.02, tint=(0.95, 0.93, 0.88)))
uvbox(band, 0.03)
z = MOLE_N.normalized(); x = Vector((1, 0, 0)); x = (x - z * x.dot(z)).normalized(); y = z.cross(x)
M = Matrix((x, y, z)).transposed().to_4x4(); M.translation = MOLE_CO + MOLE_N * 0.0015
bone_parent(band, MBR, "neck02", MBR.matrix_world @ M)
bsw = band.modifiers.new("fit", 'SHRINKWRAP'); bsw.target = [c for c in MBR.children if c.name.endswith(".body")][0]; bsw.wrap_mode = 'OUTSIDE'; bsw.offset = 0.0012
band.scale = (0.001,) * 3; band.keyframe_insert("scale", frame=F(27.83)); band.scale = (1, 1, 1); band.keyframe_insert("scale", frame=F(27.87))
# carried in her left hand from the pocket, pressed on at 28.2 (Child Of the hand, then released onto the neck)
sc.frame_set(F(28.2)); bpy.context.view_layer.update()
_co = band.constraints.new('CHILD_OF'); _co.target = DR; _co.subtarget = "wrist.L"
_co.inverse_matrix = (DR.matrix_world @ DR.pose.bones["wrist.L"].matrix).inverted()
_co.influence = 1.0; _co.keyframe_insert("influence", frame=F(28.2)); _co.influence = 0.0; _co.keyframe_insert("influence", frame=F(28.27))
for _f, _v in ((1, False), (F(28.27), True)):
    bsw.show_viewport = bsw.show_render = _v; bsw.keyframe_insert("show_viewport", frame=_f); bsw.keyframe_insert("show_render", frame=_f)
moleB.keyframe_insert("scale", frame=F(28.2)); moleB.scale = (0.001,) * 3; moleB.keyframe_insert("scale", frame=F(28.3))

# dermatoscope + forceps in the doctor's hands
M_metal = mat("SteelBrushed", (0.7, 0.71, 0.72), 0.25, 1.0, noise=0.15, nscale=400)
M_blk = mat("ScopeGrip", (0.03, 0.03, 0.035), 0.5, noise=0.4, nscale=300)
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.014, depth=0.13); scope = bpy.context.object; scope.name = "Dermatoscope"
scope.data.materials.append(M_blk)
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.024, depth=0.03, location=(0, 0, 0.075)); head_ = bpy.context.object
head_.data.materials.append(M_metal)
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.019, depth=0.002, location=(0, 0, 0.091)); lens = bpy.context.object
lens.data.materials.append(mat("ScopeLens", (0.05, 0.07, 0.08), 0.05, metal=0.3))
for o in (head_, lens): o.select_set(True)
scope.select_set(True); bpy.context.view_layer.objects.active = scope; bpy.ops.object.join()
for u in list(scope.users_collection): u.objects.unlink(scope)
C_CHAR.objects.link(scope)
b_ = scope.modifiers.new("bev", 'BEVEL'); b_.width = 0.002; b_.segments = 2
ctr, dd, aa, nn = palm_frame(DR, "R")
Za = dd; Xa = aa; Ya = Za.cross(Xa)
M = Matrix((Xa, Ya, Za)).transposed().to_4x4(); M.translation = ctr + nn * 0.022
bone_parent(scope, DR, "wrist.R", DR.matrix_world @ M)
scope.keyframe_insert("scale", frame=F(25.45)); scope.scale = (0.001,) * 3; scope.keyframe_insert("scale", frame=F(25.5))
# forceps holding a folded gauze square (no blood detail)
bm_ = bpy.data.meshes.new("Forceps"); import bmesh as _bm
bb_ = _bm.new()
for sgn in (1, -1):
    vs_ = [bb_.verts.new((sgn * 0.002 + sgn * 0.004 * (1 - u), 0, u * 0.12)) for u in (0, 0.5, 1)]
for v_ in bb_.verts: pass
bb_.to_mesh(bm_)
fc_ = bpy.data.curves.new("ForcepsC", 'CURVE'); fc_.dimensions = '3D'; fc_.bevel_depth = 0.0016
for sgn in (1, -1):
    sp_ = fc_.splines.new('POLY'); sp_.points.add(2)
    for i_, (xx, zz) in enumerate(((sgn * 0.001, 0.0), (sgn * 0.007, 0.07), (sgn * 0.002, 0.13))): sp_.points[i_].co = (xx, 0, zz, 1)
forc = bpy.data.objects.new("Forceps", fc_); forc.data.materials.append(M_metal); C_CHAR.objects.link(forc)
ctr, dd, aa, nn = palm_frame(DR, "R")
M = Matrix((aa, dd.cross(aa), dd)).transposed().to_4x4(); M.translation = ctr + nn * 0.015 - dd * 0.03
bone_parent(forc, DR, "wrist.R", DR.matrix_world @ M)
forc.scale = (0.001,) * 3; forc.keyframe_insert("scale", frame=F(25.98)); forc.scale = (1, 1, 1); forc.keyframe_insert("scale", frame=F(26.02))
forc.keyframe_insert("scale", frame=F(28.68)); forc.scale = (0.001,) * 3; forc.keyframe_insert("scale", frame=F(28.72))

# sticks for the skaters and the finale players
stick_src = glb(os.path.join(A, "objv", "stick.glb"), "StickSrc", C_CHAR)
sd = stick_src.dimensions; stick_src.data.transform(Matrix.Scale(1.55 / max(sd.x, sd.y, sd.z), 4))
stick_src.hide_render = stick_src.hide_viewport = True
for r in SKATE:
    st = stick_src.copy(); st.hide_render = st.hide_viewport = False; C_CHAR.objects.link(st)
    ctr, dd, aa, nn = palm_frame(r, "R")
    M = Matrix((dd, aa, dd.cross(aa))).transposed().to_4x4(); M.translation = ctr + nn * 0.02
    bone_parent(st, r, "wrist.R", r.matrix_world @ M)

# the cheque: blank, big, paper on foam board, held at its edges by her hands (finale)
M_paper = mat("ChequePaper", (0.93, 0.92, 0.88), 0.7, noise=0.15, nscale=300)
cq = box("Cheque", (0.95, 0.012, 0.45), (0, 0, 0), M_paper, C_CHAR, bevel=0.003)
cq.location = FIN + Vector((-0.35, -0.42, 1.02)); cq.rotation_euler.z = 0
# follow the fan's body yaw: parent to the fan's root bone at rest
cq.scale = (0.001,) * 3; cq.keyframe_insert("scale", frame=F(37.95)); cq.scale = (1, 1, 1); cq.keyframe_insert("scale", frame=F(38.0))
# blue border stripe (no text)
cb_ = box("ChequeBorder", (0.97, 0.010, 0.47), (0, 0, 0), mat("ChequeBlue", (0.08, 0.2, 0.45), 0.6, noise=0.1), C_CHAR, bevel=0.002)
cb_.parent = cq; cb_.matrix_parent_inverse.identity(); cb_.location = (0, 0.003, 0)

# ================================================================== FX: confetti, camera flashes, door, monitor, bus, TV, windows
M_conf = [mat(f"Confetti{i}", c_, 0.4, noise=0.2, nscale=200) for i, c_ in enumerate(((0.9, 0.1, 0.1), (0.1, 0.3, 0.9), (0.95, 0.8, 0.1), (0.95, 0.95, 0.95), (0.1, 0.7, 0.3)))]
bpy.ops.mesh.primitive_plane_add(size=0.035); _cm = bpy.context.object.data; _cm.name = "ConfMesh"; _cm.materials.append(M_conf[0])
bpy.data.objects.remove(bpy.context.object)
for i_ in range(260):
    cf = bpy.data.objects.new(f"Conf{i_}", _cm); C_FX.objects.link(cf)
    cf.material_slots[0].link = 'OBJECT'; cf.material_slots[0].material = M_conf[i_ % 5]
    x0, y0 = FIN.x + random.uniform(-5, 5), FIN.y + random.uniform(-4, 4); t0 = 38.0 + random.uniform(-0.6, 1.5)
    z0 = 10.5; spd = random.uniform(1.2, 2.0); ph = random.random() * 6.28
    cf.location = (x0, y0, 30); cf.keyframe_insert("location", frame=F(t0) - 1)
    for k_ in range(0, 420, 8):
        t = t0 + k_ / 60.0; z = z0 - spd * (k_ / 60.0)
        if t > 44.3: break
        cf.location = (x0 + 0.4 * math.sin(t * 2.5 + ph), y0 + 0.3 * math.cos(t * 2.1 + ph), max(0.003, z))
        cf.rotation_euler = (t * 4 + ph, t * 3 + ph, t * 2)
        if z <= 0.003: cf.rotation_euler = (0, 0, ph)
        cf.keyframe_insert("location", frame=F(t)); cf.keyframe_insert("rotation_euler", frame=F(t))
# camera flashes in the crowd at the finale
for i_ in range(10):
    L = bpy.data.lights.new(f"Flash{i_}", 'POINT'); L.shadow_soft_size = 0.05; L.color = (0.95, 0.97, 1.0)
    lo = bpy.data.objects.new(L.name, L); C_FX.objects.link(lo)
    lo.location = (random.uniform(-8, 8), random.choice((2.5, 3.5, 4.5, -34.5, -35.5)), random.uniform(1.5, 3.5))
    for k_ in range(4):
        t = 38.4 + random.uniform(0, 5.4)
        L.energy = 0; L.keyframe_insert("energy", frame=F(t) - 2); L.energy = 400; L.keyframe_insert("energy", frame=F(t))
        L.energy = 0; L.keyframe_insert("energy", frame=F(t) + 3)
    L.energy = 0; L.keyframe_insert("energy", frame=1)
# clinic door swings open as the camera arrives
dp = bpy.data.objects["DoorPivot"]
dp.rotation_euler.z = 0; dp.keyframe_insert("rotation_euler", frame=F(21.6))
dp.rotation_euler.z = R_(-100); dp.keyframe_insert("rotation_euler", frame=F(22.4))
# monitor trace scrolls
tm = bpy.data.materials["MonitorTrace"].node_tree.nodes["TraceMap"]
tm.inputs['Location'].default_value = (0, 0, 0); tm.inputs['Location'].keyframe_insert("default_value", frame=1)
tm.inputs['Location'].default_value = (-44.0, 0, 0); tm.inputs['Location'].keyframe_insert("default_value", frame=2640)
# bus drives through the city
busO = bpy.data.objects["Bus"]; CT = Vector((-300, 0, 0))
busO.location = CT + Vector((-45, -4, 0)); busO.keyframe_insert("location", frame=F(31.5))
busO.location = CT + Vector((10, -4, 0)); busO.keyframe_insert("location", frame=F(36.0))
riders = []
for i_ in range(4):
    r = dup_rig(SRC[(i_ + 2) % 6], f"Rider{i_}", C_CHAR); riders.append(r)
    r.parent = busO; r.matrix_parent_inverse.identity()
    for f in range(F(30.0), F(37.0), 30):
        seated_fk(r, f, Vector((-3.2 + i_ * 1.9, 0.55 if i_ % 2 else -0.55, 0.55)), 90, phone=True, head=(25, 0), sway=math.sin(f * 0.05 + i_))
# rider phone glows
for i_, r in enumerate(riders):
    gl = plane(f"RiderGlow{i_}", 0.07, 0.14, (0, 0, 0), bpy.data.materials["PhoneGlow"], C_CHAR)
    ctr, dd, aa, nn = palm_frame(r, "R")
    M = Matrix((aa, dd, nn)).transposed().to_4x4(); M.translation = ctr + nn * 0.02
    bone_parent(gl, r, "wrist.R", r.matrix_world @ M)
# windows light up one by one (beats 10-11)
for i_, w_ in enumerate(bpy.data.collections["CITY"].objects):
    if not w_.name.startswith("Win_"): continue
    t = 31.6 + random.uniform(0, 3.8)
    w_.scale = (0.001,) * 3; w_.keyframe_insert("scale", frame=F(t) - 1); w_.scale = (1, 1, 1); w_.keyframe_insert("scale", frame=F(t))
# TV flicker + curtain sway in the home
tv = bpy.data.lights["TVFlicker"]
for f in range(F(35.0), F(38.5), 6):
    tv.energy = 80 + 120 * random.random(); tv.keyframe_insert("energy", frame=f)
# laptop video call screen (blurred face-like blobs, no text) on the classic laptop
ci = bpy.data.images.load(os.path.join(WORK, "call.png")); ci.pack()
M_call = screen_mat("LaptopCall", ci, strength=3.0)
lapscr = plane("LaptopScreen", 0.30, 0.19, (0, 0, 0), M_call, C_HOME)

# ================================================================== world switching
nt = sc.world.node_tree
def wkey(f, a, b, c_):
    for nm, v in (("WMIX1", a), ("WMIX2", b), ("WMIX3", c_)):
        s_ = nt.nodes[nm].inputs['Factor']; s_.default_value = v; s_.keyframe_insert("default_value", frame=f)
wkey(1, 0, 0, 0)

for _o in ("Beanie", "Scarf"):
    _b = bpy.data.objects[_o]
    for _f, _v in ((F(34.0) - 1, 1), (F(34.0), 0.001), (F(37.9), 0.001), (F(37.9) + 1, 1)):
        _b.scale = (_v,) * 3; _b.keyframe_insert("scale", frame=_f)
print("ANIM_OK")
exec(open(os.path.join(D, "03b_fixes.py")).read())
exec(open(os.path.join(D, "04_camera.py")).read())
