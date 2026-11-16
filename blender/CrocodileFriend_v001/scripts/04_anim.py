"""Phase-1 clips: every shot is its own range on one timeline (hard cuts via camera markers), ~30% longer than
the expected beat so it can be trimmed to the VO later without stretching.
blender -b work/sets.blend -P scripts/04_anim.py -- work/film.blend"""
import bpy, sys, os, math, json
from mathutils import Vector, Matrix, Quaternion, Euler
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PIPE = os.path.join(HERE, "..", "pipeline")
OUT = sys.argv[-1]
exec(open(os.path.join(PIPE, "anim_lib.py")).read())
exec(open(os.path.join(PIPE, "hand_poses.py")).read())
sc = bpy.context.scene; R_ = math.radians
sc.render.fps = 60; sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
WATER_Z = -0.22; RX = -45.0; HX = 45.0
OB = bpy.data.objects

# ------------------------------------------------------------------ ground (ray cast on walkable surfaces)
GROUND = [o for o in OB if o.type == 'MESH' and (o.name.startswith(("Ground_", "House", "Hall_Floor", "DeckPlank")))]
def ground_z(x, y, top=3.0):
    return max(_gz(x, y, top), _gz(x, y + 0.06, top), _gz(x, y - 0.06, top))   # deck planks have 2 cm gaps
def _gz(x, y, top=3.0):
    best = None
    for o in GROUND:
        inv = o.matrix_world.inverted(); oo = inv @ Vector((x, y, top)); dd = (inv.to_3x3() @ Vector((0, 0, -1))).normalized()
        ok, loc, n, i = o.ray_cast(oo, dd)
        if ok:
            z = (o.matrix_world @ loc).z
            if best is None or z > best: best = z
    return best if best is not None else 0.0

# ------------------------------------------------------------------ man (Keeper) rig prep
MAN = OB["Keeper"]
for ch in MAN.children:
    if "short02" in ch.name: ch.hide_render = ch.hide_viewport = True     # bald, like the real story's man (generic face)
bpy.context.view_layer.objects.active = MAN
for o in bpy.context.selected_objects: o.select_set(False)
MAN.select_set(True)
bpy.ops.object.mode_set(mode='POSE')
for pb in MAN.pose.bones:
    for c in list(pb.constraints):
        if c.type in ('IK', 'COPY_ROTATION'): pb.constraints.remove(c)
bpy.ops.object.mode_set(mode='EDIT')
for b in list(MAN.data.edit_bones):
    if b.name.startswith(("IK_", "Pole_")): MAN.data.edit_bones.remove(b)
bpy.ops.object.mode_set(mode='OBJECT')
RM = make_human_ctrl(MAN); add_hand_limits(MAN)
for s in "LR":
    lo = MAN.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = R_(-40); lo.ik_max_x = R_(140)
H = Human(RM)
# shirt / trousers: clean solid colours (non-skin)
def recolor(rig, key, rgb):
    for ch in rig.children:
        if key in ch.name:
            for i, m in enumerate(ch.data.materials):
                if not m: continue
                m2 = m.copy(); ch.data.materials[i] = m2
                for n in m2.node_tree.nodes:
                    if n.type == 'BSDF_PRINCIPLED':
                        for l in list(n.inputs["Base Color"].links): m2.node_tree.links.remove(l)
                        n.inputs["Base Color"].default_value = rgb + (1,)
recolor(MAN, "casualsuit01", (0.10, 0.30, 0.62))   # mid-blue shirt + trousers: clearly clothed, never skin-toned

# ------------------------------------------------------------------ croc rig helpers
CROC = OB["Croc"]; CR = Rig(CROC)
for pb in CROC.pose.bones: pb.rotation_mode = 'QUATERNION'
LEGSIDE = {k: (1 if CROC.data.bones[k + "_up"].tail_local.x > 0 else -1) for k in ("FL", "FR", "HL", "HR")}
CROC_HEAD_Y = CROC.data.bones["head"].tail_local.y
def croc_key(f, x, y, head_deg, z=None, pitch=0.0, roll=0.0, gait=0.0, gait_amp=0.0, swim=0.0, swim_amp=0.0,
             neck=(0.0, 0.0), head_up=0.0, tuck=0.0, breathe=0.0, curl=0.0, tail_lift=0.0):
    """head_deg: world heading of the snout (0 = +X). gait: phase (cycles) for the belly-crawl walk; swim: phase for tail undulation.
    curl: static body curve (deg per segment, + = snout turns left)."""
    yaw = head_deg + 90.0
    if z is None: z = ground_z(x, y)
    M = Matrix.Translation(Vector((x, y, z))) @ Matrix.Rotation(R_(yaw), 4, 'Z') @ Matrix.Rotation(R_(pitch), 4, 'X') @ \
        Matrix.Rotation(R_(roll), 4, 'Y') @ CR.rest("root")
    CR.key_world("root", f, M)
    tw = 2 * math.pi * swim; gw = 2 * math.pi * gait
    for i in range(1, 9):
        a = curl * 0.6 + swim_amp * (0.35 + 0.1 * i) * math.sin(tw - 0.7 * i) + gait_amp * 0.35 * math.sin(gw - 0.5 * i)
        tl = tail_lift * (0.0 if i < 3 else (0.5 if i == 3 else 0.35))
        CR.key_rot("tail%d" % i, f, [("Z", a), ("X", tl)])
    sp = gait_amp * 0.25 * math.sin(gw)
    CR.key_rot("spine1", f, [("Z", sp + curl * 0.5), ("X", breathe)])
    CR.key_rot("spine2", f, [("Z", -sp + curl * 0.5)])
    CR.key_rot("neck", f, [("X", -neck[0]), ("Z", neck[1] - sp * 0.5 + curl * 0.4)])
    CR.key_rot("head", f, [("X", -head_up)])
    for k in ("FL", "FR", "HL", "HR"):
        sd = LEGSIDE[k]; ph = 0.0 if k in ("FL", "HR") else 0.5
        c = math.sin(gw + 2 * math.pi * ph); lift = max(0.0, math.cos(gw + 2 * math.pi * ph))
        fore = -1 if k[0] == "F" else 1
        swing = gait_amp * c * sd * (-1)
        tk = tuck * sd * (70 if k[0] == "F" else 60)
        CR.key_rot(k + "_up", f, [("Y", -sd * gait_amp * 0.6 * lift), ("Z", swing + tk)])
        CR.key_rot(k + "_lo", f, [("Z", 0.0)])

# ------------------------------------------------------------------ man pose helpers
SH = {s: RM.BN["upperarm01." + s].head_local.copy() for s in "LR"}
def root_matrix(pos, yaw, flex=0.0, side=0.0):
    Rw = Matrix.Rotation(R_(yaw), 3, 'Z') @ Matrix.Rotation(R_(flex), 3, 'X') @ Matrix.Rotation(R_(side), 3, 'Y')
    return Matrix.Translation(pos) @ Rw.to_4x4() @ Matrix.Translation(-H.root_head)
def fwd(yaw):  # MPFB faces -Y at rest
    return Matrix.Rotation(R_(yaw), 3, 'Z') @ Vector((0, -1, 0))
def rightv(yaw):
    return Matrix.Rotation(R_(yaw), 3, 'Z') @ Vector((-1, 0, 0))
def man_stand(f, pos, yaw, flex=0.0, spine=(0, 0, 0), head=(0, 0), crouch=0.0, stance=0.0, feet=None):
    """pos: xy floor point under the pelvis; z from ground. feet: optional dict side->(xy Vector, yaw, lift, pitch)"""
    g = ground_z(pos.x, pos.y)
    H.key_root(f, Vector((pos.x, pos.y, g + H.root_head.z - crouch)), yaw=yaw, flex=flex * 0.5)
    H.key_spine(f, flex=spine[0], twist=spine[1], side=spine[2], head=head)
    for s in "LR":
        if feet and s in feet:
            xy, fy, lf, pt = feet[s]; H.key_foot(s, f, xy, fy, lf, pt)
        else:
            sx = 1 if s == "L" else -1
            xy = H.foot_xy(s, pos, yaw) + (rightv(yaw) * (-sx * stance)).to_2d()
            H.key_foot(s, f, xy, yaw)
def hand_idle(f, s, yaw, fwd_off=0.06, out=0.10, drop=0.0):
    """relaxed hanging hand beside the thigh (evaluated shoulder)"""
    sc.frame_set(f); sh = MAN.matrix_world @ MAN.pose.bones["upperarm01." + s].head
    sx = 1 if s == "L" else -1
    W = sh + Vector((0, 0, -0.56 + drop)) + fwd(yaw) * fwd_off + rightv(yaw) * (-sx * out)
    d = Vector((0, 0, -1)) + fwd(yaw) * 0.15; n = rightv(yaw) * sx
    pole = sh + fwd(yaw) * -0.5 + Vector((0, 0, -0.3)) + rightv(yaw) * (-sx * 0.2)
    H.key_hand(s, f, W, d, n, pole)
def hand_at(f, s, W, d, n, yaw, pole_off=(-0.5, -0.25, 0.25)):
    sc.frame_set(f); sh = MAN.matrix_world @ MAN.pose.bones["upperarm01." + s].head; sx = 1 if s == "L" else -1
    pole = sh + fwd(yaw) * pole_off[0] + Vector((0, 0, pole_off[1])) + rightv(yaw) * (-sx * pole_off[2])
    H.key_hand(s, f, Vector(W), Vector(d), Vector(n), pole)
def palm_on(f, s, P, normal, fdir, yaw, pole_off=(-0.5, -0.25, 0.3)):
    sc.frame_set(f); sh = MAN.matrix_world @ MAN.pose.bones["upperarm01." + s].head; sx = 1 if s == "L" else -1
    place_hand(MAN, s, f, P, normal, fdir)
    pole = sh + fwd(yaw) * pole_off[0] + Vector((0, 0, pole_off[1])) + rightv(yaw) * (-sx * pole_off[2])
    pb = MAN.pose.bones["Pole_elbow." + s]; nme = pb.name
    pb.location = RM.rest(nme).to_3x3().inverted() @ (pole - RM.BN[nme].head_local); pb.keyframe_insert("location", frame=f, group=nme)
def fingers(f, s, pose="relaxed"):
    apply_pose(MAN, s, pose, f)
_wr, _B0, _bas, _pm = _rest_hand(MAN, "R")
RPALM = _rest_palm_sign(MAN, "R", _B0.col[2])           # +1: the key_hand normal points out of the palm
def palm_normal_w(s_):
    wr, B0, bas, pm = _rest_hand(MAN, s_); sg = _rest_palm_sign(MAN, s_, B0.col[2])
    pb = MAN.pose.bones["wrist." + s_]; Rp = (pb.matrix.to_3x3() @ MAN.data.bones["wrist." + s_].matrix_local.to_3x3().inverted())
    return ((MAN.matrix_world.to_3x3() @ Rp) @ (B0.col[2] * sg)).normalized()
def croc_point(local):
    """world point on the croc in its evaluated pose: local = (bone, offset in bone-rest world-aligned frame)"""
    bone, off = local; pb = CROC.pose.bones[bone]
    M = CROC.matrix_world @ pb.matrix @ CROC.data.bones[bone].matrix_local.inverted()
    return M @ (CROC.data.bones[bone].head_local + Vector(off))
def croc_dir(bone, v):
    pb = CROC.pose.bones[bone]; M = (CROC.matrix_world @ pb.matrix @ CROC.data.bones[bone].matrix_local.inverted()).to_3x3()
    return (M @ Vector(v)).normalized()

# ------------------------------------------------------------------ extras
EXTRAS = [o for o in OB if o.type == 'ARMATURE' and o.name not in ("Keeper", "Croc")]
EX = {}
for o in EXTRAS:
    bpy.context.view_layer.objects.active = o
    if not o.pose.bones.get("IK_foot.L"):
        bpy.ops.object.mode_set(mode='POSE')
        for pb in o.pose.bones:
            for c in list(pb.constraints):
                if c.type in ('IK', 'COPY_ROTATION'): pb.constraints.remove(c)
        bpy.ops.object.mode_set(mode='EDIT')
        for b in list(o.data.edit_bones):
            if b.name.startswith(("IK_", "Pole_")): o.data.edit_bones.remove(b)
        bpy.ops.object.mode_set(mode='OBJECT')
        r = make_human_ctrl(o)
    else:
        o.location = (0, 0, 0); r = Rig(o)
        for pb in o.pose.bones: pb.rotation_mode = 'QUATERNION'
    for s in "LR":
        lo = o.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = R_(-40); lo.ik_max_x = R_(140)
    EX[o.name] = Human(r)
def vis(objs, f0, f1):
    """visible only in [f0, f1] (keys hide_render + hide_viewport together)"""
    for o in objs:
        for ob in [o] + list(o.children):
            for f, h in ((1, True), (f0, False), (f1 + 1, True)):
                ob.hide_render = h; ob.hide_viewport = h
                ob.keyframe_insert("hide_render", frame=f); ob.keyframe_insert("hide_viewport", frame=f)
def ex_pose(name, f, pos, yaw, mode="stand", t=0.0, seat_z=0.47):
    h = EX[name]; r = h.r; o = r.o
    if mode == "stand":
        g = ground_z(pos.x, pos.y)
        h.key_root(f, Vector((pos.x, pos.y, g + h.root_head.z - 0.01 - 0.008 * math.sin(t * 2.0))), yaw=yaw)
        h.key_spine(f, flex=2 + 2 * math.sin(t * 1.3), head=(4 * math.sin(t * 0.9), 8 * math.sin(t * 0.6 + len(name))))
        for s in "LR": h.key_foot(s, f, h.foot_xy(s, pos, yaw), yaw)
    elif mode == "sit":
        z = 0.47
        for bo in [o for o in OB if o.name.startswith("Bench.")]:
            inv = bo.matrix_world.inverted(); ok, loc, nn, ii = bo.ray_cast(inv @ Vector((pos.x, pos.y, 0.9)), (inv.to_3x3() @ Vector((0, 0, -1))).normalized())
            if ok: z = max(z if z != 0.47 else 0, (bo.matrix_world @ loc).z)
        z = z + 0.14
        h.key_root(f, Vector((pos.x, pos.y, z)), yaw=yaw, flex=-4)
        h.key_spine(f, flex=6 + 2 * math.sin(t * 1.1), head=(3 * math.sin(t * 0.7), 6 * math.sin(t * 0.5 + len(name))))
        for s in "LR":
            sx = 1 if s == "L" else -1
            xy = (Vector((pos.x, pos.y)) + (fwd(yaw) * 0.58).to_2d() + (rightv(yaw) * (-sx * 0.14)).to_2d())
            h.key_foot(s, f, xy, yaw)

# ------------------------------------------------------------------ cameras + shot table
CAMS = bpy.data.collections.new("CAMERAS"); sc.collection.children.link(CAMS)
SHOTS = []
def shot(name, dur, beat, cam, fn, lens=30, fstop=8.0):
    f0 = (SHOTS[-1]["f1"] + 1) if SHOTS else 1; f1 = f0 + dur - 1
    c = bpy.data.objects.new("CAM_" + name, bpy.data.cameras.new("CAM_" + name)); CAMS.objects.link(c)
    c.data.lens = lens; c.data.clip_start = 0.05; c.data.dof.use_dof = False; c.data.sensor_width = 36
    (l0, t0), (l1, t1) = cam
    for f, l, t in ((f0, l0, t0), (f1, l1, t1)):
        c.location = Vector(l); c.rotation_euler = (Vector(t) - Vector(l)).to_track_quat('-Z', 'Y').to_euler()
        c.keyframe_insert("location", frame=f); c.keyframe_insert("rotation_euler", frame=f)
    m = sc.timeline_markers.new(name, frame=f0); m.camera = c
    SHOTS.append(dict(name=name, f0=f0, f1=f1, beat=beat, fn=fn))
def frames(s, step=2):
    fs = list(range(s["f0"], s["f1"] + 1, step))
    if fs[-1] != s["f1"]: fs.append(s["f1"])
    return fs
def u_of(s, f): return (f - s["f0"]) / max(1, s["f1"] - s["f0"])
V = Vector

# ---------------- B1 river: he pulls the dying croc out by its tail, walking backwards up the bank
def tail_pull(s, start, end, head_deg, cam_unused=None):
    hd = R_(head_deg); back = V((-math.cos(hd), -math.sin(hd)))     # tail direction (where the man is)
    yaw = head_deg + 90.0                                            # man faces the croc (toward its head)
    for f in frames(s):
        u = u_of(s, f); c = start.lerp(end, smooth(u))
        croc_key(f, c.x, c.y, head_deg, head_up=-3, breathe=1.5 * math.sin(f * 0.05), tail_lift=20, curl=2 * math.sin(f * 0.02))
        step = 0.012 * math.sin(f * 0.21)
        man_stand(f, c + back * 2.45, yaw, flex=16, spine=(26, 0, 0), head=(-10, 0), crouch=0.06, stance=0.06)
    for f in frames(s, 2):
        sc.frame_set(f)
        side = croc_dir("tail6", (1, 0, 0))
        for s_, bone in (("L", "tail6"), ("R", "tail5")):
            P = croc_point((bone, (0.0, 0.15, 0.085)))
            palm_on(f, s_, P, V((0, 0, -1)), side if s_ == "R" else -side, yaw, pole_off=(-0.35, -0.1, 0.45))
    for s_ in "LR": fingers(s["f0"], s_, "cup_hold"); fingers(s["f1"], s_, "cup_hold")
def s01(s): tail_pull(s, V((RX - 3.4, 0.0)), V((RX - 1.4, 0.0)), 180.0)
shot("S01_RiverPull", 190, "B1 pulled a dying croc from the riverbank",
     (((RX - 5.4, -1.9, 1.1), (RX - 1.4, 0.2, 0.6)), ((RX - 5.0, -2.2, 1.0), (RX - 0.6, 0.2, 0.6))), s01, 30)
def s02(s): tail_pull(s, V((RX - 1.4, 0.0)), V((RX + 0.0, 0.0)), 180.0)
shot("S02_CrocCloseLow", 150, "B1 (croc head close + man pulling behind)",
     (((RX - 3.4, -0.9, 0.45), (RX - 1.4, 0.0, 0.3)), ((RX - 3.0, -1.2, 0.45), (RX - 0.6, 0.1, 0.4))), s02, 30)

# ---------------- B2 took it home: drags it across the yard to the house
def s03(s): tail_pull(s, V((0.6, -16.6)), V((0.6, -14.4)), -90.0)
shot("S03_DragHome", 170, "B2 and took it home",
     (((2.6, -20.6, 1.0), (0.4, -12.0, 1.4)), ((2.3, -19.6, 1.0), (0.4, -11.0, 1.4))), s03, 28)

# ---------------- B3 treat its wounds: kneels beside it in front of the porch, hand on its back
def kneel(f, pos, yaw, sway=0.0, lean=18.0, head=(-20, 0)):
    g = ground_z(pos.x, pos.y)
    H.key_root(f, Vector((pos.x, pos.y, g + 0.52)), yaw=yaw, flex=8)
    H.key_spine(f, flex=lean + sway, head=head)
    for s in "LR":
        sx = 1 if s == "L" else -1
        xy = (Vector((pos.x, pos.y)) - (fwd(yaw) * 0.42).to_2d() + (rightv(yaw) * (-sx * 0.12)).to_2d())
        H.key_foot(s, f, xy, yaw, 0.0, 70)
def s04(s):
    for f in frames(s):
        u = u_of(s, f)
        croc_key(f, 1.5, -11.0, 180.0, breathe=2 * math.sin(f * 0.06), neck=(0, 6 * math.sin(f * 0.02)), curl=4)
        kneel(f, V((1.25, -10.4)), 0.0, sway=3 * math.sin(u * 6.0))
    for f in frames(s, 4):
        sc.frame_set(f); u = u_of(s, f)
        P = croc_point(("spine2", (0.0, 0.05 + 0.12 * math.sin(u * 9.0), 0.40)))
        palm_on(f, "R", P, V((0, 0, -1)), V((-1, -0.2, 0)), 0.0, pole_off=(-0.3, -0.2, 0.4))
        sh = MAN.matrix_world @ MAN.pose.bones["upperarm01.L"].head
        hand_at(f, "L", sh + V((0.20, 0.04, -0.42)), V((0, 0, -1)), V((-1, 0, 0)), 0.0)
    fingers(s["f0"], "R", "flat_palm"); fingers(s["f1"], "R", "flat_palm"); fingers(s["f0"], "L", "relaxed"); fingers(s["f1"], "L", "relaxed")
shot("S04_Treat", 190, "B3 to treat its wounds (logo crate by the porch steps)",
     (((3.2, -13.6, 1.25), (1.2, -10.6, 0.7)), ((2.8, -13.3, 1.2), (1.2, -10.6, 0.7))), s04, 30)

# ---------------- B4 six months in a secret pond behind his house
def s05(s):
    for f in frames(s):
        u = u_of(s, f)
        croc_key(f, -4.0 + 7.0 * u, 9.0 + 0.6 * math.sin(u * 3), 0.0 + 10 * math.cos(u * 3), z=WATER_Z - 0.28, swim=f / 70.0, swim_amp=14, tuck=0.8)
    pathf = lambda f: V((-3.0 + 5.0 * u_of(s, f), 3.4, 0))
    H.walk(pathf, lambda f: 90.0, s["f0"], s["f1"], stride=0.72)
    for f in frames(s, 4):
        for s_ in "LR":
            sc.frame_set(f); cyc = math.sin(2 * math.pi * (u_of(s, f) * 5.0 / 0.72 * 0.5) + (0 if s_ == "L" else math.pi))
            hand_idle(f, s_, 90.0, fwd_off=0.06 + 0.12 * cyc)
    for s_ in "LR": fingers(s["f0"], s_, "relaxed"); fingers(s["f1"], s_, "relaxed")
shot("S05_PondWide", 200, "B4 kept it in a secret pond behind his house",
     (((-3.6, 0.7, 2.5), (-1.8, 6.5, 0.2)), ((1.6, 0.7, 2.5), (3.0, 6.5, 0.2))), s05, 24)
def s06(s):
    for f in frames(s):
        u = u_of(s, f)
        croc_key(f, 2.6, 8.6 + 2.6 * u, 90.0, z=WATER_Z - 0.27, swim=f / 60.0, swim_amp=16, tuck=0.8)
        man_stand(f, V((-2.0, 3.6)), 200.0, spine=(4, 0, 0), head=(-8, 8))
        for s_ in "LR":
            if f % 4 == 1 or f == s["f1"]: hand_idle(f, s_, 200.0)
    for s_ in "LR": fingers(s["f0"], s_, "relaxed"); fingers(s["f1"], s_, "relaxed")
shot("S06_CrocSwim", 150, "B4 (croc swimming toward camera, house behind)",
     (((3.4, 14.6, 0.75), (2.0, 6.0, 0.9)), ((3.2, 14.3, 0.7), (2.0, 6.0, 0.85))), s06, 30)

# ---------------- B5 nine pounds of meat a day: bucket + toss
BUCKET = OB["Bucket"]; MEAT = OB["Meat"]; MEAT2 = OB["MeatInBucket"]
def s07(s):
    yaw = 0.0; pos = V((-1.0, 4.1))             # standing at the pond edge facing +Y (pond)
    toss_f = s["f0"] + 110
    for f in frames(s):
        u = u_of(s, f); tt = (f - s["f0"]) / 60.0
        man_stand(f, pos, 180.0, spine=(6 + (8 if abs(f - toss_f) < 25 else 0), 0, 0), head=(-12, 0))
        croc_key(f, -0.6, 6.6 - 0.4 * smooth(u * 1.5), -90.0, z=WATER_Z - 0.26 + (0.08 * smooth((f - toss_f + 20) / 25.0) if f > toss_f - 20 else 0),
                 swim=f / 80.0, swim_amp=6, tuck=0.8, neck=(10 * smooth((f - toss_f + 10) / 20.0) if f > toss_f - 10 else 0, 0), head_up=0)
    for f in frames(s, 2):
        sc.frame_set(f)
        # left hand holds the bucket handle at the side
        sh = MAN.matrix_world @ MAN.pose.bones["upperarm01.L"].head
        hand_at(f, "L", sh + V((-0.24, 0.06, -0.52)), V((0, 0, -1)), V((1, 0, 0)), 180.0)
        # right hand: reach into bucket, raise, toss forward (+Y)
        shR = MAN.matrix_world @ MAN.pose.bones["upperarm01.R"].head
        k = (f - s["f0"]) / (toss_f - s["f0"])
        if k < 0.45:   W = shR + V((-0.05, 0.12, -0.55))
        elif k < 0.8:  W = shR + V((-0.05, 0.12, -0.55)).lerp(V((0.22, 0.10, -0.15)), smooth((k - 0.45) / 0.35))
        elif k < 1.0:  W = shR + V((0.22, 0.10, -0.15)).lerp(V((0.0, 0.45, 0.05)), smooth((k - 0.8) / 0.2))
        else:          W = shR + V((0.0, 0.45, 0.05)).lerp(V((-0.05, 0.12, -0.5)), smooth((f - toss_f) / 50.0))
        palm_up = V((0, 0, 1)) * RPALM
        hand_at(f, "R", W, V((0, 1, 0)) if k >= 0.45 else V((0, 0.6, -0.6)), palm_up if k >= 0.45 else V((1, 0, 0)), 180.0)
    fingers(s["f0"], "L", "cup_hold"); fingers(s["f1"], "L", "cup_hold")
    fingers(s["f0"], "R", "relaxed"); fingers(toss_f - 50, "R", "flat_palm"); fingers(toss_f, "R", "flat_palm"); fingers(s["f1"], "R", "relaxed")
    # bucket hangs vertically, its handle apex in the curled left fingers (keyed every frame from the palm)
    BUCKET.rotation_euler = (0, 0, R_(90))
    for f in frames(s, 1):
        sc.frame_set(f); pb = MAN.pose.bones["wrist.L"]
        palm = MAN.matrix_world @ (pb.head.lerp(MAN.pose.bones["finger3-1.L"].head, 1.0))
        BUCKET.location = palm - V((0, 0, 0.42 + 0.03)); BUCKET.keyframe_insert("location", frame=f)
    # meat: rides in the right hand until the toss, then a ballistic arc into the croc's jaws
    MEAT2.hide_render = MEAT2.hide_viewport = True
    rel_f = toss_f
    for f in frames(s, 1):
        sc.frame_set(f)
        if f <= rel_f - 45:
            P = BUCKET.matrix_world.translation + V((0, 0, 0.25))
        elif f <= rel_f:
            pw = MAN.pose.bones["wrist.R"]; P = MAN.matrix_world @ (pw.head.lerp(MAN.pose.bones["finger3-1.R"].head, 0.85))
            P = P + palm_normal_w("R") * 0.05
            if f == rel_f: P_rel = P.copy(); V0 = V((0.0, 2.6, 2.2)) / 1.0
        else:
            t = (f - rel_f) / 60.0; P = P_rel + V0 * t + V((0, 0, -4.9 * t * t))
        MEAT.location = P; MEAT.rotation_euler = (f * 0.08 if f > rel_f else 0.3, 0.2, 0.4)
        MEAT.keyframe_insert("location", frame=f); MEAT.keyframe_insert("rotation_euler", frame=f)
        MEAT.hide_render = MEAT.hide_viewport = (f < rel_f - 45) or (f > rel_f + 45)
        MEAT.keyframe_insert("hide_render", frame=f); MEAT.keyframe_insert("hide_viewport", frame=f)
shot("S07_Feed", 200, "B5 he would feed it 9 pounds of meat a day (plain bucket, no text)",
     (((1.6, 6.4, 1.3), (-0.9, 4.2, 0.9)), ((1.3, 6.7, 1.25), (-0.9, 4.3, 0.85))), s07, 26)
def s08(s):
    for f in frames(s):
        u = u_of(s, f); lunge = math.sin(math.pi * min(1, u * 2.2)) if u < 0.46 else 0.0
        croc_key(f, -0.6, 6.4, -90.0, z=WATER_Z - 0.26 + 0.25 * lunge, pitch=-14 * lunge, swim=f / 60.0, swim_amp=10, tuck=0.8,
                 neck=(16 * lunge, 0), head_up=6 * lunge)
        man_stand(f, V((-1.0, 4.1)), 180.0, spine=(8, 0, 0), head=(-18, 0))
    for f in frames(s, 2):
        sc.frame_set(f)
        sh = MAN.matrix_world @ MAN.pose.bones["upperarm01.L"].head
        hand_at(f, "L", sh + V((-0.24, 0.06, -0.52)), V((0, 0, -1)), V((1, 0, 0)), 180.0)
        hand_idle(f, "R", 180.0)
    for f in frames(s, 1):
        sc.frame_set(f); pb = MAN.pose.bones["wrist.L"]
        palm = MAN.matrix_world @ (pb.head.lerp(MAN.pose.bones["finger3-1.L"].head, 1.0))
        BUCKET.location = palm - V((0, 0, 0.42 + 0.03)); BUCKET.keyframe_insert("location", frame=f)
    vis([BUCKET], SHOTS[-2]["f0"] if False else s["f0"] - 200, s["f1"])
    fingers(s["f0"], "L", "cup_hold"); fingers(s["f1"], "L", "cup_hold"); fingers(s["f0"], "R", "relaxed"); fingers(s["f1"], "R", "relaxed")
shot("S08_Snap", 150, "B5 (croc rises for the meat)",
     (((1.0, 9.6, 0.7), (-0.7, 5.4, 0.8)), ((0.8, 9.2, 0.75), (-0.7, 5.4, 0.85))), s08, 24)

# ---------------- B6 slept beside it (night): on his back, knees drawn up, rolled toward the croc, one hand by his head
SLEEP_P = V((0.6, 2.75)); CROC_SLEEP = (1.2, 3.6)
def sleep_pose(f, u):
    g = ground_z(SLEEP_P.x, SLEEP_P.y); br = math.sin(f * 0.045)
    M = Matrix.Translation(V((SLEEP_P.x, SLEEP_P.y, g + 0.14))) @ Matrix.Rotation(R_(90), 4, 'Z') @ Matrix.Rotation(R_(-88), 4, 'X') @ \
        Matrix.Rotation(R_(-26), 4, 'Y') @ Matrix.Translation(-H.root_head) @ RM.rest("root")
    RM.key_world("root", f, M)
    H.key_spine(f, flex=4 + 1.2 * br, twist=0, side=0, head=(10, 34))
    T = M @ RM.rest("root").inverted()
    for s_ in "LR":
        a_ = H.ankle[s_]
        fw_ = T @ (a_ + V((0, 0, 0.36)))                      # feet slid toward the hips -> knees up
        fw_.z = g + 0.08
        Mf = Matrix.Translation(fw_) @ (T.to_3x3() @ RM.rest("IK_foot." + s_).to_3x3()).to_4x4()
        RM.key_world("IK_foot." + s_, f, Mf)
        pb = RM.PB["Pole_knee." + s_]; n = "Pole_knee." + s_
        pole = (T @ RM.BN["lowerleg01." + s_].head_local) + V((0, 0, 0.9))
        pb.location = RM.rest(n).to_3x3().inverted() @ (pole - RM.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)
    sc.frame_set(f)
    head_w = MAN.matrix_world @ MAN.pose.bones["head"].head
    shR = MAN.matrix_world @ MAN.pose.bones["upperarm01.R"].head
    W = V((head_w.x + 0.05, head_w.y - 0.22, g + 0.06))     # right hand resting on the grass beside his head
    H.key_hand("R", f, W, V((-0.6, -0.4, 0)), V((0, 0, 1)), shR + V((0.2, -0.4, 0.3)))
def sleep_hand(f):
    sc.frame_set(f)
    P = croc_point(("spine2", (0.0, 0.25, 0.40)))
    palm_on(f, "L", P, V((0, 0, -1)), V((-1, 0, 0)), 90.0, pole_off=(0.3, 0.4, 0.3))
def s09(s):
    for f in frames(s):
        croc_key(f, CROC_SLEEP[0], CROC_SLEEP[1], 180.0, breathe=2 * math.sin(f * 0.04), curl=-6)
        sleep_pose(f, u_of(s, f))
    for f in frames(s, 4): sleep_hand(f)
    for s_ in "LR": fingers(s["f0"], s_, "relaxed"); fingers(s["f1"], s_, "relaxed")
shot("S09_SleepWide", 200, "B6 he even slept beside it (night)",
     (((0.9, -0.1, 2.3), (0.8, 3.1, 0.2)), ((0.9, 0.5, 1.9), (0.8, 3.1, 0.2))), s09, 26)
def s10(s): s09(s)
shot("S10_SleepClose", 170, "B6 thinking his love would heal its wounds",
     (((-0.95, 4.25, 1.15), (-0.1, 3.05, 0.25)), ((-0.6, 3.85, 0.9), (-0.1, 3.05, 0.25))), s10, 32)

# ---------------- B7 release: points to the river, croc leaves, refuses, comes back
def s11(s):
    for f in frames(s):
        u = u_of(s, f)
        croc_key(f, -3.6 - 1.8 * u, 2.6 + 1.4 * u, 140.0, gait=f / 45.0, gait_amp=22)
        man_stand(f, V((-1.8, 0.6)), 225.0 - 90 + 90, spine=(4, -10, 0), head=(-5, -12))
    for f in frames(s, 2):
        sc.frame_set(f); u = u_of(s, f)
        shR = MAN.matrix_world @ MAN.pose.bones["upperarm01.R"].head
        a = smooth(min(1, u * 3)) * (1 - smooth(max(0, u - 0.75) * 4))
        W = (shR + V((0, 0, -0.55))).lerp(shR + V((-0.45, 0.35, 0.05)), a)
        hand_at(f, "R", W, V((-0.7, 0.6, 0.1)) * a + V((0, 0, -1)) * (1 - a), V((0, 0, -1)) * a + V((1, 0, 0)) * (1 - a), 225.0)
        hand_idle(f, "L", 225.0)
    fingers(s["f0"], "R", "relaxed"); fingers(s["f0"] + 50, "R", "point"); fingers(s["f1"] - 30, "R", "point"); fingers(s["f1"], "R", "relaxed")
    fingers(s["f0"], "L", "relaxed"); fingers(s["f1"], "L", "relaxed")
shot("S11_Release", 200, "B7 when he tried to release it back to the wild",
     (((-3.7, -0.7, 1.6), (-3.0, 2.2, 0.8)), ((-3.5, -0.4, 1.55), (-3.2, 2.5, 0.8))), s11, 26)
def s12(s):
    for f in frames(s):
        u = u_of(s, f); turn = smooth(min(1, max(0, (u - 0.2) / 0.6)))
        croc_key(f, -5.4, 4.0, 140.0 + 160.0 * turn, gait=f / 45.0 if 0.15 < u < 0.85 else 0.0, gait_amp=18 if 0.15 < u < 0.85 else 0, curl=-12 * math.sin(math.pi * turn))
        man_stand(f, V((-1.8, 0.6)), 225.0, spine=(4, -6, 0), head=(-5, -10))
        if f % 4 == 1 or f == s["f1"]:
            for s_ in "LR": hand_idle(f, s_, 225.0)
    for s_ in "LR": fingers(s["f0"], s_, "relaxed"); fingers(s["f1"], s_, "relaxed")
shot("S12_RefuseTurn", 170, "B7 the crocodile refused to leave (turns back)",
     (((-5.6, 1.6, 2.4), (-5.3, 4.1, 0.1)), ((-5.9, 1.9, 2.3), (-5.3, 4.1, 0.1))), s12, 28)
def s13(s):
    kf = s["f0"] + 90
    for f in frames(s):
        u = u_of(s, f); k = smooth(min(1, (f - s["f0"]) / 120.0))
        croc_key(f, -5.0 + 2.7 * k, 3.6 - 2.0 * k, -40.0, gait=f / 45.0 if k < 0.97 else 0, gait_amp=20 * (1 - k * 0.9),
                 neck=(6 * smooth((f - kf) / 40.0) if f > kf else 0, 0))
        kneel(f, V((-1.8, 0.6)), 225.0, sway=2 * math.sin(f * 0.05), lean=14 + 6 * smooth((f - kf) / 40.0) if f > kf else 14, head=(-10, 0))
    for f in frames(s, 2):
        sc.frame_set(f)
        if f < kf + 30:
            for s_ in "LR": hand_idle(f, s_, 225.0, fwd_off=-0.02, drop=0.10)
        else:
            P = croc_point(("head", (0.0, -0.12, 0.30)))
            palm_on(f, "R", P, V((0, 0, -1)), croc_dir("head", (0, -1, 0)) * -1, 225.0, pole_off=(-0.3, -0.2, 0.4))
            hand_idle(f, "L", 225.0, drop=0.12, fwd_off=0.2)
    fingers(s["f0"], "R", "relaxed"); fingers(kf + 30, "R", "relaxed"); fingers(kf + 50, "R", "flat_palm"); fingers(s["f1"], "R", "flat_palm")
    fingers(s["f0"], "L", "relaxed"); fingers(s["f1"], "L", "relaxed")
shot("S13_ComesBack", 220, "B7 (croc crawls back, he kneels, hand on its head)",
     (((-4.1, -0.1, 1.3), (-2.2, 1.1, 0.5)), ((-3.9, 0.15, 1.25), (-2.2, 1.1, 0.5))), s13, 28)

# ---------------- B8 together 20 years: walking along the pond bank
def walk_pair(s, y0, x0, x1):
    pathf = lambda f: V((x0 + (x1 - x0) * u_of(s, f), y0, 0))
    H.walk(pathf, lambda f: 90.0, s["f0"], s["f1"], stride=0.62)
    for f in frames(s):
        u = u_of(s, f); cx = x0 + (x1 - x0) * u + 0.6
        croc_key(f, cx, y0 + 1.05, 0.0, gait=f / 40.0, gait_amp=20)
    for f in frames(s, 4):
        for s_ in "LR":
            cyc = math.sin(2 * math.pi * ((x1 - x0) * u_of(s, f) / 0.62 * 0.5) + (0 if s_ == "L" else math.pi))
            hand_idle(f, s_, 90.0, fwd_off=0.06 + 0.12 * cyc)
    for s_ in "LR": fingers(s["f0"], s_, "relaxed"); fingers(s["f1"], s_, "relaxed")
def s14(s): walk_pair(s, 3.3, -5.0, -2.2)
shot("S14_WalkSide", 200, "B8 staying with him for over 20 years",
     (((-4.8, 0.9, 1.4), (-4.2, 3.8, 0.45)), ((-2.0, 0.9, 1.4), (-1.4, 3.8, 0.45))), s14, 26)
def s15(s): walk_pair(s, 3.3, -2.0, 0.4)
shot("S15_WalkFront", 170, "B8 (front low)",
     (((2.9, 2.7, 1.5), (0.0, 3.8, 0.45)), ((2.7, 2.7, 1.45), (0.6, 3.8, 0.45))), s15, 28)

# ---------------- B9 shows for tourists
TOUR = [n for n in EX if n.startswith("Spec")]
def tourists(s):
    xs = [-3.2, -2.2, -1.2, -0.2, 0.9, 2.9, 3.6]
    vis([OB[n] for n in TOUR], s["f0"], s["f1"])
    for i, n in enumerate(TOUR):
        h = EX[n]; pos = V((xs[i], 16.25 + 0.25 * (i % 2)))
        for f in frames(s, 4):
            ex_pose(n, f, pos, 0.0 + (i - 3) * 5, t=f / 60.0 + i)
        # arms: lean on the rail / clap / point
        for f in frames(s, 4):
            sc.frame_set(f); o = h.r.o
            for s_ in "LR":
                sh = o.matrix_world @ o.pose.bones["upperarm01." + s_].head; sx = 1 if s_ == "L" else -1
                if i % 3 == 0:     # hands on the rail top
                    W = V((sh.x - sx * 0.02, 15.66, 1.53)); d = V((0, -1, -0.15)); nrm = V((0, 0, -1))
                elif i % 3 == 1:   # clapping in front of the chest
                    cl = 0.05 + 0.05 * abs(math.sin(f * 0.25 + i))
                    W = sh + V((-sx * (cl - 0.17) * -1, -0.32, -0.25)); d = V((0, -0.6, 0.8)); nrm = V((sx, 0, 0))
                else:              # hanging relaxed
                    W = sh + V((sx * 0.07, -0.05, -0.56)); d = V((0, -0.15, -1)); nrm = V((-sx, 0, 0))
                pole = sh + V((sx * 0.25, 0.5, -0.3))
                h.key_hand(s_, f, W, d, nrm, pole)
        for s_ in "LR":
            apply_pose(h.r.o, s_, "relaxed", s["f0"]); apply_pose(h.r.o, s_, "relaxed", s["f1"])
def in_water(s, pat=True):
    mp = V((0.4, 12.6)); yaw = -35.0
    for f in frames(s):
        u = u_of(s, f)
        y_ = yaw + 6 * math.sin(u * 2)
        H.key_root(f, V((mp.x, mp.y, WATER_Z - 0.75 + H.root_head.z)), yaw=y_)
        H.key_spine(f, flex=10, twist=-8, head=(-6, 6 * math.sin(u * 3)))
        for s_ in "LR": H.key_foot(s_, f, H.foot_xy(s_, mp, y_), y_, lift=0.0)
        rt = rightv(yaw); fw = fwd(yaw); hd = math.degrees(math.atan2(fw.y, fw.x))
        cp = mp + (rt * -0.62).to_2d() - (fw * 0.55).to_2d()
        croc_key(f, cp.x, cp.y, hd, z=WATER_Z - 0.2, swim=f / 90.0, swim_amp=6, tuck=0.8, neck=(8 + 4 * math.sin(f * 0.05), 0), head_up=4)
    for f in frames(s, 2):
        sc.frame_set(f); u = u_of(s, f)
        P = croc_point(("head", (0.0, -0.05 - 0.06 * math.sin(f * 0.08), 0.20)))
        palm_on(f, "R", P, V((0, 0, -1)), croc_dir("head", (0, -1, 0)), yaw, pole_off=(-0.3, -0.25, 0.45))
        sh = MAN.matrix_world @ MAN.pose.bones["upperarm01.L"].head
        wave = math.sin(f * 0.15) * 0.08
        hand_at(f, "L", sh + rightv(yaw) * 0.25 + V((0, 0, 0.35 + wave)), V((0, 0, 1)), fwd(yaw), yaw, pole_off=(-0.2, -0.4, 0.5))
    fingers(s["f0"], "R", "flat_palm"); fingers(s["f1"], "R", "flat_palm"); fingers(s["f0"], "L", "relaxed"); fingers(s["f1"], "L", "relaxed")
def s16(s): tourists(s); in_water(s)
shot("S16_ShowWide", 220, "B9 they performed for tourists (logo sign on the deck rail)",
     (((0.6, 8.4, 0.95), (0.8, 14.5, 1.1)), ((0.3, 9.0, 1.0), (0.8, 14.5, 1.1))), s16, 26)
def s17(s): tourists(s); in_water(s)
shot("S17_Tourists", 170, "B9 (tourists' faces, man + croc below)",
     (((-0.9, 13.0, 1.3), (-1.3, 16.4, 1.75)), ((-0.4, 13.2, 1.3), (-1.0, 16.4, 1.75))), s17, 28)

# ---------------- B10 when it finally died (quiet, no close-up distress)
def s18(s):
    for f in frames(s):
        u = u_of(s, f)
        croc_key(f, 1.0, 4.2, 200.0, curl=-3)
        kneel(f, V((0.9, 3.25)), 180.0, sway=1.0 * math.sin(f * 0.03), lean=28, head=(-22, 0))
    for f in frames(s, 4):
        sc.frame_set(f)
        P = croc_point(("spine2", (0.05, 0.1, 0.40)))
        palm_on(f, "R", P, V((0, 0, -1)), V((1, 0, 0)), 180.0, pole_off=(-0.3, -0.2, 0.4))
        hand_idle(f, "L", 180.0, drop=0.14, fwd_off=0.22)
    fingers(s["f0"], "R", "flat_palm"); fingers(s["f1"], "R", "flat_palm"); fingers(s["f0"], "L", "relaxed"); fingers(s["f1"], "L", "relaxed")
shot("S18_Died", 220, "B10 and when it finally died",
     (((0.4, 6.0, 1.35), (0.9, 3.5, 0.55)), ((0.5, 5.7, 1.25), (0.9, 3.5, 0.55))), s18, 30)

# ---------------- B11 public funeral, he sang for his friend
FUN = [n for n in EX if n.startswith("Crowd")] + ["SpecB", "SpecE"]
def audience(s):
    vis([OB[n] for n in FUN], s["f0"], s["f1"])
    seats = [(HX - 2.4, -0.1), (HX - 1.3, 0.25), (HX + 0.4, -0.2), (HX + 2.6, 0.5), (HX - 1.8, -1.4), (HX + 0.9, -1.3)]
    for i, n in enumerate(FUN):
        h = EX[n]; x, y = seats[i]
        yw = 180.0 + math.degrees(math.atan2(x - (HX - 0.7), 2.3 - y)) * 0.6
        for f in frames(s, 4):
            ex_pose(n, f, V((x, y)), yw, mode="stand", t=f / 60.0 + i)
        for f in frames(s, 4):
            sc.frame_set(f); o = h.r.o
            for s_ in "LR":
                sh = o.matrix_world @ o.pose.bones["upperarm01." + s_].head; sx = 1 if s_ == "L" else -1
                Rz = Matrix.Rotation(R_(yw), 3, 'Z')
                if i % 2 == 0:   # hands loosely clasped in front (wrists apart, no finger overlap)
                    W = sh + Rz @ V((-sx * 0.12 * -1 * -1 if False else sx * -0.10, -0.18, -0.48)); d = Rz @ V((0, -0.4, -1)); nrm = Rz @ V((-sx, 0, 0))
                else:            # hanging relaxed
                    W = sh + Rz @ V((sx * 0.13, -0.07, -0.54)); d = Rz @ V((0, -0.15, -1)); nrm = Rz @ V((-sx, 0, 0))
                h.key_hand(s_, f, W, d, nrm, sh + Rz @ V((sx * 0.25, 0.5, -0.3)))
        for s_ in "LR":
            apply_pose(h.r.o, s_, "relaxed", s["f0"]); apply_pose(h.r.o, s_, "relaxed", s["f1"])
def singer(s):
    pos = V((HX - 0.7, 2.3))
    for f in frames(s):
        u = u_of(s, f)
        man_stand(f, pos, 0.0 + 180 - 180 + 0, spine=(-3, 6 * math.sin(f * 0.03), 0), head=(6 + 3 * math.sin(f * 0.07), 10 * math.sin(f * 0.025)))
    for f in frames(s, 2):
        sc.frame_set(f)
        sh = MAN.matrix_world @ MAN.pose.bones["upperarm01.R"].head
        ch = MAN.matrix_world @ MAN.pose.bones["spine03"].head
        hand_at(f, "R", ch + V((0.05, -0.20, 0.10)), V((1, 0, 0.3)), V((0, 1, 0)), 0.0, pole_off=(0.2, -0.3, 0.45))
        shL = MAN.matrix_world @ MAN.pose.bones["upperarm01.L"].head
        lift = 0.18 + 0.06 * math.sin(f * 0.04)
        hand_at(f, "L", shL + V((0.32, -0.25, -0.3 + lift)), V((0.5, -0.6, 0.4)), V((0, 0, 1)), 0.0, pole_off=(0.1, -0.4, 0.5))
    fingers(s["f0"], "R", "flat_palm"); fingers(s["f1"], "R", "flat_palm"); fingers(s["f0"], "L", "relaxed"); fingers(s["f1"], "L", "relaxed")
    # singing: jaw opens and closes softly (no teeth grimace)
    jaw = MAN.pose.bones.get("jaw")
    if jaw:
        for f in frames(s, 6):
            a = 4 + 5 * abs(math.sin(f * 0.11)) * (0.6 + 0.4 * math.sin(f * 0.023))
            RM.key_rot("jaw", f, [("X", a)])
        RM.key_rot("jaw", s["f1"] + 1, [("X", 0)])
def s19(s):
    vis([OB[n] for n in FUN], s["f0"], s["f1"])
    singer(s); audience(s)
shot("S19_Portrait", 170, "B11 the man held a public funeral (painting + flowers)",
     (((HX + 1.2, 0.6, 1.5), (HX + 1.2, 3.2, 1.4)), ((HX + 1.2, 1.3, 1.45), (HX + 1.2, 3.2, 1.4))), s19, 30)
def s20(s): singer(s); audience(s)
shot("S20_Sing", 220, "B11 where he sang a song for his crocodile friend",
     (((HX + 0.25, -2.4, 2.0), (HX + 0.25, 2.5, 1.3)), ((HX + 0.25, -2.0, 1.95), (HX + 0.2, 2.5, 1.3))), s20, 26)
def s21(s): singer(s); audience(s)
shot("S21_HallWide", 170, "B11 (wide: guests, singer, portrait)",
     (((HX + 3.4, 3.4, 2.4), (HX - 0.6, 0.6, 1.0)), ((HX + 3.0, 3.6, 2.35), (HX - 0.7, 0.6, 1.0))), s21, 20)

# ------------------------------------------------------------------ run
for o in [o for o in OB if o.name.startswith("Bench")]: o.hide_render = o.hide_viewport = True
_s16 = [x for x in SHOTS if x["name"].startswith("S16")][0]; _s17 = [x for x in SHOTS if x["name"].startswith("S17")][0]
vis([OB["LogoSign_Board"], OB["LogoSign_Face"]], _s16["f0"], _s17["f1"])
OB["Crate"].location = (-0.2, -8.9, ground_z(-0.2, -8.9))
OB["Crate"].rotation_euler = (0, 0, R_(-15))
EXTRA_ALL = [OB[n] for n in EX]
for o in EXTRA_ALL:
    for ob in [o] + list(o.children):
        ob.hide_render = ob.hide_viewport = True; ob.keyframe_insert("hide_render", frame=1); ob.keyframe_insert("hide_viewport", frame=1)
ONLY = os.environ.get("SHOTS")
for s in SHOTS:
    if ONLY and s["name"].split("_")[0] not in ONLY.split(","): continue
    print("SHOT", s["name"], s["f0"], s["f1"], flush=True)
    s["fn"](s)
sc.frame_start = 1; sc.frame_end = SHOTS[-1]["f1"]
json.dump([{k: v for k, v in s.items() if k != "fn"} for s in SHOTS], open(os.path.join(HERE, "shots.json"), "w"), indent=1)
# night for B6 (S09, S10): key sun + world down and blue
sun = OB["Sun"]; bg = sc.world.node_tree.nodes["Background"]
night = [s for s in SHOTS if s["name"].startswith(("S09", "S10"))]
evening = [s for s in SHOTS if s["name"].startswith("S18")]
moon = bpy.data.objects.new("MoonFill", bpy.data.lights.new("MoonFill", "SUN")); sc.collection.objects.link(moon)
moon.data.color = (0.6, 0.7, 1.0); moon.rotation_euler = (R_(45), 0, R_(200))
def key_light(f, e_sun, col, e_bg, e_moon):
    sun.data.energy = e_sun; sun.data.color = col; bg.inputs[1].default_value = e_bg; moon.data.energy = e_moon
    sun.data.keyframe_insert("energy", frame=f); sun.data.keyframe_insert("color", frame=f)
    bg.inputs[1].keyframe_insert("default_value", frame=f); moon.data.keyframe_insert("energy", frame=f)
key_light(1, 3.5, (1, 0.96, 0.9), 1.0, 0.0)
for s in SHOTS:
    if s in night: key_light(s["f0"], 0.0, (1, 1, 1), 0.22, 3.2); key_light(s["f1"], 0.0, (1, 1, 1), 0.22, 3.2)
    elif s in evening: key_light(s["f0"], 2.6, (1, 0.78, 0.55), 0.7, 0.0); key_light(s["f1"], 2.6, (1, 0.78, 0.55), 0.7, 0.0)
    else: key_light(s["f0"], 3.5, (1, 0.96, 0.9), 1.0, 0.0); key_light(s["f1"], 3.5, (1, 0.96, 0.9), 1.0, 0.0)
for a in bpy.data.actions:
    for fc in getattr(a, "fcurves", []):
        for kp in fc.keyframe_points:
            if fc.data_path.startswith(("hide_", "nodes", "energy", "color")) or 'default_value' in fc.data_path: kp.interpolation = 'CONSTANT'
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("DONE frames", sc.frame_end)
