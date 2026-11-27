"""RingBullet v009 stage B: acting, the ONE bullet, the ring, the two fragments, the ONE camera (no cuts), lights, VO.
blender -b a.blend --python 02_animate.py -- <vo.mp3> <out.blend>
Built to the client's VO (the v008 sync, frames 1-1395). Beats (VO frames):
  1 'The robber fired the gun' / 245 'threw his hands up' / 392 'instead of going through his skull' / 518 'hit his wedding ring'
  624 'glanced off ... split into two pieces' / 786 'One piece lodged in his finger' / 894 'the other went into his neck'
  997 'minor injuries and a dented ring' / 1175 'walked away okay' / end 1395.
Slow motion runs from the shot (f45) to the neck graze (f894): the owner moves little there, the camera always moves."""
import bpy, sys, math, random, os
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
PIPE = "/home/user/Muhammed/blender/pipeline"
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(PIPE + "/anim_lib.py").read())
exec(open(PIPE + "/hand_poses.py").read())
exec(open(HERE + "/lib_anim.py").read())
args = sys.argv[sys.argv.index("--") + 1:]
VO, OUT = args[0], args[1]
random.seed(21)
END = 1395
B_FIRE, B_HANDS, B_SKULL, B_HIT, B_SPLIT, B_FING, B_NECK, B_DENT, B_WALK = 45, 245, 392, 518, 624, 786, 894, 997, 1175
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); LOG.append(s); print("LOG", s)
O = bpy.data.objects
OW, OWB, OWC = O["Owner"], O["Owner.body"], O["Owner.clothes"]
RB, RBB, RBC = O["Robber"], O["Robber.body"], O["Robber.clothes"]
BUL, BUL2, FA, FB, MF = O["Bullet"], O["BulletFlat"], O["FragA"], O["FragB"], O["MuzzleFlash"]
GUN = O["Pistol"]

# ---- the sole offset: the MPFB rest pose puts the shoe soles below the ankle rest height; plant them ON the floor (z=0)
def min_z(obj):
    upd(); dg = bpy.context.evaluated_depsgraph_get(); e = obj.evaluated_get(dg); me = e.to_mesh()
    z = min((obj.matrix_world @ v.co).z for v in me.vertices); e.to_mesh_clear(); return z
SOLE = {"Owner": -min_z(O["Owner.shoes"]), "Robber": -min_z(O["Robber.shoes"])}
log("sole offsets mm", {k: round(v * 1000, 1) for k, v in SOLE.items()})
_CUR_SOLE = [0.0]
def ground_z(x, y):                       # anim_lib's walk/key_foot read this: the floor (z=0) plus the sole
    return _CUR_SOLE[0]

# ================================================================== rigs: IK + rotation limits on knees, elbows, hips
def limb_limits(rig):
    """IK rotation limits: knees bend one way only, elbows open to near-straight but never hyper-extend, hips stay
    in a natural range (flex/extend, small abduction). Flex signs are measured on this rig, not assumed."""
    upd()
    def flex_sign(bone, tip_bone, want):
        pb = rig.pose.bones[bone]; q0 = pb.rotation_quaternion.copy()
        t0 = (rig.matrix_world @ rig.pose.bones[tip_bone].tail).copy()
        pb.rotation_quaternion = Quaternion((1, 0, 0), math.radians(20)); upd()
        t1 = rig.matrix_world @ rig.pose.bones[tip_bone].tail
        pb.rotation_quaternion = q0; upd()
        return 1 if (t1 - t0).dot(Vector(want)) > 0 else -1
    out = {}
    for s in "LR":
        kn = rig.pose.bones["lowerleg01." + s]; sg = flex_sign("lowerleg01." + s, "lowerleg02." + s, (0, 1, 0))   # shin swings back
        kn.use_ik_limit_x = True
        kn.ik_min_x, kn.ik_max_x = (math.radians(0), math.radians(140)) if sg > 0 else (math.radians(-140), math.radians(0))
        kn.lock_ik_y = kn.lock_ik_z = True
        el = rig.pose.bones["lowerarm01." + s]; sa = flex_sign("lowerarm01." + s, "lowerarm02." + s, (0, -1, 0.3))
        el.use_ik_limit_x = True
        el.ik_min_x, el.ik_max_x = (math.radians(-40), math.radians(145)) if sa > 0 else (math.radians(-145), math.radians(40))
        hp = rig.pose.bones["upperleg01." + s]; sh = flex_sign("upperleg01." + s, "upperleg02." + s, (0, -1, 0))    # thigh swings forward
        hp.use_ik_limit_x = True; hp.use_ik_limit_z = True; hp.use_ik_limit_y = True
        hp.ik_min_x, hp.ik_max_x = (math.radians(-25), math.radians(95)) if sh > 0 else (math.radians(-95), math.radians(25))
        hp.ik_min_z, hp.ik_max_z = math.radians(-20), math.radians(20)
        hp.ik_min_y, hp.ik_max_y = math.radians(-15), math.radians(15)
        out[s] = (sg, sa, sh)
    return out
CTRL = {}; HUM = {}
for rig in (OW, RB):
    CT = make_human_ctrl(rig); add_hand_limits(rig)
    for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'
    log("limit signs (knee, elbow, hip)", rig.name, limb_limits(rig))
    CTRL[rig.name] = CT; HUM[rig.name] = Human(CT)
CO, CR = CTRL["Owner"], CTRL["Robber"]; HO, HR = HUM["Owner"], HUM["Robber"]

def key_pole(CT, s, f, target, kind="elbow"):
    n = ("Pole_elbow." if kind == "elbow" else "Pole_knee.") + s; pb = CT.PB[n]
    pb.location = CT.rest(n).to_3x3().inverted() @ (Vector(target) - CT.BN[n].head_local)
    pb.keyframe_insert("location", frame=f, group=n)

def key_spine(CT, f, flex=0.0, twist=0.0, side=0.0):
    for n, w in Human.SPINE_W.items():
        CT.key_rot(n, f, [("X", flex * w), ("Y", side * w), ("Z", twist * w)])

_HS = {}
def head_signs(rig):
    if rig.name in _HS: return _HS[rig.name]
    pb = rig.pose.bones["head"]; q0 = pb.rotation_quaternion.copy(); upd()
    e0 = Wh(rig, "eye.L"); out = {}
    for ax, i in (("X", 0), ("Z", 2)):
        pb.rotation_quaternion = Quaternion(Vector([1 if k == i else 0 for k in range(3)]), math.radians(10)); upd()
        out[ax] = Wh(rig, "eye.L") - e0; pb.rotation_quaternion = q0; upd()
    _HS[rig.name] = (1 if out["X"].z < 0 else -1, 1 if out["Z"].x > 0 else -1)
    return _HS[rig.name]
def key_head(rig, CT, f, yaw, pitch, roll=0.0):
    """yaw +: toward the character's own left (+X at rest); pitch +: look down"""
    sx, sz = head_signs(rig)
    for n, w in (("neck01", 0.25), ("neck02", 0.25), ("neck03", 0.2), ("head", 0.3)):
        CT.key_rot(n, f, [("X", sx * pitch * w), ("Y", roll * w), ("Z", sz * yaw * w)])

def stand(rig, H, CT, f, pos, yaw=0.0, flex=2.0, side=0.0, dz=0.0, feet=(0.12, 0.12), fwd=(0.0, 0.0)):
    """standing, both IK feet planted ON the floor (sole offset), knee poles forward"""
    sole = SOLE[rig.name]
    H.key_root(f, Vector((pos[0], pos[1], H.root_head.z - 0.012 + sole + dz)), yaw=yaw, flex=flex, side=side)
    Ry = Matrix.Rotation(math.radians(yaw), 3, 'Z')
    for s, sg, fx, fy in (("L", 1, feet[0], fwd[0]), ("R", -1, feet[1], fwd[1])):
        a = CT.BN["foot." + s].head_local
        tgt = Vector((pos[0], pos[1], a.z + sole)) + Ry @ Vector((sg * fx, fy, 0))
        M = Matrix.Translation(tgt) @ Ry.to_4x4() @ Matrix.Translation(-a) @ CT.rest("IK_foot." + s)
        CT.key_world("IK_foot." + s, f, M)
        key_pole(CT, s, f, tgt + Ry @ Vector((sg * 0.05, -0.8, 0.45)), kind="knee")

def bvh_eval(objs):
    upd(); dg = bpy.context.evaluated_depsgraph_get(); V = []; F = []
    for obj in objs:
        e = obj.evaluated_get(dg); me = e.to_mesh(); Mw = obj.matrix_world; off = len(V)
        V += [Mw @ v.co for v in me.vertices]; F += [[i + off for i in p.vertices] for p in me.polygons]; e.to_mesh_clear()
    return BVHTree.FromPolygons(V, F)
def ray_surface(objs, origin, direction):
    h = bvh_eval(objs).ray_cast(Vector(origin), Vector(direction).normalized(), 5.0)
    return h if h[0] is not None else None

def hang_hand(rig, H, s, f, fwd=0.06, drop=0.50, out_extra=0.0, swing=0.0):
    """hand hanging relaxed by the side, 4.5 cm outside the hip surface (ray-cast), palm toward the thigh"""
    sx = 1 if s == "L" else -1
    fs(f); sh = Wh(rig, "upperarm01." + s); yaw_m = rig.pose.bones["root"].matrix.to_3x3()
    z = sh.z - drop; y = sh.y - fwd - swing
    rm = rig.matrix_world @ rig.pose.bones["root"].matrix
    side_w = (rm.to_3x3() @ Vector((1, 0, 0))).normalized(); side_w.z = 0; side_w.normalize()
    # the bone's x axis may point either way: pick the one toward this side of the body
    if (sh - rm.translation).dot(side_w) * 1 < 0: side_w = -side_w
    hipc = Vector((rm.translation.x, rm.translation.y, z))
    wrist = hipc + side_w * (0.265 + out_extra) + Vector((0, sh.y - rm.translation.y - fwd - swing, 0))
    d = Vector((sx * 0.08, -0.25 - swing * 1.5, -1.0)).normalized(); n = Vector((-sx, 0.0, 0.0))
    H.key_hand(s, f, wrist, d, n, pole=sh + Vector((sx * 0.25, 0.45, -0.25)))
    apply_pose(rig, s, "relaxed", f)

# ================================================================== the OWNER (origin, facing -Y)
_CUR_SOLE[0] = SOLE["Owner"]
STAND_KEYS = [(1, 2.0, 0.0, 0.0), (45, 2.0, 0.5, 0.0), (60, 0.0, 0.0, 0.004), (245, 0.5, 0.0, 0.0), (300, 1.0, 0.0, -0.004),
              (518, 1.0, 0.0, -0.004), (540, 1.5, 0.0, -0.005), (894, 1.5, 0.0, -0.005), (910, 4.0, -2.0, -0.010),
              (997, 4.0, 0.0, -0.008), (1100, 4.0, 0.0, -0.008), (1140, 2.0, 0.0, 0.0), (1178, 1.5, 0.0, 0.0)]
for f, fl, sd, dz in STAND_KEYS:
    stand(OW, HO, CO, f, (0.0, 0.0), flex=fl, side=sd, dz=dz)
def breath(f, per, amp): return amp * math.sin(2 * math.pi * f / per)
SPF = pchip([(1, 1.5), (45, 1.5), (60, -3.0), (245, -1.0), (300, 1.0), (894, 1.0), (910, 5.0), (997, 5.0), (1100, 5.0), (1140, 1.5), (1178, 1.0)])
for f in list(range(1, 1180, 10)):
    slow = 245 < f < 894
    key_spine(CO, f, flex=SPF(f) + breath(f, 900 if slow else 150, 0.5 if slow else 1.4),
              twist=pchip([(1, 0), (45, 0), (60, -4), (245, -2), (300, 0), (910, -6), (997, 2), (1178, 0)])(f))
# head: on the robber (forward), flinch at the shot, tucked behind the hands, flinch away from the neck hit (to his right),
# down to the ring, up and relieved
HEAD = [(1, 22, 2), (45, 22, 2), (58, 18, -6), (245, 18, -4), (300, 14, -2), (518, 14, -2), (528, 16, -3), (894, 16, -3),
        (906, -14, 8), (930, -10, 6), (997, 4, 22), (1060, 6, 26), (1110, 4, 18), (1140, 0, -2), (1178, 2, 0)]
hy = pchip([(f, y) for f, y, p in HEAD]); hp = pchip([(f, p) for f, y, p in HEAD])
hr = pchip([(1, 0), (894, 0), (906, -10), (940, -6), (997, 0), (1178, 0)])
for f in list(range(1, 1180, 6)):
    tr_ = 1.2 if 60 < f < 900 else 0.4
    key_head(OW, CO, f, hy(f) + tr_ * math.sin(f / 9.0), hp(f) + tr_ * 0.7 * math.sin(f / 13.0 + 1.0), hr(f) + tr_ * 0.5 * math.sin(f / 17.0))
for f, sm, br, jaw, sq in ((1, -0.3, 0.9, 0.25, 0.0), (45, -0.3, 0.9, 0.25, 0.0), (52, -0.5, 1.0, 0.45, 0.5), (90, -0.4, 0.9, 0.40, 0.2), (140, -0.5, 0.6, 0.30, 0.3), (190, -0.3, 1.0, 0.45, 0.1), (230, -0.5, 0.7, 0.30, 0.3),
                           (245, -0.4, 0.9, 0.35, 0.1), (300, -0.5, -0.4, 0.30, 0.7), (518, -0.5, -0.4, 0.35, 0.8),
                           (700, -0.6, -0.2, 0.40, 0.6), (786, -0.5, -0.5, 0.35, 0.8), (800, -0.7, -0.8, 0.45, 1.0), (830, -0.5, -0.4, 0.30, 0.6), (860, -0.7, -0.7, 0.45, 0.9), (894, -0.6, -0.7, 0.40, 0.9),
                           (904, -0.8, -0.9, 0.55, 1.0), (960, -0.5, -0.3, 0.30, 0.5), (997, -0.2, 0.8, 0.35, 0.0),
                           (1080, -0.1, 0.9, 0.30, 0.0), (1120, 0.2, 0.5, 0.15, 0.0), (1160, 0.7, 0.3, 0.05, 0.1), (END, 0.75, 0.3, 0.05, 0.1)):
    key_face(OW, f, smile=sm, brow=br, jaw=jaw, squint=sq)
blinks(OW, [20, 140, 205, 330, 455, 700, 765, 840, 1010, 1090, 1150, 1250, 1340])
saccades(CO, 1, 245, every=30, amp=(1.5, 3.0), seed=4)
saccades(CO, 250, 955, every=26, amp=(2.0, 3.5), seed=7)
saccades(CO, 960, END, every=34, amp=(1.5, 2.5), seed=5)

# ---- arms: surrender ("hands up", palms forward at shoulder height) -> throws both hands up in front of his face (245-290)
def surrender(s, f, lift=0.0, out=0.0):
    sx = 1 if s == "L" else -1
    pc = Vector((sx * (0.36 + out), -0.17, 1.60 + lift))
    place_hand(OW, s, f, pc + Vector((0, -0.02, 0)), Vector((0, -1, 0)), Vector((sx * 0.15, 0, 1)), skin=0.02)
    key_pole(CO, s, f, Vector((sx * 0.75, 0.15, 1.05)))
    apply_pose(OW, s, "open_alarm", f)
def eyes(f): fs(f); return (Wh(OW, "eye.L") + Wh(OW, "eye.R")) / 2
EY = eyes(300)
SHIELD = {"L": EY + Vector((0.060, -0.215, -0.105)), "R": EY + Vector((-0.085, -0.205, -0.125))}
log("eyes at 300", tuple(round(x, 3) for x in EY))
def shield(s, f, dy=0.0, rot=0.0, pose="open_alarm", spread=None, amount=1.0):
    sx = 1 if s == "L" else -1
    pc = SHIELD[s] + Vector((0, dy, 0))
    fd = Matrix.Rotation(math.radians(rot), 3, 'Y') @ Vector((sx * 0.12, 0.05, 1.0))
    place_hand(OW, s, f, pc + Vector((0, -0.02, 0)), Vector((0, -1, 0)), fd, skin=0.02)
    key_pole(CO, s, f, Vector((sx * 0.55, -0.05, 1.10)))
    apply_pose(OW, s, pose, f, amount=amount, spread=spread)
for f, li in ((1, 0.0), (45, 0.0), (52, 0.03), (120, 0.02), (200, 0.0), (245, 0.0)):
    surrender("L", f, lift=li); surrender("R", f, lift=li * 0.8, out=0.01)
SPREAD = 9.0
for f in (290, 300, 518):
    shield("L", f, spread=SPREAD); shield("R", f, spread=2.0)
# impact micro-jolt (3 mm back, 2 deg) and settle; wince at the finger hit (fingers curl, hand pulls 2 cm toward him)
shield("L", 521, dy=0.003, rot=2.0, spread=SPREAD); shield("L", 540, spread=SPREAD); shield("L", 786, spread=SPREAD)
shield("L", 800, dy=0.02, rot=-4.0, pose="relaxed", amount=1.0); shield("L", 894, dy=0.02, rot=-4.0, pose="relaxed")
shield("R", 786, spread=2.0); shield("R", 894, spread=2.0)
# after the neck graze: the right hand drops to his side; the left comes down in front of his chest to look at the ring
fs(897)
for f in (920, 960):
    hang_hand(OW, HO, "R", f, fwd=0.10, drop=0.46)
LOOK_PC = Vector((0.10, -0.36, 1.27))
def look_hand(f, tilt=0.0):
    nrm = Vector((-0.15, 0.85, 0.55)).normalized()          # palm toward his face; he looks at the back of the hand? no: the palm side faces him
    fd = Vector((-0.55 + tilt, -0.35, 0.75)).normalized()
    place_hand(OW, "L", f, LOOK_PC - nrm * 0.02, -nrm, fd, skin=0.02)   # back of the hand (and the ring's top) toward him
    key_pole(CO, "L", f, Vector((0.60, 0.05, 1.00)))
    apply_pose(OW, "L", "relaxed", f, amount=0.7)
look_hand(950); look_hand(997); look_hand(1060, tilt=0.15); look_hand(1110, tilt=-0.05)
for f in (1000, 1060, 1110, 1140, 1178):
    hang_hand(OW, HO, "R", f, fwd=0.08, drop=0.48)
hang_hand(OW, HO, "L", 1150, fwd=0.07, drop=0.47); hang_hand(OW, HO, "L", 1178, fwd=0.06, drop=0.48)

# ---- the walk out (1180-1365): toward the door, arms swinging, feet planted on the floor; settles to the end
W0, W1 = 1182, 1365
P0, P1 = Vector((0.0, 0.0, 0.0)), Vector((0.24, -1.75, 0.0))
def wpath(f):
    u = smoothstep((f - W0) / (W1 - W0)); u = 0.5 * u + 0.5 * ((f - W0) / (W1 - W0))
    return P0.lerp(P1, max(0.0, min(1.0, u)))
WYAW = math.degrees(math.atan2(P1.x - P0.x, -(P1.y - P0.y)))     # the rest faces -Y
HO.walk(wpath, lambda f: WYAW, W0, W1, stride=0.64, duty=0.60, lift=0.10, bob=0.022, crouch=0.03, lean=5.0, step=2)
def del_keys(rig, bones, f0, f1):
    for fc in iter_fcurves(rig.animation_data.action):
        if not any('"%s"' % b in fc.data_path for b in bones): continue
        for kp in [k for k in fc.keyframe_points if f0 <= k.co.x <= f1][::-1]:
            fc.keyframe_points.remove(kp)
del_keys(OW, ("neck01", "neck02", "neck03", "head"), W0, W1)
for f in range(1180, END + 1, 6):
    key_head(OW, CO, f, 2 * math.sin(f / 40.0), -2 + 1.5 * math.sin(f / 33.0), 0.0)
stand(OW, HO, CO, W1 + 4, (P1.x, P1.y), yaw=WYAW, flex=2.0)
stand(OW, HO, CO, END, (P1.x, P1.y), yaw=WYAW, flex=3.0, dz=-0.003)
# arm swing: opposite to the legs (left arm forward with the right leg)
dist = 0.0; prev = wpath(W0)
for f in range(W0, W1 + 1, 3):
    p = wpath(f); dist += (p - prev).length; prev = p
    ph = 2 * math.pi * dist / 0.64
    for s, sg in (("L", 1), ("R", -1)):
        hang_hand(OW, HO, s, f, fwd=0.07, drop=0.48, swing=sg * 0.085 * math.sin(ph))
for f in (W1 + 4, END):
    for s in "LR": hang_hand(OW, HO, s, f, fwd=0.06, drop=0.49)

# ================================================================== the RING (gold band on the left ring finger) - sized to the finger
def finger_frame(f, bone="finger4-1.L", t=0.42):
    fs(f); pb = OW.pose.bones[bone]
    h = OW.matrix_world @ pb.head; tl = OW.matrix_world @ pb.tail
    return h.lerp(tl, t), (tl - h).normalized()
def body_points_near(f, c, ax, half=0.003, rmax=0.016):
    pts = eval_points(OWB)
    out = []
    for i, p, n in pts:
        d = p - c; along = d.dot(ax)
        if abs(along) < half:
            r = (d - ax * along).length
            if r < rmax: out.append((r, p))
    return out
fs(300)
RC, RAX = finger_frame(300)
# the finger's own surface radius at the ring: the nearest ring of body points around the bone axis (the neighbours are further)
near = sorted(body_points_near(300, RC, RAX), key=lambda t: t[0])
rf = sum(r for r, p in near[:10]) / max(1, len(near[:10])) if near else 0.008
rads = [r for r, p in near if r < rf * 1.6]
RF = max(rads) if rads else 0.009
log("finger radius at the ring mm", round(RF * 1000, 2), "points", len(rads))
bpy.ops.mesh.primitive_torus_add(major_radius=RF + 0.0017, minor_radius=0.0016, major_segments=64, minor_segments=16)
RING = bpy.context.active_object; RING.name = "Ring"
RING.scale = (1, 1, 1.75); bpy.ops.object.transform_apply(scale=True)
for p_ in RING.data.polygons: p_.use_smooth = True
gold = bpy.data.materials.new("M_Gold"); gold.use_nodes = True; pg = gold.node_tree.nodes["Principled BSDF"]
pg.inputs["Base Color"].default_value = (1.0, 0.66, 0.20, 1); pg.inputs["Metallic"].default_value = 1.0; pg.inputs["Roughness"].default_value = 0.18
RING.data.materials.append(gold)
# place: axis along the finger, at RC; owned by the finger bone (Child Of) for the whole film
RING.rotation_mode = 'QUATERNION'
RING.matrix_world = Matrix.Translation(RC) @ Vector((0, 0, 1)).rotation_difference(RAX).to_matrix().to_4x4()
c = RING.constraints.new('CHILD_OF'); c.target = OW; c.subtarget = "finger4-1.L"
fs(300); upd(); c.inverse_matrix = (OW.matrix_world @ OW.pose.bones["finger4-1.L"].matrix).inverted()
upd()

# ================================================================== where the bullet strikes (f518 pose) and where the pieces go
fs(B_HIT)
RC, RAX = finger_frame(B_HIT)
RPOS = (1.25, -1.45)                                                          # the robber: at his front-left
ROB_AIM = Vector((RPOS[0] - 0.10, RPOS[1] + 0.35, 1.55))
NP = ROB_AIM - RC; NP = (NP - RAX * NP.dot(RAX)).normalized()                  # the ring side facing the gun
P_IMP = RC + NP * (RF + 0.0035)                                               # front face of the ring
log("ring centre", tuple(round(x, 4) for x in RC), "impact", tuple(round(x, 4) for x in P_IMP))
BODY_HIT = [OWB, OWC]
# fragment B: from just in front of the gap between the ring finger and the little finger, back THROUGH the gap to the
# left side of his neck. Search the gap point and neck point for the path with the most clearance from his body.
fs(B_SPLIT + 10)
BV = bvh_eval([OWB, OWC])
def seg_clear(a_, b_, skip_end=0.010):
    L_ = (b_ - a_).length; n_ = max(8, int(L_ / 0.002)); worst = 9.0
    for i in range(n_ + 1):
        p = a_.lerp(b_, i / n_)
        if (p - b_).length < skip_end: continue
        loc, nrm, idx, d = BV.find_nearest(p)
        if loc is None: continue
        sd = d if (p - loc).dot(nrm) >= 0 else -d
        worst = min(worst, sd)
    return worst
best = None
nk0 = OW.matrix_world @ OW.pose.bones["neck01"].head; nk1 = OW.matrix_world @ OW.pose.bones["neck03"].tail
g4b = OW.pose.bones["finger4-1.L"]; g5b = OW.pose.bones["finger5-1.L"]
sideG = ((OW.matrix_world @ g5b.head) - (OW.matrix_world @ g4b.head)); sideG = (sideG - RAX * sideG.dot(RAX) - NP * sideG.dot(NP)).normalized()
necks = []
for u in (0.1, 0.25, 0.4, 0.55, 0.7):
    nc = nk0.lerp(nk1, u)
    for ang in (-75, -60, -45, -30, -15, 0, 15):
        dd = Matrix.Rotation(math.radians(ang), 3, 'Z') @ Vector((0, -1, 0))
        h = ray_surface([OWB, OWC], nc + dd * 0.12, -dd)
        if h and (h[0] - nc).length < 0.10 and h[0].x > -0.005 and h[0].z < Wh(OW, 'neck03').z - 0.012: necks.append((h[0].copy(), h[1].copy()))
log("neck candidates", len(necks)); C1MAX = [-1.0]
fs(B_FING - 2)
pa, axa = finger_frame(B_FING - 2, "finger4-2.L", 0.45)
hA = ray_surface([OWB], pa + NP * 0.03, -NP)
S_A, N_A = (hA[0].copy(), hA[1].copy()) if hA else (pa + NP * 0.008, NP)
fs(B_SPLIT + 10)

for aa in (0.008, 0.016, 0.026, 0.036, 0.05):
    for bb in (-0.08, -0.06, -0.045, -0.03, 0.0, 0.03, 0.045, 0.06, 0.08):
        for cc in (-0.03, -0.015, 0.0, 0.015, 0.03):
            Q = RC + NP * (RF + aa) + sideG * bb + RAX * cc
            c1 = seg_clear(P_IMP + NP * 0.003, Q, skip_end=0.0)
            C1MAX[0] = max(C1MAX[0], c1)
            if c1 < 0.002: continue
            for N_, NN_ in necks:
                cl = min(c1, seg_clear(Q, N_))
                if best is None or cl > best[0] + 1e-4 or (abs(cl - best[0]) < 1e-4 and bb < best[1][1]):
                    best = (cl, (aa, bb, cc), Q.copy(), None, N_.copy(), NN_.copy())
log("glance clearance max mm", round(C1MAX[0] * 1000, 2))
if best is None:
    best = (-1, None, RC + NP * 0.03 + sideG * 0.05, None, necks[0][0], necks[0][1]) if necks else None
CLB, tB, Q_B, G_B, N_B, NN_B = best
log("parts mm glance/B/A", round(seg_clear(P_IMP + NP * 0.003, Q_B, skip_end=0.0)*1000,2), round(seg_clear(Q_B, N_B)*1000,2), round(seg_clear(Q_B, S_A, skip_end=0.004)*1000,2), "necks", [tuple(round(x,3) for x in n[0]) for n in necks])
log("fragment B path clearance mm", round(CLB * 1000, 2), "q", tB, "Q", tuple(round(x, 4) for x in Q_B), "neck", tuple(round(x, 4) for x in N_B))
log("split point clearance mm: B path", round(seg_clear(Q_B, N_B) * 1000, 2))
Q_A = Q_B.copy()                     # both pieces leave from the split point beside the little finger
hA2 = ray_surface([OWB], Q_A, (pa - Q_A))           # piece A flies straight from the split point into the finger
if hA2: S_A, N_A = hA2[0].copy(), hA2[1].copy()
log("fragment A lodge point (little finger, outer side)", tuple(round(x, 4) for x in S_A), "clear", round(seg_clear(Q_A, S_A) * 1000, 1))

# ================================================================== the ROBBER (y=-2.0, facing +Y), the gun in his right hand
_CUR_SOLE[0] = SOLE["Robber"]
RYAW = math.degrees(math.atan2((RC.x - RPOS[0]), -(RC.y - RPOS[1])))       # rest faces -Y
RDIR = Vector((RC.x - RPOS[0], RC.y - RPOS[1], 0)).normalized()
RRIGHT = Matrix.Rotation(math.radians(RYAW), 3, 'Z') @ Vector((-1, 0, 0))
RLEFT = -RRIGHT
log("robber yaw", round(RYAW, 1), "dir", tuple(round(x, 2) for x in RDIR), "right", tuple(round(x, 2) for x in RRIGHT))
for f, fl in ((1, 4.0), (45, 4.0), (50, 1.0), (70, 3.5), (300, 4.0)):
    stand(RB, HR, CR, f, RPOS, yaw=RYAW, flex=fl, feet=(0.15, 0.13), fwd=(0.06, -0.10))
for f in range(1, 301, 20):
    key_spine(CR, f, flex=4.0 + breath(f, 160, 1.0), twist=-8.0)
for f in (1, 300):
    key_head(RB, CR, f, 4.0, 4.0)
hang_hand(RB, HR, "L", 1, fwd=0.04, drop=0.50); hang_hand(RB, HR, "L", 300, fwd=0.05, drop=0.50)
# right arm: extended toward the ring/face, elbow softly bent
def aim_arm(f, kick=0.0):
    fs(f); sh = Wh(RB, "upperarm01.R")
    aim = (P_IMP - sh).normalized()
    nrm = RLEFT.copy(); nrm = (nrm - aim * nrm.dot(aim)).normalized()     # palm toward his midline (the grip)
    fd = (aim + Vector((0, 0, kick * 6))).normalized()
    place_hand(RB, "R", f, sh + aim * 0.56 + Vector((0, 0, kick)), nrm, fd, skin=0.015)
    key_pole(CR, "R", f, sh + RRIGHT * 0.35 - RDIR * 0.10 + Vector((0, 0, -0.45)))
    apply_pose(RB, "R", "wrap_grip", f)
for f, k in ((1, 0.0), (45, 0.0), (48, 0.05), (60, 0.015), (90, 0.0), (300, 0.0)):
    aim_arm(f, k)
# the gun: grip in the palm, barrel along the aim; owned by the right wrist bone (Child Of) for the whole film
fs(1); upd()
wr = Wh(RB, "wrist.R"); k3 = Wh(RB, "finger3-1.R"); k2 = Wh(RB, "finger2-1.R"); k5 = Wh(RB, "finger5-1.R")
dH = (k3 - wr).normalized(); aH = (k5 - k2).normalized()
palmc = wr.lerp(k3, 0.55)
nH = dH.cross(aH).normalized()
# which side is the palm: the curled middle finger tip lies on it
tipm = Wt(RB, "finger3-3.R")
if (tipm - palmc).dot(nH) < 0: nH = -nH
gm = [o for o in GUN.children_recursive if o.type == 'MESH']
loc_pts = [GUN.matrix_world.inverted() @ (o.matrix_world @ Vector(cc)) for o in gm for cc in o.bound_box]
gmax_x = max(p.x for p in loc_pts)
fwdH = (dH - aH * dH.dot(aH)).normalized()
fwdA = (P_IMP - palmc); fwdA = (fwdA - aH * fwdA.dot(aH)).normalized()
fwdB = fwdA.lerp(fwdH, 0.15).normalized()
Xg = fwdB; Zg = (-aH - Xg * (-aH).dot(Xg)).normalized(); Yg = Zg.cross(Xg)
Rg = Matrix((Xg, Yg, Zg)).transposed()
GRIP_L = Vector((-0.035, 0.0, -0.012))                         # the grip's middle in the pistol's own frame
gpos = palmc + nH * 0.022 - Rg @ GRIP_L
GUN.matrix_world = Matrix.Translation(gpos) @ Rg.to_4x4()
# move the grip so the curled fingers wrap round it instead of passing through (finger-bone points vs the pistol mesh)
upd(); dg_ = bpy.context.evaluated_depsgraph_get(); GV = []; GF = []
for o in gm:
    e = o.evaluated_get(dg_); me = e.to_mesh(); off = len(GV)
    GV += [GUN.matrix_world.inverted() @ (o.matrix_world @ v.co) for v in me.vertices]; GF += [[i + off for i in p_.vertices] for p_ in me.polygons]; e.to_mesh_clear()
GB = BVHTree.FromPolygons(GV, GF)
FPTS = []
for pb in RB.pose.bones:
    if pb.name.endswith(".R") and (pb.name.startswith("finger") or pb.name.startswith("metacarpal")):
        for t in (0.0, 0.5, 1.0): FPTS.append(RB.matrix_world @ pb.head.lerp(pb.tail, t))
def grip_cost(off):
    Mg = Matrix.Translation(gpos + off) @ Rg.to_4x4(); Mi = Mg.inverted(); bad = 0; near_ = 0
    for p in FPTS:
        q = Mi @ p; loc, nrm, idx, d = GB.find_nearest(q)
        if loc is None: continue
        sd = d if (q - loc).dot(nrm) >= 0 else -d
        if sd < 0.003: bad += 1
        if sd < 0.018: near_ += 1
    return 3 * bad - near_, bad
bestg = None
for a1 in (-0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.03):
    for a2 in (-0.05, -0.035, -0.02, -0.01, 0.0, 0.01, 0.02):
        for a3 in (-0.03, -0.015, 0.0, 0.015, 0.03):
            off = nH * a1 + fwdB * a2 + Zg * a3
            c_ = grip_cost(off)
            if bestg is None or c_ < bestg[0]: bestg = (c_, off)
log("gun grip search (bad, -near)", bestg[0], "offset mm", tuple(round(x * 1000, 1) for x in bestg[1]))
gpos = gpos + bestg[1]
GUN.matrix_world = Matrix.Translation(gpos) @ Rg.to_4x4()
c = GUN.constraints.new('CHILD_OF'); c.target = RB; c.subtarget = "wrist.R"
upd(); c.inverse_matrix = (RB.matrix_world @ RB.pose.bones["wrist.R"].matrix).inverted(); upd()
tipv = [GUN.matrix_world.inverted() @ (o.matrix_world @ v.co) for o in gm for v in o.data.vertices]
tipv = [v for v in tipv if v.x > gmax_x - 0.004]
MUZ_L = Vector((gmax_x, sum(v.y for v in tipv) / len(tipv), sum(v.z for v in tipv) / len(tipv)))
log("muzzle local", tuple(round(x, 4) for x in MUZ_L))
def muzzle(f): fs(f); return GUN.matrix_world @ MUZ_L
def barrel(f): fs(f); return (GUN.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
M0 = muzzle(B_FIRE)
log("muzzle at fire", tuple(round(x, 3) for x in M0), "barrel->impact deg", round(math.degrees(barrel(B_FIRE).angle(P_IMP - M0)), 1))

# ================================================================== the bullet: one object; flat shape after the ring; two fragments
BL = 0.0155
BDIR = (P_IMP - M0).normalized()
SB = pchip([(B_FIRE, 0.0), (B_FIRE + 3, 0.07), (B_FIRE + 10, 0.09), (B_HANDS, 0.45), (B_SKULL, 0.78), (B_HIT, 1.0)])
P_STOP = P_IMP - BDIR * 0.006
def nose(f): return M0.lerp(P_STOP, SB(f))
BUL.rotation_mode = 'QUATERNION'; spin = 0.0
for f in range(B_FIRE, B_HIT + 1):
    spin += math.radians(30 if f < B_FIRE + 4 else 4)
    BUL.location = nose(f) - BDIR * BL; BUL.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(BDIR) @ Quaternion((0, 0, 1), spin)
    BUL.keyframe_insert("location", frame=f); BUL.keyframe_insert("rotation_quaternion", frame=f)
set_interp(BUL, 'LINEAR'); quat_continuity(BUL)
vis(BUL, 1, False); vis(BUL, B_FIRE, True); vis(BUL, B_HIT + 1, False)
# the flattened slug: glances off the ring toward the gap (518 -> 624), then splits
GDIR = (Q_B - P_IMP).normalized()
BUL2.rotation_mode = 'QUATERNION'; BUL2.scale = (0.55,) * 3
for f in range(B_HIT + 1, B_SPLIT + 1):
    u = (f - B_HIT - 1) / (B_SPLIT - B_HIT - 1)
    p = (P_IMP + NP * 0.004).lerp(Q_B, 1 - (1 - u) ** 1.6)
    nd_ = -NP.lerp(GDIR, 0.3 + 0.5 * u); nd_.normalize()
    BUL2.location = p - nd_ * 0.0108 * 0.55; BUL2.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(nd_) @ Quaternion((0, 0, 1), math.radians(2.5 * f))
    BUL2.keyframe_insert("location", frame=f); BUL2.keyframe_insert("rotation_quaternion", frame=f)
set_interp(BUL2, 'LINEAR'); quat_continuity(BUL2)
vis(BUL2, 1, False); vis(BUL2, B_HIT + 1, True); vis(BUL2, B_SPLIT + 1, False)
# fragment A: split point -> lodged in the finger front (786), then owned by the finger bone
FA.rotation_mode = 'QUATERNION'; FB.rotation_mode = 'QUATERNION'
FA.scale = (0.9,) * 3; FB.scale = (0.9,) * 3
S_A_in = S_A - N_A * 0.0012
for f in range(B_SPLIT + 1, B_FING + 1):
    u = (f - B_SPLIT - 1) / (B_FING - B_SPLIT - 1)
    FA.location = Q_A.lerp(S_A_in, u); FA.rotation_quaternion = Quaternion((0.3, 0.8, 0.5), math.radians(3 * f)).normalized()
    FA.keyframe_insert("location", frame=f); FA.keyframe_insert("rotation_quaternion", frame=f)
set_interp(FA, 'LINEAR'); quat_continuity(FA)
owner_switch(FA, B_FING + 1, OW, "finger4-2.L", log=log)
vis(FA, 1, False); vis(FA, B_SPLIT + 1, True)
# fragment B: split point -> through the gap -> the left side of his neck (894), then gone (a small graze mark stays)
N_B_in = N_B - NN_B * 0.002
for f in range(B_SPLIT + 1, B_NECK + 1):
    u = (f - B_SPLIT - 1) / (B_NECK - B_SPLIT - 1)
    FB.location = Q_B.lerp(N_B_in, u); FB.rotation_quaternion = Quaternion((0.7, 0.2, 0.6), math.radians(4 * f)).normalized()
    FB.keyframe_insert("location", frame=f); FB.keyframe_insert("rotation_quaternion", frame=f)
set_interp(FB, 'LINEAR'); quat_continuity(FB)
vis(FB, 1, False); vis(FB, B_SPLIT + 1, True); vis(FB, B_NECK + 2, False)
def mark(name, p, n, bone, f_on, size=0.0035):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=16, ring_count=8)
    o = bpy.context.active_object; o.name = name; o.scale = (size, size * 0.7, size * 0.25)
    m = bpy.data.materials.new("M_" + name); m.use_nodes = True; pr = m.node_tree.nodes["Principled BSDF"]
    pr.inputs["Base Color"].default_value = (0.42, 0.04, 0.05, 1); pr.inputs["Roughness"].default_value = 0.45
    o.data.materials.append(m); bpy.ops.object.shade_smooth()
    o.rotation_mode = 'QUATERNION'
    o.matrix_world = Matrix.Translation(p - n * 0.0004) @ Vector((0, 0, 1)).rotation_difference(n).to_matrix().to_4x4() @ Matrix.Diagonal((size, size * 0.7, size * 0.25, 1))
    fs(f_on); upd()
    c = o.constraints.new('CHILD_OF'); c.target = OW; c.subtarget = bone
    c.inverse_matrix = (OW.matrix_world @ OW.pose.bones[bone].matrix).inverted(); upd()
    vis(o, 1, False); vis(o, f_on, True)
    return o
fs(B_FING); mark("CutFinger", S_A, N_A, "finger4-2.L", B_FING, size=0.0028)
fs(B_NECK)
mark("NeckGraze", N_B, NN_B, "neck02", B_NECK + 1, size=0.0045)

# ---- the dent in the ring: a shape key pushing the struck side in and flattening it (keyed on at the hit)
RING.shape_key_add(name="Basis"); dk = RING.shape_key_add(name="dent")
fs(B_HIT); upd()
Mi = RING.matrix_world.inverted(); pl = Mi @ P_IMP; nl = (Mi.to_3x3() @ NP).normalized(); cl_ = Mi @ RC
for i, v in enumerate(RING.data.vertices):
    d = (v.co - pl).length
    if d < 0.006:
        w = 0.5 * (1 + math.cos(math.pi * d / 0.006))
        dk.data[i].co = v.co - nl * 0.0011 * w
for f, v in ((1, 0.0), (B_HIT, 0.0), (B_HIT + 3, 1.0), (END, 1.0)):
    dk.value = v; dk.keyframe_insert("value", frame=f)

# ---- sparks at the hit: thin streaks flying out of the ring face (518-570), the hit light
SPK = sorted([o for o in O if o.name.startswith("Spark")], key=lambda o: o.name)
rnd = random.Random(5)
for k, s_ in enumerate(SPK):
    d = (NP * rnd.uniform(0.4, 1.0) + RAX * rnd.uniform(-1, 1) + NP.cross(RAX) * rnd.uniform(-1, 1)).normalized()
    Lk = rnd.uniform(0.015, 0.045); f1 = B_HIT + rnd.randint(30, 52)
    s_.rotation_mode = 'QUATERNION'; s_.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    s_.keyframe_insert("rotation_quaternion", frame=B_HIT)
    for f, u, sc_ in ((B_HIT, 0.0, 0.3), (B_HIT + 4, 0.25, 1.3), (f1 - 8, 0.85, 1.0), (f1, 1.0, 0.05)):
        s_.location = P_IMP + d * (0.002 + Lk * u); s_.scale = (sc_, sc_, sc_)
        s_.keyframe_insert("location", frame=f); s_.keyframe_insert("scale", frame=f)
    vis(s_, 1, False); vis(s_, B_HIT, True); vis(s_, f1 + 1, False)
HL = bpy.data.lights.new("HitLight", 'POINT'); HL.color = (1.0, 0.7, 0.35); HL.shadow_soft_size = 0.002
hlo = bpy.data.objects.new("HitLight", HL); bpy.context.scene.collection.objects.link(hlo); hlo.location = P_IMP + NP * 0.015
for f, e in ((1, 0.0), (B_HIT - 1, 0.0), (B_HIT, 0.15), (B_HIT + 6, 0.08), (B_HIT + 40, 0.0), (END, 0.0)):
    HL.energy = e; HL.keyframe_insert("energy", frame=f)

# ---- muzzle flash (3 frames) and a little smoke that drifts slowly in the slow motion
fs(B_FIRE)
MF.rotation_mode = 'QUATERNION'
MF.matrix_world = Matrix.Translation(M0) @ Vector((1, 0, 0)).rotation_difference(barrel(B_FIRE)).to_matrix().to_4x4()
for f, sc_ in ((B_FIRE - 1, 0.2), (B_FIRE, 1.0), (B_FIRE + 1, 1.3), (B_FIRE + 2, 0.8), (B_FIRE + 3, 0.1)):
    MF.scale = (sc_,) * 3; MF.keyframe_insert("scale", frame=f)
vis(MF, 1, False); vis(MF, B_FIRE, True); vis(MF, B_FIRE + 3, False)
for k, sm_ in enumerate(sorted([o for o in O if o.name.startswith("Smoke")], key=lambda o: o.name)):
    d = (barrel(B_FIRE) + Vector((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), rnd.uniform(0.0, 0.4)))).normalized()
    for f, u, s2 in ((B_FIRE, 0.0, 0.4), (B_FIRE + 6, 0.35, 1.3), (300, 0.8, 2.0)):
        sm_.location = M0 + d * (0.01 + 0.07 * u) + Vector((0, 0, 0.02 * u)); sm_.scale = (s2,) * 3
        sm_.keyframe_insert("location", frame=f); sm_.keyframe_insert("scale", frame=f)
    vis(sm_, 1, False)
FL = bpy.data.lights.new("MuzzleLight", 'POINT'); FL.color = (1.0, 0.7, 0.35); FL.shadow_soft_size = 0.02
flo = bpy.data.objects.new("MuzzleLight", FL); bpy.context.scene.collection.objects.link(flo); flo.location = M0 + barrel(B_FIRE) * 0.05
for f, e in ((1, 0.0), (B_FIRE - 1, 0.0), (B_FIRE, 60.0), (B_FIRE + 2, 30.0), (B_FIRE + 6, 0.0), (END, 0.0)):
    FL.energy = e; FL.keyframe_insert("energy", frame=f)

# ---- the robber runs off while the camera is on the owner (he and his gun are hidden from f330: never in frame then)
for o in [RB] + [c for c in RB.children] + [GUN] + list(GUN.children_recursive):
    vis(o, 1, True); vis(o, 330, False)

# ---- police lights through the door from 1060 (red/blue alternating, 6 flashes a second)
PR, PRL, PBL_, PBLL = O["OUT_PoliceRed"], O["OUT_PoliceRed_L"], O["OUT_PoliceBlue"], O["OUT_PoliceBlue_L"]
def flash(obj, light, f, on, strength=60.0, energy=3000.0):
    em = obj.data.materials[0].node_tree.nodes["Emission"].inputs["Strength"]
    em.default_value = strength if on else 0.0; em.keyframe_insert("default_value", frame=f)
    light.data.energy = energy if on else 0.0; light.data.keyframe_insert("energy", frame=f)
flash(PR, PRL, 1, False); flash(PBL_, PBLL, 1, False)
for i, f in enumerate(range(1060, END + 1, 10)):
    flash(PR, PRL, f, i % 2 == 0); flash(PBL_, PBLL, f, i % 2 == 1)
for o in (PR, PBL_):
    nt = o.data.materials[0].node_tree
    if nt.animation_data and nt.animation_data.action: set_interp(nt, 'CONSTANT')
for o in (PRL, PBLL): set_interp(o.data, 'CONSTANT')

# ================================================================== camera: ONE camera, PCHIP paths, level horizon
cam_d = bpy.data.cameras.new("CAM_Film"); CAM = bpy.data.objects.new("CAM_Film", cam_d); bpy.context.scene.collection.objects.link(CAM)
sc.camera = CAM
cam_d.sensor_fit = 'AUTO'; cam_d.sensor_width = 36; cam_d.dof.use_dof = False; cam_d.clip_start = 0.004; cam_d.clip_end = 60
CAM.rotation_mode = 'QUATERNION'
def P(*v): return Vector(v)
UPV = Vector((0, 0, 1)); RGT = BDIR.cross(UPV).normalized()
fs(1); RB0 = Vector((RPOS[0], RPOS[1], 0.0))
VS = (-BDIR + RGT).normalized()
VS2 = Matrix.Rotation(math.radians(-12), 3, 'Z') @ VS; VS3 = Matrix.Rotation(math.radians(-24), 3, 'Z') @ VS
VM = Matrix.Rotation(math.radians(-20), 3, 'Z') @ VS
def pth(u): return M0.lerp(P_IMP, u)
def bofs(f, back, right, up): return bpos(f) - BDIR * back + RGT * right + UPV * up
def bpos(f): fs(f); return BUL.matrix_world @ Vector((0, 0, BL * 0.6))
def fbpos(f): fs(f); return FB.matrix_world.translation.copy()
def ring_w(f): fs(f); return RING.matrix_world.translation.copy()
SIDE = Vector((1, 0, 0))
K = [
    (1,   lambda: RB0 - RDIR * 0.80 + RRIGHT * 0.32 + P(0, 0, 1.56), lambda: P(0.05, -0.25, 1.45), 24),
    (40,  lambda: RB0 - RDIR * 0.70 + RRIGHT * 0.40 + P(0, 0, 1.57), lambda: P(0.05, -0.28, 1.48), 25),
    (80,  lambda: pth(0.25) + VS * 0.75 + UPV * 0.08, lambda: pth(0.55).lerp(eyes(80), 0.45), 26),
    (170, lambda: pth(0.38) + VS * 0.62 + UPV * 0.08, lambda: pth(0.65).lerp(eyes(170), 0.40), 27),
    (B_HANDS, lambda: pth(0.50) + VS * 0.55 + UPV * 0.08, lambda: pth(0.75).lerp(eyes(B_HANDS), 0.30), 28),
    (B_SKULL, lambda: pth(0.75) + VS * 0.46 + UPV * 0.08, lambda: pth(0.88).lerp(eyes(B_SKULL), 0.40), 28),
    (470, lambda: P_IMP + VS * 0.40 + UPV * 0.07, lambda: P_IMP.lerp(eyes(470), 0.38), 30),
    (B_HIT, lambda: P_IMP + VM * 0.30 + UPV * 0.05, lambda: P_IMP.lerp(eyes(B_HIT), 0.30), 32),
    (580, lambda: P_IMP + VS * 0.34 + UPV * 0.06, lambda: P_IMP.lerp(eyes(580), 0.35), 30),
    (618, lambda: Q_B + VS * 0.12 + UPV * 0.03, lambda: Q_B.copy(), 36),
    (648, lambda: Q_B + VS * 0.13 + UPV * 0.035, lambda: Q_B.lerp(fbpos(648), 0.5), 36),
    (690, lambda: Q_B + VS * 0.38 + UPV * 0.07, lambda: Q_B.lerp(eyes(690), 0.40), 28),
    (B_FING, lambda: S_A + VS * 0.36 + UPV * 0.06, lambda: S_A.lerp(eyes(B_FING), 0.40), 28),
    (840, lambda: fbpos(840) + VS2 * 0.36 + UPV * 0.05, lambda: fbpos(840).lerp(eyes(840), 0.40), 28),
    (B_NECK, lambda: N_B + VS3 * 0.40 + UPV * 0.04, lambda: N_B.lerp(eyes(B_NECK), 0.45), 28),
    (950, lambda: P(0.42, -0.70, 1.55), lambda: eyes(950).lerp(Wh(OW, "wrist.L"), 0.3), 30),
    (B_DENT, lambda: P(0.40, -0.82, 1.50), lambda: eyes(B_DENT).lerp(ring_w(B_DENT), 0.5), 30),
    (1060, lambda: P(0.14, -0.92, 1.50), lambda: eyes(1060).lerp(ring_w(1060), 0.45), 30),
    (1110, lambda: P(-0.15, -1.00, 1.55), lambda: eyes(1110).lerp(ring_w(1110), 0.4), 28),
    (B_WALK, lambda: P(0.10, -1.60, 1.72), lambda: eyes(B_WALK) + P(0, 0, -0.32), 26),
    (1280, lambda: P(0.34, -2.45, 1.74), lambda: eyes(1280) + P(0, 0, -0.34), 26),
    (END, lambda: P(0.48, -3.02, 1.75), lambda: eyes(END) + P(0, 0, -0.30), 26),
]
def look_q(p, a, up=Vector((0, 0, 1))):
    zc_ = (p - a).normalized(); yc = (up - zc_ * up.dot(zc_)); yc = yc.normalized() if yc.length > 1e-6 else Vector((0, 1, 0))
    xc = yc.cross(zc_); return Matrix((xc, yc, zc_)).transposed().to_quaternion()
ks = [(f, pf(), af(), l) for f, pf, af, l in K]
fx = [pchip([(k[0], k[1][i]) for k in ks]) for i in range(3)]
ax = [pchip([(k[0], k[2][i]) for k in ks]) for i in range(3)]
fl = pchip([(k[0], k[3]) for k in ks])
prev = None
for f in range(1, END + 1):
    p = Vector([fx[i](f) for i in range(3)]); a_ = Vector([ax[i](f) for i in range(3)]); q = look_q(p, a_)
    if prev is not None and prev.dot(q) < 0: q = -q
    prev = q
    CAM.location = p; CAM.rotation_quaternion = q; cam_d.lens = fl(f)
    CAM.keyframe_insert("location", frame=f); CAM.keyframe_insert("rotation_quaternion", frame=f); cam_d.keyframe_insert("lens", frame=f)
set_interp(CAM, 'LINEAR'); set_interp(cam_d, 'LINEAR')
# catchlight riding with the camera (eyes never read as black holes), scaled with distance
cl = bpy.data.lights.new("Catch", 'AREA'); cl.energy = 3.0; cl.size = 0.25; cl.color = (1, 0.95, 0.9)
clo = bpy.data.objects.new("Catchlight", cl); bpy.context.scene.collection.objects.link(clo); clo.parent = CAM; clo.location = (0.0, 0.10, 0.0)
for f in list(range(1, END + 1, 6)) + [END]:
    fs(f); d_ = (CAM.matrix_world.translation - eyes(f)).length
    cl.energy = max(0.05, min(3.0, 3.0 * (d_ / 1.0) ** 2)); cl.keyframe_insert("energy", frame=f)

# ================================================================== VO, output
sc.frame_start, sc.frame_end = 1, END
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor; strips = se.strips if hasattr(se, "strips") else se.sequences
strips.new_sound("VO", VO, 1, 1)
sc.render.filepath = "//render/RingBullet_v009_####.png"; sc.render.image_settings.file_format = 'PNG'
for o in O:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = False
log("quat flips fixed", quat_continuity(OW), quat_continuity(RB))
json_out = {"P_IMP": list(P_IMP), "Q_B": list(Q_B), "N_B": list(N_B), "S_A": list(S_A), "M0": list(M0)}
import json
open(os.path.join(os.path.dirname(OUT), "anchors_points.json"), "w").write(json.dumps(json_out))
sc.frame_set(1)
open(os.path.join(os.path.dirname(OUT), "animate_log.txt"), "w").write("\n".join(LOG))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("ANIM_DONE", OUT)
