"""SpeakWithoutSight v007 stage B: seating, acting, the hand contacts, the vibration rings, the ONE camera, lights, VO.
blender -b a.blend --python 02_animate.py -- <vo.mp3> <out.blend> [test]
Built to the client's VO from the start (the v006 timing, frames 1-1645). Beats (VO):
  1 'She lost her sight and hearing'   f1      2 'trapped inside her own head' f131   3 'placed the girl's hand'  f362
  4 'began to speak'                   f507    5 'The vibrations told her'     f612   6 'how strong or soft'      f747
  7 'moved her fingers to ... lips'    f891    8 'different shapes ... word'   f1080  9 'practiced ... own face'  f1219
 10 'over and over again'              f1359  11 'until she was finally able to speak' f1497   end 1645"""
import bpy, sys, math, random, os
from mathutils import Vector, Matrix, Quaternion
PIPE = "/home/user/Muhammed/blender/pipeline"
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(PIPE + "/anim_lib.py").read())
exec(open(PIPE + "/hand_poses.py").read())
exec(open(HERE + "/lib_anim.py").read())
exec(open(HERE + "/lib_seat.py").read())
args = sys.argv[sys.argv.index("--") + 1:]
VO, OUT = args[0], args[1]
TEST = args[2] if len(args) > 2 else ""
random.seed(19)
END = 1645
B = {1: 1, 2: 131, 3: 362, 4: 507, 5: 612, 6: 747, 7: 891, 8: 1080, 9: 1219, 10: 1359, 11: 1497}
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); LOG.append(s); print("LOG", s)
O = bpy.data.objects
GR, GB, GC = O["Girl"], O["Girl.body"], O["Girl.clothes"]
TR, TB, TC = O["Teacher"], O["Teacher.body"], O["Teacher.clothes"]
SEAT_Z, SEAT_FRONT = 0.44, -0.30

# ================================================================== rigs
CTG = make_human_ctrl(GR); add_hand_limits(GR)
CTT = make_human_ctrl(TR); add_hand_limits(TR)
for r in (GR, TR):
    for pb in r.pose.bones: pb.rotation_mode = 'QUATERNION'
SG = joint_limits(GR, CTG); ST = joint_limits(TR, CTT)
log("joint signs girl", SG, "teacher", ST)
HG, HT = Human(CTG), Human(CTT)
CH = {"G": (GR, GB, GC, CTG, HG), "T": (TR, TB, TC, CTT, HT)}

def key_pole(CT, s, f, target, kind="elbow"):
    n = ("Pole_elbow." if kind == "elbow" else "Pole_knee.") + s; pb = CT.PB[n]
    pb.location = CT.rest(n).to_3x3().inverted() @ (Vector(target) - CT.BN[n].head_local)
    pb.keyframe_insert("location", frame=f, group=n)

_HS = {}
def head_signs(rig, CT):
    if rig.name in _HS: return _HS[rig.name]
    pb = rig.pose.bones["head"]; q0 = pb.rotation_quaternion.copy(); upd()
    e0 = Wh(rig, "eye.L"); out = {}
    for ax, i in (("X", 0), ("Z", 2)):
        pb.rotation_quaternion = Quaternion(Vector([1 if k == i else 0 for k in range(3)]), math.radians(10)); upd()
        out[ax] = Wh(rig, "eye.L") - e0; pb.rotation_quaternion = q0; upd()
    _HS[rig.name] = (1 if out["X"].z < 0 else -1, 1 if out["Z"].x > 0 else -1); return _HS[rig.name]

def key_head(c, f, yaw, pitch, roll=0.0):
    """yaw +: toward the character's own left (+X at rest); pitch +: look down"""
    rig, CT = CH[c][0], CH[c][3]; sx, sz = head_signs(rig, CT)
    for n, w in (("neck01", 0.25), ("neck02", 0.25), ("neck03", 0.2), ("head", 0.3)):
        CT.key_rot(n, f, [("X", sx * pitch * w), ("Y", roll * w), ("Z", sz * yaw * w)])

def key_spine(c, f, flex=0.0, twist=0.0, side=0.0):
    CT = CH[c][3]
    for n, w in Human.SPINE_W.items():
        CT.key_rot(n, f, [("X", flex * w), ("Y", side * w), ("Z", twist * w)])

# ================================================================== seating (pelvis ON the seat, thighs ON the cushion, feet ON the floor / footstool)
PELVIS = {"G": (0.27, None), "T": (-0.28, None)}
YAW = {"G": -12.0, "T": 14.0}           # each turned a little toward the other
FOOT_Z = {"G": 0.12, "T": 0.0}           # teacher: feet on the floor; girl: feet ON the footstool (built to her soles)
CAL = {}
def thigh_len(c):
    BN = CH[c][3].BN; return (BN["lowerleg01.L"].head_local - BN["upperleg01.L"].head_local).length
def shin_len(c):
    BN = CH[c][3].BN; return (BN["foot.L"].head_local - BN["lowerleg01.L"].head_local).length

def seat_pose(c, f, root_dz=0.0, flex=0.0, foot_fwd=0.0, knee_out=0.0):
    rig, body, cl, CT, H = CH[c]
    x = PELVIS[c][0]; yaw = YAW[c]
    rh = H.root_head; hip = CT.BN["upperleg01.L"].head_local
    tl = thigh_len(c)
    # hip joints so that the knee joint sits 9 cm past the seat front (calves clear the cushion and rail)
    Ryaw = Matrix.Rotation(math.radians(yaw), 3, 'Z')
    fwd = Ryaw @ Vector((0, -1, 0))
    hip_y = SEAT_FRONT - 0.12 + tl * 0.97
    z0 = CAL.get(c, SEAT_Z + (rh.z - hip.z) + 0.10)
    pos = Vector((x, hip_y, z0 + root_dz)) + Vector((0, (rh.y - hip.y), 0))
    H.key_root(f, pos, yaw=yaw, flex=flex)
    sl = shin_len(c)
    for s, sg in (("L", 1), ("R", -1)):
        hx = CT.BN["upperleg01." + s].head_local.x
        side = Ryaw @ Vector((hx * 1.05 + sg * knee_out, 0, 0))
        knee = Vector((x, hip_y, 0)) + side + fwd * tl * 0.97
        fz = FOOT_Z[c]
        a = CT.BN["foot." + s].head_local
        ank = knee + fwd * (0.06 + foot_fwd)
        ank.z = fz + a.z
        M = Matrix.Translation(ank) @ Ryaw.to_4x4() @ Matrix.Translation(-a) @ CT.rest("IK_foot." + s)
        CT.key_world("IK_foot." + s, f, M)
        key_pole(CT, s, f, knee + fwd * 0.6 + Vector((0, 0, 0.1)), kind="knee")

def calibrate(c):
    """move the pelvis so the lowest buttock / thigh-underside skin rests 6 mm INTO the velvet (it reads as sitting ON it):
    rays cast UP from the floor under each hip joint and mid-thigh hit the underside of the posed body."""
    rig, body, cl, CT, H = CH[c]
    for it in range(4):
        seat_pose(c, 1); fs(1)
        mks = [m for m in body.modifiers if m.type == 'MASK' and m.show_viewport]
        for m in mks: m.show_viewport = False      # measure the real skin (clothes masks hide it)
        bvs = [bvh_eval(body)]; mz = 9.0
        for m in mks: m.show_viewport = True
        for s in "LR":
            hp = Wh(rig, "upperleg01." + s); kn = Wh(rig, "lowerleg01." + s)
            for u in (0.0, 0.25, 0.5, 0.75):
                q = hp.lerp(kn, u)
                for dy in (0.0, 0.04):
                    for bv in bvs:
                        h = bv.ray_cast(Vector((q.x, q.y + dy, 0.02)), Vector((0, 0, 1)), 3.0)
                        if h[0] is not None and h[0].y > SEAT_FRONT + 0.02: mz = min(mz, h[0].z)
        cur = CAL.get(c, SEAT_Z + (H.root_head.z - CT.BN["upperleg01.L"].head_local.z) + 0.10)
        CAL[c] = cur + (SEAT_Z + 0.002 - mz)
        log("calibrate", c, it, "min skin z", round(mz, 4), "->", round(CAL[c], 4), "foot err", round((Wh(rig, "foot.L") - Wh(rig, "IK_foot.L")).length, 3))
        if abs(SEAT_Z + 0.002 - mz) < 0.002: break

def setup_seating():
    FOOT_Z["T"] = 0.0; calibrate("T")
    # the girl's soles: knee 90 deg, shin hanging -> sole height; she rests her feet ON a footstool built to that height
    FOOT_Z["G"] = 0.12; calibrate("G")
    fs(1); kz = Wh(GR, "lowerleg01.L").z; a = CTG.BN["foot.L"].head_local
    FOOT_Z["G"] = max(0.06, round(kz - shin_len("G") - a.z - 0.004, 3)); calibrate("G")
    for c in "GT":
        fs(1); r = CH[c][0]
        log("seated", c, "knee z", round(Wh(r, "lowerleg01.L").z, 3), "hip z", round(Wh(r, "upperleg01.L").z, 3),
            "foot reach err mm", round((Wh(r, "foot.L") - Wh(r, "IK_foot.L")).length * 1000, 1))
setup_seating()

# the footstool: its top meets the real bottom of her shoes, its footprint is just under the shoes (shins clear above it)
fs(1); shoes = [ch for ch in GR.children if "shoes" in ch.name][0]
upd(); dg = bpy.context.evaluated_depsgraph_get(); e = shoes.evaluated_get(dg); me = e.to_mesh()
SP = [shoes.matrix_world @ v.co for v in me.vertices]; e.to_mesh_clear()
TOP = min(p_.z for p_ in SP) - 0.002
x0, x1 = min(p_.x for p_ in SP) - 0.04, max(p_.x for p_ in SP) + 0.04
y0, y1 = min(p_.y for p_ in SP) - 0.04, max(p_.y for p_ in SP) + 0.02
bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, 0.05 + (TOP - 0.05) / 2))
FS = bpy.context.active_object; FS.name = "PL_Footstool"; FS.scale = (x1 - x0, y1 - y0, TOP - 0.05); bpy.ops.object.transform_apply(scale=True)
bv = FS.modifiers.new("bev", 'BEVEL'); bv.width = 0.02; bv.segments = 4; FS.data.materials.append(bpy.data.materials["M_Velvet"])
for p_ in FS.data.polygons: p_.use_smooth = True
for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.013, depth=0.05, location=((x0 + x1) / 2 + sx * ((x1 - x0) / 2 - 0.03), (y0 + y1) / 2 + sy * ((y1 - y0) / 2 - 0.03), 0.025))
    o = bpy.context.active_object; o.name = "PL_FootstoolLeg%d" % i; o.data.materials.append(bpy.data.materials["M_Mahogany"])
log("footstool top", round(TOP, 3), "x", round(x0, 2), round(x1, 2), "y", round(y0, 2), round(y1, 2))

if TEST == "seat":
    for c in "GT":
        for f in (1, 400): seat_pose(c, f)
    cam = bpy.data.objects.new("TC", bpy.data.cameras.new("TC")); bpy.context.scene.collection.objects.link(cam); bpy.context.scene.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = 540, 960; sc.cycles.samples = 16
    for nm, loc, rot, lens in (("front", (0.0, -2.6, 0.95), (88, 0, 0), 30), ("side", (2.2, -0.6, 0.7), (85, 0, 75), 32),
                               ("low", (-0.9, -1.2, 0.35), (80, 0, -40), 24)):
        cam.location = loc; cam.rotation_euler = [math.radians(v) for v in rot]; cam.data.lens = lens
        fs(1); sc.render.filepath = os.path.join(os.path.dirname(OUT), "seat_%s.png" % nm); bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT); sys.exit(0)

# ================================================================== BODY ACTING (seated, both all film)
POSES["two_point"] = dict(curl={2: (6, 8, 5), 3: (10, 12, 6), 4: (62, 80, 50), 5: (68, 85, 55)}, spread=3.0, thumb=("over_middle2", 0.014))
POSES["soft_cup"] = dict(curl={2: (12, 14, 8), 3: (13, 15, 8), 4: (14, 16, 9), 5: (16, 18, 10)}, spread=1.5, thumb=("beside_index", 0.014))
KF = list(range(1, END + 1, 10)) + [END]

def breath(f, per, amp, ph=0.0): return amp * math.sin(2 * math.pi * (f + ph) / per)
# teacher: leans toward the girl when she works with her hand, upright with joy at the end
T_FLEX = pchip([(1, 4), (131, 6), (362, 8), (455, 10), (900, 9), (1219, 8), (1497, 7), (1530, 2), (END, 4)])
T_SIDE = pchip([(1, 3), (362, 4), (440, 9), (900, 9), (1440, 8), (1497, 3), (END, 4)])       # + toward her left = the girl
T_TWIST = pchip([(1, 6), (362, 8), (455, 12), (1440, 10), (1497, 8), (END, 9)])
for f in KF:
    seat_pose("T", f, root_dz=0.0)
    key_spine("T", f, flex=T_FLEX(f) + breath(f, 230, 0.8), twist=T_TWIST(f), side=T_SIDE(f))
# girl: still and closed-in at the start, then attentive (leans in), finally upright and confident
G_FLEX = pchip([(1, 9), (131, 11), (362, 9), (455, 7), (891, 6), (1219, 7), (1359, 5), (1497, 1), (1560, -2), (END, -1)])
G_TWIST = pchip([(1, 0), (362, -4), (455, -10), (891, -12), (1219, -8), (1497, -4), (END, -4)])  # - toward her right = the teacher
G_SIDE = pchip([(1, 0), (362, -2), (440, -8), (891, -9), (1219, -7), (1440, -6), (1497, -1), (END, -1)])
for f in KF:
    seat_pose("G", f, root_dz=0.0)
    key_spine("G", f, flex=G_FLEX(f) + breath(f, 190, 1.0, 40), twist=G_TWIST(f), side=G_SIDE(f))
# heads (yaw + toward own left, pitch + down)
T_HEAD = [(1, 18, 6), (60, 24, 4), (131, 20, 6), (300, 22, 4), (362, 24, 8), (420, 22, 3), (455, 18, -6), (507, 16, -8),
          (612, 14, -7), (747, 12, -9), (891, 10, -4), (1080, 8, -3), (1219, 10, -3), (1359, 14, 2), (1440, 16, 4),
          (1497, 20, 2), (1530, 24, -4), (1580, 22, 0), (END, 20, 2)]
G_HEAD = [(1, -4, 10), (70, -2, 12), (131, -3, 12), (220, -5, 13), (362, -8, 10), (455, -14, 2), (507, -16, 0),
          (612, -18, -2), (747, -18, -4), (820, -17, -2), (891, -18, -3), (1080, -17, -4), (1219, -14, -2), (1359, -10, 0),
          (1497, -6, -2), (1530, -4, -6), (1580, -8, -3), (END, -10, -2)]
for c, HK in (("T", T_HEAD), ("G", G_HEAD)):
    hy = pchip([(f, y) for f, y, p in HK]); hp = pchip([(f, p) for f, y, p in HK])
    for f in list(range(1, END + 1, 6)) + [END]:
        key_head(c, f, hy(f) + breath(f, 300, 1.2), hp(f) + breath(f, 260, 0.8, 70))

# ---- faces. Teacher talks (syllables) from 507; her joy at the end. The girl: blank, then attentive, mimicking, speaking.
def speech(rig, f0, f1, seed, amp=(0.15, 0.5), gap=0.18, every=9, smile=0.2, brow=0.1):
    rnd = random.Random(seed); f = f0
    while f < f1:
        j = 0.0 if rnd.random() < gap else rnd.uniform(*amp)
        key_face(rig, f, smile=smile, jaw=j, brow=brow)
        f += every + rnd.randint(-2, 3)
    key_face(rig, f1, smile=smile, jaw=0.0, brow=brow)
key_face(TR, 1, smile=0.35, brow=0.2); key_face(TR, 131, smile=0.25, brow=0.3); key_face(TR, 362, smile=0.4, brow=0.3)
key_face(TR, 500, smile=0.3, brow=0.3)
speech(TR, 507, 612, 1, amp=(0.15, 0.45), smile=0.25, brow=0.3)
speech(TR, 612, 747, 2, amp=(0.15, 0.40), smile=0.2, brow=0.3)
speech(TR, 747, 820, 3, amp=(0.45, 0.75), gap=0.05, every=8, smile=0.1, brow=0.6)      # strong
speech(TR, 820, 891, 4, amp=(0.06, 0.16), gap=0.25, every=11, smile=0.35, brow=0.1)     # soft
speech(TR, 891, 1080, 5, amp=(0.12, 0.35), smile=0.25, brow=0.3)
# O / E / M shapes on the beat 8 words
for f, sm, jw in ((1080, 0.2, 0.0), (1092, -0.7, 0.42), (1120, -0.7, 0.42), (1132, 0.85, 0.16), (1160, 0.85, 0.16),
                  (1172, 0.1, 0.0), (1200, 0.1, 0.0), (1219, 0.25, 0.1)):
    key_face(TR, f, smile=sm, jaw=jw, brow=0.35)
speech(TR, 1225, 1440, 6, amp=(0.12, 0.35), smile=0.3, brow=0.3)
for f, sm, br, jw in ((1440, 0.4, 0.3, 0.0), (1497, 0.35, 0.3, 0.0), (1512, 0.5, 0.9, 0.38), (1535, 0.9, 0.8, 0.30),
                      (1570, 1.0, 0.7, 0.12), (END, 1.0, 0.6, 0.10)):
    key_face(TR, f, smile=sm, brow=br, jaw=jw)
# girl
for f, sm, br, jw in ((1, -0.05, -0.2, 0.0), (131, -0.15, -0.3, 0.0), (300, -0.15, -0.25, 0.0), (362, -0.05, 0.0, 0.0),
                      (420, 0.0, 0.3, 0.05), (507, 0.0, 0.4, 0.08), (612, 0.05, 0.5, 0.10), (747, 0.0, 0.9, 0.25),
                      (800, 0.1, 0.8, 0.18), (840, 0.3, 0.3, 0.05), (891, 0.2, 0.4, 0.05), (1080, 0.15, 0.5, 0.08), (1219, 0.1, 0.4, 0.0)):
    key_face(GR, f, smile=sm, brow=br, jaw=jw)
speech(GR, 1240, 1480, 7, amp=(0.10, 0.35), gap=0.25, every=12, smile=0.1, brow=0.5)
for f, sm, br, jw in ((1497, 0.1, 0.5, 0.0), (1512, 0.2, 0.6, 0.45), (1530, 0.5, 0.7, 0.35), (1550, 0.8, 0.7, 0.15),
                      (1575, 1.0, 0.6, 0.10), (END, 1.0, 0.5, 0.08)):
    key_face(GR, f, smile=sm, brow=br, jaw=jw)
blinks(TR, [40, 205, 330, 470, 690, 860, 1010, 1250, 1390, 1500, 1600])
blinks(GR, [95, 260, 400, 560, 780, 960, 1150, 1330, 1460, 1590])
saccades(CTT, 1, END, every=45, amp=(1.2, 2.0), seed=11)
# the girl's eyes: soft and unfocused (gaze a little low and slightly apart, slow drift, never locked on anything)
for f in list(range(1, END + 1, 60)) + [END]:
    d = 2.0 * math.sin(f / 97.0)
    for s_, sg in (("L", 1), ("R", -1)):
        CTG.key_rot("eye." + s_, f, [("X", -7.0 + d * 0.5), ("Z", sg * 2.5 + d)])

# ================================================================== HANDS
def pose_hand(rig, s, f, pose, spread=None): apply_pose(rig, s, pose, f, spread=spread)
def tip(rig, s, k=2): fs_ = None; return Wt(rig, "finger%d-3.%s" % (k, s))
def palm_frame(rig, s):
    """world palm centre, finger dir d, palm normal n (palm side) of the evaluated hand"""
    wr = Wh(rig, "wrist." + s); m3 = Wh(rig, "finger3-1." + s); i2 = Wh(rig, "finger2-1." + s); p5 = Wh(rig, "finger5-1." + s)
    d = (m3 - wr).normalized(); a = (i2 - p5).normalized()
    n = d.cross(a) if s == "L" else a.cross(d); n = (n - d * n.dot(d)).normalized()
    t0 = Wt(rig, "finger3-3." + s)
    if (t0 - wr.lerp(m3, 0.6)).dot(n) < 0: n = -n            # fingers curl toward the palm side
    return wr.lerp(m3, 0.6), d, n

def ik_shift(rig, s, f, delta):
    pb = rig.pose.bones["IK_hand." + s]
    R = rig.data.bones["IK_hand." + s].matrix_local.to_3x3().inverted()
    pb.location = pb.location + R @ delta; pb.keyframe_insert("location", frame=f, group=pb.name)

WORSTB = [None]
def surf_clear(rig, s, bvhs):
    """min signed distance (m) of the finger/metacarpal bone axes (3 samples each) to the given surfaces"""
    worst = 9.0
    for n in [pb.name for pb in rig.pose.bones if pb.name.endswith("." + s) and (pb.name.startswith("finger") or pb.name.startswith("metacarpal"))]:
        for t in (0.0, 0.5, 1.0):
            p = rig.matrix_world @ rig.pose.bones[n].head.lerp(rig.pose.bones[n].tail, t)
            for b in bvhs:
                loc, nrm, idx, dist = b.find_nearest(p)
                if loc is None: continue
                dd = (p - loc).dot(nrm) if (p - loc).length < 0.05 else 9.0
                if dd < worst: worst = dd; WORSTB[0] = n
    return worst

def skirt_bvh(cl):
    upd(); dg = bpy.context.evaluated_depsgraph_get(); e = cl.evaluated_get(dg); me = e.to_mesh(); Mw = cl.matrix_world
    polys = [p.vertices[:] for p in me.polygons if p.material_index == 1]
    b = BVHTree.FromPolygons([Mw @ v.co for v in me.vertices], polys); e.to_mesh_clear(); return b

def rest_on_thigh(c, s, f, fwd=0.0, side=0.0, lift=0.0):
    """hand resting palm-down on its own thigh (skirt surface found by a ray from above)"""
    rig, body, cl, CT, H = CH[c]
    fs(f); hp = Wh(rig, "upperleg01." + s); kn = Wh(rig, "lowerleg01." + s)
    q = hp.lerp(kn, 0.62 + fwd); sx = 1 if s == "L" else -1
    q = q + (Matrix.Rotation(math.radians(YAW[c]), 3, 'Z') @ Vector((sx * (0.01 + side), 0, 0)))
    h = skirt_bvh(cl).ray_cast(Vector((q.x, q.y, q.z + 0.25)), Vector((0, 0, -1)), 0.5)   # the trousers only (never an arm)
    P = h[0] if h[0] is not None else q + Vector((0, 0, 0.07))
    fd = (kn - hp).normalized(); fd = Vector((fd.x, fd.y, -0.25)).normalized()
    fd = (Matrix.Rotation(math.radians(-sx * 12), 3, 'Z') @ fd)
    place_hand(rig, s, f, P + Vector((0, 0, lift)), Vector((0, 0, -1)), fd, skin=0.016)
    sh = Wh(rig, "upperarm01." + s)
    key_pole(CT, s, f, sh + Matrix.Rotation(math.radians(YAW[c]), 3, 'Z') @ Vector((sx * 0.30, 0.35, -0.30)))
    pose_hand(rig, s, f, "relaxed")

def settle(c, s, f, bvhs_fn, min_gap=0.006, axis=Vector((0, 0, 1)), tries=5):
    """push the IK hand out along `axis` until every finger bone clears the surfaces by min_gap"""
    rig = CH[c][0]
    for it in range(tries):
        fs(f); g = surf_clear(rig, s, bvhs_fn())
        if g >= min_gap: SETTLE.append((c, s, f, round(g * 1000, 1))); return g
        ik_shift(rig, s, f, axis * (min_gap - g + 0.002))
    fs(f); g = surf_clear(rig, s, bvhs_fn()); SETTLE.append((c, s, f, round(g * 1000, 1))); return g
SETTLE = []

# ---- resting hands (keys spaced; idle motion is tiny finger/position drift)
ARMB = ("upperarm", "lowerarm", "wrist", "finger", "metacarpal")
def body_noarms(rig, body):
    """the character's own body WITHOUT its arms and hands (a hand is never 'inside' itself)"""
    db = DOMB.get(body.name)
    if db is None: db = dom_bones(body, rig); DOMB[body.name] = db
    saved = []
    for m in body.modifiers:
        if m.type in ('MASK', 'SUBSURF'): saved.append((m, m.show_viewport)); m.show_viewport = False
    upd(); dg = bpy.context.evaluated_depsgraph_get(); e = body.evaluated_get(dg); me = e.to_mesh(); Mw = body.matrix_world
    polys = [p.vertices[:] for p in me.polygons if not any((db.get(v) or "").startswith(ARMB) for v in p.vertices)]
    b = BVHTree.FromPolygons([Mw @ v.co for v in me.vertices], polys); e.to_mesh_clear()
    for m, sv in saved: m.show_viewport = sv
    upd(); return b
def girl_bvh(): return [skirt_bvh(GC), body_noarms(GR, GB)]
def teach_bvh(): return [skirt_bvh(TC), body_noarms(TR, TB)]
REST_T_R = list(range(1, END + 1, 60)) + [END]
for i, f in enumerate(REST_T_R):
    rest_on_thigh("T", "R", f, fwd=0.02 * math.sin(i), lift=0.0)
for f in REST_T_R:
    settle("T", "R", f, teach_bvh)
GL_REST = [f for f in range(1, 1220, 60)] + [1219]
for i, f in enumerate(GL_REST):
    rest_on_thigh("G", "L", f, fwd=0.015 * math.sin(i * 1.3))
for f in GL_REST:
    settle("G", "L", f, girl_bvh)

# ---- girl's right hand: on her thigh until the teacher takes it
GR_REST = list(range(1, 395, 50)) + [395]
for i, f in enumerate(GR_REST):
    rest_on_thigh("G", "R", f, fwd=0.01 * math.sin(i))
for f in GR_REST:
    settle("G", "R", f, girl_bvh)

# ---- the contact points (stored in the teacher's own bone space so they follow her head and neck)
def bone_local(rig, bone, P, N=None):
    M = (rig.matrix_world @ rig.pose.bones[bone].matrix).inverted()
    return (M @ P, (M.to_3x3() @ N).normalized() if N is not None else None)
def bone_world(rig, bone, Pl, Nl=None):
    M = rig.matrix_world @ rig.pose.bones[bone].matrix
    return (M @ Pl, (M.to_3x3() @ Nl).normalized() if Nl is not None else None)

F_THROAT = 470
fs(F_THROAT)
nk = (Wh(TR, "neck02") + Wh(TR, "neck03")) / 2
nk.z = (Wh(TR, "eye.L").z + Wh(TR, "eye.R").z) / 2 - 0.126      # the larynx: below the jaw, above the collar          # the larynx: 12 cm below the eyes (not under the jaw)
fdir = Matrix.Rotation(math.radians(YAW["T"] + 40), 3, 'Z') @ Vector((0, -1, 0))   # front-left of her neck (toward the girl and the camera)
h = ray_surface([TB], nk + fdir * 0.25, -fdir)
TH_P, TH_N = h[0].copy(), h[1].copy()
TH_L = bone_local(TR, "neck02", TH_P, TH_N)
log("throat point", tuple(round(v, 3) for v in TH_P), "normal", tuple(round(v, 2) for v in TH_N))
F_LIPS = 980
fs(F_LIPS)
ey = (Wh(TR, "eye.L") + Wh(TR, "eye.R")) / 2
hdir = Matrix.Rotation(math.radians(YAW["T"] + 20), 3, 'Z') @ Vector((0, -1, 0))
best = None
for dz in (-0.060, -0.064, -0.068):
    h = ray_surface([TB], ey + Vector((0, 0, dz)) + hdir * 0.25 + Vector((0.012, 0, 0)), -hdir)
    if h and (best is None or h[0].y < best[0].y): best = h
LIP_P, LIP_N = best[0].copy(), best[1].copy()
LIP_L = bone_local(TR, "head", LIP_P, LIP_N)
log("upper lip point", tuple(round(v, 3) for v in LIP_P), "eye mid", tuple(round(v, 3) for v in ey))

def throat_hand(f, lift=0.0):
    fs(f); P, N = bone_world(TR, "neck02", *TH_L); N = Vector((N.x, N.y, 0)).normalized()
    t = Vector((0, 0, 1)).cross(N).normalized()
    if t.x > 0: t = -t                     # fingers across the front of her throat (away from the girl's wrist)
    fd = Vector((t.x, t.y, 0.0)).normalized()          # fingers level across the throat
    place_hand(GR, "R", f, P + N * lift, -N, fd, skin=0.015)
    sh = Wh(GR, "upperarm01.R"); key_pole(CTG, "R", f, sh + Vector((0.10, 0.30, -0.40)))
    pose_hand(GR, "R", f, "soft_cup")
    return P, N

def tip_on(rig, s, f, want, fd, pn, back=0.075, pose="two_point"):
    place_hand(rig, s, f, want - fd * back, pn, fd, skin=0.0)
    pose_hand(rig, s, f, pose, spread=3)
    for it in range(4):
        fs(f); e = want - Wt(rig, "finger2-3." + s)
        if e.length < 0.0015: break
        ik_shift(rig, s, f, e)
    fs(f); return (Wt(rig, "finger2-3." + s) - want).length

def tip_natural(rig, s, f, want, flex=12.0, pose="two_point", iters=7, side_dev=0.0):
    """the wrist stays in line with the forearm (no forced twist past the joint limits): only the IK position is solved
    so the index fingertip lands on `want`"""
    pose_hand(rig, s, f, pose, spread=3)
    BN = rig.data.bones; pb = rig.pose.bones["IK_hand." + s]
    rel = BN["lowerarm02." + s].matrix_local.inverted() @ BN["wrist." + s].matrix_local
    for it in range(iters):
        fs(f)
        Mf = rig.pose.bones["lowerarm02." + s].matrix
        Mw = Mf @ rel @ Matrix.Rotation(math.radians(flex), 4, 'X') @ Matrix.Rotation(math.radians(side_dev), 4, 'Z')
        q = (BN["IK_hand." + s].matrix_local.to_3x3().inverted() @ Mw.to_3x3()).to_quaternion()
        if pb.rotation_quaternion.dot(q) < 0: q = -q
        pb.rotation_quaternion = q; pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
        fs(f); e = want - Wt(rig, "finger2-3." + s)
        if e.length < 0.0015 and it > 1: break
        ik_shift(rig, s, f, e)
    fs(f); return (Wt(rig, "finger2-3." + s) - want).length

def lips_hand(f):
    """the girl's index fingertip rests on the teacher's upper lip, fingers rising from below her chin (palm toward her face)"""
    fs(f); P, N = bone_world(TR, "head", *LIP_L)
    up = Vector((0, 0, 1)); side = up.cross(N).normalized()
    if side.x < 0: side = -side            # toward the girl
    fd = (up * 0.70 - side * 0.40 - N * 0.30).normalized()
    pn = (-N).normalized()
    sh = Wh(GR, "upperarm01.R"); key_pole(CTG, "R", f, sh + Vector((0.0, -0.30, -0.50)))
    tip_on(GR, "R", f, P + N * 0.010, fd, pn)
    return tip_natural(GR, "R", f, P + N * 0.010, flex=15.0)

# ---- the teacher's hand covers the girl's hand and guides it (362-470), then lets go (470-505)
def cover_hand(f, lift=0.0):
    fs(f); pc, d, n = palm_frame(GR, "R")
    dors = pc - n * 0.012                   # the back of the girl's hand
    h = ray_surface([GB], pc - n * 0.08, n, 0.1)
    if h: dors = h[0]
    place_hand(TR, "L", f, dors - n * lift, n, d, skin=0.013)
    sh = Wh(TR, "upperarm01.L"); key_pole(CTT, "L", f, sh + Vector((0.30, 0.25, -0.35)))
    pose_hand(TR, "L", f, "soft_cup")

def ik_get(rig, s, f):
    fs(f); pb = rig.pose.bones["IK_hand." + s]; return pb.location.copy(), pb.rotation_quaternion.copy()
def ik_set(rig, s, f, loc, q):
    pb = rig.pose.bones["IK_hand." + s]; pb.location = loc
    if pb.rotation_quaternion.dot(q) < 0: q = -q
    pb.rotation_quaternion = q
    pb.keyframe_insert("location", frame=f, group=pb.name); pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
def arc_key(rig, s, fa, fb, fm, lift_arm=Vector((0, 0, 0.05)), u=0.5):
    """one in-between key at fm on a raised arc between the keys at fa and fb (rotation slerped)"""
    la, qa = ik_get(rig, s, fa); lb, qb = ik_get(rig, s, fb)
    R = rig.data.bones["IK_hand." + s].matrix_local.to_3x3().inverted()
    ik_set(rig, s, fm, la.lerp(lb, u) + R @ lift_arm, qa.slerp(qb, u))

# ---- girl's right hand: thigh (to 395) -> carried up (395-456) -> on the teacher's throat (456-905)
F_ON = F_THROAT - 14
for f in list(range(F_ON, 905, 6)) + [905]:
    throat_hand(f)
arc_key(GR, "R", 395, F_ON, 418, lift_arm=Vector((-0.02, -0.12, 0.06)), u=0.35)
arc_key(GR, "R", 395, F_ON, 440, lift_arm=Vector((-0.02, -0.08, 0.03)), u=0.75)
pose_hand(GR, "R", 418, "soft_cup", spread=1)
TH_GAP = {}
for f in (F_ON, 520, 612, 700, 800, 905):
    g = settle("G", "R", f, lambda: [bvh_eval(TC), body_noarms(TR, TB)], min_gap=0.004, axis=bone_world(TR, "neck02", *TH_L)[1])
    fs(f); TH_GAP[f] = (round(g * 1000, 1), WORSTB[0], round((Wh(GR, "wrist.R") - Wh(GR, "IK_hand.R")).length * 1000, 1))
log("girl fingers on throat: min clearance mm", TH_GAP)

# ---- teacher's left hand: rests; waves slowly in front of the girl's eyes in beat 1 (no reaction); covers and guides
for f in (1, 362):
    rest_on_thigh("T", "L", f)
settle("T", "L", 1, teach_bvh); settle("T", "L", 362, teach_bvh)
def wave_hand(f, dx):
    fs(f); ge = (Wh(GR, "eye.L") + Wh(GR, "eye.R")) / 2
    fwdg = Matrix.Rotation(math.radians(YAW["G"]), 3, 'Z') @ Vector((0, -1, 0))
    P = ge + fwdg * 0.22 + Vector((dx - 0.11, 0, -0.05))
    place_hand(TR, "L", f, P, (ge - P).normalized(), Vector((0.25, 0.0, 1.0)).normalized(), skin=0.0)
    fs(f); WAVE[f] = round((Wh(TR, "wrist.L") - Wh(TR, "IK_hand.L")).length * 1000, 1)
    sh = Wh(TR, "upperarm01.L"); key_pole(CTT, "L", f, sh + Vector((0.15, 0.30, -0.40)))
    pose_hand(TR, "L", f, "open_alarm", spread=4)
WAVE = {}
for f, dx in ():
    wave_hand(f, dx)
log("teacher wave: wrist reach err mm", WAVE)
rest_on_thigh("T", "L", 128); settle("T", "L", 128, teach_bvh)
rest_on_thigh("T", "L", 362); settle("T", "L", 362, teach_bvh)
F_REL = 410
for f in list(range(386, F_REL + 1, 4)):
    cover_hand(f)
arc_key(TR, "L", 362, 386, 374, lift_arm=Vector((0, 0, 0.05)))
pose_hand(TR, "L", 374, "relaxed")
COV = {}
for f in (386, 398, F_REL):
    fs(f); pc, d, n = palm_frame(GR, "R")
    g = settle("T", "L", f, lambda: [bvh_eval(GB)], axis=-n)
    COV[f] = round(g * 1000, 1)
log("teacher palm over the girl's hand: min clearance mm", COV)
rest_on_thigh("T", "L", 505); settle("T", "L", 505, teach_bvh)
rest_on_thigh("T", "L", 446); settle("T", "L", 446, teach_bvh)
arc_key(TR, "L", F_REL, 446, 426, lift_arm=Vector((0.0, -0.04, -0.03)))
for f in range(565, END + 1, 70):
    rest_on_thigh("T", "L", f, fwd=0.015 * math.sin(f)); settle("T", "L", f, teach_bvh)
rest_on_thigh("T", "L", END); settle("T", "L", END, teach_bvh)

# ---- girl's right hand: throat -> lips (905-950), on the lips (950-1440), back to her lap (1440-1490)
LIP_ERR = {}
for f in list(range(950, 1441, 6)) + [1440]:
    LIP_ERR[f] = lips_hand(f)
log("girl index tip on the teacher's lip: max reach err mm", round(max(LIP_ERR.values()) * 1000, 1))
log("lip err per frame", {f: round(v * 1000) for f, v in LIP_ERR.items() if v > 0.004})
arc_key(GR, "R", 905, 950, 928, lift_arm=Vector((0.03, -0.04, 0.03)))
pose_hand(GR, "R", 928, "soft_cup")
LIPS_GAP = {}
for f in (950, 1080, 1120, 1160, 1219, 1359, 1440):
    fs(f); g = surf_clear(GR, "R", [bvh_eval(TB)]); LIPS_GAP[f] = (round(g * 1000, 1), WORSTB[0])
log("girl fingers vs the teacher's face: min clearance mm (tip is 3 mm off by design)", LIPS_GAP)
for f in (1490, 1560, END):
    rest_on_thigh("G", "R", f); settle("G", "R", f, girl_bvh)
arc_key(GR, "R", 1440, 1490, 1465, lift_arm=Vector((0.02, -0.06, 0.02)))
pose_hand(GR, "R", 1465, "relaxed")

# ---- girl's left hand: her own lips (1262-1497), then her own throat (1530-end) as she speaks
fs(1262)
gey = (Wh(GR, "eye.L") + Wh(GR, "eye.R")) / 2
gdir = Matrix.Rotation(math.radians(YAW["G"] + 10), 3, 'Z') @ Vector((0, -1, 0))
best = None
for dz in (-0.050, -0.054, -0.058):
    h = ray_surface([GB], gey + Vector((0, 0, dz)) + gdir * 0.25 + Vector((0.006, 0, 0)), -gdir)
    if h and (best is None or h[0].y < best[0].y): best = h
GLIP_L = bone_local(GR, "head", best[0], best[1])
def own_lips(f):
    fs(f); P, N = bone_world(GR, "head", *GLIP_L)
    up = Vector((0, 0, 1)); side = up.cross(N).normalized()
    if side.x < 0: side = -side            # toward her left (+X side), where her left hand comes from
    fd = (up * 0.70 - side * 0.40 - N * 0.30).normalized()
    sh = Wh(GR, "upperarm01.L"); key_pole(CTG, "L", f, sh + Vector((0.25, 0.20, -0.40)))
    return tip_on(GR, "L", f, P + N * 0.012, fd, -N)
OWN = {}
for f in list(range(1262, 1498, 6)) + [1497]:
    OWN[f] = own_lips(f)
for f in (1530, 1590, END):
    rest_on_thigh("G", "L", f, fwd=0.01 * math.sin(f)); settle("G", "L", f, girl_bvh)
arc_key(GR, "L", 1497, 1530, 1513, lift_arm=Vector((0.03, -0.06, 0.0)))
pose_hand(GR, "L", 1513, "relaxed")
log("girl own-lip tip err mm", round(max(OWN.values()) * 1000, 1))
arc_key(GR, "L", 1219, 1262, 1240, lift_arm=Vector((0.03, -0.06, 0.02)))
pose_hand(GR, "L", 1240, "relaxed")
fs(1530)
gnk = (Wh(GR, "neck02") + Wh(GR, "neck03")) / 2
gnk.z = (Wh(GR, "eye.L").z + Wh(GR, "eye.R").z) / 2 - 0.098
gfd = Matrix.Rotation(math.radians(YAW["G"] - 10), 3, 'Z') @ Vector((0, -1, 0))
h = ray_surface([GB], gnk + gfd * 0.2, -gfd)
GTH_L = bone_local(GR, "neck02", h[0], h[1])
def own_throat(f):
    """her left palm on the left side of her own neck, the fingertips curling round to the front of her throat"""
    fs(f); P, N = bone_world(GR, "neck02", *GTH_L); N = Vector((N.x, N.y, 0)).normalized()
    up = Vector((0, 0, 1)); side = up.cross(N).normalized()
    if side.x < 0: side = -side            # toward her left
    fd = (N * 0.80 - side * 0.30 + up * 0.10).normalized()
    sh = Wh(GR, "upperarm01.L"); key_pole(CTG, "L", f, sh + Vector((0.20, -0.20, -0.45)))
    tip_on(GR, "L", f, P + N * 0.006, fd, -side, back=0.07, pose="two_point")
    return tip_natural(GR, "L", f, P + N * 0.007, flex=20.0)
OWNL = {}
for f in (1270, 1359, 1497):
    fs(f); g = surf_clear(GR, "L", [body_noarms(GR, GB)]); OWNL[f] = (round(g * 1000, 1), WORSTB[0])
log("girl own lips: finger clearance mm", OWNL)

# ================================================================== FX: vibration rings at the throat, pulse dots up the girl's arm, lip contour
def glow_mat(name, col):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1); em.inputs["Strength"].default_value = 6.0
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader"); mx.inputs["Fac"].default_value = 1.0
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m, mx.inputs["Fac"], em.inputs["Strength"]
def no_cast(o):
    o.visible_shadow = False; o.visible_diffuse = False; o.visible_glossy = False; o.visible_transmission = False
RINGS = []
def make_rings(prefix, rig, bone, Pl, Nl, windows, n=4, period=26, col=(1.0, 0.62, 0.12)):
    """concentric glowing ripples spreading over the skin from the contact; windows = [(f0, f1, rmax, strength)]"""
    for k in range(n):
        bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.035, major_segments=64, minor_segments=8)
        r = bpy.context.active_object; r.name = "%s_Ring%d" % (prefix, k); no_cast(r)
        m, fac, stg = glow_mat("M_%s_Ring%d" % (prefix, k), col); r.data.materials.append(m)
        P, N = bone_world(rig, bone, Pl, Nl)
        q = Vector((0, 0, 1)).rotation_difference(N)
        r.rotation_mode = 'QUATERNION'; r.rotation_quaternion = q; r.location = P + N * 0.004
        c = r.constraints.new('CHILD_OF'); c.target = rig; c.subtarget = bone
        fs(1); c.inverse_matrix = (rig.matrix_world @ rig.pose.bones[bone].matrix).inverted()
        # NB: the inverse is taken at frame 1; the ring basis is keyed in that frame's bone space below
        M1 = rig.matrix_world @ rig.pose.bones[bone].matrix
        loc1 = M1 @ Pl; n1 = (M1.to_3x3() @ Nl).normalized()
        r.location = loc1 + n1 * 0.004; r.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(n1)
        r.scale = (0.001,) * 3; r.keyframe_insert("scale", frame=1)
        fac.default_value = 0.0; fac.keyframe_insert("default_value", frame=1)
        for (f0, f1, rmax, st) in windows:
            f = f0 + k * period / n
            while f + period <= f1:
                r.scale = (0.006,) * 3; r.keyframe_insert("scale", frame=int(f))
                fac.default_value = 0.0; fac.keyframe_insert("default_value", frame=int(f))
                stg.default_value = st; stg.keyframe_insert("default_value", frame=int(f))
                fac.default_value = 0.9; fac.keyframe_insert("default_value", frame=int(f) + 3)
                r.scale = (rmax,) * 3; r.keyframe_insert("scale", frame=int(f + period) - 1)
                fac.default_value = 0.0; fac.keyframe_insert("default_value", frame=int(f + period) - 1)
                f += period
        RINGS.append(r)
def skin_ripples(prefix, rig, body, bone, Pl, keys_S, col=(1.0, 0.62, 0.12), K=320.0):
    """vibration ripples drawn ON the skin (a shader ring pattern around the contact): never cut into the neck or jaw.
    Distance is measured from an empty that follows the neck bone; the phase and strength are keyed values."""
    e = bpy.data.objects.new(prefix + "_RippleCentre", None); sc.collection.objects.link(e); e.empty_display_size = 0.01
    c = e.constraints.new('CHILD_OF'); c.target = rig; c.subtarget = bone
    fs(1); M1 = rig.matrix_world @ rig.pose.bones[bone].matrix; c.inverse_matrix = M1.inverted(); e.location = M1 @ Pl
    m = body.data.materials[0]; nt = m.node_tree
    out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]; lk = out.inputs["Surface"].links[0]; src = lk.from_socket
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.object = e
    ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; nt.links.new(tc.outputs["Object"], ln.inputs[0])
    def mth(op, a_, b_=None):
        n_ = nt.nodes.new("ShaderNodeMath"); n_.operation = op
        for i_, x in enumerate((a_, b_)):
            if x is None: continue
            if isinstance(x, (int, float)): n_.inputs[i_].default_value = float(x)
            else: nt.links.new(x, n_.inputs[i_])
        return n_.outputs[0]
    vT = nt.nodes.new("ShaderNodeValue"); vT.name = prefix + "_Phase"
    vS = nt.nodes.new("ShaderNodeValue"); vS.name = prefix + "_Strength"
    vR = nt.nodes.new("ShaderNodeValue"); vR.name = prefix + "_Radius"
    d = ln.outputs["Value"]
    ring = mth('POWER', mth('MAXIMUM', mth('SINE', mth('SUBTRACT', mth('MULTIPLY', d, K), vT.outputs[0])), 0.0), 6.0)
    fade = mth('MAXIMUM', mth('SUBTRACT', 1.0, mth('DIVIDE', d, vR.outputs[0])), 0.0)
    mask = mth('MULTIPLY', mth('MULTIPLY', ring, fade), vS.outputs[0])
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1); nt.links.new(mask, em.inputs["Strength"])
    add = nt.nodes.new("ShaderNodeAddShader"); nt.links.new(src, add.inputs[0]); nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    vR.outputs[0].default_value = 0.05
    for f, st, rr in keys_S:
        vS.outputs[0].default_value = st; vS.outputs[0].keyframe_insert("default_value", frame=f)
        vR.outputs[0].default_value = rr; vR.outputs[0].keyframe_insert("default_value", frame=f)
    vT.outputs[0].default_value = 0.0; vT.outputs[0].keyframe_insert("default_value", frame=1)
    vT.outputs[0].default_value = -(END - 1) * 0.30; vT.outputs[0].keyframe_insert("default_value", frame=END)   # rings travel outward
    for fc in iter_fcurves(nt.animation_data.action):
        if "_Phase" in fc.data_path:
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
fs(1)
skin_ripples("TH", TR, TB, "neck02", TH_L[0], [(1, 0.0, 0.04), (610, 0.0, 0.04), (626, 4.0, 0.045), (745, 4.0, 0.045), (752, 12.0, 0.07),
                                               (818, 12.0, 0.07), (826, 1.5, 0.028), (885, 1.5, 0.028), (893, 0.0, 0.028)])
skin_ripples("GTH", GR, GB, "neck02", GTH_L[0], [(1, 0.0, 0.035), (1508, 0.0, 0.035), (1522, 5.0, 0.04), (END, 5.0, 0.04)], col=(1.0, 0.75, 0.25))

# pulse dots: travel from the girl's fingertips up her forearm and upper arm (on the camera side of the sleeve)
CAMPOS = {}
DOTS = []
M_DOT, DOT_FAC, DOT_ST = glow_mat("M_PulseDot", (1.0, 0.70, 0.20))
for k in range(6):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0065, segments=16, ring_count=8); d = bpy.context.active_object
    d.name = "PulseDot%d" % k; d.data.materials.append(M_DOT); no_cast(d); DOTS.append(d)
def arm_path(f):
    fs(f)
    return [Wh(GR, "wrist.R").lerp(Wt(GR, "finger3-2.R"), 0.3), Wh(GR, "wrist.R"), Wh(GR, "lowerarm01.R").lerp(Wh(GR, "wrist.R"), 0.5), Wh(GR, "lowerarm01.R"),
            Wh(GR, "upperarm01.R").lerp(Wh(GR, "lowerarm01.R"), 0.5), Wh(GR, "upperarm01.R")]
RAD = [0.016, 0.026, 0.036, 0.042, 0.050, 0.058]
DOT_WIN = [(616, 891)]
def place_dots(f, campos):
    pts = arm_path(f); segs = [(pts[i], pts[i + 1], RAD[i], RAD[i + 1]) for i in range(len(pts) - 1)]
    L = [(b - a).length for a, b, ra, rb in segs]; tot = sum(L)
    per = 46
    for k, d in enumerate(DOTS):
        u = ((f - 616) / per + k / len(DOTS)) % 1.0
        s_ = u * tot; i = 0
        while i < len(L) - 1 and s_ > L[i]: s_ -= L[i]; i += 1
        a, b, ra, rb = segs[i]; t = s_ / max(L[i], 1e-6)
        p = a.lerp(b, t); r = ra + (rb - ra) * t
        out = (campos - p); ax = (b - a).normalized(); out = (out - ax * out.dot(ax)).normalized()
        d.location = p + out * r; d.keyframe_insert("location", frame=f)
        sc_ = 0.4 + 0.6 * math.sin(math.pi * u); d.scale = (sc_,) * 3; d.keyframe_insert("scale", frame=f)

# lip contour (beat 8): a thin glowing outline at her mouth that takes the O / E / M shape (stays 6 mm off her lips)
bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.06, major_segments=64, minor_segments=8)
LC = bpy.context.active_object; LC.name = "LipContour"; no_cast(LC)
mlc, lc_fac, lc_st = glow_mat("M_LipContour", (0.35, 0.85, 1.0)); LC.data.materials.append(mlc)
fs(1080); MH = TR.matrix_world @ TR.pose.bones["head"].matrix
ey_ = (Wh(TR, "eye.L") + Wh(TR, "eye.R")) / 2; hd_ = (MH.to_3x3() @ Vector((0, 0, 1))).normalized()
fw_ = Matrix.Rotation(math.radians(YAW["T"] + 12), 3, 'Z') @ Vector((0, -1, 0))
hm = ray_surface([TB], ey_ + Vector((0, 0, -0.072)) + fw_ * 0.25, -fw_)
LP, LN = hm[0].copy(), hm[1].copy()
mouth_c = LP + LN * 0.008
LC.rotation_mode = 'QUATERNION'; LC.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(LN); LC.location = mouth_c
c = LC.constraints.new('CHILD_OF'); c.target = TR; c.subtarget = "head"; c.inverse_matrix = MH.inverted()
for f, sx, sy in ((1080, 0.010, 0.010), (1092, 0.012, 0.014), (1120, 0.012, 0.014), (1132, 0.024, 0.006), (1160, 0.024, 0.006),
                  (1172, 0.022, 0.0025), (1200, 0.022, 0.0025), (1219, 0.012, 0.004)):
    LC.scale = (sx, sy, 0.012); LC.keyframe_insert("scale", frame=f)
for f, v in ((1080, 0.0), (1090, 0.8), (1205, 0.8), (1219, 0.0)):
    lc_fac.default_value = v; lc_fac.keyframe_insert("default_value", frame=f)
bpy.data.objects.remove(LC, do_unlink=True)      # (tested: a white hoop at the mouth read as a prop, removed)

# ================================================================== lights: the dim 'trapped' beat, the time-lapse (keyed values only)
L = {n: O[n].data for n in ("Key", "Fill", "Rim", "WinFill", "Sun")}
BASE = {n: l.energy for n, l in L.items()}
gm = bpy.data.materials["M_Garden"].node_tree.nodes
VS, VD = gm["Season"].outputs[0], gm["Daylight"].outputs[0]
LL = O["LampLight"].data
lamp_flame = [o for o in O if o.name.startswith("vintage_oil_lamp_flame")]
def key_light(f, k=1.0, day=1.0, lamp=0.0):
    for n, l in L.items():
        mult = k
        if n in ("WinFill", "Sun"): mult = k * (0.08 + 0.92 * day)
        if n in ("Key", "Fill"): mult = k * (0.55 + 0.45 * day)
        l.energy = BASE[n] * mult; l.keyframe_insert("energy", frame=f)
    VD.default_value = day; VD.keyframe_insert("default_value", frame=f)
    LL.energy = 40.0 * lamp; LL.keyframe_insert("energy", frame=f)
# the face light: a soft key on the girl's face that stays when the room goes dark (beat 2)
FKL = bpy.data.lights.new("FaceKey", 'AREA'); FKL.size = 0.35; FKL.color = (1.0, 0.86, 0.72); FKL.energy = 0.0
FK = bpy.data.objects.new("FaceKey", FKL); sc.collection.objects.link(FK); FK.visible_camera = False
fs(250); gface = (Wh(GR, "eye.L") + Wh(GR, "eye.R")) / 2
FK.location = gface + Vector((0.25, -0.55, 0.20)); FK.rotation_mode = 'QUATERNION'
FK.rotation_quaternion = (FK.location - gface).normalized().to_track_quat('Z', 'Y')
for f, v in ((1, 0.0), (140, 0.0), (175, 14.0), (320, 14.0), (362, 0.0)):
    FKL.energy = v; FKL.keyframe_insert("energy", frame=f)
for f, k, dl in ((1, 1.0, 1.0), (140, 1.0, 1.0), (178, 0.03, 0.15), (318, 0.03, 0.15), (362, 1.0, 1.0)):
    key_light(f, k=k, day=dl)
w_bg = sc.world.node_tree.nodes["Background"].inputs[1]
for f, v in ((1, 0.35), (140, 0.35), (178, 0.01), (318, 0.01), (362, 0.35)):
    w_bg.default_value = v; w_bg.keyframe_insert("default_value", frame=f)
# time-lapse 1359-1497: day -> night -> day -> night -> day, the seasons turn, the lamp is lit at night
TL = [(1359, 1.0, 0.0), (1376, 0.0, 1.0), (1394, 0.0, 1.0), (1410, 1.0, 0.0), (1428, 1.0, 0.0), (1444, 0.0, 1.0),
      (1460, 0.0, 1.0), (1476, 1.0, 0.0), (1497, 1.0, 0.0)]
for f, day, lamp in TL:
    key_light(f, k=1.0, day=day, lamp=lamp)
key_light(END, 1.0, 1.0, 0.0)
for f, v in ((1, 0.0), (1359, 0.0), (1400, 1.0), (1445, 2.0), (1490, 3.0), (END, 3.0)):
    VS.default_value = v; VS.keyframe_insert("default_value", frame=f)
# the clock: hands turn (slowly; fast during the time-lapse)
for o in O:
    if o.name.startswith("vintage_grandfather_clock_01_MinuteHand") or o.name.startswith("vintage_grandfather_clock_01_HourHand"):
        o.rotation_mode = 'XYZ'; base = o.rotation_euler.y
        rate = 1.0 if "Minute" in o.name else 1 / 12
        for f, turns in ((1, 0.0), (1359, 0.10), (1497, 0.10 + 6.0), (END, 6.12)):
            o.rotation_euler.y = base - 2 * math.pi * turns * rate; o.keyframe_insert("rotation_euler", index=1, frame=f)
        set_interp(o, 'LINEAR')

# ================================================================== the ONE camera
cam_d = bpy.data.cameras.new("CAM_Film"); CAM = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(CAM); sc.camera = CAM
AIM = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(AIM)
cam_d.sensor_fit = 'AUTO'; cam_d.sensor_width = 36; cam_d.clip_start = 0.01; cam_d.clip_end = 60
cam_d.dof.use_dof = True; cam_d.dof.focus_object = AIM; cam_d.dof.aperture_fstop = 8.0
CAM.rotation_mode = 'QUATERNION'
def P(*v): return Vector(v)
def gF(f): fs(f); return (Wh(GR, "eye.L") + Wh(GR, "eye.R")) / 2 + Vector((0, 0, -0.03))
def tF(f): fs(f); return (Wh(TR, "eye.L") + Wh(TR, "eye.R")) / 2 + Vector((0, 0, -0.03))
def thr(f): fs(f); return bone_world(TR, "neck02", *TH_L)[0]
def lip(f): fs(f); return bone_world(TR, "head", *LIP_L)[0]
def gthr(f): fs(f); return bone_world(GR, "neck02", *GTH_L)[0]
def mid(a, b, u=0.5): return a.lerp(b, u)
def MF(f): return mid(gF(f), tF(f))
def K(f, off, aim_off, lens, toward=None, u=0.0):
    pf = lambda: MF(f) + P(*off)
    if toward is None: af = lambda: MF(f) + P(*aim_off)
    else: af = lambda: mid(MF(f) + P(*aim_off), toward(f), u)
    return (f, pf, af, lens)
SEG = [K(1, (0.35, -1.85, 0.10), (0, 0, -0.14), 28), K(70, (0.26, -1.62, 0.08), (0, 0, -0.12), 28),
       K(131, (0.20, -1.32, 0.06), (0.03, 0, -0.06), 29), K(250, (0.26, -1.16, 0.04), (0.05, 0, -0.04), 30),
       K(362, (0.12, -1.26, 0.02), (0, 0, -0.10), 29), K(450, (0.05, -1.16, 0.00), (0, 0, -0.04), 30, thr, 0.35),
       K(612, (-0.05, -1.10, 0.00), (0, 0, -0.03), 31, thr, 0.40), K(747, (0.10, -1.13, 0.02), (0, 0, -0.03), 30, thr, 0.35),
       K(891, (0.16, -1.12, 0.03), (0, 0, -0.03), 30, lip, 0.30), K(1080, (0.04, -1.06, 0.02), (0, 0, -0.02), 31, lip, 0.30),
       K(1219, (-0.08, -1.12, 0.02), (0.02, 0, -0.04), 30), K(1359, (-0.25, -1.62, 0.12), (-0.20, 0, 0.00), 27),
       K(1430, (-0.35, -1.72, 0.14), (-0.22, 0, 0.02), 26), K(1497, (0.10, -1.26, 0.03), (0, 0, -0.05), 29),
       K(1570, (0.05, -1.13, 0.02), (0, 0, -0.03), 30), K(END, (-0.06, -1.04, 0.02), (0, 0, -0.02), 31)]
def look_q(p, a, up=Vector((0, 0, 1))):
    zc_ = (p - a).normalized(); yc = (up - zc_ * up.dot(zc_)).normalized(); xc = yc.cross(zc_)
    return Matrix((xc, yc, zc_)).transposed().to_quaternion()
ks = [(f, pf(), af(), l) for f, pf, af, l in SEG]
fx = [pchip([(k[0], k[1][i]) for k in ks]) for i in range(3)]
ax = [pchip([(k[0], k[2][i]) for k in ks]) for i in range(3)]
fl = pchip([(k[0], k[3]) for k in ks])
prev = None
for f in range(1, END + 1):
    p = Vector([fx[i](f) for i in range(3)]); a_ = Vector([ax[i](f) for i in range(3)])
    q = look_q(p, a_)
    if prev is not None and prev.dot(q) < 0: q = -q
    prev = q; CAMPOS[f] = p
    CAM.location = p; CAM.rotation_quaternion = q; AIM.location = a_; cam_d.lens = fl(f)
    CAM.keyframe_insert("location", frame=f); CAM.keyframe_insert("rotation_quaternion", frame=f)
    AIM.keyframe_insert("location", frame=f); cam_d.keyframe_insert("lens", frame=f)
set_interp(CAM, 'LINEAR'); set_interp(AIM, 'LINEAR'); set_interp(cam_d, 'LINEAR')
# small catchlight on the camera (eyes never black holes)
cl = bpy.data.lights.new("Catch", 'AREA'); cl.energy = 1.5; cl.size = 0.2; cl.color = (1, 0.96, 0.92)
clo = bpy.data.objects.new("Catchlight", cl); sc.collection.objects.link(clo); clo.parent = CAM; clo.location = (0.0, 0.08, 0.0); clo.visible_camera = False

# pulse dots now (they face the camera)
for d in DOTS: vis(d, 1, False); vis(d, 616, True); vis(d, 892, False)
for f in range(616, 892, 2):
    place_dots(f, CAMPOS[f])
for d in DOTS: set_interp(d, 'LINEAR')
for f, v in ((616, 0.0), (624, 0.9), (747, 0.9), (750, 1.0), (820, 1.0), (824, 0.5), (885, 0.5), (891, 0.0)):
    DOT_FAC.default_value = v; DOT_FAC.keyframe_insert("default_value", frame=f)
for f, v in ((616, 5.0), (747, 5.0), (750, 12.0), (820, 12.0), (824, 2.5), (891, 2.5)):
    DOT_ST.default_value = v; DOT_ST.keyframe_insert("default_value", frame=f)

# ================================================================== finish
log("settled hands (char, side, frame, min finger clearance mm)", SETTLE)
log("quat flips fixed", quat_continuity(GR) + quat_continuity(TR))
sc.frame_start, sc.frame_end = 1, END
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor; strips = se.strips if hasattr(se, "strips") else se.sequences
strips.new_sound("VO", VO, 1, 1)
sc.render.filepath = "//render/SpeakWithoutSight_v007_####.png"; sc.render.image_settings.file_format = 'PNG'
for o in O:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = False
sc.frame_set(1)
open(os.path.join(os.path.dirname(OUT), "animate_log.txt"), "w").write("\n".join(LOG))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("ANIM_DONE", OUT)
