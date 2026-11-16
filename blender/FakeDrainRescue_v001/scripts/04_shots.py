"""FakeDrainRescue Phase 1: every shot is built from the SHOTS table (provisional windows at the reference pacing).
Each action is written in shot-local time at 1x and runs >= 1.3x its provisional window, so Phase 2 only re-lays the
windows to the VO frames and rebuilds (nothing is time-stretched). One camera per shot, hard cuts by timeline markers.
blender -b work/sets.blend --python 04_shots.py -- work/film.blend [S01,S02]"""
import bpy, sys, math, json, random
from mathutils import Vector, Matrix
P_ = "/home/user/Muhammed/blender/pipeline/"; HERE = "/home/user/Muhammed/blender/FakeDrainRescue_v001/"
exec(open(P_ + "anim_lib.py").read()); exec(open(P_ + "hand_poses.py").read()); exec(open(HERE + "scripts/fdr_lib.py").read())
argv = sys.argv[sys.argv.index("--") + 1:]; out = argv[0]
ONLY = set(argv[1].split(",")) if len(argv) > 1 else None
sc = bpy.context.scene; sc.render.fps = 60; R_ = math.radians; random.seed(3)
SHOTS = json.load(open(HERE + "shots.json"))
SH = {s["id"]: s for s in SHOTS}
sc.frame_start = 1; sc.frame_end = SHOTS[-1]["f1"]
_GZ = [0.0]
def ground_z(x, y): return _GZ[0]
OX = 80.0
# ------------------------------------------------------------------ helpers (after AshaDegree asha_lib)
def Rz(yaw): return Matrix.Rotation(math.radians(yaw), 3, 'Z')
def setup_char(rig):
    R = make_human_ctrl(rig); add_hand_limits(rig)
    for s in "LR":
        lo = rig.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(140)
    H = Human(R); H.rig = rig; B = R.BN
    H.sh = {s: B["upperarm01." + s].head_local.copy() for s in "LR"}
    H.arm = (B["upperarm01.L"].head_local - B["lowerarm01.L"].head_local).length + (B["lowerarm01.L"].head_local - B["wrist.L"].head_local).length
    return H
def body_hand(H, s, f, pos, yaw, off, d, n, pole_off=None):
    Rm = Rz(yaw); W = pos + Rm @ Vector(off)
    if pole_off is None:
        sx = 1 if s == "L" else -1; pole_off = Vector((0.35 * sx, 0.45, off[2] + 0.25))
    H.key_hand(s, f, W, Rm @ Vector(d), Rm @ Vector(n), pole=pos + Rm @ Vector(pole_off))
def hang_off(H, s, fwd=0.0, swing=0.0, bend=0.03):
    sh = H.sh[s] - H.root_head; sx = 1 if s == "L" else -1
    z = sh.z - H.arm * 0.965 + abs(swing) * 0.2
    return (sh.x + (0.03 + 0.05 * max(0.0, -swing) / 0.08) * sx, sh.y - bend - fwd - swing, z)
def key_hang(H, f, pos, yaw, swingL=0.0, swingR=0.0, fwd=0.0, only=("L", "R")):
    for s, sw in (("L", swingL), ("R", swingR)):
        if s not in only: continue
        sx = 1 if s == "L" else -1
        body_hand(H, s, f, pos, yaw, hang_off(H, s, fwd, sw), (0.0, -0.15, -1.0), (-sx, 0.0, 0.0))
def walk(H, p0, p1, yaw, f0, f1, stride=0.9, amp=0.08, head=(0, 0), arms=("L", "R"), **kw):
    p0 = Vector(p0); p1 = Vector(p1)
    path = lambda f: p0.lerp(p1, max(0.0, min(1.0, (f - f0) / max(1, f1 - f0))))
    kw.setdefault("crouch", 0.0); kw.setdefault("lean", 3.0); kw.setdefault("bob", 0.015)
    H.walk(path, lambda f: yaw, f0, f1, stride=stride, step=2, **kw)
    dist = 0.0; prev = path(f0)
    for f in range(f0, f1 + 1, 2):
        p = path(f); dist += (p - prev).to_2d().length; prev = p
        ph = 2 * math.pi * dist / stride
        key_hang(H, f, Vector((p.x, p.y, _GZ[0] + H.root_head.z)), yaw, swingL=-amp * math.sin(ph), swingR=amp * math.sin(ph), only=arms)
        H.key_spine(f, flex=3, head=head)
def stand(H, f, pos, yaw, flex=2.0, head=(0.0, 0.0), twist=0.0, crouch=0.0, side=0.0, arms=True, fwd=0.0):
    p = Vector((pos[0], pos[1], _GZ[0] + H.root_head.z - crouch))
    H.key_root(f, p, yaw=yaw, flex=flex * 0.4, side=side); H.key_spine(f, flex=flex, twist=twist, head=head)
    for s in "LR": H.key_foot(s, f, H.foot_xy(s, Vector((pos[0], pos[1], 0)), yaw), yaw)
    if arms: key_hang(H, f, p, yaw, fwd=fwd)
    return p
def attach(o, rig, bone, f=None):
    if f is not None: sc.frame_set(f)
    bpy.context.view_layer.update(); pb = rig.pose.bones[bone]
    c = o.constraints.new('CHILD_OF'); c.target = rig; c.subtarget = bone
    c.inverse_matrix = (rig.matrix_world @ pb.matrix).inverted(); return c
def poses(rig, f, L="relaxed", R="relaxed"):
    for s, p in (("L", L), ("R", R)):
        if p: apply_pose(rig, s, p, f)
def cam_shot(sid, keys, tkeys, lens=35):
    c = bpy.data.cameras.new("CAM_" + sid); c.lens = lens; c.clip_start = 0.05; c.clip_end = 400; c.dof.use_dof = False; c.sensor_width = 36
    o = bpy.data.objects.new("CAM_" + sid, c); sc.collection.objects.link(o)
    t = bpy.data.objects.new("TGT_" + sid, None); sc.collection.objects.link(t)
    f0, f1 = SH[sid]["f0"], SH[sid]["f1"]
    for u, p in keys: o.location = p; o.keyframe_insert("location", frame=round(f0 + u * (f1 - f0)))
    for u, p in tkeys: t.location = p; t.keyframe_insert("location", frame=round(f0 + u * (f1 - f0)))
    tr = o.constraints.new('TRACK_TO'); tr.target = t; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
    m = sc.timeline_markers.new(sid, frame=f0); m.camera = o; return o
CH = {n: bpy.data.objects[n] for n in ("Mom", "Kid", "CopA", "CopB", "ResA", "ResB", "Clerk")}
HS = {}
for n, rig in CH.items(): HS[n] = setup_char(rig)
VIS = {n: [] for n in CH}
def use(n, sid): VIS[n].append((SH[sid]["f0"], SH[sid]["f1"]))
def W(sid): return SH[sid]["f0"], SH[sid]["f1"]
def T(sid, u): f0, f1 = W(sid); return round(f0 + u * (f1 - f0))
def blinkless(): pass
# ------------------------------------------------------------------ props
torch = bpy.data.objects["small_plastic_torch"]; phone = bpy.data.objects["Phone"]; scr = bpy.data.objects["Phone_Screen"]
# phone screen sits on the phone front face (phone thin axis = x)
bpy.context.view_layer.update()
scr.parent = phone; scr.matrix_parent_inverse = Matrix.Identity(4)
scr.matrix_basis = Matrix(((0, 0, -1, -0.0052), (-1, 0, 0, 0), (0, 1, 0, 0.075), (0, 0, 0, 1)))
# torch light
tl = bpy.data.lights.new("TorchBeam", 'SPOT'); tl.energy = 60; tl.spot_size = R_(35); tl.color = (1, 0.95, 0.8); tl.shadow_soft_size = 0.02
tlo = bpy.data.objects.new("TorchBeam", tl); sc.collection.objects.link(tlo)
SHOT_FUNCS = {}
def shot(sid):
    def deco(fn): SHOT_FUNCS[sid] = fn; return fn
    return deco
def D(sid): f0, f1 = W(sid); return int(1.3 * (f1 - f0 + 1))
def trim(names, f1):
    """drop keys past the shot window (actions run 1.3x long; the cut trims them, nothing is stretched)"""
    for n in names:
        for idb in (CH[n],):
            for fc in fcurves_of(idb):
                for kp in [k for k in fc.keyframe_points if k.co.x > f1 + 0.5][::-1]: fc.keyframe_points.remove(kp)
def fcurves_of(idb):
    ad = getattr(idb, "animation_data", None)
    if not ad or not ad.action: return []
    act = ad.action; out = []
    try: out = list(act.fcurves)
    except Exception: out = []
    if not out:
        for layer in getattr(act, "layers", []):
            for strip in layer.strips:
                for cb in getattr(strip, "channelbags", []): out += list(cb.fcurves)
    return out
DRAIN_TOP = 0.0; DRAIN_FLOOR = -1.9
# ================================================================== shots
@shot("S01")
def _():
    f0, f1 = W("S01"); d = D("S01"); _GZ[0] = 0.0
    walk(HS["Mom"], (2.7, 12.6, 0), (2.7, 12.6 - 1.15 * d / 60, 0), 0, f0, f0 + d, stride=1.25, head=(4, 8))
    walk(HS["Kid"], (2.1, 11.2, 0), (2.1, 11.2 - 1.15 * d / 60, 0), 0, f0, f0 + d, stride=0.62, amp=0.06, head=(0, -10))
    for n in ("Mom", "Kid"): poses(CH[n], f0); use(n, "S01")
    cam_shot("S01", [(0, (0.5, 7.4, 2.5)), (1, (0.6, 6.9, 2.4))], [(0, (2.4, 11.4, 0.6)), (1, (2.4, 10.6, 0.6))], lens=30)
@shot("S02")
def _():
    f0, f1 = W("S02"); d = D("S02"); _GZ[0] = 0.0; H = HS["Mom"]; rig = CH["Mom"]
    pos = Vector((2.05, 8.6, 0)); yaw = -90
    for t, flex, pt in ((0, 6, 0.0), (0.35, 18, 1.0), (1.3, 20, 1.0)):
        f = f0 + round(t * (f1 - f0)); p = stand(H, f, pos, yaw, flex=flex, head=(6, 0), arms=False)
        sh = H.sh["R"] - H.root_head
        body_hand(H, "R", f, p, yaw, (sh.x - 0.03, sh.y - 0.25 - 0.32 * pt, sh.z - 0.5 + 0.12 * pt), (0.0, -0.75, -0.65), (0.9, 0.0, -0.3))
        key_hang(H, f, p, yaw, fwd=0.05, only=("L",))
    apply_pose(rig, "R", "point", f0 + round(0.35 * (f1 - f0))); apply_pose(rig, "R", "relaxed", f0); apply_pose(rig, "L", "relaxed", f0)
    use("Mom", "S02")
    cam_shot("S02", [(0, (-0.6, 6.9, 0.55)), (1, (-0.45, 7.4, 0.45))], [(0, (1.6, 8.6, 0.7)), (1, (1.6, 8.6, 0.75))], lens=28)
@shot("S03")
def _():
    f0, f1 = W("S03"); _GZ[0] = 0.0; H = HS["Mom"]
    for t, y in ((0, 8.6), (1.3, 8.9)):
        stand(H, f0 + round(t * (f1 - f0)), (2.15 + 0.25 * t, y, 0), -90 + 20 * t, flex=4, head=(10, 0))
    poses(CH["Mom"], f0); use("Mom", "S03")
    cam_shot("S03", [(0, (0.0, 2.2, 9.5)), (1, (0.1, 3.0, 10.5))], [(0, (0.4, 9.0, -0.7)), (1, (0.4, 9.6, -0.7))], lens=30)
@shot("S04")
def _():
    f0, f1 = W("S04"); _GZ[0] = 0.0; H = HS["Mom"]; rig = CH["Mom"]
    pos = Vector((2.7, 5.0, 0)); yaw = 110
    for i, t in enumerate((0, 0.25, 0.5, 0.75, 1.0, 1.3)):
        f = f0 + round(t * (f1 - f0)); a = 1 if i % 2 else 0
        p = stand(H, f, pos, yaw, flex=5 + 4 * a, head=(4 - 8 * a, -14 + 22 * a), arms=False, twist=-8 + 14 * a)
        for s in "LR":
            sx = 1 if s == "L" else -1; sh = H.sh[s] - H.root_head
            body_hand(H, s, f, p, yaw, (sh.x - sx * 0.1, sh.y - 0.32 - 0.06 * a, sh.z - 0.24 + 0.05 * a), (-sx * 0.35, -0.85, 0.35), (-sx * 0.25, -0.3, 0.9))
    poses(rig, f0, "relaxed", "relaxed"); use("Mom", "S04")
    cam_shot("S04", [(0, (4.45, 5.95, 1.45)), (1, (3.75, 5.35, 1.55))], [(0, (2.7, 5.0, 1.32)), (1, (2.7, 5.0, 1.45))], lens=40)
@shot("S05")
def _():
    f0, f1 = W("S05"); _GZ[0] = 0.0
    H = HS["Mom"]; pos = Vector((2.55, 5.05, 0))
    for i, t in enumerate((0, 0.3, 0.6, 0.9, 1.3)):
        f = f0 + round(t * (f1 - f0)); a = i % 2; yw = 100 - 30 * a
        p = stand(H, f, pos, yw, flex=4, head=(0, 0), arms=False, twist=-10 * a)
        sh = H.sh["L"] - H.root_head
        body_hand(H, "L", f, p, yw, (sh.x + 0.05 - 0.12 * a, sh.y - 0.32, sh.z - 0.28 + 0.06 * a), (0.2, -0.85, 0.3), (0.3, -0.2, 0.9))
        key_hang(H, f, p, yw, only=("R",))
    for n, pp, yw, nod in (("CopA", (3.45, 5.75), -52, 1), ("CopB", (3.5, 4.25), -128, 0)):
        Hc = HS[n]
        for i, t in enumerate((0, 0.3, 0.6, 0.9, 1.3)):
            f = f0 + round(t * (f1 - f0))
            stand(Hc, f, pp, yw, flex=2, head=(8 * nod * (i % 2), 0 if nod else -20 * (i % 2)))
        poses(CH[n], f0); use(n, "S05")
    poses(CH["Mom"], f0); use("Mom", "S05")
    cam_shot("S05", [(0, (5.6, 3.2, 1.7)), (1, (5.1, 3.6, 1.62))], [(0, (3.0, 5.0, 1.3)), (1, (3.0, 5.05, 1.32))], lens=30)
def wade(n, sid, p0, p1, yaw, sweep=True):
    f0, f1 = W(sid); d = D(sid); _GZ[0] = DRAIN_FLOOR; H = HS[n]
    p0 = Vector(p0); p1 = Vector(p1)
    path = lambda f: p0.lerp(p1, max(0.0, min(1.0, (f - f0) / d)))
    H.walk(path, lambda f: yaw, f0, f0 + d, stride=0.7, step=2, crouch=0.04, lean=8, bob=0.01)
    for f in range(f0, f0 + d + 1, 4):
        p = path(f); u = (f - f0) / 60.0; ph = 2 * math.pi * u / 1.6
        pos = Vector((p.x, p.y, DRAIN_FLOOR + H.root_head.z))
        for s in "LR":
            sx = 1 if s == "L" else -1; sh = H.sh[s] - H.root_head
            zw = -0.75 - pos.z + 0.04   # just above the water surface
            sw = 0.16 * math.sin(ph + (0 if s == "L" else math.pi)) if sweep else 0
            body_hand(H, s, f, pos, yaw, (sh.x + sx * 0.05 + sw, sh.y - 0.42, zw), (sx * 0.2, -0.9, -0.25), (0, 0, -1))
        H.key_spine(f, flex=10, head=(14, 12 * math.sin(ph * 0.5)))
    poses(CH[n], f0, "relaxed", "relaxed"); use(n, sid)
@shot("S06")
def _():
    wade("ResA", "S06", (-0.35, 17.0, 0), (-0.35, 18.6, 0), 180); wade("ResB", "S06", (0.55, 23.4, 0), (0.55, 24.9, 0), 180)
    cam_shot("S06", [(0, (1.1, 27.6, 1.7)), (1, (1.0, 27.0, 1.55))], [(0, (0.0, 21.4, -0.8)), (1, (0.0, 21.0, -0.8))], lens=30)
@shot("S07")
def _():
    wade("ResA", "S07", (-0.35, 19.0, 0), (-0.35, 20.3, 0), 180)
    cam_shot("S07", [(0, (0.55, 22.8, -0.05)), (1, (0.45, 22.4, -0.08))], [(0, (-0.35, 19.6, -0.55)), (1, (-0.35, 20.0, -0.5))], lens=32)
def torch_hold(n, sid, pos, yaw, aim_dz=-0.25, turn=None):
    """torch in the right fist, beam forward-down; the left hand hangs. aim_dz: beam end height"""
    f0, f1 = W(sid); _GZ[0] = DRAIN_FLOOR; H = HS[n]; rig = CH[n]
    for t in (0, 0.5, 1.0, 1.3):
        f = f0 + round(t * (f1 - f0)); yw = yaw + (turn or 0) * (math.sin(t * 3.0))
        p = stand(H, f, pos, yw, flex=8, head=(10, 0), arms=False)
        sh = H.sh["R"] - H.root_head
        body_hand(H, "R", f, p, yw, (sh.x + 0.02, sh.y - 0.40, sh.z - 0.32), (0.0, -0.3, -0.95), (0.95, 0, 0))
        key_hang(H, f, p, yw, only=("L",), fwd=0.04)
    poses(rig, f0, "relaxed", None); use(n, sid)
@shot("S08")
def _():
    torch_hold("ResA", "S08", (0.0, -12.55, 0), 0, turn=12)
    cam_shot("S08", [(0, (1.4, -13.0, 0.05)), (1, (1.15, -13.55, -0.2))], [(0, (-0.05, -12.45, -0.45)), (1, (-0.05, -12.5, -0.5))], lens=30)
@shot("S09")
def _():
    torch_hold("ResA", "S09", (-0.4, -12.75, 0), 0, turn=6)
    cam_shot("S09", [(0, (0.55, -11.7, -0.15)), (1, (0.4, -12.6, -0.3))], [(0, (-0.15, -15.8, -0.8)), (1, (-0.15, -15.9, -0.8))], lens=35)
@shot("S10")
def _():
    f0, f1 = W("S10"); _GZ[0] = DRAIN_FLOOR; H = HS["ResA"]; pos = Vector((0.0, -12.4, 0))
    for i, t in enumerate((0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.3)):
        f = f0 + round(t * (f1 - f0)); sh = 0 if i in (0, 6) else (-26 if i % 2 else 26)
        stand(HS["ResA"], f, pos, 180, flex=4, head=(-4, sh))
    poses(CH["ResA"], f0, "relaxed", None); use("ResA", "S10")
    cam_shot("S10", [(0, (0.6, -10.8, -0.05)), (1, (0.3, -11.35, -0.18))], [(0, (0.0, -12.4, -0.3)), (1, (0.0, -12.4, -0.28))], lens=45)
def edge_stand(n, sid, pos, yaw, look=18, shift=0.0):
    f0, f1 = W(sid); _GZ[0] = 0.0; H = HS[n]
    for i, t in enumerate((0, 0.45, 0.9, 1.3)):
        stand(H, f0 + round(t * (f1 - f0)), (pos[0], pos[1] + shift * t), yaw + 8 * (i % 2), flex=6, head=(look, 10 * (i % 2)))
    poses(CH[n], f0); use(n, sid)
@shot("S11")
def _():
    edge_stand("ResA", "S11", (1.95, 7.0), -90); edge_stand("ResB", "S11", (1.95, 10.2), -100)
    cam_shot("S11", [(0, (-1.0, 4.2, 2.6)), (1, (-0.8, 4.9, 2.9))], [(0, (1.5, 8.8, 0.3)), (1, (1.5, 9.0, 0.2))], lens=28)
@shot("S12")
def _():
    f0, f1 = W("S12"); d = D("S12"); _GZ[0] = 0.0
    walk(HS["Mom"], (2.3, 14.2, 0), (2.3, 14.2 - 0.9 * d / 60, 0), 0, f0, f0 + d, stride=1.1, head=(12, -25))
    poses(CH["Mom"], f0); use("Mom", "S12")
    cam_shot("S12", [(0, (1.15, 9.8, 1.35)), (1, (1.2, 9.2, 1.3))], [(0, (2.3, 13.3, 1.1)), (1, (2.3, 12.6, 1.1))], lens=38)
@shot("S13")
def _():
    f0, f1 = W("S13"); _GZ[0] = 0.0; H = HS["Mom"]
    for i, t in enumerate((0, 0.25, 0.5, 0.75, 1.0, 1.3)):
        stand(H, f0 + round(t * (f1 - f0)), (2.3, 11.8), -20, flex=3, head=(10, -10 + (22 if i % 2 else -16)), twist=(8 if i % 2 else -6))
    poses(CH["Mom"], f0); use("Mom", "S13")
    cam_shot("S13", [(0, (1.75, 10.6, 1.0)), (1, (2.1, 10.95, 1.12))], [(0, (2.3, 11.8, 1.5)), (1, (2.3, 11.8, 1.5))], lens=40)
@shot("S14")
def _():
    cam_shot("S14", [(0, (0.5, -9.8, 0.6)), (1, (0.3, -10.9, 0.25))], [(0, (0.0, -13.6, -0.85)), (1, (0.0, -13.7, -0.9))], lens=30)
def sit(n, sid, pos, yaw, desk_z=0.79, lean=(0, 0), heads=((0, 0),)):
    f0, f1 = W(sid); _GZ[0] = 0.0; H = HS[n]; rig = CH[n]
    seat = 0.46
    for i, t in enumerate((0, 0.3, 0.6, 0.9, 1.3)):
        f = f0 + round(t * (f1 - f0)); hd = heads[i % len(heads)]
        Rm = Rz(yaw); hip = Vector((pos[0], pos[1], seat + 0.10)) + Rm @ Vector((0, 0.05, 0))
        H.key_root(f, hip, yaw=yaw, flex=-75 + lean[i % len(lean)] if False else 0, side=0)
        rig.pose.bones["root"]
        H.key_spine(f, flex=24 + lean[i % 2], head=(hd[0] - 12, hd[1]))
        for s in "LR":
            sx = 1 if s == "L" else -1
            H.key_foot(s, f, Vector((pos[0], pos[1])) + (Rm @ Vector((sx * 0.14, -0.42, 0))).to_2d(), yaw)
        for s in "LR":
            sx = 1 if s == "L" else -1
            Wd = Vector((pos[0], pos[1], desk_z + 0.035)) + Rm @ Vector((sx * 0.22, -0.66, 0))
            H.key_hand(s, f, Wd, Rm @ Vector((-sx * 0.25, -1, 0)), Vector((0, 0, -1)), pole=Vector((pos[0], pos[1], 0.6)) + Rm @ Vector((sx * 0.6, 0.2, 0)))
    poses(rig, f0, "flat_palm", "flat_palm"); use(n, sid)
@shot("S15")
def _():
    sit("Clerk", "S15", (OX, 2.45), 0, heads=((4, 0), (2, 18), (6, 0), (2, -14)))
    cam_shot("S15", [(0, (OX + 1.0, -0.3, 1.6)), (1, (OX + 0.6, 0.15, 1.5))], [(0, (OX, 1.9, 1.0)), (1, (OX, 1.95, 1.05))], lens=30)
@shot("S16")
def _():
    sit("Clerk", "S16", (OX, 2.45), 0, heads=((14, -10), (10, 15)))
    cam_shot("S16", [(0, (OX - 0.7, 0.6, 1.75)), (1, (OX - 0.55, 0.8, 1.45))], [(0, (OX - 0.35, 1.45, 0.8)), (1, (OX - 0.35, 1.45, 0.82))], lens=30)
@shot("S17")
def _():
    cam_shot("S17", [(0, (1.45, -10.2, 2.3)), (1, (1.35, -10.9, 2.0))], [(0, (0.0, -13.2, -0.75)), (1, (0.0, -13.3, -0.75))], lens=30)
@shot("S18")
def _():
    f0, f1 = W("S18"); _GZ[0] = 0.0; H = HS["Mom"]
    for i, (t, hd, fl) in enumerate(((0, (14, -10), 6), (0.35, (12, -10), 6), (0.6, (-6, 4), 0), (1.0, (-4, 8), -1), (1.3, (-4, 8), -1))):
        stand(H, f0 + round(t * (f1 - f0)), (2.7, 5.0), 105, flex=fl, head=hd)
    poses(CH["Mom"], f0); use("Mom", "S18")
    cam_shot("S18", [(0, (3.85, 5.35, 1.5)), (1, (3.7, 5.28, 1.52))], [(0, (2.7, 5.0, 1.45)), (1, (2.7, 5.0, 1.48))], lens=45)
def phone_shot(sid, yaw, heads, ear=False):
    f0, f1 = W(sid); _GZ[0] = 0.0; H = HS["Mom"]; rig = CH["Mom"]; pos = Vector((2.7, 5.0, 0))
    for i, t in enumerate((0, 0.3, 0.6, 0.9, 1.3)):
        f = f0 + round(t * (f1 - f0)); p = stand(H, f, pos, yaw, flex=4, head=heads[i % len(heads)], arms=False)
        sh = H.sh["R"] - H.root_head
        body_hand(H, "R", f, p, yaw, (sh.x + 0.10, sh.y - 0.30, sh.z - 0.17), (0.45, -0.35, 0.82), (0.0, 0.9, 0.35))
        key_hang(H, f, p, yaw, only=("L",))
    apply_pose(rig, "R", "hold_flat_object", f0); apply_pose(rig, "L", "relaxed", f0); use("Mom", sid)
    return f0
@shot("S19")
def _():
    phone_shot("S19", 80, ((24, 0), (26, 3)))
    cam_shot("S19", [(0, (3.5, 4.7, 1.5)), (1, (3.45, 4.75, 1.47))], [(0, (3.0, 5.05, 1.3)), (1, (3.0, 5.05, 1.3))], lens=40)
@shot("S20")
def _():
    phone_shot("S20", 80, ((20, 0), (16, 4), (20, -3)))
    cam_shot("S20", [(0, (4.15, 4.75, 1.5)), (1, (4.0, 4.8, 1.48))], [(0, (2.75, 5.0, 1.3)), (1, (2.75, 5.0, 1.3))], lens=38)
@shot("S21")
def _():
    phone_shot("S21", 80, ((18, 0), (6, -35), (6, -40)))
    cam_shot("S21", [(0, (3.6, 3.2, 1.55)), (1, (3.5, 3.4, 1.5))], [(0, (2.6, 5.0, 1.3)), (1, (2.6, 5.0, 1.3))], lens=35)
@shot("S22")
def _():
    f0, f1 = W("S22"); d = D("S22"); _GZ[0] = 0.0
    walk(HS["ResB"], (3.75, 15.5, 0), (3.75, 15.5 - 1.0 * d / 60, 0), 0, f0, f0 + d, stride=1.1, head=(6, 0))
    poses(CH["ResB"], f0); use("ResB", "S22")
    edge_stand("ResA", "S22", (1.95, 9.0), -95, shift=0.0)
    cam_shot("S22", [(0, (4.15, 9.4, 1.6)), (1, (4.1, 8.9, 1.5))], [(0, (3.6, 14.2, 1.0)), (1, (3.6, 13.3, 1.0))], lens=32)
@shot("S23")
def _():
    cam_shot("S23", [(0, (2.2, 21.6, 1.6)), (1, (2.9, 22.7, 1.85))], [(0, (7.0, 24.2, 1.6)), (1, (7.0, 24.4, 1.6))], lens=30)
@shot("S24")
def _():
    edge_stand("ResA", "S24", (1.95, 6.5), -90); edge_stand("ResB", "S24", (-1.95, 8.5), 90)
    cam_shot("S24", [(0, (-0.9, -3.0, 3.4)), (1, (-0.7, -2.0, 3.2))], [(0, (0.5, 8.0, -0.8)), (1, (0.5, 8.4, -0.8))], lens=30)
@shot("S25")
def _():
    cam_shot("S25", [(0, (0.3, 10.0, 7.0)), (1, (0.3, 10.0, 15.0))], [(0, (0.31, 10.4, -1.4)), (1, (0.31, 10.4, -1.4))], lens=28)
# ------------------------------------------------------------------ build
for s in SHOTS:
    if ONLY and s["id"] not in ONLY: continue
    used_before = {n: len(v) for n, v in VIS.items()}
    SHOT_FUNCS[s["id"]]()
    trim([n for n in CH if len(VIS[n]) > used_before[n]], s["f1"])
    print("SHOT", s["id"], s["f0"], s["f1"], [n for n in CH if len(VIS[n]) > used_before[n]])
# ------------------------------------------------------------------ props in hands
def hand_frame(rig, s):
    Mw = rig.matrix_world; PB = rig.pose.bones
    wr = Mw @ PB["wrist." + s].head; m3 = Mw @ PB["finger3-1." + s].head
    i2 = Mw @ PB["finger2-1." + s].head; p5 = Mw @ PB["finger5-1." + s].head
    d = (m3 - wr).normalized(); a = (i2 - p5).normalized()
    n = d.cross(a) if s == "L" else a.cross(d)
    BN = rig.data.bones; dr = BN["finger3-1." + s].head_local - BN["wrist." + s].head_local; ar = BN["finger2-1." + s].head_local - BN["finger5-1." + s].head_local
    nr = dr.cross(ar) if s == "L" else ar.cross(dr)
    n = n.normalized() * _rest_palm_sign(rig, s, nr)
    return wr, d, a, n, wr.lerp(m3, 0.6)
def frame_matrix(xax, yax, zax, loc):
    M = Matrix((xax, yax, zax)).transposed().to_4x4(); M.translation = loc; return M
PHONE_SHOTS = [s for s in ("S19", "S20", "S21") if (not ONLY or s in ONLY)]
if PHONE_SHOTS:
    f0 = SH[PHONE_SHOTS[0]]["f0"]; sc.frame_set(f0); rig = CH["Mom"]
    wr, d, a, n, palm = hand_frame(rig, "R")
    zax = d; xax = (-n - d * (-n).dot(d)).normalized(); yax = zax.cross(xax)
    phone.matrix_world = frame_matrix(xax, yax, zax, palm + n * 0.034 - d * 0.01)
    attach(phone, rig, "wrist.R", f0)
    key_vis([phone, scr], [W(s) for s in PHONE_SHOTS])
    if "S19" in PHONE_SHOTS:
        cam = bpy.data.objects["CAM_S19"]; tg = bpy.data.objects["TGT_S19"]; cam.animation_data_clear(); tg.animation_data_clear()
        for u in (0.0, 1.0):
            f = T("S19", u); sc.frame_set(f); M = phone.matrix_world; P = M @ Vector((0, 0, 0.075)); nS = (M.to_3x3() @ Vector((-1, 0, 0))).normalized()
            up = (M.to_3x3() @ Vector((0, 0, 1))).normalized(); side = nS.cross(up).normalized()
            cam.location = P + nS * (0.42 - 0.05 * u) + side * 0.12 + up * 0.05; cam.keyframe_insert("location", frame=f)
            tg.location = P; tg.keyframe_insert("location", frame=f)
            print("S19 cam", tuple(round(x, 2) for x in cam.location), "phone", tuple(round(x, 2) for x in P))
else:
    key_vis([phone, scr], [])
TORCH_SHOTS = [s for s in ("S08", "S09") if (not ONLY or s in ONLY)]
bpy.context.view_layer.update()
tv = [Vector(v.co) for v in torch.data.vertices]
ylo = [v for v in tv if v.y < min(p.y for p in tv) + 0.03]; yhi = [v for v in tv if v.y > max(p.y for p in tv) - 0.03]
head_dir = 1 if max(abs(v.x) for v in yhi) > max(abs(v.x) for v in ylo) else -1
print("TORCH head toward local", "+Y" if head_dir > 0 else "-Y")
key_vis([torch], [])
if TORCH_SHOTS:
    f0 = SH[TORCH_SHOTS[0]]["f0"]; sc.frame_set(f0); rig = CH["ResA"]
    wr, d, a, n, palm = hand_frame(rig, "R")
    fwd = Rz(0) @ Vector((0, -1, -0.35))   # he faces -Y into the pipe: beam forward and down
    zax = (-fwd).normalized(); xax = Vector((1, 0, 0)); yax = zax.cross(xax)
    tlo.matrix_world = frame_matrix(xax, yax, zax, palm + n * 0.04)
    attach(tlo, rig, "wrist.R", f0)
    apply_pose(rig, "R", "power_fist", f0)
    key_vis([tlo], [W(s) for s in TORCH_SHOTS])
else:
    key_vis([tlo], [])
# ------------------------------------------------------------------ set states
def rng(state): return [(s["f0"], s["f1"]) for s in SHOTS if s["state"] == state]
key_vis([o.name for o in bpy.data.collections["TrashDirty"].objects] + ["Water_Murky"], rng("drain"))
key_vis([o.name for o in bpy.data.collections["TrashClean"].objects] + ["Water_Clean"], rng("clean"))
for n, rr in VIS.items():
    rig = CH[n]; names = [c.name for c in rig.children_recursive] + [rig.name]
    names += [o.name for o in bpy.data.objects if any(c.type == 'CHILD_OF' and c.target == rig for c in o.constraints) and o not in (phone, torch)]
    key_vis(names, rr)
# clog (S14, S17): trash jammed at the culvert mouth; drift (S17): items floating out of the pipe
bag_ph = bpy.data.objects["trashbag"]; bot = bpy.data.objects["Lib_Bottle"]; can = bpy.data.meshes["Lib_Can"]
bag_mats = [m for m in bpy.data.materials if m.name.startswith("Bag_")]
clog = []
random.seed(11)
for i in range(34):
    x = random.uniform(-0.75, 0.75); y = random.uniform(-14.3, -11.8) if i < 26 else random.uniform(-15.5, -14.3)
    if y < -14.0 and math.hypot(x, 0) > 0.55: x *= 0.6
    k = random.choice(["bag", "bag", "bottle", "can"])
    src = {"bag": bag_ph.data, "bottle": bot.data, "can": can}[k]
    o = bpy.data.objects.new("Clog_%d" % i, src); coll("TrashClog").objects.link(o)
    o.location = (x, y, -0.75 - (0.3 if k == "bag" else 0.02)); o.rotation_euler = (R_(90) if k != "bag" else random.uniform(-0.3, 0.3), 0, random.uniform(0, 6.28))
    if k == "bag": o.material_slots[0].link = 'OBJECT'; o.material_slots[0].material = random.choice(bag_mats)
    if k == "can": o.material_slots[0].link = 'OBJECT'; o.material_slots[0].material = bpy.data.materials["Can_%d" % random.randint(0, 3)]
    clog.append(o.name)
clog_rng = [W(s) for s in ("S14", "S17") if s in SH]
key_vis([c for c in clog], clog_rng)
for c in clog:
    if bpy.data.objects[c].location.y < -14.3: key_vis([c], clog_rng + [W("S09")])
f0, f1 = W("S17"); drift = []
for i in range(7):
    k = ["bag", "bottle", "bag", "can", "bottle", "bag", "bottle"][i]
    src = {"bag": bag_ph.data, "bottle": bot.data, "can": can}[k]
    o = bpy.data.objects.new("Drift_%d" % i, src); coll("TrashDrift").objects.link(o)
    if k == "bag": o.material_slots[0].link = 'OBJECT'; o.material_slots[0].material = bag_mats[i % len(bag_mats)]
    x = [-0.35, 0.25, 0.4, -0.1, -0.45, 0.05, 0.3][i]; z = -0.75 - (0.3 if k == "bag" else 0.02)
    st = f0 - 40 + i * 18
    for f, y in ((st, -17.5), (st + 260, -11.6)):
        o.location = (x, y, z); o.rotation_euler = (R_(90) if k != "bag" else 0, 0, i + (f - st) * 0.004); o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
    for fc in fcurves_of(o):
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
        if fc.data_path == "location" and fc.array_index == 2:
            nm = fc.modifiers.new('NOISE'); nm.scale = 30; nm.strength = 0.03; nm.phase = i * 3
    drift.append(o.name)
key_vis(drift, [W("S17")])
# forms pile on the desk (office)
FORMM = [img_mat("FormM%d" % k, HERE + "assets/tex/form_%d.png" % k, 0.6) for k in range(3)]
random.seed(5)
for i in range(42):
    p = plane("Form_%d" % i, 0.21, 0.297, (OX - 0.42 + random.uniform(-0.03, 0.03), 1.33 + random.uniform(-0.03, 0.03), 0.792 + i * 0.0016), FORMM[i % 3], "Office", rot=(0, 0, R_(random.uniform(-12, 12))))
for i in range(5):
    plane("FormLoose_%d" % i, 0.21, 0.297, (OX + 0.15 + i * 0.12, 1.25 + random.uniform(-0.05, 0.08), 0.792 + i * 0.0015), FORMM[i % 3], "Office", rot=(0, 0, R_(random.uniform(-25, 25))))
# ------------------------------------------------------------------ truck logo + slow drive in S25
truck = bpy.data.objects["Truck"]; truck.scale = (0.8, 0.8, 0.8); truck.location = (8.0, 24.0, -0.1); bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
best = None
for yy in [24 + k * 0.25 for k in range(-12, 13)]:
    hit, loc, nrm, idx, ob, _ = sc.ray_cast(dg, Vector((5.0, yy, 2.0)), Vector((1, 0, 0)))
    if hit and ob == truck: best = (yy, loc.x) if best is None or loc.x < best[1] - 0.01 or (abs(loc.x - best[1]) < 0.01 and abs(yy - 24) < abs(best[0] - 24)) else best
print("TRUCK side hit", best)
# flat side panel of the refuse box: x 7.06, y 23.9-25.6, z 1.0-2.6 (ray-sampled)
logo = plane("Logo_Truck", 1.6, 1.6 * 414 / 967, (7.046, 24.75, 1.95), img_mat("LogoWhite", "/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_white.png", 0.4, alpha=True), "Truck", rot=(R_(90), 0, R_(-90)))
logo.parent = truck; logo.matrix_parent_inverse = truck.matrix_world.inverted()
f0, f1 = W("S25")
truck.keyframe_insert("location", frame=f0)
truck.location = (8.0, 24.0 + 9.0 * (f1 - f0) / 60.0 * 0.5, -0.1); truck.keyframe_insert("location", frame=f1)
for fc in fcurves_of(truck):
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
key_vis(["Truck", "Logo_Truck"], rng("clean"))
# ------------------------------------------------------------------ world, lights, render
w = bpy.data.worlds.get("FDR_World") or bpy.data.worlds.new("FDR_World"); sc.world = w; w.use_nodes = True; nt = w.node_tree
for nd in list(nt.nodes): nt.nodes.remove(nd)
env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(HERE + "work/ph/hdri/kloofendal_48d_partly_cloudy_puresky_1k.hdr"); env.image.pack()
bg = nt.nodes.new("ShaderNodeBackground"); bg.inputs[1].default_value = 1.0; o_ = nt.nodes.new("ShaderNodeOutputWorld")
nt.links.new(env.outputs[0], bg.inputs[0]); nt.links.new(bg.outputs[0], o_.inputs[0])
sun = bpy.data.lights.new("Sun", 'SUN'); sun.energy = 3.2; sun.angle = R_(3); so = bpy.data.objects.new("Sun", sun); sc.collection.objects.link(so)
so.rotation_euler = (R_(42), R_(8), R_(130))
for nm, loc, e, size in (("Off_Light1", (OX - 1.0, 0.8, 2.9), 220, 1.6), ("Off_Light2", (OX + 1.0, 0.2, 2.9), 160, 1.6)):
    l = bpy.data.lights.new(nm, 'AREA'); l.energy = e; l.size = size; lo = bpy.data.objects.new(nm, l); sc.collection.objects.link(lo); lo.location = loc
l = bpy.data.lights.new("Pipe_Fill", 'AREA'); l.energy = 40; l.size = 0.8; lo = bpy.data.objects.new("Pipe_Fill", l); sc.collection.objects.link(lo)
lo.location = (0.0, -15.5, -0.3); lo.rotation_euler = (R_(-90), 0, 0)
key_vis(["Pipe_Fill"], [W("S09")])
# catchlights: a small emitter beside each close camera, seen only in glossy reflections (eyes)
CL = mat("Catchlight", (1, 1, 1), 0.5, emit=((1, 1, 1), 6.0))
for s in SHOTS:
    cam = bpy.data.objects.get("CAM_" + s["id"])
    if not cam: continue
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.015, location=(0, 0, 0)); c = bpy.context.object; c.name = "Catch_" + s["id"]
    c.data.materials.append(CL); c.parent = cam; c.location = (0.12, 0.10, 0); c.visible_camera = False; c.visible_diffuse = False
    c.visible_transmission = False; c.visible_volume_scatter = False; c.visible_shadow = False
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.render.resolution_x = 1080; sc.render.resolution_y = 1920; sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'; sc.render.use_motion_blur = False
sc.cycles.max_bounces = 6; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.camera = bpy.data.objects.get("CAM_S01") or next(o for o in bpy.data.objects if o.type == 'CAMERA')
for o in bpy.data.objects:
    if o.type == 'ARMATURE': o.location = (0, 0, 0)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("SAVED", out)
