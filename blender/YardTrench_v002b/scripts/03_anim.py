"""Animation + camera for every shot. blender -b work/sets.blend -P 03_anim.py -- <out.blend> [timing.json]
One camera object keyed every frame; a cut = a jump between frames. Each shot's character action is keyed at 1x from the
shot start and runs ~30% past its planned length (trimmed by the next cut). Environment time-lapses (groove depth, bare/dry
strip, water level, sun) are camera-independent scene states keyed per shot window.
Phase 2: timing.json {"S1": seconds, ..., "END": seconds} replaces the reference start times; nothing is time-stretched.
Helpers adapted from LoveCanal_v001 (ConnectB05)."""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib.py")).read())
exec(open(os.path.join(FILM, "..", "pipeline", "anim_lib.py")).read())
exec(open(os.path.join(FILM, "..", "pipeline", "hand_poses.py")).read())
args = sys.argv[sys.argv.index("--") + 1:]; out = args[0]
FPS = 60
# reference start seconds (Phase 1, from the 1 fps reference sheet); END = film end
T = {"S1": 0.0, "S2": 1.0, "S3": 3.0, "S4": 5.0, "S5": 7.0, "S6": 8.0, "S7": 9.5, "S8": 11.0, "S9": 14.0, "S10": 15.0,
     "S11": 16.0, "S12": 17.0, "S13": 19.0, "S14": 21.0, "S15": 22.0, "S16": 25.0, "S17": 27.0, "S18": 28.0, "S19": 31.0,
     "S20": 33.0, "S21": 34.0, "S22": 35.5, "S23": 36.8, "END": 38.5}
if len(args) > 1: T = json.load(open(args[1]))          # Phase 2: VO word timing replaces the reference timing entirely
ORDER = sorted([k for k in T if k != "END"], key=lambda k: T[k])
F = {k: 1 + round(v * FPS) for k, v in T.items()}
def f0(s): return F[s]
def f1(s): i = ORDER.index(s); return (F[ORDER[i + 1]] if i + 1 < len(ORDER) else F["END"]) - 1
def dur(s): return f1(s) - f0(s) + 1
def fx(s, extra=1.3): return f1(s)   # actions are procedural: Phase 2 regenerates each one at 1x to the VO window (no overlap into the next shot, no stretch)
sc.frame_start = 1; sc.frame_end = F["END"] - 1
OB = bpy.data.objects
G = OB["Ground"]; KB = G.data.shape_keys.key_blocks; GMN = bpy.data.materials["GroundMat"].node_tree.nodes
STAGES = eval(G["groove_stages"])

# ------------------------------------------------------------------ yard geometry (same formulas as 02_sets.py)
def path_x(y): return 0.55 * math.sin(y * 0.22) + 0.25 * math.sin(y * 0.07 + 1.0)
Y_PORCH, Y_BACK = 9.0, -12.5
def taper(y, a=Y_BACK + 0.6, b=Y_PORCH - 0.6, r=1.6): return smooth((y - a) / r) * smooth((b - y) / r)
def hsh(i, j): return (math.sin(i * 12.9898 + j * 78.233) * 43758.5453) % 1.0
def vnoise(x, y, s):
    xi, yi = math.floor(x / s), math.floor(y / s); fx_, fy_ = smooth(x / s - xi), smooth(y / s - yi)
    a, b, c, d = hsh(xi, yi), hsh(xi + 1, yi), hsh(xi, yi + 1), hsh(xi + 1, yi + 1)
    return (a * (1 - fx_) + b * fx_) * (1 - fy_) + (c * (1 - fx_) + d * fx_) * fy_
def prof(t, edge): return 1.0 - smooth((t - (1 - edge)) / edge) if t < 1 else 0.0
def stage_z(nm, x, y):
    hw, dep, ed = STAGES[nm]; t = abs(x - path_x(y)) / hw
    z = -dep * prof(t, ed) * taper(y)
    z += (0.02 * (vnoise(x, y, 0.3) - 0.5) * prof(t, 0.9) if nm == "Rut" else 0.03 * (vnoise(x, y, 0.5) - 0.5) * prof(t * 0.9, 0.5)) * taper(y)
    return z
STATE = {}          # frame -> {"Rut": v, "Groove": v, "Trench": v}
def stage_at(f):
    ks = sorted(STATE)
    if f <= ks[0]: return STATE[ks[0]]
    if f >= ks[-1]: return STATE[ks[-1]]
    a = max(k for k in ks if k <= f); b = min(k for k in ks if k > f)
    u = (f - a) / (b - a); va, vb = STATE[a], STATE[b]
    return {k: va[k] + (vb[k] - va[k]) * u for k in va}
def world_ground(x, y, f):
    if x > 60: return SECT_TOP                     # section block top
    st = stage_at(f); return sum(st[k] * stage_z(k, x, y) for k in st)

# ------------------------------------------------------------------ keyed scene states
def kval(sock_owner, attr, f, v):
    setattr(sock_owner, attr, v); sock_owner.keyframe_insert(attr, frame=f)
def key_env(f, rut=None, groove=None, trench=None, bare=None, dry=None, wet=None, halfw=None, crush=None):
    if rut is not None or groove is not None or trench is not None:
        prev = stage_at(f) if STATE else {"Rut": 0.0, "Groove": 0.0, "Trench": 0.0}
        st = {"Rut": prev["Rut"] if rut is None else rut, "Groove": prev["Groove"] if groove is None else groove, "Trench": prev["Trench"] if trench is None else trench}
        STATE[f] = st
        for k, v in st.items(): kval(KB[k], "value", f, v)
    for nm, v in (("bare", bare), ("dry", dry), ("wet", wet), ("halfw", halfw)):
        if v is not None: kval(GMN[nm].outputs[0], "default_value", f, v)
    for nm, v in (("bare", bare), ("halfw", halfw), ("crush", crush)):
        if v is not None: gn_set(OB["GrassBlades"], "Grass", nm, v, f)
def env_ramp(s, a, b, end=None):
    """scene state a at the shot start -> b at the cut (or `end` frame)"""
    key_env(f0(s), **a); key_env(end or f1(s), **b)

SUN = OB["Sun"]; SKY = sc.world.node_tree.nodes["SkyBG"]
def key_light(f, sun=3.4, sky=1.0, rz=-28.0, rx=42.0):
    kval(SUN.data, "energy", f, sun); kval(SKY.inputs[1], "default_value", f, sky)
    SUN.rotation_euler = (R_(rx), 0, R_(rz)); SUN.keyframe_insert("rotation_euler", frame=f)
RAIN = OB["Rain"]
_cam0 = OB.get("Camera") or bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
if _cam0.name not in sc.collection.objects: sc.collection.objects.link(_cam0)
RAIN.modifiers["Rain"].node_group.nodes["CamInfo"].inputs[0].default_value = _cam0; WATER = OB["Water"]; FLOW = bpy.data.materials["WaterMat"].node_tree.nodes["Flow"]
def key_rain(f, on, loc=None, t=None):
    key_vis(RAIN, [(f, on)])
    if loc is not None: RAIN.location = Vector(loc); RAIN.keyframe_insert("location", frame=f)
    if t is not None: gn_set(RAIN, "Rain", "t", t, f)
def key_water(f, on, z=None, flow=None):
    key_vis(WATER, [(f, on)])
    if z is not None: WATER.location = (0, 0, z); WATER.keyframe_insert("location", frame=f)
    if flow is not None: FLOW.inputs["Location"].default_value = (0, flow, 0); FLOW.inputs["Location"].keyframe_insert("default_value", frame=f)

# ------------------------------------------------------------------ characters
CH = {}
for n in ("Boy", "Man"):
    r = Rig(OB[n]); CH[n] = Human(r); OB[n].animation_data_create()
for H in CH.values():
    add_hand_limits(H.r.o)
    H.r.o.location = (0, 0, 0); H.r.o.rotation_mode = 'QUATERNION'; H.r.o.rotation_quaternion = (1, 0, 0, 0)   # world == rig space while keying
PLACE = {"M": Matrix.Identity(4), "f": 1}
def ground_z(x, y):
    p = PLACE["M"] @ Vector((x, y, 0)); return world_ground(p.x, p.y, PLACE["f"]) - PLACE["M"].translation.z
# frame hooks so the walk solver reads the ground at the frame being keyed
SOLE = 0.016      # MPFB shoe soles sit 1.5 cm below the rest ground plane: lift feet and root so soles rest ON the surface
_kf = Human.key_foot
def _key_foot(self, s, f, xy, yaw, lift=0.0, pitch=0.0): PLACE["f"] = f; return _kf(self, s, f, xy, yaw, lift + SOLE, pitch)
Human.key_foot = _key_foot
_kr = Human.key_root
def _key_root(self, f, pos, *a, **k): return _kr(self, f, Vector(pos) + Vector((0, 0, SOLE)), *a, **k)
Human.key_root = _key_root
def framed(path):
    def p(f): PLACE["f"] = f; return path(f)
    return p

PUTS = {n: [] for n in CH}
def put(n, s, pos, yaw):
    PUTS[n].append((f0(s), Matrix.Translation(Vector(pos)) @ Matrix.Rotation(R_(yaw), 4, 'Z')))
    PLACE["M"] = PUTS[n][-1][1]
def bake_puts():
    for i, (n, lst) in enumerate(PUTS.items()):
        o = OB[n]; o.rotation_mode = 'QUATERNION'; PK = Matrix.Translation((i * 40.0, -5000, -500))
        marks = []; starts = sorted(f for f, _ in lst)
        for f, M in lst:
            s = next(s_ for s_ in ORDER if f0(s_) == f); nxt = min([x for x in starts if x > f] or [10 ** 6])
            marks.append((f, M)); park = f1(s) + 1
            if park < nxt: marks.append((park, PK))
        marks = [(0, PK)] + sorted(marks, key=lambda m: m[0])
        for f, M in marks:
            loc, q, _ = M.decompose(); o.location = loc; o.rotation_quaternion = q
            o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_quaternion", frame=f)
        constant_all(o)

def frs(a, b, step):
    r = list(range(a, b + 1, step))
    if r and r[-1] != b: r.append(b)
    return r

def gz_local(x, y, f): PLACE["f"] = f; return ground_z(x, y)

def stand(H, f, pos=(0, 0), yaw=0.0, flex=4, spine=4, twist=0.0, head=(4, 0), side=0.0, dz=0.0):
    g = gz_local(pos[0], pos[1], f)
    H.key_root(f, Vector((pos[0], pos[1], g + H.root_head.z - 0.015 + dz)), yaw=yaw, flex=flex, side=side)
    H.key_spine(f, flex=spine, twist=twist, head=head)
    for s in "LR": H.key_foot(s, f, H.foot_xy(s, Vector(pos), yaw), yaw)

HX, HY, HZ = [float(v) for v in os.environ.get('YT_HANG', '0.075,0.07,0.50').split(',')]   # hand beside (not in front of) the thigh
def arms_hang(H, f, pos=(0, 0), sway=0.0, dz=0.0, yaw=0.0, bend=0.0, sides="LR"):
    """relaxed hands beside the thighs, elbows bent ~30 deg (bend > 0: more elbow, hand higher and forward); offsets turn with the body (yaw)"""
    g = gz_local(pos[0], pos[1], f); Rz = Matrix.Rotation(R_(yaw), 3, 'Z')
    for s, sx in (("L", 1), ("R", -1)):
        if s not in sides: continue
        sh = H.r.BN["upperarm01." + s].head_local
        off = Vector((sh.x + HX * sx, sh.y - HY - 0.9 * bend + sway * sx, 0))
        W = Vector((pos[0], pos[1], 0)) + Rz @ off; W.z = g + sh.z - HZ + dz + bend
        H.key_hand(s, f, W, Rz @ Vector((0, -0.3, -1)), Rz @ Vector((-sx, 0.0, 0)), pole=W + Rz @ Vector((0.3 * sx, 0.5, 0.25)))
        apply_pose(H.r.o, s, "relaxed", f)

def walk_arms(H, fa, fb, path, stride=0.72, step=2, amp=0.11, bend=0.0):
    """hands hang and swing opposite to the legs (local frame, facing -Y); elbows bent a little"""
    d = 0.0; prev = path(fa)
    for f in range(fa, fb + 1):
        p = path(f); d += (p - prev).to_2d().length; prev = p
        if (f - fa) % step and f != fb: continue
        ph = math.sin(2 * math.pi * d / stride); g = gz_local(p.x, p.y, f)
        for s, sx, sg in (("L", 1, 1), ("R", -1, -1)):
            sh = H.r.BN["upperarm01." + s].head_local
            W = Vector((p.x + sh.x + 0.07 * sx, p.y + sh.y - 0.06 - 0.8 * bend - amp * ph * sg, g + sh.z - 0.52 + bend + 0.04 * abs(ph)))
            H.key_hand(s, f, W, Vector((0, -0.25 * ph * sg - 0.08, -1)), Vector((-sx, 0, 0)), pole=W + Vector((0.3 * sx, 0.5, 0.3)))
    for s in "LR": apply_pose(H.r.o, s, "relaxed", fa)

def walk_line(H, fa, fb, start, speed, stride=0.72, lean=4, bend=0.0, amp=0.11):
    """walk straight along local -Y from local `start` at `speed` m/s; arms swing"""
    path = framed(lambda f: Vector((start[0], start[1] - speed * (f - fa) / FPS, 0)))
    H.walk(path, lambda f: 0.0, fa, fb, stride=stride, lift=0.07, bob=0.018, lean=lean)
    walk_arms(H, fa, fb, path, stride, amp=amp, bend=bend)
    return path

def face(H, f, brow=0.0, lid=-6, jaw=0.0):
    if lid > -50: lid = max(lid, -12.0)
    brow = min(max(brow, -0.002), 0.003); PB_ = H.r.PB
    for s_ in "LR":
        for b_ in ("oculi01.", "oculi02."):
            if b_ + s_ in PB_:
                pb = PB_[b_ + s_]; pb.location = (0, 0, brow); pb.keyframe_insert("location", frame=f)
        if "orbicularis03." + s_ in PB_:
            pb = PB_["orbicularis03." + s_]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R_(lid), 0, 0); pb.keyframe_insert("rotation_euler", frame=f)
    pb = PB_["jaw"]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R_(jaw), 0, 0); pb.keyframe_insert("rotation_euler", frame=f)
def blinks(H, fa, fb, brow=0.0, lid=-6, every=150, ofs=20):
    face(H, fa, brow, lid)
    for fb_ in range(fa + ofs, fb, every):
        face(H, fb_, brow, lid); face(H, fb_ + 4, brow, -55); face(H, fb_ + 9, brow, lid)

def key_prop(o, f, loc=None, rot=None):
    o.rotation_mode = 'XYZ'
    if loc is not None: o.location = Vector(loc); o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = Euler([R_(a) for a in rot]); o.keyframe_insert("rotation_euler", frame=f)

def follow_bone(prop, rig, bone, fa, fb, OFF, step=1):
    """prop rides on a bone (Child-Of style, keyed) with a fixed offset matrix in bone space"""
    prop.rotation_mode = 'QUATERNION'
    for f in frs(fa, fb, step):
        ev(f); M = rig.matrix_world @ rig.pose.bones[bone].matrix @ OFF
        l_, q_, _ = M.decompose(); prop.location = l_; prop.rotation_quaternion = q_
        prop.keyframe_insert("location", frame=f); prop.keyframe_insert("rotation_quaternion", frame=f)

# ------------------------------------------------------------------ camera
cam = OB.get("Camera") or bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
if cam.name not in sc.collection.objects: sc.collection.objects.link(cam)
sc.camera = cam; cam.data.clip_start = 0.03; cam.data.clip_end = 1500; cam.data.dof.use_dof = False; cam.data.sensor_width = 36
CAM = {}
def camshot(s, keys): CAM[s] = keys
def cam_at(s, f):
    ks = CAM[s]; u = (f - f0(s)) / max(1, dur(s) * 1.3)
    if u <= ks[0][0]: k = ks[0]; return Vector(k[1]), Vector(k[2]), k[3]
    for a, b in zip(ks, ks[1:]):
        if u <= b[0]:
            t = (u - a[0]) / (b[0] - a[0]); t = smooth(t) * 0.4 + t * 0.6
            return Vector(a[1]).lerp(Vector(b[1]), t), Vector(a[2]).lerp(Vector(b[2]), t), a[3] + (b[3] - a[3]) * t
    k = ks[-1]; return Vector(k[1]), Vector(k[2]), k[3]
def bake_camera():
    cam.rotation_mode = 'QUATERNION'
    for s in ORDER:
        for f in range(f0(s), f1(s) + 1):
            loc, tg, lens = cam_at(s, f)
            d = (tg - loc)
            up = 'Y' if abs(d.normalized().z) < 0.97 else 'Y'
            q = d.to_track_quat('-Z', 'Y')
            if abs(d.normalized().z) > 0.97:            # straight down: keep the frame's up = +Y world (house at the top)
                q = Euler((0, 0, 0)).to_quaternion()
                q = (Matrix.Rotation(math.atan2(d.y, d.x) if False else 0, 4, 'Z')).to_quaternion()
            cam.location = loc; cam.rotation_quaternion = q; cam.data.lens = lens
            cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_quaternion", frame=f); cam.data.keyframe_insert("lens", frame=f)
    for o in (cam, cam.data):
        for fc in fcurves_of(o.animation_data.action):
            for k in fc.keyframe_points: k.interpolation = 'LINEAR'
def top(p, h, yoff=0.08):
    """top-down camera at p (x,y) height h: target slightly toward +Y so 'up' in frame is +Y (the house side)"""
    return ((p[0], p[1] - yoff, h), (p[0], p[1], 0.0))

# ------------------------------------------------------------------ section block (S6) visibility, foot probes
SECT_OBJS = [o for o in bpy.data.collections["Section"].all_objects]
SECT_TOP = 0.62
for o in SECT_OBJS: key_vis(o, [(0, False), (f0("S6"), True), (f1("S6") + 1, False)])
BOY, MAN = CH["Boy"], CH["Man"]
for e, s_ in ((OB["FootProbe.L"], "L"), (OB["FootProbe.R"], "R")):
    c = e.constraints.new('COPY_LOCATION'); c.target = OB["Boy"]; c.subtarget = "foot." + s_; c.head_tail = 0.55
# blade crush hz window for the ankle-mid probe
for gname in ("GrassGN", "SectGrassGN"):
    for n_ in bpy.data.node_groups[gname].nodes:
        if n_.type == 'MAP_RANGE' and abs(n_.inputs[1].default_value + 0.2) < 1e-6:
            n_.inputs[1].default_value = -0.16; n_.inputs[2].default_value = -0.07

# ------------------------------------------------------------------ DA KRAS FILMS logo printed on the man's white shirt front
def shirt_logo(obj, rig, width=0.24):
    me = obj.data; me.use_auto_texspace = True
    tl, ts = Vector(me.texspace_location), Vector(me.texspace_size); lmin = tl - ts
    chest_z = rig.data.bones["upperarm01.L"].head_local.z - 0.13
    band = [v.co for v in me.vertices if abs(v.co.z - chest_z) < 0.02 and abs(v.co.x) < 0.04]
    fy = min(c.y for c in band)
    img = bpy.data.images.load(os.path.join(FILM, "..", "assets", "brand", "DaKrasFilms_logo_dark.png"), check_existing=True); h = width * img.size[1] / img.size[0]
    m = obj.active_material; nt = m.node_tree; N = nt.nodes; L = nt.links
    P = next(n for n in N if n.type == "BSDF_PRINCIPLED"); src = P.inputs["Base Color"].links[0].from_socket
    tc = N.new("ShaderNodeTexCoord")
    va = N.new("ShaderNodeVectorMath"); va.operation = 'MULTIPLY_ADD'; L.new(tc.outputs["Generated"], va.inputs[0])
    va.inputs[1].default_value = ts * 2; va.inputs[2].default_value = lmin                      # rest-space position
    vs = N.new("ShaderNodeVectorMath"); vs.operation = 'SUBTRACT'; L.new(va.outputs[0], vs.inputs[0]); vs.inputs[1].default_value = (-width / 2, 0, chest_z - h / 2)
    vd = N.new("ShaderNodeVectorMath"); vd.operation = 'DIVIDE'; L.new(vs.outputs[0], vd.inputs[0]); vd.inputs[1].default_value = (width, 1, h)
    sp = N.new("ShaderNodeSeparateXYZ"); L.new(vd.outputs[0], sp.inputs[0])
    uv = N.new("ShaderNodeCombineXYZ"); L.new(sp.outputs["X"], uv.inputs[0]); L.new(sp.outputs["Z"], uv.inputs[1])
    ti = N.new("ShaderNodeTexImage"); ti.image = img; ti.extension = 'CLIP'; L.new(uv.outputs[0], ti.inputs[0])
    sy = N.new("ShaderNodeSeparateXYZ"); L.new(va.outputs[0], sy.inputs[0])
    fm = N.new("ShaderNodeMath"); fm.operation = 'LESS_THAN'; L.new(sy.outputs["Y"], fm.inputs[0]); fm.inputs[1].default_value = fy + 0.06
    am = N.new("ShaderNodeMath"); am.operation = 'MULTIPLY'; L.new(ti.outputs["Alpha"], am.inputs[0]); L.new(fm.outputs[0], am.inputs[1])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; L.new(am.outputs[0], mx.inputs[0]); L.new(src, mx.inputs[6]); L.new(ti.outputs["Color"], mx.inputs[7])
    L.new(mx.outputs[2], P.inputs["Base Color"])
    print("LOGO on", obj.name, "chest_z", round(chest_z, 3), "front y", round(fy, 3))
shirt_logo(OB["Man.male_casualsuit02"], OB["Man"])

# ------------------------------------------------------------------ hidden-by-default FX
key_rain(0, False, (0, 0, 0), 0.0); key_water(0, False, -0.2, 0.0)
for b in [o for o in OB if o.name.startswith("Bag_")]: key_vis(b, [(0, False), (f0("S22"), True)])
HEL = OB["Helmet"]; key_vis(HEL, [(0, False), (f0("S22"), True)])
key_light(1)

exec(open(os.path.join(HERE, "03a_shots.py")).read())

bake_puts()
bake_camera()
os.makedirs(os.path.join(FILM, "work"), exist_ok=True)
json.dump([{"shot": s, "frame": f0(s), "end": f1(s), "seconds": T[s]} for s in ORDER], open(os.path.join(FILM, "work", "shots.json"), "w"), indent=1)
json.dump([{"shot": s, "frame": f0(s), "end": f1(s), "seconds": T[s]} for s in ORDER], open(os.path.join(FILM, "shots_provisional.json"), "w"), indent=1)
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
