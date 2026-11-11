"""Characters, props and effects animation. blender -b work/sets.blend --python 03_animate.py -- work/anim.blend
Beat start frames (60 fps): 1, 127, 343, 565, 775, 1063, 1309, 1501, 1645; end 1770."""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion, Euler
HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[sys.argv.index("--") + 1]
R_ = math.radians
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
exec(open(os.path.join(HERE, "lib_human.py")).read())
sc = bpy.context.scene
sc.render.fps = 60; sc.render.fps_base = 1.0; sc.frame_start, sc.frame_end = 1, 1770
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
random.seed(11)
OB = bpy.data.objects
B = dict(b1=1, b2=127, b3=343, b4=565, b5=775, b6=1063, b7=1309, b8=1501, b9=1645, end=1770)
C_PROP = bpy.data.collections["Props"]

def newmat(name, col, rough=0.5, sss=0.0, emit=None, alpha=1.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    if sss: b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Scale"].default_value = 0.01
    if emit: b.inputs["Emission Color"].default_value = (*emit[0], 1); b.inputs["Emission Strength"].default_value = emit[1]
    if alpha < 1: b.inputs["Alpha"].default_value = alpha
    if coat: b.inputs["Coat Weight"].default_value = coat
    return m

def key_vis(o, f, on):
    o.hide_render = not on; o.hide_viewport = not on
    o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)

def set_interp(obj_or_data, kind='CONSTANT', path=None):
    ad = obj_or_data.animation_data
    if not ad or not ad.action: return
    for layer in ad.action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    if path is None or fc.data_path == path:
                        for kp in fc.keyframe_points: kp.interpolation = kind

def smoothstep(a, b, x):
    return smooth((x - a) / (b - a)) if b != a else float(x >= a)

# ================================================================== chair tilt rig
tilt = OB.new("ChairTilt", None) if False else bpy.data.objects.new("ChairTilt", None)
bpy.data.collections["OR_Set"].objects.link(tilt); tilt.location = (0, 0.0, 0.55)
for n in ("Chair_Seat", "Chair_LegRest", "Chair_BackPivot", "Chair_Arm0", "Chair_Arm1", "Chair_ArmPost0", "Chair_ArmPost1",
          "ArmBoard", "ArmBoard_Drape"):
    o = OB[n]; M = o.matrix_world.copy(); o.parent = tilt; o.matrix_parent_inverse = tilt.matrix_world.inverted()
for n in ("ArmBoard_Post", "ArmBoard_Foot"): bpy.data.objects.remove(OB[n])
# bracket from the left chair arm to the arm board
o = bpy.data.objects["ArmBoard"]
TILT_UP, TILT_REC = 0.0, -32.0
def key_tilt(f, deg):
    tilt.rotation_euler = (R_(deg), 0, 0); tilt.keyframe_insert("rotation_euler", index=0, frame=f)
for f, d in ((1, TILT_UP), (175, TILT_UP), (300, TILT_REC), (B["b9"] + 10, TILT_REC), (B["b9"] + 75, TILT_UP), (B["end"], TILT_UP)):
    key_tilt(f, d)

# ================================================================== people
PAT = Person(OB["Patient"]); SUR = Person(OB["Surgeon"]); NUR = Person(OB["Nurse"])
pr = PAT.o; M = pr.matrix_world.copy(); pr.parent = tilt; pr.matrix_parent_inverse = tilt.matrix_world.inverted()
for s in "LR":
    PAT.R.PB["lowerleg02." + s].constraints[0].influence = 0.0   # FK seated legs
SEAT = Vector((0, 0.0, 0.66))
LEGS = {"L": (88, 6, 92, 5), "R": (88, 6, 92, 5)}

# --- patient ear removed (shape key from the mixed shape), bandage on the left ear
body = PAT.body; kb = body.data.shape_keys.key_blocks
mix = [Vector(v.co) for v in body.data.vertices]
for k in kb[1:]:
    if k.value > 0 and not k.name.startswith("X_"):
        for i, (a, c) in enumerate(zip(k.data, kb[0].data)): mix[i] += (a.co - c.co) * k.value
eg = body.shape_key_add(name="EarGone", from_mix=False)
EAR_IDS = [i for i, m in enumerate(mix) if m.x > 0.074 and 1.58 < m.z < 1.765 and -0.085 < m.y < 0.06]
for i in EAR_IDS:
    m = mix[i]; t = Vector((0.074 + (m.x - 0.074) * 0.08, m.y, m.z))
    eg.data[i].co = kb[0].data[i].co + (t - m)
eg.value = 1.0
EAR_C = sum((mix[i] for i in EAR_IDS), Vector()) / len(EAR_IDS)   # rest armature space centre of the old ear
print("EAR_C", EAR_C, len(EAR_IDS))
HEAD_REST = PAT.R.BN["head"].matrix_local.copy()
def attach_bone(o, person, bone, M_rest_world):
    """parent o to a bone so that at rest pose it sits at M_rest_world (armature space)"""
    o.parent = person.o; o.parent_type = 'BONE'; o.parent_bone = bone
    bm_ = person.R.BN[bone].matrix_local; L = person.R.BN[bone].length
    o.matrix_parent_inverse = Matrix.Identity(4)
    o.matrix_basis = (Matrix.Translation((0, L, 0)).inverted() @ bm_.inverted()) @ M_rest_world
M_GAUZE = bpy.data.materials["Gauze"]
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, segments=24, ring_count=12); pad = bpy.context.object; pad.name = "Bandage_Pad"
pad.scale = (0.35, 0.8, 1.0); bpy.ops.object.transform_apply(scale=True); bpy.ops.object.shade_smooth(); pad.data.materials.append(M_GAUZE)
attach_bone(pad, PAT, "head", Matrix.Translation(EAR_C + Vector((0.004, 0, 0))))
bpy.ops.mesh.primitive_torus_add(major_radius=0.098, minor_radius=0.012, major_segments=48, minor_segments=8); band = bpy.context.object; band.name = "Bandage_Wrap"
band.scale = (0.97, 1.16, 1.0); bpy.ops.object.transform_apply(scale=True); band.data.materials.append(M_GAUZE); bpy.ops.object.shade_smooth()
attach_bone(band, PAT, "head", Matrix.Translation(Vector((0, -0.005, EAR_C.z + 0.035))) @ Matrix.Rotation(R_(-25), 4, 'Y') @ Matrix.Rotation(R_(10), 4, 'X'))
for o in (pad, band):
    for c in list(o.users_collection): c.objects.unlink(o)
    C_PROP.objects.link(o); key_vis(o, 1, True); key_vis(o, 900, False)

def pat_up(f, face=None, head=(0, 0, 0), spine=(6, 0, 0)):
    PAT.key_body(f, SEAT, pitch=-8, spine=spine, head=head, legs=LEGS)
def pat_rec(f, head=(4, -28, 6), breath=0.0):
    PAT.key_body(f, SEAT, pitch=-10, spine=(2 + breath, 0, 0), head=head, legs=LEGS)
ARM_R = ((-0.32, -0.12, 0.77), (0, -1, -0.15), (0, 0, -1))
ARM_L_REST = ((0.32, -0.12, 0.77), (0, -1, -0.15), (0, 0, -1))
EARHAND_W = EAR_C + Vector((0.02, -0.075, -0.33))   # seated: head is 0.304 lower than rest
ARM_L_BOARD = ((0.74, -0.04, 1.03), (1, -0.15, 0.0), (0, 0, 1))   # palm up on the arm board (tilt frame)
# beat 1: shock. Head jolts back, hand flies up toward the dressing, then settles
pat_up(1, head=(0, -8, 0)); pat_up(18, head=(-6, -12, 3), spine=(2, 0, 0)); pat_up(40, head=(-10, -18, 4), spine=(-2, 2, 0))
pat_up(80, head=(-4, -22, 6), spine=(4, 3, 4)); pat_up(126, head=(-2, -16, 4), spine=(6, 2, 2)); pat_up(165, head=(0, -4, 0))
for f, a in ((1, ARM_L_REST), (22, ARM_L_REST)): PAT.key_hand("L", f, *a)
PAT.key_hand("L", 44, EARHAND_W + Vector((0.08, -0.08, -0.05)), (-0.2, 0.3, 1.0), (-1, 0, 0.2))
PAT.key_hand("L", 70, EARHAND_W, (-0.25, 0.35, 1.0), (-1, 0, 0.1))
PAT.key_hand("L", 110, EARHAND_W + Vector((0.005, 0.005, -0.004)), (-0.25, 0.35, 1.0), (-1, 0, 0.1))
PAT.key_hand("L", 150, EARHAND_W + Vector((0.12, -0.06, -0.2)), (0.2, -0.6, -0.5), (0, 0, -1))
PAT.key_hand("L", 200, ARM_L_REST[0], ARM_L_REST[1], ARM_L_REST[2])
PAT.key_hand("L", 300, *ARM_L_BOARD); PAT.key_hand("L", B["b9"] + 15, *ARM_L_BOARD)
for f in (1, 300, B["b9"]): PAT.key_hand("R", f, *ARM_R)
PAT.key_fingers("L", 1, 18); PAT.key_fingers("L", 50, 8, 10); PAT.key_fingers("L", 150, 15); PAT.key_fingers("L", 300, 25, 15)
PAT.key_fingers("R", 1, 22); PAT.key_fingers("R", 30, 45, 30); PAT.key_fingers("R", 150, 22)
N0 = FACE_NEUTRAL()
PAT.face(1, **dict(N0, eye_left_opened_up=0.4, eye_right_opened_up=0.4))
SHOCK = dict(N0, eye_left_opened_up=1, eye_right_opened_up=1, eyebrows_left_up=1, eyebrows_right_up=1, eyebrows_left_inner_up=0.8,
             eyebrows_right_inner_up=0.8, mouth_open=0.75)
PAT.face(14, **SHOCK); PAT.face(100, **dict(SHOCK, mouth_open=0.45, mouth_depression=0.4)); PAT.face(160, **dict(N0, eyebrows_left_inner_up=0.5, eyebrows_right_inner_up=0.5))
SLEEP = dict(N0, eye_left_closure=1, eye_right_closure=1)
PAT.face(260, **SLEEP); PAT.face(B["b9"] + 20, **SLEEP)
SMILE = dict(N0, mouth_corner_puller=1.0, mouth_upward_retraction=0.5, eye_left_slit=0.35, eye_right_slit=0.35, eyebrows_left_up=0.3, eyebrows_right_up=0.3)
PAT.face(B["b9"] + 45, **dict(N0, eye_left_opened_up=0.3, eye_right_opened_up=0.3)); PAT.face(B["b9"] + 75, **SMILE); PAT.face(B["end"], **SMILE)
# reclined: breathing and a slow head roll; head turned to the right so the left ear faces the surgeon
for f in range(300, B["b9"], 120):
    pat_rec(f, breath=0.0); pat_rec(f + 60, breath=1.5)
pat_rec(B["b9"] + 10)
# beat 9: sits up, turns to camera, left hand comes up and touches the new ear, big smile
pat_up(B["b9"] + 75, head=(-2, -8, 0)); pat_up(B["b9"] + 100, head=(-4, -14, 3), spine=(4, 2, 3)); pat_up(B["end"], head=(-5, -10, 2), spine=(5, 1, 2))
EAR_TOUCH = EAR_C + Vector((0.035, -0.07, -0.36))
PAT.key_hand("L", B["b9"] + 60, *ARM_L_REST)
PAT.key_hand("L", B["b9"] + 92, EAR_TOUCH + Vector((0.05, -0.05, -0.08)), (-0.2, 0.35, 1.0), (-1, 0.1, 0.1))
PAT.key_hand("L", B["b9"] + 108, EAR_TOUCH, (-0.25, 0.4, 1.0), (-1, 0.1, 0.1))
PAT.key_hand("L", B["end"], EAR_TOUCH + Vector((0.003, 0.004, 0.006)), (-0.25, 0.4, 1.0), (-1, 0.1, 0.1))
PAT.key_fingers("L", B["b9"] + 60, 20); PAT.key_fingers("L", B["b9"] + 100, 6, 10)

def ev_at(f):
    sc.frame_set(f); bpy.context.view_layer.update()
def pw(person, bone, f, head=True):
    ev_at(f); return person.wpos(bone, head)
def pat_world(f, local):
    """armature-space point of the patient -> world at frame f"""
    ev_at(f); return pr.matrix_world @ Vector(local)

# arm board: put the board directly under the reclined forearm
ev_at(400)
el = pr.matrix_world @ PAT.R.PB["lowerarm01.L"].head; wr = pr.matrix_world @ PAT.R.PB["wrist.L"].head
ab = OB["ArmBoard"]; mid = (el + wr) / 2
tilt_inv = tilt.matrix_world.inverted()
ab_local = tilt_inv @ (mid + Vector((0, 0, -0.05)))
ab.matrix_parent_inverse = Matrix.Identity(4); ab.location = ab_local; ab.rotation_euler = (0, 0, math.atan2((wr - el).y, (wr - el).x))
ad_ = OB["ArmBoard_Drape"]; ad_.matrix_parent_inverse = Matrix.Identity(4); ad_.location = ab_local + Vector((0, 0, 0.023)); ad_.rotation_euler = ab.rotation_euler
print("FOREARM", el, wr)

# --- key points on the patient (world, reclined) used by the surgeon
FA_LOCAL = lambda u: None
ev_at(600)
EL = pr.matrix_world @ PAT.R.PB["lowerarm01.L"].head; WR = pr.matrix_world @ PAT.R.PB["wrist.L"].head
INC = EL.lerp(WR, 0.45) + Vector((0, 0, 0.032))   # incision point on the volar forearm (palm-up -> top)
FA_DIR = (WR - EL).normalized()
HM = pr.matrix_world @ PAT.R.PB["head"].matrix @ Matrix.Translation((0, -PAT.R.BN["head"].length, 0)) @ HEAD_REST.inverted()  # rest arm. -> world (head)
EAR_W = HM @ EAR_C
EAR_OUT = (HM.to_3x3() @ Vector((1, 0, 0))).normalized()
print("INC", INC, "EAR_W", EAR_W, "EAR_OUT", EAR_OUT)

# ================================================================== surgeon
SH = Human(SUR.R)
def yaw_to(v):
    return math.degrees(math.atan2(v.x, -v.y))
def stand(P, f, pos, yaw, flex=0.0, crouch=0.0, spine=(0, 0, 0), head=(0, 0, 0), side=0.0):
    p = Vector(pos)
    P.key_body(f, Vector((p.x, p.y, P.root_head.z - 0.02 - crouch)), yaw=yaw, pitch=flex * 0.4, spine=spine, head=head)
    H = Human(P.R)
    for s in "LR":
        H.key_foot(s, f, H.foot_xy(s, Vector((p.x, p.y, 0)), yaw), yaw)
def walk(P, a, b, f0, f1, yaw0, yaw1, stride=0.55):
    H = Human(P.R); A, Bv = Vector(a), Vector(b)
    path = lambda f: A.lerp(Bv, smooth((f - f0) / (f1 - f0))).to_3d()
    yawf = lambda f: yaw0 + (yaw1 - yaw0) * smooth((f - f0) / (f1 - f0))
    H.walk(path, yawf, f0, f1, stride=stride, lift=0.07, bob=0.015, crouch=0.03, lean=4.0, step=2)

SA_ = Vector((-0.5, -0.42)); yA = yaw_to(Vector((0, -0.05)) - SA_)
ST = Vector((1.05, -0.32)); yT = 0.0
SB_ = Vector((INC.x - 0.02, INC.y + 0.42)); yB = 0.0
SC_ = Vector((EAR_W.x + 0.22, EAR_W.y + 0.5)); yC = yaw_to(EAR_W.to_2d() - Vector((EAR_W.x + 0.22, EAR_W.y + 0.5)))
stand(SUR, 1, SA_, yA, head=(10, 0, 0)); stand(SUR, 60, SA_, yA, spine=(6, 0, 0), head=(14, 0, 0)); stand(SUR, 128, SA_, yA, spine=(14, 0, 4), head=(18, 0, 0), crouch=0.03)
stand(SUR, 160, SA_, yA, spine=(8, 0, 0))
stand(SUR, 199, SA_, yA, spine=(8, 0, 0)); stand(SUR, 200, ST, yT, spine=(18, 0, 0))
stand(SUR, 330, ST, yT, spine=(18, 0, 0), head=(28, 0, 0), crouch=0.02)
for f in range(343, 565, 40):
    stand(SUR, f, ST, yT, spine=(20 + 3 * math.sin(f), 2 * math.sin(f * 0.3), 3 * math.sin(f * 0.2)), head=(30, 4 * math.sin(f * 0.1), 0), crouch=0.03)
stand(SUR, 566, ST, yT, spine=(18, 0, 0)); stand(SUR, 590, ST + Vector((-0.1, 0.25)), 60, spine=(6, 0, 0)); walk(SUR, ST + Vector((-0.1, 0.25)), Vector((1.0, 0.75)), 591, 625, 60, 100, stride=0.45); walk(SUR, Vector((1.0, 0.75)), SB_, 626, 660, 100, yB, stride=0.4)
for f in range(662, 1309, 60):
    stand(SUR, f, SB_, yB, spine=(22 + 2 * math.sin(f * 0.05), 0, 2 * math.sin(f * 0.07)), head=(30, 0, 0), crouch=0.04)
walk(SUR, SB_, SC_, 1312, 1385, yB, yC + 360 if False else yC - 0.0 if abs(yB - yC) < 180 else yC + 360, stride=0.5)
for f in range(1395, B["b9"], 50):
    stand(SUR, f, SC_, yC + 360 if abs(yB - (yC + 360)) < abs(yB - yC) else yC, spine=(26, 0, 0), head=(32, 0, 0), crouch=0.05)
yCC = yC + 360 if abs(yB - (yC + 360)) < abs(yB - yC) else yC
stand(SUR, B["b9"] + 20, SC_, yCC, spine=(14, 0, 0), head=(18, 0, 0))
stand(SUR, B["b9"] + 70, SC_ + Vector((0.35, 0.15)), yCC, spine=(4, 0, 0), head=(6, 0, 0))
stand(SUR, B["end"], SC_ + Vector((0.37, 0.15)), yCC, spine=(2, 0, -6), head=(4, 8, 0))

# surgeon hands. Block/ear positions on the tray
TRAY = OB["Tray"].matrix_world.translation.copy()
BLK = TRAY + Vector((-0.02, -0.02, 0.035))
def sh(f, s, W, d, n, pole=None): SUR.key_hand(s, f, W, d, n, pole)
# beat 1: hands together in front, then R hand to the patient's chest on "A surgeon takes"
CHEST = pat_world(130, (0.08, -0.16, 1.02))
for f in (1, 60):
    ev_at(f); c = SUR.wpos("spine03")
    fwd = Matrix.Rotation(R_(yA), 3, 'Z') @ Vector((0, -1, 0))
    sh(f, "L", c + fwd * 0.25 + Vector((0.05, 0, -0.12)), fwd + Vector((0, 0, -0.3)), Vector((0, 0, 1)).cross(fwd))
    sh(f, "R", c + fwd * 0.27 + Vector((-0.02, 0, -0.1)), fwd + Vector((0, 0, -0.3)), -Vector((0, 0, 1)).cross(fwd))
sh(100, "R", CHEST + Vector((-0.1, -0.14, 0.05)), (0.6, 0.6, -0.4), (-0.4, -0.5, 0.6))
sh(128, "R", CHEST + Vector((-0.02, -0.035, 0.0)), (0.6, 0.6, -0.3), (-0.4, -0.6, 0.5))
sh(199, "R", CHEST + Vector((-0.02, -0.04, 0.0)), (0.6, 0.6, -0.3), (-0.4, -0.6, 0.5))
# beat 3: carving at the tray. L holds the block, R draws the scalpel over it in strokes
for f in range(300, 565, 6):
    k = (f - 343) / 37.0
    sh(f, "L", BLK + Vector((-0.075, 0.03, 0.02)), (0.9, -0.1, -0.3), (0.0, 0.3, 1.0))
    ph = (k % 1.0)
    sweep = Vector((0.03 - 0.06 * ph, -0.02 + 0.01 * math.sin(k * 2.3), 0.045 - 0.025 * math.sin(math.pi * ph)))
    sh(f, "R", BLK + Vector((0.09, -0.05, 0.03)) + sweep * (1 if f > 343 else 0.2), (-0.7, 0.35, -0.5), (-0.2, -0.4, 1.0))
SUR.key_fingers("L", 300, 40, 35); SUR.key_fingers("R", 300, 55, 40)
# beat 4: R forceps carries the ear to the forearm, slides it in; L forceps lifts the skin edge
ev_at(640)
sh(570, "R", BLK + Vector((0.05, -0.04, 0.08)), (-0.6, 0.4, -0.5), (-0.2, -0.4, 1.0))
sh(610, "R", INC + Vector((-0.08, 0.2, 0.15)), (-0, -1, -0.4), (-0, -0.2, 1))
sh(650, "R", INC + Vector((-0.07, 0.16, 0.07)), (0.2, -1, -0.5), (-0, -0.4, 1))
sh(700, "R", INC + Vector((-0.04, 0.13, 0.05)), (0.3, -1, -0.6), (-0, -0.4, 1))
sh(740, "R", INC + Vector((-0.06, 0.15, 0.07)), (0.3, -1, -0.6), (-0, -0.4, 1))
sh(775, "R", INC + Vector((-0.12, 0.2, 0.12)), (0.2, -1, -0.4), (-0, -0.4, 1))
sh(570, "L", BLK + Vector((-0.12, 0.05, 0.1)), (0.6, 0.4, -0.5), (0.2, -0.4, 1.0))
sh(640, "L", INC + Vector((0.12, 0.12, 0.07)), (-0.4, -1, -0.5), (-0, -0.4, 1))
sh(700, "L", INC + Vector((0.1, 0.11, 0.05)), (-0.4, -1, -0.6), (-0, -0.4, 1))
sh(775, "L", INC + Vector((0.12, 0.16, 0.1)), (-0.4, -1, -0.4), (-0, -0.4, 1))
# beat 6: reopen and lift the ear out
sh(1063, "R", INC + Vector((-0.12, 0.2, 0.12)), (0.2, -1, -0.4), (-0, -0.4, 1))
sh(1120, "R", INC + Vector((-0.05, 0.135, 0.055)), (0.3, -1, -0.6), (-0, -0.4, 1))
sh(1160, "R", INC + Vector((-0.05, 0.135, 0.055)), (0.3, -1, -0.6), (-0, -0.4, 1))
sh(1240, "R", INC + Vector((-0.06, 0.17, 0.25)), (0.2, -1, -0.3), (-0, -0.3, 1))
sh(1308, "R", INC + Vector((-0.08, 0.2, 0.32)), (0.2, -1, -0.2), (-0, -0.3, 1))
sh(1063, "L", INC + Vector((0.12, 0.16, 0.1)), (-0.4, -1, -0.4), (-0, -0.4, 1))
sh(1110, "L", INC + Vector((0.1, 0.11, 0.05)), (-0.4, -1, -0.6), (-0, -0.4, 1))
sh(1250, "L", INC + Vector((0.14, 0.15, 0.08)), (-0.4, -1, -0.4), (-0, -0.4, 1))
# beat 7-8: at the head. EAR_W is where the new ear goes, EAR_OUT points away from the skull
side = EAR_OUT
def at_ear(off_out, off_fwd, off_up):
    # surgeon reaches from behind the head (+Y); off_out pushes away from the skull, off_fwd along -Y
    back = Vector((0, 1, 0))
    return EAR_W + side * (off_out * 0.35) + back * (off_out * 0.9) - back * off_fwd + Vector((0, 0, 1)) * off_up
sh(1390, "R", at_ear(0.22, -0.02, 0.12), (-0.3, -1, -0.4), (0, 0, 1))
sh(1440, "R", at_ear(0.14, 0.0, 0.07), (-0.3, -1, -0.5), (0, 0, 1))
sh(1470, "R", at_ear(0.12, 0.0, 0.06), (-0.3, -1, -0.5), (0, 0, 1))
sh(1500, "R", at_ear(0.16, 0.0, 0.1), (-0.3, -1, -0.4), (0, 0, 1))
sh(1390, "L", at_ear(0.2, -0.15, 0.08), (0.2, -1, -0.4), (0, 0, 1))
sh(1500, "L", at_ear(0.15, -0.12, 0.05), (0.2, -1, -0.5), (0, 0, 1))
# stitching: R needle holder travels along the ear base in arcs
STITCH_N = 9
for i in range(STITCH_N):
    f = 1505 + i * 15; u = i / (STITCH_N - 1)
    pt = at_ear(0.13, -0.03 + 0.06 * u, -0.025 + 0.07 * math.sin(math.pi * u))
    sh(f, "R", pt, (-0.3, -1, -0.5), (0, 0, 1)); sh(f + 8, "R", pt + Vector((0.01, 0.03, 0.04)), (-0.3, -1, -0.3), (0, 0, 1))
sh(B["b9"] + 5, "L", at_ear(0.18, -0.12, 0.05), (0.2, -1, -0.4), (0, 0, 1))
for s in "LR":
    ev_at(B["b9"] + 70)
    sh(B["b9"] + 70, s, SUR.wpos("spine04") + Vector((0.0, 0, -0.05)) + (Matrix.Rotation(R_(yCC), 3, 'Z') @ Vector(((0.12 if s == "R" else -0.12), -0.22, -0.12))),
       Matrix.Rotation(R_(yCC), 3, 'Z') @ Vector((0, -1, -0.5)), (0, 0, 1))
SUR.key_fingers("R", B["b9"] + 70, 20); SUR.key_fingers("L", B["b9"] + 70, 20)
SUR.face(1, **N0); SUR.face(B["b9"] + 60, **N0); SUR.face(B["b9"] + 90, **dict(N0, eye_left_slit=0.5, eye_right_slit=0.5, mouth_corner_puller=0.7))

# ================================================================== nurse
NH = Human(NUR.R)
for s in "LR": NUR.ik(s, 1, False)
def nurse_arms(f, swing=0.0, fwd=0.0):
    for s in "LR":
        sx = 1 if s == "L" else -1
        NUR.R.key_rot("upperarm01." + s, f, [("Y", sx * 62), ("X", -(fwd + swing * sx))])
        NUR.R.key_rot("lowerarm01." + s, f, [("X", -(20 + fwd * 0.6))])
N_A, N_B, N_C, N_D = Vector((-1.9, 1.75)), Vector((1.6, -0.15)), Vector((1.25, -0.35)), Vector((-0.75, 0.85))
walk(NUR, N_A, Vector((1.0, 1.6)), 1, 120, -90, -90, stride=0.6)
for f in range(1, 121, 18): nurse_arms(f, swing=12 * math.sin(f * 0.21))
walk(NUR, Vector((1.0, 1.6)), N_B, 121, 300, -90, -100, stride=0.6)
for f in range(121, 300, 18): nurse_arms(f, swing=12 * math.sin(f * 0.21))
for f in range(310, 565, 50):
    stand(NUR, f, N_B, -100 + 8 * math.sin(f * 0.02), spine=(10, 0, 0), head=(16, 0, 0)); nurse_arms(f, fwd=45 + 10 * math.sin(f * 0.05))
walk(NUR, N_B, N_C, 570, 700, -100, -150, stride=0.5)
for f in range(570, 700, 18): nurse_arms(f, swing=10 * math.sin(f * 0.21))
for f in range(710, 1309, 60):
    stand(NUR, f, N_C, -150, spine=(8, 0, 0), head=(18, 0, 0)); nurse_arms(f, fwd=55)
walk(NUR, N_C, N_D, 1312, 1440, -150, -150, stride=0.55)
for f in range(1312, 1440, 18): nurse_arms(f, swing=10 * math.sin(f * 0.21))
for f in range(1450, B["end"] + 1, 60):
    stand(NUR, f, N_D, -150, spine=(6, 0, 0), head=(12, 0, 0)); nurse_arms(f, fwd=40 if f < B["b9"] else 70)
for f in range(B["b9"] + 60, B["end"], 12):   # little clap
    nurse_arms(f, fwd=70 + (6 if (f // 12) % 2 else -2))
NUR.face(1, **N0); NUR.face(B["b9"] + 50, **N0); NUR.face(B["b9"] + 80, **SMILE)

# ================================================================== surgeon look: gloves, cap, mask
M_GLOVE = newmat("NitrileGlove", (0.18, 0.35, 0.75), 0.35, sss=0.05, coat=0.2)
sb = SUR.body; sb.data.materials.append(M_GLOVE); gi = len(sb.data.materials) - 1
hand_groups = [g.index for g in sb.vertex_groups if g.name.startswith(("wrist.", "finger", "metacarpal"))]
for p in sb.data.polygons:
    w = 0.0
    for vi in p.vertices:
        for g in sb.data.vertices[vi].groups:
            if g.group in hand_groups: w += g.weight
    if w / len(p.vertices) > 0.5: p.material_index = gi
HEADW = SUR.R.BN["head"].head_local
M_CAP = newmat("ScrubCap", (0.15, 0.45, 0.5), 0.8); M_MASK = newmat("SurgMask", (0.55, 0.75, 0.85), 0.8)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.105, segments=32, ring_count=16); cap = bpy.context.object; cap.name = "Surgeon_Cap"
for v in cap.data.vertices:
    if v.co.z < -0.01: v.co.z = -0.01 + (v.co.z + 0.01) * 0.1
cap.scale = (0.92, 1.02, 0.85); bpy.ops.object.transform_apply(scale=True); bpy.ops.object.shade_smooth(); cap.data.materials.append(M_CAP)
attach_bone(cap, SUR, "head", Matrix.Translation(HEADW + Vector((0, 0.01, 0.12))))
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, segments=32, ring_count=16); mk = bpy.context.object; mk.name = "Surgeon_Mask"
bm = bmesh.new(); bm.from_mesh(mk.data)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y > -0.02 or v.co.z > 0.045 or v.co.z < -0.07], context='VERTS'); bm.to_mesh(mk.data); bm.free()
mk.scale = (0.78, 1.05, 1.0); bpy.ops.object.transform_apply(scale=True); bpy.ops.object.shade_smooth(); mk.data.materials.append(M_MASK)
mk.modifiers.new("solid", 'SOLIDIFY').thickness = 0.003
attach_bone(mk, SUR, "head", Matrix.Translation(HEADW + Vector((0, 0.005, 0.03))))
for o in (cap, mk):
    for c in list(o.users_collection): c.objects.unlink(o)
    C_PROP.objects.link(o)

# ================================================================== cartilage block -> ear, shavings (beat 3) on the tray
M_CART = bpy.data.materials["Cartilage"]
ear_src = OB["Ear_Src"]
def ear_copy(name, mat_):
    o = ear_src.copy(); o.data = ear_src.data.copy(); o.name = name; C_PROP.objects.link(o)
    o.data.materials.clear(); o.data.materials.append(mat_); return o
EAR_FLAT = Matrix.Rotation(R_(90), 4, 'X')   # ear lies flat (front face up) on the tray
ear_real = ear_copy("Ear_Cartilage", M_CART)
ear_real.matrix_world = Matrix.Translation(BLK + Vector((0, 0, -0.025))) @ EAR_FLAT
blk = bpy.data.objects.new("Cart_Block", bpy.data.meshes.new("Cart_Block")); C_PROP.objects.link(blk)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(blk.data); bm.free()
blk.data.materials.append(M_CART); blk.modifiers.new("bev", 'BEVEL').width = 0.006
blk.location = BLK + Vector((0, 0, -0.01)); blk.scale = (0.05, 0.072, 0.03)
blk.keyframe_insert("scale", frame=343)
for f, s_ in ((420, (0.047, 0.068, 0.022)), (480, (0.043, 0.064, 0.014)), (540, (0.04, 0.06, 0.006))):
    blk.scale = s_; blk.keyframe_insert("scale", frame=f)
key_vis(blk, 1, True); key_vis(blk, 545, False)
key_vis(ear_real, 1, False); key_vis(ear_real, 400, True)
ear_real.scale = (0.85, 0.85, 0.3); ear_real.keyframe_insert("scale", frame=400)
ear_real.scale = (1, 1, 1); ear_real.keyframe_insert("scale", frame=540)
M_SHAV = M_CART
for i in range(28):
    bpy.ops.mesh.primitive_torus_add(major_radius=random.uniform(0.003, 0.006), minor_radius=0.0012, major_segments=10, minor_segments=4)
    t = bpy.context.object; t.name = "Shaving%d" % i; t.data.materials.append(M_SHAV); bpy.ops.object.shade_smooth()
    for c in list(t.users_collection): c.objects.unlink(t)
    C_PROP.objects.link(t)
    f0 = 350 + i * 7; land = TRAY + Vector((random.uniform(-0.1, 0.12), random.uniform(-0.15, 0.13), 0.009))
    st = BLK + Vector((random.uniform(-0.02, 0.02), random.uniform(-0.03, 0.03), 0.015))
    apex = st.lerp(land, 0.5) + Vector((0, 0, random.uniform(0.05, 0.12)))
    key_vis(t, 1, False); key_vis(t, f0, True)
    for j in range(0, 19, 3):
        u = j / 18; p = (1 - u) ** 2 * st + 2 * (1 - u) * u * apex + u * u * land
        t.location = p; t.rotation_euler = (u * 9 + i, u * 6, i); t.keyframe_insert("location", frame=f0 + j); t.keyframe_insert("rotation_euler", frame=f0 + j)
    t.rotation_euler = (math.pi / 2, 0, i); t.keyframe_insert("rotation_euler", frame=f0 + 19)

# ================================================================== forearm skin pocket (beats 4-6)
M_SKINPATCH = newmat("ArmSkinPatch", (0.62, 0.42, 0.33), 0.5, sss=0.25)
# radial alpha so the patch blends into the arm skin
nt = M_SKINPATCH.node_tree; bsdf = nt.nodes["Principled BSDF"]
tc = nt.nodes.new("ShaderNodeTexCoord"); gr = nt.nodes.new("ShaderNodeTexGradient"); gr.gradient_type = 'SPHERICAL'
mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); mpS = mp
mp.inputs["Scale"].default_value = (12.0, 22.0, 22.0)
nt.links.new(mp.outputs["Vector"], gr.inputs["Vector"])
cr = nt.nodes.new("ShaderNodeMapRange"); cr.inputs["From Min"].default_value = 0.0; cr.inputs["From Max"].default_value = 0.35
nt.links.new(gr.outputs["Fac"], cr.inputs["Value"]); nt.links.new(cr.outputs["Result"], bsdf.inputs["Alpha"])
bpy.ops.mesh.primitive_grid_add(x_subdivisions=60, y_subdivisions=30, size=1.0); patch = bpy.context.object; patch.name = "Arm_Pocket"
patch.scale = (0.17, 0.09, 1); bpy.ops.object.transform_apply(scale=True); bpy.ops.object.shade_smooth()
patch.data.materials.append(M_SKINPATCH)
for c in list(patch.users_collection): c.objects.unlink(patch)
C_PROP.objects.link(patch)
# bump: displace by a soft dome (vertex group weights), keyed strength
vg = patch.vertex_groups.new(name="bump")
for v in patch.data.vertices:
    r = math.sqrt((v.co.x / 0.04) ** 2 + (v.co.y / 0.026) ** 2)
    if r < 1: vg.add([v.index], (1 - r * r) ** 1.5, 'REPLACE')
sw = patch.modifiers.new("wrap", 'SHRINKWRAP'); sw.target = PAT.body; sw.wrap_method = 'NEAREST_SURFACEPOINT'; sw.offset = 0.0012
dp = patch.modifiers.new("bump", 'DISPLACE'); dp.vertex_group = "bump"; dp.mid_level = 0.0; dp.direction = 'NORMAL'
dp.strength = 0.0
attach_m = (pr.matrix_world.inverted())  # placeholder
ev_at(600)
LA = PAT.R.PB["lowerarm01.L"]
Mfa = pr.matrix_world @ LA.matrix
up_w = Vector((0, 0, 1))
xw = FA_DIR; yw = up_w.cross(xw).normalized(); zw = xw.cross(yw)
Mp = Matrix((xw, yw, zw)).transposed().to_4x4(); Mp.translation = INC - zw * 0.004
patch.parent = pr; patch.parent_type = 'BONE'; patch.parent_bone = "lowerarm01.L"
patch.matrix_parent_inverse = Matrix.Identity(4)
patch.matrix_world = Mp
patch.matrix_parent_inverse = (pr.matrix_world @ LA.matrix @ Matrix.Translation((0, LA.length, 0))).inverted() @ Mp @ patch.matrix_basis.inverted() if False else patch.matrix_parent_inverse
key_vis(patch, 1, False); key_vis(patch, 300, True); key_vis(patch, 1400, False)
for f, s_ in ((1, 0.0), (700, 0.0), (760, 0.010), (1063, 0.010), (1110, 0.012), (1200, 0.002), (1250, 0.0)):
    dp.strength = s_; dp.keyframe_insert("strength", frame=f)
# incision: a dark-pink slit that opens and closes
M_SLIT = newmat("Incision", (0.45, 0.08, 0.1), 0.35, sss=0.3)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=24, ring_count=12); slit = bpy.context.object; slit.name = "Incision"
slit.data.materials.append(M_SLIT); bpy.ops.object.shade_smooth()
for c in list(slit.users_collection): c.objects.unlink(slit)
C_PROP.objects.link(slit)
slit.parent = patch; slit.location = (-0.035, 0, 0.0005); slit.rotation_euler = (0, 0, R_(90))
for f, w in ((1, 0.0), (620, 0.0), (640, 0.001), (660, 0.006), (720, 0.007), (760, 0.0015), (1063, 0.0012), (1090, 0.007), (1240, 0.007), (1270, 0.0015)):
    slit.scale = (0.022, w + 0.0004, 0.0015); slit.keyframe_insert("scale", frame=f)
# "x-ray": patch turns glassy at the start of beat 5 and shows the ear under the skin
mixA = nt.nodes.new("ShaderNodeMath"); mixA.operation = 'MULTIPLY'; mixA.inputs[1].default_value = 1.0
nt.links.new(cr.outputs["Result"], mixA.inputs[0]); nt.links.new(mixA.outputs[0], bsdf.inputs["Alpha"])
for f, v in ((1, 1.0), (780, 1.0), (815, 0.35), (1063, 0.35), (1080, 1.0)):
    mixA.inputs[1].default_value = v; mixA.inputs[1].keyframe_insert("default_value", frame=f)
xray_emit = bsdf.inputs["Emission Strength"]; bsdf.inputs["Emission Color"].default_value = (0.4, 0.8, 1.0, 1)
for f, v in ((1, 0.0), (780, 0.0), (815, 0.6), (1063, 0.6), (1080, 0.0)):
    xray_emit.default_value = v; xray_emit.keyframe_insert("default_value", frame=f)
# ear inside the arm (scaled into the pocket); turns from cartilage to pink skin in beat 6
M_EARPINK = newmat("EarSkin", (0.72, 0.45, 0.38), 0.45, sss=0.3)
ear_arm = ear_copy("Ear_InArm", M_CART)
M_EARPINK_N = M_EARPINK

# ================================================================== carried ear (forceps) and the grafted ear on the head
ear_new = ear_copy("Ear_New", M_EARPINK)
# ear plane faces +X on the head: model is flat in Y, rotate so its face points along EAR_OUT
EAR_ON_HEAD_REST = Matrix.Translation(EAR_C + Vector((0.006, -0.004, 0.0))) @ Matrix.Rotation(R_(90), 4, 'Z') @ Matrix.Rotation(R_(8), 4, 'X')
# forceps: tips at local origin? our forceps run along +Y from 0 to 0.13; tip at y=0.13
forc = OB["Forceps"]; forc2 = OB["Forceps_Nurse"]; scal = OB["Scalpel"]; nh = OB["NeedleHolder"]
for o in (forc2,): o.location = TRAY + Vector((-0.12, 0.1, 0.01)); o.rotation_euler = (0, 0, R_(80))
kd = OB["KidneyDish"]

# held-prop bake: matrix in the wrist frame
def wrist_w(person, s):
    return person.o.matrix_world @ person.R.PB["wrist." + s].matrix
G_SCAL = Matrix.Translation((0.0, 0.07, -0.025)) @ Matrix.Rotation(R_(90), 4, 'Z')
G_FORC = Matrix.Translation((0.0, 0.03, -0.02)) @ Matrix.Rotation(R_(0), 4, 'Z')
G_NH = Matrix.Translation((0.0, 0.05, -0.025))
def tip_of_forceps():
    return forc.matrix_world @ Vector((0, 0.13, 0))
FAST = []
for o in bpy.data.objects:
    if o.type == 'MESH':
        for m in o.modifiers:
            if m.type in ('SUBSURF', 'SHRINKWRAP', 'DISPLACE', 'BEVEL', 'SOLIDIFY'):
                FAST.append((m, m.show_viewport)); m.show_viewport = False
sc.frame_set(1)
scal_rest = Matrix.Translation(TRAY + Vector((0.13, 0.12, 0.012))) @ Matrix.Rotation(R_(15), 4, 'Z')
forc_rest = Matrix.Translation(TRAY + Vector((0.13, -0.13, 0.01))) @ Matrix.Rotation(R_(-10), 4, 'Z')
nh_rest = Matrix.Translation(TRAY + Vector((-0.14, -0.1, 0.01))) @ Matrix.Rotation(R_(90), 4, 'Z') @ Matrix.Rotation(R_(90), 4, 'X')
def keymat(o, f, M):
    o.matrix_world = M; o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
for o in (scal, forc, nh, ear_arm, ear_new, kd):
    o.rotation_mode = 'XYZ'
for f in list(range(1, B["end"] + 1, 2)) + [B["end"]]:
    sc.frame_set(f)
    # scalpel: held in R from 330 to 560
    keymat(scal, f, wrist_w(SUR, "R") @ G_SCAL if 330 <= f <= 562 else scal_rest)
    # forceps in R hand 566..1500
    keymat(forc, f, wrist_w(SUR, "R") @ G_FORC if 566 <= f <= 1500 else forc_rest)
    keymat(nh, f, wrist_w(SUR, "R") @ G_NH if 1502 <= f <= B["b9"] + 40 else nh_rest)
    tip = forc.matrix_world @ Vector((0, 0.13, 0))
    # the carved ear: on the tray until 566, in forceps 566..700, in the pocket 700..1120, forceps 1120..1440, head after
    pocket = patch.matrix_world @ Matrix.Translation((0, 0, -0.004)) @ Matrix.Rotation(R_(90), 4, 'X') @ Matrix.Scale(0.85, 4)
    Rf = forc.matrix_world.to_quaternion().to_matrix().to_4x4()
    if f < 566:
        Me = ear_real.matrix_world.copy() if f >= 540 else None
    if 566 <= f < 712:
        keymat(ear_arm, f, Matrix.Translation(tip) @ Rf @ Matrix.Translation((0, 0.03, 0)) @ Matrix.Rotation(R_(90), 4, 'X') @ Matrix.Scale(0.85, 4))
    elif 712 <= f < 1150:
        u = smoothstep(712, 760, f); keymat(ear_arm, f, pocket)
    else:
        keymat(ear_arm, f, pocket)
    if 1150 <= f < 1440:
        keymat(ear_new, f, Matrix.Translation(tip) @ Rf @ Matrix.Translation((0, 0.03, 0)) @ Matrix.Rotation(R_(90), 4, 'X') @ Matrix.Scale(1.0, 4))
    elif f >= 1440:
        Hm = pr.matrix_world @ PAT.R.PB["head"].matrix @ HEAD_REST.inverted()
        keymat(ear_new, f, Hm @ EAR_ON_HEAD_REST)
    else:
        keymat(ear_new, f, Matrix.Translation(Vector((0, 0, -5))))
    # kidney dish in the nurse's hands from 700 to 1309
    if 700 <= f < 1309:
        Lw = wrist_w(NUR, "L").translation; Rw_ = wrist_w(NUR, "R").translation
        keymat(kd, f, Matrix.Translation((Lw + Rw_) / 2 + Vector((0, 0, 0.03))) @ Matrix.Rotation(R_(-200 + 90), 4, 'Z'))
    else:
        keymat(kd, f, Matrix.Translation(TRAY + Vector((-0.6, 1.6, 0.02)) + Vector((1.9 - 1.05 - 0.25, 1.4 - TRAY.y - 1.6, 0.0))))
# ear_real only on the tray; hidden once lifted (ear_arm takes over). ear_arm hidden before 566, swapped for ear_new at 1150
key_vis(ear_real, 566, False)
key_vis(ear_arm, 1, False); key_vis(ear_arm, 566, True); key_vis(ear_arm, 1150, False)
# cartilage -> pink while in the arm: ear_arm material is cartilage, ear_new pink
for m, v in FAST: m.show_viewport = v
# Ear_InArm should sit in the forceps exactly where Ear_Cartilage lay (566): snap the first frames
set_interp(ear_arm, 'LINEAR'); set_interp(ear_new, 'LINEAR')

# ================================================================== vessels joining at the ear (beat 7) + glow
M_VES = newmat("Vessel", (0.55, 0.02, 0.03), 0.3, sss=0.3, emit=((1.0, 0.1, 0.1), 0.0))
vb = M_VES.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f, v in ((1, 0.0), (1430, 0.0), (1460, 3.0), (1490, 0.8), (B["end"], 0.5)):
    vb.default_value = v; vb.keyframe_insert("default_value", frame=f)
VES = []
for i in range(3):
    for side_ in (0, 1):
        cu = bpy.data.curves.new("JoinVessel%d_%d" % (i, side_), 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0011; cu.bevel_resolution = 2
        sp = cu.splines.new('BEZIER'); sp.bezier_points.add(1)
        base_ = EAR_C + Vector((0.012, -0.012 + i * 0.008, -0.012 + 0.012 * i))
        a = base_ + (Vector((0.006, -0.01, -0.006)) if side_ == 0 else Vector((-0.004, 0.006, 0.004)))
        sp.bezier_points[0].co = a; sp.bezier_points[1].co = base_
        for bp in sp.bezier_points: bp.handle_left_type = bp.handle_right_type = 'AUTO'
        cu.materials.append(M_VES); o = bpy.data.objects.new(cu.name, cu); C_PROP.objects.link(o)
        attach_bone(o, PAT, "head", Matrix.Identity(4))
        cu.bevel_factor_end = 0.0; cu.keyframe_insert("bevel_factor_end", frame=1400 + i * 8)
        cu.bevel_factor_end = 1.0; cu.keyframe_insert("bevel_factor_end", frame=1445 + i * 8)
        key_vis(o, 1, False); key_vis(o, 1395, True)
glow = bpy.data.objects.new("JoinGlow", None)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.006); gl = bpy.context.object; gl.name = "JoinGlow"
gl.data.materials.append(newmat("Glow", (1, 0.5, 0.4), 0.5, emit=((1.0, 0.45, 0.3), 25.0), alpha=0.5))
for c in list(gl.users_collection): c.objects.unlink(gl)
C_PROP.objects.link(gl); attach_bone(gl, PAT, "head", Matrix.Translation(EAR_C + Vector((0.012, -0.004, -0.002))))
for f, s_ in ((1, 0.0), (1440, 0.0), (1458, 1.6), (1490, 0.5), (1510, 0.0)):
    gl.scale = (s_,) * 3; gl.keyframe_insert("scale", frame=f)

# ================================================================== stitches (beat 8): appear one by one along the ear base
M_SUT = newmat("Suture", (0.1, 0.12, 0.35), 0.5)
for i in range(STITCH_N):
    u = i / (STITCH_N - 1)
    p = EAR_C + Vector((0.006, -0.03 + 0.06 * u - 0.0, -0.025 + 0.06 * math.sin(math.pi * u) - 0.005))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.0035, minor_radius=0.0005, major_segments=12, minor_segments=4); st = bpy.context.object
    st.name = "Stitch%d" % i; st.data.materials.append(M_SUT)
    for c in list(st.users_collection): c.objects.unlink(st)
    C_PROP.objects.link(st)
    attach_bone(st, PAT, "head", Matrix.Translation(p) @ Matrix.Rotation(R_(90), 4, 'Y') @ Matrix.Rotation(R_(30), 4, 'X'))
    f0 = 1510 + i * 15
    st.scale = (0.01,) * 3; st.keyframe_insert("scale", frame=f0); st.scale = (1.2,) * 3; st.keyframe_insert("scale", frame=f0 + 5)
    st.scale = (1.0,) * 3; st.keyframe_insert("scale", frame=f0 + 9)
    key_vis(st, 1, False); key_vis(st, f0, True)
# old ear: gone (EarGone=1) all film; the grafted ear (Ear_New) replaces it from 1440

# ================================================================== studio A: block lift (beat 2)
SA = Vector((40, 0, 1.2))
cb = OB["SA_CartBlock"]; cl = OB["SA_CutLine"]
cu = cl.data
for f, v in ((1, 0.0), (215, 0.0), (265, 1.0)):
    cu.bevel_factor_end = v; cu.keyframe_insert("bevel_factor_end", frame=f)
P0 = cb.location.copy()
for f, d in ((1, Vector()), (275, Vector()), (300, Vector((0, -0.02, 0.005))), (340, Vector((0, -0.09, 0.06)))):
    cb.location = P0 + d; cb.keyframe_insert("location", frame=f)
cb.rotation_euler = (0, 0, 0); cb.keyframe_insert("rotation_euler", frame=290); cb.rotation_euler = (R_(25), R_(10), 0); cb.keyframe_insert("rotation_euler", frame=340)
th = OB["SA_Thorax"]
th.rotation_euler = (0, 0, R_(-8)); th.keyframe_insert("rotation_euler", frame=150); th.rotation_euler = (0, 0, R_(10)); th.keyframe_insert("rotation_euler", frame=340)
cb.parent = None
# gloved hand in studio A: a static copy of the surgeon's right hand (gripping the scalpel at f450), in its wrist frame
sc.frame_set(450); dg = bpy.context.evaluated_depsgraph_get()
ev_b = SUR.body.evaluated_get(dg)
me = bpy.data.meshes.new_from_object(ev_b, preserve_all_data_layers=True, depsgraph=dg)
WM = wrist_w(SUR, "R"); WMi = (WM).inverted()
gb = bpy.data.objects.new("SA_GloveHand", me); bpy.data.collections["Studio_Ribs"].objects.link(gb)
bm = bmesh.new(); bm.from_mesh(me); dl = bm.verts.layers.deform.active
keep = [g.index for g in SUR.body.vertex_groups if g.name.startswith(("wrist.R", "finger", "metacarpal", "lowerarm02.R"))]
kill = [v for v in bm.verts if (sum(v[dl].get(g, 0.0) for g in keep) < 0.5) or (SUR.body.matrix_world @ v.co - WM.translation).length > 0.3]
bmesh.ops.delete(bm, geom=kill, context='VERTS')
for v in bm.verts: v.co = WMi @ (SUR.body.matrix_world @ v.co)
bm.to_mesh(me); bm.free()
me.materials.clear(); me.materials.append(M_GLOVE)
for p_ in me.polygons: p_.use_smooth = True; p_.material_index = 0
cuff = bpy.data.objects.new("SA_Cuff", None)
scal_sa = scal.copy(); scal_sa.animation_data_clear(); scal_sa.name = "SA_Scalpel"; bpy.data.collections["Studio_Ribs"].objects.link(scal_sa)
scal_sa.parent = gb; scal_sa.matrix_parent_inverse = Matrix.Identity(4); scal_sa.matrix_basis = G_SCAL
gb.rotation_mode = 'XYZ'
for f, off, rot in ((127, Vector((0.32, -0.4, 0.2)), (20, 0, 60)), (200, Vector((0.14, -0.22, 0.04)), (40, 0, 75)), (240, Vector((0.09, -0.16, -0.0)), (50, 10, 80)),
                    (265, Vector((0.1, -0.16, -0.07)), (55, 15, 85)), (300, Vector((0.2, -0.12, -0.05)), (40, 10, 80)), (342, Vector((0.26, -0.15, 0.05)), (30, 0, 70))):
    gb.location = P0 + off; gb.rotation_euler = [R_(x) for x in rot]
    gb.keyframe_insert("location", frame=f); gb.keyframe_insert("rotation_euler", frame=f)
print("ANIM_DONE")
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=out)
