"""Animation + the single continuous camera.  blender -b work/sets.blend -P 04_anim.py -- <out.blend>"""
import bpy, bmesh, sys, os, math, json, random
import numpy as np
from mathutils import Vector, Matrix, Euler, Quaternion
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
exec(open(os.path.join(HERE, "..", "pipeline", "anim_lib.py")).read())
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; OB = bpy.data.objects; R_ = math.radians
random.seed(11)
FPS = 60
BEATS = [(1, 0.0, "A stick swung down and smashed"), (2, 1.7, "right into the toucan's upper beak"), (3, 4.7, "every time it tried to eat"),
         (4, 8.9, "rescuers scanned the broken stump"), (5, 11.3, "compared it to another toucan's beak"),
         (6, 14.1, "rebuild the missing half on a computer"), (7, 17.7, "But the new beak couldn't be too heavy"),
         (8, 22.5, "So they made it full-size, but almost hollow"), (9, 25.2, "rescuers lined it up with the broken stump"),
         (10, 28.4, "glued the base into place, and fixed the rest with a pin"), (11, 33.0, "the toucan could pick up fruit again")]
BF = {b: 1 + round(t * FPS) for b, t, _ in BEATS}
json.dump([{"beat": b, "frame": BF[b], "first_words": w} for b, t, w in BEATS], open(os.path.join(HERE, "beats.json"), "w"), indent=1)
TZ = sc["TABLE_Z"]
C_ANIM = bpy.data.collections.new("Anim"); sc.collection.children.link(C_ANIM)

def key_vis(o, frames_states):
    """[(frame, visible_bool)] constant interpolation on hide_render/hide_viewport"""
    for f, v in frames_states:
        o.hide_render = not v; o.keyframe_insert("hide_render", frame=f)
        o.hide_viewport = not v; o.keyframe_insert("hide_viewport", frame=f)
def constant(o):
    if o.animation_data and o.animation_data.action:
        for fc in fcurves(o):
            for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
def fcurves(o):
    act = o.animation_data.action
    try:
        return list(act.fcurves)
    except Exception:
        res = []
        for layer in act.layers:
            for st in layer.strips:
                for cb in st.channelbags: res += list(cb.fcurves)
        return res
def key_loc(o, f, loc, rot=None):
    o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None:
        o.rotation_euler = rot; o.keyframe_insert("rotation_euler", frame=f)

# ================================================================== BIRD
rig = OB["ToucanRig"]; P = rig.pose.bones
for pb in P: pb.rotation_mode = 'XYZ'
def bk(bone, f, rx=0, ry=0, rz=0):
    pb = P[bone]; pb.rotation_euler = (R_(rx), R_(ry), R_(rz)); pb.keyframe_insert("rotation_euler", frame=f, group=bone)
def pose(f, **kw):
    """pose(f, head=(rx,ry,rz), neck=..., ...) ; unspecified bones -> rest"""
    for b in ("body", "chest", "neck", "head", "tail", "wing.L", "wing.R", "jaw"):
        bk(b, f, *kw.get(b.replace(".", "_"), (0, 0, 0)))
# placement: jungle perch -> clinic table (528) -> enclosure platform (1976)
dg = bpy.context.evaluated_depsgraph_get()
def top_z(obj, x, y, z0=5.0):
    o = obj.evaluated_get(dg); mi = o.matrix_world.inverted()
    hit, loc, n, i = o.ray_cast(mi @ Vector((x, y, z0)), (mi.to_3x3() @ Vector((0, 0, -1))).normalized())
    return (o.matrix_world @ loc).z if hit else None
def vtop(obj, x, y, r=0.03):
    M = np.array(obj.matrix_world); V = np.array([v.co[:] + (1,) for v in obj.data.vertices]) @ M.T
    s_ = (np.abs(V[:, 0] - x) < r) & (np.abs(V[:, 1] - y) < r)
    return float(V[s_, 2].max()) if s_.sum() else None
PERCH_Z = vtop(OB["Perch"], 0.05, -0.035) or 1.68
print("PERCH_Z", PERCH_Z)
BIRD_J = Vector((0.05, -0.035, PERCH_Z - 0.006))
BIRD_C = Vector((7.0, -0.02, TZ + 0.012)); ROT_C = (0, 0, R_(90))   # faces -x (toward the window)
_po = OB["Feeding_platform"]; plat_top = max((_po.matrix_world @ v.co).z for v in _po.data.vertices)
_pc = sum((_po.matrix_world @ v.co for v in _po.data.vertices), Vector()) / len(_po.data.vertices)
print("PLAT_TOP", plat_top, _pc)
BIRD_E = Vector((_pc.x - 0.04, _pc.y - 0.11, plat_top)); ROT_E = (0, 0, R_(0))
rig.rotation_mode = 'XYZ'
for f, p, r in ((1, BIRD_J, (0, 0, R_(0))), (527, BIRD_J, (0, 0, 0)), (528, BIRD_C, ROT_C), (1975, BIRD_C, ROT_C), (1976, BIRD_E, ROT_E)):
    key_loc(rig, f, p, r)
constant(rig)
# beak states
UP, UPB, LOW = OB["Toucan_beak_upper"], OB["Toucan_beak_upper_broken"], OB["Toucan_beak_lower"]
LB_base, LB_tip = Vector(UP["base"]), Vector(UP["tip"])
key_vis(UP, [(1, True), (104, False), (1976, True)])
key_vis(UPB, [(1, False), (104, True), (1976, False)])
# prosthetic: full upper beak copy (printed + painted), parented to head, slides on 1600-1690
PRO = bpy.data.objects.new("Prosthetic_beak", UP.data.copy()); C_ANIM.objects.link(PRO)
pm = UP.data.materials[0].copy(); pm.name = "Prosthetic_paint"
for nd in pm.node_tree.nodes:
    if nd.type == 'BSDF_PRINCIPLED': nd.inputs["Roughness"].default_value = 0.22; nd.inputs["Coat Weight"].default_value = 0.8
PRO.data.materials[0] = pm
axis_r = (LB_tip - LB_base).normalized()
key_vis(PRO, [(1, False), (528, True), (1976, False)])

def beak_point(frac, f=None, obj=None):
    if f is not None: ev(f)
    o = obj or UP
    return o.matrix_world @ (LB_base + (LB_tip - LB_base) * frac + Vector((0, 0, 0.0)))
def head_world(f):
    ev(f); return rig.matrix_world @ P["head"].tail

# ---- beat 1-3 acting (jungle)
pose(1, head=(0, 0, 10)); pose(30, head=(4, 0, 22), tail=(3, 0, 0)); pose(62, head=(-4, 0, -12), neck=(3, 0, 0))
pose(88, head=(2, 0, -4), neck=(0, 0, 0))
pose(102, head=(-4, 0, -2))
pose(108, head=(-34, -10, -22), neck=(-14, 0, -6), chest=(-10, 0, 0), body=(-6, 0, 0), wing_L=(0, 0, -30), wing_R=(0, 0, 30), tail=(18, 0, 0))
pose(128, head=(-42, -14, -30), neck=(-18, 0, -8), chest=(-14, 0, 0), body=(-8, 0, 0), wing_L=(-10, 0, -55), wing_R=(-10, 0, 55), tail=(25, 0, 0), jaw=(-14, 0, 0))
pose(165, head=(-12, 0, -18), neck=(-6, 0, 0), chest=(-4, 0, 0), wing_L=(0, 0, -20), wing_R=(0, 0, 20), tail=(8, 0, 0), jaw=(-6, 0, 0))
pose(195, head=(6, 0, 18), neck=(4, 0, 0))
for i, f in enumerate(range(205, 275, 10)):
    pose(f, head=(4, 8 * (-1) ** i, 26 * (-1) ** i), neck=(2, 0, 6 * (-1) ** i), tail=(6 * (-1) ** i, 0, 0))
pose(290, head=(-6, 0, 0))
pose(312, head=(14, 0, 0), neck=(8, 0, 0), chest=(4, 0, 0))                    # anticipation
pose(324, head=(-24, 0, 0), neck=(-26, 0, 0), chest=(-12, 0, 0), jaw=(-14, 0, 0))   # lunge 1
pose(346, head=(4, 0, 6), neck=(2, 0, 0), jaw=(0, 0, 0))
pose(362, head=(12, 0, -4), neck=(6, 0, 0))
pose(376, head=(-28, 0, 4), neck=(-28, 0, 0), chest=(-14, 0, 0), jaw=(-16, 0, 0))   # lunge 2
pose(398, head=(-30, 0, -6), neck=(-26, 0, 0), chest=(-12, 0, 0), jaw=(-4, 0, 0))   # watches it fall
for i, f in enumerate(range(418, 512, 9)):
    pose(f, head=(-2 + 6 * (i % 2), 10 * (-1) ** i, 30 * (-1) ** i), neck=(0, 0, 8 * (-1) ** i), chest=(0, 0, 4 * (-1) ** i),
         wing_L=(0, 0, -8 * (i % 2)), wing_R=(0, 0, 8 * (i % 2)), tail=(10 * (-1) ** i, 0, 0))
pose(520, head=(0, 0, 0))
# ---- clinic (held, small breaths/looks)
FE = OB["Fig_enclosure"]
for k, f in enumerate(range(540, 1960, 60)):
    pose(f, head=(-6 + 3 * (k % 2), 0, 6 * math.sin(k * 1.3) if not (1560 < f < 1950) else 0), chest=(2 * (k % 2), 0, 0))
pose(1960, head=(0, 0, 0))
# ---- enclosure: grab fig, toss, catch, swallow
pose(1985, head=(0, 0, 12)); pose(2004, head=(10, 0, 0), neck=(6, 0, 0))
pose(2026, head=(-46, 0, 0), neck=(-30, 0, 0), chest=(-24, 0, 0), body=(-8, 0, 0), jaw=(-12, 0, 0))
pose(2036, head=(-48, 0, 0), neck=(-30, 0, 0), chest=(-24, 0, 0), body=(-8, 0, 0), jaw=(-3, 0, 0))   # grip
pose(2064, head=(4, 0, 0), neck=(4, 0, 0), jaw=(-3, 0, 0))
pose(2080, head=(24, 0, 0), neck=(10, 0, 0), jaw=(-3, 0, 0))     # toss
pose(2086, head=(30, 0, 0), neck=(12, 0, 0), jaw=(-22, 0, 0))
pose(2104, head=(34, 0, 0), neck=(14, 0, 0), jaw=(-20, 0, 0))    # catch
pose(2112, head=(36, 0, 0), neck=(14, 0, 0), jaw=(-2, 0, 0))
pose(2140, head=(46, 0, 0), neck=(18, 0, 0), chest=(6, 0, 0))    # swallow
pose(2175, head=(2, 0, 10), tail=(10, 0, 0)); pose(2215, head=(-4, 0, -14)); pose(2250, head=(0, 0, -6))

# ---- prosthetic: follows the (hidden) intact upper beak's head-bone pose, slid out along the beak axis until seated at 1692
pro_off = pchip([(1515, 0.09), (1560, 0.09), (1600, 0.05), (1660, 0.008), (1692, 0.0), (1980, 0.0)])
PRO.rotation_mode = 'QUATERNION'
# table rest pose: upright on its cutting edge on the exam table, at VetB's right hand
_R = Matrix.Rotation(R_(70), 4, 'Z') @ Matrix.Translation(-(LB_base + LB_tip) / 2)
_zmin = min((_R @ v.co).z for v in UP.data.vertices)
PRO_TABLE = Matrix.Translation(Vector((6.70, 0.30, sc["TABLE_Z"] - _zmin + 0.001))) @ _R
def pro_seat(f):
    # UP is hidden (not evaluated) 104-1976, so its matrix_world is stale: rebuild its bone-parented world matrix from the head bone
    ev(f); _tr = UP.parent; _pb = _tr.pose.bones[UP.parent_bone]
    M = _tr.matrix_world @ _pb.matrix @ Matrix.Translation((0, _pb.bone.length, 0)) @ UP.matrix_parent_inverse @ UP.matrix_basis
    axw = (M.to_3x3() @ axis_r).normalized()
    o_ = pro_off(f); return Matrix.Translation(axw * o_ + Vector((0, 0, 0.004 if o_ > 0 else 0))) @ M
def mlerp(A, B, t):
    la, qa, sa = A.decompose(); lb, qb, sb = B.decompose()
    return Matrix.LocRotScale(la.lerp(lb, t), qa.slerp(qb, t), sa.lerp(sb, t))
for f in [528, 1508] + list(range(1510, 1980, 2)):
    if f <= 1510: M = PRO_TABLE
    elif f < 1560:
        t = smooth((f - 1510) / 50.0); lift = Matrix.Translation(Vector((0, 0, 0.12 * math.sin(math.pi * t))))
        M = lift @ mlerp(PRO_TABLE, pro_seat(1560), t)
    else:
        M = pro_seat(f)
    if True:
        loc, q, sc_ = M.decompose(); PRO.location = loc; PRO.rotation_quaternion = q; PRO.scale = sc_
        PRO.keyframe_insert("location", frame=f); PRO.keyframe_insert("rotation_quaternion", frame=f); PRO.keyframe_insert("scale", frame=f)

# ---- the stick (swing plane = bird's side; contact on the upper beak at frame 102)
stick = OB["Strike_stick"]; pivot = bpy.data.objects.new("Stick_pivot", None); C_ANIM.objects.link(pivot)
ev(100)
HIT = beak_point(0.45)
PV = HIT + Vector((0.0, -0.26, 0.97)).normalized() * 1.42   # held end far above/behind, always outside the frame
pivot.location = PV; stick.parent = pivot; stick.location = (0, 0, 0)
d0 = (HIT - PV).normalized()
base_q = Vector((0, 0, -1)).rotation_difference(d0)    # stick local +z points from pivot outward? our mesh runs z -0.05..0.9 -> use -z? fix below
# stick mesh runs from pivot along +z; we want +z -> d0
base_q = Vector((0, 0, 1)).rotation_difference(d0)
pivot.rotation_mode = 'QUATERNION'
def stick_ang(f, a):
    pivot.rotation_quaternion = Quaternion(Vector((1, 0, 0)), R_(a)) @ base_q; pivot.keyframe_insert("rotation_quaternion", frame=f)
for f, a in ((1, -95), (30, -80), (60, -48), (85, -18), (102, 0), (108, 3), (124, -12), (150, -45), (190, -85), (240, -110), (300, -120)):
    stick_ang(f, a)
key_vis(stick, [(1, True), (300, False)])
# tip piece + shards: fly from the beak in slow motion (time scale 0.3 until 220)
pieces = [OB["Beak_tip_piece"]] + [OB["Beak_shard_%d" % i] for i in range(9) if ("Beak_shard_%d" % i) in OB]
ev(104)
GROUND_Y = None
for k, pc in enumerate(pieces):
    rest = pc.matrix_world.copy()
    w0 = rig.matrix_world @ P["head"].matrix @ P["head"].bone.matrix_local.inverted() @ rest   # world at impact (follows head pose)
    pc.parent = None; pc.matrix_world = w0
    p0 = w0.translation.copy(); pc.rotation_mode = 'XYZ'; e0 = w0.to_euler()
    v = Vector((random.uniform(-0.25, 0.25), random.uniform(0.35, 0.9), random.uniform(0.1, 0.9))) * (0.6 if k == 0 else 1.0)
    spin = Vector((random.uniform(-18, 18), random.uniform(-18, 18), random.uniform(-18, 18)))
    gz = top_z(OB["Ground"], p0.x, p0.y) or 0.0
    t = 0.0; f = 104; landed = False
    while f <= 330:
        dt = (1 / FPS) * (0.28 if f < 230 else 1.0)
        if not landed:
            t += dt
            p = p0 + v * t + Vector((0, 0, -4.9 * t * t))
            if p.z < gz + 0.01: p.z = gz + 0.01; landed = True
            e = Euler((e0.x + spin.x * t, e0.y + spin.y * t, e0.z + spin.z * t))
        key_loc(pc, f, p, e); f += 2
    key_vis(pc, [(1, False), (104, True), (528, False)])
# fig hanging on a twig in front of the bird
ev(376)
stub_tip_lunge = beak_point(0.43, obj=UPB)
FIG = OB["Fig"]; TWIG = OB["Fig_twig"]
fpiv = bpy.data.objects.new("Fig_pivot", None); C_ANIM.objects.link(fpiv)
FIG0 = stub_tip_lunge + Vector((0, 0.03, -0.004))
fpiv.location = FIG0 + Vector((0, 0, 0.42))
TWIG.parent = fpiv; TWIG.location = (0, 0, -0.21); TWIG.rotation_euler = (0, 0, 0); TWIG.scale = (1, 1, 1)
FIG.parent = fpiv; FIG.location = (0, 0, -0.42 - 0.012)
fpiv.rotation_mode = 'XYZ'
for f, a in ((1, 0), (320, 0), (326, 18), (338, -10), (350, 6), (362, -3), (372, 0), (378, 24), (390, -14), (404, 8), (420, -4), (440, 2), (470, 0)):
    fpiv.rotation_euler = (R_(-a), 0, 0); fpiv.keyframe_insert("rotation_euler", frame=f)
for f, a in ((1, 0), (60, 2), (140, -3), (220, 2)):
    fpiv.rotation_euler = (R_(a), 0, 0); fpiv.keyframe_insert("rotation_euler", frame=f) if f < 300 else None
# second slip: fig drops off at 392 and falls to the leaves
ev(392); fw = FIG.matrix_world.copy()
FIG_FALL = bpy.data.objects.new("Fig_fall", FIG.data); C_ANIM.objects.link(FIG_FALL)
gz = top_z(OB["Ground"], fw.translation.x, fw.translation.y) or 0.0
for f in range(392, 470, 2):
    t = (f - 392) / FPS; p = fw.translation + Vector((0, 0.15 * t, -4.9 * t * t)); p.z = max(p.z, gz + 0.025)
    key_loc(FIG_FALL, f, p, (t * 6, t * 2, 0))
key_vis(FIG_FALL, [(1, False), (392, True), (528, False)])
key_vis(FIG, [(1, False), (262, True), (392, False)])
key_vis(TWIG, [(1, False), (262, True), (528, False)])

# background toucan (second bird, static copy) on the far perch, head bob = life
bg = bpy.data.objects.new("BG_toucan", None); C_ANIM.objects.link(bg)
for n in ("Toucan_body", "Toucan_beak_upper", "Toucan_beak_lower", "Toucan_eye.L", "Toucan_eye.R", "Toucan_eyeskin.L", "Toucan_eyeskin.R"):
    src = OB[n]; c = bpy.data.objects.new("BG_" + n, src.data); C_ANIM.objects.link(c); c.parent = bg
    ev(1); c.matrix_parent_inverse = Matrix(); c.matrix_basis = rig.matrix_world.inverted() @ src.matrix_world if n != "Toucan_body" else Matrix()
bpz = top_z(OB["Perch_bg"], -3.3, -2.0) or 3.1
bg.location = (-3.3, -2.0, bpz); bg.rotation_euler = (0, 0, R_(140))
for f in range(1, 560, 40):
    bg.rotation_euler = (R_(random.uniform(-4, 4)), 0, R_(140 + random.uniform(-25, 25))); bg.keyframe_insert("rotation_euler", frame=f)

# ---- enclosure fig: on the platform -> gripped in the beak tip -> tossed -> caught -> swallowed
FE.parent = None; FE.rotation_mode = 'XYZ'
ev(2036); grip0 = beak_point(0.9)
fig_rest = Vector((grip0.x, grip0.y, plat_top + 0.024))
key_loc(FE, 1, fig_rest, (0, 0, 0)); key_loc(FE, 2030, fig_rest, (0, 0, 0))
for f in range(2036, 2082, 2):
    key_loc(FE, f, beak_point(0.9, f) + Vector((0, 0, -0.012)), (0, 0, 0))
ev(2082); p0 = beak_point(0.9) + Vector((0, 0, -0.012)); ev(2104); p1 = beak_point(0.55) + Vector((0, 0, -0.01))
T = (2104 - 2082) / FPS; vz = (p1.z - p0.z + 4.9 * T * T) / T
for f in range(2082, 2106, 2):
    t = (f - 2082) / FPS; p = p0.lerp(p1, t / T); p.z = p0.z + vz * t - 4.9 * t * t
    key_loc(FE, f, p, (t * 9, t * 3, 0))
for f in range(2106, 2136, 2):
    key_loc(FE, f, beak_point(0.25 - 0.006 * (f - 2106), f) + Vector((0, 0, -0.01)), (2, 0.6, 0))
key_vis(FE, [(1, False), (1976, True), (2136, False)])

# ================================================================== PEOPLE (clinic)
def ground_z(x, y): return 0.0
people = {}
for nm in ("VetA", "VetB", "Assist"):
    r = make_human_ctrl(OB[nm]); people[nm] = Human(r)
VA, VB, AS = people["VetA"], people["VetB"], people["Assist"]
# hands rule: joint limits (local space) on fingers / thumbs / wrists; wrist copy-rotation softened (full influence twisted
# the wrist into a "balloon" candy-wrapper, found in the C close-ups)
for nm in ("VetA", "VetB", "Assist"):
    for s_ in "LR":
        for c in OB[nm].pose.bones["wrist." + s_].constraints:
            if c.type == 'COPY_ROTATION': c.influence = 1.0   # full hand orientation; hand_poses.add_hand_limits clamps the wrist (director, Nov 12 16:18)
for nm in ("VetA", "VetB", "Assist"):
    for pb in OB[nm].pose.bones:
        n = pb.name
        if n.startswith("finger") and "-" in n:
            c = pb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'; c.use_limit_x = c.use_limit_y = c.use_limit_z = True
            if n.startswith("finger1"): c.min_x, c.max_x, c.min_y, c.max_y, c.min_z, c.max_z = R_(-10), R_(60), R_(-30), R_(30), R_(-30), R_(30)
            else: c.min_x, c.max_x, c.min_y, c.max_y, c.min_z, c.max_z = R_(0), R_(90), R_(-5), R_(5), R_(-10), R_(10)
        elif n.startswith("wrist."):
            c = pb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'; c.use_limit_x = c.use_limit_z = True
            c.min_x, c.max_x, c.min_z, c.max_z = R_(-60), R_(60), R_(-25), R_(25)
def stand(H, f, pos, yaw, flex=8, head=(10, 0), spine_flex=14, twist=0):
    H.key_root(f, Vector((pos[0], pos[1], H.root_head.z - 0.02)), yaw=yaw, flex=flex)
    H.key_spine(f, flex=spine_flex, twist=twist, head=head)
    for s in "LR": H.key_foot(s, f, H.foot_xy(s, Vector(pos), yaw), yaw)
def yaw_of_xy(v): return math.degrees(math.atan2(v.x, -v.y))
def grip_key(H, s_, f, G, d, n, pole, reach=0.07, palm=0.03):
    """wrist target so the palm sits on G: fingers along d (wrapping), palm facing n"""
    d = d.normalized(); n = (n - d * n.dot(d)).normalized()
    H.key_hand(s_, f, G - d * reach - n * palm, d, n, pole=pole)
ev(600)
def bw(local):     # bird-space (rest) point -> world, clinic placement
    return Matrix.Translation(BIRD_C) @ Euler(ROT_C).to_matrix().to_4x4() @ Vector(local)
A_POS, B_POS = (7.02, -0.6), (6.98, 0.58)
for f in (530, 900, 1400, 1960):
    stand(VA, f, A_POS, 180, flex=6, head=(14, 0), spine_flex=8)
for f in (530, 700, 1500, 1960):
    stand(VB, f, B_POS, 0, flex=8, head=(18, 0), spine_flex=10)
# VetA cradles the bird the whole clinic stay
for f in (530, 1000, 1500, 1960):
    pass
    pass
# scanner sweeping (VetB right hand), beat 4
SCN = OB["Scanner"]; SCN.rotation_mode = 'QUATERNION'
stub_mid = bw(LB_base + (LB_tip - LB_base) * 0.25)
for f, dx in ((528, 0.06), (540, 0.06), (575, -0.04), (610, 0.05), (645, -0.05), (680, 0.02)):
    S = stub_mid + Vector((dx - 0.1, 0.12, 0.13))
    q = (stub_mid - S).to_track_quat('Y', 'Z')
    key_loc(SCN, f, S); SCN.rotation_quaternion = q; SCN.keyframe_insert("rotation_quaternion", frame=f)
    G = S + q @ Vector((0, -0.02, -0.11))
    grip_key(VB, "R", f, G, q @ Vector((-1, 0, 0)), q @ Vector((0, 1, 0)), pole=G + Vector((0.35, 0.35, -0.25)), reach=0.06, palm=0.035)
    VB.key_hand("L", f, Vector((7.38, 0.18, TZ + 0.02)), Vector((0, -1, 0)), Vector((0, 0, -1)), pole=Vector((7.6, 0.8, 1.0)))
VB.key_hand("R", 696, Vector((6.86, 0.12, TZ + 0.46)), Vector((0, -1, -0.3)), Vector((0, 0, -1)), pole=Vector((7.2, 0.9, 1.2)))
VB.key_hand("R", 712, Vector((6.62, 0.22, TZ + 0.2)), Vector((0, -1, -0.3)), Vector((0, 0, -1)), pole=Vector((6.3, 0.9, 1.2)))
SCN_REST = Vector((6.38, 0.2, TZ + 0.0335))   # clear of the tweezers/pin resting at (6.52, 0.3)      # put down on VetB's right, standing on its grip end (hand-driven below)
for f in (760, 1500):
    VB.key_hand("R", f, Vector((6.6, 0.16, TZ + 0.03)), Vector((0, -1, 0)), Vector((0, 0, -1)), pole=Vector((6.3, 0.8, 1.0)))
    VB.key_hand("L", f, Vector((7.38, 0.18, TZ + 0.03)), Vector((0, -1, 0)), Vector((0, 0, -1)), pole=Vector((7.6, 0.8, 1.0)))
# laser line: narrow red spot projected from the scanner lens onto the stump
las = bpy.data.objects.new("Laser_spot", bpy.data.lights.new("Laser_spot", 'SPOT')); C_ANIM.objects.link(las)
las.data.energy = 6; las.data.color = (1, 0.04, 0.02); las.data.spot_size = R_(28); las.data.spot_blend = 0.0; las.data.shadow_soft_size = 0
las.parent = SCN; las.location = (0, 0.03, 0); las.rotation_euler = (R_(-90), 0, 0); las.scale = (1, 0.02, 1)
OB["Laser_line"].hide_render = True
key_vis(las, [(1, False), (538, True), (690, False)])
# prosthetic in VetB's hand (1515-1692): hand follows the prosthetic
VB.key_hand("R", 1503, Vector((6.68, 0.24, TZ + 0.12)), Vector((0, -1, -0.3)), Vector((0, 0, -1)), pole=Vector((6.3, 0.9, 1.2)))
PRO_D = Vector((0, -1, -0.6)).normalized(); PRO_N = Vector((0, 0, -1))   # pinch over the top: fingers wrap the far flank, thumb on the near flank
def pro_grip_pt(f):
    ev(f); return PRO.matrix_world @ (LB_base + (LB_tip - LB_base) * 0.5 + Vector((0, 0, 0.012)))
for f in list(range(1508, 1693, 6)):
    pw = pro_grip_pt(f)
    grip_key(VB, "R", f, pw, PRO_D, PRO_N, pole=pw + Vector((0.35, 0.35, -0.15)), reach=0.05, palm=0.016)
# glue syringe (left hand) 1704-1800, tweezers + pin (right) 1810-1950
SYR, TWZ, PIN = OB["Glue_syringe"], OB["Tweezers"], OB["Pin"]
seam = bw(LB_base + (LB_tip - LB_base) * 0.42 + Vector((0, 0.012, 0.02)))
_pw = pro_grip_pt(1692)
grip_key(VB, "R", 1693, _pw, PRO_D, PRO_N, pole=_pw + Vector((0.35, 0.35, -0.15)), reach=0.05, palm=0.016)
VB.key_hand("R", 1702, _pw + Vector((0.14, 0.04, 0.22)), Vector((0, -1, -0.3)), Vector((0, 0, -1)), pole=_pw + Vector((0.3, 0.5, 0.0)))
VB.key_hand("L", 1712, Vector((7.38, 0.18, TZ + 0.03)), Vector((0, -1, 0)), Vector((0, 0, -1)), pole=Vector((7.6, 0.8, 1.0)))
SYR.rotation_mode = 'QUATERNION'
SYR_AX = Vector((0, -1, -0.02)).normalized(); SYR_C = Vector((7.36, 0.18, TZ + 0.0095))
def syr_grip(f, C, ax, palm=0.03):
    grip_key(VB, "L", f, C, ax + Vector((0, 0, -0.35)), Vector((-0.3, 0, -1)), pole=C + Vector((0.3, 0.4, -0.2)), reach=0.07, palm=palm)   # pen grip from above: fingers along the barrel, thumb on its side
syr_grip(1717, SYR_C, SYR_AX, 0.065)                    # picks the syringe up off the table
VB.key_hand("L", 1721, Vector((7.3, -0.04, TZ + 0.36)), Vector((-0.2, -1, -0.6)), Vector((0, 0, -1)), pole=Vector((7.7, 0.7, 1.3)))
for f, s_ in ((1726, 0.1), (1744, 0.0), (1768, 0.0), (1792, 0.08)):
    p_ = seam + Vector((0.0, 0.04 + s_, 0.06)); q = (seam - p_).to_track_quat('Z', 'Y')
    ax_s = (seam - p_).normalized(); Gs = p_ - ax_s * 0.06
    grip_key(VB, "L", f, Gs, ax_s, Vector((-0.5, 0, -0.85)), pole=Gs + Vector((0.3, 0.4, -0.2)), reach=0.07, palm=0.03)   # pen grip, needle along the fingers
key_vis(SYR, [(1, False), (528, True), (1976, False)])
for f in (1712, 1800):
    VB.key_hand("R", f, Vector((6.62, 0.16, TZ + 0.03)), Vector((0, -1, 0)), Vector((0, 0, -1)), pole=Vector((6.3, 0.8, 1.0)))
VB.key_hand("L", 1797, Vector((7.3, 0.02, TZ + 0.34)), Vector((-0.2, -1, -0.6)), Vector((0, 0, -1)), pole=Vector((7.7, 0.7, 1.3)))
syr_grip(1803, SYR_C, SYR_AX, 0.065)                    # puts it back down where it was
for f in (1810, 1950):
    VB.key_hand("L", f, Vector((7.38, 0.18, TZ + 0.03)), Vector((0, -1, 0)), Vector((0, 0, -1)), pole=Vector((7.6, 0.8, 1.0)))
pin_in = bw(LB_base + (LB_tip - LB_base) * 0.36 + Vector((0, 0.0, 0.03)))
PIN_REST = Vector((6.52, 0.3, TZ + 0.006))
def twz_grip(f, p_):
    grip_key(VB, "R", f, p_ + Vector((0, 0.075, 0.006)), Vector((0, -1, -0.15)), Vector((0, 0, -1)), pole=p_ + Vector((0.3, 0.4, -0.2)), reach=0.055, palm=0.022)
twz_grip(1807, PIN_REST)                           # picks up the tweezers (pin held in the tips)
for f, d_ in ((1810, 0.08), (1850, 0.02), (1880, 0.008), (1910, 0.0), (1945, 0.0)):
    p_ = pin_in + Vector((0, d_, 0.01 + d_ * 0.5))
    grip_key(VB, "R", f, p_ + Vector((0, 0.075, 0.006)), Vector((0, -1, -0.15)), Vector((0, 0, -1)), pole=p_ + Vector((0.3, 0.4, -0.2)), reach=0.055, palm=0.022)
key_vis(PIN, [(1, False), (528, True), (1976, False)]); key_vis(TWZ, [(1, False), (528, True), (1976, False)])
VB.key_hand("R", 1950, pin_in + Vector((-0.14, 0.05, 0.16)), Vector((0, -1, -0.3)), Vector((0, 0, -1)), pole=pin_in + Vector((0.3, 0.5, 0.0)))
twz_grip(1962, PIN_REST)                           # tweezers back on the table
VB.key_hand("R", 1972, Vector((6.6, 0.16, TZ + 0.03)), Vector((0, -1, 0)), Vector((0, 0, -1)), pole=Vector((6.3, 0.8, 1.0)))
# glue bead along the seam (grows)
st_a = (LB_tip - LB_base).length * 0.42
VV = [v.co for o_ in (UPB, LOW) for v in o_.data.vertices]
sec = [v for v in VV if abs((v - LB_base).dot(axis_r) - st_a) < 0.003]
cy = sum((v.y for v in sec)) / len(sec); cz = (max(v.z for v in sec) + min(v.z for v in sec)) / 2
hz = (max(v.z for v in sec) - min(v.z for v in sec)) / 2 + 0.0012; hx = (max(v.x for v in sec) - min(v.x for v in sec)) / 2 + 0.0012
bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.035, major_segments=48, minor_segments=8, location=(0, 0, -30))
glue = bpy.context.active_object; glue.name = "Glue_bead"
for c in glue.users_collection: c.objects.unlink(glue)
C_ANIM.objects.link(glue)
# ring in bird rest space: axis along the beak axis, radii hx (sideways) and hz (vertical), then into clinic world
Mr = Matrix.Translation(Vector((0, cy, cz))) @ Vector((0, 0, 1)).rotation_difference(axis_r).to_matrix().to_4x4() @ Matrix.Diagonal((hx, hz, 0.02, 1))
glue.data.transform(Mr)
for v in glue.data.vertices: v.co.z += 0.0          # keep
glue.matrix_world = Matrix.Translation(BIRD_C) @ Euler(ROT_C).to_matrix().to_4x4()
glue.data.transform(Matrix.Diagonal((1, 1, 1, 1)))
gm = bpy.data.materials.new("Glue"); gm.use_nodes = True; gb = gm.node_tree.nodes["Principled BSDF"]
gb.inputs["Base Color"].default_value = (0.9, 0.88, 0.8, 1); gb.inputs["Roughness"].default_value = 0.05; gb.inputs["Transmission Weight"].default_value = 0.7
glue.data.materials.append(gm)
gm.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 1.0
key_vis(glue, [(1, False), (1736, True), (1976, False)])
bld = glue.modifiers.new("grow", 'BUILD'); bld.frame_start = 1736; bld.frame_duration = 34
# assistant: background walk (life)
# the assistant walks to the desk and works the mouse while the monitor shows the 3D beak (director note, 12 s)
AS_DESK = Vector((9.0, 1.95, 0))
AS.walk(lambda f: Vector((5.0, 2.15, 0)).lerp(AS_DESK, smooth((f - 560) / 100)), lambda f: yaw_of_xy(AS_DESK - Vector((5.0, 2.15, 0))) if f < 655 else 90, 560, 660, stride=0.72)
stand(AS, 672, (AS_DESK.x, AS_DESK.y), 90, head=(22, 0)); stand(AS, 1505, (AS_DESK.x, AS_DESK.y), 90, head=(22, 0)); stand(AS, 1520, (AS_DESK.x, AS_DESK.y), 90, head=(12, 0))
stand(AS, 1560, (AS_DESK.x, AS_DESK.y), 90, head=(18, 0))
_md = OB["desk"]; DESK_TOP = max((_md.matrix_world @ v.co).z for v in _md.data.vertices)
mouse = bpy.data.objects.new("Mouse", bpy.data.meshes.new("Mouse")); C_ANIM.objects.link(mouse)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(mouse.data); bm.free()
mouse.scale = (0.11, 0.062, 0.034); mouse.location = (9.45, 1.58, DESK_TOP + 0.017)
bv_ = mouse.modifiers.new("bv", 'BEVEL'); bv_.width = 0.45; bv_.segments = 5; bv_.limit_method = 'NONE'
mouse.modifiers.new("sub", 'SUBSURF').levels = 2
mouse.data.materials.append(bpy.data.materials["Scanner_plastic"]); [setattr(p_, "use_smooth", True) for p_ in mouse.data.polygons]
pad = bpy.data.objects.new("Mouse_pad", bpy.data.meshes.new("Mouse_pad")); C_ANIM.objects.link(pad)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(pad.data); bm.free()
pad.scale = (0.24, 0.2, 0.003); pad.location = (9.45, 1.58, DESK_TOP + 0.0015); pad.data.materials.append(bpy.data.materials["Towel"])
MTOP = Vector((9.44, 1.58, DESK_TOP + 0.036))
for f, dx in ((662, -0.15), (676, 0.0), (700, 0.012), (730, -0.01), (760, 0.008), (1505, 0.0)):
    grip_key(AS, "R", f, MTOP + Vector((dx, 0, 0.0 if dx > -0.1 else 0.08)), Vector((1, 0, -0.25)), Vector((0, 0, -1)), pole=Vector((AS_DESK.x - 0.1, AS_DESK.y - 0.5, 1.0)), reach=0.06, palm=0.025)
    if dx > -0.1: key_loc(mouse, f, Vector((9.45 + dx, 1.58, DESK_TOP + 0.017)))
AS.key_hand("L", 676, Vector((9.3, 2.1, DESK_TOP + 0.02)), Vector((1, 0, 0)), Vector((0, 0, -1)), pole=Vector((AS_DESK.x - 0.1, AS_DESK.y + 0.5, 1.0)))
# leaves the desk on a curved path: turns while stepping (no spin on the spot)
_P0, _C, _P2 = AS_DESK.copy(), Vector((8.55, 1.15, 0)), Vector((5.2, 2.15, 0))
def as_t(f): return smooth((f - 1566) / 254.0)
def as_path(f):
    t = as_t(f); return _P0 * (1 - t) ** 2 + _C * (2 * (1 - t) * t) + _P2 * t * t
def as_yaw(f):
    t = max(as_t(f), 0.02); tg = (_C - _P0) * (2 * (1 - t)) + (_P2 - _C) * (2 * t); y_ = yaw_of_xy(tg)
    k = smooth((f - 1566) / 30.0); y0 = 90.0
    d = ((y_ - y0 + 180) % 360) - 180
    return y0 + d * k
AS.walk(as_path, as_yaw, 1566, 1820, stride=0.68)
stand(AS, 1840, (5.2, 2.15), 180, head=(20, 0)); stand(AS, 1960, (5.2, 2.15), 180, head=(25, 10))
for nm in ("VetA", "VetB", "Assist"):
    o = OB[nm]
    for ch in [o] + list(o.children): key_vis(ch, [(1, False), (525, True), (1980, False)])

# finger articulation: grips (fingers curl around bird body / tools), thumbs oppose
def curl(H, side, f, amt, thumb=0.5, spread=0.0):
    for fi in range(1, 6):
        for seg in (1, 2, 3):
            n = "finger%d-%d.%s" % (fi, seg, side)
            if n not in H.r.PB: continue
            a = amt * (0.6 if seg == 1 else 1.0) * (thumb if fi == 1 else 1.0)
            q = Quaternion(Vector((1, 0, 0)), R_(a)) @ Quaternion(Vector((0, 0, 1)), R_(spread * (fi - 3) if seg == 1 else 0))
            H.r.PB[n].rotation_quaternion = q; H.r.PB[n].keyframe_insert("rotation_quaternion", frame=f, group=n)
# finger poses from the shared library (blender/pipeline/hand_poses.py): no hand-set finger angles
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("hand_poses", os.path.join(HERE, "..", "pipeline", "hand_poses.py")); HP = _ilu.module_from_spec(_spec); _spec.loader.exec_module(HP)
for _h in (VA, VB, AS): HP.add_hand_limits(_h.r.o)
def hpose(H, side, frames, name):
    for f in frames: HP.apply_pose(H.r.o, side, name, f)
hpose(VA, "L", (530, 1960), "flat_palm")              # steadying hand flat on the table
hpose(VA, "R", (530, 1960), "cup_hold")               # palm on the bird's back, fingers following its curve
hpose(VB, "R", (760, 1500), "relaxed")                # after the scanner is set down (held frames: closure pass below)
hpose(VB, "L", (530, 1500, 1712, 1806, 1960), "relaxed")
hpose(VB, "R", (1506,), "tripod")                     # pre-shape on the reach to the prosthetic
hpose(VB, "R", (1712, 1800), "relaxed")
hpose(VB, "L", (1715, 1805), "tripod")                # pre-shape before pick-up / after put-down of the syringe
hpose(AS, "L", (560, 1960), "relaxed"); hpose(AS, "R", (560, 1960), "relaxed")
hpose(AS, "R", (676, 1505), "cup_hold")              # hand over the mouse

# relaxed arms while walking / standing idle: hands hang at the thighs with a small counter-swing (no IK target left at the origin)
def arms_relaxed(H, f0, f1, step=4, swing=0.07, period=48.0):
    rig_ = H.r.o
    for f in list(range(f0, f1, step)) + [f1]:
        ev(f); M = rig_.matrix_world
        shL = M @ H.r.PB["upperarm01.L"].head; shR = M @ H.r.PB["upperarm01.R"].head
        side = (shL - shR); side.z = 0; side.normalize()          # points to the character's left
        fwd = Vector((0, 0, 1)).cross(side).normalized() * -1
        ph = math.sin(2 * math.pi * (f - f0) / period)
        for s_, sh, sgn in (("L", shL, 1), ("R", shR, -1)):
            W = sh + Vector((0, 0, -0.56)) + side * (0.05 * sgn) + fwd * (0.04 + swing * ph * sgn)
            H.key_hand(s_, f, W, Vector((0, 0, -1)) + fwd * 0.15, -side * sgn, pole=sh + Vector((0, 0, -0.3)) - fwd * 0.4)
arms_relaxed(AS, 556, 660)
AS.key_hand("L", 662, None, None, None) if False else None
arms_relaxed(AS, 1522, 1840)
arms_relaxed(AS, 1844, 1980, step=20, swing=0.0)

# faces (MPFB face bones): focused concentration while working, blinks, relief when the pin is in
def face(H, f, brow=-0.006, lid=-14, jaw=0.0, brow_y=0.0):
    PB_ = H.r.PB
    for s_ in "LR":
        for b_ in ("oculi01.", "oculi02."):
            pb = PB_[b_ + s_]; pb.location = (0, brow_y, brow); pb.keyframe_insert("location", frame=f)
        pb = PB_["orbicularis03." + s_]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R_(lid), 0, 0); pb.keyframe_insert("rotation_euler", frame=f)
    pb = PB_["jaw"]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R_(jaw), 0, 0); pb.keyframe_insert("rotation_euler", frame=f)
for H, ofs in ((VA, 0), (VB, 23), (AS, 41)):
    face(H, 530, -0.005, -12)
    face(H, 640, -0.007, -16); face(H, 1520, -0.006, -14); face(H, 1700, -0.008, -18); face(H, 1880, -0.008, -18)
    face(H, 1925, 0.003, -4, 4, 0.002); face(H, 1975, 0.002, -2, 2, 0.002)            # relief: brows lift, mouth softens
    for fb in range(560 + ofs, 1960, 170):                                                 # blinks
        if 760 < fb < 1500: continue
        face(H, fb, -0.006, -14); face(H, fb + 3, -0.006, -55); face(H, fb + 7, -0.006, -14)

# ---- props are moved only by hands: from pick-up to put-down each tool rides on the wrist bone that holds it
def follow(prop, rig_, side, f0, f1, rest_before=True, extra=()):
    bone = rig_.pose.bones["wrist." + side]; prop.rotation_mode = 'QUATERNION'
    ev(f0); Wm0 = rig_.matrix_world @ bone.matrix; P0 = prop.matrix_world.copy(); OFF = Wm0.inverted() @ P0
    xo = [(o, P0.inverted() @ o.matrix_world) for o in extra]
    for f in range(f0, f1 + 1, 2):
        ev(f); M = rig_.matrix_world @ bone.matrix @ OFF
        loc, q, sc_ = M.decompose(); prop.location = loc; prop.rotation_quaternion = q
        prop.keyframe_insert("location", frame=f); prop.keyframe_insert("rotation_quaternion", frame=f)
        for o, rel in xo:
            if f <= o["_until"]:
                Mo = M @ rel; lo, qo, _ = Mo.decompose(); o.rotation_mode = 'QUATERNION'; o.location = lo; o.rotation_quaternion = qo
                o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_quaternion", frame=f)
def rest_key(o, f, loc, q):
    o.rotation_mode = 'QUATERNION'; o.location = loc; o.rotation_quaternion = q
    o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_quaternion", frame=f)

# ---- settle VetA's cradling hands: push each wrist target away from the bird until the glove only touches (few overlaps)
from mathutils.bvhtree import BVHTree
def side_polys(o, side):
    vg = {g.index: g.name for g in o.vertex_groups}
    gi = [i for i, m in enumerate(o.data.materials) if m and m.name.startswith("Nitrile")]
    vs = set(v.index for v in o.data.vertices if any(vg.get(g.group, "").endswith("." + side) and g.weight > 0.3 for g in v.groups))
    return [p.index for p in o.data.polygons if p.material_index in gi and all(x in vs for x in p.vertices)]
def tri_tree(o, side=None):
    dg_ = bpy.context.evaluated_depsgraph_get(); ev_ = o.evaluated_get(dg_); me_ = ev_.to_mesh(); mw_ = o.matrix_world
    vs_ = [mw_ @ v.co for v in me_.vertices]
    if side is not None:
        gi = [i for i, m in enumerate(o.data.materials) if m and m.name.startswith("Nitrile")]
        wr = OB["VetA"].matrix_world @ OB["VetA"].pose.bones["wrist." + side].head
        wo = OB["VetA"].matrix_world @ OB["VetA"].pose.bones["wrist." + ("L" if side == "R" else "R")].head
        ps_ = [tuple(p.vertices) for p in me_.polygons if p.material_index in gi and (mw_ @ p.center - wr).length < 0.16 and (mw_ @ p.center - wr).length < (mw_ @ p.center - wo).length]
    else: ps_ = [tuple(p.vertices) for p in me_.polygons]
    ev_.to_mesh_clear(); return BVHTree.FromPolygons(vs_, ps_)
GA = OB["VetA.body"]
def deep_count(o, rig_, side, target, depth=0.012):
    """glove vertices of one hand deeper than `depth` inside `target` (nearest point + normal test)"""
    dg_ = bpy.context.evaluated_depsgraph_get(); ev_ = o.evaluated_get(dg_); me_ = ev_.to_mesh(); mw_ = o.matrix_world
    gi = [i for i, m in enumerate(o.data.materials) if m and m.name.startswith("Nitrile")]
    wr = rig_.matrix_world @ rig_.pose.bones["wrist." + side].head; wo = rig_.matrix_world @ rig_.pose.bones["wrist." + ("L" if side == "R" else "R")].head
    vids = set()
    for p in me_.polygons:
        if p.material_index in gi: vids.update(p.vertices)
    pts = [mw_ @ me_.vertices[i].co for i in vids]
    ev_.to_mesh_clear()
    pts = [q for q in pts if (q - wr).length < 0.16 and (q - wr).length < (q - wo).length]
    n = 0
    for q in pts:
        loc, nrm, _, d = target.find_nearest(q, 0.06)
        if loc is not None and depth < d < 0.06 and (q - loc).dot(nrm) < 0: n += 1
    return n
BODY_C = bw((0, -0.03, 0.14))
ev(600); _bt = tri_tree(OB["Toucan_body"]); _h = _bt.ray_cast(Vector((7.15, -0.055, 1.6)), Vector((0, 0, -1)), 0.8)
BACK = _h[0] if _h[0] is not None else Vector((7.08, -0.06, 1.12)); print("BACK", BACK)
_dB = Vector((0.5, 1, -0.45)).normalized()
_h2 = _bt.ray_cast(Vector((6.95, -0.4, TZ + 0.08)), Vector((0, 1, 0)), 0.6)
CHEST = _h2[0] if _h2[0] is not None else Vector((6.98, -0.07, TZ + 0.11)); print("CHEST", CHEST)
_dC = Vector((-0.75, 0.25, -0.6)).normalized()
HANDA = {"R": (lambda: BACK + Vector((0, 0, 0.024)) - _dB * 0.07, _dB, Vector((0, 0, -1)), Vector((A_POS[0] + 0.45, A_POS[1] - 0.15, 1.2))),
         "L": (lambda: Vector((6.78, -0.27, TZ + 0.03)), Vector((0.2, 1, -0.05)), Vector((0, 0, -1)), Vector((A_POS[0] - 0.5, A_POS[1] + 0.05, 0.85)))}   # steadying hand on the towel in front of the chest
for f in (530, 1000, 1500, 1960):
    for s_ in "LR":
        Wf, d_, n_, pole_ = HANDA[s_]; W = Wf()
        VA.key_hand(s_, f, W, d_, n_, pole=pole_)
        away = (W - BODY_C); away.normalize()
        if s_ == "R": away = Vector((0, -0.3, 1)).normalized()
        else: away = Vector((0, -1, 0.15)).normalized()
        for it in range(40):
            ev(f); bt_ = tri_tree(OB["Toucan_body"]); n = deep_count(GA, OB["VetA"], s_, bt_, depth=0.007)
            if n == 0: break
            W = W + away * 0.002
            VA.key_hand(s_, f, W, d_, n_, pole=pole_)
        print("SETTLE VetA", s_, f, "iters", it, "overlaps", n)

# ---- settle VetB's prosthetic grip: raise the palm off the held beak until only light contact remains
GB = OB["VetB.body"]
def glove_tree_side(o, rig, side):
    dg_ = bpy.context.evaluated_depsgraph_get(); ev_ = o.evaluated_get(dg_); me_ = ev_.to_mesh(); mw_ = o.matrix_world
    vs_ = [mw_ @ v.co for v in me_.vertices]
    gi = [i for i, m in enumerate(o.data.materials) if m and m.name.startswith("Nitrile")]
    wr = rig.matrix_world @ rig.pose.bones["wrist." + side].head
    wo = rig.matrix_world @ rig.pose.bones["wrist." + ("L" if side == "R" else "R")].head
    ps_ = [tuple(p.vertices) for p in me_.polygons if p.material_index in gi and (mw_ @ p.center - wr).length < 0.16 and (mw_ @ p.center - wr).length < (mw_ @ p.center - wo).length]
    ev_.to_mesh_clear(); return BVHTree.FromPolygons(vs_, ps_)
for f in list(range(1508, 1540, 2)) + list(range(1540, 1693, 6)) + [1693]:
    pw = pro_grip_pt(min(f, 1692)); palm = 0.016
    for it in range(14):
        ev(f); n = deep_count(GB, OB["VetB"], "R", tri_tree(PRO), depth=0.006)
        if n == 0: break
        palm += 0.004
        grip_key(VB, "R", f, pw, PRO_D, PRO_N, pole=pw + Vector((0.35, 0.35, -0.15)), reach=0.05, palm=palm)
    if f % 30 == 3: print("SETTLE VetB prosthetic", f, "palm", round(palm, 3), "overlaps", n)

# ---- tools ride on the hand that holds them (after all hand keys are final)
q_syr = SYR_AX.to_track_quat('Z', 'Y')
rest_key(SYR, 528, SYR_C + (-SYR_AX) * 0.0, q_syr); rest_key(SYR, 1717, SYR_C, q_syr)
SYR_ACT = [(f_, seam + Vector((0.0, 0.04 + s_, 0.06))) for f_, s_ in ((1726, 0.1), (1744, 0.0), (1768, 0.0), (1792, 0.08))]
adj = {f_: Vector() for f_, _ in SYR_ACT}
for it in range(4):
    for f_, p_ in SYR_ACT:
        ax_s = (seam - p_).normalized(); syr_grip(f_, seam - ax_s * 0.072 + adj[f_], ax_s)
    follow(SYR, OB["VetB"], "L", 1717, 1803)
    errs = []
    for f_, p_ in SYR_ACT:
        ev(f_); want = seam - (seam - p_).normalized() * 0.072; e = want - SYR.matrix_world.translation; adj[f_] += e; errs.append(e.length)
    print("SYR correction", it, [round(x, 3) for x in errs])
# finger regrip: the barrel rolls in the fingers about its grip point into a pen angle (needle tip on the seam), and back before the put-down
_bn = OB["VetB"].pose.bones["wrist.L"]
ev(1717); _OFF = (OB["VetB"].matrix_world @ _bn.matrix).inverted() @ SYR.matrix_world; _t0 = _OFF.translation.copy(); _q0 = _OFF.to_quaternion()
ev(1744); _qact = (OB["VetB"].matrix_world @ _bn.matrix).to_quaternion().inverted() @ (seam - SYR_ACT[1][1]).normalized().to_track_quat('Z', 'Y')
def _ss(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
for f in range(1717, 1804, 2):
    t = _ss((f - 1717) / 13) * (1 - _ss((f - 1790) / 13)); ev(f); W = OB["VetB"].matrix_world @ _bn.matrix
    SYR.location = W @ _t0; SYR.rotation_quaternion = W.to_quaternion() @ _q0.slerp(_qact, t)
    SYR.keyframe_insert("location", frame=f); SYR.keyframe_insert("rotation_quaternion", frame=f)
q_twz = Euler((0, 0, R_(90))).to_quaternion(); q_pin = Euler((R_(90), 0, 0)).to_quaternion()
TWZ_REST = PIN_REST + Vector((0, 0.065, 0.004))
rest_key(TWZ, 528, TWZ_REST, q_twz); rest_key(TWZ, 1807, TWZ_REST, q_twz)
rest_key(PIN, 528, PIN_REST, q_pin); rest_key(PIN, 1807, PIN_REST, q_pin)
PIN["_until"] = 1910
TWZ_ACT = [(f_, pin_in + Vector((0, d_, 0.01 + d_ * 0.5))) for f_, d_ in ((1810, 0.08), (1850, 0.02), (1880, 0.008), (1910, 0.0), (1944, 0.0))]
adj = {f_: Vector() for f_, _ in TWZ_ACT}
for it in range(4):
    for f_, p_ in TWZ_ACT: twz_grip(f_, p_ + adj[f_])
    rest_key(PIN, 1807, PIN_REST, q_pin)
    follow(TWZ, OB["VetB"], "R", 1807, 1962, extra=(PIN,))
    errs = []
    for f_, p_ in TWZ_ACT:
        ev(min(f_, 1910)); e = p_ - PIN.matrix_world.translation; adj[f_] += e; errs.append(e.length)
    print("PIN correction", it, [round(x, 3) for x in errs])
follow(SCN, OB["VetB"], "R", 680, 744)
rest_key(SCN, 746, SCN_REST + Vector((0, 0, 0.0)), Vector((0, 0, 1)).to_track_quat('Z', 'Y'))   # set down upright on the table (camera is inside the void)
for o_ in (SYR, TWZ, PIN, SCN):
    ev(1000 if o_ is SCN else 1975); print("TOOL", o_.name, [round(x, 3) for x in o_.matrix_world.translation])
# ---- fingers close onto every held tool, using hand_poses.py presets + its closure test (each finger stops at the
# first surface contact, the thumb opposes). The wrist placement stays the grip_key solve above (props ride on it).
def _closest_w(obj, p):
    ok, loc, nrm, idx = obj.closest_point_on_mesh(obj.matrix_world.inverted() @ p); return obj.matrix_world @ loc
def nudge_hand(rig, s, f, obj, grip):
    """like hand_poses.grip_object: move IK_hand so the pinch point (thumb+index tips) / the palm centre lands on obj's surface"""
    b = HP._b; pb = rig.pose.bones["IK_hand." + s]; Bm = rig.data.bones["IK_hand." + s].matrix_local.to_3x3().inverted()
    for _ in range(3):
        ev(f); Mw = rig.matrix_world; Hh = HP._Hand(rig, s)
        if grip == "pinch":
            F = Hh.fk(HP._pose_rots(rig, s, "pinch")); P = Mw @ ((F[b(1, 3, s)][1] + F[b(2, 3, s)][1]) / 2); T = _closest_w(obj, P)
        else:
            wr_, d_, n_, a_ = Hh.frame(); P = Mw @ (wr_ + d_ * 0.055 + n_ * 0.012); C = _closest_w(obj, P)
            T = C + (P - C).normalized() * 0.022 if (P - C).length > 1e-6 else C
        delta = T - P
        if delta.length < 0.002: break
        pb.location = pb.location + Bm @ (Mw.inverted().to_3x3() @ delta); pb.keyframe_insert("location", frame=f, group=pb.name)
def close_on(H, s, f, obj, grip):
    rig = H.r.o; nudge_hand(rig, s, f, obj, grip); ev(f); Mw = rig.matrix_world; Hh = HP._Hand(rig, s); b = HP._b
    rot = dict(HP._pose_rots(rig, s, "relaxed")); rep = {}
    if grip == "pinch":
        open_ = HP._pose_rots(rig, s, "open_alarm"); closed = HP._pose_rots(rig, s, "pinch"); rot.update(open_)
        for k in (3, 4, 5):
            for j in (1, 2, 3): rot[b(k, j, s)] = closed[b(k, j, s)]
        fingers = (2, 1)
    else:
        open_ = HP._pose_rots(rig, s, "shield"); closed = HP._pose_rots(rig, s, "power_fist"); rot.update(open_); fingers = HP.FING
    def touching(bones, Rq):
        F = Hh.fk(Rq)
        for bn in bones:
            h, t = F[bn]
            for u in (0.35, 0.7, 1.0):
                if HP._dist_to(obj, Mw @ h.lerp(t, u)) < 0.008: return True
        return False
    for k in fingers:
        chain = [b(k, j, s) for j in (1, 2, 3)]; probe = chain[1:] if k == 1 else chain; hit = None
        for i in range(41):
            u = i / 40; trial = dict(rot)
            for bn in chain: trial[bn] = open_[bn].slerp(closed[bn], u)
            if touching(probe, trial): hit = u; break
            rot = trial
        rep[k] = hit
    if grip == "wrap":
        wr_, d_, n_, a_ = Hh.frame(); F = Hh.fk(rot)
        side_ = (F[b(2, 1, s)][0] - F[b(3, 1, s)][0]).normalized(); guess = Mw @ (F[b(2, 1, s)][0] + side_ * 0.02 + n_ * 0.035)
        ok, loc, nrm, idx = obj.closest_point_on_mesh(obj.matrix_world.inverted() @ guess)
        rot.update(HP._solve_thumb(Hh, rot, ("point", 0.010), wr_, d_, n_, a_, target=Mw.inverted() @ (obj.matrix_world @ loc), obj=obj, radius=0.008))
    HP._key(rig, s, rot, f, 1.0); return rep
# director review: hand placed on the tool (nudge_hand, as grip_object), then a whole library preset keyed (no per-finger
# closure, which left half-open claws): wrap_grip on the scanner handle, cup_hold under the prosthetic, pinch on syringe/tweezers
for obj_, s_, f0_, f1_, g_, pz_ in ((SCN, "R", 528, 744, "wrap", "wrap_grip"), (PRO, "R", 1509, 1692, "wrap", "cup_hold"),
                                    (SYR, "L", 1717, 1803, "pinch", "pinch"), (TWZ, "R", 1807, 1962, "pinch", "pinch")):
    for f_ in sorted(set(list(range(f0_, f1_ + 1, 4)) + [f1_])):
        ev(f_); Mo = obj_.matrix_world
        if obj_ is SCN:   C_ = Mo @ Vector((0, -0.02, -0.11)); ap_ = Mo.to_3x3() @ Vector((0, 1, 0))     # handle, palm side
        elif obj_ is PRO: C_ = Mo @ (LB_base + (LB_tip - LB_base) * 0.5 + Vector((0, 0, 0.012))); ap_ = Vector((0, 0, -1))
        else:
            C_ = Mo.translation.copy(); sh_ = VB.r.o.matrix_world @ VB.r.o.pose.bones["upperarm01." + s_].head
            ap_ = (C_ - sh_).normalized() + Vector((0, 0, -0.5))
        HP.grip_object(VB.r.o, s_, f_, obj_, C_, ap_.normalized(), grip=("pinch" if g_ == "pinch" else "wrap"))
hpose(VB, "R", (1968, 1975), "relaxed")               # released after setting the tweezers down
hpose(VB, "R", (748,), "relaxed")                     # released after setting the scanner down
ev(1910); print("PIN at 1910", [round(x, 3) for x in PIN.matrix_world.translation], "target", [round(x, 3) for x in pin_in])
ev(1768); print("SYR tip region at 1768", [round(x, 3) for x in (SYR.matrix_world @ Vector((0, 0, 0.06)))], "dist", round((SYR.matrix_world @ Vector((0, 0, 0.06)) - seam).length, 3), "seam", [round(x, 3) for x in seam])

# ================================================================== VOID (beats 5-8)
V1 = Vector((11.7, 1.65, 0.75)); V2 = Vector((14.2, 3.0, -0.2)); V3 = Vector((13.6, -1.0, 0.95)); P3 = Vector((15.4, -2.4, -0.7))
BEAK_MID = (LB_base + LB_tip) / 2
def void_copy(src, name, at, scale, mat=None, coll=C_ANIM, rest=None):
    o = bpy.data.objects.new(name, src.data.copy() if mat else src.data); coll.objects.link(o)
    M0 = rest if rest is not None else Matrix()
    o.matrix_world = Matrix.Translation(at) @ Matrix.Scale(scale, 4) @ Matrix.Translation(-BEAK_MID) @ M0
    if mat:
        o.data.materials.clear(); o.data.materials.append(mat)
    return o
def emis(name, rgb, strength=2.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgb + (1,); b.inputs["Emission Color"].default_value = rgb + (1,); b.inputs["Emission Strength"].default_value = strength
    b.inputs["Alpha"].default_value = alpha; b.inputs["Roughness"].default_value = 0.3
    return m
M_pts = emis("Scan_points", (0.1, 0.9, 1.0), 4.0)
M_ref = emis("Ref_holo", (1.0, 0.5, 0.08), 1.2, 0.4)
M_new = bpy.data.materials.new("CAD_new"); M_new.use_nodes = True; nb = M_new.node_tree.nodes["Principled BSDF"]
nb.inputs["Base Color"].default_value = (0.42, 0.5, 0.56, 1); nb.inputs["Roughness"].default_value = 0.35; nb.inputs["Coat Weight"].default_value = 0.5
nb.inputs["Emission Color"].default_value = (0.2, 0.8, 1.0, 1); nb.inputs["Emission Strength"].default_value = 0.15
# point-cloud GN
gnp = bpy.data.node_groups.new("ScanPoints", 'GeometryNodeTree')
gnp.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry'); gnp.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
gi = gnp.nodes.new("NodeGroupInput"); go = gnp.nodes.new("NodeGroupOutput")
dp = gnp.nodes.new("GeometryNodeDistributePointsOnFaces"); dp.inputs["Density"].default_value = 260000.0
sm = gnp.nodes.new("GeometryNodeSetMaterial"); sm.inputs["Material"].default_value = M_pts
rp = gnp.nodes.new("GeometryNodeSetPointRadius"); rp.inputs["Radius"].default_value = 0.00022
gnp.links.new(gi.outputs[0], dp.inputs[0]); gnp.links.new(dp.outputs[0], rp.inputs[0]); gnp.links.new(rp.outputs[0], sm.inputs[0]); gnp.links.new(sm.outputs[0], go.inputs[0])
S5 = 6.0
stump = [void_copy(UPB, "Scan_stump_up", V1, S5), void_copy(LOW, "Scan_stump_low", V1, S5)]
for o in stump:
    o.modifiers.new("pts", 'NODES').node_group = gnp
ref = [void_copy(UP, "Ref_beak_up", V1, S5, M_ref), void_copy(LOW, "Ref_beak_low", V1, S5, M_ref)]
refpar = bpy.data.objects.new("Ref_beak", None); C_ANIM.objects.link(refpar); refpar.location = V1
bpy.context.view_layer.update()
for o in ref:
    mw = o.matrix_world.copy(); o.parent = refpar; o.matrix_parent_inverse = refpar.matrix_world.inverted()
refpar.rotation_mode = 'XYZ'
for f, off, rz in ((1, (0, 0.28, 0.12), 12), (700, (0, 0.28, 0.12), 12), (760, (0, 0.2, 0.1), 9), (835, (0, 0.0, 0.0), 0), (900, (0, 0, 0), 0)):
    key_loc(refpar, f, V1 + Vector(off), (0, 0, R_(rz)))
# rotating slowly for life
for o in stump + [refpar]: pass
tipr = OB["Beak_tip_piece"]
newhalf = bpy.data.objects.new("New_half", tipr.data.copy()); C_ANIM.objects.link(newhalf)
newhalf.data.materials.clear(); newhalf.data.materials.append(M_new)
# tip_piece mesh is around its own origin; its rest centre is stored in the bird file location (frame 1 key)
tip_rest_center = Vector(sc.get("TIP_REST", (0.0, 0.147, 0.236)))
newhalf.matrix_world = Matrix.Translation(V1) @ Matrix.Scale(S5, 4) @ Matrix.Translation(-BEAK_MID) @ Matrix.Translation(tip_rest_center)
cut = bpy.data.objects.new("Extrude_cutter", bpy.data.meshes.new("Extrude_cutter")); C_ANIM.objects.link(cut)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(cut.data); bm.free()
cut.hide_render = True; cut.display_type = 'WIRE'
ax_w = (LB_tip - LB_base).normalized()
cut.rotation_mode = 'QUATERNION'; cut.rotation_quaternion = Vector((0, 1, 0)).rotation_difference(ax_w)
cut.scale = (1.0, 0.0, 1.0)
for f, L_ in ((1, 0.001), (860, 0.001), (1000, 0.9)):
    st = V1 + (LB_base + (LB_tip - LB_base) * 0.40 - BEAK_MID) * S5
    cut.scale = (1.5, L_ * 2, 1.5); cut.location = st + ax_w * L_; cut.keyframe_insert("scale", frame=f); cut.keyframe_insert("location", frame=f)
# reveal: the new half grows out of the stump cut (scale about the cut point), no boolean (scan mesh is not manifold)
grow = bpy.data.objects.new("New_half_grow", None); C_ANIM.objects.link(grow)
grow.location = V1 + (LB_base + (LB_tip - LB_base) * 0.42 - BEAK_MID) * S5
bpy.context.view_layer.update()
mwn = newhalf.matrix_world.copy(); newhalf.parent = grow; newhalf.matrix_parent_inverse = grow.matrix_world.inverted(); newhalf.matrix_world = mwn
grow.rotation_mode = 'QUATERNION'; grow.rotation_quaternion = Vector((0, 1, 0)).rotation_difference(ax_w)
bpy.context.view_layer.update(); mwn = newhalf.matrix_world.copy(); newhalf.matrix_parent_inverse = grow.matrix_world.inverted(); newhalf.matrix_world = mwn
for f, k_ in ((1, 0.02), (860, 0.02), (1000, 1.0)):
    grow.scale = (1.0, k_, 1.0); grow.keyframe_insert("scale", frame=f)
key_vis(newhalf, [(1, False), (860, True), (1140, False)])
for o in stump: key_vis(o, [(1, False), (690, True), (1140, False)])
for o in ref: key_vis(o, [(1, False), (690, True), (858, False)])
# ---- ghost demo bird (beat 7): copy rig + meshes, translucent; heavy beak tips the head
M_ghost = bpy.data.materials.new("Ghost"); M_ghost.use_nodes = True; gt = M_ghost.node_tree
for n in list(gt.nodes):
    if n.type == 'BSDF_PRINCIPLED': gt.nodes.remove(n)
lw = gt.nodes.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = 0.35
em_ = gt.nodes.new("ShaderNodeEmission"); em_.inputs[0].default_value = (0.3, 0.85, 1.0, 1); em_.inputs[1].default_value = 3.0
tr = gt.nodes.new("ShaderNodeBsdfTransparent"); mx = gt.nodes.new("ShaderNodeMixShader")
gt.links.new(lw.outputs["Facing"], mx.inputs[0]); gt.links.new(tr.outputs[0], mx.inputs[1]); gt.links.new(em_.outputs[0], mx.inputs[2])
gt.links.new(mx.outputs[0], gt.nodes["Material Output"].inputs[0])
M_heavy = bpy.data.materials.new("Heavy_beak"); M_heavy.use_nodes = True; hb = M_heavy.node_tree.nodes["Principled BSDF"]
hb.inputs["Base Color"].default_value = (0.35, 0.33, 0.3, 1); hb.inputs["Metallic"].default_value = 1.0; hb.inputs["Roughness"].default_value = 0.35
M_light = bpy.data.materials.new("Light_beak"); M_light.use_nodes = True; lb = M_light.node_tree.nodes["Principled BSDF"]
lb.inputs["Base Color"].default_value = (0.95, 0.6, 0.1, 1); lb.inputs["Roughness"].default_value = 0.3
gr = rig.copy(); gr.data = rig.data.copy(); gr.name = "Ghost_rig"; C_ANIM.objects.link(gr); gr.animation_data_clear()
GS = 4.0
gr.location = V2; gr.scale = (GS, GS, GS); gr.rotation_euler = (0, 0, R_(0))
for pb in gr.pose.bones: pb.rotation_mode = 'XYZ'
def gmesh(src, name, mat):
    o = bpy.data.objects.new(name, src.data.copy()); C_ANIM.objects.link(o)
    o.data.materials.clear(); o.data.materials.append(mat)
    if src.parent_type == 'BONE':
        bn = gr.data.bones[src.parent_bone]
        o.parent = gr; o.parent_type = 'BONE'; o.parent_bone = src.parent_bone
        o.matrix_parent_inverse = (Matrix.Translation(bn.tail_local) @ bn.matrix_local.to_3x3().to_4x4()).inverted(); o.matrix_basis = Matrix()
    else:
        o.parent = gr; o.matrix_parent_inverse = Matrix()
        for m in src.modifiers:
            if m.type == 'ARMATURE': o.modifiers.new("arm", 'ARMATURE').object = gr
        for g in src.vertex_groups: pass
    return o
gbody = gmesh(OB["Toucan_body"], "Ghost_body", M_ghost)
gheavy = gmesh(UP, "Ghost_beak_heavy", M_heavy); glow = gmesh(LOW, "Ghost_beak_low", M_ghost); glight = gmesh(UP, "Ghost_beak_light", M_light)
gperch = bpy.data.objects.new("Ghost_perch", OB["Perch"].data); C_ANIM.objects.link(gperch)
gperch.location = V2 + Vector((0, 0, -0.07)); gperch.scale = (2.5, 2.5, 2.5)
GP = gr.pose.bones
def gpose(f, head=0, neck=0, chest=0):
    for b, v in (("head", head), ("neck", neck), ("chest", chest)):
        GP[b].rotation_euler = (R_(v), 0, 0); GP[b].keyframe_insert("rotation_euler", frame=f)
gpose(1); gpose(1080); gpose(1110, -6, -4); gpose(1150, -34, -22, -14); gpose(1175, -44, -30, -18); gpose(1200, -40, -28, -16)
gpose(1240, -42, -28, -16); gpose(1262, -10, -6, -4); gpose(1290, 6, 3, 2); gpose(1320, 0, 0, 0)
for f, a in ((1, 0), (1150, 0), (1170, 7), (1190, -4), (1210, 2), (1240, 0)):
    gperch.rotation_euler = (R_(a), 0, 0); gperch.keyframe_insert("rotation_euler", frame=f)
for o in (gbody, glow, gperch): key_vis(o, [(1, False), (1050, True), (1350, False)])
key_vis(gheavy, [(1, False), (1050, True), (1250, False)]); key_vis(glight, [(1, False), (1250, True), (1350, False)])
key_vis(gr, [(1, False), (1050, True), (1350, False)])
# ---- hollow printed beak cutaway (beat 8): gyroid lattice inside a thin shell, half cut away
M_pla = bpy.data.materials.new("PLA_print"); M_pla.use_nodes = True; pl = M_pla.node_tree.nodes["Principled BSDF"]
pl.inputs["Base Color"].default_value = (0.7, 0.66, 0.56, 1); pl.inputs["Roughness"].default_value = 0.45; pl.inputs["Subsurface Weight"].default_value = 0.0
wv = M_pla.node_tree.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'; wv.inputs["Scale"].default_value = 60
tcp = M_pla.node_tree.nodes.new("ShaderNodeTexCoord"); M_pla.node_tree.links.new(tcp.outputs["Object"], wv.inputs["Vector"])
bpl = M_pla.node_tree.nodes.new("ShaderNodeBump"); bpl.inputs["Strength"].default_value = 0.3
M_pla.node_tree.links.new(wv.outputs["Fac"], bpl.inputs["Height"]); M_pla.node_tree.links.new(bpl.outputs["Normal"], pl.inputs["Normal"])
hollow = void_copy(UP, "Hollow_beak", V3, S5, M_pla)
_bm = bmesh.new(); _bm.from_mesh(UP.data); _bm.from_mesh(LOW.data); _bm.to_mesh(hollow.data); _bm.free()
hollow.data.materials.clear(); hollow.data.materials.append(M_pla)
# gyroid infill points: per (x,y) column, ray intervals inside the closed beak (upper+lower), gyroid band in numpy
from mathutils.bvhtree import BVHTree
bvh = BVHTree.FromObject(hollow, bpy.context.evaluated_depsgraph_get(), deform=False) if False else None
_bm = bmesh.new(); _bm.from_mesh(hollow.data); bvh = BVHTree.FromBMesh(_bm)
Vh = np.array([v.co[:] for v in hollow.data.vertices]); mn_, mx_ = Vh.min(0), Vh.max(0)
VOX = 0.0007; per = 0.011; kk = 2 * math.pi / per
pts = []
for x in np.arange(mn_[0] + VOX, mx_[0], VOX):
    for y in np.arange(mn_[1] + VOX, mx_[1], VOX):
        o = Vector((x, y, mx_[2] + 0.01)); hits = []
        while True:
            h = bvh.ray_cast(o, Vector((0, 0, -1)))
            if h[0] is None: break
            hits.append(h[0].z); o = h[0] + Vector((0, 0, -1e-5))
            if len(hits) > 12: break
        for a, b in ([(hits[0], hits[-1])] if len(hits) >= 2 else []):
            zs = np.arange(b + 0.0018, a - 0.0018, VOX)
            if len(zs) == 0: continue
            g = np.sin(kk * x) * np.cos(kk * y) + np.sin(kk * y) * np.cos(kk * zs) + np.sin(kk * zs) * np.cos(kk * x)
            for z in zs[np.abs(g) < 0.32]: pts.append((x, y, z))
_bm.free()
print("GYROID points", len(pts))
lat = bpy.data.objects.new("Hollow_lattice", bpy.data.meshes.new("Hollow_lattice")); C_ANIM.objects.link(lat)
lat.data.from_pydata(pts, [], []); lat.matrix_world = hollow.matrix_world.copy()
gy = bpy.data.node_groups.new("LatticeSkin", 'GeometryNodeTree')
gy.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry'); gy.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
N_ = gy.nodes; L_ = gy.links
gi = N_.new("NodeGroupInput"); go = N_.new("NodeGroupOutput")
m2p = N_.new("GeometryNodeMeshToPoints"); p2v = N_.new("GeometryNodePointsToVolume"); v2m = N_.new("GeometryNodeVolumeToMesh")
p2v.inputs["Radius"].default_value = VOX * 0.9
try: p2v.resolution_mode = 'VOXEL_SIZE'
except Exception: pass
if "Voxel Size" in p2v.inputs: p2v.inputs["Voxel Size"].default_value = VOX * 0.4
L_.new(gi.outputs[0], m2p.inputs[0]); L_.new(m2p.outputs[0], p2v.inputs[0]); L_.new(p2v.outputs[0], v2m.inputs[0])
pos = N_.new("GeometryNodeInputPosition"); sx_ = N_.new("ShaderNodeSeparateXYZ"); L_.new(pos.outputs[0], sx_.inputs[0])
gt_ = N_.new("ShaderNodeMath"); gt_.operation = 'GREATER_THAN'; gt_.inputs[1].default_value = 0.0; L_.new(sx_.outputs[0], gt_.inputs[0])
dg_ = N_.new("GeometryNodeDeleteGeometry"); L_.new(v2m.outputs[0], dg_.inputs[0]); L_.new(gt_.outputs[0], dg_.inputs["Selection"])
smt = N_.new("GeometryNodeSetMaterial"); smt.inputs["Material"].default_value = M_pla
ssm = N_.new("GeometryNodeSetShadeSmooth")
L_.new(dg_.outputs[0], ssm.inputs[0]); L_.new(ssm.outputs[0], smt.inputs[0]); L_.new(smt.outputs[0], go.inputs[0])
lat.modifiers.new("skin", 'NODES').node_group = gy
# outer shell: half cut away (x>0 deleted) + 1.2 mm wall
bm = bmesh.new(); bm.from_mesh(hollow.data)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.x > 0.0], context='VERTS'); bm.to_mesh(hollow.data); bm.free()
so_ = hollow.modifiers.new("wall", 'SOLIDIFY'); so_.thickness = 0.0012; so_.offset = -1
M_shell = UP.data.materials[0].copy(); M_shell.name = "Printed_shell_paint"
hollow.data.materials.clear(); hollow.data.materials.append(M_pla)
key_vis(lat, [(1, False), (1330, True), (1530, False)])
key_vis(hollow, [(1, False), (1330, True), (1530, False)])
# printer + printing beak + nozzle (beat 8 end)
prn = OB["printer"]; prn_v = bpy.data.objects.new("Printer_void", prn.data); C_ANIM.objects.link(prn_v)
prn_v.location = P3; prn_v.scale = (3.2, 3.2, 3.2); prn_v.rotation_euler = (0, 0, R_(-60))
Vp = np.array([v.co[:] for v in prn.data.vertices]); bed_z = P3.z + 3.2 * (Vp[:, 2].min() + 0.18 * np.ptp(Vp[:, 2]))
printed = void_copy(UP, "Printing_beak", Vector((P3.x, P3.y, bed_z + 0.0)), 4.0, M_pla)
Vb_ = np.array([printed.matrix_world @ Vector(v.co) for v in printed.data.vertices]); zmin, zmax = Vb_[:, 2].min(), Vb_[:, 2].max()
printed.location.z += bed_z - zmin; zmax += bed_z - zmin; zmin = bed_z
# printing reveal: the beak rises layer by layer from the bed (scale in z about the bed), no boolean (scan mesh not manifold)
grw = bpy.data.objects.new("Print_grow", None); C_ANIM.objects.link(grw); grw.location = (printed.location.x, printed.location.y, zmin)
bpy.context.view_layer.update(); mwp = printed.matrix_world.copy(); printed.parent = grw; printed.matrix_parent_inverse = grw.matrix_world.inverted(); printed.matrix_world = mwp
for f, h in ((1, 0.02), (1340, 0.02), (1420, 0.35), (1530, 1.0)):
    grw.scale = (1, 1, h); grw.keyframe_insert("scale", frame=f)
M_brass = bpy.data.materials.new("Brass"); M_brass.use_nodes = True; bs = M_brass.node_tree.nodes["Principled BSDF"]
bs.inputs["Base Color"].default_value = (0.8, 0.55, 0.25, 1); bs.inputs["Metallic"].default_value = 1; bs.inputs["Roughness"].default_value = 0.3
bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.035, radius2=0.004, depth=0.06, location=(0, 0, -50)); noz = bpy.context.active_object; noz.name = "Nozzle"
for c in noz.users_collection: c.objects.unlink(noz)
C_ANIM.objects.link(noz); noz.data.materials.append(M_brass); noz.rotation_euler = (math.pi, 0, 0)
blk = bpy.data.objects.new("Nozzle_block", bpy.data.meshes.new("Nozzle_block")); C_ANIM.objects.link(blk)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(blk.data); bm.free(); blk.scale = (0.09, 0.09, 0.07); blk.parent = noz; blk.location = (0, 0, 0.06)
blk.data.materials.append(OB["Steel"].active_material if "Steel" in OB else bpy.data.materials["Steel"])
cx, cy = P3.x, P3.y
for f in range(1340, 1540, 6):
    h = 0.001 + (0.2 - 0.001) * min(1, max(0, (f - 1) / 1419)) if f < 1420 else 0.2 + 0.55 * (f - 1420) / 110
    z = zmin + (zmax - zmin) * min(1.0, 0.02 + (0.33 * (f - 1340) / 80 if f < 1420 else 0.35 + 0.65 * (f - 1420) / 110)) + 0.035
    a = f * 0.35; key_loc(noz, f, Vector((cx + 0.12 * math.cos(a), cy + 0.25 * math.sin(a * 1.3), z)))
for o in (prn_v, printed, noz, blk): key_vis(o, [(1, False), (1330, True), (1540, False)])
print('BED_Z', bed_z, 'PRINT z', zmin, zmax)
# portal: hide wall patch + monitor back from camera while the camera passes through the screen
vf_ = OB["Void_front"]   # keyed after the camera path is known (see end)
for nm in ("Wall_patch", "Monitor_back"):
    o = OB[nm]
    for f, v in ((1, True), (690, False), (1560, True)):
        o.visible_camera = v; o.keyframe_insert("visible_camera", frame=f)
    constant(o)

# ================================================================== CAMERA (one camera, Catmull-Rom spline through framings)
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.sensor_width = 36; cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.8; cam.data.clip_start = 0.01
ev(1)
def bwj(local, f=None):          # jungle bird space -> world
    return BIRD_J + Vector(local)
HEADJ = BIRD_J + Vector((0, 0.03, 0.25)); BEAKJ = BIRD_J + (LB_base + LB_tip) / 2
STK = lambda a: PV + (Quaternion(Vector((1, 0, 0)), R_(a)) @ base_q) @ Vector((0, 0, 1.12))
BC = BIRD_C; HEADC = bw((0, 0.03, 0.25)); BEAKC = bw((LB_base + LB_tip) / 2); SEAM = seam
SCREEN = Vector(sc["SCREEN"]) + Vector((0.0, 0, 0.06))
ENC = BIRD_E; HEADE = BIRD_E + Vector((0, 0.03, 0.25))
K = [  # frame, position, target, lens, focus target(None = target)
 (1, BIRD_J + Vector((0.85, 1.25, -0.55)), HEADJ + Vector((0, 0, -0.08)), 24),
 (34, BIRD_J + Vector((0.75, 0.85, 0.05)), HEADJ, 28),
 (64, STK(-48) + Vector((0.45, 0.2, 0.28)), STK(-48) * 0.3 + BEAKJ * 0.7, 28),
 (90, STK(-14) + Vector((0.38, 0.22, 0.12)), BEAKJ, 32),
 (104, BEAKJ + Vector((0.46, 0.2, 0.12)), BEAKJ, 34),
 (135, BEAKJ + Vector((0.12, 0.34, 0.08)), BEAKJ + Vector((0, 0.1, 0.02)), 45),
 (175, BEAKJ + Vector((-0.16, 0.30, 0.02)), BEAKJ + Vector((0, 0.18, -0.04)), 52),
 (215, BIRD_J + Vector((-0.65, 0.75, 0.42)), HEADJ, 32),
 (255, BIRD_J + Vector((-0.45, 0.9, 0.18)), HEADJ + Vector((0, 0, -0.04)), 30),
 (300, HEADJ + Vector((0.28, 0.36, -0.16)), FIG0, 32),
 (345, BIRD_J + Vector((0.78, 0.18, 0.26)), (HEADJ + FIG0) / 2, 36),
 (395, FIG0 + Vector((0.42, 0.34, 0.36)), (FIG0 + HEADJ) / 2 + Vector((0, 0.04, -0.22)), 26),
 (445, BIRD_J + Vector((0.55, 0.62, 0.32)), HEADJ, 40),
 (495, BIRD_J + Vector((1.0, 0.25, 0.25)), HEADJ, 34),
 (528, Vector((2.3, 0.0, 1.62)), Vector((4.6, 0, 1.5)), 22),
 (552, Vector((3.85, 0.0, 1.55)), BC + Vector((0, 0, 0.1)), 22),
 (592, Vector((5.55, -0.45, 1.45)), BC + Vector((0, 0, 0.15)), 28),
 (636, BEAKC + Vector((-0.14, 0.06, 0.5)), BEAKC, 34),
 (672, BEAKC + Vector((-0.2, -0.04, 0.42)), BEAKC, 40),
 (689, Vector((7.45, 0.1, 1.85)), BEAKC, 30),
 (708, Vector((7.95, 0.9, 1.45)), SCREEN, 28),
 (738, SCREEN + Vector((-0.42, 0, 0.0)), SCREEN + Vector((1, 0, 0)), 30),
 (756, SCREEN + Vector((0.12, 0, 0.0)), SCREEN + Vector((1.5, 0, 0)), 30),
 (800, V1 + Vector((-0.95, -0.25, 0.18)), V1, 32),
 (846, V1 + Vector((-0.55, -0.85, 0.25)), V1, 34),
 (905, V1 + Vector((0.3, -1.45, 0.5)), V1 + Vector((0.1, 0, 0)), 34),
 (965, V1 + Vector((1.25, -0.9, 0.2)), V1 + Vector((0.2, 0.05, -0.05)), 38),
 (1025, V1 + Vector((1.1, -0.3, 0.05)), V1 + Vector((0.3, 0.3, -0.12)), 40),
 (1075, V2 + Vector((-2.6, -0.6, 1.4)), V2 + Vector((0, 0.3, 0.9)), 30),
 (1130, V2 + Vector((-2.2, 0.0, 1.1)), V2 + Vector((0, 0.4, 0.85)), 30),
 (1185, V2 + Vector((-1.9, 0.9, 0.35)), V2 + Vector((0, 0.6, 0.6)), 28),
 (1245, V2 + Vector((-1.9, 0.5, 1.9)), V2 + Vector((0, 0.5, 0.8)), 30),
 (1300, V2 + Vector((-2.3, -0.6, 1.3)), V2 + Vector((0, 0.4, 0.9)), 30),
 (1360, V3 + Vector((1.05, 0.75, 0.4)), V3, 30),
 (1410, V3 + Vector((0.62, -0.05, 0.12)), V3 + Vector((0.0, 0.1, -0.03)), 36),
 (1460, P3 + Vector((-1.0, 0.9, 1.45)), Vector((P3.x, P3.y, bed_z + 0.2)), 34),
 (1492, P3 + Vector((-1.2, 1.3, 1.4)), Vector((P3.x, P3.y, bed_z + 0.25)), 30),
 (1500, SCREEN + Vector((0.95, -0.05, 0.05)), SCREEN, 30),
 (1530, SCREEN + Vector((0.45, 0, 0.0)), SCREEN + Vector((-1, 0, 0)), 30),
 (1552, SCREEN + Vector((-0.5, -0.1, 0.05)), BEAKC, 30),
 (1575, Vector((7.25, 0.05, 1.78)), SEAM, 36),
 (1600, BEAKC + Vector((-0.3, -0.22, 0.16)), SEAM, 42),
 (1650, BEAKC + Vector((-0.26, 0.02, 0.05)), SEAM, 55),
 (1700, BEAKC + Vector((-0.18, -0.2, 0.12)), SEAM, 52),
 (1750, SEAM + Vector((-0.1, -0.1, 0.08)), SEAM, 62),
 (1800, SEAM + Vector((-0.26, -0.16, 0.18)), SEAM + Vector((0, 0.04, 0.01)), 45),
 (1836, SEAM + Vector((-0.34, -0.3, 0.24)), SEAM + Vector((0, 0.04, 0.0)), 40),
 (1870, BC + Vector((-0.95, -0.25, 0.62)), BC + Vector((0, 0.1, 0.35)), 28),
 (1925, Vector((4.9, -0.25, 1.5)), BC + Vector((0, 0, 0.3)), 24),
 (1957, Vector((3.65, -0.1, 1.55)), BC + Vector((0, 0, 0.3)), 22),
 (1976, Vector((2.35, -0.5, 1.5)), HEADE + Vector((0, 0, 0.1)), 24),
 (2010, ENC + Vector((0.95, 0.3, 0.3)), HEADE, 34),
 (2070, ENC + Vector((0.72, 0.72, 0.16)), HEADE + Vector((0, 0.1, -0.05)), 36),
 (2130, ENC + Vector((0.9, 0.2, 0.22)), HEADE, 36),
 (2195, ENC + Vector((0.88, 0.42, 0.26)), HEADE, 36),
 (2250, ENC + Vector((0.82, 0.55, 0.3)), HEADE, 36),
]
fp, ft, fl = catmull([(k[0], k[1]) for k in K]), catmull([(k[0], k[2]) for k in K]), pchip([(k[0], float(k[3])) for k in K])
cam.rotation_mode = 'QUATERNION'; prevq = None
foc = bpy.data.objects.new("Cam_focus", None); C_ANIM.objects.link(foc); cam.data.dof.focus_object = foc
for f in range(1, 2251):
    p = fp(f); t = ft(f); q = (t - p).to_track_quat('-Z', 'Y')
    if prevq is not None and prevq.dot(q) < 0: q = -q
    prevq = q
    cam.location = p; cam.keyframe_insert("location", frame=f)
    cam.rotation_quaternion = q; cam.keyframe_insert("rotation_quaternion", frame=f)
    cam.data.lens = fl(f); cam.data.keyframe_insert("lens", frame=f)
    foc.location = t; foc.keyframe_insert("location", frame=f)
# void front face: camera-visible only while the camera is well inside the void and looking away from the wall
inside = [f for f in range(1, 2251) if fp(f).x > 10.45 and f < 1490]
f_in, f_out = (min(inside), max(inside)) if inside else (800, 1490)
for f, v in ((1, False), (f_in, True), (f_out + 1, False)):
    vf_.visible_camera = v; vf_.keyframe_insert("visible_camera", frame=f)
constant(vf_); print("VOID_FRONT visible", f_in, f_out)
json.dump([[k[0], list(k[1]), list(k[2]), k[3]] for k in K], open(os.path.join(HERE, "camera_keys.json"), "w"))
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=out)
print("ANIM_DONE", out)
