"""LakeSword: every shot as its own clip (character keys, props, camera + marker = hard cut).
blender -b sets.blend --python 03_shots.py -- <out.blend> [shots.json]
shots.json (optional, Phase 2): {"01": [f0, len], ...}. Default = provisional contiguous layout (SHOTS below).
Each shot function gets (f0, n) and keys its action at 1x from f0; a shot shorter than its clip is trimmed, never stretched."""
import sys, os, math, json
import bpy
from mathutils import Vector, Matrix, Quaternion
from mathutils.noise import noise
V = Vector; R_ = math.radians
HERE = os.path.dirname(os.path.abspath(__file__)); PIPE = os.path.join(HERE, "..", "..", "pipeline")
exec(open(os.path.join(PIPE, "anim_lib.py")).read())
exec(open(os.path.join(PIPE, "hand_poses.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]
sc = bpy.context.scene
def ss(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

# ---- ground heights (same functions as 02_sets.py)
def lake_h(x, y):
    z = -0.25 + 0.45 * ss((y - 2.5) / 3.5) + 0.05 * max(0.0, y - 6.0) ** 1.1
    z += 0.35 * ss((-y - 45.0) / 8.0) + 0.03 * max(0.0, -y - 53.0)
    return z + 0.025 * noise(V((x * 0.6, y * 0.6, 0.0))) + 0.008 * noise(V((x * 3.1, y * 3.1, 1.0)))
def camp_h(x, y):
    z = -0.4 + 0.5 * ss((y + 1.0) / 3.0) + 0.04 * max(0.0, y - 2.0) ** 1.1
    z += 0.35 * ss((-y - 45.0) / 8.0) + 0.03 * max(0.0, -y - 53.0)
    return z + 0.03 * noise(V((x * 0.5, y * 0.5, 2.0))) + 0.01 * noise(V((x * 2.7, y * 2.7, 3.0)))
def ground_z(x, y):
    if x < 50: return lake_h(x, y)
    if x > 250: return camp_h(x - 300, y)
    return 0.0
GZ = [0.0]

CH = ("Girl", "Dad", "ExpM", "ExpF", "Warrior", "Comp")
RIG = {n: make_human_ctrl(bpy.data.objects[n]) for n in CH}; HUM = {n: Human(RIG[n]) for n in CH}
for n in CH:
    o = bpy.data.objects[n]; add_hand_limits(o)
    for s in "LR":   # re-open the elbow after add_hand_limits (MPFB rest elbow ~46 deg)
        lo = o.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = R_(-40); lo.ik_max_x = R_(100)
    o.animation_data_create()
PARK = {n: V((-400.0 - 10 * i, 0, 0)) for i, n in enumerate(CH)}
exec(open(os.path.join(HERE, "lib_shots.py")).read())

# lib overrides: feet on the local ground
def P2(B, x, y): return V((B[0] + x, B[1] + y))
def stand_feet(n, f, root, yaw, spread=0.0, back=0.0):
    root = V((root[0], root[1], 0.0))
    for s in "LR":
        sx = 1 if s == "L" else -1
        xy = V(root) + rgt(yaw) * (-sx) * (0.11 * HSC[n] + spread) + fwd(yaw) * (0.02 - back * sx * 0.5)
        foot(n, s, f, (xy.x, xy.y, ground_z(xy.x, xy.y) + HUM[n].ankle[s].z), yaw + sx * 6)
HSC = {n: RIG[n].BN["head"].head_local.z / 1.6 for n in CH}       # body scale (girl ~0.55)
def stand(n, f, pos, yaw, dz=0.0, flex=0.0, spine=(3.0, 0, 0), head=(0, 0), feet=True, side=0.0):
    p = V((pos[0], pos[1], ground_z(pos[0], pos[1]) + HUM[n].root_head.z - 0.01 * HSC[n] + dz))
    body(n, f, p, yaw, flex=flex, spine=spine, head=head, side=side)
    if feet: stand_feet(n, f, pos, yaw)
    return p
def arms_relaxed(n, f, yaw, **kw):
    relaxed_arm(n, "L", f, yaw, fwd_=0.04 * HSC[n], out=0.04 * HSC[n], **kw); relaxed_arm(n, "R", f, yaw, fwd_=0.04 * HSC[n], out=0.04 * HSC[n], **kw)
def relaxed_arm(n, s, f, yaw, fwd_=0.04, out=0.04, up=0.0, pose="relaxed", swing=0.0):
    """arm hanging with a soft elbow; swing>0 moves the hand forward (walk arm swing)"""
    sx = 1 if s == "L" else -1; k = HSC[n]
    sh = wpos(n, "upperarm01." + s, f)
    down = V((0, 0, -1)); r = rgt(yaw) * (-sx)
    palm = sh + down * (0.58 * k - up) + r * (0.03 * k + out) + fwd(yaw) * (fwd_ + swing)
    hand(n, s, f, palm, -r, down + fwd(yaw) * 0.15, pole=sh + down * 0.3 * k + r * 0.2 - fwd(yaw) * 0.45, pose=pose)

def walk(n, f0, f1, p0, p1, yaw, stride=0.7, lift=0.08, swing=0.16, head=(0, 0), step=2, out=0.05):
    """walk p0 -> p1 at 1x (feet planted by Human.walk), bent arms swinging opposite the legs, head keys on top"""
    p0 = V((p0[0], p0[1], 0)); p1 = V((p1[0], p1[1], 0))
    if PLAN_LEN[0] and PLAN_LEN[0] != (f1 - f0 + 1):        # VO layout: same speed as planned (1x), distance follows the length
        p1 = p0 + (p1 - p0) * ((f1 - f0 + 1) / PLAN_LEN[0])
    def path(f):
        u = (f - f0) / max(1, f1 - f0); xy = p0.lerp(p1, u)
        return V((xy.x, xy.y, 0))
    HUM[n].walk(path, lambda f: yaw, f0, f1, stride=stride * HSC[n] / 1.0 if HSC[n] < 0.8 else stride, lift=lift * max(HSC[n], 0.6),
                bob=0.02 * HSC[n], crouch=0.03 * HSC[n], lean=5.0, step=step)
    dist = (p1 - p0).length; st = stride * HSC[n] if HSC[n] < 0.8 else stride
    for f in sorted(set(list(range(f0, f1 + 1, 6)) + [f1])):
        u = (f - f0) / max(1, f1 - f0); cyc = u * dist / st
        HUM[n].key_spine(f, flex=5.0, twist=-6 * math.sin(2 * math.pi * cyc), head=head)
        for s, ph in (("L", 0.0), ("R", 0.5)):
            relaxed_arm(n, s, f, yaw, fwd_=0.04 * HSC[n], out=out * HSC[n] if s == 'R' or n != 'Warrior' else 0.10, swing=(0.6 if (n == 'Warrior' and s == 'L') else 1.0) * swing * HSC[n] * math.sin(2 * math.pi * (cyc + ph)), up=0.03 * HSC[n])

# ---------------------------------------------------------------- props per shot
def sword_copy(src, name, f0, f1):
    s0 = bpy.data.objects[src]; o = s0.copy(); o.name = name; o.animation_data_clear(); s0.users_collection[0].objects.link(o)
    o.constraints.clear() if hasattr(o.constraints, "clear") else None
    sh0 = next(c for c in s0.children); h = sh0.copy(); h.name = name + ".sheath"; s0.users_collection[0].objects.link(h)
    h.parent = o; h.matrix_parent_inverse = Matrix()
    for x in (o, h): vis_window(x, f0, f1)
    return o, h
def sword_M(grip, ydir, xdir):
    """world matrix of a sword: origin (grip centre) at `grip`, blade along ydir, blade flat along xdir"""
    y = V(ydir).normalized(); x = (V(xdir) - y * V(xdir).dot(y)).normalized(); z = x.cross(y)
    return Matrix.Translation(V(grip)) @ Matrix((x, y, z)).transposed().to_4x4()
def set_M(o, M, f=None):
    o.matrix_world = M
    if f is not None:
        o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
GRIP_R = 0.0     # grip centre (local y)

def hold_sword(n, sid, f0, f1, keys, left=None, src="Sword_Found", right_side="R", palm_dir=None, finger_dir=None, fr=0.012, gy=0.0):
    """n grips the sword's grip in the right hand (Child Of wrist); `keys` = [(frame, sword world Matrix)] drive the hand.
    left = (y_on_blade, from_frame) -> the left hand wraps the blade/sheath at local y from that frame on."""
    sw, shth = sword_copy(src, "%s_%s" % (src, sid), f0, f1)
    fA, MA = keys[0]; s = right_side; ro = bpy.data.objects[n]; BN = ro.data.bones
    # 1) keep the grip within reach: 90% of shoulder->palm length
    Larm = (BN["lowerarm01." + s].head_local - BN["upperarm01." + s].head_local).length + (BN["wrist." + s].head_local - BN["lowerarm01." + s].head_local).length \
        + 0.6 * (BN["finger3-1." + s].head_local - BN["wrist." + s].head_local).length
    sh = wpos(n, "upperarm01." + s, fA); v = MA.translation - sh
    if v.length > 0.9 * Larm:
        T = Matrix.Translation(-v.normalized() * (v.length - 0.9 * Larm)); keys = [(f, T @ Mk) for f, Mk in keys]; fA, MA = keys[0]
    def surface(obj, M, p, d):
        Mi = (obj.matrix_world).inverted(); ok, loc, nrm, idx = obj.ray_cast(Mi @ (p - d * 0.2), (Mi.to_3x3() @ d).normalized(), distance=0.4)
        return (obj.matrix_world @ loc) if ok else p - d * 0.016
    for it in range(3):          # 2) solve, move the sword to where the hand really is, re-solve on the real surface
        set_M(sw, MA); bpy.context.view_layer.update()
        R3 = MA.to_3x3(); ax = R3 @ V((0, 1, 0)); sh = wpos(n, "upperarm01." + s, fA)
        pd = V(palm_dir) if palm_dir else (MA.translation - sh)
        pd = (pd - ax * pd.dot(ax)).normalized()
        c = surface(sw, MA, MA @ V((0, gy, 0)), pd)
        rep = grip_object(ro, s, fA, sw, c - pd * (0.006 if HSC[n] < 0.8 else 0.014), pd, finger_dir=finger_dir, finger_radius=fr)
        sc.frame_set(fA); bpy.context.view_layer.update()
        Wa = ro.matrix_world @ ro.pose.bones["wrist." + s].matrix; Wt = ro.matrix_world @ ro.pose.bones["IK_hand." + s].matrix
        err = (Wa.translation - Wt.translation).length; print("REACH", sid, n, s, "pass", it, round(err, 3))
        if err < 0.008: break
        C = Wa @ Wt.inverted(); keys = [(f, C @ Mk) for f, Mk in keys]; fA, MA = keys[0]
    M0 = ik_mat(n, s, fA)
    set_M(sw, MA); bpy.context.view_layer.update()
    child_of(sw, n, "wrist." + s, fA)
    pe = bpy.data.objects[n].pose.bones["Pole_elbow." + s]; sc.frame_set(fA); ploc = pe.location.copy()
    for f, _ in keys + [(f1, None)]:          # pin the elbow pole for the whole hold (no swing from neighbouring shots' keys)
        pe.location = ploc; pe.keyframe_insert("location", frame=f, group=pe.name)
    for f, Mk in keys:
        key_ik(n, s, f, Mk @ MA.inverted() @ M0)
    if left:
        yl, fl = left; o2 = "L" if s == "R" else "R"
        for f, Mk in keys:
            if f < fl: continue
            sc.frame_set(f); bpy.context.view_layer.update()
            Mw = sw.matrix_world; p = Mw @ V((0, yl, 0)); sh2 = wpos(n, "upperarm01." + o2, f)
            d = (p - sh2); ax = Mw.to_3x3() @ V((0, 1, 0)); d = (d - ax * d.dot(ax)).normalized()
            grip_object(bpy.data.objects[n], o2, f, shth, p - d * 0.016, d)
    return sw, rep

def hands_grip(n, f, sw, ys=(0.0, 0.42)):
    """right hand wraps the grip (y=ys[0] on the sword), left wraps the sheath at ys[1], both from below/behind; sw keyed in world"""
    sc.frame_set(f); bpy.context.view_layer.update(); Mw = sw.matrix_world; ax = Mw.to_3x3() @ V((0, 1, 0))
    for s_, y, tgt in (("R", ys[0], sw), ("L", ys[1], sw.children[0])):
        p = Mw @ V((0, y, 0)); shp = wpos(n, "upperarm01." + s_, f)
        d = (p - shp); d = (d - ax * d.dot(ax)).normalized()
        d = (d + V((0, 0, 0.8))); d = (d - ax * d.dot(ax)).normalized()          # palm comes from below and behind
        Mi = tgt.matrix_world.inverted(); o_ = Mi @ (p - d * 0.2); dl = (Mi.to_3x3() @ d).normalized()
        ok, loc, nrm, idx = tgt.ray_cast(o_, dl, distance=0.4)
        c = tgt.matrix_world @ loc if ok else p - d * 0.016                       # the real surface point, not a guessed radius
        grip_object(bpy.data.objects[n], s_, f, tgt, c - d * 0.010, d)
        elbow(n, s_, f, shp + V((0, 0, -0.4)) + (shp - wpos(n, "spine01", f)).normalized() * 0.2)

def palms_under(n, f, M, ys=(0.12, 0.42), lift=0.0):
    """both palms flat under the blade (palm up), fingers across it, at local y positions ys"""
    ax = M.to_3x3() @ V((0, 1, 0)); sh = wpos(n, "spine01", f)
    for s, y in zip("RL", ys):
        p = M @ V((0, y, 0)) - V((0, 0, 0.012 + lift))
        across = (p - sh); across.z = 0; across = (across - ax * across.dot(ax)).normalized()
        shp = wpos(n, "upperarm01." + s, f); outw = (shp - sh); outw.z = 0; outw = outw.normalized()
        hand(n, s, f, p, V((0, 0, 1)), across, pole=shp + V((0, 0, -0.4)) + outw * 0.25 - across * 0.15, pose="hold_flat_object")

# ================================================================== SHOTS
LG = V((0.0, 0.0))            # girl's spot in the lake
HILT = V((-0.18, -0.36))      # sword stuck in the bed, hilt up near the surface
def stuck_M():
    tip_dir = V((0.25, -0.55, -0.40)).normalized()        # blade down into the sand, away from her
    grip = V((HILT.x, HILT.y, -0.045))
    return sword_M(grip, tip_dir, V((1, 0.4, 0)))
SW_STUCK = None

def reach_report(n, s, f, tag):
    sc.frame_set(f); bpy.context.view_layer.update(); ro = bpy.data.objects[n]
    Wa = ro.matrix_world @ ro.pose.bones["wrist." + s].matrix; Wt = ro.matrix_world @ ro.pose.bones["IK_hand." + s].matrix
    print("REACH", tag, n, s, f, round((Wa.translation - Wt.translation).length, 3))

def shot_01(f0, n):
    """low by the water: the girl wades toward camera through the shallows, arms swinging, looking ahead/down"""
    walk("Girl", f0, f0 + n - 1, (0.25, 1.15), (0.02, 0.05), 0.0, stride=0.62, lift=0.12, head=(8, 0))
    camera("01", f0, n, [(0, (0.3, -1.85, 0.2), (0.1, 0.6, 0.5), 30), (1, (0.22, -1.55, 0.24), (0.05, 0.1, 0.5), 30)])
    return ("Girl",)

def shot_02(f0, n):
    """high front: she takes a step, her right foot comes down beside the hilt in the sand; she stops and looks down"""
    f1 = f0 + n - 1
    for k, f in enumerate((f0, f0 + 30, f0 + 60, f0 + 90, f1)):
        stand("Girl", f, (LG.x, LG.y + 0.0), 0.0, spine=(6 + 6 * min(k, 2), 0, 0), head=(10 + 7 * min(k, 2), 4 * math.sin(k)), feet=False)
    G = HUM["Girl"]
    for s in "LR":
        sx = 1 if s == "L" else -1
        a0 = V((LG.x + sx * 0.07, LG.y + 0.02)); foot("Girl", s, f0, (a0.x, a0.y, ground_z(a0.x, a0.y) + G.ankle[s].z), sx * 6)
        if s == "L": foot("Girl", s, f1, (a0.x, a0.y, ground_z(a0.x, a0.y) + G.ankle[s].z), sx * 6)
    aR = V((HILT.x + 0.08, HILT.y + 0.18)); a0 = V((LG.x - 0.07, LG.y + 0.02))
    foot("Girl", "R", f0 + 24, (a0.x, a0.y, ground_z(a0.x, a0.y) + G.ankle["R"].z), -6)
    mid = a0.lerp(aR, 0.5); foot("Girl", "R", f0 + 40, (mid.x, mid.y, ground_z(mid.x, mid.y) + G.ankle["R"].z + 0.07), -6, pitch=10)
    for f in (f0 + 56, f1): foot("Girl", "R", f, (aR.x, aR.y, ground_z(aR.x, aR.y) + G.ankle["R"].z), -10)
    for f in (f0, f0 + 40, f0 + 70, f1): arms_relaxed("Girl", f, 0.0)
    camera("02", f0, n, [(0, (0.75, -1.25, 0.55), (-0.1, -0.15, 0.22), 30), (1, (0.68, -1.12, 0.5), (-0.12, -0.2, 0.18), 30)])
    return ("Girl",)

def shot_03a(f0, n):
    """wide front: playing in the shallow water, she kicks a splash with her right foot twice, arms out for balance"""
    f1 = f0 + n - 1; G = HUM["Girl"]
    for k, f in enumerate(range(f0, f1 + 1, 25)):
        stand("Girl", f, LG, 10.0, spine=(4, 3 * math.sin(k), 0), head=(10, 6 * math.sin(k * 0.9)), feet=False, side=3 * math.sin(k))
    stand("Girl", f1, LG, 10.0, spine=(4, 0, 0), head=(10, 0), feet=False)
    aL = V((LG.x + 0.08, LG.y)); aR0 = V((LG.x - 0.08, LG.y))
    for f in (f0, f1): foot("Girl", "L", f, (aL.x, aL.y, ground_z(aL.x, aL.y) + G.ankle["L"].z), 16)
    for i, fk in enumerate((f0, f0 + 25, f0 + 40, f0 + 55, f0 + 80, f0 + 95, f0 + 110, f1)):
        kick = i in (2, 5)
        p = aR0 + (V((0, -0.22)) if kick else V((0, 0)))
        foot("Girl", "R", fk, (p.x, p.y, ground_z(p.x, p.y) + G.ankle["R"].z + (0.16 if kick else 0)), 4, pitch=-15 if kick else 0)
    for k, f in enumerate(range(f0, f1 + 1, 15)):
        for s in "LR":
            relaxed_arm("Girl", s, f, 10.0, out=0.10 + 0.04 * math.sin(k), up=0.08)
    camera("03a", f0, n, [(0, (0.6, -2.7, 0.72), (0.0, 0.0, 0.48), 30), (1, (0.4, -2.3, 0.7), (0.0, 0.0, 0.48), 30)])
    return ("Girl",)

def shot_03b(f0, n):
    """side wide: she stands in the shallows looking down into the clear water, head turning, a small sway"""
    f1 = f0 + n - 1
    for k, f in enumerate(range(f0, f1 + 1, 30)):
        stand("Girl", f, LG, -10.0, spine=(14, 4 * math.sin(k), 0), head=(25 + 4 * (k % 2), 10 * math.sin(k * 0.8)), side=2 * math.sin(k))
        arms_relaxed("Girl", f, -10.0)
    stand("Girl", f1, LG, -10.0, spine=(14, 0, 0), head=(28, 0)); arms_relaxed("Girl", f1, -10.0)
    camera("03b", f0, n, [(0, (-1.9, -1.75, 0.72), (0.0, 0.0, 0.45), 30), (1, (-1.6, -1.45, 0.68), (0.0, 0.0, 0.45), 30)])
    return ("Girl",)

GPOS4 = V((HILT.x + 0.05, HILT.y + 0.42))       # where she stands to reach the hilt
def shot_04(f0, n):
    """low side: she bends down and reaches into the water; her right hand closes on the hilt just under the surface"""
    global SW_STUCK
    f1 = f0 + n - 1; yaw = 0.0
    sw, sh = sword_copy("Sword_Found", "Sword_Found_04", f0, f1); set_M(sw, stuck_M())
    for f, fl, sp, hd, dz in ((f0, 5, 10, 20, 0), (f0 + 40, 30, 35, 30, -0.10), (f0 + 60, 35, 40, 28, -0.13), (f1, 36, 40, 26, -0.13)):
        stand("Girl", f, GPOS4, yaw, dz=dz, flex=fl, spine=(sp, 0, 0), head=(hd, 0))
    relaxed_arm("Girl", "R", f0, yaw); relaxed_arm("Girl", "L", f0, yaw)
    for f in (f0 + 40, f0 + 60, f1):
        sh_ = wpos("Girl", "upperarm01.L", f); hand("Girl", "L", f, sh_ + V((0.10, -0.12, -0.32)), V((-0.3, 0, -1)), V((0, -0.4, -1)), pose="relaxed")
    # right hand: reach (open) then grip at f0+60
    M = stuck_M(); sc.frame_set(f0 + 60)
    sh_ = wpos("Girl", "upperarm01.R", f0 + 60)
    pd = (M.translation - sh_); ax = M.to_3x3() @ V((0, 1, 0)); pd = (pd - ax * pd.dot(ax)).normalized()
    hand("Girl", "R", f0 + 36, M.translation - pd * 0.12 + V((0, 0, 0.08)), pd, V((0, -0.3, -1)), pose="open_alarm")
    rep = grip_object(bpy.data.objects["Girl"], "R", f0 + 60, sw, M.translation - pd * 0.016, pd)
    M0 = ik_mat("Girl", "R", f0 + 60); key_ik("Girl", "R", f1, M0); reach_report("Girl", "R", f0 + 60, "04")
    SW_STUCK = M0
    camera("04", f0, n, [(0, (-1.6, -0.95, 0.42), (-0.16, -0.08, 0.28), 26), (1, (-1.45, -0.85, 0.4), (-0.16, -0.1, 0.24), 26)])
    return ("Girl",)

def shot_05(f0, n):
    """front medium: she straightens up and pulls the long crusty 'stick' out of the water, then takes it in both hands"""
    f1 = f0 + n - 1; yaw = 0.0
    for f, fl, sp, hd, dz in ((f0, 36, 40, 26, -0.13), (f0 + 30, 20, 22, 18, -0.07), (f0 + 60, 2, 6, 6, 0.0), (f0 + 95, 0, 4, 2, 0.0), (f1, 0, 5, 4, 0.0)):
        stand("Girl", f, GPOS4, yaw, dz=dz, flex=fl, spine=(sp, 0, 0), head=(hd, 0))
    for f in (f0, f0 + 30):
        sh_ = wpos("Girl", "upperarm01.L", f); hand("Girl", "L", f, sh_ + V((0.10, -0.12, -0.32)), V((-0.3, 0, -1)), V((0, -0.4, -1)), pose="relaxed")
    Ms = stuck_M()
    chest = V((GPOS4.x, GPOS4.y, ground_z(GPOS4.x, GPOS4.y))) + V((-0.06, -0.24, 0.50))
    Mmid = sword_M(V((HILT.x + 0.02, HILT.y + 0.02, 0.12)), V((0.25, -0.9, -0.15)), V((1, 0.3, 0)))
    base = V((GPOS4.x, GPOS4.y, ground_z(GPOS4.x, GPOS4.y))) + rgt(yaw) * 0.13 + fwd(yaw) * 0.21 + V((0, 0, 0.54))
    Me = sword_M(base, V((0, 0, 1)) + rgt(yaw) * 0.25 + fwd(yaw) * 0.08, fwd(yaw))      # ends in the upright side hold of 06
    keys = [(f0, Ms), (f0 + 30, Mmid), (f0 + 60, Me), (f1, Me)]
    sw, rep = hold_sword("Girl", "05", f0, f1, keys, left=None, palm_dir=rgt(yaw) * -1, finger_dir=fwd(yaw))
    for f in (f0 + 60, f1): relaxed_arm("Girl", "L", f, yaw)
    camera("05", f0, n, [(0, (0.25, -1.9, 0.62), (-0.12, -0.1, 0.42), 32), (1, (0.2, -1.6, 0.68), (-0.1, -0.1, 0.5), 32)])
    return ("Girl",)

def side_hold(n, sid, f0, f1, P, yaw, lean=-0.25, up=0.46, out=0.19, fw=0.25, rise=0.05):
    """one hand (right) on the grip, the sword upright at her right side, tip leaning a little outward; left arm relaxed"""
    base = V((P.x, P.y, ground_z(P.x, P.y))) + rgt(yaw) * out + fwd(yaw) * fw + V((0, 0, up))
    tip = V((0, 0, 1)) + rgt(yaw) * (-lean) + fwd(yaw) * 0.08     # lean toward her right (outward)
    flat = fwd(yaw)
    keys = [(f0, sword_M(base, tip, flat)), (f0 + (f1 - f0) // 2, sword_M(base + V((0, 0, rise * 0.6)), tip + rgt(yaw) * 0.04, flat)), (f1, sword_M(base + V((0, 0, rise)), tip, flat))]
    if rise == 0: keys = [(f0, sword_M(base, tip, flat)), (f1, sword_M(base, tip, flat))]
    sw, _ = hold_sword(n, sid, f0, f1, keys, left=None, palm_dir=rgt(yaw) * -1, finger_dir=fwd(yaw))
    for f in range(f0, f1 + 1, 40): relaxed_arm(n, "L", f, yaw)
    relaxed_arm(n, "L", f1, yaw)
    return sw

def shot_06(f0, n):
    """low front push-in: she holds it upright in both hands and looks up along it - it is a sword"""
    f1 = f0 + n - 1; yaw = 0.0; P = GPOS4
    for k, f in enumerate(range(f0, f1 + 1, 30)):
        stand("Girl", f, P, yaw, spine=(-3, 0, 0), head=(-14 - 3 * (k % 2), 4 * math.sin(k)))
    stand("Girl", f1, P, yaw, spine=(-3, 0, 0), head=(-16, 0))
    side_hold("Girl", "06", f0, f1, P, yaw, out=0.13, fw=0.21, up=0.54)
    camera("06", f0, n, [(0, (0.15, -1.55, 0.32), (-0.05, 0.0, 0.72), 30), (1, (0.08, -1.15, 0.4), (-0.05, 0.0, 0.75), 30)])
    return ("Girl",)

def shot_07(f0, n):
    """close: the crusty, chipped blade fills the left of frame, her face beside it studying it"""
    f1 = f0 + n - 1; yaw = 0.0; P = GPOS4
    for k, f in enumerate(range(f0, f1 + 1, 30)):
        stand("Girl", f, P, yaw, spine=(2, -6, 0), head=(-4, -12 + 4 * math.sin(k)))
    stand("Girl", f1, P, yaw, spine=(2, -6, 0), head=(-4, -14))
    side_hold("Girl", "07", f0, f1, P, yaw, lean=-0.12, rise=0.03)
    gz = ground_z(P.x, P.y)
    camera("07", f0, n, [(0, (0.05, -1.85, gz + 0.85), (-0.09, -0.05, gz + 0.80), 55), (1, (0.02, -1.72, gz + 0.88), (-0.09, -0.05, gz + 0.84), 55)])
    return ("Girl",)

DAD8 = V((0.12, 5.75)); GIRL8 = V((0.10, 4.75))
def shot_08(f0, n):
    """shore: dad kneels to her height; she shows him the long crusty sword in both hands; he leans in to look"""
    f1 = f0 + n - 1; yawG, yawD = 180.0, 0.0
    for k, f in enumerate(range(f0, f1 + 1, 30)):
        stand("Girl", f, GIRL8, yawG, spine=(8, 0, 0), head=(22, 3 * math.sin(k)))
        arms_relaxed("Girl", f, yawG)
        kneel("Dad", f, (DAD8.x, DAD8.y), yawD, lean=4 + 2 * min(k, 2), spine=(6 + 2 * min(k, 2), 0, 0), head=(30 + 3 * (k % 2), 4 * math.sin(k)))
        relaxed_arm("Dad", "L", f, yawD, out=0.06, fwd_=0.06); relaxed_arm("Dad", "R", f, yawD, out=0.06, fwd_=0.06)
    stand("Girl", f1, GIRL8, yawG, spine=(8, 0, 0), head=(20, 0))
    kneel("Dad", f1, (DAD8.x, DAD8.y), yawD, lean=8, spine=(10, 0, 0), head=(30, 2))
    relaxed_arm("Dad", "L", f1, yawD, out=0.06, fwd_=0.06); relaxed_arm("Dad", "R", f1, yawD, out=0.06, fwd_=0.06)
    swg, _ = sword_copy("Sword_Found", "Sword_Found_08", f0, f1)
    mid = (GIRL8 + DAD8) / 2; gzm = ground_z(mid.x, mid.y)
    set_M(swg, sword_M(V((mid.x - 0.30, mid.y - 0.02, gzm + 0.012)), V((1, 0.08, 0)), V((0, 1, 0))))
    for f in range(f0, f1 + 1, 30): arms_relaxed("Girl", f, yawG)
    arms_relaxed("Girl", f1, yawG)
    camera("08", f0, n, [(0, (1.55, 4.55, 0.8), (0.1, 5.25, 0.68), 28), (1, (1.4, 4.45, 0.8), (0.1, 5.25, 0.7), 28)])
    return ("Girl", "Dad")

def shot_09(f0, n):
    """low, against the sky: still kneeling, dad holds the sword level on his palms at chest height, looks along it, amazed"""
    f1 = f0 + n - 1; yawD = 0.0
    for k, f in enumerate(range(f0, f1 + 1, 30)):
        kneel("Dad", f, (DAD8.x, DAD8.y), yawD, lean=4, spine=(4, 0, 0), head=(-8 - 3 * (k % 2), -22 + 4 * math.sin(k)))
    kneel("Dad", f1, (DAD8.x, DAD8.y), yawD, lean=4, spine=(4, 0, 0), head=(-10, -24))
    sc.frame_set(f0); bpy.context.view_layer.update()
    ch = wpos("Dad", "spine01", f0)
    side_hold("Dad", "09", f0, f1, DAD8, yawD, lean=-0.15, up=ch.z - ground_z(DAD8.x, DAD8.y) - 0.30, out=0.24, fw=0.30, rise=0)
    camera("09", f0, n, [(0, (0.12, 4.3, 1.12), (-0.06, 5.6, 1.24), 40), (1, (0.1, 4.4, 1.12), (-0.06, 5.6, 1.25), 40)])     # face and the upright blade beside it (>1 m from the lens); the fist below the frame edge
    return ("Dad",)

MO = V((100, 0, 0)); TBL = MO + V((0, 0.6, 0))
def museum_sword(name, f0, f1, M=None):
    sw, sh = sword_copy("Sword_Found", name, f0, f1)
    M = M or sword_M(TBL + V((-0.32, -0.05, sc["TABLE_TOP"] + 0.02)), V((1, 0.04, 0)), V((0, 1, 0)))
    set_M(sw, M); return sw, M
def shot_10(f0, n):
    """museum wide: the sword on the felt; two experts behind the table lean in, girl and dad at the table end"""
    f1 = f0 + n - 1; sw, M = museum_sword("Sword_Found_10", f0, f1)
    tz = sc["TABLE_TOP"]
    for k, f in enumerate(range(f0, f1 + 1, 30)):
        stand("ExpM", f, P2(TBL, 0.25, 0.98), 0.0, flex=4, spine=(10, 0, 0), head=(30, 6 * math.sin(k)))
        stand("ExpF", f, P2(TBL, -0.55, 0.72), 8.0, spine=(10, 0, 0), head=(26, -8 + 5 * math.sin(k)))
        stand("Dad", f, P2(TBL, -1.55, -0.25), -70.0, spine=(4, 0, 0), head=(12, -6))
        stand("Girl", f, P2(TBL, -1.30, -0.70), -55.0, spine=(2, 0, 0), head=(-6, 3 * math.sin(k)))
        for nn, yw in (("ExpF", 8.0), ("Dad", -70.0), ("Girl", -55.0)): arms_relaxed(nn, f, yw)
        arms_relaxed("ExpM", f, 0.0)
    camera("10", f0, n, [(0, (101.6, -3.6, 1.65), (100.0, 1.2, 1.25), 26), (1, (101.3, -3.1, 1.6), (100.0, 1.2, 1.25), 26)])
    return ("ExpM", "ExpF", "Dad", "Girl")

def shot_11(f0, n):
    """experts: she lifts the sword on her flat palms over the table; he leans in, studying it; the girl watches"""
    f1 = f0 + n - 1; tz = sc["TABLE_TOP"]
    P_F = P2(TBL, -0.15, 0.70); P_M = P2(TBL, 0.62, 0.98)
    for k, f in enumerate(range(f0, f1 + 1, 30)):
        stand("ExpF", f, P_F, 0.0, spine=(8, 0, 0), head=(22, 0))
        stand("ExpM", f, P_M, 25.0, flex=4, spine=(8, 0, 0), head=(22, 10 + 4 * math.sin(k)))
        stand("Girl", f, P2(TBL, -1.05, -0.35), -60.0, head=(-8, 0)); arms_relaxed("Girl", f, -60.0)
        arms_relaxed("ExpM", f, 25.0)
    stand("ExpF", f1, P_F, 0.0, spine=(8, 0, 0), head=(24, 0))
    M0 = sword_M(TBL + V((-0.45, -0.05, tz + 0.02)), V((1, 0.04, 0)), V((0, 1, 0)))
    gF = V((P_F.x - 0.16, P_F.y - 0.26, tz + 0.04))
    M1 = sword_M(gF + V((0, 0, 0.03)), V((0.55, -0.80, 0.06)), V((0.3, 0.2, 0.9))); M0 = sword_M(gF, V((0.55, -0.80, 0.03)), V((0.3, 0.2, 0.9)))
    hold_sword("ExpF", "11", f0, f1, [(f0, M0), (f0 + 70, M1), (f1, M1)])
    for f in (f0, f0 + 70, f1): relaxed_arm("ExpF", "L", f, 0.0)
    camera("11", f0, n, [(0, (100.25, -1.55, 1.45), (100.0, 1.0, 1.15), 32), (1, (100.15, -1.3, 1.45), (100.0, 1.0, 1.2), 32)])
    return ("ExpF", "ExpM", "Girl")

def shot_12(f0, n):
    """closer two-shot: the experts look up from the sword to each other and nod: a thousand years old"""
    f1 = f0 + n - 1; tz = sc["TABLE_TOP"]
    P_F = P2(TBL, -0.15, 0.70); P_M = P2(TBL, 0.62, 0.98)
    for k, f in enumerate((f0, f0 + 40, f0 + 70, f0 + 100, f1)):
        stand("ExpF", f, P_F, 0.0, spine=(8, 0, 0), head=((22, 10, 8, 12, 10)[k], (0, 18, 20, 16, 18)[k]))
        stand("ExpM", f, P_M, 25.0, flex=3, spine=(6, 0, 0), head=((20, 6, 14, 4, 6)[k], (10, -20, -22, -20, -18)[k]))
        arms_relaxed("ExpM", f, 25.0); relaxed_arm("ExpF", "L", f, 0.0)
    museum_sword("Sword_Found_12", f0, f1)             # put down on the felt in front of them
    for f in (f0, f1): relaxed_arm("ExpF", "R", f, 0.0)
    camera("12", f0, n, [(0, (100.55, -0.55, 1.55), (100.2, 1.3, 1.35), 38), (1, (100.45, -0.4, 1.55), (100.2, 1.3, 1.38), 38)])
    return ("ExpF", "ExpM")

MAC_SET = []
def macro_sword():
    if MAC_SET: return
    O = V(sc["MACRO_ORIGIN"]); o = bpy.data.objects["Sword_Macro"]; o.rotation_mode = 'XYZ'
    o.matrix_world = sword_M(O + V((-0.22, 0, -0.30)), V((0.6, 0, 0.8)), V((-0.8, 0, 0.6))); MAC_SET.append(1)
def shot_13(f0, n):
    """macro on the sky-blue gradient: the camera glides along the crusty blade (looks like rust)"""
    O = V(sc["MACRO_ORIGIN"]); macro_sword()
    camera("13", f0, n, [(0, O + V((0.1, -1.0, 0.0)), O + V((0.02, 0, 0.02)), 35), (1, O + V((0.05, -0.75, 0.08)), O + V((0.05, 0, 0.08)), 35)], fstop=11, catch=False)
    return ()

def shot_14(f0, n):
    """macro: the crust gives way to an old leather sheath with an embossed interlace pattern"""
    O = V(sc["MACRO_ORIGIN"]); macro_sword(); m = bpy.data.materials["M_SheathMorph"].node_tree
    for nm in ("Leather", "LeatherH"):
        s = m.nodes[nm].inputs['Factor']
        s.default_value = 0.0; s.keyframe_insert("default_value", frame=f0 + 10)
        s.default_value = 1.0; s.keyframe_insert("default_value", frame=f0 + 80)
    camera("14", f0, n, [(0, O + V((0.2, -0.62, 0.25)), O + V((0.12, 0, 0.15)), 40), (1, O + V((0.0, -0.55, 0.0)), O + V((-0.04, 0, -0.04)), 40)], fstop=11, catch=False)
    return ()

CO = V((300, 0, 0))
def belt_sword(f0, f1, sid):
    """Sword_Warrior hangs from the belt on the warrior's left hip (bone-parented to root: moves with the pelvis)"""
    sw, sh = sword_copy("Sword_Warrior", "Sword_Warrior_" + sid, f0, f1)
    r = bpy.data.objects["Warrior"]; R = RIG["Warrior"]
    rootM = R.BN["root"].matrix_local
    hip = V((0.30, 0.13, R.BN["pelvis.L"].head_local.z + 0.02))            # character's left = +x at rest
    Mrest = sword_M(hip, V((0.18, 0.95, -1.0)), V((0, 1, 0.95)))             # tip down and back
    sw.parent = r; sw.parent_type = 'BONE'; sw.parent_bone = "root"
    bpy.context.view_layer.update()
    pbM = rootM   # rest pose of the bone
    sw.matrix_parent_inverse = Matrix()
    # bone-parent space: object matrix relative to the bone tail; compute through the rest pose
    sc.frame_set(f0); bpy.context.view_layer.update()
    sw.matrix_world = r.matrix_world @ R.PB["root"].matrix @ rootM.inverted() @ Mrest
    bpy.context.view_layer.update(); print('BELT', sid, tuple(round(x, 2) for x in sw.matrix_world.translation), tuple(round(x, 2) for x in r.matrix_world @ R.PB['root'].head))
    return sw
def shot_15(f0, n):
    """camp, long ago: the warrior walks toward camera along the shore, his sheathed sword at his hip; a companion behind"""
    f1 = f0 + n - 1
    walk("Warrior", f0, f1, P2(CO, 1.55, 6.0), P2(CO, 1.3, 2.9), 0.0, stride=0.72, head=(4, 0))     # beside the fire pit, not through it
    walk("Comp", f0, f1, P2(CO, -4.5, 9.8), P2(CO, -1.0, 9.4), -80.0, stride=0.7, head=(0, -30))
    belt_sword(f0, f1, "15")
    camera("15", f0, n, [(0, CO + V((1.75, 0.7, 1.25)), CO + V((1.45, 5.4, 1.15)), 30), (1, CO + V((1.7, 0.4, 1.25)), CO + V((1.35, 4.2, 1.2)), 30)])
    return ("Warrior", "Comp")

def shot_16(f0, n):
    """wide: tents, boats, the fire; the warrior stops near the water and looks out over the lake; camera cranes up"""
    f1 = f0 + n - 1; P = P2(CO, 0.25, 2.6)
    for k, f in enumerate(range(f0, f1 + 1, 30)):
        stand("Warrior", f, P, 15.0, spine=(2, 0, 0), head=(-2, -25 + 12 * math.sin(k * 0.6)))
        relaxed_arm("Warrior", "R", f, 15.0); relaxed_arm("Warrior", "L", f, 15.0, out=0.12, fwd_=0.08)
    stand("Warrior", f1, P, 15.0, spine=(2, 0, 0), head=(-2, -20)); relaxed_arm("Warrior", "R", f1, 15.0); relaxed_arm("Warrior", "L", f1, 15.0, out=0.12, fwd_=0.08)
    walk("Comp", f0, f1, P2(CO, -2.0, 9.2), P2(CO, 1.6, 8.6), -95.0, stride=0.7)
    belt_sword(f0, f1, "16")
    camera("16", f0, n, [(0, CO + V((-2.3, -0.7, 0.9)), CO + V((0.3, 3.4, 1.3)), 26), (1, CO + V((-2.1, -0.5, 1.45)), CO + V((0.3, 3.6, 1.15)), 26)])
    return ("Warrior", "Comp")

def shot_17(f0, n):
    """by the boat: the sheathed sword drops into the lake, sinks through the clear water and settles on the bed"""
    f1 = f0 + n - 1
    sw, sh = sword_copy("Sword_Warrior", "Sword_Warrior_17", f0, f1)
    b = V(sc["BOAT_WATER"]); x0 = b + V((2.9, -0.9, 0))
    g_end = x0 + V((0.12, 0.05, 0)); bdir = V((1, 0.35, -0.02)).normalized(); flat = V((-0.35, 1, 0))
    bed_end = max(camp_h(g_end.x - 300 + bdir.x * t, g_end.y + bdir.y * t) for t in (0.0, 0.2, 0.4, 0.6, 0.77))
    keys = [(f0, sword_M(x0 + V((0, 0, 0.75)), V((0.3, 0.2, -1)), V((1, 0, 0)))),
            (f0 + 18, sword_M(x0 + V((0.02, 0.01, 0.05)), V((0.4, 0.25, -1)), V((1, 0, 0)))),
            (f0 + 60, sword_M(x0 + V((0.08, 0.04, bed_end + 0.25)), V((0.9, 0.3, -0.5)), flat)),
            (f0 + 100, sword_M(V((g_end.x, g_end.y, bed_end + 0.03)), bdir, flat)),
            (f1, sword_M(V((g_end.x, g_end.y, bed_end + 0.03)), bdir, flat))]
    for f, M in keys: set_M(sw, M, f)
    rest = V((g_end.x, g_end.y, bed_end + 0.03)) + bdir * 0.38      # blade middle at rest
    camera("17", f0, n, [(0, x0 + V((0.9, -1.2, 1.3)), x0 + V((-0.1, 0.1, -0.05)), 30), (0.45, x0 + V((0.6, -0.6, 1.2)), rest, 30),
                         (1, rest + V((0.05, -0.18, 0.95)), rest, 30)], catch=False)      # nearly overhead: refraction barely shifts the sword
    return ()

def shot_18(f0, n):
    """today: the girl wades along the shallows past camera, arms swinging, happy"""
    f1 = f0 + n - 1
    walk("Girl", f0, f1, (-1.6, -0.2), (0.7, -0.35), 90.0, stride=0.6, lift=0.12, head=(0, 12))
    k = min(1.0, n / 150.0)
    camera("18", f0, n, [(0, (-0.4, -2.6, 0.55), (-1.5, -0.2, 0.5), 30), (1, (-0.4 + 1.2 * k, -2.6, 0.58), (-1.5 + 2.2 * k, -0.25, 0.5), 30)])
    return ("Girl",)

# clip lengths: ~1.3x the matching stretch of the reference (60 fps)
SHOTS = [("01", 110, shot_01), ("02", 110, shot_02), ("03a", 150, shot_03a), ("03b", 130, shot_03b), ("04", 140, shot_04),
         ("05", 140, shot_05), ("06", 140, shot_06), ("07", 120, shot_07), ("08", 170, shot_08), ("09", 140, shot_09),
         ("10", 150, shot_10), ("11", 170, shot_11), ("12", 140, shot_12), ("13", 130, shot_13), ("14", 150, shot_14),
         ("15", 160, shot_15), ("16", 160, shot_16), ("17", 150, shot_17), ("18", 150, shot_18)]
bpy.data.objects["Sword_Found"].rotation_mode = 'XYZ'; bpy.data.objects["Sword_Found"].matrix_world = stuck_M()
PLAN_LEN = [0]
LAY = json.load(open(a[1])) if len(a) > 1 else None
f = 1; table = []
for sid, ln, fn in SHOTS:
    if LAY and sid not in LAY: continue
    f0, n = (LAY[sid] if LAY else (f, ln))
    PLAN_LEN[0] = ln
    used = fn(f0, n) or ()
    for c in CH: place_rig(c, f0, f0 + n - 1, c in used)
    table.append({"id": sid, "f0": f0, "len": n, "f1": f0 + n - 1, "chars": list(used)})
    print("SHOT", sid, f0, f0 + n - 1, used); f = f0 + n
sc.frame_start = 1; sc.frame_end = f - 1
# hide the static lake sword copy outside nothing: the original Sword_Found lies on the bed only in shots 01-03b
for so in [bpy.data.objects["Sword_Found"]] + list(bpy.data.objects["Sword_Found"].children): key_vis(so, 1, True); key_vis(so, next(t["f0"] for t in table if t["id"] == "04"), False)
for c in bpy.data.cameras: c.clip_end = 80.0
for o in bpy.data.objects:     # constant interpolation for visibility / park keys
    ad = o.animation_data
    if not ad or not ad.action: continue
    for fc in getattr(ad.action, "fcurves", []):
        if fc.data_path in ("hide_render", "hide_viewport"):
            for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
json.dump(table, open(os.path.join(os.path.dirname(OUT), "shots_table.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SHOTS_OK", sc.frame_end)
