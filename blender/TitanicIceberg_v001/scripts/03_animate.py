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

# v007: the wave patch also covers the ship's water (its edge at y=-100 showed as a dark line in the beat-4 wide); shifted by one 120 m tile so the waves elsewhere are unchanged
_sea = O["Ocean"]; _sea.location.y -= 120; _sea.modifiers["Ocean"].repeat_y = 3
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
for f, v in ((0, SMX[0] - 6),):   # v008: the paint is on the ice; the night shot reveals it behind the liner's stern
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
LLEN = LMAXX - LMINX
def stern_at(f): return 64 - (f - 912) * 0.5        # v008: the stern clears the smear (x 16 -> -14) during the shot
for f in range(900, 1100, 6):
    liner_at(f, stern_at(f) - LLEN, YS, yaw=0.0)
set_interp(liner, 'LINEAR')
for f, v in ((0, 0.0), (140, 0.0), (185, 2.0), (300, 2.0), (345, 0.0), (918, 0.0), (945, 0.9), (1045, 0.9), (1086, 0.0)):
    node_key(gm, "GhostAlpha", f, v)
liner.hide_render = False
HM = D.materials.new("M_Liner_Hull"); HM.use_nodes = True; _hn = HM.node_tree.nodes; _hl = HM.node_tree.links
_bs = _hn["Principled BSDF"]; _bs.inputs['Roughness'].default_value = 0.45
_tc = _hn.new('ShaderNodeTexCoord'); _sx = _hn.new('ShaderNodeSeparateXYZ'); _hl.new(_tc.outputs['Object'], _sx.inputs[0])
_lt = _hn.new('ShaderNodeMath'); _lt.operation = 'LESS_THAN'; _lt.inputs[1].default_value = 3.0; _hl.new(_sx.outputs['Z'], _lt.inputs[0])
_hi = _hn.new('ShaderNodeMath'); _hi.operation = 'GREATER_THAN'; _hi.inputs[1].default_value = 19.0; _hl.new(_sx.outputs['Z'], _hi.inputs[0])
_m1 = _hn.new('ShaderNodeMix'); _m1.data_type = 'RGBA'; _m1.inputs['A'].default_value = (0.012, 0.012, 0.014, 1); _m1.inputs['B'].default_value = (0.45, 0.03, 0.02, 1)
_hl.new(_lt.outputs[0], _m1.inputs['Factor'])
_m2 = _hn.new('ShaderNodeMix'); _m2.data_type = 'RGBA'; _m2.inputs['B'].default_value = (0.55, 0.52, 0.46, 1)
_hl.new(_m1.outputs['Result'], _m2.inputs['A']); _hl.new(_hi.outputs[0], _m2.inputs['Factor']); _hl.new(_m2.outputs['Result'], _bs.inputs['Base Color'])
for _ob in (liner, O["Liner_Explainer"]):
    for _sl in _ob.material_slots: _sl.link = 'OBJECT'; _sl.material = HM
O["Funnel_Smoke"].hide_render = True     # v008: the smoke smudged the sky near the lens
# smear sweep follows the contact (bow passes the face from +X to -X)
# sparks emitter rides the contact point
spk = O["Spark_Emitter"]
for f in range(920, 1092, 6):
    x = max(SMX[0], min(SMX[1] + 10, stern_at(f) - 3))
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
CAMP = {0: (Vector((SP.x, SP.y + 0.30, DK.z + 1.08)), -12), 50: (Vector((SP.x, SP.y + 0.32, DK.z + 1.14)), 2),
        95: (Vector((SP.x + 0.01, SP.y + 0.33, DK.z + 1.16)), 4), 160: (Vector((SP.x + 0.01, SP.y + 0.33, DK.z + 1.15)), 3),
        230: (Vector((SP.x, SP.y + 0.31, DK.z + 1.1)), -8), 360: (Vector((SP.x - 0.02, SP.y + 0.31, DK.z + 1.08)), -10)}
for f, (cp, pitch) in CAMP.items():
    Rm = Matrix.Rotation(R_(180), 4, 'Z') @ Matrix.Rotation(R_(pitch), 4, 'X')   # model lens points -Y; turn it to +Y
    cam_xf(f, Matrix.Translation(cp) @ Rm)
    # hands on the camera body sides, palms in
    st.hand("L", f, cp + Vector((0.165, 0.09, 0.07)), (0, 1, 0.15), (-1, 0, 0), pole=cp + Vector((0.6, -0.4, -0.5)), curl=48, thumb=42)
    st.hand("R", f, cp + Vector((-0.06, 0.02, -0.035)), (0.15, 1, 0.0), (0, 0, 1), pole=cp + Vector((-0.6, -0.4, -0.5)), curl=22, thumb=25)
STP = [(0, (2, 0, 0), (-2, 6), 0.0), (25, (3, 1, 0), (6, 3), 0.005), (50, (6, 0, 0), (24, 0), 0.01), (80, (7, -1, 0), (28, -2), 0.015),
       (100, (8, 0, 0), (30, 0), 0.02), (112, (9, 0, 0), (31, 0), 0.025), (125, (6, 0, 0), (12, 0), 0.015), (145, (3, 0, 0), (-4, 2), 0.0),
       (175, (4, 2, 0), (-6, 6), 0.0), (230, (2, 5, 0), (-3, 9), 0.0), (300, (3, 3, 0), (-4, 5), 0.0), (360, (2, 3, 0), (-4, 4), 0.0)]
for f, sp_, hd, cr in STP:   # breathing + a small weight shift side to side over planted feet
    sh = 0.015 * math.sin(f / 60 * 1.3)
    st.pose(f, (SP.x + sh, SP.y), YAW, flex=sp_[0] * 0.5, spine=(sp_[0] + 1.2 * math.sin(f / 60 * 2.2), sp_[1], sp_[2]), head=hd, feet=FEET, crouch=cr)
for f, kw in ((0, dict(brow=0.6, lids=0.5, jaw=3)), (50, dict(brow=0.1, lids=-0.3)), (110, dict(brow=-0.2, lids=-0.5, jaw=1)),
              (145, dict(brow=1.2, lids=1.0, jaw=9)), (200, dict(brow=1.3, lids=1.0, jaw=10, smile=0.2)), (360, dict(brow=0.8, lids=0.6, jaw=5))):
    face(st.R, f, **kw)
# shutter click: right index finger pushes at 112


# --- deckhand coiling rope in the background
dh = Actor("Deckhand", DK.z + 0.025); dh.o.parent = ship_root; dh.o.matrix_parent_inverse = Matrix.Identity(4); dh.o.location = (0, 0, 0)
DP = DK + Vector((1.5, -1.0 + 0.78, 0))  # beside the coil, facing it (-Y)
dfeet = {"L": (Vector((DP.x + 0.22, DP.y + 0.08)), 10), "R": (Vector((DP.x - 0.24, DP.y + 0.02)), -12)}
for f in range(0, 940, 20):
    a = f / 60 * 3.5
    up = max(0.0, 1 - abs(f - 170) / 50)
    dh.pose(f, (DP.x, DP.y), 0.0, flex=34, spine=(55 - 12 * up, 8 * math.sin(a), 0), head=(5 - 40 * up, 5 * math.sin(a) + 25 * up), feet=dfeet, crouch=0.36)
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
    lean = smooth((f - 1095) / 20) * (1 - smooth((f - 1125) / 12)); lift = smooth((f - 1125) / 12) * (1 - smooth((f - 1180) / 18))
    tech.pose(f, TP, 180.0, flex=10 + 2 * lean, spine=(26 + 3 * lean - 10 * lift + 1.0 * math.sin(t * 2.4), 3 * rock, 0), head=(26 + 4 * lean - 24 * lift, 2 + 3 * lift), feet=tfeet, crouch=0.04)
    tip = Vector((1.25 + 0.085 * rock, Y0 + 5.35 + 0.03 * math.sin(t * 2.5), BENCH_TOP + 0.06 + 0.022 * rock))   # v008: livelier agitation
    tongs.location = tip + Vector((0, -0.12, 0.04)); tongs.rotation_euler = (R_(-20), 0, R_(90)); tongs.keyframe_insert("location", frame=f); tongs.keyframe_insert("rotation_euler", frame=f)
    tech.hand("R", f, tip + Vector((0, -0.245, 0.11)), (0, 1, -0.35), (0, 0, -1), pole=tip + Vector((-0.6, -0.6, 0)), curl=62, thumb=40)
    # left hand tilts the tray edge
    tech.hand("L", f, Vector((0.62, Y0 + 5.27, BENCH_TOP + 0.014)), (0.2, 1, 0), (0, 0, -1), pole=Vector((0.1, Y0 + 4.6, 1.6)), curl=10, thumb=15)
for f, kw in ((1060, dict(brow=-0.2, lids=-0.4, frown=0.3)), (1130, dict(brow=0.4, lids=0.2, jaw=2)), (1160, dict(brow=1.4, lids=1.1, jaw=11)), (1190, dict(brow=1.0, lids=0.8, jaw=6, smile=0.3))):
    face(tech.R, f, **kw)
# v008: safelight fill on his face and a lamp over the tray so the image visibly comes up
for _nm, _loc, _rot, _e, _sz in (("Safelight_Fill", (1.3, Y0 + 5.95, 2.45), (R_(-72), 0, 0), 70.0, 0.7),
                                  ("Tray_Lamp", (1.35, Y0 + 5.35, 2.55), (0, 0, 0), 45.0, 0.5)):
    _ld = D.lights.new(_nm, 'AREA'); _ld.energy = _e; _ld.size = _sz; _ld.color = (1.0, 0.42, 0.28)
    _lo = D.objects.new(_nm, _ld); _lo.location = _loc; _lo.rotation_euler = _rot; D.collections["Rooms_In_Berg"].objects.link(_lo)
pd = D.materials["M_Print_Dev"]
for f, v in ((0, 0.0), (1092, 0.0), (1145, 1.0)): node_key(pd, "Develop", f, v)
for i in range(5):
    hp = O[f"Hanging_Print_{i}"]
    for f in range(1050, 1220, 15):
        hp.rotation_euler = (R_(4 * math.sin(f / 20 + i)), 0, R_(3 * math.sin(f / 31 + i))); hp.keyframe_insert("rotation_euler", frame=f)

# --- office: Expert B holds the print up, Expert A brings the magnifier in
eb = Actor("ExpertB", RZ0); ea = Actor("ExpertA", RZ0)
PR = O["Print_Office"]; PRC = Vector((8.2, Y0 + 4.86, 2.0)); PR.location = PRC; PR.rotation_euler = (R_(-8), 0, 0)
BP = Vector((8.25, Y0 + 5.25))
bfeet = {"L": (Vector((BP.x + 0.14, BP.y - 0.02)), -5), "R": (Vector((BP.x - 0.16, BP.y + 0.02)), 5)}
POINT_K = lambda f: smooth((f - 1335) / 15) * (1 - smooth((f - 1490) / 20))
for f in range(1180, 1710, 10):
    t = (f - 1180) / 60; sway = math.sin(t * 2)
    look = smooth((f - 1250) / 20) * (1 - smooth((f - 1290) / 15))
    eb.pose(f, BP, 0.0 + 3 * sway, flex=4, spine=(6 + 1.0 * math.sin(t * 2.3), 2 * sway, 0), head=(4 + 12 * look + 14 * POINT_K(f), -14 + 10 * look + 8 * POINT_K(f)), feet=bfeet, crouch=0.01)
    pc = PRC + Vector((0.01 * sway, 0, 0.01 * math.sin(t * 3)))
    PR.location = pc; PR.keyframe_insert("location", frame=f)
    kk = POINT_K(f)       # v008: B lets go with his left hand and points at the red streak (the proof), then takes the corner again
    tipP = pc + Vector((0.10 + 0.008 * math.sin(t * 6), -0.014, -0.05)); dP = Vector((-0.45, 0.77, -0.39)).normalized()
    W_ = (pc + Vector((0.16, 0.045, 0.06))).lerp(tipP - dP * 0.17, kk)
    d_ = Vector((-0.25, 0, 1)).lerp(dP, kk); n_ = Vector((0, -1, 0)).lerp(Vector((0, 0, -1)), kk)
    eb.hand("L", f, W_, d_, n_, pole=(pc + Vector((0.55, 0.2, -0.6))).lerp(pc + Vector((0.6, 0.35, -0.4)), kk), curl=50, thumb=35)
    eb.hand("R", f, pc + Vector((-0.165, 0.052, 0.06)), (0.25, 0, 1), (0, -1, 0), pole=pc + Vector((-0.55, 0.2, -0.6)), curl=50, thumb=35)
AP = Vector((7.72, Y0 + 3.9))
afeet = {"L": (Vector((AP.x - 0.14, AP.y + 0.02)), 172), "R": (Vector((AP.x + 0.15, AP.y - 0.06)), 190)}
mag = O["magnifier"]
_dg = bpy.context.evaluated_depsgraph_get()
_h = sc.ray_cast(_dg, Vector((7.55, Y0 + 4.3, 3.5)), Vector((0, 0, -1)))
DESK_HIT = _h[1].z if _h[0] else DESK_TOP
print("DESK top at A's hand", DESK_HIT, _h[4].name if _h[0] else None)
for f in range(1180, 1710, 10):
    t = (f - 1180) / 60; k = smooth((f - 1190) / 70)
    ea.pose(f, AP, 180.0, flex=5 + 4 * k, spine=(6 + 6 * k + 1.0 * math.sin(t * 2.1), -6, 0), head=(-2 + 2 * k, -10 + 4 * k), feet=afeet, crouch=0.02 + 0.02 * k)
    mc = Vector((7.98 + 0.03 * k, Y0 + 4.4 + 0.1 * k, 2.08 + 0.06 * k)) + Vector((0.008 * math.sin(t * 4), 0, 0))
    mag.location = mc - Vector((0, 0, 0.235)); mag.rotation_euler = (R_(-6), 0, R_(4)); mag.keyframe_insert("location", frame=f); mag.keyframe_insert("rotation_euler", frame=f)
    hd = mc + Vector((0, 0, -0.16))     # handle grip below the lens
    ea.hand("R", f, hd + Vector((0.068, -0.025, -0.05)), (-0.1, 0.1, 1), (-1, 0, 0), pole=hd + Vector((0.4, -0.5, -0.5)), curl=58, thumb=35)
    ea.hand("L", f, Vector((7.5, Y0 + 4.52, DESK_TOP + 0.03)), (0.15, 1, -0.1), (0, 0, -1), pole=Vector((7.1, Y0 + 3.9, 1.9)), curl=8, thumb=12)
for R, ks in ((ea.R, ((1180, dict(brow=0.3, lids=-0.5, frown=0.3)), (1260, dict(brow=0.8, lids=0.5, jaw=3)), (1300, dict(brow=1.4, lids=1.2, jaw=12)), (1420, dict(brow=1.1, lids=0.9, jaw=7)), (1560, dict(brow=1.3, lids=1.0, jaw=10)))),
              (eb.R, ((1180, dict(brow=0.5, lids=0.2)), (1270, dict(brow=1.2, lids=1.0, jaw=8)), (1320, dict(brow=1.4, lids=1.0, jaw=12, smile=0.3)), (1450, dict(brow=1.0, lids=0.8, jaw=5)), (1580, dict(brow=1.3, lids=1.0, jaw=9))))):
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

# ---------------------------------------------------------------- camera: v008 shot list (director asked for clean cuts)
cam = D.objects.new("Camera_Main", D.cameras.new("Camera_Main")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.sensor_width = 36; cam.data.clip_start = 0.02; cam.data.clip_end = 3000
cam.data.dof.use_dof = True
def SW(f, v):   # ship-local -> world at frame f
    return ship_mat(f) @ Vector(v)
STW = lambda f, d: SW(f, SP + Vector(d))
L_SHIP = lambda f, d: ("ship", d)          # marker: ship-local key, evaluated per frame (the ship moves)
GP_ = O["Print_Giant"].location.copy()
CUT_BERG, CUT_STEW, CUT_SHIP, CUT_DECK2, CUT_NIGHT, CUT_DARK, CUT_OFFICE = 121, 432, 606, 730, 906, 1070, 1170
CUT_A, CUT_PT, CUT_PROOF, CUT_BACK, CUT_B2, CUT_END = 1260, 1340, 1438, 1530, 1615, 1700
D0 = DESK_TOP
SHOTS = [
  # A1: the steward with his camera (beat 1)
  (0, CUT_BERG, [
    (0,    STW(0, (-1.3, 0.55, 0.45)),   STW(0, (0.0, 0.0, 1.35)),  22),
    (60,   STW(60, (-0.85, 0.45, 1.55)), STW(60, (0.0, 0.05, 1.6)), 28),
    (90,   STW(90, (-0.8, -0.15, 1.7)),  STW(90, (0.0, 0.35, 1.55)), 28),
    (CUT_BERG, STW(CUT_BERG, (-0.75, 0.55, 1.72)), STW(CUT_BERG, (0.0, 0.15, 1.45)), 28)]),
  # A2: cut to the berg, then a clear push-in to the red smear (beats 2-3)
  (CUT_BERG, CUT_STEW, [
    (CUT_BERG, Vector((-14, -80, 7)),    Vector((-4, Y0, 9)),       36),
    (240,  Vector((-12, -70, 6)),        Vector((-4, -30, 9)),      40),
    (300,  Vector((-10, -50, 4.5)),      Vector((-6, Y0, 3.5)),     30),
    (360,  Vector((-6, -37, 3.0)),       Vector((-4, Y0, 2.3)),     34),
    (CUT_STEW, Vector((-5, -34.0, 2.8)), Vector((-3.5, Y0, 2.2)),   38)]),
  # B: the photographer on deck framing the shot, face visible (ship-local)
  (CUT_STEW, CUT_SHIP, [
    (CUT_STEW, ("ship", (-0.62, 1.1, 1.42)), ("ship", (0.0, 0.12, 1.42)), 30),
    (500,      ("ship", (-0.5, 1.12, 1.38)), ("ship", (0.0, 0.12, 1.40)), 31),
    (CUT_SHIP, ("ship", (-0.38, 1.12, 1.40)), ("ship", (0.0, 0.12, 1.45)), 32)]),
  # C1: his steamship sailing past the debris, the berg beyond - visible push-in (2 s)
  (CUT_SHIP, CUT_DECK2, [
    (CUT_SHIP, Vector((14, -186, 40)),   Vector((-6, -92, 4)),      20),
    (CUT_DECK2, Vector((2, -150, 22)),   Vector((-8, -100, 6)),     22)]),
  # C2: on his deck, over his shoulder: the photographer watching the berg and the debris (beat 4)
  (CUT_DECK2, CUT_NIGHT, [
    (CUT_DECK2, ("ship", (-0.38, -1.35, 1.88)), ("ship", (0.45, 8.0, 1.0)), 24),
    (CUT_NIGHT, ("ship", (-0.32, -1.05, 1.86)), ("ship", (0.45, 8.0, 1.0)), 26)]),
  # D: night - the solid dark liner scrapes past; the red paint on the ice is revealed behind its stern (safe distance)
  (CUT_NIGHT, CUT_DARK, [
    (CUT_NIGHT, Vector((60, Y0 - 66, 13)), Vector((8, Y0, 6)),      26),
    (CUT_DARK, Vector((32, Y0 - 44, 7)),  Vector((2, Y0, 3.0)),     28)]),
  # E: darkroom - across the tray, facing him: his face in the safelight, the image coming up in the tray in front
  (CUT_DARK, CUT_OFFICE, [
    (CUT_DARK, Vector((1.32, Y0 + 5.9, 2.2)), Vector((1.22, Y0 + 5.0, 1.98)), 18),
    (CUT_OFFICE, Vector((1.3, Y0 + 5.82, 2.18)), Vector((1.22, Y0 + 5.0, 2.02)), 20)]),
  # F1: B holds the print up, face clear (beat 7)
  (CUT_OFFICE, CUT_A, [
    (CUT_OFFICE, Vector((8.42, Y0 + 3.5, 2.32)), Vector((8.22, Y0 + 5.0, 2.28)), 30),
    (CUT_A, Vector((8.36, Y0 + 3.85, 2.3)), Vector((8.22, Y0 + 5.0, 2.3)), 36)]),
  # F2: A leans in with the magnifier, his face toward us
  (CUT_A, CUT_PT, [
    (CUT_A, Vector((7.28, Y0 + 4.9, 2.42)), Vector((7.78, Y0 + 4.05, 2.4)), 30),
    (CUT_PT, Vector((7.38, Y0 + 4.72, 2.4)), Vector((7.8, Y0 + 4.05, 2.38)), 36)]),
  # F3: B points at the red streak (beat 8)
  (CUT_PT, CUT_PROOF, [
    (CUT_PT, Vector((8.52, Y0 + 3.7, 2.25)), Vector((8.24, Y0 + 4.9, 2.2)), 28),
    (CUT_PROOF, Vector((8.45, Y0 + 3.9, 2.22)), Vector((8.24, Y0 + 4.9, 2.16)), 32)]),
  # G: the proof on the desk - the hull model's red band lines up with the photo's streak; push in
  (CUT_PROOF, CUT_BACK, [
    (CUT_PROOF, Vector((8.4, -13.55, D0 + 0.17)), Vector((8.4, -12.45, D0 + 0.12)), 34),
    (CUT_BACK, Vector((8.38, -13.15, D0 + 0.12)), Vector((8.38, -12.45, D0 + 0.08)), 40)]),
  # H1: A's face reacts (beat 9)
  (CUT_BACK, CUT_B2, [
    (CUT_BACK, Vector((7.32, Y0 + 4.8, 2.42)), Vector((7.8, Y0 + 4.05, 2.42)), 34),
    (CUT_B2, Vector((7.4, Y0 + 4.65, 2.42)), Vector((7.8, Y0 + 4.05, 2.42)), 40)]),
  # H2: B's face with the print
  (CUT_B2, CUT_END, [
    (CUT_B2, Vector((8.38, Y0 + 3.75, 2.36)), Vector((8.22, Y0 + 5.05, 2.4)), 36),
    (CUT_END, Vector((8.33, Y0 + 4.0, 2.38)), Vector((8.22, Y0 + 5.05, 2.45)), 42)]),
  # I: closer (2.2 s) - fast push-in on the lone berg, the steamer beyond it
  (CUT_END, END + 1, [
    (CUT_END, Vector((96, 104, 14)),    Vector((-4, -20, 9)),       22),
    (END,  Vector((44, 44, 7.5)),        Vector((-2, -22, 8)),      24)]),
]
def _ev(f, v):
    return STW(f, v[1]) if isinstance(v, tuple) and v and v[0] == "ship" else v
SHOT_F = []
for s0, s1, ks in SHOTS:
    SHOT_F.append((s0, s1, ks))
def cam_at(f):
    for s0, s1, ks in SHOT_F:
        if s0 <= f < s1:
            if len(ks) == 1: k = ks[0]; return _ev(f, k[1]), _ev(f, k[2]), k[3]
            pos = catmull([(k[0], _ev(f, k[1])) for k in ks])(f)
            _tg = [pchip([(k[0], _ev(f, k[2])[c]) for k in ks]) for c in range(3)]
            return pos, Vector((_tg[0](f), _tg[1](f), _tg[2](f))), pchip([(k[0], float(k[3])) for k in ks])(f)
    k = SHOT_F[-1][2][-1]; return _ev(f, k[1]), _ev(f, k[2]), k[3]
prevq = None
for f in range(0, END + 1):          # baked on every frame: a cut is two adjacent keys
    p, t, ln = cam_at(f)
    q = (t - p).to_track_quat('-Z', 'Y')
    if prevq is not None and prevq.dot(q) < 0: q = -q
    prevq = q
    cam.location = p; cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = q
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_quaternion", frame=f)
    cam.data.lens = ln; cam.data.keyframe_insert("lens", frame=f)
    cam.data.dof.aperture_fstop = 8.0; cam.data.dof.keyframe_insert("aperture_fstop", frame=f)
    fd = (t - p).length
    if f < CUT_BERG: fd = (p - STW(f, (0, 0.3, 1.5))).length
    cam.data.dof.focus_distance = max(0.1, fd); cam.data.dof.keyframe_insert("focus_distance", frame=f)
set_interp(cam, 'LINEAR'); set_interp(cam.data, 'LINEAR')
# ---------------------------------------------------------------- visibility per shot
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
cross_skin, cross_print, back_on = CUT_DARK, CUT_END, CUT_END
for n in ("Iceberg", "Mist_Bank"):
    ob = O[n]; ob.hide_render = False; ob.keyframe_insert("hide_render", frame=0)
    ob.hide_render = True; ob.keyframe_insert("hide_render", frame=cross_skin)
    ob.hide_render = False; ob.keyframe_insert("hide_render", frame=back_on)
    set_interp(ob, 'CONSTANT', lambda p_: p_ == "hide_render")
cross_giant = CUT_BACK
print("CROSS", cross_skin, cross_print)
# rooms render only in their shots
for o in list(D.collections["Rooms_In_Berg"].objects) + [O[n] for n in ("Tech", "ExpertA", "ExpertB", "magnifier", "Print_Office", "Tongs") if n in O and O[n] not in list(D.collections["Rooms_In_Berg"].objects)]:
    if "DoorCut" in o.name: continue
    for ob in [o] + list(o.children):
        ob.hide_render = True; ob.keyframe_insert("hide_render", frame=0)
        ob.hide_render = False; ob.keyframe_insert("hide_render", frame=cross_skin - 2)
        ob.hide_render = True; ob.keyframe_insert("hide_render", frame=cross_print)
        set_interp(ob, 'CONSTANT', lambda p_: p_ == "hide_render")
# the proof stage renders only for its 1.5 s insert; no match line
for o in list(D.collections["Explainer_Cyc"].objects):
    o.hide_render = True; o.keyframe_insert("hide_render", frame=0)
    set_interp(o, 'CONSTANT', lambda p_: p_ == "hide_render")
sc["CROSS"] = [cross_skin, cross_print, cross_giant]
# v009: the proof on the office desk - a copy of the photo propped up, the hull model beside it, its red band at the streak's height
PH = PR.copy(); PH.data = PR.data; PH.animation_data_clear(); PH.name = "Print_Desk"; D.collections["Rooms_In_Berg"].objects.link(PH)
PH_H = PR.dimensions.z
PH.rotation_euler = (0, 0, 0); PH.location = (8.2, -12.45, DESK_TOP + PH_H / 2 + 0.002)
SK = 0.26 * PH_H / 13.5                         # streak at 26 % of the photo height = top of the hull's red band (model z 3), keel on the desk
lx.animation_data_clear(); lx.scale = (SK, SK, SK); lx.rotation_euler = (0, 0, 0 if BOW_SIGN < 0 else math.pi)
lx.location = (8.2 + 0.36 / 2 + 0.05 - LMINX * SK, -12.45 + 0.02, DESK_TOP + 10.5 * SK)
for ob in (PH, lx):
    ob.animation_data_clear() if ob is PH else None
    ob.hide_render = True; ob.keyframe_insert("hide_render", frame=0)
    ob.hide_render = False; ob.keyframe_insert("hide_render", frame=CUT_PROOF)
    ob.hide_render = True; ob.keyframe_insert("hide_render", frame=CUT_BACK)
    set_interp(ob, 'CONSTANT', lambda p_: p_ == "hide_render")
for ob in [PR, eb.o] + list(eb.o.children):     # the proof shot is the desk alone: one photo, no hand pointing at nothing
    for f_, v_ in ((CUT_PROOF, True), (CUT_BACK, False)):
        ob.hide_render = v_; ob.keyframe_insert("hide_render", frame=f_)
    set_interp(ob, 'CONSTANT', lambda p_: p_ == "hide_render")
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
# ---------------------------------------------------------------- hands: director's shared library (pipeline/hand_poses.py)
# every contact is re-keyed with grip_object / place_hand + presets; joint limits via add_hand_limits (v004 rev3)
HP = {"__name__": "hand_poses"}; exec(open(os.path.join(os.path.dirname(LIB), "hand_poses.py")).read(), HP)
for nm_ in ("Steward", "Deckhand", "Tech", "ExpertA", "ExpertB"):
    HP["add_hand_limits"](O[nm_])
def _wpos(ob): return ob.matrix_world.translation.copy()
def _bb_world(ob):
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return Vector([min(v[i] for v in bb) for i in range(3)]), Vector([max(v[i] for v in bb) for i in range(3)])
GRIP_LOG = []
def _log(tag, f, rep): GRIP_LOG.append((tag, f, {k: v for k, v in (rep or {}).items()}))
# steward: one hand grips the camera's side frame (wrap, thumb opposing), the other palm supports it underneath
for f in sorted(CAMP):
    sc.frame_set(f); mn, mx = _bb_world(bc); c = (mn + mx) / 2
    wl = st.o.matrix_world @ st.R.PB["wrist.L"].head
    sx = 1.0 if wl.x > c.x else -1.0
    side_pt = Vector((mx.x if sx > 0 else mn.x, c.y + 0.25 * (mx.y - mn.y), c.z + 0.1 * (mx.z - mn.z)))
    HP["apply_pose"](st.o, "L", "wrap_grip", f, amount=0.75)
    HP["apply_pose"](st.o, "R", "cup_hold", f)
# deckhand: right hand wraps the rope at the coil (preset; the coil is a curve), left hand holds the rope end loosely
for f in range(0, 940, 20):
    HP["apply_pose"](dh.o, "R", "wrap_grip", f); HP["apply_pose"](dh.o, "L", "cup_hold", f)
# tech: right hand pinches the bamboo tongs, left palm flat on the bench
for f in range(1060, 1215, 6):
    sc.frame_set(f); mn, mx = _bb_world(tongs); end = Vector(((mn.x + mx.x) / 2, mn.y + 0.04, (mn.z + mx.z) / 2))
    HP["apply_pose"](tech.o, "R", "pinch", f)          # acting-pass IK placement on the tongs, library pinch
    t0 = O["Tray_0"]; tmn, tmx = _bb_world(t0)   # left hand holds the near rim of the tray beside it
    _log("tech_L_tray", f, HP["grip_object"](tech.o, "L", f, t0, Vector(((tmn.x + tmx.x) / 2 + 0.1, tmn.y + 0.004, tmx.z - 0.004)), Vector((0, 0, -1))))
# office: A wraps the magnifier handle, other palm flat on the desk; B pinches the print's top corners
for f in range(1180, 1710, 10):
    sc.frame_set(f); mn, mx = _bb_world(mag)
    handle = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z + 0.07))
    wr_ = ea.o.matrix_world @ ea.R.PB["wrist.R"].head
    ap = Vector((handle.x - wr_.x, handle.y - wr_.y, 0)).normalized()
    HP["apply_pose"](ea.o, "R", "wrap_grip", f)      # IK placement from the acting pass (hand round the handle), library wrap preset
    HP["apply_pose"](ea.o, "L", "flat_palm", f)
    pmn, pmx = _bb_world(PR)
    for sd, x in (("L", pmx.x - 0.03), ("R", pmn.x + 0.03)):
        sh_ = eb.o.matrix_world @ eb.R.PB["upperarm01." + sd].head      # corner on the same side as that arm's shoulder
        x = pmx.x - 0.03 if sh_.x > (pmn.x + pmx.x) / 2 else pmn.x + 0.03
        HP["apply_pose"](eb.o, sd, "point" if (sd == "L" and POINT_K(f) > 0.5) else "pinch", f)        # acting-pass IK placement at the top corners (no arm crossing), library pinch
for t_, f_, r_ in GRIP_LOG[::8]: print("GRIP", t_, f_, r_)
# props held in a hand follow that hand's real (limit-clamped) palm, so contact holds whatever the wrist limits do
def palm_frame(rig, s_, space="world"):
    P = rig.pose.bones; M = rig.matrix_world if space == "world" else Matrix.Identity(4)
    wr = M @ P["wrist." + s_].head; f3 = M @ P["finger3-1." + s_].head
    f2 = M @ P["finger2-1." + s_].head; f5 = M @ P["finger5-1." + s_].head
    d = (f3 - wr).normalized(); a_ = (f2 - f5).normalized(); n = d.cross(a_) if s_ == "L" else a_.cross(d)
    return wr.lerp(f3, 0.75), n.normalized(), d
# magnifier handle sits in Expert A's right palm
for f in range(1176, 1711, 6):
    sc.frame_set(f); pp, n, d = palm_frame(ea.o, "R")
    off = mag.location - (mag.matrix_world.translation)          # zero for an unparented object
    mag.location = pp + n * 0.024 - Vector((0, 0, 0.07)); mag.keyframe_insert("location", frame=f)
# the tongs sit in the tech's thumb-index pinch
for f in range(1060, 1216, 6):
    sc.frame_set(f); P_ = tech.o.pose.bones; M_ = tech.o.matrix_world
    pinch = (M_ @ P_["finger1-3.R"].tail + M_ @ P_["finger2-3.R"].tail) / 2
    tongs.location = pinch + Vector((0, 0.095, -0.012)); tongs.keyframe_insert("location", frame=f)
# the office print sits between Expert B's two thumb-index pinches (it is held, it never floats)
for f in range(1176, 1711, 5):
    sc.frame_set(f); P_ = eb.o.pose.bones; M_ = eb.o.matrix_world
    pL = (M_ @ P_["finger1-3.L"].tail + M_ @ P_["finger2-3.L"].tail) / 2
    pR = (M_ @ P_["finger1-3.R"].tail + M_ @ P_["finger2-3.R"].tail) / 2
    mid = (pL + pR) / 2
    if f <= 1330: OFF_R = mid - pR                      # while he points, the print hangs from his right pinch alone
    mid = mid.lerp(pR + OFF_R, POINT_K(f))
    PR.location = mid - Vector((0, 0, 0.115)); PR.keyframe_insert("location", frame=f)   # pinches sit 1.5-2 cm in from the top edge
# the camera rests on the steward's right palm (armature space, the camera is parented to the rig)
for f in range(0, 366, 6):
    sc.frame_set(f); pp, n, d = palm_frame(st.o, "R", space="arm")
    up = n if n.z > 0 else -n
    bc.location = pp + up * 0.026; bc.keyframe_insert("location", frame=f)
set_interp(mag, 'BEZIER')
# v005: the camera is IN his hands -> Child Of the right hand bone (resting on the palm, no gap), not keyed beside it
sc.frame_set(100); bpy.context.view_layer.update()
W100 = bc.matrix_world.copy()
bc.animation_data_clear(); bc.parent = None; bc.matrix_world = W100
co_ = bc.constraints.new('CHILD_OF'); co_.name = "InRightHand"; co_.target = st.o; co_.subtarget = "wrist.R"
co_.inverse_matrix = (st.o.matrix_world @ st.R.PB["wrist.R"].matrix).inverted()
# left palm also under the camera (both palms carry it, palm-up stays inside the wrist limits)
for f in range(0, 366, 12):
    sc.frame_set(f); bpy.context.view_layer.update(); mn, mx = _bb_world(bc); c = (mn + mx) / 2
    fwd = (bc.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()          # camera lens direction (model lens = -Y)
    shL = st.o.matrix_world @ st.R.PB["upperarm01.L"].head
    side = Vector((shL.x - c.x, shL.y - c.y, 0)); side = side - fwd * side.dot(fwd); side.normalize()
    under = Vector((c.x, c.y, mn.z)) + side * 0.07 + fwd * 0.03             # left palm under the camera's near-left corner
    HP["place_hand"](st.o, "L", f, under, Vector((0, 0, 1)), Vector((fwd.x, fwd.y, 0)), skin=0.012)
    HP["apply_pose"](st.o, "L", "cup_hold", f)
# v008: shot B - he frames the shot again (same performance as 0-180, offset to 420-600: look down into the finder, shutter, look up)
for fc in all_fcurves(st.o):
    pts = [(k.co.x, k.co.y) for k in fc.keyframe_points if k.co.x <= 180]
    for x, y in pts: fc.keyframe_points.insert(x + 420, y)
    for x, y in [(k.co.x, k.co.y) for k in fc.keyframe_points if 180 <= k.co.x <= 360]: fc.keyframe_points.insert(x + 560, y)
    fc.update()

for L_ in [o for o in O if o.type == "LIGHT"]: L_.visible_camera = False
O["Darkroom_DoorCut"].hide_render = True
# the ghost liner is done after the night scrape: off the render entirely (it showed as a faint hull at the berg at 1760+)
for f_, v_ in ((0, True), (906, False), (1100, True)):   # v007: no ghost panes over the berg in beat 2; only the night scrape
    liner.hide_render = v_; liner.keyframe_insert("hide_render", frame=f_)
set_interp(liner, 'CONSTANT', lambda p_: p_ == "hide_render")
# hidden objects must not block camera rays: mirror every hide_render key onto hide_viewport (after all evaluation passes)
for ob in O:
    for fc in all_fcurves(ob):
        if fc.data_path == "hide_render":
            for k in fc.keyframe_points:
                ob.hide_viewport = bool(k.co.y); ob.keyframe_insert("hide_viewport", frame=int(k.co.x))
            set_interp(ob, 'CONSTANT', lambda p_: p_ == "hide_viewport")
            break
sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ANIM DONE")
