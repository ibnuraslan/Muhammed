"""Tsunami2004 v013 stage B: the family's acting, the sea (drawdown, wave, flood, drain), the earthquake, the debris,
the ONE camera (no cuts), golden hour, VO. Built to the client's VO (Tsunami2004 v012 timing, frames 1-2066).
blender -b a.blend --python 02_animate.py -- <vo.mp3> <out.blend>
Beats (frame = 1 + round(s*60) of the first word): 1 sea pulled back | 127 ocean floor bare | 259 people walked out |
395 then they saw it | 503 a wave heading for the shore | 648 massive tsunami | 740 set off by an earthquake (798 'earthquake') |
909 as it got closer, it grew | 1025 up to 100 feet | 1217 it hit the coast | 1375 flattening everything | 1509 whole
neighborhoods | 1621 nothing but rubble | 1689 167,000 people lost their lives (end 2066).
No person is ever shown being hit: the family runs off frame (hidden from 1245, while off frame) and is next seen on the
high ground at the end (shown from 1682, off frame)."""
import bpy, sys, math, random, os, json
from mathutils import Vector, Matrix, Quaternion
PIPE = "/home/user/Muhammed/blender/pipeline"
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(PIPE + "/anim_lib.py").read())
exec(open(PIPE + "/hand_poses.py").read())
exec(open(HERE + "/lib_anim.py").read())
exec(open(HERE + "/lib_tsu.py").read())
args = sys.argv[sys.argv.index("--") + 1:]
VO, OUT = args[0], args[1]
random.seed(25)
END = 2066
O = bpy.data.objects
def ground_z(x, y): return G(x, y)          # anim_lib's walk() plants the feet on the real ground
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); LOG.append(s); print("LOG", s)
O["Ocean"].modifiers["Ocean"].show_viewport = False        # keying speed; restored before saving

# ================================================================== the sea: WaveCtl loc=(L, Yf, A) scale=(p, curl, phase)
Lk_ = pchip([(1, 0.0), (55, -0.12), (127, -0.9), (259, -1.8), (400, -3.5), (1150, -3.5), (1260, 0.0), (END, 0.0)])
YF = pchip([(1, -2600), (399, -2600), (400, -900), (470, -820), (503, -780), (648, -650), (740, -580), (800, -530), (909, -400), (960, -360), (1025, -300),
            (1060, -230), (1100, -125), (1150, -62), (1200, -27), (1229, -8), (1260, 25), (1300, 60), (1375, 110), (1450, 160),
            (1509, 210), (1600, 300), (1660, 370), (1700, 430), (END, 470)])
AF = pchip([(1, 0.0), (400, 0.0), (470, 6.0), (503, 8.0), (648, 10.0), (800, 11.5), (909, 14.0), (960, 17.0), (1025, 22.0), (1060, 28.0), (1100, 33.0),
            (1150, 35.0), (1200, 35.0), (1229, 34.0), (1260, 30.0), (1300, 22.0), (1375, 14.0), (1450, 10.0), (1509, 8.0), (1600, 6.0),
            (1660, 3.5), (1700, 0.0), (END, 0.0)])
CURL = pchip([(1, 0.0), (900, 0.05), (1060, 0.25), (1229, 0.35), (1300, 0.1), (1400, 0.0), (END, 0.0)])
PLATEAU = 0.55
WC = O["WaveCtl"]; QC = O["QuakeCtl"]
for f in list(range(1, END + 1, 2)) + [END]:
    WC.location = (Lk_(f), YF(f), AF(f)); WC.scale = (PLATEAU, CURL(f), f * 0.012)
    WC.keyframe_insert("location", frame=f); WC.keyframe_insert("scale", frame=f)
set_interp(WC, 'LINEAR')
def surf(x, y, f): return wave_z(x, y, Lk_(f), YF(f), AF(f), PLATEAU, q=tuple(QC.location) if False else (0, 0, 0))

# ---- the earthquake (cut-away at y=-600): the wedge snaps up, a flash at the focus, a shock ring, the bulge above
QB = pchip([(1, 0.0), (800, 0.0), (812, 1.8), (850, 5.0), (900, 5.5), (960, 2.0), (1010, 0.0), (END, 0.0)])
for f in range(1, END + 1, 4):
    QC.location = (60.0, -240.0, QB(f)); QC.keyframe_insert("location", frame=f)
set_interp(QC, 'LINEAR')
WEDGE, FOCUS, RING = O["SEC_Wedge"], O["SEC_Focus"], O["SEC_Ring"]
WEDGE.rotation_mode = 'XYZ'
for f, rx, dz in ((1, 0.0, 0.0), (799, 0.0, 0.0), (803, -4.2, 0.9), (807, -3.2, 0.7), (812, -3.6, 0.8), (830, -3.5, 0.8), (END, -3.5, 0.8)):
    WEDGE.rotation_euler.x = math.radians(rx); WEDGE.keyframe_insert("rotation_euler", frame=f)
    WEDGE.delta_location = (0, 0, dz); WEDGE.keyframe_insert("delta_location", frame=f)
set_interp(WEDGE, 'LINEAR')
for f, s_ in ((1, 0.01), (797, 0.01), (801, 3.2), (812, 2.0), (850, 1.6), (880, 1.2), (900, 0.01), (END, 0.01)):
    FOCUS.scale = (s_,) * 3; FOCUS.keyframe_insert("scale", frame=f)
for f, s_ in ((1, 0.01), (799, 0.01), (800, 1.0), (860, 45.0), (861, 0.01), (END, 0.01)):
    RING.scale = (s_,) * 3; RING.keyframe_insert("scale", frame=f)
set_interp(FOCUS, 'LINEAR'); set_interp(RING, 'LINEAR')

# ================================================================== the family
PEOPLE = {}
for name in ("Dad", "Mom", "Boy", "Girl"):
    rig = O[name]; ct = make_human_ctrl(rig); add_hand_limits(rig)
    for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'
    for s in "LR":          # arms are animated in FK (no hand contacts in this film); IK off
        for c in rig.pose.bones["lowerarm02." + s].constraints:
            if c.type == 'IK': c.influence = 0.0
        for c in rig.pose.bones["wrist." + s].constraints:
            if c.type == 'COPY_ROTATION': c.influence = 0.0
    PEOPLE[name] = (rig, ct, Human(ct))
# standing spots at the water's edge, the walk out, the run (+Y, past the camera's left), the hill
X0 = {"Dad": -3.0, "Mom": -1.5, "Boy": 0.1, "Girl": 1.5}
Y0 = {"Dad": -8.4, "Mom": -8.9, "Boy": -9.2, "Girl": -8.7}
YW = {"Dad": -13.0, "Mom": -12.9, "Boy": -14.2, "Girl": -13.6}            # where the walk out stops
WALK = (150, 400)
STRIDE = {"Dad": (1.45, 2.6), "Mom": (1.3, 2.4), "Boy": (1.05, 1.9), "Girl": (0.95, 1.8)}   # (walk, run) cycle length
RUN0, RUN1 = 565, 1290
def run_dist(f):
    return pchip([(RUN0, 0.0), (600, 0.9), (640, 3.6), (RUN1, 3.6 + 0.10 * (RUN1 - 640))])(f)
DIR = math.radians(51.5)            # on the hill they face the town and the mosque
HC = Vector((-70.0, 280.0))
LAT = Vector((math.cos(DIR), math.sin(DIR)))
HILLPOS = {"Dad": HC + LAT * -1.25, "Boy": HC + LAT * -0.45 + Vector((0.2, 0.15)), "Mom": HC + LAT * 0.5, "Girl": HC + LAT * 1.35 + Vector((0.15, 0.1))}
SHOW_HILL = 1682

def arm(ct, s, f, lower=38.0, swing=0.0, elbow=18.0, out=0.0, inward=None):
    sg = 1 if s == "L" else -1
    ct.key_rot("upperarm01." + s, f, [("Y", sg * (lower - out)), ("X", -swing)])
    # the elbow bends about its real hinge (perpendicular to the forearm and to 'forward'), so the forearm swings
    # forward and up in the arm's own plane, never out to the side (no T/A-pose wings)
    fr = (ct.BN["wrist." + s].head_local - ct.BN["lowerarm01." + s].head_local).normalized()
    axh = fr.cross(Vector((0, -1, 0))).normalized()
    if (Matrix.Rotation(math.radians(30), 3, axh) @ fr).y > 0: axh = -axh
    ct.key_q("lowerarm01." + s, f, ct.local_q("lowerarm01." + s, Matrix.Rotation(math.radians(elbow), 3, axh)))

def stand(h, f, pos2, yaw, flex=2.0, side=0.0, twist=0.0, head=(0.0, 0.0), dz=0.0, stance=1.0):
    z = G(pos2.x, pos2.y) + h.root_head.z - 0.012 + dz
    h.key_root(f, Vector((pos2.x, pos2.y, z)), yaw=yaw, flex=flex * 0.4, side=side)
    h.key_spine(f, flex=flex, twist=twist, side=side * 0.5, head=head)
    for s in "LR":
        xy = h.foot_xy(s, pos2, yaw)
        xy = pos2 + (xy - pos2) * stance
        h.key_foot(s, f, xy, yaw)

for name, (rig, ct, h) in PEOPLE.items():
    rnd = random.Random(hash(name) % 1000)
    p0 = Vector((X0[name], Y0[name])); pw = Vector((X0[name] + rnd.uniform(-0.3, 0.3), YW[name]))
    # ---- 1..150: at the water's edge, watching the sea pull back (breathing, small weight shifts, head turns)
    for f in range(1, WALK[0] + 1, 10):
        stand(h, f, p0, 0.0, flex=2.0 + 0.8 * math.sin(f / 35.0 + rnd.random()), side=1.5 * math.sin(f / 50.0 + rnd.random()),
              head=(4.0 + 3 * math.sin(f / 40.0), 8.0 * math.sin(f / 70.0 + rnd.random() * 3)))
    # ---- 150..400: they walk out onto the bare sea floor, confused, looking down at the fish
    path_w = lambda f, a_=p0, b_=pw: a_.lerp(b_, smooth((f - WALK[0]) / (WALK[1] - WALK[0]))).to_3d()
    h.walk(path_w, lambda f: 0.0, WALK[0], WALK[1], stride=STRIDE[name][0], duty=0.62, lift=0.07, bob=0.018, crouch=0.02, lean=3.0, step=2)
    for f in range(WALK[0], WALK[1] + 1, 2):        # heads down to the fish, then around (same frames as walk(): no fighting keys)
        u = (f - WALK[0]) / (WALK[1] - WALK[0])
        h.key_spine(f, flex=4.0 + 6 * math.sin(math.pi * u), twist=6 * math.sin(f / 30.0 + rnd.random()),
                    head=(14.0 * math.sin(math.pi * u) + 4, 15.0 * math.sin(f / 45.0 + rnd.random() * 3)))
    # ---- 400..565: they stop; at 'saw it' (395..) they look up at the horizon; fear builds
    for f in range(WALK[1] + 4, RUN0 + 1, 8):
        u = (f - 400) / 165.0
        stand(h, f, pw, 0.0, flex=1.0 - 3.0 * u, side=1.0 * math.sin(f / 30.0), twist=3 * math.sin(f / 25.0 + rnd.random()),
              head=(-6.0 - 4 * u, 4.0 * math.sin(f / 40.0 + rnd.random() * 3)), stance=1.05)
    # ---- 565..1244: they turn and run for the land (+Y), arms pumping
    def path_r(f, a_=pw): return Vector((a_.x, a_.y + run_dist(f), 0.0))
    def yaw_r(f): return 180.0 * smooth((f - RUN0) / 32.0)
    st = STRIDE[name][1]
    h.walk(path_r, yaw_r, RUN0, RUN1, stride=st, duty=0.36, lift=0.20, bob=0.045, crouch=0.07, lean=11.0, step=2)
    for f in range(RUN0, RUN1 + 1, 2):
        d = run_dist(f); cyc = d / st
        amp = 38.0 * smooth((f - RUN0) / 40.0)
        for s, sg in (("L", -1), ("R", 1)):
            arm(ct, s, f, lower=43.0, swing=10.0 + sg * amp * math.cos(2 * math.pi * cyc), elbow=20.0 + 65.0 * smooth((f - RUN0) / 30.0))
        h.key_spine(f, flex=11.0, twist=-8 * math.sin(2 * math.pi * cyc), head=(-6.0, 0.0))
    # ---- the hill (from 1680): standing, quiet, facing the town; breathing, head turns
    hp = HILLPOS[name]; yh = math.degrees(DIR) + 180.0        # they face inland, the ruins behind them
    stand(h, SHOW_HILL - 3, path_r(RUN1).to_2d(), 180.0)        # holds the run's end pose while hidden
    for f in range(SHOW_HILL - 2, END + 1, 12):
        bow = {"Mom": 10.0, "Dad": 3.0, "Boy": 2.0, "Girl": 6.0}[name]
        look = {"Dad": pchip([(1680, 0.0), (1860, 0.0), (1900, 38.0), (1960, 38.0), (2000, 5.0), (END, 0.0)])(f),
                "Mom": -6.0 + 8.0 * math.sin(f / 70.0), "Boy": pchip([(1680, 0.0), (1770, 0.0), (1800, -22.0), (1880, -22.0), (1910, 0.0), (END, 0.0)])(f),
                "Girl": 8.0 * math.sin(f / 60.0)}[name]
        stand(h, f, hp, yh, flex=2.0 + 1.5 * math.sin(f / 30.0), side=1.5 * math.sin(f / 45.0 + rnd.random()), twist=4.0 * math.sin(f / 80.0 + rnd.random()),
              head=(bow + 4 * math.sin(f / 55.0), look + 4.0 * math.sin(f / 90.0 + rnd.random() * 3)))
    # ---- arms outside the run: relaxed, slightly bent, small sway
    for f in list(range(1, RUN0, 8)) + list(range(SHOW_HILL - 2, END + 1, 10)):
        if f > RUN0 - 3 and f < SHOW_HILL - 2: continue
        busy = {"Dad": ("R", 416, 566), "Boy": ("L", 286, 390)}.get(name)
        sw = 3.0 * math.sin(f / 40.0 + rnd.random())
        walking = WALK[0] <= f <= WALK[1]
        if walking:
            ph = 2 * math.pi * (f - WALK[0]) / (WALK[1] - WALK[0]) * ((pw - p0).length / STRIDE[name][0])
            sw = 14.0 * math.cos(ph)
        for s, sg in (("L", 1), ("R", -1)):
            if busy and s == busy[0] and busy[1] <= f <= busy[2]: continue
            arm(ct, s, f, lower=41.0, swing=4.0 + sg * sw, elbow=18.0 + 4 * math.sin(f / 33.0))
    for s in "LR":
        apply_pose(rig, s, "relaxed", 1)
        apply_pose(rig, s, "relaxed", END)
    # faces: calm -> puzzled -> fear (saw it) -> shout/run -> grief on the hill
    face_keys = [(1, 0.0, 0.1, 0.0), (150, 0.0, 0.4, 0.05), (300, -0.1, 0.6, 0.08), (395, 0.0, 0.5, 0.05), (450, -0.2, 0.9, 0.25),
                 (520, -0.3, 1.0, 0.45), (600, -0.3, 1.0, 0.5), (RUN1, -0.3, 1.0, 0.4),
                 (SHOW_HILL, -0.35, -0.5, 0.05), (1850, -0.35, -0.6, 0.05), (END, -0.3, -0.5, 0.03)]
    for f, sm, br, jw in face_keys:
        key_face(rig, f, smile=sm, brow=br, jaw=jw)
    blinks(rig, [b + rnd.randint(-8, 8) for b in (70, 210, 350, 470, 640, 1720, 1810, 1905, 1995)])
    # visibility: hidden while off frame between the run and the hill
    set_interp(rig, 'LINEAR')
    log("person", name, "walk", tuple(round(v, 2) for v in pw), "run end", tuple(round(v, 2) for v in path_r(RUN1)))

# Dad: points at the horizon (430-520) and shouts (520-560), then runs
rig, ct, h = PEOPLE["Dad"]
for f, sw, lo, el in ((420, 4.0, 37.0, 18.0), (440, 55.0, 30.0, 12.0), (455, 78.0, 26.0, 8.0), (515, 80.0, 26.0, 8.0), (540, 40.0, 33.0, 20.0), (562, 6.0, 37.0, 22.0)):
    arm(ct, "R", f, lower=lo, swing=sw, elbow=el)
apply_pose(rig, "R", "relaxed", 425); apply_pose(rig, "R", "point", 452); apply_pose(rig, "R", "point", 515); apply_pose(rig, "R", "relaxed", 545)
key_face(rig, 530, smile=-0.3, brow=1.0, jaw=0.75); key_face(rig, 556, smile=-0.3, brow=1.0, jaw=0.3)
# Boy: points down at a fish on the sea floor (300-370)
rig, ct, h = PEOPLE["Boy"]
for f, sw, lo, el in ((290, 4.0, 37.0, 18.0), (310, 42.0, 30.0, 10.0), (360, 44.0, 30.0, 10.0), (385, 5.0, 37.0, 18.0)):
    arm(ct, "L", f, lower=lo, swing=sw, elbow=el)
apply_pose(rig, "L", "point", 312); apply_pose(rig, "L", "point", 358); apply_pose(rig, "L", "relaxed", 382)
for name in PEOPLE:
    set_interp(PEOPLE[name][0], 'LINEAR')

# ================================================================== the fish flop on the sand (always touching it)
for i, fo in enumerate([o for o in O if o.name.startswith("Fish")]):
    rnd = random.Random(i); base_rz = fo.rotation_euler.z; z0 = fo.location.z
    for f in range(1, 700, 3):
        ph = f / 9.0 + rnd.random() * 6
        hop = max(0.0, math.sin(ph * 0.5)) ** 6 * 0.05            # short hops, landing back on the sand
        fo.location.z = z0 + hop
        fo.rotation_euler.z = base_rz + 0.25 * math.sin(ph)
        fo.rotation_euler.x = 0.35 * max(0.0, math.sin(ph * 0.5)) ** 6
        fo.keyframe_insert("location", frame=f); fo.keyframe_insert("rotation_euler", frame=f)
    set_interp(fo, 'LINEAR')

# ================================================================== what the water does to the land
def f_hit(y):
    for f in range(400, END):
        if YF(f) >= y: return f
    return END
def sweep(o, f0, kind):
    """kind: 'palm' (snaps landward and goes under), 'float' (carried by the surge, tumbling, then under), 'house'"""
    rnd = random.Random(hash(o.name) % 9999)
    loc0 = o.location.copy(); rot0 = o.rotation_euler.copy()
    o.keyframe_insert("location", frame=1); o.keyframe_insert("rotation_euler", frame=1)
    o.keyframe_insert("location", frame=f0); o.keyframe_insert("rotation_euler", frame=f0)
    if kind == 'palm':
        for k, (df, tilt, sink) in enumerate(((8, 30, 0.0), (18, 70, 0.5), (30, 82, 2.0), (70, 84, 7.0))):
            o.rotation_euler = (rot0.x - math.radians(tilt), rot0.y, rot0.z)      # trunk falls toward +Y (landward)
            o.location = loc0 + Vector((0, 2.0 * k, -sink))
            o.keyframe_insert("location", frame=f0 + df); o.keyframe_insert("rotation_euler", frame=f0 + df)
    elif kind == 'float':
        spin = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * 0.06
        y = loc0.y
        for df in range(2, 101, 2):
            f = f0 + df
            y = max(y, YF(f) - 6.0 - df * 0.05)
            z = surf(loc0.x, y, f) + 0.2 - (max(0, df - 70) / 30.0) ** 2 * 6.0
            o.location = (loc0.x + 0.03 * df * rnd.uniform(-1, 1), y, z)
            o.rotation_euler = (rot0.x + spin.x * df, rot0.y + spin.y * df, rot0.z + spin.z * df)
            o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
    elif kind == 'house':
        ax = rnd.choice((0, 1)); sg = rnd.choice((-1, 1)); tilt = math.radians(rnd.uniform(14, 26))
        for df, u in ((10, 0.1), (30, 0.35), (60, 0.65), (100, 0.9), (130, 1.0)):
            r_ = rot0.copy()
            if ax == 0: r_.x += sg * tilt * u
            else: r_.y += sg * tilt * u
            o.rotation_euler = r_
            o.location = loc0 + Vector((0, 9.0 * u, -14.0 * u ** 1.6))
            o.keyframe_insert("location", frame=f0 + df); o.keyframe_insert("rotation_euler", frame=f0 + df)
    set_interp(o, 'LINEAR')
for o in O:
    n = o.name
    if n.startswith("Palm"): sweep(o, f_hit(o.location.y - 4), 'palm')
    elif n.startswith(("Longtail", "Rowboat", "Umbrella", "Car")) and n != "LongtailTipped": sweep(o, f_hit(o.location.y - 3), 'float')
    elif n.startswith("House"): sweep(o, f_hit(o.location.y - 6), 'house')
    elif n == "LongtailTipped" or n.startswith(("Coral", "Fish")): sweep(o, f_hit(o.location.y - 2), 'float')
# rubble rises out of sight under the brown flood, where the houses stood
for o in O:
    if o.name.startswith("Rubble"):
        f0 = max(f_hit(o.location.y) + 25, 1300); f1 = min(f0 + 50, 1540)
        zf = o["z_final"]
        o.location.z = zf - 4.0; o.keyframe_insert("location", frame=1); o.keyframe_insert("location", frame=f0)
        o.location.z = zf; o.keyframe_insert("location", frame=f1)
        set_interp(o, 'LINEAR')
        if surf(o.location.x, o.location.y, f1) < zf + 1.2:
            log("WARN rubble top above the flood at its rise end", o.name, f1)

# ================================================================== golden hour (from 1650): sky, clouds, sun
W = bpy.context.scene.world; SM = W.node_tree.nodes["SkyMix"]; CC = W.node_tree.nodes["CloudCol"]
SUN = O["Sun"]; SUN.rotation_mode = 'XYZ'
for f, u in ((1, 0.0), (1650, 0.0), (1900, 0.8), (END, 0.8)):
    SM.inputs["Factor"].default_value = u; SM.inputs["Factor"].keyframe_insert("default_value", frame=f)
    CC.inputs["Factor"].default_value = u; CC.inputs["Factor"].keyframe_insert("default_value", frame=f)
    SUN.rotation_euler = (math.radians(45 + 27 * u), 0, math.radians(20 - 58.5 * u)); SUN.keyframe_insert("rotation_euler", frame=f)
    SUN.data.color = (1.0, 0.95 - 0.33 * u, 0.86 - 0.56 * u); SUN.data.keyframe_insert("color", frame=f)
    SUN.data.energy = 4.5 - 0.6 * u; SUN.data.keyframe_insert("energy", frame=f)

# ================================================================== camera: ONE camera, PCHIP paths, level horizon
sc = bpy.context.scene
cam_d = bpy.data.cameras.new("CAM_Film"); CAM = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(CAM); sc.camera = CAM
cam_d.sensor_fit = 'VERTICAL'; cam_d.sensor_height = 36.0; cam_d.clip_start = 0.05; cam_d.clip_end = 30000.0; cam_d.dof.use_dof = False
CAM.rotation_mode = 'QUATERNION'
K = [  # frame, position, aim, lens
    (1, (2.4, -13.4, 1.05), (-0.7, -8.6, 1.15), 32),          # faces; the water pulls away from their feet
    (50, (3.0, -15.0, 1.0), (-0.5, -8.8, 1.0), 30),
    (95, (4.0, -17.5, 1.0), (7.0, -60.0, 0.0), 26),           # turn: low over the retreating sea, the edge racing away
    (127, (5.0, -21.0, 0.85), (11.0, -38.0, 0.2), 26),         # the bare sea floor: fish, the stranded boat
    (165, (3.5, -22.5, 0.9), (-0.5, -11.0, 0.9), 30),
    (210, (2.0, -19.5, 1.05), (-0.6, -10.5, 1.0), 34),
    (259, (1.5, -18.0, 1.1), (-0.6, -11.5, 1.0), 35),         # they walk out toward the camera
    (340, (1.4, -18.0, 1.1), (-0.8, -12.8, 1.05), 35),
    (395, (4.0, -18.0, 1.35), (-1.0, -13.0, 1.3), 30),
    (450, (5.6, -14.6, 1.6), (-2.5, -14.6, 1.4), 28),         # beside them: faces in three-quarter, Dad points
    (503, (-3.0, -18.5, 2.0), (-6.0, -780.0, 2.5), 60),       # a wave, heading for the shore: push in on the white line
    (545, (-2.6, -21.0, 2.0), (-6.0, -760.0, 3.0), 90),
    (575, (2.0, -19.0, 1.6), (-0.6, -12.8, 1.5), 32),         # back to their faces: the shout, the turn
    (612, (2.0, -16.0, 6.0), (-0.5, -200.0, 2.0), 26),
    (648, (0.0, -300.0, 55.0), (0.0, -650.0, 2.0), 30),       # high above the sea: the front across the whole ocean
    (700, (-30.0, -420.0, 42.0), (-20.0, -600.0, 8.0), 26),
    (745, (-75.0, -232.0, 12.0), (0.0, -250.0, -22.0), 24),   # dive toward the cut-away
    (766, (-95.0, -248.0, -5.0), (0.0, -250.0, -30.0), 22),   # through the surface
    (790, (-150.0, -258.0, -22.0), (0.0, -248.0, -40.0), 20),
    (860, (-140.0, -236.0, -20.0), (0.0, -248.0, -36.0), 20),
    (880, (-125.0, -244.0, -10.0), (-40.0, -262.0, 6.0), 22),  # tilt up toward the surface, the cut still in frame
    (898, (-112.0, -248.0, 3.0), (-80.0, -390.0, 10.0), 24),  # straight up and out: the wave right there
    (960, (-70.0, -205.0, 14.0), (-30.0, -360.0, 14.0), 24),  # as it got closer, it grew
    (1025, (-20.0, -60.0, 22.0), (-5.0, -300.0, 16.0), 24),
    (1050, (-0.7, 22.0, 10.0), (-0.7, -60.0, 6.0), 24),       # backward over the beach (still looking at the sea), over their heads
    (1062, (-0.7, 46.0, 3.6), (-0.7, 30.0, 2.4), 20),         # their faces as they run, the wall behind them
    (1110, (-0.7, 50.5, 3.6), (-0.7, 20.0, 5.5), 20),
    (1170, (2.0, 75.0, 6.0), (0.0, -20.0, 12.0), 32),         # pull back inland: the wall towers over the palms and the hotel
    (1205, (6.0, 82.0, 12.0), (10.0, -15.0, 20.0), 30),
    (1229, (-4.0, 78.0, 26.0), (0.0, -10.0, 20.0), 26),       # it hits the coast (the family has run off the bottom of frame)
    (1260, (0.0, 98.0, 36.0), (4.0, 20.0, 4.0), 26),
    (1300, (5.0, 140.0, 48.0), (5.0, 40.0, 6.0), 24),
    (1375, (0.0, 178.0, 14.0), (-4.0, 110.0, 3.0), 24),       # rides ahead of the surge up the road: houses go under
    (1450, (0.0, 222.0, 13.0), (-2.0, 155.0, 3.0), 24),
    (1509, (-15.0, 262.0, 30.0), (0.0, 170.0, 2.0), 24),
    (1565, (-60.0, 310.0, 70.0), (15.0, 150.0, 0.0), 26),     # whole neighbourhoods gone
    (1621, (-45.0, 300.0, 62.0), (35.0, 175.0, 4.0), 28),
    (1689, (-28.0, 258.0, 30.0), (45.0, 186.0, 8.0), 30),     # the rubble, the mosque standing
]

D3 = Vector((math.sin(DIR), -math.cos(DIR), 0.0)); L3 = Vector((LAT.x, LAT.y, 0.0)); HC3 = Vector((HC.x, HC.y, G(HC.x, HC.y)))
def hk(f, back, lat, up, aim_fwd, aim_lat, aim_up, lens):
    return (f, tuple(HC3 - D3 * back + L3 * lat + Vector((0, 0, up))), tuple(HC3 + D3 * aim_fwd + L3 * aim_lat + Vector((0, 0, aim_up))), lens)
K += [hk(1725, 9.0, 1.5, 4.0, 0.0, 0.0, 1.0, 26),           # down to the family on the high ground (all four in frame)
      hk(1770, 4.6, -0.5, 1.55, 0.0, -0.5, 1.3, 30),       # faces; the ruins and the mosque behind them
      hk(1840, 4.6, 0.7, 1.5, 0.0, 0.7, 1.25, 30),
      hk(1920, 6.0, 0.2, 2.8, 12.0, 0.0, 0.0, 26),
      hk(2000, 7.0, 0.8, 5.0, 40.0, 0.0, -1.0, 26),
      hk(END, 8.0, 1.6, 7.0, 45.0, 0.0, -4.0, 24)]
ks = [(k[0], Vector(k[1]), Vector(k[2]), k[3]) for k in K]
fx = [pchip([(k[0], k[1][i]) for k in ks]) for i in range(3)]
ax = [pchip([(k[0], k[2][i]) for k in ks]) for i in range(3)]
fl = pchip([(k[0], k[3]) for k in ks])
for f in range(1, END + 1):
    p = Vector([fx[i](f) for i in range(3)]); a_ = Vector([ax[i](f) for i in range(3)])
    if 800 <= f <= 840:      # the quake shakes the camera a little
        k_ = (840 - f) / 40.0; p += Vector((0, math.sin(f * 2.1), math.sin(f * 2.9))) * 0.35 * k_
    q = (a_ - p).to_track_quat('-Z', 'Y')
    CAM.location = p; CAM.rotation_quaternion = q; cam_d.lens = fl(f)
    CAM.keyframe_insert("location", frame=f); CAM.keyframe_insert("rotation_quaternion", frame=f); cam_d.keyframe_insert("lens", frame=f)
set_interp(CAM, 'LINEAR'); set_interp(cam_d, 'LINEAR')
# safety: the camera never under the ground (outside the cut-away hole) and never just under the water where nothing is
for f in range(1, END + 1, 2):
    p = Vector([fx[i](f) for i in range(3)])
    in_hole = p.x < 0 and SECTION_Y[0] < p.y < SECTION_Y[1]
    if not in_hole and p.z < G(p.x, p.y) + 0.4: log("WARN camera near/below ground", f, tuple(round(v, 2) for v in p))
from bpy_extras.object_utils import world_to_camera_view
def fam_in_view(f):
    sc.frame_set(f); seen = []
    for name, (rig, ct, h) in PEOPLE.items():
        hp_ = rig.matrix_world @ rig.pose.bones["head"].head
        for pt in (hp_, hp_ - Vector((0, 0, 1.2))):
            c = world_to_camera_view(sc, CAM, pt)
            if c.z > 0 and -0.05 < c.x < 1.05 and -0.05 < c.y < 1.05: seen.append(name); break
    return seen
HIDE = None
for f in range(1200, RUN1):
    if not fam_in_view(f) and not fam_in_view(f + 1) and not fam_in_view(f + 3):
        HIDE = f; break
log("HIDE frame", HIDE)
if HIDE is None: HIDE = RUN1; log("WARN no off-frame hide frame found")
for name, (rig, ct, h) in PEOPLE.items():
    for o in [rig] + list(rig.children):
        vis(o, 1, True); vis(o, HIDE + 1, False); vis(o, SHOW_HILL, True)
for f in (HIDE - 3, HIDE, HIDE + 1, SHOW_HILL - 1, SHOW_HILL, SHOW_HILL + 2):
    log("FAMVIEW", f, fam_in_view(f))
# a small catchlight riding with the camera (eyes never read as black holes)
cl = bpy.data.lights.new("Catchlight", 'POINT'); cl.energy = 6.0; cl.shadow_soft_size = 0.15
clo = bpy.data.objects.new("Catchlight", cl); sc.collection.objects.link(clo); clo.parent = CAM; clo.location = (0.0, 0.15, 0.0)

# ================================================================== VO + range
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor; coll = se.strips if hasattr(se, "strips") else se.sequences
snd = coll.new_sound("VO", VO, 1, 1)
sc.frame_start, sc.frame_end = 1, END
O["Ocean"].modifiers["Ocean"].show_viewport = True
json.dump([{"beat": i + 1, "frame": f, "first_words": w} for i, (f, w) in enumerate((
    (1, "The sea suddenly pulled back"), (127, "leaving the ocean floor bare"), (259, "People walked out, confused"),
    (395, "and then they saw it"), (503, "A wave heading for the shore"), (648, "It was a massive tsunami"),
    (740, "set off by an earthquake under the sea"), (909, "As it got closer, it grew"), (1025, "reaching up to 100 feet high"),
    (1217, "It hit the coast with unimaginable force"), (1375, "flattening everything in its way"),
    (1509, "Whole neighborhoods were swept away"), (1621, "leaving nothing but rubble"),
    (1689, "And in this region alone, more than 167,000 people lost their lives")))],
    open(os.path.join(os.path.dirname(HERE), "beats.json"), "w"), indent=1)
open(os.path.join(os.path.dirname(HERE), "review", "animate_log.txt"), "w").write("\n".join(LOG))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
