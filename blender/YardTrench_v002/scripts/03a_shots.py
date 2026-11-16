# exec'd by 03_anim.py: all 23 shots. World: house at +Y, worn line along path_x(y) from the porch (y=9) to the back fence (y=-12.5).
# A rig placed with yaw 0 faces -Y (toward the back fence); yaw 180 faces the house; yaw 90 faces +X.

def walk_path(H, fa, fb, y0, speed, dirn=-1, xoff=0.0, stride=0.72, lean=4):
    """walk along the worn line (world == local: rig placed at the origin, yaw 0). dirn -1 = toward the back fence.
    Facing follows the curve; arms swing in the body frame."""
    def P(f):
        y = y0 + dirn * speed * (f - fa) / FPS; return Vector((path_x(y) + xoff, y, 0))
    def Y(f):
        y = y0 + dirn * speed * (f - fa) / FPS; dx = (path_x(y + 0.05) - path_x(y - 0.05)) / 0.1
        d = Vector((dx * dirn, dirn, 0)).normalized(); return math.degrees(math.atan2(d.x, -d.y))
    path = framed(P)
    H.walk(path, Y, fa, fb, stride=stride, lift=0.07, bob=0.018, lean=lean)
    d = 0.0; prev = P(fa)
    for f in range(fa, fb + 1):
        p = P(f); d += (p - prev).to_2d().length; prev = p
        if (f - fa) % 2 and f != fb: continue
        ph = math.sin(2 * math.pi * d / stride); g = gz_local(p.x, p.y, f); Rz = Matrix.Rotation(R_(Y(f)), 3, 'Z')
        for s, sx, sg in (("L", 1, 1), ("R", -1, -1)):
            sh = H.r.BN["upperarm01." + s].head_local
            off = Vector((sh.x + 0.07 * sx, sh.y - 0.06 - 0.11 * ph * sg, 0))
            W = p + Rz @ off; W.z = g + sh.z - 0.52 + 0.04 * abs(ph)
            H.key_hand(s, f, W, Rz @ Vector((0, -0.25 * ph * sg - 0.08, -1)), Rz @ Vector((-sx, 0, 0)), pole=W + Rz @ Vector((0.3 * sx, 0.5, 0.3)))
    for s in "LR": apply_pose(H.r.o, s, "relaxed", fa)
    return P

def boy_at(s, x, y, yaw):
    put("Boy", s, (x, y, 0), yaw)

def bp(y): return Vector((path_x(y), y, 0))

# ================================================================== S1: the boy walks along the lawn line (front three-quarter)
s = "S1"; fa, fb = f0(s), fx(s)
env_ramp(s, dict(rut=0.0, groove=0.0, trench=0.0, bare=0.12, dry=0.0, wet=0.0, halfw=0.42, crush=0.25), dict(bare=0.15, crush=0.3))
key_light(fa)
put("Boy", s, (0, 0, 0), 0)
P1 = walk_path(BOY, fa, fb, 4.6, 1.25)
blinks(BOY, fa, fb, lid=-4)
for f in frs(fa, fb, 30): BOY.key_spine(f, flex=4, twist=0, head=(2, -10))
ya, yb = 4.6, 4.6 - 1.25 * (fb - fa) / FPS
camshot(s, [(0.0, (path_x(ya) + 1.5, ya - 2.6, 1.05), (path_x(ya) + 0.1, ya, 1.05), 32),
            (1.0, (path_x(yb) + 1.4, yb - 2.3, 1.0), (path_x(yb) + 0.1, yb, 1.05), 32)])

# ================================================================== S2: top-down, the same line wearing bare under his steps (time-lapse)
s = "S2"; fa, fb = f0(s), fx(s)
env_ramp(s, dict(bare=0.25, crush=0.5), dict(bare=0.7, crush=0.9))
put("Boy", s, (0, 0, 0), 0)
walk_path(BOY, fa, fb, 3.0, 1.3)
blinks(BOY, fa, fb, lid=-4)
camshot(s, [(0.0, *top((path_x(2.4), 2.4), 7.0), 35), (1.0, *top((path_x(-0.6), -0.6), 7.4), 35)])

# ================================================================== S3: high aerial of the yard and house; the worn strip; boy small on it
s = "S3"; fa, fb = f0(s), fx(s)
env_ramp(s, dict(bare=0.72, crush=0.9), dict(bare=0.9, crush=1.0))
put("Boy", s, (0, 0, 0), 0)
walk_path(BOY, fa, fb, 0.5, 1.3)
camshot(s, [(0.0, *top((0.0, -0.5), 24.0, 0.1), 30), (1.0, *top((0.0, -0.8), 29.0, 0.1), 30)])

# ================================================================== S4: shoe level, his sneakers walk away toward the house over flattened grass
s = "S4"; fa, fb = f0(s), fx(s)
env_ramp(s, dict(bare=0.3, crush=0.55, halfw=0.42), dict(bare=0.32, crush=0.62))
put("Boy", s, (0, 0, 0), 0)
P4 = walk_path(BOY, fa, fb, -0.9, 0.95, dirn=1, stride=0.66)
blinks(BOY, fa, fb, lid=-4)
camshot(s, [(0.0, (path_x(-2.6) + 0.3, -2.6, 0.16), (path_x(0.5) - 0.05, 0.5, 0.62), 26),
            (1.0, (path_x(-2.4) + 0.28, -2.4, 0.2), (path_x(1.5) - 0.05, 1.5, 0.75), 26)])

# ================================================================== S5: side, low: a shoe presses the blades flat
s = "S5"; fa, fb = f0(s), fx(s)
env_ramp(s, dict(bare=0.33, crush=0.62), dict(bare=0.36, crush=0.7))
put("Boy", s, (0, 0, 0), 0)
walk_path(BOY, fa, fb, -1.2, 0.8, dirn=1, stride=0.62)
yc0, yc1 = -1.0, -1.2 + 0.8 * (fb - fa) / FPS
camshot(s, [(0.0, (path_x(yc0) + 1.2, yc0 - 0.15, 0.32), (path_x(yc0), yc0, 0.2), 32),
            (1.0, (path_x(yc1) + 1.2, yc1 - 0.15, 0.32), (path_x(yc1), yc1, 0.2), 32)])

# ================================================================== S6: cut-away block of lawn + soil; he walks across, the clods squash
s = "S6"; fa, fb = f0(s), fx(s)
SXB = 100.0
put("Boy", s, (SXB - 0.55, 0.0, 0.0), 90)                    # walks toward +X along local -Y
walk_line(BOY, fa, fb, (0.0, 0.0), 0.6, stride=0.55)
blinks(BOY, fa, fb, lid=-4)
CL = [o for o in OB if o.name.startswith("Clod_")]
for o in CL:
    ix = int(o.name.split("_")[1]); iz = int(o.name.split("_")[2])
    xw = o.location.x; tpass = (xw - (SXB - 0.55)) / 0.6; fp = fa + int(tpass * FPS)
    k = (0.55 + 0.45 * iz / 2)                                 # top layer squashes most
    o.rotation_mode = 'XYZ'
    o.scale = (1.0, 1.0, 0.82); o.keyframe_insert("scale", frame=fa); o.keyframe_insert("scale", frame=max(fa, fp - 2))
    o.keyframe_insert("location", frame=fa); o.keyframe_insert("location", frame=max(fa, fp - 2))
    o.scale = (1.0 + 0.14 * k, 1.0 + 0.1 * k, 0.82 - 0.22 * k); o.keyframe_insert("scale", frame=fp + 12)
    loc0 = o.location.copy(); o.location = (loc0.x, loc0.y, loc0.z - 0.035 * iz * k); o.keyframe_insert("location", frame=fp + 12)
    o.location = loc0
camshot(s, [(0.0, (SXB - 0.4, -2.6, 0.66), (SXB - 0.4, 0.0, 0.62), 46), (1.0, (SXB + 0.25, -2.5, 0.66), (SXB + 0.25, 0.0, 0.62), 46)])

# ================================================================== S7: top-down close: the strip goes bare (time-lapse, shadows sweep)
s = "S7"; fa, fb = f0(s), f1(s)
env_ramp(s, dict(rut=0.0, bare=0.55, crush=0.8, dry=0.0), dict(rut=0.6, bare=1.0, crush=1.0, dry=0.15))
key_light(fa, rz=-60); key_light(fb, rz=10)
camshot(s, [(0.0, *top((path_x(-3.0), -3.0), 2.7), 30), (1.0, *top((path_x(-3.4), -3.4), 2.4), 30)])

# ================================================================== S8: top-down closer: it dries hard and cracks (time-lapse)
s = "S8"; fa, fb = f0(s), f1(s)
env_ramp(s, dict(rut=0.6, dry=0.15), dict(rut=1.0, dry=1.0))
key_light(fa, rz=10); key_light(fa + (fb - fa) // 2, rz=70); key_light(fb, rz=-28)
camshot(s, [(0.0, *top((path_x(-4.2), -4.2), 1.9), 30), (1.0, *top((path_x(-4.6), -4.6), 1.35), 30)])

# ================================================================== S9: rain starts; the boy looks up, palm out
s = "S9"; fa, fb = f0(s), fx(s)
env_ramp(s, dict(rut=1.0, dry=1.0, bare=1.0, crush=1.0, wet=0.0), dict(wet=0.35))
key_light(fa, sun=1.1, sky=0.45)
BX9, BY9 = path_x(-2.0) + 0.95, -2.0
put("Boy", s, (0, 0, 0), 0)
key_rain(fa, True, (BX9, BY9 - 1.0, 0), 0.0); key_rain(fb, True, None, (fb - fa) / FPS)
for i, f in enumerate(frs(fa, fb, 20)):
    u = min(1.0, (f - fa) / 50)
    stand(BOY, f, (BX9, BY9), 0, flex=3, spine=2 - 6 * u, head=(4 - 30 * u, 6 * math.sin(i * 0.9)))
arms_hang(BOY, fa, (BX9, BY9))
ev(fa + 40)
# right hand rises to chest height, palm up, forearm forward (elbow bent ~90 deg), arm stays outside the body
for f, up in ((fa + 18, 0.0), (fa + 52, 1.0), (fb, 1.0)):
    sh = BOY.r.BN["upperarm01.R"].head_local
    W = Vector((BX9 + sh.x - 0.075 - 0.02 * up, BY9 + sh.y - 0.06 - 0.31 * up, sh.z - 0.52 + 0.36 * up))
    BOY.key_hand("R", f, W, Vector((0, -1, 0.1 * up)) if up > 0.5 else Vector((0, -0.12, -1)), Vector((0, 0, -1)) if up > 0.5 else Vector((1, 0, 0)),
                 pole=W + Vector((-0.4, 0.4, -0.25)))
apply_pose(BOY.r.o, "R", "relaxed", fa + 18); apply_pose(BOY.r.o, "R", "cup_hold", fa + 52)
blinks(BOY, fa, fb, lid=-2, every=70)
camshot(s, [(0.0, (BX9 + 0.35, BY9 - 2.4, 1.0), (BX9, BY9, 1.42), 35), (1.0, (BX9 + 0.3, BY9 - 1.9, 1.05), (BX9, BY9, 1.48), 35)])

# ================================================================== S10: he looks down at the hard strip in the rain (side-front)
s = "S10"; fa, fb = f0(s), fx(s)
env_ramp(s, dict(wet=0.35), dict(wet=0.6))
key_light(fa, sun=1.1, sky=0.45)
put("Boy", s, (0, 0, 0), 0)
key_rain(fa, True, (BX9, BY9 - 1.0, 0), 2.0); key_rain(fb, True, None, 2.0 + (fb - fa) / FPS)
for i, f in enumerate(frs(fa, fb, 20)):
    u = min(1.0, (f - fa) / 40)
    stand(BOY, f, (BX9, BY9), 0, flex=4, spine=6 + 4 * u, head=(14 + 14 * u, 22 + 4 * math.sin(i * 0.8)))
arms_hang(BOY, fa, (BX9, BY9)); arms_hang(BOY, fb, (BX9, BY9))
blinks(BOY, fa, fb, lid=-6, every=80)
camshot(s, [(0.0, (BX9 + 1.25, BY9 - 1.35, 1.32), (BX9 - 0.35, BY9 - 0.25, 0.85), 30), (1.0, (BX9 + 1.15, BY9 - 1.2, 1.28), (BX9 - 0.4, BY9 - 0.3, 0.8), 30)])

# ================================================================== S11-S12: water can't soak in: puddles collect on the crust
s = "S11"; fa, fb = f0(s), f1(s)
env_ramp(s, dict(wet=0.6), dict(wet=0.7))
key_light(fa, sun=1.1, sky=0.45)
key_rain(fa, True, (path_x(-4.5), -4.5, 0), 4.0); key_rain(fb, True, None, 4.0 + (fb - fa) / FPS)
key_water(fa, True, -0.041, 0.0); key_water(fb, True, -0.031, 0.3)
camshot(s, [(0.0, (path_x(-4.4) + 0.75, -5.2, 0.62), (path_x(-4.3), -4.3, 0.0), 30), (1.0, (path_x(-4.4) + 0.68, -5.05, 0.55), (path_x(-4.2), -4.2, 0.0), 30)])
s = "S12"; fa, fb = f0(s), f1(s)
env_ramp(s, dict(wet=0.7), dict(wet=0.8))
key_light(fa, sun=1.1, sky=0.45)
key_rain(fa, True, (path_x(-3.0), -3.0, 0), 6.0); key_rain(fb, True, None, 6.0 + (fb - fa) / FPS)
key_water(fa, True, -0.031, 0.3); key_water(fb, True, -0.016, 1.4)
camshot(s, [(0.0, (path_x(-6.5) + 1.1, -6.6, 1.75), (path_x(-3.0), -3.0, 0.0), 30), (1.0, (path_x(-6.0) + 1.0, -6.1, 1.55), (path_x(-2.5), -2.5, 0.0), 30)])

# ================================================================== S13-S14: it flows along the groove instead
s = "S13"; fa, fb = f0(s), f1(s)
env_ramp(s, dict(wet=0.85), dict(wet=0.9))
key_light(fa, sun=1.1, sky=0.45)
key_rain(fa, True, (path_x(-6.0), -6.0, 0), 8.0); key_rain(fb, True, None, 8.0 + (fb - fa) / FPS)
key_water(fa, True, -0.012, 1.4); key_water(fb, True, -0.010, 1.4 - 2.2 * (fb - fa) / FPS)
camshot(s, [(0.0, (path_x(-9.0) + 0.3, -9.0, 0.38), (path_x(-3.0), -3.0, 0.0), 32), (1.0, (path_x(-8.3) + 0.3, -8.3, 0.34), (path_x(-2.3), -2.3, 0.0), 32)])
s = "S14"; fa, fb = f0(s), f1(s)
env_ramp(s, dict(wet=0.9), dict(wet=0.9))
key_light(fa, sun=1.1, sky=0.45)
key_rain(fa, True, (path_x(-5.0), -5.0, 0), 10.0); key_rain(fb, True, None, 10.0 + (fb - fa) / FPS)
key_water(fa, True, -0.010, -4.0); key_water(fb, True, -0.010, -4.0 - 2.2 * (fb - fa) / FPS)
camshot(s, [(0.0, *top((path_x(-4.0), -4.0), 2.2), 30), (1.0, *top((path_x(-4.9), -4.9), 2.2), 30)])

# ================================================================== S15: wide time-lapse: storm after storm, the groove grows
s = "S15"; fa, fb = f0(s), f1(s)
key_env(fa, rut=1.0, groove=0.0, wet=0.8, halfw=0.42)
key_env(fb, rut=0.0, groove=1.0, wet=0.4, halfw=0.5)
n = 4
for i in range(n + 1):
    f = fa + int((fb - fa) * i / n); stormy = (i % 2 == 0)
    key_light(f, sun=1.1 if stormy else 3.4, sky=0.45 if stormy else 1.0)
for i in range(n):
    a_ = fa + int((fb - fa) * i / n); b_ = fa + int((fb - fa) * (i + 1) / n)
    key_rain(a_, i % 2 == 0, (2.0, -3.0, 0), 12.0 + i); key_rain(b_ - 1, i % 2 == 0, None, 12.0 + i + (b_ - a_) / FPS)
key_rain(fb, False)
key_water(fa, False)
camshot(s, [(0.0, (6.0, -12.5, 4.6), (0.0, 0.5, 0.6), 24), (1.0, (5.2, -11.0, 4.0), (0.0, 1.0, 0.6), 24)])

# ================================================================== S16: low along the groove: it grows deeper
s = "S16"; fa, fb = f0(s), f1(s)
key_light(fa)
key_env(fa, rut=0.0, groove=1.0, trench=0.0, wet=0.3, halfw=0.5)
key_env(fb, groove=0.45, trench=0.32, wet=0.2, halfw=0.62)
camshot(s, [(0.0, (path_x(-7.5) + 0.75, -7.6, 0.42), (path_x(-1.0), -1.0, -0.15), 28), (1.0, (path_x(-6.6) + 0.72, -6.7, 0.42), (path_x(-0.2), -0.2, -0.2), 28)])

# ================================================================== S17: the grown man beside the groove near the house (logo on his shirt)
s = "S17"; fa, fb = f0(s), fx(s)
key_env(fa, groove=0.45, trench=0.32, wet=0.0, halfw=0.62)
key_light(fa)
MX17 = path_x(4.6) + 1.15
put("Man", s, (0, 0, 0), 0)
p17 = walk_line(MAN, fa, fb, (MX17, 4.6), 0.75, stride=0.66)
blinks(MAN, fa, fb, lid=-4, every=90)
for f in frs(fa, fb, 30): MAN.key_spine(f, flex=4, head=(2, 0))
camshot(s, [(0.0, (MX17 + 0.25, 2.15, 1.38), (MX17, 4.3, 1.22), 35), (1.0, (MX17 + 0.25, 1.75, 1.36), (MX17, 3.6, 1.2), 35)])

# ================================================================== S18: top-down: he walks the trench floor as it deepens (decades)
s = "S18"; fa, fb = f0(s), fx(s)
key_env(fa, groove=0.45, trench=0.32); key_env(f1(s), groove=0.0, trench=0.72, halfw=0.85)
put("Man", s, (0, 0, 0), 0)
walk_path(MAN, fa, fb, 1.4, 1.05)
blinks(MAN, fa, fb, every=90)
camshot(s, [(0.0, *top((path_x(0.6), 0.6), 6.0), 32), (1.0, *top((path_x(-1.8), -1.8), 6.0), 32)])

# ================================================================== S19: wide: house, yard, the trench; he walks in it
s = "S19"; fa, fb = f0(s), fx(s)
key_env(fa, groove=0.0, trench=0.72, halfw=0.85); key_env(f1(s), trench=1.0, halfw=0.9)
put("Man", s, (0, 0, 0), 0)
walk_path(MAN, fa, fb, -3.0, 1.0)
camshot(s, [(0.0, (7.5, -13.0, 6.6), (0.0, -1.0, -0.3), 26), (1.0, (6.6, -12.0, 6.0), (0.0, -1.5, -0.3), 26)])

# ================================================================== S20: from the lawn rim: he stands deep in the trench
s = "S20"; fa, fb = f0(s), fx(s)
key_env(fa, trench=1.0, halfw=0.9)
MY20 = -6.6; MX20 = path_x(MY20)
put("Man", s, (0, 0, 0), 0)
for i, f in enumerate(frs(fa, fb, 20)):
    u = min(1.0, (f - fa) / 50)
    stand(MAN, f, (MX20, MY20), 36, flex=3, spine=2, side=2.5 * math.sin(i * 0.6), head=(2 - 42 * u, 3 * math.sin(i)))   # turns to the rim/camera side, looks up
arms_hang(MAN, fa, (MX20, MY20), yaw=36); arms_hang(MAN, fb, (MX20, MY20), yaw=36)
blinks(MAN, fa, fb, every=70)
camshot(s, [(0.0, (MX20 + 1.7, MY20 - 2.2, 1.9), (MX20, MY20, -0.75), 32), (1.0, (MX20 + 1.55, MY20 - 1.95, 1.75), (MX20, MY20, -0.7), 32)])

# ================================================================== S21: inside the trench: walls above his head (the depth, read by a person)
s = "S21"; fa, fb = f0(s), fx(s)
MY21 = -7.4; MX21 = path_x(MY21)
put("Man", s, (0, 0, 0), 0)
for i, f in enumerate(frs(fa, fb, 12)):
    t = (f - fa) / FPS
    up = smooth(t / 0.5) * (1 - smooth((t - 0.9) / 0.5))          # looks up at the rim, then back down to us
    shift = math.sin(t * 2.4)                                      # slow weight shift side to side
    stand(MAN, f, (MX21 + 0.015 * shift, MY21), 0, flex=3, spine=2, twist=4 * shift, side=3.5 * shift,
          head=(6 - 30 * up, -10 * up + 6 * (1 - up) * math.sin(t * 1.7)))
for f in frs(fa, fb, 24): arms_hang(MAN, f, (MX21, MY21), sway=0.012 * math.sin((f - fa) / FPS * 2.4))
blinks(MAN, fa, fb, every=80)
gz21 = world_ground(MX21, MY21, fa)
camshot(s, [(0.0, (path_x(-10.0), -10.0, gz21 + 1.25), (MX21, MY21, gz21 + 1.25), 26), (1.0, (path_x(-9.6), -9.6, gz21 + 1.3), (MX21, MY21, gz21 + 1.35), 26)])

# ================================================================== S22-S23: punchline: sandbags on the rims, helmet, he peeks over
MY22 = -4.5; MX22 = path_x(MY22)
STEP = box("FireStep", (1.3, 1.0, 0.86), (MX22, MY22, 0.0), bpy.data.materials["GroundMat"], bpy.data.collections["Yard"])
gzs = world_ground(MX22, MY22, f0("S22")) if False else -STAGES["Trench"][1] * taper(MY22)
STEP.location.z = gzs + 0.43
key_vis(STEP, [(0, False), (f0("S22"), True)])
SECT_TOP_SAVE = SECT_TOP
for s, (fa, fb) in [(x, (f0(x), fx(x))) for x in ("S22", "S23") if x in ORDER]:
    put("Man", s, (0, 0, 0), 0)
    PLACE["M"] = Matrix.Identity(4)
    top_z = gzs + 0.86
    base = MAN.root_head.z - 0.015
    for i, f in enumerate(frs(fa, fb, 15)):
        u = min(1.0, (f - fa) / 45) if s == "S22" else 1.0
        MAN.key_root(f, Vector((MX22, MY22, top_z + base - 0.28 * (1 - u))), yaw=90, flex=6, side=0)
        MAN.key_spine(f, flex=8, twist=0, head=(-4, 28 * math.sin((f - fa) / 38.0)))
        for sd in "LR": MAN.key_foot(sd, f, MAN.foot_xy(sd, Vector((MX22, MY22)), 90), 90, lift=top_z - gz_local(MAN.foot_xy(sd, Vector((MX22, MY22)), 90).x, MAN.foot_xy(sd, Vector((MX22, MY22)), 90).y, f))
    arms_hang(MAN, fa, (MX22, MY22), dz=top_z - gz_local(MX22, MY22, fa))
    blinks(MAN, fa, fb, every=75)
# arms_hang uses local -Y facing; re-key hands for yaw 90 (facing +X): hands rest on the sandbag-side wall top? keep them hanging at the sides
for s, (fa, fb) in [(x, (f0(x), fx(x))) for x in ("S22", "S23") if x in ORDER]:
    Rz = Matrix.Rotation(R_(90), 3, 'Z')
    for f in (fa, fb):
        for sd, sx in (("L", 1), ("R", -1)):
            sh = MAN.r.BN["upperarm01." + sd].head_local
            off = Vector((sh.x + 0.075 * sx, sh.y - 0.07, 0)); W = Vector((MX22, MY22, 0)) + Rz @ off
            W.z = top_z + sh.z - 0.535
            MAN.key_hand(sd, f, W, Rz @ Vector((0, -0.12, -1)), Rz @ Vector((-sx, 0, 0)), pole=W + Rz @ Vector((0.3 * sx, 0.5, 0.25)))
            apply_pose(MAN.r.o, sd, "relaxed", f)
# helmet rides on the head bone
OB['Man'].location = (0, 0, 0); OB['Man'].rotation_quaternion = (1, 0, 0, 0)
ev(f0("S22") + 50)
hb = MAN.r.o.matrix_world @ MAN.r.PB["head"].matrix
crown = MAN.r.o.matrix_world @ MAN.r.PB["head"].tail
HEL.scale = (1.1, 1.1, 1.1)
want = Matrix.Translation(crown + Vector((0, 0, -0.122))) @ Matrix.Scale(1.1, 4) @ Matrix.Rotation(R_(90), 4, 'Z')
OFFH = hb.inverted() @ want
HEL_END = max(f1(x) for x in ORDER if x in ("S21", "S22", "S23") and f0(x) >= f0("S22"))   # helmet stays on through every later shot
follow_bone(HEL, MAN.r.o, "head", f0("S22"), HEL_END, OFFH, step=2)
camshot("S22", [(0.0, (MX22 + 2.9, MY22 + 0.5, 0.62), (MX22, MY22, 0.42), 40), (1.0, (MX22 + 2.5, MY22 + 0.4, 0.62), (MX22, MY22, 0.45), 40)])
if "S23" in ORDER: camshot("S23", [(0.0, (MX22 + 2.4, MY22 - 1.0, 1.0), (MX22, MY22, 0.4), 32), (1.0, (MX22 + 6.5, MY22 - 7.0, 5.5), (MX22, MY22 + 1.0, -0.2), 28)])
key_light(f0("S22")); key_env(f0("S22"), trench=1.0, wet=0.0)
