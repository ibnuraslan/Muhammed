"""v003 pass: hands (relaxed curl, real grips, Limit Rotation on fingers/thumbs/wrists), couple facial expressions,
and a hand-contact audit. blender -b film.blend --python 08_hands_faces.py -- <out.blend> <audit.txt>"""
import sys, os, math
import bpy
from mathutils import Vector, Matrix, Quaternion
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
exec(open(os.path.join(HERE, "00_story.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]
sc = bpy.context.scene
R_ = math.radians
humans = [o for o in bpy.data.objects if o.type == 'ARMATURE' and "finger1-1.L" in o.pose.bones]
GRIP = {("NerveA", "R"): 22, ("Officer", "L"): 62, ("Officer", "R"): 16, ("Archduke", "L"): 6, ("Archduke", "R"): 6, ("Duchess", "R"): 10, ("Duchess", "L"): 62, ("Gunman", "R"): 70, ("Driver", "L"): 55, ("Driver", "R"): 55, ("Bomber", "R"): 60,
        }

def palm_frame(arm, s):
    B = arm.data.bones
    wr = B["wrist." + s].head_local
    dd = (B["finger3-1." + s].head_local - wr).normalized()
    aa = (B["finger2-1." + s].head_local - B["finger5-1." + s].head_local).normalized()
    n = dd.cross(aa) if s == "L" else aa.cross(dd)
    return dd, aa, n.normalized()

def curl_hand(arm, s, deg):
    B = arm.data.bones; PB = arm.pose.bones
    dd, aa, n = palm_frame(arm, s)
    for fi in range(1, 6):
        for j in range(1, 4):
            nm = f"finger{fi}-{j}.{s}"
            if nm not in PB: continue
            b = B[nm]; d = (b.tail_local - b.head_local).normalized()
            if fi == 1:   # thumb: curl across the palm toward the fingers (opposition)
                tgt = (n * 0.6 + aa * -0.8 * (1 if s == "L" else 1)).normalized()
                ang = deg * (0.45 if j == 1 else 0.6)
            else:
                tgt = n; ang = deg * (1.0 if j == 1 else 1.15 if j == 2 else 0.9) * (1.0 + 0.06 * (fi - 2))
            ax_w = d.cross(tgt)
            if ax_w.length < 1e-4: continue
            ax_l = (b.matrix_local.to_3x3().inverted() @ ax_w).normalized()
            q = Quaternion(ax_l, R_(min(ang, 95)))
            pb = PB[nm]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q
            # limits in local space around the curl: forward 0..90 on the dominant axis, small spread
            c = pb.constraints.get("HandLimit") or pb.constraints.new('LIMIT_ROTATION'); c.name = "HandLimit"
            c.owner_space = 'LOCAL'
            e = q.to_euler('XYZ')
            for k, axn in enumerate("xyz"):
                lo, hi = (min(0.0, e[k]) - R_(10), max(0.0, e[k]) + R_(10))
                if abs(ax_l[k]) == max(abs(x) for x in ax_l):   # bend axis: 0..90 in the curl direction only
                    lo, hi = (min(0.0, math.copysign(R_(90), e[k])), max(0.0, math.copysign(R_(90), e[k])))
                setattr(c, "use_limit_" + axn, True); setattr(c, "min_" + axn, lo); setattr(c, "max_" + axn, hi)
for arm in humans:
    base = arm.name.split("_")[0] if arm.name.startswith("Crowd") else arm.name
    for s in "LR":
        curl_hand(arm, s, GRIP.get((arm.name, s), 12 + 4 * ((hash(arm.name) % 3))))
        pb = arm.pose.bones["wrist." + s]
        c = pb.constraints.get("WristLimit") or pb.constraints.new('LIMIT_ROTATION'); c.name = "WristLimit"; c.owner_space = 'LOCAL'
        c.use_limit_x = c.use_limit_z = True; c.min_x, c.max_x = R_(-60), R_(60); c.min_z, c.max_z = R_(-35), R_(35)
        c.use_limit_y = True; c.min_y, c.max_y = R_(-70), R_(70)
# lift the Archduke's resting hands onto the thighs (clip_scan: fingertips were 3-5 cm inside the thighs)
def lift_hand(name, side, dz, dx=0.0, fmin=0):
    arm = bpy.data.objects[name]; n = "IK_hand." + side
    dl = arm.data.bones[n].matrix_local.to_3x3().inverted() @ Vector((dx, 0, dz))
    for l in arm.animation_data.action.layers:
        for st in l.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    if fc.data_path == f'pose.bones["{n}"].location':
                        for kp in fc.keyframe_points:
                            if kp.co[0] < fmin: continue
                            kp.co[1] += dl[fc.array_index]; kp.handle_left[1] += dl[fc.array_index]; kp.handle_right[1] += dl[fc.array_index]
                        fc.update()
for sd in "LR": lift_hand("Archduke", sd, 0.07)
lift_hand("Duchess", "R", 0.03)
# slumped (story 26.75+ = film 1583+): hands fall beside the thighs onto the seat, not into them
lift_hand("Archduke", "R", 0.03, dx=-0.09, fmin=1561)   # outer hand drops beside his thigh onto the seat
lift_hand("Archduke", "L", 0.04, fmin=1561)            # inner hand stays on his thigh (moving it inward would hit the Duchess)
# would-be assassin: flat palm resting ON the coat (it floated 3-4 cm in front of the chest)
def shift_hand_world(name, side, v, f0=0, f1=10**9):
    arm = bpy.data.objects[name]; n = "IK_hand." + side
    dl = arm.data.bones[n].matrix_local.to_3x3().inverted() @ v
    for l in arm.animation_data.action.layers:
        for st in l.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    if fc.data_path == f'pose.bones["{n}"].location':
                        for kp in fc.keyframe_points:
                            if f0 <= kp.co[0] <= f1:
                                kp.co[1] += dl[fc.array_index]; kp.handle_left[1] += dl[fc.array_index]; kp.handle_right[1] += dl[fc.array_index]
                        fc.update()
# palm keyed onto the chest surface while the hand is "in the coat" (story 0.7-2.2 s)
NA_ = bpy.data.objects["NerveA"]; RN = Rig(NA_)
for f in range(380, 1201, 2):
    s_ = sig_f(f)
    k = smooth((s_ - 0.7) / 0.4) * (1 - smooth((s_ - 2.0) / 0.3))
    if k < 0.02: continue
    sc.frame_set(f)
    ch = NA_.matrix_world @ NA_.pose.bones["spine03"].head
    hn = NA_.matrix_world @ RN.PB["IK_hand.R"].head
    d = hn - ch; d.z = 0; d = d.normalized()
    side = Vector((0, 0, 1)).cross(d).normalized()
    tgt = ch + d * 0.16 + side * 0.04 + Vector((0, 0, 0.1))
    tgt = hn.lerp(tgt, k)
    RN.key_world("IK_hand.R", f, Matrix.Translation(NA_.matrix_world.inverted() @ tgt - RN.BN["IK_hand.R"].head_local) @ RN.rest("IK_hand.R"), rot=False)
# officer's grab: both hands keyed onto the gunman's actual right arm every 2 frames while he holds him
OFF = bpy.data.objects["Officer"]; GNo = bpy.data.objects["Gunman"]; RO = Rig(OFF)
grab_frames = [f for f in range(1301, 1781, 2) if sig_f(f) > 27.0]
targets = {}
for f in grab_frames:
    sc.frame_set(f)
    up = GNo.matrix_world @ GNo.pose.bones["upperarm02.R"].head.lerp(GNo.pose.bones["upperarm02.R"].tail, 0.4)
    fo = GNo.matrix_world @ GNo.pose.bones["upperarm02.R"].head.lerp(GNo.pose.bones["upperarm02.R"].tail, 0.9)   # second hand near his elbow
    osh = OFF.matrix_world @ OFF.pose.bones["spine03"].head
    targets[f] = (up, fo, osh)
for f, (up, fo, osh) in targets.items():
    k = min(1.0, (sig_f(f) - 27.0) / 0.3)
    for side, pt in (("L", up),):   # one-handed grab: the far hand cannot reach across, it stays relaxed at his side
        n = "IK_hand." + side
        cur = RO.PB[n]; sc.frame_set(f)
        now = OFF.matrix_world @ cur.head
        toward = (osh - pt); toward.z = 0; toward = toward.normalized() * 0.055     # palm on the sleeve surface, on the officer's side
        tgt = now.lerp(pt + toward, k)
        RO.key_world(n, f, Matrix.Translation(OFF.matrix_world.inverted() @ tgt - RO.BN[n].head_local) @ RO.rest(n), rot=False)
for f in targets:
    sc.frame_set(f)
    k = min(1.0, (sig_f(f) - 27.0) / 0.3)
    hip = OFF.matrix_world @ OFF.pose.bones["upperleg01.R"].head
    pel = OFF.matrix_world @ OFF.pose.bones["root"].head
    out = hip - pel; out.z = 0; out = out.normalized() if out.length > 1e-4 else Vector((0, 0, 0))
    tgt = hip + out * 0.1 + Vector((0, 0, -0.08))
    now = OFF.matrix_world @ RO.PB["IK_hand.R"].head
    RO.key_world("IK_hand.R", f, Matrix.Translation(OFF.matrix_world.inverted() @ now.lerp(tgt, k) - RO.BN["IK_hand.R"].head_local) @ RO.rest("IK_hand.R"), rot=False)
print("OFFICER grab keyed", len(targets))
print("HANDS curled + limits on", len(humans), "rigs")
# ================================================================ shared hand-pose library (director, Nov 12): replaces the hand-set curls
exec(open(os.path.join(HERE, "..", "..", "pipeline", "hand_poses.py")).read())
for arm in humans:
    for s_ in "LR":
        for n in [f"finger{k}-{j}.{s_}" for k in range(1, 6) for j in (1, 2, 3)] + ["wrist." + s_]:
            pb = arm.pose.bones.get(n)
            if pb is None: continue
            for c in [c for c in pb.constraints if c.name in ("HandLimit", "WristLimit")]: pb.constraints.remove(c)
            pb.rotation_quaternion = (1, 0, 0, 0)
    add_hand_limits(arm)
    if arm.name.startswith("Crowd"):   # the library's elbow IK limit flips the crowd's clapping arms into their torsos; keep the old elbow solve
        for s_ in "LR":
            lo = arm.pose.bones.get("lowerarm01." + s_)
            if lo: lo.use_ik_limit_x = False
def pose_track(arm, side, chooser, frames):
    prev = None
    for f in frames:
        pz = chooser(sig_f(f))
        if pz != prev:
            if prev is not None: apply_pose(arm, side, prev, f - 2)
            apply_pose(arm, side, pz, f); prev = pz
STORY = list(range(1, 2131, 2))
special = {"Archduke", "Duchess", "Driver", "Gunman", "Bomber", "NerveA", "Officer"}
for arm in humans:
    if arm.name in special or arm.hide_render: continue
    for s_ in "LR": apply_pose(arm, s_, "relaxed", 1, amount=0.45)   # half curl: full relaxed curl put fingertips into the thighs/other hand while clapping
for s_ in "LR": apply_pose(bpy.data.objects["Archduke"], s_, "flat_palm", 1)
apply_pose(bpy.data.objects["Duchess"], "L", "wrap_grip", 1)
apply_pose(bpy.data.objects["Duchess"], "R", "flat_palm", 1)
apply_pose(bpy.data.objects["NerveA"], "R", "flat_palm", 1); apply_pose(bpy.data.objects["NerveA"], "L", "relaxed", 1)
pose_track(bpy.data.objects["Gunman"], "R", lambda s_: "wrap_grip" if 24.6 <= s_ < 40 else "relaxed", STORY)
apply_pose(bpy.data.objects["Gunman"], "L", "relaxed", 1)
pose_track(bpy.data.objects["Bomber"], "R", lambda s_: "wrap_grip" if 1.5 <= s_ < REL_S else "relaxed", list(range(380, 1201, 2)))
apply_pose(bpy.data.objects["Bomber"], "L", "relaxed", 1)
pose_track(bpy.data.objects["Officer"], "L", lambda s_: "wrap_grip" if s_ >= 27.0 else "relaxed", STORY)
apply_pose(bpy.data.objects["Officer"], "R", "relaxed", 1)
# --- driver: real grips on the steering-wheel rim (contact points from the wheel model's geometry, car-local, held constant)
DRV = bpy.data.objects["Driver"]; BODY = bpy.data.objects["Car1_Body"]; SW_ = bpy.data.objects["Car1_Sway"]
WC = Vector((0.178, -0.307, 1.323)); XA = Vector((1, 0, 0)); UP = Vector((0, 0.63, 0.78)).normalized(); NRM = XA.cross(UP).normalized()
for arm_side in ("L", "R"):
    n = "IK_hand." + arm_side
    for l in DRV.animation_data.action.layers:
        for st in l.strips:
            for cb in st.channelbags:
                for fc in list(cb.fcurves):
                    if fc.data_path in (f'pose.bones["{n}"].location', f'pose.bones["{n}"].rotation_quaternion'): cb.fcurves.remove(fc)
FREF = 1451; sc.frame_set(FREF)
Ms = SW_.matrix_world
for side, th in (("L", math.radians(25)), ("R", math.radians(155))):
    radial = (XA * math.cos(th) + UP * math.sin(th)).normalized()
    cp_local = WC + radial * 0.175
    cpw = Ms @ cp_local; nw = (Ms.to_3x3() @ NRM).normalized()
    shp = DRV.matrix_world @ DRV.pose.bones["upperarm01." + side].head
    if nw.dot(cpw - shp) < 0: nw = -nw
    print("DRIVER", side, "grip", grip_object(DRV, side, FREF, BODY, cpw, nw, finger_dir=(Ms.to_3x3() @ radial).normalized()))
    n = "IK_hand." + side; pb = DRV.pose.bones[n]
    loc, q = pb.location.copy(), pb.rotation_quaternion.copy()
    for f in (1, 2130):
        pb.location = loc; pb.rotation_quaternion = q
        pb.keyframe_insert("location", frame=f, group=n); pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
    # copy the finger closure (keyed at FREF) to the ends so it holds for the whole drive
    for k in range(1, 6):
        for j in (1, 2, 3):
            fb = DRV.pose.bones.get(f"finger{k}-{j}.{side}")
            if fb:
                sc.frame_set(FREF); qq = fb.rotation_quaternion.copy()
                for f in (1, 2130): fb.rotation_quaternion = qq; fb.keyframe_insert("rotation_quaternion", frame=f, group=fb.name)
print("DRIVER grips on rim")
# --- Duchess: inner (R) hand rests flat on the seat cushion beside her (it hovered 3-8 cm over the seat), until the fright at 25.1 s
DU_ = bpy.data.objects["Duchess"]
fstar = next(f for f in range(1300, 2131) if sig_f(f) >= 25.1)
n_ = "IK_hand.R"
for l in DU_.animation_data.action.layers:
    for st in l.strips:
        for cb in st.channelbags:
            for fc in cb.fcurves:
                if fc.data_path in (f'pose.bones["{n_}"].location', f'pose.bones["{n_}"].rotation_quaternion'):
                    for kp in [k for k in fc.keyframe_points if k.co[0] < fstar - 12][::-1]: fc.keyframe_points.remove(kp)
                    fc.update()
SEATZ = sc.get("SEAT_R", 0.96)
sc.frame_set(FREF); Ms = SW_.matrix_world; R3s = Ms.to_3x3()
for f in (1, fstar - 12):
    place_hand(DU_, "R", f, Ms @ Vector((0.11, 0.80, SEATZ + 0.005)), (R3s @ Vector((0, 0, -1))).normalized(), (R3s @ Vector((-0.25, -1, 0))).normalized())
# parasol hand lifted clear of the door top (it hovered 2-5 cm over it)
shift_hand_world("Duchess", "L", Vector((-0.04, -0.02, 0.1)), f1=fstar)
# parasol re-seated so the shaft runs through the closed hand (between the thumb tip and the index root)
sc.frame_set(1); bpy.context.view_layer.update()
par = bpy.data.objects["Parasol"]; DU = bpy.data.objects["Duchess"]
grip = (DU.matrix_world @ DU.pose.bones["finger2-1.L"].head + DU.matrix_world @ DU.pose.bones["finger1-3.L"].tail + DU.matrix_world @ DU.pose.bones["finger5-1.L"].head) / 3
M = par.matrix_world.copy(); ax = (M.to_3x3() @ Vector((0, 0, 1))).normalized(); o = M.translation
closest = o + ax * (grip - o).dot(ax)
delta = grip - closest
cst = par.constraints["Child Of"]
par.matrix_basis = Matrix.Translation(cst.inverse_matrix.inverted() @ (M.translation + delta) - cst.inverse_matrix.inverted() @ M.translation) @ par.matrix_basis
print("PARASOL shifted", round(delta.length, 3))
print("DUCHESS hands placed")

# ---------------------------------------------------------------- faces: couple expressions on the story clock
def face(arm_name, f, smile, shock, closed):
    arm = bpy.data.objects[arm_name]; R = Rig(arm)
    def off(n, v):
        if n in R.PB: R.key_world(n, f, Matrix.Translation(v) @ R.rest(n), rot=False)
    for s, sx in (("L", 1), ("R", -1)):
        off("risorius03." + s, Vector((sx * 0.006 * smile - sx * 0.002 * shock, 0.004 * smile, 0.006 * smile - 0.004 * shock)))
        off("risorius02." + s, Vector((sx * 0.003 * smile, 0.002 * smile, 0.003 * smile)))
        off("oris04." + s, Vector((sx * 0.003 * smile, 0.0, 0.003 * smile)))
        off("levator05." + s, Vector((0, 0, 0.002 * smile)))
        off("orbicularis03." + s, Vector((0, 0, 0.0035 * shock - 0.007 * closed - 0.0015 * smile)))
        off("orbicularis04." + s, Vector((0, 0, -0.002 * shock + 0.003 * closed + 0.0015 * smile)))
        off("oculi02." + s, Vector((0, 0, 0.007 * shock)))
        off("temporalis01." + s, Vector((0, 0, 0.004 * shock)))
    R.key_rot("jaw", f, [("X", 13 * shock + 4 * closed + 2 * smile)])
import random as _r
_r.seed(11)
def _blinker():
    bl = []; t = _r.uniform(0.5, 1.5)
    while t < 30.0: bl.append(1 + round(t * 60)); t += _r.uniform(2.4, 3.6)
    return lambda f: max([0.0] + [max(0.0, 1 - abs(f - b0 - 2) / 3.0) for b0 in bl if abs(f - b0 - 2) < 3])
BL = {n: _blinker() for n in ("Archduke", "Duchess", "Gunman")}
FR2 = list(range(1, 1781, 2))
def sm(x): return max(0.0, min(1.0, x)) ** 2 * (3 - 2 * max(0.0, min(1.0, x)))
for f in FR2:
    s = sig_f(f)
    # smiles while waving to the crowd; fright at the thrown object; shock at the gun; eyes close after the slump
    a_smile = (1 - sm((s - 3.35) / 0.2)) if s < 4 else (1 - sm((s - 25.0) / 0.3)) * sm((s - 7.0) / 1.0)
    a_shock = max(sm((s - 3.4) / 0.2) * (1 - sm((s - 5.5) / 0.8)), sm((s - 25.15) / 0.3))
    a_closed = sm((s - 26.8) / 0.5)
    d_smile = (1 - sm((s - 3.4) / 0.2)) if s < 4 else (1 - sm((s - 25.1) / 0.3)) * sm((s - 7.0) / 1.0)
    d_shock = max(sm((s - 3.45) / 0.2) * (1 - sm((s - 5.6) / 0.8)), sm((s - 25.2) / 0.3))
    d_closed = sm((s - 26.3) / 0.5)
    face("Archduke", f, a_smile * (1 - a_shock), a_shock * (1 - a_closed), max(a_closed, BL["Archduke"](f)))
    face("Duchess", f, d_smile * (1 - d_shock), d_shock * (1 - d_closed), max(d_closed, BL["Duchess"](f)))
for f in range(1301, 1781, 2):
    s = sig_f(f)
    flinch = max((1 - min(1.0, abs(s - st) / 0.12)) for st in SHOT_S)
    face("Gunman", f, 0.0, flinch * 0.6, BL["Gunman"](f))
print("FACES keyed")

bpy.ops.wm.save_as_mainfile(filepath=OUT)
