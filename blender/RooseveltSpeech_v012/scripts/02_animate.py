"""RooseveltSpeech v012 stage B: acting, the ONE bullet, the wound, the ONE camera (no cuts), the flashes, the VO.
blender -b a.blend --python 02_animate.py -- <vo.mp3> <out.blend>
Built to the client's VO from the start (v011 timing, frames 1-1307). Beats (VO frames): 1 'The bullet hit him' /
173 'somehow, he stayed on his feet' / 265 'So how was that possible?' / 389 'a thick, folded-up speech' /
615 'a metal glasses case' / 737 'The bullet tore through both' / 847 'slowed it down ... lungs' /
1028 'And despite the wound' / 1139 'he insisted on finishing his 90-minute speech'.
Set changes happen inside short full-frame flashes: STREET -> MACRO at 390 (the camera dives into the coat hole),
MACRO -> HALL at 1028."""
import bpy, sys, math, random, os, json
from mathutils import Vector, Matrix, Quaternion, Euler
from mathutils.bvhtree import BVHTree
PIPE = "/home/user/Muhammed/blender/pipeline"
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(PIPE + "/anim_lib.py").read())
exec(open(PIPE + "/hand_poses.py").read())
exec(open(HERE + "/lib_anim.py").read())
args = sys.argv[sys.argv.index("--") + 1:]
VO, OUT = args[0], args[1]
random.seed(24)
END = 1307
SW1, SW2 = 390, 1028
F_SHOT, F_HIT = 40, 128
BEATS = [(1, "The bullet hit him"), (173, "but somehow, he stayed on his feet"), (265, "So how was that possible?"),
         (389, "Roosevelt had a thick, folded-up speech"), (615, "along with a metal glasses case"),
         (737, "The bullet tore through both"), (847, "which slowed it down"), (1028, "And despite the wound"),
         (1139, "he insisted on finishing his 90-minute speech")]
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); LOG.append(s); print("LOG", s)
O = bpy.data.objects
MX = Vector((40.0, 0.0, 0.0)); HX = Vector((0.0, 60.0, 0.0)); STAGE_Z = 1.0
HERO, GUN = O["Hero"], O["Gunman"]
EXTRAS = [O["Extra%d" % i] for i in range(4)]
BUL, TRAIL, TIP, REV, SPEECH, HOLE = O["Bullet"], O["BulletTrail"], O["TipCtl"], O["Revolver"], O["Speech"], O["CoatHole"]
HSUIT = O["Hero.male_elegantsuit01"]

def rz(yaw): return Matrix.Rotation(math.radians(yaw), 3, 'Z')

# ================================================================== rigs
class Actor:
    def __init__(self, rig):
        self.rig = rig; self.CT = make_human_ctrl(rig); add_hand_limits(rig)
        for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'
        for s in "LR":
            lo = rig.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(145)
        self.H = Human(self.CT); self.hs = None
        self.base = {}; self.yaw = {}
    def key_pole(self, s, f, target, kind="elbow"):
        n = ("Pole_elbow." if kind == "elbow" else "Pole_knee.") + s; pb = self.CT.PB[n]
        pb.location = self.CT.rest(n).to_3x3().inverted() @ (Vector(target) - self.CT.BN[n].head_local)
        pb.keyframe_insert("location", frame=f, group=n)
    def key_spine(self, f, flex=0.0, twist=0.0, side=0.0):
        for n, w in Human.SPINE_W.items():
            self.CT.key_rot(n, f, [("X", flex * w), ("Y", side * w), ("Z", twist * w)])
    def head_signs(self):
        if self.hs: return self.hs
        rig = self.rig; pb = rig.pose.bones["head"]; q0 = pb.rotation_quaternion.copy(); upd()
        e0 = Wh(rig, "eye.L"); out = {}
        for ax, i in (("X", 0), ("Z", 2)):
            pb.rotation_quaternion = Quaternion(Vector([1 if k == i else 0 for k in range(3)]), math.radians(10)); upd()
            out[ax] = rig.matrix_world.inverted() @ Wh(rig, "eye.L") - rig.matrix_world.inverted() @ e0; pb.rotation_quaternion = q0; upd()
        self.hs = (1 if out["X"].z < 0 else -1, 1 if out["Z"].x > 0 else -1)
        return self.hs
    def key_head(self, f, yaw, pitch, roll=0.0):
        """yaw +: toward his own left; pitch +: look down"""
        sx, sz = self.head_signs()
        for n, w in (("neck01", 0.25), ("neck02", 0.25), ("neck03", 0.2), ("head", 0.3)):
            self.CT.key_rot(n, f, [("X", sx * pitch * w), ("Y", roll * w), ("Z", sz * yaw * w)])
    def stand(self, f, base, yaw, flex=2.0, side=0.0, dz=0.0, feet=None):
        """root over the feet; both feet planted flat ON the floor at base.z (IK), knees forward"""
        base = Vector(base); R = rz(yaw)
        self.H.key_root(f, base + Vector((0, 0, self.H.root_head.z - 0.012 + dz)), yaw=yaw, flex=flex, side=side)
        for s, sg in (("L", 1), ("R", -1)):
            a = self.CT.BN["foot." + s].head_local
            off = (feet or {}).get(s, Vector((0, 0, 0)))
            tgt = base + R @ Vector((sg * 0.12 + off.x, off.y, 0)) + Vector((0, 0, a.z + off.z))
            M = Matrix.Translation(tgt) @ R.to_4x4() @ Matrix.Translation(-a) @ self.CT.rest("IK_foot." + s)
            self.CT.key_world("IK_foot." + s, f, M)
            self.key_pole(s, f, tgt + R @ Vector((sg * 0.05, -0.8, 0.45)), kind="knee")
        self.base[f] = base; self.yaw[f] = yaw
    def shoulder(self, s, f):
        fs(f); return Wh(self.rig, "upperarm01." + s)
    def hand(self, s, f, local_off, d_loc, n_loc, pole_loc, yaw, pose=None, amount=1.0, ref=None):
        """wrist at shoulder + R(yaw)*local_off (shoulder sampled at frame ref or f); directions in the body frame"""
        R = rz(yaw); sh = self.shoulder(s, ref or f)
        W = sh + R @ Vector(local_off)
        self.H.key_hand(s, f, W, R @ Vector(d_loc), R @ Vector(n_loc), pole=sh + R @ Vector(pole_loc))
        if pose: apply_pose(self.rig, s, pose, f, amount=amount)
        return W
    def hang(self, s, f, yaw, fwd=0.05, drop=0.52, out=0.0, ref=None):
        sx = 1 if s == "L" else -1
        return self.hand(s, f, (sx * (0.075 + out), -fwd, -drop), (sx * 0.08, -0.25, -1.0), (-sx, 0.0, 0.0),
                         (sx * 0.25, 0.45, -0.25), yaw, pose="relaxed", ref=ref)

ACT = {}
for r in [HERO, GUN] + EXTRAS:
    ACT[r.name] = Actor(r)
A_H, A_G = ACT["Hero"], ACT["Gunman"]

# ---- 8 audience copies for the hall (linked mesh data, own pose and keys, re-tinted suits)
def copy_actor(src, name, tint_mul):
    r = src.copy(); r.name = name; bpy.data.collections["CHARS"].objects.link(r)
    if r.animation_data: r.animation_data_clear()
    for c in src.children:
        if c.type != 'MESH' or c.name.endswith((".eyebrow001", ".eyebrow003", ".eyebrow005", ".eyebrow009")) and False: pass
        if c.type != 'MESH': continue
        c2 = c.copy(); c2.name = name + "." + c.name.split(".", 1)[1]; c2.parent = r
        bpy.data.collections["CHARS"].objects.link(c2)
        for m in c2.modifiers:
            if m.type == 'ARMATURE': m.object = r
        if "elegantsuit" in c2.name:
            for i, sl in enumerate(c2.material_slots):
                m2 = sl.material.copy(); sl.link = 'OBJECT'; sl.material = m2
                for nd in m2.node_tree.nodes:
                    if nd.type == 'MIX' and nd.blend_type == 'MULTIPLY': nd.inputs['B'].default_value = (*tint_mul, 1)
    for pb in r.pose.bones:
        for c_ in pb.constraints:
            if getattr(c_, "target", None) == src: c_.target = r
            if getattr(c_, "pole_target", None) == src: c_.pole_target = r
    a = Actor.__new__(Actor); a.rig = r; a.CT = Rig(r); a.H = Human(a.CT); a.hs = None; a.base = {}; a.yaw = {}
    for pb in r.pose.bones: pb.rotation_mode = 'QUATERNION'
    return a
TINTS = [(0.30, 0.12, 0.08), (0.08, 0.10, 0.30), (0.25, 0.25, 0.27), (0.10, 0.22, 0.12), (0.35, 0.22, 0.10), (0.06, 0.06, 0.08),
         (0.32, 0.05, 0.08), (0.18, 0.14, 0.24)]
AUD = [ACT[e.name] for e in EXTRAS]
for k in range(8):
    AUD.append(copy_actor(EXTRAS[k % 4], "Aud%d" % k, TINTS[k]))

# ================================================================== HERO acting
HB0 = Vector((0, 0, 0)); HB1 = HX + Vector((0, 0, STAGE_Z))
# --- street body: steady, waving (to 128) -> jolt back (128-150) -> sway, a step, plants (150-264) -> slow-time (265-388)
for f, flex, side, dz in ((1, 2.0, 0.0, 0.0), (60, 2.5, 1.0, 0.0), (128, 2.0, 0.5, 0.0), (136, -9.0, -4.0, -0.012), (150, -6.0, 5.0, -0.02),
                          (175, 4.0, -5.0, -0.018), (200, 2.0, 3.0, -0.008), (230, 1.0, -1.5, -0.004), (264, 1.5, 0.0, 0.0),
                          (330, 2.5, 0.0, 0.0), (388, 2.0, 0.0, 0.0), (1027, 2.0, 0.0, 0.0)):
    feet = None
    if 182 <= f <= 330 or f == 1027 or f == 388: feet = {"R": Vector((-0.02, 0.10, 0))}     # the right foot stepped back to plant
    A_H.stand(f, HB0, 0.0, flex=flex, side=side, dz=dz, feet=feet)
# the planting step: right foot lifts and moves 10 cm back between 175 and 190
A_H.stand(182, HB0, 0.0, flex=3.0, side=-3.0, dz=-0.014, feet={"R": Vector((-0.01, 0.05, 0.05))})
def spine_h(f):
    return pchip([(1, 2.0), (128, 2.0), (136, -10.0), (150, -7.0), (175, 5.0), (210, 2.0), (264, 1.0), (330, 3.0), (388, 2.0)])(f)
for f in list(range(1, 389, 12)) + [388]:
    br = 1.0 * math.sin(2 * math.pi * f / (200 if f < 128 else 90))
    A_H.key_spine(f, flex=spine_h(f) + br, twist=pchip([(1, -4), (128, -4), (140, 3), (200, 0), (388, 0)])(f),
                  side=pchip([(1, 0), (128, 0), (140, -3), (160, 3), (200, -1), (240, 0), (388, 0)])(f))
HEADK = [(1, -6, -4), (40, -8, -4), (60, -14, -1), (128, -10, -2), (136, -2, -14), (150, 4, -6), (190, -6, 2), (264, -2, 0),
         (290, 0, 6), (330, 4, 16), (360, 0, 6), (388, 0, 2)]
hy = pchip([(f, y) for f, y, p in HEADK]); hp = pchip([(f, p) for f, y, p in HEADK])
for f in list(range(1, 389, 6)) + [388]:
    A_H.key_head(f, hy(f), hp(f))
# face: genial smile while waving -> shock and pain at the hit -> grits, determined -> puzzled look down at his chest
for f, sm, br, jaw, sq in ((1, 0.6, 0.3, 0.05, 0.1), (110, 0.6, 0.3, 0.08, 0.1), (128, 0.5, 0.3, 0.05, 0.1), (134, -0.5, 0.9, 0.45, 0.0),
                           (150, -0.6, -0.7, 0.30, 0.6), (190, -0.3, -0.6, 0.10, 0.4), (240, 0.0, -0.4, 0.02, 0.2), (264, 0.0, -0.3, 0.0, 0.1),
                           (300, -0.1, 0.5, 0.1, 0.0), (388, -0.1, 0.4, 0.05, 0.0)):
    key_face(HERO, f, smile=sm, brow=br, jaw=jaw, squint=sq)
# arms: right hand waves high (open palm, elbow bent ~90) until the hit, then drops to his side; left hangs
WAVE = []
for f in range(1, 129, 6):
    ph = math.sin(2 * math.pi * f / 40.0)
    A_H.hand("R", f, (-0.20 + 0.09 * ph, -0.10, 0.34), (-0.15 + 0.45 * ph, -0.15, 1.0), (0.0, -1.0, 0.0), (-0.45, 0.25, -0.30), 0.0,
             pose="open_alarm" if f == 1 else None, ref=1)
apply_pose(HERO, "R", "open_alarm", 128)
A_H.hand("R", 134, (-0.16, -0.22, 0.12), (-0.1, -0.4, 0.6), (0.2, -0.8, 0.0), (-0.45, 0.30, -0.30), 0.0, ref=134)
A_H.hand("R", 142, (-0.06, -0.30, -0.28), (0.3, -0.5, -0.6), (0.4, 0.4, 0.2), (-0.45, 0.30, -0.30), 0.0, pose="relaxed", ref=142)
A_H.hang("R", 165, 0.0, fwd=0.06, drop=0.50, ref=165)
for f in (205, 240, 285):
    A_H.hand("R", f, (0.04, -0.27, -0.22), (0.6, -0.2, 0.25), (0.0, 1.0, 0.0), (-0.40, 0.25, -0.35), 0.0, pose="relaxed", ref=f)
for f in (330, 388):
    A_H.hang("R", f, 0.0, fwd=0.06, drop=0.50, ref=f)
for f in (1, 60, 128, 140, 165, 200, 264, 330, 388):
    A_H.hang("L", f, 0.0, fwd=0.05 + (0.04 if 130 < f < 200 else 0.0), drop=0.50, ref=f)
blinks(HERO, [70, 200, 300])

# --- hall: on the stage beside the lectern, right hand holds the holed speech up; from 1139 the left fist rises
for f, flex, side in ((1028, 3.0, 0.0), (1080, 4.0, 1.5), (1139, 1.0, 0.0), (1170, -2.0, -1.5), (1230, 0.0, 1.0), (1280, -1.5, 0.0), (END, -1.0, 0.0)):
    A_H.stand(f, HB1, 0.0, flex=flex, side=side)
for f in list(range(1028, END + 1, 15)) + [END]:
    br = 1.2 * math.sin(2 * math.pi * f / 70)
    A_H.key_spine(f, flex=pchip([(1028, 3), (1139, 2), (1165, -4), (1230, -1), (END, -2)])(f) + br,
                  twist=pchip([(1028, -8), (1060, 6), (1095, -7), (1139, 4), (1170, -6), (1200, 7), (1250, -4), (END, 2)])(f))
HEADH = [(1028, -10, -2), (1060, -20, 4), (1085, 12, -4), (1110, -14, -3), (1139, 0, -6), (1170, 8, -9), (1220, -6, -5), (1270, 2, -7), (END, 0, -6)]
hy2 = pchip([(f, y) for f, y, p in HEADH]); hp2 = pchip([(f, p) for f, y, p in HEADH])
for f in list(range(1028, END + 1, 6)) + [END]:
    A_H.key_head(f, hy2(f), hp2(f))
# speaking: syllable jaw motion (about 4-5 per second) with passion in the brows
rnd = random.Random(7)
f = 1034
while f < END:
    open_ = rnd.uniform(0.25, 0.6) if f > 1045 else 0.1
    passion = 1.0 if f > 1139 else 0.6
    key_face(HERO, f, smile=0.25 if f < 1139 else 0.45, brow=0.5 * passion, jaw=open_, squint=0.1)
    key_face(HERO, f + 6, smile=0.25 if f < 1139 else 0.45, brow=0.45 * passion, jaw=0.06, squint=0.1)
    f += rnd.choice((12, 13, 14, 16))
blinks(HERO, [1090, 1190, 1262])
# right arm: speech raised beside his head toward the audience (elbow bent ~95 deg, fingers up, palm toward the audience)
SPEECH_POSE = [(1028, (-0.16, -0.20, 0.30)), (1055, (-0.14, -0.24, 0.36)), (1080, (-0.17, -0.20, 0.28)), (1105, (-0.13, -0.24, 0.37)), (1139, (-0.17, -0.20, 0.30)), (1170, (-0.12, -0.30, 0.04)), (1200, (-0.11, -0.31, 0.07)), (1240, (-0.12, -0.30, 0.03)), (END, (-0.11, -0.31, 0.06))]
for f, off in SPEECH_POSE:
    A_H.hand("R", f, off, (0.05, -0.12, 1.0), (0.0, -1.0, 0.0), (-0.45, 0.10, -0.30), 0.0, pose="hold_flat_object", ref=1028)
# left: hangs, then the fist rises (1139-1165) and pumps at 1215
for f in (1028, 1080, 1139):
    A_H.hang("L", f, 0.0, fwd=0.05, drop=0.50, ref=1028)
FIST = [(1165, (0.14, -0.14, 0.40)), (1200, (0.15, -0.13, 0.38)), (1215, (0.14, -0.15, 0.46)), (1235, (0.15, -0.14, 0.40)), (END, (0.15, -0.14, 0.42))]
for f, off in FIST:
    A_H.hand("L", f, off, (0.0, -0.10, 1.0), (-1.0, 0.0, 0.0), (0.45, 0.20, -0.25), 0.0, pose="power_fist", ref=1028)
# the jump STREET -> HALL happens at 1027/1028 inside the flash: hold the street pose to 1027
A_H.hang("L", 1027, 0.0, ref=388); A_H.hang("R", 1027, 0.0, ref=388)

# ================================================================== GUNMAN: aims from the crowd, fires at F_SHOT, recoil
GB0 = Vector((-0.72, -3.05, 0)); GYAW = 180.0 + 8.0
for f, flex, side in ((1, 4.0, 0.0), (F_SHOT, 5.0, 0.0), (F_SHOT + 6, 1.0, 1.5), (90, 3.0, 0.5), (200, 2.0, 0.0), (388, 2.0, 0.0)):
    A_G.stand(f, GB0, GYAW, flex=flex, side=side)
for f in (1, F_SHOT, 90, 388):
    A_G.key_spine(f, flex=5.0 if f <= F_SHOT else 2.0, twist=-8.0)
    A_G.key_head(f, 6.0, 2.0)
# right arm extended at the chest of Roosevelt (elbow ~15 deg), wrist braced
HIT_GUESS = Vector((-0.09, -0.12, 1.31))
def aim_dir(f):
    fs(f); sh = Wh(GUN, "upperarm01.R"); return (HIT_GUESS - sh).normalized(), sh
for f, kick in ((1, 0.0), (F_SHOT, 0.0), (F_SHOT + 3, 0.09), (F_SHOT + 10, 0.03), (90, 0.0), (160, -0.15), (388, -0.15)):
    d, sh = aim_dir(1)
    W = sh + d * 0.52 + Vector((0, 0, 0.02 + kick * 0.6))
    if f >= 160: W = sh + d * 0.42 + Vector((0, 0, -0.18))
    dd = (d + Vector((0, 0, kick * 2.5))).normalized()
    side = Vector((0, 0, 1)).cross(dd).normalized()        # palm faces his left (inward), thumb up
    A_G.H.key_hand("R", f, W, dd, side, pole=sh + Vector((0.1, 0.2, -0.45)))
apply_pose(GUN, "R", "wrap_grip", 1)
for f in (1, 90, 388):
    A_G.hang("L", f, GYAW, fwd=0.04, drop=0.50, ref=f)
# the revolver sits IN the wrap grip: grip centred in the curl of the fingers, barrel along the hand, Child Of the wrist
fs(1); upd()
rig = GUN; Mw = rig.matrix_world
def P(b, tail=False): return Mw @ (rig.pose.bones[b].tail if tail else rig.pose.bones[b].head)
curl = [((P("finger%d-1.R" % k) + P("finger%d-3.R" % k, True)) / 2) for k in (2, 3, 4, 5)]
C = sum(curl, Vector()) / 4
wr = P("wrist.R"); dvec = (P("finger3-1.R") - wr).normalized()
avec = (P("finger5-1.R") - P("finger2-1.R")).normalized()          # index -> little finger
nvec = dvec.cross(avec).normalized()
# revolver local frame: barrel +Y, grip down -Z (tilted 0.38 rad), width X. grip centre local (0,-0.034,-0.045)
gaxis = Vector((0, math.sin(0.38), -math.cos(0.38)))                # grip long axis (down) in local
Rloc = Matrix((Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))))
# world: grip axis -> avec, barrel (+Y) ~ dvec orthogonalised
yw = (dvec - avec * dvec.dot(avec)).normalized(); xw = yw.cross(-avec).normalized()
# build rotation mapping local (x, y, gaxis) -> (xw, yw', avec)
ly = Vector((0, 1, 0)); lg = gaxis; lx = Vector((1, 0, 0))
ly2 = (ly - lg * ly.dot(lg)).normalized()
Ml = Matrix((lx, ly2, lg)).transposed(); Mwld = Matrix((xw, yw, avec)).transposed()
Rw = Mwld @ Ml.inverted()
gc_local = Vector((0, -0.034, -0.045))
REV.rotation_mode = 'QUATERNION'
best = None
for shift in [i * 0.002 for i in range(-6, 7)]:
    loc = C + nvec * shift - Rw @ gc_local
    REV.matrix_world = Matrix.Translation(loc) @ Rw.to_4x4(); upd()
    inside = 0; near = 0
    for k in (1, 2, 3, 4, 5):
        for j in (1, 2, 3):
            b = "finger%d-%d.R" % (k, j)
            for u in (0.5, 1.0):
                p_ = P(b).lerp(P(b, True), u)
                d_ = hand_dist = None
                inv = REV.matrix_world.inverted(); ok, lc, nr, ix = REV.closest_point_on_mesh(inv @ p_)
                w_ = REV.matrix_world @ lc; nw = (REV.matrix_world.to_3x3() @ nr).normalized()
                dist = (p_ - w_).length * (1 if (p_ - w_).dot(nw) >= 0 else -1)
                if dist < 0.004: inside += 1
                if dist < 0.02: near += 1
    if best is None or (inside, -near) < (best[0], -best[1]): best = (inside, near, shift)
loc = C + nvec * best[2] - Rw @ gc_local
REV.matrix_world = Matrix.Translation(loc) @ Rw.to_4x4(); upd()
log("revolver grip: fingers inside", best[0], "near", best[1], "shift", best[2])
c = REV.constraints.new('CHILD_OF'); c.target = GUN; c.subtarget = "wrist.R"; fs(1); upd()
c.inverse_matrix = (GUN.matrix_world @ GUN.pose.bones["wrist.R"].matrix).inverted()
REV.matrix_world = Matrix.Translation(loc) @ Rw.to_4x4()
REV.matrix_basis = Matrix.Translation(loc) @ Rw.to_4x4(); upd()
fs(1); upd(); log("revolver world after child-of", tuple(round(x, 3) for x in REV.matrix_world.translation), "want", tuple(round(x, 3) for x in loc))

# ================================================================== EXTRAS: street onlookers, then the hall audience
STREET_POS = [((1.05, 0.75, 0), 18.0), ((-1.05, 0.80, 0), -15.0), ((1.9, -0.9, 0), -115.0), ((-1.7, -1.3, 0), 127.0)]
hall_rows = []
for i in range(12):
    row = i // 6; col_ = i % 6
    x = -3.2 + col_ * 1.25 + (0.55 if row else 0) + random.uniform(-0.15, 0.15)
    y = HX.y - 2.4 - row * 1.3 + random.uniform(-0.15, 0.15)
    hall_rows.append(((x, y, 0), 180.0 + math.degrees(math.atan2(x, 4.5)) * 0.6 + random.uniform(-6, 6)))
for i, a in enumerate(AUD):
    rr = random.Random(100 + i)
    hb, hyaw = hall_rows[i]
    if i < 4:
        sb, syaw = STREET_POS[i]
        for f, flex, dz in ((1, 2.0, 0.0), (F_SHOT + 4, 2.0, 0.0), (F_SHOT + 14, -6.0, -0.02), (120, -3.0, -0.01), (175, -4.0, -0.012), (230, 1.0, 0.0), (388, 2.0, 0.0), (1027, 2.0, 0.0)):
            a.stand(f, sb, syaw, flex=flex, dz=dz)
        for f in (1, 30, F_SHOT + 3):
            a.key_head(f, rr.uniform(-8, 8), rr.uniform(-4, 2))
        a.key_head(F_SHOT + 12, -25 if STREET_POS[i][0][0] > 0 else 25, -2)     # snap toward the shot
        a.key_head(140, rr.uniform(-6, 6), -2); a.key_head(230, rr.uniform(-6, 6), 0); a.key_head(388, rr.uniform(-6, 6), 0)
        for s in "LR":
            sx = 1 if s == "L" else -1
            for f in (1, F_SHOT + 4):
                a.hang(s, f, syaw, ref=f)
            # flinch: hands come up in front of the chest, palms out (well clear of the body)
            a.hand(s, F_SHOT + 18, (sx * 0.02, -0.34, -0.22), (sx * 0.15, -0.2, 1.0), (0, -1.0, 0), (sx * 0.4, 0.2, -0.35), syaw, pose="shield", ref=F_SHOT + 4)
            a.hand(s, 150, (sx * 0.03, -0.32, -0.25), (sx * 0.15, -0.2, 1.0), (0, -1.0, 0), (sx * 0.4, 0.2, -0.35), syaw, ref=F_SHOT + 4)
            a.hang(s, 240, syaw, ref=240); a.hang(s, 388, syaw, ref=388); a.hang(s, 1027, syaw, ref=388)
        for f, br, jaw in ((1, 0.0, 0.0), (F_SHOT + 6, 0.9, 0.5), (130, 0.8, 0.4), (175, 1.0, 0.55), (230, 0.3, 0.1), (388, 0.1, 0.0)):
            key_face(a.rig, f, smile=0.0, brow=br, jaw=jaw)
    # hall: standing ovation with varied timing (fists up on some beats, others clapping-free cheering with open hands)
    for f in (1028, 1100, 1139, 1200, 1250, END):
        a.stand(f, hb, hyaw, flex=rr.uniform(-4, 1), side=rr.uniform(-2, 2))
    for f in list(range(1028, END + 1, 30)) + [END]:
        a.key_head(f, rr.uniform(-5, 5), rr.uniform(-14, -6))
    side_up = rr.choice("LR"); t_up = 1139 + rr.randint(4, 40); t_dn = t_up + rr.randint(40, 90)
    for s in "LR":
        sx = 1 if s == "L" else -1
        a.hang(s, 1028, hyaw, ref=1028); a.hang(s, 1100, hyaw, ref=1028)
        if s == side_up:
            a.hang(s, t_up - 20, hyaw, ref=1028)
            h_ = rr.uniform(0.30, 0.44)
            a.hand(s, t_up, (sx * 0.12, -0.16, h_), (0, -0.1, 1.0), (-sx, 0, 0), (sx * 0.45, 0.2, -0.25), hyaw, pose="power_fist", ref=1028)
            a.hand(s, t_up + 25, (sx * 0.13, -0.15, h_ + 0.05), (0, -0.1, 1.0), (-sx, 0, 0), (sx * 0.45, 0.2, -0.25), hyaw, ref=1028)
            a.hand(s, min(END, t_dn), (sx * 0.12, -0.16, h_), (0, -0.1, 1.0), (-sx, 0, 0), (sx * 0.45, 0.2, -0.25), hyaw, ref=1028)
            if t_dn + 30 < END: a.hang(s, t_dn + 30, hyaw, ref=1028)
        else:
            a.hang(s, END, hyaw, ref=1028)
    for f in range(1032, END, rr.randint(18, 26)):
        key_face(a.rig, f, smile=rr.uniform(0.3, 0.8), brow=rr.uniform(0.2, 0.8), jaw=rr.uniform(0.1, 0.55))
    blinks(a.rig, [rr.randint(1040, 1290)])

# ================================================================== the bullet: street flight -> macro; the coat hole
fs(F_HIT); upd()
def bvh_eval(obj):
    upd(); dg = bpy.context.evaluated_depsgraph_get(); e = obj.evaluated_get(dg); me = e.to_mesh(); Mw_ = obj.matrix_world
    b = BVHTree.FromPolygons([Mw_ @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons]); e.to_mesh_clear(); return b
fs(F_SHOT); upd()
MUZ = REV.matrix_world @ Vector((0, 0.135, 0.0))
fs(F_HIT); upd()
bv = bvh_eval(HSUIT)
hit = bv.ray_cast(MUZ, (HIT_GUESS - MUZ).normalized(), 10.0)
B_HIT, B_N = hit[0].copy(), hit[1].copy()
if B_N.dot(MUZ - B_HIT) < 0: B_N = -B_N
BDIR = (B_HIT - MUZ).normalized()
log("muzzle", tuple(round(x, 3) for x in MUZ), "hit", tuple(round(x, 3) for x in B_HIT), "dist", round((B_HIT - MUZ).length, 3))
BL = 0.015
def qd(d): return Vector((0, 0, 1)).rotation_difference(Vector(d).normalized())
BUL.rotation_mode = 'QUATERNION'; spin = 0.0
for f in range(F_SHOT, F_HIT + 6):
    spin += math.radians(9)
    u = (f - F_SHOT) / (F_HIT - F_SHOT)
    nose = MUZ.lerp(B_HIT, u) if f <= F_HIT else B_HIT + BDIR * 0.004 * (f - F_HIT)
    BUL.location = nose - BDIR * BL; BUL.rotation_quaternion = qd(BDIR) @ Quaternion((0, 0, 1), spin)
    BUL.keyframe_insert("location", frame=f); BUL.keyframe_insert("rotation_quaternion", frame=f)
# macro: nose depth below the coat top (m) on the VO beats; monotone so it only ever slows
ZN = pchip([(SW1, -0.0060), (500, -0.0095), (615, -0.0135), (736, -0.0168), (770, -0.0182), (790, -0.0190), (800, -0.0186), (816, -0.0218), (832, -0.0400), (846, -0.0436), (860, -0.0470),
            (878, -0.0508), (905, -0.0585), (950, -0.0670), (990, -0.0703), (1010, -0.0706), (SW2, -0.0706)])
QM = Quaternion((1, 0, 0), math.pi)
for f in range(SW1, SW2 + 1):
    spin += math.radians(max(0.0, 6.0 if 736 < f < 990 else 0.4))
    zn = ZN(f); TIP.location = MX + Vector((0, 0, zn)); TIP.keyframe_insert("location", frame=f)
    BUL.location = MX + Vector((0, 0, zn + BL)); BUL.rotation_quaternion = QM @ Quaternion((0, 0, 1), spin)
    BUL.keyframe_insert("location", frame=f); BUL.keyframe_insert("rotation_quaternion", frame=f)
set_interp(BUL, 'LINEAR'); quat_continuity(BUL); set_interp(TIP, 'LINEAR')
vis(BUL, 1, False); vis(BUL, F_SHOT + 1, True); vis(BUL, F_HIT + 4, False); vis(BUL, SW1, True); vis(BUL, SW2, False)
# trail behind it in flight
TRAIL.rotation_mode = 'QUATERNION'
for f in range(F_SHOT, F_HIT + 1, 2):
    u = (f - F_SHOT) / (F_HIT - F_SHOT); nose = MUZ.lerp(B_HIT, u)
    L_ = min(0.07, (nose - MUZ).length) * (1 - smoothstep((u - 0.75) / 0.25))
    TRAIL.location = nose - BDIR * BL; TRAIL.rotation_quaternion = qd(BDIR); TRAIL.scale = (1, 1, max(0.001, L_))
    for k in ("location", "rotation_quaternion", "scale"): TRAIL.keyframe_insert(k, frame=f)
vis(TRAIL, 1, False)   # no trail: it read as a stick
# muzzle flash
FL = O["MuzzleFlash"]; FLL = O["FlashLight"]
for f, s_, e in ((1, 0.001, 0), (F_SHOT - 1, 0.001, 0), (F_SHOT, 1.0, 900), (F_SHOT + 2, 1.3, 600), (F_SHOT + 5, 0.4, 120), (F_SHOT + 8, 0.001, 0)):
    FL.scale = (s_,) * 3; FL.keyframe_insert("scale", frame=f); FLL.data.energy = e; FLL.data.keyframe_insert("energy", frame=f)
vis(FL, 1, False); vis(FL, F_SHOT, True); vis(FL, F_SHOT + 8, False)
# coat hole: on the jacket at the hit point, facing out, Child Of the chest bone (visible from the hit on, also in the hall)
fs(F_HIT); upd()
HOLE.matrix_world = Matrix.Translation(B_HIT + B_N * 0.0055) @ qd(B_N).to_matrix().to_4x4()
cbone = "spine04"
c = HOLE.constraints.new('CHILD_OF'); c.target = HERO; c.subtarget = cbone; upd()
c.inverse_matrix = (HERO.matrix_world @ HERO.pose.bones[cbone].matrix).inverted()
HOLE.matrix_basis = Matrix.Translation(B_HIT + B_N * 0.0055) @ qd(B_N).to_matrix().to_4x4()
vis(HOLE, 1, False); vis(HOLE, F_HIT + 3, True)
fs(1100); upd(); log("hole in hall", tuple(round(x, 3) for x in HOLE.matrix_world.translation))

# ================================================================== the speech IN his right hand (hall)
fs(1028); upd()
rig = HERO; Mw = rig.matrix_world
def PH(b, tail=False): return Mw @ (rig.pose.bones[b].tail if tail else rig.pose.bones[b].head)
pads = sum([PH("finger%d-2.R" % k).lerp(PH("finger%d-2.R" % k, True), 0.5) for k in (2, 3, 4)], Vector()) / 3
thumb = PH("finger1-3.R", True)
wr = PH("wrist.R"); dvec = (PH("finger3-1.R") - wr).normalized()
gap_n = (thumb - pads); gap = gap_n.length; nrm = gap_n.normalized()
mid = (thumb + pads) / 2
thick = max(0.006, min(0.012, gap - 0.008))
SPEECH.scale = (1, thick / 0.012, 1)
up = (dvec - nrm * dvec.dot(nrm)).normalized(); xx = up.cross(nrm).normalized()
# speech local: x width, y thickness (normal), z height. It must face the audience (-Y): flip so the hole face is seen
Rs = Matrix((xx, nrm, up)).transposed()
if (Rs @ Vector((0, -1, 0))).y > 0: Rs = Rs @ Matrix.Rotation(math.pi, 3, 'Z')
SPEECH.matrix_world = Matrix.Translation(mid + up * 0.05) @ Rs.to_4x4() @ Matrix.Scale(1, 4)
SPEECH.scale = (1, thick / 0.012, 1); upd()
log("speech grip gap", round(gap, 4), "thickness", round(thick, 4))
owner_switch(SPEECH, 1028, HERO, "wrist.R", log=log)
vis(SPEECH, 1, False); vis(SPEECH, SW2, True)
for ch in SPEECH.children: vis(ch, 1, False); vis(ch, SW2, True)

# he takes his hat off indoors: the fedora is hidden in the hall (switch inside the flash)

# ================================================================== clock hands spin (the 90 minutes), flags already wave
for nm, turns in (("ClockMinute", 6.0), ("ClockHour", 0.5)):
    h = O[nm]; h.rotation_mode = 'XYZ'
    for f, u in ((1, 0.0), (1139, 0.0), (1290, 1.0), (END, 1.0)):
        h.rotation_euler = (0, -turns * math.tau * u, 0); h.keyframe_insert("rotation_euler", frame=f)

# ================================================================== the ONE camera
cam = O["CAM_Film"]; cam.rotation_mode = 'XYZ'
def chest(f): fs(f); upd(); return Wh(HERO, "spine04")
def face(f): fs(f); upd(); return (Wh(HERO, "eye.L") + Wh(HERO, "eye.R")) / 2
CAMK = []
def ck(f, loc, tgt, lens): CAMK.append((f, Vector(loc), Vector(tgt), lens))
fc1 = face(1)
# STREET: over the gunman's right shoulder, Roosevelt waving 3.2 m away
ck(1, (-0.60, -4.15, 1.80), (-0.18, 0.0, 1.45), 36)
ck(F_SHOT, (-0.50, -3.95, 1.74), (-0.15, 0.0, 1.45), 38)
# chase the bullet: just behind and beside it, his face and chest ahead
for f in range(F_SHOT + 22, F_HIT + 1, 16):
    u = (f - F_SHOT) / (F_HIT - F_SHOT); nose = MUZ.lerp(B_HIT, u)
    back = 0.11 + 0.30 * u
    ck(f, nose - BDIR * back + Vector((0.07 - 0.12 * u, 0, 0.04 + 0.10 * u)), nose.lerp(Vector((B_HIT.x, B_HIT.y, fc1.z - 0.05)), 0.35 + 0.4 * u), 38)
ck(F_HIT + 20, B_HIT + Vector((-0.45, -0.95, 0.30)), Vector((0.0, 0.0, 1.45)), 32)
ck(173, (-0.70, -1.65, 1.55), (0.0, 0.0, 1.38), 30)
ck(225, (0.35, -1.75, 1.45), (0.0, 0.0, 1.40), 32)
ck(265, (0.65, -1.35, 1.50), (0.0, 0.0, 1.45), 32)
ck(320, (0.30, -1.05, 1.52), (B_HIT.x * 0.6, 0.0, (B_HIT.z + fc1.z) / 2), 32)
ck(362, B_HIT + B_N * 0.34 + Vector((0.02, 0, 0.16)), B_HIT + Vector((0, 0, 0.15)), 32)
ck(SW1 - 1, B_HIT + B_N * 0.06, B_HIT, 40)
# MACRO (from SW1): above-front of the cut, the bullet frozen on the inked top page
ck(SW1, MX + Vector((-0.030, -0.055, 0.050)), MX + Vector((0.0, 0.012, -0.006)), 40)
ck(470, MX + Vector((0.040, -0.060, 0.042)), MX + Vector((0.0, 0.014, -0.008)), 40)
ck(560, MX + Vector((0.055, -0.095, 0.012)), MX + Vector((0.0, 0.014, -0.014)), 40)
ck(640, MX + Vector((0.010, -0.120, -0.004)), MX + Vector((0.0, 0.016, -0.026)), 40)
ck(700, MX + Vector((-0.045, -0.105, -0.010)), MX + Vector((0.0, 0.016, -0.028)), 40)
for f in (737, 780, 820, 860, 900, 950, 990):
    t = MX + Vector((0, 0, ZN(f)))
    ck(f, t + Vector((-0.025 + 0.05 * (f - 737) / 253, -0.085 + 0.02 * max(0, f - 860) / 130, 0.018)), t + Vector((0, 0.015, -0.006)), 40)
ck(SW2 - 1, MX + Vector((0.03, -0.24, -0.050)), MX + Vector((0.0, 0.02, -0.075)), 40)
# HALL (from SW2): close on the holed speech in his raised hand, pull out to him, then crane up over the audience
fs(1028); upd(); sp0 = SPEECH.matrix_world.translation.copy(); fh = face(1028)
ck(SW2, sp0 + Vector((-0.10, -0.42, 0.02)), sp0, 40)
ck(1080, sp0 + Vector((-0.35, -0.95, 0.0)), sp0.lerp(fh, 0.5), 35)
ck(1139, HB1 + Vector((-0.9, -2.0, 1.55)), HB1 + Vector((0.0, 0.0, 1.55)), 32)
ck(1200, HB1 + Vector((-1.2, -3.2, 1.75)), HB1 + Vector((0.1, 0.0, 1.70)), 30)
ck(1255, HB1 + Vector((-0.8, -5.6, 2.7)), HB1 + Vector((0.0, -0.6, 1.3)), 30)
ck(END, HB1 + Vector((-0.6, -7.0, 3.1)), HB1 + Vector((0.0, -0.9, 1.0)), 30)
CAMK.sort(key=lambda k: k[0])
def seg_interp(keys, f):
    """PCHIP per component inside each set (no blending across a set switch)"""
    sets = [(1, SW1 - 1), (SW1, SW2 - 1), (SW2, END)]
    for a_, b_ in sets:
        if a_ <= f <= b_:
            kk = [k for k in keys if a_ <= k[0] <= b_]
            loc = Vector([pchip([(k[0], k[1][i]) for k in kk])(f) for i in range(3)])
            tgt = Vector([pchip([(k[0], k[2][i]) for k in kk])(f) for i in range(3)])
            lens = pchip([(k[0], k[3]) for k in kk])(f)
            return loc, tgt, lens
prev = None
for f in range(1, END + 1):
    loc, tgt, lens = seg_interp(CAMK, f)
    e = (tgt - loc).to_track_quat('-Z', 'Y').to_euler('XYZ', prev) if prev else (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
    prev = e
    cam.location = loc; cam.rotation_euler = e; cam.data.lens = lens
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f); cam.data.keyframe_insert("lens", frame=f)
set_interp(cam, 'LINEAR'); set_interp(cam.data, 'LINEAR')

# ================================================================== the set-switch flashes (warm white card in front of the lens)
bpy.ops.mesh.primitive_plane_add(size=0.2, location=(0, 0, 0))
card = bpy.context.active_object; card.name = "FlashCard"; card.parent = cam; card.location = (0, 0, -0.01)
fm = bpy.data.materials.new("M_FlashCard"); fm.use_nodes = True; nt = fm.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.92, 0.78, 1); em.inputs["Strength"].default_value = 4.0
mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], nt.nodes["Material Output"].inputs["Surface"]); card.data.materials.append(fm)
card.visible_shadow = False; card.visible_diffuse = False; card.visible_glossy = False
fac_ = mx.inputs[0]
for f, v in ((1, 0.0), (SW1 - 6, 0.0), (SW1 - 2, 1.0), (SW1 + 1, 1.0), (SW1 + 6, 0.0), (SW2 - 6, 0.0), (SW2 - 2, 1.0), (SW2 + 1, 1.0), (SW2 + 7, 0.0)):
    fac_.default_value = v; fac_.keyframe_insert("default_value", frame=f)
for o_ in list(bpy.data.collections["CHARS"].all_objects): pass
bpy.data.collections["CHARS"].objects.link(card) if card.name not in bpy.data.collections["CHARS"].objects else None
for cc in list(card.users_collection):
    if cc.name != "CHARS": cc.objects.unlink(card)

# ================================================================== VO + scene
sc = bpy.context.scene
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor; strips = se.strips if hasattr(se, "strips") else se.sequences
s_ = strips.new_sound("VO", VO, 1, 1)
sc.frame_start, sc.frame_end = 1, END
for r in [HERO, GUN] + [a.rig for a in AUD]:
    quat_continuity(r)
json.dump([{"beat": i + 1, "frame": f, "first_words": w} for i, (f, w) in enumerate(BEATS)], open(os.path.join(HERE, "..", "beats.json"), "w"), indent=1)
open(os.path.join(HERE, "..", "review", "animate_log.txt"), "w").write("\n".join(LOG))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ANIM_DONE", OUT)
