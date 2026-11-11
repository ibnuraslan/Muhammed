# Part 2 of 03_animate.py (exec'd): crowd instances with FK acting, the shooter silhouette, and the one camera.
random.seed(11)
VARIANTS = ["CrowdA", "CrowdB", "CrowdC", "CrowdD", "CrowdE", "CrowdF"]
def instance(variant, name, loc, yaw, coll, black=False):
    src = bpy.data.objects[variant]
    a = src.copy(); a.name = name; a.animation_data_clear(); coll.objects.link(a)
    a.location = loc; a.rotation_euler = (0, 0, yaw)
    for ch in src.children:
        if ch.type != "MESH": continue
        c = ch.copy(); c.name = name + "." + ch.name.split(".")[-1]; c.parent = a
        if black:
            c.data = ch.data.copy(); c.data.materials.clear(); c.data.materials.append(SIL)
        for m in c.modifiers:
            if m.type == "ARMATURE": m.object = a
        coll.objects.link(c)
    for pb in a.pose.bones: pb.rotation_mode = "QUATERNION"
    return a
SIL = bpy.data.materials.new("Silhouette"); SIL.use_nodes = True
SIL.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.004, 0.004, 0.005, 1)
SIL.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9

class FK:
    def __init__(self, a):
        self.a = a; self.R = Rig(a); B_ = a.data.bones
        self.up0 = {s: (B_["lowerarm01." + s].head_local - B_["upperarm01." + s].head_local).normalized() for s in "LR"}
        self.lo0 = {s: (B_["wrist." + s].head_local - B_["lowerarm01." + s].head_local).normalized() for s in "LR"}
    def arm(self, s, f, up, lo):
        q1 = self.up0[s].rotation_difference(up.normalized())
        q2 = (q1 @ self.lo0[s]).rotation_difference(lo.normalized())
        self.R.key_q("upperarm01." + s, f, self.R.local_q("upperarm01." + s, q1.to_matrix()))
        m = q1.to_matrix().inverted() @ q2.to_matrix() @ q1.to_matrix()
        self.R.key_q("lowerarm01." + s, f, self.R.local_q("lowerarm01." + s, m))
    def body(self, f, flex=0.0, twist=0.0, side=0.0, head=(0.0, 0.0)):
        for n, w_ in Human.SPINE_W.items(): self.R.key_rot(n, f, [("X", flex * w_), ("Y", side * w_), ("Z", twist * w_)])
        for n, w_ in Human.HEAD_W.items(): self.R.key_rot(n, f, [("X", head[0] * w_), ("Z", head[1] * w_)])

def pose_dirs(kind, s, t, ph):
    sx = 1 if s == "L" else -1; o = math.sin(2 * math.pi * (t / 38.0 + ph)); o2 = math.sin(2 * math.pi * (t / 13.0 + ph))
    if kind == "relaxed": return Vector((0.22 * sx, -0.06, -1)), Vector((0.08 * sx, -0.35, -1))
    if kind == "cheer": return Vector((0.35 * sx + 0.12 * o, -0.15, 1)), Vector((0.15 * sx + 0.25 * o, -0.15, 1))
    if kind == "wave":
        if s == "R": return Vector((-0.6, -0.25, 0.75)), Vector((-0.25 + 0.45 * o, -0.1, 1))
        return pose_dirs("relaxed", s, t, ph)
    if kind == "gasp": return Vector((0.25 * sx, -0.7, -0.6)), Vector((-0.25 * sx, -0.25, 1))
    if kind == "clap": return Vector((0.2 * sx, -0.8, -0.55)), Vector((-0.55 * sx * (0.6 + 0.4 * o2), -0.7, 0.3))
    if kind == "fist":
        if s == "L": return Vector((0.3, -0.25, 1)), Vector((0.1, -0.1, 1 + 0.3 * o2))
        return pose_dirs("clap", s, t, ph)
    if kind == "reach": return Vector((0.1 * sx, -1, 0.1)), Vector((0.0, -1, 0.15))
    return pose_dirs("relaxed", s, t, ph)

def act(fk, f0, f1, timeline, look_fn, flex_fn, timefn, ph, step=6):
    """timeline: [(t, kind), ...] in that character's time; blends 10 frames between kinds"""
    for f in list(range(f0, f1, step)) + [f1]:
        t = timefn(f)
        k0 = max([i for i, (tt, _) in enumerate(timeline) if tt <= t] or [0]); kind = timeline[k0][1]
        prev = timeline[k0 - 1][1] if k0 > 0 else kind; u = smooth((t - timeline[k0][0]) / 10.0) if k0 > 0 else 1.0
        for s in "LR":
            a0, b0 = pose_dirs(prev, s, t, ph); a1, b1 = pose_dirs(kind, s, t, ph)
            fk.arm(s, f, a0.normalized().lerp(a1.normalized(), u), b0.normalized().lerp(b1.normalized(), u))
        yw, pt = look_fn(f, t)
        fk.body(f, flex=flex_fn(t) + 2 * math.sin(t / 17.0 + ph * 6), twist=yw * 0.4 + 4 * math.sin(t / 23.0 + ph * 3),
                side=3 * math.sin(t / 29.0 + ph * 5), head=(pt, yw))

def look_at_yaw(a, tgt):
    d = (tgt - a.location); yaw_w = math.degrees(math.atan2(-d.x, -d.y)) - math.degrees(a.rotation_euler.z)
    yaw_w = (yaw_w + 180) % 360 - 180
    dist = d.to_2d().length; pitch = -math.degrees(math.atan2(d.z - 1.5, max(0.5, dist)))
    return max(-45, min(45, yaw_w)), max(-25, min(25, pitch))

HERO_HEAD = Vector((0, 0, 1.62))
CR = bpy.data.collections.new("Crowds"); sc.collection.children.link(CR)
# ---------------------------------------------------------------- street crowd: arc in front of the car, a few by the hotel door
SPOTS = []
for ring, (rad, n_) in enumerate(((2.3, 9), (3.3, 11), (4.4, 12))):
    for k in range(n_):
        a_ = R_(-160 + 140 * (k + 0.5 * (ring % 2)) / (n_ - 1 + 0.5))
        p = Vector((0.35 + rad * math.cos(a_) * 1.25, -0.2 + rad * math.sin(a_), STREET_Z))
        p.x += random.uniform(-0.2, 0.2); p.y += random.uniform(-0.2, 0.2)
        if (p - Vector((-1.15, -3.35, STREET_Z))).length < 0.8: continue        # shooter's space
        if min((p.to_2d() - Vector(q)).length for q in ((-1.9, -5.3), (-1.75, -4.4), (-0.3, -6.4), (-1.2, -2.6), (-0.8, -1.6))) < 0.75: continue   # camera lane
        if abs(p.y) < 1.1 and -1.6 < p.x < 2.4: continue                      # the car
        SPOTS.append(p)
for p in ((Vector((-3.2, 3.9, STREET_Z + 0.15))), Vector((2.8, 4.2, STREET_Z + 0.15)), Vector((3.6, 3.6, STREET_Z + 0.15)), Vector((-2.4, 4.4, STREET_Z + 0.15))):
    SPOTS.append(p)
print("STREET CROWD", len(SPOTS))
SHOOTER_POS = Vector((-1.15, -3.55, STREET_Z))
for i, p in enumerate(SPOTS):
    d = (HERO_HEAD - p); yaw = math.atan2(-d.x, -d.y) + R_(180) + random.uniform(-0.3, 0.3)
    a = instance(VARIANTS[i % 6], f"StreetP{i:02d}", p, yaw, CR); fk = FK(a)
    near = (p - SHOOTER_POS).to_2d().length < 1.6
    ph = random.random()
    tl = [(0, random.choice(["cheer", "wave", "cheer", "relaxed", "clap"])), (F_IMPACT + random.uniform(4, 14), "reach" if near else random.choice(["gasp", "gasp", "relaxed"])),
          (F_IMPACT + 70, "reach" if near else random.choice(["gasp", "relaxed"]))]
    def lk(f, t, a=a, near=near):
        if t > F_IMPACT + 6 and near: return look_at_yaw(a, SHOOTER_POS + Vector((0, 0, 1.4)))
        return look_at_yaw(a, Vector((0, 0, 1.6)))
    fx = pk([(0, 0.0), (F_IMPACT + 4, 0.0), (F_IMPACT + 14, -10.0 if not near else 14.0), (F_IMPACT + 60, -4.0 if not near else 18.0), (9999, -4.0)])
    act(fk, 1, F_OUT, tl, lk, fx, wt, ph)
    for o in [a] + list(a.children):
        o.hide_render = False; o.keyframe_insert("hide_render", frame=1); o.hide_render = True; o.keyframe_insert("hide_render", frame=F_OUT)
# the shooter: a black silhouette, arm raised toward the car; no weapon detail (a dark blob in the hand)
sh = instance("CrowdB", "Shooter", SHOOTER_POS, math.atan2(-(0 - SHOOTER_POS.x), -(0 - SHOOTER_POS.y)) + R_(180), CR, black=True)
fks = FK(sh)
aim = (HIT - (SHOOTER_POS + Vector((-0.2, 0, 1.4)))).normalized()
aim_l = sh.matrix_world.to_3x3().inverted() @ aim
for f in range(1, F_OUT, 4):
    t = wt(f); u = smooth((t - 70) / 30.0)
    up_ = pose_dirs("relaxed", "R", t, 0)[0].normalized().lerp(aim_l, u); lo_ = pose_dirs("relaxed", "R", t, 0)[1].normalized().lerp(aim_l, u)
    if t > F_IMPACT + 20:   # grabbed and pulled down
        v = smooth((t - F_IMPACT - 20) / 30.0); up_ = up_.lerp(Vector((-0.5, 0.3, -0.6)).normalized(), v); lo_ = lo_.lerp(Vector((-0.3, 0.2, -1)).normalized(), v)
    fks.arm("R", f, up_, lo_); a0, b0 = pose_dirs("relaxed", "L", t, 0); fks.arm("L", f, a0, b0)
    fks.body(f, flex=6 * u + (18 * smooth((t - F_IMPACT - 20) / 30.0) if t > F_IMPACT + 20 else 0), twist=0, head=(0, 0))
blob = bpy.data.objects.new("ShooterHandBlob", bpy.data.meshes.new("Blob")); CR.objects.link(blob)
import bmesh as _bm
bmm = _bm.new(); _bm.ops.create_cube(bmm, size=1.0); bmm.to_mesh(blob.data); bmm.free(); blob.scale = (0.035, 0.12, 0.06); blob.data.materials.append(SIL)
sc.frame_set(1); blob.matrix_world = (sh.matrix_world @ sh.pose.bones["wrist.R"].matrix) @ Matrix.Translation((0, 0.08, 0)) @ Matrix.Diagonal((0.035, 0.12, 0.06, 1))
cb = blob.constraints.new("CHILD_OF"); cb.target = sh; cb.subtarget = "wrist.R"; cb.inverse_matrix = (sh.matrix_world @ sh.pose.bones["wrist.R"].matrix).inverted()
for o in [sh, blob] + list(sh.children):
    o.hide_render = False; o.keyframe_insert("hide_render", frame=1); o.hide_render = True; o.keyframe_insert("hide_render", frame=F_OUT)
# ---------------------------------------------------------------- hall audience: packed floor + balcony, roaring in beat 9
HALL_SPOTS = []
for row in range(9):
    y = -2.9 - row * 0.95
    for k in range(-9 - row // 2, 10 + row // 2):
        x = k * 0.72 + (0.36 if row % 2 else 0) + random.uniform(-0.1, 0.1)
        if abs(x) > 13: continue
        HALL_SPOTS.append(Vector((x, y + random.uniform(-0.12, 0.12), -1.2)))
for k in range(-14, 15):
    HALL_SPOTS.append(Vector((k * 0.9 + random.uniform(-0.1, 0.1), -21.4 + random.uniform(-0.1, 0.1), 3.4)))
random.shuffle(HALL_SPOTS)
HALL_SPOTS = HALL_SPOTS[:150]
print("HALL CROWD", len(HALL_SPOTS))
def hall_time(f): return f
for i, p in enumerate(HALL_SPOTS):
    d = (HERO_HEAD - p); yaw = math.atan2(-d.x, -d.y) + R_(180) + random.uniform(-0.2, 0.2)
    a = instance(VARIANTS[(i * 5) % 6], f"HallP{i:03d}", p, yaw, CR); fk = FK(a); ph = random.random()
    tl = [(0, random.choice(["relaxed", "relaxed", "clap"])), (B[7] + random.uniform(0, 40), random.choice(["clap", "relaxed", "gasp"])),
          (B[8] + random.uniform(0, 30), random.choice(["cheer", "fist", "cheer", "clap", "wave"])), (1420 + random.uniform(0, 30), random.choice(["cheer", "clap", "fist"]))]
    def lk(f, t, a=a): return look_at_yaw(a, Vector((0, 0, 1.6)))
    fx = pk([(0, 0.0), (B[7], 4.0), (B[8], 8.0), (B[8] + 40, -6.0), (9999, -4.0)])
    act(fk, F_IN, END, tl, lk, fx, hall_time, ph, step=8)
    for o in [a] + list(a.children):
        o.hide_render = True; o.keyframe_insert("hide_render", frame=1); o.hide_render = False; o.keyframe_insert("hide_render", frame=F_IN)
# hide the crowd library
for o in bpy.data.collections["CrowdLib"].all_objects: o.hide_render = True; o.hide_viewport = True
bpy.data.collections["CrowdLib"].hide_render = True

# ---------------------------------------------------------------- the one camera: Catmull-Rom through framings (~1 per second)
cam_d = bpy.data.cameras.new("Cam"); cam_d.clip_start = 0.004; cam_d.clip_end = 200; cam_d.sensor_width = 36
cam = bpy.data.objects.new("Cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
sc.frame_set(400)
def P(v): return PL(v)
bul = lambda f: (SHOOTER.lerp(HIT, (f - F_FLASH) / (F_IMPACT - F_FLASH)))
K = [  # frame, position, target, lens
 (1,    Vector((4.2, -12.5, 5.6)),  Vector((0.3, -1.2, 0.5)), 26),
 (40,   Vector((0.9, -7.8, 2.9)),   Vector((-0.1, -1.0, 1.0)), 30),
 (75,   Vector((-0.6, -6.6, 1.6)),  Vector((-0.3, -1.0, 1.2)), 32),
 (100,  Vector((-1.9, -5.3, 0.85)), Vector((-0.5, -1.0, 1.2)), 32),   # low between heads, shooter silhouette in the foreground
 (F_FLASH, Vector((-1.75, -4.4, 0.95)), bul(F_FLASH + 6), 32),
 (135,  bul(135) + Vector((-0.30, -0.42, 0.10)), bul(141), 30),          # riding along the bullet
 (152,  bul(152) + Vector((-0.40, -0.55, 0.12)), bul(158), 30),
 (F_IMPACT, HIT + Vector((-0.55, -1.0, 0.12)), HIT + Vector((0, 0, 0.05)), 30),
 (187,  Vector((0.8, -1.5, 1.25)), Vector((0.0, -0.05, 0.5)), 26),   # looking down into the footwell at the planting feet
 (245,  Vector((0.95, -1.55, 0.95)), Vector((0.0, -0.05, 0.95)), 30),   # crane up his body
 (300,  Vector((0.55, -1.15, 1.6)),  Vector((0.0, -0.12, 1.55)), 35),   # face, straightening
 (B[2], Vector((0.15, -1.05, 1.45)), Vector((-0.05, -0.15, 1.38)), 35),
 (395,  Vector((-0.85, -0.85, 1.4)), P((0, 0, 0.02)), 35),              # orbit to the coat breast
 (B[3], P((-0.204, -0.544, 0.051)), P((0, 0, 0)), 35),
 (480, P((-0.06, -0.30, 0.03)), P((0, 0.03, -0.01)), 30),              # through the cloth
 (540, P((0.15, -0.27, 0.09)), P((0, 0.03, -0.02)), 28),
 (600, P((0.204, -0.092, 0.13)), P((0, 0.03, -0.02)), 30),
 (660, P((0.041, -0.038, 0.208)), P((0, 0.03, -0.01)), 30),          # over the fold edge
 (B[4], P((-0.153, -0.11, 0.075)), P((0.01, 0.04, -0.02)), 30),
 (780, P((0.178, -0.044, -0.016)), P((0.035, 0.047, -0.03)), 32),     # lateral to the steel case
 (840, P((0.124, 0.01, -0.139)), P((0.035, 0.047, -0.03)), 32),     # low over the hinge
 (B[5], P((-0.177, -0.129, 0.014)), P((0.01, -0.01, -0.02)), 35),      # alongside the bullet
 (940, P((-0.147, -0.035, 0.048)), P((0.015, 0.025, -0.02)), 35),
 (B[6], P((-0.133, 0.016, -0.037)), P((0.02, 0.05, -0.02)), 35),       # push to the dent
 (1060, P((-0.272, 0.046, -0.057)), P((0.0, 0.08, -0.04)), 30),        # past the ribs: bullet short of the lung
 (1120, P((-0.442, -0.134, 0.055)), P((0.0, 0.07, -0.03)), 28),
 (B[7], Vector((-0.55, -1.35, 1.4)), Vector((-0.05, -0.2, 1.35)), 30),  # pull out: podium
 (1245, Vector((0.35, -2.5, 1.55)),  Vector((-0.05, -0.2, 1.55)), 30),
 (B[8], Vector((1.3, -2.7, 1.7)),    Vector((0.0, -0.2, 1.5)), 30),
 (1340, Vector((1.4, 1.5, 2.1)),     Vector((0.0, -3.0, 0.9)), 26),     # behind him, the packed hall
 (1400, Vector((-0.6, 2.2, 3.2)),    Vector((0.0, -5.0, 0.4)), 26),
 (1455, Vector((-1.4, 1.4, 6.0)),    Vector((0.0, -4.5, 0.0)), 24),     # crane up
 (END,  Vector((-1.5, 1.2, 6.4)),    Vector((0.0, -4.5, 0.0)), 24),
]
cp = catmull([(k[0], k[1]) for k in K]); ct = catmull([(k[0], k[2]) for k in K]); cl = pchip([(k[0], float(k[3])) for k in K])
cam.rotation_mode = "QUATERNION"
for f in range(1, END + 1):
    p = cp(f); t = ct(f); cam.location = p
    q = (t - p).to_track_quat("-Z", "Y"); roll = 4.0 * math.sin(f / 70.0) if f < B[3] or f > B[7] else 0.0
    cam.rotation_quaternion = q @ Quaternion((0, 0, 1), R_(roll))
    cam_d.lens = cl(f)
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_quaternion", frame=f); cam_d.keyframe_insert("lens", frame=f)
json.dump([{"beat": i + 1, "frame": f_, "first_words": w_} for i, (f_, w_) in enumerate(zip(B, [
    "The bullet hit him", "somehow, he stayed", "So how was", "Well, Roosevelt had", "along with a", "The bullet tore", "kept it from", "And despite the", "he insisted on"]))],
    open(os.path.dirname(HERE) + "/beats.json", "w"), indent=1)
