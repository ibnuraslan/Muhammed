"""Animate EscapeArtist. blender -b scene.blend --python 03_animate.py -- <out.blend>
Beat starts (frames @60fps) follow the brief's target times."""
import sys, math, random
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler
HERE = "/home/user/Muhammed/blender/"
exec(open(HERE + "pipeline/anim_lib.py").read())
exec(open(HERE + "EscapeArtist_v001/scripts/escape_lib.py").read())
OUT = sys.argv[sys.argv.index("--") + 1]
random.seed(3)
B = [0, 276, 558, 678, 942, 1128, 1422, 1548, 1860, 2172, 2484, 2898, 3228, 3498, 3618, 3750]
END = 3750
sc.frame_start, sc.frame_end = 0, END
O = bpy.data.objects

def wpath(pts):
    """pts: [(frame, (x,y))] -> path(f) Vector, yaw(f) along travel"""
    P = catmull([(f, Vector((x, y, 0))) for f, (x, y) in pts])
    def yaw(f):
        d = P(min(f + 3, pts[-1][0])) - P(max(f - 3, pts[0][0]))
        if d.length < 1e-4: d = P(pts[-1][0]) - P(pts[0][0])
        return math.degrees(math.atan2(d.x, -d.y))
    return P, yaw

def walk(H, pts, f0, f1, run=False, yaw_fn=None, arms=True, hands=None):
    P, Y = wpath(pts)
    yf = yaw_fn or Y
    if run: H.walk(P, yf, f0, f1, stride=1.5, duty=0.42, lift=0.16, bob=0.04, crouch=0.08, lean=16.0)
    else: H.walk(P, yf, f0, f1, stride=0.72, duty=0.62, lift=0.08)
    stride = 1.5 if run else 0.72; dist = 0.0; prev = P(f0)
    for f in range(f0, f1 + 1, 2):
        p = P(f); dist += (p - prev).to_2d().length; prev = p
        ph = 2 * math.pi * dist / stride; yw = yf(f); root = Vector((p.x, p.y, ground_z(p.x, p.y) + H.root_head.z))
        for s, sg in (("L", -1), ("R", 1)):
            if hands and s in hands: continue
            sw = math.sin(ph + (0 if s == "L" else math.pi)) * (0.32 if run else 0.18)
            W = rel(root, yw, (sg * 0.22, sw, (-0.05 if run else -0.12) + abs(sw) * 0.25 + (0.15 if run else 0)))
            d, n = hand_dirs(yw, (0, 0.2 + sw, -1 if not run else -0.4), (-sg, 0, 0))
            H.key_hand(s, f, W, d, n, rel(root, yw, (sg * 0.5, -0.45, 0.25)))
            grip(H, s, f, 0.75 if run else 0.35, 0.4)
    return P, yf

# ---------------------------------------------------------------- rigs
CAST = ["Prisoner", "PrisonerOld", "Boy", "Father", "Stepmother", "Guard", "Guard2", "Judge", "Protester1", "Protester2"]
HS = {}
for n in CAST:
    HS[n] = Human(make_human_ctrl(O[n]))
P_, PO, BOY, FA, SM, G1, G2, JU, PR1, PR2 = [HS[n] for n in CAST]
Z = {n: HS[n].root_head.z for n in CAST}

# visibility per character
VIS = {
    "Prisoner": [(0, 3110)],
    "PrisonerOld": [(3100, END)],
    "Boy": [(678, 1421)],
    "Father": [(678, 1040)],
    "Stepmother": [(942, 1421)],
    "Guard": [(0, 1547), (1860, 3228)],
    "Guard2": [(0, 677), (2172, 2897), (3480, END)],
    "Judge": [(1380, 1547), (3480, END)],
    "Protester1": [(3480, END)],
    "Protester2": [(0, 677), (2172, 3227), (3480, END)],
}
for n, rg in VIS.items(): vis_key(human_objs(n), rg)

# ================================================================ BEAT 1 (0-276): guard walks past, key ring swings; prisoner at the bars watches
g1_pts = [(0, (4.2, 1.15)), (140, (1.2, 1.15)), (276, (-2.6, 1.2)), (420, (-6.0, 1.3)), (557, (-9.5, 1.3))]
walk(G1, g1_pts, 0, 557)
face(G1, 0, brow=-0.3); face(G1, 557, brow=-0.3)
PR = Vector((0.4, -0.38, Z["Prisoner"]))
bars = {"L": Vector((0.23, -0.045, 1.32)), "R": Vector((0.575, -0.045, 1.32))}
for f, hd, br, ld in ((0, (5, -35), -0.2, 0.0), (60, (0, -25), -0.6, 0.2), (130, (8, 5), -0.9, 0.35), (200, (5, 35), -1.0, 0.4), (232, (0, 30), -0.8, 0.3)):
    dL, nL = hand_dirs(180, (0, 0.3, 1), (1, 0, 0)); dR, nR = hand_dirs(180, (0, 0.3, 1), (-1, 0, 0))
    pose(P_, f, PR + Vector((0, 0, -0.01 * (f % 2))), yaw=180, spine=(4, hd[1] * 0.3, 0), head=hd,
         hands={"L": (bars["L"], dL, nL, None), "R": (bars["R"], dR, nR, None)}, fingers={"L": 0.85, "R": 0.85})
    face(P_, f, brow=br, lid=ld)
# key ring rides the guard's right hip, swinging
ring = O["KeyRing"]
for f in range(0, 558, 2):
    sc.frame_set(f)
    M = bone_world(O["Guard"], "root"); hip = M @ Vector((-0.2, 0.0, 0.02))
    yw = math.atan2(M.col[1].x, M.col[1].y)
    sw = math.sin(f * 0.25) * 0.5
    key_obj(ring, f, loc=hip, rot=(R_(90) + sw * 0.4, sw, 0))
# memory overlay: glowing key outline floats beside his eyes, then grows and flips
kg = O["KeyGlow"]
vis_key([kg], [(150, 300)])
for f, loc, sc_, rz in ((150, (0.05, 0.12, 1.62), 0.2, 0), (200, (0.15, 0.1, 1.66), 3.2, 0.3), (250, (0.25, 0.05, 1.7), 4.2, 0.6), (300, (0.35, -1.0, 0.9), 2.0, 1.2)):
    key_obj(kg, f, loc=loc, rot=(R_(90), rz, 0), scale=(sc_,) * 3)

# ================================================================ BEAT 2 (276-558): night, sits on the bunk filing scrap into a key
SEAT = 0.47
sit_root = Vector((0.6, -1.85, SEAT + 0.1)); SY = -90       # faces -x (into the cell)
walk(P_, [(236, (0.4, -0.45)), (262, (0.3, -1.2)), (290, (0.35, -1.85))], 236, 290, yaw_fn=lambda f: -10 * (f - 236) / 54 * 9)
feet_sit = {"L": (rel(sit_root, SY, (-0.16, 0.42, 0)).to_2d(), SY), "R": (rel(sit_root, SY, (0.16, 0.42, 0)).to_2d(), SY)}
scrap = O["ScrapKey"]; filev = O["File_Blade"]
def scrap_pose(f):
    return rel(sit_root, SY, (-0.04, 0.36, 0.18))
for f in range(300, 541, 4):
    stroke = math.sin((f - 300) * 2 * math.pi / 22)
    sp = scrap_pose(f)
    key_obj(scrap, f, loc=sp, rot=(R_(90), 0, R_(SY + 90 + 0)))
    fp = sp + Vector((0, -0.01, 0.012)) + rel(Vector((0, 0, 0)), SY, (0.0, 0.03 * stroke, 0)) - Vector((0, 0, 0))
    key_obj(filev, f, loc=fp + Vector((0, 0, 0.008)), rot=(0, R_(-12 + 6 * stroke), R_(SY + 90 + 35)))
    dL, nL = hand_dirs(SY, (1, 0.2, 0), (0, 0, 1)); dR, nR = hand_dirs(SY, (-0.6, 0.6, 0), (0, 0, -1))
    hdx = 6 * math.sin(f * 0.05)
    pose(P_, f, sit_root + Vector((0, 0, 0.004 * stroke)), yaw=SY, flex=-8, feet=feet_sit, spine=(28, 4 * stroke, 0), head=(26, hdx),
         hands={"L": (sp + rel(Vector(), SY, (-0.07, -0.02, -0.01)), dL, nL, None),
                "R": (fp + rel(Vector(), SY, (0.13, -0.03, 0.03)), dR, nR, None)},
         fingers={"L": 0.85, "R": 0.9})
    face(P_, f, brow=-0.9, lid=0.35, jaw=1)
sk = scrap.data.shape_keys.key_blocks["Cut"]
sk.value = 0; sk.keyframe_insert("value", frame=310); sk.value = 1; sk.keyframe_insert("value", frame=530)
# sparks: tiny emissive specks thrown from the scrap edge while filing
spk_mat = emit_mat("Spark", (1.0, 0.55, 0.15), 60.0)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.0025); spark = bpy.context.object; spark.name = "SparkMesh"; spark.data.materials.append(spk_mat); spark.hide_render = True
ps = scrap.modifiers.new("sparks", "PARTICLE_SYSTEM").particle_system.settings
ps.count = 600; ps.frame_start, ps.frame_end = 300, 535; ps.lifetime = 14; ps.normal_factor = 0.6; ps.factor_random = 0.8
ps.render_type = "OBJECT"; ps.instance_object = spark; ps.particle_size = 1.0; ps.size_random = 0.6; ps.effector_weights.gravity = 1.0
ps.emit_from = "FACE"
# file & scrap visible only in their beats; key visible 300-678
vis_key([filev] + list(filev.children), [(300, 545)])
vis_key([scrap], [(300, 678)])

# ================================================================ BEAT 3 (558-678): key turns in the lock, door swings, he slips out
walk(P_, [(541, (0.35, -1.85)), (575, (-0.1, -0.9)), (600, (-0.25, -0.45))], 541, 600)
lockp = Vector((-0.15, 0.08, 1.05))
for f in range(600, 641, 4):
    turn = min(1, max(0, (f - 604) / 20))
    dR, nR = hand_dirs(180, (0, 1, 0), (-1 + turn * 1.0, 0, -turn))
    pose(P_, f, Vector((-0.25, -0.42, Z["Prisoner"] - 0.03)), yaw=170, spine=(10, 0, 0), head=(18, 0),
         hands={"R": (lockp + Vector((0.0, 0.04, 0.0)) + Vector((0, -0.12, 0)), dR, nR, None)}, fingers={"R": 0.9})
    face(P_, f, brow=-0.6, lid=0.25)
door = O["HeroDoor"]
key_obj(door, 0, rot=(0, 0, 0)); key_obj(door, 618, rot=(0, 0, 0)); key_obj(door, 650, rot=(0, 0, R_(-72))); key_obj(door, 1859, rot=(0, 0, R_(-72)))
key_obj(door, 1860, rot=(0, 0, 0)); key_obj(door, 2484, rot=(0, 0, 0)); key_obj(door, 2490, rot=(0, 0, R_(-72))); key_obj(door, 3227, rot=(0, 0, R_(-72)))
key_obj(door, 3228, rot=(0, 0, 0))
walk(P_, [(640, (-0.25, -0.42)), (660, (-0.45, 0.4)), (678, (-0.9, 1.1)), (700, (-1.6, 1.3))], 640, 700)
face(P_, 660, brow=0.4, lid=0.0); face(P_, 700, brow=0.4)

# ================================================================ BEAT 4 (678-942): memory: boy at the workbench taking apart a clock
BR = Vector((0.45, 8.05, Z["Boy"])); BY = 180
for f in range(680, 942, 6):
    t = (f - 680) / 60.0
    jit = 0.012 * math.sin(t * 9); jit2 = 0.01 * math.cos(t * 7)
    dL, nL = hand_dirs(BY, (0.3, 1, -0.4), (0.2, 0, -1)); dR, nR = hand_dirs(BY, (-0.3, 1, -0.5), (-0.2, 0, -1))
    pose(BOY, f, BR + Vector((0, 0, -0.01 * math.sin(t * 3))), yaw=BY, spine=(18, 5 * math.sin(t), 0), head=(22, 6 * math.sin(t * 1.3)),
         hands={"L": (Vector((0.36 + jit, 8.47, 0.8)), dL, nL, None), "R": (Vector((0.55, 8.45 + jit2, 0.81 + abs(jit))), dR, nR, None)},
         fingers={"L": 0.5, "R": 0.7})
    face(BOY, f, brow=0.5, smile=0.8 if t > 0.6 else 0.4, jaw=4)
# father watching from behind, hand on chin, shifting weight
FR = Vector((-0.6, 7.2, Z["Father"]))
for f in range(678, 941, 30):
    s = math.sin((f - 678) / 40)
    dR, nR = hand_dirs(150, (0, 0.2, 1), (0, -1, 0))
    pose(FA, f, FR + Vector((0.02 * s, 0, 0)), yaw=150, side=2 * s, spine=(6, 0, 0), head=(10, 10),
         hands={"R": (rel(FR, 150, (0.05, 0.22, 0.48)), dR, nR, None)}, fingers={"R": 0.6})
    face(FA, f, smile=0.7, brow=0.3)
# a gear spins on the bench (life)
gr = O["Gear_2"]
key_obj(gr, 678, rot=(0, 0, 0)); key_obj(gr, 1128, rot=(0, 0, R_(720)))

# ================================================================ BEAT 5 (942-1128): father passes the worn toolbox; then his empty chair
tbx = O["Toolbox"]
# father walks to the toolbox, lifts it, carries to the boy; boy turns and takes it
walk(FA, [(942, (-0.6, 7.2)), (970, (0.6, 7.3)), (990, (1.75, 7.55))], 942, 990)
H_TB = 0.43
tb_path = [(990, Vector((2.2, 7.6, 0.0))), (1004, Vector((2.15, 7.55, 0.0))), (1030, Vector((1.6, 7.75, 0.35))), (1060, Vector((1.05, 7.8, 0.4))), (1128, Vector((0.95, 7.75, 0.38))), (1421, Vector((0.95, 7.75, 0.38)))]
TBP = catmull(tb_path)
for f in range(990, 1128, 2):
    p = TBP(f); key_obj(tbx, f, loc=p, rot=(0, 0, R_(-15 + (f - 990) * 0.4 if f < 1060 else 13)))
key_obj(tbx, 942, loc=(2.2, 7.6, 0), rot=(0, 0, R_(-15))); key_obj(tbx, 0, loc=(2.2, 7.6, 0), rot=(0, 0, R_(-15)))
for f in range(992, 1041, 4):
    handle = TBP(f) + Vector((0, 0, H_TB + 0.03))
    fr = Vector((1.75 - 0.5 * min(1, (f - 992) / 60), 7.55, Z["Father"] - (0.25 if f < 1010 else 0.05)))
    dR, nR = hand_dirs(-60, (0.4, 0.3, -1), (0, 0, -1)); dL, nL = hand_dirs(-60, (-0.4, 0.3, -1), (0, 0, -1))
    pose(FA, f, fr, yaw=-60 + 30 * min(1, (f - 992) / 40), flex=6, spine=(30 if f < 1010 else 10, 0, 0), head=(15, 0),
         hands={"R": (handle + Vector((0.05, 0, 0.07)), dR, nR, None), "L": (handle + Vector((-0.06, 0, 0.07)), dL, nL, None)},
         fingers={"R": 0.95, "L": 0.95})
    face(FA, f, smile=0.5, brow=0.2)
for f in range(942, 1128, 4):
    t = (f - 942)
    yb = 180 if f < 1000 else 180 - min(70, (f - 1000) * 1.5)
    if f < 1036:
        pose(BOY, f, BR, yaw=yb, spine=(8, 0, 0), head=(5, 20 if f > 990 else 0))
    else:
        handle = TBP(f) + Vector((0, 0, H_TB + 0.03))
        dR, nR = hand_dirs(yb, (0, 0.3, -1), (0, 0, -1))
        pose(BOY, f, BR + Vector((0.15, -0.1, -0.02)), yaw=yb, spine=(12, 0, 0), head=(20, 0),
             hands={"R": (handle + Vector((0.04, 0, 0.07)), dR, nR, None), "L": (handle + Vector((-0.04, 0, 0.07)), dR, nR, None)}, fingers={"R": 0.95, "L": 0.95})
    face(BOY, f, smile=0.9 if f < 1070 else 0.0, frown=0.0 if f < 1070 else 0.6, brow=0.6 if f < 1070 else -0.2)
chair = O["Armchair"]
for f in range(1040, 1422, 10):
    key_obj(chair, f, rot=(0, R_(1.2 * math.sin((f - 1040) / 14)), R_(200)))
key_obj(chair, 0, rot=(0, 0, R_(200)))

# ================================================================ BEAT 6 (1128-1422): stepmother on the phone, angry, pointing; police lights
SR = Vector((6.55, 7.3, Z["Stepmother"])); SYw = 120
walk(SM, [(942, (7.5, 4.0)), (1020, (7.0, 6.0)), (1100, (6.55, 7.3))], 942, 1100)
phone = O["Phone"]
key_obj(phone, 0, loc=(6.9, 7.8, 0.435), rot=(0, 0, R_(200))); key_obj(phone, 1140, loc=(6.9, 7.8, 0.435), rot=(0, 0, R_(200)))
for f in range(1140, 1422, 4):
    t = (f - 1140) / 60
    lift = min(1, (f - 1140) / 30)
    ear = rel(SR, SYw, (0.16, 0.12, 0.62))
    pp = Vector((6.9, 7.8, 0.435)).lerp(ear + Vector((0, 0, -0.42)), lift)
    key_obj(phone, f, loc=pp, rot=(R_(-10 * lift), 0, R_(200 - 60 * lift)))
    pt = 0.5 + 0.5 * math.sin(t * 5)
    dR, nR = hand_dirs(SYw, (0, 0.2, 1), (-1, 0, 0)); dL, nL = hand_dirs(SYw - 60, (0, 1, 0.1), (0, 0, -1))
    pose(SM, f, SR + Vector((0, 0, -0.01 * pt)), yaw=SYw, side=-3, spine=(-4, -14 - 6 * pt, 0), head=(-6 + 4 * pt, -20),
         hands={"R": (pp + Vector((0, 0, 0.36)), dR, nR, None), "L": (rel(SR, SYw - 60, (-0.15, 0.55 + 0.06 * pt, 0.55)), dL, nL, None)},
         fingers={"R": 0.9, "L": 0.35})
    face(SM, f, brow=-1.0, lid=0.25, jaw=6 + 10 * pt, frown=1.0)
# the boy reacts: clutches the toolbox, steps back toward the chair
for f in range(1132, 1422, 6):
    yb = 110 + 20 * min(1, (f - 1132) / 60)
    handle = Vector((0.95, 7.75, 0.38 + H_TB + 0.03))
    pose(BOY, f, BR + Vector((0.15, -0.1, -0.02)), yaw=yb, spine=(4, 0, 0), head=(-5, 15 * math.sin(f / 30)))
    face(BOY, f, brow=0.9, lid=0.0, jaw=6, frown=0.7)
for nm in ("PoliceRed", "PoliceBlue"):
    L = O[nm]; ph = 0 if nm == "PoliceRed" else 1
    L.data.energy = 0; L.data.keyframe_insert("energy", frame=0); L.data.keyframe_insert("energy", frame=1240)
    for f in range(1250, 1560, 8):
        L.data.energy = 2500 if ((f // 8) + ph) % 2 else 50; L.data.keyframe_insert("energy", frame=f)
    L.data.energy = 0; L.data.keyframe_insert("energy", frame=1560)
    for fc in fcurves_of(L.data):
        for k in fc.keyframe_points: k.interpolation = "CONSTANT"

# ================================================================ BEAT 7 (1422-1548): gavel strikes; gate slams
JR = Vector((10.4, 8.15, Z["Judge"])); JY = 0
gav = O["Gavel"]; gpiv = Vector((10.2, 7.48, 1.2))        # handle end in the judge's hand
def gavel_at(ang):
    """gavel rotated up by ang about the handle end (x axis); returns object rotation and location of root"""
    R = Matrix.Rotation(ang, 4, "X") @ Matrix.Rotation(R_(10), 4, "Z")
    root0 = Vector((10.2, 7.25, 1.145)); off = root0 - gpiv
    return gpiv + (R.to_3x3() @ (Matrix.Rotation(R_(-10), 3, "Z") @ off)), R.to_euler()
strike = [(1380, 0.0), (1415, -0.9), (1432, -1.1), (1440, 0.03), (1446, -0.12), (1452, 0.0), (1470, -0.7), (1478, 0.02), (1500, 0.0)]
SP = catmull([(f, a) for f, a in strike])
for f in range(1380, 1548, 2):
    a = SP(f); loc, rot = gavel_at(-a)
    key_obj(gav, f, loc=loc, rot=rot)
    hp = gpiv + Vector((0, 0.06, 0.02))
    dR, nR = hand_dirs(JY, (0, -0.2, 0.3), (1, 0, 0))
    pose(JU, f, JR + Vector((0, 0, -0.05)), yaw=JY, spine=(16, 0, 0), head=(10, 0),
         hands={"R": (hp + Vector((0, 0.04, 0.04)), dR, nR, None), "L": (Vector((10.75, 7.3, 1.2)), *hand_dirs(JY, (0, 1, 0), (0, 0, -1)), None)},
         fingers={"R": 1.0, "L": 0.2})
    face(JU, f, brow=-0.8, lid=0.3, frown=0.5)
key_obj(gav, 0, loc=(10.2, 7.25, 1.145), rot=(0, 0, R_(10)))
gate = O["CorridorGate"]
key_obj(gate, 0, rot=(0, 0, R_(80))); key_obj(gate, 1475, rot=(0, 0, R_(80))); key_obj(gate, 1500, rot=(0, 0, R_(-3)))
key_obj(gate, 1506, rot=(0, 0, R_(1.5))); key_obj(gate, 1512, rot=(0, 0, 0))
key_obj(gate, 2600, rot=(0, 0, 0)); key_obj(gate, 2640, rot=(0, 0, R_(80)))
# guard who slammed it stands behind the gate
for f in (1470, 1500, 1547):
    pose(G1, f, Vector((7.6, 1.6, Z["Guard"])), yaw=-90 if f < 1500 else -80, spine=(5, 0, 0), head=(0, 0))
    face(G1, f, brow=-0.6, frown=0.5)

# ================================================================ BEAT 8 (1548-1860): climbs the razor-wire fence and runs into the fields
FX = 7.0; MESH_Y = -13.8
walk(P_, [(1548, (6.6, -7.0)), (1575, (6.9, -10.5)), (1600, (FX, -13.3))], 1548, 1600, run=True)
for f in range(1600, 1790, 4):
    u = (f - 1600) / 120.0                      # 0..1 climb up to the top
    if f <= 1720:
        rz = Z["Prisoner"] + u * 2.6; ry = MESH_Y + 0.38
        ph = (f - 1600) / 20.0; a = (ph % 2) < 1
        hL = Vector((FX - 0.2, MESH_Y + 0.05, rz + 0.55 + (0.12 if a else -0.05)))
        hR = Vector((FX + 0.2, MESH_Y + 0.05, rz + 0.55 + (-0.05 if a else 0.12)))
        fL = Vector((FX - 0.15, MESH_Y + 0.1, rz - 0.85 + (0.0 if a else 0.18)))
        fR = Vector((FX + 0.15, MESH_Y + 0.1, rz - 0.85 + (0.18 if a else 0.0)))
        root = Vector((FX, ry, rz)); yw = 0; fl = 12
    else:
        v = (f - 1720) / 70.0                    # over the top and down the far side
        root = Vector((FX, MESH_Y + 0.38 - v * 0.9, Z["Prisoner"] + 2.6 + 0.6 * math.sin(math.pi * min(1, v * 1.4)) - max(0, v - 0.6) * 4.0))
        hL = Vector((FX - 0.2, MESH_Y + 0.0, 3.62)); hR = Vector((FX + 0.2, MESH_Y + 0.0, 3.62))
        if v > 0.55: hL = hL + Vector((0, -0.2, -0.3)); hR = hR + Vector((0, -0.2, -0.3))
        fL = root + Vector((-0.15, 0.25 - v * 0.5, -0.8)); fR = root + Vector((0.15, 0.3 - v * 0.5, -0.75)); yw = 0; fl = 25 * (1 - v)
    dd, nn = hand_dirs(0, (0, 0.2, 1), (0, 1, 0))
    P_.key_root(f, root, yaw=yw, flex=fl)
    P_.key_spine(f, flex=fl, head=(-20, 0))
    for s, W, F in (("L", hL, fL), ("R", hR, fR)):
        P_.key_hand(s, f, W, dd, nn, root + Vector((-0.5 if s == "L" else 0.5, 0.3, 0.2)))
        grip(P_, s, f, 0.9, 0.8)
        P_.r.key_world("IK_foot." + s, f, Matrix.Translation(F) @ Matrix.Rotation(R_(-30), 4, "X") @ Matrix.Translation(-P_.ankle[s]) @ P_.r.rest("IK_foot." + s))
        pb = P_.r.PB["Pole_knee." + s]; pn = "Pole_knee." + s
        pb.location = P_.r.rest(pn).to_3x3().inverted() @ (root + Vector((0, -0.7, -0.4)) - P_.r.BN[pn].head_local); pb.keyframe_insert("location", frame=f)
    face(P_, f, brow=-1.0, lid=0.45, jaw=10, frown=0.6)
# drop and land (crouch), then sprint into the dark field
gz = ground_z(FX, MESH_Y - 0.6)
pose(P_, 1792, Vector((FX, MESH_Y - 0.6, gz + Z["Prisoner"] - 0.38)), yaw=0, flex=25, spine=(25, 0, 0), head=(-10, 0))
pose(P_, 1800, Vector((FX, MESH_Y - 0.7, gz + Z["Prisoner"] - 0.3)), yaw=0, flex=22, spine=(20, 0, 0), head=(-10, 0))
walk(P_, [(1802, (FX, MESH_Y - 0.75)), (1830, (FX - 0.6, MESH_Y - 4.5)), (1860, (FX - 1.5, MESH_Y - 9.5))], 1802, 1860, run=True)
face(P_, 1830, brow=-0.6, jaw=12, frown=0.5)
sl = O["Searchlight"]
for f in range(1500, 1870, 20):
    key_obj(sl, f, rot=(R_(55 + 10 * math.sin(f / 45)), 0, R_(-60 + 35 * math.sin(f / 60))))

# ================================================================ BEAT 9 (1860-2172): solitary: door slams shut, he slumps on the bunk
sol = O["SolitaryPanel"]
vis_key([sol], [(1860, 2171), (3228, 3497)])
# slot light into the dark cell
bpy.ops.object.light_add(type="SPOT", location=(0.0, 0.7, 1.3)); slot = bpy.context.object; slot.name = "SlotLight"
slot.data.energy = 0; slot.data.spot_size = R_(30); slot.data.color = (1.0, 0.9, 0.7); slot.rotation_euler = (R_(95), 0, R_(180))
for f, e in ((0, 0), (1859, 0), (1860, 900), (2171, 900), (2172, 0), (3227, 0), (3228, 900), (3497, 900), (3498, 0)):
    slot.data.energy = e; slot.data.keyframe_insert("energy", frame=f)
for fc in fcurves_of(slot.data):
    for k in fc.keyframe_points: k.interpolation = "CONSTANT"
walk(P_, [(1866, (-0.35, -0.5)), (1900, (0.05, -1.3)), (1930, (0.3, -1.85))], 1866, 1930)
for f in range(1932, 2172, 8):
    t = (f - 1932) / 60
    pose(P_, f, sit_root + Vector((0, 0, -0.02)), yaw=SY, flex=-4, feet=feet_sit, spine=(34 - 6 * math.sin(t), 0, 0), head=(30 - 15 * min(1, t / 3), 6 * math.sin(t)),
         hands={"L": (rel(sit_root, SY, (-0.12, 0.42, 0.05)), *hand_dirs(SY, (0, 0.3, -1), (1, 0, 0)), None),
                "R": (rel(sit_root, SY, (0.12, 0.42, 0.05)), *hand_dirs(SY, (0, 0.3, -1), (-1, 0, 0)), None)},
         fingers={"L": 0.6, "R": 0.6})
    face(P_, f, brow=-0.7 + 0.3 * math.sin(t), lid=0.35, frown=0.8)

# ================================================================ BEAT 10 (2172-2484): saws through a window bar
saw = O["Hacksaw"]; barp = Vector((0.0, -3.2, 1.62))
walk(P_, [(2160, (0.3, -1.85)), (2185, (0.05, -2.5))], 2160, 2185)
SWR = Vector((0.05, -2.55, Z["Prisoner"] + 0.03))
for f in range(2186, 2484, 3):
    st = math.sin((f - 2186) * 2 * math.pi / 26)
    sp = barp + Vector((-0.05 + 0.11 * st, 0.03, 0.0))
    key_obj(saw, f, loc=sp, rot=(0, 0, R_(90)))
    handle = sp + Vector((-0.17, 0, 0.0)); tip = sp + Vector((0.17, 0, 0))
    glance = 1 if 2330 < f < 2380 else 0
    dR, nR = hand_dirs(0, (0.3, 1, 0.3), (0, 0, -1)); dL, nL = hand_dirs(0, (-0.2, 1, 0.1), (0, 0, -1))
    pose(P_, f, SWR + Vector((0.03 * st, 0, 0)), yaw=0, spine=(6, 6 * st, 0), head=(-12, 70 * glance),
         hands={"R": (handle + Vector((0, 0.07, 0.02)), dR, nR, None), "L": (tip + Vector((-0.02, 0.07, 0.02)), dL, nL, None)},
         fingers={"R": 0.95, "L": 0.85})
    face(P_, f, brow=-1.0 if not glance else 0.7, lid=0.4 if not glance else 0.0, jaw=4, frown=0.7)
key_obj(saw, 0, loc=(0.9, -2.7, 0.49), rot=(0, 0, R_(30))); key_obj(saw, 2150, loc=(0.9, -2.7, 0.49), rot=(0, 0, R_(30)))
vis_key([saw] + saw.children_recursive, [(2150, 2484)])
# filings falling from the cut
bpy.ops.mesh.primitive_plane_add(size=0.02, location=barp + Vector((0, 0.03, -0.01))); fem = bpy.context.object; fem.name = "FilingsEmitter"; fem.hide_render = True
fmat = bpy.data.materials.new("Filings"); fmat.use_nodes = True; fb_ = fmat.node_tree.nodes["Principled BSDF"]; fb_.inputs["Metallic"].default_value = 1; fb_.inputs["Base Color"].default_value = (0.6, 0.6, 0.62, 1)
bpy.ops.mesh.primitive_cube_add(size=0.002); fil = bpy.context.object; fil.name = "FilingMesh"; fil.data.materials.append(fmat); fil.hide_render = True
pf = fem.modifiers.new("filings", "PARTICLE_SYSTEM").particle_system.settings
pf.count = 900; pf.frame_start, pf.frame_end = 2190, 2480; pf.lifetime = 40; pf.normal_factor = 0.2; pf.factor_random = 0.3
pf.render_type = "OBJECT"; pf.instance_object = fil; pf.particle_size = 1.0; pf.size_random = 0.5; fem.show_instancer_for_render = False
# a notch deepens on the bar: dark ring scaled in
bpy.ops.mesh.primitive_torus_add(major_radius=0.0145, minor_radius=0.003, location=barp); notch = bpy.context.object; notch.name = "BarNotch"
nm_ = bpy.data.materials.new("Notch"); nm_.use_nodes = True; nm_.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.75, 0.74, 0.72, 1); nm_.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 1
notch.data.materials.append(nm_)
key_obj(notch, 0, scale=(1, 1, 0.01)); key_obj(notch, 2200, scale=(1, 1, 0.1)); key_obj(notch, 2480, scale=(1, 1, 1.0))
vis_key([notch], [(2190, 3750)])

# ================================================================ BEAT 11 (2484-2898): bent toothpaste tube held like a gun; guards freeze, then chase
tube = O["ToothpasteTube"]
for c in tube.children_recursive:
    if c.type == "MESH":
        m = c.modifiers.new("bend", "SIMPLE_DEFORM"); m.deform_method = "BEND"; m.angle = R_(85); m.deform_axis = "X"
walk(P_, [(2484, (0.05, -2.5)), (2510, (-0.4, -1.0)), (2530, (-0.5, 0.4)), (2560, (-1.6, 1.4))], 2484, 2560)
GR = [Vector((-4.6, 1.0, Z["Guard"])), Vector((-5.2, 2.0, Z["Guard2"]))]
for f in range(2560, 2660, 4):
    back = (f - 2560) / 100.0
    root = Vector((-1.6 + 0.9 * back, 1.4, Z["Prisoner"])); yw = -90
    hand = rel(root, yw, (0.18, 0.55, 0.45))
    dR, nR = hand_dirs(yw, (0, 1, 0), (-1, 0, 0))
    pose(P_, f, root, yaw=yw, spine=(-4, -5, 0), head=(0, 0), feet={"L": (rel(root, yw, (-0.12, -0.15 + 0.2 * math.sin(f / 9), 0)).to_2d(), yw), "R": (rel(root, yw, (0.14, 0.1, 0)).to_2d(), yw)},
         hands={"R": (hand, dR, nR, None)}, fingers={"R": 0.95})
    face(P_, f, brow=-0.8, lid=0.3, jaw=3)
    for G, gr, gy in ((G1, GR[0], 90), (G2, GR[1], 100)):
        frz = min(1, (f - 2560) / 12)
        up = rel(gr, gy, (0, 0.1, 0.75 * frz))
        dL, nL = hand_dirs(gy, (0, 0.1, 1), (0, 1, 0))
        pose(G, f, gr + Vector((0, 0, -0.03 * frz)), yaw=gy, spine=(-6 * frz, 0, 0), head=(-5, 0),
             hands={"L": (up + rel(Vector(), gy, (-0.35, 0, 0)), dL, nL, None), "R": (up + rel(Vector(), gy, (0.35, 0, 0)), dL, nL, None)}, fingers={"L": 0.1, "R": 0.1})
        face(G, f, brow=1.0 * frz, lid=0, jaw=12 * frz)
walk(P_, [(2660, (-0.7, 1.4)), (2700, (1.8, 1.5)), (2800, (6.5, 1.5)), (2898, (11.5, 1.6))], 2660, 2898, run=True, hands={"R": 1})
for f in range(2660, 2899, 4):
    sc.frame_set(f); M = bone_world(O["Prisoner"], "root"); r = M.translation
    P_.key_hand("R", f, Vector((r.x + 0.3, r.y - 0.25, r.z + 0.45)), Vector((1, 0, 0)), Vector((0, 0, -1)), Vector((r.x - 0.3, r.y - 0.7, r.z + 0.2)))
    grip(P_, "R", f, 0.95)
face(P_, 2700, brow=-0.5, jaw=14, frown=0.4)
walk(G1, [(2672, (-4.6, 1.0)), (2760, (0.5, 1.1)), (2898, (7.0, 1.2))], 2672, 2898, run=True)
walk(G2, [(2685, (-5.2, 2.0)), (2770, (-0.5, 1.9)), (2898, (5.5, 1.8))], 2685, 2898, run=True)
for G in (G1, G2): face(G, 2700, brow=-1.0, jaw=10, frown=0.8)
# bake the tube into his right hand (silhouette)
tube.parent = None
for f in list(range(2486, 2899, 2)):
    sc.frame_set(f)
    M = bone_world(O["Prisoner"], "wrist.R")
    tube.matrix_world = M @ Matrix.Translation((0.0, 0.09, 0.03)) @ Matrix.Rotation(R_(90), 4, "Z")
    tube.keyframe_insert("location", frame=f); tube.rotation_mode = "XYZ"; tube.keyframe_insert("rotation_euler", frame=f)
vis_key([tube] + tube.children_recursive, [(2486, 2898)])
# backlight for the silhouette
bpy.ops.object.light_add(type="SPOT", location=(-6.5, 1.5, 2.2)); bl = bpy.context.object; bl.name = "SilhouetteBacklight"
bl.data.spot_size = R_(60); bl.data.color = (0.8, 0.9, 1.0); bl.rotation_euler = (R_(90), 0, R_(-95))
for f, e in ((0, 0), (2500, 0), (2510, 4000), (2660, 4000), (2700, 0)):
    bl.data.energy = e; bl.data.keyframe_insert("energy", frame=f)

# ================================================================ BEAT 12 (2898-3228): time-lapse in the cell: tally marks, hair greys
tal = bpy.data.materials["Tally_Scratch"].node_tree.nodes["Reveal"].outputs[0]
for f, v in ((0, 0.02), (2898, 0.05), (3228, 0.85), (3750, 0.97)):
    tal.default_value = v; tal.keyframe_insert("default_value", frame=f)
TL = [(2898, "window"), (2940, "sit"), (2980, "scratch"), (3020, "pace"), (3060, "sit"), (3100, "window"), (3140, "scratch"), (3180, "sit")]
for i, (f, kind) in enumerate(TL):
    for H, nm in ((P_, "Prisoner"), (PO, "PrisonerOld")):
        if H is P_ and f > 3100: continue
        if H is PO and f < 3100: continue
        z = Z[nm]; sr = sit_root
        for ff in (f, f + 38):
            w = 0.05 * (ff - f) / 38
            if kind == "sit":
                pose(H, ff, sr + Vector((0, 0, -0.02)), yaw=SY, flex=-4, feet=feet_sit, spine=(30, 0, 0), head=(20 - 30 * w * 10, 0),
                     hands={"L": (rel(sr, SY, (-0.12, 0.42, 0.05)), *hand_dirs(SY, (0, 0.3, -1), (1, 0, 0)), None),
                            "R": (rel(sr, SY, (0.12, 0.42, 0.05)), *hand_dirs(SY, (0, 0.3, -1), (-1, 0, 0)), None)})
            elif kind == "window":
                r = Vector((0.0, -2.62, z)); dd, nn_ = hand_dirs(0, (0, 0.3, 1), (0, 1, 0))
                pose(H, ff, r, yaw=0, spine=(-4, 0, 0), head=(-12, 0),
                     hands={"L": (Vector((-0.08, -3.15, 1.6)), dd, nn_, None), "R": (Vector((0.16, -3.15, 1.6)), dd, nn_, None)}, fingers={"L": 0.9, "R": 0.9})
            elif kind == "scratch":
                r = Vector((-0.85, -1.6 - w * 2, z)); dd, nn_ = hand_dirs(90, (0, 1, 0.2), (0, 0, -1))
                pose(H, ff, r, yaw=90, spine=(4, 0, 0), head=(5, 0), hands={"R": (Vector((-1.33, -1.4 - w * 4, 1.9 - w * 6)), dd, nn_, None)}, fingers={"R": 0.9})
            else:
                r = Vector((-0.5 + w * 10, -1.2, z))
                pose(H, ff, r, yaw=-90, spine=(8, 0, 0), head=(10, 0))
            face(H, ff, brow=-0.3, lid=0.3, frown=0.5)
# day/night strobe through the window
bpy.ops.object.light_add(type="SUN", location=(0, -6, 4)); sun = bpy.context.object; sun.name = "TimeLapseSun"
sun.data.angle = R_(1.5)
for f in range(0, END + 1, 4):
    if 2898 <= f <= 3228:
        day = math.sin((f - 2898) / 330 * 2 * math.pi * 5)
        sun.data.energy = max(0, day) * 6.0; sun.rotation_euler = (R_(70 + 15 * day), 0, R_((f - 2898) * 4.0 % 120 - 60))
        sun.data.color = (1.0, 0.8 + 0.15 * day, 0.6 + 0.3 * day)
    else:
        sun.data.energy = 0.0; sun.rotation_euler = (R_(70), 0, 0)
    sun.data.keyframe_insert("energy", frame=f); sun.keyframe_insert("rotation_euler", frame=f); sun.data.keyframe_insert("color", frame=f)

# ================================================================ BEAT 13 (3228-3498): old man in solitary, the light shifts across decades
for f in range(3228, 3500, 10):
    t = (f - 3228) / 270
    pose(PO, f, sit_root + Vector((0, 0, -0.02)), yaw=SY, flex=-4, feet=feet_sit, spine=(30 - 10 * t, 0, 0), head=(25 - 35 * t, 10 * math.sin(t * 4)),
         hands={"L": (rel(sit_root, SY, (-0.12, 0.4, 0.06)), *hand_dirs(SY, (0, 0.3, -1), (1, 0, 0)), None),
                "R": (rel(sit_root, SY, (0.12, 0.4, 0.06)), *hand_dirs(SY, (0, 0.3, -1), (-1, 0, 0)), None)}, fingers={"L": 0.5, "R": 0.5})
    face(PO, f, brow=-0.2 + 0.6 * t, lid=0.5 - 0.4 * t, frown=0.4)
for f in range(3228, 3500, 6):
    slot.data.color = (1.0, 0.9 - 0.3 * ((f - 3228) / 270), 0.7 - 0.2 * ((f - 3228) / 270)); slot.data.keyframe_insert("color", frame=f)
    slot.rotation_euler = (R_(95), 0, R_(180 + 14 * math.sin((f - 3228) / 60))); slot.keyframe_insert("rotation_euler", frame=f)

# ================================================================ BEAT 14-15 (3498-3750): protesters with blank placards & candles; old man at the window
M_CARD = bpy.data.materials.new("Cardboard"); M_CARD.use_nodes = True
cb = M_CARD.node_tree.nodes["Principled BSDF"]; cb.inputs["Base Color"].default_value = (0.78, 0.74, 0.66, 1); cb.inputs["Roughness"].default_value = 0.9
nz = M_CARD.node_tree.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 30
bp = M_CARD.node_tree.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.15
M_CARD.node_tree.links.new(nz.outputs["Fac"], bp.inputs["Height"]); M_CARD.node_tree.links.new(bp.outputs["Normal"], cb.inputs["Normal"])
PROT = [(PR1, "Protester1", Vector((-1.4, -17.4)), 0), (PR2, "Protester2", Vector((-0.2, -17.8)), 0), (G2, "Guard2", Vector((1.1, -17.5)), 0), (JU, "Judge", Vector((2.3, -18.1)), 0)]
for i, (H, nm, xy, yw) in enumerate(PROT):
    bpy.ops.mesh.primitive_cube_add(size=1); card = bpy.context.object; card.name = "Placard_%d" % i
    card.scale = (0.55, 0.012, 0.4); bpy.ops.object.transform_apply(scale=True); card.data.materials.append(M_CARD)
    bv = card.modifiers.new("b", "BEVEL"); bv.width = 0.004
    stick = cyl("PlacardStick_%d" % i, (0, 0, -0.75), (0, 0, -0.15), 0.012, bpy.data.materials["Wood"]) if "cyl" in globals() else None
    if stick is None:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.7, location=(0, 0, -0.5)); stick = bpy.context.object; stick.name = "PlacardStick_%d" % i
        stick.data.materials.append(bpy.data.materials["Wood"])
    stick.parent = card
    vis_key([card, stick], [(3480, END)])
    gz = ground_z(xy.x, xy.y); root = Vector((xy.x, xy.y, gz + Z[nm]))
    for f in range(3480, END + 1, 6):
        bob = 0.08 * math.sin(f / 9 + i * 1.7)
        cp = rel(root, yw, (0, 0.35, 0.95 + bob))
        key_obj(card, f, loc=cp + Vector((0, 0, 0.0)), rot=(0, R_(4 * math.sin(f / 13 + i)), 0))
        sp_ = cp + Vector((0, 0, -0.45))
        dd, nn_ = hand_dirs(yw, (0.0, 0.2, 1), (0, 1, 0))
        pose(H, f, root + Vector((0, 0, -0.01 * bob)), yaw=yw + 180 if False else yw + 180, spine=(-3, 5 * math.sin(f / 20 + i), 0), head=(-10, 0),
             hands={"L": (sp_ + Vector((-0.02, 0.05, -0.05)), dd, nn_, None), "R": (sp_ + Vector((0.02, 0.05, -0.2)), dd, nn_, None)}, fingers={"L": 0.95, "R": 0.95})
        face(H, f, brow=0.2, jaw=4 + 8 * max(0, math.sin(f / 7 + i)), frown=0.3)
# candles flicker
cd = O["Candles"]; cd.location = (0.4, -17.0, ground_z(0.4, -17.0))
for k, (x, y) in enumerate(((0.4, -17.0), (-0.9, -16.9), (1.6, -17.1))):
    if k:
        c2 = cd.copy(); sc.collection.objects.link(c2); c2.location = (x, y, ground_z(x, y))
        for ch in cd.children:
            cc = ch.copy(); sc.collection.objects.link(cc); cc.parent = c2
    bpy.ops.object.light_add(type="POINT", location=(x, y, ground_z(x, y) + 0.5)); cl = bpy.context.object; cl.name = "CandleLight_%d" % k
    cl.data.color = (1.0, 0.6, 0.25); cl.data.shadow_soft_size = 0.02
    for f in range(3460, END + 1, 3):
        cl.data.energy = 25 + 10 * random.random(); cl.data.keyframe_insert("energy", frame=f)
    cl.data.energy = 0; cl.data.keyframe_insert("energy", frame=3440)
# the old man at the window, looking out
for f in range(3498, END + 1, 8):
    t = (f - 3498) / 252
    r = Vector((0.0, -2.62, Z["PrisonerOld"])); dd, nn_ = hand_dirs(0, (0, 0.3, 1), (0, 1, 0))
    pose(PO, f, r + Vector((0, 0, -0.005 * math.sin(f / 20))), yaw=0, spine=(-2, 0, 0), head=(-10, 4 * math.sin(f / 50)),
         hands={"L": (Vector((-0.08, -3.15, 1.62)), dd, nn_, None), "R": (Vector((0.16, -3.15, 1.62)), dd, nn_, None)}, fingers={"L": 0.9, "R": 0.9})
    face(PO, f, brow=0.4, lid=0.15, smile=0.2 * t)

# ================================================================ corridor/inmate life: neighbour inmate paces in cell x=3; second guard at the far end
for rg in ((0, 677), (2172, 3227)):
    pts = []; f = rg[0]; k = 0
    while f < rg[1]:
        pts.append((f, (2.4 + 1.2 * (k % 2), -1.4 - 0.6 * ((k // 2) % 2)))); f += 70; k += 1
    walk(PR2, pts, pts[0][0], pts[-1][0])
walk(G2, [(0, (-8.5, 2.2)), (300, (-6.5, 2.1)), (677, (-9.0, 2.2))], 0, 677)
# corridor lights: lights-out at night (beat 2), off in solitary beats, flicker on one tube
for l in [o for o in O if o.name.startswith("CorrLight_")]:
    e0 = l.data.energy
    for f, e in ((0, e0), (276, e0), (300, e0 * 0.25), (557, e0 * 0.25), (580, e0), (1859, e0), (1860, e0 * 0.1), (2171, e0 * 0.1), (2172, e0 * 0.35),
                 (2484, e0), (2898, e0), (2899, e0 * 0.35), (3227, e0 * 0.35), (3228, e0 * 0.05), (3497, e0 * 0.05), (3498, e0 * 0.3)):
        l.data.energy = e; l.data.keyframe_insert("energy", frame=f)
fl = O["CorrLight_4"]
for f in range(0, 700, 7):
    if random.random() < 0.15:
        fl.data.energy = 15; fl.data.keyframe_insert("energy", frame=f); fl.data.energy = 120; fl.data.keyframe_insert("energy", frame=f + 3)

# dust motes drifting in the air of the cell block (life in every interior frame)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.2, 1.5)); dv = bpy.context.object; dv.name = "DustVolume"; dv.scale = (6, 3.2, 1.4)
dv.hide_render = True; dv.display_type = "WIRE"
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.0012); dm = bpy.context.object; dm.name = "DustMote"; dm.hide_render = True
dmat = emit_mat("Dust", (1.0, 0.95, 0.85), 3.0); dm.data.materials.append(dmat)
pd = dv.modifiers.new("dust", "PARTICLE_SYSTEM").particle_system.settings
pd.count = 1500; pd.frame_start, pd.frame_end = -200, -199; pd.lifetime = 5000; pd.emit_from = "VOLUME"; pd.normal_factor = 0
pd.effector_weights.gravity = 0.0; pd.brownian_factor = 0.02; pd.render_type = "OBJECT"; pd.instance_object = dm; dv.show_instancer_for_render = False
sc.frame_start = 0

# ================================================================ CAMERA: one continuous Catmull-Rom move through every framing
camd = bpy.data.cameras.new("CAM_Main"); cam = bpy.data.objects.new("CAM_Main", camd); sc.collection.objects.link(cam); sc.camera = cam
camd.dof.use_dof = True; camd.dof.aperture_fstop = 2.8; camd.clip_start = 0.02; camd.sensor_width = 36
CK = [
 # beat 1: corridor, guard & key ring, then the prisoner's eyes
 (0,   (5.2, 2.4, 0.45), (3.4, 1.0, 1.0), 24, 0),
 (45,  (3.5, 1.9, 0.75), (2.4, 1.1, 0.95), 30, -4),
 (95,  (2.0, 1.55, 0.9), (1.25, 1.0, 0.95), 45, 0),
 (150, (0.9, 0.85, 1.55), (0.38, -0.3, 1.62), 40, 0),
 (205, (0.42, 0.32, 1.66), (0.38, -0.3, 1.66), 70, 0),
 # beat 2: rise over the bars into the night cell, down to the hands filing
 (276, (0.40, 0.05, 2.35), (0.3, -1.6, 0.8), 28, 0),
 (330, (-0.35, -1.0, 1.4), (0.2, -1.85, 0.72), 32, 0),
 (390, (-0.15, -1.6, 0.95), (0.2, -1.85, 0.72), 45, 8),
 (450, (-0.05, -2.35, 0.95), (0.25, -1.85, 0.75), 40, 0),
 (510, (-0.3, -1.75, 1.35), (0.45, -1.85, 1.25), 38, 0),
 # beat 3: the lock from the corridor side, door swings, he steps out
 (558, (0.2, 0.5, 1.15), (-0.15, 0.05, 1.05), 45, 0),
 (612, (0.55, 0.85, 1.25), (-0.2, -0.1, 1.05), 32, 0),
 (660, (0.8, 2.2, 1.5), (-0.7, 0.6, 1.2), 26, 0),
 # beat 4: turn and fly through the far wall into the memory workshop
 (690, (0.6, 2.75, 1.5), (0.6, 4.5, 1.3), 26, 0),
 (712, (0.55, 5.6, 1.45), (0.45, 8.3, 0.9), 28, 0),
 (770, (0.9, 7.2, 1.2), (0.45, 8.45, 0.82), 35, 0),
 (830, (0.75, 8.0, 1.05), (0.45, 8.5, 0.78), 55, 0),
 (890, (0.95, 8.25, 1.25), (0.45, 8.0, 1.25), 40, 0),
 # beat 5: two-shot of the handover, then rack to the empty chair
 (942, (2.4, 6.4, 1.4), (1.2, 7.7, 1.0), 30, 0),
 (1000, (2.6, 6.3, 1.0), (1.5, 7.6, 0.8), 32, 0),
 (1050, (1.9, 6.6, 1.05), (1.0, 7.75, 0.9), 38, 0),
 (1095, (3.3, 6.3, 1.2), (4.4, 7.4, 0.7), 35, 0),
 # beat 6: past the chair to the stepmother on the phone, drift to the window lights
 (1128, (4.6, 6.1, 1.5), (6.55, 7.3, 1.45), 30, 0),
 (1190, (5.6, 6.4, 1.55), (6.55, 7.3, 1.5), 45, 0),
 (1250, (5.3, 5.8, 1.5), (6.5, 7.3, 1.4), 30, 0),
 (1320, (6.2, 5.2, 1.5), (8.2, 5.7, 1.55), 28, 0),
 (1385, (7.6, 5.7, 1.55), (8.6, 5.7, 1.5), 28, 0),
 # beat 7: through the window to the gavel, whip back through the wall to the gate slam
 (1422, (9.4, 6.3, 1.3), (10.1, 7.3, 1.2), 35, 0),
 (1445, (9.85, 6.8, 1.25), (10.1, 7.3, 1.2), 50, 0),
 (1470, (10.2, 4.2, 1.6), (9.4, 1.5, 1.4), 28, 15),
 (1500, (10.4, 2.0, 1.5), (8.7, 1.3, 1.4), 30, 0),
 # beat 8: through cell x=6 and its window into the night yard; crane up the fence with him, over, chase
 (1525, (6.1, -1.2, 1.7), (6.0, -4.0, 1.7), 26, 0),
 (1548, (6.05, -3.6, 1.72), (6.6, -8.0, 1.2), 24, 0),
 (1590, (5.4, -10.6, 0.5), (7.0, -13.4, 1.0), 24, 0),
 (1650, (5.9, -12.0, 1.6), (7.0, -13.8, 2.0), 26, 0),
 (1710, (6.0, -12.3, 3.2), (7.0, -13.8, 3.5), 26, 0),
 (1760, (7.6, -12.6, 4.6), (7.0, -14.2, 3.6), 24, 0),
 (1810, (8.2, -15.0, 1.6), (6.9, -16.5, 1.0), 26, 0),
 # beat 9: back to the building, in through the hero window: solitary
 (1860, (6.0, -19.5, 1.4), (5.6, -23.5, 1.0), 26, 0),
 (1880, (2.0, -9.5, 2.5), (0.0, -3.2, 1.7), 30, 0),
 (1905, (0.0, -3.6, 1.72), (0.0, -2.0, 1.4), 26, 0),
 (1950, (-0.2, -2.6, 1.6), (0.4, -1.6, 0.8), 24, 0),
 (2010, (-0.7, -2.3, 1.1), (0.4, -1.8, 0.95), 30, 0),
 (2080, (-0.6, -1.0, 1.3), (0.5, -2.0, 0.9), 30, 0),
 (2140, (-0.3, -1.9, 1.7), (0.0, -3.0, 1.6), 26, 0),
 # beat 10: the saw on the bar, macro, his straining face, glance at the door
 (2172, (-0.35, -2.75, 1.7), (0.0, -3.2, 1.62), 40, 0),
 (2230, (0.3, -2.9, 1.62), (0.0, -3.2, 1.62), 55, 0),
 (2290, (0.3, -2.65, 1.78), (0.05, -2.55, 1.72), 38, 0),
 (2360, (-0.25, -2.35, 1.6), (0.05, -2.55, 1.7), 35, 0),
 (2430, (-0.2, -2.9, 1.5), (0.0, -3.2, 1.62), 45, 0),
 # beat 11: out to the corridor: silhouette profile, swing to frozen guards, chase dolly
 (2484, (0.3, -1.6, 1.5), (-0.3, 0.6, 1.4), 26, 0),
 (2545, (-1.2, 2.7, 1.25), (-1.5, 1.2, 1.5), 28, 0),
 (2600, (-1.4, 2.8, 1.3), (-4.0, 1.3, 1.5), 30, 0),
 (2650, (-2.6, 2.6, 1.6), (-4.8, 1.4, 1.5), 34, 0),
 (2700, (1.5, 2.2, 1.3), (-1.0, 1.4, 1.2), 24, 0),
 (2760, (4.8, 2.2, 1.2), (2.0, 1.4, 1.2), 24, 0),
 (2820, (5.5, 2.4, 1.6), (3.5, 1.4, 1.1), 26, 0),
 # beat 12: turn into the hero cell; time-lapse orbit; slide along the tally wall
 (2898, (0.6, 0.8, 1.9), (0.0, -2.0, 1.2), 22, 0),
 (2960, (0.9, -0.6, 1.8), (-0.3, -2.4, 1.2), 22, 0),
 (3030, (0.9, -2.7, 1.7), (-0.4, -1.4, 1.1), 22, 0),
 (3100, (-0.2, -2.8, 1.5), (0.4, -1.4, 1.1), 22, 0),
 (3170, (-0.6, -0.8, 1.8), (-1.37, -1.6, 1.7), 28, 0),
 # beat 13: slow circle around the old man in solitary
 (3228, (-0.2, -0.9, 1.5), (0.55, -1.85, 1.0), 30, 0),
 (3300, (-0.45, -1.8, 1.25), (0.55, -1.85, 1.05), 32, 0),
 (3370, (-0.3, -2.7, 1.35), (0.55, -1.85, 1.05), 32, 0),
 (3440, (0.2, -2.8, 1.7), (0.6, -1.8, 1.15), 30, 0),
 # beat 14: past him, out through the window, over the fence to the protesters
 (3498, (0.0, -2.2, 1.85), (0.0, -3.5, 1.75), 26, 0),
 (3525, (0.0, -3.5, 1.72), (0.0, -10.0, 2.0), 24, 0),
 (3570, (0.2, -11.0, 4.6), (0.4, -17.5, 1.5), 24, 0),
 (3618, (0.8, -15.2, 1.3), (0.3, -17.6, 1.4), 28, 0),
 # beat 15: swing back to the building, push to his face at the window, then pull back away from the bars and settle
 (3655, (0.5, -10.0, 2.6), (0.0, -3.2, 1.75), 30, 0),
 (3700, (0.0, -3.62, 1.74), (0.0, -2.6, 1.68), 40, 0),
 (3750, (0.0, -5.0, 1.95), (0.0, -2.8, 1.65), 32, 0),
]
build_camera(cam, CK)
for f, fs in ((0, 2.8), (676, 2.8), (700, 1.6), (1420, 1.6), (1440, 2.8)):
    camd.dof.aperture_fstop = fs; camd.dof.keyframe_insert("aperture_fstop", frame=f)

# beats.json for VO retime
LINES = ["glance at a guard's key", "file a piece of scrap metal", "let himself out of prison", "as an autistic child", "when his father died",
         "his stepmother called the police", "sentenced to four years", "after just one month", "That added more time", "makeshift saw",
         "shaped a toothpaste tube", "after 13 escape attempts", "27 of those spent in solitary", "people have protested", "he's still in prison to this day"]
import json
json.dump([{"beat": i + 1, "frame": B[i], "first_words": LINES[i]} for i in range(15)], open(HERE + "EscapeArtist_v001/beats.json", "w"), indent=1)

# render settings (farm)
sc.render.engine = "CYCLES"; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.cycles.denoiser = "OPENIMAGEDENOISE"; sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.fps = 60; sc.render.fps_base = 1.0
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
sc.render.image_settings.file_format = "PNG"
for o in O:
    if o.type == "EMPTY": o.hide_render = True
for n in ("PCam",):
    if n in O: bpy.data.objects.remove(O[n])
sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ANIMATED", OUT)
