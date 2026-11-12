"""TitanicIceberg animation: ship + ghost liner, day/night, smear transfer, humans, props, FX, one continuous camera.
blender -b scene.blend --python 03_animate.py -- <anim_lib.py> <out.blend>"""
import sys, os, math, random
import bpy
from mathutils import Vector, Matrix, Euler, Quaternion

argv = sys.argv[sys.argv.index("--") + 1:]
LIB, OUT = argv[0], argv[1]
NS = {"__name__": "anim_lib"}; exec(open(LIB).read(), NS)
Rig, Human, make_human_ctrl, catmull, pchip, smooth, rotw = (NS[k] for k in ("Rig", "Human", "make_human_ctrl", "catmull", "pchip", "smooth", "rotw"))
sc = bpy.context.scene; D = bpy.data; O = D.objects
R_ = math.radians; random.seed(7)
Y0 = sc["Y0"]; DK = Vector(sc["DECK"]); SHIP0 = Vector(sc["SHIP_START"]); BENCH_TOP = sc["BENCH_TOP"]; DESK_TOP = sc["DESK_TOP"]
CYC_C = Vector(sc["CYC_C"]); RZ0 = sc["RZ0"]; SMX = sc["SMEAR_X"]
END = sc.frame_end
BEATS = [0, 120, 348, 612, 912, 1092, 1200, 1338, 1530]

def kv(obj, path, f, v, idx=-1, interp=None):
    if idx >= 0: getattr(obj, path)[idx] = v
    else: setattr(obj, path, v)
    obj.keyframe_insert(path, index=idx, frame=f)
    if interp:
        ad = obj.animation_data if hasattr(obj, "animation_data") else None
        if ad and ad.action:
            for fc in ad.action.fcurves if hasattr(ad.action, "fcurves") else []:
                if fc.data_path == path:
                    for k in fc.keyframe_points:
                        if k.co.x == f: k.interpolation = interp

def all_fcurves(idblock):
    ad = idblock.animation_data
    if not ad or not ad.action: return []
    act = ad.action
    if hasattr(act, "fcurves") and len(act.fcurves): return list(act.fcurves)
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags: out += list(cb.fcurves)
    return out

def set_interp(idblock, interp, path_pred=lambda p: True):
    for fc in all_fcurves(idblock):
        if path_pred(fc.data_path):
            for k in fc.keyframe_points: k.interpolation = interp

def node_key(tree_owner, node_name, f, v, sock=0, inp=None):
    nt = tree_owner.node_tree; nd = nt.nodes[node_name]
    s = nd.outputs[sock] if inp is None else nd.inputs[inp]
    s.default_value = v; s.keyframe_insert("default_value", frame=f)

# ---------------------------------------------------------------- ship: slow forward motion + gentle roll
ship_root = O["Ship_Root"]
def ship_pos(f): return SHIP0 + Vector((1.5 * f / 60, 0, 0))
for f in range(0, END + 1, 30):
    ship_root.location = ship_pos(f) + Vector((0, 0, 0.12 * math.sin(f / 60 * 1.1)))
    ship_root.rotation_euler = (R_(0.8) * math.sin(f / 60 * 0.9), R_(0.5) * math.sin(f / 60 * 0.7 + 1), 0)
    ship_root.keyframe_insert("location", frame=f); ship_root.keyframe_insert("rotation_euler", frame=f)
def ship_mat(f):
    return Matrix.Translation(ship_pos(f) + Vector((0, 0, 0.12 * math.sin(f / 60 * 1.1)))) @ \
        Euler((R_(0.8) * math.sin(f / 60 * 0.9), R_(0.5) * math.sin(f / 60 * 0.7 + 1), 0)).to_matrix().to_4x4()

# ---------------------------------------------------------------- world: dawn -> night (beat 5) -> dawn fog (beat 9)
W = sc.world
for f, v in ((0, 0.0), (905, 0.0), (940, 1.0), (1095, 1.0), (1150, 0.0)):
    node_key(W, "DayNight", f, v, inp='Factor')
for f, v in ((0, 1.0), (905, 1.0), (940, 1.0), (1095, 1.0), (1150, 1.0)):
    node_key(W, "SkyStrength", f, v, inp='Strength')
sun, moon = O["Key_Sun"], O["Moon_Key"]
for f, e in ((0, 4.0), (905, 4.0), (940, 0.0), (1095, 0.0), (1150, 4.0)): kv(sun.data, "energy", f, e)
for f, e in ((0, 0.0), (905, 0.0), (940, 5.0), (1095, 5.0), (1150, 0.0)): kv(moon.data, "energy", f, e)
fogm = D.materials["M_Fog"]
for f, v in ((0, 0.0004), (1500, 0.0004), (1620, 0.0009), (END, 0.0011)): node_key(fogm, "FogVol", f, v, inp='Density')
mm = D.materials["M_Mist"]; md = mm.node_tree.nodes["MistDrift"]
md.inputs['Location'].default_value = (0, 0, 0); md.inputs['Location'].keyframe_insert("default_value", frame=0)
md.inputs['Location'].default_value = (-9, 3, 0); md.inputs['Location'].keyframe_insert("default_value", frame=END)
smk = D.materials["M_Smoke"].node_tree.nodes["SmokeDrift"]
smk.inputs['Location'].default_value = (0, 0, 0); smk.inputs['Location'].keyframe_insert("default_value", frame=0)
smk.inputs['Location'].default_value = (0, 0, -40); smk.inputs['Location'].keyframe_insert("default_value", frame=END)
for idb in (W, fogm, mm, D.materials["M_Smoke"]): set_interp(idb.node_tree if hasattr(idb, "node_tree") else idb, 'LINEAR')

# ---------------------------------------------------------------- smear: present (photo era) except while the replay paints it
icem = D.materials["M_Ice"]
for f, v in ((0, SMX[0] - 6), (918, SMX[0] - 6), (919, SMX[1] + 6)):
    node_key(icem, "SmearSweep", f, v)

# ---------------------------------------------------------------- ghost liner
liner = O["liner"]; gm = D.materials["M_Ghost"]
pts = [v.co for v in liner.data.vertices]
LMINX, LMAXX = min(p.x for p in pts), max(p.x for p in pts)
BEAM = max(p.y for p in pts) - min(p.y for p in pts)
BOW_SIGN = int(os.environ.get("BOW_SIGN", "-1"))     # which end of the model is the bow (-1: -X end)
def liner_at(f, bow_x, y, yaw=0.0):
    # place so that the bow tip is at world x = bow_x moving along -X
    rot = 0.0 if BOW_SIGN < 0 else math.pi
    liner.rotation_euler = (0, 0, rot + yaw)
    tip_local = LMINX if BOW_SIGN < 0 else -LMAXX
    liner.location = (bow_x - tip_local, y, 0.0)
    liner.keyframe_insert("location", frame=f); liner.keyframe_insert("rotation_euler", frame=f)
# beat 2: passing between ship and berg (dawn ghost)
for f in range(110, 352, 8):
    liner_at(f, 40 - (f - 150) * 0.6, -46)
# beat 5: scraping along the scrape face; starboard side touching Y0
YS = Y0 - BEAM / 2 + 1.2
for f in range(900, 1100, 6):
    bow = 60 - (f - 912) * 0.5
    liner_at(f, bow, YS, yaw=R_(-1.5))
set_interp(liner, 'LINEAR')
for f, v in ((0, 0.0), (140, 0.0), (185, 2.0), (300, 2.0), (345, 0.0), (918, 0.0), (945, 0.9), (1045, 0.9), (1086, 0.0)):
    node_key(gm, "GhostAlpha", f, v)
liner.hide_render = False
# smear sweep follows the contact (bow passes the face from +X to -X)
for f in range(920, 1092, 6):
    bow = 60 - (f - 912) * 0.5
    node_key(icem, "SmearSweep", f, max(SMX[0] - 6, min(SMX[1] + 6, bow + 8)))
# sparks emitter rides the contact point
spk = O["Spark_Emitter"]
for f in range(920, 1092, 6):
    bow = 60 - (f - 912) * 0.5
    x = max(SMX[0], min(SMX[1], bow + 8))
    spk.location = (x, Y0 - 0.4, 1.3); spk.rotation_euler = (R_(90), 0, 0); spk.keyframe_insert("location", frame=f)
spk.location = (0, 0, -400); spk.keyframe_insert("location", frame=1095); spk.keyframe_insert("location", frame=0)
spk.location = (SMX[1], Y0 - 0.4, 1.3); spk.keyframe_insert("location", frame=919)
glow = O["Scrape_Glow"]
for f, e in ((0, 0), (925, 0), (945, 900), (1084, 900), (1090, 0)): kv(glow.data, "energy", f, e)
# falling ice blocks during the scrape (shed from the face above the contact)
for i in range(7):
    ob = O[f"Ice_Shard_{i}"]
    x0 = random.uniform(SMX[0] + 2, SMX[1] - 2); bow_f = 912 + (60 - (x0 - 8)) / 0.5
    t0 = int(max(930, min(1070, bow_f))); z0 = random.uniform(8, 16)
    rest = ob.location.copy()
    ob.location = (x0, Y0 + 0.4, z0); ob.keyframe_insert("location", frame=0); ob.keyframe_insert("location", frame=t0)
    T = math.sqrt(2 * z0 / 9.81)
    for k in range(1, 8):
        tt = T * k / 7; ob.location = (x0, Y0 - 1.0 - 3.0 * tt, z0 - 0.5 * 9.81 * tt * tt)
        ob.rotation_euler = (k * 0.6, k * 0.3, 0); ob.keyframe_insert("location", frame=t0 + int(tt * 60)); ob.keyframe_insert("rotation_euler", frame=t0 + int(tt * 60))
    tl = t0 + int(T * 60)
    for k in range(1, 12):
        ob.location = (x0, Y0 - 1.0 - 3.0 * T - 0.3 * k, -0.2 * math.exp(-k / 3) + 0.08 * math.sin(k)); ob.keyframe_insert("location", frame=tl + 8 * k)

# ---------------------------------------------------------------- floating things bob (ice bits, debris)
for ob in [o for o in O if o.name.startswith(("Bergy_Bit", "Debris_"))]:
    ph = random.random() * 6; base = ob.location.copy(); r0 = ob.rotation_euler.copy()
    drift = Vector((random.uniform(-0.3, 0.3), random.uniform(-0.2, 0.2), 0))
    sink = 0.35 if ob.name.startswith("Bergy") else 0.02
    for f in range(0, END + 1, 20):
        t = f / 60
        ob.location = base + drift * t + Vector((0, 0, -sink + 0.18 * math.sin(t * 1.3 + ph)))
        ob.rotation_euler = (r0.x + 0.06 * math.sin(t * 1.1 + ph), r0.y + 0.05 * math.sin(t * 0.9 + ph * 2), r0.z + 0.02 * t)
        ob.keyframe_insert("location", frame=f); ob.keyframe_insert("rotation_euler", frame=f)
# the berg drifts and slowly turns in the final beat (rooms are not used any more)
berg = O["Iceberg"]
berg.keyframe_insert("location", frame=1530); berg.keyframe_insert("rotation_euler", frame=1530)
berg.location = (2.5, 1.0, 0); berg.rotation_euler = (0, 0, R_(4)); berg.keyframe_insert("location", frame=END); berg.keyframe_insert("rotation_euler", frame=END)
set_interp(berg, 'LINEAR')

# ---------------------------------------------------------------- gulls gliding (beats 1-2 around the ship, beat 9 around the berg)
gull = O["gull"]; gull.rotation_euler = (0, 0, 0)
GULLS = [gull] + [gull.copy() for _ in range(5)]
for g in GULLS[1:]: g.data = gull.data; D.collections["Steamship"].objects.link(g)
for i, g in enumerate(GULLS):
    g.scale = (0.55,) * 3
    c0 = Vector((-20 + i * 6, -96 + i * 3, 14 + i * 2)) if i < 3 else Vector((10 * i - 40, 10, 24 + i))
    r = 9 + 3 * i; w = (0.5 + 0.08 * i) * (1 if i % 2 else -1)
    for f in range(0, END + 1, 10):
        t = f / 60; a = w * t + i
        p = c0 + Vector((r * math.cos(a) + 1.5 * t, r * math.sin(a), 1.5 * math.sin(t * 0.8 + i)))
        g.location = p; g.rotation_euler = (R_(8 * math.sin(t * 2 + i)), R_(-20 * w / abs(w)), a + (math.pi / 2 if w > 0 else -math.pi / 2))
        g.keyframe_insert("location", frame=f); g.keyframe_insert("rotation_euler", frame=f)

for g in GULLS: g.hide_render = True
# ---------------------------------------------------------------- humans
def rig_of(name): return O[name]
def gz_set(z): NS["ground_z"] = lambda x, y: z
FINGERS = None
def key_fingers(R, s, f, curl, thumb=20):
    Rh = R.rest("wrist." + s).to_3x3().normalized()
    a = Rh.col[0]; sign = 1 if s == "R" else -1
    for k in range(2, 6):
        c = curl[k - 2] if isinstance(curl, (list, tuple)) else curl
        for j, jw in ((1, 0.8), (2, 1.1), (3, 0.8)):
            b = "finger%d-%d.%s" % (k, j, s)
            R.key_q(b, f, R.local_q(b, Matrix.Rotation(R_(c * jw * sign), 3, a)))
    for j, fl in ((1, thumb * 0.4), (2, thumb * 0.8), (3, thumb)):
        b = "finger1-%d.%s" % (j, s)
        R.key_q(b, f, R.local_q(b, Matrix.Rotation(R_(fl * sign), 3, a)))

def face(R, f, brow=0.0, lids=0.0, jaw=0.0, smile=0.0, frown=0.0):
    """brow: +up (mm*), lids: +wide/-squint, jaw: degrees open, smile/frown: mouth corners"""
    def mv(n, d):
        if n not in R.PB: return
        pb = R.PB[n]; Rr = R.rest(n).to_3x3().normalized()
        pb.location = Rr.inverted() @ (Vector(d) * 0.001); pb.keyframe_insert("location", frame=f, group=n)
    for s, sx in (("L", 1), ("R", -1)):
        mv("oculi01." + s, (0, 0, 5 * brow - 3 * frown)); mv("oculi02." + s, (-1.5 * sx * frown, 0, 4 * brow - 2 * frown))
        mv("orbicularis03." + s, (0, 0, 2.5 * lids)); mv("orbicularis04." + s, (0, 0, -1.2 * lids))
        mv("risorius03." + s, (sx * 3 * smile, 0, 3 * smile - 4 * frown)); mv("levator05." + s, (0, 0, 1.5 * smile))
    R.key_rot("jaw", f, [("X", -jaw)])

class Actor:
    def __init__(self, name, gz):
        self.o = rig_of(name); self.R = make_human_ctrl(self.o); self.H = Human(self.R); self.gz = gz
        self.o.location = (0, 0, 0)
    def pose(self, f, pos, yaw, flex=0.0, spine=(0, 0, 0), head=(0, 0), feet=None, crouch=0.0):
        gz_set(self.gz)
        p = Vector((pos[0], pos[1], self.gz + self.H.root_head.z - crouch))
        self.H.key_root(f, p, yaw=yaw, flex=flex)
        self.H.key_spine(f, flex=spine[0], twist=spine[1], side=spine[2], head=head)
        for s in "LR":
            if feet and s in feet: xy, fy = feet[s]
            else: xy, fy = self.H.foot_xy(s, p, yaw), yaw
            self.H.key_foot(s, f, Vector(xy), fy)
    def hand(self, s, f, W, d, n, pole=None, curl=40, thumb=25):
        self.H.key_hand(s, f, Vector(W), Vector(d), Vector(n), pole=Vector(pole) if pole else None)
        key_fingers(self.R, s, f, curl, thumb)

# --- steward on deck (armature space == ship-local because the rig is parented to the ship)
st = Actor("Steward", DK.z)
st.o.parent = ship_root; st.o.matrix_parent_inverse = Matrix.Identity(4); st.o.location = (0, 0, 0)
SP = DK + Vector((0.0, 1.55, 0))        # standing spot, facing +Y (the berg side)
YAW = 180.0
FEET = {"L": (Vector((SP.x - 0.13, SP.y - 0.02)), YAW - 8), "R": (Vector((SP.x + 0.16, SP.y - 0.12)), YAW + 10)}
bc = O["bcamera"]; bc.parent = st.o; bc.matrix_parent_inverse = Matrix.Identity(4)
def cam_xf(f, M):
    loc, q, _ = M.decompose(); bc.location = loc; bc.rotation_mode = 'QUATERNION'; bc.rotation_quaternion = q
    bc.keyframe_insert("location", frame=f); bc.keyframe_insert("rotation_quaternion", frame=f)
# camera held at chest -> raised to the eye -> shutter -> lowered and looking
CAMP = {0: (Vector((SP.x, SP.y + 0.32, DK.z + 1.12)), -15), 50: (Vector((SP.x, SP.y + 0.34, DK.z + 1.25)), -5),
        95: (Vector((SP.x + 0.02, SP.y + 0.40, DK.z + 1.5)), 4), 160: (Vector((SP.x + 0.02, SP.y + 0.40, DK.z + 1.51)), 5),
        230: (Vector((SP.x, SP.y + 0.33, DK.z + 1.2)), -10), 360: (Vector((SP.x - 0.02, SP.y + 0.33, DK.z + 1.18)), -12)}
for f, (cp, pitch) in CAMP.items():
    Rm = Matrix.Rotation(R_(180), 4, 'Z') @ Matrix.Rotation(R_(pitch), 4, 'X')   # model lens points -Y; turn it to +Y
    cam_xf(f, Matrix.Translation(cp) @ Rm)
    # hands on the camera body sides, palms in
    st.hand("L", f, cp + Vector((0.172, 0.0, 0.05)), (0, 1, 0.1), (-1, 0, 0), pole=cp + Vector((0.6, -0.4, -0.5)), curl=16, thumb=22)
    st.hand("R", f, cp + Vector((-0.06, 0.02, -0.035)), (0.15, 1, 0.0), (0, 0, 1), pole=cp + Vector((-0.6, -0.4, -0.5)), curl=22, thumb=25)
STP = [(0, (0, 0, 0), (-6, 0), 0.0), (50, (4, 0, 0), (2, 0), 0.0), (95, (8, 0, 0), (6, 0), 0.02), (115, (9, -2, 0), (6, 0), 0.03),
       (125, (6, 0, 0), (4, 0), 0.02), (160, (5, 0, 0), (4, 0), 0.02), (230, (0, 5, 0), (-6, 8), 0.0), (360, (2, 3, 0), (-4, 4), 0.0)]
for f, sp_, hd, cr in STP:
    st.pose(f, (SP.x, SP.y), YAW, flex=sp_[0] * 0.5, spine=sp_, head=hd, feet=FEET, crouch=cr)
for f, kw in ((0, dict(brow=0.2, lids=0.2)), (60, dict(brow=0.8, lids=0.6, jaw=4)), (110, dict(brow=0.4, lids=-0.4, jaw=2)),
              (130, dict(brow=1.0, lids=1.0, jaw=8, smile=0.3)), (200, dict(brow=1.2, lids=1.0, jaw=10)), (360, dict(brow=0.8, lids=0.6, jaw=5))):
    face(st.R, f, **kw)
# shutter click: right index finger pushes at 112


# --- deckhand coiling rope in the background
dh = Actor("Deckhand", DK.z + 0.025); dh.o.parent = ship_root; dh.o.matrix_parent_inverse = Matrix.Identity(4); dh.o.location = (0, 0, 0)
DP = DK + Vector((1.5, -1.0 + 0.78, 0))  # beside the coil, facing it (-Y)
dfeet = {"L": (Vector((DP.x + 0.22, DP.y + 0.08)), 10), "R": (Vector((DP.x - 0.24, DP.y + 0.02)), -12)}
for f in range(0, 400, 20):
    a = f / 60 * 3.5
    dh.pose(f, (DP.x, DP.y), 0.0, flex=34, spine=(55, 8 * math.sin(a), 0), head=(5, 5 * math.sin(a)), feet=dfeet, crouch=0.36)
    c = DK + Vector((1.5, -1.0, 0.3)) + Vector((0.16 * math.cos(a), 0.1 * math.sin(a) - 0.05, 0.05 * math.sin(a * 2)))
    dh.hand("R", f, c, (0, -0.3, -1), (0, 1, 0), pole=c + Vector((-0.5, 0.6, 0.2)), curl=70, thumb=40)
    dh.hand("L", f, DK + Vector((1.9, -0.85, 0.75)), (0.2, -0.5, -1), (-1, 0, 0), pole=DK + Vector((2.4, -0.3, 1.0)), curl=65)
    face(dh.R, f, brow=-0.3, lids=-0.3, frown=0.4, jaw=2)

# --- darkroom technician rocking the tray with tongs
tech = Actor("Tech", RZ0 + 0.026)
TP = Vector((1.2, Y0 + 4.72))
tfeet = {"L": (Vector((TP.x + 0.15, TP.y - 0.05)), 172), "R": (Vector((TP.x - 0.17, TP.y)), 188)}
tongs = O["Tongs"]
for f in range(1060, 1215, 6):
    t = (f - 1060) / 60; rock = math.sin(t * 5.0)
    tech.pose(f, TP, 180.0, flex=10, spine=(26, 3 * rock, 0), head=(26, 2), feet=tfeet, crouch=0.04)
    tip = Vector((1.25 + 0.05 * rock, Y0 + 5.35, BENCH_TOP + 0.06 + 0.012 * rock))
    tongs.location = tip + Vector((0, -0.12, 0.04)); tongs.rotation_euler = (R_(-20), 0, R_(90)); tongs.keyframe_insert("location", frame=f); tongs.keyframe_insert("rotation_euler", frame=f)
    tech.hand("R", f, tip + Vector((0, -0.27, 0.11)), (0, 1, -0.35), (0, 0, -1), pole=tip + Vector((-0.6, -0.6, 0)), curl=62, thumb=40)
    # left hand tilts the tray edge
    tech.hand("L", f, Vector((0.5, Y0 + 5.2, BENCH_TOP + 0.065 + 0.01 * rock)), (0, 1, -0.2), (0, 0, -1), pole=Vector((0.0, Y0 + 4.6, 1.5)), curl=30)
    tray = O["Tray_1"]; tray.rotation_euler = (R_(1.2 * rock), 0, 0); tray.keyframe_insert("rotation_euler", frame=f)
for f, kw in ((1060, dict(brow=-0.2, lids=-0.4, frown=0.3)), (1130, dict(brow=0.6, lids=0.4, jaw=4)), (1180, dict(brow=1.3, lids=1.0, jaw=10))):
    face(tech.R, f, **kw)
pd = D.materials["M_Print_Dev"]
for f, v in ((0, 0.0), (1105, 0.0), (1185, 1.0)): node_key(pd, "Develop", f, v)
for i in range(5):
    hp = O[f"Hanging_Print_{i}"]
    for f in range(1050, 1220, 15):
        hp.rotation_euler = (R_(4 * math.sin(f / 20 + i)), 0, R_(3 * math.sin(f / 31 + i))); hp.keyframe_insert("rotation_euler", frame=f)

# --- office: Expert B holds the print up, Expert A brings the magnifier in
eb = Actor("ExpertB", RZ0); ea = Actor("ExpertA", RZ0)
PR = O["Print_Office"]; PRC = Vector((8.2, Y0 + 5.0, 1.99)); PR.location = PRC; PR.rotation_euler = (R_(-8), 0, 0)
BP = Vector((8.25, Y0 + 5.25))
bfeet = {"L": (Vector((BP.x - 0.14, BP.y + 0.02)), 175), "R": (Vector((BP.x + 0.16, BP.y - 0.02)), 185)}
for f in range(1180, 1345, 10):
    t = (f - 1180) / 60; sway = math.sin(t * 2)
    eb.pose(f, BP, 180.0 + 3 * sway, flex=8, spine=(14, 2 * sway, 0), head=(18, 3 * sway), feet=bfeet, crouch=0.02)
    pc = PRC + Vector((0.01 * sway, 0, 0.01 * math.sin(t * 3)))
    PR.location = pc; PR.keyframe_insert("location", frame=f)
    eb.hand("L", f, pc + Vector((0.185, 0.04, -0.02)), (-0.3, 0, 1), (0, -1, 0), pole=pc + Vector((0.6, 0.4, -0.5)), curl=45, thumb=35)
    eb.hand("R", f, pc + Vector((-0.15, 0.025, -0.02)), (0.3, 0, 1), (0, -1, 0), pole=pc + Vector((-0.6, 0.4, -0.5)), curl=45, thumb=35)
AP = Vector((7.72, Y0 + 3.72))
afeet = {"L": (Vector((AP.x - 0.14, AP.y + 0.02)), 172), "R": (Vector((AP.x + 0.15, AP.y - 0.06)), 190)}
mag = O["magnifier"]
for f in range(1180, 1345, 10):
    t = (f - 1180) / 60; k = smooth((f - 1190) / 70)
    ea.pose(f, AP, 180.0, flex=6 + 8 * k, spine=(8 + 12 * k, -6, 0), head=(12 + 8 * k, -8), feet=afeet, crouch=0.02 + 0.04 * k)
    mc = Vector((7.98 + 0.03 * k, Y0 + 4.25 + 0.1 * k, 2.08 + 0.06 * k)) + Vector((0.008 * math.sin(t * 4), 0, 0))
    mag.location = mc - Vector((0, 0, 0.235)); mag.rotation_euler = (R_(-6), 0, R_(4)); mag.keyframe_insert("location", frame=f); mag.keyframe_insert("rotation_euler", frame=f)
    hd = mc + Vector((0, 0, -0.16))     # handle grip below the lens
    ea.hand("R", f, hd + Vector((0.068, -0.025, -0.05)), (-0.1, 0.1, 1), (-1, 0, 0), pole=hd + Vector((0.4, -0.5, -0.5)), curl=58, thumb=35)
    ea.hand("L", f, Vector((7.55, Y0 + 4.3, DESK_TOP + 0.012)), (0.2, 1, 0), (0, 0, -1), pole=Vector((7.2, Y0 + 3.7, 1.6)), curl=15)
for R, ks in ((ea.R, ((1180, dict(brow=0.3, lids=-0.5, frown=0.3)), (1260, dict(brow=0.8, lids=0.5, jaw=3)), (1300, dict(brow=1.4, lids=1.2, jaw=12)))),
              (eb.R, ((1180, dict(brow=0.5, lids=0.2)), (1270, dict(brow=1.2, lids=1.0, jaw=8)), (1320, dict(brow=1.4, lids=1.0, jaw=12, smile=0.3))))):
    for f, kw in ks: face(R, f, **kw)

# ---------------------------------------------------------------- explainer: ghost hull slides in beside the giant print, band lights up
lx = O["Liner_Explainer"]; gmx = D.materials["M_Ghost_Explainer"]
S = 0.05; lx.scale = (S, S, S)
GP = O["Print_Giant"].location.copy()
WL = GP.z - 4.05 / 2 + 1.05            # waterline height = the streak height in the photo (lower third)
for f, x in ((1338, GP.x + 2.7 + 18), (1395, GP.x + 2.7 + 9), (1450, GP.x + 2.7 + 0.4), (1530, GP.x + 2.7 + 0.2)):
    tip_local = LMINX if BOW_SIGN < 0 else -LMAXX
    lx.rotation_euler = (0, 0, 0.0 if BOW_SIGN < 0 else math.pi)
    lx.location = (x - tip_local * S, GP.y - 0.6, WL); lx.keyframe_insert("location", frame=f); lx.keyframe_insert("rotation_euler", frame=f)
# on the bright cyc an additive ghost vanishes: give the explainer hull a translucent blue body
_n = gmx.node_tree.nodes; _l = gmx.node_tree.links
_out = next(n for n in _n if n.type == 'OUTPUT_MATERIAL'); _src = _out.inputs['Surface'].links[0].from_socket
_body = _n.new('ShaderNodeBsdfPrincipled'); _body.inputs['Base Color'].default_value = (0.08, 0.35, 0.85, 1); _body.inputs['Roughness'].default_value = 0.4
_lw = _n.new('ShaderNodeLayerWeight'); _lw.inputs['Blend'].default_value = 0.5
_fa = _n.new('ShaderNodeMath'); _fa.operation = 'MULTIPLY_ADD'; _fa.inputs[1].default_value = 0.4; _fa.inputs[2].default_value = 0.25
_l.new(_lw.outputs['Facing'], _fa.inputs[0])
_fb = _n.new('ShaderNodeMath'); _fb.operation = 'MULTIPLY'; _fb.use_clamp = True; _l.new(_fa.outputs[0], _fb.inputs[0]); _l.new(_n["GhostAlpha"].outputs[0], _fb.inputs[1])
_lp = _n.new('ShaderNodeLightPath'); _fc = _n.new('ShaderNodeMath'); _fc.operation = 'MULTIPLY'
_lt = _n.new('ShaderNodeMath'); _lt.operation = 'LESS_THAN'; _lt.inputs[1].default_value = 0.5; _l.new(_lp.outputs['Transparent Depth'], _lt.inputs[0])
_l.new(_fb.outputs[0], _fc.inputs[0]); _l.new(_lt.outputs[0], _fc.inputs[1])
_mx = _n.new('ShaderNodeMixShader'); _l.new(_fc.outputs[0], _mx.inputs['Fac']); _l.new(_src, _mx.inputs[1]); _l.new(_body.outputs[0], _mx.inputs[2])
_l.new(_mx.outputs[0], _out.inputs['Surface'])
for f, v in ((1338, 0.0), (1360, 1.0), (1530, 1.0), (1545, 0.0)): node_key(gmx, "GhostAlpha", f, v)
for f, v in ((0, 0.0), (1440, 0.0), (1470, 1.0), (1530, 1.0), (1545, 0.0)): node_key(gmx, "RedBand", f, v)
# horizontal match line sweeping across print + hull at the waterline height
bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=1.0, location=(0, 0, 0), rotation=(0, R_(90), 0))
mline = bpy.context.object; mline.name = "Match_Line"
for c_ in list(mline.users_collection): c_.objects.unlink(mline)
D.collections["Explainer_Cyc"].objects.link(mline)
mlm = D.materials.new("M_MatchLine"); mlm.use_nodes = True; p = mlm.node_tree.nodes["Principled BSDF"]
p.inputs['Emission Color'].default_value = (1.0, 0.25, 0.12, 1); p.inputs['Emission Strength'].default_value = 12; mline.data.materials.append(mlm)
for f, sx_, cx in ((0, 0.01, GP.x - 2.7), (1455, 0.01, GP.x - 2.7), (1500, 9.0, GP.x + 1.8), (1530, 9.0, GP.x + 1.8), (1545, 0.01, GP.x + 1.8)):
    mline.scale = (1, 1, sx_); mline.location = (cx - 2.7 + sx_ / 2 if sx_ > 0.1 else cx, GP.y - 0.7, WL)
    mline.keyframe_insert("scale", frame=f); mline.keyframe_insert("location", frame=f)
# the photo itself: real streak pulse on the giant print (glow overlay)
cyc_m = D.materials["M_CycGradient"]
for f, v in ((0, 1.0), (1560, 1.0), (1590, 0.0)): node_key(cyc_m, "CycFade", f, v)

# ---------------------------------------------------------------- camera: one continuous spline
cam = D.objects.new("Camera_Main", D.cameras.new("Camera_Main")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.sensor_width = 36; cam.data.clip_start = 0.02; cam.data.clip_end = 3000
cam.data.dof.use_dof = True
def SW(f, v):   # ship-local -> world at frame f
    return ship_mat(f) @ Vector(v)
STW = lambda f, d: SW(f, SP + Vector(d))
CK = [  # frame, camera position, look target, lens, f-stop
    (0,    STW(0, (-1.3, 0.55, 0.45)),   STW(0, (0.0, 0.0, 1.35)),  22, 4.0),
    (60,   STW(60, (-0.85, 0.45, 1.55)),   STW(60, (0.0, 0.05, 1.6)), 28, 2.8),
    (90,   STW(90, (-0.8, -0.15, 1.7)), STW(90, (0.0, 0.35, 1.55)), 28, 2.8),
    (118,  STW(118, (-0.42, -0.5, 1.72)), STW(118, (0.0, 0.5, 1.5)), 28, 2.8),
    (180,  STW(180, (0.1, 0.9, 2.0)),    Vector((0, Y0, 14)),       30, 8.0),
    (240,  Vector((-12, -78, 6)),        Vector((-4, -30, 11)),     45, 8.0),
    (300,  Vector((-14, -58, 5)),        Vector((-4, -30, 7)),      26, 8.0),
    (350,  Vector((-14, -30, 2.4)),      Vector((-9, Y0, 1.6)),     28, 5.6),
    (410,  Vector((-15, Y0 - 17, 4.5)),  Vector((-4, Y0, 3.0)),     30, 5.6),
    (470,  Vector((-6, Y0 - 11, 3.0)),   Vector((0, Y0, 1.8)),      32, 5.6),
    (530,  Vector((1.5, Y0 - 4.2, 2.2)), Vector((3.2, Y0, 1.6)),    35, 5.6),
    (580,  Vector((6, Y0 - 7.5, 2.4)),   Vector((7.5, Y0, 1.6)),    32, 5.6),
    (625,  Vector((10, Y0 - 12.0, 4.5)), Vector((6, Y0, 2.0)),      30, 5.6),
    (680,  Vector((6, Y0 - 13, 11)),     Vector((0, -45, 0)),       26, 8.0),
    (740,  Vector((-2, -36, 30)),        Vector((-6, -62, 0)),      24, 8.0),
    (800,  Vector((-8, -62, 38)),        Vector((-14, -84, 0)),     24, 8.0),
    (860,  Vector((-42, -90, 20)),       ship_pos(860) + Vector((0, 4, 6)), 26, 8.0),
    (915,  Vector((-34, -44, 12)),       Vector((0, Y0, 8)),        26, 8.0),
    (965,  Vector((-28, Y0 - 7, 3.2)),   Vector((10, Y0 - 3, 3.0)), 24, 5.6),
    (1015, Vector((-10, Y0 - 4.2, 2.4)), Vector((6, Y0 - 1, 2.0)),  26, 5.6),
    (1055, Vector((0.5, Y0 - 3.4, 2.6)), Vector((2, Y0, 2.5)),      30, 5.6),
    (1080, Vector((2.0, Y0 - 0.7, 1.95)), Vector((2.0, Y0 + 5, 2.5)), 30, 5.6),
    (1105, Vector((1.8, Y0 + 1.4, 2.85)), Vector((1.2, Y0 + 5.45, 1.7)), 26, 5.6),
    (1150, Vector((2.0, Y0 + 4.95, 2.35)), Vector((1.2, Y0 + 5.45, 1.72)), 35, 2.8),
    (1185, Vector((3.4, Y0 + 4.0, 2.35)), Vector((6.5, Y0 + 4.4, 2.0)), 24, 5.6),
    (1215, Vector((5.2, Y0 + 4.3, 2.3)), Vector((7.8, Y0 + 4.3, 2.0)), 24, 5.6),
    (1265, Vector((8.9, Y0 + 2.5, 2.55)), Vector((8.1, Y0 + 4.6, 2.1)), 26, 4.0),
    (1310, Vector((8.27, Y0 + 3.75, 2.05)), Vector((8.22, Y0 + 5.0, 1.99)), 30, 4.0),
    (1328, Vector((8.24, Y0 + 4.96, 1.99)), Vector((8.0, Y0 + 9, 2.6)), 30, 5.6),
    (1350, Vector((7.8, Y0 + 9.6, 2.6)), Vector((6.5, Y0 + 18.7, 3.3)), 24, 8.0),
    (1405, Vector((10.0, Y0 + 11.0, 2.7)), Vector((9.2, Y0 + 18.4, 2.6)), 22, 8.0),
    (1465, Vector((9.6, Y0 + 14.2, 2.5)), Vector((9.3, Y0 + 18.5, 2.45)), 26, 5.6),
    (1520, Vector((7.0, Y0 + 14.3, 2.9)), Vector((6.5, Y0 + 18.7, 3.0)), 26, 8.0),
    (1555, Vector((6.6, Y0 + 20.5, 3.3)), Vector((7.5, Y0 + 32, 3.8)), 26, 8.0),
    (1572, Vector((9, 36, 7)),           Vector((24, 74, 3)),       24, 8.0),
    (1581, Vector((14, 41, 8.5)),        Vector((46, 44, 5)),       24, 8.0),
    (1590, Vector((20, 44, 10)),         Vector((4, 4, 10)),        24, 8.0),
    (1640, Vector((32, 44, 12)),         Vector((4, 4, 10)),        24, 8.0),
    (1700, Vector((58, 30, 12)),         Vector((0, 0, 11)),        24, 8.0),
    (1770, Vector((66, -28, 9)),         Vector((0, 0, 11)),        26, 8.0),
    (END,  Vector((42, -72, 7)),         Vector((0, 0, 12)),        28, 8.0),
]
# real ice surface on the dive line (the facet displacement moves it off the Y0 plane)
dg = bpy.context.evaluated_depsgraph_get(); bev = O["Iceberg"].evaluated_get(dg)
hit_, loc_, _, _ = bev.ray_cast(Vector((2.0, Y0 - 12, 2.5)), Vector((0, 1, 0)))
YS_ICE = loc_.y if hit_ else Y0
print("ICE SURFACE", YS_ICE)
CK = [k if k[0] != 1080 else (1080, Vector((2.0, YS_ICE - 0.45, 2.5)), k[2], k[3], k[4]) for k in CK]
fpos = catmull([(k[0], k[1]) for k in CK])
_tg = [pchip([(k[0], k[2][c]) for k in CK]) for c in range(3)]
ftgt = lambda f: Vector((_tg[0](f), _tg[1](f), _tg[2](f)))   # monotone: no overshoot when the target jumps far
flen = pchip([(k[0], float(k[3])) for k in CK]); fst = pchip([(k[0], float(k[4])) for k in CK])
prevq = None
for f in range(0, END + 1, 2):
    p = fpos(f); t = ftgt(f)
    q = (t - p).to_track_quat('-Z', 'Y')
    if prevq is not None and prevq.dot(q) < 0: q = -q
    prevq = q
    cam.location = p; cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = q
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_quaternion", frame=f)
    cam.data.lens = flen(f); cam.data.keyframe_insert("lens", frame=f)
    cam.data.dof.aperture_fstop = max(fst(f), 4.0 if (500 <= f <= 560 or 1130 <= f <= 1165) else 5.6); cam.data.dof.keyframe_insert("aperture_fstop", frame=f)
    fd = (t - p).length
    if f < 175: fd = (p - (STW(f, (0, 0.3, 1.5)) if f < 150 else Vector((0, Y0, 10)))).length if f < 150 else fd   # rack focus lens -> berg
    cam.data.dof.focus_distance = max(0.1, fd); cam.data.dof.keyframe_insert("focus_distance", frame=f)

# ---------------------------------------------------------------- fly-through visibility (camera passes through surfaces)
def vis(names, f_off, f_on=None):
    for n in names:
        o = O.get(n)
        if not o: continue
        objs = [o] + ([c for c in o.children] if o.type == 'ARMATURE' else [])
        for ob in objs:
            ob.visible_camera = True; ob.keyframe_insert("visible_camera", frame=0)
            ob.visible_camera = False; ob.keyframe_insert("visible_camera", frame=f_off)
            if f_on is not None:
                ob.visible_camera = True; ob.keyframe_insert("visible_camera", frame=f_on)
            set_interp(ob, 'CONSTANT', lambda p_: p_ == "visible_camera")
cross_skin = next(f for f in range(1060, 1100) if fpos(f).y > YS_ICE - 0.15)
vis(["Darkroom_WallFront", "liner"], cross_skin, 1700)
bb = [O["Iceberg"].matrix_world @ Vector(c) for c in O["Iceberg"].bound_box]
BERG_MAXY = max(v.y for v in bb)
back_on = next(f for f in range(1561, 1700) if fpos(f).y > BERG_MAXY + 1.0)
print("BERG back on", back_on, BERG_MAXY)
for n in ("Iceberg", "Mist_Bank"):
    ob = O[n]; ob.hide_render = False; ob.keyframe_insert("hide_render", frame=0)
    ob.hide_render = True; ob.keyframe_insert("hide_render", frame=cross_skin)
    ob.hide_render = False; ob.keyframe_insert("hide_render", frame=back_on)
    set_interp(ob, 'CONSTANT', lambda p_: p_ == "hide_render")
cross_print = next(f for f in range(1310, 1345) if fpos(f).y > Y0 + 5.0)
vis(["Print_Office", "ExpertB", "Office_WallBack", "Darkroom_WallRight", "Office_WallLeft"], cross_print)
cross_giant = next(f for f in range(1530, 1600) if fpos(f).y > GP.y - 0.02)
vis(["Print_Giant", "Liner_Explainer", "Explainer_Stage", "Match_Line"], cross_giant)
print("CROSS", cross_skin, cross_print, cross_giant)
# rooms never render outside their beats (safety: they're inside the berg anyway)
for o in list(D.collections["Rooms_In_Berg"].objects) + [O[n] for n in ("Tech", "ExpertA", "ExpertB")]:
    if "DoorCut" in o.name: continue
    for ob in [o] + list(o.children):
        ob.hide_render = True; ob.keyframe_insert("hide_render", frame=0)
        ob.hide_render = False; ob.keyframe_insert("hide_render", frame=cross_skin - 2)
        ob.hide_render = True; ob.keyframe_insert("hide_render", frame=cross_print + 30)
        set_interp(ob, 'CONSTANT', lambda p_: p_ == "hide_render")
for o in list(D.collections["Explainer_Cyc"].objects):
    o.hide_render = True; o.keyframe_insert("hide_render", frame=0)
    o.hide_render = False; o.keyframe_insert("hide_render", frame=cross_print - 4)
    o.hide_render = True; o.keyframe_insert("hide_render", frame=cross_giant + 1)
    set_interp(o, 'CONSTANT', lambda p_: p_ == "hide_render")
sc["CROSS"] = [cross_skin, cross_print, cross_giant]
# ---------------------------------------------------------------- hands: Limit Rotation on every finger, thumb and wrist (no backward bends)
import re
def limit_hands(rig, probe_frames):
    pbs = rig.pose.bones; nlim = 0
    for pb in pbs:
        m = re.match(r"finger(\d)-(\d)\.([LR])$", pb.name)
        if not m and not (re.match(r"wrist\.[LR]$", pb.name) and rig.name.startswith("Expert")): continue
        c = pb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'; c.name = "HandLimit"
        c.use_limit_x = c.use_limit_y = c.use_limit_z = True
        if m and m.group(1) != "1":
            # forward-curl axis/sign measured from the keyed poses
            acc = Vector((0, 0, 0))
            for f in probe_frames:
                sc.frame_set(f); e = pb.matrix_basis.to_euler('XYZ'); acc += Vector(e)
            ax = max(range(3), key=lambda i: abs(acc[i])); sg = 1 if acc[ax] >= 0 else -1
            lims = [(-R_(12), R_(12))] * 3
            lims[ax] = (0.0, R_(95)) if sg > 0 else (-R_(95), 0.0)
        elif m:
            lims = [(-R_(50), R_(50))] * 3
        else:
            lims = [(-R_(65), R_(65)), (-R_(45), R_(45)), (-R_(30), R_(30))]
        (c.min_x, c.max_x), (c.min_y, c.max_y), (c.min_z, c.max_z) = lims
        nlim += 1
    return nlim
for nm_, fr_ in (("Steward", (60, 120, 200)), ("Deckhand", (100, 200)), ("Tech", (1120, 1160)), ("ExpertA", (1250, 1300)), ("ExpertB", (1250, 1300))):
    print("HANDLIMIT", nm_, limit_hands(O[nm_], fr_))
for L_ in [o for o in O if o.type == "LIGHT"]: L_.visible_camera = False
O["Darkroom_DoorCut"].hide_render = True
sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ANIM DONE")
