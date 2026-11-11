"""All world animation, baked per film frame through the story clock SIG(t): cars, couple, driver, assassins, officer, crowd, bomb.
blender -b props.blend --python 04_anim.py -- <out.blend>"""
import sys, os, math, random
import bpy
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "00_lib.py")).read())
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
exec(open(os.path.join(HERE, "00_story.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
F_END = 2130
random.seed(28)

def ground_z(x, y):
    if 6.0 <= y <= 8.0 and not (-2.5 < x < 2.5): return 0.15
    if -7.0 <= y <= -5.5: return 0.15
    if y > 8.0 and 2.5 <= abs(x) <= 4.5: return 0.15
    return 0.0

def frames(ranges, step):
    out = set()
    for a, b in ranges:
        out.update(range(a - (a - 1) % step, b + 1, step))
    return sorted(f for f in out if 1 <= f <= F_END)
ALL2 = frames([(1, F_END)], 2)

def key_vis(obj, cond, fr):
    prev = None
    for f in fr:
        v = bool(cond(sig_f(f)))
        if v != prev:
            obj.hide_render = not v; obj.hide_viewport = not v
            obj.keyframe_insert("hide_render", frame=f); obj.keyframe_insert("hide_viewport", frame=f); prev = v
    for fc in fcurves_of(obj):
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'

def fcurves_of(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    out = []
    for layer in getattr(ad.action, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags: out.extend(cb.fcurves)
    return out

def yaw_to(d):
    return math.degrees(math.atan2(d.x, -d.y))

# ================================================================ cars
def key_car(root, sway, wheels, posfn, fr, blast=False):
    prev = None; ang = 0.0; R = root["wheel_r"]
    for f in fr:
        s = sig_f(f); p, h = posfn(s)
        root.location = (p.x, p.y, 0.0); root.rotation_euler = (0, 0, h + math.pi)  # model front is -Y; heading 0 = facing -Y
        root.rotation_euler = (0, 0, h)
        root.keyframe_insert("location", frame=f); root.keyframe_insert("rotation_euler", frame=f)
        if prev is not None:
            dp = (p - prev[0]); fwd = Vector((math.sin(h), -math.cos(h)))
            ang += dp.dot(fwd) / R
        prev = (p, h)
        for w in wheels:
            w.rotation_euler = (ang, 0, 0); w.keyframe_insert("rotation_euler", frame=f)
        # body: gentle idle shake + brake pitch from acceleration
        a = (D1(s + 0.15) - 2 * D1(s) + D1(s - 0.15)) / 0.0225 if not blast else 0.0
        pitch = max(-0.04, min(0.04, -0.006 * a)); heave = 0.004 * math.sin(s * 37.0)
        lift = 0.0; roll = 0.0
        if blast and s > BLAST_SIG:
            u = s - BLAST_SIG
            lift = max(0.0, 2.6 * u - 4.9 * u * u * 1.6) if u < 0.34 else 0.0
            pitch = 0.18 * math.exp(-4 * u) * math.sin(13 * u); roll = -0.08 * math.exp(-3 * u) * math.sin(9 * u)
        sway.location = (0, 0, heave + lift); sway.rotation_euler = (pitch, roll, 0)
        sway.keyframe_insert("location", frame=f); sway.keyframe_insert("rotation_euler", frame=f)

C1, C1S = bpy.data.objects["Car1"], bpy.data.objects["Car1_Sway"]
C2, C2S = bpy.data.objects["Car2"], bpy.data.objects["Car2_Sway"]
W1 = [o for o in bpy.data.objects if o.name.startswith("Car1_wheel")]
W2 = [o for o in bpy.data.objects if o.name.startswith("Car2_wheel")]
key_car(C1, C1S, W1, car1, ALL2)
key_car(C2, C2S, W2, car2, ALL2, blast=True)
# car2 shows blast scorch after the explosion (darken paint)
for m in C2.children_recursive[0].data.materials if False else []: pass
print("CARS keyed")

# measure seats by ray casting the car body in its rest pose
bpy.context.view_layer.update()
sc.frame_set(1)
body1 = bpy.data.objects["Car1_Body"]
def car_local_hit(x, y, z0=2.0):
    dg = bpy.context.evaluated_depsgraph_get(); ob = body1.evaluated_get(dg)
    Mi = body1.matrix_world.inverted(); M = body1.matrix_world
    o_w = M @ Vector((x, y, z0)); d_w = (M.to_3x3() @ Vector((0, 0, -1))).normalized()
    hit, loc, nrm, idx, obj, mat = sc.ray_cast(dg, o_w, d_w)
    if not hit: return None
    return (Mi @ loc).z
SEAT_R = car_local_hit(-0.3, 0.78); SEAT_F = car_local_hit(0.25, 0.05); FLOOR_R = car_local_hit(-0.3, 0.32); FLOOR_F = car_local_hit(0.25, -0.5)
print("SEATS", SEAT_R, SEAT_F, FLOOR_R, FLOOR_F)
SEAT_R = SEAT_R or 0.95; SEAT_F = SEAT_F or 0.9; FLOOR_R = FLOOR_R or 0.6; FLOOR_F = FLOOR_F or 0.6
if FLOOR_R > SEAT_R - 0.2: FLOOR_R = SEAT_R - 0.38
if FLOOR_F > SEAT_F - 0.2: FLOOR_F = SEAT_F - 0.38

# ================================================================ human helpers
HUM = {}
def setup(name):
    o = bpy.data.objects[name]
    R = make_human_ctrl(o); H = Human(R); HUM[name] = H
    return H

def base_data(H):
    B = H.r.BN
    return dict(sh={s: B["upperarm01." + s].head_local.copy() for s in "LR"}, rh=H.root_head.copy())

def key_head(H, f, pitch, yaw):
    for n, w in H.HEAD_W.items():
        H.r.key_rot(n, f, [("X", pitch * w), ("Z", yaw * w)])

def person_M(pos, yaw, gz):
    return Matrix.Translation(Vector((pos.x, pos.y, gz))) @ Matrix.Rotation(R_(yaw), 4, 'Z')

def W(H, pos, yaw, gz, local):
    """rest-space point (x, y relative to root, z absolute in rest) to world for a standing person"""
    rh = H.root_head
    return person_M(pos, yaw, gz) @ Vector((local[0], local[1] - rh.y * 0, local[2]))

def arm_pose(H, s, f, pos, yaw, gz, kind, k=0.0, ph=0.0, extra=None):
    """kind: down / wave / cheer / coat / hip / aim(target world)"""
    sh = {x: H.r.BN["upperarm01." + x].head_local for x in "LR"}
    Rz = Matrix.Rotation(R_(yaw), 3, 'Z')
    for side in "LR":
        sx = 1 if side == "L" else -1
        S = sh[side]
        loc = Vector((S.x + sx * 0.04, S.y + 0.03, S.z - 0.56)); d = Vector((0, 0.05, -1)); n = Vector((-sx, 0, 0))
        pole = Vector((S.x + sx * 0.3, S.y + 0.5, S.z - 0.3))
        sway = 0.02 * math.sin(s * 1.3 + ph + (0 if side == "L" else 1.7))
        loc = loc + Vector((0, sway, 0))
        if kind == "wave" and side == "R" and k > 0.01:
            up = Vector((S.x + sx * 0.18, S.y - 0.12, S.z + 0.5)) + Vector((sx * 0.12 * math.sin(s * 11 + ph), 0, 0))
            loc = loc.lerp(up, k); d = d.lerp(Vector((0, -0.2, 1)), k); n = n.lerp(Vector((0, -1, 0)), k)
            pole = pole.lerp(Vector((S.x + sx * 0.6, S.y + 0.2, S.z)), k)
        if kind == "cheer" and k > 0.01:
            up = Vector((S.x + sx * 0.2, S.y - 0.15, S.z + 0.45 + 0.06 * math.sin(s * 9 + ph + (0 if side == "L" else 2))))
            loc = loc.lerp(up, k); d = d.lerp(Vector((0, 0, 1)), k); n = n.lerp(Vector((0, -1, 0)), k)
            pole = pole.lerp(Vector((S.x + sx * 0.6, S.y + 0.2, S.z)), k)
        if kind == "clap" and k > 0.01:
            c = 0.03 + 0.06 * (0.5 + 0.5 * math.sin(s * 14 + ph))
            mid = Vector((sx * c, S.y - 0.33, S.z - 0.2))
            loc = loc.lerp(mid, k); d = d.lerp(Vector((0, -0.6, 0.8)), k); n = n.lerp(Vector((-sx, 0, 0)), k)
        if kind == "coat" and side == "R":
            chest = Vector((0.06, S.y - 0.12, S.z - 0.2))
            loc = loc.lerp(chest, k); d = d.lerp(Vector((1, 0.3, 0.2)), k); n = n.lerp(Vector((0, 1, 0)), k)
        if kind == "aim" and side == "R" and extra is not None:
            tgt, kk = extra
            Sw = person_M(pos, yaw, gz) @ S
            dirw = (tgt - Sw).normalized()
            dl = Rz.inverted() @ dirw
            aimp = S + dl * 0.6
            chest = Vector((0.06, S.y - 0.12, S.z - 0.2))
            loc = chest.lerp(aimp, kk) if kk > 0 else loc.lerp(chest, k)
            d = d.lerp(dl, max(k, kk)); n = n.lerp(Vector((1, 0, 0)), max(k, kk))
            pole = Vector((S.x + sx * 0.3, S.y + 0.4, S.z - 0.5))
        Mw = person_M(pos, yaw, gz)
        H.key_hand(side, f, Mw @ loc, (Rz @ d).normalized(), (Rz @ n).normalized(), pole=Mw @ pole)

def stand(H, f, pos, yaw, gz, bob=0.0, flex=0.0, twist=0.0, side=0.0, crouch=0.012):
    rh = H.root_head
    H.key_root(f, Vector((pos.x, pos.y, gz + rh.z - crouch + bob)), yaw=yaw, flex=flex * 0.4, side=side)
    H.key_spine(f, flex=flex, twist=twist, side=side * 0.5)
    for s_ in "LR":
        H.key_foot(s_, f, H.foot_xy(s_, pos, yaw), yaw)

class Actor:
    """story-driven standing/walking person. plan(s) -> (pos Vector2, yaw deg, mode 'stand'|'walk')"""
    def __init__(self, H, plan, arms, head, fr, stride=0.72, lean=6.0, run_s=None):
        self.H, self.plan, self.arms, self.head, self.fr, self.stride, self.lean = H, plan, arms, head, fr, stride, lean
        self.run_s = run_s
    def bake(self):
        H = self.H; fr = self.fr; step = fr[1] - fr[0] if len(fr) > 1 else 2
        modes = [(f,) + tuple(self.plan(sig_f(f))) for f in fr]
        # group walk runs
        i = 0
        while i < len(modes):
            f, pos, yaw, mode = modes[i]
            if mode == "walk":
                j = i
                while j + 1 < len(modes) and modes[j + 1][3] == "walk" and modes[j + 1][0] - modes[j][0] == step: j += 1
                f0, f1 = modes[i][0], modes[j][0]
                if f1 > f0:
                    st = self.stride
                    pth = lambda ff: (lambda P: Vector((P[0].x, P[0].y, 0)))(self.plan(sig_f(ff)))
                    yf = lambda ff: self.plan(sig_f(ff))[1]
                    H.walk(pth, yf, f0, f1, stride=st, lean=self.lean, step=step, lift=0.1 if st < 1.0 else 0.16, bob=0.025)
                else:
                    stand(H, f, pos, yaw, ground_z(pos.x, pos.y))
                i = j + 1; continue
            gz = ground_z(pos.x, pos.y)
            s = sig_f(f)
            stand(H, f, pos, yaw, gz, bob=0.006 * math.sin(s * 2.1 + hash(H.r.o.name) % 7), side=1.2 * math.sin(s * 0.9 + hash(H.r.o.name) % 5))
            i += 1
        for f, pos, yaw, mode in modes:
            s = sig_f(f); gz = ground_z(pos.x, pos.y)
            self.arms(H, s, f, pos, yaw, gz, mode)
            hp, hy = self.head(s, pos, yaw)
            key_head(H, f, hp, hy)

def look_yaw(pos, yaw, target, lim=70):
    d = target - pos
    a = yaw_to(d) - yaw
    a = (a + 180) % 360 - 180
    return max(-lim, min(lim, a))

# ================================================================ crowd (linked duplicates of the six bases)
BASES = ["CrowdM1", "CrowdM2", "CrowdM3", "CrowdF1", "CrowdF2", "CrowdF3"]
CCR = coll("Crowd")
def clone(base, name):
    src = bpy.data.objects[base]
    a = src.copy(); a.name = name; CCR.objects.link(a)
    a.animation_data_clear()
    for pb in a.pose.bones:
        for c in pb.constraints:
            if getattr(c, "target", None) == src: c.target = a
            if getattr(c, "pole_target", None) == src: c.pole_target = a
    for ch in src.children:
        cc = ch.copy(); cc.name = name + "_" + ch.name.split(".")[-1]; CCR.objects.link(cc); cc.parent = a
        for m in cc.modifiers:
            if m.type == 'ARMATURE': m.object = a
    return a

for b in BASES: setup(b)
for nm in ("Archduke", "Duchess", "Driver", "Gunman", "Bomber", "NerveA", "NerveB", "Officer"): setup(nm)
print("RIGS ready")

def car_pos_w(s):
    p, h = car1(s); return p

CORNER_FR = frames([(1, 520), (1080, 1800)], 4)
BOMB_FR = frames([(380, 1200)], 4)
crowd = []
def add_crowd(n, region, yaw, fr, group):
    for k in range(n):
        x = random.uniform(*region[0]); y = random.uniform(*region[1])
        if any((Vector((x, y)) - c[1]).length < 0.62 for c in crowd): continue
        crowd.append((group, Vector((x, y)), yaw + random.uniform(-25, 25), fr))
add_crowd(16, ((-20, -3.2), (6.35, 7.8)), 0, CORNER_FR, "corner")
add_crowd(12, ((5.0, 24), (6.35, 6.8)), 0, CORNER_FR, "corner")
add_crowd(11, ((-4.3, -2.8), (8.6, 26)), 90, CORNER_FR, "corner")
add_crowd(4, ((3.0, 3.4), (13.5, 24)), -90, CORNER_FR, "corner")
add_crowd(12, ((-22, 24), (-6.9, -5.8)), 180, CORNER_FR, "corner")
add_crowd(26, ((64, 104), (6.35, 7.9)), 0, BOMB_FR, "bomb")
add_crowd(12, ((66, 102), (-6.9, -5.8)), 180, BOMB_FR, "bomb")
print("CROWD", len(crowd))

def crowd_plan_factory(home, yaw, group):
    away = None
    if group == "bomb":
        d = Vector((home.x - BLAST_P.x, home.y - BLAST_P.y)); dist = d.length
        if dist < 16:
            dd = Vector((d.x, 0.0)).normalized() if abs(d.x) > 0.5 else Vector((1.0, 0.0))
            away = home + dd * (9.0 - 0.3 * dist) + Vector((0, random.uniform(-0.4, 0.4)))
    surge = None
    if group == "corner" and home.y > 6.2 and (home - GUNMAN1).length < 12:
        surge = home + (GUNMAN1 - home).normalized() * min(2.2, (GUNMAN1 - home).length - 1.0)
    rs = random.uniform(0.0, 0.35)
    def plan(s):
        if away is not None and s > BLAST_SIG + 0.15 + rs:
            u = min(1.0, (s - BLAST_SIG - 0.15 - rs) / 2.2)
            p = home.lerp(away, smooth(u) if u < 1 else 1.0)
            ya = yaw_to(away - home)
            return p, ya, ("walk" if u < 1.0 else "stand")
        if surge is not None and s > 26.8 + rs:
            u = min(1.0, (s - 26.8 - rs) / 1.6)
            return home.lerp(surge, smooth(u)), yaw_to(GUNMAN1 - home), ("walk" if u < 1.0 else "stand")
        return home, yaw, "stand"
    return plan

styles = ["wave", "cheer", "clap", "down", "wave", "clap"]
for k, (group, home, yaw, fr) in enumerate(crowd):
    base = BASES[k % len(BASES)]
    a = clone(base, f"Crowd_{group}_{k:02d}")
    H = Human(Rig(a))
    style = styles[(k * 7) % len(styles)]; ph = random.uniform(0, 6)
    plan = crowd_plan_factory(home, yaw, group)
    def arms(H, s, f, pos, yw, gz, mode, style=style, ph=ph, home=home, group=group):
        e = max(0.0, min(1.0, 1.4 - (car_pos_w(s) - home).length / 14.0))
        if group == "bomb" and s > BLAST_SIG: e = 0.0
        if group == "corner" and s > 26.0: e = 0.0
        if mode == "walk":
            arm_pose(H, s * 1.0, f, pos, yw, gz, "down", ph=ph * 3)
        else:
            arm_pose(H, s, f, pos, yw, gz, style, k=smooth(e * 1.2), ph=ph)
    def head(s, pos, yw, home=home, group=group):
        tgt = car_pos_w(s)
        if group == "bomb" and s > BLAST_SIG - 0.2: tgt = BLAST_P.to_2d()
        if group == "corner" and s > 25.9: tgt = GUNMAN1
        return (-5.0 + 3 * math.sin(s * 0.7), look_yaw(pos, yw, tgt, 65))
    Actor(H, plan, arms, head, fr, stride=1.25 if group == "bomb" else 0.72, lean=12 if group == "bomb" else 5).bake()
print("CROWD baked")

# ================================================================ seated principals (armatures parented to car1 sway; car-local space)
def seat(H, f, base, flex=-6.0, side=0.0, twist=0.0, fwd=0.0, drop=0.0, head=(0.0, 0.0), legs=None):
    rh = H.root_head
    H.key_root(f, Vector((base.x, base.y - fwd, base.z + drop)), yaw=0, flex=flex * 0.3, side=side * 0.4)
    H.key_spine(f, flex=flex, twist=twist, side=side, head=head)
    for s_ in "LR":
        sx = 1 if s_ == "L" else -1
        fx, fy, fz = legs if legs else (0.0, 0.0, FLOOR_R if base.y > 0.4 else FLOOR_F)
        a = H.ankle[s_]
        xy = Vector((base.x + sx * 0.12, base.y - 0.48 + fy))
        M = Matrix.Translation(Vector((xy.x, xy.y, fz + a.z * 0.6))) @ Matrix.Rotation(R_(-15), 4, 'X') @ \
            Matrix.Translation(-a) @ H.r.rest("IK_foot." + s_)
        H.r.key_world("IK_foot." + s_, f, M)
        pole = Vector((xy.x + sx * 0.05, xy.y - 0.6, fz + 1.0))
        pb = H.r.PB["Pole_knee." + s_]; n = "Pole_knee." + s_
        pb.location = H.r.rest(n).to_3x3().inverted() @ (pole - H.r.BN[n].head_local)
        pb.keyframe_insert("location", frame=f, group=n)

def hand_local(H, side, f, loc, d, n, pole):
    H.key_hand(side, f, loc, d.normalized(), n.normalized(), pole=pole)

def parent_to(arm, parent):
    arm.parent = parent; arm.matrix_parent_inverse = Matrix.Identity(4)

ARCH, DUCH, DRV = HUM["Archduke"], HUM["Duchess"], HUM["Driver"]
for H in (ARCH, DUCH, DRV): parent_to(H.r.o, C1S)
A_BASE = Vector((-0.33, 0.92, SEAT_R + 0.03)); D_BASE = Vector((0.31, 0.92, SEAT_R + 0.01)); V_BASE = Vector((0.2, 0.08, SEAT_F + 0.1))
GUN_LOCAL = None
def world_to_car_local(s, pw):
    p, h = car1(s); M = Matrix.Translation(Vector((p.x, p.y, 0))) @ Matrix.Rotation(h, 4, 'Z')
    return M.inverted() @ pw
for f in ALL2:
    s = sig_f(f)
    # --- Archduke
    gun_l = world_to_car_local(s, Vector((GUNMAN1.x, GUNMAN1.y, 1.5)))
    look = math.degrees(math.atan2(gun_l.x - A_BASE.x, -(gun_l.y - A_BASE.y)))
    crowd_look = 35 * math.sin(s * 0.55) - 20
    hy = crowd_look
    if s > 25.0: hy = crowd_look + (look - crowd_look) * smooth((s - 25.0) / 0.5)
    if 3.4 < s < 6.5:   # bomb: head snaps toward the thrower then back to the blast
        hy = -70 * smooth((s - 3.4) / 0.3) * (1 - smooth((s - 5.4) / 1.0))
    slump = smooth((s - 26.75) / 0.9)
    seat(ARCH, f, A_BASE, flex=-6 + 34 * slump, side=-10 * slump, fwd=0.06 * slump, drop=-0.02 * slump,
         head=(-4 + 30 * slump, hy * (1 - slump)))
    sh = {x: ARCH.r.BN["upperarm01." + x].head_local for x in "LR"}
    for side in "LR":
        sx = 1 if side == "L" else -1
        knee = Vector((A_BASE.x + sx * 0.14, A_BASE.y - 0.38, A_BASE.z + 0.04))
        loc = knee + Vector((0, 0, 0.06)); d = Vector((0, -1, -0.3)); n = Vector((0, 0, -1))
        if side == "R" and 3.45 < s < 5.6:
            k = smooth((s - 3.45) / 0.25) * (1 - smooth((s - 4.6) / 0.8))
            up = Vector((A_BASE.x - 0.25, A_BASE.y - 0.15, A_BASE.z + 0.62)); loc = loc.lerp(up, k); d = d.lerp(Vector((-0.3, 0.3, 1)), k); n = n.lerp(Vector((-1, 0, 0)), k)
        if side == "L" and s < 3.3:
            k = 0.6 + 0.4 * math.sin(s * 3)   # salute-ish wave to the crowd
            up = Vector((A_BASE.x + 0.12, A_BASE.y - 0.2, A_BASE.z + 0.5 + 0.04 * math.sin(s * 8))); loc = loc.lerp(up, max(0, min(1, k)) * 0.8)
        if slump > 0:
            loc = loc.lerp(Vector((A_BASE.x + sx * 0.18, A_BASE.y - 0.32, A_BASE.z - 0.05)), slump)
        pole = Vector((A_BASE.x + sx * 0.5, A_BASE.y + 0.4, A_BASE.z + 0.2))
        hand_local(ARCH, side, f, loc, d, n, pole)
    # --- Duchess
    hy = -crowd_look * 0.8 + 10
    if s > 25.1: hy = hy + (look + 8 - hy) * smooth((s - 25.1) / 0.5)
    if 3.4 < s < 6.5: hy = -60 * smooth((s - 3.5) / 0.3) * (1 - smooth((s - 5.4) / 1.0))
    sl = smooth((s - 26.15) / 0.8)
    seat(DUCH, f, D_BASE, flex=-6 + 18 * sl, side=-32 * sl, fwd=0.03 * sl, head=(-2 + 22 * sl, hy * (1 - sl)), twist=-8 * sl)
    for side in "LR":
        sx = 1 if side == "L" else -1
        lap = Vector((D_BASE.x + sx * 0.1, D_BASE.y - 0.34, D_BASE.z + 0.06))
        if side == "L":   # parasol hand (outer side)
            loc = Vector((D_BASE.x + 0.2, D_BASE.y - 0.3, D_BASE.z + 0.38)); d = Vector((0.0, -0.4, -0.25)); n = Vector((-1, 0, 0))
            loc = loc.lerp(lap + Vector((0.08, 0, 0.05)), sl); pole = Vector((D_BASE.x + 0.55, D_BASE.y + 0.2, D_BASE.z + 0.1))
        else:
            loc = lap; d = Vector((0, -1, -0.3)); n = Vector((0, 0, -1))
            if s > 25.3 and sl < 1:   # hand to chest in fright
                k = smooth((s - 25.3) / 0.4) * (1 - sl); loc = loc.lerp(Vector((D_BASE.x - 0.02, D_BASE.y - 0.16, D_BASE.z + 0.42)), k)
            pole = Vector((D_BASE.x - 0.5, D_BASE.y + 0.4, D_BASE.z + 0.2))
        hand_local(DUCH, side, f, loc, d, n, pole)
    # --- Driver: hands on the wheel; looks back while reversing
    seat(DRV, f, V_BASE, flex=-2, head=(0, 120 * smooth((s - 23.5) / 0.4) * (1 - smooth((s - 25.6) / 0.5)) * 0.6))
    WC = Vector((0.176, -0.31, 1.33))
    steer = 0.0
    if 20.0 < s < 22.3: steer = 0.5 * math.sin(math.pi * (s - 20.0) / 2.3)
    for side in "LR":
        sx = 1 if side == "L" else -1
        a = math.pi / 2 + sx * 0.9 - steer
        loc = WC + Vector((math.cos(a) * 0.17, 0.05, math.sin(a) * 0.15)) + Vector((0, 0.08, 0))
        hand_local(DRV, side, f, loc, Vector((0, -1, 0.2)), Vector((-sx * 0.2, -0.5, 0.0)), Vector((V_BASE.x + sx * 0.5, V_BASE.y + 0.3, V_BASE.z)))
print("PRINCIPALS seated")

# parasol in the Duchess's left hand (visible grasp)
par = bpy.data.objects["Parasol"]
sc.frame_set(1); bpy.context.view_layer.update()
cst = par.constraints.new('CHILD_OF'); cst.target = DUCH.r.o; cst.subtarget = "wrist.L"
pb = DUCH.r.PB["wrist.L"]
Mw = DUCH.r.o.matrix_world @ pb.matrix
grip = Mw @ Vector((0, 0.06, 0))
Rcar = C1S.matrix_world.to_3x3().normalized().to_4x4()
par.matrix_world = Matrix.Translation(grip - Rcar.to_3x3() @ Vector((0, 0, 0.25))) @ Rcar @ Matrix.Rotation(R_(14), 4, 'X') @ Matrix.Rotation(R_(-10), 4, 'Y')
cst.inverse_matrix = Mw.inverted()

# ================================================================ assassins + officer (standing, story-driven)
GN, BM_, NA, NB, OF = HUM["Gunman"], HUM["Bomber"], HUM["NerveA"], HUM["NerveB"], HUM["Officer"]
G_FR = frames([(1, 520), (1080, 1800)], 2)
def gun_plan(s):
    face = yaw_to(car_pos_w(s) - GUNMAN0) if s < 22.6 else yaw_to(Vector((1.2, 10.0)) - GUNMAN1)
    if s < STEP_S[0]: return GUNMAN0, face, "stand"
    if s < STEP_S[1]:
        u = (s - STEP_S[0]) / (STEP_S[1] - STEP_S[0]); return GUNMAN0.lerp(GUNMAN1, smooth(u)), yaw_to(GUNMAN1 - GUNMAN0), "walk"
    if s > 27.0:   # pulled back by the officer
        u = min(1.0, (s - 27.0) / 1.2); p = GUNMAN1.lerp(GUNMAN1 + Vector((0.9, 0.5)), smooth(u))
        return p, yaw_to(Vector((1.2, 10.0)) - GUNMAN1) + 25 * smooth(u), ("walk" if u < 1 else "stand")
    return GUNMAN1, yaw_to(Vector((1.0, 10.2)) - GUNMAN1), "stand"
def gun_target(s):
    p, h = car1(s); c, sn = math.cos(h), math.sin(h)
    lx, ly = A_BASE.x, A_BASE.y
    return Vector((p.x + c * lx - sn * ly, p.y + sn * lx + c * ly, 1.55))
def gun_arms(H, s, f, pos, yw, gz, mode):
    k_draw = smooth((s - DRAW_S[0]) / (DRAW_S[1] - DRAW_S[0])) if s < 27.0 else 1.0
    k_aim = smooth((s - AIM_S[0]) / (AIM_S[1] - AIM_S[0])) if s < 27.0 else max(0.0, 1 - (s - 27.0) / 0.6)
    tgt = gun_target(s)
    if s > SHOT_S[0] - 0.05:   # recoil kicks
        for st in SHOT_S:
            if 0 < s - st < 0.25: tgt = tgt + Vector((0, 0, 0.9 * (1 - (s - st) / 0.25)))
    arm_pose(H, s, f, pos, yw, gz, "aim", k=k_draw, extra=(tgt, k_aim))
def gun_head(s, pos, yw):
    if s < 25.0: return (-3.0, look_yaw(pos, yw, car_pos_w(s), 70))
    return (-6.0, look_yaw(pos, yw, gun_target(s).to_2d(), 60))
Actor(GN, gun_plan, gun_arms, gun_head, G_FR, stride=0.6, lean=8).bake()
pistol = bpy.data.objects["Pistol"]
sc.frame_set(1); bpy.context.view_layer.update()
c_ = pistol.constraints.new('CHILD_OF'); c_.target = GN.r.o; c_.subtarget = "wrist.R"
Mw = GN.r.o.matrix_world @ GN.r.PB["wrist.R"].matrix
pistol.matrix_world = Mw @ Matrix.Translation(Vector((0.0, 0.09, 0.02))) @ Matrix.Rotation(R_(90), 4, 'X')
c_.inverse_matrix = Mw.inverted()
key_vis(pistol, lambda s: s > DRAW_S[0] + 0.35, ALL2)

O0, O1 = Vector((6.2, 13.8)), Vector((3.5, 11.0))
def off_plan(s):
    if s < 26.3: return O0, yaw_to(car_pos_w(s) - O0), "stand"
    u = min(1.0, (s - 26.3) / 0.9); return O0.lerp(O1, smooth(u)), yaw_to(GUNMAN1 - O0), ("walk" if u < 1 else "stand")
def off_arms(H, s, f, pos, yw, gz, mode):
    if s < 26.9: arm_pose(H, s, f, pos, yw, gz, "down"); return
    k = smooth((s - 26.9) / 0.4)
    gp, gy, _ = gun_plan(s); grab = Vector((gp.x, gp.y, 1.25))
    Rz = Matrix.Rotation(R_(yw), 3, 'Z'); Mw = person_M(pos, yw, gz)
    local = Mw.inverted() @ grab
    for side in "LR":
        sx = 1 if side == "L" else -1
        S = H.r.BN["upperarm01." + side].head_local
        rest = Vector((S.x + sx * 0.04, S.y + 0.03, S.z - 0.56)); tgt = local + Vector((sx * 0.06, 0, -0.05 * sx))
        loc = rest.lerp(tgt, k)
        H.key_hand(side, f, Mw @ loc, (Rz @ Vector((0, -1, 0))).normalized(), (Rz @ Vector((-sx, 0, 0))).normalized(),
                   pole=Mw @ Vector((S.x + sx * 0.4, S.y + 0.3, S.z - 0.4)))
Actor(OF, off_plan, off_arms, lambda s, p, y: (-4.0, look_yaw(p, y, GUNMAN1 if s > 25.5 else car_pos_w(s), 70)), G_FR, stride=0.85, lean=10).bake()

# bomber + the two who lost their nerve
B_FR = frames([(380, 1200)], 2)
BOMBER_YAW = yaw_to(Vector((80.0, 1.5)) - BOMBER)
def bomber_plan(s):
    if s < 2.3: return BOMBER + Vector((0.4, 0.5)), BOMBER_YAW, "stand"
    if s < 2.8: return (BOMBER + Vector((0.4, 0.5))).lerp(BOMBER, smooth((s - 2.3) / 0.5)), BOMBER_YAW, "walk"
    if s > 4.6:   # flees
        u = min(1.0, (s - 4.6) / 2.0); return BOMBER.lerp(BOMBER + Vector((-7.0, 3.0)), smooth(u)), yaw_to(Vector((-7.0, 3.0))), ("walk" if u < 1 else "stand")
    return BOMBER, BOMBER_YAW, "stand"
def bomber_arms(H, s, f, pos, yw, gz, mode):
    Rz = Matrix.Rotation(R_(yw), 3, 'Z'); Mw = person_M(pos, yw, gz)
    S = H.r.BN["upperarm01.R"].head_local
    if 2.5 < s < 3.6:
        # wind-up behind the head, then throw forward-down
        if s < REL_S:
            u = smooth((s - 2.5) / (REL_S - 0.1 - 2.5))
            back = Vector((S.x - 0.15, S.y + 0.35, S.z + 0.3)); fwd = Vector((S.x + 0.05, S.y - 0.55, S.z + 0.25))
            loc = (Vector((S.x - 0.04, S.y - 0.25, S.z - 0.2))).lerp(back, u) if s < REL_S - 0.12 else back.lerp(fwd, (s - (REL_S - 0.12)) / 0.12)
        else:
            u = smooth((s - REL_S) / 0.4); loc = Vector((S.x + 0.05, S.y - 0.55, S.z + 0.25)).lerp(Vector((S.x + 0.1, S.y - 0.4, S.z - 0.4)), u)
        H.key_hand("R", f, Mw @ loc, (Rz @ Vector((0, -1, 0.3))).normalized(), (Rz @ Vector((0, 0, -1))).normalized(),
                   pole=Mw @ Vector((S.x - 0.5, S.y + 0.3, S.z - 0.2)))
        SL = H.r.BN["upperarm01.L"].head_local
        H.key_hand("L", f, Mw @ Vector((SL.x + 0.1, SL.y - 0.3, SL.z - 0.1)), (Rz @ Vector((0, -1, 0))).normalized(), (Rz @ Vector((-1, 0, 0))).normalized(),
                   pole=Mw @ Vector((SL.x + 0.4, SL.y + 0.3, SL.z - 0.4)))
    elif s <= 2.5:
        arm_pose(H, s, f, pos, yw, gz, "coat", k=smooth((s - 1.5) / 0.6))
    else:
        arm_pose(H, s, f, pos, yw, gz, "down", ph=2)
def bomber_head(s, pos, yw):
    if s < 4.6: return (-3, look_yaw(pos, yw, car_pos_w(s), 70))
    return (0, 0)
Actor(BM_, bomber_plan, bomber_arms, bomber_head, B_FR, stride=1.2, lean=12).bake()
bomb = bpy.data.objects["Bomb"]
f_rel = next(f for f in range(700, 1000) if sig_f(f) >= REL_S)
sc.frame_set(f_rel); bpy.context.view_layer.update()
REL_P = BM_.r.o.matrix_world @ BM_.r.PB["wrist.R"].tail
print("REL_P", REL_P, "frame", f_rel)
cl = bomb.constraints.new('COPY_LOCATION'); cl.target = BM_.r.o; cl.subtarget = "wrist.R"; cl.head_tail = 1.0
for f in ALL2:
    s = sig_f(f); p = bomb_pos(s)
    infl = 1.0 if (p is None) else 0.0
    cl.influence = infl; cl.keyframe_insert("influence", frame=f)
    if p is not None:
        bomb.location = p; bomb.rotation_euler = (s * 14, s * 9, 0)
    bomb.keyframe_insert("location", frame=f); bomb.keyframe_insert("rotation_euler", frame=f)
key_vis(bomb, lambda s: 1.6 < s < BLAST_SIG, ALL2)

NA0, NB0 = Vector((90.6, 6.7)), Vector((91.5, 7.1))
def nerve_plan(home, away):
    def plan(s):
        face = yaw_to(car_pos_w(s) - home) if s < 2.0 else yaw_to(away - home)
        if s < 2.05: return home, max(-60, min(60, face)) if False else face, "stand"
        u = min(1.0, (s - 2.05) / 1.4)
        return home.lerp(away, smooth(u)), yaw_to(away - home), ("walk" if u < 1 else "stand")
    return plan
def na_arms(H, s, f, pos, yw, gz, mode):
    k = smooth((s - 0.6) / 0.5) * (1 - smooth((s - 2.0) / 0.4))
    arm_pose(H, s, f, pos, yw, gz, "coat", k=k)
def nb_arms(H, s, f, pos, yw, gz, mode):
    arm_pose(H, s, f, pos, yw, gz, "down", ph=1.0)
def na_head(s, pos, yw):
    if 1.4 < s < 2.0: return (8, look_yaw(pos, yw, NB0, 80))
    return (-2, look_yaw(pos, yw, car_pos_w(s), 70))
def nb_head(s, pos, yw):
    if 1.5 < s < 2.05: return (5, look_yaw(pos, yw, NA0, 80))
    return (0, look_yaw(pos, yw, car_pos_w(s), 70))
Actor(NA, nerve_plan(NA0, NA0 + Vector((1.6, 2.6))), na_arms, na_head, B_FR, stride=0.7).bake()
Actor(NB, nerve_plan(NB0, NB0 + Vector((2.6, 1.2))), nb_arms, nb_head, B_FR, stride=0.7).bake()

# hide the six crowd bases (only their linked clones are seen)
for b in BASES:
    o = bpy.data.objects[b]; o.hide_render = True; o.hide_viewport = True
    for ch in o.children: ch.hide_render = True; ch.hide_viewport = True
sc["SEAT_R"] = SEAT_R
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ANIM_DONE")
