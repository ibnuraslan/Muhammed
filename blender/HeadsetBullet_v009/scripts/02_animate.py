"""HeadsetBullet v009 stage B: his acting, the ONE bullet, the impacts, the cross-section, the ONE camera (no cuts), VO.
blender -b a.blend --python 02_animate.py -- <vo.mp3> <out.blend>
Built to the client's VO (HeadsetBullet v008 recording, frames 1-1203). Beats (whisper word times, frame = 1 + s*60):
1 'A bullet', 31 'smashed through the window', 126 'flying straight at his head', 228 'But he was gaming', 392 'And instead of
going through his skull', 516 'the bullet hit the headset', 624 'The thick padding', 715 'knocked it off course', 791 'sent
it flying away', 902 'Shocked,', 937 'he pulled off the broken headset', 1019 'and realized it had just saved his life'.
Scene changes happen inside the move: the bullet dents the ear cup -> a short warm flash around the bullet -> the same
bullet, same camera-relative pose, in the ear-cup cross-section (600). Back out: flash -> the bullet leaving the cup (752)."""
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
random.seed(20)
END = 1203
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); LOG.append(s); print("LOG", s)
O = bpy.data.objects
BR, BB, CL = O["Boy"], O["Boy.body"], O["Boy.clothes"]
BUL, TIP, TRAIL, WCTL = O["Bullet"], O["TipCtl"], O["BulletTrail"], O["WoundCtl"]
CRACK, CK, SHL, HS = O["HM_GlassCrack"], O["HS_CupCrack"], O["HS_ShellL"], O["HS_Root"]
PIVL, PIVR = O["HS_CupPivotL"], O["HS_CupPivotR"]
WH, MCK = O["HM_WallHole"], O["MC_ShellCrack"]
MX = Vector((20.0, 0.0, 0.0))
F_BUL, F_GLASS, F_HIT, SWAP1, SWAP2, F_WALL = 1, 45, 525, 600, 738, 835
UP = Vector((0, 0, 1))

# ================================================================== rig + joint limits (knees, elbows, hips never bend backward)
CT = make_human_ctrl(BR)
add_hand_limits(BR)
for pb in BR.pose.bones: pb.rotation_mode = 'QUATERNION'
H = Human(CT)
def _joint_sign(bone, tip_bone, want):
    """+1 if rotating `bone` +30 deg about its local X moves `tip_bone`'s head along `want` (world dir)"""
    pb = BR.pose.bones[bone]; q0 = pb.rotation_quaternion.copy(); upd(); p0 = Wh(BR, tip_bone)
    pb.rotation_quaternion = Quaternion((1, 0, 0), math.radians(30)); upd(); p1 = Wh(BR, tip_bone)
    pb.rotation_quaternion = q0; upd()
    return 1 if (p1 - p0).dot(Vector(want)) > 0 else -1
for s in "LR":
    # elbow: flexion brings the hand forward (-Y) from the A-pose; rest is bent ~46 deg, so allow -40 (straight) .. 140
    sg = _joint_sign("lowerarm01." + s, "wrist." + s, (0, -1, 0.3))
    lo = BR.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True
    lo.ik_min_x, lo.ik_max_x = (math.radians(-40), math.radians(150)) if sg > 0 else (math.radians(-150), math.radians(40))
    lo.lock_ik_z = True
    # knee: flexion swings the foot backward (+Y); 0 .. 150, never hyper-extended
    sg = _joint_sign("lowerleg01." + s, "foot." + s, (0, 1, 0))
    kn = BR.pose.bones["lowerleg01." + s]; kn.use_ik_limit_x = True
    kn.ik_min_x, kn.ik_max_x = (0.0, math.radians(150)) if sg > 0 else (math.radians(-150), 0.0)
    # hip: flexion lifts the knee forward (-Y): -20 (extension) .. 125; abduction/adduction +-35; twist +-30
    sg = _joint_sign("upperleg01." + s, "lowerleg01." + s, (0, -1, 0))
    hp = BR.pose.bones["upperleg01." + s]; hp.use_ik_limit_x = hp.use_ik_limit_z = True
    hp.ik_min_x, hp.ik_max_x = (math.radians(-20), math.radians(125)) if sg > 0 else (math.radians(-125), math.radians(20))
    hp.ik_min_z, hp.ik_max_z = math.radians(-35), math.radians(35)
    log("limits", s, "elbow", [round(math.degrees(v)) for v in (lo.ik_min_x, lo.ik_max_x)], "knee", [round(math.degrees(v)) for v in (kn.ik_min_x, kn.ik_max_x)],
        "hip", [round(math.degrees(v)) for v in (hp.ik_min_x, hp.ik_max_x)])

def key_pole(s, f, target, kind="elbow"):
    n = ("Pole_elbow." if kind == "elbow" else "Pole_knee.") + s; pb = CT.PB[n]
    pb.location = CT.rest(n).to_3x3().inverted() @ (Vector(target) - CT.BN[n].head_local)
    pb.keyframe_insert("location", frame=f, group=n)
def key_spine(f, flex=0.0, twist=0.0, side=0.0):
    for n, w in Human.SPINE_W.items():
        CT.key_rot(n, f, [("X", flex * w), ("Y", side * w), ("Z", twist * w)])
_HS = {}
def head_signs():
    if _HS: return _HS["s"]
    pb = BR.pose.bones["head"]; q0 = pb.rotation_quaternion.copy(); upd()
    e0 = Wh(BR, "eye.L"); out = {}
    for ax, i in (("X", 0), ("Z", 2)):
        pb.rotation_quaternion = Quaternion(Vector([1 if k == i else 0 for k in range(3)]), math.radians(10)); upd()
        out[ax] = Wh(BR, "eye.L") - e0; pb.rotation_quaternion = q0; upd()
    _HS["s"] = (1 if out["X"].z < 0 else -1, 1 if out["Z"].x > 0 else -1)
    return _HS["s"]
def key_head(f, yaw, pitch, roll=0.0):
    """yaw +: toward his own left (+X); pitch +: look down"""
    sx, sz = head_signs()
    for n, w in (("neck01", 0.25), ("neck02", 0.25), ("neck03", 0.2), ("head", 0.3)):
        CT.key_rot(n, f, [("X", sx * pitch * w), ("Y", roll * w), ("Z", -sz * yaw * w)])   # sign checked on the moving preview

# ================================================================== seated pose (root over the seat, feet flat on the floor)
ROOT_Z = 0.60
def sit(f, flex=0.0, dz=0.0, dy=0.0):
    H.key_root(f, Vector((0.0, 0.02 + dy, ROOT_Z + dz)), yaw=0.0, flex=flex, side=0.0)
for f, fl, dz, dy in ((1, 0, 0, 0), (840, 0, 0, 0), (860, -3, 0.004, 0.01), (900, -2, 0.002, 0.006), (END, -1, 0, 0.004)):
    sit(f, fl, dz, dy)
def feet(f, fwd=0.0):
    for s, sg in (("L", 1), ("R", -1)):
        a = CT.BN["foot." + s].head_local
        tgt = Vector((sg * 0.15, -0.36 - fwd, a.z))
        M = Matrix.Translation(tgt) @ Matrix.Translation(-a) @ CT.rest("IK_foot." + s)
        CT.key_world("IK_foot." + s, f, M)
        key_pole(s, f, tgt + Vector((sg * 0.08, -0.9, 0.55)), kind="knee")
for f, fw in ((1, 0.0), (840, 0.0), (870, 0.03), (END, 0.03)):
    feet(f, fw)
# spine: leaning toward the screen while gaming; sits up straight in shock; breathing on top (every 20 frames)
def spine_flex(f):
    return pchip([(1, 9.0), (520, 10.0), (560, 8.0), (840, 9.0), (870, -2.0), (930, 2.0), (1010, 6.0), (1100, 5.0), (END, 6.0)])(f)
def breath(f):
    per = 200 if f < 840 else 110 if f < 1100 else 180
    return (0.8 if f < 840 else 1.5) * math.sin(2 * math.pi * f / per)
for f in list(range(1, END + 1, 20)) + [END]:
    key_spine(f, flex=spine_flex(f) + breath(f), twist=pchip([(1, 0), (500, 0), (530, -3), (600, -2), (840, 0), (END, 0)])(f))
# head: watches the screen (micro moves), jolts away at the hit, frozen, startled up at the wall hit, looks down at the headset,
# turns to the hole in the wall, back to the headset
HEAD = [(1, 2, 8), (60, -2, 9), (130, 1, 8), (200, -3, 9), (260, 2, 8), (330, -2, 10), (400, 1, 9), (470, 0, 9), (524, 0, 9),
        (532, -7, 6, -6), (560, -5, 7, -4), (750, -5, 7, -3), (840, -4, 5, -2), (860, 4, -4, 0), (900, 0, 0, 0), (930, 0, -2, 0),
        (1000, 0, 4, 0), (1030, 6, 18, 0), (1080, 8, 20, 0), (1100, 40, -6, 0), (1135, 48, -8, 0), (1160, 10, 12, 0),
        (1185, 4, 16, 0), (END, 2, 14, 0)]
hy = pchip([(k[0], k[1]) for k in HEAD]); hp_ = pchip([(k[0], k[2]) for k in HEAD]); hr = pchip([(k[0], k[3] if len(k) > 3 else 0.0) for k in HEAD])
for f in list(range(1, END + 1, 4)) + [END]:
    key_head(f, hy(f), hp_(f), hr(f))
# face: focused (slight squint), the hit (eyes wide), shock (jaw drops, brows up), relief (exhale, small smile)
for f, sm, br, jaw, sq in ((1, 0.05, -0.1, 0.0, 0.25), (500, 0.05, -0.1, 0.0, 0.25), (530, -0.3, 0.8, 0.25, 0.0), (750, -0.3, 0.8, 0.25, 0.0),
                           (840, -0.2, 0.6, 0.1, 0.0), (860, -0.4, 1.0, 0.45, 0.0), (930, -0.3, 0.9, 0.30, 0.0), (1030, -0.2, 0.8, 0.2, 0.0),
                           (1100, -0.2, 0.9, 0.35, 0.0), (1150, -0.1, 0.7, 0.2, 0.0), (1175, 0.3, 0.4, 0.05, 0.1), (END, 0.75, 0.3, 0.05, 0.15)):
    key_face(BR, f, smile=sm, brow=br, jaw=jaw, squint=sq)
blinks(BR, [70, 210, 330, 455, 905, 1050, 1165])
saccades(CT, 1, 520, every=30, amp=(1.5, 3.0), seed=4)
saccades(CT, 900, END, every=34, amp=(1.0, 2.0), seed=5)

# ================================================================== the headset rides on his head (Child Of head) until he lifts it off
owner_switch(HS, 1, BR, "head", log=log)
# the headset was fitted to the REST head: the Child Of inverse comes from the rest pose, so it sits on the posed head
for c in HS.constraints:
    if c.type == 'CHILD_OF': c.inverse_matrix = (BR.matrix_world @ BR.data.bones["head"].matrix_local).inverted() @ Matrix.Translation(Vector(HS["rest_loc"]))

# ================================================================== hands: left on the keyboard (WASD), right on the mouse; typing
DESK_Z = 0.73                       # desk top (01_build)
def surf_top(obj):
    upd(); dg = bpy.context.evaluated_depsgraph_get(); e = obj.evaluated_get(dg); me = e.to_mesh()
    z = max((obj.matrix_world @ v.co).z for v in me.vertices); e.to_mesh_clear(); return z
KEY_Z = surf_top(O["HM_Keys"]); MOUSE = O["HM_Mouse"]; MOUSE_Z = surf_top(MOUSE)
MOUSE0 = MOUSE.location.copy()
log("key top z", round(KEY_Z, 3), "mouse top z", round(MOUSE_Z, 3))
def kb_hand(f, dx=0.0, dz=0.0):
    p = Vector((0.20 + dx, -0.47, KEY_Z))
    place_hand(BR, "L", f, p + Vector((0, 0, dz)), Vector((0.1, 0, -1)), Vector((-0.15, -1, 0)), skin=0.040)
    key_pole("L", f, Vector((0.45, 0.10, 0.85)))
def mouse_hand(f, dx=0.0, dy=0.0):
    p = Vector((MOUSE0.x + dx, MOUSE0.y + 0.005 + dy, MOUSE_Z))
    place_hand(BR, "R", f, p, Vector((-0.1, 0, -1)), Vector((0.05, -1, 0)), skin=0.018)
    key_pole("R", f, Vector((-0.45, 0.10, 0.85)))
    MOUSE.location = (MOUSE0.x + dx, MOUSE0.y + dy, MOUSE0.z); MOUSE.keyframe_insert("location", frame=f)
rk = random.Random(3)
for f in range(1, 841, 10):
    kb_hand(f, dx=rk.uniform(-0.012, 0.012), dz=0.004 if (f // 10) % 2 else 0.0)
    apply_pose(BR, "L", "relaxed", f, amount=1.0 if (f // 10) % 2 else 1.0)
    if (f // 10) % 3 == 1: apply_pose(BR, "L", "pinch", f, amount=0.35)
for f in range(1, 841, 14):
    mouse_hand(f, dx=0.012 * math.sin(f * 0.05), dy=0.008 * math.sin(f * 0.031))
    apply_pose(BR, "R", "cup_hold", f)

# ================================================================== the bullet path: far -> glass -> his left ear cup
GLASS = CRACK.location.copy() + Vector((0.004, 0, 0))
fs(F_HIT); CUP_HIT = CK.matrix_world.translation.copy()
D = (CUP_HIT - GLASS).normalized(); L_IN = (CUP_HIT - GLASS).length
RGT = D.cross(UP).normalized()
log("glass", tuple(round(x, 3) for x in GLASS), "cup hit", tuple(round(x, 3) for x in CUP_HIT), "inside flight m", round(L_IN, 3))
BL = 0.0155
S_IN = pchip([(F_GLASS, 0.0), (60, 0.20), (126, 0.42), (230, 0.95), (387, 1.12), (470, L_IN - 0.10), (F_HIT, L_IN)])
def nose_room(f):
    if f <= F_GLASS: return GLASS - D * (F_GLASS - f) * 0.0625
    if f <= F_HIT: return GLASS + D * S_IN(f)
    u = min(1.0, (f - F_HIT) / 20.0); return CUP_HIT + D * 0.005 * (1 - (1 - u) ** 2)
def q_dir(d): return Vector((0, 0, 1)).rotation_difference(Vector(d).normalized())
BUL.rotation_mode = 'QUATERNION'
spin = 0.0
fs(F_HIT); MCK0 = CK.matrix_world.copy()
for f in range(1, SWAP1):
    spin += math.radians(14 if f <= F_GLASS else 4 if f < F_HIT else 1)
    nose = nose_room(f)
    M = Matrix.Translation(nose - D * BL) @ (q_dir(D) @ Quaternion((0, 0, 1), spin)).to_matrix().to_4x4()
    if f > F_HIT:                      # embedded in the cup: it moves with the cup (his head jolts)
        fs(f); M = CK.matrix_world @ MCK0.inverted() @ M
    loc, q, _ = M.decompose()
    BUL.location = loc; BUL.rotation_quaternion = q
    BUL.keyframe_insert("location", frame=f); BUL.keyframe_insert("rotation_quaternion", frame=f)
# ---- macro: nose depth below the shell face (local z) on the VO beats; deflection at the metal frame
ZN = pchip([(SWAP1, 0.0030), (606, 0.0), (614, -0.0032), (640, -0.0080), (680, -0.0140), (705, -0.0166), (712, -0.0171)])
QM = Quaternion((1, 0, 0), math.pi)
EXIT = Vector((-0.30, -0.55, 0.78)).normalized()
for f in range(SWAP1, SWAP2):
    if f <= 712:
        spin += math.radians(3)
        BUL.location = MX + Vector((0, 0, ZN(f) + BL)); BUL.rotation_quaternion = QM @ Quaternion((0, 0, 1), spin)
    else:
        u = (f - 712) / 40.0; e_ = smoothstep(min(1.0, u * 1.6))
        nose = MX + Vector((0, 0, -0.0171)) + EXIT * (0.0 if f < 716 else 0.0016 * (f - 716) ** 1.25)
        tilt = Quaternion((1, 0, 0), math.radians(-130 * e_))           # the nose tips toward the camera side and up
        q = tilt @ QM @ Quaternion((0, 0, 1), spin)
        BUL.location = nose - (q @ Vector((0, 0, BL))); BUL.rotation_quaternion = q
    BUL.keyframe_insert("location", frame=f); BUL.keyframe_insert("rotation_quaternion", frame=f)
# ---- room again: leaves the cup toward the back wall, embeds in it
WALL = WH.location.copy()
fs(SWAP2); CUP2 = CK.matrix_world.translation.copy()
DW = (WALL - CUP2).normalized(); LW = (WALL - CUP2).length
SW = pchip([(SWAP2, 0.0), (770, 0.30), (F_WALL, LW + 0.006)])
for f in range(SWAP2, END + 1):
    spin += math.radians(6 if f < F_WALL else 0)
    nose = CUP2 + DW * SW(min(f, F_WALL)) + CK.matrix_world.translation * 0
    if f < 760: fs(f); nose = CK.matrix_world.translation + DW * SW(f)       # still leaving the (moving) cup
    q = q_dir(DW) @ Quaternion((0, 0, 1), spin)
    BUL.location = nose - DW * BL; BUL.rotation_quaternion = q
    BUL.keyframe_insert("location", frame=f); BUL.keyframe_insert("rotation_quaternion", frame=f)
set_interp(BUL, 'LINEAR'); quat_continuity(BUL)
# trail: long outside, short in slow motion, none in the cup/macro, short again toward the wall
for f, L_ in ((1, 0.40), (F_GLASS, 0.40), (F_GLASS + 4, 0.06), (400, 0.04), (515, 0.015), (522, 0.001), (SWAP2, 0.001), (758, 0.08), (F_WALL - 4, 0.08), (F_WALL, 0.001)):
    w_ = 2.5 if f <= F_GLASS else 1.0
    TRAIL.scale = (w_, w_, L_); TRAIL.keyframe_insert("scale", frame=f)
vis(TRAIL, 1, False); vis(TRAIL, F_BUL, True); vis(TRAIL, 523, False); vis(TRAIL, SWAP2 + 2, True); vis(TRAIL, F_WALL, False)
vis(BUL, 1, False); vis(BUL, F_BUL, True)

# ================================================================== glass: crack + 36 shards falling to the floor/sill (they settle)
for f, s_ in ((1, 0.001), (F_GLASS, 0.001), (F_GLASS + 1, 0.5), (F_GLASS + 4, 1.0)):
    CRACK.scale = (s_,) * 3; CRACK.keyframe_insert("scale", frame=f)
vis(CRACK, 1, False); vis(CRACK, F_GLASS, True)
SILL_Z = O["HM_SillIn"].location.z + 0.015
rg = random.Random(11)
for o in [o for o in O if o.name.startswith("HM_Shard")]:
    p0 = Vector(o["home"]); v = Vector((-rg.uniform(0.001, 0.004), rg.uniform(-0.002, 0.002), rg.uniform(-0.001, 0.002)))
    p = p0.copy(); rot = Vector((0, 0, 0)); w = Vector((rg.uniform(-0.2, 0.2), rg.uniform(-0.2, 0.2), rg.uniform(-0.2, 0.2)))
    o.rotation_mode = 'XYZ'
    vis(o, 1, False); vis(o, F_GLASS + 1, True)
    landed = False
    for f in range(F_GLASS + 1, F_GLASS + 120):
        if not landed:
            v.z -= 0.0006 * (1.0 if f > F_GLASS + 4 else 0.3)
            p += v; rot += w
            floor = SILL_Z if p.x > O["HM_SillIn"].location.x - 0.09 and p.z > SILL_Z - 0.01 else 0.0015
            if p.z <= floor:
                p.z = floor; landed = True
                o.location = p; o.rotation_euler = (0, math.radians(90), rot.z)     # lies flat on the floor / sill
                o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
                break
        if (f - F_GLASS) % 2 == 0:
            o.location = p; o.rotation_euler = rot; o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
    set_interp(o, 'LINEAR')

# ================================================================== the cup hit: crack spreads, crater, chips, sparks; the shard drift settles
gr = CK.data.materials[0].node_tree.nodes["Grow"].outputs[0]
for f, v in ((1, 0.01), (F_HIT, 0.01), (F_HIT + 3, 0.45), (F_HIT + 18, 1.0), (END, 1.0)):
    gr.default_value = v; gr.keyframe_insert("default_value", frame=f)
vis(CK, 1, False); vis(CK, F_HIT, True)
for ob_ in (SHL, CK):
    kb = ob_.data.shape_keys.key_blocks["crater"]
    for f, v in ((1, 0.0), (F_HIT, 0.0), (F_HIT + 12, 1.0), (END, 1.0)):
        kb.value = v; kb.keyframe_insert("value", frame=f)
fs(F_HIT); CN = (CK.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()     # the cup's outward face normal
rc = random.Random(4)
for o in [o for o in O if o.name.startswith("HS_Chip")]:
    o.rotation_mode = 'XYZ'
    v = (CN * rc.uniform(0.002, 0.004) + Vector((0, rc.uniform(-0.003, 0.003), rc.uniform(0.0, 0.004))))
    p = CUP_HIT + CN * 0.003; w = Vector((rc.uniform(-0.3, 0.3), rc.uniform(-0.3, 0.3), rc.uniform(-0.3, 0.3))); r_ = Vector((0, 0, 0))
    vis(o, 1, False); vis(o, F_HIT + 1, True)
    for f in range(F_HIT + 1, F_HIT + 200):
        v.z -= 0.0003
        p += v; r_ += w
        if p.z <= 0.002:
            p.z = 0.002; o.location = p; o.rotation_euler = (0, 0, r_.z); o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f); break
        if f % 3 == 0:
            o.location = p; o.rotation_euler = r_; o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
    set_interp(o, 'LINEAR')
SPARKS = [o for o in O if o.name.startswith("FX_Spark")]
def spark_burst(objs, f0, origin, normal, spread=0.8, speed=(0.002, 0.006), life=14, seed=1, size=1.0):
    r = random.Random(seed)
    for o in objs:
        d = (Vector(normal) + Vector((r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-1, 1))) * spread).normalized()
        sp = r.uniform(*speed); o.rotation_mode = 'QUATERNION'
        o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
        for k in range(life + 1):
            o.location = Vector(origin) + d * sp * k + Vector((0, 0, -0.00004 * k * k))
            s_ = size * (1.0 - k / (life + 1))
            o.scale = (s_, s_, s_ * (2.0 if k < life // 2 else 1.0))
            for p_ in ("location", "rotation_quaternion", "scale"): o.keyframe_insert(p_, frame=f0 + k)
        vis(o, f0 - 1, False); vis(o, f0, True); vis(o, f0 + life + 1, False)
for o in SPARKS: vis(o, 1, False)
spark_burst(SPARKS[:12], F_HIT + 1, CUP_HIT + CN * 0.003, CN, speed=(0.0015, 0.004), life=22, seed=1)
spark_burst(SPARKS[12:], 708, MX + Vector((0, -0.003, -0.0172)), Vector((0, -1, 0.6)), spread=0.7, speed=(0.0006, 0.0016), life=24, seed=2, size=0.35)
spark_burst(SPARKS[:12], SWAP2 + 1, CUP2 + CN * 0.003, (DW + CN).normalized(), speed=(0.002, 0.005), life=18, seed=3)
spark_burst(SPARKS[12:], F_WALL, WALL + Vector((0, -0.004, 0)), Vector((0, -1, 0.2)), speed=(0.004, 0.010), life=16, seed=5, size=1.6)
for o in SPARKS: set_interp(o, 'LINEAR')

# ================================================================== macro wound state + shell crack
EN = pchip([(SWAP1, 0.0), (606, 0.6), (612, 1.0), (690, 0.8), (708, 1.0), (716, 0.6), (732, 0.0), (SWAP2, 0.0)])
TB = pchip([(SWAP1, 0.0005), (606, 0.0005), (614, ZN(614)), (640, ZN(640)), (680, ZN(680)), (705, ZN(705)), (712, ZN(712)), (SWAP2, ZN(712))])
for f in range(SWAP1, SWAP2 + 1, 2):
    WCTL.location = (EN(f), TB(f), 1.0 if f >= 611 else 0.0)
    WCTL.keyframe_insert("location", frame=f)
WCTL.location = (0, 0.0005, 0); WCTL.keyframe_insert("location", frame=1)
set_interp(WCTL, 'LINEAR')
for f, s_ in ((1, 0.001), (607, 0.001), (611, 0.5), (616, 1.0)):
    MCK.scale = (s_,) * 3; MCK.keyframe_insert("scale", frame=f)

# ================================================================== the wall hit: hole, plaster chips falling and settling on the floor
gw = WH.data.materials[0].node_tree.nodes["Grow"].outputs[0]
WH.scale = (1, 1, 1)
for f, v in ((1, 0.01), (F_WALL, 0.05), (F_WALL + 4, 1.0), (END, 1.0)):
    gw.default_value = v; gw.keyframe_insert("default_value", frame=f)
vis(WH, 1, False); vis(WH, F_WALL, True)
rp = random.Random(8)
for o in [o for o in O if o.name.startswith("HM_PlasterChip")]:
    v = Vector((rp.uniform(-0.006, 0.006), -rp.uniform(0.004, 0.012), rp.uniform(0.0, 0.008))); p = WALL + Vector((0, -0.006, 0))
    vis(o, 1, False); vis(o, F_WALL, True)
    for f in range(F_WALL, F_WALL + 120):
        v.z -= 0.0008; p += v
        if p.z <= 0.004:
            p.z = 0.004; o.location = p; o.keyframe_insert("location", frame=f); break
        o.location = p; o.keyframe_insert("location", frame=f)
    set_interp(o, 'LINEAR')

# ================================================================== startle (hands off the desk), then he pulls the headset off
def cup_face(side, f):
    """world centre of the outer face of a cup, its outward normal and the cup's 'up' direction"""
    fs(f); sh = O["HS_Shell" + side]; M = sh.matrix_world
    sx = 1 if side == "L" else -1
    out_n = (M.to_3x3() @ Vector((1, 0, 0))).normalized()          # the right cup has scale.x = -1, so this is outward for both
    centre = M @ Vector((0.020 + 0.026, 0, 0))                                         # cushion + shell depth along the cup axis
    upv = (M.to_3x3() @ Vector((0, 0, 1))).normalized()
    return centre, out_n, upv
# hands lift off the keyboard and mouse in shock (f840-880), then rise to the cups (grip at 935)
for f in (845, 870):
    u = (f - 840) / 30.0
    place_hand(BR, "L", f, Vector((0.22, -0.40 + 0.04 * u, KEY_Z + 0.06 + 0.05 * u)), Vector((0.2, 0.3, -1)), Vector((-0.1, -1, 0.2)), skin=0.02)
    key_pole("L", f, Vector((0.45, 0.10, 0.85)))
    place_hand(BR, "R", f, Vector((-0.24, -0.40 + 0.04 * u, MOUSE_Z + 0.06 + 0.05 * u)), Vector((-0.2, 0.3, -1)), Vector((0.1, -1, 0.2)), skin=0.02)
    key_pole("R", f, Vector((-0.45, 0.10, 0.85)))
    apply_pose(BR, "L", "open_alarm", f, amount=0.6); apply_pose(BR, "R", "open_alarm", f, amount=0.6)
F_GRIP, F_OFF, F_SIDE, F_FWD, F_DOWN = 935, 972, 995, 1015, 1035
# the right hand takes the headset by the top of its band (a closed fist), the left hand goes back down to the keyboard
fs(925); HSinv = HS.matrix_world.inverted()
upd(); dgb = bpy.context.evaluated_depsgraph_get(); eb_ = O["HS_Band"].evaluated_get(dgb); meb_ = eb_.to_mesh()
bl_ = [HSinv @ (O["HS_Band"].matrix_world @ v.co) for v in meb_.vertices]; eb_.to_mesh_clear()
LP = max(bl_, key=lambda v: v.z)                                 # top of the band, outer surface (HS local)
log("band top (HS local)", tuple(round(x, 3) for x in LP))
def band_grip(f, lift=0.0, pose_amt=0.55):
    fs(f); M = HS.matrix_world; R3 = M.to_3x3().normalized()
    top = M @ LP; dn = -(R3 @ Vector((0, 0, 1))).normalized(); fw = (R3 @ Vector((0, -1, 0))).normalized()
    place_hand(BR, "R", f, top - dn * lift, dn, fw, skin=0.012)
    key_pole("R", f, Wh(BR, "upperarm01.R") + Vector((-0.45, 0.10, 0.0)))
    if pose_amt > 0: apply_pose(BR, "R", "wrap_grip", f, amount=pose_amt)
    else: apply_pose(BR, "R", "relaxed", f)
band_grip(905, lift=0.09, pose_amt=0.0); band_grip(925, lift=0.025, pose_amt=0.0)
for f in (910, 930, 1000, 1100, END):
    kb_hand(f); apply_pose(BR, "L", "relaxed", f)
# from F_GRIP the headset leaves the head: straight up, out to his right, forward clear of his face, then down to chest height
fs(F_GRIP); M0 = HS.matrix_world.copy(); c0 = M0.translation.copy()
owner_switch(HS, F_GRIP + 1, None, log=log)
OFFS = [(F_GRIP, Vector((0, 0, 0))), (F_OFF, Vector((0, 0, 0.17))), (F_SIDE, Vector((-0.30, -0.06, 0.17))),
        (F_FWD, Vector((-0.32 - c0.x, -0.47 - c0.y, 0.10 + 1.10 - c0.z))), (F_DOWN, Vector((-0.12 - c0.x, -0.45 - c0.y, 0.965 - c0.z)))]
ox = [pchip([(f, v[i]) for f, v in OFFS]) for i in range(3)]
def hs_world(f):
    u = smoothstep((f - F_FWD) / (F_DOWN - F_FWD))
    R = Matrix.Rotation(math.radians(-30 * u), 4, 'Z')             # the damaged left cup turns toward the front-left
    T = Matrix.Translation(c0 + Vector([ox[i](f) for i in range(3)]))
    return T @ R @ Matrix.Translation(-c0) @ M0
for f in range(F_GRIP + 1, F_DOWN + 1, 2):
    key_world_while_owned(HS, f, hs_world(f))
fs(F_DOWN); MD = HS.matrix_world.copy(); cD = MD.translation.copy()
def hs_hold(f):
    R = Matrix.Rotation(math.radians(-6 * smoothstep((f - 1045) / 60.0)), 4, 'Z') @ Matrix.Rotation(math.radians(2.5 * math.sin(f * 0.05)), 4, 'X')
    return Matrix.Translation(cD + Vector((0, 0, 0.005 * math.sin(f * 0.04)))) @ R @ Matrix.Translation(-cD) @ MD
for f in range(F_DOWN + 2, END + 1, 3):
    key_world_while_owned(HS, f, hs_hold(f))
set_interp(HS, 'LINEAR')
for piv, sx in ((PIVL, 1), (PIVR, -1)):
    piv.rotation_mode = 'XYZ'
    for f, a_ in ((1, 0), (F_GRIP, 0), (955, 9), (F_SIDE, 9), (F_DOWN, 4), (END, 4)):
        piv.rotation_euler = (0, math.radians(-sx * a_), 0); piv.keyframe_insert("rotation_euler", frame=f)
for f in range(F_GRIP, END + 1, 2):
    band_grip(f)

# ================================================================== camera: ONE camera, PCHIP paths, level horizon
cam_d = bpy.data.cameras.new("CAM_Film"); CAM = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(CAM); sc.camera = CAM
AIM = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(AIM)
cam_d.sensor_fit = 'AUTO'; cam_d.sensor_width = 36; cam_d.dof.use_dof = False; cam_d.clip_start = 0.004; cam_d.clip_end = 80
CAM.rotation_mode = 'QUATERNION'
def bpos(f): fs(f); return BUL.matrix_world.translation.copy()
def head_c(f): fs(f); return (Wh(BR, "eye.L") + Wh(BR, "eye.R")) / 2
def cupc(f): fs(f); return (SHL.matrix_world @ CK.matrix_parent_inverse @ CK.matrix_basis).translation.copy()   # valid while CK is hidden
def P(*v): return Vector(v)
HC = head_c(300); log('seated head centre', tuple(round(x, 3) for x in HC))
SEG_A = [
    (1,   lambda: GLASS - D * 3.9 + UP * 0.35 + RGT * 0.30, lambda: GLASS + UP * 0.40, 22),
    (24,  lambda: bpos(24) - D * 0.60 + UP * 0.14 + RGT * 0.30, lambda: bpos(24) + D * 0.9, 24),
    (40,  lambda: P(2.30, 0.33, 1.42), lambda: GLASS + D * 0.25, 24),
    (56,  lambda: P(1.46, 0.26, 1.36), lambda: bpos(56).lerp(head_c(56), 0.4), 26),
    (90,  lambda: bpos(90) - D * 0.24 + RGT * 0.05 + UP * 0.03, lambda: bpos(90) + D * 0.6, 28),
    (185, lambda: bpos(185) - D * 0.15 + RGT * 0.03 + UP * 0.02, lambda: bpos(185) + D * 0.6, 30),
    (228, lambda: bpos(228) - D * 0.14 + RGT * 0.03 + UP * 0.02, lambda: bpos(228) + D * 0.6, 30),
    (275, lambda: HC + Vector((0.75, -0.25, 0.10)), lambda: HC.lerp(Vector((0.10, -0.45, 0.78)), 0.5), 28),
    (318, lambda: P(0.48, -0.72, HC.z + 0.02), lambda: P(0.05, -0.36, HC.z - 0.15), 24),
    (352, lambda: P(0.14, -0.72, HC.z + 0.06), lambda: head_c(352) + Vector((0, 0, -0.04)), 28),
    (387, lambda: P(0.32, -0.60, HC.z + 0.08), lambda: head_c(387).lerp(cupc(387), 0.5), 32),
    (430, lambda: cupc(430) + Vector((0.16, -0.55, 0.05)), lambda: head_c(430).lerp(cupc(430), 0.55), 26),
    (480, lambda: cupc(480) + Vector((0.15, -0.46, 0.04)), lambda: head_c(480).lerp(cupc(480), 0.6), 28),
    (519, lambda: cupc(519) + Vector((0.12, -0.34, 0.03)), lambda: head_c(519).lerp(cupc(519), 0.7), 30),
    (560, lambda: cupc(560) + Vector((0.09, -0.10, 0.02)), lambda: cupc(560), 40),
    (590, lambda: cupc(590) + Vector((0.040, -0.040, 0.010)), lambda: cupc(590), 40),
    (599, lambda: cupc(599) + Vector((0.034, -0.034, 0.008)), lambda: cupc(599), 40),
]
def zc(f): return BUL.matrix_world.translation.copy() if False else MX + Vector((0, 0, ZN(min(f, 712)) + BL * 0.5))
def orb(f, ang, dist, dz, aimz=0.0):
    a_ = math.radians(ang); return (lambda: zc(f) + P(math.sin(a_) * dist, -math.cos(a_) * dist, dz), lambda: zc(f) + P(0, 0, aimz))
SEG_M = []
for f, ang, dist, dz, az, ln in ((607, 12, 0.045, 0.008, -0.002, 40), (640, -8, 0.052, 0.004, -0.004, 42), (680, -20, 0.058, -0.002, -0.006, 42),
                                 (705, -10, 0.050, -0.004, -0.006, 44), (722, 22, 0.058, 0.004, 0.0, 42), (735, 28, 0.066, 0.010, 0.005, 40)):
    pf, af = orb(f, ang, dist, dz, az); SEG_M.append((f, pf, af, ln))
SEG_B = [
    (SWAP2, lambda: P(0.30, -0.75, HC.z + 0.06), lambda: head_c(SWAP2).lerp(WALL, 0.05), 24),
    (800, lambda: P(0.32, -0.73, HC.z + 0.05), lambda: head_c(800).lerp(WALL, 0.10), 22),
    (F_WALL, lambda: P(0.28, -0.73, HC.z + 0.05), lambda: head_c(F_WALL).lerp(WALL, 0.12), 22),
    (880, lambda: P(0.15, -0.72, HC.z + 0.05), lambda: head_c(880) + Vector((0, 0, -0.05)), 26),
    (940, lambda: P(0.14, -0.73, HC.z + 0.10), lambda: head_c(940) + Vector((0, 0, 0.02)), 24),
    (995, lambda: P(0.55, -0.70, HC.z + 0.04), lambda: head_c(995), 26),
    (1040, lambda: P(0.60, -0.70, HC.z - 0.02), lambda: head_c(1040).lerp(cupc(1040), 0.45), 28),
    (1085, lambda: P(0.62, -0.64, HC.z), lambda: head_c(1085).lerp(cupc(1085), 0.40), 30),
    (1130, lambda: P(0.50, -0.74, HC.z + 0.04), lambda: head_c(1130) + Vector((0.05, 0, -0.03)), 26),
    (END, lambda: P(0.58, -0.66, HC.z - 0.03), lambda: head_c(END).lerp(cupc(END), 0.45), 30),
]
def look_q(p, a, up=Vector((0, 0, 1))):
    zc_ = (p - a).normalized(); yc = (up - zc_ * up.dot(zc_)); yc = yc.normalized() if yc.length > 1e-6 else Vector((0, 1, 0))
    xc = yc.cross(zc_); return Matrix((xc, yc, zc_)).transposed().to_quaternion()
CAMKEYS = {}
def run_seg(seg, f_from, f_to):
    ks = [(f, pf(), af(), l) for f, pf, af, l in seg]
    fx = [pchip([(k[0], k[1][i]) for k in ks]) for i in range(3)]
    ax = [pchip([(k[0], k[2][i]) for k in ks]) for i in range(3)]
    fl = pchip([(k[0], k[3]) for k in ks])
    for f in range(f_from, f_to + 1):
        p = Vector([fx[i](f) for i in range(3)]); a_ = Vector([ax[i](f) for i in range(3)])
        CAMKEYS[f] = (p, look_q(p, a_), a_, fl(f))
run_seg(SEG_A, 1, SWAP1 - 1)
run_seg(SEG_M, 607, SWAP2 - 1)
run_seg(SEG_B, SWAP2, END)
# inside the first flash (600-606): the camera keeps its pose relative to the bullet (room -> macro), then eases to the orbit
pS, qS, aS, lS = CAMKEYS[SWAP1 - 1]
fs(SWAP1 - 1); MB_s = BUL.matrix_world.copy()
rel = MB_s.inverted() @ (Matrix.Translation(pS) @ qS.to_matrix().to_4x4())
fs(SWAP1); MB_m = BUL.matrix_world.copy()
M0c = MB_m @ rel; p0, q0 = M0c.translation.copy(), M0c.to_quaternion()
p1, q1, a1, l1 = CAMKEYS[607]
for f in range(SWAP1, 607):
    u = smoothstep((f - SWAP1) / (607 - SWAP1))
    CAMKEYS[f] = (p0.lerp(p1, u), q0.slerp(q1, u), a1, lS + (l1 - lS) * u)
prev = None
for f in range(1, END + 1):
    p, q, a_, l_ = CAMKEYS[f]
    if prev is not None and prev.dot(q) < 0: q = -q
    prev = q
    CAM.location = p; CAM.rotation_quaternion = q; AIM.location = a_; cam_d.lens = l_
    CAM.keyframe_insert("location", frame=f); CAM.keyframe_insert("rotation_quaternion", frame=f)
    AIM.keyframe_insert("location", frame=f); cam_d.keyframe_insert("lens", frame=f)
set_interp(CAM, 'LINEAR'); set_interp(AIM, 'LINEAR'); set_interp(cam_d, 'LINEAR')
log("camera keyed", len(CAMKEYS))
cl = bpy.data.lights.new("Catch", 'AREA'); cl.energy = 2.0; cl.size = 0.25; cl.color = (1, 0.96, 0.92)
clo = bpy.data.objects.new("Catchlight", cl); bpy.data.collections["HOME"].objects.link(clo); clo.parent = CAM; clo.location = (0.0, 0.10, 0.0)
for f in list(range(1, END + 1, 6)) + [END]:
    fs(f); d_ = (CAM.matrix_world.translation - head_c(f)).length
    cl.energy = max(0.1, min(2.0, 2.0 * (d_ / 0.9) ** 2)); cl.keyframe_insert("energy", frame=f)

# ================================================================== the impact flashes (camera-parented sphere, camera rays only)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=48, ring_count=24); FL = bpy.context.active_object; FL.name = "ImpactFlash"
for p_ in FL.data.polygons: p_.use_smooth = True
fm = bpy.data.materials.new("M_ImpactFlash"); fm.use_nodes = True; nt = fm.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
cxy = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(sep.outputs["X"], cxy.inputs[0]); nt.links.new(sep.outputs["Y"], cxy.inputs[1])
ab = nt.nodes.new("ShaderNodeVectorMath"); ab.operation = 'LENGTH'; nt.links.new(cxy.outputs[0], ab.inputs[0])
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (1.0, 0.92, 0.65, 1); cr.color_ramp.elements[1].position = 0.95
cr.color_ramp.elements[1].color = (0.55, 0.02, 0.01, 1)
e_ = cr.color_ramp.elements.new(0.35); e_.color = (1.0, 0.45, 0.05, 1)
nt.links.new(ab.outputs[1], cr.inputs["Fac"])
em = nt.nodes.new("ShaderNodeEmission"); nt.links.new(cr.outputs["Color"], em.inputs["Color"])
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); lp = nt.nodes.new("ShaderNodeLightPath")
av = nt.nodes.new("ShaderNodeValue"); av.name = "FlashAlpha"; av.outputs[0].default_value = 0.0
mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; nt.links.new(lp.outputs["Is Camera Ray"], mul.inputs[0]); nt.links.new(av.outputs[0], mul.inputs[1])
mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(mul.outputs[0], mx.inputs["Fac"]); nt.links.new(tr.outputs["BSDF"], mx.inputs[1]); nt.links.new(em.outputs["Emission"], mx.inputs[2])
nt.links.new(mx.outputs["Shader"], nt.nodes["Material Output"].inputs["Surface"])
FL.data.materials.append(fm)
FL.visible_shadow = False; FL.visible_diffuse = False; FL.visible_glossy = False; FL.visible_transmission = False
for c in list(FL.users_collection): c.objects.unlink(FL)
sc.collection.objects.link(FL)
FL.parent = CAM; FL.matrix_parent_inverse = Matrix.Identity(4); FL.location = (0, 0, 0); FL.scale = (0.060,) * 3                  # the bullet (and the cup it touches) stay visible inside the flash
VA = av.outputs[0]
for f, a_ in ((1, 0.0), (595, 0.0), (599, 1.0), (602, 1.0), (607, 0.0), (733, 0.0), (736, 1.0), (740, 1.0), (744, 0.0), (END, 0.0)):
    VA.default_value = a_; VA.keyframe_insert("default_value", frame=f)
vis(FL, 1, False); vis(FL, 594, True); vis(FL, 608, False); vis(FL, 732, True); vis(FL, 745, False)

# ================================================================== set visibility (keyed hide_render + hide_viewport on every object)
HOME = [o for o in bpy.data.collections["HOME"].all_objects]
MACRO = [o for o in bpy.data.collections["MACRO"].all_objects]
EXTRA = {}
for o in HOME:
    vis(o, 1, True); vis(o, SWAP1, False); vis(o, SWAP2, True)
for o in MACRO:
    vis(o, 1, False); vis(o, SWAP1, True); vis(o, SWAP2, False)
vis(CRACK, 1, False); vis(CRACK, F_GLASS, True); vis(CRACK, SWAP1, False); vis(CRACK, SWAP2, True)
vis(CK, 1, False); vis(CK, F_HIT, True); vis(CK, SWAP1, False); vis(CK, SWAP2, True)
vis(WH, 1, False); vis(WH, F_WALL, True)
for o in [o for o in O if o.name.startswith("HM_Shard")]:
    vis(o, 1, False); vis(o, F_GLASS + 1, True); vis(o, SWAP1, False); vis(o, SWAP2, True)
for o in [o for o in O if o.name.startswith("HS_Chip")]:
    vis(o, 1, False); vis(o, F_HIT + 1, True); vis(o, SWAP1, False); vis(o, SWAP2, True)
for o in [o for o in O if o.name.startswith("HM_PlasterChip")]:
    vis(o, 1, False); vis(o, F_WALL, True)

# ================================================================== the chair sits under him (seat top at his trousers' lowest point)
fs(300)
def low_z(obj, x0, x1, y0, y1):
    upd(); dg = bpy.context.evaluated_depsgraph_get(); e = obj.evaluated_get(dg); me = e.to_mesh(); Mw = obj.matrix_world
    zs = [(Mw @ v.co).z for v in me.vertices if x0 < (Mw @ v.co).x < x1 and y0 < (Mw @ v.co).y < y1]
    e.to_mesh_clear(); return min(zs) if zs else None
seat_low = low_z(CL, -0.18, 0.18, -0.05, 0.20)
back_y = None
upd(); dg = bpy.context.evaluated_depsgraph_get(); e = CL.evaluated_get(dg); me = e.to_mesh(); Mw = CL.matrix_world
back_y = max((Mw @ v.co).y for v in me.vertices if 0.75 < (Mw @ v.co).z < 1.1 and abs((Mw @ v.co).x) < 0.12); e.to_mesh_clear()
CH = O["HM_Chair"]; CHB = O["HM_ChairBase"]
CH.location = (0.0, 0.02, seat_low - 0.045 + 0.006)          # seat cushion top (0.045 above its centre) 6 mm into the trousers (soft)
fs(300); upd()
log("seat low z", round(seat_low, 3), "back y", round(back_y, 3))
# backrest: its front face ~1.5 cm behind his back
bk = O["CH_Back"]; upd()
front_y = world_bvh(bk).ray_cast(Vector((0, -0.5, 0.92)), Vector((0, 1, 0)), 3.0)[0].y
CH.location.y += (back_y + 0.015) - front_y
CHB.location = (0.0, CH.location.y + 0.06, 0.0)
sb = CH.location.z - 0.045; gas = O["CH_Gas"]; gas.scale.z = (sb - 0.07) / 0.30; gas.location.z = 0.07 + (sb - 0.07) / 2
log("chair at", tuple(round(x, 3) for x in CH.location))

# ================================================================== VO, output
sc.frame_start, sc.frame_end = 1, END
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor; strips = se.strips if hasattr(se, "strips") else se.sequences
strips.new_sound("VO", VO, 1, 1)
sc.render.filepath = "//render/HeadsetBullet_v009_####.png"; sc.render.image_settings.file_format = 'PNG'
for o in O:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = False
log("quat flips fixed", quat_continuity(BR))
sc.frame_set(1)
open(os.path.join(os.path.dirname(OUT), "animate_log.txt"), "w").write("\n".join(LOG))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("ANIM_DONE", OUT)
