# ================================================================== NeverBathed shots (appended to 03_head.py)
DX, RX = sc["DX"], sc["RX"]
TROUGH = V(sc["TROUGH"]); TUBP = V(sc["TUB"]); PIT = V(sc["PIT"]); FIRE = V(sc["FIRE"]); SEAT = V(sc["SEAT"]); FLAT = V(sc["FLAT"]); HARE = V(sc["HARE"])
OB = bpy.data.objects
def yaw_to(a_, b_):
    d = V(b_) - V(a_); return math.degrees(math.atan2(d.x, -d.y))
def top_z(o):
    return max((o.matrix_world @ V(c)).z for c in o.bound_box)
SEAT_Z = top_z(OB["D_SeatRock"]) - 0.01
def pit_z(x, y):
    lx, ly = x - PIT.x, y - PIT.y
    ex = (lx / 1.05) ** 2 + (ly / 0.45) ** 2
    z = -0.32 * max(0.0, 1.0 - ex) ** 0.6
    md = math.hypot(lx / 1.2, (ly - 0.95) / 0.32)
    if md < 1.0: z += 0.22 * (1 - md * md)
    return z

# ------------------------------------------------------------------ light states (keyed per shot, constant)
SUN = OB["Sun"]; WT = sc.world.node_tree; SKYN = next(n for n in WT.nodes if n.type == 'TEX_SKY'); BG = WT.nodes["SkyBG"]
def light(f, dusk=False):
    if dusk:
        SUN.data.energy = 1.6; SUN.data.color = (1.0, 0.62, 0.38); SUN.rotation_euler = (R_(78), 0, R_(60)); BG.inputs['Strength'].default_value = 0.22
        SKYN.sun_elevation = R_(6)
    else:
        SUN.data.energy = 2.6; SUN.data.color = (1.0, 0.95, 0.86); SUN.rotation_euler = (R_(48), 0, R_(45)); BG.inputs['Strength'].default_value = 0.18
        SKYN.sun_elevation = R_(42)
    SUN.data.keyframe_insert("energy", frame=f); SUN.data.keyframe_insert("color", frame=f); SUN.keyframe_insert("rotation_euler", frame=f)
    BG.inputs['Strength'].keyframe_insert("default_value", frame=f); SKYN.keyframe_insert("sun_elevation", frame=f)

# ------------------------------------------------------------------ small helpers
def stand(n, f, pos, yaw, head=(0.0, 0.0), spine=(3.0, 0.0, 0.0), flex=0.0, arms=True, dz=0.0):
    body(n, f, V(pos) + V((0, 0, HUM[n].root_head.z - 0.01 + dz)), yaw, flex=flex, spine=spine, head=head)
    stand_feet(n, f, pos, yaw)
    if arms: relaxed_arm(n, "L", f, yaw); relaxed_arm(n, "R", f, yaw)

def head_pt(n, f, rest_pt):
    sc.frame_set(int(f)); bpy.context.view_layer.update()
    return OB[n].matrix_world @ (RIG[n].delta("head") @ V(rest_pt))
def eye_mid_rest(n):
    B = RIG[n].BN; return (B["eye.L"].head_local + B["eye.R"].head_local) / 2
def mouth(n, f):
    e = eye_mid_rest(n); return head_pt(n, f, e + V((0, -0.035, -0.072)))
def head_fwd(n, f):
    e = eye_mid_rest(n); return (head_pt(n, f, e + V((0, -1, 0))) - head_pt(n, f, e)).normalized()

def thighs_hands(n, f, yaw, root):
    """seated: both hands rest on the thighs just behind the knees"""
    for s in "LR":
        sx = 1 if s == "L" else -1
        p = V(root) + fwd(yaw) * 0.30 - rgt(yaw) * sx * 0.13 + V((0, 0, 0.09))
        hand(n, s, f, p, V((0, 0, -1)), fwd(yaw) + V((0, 0, -0.3)), pole=wpos(n, "upperarm01." + s, f) - rgt(yaw) * sx * 0.35 - fwd(yaw) * 0.25, pose="relaxed")

def vis_only(o, f0, f1):
    key_vis(o, 1, False); key_vis(o, f0, True); key_vis(o, f1 + 1, False)

SMOKES = [OB["Smoke%d" % i] for i in range(8)]
for o in SMOKES + [OB["Fly%d" % i] for i in range(6)]: key_vis(o, 1, False)
def puffs(src_fn, f0, f1, every=14, rise=0.28, drift=V((0.03, 0.02, 0)), grow=4.0, life=50, count=None):
    """soft smoke puffs born at src_fn(f) and rising/growing; keyed per frame, constant visibility windows"""
    births = list(range(f0, f1 - 10, every))[:count or len(SMOKES)]
    for i, fb in enumerate(births):
        o = SMOKES[i % len(SMOKES)]; p0 = V(src_fn(fb)); fe = min(f1, fb + life)
        for f in range(fb, fe + 1, 2):
            u = (f - fb) / life
            o.location = p0 + V((0, 0, rise * u)) + drift * u + V((0.01 * math.sin(f / 5.0), 0, 0)); s = 1.0 + grow * u
            o.scale = (s, s, s * 0.8)
            o.keyframe_insert("location", frame=f); o.keyframe_insert("scale", frame=f)
        key_vis(o, fb, True); key_vis(o, fe + 1, False)

def flies(n, f0, f1, k=4):
    for i in range(k):
        o = OB["Fly%d" % i]; r = 0.18 + 0.05 * i; h = 0.16 + 0.05 * (i % 2); ph = i * 1.7; sp = 0.09 + 0.02 * i
        for f in range(f0, f1 + 1, 2):
            c = head_pt(n, f, eye_mid_rest(n) + V((0, 0.03, 0.17))) if f % 10 == 0 or f == f0 else c
            a_ = ph + (f - f0) * sp
            o.location = c + V((r * math.cos(a_), r * 0.8 * math.sin(a_), h + 0.04 * math.sin(a_ * 2.3)))
            o.rotation_euler = (0, 0, a_ + math.pi / 2)
            o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
        key_vis(o, f0, True); key_vis(o, f1 + 1, False)

def flame_flicker():
    for i in range(5):
        o = OB["D_Flame%d" % i]; o.scale = (0.75, 0.75, 0.75); o.keyframe_insert("scale", frame=1)
        for fc in all_fcurves(o):
            if fc.data_path == "scale":
                m = fc.modifiers.new('NOISE'); m.scale = 6 + i; m.strength = 0.35 if fc.array_index == 2 else 0.15; m.phase = i * 7 + fc.array_index
    L = OB["D_FireLight"].data; L.energy = 60; L.keyframe_insert("energy", frame=1)
    for fc in all_fcurves(L):
        m = fc.modifiers.new('NOISE'); m.scale = 5; m.strength = 18

# pipe geometry: find the bowl end and the stem tip in local space
PIPE = OB["Pipe"]
_pv = [v.co for v in PIPE.data.vertices]; _zm = max(v.z for v in _pv)
_xs = [v.x for v in _pv]; _x0, _x1 = min(_xs), max(_xs); _w = (_x1 - _x0) * 0.22
def _thick(sel): ys = [v.y for v in sel]; zs = [v.z for v in sel]; return (max(ys) - min(ys)) * (max(zs) - min(zs))
_lo = [v for v in _pv if v.x < _x0 + _w]; _hi = [v for v in _pv if v.x > _x1 - _w]
_bowl = _hi if _thick(_hi) > _thick(_lo) else _lo            # the bowl end is the thick end
BOWL_X = sum(v.x for v in _bowl) / len(_bowl)
_sgn = 1 if BOWL_X > (_x0 + _x1) / 2 else -1
TIP_L = min(_pv, key=lambda v: v.x * _sgn).copy()                         # far end of the stem (mouthpiece)
BOWL_L = V((BOWL_X, sum(v.y for v in _bowl) / len(_bowl), sum(v.z for v in _bowl) / len(_bowl)))
BOWL_TOP = V((BOWL_X, BOWL_L.y, _zm))
def place_pipe(o, tip_w, stem_dir, up=V((0, 0, 1))):
    """put the pipe so its stem tip is at tip_w and the stem runs from the tip toward the bowl along stem_dir"""
    xl = (V((BOWL_X, 0, TIP_L.z)) - V((TIP_L.x, 0, TIP_L.z))).normalized()      # local tip->bowl direction (along +-x)
    xw = V(stem_dir).normalized(); zw = (V(up) - xw * V(up).dot(xw)).normalized(); yw = zw.cross(xw)
    Rw = Matrix((xw, yw, zw)).transposed(); Rl = Matrix((xl, V((0, 0, 1)).cross(xl), V((0, 0, 1)))).transposed()
    R3 = Rw @ Rl.inverted()
    o.matrix_world = Matrix.Translation(V(tip_w) - R3 @ TIP_L) @ R3.to_4x4()
TWIG = OB["Twig"]

# ================================================================== BEAT 1: he thought a bath would make him sick (young)
YP = V((-2.75, -4.98, 0)); YYAW = 180.0          # at the south end of the trough, facing along it (+y)
def trough_reach(n, f0, n_fr, use_hand=True):
    """lean over the trough end; right hand (camera side) reaches down, index pointing, and stops above the water"""
    f1 = f0 + n_fr - 1
    keys = ((f0, 0.0, 4.0, (2, 0), 0.0), (f0 + 40, 10.0, 20.0, (14, 6), 0.6), (f0 + 75, 14.0, 26.0, (16, 10), 1.0), (f1, 14.0, 27.0, (14, 14), 1.0))
    for f, fl, sp, hd, u in keys:
        stand(n, f, YP, YYAW, head=hd, spine=(sp, 0, 0), flex=fl, arms=False)
        th = wpos(n, "upperleg01.L", f) + fwd(YYAW) * 0.12 - rgt(YYAW) * 0.04 + V((0, 0, -0.22))
        hand(n, "L", f, th, rgt(YYAW) * 0.3 + fwd(YYAW) * 0.5 + V((0, 0, -0.4)), V((0, 0, -1)) + fwd(YYAW) * 0.3, pole=wpos(n, "upperarm01.L", f) - rgt(YYAW) * 0.4 - fwd(YYAW) * 0.2, pose="relaxed")
        sh = wpos(n, "upperarm01.R", f)
        rest = sh + V((0, 0, -0.55)) + fwd(YYAW) * 0.05 + rgt(YYAW) * 0.05
        tgt = V((TROUGH.x + 0.12, TROUGH.y - 0.55, TROUGH.z + 0.17))
        p = rest.lerp(tgt, ss(u)) + V((0, 0, 0.004 * math.sin(f)))
        hand(n, "R", f, p, V((0, 0, -1)), fwd(YYAW) + V((0, 0, -0.9)), pole=sh + rgt(YYAW) * 0.4 + V((0, 0, -0.2)), pose="point" if u > 0.5 else "relaxed")
def shot_1a(f0, n):
    """young hermit at the stone trough: leans in, his right hand reaches toward the water and stops just above it"""
    light(f0); trough_reach("AmouY", f0, n)
    camera("1a", f0, n, [(0, (-1.55, -3.35, 1.3), (YP.x + 0.1, YP.y + 0.2, 1.15), 30), (1, (-1.6, -3.5, 1.25), (YP.x + 0.1, YP.y + 0.25, 1.1), 30)])
    return ("AmouY",)

def shot_1b(f0, n):
    """he pulls back, straightens and turns away from the water shaking his head"""
    use = ("AmouY",); f1 = f0 + n - 1; light(f0)
    for k, f in enumerate(range(f0, f1 + 1, 12)):
        u = ss((f - f0) / 40.0)
        yw = YYAW - 125 * u; shake = 16 * math.sin((f - f0) / 7.0) * (1 if f - f0 > 25 else 0) * (1 - ss((f - f0 - 80) / 30.0))
        stand("AmouY", f, YP, yw, head=(-4 + 8 * (1 - u), shake), spine=(12 * (1 - u) + 2, 0, 0), flex=6 * (1 - u))
    camera("1b", f0, n, [(0, (YP.x + 1.35, YP.y - 1.25, 1.62), (YP.x, YP.y, 1.52), 40), (1, (YP.x + 1.2, YP.y - 1.1, 1.62), (YP.x, YP.y, 1.54), 40)])
    return use

# ================================================================== BEAT 2: for 60 years he refused to wash (young -> old)
LP = V((0.0, 0.5, 0))
def portrait(n, f0, n_fr, c0, c1, lens=40):
    f1 = f0 + n_fr - 1
    for k, f in enumerate(range(f0, f1 + 1, 30)):
        stand(n, f, LP, 0.0, head=(1.5 * (k % 2), -8 + 4 * k), spine=(3 + 1.5 * (k % 2), 0, 0), dz=0.004 * (k % 2))
    hz = RIG[n].BN["head"].head_local.z + 0.06
    camera(n + f0.__str__(), f0, n_fr, [(0, (LP.x + c0[0], LP.y + c0[1], hz), (LP.x, LP.y, hz - 0.03), lens), (1, (LP.x + c1[0], LP.y + c1[1], hz), (LP.x, LP.y, hz - 0.03), lens)])
def shot_2a(f0, n):
    light(f0); portrait("AmouY", f0, n, (0.95, -1.35), (0.55, -1.55)); return ("AmouY",)
def shot_2b(f0, n):
    light(f0); portrait("AmouO", f0, n, (0.55, -1.55), (0.1, -1.62)); return ("AmouO",)
def shot_2c(f0, n):
    """old hermit at the same trough: looks at the water, turns his body and head away, a palm raised 'no'"""
    use = ("AmouO",); f1 = f0 + n - 1; light(f0)
    for f in range(f0, f1 + 1, 10):
        u = ss((f - f0 - 20) / 35.0); g = ss((f - f0 - 30) / 20.0) * (1 - ss((f - f0 - 95) / 20.0))
        yw = YYAW - 80 * u
        stand("AmouO", f, YP, yw, head=(12 * (1 - u) - 6 * u, -25 * u), spine=(8 * (1 - u) + 2, 0, 0), arms=False)
        relaxed_arm("AmouO", "L", f, yw)
        sh = wpos("AmouO", "upperarm01.R", f)
        rest = sh + V((0, 0, -0.55)) + fwd(yw) * 0.05 + rgt(yw) * 0.05
        up = sh + fwd(YYAW) * 0.30 + V((0, 0, -0.2)) + rgt(yw) * 0.08
        p = rest.lerp(up, g)
        hand("AmouO", "R", f, p, fwd(YYAW) * g + V((0, 0, -1)) * (1 - g) - rgt(yw) * 0.3, V((0, 0, 1)) * g + V((0, 0, -1)) * (1 - g) + fwd(yw) * 0.3,
             pole=sh + rgt(yw) * 0.35 + V((0, 0, -0.35)), pose="flat_palm")
    camera("2c", f0, n, [(0, (YP.x + 1.6, YP.y - 0.2, 1.5), (YP.x, YP.y + 0.1, 1.35), 32), (1, (YP.x + 1.5, YP.y - 0.45, 1.5), (YP.x, YP.y + 0.1, 1.37), 32)])
    return use

# ================================================================== BEAT 3: the dirt kept him healthy
FP = V((0.3, -2.0, 0)); FYAW = 8.0
def shot_3a(f0, n):
    """in the lane he flexes both arms like a strongman, pumping twice, chest out"""
    use = ("AmouO",); f1 = f0 + n - 1; light(f0)
    for f in range(f0, f1 + 1, 6):
        g = ss((f - f0 - 10) / 25.0); pump = 0.03 * math.sin((f - f0) / 9.0) * g
        stand("AmouO", f, FP, FYAW, head=(-6 * g, 6 * math.sin((f - f0) / 30.0)), spine=(-5 * g + 2, 0, 0), arms=False, dz=pump * 0.2)
        for s in "LR":
            sx = 1 if s == "L" else -1
            sh = wpos("AmouO", "upperarm01." + s, f); out = -rgt(FYAW) * sx
            rest = sh + V((0, 0, -0.55)) + out * 0.07 + fwd(FYAW) * 0.04
            flex_p = sh + out * 0.36 + V((0, 0, 0.12 + pump)) + fwd(FYAW) * 0.05
            p = rest.lerp(flex_p, g)
            nrm = (-out * g + out * 0.2 * (1 - g) + V((0, 0, -1)) * (1 - g)).normalized()
            fd = (V((0, 0, 1)) * g + V((0, 0, -1)) * (1 - g) - out * 0.3 * g).normalized()
            hand("AmouO", s, f, p, nrm, fd, pole=sh + out * 0.5 + V((0, 0, -0.45 * g - 0.2)) - fwd(FYAW) * 0.2, pose="power_fist" if g > 0.5 else "relaxed")
    camera("3a", f0, n, [(0, (FP.x + 0.4, FP.y - 3.4, 0.85), (FP.x, FP.y, 1.25), 28), (1, (FP.x + 0.3, FP.y - 2.7, 0.95), (FP.x, FP.y, 1.3), 28)])
    return use

def shot_3b(f0, n):
    """a villager by the shop crates (our logo) watches him and shakes his head"""
    use = ("V1",); f1 = f0 + n - 1; light(f0)
    VP = V((2.05, -3.45, 0)); yw = yaw_to(VP, FP) + 10
    for f in range(f0, f1 + 1, 8):
        u = ss((f - f0) / 50.0)
        stand("V1", f, VP, yw - 25 * (1 - u), head=(4 + 6 * u, -20 * (1 - u) + 14 * math.sin((f - f0) / 8.0) * ss((f - f0 - 45) / 15.0)), spine=(4 + 5 * u, -10 * (1 - u), 0), flex=2 * u)
    camera("3b", f0, n, [(0, (-0.75, -4.6, 1.5), (2.4, -2.8, 1.15), 30), (1, (-0.05, -4.05, 1.45), (2.35, -2.75, 1.2), 30)])
    return use

# ================================================================== BEAT 4: he left his home
def walk_shot(n, f0, f1, pts, speed=1.15, head=(-4, 0)):
    """walk along a polyline at constant speed (1x), arms swinging; returns the path"""
    P = [V(p) for p in pts]; seg = [(b - a).length for a, b in zip(P, P[1:])]; tot = sum(seg)
    def path(f):
        d = min(tot, max(0.0, (f - f0) / 60.0 * speed));
        for a_, b_, L in zip(P, P[1:], seg):
            if d <= L: return a_.lerp(b_, d / L)
            d -= L
        return P[-1].copy()
    def yawf(f):
        a_ = path(f - 6); b_ = path(f + 6)
        if (b_ - a_).length < 1e-4: a_, b_ = P[-2], P[-1]
        return yaw_to(a_, b_)
    HUM[n].walk(path, yawf, f0, f1, stride=0.66, lift=0.07)
    for f in range(f0, f1 + 1, 12): HUM[n].key_spine(f, flex=5, twist=0, head=(head[0], head[1] + 6 * math.sin(f / 20.0)))
    walk_arms(n, f0, f1, yawf)
    return path
def shot_4a(f0, n):
    """he steps out through the open door of his house into the lane"""
    use = ("AmouO",); f1 = f0 + n - 1; light(f0)
    walk_shot("AmouO", f0, f1, [(3.75, 2.6, 0), (3.0, 2.55, 0), (1.6, 1.7, 0), (1.0, 0.6, 0)])
    camera("4a", f0, n, [(0, (1.0, 0.6, 1.5), (3.6, 2.55, 1.25), 28), (1, (0.4, -0.6, 1.5), (1.4, 1.3, 1.15), 28)])
    return use
def shot_4b(f0, n):
    """he walks down the lane toward the village edge, past the houses"""
    use = ("AmouO",); f1 = f0 + n - 1; light(f0)
    path = walk_shot("AmouO", f0, f1, [(1.0, 0.0, 0), (0.6, -4.0, 0)])
    camera("4b", f0, n, [(0, (-0.7, -5.0, 1.45), (0.9, -0.2, 1.1), 26), (1, (-0.9, -6.4, 1.45), (0.65, -2.2, 1.1), 26)])
    return use

# ================================================================== BEAT 5: dug a shallow hole
def shot_5a(f0, n):
    """he kneels at the pit's edge and scoops the loose soil out of the hollow with both hands"""
    use = ("AmouO",); f1 = f0 + n - 1; light(f0)
    kn = V((PIT.x + 0.05, PIT.y - 0.56, 0)); yw = 180.0
    for f in range(f0, f1 + 1, 6):
        ph = (f - f0) / 34.0 * 2 * math.pi
        kneel("AmouO", f, kn, yw, lean=34, spine=(40, 0, 0), head=(-14, 4 * math.sin(ph / 2)))
        for s in "LR":
            sx = 1 if s == "L" else -1
            reach = 0.12 + 0.1 * (0.5 + 0.5 * math.cos(ph + (0 if s == "L" else 0.6)))
            x = kn.x - rgt(yw).x * sx * 0.16; y = kn.y + reach + 0.1
            p = V((x, y, pit_z(x, y) + 0.03 + 0.04 * max(0, math.sin(ph))))
            hand("AmouO", s, f, p, V((0, -0.3, -1)), fwd(yw) + V((0, 0, -0.5)), pole=wpos("AmouO", "upperarm01." + s, f) - rgt(yw) * sx * 0.4 + V((0, 0, -0.3)), pose="cup_hold")
    camera("5a", f0, n, [(0, (PIT.x - 0.9, PIT.y + 1.9, 0.75), (PIT.x + 0.05, PIT.y - 0.5, 0.6), 28), (1, (PIT.x - 0.7, PIT.y + 1.75, 0.72), (PIT.x + 0.05, PIT.y - 0.5, 0.6), 28)])
    return use
def shot_5b(f0, n):
    """he lies on his back in the shallow pit, head on the folded blanket, breathing; the camera cranes up"""
    use = ("AmouO",); f1 = f0 + n - 1; light(f0)
    yw = 90.0                                 # head toward -x
    for k, f in enumerate(range(f0, f1 + 1, 20)):
        b = 0.006 * (k % 2)
        root = V((PIT.x + 0.15, PIT.y, pit_z(PIT.x + 0.15, PIT.y) + 0.115 + b))
        body("AmouO", f, root, yw, flex=-84.0, spine=(-4, 0, 0), head=(12, 18 * ss((f - f0) / 60.0)))
        for s in "LR":
            sx = 1 if s == "L" else -1
            ax = PIT.x + 0.98; ay = PIT.y - rgt(yw).y * sx * 0.13
            foot("AmouO", s, f, (ax, ay, pit_z(ax, ay) + 0.07), yw, pitch=-80.0, knee=V((ax - 0.4, ay, 0.6)))
            belly = root + V((-0.22, -rgt(yw).y * sx * 0.06, 0.13 + b))
            hand("AmouO", s, f, belly, V((0, 0, -1)), V((0, -rgt(yw).y * sx, 0)) * -1 + V((0.3, 0, 0)), pole=belly + V((0, -rgt(yw).y * sx * 0.45, 0.05)), pose="relaxed")
    camera("5b", f0, n, [(0, (PIT.x + 0.3, PIT.y - 1.7, 2.3), (PIT.x - 0.2, PIT.y, -0.05), 26), (1, (PIT.x + 0.35, PIT.y - 1.6, 2.75), (PIT.x - 0.15, PIT.y, -0.05), 26)])
    return use

# ================================================================== BEAT 6: he ate only roadkill
def shot_6a(f0, n):
    """on the dirt road verge he kneels by a dead hare and studies it, leaning in"""
    use = ("AmouO",); f1 = f0 + n - 1; light(f0)
    kn = V((HARE.x + 0.05, HARE.y - 0.55, 0)); yw = 180.0
    for f in range(f0, f1 + 1, 10):
        u = ss((f - f0) / 50.0)
        kneel("AmouO", f, kn, yw, lean=12 + 14 * u, spine=(12 + 16 * u, 0, 0), head=(22 + 8 * u, 6 * math.sin((f - f0) / 25.0)))
        for s in "LR":
            sx = 1 if s == "L" else -1
            th = kn + fwd(yw) * 0.08 - rgt(yw) * sx * 0.14 + V((0, 0, 0.36))
            hand("AmouO", s, f, th, V((0, 0, -1)) + fwd(yw) * 0.3, fwd(yw) + V((0, 0, -0.6)), pole=wpos("AmouO", "upperarm01." + s, f) - rgt(yw) * sx * 0.4 - fwd(yw) * 0.2, pose="relaxed")
    camera("6a", f0, n, [(0, (HARE.x - 1.1, HARE.y + 1.35, 0.95), (HARE.x + 0.0, HARE.y - 0.35, 0.45), 30), (1, (HARE.x - 0.95, HARE.y + 1.15, 0.9), (HARE.x + 0.0, HARE.y - 0.35, 0.45), 30)])
    return use
def sit_fire(n, f, head=(10, 0), lean=8.0, hands=True, spine=(10, 0, 0)):
    root = sit(n, f, SEAT, SEAT_Z + 0.03 + 0.003 * max(0.0, lean - 8.0), 0.0, lean=lean, spine=spine, head=head, knee_fwd=0.5)
    if hands: thighs_hands(n, f, 0.0, root)
    return root
def shot_6b(f0, n):
    """at his campfire a lump of meat roasts on a spit; he leans in and sniffs it, nodding"""
    use = ("AmouO",); f1 = f0 + n - 1; light(f0)
    for f in range(f0, f1 + 1, 10):
        u = ss((f - f0) / 45.0) * (1 - ss((f - f0 - 100) / 30.0))
        sit_fire("AmouO", f, head=(14 + 10 * u + 5 * math.sin((f - f0) / 9.0) * u, 0), lean=8 + 14 * u, spine=(10 + 10 * u, 0, 0))
    camera("6b", f0, n, [(0, (FIRE.x + 1.1, FIRE.y - 2.0, 1.25), (SEAT.x - 0.05, SEAT.y - 0.35, 0.8), 32), (1, (FIRE.x + 0.95, FIRE.y - 1.8, 1.2), (SEAT.x - 0.05, SEAT.y - 0.35, 0.82), 32)])
    return use

# ================================================================== BEAT 7: smoked animal dung in a pipe
def shot_7a(f0, n):
    """insert: dried dung cakes on a flat rock beside his pipe; a wisp of smoke rises from the bowl"""
    use = (); f1 = f0 + n - 1; light(f0)
    PIPE.location = (FLAT.x + 0.12, FLAT.y - 0.15, top_z(OB["D_FlatRock"]) - 0.003); PIPE.rotation_euler = (0, 0, R_(25))
    PIPE.keyframe_insert("location", frame=f0); PIPE.keyframe_insert("rotation_euler", frame=f0)
    bpy.context.view_layer.update(); bt = PIPE.matrix_world @ BOWL_TOP
    puffs(lambda f: bt, f0, f1, every=24, rise=0.16, grow=1.2, life=60, count=4)
    camera("7a", f0, n, [(0, (FLAT.x + 0.45, FLAT.y - 0.75, 0.62), (FLAT.x + 0.0, FLAT.y - 0.05, 0.2), 40), (1, (FLAT.x + 0.38, FLAT.y - 0.62, 0.55), (FLAT.x + 0.0, FLAT.y - 0.05, 0.2), 40)], fstop=11)
    return use
def shot_7b(f0, n):
    """seated by the fire he holds the pipe in his right fingers, stem at his lips; he puffs, lowers it, exhales smoke"""
    use = ("AmouO",); f1 = f0 + n - 1; light(f0)
    keys = [(f0 + i, (10, 0)) for i in range(0, n, 15)] + [(f1, (10, 0))]
    for f, hd in keys:
        root = sit_fire("AmouO", f, head=(4, -6), lean=6, hands=False, spine=(6, 0, 0))
        hand("AmouO", "L", f, root + fwd(0) * 0.3 - rgt(0) * 0.13 + V((0, 0, 0.09)), V((0, 0, -1)), fwd(0) + V((0, 0, -0.3)), pole=wpos("AmouO", "upperarm01.L", f) - rgt(0) * 0.35 - fwd(0) * 0.25, pose="relaxed")
    p = prop_copy("Pipe", "Pipe_7b", f0, f1); key_vis(PIPE, 1, True); key_vis(PIPE, f0, False); key_vis(PIPE, f1 + 1, True)
    m0 = mouth("AmouO", f0); hf = head_fwd("AmouO", f0)
    tip = m0 + hf * 0.026                                            # mouthpiece just at the lips, never inside
    bowl_t = m0 + hf * 0.075 + V((0, 0, -0.10)) + rgt(0) * 0.02
    place_pipe(p, tip, (bowl_t - tip).normalized())
    bpy.context.view_layer.update()
    bowl_w = p.matrix_world @ BOWL_L
    npalm = (-rgt(0) * 0.9 + V((0, 0, -0.2))).normalized()             # the hand comes from his right; thumb and index pinch the stem shank
    shank = bowl_w.lerp(tip, 0.48)
    sh = wpos("AmouO", "upperarm01.R", f0)
    hand("AmouO", "R", f0, shank - npalm * 0.03, npalm, (hf * 0.8 + V((0, 0, -0.3))).normalized(), pole=sh + V((0, 0, -0.4)) + rgt(0) * 0.3 - fwd(0) * 0.1, pose=None)
    sc.frame_set(f0); bpy.context.view_layer.update()
    grip_object(OB["AmouO"], "R", f0, p, shank, npalm, finger_dir=(hf * 0.8 + V((0, 0, -0.3))).normalized(), grip="pinch")
    M0 = ik_mat("AmouO", "R", f0); child_of(p, "AmouO", "wrist.R", f0)
    for pb_ in OB["AmouO"].pose.bones:          # middle/ring/little fingers curl loosely below the stem (never into it)
        if pb_.name.endswith(".R") and pb_.name.split("-")[0] in ("finger3", "finger4", "finger5") and "-" in pb_.name and pb_.name[-3] in "123":
            pb_.rotation_quaternion = Quaternion().slerp(pb_.rotation_quaternion, 0.12 if pb_.name.startswith("finger3") else 0.45); pb_.keyframe_insert("rotation_quaternion", frame=f0, group=pb_.name)
    _fing = {pb.name: pb.rotation_quaternion.copy() for pb in OB["AmouO"].pose.bones if pb.name.endswith(".R") and ("finger" in pb.name or "metacarpal" in pb.name)}
    piv = bowl_w; down = V((0, 0, -0.15)) + hf * 0.06
    for f, u in ((f0 + 40, 0.0), (f0 + 65, 1.0), (f0 + 105, 1.0), (f0 + 130, 0.0), (f1, 0.0)):
        key_ik("AmouO", "R", f, rigid(piv, Rx(-15 * u), down * u) @ M0)
        sh = wpos("AmouO", "upperarm01.R", f); elbow("AmouO", "R", f, sh + V((0, 0, -0.4)) + rgt(0) * 0.3 - fwd(0) * 0.1)
        for nm_, q_ in _fing.items():
            pb_ = OB["AmouO"].pose.bones[nm_]; pb_.rotation_quaternion = q_; pb_.keyframe_insert("rotation_quaternion", frame=f, group=nm_)
    mo = mouth("AmouO", f0 + 70)
    puffs(lambda f: mo + hf * 0.05 + V((0, 0, -0.02)), f0 + 66, f1, every=10, rise=0.15, drift=hf * 0.15, grow=2.5, life=45, count=5)
    camera("7b", f0, n, [(0, (SEAT.x + 0.75, SEAT.y - 1.5, 1.3), (SEAT.x, SEAT.y - 0.05, 1.2), 40), (1, (SEAT.x + 0.65, SEAT.y - 1.38, 1.28), (SEAT.x, SEAT.y - 0.05, 1.22), 40)])
    return use

# ================================================================== BEAT 8: burned his hair over a fire instead of cutting it
def beard_tip(f):
    sc.frame_set(int(f)); bpy.context.view_layer.update(); o = OB["AmouO.beard"]
    pts = [o.matrix_world @ V(c) for c in o.bound_box]
    zmin = min(p.z for p in pts); cx = sum(p.x for p in pts) / 8; cy = min(p.y for p in pts)
    return V((cx, cy + 0.03, zmin + 0.03))
def shot_8a(f0, n):
    """seated, he holds a smouldering twig in his right hand to the very ends of his beard: a small singe and smoke, no flame near the face"""
    use = ("AmouO",); f1 = f0 + n - 1; light(f0)
    for f in list(range(f0, f1 + 1, 20)) + [f1]:
        root = sit_fire("AmouO", f, head=(24, -8), lean=6, hands=False, spine=(8, 0, 0))
        hand("AmouO", "L", f, root + fwd(0) * 0.3 - rgt(0) * 0.13 + V((0, 0, 0.09)), V((0, 0, -1)), fwd(0) + V((0, 0, -0.3)), pole=wpos("AmouO", "upperarm01.L", f) - rgt(0) * 0.35 - fwd(0) * 0.25, pose="relaxed")
    t = prop_copy("Twig", "Twig_8a", f0, f1)
    bt = beard_tip(f0)
    d = (V((0, 0, 0)) + rgt(0) * 1.0 + fwd(0) * 0.35 + V((0, 0, -0.15))).normalized()      # twig runs from the beard tip out to his right hand
    tipw = bt + rgt(0) * 0.015 + fwd(0) * 0.02
    xw = -d; zw = V((0, 0, 1)); zw = (zw - xw * zw.dot(xw)).normalized(); yw = zw.cross(xw)
    t.matrix_world = Matrix.Translation(tipw - xw * 0.21) @ Matrix((xw, yw, zw)).transposed().to_4x4()
    bpy.context.view_layer.update()
    grip_pt = t.matrix_world @ V((-0.13, 0, 0))
    sh = wpos("AmouO", "upperarm01.R", f0); elbow("AmouO", "R", f0, sh + V((0, 0, -0.45)) + rgt(0) * 0.3)
    M0 = hold_prop("AmouO", "R", f0, t, grip_pt, (V((0, 0, 1)) + rgt(0) * 0.4).normalized(), fwd(0), "pinch")
    piv = grip_pt
    for f, u in ((f0 + 30, 0.0), (f0 + 60, 1.0), (f0 + 85, 0.3), (f0 + 105, 1.0), (f1, 0.6)):
        key_ik("AmouO", "R", f, rigid(piv, Matrix.Identity(3), rgt(0) * 0.03 * (1 - u)) @ M0)
        sh = wpos("AmouO", "upperarm01.R", f); elbow("AmouO", "R", f, sh + V((0, 0, -0.45)) + rgt(0) * 0.3)
    key_ik("AmouO", "R", f0, M0)
    puffs(lambda f: beard_tip(f0) + V((0, 0, 0.0)), f0 + 50, f1, every=12, rise=0.15, drift=rgt(0) * 0.06, grow=2.0, life=40, count=6)
    camera("8a", f0, n, [(0, (SEAT.x - 1.05, SEAT.y - 1.25, 1.15), (SEAT.x - 0.2, SEAT.y - 0.2, 0.98), 34), (1, (SEAT.x - 0.95, SEAT.y - 1.12, 1.12), (SEAT.x - 0.2, SEAT.y - 0.2, 1.0), 34)])
    return use
def shot_8b(f0, n):
    """wide: the hermit at his fire by the pit, smoke drifting from the singed beard ends"""
    use = ("AmouO",); f1 = f0 + n - 1; light(f0)
    for f in range(f0, f1 + 1, 25):
        sit_fire("AmouO", f, head=(20, 10 * math.sin((f - f0) / 30.0)), lean=10, spine=(12, 0, 0))
    puffs(lambda f: beard_tip(f0), f0, f1, every=14, rise=0.3, drift=rgt(0) * 0.1, grow=4, life=50, count=6)
    camera("8b", f0, n, [(0, (DX - 0.4, 0.6, 1.7), (SEAT.x, SEAT.y - 0.4, 0.7), 24), (1, (DX - 0.8, 0.9, 1.6), (SEAT.x, SEAT.y - 0.4, 0.7), 24)])
    return use

# ================================================================== BEAT 9: the dirtiest man in the world
HP9 = V((0.0, 4.5, 0))
def shot_9a(f0, n):
    use = ("AmouO",); f1 = f0 + n - 1; light(f0)
    for k, f in enumerate(range(f0, f1 + 1, 30)):
        stand("AmouO", f, HP9, 0.0, head=(-6 + 1.5 * (k % 2), 4 * math.sin(k)), spine=(-2, 0, 0), dz=0.004 * (k % 2))
    flies("AmouO", f0, f1)
    camera("9a", f0, n, [(0, (0.25, HP9.y - 3.0, 0.95), (0, HP9.y, 1.45), 30), (1, (0.18, HP9.y - 2.1, 1.1), (0, HP9.y, 1.5), 30)])
    return use
def shot_9b(f0, n):
    use = ("AmouO",); f1 = f0 + n - 1; light(f0)
    for k, f in enumerate(range(f0, f1 + 1, 30)):
        stand("AmouO", f, HP9, 0.0, head=(-4, -10 - 6 * k), spine=(-2, 0, 0), dz=0.004 * (k % 2))
    flies("AmouO", f0, f1)
    ks = []
    for i in range(5):
        a_ = R_(-90 - 22 * i); r = 2.3
        ks.append((i / 4, (HP9.x + r * math.cos(a_), HP9.y + r * math.sin(a_), 1.45 + 0.08 * i), (HP9.x, HP9.y, 1.35), 26))
    camera("9b", f0, n, ks)
    return use

# ================================================================== BEAT 10: someone finally convinced him to take a bath
A10 = V((-1.15, 17.6, 0)); V10 = V((0.85, 17.6, 0))
def shot_10a(f0, n):
    """a villager talks to him and points an open hand toward the tub; the hermit looks at it and gives a reluctant nod"""
    use = ("AmouO", "V1"); f1 = f0 + n - 1; light(f0)
    ya = yaw_to(A10, V10); yv = yaw_to(V10, A10)
    for f in range(f0, f1 + 1, 8):
        look = ss((f - f0 - 40) / 20.0); nod = 8 * math.sin((f - f0 - 75) / 6.0) * (1 if 75 < f - f0 < 113 else 0)
        stand("AmouO", f, A10, ya - 25, head=(4 + 8 * look + nod, 20 - 45 * look))
        g = ss((f - f0 - 15) / 20.0) * (1 - ss((f - f0 - 100) / 20.0))
        stand("V1", f, V10, yv + 20, head=(2, -10 - 25 * g), spine=(3, -10 * g, 0), arms=False)
        relaxed_arm("V1", "L", f, yv)
        sh = wpos("V1", "upperarm01.R", f)
        dirt = (TUBP + V((0, 0.6, 0)) - V10); dirt.z = 0
        rest = sh + V((0, 0, -0.55)) + rgt(yv) * 0.05 + fwd(yv) * 0.04
        out = sh + dirt.normalized() * 0.40 + V((0, 0, -0.18)) + rgt(yv) * 0.1
        hand("V1", "R", f, rest.lerp(out, g), V((0, 0, -1)) * (1 - g) + V((0, 0, -1)) * g * -1, (V((0, 0, -1)) * (1 - g) + dirt * g).normalized(),
             pole=sh + V((0, 0, -0.4)) + rgt(yv) * 0.4 - fwd(yv) * 0.2, pose="flat_palm")
    camera("10a", f0, n, [(0, (-0.35, 13.9, 1.55), (-0.15, 17.8, 1.25), 28), (1, (-0.15, 14.3, 1.55), (-0.15, 17.8, 1.27), 28)])
    return use
TUBO = OB["V_Tub"]
_tb = [TUBO.matrix_world @ v.co for v in TUBO.data.vertices]
TUB_X0, TUB_X1 = min(p.x for p in _tb), max(p.x for p in _tb); TUB_Y0, TUB_Y1 = min(p.y for p in _tb), max(p.y for p in _tb); TUB_Z1 = max(p.z for p in _tb)
LONG_X = (TUB_X1 - TUB_X0) > (TUB_Y1 - TUB_Y0)
def shot_10b(f0, n):
    """he sits in the tin tub, water to his chest; the villager behind him has both hands resting on his shoulders and rubs gently"""
    use = ("AmouO", "V1", "V2"); f1 = f0 + n - 1; light(f0)
    if LONG_X:
        yw = 90.0; seat = V((TUB_X0 + 0.44, (TUB_Y0 + TUB_Y1) / 2, 0)); vpos = V((TUB_X0 - 0.34, seat.y, 0)); ax = 'x'
    else:
        yw = 180.0; seat = V(((TUB_X0 + TUB_X1) / 2, TUB_Y0 + 0.42, 0)); vpos = V((seat.x, TUB_Y0 - 0.38, 0)); ax = 'y'
    for k, f in enumerate(range(f0, f1 + 1, 10)):
        root = V((seat.x, seat.y, 0.10 + HUM["AmouO"].root_head.z - RIG["AmouO"].BN["upperleg01.L"].head_local.z + 0.02))
        body("AmouO", f, root, yw, flex=4, spine=(8, 0, 0), head=(4 + 3 * math.sin((f - f0) / 20.0), -10 + 6 * math.sin((f - f0) / 35.0)))
        for s in "LR":
            sx = 1 if s == "L" else -1
            ank = root + fwd(yw) * 0.72 - rgt(yw) * sx * 0.11; ank.z = 0.16
            foot("AmouO", s, f, ank, yw, pitch=-40, knee=root + fwd(yw) * 0.4 - rgt(yw) * sx * 0.12 + V((0, 0, 0.8)))
            pp = root + fwd(yw) * 0.42 - rgt(yw) * sx * 0.12 + V((0, 0, 0.22))
            hand("AmouO", s, f, pp, V((0, 0, -1)), fwd(yw) + V((0, 0, -0.4)), pole=wpos("AmouO", "upperarm01." + s, f) - rgt(yw) * sx * 0.4 - fwd(yw) * 0.1, pose="relaxed")
        rub = 0.012 * math.sin((f - f0) / 8.0)
        kneel("V1", f, vpos, yw, thigh_back=0.0, lean=8, spine=(26, 0, 0), head=(24, 0))
        for s in "LR":
            sx = 1 if s == "L" else -1
            shA = wpos("AmouO", "upperarm01." + s, f) - rgt(yw) * sx * 0.05 + V((0, 0, 0.06)) + fwd(yw) * rub
            hand("V1", s, f, shA, V((0, 0, -1)), (fwd(yw) + V((0, 0, -0.5))).normalized(), pole=wpos("V1", "upperarm01." + s, f) - rgt(yw) * sx * 0.45 + V((0, 0, -0.3)), pose="relaxed")
        stand("V2", f, seat + fwd(yw) * 0.9 - rgt(yw) * 1.05, yaw_to(seat + fwd(yw) * 0.9 - rgt(yw) * 1.05, seat), head=(8, 4 * math.sin(k)))
    side = -rgt(yw) * -1
    cpos0 = seat + fwd(yw) * 1.9 + rgt(yw) * 0.9 + V((0, 0, 1.35)); cpos1 = seat + fwd(yw) * 1.7 + rgt(yw) * 0.75 + V((0, 0, 1.3))
    camera("10b", f0, n, [(0, cpos0, seat + V((0, 0, 0.85)), 30), (1, cpos1, seat + V((0, 0, 0.85)), 30)])
    return use

# ================================================================== BEAT 11: he died shortly after (off-screen)
def shot_11a(f0, n):
    """dusk: the empty pit, his pipe resting on the edge, the shovel standing in the mound"""
    use = (); f1 = f0 + n - 1; light(f0, dusk=True)
    p = prop_copy("Pipe", "Pipe_11", f0, f1)
    p.location = (PIT.x - 0.3, PIT.y - 0.52, pit_z(PIT.x - 0.3, PIT.y - 0.52)); p.rotation_euler = (0, 0, R_(70))
    p.keyframe_insert("location", frame=f0); p.keyframe_insert("rotation_euler", frame=f0)
    camera("11a", f0, n, [(0, (PIT.x + 1.6, PIT.y - 2.3, 1.15), (PIT.x - 0.1, PIT.y + 0.1, 0.0), 28), (1, (PIT.x + 1.25, PIT.y - 1.85, 1.0), (PIT.x - 0.1, PIT.y + 0.1, 0.0), 28)])
    return use
def shot_11b(f0, n):
    """dusk wide: two villagers stand quietly beyond the empty pit, heads bowed; slow pull back"""
    use = ("V1", "V2"); f1 = f0 + n - 1; light(f0, dusk=True)
    for k, f in enumerate(range(f0, f1 + 1, 30)):
        stand("V1", f, V((PIT.x - 0.45, PIT.y + 1.75, 0)), 8.0, head=(24 + 2 * (k % 2), 0), spine=(8, 0, 0), dz=0.003 * (k % 2))
        stand("V2", f, V((PIT.x + 0.55, PIT.y + 1.85, 0)), -6.0, head=(22 + 2 * ((k + 1) % 2), 0), spine=(8, 0, 0), dz=0.003 * ((k + 1) % 2))
    camera("11b", f0, n, [(0, (PIT.x + 0.4, PIT.y - 2.6, 1.3), (PIT.x, PIT.y + 1.6, 1.0), 30), (1, (PIT.x + 0.5, PIT.y - 3.4, 1.4), (PIT.x, PIT.y + 1.5, 1.0), 30)])
    return use

flame_flicker()
SHOT_FUNCS = {k[5:]: v for k, v in list(globals().items()) if k.startswith("shot_")}
