"""PrisonKeyCake blocking animation (60 fps, frames 1-1890).
blender -b work/scene.blend --python scripts/03_animate.py -- work/anim.blend"""
import sys, os, math, random
import bpy
from mathutils import Vector, Matrix, Quaternion
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
exec(open(os.path.join(HERE, "03_anim_core.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; random.seed(66)
OB = bpy.data.objects
TABLE_Z = sc["TABLE_Z"]; TIN_P = Vector(sc["TIN_P"]); LOCK_C = Vector(sc["LOCK_C"]); CANDLE_P = Vector(sc["CANDLE_P"])
BENCH_Z = sc["BENCH_Z"]; MOULD_P = Vector(sc["MOULD_P"]); CAKE2_P = Vector(sc["CAKE2_P"]); PBOX_P = Vector(sc["PBOX_P"])
GY = sc["GOV_Y"]; TOPZ = sc["GOV_TOPZ"]
WAX = OB["WaxPool"]; WAXM = OB["WaxMold_Pocket"]
KM, K1, K2 = OB["Key_Master"], OB["Key_Copy1"], OB["Key_Copy2"]
UP = V(0, 0, 1)

def end_walk(a, f1, path, yaw_fn, hold_until=None):
    p = path(f1); yw = yaw_fn(f1)
    for s in "LR":
        a.plant(s, f1 - 1, f1, a.h.foot_xy(s, p, yw), yw, 0.0)
    return p, yw

# ================================================================== PRISONER
P = Actor("Prisoner")
STA = V(0.92, 0.97, 0.99)            # at the table, facing +Y
DOOR_ST = V(1.5, 0.9, 1.0)           # at the door (beyond the lock), facing +X
P.stand(1, STA, 180)
# key frames for KEY_M (prop drives the hands)
WAX_TOP = TIN_P.z + 0.012 + 0.0035
POOL_M = Matrix.Translation(WAX.location) @ Matrix.Rotation(WAX.rotation_euler.z, 4, 'Z')
def key_on_wax(dz):
    M = POOL_M.copy(); M.translation = WAX.location + V(0, 0, 0.0035 + 0.003 + dz); return M
K_HOLD = mat_from(V(1.02, 1.30, 1.30), V(0.3, 0.4, 0.85), V(-1, 0.25, 0.1))
K_LOOK = mat_from(V(0.96, 1.22, 1.16), V(0.6, 0.2, 0.35), V(0, -0.3, 1))
K_POCKET = mat_from(V(0.82, 1.08, 1.28), V(0, 0, -1), V(0, -1, 0))
def km_path(f, base=0):
    f = f - base
    if f <= 60: return mlerp(K_HOLD, mat_from(V(1.0, 1.28, 1.24), V(0.2, 0.5, 0.85), V(-1, 0.2, 0.1)), ss(f, 0, 60))
    if f <= 110: return mlerp(mat_from(V(1.0, 1.28, 1.24), V(0.2, 0.5, 0.85), V(-1, 0.2, 0.1)), key_on_wax(0.05), ss(f, 60, 110))
    if f <= 150: return mlerp(key_on_wax(0.05), key_on_wax(0.0), ss(f, 110, 150))
    if f <= 230: return mlerp(key_on_wax(0.0), key_on_wax(-0.0042), ss(f, 150, 230))
    if f <= 258: return key_on_wax(-0.0042)
    if f <= 292: return mlerp(key_on_wax(-0.0042), key_on_wax(0.11) @ Matrix.Rotation(R_(-35), 4, 'X'), ss(f, 258, 292))
    if f <= 340: return mlerp(key_on_wax(0.11) @ Matrix.Rotation(R_(-35), 4, 'X'), K_LOOK, ss(f, 292, 340))
    return mlerp(K_LOOK, K_POCKET, ss(f, 340, 380))
bake_obj(KM, 1, 380, km_path)
def bow(M): return M @ V(-0.045, 0, 0)
def shaft(M): return M @ V(0.03, 0, 0)
def hand_on_key(M, press=False):
    x = (M.to_3x3() @ V(1, 0, 0)).normalized(); z = (M.to_3x3() @ V(0, 0, 1)).normalized()
    if press:   # fingertips on the bow ring, the palm beyond the key's end, so the key stays visible
        return grip_hand(bow(M) - x * 0.05 + z * 0.056, x + V(0, 0, -0.5), -z)
    return grip_hand(bow(M), x, -z)
P.hand_fn["R"].append((1, 380, lambda f: hand_on_key(km_path(f), press=110 <= f <= 258)))
def lhand_press(f):
    M = km_path(f); z = (M.to_3x3() @ V(0, 0, 1)).normalized(); x = (M.to_3x3() @ V(1, 0, 0)).normalized()
    return grip_hand(M @ V(0.12, -0.012, 0) + z * 0.056, -x + V(0, 0, -0.5), -z)
P.hand_fn["L"].append((150, 252, lhand_press))
TABLE_EDGE_L = V(0.66, 1.31, TABLE_Z + 0.045)
LH_TABLE = grip_hand(TABLE_EDGE_L + V(0, 0.05, 0), V(0.1, 1, -0.1), V(0, 0, -1))
P.k(1, root=STA, yaw=180, flex=8, sp_flex=14, h_pitch=18, h_yaw=0, sp_twist=0, cL=20, cR=55, hL=LH_TABLE)
P.k(30, sp_twist=-10, h_yaw=-45, h_pitch=5, flex=6)                       # glance at the door
P.k(62, sp_twist=-4, h_yaw=-12, h_pitch=22)
P.k(100, sp_twist=0, h_yaw=0, h_pitch=40, sp_flex=26, flex=14, root=STA + V(0, 0.04, -0.03))
P.k(130, hL=LH_TABLE, cL=25)
P.k(150, cL=8, cR=10)
P.k(190, root=STA + V(0, 0.07, -0.08), flex=20, sp_flex=36, h_pitch=45, side=2)     # bear down
P.k(232, root=STA + V(0, 0.07, -0.09), flex=21, sp_flex=38, side=-2)
P.k(252, hL=LH_TABLE, cL=20)
P.k(258, cR=30)
P.k(262, root=STA + V(0, 0.06, -0.06), flex=18, sp_flex=30, h_pitch=50, cR=55)
P.k(294, root=STA + V(0, 0.05, -0.04), flex=16, sp_flex=26, h_pitch=40)
P.k(300, root=STA + V(0, 0.0, 0.0), flex=6, sp_flex=12, h_pitch=20, h_yaw=10, hL=HANG["L"], cL=15)
P.k(345, h_yaw=-35, sp_twist=-8, h_pitch=8)                               # checks the door again
P.k(380, h_yaw=-5, sp_twist=0, h_pitch=15, hR=B((-0.12, -0.2, 0.25), (0, 0, -1), (0, 1, 0)), cR=40)
P.k(400, hR=HANG["R"], hL=HANG["L"], cL=15, cR=15, flex=4, sp_flex=8)
# off-screen while the camera is outside: walks to the door for the night attempt
P.k(600, root=STA, yaw=180)
pth, yfn = P.walk(610, 700, [(0.92, 0.97), (1.2, 0.95), (1.5, 0.9)], stride=0.6, yaw_override=lambda f: lerp(180, 90, ss(f, 610, 690)))
arm_swing(P, 610, 700, pth)
end_walk(P, 700, pth, yfn)
P.k(700, root=DOOR_ST, yaw=90, flex=4, sp_flex=6, h_pitch=8, h_yaw=0, hR=HANG["R"], hL=HANG["L"])
P.k(830, root=DOOR_ST, yaw=90)
# ---- beat 6: the first copy jams (f871-1056)
def lock_key(depth, ang):
    """key pointing +X into the keyhole, bit down; depth 0 = fully in; ang = turn about X"""
    base = mat_from(V(LOCK_C.x - 0.005 - depth, LOCK_C.y, LOCK_C.z - 0.004), V(1, 0, 0), V(0, 1, 0))
    return base @ Matrix.Rotation(R_(ang), 4, 'X')
JAM = [(870, None), (894, (0.05, 0)), (900, (0.03, 0)), (903, (0.032, 0)), (910, (0.0, 0)), (920, (0.0, 14)), (925, (0.0, 3)), (934, (0.0, 16)),
       (939, (0.0, 2)), (948, (0.0, 2)), (958, (0.0, -12)), (964, (0.0, 4)), (972, (0.0, 15)), (977, (0.0, 0)), (1000, (0.0, 0)), (1018, (0.06, 0))]
K1_HAND = mat_from(V(1.62, 0.64, 1.08), V(0.6, -0.3, 0.4), V(0, -0.5, 1))
def k1_path(f):
    if f < 894: return mlerp(K1_HAND, lock_key(0.05, 0), ss(f, 866, 894))
    for (fa, va), (fb, vb) in zip(JAM[1:], JAM[2:]):
        if fa <= f <= fb:
            t = ss(f, fa, fb); return lock_key(lerp(va[0], vb[0], t), lerp(va[1], vb[1], t))
    if f <= 1040: return mlerp(lock_key(0.06, 0), K1_HAND, ss(f, 1018, 1040))
    return K1_HAND
bake_obj(K1, 845, 1040, k1_path)
def hand_lock(M):
    x = (M.to_3x3() @ V(1, 0, 0)).normalized(); y = (M.to_3x3() @ V(0, 1, 0)).normalized()
    return grip_hand(bow(M) - x * 0.05, x + V(0, 0.1, 0), y)
P.hand_fn["R"].append((845, 1040, lambda f: hand_lock(k1_path(f))))
DOOR_FACE_X = 2.05
LH_DOOR = grip_hand(V(1.96, 1.08, 1.34), V(0, 0.2, 1), V(1, 0, 0))
P.k(845, root=DOOR_ST, yaw=90, sp_flex=10, h_pitch=20, cR=50)
P.k(894, root=DOOR_ST + V(0.04, 0, -0.01), sp_flex=14, h_pitch=26, h_yaw=-26, hL=LH_DOOR, cL=10)
P.k(920, sp_twist=-6, side=3, h_yaw=-28)
P.k(934, sp_twist=-10, side=5, h_pitch=30, flex=8)
P.k(940, h_yaw=-38, h_pitch=8, sp_twist=-4)          # a light passes outside: freezes, eyes to the gap under the door
P.k(950, h_yaw=-32, h_pitch=12)
P.k(958, sp_twist=4, side=-3, h_yaw=-24, h_pitch=26)
P.k(972, sp_twist=-12, side=6, flex=10, h_pitch=34)                  # strain
P.k(982, hL=grip_hand(V(DOOR_FACE_X - 0.25, 0.76, 1.42), V(0, -0.2, 1), V(1, 0, 0)), sp_twist=6, h_pitch=10, h_yaw=10)  # wind up
P.k(992, hL=grip_hand(V(DOOR_FACE_X, 0.74, 1.40), V(0, -0.2, 1), V(1, 0, 0)), sp_twist=-4, flex=12)            # slap
P.k(998, root=DOOR_ST + V(0.09, 0, -0.03), flex=14)
P.k(1018, root=DOOR_ST + V(0.14, -0.08, -0.08), flex=22, sp_flex=24, h_pitch=40, h_yaw=0, sp_twist=0, side=0)   # forehead to the door
P.k(1034, root=DOOR_ST + V(0.12, -0.08, -0.06))
P.k(1046, root=DOOR_ST, flex=6, sp_flex=10, h_pitch=12, hL=HANG["L"], hR=HANG["R"], cR=20)
# ---- beat 7: second impression + wait (1057-1302)
pth, yfn = P.walk(1046, 1100, [(1.5, 0.9), (1.2, 0.95), (0.92, 0.97)], stride=0.6, yaw_override=lambda f: lerp(90, 180, ss(f, 1046, 1094)))
arm_swing(P, 1046, 1100, pth)
end_walk(P, 1100, pth, yfn)
P.k(1100, root=STA, yaw=180, flex=8, sp_flex=16, h_pitch=30, hL=LH_TABLE, cL=20)
B7 = 1100 - 110 + 10    # re-use the beat-1 key path shifted (press at ~1110-1180)
def km2(f):
    g = f - B7
    if g < 110: return mlerp(K_POCKET, key_on_wax(0.05), ss(g, 60, 110))
    if g <= 258: return km_path(min(g, 230) if g < 230 else g)
    return km_path(g)
# condensed second press: 1060-1195
def km_b7(f):
    if f <= 1112: return mlerp(K_POCKET, key_on_wax(0.05), ss(f, 1098, 1112))
    if f <= 1122: return mlerp(key_on_wax(0.05), key_on_wax(0.0), ss(f, 1112, 1122))
    if f <= 1150: return mlerp(key_on_wax(0.0), key_on_wax(-0.0042), ss(f, 1122, 1150))
    if f <= 1158: return key_on_wax(-0.0042)
    if f <= 1170: return mlerp(key_on_wax(-0.0042), K_LOOK, ss(f, 1158, 1170))
    return mlerp(K_LOOK, K_POCKET, ss(f, 1170, 1180))
bake_obj(KM, 1098, 1180, km_b7)
key_hide(KM, [(1, False), (382, True), (1098, False), (1182, True)])
P.hand_fn["R"].append((1098, 1180, lambda f: hand_on_key(km_b7(f), press=1112 <= f <= 1158)))
P.hand_fn["L"].append((1122, 1156, lambda f: (lambda M: grip_hand(M @ V(0.12, -0.012, 0) + M.to_3x3() @ V(0, 0, 0.056), -(M.to_3x3() @ V(1, 0, 0)) + V(0, 0, -0.5), -(M.to_3x3() @ V(0, 0, 1))))(km_b7(f))))
P.k(1122, root=STA + V(0, 0.07, -0.08), flex=20, sp_flex=36, h_pitch=45, cR=10, cL=8)
P.k(1156, root=STA + V(0, 0.07, -0.09), flex=21, sp_flex=38, hL=LH_TABLE)
# hands the mould up through the window bars (1182-1215)
WIN_C = V(0.80, 1.99, 1.665)
def mold_up(f):
    A = Matrix.Translation(WAX.location + V(0, 0, 0.004))
    Bm = Matrix.Translation(WIN_C + V(0, -0.12, 0.0)) @ Matrix.Rotation(R_(70), 4, 'X')
    Cm = Matrix.Translation(WIN_C + V(0, 0.05, -0.08)) @ Matrix.Rotation(R_(10), 4, 'X')
    Dm = Matrix.Translation(WIN_C + V(0, 0.45, -0.08)) @ Matrix.Rotation(R_(10), 4, 'X')
    if f <= 1200: return mlerp(A, Bm, ss(f, 1182, 1200))
    if f <= 1214: return mlerp(Bm, Cm, ss(f, 1200, 1214))
    return mlerp(Cm, Dm, ss(f, 1236, 1250))     # taken from outside
bake_obj(WAXM, 1182, 1252, mold_up)
key_hide(WAXM, [(1, True), (330, False), (414, True), (1182, False), (1252, True)])
key_hide(WAX, [(1, False), (1182, True)])
key_hide(OB["WaxTin"], [(1, False), (1182, True)])
P.hand_fn["R"].append((1182, 1214, lambda f: grip_hand(mold_up(f) @ V(0, 0.075, 0), V(0, 0.3, 1), V(0, 1, 0))))
P.k(1182, root=STA + V(0, 0.06, -0.06), flex=18, sp_flex=26, h_pitch=30, cR=45)
P.k(1192, root=V(0.88, 1.1, 0.97), flex=26, sp_flex=18, h_pitch=-10)
P.k(1205, root=V(0.84, 1.2, 1.0), flex=42, sp_flex=16, h_pitch=-35, sp_side=-4, hL=grip_hand(V(0.7, 1.45, TABLE_Z + 0.02), V(0, 1, -0.2), V(0, 0, -1)))   # leans over the table to the sill
P.k(1214, root=V(0.84, 1.21, 1.0), flex=44, sp_flex=20, h_pitch=-40)
P.k(1228, root=STA + V(0, 0.03, 0), flex=6, sp_flex=6, h_pitch=-20, hR=HANG["R"], cR=15, hL=HANG["L"])
for i, s in enumerate("LR"):
    P.plant(s, 1186 + i * 6, 1198 + i * 6, P.h.foot_xy(s, V(0.86, 1.1, 0), 180), 180, 0.05)
# sits on the stool to wait (1235-1290), gets up (1290-1305)
STOOL = OB["painted_wooden_stool"]
SIT = V(0.3, 1.0, 0.70)
STOOL.location = (0, 0, 0); STOOL.rotation_euler = (0, 0, R_(5)); bpy.context.view_layer.update()
_bb = [STOOL.matrix_world @ Vector(c) for c in STOOL.bound_box]; _c = sum(_bb, Vector()) / 8
STOOL.location = (SIT.x - _c.x - 0.04, SIT.y - _c.y, 0)
SIT.z = max(c.z for c in _bb) + 0.11
P.k(1240, root=STA + V(-0.25, -0.05, -0.05), yaw=150, flex=10, sp_flex=14, h_pitch=15)
P.k(1258, root=SIT, yaw=110, flex=-2, sp_flex=38, h_pitch=35, h_yaw=10,
    hL=B((0.12, -0.36, -0.12), (-0.4, -0.3, -1), (-1, 0, 0)), hR=B((-0.12, -0.36, -0.12), (0.4, -0.3, -1), (1, 0, 0)), cL=35, cR=35)
P.k(1285, root=SIT + V(0, 0, 0.0), sp_flex=42, h_pitch=45, h_yaw=-8)
for s, o_ in (("L", 0.13), ("R", -0.13)):
    P.plant(s, 1232 + (s == "R") * 8, 1248 + (s == "R") * 8, P.h.foot_xy(s, V(0.42, 0.72, 0), 110) , 110)
P.k(1300, root=STA + V(0.2, 0.01, -0.02), yaw=180, flex=12, sp_flex=18, h_pitch=35, hL=LH_TABLE, cL=20, hR=HANG["R"])
STB = STA + V(0.24, 0.0, 0.0)   # in front of the cake
for i, s in enumerate("LR"):
    P.plant(s, 1286 + i * 8, 1300 + i * 8, P.h.foot_xy(s, STB, 180), 180)
# ---- beat 8: cut the cake, pull the key, it turns (1303-1428)
KNIFE = OB["Knife_Blade"]; KN0 = KNIFE.matrix_world.copy()
SLICE = OB["Cake2_Slice"]; CMAIN = OB["Cake2_Main"]
def cutm(a_deg, r, h):
    a = R_(a_deg); rad = V(math.cos(a), math.sin(a), 0); perp = V(-math.sin(a), math.cos(a), 0)
    return mat_from(CAKE2_P + rad * r + V(0, 0, h), V(0, 0, -1), perp)
def knife(f):
    A1, D1, E1 = cutm(160, 0.07, 0.30), cutm(160, 0.07, 0.16), cutm(160, 0.02, 0.16)
    A2, D2, E2 = cutm(200, 0.07, 0.30), cutm(200, 0.07, 0.16), cutm(200, 0.02, 0.16)
    if f <= 1306: return mlerp(KN0, A1, ss(f, 1294, 1306))
    if f <= 1313: return mlerp(A1, D1, ss(f, 1306, 1313))
    if f <= 1319: return mlerp(D1, E1, ss(f, 1313, 1319))
    if f <= 1324: return mlerp(E1, A2, ss(f, 1319, 1324))
    if f <= 1331: return mlerp(A2, D2, ss(f, 1324, 1331))
    if f <= 1336: return mlerp(D2, E2, ss(f, 1331, 1336))
    if f <= 1341: return mlerp(E2, A2, ss(f, 1336, 1341))
    return mlerp(A2, mat_from(V(1.38, 1.78, TABLE_Z + 0.008), V(1, 0.1, 0), V(0, 0, 1)), ss(f, 1341, 1350))
# knife blade origin is at the handle end: blade runs +x
bake_obj(KNIFE, 1294, 1350, knife)
P.hand_fn["R"].append((1294, 1350, lambda f: grip_hand(knife(f) @ V(-0.05, 0, 0), V(0, 1, -0.3), V(-1, 0, 0))))
def slice_m(f):
    out = Matrix.Translation(CAKE2_P + V(-0.09, 0.03, 0.0)) @ Matrix.Rotation(R_(-14), 4, 'Z')
    up = Matrix.Translation(CAKE2_P + V(-0.05, 0.015, 0.025)) @ Matrix.Rotation(R_(-6), 4, 'Z') @ Matrix.Rotation(R_(8), 4, 'Y')
    if f <= 1336: return Matrix.Translation(CAKE2_P)
    if f <= 1343: return mlerp(Matrix.Translation(CAKE2_P), up, ss(f, 1336, 1343))
    return mlerp(up, out, ss(f, 1343, 1352))
bake_obj(SLICE, 1336, 1352, slice_m)
P.hand_fn["L"].append((1334, 1352, lambda f: grip_hand(slice_m(f) @ V(-0.125, 0, 0.06), V(0.35, 0, -1), V(1, 0, 0))))
for i in range(26):
    c = OB["Crumb%02d" % i]; t0 = 1314 if i < 9 else (1332 if i < 17 else 1346)
    c.scale = (0, 0, 0); c.keyframe_insert("scale", frame=1)
    c.keyframe_insert("scale", frame=t0); c.scale = (1, 1, 1); c.keyframe_insert("scale", frame=t0 + 3)
    c.location = CAKE2_P + V(-0.06, 0, 0.06); c.keyframe_insert("location", frame=t0)
    c.location = Vector(c["rest"]); c.keyframe_insert("location", frame=t0 + 6)
for o_ in [SLICE, CMAIN] + [OB["Crumb%02d" % i] for i in range(26)]:
    key_hide(o_, [(1, True), (1250, False)])
K2_IN = mat_from(CAKE2_P + V(-0.012, 0, 0.047), V(0, 0.05, -1), V(0, 1, 0))
K2_UP = mat_from(V(1.18, 1.2, 1.15), V(0.5, 0.3, 0.8), V(0, -1, 0.3))
def k2_path(f):
    if f <= 1352: return K2_IN
    if f <= 1372: return mlerp(K2_IN, K2_UP, ss(f, 1352, 1372))
    if f <= 1400: return mlerp(K2_UP, lock_key(0.06, 0), ss(f, 1370, 1400))
    if f <= 1412: return mlerp(lock_key(0.06, 0), lock_key(0.0, 0), ss(f, 1400, 1412))
    if f <= 1426: return lock_key(0.0, 90 * ss(f, 1414, 1424))
    return lock_key(0.0, 90)
bake_obj(K2, 1300, 1440, k2_path)
key_hide(K2, [(1, True), (1250, False), (1434, True)])
P.hand_fn["R"].append((1351, 1372, lambda f: grip_hand(bow(k2_path(f)), k2_path(f).to_3x3() @ V(1, 0, 0), k2_path(f).to_3x3() @ V(0, 0, -1))))
P.hand_fn["R"].append((1373, 1432, lambda f: hand_lock(k2_path(f)) if f > 1398 else grip_hand(bow(k2_path(f)), k2_path(f).to_3x3() @ V(1, 0, 0), k2_path(f).to_3x3() @ V(0, 0, -1))))
P.k(1312, root=STB + V(0, 0.05, -0.04), flex=16, sp_flex=26, h_pitch=45, cR=60, hL=grip_hand(CAKE2_P + V(-0.09, -0.08, 0.06), V(0.7, 0.6, -0.5), V(0.7, 0.7, 0)), cL=30)
P.k(1330, root=STB + V(0, 0.07, -0.07), flex=20, sp_flex=32)
P.k(1356, hL=HANG["L"], h_pitch=48)
P.k(1354, root=STB + V(0, 0.08, -0.08), flex=22, sp_flex=32)
P.k(1360, root=STB + V(0, 0.02, 0), flex=8, sp_flex=12, h_pitch=20, hL=HANG["L"], cR=55)
# steps to the door (1370-1400)
for i, s in enumerate("RL"):
    P.plant(s, 1368 + i * 12, 1386 + i * 12, P.h.foot_xy(s, DOOR_ST, 90), 90, 0.08)
P.k(1372, root=STB + V(0.1, -0.05, 0), yaw=160)
P.k(1398, root=DOOR_ST, yaw=90, flex=6, sp_flex=12, h_pitch=22, h_yaw=-26, hL=LH_DOOR, cL=10)
P.k(1418, sp_twist=-8, side=3, h_pitch=26)
P.k(1428, sp_twist=2, side=0, h_pitch=12, h_yaw=-10)
# door: bolt slides, door swings out (pushed with the left hand)
DP = OB["CellDoor_Pivot"]; BOLT = OB["CellLock_Bolt"]
DANG = pchip([(1, 90.0), (1432, 90.0), (1470, -5.0), (1890, -8.0)])
for f in list(range(1, 1433, 400)) + list(range(1432, 1891, 2)):
    DP.rotation_euler = (0, 0, R_(DANG(f))); DP.keyframe_insert("rotation_euler", frame=f)
for f, dy in ((1, 0.0), (1418, 0.0), (1428, -0.15)):
    BOLT.location = (0, dy, 0); BOLT.keyframe_insert("location", frame=f)
P.k(1436, flex=10, cR=15)
P.k(1450, hR=HANG["R"])
P.k(1452, flex=8, hL=HANG["L"], cL=15)
def door_M(f): return Matrix.Translation(DP.location) @ Matrix.Rotation(R_(DANG(f)), 4, 'Z')
P.hand_fn["R"].append((1433, 1446, lambda f: grip_hand(door_M(f) @ V(0.86, 0.06, 1.48), door_M(f).to_3x3() @ V(0, 0, 1), door_M(f).to_3x3() @ V(0, -1, 0))))
# ---- beat 9: walks out through the corridor gates and the yard (1456-1890)
WALK9 = [(1.5, 0.9), (1.75, 0.55), (2.25, 0.3), (3.0, 0.12), (5.0, 0.1), (7.2, 0.1), (7.45, 0.6), (7.6, 1.8), (8.6, 3.8), (9.7, 5.5), (10.6, 6.0), (12.6, 6.05)]
pth9, yfn9 = P.walk(1456, 1890, WALK9, stride=0.9, lean=7)
arm_swing(P, 1462, 1890, pth9, amp=0.13)
P.k(1890, root=V(12.6, 6.05, 0.99), yaw=90)
P.k(1500, h_pitch=4, h_yaw=0, sp_twist=0, side=0, flex=5)
P.k(1600, h_yaw=18); P.k(1640, h_yaw=-10); P.k(1700, h_pitch=-6, h_yaw=12); P.k(1780, h_pitch=-2, h_yaw=-5)
sc["WALK9_T"] = [[f, *pth9(f)[:2]] for f in range(1456, 1891, 10)]
P.bake()

# ================================================================== VISITOR (beat 3: pocket + walk to the gate)
Vi = Actor("Visitor")
VST = V(0.9, 3.05, 0.99)
Vi.stand(1, VST, 120)
def mold_v(f):
    hand = Matrix.Translation(VST + Matrix.Rotation(R_(120), 3, 'Z') @ V(-0.05, -0.32, 0.12)) @ Matrix.Rotation(R_(80), 4, 'X') @ Matrix.Rotation(R_(30), 4, 'Z')
    pocket = Matrix.Translation(VST + Matrix.Rotation(R_(120), 3, 'Z') @ V(-0.19, -0.13, -0.12)) @ Matrix.Rotation(R_(95), 4, 'X') @ Matrix.Rotation(R_(120), 4, 'Z')
    if f <= 372: return hand
    return mlerp(hand, pocket, ss(f, 372, 402))
bake_obj(WAXM, 330, 412, mold_v)
Vi.hand_fn["R"].append((330, 410, lambda f: grip_hand(mold_v(f) @ V(0, 0.07, 0), mold_v(f).to_3x3() @ V(0, -1, 0) , mold_v(f).to_3x3() @ V(0, 0, 1) * -1)))
Vi.k(1, root=VST, yaw=120, sp_flex=6, h_pitch=20, h_yaw=10, hL=HANG["L"], hR=HANG["R"], cR=40)
Vi.k(340, h_pitch=30, h_yaw=-25, sp_twist=-6)         # glances back at the window
Vi.k(372, h_pitch=10, h_yaw=30, sp_twist=5)           # looks to the guard
Vi.k(410, h_yaw=0, sp_twist=0, cR=15, hR=HANG["R"])
pv, yv = Vi.walk(420, 860, [(0.9, 3.05), (3.5, 4.0), (6.5, 5.0), (9.4, 5.95), (11.6, 6.0), (13.2, 5.6), (13.9, 4.4)], stride=0.82)
arm_swing(Vi, 424, 860, pv)
end_walk(Vi, 860, pv, yv)
Vi.k(860, root=V(13.9, 4.4, 0.99), yaw=yv(860), hL=HANG["L"], hR=HANG["R"])
Vi.k(900, yaw=60, h_yaw=10)
Vi.k(500, h_yaw=-20); Vi.k(560, h_yaw=15); Vi.k(640, h_yaw=0)
Vi.bake()

# ================================================================== GUARD (yard gate, receives the box, asleep in the corridor)
G = Actor("Guard")
GST = V(9.45, 4.45, 0.99)
G.stand(1, GST, 150)
G.k(1, root=GST, yaw=150, sp_flex=2, h_pitch=5, hL=HANG["L"], hR=HANG["R"], cR=20)
YGR, YGL = OB["YardGate_Pivot_R"], OB["YardGate_Pivot_L"]
for f, a in ((1, 90), (440, 90), (500, 5), (900, 5), (960, 90), (1760, 90), (1800, 3)):
    YGR.rotation_euler = (0, 0, R_(a)); YGR.keyframe_insert("rotation_euler", frame=f)
    YGL.rotation_euler = (0, 0, R_(180 - a)); YGL.keyframe_insert("rotation_euler", frame=f)
def gate_bar(f):
    return YGR.matrix_world @ V(0.85, 0, 1.15)
G.k(400, hR=HANG["R"])
G.k(430, yaw=150, h_yaw=-20, hR=B((-0.22, -0.34, 0.22), (-0.2, -1, 0.1), (0, 0, -1)), cR=5, sp_twist=-8)   # waves him through
G.k(440, root=GST + V(0.1, 0.08, 0), yaw=140)
G.k(500, root=GST + V(0.22, 0.12, -0.02), yaw=120, flex=6, sp_twist=-10, h_yaw=-30)
G.k(470, hR=B((-0.26, -0.3, 0.16), (-0.6, -1, 0.1), (0, 0, -1)))
G.k(530, hR=HANG["R"], cR=15, sp_twist=0, h_yaw=-15)
for i, s in enumerate("RL"):
    G.plant(s, 440 + i * 14, 458 + i * 14, G.h.foot_xy(s, GST + V(0.1, 0.08, 0), 140), 140)
    G.plant(s, 476 + i * 14, 494 + i * 14, G.h.foot_xy(s, GST + V(0.22, 0.12, 0), 120), 120)
pg, yg = G.walk(600, 800, [(9.67, 4.57), (9.65, 5.5), (10.6, 6.0), (12.4, 6.0), (13.9, 6.15)], stride=0.75)
arm_swing(G, 604, 800, pg)
end_walk(G, 800, pg, yg)
G.k(600, root=V(9.67, 4.57, 0.99), yaw=yg(600))
G.k(800, root=V(13.9, 6.15, 0.99), yaw=yg(800), hL=HANG["L"], hR=HANG["R"])
G.k(820, yaw=90, h_yaw=5, h_pitch=12)
for i, s in enumerate("LR"):
    G.plant(s, 802 + i * 10, 816 + i * 10, G.h.foot_xy(s, V(13.9, 6.15, 0), 90), 90)
# sleeping on the corridor stool (from 1300, unseen move)
GS = V(6.12, -0.62, 0.70)
G.k(1290, root=V(13.9, 6.15, 0.99), yaw=90, hL=HANG["L"], hR=HANG["R"])
G.k(1300, root=GS, yaw=180, flex=-12, sp_flex=-4, h_pitch=40, h_yaw=15, side=4,
    hL=B((0.05, -0.28, 0.02), (-1, -0.2, 0), (0, 1, 0)), hR=B((-0.05, -0.26, 0.04), (1, -0.2, 0), (0, 1, 0)), cL=30, cR=30)
for i, s in enumerate("LR"):
    G.plant(s, 1294, 1300, G.h.foot_xy(s, V(6.12, -0.2, 0), 180), 180, 0.0)
G.k(1560, h_pitch=34, h_yaw=-5)     # stirs as the gate clangs
G.k(1600, h_pitch=42, h_yaw=10)
G.breath = 2.5
exec(open(os.path.join(HERE, "03b_life.py")).read())
G.hand_fn["L"].append((842, 1000, lambda f: grip_hand(box_m(f) @ V(0.19, 0, 0.06), box_m(f).to_3x3() @ V(-0.2, -1, -0.3), box_m(f).to_3x3() @ V(-1, 0, 0))))
G.hand_fn["R"].append((842, 1000, lambda f: grip_hand(box_m(f) @ V(-0.19, 0, 0.06), box_m(f).to_3x3() @ V(0.2, -1, -0.3), box_m(f).to_3x3() @ V(1, 0, 0))))
pg2, yg2 = G.walk(858, 1000, [(13.9, 6.15), (12.6, 6.0), (11.0, 6.0), (9.4, 5.6)], stride=0.75)
end_walk(G, 1000, pg2, yg2)
G.k(852, yaw=90, root=V(13.9, 6.15, 0.99), cL=50, cR=50)
G.k(1000, root=V(9.4, 5.6, 0.99), yaw=yg2(1000))
G.k(1010, hL=HANG["L"], hR=HANG["R"], cL=15, cR=15)
G.compile()

# ================================================================== ALLY (foundry: pour, open mould, key into cake, box, hand-off)
A = Actor("CrowdB")
AST = V(14.3, 6.4, 0.99)
A.stand(1, AST, 180)
CRU = OB["Crucible"]; CAKE1_P = OB["Cake1"].location.copy()
def cru(f):
    up = Matrix.Translation(V(14.65, 7.08, 1.22))
    tilt = Matrix.Translation(V(14.65, 7.08, 1.14)) @ Matrix.Rotation(R_(75), 4, 'X')
    rest = Matrix.Translation(V(14.62, 7.25, BENCH_Z + 0.08))
    if f <= 515: return mlerp(up, tilt, ss(f, 480, 515))
    if f <= 598: return tilt @ Matrix.Rotation(R_(3 * math.sin(f / 5.0)), 4, 'X')
    if f <= 625: return mlerp(tilt, up, ss(f, 598, 625))
    return mlerp(up, rest, ss(f, 625, 650))
bake_obj(CRU, 470, 650, cru)
CRU.matrix_world = cru(470); CRU.keyframe_insert("location", frame=1); CRU.keyframe_insert("rotation_euler", frame=1)
def shank_grip(f, x):
    M = cru(f); return grip_hand(M @ V(x, 0, 0) + V(0, 0, 0.0), V(0.2, 1, -0.2), V(0, 0, -1))
A.hand_fn["L"].append((470, 650, lambda f: shank_grip(f, -0.68)))
A.hand_fn["R"].append((470, 650, lambda f: shank_grip(f, -0.5)))
A.k(1, root=AST, yaw=180, flex=8, sp_flex=16, h_pitch=35, cL=60, cR=60, hL=HANG["L"], hR=HANG["R"])
A.k(500, root=AST + V(0, 0.03, -0.03), flex=12, sp_flex=22, h_pitch=40, side=-3)
A.k(598, root=AST + V(0, 0.04, -0.04), flex=14, sp_flex=24)
A.k(640, root=AST + V(0.05, 0.08, -0.05), flex=18, sp_flex=26)
A.k(650, root=AST + V(-0.0, 0.05, -0.04), flex=14)
# pour stream: bezier from the crucible lip to the sprue, keyed by hide + bevel
pour = OB["PourStream"]; sp = pour.data.splines[0]
SPRUE = MOULD_P + V(0, 0, 0.123)
def set_pour(f):
    lip = cru(f) @ V(0, -0.088, 0.08)
    sp.bezier_points[0].co = lip; sp.bezier_points[0].handle_left = lip + V(0, 0.02, 0.02); sp.bezier_points[0].handle_right = lip + V(0, -0.03, -0.02)
    sp.bezier_points[1].co = SPRUE; sp.bezier_points[1].handle_left = SPRUE + V(0, 0, 0.05); sp.bezier_points[1].handle_right = SPRUE + V(0, 0, -0.02)
for f in range(505, 612, 2):
    set_pour(f)
    for bp in sp.bezier_points:
        bp.keyframe_insert("co", frame=f); bp.keyframe_insert("handle_left", frame=f); bp.keyframe_insert("handle_right", frame=f)
for f, d in ((1, 0.0), (512, 0.0), (520, 0.009), (590, 0.008), (608, 0.0)):
    pour.data.bevel_depth = d; pour.data.keyframe_insert("bevel_depth", frame=f)
key_hide(pour, [(1, True), (512, False), (610, True)])
glow = OB["L_PourGlow"]
for f, e in ((1, 0), (505, 0), (520, 30), (600, 30), (640, 12), (700, 18), (760, 3), (800, 0)):
    glow.data.energy = e; glow.data.keyframe_insert("energy", frame=f)
# sparks: ballistic from the sprue, re-launched in waves
SPK = [OB[f"Spark{i}"] for i in range(40)]
for i, s in enumerate(SPK):
    t0 = 515 + (i * 7) % 85; life = random.randint(14, 26)
    v = V(random.uniform(-1.2, 1.2), random.uniform(-1.4, 0.6), random.uniform(0.8, 2.2))
    s.location = (0, 0, -50); s.keyframe_insert("location", frame=t0 - 1)
    for j in range(0, life + 1, 2):
        t = j / 60.0; p = SPRUE + v * t + V(0, 0, -4.9 * t * t)
        s.location = p; s.keyframe_insert("location", frame=t0 + j)
        s.rotation_euler = (0, math.atan2(v.x, v.z), 0); s.keyframe_insert("rotation_euler", frame=t0 + j)
    s.location = (0, 0, -50); s.keyframe_insert("location", frame=t0 + life + 1)
    for fc in fcurves(s.animation_data.action):
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
smk = bpy.data.materials["M_Smoke"].node_tree
for f, d in ((1, 0.0), (520, 0.0), (560, 0.6), (690, 0.8), (760, 0.25), (820, 0.0)):
    smk.nodes["SmokeAmt"].outputs[0].default_value = d; smk.nodes["SmokeAmt"].outputs[0].keyframe_insert("default_value", frame=f)
for f, z in ((1, 0.0), (900, 1.6)):
    smk.nodes["SmokeMap"].inputs['Location'].default_value = (0, 0, -z); smk.nodes["SmokeMap"].inputs['Location'].keyframe_insert("default_value", frame=f)
key_hide(OB["Smoke"], [(1, True), (515, False), (830, True)])
# mould top lifted off (660-692)
MT = OB["Mould_Top"]; MT0 = MT.matrix_world.copy()
def mtop(f):
    off = Matrix.Translation(V(-0.42, 0.12, 0)) @ MT0
    mid = Matrix.Translation(V(-0.2, 0.06, 0.18)) @ MT0 @ Matrix.Rotation(R_(-30), 4, 'Y')
    if f <= 676: return mlerp(MT0, mid, ss(f, 660, 676))
    return mlerp(mid, Matrix.Translation(V(0, 0, -0.062)) @ off, ss(f, 676, 692))
bake_obj(MT, 655, 694, mtop)
A.hand_fn["L"].append((656, 692, lambda f: grip_hand(mtop(f) @ V(-0.17, 0, 0.03), V(0.3, 0.8, -0.5), V(1, 0, 0))))
A.hand_fn["R"].append((656, 692, lambda f: grip_hand(mtop(f) @ V(0.17, 0, 0.03), V(-0.3, 0.8, -0.5), V(-1, 0, 0))))
A.k(655, root=AST + V(0.12, 0.05, -0.05), flex=16, sp_flex=26, h_pitch=45, cL=45, cR=45)
A.k(692, root=AST + V(0.05, 0.02, -0.03), flex=12, sp_flex=20)
# casting cools: emission keyed down, swapped for the real copy (Key_Copy1)
CAST = OB["Key_Casting"]; mm = bpy.data.materials.new("M_CastCool"); mm.use_nodes = True
bsd = mm.node_tree.nodes["Principled BSDF"]; bsd.inputs['Base Color'].default_value = (0.12, 0.11, 0.1, 1); bsd.inputs['Metallic'].default_value = 0.8
bsd.inputs['Roughness'].default_value = 0.5; bsd.inputs['Emission Color'].default_value = (1.0, 0.35, 0.05, 1)
for f, e in ((1, 25.0), (692, 25.0), (712, 6.0), (726, 0.3), (730, 0.0)):
    bsd.inputs['Emission Strength'].default_value = e; bsd.inputs['Emission Strength'].keyframe_insert("default_value", frame=f)
CAST.data.materials[0] = mm
key_hide(CAST, [(1, True), (560, False), (731, True)])
# A steps right to the cake (700-725)
AST2 = V(15.05, 6.4, 0.99)
for i, s in enumerate("RL"):
    A.plant(s, 698 + i * 10, 714 + i * 10, A.h.foot_xy(s, AST2 - V(0.25, 0, 0), 180), 180)
K_CAST = CAST.matrix_world.copy()
def k1_cake(f):
    above = mat_from(CAKE1_P + V(0.0, 0.0, 0.2), V(0, 0.1, -1), V(1, 0, 0))
    inside = mat_from(CAKE1_P + V(0.0, 0.0, 0.04), V(0, 0.1, -1), V(1, 0, 0))
    if f <= 730: return K_CAST
    if f <= 750: return mlerp(K_CAST, above, ss(f, 730, 750))
    return mlerp(above, inside, ss(f, 750, 772))
bake_obj(K1, 728, 772, k1_cake)
key_hide(K1, [(1, True), (730, False), (775, True), (845, False), (1044, True)])
A.hand_fn["R"].append((728, 772, lambda f: grip_hand(k1_cake(f) @ V(-0.05, 0, 0), k1_cake(f).to_3x3() @ V(1, 0, 0), k1_cake(f).to_3x3() @ V(0, 1, 0))))
A.k(726, root=AST2 - V(0.25, -0.06, 0.05), flex=18, sp_flex=28, h_pitch=40, hL=grip_hand(CAKE1_P + V(-0.138, 0, 0.065), V(1, 0.3, -0.4), V(1, 0, 0)), cL=30, cR=55)
A.k(772, root=AST2 - V(0.2, -0.03, 0.05), flex=16, sp_flex=26)
# cake into the box (776-798), lid (800-812), lift (814-828), turn to the guard and hand over (828-852)
CK = OB["Cake1"]; CK0 = CK.matrix_world.copy(); PB = OB["ParcelBox"]; PB0 = PB.matrix_world.copy(); LID = OB["ParcelBox_Lid"]; LID0 = LID.matrix_world.copy()
def cake_m(f):
    inbox = Matrix.Translation(PBOX_P + V(0, 0, 0.014))
    mid = Matrix.Translation((CK0.translation + PBOX_P) / 2 + V(0, 0, 0.18))
    if f <= 787: return mlerp(CK0, mid, ss(f, 776, 787))
    if f <= 798: return mlerp(mid, inbox, ss(f, 787, 798))
    return box_m(f) @ PB0.inverted() @ inbox
HANDOFF = V(14.28, 6.15, 1.08)
def box_m(f):
    lift = Matrix.Translation(V(0, 0, 0.22)) @ PB0
    hand = Matrix.Translation(HANDOFF) @ Matrix.Rotation(R_(90), 4, 'Z')
    if f <= 814: return PB0
    if f <= 828: return mlerp(PB0, lift, ss(f, 814, 828))
    if f <= 850: return mlerp(lift, hand, ss(f, 828, 850))
    gp, gy = G.root_at(f)
    return Matrix.Translation(gp + Matrix.Rotation(R_(gy), 3, 'Z') @ V(0, -0.38, 0.12)) @ Matrix.Rotation(R_(gy), 4, 'Z')
def lid_m(f):
    on = PB0 @ Matrix.Translation(V(0, 0, 0.13))
    up = Matrix.Translation(LID0.translation + V(0, -0.15, 0.15)) @ Matrix.Rotation(R_(60), 4, 'X')
    if f <= 806: return mlerp(LID0, up, ss(f, 798, 806))
    if f <= 813: return mlerp(up, on, ss(f, 806, 813))
    return box_m(f) @ PB0.inverted() @ on
bake_obj(CK, 774, 1000, cake_m)
bake_obj(PB, 812, 1000, box_m)
bake_obj(LID, 796, 1000, lid_m)
for o_ in (CK, PB, LID, OB["ParcelBox_Inside"], OB["ParcelBox_Twine"]):
    key_hide(o_, [(1, False), (1000, True)])
A.hand_fn["L"].append((776, 798, lambda f: grip_hand(cake_m(f) @ V(-0.12, 0, 0.05), V(0.3, 1, -0.4), V(1, 0, 0))))
A.hand_fn["R"].append((776, 798, lambda f: grip_hand(cake_m(f) @ V(0.12, 0, 0.05), V(-0.3, 1, -0.4), V(-1, 0, 0))))
A.hand_fn["R"].append((798, 813, lambda f: grip_hand(lid_m(f) @ V(0.0, 0.0, 0.03), V(0, 1, -0.3), V(0, 0, -1))))
A.hand_fn["L"].append((814, 852, lambda f: grip_hand(box_m(f) @ V(-0.19, 0, 0.06), box_m(f).to_3x3() @ V(0.2, 1, -0.3), box_m(f).to_3x3() @ V(1, 0, 0))))
A.hand_fn["R"].append((814, 852, lambda f: grip_hand(box_m(f) @ V(0.19, 0, 0.06), box_m(f).to_3x3() @ V(-0.2, 1, -0.3), box_m(f).to_3x3() @ V(-1, 0, 0))))
AST3 = V(15.42, 6.42, 0.99)
for i, s in enumerate("RL"):
    A.plant(s, 780 + i * 8, 794 + i * 8, A.h.foot_xy(s, AST3, 180), 180, 0.05)
A.k(790, root=(AST2 + AST3) / 2 - V(0, 0, 0.03), flex=12, sp_flex=20)
A.k(798, root=AST3 - V(0.0, 0.0, 0.04), flex=14, sp_flex=24, hL=HANG["L"], cL=20)
A.k(812, cL=50, cR=50)
A.k(828, root=AST3 - V(0.15, 0.05, 0.0), yaw=200, flex=6, sp_flex=10, h_pitch=20)
A.k(852, root=V(14.85, 6.3, 0.99), yaw=260, flex=8, sp_flex=10, h_pitch=10, h_yaw=0)
A.k(870, hL=HANG["L"], hR=HANG["R"], cL=15, cR=15, flex=2, sp_flex=4, h_pitch=0, h_yaw=-15)
for i, s in enumerate("LR"):
    A.plant(s, 826 + i * 10, 842 + i * 10, A.h.foot_xy(s, V(14.85, 6.3, 0), 260), 260)
A.bake()
G.bake()

# ================================================================== PRESIDENT + CROWD (FK, object-placed)
def fk_wave(rig_obj, f0, f1, ph, kind):
    R = Rig(rig_obj)
    for pb in rig_obj.pose.bones: pb.rotation_mode = 'QUATERNION'
    for f in range(f0, f1 + 1, 4):
        t = (f + ph) / 60.0
        if kind == "wave":   # right arm up, waving from the elbow
            R.key_rot("upperarm01.R", f, [("Y", 95), ("X", -15)])
            R.key_rot("lowerarm01.R", f, [("Y", 25 + 18 * math.sin(2 * math.pi * 1.6 * t))])
            R.key_rot("upperarm01.L", f, [("Y", 44), ("X", 4)]); R.key_rot("lowerarm01.L", f, [("Y", 8), ("X", -10)])
            R.key_rot("spine03", f, [("Z", 4 * math.sin(2 * math.pi * 0.2 * t)), ("X", -3)])
            R.key_rot("head", f, [("Z", 14 * math.sin(2 * math.pi * 0.15 * t)), ("X", -4)])
        else:                # cheering: both arms pump, bob
            a = 0.5 + 0.5 * math.sin(2 * math.pi * (1.1 + 0.3 * ((ph % 7) / 7)) * t)
            up = 120 if kind == "both" else 0
            R.key_rot("upperarm01.R", f, [("Y", 70 + 55 * a)])
            R.key_rot("lowerarm01.R", f, [("Y", 30 * (1 - a))])
            R.key_rot("upperarm01.L", f, [("Y", -(60 + 50 * (1 - a)) if kind == "both" else -10)])
            R.key_rot("lowerarm01.L", f, [("Y", -25 * a if kind == "both" else 0)])
            R.key_rot("spine02", f, [("X", -4 - 3 * a), ("Z", 5 * math.sin(t + ph))])
            R.key_rot("head", f, [("X", -12 - 6 * a), ("Z", 8 * math.sin(0.7 * t + ph))])
PR = OB["President"]; PR.location = (0.0, GY + 2.55, TOPZ); PR.rotation_euler = (0, 0, 0)
fk_wave(PR, 1600, 1890, 0, "wave")
crowd_src = [OB["CrowdA"], OB["CrowdC"]]
CROWD = []
random.seed(9)
spots = [(-3.6, 18.7), (-2.3, 19.0), (-1.0, 18.6), (0.5, 19.0), (1.8, 18.7), (3.1, 19.1), (4.4, 18.8),
         (-4.2, 19.7), (-2.9, 19.8), (-1.6, 19.6), (1.3, 19.7), (2.6, 19.6), (3.9, 19.8), (-0.4, 19.9), (5.4, 19.5), (-5.3, 19.4)]
for i, (x, y) in enumerate(spots):
    src = crowd_src[i % 2]
    if i < 2:
        a = src
    else:
        a = src.copy(); a.data = src.data; a.animation_data_clear(); sc.collection.objects.link(a); a.name = f"Crowd{i:02d}"
        for ch in src.children:
            c2 = ch.copy(); c2.parent = a; sc.collection.objects.link(c2)
            for m in c2.modifiers:
                if m.type == 'ARMATURE': m.object = a
    a.location = (x + random.uniform(-0.15, 0.15), y + random.uniform(-0.1, 0.1), 0); a.rotation_euler = (0, 0, R_(180 + random.uniform(-25, 25)))
    a.scale = (1, 1, random.uniform(0.94, 1.06))
    fk_wave(a, 1600, 1890, i * 13, "both" if i % 3 else "one")
    CROWD.append(a)
# everyone not needed is moved away before/after their scenes
for o_, rngs in ((PR, [(1, True), (1730, False)]), ):
    key_hide(o_, rngs)
for a in CROWD: key_hide(a, [(1, True), (1730, False)])
for o_ in bpy.data.collections["Gov"].objects:
    if o_.parent is None: key_hide(o_, [(1, True), (1730, False)])
key_hide(OB["Visitor"], [(1, False), (900, True)])
key_hide(OB["Guard"], [(1, False), (1012, True), (1299, False)])
key_hide(OB["CrowdB"], [(1, True), (420, False), (900, True)])

# ================================================================== candle burn-down, flicker; lights + world time of day
CND = OB["Candle"]; FL = OB["Candle_Flame"]; WK = OB["Candle_Wick"]; LC = OB["L_Candle"]
for f, s in ((1, 1.0), (1150, 0.92), (1300, 0.3), (1890, 0.28)):
    CND.scale = (1, 1, s); CND.keyframe_insert("scale", frame=f)
    top = CANDLE_P.z + 0.012 + 0.2 * s
    FL.location.z = top + 0.018; FL.keyframe_insert("location", frame=f)
    WK.location.z = top + 0.007; WK.keyframe_insert("location", frame=f)
    LC.location.z = top + 0.04; LC.keyframe_insert("location", frame=f)
for f in range(1, 1891, 3):
    n = 0.75 + 0.25 * math.sin(f * 0.9) * math.sin(f * 0.37 + 1.0) + random.uniform(-0.08, 0.08)
    LC.data.energy = 14.0 * n; LC.data.keyframe_insert("energy", frame=f)
    FL.scale = (1.0, 1.0, 0.85 + 0.25 * n); FL.rotation_euler = (random.uniform(-0.08, 0.08), random.uniform(-0.08, 0.08), 0)
    FL.keyframe_insert("scale", frame=f); FL.keyframe_insert("rotation_euler", frame=f)
wax_sk = WAX.data.shape_keys.key_blocks["Imprint"]
for f, v in ((1, 0.0), (150, 0.0), (230, 1.0), (1000, 1.0), (1001, 0.0), (1122, 0.0), (1150, 1.0)):
    wax_sk.value = v; wax_sk.keyframe_insert("value", frame=f)
bs_w = bpy.data.materials["M_Wax"].node_tree.nodes["Principled BSDF"]
for f, r in ((1, 0.08), (250, 0.1), (330, 0.45), (1000, 0.45), (1001, 0.08), (1180, 0.4)):
    bs_w.inputs['Roughness'].default_value = r; bs_w.inputs['Roughness'].keyframe_insert("default_value", frame=f)
# world: day (1-850) -> night (870-1690) -> day (1730-)
mix = sc.world.node_tree.nodes["DayNight"]; bg = sc.world.node_tree.nodes["Background"]
SUN = OB["L_Sun"].data; MOON = OB["L_Moon"].data; WL = OB["L_Window"].data
for f, n in ((1, 0.0), (845, 0.0), (868, 1.0), (1728, 1.0), (1760, 0.0)):
    mix.inputs['Factor'].default_value = n; mix.inputs['Factor'].keyframe_insert("default_value", frame=f)
    bg.inputs['Strength'].default_value = lerp(1.0, 0.5, n); bg.inputs['Strength'].keyframe_insert("default_value", frame=f)
    SUN.energy = lerp(2.5 if f < 1000 else 3.4, 0.0, n); SUN.keyframe_insert("energy", frame=f)
    MOON.energy = lerp(0.0, 1.0, n); MOON.keyframe_insert("energy", frame=f)
    WL.energy = lerp(70, 35, n); WL.color = (lerp(0.8, 0.55, n), lerp(0.85, 0.68, n), 1.0)
    WL.keyframe_insert("energy", frame=f); WL.keyframe_insert("color", frame=f)
for f, e in ((1, 0.3), (845, 0.3), (868, 0.9), (1728, 0.9), (1760, 0.0)):
    sc.view_settings.exposure = e; sc.view_settings.keyframe_insert("exposure", frame=f)
# moonlight patch across the cell floor (time passing in beat 7): the window light swings
WO = OB["L_Window"]
for f, rz in ((1, 0.0), (1150, 0.0), (1300, 25.0), (1890, 25.0)):
    WO.rotation_euler = (R_(-80 + 0.12 * rz), 0, R_(rz)); WO.keyframe_insert("rotation_euler", frame=f)
for nm in ("L_YardLamp0", "L_YardLamp1", "L_YardLamp2", "L_CorrLantern0", "L_CorrLantern1"):
    L = OB[nm].data
    for f, e in ((1, L.energy * 0.3), (845, L.energy * 0.3), (868, L.energy)):
        L.energy = e; L.keyframe_insert("energy", frame=f)
    L.energy = 0
# corridor gates open in sequence (beat 9)
for i, (fa, fb) in enumerate(((1478, 1506), (1496, 1522), (1520, 1548))):
    for side, sg in (("N", 1), ("S", -1)):
        g = OB[f"CorrGate{i}{side}_Pivot"]
        for f, a in ((1, -90), (fa + (side == "S") * 3, -90), (fb - 6, -6), (fb, -10), (fb + 8, -8)):
            g.rotation_euler = (0, 0, R_(sg * a)); g.keyframe_insert("rotation_euler", frame=f)
exec(open(os.path.join(HERE, "03c_details.py")).read())
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ANIM saved", OUT)
