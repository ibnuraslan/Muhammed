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
PRO = UP.copy(); PRO.data = UP.data.copy(); PRO.name = "Prosthetic_beak"; C_ANIM.objects.link(PRO)
pm = UP.data.materials[0].copy(); pm.name = "Prosthetic_paint"
for nd in pm.node_tree.nodes:
    if nd.type == 'BSDF_PRINCIPLED': nd.inputs["Roughness"].default_value = 0.22; nd.inputs["Coat Weight"].default_value = 0.8
PRO.data.materials[0] = pm
axis_r = (LB_tip - LB_base).normalized()
for f, off in ((1, 0.09), (1560, 0.09), (1600, 0.05), (1660, 0.008), (1692, 0.0)):
    PRO.location = axis_r * off + Vector((0, 0, 0.004 if off > 0 else 0)); PRO.keyframe_insert("location", frame=f)
key_vis(PRO, [(1, False), (1515, True), (1976, False)])

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

# ---- the stick (swing plane = bird's side; contact on the upper beak at frame 102)
stick = OB["Strike_stick"]; pivot = bpy.data.objects.new("Stick_pivot", None); C_ANIM.objects.link(pivot)
ev(100)
HIT = beak_point(0.45)
PV = HIT + Vector((0.0, -0.18, 0.66))        # pivot above/behind (out of frame)
pivot.location = PV; stick.parent = pivot; stick.location = (0, 0, 0)
d0 = (HIT - PV).normalized()
base_q = Vector((0, 0, -1)).rotation_difference(d0)    # stick local +z points from pivot outward? our mesh runs z -0.05..0.9 -> use -z? fix below
# stick mesh runs from pivot along +z; we want +z -> d0
base_q = Vector((0, 0, 1)).rotation_difference(d0)
pivot.rotation_mode = 'QUATERNION'
def stick_ang(f, a):
    pivot.rotation_quaternion = Quaternion(Vector((1, 0, 0)), R_(a)) @ base_q; pivot.keyframe_insert("rotation_quaternion", frame=f)
for f, a in ((1, -95), (30, -80), (60, -48), (85, -18), (102, 0), (110, 7), (130, 14), (160, 20), (200, 34), (260, 70), (300, 100)):
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
TWIG.parent = fpiv; TWIG.location = (0, 0, -0.21); TWIG.rotation_euler = (0, 0, 0)
V = np.array([v.co[:] for v in TWIG.data.vertices]); ax_ = int(np.argmax(V.max(0) - V.min(0)))
sc_ = [0.45] * 3; sc_[ax_] = 1.0; TWIG.scale = sc_
if ax_ == 0: TWIG.rotation_euler = (0, R_(90), 0)
if ax_ == 1: TWIG.rotation_euler = (R_(90), 0, 0)
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
key_vis(FIG, [(1, True), (392, False)])
key_vis(TWIG, [(1, True), (528, False)])

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
def stand(H, f, pos, yaw, flex=8, head=(10, 0), spine_flex=14, twist=0):
    H.key_root(f, Vector((pos[0], pos[1], H.root_head.z - 0.02)), yaw=yaw, flex=flex)
    H.key_spine(f, flex=spine_flex, twist=twist, head=head)
    for s in "LR": H.key_foot(s, f, H.foot_xy(s, Vector(pos), yaw), yaw)
ev(600)
def bw(local):     # bird-space (rest) point -> world, clinic placement
    return Matrix.Translation(BIRD_C) @ Euler(ROT_C).to_matrix().to_4x4() @ Vector(local)
A_POS, B_POS = (7.02, -0.56), (6.98, 0.58)
for f in (530, 900, 1400, 1960):
    stand(VA, f, A_POS, 180, flex=10, head=(18, 0), spine_flex=18)
for f in (530, 700, 1500, 1960):
    stand(VB, f, B_POS, 0, flex=10, head=(16, 0), spine_flex=16)
# VetA cradles the bird the whole clinic stay
for f in (530, 1000, 1500, 1960):
    VA.key_hand("R", f, bw((-0.075, -0.03, 0.10)), Vector((0.15, 0.1, 1)), Vector((1, 0, 0)), pole=Vector((A_POS[0] - 0.4, A_POS[1] - 0.2, 1.0)))
    VA.key_hand("L", f, bw((0.06, -0.06, 0.2)), Vector((-1, 0.0, -0.4)), Vector((0, 0, -1)), pole=Vector((A_POS[0] + 0.4, A_POS[1] - 0.2, 1.2)))
# scanner sweeping (VetB right hand), beat 4
SCN = OB["Scanner"]; SCN.rotation_mode = 'QUATERNION'
stub_mid = bw(LB_base + (LB_tip - LB_base) * 0.25)
for f, dx in ((540, 0.06), (575, -0.04), (610, 0.05), (645, -0.05), (680, 0.02)):
    S = stub_mid + Vector((dx, 0.17, 0.12))
    q = (stub_mid - S).to_track_quat('Y', 'Z')
    key_loc(SCN, f, S); SCN.rotation_quaternion = q; SCN.keyframe_insert("rotation_quaternion", frame=f)
    grip = S + q @ Vector((0, -0.02, -0.11))
    VB.key_hand("R", f, grip, q @ Vector((0, 1, 0.2)), q @ Vector((0, 0, -1)) * -1, pole=grip + Vector((0.3, 0.3, -0.3)))
    VB.key_hand("L", f, Vector((6.85, 0.32, TZ + 0.02)), Vector((0, -1, 0)), Vector((0, 0, -1)), pole=Vector((6.6, 0.8, 1.0)))
key_loc(SCN, 760, Vector((7.45, 0.25, TZ + 0.03))); SCN.rotation_quaternion = Quaternion((1, 0, 0, 0)); SCN.keyframe_insert("rotation_quaternion", frame=760)
for f in (760, 1500):
    VB.key_hand("R", f, Vector((7.3, 0.3, TZ + 0.03)), Vector((0, -1, 0)), Vector((0, 0, -1)), pole=Vector((7.5, 0.8, 1.0)))
    VB.key_hand("L", f, Vector((6.75, 0.3, TZ + 0.03)), Vector((0, -1, 0)), Vector((0, 0, -1)), pole=Vector((6.5, 0.8, 1.0)))
# laser line: narrow red spot projected from the scanner lens onto the stump
las = bpy.data.objects.new("Laser_spot", bpy.data.lights.new("Laser_spot", 'SPOT')); C_ANIM.objects.link(las)
las.data.energy = 6; las.data.color = (1, 0.04, 0.02); las.data.spot_size = R_(28); las.data.spot_blend = 0.0; las.data.shadow_soft_size = 0
las.parent = SCN; las.location = (0, 0.03, 0); las.rotation_euler = (R_(-90), 0, 0); las.scale = (1, 0.02, 1)
OB["Laser_line"].hide_render = True
key_vis(las, [(1, False), (538, True), (690, False)])
# prosthetic in VetB's hand (1515-1692): hand follows the prosthetic
for f in range(1515, 1700, 6):
    ev(f); pw = PRO.matrix_world @ (LB_base + (LB_tip - LB_base) * 0.75)
    VB.key_hand("R", f, pw + Vector((0.0, 0.07, 0.05)), Vector((0, -1, -0.5)), Vector((0, 0, -1)), pole=pw + Vector((0.3, 0.4, -0.2)))
# glue syringe (left hand) 1704-1800, tweezers + pin (right) 1810-1950
SYR, TWZ, PIN = OB["Glue_syringe"], OB["Tweezers"], OB["Pin"]
seam = bw(LB_base + (LB_tip - LB_base) * 0.42 + Vector((0, 0.012, 0.02)))
for f, s_ in ((1700, 0.08), (1730, 0.0), (1760, 0.0), (1790, 0.06)):
    p_ = seam + Vector((0.0, 0.05 + s_, 0.035)); q = (seam - p_).to_track_quat('Z', 'Y')
    SYR.rotation_mode = 'QUATERNION'; key_loc(SYR, f, p_ + (p_ - seam).normalized() * 0.06); SYR.rotation_quaternion = q; SYR.keyframe_insert("rotation_quaternion", frame=f)
    VB.key_hand("L", f, p_ + (p_ - seam).normalized() * 0.1, (seam - p_).normalized(), Vector((0, 0, -1)), pole=p_ + Vector((-0.3, 0.4, -0.2)))
key_vis(SYR, [(1, False), (1690, True), (1810, False)])
pin_in = bw(LB_base + (LB_tip - LB_base) * 0.36 + Vector((0, 0.0, 0.03)))
for f, d_ in ((1810, 0.08), (1850, 0.02), (1880, 0.008), (1910, 0.0), (1945, 0.0)):
    p_ = pin_in + Vector((0, d_, 0.01 + d_ * 0.5))
    PIN.rotation_mode = 'XYZ'; key_loc(PIN, f, p_, (R_(90), 0, 0))
    TWZ.rotation_mode = 'XYZ'; key_loc(TWZ, f, p_ + Vector((0, 0.065, 0.004)), (0, 0, R_(90)))
    VB.key_hand("R", f, p_ + Vector((0, 0.13, 0.03)), Vector((0, -1, -0.1)), Vector((0, 0, -1)), pole=p_ + Vector((0.3, 0.4, -0.2)))
key_vis(PIN, [(1, False), (1800, True), (1976, False)]); key_vis(TWZ, [(1, False), (1800, True), (1950, False)])
# glue bead along the seam (grows)
bpy.ops.mesh.primitive_torus_add(major_radius=0.016, minor_radius=0.0016, location=seam - Vector((0, 0.012, 0.02)))
glue = bpy.context.active_object; glue.name = "Glue_bead"
for c in glue.users_collection: c.objects.unlink(glue)
C_ANIM.objects.link(glue)
glue.rotation_euler = (0, R_(90), 0)
gm = bpy.data.materials.new("Glue"); gm.use_nodes = True; gb = gm.node_tree.nodes["Principled BSDF"]
gb.inputs["Base Color"].default_value = (0.9, 0.88, 0.8, 1); gb.inputs["Roughness"].default_value = 0.05; gb.inputs["Transmission Weight"].default_value = 0.7
glue.data.materials.append(gm)
for f, s_ in ((1, 0.0), (1725, 0.0), (1770, 1.0)):
    glue.scale = (s_, 1, 1) if s_ else (0.001, 0.001, 0.001); glue.keyframe_insert("scale", frame=f)
key_vis(glue, [(1, False), (1725, True), (1976, False)])
# assistant: background walk (life)
AS.walk(lambda f: Vector((5.0 + 3.6 * smooth((f - 560) / 240), 2.15, 0)) if f < 820 else Vector((8.6 - 3.4 * smooth((f - 1520) / 300), 2.15, 0)),
        lambda f: -90 if f < 820 else 90, 560, 800, stride=0.72)
AS.walk(lambda f: Vector((8.6 - 3.4 * smooth((f - 1520) / 300), 2.15, 0)), lambda f: 90, 1520, 1820, stride=0.72)
stand(AS, 1840, (5.2, 2.15), 180, head=(20, 0)); stand(AS, 1960, (5.2, 2.15), 180, head=(25, 10))
for nm in ("VetA", "VetB", "Assist"):
    o = OB[nm]
    for ch in [o] + list(o.children): key_vis(ch, [(1, False), (525, True), (1980, False)])

# ================================================================== VOID (beats 5-8)
V1 = Vector((11.7, 1.25, 1.05)); V2 = Vector((14.2, 3.0, -0.2)); V3 = Vector((13.6, -1.0, 0.95)); P3 = Vector((15.4, -2.4, -0.7))
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
M_ref = emis("Ref_holo", (1.0, 0.55, 0.1), 0.8, 0.55)
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
for o in ref:
    mw = o.matrix_world.copy(); o.parent = refpar; o.matrix_parent_inverse = refpar.matrix_world.inverted()
refpar.rotation_mode = 'XYZ'
for f, off, rz in ((1, (0, 0.9, 0.25), 25), (700, (0, 0.9, 0.25), 25), (760, (0, 0.6, 0.2), 18), (835, (0, 0.0, 0.0), 0), (900, (0, 0, 0), 0)):
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
bo = newhalf.modifiers.new("reveal", 'BOOLEAN'); bo.object = cut; bo.operation = 'INTERSECT'; bo.solver = 'EXACT'
key_vis(newhalf, [(1, False), (860, True), (1140, False)])
for o in stump: key_vis(o, [(1, False), (690, True), (1140, False)])
for o in ref: key_vis(o, [(1, False), (690, True), (930, False)])
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
pl.inputs["Base Color"].default_value = (0.55, 0.5, 0.42, 1); pl.inputs["Roughness"].default_value = 0.45; pl.inputs["Subsurface Weight"].default_value = 0.2
wv = M_pla.node_tree.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'; wv.inputs["Scale"].default_value = 60
tcp = M_pla.node_tree.nodes.new("ShaderNodeTexCoord"); M_pla.node_tree.links.new(tcp.outputs["Object"], wv.inputs["Vector"])
bpl = M_pla.node_tree.nodes.new("ShaderNodeBump"); bpl.inputs["Strength"].default_value = 0.3
M_pla.node_tree.links.new(wv.outputs["Fac"], bpl.inputs["Height"]); M_pla.node_tree.links.new(bpl.outputs["Normal"], pl.inputs["Normal"])
hollow = void_copy(UP, "Hollow_beak", V3, S5, M_pla)
gy = bpy.data.node_groups.new("Gyroid", 'GeometryNodeTree')
gy.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry'); gy.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
N_ = gy.nodes; L_ = gy.links
gi = N_.new("NodeGroupInput"); go = N_.new("NodeGroupOutput")
bb = N_.new("GeometryNodeBoundBox"); L_.new(gi.outputs[0], bb.inputs[0])
vc = N_.new("GeometryNodeVolumeCube")
for k, v in (("Resolution X", 110), ("Resolution Y", 110), ("Resolution Z", 110)): vc.inputs[k].default_value = v
L_.new(bb.outputs["Min"], vc.inputs["Min"]); L_.new(bb.outputs["Max"], vc.inputs["Max"])
pos = N_.new("GeometryNodeInputPosition"); scl = N_.new("ShaderNodeVectorMath"); scl.operation = 'SCALE'; scl.inputs["Scale"].default_value = 2 * math.pi / 0.011
L_.new(pos.outputs[0], scl.inputs[0]); sxyz = N_.new("ShaderNodeSeparateXYZ"); L_.new(scl.outputs[0], sxyz.inputs[0])
def M(op, a, b=None):
    n = N_.new("ShaderNodeMath"); n.operation = op
    for i, x in enumerate((a, b)):
        if x is None: continue
        if isinstance(x, (int, float)): n.inputs[i].default_value = x
        else: L_.new(x, n.inputs[i])
    return n.outputs[0]
X_, Y_, Z_ = sxyz.outputs[0], sxyz.outputs[1], sxyz.outputs[2]
g_ = M('ADD', M('ADD', M('MULTIPLY', M('SINE', X_), M('COSINE', Y_)), M('MULTIPLY', M('SINE', Y_), M('COSINE', Z_))), M('MULTIPLY', M('SINE', Z_), M('COSINE', X_)))
dens = M('SUBTRACT', 0.28, M('ABSOLUTE', g_))
L_.new(dens, vc.inputs["Density"])
v2m = N_.new("GeometryNodeVolumeToMesh"); L_.new(vc.outputs[0], v2m.inputs[0])
if "Threshold" in v2m.inputs: v2m.inputs["Threshold"].default_value = 0.0
mb = N_.new("GeometryNodeMeshBoolean"); mb.operation = 'INTERSECT'
L_.new(v2m.outputs[0], mb.inputs["Mesh"]); L_.new(gi.outputs[0], mb.inputs["Mesh"])
# shell (thin wall)
ext = N_.new("GeometryNodeJoinGeometry")
L_.new(mb.outputs[0], ext.inputs[0]); L_.new(gi.outputs[0], ext.inputs[0])
# cut away half (x > 0 removed): difference with a box
cbx = N_.new("GeometryNodeMeshCube"); cbx.inputs["Size"].default_value = (0.2, 0.5, 0.5)
tr_ = N_.new("GeometryNodeTransform"); tr_.inputs["Translation"].default_value = (0.1, 0.1, 0.2)
L_.new(cbx.outputs[0], tr_.inputs[0])
mb2 = N_.new("GeometryNodeMeshBoolean"); mb2.operation = 'DIFFERENCE'
L_.new(ext.outputs[0], mb2.inputs[0]); L_.new(tr_.outputs[0], mb2.inputs[1])
smt = N_.new("GeometryNodeSetMaterial"); smt.inputs["Material"].default_value = M_pla
L_.new(mb2.outputs[0], smt.inputs[0]); L_.new(smt.outputs[0], go.inputs[0])
hollow.modifiers.new("gyroid", 'NODES').node_group = gy
hollow.data.transform(Matrix())  # data stays in bird rest coords (metres), object scaled x6
key_vis(hollow, [(1, False), (1330, True), (1530, False)])
# printer + printing beak + nozzle (beat 8 end)
prn = OB["printer"]; prn_v = bpy.data.objects.new("Printer_void", prn.data); C_ANIM.objects.link(prn_v)
prn_v.location = P3; prn_v.scale = (3.2, 3.2, 3.2); prn_v.rotation_euler = (0, 0, R_(-60))
Vp = np.array([v.co[:] for v in prn.data.vertices]); bed_z = P3.z + 3.2 * (Vp[:, 2].min() + 0.18 * np.ptp(Vp[:, 2]))
printed = void_copy(UP, "Printing_beak", Vector((P3.x, P3.y, bed_z + 0.0)) + Vector((0, 0, 0.0)), 3.0, M_pla)
pc_ = bpy.data.objects.new("Print_clip", bpy.data.meshes.new("Print_clip")); C_ANIM.objects.link(pc_)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(pc_.data); bm.free(); pc_.hide_render = True; pc_.display_type = 'WIRE'
Vb_ = np.array([printed.matrix_world @ Vector(v.co) for v in printed.data.vertices]); zmin, zmax = Vb_[:, 2].min(), Vb_[:, 2].max()
printed.location.z += bed_z - zmin; zmax += bed_z - zmin; zmin = bed_z
for f, h in ((1, 0.001), (1420, 0.2), (1530, 0.75)):
    pc_.scale = (1.5, 1.5, (zmax - zmin) * h); pc_.location = (P3.x, P3.y, zmin + (zmax - zmin) * h / 2)
    pc_.keyframe_insert("scale", frame=f); pc_.keyframe_insert("location", frame=f)
b2 = printed.modifiers.new("clip", 'BOOLEAN'); b2.object = pc_; b2.operation = 'INTERSECT'; b2.solver = 'EXACT'
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
    z = zmin + (zmax - zmin) * min(h, 0.75) + 0.035
    a = f * 0.35; key_loc(noz, f, Vector((cx + 0.12 * math.cos(a), cy + 0.25 * math.sin(a * 1.3), z)))
for o in (prn_v, printed, noz, blk): key_vis(o, [(1, False), (1330, True), (1540, False)])
# portal: hide wall patch + monitor back from camera while the camera passes through the screen
vf_ = OB["Void_front"]
for f, v in ((1, False), (758, True), (1527, False)):
    vf_.visible_camera = v; vf_.keyframe_insert("visible_camera", frame=f)
constant(vf_)
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
STK = lambda a: PV + (Quaternion(Vector((1, 0, 0)), R_(a)) @ base_q) @ Vector((0, 0, 0.55))
BC = BIRD_C; HEADC = bw((0, 0.03, 0.25)); BEAKC = bw((LB_base + LB_tip) / 2); SEAM = seam
SCREEN = Vector(sc["SCREEN"]) + Vector((0.0, 0, 0.06))
ENC = BIRD_E; HEADE = BIRD_E + Vector((0, 0.03, 0.25))
K = [  # frame, position, target, lens, focus target(None = target)
 (1, Vector((1.3, 2.0, 0.75)), HEADJ + Vector((0, 0, -0.05)), 22),
 (34, Vector((0.95, 1.35, 1.45)), HEADJ, 26),
 (64, STK(-48) + Vector((0.42, 0.12, 0.05)), STK(-48) * 0.4 + BEAKJ * 0.6, 28),
 (90, STK(-14) + Vector((0.36, 0.14, 0.02)), BEAKJ, 32),
 (104, BEAKJ + Vector((0.34, 0.12, 0.06)), BEAKJ, 38),
 (135, BEAKJ + Vector((0.12, 0.34, 0.08)), BEAKJ + Vector((0, 0.1, 0.02)), 45),
 (175, BEAKJ + Vector((-0.16, 0.30, 0.02)), BEAKJ + Vector((0, 0.18, -0.04)), 52),
 (215, BIRD_J + Vector((-0.65, 0.75, 0.42)), HEADJ, 32),
 (255, BIRD_J + Vector((-0.45, 0.9, 0.18)), HEADJ + Vector((0, 0, -0.04)), 30),
 (300, HEADJ + Vector((0.28, 0.36, -0.16)), FIG0, 32),
 (345, BIRD_J + Vector((0.78, 0.18, 0.26)), (HEADJ + FIG0) / 2, 36),
 (395, FIG0 + Vector((0.12, 0.06, 0.62)), FIG0 + Vector((0, 0.05, -0.35)), 24),
 (445, BIRD_J + Vector((0.55, 0.62, 0.32)), HEADJ, 40),
 (495, BIRD_J + Vector((1.0, 0.25, 0.25)), HEADJ, 34),
 (528, Vector((2.3, 0.0, 1.62)), Vector((4.6, 0, 1.5)), 22),
 (552, Vector((3.85, 0.0, 1.55)), BC + Vector((0, 0, 0.1)), 22),
 (592, Vector((5.55, -0.45, 1.45)), BC + Vector((0, 0, 0.15)), 28),
 (636, BEAKC + Vector((-0.36, 0.26, 0.22)), BEAKC, 36),
 (672, BEAKC + Vector((-0.22, 0.14, 0.12)), BEAKC, 42),
 (705, Vector((8.1, 0.65, 1.38)), SCREEN, 30),
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
 (1360, V3 + Vector((-1.0, 0.65, 0.45)), V3, 30),
 (1410, V3 + Vector((-0.9, -0.2, 0.25)), V3 + Vector((0.05, 0.1, -0.05)), 34),
 (1460, P3 + Vector((-1.2, 1.0, 1.75)), P3 + Vector((0, 0, 1.0)), 32),
 (1500, P3 + Vector((-1.6, 1.8, 1.7)), SCREEN, 28),
 (1530, SCREEN + Vector((0.45, 0, 0.0)), SCREEN + Vector((-1, 0, 0)), 30),
 (1552, SCREEN + Vector((-0.5, -0.1, 0.05)), BEAKC, 30),
 (1600, BEAKC + Vector((-0.2, -0.16, 0.1)), SEAM, 48),
 (1650, BEAKC + Vector((-0.26, 0.02, 0.05)), SEAM, 55),
 (1700, BEAKC + Vector((-0.18, -0.2, 0.12)), SEAM, 52),
 (1750, SEAM + Vector((-0.1, -0.1, 0.08)), SEAM, 62),
 (1800, SEAM + Vector((-0.26, -0.16, 0.18)), SEAM + Vector((0, 0.04, 0.01)), 45),
 (1870, BC + Vector((-0.95, -0.25, 0.62)), BC + Vector((0, 0.1, 0.35)), 28),
 (1925, Vector((4.9, -0.25, 1.5)), BC + Vector((0, 0, 0.3)), 24),
 (1957, Vector((3.65, -0.1, 1.55)), BC + Vector((0, 0, 0.3)), 22),
 (1976, Vector((2.35, -0.5, 1.5)), HEADE + Vector((0, 0, 0.1)), 24),
 (2010, ENC + Vector((0.95, 0.3, 0.3)), HEADE, 34),
 (2070, ENC + Vector((0.72, 0.72, 0.16)), HEADE + Vector((0, 0.1, -0.05)), 36),
 (2130, ENC + Vector((0.1, 0.95, 0.3)), HEADE, 36),
 (2195, ENC + Vector((-0.35, 0.85, 0.32)), HEADE, 34),
 (2250, ENC + Vector((-0.45, 0.78, 0.36)), HEADE, 34),
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
json.dump([[k[0], list(k[1]), list(k[2]), k[3]] for k in K], open(os.path.join(HERE, "camera_keys.json"), "w"))
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=out)
print("ANIM_DONE", out)
