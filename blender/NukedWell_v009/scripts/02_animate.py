"""NukedWell v009 stage B: crew acting, the device, concrete, gas, fire, water, cap, blast, squeeze, the ONE camera, VO.
blender -b a.blend --python 02_animate.py -- <vo.mp3> <out.blend>
Built to the client's VO from the start (v008 timing): beats 1/156/282/387/507/777/875/1023/1131/1202/1341, end 1541.
States: PRESENT (device job) f1-349 and f1000-END; PAST (the blowout, three years earlier) f350-999. Every state switch
happens while the camera is underground looking at the cut face (the surface is out of frame)."""
import bpy, sys, math, random, os
from mathutils import Vector, Matrix, Quaternion
PIPE = "/home/user/Muhammed/blender/pipeline"
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(PIPE + "/anim_lib.py").read())
exec(open(PIPE + "/hand_poses.py").read())
exec(open(HERE + "/lib_anim.py").read())
args = sys.argv[sys.argv.index("--") + 1:]
VO, OUT = args[0], args[1]
random.seed(18)
END = 1541
SW_PAST, SW_PRESENT, SW_END = 350, 1000, 1260
O = bpy.data.objects
NBX, GPX = -3.0, 7.0
def log(*a): print("LOG", " ".join(str(x) for x in a))

def keyv(obj, path, f, val, idx=-1, interp=None):
    if idx >= 0:
        getattr(obj, path)[idx] = val
    else:
        setattr(obj, path, val)
    obj.keyframe_insert(path, frame=f, index=idx)
def socket_key(sock, f, val):
    sock.default_value = val; sock.keyframe_insert("default_value", frame=f)
def all_interp(idblock, kind):
    ad = idblock.animation_data
    if ad and ad.action:
        for fc in iter_fcurves(ad.action):
            for kp in fc.keyframe_points: kp.interpolation = kind

# ================================================================== the crew rigs
JOLT = O["Jolt"]
CREW = {}
for nm in ("CrewA", "CrewB"):
    rig = O[nm]
    CT_ = make_human_ctrl(rig)
    add_hand_limits(rig)
    for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'
    for s in "LR":
        lo = rig.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(145)
    CREW[nm] = (rig, CT_, Human(CT_), [c for c in rig.children if c.type == 'MESH' and c.name.endswith(".body")][0],
                [c for c in rig.children if c.type == 'MESH' and ("suit" in c.name)][0])

def frame_of(pos, yaw):
    return Matrix.Translation(Vector((pos[0], pos[1], 0))) @ Matrix.Rotation(math.radians(yaw), 4, 'Z')

# placements (x, y, yaw) per state; yaw 0 faces -Y (the camera side), + turns toward +X
PLACE = {
    "CrewA": [(1, (-4.55, 1.15, 40)), (SW_PAST, (1.2, 2.0, 62)), (SW_PRESENT, (-4.55, 1.15, 40)), (SW_END, (3.9, 0.95, 38))],
    "CrewB": [(1, (-1.35, 1.75, -42)), (SW_PAST, (2.5, 3.1, 52)), (SW_PRESENT, (-1.35, 1.75, -42)), (SW_END, (5.15, 1.75, 22))],
}
def place_at(nm, f):
    cur = None
    for f0, p in PLACE[nm]:
        if f >= f0: cur = p
    return cur
BOUNDS = sorted({f0 for v in PLACE.values() for f0, _ in v})

def look_target(nm, f):
    """what each man watches"""
    dz = O["Device"].matrix_world.translation if False else None
    if f < SW_PAST:
        return Vector((NBX, 0.0, max(0.2, dev_z(f) + 0.8)))
    if f < SW_PRESENT:
        if f < 760: return Vector((GPX, 0.3, 4.5 + 3.0 * smooth((f - 470) / 60)))
        if f < 935: return Vector((GPX, 0.3, 3.0))
        return Vector((GPX - 1.0, 2.0, 0.8))
    if f < SW_END:
        return Vector((NBX, 0.0, 0.3)) if nm == "CrewA" else Vector((NBX - 2.0, -1.0, 1.4))
    if f < 1440: return Vector((GPX, 0.0, 2.5))
    return Vector((GPX - 1.0, -6.0, 2.2))   # toward each other / the camera side while cheering

# ---------------------------------------------------------------- device path (needed by look targets)
DEV_KEYS = [(1, 2.6), (30, 2.25), (80, -0.6), (155, -9.0), (200, -16.4), (214, -16.9), (300, -16.9), (312, -15.8), (345, 2.0)]
def dev_z(f):
    if f >= SW_PRESENT: return -16.9
    if f >= 345: return 2.0
    return pchip(DEV_KEYS)(f)

def head_signs_for(rig):
    pb = rig.pose.bones["head"]; q0 = pb.rotation_quaternion.copy(); upd()
    e0 = Wh(rig, "eye.L"); out = {}
    for ax, i in (("X", 0), ("Z", 2)):
        pb.rotation_quaternion = Quaternion(Vector([1 if k == i else 0 for k in range(3)]), math.radians(10)); upd()
        out[ax] = Wh(rig, "eye.L") - e0; pb.rotation_quaternion = q0; upd()
    return (1 if out["X"].z < 0 else -1, 1 if out["Z"].x > 0 else -1)

for nm, (rig, CT_, H_, BODY, SUIT) in CREW.items():
    fs(1); signs = head_signs_for(rig)
    rest_eye = rig.data.bones["eye.L"].head_local.copy()
    sh_rest = {s: rig.data.bones["upperarm01." + s].head_local.copy() for s in "LR"}
    rnd = random.Random(hash(nm) % 1000)
    # -------- body: root, feet planted, breathing, weight shift
    keyframes = sorted(set(list(range(1, END + 1, 3)) + [END] + [b - 1 for b in BOUNDS if b > 1] + BOUNDS))
    for f in keyframes:
        x, y, yaw = place_at(nm, f)
        cheer = smooth((f - 1440) / 20) if f >= 1440 else 0.0
        bob = 0.03 * cheer * max(0.0, math.sin(2 * math.pi * (f - 1440) / 34)) if nm == "CrewB" else 0.02 * cheer * max(0.0, math.sin(2 * math.pi * (f - 1440) / 40))
        sway = 0.012 * math.sin(2 * math.pi * f / 260 + rnd.random() * 6)
        flex = 4.0 + 1.0 * math.sin(2 * math.pi * f / 210)
        if nm == "CrewA" and f < 160: flex += 4.0         # leans to watch the device go down
        M = frame_of((x, y), yaw)
        pos = M @ Vector((sway, 0.0, 0.0)); pos.z = H_.root_head.z - 0.015 + bob
        H_.key_root(f, pos, yaw=yaw, flex=flex * 0.4, side=1.5 * math.sin(2 * math.pi * f / 260))
        for s, sg in (("L", 1), ("R", -1)):
            fxy = (M @ Vector((sg * 0.13, -0.02 if s == "L" else 0.03, 0))).to_2d()
            H_.key_foot(s, f, fxy, yaw, lift=0.0)
        # spine breathing
        for n_, w in Human.SPINE_W.items():
            CT_.key_rot(n_, f, [("X", (flex + 1.2 * math.sin(2 * math.pi * f / 200)) * w), ("Z", 0.0)])
    # -------- head: look at the target (yaw/pitch relative to the body), clamped
    for f in keyframes:
        x, y, yaw = place_at(nm, f)
        tgt = look_target(nm, f)
        eye = Vector((x, y, rest_eye.z))
        d = tgt - eye
        ang = math.degrees(math.atan2(d.x, -d.y)) - yaw
        ang = (ang + 180) % 360 - 180
        pitch = -math.degrees(math.atan2(d.z, d.to_2d().length))
        ang = max(-55, min(55, ang)); pitch = max(-25, min(32, pitch))
        if f >= 1440: ang = ang * 0.6
        sx_, sz_ = signs
        for n_, w in (("neck01", 0.25), ("neck02", 0.25), ("neck03", 0.2), ("head", 0.3)):
            CT_.key_rot(n_, f, [("X", sx_ * pitch * w), ("Z", sz_ * ang * w)])
    # -------- face
    smile_keys = [(1, 0.1), (1000, 0.1), (1100, 0.2), (1400, 0.0), (1445, 0.9), (END, 0.85)]
    brow_keys = [(1, 0.0), (440, 0.0), (470, 0.9), (520, 0.4), (950, 0.6), (1000, 0.0), (1135, 0.0), (1145, 0.8), (1200, 0.3), (1420, 0.5), (1445, 0.4), (END, 0.3)]
    jaw_keys = [(1, 0.0), (460, 0.0), (475, 0.35), (520, 0.05), (1445, 0.0), (1452, 0.45), (1490, 0.25), (END, 0.2)]
    sm_, br_, jw_ = pchip(smile_keys), pchip(brow_keys), pchip(jaw_keys)
    for f in range(1, END + 1, 6):
        key_face(rig, f, smile=sm_(f), brow=br_(f), jaw=jw_(f))
    bl = [b + rnd.randint(-8, 8) for b in range(40, END - 20, 140)]
    blinks(rig, bl)
    saccades(CT_, 1, END, every=45, amp=(1.5, 2.5), seed=hash(nm) % 97)
    CREW[nm] = (rig, CT_, H_, BODY, SUIT, sh_rest)
log("crew bodies keyed")

# ---------------------------------------------------------------- arms (IK hands in each man's own frame)
def ray_surface(objs, origin, direction):
    best = None
    for o in objs:
        h = bvh_eval(o).ray_cast(Vector(origin), Vector(direction).normalized(), 5.0)
        if h[0] is not None and (best is None or h[3] < best[3]): best = h
    return best
def bvh_eval(obj):
    upd(); dg = bpy.context.evaluated_depsgraph_get(); e = obj.evaluated_get(dg); me = e.to_mesh(); Mw = obj.matrix_world
    b = BVHTree.FromPolygons([Mw @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons]); e.to_mesh_clear(); return b
from mathutils.bvhtree import BVHTree

def key_hand_local(nm, s, f, wl, dl, nl, pole_l, pose="relaxed"):
    rig, CT_, H_, BODY, SUIT, sh_rest = CREW[nm]
    x, y, yaw = place_at(nm, f); M = frame_of((x, y), yaw); R3 = M.to_3x3()
    H_.key_hand(s, f, M @ Vector(wl), R3 @ Vector(dl), R3 @ Vector(nl), pole=M @ Vector(pole_l))
    apply_pose(rig, s, pose, f)

_SURF = {}
def hang(nm, s, f, fwd=0.05, out=0.0, pose="relaxed"):
    """relaxed hanging arm: wrist 5 cm outside the clothed hip (ray-cast in the man's own frame), elbow bent slightly"""
    rig, CT_, H_, BODY, SUIT, sh_rest = CREW[nm]
    sx = 1 if s == "L" else -1
    sh = sh_rest[s]; z = sh.z - 0.52
    x, y, yaw = place_at(nm, f); M = frame_of((x, y), yaw); R3 = M.to_3x3()
    if (nm, s) not in _SURF:
        fs(f)
        o_w = M @ Vector((sx * 0.8, sh.y - fwd, z)); d_w = R3 @ Vector((-sx, 0, 0))
        hit = ray_surface([SUIT, BODY], o_w, d_w)
        _SURF[(nm, s)] = (M.inverted() @ hit[0]).x if hit else sx * 0.24
        log("hip surface", nm, s, round(_SURF[(nm, s)], 3))
    surf = _SURF[(nm, s)]
    wl = Vector((surf + sx * (0.05 + out), sh.y - fwd, z))
    key_hand_local(nm, s, f, wl, (sx * 0.08, -0.25, -1.0), (-sx, 0.0, 0.0), (sh.x + sx * 0.3, sh.y + 0.45, sh.z - 0.3), pose)

def signal_lower(nm, s, f, phase):
    """crane-signal 'lower slowly': forearm forward at chest height, palm down, small patting motion"""
    rig, CT_, H_, BODY, SUIT, sh_rest = CREW[nm]; sx = 1 if s == "L" else -1; sh = sh_rest[s]
    wl = Vector((sh.x + sx * 0.10, sh.y - 0.40, sh.z - 0.22 + 0.05 * math.sin(phase)))
    key_hand_local(nm, s, f, wl, (sx * -0.2, -1.0, 0.0), (0, 0, -1), (sh.x + sx * 0.45, sh.y + 0.1, sh.z - 0.45), "flat_palm")

def arm_up(nm, s, f, height=0.42, side=0.20, fwd=-0.05, pose="open_alarm", pump=0.0):
    rig, CT_, H_, BODY, SUIT, sh_rest = CREW[nm]; sx = 1 if s == "L" else -1; sh = sh_rest[s]
    wl = Vector((sh.x + sx * side, sh.y + fwd, sh.z + height - pump))
    key_hand_local(nm, s, f, wl, (sx * 0.15, 0.0, 1.0), (0, -1, 0), (sh.x + sx * 0.6, sh.y + 0.25, sh.z - 0.15), pose)

def point_at(nm, s, f, target):
    rig, CT_, H_, BODY, SUIT, sh_rest = CREW[nm]; sx = 1 if s == "L" else -1; sh = sh_rest[s]
    x, y, yaw = place_at(nm, f); M = frame_of((x, y), yaw); Mi = M.inverted()
    tl = Mi @ Vector(target); d = (tl - sh); d.z = max(-0.2, min(0.5, d.z)); d.normalize()
    wl = sh + d * 0.50 + Vector((0, 0, -0.06))
    key_hand_local(nm, s, f, wl, tuple(d), (0, 0, -1), (sh.x + sx * 0.4, sh.y + 0.3, sh.z - 0.4), "point")

for f in sorted(set(list(range(1, END + 1, 4)) + [END] + [b - 1 for b in BOUNDS if b > 1] + BOUNDS)):
    # CrewA: signals 'lower' while the device goes down (f1-150), then idle; in the end he cheers with both arms
    if f <= 150:
        signal_lower("CrewA", "R", f, 2 * math.pi * f / 36)
    elif f >= 1452:
        u = smooth((f - 1452) / 14)
        arm_up("CrewA", "R", f, height=0.10 + 0.36 * u, side=0.18 + 0.05 * u, pump=0.05 * math.sin(2 * math.pi * (f - 1452) / 40) * u)
    else:
        hang("CrewA", "R", f, fwd=0.05 + 0.01 * math.sin(f / 37.0))
    if f >= 1458:
        u = smooth((f - 1458) / 14)
        arm_up("CrewA", "L", f, height=0.10 + 0.34 * u, side=0.18 + 0.05 * u, pump=0.05 * math.sin(2 * math.pi * (f - 1458) / 40 + 1.0) * u)
    else:
        hang("CrewA", "L", f, fwd=0.05 + 0.01 * math.sin(f / 41.0))
    # CrewB: points at the fire in the past (f560-640), gives the 'go' with a raised hand (f1060-1110), fist pump at the end
    if 1060 <= f <= 1110 or f >= 1446:
        if f >= 1446:
            u = smooth((f - 1446) / 12)
            arm_up("CrewB", "R", f, height=0.08 + 0.38 * u, side=0.16, pose="power_fist",
                   pump=0.10 * max(0.0, math.sin(2 * math.pi * (f - 1446) / 34)) * u)
        else:
            u = smooth((f - 1060) / 12) * (1 - smooth((f - 1098) / 12))
            arm_up("CrewB", "R", f, height=0.05 + 0.38 * u, side=0.16, pose="open_alarm")
    else:
        hang("CrewB", "R", f, fwd=0.06)
    hang("CrewB", "L", f, fwd=0.05 + 0.01 * math.sin(f / 33.0))
log("arms keyed")
for nm, v in CREW.items():
    rig = v[0]; quat_continuity(rig)
    all_interp(rig, 'LINEAR')
    # teleports between states happen in one frame (camera underground): constant step at the boundaries
    ad = rig.animation_data
    for fc in iter_fcurves(ad.action):
        for kp in fc.keyframe_points:
            if int(round(kp.co.x)) in [b - 1 for b in BOUNDS if b > 1]: kp.interpolation = 'CONSTANT'
    rig.parent = JOLT

# ================================================================== device, cable, concrete
DEV, CAB, PLUG, POUR = O["Device"], O["Device_Cable"], O["Concrete_Plug"], O["Concrete_Pour"]
SHV_Z = O["HF_Sheave"].location.z
for f in range(1, END + 1, 2):
    z = dev_z(f)
    keyv(DEV, "location", f, Vector((NBX, 0.0, z)))
    top = z + 1.77
    keyv(CAB, "location", f, Vector((NBX, 0.0, top)))
    keyv(CAB, "scale", f, Vector((1, 1, max(0.01, SHV_Z - 0.38 * 0 - top))))
all_interp(DEV, 'LINEAR'); all_interp(CAB, 'LINEAR')
# after the plug sets (present again), the cable is cut off at the collar: hide the part hanging in the air
PLUG_TOP = [(1, -15.12), (214, -15.12), (281, -9.0), (284, -9.0), (300, -15.12)]
pt = pchip(PLUG_TOP)
for f in sorted(set(range(1, END + 1, 2)) | {1136, 1137}):
    if f < SW_PAST:
        top = pt(f) if f >= 214 else -15.12
    elif f < SW_PRESENT:
        top = -15.12
    else:
        top = -0.6
    z0 = -12.2 if f >= 1137 else -15.12
    keyv(PLUG, "location", f, Vector((NBX, 0.0, z0)))
    keyv(PLUG, "scale", f, Vector((1, 1, max(0.001, top - z0 + 0.001))))
all_interp(PLUG, 'LINEAR')
# falling concrete: a stream from the collar down to the plug top, f186-281 (reversed upward f282-300)
for f in range(170, 330, 2):
    if f < 186 or f > 300:
        L = 0.001
    elif f <= 281:
        L = max(0.001, min(1.0, (f - 186) / 10.0) * (0.0 - pt(f)))
    else:   # rewind: the stream's top end falls back down onto the draining plug (never a gap)
        u = min(1.0, (f - 281) / 12.0); top = -u * (0.0 - pt(f)) * 0.999
        keyv(POUR, "location", f, Vector((NBX + 0.12, 0.0, top)))
        L = max(0.001, top - pt(f))
    if f <= 281: keyv(POUR, "location", f, Vector((NBX + 0.12, 0.0, 0.0)))
    keyv(POUR, "scale", f, Vector((1, 1, L)))
all_interp(POUR, 'LINEAR')

# ================================================================== visibility per state (switches happen off camera)
def vis_on(obj, ranges):
    """ranges = [(f0, f1), ...] inclusive frames when visible; keyed on hide_render + hide_viewport"""
    on = lambda f: any(a <= f <= b for a, b in ranges)
    obj.hide_render = obj.hide_viewport = not on(1)
    obj.keyframe_insert("hide_render", frame=1); obj.keyframe_insert("hide_viewport", frame=1)
    for a, b in ranges:
        for f, st in ((a, True), (b + 1, False)):
            if f <= 1: continue
            obj.hide_render = obj.hide_viewport = not st
            obj.keyframe_insert("hide_render", frame=f); obj.keyframe_insert("hide_viewport", frame=f)
    set_interp(obj, 'CONSTANT', "hide")
PRESENT = [(1, SW_PAST - 1), (SW_PRESENT, END)]
PAST = [(SW_PAST, SW_PRESENT - 1)]
def tree(o): return [o] + [c for c in o.children_recursive]
for o in list(O):
    n = o.name
    if n.startswith(("FireTruck_", "WaterArc")) or n.startswith(("Steam",)):
        for t in tree(o): vis_on(t, PAST)
    if n.startswith(("Cap_Body",)):
        for t in tree(o): vis_on(t, [(860, END)])
    if n == "Cap_Cable":
        vis_on(o, [(860, 999)])
    if n.startswith("Dust_Ring"):
        vis_on(o, [(1100, 1320)])
    if n == "Fire_Main" or (o.parent and o.parent.name == "Fire_Main"):
        vis_on(o, [(SW_PAST, 999)])
    if n == "Concrete_Plug":
        vis_on(o, [(212, SW_PAST - 1), (SW_PRESENT, END)])
    if n.startswith(("HF_", "Winch_", "Logo_Crate", "Crate_", "NukeBore_Collar", "Device", "Concrete_Pour", "Logo_CratePrint")):
        if o.parent is None or o.parent.name == "Jolt" or n.startswith("Device"):
            vis_on(o, PRESENT)
    if n.startswith(("Fire_Fissure", "Crack")):
        for t in tree(o): vis_on(t, [(930, END)])
# device and cable are also gone in the past part (vis via PRESENT covers it)

# ================================================================== gas, fire, water, cap, cracks
GF, GFRONT = O["GasFlow"], O["GasFront"]
for f in range(1, END + 1, 30):
    keyv(GF, "location", f, Vector((0, 0, -f * 0.12)))
all_interp(GF, 'LINEAR')
# the gas front (gas exists below this height): full in the present; in the past it surges up f395-452
for f, z in ((1, 2.0), (SW_PAST - 1, 2.0), (SW_PAST, -28.0), (395, -28.0), (452, 0.5), (END, 0.5)):
    keyv(GFRONT, "location", f, Vector((0, 0, z)))
all_interp(GFRONT, 'LINEAR')
gas_hi = bpy.data.materials["M_GasUpper"].node_tree.nodes["GasOn"].outputs[0]
for f, v in ((1, 1.0), (1262, 1.0), (1320, 0.0), (END, 0.0)): socket_key(gas_hi, f, v)
for o in (O["GasWell_Casing"], O["Gas_Lower"], O["Gas_Upper"]):
    kb = o.data.shape_keys.key_blocks["Pinch"]
    for f, v in ((1, 0.0), (1238, 0.0), (1280, 1.0), (END, 1.0)):
        kb.value = v; kb.keyframe_insert("value", frame=f)
# fire turbulence clock (keyed, linear): flow drifts up, the 4D noise evolves
FF = O["FireFlow"]
keyv(FF, "location", 1, Vector((0, 0, 0))); keyv(FF, "location", END, Vector((0.6, 0.3, -END * 0.11)))
all_interp(FF, 'LINEAR')
fire_mats = [m for m in bpy.data.materials if m.name.startswith(("M_Fire_", "M_Smoke_Wisp"))]
for m in fire_mats:
    w = m.node_tree.nodes.get("FireW")
    if w: socket_key(w.outputs[0], 1, 0.0); socket_key(w.outputs[0], END, END * 0.035)
    all_interp(m.node_tree, 'LINEAR')
# main fire: burning in the present; in the past it erupts at f452; squeezed by the cap f905-935; dies f1385-1440
FIRE = O["Fire_Main"]
FK = [(1, 0.0), (452, 0.0), (462, 0.35), (490, 1.0), (880, 1.0), (905, 0.7), (925, 0.35), (937, 0.06), (950, 0.0), (END, 0.0)]
fk = FK
def fire_val(f):
    for (a, va), (b, vb) in zip(fk, fk[1:]):
        if a <= f <= b:
            if b - a == 1: return va if f == a else vb
            u = (f - a) / (b - a); return va + (vb - va) * smooth(u)
    return fk[-1][1]
for f in range(1, END + 1):
    v = fire_val(f)
    if f % 2 and not any(abs(f - a) <= 1 for a, _ in fk): continue
    sz = max(0.001, v)
    FIRE.scale = (0.75 + 0.25 * sz, 0.75 + 0.25 * sz, sz); FIRE.keyframe_insert("scale", frame=f)
    for m in fire_mats:
        if "Fire_Main" in m.name:
            socket_key(m.node_tree.nodes["FireAmt"].outputs[0], f, min(1.0, v * 1.3))
all_interp(FIRE, 'LINEAR')
for m in fire_mats: all_interp(m.node_tree, 'LINEAR')
FL = O["Fire_Light"]
def fire_val(f, _fv=fire_val):
    fis = 0.0 if f < 940 else (0.5 if f < SW_PRESENT else (1.0 if f < 1385 else max(0.0, 1 - (f - 1385) / 55)))
    return max(_fv(f), 0.6 * fis)
for f in range(1, END + 1, 2):
    v = fire_val(f); FL.data.energy = 60000 * v * (0.9 + 0.1 * math.sin(f * 1.7)); FL.data.keyframe_insert("energy", frame=f)
# fissure jets (past only, after capping)
for i in range(3):
    r_ = O["Fire_Fissure%d" % i]; ck = O["Crack%d" % i]; d0 = 940 + 10 * i
    for f, s_ in ((1, 0.001), (d0 - 12, 0.001), (d0, 0.6), (d0 + 8, 1.0), (END, 1.0)):
        ck.scale = (3.6 * s_, 0.45 * s_, 1); ck.keyframe_insert("scale", frame=f)
    for f, s_ in ((1, 0.001), (d0, 0.001), (d0 + 6, 0.2), (d0 + 22, 0.34), (999, 0.34), (SW_PRESENT, 0.5), (1385 + 6 * i, 0.5),
                  (1393 + 6 * i, 0.32), (1398 + 6 * i, 0.40), (1406 + 6 * i, 0.18), (1412 + 6 * i, 0.22), (1422 + 6 * i, 0.05), (1430 + 6 * i, 0.001), (END, 0.001)):
        r_.scale = (s_, s_, s_); r_.keyframe_insert("scale", frame=f)
    all_interp(ck, 'LINEAR'); all_interp(r_, 'LINEAR')
# water: both monitors open at f779, close (stream detaches and falls away) f872-890
for i in range(2):
    cu = O["WaterArc%d" % i].data
    for f, e, s_ in ((1, 0.0, 0.0), (779 + 6 * i, 0.0, 0.0), (800 + 6 * i, 1.0, 0.0), (872, 1.0, 0.0), (892, 1.0, 1.0), (END, 1.0, 1.0)):
        cu.bevel_factor_end = e; cu.keyframe_insert("bevel_factor_end", frame=f)
        cu.bevel_factor_start = s_; cu.keyframe_insert("bevel_factor_start", frame=f)
    all_interp(cu, 'LINEAR')
for i, s_o in enumerate(O[n] for n in ("Steam0", "Steam1", "Steam2", "Steam3")):
    a = 800 + 9 * i
    base = s_o.location.copy()
    for f, sc_, dz in ((1, 0.001, 0), (a, 0.001, 0), (a + 14, 1.4, 0.6), (a + 60, 2.4, 2.6), (a + 90, 2.8, 4.0), (END, 2.8, 4.0)):
        s_o.scale = (sc_,) * 3; s_o.keyframe_insert("scale", frame=f)
        s_o.location = base + Vector((0, 0, dz)); s_o.keyframe_insert("location", frame=f)
    m = s_o.data.materials[0]
    all_interp(s_o, 'LINEAR')
stm = bpy.data.materials["M_Steam"].node_tree.nodes["Amt"].outputs[0]
for f, v in ((1, 1.0), (850, 1.0), (900, 0.0), (END, 0.0)): socket_key(stm, f, v)
# cap: lowered on its cable from above (the cable runs out of the top of frame), seated at f935
CAP = O["Cap_Body"]
for f, z in ((1, 40.0), (860, 14.0), (875, 11.0), (925, 1.6), (937, 0.80), (END, 0.80)):
    keyv(CAP, "location", f, Vector((GPX, 0.0, z)))
all_interp(CAP, 'BEZIER')

# ================================================================== the blast (f1131), the squeeze (f1202-1280), the jolt
BL, CAV, RING, DUST = O["Blast_Sphere"], O["Blast_Cavity"], O["Pressure_Ring"], O["Dust_Ring"]
T0 = 1133
for f, r in ((1, 0.001), (T0, 0.001), (T0 + 4, 2.2), (T0 + 10, 4.2), (T0 + 16, 4.7), (T0 + 40, 4.7), (T0 + 55, 0.001), (END, 0.001)):
    BL.scale = (r,) * 3; BL.keyframe_insert("scale", frame=f)
bst = BL.data.materials[0].node_tree.nodes["Strength"].outputs[0]
for f, v in ((1, 12.0), (T0 + 6, 12.0), (T0 + 30, 3.0), (T0 + 50, 0.0), (END, 0.0)): socket_key(bst, f, v)
for f, r in ((1, 0.001), (T0 + 14, 0.001), (T0 + 18, 4.5), (END, 4.5)):
    CAV.scale = (r,) * 3; CAV.keyframe_insert("scale", frame=f)
cst = CAV.data.materials[0].node_tree.nodes["Strength"].outputs[0]
for f, v in ((1, 6.0), (T0 + 40, 6.0), (1300, 2.0), (END, 1.2)): socket_key(cst, f, v)
BLT = O["Blast_Light"]
for f, e in ((1, 0.0), (T0, 0.0), (T0 + 4, 1.5e5), (T0 + 30, 4.0e4), (T0 + 70, 1.5e4), (END, 8.0e3)):
    BLT.data.energy = e; BLT.data.keyframe_insert("energy", frame=f)
for f, r in ((1, 0.001), (1204, 0.001), (1206, 4.6), (1268, 12.5), (1272, 0.001), (END, 0.001)):
    RING.scale = (r,) * 3; RING.keyframe_insert("scale", frame=f)
all_interp(RING, 'LINEAR')
sq = bpy.data.materials["M_Strata"].node_tree.nodes["Squeeze"].outputs[0]
for f, v in ((1, 0.0), (1206, 0.0), (1268, 1.0), (END, 1.0)): socket_key(sq, f, v)
# the device is vaporised inside the flash; the plug's lower end is gone into the cavity
for o in [DEV] + list(DEV.children):
    o.hide_render = o.hide_viewport = False
    for k in ("hide_render", "hide_viewport"): o.keyframe_insert(k, frame=T0 + 3)
    o.hide_render = o.hide_viewport = True
    for k in ("hide_render", "hide_viewport"): o.keyframe_insert(k, frame=T0 + 4)
    set_interp(o, 'CONSTANT', "hide")
# dust ring at the surface over the blast; the surface jolts
dst = bpy.data.materials["M_Dust"].node_tree.nodes["Amt"].outputs[0]
for f, r, z in ((1, 0.001, 0.3), (T0 + 5, 0.001, 0.3), (T0 + 8, 1.5, 0.4), (T0 + 30, 6.0, 0.9), (T0 + 90, 10.0, 1.6), (END, 10.0, 1.6)):
    DUST.scale = (r, r, 1.0 + 0.8 * (r / 10)); DUST.keyframe_insert("scale", frame=f)
    DUST.location = (NBX, 3.0, z); DUST.keyframe_insert("location", frame=f)
for f, v in ((1, 1.0), (T0 + 40, 1.0), (T0 + 150, 0.0), (END, 0.0)): socket_key(dst, f, v)
for f, z in ((1, 0.0), (T0 + 5, 0.0), (T0 + 8, 0.12), (T0 + 11, -0.05), (T0 + 15, 0.03), (T0 + 20, 0.0), (END, 0.0)):
    keyv(JOLT, "location", f, Vector((0, 0, z)))
all_interp(JOLT, 'LINEAR')
# smoke wisp after the fire dies
for m in bpy.data.materials:
    if m.name.startswith("M_Smoke_Wisp"):
        a_ = m.node_tree.nodes["FireAmt"].outputs[0]
        for f, v in ((1, 0.0), (1420, 0.0), (1450, 0.9), (END, 0.6)): socket_key(a_, f, v)
        all_interp(m.node_tree, 'LINEAR')
for m in bpy.data.materials:
    if m.name.startswith("M_Fire_Fissure"):
        pass

# ================================================================== sky, sun: present (vivid blue), past (warm), the night in B5
W = bpy.context.scene.world; ramp = W.node_tree.nodes["SkyRamp"].color_ramp
SUN, MOON = O["Sun"], O["Moon"]
SKY = {"present": ((0.55, 0.85, 1.0), (0.02, 0.30, 0.95), 4.0, 0.0),
       "past": ((1.0, 0.55, 0.28), (0.04, 0.26, 0.85), 4.2, 0.0),
       "dusk": ((1.0, 0.42, 0.22), (0.22, 0.12, 0.45), 1.2, 0.1),
       "night": ((0.20, 0.10, 0.38), (0.01, 0.015, 0.09), 0.0, 0.9)}
for f, k in ((1, "present"), (SW_PAST - 1, "present"), (SW_PAST, "past"), (600, "past"), (632, "dusk"), (660, "night"), (700, "night"),
             (728, "dusk"), (756, "past"), (SW_PRESENT - 1, "past"), (SW_PRESENT, "present"), (END, "present")):
    lo, hi, sun_e, moon_e = SKY[k]
    ramp.elements[0].color = (*lo, 1); ramp.elements[0].keyframe_insert("color", frame=f)
    ramp.elements[1].color = (*hi, 1); ramp.elements[1].keyframe_insert("color", frame=f)
    SUN.data.energy = sun_e; SUN.data.keyframe_insert("energy", frame=f)
    MOON.data.energy = moon_e; MOON.data.keyframe_insert("energy", frame=f)
    SUN.rotation_euler = (math.radians(52 if k in ("present", "past") else 80), 0, math.radians(-32)); SUN.keyframe_insert("rotation_euler", frame=f)
all_interp(W.node_tree, 'LINEAR'); all_interp(SUN.data, 'LINEAR'); all_interp(MOON.data, 'LINEAR'); all_interp(SUN, 'LINEAR')
for f in (SW_PAST - 1, SW_PRESENT - 1):
    pass
# exposure: a controlled flash at the detonation (never a white frame)
sc.view_settings.exposure = -0.3
for f, e in ((1, -0.3), (T0, -0.3), (T0 + 4, -1.6), (T0 + 14, -0.9), (T0 + 40, -0.4), (T0 + 80, -0.3), (END, -0.3)):
    sc.view_settings.exposure = e; sc.view_settings.keyframe_insert("exposure", frame=f)

# ================================================================== the ONE camera (no cuts), level horizon, f/inf (no DOF)
cam = bpy.data.objects.new("CAM_Film", bpy.data.cameras.new("CAM_Film")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.clip_start = 0.1; cam.data.clip_end = 2000; cam.data.sensor_fit = 'AUTO'; cam.data.dof.use_dof = False
CAMK = [
    # f, position, target, lens
    (1, (-3.0, -5.7, 2.35), (-3.0, 1.0, 2.05), 30),
    (45, (-3.0, -5.5, 1.9), (-3.0, 1.0, 1.2), 30),
    (95, (-3.0, -8.5, -1.6), (-3.0, 0.0, -2.2), 30),
    (155, (-2.6, -10.5, -8.0), (-2.6, 0.0, -8.4), 30),
    (212, (-2.4, -10.5, -14.6), (-2.6, 0.0, -14.6), 30),
    (250, (-2.4, -10.8, -12.6), (-2.6, 0.0, -12.4), 30),
    (281, (-2.2, -11.0, -10.8), (-2.6, 0.0, -10.6), 30),
    (300, (-1.5, -11.0, -11.0), (-2.6, 0.0, -10.0), 30),
    (335, (-1.5, -14.0, -14.5), (-1.5, 0.0, -14.5), 30),
    (387, (6.0, -11.0, -20.0), (6.0, 0.0, -19.5), 30),
    (420, (6.4, -11.0, -12.0), (6.6, 0.0, -11.5), 30),
    (452, (6.8, -8.2, -0.2), (7.0, 0.0, 0.6), 30),
    (480, (6.6, -11.5, 3.0), (7.0, 0.0, 6.0), 28),
    (506, (6.2, -15.5, 4.2), (7.0, 0.0, 9.0), 26),
    (560, (2.4, -11.0, 2.6), (5.2, 2.0, 5.5), 24),
    (640, (2.6, -9.5, 2.4), (5.6, 2.0, 5.5), 24),
    (700, (2.2, -9.0, 2.3), (5.6, 2.0, 5.3), 24),
    (776, (1.4, -9.5, 2.4), (5.2, 2.6, 3.8), 24),
    (840, (3.2, -10.5, 3.0), (6.0, 3.0, 4.2), 22),
    (875, (5.0, -10.5, 3.4), (7.0, 1.0, 4.6), 26),
    (935, (6.0, -10.0, 2.6), (7.0, 1.0, 2.2), 28),
    (975, (6.0, -12.5, 4.5), (6.8, 2.5, 1.0), 26),
    (1000, (5.0, -12.0, -8.0), (5.0, 0.0, -8.5), 30),
    (1023, (1.0, -13.0, -10.0), (0.5, 0.0, -10.5), 30),
    (1060, (-2.5, -11.0, -14.0), (-2.5, 0.0, -14.3), 30),
    (1100, (-1.5, -16.0, -13.5), (-1.0, 0.0, -12.5), 30),
    (1131, (2.0, -29.0, -9.5), (2.0, 0.0, -9.5), 35),
    (1200, (2.2, -29.5, -9.6), (2.2, 0.0, -9.6), 35),
    (1250, (3.5, -16.0, -14.0), (4.0, 0.0, -14.5), 32),
    (1340, (5.2, -9.0, -16.2), (5.4, 0.0, -16.6), 30),
    (1370, (6.2, -9.0, -6.0), (6.6, 0.0, -5.5), 30),
    (1395, (6.4, -9.5, 1.2), (6.8, 0.0, 2.6), 28),
    (1440, (5.0, -5.6, 1.75), (5.2, 1.5, 1.6), 30),
    (1541, (4.8, -6.0, 2.3), (5.1, 1.5, 1.6), 30),
]
fP = [pchip([(k[0], k[1][i]) for k in CAMK]) for i in range(3)]
fT = [pchip([(k[0], k[2][i]) for k in CAMK]) for i in range(3)]
fL = pchip([(k[0], k[3]) for k in CAMK])
rnd = random.Random(5)
for f in range(1, END + 1):
    p = Vector([g(f) for g in fP]); t = Vector([g(f) for g in fT])
    if T0 + 5 <= f <= T0 + 30:
        a_ = 0.10 * (1 - (f - T0 - 5) / 25)
        p += Vector((rnd.uniform(-a_, a_), 0, rnd.uniform(-a_, a_)))
    cam.location = p; cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler()
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
    cam.data.lens = fL(f); cam.data.keyframe_insert("lens", frame=f)
all_interp(cam, 'LINEAR'); all_interp(cam.data, 'LINEAR')
for o in list(O):
    if o.name == "VCam": bpy.data.objects.remove(o, do_unlink=True)

# ================================================================== VO
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor; strips = se.strips if hasattr(se, "strips") else se.sequences
snd = strips.new_sound("VO", VO, 1, 1)
sc.frame_start, sc.frame_end = 1, END
json_b = [(1, "lowered down the shaft"), (156, "concrete was poured on top"), (282, "three years earlier"), (387, "erupted into flames"),
          (507, "a fireball over 400 feet tall"), (777, "tried to put it out with water"), (875, "capping it with a lid"),
          (1023, "they sent down a nuclear bomb"), (1131, "When it detonated"), (1202, "squeezed the earth around the well"),
          (1341, "sealing the pipe shut")]
import json
json.dump([{"beat": i + 1, "frame": f, "first_words": w} for i, (f, w) in enumerate(json_b)],
          open(os.path.join(os.path.dirname(HERE), "beats.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("ANIM_DONE", OUT)
