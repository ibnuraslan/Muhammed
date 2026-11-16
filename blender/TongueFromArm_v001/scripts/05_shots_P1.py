"""TongueFromArm Phase 1: per-set action clips (about 30% longer than their provisional windows), one camera per shot,
hard cuts by timeline markers. Provisional timing = reference pacing (~1 s per beat line); Phase 2 re-lays to the VO.
blender -b work/sets.blend --python 05_shots.py -- work/film.blend"""
import bpy, sys, math, json
from mathutils import Vector, Matrix, Euler, Quaternion
P_ = "/home/user/Muhammed/blender/pipeline/"; HERE = "/home/user/Muhammed/blender/TongueFromArm_v001/"
exec(open(P_ + "anim_lib.py").read()); exec(open(P_ + "hand_poses.py").read()); exec(open(HERE + "scripts/lib_human.py").read())
exec(open(HERE + "scripts/lib.py").read())
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; sc.render.fps = 60; sc.frame_start = 1
R_ = math.radians
SHOTS = [  # id, set, f0, f1, line
    ("S01", "or", 1, 72, "They surgically removed - OR, surgeon over the sleeping patient"),
    ("S02", "dia", 73, 132, "90% of her tongue - mouth model, tumour on the tongue"),
    ("S03", "dia", 133, 192, "90% of her tongue - the front 90% lifts out, the stump stays"),
    ("S04", "dia", 193, 252, "because it had cancer - the removed piece turns, purple tumour"),
    ("S05", "or", 253, 312, "they cut a muscle - her arm on the arm board, nurse at the arm"),
    ("S06", "dia", 313, 372, "out of her arm - forearm model, muscle flap lifts out with its vessels"),
    ("S07", "dia", 373, 432, "They connected - flap set onto the stump, vessels run to the neck"),
    ("S08", "dia", 433, 492, "the veins inside her mouth - vessels join, stitches"),
    ("S09", "dia", 493, 552, "and stitched the nerves - yellow nerve joins"),
    ("S10", "or", 553, 612, "(stitching) - surgeon's masked face, concentrating"),
    ("S11", "dia", 613, 672, "The muscle was shaped - the slab starts to take the tongue's form"),
    ("S12", "dia", 673, 732, "onto what was left of her tongue - shaping completes, colour turns tongue-pink"),
    ("S13", "dia", 733, 792, "matching its shape - full mouth, new tongue"),
    ("S14", "or", 793, 852, "its shape - surgeon straightens up, patient resting"),
    ("S15", "ward", 853, 942, "doctors said - ward wide, doctor at the bedside"),
    ("S16", "ward", 943, 1032, "she would never speak - doctor, slight head shake"),
    ("S17", "ward", 1033, 1122, "just days later - daughter walks in through the door"),
    ("S18", "ward", 1123, 1212, "she said hello - patient close: turns, smiles, says hello"),
    ("S19", "ward", 1213, 1302, "to her daughter - daughter walks to the bedside"),
    ("S20", "ward", 1303, 1392, "both faces, mother and daughter"),
]
SH = {s[0]: s for s in SHOTS}
sc.frame_end = SHOTS[-1][3]
json.dump([dict(id=s[0], set=s[1], f0=s[2], f1=s[3], line=s[4]) for s in SHOTS], open(HERE + "shots_provisional.json", "w"), indent=1)
DX = Vector((40, 0, 0)); W0 = Vector((-40, 0, 0)); MZ = sc["MZ"]

def cam_shot(sid, keys, lens=35, target_keys=None, fstop=11.0):
    c = bpy.data.cameras.new("CAM_" + sid); c.lens = lens; c.clip_start = 0.01; c.clip_end = 200; c.sensor_width = 36
    c.dof.use_dof = False
    o = bpy.data.objects.new("CAM_" + sid, c); sc.collection.objects.link(o)
    t = bpy.data.objects.new("TGT_" + sid, None); sc.collection.objects.link(t)
    for f, p in keys: o.location = p; o.keyframe_insert("location", frame=f)
    for f, p in target_keys: t.location = p; t.keyframe_insert("location", frame=f)
    tr = o.constraints.new('TRACK_TO'); tr.target = t; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
    m = sc.timeline_markers.new(sid, frame=SH[sid][2]); m.camera = o
    return o
def keyv(o, path, f, v, idx=None):
    if idx is None: setattr(o, path, v); o.keyframe_insert(path, frame=f)
    else:
        getattr(o, path)[idx] = v; o.keyframe_insert(path, index=idx, frame=f)
def vis(o, f, on):
    o.hide_render = not on; o.hide_viewport = not on
    o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)

# ============================================================ OR clip (frames 1-1110)
P = bpy.data.objects["Patient"]; PR = Rig(P)
def wpos(rig, bone, tail=False):
    bpy.context.view_layer.update(); pb = rig.pose.bones[bone]
    return rig.matrix_world @ (pb.tail if tail else pb.head)
# patient re-staged with IK: seated deep in the reclined chair, R forearm on the chair arm, L forearm forward on the arm board
def chair_hit(x, y, names=("Chair_Seat", "Chair_LegRest", "Chair_Back", "Chair_Arm0", "ArmBoard_Drape"), z0=3.0):
    dg = bpy.context.evaluated_depsgraph_get(); best = None
    for n in names:
        o = bpy.data.objects[n].evaluated_get(dg); mi = o.matrix_world.inverted()
        ok, loc, nrm, idx = o.ray_cast(mi @ Vector((x, y, z0)), (mi.to_3x3() @ Vector((0, 0, -1))).normalized())
        if ok:
            z = (o.matrix_world @ loc).z
            best = z if best is None else max(best, z)
    return best
ab = bpy.data.objects["ArmBoard"]; abd = bpy.data.objects["ArmBoard_Drape"]
bpy.context.view_layer.update()
for o in (ab, abd):   # board turned to run forward beside the chair arm (forearm rests on it, no arm out to the side)
    o.rotation_euler.z += R_(90); o.location = Vector((0.47, -0.18, 0.74 + (0.035 if o is abd else 0.0)))
bpy.context.view_layer.update()
P.animation_data_clear()
for pb in P.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
P.matrix_world = Matrix.Identity(4)
HPt = setup_char(P)
zs = chair_hit(0.0, -0.08, ("Chair_Seat",))
HIP = Vector((0.0, 0.0, zs + 0.115))
_g = globals(); _g["ground_z"] = lambda x, y: (chair_hit(x, y, ("Chair_LegRest", "Chair_Seat")) or 0.4)
zR = chair_hit(-0.32, -0.02, ("Chair_Arm0",)); zL = chair_hit(0.47, -0.26, ("ArmBoard_Drape",))
print("CHAIR seat", zs, "armR", zR, "board", zL)
for f in range(1, 1112, 30):
    br = math.sin(2 * math.pi * f / 240.0)
    HPt.key_root(f, HIP, yaw=0, flex=-36)
    HPt.key_spine(f, flex=6 + 1.2 * br, head=(16, -4))
    for s_ in "LR":
        sx = 1 if s_ == "L" else -1
        HPt.key_foot(s_, f, Vector((0.10 * sx, -0.66)), 0, lift=0.03, pitch=-30)
    HPt.key_hand("R", f, Vector((-0.31, -0.04, zR + 0.09)), Vector((0.0, -1.0, -0.15)), Vector((0, 0, -1)), pole=Vector((-0.55, 0.45, 0.6)))
    HPt.key_hand("L", f, Vector((0.45, -0.30, zL + 0.06)), Vector((0.05, -1.0, -0.05)), Vector((0, 0, -1)), pole=Vector((0.75, 0.45, 0.6)))
for s_ in "LR": apply_pose(P, s_, "relaxed", 1)
_g["ground_z"] = lambda x, y: 0.0
for n in ("orbicularis03.L", "orbicularis03.R"):
    pb = P.pose.bones[n]; pb.rotation_quaternion = Euler((R_(26), 0, 0)).to_quaternion(); pb.keyframe_insert("rotation_quaternion", frame=1)
sc.frame_set(1); bpy.context.view_layer.update()
HEAD = wpos(P, "head"); HEADT = wpos(P, "head", True); FACE = HEAD + (HEADT - HEAD) * 0.45
EL = wpos(P, "lowerarm01.L"); WR = wpos(P, "wrist.L"); FA = (EL + WR) / 2
print("OR head", HEAD, "forearm", FA)
# surgeon at her head (left side), sterile hands held in front of his chest, leaning to look at her face
Sg = bpy.data.objects["Surgeon"]; Sg.animation_data_clear()
for pb in Sg.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
HS = setup_char(Sg)
SP = Vector((HEAD.x - 0.92, HEAD.y + 0.05, 0))
bpy.data.objects['IV_Stand'].location.x = -1.4; bpy.data.objects['IV_Stand'].location.y = 1.2
def surgeon_pose(f, flex, head_p, head_y=0.0, twist=0.0, hands_up=0.0):
    pos = Vector((SP.x, SP.y, HS.root_head.z - 0.02)); yaw = 90
    HS.key_root(f, pos, yaw=yaw, flex=flex * 0.4); HS.key_spine(f, flex=flex, twist=twist, head=(head_p, head_y))
    for s in "LR": HS.key_foot(s, f, HS.foot_xy(s, Vector((pos.x, pos.y, 0)), yaw), yaw)
    for s in "LR":
        sx = 1 if s == "L" else -1
        body_hand(HS, s, f, pos, yaw, (0.13 * sx, -0.22 - 0.05 * hands_up, -0.10 + 0.06 * hands_up), (-0.5 * sx, -0.4, 0.8), (-sx * 0.9, 0.0, 0.2),
                  pole_off=(0.45 * sx, 0.15, -0.1))
for f, fl, hp, hy, tw in ((1, 14, 26, -4, 0), (60, 16, 28, 3, 2), (130, 15, 27, -2, 0), (253, 14, 24, 0, -3), (330, 15, 28, 4, 0),
                          (553, 16, 30, -3, 0), (590, 17, 31, 2, 2), (640, 16, 28, -2, 0), (793, 15, 26, 0, 0), (830, 10, 6, 8, -4), (900, 6, 2, 12, -6), (1110, 6, 2, 10, -6)):
    surgeon_pose(f, fl, hp, hy, tw)
for s in "LR":
    apply_pose(Sg, s, "relaxed", 1)
# nurse at the arm board, looking at the forearm, hands held in front
N = bpy.data.objects["Nurse"]; N.location = (0, 0, 0); N.animation_data_clear()
for pb in N.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
HN = setup_char(N)
NP = Vector((FA.x + 0.45, FA.y - 0.35, 0))
for f, fl, hp, hy in ((1, 8, 8, 0), (120, 9, 10, -5), (253, 10, 12, 4), (300, 10, 14, -2), (420, 9, 10, 3), (700, 8, 8, 0), (1110, 8, 8, 0)):
    pos = Vector((NP.x, NP.y, HN.root_head.z - 0.02)); yaw = -128
    HN.key_root(f, pos, yaw=yaw, flex=fl * 0.4); HN.key_spine(f, flex=fl, head=(hp, hy))
    for s in "LR": HN.key_foot(s, f, HN.foot_xy(s, Vector((pos.x, pos.y, 0)), yaw), yaw)
    for s in "LR":
        sx = 1 if s == "L" else -1
        body_hand(HN, s, f, pos, yaw, (0.12 * sx, -0.30, 0.10), (-0.5 * sx, -0.4, 0.8), (-sx * 0.9, 0.0, 0.2), pole_off=(0.45 * sx, 0.15, -0.1))
for s in "LR": apply_pose(N, s, "relaxed", 1)
# simplest re-stage (LESSONS 2.15): the nurse is not in the film (she blocked the arm shots); the surgeon is the only OR staff
for c in [N] + list(N.children): c.hide_render = True; c.hide_viewport = True
N.location = (0, 0, -30)
# surgical drape over the patient's legs (covers the lower body in the chair)
# OR cameras
cam_shot("S01", [(1, HEAD + Vector((0.95, -0.40, 0.50))), (72, HEAD + Vector((0.82, -0.36, 0.44)))], 28,
         [(1, FACE + Vector((-0.30, 0.0, -0.10))), (72, FACE + Vector((-0.28, 0.0, -0.10)))])
cam_shot("S05", [(253, FA + Vector((0.62, -0.92, 0.62))), (312, FA + Vector((0.55, -0.82, 0.58)))], 26,
         [(253, FA + Vector((-0.14, 0.10, 0.14))), (312, FA + Vector((-0.14, 0.10, 0.14)))])
sc.frame_set(560); SF = wpos(Sg, 'head') + Vector((0, 0, 0.06)); sc.frame_set(1)
cam_shot("S10", [(553, SF + Vector((0.70, -0.62, -0.05))), (612, SF + Vector((0.60, -0.52, -0.06)))], 40,
         [(553, SF + Vector((0.0, 0.0, -0.05))), (612, SF + Vector((0.0, 0.0, -0.05)))])
cam_shot("S14", [(793, HEAD + Vector((1.30, -0.25, 0.40))), (852, HEAD + Vector((1.40, -0.30, 0.45)))], 28,
         [(793, HEAD + Vector((-0.45, 0.05, -0.05))), (852, HEAD + Vector((-0.45, 0.05, 0.02)))])

# ============================================================ DIAGRAM clip (frames 1-1110)
ob = bpy.data.objects
for n in ("UpperHinge",):
    keyv(ob[n], "rotation_euler", 1, Euler((R_(-0.75 * 57.3), 0, 0)))
front = ob["Tongue_front"]; flap = ob["Flap"]; stump = ob["Tongue_stump"]
fl0 = front.location.copy(); fr0 = front.rotation_euler.copy()
keyv(front, "location", 1, fl0); keyv(front, "location", 150, fl0); keyv(front, "rotation_euler", 150, fr0)
keyv(front, "location", 205, fl0 + Vector((0, -0.012, 0.032))); keyv(front, "rotation_euler", 205, Euler((R_(-18), 0, 0)))
keyv(front, "location", 330, fl0 + Vector((0, -0.016, 0.050))); keyv(front, "rotation_euler", 330, Euler((R_(-22), 0, R_(70))))
vis(front, 1, True); vis(front, 373, False); vis(ob["Tumour"], 1, True); vis(ob["Tumour"], 373, False)
vis(flap, 1, False); vis(flap, 340, True)
flap.location = fl0 + Vector((0, 0, 0.03)); flap.keyframe_insert("location", frame=340); flap.keyframe_insert("location", frame=380)
flap.location = fl0 + Vector((0, 0, -0.0015)); flap.keyframe_insert("location", frame=418)
kb = flap.data.shape_keys.key_blocks["Slab"]
for f, v in ((1, 1.0), (625, 1.0), (735, 0.0)): kb.value = v; kb.keyframe_insert("value", frame=f)
mixn = bpy.data.materials["D_Flap"].node_tree.nodes["Pinkify"]
for f, v in ((1, 0.0), (630, 0.0), (750, 0.88)): mixn.inputs[0].default_value = v; mixn.inputs[0].keyframe_insert("default_value", frame=f)
for nm, f0 in (("Artery", 392), ("Vein", 404), ("Nerve", 500)):
    cu = ob["Join" + nm].data
    for f, v in ((1, 0.0), (f0, 0.0), (f0 + 45, 1.0)): cu.bevel_factor_end = v; cu.keyframe_insert("bevel_factor_end", frame=f)
for nm, f0 in (("Artery", 452), ("Vein", 470), ("Nerve", 540)):
    st = ob["Stitch" + nm]
    for f, v in ((1, 0.0), (f0, 0.0), (f0 + 14, 1.0)): st.scale = (v, v, v); st.keyframe_insert("scale", frame=f)
# forearm flap lift + hooked strands
af = ob["ArmFlap"]; a0 = af.location.copy()
keyv(af, "location", 1, a0); keyv(af, "location", 325, a0); keyv(af, "rotation_euler", 325, Euler((0, 0, 0)))
keyv(af, "location", 395, a0 + Vector((0.004, 0, 0.028))); keyv(af, "rotation_euler", 395, Euler((R_(-6), R_(-8), 0)))
for nm in ("Artery", "Vein", "Nerve"):
    c = ob["ArmVes" + nm]; e = bpy.data.objects.new("Hook" + nm, None); sc.collection.objects.link(e)
    e.location = Vector(c.data.splines[0].points[0].co[:3]); e.parent = af; e.matrix_parent_inverse = af.matrix_world.inverted()
    h = c.modifiers.new("Hook", 'HOOK'); h.object = e
    # hook point 0 (curves: assign via edit mode free API)
    bpy.context.view_layer.objects.active = c; c.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.curve.select_all(action='DESELECT')
    c.data.splines[0].points[0].select = True
    bpy.ops.object.hook_reset(modifier="Hook") if False else None
    bpy.ops.object.mode_set(mode='OBJECT')
    h.vertex_indices_set([0])
    h.center = e.location
    h.matrix_inverse = e.matrix_world.inverted()
# diagram lights (soft key + fill), outside every camera path
def area(name, loc, tgt, size, energy, col=(1, 1, 1)):
    l = bpy.data.lights.new(name, 'AREA'); l.size = size; l.energy = energy; l.color = col
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return o
area("D_Key", DX + Vector((0.25, -0.35, 0.45)), DX, 0.5, 18); area("D_Fill", DX + Vector((-0.4, -0.2, 0.15)), DX, 0.6, 8)
area("D_Rim", DX + Vector((0, 0.4, 0.3)), DX, 0.4, 8)
AXc = ob["D_Forearm"].location + Vector((-0.03, 0, 0))
area("A_Key", AXc + Vector((0.2, -0.35, 0.5)), AXc, 0.5, 30); area("A_Fill", AXc + Vector((-0.4, -0.2, 0.2)), AXc, 0.6, 12)
# diagram cameras (f/11 equivalent: no DOF)
M = DX
cam_shot("S02", [(73, M + Vector((0.0, -0.21, 0.13))), (132, M + Vector((0.02, -0.17, 0.11)))], 50,
         [(73, M + Vector((0, 0.0, -0.002))), (132, M + Vector((0, 0.002, -0.002)))])
cam_shot("S03", [(133, M + Vector((0.08, -0.15, 0.15))), (192, M + Vector((0.06, -0.13, 0.17)))], 50,
         [(133, M + Vector((0, -0.002, 0.004))), (192, M + Vector((0, -0.006, 0.018)))])
PC = ob['Mouth'].matrix_world @ (fl0 + Vector((0, -0.016, 0.050)))
cam_shot("S04", [(193, PC + Vector((0.07, -0.12, 0.05))), (252, PC + Vector((-0.04, -0.12, 0.06)))], 50,
         [(193, PC + Vector((0, 0, -0.008))), (252, PC + Vector((0, 0, -0.004)))])
cam_shot("S06", [(313, AXc + Vector((0.08, -0.16, 0.30))), (372, AXc + Vector((0.05, -0.13, 0.27)))], 50,
         [(313, AXc + Vector((0.02, 0, 0.0))), (372, AXc + Vector((0.0, 0, 0.012)))])
cam_shot("S07", [(373, M + Vector((0.10, -0.12, 0.16))), (432, M + Vector((0.07, -0.10, 0.15)))], 50,
         [(373, M + Vector((0, 0.008, -0.004))), (432, M + Vector((0, 0.012, -0.006)))])
BK = Vector(ob["StitchArtery"].location) - Vector((0.010, 0, 0))
cam_shot("S08", [(433, BK + Vector((0.05, -0.10, 0.11))), (492, BK + Vector((0.04, -0.085, 0.10)))], 60,
         [(433, BK + Vector((0, -0.004, -0.004))), (492, BK + Vector((0, 0, -0.004)))])
cam_shot("S09", [(493, BK + Vector((-0.08, -0.15, 0.16))), (552, BK + Vector((-0.07, -0.13, 0.15)))], 50,
         [(493, BK + Vector((0, -0.004, -0.004))), (552, BK + Vector((0, 0, -0.006)))])
cam_shot("S11", [(613, M + Vector((0.0, -0.12, 0.16))), (672, M + Vector((0.01, -0.10, 0.15)))], 50,
         [(613, M + Vector((0, 0.004, -0.004))), (672, M + Vector((0, 0.004, -0.004)))])
cam_shot("S12", [(673, M + Vector((-0.09, -0.12, 0.12))), (732, M + Vector((-0.06, -0.12, 0.13)))], 50,
         [(673, M + Vector((0, 0.004, -0.004))), (732, M + Vector((0, 0.002, -0.004)))])
cam_shot("S13", [(733, M + Vector((0.12, -0.18, 0.10))), (792, M + Vector((-0.06, -0.21, 0.11)))], 50,
         [(733, M + Vector((0, 0.0, 0.0))), (792, M + Vector((0, 0.0, 0.0)))])

# ============================================================ WARD clip (frames 853-1520)
PW = dup_char(P, "PatientW"); PW.animation_data_clear()
for c in PW.children:
    if 'shoes' in c.name: c.hide_render = True; c.hide_viewport = True
for c in PW.children: c.animation_data_clear()
for pb in PW.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
HP = setup_char(PW)
_g = globals()
def ground_bed(x, y):
    return MZ + 0.02 if (-0.5 < x - W0.x < 0.5 and -0.8 < y - W0.y < 1.45) else 0.0
_g["ground_z"] = ground_bed
PP = W0 + Vector((0, 0.62, 0))
HZ = {'L': 0.17, 'R': 0.17}
def patient_w(f, head_p, head_y, twist=0.0, lean=-14, jaw=0.0, hand_dy=0.0, hands_up=False):
    pos = Vector((PP.x, PP.y, MZ + 0.10)); yaw = 0
    HP.key_root(f, pos, yaw=yaw, flex=0); HP.key_spine(f, flex=lean + 12, twist=twist, head=(head_p, head_y))
    # legs straight under the blanket
    for s in "LR":
        sx = 1 if s == "L" else -1
        HP.key_foot(s, f, Vector((pos.x + 0.10 * sx, pos.y - 0.82)), 0, lift=-0.10, pitch=-50)
        body_hand(HP, s, f, pos, yaw, (0.16 * sx, -0.30 + hand_dy, (0.75 if hands_up else HZ[s])), (0.15 * sx, -1.0, -0.15), (0, 0, -1.0), pole_off=(0.45 * sx, 0.25, 0.1))
    pb = PW.pose.bones["jaw"]; pb.rotation_quaternion = Euler((R_(jaw), 0, 0)).to_quaternion(); pb.keyframe_insert("rotation_quaternion", frame=f)
WKEYS = ((853, 4, 22, 6, 0), (942, 2, 26, 8, 0), (1000, 6, 24, 6, 0), (1033, 2, 10, 0, 0), (1080, 0, -18, -6, 0),
                          (1123, -2, -28, -10, 0), (1150, -4, -30, -12, 7), (1166, -4, -30, -12, 2), (1180, -4, -30, -12, 8), (1200, -4, -30, -12, 0),
                          (1260, 0, -34, -12, 0), (1303, 2, -40, -14, 0), (1340, 0, -38, -14, 5), (1360, 0, -38, -14, 0), (1520, 0, -36, -12, 0))
for f, hp, hy, tw, jw in WKEYS:
    patient_w(f, hp, hy, tw, jaw=jw)
for s in "LR": apply_pose(PW, s, "relaxed", 853)
# blanket: a soft sheet shaped over her legs (built at frame 840 with her hands lifted out of the way)
patient_w(840, 4, 22, 6, hands_up=True)
sc.frame_set(840); bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
from mathutils.bvhtree import BVHTree
vs_, ps_ = [], []
for n in ("PatientW.body", "PatientW.gown"):
    e = bpy.data.objects[n].evaluated_get(dg); me = e.to_mesh(); off = len(vs_)
    vs_ += [e.matrix_world @ v.co for v in me.vertices]; ps_ += [tuple(i + off for i in p.vertices) for p in me.polygons]; e.to_mesh_clear()
bvh = BVHTree.FromPolygons(vs_, ps_)
y0, y1 = PP.y - 0.02, W0.y + 1.45 - 2.15 + 0.02; NX, NY = 34, 48
Z = [[0.0] * (NX + 1) for _ in range(NY + 1)]
for j in range(NY + 1):
    for i in range(NX + 1):
        x = -0.56 + 1.12 * i / NX; y = y0 + (y1 - y0) * j / NY
        hit = bvh.ray_cast(Vector((W0.x + x, y, MZ + 0.45)), Vector((0, 0, -1)))
        z = MZ + 0.035
        if hit[0] is not None: z = max(z, hit[0].z + 0.03)
        if abs(x) > 0.47: z = MZ + 0.035 - (abs(x) - 0.47) * 2.6
        Z[j][i] = z
for it in range(5):
    Z2 = [r[:] for r in Z]
    for j in range(1, NY):
        for i in range(1, NX):
            Z2[j][i] = max(Z[j][i], (Z[j][i] * 2 + Z[j - 1][i] + Z[j + 1][i] + Z[j][i - 1] + Z[j][i + 1]) / 6)
    Z = Z2
verts = [(W0.x - 0.56 + 1.12 * i / NX, y0 + (y1 - y0) * j / NY, Z[j][i]) for j in range(NY + 1) for i in range(NX + 1)]
faces = [(j * (NX + 1) + i, j * (NX + 1) + i + 1, (j + 1) * (NX + 1) + i + 1, (j + 1) * (NX + 1) + i) for j in range(NY) for i in range(NX)]
bme = bpy.data.meshes.new("W_Blanket"); bme.from_pydata(verts, [], faces); bme.polygons.foreach_set("use_smooth", [True] * len(faces))
blk = bpy.data.objects.new("W_Blanket", bme); sc.collection.objects.link(blk); bme.materials.append(mat("W_BlanketM", (0.55, 0.75, 0.92), 0.8))
so = blk.modifiers.new("Thick", 'SOLIDIFY'); so.thickness = 0.015; so.offset = -1; blk.modifiers.new("Sub", 'SUBSURF').levels = 1
bpy.context.view_layer.update()
def blanket_top(x, y):
    i = round((x - (W0.x - 0.56)) / 1.12 * NX); j = round((y - y0) / (y1 - y0) * NY)
    return Z[max(0, min(NY, j))][max(0, min(NX, i))]
for s_ in "LR":
    sx = 1 if s_ == "L" else -1
    HZ[s_] = blanket_top(PP.x + 0.16 * sx, PP.y - 0.30) + 0.10 - (MZ + 0.10)
print("BLANKET hand z", HZ)
for f, hp, hy, tw, jw in WKEYS:
    patient_w(f, hp, hy, tw, jaw=jw)
_g["ground_z"] = lambda x, y: 0.0
# doctor at the right side of the bed, facing the patient
D = bpy.data.objects["Doctor"]; D.location = (0, 0, 0); HD = setup_char(D)
DP = W0 + Vector((0.64, 0.42, 0))
for f, fl, hp, hy, gest in ((853, 4, 6, 0, 0), (885, 5, 9, -4, 0.6), (915, 6, 12, 2, 1.0), (942, 5, 8, -2, 0.8), (958, 6, 10, 10, 1.0), (972, 6, 10, -10, 1.0),
                            (986, 6, 11, 10, 0.9), (1000, 6, 10, -10, 0.8), (1016, 5, 8, 6, 0.5), (1032, 4, 6, -2, 0), (1123, 3, 2, -30, 0), (1300, 3, 4, -20, 0), (1520, 3, 4, -16, 0)):
    pos = Vector((DP.x, DP.y, HD.root_head.z - 0.01)); yaw = -90
    HD.key_root(f, pos, yaw=yaw, flex=fl * 0.4); HD.key_spine(f, flex=fl, head=(hp, hy))
    for s in "LR": HD.key_foot(s, f, HD.foot_xy(s, Vector((pos.x, pos.y, 0)), yaw), yaw)
    key_hang(HD, f, pos, yaw)
    if gest:   # right hand opens forward at waist height while she explains
        body_hand(HD, "R", f, pos, yaw, (-0.17, -0.34 * gest - 0.06, 0.10 * gest - 0.04), (0.15, -1.0, 0.2), (0.0, 0.3, -1.0), pole_off=(-0.45, 0.2, -0.1))
for s in "LR": apply_pose(D, s, "relaxed", 853)
# daughter walks in from the door to the left bedside
G = bpy.data.objects["Girl"]; G.location = (0, 0, 0); HG = setup_char(G)
p0 = W0 + Vector((-3.0, -1.9, 0)); p1 = W0 + Vector((-1.6, -1.6, 0)); p2 = W0 + Vector((-0.85, -0.55, 0))
path = catmull([(1040, p0), (1110, p1), (1260, p2)])
def gyaw(f):
    a = path(max(1040, f - 3)); b = path(min(1260, f + 3)); d = (b - a)
    return math.degrees(math.atan2(d.x, -d.y)) if d.length > 1e-4 else 60.0
walk_with_arms(HG, path, gyaw, 1040, 1260, stride=0.75, amp=0.07)
for f in (1262, 1300, 1340, 1400, 1520):
    pos = Vector((p2.x, p2.y, HG.root_head.z)); yaw = gyaw(1258)
    HG.key_root(f, pos, yaw=yaw, flex=1); HG.key_spine(f, flex=2, head=(-8 if f < 1350 else -6, 4 * math.sin(f / 30)))
    for s in "LR": HG.key_foot(s, f, HG.foot_xy(s, Vector((pos.x, pos.y, 0)), yaw), yaw)
    key_hang(HG, f, pos, yaw)
for s in "LR": apply_pose(G, s, "relaxed", 1040)
# ward lights
for i, x in enumerate((-1.0, 0.0, 1.0)):
    area("W_L%d" % i, W0 + Vector((x, 0.0, 2.7)), W0 + Vector((x, 0.0, 0)), 1.0, 40)
area("W_Fill", W0 + Vector((0.4, -2.6, 1.8)), W0 + Vector((0, 0.5, 1.0)), 1.5, 22)
# ward cameras
HPW = W0 + Vector((0, 0.55, MZ + 0.75))   # patient head approx
cam_shot("S15", [(853, W0 + Vector((0.55, -2.75, 1.55))), (942, W0 + Vector((0.45, -2.45, 1.5)))], 24,
         [(853, W0 + Vector((-0.3, 0.4, 1.15))), (942, W0 + Vector((-0.28, 0.4, 1.15)))])
DH = DP + Vector((0, 0, 1.55))
cam_shot("S16", [(943, DH + Vector((-1.05, -0.85, -0.1))), (1032, DH + Vector((-0.95, -0.70, -0.1)))], 40,
         [(943, DH + Vector((0, 0, -0.05))), (1032, DH + Vector((0, 0, -0.05)))])
cam_shot("S17", [(1033, W0 + Vector((-0.2, -0.6, 1.25))), (1122, W0 + Vector((-0.35, -0.5, 1.2)))], 26,
         [(1033, W0 + Vector((-2.4, -1.9, 0.95))), (1122, W0 + Vector((-1.7, -1.6, 0.9)))])
cam_shot("S18", [(1123, HPW + Vector((-0.75, -0.62, 0.02))), (1212, HPW + Vector((-0.62, -0.52, 0.02)))], 45,
         [(1123, HPW + Vector((0, 0, -0.02))), (1212, HPW + Vector((0, 0, -0.02)))])
cam_shot("S19", [(1213, W0 + Vector((0.75, -2.65, 1.4))), (1302, W0 + Vector((0.68, -2.5, 1.38)))], 20,
         [(1213, W0 + Vector((-0.4, -0.05, 1.0))), (1302, W0 + Vector((-0.36, 0.0, 1.0)))])
cam_shot("S20", [(1303, W0 + Vector((0.95, 0.15, 1.45))), (1392, W0 + Vector((0.88, 0.12, 1.43)))], 40,
         [(1303, W0 + Vector((-0.82, -0.52, 0.95))), (1392, W0 + Vector((-0.82, -0.52, 0.97)))])
# smooth camera keys
for o in bpy.data.objects:
    if o.name.startswith(("CAM_", "TGT_")) and o.animation_data and o.animation_data.action:
        for fc in fcurves_of(o) if 'fcurves_of' in globals() else []:
            pass
sc.camera = bpy.data.objects["CAM_S01"]
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
