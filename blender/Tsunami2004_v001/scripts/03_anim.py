"""Animate everything except the camera.  blender -b scene.blend --python 03_anim.py -- <out.blend>"""
import sys
exec(open("/home/user/Muhammed/blender/Tsunami2004_v001/scripts/lib.py").read())
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
random.seed(2004)
SKIP_PEOPLE = "--nopeople" in sys.argv
CURL = float(next((a.split("=")[1] for a in sys.argv if a.startswith("--curl=")), "55"))

# ---------------------------------------------------------------- people
if not SKIP_PEOPLE:
    with bpy.data.libraries.load(HERE + "/people.blend", link=False) as (src, dst):
        dst.objects = list(src.objects)
    CP = coll("People")
    for o in dst.objects:
        if o is not None: CP.objects.link(o)
    exec(open("/home/user/Muhammed/blender/pipeline/anim_lib.py").read())
    exec(open(HERE + "/scripts/03_people.py").read())
    # crowd: time-shifted clones of the eight performers, offset along the beach (x only: the beach height depends on y)
    def shifted(act, df):
        a2 = act.copy()
        for fc in _fcurves(a2):
            for kp in fc.keyframe_points:
                kp.co.x += df; kp.handle_left.x += df; kp.handle_right.x += df
        return a2
    CLONES = [("TouristM", 9), ("TouristW", -7), ("LocalM", 5), ("LocalW", 12), ("OldM", -4), ("KidA", 14),
              ("Fisher", 6), ("KidB", -10), ("TouristM", 15), ("LocalW", 3), ("LocalM", -12), ("TouristW", 8)]
    def pos_at(name, f):
        st = P[name].st; k = min(st, key=lambda q: abs(q - f)); return st[k][0]
    SAMPLE = list(range(1, F(21.1), 15))
    placed = [(n, 0.0, 0) for n in P]          # (source, dx, df)
    rng = random.Random(7)
    for i, (src, df) in enumerate(CLONES):
        best = None
        cands = [dx for dx in range(-75, 76, 2) if abs(dx) >= 14]
        rng.shuffle(cands)
        for dx in cands[:60]:
            md = 1e9
            for f in SAMPLE:
                p0 = pos_at(src, f - df) + Vector((dx, 0, 0))
                for (n2, dx2, df2) in placed:
                    q = pos_at(n2, f - df2) + Vector((dx2, 0, 0))
                    md = min(md, (p0 - q).length)
            if best is None or md > best[0]: best = (md, dx)
        placed.append((src, float(best[1]), df)); print("CLONE", src, best[1], df, "min dist %.1f" % best[0])
    for i, (src, dx, df) in enumerate(placed[len(P):]):
        rig = bpy.data.objects[src]; r2 = rig.copy(); r2.data = rig.data.copy(); r2.name = "%s_C%02d" % (src, i); CP.objects.link(r2)
        r2.animation_data.action = shifted(rig.animation_data.action, df); r2.location.x += dx
        # height correction: the shelf height varies along x, so lift/lower the clone by the local difference
        for f in range(1, F(21.3), 4):
            p0 = pos_at(src, f - df)
            r2.location.z = ground_z(p0.x + dx, p0.y) - ground_z(p0.x, p0.y); r2.keyframe_insert("location", index=2, frame=f)
        for ch in rig.children:
            c2 = ch.copy(); c2.name = "%s_C%02d.%s" % (src, i, ch.name.split(".", 1)[1]); CP.objects.link(c2); c2.parent = r2
            for md in c2.modifiers:
                if md.type == 'ARMATURE': md.object = r2
            if ch.animation_data and ch.animation_data.action:
                c2.animation_data.action = shifted(ch.animation_data.action, df)
    # grasp: fisher's right fingers close round the fish
    rr = P["Fisher"].H.r
    for f, a in ((T(6.5), 0), (T(6.75), 1), (T(9.0), 1), (T(9.2), 0)):
        for fn_ in ("finger2", "finger3", "finger4", "finger5"):
            for seg in ("-1", "-2", "-3"):
                pb = rr.PB[fn_ + seg + ".R"]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (math.radians(18 + (CURL - 18) * a * (0.8 if seg == "-1" else 1.0)), 0, 0)
                pb.keyframe_insert("rotation_euler", frame=f)
        pb = rr.PB["finger1-2.R"]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (math.radians(10 + 30 * a), 0, 0); pb.keyframe_insert("rotation_euler", frame=f)

# ---------------------------------------------------------------- sea drawback
sea = bpy.data.objects["SeaPlane"]
for t in np.arange(0, 6.01, 0.25):
    sea.location.z = sea_level(t); sea.keyframe_insert("location", index=2, frame=F(t))

# ---------------------------------------------------------------- the wave: position, stage blend, chop
WK = [  # t, front y, (S1, S2, S2b, S3) weights, z offset
    (0.0, 2600, (0, 0, 0, 0), 0), (5.0, 2050, (0, 0, 0, 0), 0), (7.2, 1750, (0.5, 0, 0, 0), 0), (10.8, 1250, (0.85, 0, 0, 0), 0),
    (13.1, 950, (0.9, 0, 0, 0), 0), (15.6, 500, (1.0, 0, 0, 0), 0), (16.6, 330, (0.5, 0.5, 0, 0), 0), (17.5, 180, (0.15, 0.85, 0, 0), 0),
    (18.3, 80, (0, 1, 0, 0), 0), (19.3, 40, (0, 1, 0, 0), 0), (20.3, 12, (0, 0.6, 0.4, 0), 0), (21.0, -8, (0, 0, 1, 0), 0),
    (21.6, -30, (0, 0, 0.3, 0.7), 0), (22.3, -62, (0, 0, 0, 1), 0), (25.7, -160, (0, 0, 0, 1), 0), (28.0, -235, (0, 0, 0, 1), 0),
    (30.0, -310, (0, 0, 0, 1), 0), (31.6, -380, (0, 0, 0, 1), -2.0), (40.0, -480, (0, 0, 0, 1), -2.05)]
def wave_y(t):
    for a, b in zip(WK, WK[1:]):
        if a[0] <= t <= b[0]:
            u = (t - a[0]) / (b[0] - a[0]); return a[1] + (b[1] - a[1]) * u
    return WK[-1][1]
def T_front(y):   # time the front passes y
    for a, b in zip(WK, WK[1:]):
        if b[1] <= y <= a[1]:
            return a[0] + (b[0] - a[0]) * (a[1] - y) / (a[1] - b[1])
    return 99.0
wave = bpy.data.objects["Wave"]; kb = wave.data.shape_keys.key_blocks
for t, y, wts, dz in WK:
    f = F(t)
    wave.location = (0, y, dz); wave.keyframe_insert("location", frame=f)
    for k, wv in zip(("S1", "S2", "S2b", "S3"), wts):
        kb[k].value = wv; kb[k].keyframe_insert("value", frame=f)
        ks_ = bpy.data.objects["WaveSpray"].data.shape_keys.key_blocks[k]; ks_.value = wv; ks_.keyframe_insert("value", frame=f)
for fc in _fcurves(bpy.data.objects["WaveSpray"].data.shape_keys.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
spd = bpy.data.materials["M_CrestSpray"].node_tree.nodes["SPRAY_DENS"].inputs["To Max"]
nq = bpy.data.materials["M_CrestSpray"].node_tree.nodes["NQ"].inputs["W"]
for t, d in ((0, 0.0), (7, 0.12), (10, 0.15), (15.6, 0.3), (18.3, 0.45), (21.3, 0.6), (22.0, 0.15), (22.5, 0.0)):
    spd.default_value = d; spd.keyframe_insert("default_value", frame=F(t))
for t, wv in ((0, 0), (40, 12)):
    nq.default_value = wv; nq.keyframe_insert("default_value", frame=F(t))
key_hide(bpy.data.objects["WaveSpray"], [(1, False), (F(22.55), True)])
fnw = bpy.data.materials["M_Wave"].node_tree.nodes["FN"].inputs["W"]
for t, wv in ((0, 0), (40, 8)):
    fnw.default_value = wv; fnw.keyframe_insert("default_value", frame=F(t))
# position should be linear-ish (constant speed between keys)
for fc in _fcurves(wave.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
ch = wave.modifiers["churn"]
ocm = wave.modifiers["ocean"]
for t, ws_, tm in ((0, 0.0, 0.0), (21.3, 0.0, 21.3), (22.0, 0.9, 22.0), (29.8, 0.8, 29.8), (31.6, 0.08, 31.6), (40, 0.05, 40.0)):
    ocm.wave_scale = ws_; ocm.keyframe_insert("wave_scale", frame=F(t)); ocm.time = tm; ocm.keyframe_insert("time", frame=F(t))
for t, v in ((0, 0.0), (20.8, 0.0), (21.8, 0.6), (29.8, 0.5), (31.6, 0.05), (40, 0.05)):
    ch.strength = v; ch.keyframe_insert("strength", frame=F(t))
wn = bpy.data.objects["WaveNoiseEmpty"]
for t in (0, 40):
    wn.location = (t * 1.5, -0.0 + t * 6.0, t * 2.0); wn.keyframe_insert("location", frame=F(t))
for fc in _fcurves(wn.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
# water colour turns muddy once it is over land, foam churn on the flood
for mname in ("M_Wave",):
    nt = bpy.data.materials[mname].node_tree; b = nt.nodes["Principled BSDF"]; fv = nt.nodes["FOAM_BASE"]; nz = nt.nodes["NZ"]
    for t, colr, foam in ((0, (0.02, 0.2, 0.28), 0.0), (20.6, (0.02, 0.2, 0.28), 0.15), (22.0, (0.07, 0.065, 0.04), 0.2),
                          (30.0, (0.075, 0.07, 0.045), 0.18), (31.6, (0.12, 0.2, 0.2), 0.08), (40, (0.12, 0.22, 0.24), 0.05)):
        b.inputs["Base Color"].default_value = (*colr, 1); b.inputs["Base Color"].keyframe_insert("default_value", frame=F(t))
        fv.outputs[0].default_value = foam; fv.outputs[0].keyframe_insert("default_value", frame=F(t))
    for t, rg in ((0, 0.07), (20.8, 0.07), (22.0, 0.4), (31.0, 0.4), (32.0, 0.05)):
        b.inputs["Roughness"].default_value = rg; b.inputs["Roughness"].keyframe_insert("default_value", frame=F(t))
    for t, wv in ((0, 0), (40, 6)):
        nz.inputs["W"].default_value = wv; nz.inputs["W"].keyframe_insert("default_value", frame=F(t))
    for fc in _fcurves(nt.animation_data.action):
        if "W" in fc.data_path or 'inputs[1]' in fc.data_path:
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
ntS = bpy.data.materials["M_Sea"].node_tree
for t, wv in ((0, 0), (40, 6)):
    ntS.nodes["NZ"].inputs["W"].default_value = wv; ntS.nodes["NZ"].inputs["W"].keyframe_insert("default_value", frame=F(t))

# ---------------------------------------------------------------- debris carried up the wave face (16.4 - 21.0 s)
FACE = []
lt = bpy.data.objects["LIB_longtail"]; pb_ = bpy.data.objects["LIB_palm_b"]; c2 = bpy.data.objects["LIB_car2"]
for i, (lib, x, frac, rot) in enumerate([(lt, -9, 0.42, (0.4, 0.9, 1.2)), (pb_, 3, 0.58, (1.4, 0.3, 0.2)), (lt, 15, 0.66, (-0.5, 2.2, 0.4)),
                                         (pb_, -20, 0.5, (1.2, -0.6, 2.0)), (c2, 24, 0.36, (0.6, 1.8, 0.3))]):
    o = bpy.data.objects.new("FaceDebris_%d" % i, lib.data); bpy.data.collections["Water"].objects.link(o); o.scale = (0.9,) * 3
    FACE.append((o, x, frac, rot))
NXW_, NUW_ = 900, 170
xs_ = np.linspace(-1500, 1500, NXW_)
for o, x, frac, rot in FACE:
    key_hide(o, [(1, True), (F(15.8), False)])
    for f in range(F(15.8), F(21.05), 6):
        t = (f - 1) / 60.0; u = frac
        yf = wave_y(t) + (8 * u - 8 * u ** 3) - 1.6 + 3 * math.sin(x / 61.0); zf = (-5 + 18 * u ** 1.6) * 1.6
        tt = t - 15.8
        key_tr(o, f, loc=(x, yf, zf), rot=(rot[0] * tt * 1.5, rot[1] * tt * 1.5, rot[2] * tt))
    o["face"] = 1
# hero wave: replaces the GN sheet 15.62 - 21.05 s
hero = bpy.data.objects["HeroWave"]
for t in list(np.arange(15.6, 21.06, 0.25)) + [21.05]:
    hero.location = (0, wave_y(t), 0); hero.keyframe_insert("location", frame=F(t))
for fc in _fcurves(hero.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
key_hide(hero, [(1, True), (F(15.62), False), (F(21.06), True)])
for nm_ in ("Wave", "WaveSpray"):
    key_hide(bpy.data.objects[nm_], [(F(15.62), True), (F(21.06), False)])
hn = bpy.data.materials["M_HeroWave"].node_tree.nodes["HN"].inputs["W"]
for t, w_ in ((15.6, 0), (21.1, 4)):
    hn.default_value = w_; hn.keyframe_insert("default_value", frame=F(t))
rs = random.Random(5)
for o in [o for o in bpy.data.objects if o.name.startswith("HeroSpray_")]:
    x = rs.uniform(-70, 70); ly = rs.uniform(-9, -2); ph = rs.uniform(0, 1)
    key_hide(o, [(1, True), (F(15.7), False), (F(21.06), True)])
    for f in range(F(15.7), F(21.06), 9):
        t = (f - 1) / 60.0; c = ((t * 1.3 + ph) % 1.0)
        o.location = (x + rs.uniform(-1, 1), wave_y(t) + ly * 1.3 - 4 * c + 3 * math.sin(x / 61.0), 18.0 + 6.0 * c + rs.uniform(-0.8, 0.8))
        o.keyframe_insert("location", frame=f)
        o.scale = (1.4 - 1.0 * c,) * 3; o.keyframe_insert("scale", frame=f)
# ---------------------------------------------------------------- moored boats settle on the sand, rowboats/fish on the seabed
def flood_z(t, y):
    """water surface height at y at time t once the wave has passed (for floating debris)"""
    dz = 0 if t < 30 else -2.0 * sstep((t - 30) / 1.6)
    return 2.5 + dz
for b in bpy.data.objects:
    if not b.name.startswith("Longtail_"): continue
    x, y = b.location.x, b.location.y; gz = terrain_h(x, y)
    if b["moored"]:
        for t in np.arange(0, 5.01, 0.5):
            z = max(gz + 0.05, sea_level(t) + 0.25)
            tilt = math.radians(14) * sstep((gz + 0.3 - sea_level(t)) / 0.6) * (1 if x > 0 else -1)
            key_tr(b, F(t), loc=(x, y, z), rot=(0, tilt, b.rotation_euler.z))
        for t in np.arange(0.5, 5.0, 0.5):   # gentle bob while still afloat
            pass
# fish flap on the exposed seabed (irregular hops)
for o in bpy.data.objects:
    if not o.name.startswith("Fish_") or o.name == "Fish_00": continue
    x, y = o.location.x, o.location.y; z0 = o.location.z; yaw0 = o.rotation_euler.z
    t = 2.4 + random.uniform(0, 0.6)
    while t < 21:
        f = F(t)
        key_tr(o, f, loc=(x, y, z0), rot=(0, math.radians(90), yaw0))
        dt = random.uniform(0.14, 0.24)
        key_tr(o, F(t + dt * 0.5), loc=(x, y, z0 + random.uniform(0.06, 0.16)), rot=(random.uniform(-0.5, 0.5), math.radians(90 + random.choice([-1, 1]) * random.uniform(25, 50)), yaw0 + random.uniform(-0.4, 0.4)))
        yaw0 += random.uniform(-0.3, 0.3)
        t += dt + random.uniform(0.05, 0.6)
    key_tr(o, F(t), loc=(x, y, z0), rot=(0, math.radians(90), yaw0))

# ---------------------------------------------------------------- impact: palms, umbrellas, loungers, boats, cars swept inland
def sweep(o, t0, dist, spin, end_tilt, sink=False, rest=True, rise=4.2, dur=None):
    """push an object inland from time t0: rises onto the flood surface, tumbles, and settles (aftermath) or sinks"""
    x, y, z = o.location; r0 = o.rotation_euler.copy()
    dur = dur or (2.4 + dist / 30)
    key_tr(o, F(t0), loc=(x, y, z), rot=tuple(r0))
    n = 6
    for i in range(1, n + 1):
        u = i / n; t = t0 + dur * u
        yy = y - dist * (1 - (1 - u) ** 1.6); xx = x + 0.12 * dist * math.sin(u * 2.5 + x)
        zz = (terrain_h(xx, yy) + rise * math.sin(min(1, u * 1.6) * math.pi / 2) * (1 - 0.7 * u)) if not sink else (z - 6 * u)
        rot = (r0.x + spin[0] * u, r0.y + spin[1] * u, r0.z + spin[2] * u)
        key_tr(o, F(t), loc=(xx, yy, zz), rot=rot)
    if rest:
        xx, yy = o.location.x, o.location.y
        key_tr(o, F(t0 + dur + 0.8), loc=(xx, yy, terrain_h(xx, yy) + 0.2), rot=(end_tilt[0], end_tilt[1], r0.z + spin[2]))
for o in bpy.data.objects:
    nm = o.name
    if nm.startswith(("Palm_", "TPalm_")):
        x, y = o.location.x, o.location.y; t0 = T_front(y) + 0.1
        # idle sway in the breeze until the wave
        for t in np.arange(0, min(t0, 40), 1.1):
            o.rotation_euler.x = math.radians(2.0 * math.sin(t * 1.7 + x)); o.keyframe_insert("rotation_euler", index=0, frame=F(t))
        if t0 > 40: continue
        o.rotation_euler.x = 0.0; o.keyframe_insert("rotation_euler", index=0, frame=F(max(0.1, t0 - 1.6)))
        o.rotation_euler.x = math.radians(-22); o.keyframe_insert("rotation_euler", index=0, frame=F(t0 - 0.05))
        if random.random() < 0.35 and nm.startswith("TPalm_"):
            continue  # some palms survive
        fall = math.radians(random.uniform(70, 88))
        o.keyframe_insert("rotation_euler", frame=F(t0))
        o.rotation_euler.x = -fall * 0.25; o.keyframe_insert("rotation_euler", index=0, frame=F(t0 + 0.25))
        o.rotation_euler.x = -fall; o.keyframe_insert("rotation_euler", index=0, frame=F(t0 + 0.9))
        o.keyframe_insert("location", frame=F(t0 + 0.6))
        o.location.y -= random.uniform(6, 18); o.location.z = terrain_h(o.location.x, o.location.y) - 0.5
        o.keyframe_insert("location", frame=F(t0 + 2.5))
    elif nm.startswith(("Umbrella_", "Lounger_")):
        sweep(o, T_front(o.location.y), random.uniform(25, 60), (random.uniform(-6, 6), random.uniform(-6, 6), random.uniform(-3, 3)), (random.uniform(-1, 1), random.uniform(-1, 1), 0), rise=3.5)
    elif nm.startswith("Longtail_"):
        sweep(o, T_front(o.location.y) + 0.05, random.uniform(60, 140), (random.uniform(-1.5, 1.5), random.uniform(-2.5, 2.5), random.uniform(-2, 2)),
              (0, math.radians(random.choice([-35, 35, 160])), 0), rise=4.0)
    elif nm.startswith("Car_"):
        sweep(o, T_front(o.location.y) + 0.1, random.uniform(40, 110), (random.uniform(-3, 3), random.uniform(-6, 6), random.uniform(-2, 2)),
              (0, math.radians(random.choice([0, 90, 180, -90])), 0), rise=3.0)
    elif nm.startswith("Rowboat_"):
        sweep(o, T_front(o.location.y), random.uniform(150, 250), (2, 3, 2), (0, 2.8, 0), rise=6.0)

for o, x, frac, rot in FACE:
    sweep(o, 21.1, random.uniform(60, 120), (2, 3, 1), (0, 2.6, 0), rise=4.0)
# ---------------------------------------------------------------- hotel ground floor blown in
for i, p in enumerate(bpy.data.objects[n] for n in sorted(o.name for o in bpy.data.objects if o.name.startswith("Hotel_Pane_"))):
    t0 = T_front(-28) + 0.02 * i
    key_tr(p, F(t0), loc=tuple(p.location), rot=(0, 0, 0))
    key_tr(p, F(t0 + 0.5), loc=(p.location.x + random.uniform(-2, 2), p.location.y - random.uniform(6, 10), p.location.z + random.uniform(-0.8, 1.0)),
           rot=(random.uniform(-1.5, 1.5), random.uniform(-0.6, 0.6), random.uniform(-0.8, 0.8)))
    key_hide(p, [(1, False), (F(t0 + 0.55), True)])
for p in (o for o in bpy.data.objects if o.name.startswith("Hotel_Sofa_")):
    t0 = T_front(-28) + 0.15
    key_tr(p, F(t0), loc=tuple(p.location), rot=(0, 0, 0))
    key_tr(p, F(t0 + 1.0), loc=(p.location.x + random.uniform(-2, 2), -42.5, p.location.z + 1.2), rot=(random.uniform(-1, 1), random.uniform(-1.5, 1.5), random.uniform(-1, 1)))
    p.location.z = 0.9; key_tr(p, F(t0 + 2.2), loc=tuple(p.location))

for o in bpy.data.objects:
    if o.name.startswith("HotelSpray_"):
        i = int(o.name.split("_")[1]); t0 = T_front(-28) - 0.05 + 0.03 * i
        key_hide(o, [(1, True), (F(t0), False), (F(t0 + 1.6), True)])
        l = o.location.copy()
        key_tr(o, F(t0), loc=tuple(l), scale=0.3)
        key_tr(o, F(t0 + 0.5), loc=(l.x, l.y + 2, l.z + 5), scale=(4, 3, 6))
        key_tr(o, F(t0 + 1.5), loc=(l.x, l.y - 4, l.z + 7), scale=(6, 5, 7))
CT = bpy.data.collections["Town"]
for i in range(30):
    lib = [bpy.data.objects[n] for n in ("LIB_car", "LIB_car2", "LIB_umbrella", "LIB_rowboat", "LIB_longtail", "LIB_umbrella2")][i % 6]
    x = random.uniform(24, 44); y = random.uniform(-70, -235)
    o = bpy.data.objects.new("Debris_S%02d" % i, lib.data); CT.objects.link(o)
    o.location = (x, y, terrain_h(x, y) - 4.0); o.rotation_euler = (random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6), random.uniform(0, 6.28))
# ---------------------------------------------------------------- town: houses come apart, tilt and slide into the flood; rubble remains
houses = [o for o in bpy.data.objects if o.name.startswith("House_") and "_" not in o.name[6:]]
survivors = set(random.sample(range(len(houses)), 8))
for i, h in enumerate(houses):
    x, y = h["hx"], h["hy"]; t0 = T_front(y) + random.uniform(0.15, 0.6)
    if i in survivors or t0 > 38: continue
    z0 = h.location.z; yaw = h.rotation_euler.z
    dist = random.uniform(10, 30); tilt = (random.uniform(-0.9, 0.9), random.uniform(-0.9, 0.9))
    key_tr(h, F(t0), loc=(x, y, z0), rot=(0, 0, yaw))
    key_tr(h, F(t0 + 0.6), loc=(x, y - dist * 0.25, z0 - 0.4), rot=(tilt[0] * 0.2, tilt[1] * 0.2, yaw + random.uniform(-0.2, 0.2)))
    key_tr(h, F(t0 + 1.6), loc=(x + random.uniform(-3, 3), y - dist * 0.7, z0 - 2.5), rot=(tilt[0] * 0.7, tilt[1] * 0.7, yaw + random.uniform(-0.5, 0.5)))
    key_tr(h, F(t0 + 2.6), loc=(x + random.uniform(-3, 3), y - dist, z0 - 9), rot=(tilt[0], tilt[1], yaw + random.uniform(-0.8, 0.8)))
    key_hide(h, [(1, False), (F(t0 + 2.7), True)])
    for ch in h.children:
        if ch.name.endswith("_roof"):
            l0 = ch.location.copy()
            key_tr(ch, F(t0 + 0.2), loc=tuple(l0), rot=(0, 0, 0))
            key_tr(ch, F(t0 + 1.4), loc=(l0.x + random.uniform(-3, 3), l0.y + random.uniform(-3, 3), l0.z + random.uniform(-1, 1.5)), rot=(random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6), random.uniform(-0.8, 0.8)))
        key_hide(ch, [(1, False), (F(t0 + 2.7), True)])
for o in bpy.data.objects:
    if o.name.startswith("Rubble_"):
        t0 = T_front(o.location.y) + 1.8
        z_end = terrain_h(o.location.x, o.location.y) - 0.15
        key_tr(o, F(min(t0, 39)), loc=tuple(o.location))
        o.location.z = z_end; key_tr(o, F(min(t0 + 1.0, 39.5)), loc=tuple(o.location))
    elif o.name.startswith(("Debris_", "Sheet_")):
        # rides the flood: surfaces in the churn at the front, drifts inland, settles when the water drains
        x, y = o.location.x, o.location.y; z_hide = o.location.z; t0 = T_front(y)
        if t0 > 30: continue
        r0 = o.rotation_euler.copy(); drift = random.uniform(12, 45); spin = random.uniform(-2.5, 2.5)
        key_tr(o, F(t0 - 0.05), loc=(x, y, z_hide), rot=tuple(r0))
        tt = t0 + 0.15; i = 0
        while tt < 30.0:
            u = 1 - math.exp(-(tt - t0) / 2.5)
            xx, yy = x + 0.15 * drift * math.sin(u * 3 + x), y - drift * u
            key_tr(o, F(tt), loc=(xx, yy, flood_z(tt, yy) - 0.05 + 0.12 * math.sin(tt * 3 + x)),
                   rot=(r0.x + 0.15 * math.sin(tt * 2 + y), r0.y + 0.15 * math.cos(tt * 2.3 + x), r0.z + spin * u))
            tt += 0.7; i += 1
        key_tr(o, F(31.6), loc=(o.location.x, o.location.y, terrain_h(o.location.x, o.location.y) + 0.05), rot=(r0.x * 0.3, r0.y * 0.3, o.rotation_euler.z))
# survivors keep a damaged look: they lose their roofs
for i in survivors:
    h = houses[i]
    for ch in h.children:
        if ch.name.endswith("_roof"):
            t0 = T_front(h["hy"]) + 0.5
            if t0 < 38:
                key_tr(ch, F(t0), loc=tuple(ch.location), rot=(0, 0, 0))
                key_tr(ch, F(t0 + 1.5), loc=(ch.location.x, ch.location.y - 12, ch.location.z - 5), rot=(0.8, 0.3, 0.5))
                key_hide(ch, [(1, False), (F(t0 + 1.6), True)])

# ---------------------------------------------------------------- diorama: tension, slip, uplift, bulge splits
tip = bpy.data.objects["D_Tip"]; wtop = bpy.data.objects["D_WaterTop"]; fault = bpy.data.objects["D_Fault"]
key_tr(tip, F(13.0), rot=(0, 0, 0)); key_tr(tip, F(14.2), rot=(math.radians(-4), 0, 0))    # dragged down
key_tr(tip, F(14.4), rot=(math.radians(5), 0, 0)); key_tr(tip, F(14.7), rot=(math.radians(3.5), 0, 0))   # snaps up
l0 = tip.location.copy()
key_tr(tip, F(14.2), loc=tuple(l0)); key_tr(tip, F(14.4), loc=(l0.x, l0.y, l0.z + 0.9)); key_tr(tip, F(14.8), loc=(l0.x, l0.y, l0.z + 0.75))
kbw = wtop.data.shape_keys.key_blocks
for t, tr in ((13.0, 0), (14.3, 0), (14.5, 1.0), (15.0, 0.6), (15.6, 0.3)):
    kbw["Trough"].value = tr; kbw["Trough"].keyframe_insert("value", frame=F(t))
op_ = bpy.data.objects["D_OceanPlate"]; os_ = bpy.data.objects["D_OceanSed"]
for o_ in (op_, os_):
    l_ = o_.location.copy(); key_tr(o_, F(14.35), loc=tuple(l_)); key_tr(o_, F(14.55), loc=(l_.x, l_.y + 0.4, l_.z - 0.35)); key_tr(o_, F(15.6), loc=(l_.x, l_.y + 0.45, l_.z - 0.35))
for nm_ in ("D_PulseSea", "D_PulseShore"):
    key_hide(bpy.data.objects[nm_], [(1, True), (F(14.55), False), (F(15.45), True)])
for t, bu, sa in ((13.0, 0, 0), (14.3, 0, 0), (14.6, 1, 0), (15.0, 0.6, 0.4), (15.6, 0.0, 1.0)):
    kbw["Bulge"].value = bu; kbw["Bulge"].keyframe_insert("value", frame=F(t))
    for k in ("SplitA", "SplitB"):
        kbw[k].value = sa; kbw[k].keyframe_insert("value", frame=F(t))
ring = bpy.data.objects["D_ShockRing"]; rme = bpy.data.materials["M_Shock"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for t, sc_, e in ((14.35, 0.01, 0.0), (14.42, 0.5, 4.0), (14.7, 2.5, 2.0), (14.9, 3.5, 0.0)):
    ring.scale = (sc_,) * 3; ring.keyframe_insert("scale", frame=F(t)); rme.default_value = e; rme.keyframe_insert("default_value", frame=F(t))
key_hide(ring, [(1, True)])
fl_ = bpy.data.lights["D_Flash"]
for t, e in ((14.35, 0.0), (14.42, 3000.0), (14.7, 800.0), (15.1, 0.0)):
    fl_.energy = e; fl_.keyframe_insert("energy", frame=F(t))
for o in bpy.data.objects:
    if o.name.startswith("D_Chunk_1"):
        l = o.location.copy(); r0 = o.rotation_euler.copy()
        key_tr(o, F(14.38), loc=tuple(l), rot=tuple(r0)); key_hide(o, [(1, True), (F(14.36), False)])
        up = random.uniform(0.8, 2.2)
        key_tr(o, F(14.65), loc=(l.x, l.y + random.uniform(-1, 1), l.z + up), rot=(r0.x + random.uniform(-2, 2), r0.y + random.uniform(-2, 2), r0.z))
        key_tr(o, F(15.3), loc=(l.x, l.y + random.uniform(-1.5, 1.5), l.z + up * 0.4), rot=(r0.x + random.uniform(-3, 3), r0.y + random.uniform(-3, 3), r0.z))
fm = bpy.data.materials["M_FaultGlow"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for t, e in ((13.0, 0.0), (14.3, 0.5), (14.4, 12.0), (15.0, 3.0), (15.6, 1.0)):
    fm.default_value = e; fm.keyframe_insert("default_value", frame=F(t))
for o in bpy.data.objects:
    if o.name.startswith("D_Chunk_X"):
        l = o.location.copy()
        for t in np.arange(14.35, 15.2, 0.05):
            key_tr(o, F(t), loc=(l.x + random.uniform(-0.05, 0.05), l.y + random.uniform(-0.05, 0.05), l.z + random.uniform(0, 0.25) * (1 - (t - 14.35) / 0.9)))

# ---------------------------------------------------------------- light: morning -> golden hour aftermath; mud; dust
sun = bpy.data.objects["Sun"]
mixn = sc.world.node_tree.nodes["HDRI_MIX"].inputs["Factor"]; bgs = sc.world.node_tree.nodes["Background"].inputs["Strength"]
for t, rot, col, en, mx, bg in ((0, (50, 0, 200), (1.0, 0.97, 0.92), 5.0, 0.0, 1.45), (29.6, (50, 0, 200), (1.0, 0.97, 0.92), 5.0, 0.0, 1.45),
                                (32.0, (68, 0, 15), (1.0, 0.82, 0.62), 4.8, 0.35, 1.45), (40, (70, 0, 12), (1.0, 0.8, 0.6), 4.6, 0.4, 1.45)):
    sun.rotation_euler = tuple(math.radians(v) for v in rot); sun.keyframe_insert("rotation_euler", frame=F(t))
    sun.data.color = col; sun.data.keyframe_insert("color", frame=F(t)); sun.data.energy = en; sun.data.keyframe_insert("energy", frame=F(t))
    mixn.default_value = mx; mixn.keyframe_insert("default_value", frame=F(t)); bgs.default_value = bg; bgs.keyframe_insert("default_value", frame=F(t))
for m_ in bpy.data.materials:
    if m_.use_nodes and "WL_MUD" in m_.node_tree.nodes:
        o_ = m_.node_tree.nodes["WL_MUD"].outputs[0]
        for t, v in ((0, 0), (30.2, 0), (31.4, 1)):
            o_.default_value = v; o_.keyframe_insert("default_value", frame=F(t))
# poles topple in the flood and their wires snap
for o in bpy.data.objects:
    if o.name.startswith("Pole_"):
        t0 = T_front(o.location.y) + random.uniform(0.1, 0.6)
        if t0 > 38 or random.random() < 0.3: continue
        key_tr(o, F(t0), rot=tuple(o.rotation_euler))
        key_tr(o, F(t0 + 0.9), rot=(-random.uniform(0.6, 1.4), random.uniform(-0.4, 0.4), o.rotation_euler.z))
        o["fell"] = t0
for o in bpy.data.objects:
    if o.name.startswith("Wire_"):
        ts = [bpy.data.objects[o[k]].get("fell", 99) for k in ("pole_a", "pole_b")]
        t0 = min(ts)
        if t0 < 38: key_hide(o, [(1, False), (F(t0 + 0.15), True)])
    elif o.name.startswith(("Banana_", "Moto_")):
        t0 = T_front(o.location.y) + random.uniform(0.0, 0.4)
        if t0 > 38: continue
        sweep(o, t0, random.uniform(10, 40), (random.uniform(-2, 2), random.uniform(-2, 2), random.uniform(-2, 2)),
              (random.uniform(-1.4, 1.4), random.uniform(-1.4, 1.4), 0), rise=2.0 if o.name.startswith("Moto_") else 1.5)
mud = bpy.data.materials["M_Terrain"].node_tree.nodes["MUD"].outputs[0]
for t, v in ((0, 0), (30.2, 0), (31.4, 1)):
    mud.default_value = v; mud.keyframe_insert("default_value", frame=F(t))
dv = bpy.data.materials["M_Dust"].node_tree.nodes["DUSTVOL"].inputs["Density"]
for t, v in ((0, 0), (30.5, 0), (32.0, 0.0004), (40, 0.0003)):
    dv.default_value = v; dv.keyframe_insert("default_value", frame=F(t))
dust = bpy.data.objects["DustVolume"]; key_hide(dust, [(1, True), (F(30.4), False)])
bowl_hide = [o for o in bpy.data.collections["Diorama"].objects]
for o in bowl_hide:
    if o.name.startswith(("D_Chunk_1", "D_ShockRing", "D_Pulse")):
        if o.name.startswith("D_Chunk_1"): key_hide(o, [(F(15.45), True)])
        continue
    key_hide(o, [(1, True), (F(12.4), False), (F(15.45), True)])
for o in bpy.data.objects:   # clear the camera's path through the beach furniture at 18-20 s
    if o.name.startswith(("Umbrella_", "Lounger_")) and abs(o.location.x - 15) < 2.5:
        bpy.data.objects.remove(o, do_unlink=True)
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=out)
print("ANIM_DONE")
